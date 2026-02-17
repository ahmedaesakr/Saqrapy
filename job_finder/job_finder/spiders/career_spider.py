"""
Company Career Pages Spider
Scrapes job listings directly from company career pages that are relevant to your CV.

These are companies in Egypt/UAE that commonly hire designers, 3D artists, etc.
"""

import scrapy
import re
from job_finder.cv_config import RELEVANT_KEYWORDS


class CareerPagesSpider(scrapy.Spider):
    name = "career_pages"

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS
    
    # List of company career pages to scrape
    # These are companies in Egypt/UAE that hire creative/tech talent
    company_pages = [
        # Egypt Companies
        {
            'name': 'Vodafone Egypt',
            'url': 'https://careers.vodafone.com/search-jobs?location=egypt',
            'location': 'Egypt'
        },
        {
            'name': 'Orange Egypt',
            'url': 'https://orange.jobs/site/en-home.html',
            'location': 'Egypt'
        },
        {
            'name': 'Instabug',
            'url': 'https://instabug.com/careers',
            'location': 'Egypt'
        },
        {
            'name': 'Swvl',
            'url': 'https://www.swvl.com/careers',
            'location': 'Egypt/UAE'
        },
        {
            'name': 'Fawry',
            'url': 'https://fawry.com/careers/',
            'location': 'Egypt'
        },
        # UAE Companies
        {
            'name': 'Careem',
            'url': 'https://www.careem.com/careers/',
            'location': 'UAE'
        },
        {
            'name': 'noon',
            'url': 'https://www.noonacademy.com/career',
            'location': 'UAE'
        },
        {
            'name': 'Kitopi',
            'url': 'https://www.kitopi.com/careers',
            'location': 'UAE'
        },
        # Gaming/Creative Studios
        {
            'name': 'Ubisoft Abu Dhabi',
            'url': 'https://www.ubisoft.com/en-us/company/careers/locations/abu-dhabi',
            'location': 'UAE'
        },
        {
            'name': 'Virtuzone',
            'url': 'https://www.vz.ae/careers/',
            'location': 'UAE'
        },
        # Architecture/Design Studios
        {
            'name': 'Perkins&Will Dubai',
            'url': 'https://perkinswill.com/careers/',
            'location': 'UAE'
        },
        # More can be added...
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 4,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        for company in self.company_pages:
            yield scrapy.Request(
                company['url'],
                callback=self.parse,
                meta={
                    'company_name': company['name'],
                    'location': company['location']
                },
                errback=self.handle_error
            )

    def handle_error(self, failure):
        self.logger.error(f"Failed to scrape: {failure.request.url}")

    def parse(self, response):
        self.logger.info(f"Scraping career page: {response.url}")
        
        company_name = response.meta.get('company_name')
        location = response.meta.get('location')
        
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        # Generic selectors that work for many career pages
        # These need to be broad since every site is different
        job_links = response.css('a[href*="job"], a[href*="career"], a[href*="position"], a[href*="opening"]')
        
        if not job_links:
            # Try to find any links with job-related text
            job_links = response.xpath('//a[contains(text(), "Designer") or contains(text(), "Artist") or contains(text(), "Creative") or contains(text(), "3D") or contains(text(), "Product")]')
        
        seen_links = set()
        
        for link in job_links:
            title = link.css('::text').get()
            href = link.css('::attr(href)').get()
            
            if not title or not href:
                continue
                
            title = title.strip()
            
            # Skip if not relevant to CV
            if not pattern.search(title):
                continue
            
            # Make link absolute
            if href.startswith('/'):
                href = response.urljoin(href)
            elif not href.startswith('http'):
                continue
            
            # Avoid duplicates
            if href in seen_links:
                continue
            seen_links.add(href)
            
            yield {
                'keyword_searched': 'Career Page',
                'title': title,
                'company': company_name,
                'location': location,
                'type': 'Full Time',
                'link': href,
                'source': f'Career Page - {company_name}'
            }
        
        # Also look for job listings in common structures
        job_cards = response.css('.job-listing, .job-card, .position-item, .career-item, li.job, div[class*="job"]')
        
        for card in job_cards:
            title = card.css('h2::text, h3::text, .job-title::text, .title::text, a::text').get()
            href = card.css('a::attr(href)').get()
            
            if not title:
                continue
                
            title = title.strip()
            
            if not pattern.search(title):
                continue
            
            if href:
                if href.startswith('/'):
                    href = response.urljoin(href)
                elif not href.startswith('http'):
                    href = None
            
            if href and href not in seen_links:
                seen_links.add(href)
                yield {
                    'keyword_searched': 'Career Page',
                    'title': title,
                    'company': company_name,
                    'location': location,
                    'type': 'Full Time',
                    'link': href,
                    'source': f'Career Page - {company_name}'
                }
