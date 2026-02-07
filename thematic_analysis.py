#!/usr/bin/env python3
"""
Thematic Analysis for Medicaid MCO RFP Claims
Aligned with Health Affairs Priority Themes
"""

import os
import re
import json
import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Configuration
TEXT_DIR = "/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/processed_text"
OUTPUT_DIR = "/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs/thematic"
CLAIMS_FILE = "/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs/interim_claims.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# THEME TAXONOMIES
# =============================================================================

HEALTH_EQUITY_PATTERNS = {
    'racial_ethnic_disparities': [
        r'racial\s+(?:and\s+ethnic\s+)?disparit(?:y|ies)',
        r'health\s+equit(?:y|able)',
        r'(?:african\s+american|black|hispanic|latino|asian|native\s+american|indigenous)\s+(?:population|communit|member|patient)',
        r'minorit(?:y|ies)\s+(?:population|health|communit)',
        r'cultural(?:ly)?\s+(?:competent|appropriate|sensitive)',
        r'race\s+and\s+ethnicit(?:y|ies)',
    ],
    'language_access': [
        r'language\s+(?:access|services|assistance|line)',
        r'limited\s+english\s+proficien(?:t|cy)',
        r'(?:lep|lei)\s+(?:members?|patients?|population)',
        r'interpret(?:er|ation)\s+services?',
        r'translat(?:e|ion|or)\s+(?:services?|materials?)',
        r'(?:spanish|bilingual|multilingual)\s+(?:speaking|services?|staff)',
        r'in-?language\s+(?:services?|materials?|support)',
    ],
    'disability': [
        r'disabilit(?:y|ies)\s+(?:services?|population|members?)',
        r'americans?\s+with\s+disabilities\s+act',
        r'\bada\b\s+compli(?:ant|ance)',
        r'accessib(?:le|ility)\s+(?:services?|facilities?|materials?)',
        r'special\s+needs?\s+(?:population|members?|plan)',
        r'intellectual\s+(?:and\s+)?developmental\s+disabilit',
        r'\bi/?dd\b',
    ],
    'lgbtq_health': [
        r'lgbtq?\+?\s+(?:health|population|members?|communit)',
        r'sexual\s+orientation\s+(?:and\s+)?gender\s+identit(?:y|ies)',
        r'transgender\s+(?:health|members?|services?)',
        r'gender[\s-]affirming\s+care',
    ],
    'geographic_disparities': [
        r'rural\s+(?:health|access|population|communit|areas?)',
        r'urban\s+(?:underserved|health|disparit)',
        r'geographic(?:al)?\s+(?:disparit|access|barrier)',
        r'medically\s+underserved\s+(?:area|population)',
        r'health\s+professional\s+shortage\s+area',
        r'\bhpsa\b',
        r'frontier\s+(?:area|communit|region)',
    ],
}

SDOH_PATTERNS = {
    'food_insecurity': [
        r'food\s+(?:insecurit(?:y|ies)|access|desert|assistance|pantry|bank)',
        r'nutrition(?:al)?\s+(?:services?|support|assistance|program)',
        r'(?:snap|wic)\s+(?:enrollment|referral|benefit)',
        r'meal\s+(?:delivery|program|services?)',
        r'hunger\s+(?:screen|assessment|program)',
    ],
    'housing_instability': [
        r'housing\s+(?:instabilit(?:y|ies)|insecurit(?:y|ies)|support|assistance|services?)',
        r'homelessness?\s+(?:prevention|services?|population)',
        r'transitional\s+housing',
        r'eviction\s+prevention',
        r'permanent\s+supportive\s+housing',
        r'housing\s+first',
    ],
    'transportation_barriers': [
        r'transportation\s+(?:barrier|services?|assistance|support|access)',
        r'non[\s-]?emergenc(?:y|t)\s+medical\s+transport',
        r'\bnemt\b',
        r'ride[\s-]?share\s+(?:services?|partner)',
        r'medical\s+transportation',
    ],
    'social_isolation': [
        r'social\s+(?:isolation|connectedness|support|determinant)',
        r'lonel(?:y|iness)\s+(?:screen|intervention|program)',
        r'community\s+(?:connection|engagement|resource)',
        r'peer\s+support\s+(?:program|services?|specialist)',
    ],
    'employment': [
        r'employment\s+(?:support|services?|assistance|program)',
        r'job\s+(?:training|placement|readiness)',
        r'vocational\s+(?:rehabilitation|services?|training)',
        r'workforce\s+(?:development|participation)',
        r'supported\s+employment',
    ],
    'sdoh_screening': [
        r'sdoh\s+(?:screen|assessment|tool)',
        r'social\s+(?:needs?\s+)?screen(?:ing)?',
        r'(?:prapare|hrsn|accountable\s+health)\s+(?:screen|tool|assessment)',
        r'z[\s-]?code\s+(?:capture|documentation)',
        r'social\s+risk\s+(?:factor|assessment)',
    ],
}

