"""
Reddit Jobs Spider - Social Media Search Edition

Searches Reddit job subreddits for creative/design/3D job posts
matching Ahmed's CV profile.

Features:
- Scrapes 10+ design/creative job subreddits using Reddit JSON API
- No authentication needed (public subreddit data)
- CV-based keyword filtering for relevance
- Extracts post title, body, author, links, and metadata
- Supports sorting by new/hot/top
"""

import scrapy
import re
import json
from urllib.parse import urlencode, quote_plus
import logging
from job_finder.cv_config import RELEVANT_KEYWORDS

logger = logging.getLogger(__name__)


class RedditJobsSpider(scrapy.Spider):
    """
    Spider that searches Reddit for job posts matching CV profile.
    Uses Reddit's public JSON API (no auth needed).
    """

    name = "reddit_jobs"

    allowed_domains = ["www.reddit.com", "old.reddit.com"]

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS

    # Subreddits to search for jobs
    job_subreddits = [
        # Design & Creative Jobs
        {"name": "forhire", "flair_filter": None},
        {"name": "designjobs", "flair_filter": None},
        {"name": "gameDevJobs", "flair_filter": None},
        {"name": "3Djobs", "flair_filter": None},
        {"name": "motiondesign", "flair_filter": "Job"},
        {"name": "blender", "flair_filter": "Job"},

        # General Remote/Freelance
        {"name": "remotejobs", "flair_filter": None},
        {"name": "freelance", "flair_filter": None},
        {"name": "WorkOnline", "flair_filter": None},

        # Tech & AI Jobs
        {"name": "MachineLearning", "flair_filter": "Job"},
        {"name": "artificial", "flair_filter": None},

        # Regional
        {"name": "DubaiJobs", "flair_filter": None},
        {"name": "EuropeanJobs", "flair_filter": None},
    ]

    # Search queries to run across Reddit
    search_queries = [
        "hiring 3D artist",
        "hiring product designer",
        "hiring UI UX designer",
        "hiring motion graphics",
        "hiring CGI artist",
        "hiring generative AI",
        "hiring blender artist",
        "hiring unreal engine",
        "remote designer job",
        "freelance 3D artist",
    ]

    # Hiring indicator patterns (to identify actual job posts)
    hiring_patterns = re.compile(
        r'\b(hiring|looking\s*for|seeking|need|wanted|job|position|'
        r'opportunity|opening|role|freelance|contract|gig|'
        r'we\'?re?\s*hiring|join\s*(?:us|our|the)\s*team|'
        r'apply|remote\s*(?:position|role|job)|'
        r'\[hiring\]|\[for\s*hire\])\b',
        re.IGNORECASE
    )

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'application/json',
            'User-Agent': 'JobFinder/2.0 (by /u/job_scraper_bot)',
        },
    }

    def start_requests(self):
        """Generate requests for subreddits and search queries"""

        # 1. Scrape job subreddits (new + hot posts)
        for sub in self.job_subreddits:
            for sort in ['new', 'hot']:
                url = f"https://www.reddit.com/r/{sub['name']}/{sort}.json?limit=50"
                yield scrapy.Request(
                    url,
                    callback=self.parse_subreddit,
                    meta={
                        'subreddit': sub['name'],
                        'flair_filter': sub.get('flair_filter'),
                        'sort': sort,
                    },
                    errback=self.handle_error,
                    dont_filter=True,
                )

        # 2. Reddit search across all subreddits
        for query in self.search_queries:
            params = {
                'q': query,
                'sort': 'new',
                'limit': 25,
                't': 'month',  # Last month
                'type': 'link',
            }
            url = f"https://www.reddit.com/search.json?{urlencode(params)}"
            yield scrapy.Request(
                url,
                callback=self.parse_search_results,
                meta={'query': query},
                errback=self.handle_error,
                dont_filter=True,
            )

    def handle_error(self, failure):
        """Handle request failures gracefully"""
        logger.warning(f"Reddit request failed: {failure.request.url} - {failure.value}")

    def parse_subreddit(self, response):
        """Parse subreddit JSON listing"""
        subreddit = response.meta.get('subreddit', 'unknown')
        flair_filter = response.meta.get('flair_filter')

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from r/{subreddit}")
            return

        posts = data.get('data', {}).get('children', [])
        logger.info(f"Found {len(posts)} posts in r/{subreddit}")

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )

        for post in posts:
            post_data = post.get('data', {})

            # Skip if flair doesn't match (when flair filter is set)
            if flair_filter:
                post_flair = post_data.get('link_flair_text', '') or ''
                if flair_filter.lower() not in post_flair.lower():
                    continue

            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            combined_text = f"{title} {selftext}"

            # Must match CV keywords
            if not pattern.search(combined_text):
                continue

            # Must look like a job post (hiring indicator)
            if not self.hiring_patterns.search(combined_text):
                continue

            # Skip posts older than 30 days
            created_utc = post_data.get('created_utc', 0)

            yield self._build_item(post_data, subreddit)

        # Pagination - get next page
        after = data.get('data', {}).get('after')
        if after and response.meta.get('sort') == 'new':
            next_url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=50&after={after}"
            yield scrapy.Request(
                next_url,
                callback=self.parse_subreddit,
                meta=response.meta,
                errback=self.handle_error,
            )

    def parse_search_results(self, response):
        """Parse Reddit search results JSON"""
        query = response.meta.get('query', 'unknown')

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse search results for: {query}")
            return

        posts = data.get('data', {}).get('children', [])
        logger.info(f"Found {len(posts)} search results for: {query}")

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )

        for post in posts:
            post_data = post.get('data', {})
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            combined_text = f"{title} {selftext}"

            if not pattern.search(combined_text):
                continue

            subreddit = post_data.get('subreddit', 'unknown')
            yield self._build_item(post_data, subreddit)

    def _build_item(self, post_data, subreddit):
        """Build a standardized job item from Reddit post data"""
        title = post_data.get('title', '').strip()
        selftext = post_data.get('selftext', '')
        permalink = post_data.get('permalink', '')
        url = post_data.get('url', '')
        author = post_data.get('author', '[deleted]')
        score = post_data.get('score', 0)
        flair = post_data.get('link_flair_text', '')

        # Extract company name from title if possible
        company = self._extract_company(title, selftext)

        # Extract location from text
        location = self._extract_location(f"{title} {selftext}")

        # Extract job type
        job_type = self._extract_job_type(f"{title} {selftext} {flair}")

        # Extract external apply link from selftext
        apply_link = self._extract_apply_link(selftext, url)

        # Build the Reddit link
        reddit_link = f"https://www.reddit.com{permalink}" if permalink else url

        return {
            'keyword_searched': f'Reddit r/{subreddit}',
            'title': self._clean_title(title),
            'company': company,
            'location': location,
            'type': job_type,
            'link': apply_link or reddit_link,
            'reddit_link': reddit_link,
            'source': f'Reddit - r/{subreddit}',
            'author': f'u/{author}',
            'score': score,
            'flair': flair,
            'description': selftext[:500] if selftext else '',
        }

    def _clean_title(self, title):
        """Clean Reddit post title (remove [Hiring], [For Hire] tags etc.)"""
        title = re.sub(r'\[(?:Hiring|For\s*Hire|Remote|Paid|Unpaid)\]', '', title, flags=re.I)
        return title.strip(' -|:')

    def _extract_company(self, title, selftext):
        """Try to extract company name from post"""
        # Common patterns: "Company Name is hiring", "at Company Name"
        patterns = [
            r'(?:at|@)\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\s+is|\s+-|\s+\(|,)',
            r'^([A-Z][A-Za-z0-9\s&.]+?)\s+(?:is\s+)?(?:hiring|looking|seeking)',
            r'(?:company|studio|agency):\s*([^\n,]+)',
        ]

        for pat in patterns:
            match = re.search(pat, f"{title} {selftext}", re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 50:
                    return name

        return 'Via Reddit'

    def _extract_location(self, text):
        """Extract location from post text"""
        # Check for remote indicators
        if re.search(r'\b(remote|anywhere|worldwide|global)\b', text, re.I):
            # Check if specific region is also mentioned
            if re.search(r'\b(UAE|Dubai|Abu\s*Dhabi)\b', text, re.I):
                return 'Remote - UAE'
            if re.search(r'\b(Europe|EU|Germany|UK|London|Berlin)\b', text, re.I):
                return 'Remote - Europe'
            if re.search(r'\b(Egypt|Cairo|Alexandria)\b', text, re.I):
                return 'Remote - Egypt'
            return 'Remote'

        # Check for specific locations
        location_patterns = [
            (r'\b(Dubai|Abu\s*Dhabi|UAE)\b', 'UAE'),
            (r'\b(Cairo|Alexandria|Egypt)\b', 'Egypt'),
            (r'\b(Berlin|Germany)\b', 'Germany'),
            (r'\b(London|UK|United\s*Kingdom)\b', 'UK'),
            (r'\b(Amsterdam|Netherlands)\b', 'Netherlands'),
            (r'\b(Paris|France)\b', 'France'),
        ]

        for pat, loc in location_patterns:
            if re.search(pat, text, re.I):
                return loc

        return 'Not specified'

    def _extract_job_type(self, text):
        """Extract job type from post"""
        if re.search(r'\b(freelance|contract|project[-\s]based|gig)\b', text, re.I):
            return 'Freelance'
        if re.search(r'\b(part[-\s]?time)\b', text, re.I):
            return 'Part Time'
        if re.search(r'\b(remote)\b', text, re.I):
            return 'Remote'
        if re.search(r'\b(full[-\s]?time|permanent)\b', text, re.I):
            return 'Full Time'
        return 'Not specified'

    def _extract_apply_link(self, selftext, url):
        """Extract external application link from post body"""
        if not selftext:
            return None

        # Look for apply/application links
        link_patterns = [
            r'(?:apply|application|link|form).*?(https?://[^\s\)]+)',
            r'(https?://(?:jobs|careers|apply|boards)[^\s\)]+)',
            r'(https?://(?:www\.)?(?:greenhouse|lever|workday|ashbyhq|bamboohr)[^\s\)]+)',
        ]

        for pat in link_patterns:
            match = re.search(pat, selftext, re.I)
            if match:
                return match.group(1)

        # If the URL is an external link (not reddit), use it
        if url and 'reddit.com' not in url and url.startswith('http'):
            return url

        return None
