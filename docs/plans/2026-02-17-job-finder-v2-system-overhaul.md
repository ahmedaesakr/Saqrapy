# Job Finder v2.0 System Overhaul - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the broken data pipeline so all 10 spiders → categorization → Excel export works end-to-end, with shared CV config and proper item schema.

**Architecture:** The system has 3 phases: Scrape (10 Scrapy spiders) → Process (categorize_jobs.py deduplicates + categorizes) → Export (json_to_excel_v2.py creates multi-sheet Excel). Currently Phase 1 works, but Phase 2 ignores social media output and Phase 3 only shows 6/10 sources. The batch files have broken directory navigation and the v1 scripts reference dead paths. All spiders duplicate CV keywords instead of sharing a single config.

**Tech Stack:** Python 3, Scrapy 2.11+, pandas, openpyxl, Windows batch scripts

---

## System Audit Summary

### Data Flow Diagram (Current - BROKEN)

```
SPIDERS (10 total)                    OUTPUT PATHS
─────────────────                    ────────────
wuzzuf_jobs      ──→  output/by_source/wuzzuf.json        ─┐
indeed_jobs      ──→  output/by_source/indeed.json         │
linkedin_jobs    ──→  output/by_source/linkedin.json       ├─→ categorize_jobs.py  ✓ READS
freelance_jobs   ──→  output/by_source/freelance.json      │     (scans by_source/)
career_pages     ──→  output/by_source/career_pages.json   │
remote_jobs      ──→  output/by_source/remote_jobs.json    ─┘

reddit_jobs      ──→  output/social_media/reddit.json      ─┐
twitter_jobs     ──→  output/social_media/twitter.json      ├─→ categorize_jobs.py  ✗ IGNORES
facebook_jobs    ──→  output/social_media/facebook.json     │     (never scans social_media/)
telegram_jobs    ──→  output/social_media/telegram.json     ─┘

categorize_jobs.py ──→ by_category/*.json + by_region/*.json ──→ json_to_excel_v2.py
                                                                   ✗ MISSING social media sheets
                                                                   ✗ REFERENCES dead wuzzuf_indeed.json
```

### Critical Bugs Found

| # | Bug | File | Impact |
|---|-----|------|--------|
| 1 | `categorize_jobs.py` doesn't scan `output/social_media/` | categorize_jobs.py:88 | 4 spider sources invisible |
| 2 | `json_to_excel_v2.py` missing social media sheet definitions | json_to_excel_v2.py:84 | Excel shows 6/10 sources |
| 3 | `json_to_excel_v2.py` references dead `wuzzuf_indeed.json` | json_to_excel_v2.py:111 | Legacy file doesn't exist |
| 4 | `run_v2.bat` `:run_boards` calls `python categorize_jobs.py` from wrong dir | run_v2.bat:99 | Script looks for `job_finder/job_finder/output/` |
| 5 | CV keywords duplicated in 10 spiders with inconsistencies | all spiders | Wuzzuf missing "Digital", Freelance has extra keywords |
| 6 | `items.py` is empty - no schema validation | items.py | No data quality control |
| 7 | `pipelines.py` does nothing, not registered in settings | pipelines.py + settings.py | No dedup at scrape time |
| 8 | `requirements.txt` missing `requests` (needed by middlewares & posters) | requirements.txt | Import crashes on fresh install |
| 9 | `run_v2_social_post.bat` preview uses wrong Python path | run_v2_social_post.bat:42 | `sys.path` hack fragile |
| 10 | Indeed spider writes debug HTML to CWD (not output/) | indeed_spider.py:88 | Debug files leak into project root |

---

## Task 1: Create Shared CV Config Module

**Why:** All 10 spiders duplicate `relevant_keywords` with slight inconsistencies. One source of truth prevents drift.

**Files:**
- Create: `job_finder/job_finder/cv_config.py`
- Modify: All 10 spider files (replace inline keywords with import)

**Step 1: Create the shared config**

