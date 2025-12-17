#!/usr/bin/env python3
"""
Full Analysis Pipeline - Medicaid MCO RFP Analysis
Runs all phases of the analysis pipeline.

This is the main entry point for the complete analysis.
"""

import os
import sys
import json
import csv
import re
import zipfile
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import anthropic
except ImportError:
    anthropic = None

# Configuration
RFP_BASE_DIR = Path("/Users/sanjaybasu/waymark-local/data/rfps")
OUTPUT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs")
PROCESSED_TEXT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/processed_text")
EXTRACTED_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/extracted_archives")

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_TEXT_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pypdf."""
    if pypdf is None:
        return None
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"  Error reading PDF {pdf_path.name}: {e}")
        return None


def extract_text_from_docx(docx_path):
    """Extract text from DOCX."""
    if DocxDocument is None:
        return None
    try:
        doc = DocxDocument(str(docx_path))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"  Error reading DOCX {docx_path.name}: {e}")
        return None


def unzip_archive(zip_path, extract_to):
    """Unzip an archive."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            return zip_ref.namelist()
    except Exception as e:
        print(f"  Error extracting {zip_path.name}: {e}")
        return []


def load_inventory():
    """Load the document inventory."""
    inventory_path = OUTPUT_DIR / 'document_inventory.json'
    with open(inventory_path) as f:
        return json.load(f)


def process_document_batch(documents, batch_name="batch"):
    """Process a batch of documents and extract text."""
    results = []

    for doc in documents:
        doc_path = Path(doc['full_path'])
        if not doc_path.exists():
            continue

        text = None
        if doc['format'] == 'pdf':
            text = extract_text_from_pdf(doc_path)
        elif doc['format'] in ['docx', 'doc']:
            text = extract_text_from_docx(doc_path)

        if text and len(text) > 100:
            # Save extracted text
            text_dir = PROCESSED_TEXT_DIR / doc['state']
            text_dir.mkdir(parents=True, exist_ok=True)
            text_path = text_dir / f"{doc_path.stem}.txt"

            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)

            results.append({
                'filename': doc['filename'],
                'state': doc['state'],
                'mco_name': doc['mco_name'],
                'year': doc['rfp_year'],
                'doc_type': doc['document_type'],
                'text_path': str(text_path),
                'text_length': len(text),
                'page_count': text.count('\n\n') + 1  # Rough estimate
            })

            print(f"  Processed: {doc['filename']} ({len(text):,} chars)")

    return results


def analyze_document_with_patterns(text, doc_info):
    """
    Analyze document using pattern matching to extract claims.
    This is a fallback/supplement to LLM analysis.
    """
    claims = []
    commitments = []
    partnerships = []

    # Patterns for quantitative claims
    percent_pattern = r'(\d+(?:\.\d+)?)\s*(?:percent|%)'
    improvement_pattern = r'(?:improved?|increased?|reduced?|decreased?|achieved?)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*(?:percent|%|percentage points?)'
    hedis_pattern = r'(?:HEDIS|CAHPS|NQF|CMS)\s+(?:measure\s+)?([A-Z0-9\-]+)'
    target_pattern = r'(?:target|goal|commit|achieve)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:percent|%)?'

    # Extract percentage-based claims
    for match in re.finditer(improvement_pattern, text, re.IGNORECASE):
        context_start = max(0, match.start() - 200)
        context_end = min(len(text), match.end() + 200)
        context = text[context_start:context_end]

        claims.append({
            'verbatim_text': context.strip()[:300],
            'change_magnitude': float(match.group(1)),
            'change_type': 'Q-PCT',
            'state': doc_info['state'],
            'mco_name': doc_info.get('mco_name'),
            'year': doc_info.get('year'),
            'doc_type': doc_info.get('doc_type'),
            'extraction_method': 'pattern'
        })

    # Extract HEDIS measures
    for match in re.finditer(hedis_pattern, text):
        context_start = max(0, match.start() - 150)
        context_end = min(len(text), match.end() + 150)
        context = text[context_start:context_end]

        claims.append({
            'verbatim_text': context.strip()[:300],
            'metric_name': match.group(1) if match.group(1) else match.group(0),
            'metric_steward': 'NCQA',
            'state': doc_info['state'],
            'mco_name': doc_info.get('mco_name'),
            'year': doc_info.get('year'),
            'doc_type': doc_info.get('doc_type'),
            'extraction_method': 'pattern'
        })

    # Extract commitments (future-oriented language)
    commitment_patterns = [
        r'(?:we\s+will|we\s+commit|we\s+shall|we\s+propose\s+to|our\s+goal\s+is\s+to)\s+([^.]+)',
        r'(?:by\s+year\s+\d|within\s+\d+\s+(?:months?|years?))[^.]+(?:achieve|reach|attain|improve)[^.]+',
    ]

    for pattern in commitment_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = match.group(0)[:300]
            commitments.append({
                'verbatim_text': context,
                'state': doc_info['state'],
                'mco_name': doc_info.get('mco_name'),
                'year': doc_info.get('year'),
                'doc_type': doc_info.get('doc_type'),
                'extraction_method': 'pattern'
            })

    # Extract partnerships
    partner_patterns = [
        r'(?:partner(?:ship|ed|ing)?|collaborat(?:e|ion|ing)|contract(?:ed)?)\s+with\s+([A-Z][^,.]+)',
        r'(?:in\s+partnership\s+with|working\s+with)\s+([A-Z][^,.]+)',
    ]

    for pattern in partner_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            partner_name = match.group(1).strip()[:100]
            partnerships.append({
                'partner_name': partner_name,
                'state': doc_info['state'],
                'mco_name': doc_info.get('mco_name'),
                'year': doc_info.get('year'),
                'doc_type': doc_info.get('doc_type'),
                'extraction_method': 'pattern'
            })

    return claims, commitments, partnerships


