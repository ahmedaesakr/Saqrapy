@echo off
REM ============================================
REM Social Media Search: Reddit + Twitter + Facebook + Telegram
REM 4 spiders - find job posts on social platforms
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

for /f "tokens=*" %%a in ('powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set RUN_ID=%%a

echo.
echo ============================================
echo  SOCIAL MEDIA SEARCH - Run ID: %RUN_ID%
echo ============================================
echo  [1] Reddit     (r/forhire, r/designjobs, r/gameDevJobs...)
echo  [2] Twitter/X  (40+ job accounts via syndication)
echo  [3] Facebook   (Egypt/Saudi/Gulf groups)
echo  [4] Telegram   (Public job channels MENA/Remote)
echo ============================================
echo.

cd /d "%~dp0job_finder"
if not exist output\social_media mkdir output\social_media

echo [1/4] reddit_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl reddit_jobs -O output/social_media/reddit.json 2>&1
echo [1/4] DONE
echo.

echo [2/4] twitter_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl twitter_jobs -O output/social_media/twitter.json 2>&1
echo [2/4] DONE
echo.

echo [3/4] facebook_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl facebook_jobs -O output/social_media/facebook.json 2>&1
echo [3/4] DONE
echo.

echo [4/4] telegram_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl telegram_jobs -O output/social_media/telegram.json 2>&1
echo [4/4] DONE
echo.

echo ============================================
echo  SOCIAL SEARCH COMPLETE - Run ID: %RUN_ID%
echo ============================================

cd /d "%~dp0"
echo Categorizing + Excel export...
"%VENV_PY%" categorize_jobs.py
"%VENV_PY%" json_to_excel_v2.py

echo.
echo  Output: job_finder\all_jobs_v2_latest.xlsx
echo ============================================
pause
