import pytest
import respx
import httpx
from unifi_mcp.clients.network import UniFiNetworkClient
from unifi_mcp.exceptions import UniFiNotFoundError


@pytest.mark.asyncio
async def test_get_sites(mock_ctx):
    """Test getting sites through the Network client."""
    client = UniFiNetworkClient(mock_ctx)

    # Mock the Integration API response for /v1/sites
    sites_data = [
        {"id": "site-id-1", "name": "Default", "internalReference": "default"},
        {"id": "site-id-2", "name": "Home", "internalReference": "home"},
    ]

    with respx.mock(base_url=mock_ctx.settings.api_base_url) as respx_mock:
        respx_mock.get("/v1/sites").mock(
            return_value=httpx.Response(200, json={"data": sites_data})
        )

        sites = await client.get_sites()

        assert len(sites) == 2
        assert sites[0]["name"] == "Default"
        assert sites[1]["id"] == "site-id-2"


@pytest.mark.asyncio
async def test_get_site_id(mock_ctx):
    """Test site ID resolution and caching."""
    client = UniFiNetworkClient(mock_ctx)

    sites_data = [{"id": "site-id-1", "name": "Default", "internalReference": "default"}]

    with respx.mock(base_url=mock_ctx.settings.api_base_url) as respx_mock:
        # First call should fetch from API
        respx_mock.get("/v1/sites").mock(
            return_value=httpx.Response(200, json={"data": sites_data})
        )

        site_id = await client._get_site_id("default")
        assert site_id == "site-id-1"
        assert "default" in client._site_id_cache

        # Second call should use cache
        cached_site_id = await client._get_site_id("default")
        assert cached_site_id == "site-id-1"


@pytest.mark.asyncio
async def test_get_devices(mock_ctx):
    """Test getting devices."""
    client = UniFiNetworkClient(mock_ctx)
    client._site_id_cache["default"] = "site-id-1"

    devices_data = [
        {"mac": "00:11:22:33:44:55", "name": "AP-Living", "type": "uap", "state": "ONLINE"},
        {"mac": "66:77:88:99:aa:bb", "name": "USW-Main", "type": "usw", "state": "ONLINE"},
    ]

    with respx.mock(base_url=mock_ctx.settings.api_base_url) as respx_mock:
        respx_mock.get("/v1/sites/site-id-1/devices").mock(
            return_value=httpx.Response(200, json={"data": devices_data})
        )

        devices = await client.get_devices()
        assert len(devices) == 2
        assert devices[0]["mac"] == "00:11:22:33:44:55"


@pytest.mark.asyncio
async def test_get_device_by_mac(mock_ctx):
    """Test getting a single device by MAC."""
    client = UniFiNetworkClient(mock_ctx)
    client._site_id_cache["default"] = "site-id-1"

    devices_data = [{"mac": "00:11:22:33:44:55", "name": "AP-Living"}]

    with respx.mock(base_url=mock_ctx.settings.api_base_url) as respx_mock:
        respx_mock.get("/v1/sites/site-id-1/devices").mock(
            return_value=httpx.Response(200, json={"data": devices_data})
        )

        # Test exact MAC
        device = await client.get_device("00:11:22:33:44:55")
        assert device["name"] == "AP-Living"

        # Test MAC without colons
        device = await client.get_device("001122334455")
        assert device["name"] == "AP-Living"

        # Test non-existent MAC
        with pytest.raises(UniFiNotFoundError):
            await client.get_device("ffffffffffff")


@pytest.mark.asyncio
async def test_get_clients(mock_ctx):
    """Test getting connected clients."""
    client = UniFiNetworkClient(mock_ctx)
    client._site_id_cache["default"] = "site-id-1"

    clients_data = [{"mac": "aa:bb:cc:dd:ee:ff", "name": "iPhone", "ip": "10.0.0.5"}]

    with respx.mock(base_url=mock_ctx.settings.api_base_url) as respx_mock:
        respx_mock.get("/v1/sites/site-id-1/clients").mock(
            return_value=httpx.Response(200, json={"data": clients_data})
        )

        clients = await client.get_clients()
        assert len(clients) == 1
        assert clients[0]["ip"] == "10.0.0.5"


@pytest.mark.asyncio
async def test_get_site_health_integration(mock_ctx):
    """Test site health generation for Integration API."""
    client = UniFiNetworkClient(mock_ctx)
    client._site_id_cache["default"] = "site-id-1"

    devices_data = [
        {"mac": "00:11:22:33:44:55", "state": "ONLINE"},
        {"mac": "66:77:88:99:aa:bb", "state": "OFFLINE"},
    ]

    with respx.mock(base_url=mock_ctx.settings.api_base_url) as respx_mock:
        respx_mock.get("/v1/sites/site-id-1/devices").mock(
            return_value=httpx.Response(200, json={"data": devices_data})
        )

        health = await client.get_site_health()
        assert len(health) == 1
        assert health[0]["status"] == "degraded"
        assert health[0]["devices_online"] == 1
        assert health[0]["devices_offline"] == 1
