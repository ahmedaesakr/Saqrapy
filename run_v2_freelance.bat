@echo off
REM ============================================
REM Job Finder v2.0 - Freelance Jobs Only
REM Focused scraping for freelance/contract gigs
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

echo.
echo ============================================
echo  Job Finder v2.0 - FREELANCE MODE
echo ============================================
echo.
echo  Platforms:
echo    [+] Mostaql (Arabic)
echo    [+] Khamsat (Arabic)
echo    [+] Upwork
echo    [+] Contract positions on job boards
echo ============================================
echo.

REM Create output directory
cd /d "%~dp0job_finder"
if not exist output\by_category mkdir output\by_category

echo [1/2] Scraping Freelance Platforms...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl freelance_jobs -O output/by_category/freelance_raw.json 2>&1
echo Done!
echo.

echo [2/2] Categorizing and filtering freelance jobs...
echo ----------------------------------------
cd /d "%~dp0"
"%VENV_PY%" -c "
from job_finder.categories import filter_by_category, categorize_job, JobType
import json, os

filepath = 'job_finder/output/by_category/freelance_raw.json'
all_jobs = []
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as fp:
        content = fp.read().replace('][', ',')
        try:
            all_jobs = json.loads(content)
        except: pass

categorized = [categorize_job(j) for j in all_jobs]
freelance_only = filter_by_category(categorized, JobType.FREELANCE)

contract_jobs = [j for j in categorized if 'contract' in j.get('type', '').lower()]
freelance_only.extend(contract_jobs)

seen = set()
unique = []
for j in freelance_only:
    if j.get('link') not in seen:
        seen.add(j.get('link'))
        unique.append(j)

os.makedirs('job_finder/output/by_category', exist_ok=True)
with open('job_finder/output/by_category/freelance_final.json', 'w', encoding='utf-8') as f:
    json.dump(unique, f, indent=2, ensure_ascii=False)
print(f'Found {len(unique)} freelance opportunities!')
"
echo.

echo ============================================
echo  FREELANCE SCRAPE COMPLETE!
echo ============================================
echo  Output: job_finder\output\by_category\freelance_final.json
echo ============================================

pause
