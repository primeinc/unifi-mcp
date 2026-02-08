import logging
import re
from typing import Any

from unifi_mcp.config import settings

# Regex patterns for common sensitive data
MAC_REGEX = re.compile(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})")
IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# UniFi API keys are typically long alphanumeric strings or UUIDs
# This is a broad pattern to catch them in headers/logs
SECRET_KEYWORDS = ["api_key", "password", "token", "csrf", "unifises", "authorization"]

class SecretMaskingFilter(logging.Filter):
    """Logging filter that masks sensitive data.
    
    Always masks secrets (API keys, passwords, tokens).
    Optionally masks PII (MAC addresses, IPs) based on settings.mask_pii.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.msg, str):
            # If msg is not a string (e.g., an object), we can't easily regex it
            # But we should still try to convert to string or handle common types
            record.msg = str(record.msg)
            
        record.msg = self.mask_secrets(record.msg)
        
        if settings.mask_pii:
            record.msg = self.mask_pii(record.msg)
            
        return True

    def mask_secrets(self, text: str) -> str:
        """Always mask high-entropy secrets and specific keywords."""
        # Mask header-like patterns: "X-API-KEY: [secret]"
        for kw in SECRET_KEYWORDS:
            # Case-insensitive match for "keyword: value" or "keyword=value"
            pattern = re.compile(rf"({kw})[\s:=]+([^\s,;]+)", re.IGNORECASE)
            text = pattern.sub(r"\1: [MASKED]", text)
            
        return text

    def mask_pii(self, text: str) -> str:
        """Mask MAC addresses and IP addresses."""
        text = MAC_REGEX.sub("[MAC_MASKED]", text)
        # We try to avoid masking common version numbers or non-IP dots
        text = IP_REGEX.sub("[IP_MASKED]", text)
        return text

def setup_logging():
    """Configure logging with the masking filter."""
    root_logger = logging.getLogger()
    
    # If handlers already exist, just add the filter to them
    if root_logger.handlers:
        for handler in root_logger.handlers:
            handler.addFilter(SecretMaskingFilter())
    else:
        # Default config if nothing exists
        logging.basicConfig(level=logging.INFO)
        root_logger.handlers[0].addFilter(SecretMaskingFilter())
