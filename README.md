# Medicaid MCO RFP Analysis Pipeline

[![DOI](https://img.shields.io/badge/DOI-10.7910%2FDVN%2FXXXXXX-blue)](https://doi.org/10.7910/DVN/XXXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Large-Scale Analysis of Medicaid Managed Care Procurement Claims

This repository contains the reproducible analysis pipeline for:

> **Basu S. Evaluating Medicaid Managed Care Organization Accountability: A Large-Scale Analysis of RFP Response Claims Across 32 US States.** *Health Affairs.* 2025.

## Key Findings

- **55,914** quantitative claims extracted from **2,833** documents
- **55,364** partnership references identified
- **32** US states represented (2017-2024)
- **534** MCOs linked to HEDIS outcomes data

## Repository Structure

```
medicaid_rfp_analysis/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── scripts/
│   ├── run_full_analysis.py          # Main pipeline orchestrator
│   ├── phase1_document_inventory.py  # Document cataloging
│   ├── phase1b_extract_documents.py  # Text extraction (PDF/DOCX)
│   ├── phase2_document_analysis.py   # Claim extraction & coding
│   ├── interim_analysis.py           # Pattern-based extraction
│   └── generate_manuscript_data.py   # Generate tables/figures
├── data/
│   └── README.md             # Data acquisition instructions
├── outputs/
│   ├── README.md             # Output file descriptions
│   ├── sample_claims.csv     # Sample output (100 rows)
│   └── sample_claim_summary.json
└── docs/
    ├── codebook.md           # Variable definitions & coding scheme
    └── data_dictionary.csv   # Complete data dictionary
```

## Quick Start

### 1. Installation

```bash
git clone https://github.com/sanjaybasu/medicaid_rfp_analysis.git
cd medicaid_rfp_analysis
pip install -r requirements.txt
```

### 2. Data Setup

Place source documents in `data/rfps/[State]/`:
```
data/rfps/
├── California/
│   ├── CA_Medi-Cal_RFP_2023.pdf
│   └── ...
├── Texas/
└── ...
```

See `data/README.md` for acquisition instructions.

### 3. Run Analysis

```bash
# Full pipeline (requires source documents)
python scripts/run_full_analysis.py

# Pattern-based extraction only (faster)
python scripts/interim_analysis.py
```

## Pipeline Phases

| Phase | Script | Description |
|-------|--------|-------------|
| 1 | `phase1_document_inventory.py` | Catalog documents, extract metadata |
| 1b | `phase1b_extract_documents.py` | Unzip archives, convert PDF/DOCX to text |
| 2 | `phase2_document_analysis.py` | Extract claims using patterns + LLM |
| 3+ | `run_full_analysis.py` | Orchestrate all phases |

## Data Access

### Pre-processed Data
The complete extracted dataset is available on Harvard Dataverse:
- **DOI**: [10.7910/DVN/XXXXXX](https://doi.org/10.7910/DVN/XXXXXX)
- Includes: 55,914 claims, 55,364 partnerships, document inventory

### Source Documents
Original procurement documents are publicly available from:
- State Medicaid agency websites
- State procurement portals
- FOIA requests (some states)

## Output Files

| File | Records | Description |
|------|---------|-------------|
| `claims_extracted.csv` | 55,914 | All quantitative claims |
| `partnerships_extracted.csv` | 55,364 | Partnership references |
| `document_inventory.csv` | 265 | Source document catalog |
| `claim_summary.json` | — | Aggregate statistics |

## Methods Summary

### Claim Extraction Patterns
```python
patterns = [
    (r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*(?:improvement|...)', 'improvement'),
    (r'(?:HEDIS|CAHPS|NQF)\s+(?:measure\s+)?([A-Z0-9\-]+)', 'metric'),
    # ... see scripts/interim_analysis.py for complete patterns
]
```

### Validation
- Inter-rater reliability: Cohen's kappa > 0.85
- Manual review of 200 randomly sampled claims
- HEDIS outcomes linkage for 534 MCOs

## Citation

```bibtex
@article{basu2025medicaid,
  title={Evaluating Medicaid Managed Care Organization Accountability:
         A Large-Scale Analysis of RFP Response Claims Across 32 US States},
  author={Basu, Sanjay},
  journal={Health Affairs},
  year={2025}
}
```

## License

- **Code**: MIT License
- **Data**: CC BY 4.0

## Contact

Sanjay Basu, MD, PhD
Waymark
sanjay.basu@waymarkcare.org

## Acknowledgments

This research was funded by Waymark.
