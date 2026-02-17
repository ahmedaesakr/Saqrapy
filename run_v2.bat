@echo off
REM ============================================
REM Job Finder v2.0 - Master Runner
REM All 10 spiders + Social Media + Categories
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

echo.
echo  ========================================================
echo   ___  ____  ____    _____ ___ _   _ ____  _____ ____
echo  ^|_  ^|/ __ \^| __ )  ^|  ___)^|_ _^| \ ^| ^|  _ \^| ____^|  _ \
echo    ^| ^| ^|  ^| ^|  _ \  ^| ^|_   ^| ^|^|  \^| ^| ^| ^| ^|  _^| ^| ^|_) ^|
echo    ^| ^| ^|__^| ^| ^|_) ^| ^|  _^|  ^| ^|^| ^|\  ^| ^|_^| ^| ^|___^|  _ ^<
echo  ^|___)\____/^|____/  ^|_^|   ^|___^|_^| \_^|____/^|_____^|_^| \_\
echo.
echo                      VERSION 2.0
echo  ========================================================
echo.
echo  10 Spiders:
echo    Job Boards  : Wuzzuf, Indeed, LinkedIn, Freelance
echo    Direct      : Career Pages, Remote Jobs, Playwright
echo    Social Media: Reddit, Twitter/X, Facebook, Telegram
echo.
echo  Features:
echo    [+] Job Categories (Remote, Freelance, Full-Time, Hybrid)
echo    [+] Region Detection (Egypt, UAE, Europe, Global)
echo    [+] Social Media Job Search (4 platforms)
echo    [+] Social Media Posting (Facebook, LinkedIn, X)
echo    [+] Excel Export with Category Tabs
echo  ========================================================
echo.

echo Select an option:
echo.
echo   [1] Full Scrape - ALL 10 Spiders + Categorize + Excel
echo   [2] Job Boards Only (Wuzzuf, Indeed, LinkedIn, Freelance)
echo   [3] Remote Jobs Only
echo   [4] Freelance Jobs Only
echo   [5] By Region (Egypt/UAE/Europe)
echo   [6] Social Media Search (Reddit, Twitter, Facebook, Telegram)
echo   [7] Social Media Post (post results to FB, LinkedIn, X)
echo   [8] Playwright Spider (JS-heavy sites)
echo   [9] Convert JSON to Excel
echo   [0] Exit
echo.

set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto run_all
if "%choice%"=="2" goto run_boards
if "%choice%"=="3" goto run_remote
if "%choice%"=="4" goto run_freelance
if "%choice%"=="5" goto run_region
if "%choice%"=="6" goto run_social_search
if "%choice%"=="7" goto run_social_post
if "%choice%"=="8" goto run_playwright
if "%choice%"=="9" goto convert_excel
if "%choice%"=="0" goto end

echo Invalid choice. Please try again.
pause
goto end

:run_all
call "%~dp0run_v2_full_scrape.bat"
goto end

:run_boards
cd /d "%~dp0job_finder"
echo.
echo Running Job Board spiders (4)...
echo ============================================
if not exist output\by_source mkdir output\by_source

echo [1/4] Wuzzuf (Egypt)...
"%VENV_PY%" -m scrapy crawl wuzzuf_jobs -O output/by_source/wuzzuf.json 2>&1
echo Done!
echo.

echo [2/4] Indeed (Egypt + UAE)...
"%VENV_PY%" -m scrapy crawl indeed_jobs -O output/by_source/indeed.json 2>&1
echo Done!
echo.

echo [3/4] LinkedIn...
"%VENV_PY%" -m scrapy crawl linkedin_jobs -O output/by_source/linkedin.json 2>&1
echo Done!
echo.

echo [4/4] Freelance (Mostaql, Khamsat, Upwork)...
"%VENV_PY%" -m scrapy crawl freelance_jobs -O output/by_source/freelance.json 2>&1
echo Done!
echo.

echo Job board scraping complete!
cd /d "%~dp0"
"%VENV_PY%" categorize_jobs.py
"%VENV_PY%" json_to_excel_v2.py
pause
goto end

:run_remote
call "%~dp0run_v2_remote.bat"
goto end

:run_freelance
call "%~dp0run_v2_freelance.bat"
goto end

:run_region
call "%~dp0run_v2_by_region.bat"
goto end

:run_social_search
call "%~dp0run_v2_social_search.bat"
goto end

:run_social_post
call "%~dp0run_v2_social_post.bat"
goto end

:run_playwright
call "%~dp0run_playwright_spider.bat"
goto end

:convert_excel
cd /d "%~dp0"
"%VENV_PY%" json_to_excel_v2.py
pause
goto end

:end
echo.
echo Done!
