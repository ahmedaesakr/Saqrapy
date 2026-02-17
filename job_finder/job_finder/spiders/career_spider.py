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
    # Companies in Egypt, Saudi Arabia, UAE, and Gulf that hire creative/tech talent
    company_pages = [
        # ══════════════════════════════════════════
        # EGYPT - Tech & Creative Companies
        # ══════════════════════════════════════════
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
        {
            'name': 'Wuzzuf (HALAN)',
            'url': 'https://www.halan.com/careers',
            'location': 'Egypt'
        },
        {
            'name': 'Valeo Egypt',
            'url': 'https://www.valeo.com/en/find-a-job/',
            'location': 'Egypt'
        },
        {
            'name': 'Si-Ware Systems',
            'url': 'https://www.si-ware.com/careers',
            'location': 'Egypt'
        },
        {
            'name': 'Breadfast',
            'url': 'https://breadfast.com/careers',
            'location': 'Egypt'
        },
        # Egypt Creative / Design Studios
        {
            'name': 'Kijamii (Digital Agency)',
            'url': 'https://www.kijamii.com/careers/',
            'location': 'Egypt'
        },
        {
            'name': 'Elmenus',
            'url': 'https://www.elmenus.com/careers',
            'location': 'Egypt'
        },
        {
            'name': 'Rabbit (Delivery)',
            'url': 'https://www.wearerabbit.com/careers',
            'location': 'Egypt'
        },

        # ══════════════════════════════════════════
        # SAUDI ARABIA - Vision 2030 & Tech Companies
        # ══════════════════════════════════════════
        {
            'name': 'NEOM',
            'url': 'https://www.neom.com/en-us/careers',
            'location': 'Saudi Arabia - NEOM'
        },
        {
            'name': 'Saudi Aramco Digital',
            'url': 'https://www.aramco.com/en/careers',
            'location': 'Saudi Arabia'
        },
        {
            'name': 'STC (Saudi Telecom)',
            'url': 'https://www.stc.com.sa/content/stc/sa/en/careers.html',
            'location': 'Saudi Arabia'
        },
        {
            'name': 'Manga Productions',
            'url': 'https://mangaproductions.com/careers/',
            'location': 'Saudi Arabia - Riyadh'
        },
        {
            'name': 'Saudi Digital Academy',
            'url': 'https://sda.edu.sa/careers',
            'location': 'Saudi Arabia'
        },
        {
            'name': 'Lucid Motors Saudi',
            'url': 'https://www.lucidmotors.com/careers',
            'location': 'Saudi Arabia - Jeddah'
        },
        {
            'name': 'Noon (Saudi)',
            'url': 'https://careers.noon.com/',
            'location': 'Saudi Arabia'
        },
        {
            'name': 'Jahez (Delivery)',
            'url': 'https://jahez.net/careers',
            'location': 'Saudi Arabia'
        },
        {
            'name': 'Foodics',
            'url': 'https://www.foodics.com/careers/',
            'location': 'Saudi Arabia - Riyadh'
        },
        {
            'name': 'Tamara (BNPL)',
            'url': 'https://tamara.co/careers',
            'location': 'Saudi Arabia - Riyadh'
        },
        {
            'name': 'Salla (E-commerce)',
            'url': 'https://salla.com/careers/',
            'location': 'Saudi Arabia'
        },
        {
            'name': 'Qiddiya (Entertainment)',
            'url': 'https://www.qiddiya.com/careers',
            'location': 'Saudi Arabia - Riyadh'
        },
        {
            'name': 'Red Sea Global',
            'url': 'https://www.redseaglobal.com/en/careers',
            'location': 'Saudi Arabia'
        },
        {
            'name': 'ROSHN (Real Estate)',
            'url': 'https://www.roshn.sa/en/careers',
            'location': 'Saudi Arabia'
        },

        # ══════════════════════════════════════════
        # UAE - Tech, Gaming & Creative Companies
        # ══════════════════════════════════════════
        {
            'name': 'Careem',
            'url': 'https://www.careem.com/careers/',
            'location': 'UAE'
        },
        {
            'name': 'noon',
            'url': 'https://careers.noon.com/',
            'location': 'UAE - Dubai'
        },
        {
            'name': 'Kitopi',
            'url': 'https://www.kitopi.com/careers',
            'location': 'UAE'
        },
        {
            'name': 'Ubisoft Abu Dhabi',
            'url': 'https://www.ubisoft.com/en-us/company/careers/locations/abu-dhabi',
            'location': 'UAE - Abu Dhabi'
        },
        {
            'name': 'Virtuzone',
            'url': 'https://www.vz.ae/careers/',
            'location': 'UAE'
        },
        {
            'name': 'Perkins&Will Dubai',
            'url': 'https://perkinswill.com/careers/',
            'location': 'UAE - Dubai'
        },
        {
            'name': 'Majid Al Futtaim',
            'url': 'https://careers.majidalfuttaim.com/',
            'location': 'UAE - Dubai'
        },
        {
            'name': 'Etisalat (e&)',
            'url': 'https://www.etisalat.ae/en/careers.html',
            'location': 'UAE'
        },
        {
            'name': 'Emirates Group',
            'url': 'https://www.emiratesgroupcareers.com/',
            'location': 'UAE - Dubai'
        },
        {
            'name': 'EXPO City Dubai',
            'url': 'https://www.expocitydubai.com/en/careers',
            'location': 'UAE - Dubai'
        },
        {
            'name': 'Talabat',
            'url': 'https://www.talabat.com/careers',
            'location': 'UAE - Dubai'
        },

        # ══════════════════════════════════════════
        # QATAR / KUWAIT / BAHRAIN
        # ══════════════════════════════════════════
        {
            'name': 'Qatar Foundation',
            'url': 'https://www.qf.org.qa/careers',
            'location': 'Qatar - Doha'
        },
        {
            'name': 'Al Jazeera Media',
            'url': 'https://careers.aljazeera.net/',
            'location': 'Qatar - Doha'
        },
        {
            'name': 'Zain Kuwait',
            'url': 'https://www.kw.zain.com/en/careers',
            'location': 'Kuwait'
        },

        # ══════════════════════════════════════════
        # GLOBAL - Creative / Gaming / Design Studios
        # ══════════════════════════════════════════
        {
            'name': 'Epic Games',
            'url': 'https://www.epicgames.com/site/en-US/careers',
            'location': 'Remote / Global'
        },
        {
            'name': 'Unity Technologies',
            'url': 'https://careers.unity.com/',
            'location': 'Remote / Global'
        },
        {
            'name': 'Canva',
            'url': 'https://www.canva.com/careers/',
            'location': 'Remote / Global'
        },
        {
            'name': 'Figma',
            'url': 'https://www.figma.com/careers/',
            'location': 'Remote / Global'
        },
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
