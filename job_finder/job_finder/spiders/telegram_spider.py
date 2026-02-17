"""
Telegram Channel Job Search Spider - Social Media Search Edition

Searches public Telegram channels for job posts matching Ahmed's CV profile.

Features:
- Scrapes public Telegram channel previews (t.me/s/ - no auth needed)
- Targets MENA, Remote, and Design/Creative job channels
- DuckDuckGo site:t.me search for discovering channels
- CV-based keyword filtering (English + Arabic)
- No Telegram account or API needed (uses public web preview)
"""

import scrapy
import re
import json
from urllib.parse import urlencode, quote_plus
import logging
from job_finder.cv_config import RELEVANT_KEYWORDS, is_relevant_social

logger = logging.getLogger(__name__)


class TelegramJobsSpider(scrapy.Spider):
    """
    Spider that searches Telegram public channels for job posts.

    Uses the t.me/s/ (public web preview) endpoint which doesn't
    require any Telegram account or authentication.
    """

    name = "telegram_jobs"

    # CV-based keywords
    relevant_keywords = RELEVANT_KEYWORDS

    # Known Telegram job channels
    job_channels = [
        # MENA Region Job Channels
        {
            "handle": "jobsinegypt",
            "name": "Jobs in Egypt",
            "region": "Egypt",
            "lang": "ar/en"
        },
        {
            "handle": "egyptremotejobs",
            "name": "Egypt Remote Jobs",
            "region": "Egypt",
            "lang": "en"
        },
        {
            "handle": "cairodesignjobs",
            "name": "Cairo Design Jobs",
            "region": "Egypt",
            "lang": "ar/en"
        },
        {
            "handle": "dubaijobs",
            "name": "Dubai Jobs",
            "region": "UAE",
            "lang": "en"
        },
        {
            "handle": "uaejobs",
            "name": "UAE Jobs",
            "region": "UAE",
            "lang": "en"
        },
        {
            "handle": "dubaifreelancers",
            "name": "Dubai Freelancers",
            "region": "UAE",
            "lang": "en"
        },

        # Design & Creative Channels
        {
            "handle": "designerjobs",
            "name": "Designer Jobs",
            "region": "Remote",
            "lang": "en"
        },
        {
            "handle": "uxjobs",
            "name": "UX Jobs",
            "region": "Remote",
            "lang": "en"
        },
        {
            "handle": "remotejobschannel",
            "name": "Remote Jobs Channel",
            "region": "Remote",
            "lang": "en"
        },
        {
            "handle": "remote_jobs_feed",
            "name": "Remote Jobs Feed",
            "region": "Remote",
            "lang": "en"
        },

        # Tech & AI Channels
        {
            "handle": "aijobsdaily",
            "name": "AI Jobs Daily",
            "region": "Remote",
            "lang": "en"
        },
        {
            "handle": "techjobsremote",
            "name": "Tech Jobs Remote",
            "region": "Remote",
            "lang": "en"
        },

        # Freelance Channels
        {
            "handle": "freelancejobschannel",
            "name": "Freelance Jobs",
            "region": "Remote",
            "lang": "en"
        },
        {
            "handle": "upworkjobs",
            "name": "Upwork Jobs",
            "region": "Remote",
            "lang": "en"
        },

        # Arabic Job Channels
        {
            "handle": "arabfreelancers",
            "name": "Arab Freelancers",
            "region": "MENA",
            "lang": "ar"
        },
        {
            "handle": "wazzafni",
            "name": "Wazzafni - وظفني",
            "region": "Egypt",
            "lang": "ar"
        },
    ]

    # DuckDuckGo queries to discover more channels
    discovery_queries = [
        'site:t.me "hiring" "designer"',
        'site:t.me "hiring" "3D artist"',
        'site:t.me "remote" "designer" "job"',
        'site:t.me "وظائف" "مصمم"',
        'site:t.me "مطلوب" "designer"',
        'site:t.me "hiring" "UI UX"',
        'site:t.me "job" "blender" OR "unreal"',
        'site:t.me "hiring" "CGI" OR "VFX"',
        'site:t.me "remote" "creative" "job"',
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 15,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_messages = set()
        self.discovered_channels = set()

    def start_requests(self):
        """Generate requests for known channels and discovery search"""

        # 1. Scrape known job channels via public preview
        for channel in self.job_channels:
            # t.me/s/ is the public web preview (no login needed)
            url = f"https://t.me/s/{channel['handle']}"
            yield scrapy.Request(
                url,
                callback=self.parse_channel,
                meta={
                    'channel_handle': channel['handle'],
                    'channel_name': channel['name'],
                    'region': channel['region'],
                },
                errback=self.handle_error,
                dont_filter=True,
            )

        # 2. Discover new channels via DuckDuckGo
        for query in self.discovery_queries:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            yield scrapy.Request(
                url,
                callback=self.parse_discovery_results,
                meta={'query': query},
                errback=self.handle_error,
                dont_filter=True,
            )

    def handle_error(self, failure):
        """Handle request failures gracefully"""
        logger.warning(f"Telegram request failed: {failure.request.url} - {failure.value}")

    def parse_channel(self, response):
        """Parse a public Telegram channel preview page"""
        channel_handle = response.meta.get('channel_handle', 'unknown')
        channel_name = response.meta.get('channel_name', channel_handle)
        region = response.meta.get('region', 'Unknown')

        logger.info(f"Parsing Telegram channel: {channel_name} (@{channel_handle})")

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )

        hiring_pattern = re.compile(
            r'\b(hiring|مطلوب|looking\s*for|seeking|need|wanted|job|position|'
            r'opportunity|فرصة|وظيفة|opening|role|freelance|'
            r'we\'?re?\s*hiring|join\s*(?:us|our)\s*team|apply|'
            r'vacancy|remote\s*(?:position|role|job))\b',
            re.IGNORECASE
        )

        # Telegram public preview uses .tgme_widget_message for each message
        messages = response.css('.tgme_widget_message_wrap, .tgme_widget_message')

        if not messages:
            # Try alternative selectors
            messages = response.css('[class*="message"]')

        logger.info(f"Found {len(messages)} messages in @{channel_handle}")

        for msg in messages:
            # Get message text
            text_parts = msg.css('.tgme_widget_message_text::text, .tgme_widget_message_text *::text').getall()
            text = ' '.join(text_parts).strip()

            if not text or len(text) < 20:
                continue

            # Must match CV keywords
            if not pattern.search(text):
                continue

            # Must look like a job post
            if not hiring_pattern.search(text):
                continue

            # Get message link
            msg_link = msg.css('.tgme_widget_message_date::attr(href)').get()
            if not msg_link:
                msg_link = msg.css('a[href*="t.me"]::attr(href)').get()
            if not msg_link:
                msg_link = f"https://t.me/s/{channel_handle}"

            # Get message date
            date = msg.css('.tgme_widget_message_date time::attr(datetime)').get('')

            # Get views count
            views = msg.css('.tgme_widget_message_views::text').get('0')

            # Dedup
            if msg_link in self.seen_messages:
                continue
            self.seen_messages.add(msg_link)

            # Extract external links from message
            links = msg.css('.tgme_widget_message_text a::attr(href)').getall()
            external_links = [l for l in links if 't.me' not in l and l.startswith('http')]
            apply_link = self._find_apply_link(external_links)

            yield self._build_item(
                text=text,
                link=apply_link or msg_link,
                telegram_link=msg_link,
                channel_handle=channel_handle,
                channel_name=channel_name,
                region=region,
                date=date,
                views=views,
            )

        # Check for "Load more" / pagination
        load_more = response.css('a.tme_messages_more::attr(href)').get()
        if load_more:
            if load_more.startswith('/'):
                load_more = f"https://t.me{load_more}"
            yield scrapy.Request(
                load_more,
                callback=self.parse_channel,
                meta=response.meta,
                errback=self.handle_error,
            )

    def parse_discovery_results(self, response):
        """Parse DuckDuckGo results to discover Telegram channels"""
        query = response.meta.get('query', 'unknown')

        results = response.css('a.result__a')
        logger.info(f"Discovery search found {len(results)} results for: {query}")

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )

        for result in results[:15]:
            href = result.css('::attr(href)').get('')
            title = ' '.join(result.css('::text').getall()).strip()

            if not href or 't.me' not in href:
                continue

            # Extract channel handle from URL
            channel_handle = self._extract_channel_handle(href)
            if not channel_handle or channel_handle in self.discovered_channels:
                continue

            self.discovered_channels.add(channel_handle)

            # Check if it's a specific message or a channel
            if re.search(r'/\d+$', href):
                # It's a specific message - still check if relevant
                if pattern.search(title):
                    yield self._build_item(
                        text=title,
                        link=href,
                        telegram_link=href,
                        channel_handle=channel_handle,
                        channel_name=self._clean_channel_name(title),
                        region='Unknown',
                        date='',
                        views='0',
                    )

                    # Also scrape the full channel
                    channel_url = f"https://t.me/s/{channel_handle}"
                    yield scrapy.Request(
                        channel_url,
                        callback=self.parse_channel,
                        meta={
                            'channel_handle': channel_handle,
                            'channel_name': self._clean_channel_name(title),
                            'region': 'Discovered',
                        },
                        errback=self.handle_error,
                    )
            else:
                # It's a channel link - scrape it
                channel_url = f"https://t.me/s/{channel_handle}"
                yield scrapy.Request(
                    channel_url,
                    callback=self.parse_channel,
                    meta={
                        'channel_handle': channel_handle,
                        'channel_name': self._clean_channel_name(title),
                        'region': 'Discovered',
                    },
                    errback=self.handle_error,
                )

    def _build_item(self, text, link, telegram_link, channel_handle,
                    channel_name, region, date='', views='0'):
        """Build a standardized job item from Telegram message"""

        title = self._extract_title(text)
        location = self._extract_location(text, region)
        job_type = self._extract_job_type(text)
        company = self._extract_company(text)

        return {
            'keyword_searched': f'Telegram @{channel_handle}',
            'title': title,
            'company': company,
            'location': location,
            'type': job_type,
            'link': link,
            'telegram_link': telegram_link,
            'source': f'Telegram - @{channel_handle}',
            'channel': f'@{channel_handle}',
            'channel_name': channel_name,
            'date': date,
            'views': views,
            'description': text[:500],
        }

    def _extract_title(self, text):
        """Extract job title from message text"""
        patterns = [
            r'(?:hiring|looking\s*for)\s*(?:a\s+)?([^.!?\n]{10,80})',
            r'(?:position|role|job):\s*([^.!?\n]{10,80})',
            r'مطلوب\s+([^\n.!؟]{5,60})',
            r'وظيفة\s*:?\s*([^\n.!؟]{5,60})',
            r'فرصة\s*:?\s*([^\n.!؟]{5,60})',
        ]

        for pat in patterns:
            match = re.search(pat, text, re.I)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'https?://\S+', '', title).strip()
                if len(title) > 5:
                    return title[:100]

        # First meaningful line
        for line in text.split('\n'):
            line = line.strip()
            if len(line) > 10 and len(line) < 150:
                return re.sub(r'https?://\S+', '', line).strip()[:100]

        return text[:100]

    def _extract_location(self, text, default_region='Unknown'):
        """Extract location from message text"""
        if re.search(r'\b(remote|عن\s*بعد|من\s*المنزل|anywhere|worldwide)\b', text, re.I):
            if re.search(r'\b(UAE|Dubai|دبي|الامارات)\b', text, re.I):
                return 'Remote - UAE'
            if re.search(r'\b(Europe|EU|UK|Germany)\b', text, re.I):
                return 'Remote - Europe'
            if re.search(r'\b(Egypt|مصر|القاهرة)\b', text, re.I):
                return 'Remote - Egypt'
            return 'Remote'

        location_map = [
            (r'\b(Dubai|UAE|دبي|الامارات|Abu\s*Dhabi)\b', 'UAE'),
            (r'\b(Cairo|القاهرة|Egypt|مصر|Alexandria|اسكندرية)\b', 'Egypt'),
            (r'\b(Riyadh|Saudi|السعودية)\b', 'Saudi Arabia'),
            (r'\b(London|UK)\b', 'UK'),
            (r'\b(Berlin|Germany)\b', 'Germany'),
        ]

        for pat, loc in location_map:
            if re.search(pat, text, re.I):
                return loc

        return default_region if default_region != 'Unknown' else 'Not specified'

    def _extract_job_type(self, text):
        """Extract job type from message text"""
        if re.search(r'\b(freelance|فريلانس|contract|project[-\s]based)\b', text, re.I):
            return 'Freelance'
        if re.search(r'\b(part[-\s]?time|دوام\s*جزئي)\b', text, re.I):
            return 'Part Time'
        if re.search(r'\b(remote|عن\s*بعد)\b', text, re.I):
            return 'Remote'
        if re.search(r'\b(full[-\s]?time|دوام\s*كامل)\b', text, re.I):
            return 'Full Time'
        return 'Not specified'

    def _extract_company(self, text):
        """Try to extract company name from message"""
        patterns = [
            r'(?:at|@|in|company:?)\s+([A-Z][A-Za-z0-9\s&.]{2,40}?)(?:\s+is|\s+-|\s+\(|,|\n)',
            r'(?:شركة|في)\s+([^\n,]{3,40}?)(?:\s+تطلب|\s+محتاجة|\s+-)',
        ]

        for pat in patterns:
            match = re.search(pat, text, re.I)
            if match:
                name = match.group(1).strip()
                if 3 < len(name) < 50:
                    return name

        return 'Via Telegram'

    def _extract_channel_handle(self, url):
        """Extract channel handle from t.me URL"""
        # Match: t.me/channelname or t.me/s/channelname or t.me/channelname/123
        match = re.search(r't\.me/(?:s/)?([a-zA-Z][\w]{2,30})', url)
        if match:
            handle = match.group(1)
            # Skip common non-channel paths
            skip_words = ['share', 'addstickers', 'joinchat', 'proxy', 'socks']
            if handle.lower() not in skip_words:
                return handle
        return None

    def _clean_channel_name(self, title):
        """Clean channel name from search result title"""
        if title:
            name = re.sub(r'\s*[-–|]\s*Telegram.*$', '', title, flags=re.I)
            return name.strip()[:60] if name.strip() else 'Telegram Channel'
        return 'Telegram Channel'

    def _find_apply_link(self, urls):
        """Find best application link from message URLs"""
        job_domains = ['greenhouse', 'lever', 'workday', 'ashbyhq', 'bamboohr',
                       'jobs', 'careers', 'apply', 'hire', 'linkedin.com/jobs',
                       'wuzzuf', 'indeed', 'bayt']

        for url in urls:
            if any(domain in url.lower() for domain in job_domains):
                return url

        return urls[0] if urls else None