LTSS_DUAL_PATTERNS = {
    'dual_eligibles': [
        r'dual[\s-]?eligible\s+(?:population|members?|beneficiar)',
        r'medicare[\s-]?medicaid\s+(?:integration|enrollee|dual)',
        r'\bd[\s-]?snp\b',
        r'fully[\s-]?integrated\s+dual[\s-]?eligible',
        r'\bfide[\s-]?snp\b',
        r'financial\s+alignment\s+(?:initiative|demonstration)',
    ],
    'ltss': [
        r'long[\s-]?term\s+(?:services?\s+(?:and\s+)?supports?|care)',
        r'\bltss\b',
        r'(?:home|community)[\s-]?based\s+(?:services?|care|waiver)',
        r'\bhcbs\b',
        r'institutional\s+(?:care|setting|placement)',
        r'rebalancing\s+(?:initiative|effort|goal)',
    ],
    'nursing_facility': [
        r'nursing\s+(?:home|facilit(?:y|ies))',
        r'skilled\s+nursing\s+facilit(?:y|ies)',
        r'\bsnf\b',
        r'post[\s-]?acute\s+care',
        r'transitional\s+care\s+(?:management|coordination)',
    ],
    'home_health': [
        r'home\s+health\s+(?:services?|care|aide)',
        r'personal\s+care\s+(?:services?|attendant|aide)',
        r'\bpca\b\s+(?:services?|program)',
        r'in[\s-]?home\s+(?:support|care|services?)',
        r'homemaker\s+services?',
    ],
    'pace': [
        r'\bpace\b\s+(?:program|model|participant)',
        r'program\s+of\s+all[\s-]?inclusive\s+care',
        r'all[\s-]?inclusive\s+care\s+for\s+(?:the\s+)?elderly',
    ],
    'aging_services': [
        r'age[\s-]?friendly\s+(?:health|care|system)',
        r'geriatric\s+(?:care|assessment|specialist)',
        r'older\s+adult\s+(?:population|services?|care)',
        r'aging\s+(?:in\s+place|services?|population)',
        r'senior\s+(?:services?|center|program)',
    ],
}

TECHNOLOGY_PATTERNS = {
    'telehealth': [
        r'tele(?:health|medicine|psychiatry|behavioral)',
        r'virtual\s+(?:visit|care|health|consultation)',
        r'video\s+(?:visit|consultation|appointment)',
        r'remote\s+(?:consultation|visit|care\s+delivery)',
        r'synchronous\s+(?:telehealth|telemedicine)',
        r'store[\s-]?and[\s-]?forward',
    ],
    'ai_predictive': [
        r'artificial\s+intelligence',
        r'\bai\b[\s-]?(?:powered|driven|based|enabled)',
        r'machine\s+learning',
        r'predictive\s+(?:analytics?|model|algorithm)',
        r'risk\s+(?:stratification|score|model|predict)',
        r'natural\s+language\s+processing',
    ],
    'remote_monitoring': [
        r'remote\s+(?:patient\s+)?monitoring',
        r'\brpm\b\s+(?:program|services?|device)',
        r'wearable\s+(?:device|technology|sensor)',
        r'connected\s+(?:device|health|care)',
        r'digital\s+(?:health|therapeutic|monitoring)',
    ],
    'member_portal': [
        r'member\s+(?:portal|app|application)',
        r'patient\s+portal',
        r'mobile\s+(?:app|application|health)',
        r'digital\s+(?:engagement|platform|tool)',
        r'online\s+(?:portal|services?|access)',
        r'self[\s-]?service\s+(?:portal|tool)',
    ],
    'digital_equity': [
        r'digital\s+(?:equit(?:y|able)|divide|literacy|access)',
        r'broadband\s+(?:access|connectivity)',
        r'(?:technology|digital)\s+(?:barrier|access|literacy)',
        r'telephone[\s-]?only\s+(?:option|services?)',
    ],
    'hie_interoperability': [
        r'health\s+information\s+exchange',
        r'\bhie\b\s+(?:connect|participat|integrat)',
        r'interoperabilit(?:y|able)',
        r'data\s+(?:exchange|sharing|integration)',
        r'adt\s+(?:notification|alert|feed)',
        r'care\s+(?:everywhere|connectivity)',
    ],
}

