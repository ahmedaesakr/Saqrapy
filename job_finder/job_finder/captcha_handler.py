"""
Captcha Handler - Detect Captchas on Scraped Pages
Detection only. Solving stubs removed (no API keys configured).
"""

import logging
import re
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class CaptchaType(Enum):
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    CLOUDFLARE = "cloudflare"
    IMAGE = "image"
    UNKNOWN = "unknown"


class CaptchaHandler:
    """
    Detects captcha pages so the spider can log warnings and skip them.
    """

    def __init__(self, service: str = None, api_key: str = None):
        self.service = service
        self.api_key = api_key
        self.enabled = bool(api_key)

    def detect_captcha(self, response) -> Tuple[bool, CaptchaType]:
        """
        Detect if a page has a captcha.
        Returns (has_captcha, captcha_type)
        """
        body = response.text if hasattr(response, 'text') else response.body.decode('utf-8', errors='ignore')

        if 'g-recaptcha' in body or 'grecaptcha' in body:
            sitekey = self._extract_recaptcha_sitekey(body)
            if sitekey:
                logger.info(f"Detected reCAPTCHA v2, sitekey: {sitekey}")
                return True, CaptchaType.RECAPTCHA_V2

        if 'recaptcha/api.js?render=' in body:
            return True, CaptchaType.RECAPTCHA_V3

        if 'hcaptcha' in body or 'h-captcha' in body:
            return True, CaptchaType.HCAPTCHA

        if 'cf-browser-verification' in body or 'Checking your browser' in body:
            return True, CaptchaType.CLOUDFLARE

        if 'captcha' in body.lower() and ('<img' in body or 'data:image' in body):
            return True, CaptchaType.IMAGE

        return False, CaptchaType.UNKNOWN

    def _extract_recaptcha_sitekey(self, html: str) -> Optional[str]:
        """Extract reCAPTCHA sitekey from HTML"""
        patterns = [
            r'data-sitekey=["\']([^"\']+)["\']',
            r'grecaptcha\.render\([^,]+,\s*\{[^}]*sitekey["\']?\s*:\s*["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None


# Global captcha handler instance
captcha_handler = CaptchaHandler()


def configure_captcha_solving(service: str, api_key: str):
    """Configure the global captcha handler"""
    global captcha_handler
    captcha_handler = CaptchaHandler(service=service, api_key=api_key)
    logger.info(f"Captcha solving configured with {service}")
