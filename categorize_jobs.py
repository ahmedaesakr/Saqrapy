"""
Job Categorizer Script v2.0
Reads all scraped JSON files and categorizes jobs into:
- By Category: remote, freelance, fulltime, hybrid
- By Region: egypt, uae, europe, global
"""

import json
import os
import sys
import glob
from datetime import datetime

# Add parent directory to path for imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'job_finder'))

from job_finder.categories import categorize_job, JobType, Region

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'job_finder', 'output')
BY_SOURCE = os.path.join(OUTPUT_DIR, 'by_source')
BY_CATEGORY = os.path.join(OUTPUT_DIR, 'by_category')
BY_REGION = os.path.join(OUTPUT_DIR, 'by_region')
SOCIAL_MEDIA = os.path.join(OUTPUT_DIR, 'social_media')


def load_json_file(filepath):
    """Load and parse JSON file, handling various formats"""
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Handle multiple JSON arrays concatenated
            if '][' in content:
                content = content.replace('][', ',')
            
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  Warning: Could not parse {filepath}: {e}")
        return []
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return []


def save_json_file(filepath, data):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(data)} jobs to {os.path.basename(filepath)}")


def deduplicate_jobs(jobs):
    """Remove duplicate jobs based on link"""
    seen = set()
    unique = []
    for job in jobs:
        link = job.get('link', '')
        if link and link not in seen:
            seen.add(link)
            unique.append(job)
        elif not link:
            # Keep jobs without links but add to unique list
            unique.append(job)
    return unique


def main():
    print("\n" + "=" * 60)
    print("  JOB CATEGORIZER v2.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    # Create output directories
    os.makedirs(BY_CATEGORY, exist_ok=True)
    os.makedirs(BY_REGION, exist_ok=True)
    
    # Load all jobs from source files
    print("Loading jobs from source files...")
    all_jobs = []
    
    # Scan all output locations (job boards + social media)
    source_patterns = [
        os.path.join(BY_SOURCE, '*.json'),
        os.path.join(SOCIAL_MEDIA, '*.json'),
    ]
    
    for pattern in source_patterns:
        for filepath in glob.glob(pattern):
            if 'by_category' not in filepath and 'by_region' not in filepath:
                jobs = load_json_file(filepath)
                if jobs:
                    print(f"  Loaded {len(jobs)} jobs from {os.path.basename(filepath)}")
                    all_jobs.extend(jobs)
    
    if not all_jobs:
        print("\n  No jobs found! Run the spiders first.")
        return
    
    print(f"\nTotal jobs loaded: {len(all_jobs)}")
    
    # Deduplicate
    all_jobs = deduplicate_jobs(all_jobs)
    print(f"After deduplication: {len(all_jobs)}")
    
    # Categorize all jobs
    print("\nCategorizing jobs...")
    categorized_jobs = [categorize_job(job) for job in all_jobs]
    
    # Group by category
    by_type = {
        'remote': [],
        'freelance': [],
        'fulltime': [],
        'hybrid': [],
        'other': [],
    }
    
    by_region = {
        'egypt': [],
        'uae': [],
        'europe': [],
        'global': [],
        'other': [],
    }
    
    for job in categorized_jobs:
        # Group by job type
        job_cat = job.get('job_category', 'other')
        if job_cat in by_type:
            by_type[job_cat].append(job)
        else:
            by_type['other'].append(job)
        
        # Group by region
        region_cat = job.get('region_category', 'other')
        if region_cat in by_region:
            by_region[region_cat].append(job)
        else:
            by_region['other'].append(job)
    
    # Print summary
    print("\n" + "-" * 40)
    print("BY CATEGORY:")
    print("-" * 40)
    for cat, jobs in by_type.items():
        if jobs:
            icon = jobs[0].get('job_category_icon', '') if jobs else ''
            print(f"  {icon} {cat.upper()}: {len(jobs)} jobs")
    
    print("\n" + "-" * 40)
    print("BY REGION:")
    print("-" * 40)
    for region, jobs in by_region.items():
        if jobs:
            icon = jobs[0].get('region_icon', '') if jobs else ''
            print(f"  {icon} {region.upper()}: {len(jobs)} jobs")
    
    # Save categorized files
    print("\n" + "-" * 40)
    print("SAVING FILES:")
    print("-" * 40)
    
    # By category
    for cat, jobs in by_type.items():
        if jobs:
            filepath = os.path.join(BY_CATEGORY, f'{cat}_jobs.json')
            save_json_file(filepath, jobs)
    
    # By region
    for region, jobs in by_region.items():
        if jobs:
            filepath = os.path.join(BY_REGION, f'{region}_jobs.json')
            save_json_file(filepath, jobs)
    
    # Save combined file
    combined_path = os.path.join(OUTPUT_DIR, 'all_jobs_categorized.json')
    save_json_file(combined_path, categorized_jobs)
    
    print("\n" + "=" * 60)
    print("  CATEGORIZATION COMPLETE!")
    print("=" * 60)
    print(f"\n  Total: {len(categorized_jobs)} unique jobs categorized")
    print(f"  Output: {OUTPUT_DIR}")
    print()


if __name__ == '__main__':
    main()
