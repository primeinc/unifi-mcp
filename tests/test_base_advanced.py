import httpx
import pytest
import respx
from cachetools import TTLCache
from unittest.mock import MagicMock, AsyncMock, patch

from unifi_mcp.clients.base import AppContext, UniFiHTTPClient, create_app_lifespan
from unifi_mcp.config import UniFiSettings
from unifi_mcp.exceptions import (
    UniFiAPIError,
    UniFiAuthError,
    UniFiConnectionError,
    UniFiRateLimitError,
)

@pytest.fixture
def mock_ctx_base():
    settings = UniFiSettings(controller_url="https://unifi.local", cloud_api_key="key", mode="local_api_key")
    auth = MagicMock()
    auth.get_request_headers.return_value = {"X-API-KEY": "key"}
    return AppContext(
        client=httpx.AsyncClient(),
        auth=auth,
        settings=settings,
        cache=TTLCache(maxsize=10, ttl=10)
    )

@pytest.mark.asyncio
async def test_make_request_errors(mock_ctx_base):
    """Test connection and timeout errors in _make_request (lines 100-103)."""
    client = UniFiHTTPClient(mock_ctx_base)
    url = f"{mock_ctx_base.settings.api_base_url}/test"
    
    with respx.mock() as respx_mock:
        respx_mock.get(url).mock(side_effect=httpx.ConnectError("Fail"))
        with pytest.raises(UniFiConnectionError, match="Failed to connect"):
            await client._make_request("GET", url)
            
        respx_mock.get(url).mock(side_effect=httpx.TimeoutException("Timeout"))
        with pytest.raises(UniFiConnectionError, match="Request timed out"):
            await client._make_request("GET", url)

@pytest.mark.asyncio
async def test_request_refresh_flow(mock_ctx_base):
    """Test 401 refresh logic (lines 132-137)."""
    from unifi_mcp.auth.local import UniFiLocalAuth
    mock_ctx_base.auth = MagicMock(spec=UniFiLocalAuth)
    mock_ctx_base.auth.get_request_headers.return_value = {"Auth": "expired"}
    mock_ctx_base.auth.refresh_session = AsyncMock(return_value=True)
    
    client = UniFiHTTPClient(mock_ctx_base)
    url = f"{mock_ctx_base.settings.api_base_url}/test"
    
    with respx.mock() as respx_mock:
        # First call 401, second call 200
        respx_mock.get(url).side_effect = [
            httpx.Response(401),
            httpx.Response(200, json={"meta": {"rc": "ok"}, "data": "success"})
        ]
        
        result = await client.request("GET", "/test")
        assert result == {"meta": {"rc": "ok"}, "data": "success"}
        mock_ctx_base.auth.refresh_session.assert_called_once()

@pytest.mark.asyncio
async def test_request_refresh_fail(mock_ctx_base):
    """Test 401 refresh fail."""
    from unifi_mcp.auth.local import UniFiLocalAuth
    mock_ctx_base.auth = MagicMock(spec=UniFiLocalAuth)
    mock_ctx_base.auth.refresh_session = AsyncMock(side_effect=UniFiAuthError("Fail"))
    
    client = UniFiHTTPClient(mock_ctx_base)
    with respx.mock() as respx_mock:
        respx_mock.get(f"{mock_ctx_base.settings.api_base_url}/test").mock(return_value=httpx.Response(401))
        with pytest.raises(UniFiAuthError, match="Session expired and refresh failed"):
            await client.request("GET", "/test")

@pytest.mark.asyncio
async def test_rate_limit(mock_ctx_base):
    """Test rate limiting (lines 141-142)."""
    client = UniFiHTTPClient(mock_ctx_base)
    with respx.mock() as respx_mock:
        respx_mock.get(f"{mock_ctx_base.settings.api_base_url}/test").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "10"})
        )
        with pytest.raises(UniFiRateLimitError, match="Rate limited"):
            await client.request("GET", "/test")

@pytest.mark.asyncio
async def test_other_methods(mock_ctx_base):
    """Test PUT/DELETE methods (lines 159, 167)."""
    client = UniFiHTTPClient(mock_ctx_base)
    with respx.mock() as respx_mock:
        respx_mock.put(f"{mock_ctx_base.settings.api_base_url}/test").mock(return_value=httpx.Response(200, json={"meta": {"rc": "ok"}}))
        respx_mock.delete(f"{mock_ctx_base.settings.api_base_url}/test").mock(return_value=httpx.Response(200, json={"meta": {"rc": "ok"}}))
        
        await client.put("/test")
        await client.delete("/test")

