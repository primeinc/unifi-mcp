import pytest
import respx
import httpx
from unifi_mcp.auth.local import UniFiLocalAuth
from unifi_mcp.exceptions import UniFiAuthError


@pytest.fixture
async def local_auth(mock_settings):
    """Fixture for UniFiLocalAuth."""
    async with httpx.AsyncClient() as client:
        yield UniFiLocalAuth(client, mock_settings)


@pytest.mark.asyncio
async def test_local_login_udm(local_auth):
    """Test login for UDM-style controller."""
    # Ensure it's treated as UDM
    local_auth.settings.controller_url = "https://udm.local"
    local_auth.settings.username = "admin"
    local_auth.settings.password = "password"

    with respx.mock() as respx_mock:
        # Mock login endpoint
        respx_mock.post("https://udm.local/api/auth/login").mock(
            return_value=httpx.Response(
                200, headers={"Set-Cookie": "unifises=abc", "X-CSRF-Token": "token"}
            )
        )

        await local_auth.login()

        assert local_auth.is_authenticated
        assert local_auth.csrf_token == "token"


@pytest.mark.asyncio
async def test_local_login_failure(local_auth):
    """Test login failure."""
    local_auth.settings.username = "admin"
    local_auth.settings.password = "pass"

    with respx.mock() as respx_mock:
        respx_mock.post(local_auth.settings.auth_url).mock(return_value=httpx.Response(401))

        with pytest.raises(UniFiAuthError) as excinfo:
            await local_auth.login()

        assert "Invalid username or password" in str(excinfo.value)


@pytest.mark.asyncio
async def test_refresh_session(local_auth):
    """Test refreshing the session."""
    local_auth.settings.username = "admin"
    local_auth.settings.password = "pass"

    with respx.mock() as respx_mock:
        # Mock initial login (implied by refresh)
        respx_mock.post(local_auth.settings.auth_url).mock(return_value=httpx.Response(200))

        await local_auth.refresh_session()
        assert local_auth.is_authenticated


@pytest.mark.asyncio
async def test_logout(local_auth):
    """Test logout."""
    local_auth._is_authenticated = True
    local_auth.settings.controller_url = "https://unifi.local"
    local_auth.settings.is_udm = True

    with respx.mock() as respx_mock:
        # Mock the UDM logout URL
        logout_url = "https://unifi.local/api/auth/logout"
        respx_mock.post(logout_url).mock(return_value=httpx.Response(200))

        await local_auth.logout()
        assert not local_auth.is_authenticated
