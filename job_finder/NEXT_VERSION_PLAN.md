# Job Finder v2.0 - Next Version Plan

## 📅 Created: 2026-02-09

---

## 🐛 Bugs Fixed in Current Version

### Critical Issues Resolved:
1. ✅ **Missing Brotli Dependency** - Added `brotli>=1.2.0` to requirements.txt
   - Many sites use Brotli compression, causing `Response content isn't text` errors
   - Fixed by installing `brotli` package

2. ✅ **Wuzzuf Spider - Duplicate Import** - Moved `import re` and `relevant_keywords` to class level
   - Was re-importing and re-defining on every parse iteration
   - Now properly defined at class level for better performance

3. ✅ **Indeed Spider - Duplicate Import** - Removed `import re` from inside pagination block
   - Was already imported at top of file

### Deprecation Warnings (To Address in v2.0):
- ⚠️ `start_requests()` deprecated → should migrate to async `start()` method
- ⚠️ Middleware methods need updated signatures (remove `spider` argument)
- ⚠️ `process_spider_output()` needs to support async generators

---

## 🚀 Version 2.0 Feature Plan

### 📱 Feature 1: Social Media Job Posting

#### Facebook Posts Integration
```python
# New file: job_finder/social_media/facebook_poster.py

class FacebookPoster:
    """
    Posts job opportunities to Facebook Pages/Groups
    
    Requirements:
    - Facebook Graph API access token
    - Page/Group admin rights
    
    Features:
    - Auto-format job posts with emojis and structure
    - Include company logos (when available)
    - Schedule posts at optimal times
    - Track engagement metrics
    """
    
    def __init__(self, access_token, page_id):
        self.access_token = access_token
        self.page_id = page_id
    
    def format_job_post(self, job):
        """Format job data into attractive Facebook post"""
        return f"""
🔥 New Job Opportunity! 🔥

📌 {job['title']}
🏢 {job['company']}
📍 {job['location']}
💼 {job['type']}

🔗 Apply here: {job['link']}

#Jobs #Hiring #{job['title'].replace(' ', '')} #Career
        """
```

#### LinkedIn Posts Integration
```python
# New file: job_finder/social_media/linkedin_poster.py

class LinkedInPoster:
    """
    Posts curated job opportunities to LinkedIn
    
    Requirements:
    - LinkedIn Marketing API access
    - LinkedIn Page admin access
    
    Features:
    - Professional formatting
    - Hashtag optimization for reach
    - Company tagging (when possible)
    - Article format for job roundups
    """
    
    def create_job_roundup(self, jobs, category):
        """Create a professional job roundup post"""
        pass
    
    def post_single_job(self, job):
        """Post individual high-value job opportunity"""
        pass
```

#### X (Twitter) Posts Integration
```python
# New file: job_finder/social_media/twitter_poster.py

class TwitterPoster:
    """
    Posts job alerts to X (Twitter)
    
    Requirements:
    - Twitter API v2 access
    - Developer account
    
    Features:
    - Concise 280-character format
    - Smart hashtag selection
    - Thread creation for multiple jobs
    - Engagement tracking
    """
    
    def format_tweet(self, job):
        """Format job for Twitter's character limit"""
        title = job['title'][:50]
        company = job['company'][:30]
        return f"""
🚀 {title} at {company}

📍 {job['location']}
🔗 {job['link'][:50]}...

#Hiring #Jobs
        """
```

### Configuration for Social Media Posting
```yaml
# New file: job_finder/config/social_media.yaml

facebook:
  enabled: true
  access_token: ${FB_ACCESS_TOKEN}
  page_id: "your_page_id"
  post_schedule: "09:00,14:00,18:00"  # UTC
  max_posts_per_day: 10
  
linkedin:
  enabled: true
  access_token: ${LINKEDIN_TOKEN}
  org_id: "your_org_id"
  post_format: "roundup"  # or "single"
  roundup_schedule: "weekly"  # or "daily"
  
twitter:
  enabled: true
  api_key: ${TWITTER_API_KEY}
  api_secret: ${TWITTER_API_SECRET}
  access_token: ${TWITTER_ACCESS_TOKEN}
  access_token_secret: ${TWITTER_ACCESS_SECRET}
  max_tweets_per_day: 20
  thread_threshold: 5  # Create thread if more than 5 jobs
```

