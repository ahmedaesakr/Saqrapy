"""
Enhanced Middlewares:
- User-Agent Rotation
- Random Delays (Human-like behavior)
- Proxy Support
- Retry Logic with Exponential Backoff
- Captcha Detection
"""

import random
import time
import logging
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

from .user_agents import get_full_headers
from .proxy_manager import proxy_manager
from .captcha_handler import captcha_handler

logger = logging.getLogger(__name__)


class RandomUserAgentMiddleware:
    """Rotates User-Agent on every request to avoid detection."""

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        headers = get_full_headers()
        for key, value in headers.items():
            request.headers[key] = value
        spider.logger.debug(f"Using User-Agent: {request.headers.get('User-Agent', b'').decode()[:50]}...")
        return None


class RandomDelayMiddleware:
    """Adds random delays between requests to mimic human behavior."""

    def __init__(self, delay_range=(1.0, 3.0)):
        self.min_delay, self.max_delay = delay_range

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        min_delay = settings.getfloat('RANDOM_DELAY_MIN', 1.0)
        max_delay = settings.getfloat('RANDOM_DELAY_MAX', 3.0)
        return cls(delay_range=(min_delay, max_delay))

    def process_request(self, request, spider):
        if request.meta.get('dont_delay'):
            return None
        delay = random.uniform(self.min_delay, self.max_delay)
        spider.logger.debug(f"Adding random delay: {delay:.2f}s")
        time.sleep(delay)
        return None


class ProxyMiddleware:
    """Rotates proxies for each request. Enable by loading proxies from file."""

    @classmethod
    def from_crawler(cls, crawler):
        proxy_file = crawler.settings.get('PROXY_LIST_FILE')
        if proxy_file:
            proxy_manager.load_from_file(proxy_file)
        return cls()

    def process_request(self, request, spider):
        if request.meta.get('dont_proxy'):
            return None
        proxy = proxy_manager.get_proxy()
        if proxy:
            request.meta['proxy'] = proxy.to_url()
            request.meta['_proxy_obj'] = proxy
            spider.logger.debug(f"Using proxy: {proxy.host}:{proxy.port}")
        return None

    def process_response(self, request, response, spider):
        proxy = request.meta.get('_proxy_obj')
        if proxy:
            proxy_manager.mark_success(proxy)
        return response

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get('_proxy_obj')
        if proxy:
            proxy_manager.mark_failure(proxy)
            spider.logger.warning(f"Proxy failed: {proxy.host}:{proxy.port}")
        return None


class ExponentialBackoffRetryMiddleware(RetryMiddleware):
    """Enhanced retry middleware with exponential backoff."""

    def __init__(self, settings):
        super().__init__(settings)
        self.base_delay = settings.getfloat('RETRY_BASE_DELAY', 1.0)
        self.max_delay = settings.getfloat('RETRY_MAX_DELAY', 60.0)
        self.jitter = settings.getfloat('RETRY_JITTER', 0.5)
        additional_codes = settings.getlist('RETRY_EXTRA_HTTP_CODES', [403, 429, 500, 502, 503, 504])
        self.retry_http_codes = set(self.retry_http_codes) | set(additional_codes)

    def _get_retry_delay(self, retry_count):
        """Calculate exponential backoff delay with jitter"""
        delay = self.base_delay * (2 ** retry_count)
        delay = min(delay, self.max_delay)
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)
        return max(0.1, delay)

    def _retry(self, request, reason, spider):
        retry_count = request.meta.get('retry_count', 0)
        if retry_count < self.max_retry_times:
            delay = self._get_retry_delay(retry_count)
            spider.logger.warning(
                f"Retrying {request.url} (attempt {retry_count + 1}/{self.max_retry_times}) "
                f"after {delay:.2f}s - Reason: {reason}"
            )
            time.sleep(delay)
            retry_request = request.copy()
            retry_request.meta['retry_count'] = retry_count + 1
            retry_request.dont_filter = True
            headers = get_full_headers()
            for key, value in headers.items():
                retry_request.headers[key] = value
            return retry_request
        else:
            spider.logger.error(f"Max retries reached for {request.url}")
            return None

    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        return self._retry(request, str(exception), spider)


class CaptchaDetectionMiddleware:
    """Detects captcha pages and logs warnings."""

    @classmethod
    def from_crawler(cls, crawler):
        service = crawler.settings.get('CAPTCHA_SERVICE')
        api_key = crawler.settings.get('CAPTCHA_API_KEY')
        if service and api_key:
            from .captcha_handler import configure_captcha_solving
            configure_captcha_solving(service, api_key)
        return cls()

    def process_response(self, request, response, spider):
        has_captcha, captcha_type = captcha_handler.detect_captcha(response)
        if has_captcha:
            spider.logger.warning(f"Captcha detected ({captcha_type.value}) on {request.url}")
        return response
