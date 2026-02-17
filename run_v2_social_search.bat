@echo off
REM ============================================
REM Job Finder v2.0 - Social Media Job Search
REM Searches social media platforms for job posts
REM ============================================

cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder

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
if not exist output\by_source mkdir output\by_source
if not exist output\by_category mkdir output\by_category
if not exist output\by_region mkdir output\by_region
if not exist output\social_media mkdir output\social_media

echo Select search mode:
echo   [1] ALL social media platforms (recommended)
echo   [2] Reddit only
echo   [3] Twitter/X only
echo   [4] Facebook only
echo   [5] Telegram only
echo   [6] Custom selection
echo.
set /p CHOICE="Enter choice (1-6): "

if "%CHOICE%"=="1" goto ALL
if "%CHOICE%"=="2" goto REDDIT
if "%CHOICE%"=="3" goto TWITTER
if "%CHOICE%"=="4" goto FACEBOOK
if "%CHOICE%"=="5" goto TELEGRAM
if "%CHOICE%"=="6" goto CUSTOM
goto ALL

:ALL
echo.
echo Running ALL social media search spiders...
echo ============================================
echo.

echo [1/4] Searching Reddit...
echo ----------------------------------------
scrapy crawl reddit_jobs -o output/social_media/reddit.json 2>&1
echo Done!
echo.

echo [2/4] Searching Twitter/X...
echo ----------------------------------------
scrapy crawl twitter_jobs -o output/social_media/twitter.json 2>&1
echo Done!
echo.

echo [3/4] Searching Facebook Groups...
echo ----------------------------------------
scrapy crawl facebook_jobs -o output/social_media/facebook.json 2>&1
echo Done!
echo.

echo [4/4] Searching Telegram Channels...
echo ----------------------------------------
scrapy crawl telegram_jobs -o output/social_media/telegram.json 2>&1
echo Done!
echo.

goto FINISH

:REDDIT
echo.
echo [1/1] Searching Reddit...
echo ----------------------------------------
scrapy crawl reddit_jobs -o output/social_media/reddit.json 2>&1
echo Done!
goto FINISH

:TWITTER
echo.
echo [1/1] Searching Twitter/X...
echo ----------------------------------------
REM Optional: Set bearer token for API v2 access
REM set TWITTER_BEARER_TOKEN=your_token_here
REM scrapy crawl twitter_jobs -a bearer_token=%TWITTER_BEARER_TOKEN% -o output/social_media/twitter.json 2>&1
scrapy crawl twitter_jobs -o output/social_media/twitter.json 2>&1
echo Done!
goto FINISH

:FACEBOOK
echo.
echo [1/1] Searching Facebook Groups...
echo ----------------------------------------
scrapy crawl facebook_jobs -o output/social_media/facebook.json 2>&1
echo Done!
goto FINISH

:TELEGRAM
echo.
echo [1/1] Searching Telegram Channels...
echo ----------------------------------------
scrapy crawl telegram_jobs -o output/social_media/telegram.json 2>&1
echo Done!
goto FINISH

:CUSTOM
echo.
echo Select platforms (Y/N for each):
set /p DO_REDDIT="  Reddit? (Y/N): "
set /p DO_TWITTER="  Twitter/X? (Y/N): "
set /p DO_FACEBOOK="  Facebook? (Y/N): "
set /p DO_TELEGRAM="  Telegram? (Y/N): "
echo.

set STEP=0
set TOTAL=0

if /i "%DO_REDDIT%"=="Y" set /a TOTAL+=1
if /i "%DO_TWITTER%"=="Y" set /a TOTAL+=1
if /i "%DO_FACEBOOK%"=="Y" set /a TOTAL+=1
if /i "%DO_TELEGRAM%"=="Y" set /a TOTAL+=1

if /i "%DO_REDDIT%"=="Y" (
    set /a STEP+=1
    echo [%STEP%/%TOTAL%] Searching Reddit...
    scrapy crawl reddit_jobs -o output/social_media/reddit.json 2>&1
    echo Done!
    echo.
)

if /i "%DO_TWITTER%"=="Y" (
    set /a STEP+=1
    echo [%STEP%/%TOTAL%] Searching Twitter/X...
    scrapy crawl twitter_jobs -o output/social_media/twitter.json 2>&1
    echo Done!
    echo.
)

if /i "%DO_FACEBOOK%"=="Y" (
    set /a STEP+=1
    echo [%STEP%/%TOTAL%] Searching Facebook Groups...
    scrapy crawl facebook_jobs -o output/social_media/facebook.json 2>&1
    echo Done!
    echo.
)

if /i "%DO_TELEGRAM%"=="Y" (
    set /a STEP+=1
    echo [%STEP%/%TOTAL%] Searching Telegram Channels...
    scrapy crawl telegram_jobs -o output/social_media/telegram.json 2>&1
    echo Done!
    echo.
)

goto FINISH

:FINISH
echo.
echo ============================================
echo  Social Media Search Complete!
echo ============================================
echo.
echo Output files in: job_finder\output\social_media\
echo   - reddit.json      (Reddit job subreddits)
echo   - twitter.json     (Twitter/X job tweets)
echo   - facebook.json    (Facebook group posts)
echo   - telegram.json    (Telegram channel posts)
echo ============================================
echo.

echo Categorizing all jobs (including social media)...
cd ..
python categorize_jobs.py
echo.

echo Converting to Excel...
python json_to_excel_v2.py
echo.

echo ============================================
echo  SOCIAL MEDIA SEARCH COMPLETE!
echo ============================================
echo  Check: job_finder\output\social_media\
echo  Excel: job_finder\all_jobs_v2.xlsx
echo ============================================

pause