```python
# job_finder/job_finder/cv_config.py
"""
Shared CV profile configuration.
Single source of truth for all spiders' keyword filtering.
Based on: Ahmed Sakr - CGI Artist & Digital Product Designer
"""

# Keywords that match CV skills and target roles
# Used by all spiders for title/description filtering
RELEVANT_KEYWORDS = [
    # Core Roles
    r'Designer', r'Artist', r'Art Director', r'Creative Director',
    # 3D & CGI
    r'3D', r'CGI', r'VFX', r'Visualizer',
    # Product & UX
    r'Product', r'UI', r'UX',
    # Motion & Video
    r'Motion', r'Animation',
    # Tools (from CV)
    r'Unreal', r'Blender', r'Figma',
    # AI & Tech
    r'Generative', r'AI', r'Graphic',
    # Web & Dev
    r'Creative', r'Frontend', r'Web', r'Digital',
    # Specialty (from CV)
    r'DOOH', r'Anamorphic',
]

# Search queries by platform type
SEARCH_KEYWORDS = [
    "Product Designer",
    "3D Artist",
    "CGI Artist",
    "Digital Product Designer",
    "UI UX Designer",
    "Motion Designer",
    "Motion Graphics",
    "Generative AI",
    "Generative AI Designer",
    "Blender Artist",
    "Unreal Engine",
    "Art Director",
    "Creative Director",
]

# Freelance-specific extras (broader for gig platforms)
FREELANCE_EXTRA_KEYWORDS = [
    r'Logo', r'Video', r'Render', r'Model',
]
```

**Step 2: Update every spider to import from cv_config**

In each spider file, replace the inline `relevant_keywords` list:

```python
# BEFORE (in every spider):
relevant_keywords = [
    r'Designer', r'3D', r'Artist', ...
]

# AFTER:
from job_finder.cv_config import RELEVANT_KEYWORDS
# ... then in spider class:
relevant_keywords = RELEVANT_KEYWORDS
```

For `freelance_spider.py` specifically:
```python
from job_finder.cv_config import RELEVANT_KEYWORDS, FREELANCE_EXTRA_KEYWORDS
# ...
relevant_keywords = RELEVANT_KEYWORDS + FREELANCE_EXTRA_KEYWORDS
```

**Spiders to update (10 files):**
- `job_finder/job_finder/spiders/wuzzuf_spider.py`
- `job_finder/job_finder/spiders/indeed_spider.py`
- `job_finder/job_finder/spiders/linkedin_spider.py`
- `job_finder/job_finder/spiders/freelance_spider.py`
- `job_finder/job_finder/spiders/career_spider.py`
- `job_finder/job_finder/spiders/remote_jobs_spider.py`
- `job_finder/job_finder/spiders/playwright_spider.py`
- `job_finder/job_finder/spiders/reddit_spider.py`
- `job_finder/job_finder/spiders/twitter_search_spider.py`
- `job_finder/job_finder/spiders/facebook_search_spider.py`
- `job_finder/job_finder/spiders/telegram_spider.py`

**Step 3: Commit**

```bash
git add job_finder/job_finder/cv_config.py job_finder/job_finder/spiders/*.py
git commit -m "refactor: extract shared CV keywords to cv_config.py"
```

---

## Task 2: Define Proper Item Schema

**Why:** `items.py` is empty. Spiders yield raw dicts with no validation. A proper Item class documents the schema and enables pipeline processing.

**Files:**
- Modify: `job_finder/job_finder/items.py`

**Step 1: Define the item schema**

