"""
Indeed Spider - Scrapes jobs from Indeed for Egypt and UAE
Output should be combined with Wuzzuf results
"""

import scrapy
from urllib.parse import urlencode
import re


class IndeedSpider(scrapy.Spider):
    name = "indeed_jobs"
    
    # CV-based keywords for filtering
    relevant_keywords = [
        r'Designer', r'3D', r'Artist', r'CGI', r'Product', r'UI', r'UX', 
        r'Motion', r'Animation', r'Visualizer', r'Art Director', 
        r'Unreal', r'Blender', r'Generative', r'AI', r'Graphic',
        r'VFX', r'Creative', r'Frontend', r'Web', r'Digital'
    ]
    
    # Keywords to search based on CV
    search_keywords = [
        "Product Designer",
        "3D Artist",
        "CGI Artist",
        "UI UX Designer",
        "Motion Designer",
        "Generative AI",
        "Blender Artist",
        "Unreal Engine Developer"
    ]
    
    # Locations to search
    locations = [
        "Egypt",
        "UAE",
        "Dubai",
        "Remote"
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,  # Indeed is strict about rate limiting
        'CONCURRENT_REQUESTS': 4,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        for keyword in self.search_keywords:
            for location in self.locations:
                # Indeed URL structure
                params = {
                    'q': keyword,
                    'l': location,
                    'sort': 'date'  # Most recent first
                }
                
                # Indeed uses different domains for different regions
                # eg.indeed.com for Egypt, ae.indeed.com for UAE
                if location in ["Egypt"]:
                    base_url = "https://eg.indeed.com/jobs?"
                elif location in ["UAE", "Dubai"]:
                    base_url = "https://ae.indeed.com/jobs?"
                else:
                    base_url = "https://www.indeed.com/jobs?"
                
                url = f"{base_url}{urlencode(params)}"
                yield scrapy.Request(
                    url, 
                    callback=self.parse, 
                    meta={'keyword': keyword, 'location': location}
                )

    def parse(self, response):
        self.logger.info(f"Scraping Indeed: {response.url}")
        
        # Indeed job cards - these selectors may need updating as Indeed changes frequently
        # Common selectors: div.job_seen_beacon, div.jobsearch-ResultsList
        job_cards = response.css('div.job_seen_beacon')
        
        if not job_cards:
            # Try alternative selector
            job_cards = response.css('div.jobsearch-ResultsList > li')
            
        if not job_cards:
            self.logger.warning("No job cards found on Indeed page. Selectors may be outdated.")
            # Save HTML for debugging
            with open(f'indeed_debug_{response.meta.get("keyword", "unknown")}.html', 'wb') as f:
                f.write(response.body)
        
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        for card in job_cards:
            # Indeed structure varies, trying common patterns
            title = card.css('h2.jobTitle span::text').get()
            if not title:
                title = card.css('a.jcs-JobTitle span::text').get()
            if not title:
                title = card.css('.jobTitle::text').get()
                
            link = card.css('h2.jobTitle a::attr(href)').get()
            if not link:
                link = card.css('a.jcs-JobTitle::attr(href)').get()
            
            company = card.css('span.companyName::text').get()
            if not company:
                company = card.css('.companyName a::text').get()
                
            location = card.css('div.companyLocation::text').get()
            
            # Skip if title doesn't match CV keywords
            if title and not pattern.search(title):
                self.logger.info(f"Skipping irrelevant title: {title}")
                continue
            
            if title and link:
                # Make link absolute if relative
                if link.startswith('/'):
                    link = response.urljoin(link)
                    
                yield {
                    'keyword_searched': response.meta.get('keyword'),
                    'title': title.strip() if title else None,
                    'company': company.strip() if company else None,
                    'location': location.strip() if location else response.meta.get('location'),
                    'type': 'Full Time',  # Indeed doesn't always show this on listing
                    'link': link,
                    'source': 'Indeed'
                }
        
        # Pagination - Indeed uses 'start' parameter (0, 10, 20, etc.)
        current_start = response.meta.get('start', 0)
        next_start = current_start + 10
        
        # Limit to first 5 pages (50 results per keyword/location)
        if next_start < 50 and job_cards:
            next_url = response.url
            if 'start=' in next_url:
                next_url = re.sub(r'start=\d+', f'start={next_start}', next_url)
            else:
                next_url = f"{next_url}&start={next_start}"
            
            meta = response.meta.copy()
            meta['start'] = next_start
            yield scrapy.Request(next_url, callback=self.parse, meta=meta)
