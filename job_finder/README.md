# Job Finder - "Chad Mode" Edition 🕷️

A powerful, stealthy web scraping system for finding job opportunities with advanced anti-detection capabilities.

## Features

### 🎭 Anti-Detection & Stealth
- **User-Agent Rotation**: Randomizes browser fingerprint on every request
- **Random Delays**: Human-like timing between requests
- **Smart Headers**: Browser-matched Accept headers
- **AutoThrottle**: Adaptive rate limiting

### 🛡️ Resilience & Reliability
- **Proxy Support**: Easy plug-and-play proxy rotation
- **Exponential Backoff**: Smart retry with increasing delays
- **Graceful Error Handling**: Never crashes, always recovers

### ⚡ Power & Speed
- **Scrapy Framework**: Built on the fastest Python scraper
- **Playwright Integration**: For JavaScript-heavy sites (SPAs)
- **Concurrent Requests**: Parallel processing with safety limits

### 🔓 Bypassing Capabilities
- **Captcha Detection**: Identifies captcha pages
- **Captcha Solving Placeholder**: Ready for 2Captcha/Anti-Captcha integration
- **Cloudflare Handler**: Structure for CF bypass (FlareSolverr compatible)

## Spiders

| Spider | Description | Sites |
|--------|-------------|-------|
| `wuzzuf_jobs` | Egyptian job board | Wuzzuf |
| `indeed_jobs` | International job board | Indeed (EG, UAE) |
| `linkedin_jobs` | Professional network | LinkedIn |
| `freelance_jobs` | Freelance platforms | Mostaql, Khamsat, Upwork |
| `career_pages` | Company career pages | Multiple companies |
| `remote_jobs` | **NEW** Remote UAE/Europe | DuckDuckGo + 30+ companies |
| `playwright_jobs` | JS-heavy sites | LinkedIn, Glassdoor, Upwork |

## Quick Start

### 1. Install Dependencies
```bash
cd job_finder
pip install -r requirements.txt
```

### 2. Run All Spiders
```bash
# Windows
.\run_all_spiders.bat

# Or manually
cd job_finder
scrapy crawl remote_jobs -o output/remote_jobs.json
```

### 3. Run Playwright Spider (for JS sites)
```bash
# First install Playwright
pip install scrapy-playwright playwright
playwright install chromium

# Then run
.\run_playwright_spider.bat
```

## Configuration

### Enable Proxy Rotation
1. Create `proxies.txt` with your proxies:
```
host:port
host:port:username:password
```

2. Update `settings.py`:
```python
PROXY_LIST_FILE = 'proxies.txt'
```

### Enable Captcha Solving
1. Get API key from 2Captcha or Anti-Captcha
2. Update `settings.py`:
```python
CAPTCHA_SERVICE = '2captcha'
CAPTCHA_API_KEY = 'YOUR_KEY'
```

## Output

Jobs are saved to `job_finder/output/` as JSON, then converted to Excel:
- `all_jobs.xlsx` - Separate sheets per source
- `all_jobs_combined.xlsx` - All jobs in one sheet

## CV Keywords

All spiders filter jobs based on these keywords:
- Designer, 3D, Artist, CGI, Product, UI/UX
- Motion, Animation, Visualizer, Art Director
- Unreal, Blender, Generative AI, VFX
- Creative, Frontend, Web, Digital

Edit the `relevant_keywords` list in each spider to customize.

## Stealth Settings

Default settings in `settings.py`:
```python
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 2
RANDOM_DELAY_MIN = 1.0
RANDOM_DELAY_MAX = 4.0
RETRY_TIMES = 5
```

For maximum stealth, increase delays and reduce concurrency.

## License

MIT License - Use responsibly and respect robots.txt where appropriate.
