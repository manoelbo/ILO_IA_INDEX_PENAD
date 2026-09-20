"""Frozen artifact and empirical contracts for dissertation Sections 4–5."""

from __future__ import annotations

from dataclasses import dataclass


EXPECTED_PANEL_OBSERVATIONS = 23_319
EXPECTED_PANEL_CBO4 = 436
EXPECTED_PANEL_MONTHS = 54
EXPECTED_CLASSIFIED_CBO4 = 629
EXPECTED_MAIN_TREATED_CBO4 = 75
EXPECTED_MAIN_CONTROL_CBO4 = 266
EXPECTED_OCCUPATION_CASE_CBO6 = 76
EVENT_TIME_MIN = -12
EVENT_TIME_MAX = 24
EVENT_TIME_REFERENCE = -1
MAIN_CONTROLS = (
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
)
MAIN_FIXED_EFFECTS = ("cbo_4d", "periodo")
MAIN_CLUSTER = "cbo_4d"

BACKING_DATA_FILES = (
    "curated_tables/table_4_2a_panel_descriptive_summary.csv",
    "curated_tables/table_4_2b_ilo_cbo_classification.csv",
    "curated_tables/table_4_2c_crosswalk_coverage.csv",
    "curated_tables/table_5_2_1_national_main_results.csv",
    "curated_tables/table_5_2_2_heterogeneity_sex.csv",
    "curated_tables/table_5_2_3_heterogeneity_income.csv",
    "curated_tables/table_5_2_4_b.csv",
    "curated_tables/table_5_2_4_heterogeneity_age_canaries.csv",
    "curated_tables/table_5_2_5_b.csv",
    "curated_tables/table_5_2_6_heterogeneity_education.csv",
    "curated_tables/table_5_2_net_flow_results.csv",
    "curated_tables/table_5_3_1_occupation_case_exposure_summary.csv",
    "national_event_study/age_cohort_canaries_results.csv",
    "national_event_study/crosswalk_exposure_summary.csv",
    "national_event_study/event_study_coefficients_long.csv",
    "national_event_study/event_study_pretrend_tests.csv",
    "national_event_study/heterogeneity_real_wage_triple_did_long.csv",
    "national_event_study/heterogeneity_triple_did_long.csv",
    "national_event_study/main_results_3plus1.csv",
    "national_event_study/net_flow_event_study_coefficients_long.csv",
    "national_event_study/net_flow_event_study_pretrends.csv",
    "national_event_study/net_flow_heterogeneity_long.csv",
    "national_event_study/net_flow_results.csv",
    "national_event_study/poisson_flow_results.csv",
    "national_event_study/real_wage_main_results_3plus1.csv",
    "section5_2_age_pnad/event_study_coefficients_long.csv",
    "section5_2_age_pnad/event_study_pretrends.csv",
    "section5_2_age_pnad/normalized_paths_long.csv",
    "section5_2_dynamic/event_study_coefficients_long.csv",
    "section5_2_dynamic/event_study_pretrends.csv",
    "section5_2_dynamic/income_pnad_b_event_study_coefficients_long.csv",
    "section5_2_dynamic/income_pnad_b_event_study_pretrends.csv",
    "section5_2_dynamic/income_pnad_b_normalized_paths_long.csv",
    "section5_2_dynamic/normalized_paths_long.csv",
    "section5_2_dynamic/race_color_b_event_study_coefficients_long.csv",
    "section5_2_dynamic/race_color_b_event_study_pretrends.csv",
    "section5_2_dynamic/race_color_b_normalized_paths_long.csv",
    "section5_3_occupation_cases/occupation_case_dictionary.csv",
    "section5_3_occupation_cases/occupation_case_exposure_composition.csv",
    "section5_3_occupation_cases/occupation_case_exposure_detail.csv",
    "section5_3_occupation_cases/occupation_case_membership_variants.csv",
    "section5_3_occupation_cases/occupation_case_monthly_paths.csv",
    "section5_3_occupation_cases/occupation_case_preperiod_diagnostics.csv",
    "section5_3_occupation_cases/occupation_case_record_wage_winsor_bounds.csv",
    "section5_3_occupation_cases/occupation_case_sensitivity_matrix.csv",
    "section5_3_occupation_cases/occupation_case_wage_winsor_bounds.csv",
    "section5_3_occupation_cases/result_selection_log.csv",
    "section5_3_occupation_cases/table_5_3_1_occupation_case_exposure_summary.csv",
)


