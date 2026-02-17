"""
Remote Jobs Europe/UAE Spider - "Chad Mode" Edition

This spider searches for remote positions from companies in UAE and Europe.
It uses web search to discover company career pages and scrapes job listings.

Features:
- Google/DuckDuckGo search to find company career pages
- Filters for remote positions only
- Targets companies in UAE and European countries
- Uses all "Chad" anti-detection capabilities
"""

import scrapy
import re
import json
from urllib.parse import urlencode, quote_plus
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RemoteJobsSpider(scrapy.Spider):
    """
    Spider that searches for remote job positions in UAE and Europe.
    Uses web search to discover career pages and extracts job listings.
    """
    
    name = "remote_jobs"
    
    # CV-based keywords for job filtering
    relevant_keywords = [
        r'Designer', r'3D', r'Artist', r'CGI', r'Product', r'UI', r'UX', 
        r'Motion', r'Animation', r'Visualizer', r'Art Director', 
        r'Unreal', r'Blender', r'Generative', r'AI', r'Graphic',
        r'VFX', r'Creative', r'Frontend', r'Web', r'Digital',
        r'Remote', r'Hybrid'
    ]
    
    # Search queries for finding remote jobs
    search_queries = [
        "remote 3D artist jobs UAE",
        "remote product designer jobs Europe",
        "remote UI UX designer jobs Dubai",
        "remote motion graphics jobs Europe",
        "remote CGI artist jobs",
        "remote generative AI designer jobs",
        "remote Blender artist jobs Europe",
        "remote Unreal Engine jobs Europe",
        "remote creative director jobs UAE Dubai",
        "remote web designer jobs Germany",
        "remote frontend developer jobs Netherlands",
        "remote digital designer jobs UK",
    ]
    
    # Curated list of companies with remote positions (UAE, Europe)
    known_remote_companies = {
        # UAE Companies with Remote Culture
        "UAE": [
            {
                "name": "Careem",
                "url": "https://www.careem.com/en-ae/careers/",
                "type": "Tech"
            },
            {
                "name": "noon",
                "url": "https://careers.noon.com/",
                "type": "E-commerce"
            },
            {
                "name": "Talabat",
                "url": "https://www.talabat.com/careers",
                "type": "Tech"
            },
            {
                "name": "Property Finder",
                "url": "https://www.propertyfinder.ae/en/careers",
                "type": "Tech"
            },
            {
                "name": "Dubizzle",
                "url": "https://dubizzle.com/careers",
                "type": "Tech"
            },
            {
                "name": "Bayt",
                "url": "https://www.bayt.com/en/careers/",
                "type": "HR Tech"
            },
        ],
        
        # European Companies with Remote-First/Hybrid Culture
        "Europe": [
            # Germany
            {
                "name": "Delivery Hero",
                "url": "https://careers.deliveryhero.com/",
                "country": "Germany",
                "type": "Tech"
            },
            {
                "name": "Zalando",
                "url": "https://jobs.zalando.com/en/jobs/",
                "country": "Germany",
                "type": "E-commerce"
            },
            {
                "name": "N26",
                "url": "https://n26.com/en/careers",
                "country": "Germany",
                "type": "Fintech"
            },
            {
                "name": "SoundCloud",
                "url": "https://careers.soundcloud.com/",
                "country": "Germany",
                "type": "Music Tech"
            },
            
            # Netherlands
            {
                "name": "Booking.com",
                "url": "https://careers.booking.com/",
                "country": "Netherlands",
                "type": "Travel Tech"
            },
            {
                "name": "Adyen",
                "url": "https://careers.adyen.com/",
                "country": "Netherlands",
                "type": "Fintech"
            },
            
            # UK
            {
                "name": "Revolut",
                "url": "https://www.revolut.com/careers/",
                "country": "UK",
                "type": "Fintech"
            },
            {
                "name": "Monzo",
                "url": "https://monzo.com/careers/",
                "country": "UK",
                "type": "Fintech"
            },
            {
                "name": "Canva",
                "url": "https://www.canva.com/careers/",
                "country": "UK",
                "type": "Design Tech"
            },
            {
                "name": "Figma",
                "url": "https://www.figma.com/careers/",
                "country": "UK",
                "type": "Design Tech"
            },
            
            # Sweden
            {
                "name": "Spotify",
                "url": "https://www.lifeatspotify.com/jobs",
                "country": "Sweden",
                "type": "Music Tech"
            },
            {
                "name": "Klarna",
                "url": "https://www.klarna.com/careers/",
                "country": "Sweden",
                "type": "Fintech"
            },
            
            # France
            {
                "name": "Datadog",
                "url": "https://careers.datadoghq.com/",
                "country": "France",
                "type": "Tech"
            },
            {
                "name": "Criteo",
                "url": "https://careers.criteo.com/",
                "country": "France",
                "type": "Ad Tech"
            },
            
            # Remote-First Companies
            {
                "name": "GitLab",
                "url": "https://about.gitlab.com/jobs/",
                "country": "Remote-First",
                "type": "Tech"
            },
            {
                "name": "Automattic (WordPress)",
                "url": "https://automattic.com/work-with-us/",
                "country": "Remote-First",
                "type": "Tech"
            },
            {
                "name": "Toptal",
                "url": "https://www.toptal.com/careers",
                "country": "Remote-First",
                "type": "Freelance Platform"
            },
        ]
    }
    
    # Job boards for remote work
    remote_job_boards = [
        {
            "name": "Remote OK",
            "url": "https://remoteok.com/remote-design-jobs",
            "type": "board"
        },
        {
            "name": "We Work Remotely",
            "url": "https://weworkremotely.com/categories/remote-design-jobs",
            "type": "board"
        },
        {
            "name": "FlexJobs",
            "url": "https://www.flexjobs.com/search?search=designer&location=",
            "type": "board"
        },
        {
            "name": "AngelList Talent",
            "url": "https://angel.co/jobs",
            "type": "board"
        },
        {
            "name": "EU Remote Jobs",
            "url": "https://euremotejobs.com/categories/design/",
            "type": "board"
        },
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 4,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
    }
    
    def start_requests(self):
        """Generate initial requests from multiple sources"""
        
        # 1. Search engine queries (using DuckDuckGo - more scrape-friendly)
        for query in self.search_queries[:5]:  # Limit initial queries
            duckduckgo_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            yield scrapy.Request(
                duckduckgo_url,
                callback=self.parse_search_results,
                meta={
                    'query': query,
                    'source': 'DuckDuckGo'
                },
                errback=self.handle_error
            )
        
        # 2. Known company career pages - UAE
        for company in self.known_remote_companies.get("UAE", []):
            yield scrapy.Request(
                company['url'],
                callback=self.parse_career_page,
                meta={
                    'company_name': company['name'],
                    'region': 'UAE',
                    'company_type': company.get('type', 'Unknown')
                },
                errback=self.handle_error
            )
        
        # 3. Known company career pages - Europe
        for company in self.known_remote_companies.get("Europe", []):
            yield scrapy.Request(
                company['url'],
                callback=self.parse_career_page,
                meta={
                    'company_name': company['name'],
                    'region': 'Europe',
                    'country': company.get('country', 'Europe'),
                    'company_type': company.get('type', 'Unknown')
                },
                errback=self.handle_error
            )
        
        # 4. Remote job boards
        for board in self.remote_job_boards:
            yield scrapy.Request(
                board['url'],
                callback=self.parse_remote_job_board,
                meta={
                    'board_name': board['name'],
                    'source': f"Remote Board - {board['name']}"
                },
                errback=self.handle_error
            )
    
    def handle_error(self, failure):
        """Handle request failures gracefully"""
        logger.error(f"Request failed: {failure.request.url}")
        logger.error(f"Error: {failure.value}")
    
    def parse_search_results(self, response):
        """Parse search engine results to find career pages"""
        logger.info(f"Parsing search results for: {response.meta.get('query')}")
        
        # DuckDuckGo result links
        results = response.css('a.result__a')
        
        for result in results[:10]:  # Limit results per query
            link = result.css('::attr(href)').get()
            title = result.css('::text').get()
            
            if not link:
                continue
            
            # Filter for career-related pages
            career_indicators = ['career', 'job', 'hiring', 'work-with-us', 'join', 'opportunities']
            if any(ind in link.lower() for ind in career_indicators):
                yield scrapy.Request(
                    link,
                    callback=self.parse_career_page,
                    meta={
                        'company_name': self._extract_company_name(title, link),
                        'region': 'Remote/International',
                        'source': 'Search Discovery'
                    },
                    errback=self.handle_error
                )
    
    def _extract_company_name(self, title: str, url: str) -> str:
        """Try to extract company name from title or URL"""
        if title:
            # Remove common suffixes
            name = re.sub(r'\s*(careers?|jobs?|hiring|opportunities).*$', '', title, flags=re.I)
            if name.strip():
                return name.strip()[:50]
        
        # Extract from URL
        domain = url.split('//')[-1].split('/')[0]
        name = domain.replace('www.', '').split('.')[0]
        return name.title()
    
    def parse_career_page(self, response):
        """Parse a company career page for job listings"""
        company_name = response.meta.get('company_name', 'Unknown')
        region = response.meta.get('region', 'Unknown')
        country = response.meta.get('country', region)
        
        logger.info(f"Parsing career page: {company_name} ({response.url})")
        
        # Create CV keyword pattern
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        remote_pattern = re.compile(r'\b(remote|hybrid|work\s*from\s*home|wfh|distributed)\b', re.IGNORECASE)
        
        seen_links = set()
        
        # Try multiple selector strategies (sites vary widely)
        selectors = [
            # Common job listing structures
            'a[href*="job"]',
            'a[href*="position"]',
            'a[href*="opening"]',
            'a[href*="career"]',
            '.job-listing a',
            '.job-card a',
            '.position-item a',
            '.career-item a',
            'li.job a',
            'div[class*="job"] a',
            'article[class*="job"] a',
            
            # Modern frameworks
            '[data-job-id] a',
            '[data-position] a',
            '.jobs-list a',
            '.openings a',
        ]
        
        for selector in selectors:
            links = response.css(selector)
            
            for link in links:
                href = link.css('::attr(href)').get()
                title = link.css('::text').get()
                
                if not href or not title:
                    # Try getting text from child elements
                    title = ' '.join(link.css('*::text').getall()).strip()
                
                if not title or not href:
                    continue
                    
                title = title.strip()
                
                # Make link absolute
                if href.startswith('/'):
                    href = response.urljoin(href)
                elif not href.startswith('http'):
                    continue
                
                # Dedup
                if href in seen_links:
                    continue
                seen_links.add(href)
                
                # Check relevance to CV
                if not pattern.search(title):
                    continue
                
                # Check if remote
                is_remote = remote_pattern.search(title) or 'remote' in href.lower()
                job_type = 'Remote' if is_remote else 'Hybrid/On-site'
                
                yield {
                    'keyword_searched': 'Remote Job Search',
                    'title': title,
                    'company': company_name,
                    'location': f"{country} ({job_type})",
                    'region': region,
                    'type': job_type,
                    'link': href,
                    'source': f'Career Page - {company_name}'
                }
        
        # Also check for structured job data (JSON-LD)
        for script in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script)
                jobs = self._extract_jobs_from_jsonld(data, company_name, region)
                for job in jobs:
                    if pattern.search(job.get('title', '')):
                        yield job
            except json.JSONDecodeError:
                continue
    
    def _extract_jobs_from_jsonld(self, data, company_name, region) -> List[Dict]:
        """Extract jobs from JSON-LD structured data"""
        jobs = []
        
        if isinstance(data, list):
            for item in data:
                jobs.extend(self._extract_jobs_from_jsonld(item, company_name, region))
        elif isinstance(data, dict):
            if data.get('@type') == 'JobPosting':
                title = data.get('title', '')
                url = data.get('url', '')
                location = data.get('jobLocation', {})
                
                if isinstance(location, dict):
                    location_str = location.get('address', {}).get('addressLocality', region)
                else:
                    location_str = region
                
                jobs.append({
                    'keyword_searched': 'Remote Job Search',
                    'title': title,
                    'company': company_name,
                    'location': location_str,
                    'region': region,
                    'type': 'Full Time',
                    'link': url,
                    'source': f'Career Page (Structured) - {company_name}'
                })
        
        return jobs
    
    def parse_remote_job_board(self, response):
        """Parse remote work job boards"""
        board_name = response.meta.get('board_name', 'Unknown')
        
        logger.info(f"Parsing remote job board: {board_name}")
        
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        # Generic job card selectors for job boards
        job_cards = response.css('''
            .job-listing,
            .job-card,
            .job-item,
            article.job,
            li.job,
            div[class*="job-row"],
            tr[class*="job"]
        ''')
        
        if not job_cards:
            # Try broader selectors
            job_cards = response.css('a[href*="job"], a[href*="position"]')
        
        for card in job_cards:
            # Try multiple title selectors
            title = (
                card.css('h2::text, h3::text, .job-title::text, .title::text').get() or
                card.css('a::text').get() or
                ' '.join(card.css('a *::text').getall())
            )
            
            if not title:
                continue
                
            title = title.strip()
            
            if not pattern.search(title):
                continue
            
            href = card.css('a::attr(href)').get()
            if href:
                if not href.startswith('http'):
                    href = response.urljoin(href)
                
                company = card.css('.company::text, .company-name::text').get() or 'Via ' + board_name
                location = card.css('.location::text, .job-location::text').get() or 'Remote'
                
                yield {
                    'keyword_searched': 'Remote Job Board',
                    'title': title,
                    'company': company.strip() if company else f'Via {board_name}',
                    'location': location.strip() if location else 'Remote',
                    'region': 'Remote/International',
                    'type': 'Remote',
                    'link': href,
                    'source': f'Job Board - {board_name}'
                }
