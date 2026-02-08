import re
from typing import Any, TypeVar

from unifi_mcp.config import settings

T = TypeVar("T")

MAC_REGEX = re.compile(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})")
IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

def mask_pii_data(data: T) -> T:
    """Recursively mask MAC addresses, IPs, and hostnames in data if mask_pii is enabled.
    
    Args:
        data: The data to mask (dict, list, string, etc.)
        
    Returns:
        The masked data
    """
    if not settings.mask_pii:
        return data
        
    return _mask_recursive(data)

def _mask_recursive(data: Any) -> Any:
    if isinstance(data, str):
        # Mask MACs
        data = MAC_REGEX.sub("[MAC_MASKED]", data)
        # Mask IPs (simple heuristic, avoid masking numbers like 1.0.0)
        data = IP_REGEX.sub("[IP_MASKED]", data)
        return data
    
    if isinstance(data, list):
        return [_mask_recursive(item) for item in data]
    
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Sensitive keys to mask entirely
            if k.lower() in ["mac", "ip", "hostname", "fixed_ip", "wan_ip"]:
                new_dict[k] = "[MASKED]"
            else:
                new_dict[k] = _mask_recursive(v)
        return new_dict
        
    return data
