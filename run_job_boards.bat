@echo off
REM ============================================
REM Job Boards: Wuzzuf + Indeed + LinkedIn + Freelance
REM 4 spiders - structured job board scraping
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

for /f "tokens=*" %%a in ('powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set RUN_ID=%%a

echo.
echo ============================================
echo  JOB BOARDS - Run ID: %RUN_ID%
echo ============================================
echo  [1] Wuzzuf       (Egypt)
echo  [2] Indeed        (Egypt, UAE, Saudi, Remote)
echo  [3] LinkedIn      (Egypt, Saudi, UAE, Qatar, Remote)
echo  [4] Freelance     (Mostaql, Khamsat, Upwork)
echo ============================================
echo.

cd /d "%~dp0job_finder"
if not exist output\by_source mkdir output\by_source

echo [1/4] wuzzuf_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl wuzzuf_jobs -O output/by_source/wuzzuf.json 2>&1
echo [1/4] DONE
echo.

echo [2/4] indeed_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl indeed_jobs -O output/by_source/indeed.json 2>&1
echo [2/4] DONE
echo.

echo [3/4] linkedin_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl linkedin_jobs -O output/by_source/linkedin.json 2>&1
echo [3/4] DONE
echo.

echo [4/4] freelance_jobs
echo ----------------------------------------
"%VENV_PY%" -m scrapy crawl freelance_jobs -O output/by_source/freelance.json 2>&1
echo [4/4] DONE
echo.

echo ============================================
echo  JOB BOARDS COMPLETE - Run ID: %RUN_ID%
echo ============================================

cd /d "%~dp0"
echo Categorizing + Excel export...
"%VENV_PY%" categorize_jobs.py
"%VENV_PY%" json_to_excel_v2.py

echo.
echo  Output: job_finder\all_jobs_v2_latest.xlsx
echo ============================================
pause
