import os
from enum import Enum
from typing import List, Optional, Set, Dict, Tuple
import ipaddress
from dataclasses import dataclass
from functools import lru_cache
import logging
from urllib.parse import urlparse
import re
import tldextract

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    NONE = "none"  # No restrictions
    BASIC = "basic"  # Basic security (block obvious dangerous patterns)
    STANDARD = "standard"  # Default level
    STRICT = "strict"  # High security
    CUSTOM = "custom"  # Custom rules


@dataclass
class SecurityConfig:
    # Main security switches
    SECURITY_LEVEL: SecurityLevel
    ALLOW_INTERNAL_REQUESTS: bool
    ALLOW_LOCAL_REQUESTS: bool
    ALLOW_FILE_PROTOCOL: bool

    # Network restrictions
    ALLOW_PRIVATE_NETWORKS: bool
    ALLOW_LOCALHOST: bool
    ALLOWED_PROTOCOLS: Set[str]
    BLOCKED_PROTOCOLS: Set[str]
    DEFAULT_ALLOWED_PROTOCOLS: Set[str] = frozenset({'http', 'https'})

    # Domain restrictions
    ALLOWED_DOMAINS: Set[str]
    BLOCKED_DOMAINS: Set[str]
    ALLOWED_TLDS: Set[str]
    BLOCKED_TLDS: Set[str]

    # IP restrictions
    ALLOWED_IPS: Set[str]
    BLOCKED_IPS: Set[str]
    ALLOWED_IP_RANGES: List[str]
    BLOCKED_IP_RANGES: List[str]

    # Content Security
    MAX_URL_LENGTH: int = 2083  # Common browser limit
    SAFE_SCHEMES: Set[str] = frozenset({'http', 'https'})
    INTERNAL_TLDS: Set[str] = frozenset({
        'local', 'localhost', 'internal', 'test', 'invalid', 'example', 'lan'
    })

    # IP Networks to consider private
    PRIVATE_NETWORKS: List[str] = [
        '10.0.0.0/8',  # RFC 1918
        '172.16.0.0/12',  # RFC 1918
        '192.168.0.0/16',  # RFC 1918
        'fc00::/7',  # ULA
        'fe80::/10',  # Link Local
        '169.254.0.0/16',  # Link Local
        '127.0.0.0/8',  # Loopback
        '::1/128',  # Loopback
    ]

    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Create security config from environment variables with smart defaults."""
        security_level = SecurityLevel(os.getenv('SECURITY_LEVEL', 'standard').lower())

        # Base configuration varies by security level
        base_config = {
            SecurityLevel.NONE: {
                'ALLOW_INTERNAL_REQUESTS': True,
                'ALLOW_LOCAL_REQUESTS': True,
                'ALLOW_FILE_PROTOCOL': True,
                'ALLOW_PRIVATE_NETWORKS': True,
                'ALLOW_LOCALHOST': True,
            },
            SecurityLevel.BASIC: {
                'ALLOW_INTERNAL_REQUESTS': True,
                'ALLOW_LOCAL_REQUESTS': False,
                'ALLOW_FILE_PROTOCOL': False,
                'ALLOW_PRIVATE_NETWORKS': True,
                'ALLOW_LOCALHOST': False,
            },
            SecurityLevel.STANDARD: {
                'ALLOW_INTERNAL_REQUESTS': False,
                'ALLOW_LOCAL_REQUESTS': False,
                'ALLOW_FILE_PROTOCOL': False,
                'ALLOW_PRIVATE_NETWORKS': False,
                'ALLOW_LOCALHOST': False,
            },
            SecurityLevel.STRICT: {
                'ALLOW_INTERNAL_REQUESTS': False,
                'ALLOW_LOCAL_REQUESTS': False,
                'ALLOW_FILE_PROTOCOL': False,
                'ALLOW_PRIVATE_NETWORKS': False,
                'ALLOW_LOCALHOST': False,
            },
            SecurityLevel.CUSTOM: {
                'ALLOW_INTERNAL_REQUESTS': False,
                'ALLOW_LOCAL_REQUESTS': False,
                'ALLOW_FILE_PROTOCOL': False,
                'ALLOW_PRIVATE_NETWORKS': False,
                'ALLOW_LOCALHOST': False,
            },
        }[security_level]

        # Allow environment variables to override base configuration
        config = cls(
            SECURITY_LEVEL=security_level,
            ALLOW_INTERNAL_REQUESTS=_parse_bool_env('ALLOW_INTERNAL_REQUESTS',
                                                    base_config['ALLOW_INTERNAL_REQUESTS']),
            ALLOW_LOCAL_REQUESTS=_parse_bool_env('ALLOW_LOCAL_REQUESTS',
                                                 base_config['ALLOW_LOCAL_REQUESTS']),
            ALLOW_FILE_PROTOCOL=_parse_bool_env('ALLOW_FILE_PROTOCOL',
                                                base_config['ALLOW_FILE_PROTOCOL']),
            ALLOW_PRIVATE_NETWORKS=_parse_bool_env('ALLOW_PRIVATE_NETWORKS',
                                                   base_config['ALLOW_PRIVATE_NETWORKS']),
            ALLOW_LOCALHOST=_parse_bool_env('ALLOW_LOCALHOST',
                                            base_config['ALLOW_LOCALHOST']),
            ALLOWED_PROTOCOLS=_parse_set_env('ALLOWED_PROTOCOLS', {'http', 'https'}),
            BLOCKED_PROTOCOLS=_parse_set_env('BLOCKED_PROTOCOLS', set()),
            ALLOWED_DOMAINS=_parse_set_env('ALLOWED_DOMAINS', set()),
            BLOCKED_DOMAINS=_parse_set_env('BLOCKED_DOMAINS', set()),
            ALLOWED_TLDS=_parse_set_env('ALLOWED_TLDS', set()),
            BLOCKED_TLDS=_parse_set_env('BLOCKED_TLDS',
                                        cls.INTERNAL_TLDS if security_level != SecurityLevel.NONE else set()),
            ALLOWED_IPS=_parse_set_env('ALLOWED_IPS', set()),
            BLOCKED_IPS=_parse_set_env('BLOCKED_IPS', set()),
            ALLOWED_IP_RANGES=_parse_list_env('ALLOWED_IP_RANGES', []),
            BLOCKED_IP_RANGES=_parse_list_env('BLOCKED_IP_RANGES', cls.PRIVATE_NETWORKS if not base_config[
                'ALLOW_PRIVATE_NETWORKS'] else []),
        )

        logger.info(f"Initialized security config with level: {security_level.value}")
        return config

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validates a URL against security rules.
        Returns (is_valid, error_message if any)
        """
        if self.SECURITY_LEVEL == SecurityLevel.NONE:
            return True, None

        try:
            # Basic URL validation
            if len(url) > self.MAX_URL_LENGTH:
                return False, f"URL exceeds maximum length of {self.MAX_URL_LENGTH}"

            # Parse URL
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False, "Invalid URL format"

            # Protocol validation
            if not self._is_protocol_allowed(parsed.scheme):
                return False, f"Protocol '{parsed.scheme}' not allowed"

            # Get domain info
            hostname = parsed.hostname or ''
            extracted = tldextract.extract(hostname)

            # Domain validation
            if self.ALLOWED_DOMAINS and hostname not in self.ALLOWED_DOMAINS:
                return False, f"Domain '{hostname}' not in allowed list"
            if hostname in self.BLOCKED_DOMAINS:
                return False, f"Domain '{hostname}' is blocked"

            # TLD validation
            if self.ALLOWED_TLDS and extracted.suffix not in self.ALLOWED_TLDS:
                return False, f"TLD '.{extracted.suffix}' not in allowed list"
            if extracted.suffix in self.BLOCKED_TLDS:
                return False, f"TLD '.{extracted.suffix}' is blocked"

            # IP address validation
            try:
                ip = ipaddress.ip_address(hostname)
                return self._validate_ip(ip)
            except ValueError:
                # Not an IP address, continue with other checks
                pass

            # SSRF protection
            if self._contains_ssrf_pattern(url):
                return False, "URL contains potentially malicious pattern"

            # Internal hostname check
            if not self.ALLOW_INTERNAL_REQUESTS and self._is_internal_hostname(hostname):
                return False, "Internal hostnames not allowed"

            return True, None

        except Exception as e:
            logger.error(f"Error validating URL: {str(e)}")
            return False, f"URL validation error: {str(e)}"

    def _is_protocol_allowed(self, protocol: str) -> bool:
        """Check if a protocol is allowed based on configuration."""
        if self.ALLOWED_PROTOCOLS and protocol not in self.ALLOWED_PROTOCOLS:
            return False
        if protocol in self.BLOCKED_PROTOCOLS:
            return False
        if protocol == 'file' and not self.ALLOW_FILE_PROTOCOL:
            return False
        return True

    def _validate_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Tuple[bool, Optional[str]]:
        """Validate an IP address against security rules."""
        # Check explicit allow/block lists
        if self.ALLOWED_IPS and str(ip) not in self.ALLOWED_IPS:
            return False, "IP not in allowed list"
        if str(ip) in self.BLOCKED_IPS:
            return False, "IP is blocked"

        # Check ranges
        for range_str in self.BLOCKED_IP_RANGES:
            if ip in ipaddress.ip_network(range_str):
                return False, f"IP in blocked range {range_str}"

        if self.ALLOWED_IP_RANGES:
            in_allowed_range = any(ip in ipaddress.ip_network(range_str)
                                   for range_str in self.ALLOWED_IP_RANGES)
            if not in_allowed_range:
                return False, "IP not in any allowed range"

        # Check for localhost/private networks
        if ip.is_loopback and not self.ALLOW_LOCALHOST:
            return False, "Loopback addresses not allowed"
        if ip.is_private and not self.ALLOW_PRIVATE_NETWORKS:
            return False, "Private network addresses not allowed"
        if ip.is_link_local and not self.ALLOW_LOCAL_REQUESTS:
            return False, "Link-local addresses not allowed"
        if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False, "Invalid IP address type"

        return True, None

    def _is_internal_hostname(self, hostname: str) -> bool:
        """Check if a hostname appears to be internal."""
        if hostname.lower() in {'localhost', 'localhost.localdomain'}:
            return True

        parts = hostname.lower().split('.')
        return any(part in self.INTERNAL_TLDS for part in parts)

    def _contains_ssrf_pattern(self, url: str) -> bool:
        """Check for common SSRF attack patterns."""
        patterns = [
            r'@',  # URL credentials
            r'\.\./',  # Directory traversal
            r'%2e%2e/',  # Encoded traversal
            r'127\.0{1,3}\.0{1,3}\.0{1,3}',  # Localhost variants
            r'0177\.0{1,3}\.0{1,3}\.0{1,3}',  # Octal localhost
            r'0x7f\.0{1,3}\.0{1,3}\.0{1,3}',  # Hex localhost
            r'2130706433',  # Decimal localhost
            r'017700000001',  # Octal localhost
            r'127\.1',  # Short localhost
            r'0:0:0:0:0:ffff:',  # IPv6 mapped IPv4
            r'::1',  # IPv6 localhost
        ]
        return any(re.search(pattern, url.lower()) for pattern in patterns)


def _parse_bool_env(key: str, default: bool = False) -> bool:
    """Parse boolean environment variables."""
    return os.getenv(key, str(default)).lower() in ('true', '1', 'yes')


def _parse_set_env(key: str, default: Set[str] = None) -> Set[str]:
    """Parse comma-separated environment variables into sets."""
    value = os.getenv(key)
    return set(value.split(',')) if value else (default or set())


def _parse_list_env(key: str, default: List[str] = None) -> List[str]:
    """Parse comma-separated environment variables into lists."""
    value = os.getenv(key)
    return value.split(',') if value else (default or [])