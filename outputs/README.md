# Outputs Directory

Analysis outputs will be generated here when running the pipeline.

## Expected Outputs

After running `run_full_analysis.py`, this directory will contain:

```
outputs/
├── document_inventory.csv       # Catalog of all source documents
├── document_inventory.json      # JSON format of inventory
├── extraction_manifest.csv      # Text extraction log
├── claims_extracted.csv         # All extracted quantitative claims
├── partnerships_extracted.csv   # All extracted partnership references
├── claim_summary.json           # Aggregate statistics
├── state_summary.csv            # Claims by state
├── table1_study_population.csv  # Study population characteristics
├── table2_claim_types.csv       # Claim type breakdown
└── table3_geographic.csv        # Geographic distribution
```

## Sample Files Included

- `sample_claims.csv` - First 100 rows of extracted claims (for testing)
- `sample_claim_summary.json` - Example summary statistics

## Full Results

Complete analysis outputs (55,914 claims) available at:
- Dataverse: [DOI link]
- Or run the full pipeline on source documents
