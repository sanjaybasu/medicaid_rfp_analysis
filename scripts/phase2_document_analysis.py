#!/usr/bin/env python3
"""
Phase 2: Per-Document Analysis
Medicaid MCO RFP Analysis Pipeline

This script analyzes RFPs and MCO proposals to extract:
1. Quantitative claims about health outcomes
2. Future commitments/promises
3. Third-party partnerships
4. Peer-reviewed citations
5. Code frequencies

Uses Claude API for LLM-assisted extraction.
"""

import os
import json
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import time

try:
    import anthropic
except ImportError:
    print("Warning: anthropic package not installed. Install with: pip install anthropic")
    anthropic = None

# Configuration
OUTPUT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs")
PROCESSED_TEXT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/processed_text")
RFP_BASE_DIR = Path("/Users/sanjaybasu/waymark-local/data/rfps")

# Coding scheme from protocol
DOMAIN_CODES = {
    'VBC': 'Value-Based Care',
    'PH': 'Population Health',
    'AC': 'Access to Care',
    'CC': 'Care Coordination',
    'QM': 'Quality Metrics',
    'PM': 'Payment Models',
    'HIT': 'Health Information Technology',
    'WD': 'Workforce Development'
}

CLAIM_TYPE_CODES = {
    'HIST': 'Historical Performance',
    'PROJ': 'Projected Performance',
    'COMP': 'Comparative Performance',
    'METH': 'Methodology Description'
}

EVIDENCE_TYPE_CODES = {
    'PR': 'Peer-Reviewed',
    'CG': 'Control Group',
    'PP': 'Pre-Post',
    'INT': 'Internal Analysis',
    'EXT': 'External Validation',
    'NONE': 'No Evidence'
}

CLINICAL_AREA_CODES = {
    'MAT': 'Maternity',
    'PED': 'Pediatrics',
    'BH': 'Behavioral Health',
    'CHR': 'Chronic Disease',
    'PCP': 'Primary Care',
    'HOSP': 'Hospital Utilization',
    'RX': 'Pharmacy'
}

QUANTIFICATION_CODES = {
    'Q-ABS': 'Absolute Number',
    'Q-PCT': 'Percentage',
    'Q-PPT': 'Percentage Points',
    'Q-TGT': 'Target with Timeline',
    'Q-NONE': 'Unquantified'
}

# Prompt templates
CLAIM_EXTRACTION_PROMPT = """You are analyzing a Medicaid MCO proposal or RFP document for a research study on accountability claims.

Document: {state} {mco_name} {year} {doc_type}
Section text (partial):
{section_text}

Extract ALL quantitative claims about health outcomes. A quantitative claim includes:
- Specific numeric improvements (percentages, counts, rates)
- Comparisons to benchmarks or prior periods
- Targets with specific values
- Quality measure results (HEDIS, etc.)

For each claim found, extract in this JSON format:
{{
  "verbatim_text": "[exact quote, max 300 chars]",
  "domain_code": "[VBC|PH|AC|CC|QM|PM|HIT|WD]",
  "clinical_area": "[MAT|PED|BH|CHR|PCP|HOSP|RX|NONE]",
  "claim_type": "[HIST|PROJ|COMP|METH]",
  "metric_name": "[specific measure name if stated]",
  "metric_steward": "[NCQA|CMS|State|Internal|Other]",
  "baseline_value": [number or null],
  "baseline_year": [year or null],
  "outcome_value": [number or null],
  "outcome_year": [year or null],
  "change_type": "[Q-ABS|Q-PCT|Q-PPT|Q-TGT|Q-NONE]",
  "change_magnitude": [number or null],
  "change_direction": "[increase|decrease|maintain|NA]",
  "timeline": "[timeframe described or null]",
  "evidence_type": "[PR|CG|PP|INT|EXT|NONE]",
  "citation": "[if peer-reviewed, citation text]",
  "partners": ["list of third parties mentioned"],
  "confidence": "[HIGH|MEDIUM|LOW]"
}}

Return ONLY a JSON array of claims. If no quantitative claims in section, return empty array [].
Do not include any explanation, just the JSON array."""

