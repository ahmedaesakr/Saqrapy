"""
Facebook Groups Job Search Spider - Social Media Search Edition

Searches Facebook public groups and pages for job posts matching
Ahmed's CV profile using DuckDuckGo site search (no Facebook API needed).

Features:
- DuckDuckGo site:facebook.com search for job posts
- Targets public Facebook job groups (MENA region, Design, Creative)
- Google cache/preview extraction for public posts
- CV-based keyword filtering
- Bilingual search (English + Arabic)
"""

import scrapy
import re
import json
from urllib.parse import urlencode, quote_plus
import logging
from job_finder.cv_config import RELEVANT_KEYWORDS

logger = logging.getLogger(__name__)


class FacebookSearchSpider(scrapy.Spider):
    """
    Spider that searches for job posts in Facebook groups/pages.

    Since Facebook Graph API search is deprecated and requires app review,
    this spider uses DuckDuckGo to find public Facebook job posts and
    directly scrapes public Facebook group pages via mbasic.facebook.com.
    """

    name = "facebook_jobs"

    # CV-based keywords
    relevant_keywords = RELEVANT_KEYWORDS

    # DuckDuckGo search queries targeting Facebook
    search_queries_en = [
        # Design jobs on Facebook
        'site:facebook.com/groups "hiring" "3D artist"',
        'site:facebook.com/groups "hiring" "product designer"',
        'site:facebook.com/groups "hiring" "UI UX designer"',
        'site:facebook.com/groups "hiring" "motion designer"',
        'site:facebook.com/groups "hiring" "graphic designer" "remote"',
        'site:facebook.com/groups "hiring" "blender" OR "unreal"',
        'site:facebook.com/groups "hiring" designer Egypt',
        'site:facebook.com/groups "hiring" designer Dubai UAE',
        'site:facebook.com/groups "hiring" "CGI artist"',
        'site:facebook.com/groups "hiring" "generative AI"',

        # Facebook pages with jobs
        'site:facebook.com "we\'re hiring" designer',
        'site:facebook.com "join our team" "3D artist" OR "designer"',
    ]

    # Arabic search queries for MENA job groups
    search_queries_ar = [
        'site:facebook.com/groups "مطلوب" "مصمم" OR "ديزاينر"',
        'site:facebook.com/groups "مطلوب" "3D" OR "ثري دي"',
        'site:facebook.com/groups "وظيفة" "مصمم جرافيك"',
        'site:facebook.com/groups "فرصة عمل" "designer"',
        'site:facebook.com/groups "مطلوب" "موشن جرافيك"',
    ]

    # Known public Facebook job groups (MENA + Design)
    known_groups = [
        # Egypt Job Groups
        {
            "name": "Jobs in Egypt - Creative",
            "group_id": "egyptcreativejobs",
            "region": "Egypt"
        },
        {
            "name": "Graphic Design Jobs Egypt",
            "group_id": "graphicdesignjobsegypt",
            "region": "Egypt"
        },
        {
            "name": "Freelancers Egypt",
            "group_id": "freelancersegypt",
            "region": "Egypt"
        },

        # UAE Job Groups
        {
            "name": "Dubai Jobs",
            "group_id": "dubaijobs",
            "region": "UAE"
        },
        {
            "name": "UAE Creative Jobs",
            "group_id": "uaecreativejobs",
            "region": "UAE"
        },

        # Design Job Groups (International)
        {
            "name": "Remote Design Jobs",
            "group_id": "remotedesignjobs",
            "region": "Remote"
        },
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 4,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 15,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_links = set()

    def start_requests(self):
        """Generate DuckDuckGo search requests for Facebook job posts"""

        # 1. English search queries
        for query in self.search_queries_en:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            yield scrapy.Request(
                url,
                callback=self.parse_search_results,
                meta={'query': query, 'language': 'en'},
                errback=self.handle_error,
                dont_filter=True,
            )

        # 2. Arabic search queries
        for query in self.search_queries_ar:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            yield scrapy.Request(
                url,
                callback=self.parse_search_results,
                meta={'query': query, 'language': 'ar'},
                errback=self.handle_error,
                dont_filter=True,
            )

        # 3. Direct group scraping via mbasic (lightweight, no JS)
        for group in self.known_groups:
            url = f"https://mbasic.facebook.com/groups/{group['group_id']}"
            yield scrapy.Request(
                url,
                callback=self.parse_facebook_group,
                meta={
                    'group_name': group['name'],
                    'region': group['region'],
                },
                errback=self.handle_error,
                dont_filter=True,
            )

    def handle_error(self, failure):
        """Handle request failures gracefully"""
        logger.warning(f"Facebook search request failed: {failure.request.url} - {failure.value}")

    def parse_search_results(self, response):
        """Parse DuckDuckGo search results for Facebook links"""
        query = response.meta.get('query', 'unknown')

        results = response.css('a.result__a')
        logger.info(f"DuckDuckGo found {len(results)} Facebook results for: {query}")

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )

        for result in results[:20]:
            href = result.css('::attr(href)').get('')
            title = ' '.join(result.css('::text').getall()).strip()

            if not href or 'facebook.com' not in href:
                continue

            # Get the snippet/description
            snippet_el = result.xpath('./ancestor::div[contains(@class,"result")]//a[contains(@class,"result__snippet")]')
            snippet = ' '.join(snippet_el.css('::text').getall()).strip() if snippet_el else ''

            combined_text = f"{title} {snippet}"

            if not pattern.search(combined_text):
                continue

            # Dedup
            if href in self.seen_links:
                continue
            self.seen_links.add(href)

            # Determine if this is a group post, page post, or job listing
            post_type = self._classify_facebook_link(href)

            yield self._build_item(
                text=combined_text,
                link=href,
                post_type=post_type,
                query=query,
            )

            # If it's a group link, try to scrape the group for more posts
            if '/groups/' in href and '/posts/' not in href:
                group_url = href.split('?')[0]
                mbasic_url = group_url.replace('www.facebook.com', 'mbasic.facebook.com')
                mbasic_url = mbasic_url.replace('facebook.com', 'mbasic.facebook.com')

                yield scrapy.Request(
                    mbasic_url,
                    callback=self.parse_facebook_group,
                    meta={
                        'group_name': self._extract_group_name(title, href),
                        'region': 'Unknown',
                    },
                    errback=self.handle_error,
                )

    def parse_facebook_group(self, response):
        """Parse a public Facebook group page (via mbasic)"""
        group_name = response.meta.get('group_name', 'Unknown Group')
        region = response.meta.get('region', 'Unknown')

        logger.info(f"Parsing Facebook group: {group_name}")

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )

        hiring_pattern = re.compile(
            r'\b(hiring|مطلوب|looking\s*for|seeking|need|wanted|job|position|'
            r'opportunity|فرصة|وظيفة|we\'?re?\s*hiring|join\s*(?:us|our)\s*team)\b',
            re.IGNORECASE
        )

        # mbasic.facebook.com uses simple HTML - posts are in article or div elements
        # Try multiple selectors for post content
        posts = response.css('article, div[data-ft], div.story_body_container')

        if not posts:
            # Fallback - look for any text blocks that look like posts
            posts = response.css('div#structured_composer_async_container ~ div')

        for post in posts:
            text = ' '.join(post.css('*::text').getall()).strip()

            if not text or len(text) < 20:
                continue

            if not pattern.search(text):
                continue

            if not hiring_pattern.search(text):
                continue

            # Get post link
            post_links = post.css('a[href*="/story.php"], a[href*="/permalink/"]')
            post_link = post_links.css('::attr(href)').get('')

            if post_link:
                if post_link.startswith('/'):
                    post_link = f"https://www.facebook.com{post_link}"
            else:
                # Generate group link as fallback
                post_link = response.url.replace('mbasic.', 'www.')

            if post_link in self.seen_links:
                continue
            self.seen_links.add(post_link)

            yield self._build_item(
                text=text[:1000],
                link=post_link,
                post_type='group_post',
                query=f'Group: {group_name}',
                group_name=group_name,
                region=region,
            )

    def _build_item(self, text, link, post_type, query,
                    group_name=None, region=None):
        """Build a standardized job item from Facebook post data"""

        title = self._extract_title(text)
        location = self._extract_location(text) if not region else region
        job_type = self._extract_job_type(text)
        company = self._extract_company(text)

        return {
            'keyword_searched': query,
            'title': title,
            'company': company,
            'location': location,
            'type': job_type,
            'link': link,
            'source': f'Facebook - {group_name}' if group_name else 'Facebook',
            'post_type': post_type,
            'description': text[:500],
        }

    def _extract_title(self, text):
        """Extract job title from post text"""
        patterns = [
            # English patterns
            r'(?:hiring|looking\s*for)\s*(?:a\s+)?([^.!?\n]{10,80})',
            r'(?:position|role|job):\s*([^.!?\n]{10,80})',
            r'(?:we\s*need)\s*(?:a\s+)?([^.!?\n]{10,80})',
            # Arabic patterns
            r'مطلوب\s+([^\n.!؟]{5,60})',
            r'وظيفة\s+([^\n.!؟]{5,60})',
        ]

        for pat in patterns:
            match = re.search(pat, text, re.I)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'https?://\S+', '', title).strip()
                if len(title) > 5:
                    return title[:100]

        # Fallback: first meaningful line
        for line in text.split('\n'):
            line = line.strip()
            if len(line) > 10 and len(line) < 150:
                return re.sub(r'https?://\S+', '', line).strip()[:100]

        return text[:100]

    def _extract_location(self, text):
        """Extract location from post text"""
        if re.search(r'\b(remote|عن\s*بعد|من\s*المنزل|anywhere)\b', text, re.I):
            if re.search(r'\b(UAE|Dubai|دبي|الامارات)\b', text, re.I):
                return 'Remote - UAE'
            if re.search(r'\b(Europe|EU|UK|Germany)\b', text, re.I):
                return 'Remote - Europe'
            if re.search(r'\b(Egypt|مصر|القاهرة|اسكندرية)\b', text, re.I):
                return 'Remote - Egypt'
            return 'Remote'

        location_map = [
            (r'\b(Dubai|UAE|دبي|الامارات|Abu\s*Dhabi)\b', 'UAE'),
            (r'\b(Cairo|القاهرة|Egypt|مصر|Alexandria|اسكندرية)\b', 'Egypt'),
            (r'\b(Riyadh|Saudi|السعودية|الرياض)\b', 'Saudi Arabia'),
            (r'\b(London|UK)\b', 'UK'),
            (r'\b(Berlin|Germany)\b', 'Germany'),
        ]

        for pat, loc in location_map:
            if re.search(pat, text, re.I):
                return loc

        return 'Not specified'

    def _extract_job_type(self, text):
        """Extract job type from post text"""
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
        """Try to extract company name from post"""
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

        return 'Via Facebook'

    def _classify_facebook_link(self, url):
        """Classify what type of Facebook content the URL points to"""
        if '/groups/' in url and '/posts/' in url:
            return 'group_post'
        if '/groups/' in url:
            return 'group'
        if '/jobs/' in url:
            return 'job_listing'
        if '/posts/' in url:
            return 'page_post'
        return 'page'

    def _extract_group_name(self, title, url):
        """Extract group name from search result title or URL"""
        if title:
            name = re.sub(r'\s*[-|]\s*Facebook.*$', '', title)
            if name:
                return name.strip()[:60]

        # From URL
        match = re.search(r'/groups/([^/?]+)', url)
        if match:
            return match.group(1).replace('.', ' ').replace('-', ' ').title()

        return 'Facebook Group'
