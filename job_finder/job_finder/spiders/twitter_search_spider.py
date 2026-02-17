"""
Twitter/X Job Search Spider - Social Media Search Edition

Searches Twitter/X for job posts matching Ahmed's CV profile.
Upgraded with Saudi Arabia, Emirates, Egypt, and Gulf region focus.

Features:
- Twitter API v2 Recent Search (requires Bearer Token)
- Fallback to Nitter public instances (no auth needed)
- DuckDuckGo site:twitter.com + site:x.com search (no auth needed)
- CV-based keyword filtering + Arabic keyword support
- Saudi Arabia, UAE, Egypt, and Gulf job market coverage
- Extracts tweet text, author, links, engagement metrics
- Handles threads and quoted tweets
"""

import scrapy
import re
import json
from urllib.parse import urlencode, quote_plus
import logging
from job_finder.cv_config import RELEVANT_KEYWORDS

logger = logging.getLogger(__name__)


class TwitterSearchSpider(scrapy.Spider):
    """
    Spider that searches Twitter/X for job posts matching CV profile.

    Supports 3 modes:
    1. Twitter API v2 (best, needs TWITTER_BEARER_TOKEN)
    2. Nitter instances (good, no auth needed)
    3. DuckDuckGo site search (fallback, always works)
    """

    name = "twitter_jobs"

    # CV-based keywords for filtering
    relevant_keywords = RELEVANT_KEYWORDS

    # Twitter search queries (each under 512 chars for API)
    search_queries = [
        # ── English: Direct hiring tweets ──
        '"hiring" "3D artist"',
        '"hiring" "product designer"',
        '"hiring" "UI designer" OR "UX designer"',
        '"hiring" "motion designer" OR "motion graphics"',
        '"hiring" "CGI" OR "visual effects"',
        '"looking for" "designer" "remote"',
        '"hiring" "blender" OR "unreal engine"',
        '"hiring" "generative AI" OR "AI designer"',
        '"hiring" "creative director" OR "art director"',
        '#hiring designer',
        '#remotejobs designer',
        '#designjobs',
        '#3Dartist hiring',

        # ── Saudi Arabia / Gulf focus ──
        '"hiring" "designer" "Saudi Arabia" OR "Riyadh" OR "Jeddah"',
        '"hiring" "designer" "Dubai" OR "Abu Dhabi" OR "UAE"',
        '"hiring" "3D" OR "CGI" "Saudi" OR "Gulf"',
        '"hiring" "motion" OR "VFX" "Riyadh" OR "Dubai"',
        '"we are hiring" designer "KSA" OR "Saudi"',
        '#SaudiJobs designer',
        '#UAEjobs designer',
        '#وظائف_السعودية مصمم',
        '#وظائف_الامارات مصمم',

        # ── Arabic: Saudi & Gulf hiring tweets ──
        'مطلوب مصمم ثلاثي الابعاد',
        'مطلوب مصمم جرافيك السعودية',
        'نبحث عن مصمم UI UX',
        'مطلوب مصمم موشن جرافيك',
        'وظيفة مصمم الرياض OR جدة',
        'مطلوب مصمم دبي OR ابوظبي',
        'توظيف مصمم عن بعد',
        '#توظيف مصمم',
        '#وظائف مصمم',
        'فرصة عمل مصمم ثري دي',
        'مطلوب مصمم CGI OR بلندر OR Blender',

        # ── Egypt focus ──
        '"hiring" "designer" "Egypt" OR "Cairo"',
        'مطلوب مصمم مصر OR القاهرة',
        '#وظائف_مصر مصمم',
    ]

    # Accounts known to post design/creative jobs
    job_accounts = [
        # ── International Design Jobs ──
        "designjobsboard",
        "UXDesignJobs",
        "remoteworkhunt",
        "GameJobHunter",
        "3DArtJobs",
        "AIJobsBoard",
        "RemoteOK",
        "wikijobart",

        # ── Saudi Arabia & Gulf Job Accounts ──
        "SaudiJobs_",
        "JobsSaudi",
        "Baaborh",              # Saudi job listings
        "Jadarat_sa",           # Jadarat Saudi platform
        "ABORH_",               # Saudi HR platform
        "LinkedInKSA",          # LinkedIn Saudi
        "GulfTalent",           # Gulf-wide talent
        "DubaiCareers",         # Dubai careers
        "UAEJobs_",             # UAE jobs
        "NaukriGulf",           # Naukri Gulf
        "waborh",               # Saudi recruitment

        # ── Egypt & MENA ──
        "WuzzufCareers",        # Wuzzuf Egypt
        "JobsMasterEG",         # Egypt jobs
    ]

    # Nitter instances (public Twitter mirrors, no auth needed)
    nitter_instances = [
        "nitter.net",
        "nitter.privacydev.net",
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 15,
    }

    def __init__(self, bearer_token=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bearer_token = bearer_token or self.settings.get('TWITTER_BEARER_TOKEN')
        self.use_api = bool(self.bearer_token)
        self.seen_tweets = set()

    def start_requests(self):
        """Generate requests based on available authentication"""

        if self.use_api:
            logger.info("Using Twitter API v2 with Bearer Token")
            yield from self._api_requests()
        else:
            logger.info("No Twitter Bearer Token found. Using Nitter + DuckDuckGo fallback")

        # Always run DuckDuckGo site search as supplementary source
        yield from self._duckduckgo_requests()

        # Always scrape Nitter for known job accounts
        yield from self._nitter_requests()

    # =========================================================================
    # MODE 1: Twitter API v2 (Best quality, needs auth)
    # =========================================================================

    def _api_requests(self):
        """Generate Twitter API v2 search requests"""
        for query in self.search_queries:
            # Use lang:en for English queries, lang:ar for Arabic
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

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )
        arabic_pattern = re.compile(
            r'(مصمم|ديزاينر|ثلاثي|3D|CGI|موشن|UI|UX|بلندر|Blender|انريل|Unreal|جرافيك|فريلانس|عن بعد|توظيف|مطلوب)',
            re.IGNORECASE
        )

        for tweet in tweets:
            tweet_id = tweet.get('id', '')

            if tweet_id in self.seen_tweets:
                continue
            self.seen_tweets.add(tweet_id)

            text = tweet.get('text', '')

            if not pattern.search(text) and not arabic_pattern.search(text):
                continue

            author_id = tweet.get('author_id', '')
            user = users.get(author_id, {})
            username = user.get('username', 'unknown')
            display_name = user.get('name', username)

            metrics = tweet.get('public_metrics', {})

            # Extract URLs from entities
            urls = []
            for url_entity in tweet.get('entities', {}).get('urls', []):
                expanded = url_entity.get('expanded_url', '')
                if expanded and 'twitter.com' not in expanded:
                    urls.append(expanded)

            apply_link = self._find_apply_link(urls)

            yield self._build_item(
                text=text,
                username=username,
                display_name=display_name,
                tweet_id=tweet_id,
                apply_link=apply_link,
                likes=metrics.get('like_count', 0),
                retweets=metrics.get('retweet_count', 0),
                query=query,
            )

    # =========================================================================
    # MODE 2: Nitter (No auth needed, public Twitter mirror)
    # =========================================================================

    def _nitter_requests(self):
        """Generate Nitter requests for known job accounts"""
        for instance in self.nitter_instances[:1]:  # Use first working instance
            for account in self.job_accounts:
                url = f"https://{instance}/{account}"
                yield scrapy.Request(
                    url,
                    callback=self.parse_nitter_profile,
                    meta={
                        'account': account,
                        'instance': instance,
                    },
                    errback=self.handle_error,
                    dont_filter=True,
                )

            # Nitter search
            for query in self.search_queries[:8]:
                clean_query = query.replace('"', '').replace('#', '')
                url = f"https://{instance}/search?q={quote_plus(clean_query)}&f=tweets"
                yield scrapy.Request(
                    url,
                    callback=self.parse_nitter_search,
                    meta={
                        'query': query,
                        'instance': instance,
                    },
                    errback=self.handle_error,
                    dont_filter=True,
                )

    def parse_nitter_profile(self, response):
        """Parse a Nitter profile page for job tweets"""
        account = response.meta.get('account', 'unknown')
        instance = response.meta.get('instance', '')

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )
        arabic_pattern = re.compile(
            r'(مصمم|ديزاينر|ثلاثي|3D|CGI|موشن|UI|UX|بلندر|Blender|انريل|Unreal|جرافيك|فريلانس|عن بعد|توظيف|مطلوب)',
            re.IGNORECASE
        )

        # Nitter uses .timeline-item for tweets
        tweets = response.css('.timeline-item')

        for tweet in tweets:
            text = ' '.join(tweet.css('.tweet-content::text, .tweet-content a::text').getall()).strip()

            if not text or (not pattern.search(text) and not arabic_pattern.search(text)):
                continue

            # Get tweet link
            tweet_link = tweet.css('.tweet-link::attr(href)').get()
            if tweet_link:
                # Convert Nitter link to Twitter link
                tweet_id = tweet_link.strip('/').split('/')[-1]
            else:
                tweet_id = ''

            username = tweet.css('.username::text').get('').strip().lstrip('@') or account
            display_name = tweet.css('.fullname::text').get('').strip() or account

            # Extract links from tweet
            links = tweet.css('.tweet-content a::attr(href)').getall()
            external_links = [l for l in links if 'twitter.com' not in l and l.startswith('http')]
            apply_link = self._find_apply_link(external_links)

            stats = tweet.css('.tweet-stat .tweet-stat-num::text').getall()
            likes = int(stats[2]) if len(stats) > 2 and stats[2].isdigit() else 0
            retweets = int(stats[1]) if len(stats) > 1 and stats[1].isdigit() else 0

            if tweet_id not in self.seen_tweets:
                self.seen_tweets.add(tweet_id)
                yield self._build_item(
                    text=text,
                    username=username,
                    display_name=display_name,
                    tweet_id=tweet_id,
                    apply_link=apply_link,
                    likes=likes,
                    retweets=retweets,
                    query=f'@{account}',
                )

    def parse_nitter_search(self, response):
        """Parse Nitter search results"""
        query = response.meta.get('query', 'unknown')

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )
        arabic_pattern = re.compile(
            r'(مصمم|ديزاينر|ثلاثي|3D|CGI|موشن|UI|UX|بلندر|Blender|انريل|Unreal|جرافيك|فريلانس|عن بعد|توظيف|مطلوب)',
            re.IGNORECASE
        )

        tweets = response.css('.timeline-item')
        logger.info(f"Nitter search found {len(tweets)} tweets for: {query}")

        for tweet in tweets:
            text = ' '.join(tweet.css('.tweet-content::text, .tweet-content a::text').getall()).strip()

            if not text or (not pattern.search(text) and not arabic_pattern.search(text)):
                continue

            tweet_link = tweet.css('.tweet-link::attr(href)').get()
            tweet_id = tweet_link.strip('/').split('/')[-1] if tweet_link else ''

            username = tweet.css('.username::text').get('').strip().lstrip('@')
            display_name = tweet.css('.fullname::text').get('').strip() or username

            links = tweet.css('.tweet-content a::attr(href)').getall()
            external_links = [l for l in links if 'twitter.com' not in l and l.startswith('http')]
            apply_link = self._find_apply_link(external_links)

            if tweet_id and tweet_id not in self.seen_tweets:
                self.seen_tweets.add(tweet_id)
                yield self._build_item(
                    text=text,
                    username=username,
                    display_name=display_name,
                    tweet_id=tweet_id,
                    apply_link=apply_link,
                    likes=0,
                    retweets=0,
                    query=query,
                )

    # =========================================================================
    # MODE 3: DuckDuckGo site:twitter.com search (Always works)
    # =========================================================================

    def _duckduckgo_requests(self):
        """Generate DuckDuckGo site:twitter.com + site:x.com search requests"""
        ddg_queries = [
            # ── English: Global design/creative jobs ──
            'site:twitter.com "hiring" "3D artist"',
            'site:twitter.com "hiring" "product designer" "remote"',
            'site:twitter.com "hiring" "UI UX designer"',
            'site:twitter.com "hiring" "motion designer"',
            'site:twitter.com "hiring" "CGI" OR "VFX" artist',
            'site:twitter.com "hiring" "blender" OR "unreal engine"',
            'site:twitter.com "hiring" "generative AI"',
            'site:x.com "hiring" designer "remote"',
            'site:x.com "hiring" "3D artist"',

            # ── Saudi Arabia focus ──
            'site:x.com "hiring" designer "Saudi Arabia" OR "Riyadh"',
            'site:x.com "hiring" "3D" OR "CGI" "Saudi" OR "KSA"',
            'site:x.com "hiring" designer "Jeddah" OR "NEOM"',
            'site:x.com "we are hiring" "Saudi" designer OR creative',
            'site:twitter.com "hiring" designer "Riyadh" OR "Saudi"',
            'site:x.com مطلوب مصمم السعودية',
            'site:x.com توظيف مصمم الرياض OR جدة',
            'site:x.com وظائف مصمم جرافيك السعودية',
            'site:x.com مطلوب مصمم ثلاثي الابعاد السعودية',

            # ── UAE / Dubai focus ──
            'site:x.com "hiring" designer "Dubai" OR "Abu Dhabi"',
            'site:x.com "hiring" "3D artist" OR "motion designer" "UAE"',
            'site:x.com "we are hiring" "UAE" creative OR designer',
            'site:twitter.com "hiring" designer "Dubai" OR "UAE"',
            'site:x.com مطلوب مصمم دبي OR الامارات',
            'site:x.com توظيف مصمم ابوظبي OR دبي',

            # ── Egypt focus ──
            'site:x.com "hiring" designer "Egypt" OR "Cairo"',
            'site:x.com "hiring" "3D artist" OR "CGI" "Egypt"',
            'site:x.com مطلوب مصمم مصر OR القاهرة',

            # ── Gulf-wide + Qatar/Kuwait/Bahrain ──
            'site:x.com "hiring" designer "Qatar" OR "Doha"',
            'site:x.com "hiring" designer "Kuwait" OR "Bahrain"',
            'site:x.com "hiring" creative "Gulf" OR "GCC" OR "MENA"',
            'site:x.com وظائف مصمم قطر OR الكويت OR البحرين',

            # ── Hashtag searches on X ──
            'site:x.com #وظائف_السعودية مصمم',
            'site:x.com #SaudiJobs designer',
            'site:x.com #UAEjobs designer OR creative',
            'site:x.com #وظائف_الامارات مصمم',
        ]

        for query in ddg_queries:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            yield scrapy.Request(
                url,
                callback=self.parse_duckduckgo,
                meta={'query': query},
                errback=self.handle_error,
                dont_filter=True,
            )

    def parse_duckduckgo(self, response):
        """Parse DuckDuckGo search results for Twitter/X links"""
        query = response.meta.get('query', 'unknown')

        results = response.css('a.result__a')
        logger.info(f"DuckDuckGo found {len(results)} results for: {query}")

        pattern = re.compile(
            r'\b(' + '|'.join(self.relevant_keywords) + r')\b',
            re.IGNORECASE
        )
        arabic_pattern = re.compile(
            r'(مصمم|ديزاينر|ثلاثي|3D|CGI|موشن|UI|UX|بلندر|Blender|انريل|Unreal|جرافيك|فريلانس|عن بعد|توظيف|مطلوب|وظيفة|وظائف|نبحث)',
            re.IGNORECASE
        )

        for result in results[:15]:
            href = result.css('::attr(href)').get('')
            title = ' '.join(result.css('::text').getall()).strip()

            if not href:
                continue

            # Only process twitter.com or x.com links
            is_twitter = 'twitter.com' in href or 'x.com' in href
            if not is_twitter:
                continue

            if not pattern.search(title) and not arabic_pattern.search(title):
                continue

            # Extract username and tweet ID from URL
            username, tweet_id = self._parse_twitter_url(href)

            if tweet_id and tweet_id not in self.seen_tweets:
                self.seen_tweets.add(tweet_id)
                yield self._build_item(
                    text=title,
                    username=username,
                    display_name=username,
                    tweet_id=tweet_id,
                    apply_link=None,
                    likes=0,
                    retweets=0,
                    query=query,
                )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def handle_error(self, failure):
        """Handle request failures gracefully"""
        logger.warning(f"Twitter search request failed: {failure.request.url} - {failure.value}")

    def _build_item(self, text, username, display_name, tweet_id,
                    apply_link, likes, retweets, query):
        """Build a standardized job item from tweet data"""
        # Extract location from tweet text
        location = self._extract_location(text)

        # Extract job type
        job_type = self._extract_job_type(text)

        # Build tweet URL
        tweet_url = f"https://twitter.com/{username}/status/{tweet_id}" if tweet_id else ''

        # Clean title (first 100 chars of tweet)
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
            # English patterns
            r'(?:hiring|looking\s*for)\s*(?:a\s+)?([^.!?\n]{10,80})',
            r'(?:open\s*)?(?:role|position):\s*([^.!?\n]{10,80})',
            # Arabic patterns
            r'(?:مطلوب|نبحث عن|نحتاج)\s+([^.!?\n]{10,80})',
            r'(?:وظيفة|فرصة عمل):\s*([^.!?\n]{10,80})',
            # Fallback: first line
            r'^([^.!?\n]{10,100})',
        ]

        for pat in patterns:
            match = re.search(pat, text, re.I)
            if match:
                title = match.group(1).strip()
                # Remove URLs
                title = re.sub(r'https?://\S+', '', title).strip()
                if len(title) > 10:
                    return title[:100]

        # Fallback: first line
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
            # Saudi Arabia
            (r'\b(Riyadh|الرياض)\b', 'Saudi Arabia - Riyadh'),
            (r'\b(Jeddah|جدة|جده)\b', 'Saudi Arabia - Jeddah'),
            (r'\b(NEOM|نيوم)\b', 'Saudi Arabia - NEOM'),
            (r'\b(Dammam|الدمام)\b', 'Saudi Arabia - Dammam'),
            (r'\b(Saudi\s*Arabia|KSA|السعودية)\b', 'Saudi Arabia'),
            # UAE
            (r'\b(Dubai|دبي)\b', 'UAE - Dubai'),
            (r'\b(Abu\s*Dhabi|ابوظبي|أبوظبي)\b', 'UAE - Abu Dhabi'),
            (r'\b(Sharjah|الشارقة)\b', 'UAE - Sharjah'),
            (r'\b(UAE|الامارات|الإمارات)\b', 'UAE'),
            # Qatar
            (r'\b(Qatar|Doha|قطر|الدوحة)\b', 'Qatar'),
            # Kuwait
            (r'\b(Kuwait|الكويت)\b', 'Kuwait'),
            # Bahrain
            (r'\b(Bahrain|البحرين|المنامة)\b', 'Bahrain'),
            # Oman
            (r'\b(Oman|عمان|مسقط)\b', 'Oman'),
            # Egypt
            (r'\b(Cairo|القاهرة)\b', 'Egypt - Cairo'),
            (r'\b(Alexandria|الاسكندرية)\b', 'Egypt - Alexandria'),
            (r'\b(Egypt|مصر)\b', 'Egypt'),
            # Europe
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
        # Priority: job boards > company sites > any link
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
