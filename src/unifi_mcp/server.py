"""UniFi MCP Server - Main entry point."""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from unifi_mcp.clients.base import create_app_lifespan
from unifi_mcp.tools.network import clients as client_tools
from unifi_mcp.tools.network import devices as device_tools
from unifi_mcp.tools.network import insights as insight_tools
from unifi_mcp.tools.network import sites as site_tools
from unifi_mcp.tools.network import stats as stat_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Create the MCP server with lifespan management
mcp = FastMCP(
    name="UniFi MCP Server",
    instructions="""
    Manage and analyze UniFi network infrastructure.

    This server provides tools for:
    - Device management (APs, switches, routers)
    - Client management (connected devices)
    - Site and network configuration
    - Network statistics and monitoring
    - AI-powered network analysis and troubleshooting

    Use the insight tools (analyze_network_issues, get_optimization_recommendations, etc.)
    for comprehensive network analysis and recommendations.
    """,
    lifespan=create_app_lifespan,
)

# =============================================================================
# Device Management Tools
# =============================================================================


@mcp.tool()
async def list_devices(ctx, site: str = "default"):
    """List all UniFi network devices (APs, switches, routers)."""
    return await device_tools.list_devices(ctx, site)


@mcp.tool()
async def get_device_details(ctx, mac: str, site: str = "default"):
    """Get detailed information about a specific device."""
    return await device_tools.get_device_details(ctx, mac, site)


@mcp.tool()
async def restart_device(ctx, mac: str, site: str = "default"):
    """Restart a UniFi device."""
    return await device_tools.restart_device(ctx, mac, site)


@mcp.tool()
async def locate_device(ctx, mac: str, enabled: bool = True, site: str = "default"):
    """Enable/disable LED blinking to locate a device."""
    return await device_tools.locate_device(ctx, mac, enabled, site)


@mcp.tool()
async def get_device_stats(ctx, mac: str, site: str = "default"):
    """Get performance statistics for a device."""
    return await device_tools.get_device_stats(ctx, mac, site)


@mcp.tool()
async def upgrade_device(ctx, mac: str, site: str = "default"):
    """Upgrade device firmware to the latest version."""
    return await device_tools.upgrade_device(ctx, mac, site)


@mcp.tool()
async def provision_device(ctx, mac: str, site: str = "default"):
    """Force re-provision a device with current configuration."""
    return await device_tools.provision_device(ctx, mac, site)


# =============================================================================
# Client Management Tools
# =============================================================================


@mcp.tool()
async def list_clients(ctx, site: str = "default"):
    """List all currently connected clients."""
    return await client_tools.list_clients(ctx, site)


@mcp.tool()
async def list_all_clients(ctx, site: str = "default"):
    """List all known clients (including offline)."""
    return await client_tools.list_all_clients(ctx, site)


@mcp.tool()
async def get_client_details(ctx, mac: str, site: str = "default"):
    """Get detailed information about a specific client."""
    return await client_tools.get_client_details(ctx, mac, site)


@mcp.tool()
async def block_client(ctx, mac: str, site: str = "default"):
    """Block a client from the network."""
    return await client_tools.block_client(ctx, mac, site)


@mcp.tool()
async def unblock_client(ctx, mac: str, site: str = "default"):
    """Unblock a previously blocked client."""
    return await client_tools.unblock_client(ctx, mac, site)


@mcp.tool()
async def kick_client(ctx, mac: str, site: str = "default"):
    """Disconnect a client (they can reconnect)."""
    return await client_tools.kick_client(ctx, mac, site)


@mcp.tool()
async def forget_client(ctx, mac: str, site: str = "default"):
    """Remove a client from the known clients list."""
    return await client_tools.forget_client(ctx, mac, site)


@mcp.tool()
async def get_client_traffic(ctx, mac: str, site: str = "default"):
    """Get traffic statistics for a specific client."""
    return await client_tools.get_client_traffic(ctx, mac, site)


# =============================================================================
# Site Management Tools
# =============================================================================


@mcp.tool()
async def list_sites(ctx):
    """List all UniFi sites accessible to the current user."""
    return await site_tools.list_sites(ctx)


@mcp.tool()
async def get_site_health(ctx, site: str = "default"):
    """Get comprehensive health status for a site."""
    return await site_tools.get_site_health(ctx, site)


@mcp.tool()
async def get_site_settings(ctx, site: str = "default"):
    """Get site configuration settings."""
    return await site_tools.get_site_settings(ctx, site)