---

### 📂 Feature 2: Job Categories

#### New Category System
```python
# New file: job_finder/categories.py

class JobCategory:
    """Categorizes jobs for better organization"""
    
    # Remote Work Category
    REMOTE = {
        "name": "Remote Opportunities",
        "keywords": ["remote", "work from home", "wfh", "distributed", "anywhere"],
        "icon": "🏠",
        "output_file": "remote_jobs.json"
    }
    
    # Freelance Category
    FREELANCE = {
        "name": "Freelance & Contract",
        "keywords": ["freelance", "contract", "project-based", "gig", "hourly"],
        "platforms": ["upwork", "fiverr", "mostaql", "khamsat", "toptal"],
        "icon": "💼",
        "output_file": "freelance_jobs.json"
    }
    
    # Full-Time Employment Category
    FULLTIME = {
        "name": "Full-Time Positions",
        "keywords": ["full-time", "permanent", "employee", "salary"],
        "icon": "🏢",
        "output_file": "fulltime_jobs.json"
    }
    
    # Hybrid Category
    HYBRID = {
        "name": "Hybrid Work",
        "keywords": ["hybrid", "flexible", "2 days office", "3 days remote"],
        "icon": "🔄",
        "output_file": "hybrid_jobs.json"
    }
    
    # Location-Based Categories
    REGIONS = {
        "Egypt": {
            "keywords": ["egypt", "cairo", "alexandria", "giza"],
            "currency": "EGP"
        },
        "UAE": {
            "keywords": ["uae", "dubai", "abu dhabi", "sharjah"],
            "currency": "AED"
        },
        "Europe": {
            "keywords": ["germany", "uk", "france", "netherlands", "remote-first"],
            "currency": "EUR"
        }
    }
```

#### Enhanced Excel Export with Categories
```python
# Updated json_to_excel.py

def main():
    files = {
        # Job Type Categories
        '🏠 Remote': os.path.join(output_dir, 'remote_jobs.json'),
        '💼 Freelance': os.path.join(output_dir, 'freelance.json'),
        '🏢 Full-Time': os.path.join(output_dir, 'fulltime.json'),
        '🔄 Hybrid': os.path.join(output_dir, 'hybrid.json'),
        
        # Source Categories
        '📋 Job Boards': os.path.join(output_dir, 'wuzzuf_indeed.json'),
        '🔗 LinkedIn': os.path.join(output_dir, 'linkedin.json'),
        '🏛️ Career Pages': os.path.join(output_dir, 'career_pages.json'),
        
        # Region Categories
        '🇪🇬 Egypt': os.path.join(output_dir, 'egypt_jobs.json'),
        '🇦🇪 UAE': os.path.join(output_dir, 'uae_jobs.json'),
        '🇪🇺 Europe': os.path.join(output_dir, 'europe_jobs.json'),
    }
```

---

### 🕷️ Feature 3: New Spiders

#### Social Media Job Scrapers
```python
# New spiders to add:

1. facebook_jobs_spider.py  # Facebook Jobs
2. linkedin_recruiter_spider.py  # LinkedIn Job API + Recruiter insights
3. twitter_jobs_spider.py  # X Job posts from hiring accounts
```

#### Enhanced Remote Job Boards
```python
# Additional remote job boards to scrape:

1. RemoteOK - Already listed, needs selector updates
2. WeWorkRemotely - Already listed, needs selector updates
3. FlexJobs - Requires account
4. JustRemote - https://justremote.co
5. RemotiveIO - https://remotive.io
6. WorkingNomads - https://www.workingnomads.com
7. Remote.co - https://remote.co
8. Himalayas - https://himalayas.app
```

#### Freelance Platform Improvements
```python
# Enhanced freelance scraping:

1. Upwork - Needs Playwright (JS-heavy)
2. Freelancer.com - Add spider
3. PeoplePerHour - Add spider
4. 99designs - Add spider (for designers)
5. Behance Jobs - Add spider (creative roles)
6. Dribbble Jobs - Add spider (designers)
7. Guru - Add spider
```

---

## 📁 New Project Structure (v2.0)

