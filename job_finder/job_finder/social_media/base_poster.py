"""
Base Poster Class
Abstract base class for all social media posters
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PostResult:
    """Result of a social media post attempt"""
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BasePoster(ABC):
    """
    Abstract base class for social media job posters.
    
    Implementations must override:
    - authenticate(): Connect to the platform API
    - format_post(): Convert job data to platform-specific format
    - post(): Send the post to the platform
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the poster with configuration.
        
        Args:
            config: Dictionary containing API credentials and settings
        """
        self.config = config
        self.authenticated = False
        self.platform_name = "Unknown"
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the social media platform.
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def format_post(self, job: Dict) -> str:
        """
        Format a job into a platform-appropriate post.
        
        Args:
            job: Job dictionary with title, company, location, link, etc.
        
        Returns:
            Formatted post string
        """
        pass
    
    @abstractmethod
    def post(self, content: str, **kwargs) -> PostResult:
        """
        Post content to the social media platform.
        
        Args:
            content: The formatted post content
            **kwargs: Platform-specific options (images, hashtags, etc.)
        
        Returns:
            PostResult with success status and details
        """
        pass
    
    def post_job(self, job: Dict, **kwargs) -> PostResult:
        """
        Convenience method to format and post a job in one step.
        
        Args:
            job: Job dictionary
            **kwargs: Platform-specific options
        
        Returns:
            PostResult with success status and details
        """
        if not self.authenticated:
            if not self.authenticate():
                return PostResult(
                    success=False,
                    platform=self.platform_name,
                    error="Authentication failed"
                )
        
        content = self.format_post(job)
        return self.post(content, **kwargs)
    
    def post_job_roundup(self, jobs: List[Dict], title: str = None) -> PostResult:
        """
        Post a roundup of multiple jobs.
        
        Args:
            jobs: List of job dictionaries
            title: Optional title for the roundup
        
        Returns:
            PostResult with success status
        """
        if not jobs:
            return PostResult(
                success=False,
                platform=self.platform_name,
                error="No jobs to post"
            )
        
        content = self.format_roundup(jobs, title)
        return self.post(content)
    
    def format_roundup(self, jobs: List[Dict], title: str = None) -> str:
        """
        Format multiple jobs into a roundup post.
        Override in subclasses for platform-specific formatting.
        
        Args:
            jobs: List of job dictionaries
            title: Optional title for the roundup
        
        Returns:
            Formatted roundup string
        """
        if title is None:
            title = f"🔥 {len(jobs)} New Job Opportunities!"
        
        lines = [title, ""]
        
        for i, job in enumerate(jobs[:10], 1):  # Limit to 10 jobs
            lines.append(f"{i}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
        
        if len(jobs) > 10:
            lines.append(f"... and {len(jobs) - 10} more!")
        
        return "\n".join(lines)
    
    def get_hashtags(self, job: Dict) -> List[str]:
        """
        Generate relevant hashtags for a job post.
        
        Args:
            job: Job dictionary
        
        Returns:
            List of hashtag strings (without #)
        """
        hashtags = ["Jobs", "Hiring", "Career"]
        
        # Add job type
        job_type = job.get('type', '').replace(' ', '')
        if job_type:
            hashtags.append(job_type)
        
        # Add location-based hashtags
        location = job.get('location', '').lower()
        if 'remote' in location:
            hashtags.extend(["Remote", "WorkFromHome", "RemoteJobs"])
        if 'egypt' in location or 'cairo' in location:
            hashtags.append("EgyptJobs")
        if 'uae' in location or 'dubai' in location:
            hashtags.append("DubaiJobs")
        
        # Add title-based hashtags
        title = job.get('title', '').lower()
        if 'designer' in title:
            hashtags.append("Design")
        if '3d' in title:
            hashtags.append("3DArtist")
        if 'developer' in title or 'engineer' in title:
            hashtags.append("Tech")
        
        return list(set(hashtags))[:10]  # Limit to 10 unique hashtags
    
    def validate_config(self, required_fields: List[str]) -> bool:
        """
        Validate that required config fields are present.
        
        Args:
            required_fields: List of required config key names
        
        Returns:
            True if all required fields present, False otherwise
        """
        missing = [f for f in required_fields if not self.config.get(f)]
        if missing:
            logger.error(f"Missing required config fields: {missing}")
            return False
        return True
