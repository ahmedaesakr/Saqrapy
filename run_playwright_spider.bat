@echo off
REM Run Playwright Spider for JavaScript-Heavy Sites
REM Requires: pip install scrapy-playwright playwright
REM           playwright install chromium

cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder

echo ============================================
echo Playwright Spider - JavaScript Sites
echo ============================================
echo.
echo This spider uses a real browser to handle:
echo   - LinkedIn (JS-rendered)
echo   - Glassdoor (Dynamic content)  
echo   - Upwork (SPA)
echo ============================================
echo.

if exist output\playwright_jobs.json del output\playwright_jobs.json

echo Running Playwright spider (this may take a while)...
scrapy crawl playwright_jobs -o output\playwright_jobs.json

echo.
echo ============================================
echo Playwright scraping complete!
echo Output: output\playwright_jobs.json
echo ============================================

pause