```
job_finder/
├── job_finder/
│   ├── spiders/
│   │   ├── __init__.py
│   │   ├── wuzzuf_spider.py
│   │   ├── indeed_spider.py
│   │   ├── linkedin_spider.py
│   │   ├── freelance_spider.py
│   │   ├── career_spider.py
│   │   ├── remote_jobs_spider.py
│   │   ├── playwright_spider.py
│   │   └── NEW: social_jobs_spider.py  # FB, LinkedIn, X jobs
│   ├── social_media/                   # NEW MODULE
│   │   ├── __init__.py
│   │   ├── facebook_poster.py
│   │   ├── linkedin_poster.py
│   │   ├── twitter_poster.py
│   │   └── scheduler.py                # Post scheduling
│   ├── categories/                      # NEW MODULE
│   │   ├── __init__.py
│   │   ├── categorizer.py              # Auto-categorize jobs
│   │   └── filters.py                  # Category-based filtering
│   ├── config/                          # NEW MODULE
│   │   ├── social_media.yaml
│   │   ├── categories.yaml
│   │   └── keywords.yaml               # CV-based keywords
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py
│   ├── user_agents.py
│   ├── proxy_manager.py
│   └── captcha_handler.py
├── output/
│   ├── by_source/                       # NEW
│   │   ├── wuzzuf_indeed.json
│   │   ├── linkedin.json
│   │   └── ...
│   ├── by_category/                     # NEW
│   │   ├── remote_jobs.json
│   │   ├── freelance_jobs.json
│   │   ├── fulltime_jobs.json
│   │   └── hybrid_jobs.json
│   └── by_region/                       # NEW
│       ├── egypt_jobs.json
│       ├── uae_jobs.json
│       └── europe_jobs.json
├── all_jobs.xlsx                        # Enhanced with tabs per category
├── all_jobs_combined.xlsx
├── requirements.txt
├── run_all_spiders.bat
├── run_playwright_spider.bat
├── NEW: run_social_poster.bat          # Social media posting
├── NEW: run_with_categories.bat        # Categorized output
└── NEXT_VERSION_PLAN.md
```

---

## 🔧 Implementation Priority

### Phase 1: Bug Fixes & Stability (Current)
- [x] Fix brotli dependency
- [x] Fix duplicate imports
- [x] Update requirements.txt
- [ ] Update middlewares for new Scrapy API
- [ ] Add error handling for non-text responses

### Phase 2: Job Categories (Week 1)
- [ ] Create categories module
- [ ] Add category detection to pipelines
- [ ] Update Excel export with category tabs
- [ ] Create category-based output folders

### Phase 3: Social Media Integration (Week 2)
- [ ] Facebook Graph API integration
- [ ] LinkedIn API integration
- [ ] X/Twitter API integration
- [ ] Post scheduling system
- [ ] Rate limiting and compliance

### Phase 4: New Spiders & Sources (Week 3)
- [ ] Add Dribbble Jobs spider
- [ ] Add Behance Jobs spider
- [ ] Add additional remote job boards
- [ ] Improve Playwright spider reliability

---

## 📋 Technical Debt to Address

1. **Async Migration**
   - Convert `start_requests()` to async `start()` method
   - Update all spiders to use async patterns

2. **Middleware Updates**
   - Update signatures to remove deprecated `spider` argument
   - Add async support to middlewares

3. **Error Handling**
   - Add try/except for response parsing
   - Handle non-text responses gracefully
   - Better logging for failed requests

4. **Testing**
   - Add unit tests for spiders
   - Add integration tests
   - Mock external APIs for testing

---

## 🔐 Required API Keys for v2.0

```env
# .env file for API keys

# Facebook
FB_ACCESS_TOKEN=your_token
FB_PAGE_ID=your_page_id

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_token
LINKEDIN_ORG_ID=your_org_id

# X (Twitter)
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret

# Optional: Captcha Solving
CAPTCHA_2_API_KEY=your_key

# Optional: Proxy Service
PROXY_API_KEY=your_key
```

---

## 📈 Success Metrics

- **Job Discovery Rate**: Target 500+ relevant jobs per week
- **Category Accuracy**: 95%+ correct categorization
- **Social Media Reach**: Track impressions and engagement
- **Spider Success Rate**: 90%+ successful requests
- **Error Rate**: <5% failed parses

---

*Document maintained by Job Finder team*
*Last updated: 2026-02-09*
