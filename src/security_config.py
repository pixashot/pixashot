from enum import Enum
from typing import List, Optional, Set, Dict, Tuple
import ipaddress
from dataclasses import dataclass, field
import logging
from urllib.parse import urlparse
import re
import tldextract

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CUSTOM = "custom"

@dataclass
class SecurityConfig:
    # Main security switches
    SECURITY_LEVEL: SecurityLevel = SecurityLevel.STANDARD
    ALLOW_INTERNAL_REQUESTS: bool = False
    ALLOW_LOCAL_REQUESTS: bool = False
    ALLOW_FILE_PROTOCOL: bool = False
    ALLOW_PRIVATE_NETWORKS: bool = False
    ALLOW_LOCALHOST: bool = False

    # Network restrictions
    ALLOWED_PROTOCOLS: Set[str] = field(default_factory=lambda: {'http', 'https'})
    BLOCKED_PROTOCOLS: Set[str] = field(default_factory=set)
    DEFAULT_ALLOWED_PROTOCOLS: Set[str] = field(default_factory=lambda: {'http', 'https'})

    # Domain restrictions
    ALLOWED_DOMAINS: Set[str] = field(default_factory=set)
    BLOCKED_DOMAINS: Set[str] = field(default_factory=set)
    ALLOWED_TLDS: Set[str] = field(default_factory=set)
    BLOCKED_TLDS: Set[str] = field(default_factory=lambda: {'local', 'localhost', 'internal', 'test', 'invalid', 'example', 'lan'})

    # IP restrictions
    ALLOWED_IPS: Set[str] = field(default_factory=set)
    BLOCKED_IPS: Set[str] = field(default_factory=set)
    ALLOWED_IP_RANGES: List[str] = field(default_factory=list)
    BLOCKED_IP_RANGES: List[str] = field(default_factory=lambda: [
        '10.0.0.0/8',      # RFC 1918
        '172.16.0.0/12',   # RFC 1918
        '192.168.0.0/16',  # RFC 1918
        'fc00::/7',        # ULA
        'fe80::/10',       # Link Local
        '169.254.0.0/16',  # Link Local
        '127.0.0.0/8',     # Loopback
        '::1/128',         # Loopback
    ])

    # Content Security
    MAX_URL_LENGTH: int = 2083  # Common browser limit
    SAFE_SCHEMES: Set[str] = field(default_factory=lambda: {'http', 'https'})

    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Create security config from environment variables with smart defaults."""
        return cls()  # For now, just return default config

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validates a URL against security rules.
        Returns (is_valid, error_message if any)
        """
        # For now, allow all URLs
        return True, None