def run_phase1b_extraction():
    """Run Phase 1b: Extract and convert all documents."""
    print("\n" + "="*60)
    print("PHASE 1B: Document Extraction and Conversion")
    print("="*60)

    data = load_inventory()
    documents = data['inventory']

    # First, extract ZIPs
    zip_docs = [d for d in documents if d['compressed']]
    print(f"\nExtracting {len(zip_docs)} ZIP archives...")

    extraction_manifest = []
    for doc in zip_docs:
        zip_path = Path(doc['full_path'])
        extract_dir = EXTRACTED_DIR / doc['state'] / zip_path.stem
        extract_dir.mkdir(parents=True, exist_ok=True)

        files = unzip_archive(zip_path, extract_dir)
        for f in files:
            extraction_manifest.append({
                'source': doc['filename'],
                'state': doc['state'],
                'extracted_file': f
            })
        print(f"  {doc['filename']}: {len(files)} files")

    # Save extraction manifest
    manifest_df = pd.DataFrame(extraction_manifest)
    manifest_df.to_csv(OUTPUT_DIR / 'extraction_manifest.csv', index=False)

    # Now process non-compressed documents
    non_zip_docs = [d for d in documents if not d['compressed'] and d['format'] in ['pdf', 'docx', 'doc']]
    print(f"\nProcessing {len(non_zip_docs)} documents...")

    processed = process_document_batch(non_zip_docs)

    # Process extracted PDFs and DOCX
    extracted_docs = []
    for doc_path in EXTRACTED_DIR.rglob('*'):
        if doc_path.is_file() and doc_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
            state = doc_path.parts[len(EXTRACTED_DIR.parts)]
            extracted_docs.append({
                'filename': doc_path.name,
                'full_path': str(doc_path),
                'state': state,
                'format': doc_path.suffix.lower().replace('.', ''),
                'mco_name': None,
                'rfp_year': None,
                'document_type': 'extracted',
                'compressed': False
            })

    print(f"\nProcessing {len(extracted_docs)} extracted documents...")
    extracted_processed = process_document_batch(extracted_docs, "extracted")
    processed.extend(extracted_processed)

    # Save processing log
    processed_df = pd.DataFrame(processed)
    processed_df.to_csv(OUTPUT_DIR / 'document_processing_log.csv', index=False)

    print(f"\nPhase 1b complete: {len(processed)} documents processed")
    return processed


def run_phase2_analysis():
    """Run Phase 2: Document analysis with pattern extraction."""
    print("\n" + "="*60)
    print("PHASE 2: Per-Document Analysis")
    print("="*60)

    all_claims = []
    all_commitments = []
    all_partnerships = []

    # Get all processed text files
    text_files = list(PROCESSED_TEXT_DIR.rglob('*.txt'))
    print(f"\nAnalyzing {len(text_files)} text files...")

    for i, text_path in enumerate(text_files):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(text_files)}")

        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except:
            continue

        # Get document info from path
        state = text_path.parts[-2] if len(text_path.parts) > 1 else 'Unknown'
        doc_info = {
            'state': state,
            'mco_name': None,  # Could extract from filename
            'year': None,
            'doc_type': 'unknown'
        }

        claims, commitments, partnerships = analyze_document_with_patterns(text, doc_info)

        all_claims.extend(claims)
        all_commitments.extend(commitments)
        all_partnerships.extend(partnerships)

    # Save results
    claims_df = pd.DataFrame(all_claims)
    commitments_df = pd.DataFrame(all_commitments)
    partnerships_df = pd.DataFrame(all_partnerships)

    claims_df.to_csv(OUTPUT_DIR / 'claim_inventory_pattern.csv', index=False)
    commitments_df.to_csv(OUTPUT_DIR / 'commitment_inventory_pattern.csv', index=False)
    partnerships_df.to_csv(OUTPUT_DIR / 'partnership_inventory_pattern.csv', index=False)

    print(f"\nPhase 2 complete:")
    print(f"  Claims extracted: {len(all_claims)}")
    print(f"  Commitments extracted: {len(all_commitments)}")
    print(f"  Partnerships extracted: {len(all_partnerships)}")

    return all_claims, all_commitments, all_partnerships


