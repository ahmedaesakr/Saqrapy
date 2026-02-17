@echo off
REM Run Playwright Spider for JavaScript-Heavy Sites
REM Requires: pip install scrapy-playwright playwright
REM           playwright install chromium

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe
cd /d "%~dp0job_finder"

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

if not exist output\by_source mkdir output\by_source

echo Running Playwright spider (this may take a while)...
"%VENV_PY%" -m scrapy crawl playwright_jobs -O output/by_source/playwright_jobs.json 2>&1

echo.
echo ============================================
echo Playwright scraping complete!
echo Output: output\by_source\playwright_jobs.json
echo ============================================

pause