@pytest.mark.asyncio
async def test_parse_response_errors(mock_ctx_base):
    """Test _parse_response errors (lines 188-189, 194-198, 203-204)."""
    client = UniFiHTTPClient(mock_ctx_base)
    
    # Invalid JSON (188-189)
    with pytest.raises(UniFiAPIError, match="Failed to parse response"):
        client._parse_response(httpx.Response(200, content="not json"))
        
    # Cloud error (194-198)
    mock_ctx_base.settings.mode = "cloud"
    with pytest.raises(UniFiAPIError, match="Cloud Error"):
        client._parse_response(httpx.Response(200, json={"error": "Cloud Error"}))
        
    # Local meta error (203-204)
    mock_ctx_base.settings.mode = "local_api_key"
    with pytest.raises(UniFiAPIError, match="Meta Error"):
        client._parse_response(httpx.Response(200, json={"meta": {"rc": "error", "msg": "Meta Error"}}))

@pytest.mark.asyncio
async def test_handle_error_response(mock_ctx_base):
    """Test _handle_error_response (lines 218-231)."""
    client = UniFiHTTPClient(mock_ctx_base)
    
    # 403 (228-229)
    with pytest.raises(UniFiAuthError, match="Access forbidden"):
        await client._handle_error_response(httpx.Response(403, content="No permission"))
        
    # Generic error parsing (218-224)
    with pytest.raises(UniFiAPIError, match="Something went wrong"):
        await client._handle_error_response(httpx.Response(500, json={"message": "Something went wrong"}))

@pytest.mark.asyncio
async def test_lifespan_cloud(mock_ctx_base):
    """Test create_app_lifespan in cloud mode (lines 249-304)."""
    from unifi_mcp.config import UniFiSettings
    test_settings = UniFiSettings(mode="cloud", cloud_api_key="mykey")
    
    with patch("unifi_mcp.clients.base.settings", test_settings):
        async with create_app_lifespan(MagicMock()) as ctx:
            assert ctx.settings.mode == "cloud"
            assert ctx.auth.api_key == "mykey"

@pytest.mark.asyncio
async def test_lifespan_local_success():
    """Test create_app_lifespan with local auth flow (lines 269-272, 288-289, 301)."""
    from unifi_mcp.config import UniFiSettings
    test_settings = UniFiSettings(mode="local", controller_url="https://u", username="u", password="p")
    
    with patch("unifi_mcp.clients.base.settings", test_settings):
        with respx.mock() as respx_mock:
            # Mock login
            respx_mock.post("https://u/api/auth/login").mock(return_value=httpx.Response(200))
            # Mock logout
            respx_mock.post("https://u/api/auth/logout").mock(return_value=httpx.Response(200))
            
            async with create_app_lifespan(MagicMock()) as ctx:
                assert ctx.settings.mode == "local"
                assert ctx.auth.is_authenticated

@pytest.mark.asyncio
async def test_cloud_success_return(mock_ctx_base):
    """Test cloud mode successful data return (line 198)."""
    mock_ctx_base.settings.mode = "cloud"
    client = UniFiHTTPClient(mock_ctx_base)
    url = f"{mock_ctx_base.settings.api_base_url}/test"
    
    with respx.mock() as respx_mock:
        respx_mock.get(url).mock(return_value=httpx.Response(200, json={"data": "ok"}))
        result = await client.get("/test")
        assert result == {"data": "ok"}

@pytest.mark.asyncio
async def test_all_methods_coverage(mock_ctx_base):
    """Explicitly hit post, put, delete wrappers (lines 149, 155, 159)."""
    client = UniFiHTTPClient(mock_ctx_base)
    with respx.mock() as respx_mock:
        respx_mock.post(f"{mock_ctx_base.settings.api_base_url}/p").mock(return_value=httpx.Response(200, json={"meta": {"rc": "ok"}}))
        respx_mock.put(f"{mock_ctx_base.settings.api_base_url}/u").mock(return_value=httpx.Response(200, json={"meta": {"rc": "ok"}}))
        respx_mock.delete(f"{mock_ctx_base.settings.api_base_url}/d").mock(return_value=httpx.Response(200, json={"meta": {"rc": "ok"}}))
        
        await client.post("/p")
        await client.put("/u")
        await client.delete("/d")

@pytest.mark.asyncio
async def test_handle_401_error(mock_ctx_base):
    """Test 401 handling in error response."""
    client = UniFiHTTPClient(mock_ctx_base)
    with pytest.raises(UniFiAuthError, match="Authentication required"):
        await client._handle_error_response(httpx.Response(401, content="Unauthorized"))
