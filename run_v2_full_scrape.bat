@echo off
REM ============================================
REM Job Finder v2.0 - Full Scrape (All 10 Spiders)
REM Job Boards + Career Pages + Social Media Search
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

echo.
echo ============================================
echo  Job Finder v2.0 - FULL SCRAPE MODE
echo ============================================
echo.
echo  10 Spiders:
echo    [+] Wuzzuf          (Egypt job board)
echo    [+] Indeed           (Egypt + UAE)
echo    [+] LinkedIn         (Global)
echo    [+] Freelance        (Mostaql, Khamsat, Upwork)
echo    [+] Career Pages     (Direct company sites)
echo    [+] Remote Jobs      (UAE/Europe companies)
echo    [+] Reddit           (r/forhire, r/designjobs...)
echo    [+] Twitter/X        (Nitter + DuckDuckGo)
echo    [+] Facebook         (Groups via DuckDuckGo)
echo    [+] Telegram         (Public job channels)
echo.
echo ============================================
echo.

REM Create output directories
cd /d "%~dp0job_finder"
if not exist output\by_source mkdir output\by_source
if not exist output\by_category mkdir output\by_category
if not exist output\by_region mkdir output\by_region
if not exist output\social_media mkdir output\social_media
if not exist output\debug mkdir output\debug

REM Clean stale output to avoid JSON append corruption
echo Cleaning old output files...
del /q output\by_source\*.json 2>nul
del /q output\social_media\*.json 2>nul
echo Done.
echo.

echo ============================================
echo  PHASE 1: Job Boards (4 spiders)
echo ============================================
echo.

echo [1/10] Scraping Wuzzuf (Egypt)...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl wuzzuf_jobs -O output/by_source/wuzzuf.json 2>&1
echo Done!
echo.

echo [2/10] Scraping Indeed (Egypt + UAE)...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl indeed_jobs -O output/by_source/indeed.json 2>&1
echo Done!
echo.

echo [3/10] Scraping LinkedIn...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl linkedin_jobs -O output/by_source/linkedin.json 2>&1
echo Done!
echo.

echo [4/10] Scraping Freelance Platforms...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl freelance_jobs -O output/by_source/freelance.json 2>&1
echo Done!
echo.

echo ============================================
echo  PHASE 2: Direct Sources (2 spiders)
echo ============================================
echo.

echo [5/10] Scraping Company Career Pages...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl career_pages -O output/by_source/career_pages.json 2>&1
echo Done!
echo.

echo [6/10] Scraping Remote Jobs (UAE/Europe)...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl remote_jobs -O output/by_source/remote_jobs.json 2>&1
echo Done!
echo.

echo ============================================
echo  PHASE 3: Social Media Search (4 spiders)
echo ============================================
echo.

echo [7/10] Searching Reddit...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl reddit_jobs -O output/social_media/reddit.json 2>&1
echo Done!
echo.

echo [8/10] Searching Twitter/X...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl twitter_jobs -O output/social_media/twitter.json 2>&1
echo Done!
echo.

echo [9/10] Searching Facebook Groups...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl facebook_jobs -O output/social_media/facebook.json 2>&1
echo Done!
echo.

echo [10/10] Searching Telegram Channels...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl telegram_jobs -O output/social_media/telegram.json 2>&1
echo Done!
echo.

echo ============================================
echo  All 10 spiders complete!
echo ============================================
echo.

echo ============================================
echo  PHASE 4: Categorize + Excel Export
echo ============================================
echo.

cd /d "%~dp0"
echo Categorizing all jobs...
"%VENV_PY%" categorize_jobs.py
echo.

echo Converting to Excel with categories...
"%VENV_PY%" json_to_excel_v2.py
echo.

echo ============================================
echo  FULL SCRAPE COMPLETE!
echo ============================================
echo  Excel: job_finder\all_jobs_v2.xlsx
echo  JSON:  job_finder\output\
echo ============================================

pause
