#!/usr/bin/env python3
"""
Interim Analysis Script
Runs pattern-based claim extraction on available text files
"""

import os
import re
import json
import csv
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np
from datetime import datetime

PROCESSED_TEXT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/processed_text")
OUTPUT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs")

def extract_claims_patterns(text, doc_info):
    """Extract claims using regex patterns."""
    claims = []

    # Pattern for percentage improvements
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*(?:improvement|increase|reduction|decrease)', 'improvement'),
        (r'(?:improved?|increased?|reduced?|decreased?|achieved?)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*(?:percent|%)', 'change'),
        (r'(?:HEDIS|CAHPS|NQF)\s+(?:measure\s+)?([A-Z0-9\-]+)', 'metric'),
        (r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s+(?:of\s+)?(?:members?|enrollees?|patients?)', 'rate'),
        (r'(?:target|goal|commit)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:percent|%)?', 'target'),
    ]

    for pattern, pattern_type in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context_start = max(0, match.start() - 200)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end].strip()

            claims.append({
                'verbatim_text': context[:300],
                'pattern_type': pattern_type,
                'matched_value': match.group(1) if match.groups() else match.group(0),
                'state': doc_info.get('state', 'Unknown'),
                'extraction_method': 'pattern'
            })

    return claims

def extract_partnerships_patterns(text, doc_info):
    """Extract partnerships using regex patterns."""
    partnerships = []

    patterns = [
        r'(?:partner(?:ship|ed|ing)?|collaborat(?:e|ion|ing))\s+with\s+([A-Z][^,.]{5,50})',
        r'(?:contract(?:ed)?|agreement)\s+with\s+([A-Z][^,.]{5,50})',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            partner = match.group(1).strip()
            if len(partner) > 5:
                partnerships.append({
                    'partner_name': partner[:100],
                    'state': doc_info.get('state', 'Unknown'),
                    'extraction_method': 'pattern'
                })

    return partnerships

def analyze_all_text_files():
    """Analyze all available text files."""
    all_claims = []
    all_partnerships = []
    files_processed = 0

    text_files = list(PROCESSED_TEXT_DIR.rglob('*.txt'))
    print(f"Analyzing {len(text_files)} text files...")

    for i, text_path in enumerate(text_files):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{len(text_files)}")

        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except:
            continue

        if len(text) < 100:
            continue

        # Get state from path
        parts = text_path.relative_to(PROCESSED_TEXT_DIR).parts
        state = parts[0] if len(parts) > 0 else 'Unknown'

        doc_info = {
            'state': state,
            'filename': text_path.name
        }

        claims = extract_claims_patterns(text, doc_info)
        partnerships = extract_partnerships_patterns(text, doc_info)

        all_claims.extend(claims)
        all_partnerships.extend(partnerships)
        files_processed += 1

    return all_claims, all_partnerships, files_processed

def summarize_claims(claims):
    """Generate claim summary statistics."""
    summary = {
        'total_claims': len(claims),
        'by_pattern_type': defaultdict(int),
        'by_state': defaultdict(int),
        'values': []
    }

    for claim in claims:
        summary['by_pattern_type'][claim.get('pattern_type', 'other')] += 1
        summary['by_state'][claim.get('state', 'Unknown')] += 1
        try:
            val = float(claim.get('matched_value', 0))
            if 0 < val < 1000:  # Reasonable range
                summary['values'].append(val)
        except:
            pass

    summary['by_pattern_type'] = dict(summary['by_pattern_type'])
    summary['by_state'] = dict(summary['by_state'])

    if summary['values']:
        summary['mean_value'] = np.mean(summary['values'])
        summary['median_value'] = np.median(summary['values'])
        summary['std_value'] = np.std(summary['values'])
    else:
        summary['mean_value'] = None
        summary['median_value'] = None
        summary['std_value'] = None

    del summary['values']  # Don't save raw values

    return summary

def main():
    print("="*60)
    print("INTERIM ANALYSIS")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}")

    # Run analysis
    claims, partnerships, files_processed = analyze_all_text_files()

    # Generate summaries
    claim_summary = summarize_claims(claims)
    claim_summary['files_processed'] = files_processed
    claim_summary['analyzed_at'] = datetime.now().isoformat()

    # Save claims
    claims_df = pd.DataFrame(claims)
    claims_df.to_csv(OUTPUT_DIR / 'interim_claims.csv', index=False)

    # Save partnerships
    partnerships_df = pd.DataFrame(partnerships)
    partnerships_df.to_csv(OUTPUT_DIR / 'interim_partnerships.csv', index=False)

    # Save summary
    with open(OUTPUT_DIR / 'interim_claim_summary.json', 'w') as f:
        json.dump(claim_summary, f, indent=2)

    print(f"\nAnalysis complete:")
    print(f"  Files processed: {files_processed}")
    print(f"  Claims extracted: {len(claims)}")
    print(f"  Partnerships extracted: {len(partnerships)}")
    print(f"  Claims by pattern type: {claim_summary['by_pattern_type']}")

    print(f"\nEnd time: {datetime.now().isoformat()}")

if __name__ == '__main__':
    main()