def run_phase3_state_analysis(claims, commitments, partnerships):
    """Run Phase 3: Aggregate analysis per state."""
    print("\n" + "="*60)
    print("PHASE 3: State-Level Analysis")
    print("="*60)

    # State-level aggregations
    state_summary = defaultdict(lambda: {
        'total_claims': 0,
        'total_commitments': 0,
        'total_partnerships': 0,
        'unique_mcos': set()
    })

    for claim in claims:
        state = claim.get('state', 'Unknown')
        state_summary[state]['total_claims'] += 1
        if claim.get('mco_name'):
            state_summary[state]['unique_mcos'].add(claim['mco_name'])

    for commitment in commitments:
        state = commitment.get('state', 'Unknown')
        state_summary[state]['total_commitments'] += 1

    for partnership in partnerships:
        state = partnership.get('state', 'Unknown')
        state_summary[state]['total_partnerships'] += 1

    # Convert to DataFrame
    state_data = []
    for state, data in state_summary.items():
        state_data.append({
            'state': state,
            'total_claims': data['total_claims'],
            'total_commitments': data['total_commitments'],
            'total_partnerships': data['total_partnerships'],
            'unique_mcos': len(data['unique_mcos'])
        })

    state_df = pd.DataFrame(state_data)
    state_df.to_csv(OUTPUT_DIR / 'state_summary.csv', index=False)

    print(f"\nPhase 3 complete: {len(state_data)} states analyzed")
    return state_df


def run_phase4_validation():
    """Run Phase 4: Outcomes validation."""
    print("\n" + "="*60)
    print("PHASE 4: Outcomes Validation")
    print("="*60)

    # Load MCO Outcomes Data
    outcomes_path = RFP_BASE_DIR / 'MCO Outcomes Data.csv'
    outcomes_df = pd.read_csv(outcomes_path)

    print(f"Loaded outcomes data: {len(outcomes_df)} records")
    print(f"Unique measures: {outcomes_df['MeasureName'].nunique()}")
    print(f"Unique MCOs: {outcomes_df['ShortName'].nunique()}")

    # Summarize outcomes by MCO
    mco_outcomes = outcomes_df.groupby('ShortName').agg({
        'Rate': ['mean', 'count'],
        'MeasureName': 'nunique'
    }).reset_index()
    mco_outcomes.columns = ['mco_name', 'avg_rate', 'measure_count', 'unique_measures']

    mco_outcomes.to_csv(OUTPUT_DIR / 'mco_outcomes_summary.csv', index=False)

    # Load claims and attempt matching
    claims_path = OUTPUT_DIR / 'claim_inventory_pattern.csv'
    if claims_path.exists():
        claims_df = pd.read_csv(claims_path)

        # Create validation summary
        validation_summary = {
            'total_claims': len(claims_df),
            'claims_with_metrics': len(claims_df[claims_df['metric_name'].notna()]) if 'metric_name' in claims_df.columns else 0,
            'total_outcomes_records': len(outcomes_df),
            'unique_mcos_in_outcomes': outcomes_df['ShortName'].nunique(),
            'validated_at': datetime.now().isoformat()
        }

        with open(OUTPUT_DIR / 'validation_summary.json', 'w') as f:
            json.dump(validation_summary, f, indent=2)

    print(f"\nPhase 4 complete")
    return outcomes_df


