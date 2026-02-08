"""Tests for Protect client session authentication."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from http.cookies import SimpleCookie
import httpx
from unifi_mcp.clients.protect import UniFiProtectClient
from unifi_mcp.config import UniFiDevice


class TestProtectSessionAuth:
    """Test session authentication and cookie reuse in Protect client."""

    @pytest.mark.asyncio
    async def test_session_auth_reuses_existing_cookies(self):
        """Test that existing session cookies are reused instead of re-authenticating."""
        # Create a mock HTTP client with existing cookies
        mock_client = Mock(spec=httpx.AsyncClient)
        
        # Create mock cookies with TOKEN and CSRF
        mock_cookie_jar = []
        token_cookie = Mock()
        token_cookie.name = "TOKEN"
        csrf_cookie = Mock()
        csrf_cookie.name = "CSRF_TOKEN"
        mock_cookie_jar.extend([token_cookie, csrf_cookie])
        
        mock_client.cookies = Mock()
        mock_client.cookies.jar = mock_cookie_jar
        
        # Create device with credentials (api_key is required by model)
        device = UniFiDevice(
            name="test-device",
            url="https://192.168.1.1",
            api_key="test-key",
            username="admin",
            password="password"
        )
        
        # Create Protect client
        protect_client = UniFiProtectClient(mock_client, device)
        
        # Call _ensure_session_auth
        await protect_client._ensure_session_auth()
        
        # Verify that no POST request was made (cookies were reused)
        mock_client.post.assert_not_called()
        
        # Verify session is marked as authenticated
        assert protect_client._session_authenticated is True

    @pytest.mark.asyncio
    async def test_session_auth_fails_without_credentials(self):
        """Test that session auth raises error when credentials are missing."""
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_client.cookies = Mock()
        mock_client.cookies.jar = []  # No existing cookies
        
        # Create device without credentials
        device = UniFiDevice(
            name="test-device",
            url="https://192.168.1.1",
            api_key="test-key"
        )
        
        # Create Protect client
        protect_client = UniFiProtectClient(mock_client, device)
        
        # Should raise error when trying to authenticate without credentials
        from unifi_mcp.exceptions import UniFiAuthError
        with pytest.raises(UniFiAuthError, match="Username and password required"):
            await protect_client._ensure_session_auth()

    @pytest.mark.asyncio
    async def test_session_auth_performs_login_without_cookies(self):
        """Test that login is performed when no session cookies exist."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.cookies = Mock()
        mock_client.cookies.jar = []  # No existing cookies
        
        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.headers = {"X-CSRF-Token": "test-csrf-token"}
        mock_client.post = AsyncMock(return_value=mock_response)
        
        # Create device with credentials (api_key is required by model)
        device = UniFiDevice(
            name="test-device",
            url="https://192.168.1.1",
            api_key="test-key",
            username="admin",
            password="password"
        )
        
        # Create Protect client
        protect_client = UniFiProtectClient(mock_client, device)
        
        # Call _ensure_session_auth
        await protect_client._ensure_session_auth()
        
        # Verify POST request was made to login endpoint
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "api/auth/login" in call_args[0][0]
        
        # Verify credentials were sent
        assert call_args[1]["json"]["username"] == "admin"
        assert call_args[1]["json"]["password"] == "password"
        
        # Verify session is marked as authenticated
        assert protect_client._session_authenticated is True

    @pytest.mark.asyncio
    async def test_session_auth_only_runs_once(self):
        """Test that session auth check short-circuits on subsequent calls."""
        mock_client = Mock(spec=httpx.AsyncClient)
        
        # Create device (api_key is required by model)
        device = UniFiDevice(
            name="test-device",
            url="https://192.168.1.1",
            api_key="test-key",
            username="admin",
            password="password"
        )
        
        # Create Protect client and mark as already authenticated
        protect_client = UniFiProtectClient(mock_client, device)
        protect_client._session_authenticated = True
        
        # Call _ensure_session_auth
        await protect_client._ensure_session_auth()
        
        # Verify no cookies check or POST was made
        # (cookies.jar is not accessed when already authenticated)
        mock_client.post.assert_not_called()
