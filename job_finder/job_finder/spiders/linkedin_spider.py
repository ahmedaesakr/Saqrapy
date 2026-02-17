"""
LinkedIn Spider - Scrapes jobs from LinkedIn
Note: LinkedIn has strong anti-scraping measures. This spider uses the public jobs page
which doesn't require login, but may be limited in results.

For better results, consider using LinkedIn's official API or job alerts via email.
"""

import scrapy
from urllib.parse import urlencode
import re
from job_finder.cv_config import RELEVANT_KEYWORDS


class LinkedInSpider(scrapy.Spider):
    name = "linkedin_jobs"

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS
    
    # Keywords to search based on CV
    search_keywords = [
        "Product Designer",
        "3D Artist",
        "CGI Artist",
        "UI UX Designer",
        "Motion Graphics",
        "Generative AI Designer",
        "Unreal Engine Artist"
    ]
    
    # Location IDs for LinkedIn (these are LinkedIn's internal geo IDs)
    # Egypt: 106155005, UAE: 104305776
    locations = {
        "Egypt": "106155005",
        "UAE": "104305776",
    }
    
    custom_settings = {
        'DOWNLOAD_DELAY': 5,  # LinkedIn is very strict
        'CONCURRENT_REQUESTS': 2,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'COOKIES_ENABLED': False,
        'RETRY_TIMES': 2,
    }

    def start_requests(self):
        for keyword in self.search_keywords:
            for location_name, geo_id in self.locations.items():
                # LinkedIn public jobs URL
                params = {
                    'keywords': keyword,
                    'geoId': geo_id,
                    'f_TPR': 'r604800',  # Last week
                    'f_WT': '2',  # Remote filter (2 = Remote)
                    'position': '1',
                    'pageNum': '0'
                }
                
                base_url = "https://www.linkedin.com/jobs/search/?"
                url = f"{base_url}{urlencode(params)}"
                
                yield scrapy.Request(
                    url, 
                    callback=self.parse, 
                    meta={
                        'keyword': keyword, 
                        'location': location_name,
                        'page': 0
                    },
                    headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                    }
                )

    def parse(self, response):
        self.logger.info(f"Scraping LinkedIn: {response.url}")
        
        # Check if we got blocked
        if response.status == 429 or 'authwall' in response.url:
            self.logger.warning("LinkedIn is blocking requests. Consider using their API or slower scraping.")
            return
        
        # LinkedIn job cards on public page
        job_cards = response.css('div.base-card')
        
        if not job_cards:
            job_cards = response.css('li.jobs-search-results__list-item')
            
        if not job_cards:
            self.logger.warning("No job cards found on LinkedIn. Page may be JS-rendered or blocked.")
            # Save for debugging
            with open(f'output/debug/linkedin_debug_{response.meta.get("keyword", "unknown")}.html', 'wb') as f:
                f.write(response.body)
            return
        
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        for card in job_cards:
            title = card.css('h3.base-search-card__title::text').get()
            if not title:
                title = card.css('.base-card__title::text').get()
                
            link = card.css('a.base-card__full-link::attr(href)').get()
            
            company = card.css('h4.base-search-card__subtitle a::text').get()
            if not company:
                company = card.css('.base-search-card__subtitle::text').get()
                
            location = card.css('span.job-search-card__location::text').get()
            
            # Clean up text
            if title:
                title = title.strip()
            if company:
                company = company.strip()
            if location:
                location = location.strip()
            
            # Skip if title doesn't match CV keywords
            if title and not pattern.search(title):
                self.logger.info(f"Skipping irrelevant title: {title}")
                continue
            
            if title and link:
                yield {
                    'keyword_searched': response.meta.get('keyword'),
                    'title': title,
                    'company': company,
                    'location': location or response.meta.get('location'),
                    'type': 'Full Time',
                    'link': link,
                    'source': 'LinkedIn'
                }
        
        # Pagination - LinkedIn uses 'start' parameter
        current_page = response.meta.get('page', 0)
        next_page = current_page + 1
        
        # Limit to 3 pages to avoid being blocked
        if next_page < 3 and job_cards:
            next_url = response.url
            if 'pageNum=' in next_url:
                next_url = re.sub(r'pageNum=\d+', f'pageNum={next_page}', next_url)
            else:
                next_url = f"{next_url}&pageNum={next_page}"
            
            meta = response.meta.copy()
            meta['page'] = next_page
            yield scrapy.Request(next_url, callback=self.parse, meta=meta)
