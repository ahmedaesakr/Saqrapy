# Scrapy settings for job_finder project with "Chad" capabilities
#
# ENHANCED FEATURES:
# - User-Agent Rotation
# - Random Delays (Human-like behavior)
# - Proxy Support (plug-and-play)
# - Retry Logic with Exponential Backoff
# - Captcha Detection

BOT_NAME = "job_finder"

SPIDER_MODULES = ["job_finder.spiders"]
NEWSPIDER_MODULE = "job_finder.spiders"

ADDONS = {}

# =============================================================================
# ANTI-DETECTION SETTINGS
# =============================================================================

# Default User-Agent (will be rotated by middleware)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# Ignore robots.txt - we're being stealthy
ROBOTSTXT_OBEY = False

# Concurrency settings (conservative for stealth)
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 2

# Random delay settings (used by RandomDelayMiddleware)
RANDOM_DELAY_MIN = 1.0
RANDOM_DELAY_MAX = 4.0

# =============================================================================
# RETRY SETTINGS (Exponential Backoff)
# =============================================================================

RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 403]
RETRY_BASE_DELAY = 2.0
RETRY_MAX_DELAY = 60.0
RETRY_JITTER = 0.3

# =============================================================================
# PROXY SETTINGS
# =============================================================================

# Uncomment and set path to enable proxy rotation
# PROXY_LIST_FILE = 'proxies.txt'

# =============================================================================
# CAPTCHA SETTINGS
# =============================================================================

# Configure captcha solving service (2captcha, anticaptcha)
# CAPTCHA_SERVICE = '2captcha'
# CAPTCHA_API_KEY = 'YOUR_API_KEY_HERE'

# =============================================================================
# COOKIE & HEADER SETTINGS
# =============================================================================

# Keep cookies enabled for session persistence
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# Spider middlewares
SPIDER_MIDDLEWARES = {
    "job_finder.middlewares.JobFinderSpiderMiddleware": 543,
}

# Downloader middlewares - ORDERED by priority (lower = earlier)
DOWNLOADER_MIDDLEWARES = {
    # First: Random User-Agent rotation
    "job_finder.middlewares.RandomUserAgentMiddleware": 400,
    
    # Second: Proxy rotation (if enabled)
    "job_finder.middlewares.ProxyMiddleware": 410,
    
    # Third: Random delays
    "job_finder.middlewares.RandomDelayMiddleware": 420,
    
    # Fourth: Captcha detection
    "job_finder.middlewares.CaptchaDetectionMiddleware": 430,
    
    # Fifth: Enhanced retry with backoff
    "job_finder.middlewares.ExponentialBackoffRetryMiddleware": 550,
    
    # Disable default retry middleware
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    
    # Default downloader middleware
    "job_finder.middlewares.JobFinderDownloaderMiddleware": 543,
}

# =============================================================================
# ITEM PIPELINES
# =============================================================================

ITEM_PIPELINES = {
    "job_finder.pipelines.CleaningPipeline": 100,
    "job_finder.pipelines.DeduplicationPipeline": 200,
}

# =============================================================================
# AUTOTHROTTLE SETTINGS
# =============================================================================

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# =============================================================================
# CACHE SETTINGS (for development/testing)
# =============================================================================

# Enable HTTP cache for faster development
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = [503, 500, 502, 504, 403, 429]
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# =============================================================================
# DOWNLOAD SETTINGS
# =============================================================================

DOWNLOAD_TIMEOUT = 30
DOWNLOAD_MAXSIZE = 10485760  # 10 MB

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

FEED_EXPORT_ENCODING = "utf-8"

# =============================================================================
# TELNET (disabled for security)
# =============================================================================

TELNETCONSOLE_ENABLED = False
