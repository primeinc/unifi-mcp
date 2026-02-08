import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# final attempt at configuration
from unifi_mcp.tools.network.insights import analyze_network_issues, troubleshoot_client


@pytest.mark.asyncio
async def test_analyze_network_issues_complex(mock_mcp_context):
    """Test analyze_network_issues with various hardware states."""
    devices = [
        # Offline device (Critical)
        {"name": "Offline AP", "state": "OFFLINE", "mac": "00:11:22", "adopted": True},
        # High CPU device (Warning)
        {
            "name": "Busy SW",
            "state": "ONLINE",
            "mac": "33:44:55",
            "system-stats": {"cpu": "95", "mem": "90"},
        },
        # Upgradable device (Warning)
        {
            "name": "Old AP",
            "state": "ONLINE",
            "mac": "66:77:88",
            "upgradable": True,
            "version": "1.0",
        },
        # AP on same channel (congestion) (Info)
        {
            "name": "AP 1",
            "state": "ONLINE",
            "mac": "aa:11",
            "type": "uap",
            "radio_table": [{"channel": 6}],
        },
        {
            "name": "AP 2",
            "state": "ONLINE",
            "mac": "aa:22",
            "type": "uap",
            "radio_table": [{"channel": 6}],
        },
    ]
    clients = [{"name": "Weak Client", "is_wired": False, "rssi": -85, "ap_name": "AP 1"}]
    health = [
        # WAN issue (Critical)
        {"subsystem": "wan", "status": "critical", "wan_ip": "0.0.0.0"}
    ]
    alarms = [
        # Active alarm (Categorized as an 'issue' entry, which current code counts as critical_issue)
        {"key": "EVT_GW_WanTransition", "msg": "WAN transition", "archived": False}
    ]

    with patch("unifi_mcp.tools.network.insights.UniFiNetworkClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get_devices = AsyncMock(return_value=devices)
        mock_client.get_clients = AsyncMock(return_value=clients)
        mock_client.get_site_health = AsyncMock(return_value=health)
        mock_client.get_alarms = AsyncMock(return_value=alarms)
        mock_client.get_events = AsyncMock(return_value=[])
        mock_client_class.return_value = mock_client

        result = await analyze_network_issues(mock_mcp_context)

        # Current implementation counts: 1 (offline) + 1 (wan) + 1 (alarm) = 3
        assert result["summary"]["critical_issues"] == 3
        # Warnings: 1 (cpu) + 1 (mem) + 1 (firmware) + 1 (poor signal) = 4
        assert result["summary"]["warnings"] == 4
        # Info: 1 (congestion)
        assert result["summary"]["informational"] == 1

        # Verify specific details
        assert any(i["category"] == "wan" for i in result["issues"])
        assert any(w["category"] == "performance" for w in result["warnings"])


@pytest.mark.asyncio
async def test_troubleshoot_client_deep(mock_mcp_context):
    """Test troubleshoot_client logic for a problematic wireless client."""
    client_data = {
        "name": "LaggyPhone",
        "mac": "aa:bb:cc:dd:ee:ff",
        "ip": "10.0.0.50",
        "is_wired": False,
        "is_online": True,
        "rssi": -80,
        "satisfaction": 60,
        "tx_retries": 150,
        "noise": -95,
        "ap_name": "Living Room AP",
    }
    events = [
        {
            "key": "EVT_WU_Disconnected",
            "client": "aabbccddeeff",
            "datetime": "2024-01-01",
            "msg": "Disconnected",
        },
        {
            "key": "EVT_WU_Disconnected",
            "client": "aabbccddeeff",
            "datetime": "2024-01-02",
            "msg": "Disconnected",
        },
        {
            "key": "EVT_WU_Disconnected",
            "client": "aabbccddeeff",
            "datetime": "2024-01-03",
            "msg": "Disconnected",
        },
        {
            "key": "EVT_WU_Disconnected",
            "client": "aabbccddeeff",
            "datetime": "2024-01-04",
            "msg": "Disconnected",
        },
        {
            "key": "EVT_WU_Disconnected",
            "client": "aabbccddeeff",
            "datetime": "2024-01-05",
            "msg": "Disconnected",
        },
        {
            "key": "EVT_WU_Disconnected",
            "client": "aabbccddeeff",
            "datetime": "2024-01-06",
            "msg": "Disconnected",
        },
        {
            "key": "EVT_WU_Roam",
            "client": "aabbccddeeff",
            "datetime": "2024-01-01",
            "ap_from": "AP1",
            "ap_name": "AP2",
        },
    ]

    with patch("unifi_mcp.tools.network.insights.UniFiNetworkClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.get_client = AsyncMock(return_value=client_data)
        mock_client.get_events = AsyncMock(return_value=events)
        mock_client_class.return_value = mock_client

        result = await troubleshoot_client(mock_mcp_context, "aa:bb:cc:dd:ee:ff")

        assert result["client"]["name"] == "LaggyPhone"
        # 3 Warnings (Signal, Satisfaction, Retries) + 1 Error (Disconnects)
        assert len(result["issues_detected"]) >= 4
        assert any(i["issue"] == "Frequent disconnections" for i in result["issues_detected"])
        assert result["wireless"]["snr"] == 15  # -80 - (-95)
