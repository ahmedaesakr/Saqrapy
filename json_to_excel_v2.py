"""
JSON to Excel Converter v2.0
Creates Excel file with multiple sheets organized by source, category, and region
"""

import json
import os
import glob
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("pandas not installed. Run: pip install pandas openpyxl")
    exit(1)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'job_finder', 'output')
BY_SOURCE = os.path.join(OUTPUT_DIR, 'by_source')
BY_CATEGORY = os.path.join(OUTPUT_DIR, 'by_category')
BY_REGION = os.path.join(OUTPUT_DIR, 'by_region')


def load_json_file(filepath):
    """Load and parse JSON file"""
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if '][' in content:
                content = content.replace('][', ',')
            return json.loads(content)
    except:
        return []


def clean_dataframe(df):
    """Clean and format DataFrame for Excel"""
    if df.empty:
        return df
    
    # Define column order
    priority_columns = [
        'title', 'company', 'location', 'type', 'link', 'source',
        'job_category', 'job_category_icon', 'region_category', 'region_icon',
        'is_remote', 'date_posted', 'salary', 'description'
    ]
    
    # Reorder columns
    existing = [c for c in priority_columns if c in df.columns]
    other = [c for c in df.columns if c not in priority_columns]
    df = df[existing + other]
    
    # Remove duplicates
    if 'link' in df.columns:
        df = df.drop_duplicates(subset=['link'], keep='first')
    
    # Truncate long text
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str[:500]
    
    return df


def create_excel_v2():
    """Create Excel file with organized sheets"""
    
    print("\n" + "=" * 60)
    print("  JSON TO EXCEL CONVERTER v2.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    # Output Excel file
    excel_path = os.path.join(BASE_DIR, 'job_finder', 'all_jobs_v2.xlsx')
    
    # Define sheets to create
    sheets = {}
    
    # --- BY SOURCE ---
    source_files = {
        '📋 Wuzzuf': os.path.join(BY_SOURCE, 'wuzzuf.json'),
        '📋 Indeed': os.path.join(BY_SOURCE, 'indeed.json'),
        '🔗 LinkedIn': os.path.join(BY_SOURCE, 'linkedin.json'),
        '💼 Freelance': os.path.join(BY_SOURCE, 'freelance.json'),
        '🏛️ Careers': os.path.join(BY_SOURCE, 'career_pages.json'),
        '🌐 Remote': os.path.join(BY_SOURCE, 'remote_jobs.json'),
    }
    
    # --- BY CATEGORY ---
    category_files = {
        '🏠 Remote Jobs': os.path.join(BY_CATEGORY, 'remote_jobs.json'),
        '💼 Freelance': os.path.join(BY_CATEGORY, 'freelance_jobs.json'),
        '🏢 Full-Time': os.path.join(BY_CATEGORY, 'fulltime_jobs.json'),
        '🔄 Hybrid': os.path.join(BY_CATEGORY, 'hybrid_jobs.json'),
    }
    
    # --- BY REGION ---
    region_files = {
        '🇪🇬 Egypt': os.path.join(BY_REGION, 'egypt_jobs.json'),
        '🇦🇪 UAE': os.path.join(BY_REGION, 'uae_jobs.json'),
        '🇪🇺 Europe': os.path.join(BY_REGION, 'europe_jobs.json'),
        '🌍 Global': os.path.join(BY_REGION, 'global_jobs.json'),
    }
    
    # --- LEGACY FILES (for backwards compatibility) ---
    legacy_files = {
        'Combined': os.path.join(OUTPUT_DIR, 'wuzzuf_indeed.json'),
        'All Jobs': os.path.join(OUTPUT_DIR, 'all_jobs_categorized.json'),
    }
    
    # Combine all file mappings
    all_files = {**source_files, **category_files, **region_files, **legacy_files}
    
    print("Loading data from JSON files...")
    
    for sheet_name, filepath in all_files.items():
        jobs = load_json_file(filepath)
        if jobs:
            # Clean sheet name for Excel (max 31 chars, no special chars)
            clean_name = sheet_name[:31].replace('/', '-').replace('\\', '-')
            clean_name = clean_name.replace(':', '').replace('*', '').replace('?', '')
            
            df = pd.DataFrame(jobs)
            df = clean_dataframe(df)
            sheets[clean_name] = df
            print(f"  ✓ {sheet_name}: {len(df)} jobs")
        else:
            print(f"  ○ {sheet_name}: No data found")
    
    if not sheets:
        print("\nNo data found! Run the spiders first.")
        return
    
    # --- CREATE SUMMARY SHEET ---
    print("\nCreating summary sheet...")
    summary_data = []
    for sheet_name, df in sheets.items():
        if not df.empty:
            summary_data.append({
                'Sheet': sheet_name,
                'Total Jobs': len(df),
                'Companies': df['company'].nunique() if 'company' in df.columns else 0,
                'Remote': len(df[df.get('is_remote', False) == True]) if 'is_remote' in df.columns else 0,
            })
    
    summary_df = pd.DataFrame(summary_data)
    
    # --- WRITE TO EXCEL ---
    print(f"\nWriting to Excel: {excel_path}")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Summary first
        if not summary_df.empty:
            summary_df.to_excel(writer, sheet_name='📊 Summary', index=False)
            print("  ✓ Summary sheet created")
        
        # All other sheets
        for sheet_name, df in sheets.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print("\n" + "=" * 60)
    print("  EXCEL EXPORT COMPLETE!")
    print("=" * 60)
    print(f"\n  File: {excel_path}")
    print(f"  Sheets: {len(sheets) + 1}")
    print(f"  Total rows: {sum(len(df) for df in sheets.values())}")
    print()


if __name__ == '__main__':
    create_excel_v2()
