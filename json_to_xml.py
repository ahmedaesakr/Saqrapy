"""
JSON to XML Converter
Reads all scraped JSON files and produces one big XML file with all jobs.
"""

import json
import os
import glob
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'job_finder', 'output')
BY_SOURCE = os.path.join(OUTPUT_DIR, 'by_source')
SOCIAL_MEDIA = os.path.join(OUTPUT_DIR, 'social_media')


def load_json_file(filepath):
    """Load and parse JSON file, handling various formats"""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if '][' in content:
                content = content.replace('][', ',')
            return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return []


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
            unique.append(job)
    return unique


def sanitize_xml_text(text):
    """Remove characters that are invalid in XML"""
    if not text:
        return ''
    # Remove XML-invalid control characters (keep tab, newline, carriage return)
    return ''.join(
        c for c in str(text)
        if c == '\t' or c == '\n' or c == '\r' or (ord(c) >= 0x20 and ord(c) != 0xFFFE and ord(c) != 0xFFFF)
    )


def main():
    print("\n" + "=" * 60)
    print("  JSON TO XML CONVERTER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Load all jobs from source files
    print("Loading jobs from source files...")
    all_jobs = []

    source_patterns = [
        os.path.join(BY_SOURCE, '*.json'),
        os.path.join(SOCIAL_MEDIA, '*.json'),
    ]

    for pattern in source_patterns:
        for filepath in glob.glob(pattern):
            jobs = load_json_file(filepath)
            if jobs:
                print(f"  Loaded {len(jobs)} jobs from {os.path.basename(filepath)}")
                all_jobs.extend(jobs)

    # Also try the combined categorized file if no source files
    if not all_jobs:
        combined = os.path.join(OUTPUT_DIR, 'all_jobs_categorized.json')
        all_jobs = load_json_file(combined)
        if all_jobs:
            print(f"  Loaded {len(all_jobs)} jobs from all_jobs_categorized.json")

    if not all_jobs:
        print("\n  No jobs found! Run the spiders first.")
        return

    print(f"\nTotal jobs loaded: {len(all_jobs)}")

    # Deduplicate
    all_jobs = deduplicate_jobs(all_jobs)
    print(f"After deduplication: {len(all_jobs)}")

    # Build XML
    print("\nBuilding XML...")
    root = Element('jobs')
    root.set('generated', datetime.now().isoformat())
    root.set('total', str(len(all_jobs)))

    # Standard fields to include
    fields = [
        'title', 'company', 'location', 'type', 'link', 'source',
        'keyword_searched', 'budget', 'salary', 'date_posted', 'description',
        'relevance_score', 'job_category', 'region_category', 'is_remote',
    ]

    for job in all_jobs:
        job_el = SubElement(root, 'job')

        for field in fields:
            value = job.get(field)
            if value is not None and str(value).strip():
                child = SubElement(job_el, field.replace(' ', '_'))
                child.text = sanitize_xml_text(value)

        # Include any extra fields not in the standard list
        for key, value in job.items():
            if key not in fields and value is not None and str(value).strip():
                safe_key = key.replace(' ', '_').replace('-', '_')
                # Skip keys that aren't valid XML element names
                if safe_key and safe_key[0].isalpha():
                    child = SubElement(job_el, safe_key)
                    child.text = sanitize_xml_text(value)

    # Pretty print
    raw_xml = tostring(root, encoding='unicode')
    pretty_xml = parseString(raw_xml).toprettyxml(indent='  ', encoding='utf-8')

    # Save
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    xml_path = os.path.join(BASE_DIR, 'job_finder', f'all_jobs_{timestamp}.xml')
    latest_path = os.path.join(BASE_DIR, 'job_finder', 'all_jobs_latest.xml')

    for out_path in [xml_path, latest_path]:
        with open(out_path, 'wb') as f:
            f.write(pretty_xml)

    print("\n" + "=" * 60)
    print("  XML EXPORT COMPLETE!")
    print("=" * 60)
    print(f"\n  Timestamped: {xml_path}")
    print(f"  Latest:      {latest_path}")
    print(f"  Total jobs:  {len(all_jobs)}")
    print()


if __name__ == '__main__':
    main()
