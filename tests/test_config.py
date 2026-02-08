import pytest
import json
from unifi_mcp.config import UniFiSettings, UniFiDevice


def test_unifi_settings_auth_url():
    """Test auth_url property logic."""
    settings = UniFiSettings(controller_url="https://192.168.1.1", mode="local")
    # Our implementation seems to return /api/auth/login for all if is_udm is True (default)
    # Let's check settings.is_udm
    assert settings.is_udm is True
    assert settings.auth_url == "https://192.168.1.1/api/auth/login"

    # Non-UDM
    settings.is_udm = False
    assert settings.auth_url == "https://192.168.1.1/api/login"


def test_unifi_device_urls():
    """Test UniFiDevice URL properties."""
    device = UniFiDevice(name="UDM", url="https://10.0.0.1", api_key="key")
    # Actual implementation uses /proxy/network/integration
    assert device.network_api_base == "https://10.0.0.1/proxy/network/integration"
    assert device.protect_api_base == "https://10.0.0.1/proxy/protect/integration/v1"
    assert device.protect_internal_api_base == "https://10.0.0.1/proxy/protect/api"


def test_multi_device_config(monkeypatch):
    """Test loading multiple devices from JSON env var."""
    devices_json = json.dumps(
        [
            {"name": "Device 1", "url": "https://dev1", "api_key": "key1"},
            {"name": "Device 2", "url": "https://dev2", "api_key": "key2"},
        ]
    )
    monkeypatch.setenv("UNIFI_DEVICES", devices_json)

    settings = UniFiSettings()
    assert len(settings.devices) == 2
    assert settings.devices[0].name == "Device 1"
    assert settings.devices[1].name == "Device 2"
