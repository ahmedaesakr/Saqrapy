"""
LinkedIn Poster
Posts job opportunities to LinkedIn Pages
"""

import logging
from typing import Dict, List, Optional
from .base_poster import BasePoster, PostResult

logger = logging.getLogger(__name__)


class LinkedInPoster(BasePoster):
    """
    Posts job opportunities to LinkedIn Company Pages.
    
    Requirements:
    - LinkedIn Marketing API access
    - Company Page admin access
    - requests package
    
    Configuration:
    {
        'access_token': 'your_linkedin_access_token',
        'organization_id': 'your_company_urn',  # Format: urn:li:organization:123456
        'author_mode': 'organization',  # or 'person'
        'person_id': 'your_person_urn',  # Optional, for personal posts
    }
    
    API Docs: https://docs.microsoft.com/en-us/linkedin/marketing/
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.platform_name = "LinkedIn"
        self.api_base = "https://api.linkedin.com/v2"
    
    def authenticate(self) -> bool:
        """
        Authenticate with LinkedIn Marketing API.
        
        Required config:
        - access_token: OAuth 2.0 access token
        - organization_id or person_id: Author URN
        """
        required = ['access_token']
        if not self.validate_config(required):
            return False
        
        if not self.config.get('organization_id') and not self.config.get('person_id'):
            logger.error("Either organization_id or person_id is required")
            return False
        
        try:
            import requests
            
            # Verify token
            headers = {
                'Authorization': f"Bearer {self.config['access_token']}",
                'Content-Type': 'application/json',
            }
            
            response = requests.get(
                f"{self.api_base}/me",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Successfully authenticated with LinkedIn")
                self.authenticated = True
                return True
            else:
                logger.error(f"LinkedIn auth failed: {response.status_code}")
                return False
                
        except ImportError:
            logger.error("requests not installed. Run: pip install requests")
            return False
        except Exception as e:
            logger.error(f"LinkedIn authentication failed: {e}")
            return False
    
    def format_post(self, job: Dict) -> str:
        """
        Format job into a professional LinkedIn post.
        
        Args:
            job: Job dictionary
        
        Returns:
            Formatted post suitable for LinkedIn's professional tone
        """
        # Get hashtags
        hashtags = self.get_hashtags(job)
        hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
        
        post = f"""
🎯 Exciting Opportunity Alert!

We're sharing a fantastic role that might be perfect for someone in your network:

📌 {job.get('title', 'Position Available')}
🏢 {job.get('company', 'Not specified')}
📍 {job.get('location', 'Not specified')}
💼 {job.get('type', 'Full Time')}

🔗 Apply here: {job.get('link', '')}

Know someone who'd be a great fit? Tag them below! 👇

{hashtag_str}
"""
        return post.strip()
    
    def format_roundup(self, jobs: List[Dict], title: str = None) -> str:
        """
        Format multiple jobs into a professional roundup.
        
        LinkedIn has a 3000 character limit for posts.
        """
        if title is None:
            title = f"🔥 {len(jobs)} Open Positions This Week"
        
        lines = [
            title,
            "",
            "Here are some excellent opportunities for professionals in our network:",
            "",
        ]
        
        for i, job in enumerate(jobs[:8], 1):  # Limited for character count
            lines.append(
                f"✅ {job.get('title', 'Unknown')} "
                f"@ {job.get('company', 'Unknown')} "
                f"| {job.get('location', 'N/A')}"
            )
        
        if len(jobs) > 8:
            lines.append(f"\n...plus {len(jobs) - 8} more opportunities!")
        
        lines.extend([
            "",
            "💡 Comment 'INTERESTED' + the position number for more details!",
            "",
            "🔄 Like and share to help others in your network!",
            "",
            "#OpenToWork #Hiring #CareerOpportunities #JobSearch",
        ])
        
        content = "\n".join(lines)
        
        # LinkedIn has 3000 character limit
        if len(content) > 3000:
            content = content[:2950] + "\n\n... See more in comments"
        
        return content
    
    def post(self, content: str, **kwargs) -> PostResult:
        """
        Post content to LinkedIn.
        
        Args:
            content: Formatted post content
            **kwargs: Optional - article_url, image_url
        
        Returns:
            PostResult with post details
        """
        if not self.authenticated:
            return PostResult(
                success=False,
                platform=self.platform_name,
                error="Not authenticated"
            )
        
        try:
            import requests
            
            # Determine author URN
            if self.config.get('author_mode') == 'person':
                author = f"urn:li:person:{self.config['person_id']}"
            else:
                author = f"urn:li:organization:{self.config['organization_id']}"
            
            headers = {
                'Authorization': f"Bearer {self.config['access_token']}",
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0',
            }
            
            # Build UGC Post payload
            post_data = {
                "author": author,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add article link if provided
            if 'article_url' in kwargs:
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                    "status": "READY",
                    "originalUrl": kwargs['article_url']
                }]
            
            response = requests.post(
                f"{self.api_base}/ugcPosts",
                headers=headers,
                json=post_data
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_id = result.get('id', '').split(':')[-1]
                post_url = f"https://www.linkedin.com/feed/update/{result.get('id', '')}"
                
                logger.info(f"Posted to LinkedIn: {post_id}")
                
                return PostResult(
                    success=True,
                    platform=self.platform_name,
                    post_id=post_id,
                    url=post_url
                )
            else:
                logger.error(f"LinkedIn post failed: {response.status_code} - {response.text}")
                return PostResult(
                    success=False,
                    platform=self.platform_name,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            logger.error(f"LinkedIn post failed: {e}")
            return PostResult(
                success=False,
                platform=self.platform_name,
                error=str(e)
            )
    
    def create_article(self, title: str, content: str, jobs: List[Dict]) -> PostResult:
        """
        Create a LinkedIn article with job listings.
        
        Note: Article creation requires additional API access.
        This is a placeholder for future implementation.
        """
        logger.warning("LinkedIn article creation not yet implemented")
        return PostResult(
            success=False,
            platform=self.platform_name,
            error="Article creation not implemented"
        )


# Example usage
if __name__ == "__main__":
    config = {
        'access_token': 'YOUR_ACCESS_TOKEN',
        'organization_id': '123456',
        'author_mode': 'organization',
    }
    
    poster = LinkedInPoster(config)
    
    # Test formatting
    test_job = {
        'title': 'Senior Product Designer',
        'company': 'Tech Startup',
        'location': 'Dubai, UAE (Hybrid)',
        'type': 'Full Time',
        'link': 'https://example.com/job/123',
    }
    
    print("Sample LinkedIn Post:")
    print("=" * 50)
    print(poster.format_post(test_job))
