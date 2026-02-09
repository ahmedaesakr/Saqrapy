@echo off
cd /d "%~dp0"
call venv\Scripts\activate
cd job_finder
scrapy crawl wuzzuf_jobs -o jobs.json
echo Done! Check job_finder/jobs.json
pause
