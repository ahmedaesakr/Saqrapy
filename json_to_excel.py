"""
Convert all JSON output files to Excel sheets
Creates separate worksheets for each source with "Chad" enhancements
"""

import pandas as pd
import json
import os
import re
from datetime import datetime


def fix_json_content(content):
    """Fix common JSON issues from Scrapy output"""
    # Fix concatenated arrays: ][  -> ,
    content = content.replace('][', ',')
    content = content.replace(']\n[', ',')
    content = content.replace('] [', ',')
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: extract individual objects
        print("Standard JSON parse failed, using regex extraction...")
        objects = re.findall(r'\{[^{}]*\}', content)
        return [json.loads(o) for o in objects]


def json_to_df(filepath):
    """Load JSON file and return DataFrame"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return pd.DataFrame()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip() or content.strip() in ['[]', '{}']:
            return pd.DataFrame()
            
        data = fix_json_content(content)
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return pd.DataFrame()


def clean_dataframe(df):
    """Clean and enhance the dataframe"""
    if df.empty:
        return df
    
    # Ensure required columns exist
    required_cols = ['title', 'company', 'location', 'type', 'link', 'source']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
    
    # Remove duplicates based on link
    df = df.drop_duplicates(subset=['link'], keep='first')
    
    # Clean string columns
    for col in ['title', 'company', 'location', 'type', 'source']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
    
    # Add timestamp
    df['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return df


def main():
    # Define input/output paths
    output_dir = 'job_finder/output'
    
    # Files to process (including new remote jobs)
    files = {
        'Job Boards': os.path.join(output_dir, 'wuzzuf_indeed.json'),
        'LinkedIn': os.path.join(output_dir, 'linkedin.json'),
        'Freelance': os.path.join(output_dir, 'freelance.json'),
        'Career Pages': os.path.join(output_dir, 'career_pages.json'),
        'Remote (UAE/Europe)': os.path.join(output_dir, 'remote_jobs.json'),
        'Playwright Jobs': os.path.join(output_dir, 'playwright_jobs.json'),
    }
    
    # Also check for individual files if output dir doesn't exist
    if not os.path.exists(output_dir):
        files = {
            'Job Boards': 'job_finder/jobs.json',
        }
    
    # Create Excel writer
    excel_path = 'job_finder/all_jobs.xlsx'
    
    all_dfs = []
    stats = {}
    
    print("\n" + "="*50)
    print("Job Finder - Excel Export")
    print("="*50 + "\n")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, filepath in files.items():
            df = json_to_df(filepath)
            
            if df.empty:
                print(f"⚪ {sheet_name}: No data")
                # Create empty sheet with headers
                df = pd.DataFrame(columns=['title', 'company', 'location', 'type', 'link', 'source', 'scraped_at'])
            else:
                df = clean_dataframe(df)
                stats[sheet_name] = len(df)
                all_dfs.append(df)
                print(f"✅ {sheet_name}: {len(df)} jobs found")
            
            # Clean sheet name for Excel (max 31 chars, no special chars)
            safe_name = sheet_name[:31].replace('/', '-')
            df.to_excel(writer, sheet_name=safe_name, index=False)
    
    print(f"\n📊 Excel file saved: {excel_path}")
    
    # Create combined file
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined = combined.drop_duplicates(subset=['link'], keep='first')
        
        # Sort by source then by title
        if 'source' in combined.columns and 'title' in combined.columns:
            combined = combined.sort_values(['source', 'title'])
        
        combined_path = 'job_finder/all_jobs_combined.xlsx'
        combined.to_excel(combined_path, index=False)
        
        print(f"📊 Combined Excel: {combined_path}")
        print(f"\n" + "="*50)
        print(f"TOTAL: {len(combined)} unique jobs found!")
        print("="*50 + "\n")
        
        # Print summary by source
        if 'source' in combined.columns:
            print("Jobs by source:")
            source_counts = combined['source'].value_counts()
            for source, count in source_counts.items():
                print(f"  • {source}: {count}")
        
        # Print by region if available
        if 'region' in combined.columns:
            print("\nJobs by region:")
            region_counts = combined['region'].value_counts()
            for region, count in region_counts.items():
                print(f"  • {region}: {count}")


if __name__ == '__main__':
    main()
