@echo off
REM ============================================
REM Job Finder v2.0 - Social Media Job Search
REM Searches social media platforms for job posts
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

echo.
echo ============================================
echo  Job Finder v2.0 - Social Media Search
echo ============================================
echo.
echo Targets:
echo   [1] Reddit     (r/forhire, r/designjobs, r/gameDevJobs...)
echo   [2] Twitter/X  (API v2 + Nitter + DuckDuckGo fallback)
echo   [3] Facebook   (Groups + Pages via DuckDuckGo search)
echo   [4] Telegram   (Public channels - job channels MENA/Remote)
echo.
echo CV Keywords: Designer, 3D, CGI, UI/UX, Motion, AI, Blender, Unreal
echo ============================================
echo.

REM Create output directories
cd /d "%~dp0job_finder"
if not exist output\social_media mkdir output\social_media

echo Select search mode:
echo   [1] ALL social media platforms (recommended)
echo   [2] Reddit only
echo   [3] Twitter/X only
echo   [4] Facebook only
echo   [5] Telegram only
echo.
set /p CHOICE="Enter choice (1-5): "

if "%CHOICE%"=="1" goto ALL
if "%CHOICE%"=="2" goto REDDIT
if "%CHOICE%"=="3" goto TWITTER
if "%CHOICE%"=="4" goto FACEBOOK
if "%CHOICE%"=="5" goto TELEGRAM
goto ALL

:ALL
echo.
echo Running ALL social media search spiders...
echo ============================================
echo.

echo [1/4] Searching Reddit...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl reddit_jobs -O output/social_media/reddit.json 2>&1
echo Done!
echo.

echo [2/4] Searching Twitter/X...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl twitter_jobs -O output/social_media/twitter.json 2>&1
echo Done!
echo.

echo [3/4] Searching Facebook Groups...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl facebook_jobs -O output/social_media/facebook.json 2>&1
echo Done!
echo.

echo [4/4] Searching Telegram Channels...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl telegram_jobs -O output/social_media/telegram.json 2>&1
echo Done!
echo.

goto FINISH

:REDDIT
echo.
echo [1/1] Searching Reddit...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl reddit_jobs -O output/social_media/reddit.json 2>&1
echo Done!
goto FINISH

:TWITTER
echo.
echo [1/1] Searching Twitter/X...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl twitter_jobs -O output/social_media/twitter.json 2>&1
echo Done!
goto FINISH

:FACEBOOK
echo.
echo [1/1] Searching Facebook Groups...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl facebook_jobs -O output/social_media/facebook.json 2>&1
echo Done!
goto FINISH

:TELEGRAM
echo.
echo [1/1] Searching Telegram Channels...
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl telegram_jobs -O output/social_media/telegram.json 2>&1
echo Done!
goto FINISH

:FINISH
echo.
echo ============================================
echo  Social Media Search Complete!
echo ============================================
echo.

cd /d "%~dp0"
echo Categorizing all jobs (including social media)...
"%VENV_PY%" categorize_jobs.py
echo.

echo Converting to Excel...
"%VENV_PY%" json_to_excel_v2.py
echo.

echo ============================================
echo  SOCIAL MEDIA SEARCH COMPLETE!
echo ============================================
echo  Check: job_finder\output\social_media\
echo  Excel: job_finder\all_jobs_v2.xlsx
echo ============================================

pause
