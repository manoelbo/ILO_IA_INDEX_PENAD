#!/usr/bin/env python3
"""Build the compact curated tables consumed by the replication renderer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from section4_5_final.section5_2_tables import (
    build_heterogeneity_long,
    build_national_long,
)
from section4_5_final.tables import (
    build_crosswalk_coverage_table,
    build_crosswalk_table,
    build_net_flow_table,
    build_panel_descriptive_table,
)


ROOT = Path(__file__).resolve().parents[2]
EVENT_TABLES = (
    ROOT
    / "outputs"
    / "dissertation_section4"
    / "final_event_study"
    / "tables"
)
OUTPUT_TABLES = ROOT / "outputs" / "section4_5_final" / "tables"


def read_event_table(filename: str) -> pd.DataFrame:
    path = EVENT_TABLES / filename
    if not path.is_file():
        raise FileNotFoundError(f"Missing event-study table: {path}")
    return pd.read_csv(path)


def build_sources() -> dict[str, pd.DataFrame]:
    return {
        "panel": pd.read_parquet(
            ROOT / "data" / "output" / "painel_2b_ready.parquet"
        ),
        "classification": pd.read_csv(
            ROOT
            / "outputs"
            / "treatment_scenario_grid"
            / "scenario_cbo_classification.csv",
            dtype={"cbo_4d": str},
        ),
        "crosswalk": read_event_table("crosswalk_exposure_summary.csv"),
        "main": read_event_table("main_results_3plus1.csv"),
        "real_main": read_event_table("real_wage_main_results_3plus1.csv"),
        "main_pretrends": read_event_table(
            "event_study_pretrend_tests.csv"
        ),
        "net_flow": read_event_table("net_flow_results.csv"),
        "net_flow_pretrends": read_event_table(
            "net_flow_event_study_pretrends.csv"
        ),
        "net_flow_heterogeneity": read_event_table(
            "net_flow_heterogeneity_long.csv"
        ),
        "heterogeneity": read_event_table(
            "heterogeneity_triple_did_long.csv"
        ),
        "heterogeneity_real_wage": read_event_table(
            "heterogeneity_real_wage_triple_did_long.csv"
        ),
        "canaries_age": read_event_table("age_cohort_canaries_results.csv"),
    }


def write_table(filename: str, frame: pd.DataFrame) -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        OUTPUT_TABLES / filename,
        index=False,
        lineterminator="\n",
    )


def run() -> None:
    sources = build_sources()
    write_table(
        "table_4_2a_panel_descriptive_summary.csv",
        build_panel_descriptive_table(sources),
    )
    write_table(
        "table_4_2b_ilo_cbo_classification.csv",
        build_crosswalk_table(sources),
    )
    write_table(
        "table_4_2c_crosswalk_coverage.csv",
        build_crosswalk_coverage_table(sources),
    )
    write_table(
        "table_5_2_1_national_main_results.csv",
        build_national_long(sources),
    )
    for table_id, filename in (
        ("sex", "table_5_2_2_heterogeneity_sex.csv"),
        ("income", "table_5_2_3_heterogeneity_income.csv"),
        ("age_pnad", "table_5_2_4_b.csv"),
        (
            "age_canaries",
            "table_5_2_4_heterogeneity_age_canaries.csv",
        ),
        ("race_color_b", "table_5_2_5_b.csv"),
        ("education", "table_5_2_6_heterogeneity_education.csv"),
    ):
        write_table(
            filename,
            build_heterogeneity_long(sources, table_id),
        )
    write_table(
        "table_5_2_net_flow_results.csv",
        build_net_flow_table(sources),
    )
    occupation = (
        ROOT
        / "outputs"
        / "section5_3_occupation_cases"
        / "tables"
        / "table_5_3_1_occupation_case_exposure_summary.csv"
    )
    if not occupation.is_file():
        raise FileNotFoundError(
            f"Missing occupation-case summary table: {occupation}"
        )
    write_table(
        "table_5_3_1_occupation_case_exposure_summary.csv",
        pd.read_csv(occupation),
    )
    print(
        "[replication_curated_tables] Wrote 12 compact source tables.",
        flush=True,
    )


if __name__ == "__main__":
    run()