```python
# job_finder/job_finder/items.py
import scrapy


class JobItem(scrapy.Item):
    """Standard job item yielded by all spiders."""
    # Required fields (every spider must yield these)
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    type = scrapy.Field()           # Full Time, Freelance, Remote, etc.
    link = scrapy.Field()
    source = scrapy.Field()         # Spider name / platform
    keyword_searched = scrapy.Field()

    # Optional fields (some spiders add these)
    description = scrapy.Field()
    budget = scrapy.Field()         # Freelance projects
    date = scrapy.Field()
    salary = scrapy.Field()
    region = scrapy.Field()

    # Social media specific
    author = scrapy.Field()
    score = scrapy.Field()          # Reddit upvotes, tweet likes
    flair = scrapy.Field()
    full_text = scrapy.Field()
    tweet_link = scrapy.Field()
    reddit_link = scrapy.Field()
    telegram_link = scrapy.Field()
    channel = scrapy.Field()
    channel_name = scrapy.Field()
    views = scrapy.Field()
    display_name = scrapy.Field()
    likes = scrapy.Field()
    retweets = scrapy.Field()
    post_type = scrapy.Field()

    # Categorization (added by pipeline/categorizer)
    job_category = scrapy.Field()
    job_category_icon = scrapy.Field()
    region_category = scrapy.Field()
    region_icon = scrapy.Field()
    is_remote = scrapy.Field()
```

**Step 2: Commit**

```bash
git add job_finder/job_finder/items.py
git commit -m "feat: define JobItem schema for all spider outputs"
```

> **Note:** We do NOT need to change spiders to yield `JobItem` instead of `dict`. Scrapy accepts both. The item class serves as schema documentation and enables pipeline validation later.

---

## Task 3: Implement Dedup + Validation Pipeline

**Why:** `pipelines.py` does nothing. Duplicates only get caught in `categorize_jobs.py` (post-scrape). Catching them at scrape time is better.

**Files:**
- Modify: `job_finder/job_finder/pipelines.py`
- Modify: `job_finder/job_finder/settings.py` (register pipeline)

**Step 1: Implement the pipeline**

```python
# job_finder/job_finder/pipelines.py
from scrapy.exceptions import DropItem
import logging

logger = logging.getLogger(__name__)


class DeduplicationPipeline:
    """Drop duplicate items based on job link URL."""

    def __init__(self):
        self.seen_links = set()

    def process_item(self, item, spider):
        link = item.get('link', '')
        if link in self.seen_links:
            raise DropItem(f"Duplicate job: {item.get('title', '')}")
        if link:
            self.seen_links.add(link)
        return item


class CleaningPipeline:
    """Strip whitespace and normalize fields."""

    def process_item(self, item, spider):
        for field in ['title', 'company', 'location', 'type']:
            val = item.get(field)
            if isinstance(val, str):
                item[field] = val.strip()

        # Ensure required fields exist
        if not item.get('title'):
            raise DropItem("Missing title")
        if not item.get('link'):
            raise DropItem("Missing link")

        return item
```

**Step 2: Register pipeline in settings.py**

Add after line 111 in `job_finder/job_finder/settings.py`:

```python
# =============================================================================
# ITEM PIPELINES
# =============================================================================

ITEM_PIPELINES = {
    "job_finder.pipelines.CleaningPipeline": 100,
    "job_finder.pipelines.DeduplicationPipeline": 200,
}
```

**Step 3: Commit**

```bash
git add job_finder/job_finder/pipelines.py job_finder/job_finder/settings.py
git commit -m "feat: add dedup and cleaning pipelines"
```

---

## Task 4: Fix categorize_jobs.py (Add Social Media Sources)

**Why:** `categorize_jobs.py` line 88 only scans `by_source/` and `output/`. It never touches `social_media/`. 4 spider sources are invisible to categorization.

**Files:**
- Modify: `categorize_jobs.py:86-91`

**Step 1: Add social_media path to source patterns**

Replace lines 86-91 in `categorize_jobs.py`:

```python
    # BEFORE:
    source_patterns = [
        os.path.join(BY_SOURCE, '*.json'),
        os.path.join(OUTPUT_DIR, '*.json'),
    ]

    # AFTER:
    SOCIAL_MEDIA = os.path.join(OUTPUT_DIR, 'social_media')
    source_patterns = [
        os.path.join(BY_SOURCE, '*.json'),
        os.path.join(SOCIAL_MEDIA, '*.json'),
        os.path.join(OUTPUT_DIR, '*.json'),
    ]
```

