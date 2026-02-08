import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Absolute imports from the installed package
from unifi_mcp.tools.protect.cameras import (
    list_cameras,
    get_protect_system_info,
    get_protect_accessories,
    get_smart_detections,
    get_camera_health_summary,
    get_event_summary,
)


@pytest.mark.asyncio
async def test_list_cameras_tool(mock_mcp_context):
    """Test the list_cameras tool handler."""
    summary_data = {
        "total_cameras": 1,
        "connected": 1,
        "disconnected": 0,
        "cameras": [{"id": "cam-1", "name": "Front", "state": "CONNECTED"}],
    }

    with patch("unifi_mcp.tools.protect.cameras._get_protect_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_camera_summary = AsyncMock(return_value=summary_data)
        mock_get_client.return_value = mock_client

        result = await list_cameras(mock_mcp_context)

        assert result["total_cameras"] == 1
        assert result["cameras"][0]["name"] == "Front"
        mock_client.get_camera_summary.assert_called_once()


@pytest.mark.asyncio
async def test_get_protect_accessories_tool(mock_mcp_context):
    """Test the get_protect_accessories tool handler."""
    lights = [{"id": "light-1", "name": "Floodlight"}]
    sensors = [{"id": "sensor-1", "name": "Motion Sensor"}]

    with patch("unifi_mcp.tools.protect.cameras._get_protect_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_lights = AsyncMock(return_value=lights)
        mock_client.get_sensors = AsyncMock(return_value=sensors)
        mock_client.get_chimes = AsyncMock(return_value=[])
        mock_client.get_viewers = AsyncMock(return_value=[])
        mock_get_client.return_value = mock_client

        result = await get_protect_accessories(mock_mcp_context)

        assert len(result["lights"]) == 1
        assert len(result["sensors"]) == 1
        assert result["summary"]["total_lights"] == 1


@pytest.mark.asyncio
async def test_get_smart_detections_tool(mock_mcp_context):
    """Test the get_smart_detections tool handler."""
    events = [
        {"camera": "cam-1", "smartDetectTypes": ["person"], "score": 85, "start": 1700000000000}
    ]
    cameras = [{"id": "cam-1", "name": "Front Door"}]

    with patch("unifi_mcp.tools.protect.cameras._get_protect_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_smart_detection_events = AsyncMock(return_value=events)
        mock_client.get_cameras = AsyncMock(return_value=cameras)
        mock_get_client.return_value = mock_client

        result = await get_smart_detections(mock_mcp_context, detection_type="person")

        assert result["total_events"] == 1
        assert result["events"][0]["camera"] == "Front Door"
        assert "person" in result["events"][0]["detections"]


@pytest.mark.asyncio
async def test_get_camera_health_summary_tool(mock_mcp_context):
    """Test health summary logic with disconnected cameras."""
    cameras = [
        {"id": "c1", "name": "Front", "state": "CONNECTED", "type": "g4"},
        {"id": "c2", "name": "Back", "state": "DISCONNECTED", "type": "g3"},
    ]

    with patch("unifi_mcp.tools.protect.cameras._get_protect_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_cameras = AsyncMock(return_value=cameras)
        mock_get_client.return_value = mock_client

        result = await get_camera_health_summary(mock_mcp_context)

        assert result["summary"]["status"] == "degraded"
        assert len(result["issues"]) == 1
        assert "Back" in result["issues"][0]["camera"]


@pytest.mark.asyncio
async def test_get_event_summary_tool(mock_mcp_context):
    """Test the get_event_summary tool handler."""
    summary = {"period_hours": 24, "total_events": 10, "motion_events": 8, "smart_detections": 2}

    with patch("unifi_mcp.tools.protect.cameras._get_protect_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get_event_summary = AsyncMock(return_value=summary)
        mock_get_client.return_value = mock_client

        result = await get_event_summary(mock_mcp_context)

        assert result["total_events"] == 10
        assert result["smart_detections"] == 2
