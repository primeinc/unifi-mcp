"""UniFi Protect API client."""

import base64
import logging
from typing import Any

import httpx

from unifi_mcp.config import UniFiDevice
from unifi_mcp.exceptions import UniFiAPIError, UniFiConnectionError, UniFiNotFoundError

logger = logging.getLogger(__name__)


class UniFiProtectClient:
    """Client for UniFi Protect Integration API.

    Provides methods for managing cameras, viewing events, and accessing
    NVR functionality via the Protect Integration API.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        device: UniFiDevice,
    ):
        """Initialize the Protect API client.

        Args:
            client: httpx AsyncClient instance
            device: UniFi device configuration
        """
        self.client = client
        self.device = device
        self.base_url = device.protect_api_base

    @property
    def _headers(self) -> dict[str, str]:
        """Get headers for requests."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-KEY": self.device.api_key,
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for httpx

        Returns:
            HTTP response

        Raises:
            UniFiConnectionError: If connection fails
            UniFiAPIError: For API errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.request(
                method,
                url,
                headers=self._headers,
                **kwargs,
            )
        except httpx.ConnectError as e:
            raise UniFiConnectionError(f"Failed to connect to Protect: {e}") from e
        except httpx.TimeoutException as e:
            raise UniFiConnectionError(f"Request timed out: {e}") from e

        if response.status_code == 401:
            raise UniFiAPIError("Authentication failed", 401)
        if response.status_code == 404:
            raise UniFiNotFoundError("Resource", endpoint)
        if response.status_code >= 400:
            raise UniFiAPIError(
                f"API error: {response.text[:200]}",
                response.status_code,
            )

        return response

    async def _get(self, endpoint: str, **kwargs: Any) -> Any:
        """Make a GET request and return JSON."""
        response = await self._request("GET", endpoint, **kwargs)
        return response.json()

    async def _get_binary(self, endpoint: str, **kwargs: Any) -> bytes:
        """Make a GET request and return binary data."""
        response = await self._request("GET", endpoint, **kwargs)
        return response.content

    # =========================================================================
    # Cameras
    # =========================================================================

    async def get_cameras(self) -> list[dict[str, Any]]:
        """Get all cameras.

        Returns:
            List of camera information dictionaries
        """
        return await self._get("/cameras")

    async def get_camera(self, camera_id: str) -> dict[str, Any]:
        """Get details for a specific camera.

        Args:
            camera_id: Camera ID

        Returns:
            Camera information dictionary

        Raises:
            UniFiNotFoundError: If camera not found
        """
        return await self._get(f"/cameras/{camera_id}")

    async def get_camera_by_name(self, name: str) -> dict[str, Any]:
        """Get a camera by name.

        Args:
            name: Camera name (case-insensitive partial match)

        Returns:
            Camera information dictionary

        Raises:
            UniFiNotFoundError: If camera not found
        """
        cameras = await self.get_cameras()
        name_lower = name.lower()

        for camera in cameras:
            if name_lower in camera.get("name", "").lower():
                return camera

        raise UniFiNotFoundError("Camera", name)

    async def get_camera_snapshot(
        self,
        camera_id: str,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes:
        """Get a snapshot from a camera.

        Args:
            camera_id: Camera ID
            width: Optional width for resizing
            height: Optional height for resizing

        Returns:
            JPEG image bytes
        """
        params = {}
        if width:
            params["w"] = width
        if height:
            params["h"] = height

        return await self._get_binary(f"/cameras/{camera_id}/snapshot", params=params)

    async def get_camera_snapshot_base64(
        self,
        camera_id: str,
        width: int | None = None,
        height: int | None = None,
    ) -> str:
        """Get a snapshot from a camera as base64.

        Args:
            camera_id: Camera ID
            width: Optional width for resizing
            height: Optional height for resizing

        Returns:
            Base64-encoded JPEG image
        """
        image_bytes = await self.get_camera_snapshot(camera_id, width, height)
        return base64.b64encode(image_bytes).decode("utf-8")

    # =========================================================================
    # Liveviews
    # =========================================================================

    async def get_liveviews(self) -> list[dict[str, Any]]:
        """Get all liveviews.

        Returns:
            List of liveview configurations
        """
        return await self._get("/liveviews")

    # =========================================================================
    # Sensors & Accessories
    # =========================================================================

    async def get_lights(self) -> list[dict[str, Any]]:
        """Get all Protect lights (floodlights).

        Returns:
            List of light information
        """
        return await self._get("/lights")

    async def get_sensors(self) -> list[dict[str, Any]]:
        """Get all Protect sensors.

        Returns:
            List of sensor information
        """
        return await self._get("/sensors")

    async def get_chimes(self) -> list[dict[str, Any]]:
        """Get all Protect chimes.

        Returns:
            List of chime information
        """
        return await self._get("/chimes")

    async def get_viewers(self) -> list[dict[str, Any]]:
        """Get all Protect viewers (Viewport devices).

        Returns:
            List of viewer information
        """
        return await self._get("/viewers")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def get_camera_summary(self) -> dict[str, Any]:
        """Get a summary of all cameras with status.

        Returns:
            Summary with camera counts and details
        """
        cameras = await self.get_cameras()

        connected = [c for c in cameras if c.get("state") == "CONNECTED"]
        disconnected = [c for c in cameras if c.get("state") == "DISCONNECTED"]

        return {
            "total_cameras": len(cameras),
            "connected": len(connected),
            "disconnected": len(disconnected),
            "cameras": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "state": c.get("state"),
                    "model": c.get("type") or c.get("modelKey"),
                    "mac": c.get("mac"),
                    "is_mic_enabled": c.get("isMicEnabled"),
                    "is_recording": c.get("isRecording"),
                }
                for c in cameras
            ],
        }

    async def get_system_info(self) -> dict[str, Any]:
        """Get Protect system information.

        Returns:
            System info including camera/sensor counts
        """
        cameras = await self.get_cameras()
        lights = await self.get_lights()
        sensors = await self.get_sensors()
        chimes = await self.get_chimes()
        viewers = await self.get_viewers()
        liveviews = await self.get_liveviews()

        connected_cams = [c for c in cameras if c.get("state") == "CONNECTED"]

        return {
            "device_name": self.device.name,
            "device_url": self.device.url,
            "cameras": {
                "total": len(cameras),
                "connected": len(connected_cams),
                "disconnected": len(cameras) - len(connected_cams),
            },
            "accessories": {
                "lights": len(lights),
                "sensors": len(sensors),
                "chimes": len(chimes),
                "viewers": len(viewers),
            },
            "liveviews": len(liveviews),
        }