Also add `SOCIAL_MEDIA` directory definition at the top (after line 25):

```python
SOCIAL_MEDIA = os.path.join(OUTPUT_DIR, 'social_media')
```

**Step 2: Commit**

```bash
git add categorize_jobs.py
git commit -m "fix: include social media output in categorization pipeline"
```

---

## Task 5: Fix json_to_excel_v2.py (Add Social Media Sheets + Remove Dead Refs)

**Why:** Excel export only has 6 source sheets. Missing Reddit, Twitter, Facebook, Telegram. Also references dead `wuzzuf_indeed.json` from v1.

**Files:**
- Modify: `json_to_excel_v2.py:80-113`

**Step 1: Add social media directory and sheets**

Add after line 22:
```python
SOCIAL_MEDIA = os.path.join(OUTPUT_DIR, 'social_media')
```

Replace the `source_files` dict (lines 84-91) with:

```python
    # --- BY SOURCE (Job Boards) ---
    source_files = {
        'Wuzzuf': os.path.join(BY_SOURCE, 'wuzzuf.json'),
        'Indeed': os.path.join(BY_SOURCE, 'indeed.json'),
        'LinkedIn': os.path.join(BY_SOURCE, 'linkedin.json'),
        'Freelance': os.path.join(BY_SOURCE, 'freelance.json'),
        'Career Pages': os.path.join(BY_SOURCE, 'career_pages.json'),
        'Remote Jobs': os.path.join(BY_SOURCE, 'remote_jobs.json'),
    }

    # --- SOCIAL MEDIA SOURCES ---
    social_files = {
        'Reddit': os.path.join(SOCIAL_MEDIA, 'reddit.json'),
        'Twitter-X': os.path.join(SOCIAL_MEDIA, 'twitter.json'),
        'Facebook': os.path.join(SOCIAL_MEDIA, 'facebook.json'),
        'Telegram': os.path.join(SOCIAL_MEDIA, 'telegram.json'),
    }
```

Replace the `legacy_files` dict (lines 109-113) — remove the dead `wuzzuf_indeed.json`:

```python
    # --- COMBINED ---
    combined_files = {
        'All Jobs': os.path.join(OUTPUT_DIR, 'all_jobs_categorized.json'),
    }
```

Update the merge line (line 116):

```python
    all_files = {**source_files, **social_files, **category_files, **region_files, **combined_files}
```

**Step 2: Commit**

```bash
git add json_to_excel_v2.py
git commit -m "fix: add social media sheets to Excel export, remove dead v1 refs"
```

---

## Task 6: Fix Batch File Directory Navigation

**Why:** `run_v2.bat` `:run_boards` section runs spiders from `job_finder/` then calls `python categorize_jobs.py` from the same dir — but that script expects to be called from root (it builds paths as `job_finder/output/`).

**Files:**
- Modify: `run_v2.bat` (`:run_boards` section)
- Modify: `run_v2_social_post.bat` (preview Python path)

**Step 1: Fix run_v2.bat :run_boards section**

The `:run_boards` section (around line 69) does `cd job_finder` to run spiders but then calls Python scripts from wrong directory. Fix:

```batch
:run_boards
cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder
echo.
echo Running Job Board spiders (4)...
echo ============================================
if not exist output\by_source mkdir output\by_source

echo [1/4] Wuzzuf (Egypt)...
scrapy crawl wuzzuf_jobs -o output/by_source/wuzzuf.json 2>&1
echo Done!
echo.

echo [2/4] Indeed (Egypt + UAE)...
scrapy crawl indeed_jobs -o output/by_source/indeed.json 2>&1
echo Done!
echo.

echo [3/4] LinkedIn...
scrapy crawl linkedin_jobs -o output/by_source/linkedin.json 2>&1
echo Done!
echo.

echo [4/4] Freelance (Mostaql, Khamsat, Upwork)...
scrapy crawl freelance_jobs -o output/by_source/freelance.json 2>&1
echo Done!
echo.

echo Job board scraping complete!
cd /d "%~dp0"
python categorize_jobs.py
python json_to_excel_v2.py
pause
goto end
```

