import httpx
import pytest
import respx
from unittest.mock import MagicMock

from unifi_mcp.auth.local import UniFiLocalAuth, UniFiCloudAuth
from unifi_mcp.config import UniFiSettings
from unifi_mcp.exceptions import UniFiAuthError, UniFiConnectionError

@pytest.fixture
def advanced_settings():
    return UniFiSettings(
        controller_url="https://unifi.local",
        username="admin",
        password="password",
        is_udm=True
    )

@pytest.fixture
async def local_auth(advanced_settings):
    async with httpx.AsyncClient() as client:
        yield UniFiLocalAuth(client, advanced_settings)

@pytest.mark.asyncio
async def test_login_no_creds(local_auth):
    """Test login with missing credentials (line 51)."""
    local_auth.settings.username = None
    with pytest.raises(UniFiAuthError, match="Username and password are required"):
        await local_auth.login()

@pytest.mark.asyncio
async def test_login_timeout(local_auth):
    """Test login timeout (line 66)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(side_effect=httpx.TimeoutException("Timeout"))
        with pytest.raises(UniFiConnectionError, match="Connection timed out"):
            await local_auth.login()

@pytest.mark.asyncio
async def test_login_forbidden(local_auth):
    """Test 403 Forbidden login (line 82)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(return_value=httpx.Response(403))
        with pytest.raises(UniFiAuthError, match="Access forbidden"):
            await local_auth.login()

@pytest.mark.asyncio
async def test_login_error_json(local_auth):
    """Test login with error message in JSON (lines 101-103)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(
            return_value=httpx.Response(500, json={"meta": {"msg": "Server Exploded"}})
        )
        with pytest.raises(UniFiAuthError, match="Authentication failed: Server Exploded"):
            await local_auth.login()

@pytest.mark.asyncio
async def test_login_error_invalid_json(local_auth):
    """Test login with invalid JSON response (lines 104-112)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(
            return_value=httpx.Response(500, content="Not JSON")
        )
        with pytest.raises(UniFiAuthError, match="Authentication failed with status 500"):
            await local_auth.login()

@pytest.mark.asyncio
async def test_logout_not_auth(local_auth):
    """Test logout when not authenticated (line 117)."""
    local_auth._is_authenticated = False
    await local_auth.logout()
    assert not local_auth.is_authenticated

@pytest.mark.asyncio
async def test_logout_non_udm(local_auth):
    """Test logout for non-UDM (line 127-132)."""
    local_auth._is_authenticated = True
    local_auth.settings.is_udm = False
    with respx.mock() as respx_mock:
        respx_mock.post("https://unifi.local/api/logout").mock(return_value=httpx.Response(200))
        await local_auth.logout()
        assert not local_auth.is_authenticated

@pytest.mark.asyncio
async def test_logout_exception(local_auth):
    """Test logout with exception (line 135-136)."""
    local_auth._is_authenticated = True
    with respx.mock() as respx_mock:
        respx_mock.post("https://unifi.local/api/auth/logout").mock(side_effect=Exception("Network fail"))
        await local_auth.logout()
        assert not local_auth.is_authenticated

@pytest.mark.asyncio
async def test_check_session_not_auth(local_auth):
    """Test check_session when not auth (line 172-173)."""
    local_auth._is_authenticated = False
    assert await local_auth.check_session() is False

@pytest.mark.asyncio
async def test_check_session_valid(local_auth):
    """Test check_session valid (line 175-180)."""
    local_auth._is_authenticated = True
    with respx.mock() as respx_mock:
        respx_mock.get(f"{local_auth.settings.api_base_url}/api/self").mock(return_value=httpx.Response(200))
        assert await local_auth.check_session() is True

@pytest.mark.asyncio
async def test_check_session_invalid(local_auth):
    """Test check_session invalid status (line 181-183)."""
    local_auth._is_authenticated = True
    with respx.mock() as respx_mock:
        respx_mock.get(f"{local_auth.settings.api_base_url}/api/self").mock(return_value=httpx.Response(401))
        assert await local_auth.check_session() is False

@pytest.mark.asyncio
async def test_cloud_auth_ensure_error():
    """Test CloudAuth ensure_authenticated error (line 224-225)."""
    auth = UniFiCloudAuth(api_key=None)
    with pytest.raises(UniFiAuthError, match="Cloud API key is required"):
        await auth.ensure_authenticated()

@pytest.mark.asyncio
async def test_login_success_with_csrf(local_auth):
    """Test login success with CSRF token (lines 91-96)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(
            return_value=httpx.Response(200, headers={"X-CSRF-Token": "test-csrf"})
        )
        await local_auth.login()
        assert local_auth.is_authenticated
        assert local_auth.csrf_token == "test-csrf"
        assert local_auth.get_request_headers()["X-CSRF-Token"] == "test-csrf"

@pytest.mark.asyncio
async def test_login_connect_error(local_auth):
    """Test login connection error (line 83)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(side_effect=httpx.ConnectError("Failed"))
        with pytest.raises(UniFiConnectionError, match="Failed to connect"):
            await local_auth.login()

@pytest.mark.asyncio
async def test_logout_no_url(local_auth):
    """Test logout with no controller_url (line 122)."""
    local_auth._is_authenticated = True
    local_auth.settings.controller_url = None
    with respx.mock() as respx_mock:
        # It will try to post to "/api/auth/logout"
        respx_mock.post("/api/auth/logout").mock(return_value=httpx.Response(200))
        await local_auth.logout()
        assert not local_auth.is_authenticated

@pytest.mark.asyncio
async def test_refresh_session_explicit(local_auth):
    """Test explicit refresh_session call (lines 149-153)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(return_value=httpx.Response(200))
        assert await local_auth.refresh_session() is True
        assert local_auth.is_authenticated

@pytest.mark.asyncio
async def test_check_session_exception(local_auth):
    """Test check_session with generic exception (lines 182-183)."""
    local_auth._is_authenticated = True
    with respx.mock() as respx_mock:
        respx_mock.get(f"{local_auth.settings.api_base_url}/api/self").mock(side_effect=Exception("Boom"))
        assert await local_auth.check_session() is False

@pytest.mark.asyncio
async def test_cloud_auth_full():
    """Test CloudAuth properties (lines 211, 220)."""
    auth = UniFiCloudAuth(api_key="key123")
    assert auth.is_authenticated is True
    headers = auth.get_request_headers()
    assert headers["X-API-KEY"] == "key123"
    await auth.ensure_authenticated() # Should not raise

@pytest.mark.asyncio
async def test_login_401(local_auth):
    """Test login 401 error (line 99)."""
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(return_value=httpx.Response(401))
        with pytest.raises(UniFiAuthError, match="Invalid username or password"):
            await local_auth.login()

@pytest.mark.asyncio
async def test_ensure_authenticated_triggers_login(local_auth):
    """Test ensure_authenticated calls login (line 163-164)."""
    local_auth._is_authenticated = False
    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(return_value=httpx.Response(200))
        await local_auth.ensure_authenticated()
        assert local_auth.is_authenticated