COMMITMENT_EXTRACTION_PROMPT = """You are analyzing a Medicaid MCO proposal to extract future performance commitments.

Document: {state} {mco_name} {year} {doc_type}
Section text (partial):
{section_text}

Extract ALL future performance commitments or promises. Look for:
- "We will achieve..."
- "Our target is..."
- "By Year X, we commit to..."
- Performance guarantees
- Quality improvement targets

For each commitment, extract:
{{
  "verbatim_text": "[exact quote]",
  "domain_code": "[VBC|PH|AC|CC|QM|PM|HIT|WD]",
  "clinical_area": "[MAT|PED|BH|CHR|PCP|HOSP|RX|NONE]",
  "metric_name": "[specific measure]",
  "metric_steward": "[NCQA|CMS|State|Internal|Other]",
  "current_baseline": "[if stated, null otherwise]",
  "target_value": "[specific target]",
  "target_type": "[Q-ABS|Q-PCT|Q-PPT|Q-TGT]",
  "deadline": "[when to be achieved]",
  "contract_year": "[Year 1|Year 2|Year 3|etc or null]",
  "consequence": "[penalty or incentive if stated, null otherwise]",
  "confidence": "[HIGH|MEDIUM|LOW]"
}}

Return ONLY a JSON array. If no commitments found, return [].
Do not include any explanation, just the JSON array."""

PARTNERSHIP_EXTRACTION_PROMPT = """You are analyzing a Medicaid MCO proposal to identify third-party partnerships.

Document: {state} {mco_name} {year} {doc_type}
Section text (partial):
{section_text}

Extract ALL mentioned partnerships with external organizations. Include:
- Community-based organizations (CBOs)
- Health systems / provider groups
- Technology vendors
- Academic institutions
- Government agencies

For each partnership:
{{
  "partner_name": "[organization name]",
  "partner_type": "[P-CBO|P-GOV|P-ACAD|P-TECH|P-PROV]",
  "relationship": "[contracted|affiliated|collaborative|other]",
  "services": ["list of services provided"],
  "outcomes_attributed": "[any outcomes/metrics attributed to partnership]",
  "geographic_scope": "[state|regional|national|local]",
  "confidence": "[HIGH|MEDIUM|LOW]"
}}

Return ONLY a JSON array. If no partnerships found, return [].
Do not include any explanation, just the JSON array."""


