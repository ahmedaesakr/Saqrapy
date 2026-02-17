@echo off
REM ============================================
REM Job Finder v2.0 - Social Media Poster
REM Post job opportunities to Facebook, LinkedIn, X
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

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
"%VENV_PY%" -c "
import sys, json, os, glob
sys.path.insert(0, 'job_finder')
from job_finder.social_media import FacebookPoster, LinkedInPoster, TwitterPoster
from job_finder.categories import categorize_job

search_paths = [
    'job_finder/output/social_media/*.json',
    'job_finder/output/by_source/*.json',
    'job_finder/output/by_category/*.json',
    'job_finder/output/by_region/*.json',
]

jobs = []
for pattern in search_paths:
    for f in glob.glob(pattern):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                content = fp.read().strip()
                if content.startswith('['):
                    content = content.replace('][', ',')
                    loaded = json.loads(content)
                    jobs.extend(loaded[:5])
        except:
            pass
    if jobs:
        break

if not jobs:
    print('No jobs found! Run a scrape first.')
    print('  Try: run_v2_full_scrape.bat')
    exit()

jobs = [categorize_job(j) for j in jobs[:3]]

fb = FacebookPoster({})
li = LinkedInPoster({})
tw = TwitterPoster({})

for i, job in enumerate(jobs, 1):
    print(f'\n{chr(61)*60}')
    print(f'JOB {i}: {job.get(\"title\", \"Unknown\")}')
    print(f'Company: {job.get(\"company\", \"N/A\")} | Location: {job.get(\"location\", \"N/A\")}')
    print('='*60)

    print('\n--- FACEBOOK ---')
    print(fb.format_post(job))

    print('\n--- LINKEDIN ---')
    print(li.format_post(job))

    print('\n--- TWITTER ---')
    tweet = tw.format_post(job)
    print(f'{tweet}')
    print(f'[{len(tweet)}/280 chars]')

print(f'\n{chr(61)*60}')
print(f'Previewed {len(jobs)} jobs across 3 platforms.')
print('To actually post, set up API credentials first.')
"
pause
goto end

:facebook
echo.
echo Posting to Facebook...
echo ============================================
echo.
echo  Setup required:
echo    1. Create a Facebook App at developers.facebook.com
echo    2. Get a Page Access Token
echo    3. Set environment variables:
echo       set FB_ACCESS_TOKEN=your_token
echo       set FB_PAGE_ID=your_page_id
echo.
echo  Or create a .env file with these values.
echo.
pause
goto end

:linkedin
echo.
echo Posting to LinkedIn...
echo ============================================
echo.
echo  Setup required:
echo    1. Create app at linkedin.com/developers
echo    2. Get OAuth 2.0 access token (w_organization_social scope)
echo    3. Set environment variables:
echo       set LINKEDIN_ACCESS_TOKEN=your_token
echo       set LINKEDIN_ORG_ID=your_org_urn
echo.
pause
goto end

:twitter
echo.
echo Posting to X (Twitter)...
echo ============================================
echo.
echo  Setup required:
echo    1. Apply at developer.twitter.com
echo    2. Create project and app
echo    3. Generate OAuth 1.0a tokens
echo    4. Set environment variables:
echo       set TWITTER_API_KEY=your_key
echo       set TWITTER_API_SECRET=your_secret
echo       set TWITTER_ACCESS_TOKEN=your_token
echo       set TWITTER_ACCESS_SECRET=your_secret
echo.
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
