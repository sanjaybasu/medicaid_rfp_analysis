#!/usr/bin/env python3
"""
Phase 1b: Document Extraction and Conversion
Medicaid MCO RFP Analysis Pipeline

This script:
1. Unzips all compressed archives
2. Converts PDFs and DOCX files to text
3. Creates a manifest of processed documents
"""

import os
import zipfile
import subprocess
import json
import csv
from pathlib import Path
from datetime import datetime
import shutil

# Configuration
RFP_BASE_DIR = Path("/Users/sanjaybasu/waymark-local/data/rfps")
OUTPUT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs")
PROCESSED_TEXT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/processed_text")
EXTRACTED_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/extracted_archives")


def unzip_archive(zip_path, extract_to):
    """Unzip an archive and return list of extracted files."""
    extracted_files = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files before extraction
            file_list = zip_ref.namelist()
            zip_ref.extractall(extract_to)
            extracted_files = [str(extract_to / f) for f in file_list]
            print(f"  Extracted {len(file_list)} files from {zip_path.name}")
    except Exception as e:
        print(f"  ERROR extracting {zip_path.name}: {e}")
    return extracted_files


def convert_pdf_to_text(pdf_path, output_path):
    """Convert PDF to text using pdftotext."""
    try:
        # Try pdftotext first
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), str(output_path)],
            capture_output=True,
            timeout=120
        )
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  pdftotext failed for {pdf_path.name}: {e}")

    # Fallback: try using Python libraries
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"  pypdf failed for {pdf_path.name}: {e}")

    return False


def convert_docx_to_text(docx_path, output_path):
    """Convert DOCX to text."""
    try:
        # Try pandoc first
        result = subprocess.run(
            ['pandoc', str(docx_path), '-o', str(output_path), '--wrap=none'],
            capture_output=True,
            timeout=60
        )
        if result.returncode == 0 and output_path.exists():
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  pandoc failed for {docx_path.name}: {e}")

    # Fallback: try python-docx
    try:
        from docx import Document
        doc = Document(str(docx_path))
        text = "\n".join([para.text for para in doc.paragraphs])
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"  python-docx failed for {docx_path.name}: {e}")

    return False


def process_all_archives():
    """Process all ZIP files in the corpus."""
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    # Load inventory
    inventory_path = OUTPUT_DIR / 'document_inventory.json'
    with open(inventory_path) as f:
        data = json.load(f)

    zip_files = [d for d in data['inventory'] if d['compressed']]
    extraction_manifest = []

    print(f"\nProcessing {len(zip_files)} ZIP archives...")

    for zip_doc in zip_files:
        zip_path = Path(zip_doc['full_path'])
        state = zip_doc['state']

        # Create extraction directory
        extract_dir = EXTRACTED_DIR / state / zip_path.stem
        extract_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nExtracting: {zip_path.name}")
        extracted = unzip_archive(zip_path, extract_dir)

        for file_path in extracted:
            extraction_manifest.append({
                'source_archive': zip_doc['filename'],
                'state': state,
                'extracted_file': os.path.basename(file_path),
                'extracted_path': file_path,
                'extracted_at': datetime.now().isoformat()
            })

    # Save extraction manifest
    manifest_path = OUTPUT_DIR / 'extraction_manifest.csv'
    with open(manifest_path, 'w', newline='') as f:
        if extraction_manifest:
            writer = csv.DictWriter(f, fieldnames=extraction_manifest[0].keys())
            writer.writeheader()
            writer.writerows(extraction_manifest)

    print(f"\nExtraction manifest saved to {manifest_path}")
    print(f"Total files extracted: {len(extraction_manifest)}")

    return extraction_manifest


def convert_documents_to_text():
    """Convert all PDF and DOCX files to text."""
    PROCESSED_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    conversion_log = []

    # Process original PDFs and DOCX files
    for doc_path in RFP_BASE_DIR.rglob('*'):
        if not doc_path.is_file():
            continue

        suffix = doc_path.suffix.lower()
        if suffix not in ['.pdf', '.docx', '.doc']:
            continue

        # Determine output path
        rel_path = doc_path.relative_to(RFP_BASE_DIR)
        output_path = PROCESSED_TEXT_DIR / rel_path.with_suffix('.txt')
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            continue

        print(f"Converting: {doc_path.name}")

        success = False
        if suffix == '.pdf':
            success = convert_pdf_to_text(doc_path, output_path)
        elif suffix in ['.docx', '.doc']:
            success = convert_docx_to_text(doc_path, output_path)

        conversion_log.append({
            'source_file': str(doc_path),
            'output_file': str(output_path) if success else None,
            'success': success,
            'converted_at': datetime.now().isoformat()
        })

    # Process extracted files from ZIPs
    if EXTRACTED_DIR.exists():
        for doc_path in EXTRACTED_DIR.rglob('*'):
            if not doc_path.is_file():
                continue

            suffix = doc_path.suffix.lower()
            if suffix not in ['.pdf', '.docx', '.doc']:
                continue

            rel_path = doc_path.relative_to(EXTRACTED_DIR)
            output_path = PROCESSED_TEXT_DIR / 'extracted' / rel_path.with_suffix('.txt')
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if output_path.exists():
                continue

            print(f"Converting extracted: {doc_path.name}")

            success = False
            if suffix == '.pdf':
                success = convert_pdf_to_text(doc_path, output_path)
            elif suffix in ['.docx', '.doc']:
                success = convert_docx_to_text(doc_path, output_path)

            conversion_log.append({
                'source_file': str(doc_path),
                'output_file': str(output_path) if success else None,
                'success': success,
                'converted_at': datetime.now().isoformat()
            })

    # Save conversion log
    log_path = OUTPUT_DIR / 'conversion_log.csv'
    with open(log_path, 'w', newline='') as f:
        if conversion_log:
            writer = csv.DictWriter(f, fieldnames=conversion_log[0].keys())
            writer.writeheader()
            writer.writerows(conversion_log)

    successful = sum(1 for c in conversion_log if c['success'])
    print(f"\nConversion complete: {successful}/{len(conversion_log)} files converted")
    print(f"Conversion log saved to {log_path}")


if __name__ == '__main__':
    print("="*60)
    print("Phase 1b: Document Extraction and Conversion")
    print("="*60)

    print("\nStep 1: Extracting ZIP archives...")
    process_all_archives()

    print("\nStep 2: Converting documents to text...")
    convert_documents_to_text()

    print("\n" + "="*60)
    print("Phase 1b Complete")
    print("="*60)
