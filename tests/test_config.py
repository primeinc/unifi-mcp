"""Tests for config module and authentication setup."""

import pytest

from unifi_mcp.config import UniFiSettings


class TestUniFiSettings:
    """Test UniFi configuration and settings."""

    def test_auth_url_with_udm(self):
        """Test auth_url property returns correct URL for UDM."""
        settings = UniFiSettings(
            controller_url="https://192.168.1.1",
            is_udm=True
        )
        assert settings.auth_url == "https://192.168.1.1/api/auth/login"

    def test_auth_url_without_udm(self):
        """Test auth_url property returns correct URL for non-UDM."""
        settings = UniFiSettings(
            controller_url="https://192.168.1.1",
            is_udm=False
        )
        assert settings.auth_url == "https://192.168.1.1/api/login"

    def test_auth_url_strips_trailing_slash(self):
        """Test auth_url property handles trailing slashes."""
        settings = UniFiSettings(
            controller_url="https://192.168.1.1/",
            is_udm=True
        )
        assert settings.auth_url == "https://192.168.1.1/api/auth/login"

    def test_auth_url_requires_controller_url(self):
        """Test auth_url raises error when controller_url is not set."""
        settings = UniFiSettings()
        with pytest.raises(ValueError, match="No controller URL configured"):
            _ = settings.auth_url

    def test_uses_api_key_cloud(self):
        """Test uses_api_key returns True for cloud mode."""
        settings = UniFiSettings(mode="cloud")
        assert settings.uses_api_key is True

    def test_uses_api_key_local_api_key(self):
        """Test uses_api_key returns True for local_api_key mode."""
        settings = UniFiSettings(mode="local_api_key")
        assert settings.uses_api_key is True

    def test_uses_api_key_local(self):
        """Test uses_api_key returns False for local mode."""
        settings = UniFiSettings(mode="local")
        assert settings.uses_api_key is False
