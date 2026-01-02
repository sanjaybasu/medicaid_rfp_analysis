# Medicaid MCO RFP Analysis Pipeline

[![DOI](https://img.shields.io/badge/DOI-10.7910%2FDVN%2F6EFL00-blue)](https://doi.org/10.7910/DVN/6EFL00)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Large Language Model Analysis of Medicaid Managed Care Procurement Accountability

This repository contains the reproducible analysis pipeline for:

> **Basu S, Fleming A, Morgan J, Batniji R. Evaluating Medicaid Managed Care Organization Accountability: Large Language Model Analysis of RFP Response Claims Across 32 US States. 2026.


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
│   ├── thematic_analysis.py          # Thematic claim extraction (RAG + LLM)
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

# Thematic analysis with RAG + LLM
python scripts/thematic_analysis.py

# Pattern-based extraction only (faster)
python scripts/interim_analysis.py
```

## Pipeline Phases

| Phase | Script | Description |
|-------|--------|-------------|
| 1 | `phase1_document_inventory.py` | Catalog documents, extract metadata |
| 1b | `phase1b_extract_documents.py` | Unzip archives, convert PDF/DOCX to text |
| 2 | `phase2_document_analysis.py` | Extract claims using patterns + LLM |
| 3 | `thematic_analysis.py` | RAG-based thematic extraction (6 domains) |
| 4 | `run_full_analysis.py` | Orchestrate all phases |

## Data Access

### Pre-processed Data
The complete extracted dataset is available on Harvard Dataverse:
- **DOI**: [10.7910/DVN/6EFL00](https://doi.org/10.7910/DVN/6EFL00)
- Includes: 372,283 thematic claims, theme taxonomy, concordance analysis, temporal trends

### Source Documents
Original procurement documents are publicly available from:
- State Medicaid agency websites
- State procurement portals
- FOIA requests (some states)

## Output Files

| File | Records | Description |
|------|---------|-------------|
| `thematic_claims.csv` | 372,283 | All thematic accountability claims |
| `exhibit2_theme_taxonomy.csv` | 36 | Theme and subcategory distribution |
| `exhibit3_temporal_by_theme.csv` | 48 | Annual claim volumes by theme |
| `exhibit4_regional_themes.csv` | 30 | Regional distribution by theme |
| `exhibit5_rfp_mco_concordance.csv` | 179 | RFP-MCO concordance ratios |
| `document_inventory.csv` | 265 | Source document catalog |

## Methods Summary

### Thematic Domains (6 categories, 36 subcategories)

1. **Chronic Disease Management** (28.9%): diabetes, behavioral health, maternal health
2. **LTSS/Dual Eligibles** (18.0%): long-term services, nursing facilities
3. **Health Equity** (14.1%): racial/ethnic disparities, language access
4. **Technology** (13.1%): telehealth, AI/predictive analytics
5. **Workforce** (13.1%): provider recruitment, CHWs
6. **SDOH** (12.8%): food insecurity, housing, transportation

### Extraction Pipeline

Claims extracted using retrieval-augmented generation (RAG) with Claude Sonnet 4.5:
- Document chunking with vector embeddings
- JSON schema-constrained outputs
- Verbatim text extraction (≤300 chars)
- Temperature=0.0 for deterministic outputs

### Hallucination Mitigation

- RAG grounding with explicit source attribution
- Automated source verification
- 10% manual validation (97.3% accuracy)

### Validation
- Inter-rater reliability: Cohen's κ = 0.86
- Machine learning sensitivity: 0.89
- Manual review of 200 randomly sampled claims

## Citation

```bibtex
@article{basu2025medicaid,
  title={Evaluating Medicaid Managed Care Organization Accountability:
         Large Language Model Analysis of RFP Response Claims Across 32 US States},
  author={Basu, Sanjay and Fleming, Alex and Morgan, John and Batniji, Rajaie},
  year={2026}
}
```

## License

- **Code**: MIT License
- **Data**: CC BY 4.0

## Contact

Sanjay Basu, MD, PhD
Waymark / University of California, San Francisco
sanjay.basu@waymarkcare.org
