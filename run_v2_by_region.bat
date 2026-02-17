@echo off
REM ============================================
REM Job Finder v2.0 - Jobs by Region
REM Scrape and categorize by geographic location
REM ============================================

cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder

echo.
echo ============================================
echo  Job Finder v2.0 - REGION MODE
echo ============================================
echo.
echo  Available Regions:
echo    [1] Egypt (Wuzzuf, Indeed EG, Cairo jobs)
echo    [2] UAE (Indeed AE, Dubai, Abu Dhabi)
echo    [3] Europe (Germany, UK, Netherlands, etc.)
echo    [4] All Regions
echo ============================================
echo.

set /p region="Select region (1-4): "

if "%region%"=="1" goto egypt
if "%region%"=="2" goto uae
if "%region%"=="3" goto europe
if "%region%"=="4" goto all_regions

echo Invalid choice.
pause
goto end

:egypt
echo.
echo Scraping jobs in EGYPT...
echo ----------------------------------------
if not exist output\by_region mkdir output\by_region
scrapy crawl wuzzuf_jobs -o output/by_region/egypt_wuzzuf.json 2>&1
scrapy crawl indeed_jobs -a location=Egypt -o output/by_region/egypt_indeed.json 2>&1
echo.
echo Combining Egypt jobs...
cd ..
python -c "
from job_finder.categories import filter_by_region, categorize_job, Region
import json, os, glob

jobs = []
for f in glob.glob('job_finder/output/by_region/egypt_*.json'):
    with open(f, 'r', encoding='utf-8') as fp:
        try:
            content = fp.read().replace('][', ',')
            jobs.extend(json.loads(content))
        except: pass

categorized = [categorize_job(j) for j in jobs]
egypt = filter_by_region(categorized, Region.EGYPT)
with open('job_finder/output/by_region/egypt_final.json', 'w', encoding='utf-8') as f:
    json.dump(egypt, f, indent=2, ensure_ascii=False)
print(f'Found {len(egypt)} jobs in Egypt!')
"
goto end

:uae
echo.
echo Scraping jobs in UAE...
echo ----------------------------------------
if not exist output\by_region mkdir output\by_region
scrapy crawl indeed_jobs -a location=UAE -o output/by_region/uae_indeed.json 2>&1
scrapy crawl remote_jobs -o output/by_region/uae_remote.json 2>&1
echo.
echo Combining UAE jobs...
cd ..
python -c "
from job_finder.categories import filter_by_region, categorize_job, Region
import json, os, glob

jobs = []
for f in glob.glob('job_finder/output/by_region/uae_*.json'):
    with open(f, 'r', encoding='utf-8') as fp:
        try:
            content = fp.read().replace('][', ',')
            jobs.extend(json.loads(content))
        except: pass

categorized = [categorize_job(j) for j in jobs]
uae = filter_by_region(categorized, Region.UAE)
with open('job_finder/output/by_region/uae_final.json', 'w', encoding='utf-8') as f:
    json.dump(uae, f, indent=2, ensure_ascii=False)
print(f'Found {len(uae)} jobs in UAE!')
"
goto end

:europe
echo.
echo Scraping jobs in EUROPE...
echo ----------------------------------------
if not exist output\by_region mkdir output\by_region
scrapy crawl remote_jobs -o output/by_region/europe_remote.json 2>&1
scrapy crawl career_pages -o output/by_region/europe_careers.json 2>&1
echo.
echo Combining Europe jobs...
cd ..
python -c "
from job_finder.categories import filter_by_region, categorize_job, Region
import json, os, glob

jobs = []
for f in glob.glob('job_finder/output/by_region/europe_*.json'):
    with open(f, 'r', encoding='utf-8') as fp:
        try:
            content = fp.read().replace('][', ',')
            jobs.extend(json.loads(content))
        except: pass

categorized = [categorize_job(j) for j in jobs]
europe = filter_by_region(categorized, Region.EUROPE)
with open('job_finder/output/by_region/europe_final.json', 'w', encoding='utf-8') as f:
    json.dump(europe, f, indent=2, ensure_ascii=False)
print(f'Found {len(europe)} jobs in Europe!')
"
goto end

:all_regions
echo Running all regions...
call :egypt
call :uae
call :europe
goto end

:end
echo.
echo ============================================
echo  REGION SCRAPE COMPLETE!
echo ============================================
echo  Check: job_finder\output\by_region\
echo ============================================
pause