def chunk_text(text: str, chunk_size: int = 8000, overlap: int = 500) -> List[str]:
    """Split text into overlapping chunks for processing."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def call_claude_api(prompt: str, max_retries: int = 3) -> Optional[str]:
    """Call Claude API with retry logic."""
    if anthropic is None:
        return None

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"API call failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    return None


def parse_json_response(response: str) -> List[Dict]:
    """Parse JSON from Claude response, handling potential formatting issues."""
    if not response:
        return []

    # Try to find JSON array in response
    try:
        # Direct parse
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from response
    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    return []


def extract_claims_from_document(
    text: str,
    state: str,
    mco_name: str,
    year: str,
    doc_type: str
) -> List[Dict]:
    """Extract all quantitative claims from a document."""
    chunks = chunk_text(text)
    all_claims = []

    for i, chunk in enumerate(chunks):
        prompt = CLAIM_EXTRACTION_PROMPT.format(
            state=state,
            mco_name=mco_name or 'Unknown',
            year=year or 'Unknown',
            doc_type=doc_type,
            section_text=chunk
        )

        response = call_claude_api(prompt)
        claims = parse_json_response(response)

        for claim in claims:
            claim['chunk_index'] = i
            claim['state'] = state
            claim['mco_name'] = mco_name
            claim['year'] = year
            claim['doc_type'] = doc_type
            all_claims.append(claim)

        print(f"  Chunk {i+1}/{len(chunks)}: {len(claims)} claims found")

    return all_claims


def extract_commitments_from_document(
    text: str,
    state: str,
    mco_name: str,
    year: str,
    doc_type: str
) -> List[Dict]:
    """Extract all future commitments from a document."""
    chunks = chunk_text(text)
    all_commitments = []

    for i, chunk in enumerate(chunks):
        prompt = COMMITMENT_EXTRACTION_PROMPT.format(
            state=state,
            mco_name=mco_name or 'Unknown',
            year=year or 'Unknown',
            doc_type=doc_type,
            section_text=chunk
        )

        response = call_claude_api(prompt)
        commitments = parse_json_response(response)

        for commitment in commitments:
            commitment['chunk_index'] = i
            commitment['state'] = state
            commitment['mco_name'] = mco_name
            commitment['year'] = year
            commitment['doc_type'] = doc_type
            all_commitments.append(commitment)

    return all_commitments


def extract_partnerships_from_document(
    text: str,
    state: str,
    mco_name: str,
    year: str,
    doc_type: str
) -> List[Dict]:
    """Extract all partnerships from a document."""
    chunks = chunk_text(text)
    all_partnerships = []

    for i, chunk in enumerate(chunks):
        prompt = PARTNERSHIP_EXTRACTION_PROMPT.format(
            state=state,
            mco_name=mco_name or 'Unknown',
            year=year or 'Unknown',
            doc_type=doc_type,
            section_text=chunk
        )

        response = call_claude_api(prompt)
        partnerships = parse_json_response(response)

        for partnership in partnerships:
            partnership['chunk_index'] = i
            partnership['state'] = state
            partnership['mco_name'] = mco_name
            partnership['year'] = year
            partnership['doc_type'] = doc_type
            all_partnerships.append(partnership)

    return all_partnerships


def calculate_code_frequencies(claims: List[Dict]) -> Dict:
    """Calculate frequency of each code type."""
    frequencies = {
        'domain_counts': {code: 0 for code in DOMAIN_CODES},
        'clinical_area_counts': {code: 0 for code in CLINICAL_AREA_CODES},
        'evidence_type_counts': {code: 0 for code in EVIDENCE_TYPE_CODES},
        'claim_type_counts': {code: 0 for code in CLAIM_TYPE_CODES},
        'quantification_counts': {code: 0 for code in QUANTIFICATION_CODES},
    }

    for claim in claims:
        domain = claim.get('domain_code')
        if domain in frequencies['domain_counts']:
            frequencies['domain_counts'][domain] += 1

        clinical = claim.get('clinical_area')
        if clinical in frequencies['clinical_area_counts']:
            frequencies['clinical_area_counts'][clinical] += 1

        evidence = claim.get('evidence_type')
        if evidence in frequencies['evidence_type_counts']:
            frequencies['evidence_type_counts'][evidence] += 1

        claim_type = claim.get('claim_type')
        if claim_type in frequencies['claim_type_counts']:
            frequencies['claim_type_counts'][claim_type] += 1

        quant = claim.get('change_type')
        if quant in frequencies['quantification_counts']:
            frequencies['quantification_counts'][quant] += 1

    return frequencies


def process_all_documents():
    """Process all documents in the corpus."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load inventory
    inventory_path = OUTPUT_DIR / 'document_inventory.json'
    with open(inventory_path) as f:
        data = json.load(f)

    # Filter to proposals and RFPs (prioritize proposals for claim extraction)
    proposals = [d for d in data['inventory']
                 if d['document_type'] in ['proposal', 'rfp']
                 and not d['compressed']]

    print(f"Processing {len(proposals)} documents...")

    all_claims = []
    all_commitments = []
    all_partnerships = []
    document_analyses = []

    for i, doc in enumerate(proposals):
        print(f"\n[{i+1}/{len(proposals)}] Processing: {doc['filename']}")

        # Find text file
        text_path = PROCESSED_TEXT_DIR / doc['state'] / Path(doc['filename']).with_suffix('.txt')

        if not text_path.exists():
            # Try original location
            orig_path = Path(doc['full_path'])
            if orig_path.suffix.lower() == '.pdf':
                print(f"  Text file not found: {text_path}")
                continue

        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            print(f"  Error reading {text_path}: {e}")
            continue

        if len(text) < 100:
            print(f"  Document too short ({len(text)} chars), skipping")
            continue

        # Extract claims
        claims = extract_claims_from_document(
            text,
            doc['state'],
            doc['mco_name'],
            str(doc['rfp_year']),
            doc['document_type']
        )
        all_claims.extend(claims)

        # Extract commitments
        commitments = extract_commitments_from_document(
            text,
            doc['state'],
            doc['mco_name'],
            str(doc['rfp_year']),
            doc['document_type']
        )
        all_commitments.extend(commitments)

        # Extract partnerships
        partnerships = extract_partnerships_from_document(
            text,
            doc['state'],
            doc['mco_name'],
            str(doc['rfp_year']),
            doc['document_type']
        )
        all_partnerships.extend(partnerships)

        # Calculate code frequencies
        frequencies = calculate_code_frequencies(claims)

        # Store document analysis
        doc_analysis = {
            'filename': doc['filename'],
            'state': doc['state'],
            'mco_name': doc['mco_name'],
            'year': doc['rfp_year'],
            'doc_type': doc['document_type'],
            'total_claims': len(claims),
            'total_commitments': len(commitments),
            'total_partnerships': len(partnerships),
            'code_frequencies': frequencies,
            'analyzed_at': datetime.now().isoformat()
        }
        document_analyses.append(doc_analysis)

        print(f"  Claims: {len(claims)}, Commitments: {len(commitments)}, Partnerships: {len(partnerships)}")

        # Save intermediate results periodically
        if (i + 1) % 5 == 0:
            save_results(all_claims, all_commitments, all_partnerships, document_analyses)

    # Final save
    save_results(all_claims, all_commitments, all_partnerships, document_analyses)

    return all_claims, all_commitments, all_partnerships, document_analyses


