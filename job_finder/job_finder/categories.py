"""
Job Categories System
Categorizes scraped jobs into Remote, Freelance, Full-Time, Hybrid, and by Region
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class JobType(Enum):
    """Job employment type categories"""
    REMOTE = "remote"
    FREELANCE = "freelance"
    FULLTIME = "fulltime"
    HYBRID = "hybrid"
    PARTTIME = "parttime"
    CONTRACT = "contract"
    UNKNOWN = "unknown"


class Region(Enum):
    """Geographic region categories"""
    EGYPT = "egypt"
    UAE = "uae"
    EUROPE = "europe"
    USA = "usa"
    GLOBAL = "global"
    UNKNOWN = "unknown"


@dataclass
class CategoryConfig:
    """Configuration for a job category"""
    name: str
    patterns: List[str]
    icon: str
    output_file: str
    priority: int = 0  # Higher = more specific


# Category Definitions
REMOTE_PATTERNS = [
    r'\bremote\b',
    r'\bwork\s*from\s*home\b',
    r'\bwfh\b',
    r'\bdistributed\b',
    r'\banywhere\b',
    r'\bfully\s*remote\b',
    r'\b100%\s*remote\b',
]

FREELANCE_PATTERNS = [
    r'\bfreelance\b',
    r'\bcontract\b',
    r'\bproject[-\s]based\b',
    r'\bgig\b',
    r'\bhourly\b',
    r'\bper\s*project\b',
    r'\bshort[-\s]term\b',
]

HYBRID_PATTERNS = [
    r'\bhybrid\b',
    r'\bflexible\s*(?:work|location)\b',
    r'\b\d+\s*days?\s*(?:in\s*)?office\b',
    r'\b\d+\s*days?\s*remote\b',
    r'\bpartially\s*remote\b',
]

FULLTIME_PATTERNS = [
    r'\bfull[-\s]?time\b',
    r'\bpermanent\b',
    r'\bemployee\b',
    r'\bsalaried\b',
    r'\bfte\b',
]

# Region Patterns
EGYPT_PATTERNS = [
    r'\begypt\b',
    r'\bcairo\b',
    r'\balexandria\b',
    r'\bgiza\b',
    r'\bmaadi\b',
    r'\bnasr\s*city\b',
    r'\bnew\s*cairo\b',
]

UAE_PATTERNS = [
    r'\buae\b',
    r'\bdubai\b',
    r'\babu\s*dhabi\b',
    r'\bsharjah\b',
    r'\bajman\b',
    r'\bunited\s*arab\s*emirates\b',
    r'\bemirati\b',
]

EUROPE_PATTERNS = [
    r'\bgermany\b',
    r'\buk\b',
    r'\bunited\s*kingdom\b',
    r'\bfrance\b',
    r'\bnetherlands\b',
    r'\bspain\b',
    r'\bitaly\b',
    r'\beurope\b',
    r'\beu\b',
    r'\bberlin\b',
    r'\blondon\b',
    r'\bparis\b',
    r'\bamsterdam\b',
]

# Freelance Platform Indicators
FREELANCE_PLATFORMS = [
    'upwork',
    'fiverr',
    'mostaql',
    'khamsat',
    'toptal',
    'freelancer',
    'peopleperhour',
    'guru',
    '99designs',
]


class JobCategorizer:
    """
    Categorizes jobs based on title, location, type, and source.
    Uses pattern matching for accurate classification.
    """
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile all regex patterns for performance"""
        self.remote_regex = re.compile(
            '|'.join(REMOTE_PATTERNS), 
            re.IGNORECASE
        )
        self.freelance_regex = re.compile(
            '|'.join(FREELANCE_PATTERNS), 
            re.IGNORECASE
        )
        self.hybrid_regex = re.compile(
            '|'.join(HYBRID_PATTERNS), 
            re.IGNORECASE
        )
        self.fulltime_regex = re.compile(
            '|'.join(FULLTIME_PATTERNS), 
            re.IGNORECASE
        )
        
        # Region patterns
        self.egypt_regex = re.compile(
            '|'.join(EGYPT_PATTERNS), 
            re.IGNORECASE
        )
        self.uae_regex = re.compile(
            '|'.join(UAE_PATTERNS), 
            re.IGNORECASE
        )
        self.europe_regex = re.compile(
            '|'.join(EUROPE_PATTERNS), 
            re.IGNORECASE
        )
    
    def categorize(self, job: Dict) -> Dict:
        """
        Add category fields to a job item.
        
        Args:
            job: Job dictionary with title, location, type, source, etc.
        
        Returns:
            Job dictionary with added category fields
        """
        # Combine relevant text for matching
        text = self._get_searchable_text(job)
        source = job.get('source', '').lower()
        
        # Determine job type
        job_type = self._detect_job_type(text, source)
        
        # Determine region
        region = self._detect_region(job)
        
        # Add category fields
        job['job_category'] = job_type.value
        job['job_category_icon'] = self._get_type_icon(job_type)
        job['region_category'] = region.value
        job['region_icon'] = self._get_region_icon(region)
        job['is_remote'] = job_type in [JobType.REMOTE, JobType.FREELANCE]
        
        return job
    
    def _get_searchable_text(self, job: Dict) -> str:
        """Combine all relevant fields for pattern matching"""
        fields = [
            job.get('title', ''),
            job.get('location', ''),
            job.get('type', ''),
            job.get('company', ''),
        ]
        return ' '.join(filter(None, fields))
    
    def _detect_job_type(self, text: str, source: str) -> JobType:
        """Detect the job type category"""
        # Check if from freelance platform
        if any(platform in source for platform in FREELANCE_PLATFORMS):
            return JobType.FREELANCE
        
        # Check patterns in order of specificity
        if self.freelance_regex.search(text):
            return JobType.FREELANCE
        
        if self.hybrid_regex.search(text):
            return JobType.HYBRID
        
        if self.remote_regex.search(text):
            return JobType.REMOTE
        
        if self.fulltime_regex.search(text):
            return JobType.FULLTIME
        
        # Default to full-time for job board listings
        return JobType.FULLTIME
    
    def _detect_region(self, job: Dict) -> Region:
        """Detect the geographic region"""
        location = job.get('location', '')
        region_field = job.get('region', '')
        text = f"{location} {region_field}"
        
        if self.egypt_regex.search(text):
            return Region.EGYPT
        
        if self.uae_regex.search(text):
            return Region.UAE
        
        if self.europe_regex.search(text):
            return Region.EUROPE
        
        # Check for remote/global indicators
        if 'remote' in text.lower() or 'global' in text.lower():
            return Region.GLOBAL
        
        return Region.UNKNOWN
    
    def _get_type_icon(self, job_type: JobType) -> str:
        """Get emoji icon for job type"""
        icons = {
            JobType.REMOTE: "🏠",
            JobType.FREELANCE: "💼",
            JobType.FULLTIME: "🏢",
            JobType.HYBRID: "🔄",
            JobType.PARTTIME: "⏰",
            JobType.CONTRACT: "📝",
            JobType.UNKNOWN: "❓",
        }
        return icons.get(job_type, "❓")
    
    def _get_region_icon(self, region: Region) -> str:
        """Get flag emoji for region"""
        icons = {
            Region.EGYPT: "🇪🇬",
            Region.UAE: "🇦🇪",
            Region.EUROPE: "🇪🇺",
            Region.USA: "🇺🇸",
            Region.GLOBAL: "🌍",
            Region.UNKNOWN: "📍",
        }
        return icons.get(region, "📍")


