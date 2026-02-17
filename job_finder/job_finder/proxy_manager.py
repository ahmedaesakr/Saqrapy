"""
Proxy Manager - Rotating Proxy Pool
Provides structure for easily plugging in proxy lists for IP rotation.
Supports both free and premium proxy services.
"""

import random
import logging
from typing import Optional, List, Dict
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
    
    def to_scrapy_meta(self) -> Dict[str, str]:
        """Convert to Scrapy request meta format"""
        url = self.to_url()
        return {'proxy': url}


class ProxyManager:
    """
    Manages a pool of rotating proxies.
    
    USAGE:
    ------
    Option 1: Add proxies manually
        manager = ProxyManager()
        manager.add_proxy("1.2.3.4", 8080)
        manager.add_proxy("5.6.7.8", 8080, username="user", password="pass")
    
    Option 2: Load from file (one proxy per line: host:port or host:port:user:pass)
        manager = ProxyManager()
        manager.load_from_file("proxies.txt")
    
    Option 3: Use premium proxy service (placeholder for integration)
        manager = ProxyManager()
        manager.use_service("brightdata", api_key="YOUR_KEY")
    """
    
    def __init__(self):
        self.proxies: List[Proxy] = []
        self.current_index = 0
        self.enabled = False
        self.max_failures = 3  # Remove proxy after this many failures
        
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
            host=host,
            port=port,
            proxy_type=proxy_type,
            username=username,
            password=password,
            country=country
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
    
    def load_from_list(self, proxy_list: List[str]):
        """Load proxies from a list of strings (host:port format)"""
        for proxy_str in proxy_list:
            parts = proxy_str.split(':')
            if len(parts) >= 2:
                self.add_proxy(parts[0], int(parts[1]))
    
    def use_service(self, service: str, api_key: str = None, **kwargs):
        """
        Placeholder for premium proxy service integration.
        
        Supported services (to be implemented):
        - brightdata (formerly luminati)
        - smartproxy
        - oxylabs
        - scraperapi
        """
        if service == "brightdata":
            # Bright Data residential proxy format
            # proxy = f"http://brd-customer-{customer_id}-zone-{zone}:{api_key}@brd.superproxy.io:22225"
            logger.info("Bright Data integration placeholder - add your credentials")
            pass
        elif service == "scraperapi":
            # ScraperAPI uses URL parameter
            # url = f"http://api.scraperapi.com?api_key={api_key}&url={target_url}"
            logger.info("ScraperAPI integration placeholder - add your API key")
            pass
        else:
            logger.warning(f"Unknown proxy service: {service}")
    
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
    
    def get_proxy_round_robin(self) -> Optional[Proxy]:
        """Get next proxy in rotation (round-robin)"""
        if not self.enabled or not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
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


# Example proxy list (replace with real proxies)
EXAMPLE_PROXIES = """
# Add your proxies here, one per line
# Format: host:port or host:port:username:password
# Example:
# 192.168.1.1:8080
# proxy.example.com:3128:user:pass
"""
