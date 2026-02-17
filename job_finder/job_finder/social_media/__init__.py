"""
Social Media Package
- Posting: Post job opportunities to Facebook, LinkedIn, and X (Twitter)
- Searching: Search social media for job posts (via Scrapy spiders)

Search Spiders (in job_finder/spiders/):
- reddit_spider.py          -> RedditJobsSpider      (name: reddit_jobs)
- twitter_search_spider.py  -> TwitterSearchSpider    (name: twitter_jobs)
- facebook_search_spider.py -> FacebookSearchSpider   (name: facebook_jobs)
- telegram_spider.py        -> TelegramJobsSpider     (name: telegram_jobs)
"""

from .base_poster import BasePoster, PostResult
from .facebook_poster import FacebookPoster
from .linkedin_poster import LinkedInPoster
from .twitter_poster import TwitterPoster

__all__ = [
    # Posters
    'BasePoster',
    'PostResult',
    'FacebookPoster',
    'LinkedInPoster',
    'TwitterPoster',
]
