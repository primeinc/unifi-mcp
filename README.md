# UniFi MCP Server

An MCP (Model Context Protocol) server that provides AI assistants like Claude with access to UniFi Network infrastructure management and analysis capabilities.

## Features

- **Device Management**: List, restart, locate, and upgrade UniFi devices (APs, switches, routers)
- **Client Management**: Monitor connected clients, block/unblock, view traffic statistics
- **Site Management**: View site health, network configurations, VLANs, and wireless settings
- **Statistics & Monitoring**: Events, alarms, speed tests, and DPI statistics
- **AI-Powered Insights**: Network analysis, optimization recommendations, and troubleshooting

## Supported Hardware

- UniFi Dream Machine (UDM, UDM-Pro, UDM-SE)
- UniFi Cloud Gateway (UCG-Ultra, UCG-Fiber)
- UniFi Network Application (self-hosted)
- Traditional Cloud Key (Gen1, Gen2)

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/unifi-mcp.git
cd unifi-mcp

# Install dependencies
uv sync
```

### Using pip

```bash
pip install -e .
```

## Configuration

Create a `.env` file in the project root (or set environment variables).

### Local Integration API (Recommended for UCG/UDM)

The recommended way to connect to UniFi OS devices (UCG-Fiber, UDM-Pro, etc.) is using the Integration API with an API key:

```bash
UNIFI_MODE=local_api_key
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CLOUD_API_KEY=your-api-key
UNIFI_SITE=default
UNIFI_VERIFY_SSL=false
```

To create an API key:
1. Log into your UniFi controller
2. Go to Settings → Control Plane → API
3. Create a new API key with appropriate permissions

### Local Session Auth (Traditional)

For traditional username/password authentication:

```bash
UNIFI_MODE=local
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_USERNAME=admin
UNIFI_PASSWORD=your-password
UNIFI_SITE=default
UNIFI_IS_UDM=true
UNIFI_VERIFY_SSL=false
```

### Cloud API (api.ui.com)

For Ubiquiti Cloud API access:

```bash
UNIFI_MODE=cloud
UNIFI_CLOUD_API_KEY=your-api-key
```

Get your API key from [unifi.ui.com](https://unifi.ui.com) → API section.

## Usage with Claude Desktop

Add to your Claude Desktop configuration (`~/.config/claude/claude_desktop_config.json` on Linux or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "unifi": {
      "command": "poetry",
      "args": ["run", "--directory", "/path/to/unifi-mcp", "python", "-m", "unifi_mcp.server"],
      "env": {
        "UNIFI_MODE": "local_api_key",
        "UNIFI_CONTROLLER_URL": "https://192.168.1.1",
        "UNIFI_CLOUD_API_KEY": "your-api-key",
        "UNIFI_VERIFY_SSL": "false"
      }
    }
  }
}
```

## Usage with Claude Code

```bash
# Add the MCP server
claude mcp add unifi -- poetry run --directory /path/to/unifi-mcp python -m unifi_mcp.server

# Or with environment variables
UNIFI_MODE=local_api_key UNIFI_CONTROLLER_URL=https://192.168.1.1 UNIFI_CLOUD_API_KEY=your-key claude mcp add unifi -- poetry run --directory /path/to/unifi-mcp python -m unifi_mcp.server
```

## Available Tools

### Device Management
- `list_devices` - List all UniFi network devices
- `get_device_details` - Get detailed device information
- `restart_device` - Restart a device
- `locate_device` - Blink LED to locate device
- `get_device_stats` - Get performance statistics
- `upgrade_device` - Upgrade firmware
- `provision_device` - Force re-provision

### Client Management
- `list_clients` - List connected clients
- `list_all_clients` - List all known clients (including offline)
- `get_client_details` - Get client details
- `block_client` / `unblock_client` - Block/unblock clients
- `kick_client` - Disconnect a client
- `forget_client` - Remove from known clients
- `get_client_traffic` - Get traffic statistics

### Site Management
- `list_sites` - List all sites
- `get_site_health` - Get site health status
- `get_site_settings` - Get site settings
- `get_sysinfo` - Get system information
- `get_networks` - Get network/VLAN configs
- `get_wlans` - Get wireless network configs
- `get_port_profiles` - Get switch port profiles
- `get_firewall_rules` - Get firewall rules
- `get_routing_table` - Get routing table

### Statistics & Monitoring
- `get_network_health` - Overall network health
- `get_recent_events` - Recent events
- `get_alarms` - Active alarms
- `archive_all_alarms` - Archive all alarms
- `run_speed_test` - Start speed test
- `get_speed_test_status` - Get speed test results
- `get_dpi_stats` - DPI statistics
- `get_traffic_summary` - Traffic summary

### AI Insight Tools
- `analyze_network_issues` - Comprehensive issue analysis
- `get_optimization_recommendations` - Configuration recommendations
- `get_client_experience_report` - Client quality metrics
- `get_device_health_summary` - Device health overview
- `get_traffic_analysis` - Traffic pattern analysis
- `troubleshoot_client` - Deep-dive client troubleshooting

## Example Conversations

After connecting the MCP server, you can ask Claude:

- "List all my UniFi devices"
- "What's the current network health?"
- "Analyze my network for any issues"
- "What optimization recommendations do you have?"
- "Show me client experience metrics"
- "Troubleshoot the client with MAC aa:bb:cc:dd:ee:ff"
- "Which clients are using the most bandwidth?"
- "Are there any devices that need firmware updates?"
- "Show me the recent network events"
- "Run a speed test"

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff check .
uv run ruff format .
```

## Security Notes

- Credentials are passed via environment variables
- SSL verification is disabled by default for self-signed certificates
- The server only exposes read operations and safe management commands
- Destructive operations (delete site, factory reset) are not exposed

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