The key fix: `cd /d "%~dp0"` returns to script root before calling Python scripts.

**Step 2: Fix run_v2_social_post.bat preview**

Replace the fragile `sys.path.insert` hack with proper `cd` before calling Python:

```batch
:preview
echo.
echo Generating post previews...
echo ============================================
cd /d "%~dp0"
python -c "
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), 'job_finder'))
from job_finder.social_media import FacebookPoster, LinkedInPoster, TwitterPoster
...
```

Actually, the cleaner fix: batch already activates venv at top. Just ensure we call Python from root:

```batch
cd /d "%~dp0"
python -c "
import sys
sys.path.insert(0, 'job_finder')
...
```

**Step 3: Commit**

```bash
git add run_v2.bat run_v2_social_post.bat
git commit -m "fix: correct directory navigation in batch files"
```

---

## Task 7: Fix Debug HTML Output Paths

**Why:** `indeed_spider.py:88` and `linkedin_spider.py:98` write debug HTML to CWD (inside `job_finder/`), which pollutes the project and those files can leak session data.

**Files:**
- Modify: `job_finder/job_finder/spiders/indeed_spider.py:88`
- Modify: `job_finder/job_finder/spiders/linkedin_spider.py:98`

**Step 1: Fix debug output to go into output/ directory**

In `indeed_spider.py`, replace line 88:

```python
# BEFORE:
with open(f'indeed_debug_{response.meta.get("keyword", "unknown")}.html', 'wb') as f:

# AFTER:
import os
debug_dir = os.path.join('output', 'debug')
os.makedirs(debug_dir, exist_ok=True)
with open(os.path.join(debug_dir, f'indeed_debug_{response.meta.get("keyword", "unknown")}.html'), 'wb') as f:
```

In `linkedin_spider.py`, replace line 98:

```python
# BEFORE:
with open(f'linkedin_debug_{response.meta.get("keyword", "unknown")}.html', 'wb') as f:

# AFTER:
import os
debug_dir = os.path.join('output', 'debug')
os.makedirs(debug_dir, exist_ok=True)
with open(os.path.join(debug_dir, f'linkedin_debug_{response.meta.get("keyword", "unknown")}.html'), 'wb') as f:
```

Also update `.gitignore` to ignore `output/debug/`:

```
job_finder/output/
```

This is already covered since `job_finder/output/` is in `.gitignore`.

**Step 2: Commit**

```bash
git add job_finder/job_finder/spiders/indeed_spider.py job_finder/job_finder/spiders/linkedin_spider.py
git commit -m "fix: move debug HTML output into output/debug/ directory"
```

---

## Task 8: Fix requirements.txt

**Why:** Missing `requests` which is imported by middlewares.py (line 55 of linkedin_poster, line 177 of the posters). Fresh installs will crash.

**Files:**
- Modify: `job_finder/requirements.txt`

**Step 1: Update requirements**

```
# Job Finder v2.0 - Requirements
# 10 Spiders + Social Media + Categories

# Core Scrapy framework
scrapy>=2.11.0

# For Brotli compression (required for many modern sites)
brotli>=1.2.0

# For Excel export
pandas>=2.0.0
openpyxl>=3.1.0

# For async operations
twisted>=23.8.0

# For better item handling
itemadapter>=0.8.0

# For social media poster API calls
requests>=2.31.0

# Optional: Playwright for JS-heavy sites
# pip install scrapy-playwright playwright && playwright install chromium
# scrapy-playwright>=0.0.33
# playwright>=1.40.0

# Optional: Social media posting
# tweepy>=4.14.0        # Twitter/X API
# facebook-sdk>=3.1.0   # Facebook Graph API
```

**Step 2: Commit**

```bash
git add job_finder/requirements.txt
git commit -m "fix: add requests to requirements, clean up optional deps"
```

---

## Task 9: Final Integration Fix — run_v2_full_scrape.bat End-to-End

