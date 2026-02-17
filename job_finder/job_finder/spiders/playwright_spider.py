"""
Playwright Async Spider - For JavaScript-Heavy Sites
Uses Playwright for true browser automation with stealth capabilities.

This spider can handle:
- Single Page Applications (SPAs)
- JavaScript-rendered content
- Dynamic loading
- Anti-bot measures (via stealth mode)

INSTALLATION:
    pip install scrapy-playwright playwright
    playwright install chromium
"""

import asyncio
import scrapy
from scrapy import signals
import re
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urlencode
from job_finder.cv_config import RELEVANT_KEYWORDS

logger = logging.getLogger(__name__)

# Try to import Playwright items - will be None if not installed
try:
    from scrapy_playwright.page import PageMethod
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PageMethod = None
    logger.warning("scrapy-playwright not installed. Run: pip install scrapy-playwright")


class PlaywrightJobsSpider(scrapy.Spider):
    """
    Async spider using Playwright for JavaScript-heavy job sites.
    Handles SPAs, dynamic content, and anti-bot measures.
    """
    
    name = "playwright_jobs"
    
    # CV-based keywords
    relevant_keywords = RELEVANT_KEYWORDS
    
    # Sites that require JavaScript rendering
    js_heavy_sites = [
        {
            "name": "LinkedIn Jobs",
            "url": "https://www.linkedin.com/jobs/search/?keywords=product%20designer&location=United%20Arab%20Emirates&f_WT=2",
            "wait_for": "div.base-card",
            "region": "UAE"
        },
        {
            "name": "LinkedIn Jobs Europe",
            "url": "https://www.linkedin.com/jobs/search/?keywords=3d%20artist&location=Europe&f_WT=2",
            "wait_for": "div.base-card",
            "region": "Europe"
        },
        {
            "name": "Glassdoor Remote",
            "url": "https://www.glassdoor.com/Job/remote-designer-jobs-SRCH_IL.0,6_IS11047_KO7,15.htm",
            "wait_for": '[data-test="job-link"]',
            "region": "Remote"
        },
        {
            "name": "Upwork Design Jobs",
            "url": "https://www.upwork.com/nx/jobs/search/?sort=recency&q=3d%20designer",
            "wait_for": 'section[data-test="job-tile"]',
            "region": "Remote"
        },
    ]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920x1080',
            ]
        },
        'PLAYWRIGHT_CONTEXTS': {
            'default': {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
            }
        },
        'DOWNLOAD_DELAY': 5,
        'CONCURRENT_REQUESTS': 2,
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        return spider
    
    def spider_opened(self, spider):
        if not PLAYWRIGHT_AVAILABLE:
            logger.error(
                "Playwright not available! Install with:\n"
                "  pip install scrapy-playwright playwright\n"
                "  playwright install chromium"
            )
    
    def start_requests(self):
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Cannot start: scrapy-playwright not installed")
            return
        
        for site in self.js_heavy_sites:
            yield scrapy.Request(
                site['url'],
                callback=self.parse_js_page,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        # Wait for dynamic content to load
                        PageMethod('wait_for_selector', site.get('wait_for', 'body'), timeout=15000),
                        # Simulate human scroll behavior
                        PageMethod('evaluate', '''
                            async () => {
                                await new Promise(r => setTimeout(r, 1000));
                                for (let i = 0; i < 3; i++) {
                                    window.scrollBy(0, 300);
                                    await new Promise(r => setTimeout(r, 500));
                                }
                            }
                        '''),
                    ],
                    'site_name': site['name'],
                    'region': site['region'],
                },
                errback=self.handle_error,
            )
    
    async def parse_js_page(self, response):
        """Parse JavaScript-rendered page"""
        site_name = response.meta.get('site_name', 'Unknown')
        region = response.meta.get('region', 'Remote')
        page = response.meta.get('playwright_page')
        
        logger.info(f"Parsing JS page: {site_name}")
        
        try:
            # Get full page content after JS execution
            content = await page.content()
            
            # Close the page to free resources
            await page.close()
        except Exception as e:
            logger.error(f"Error with Playwright page: {e}")
            return
        
        # Create pattern for CV keywords
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        # Parse based on site and yield results
        # Note: Can't use 'yield from' in async function, so we iterate and yield
        results = []
        if 'linkedin' in response.url.lower():
            results = list(self._parse_linkedin(response, content, pattern, region))
        elif 'glassdoor' in response.url.lower():
            results = list(self._parse_glassdoor(response, content, pattern, region))
        elif 'upwork' in response.url.lower():
            results = list(self._parse_upwork(response, content, pattern, region))
        else:
            results = list(self._parse_generic(response, content, pattern, site_name, region))
        
        for item in results:
            yield item
    
    def _parse_linkedin(self, response, content, pattern, region):
        """Parse LinkedIn job cards"""
        from scrapy import Selector
        sel = Selector(text=content)
        
        job_cards = sel.css('div.base-card, div.job-search-card')
        
        for card in job_cards:
            title = card.css('h3.base-search-card__title::text, .job-title::text').get()
            if title:
                title = title.strip()
            
            if not title or not pattern.search(title):
                continue
            
            link = card.css('a.base-card__full-link::attr(href)').get()
            company = card.css('h4.base-search-card__subtitle a::text, .company-name::text').get()
            location = card.css('span.job-search-card__location::text').get()
            
            yield {
                'keyword_searched': 'Playwright LinkedIn',
                'title': title,
                'company': company.strip() if company else 'Unknown',
                'location': location.strip() if location else region,
                'region': region,
                'type': 'Remote',
                'link': link,
                'source': 'LinkedIn (Playwright)'
            }
    
    def _parse_glassdoor(self, response, content, pattern, region):
        """Parse Glassdoor job listings"""
        from scrapy import Selector
        sel = Selector(text=content)
        
        job_cards = sel.css('[data-test="job-link"], .job-listing')
        
        for card in job_cards:
            title = card.css('::text').get()
            if title:
                title = title.strip()
            
            if not title or not pattern.search(title):
                continue
            
            link = card.css('::attr(href)').get()
            if link and not link.startswith('http'):
                link = response.urljoin(link)
            
            yield {
                'keyword_searched': 'Playwright Glassdoor',
                'title': title,
                'company': 'Via Glassdoor',
                'location': region,
                'region': region,
                'type': 'Remote',
                'link': link,
                'source': 'Glassdoor (Playwright)'
            }
    
    def _parse_upwork(self, response, content, pattern, region):
        """Parse Upwork job tiles"""
        from scrapy import Selector
        sel = Selector(text=content)
        
        job_tiles = sel.css('section[data-test="job-tile"], article.job-tile')
        
        for tile in job_tiles:
            title = tile.css('h2 a::text, .job-title-link::text').get()
            if title:
                title = title.strip()
            
            if not title or not pattern.search(title):
                continue
            
            link = tile.css('h2 a::attr(href), .job-title-link::attr(href)').get()
            if link and not link.startswith('http'):
                link = f"https://www.upwork.com{link}"
            
            budget = tile.css('[data-test="budget"]::text, .job-budget::text').get()
            
            yield {
                'keyword_searched': 'Playwright Upwork',
                'title': title,
                'company': 'Upwork Client',
                'location': 'Remote',
                'region': 'Remote',
                'type': 'Freelance',
                'budget': budget.strip() if budget else None,
                'link': link,
                'source': 'Upwork (Playwright)'
            }
    
    def _parse_generic(self, response, content, pattern, site_name, region):
        """Generic parser for unknown sites"""
        from scrapy import Selector
        sel = Selector(text=content)
        
        # Try common job listing selectors
        links = sel.css('''
            a[href*="job"], 
            a[href*="position"], 
            a[href*="career"],
            .job-listing a,
            .job-card a
        ''')
        
        for link in links:
            title = link.css('::text').get()
            if not title:
                title = ' '.join(link.css('*::text').getall())
            
            if title:
                title = title.strip()
            
            if not title or not pattern.search(title):
                continue
            
            href = link.css('::attr(href)').get()
            if href and not href.startswith('http'):
                href = response.urljoin(href)
            
            yield {
                'keyword_searched': 'Playwright Generic',
                'title': title[:200],  # Limit title length
                'company': f'Via {site_name}',
                'location': region,
                'region': region,
                'type': 'Remote',
                'link': href,
                'source': f'{site_name} (Playwright)'
            }
    
    def handle_error(self, failure):
        """Handle request failures"""
        logger.error(f"Playwright request failed: {failure.request.url}")
        logger.error(f"Error: {failure.value}")
