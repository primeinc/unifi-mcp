"""Configuration settings for UniFi MCP Server."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UniFiSettings(BaseSettings):
    """UniFi MCP Server configuration.

    Settings can be configured via environment variables with UNIFI_ prefix.

    Supported modes:
    - local: Session-based auth with username/password (traditional)
    - local_api_key: UniFi OS Integration API with API key (recommended for UCG/UDM)
    - cloud: Ubiquiti Cloud API (api.ui.com)
    """

    model_config = SettingsConfigDict(
        env_prefix="UNIFI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Connection mode
    mode: Literal["local", "local_api_key", "cloud"] = Field(
        default="local_api_key",
        description="Connection mode: 'local' for session auth, 'local_api_key' for Integration API, 'cloud' for api.ui.com",
    )

    # Local controller settings
    controller_url: str | None = Field(
        default=None,
        description="URL of the UniFi controller (e.g., https://192.168.1.1)",
    )
    username: str | None = Field(
        default=None,
        description="Username for local controller authentication",
    )
    password: str | None = Field(
        default=None,
        description="Password for local controller authentication",
    )
    site: str = Field(
        default="default",
        description="UniFi site name (use 'default' for single-site setups)",
    )
    verify_ssl: bool = Field(
        default=False,
        description="Verify SSL certificates (set False for self-signed certs)",
    )
    is_udm: bool = Field(
        default=True,
        description="True for UniFi OS devices (UDM, UCG), False for traditional controller",
    )

    # Cloud API settings
    cloud_api_key: str | None = Field(
        default=None,
        description="API key for Ubiquiti Cloud API (api.ui.com)",
    )

    # Performance settings
    request_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )
    max_connections: int = Field(
        default=10,
        description="Maximum number of HTTP connections",
    )
    cache_ttl: int = Field(
        default=30,
        description="Default cache TTL in seconds",
    )

    @property
    def api_base_url(self) -> str:
        """Get the base URL for API requests."""
        if self.mode == "cloud":
            return "https://api.ui.com"

        if not self.controller_url:
            raise ValueError("controller_url is required for local/local_api_key mode")

        base = self.controller_url.rstrip("/")

        # local_api_key mode uses the Integration API
        if self.mode == "local_api_key":
            return f"{base}/proxy/network/integration"

        # Traditional local mode
        if self.is_udm:
            return f"{base}/proxy/network"

        return base

    @property
    def auth_url(self) -> str:
        """Get the authentication URL."""
        if self.mode in ("cloud", "local_api_key"):
            # API key modes don't use auth URL
            return ""

        if not self.controller_url:
            raise ValueError("controller_url is required for local mode")

        base = self.controller_url.rstrip("/")

        # UniFi OS uses different auth endpoint
        if self.is_udm:
            return f"{base}/api/auth/login"

        # Traditional controller
        return f"{base}/api/login"

    @property
    def uses_api_key(self) -> bool:
        """Check if the current mode uses API key authentication."""
        return self.mode in ("cloud", "local_api_key")


# Global settings instance
settings = UniFiSettings()