**Why:** This is the main script users will run. It must correctly: create dirs → run all 10 spiders → categorize (including social media) → export Excel (all 10 sources). Currently the categorize and export steps miss social media data.

**Files:**
- Verify: `run_v2_full_scrape.bat` (already updated, but verify the cd/path flow)

**Step 1: Verify the directory flow**

The batch file should:
1. `cd /d "%~dp0"` — go to script root
2. `call venv\Scripts\activate` — activate venv
3. `cd job_finder` — enter scrapy project
4. Run all 10 `scrapy crawl` commands with correct output paths
5. `cd /d "%~dp0"` — return to root (NOT `cd ..` which can fail)
6. `python categorize_jobs.py` — from root, where script expects to be
7. `python json_to_excel_v2.py` — from root

Fix `run_v2_full_scrape.bat` Phase 4 section. Replace `cd ..` with `cd /d "%~dp0"`:

```batch
echo Categorizing all jobs...
cd /d "%~dp0"
python categorize_jobs.py
echo.

echo Converting to Excel with categories...
python json_to_excel_v2.py
echo.
```

**Step 2: Apply same fix to run_v2_social_search.bat**

Replace `cd ..` with `cd /d "%~dp0"` in the FINISH section.

**Step 3: Commit**

```bash
git add run_v2_full_scrape.bat run_v2_social_search.bat
git commit -m "fix: use absolute path navigation in batch scripts"
```

---

## Task 10: Smoke Test the Full Pipeline

**Why:** Verify end-to-end flow works after all fixes.

**Step 1: Verify spider names are discoverable**

```bash
cd job_finder
scrapy list
```

Expected output (all 10 + playwright):
```
career_pages
facebook_jobs
freelance_jobs
indeed_jobs
linkedin_jobs
playwright_jobs
reddit_jobs
remote_jobs
telegram_jobs
twitter_jobs
wuzzuf_jobs
```

**Step 2: Test one spider outputs correctly**

```bash
scrapy crawl reddit_jobs -o output/social_media/reddit_test.json -s CLOSESPIDER_ITEMCOUNT=3 -s LOG_LEVEL=WARNING
```

Check the JSON output has expected fields (title, company, location, type, link, source).

**Step 3: Test categorize_jobs.py picks up social media output**

```bash
cd /d "%~dp0"
python categorize_jobs.py
```

Verify output mentions social media source files being loaded.

**Step 4: Test json_to_excel_v2.py creates all sheets**

```bash
python json_to_excel_v2.py
```

Verify output mentions Reddit, Twitter, Facebook, Telegram sheets.

**Step 5: Commit all remaining changes**

```bash
git add -A
git commit -m "feat: complete v2.0 system overhaul - 10 spiders end-to-end"
```

---

## Summary of Changes

| Task | Files Changed | Bug Fixed |
|------|--------------|-----------|
| 1 | cv_config.py + 10 spiders | CV keywords inconsistency |
| 2 | items.py | Empty schema |
| 3 | pipelines.py + settings.py | No dedup/validation |
| 4 | categorize_jobs.py | Social media sources ignored |
| 5 | json_to_excel_v2.py | Missing sheets + dead refs |
| 6 | run_v2.bat + run_v2_social_post.bat | Wrong directory for Python calls |
| 7 | indeed_spider.py + linkedin_spider.py | Debug HTML pollution |
| 8 | requirements.txt | Missing `requests` package |
| 9 | run_v2_full_scrape.bat + run_v2_social_search.bat | `cd ..` fragile navigation |
| 10 | (verification) | End-to-end smoke test |

### Data Flow After Fix

```
ALL 10 SPIDERS
    ↓
output/by_source/*.json  +  output/social_media/*.json
    ↓
categorize_jobs.py  (scans BOTH directories)
    ↓
output/by_category/*.json  +  output/by_region/*.json  +  all_jobs_categorized.json
    ↓
json_to_excel_v2.py  (10 source sheets + 4 category + 4 region + summary)
    ↓
all_jobs_v2.xlsx  (all data, all sources)
```
