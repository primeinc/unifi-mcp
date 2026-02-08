# Test Coverage Requirements

## Current Status
- **Current Coverage**: 28%
- **Required Coverage**: 60%
- **Status**: ❌ FAILING (CI will block merge)

## Coverage by Module

### High Priority (Core Functionality - Need >60% coverage)
- `src/unifi_mcp/auth/local.py` - 25% → Need 60%+
  - Add tests for login, logout, token refresh
  - Test authentication error handling
  
- `src/unifi_mcp/clients/base.py` - 27% → Need 60%+
  - Test HTTP client setup and request handling
  - Test retry logic and error handling
  - Test multi-device authentication flow
  
- `src/unifi_mcp/clients/network.py` - 18% → Need 60%+
  - Add tests for network client methods
  - Test API endpoint calls
  
- `src/unifi_mcp/clients/protect.py` - 30% → Need 60%+
  - Test Protect client operations
  - Test event retrieval and thumbnail generation
  
### Medium Priority (Tool Implementations - Need >40% coverage)
- `src/unifi_mcp/tools/network/clients.py` - 26% → Need 40%+
- `src/unifi_mcp/tools/network/devices.py` - 29% → Need 40%+
- `src/unifi_mcp/tools/network/sites.py` - 19% → Need 40%+
- `src/unifi_mcp/tools/network/stats.py` - 15% → Need 40%+
- `src/unifi_mcp/tools/protect/cameras.py` - 19% → Need 40%+

### Critical Priority (Extremely Low Coverage)
- `src/unifi_mcp/tools/network/insights.py` - 4% → Need 60%+
  - This is a critical AI analysis module
  - Needs comprehensive testing of all analysis functions

## Action Items

### Immediate (To reach 60% overall)
1. Add integration tests for network client operations
2. Add unit tests for authentication flows
3. Add tests for Protect client event handling
4. Add tests for insight analysis functions
5. Add tests for error handling across all clients

### Test Types Needed
- **Unit Tests**: Test individual functions with mocked dependencies
- **Integration Tests**: Test client interactions with mocked HTTP responses
- **Error Handling Tests**: Test failure scenarios and edge cases
- **Security Tests**: Test authentication, authorization, and input validation

## How to Add Tests

### Example: Testing a client method
```python
import pytest
from unittest.mock import AsyncMock, Mock
from unifi_mcp.clients.network import UniFiNetworkClient

@pytest.mark.asyncio
async def test_list_devices():
    mock_http_client = AsyncMock()
    mock_response = Mock()
    mock_response.json.return_value = {"data": [{"mac": "00:00:00:00:00:00"}]}
    mock_http_client.get.return_value = mock_response
    
    # Test the method
    client = UniFiNetworkClient(mock_http_client, ...)
    devices = await client.list_devices()
    
    assert len(devices) > 0
    assert devices[0]["mac"] == "00:00:00:00:00:00"
```

## Running Coverage Locally
```bash
# Run tests with coverage report
poetry run pytest --cov=src/unifi_mcp --cov-report=term-missing

# Run with failure threshold
poetry run pytest --cov=src/unifi_mcp --cov-fail-under=60

# Generate HTML coverage report
poetry run pytest --cov=src/unifi_mcp --cov-report=html
# Open htmlcov/index.html in browser
```

## CI/CD Enforcement
- Coverage threshold is enforced in CI at 60%
- PRs will fail if coverage drops below this threshold
- Coverage reports are uploaded to Codecov for tracking

## Notes
- Focus on critical paths and error handling first
- Mock external dependencies (HTTP clients, file I/O)
- Test both success and failure scenarios
- Security-critical code should have >80% coverage
