import pytest
from unittest.mock import MagicMock, AsyncMock
from unifi_mcp.tools.network.insights import analyze_network_issues


@pytest.mark.asyncio
async def test_analyze_network_issues_tool(mock_mcp_context):
    """Test the analyze_network_issues tool handler."""
    # Data mocks
    devices = [{"name": "AP-1", "state": "ONLINE", "mac": "00:11:22:33:44:55"}]
    clients = [{"mac": "aa:bb:cc:dd:ee:ff", "is_wired": False, "rssi": -80}]
    health = [{"subsystem": "wan", "status": "ok"}]
    alarms = []

    import unifi_mcp.tools.network.insights as insights_module

    with MagicMock() as mock_client:
        mock_client.get_devices = AsyncMock(return_value=devices)
        mock_client.get_clients = AsyncMock(return_value=clients)
        mock_client.get_site_health = AsyncMock(return_value=health)
        mock_client.get_alarms = AsyncMock(return_value=alarms)

        insights_module.UniFiNetworkClient = MagicMock(return_value=mock_client)

        result = await analyze_network_issues(mock_mcp_context)

        assert result["site"] == "default"
        assert result["summary"]["warnings"] == 1  # Low RSSI client
        assert "poor signal strength" in result["warnings"][0]["issue"]
