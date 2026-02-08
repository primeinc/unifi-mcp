import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from unifi_mcp.tools.network.sites import list_sites, get_site_health


@pytest.mark.asyncio
async def test_list_sites_tool(mock_mcp_context):
    """Test the list_sites tool handler."""
    sites_data = [{"name": "Default", "desc": "Main Site", "role": "admin"}]

    with patch("unifi_mcp.tools.network.sites.UniFiNetworkClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get_sites = AsyncMock(return_value=sites_data)
        mock_client_class.return_value = mock_client

        result = await list_sites(mock_mcp_context)

        assert len(result) == 1
        assert result[0]["name"] == "Default"
        mock_client.get_sites.assert_called_once()


@pytest.mark.asyncio
async def test_get_site_health_tool(mock_mcp_context):
    """Test the get_site_health tool handler."""
    health_data = [
        {"subsystem": "lan", "status": "ok", "num_adopted": 5},
        {"subsystem": "wan", "status": "warning", "wan_ip": "1.1.1.1"},
    ]

    with patch("unifi_mcp.tools.network.sites.UniFiNetworkClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get_site_health = AsyncMock(return_value=health_data)
        mock_client_class.return_value = mock_client

        result = await get_site_health(mock_mcp_context)

        assert result["overall_status"] == "issues_detected"
        assert result["subsystems"]["lan"]["status"] == "ok"
        assert result["subsystems"]["wan"]["wan_ip"] == "1.1.1.1"
        assert len(result["issues"]) == 1