# Global categorizer instance
categorizer = JobCategorizer()


def categorize_job(job: Dict) -> Dict:
    """Convenience function to categorize a job"""
    return categorizer.categorize(job)


def filter_by_category(jobs: List[Dict], category: JobType) -> List[Dict]:
    """Filter jobs by category"""
    return [j for j in jobs if j.get('job_category') == category.value]


def filter_by_region(jobs: List[Dict], region: Region) -> List[Dict]:
    """Filter jobs by region"""
    return [j for j in jobs if j.get('region_category') == region.value]


def filter_remote_only(jobs: List[Dict]) -> List[Dict]:
    """Filter to remote jobs only"""
    return [j for j in jobs if j.get('is_remote', False)]


if __name__ == "__main__":
    # Test categorization
    test_jobs = [
        {
            "title": "Senior Product Designer",
            "company": "Remote-First Startup",
            "location": "Remote - Anywhere",
            "type": "Full Time",
            "source": "LinkedIn"
        },
        {
            "title": "3D Artist - Contract",
            "company": "Game Studio",
            "location": "Dubai, UAE",
            "type": "Contract",
            "source": "Career Page"
        },
        {
            "title": "UI/UX Designer",
            "company": "Tech Company",
            "location": "Cairo, Egypt",
            "type": "Full Time",
            "source": "Wuzzuf"
        },
        {
            "title": "Motion Graphics Project",
            "company": "Freelance Client",
            "location": "Remote",
            "type": "Freelance",
            "source": "Upwork"
        },
        {
            "title": "Senior Designer - Hybrid",
            "company": "Enterprise Corp",
            "location": "Berlin, Germany (2 days office)",
            "type": "Full Time",
            "source": "Indeed"
        },
    ]
    
    print("=" * 60)
    print("Job Categorization Test")
    print("=" * 60)
    
    for job in test_jobs:
        categorized = categorize_job(job)
        print(f"\n{categorized['job_category_icon']} {categorized['title']}")
        print(f"   Type: {categorized['job_category']}")
        print(f"   {categorized['region_icon']} Region: {categorized['region_category']}")
        print(f"   Remote: {categorized['is_remote']}")
