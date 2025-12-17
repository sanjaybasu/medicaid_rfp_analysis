# Data Directory

This directory should contain the source Medicaid procurement documents.

## Expected Structure

```
data/
├── rfps/
│   ├── Alabama/
│   ├── Arizona/
│   ├── California/
│   │   ├── CA_Medi-Cal_RFP_2023.pdf
│   │   ├── CA_MCO_Proposal_Anthem.pdf
│   │   └── ...
│   ├── ...
│   └── [State]/
│       └── [documents].pdf/.docx/.zip
└── hedis/
    └── hedis_medicaid_2023.csv
```

## Data Acquisition

### Procurement Documents

Source documents can be obtained from:

1. **State Procurement Portals**
   - Search "[State] Medicaid managed care RFP"
   - Example: California DHCS procurement portal

2. **State Medicaid Agency Websites**
   - Look under "Managed Care" or "Contracts" sections

3. **FOIA Requests**
   - For documents not publicly posted
   - Contact state Medicaid agency directly

### HEDIS Data

NCQA HEDIS Medicaid data available from:
- NCQA Quality Compass: https://www.ncqa.org/hedis/
- State-specific quality reports

## Sample Data

A small sample dataset for testing is available at:
[Dataverse DOI link - to be added after publication]

## Notes

- Original documents are not included in this repository due to size (22+ GB)
- Contact Sanjay Basu (sanjay.basu@waymarkcare.org) for data access inquiries
- Some documents may be subject to state-specific access restrictions
