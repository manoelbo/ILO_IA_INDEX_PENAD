"""Configuration for the final Section 4/5 curation package."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = ROOT / "outputs" / "dissertation_section4"
SECTION5_3_ROOT = ROOT / "outputs" / "section5_3_occupation_cases"
PANEL_PATH = ROOT / "data" / "output" / "painel_2b_ready.parquet"
CLASSIFICATION_PATH = ROOT / "outputs" / "treatment_scenario_grid" / "scenario_cbo_classification.csv"
OUTPUT_ROOT = ROOT / "outputs" / "section4_5_final"
TABLE_DIR = OUTPUT_ROOT / "tables"
FIGURE_DIR = OUTPUT_ROOT / "figures"
AUDIT_DIR = OUTPUT_ROOT / "audit"

EXPECTED_FIGURES = [
    "figure_4_1_empirical_timeline.png",
    "figure_4_2_caged_crosswalk_pipeline.png",
    "figure_5_1_national_event_studies.png",
    "figure_5_3_1_occupation_cases_admissions_by_age.png",
    "figure_5_3_2_occupation_cases_real_admission_wage_by_age.png",
    "figure_a_1_connectivity_extension.png",
    "figure_b_1_occupation_cases_by_sex.png",
    "figure_b_2_occupation_cases_by_race_color.png",
    "figure_b_3_occupation_cases_by_education.png",
]

EXPECTED_TABLES = [
    "table_4_1_crosswalk_exposure_summary",
    "table_4_2a_panel_descriptive_summary",
    "table_4_2b_ilo_cbo_classification",
    "table_4_2c_crosswalk_coverage",
    "table_5_2_1_national_main_results",
    "table_5_2_2_heterogeneity_sex",
    "table_5_2_3_heterogeneity_income",
    "table_5_2_3_b",
    "table_5_2_4_heterogeneity_age_canaries",
    "table_5_2_4_b",
    "table_5_2_5_heterogeneity_race_color",
    "table_5_2_5_b",
    "table_5_2_6_heterogeneity_education",
    "table_5_2_net_flow_results",
    "table_5_3_1_occupation_case_exposure_summary",
    "table_5_5_robustness_and_limits",
    "table_a_1_connectivity_extension",
    "table_a_2_top_30_results",
    "table_b_1_occupation_case_age_terminal_matrix",
    "table_b_2_occupation_case_preperiod_diagnostics",
    "table_b_3_occupation_case_sensitivity_matrix",
    "table_b_4_occupation_case_demographic_terminal_matrix",
    "table_b_5_legacy_manual_group_diagnostics",
]

CORE_OCCUPATION_GROUPS = [
    "software_it_core",
    "customer_contact",
    "finance_accounting_admin",
    "creative_communication_language",
]

CORE_OUTCOMES = [
    "ln_admissoes",
    "ln_desligamentos",
    "ln_salario_real_adm",
]
