"""Source loading for final Section 4/5 curation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import CLASSIFICATION_PATH, PANEL_PATH, SECTION5_3_ROOT, SOURCE_ROOT


def require_csv(relative_path: str) -> pd.DataFrame:
    path = SOURCE_ROOT / relative_path
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Required source CSV is missing or empty: {path}")
    return pd.read_csv(path)


def require_local_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Required source CSV is missing or empty: {path}")
    return pd.read_csv(path)


def require_parquet(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Required source parquet is missing or empty: {path}")
    return pd.read_parquet(path)


def source_path(relative_path: str) -> Path:
    return SOURCE_ROOT / relative_path


def load_sources() -> dict[str, pd.DataFrame]:
    occupation_case_tables = SECTION5_3_ROOT / "tables"
    return {
        "panel": require_parquet(PANEL_PATH),
        "classification": require_local_csv(CLASSIFICATION_PATH),
        "crosswalk": require_csv("final_event_study/tables/crosswalk_exposure_summary.csv"),
        "main": require_csv("final_event_study/tables/main_results_3plus1.csv"),
        "real_main": require_csv("final_event_study/tables/real_wage_main_results_3plus1.csv"),
        "main_pretrends": require_csv("final_event_study/tables/event_study_pretrend_tests.csv"),
        "event_study": require_csv("final_event_study/tables/event_study_coefficients_long.csv"),
        "net_flow": require_csv("final_event_study/tables/net_flow_results.csv"),
        "net_flow_pretrends": require_csv("final_event_study/tables/net_flow_event_study_pretrends.csv"),
        "net_flow_event_study": require_csv("final_event_study/tables/net_flow_event_study_coefficients_long.csv"),
        "net_flow_heterogeneity": require_csv("final_event_study/tables/net_flow_heterogeneity_long.csv"),
        "control_ladder": require_csv("final_event_study/tables/model_ladder_controls.csv"),
        "robustness": require_csv("final_event_study/tables/robustness_results_long.csv"),
        "heterogeneity": require_csv("final_event_study/tables/heterogeneity_triple_did_long.csv"),
        "heterogeneity_real_wage": require_csv("final_event_study/tables/heterogeneity_real_wage_triple_did_long.csv"),
        "canaries_age": require_csv("final_event_study/tables/age_cohort_canaries_results.csv"),
        "occupation_main": require_csv("manual_occupation_groups_extension/tables/occupation_group_main_results.csv"),
        "occupation_pretrends": require_csv("manual_occupation_groups_extension/tables/occupation_group_event_study_pretrends.csv"),
        "occupation_canaries": require_csv("manual_occupation_groups_extension/tables/occupation_group_canaries_age_heterogeneity.csv"),
        "occupation_demographic": require_csv("manual_occupation_groups_extension/tables/occupation_group_demographic_heterogeneity.csv"),
        "occupation_summary": require_csv("manual_occupation_groups_extension/tables/occupation_group_evidence_summary.csv"),
        "occupation_audit": require_csv("manual_occupation_groups_extension/audit/manual_group_cbo_audit.csv"),
        "connectivity_main": require_csv("connectivity_extension/tables/main_connectivity_triple_did.csv"),
        "connectivity_pretrends": require_csv("connectivity_extension/tables/connectivity_event_study_pretrends.csv"),
        "connectivity_event_study": require_csv("connectivity_extension/tables/connectivity_event_study_coefficients.csv"),
        "connectivity_net_flow": require_csv("connectivity_extension/tables/connectivity_net_flow_results.csv"),
        "top30": require_csv("result_evaluation/top_30_results.csv"),
        "occupation_case_exposure_summary": require_local_csv(
            occupation_case_tables
            / "table_5_3_1_occupation_case_exposure_summary.csv"
        ),
        "occupation_case_age_terminal": require_local_csv(
            occupation_case_tables / "occupation_case_age_terminal_matrix.csv"
        ),
        "occupation_case_preperiod": require_local_csv(
            occupation_case_tables / "occupation_case_preperiod_diagnostics.csv"
        ),
        "occupation_case_sensitivity": require_local_csv(
            occupation_case_tables / "occupation_case_sensitivity_matrix.csv"
        ),
        "occupation_case_demographic": require_local_csv(
            occupation_case_tables
            / "occupation_case_demographic_terminal_matrix.csv"
        ),
    }
