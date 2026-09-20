"""Configuration and validation for the Section 5.3 occupation cases."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DICTIONARY_PATH = ROOT / "data" / "input" / "occupation_case_dictionary.csv"
OFFICIAL_METADATA_PATH = (
    ROOT / "data" / "input" / "occupation_case_official_metadata.csv"
)
SOURCE_MANIFEST_PATH = ROOT / "data" / "input" / "occupation_case_dictionary_source_manifest.csv"
DATA_RAW = ROOT / "data" / "raw"
IPCA_PATH = ROOT / "data" / "processed" / "ipca_mensal.parquet"
CLASSIFICATION_PATH = ROOT / "outputs" / "treatment_scenario_grid" / "scenario_cbo_classification.csv"
OUTPUT_ROOT = ROOT / "outputs" / "section5_3_occupation_cases"
TABLE_DIR = OUTPUT_ROOT / "tables"
FIGURE_DIR = OUTPUT_ROOT / "figures"
AUDIT_DIR = OUTPUT_ROOT / "audit"
INTERMEDIATE_DIR = OUTPUT_ROOT / "intermediate"

START_PERIOD = "2021-01"
END_PERIOD = "2025-06"
BASELINE_PERIOD = "2022-10"
SHOCK_DATE = "2022-11-30"
TERMINAL_START = "2025-01"
TERMINAL_END = "2025-06"
MIN_BASELINE_SUPPORT = 30

CASE_ORDER = [
    "software_developers",
    "customer_service",
    "marketing_sales_managers",
    "production_supervisors",
    "stock_clerks",
    "health_care_aides",
]
PRIMARY_CASE_SIZES = {
    "software_developers": 7,
    "customer_service": 2,
    "marketing_sales_managers": 2,
    "production_supervisors": 53,
    "stock_clerks": 5,
    "health_care_aides": 7,
}
CASE_SHORT_LABELS = {
    "software_developers": "Desenvolvedores de software",
    "customer_service": "Atendimento ao cliente",
    "marketing_sales_managers": "Gerentes de marketing e vendas",
    "production_supervisors": "Supervisores de produção",
    "stock_clerks": "Estoquistas e repositores",
    "health_care_aides": "Auxiliares de saúde e cuidado",
}
CANARIES_BENCHMARK = {
    "software_developers": "Alta exposição",
    "customer_service": "Alta exposição",
    "marketing_sales_managers": "Quintil 4",
    "production_supervisors": "Quintil 3",
    "stock_clerks": "Quintil 2",
    "health_care_aides": "Quintil 1",
}

AGE_ORDER = [
    "age_22_25",
    "age_26_30",
    "age_31_34",
    "age_35_40",
    "age_41_49",
    "age_50_plus",
]
AGE_LABELS = {
    "age_22_25": "22–25",
    "age_26_30": "26–30",
    "age_31_34": "31–34",
    "age_35_40": "35–40",
    "age_41_49": "41–49",
    "age_50_plus": "50+",
}

DEMOGRAPHIC_SPECS = {
    "sex": [("women", "Mulheres"), ("men", "Homens")],
    "race_color": [
        ("race_black_combined", "Negros"),
        ("race_white", "Brancos"),
    ],
    "education": [
        ("higher_education", "Ensino superior"),
        ("education_other", "Demais níveis"),
    ],
}

DIMENSION_GROUPS = {
    "overall": [("all", "Total")],
    "age": [(group_id, AGE_LABELS[group_id]) for group_id in AGE_ORDER],
    **DEMOGRAPHIC_SPECS,
}


def load_occupation_dictionary(path: Path = DICTIONARY_PATH) -> pd.DataFrame:
    """Load and validate the frozen semantic occupation dictionary."""
    data = pd.read_csv(path, dtype={"cbo_6d": str})
    required = {
        "case_id",
        "case_label_pt",
        "cbo_6d",
        "cbo_title",
        "primary_included",
        "variant_membership",
        "mapping_confidence",
        "semantic_rationale",
        "source_name",
        "source_url",
        "retrieved_on",
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise RuntimeError(f"Occupation dictionary is missing columns: {missing}")
    data["cbo_6d"] = data["cbo_6d"].astype(str).str.zfill(6)
    if not bool(data["cbo_6d"].str.fullmatch(r"\d{6}", na=False).all()):
        raise RuntimeError("Occupation dictionary contains an invalid CBO 6-digit code.")
    data["primary_included"] = data["primary_included"].astype(str).str.lower().map(
        {"true": True, "false": False}
    )
    if data["primary_included"].isna().any():
        raise RuntimeError("primary_included must contain only True or False.")
    primary = data[data["primary_included"]]
    if primary["cbo_6d"].duplicated().any():
        raise RuntimeError("Primary occupation cases contain overlapping CBO codes.")
    observed_order = primary["case_id"].drop_duplicates().tolist()
    if observed_order != CASE_ORDER:
        raise RuntimeError(f"Occupation case order differs from the frozen contract: {observed_order}")
    observed_sizes = primary.groupby("case_id", sort=False)["cbo_6d"].nunique().to_dict()
    if observed_sizes != PRIMARY_CASE_SIZES:
        raise RuntimeError(f"Primary occupation-case sizes differ from the frozen contract: {observed_sizes}")
    if not OFFICIAL_METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Stable official CBO metadata extract is missing: {OFFICIAL_METADATA_PATH}"
        )
    metadata = pd.read_csv(OFFICIAL_METADATA_PATH, dtype={"cbo_6d": str})
    metadata["cbo_6d"] = metadata["cbo_6d"].astype(str).str.zfill(6)
    required_metadata = {"cbo_6d", "official_title", "official_activities"}
    missing_metadata = sorted(required_metadata - set(metadata.columns))
    if missing_metadata:
        raise RuntimeError(
            f"Official CBO metadata extract is missing columns: {missing_metadata}"
        )
    if metadata["cbo_6d"].duplicated().any() or set(metadata["cbo_6d"]) != set(data["cbo_6d"]):
        raise RuntimeError("Official CBO metadata extract does not match the frozen dictionary.")
    official_titles = metadata.set_index("cbo_6d")["official_title"].sort_index()
    dictionary_titles = data.set_index("cbo_6d")["cbo_title"].sort_index()
    if not official_titles.equals(dictionary_titles):
        raise RuntimeError("Dictionary titles differ from the stable official CBO extract.")
    if metadata["official_activities"].fillna("").str.len().eq(0).any():
        raise RuntimeError("Official CBO metadata extract contains occupations without tasks.")
    return data
