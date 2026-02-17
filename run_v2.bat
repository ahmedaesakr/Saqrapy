@echo off
REM ============================================
REM Job Finder v2.0 - Master Runner
REM Enhanced with Categories and Social Media
REM ============================================

cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder

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
echo  New Features:
echo    [+] Job Categories (Remote, Freelance, Full-Time, Hybrid)
echo    [+] Region Detection (Egypt, UAE, Europe, Global)
echo    [+] Social Media Posting (Facebook, LinkedIn, X)
echo    [+] Enhanced Excel Export with Category Tabs
echo  ========================================================
echo.

echo Select an option:
echo.
echo   [1] Run ALL Spiders (Full Scrape with Categories)
echo   [2] Run Remote Jobs Only
echo   [3] Run Freelance Jobs Only
echo   [4] Run by Region (Egypt/UAE/Europe)
echo   [5] Convert JSON to Excel (with Categories)
echo   [6] Post to Social Media
echo   [7] Run Everything (Scrape + Categorize + Post)
echo   [0] Exit
echo.

set /p choice="Enter your choice (0-7): "

if "%choice%"=="1" goto run_all
if "%choice%"=="2" goto run_remote
if "%choice%"=="3" goto run_freelance
if "%choice%"=="4" goto run_region
if "%choice%"=="5" goto convert_excel
if "%choice%"=="6" goto social_media
if "%choice%"=="7" goto run_everything
if "%choice%"=="0" goto end

echo Invalid choice. Please try again.
pause
goto end

:run_all
call "%~dp0run_v2_full_scrape.bat"
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

:convert_excel
cd ..
python json_to_excel_v2.py
cd job_finder
pause
goto end

:social_media
call "%~dp0run_v2_social_post.bat"
goto end

:run_everything
call "%~dp0run_v2_full_scrape.bat"
cd ..
python json_to_excel_v2.py
call "%~dp0run_v2_social_post.bat"
goto end

:end
echo.
echo Done!
