# Medicaid Managed Care Procurement Analysis

[![DOI](https://img.shields.io/badge/DOI-10.7910%2FDVN%2F6EFL00-blue)](https://doi.org/10.7910/DVN/6EFL00)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Medicaid Managed Care Procurement Reveals Systematic Overemphasis of Technology and Equity Performance Claims Across 32 States

**Authors:** Sanjay Basu, Alex Fleming, John Morgan, Rajaie Batniji

**Manuscript status:** Under review, INQUIRY: The Journal of Health Care Organization, Provision, and Financing (R2 revision submitted April 2026)

---

## Overview

This repository contains all code for reproducing analyses from our study examining performance claims in Medicaid managed care procurement documents across 32 US states (2017-2024). Using retrieval-augmented generation (RAG) with large language models, we extracted and analyzed 372,283 performance claims from 265 source documents to evaluate alignment between MCO commitments and state priorities.


## Repository Structure

```
medicaid_rfp_analysis/
├── scripts/                          # Analysis code
│   ├── phase1_document_inventory.py       # Document cataloging
│   ├── phase1b_extract_documents.py       # Text extraction from PDFs/ZIPs
│   ├── phase2_document_analysis.py        # Claim extraction using RAG+LLM
│   ├── thematic_analysis.py               # Thematic classification
│   ├── generate_manuscript_data.py        # Table/figure generation
│   └── normalized_concordance_analysis.py  # Normalized concordance analyses
├── data/                             # Source documents (not included - see below)
│   └── README.md                     # Instructions for obtaining source data
├── outputs/                          # Analysis results
│   ├── normalized_concordance_by_theme.csv
│   ├── covid_comparison_stratified.csv
│   ├── document_count_clarification.json
│   ├── sample_claims.csv
│   └── sample_claim_summary.json
├── docs/                             # Documentation
│   ├── codebook.md                   # Variable definitions
│   └── data_dictionary.csv           # Data dictionary
├── tests/                            # Test suite
│   └── test_data_integrity.py        # Data validation tests
├── pyproject.toml                    # Package configuration
├── requirements.txt                  # Python dependencies
├── Makefile                          # Build automation
├── CHANGELOG.md                      # Version history
├── CONTRIBUTING.md                   # Contribution guidelines
├── LICENSE                           # MIT License
└── README.md                         # This file
```

---

## Data Availability

### Complete Analysis Dataset

The complete analysis dataset (all 372,283 extracted claims) is deposited at Harvard Dataverse:

**https://doi.org/10.7910/DVN/6EFL00**

Dataverse contents:
- `all_themes_combined.csv` - All extracted claims with state, theme, file, year (127 MB)
- `normalized_concordance_by_theme.csv` - Per-file normalized concordance ratios
- `covid_comparison_stratified.csv` - Temporal trends stratified by document type
- `document_inventory.csv` - Source document catalog with metadata
- Additional summary tables and figures

---

## Installation

### Prerequisites

- Python 3.11 or higher
- 16GB RAM minimum (32GB recommended for full corpus processing)
- ~10GB disk space for full dataset

### Setup

```bash
# Clone repository
git clone https://github.com/sanjaybasu/medicaid_rfp_analysis.git
cd medicaid_rfp_analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Quick Start: Analyze Pre-Extracted Claims

Use the pre-extracted claims from Dataverse to reproduce manuscript analyses without processing source documents:

```python
import pandas as pd

# Load all claims (download from Dataverse first)
claims = pd.read_csv('all_themes_combined.csv')

# Reproduce Table 2: Theme distribution
theme_counts = claims['theme'].value_counts()
print(theme_counts)

# Reproduce temporal analysis
temporal = claims.groupby(['year', 'theme']).size().reset_index(name='claims')
```

### Full Pipeline: Process Source Documents

If you have obtained source documents:

```bash
# 1. Create document inventory
python scripts/phase1_document_inventory.py

# 2. Extract text from PDFs and ZIP archives
python scripts/phase1b_extract_documents.py

# 3. Extract claims using RAG+LLM (requires Anthropic API key)
export ANTHROPIC_API_KEY="your-api-key"
python scripts/phase2_document_analysis.py

# 4. Run thematic analysis
python scripts/thematic_analysis.py

# 5. Generate manuscript tables and figures
python scripts/generate_manuscript_data.py

# 6. Run normalized concordance analyses (stratified analyses)
python scripts/normalized_concordance_analysis.py
```

### Key Analysis Scripts

**Normalized Concordance Analysis:**
```python
# calculates per-file concordance ratios
python scripts/normalized_concordance_analysis.py
```

This script:
- Calculates per-file claim rates for RFPs and MCO proposals
- Computes normalized concordance ratios (MCO claims/file ÷ RFP claims/file)
- Aggregates across states using inverse-variance weighting
- Generates `normalized_concordance_by_theme.csv`

**Stratified Temporal Analysis:**
```python
# Separates RFP, MCO, and Other documents
temporal_data = claims[claims['doc_type'].notna()]
temporal_data['doc_category'] = temporal_data['doc_type'].apply(
    lambda x: 'RFP' if 'rfp' in x.lower() else
              ('MCO' if 'proposal' in x.lower() else 'Other')
)
temporal_stratified = temporal_data.groupby(['year', 'theme', 'doc_category']).size()
```

---

## Methodology

### Document Corpus

- **Source Documents:** 265 (RFPs, MCO proposals, contracts, scoring documents)
- **Processed Text Files:** 1,666 (6.29x expansion from extracting compressed archives)
- **States:** 32 + District of Columbia
- **Time Period:** January 2017 - December 2024
- **Total Pages:** ~460,000

### Claim Extraction Pipeline

1. **Text Extraction:** PDFs processed with pypdf; ZIP archives extracted recursively
2. **Document Chunking:** 8,000-character chunks with 500-character overlap
3. **Vector Embedding:** all-MiniLM-L6-v2 sentence transformer (384-dimensional)
4. **Retrieval:** Top-5 most similar chunks retrieved via ChromaDB (cosine similarity)
5. **Extraction:** Claude Sonnet 4.5 with structured JSON output (temperature=0.0)
6. **Validation:** 97.3% source attribution accuracy on 10% random sample

### Thematic Classification

Six primary themes developed through iterative grounded theory:
- Chronic Disease Management (28.9% of claims)
- Long-Term Services & Supports/Dual Eligibles (18.0%)
- Health Equity (14.1%)
- Technology & Digital Health (13.1%)
- Workforce Development (13.1%)
- Social Determinants of Health (12.8%)

### Human Validation

- **Sample:** 200 stratified random document sections
- **Coders:** 2 independent doctoral-level researchers
- **Inter-rater Reliability:** Cohen's kappa = 0.86 (95% CI: 0.81-0.91)
- **ML Performance:** Sensitivity 0.89, Specificity 0.94

---

## Citation

If you use this code or data in your research, please cite:

```bibtex
@article{basu2026medicaid,
  title={Medicaid Managed Care Procurement Reveals Systematic Overemphasis of Technology and Equity Performance Claims Across 32 States},
  author={Basu, Sanjay and Fleming, Alex and Morgan, John and Batniji, Rajaie},
  journal={INQUIRY: The Journal of Health Care Organization, Provision, and Financing},
  year={2026},
  note={Under review},
  url={https://doi.org/10.7910/DVN/6EFL00}
}
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Source procurement documents remain subject to original state copyright and distribution restrictions.

- Dataset: Basu S, Fleming A, Morgan J, Batniji R. Medicaid Managed Care Procurement Claims Dataset, 32 States, 2017-2024. Harvard Dataverse. 2026. https://doi.org/10.7910/DVN/6EFL00

---

**Last Updated:** April 2, 2026 (R2 revision)