def run_phase5_cross_state():
    """Run Phase 5: Cross-state analysis."""
    print("\n" + "="*60)
    print("PHASE 5: Cross-State Analysis")
    print("="*60)

    # Load all data
    inventory_path = OUTPUT_DIR / 'document_inventory.json'
    with open(inventory_path) as f:
        inventory = json.load(f)

    # National summary
    national_summary = {
        'total_states': inventory['statistics']['states'],
        'total_documents': inventory['statistics']['total_documents'],
        'documents_by_year': inventory['statistics']['documents_by_year'],
        'documents_by_type': inventory['statistics']['documents_by_type'],
        'unique_mcos': inventory['statistics']['unique_mcos'],
        'total_size_gb': round(inventory['statistics']['total_size_mb'] / 1024, 2),
        'analysis_date': datetime.now().isoformat()
    }

    # Load claims if available
    claims_path = OUTPUT_DIR / 'claim_inventory_pattern.csv'
    if claims_path.exists():
        claims_df = pd.read_csv(claims_path)
        national_summary['total_claims_extracted'] = len(claims_df)

        # Claims by state
        if 'state' in claims_df.columns:
            claims_by_state = claims_df['state'].value_counts().to_dict()
            national_summary['claims_by_state'] = claims_by_state

    with open(OUTPUT_DIR / 'national_summary.json', 'w') as f:
        json.dump(national_summary, f, indent=2)

    print(f"\nPhase 5 complete: National summary generated")
    return national_summary


def run_phase6_dataverse():
    """Run Phase 6: Prepare Harvard Dataverse package."""
    print("\n" + "="*60)
    print("PHASE 6: Dataverse Package Preparation")
    print("="*60)

    dataverse_dir = OUTPUT_DIR / 'dataverse_package'
    dataverse_dir.mkdir(parents=True, exist_ok=True)

    # Copy key files to dataverse package
    files_to_include = [
        'document_inventory.csv',
        'claim_inventory_pattern.csv',
        'commitment_inventory_pattern.csv',
        'partnership_inventory_pattern.csv',
        'state_summary.csv',
        'mco_outcomes_summary.csv',
        'national_summary.json',
        'validation_summary.json'
    ]

    for filename in files_to_include:
        src = OUTPUT_DIR / filename
        if src.exists():
            import shutil
            shutil.copy(src, dataverse_dir / filename)
            print(f"  Included: {filename}")

    # Create data dictionary
    data_dictionary = [
        {'variable': 'state', 'file': 'document_inventory.csv', 'definition': 'US state name', 'type': 'string'},
        {'variable': 'filename', 'file': 'document_inventory.csv', 'definition': 'Original document filename', 'type': 'string'},
        {'variable': 'document_type', 'file': 'document_inventory.csv', 'definition': 'Type of document (rfp, proposal, scoring, contract, award, etc.)', 'type': 'categorical'},
        {'variable': 'mco_name', 'file': 'document_inventory.csv', 'definition': 'Managed Care Organization name if identifiable', 'type': 'string'},
        {'variable': 'rfp_year', 'file': 'document_inventory.csv', 'definition': 'Year of RFP issuance', 'type': 'integer'},
        {'variable': 'verbatim_text', 'file': 'claim_inventory_pattern.csv', 'definition': 'Exact text excerpt containing the claim', 'type': 'string'},
        {'variable': 'change_magnitude', 'file': 'claim_inventory_pattern.csv', 'definition': 'Numeric magnitude of claimed change', 'type': 'float'},
        {'variable': 'change_type', 'file': 'claim_inventory_pattern.csv', 'definition': 'Type of quantification (Q-PCT, Q-ABS, Q-PPT, Q-TGT, Q-NONE)', 'type': 'categorical'},
        {'variable': 'metric_name', 'file': 'claim_inventory_pattern.csv', 'definition': 'Name of quality metric (e.g., HEDIS measure)', 'type': 'string'},
        {'variable': 'partner_name', 'file': 'partnership_inventory_pattern.csv', 'definition': 'Name of partner organization', 'type': 'string'},
    ]

    dd_df = pd.DataFrame(data_dictionary)
    dd_df.to_csv(dataverse_dir / 'data_dictionary.csv', index=False)

    print(f"\nPhase 6 complete: Dataverse package prepared in {dataverse_dir}")
    return dataverse_dir


def main():
    """Run the full analysis pipeline."""
    print("="*60)
    print("MEDICAID MCO RFP ANALYSIS PIPELINE")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}")

    # Phase 1b: Extract and convert documents
    processed = run_phase1b_extraction()

    # Phase 2: Analyze documents
    claims, commitments, partnerships = run_phase2_analysis()

    # Phase 3: State-level analysis
    state_df = run_phase3_state_analysis(claims, commitments, partnerships)

    # Phase 4: Outcomes validation
    outcomes_df = run_phase4_validation()

    # Phase 5: Cross-state analysis
    national_summary = run_phase5_cross_state()

    # Phase 6: Dataverse package
    dataverse_dir = run_phase6_dataverse()

    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"End time: {datetime.now().isoformat()}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Dataverse package: {dataverse_dir}")


if __name__ == '__main__':
    main()
