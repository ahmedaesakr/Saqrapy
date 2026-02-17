"""
Facebook Poster
Posts job opportunities to Facebook Pages
"""

import logging
from typing import Dict, List, Optional
from .base_poster import BasePoster, PostResult

logger = logging.getLogger(__name__)


class FacebookPoster(BasePoster):
    """
    Posts job opportunities to Facebook Pages/Groups.
    
    Requirements:
    - Facebook Graph API access token
    - Page/Group admin rights
    - facebook-sdk package: pip install facebook-sdk
    
    Configuration:
    {
        'access_token': 'your_facebook_access_token',
        'page_id': 'your_page_id',
        'max_posts_per_day': 10,
        'include_images': True,
    }
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.platform_name = "Facebook"
        self.api = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Facebook Graph API.
        
        Required config:
        - access_token: Facebook Page Access Token
        - page_id: Facebook Page ID
        """
        if not self.validate_config(['access_token', 'page_id']):
            return False
        
        try:
            # Import facebook SDK (optional dependency)
            import facebook
            
            self.api = facebook.GraphAPI(
                access_token=self.config['access_token'],
                version="3.1"
            )
            
            # Verify token by getting page info
            page = self.api.get_object(self.config['page_id'])
            logger.info(f"Authenticated with Facebook page: {page.get('name')}")
            self.authenticated = True
            return True
            
        except ImportError:
            logger.error("facebook-sdk not installed. Run: pip install facebook-sdk")
            return False
        except Exception as e:
            logger.error(f"Facebook authentication failed: {e}")
            return False
    
    def format_post(self, job: Dict) -> str:
        """
        Format job into an attractive Facebook post.
        
        Args:
            job: Job dictionary
        
        Returns:
            Formatted post with emojis and structure
        """
        # Get category info if available
        type_icon = job.get('job_category_icon', '💼')
        region_icon = job.get('region_icon', '📍')
        
        # Build hashtags
        hashtags = self.get_hashtags(job)
        hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
        
        post = f"""
🔥 فرصة عمل جديدة! | New Job Opportunity! 🔥

{type_icon} {job.get('title', 'Position Available')}

🏢 Company: {job.get('company', 'Not specified')}
{region_icon} Location: {job.get('location', 'Not specified')}
📋 Type: {job.get('type', 'Not specified')}

🔗 Apply here: {job.get('link', '')}

{hashtag_str}

---
Follow for more job opportunities! 🚀
Like & Share to help someone find their dream job! ❤️
"""
        return post.strip()
    
    def format_roundup(self, jobs: List[Dict], title: str = None) -> str:
        """
        Format multiple jobs into a roundup post.
        
        Args:
            jobs: List of job dictionaries
            title: Optional title
        
        Returns:
            Formatted roundup
        """
        if title is None:
            title = f"🔥 {len(jobs)} New Job Opportunities This Week!"
        
        lines = [
            title,
            "",
            "Here are the latest openings matching your profile:",
            "",
        ]
        
        for i, job in enumerate(jobs[:10], 1):
            icon = job.get('job_category_icon', '💼')
            lines.append(
                f"{i}. {icon} {job.get('title', 'Unknown')} "
                f"at {job.get('company', 'Unknown')} "
                f"({job.get('location', 'N/A')})"
            )
        
        if len(jobs) > 10:
            lines.append(f"\n... and {len(jobs) - 10} more opportunities!")
        
        lines.extend([
            "",
            "🔗 Full list with links in the comments!",
            "",
            "#Jobs #Hiring #Career #JobSearch #Opportunities",
        ])
        
        return "\n".join(lines)
    
    def post(self, content: str, **kwargs) -> PostResult:
        """
        Post content to Facebook page.
        
        Args:
            content: Formatted post content
            **kwargs: Optional - image_url, link
        
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
            page_id = self.config['page_id']
            
            # Prepare post data
            post_data = {'message': content}
            
            # Add link if provided
            if 'link' in kwargs:
                post_data['link'] = kwargs['link']
            
            # Post to Facebook
            result = self.api.put_object(
                parent_object=page_id,
                connection_name='feed',
                **post_data
            )
            
            post_id = result.get('id')
            post_url = f"https://www.facebook.com/{post_id}" if post_id else None
            
            logger.info(f"Posted to Facebook: {post_id}")
            
            return PostResult(
                success=True,
                platform=self.platform_name,
                post_id=post_id,
                url=post_url
            )
            
        except Exception as e:
            logger.error(f"Facebook post failed: {e}")
            return PostResult(
                success=False,
                platform=self.platform_name,
                error=str(e)
            )
    
    def post_with_image(self, content: str, image_url: str) -> PostResult:
        """
        Post content with an image.
        
        Args:
            content: Post text
            image_url: URL of image to include
        
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
            page_id = self.config['page_id']
            
            result = self.api.put_object(
                parent_object=page_id,
                connection_name='photos',
                message=content,
                url=image_url
            )
            
            post_id = result.get('id')
            
            return PostResult(
                success=True,
                platform=self.platform_name,
                post_id=post_id,
                url=f"https://www.facebook.com/{post_id}"
            )
            
        except Exception as e:
            logger.error(f"Facebook image post failed: {e}")
            return PostResult(
                success=False,
                platform=self.platform_name,
                error=str(e)
            )


# Example usage
if __name__ == "__main__":
    config = {
        'access_token': 'YOUR_ACCESS_TOKEN',
        'page_id': 'YOUR_PAGE_ID',
    }
    
    poster = FacebookPoster(config)
    
    # Test formatting (doesn't require auth)
    test_job = {
        'title': 'Senior Product Designer',
        'company': 'Tech Startup',
        'location': 'Remote - UAE',
        'type': 'Full Time',
        'link': 'https://example.com/job/123',
        'job_category_icon': '🏠',
        'region_icon': '🇦🇪',
    }
    
    print("Sample Facebook Post:")
    print("=" * 50)
    print(poster.format_post(test_job))
