@echo off
REM ============================================
REM Export: Categorize all JSON + Generate Excel + XML
REM No scraping - just processes existing output
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

echo.
echo ============================================
echo  EXPORT - Categorize + Excel + XML
echo ============================================
echo.

echo Categorizing all jobs...
"%VENV_PY%" categorize_jobs.py
echo.

echo Converting to Excel...
"%VENV_PY%" json_to_excel_v2.py
echo.

echo Converting to XML...
"%VENV_PY%" json_to_xml.py
echo.

echo ============================================
echo  EXPORT COMPLETE
echo ============================================
echo  Excel: job_finder\all_jobs_v2_latest.xlsx
echo  XML:   job_finder\all_jobs_latest.xml
echo ============================================
pause
