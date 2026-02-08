"""Tests for server module and Context type hints."""

import pytest
from typing import get_type_hints
from unifi_mcp import server
from mcp.server.fastmcp import Context


class TestContextTypeHints:
    """Test that all tool handlers have proper Context type hints for MCP SDK 1.x."""

    def test_list_devices_has_context_type_hint(self):
        """Test list_devices has Context type hint."""
        hints = get_type_hints(server.list_devices)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_get_device_details_has_context_type_hint(self):
        """Test get_device_details has Context type hint."""
        hints = get_type_hints(server.get_device_details)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_list_clients_has_context_type_hint(self):
        """Test list_clients has Context type hint."""
        hints = get_type_hints(server.list_clients)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_list_sites_has_context_type_hint(self):
        """Test list_sites has Context type hint."""
        hints = get_type_hints(server.list_sites)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_list_cameras_has_context_type_hint(self):
        """Test list_cameras has Context type hint."""
        hints = get_type_hints(server.list_cameras)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_get_camera_snapshot_has_context_type_hint(self):
        """Test get_camera_snapshot has Context type hint."""
        hints = get_type_hints(server.get_camera_snapshot)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_get_event_thumbnail_has_context_type_hint(self):
        """Test get_event_thumbnail (new tool) has Context type hint."""
        hints = get_type_hints(server.get_event_thumbnail)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_get_camera_snapshot_file_has_context_type_hint(self):
        """Test get_camera_snapshot_file (new tool) has Context type hint."""
        hints = get_type_hints(server.get_camera_snapshot_file)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_analyze_network_issues_has_context_type_hint(self):
        """Test analyze_network_issues has Context type hint."""
        hints = get_type_hints(server.analyze_network_issues)
        assert 'ctx' in hints
        assert hints['ctx'] == Context

    def test_list_unifi_devices_has_context_type_hint(self):
        """Test list_unifi_devices has Context type hint."""
        hints = get_type_hints(server.list_unifi_devices)
        assert 'ctx' in hints
        assert hints['ctx'] == Context
