import httpx
import pytest
from unittest.mock import AsyncMock
from cachetools import TTLCache

from unifi_mcp.auth.local import UniFiCloudAuth
from unifi_mcp.clients.base import AppContext
from unifi_mcp.clients.protect import UniFiProtectClient
from unifi_mcp.config import UniFiDevice, UniFiSettings


@pytest.fixture
def mock_settings():
    """Mock settings with a single local device."""
    settings = UniFiSettings(
        controller_url="https://unifi.local",
        cloud_api_key="fake-key",
        mode="local_api_key",
        site="default",
    )
    return settings


@pytest.fixture
def mock_device():
    """Mock UniFi device."""
    return UniFiDevice(
        name="test-device",
        url="https://unifi.local",
        api_key="fake-key",
        services=["network", "protect"],
        username="admin",
        password="password",
    )


@pytest.fixture
def mock_auth():
    """Mock cloud auth."""
    return UniFiCloudAuth(api_key="fake-key")


@pytest.fixture
def mock_cache():
    """Mock cache."""
    return TTLCache(maxsize=100, ttl=30)


@pytest.fixture
async def mock_ctx(mock_settings, mock_auth, mock_cache):
    """Mock application context."""
    async with httpx.AsyncClient(base_url=mock_settings.api_base_url) as client:
        yield AppContext(client=client, auth=mock_auth, settings=mock_settings, cache=mock_cache)


@pytest.fixture
def mock_mcp_context(mock_ctx):
    """Mock MCP Context with lifespan_context."""
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.request_context.lifespan_context = mock_ctx
    return ctx


@pytest.fixture
async def mock_protect_client(mock_device):
    """Fixture for UniFiProtectClient."""
    async with httpx.AsyncClient() as client:
        yield UniFiProtectClient(client, mock_device)
