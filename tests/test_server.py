"""Tests for server module and Context type hints."""

from typing import get_type_hints

from mcp.server.fastmcp import Context

from unifi_mcp import server


class TestContextTypeHints:
    """Test that all tool handlers have proper Context type hints for MCP SDK 1.x."""

    def test_all_tool_handlers_have_context_type_hints(self):
        """Test that all @mcp.tool() decorated functions have ctx: Context type hint."""
        # Get all functions from server module that are likely tool handlers
        tool_functions = [
            name for name in dir(server)
            if callable(getattr(server, name))
            and not name.startswith('_')
            and name not in ['logging', 'sys', 'mcp', 'Context', 'FastMCP',
                             'create_app_lifespan', 'settings', 'client_tools',
                             'device_tools', 'insight_tools', 'site_tools',
                             'stat_tools', 'protect_tools', 'main']
        ]

        missing_hints = []
        incorrect_hints = []

        for func_name in tool_functions:
            func = getattr(server, func_name)
            try:
                hints = get_type_hints(func)
                if 'ctx' not in hints:
                    missing_hints.append(func_name)
                elif hints['ctx'] != Context:
                    incorrect_hints.append(f"{func_name}: {hints['ctx']}")
            except Exception:
                # Skip functions that can't be type-hinted (e.g., imported objects)
                continue

        assert not missing_hints, f"Functions missing ctx type hint: {missing_hints}"
        assert not incorrect_hints, f"Functions with incorrect ctx type: {incorrect_hints}"
