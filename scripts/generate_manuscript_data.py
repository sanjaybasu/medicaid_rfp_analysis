#!/usr/bin/env python3
"""
Generate Manuscript Data
Creates summary statistics and tables for Health Affairs manuscript
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
OUTPUT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs")
RFP_BASE_DIR = Path("/Users/sanjaybasu/waymark-local/data/rfps")
PROCESSED_TEXT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/processed_text")

def load_inventory():
    """Load document inventory."""
    inventory_path = OUTPUT_DIR / 'document_inventory.json'
    with open(inventory_path) as f:
        return json.load(f)

def load_outcomes_data():
    """Load MCO outcomes data."""
    outcomes_path = RFP_BASE_DIR / 'MCO Outcomes Data.csv'
    return pd.read_csv(outcomes_path)

def generate_table1_study_population():
    """Generate Table 1: Study Population Characteristics."""
    data = load_inventory()
    inventory = data['inventory']
    stats = data['statistics']

    # Document type distribution
    doc_types = stats['documents_by_type']

    # Year distribution
    years = stats['documents_by_year']

    # State distribution
    states = stats['documents_by_state']

    # Calculate statistics
    table1_data = {
        'Characteristic': [],
        'N': [],
        'Percentage': []
    }

    total_docs = stats['total_documents']

    # Document types
    table1_data['Characteristic'].append('Document Type')
    table1_data['N'].append('')
    table1_data['Percentage'].append('')

    for doc_type, count in sorted(doc_types.items(), key=lambda x: -x[1]):
        table1_data['Characteristic'].append(f'  {doc_type.title()}')
        table1_data['N'].append(count)
        table1_data['Percentage'].append(f'{100*count/total_docs:.1f}%')

    # Procurement years
    table1_data['Characteristic'].append('Procurement Year')
    table1_data['N'].append('')
    table1_data['Percentage'].append('')

    for year, count in sorted(years.items()):
        if 2017 <= int(year) <= 2024:
            table1_data['Characteristic'].append(f'  {year}')
            table1_data['N'].append(count)
            table1_data['Percentage'].append(f'{100*count/total_docs:.1f}%')

    # Geographic coverage
    table1_data['Characteristic'].append('Geographic Region')
    table1_data['N'].append('')
    table1_data['Percentage'].append('')

    regions = {
        'Northeast': ['Massachusetts', 'Rhode Island', 'New Hampshire', 'Delaware', 'Washington DC'],
        'Southeast': ['Georgia', 'Kentucky', 'Tennessee', 'Virginia', 'West Virginia', 'Louisiana', 'Mississippi', 'Florida'],
        'Midwest': ['Ohio', 'Indiana', 'Illinois', 'Michigan', 'Missouri', 'Iowa', 'Minnesota', 'Nebraska', 'Kansas'],
        'Southwest': ['Texas', 'Oklahoma', 'New Mexico', 'Arizona'],
        'West': ['California', 'Colorado', 'Oregon', 'Washington', 'Hawaii', 'Nevada']
    }

    for region, region_states in regions.items():
        count = sum(states.get(s, 0) for s in region_states)
        table1_data['Characteristic'].append(f'  {region}')
        table1_data['N'].append(count)
        table1_data['Percentage'].append(f'{100*count/total_docs:.1f}%')

    # MCO representation
    table1_data['Characteristic'].append('MCO Representation')
    table1_data['N'].append('')
    table1_data['Percentage'].append('')

    mco_counts = defaultdict(int)
    for doc in inventory:
        if doc['mco_name']:
            mco_counts[doc['mco_name']] += 1

    for mco, count in sorted(mco_counts.items(), key=lambda x: -x[1])[:10]:
        table1_data['Characteristic'].append(f'  {mco}')
        table1_data['N'].append(count)
        table1_data['Percentage'].append(f'{100*count/total_docs:.1f}%')

    df = pd.DataFrame(table1_data)
    return df

def generate_outcomes_summary():
    """Generate summary of HEDIS outcomes data."""
    outcomes_df = load_outcomes_data()

    # Filter to numeric rates
    outcomes_df['Rate_numeric'] = pd.to_numeric(outcomes_df['Rate'], errors='coerce')
    valid_rates = outcomes_df[outcomes_df['Rate_numeric'].notna()]

    summary = {
        'total_records': len(outcomes_df),
        'valid_rate_records': len(valid_rates),
        'unique_mcos': outcomes_df['ShortName'].nunique(),
        'unique_measures': outcomes_df['MeasureName'].nunique(),
        'years_covered': sorted(outcomes_df['ProductYear'].unique().tolist()),
        'mean_rate': valid_rates['Rate_numeric'].mean(),
        'median_rate': valid_rates['Rate_numeric'].median(),
        'std_rate': valid_rates['Rate_numeric'].std()
    }

    # Top measures by frequency
    measure_counts = outcomes_df['MeasureName'].value_counts().head(20)
    summary['top_measures'] = measure_counts.to_dict()

    return summary

def generate_extraction_summary():
    """Generate summary of text extraction results."""
    # Count processed files
    text_files = list(PROCESSED_TEXT_DIR.rglob('*.txt'))

    total_chars = 0
    file_sizes = []
    states_covered = set()

    for text_file in text_files:
        try:
            size = text_file.stat().st_size
            file_sizes.append(size)
            total_chars += size

            # Extract state from path
            parts = text_file.relative_to(PROCESSED_TEXT_DIR).parts
            if len(parts) > 0:
                states_covered.add(parts[0])
        except:
            pass

    return {
        'total_text_files': len(text_files),
        'total_characters': total_chars,
        'mean_file_size': np.mean(file_sizes) if file_sizes else 0,
        'median_file_size': np.median(file_sizes) if file_sizes else 0,
        'states_with_text': len(states_covered)
    }

def main():
    """Generate all manuscript data."""
    print("Generating manuscript data...")

    # Table 1: Study population
    table1 = generate_table1_study_population()
    table1.to_csv(OUTPUT_DIR / 'table1_study_population.csv', index=False)
    print(f"Table 1 saved: {len(table1)} rows")

    # Outcomes summary
    outcomes_summary = generate_outcomes_summary()
    with open(OUTPUT_DIR / 'outcomes_summary.json', 'w') as f:
        json.dump(outcomes_summary, f, indent=2, default=str)
    print(f"Outcomes summary saved: {outcomes_summary['unique_mcos']} MCOs, {outcomes_summary['unique_measures']} measures")

    # Extraction summary
    extraction_summary = generate_extraction_summary()
    with open(OUTPUT_DIR / 'extraction_summary.json', 'w') as f:
        json.dump(extraction_summary, f, indent=2)
    print(f"Extraction summary saved: {extraction_summary['total_text_files']} text files")

    print("\nManuscript data generation complete!")

if __name__ == '__main__':
    main()
