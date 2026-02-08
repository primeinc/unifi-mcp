"""Base HTTP client and lifespan management for UniFi MCP Server."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from cachetools import TTLCache
from mcp.server.fastmcp import FastMCP
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from unifi_mcp.auth.local import UniFiCloudAuth, UniFiLocalAuth
from unifi_mcp.config import UniFiSettings, settings
from unifi_mcp.exceptions import (
    UniFiAPIError,
    UniFiAuthError,
    UniFiConnectionError,
    UniFiRateLimitError,
)
from unifi_mcp.utils.privacy import mask_pii_data

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with shared resources.

    This context is created during server startup and made available
    to all tool handlers via the request context.
    """

    client: httpx.AsyncClient
    auth: UniFiLocalAuth | UniFiCloudAuth
    settings: UniFiSettings
    cache: TTLCache


class UniFiHTTPClient:
    """Base HTTP client for UniFi API requests.

    Provides retry logic, authentication handling, and error processing.
    """

    def __init__(self, ctx: AppContext):
        """Initialize the HTTP client.

        Args:
            ctx: Application context with shared resources
        """
        self.ctx = ctx
        self._retry_count = 0

    @property
    def _headers(self) -> dict[str, str]:
        """Get headers for requests."""
        return self.ctx.auth.get_request_headers()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            **kwargs: Additional arguments passed to httpx

        Returns:
            HTTP response

        Raises:
            UniFiConnectionError: If connection fails after retries
            UniFiAuthError: If authentication fails
            UniFiRateLimitError: If rate limited
            UniFiAPIError: For other API errors
        """
        try:
            response = await self.ctx.client.request(
                method,
                url,
                headers=self._headers,
                **kwargs,
            )
        except httpx.ConnectError as e:
            raise UniFiConnectionError(f"Failed to connect: {e}") from e
        except httpx.TimeoutException as e:
            raise UniFiConnectionError(f"Request timed out: {e}") from e

        return response

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (will be appended to base URL)
            **kwargs: Additional arguments (json, params, etc.)

        Returns:
            Parsed JSON response data

        Raises:
            UniFiAPIError: For API errors
        """
        url = f"{self.ctx.settings.api_base_url}{endpoint}"

        response = await self._make_request(method, url, **kwargs)

        # Handle 401 - try to refresh session once
        if response.status_code == 401:
            if isinstance(self.ctx.auth, UniFiLocalAuth):
                logger.info("Session expired, refreshing authentication")
                try:
                    await self.ctx.auth.refresh_session()
                    response = await self._make_request(method, url, **kwargs)
                except UniFiAuthError:
                    raise UniFiAuthError("Session expired and refresh failed")

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise UniFiRateLimitError(
                f"Rate limited, retry after {retry_after}s",
                retry_after=retry_after,
            )

        # Handle other errors
        if response.status_code >= 400:
            await self._handle_error_response(response)

        data = self._parse_response(response)
        return mask_pii_data(data)

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request."""
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a POST request."""
        return await self.request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a PUT request."""
        return await self.request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self.request("DELETE", endpoint, **kwargs)

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse API response.

        UniFi API returns responses in format:
        {
            "meta": {"rc": "ok"},
            "data": [...]
        }

        Cloud API (api.ui.com) returns data directly or in a simpler format.

        Args:
            response: HTTP response

        Returns:
            Parsed response data
        """
        try:
            data = response.json()
        except Exception as e:
            raise UniFiAPIError(f"Failed to parse response: {e}")

        # Cloud API returns data directly without meta wrapper
        if self.ctx.settings.mode == "cloud":
            # Check for error in cloud response
            if isinstance(data, dict) and data.get("error"):
                raise UniFiAPIError(data.get("error", "Unknown API error"), response.status_code, data)
            return data

        # Check for API-level errors (local controller format)
        meta = data.get("meta", {})
        if meta.get("rc") == "error":
            msg = meta.get("msg", "Unknown API error")
            raise UniFiAPIError(msg, response.status_code, data)

        return data

    async def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses.

        Args:
            response: HTTP response with error status

        Raises:
            UniFiAuthError: For 401/403
            UniFiAPIError: For other errors
        """
        try:
            data = response.json()
            error_msg = data.get("meta", {}).get("msg", "")
            if not error_msg:
                error_msg = data.get("error", data.get("message", "Unknown error"))
        except Exception:
            error_msg = response.text or "Unknown error"

        if response.status_code == 401:
            raise UniFiAuthError(f"Authentication required: {error_msg}")
        if response.status_code == 403:
            raise UniFiAuthError(f"Access forbidden: {error_msg}")

        raise UniFiAPIError(error_msg, response.status_code)


@asynccontextmanager
async def create_app_lifespan(
    server: FastMCP,
) -> AsyncIterator[AppContext]:
    """Create and manage application lifecycle.

    Initializes HTTP client, authentication, and cache on startup.
    Cleans up resources on shutdown.

    Args:
        server: FastMCP server instance

    Yields:
        AppContext with initialized resources
    """
    logger.info("Initializing UniFi MCP Server")

    # Create HTTP client with connection pooling
    client = httpx.AsyncClient(
        timeout=settings.request_timeout,
        limits=httpx.Limits(
            max_keepalive_connections=5,
            max_connections=settings.max_connections,
        ),
        verify=settings.verify_ssl,
    )

    # Initialize auth based on configured devices or legacy mode
    device = settings.get_device()
    if device and device.has_protect_credentials:
        # Multi-device mode with credentials: use session auth
        # Populate legacy settings from device so UniFiLocalAuth works
        settings.controller_url = device.url
        settings.username = device.username
        settings.password = device.password
        settings.is_udm = True
        settings.mode = "local"
        auth: UniFiLocalAuth | UniFiCloudAuth = UniFiLocalAuth(client, settings)
        logger.info(f"Using device session authentication for {device.name} ({device.url})")
    elif device:
        # Multi-device mode without credentials: use API key
        auth = UniFiCloudAuth(device.api_key)
        logger.info(f"Using device API key authentication for {device.name} ({device.url})")
    elif settings.uses_api_key:
        if not settings.cloud_api_key:
            raise UniFiAuthError("API key is required for cloud/local_api_key mode")
        auth = UniFiCloudAuth(settings.cloud_api_key)
        if settings.mode == "cloud":
            logger.info("Using cloud authentication (api.ui.com)")
        else:
            logger.info(f"Using local Integration API authentication for {settings.controller_url}")
    else:
        auth = UniFiLocalAuth(client, settings)
        logger.info(f"Using local session authentication for {settings.controller_url}")

    # Initialize cache
    cache: TTLCache = TTLCache(maxsize=100, ttl=settings.cache_ttl)

    # Create context
    ctx = AppContext(
        client=client,
        auth=auth,
        settings=settings,
        cache=cache,
    )

    try:
        # Authenticate on startup (local session mode only)
        if isinstance(auth, UniFiLocalAuth):
            await auth.login()
            logger.info("Successfully authenticated with UniFi controller")
        else:
            # For API key modes, just log the configured endpoint
            logger.info(f"API key configured, endpoint: {settings.api_base_url}")

        yield ctx

    finally:
        # Cleanup
        logger.info("Shutting down UniFi MCP Server")

        if isinstance(auth, UniFiLocalAuth):
            await auth.logout()

        await client.aclose()
        logger.info("Cleanup complete")