@dataclass(frozen=True)
class TableSpec:
    artifact_id: str
    title: str
    source_authority: str
    source_function: str


@dataclass(frozen=True)
class FigureSpec:
    artifact_id: str
    canonical_name: str
    source_authority: str
    source_function: str


TABLE_SPECS = (
    TableSpec(
        "table_4_2_1_panel_scope",
        "Panel scope",
        "outputs/section4_5_final/tables/table_4_2a_panel_descriptive_summary.csv",
        "section4_5_final.tables.build_panel_descriptive_table",
    ),
    TableSpec(
        "table_4_2_2_ilo_cbo_classification",
        "ILO exposure classification and empirical roles",
        "outputs/section4_5_final/tables/table_4_2b_ilo_cbo_classification.csv",
        "section4_5_final.tables.build_crosswalk_table",
    ),
    TableSpec(
        "table_4_2_3_crosswalk_coverage",
        "Crosswalk and panel coverage",
        "outputs/section4_5_final/tables/table_4_2c_crosswalk_coverage.csv",
        "section4_5_final.tables.build_crosswalk_coverage_table",
    ),
    TableSpec(
        "table_4_2_outcomes",
        "Analysis outcomes",
        "code/sections4_5/publication.py",
        "sections4_5.publication.render_tables",
    ),
    TableSpec(
        "table_5_1_national_results",
        "National average results",
        "outputs/section4_5_final/tables/table_5_2_1_national_main_results.csv",
        "section4_5_final.section5_2_tables.build_national_long",
    ),
    TableSpec(
        "table_5_2_1_sex",
        "Heterogeneity by sex",
        "outputs/section4_5_final/tables/table_5_2_2_heterogeneity_sex.csv",
        "section4_5_final.section5_2_tables.build_heterogeneity_long",
    ),
    TableSpec(
        "table_5_2_2_race_color",
        "Heterogeneity by race or color",
        "outputs/section4_5_final/tables/table_5_2_5_b.csv",
        "section4_5_final.section5_2_tables.build_heterogeneity_long",
    ),
    TableSpec(
        "table_5_2_3_age_pnad",
        "Heterogeneity by PNAD age group",
        "outputs/section4_5_final/tables/table_5_2_4_b.csv",
        "section4_5_final.section5_2_tables.build_heterogeneity_long",
    ),
    TableSpec(
        "table_5_2_4_education",
        "Heterogeneity by education",
        "outputs/section4_5_final/tables/table_5_2_6_heterogeneity_education.csv",
        "section4_5_final.section5_2_tables.build_heterogeneity_long",
    ),
    TableSpec(
        "table_5_2_5_income",
        "Heterogeneity by pre-treatment occupational income",
        "outputs/section4_5_final/tables/table_5_2_3_heterogeneity_income.csv",
        "section4_5_final.section5_2_tables.build_heterogeneity_long",
    ),
    TableSpec(
        "table_5_3_1_occupation_cases",
        "Occupation-case selection and exposure composition",
        "outputs/section5_3_occupation_cases/tables/table_5_3_1_occupation_case_exposure_summary.csv",
        "section5_3_occupation_cases.tables.build_exposure_summary_table",
    ),
    TableSpec(
        "table_a_1_national_main_diagnostics",
        "Appendix national main-outcome diagnostics",
        "outputs/section4_5_final/tables/table_5_2_1_national_main_results.csv",
        "section4_5_final.section5_2_tables._national_diagnostic_panel",
    ),
    TableSpec(
        "table_a_1_national_net_flow_diagnostics",
        "Appendix national net-flow diagnostics",
        "outputs/section4_5_final/tables/table_5_2_net_flow_results.csv",
        "section4_5_final.tables.build_net_flow_table",
    ),
    TableSpec(
        "table_a_2_sex_main_diagnostics",
        "Appendix sex main-outcome diagnostics",
        "outputs/section4_5_final/tables/table_5_2_2_heterogeneity_sex.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_2_sex_net_flow_diagnostics",
        "Appendix sex net-flow diagnostics",
        "outputs/dissertation_section4/final_event_study/tables/net_flow_heterogeneity_long.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_3_race_color_diagnostics",
        "Appendix race or color diagnostics",
        "outputs/section4_5_final/tables/table_5_2_5_b.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_4_age_pnad_main_diagnostics",
        "Appendix PNAD age main-outcome diagnostics",
        "outputs/section4_5_final/tables/table_5_2_4_b.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_4_age_pnad_net_flow_diagnostics",
        "Appendix PNAD age net-flow diagnostics",
        "outputs/dissertation_section4/final_event_study/tables/net_flow_heterogeneity_long.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_4_canaries_age_main_diagnostics",
        "Appendix Canaries age main-outcome diagnostics",
        "outputs/section4_5_final/tables/table_5_2_4_heterogeneity_age_canaries.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_4_canaries_age_net_flow_diagnostics",
        "Appendix Canaries age net-flow diagnostics",
        "outputs/dissertation_section4/final_event_study/tables/net_flow_heterogeneity_long.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_5_education_diagnostics",
        "Appendix education diagnostics",
        "outputs/section4_5_final/tables/table_5_2_6_heterogeneity_education.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_6_income_main_diagnostics",
        "Appendix income main-outcome diagnostics",
        "outputs/section4_5_final/tables/table_5_2_3_heterogeneity_income.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
    TableSpec(
        "table_a_6_income_net_flow_diagnostics",
        "Appendix income net-flow diagnostics",
        "outputs/dissertation_section4/final_event_study/tables/net_flow_heterogeneity_long.csv",
        "section4_5_final.section5_2_tables._heterogeneity_diagnostic_panel",
    ),
)


FIGURE_SPECS = (
    FigureSpec(
        "figure_5_1_national",
        "figure_s5_2_national_main_outcomes_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_national_main_outcomes_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_national_outcomes_figure",
    ),
    FigureSpec(
        "figure_5_2_1_1_sex_admissions",
        "figure_s5_2_sex_admissions_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_sex_admissions_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_2_1_2_sex_real_wage",
        "figure_s5_2_sex_real_admission_wage_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_sex_real_admission_wage_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_2_2_1_race_admissions",
        "figure_s5_2_race_color_b_admissions_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_race_color_b_admissions_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_2_2_2_race_real_wage",
        "figure_s5_2_race_color_b_real_admission_wage_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_race_color_b_real_admission_wage_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_2_3_1_age_admissions",
        "figure_s5_2_age_pnad_all_age_groups_admissions_event_study_paths.png",
        "outputs/section4_5_final/section5_2_age_pnad_combined/figures/figure_s5_2_age_pnad_all_age_groups_admissions_event_study_paths.png",
        "section4_5_final.section5_2_age_pnad_figures.plot_age_outcome_overview_figure",
    ),
    FigureSpec(
        "figure_5_2_3_2_age_real_wage",
        "figure_s5_2_age_pnad_all_age_groups_real_admission_wage_event_study_paths.png",
        "outputs/section4_5_final/section5_2_age_pnad_combined/figures/figure_s5_2_age_pnad_all_age_groups_real_admission_wage_event_study_paths.png",
        "section4_5_final.section5_2_age_pnad_figures.plot_age_outcome_overview_figure",
    ),
    FigureSpec(
        "figure_5_2_4_1_education_admissions",
        "figure_s5_2_education_admissions_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_education_admissions_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_2_4_2_education_real_wage",
        "figure_s5_2_education_real_admission_wage_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_education_real_admission_wage_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_2_5_1_income_admissions",
        "figure_s5_2_income_admissions_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_income_admissions_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_2_5_2_income_real_wage",
        "figure_s5_2_income_real_admission_wage_event_study_paths.png",
        "outputs/section4_5_final/section5_2_dynamic_combined/figures/figure_s5_2_income_real_admission_wage_event_study_paths.png",
        "section4_5_final.section5_2_combined_figures.plot_combined_figure",
    ),
    FigureSpec(
        "figure_5_3_1_occupation_admissions",
        "figure_5_3_1_occupation_cases_admissions_by_age.png",
        "outputs/section5_3_occupation_cases/figures/figure_5_3_1_occupation_cases_admissions_by_age.png",
        "section5_3_occupation_cases.pipeline._write_figures",
    ),
    FigureSpec(
        "figure_5_3_2_occupation_real_wage",
        "figure_5_3_2_occupation_cases_real_admission_wage_by_age.png",
        "outputs/section5_3_occupation_cases/figures/figure_5_3_2_occupation_cases_real_admission_wage_by_age.png",
        "section5_3_occupation_cases.pipeline._write_figures",
    ),
)
