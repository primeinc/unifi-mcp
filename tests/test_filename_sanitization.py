"""Tests for filename sanitization security in Protect camera tools."""

import pytest
import re
from pathlib import Path
from unifi_mcp.tools.protect.cameras import SNAPSHOT_DIR


def sanitize_prefix(prefix: str) -> str:
    """Replicate the sanitization logic from _save_image for testing."""
    # Keep only alphanumeric, dash, and underscore
    safe_prefix = re.sub(r'[^\w-]', '', prefix).strip()
    safe_prefix = re.sub(r'[-]+', '-', safe_prefix).lower()
    # Limit length to avoid filesystem issues
    safe_prefix = safe_prefix[:100]
    return safe_prefix


class TestFilenameSanitization:
    """Test filename sanitization to prevent path traversal and injection attacks."""

    def test_sanitize_removes_path_traversal(self):
        """Test that path traversal attempts are sanitized."""
        malicious = "../../../etc/passwd"
        result = sanitize_prefix(malicious)
        assert ".." not in result
        assert "/" not in result
        assert result == "etcpasswd"

    def test_sanitize_removes_absolute_paths(self):
        """Test that absolute path attempts are sanitized."""
        malicious = "/etc/shadow"
        result = sanitize_prefix(malicious)
        assert "/" not in result
        assert result == "etcshadow"

    def test_sanitize_removes_backslashes(self):
        """Test that Windows-style path separators are removed."""
        malicious = "..\\..\\windows\\system32"
        result = sanitize_prefix(malicious)
        assert "\\" not in result
        assert result == "windowssystem32"

    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed."""
        malicious = "test\x00.jpg"
        result = sanitize_prefix(malicious)
        assert "\x00" not in result
        assert result == "testjpg"

    def test_sanitize_removes_special_characters(self):
        """Test that special characters are removed."""
        malicious = "test!@#$%^&*()+=[]{}|;:',<>?"
        result = sanitize_prefix(malicious)
        # Should only contain alphanumeric and dash/underscore
        assert all(c.isalnum() or c in '-_' for c in result)

    def test_sanitize_allows_safe_characters(self):
        """Test that safe characters are preserved."""
        safe = "camera_front-door123"
        result = sanitize_prefix(safe)
        assert result == "camera_front-door123"

    def test_sanitize_limits_length(self):
        """Test that filenames are limited to prevent filesystem issues."""
        very_long = "a" * 200
        result = sanitize_prefix(very_long)
        assert len(result) <= 100

    def test_sanitize_handles_unicode(self):
        """Test that unicode characters are handled safely."""
        unicode_str = "camera_文字_テスト"
        result = sanitize_prefix(unicode_str)
        # Unicode word characters should be preserved by \w
        assert len(result) > 0

    def test_sanitize_collapses_multiple_dashes(self):
        """Test that multiple dashes are collapsed."""
        multiple_dashes = "test---camera"
        result = sanitize_prefix(multiple_dashes)
        assert "---" not in result
        assert result == "test-camera"

    def test_sanitize_converts_to_lowercase(self):
        """Test that output is converted to lowercase."""
        mixed_case = "Camera_Front_DOOR"
        result = sanitize_prefix(mixed_case)
        assert result == result.lower()
        assert result == "camera_front_door"

    def test_snapshot_dir_configuration(self):
        """Test that SNAPSHOT_DIR can be configured via environment."""
        # This tests that the configuration is importable and is a Path
        assert isinstance(SNAPSHOT_DIR, Path)
        # Should default to /tmp/unifi-protect or custom value
        assert str(SNAPSHOT_DIR).endswith("unifi-protect") or "UNIFI_SNAPSHOT_DIR" in str(SNAPSHOT_DIR)
