import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from unifi_mcp.tools.network.stats import get_network_health


@pytest.mark.asyncio
async def test_get_network_health_tool(mock_mcp_context):
    """Test the get_network_health tool handler."""
    health_data = [{"subsystem": "wan", "status": "ok", "wan_ip": "1.1.1.1"}]
    devices = [{"state": 1, "adopted": True}]
    clients = [{"mac": "mac1", "is_wired": True}]

    with patch("unifi_mcp.tools.network.stats.UniFiNetworkClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get_site_health = AsyncMock(return_value=health_data)
        mock_client.get_devices_basic = AsyncMock(return_value=devices)
        mock_client.get_clients = AsyncMock(return_value=clients)
        mock_client_class.return_value = mock_client

        result = await get_network_health(mock_mcp_context)

        assert result["overall_status"] == "healthy"
        assert result["devices"]["total"] == 1
        assert result["clients"]["total"] == 1
        assert result["wan"]["wan_ip"] == "1.1.1.1"
