"""
LinkedIn Spider - Scrapes jobs from LinkedIn's Guest Job Search API

LinkedIn blocks normal page scraping with an authwall, but their guest
jobs API endpoint returns paginated HTML without requiring login.

Endpoint: linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
Returns: HTML fragments with job cards (25 per page)

Features:
- No login required (guest API)
- Pagination support (up to 5 pages per query)
- CV-based keyword filtering via cv_config
- Targets: Egypt, Saudi Arabia, UAE, Qatar, Remote, Europe
- Relevance scoring via pipeline
"""

import scrapy
from urllib.parse import urlencode
import re
import logging
from job_finder.cv_config import SEARCH_KEYWORDS, RELEVANT_KEYWORDS, is_relevant

logger = logging.getLogger(__name__)


class LinkedInSpider(scrapy.Spider):
    name = "linkedin_jobs"

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS

    # Use centralized search keywords from cv_config
    search_keywords = SEARCH_KEYWORDS

    # Location IDs for LinkedIn (LinkedIn's internal geo IDs)
    locations = {
        "Egypt": "106155005",
        "Saudi Arabia": "100459316",
        "UAE": "104305776",
        "Qatar": "104111990",
        "Remote": "",  # empty = worldwide with remote filter
    }

    # Remote filter: f_WT=2 means Remote
    # Time filter: f_TPR=r604800 means last 7 days
    # Sort: sortBy=DD means most recent

    custom_settings = {
        'DOWNLOAD_DELAY': 4,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'COOKIES_ENABLED': False,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [429, 500, 502, 503],
    }

    def start_requests(self):
        """Generate guest API requests for each keyword + location combo"""
        for keyword in self.search_keywords:
            for location_name, geo_id in self.locations.items():
                params = {
                    'keywords': keyword,
                    'location': location_name if geo_id else '',
                    'f_TPR': 'r604800',  # Last week
                    'sortBy': 'DD',       # Most recent
                    'start': '0',
                }

                if geo_id:
                    params['geoId'] = geo_id

                # For "Remote" location, add remote work type filter
                if location_name == 'Remote':
                    params['f_WT'] = '2'

                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{urlencode(params)}"

                yield scrapy.Request(
                    url,
                    callback=self.parse_guest_api,
                    meta={
                        'keyword': keyword,
                        'location': location_name,
                        'page': 0,
                    },
                    headers={
                        'Accept': 'text/html',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    },
                    errback=self.handle_error,
                    dont_filter=True,
                )

    def handle_error(self, failure):
        url = failure.request.url
        keyword = failure.request.meta.get('keyword', '?')
        location = failure.request.meta.get('location', '?')
        if '429' in str(failure.value):
            logger.warning(f"LinkedIn rate limited: {keyword} in {location}")
        else:
            logger.warning(f"LinkedIn request failed ({keyword}/{location}): {failure.value}")

    def parse_guest_api(self, response):
        """Parse LinkedIn guest jobs API response (HTML fragment)"""
        keyword = response.meta.get('keyword', 'unknown')
        location = response.meta.get('location', 'unknown')
        page = response.meta.get('page', 0)

        # Check for rate limiting or auth wall
        if response.status == 429:
            logger.warning(f"LinkedIn rate limited for: {keyword} in {location}")
            return

        if 'authwall' in response.url or response.status == 403:
            logger.warning(f"LinkedIn authwall hit for: {keyword} in {location}")
            return

        # The guest API returns HTML with <li> job cards
        job_cards = response.css('li')

        if not job_cards:
            # Try alternative: the response might be a div with base-cards
            job_cards = response.css('div.base-card, div.base-search-card')

        if not job_cards:
            logger.debug(f"No jobs found for: {keyword} in {location} (page {page})")
            return

        logger.info(f"LinkedIn: {len(job_cards)} cards for '{keyword}' in {location} (page {page})")

        count = 0
        for card in job_cards:
            # Extract job details from base-card structure
            title = (
                card.css('h3.base-search-card__title::text').get() or
                card.css('.base-card__title::text').get() or
                card.css('h3::text').get() or
                card.css('a.base-card__full-link span::text').get()
            )

            link = (
                card.css('a.base-card__full-link::attr(href)').get() or
                card.css('a::attr(href)').get()
            )

            company = (
                card.css('h4.base-search-card__subtitle a::text').get() or
                card.css('.base-search-card__subtitle::text').get() or
                card.css('h4 a::text').get() or
                card.css('h4::text').get()
            )

            job_location = (
                card.css('span.job-search-card__location::text').get() or
                card.css('.base-search-card__metadata span::text').get()
            )

            date_posted = card.css('time::attr(datetime)').get()

            # Clean text
            if title:
                title = title.strip()
            if company:
                company = company.strip()
            if job_location:
                job_location = job_location.strip()

            # Skip empty
            if not title or not link:
                continue

            # Filter using centralized cv_config
            if not is_relevant(title=title):
                continue

            # Clean link (remove tracking params)
            if '?' in link:
                link = link.split('?')[0]

            count += 1
            yield {
                'keyword_searched': keyword,
                'title': title,
                'company': company or 'Unknown',
                'location': job_location or location,
                'type': 'Remote' if location == 'Remote' else 'Full Time',
                'link': link,
                'source': 'LinkedIn',
                'date_posted': date_posted or '',
            }

        if count:
            logger.info(f"LinkedIn: {count} relevant jobs for '{keyword}' in {location}")

        # Pagination - LinkedIn guest API uses start=0, 25, 50...
        # Limit to 5 pages (125 results per keyword/location)
        if len(job_cards) >= 20 and page < 4:
            next_start = (page + 1) * 25
            next_url = re.sub(r'start=\d+', f'start={next_start}', response.url)
            if f'start={next_start}' not in next_url:
                next_url = f"{response.url}&start={next_start}"

            yield scrapy.Request(
                next_url,
                callback=self.parse_guest_api,
                meta={
                    'keyword': keyword,
                    'location': location,
                    'page': page + 1,
                },
                headers={
                    'Accept': 'text/html',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                errback=self.handle_error,
                dont_filter=True,
            )
