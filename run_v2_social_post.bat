@echo off
REM ============================================
REM Job Finder v2.0 - Social Media Poster
REM Post job opportunities to Facebook, LinkedIn, X
REM ============================================

cd /d "%~dp0"
call venv\Scripts\activate

echo.
echo ============================================
echo  Job Finder v2.0 - SOCIAL MEDIA POSTER
echo ============================================
echo.
echo  Platforms:
echo    [1] Facebook Page
echo    [2] LinkedIn Company Page
echo    [3] X (Twitter)
echo    [4] All Platforms
echo    [5] Preview Posts Only (No Posting)
echo    [0] Back
echo ============================================
echo.

set /p platform="Select platform (0-5): "

if "%platform%"=="0" goto end
if "%platform%"=="1" goto facebook
if "%platform%"=="2" goto linkedin
if "%platform%"=="3" goto twitter
if "%platform%"=="4" goto all_platforms
if "%platform%"=="5" goto preview

echo Invalid choice.
pause
goto end

:preview
echo.
echo Generating post previews...
echo ============================================
python -c "
from job_finder.social_media import FacebookPoster, LinkedInPoster, TwitterPoster
from job_finder.categories import categorize_job
import json
import os

# Load recent jobs
job_files = [
    'job_finder/output/by_category/remote_jobs_final.json',
    'job_finder/output/by_source/remote_jobs.json',
    'job_finder/output/wuzzuf_indeed.json',
]

jobs = []
for f in job_files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as fp:
            try:
                content = fp.read().replace('][', ',')
                jobs.extend(json.loads(content)[:5])  # First 5
            except:
                pass
        break

if not jobs:
    print('No jobs found to preview!')
    exit()

# Categorize
jobs = [categorize_job(j) for j in jobs[:3]]

# Preview posts
fb = FacebookPoster({})
li = LinkedInPoster({})
tw = TwitterPoster({})

for i, job in enumerate(jobs, 1):
    print(f'\\n{\"=\"*60}')
    print(f'JOB {i}: {job.get(\"title\", \"Unknown\")}')
    print('='*60)
    
    print('\\n--- FACEBOOK ---')
    print(fb.format_post(job)[:500] + '...')
    
    print('\\n--- LINKEDIN ---')
    print(li.format_post(job)[:500] + '...')
    
    print('\\n--- TWITTER ---')
    tweet = tw.format_post(job)
    print(f'{tweet}')
    print(f'[{len(tweet)}/280 chars]')
"
pause
goto end

:facebook
echo.
echo Posting to Facebook...
echo ============================================
echo.
echo NOTE: You need to set up Facebook API credentials in:
echo   job_finder/config/social_media.yaml
echo.
echo Or set environment variables:
echo   FB_ACCESS_TOKEN
echo   FB_PAGE_ID
echo.
echo Feature coming soon! Use Preview mode to test.
pause
goto end

:linkedin
echo.
echo Posting to LinkedIn...
echo ============================================
echo.
echo NOTE: You need to set up LinkedIn Marketing API:
echo   1. Create app at developers.linkedin.com
echo   2. Get access token with w_organization_social scope
echo   3. Add credentials to config
echo.
echo Feature coming soon! Use Preview mode to test.
pause
goto end

:twitter
echo.
echo Posting to X (Twitter)...
echo ============================================
echo.
echo NOTE: You need Twitter Developer API access:
echo   1. Apply at developer.twitter.com
echo   2. Create project and app
echo   3. Generate OAuth 1.0a tokens
echo   4. Add credentials to config
echo.
echo Feature coming soon! Use Preview mode to test.
pause
goto end

:all_platforms
echo Posting to all platforms...
call :facebook
call :linkedin
call :twitter
goto end

:end
echo.
echo ============================================