def save_results(claims, commitments, partnerships, analyses):
    """Save analysis results to files."""
    # Save claims
    claims_path = OUTPUT_DIR / 'claim_inventory_full.json'
    with open(claims_path, 'w') as f:
        json.dump(claims, f, indent=2)

    # Save commitments
    commitments_path = OUTPUT_DIR / 'promise_inventory.json'
    with open(commitments_path, 'w') as f:
        json.dump(commitments, f, indent=2)

    # Save partnerships
    partnerships_path = OUTPUT_DIR / 'partnership_inventory.json'
    with open(partnerships_path, 'w') as f:
        json.dump(partnerships, f, indent=2)

    # Save document analyses
    analyses_path = OUTPUT_DIR / 'document_analyses.json'
    with open(analyses_path, 'w') as f:
        json.dump(analyses, f, indent=2)

    print(f"\nResults saved: {len(claims)} claims, {len(commitments)} commitments, {len(partnerships)} partnerships")


if __name__ == '__main__':
    print("="*60)
    print("Phase 2: Per-Document Analysis")
    print("="*60)

    if anthropic is None:
        print("\nWARNING: anthropic package not installed.")
        print("This script requires the Anthropic API for document analysis.")
        print("Install with: pip install anthropic")
        print("Set ANTHROPIC_API_KEY environment variable.")
    else:
        claims, commitments, partnerships, analyses = process_all_documents()

        print("\n" + "="*60)
        print("Phase 2 Complete")
        print("="*60)
        print(f"Total claims extracted: {len(claims)}")
        print(f"Total commitments extracted: {len(commitments)}")
        print(f"Total partnerships extracted: {len(partnerships)}")
        print(f"Documents analyzed: {len(analyses)}")
