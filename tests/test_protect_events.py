import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from unifi_mcp.tools.protect.cameras import (
    get_smart_detections,
    get_event_summary,
    get_recent_activity,
)
from unifi_mcp.config import UniFiDevice


@pytest.mark.asyncio
async def test_get_smart_detections(mock_mcp_context):
    """Test retrieving smart detection events."""
    mock_device = UniFiDevice(
        name="test-protect",
        url="https://unifi.local",
        api_key="fake",
        services=["protect"],
        username="admin",
        password="password",
    )

    with (
        patch("unifi_mcp.tools.protect.cameras.settings") as mock_settings,
        patch("unifi_mcp.tools.protect.cameras.UniFiProtectClient") as mock_client_class,
    ):
        mock_settings.get_protect_devices.return_value = [mock_device]
        mock_settings.default_device_name = "test-protect"

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_client.get_smart_detection_events.return_value = [
            {
                "id": "event1",
                "start": 1600000000000,
                "smartDetectTypes": ["person"],
                "score": 85,
                "camera": "cam1",
            }
        ]
        mock_client.get_cameras.return_value = [{"id": "cam1", "name": "Front Door"}]

        result = await get_smart_detections(mock_mcp_context, hours=24, detection_type="person")

        assert result["total_events"] == 1
        assert result["events"][0]["camera"] == "Front Door"
        assert result["events"][0]["detections"] == ["person"]


@pytest.mark.asyncio
async def test_get_event_summary(mock_mcp_context):
    """Test retrieving protect event summary."""
    mock_device = UniFiDevice(
        name="test-protect",
        url="https://unifi.local",
        api_key="fake",
        services=["protect"],
        username="admin",
        password="password",
    )

    with (
        patch("unifi_mcp.tools.protect.cameras.settings") as mock_settings,
        patch("unifi_mcp.tools.protect.cameras.UniFiProtectClient") as mock_client_class,
    ):
        mock_settings.get_protect_devices.return_value = [mock_device]
        mock_settings.default_device_name = "test-protect"

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get_event_summary.return_value = {"motion": 10, "smart": 5, "doorbell": 1}

        result = await get_event_summary(mock_mcp_context, hours=24)

        assert result["motion"] == 10
        assert result["smart"] == 5


@pytest.mark.asyncio
async def test_get_recent_activity(mock_mcp_context):
    """Test retrieving recent protect activity."""
    mock_device = UniFiDevice(
        name="test-protect",
        url="https://unifi.local",
        api_key="fake",
        services=["protect"],
        username="admin",
        password="password",
    )

    with (
        patch("unifi_mcp.tools.protect.cameras.settings") as mock_settings,
        patch("unifi_mcp.tools.protect.cameras.UniFiProtectClient") as mock_client_class,
    ):
        mock_settings.get_protect_devices.return_value = [mock_device]
        mock_settings.default_device_name = "test-protect"

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get_recent_activity.return_value = [
            {"id": "event1", "type": "motion", "camera": "Front Door"}
        ]

        result = await get_recent_activity(mock_mcp_context, limit=5)

        assert result["total_events"] == 1
        assert result["events"][0]["type"] == "motion"