WORKFORCE_PATTERNS = {
    'direct_care_worker': [
        r'direct\s+(?:care|service|support)\s+worker',
        r'home\s+care\s+(?:worker|aide|workforce)',
        r'personal\s+care\s+(?:attendant|aide|worker)',
        r'caregiver\s+(?:support|training|retention)',
        r'dsw\s+(?:training|retention|recruitment)',
    ],
    'provider_recruitment': [
        r'provider\s+(?:recruitment|retention|network)',
        r'physician\s+(?:recruitment|shortage|retention)',
        r'network\s+(?:adequacy|development|expansion)',
        r'specialist\s+(?:access|recruitment|availability)',
    ],
    'cultural_competency': [
        r'cultural\s+(?:competenc(?:y|e)|humility)\s+training',
        r'implicit\s+bias\s+training',
        r'diversity\s+(?:equity\s+(?:and\s+)?inclusion|training)',
        r'\bdei\b\s+(?:training|initiative|program)',
        r'health\s+equity\s+training',
    ],
    'chw_programs': [
        r'community\s+health\s+worker',
        r'\bchw\b\s+(?:program|model|integration)',
        r'promotor(?:a|es)',
        r'peer\s+(?:support\s+)?specialist',
        r'lay\s+health\s+worker',
        r'health\s+navigator',
    ],
    'workforce_diversity': [
        r'workforce\s+(?:diversity|representation)',
        r'diverse\s+(?:workforce|staff|provider)',
        r'representative\s+workforce',
        r'(?:minority|underrepresented)\s+(?:provider|staff|workforce)',
    ],
}

CHRONIC_DISEASE_PATTERNS = {
    'diabetes': [
        r'diabetes\s+(?:management|prevention|care|program)',
        r'diabetic\s+(?:patient|member|population)',
        r'(?:hba1c|a1c|hemoglobin)\s+(?:control|level|monitor)',
        r'blood\s+(?:sugar|glucose)\s+(?:control|monitor)',
        r'diabetes\s+(?:self[\s-]?management|education)',
    ],
    'hypertension': [
        r'hypertension\s+(?:management|control|program)',
        r'blood\s+pressure\s+(?:control|management|monitor)',
        r'(?:high|elevated)\s+blood\s+pressure',
        r'cardiovascular\s+(?:disease|risk|health)',
    ],
    'asthma': [
        r'asthma\s+(?:management|control|program|action)',
        r'respiratory\s+(?:condition|disease|health)',
        r'asthma\s+(?:attack|exacerbation|trigger)',
        r'inhaler\s+(?:technique|adherence|use)',
    ],
    'chf': [
        r'(?:congestive\s+)?heart\s+failure',
        r'\bchf\b\s+(?:management|program|patient)',
        r'cardiac\s+(?:rehabilitation|care|disease)',
        r'heart\s+(?:disease|health|condition)',
    ],
    'copd': [
        r'\bcopd\b\s+(?:management|program|patient)',
        r'chronic\s+obstructive\s+pulmonary',
        r'pulmonary\s+(?:rehabilitation|disease)',
        r'emphysema',
    ],
    'behavioral_health': [
        r'behavioral\s+health\s+(?:integration|services?|care)',
        r'mental\s+health\s+(?:services?|integration|parity)',
        r'substance\s+(?:use|abuse)\s+(?:disorder|treatment)',
        r'\bsud\b\s+(?:treatment|services?|program)',
        r'(?:opioid|medication[\s-]?assisted)\s+treatment',
        r'\bmat\b\s+(?:program|services?|provider)',
        r'crisis\s+(?:intervention|services?|stabilization)',
        r'psychiatric\s+(?:services?|care|provider)',
    ],
    'maternal_health': [
        r'maternal\s+(?:health|mortality|morbidity|care)',
        r'prenatal\s+(?:care|services?|visit)',
        r'perinatal\s+(?:care|services?|health)',
        r'postpartum\s+(?:care|services?|visit|depression)',
        r'pregnancy\s+(?:care|services?|support)',
        r'high[\s-]?risk\s+(?:pregnancy|obstetric)',
        r'birth\s+(?:outcome|equity)',
    ],
    'pediatric': [
        r'pediatric\s+(?:care|services?|population)',
        r'child(?:ren)?\s+(?:health|care|services?)',
        r'well[\s-]?child\s+(?:visit|care|check)',
        r'immunization\s+(?:rate|compliance|schedule)',
        r'vaccination\s+(?:rate|compliance|coverage)',
        r'(?:epsdt|early\s+periodic)',
    ],
}

# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def compile_patterns(pattern_dict):
    """Compile regex patterns for efficiency."""
    compiled = {}
    for category, patterns in pattern_dict.items():
        compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
    return compiled

def extract_themes_from_text(text, compiled_patterns):
    """Extract theme matches from text."""
    results = defaultdict(list)
    for category, patterns in compiled_patterns.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                # Get context (50 chars before and after)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].replace('\n', ' ').strip()
                results[category].append({
                    'match': match.group(),
                    'context': context,
                    'position': match.start()
                })
    return results

def analyze_text_files(text_dir, compiled_patterns, theme_name):
    """Analyze all text files for a theme category."""
    results = []

    for state_dir in Path(text_dir).iterdir():
        if not state_dir.is_dir():
            continue
        state = state_dir.name

        for txt_file in state_dir.glob('*.txt'):
            try:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()

                # Extract year from filename
                year_match = re.search(r'20(1[7-9]|2[0-4])', txt_file.name)
                year = int('20' + year_match.group(1)) if year_match else None

                # Determine document type
                fname_lower = txt_file.name.lower()
                if 'rfp' in fname_lower or 'request' in fname_lower:
                    doc_type = 'RFP'
                elif 'proposal' in fname_lower or 'response' in fname_lower:
                    doc_type = 'Proposal'
                elif 'contract' in fname_lower:
                    doc_type = 'Contract'
                else:
                    doc_type = 'Other'

                # Extract MCO name
                mco_patterns = ['centene', 'molina', 'anthem', 'united', 'aetna',
                               'humana', 'amerigroup', 'wellcare', 'caresource',
                               'healthfirst', 'kaiser', 'blue cross', 'cigna']
                mco = None
                for mco_name in mco_patterns:
                    if mco_name in fname_lower:
                        mco = mco_name.title()
                        break

                # Extract themes
                themes = extract_themes_from_text(text, compiled_patterns)

                for category, matches in themes.items():
                    for match_info in matches:
                        results.append({
                            'state': state,
                            'file': txt_file.name,
                            'year': year,
                            'doc_type': doc_type,
                            'mco': mco,
                            'theme': theme_name,
                            'subcategory': category,
                            'match_text': match_info['match'],
                            'context': match_info['context'],
                        })

            except Exception as e:
                print(f"  Error processing {txt_file}: {e}")

    return pd.DataFrame(results)

