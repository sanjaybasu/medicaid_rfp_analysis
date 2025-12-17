#!/usr/bin/env python3
"""
Phase 1: Document Inventory and Extraction
Medicaid MCO RFP Analysis Pipeline

This script catalogs all documents in the RFP corpus and generates
a comprehensive inventory for the analysis pipeline.
"""

import os
import re
import csv
import json
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
RFP_BASE_DIR = Path("/Users/sanjaybasu/waymark-local/data/rfps")
OUTPUT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs")
PROCESSED_TEXT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/processed_text")

# Document type classification patterns
DOC_TYPE_PATTERNS = {
    'rfp': [r'rfp', r'rfq', r'rfa', r'rfr', r'rfi'],
    'proposal': [r'proposal', r'response', r'redacted.*proposal', r'application'],
    'scoring': [r'scor', r'evaluat', r'rating'],
    'contract': [r'contract', r'model.*contract', r'executed'],
    'award': [r'award', r'intent.*award', r'notice'],
    'amendment': [r'amend', r'addend', r'add\d'],
    'attachment': [r'attach', r'appendix', r'appendices', r'exhibit', r'schedule'],
    'protest': [r'protest', r'appeal'],
}

# MCO name patterns (major national MCOs)
MCO_PATTERNS = {
    'Aetna': [r'aetna', r'cvs.*aetna', r'cvs'],
    'Anthem': [r'anthem', r'bcbs', r'blue.*cross', r'wellpoint', r'elevance'],
    'Centene': [r'centene', r'wellcare', r'ambetter', r'health.*net', r'meridian', r'magnolia', r'truecare', r'sunflower', r'peach.*state', r'buckeye'],
    'Cigna': [r'cigna'],
    'Humana': [r'humana'],
    'Molina': [r'molina'],
    'UnitedHealthcare': [r'united', r'uhc', r'optum', r'uhg'],
    'Amerigroup': [r'amerigroup'],
    'AmeriHealth Caritas': [r'amerihealth'],
    'CareSource': [r'caresource'],
    'BCBS_Regional': [r'bcbs.*michigan', r'blue.*cross.*michigan', r'hap'],
    'Kaiser': [r'kaiser'],
    'Health Choice Arizona': [r'health.*choice.*arizona', r'azch', r'care1st'],
    'Mercy Care': [r'mercy.*care', r'banner.*ufc'],
    'AlohaCare': [r'alohacare'],
    'HMSA': [r'hmsa'],
    'Ohana': [r'ohana'],
    'Neighborhood Health Plan': [r'neighborhood', r'nhp'],
    'Tufts Health': [r'tufts'],
    'Priority Health': [r'priority.*health'],
    'McLaren': [r'mclaren'],
    'UPHP': [r'uphp'],
    'Harmony': [r'harmony'],
    'IlliniCare': [r'illinicare'],
    'CountyCare': [r'countycare'],
    'NextLevel': [r'nextlevel'],
    'Trusted': [r'trusted'],
    'The Health Plan': [r'the.*health.*plan'],
    'UniCare': [r'unicare'],
    'Medical Mutual': [r'medical.*mutual'],
    'Total Care': [r'total.*care'],
}


def extract_year_from_filename(filename):
    """Extract year from filename patterns."""
    # Pattern: explicit year (e.g., 2021, 2022)
    year_match = re.search(r'20(1[7-9]|2[0-4])', filename)
    if year_match:
        return int(year_match.group())

    # Pattern: month-year (e.g., Nov-21, Dec-22)
    month_year = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-_]?(\d{2})', filename.lower())
    if month_year:
        year = int(month_year.group(2))
        return 2000 + year if year < 50 else 1900 + year

    # Pattern: date format (e.g., 12-10-21)
    date_match = re.search(r'\d{1,2}[-_]\d{1,2}[-_](\d{2})\b', filename)
    if date_match:
        year = int(date_match.group(1))
        return 2000 + year if year < 50 else 1900 + year

    return None


def classify_document_type(filename):
    """Classify document type based on filename patterns."""
    filename_lower = filename.lower()

    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower):
                return doc_type

    return 'other'


def extract_mco_name(filename):
    """Extract MCO name from filename."""
    filename_lower = filename.lower()

    for mco_name, patterns in MCO_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower):
                return mco_name

    return None


def get_file_size_mb(filepath):
    """Get file size in megabytes."""
    try:
        return round(os.path.getsize(filepath) / (1024 * 1024), 2)
    except:
        return None


