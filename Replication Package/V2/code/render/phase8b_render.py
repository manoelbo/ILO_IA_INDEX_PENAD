"""Orchestrate and audit the 33 CAGED dissertation artifacts."""

from __future__ import annotations

import sys
from pathlib import Path


RENDER_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = RENDER_DIR.parents[1]
RESULTS_DIR = PACKAGE_ROOT / "results"
for _directory in (RENDER_DIR,):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from phase8b_common import atomic_text
from phase8b_figures import render_all_figures
from phase8b_tables import render_all_tables


TABLE_SPECS = (
    (
        "Tabela 4.2.1",
        "table_4_2_1_panel_scope",
        "results/reconciliation/painel_nacional_support.json; "
        "results/models/specification_ladder.csv",
        "none",
        "yes: updated window, months, and occupation-month cells",
    ),
    (
        "Tabela 4.2.2",
        "table_4_2_2_treatment_classification",
        "results/treatment/treatment_variant_comparison.csv",
        "none",
        "yes: reports all three preregistered treatment variants",
    ),
    (
        "Tabela 4.2.3",
        "table_4_2_3_panel_coverage",
        "results/reconciliation/completude_por_tratamento.csv",
        "none",
        "yes: V2 panel coverage",
    ),
    (
        "Tabela 4.3.1",
        "table_4_3_1_outcomes",
        "results/models/specification_ladder.csv; V2 outcome contract",
        "none",
        "yes: five outcomes and PPML count estimators",
    ),
    (
        "Tabela 5.1",
        "table_5_1_national_results",
        "results/models/specification_ladder.csv; "
        "results/diagnostics/pretrend_diagnostics.csv",
        "none",
        "yes: national estimates changed and causal claim fell",
    ),
    (
        "Tabela 5.1.1",
        "table_5_1_1_sector_control",
        "results/models/specification_ladder.csv; "
        "results/models/sector_fixed_effect_ladder.csv; "
        "results/models/sector_level1_vs_level2.csv; "
        "results/diagnostics/pretrend_diagnostics.csv; "
        "results/diagnostics/pretrend_level2.csv",
        "none",
        "yes: co-principal sector control and two-way inference shown",
    ),
    (
        "Tabela A.1",
        "table_a_1_national_diagnostics",
        "results/diagnostics/pretrend_diagnostics.csv; "
        "results/mechanisms/stock_proxy_result.csv",
        "none",
        "yes: wage pretrend fails; B.2 is a cumulative-flow proxy",
    ),
    (
        "Tabela 5.2.1",
        "table_5_2_1_sex",
        "results/models/group_did_results.csv; "
        "results/diagnostics/ddd_pretrends.csv",
        "C (130)",
        "yes: within-group DiD replaces unadjusted V1 display",
    ),
    (
        "Tabela 5.2.2",
        "table_5_2_2_race",
        "results/models/group_did_results.csv; "
        "results/diagnostics/ddd_alternative_partitions_pretrends.csv",
        "C (130)",
        "yes: Negra aggregate constructed from preta and parda",
    ),
    (
        "Tabela 5.2.3",
        "table_5_2_3_age",
        "results/models/group_did_results.csv; "
        "results/diagnostics/ddd_alternative_partitions_pretrends.csv",
        "C (130)",
        "yes: PNAD/IBGE age partition constructed",
    ),
    (
        "Tabela 5.2.4",
        "table_5_2_4_education",
        "results/models/group_did_results.csv; "
        "results/diagnostics/ddd_pretrends.csv",
        "C (130)",
        "yes: BH-adjusted within-group DiD",
    ),
    (
        "Tabela 5.2.5",
        "table_5_2_5_income",
        "results/models/group_did_results.csv; "
        "results/diagnostics/ddd_pretrends.csv",
        "C (130)",
        "yes: BH-adjusted DiD with thin-support warning",
    ),
    (
        "Tabela A.2",
        "table_a_2_sex",
        "results/diagnostics/ddd_pretrends.csv; "
        "results/diagnostics/ddd_family_support.csv",
        "A (100)",
        "yes: nominal and frozen BH values shown together",
    ),
    (
        "Tabela A.3",
        "table_a_3_race",
        "results/diagnostics/ddd_pretrends.csv; "
        "results/diagnostics/ddd_family_support.csv",
        "A (100)",
        "yes: all six race/color categories shown",
    ),
    (
        "Tabela A.4",
        "table_a_4_age",
        "results/diagnostics/ddd_pretrends.csv; "
        "results/diagnostics/ddd_alternative_partitions_pretrends.csv",
        "A (100) and B (30)",
        "yes: Canaries and PNAD/IBGE panels shown with family IDs",
    ),
    (
        "Tabela A.5",
        "table_a_5_education",
        "results/diagnostics/ddd_pretrends.csv; "
        "results/diagnostics/ddd_family_support.csv",
        "A (100)",
        "yes: nominal and frozen BH values shown together",
    ),
    (
        "Tabela A.6",
        "table_a_6_income",
        "results/diagnostics/ddd_pretrends.csv; "
        "results/diagnostics/ddd_family_support.csv",
        "A (100)",
        "yes: support limitations made explicit",
    ),
    (
        "Tabela C.1",
        "table_c_1_occupation_cases",
        "data/derived/occupation_cases/occupation_case_dictionary.csv; "
        "results/mechanisms/occupation_case_panel_support.json",
        "none",
        "yes: six cases and frozen-code composition constructed",
    ),
)


