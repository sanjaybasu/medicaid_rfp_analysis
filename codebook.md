# Medicaid MCO RFP Analysis Codebook

## Version 1.0 | December 2025

---

## 1. Domain Codes (Level 1)

| Code | Domain | Definition | Examples |
|------|--------|------------|----------|
| VBC | Value-Based Care | Payment models, quality incentives, shared savings, outcome-based contracts | Shared savings arrangements, pay-for-performance, ACO contracts |
| PH | Population Health | Population health management, health equity, SDOH interventions, community health | Community health workers, social determinants screening, health equity initiatives |
| AC | Access to Care | Network adequacy, specialty access, telehealth, geographic coverage | 30-day PCP appointment access, telehealth visits, network expansion |
| CC | Care Coordination | Case management, care transitions, CHW programs, care teams | Discharge planning, transitions of care, care management programs |
| QM | Quality Metrics | HEDIS measures, state quality metrics, accreditation, performance measurement | HEDIS breast cancer screening, CAHPS scores, state quality targets |
| PM | Payment Models | Capitation structures, risk adjustment, incentive arrangements | PMPM rates, risk corridors, value-based incentive pools |
| HIT | Health Information Technology | EHR integration, data analytics, interoperability, predictive modeling | Health information exchange, predictive analytics, care gaps alerts |
| WD | Workforce Development | Training programs, staffing ratios, provider engagement | Provider training, care manager FTEs, cultural competency education |

---

## 2. Claim Type Codes (Level 2)

| Code | Claim Type | Definition | Signal Words |
|------|------------|------------|--------------|
| HIST | Historical Performance | Claims about past achievements with this or other contracts | "achieved," "demonstrated," "historically," "in [year]" |
| PROJ | Projected Performance | Commitments to future performance levels | "will achieve," "commit to," "target of," "by Year X" |
| COMP | Comparative Performance | Claims relative to benchmarks, competitors, or national standards | "above national average," "exceeds benchmark," "compared to" |
| METH | Methodology | Description of approach without quantified outcomes | "our approach," "we utilize," "our process involves" |

---

## 3. Evidence Quality Codes (Level 3)

| Code | Evidence Type | Definition | Required Elements |
|------|---------------|------------|-------------------|
| PR | Peer-Reviewed | Cited in peer-reviewed publication | Journal name, authors, year |
| CG | Control Group | RCT or quasi-experimental design with comparison | Comparison group mentioned, statistical testing |
| PP | Pre-Post | Before-after analysis without control | Baseline and follow-up timepoints specified |
| INT | Internal Analysis | MCO's own unpublished analysis | Source attributed to internal team |
| EXT | External Validation | Third-party audit or evaluation | External organization named |
| NONE | No Evidence | Claim without supporting evidence | No source or methodology cited |

---

## 4. Quantification Codes (Level 4)

| Code | Quantification Level | Definition | Examples |
|------|---------------------|------------|----------|
| Q-ABS | Absolute Number | Specific count or amount | "reduced by 500 admissions," "saved $2.3 million" |
| Q-PCT | Percentage | Percent change or rate | "15% improvement," "achieved 85% rate" |
| Q-PPT | Percentage Points | Percentage point change | "increased 5 percentage points from 75% to 80%" |
| Q-TGT | Target with Timeline | Specific goal with timeframe | "achieve 90% by Year 2" |
| Q-NONE | Unquantified | Qualitative claim without numbers | "improved outcomes," "enhanced quality" |

---

## 5. Clinical Domain Subcodes

| Code | Domain | Definition | Common Metrics |
|------|--------|------------|----------------|
| MAT | Maternity | Prenatal care, delivery, postpartum, NICU | Prenatal care visits, C-section rates, postpartum care |
| PED | Pediatrics | Well-child, immunizations, developmental screening | Immunization rates, well-child visits, lead screening |
| BH | Behavioral Health | Mental health, SUD, integration | Depression screening, SUD treatment, BH/PH integration |
| CHR | Chronic Disease | Diabetes, hypertension, asthma, heart failure | HbA1c control, BP control, asthma medication ratio |
| PCP | Primary Care | PCP access, utilization, medical home | PCP visit rates, PCMH attribution, same-day access |
| HOSP | Hospital Utilization | ED visits, admissions, readmissions, LOS | ED visit rate, readmission rate, avoidable admissions |
| RX | Pharmacy | Medication adherence, PBM, specialty drugs | PDC rates, generic utilization, specialty Rx management |

---

## 6. Partnership Codes

| Code | Partner Type | Definition | Examples |
|------|--------------|------------|----------|
| P-CBO | Community-Based Organization | Non-profit service organizations | Food banks, housing agencies, faith-based organizations |
| P-GOV | Government Agency | State/local health departments, social services | Health departments, SNAP offices, WIC programs |
| P-ACAD | Academic/Research | Universities, research institutions | Medical schools, health policy institutes, evaluation centers |
| P-TECH | Technology Vendor | Health IT, analytics companies | EHR vendors, analytics platforms, telehealth providers |
| P-PROV | Provider Organization | Health systems, FQHCs, physician groups | Hospital systems, FQHCs, IPAs, specialty groups |

---

## 7. Confidence Ratings

| Rating | Definition | When to Use |
|--------|------------|-------------|
| HIGH | Clear, unambiguous extraction | Numeric values explicit, metric clearly named, timeframe stated |
| MEDIUM | Some interpretation required | Values or context partially inferred, some ambiguity |
| LOW | Significant uncertainty | Multiple interpretations possible, context unclear |

---

## 8. Coding Decision Rules

### Rule 1: Multiple Domains
If a claim spans multiple domains, code the PRIMARY domain based on the metric being quantified.

### Rule 2: Implied Evidence
Do not assume evidence type. If methodology is not explicitly stated, code as NONE.

### Rule 3: Timeline Ambiguity
If no timeline is stated, leave timeline fields null. Do not infer from contract dates.

### Rule 4: Partnership Attribution
Only code partnerships where outcomes are explicitly attributed to the partnership.

### Rule 5: Comparative Baselines
For COMP claims, baseline must be explicitly stated (e.g., "national average"), not assumed.

---

## 9. Quality Control Procedures

1. **Inter-rater reliability**: Two coders independently code 10% sample
2. **Discrepancy resolution**: Discussion and consensus for disagreements
3. **LLM validation**: Human review of 100+ LLM-coded sections
4. **Kappa thresholds**: Domain codes κ≥0.85, Evidence codes κ≥0.75

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 2025 | Initial release |
