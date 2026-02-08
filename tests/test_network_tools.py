import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from unifi_mcp.tools.network.devices import list_devices
from unifi_mcp.tools.network.clients import list_clients


@pytest.mark.asyncio
async def test_list_devices_tool(mock_mcp_context):
    """Test the list_devices tool handler."""
    # Mock the client response
    devices_data = [{"mac": "00:11:22:33:44:55", "name": "AP-1", "type": "uap", "state": "ONLINE"}]

    with patch("unifi_mcp.tools.network.devices.UniFiNetworkClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get_devices = AsyncMock(return_value=devices_data)
        mock_client_class.return_value = mock_client

        result = await list_devices(mock_mcp_context)

        assert "AP-1" in str(result)
        mock_client.get_devices.assert_called_once()


@pytest.mark.asyncio
async def test_list_clients_tool(mock_mcp_context):
    """Test the list_clients tool handler."""
    clients_data = [
        {"mac": "aa:bb:cc:dd:ee:ff", "name": "Phone", "ip": "10.0.0.1", "is_online": True}
    ]

    with patch("unifi_mcp.tools.network.clients.UniFiNetworkClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get_clients = AsyncMock(return_value=clients_data)
        mock_client_class.return_value = mock_client

        result = await list_clients(mock_mcp_context)

        assert "Phone" in str(result)
        assert "10.0.0.1" in str(result)
        mock_client.get_clients.assert_called_once()
