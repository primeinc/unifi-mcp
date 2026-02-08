import pytest
import respx
import httpx
from unifi_mcp.clients.protect import UniFiProtectClient
from unifi_mcp.exceptions import UniFiAuthError, UniFiNotFoundError


@pytest.mark.asyncio
async def test_get_cameras(mock_protect_client):
    """Test getting all cameras."""
    cameras_data = [
        {"id": "cam-1", "name": "Front Door", "state": "CONNECTED"},
        {"id": "cam-2", "name": "Backyard", "state": "DISCONNECTED"},
    ]

    with respx.mock(base_url=mock_protect_client.base_url) as respx_mock:
        respx_mock.get("/cameras").mock(return_value=httpx.Response(200, json=cameras_data))

        cameras = await mock_protect_client.get_cameras()
        assert len(cameras) == 2
        assert cameras[0]["name"] == "Front Door"


@pytest.mark.asyncio
async def test_get_camera_by_name(mock_protect_client):
    """Test finding a camera by name."""
    cameras_data = [{"id": "cam-1", "name": "Front Door"}]

    with respx.mock(base_url=mock_protect_client.base_url) as respx_mock:
        respx_mock.get("/cameras").mock(return_value=httpx.Response(200, json=cameras_data))

        camera = await mock_protect_client.get_camera_by_name("front")
        assert camera["id"] == "cam-1"

        with pytest.raises(UniFiNotFoundError):
            await mock_protect_client.get_camera_by_name("non-existent")


@pytest.mark.asyncio
async def test_get_camera_snapshot(mock_protect_client):
    """Test getting camera snapshot bytes."""
    with respx.mock(base_url=mock_protect_client.base_url) as respx_mock:
        respx_mock.get("/cameras/cam-1/snapshot").mock(
            return_value=httpx.Response(200, content=b"fake-jpeg-data")
        )

        snapshot = await mock_protect_client.get_camera_snapshot("cam-1")
        assert snapshot == b"fake-jpeg-data"


@pytest.mark.asyncio
async def test_session_auth_flow(mock_protect_client):
    """Test the session authentication flow for internal API."""
    with respx.mock() as respx_mock:
        # Mock login
        login_route = respx_mock.post(f"{mock_protect_client.device.url}/api/auth/login").mock(
            return_value=httpx.Response(200, headers={"X-CSRF-Token": "test-token"})
        )

        # Mock internal API call
        respx_mock.get(f"{mock_protect_client.internal_base_url}/events").mock(
            return_value=httpx.Response(200, json=[])
        )

        await mock_protect_client.get_events()

        assert login_route.called
        assert mock_protect_client._session_authenticated
        assert mock_protect_client._csrf_token == "test-token"


@pytest.mark.asyncio
async def test_get_motion_events(mock_protect_client):
    """Test getting motion events."""
    events_data = [{"id": "event-1", "type": "motion", "camera": "cam-1"}]

    with respx.mock() as respx_mock:
        # Mock auth
        respx_mock.post(f"{mock_protect_client.device.url}/api/auth/login").mock(
            return_value=httpx.Response(200, headers={"X-CSRF-Token": "token"})
        )

        # Mock events
        respx_mock.get(f"{mock_protect_client.internal_base_url}/events").mock(
            return_value=httpx.Response(200, json=events_data)
        )

        events = await mock_protect_client.get_motion_events(hours=1)
        assert len(events) == 1
        assert events[0]["type"] == "motion"


@pytest.mark.asyncio
async def test_auth_failure(mock_protect_client):
    """Test authentication failure handling."""
    with respx.mock() as respx_mock:
        respx_mock.post(f"{mock_protect_client.device.url}/api/auth/login").mock(
            return_value=httpx.Response(401)
        )

        with pytest.raises(UniFiAuthError):
            await mock_protect_client._ensure_session_auth()