def generate_document_inventory():
    """Generate comprehensive document inventory."""
    inventory = []

    for state_dir in sorted(RFP_BASE_DIR.iterdir()):
        if not state_dir.is_dir():
            # Handle files in root (like MCO Outcomes Data.csv)
            if state_dir.is_file():
                file_ext = state_dir.suffix.lower()
                if file_ext in ['.pdf', '.docx', '.doc', '.zip', '.csv', '.xlsx']:
                    entry = {
                        'state': 'NATIONAL',
                        'filename': state_dir.name,
                        'document_type': 'data' if file_ext in ['.csv', '.xlsx'] else classify_document_type(state_dir.name),
                        'mco_name': extract_mco_name(state_dir.name),
                        'rfp_year': extract_year_from_filename(state_dir.name),
                        'format': file_ext.replace('.', ''),
                        'size_mb': get_file_size_mb(state_dir),
                        'compressed': file_ext == '.zip',
                        'full_path': str(state_dir),
                    }
                    inventory.append(entry)
            continue

        state_name = state_dir.name

        for filepath in state_dir.rglob('*'):
            if not filepath.is_file():
                continue

            file_ext = filepath.suffix.lower()
            if file_ext not in ['.pdf', '.docx', '.doc', '.zip', '.csv', '.xlsx']:
                continue

            entry = {
                'state': state_name,
                'filename': filepath.name,
                'document_type': classify_document_type(filepath.name),
                'mco_name': extract_mco_name(filepath.name),
                'rfp_year': extract_year_from_filename(filepath.name),
                'format': file_ext.replace('.', ''),
                'size_mb': get_file_size_mb(filepath),
                'compressed': file_ext == '.zip',
                'full_path': str(filepath),
            }
            inventory.append(entry)

    return inventory


def generate_summary_statistics(inventory):
    """Generate summary statistics for the inventory."""
    stats = {
        'total_documents': len(inventory),
        'states': len(set(d['state'] for d in inventory if d['state'] != 'NATIONAL')),
        'documents_by_state': defaultdict(int),
        'documents_by_type': defaultdict(int),
        'documents_by_format': defaultdict(int),
        'documents_by_year': defaultdict(int),
        'unique_mcos': set(),
        'compressed_files': sum(1 for d in inventory if d['compressed']),
        'total_size_mb': sum(d['size_mb'] or 0 for d in inventory),
    }

    for doc in inventory:
        stats['documents_by_state'][doc['state']] += 1
        stats['documents_by_type'][doc['document_type']] += 1
        stats['documents_by_format'][doc['format']] += 1
        if doc['rfp_year']:
            stats['documents_by_year'][doc['rfp_year']] += 1
        if doc['mco_name']:
            stats['unique_mcos'].add(doc['mco_name'])

    stats['unique_mcos'] = len(stats['unique_mcos'])
    stats['documents_by_state'] = dict(stats['documents_by_state'])
    stats['documents_by_type'] = dict(stats['documents_by_type'])
    stats['documents_by_format'] = dict(stats['documents_by_format'])
    stats['documents_by_year'] = dict(sorted(stats['documents_by_year'].items()))

    return stats


def save_inventory(inventory, stats):
    """Save inventory to CSV and JSON files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save CSV inventory
    csv_path = OUTPUT_DIR / 'document_inventory.csv'
    with open(csv_path, 'w', newline='') as f:
        fieldnames = ['state', 'filename', 'document_type', 'mco_name', 'rfp_year',
                      'format', 'size_mb', 'compressed', 'full_path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(inventory)

    # Save JSON inventory (for programmatic access)
    json_path = OUTPUT_DIR / 'document_inventory.json'
    with open(json_path, 'w') as f:
        json.dump({
            'inventory': inventory,
            'statistics': stats,
            'generated_at': datetime.now().isoformat(),
        }, f, indent=2)

    # Save summary statistics
    stats_path = OUTPUT_DIR / 'inventory_summary.json'
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"Inventory saved to {csv_path}")
    print(f"JSON inventory saved to {json_path}")
    print(f"Summary statistics saved to {stats_path}")

    return csv_path, json_path, stats_path


def print_summary(stats):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("DOCUMENT INVENTORY SUMMARY")
    print("="*60)
    print(f"\nTotal Documents: {stats['total_documents']}")
    print(f"Total States: {stats['states']}")
    print(f"Unique MCOs Identified: {stats['unique_mcos']}")
    print(f"Compressed Files: {stats['compressed_files']}")
    print(f"Total Size: {stats['total_size_mb']:.2f} MB")

    print("\n--- Documents by Type ---")
    for doc_type, count in sorted(stats['documents_by_type'].items(), key=lambda x: -x[1]):
        print(f"  {doc_type}: {count}")

    print("\n--- Documents by Format ---")
    for fmt, count in sorted(stats['documents_by_format'].items(), key=lambda x: -x[1]):
        print(f"  {fmt}: {count}")

    print("\n--- Documents by Year ---")
    for year, count in sorted(stats['documents_by_year'].items()):
        print(f"  {year}: {count}")

    print("\n--- Documents by State ---")
    for state, count in sorted(stats['documents_by_state'].items(), key=lambda x: -x[1]):
        print(f"  {state}: {count}")


if __name__ == '__main__':
    print("Starting Phase 1: Document Inventory Generation")
    print(f"Scanning directory: {RFP_BASE_DIR}")

    inventory = generate_document_inventory()
    stats = generate_summary_statistics(inventory)
    save_inventory(inventory, stats)
    print_summary(stats)

    print("\n" + "="*60)
    print("Phase 1 Complete")
    print("="*60)
