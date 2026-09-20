"""Configuration for Section 4 result evaluation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SECTION4_ROOT = ROOT / "outputs" / "dissertation_section4"
OUTPUT_DIR = SECTION4_ROOT / "result_evaluation"

SOURCE_DIRS = [
    SECTION4_ROOT / "final_event_study" / "tables",
    SECTION4_ROOT / "connectivity_extension" / "tables",
    SECTION4_ROOT / "manual_occupation_groups_extension" / "tables",
    SECTION4_ROOT / "manual_tech_extension" / "tables",
    SECTION4_ROOT / "event_study",
    SECTION4_ROOT / "event_study_profiles",
    SECTION4_ROOT / "tables",
]

SKIP_FILE_PATTERNS = [
    "coefficients_long",
    "event_study_coefficients",
    "pretrend_tests",
    "pretrends",
    "crosswalk",
    "sample_summary",
    "cbo_roles",
    "keyword_audit",
    "manual_review",
    "evidence_summary",
    "balance",
]

TOP_N = 30
JUDGE_POOL_N = 80

MINIMUM_TAG_COUNTS = {
    "admission_flow": 4,
    "separation_flow": 4,
    "net_flow": 2,
    "wage_any": 6,
    "composition_or_heterogeneity": 5,
    "spatial_connectivity": 3,
    "occupational_mechanism": 3,
}