def get_region(state):
    """Map state to US Census region."""
    regions = {
        'Northeast': ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire',
                     'Rhode Island', 'Vermont', 'New Jersey', 'New York',
                     'Pennsylvania', 'Delaware', 'Washington DC'],
        'Southeast': ['Alabama', 'Arkansas', 'Florida', 'Georgia', 'Kentucky',
                     'Louisiana', 'Mississippi', 'North Carolina', 'South Carolina',
                     'Tennessee', 'Virginia', 'West Virginia', 'Maryland'],
        'Midwest': ['Illinois', 'Indiana', 'Iowa', 'Kansas', 'Michigan',
                   'Minnesota', 'Missouri', 'Nebraska', 'North Dakota',
                   'Ohio', 'South Dakota', 'Wisconsin'],
        'Southwest': ['Arizona', 'New Mexico', 'Oklahoma', 'Texas'],
        'West': ['Alaska', 'California', 'Colorado', 'Hawaii', 'Idaho',
                'Montana', 'Nevada', 'Oregon', 'Utah', 'Washington', 'Wyoming']
    }
    for region, states in regions.items():
        if state in states:
            return region
    return 'Unknown'

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def main():
    print("=" * 60)
    print("THEMATIC ANALYSIS FOR HEALTH AFFAIRS")
    print("=" * 60)
    print(f"Start time: {datetime.now().isoformat()}")

    all_themes = []

    # Priority 1: Health Equity
    print("\n[1/6] Analyzing Health Equity themes...")
    equity_patterns = compile_patterns(HEALTH_EQUITY_PATTERNS)
    equity_df = analyze_text_files(TEXT_DIR, equity_patterns, 'health_equity')
    equity_df.to_csv(f"{OUTPUT_DIR}/equity_theme_analysis.csv", index=False)
    print(f"  Found {len(equity_df)} health equity claims")
    all_themes.append(equity_df)

    # Priority 2: SDOH
    print("\n[2/6] Analyzing SDOH themes...")
    sdoh_patterns = compile_patterns(SDOH_PATTERNS)
    sdoh_df = analyze_text_files(TEXT_DIR, sdoh_patterns, 'sdoh')
    sdoh_df.to_csv(f"{OUTPUT_DIR}/sdoh_theme_analysis.csv", index=False)
    print(f"  Found {len(sdoh_df)} SDOH claims")
    all_themes.append(sdoh_df)

    # Priority 3: LTSS/Dual Eligible
    print("\n[3/6] Analyzing LTSS/Dual Eligible themes...")
    ltss_patterns = compile_patterns(LTSS_DUAL_PATTERNS)
    ltss_df = analyze_text_files(TEXT_DIR, ltss_patterns, 'ltss_dual')
    ltss_df.to_csv(f"{OUTPUT_DIR}/ltss_dual_analysis.csv", index=False)
    print(f"  Found {len(ltss_df)} LTSS/Dual claims")
    all_themes.append(ltss_df)

    # Priority 4: Technology
    print("\n[4/6] Analyzing Technology themes...")
    tech_patterns = compile_patterns(TECHNOLOGY_PATTERNS)
    tech_df = analyze_text_files(TEXT_DIR, tech_patterns, 'technology')
    tech_df.to_csv(f"{OUTPUT_DIR}/technology_theme_analysis.csv", index=False)
    print(f"  Found {len(tech_df)} technology claims")
    all_themes.append(tech_df)

    # Priority 5: Workforce
    print("\n[5/6] Analyzing Workforce themes...")
    workforce_patterns = compile_patterns(WORKFORCE_PATTERNS)
    workforce_df = analyze_text_files(TEXT_DIR, workforce_patterns, 'workforce')
    workforce_df.to_csv(f"{OUTPUT_DIR}/workforce_theme_analysis.csv", index=False)
    print(f"  Found {len(workforce_df)} workforce claims")
    all_themes.append(workforce_df)

    # Priority 6: Chronic Disease
    print("\n[6/6] Analyzing Chronic Disease themes...")
    chronic_patterns = compile_patterns(CHRONIC_DISEASE_PATTERNS)
    chronic_df = analyze_text_files(TEXT_DIR, chronic_patterns, 'chronic_disease')
    chronic_df.to_csv(f"{OUTPUT_DIR}/chronic_disease_analysis.csv", index=False)
    print(f"  Found {len(chronic_df)} chronic disease claims")
    all_themes.append(chronic_df)

    # Combine all themes
    print("\n" + "=" * 60)
    print("GENERATING CROSS-CUTTING ANALYSES")
    print("=" * 60)

    combined_df = pd.concat(all_themes, ignore_index=True)
    combined_df['region'] = combined_df['state'].apply(get_region)
    combined_df.to_csv(f"{OUTPUT_DIR}/all_themes_combined.csv", index=False)

    # ==========================================================================
    # EXHIBIT 2: Theme Taxonomy with Frequencies
    # ==========================================================================
    print("\nGenerating Exhibit 2: Theme Taxonomy...")

    theme_summary = combined_df.groupby(['theme', 'subcategory']).agg({
        'match_text': 'count',
        'state': 'nunique',
        'file': 'nunique'
    }).reset_index()
    theme_summary.columns = ['theme', 'subcategory', 'claim_count', 'states', 'documents']
    theme_summary['pct_of_total'] = (theme_summary['claim_count'] / theme_summary['claim_count'].sum() * 100).round(2)
    theme_summary = theme_summary.sort_values('claim_count', ascending=False)
    theme_summary.to_csv(f"{OUTPUT_DIR}/exhibit2_theme_taxonomy.csv", index=False)

    # Top themes summary
    top_themes = combined_df.groupby('theme')['match_text'].count().sort_values(ascending=False)
    print(f"\n  Top themes by frequency:")
    for theme, count in top_themes.items():
        print(f"    {theme}: {count:,}")

    # ==========================================================================
    # EXHIBIT 3: Temporal Trends (for themes with year data)
    # ==========================================================================
    print("\nGenerating Exhibit 3: Temporal Trends...")

    temporal_df = combined_df[combined_df['year'].notna()].copy()
    temporal_df['year'] = temporal_df['year'].astype(int)

    # Priority themes for temporal analysis
    priority_themes = ['health_equity', 'sdoh', 'technology', 'chronic_disease', 'workforce']
    priority_subcats = ['behavioral_health', 'maternal_health', 'telehealth',
                       'racial_ethnic_disparities', 'sdoh_screening']

    # By main theme
    temporal_theme = temporal_df.groupby(['year', 'theme'])['match_text'].count().unstack(fill_value=0)
    temporal_theme.to_csv(f"{OUTPUT_DIR}/exhibit3_temporal_by_theme.csv")

    # By subcategory for priority topics
    temporal_subcat = temporal_df[temporal_df['subcategory'].isin(priority_subcats)].groupby(
        ['year', 'subcategory'])['match_text'].count().unstack(fill_value=0)
    temporal_subcat.to_csv(f"{OUTPUT_DIR}/exhibit3_temporal_by_subcategory.csv")

    # Pre/post COVID comparison (2020 as inflection)
    covid_comparison = temporal_df.copy()
    covid_comparison['period'] = covid_comparison['year'].apply(
        lambda x: 'Pre-COVID (2017-2019)' if x < 2020 else 'COVID/Post (2020-2024)'
    )
    covid_summary = covid_comparison.groupby(['period', 'theme'])['match_text'].count().unstack(fill_value=0)
    covid_summary.to_csv(f"{OUTPUT_DIR}/temporal_covid_comparison.csv")

    # ==========================================================================
    # EXHIBIT 4: Regional Theme Patterns
    # ==========================================================================
    print("\nGenerating Exhibit 4: Regional Patterns...")

    regional_df = combined_df.groupby(['region', 'theme'])['match_text'].count().unstack(fill_value=0)
    regional_df.to_csv(f"{OUTPUT_DIR}/exhibit4_regional_themes.csv")

    # Regional percentages
    regional_pct = regional_df.div(regional_df.sum(axis=1), axis=0) * 100
    regional_pct.to_csv(f"{OUTPUT_DIR}/exhibit4_regional_themes_pct.csv")

    # Chi-square test results (simplified - compute proportions by region)
    regional_summary = combined_df.groupby(['region', 'theme']).agg({
        'match_text': 'count',
        'state': 'nunique'
    }).reset_index()
    regional_summary.columns = ['region', 'theme', 'claims', 'states']
    regional_summary.to_csv(f"{OUTPUT_DIR}/regional_statistical_summary.csv", index=False)

    # ==========================================================================
    # EXHIBIT 5: RFP-MCO Theme Concordance
    # ==========================================================================
    print("\nGenerating Exhibit 5: RFP-MCO Concordance...")

    # RFP themes
    rfp_themes = combined_df[combined_df['doc_type'] == 'RFP'].groupby(
        ['state', 'theme'])['match_text'].count().reset_index()
    rfp_themes.columns = ['state', 'theme', 'rfp_claims']

    # MCO/Proposal themes
    mco_themes = combined_df[combined_df['doc_type'] == 'Proposal'].groupby(
        ['state', 'theme'])['match_text'].count().reset_index()
    mco_themes.columns = ['state', 'theme', 'mco_claims']

    # Merge for concordance
    concordance = pd.merge(rfp_themes, mco_themes, on=['state', 'theme'], how='outer').fillna(0)
    concordance['concordance_ratio'] = concordance.apply(
        lambda x: x['mco_claims'] / x['rfp_claims'] if x['rfp_claims'] > 0 else np.nan, axis=1
    )
    concordance.to_csv(f"{OUTPUT_DIR}/exhibit5_rfp_mco_concordance.csv", index=False)

    # Summary by theme
    concordance_summary = concordance.groupby('theme').agg({
        'rfp_claims': 'sum',
        'mco_claims': 'sum'
    }).reset_index()
    concordance_summary['mco_to_rfp_ratio'] = (
        concordance_summary['mco_claims'] / concordance_summary['rfp_claims']
    ).round(2)
    concordance_summary.to_csv(f"{OUTPUT_DIR}/concordance_summary_by_theme.csv", index=False)

    # ==========================================================================
    # Additional Analyses
    # ==========================================================================

    # State-level summary
    print("\nGenerating state-level summaries...")
    state_summary = combined_df.groupby(['state', 'region']).agg({
        'match_text': 'count',
        'theme': lambda x: x.value_counts().index[0],  # Most common theme
        'file': 'nunique'
    }).reset_index()
    state_summary.columns = ['state', 'region', 'total_claims', 'top_theme', 'documents']
    state_summary = state_summary.sort_values('total_claims', ascending=False)
    state_summary.to_csv(f"{OUTPUT_DIR}/state_theme_summary.csv", index=False)

    # Subcategory details for each priority area
    for theme in ['health_equity', 'sdoh', 'technology', 'chronic_disease']:
        subcat_detail = combined_df[combined_df['theme'] == theme].groupby('subcategory').agg({
            'match_text': 'count',
            'state': 'nunique',
            'context': 'first'  # Example context
        }).reset_index()
        subcat_detail.columns = ['subcategory', 'claims', 'states', 'example_context']
        subcat_detail = subcat_detail.sort_values('claims', ascending=False)
        subcat_detail.to_csv(f"{OUTPUT_DIR}/{theme}_subcategory_detail.csv", index=False)

    # ==========================================================================
    # Final Summary Statistics
    # ==========================================================================
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    summary_stats = {
        'total_theme_claims': len(combined_df),
        'unique_states': combined_df['state'].nunique(),
        'unique_documents': combined_df['file'].nunique(),
        'years_covered': sorted(temporal_df['year'].dropna().unique().tolist()),
        'themes_analyzed': combined_df['theme'].nunique(),
        'subcategories_analyzed': combined_df['subcategory'].nunique(),
        'claims_by_theme': combined_df.groupby('theme')['match_text'].count().to_dict(),
        'claims_by_region': combined_df.groupby('region')['match_text'].count().to_dict(),
        'analyzed_at': datetime.now().isoformat()
    }

    with open(f"{OUTPUT_DIR}/thematic_analysis_summary.json", 'w') as f:
        json.dump(summary_stats, f, indent=2)

    print(f"\nTotal thematic claims: {summary_stats['total_theme_claims']:,}")
    print(f"States: {summary_stats['unique_states']}")
    print(f"Documents: {summary_stats['unique_documents']}")
    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print(f"End time: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
