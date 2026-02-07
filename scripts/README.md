# analysis scripts

## pipeline order

run scripts in this order for full analysis:

1. `phase1_document_inventory.py` - catalog source documents
2. `phase1b_extract_documents.py` - extract text from pdfs/zips
3. `phase2_document_analysis.py` - extract claims using rag+llm
4. `thematic_analysis.py` - classify claims by theme
5. `generate_manuscript_data.py` - create tables
6. `normalized_concordance_analysis.py` - normalized concordance
7. `generate_figures.py` - create manuscript figures

## quick reference

### phase1_document_inventory.py
- scans data directory for procurement documents
- creates document_inventory.csv with metadata
- no external dependencies

### phase1b_extract_documents.py
- extracts text from pdfs using pypdf
- unpacks zip archives
- saves to processed_text/

### phase2_document_analysis.py
- requires anthropic api key
- uses claude sonnet 4.5 for claim extraction
- implements rag with chromadb
- outputs raw claims by state

### thematic_analysis.py
- loads raw claims
- applies thematic classification
- creates all_themes_combined.csv (372,283 claims)

### generate_manuscript_data.py
- creates summary statistics
- generates table 1 (study population)
- produces hedis outcomes summary

### normalized_concordance_analysis.py
- calculates per-file normalized concordance
- stratifies temporal/regional analyses
- outputs normalized_concordance_by_theme.csv

### generate_figures.py
- figure 1: normalized concordance bar chart
- figure 2: temporal trends by document type
- figure 3: regional distribution heat map
- all figures saved as png (300 dpi) and pdf (vector)

## data flow

```
source documents (265 pdfs/zips)
  ↓
processed text (1,668 files)
  ↓
raw claims (extracted via llm)
  ↓
thematic claims (372,283 classified)
  ↓
analysis outputs (concordance, temporal, regional)
  ↓
figures (3 manuscript figures)
```

## requirements

- python 3.11+
- 16gb ram (32gb for full pipeline)
- anthropic api key (phase 2 only)
- see requirements.txt for packages
