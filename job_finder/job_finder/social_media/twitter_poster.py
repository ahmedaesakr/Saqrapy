"""
Twitter (X) Poster
Posts job opportunities to X (formerly Twitter)
"""

import logging
from typing import Dict, List, Optional
from .base_poster import BasePoster, PostResult

logger = logging.getLogger(__name__)


class TwitterPoster(BasePoster):
    """
    Posts job opportunities to X (Twitter).
    
    Requirements:
    - Twitter Developer API v2 access
    - tweepy package: pip install tweepy
    
    Configuration:
    {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret',
        'access_token': 'your_access_token',
        'access_token_secret': 'your_access_token_secret',
        'bearer_token': 'your_bearer_token',  # For v2 API
    }
    
    API Docs: https://developer.twitter.com/en/docs/twitter-api
    """
    
    # Twitter character limit
    CHAR_LIMIT = 280
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.platform_name = "Twitter/X"
        self.client = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Twitter API v2 using OAuth 1.0a or 2.0.
        """
        required = ['api_key', 'api_secret', 'access_token', 'access_token_secret']
        if not self.validate_config(required):
            return False
        
        try:
            import tweepy
            
            # OAuth 1.0a User Context for posting
            self.client = tweepy.Client(
                consumer_key=self.config['api_key'],
                consumer_secret=self.config['api_secret'],
                access_token=self.config['access_token'],
                access_token_secret=self.config['access_token_secret']
            )
            
            # Verify credentials
            me = self.client.get_me()
            if me.data:
                logger.info(f"Authenticated as @{me.data.username}")
                self.authenticated = True
                return True
            else:
                logger.error("Twitter auth verification failed")
                return False
                
        except ImportError:
            logger.error("tweepy not installed. Run: pip install tweepy")
            return False
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            return False
    
    def format_post(self, job: Dict) -> str:
        """
        Format job into a tweet (280 characters max).
        
        Args:
            job: Job dictionary
        
        Returns:
            Formatted tweet
        """
        # Build components
        title = job.get('title', 'New Opportunity')[:50]
        company = job.get('company', '')[:30]
        location = job.get('location', '')[:20]
        link = job.get('link', '')
        
        # Get top hashtags (limited space)
        hashtags = self.get_hashtags(job)[:3]
        hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
        
        # Build tweet - prioritize essential info
        if company:
            main_line = f"🚀 {title} at {company}"
        else:
            main_line = f"🚀 {title}"
        
        # Calculate available space
        base = f"{main_line}\n📍 {location}\n🔗 {link}\n{hashtag_str}"
        
        # Truncate if needed
        if len(base) > self.CHAR_LIMIT:
            # Shorten link display (Twitter auto-shortens anyway)
            base = f"{main_line}\n📍 {location}\n🔗 Apply: {link[:30]}...\n{hashtag_str}"
        
        if len(base) > self.CHAR_LIMIT:
            # Minimal format
            base = f"🚀 {title[:40]}...\n📍 {location}\n{link}"
        
        return base[:self.CHAR_LIMIT]
    
    def format_roundup(self, jobs: List[Dict], title: str = None) -> str:
        """
        Format for a single tweet introducing a thread.
        
        Args:
            jobs: List of jobs
            title: Optional title
        
        Returns:
            Formatted tweet (first in thread)
        """
        count = len(jobs)
        
        if title:
            return f"{title}\n\n🧵 Thread: {count} new opportunities below 👇\n\n#Hiring #Jobs"
        
        return f"🔥 {count} New Job Opportunities! 🔥\n\n🧵 Thread of the latest openings matching your profile 👇\n\n#Hiring #Jobs #Career"
    
    def post(self, content: str, **kwargs) -> PostResult:
        """
        Post a tweet.
        
        Args:
            content: Tweet text
            **kwargs: Optional - reply_to (for threads)
        
        Returns:
            PostResult with tweet details
        """
        if not self.authenticated:
            return PostResult(
                success=False,
                platform=self.platform_name,
                error="Not authenticated"
            )
        
        try:
            # Check for thread reply
            reply_to = kwargs.get('reply_to')
            
            if reply_to:
                response = self.client.create_tweet(
                    text=content,
                    in_reply_to_tweet_id=reply_to
                )
            else:
                response = self.client.create_tweet(text=content)
            
            if response.data:
                tweet_id = response.data.get('id')
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
                
                logger.info(f"Posted to Twitter: {tweet_id}")
                
                return PostResult(
                    success=True,
                    platform=self.platform_name,
                    post_id=tweet_id,
                    url=tweet_url
                )
            else:
                return PostResult(
                    success=False,
                    platform=self.platform_name,
                    error="No data returned"
                )
                
        except Exception as e:
            logger.error(f"Twitter post failed: {e}")
            return PostResult(
                success=False,
                platform=self.platform_name,
                error=str(e)
            )
    
    def post_thread(self, jobs: List[Dict], intro: str = None) -> List[PostResult]:
        """
        Post a thread of job opportunities.
        
        Args:
            jobs: List of jobs to post
            intro: Optional intro tweet
        
        Returns:
            List of PostResults for each tweet
        """
        if not self.authenticated:
            return [PostResult(
                success=False,
                platform=self.platform_name,
                error="Not authenticated"
            )]
        
        results = []
        last_tweet_id = None
        
        try:
            # Post intro tweet
            if intro is None:
                intro = self.format_roundup(jobs)
            
            intro_result = self.post(intro)
            results.append(intro_result)
            
            if not intro_result.success:
                return results
            
            last_tweet_id = intro_result.post_id
            
            # Post each job as a reply
            for i, job in enumerate(jobs[:15]):  # Limit thread length
                tweet_text = f"{i+1}/{len(jobs[:15])}: {self.format_post(job)}"
                
                # Ensure within limit
                if len(tweet_text) > self.CHAR_LIMIT:
                    tweet_text = f"{i+1}. {job.get('title', '')[:40]}\n{job.get('link', '')}"
                
                result = self.post(tweet_text, reply_to=last_tweet_id)
                results.append(result)
                
                if result.success:
                    last_tweet_id = result.post_id
                else:
                    break
            
            logger.info(f"Posted thread with {len(results)} tweets")
            return results
            
        except Exception as e:
            logger.error(f"Thread posting failed: {e}")
            results.append(PostResult(
                success=False,
                platform=self.platform_name,
                error=str(e)
            ))
            return results
    
    def get_hashtags(self, job: Dict) -> List[str]:
        """
        Get Twitter-optimized hashtags (shorter, trending).
        """
        hashtags = []
        
        title = job.get('title', '').lower()
        location = job.get('location', '').lower()
        
        # Job type hashtags
        if 'remote' in location or 'remote' in title:
            hashtags.append("RemoteWork")
        
        # Role-based hashtags
        if 'designer' in title:
            hashtags.append("Design")
        if '3d' in title:
            hashtags.append("3D")
        if 'developer' in title or 'engineer' in title:
            hashtags.append("Tech")
        if 'ai' in title or 'machine learning' in title:
            hashtags.append("AI")
        
        # General
        hashtags.extend(["Hiring", "Jobs"])
        
        return list(set(hashtags))[:4]  # Twitter prefers fewer hashtags


# Example usage
if __name__ == "__main__":
    config = {
        'api_key': 'YOUR_API_KEY',
        'api_secret': 'YOUR_API_SECRET',
        'access_token': 'YOUR_ACCESS_TOKEN',
        'access_token_secret': 'YOUR_ACCESS_TOKEN_SECRET',
    }
    
    poster = TwitterPoster(config)
    
    # Test formatting
    test_job = {
        'title': 'Senior Product Designer',
        'company': 'Tech Startup',
        'location': 'Remote',
        'type': 'Full Time',
        'link': 'https://example.com/job/123',
    }
    
    print("Sample Tweet:")
    print("=" * 50)
    tweet = poster.format_post(test_job)
    print(tweet)
    print(f"\nCharacter count: {len(tweet)}/{TwitterPoster.CHAR_LIMIT}")
