"""
test data integrity
ensures all manuscript numbers match source data
"""

import pandas as pd
import pytest
from pathlib import Path

# paths
OUTPUT_DIR = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs/thematic")
DOC_INV_PATH = Path("/Users/sanjaybasu/waymark-local/notebooks/rfp_analysis/analysis_outputs/dataverse_package/document_inventory.csv")


def test_claim_count():
    """verify total claim count matches manuscript"""
    all_claims = pd.read_csv(OUTPUT_DIR / "all_themes_combined.csv")
    assert len(all_claims) == 372283, f"expected 372,283 claims, got {len(all_claims)}"


def test_document_count():
    """verify document count matches manuscript"""
    doc_inv = pd.read_csv(DOC_INV_PATH)
    assert len(doc_inv) == 265, f"expected 265 documents, got {len(doc_inv)}"


def test_state_count():
    """verify state count matches manuscript"""
    all_claims = pd.read_csv(OUTPUT_DIR / "all_themes_combined.csv")
    n_states = all_claims['state'].nunique()
    assert n_states == 32, f"expected 32 states, got {n_states}"


def test_file_count():
    """verify processed file count matches manuscript"""
    all_claims = pd.read_csv(OUTPUT_DIR / "all_themes_combined.csv")
    n_files = all_claims['file'].nunique()
    assert n_files == 1668, f"expected 1,668 files, got {n_files}"


def test_technology_ratio():
    """verify technology concordance ratio matches manuscript"""
    norm_conc = pd.read_csv(OUTPUT_DIR / "normalized_concordance_by_theme.csv", skiprows=1)
    norm_conc.columns = ['theme', 'mean', 'median', 'std', 'count', 'rfp_claims_per_file', 'mco_claims_per_file']

    tech = norm_conc[norm_conc['theme'] == 'technology']
    assert abs(tech['mean'].values[0] - 53.9) < 0.1, f"technology mean should be ~53.9, got {tech['mean'].values[0]}"


def test_health_equity_ratio():
    """verify health equity concordance ratio matches manuscript"""
    norm_conc = pd.read_csv(OUTPUT_DIR / "normalized_concordance_by_theme.csv", skiprows=1)
    norm_conc.columns = ['theme', 'mean', 'median', 'std', 'count', 'rfp_claims_per_file', 'mco_claims_per_file']

    heq = norm_conc[norm_conc['theme'] == 'health_equity']
    assert abs(heq['mean'].values[0] - 22.0) < 0.1, f"health equity mean should be ~22.0, got {heq['mean'].values[0]}"


def test_no_missing_values():
    """check for unexpected missing values in critical columns"""
    all_claims = pd.read_csv(OUTPUT_DIR / "all_themes_combined.csv")

    assert all_claims['theme'].notna().all(), "found missing theme values"
    assert all_claims['state'].notna().all(), "found missing state values"
    assert all_claims['file'].notna().all(), "found missing file values"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
