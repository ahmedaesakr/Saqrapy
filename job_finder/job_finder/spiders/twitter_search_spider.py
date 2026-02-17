"""
Twitter/X Job Search Spider - Social Media Search Edition

Searches Twitter/X for job posts matching Ahmed's CV profile.
Upgraded with Saudi Arabia, Emirates, Egypt, and Gulf region focus.

Features:
- Twitter Syndication API (NO auth needed! scrapes profile timelines)
- Twitter API v2 Recent Search (optional, requires Bearer Token)
- CV-based keyword filtering + Arabic keyword support
- Saudi Arabia, UAE, Egypt, and Gulf job market coverage
- Extracts tweet text, author, links, engagement metrics

How it works:
  Without API key: Scrapes 40+ job account timelines via Twitter's
  syndication endpoint (up to 99 tweets each). Filters for CV-relevant posts.

  With API key: Also runs keyword searches via Twitter API v2 for
  broader coverage. Set TWITTER_BEARER_TOKEN in settings.py.
"""

import scrapy
import re
import json
from urllib.parse import urlencode, quote_plus
import logging
from job_finder.cv_config import RELEVANT_KEYWORDS, is_relevant_social

logger = logging.getLogger(__name__)


class TwitterSearchSpider(scrapy.Spider):
    """
    Spider that searches Twitter/X for job posts matching CV profile.

    Modes:
    1. Twitter Syndication (default, no auth needed) - scrapes profile timelines
    2. Twitter API v2 (optional, needs TWITTER_BEARER_TOKEN) - keyword search
    """

    name = "twitter_jobs"

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS

    # Twitter search queries - only used with API v2 bearer token
    search_queries = [
        # English: Direct hiring tweets
        '"hiring" "3D artist"',
        '"hiring" "product designer"',
        '"hiring" "UI designer" OR "UX designer"',
        '"hiring" "motion designer" OR "motion graphics"',
        '"hiring" "CGI" OR "visual effects"',
        '"looking for" "designer" "remote"',
        '"hiring" "blender" OR "unreal engine"',
        '"hiring" "generative AI" OR "AI designer"',
        '"hiring" "creative director" OR "art director"',

        # Saudi Arabia / Gulf focus
        '"hiring" "designer" "Saudi Arabia" OR "Riyadh" OR "Jeddah"',
        '"hiring" "designer" "Dubai" OR "Abu Dhabi" OR "UAE"',
        '"hiring" "3D" OR "CGI" "Saudi" OR "Gulf"',
        '"we are hiring" designer "KSA" OR "Saudi"',

        # Arabic
        'مطلوب مصمم ثلاثي الابعاد',
        'مطلوب مصمم جرافيك السعودية',
        'نبحث عن مصمم UI UX',
        'مطلوب مصمم موشن جرافيك',
        'توظيف مصمم عن بعد',
        'مطلوب مصمم مصر OR القاهرة',
    ]

    # Accounts to scrape via syndication - these post job listings
    job_accounts = [
        # ── International: Design & Creative Jobs ──
        "designjobsboard",
        "UXDesignJobs",
        "remoteworkhunt",
        "GameJobHunter",
        "3DArtJobs",
        "AIJobsBoard",
        "RemoteOK",
        "wikijobart",
        "Designjobs",
        "UXJobBoard",
        "driaborh",
        "DesignJobsHQ",
        "GraphicDesignJB",
        "CreativeJobsCen",

        # ── Saudi Arabia & Gulf Job Accounts ──
        "SaudiJobs_",
        "JobsSaudi",
        "Baaborh",
        "Jadarat_sa",
        "ABORH_",
        "GulfTalent",
        "DubaiCareers",
        "UAEJobs_",
        "NaukriGulf",
        "waborh",
        "Tawdheef",
        "SaudiExpatriates",
        "JobzillaSA",
        "waaborh",
        "HRDFsaudi",

        # ── Egypt & MENA ──
        "WuzzufCareers",
        "JobsMasterEG",
        "ForasaMasria",
        "ElWazifa",

        # ── Tech Companies (post job openings on X) ──
        "CanvaCareers",
        "FigmaCareers",
        "SpotifyJobs",
        "EpicGames",
        "unrealengine",
        "unity3d",
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 4,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 20,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [429, 500, 502, 503],
    }

    def __init__(self, bearer_token=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bearer_token_arg = bearer_token
        self.seen_tweets = set()

    def start_requests(self):
        """Generate requests - syndication profiles + optional API search"""
        # Access settings here (not in __init__) because Scrapy sets them later
        self.bearer_token = self._bearer_token_arg or self.settings.get('TWITTER_BEARER_TOKEN')
        self.use_api = bool(self.bearer_token)

        # MODE 1: If API token available, run keyword searches
        if self.use_api:
            logger.info("Twitter API v2 Bearer Token found - running keyword searches")
            yield from self._api_requests()
        else:
            logger.info("No Twitter Bearer Token. Using syndication profile scraping only.")
            logger.info("Tip: Set TWITTER_BEARER_TOKEN in settings.py for broader search coverage.")

        # MODE 2: Always scrape job account timelines via syndication (no auth needed)
        logger.info(f"Scraping {len(self.job_accounts)} job account timelines via syndication...")
        yield from self._syndication_requests()

    # =========================================================================
    # MODE 1: Twitter API v2 (Best quality, needs auth)
    # =========================================================================

    def _api_requests(self):
        """Generate Twitter API v2 search requests"""
        for query in self.search_queries:
            has_arabic = bool(re.search(r'[\u0600-\u06FF]', query))
            lang_filter = 'lang:ar' if has_arabic else 'lang:en'

            params = {
                'query': f'{query} -is:retweet {lang_filter}',
                'max_results': 50,
                'tweet.fields': 'created_at,author_id,public_metrics,entities,context_annotations',
                'user.fields': 'name,username,verified',
                'expansions': 'author_id',
                'sort_order': 'recency',
            }
            url = f"https://api.twitter.com/2/tweets/search/recent?{urlencode(params)}"
            yield scrapy.Request(
                url,
                callback=self.parse_api_results,
                headers={
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json',
                },
                meta={'query': query},
                errback=self.handle_error,
                dont_filter=True,
            )

    def parse_api_results(self, response):
        """Parse Twitter API v2 search results"""
        query = response.meta.get('query', 'unknown')

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Twitter API response for: {query}")
            return

        if 'errors' in data:
            logger.error(f"Twitter API error: {data['errors']}")
            return

        tweets = data.get('data', [])
        users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

        logger.info(f"Twitter API returned {len(tweets)} tweets for: {query}")

        for tweet in tweets:
            tweet_id = tweet.get('id', '')
            if tweet_id in self.seen_tweets:
                continue
            self.seen_tweets.add(tweet_id)

            text = tweet.get('text', '')
            if not self._is_relevant(text):
                continue

            author_id = tweet.get('author_id', '')
            user = users.get(author_id, {})
            username = user.get('username', 'unknown')
            display_name = user.get('name', username)
            metrics = tweet.get('public_metrics', {})

            urls = []
            for url_entity in tweet.get('entities', {}).get('urls', []):
                expanded = url_entity.get('expanded_url', '')
                if expanded and 'twitter.com' not in expanded:
                    urls.append(expanded)

            yield self._build_item(
                text=text,
                username=username,
                display_name=display_name,
                tweet_id=tweet_id,
                apply_link=self._find_apply_link(urls),
                likes=metrics.get('like_count', 0),
                retweets=metrics.get('retweet_count', 0),
                query=query,
            )

    # =========================================================================
    # MODE 2: Twitter Syndication (No auth needed! Primary method)
    # =========================================================================

    def _syndication_requests(self):
        """Scrape job account timelines via Twitter's syndication endpoint.
        Returns up to 99 tweets per account, rendered as server-side HTML+JSON."""
        for account in self.job_accounts:
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
            yield scrapy.Request(
                url,
                callback=self.parse_syndication_profile,
                meta={'account': account},
                errback=self.handle_error,
                dont_filter=True,
            )

    def parse_syndication_profile(self, response):
        """Parse Twitter syndication timeline - extracts tweets from __NEXT_DATA__ JSON"""
        account = response.meta.get('account', 'unknown')

        if response.status == 429:
            logger.warning(f"Rate limited on @{account} - will retry")
            return

        # Extract __NEXT_DATA__ JSON embedded in the HTML
        script = response.css('script#__NEXT_DATA__::text').get()
        if not script:
            # Fallback: regex extraction
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.DOTALL)
            script = match.group(1) if match else None

        if not script:
            logger.debug(f"No syndication data for @{account}")
            return

        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse syndication JSON for @{account}")
            return

        entries = (data.get('props', {})
                       .get('pageProps', {})
                       .get('timeline', {})
                       .get('entries', []))

        if not entries:
            logger.debug(f"@{account}: no tweets in timeline")
            return

        logger.info(f"@{account}: found {len(entries)} tweets in timeline")
        relevant_count = 0

        for entry in entries:
            content = entry.get('content', {})
            tweet = content.get('tweet', content)

            tweet_id = str(tweet.get('id_str', '') or entry.get('entry_id', '').replace('tweet-', ''))
            if not tweet_id or tweet_id in self.seen_tweets:
                continue
            self.seen_tweets.add(tweet_id)

            text = tweet.get('text', '')
            if not text or not self._is_relevant(text):
                continue

            relevant_count += 1
            user = tweet.get('user', {})
            username = user.get('screen_name', account)
            display_name = user.get('name', username)

            # Extract URLs from tweet entities
            urls = []
            for url_entity in tweet.get('entities', {}).get('urls', []):
                expanded = url_entity.get('expanded_url', '')
                if expanded and 'twitter.com' not in expanded and 'x.com' not in expanded:
                    urls.append(expanded)

            # Get engagement metrics
            likes = tweet.get('favorite_count', 0) or 0
            retweets = tweet.get('retweet_count', 0) or 0

            yield self._build_item(
                text=text,
                username=username,
                display_name=display_name,
                tweet_id=tweet_id,
                apply_link=self._find_apply_link(urls),
                likes=likes,
                retweets=retweets,
                query=f'@{account}',
            )

        if relevant_count:
            logger.info(f"@{account}: {relevant_count} relevant job tweets found!")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def handle_error(self, failure):
        """Handle request failures gracefully"""
        url = failure.request.url
        if '429' in str(failure.value):
            logger.warning(f"Rate limited: {url}")
        else:
            logger.warning(f"Request failed: {url} - {failure.value}")

    def _is_relevant(self, text):
        """Check if tweet text matches CV keywords (English + Arabic)"""
        return is_relevant_social(text)

    def _build_item(self, text, username, display_name, tweet_id,
                    apply_link, likes, retweets, query):
        """Build a standardized job item from tweet data"""
        location = self._extract_location(text)
        job_type = self._extract_job_type(text)
        tweet_url = f"https://x.com/{username}/status/{tweet_id}" if tweet_id else ''
        title = self._extract_title(text)

        return {
            'keyword_searched': query,
            'title': title,
            'company': f'@{username}' if username else 'Via Twitter/X',
            'location': location,
            'type': job_type,
            'link': apply_link or tweet_url,
            'tweet_link': tweet_url,
            'source': 'Twitter/X',
            'author': f'@{username}',
            'display_name': display_name,
            'likes': likes,
            'retweets': retweets,
            'full_text': text[:500],
        }

    def _extract_title(self, text):
        """Extract a clean job title from tweet text (English + Arabic)"""
        patterns = [
            r'(?:hiring|looking\s*for)\s*(?:a\s+)?([^.!?\n]{10,80})',
            r'(?:open\s*)?(?:role|position):\s*([^.!?\n]{10,80})',
            r'(?:مطلوب|نبحث عن|نحتاج)\s+([^.!?\n]{10,80})',
            r'(?:وظيفة|فرصة عمل):\s*([^.!?\n]{10,80})',
            r'^([^.!?\n]{10,100})',
        ]

        for pat in patterns:
            match = re.search(pat, text, re.I)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'https?://\S+', '', title).strip()
                if len(title) > 10:
                    return title[:100]

        first_line = text.split('\n')[0][:100]
        return re.sub(r'https?://\S+', '', first_line).strip() or text[:100]

    def _extract_location(self, text):
        """Extract location from tweet text (expanded for Gulf region)"""
        if re.search(r'\b(remote|anywhere|worldwide|global|عن بعد|ريموت)\b', text, re.I):
            if re.search(r'\b(UAE|Dubai|دبي|الامارات)\b', text, re.I):
                return 'Remote - UAE'
            if re.search(r'\b(Saudi|KSA|السعودية|الرياض)\b', text, re.I):
                return 'Remote - Saudi Arabia'
            if re.search(r'\b(Europe|EU|UK|Germany)\b', text, re.I):
                return 'Remote - Europe'
            return 'Remote'

        location_map = [
            (r'\b(Riyadh|الرياض)\b', 'Saudi Arabia - Riyadh'),
            (r'\b(Jeddah|جدة|جده)\b', 'Saudi Arabia - Jeddah'),
            (r'\b(NEOM|نيوم)\b', 'Saudi Arabia - NEOM'),
            (r'\b(Dammam|الدمام)\b', 'Saudi Arabia - Dammam'),
            (r'\b(Saudi\s*Arabia|KSA|السعودية)\b', 'Saudi Arabia'),
            (r'\b(Dubai|دبي)\b', 'UAE - Dubai'),
            (r'\b(Abu\s*Dhabi|ابوظبي|أبوظبي)\b', 'UAE - Abu Dhabi'),
            (r'\b(Sharjah|الشارقة)\b', 'UAE - Sharjah'),
            (r'\b(UAE|الامارات|الإمارات)\b', 'UAE'),
            (r'\b(Qatar|Doha|قطر|الدوحة)\b', 'Qatar'),
            (r'\b(Kuwait|الكويت)\b', 'Kuwait'),
            (r'\b(Bahrain|البحرين|المنامة)\b', 'Bahrain'),
            (r'\b(Oman|عمان|مسقط)\b', 'Oman'),
            (r'\b(Cairo|القاهرة)\b', 'Egypt - Cairo'),
            (r'\b(Alexandria|الاسكندرية)\b', 'Egypt - Alexandria'),
            (r'\b(Egypt|مصر)\b', 'Egypt'),
            (r'\b(London|UK)\b', 'UK'),
            (r'\b(Berlin|Germany)\b', 'Germany'),
            (r'\b(Amsterdam|Netherlands)\b', 'Netherlands'),
        ]

        for pat, loc in location_map:
            if re.search(pat, text, re.I):
                return loc

        return 'Not specified'

    def _extract_job_type(self, text):
        """Extract job type from tweet text (English + Arabic)"""
        if re.search(r'\b(freelance|contract|gig|فريلانس|عمل حر|مستقل)\b', text, re.I):
            return 'Freelance'
        if re.search(r'\b(part[-\s]?time|دوام جزئي)\b', text, re.I):
            return 'Part Time'
        if re.search(r'\b(remote|عن بعد|ريموت)\b', text, re.I):
            return 'Remote'
        if re.search(r'\b(full[-\s]?time|دوام كامل)\b', text, re.I):
            return 'Full Time'
        return 'Not specified'

    def _find_apply_link(self, urls):
        """Find the best application link from a list of URLs"""
        job_domains = ['greenhouse', 'lever', 'workday', 'ashbyhq', 'bamboohr',
                       'jobs', 'careers', 'apply', 'hire', 'linkedin.com/jobs',
                       'bayt.com', 'gulftalent', 'naukrigulf', 'wuzzuf', 'indeed']

        for url in urls:
            if any(domain in url.lower() for domain in job_domains):
                return url

        return urls[0] if urls else None

    def _parse_twitter_url(self, url):
        """Extract username and tweet ID from a Twitter/X URL"""
        match = re.search(r'(?:twitter\.com|x\.com)/(\w+)/status/(\d+)', url)
        if match:
            return match.group(1), match.group(2)

        match = re.search(r'(?:twitter\.com|x\.com)/(\w+)', url)
        if match:
            return match.group(1), ''

        return 'unknown', ''