FIGURE_SPECS = (
    (
        "Figura 5.1",
        "figure_5_1_national_event_studies",
        "results/models/national_event_study_extended_coefficients.csv",
        "none",
        "yes: V2 event studies through +41 with pre-period means",
    ),
    (
        "Figura 5.2.1.1",
        "figure_5_2_1_1_sex_admissions",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: V2 group event study",
    ),
    (
        "Figura 5.2.1.2",
        "figure_5_2_1_2_sex_wage",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: V2 group event study",
    ),
    (
        "Figura 5.2.2.1",
        "figure_5_2_2_1_race_admissions",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: Branca/Negra main partition",
    ),
    (
        "Figura 5.2.2.2",
        "figure_5_2_2_2_race_wage",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: Branca/Negra main partition",
    ),
    (
        "Figura 5.2.3.1",
        "figure_5_2_3_1_age_admissions",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: PNAD/IBGE main partition",
    ),
    (
        "Figura 5.2.3.2",
        "figure_5_2_3_2_age_wage",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: PNAD/IBGE main partition",
    ),
    (
        "Figura 5.2.3.3",
        "figure_5_2_3_3_canaries_22_25_wage",
        "results/models/canaries_22_25_wage_event_study.csv",
        "none",
        "yes: Canaries 22-25 cohort, the only contrast whose joint pretrend "
        "test is not rejected. Rendered by its own DAG node, "
        "code/render/canaries_wage_figure.py, not by phase8b_figures.",
    ),
    (
        "Figura 5.2.4.1",
        "figure_5_2_4_1_education_admissions",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: V2 group event study",
    ),
    (
        "Figura 5.2.4.2",
        "figure_5_2_4_2_education_wage",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: V2 group event study",
    ),
    (
        "Figura 5.2.5.1",
        "figure_5_2_5_1_income_admissions",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: V2 group event study with thin-support group",
    ),
    (
        "Figura 5.2.5.2",
        "figure_5_2_5_2_income_wage",
        "results/models/group_event_study_coefficients.csv",
        "none",
        "yes: V2 group event study with thin-support group",
    ),
    (
        "Figura 5.2.6",
        "figure_5_2_6_group_outcome_forest",
        "results/models/group_did_results.csv; "
        "results/diagnostics/ddd_multiplicity_results.csv; "
        "results/backing_data/figure_5_2_6_group_outcome_forest.csv",
        "C (130); A (100) used only for the interpretation note",
        "yes: all 130 within-group DiD estimates and support flags shown",
    ),
    (
        "Figura C.1",
        "figure_c_1_occupation_cases_admissions_by_age",
        "results/mechanisms/occupation_case_trajectories.csv",
        "none",
        "yes: constructed through the terminal 202506-202605 window",
    ),
    (
        "Figura C.2",
        "figure_c_2_occupation_cases_wage_by_age",
        "results/mechanisms/occupation_case_trajectories.csv",
        "none",
        "yes: constructed through the terminal 202506-202605 window",
    ),
)


