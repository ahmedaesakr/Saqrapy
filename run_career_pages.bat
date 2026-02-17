@echo off
REM ============================================
REM Career & Remote Pages: Direct company scraping
REM 2 spiders - 50+ MENA companies + remote boards
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

for /f "tokens=*" %%a in ('powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set RUN_ID=%%a

echo.
echo ============================================
echo  CAREER PAGES - Run ID: %RUN_ID%
echo ============================================
echo  [1] Career Pages  (50+ Egypt/Saudi/UAE/Qatar companies)
echo  [2] Remote Jobs    (Saudi/UAE/Europe + remote boards)
echo ============================================
echo.

cd /d "%~dp0job_finder"
if not exist output\by_source mkdir output\by_source

echo [1/2] career_pages
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl career_pages -O output/by_source/career_pages.json 2>&1
echo [1/2] DONE
echo.

echo [2/2] remote_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl remote_jobs -O output/by_source/remote_jobs.json 2>&1
echo [2/2] DONE
echo.

echo ============================================
echo  CAREER PAGES COMPLETE - Run ID: %RUN_ID%
echo ============================================

cd /d "%~dp0"
echo Categorizing + Excel export...
"%VENV_PY%" categorize_jobs.py
"%VENV_PY%" json_to_excel_v2.py

echo.
echo  Output: job_finder\all_jobs_v2_latest.xlsx
echo ============================================
pause
