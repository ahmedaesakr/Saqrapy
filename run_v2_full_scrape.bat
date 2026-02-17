@echo off
REM ============================================
REM Job Finder v2.0 - Full Scrape with Categories
REM Runs all spiders and categorizes results
REM ============================================

cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder

echo.
echo ============================================
echo  Job Finder v2.0 - Full Scrape Mode
echo ============================================
echo.
echo Features:
echo   [+] All job sources enabled
echo   [+] Auto-categorization (Remote/Freelance/Full-Time/Hybrid)
echo   [+] Region detection (Egypt/UAE/Europe/Global)
echo   [+] Brotli compression support
echo ============================================
echo.

REM Create output directories
if not exist output\by_source mkdir output\by_source
if not exist output\by_category mkdir output\by_category
if not exist output\by_region mkdir output\by_region

echo [1/6] Scraping Wuzzuf (Egypt)...
echo ----------------------------------------
scrapy crawl wuzzuf_jobs -o output/by_source/wuzzuf.json 2>&1
echo Done!
echo.

echo [2/6] Scraping Indeed (Egypt + UAE)...
echo ----------------------------------------
scrapy crawl indeed_jobs -o output/by_source/indeed.json 2>&1
echo Done!
echo.

echo [3/6] Scraping LinkedIn...
echo ----------------------------------------
scrapy crawl linkedin_jobs -o output/by_source/linkedin.json 2>&1
echo Done!
echo.

echo [4/6] Scraping Freelance Platforms (Mostaql, Khamsat, Upwork)...
echo ----------------------------------------
scrapy crawl freelance_jobs -o output/by_source/freelance.json 2>&1
echo Done!
echo.

echo [5/6] Scraping Company Career Pages...
echo ----------------------------------------
scrapy crawl career_pages -o output/by_source/career_pages.json 2>&1
echo Done!
echo.

echo [6/6] Scraping Remote Jobs (UAE/Europe)...
echo ----------------------------------------
scrapy crawl remote_jobs -o output/by_source/remote_jobs.json 2>&1
echo Done!
echo.

echo ============================================
echo  All scraping complete!
echo ============================================
echo.
echo Output files in: job_finder\output\by_source\
echo   - wuzzuf.json
echo   - indeed.json
echo   - linkedin.json
echo   - freelance.json
echo   - career_pages.json
echo   - remote_jobs.json
echo ============================================
echo.

echo Categorizing jobs...
cd ..
python categorize_jobs.py
echo.

echo Converting to Excel with categories...
python json_to_excel_v2.py
echo.

echo ============================================
echo  V2 SCRAPE COMPLETE!
echo ============================================
echo  Check: job_finder\all_jobs_v2.xlsx
echo ============================================

pause
