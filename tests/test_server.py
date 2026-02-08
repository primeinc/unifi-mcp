import pytest
from unittest.mock import MagicMock, patch
from unifi_mcp.server import mcp, main


def test_mcp_instance():
    """Test that the MCP instance is correctly initialized."""
    assert mcp.name == "UniFi MCP Server"
    # Verify some tools are registered
    tool_names = [tool.name for tool in mcp._tool_manager.list_tools()]
    assert "list_devices" in tool_names
    assert "list_clients" in tool_names
    assert "list_cameras" in tool_names


@patch("unifi_mcp.server.mcp.run")
@patch("unifi_mcp.server.settings")
def test_main_execution(mock_settings, mock_run):
    """Test the main entry point."""
    mock_settings.devices = [MagicMock(name="test-device")]
    mock_settings.get_device_names.return_value = ["test-device"]

    main()

    mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_tool_registration_wrappers():
    """Test that tool wrappers correctly call their respective modules."""
    # This is a bit redundant but helps with coverage of the wrapper functions in server.py
    from unifi_mcp.server import list_devices

    with patch(
        "unifi_mcp.tools.network.devices.list_devices", new_callable=AsyncMock
    ) as mock_device_list:
        ctx = MagicMock()
        await list_devices(ctx, site="test-site")
        mock_device_list.assert_called_once_with(ctx, "test-site")


# Helper for AsyncMock in older python if needed,
# but 3.12 has it in unittest.mock
from unittest.mock import AsyncMock
