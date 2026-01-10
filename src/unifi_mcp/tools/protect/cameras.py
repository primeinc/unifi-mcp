"""UniFi Protect camera management tools."""

from typing import Any

from mcp.server.fastmcp import Context

from unifi_mcp.clients.base import AppContext
from unifi_mcp.clients.protect import UniFiProtectClient
from unifi_mcp.config import settings
from unifi_mcp.exceptions import UniFiNotFoundError


def _get_protect_client(ctx: Context, device_name: str | None = None) -> UniFiProtectClient:
    """Get a Protect client for the specified device.

    Args:
        ctx: MCP context
        device_name: Device name. If None, uses first Protect-enabled device.

    Returns:
        UniFiProtectClient instance

    Raises:
        ValueError: If no Protect-enabled device found
    """
    app_ctx: AppContext = ctx.request_context.lifespan_context

    # Find device with Protect service
    if device_name:
        device = settings.get_device(device_name)
        if not device or not device.has_protect:
            raise ValueError(f"Device '{device_name}' not found or doesn't have Protect")
    else:
        protect_devices = settings.get_protect_devices()
        if not protect_devices:
            raise ValueError("No Protect-enabled devices configured")
        device = protect_devices[0]

    return UniFiProtectClient(app_ctx.client, device)


async def list_cameras(
    ctx: Context,
    device: str | None = None,
) -> dict[str, Any]:
    """List all UniFi Protect cameras.

    Args:
        ctx: MCP context
        device: Device name (optional, uses first Protect device if not specified)

    Returns:
        Camera summary with status and details
    """
    client = _get_protect_client(ctx, device)
    return await client.get_camera_summary()


async def get_camera_details(
    ctx: Context,
    camera_id: str,
    device: str | None = None,
) -> dict[str, Any]:
    """Get detailed information about a specific camera.

    Args:
        ctx: MCP context
        camera_id: Camera ID or name
        device: Device name (optional)

    Returns:
        Camera details
    """
    client = _get_protect_client(ctx, device)

    # Try by ID first, then by name
    try:
        return await client.get_camera(camera_id)
    except UniFiNotFoundError:
        return await client.get_camera_by_name(camera_id)


async def get_camera_snapshot(
    ctx: Context,
    camera_id: str,
    device: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    """Get a snapshot from a camera.

    Args:
        ctx: MCP context
        camera_id: Camera ID or name
        device: Device name (optional)
        width: Optional width for resizing
        height: Optional height for resizing

    Returns:
        Dictionary with base64-encoded image and metadata
    """
    client = _get_protect_client(ctx, device)

    # Find camera (by ID or name)
    try:
        camera = await client.get_camera(camera_id)
    except UniFiNotFoundError:
        camera = await client.get_camera_by_name(camera_id)

    actual_id = camera.get("id")
    if not actual_id:
        raise ValueError(f"Could not find camera: {camera_id}")

    # Check if camera is connected
    if camera.get("state") != "CONNECTED":
        return {
            "success": False,
            "error": f"Camera '{camera.get('name')}' is not connected (state: {camera.get('state')})",
            "camera_id": actual_id,
            "camera_name": camera.get("name"),
        }

    # Get snapshot
    image_base64 = await client.get_camera_snapshot_base64(actual_id, width, height)

    return {
        "success": True,
        "camera_id": actual_id,
        "camera_name": camera.get("name"),
        "image_base64": image_base64,
        "image_format": "jpeg",
        "note": "Image is base64-encoded JPEG",
    }


async def get_protect_system_info(
    ctx: Context,
    device: str | None = None,
) -> dict[str, Any]:
    """Get UniFi Protect system information.

    Args:
        ctx: MCP context
        device: Device name (optional)

    Returns:
        System information including camera and accessory counts
    """
    client = _get_protect_client(ctx, device)
    return await client.get_system_info()


async def list_protect_devices(ctx: Context) -> dict[str, Any]:
    """List all configured devices with Protect service.

    Args:
        ctx: MCP context

    Returns:
        List of Protect-enabled devices
    """
    protect_devices = settings.get_protect_devices()

    return {
        "total_devices": len(protect_devices),
        "devices": [
            {
                "name": d.name,
                "url": d.url,
                "services": d.services,
            }
            for d in protect_devices
        ],
    }


async def get_camera_health_summary(
    ctx: Context,
    device: str | None = None,
) -> dict[str, Any]:
    """Get a health summary of all cameras.

    Provides an overview of camera status, connectivity, and potential issues.

    Args:
        ctx: MCP context
        device: Device name (optional)

    Returns:
        Health summary with issues and recommendations
    """
    client = _get_protect_client(ctx, device)
    cameras = await client.get_cameras()

    connected = []
    disconnected = []
    issues = []

    for cam in cameras:
        cam_info = {
            "id": cam.get("id"),
            "name": cam.get("name"),
            "state": cam.get("state"),
            "model": cam.get("type") or cam.get("modelKey"),
        }

        if cam.get("state") == "CONNECTED":
            connected.append(cam_info)
        else:
            disconnected.append(cam_info)
            issues.append({
                "camera": cam.get("name"),
                "issue": f"Camera is {cam.get('state', 'UNKNOWN')}",
                "severity": "critical",
            })

    return {
        "summary": {
            "total_cameras": len(cameras),
            "connected": len(connected),
            "disconnected": len(disconnected),
            "status": "healthy" if not disconnected else "degraded",
        },
        "connected_cameras": connected,
        "disconnected_cameras": disconnected,
        "issues": issues,
        "recommendations": [
            "Check network connectivity for disconnected cameras",
            "Verify PoE power supply for wired cameras",
            "Check camera logs in Protect for more details",
        ] if disconnected else [],
    }


async def get_liveviews(
    ctx: Context,
    device: str | None = None,
) -> list[dict[str, Any]]:
    """Get all configured liveviews.

    Args:
        ctx: MCP context
        device: Device name (optional)

    Returns:
        List of liveview configurations
    """
    client = _get_protect_client(ctx, device)
    return await client.get_liveviews()


async def get_protect_accessories(
    ctx: Context,
    device: str | None = None,
) -> dict[str, Any]:
    """Get all Protect accessories (lights, sensors, chimes).

    Args:
        ctx: MCP context
        device: Device name (optional)

    Returns:
        Dictionary of all accessories by type
    """
    client = _get_protect_client(ctx, device)

    lights = await client.get_lights()
    sensors = await client.get_sensors()
    chimes = await client.get_chimes()
    viewers = await client.get_viewers()

    return {
        "lights": lights,
        "sensors": sensors,
        "chimes": chimes,
        "viewers": viewers,
        "summary": {
            "total_lights": len(lights),
            "total_sensors": len(sensors),
            "total_chimes": len(chimes),
            "total_viewers": len(viewers),
        },
    }
