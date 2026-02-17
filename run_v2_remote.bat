@echo off
REM ============================================
REM Job Finder v2.0 - Remote Jobs Only
REM Focused scraping for remote positions
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

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
cd /d "%~dp0job_finder"
if not exist output\by_category mkdir output\by_category

echo [1/3] Scraping Remote Job Boards + Company Pages...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl remote_jobs -O output/by_category/remote_jobs_raw.json 2>&1
echo Done!
echo.

echo [2/3] Scraping LinkedIn (Remote Filter)...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl linkedin_jobs -O output/by_category/linkedin_remote.json 2>&1
echo Done!
echo.

echo [3/3] Filtering for Remote positions only...
echo ----------------------------------------
cd /d "%~dp0"
"%VENV_PY%" -c "
from job_finder.categories import filter_remote_only, categorize_job
import json, os

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
                all_jobs.extend(json.loads(content))
            except: pass

categorized = [categorize_job(j) for j in all_jobs]
remote_only = filter_remote_only(categorized)

os.makedirs('job_finder/output/by_category', exist_ok=True)
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