@mcp.tool()
async def get_sysinfo(ctx, site: str = "default"):
    """Get system information for the site controller."""
    return await site_tools.get_sysinfo(ctx, site)


@mcp.tool()
async def get_networks(ctx, site: str = "default"):
    """Get all network/VLAN configurations."""
    return await site_tools.get_networks(ctx, site)


@mcp.tool()
async def get_wlans(ctx, site: str = "default"):
    """Get all wireless network (SSID) configurations."""
    return await site_tools.get_wlans(ctx, site)


@mcp.tool()
async def get_port_profiles(ctx, site: str = "default"):
    """Get switch port profile configurations."""
    return await site_tools.get_port_profiles(ctx, site)


@mcp.tool()
async def get_firewall_rules(ctx, site: str = "default"):
    """Get firewall rule configurations."""
    return await site_tools.get_firewall_rules(ctx, site)


@mcp.tool()
async def get_routing_table(ctx, site: str = "default"):
    """Get the current routing table."""
    return await site_tools.get_routing_table(ctx, site)


# =============================================================================
# Statistics & Monitoring Tools
# =============================================================================


@mcp.tool()
async def get_network_health(ctx, site: str = "default"):
    """Get overall network health summary."""
    return await stat_tools.get_network_health(ctx, site)


@mcp.tool()
async def get_recent_events(ctx, limit: int = 50, site: str = "default"):
    """Get recent network events."""
    return await stat_tools.get_recent_events(ctx, limit, site)


@mcp.tool()
async def get_alarms(ctx, site: str = "default"):
    """Get active alarms."""
    return await stat_tools.get_alarms(ctx, site)


@mcp.tool()
async def archive_all_alarms(ctx, site: str = "default"):
    """Archive all active alarms."""
    return await stat_tools.archive_all_alarms(ctx, site)


@mcp.tool()
async def run_speed_test(ctx, site: str = "default"):
    """Initiate a WAN speed test."""
    return await stat_tools.run_speed_test(ctx, site)


@mcp.tool()
async def get_speed_test_status(ctx, site: str = "default"):
    """Get speed test status and results."""
    return await stat_tools.get_speed_test_status(ctx, site)


@mcp.tool()
async def get_dpi_stats(ctx, site: str = "default"):
    """Get Deep Packet Inspection statistics for the site."""
    return await stat_tools.get_dpi_stats(ctx, site)


@mcp.tool()
async def get_traffic_summary(ctx, site: str = "default"):
    """Get traffic summary for the site."""
    return await stat_tools.get_traffic_summary(ctx, site)


# =============================================================================
# AI Insight Tools
# =============================================================================


@mcp.tool()
async def analyze_network_issues(ctx, site: str = "default"):
    """
    Analyze the network for potential issues and return a structured report.

    Aggregates device health, client connection issues, interference,
    firmware status, and recent alarms into an AI-friendly summary.
    """
    return await insight_tools.analyze_network_issues(ctx, site)


@mcp.tool()
async def get_optimization_recommendations(ctx, site: str = "default"):
    """
    Analyze network configuration and provide optimization recommendations.

    Checks channel selection, TX power, VLAN efficiency, port configurations,
    and bandwidth utilization patterns.
    """
    return await insight_tools.get_optimization_recommendations(ctx, site)


@mcp.tool()
async def get_client_experience_report(ctx, site: str = "default"):
    """
    Generate a client experience report with connection quality metrics.

    Includes signal strength distribution, roaming stats, failed connections,
    and problematic clients.
    """
    return await insight_tools.get_client_experience_report(ctx, site)


@mcp.tool()
async def get_device_health_summary(ctx, site: str = "default"):
    """
    Summarize device health across all APs, switches, and routers.

    Includes uptime, load, memory, temperature, firmware versions,
    and devices needing attention.
    """
    return await insight_tools.get_device_health_summary(ctx, site)


@mcp.tool()
async def get_traffic_analysis(ctx, hours: int = 24, site: str = "default"):
    """
    Analyze traffic patterns over the specified time period.

    Includes top talkers, application breakdown (DPI), bandwidth trends,
    and unusual activity.
    """
    return await insight_tools.get_traffic_analysis(ctx, hours, site)


@mcp.tool()
async def troubleshoot_client(ctx, mac: str, site: str = "default"):
    """
    Deep-dive troubleshooting for a specific client.

    Includes connection history, signal quality, AP associations,
    roaming events, and potential issues.
    """
    return await insight_tools.troubleshoot_client(ctx, mac, site)


def main():
    """Run the MCP server."""
    logger.info("Starting UniFi MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()
