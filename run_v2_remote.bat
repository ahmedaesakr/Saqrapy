@echo off
REM ============================================
REM Job Finder v2.0 - Remote Jobs Only
REM Focused scraping for remote positions
REM ============================================

cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder

echo.
echo ============================================
echo  Job Finder v2.0 - REMOTE JOBS MODE
echo ============================================
echo.
echo  Targeting:
echo    [+] Remote OK
echo    [+] We Work Remotely
echo    [+] Remote-First Companies
echo    [+] LinkedIn Remote Filter
echo    [+] Remote positions on Wuzzuf/Indeed
echo ============================================
echo.

REM Create output directory
if not exist output\by_category mkdir output\by_category

echo [1/3] Scraping Remote Job Boards + Company Pages...
echo ----------------------------------------
scrapy crawl remote_jobs -o output/by_category/remote_jobs_raw.json 2>&1
echo Done!
echo.

echo [2/3] Scraping LinkedIn (Remote Filter)...
echo ----------------------------------------
scrapy crawl linkedin_jobs -o output/by_category/linkedin_remote.json 2>&1
echo Done!
echo.

echo [3/3] Filtering for Remote positions only...
echo ----------------------------------------
cd ..
python -c "
from job_finder.categories import filter_remote_only, categorize_job
import json
import os

# Load all scraped jobs
files = [
    'job_finder/output/by_category/remote_jobs_raw.json',
    'job_finder/output/by_category/linkedin_remote.json',
]

all_jobs = []
for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read().replace('][', ',')
            try:
                jobs = json.loads(content)
                all_jobs.extend(jobs)
            except:
                pass

# Categorize and filter
categorized = [categorize_job(j) for j in all_jobs]
remote_only = filter_remote_only(categorized)

# Save
with open('job_finder/output/by_category/remote_jobs_final.json', 'w', encoding='utf-8') as f:
    json.dump(remote_only, f, indent=2, ensure_ascii=False)

print(f'Found {len(remote_only)} remote jobs!')
"
echo.

echo ============================================
echo  REMOTE JOBS SCRAPE COMPLETE!
echo ============================================
echo  Output: job_finder\output\by_category\remote_jobs_final.json
echo ============================================

pause
