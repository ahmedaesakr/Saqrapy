@echo off
REM ============================================
REM Export: Categorize all JSON + Generate Excel
REM No scraping - just processes existing output
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

echo.
echo ============================================
echo  EXPORT - Categorize + Excel
echo ============================================
echo.

echo Categorizing all jobs...
"%VENV_PY%" categorize_jobs.py
echo.

echo Converting to Excel...
"%VENV_PY%" json_to_excel_v2.py
echo.

echo ============================================
echo  EXPORT COMPLETE
echo ============================================
echo  Output: job_finder\all_jobs_v2_latest.xlsx
echo ============================================
pause
