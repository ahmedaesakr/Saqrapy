@echo off
REM Job Finder - Run All Spiders
REM This script runs all spiders and saves results to separate JSON files

cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder

echo ============================================
echo Job Finder - Scraping All Sources
echo ============================================
echo.

REM Clean old output files
if exist output\nul rd /s /q output
mkdir output

echo [1/4] Scraping Wuzzuf + Indeed (Job Boards)...
scrapy crawl wuzzuf_jobs -o output\wuzzuf_indeed.json
scrapy crawl indeed_jobs -o output\wuzzuf_indeed.json
echo Done!
echo.

echo [2/4] Scraping LinkedIn...
scrapy crawl linkedin_jobs -o output\linkedin.json
echo Done!
echo.

echo [3/4] Scraping Freelance Platforms...
scrapy crawl freelance_jobs -o output\freelance.json
echo Done!
echo.

echo [4/4] Scraping Company Career Pages...
scrapy crawl career_pages -o output\career_pages.json
echo Done!
echo.

echo ============================================
echo All scraping complete!
echo.
echo Output files:
echo   - output\wuzzuf_indeed.json  (Job Boards)
echo   - output\linkedin.json       (LinkedIn)
echo   - output\freelance.json      (Freelance Projects)
echo   - output\career_pages.json   (Company Careers)
echo ============================================

pause
