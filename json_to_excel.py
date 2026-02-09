"""
Convert all JSON output files to Excel sheets
Creates separate worksheets for each source
"""

import pandas as pd
import json
import os
import re


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
        
        if not content.strip():
            return pd.DataFrame()
            
        data = fix_json_content(content)
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return pd.DataFrame()


def main():
    # Define input/output paths
    output_dir = 'job_finder/output'
    
    # Files to process
    files = {
        'Job Boards': os.path.join(output_dir, 'wuzzuf_indeed.json'),
        'LinkedIn': os.path.join(output_dir, 'linkedin.json'),
        'Freelance': os.path.join(output_dir, 'freelance.json'),
        'Career Pages': os.path.join(output_dir, 'career_pages.json'),
    }
    
    # Also check for individual files if output dir doesn't exist
    if not os.path.exists(output_dir):
        files = {
            'Job Boards': 'job_finder/jobs.json',
        }
    
    # Create Excel writer
    excel_path = 'job_finder/all_jobs.xlsx'
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, filepath in files.items():
            df = json_to_df(filepath)
            
            if df.empty:
                print(f"No data for {sheet_name}")
                # Create empty sheet with headers
                df = pd.DataFrame(columns=['title', 'company', 'location', 'type', 'link', 'source'])
            else:
                # Remove duplicates based on link
                df = df.drop_duplicates(subset=['link'], keep='first')
                print(f"{sheet_name}: {len(df)} jobs found")
            
            # Clean sheet name for Excel (max 31 chars, no special chars)
            safe_name = sheet_name[:31].replace('/', '-')
            df.to_excel(writer, sheet_name=safe_name, index=False)
    
    print(f"\nExcel file saved: {excel_path}")
    
    # Also create a combined "All Jobs" sheet
    all_dfs = []
    for filepath in files.values():
        df = json_to_df(filepath)
        if not df.empty:
            all_dfs.append(df)
    
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined = combined.drop_duplicates(subset=['link'], keep='first')
        combined.to_excel('job_finder/all_jobs_combined.xlsx', index=False)
        print(f"Combined Excel: job_finder/all_jobs_combined.xlsx ({len(combined)} total jobs)")


if __name__ == '__main__':
    main()
