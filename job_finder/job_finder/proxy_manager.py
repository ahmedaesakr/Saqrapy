"""
Proxy Manager - Rotating Proxy Pool
Provides structure for easily plugging in proxy lists for IP rotation.
"""

import random
import logging
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


@dataclass
class Proxy:
    """Represents a proxy server"""
    host: str
    port: int
    proxy_type: ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    failures: int = 0

    def to_url(self) -> str:
        """Convert proxy to URL format for requests/scrapy"""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.proxy_type.value}://{auth}{self.host}:{self.port}"


class ProxyManager:
    """
    Manages a pool of rotating proxies.

    Usage:
        manager = ProxyManager()
        manager.load_from_file("proxies.txt")   # one per line: host:port or host:port:user:pass
        proxy = manager.get_proxy()
    """

    def __init__(self):
        self.proxies: List[Proxy] = []
        self.enabled = False
        self.max_failures = 3

    def add_proxy(
        self,
        host: str,
        port: int,
        proxy_type: ProxyType = ProxyType.HTTP,
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: Optional[str] = None
    ):
        """Add a single proxy to the pool"""
        proxy = Proxy(
            host=host, port=port, proxy_type=proxy_type,
            username=username, password=password, country=country
        )
        self.proxies.append(proxy)
        self.enabled = True
        logger.info(f"Added proxy: {host}:{port}")

    def load_from_file(self, filepath: str):
        """
        Load proxies from a text file.
        Format: host:port or host:port:username:password
        """
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split(':')
                    if len(parts) >= 2:
                        host = parts[0]
                        port = int(parts[1])
                        username = parts[2] if len(parts) > 2 else None
                        password = parts[3] if len(parts) > 3 else None
                        self.add_proxy(host, port, username=username, password=password)
            logger.info(f"Loaded {len(self.proxies)} proxies from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Proxy file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")

    def get_proxy(self, country: Optional[str] = None) -> Optional[Proxy]:
        """Get a random proxy from the pool"""
        if not self.enabled or not self.proxies:
            return None
        available = self.proxies
        if country:
            available = [p for p in self.proxies if p.country == country]
        if not available:
            return None
        return random.choice(available)

    def mark_failure(self, proxy: Proxy):
        """Mark a proxy as failed. Remove if too many failures."""
        proxy.failures += 1
        if proxy.failures >= self.max_failures:
            self.proxies.remove(proxy)
            logger.warning(f"Removed failed proxy: {proxy.host}:{proxy.port}")

    def mark_success(self, proxy: Proxy):
        """Reset failure count on success"""
        proxy.failures = 0


# Global proxy manager instance
proxy_manager = ProxyManager()