def artifact_registry() -> list[dict[str, str]]:
    """Return the frozen 18-table and 15-figure CAGED render contract."""
    rows: list[dict[str, str]] = []
    for artifact_id, stem, source, family, claim_changed in TABLE_SPECS:
        rows.append(
            {
                "artifact_id": artifact_id,
                "artifact_type": "table",
                "csv_path": f"results/tables/{stem}.csv",
                "md_path": f"results/tables/{stem}.md",
                "png_path": "",
                "source": source,
                "multiplicity_family": family,
                "claim_changed": claim_changed,
            }
        )
    for artifact_id, stem, source, family, claim_changed in FIGURE_SPECS:
        rows.append(
            {
                "artifact_id": artifact_id,
                "artifact_type": "figure",
                "csv_path": "",
                "md_path": "",
                "png_path": f"results/figures/{stem}.png",
                "source": source,
                "multiplicity_family": family,
                "claim_changed": claim_changed,
            }
        )
    return rows


def _validate_artifacts(registry: list[dict[str, str]]) -> None:
    missing: list[str] = []
    for row in registry:
        for field in ("csv_path", "md_path", "png_path"):
            relative_path = row[field]
            if relative_path and not (PACKAGE_ROOT / relative_path).is_file():
                missing.append(relative_path)
    if missing:
        raise RuntimeError(
            "Phase 8B render is incomplete: " + ", ".join(missing)
        )


def _render_report(registry: list[dict[str, str]]) -> None:
    header = (
        "# Phase 8B rendering audit\n\n"
        "This report inventories the 33 CAGED artifacts rendered for the "
        "dissertation. A table artifact is one logical item represented by "
        "its CSV and Markdown pair.\n\n"
        "| ID | Type | Output | Source | Multiplicity family | "
        "Claim changed? |\n"
        "|---|---|---|---|---|---|\n"
    )
    rows: list[str] = []
    for row in registry:
        outputs = ", ".join(
            row[field]
            for field in ("csv_path", "md_path", "png_path")
            if row[field]
        )
        values = (
            row["artifact_id"],
            row["artifact_type"],
            outputs,
            row["source"],
            row["multiplicity_family"],
            row["claim_changed"],
        )
        rows.append("| " + " | ".join(values) + " |")
    footer = (
        "\n\n## Inventory boundary\n\n"
        "- Section 3 and the complementary RAIS, PNADc, and spatial "
        "artifacts are rendered by their component pipelines.\n"
        "- Figure 5.2.6 displays all 130 Family C within-group DiD "
        "estimates; its backing table is generated from the same signed "
        "Family C results without applying BH a second time.\n"
        "- Every event-study figure marks November 2022, the +23 frozen-data "
        "boundary, and the corresponding pre-period coefficient mean.\n"
        "- No table or figure is evidence of a causal effect because the "
        "Phase 8A pretrend diagnostics fail across the available national "
        "specifications.\n"
    )
    atomic_text(
        header + "\n".join(rows) + footer,
        RESULTS_DIR / "RENDERIZACAO_8B.md",
    )


def render_phase8b() -> None:
    """Render all artifacts, validate the contract, and write the audit."""
    render_all_tables()
    render_all_figures()
    registry = artifact_registry()
    _validate_artifacts(registry)
    _render_report(registry)


if __name__ == "__main__":
    render_phase8b()
