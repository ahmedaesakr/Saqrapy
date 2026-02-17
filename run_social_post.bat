@echo off
REM ============================================
REM Social Media Poster - Post job results to platforms
REM Requires API credentials for each platform
REM ============================================

cd /d "%~dp0"
set VENV_PY=%~dp0venv\Scripts\python.exe

echo.
echo ============================================
echo  SOCIAL MEDIA POSTER
echo ============================================
echo  [1] Preview Posts Only (no posting)
echo  [2] Facebook Page
echo  [3] LinkedIn Company Page
echo  [4] X (Twitter)
echo  [5] All Platforms
echo  [0] Back
echo ============================================
echo.

set /p choice="Select (0-5): "

if "%choice%"=="0" goto end
if "%choice%"=="1" goto preview
if "%choice%"=="2" goto facebook
if "%choice%"=="3" goto linkedin
if "%choice%"=="4" goto twitter
if "%choice%"=="5" goto all_platforms

echo Invalid choice.
pause
goto end

:preview
echo.
echo Generating post previews...
"%VENV_PY%" -c "
import sys, json, os, glob
sys.path.insert(0, 'job_finder')
from job_finder.social_media import FacebookPoster, LinkedInPoster, TwitterPoster
from job_finder.categories import categorize_job

search_paths = [
    'job_finder/output/social_media/*.json',
    'job_finder/output/by_source/*.json',
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

print(f'\nPreviewed {len(jobs)} jobs. Set up API credentials to actually post.')
"
pause
goto end

:facebook
echo.
echo  Setup required:
echo    1. Create Facebook App at developers.facebook.com
echo    2. Get Page Access Token
echo    3. Set: FB_ACCESS_TOKEN and FB_PAGE_ID
echo.
pause
goto end

:linkedin
echo.
echo  Setup required:
echo    1. Create app at linkedin.com/developers
echo    2. Get OAuth 2.0 token (w_organization_social)
echo    3. Set: LINKEDIN_ACCESS_TOKEN and LINKEDIN_ORG_ID
echo.
pause
goto end

:twitter
echo.
echo  Setup required:
echo    1. Apply at developer.twitter.com
echo    2. Generate OAuth 1.0a tokens
echo    3. Set: TWITTER_API_KEY, TWITTER_API_SECRET,
echo           TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
echo.
pause
goto end

:all_platforms
call :facebook
call :linkedin
call :twitter
goto end

:end
