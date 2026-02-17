@echo off
REM ============================================
REM Ahmed's Job Finder - Master Runner
REM 10 Spiders | Smart CV Filtering | Excel Export
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

for /f "tokens=*" %%a in ('powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set RUN_ID=%%a

:menu
echo.
echo  ========================================================
echo   ___  ____  ____    _____ ___ _   _ ____  _____ ____
echo  ^|_  ^|/ __ \^| __ )  ^|  ___)^|_ _^| \ ^| ^|  _ \^| ____^|  _ \
echo    ^| ^| ^|  ^| ^|  _ \  ^| ^|_   ^| ^|^|  \^| ^| ^| ^| ^|  _^| ^| ^|_) ^|
echo    ^| ^| ^|__^| ^| ^|_) ^| ^|  _^|  ^| ^|^| ^|\  ^| ^|_^| ^| ^|___^|  _ ^<
echo  ^|___)\____/^|____/  ^|_^|   ^|___^|_^| \_^|____/^|_____^|_^| \_\
echo.
echo                 Ahmed Sakr - CGI Artist
echo  ========================================================
echo  Run ID: %RUN_ID%
echo.
echo  10 Spiders:
echo    Job Boards   : Wuzzuf, Indeed, LinkedIn, Freelance
echo    Career Pages : 50+ MENA companies + Remote boards
echo    Social Media : Reddit, Twitter/X, Facebook, Telegram
echo.
echo  ========================================================
echo.
echo   [1] FULL SCRAPE      All 10 spiders + categorize + Excel
echo   [2] Job Boards        Wuzzuf, Indeed, LinkedIn, Freelance
echo   [3] Career Pages      50+ company sites + remote boards
echo   [4] Social Search     Reddit, Twitter, Facebook, Telegram
echo   [5] Social Post       Post results to FB/LinkedIn/X
echo   [6] Export Excel      Categorize + Excel (no scraping)
echo   [0] Exit
echo.
echo  ========================================================

set /p choice="  Select (0-6): "

if "%choice%"=="0" goto end
if "%choice%"=="1" goto full_scrape
if "%choice%"=="2" goto job_boards
if "%choice%"=="3" goto career_pages
if "%choice%"=="4" goto social_search
if "%choice%"=="5" goto social_post
if "%choice%"=="6" goto export

echo  Invalid choice.
pause
goto menu

:full_scrape
echo.
echo ============================================
echo  FULL SCRAPE - Run ID: %RUN_ID%
echo  All 10 spiders
echo ============================================
echo.

cd /d "%~dp0job_finder"
if not exist output\by_source mkdir output\by_source
if not exist output\social_media mkdir output\social_media
if not exist output\by_category mkdir output\by_category
if not exist output\by_region mkdir output\by_region
if not exist output\debug mkdir output\debug

REM Clean stale output
del /q output\by_source\*.json 2>nul
del /q output\social_media\*.json 2>nul

echo  PHASE 1: Job Boards (4 spiders)
echo ============================================

echo [1/10] wuzzuf_jobs
"%VENV_PY%" -m scrapy crawl wuzzuf_jobs -O output/by_source/wuzzuf.json 2>&1
echo [1/10] DONE
echo.

echo [2/10] indeed_jobs
"%VENV_PY%" -m scrapy crawl indeed_jobs -O output/by_source/indeed.json 2>&1
echo [2/10] DONE
echo.

echo [3/10] linkedin_jobs
"%VENV_PY%" -m scrapy crawl linkedin_jobs -O output/by_source/linkedin.json 2>&1
echo [3/10] DONE
echo.

echo [4/10] freelance_jobs
"%VENV_PY%" -m scrapy crawl freelance_jobs -O output/by_source/freelance.json 2>&1
echo [4/10] DONE
echo.

echo  PHASE 2: Career Pages (2 spiders)
echo ============================================

echo [5/10] career_pages
"%VENV_PY%" -m scrapy crawl career_pages -O output/by_source/career_pages.json 2>&1
echo [5/10] DONE
echo.

echo [6/10] remote_jobs
"%VENV_PY%" -m scrapy crawl remote_jobs -O output/by_source/remote_jobs.json 2>&1
echo [6/10] DONE
echo.

echo  PHASE 3: Social Media (4 spiders)
echo ============================================

echo [7/10] reddit_jobs
"%VENV_PY%" -m scrapy crawl reddit_jobs -O output/social_media/reddit.json 2>&1
echo [7/10] DONE
echo.

echo [8/10] twitter_jobs
"%VENV_PY%" -m scrapy crawl twitter_jobs -O output/social_media/twitter.json 2>&1
echo [8/10] DONE
echo.

echo [9/10] facebook_jobs
"%VENV_PY%" -m scrapy crawl facebook_jobs -O output/social_media/facebook.json 2>&1
echo [9/10] DONE
echo.

echo [10/10] telegram_jobs
"%VENV_PY%" -m scrapy crawl telegram_jobs -O output/social_media/telegram.json 2>&1
echo [10/10] DONE
echo.

echo  PHASE 4: Categorize + Excel + XML
echo ============================================

cd /d "%~dp0"
"%VENV_PY%" categorize_jobs.py
"%VENV_PY%" json_to_excel_v2.py
"%VENV_PY%" json_to_xml.py

echo.
echo ============================================
echo  FULL SCRAPE COMPLETE - Run ID: %RUN_ID%
echo ============================================
echo  Excel: job_finder\all_jobs_v2_latest.xlsx
echo  XML:   job_finder\all_jobs_latest.xml
echo ============================================
pause
goto end

:job_boards
call "%~dp0run_job_boards.bat"
goto end

:career_pages
call "%~dp0run_career_pages.bat"
goto end

:social_search
call "%~dp0run_social_search.bat"
goto end

:social_post
call "%~dp0run_social_post.bat"
goto end

:export
call "%~dp0run_export.bat"
goto end

:end
