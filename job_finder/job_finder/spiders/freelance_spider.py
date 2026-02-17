"""
Freelance Spider - Scrapes freelance projects from various platforms
Targets: Upwork, Freelancer, Mostaql (Arabic), Khamsat (Arabic)
"""

import scrapy
from urllib.parse import urlencode
import re
from job_finder.cv_config import RELEVANT_KEYWORDS, FREELANCE_EXTRA_KEYWORDS, is_relevant


class FreelanceSpider(scrapy.Spider):
    name = "freelance_jobs"

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS + FREELANCE_EXTRA_KEYWORDS
    
    # Keywords to search based on CV - simpler for freelance platforms
    search_keywords = [
        "3D",
        "blender",
        "product design",
        "ui ux",
        "motion graphics",
        "video editing",
        "graphic design",
        "unreal engine"
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 4,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        # Mostaql (Arabic freelance platform - good for MENA region)
        for keyword in self.search_keywords:
            mostaql_url = f"https://mostaql.com/projects?keyword={keyword}"
            yield scrapy.Request(
                mostaql_url,
                callback=self.parse_mostaql,
                meta={'keyword': keyword, 'platform': 'Mostaql'}
            )
        
        # Khamsat (Arabic microservices platform)
        for keyword in self.search_keywords[:4]:  # Limit keywords for Khamsat
            khamsat_url = f"https://khamsat.com/search?query={keyword}"
            yield scrapy.Request(
                khamsat_url,
                callback=self.parse_khamsat,
                meta={'keyword': keyword, 'platform': 'Khamsat'}
            )
        
        # Upwork RSS feeds (public, no auth needed)
        upwork_keywords = ["3d-design", "product-design", "ui-ux-design", "motion-graphics", "blender"]
        for keyword in upwork_keywords:
            # Upwork public job search
            upwork_url = f"https://www.upwork.com/freelance-jobs/{keyword}/"
            yield scrapy.Request(
                upwork_url,
                callback=self.parse_upwork,
                meta={'keyword': keyword, 'platform': 'Upwork'}
            )

    def parse_mostaql(self, response):
        """Parse Mostaql (مستقل) freelance projects"""
        self.logger.info(f"Scraping Mostaql: {response.url}")
        
        # Mostaql project cards
        projects = response.css('div.project-row, article.project')
        
        if not projects:
            self.logger.warning("No projects found on Mostaql")
            
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        for project in projects:
            title = project.css('h2 a::text, .project-title a::text').get()
            link = project.css('h2 a::attr(href), .project-title a::attr(href)').get()
            budget = project.css('.project-budget::text, .budget::text').get()
            description = project.css('.project-brief::text, .project-description::text').get()
            
            if title:
                title = title.strip()
                
            # Filter based on CV keywords
            text_to_check = f"{title or ''} {description or ''}"
            if not pattern.search(text_to_check):
                continue
            
            if title and link:
                if not link.startswith('http'):
                    link = f"https://mostaql.com{link}"
                    
                yield {
                    'keyword_searched': response.meta.get('keyword'),
                    'title': title,
                    'company': 'Freelance Client',
                    'location': 'Remote',
                    'type': 'Freelance',
                    'budget': budget.strip() if budget else None,
                    'link': link,
                    'source': 'Mostaql'
                }
        
        # Pagination
        next_page = response.css('a.pagination-next::attr(href), .next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_mostaql, meta=response.meta)

    def parse_khamsat(self, response):
        """Parse Khamsat (خمسات) microservices"""
        self.logger.info(f"Scraping Khamsat: {response.url}")
        
        # Khamsat service cards
        services = response.css('div.service-box, article.service')
        
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        for service in services:
            title = service.css('h3 a::text, .service-title a::text').get()
            link = service.css('h3 a::attr(href), .service-title a::attr(href)').get()
            price = service.css('.price::text, .service-price::text').get()
            
            if title:
                title = title.strip()
                
            if not pattern.search(title or ''):
                continue
            
            if title and link:
                if not link.startswith('http'):
                    link = f"https://khamsat.com{link}"
                    
                yield {
                    'keyword_searched': response.meta.get('keyword'),
                    'title': title,
                    'company': 'Khamsat Seller',
                    'location': 'Remote',
                    'type': 'Freelance/Gig',
                    'budget': price.strip() if price else None,
                    'link': link,
                    'source': 'Khamsat'
                }

    def parse_upwork(self, response):
        """Parse Upwork public job listings"""
        self.logger.info(f"Scraping Upwork: {response.url}")
        
        # Upwork may block or require JS, but let's try
        jobs = response.css('article.job-tile, div.job-tile-content')
        
        if not jobs:
            self.logger.warning("No jobs found on Upwork - page may require JavaScript")
            return
        
        pattern = re.compile(r'\b(' + '|'.join(self.relevant_keywords) + r')\b', re.IGNORECASE)
        
        for job in jobs:
            title = job.css('h2.job-title a::text, .job-title-link::text').get()
            link = job.css('h2.job-title a::attr(href), .job-title-link::attr(href)').get()
            budget = job.css('.js-budget::text, .budget::text').get()
            
            if title:
                title = title.strip()
                
            if not pattern.search(title or ''):
                continue
            
            if title and link:
                if not link.startswith('http'):
                    link = f"https://www.upwork.com{link}"
                    
                yield {
                    'keyword_searched': response.meta.get('keyword'),
                    'title': title,
                    'company': 'Upwork Client',
                    'location': 'Remote',
                    'type': 'Freelance',
                    'budget': budget.strip() if budget else None,
                    'link': link,
                    'source': 'Upwork'
                }
