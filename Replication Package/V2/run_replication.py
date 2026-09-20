#!/usr/bin/env python3
"""Public V2 replication CLI with an explicit estimation DAG."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PACKAGE_ROOT = Path(__file__).resolve().parent
REPLICATION_CODE = PACKAGE_ROOT / "code" / "replication"
COMMON_CODE = PACKAGE_ROOT / "code" / "common"
if str(REPLICATION_CODE) not in sys.path:
    sys.path.insert(0, str(REPLICATION_CODE))
if str(COMMON_CODE) not in sys.path:
    sys.path.insert(0, str(COMMON_CODE))

from contracts import validate_reference
from data_manifest import validate_manifest as validate_analytical_bundle
from paths import ReplicationPaths
from registry import (
    expected_publication_outputs,
    validate_dag_nodes,
    validate_publications,
)
from reference_validation import compare_reproduced_components
from raw_cache import validate_raw_cache


REESTIMATED = "RE-ESTIMATED"
FROZEN_VALIDATED = "FROZEN ESTIMATE VALIDATED"
RENDERED = "ARTIFACT RENDERED"
DATA_REBUILT = "DATA REBUILT"
DEFAULT_PATHS = ReplicationPaths.defaults()
DEFAULT_RAW_DIR = DEFAULT_PATHS.raw
DEFAULT_DATA_DIR = DEFAULT_PATHS.data
DEFAULT_OUTPUT_DIR = DEFAULT_PATHS.reproduced
LEGACY_RESULTS_DIR = PACKAGE_ROOT / "results"
REFERENCE_DIR = PACKAGE_ROOT / "results" / "reference"
COMPONENTS = ("section3", "caged", "rais", "pnadc", "spatial")


DAG_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "group_did_family_c": (
        "ddd_pretrend_diagnostics",
        "ddd_alternative_partitions_pretrends",
    ),
    "audit_wage_composition": (
        "national_specification_ladder",
        "hourly_wage_and_schedules",
        "group_did_family_c",
    ),
    "complete_r_replication": ("export_complete_r_inputs",),
    "compare_complete_r_replication": ("complete_r_replication",),
    "honest_did": ("compare_complete_r_replication",),
    "honest_did_smoothness": ("honest_did",),
    "phase8b_rendering": ("canaries_wage_figure",),
}


@dataclass(frozen=True)
class DagNode:
    node_id: str
    description: str
    command: tuple[str, ...]
    disposition: str
    outputs: tuple[str, ...] = ()
    inferential: bool = False
    component: str = "caged"


def validate_dag_dependencies(nodes: Sequence[DagNode]) -> None:
    """Reject missing, duplicated, or inverted producer dependencies."""
    identifiers = [node.node_id for node in nodes]
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("DAG contains duplicate node IDs")
    positions = {
        node_id: position
        for position, node_id in enumerate(identifiers)
    }
    for consumer, producers in DAG_DEPENDENCIES.items():
        if consumer not in positions:
            continue
        for producer in producers:
            if producer not in positions:
                raise RuntimeError(
                    f"DAG node {consumer} requires missing producer {producer}"
                )
            if positions[consumer] <= positions[producer]:
                raise RuntimeError(
                    f"DAG node {consumer} must run after {producer}"
                )


def _python(script: str, *arguments: str) -> tuple[str, ...]:
    return (
        sys.executable,
        str(PACKAGE_ROOT / script),
        *arguments,
    )


def _reference_node() -> DagNode:
    return DagNode(
        node_id="validate_reference_manifest",
        description=(
            "Validate the signed frozen reference before any comparison"
        ),
        command=_python(
            "code/replication/contracts.py",
            "validate",
        ),
        disposition=FROZEN_VALIDATED,
        component="common",
    )


def _construction_nodes(raw_dir: Path, data_dir: Path) -> list[DagNode]:
    movements = data_dir / "interim" / "movimentacoes"
    return [
        DagNode(
            "download_official_caged",
            "Download any missing archive in the frozen official vintage",
            _python(
                "code/caged/ingest/download.py",
                "--inventory",
                str(raw_dir / "ftp_inventory.csv"),
                "--data-dir",
                str(raw_dir),
                "--manifest",
                str(raw_dir / "manifest.json"),
            ),
            DATA_REBUILT,
        ),
        DagNode(
            "verify_official_caged",
            "Hash-verify every archive against the frozen inventory manifest",
            _python(
                "code/caged/ingest/download.py",
                "--inventory",
                str(raw_dir / "ftp_inventory.csv"),
                "--data-dir",
                str(raw_dir),
                "--manifest",
                str(raw_dir / "manifest.json"),
                "--verify-only",
            ),
            FROZEN_VALIDATED,
        ),
        DagNode(
            "build_signed_movements",
            "Rebuild MOV + FOR - EXC partitions by fact month",
            _python(
                "code/caged/ingest/build_movements.py",
                "--inventory",
                str(raw_dir / "ftp_inventory.csv"),
                "--vintage-dir",
                str(raw_dir),
                "--output-dir",
                str(movements),
            ),
            DATA_REBUILT,
            ("reconciliation/origem_por_competencia.csv",),
        ),
        DagNode(
            "classify_treatment",
            "Reproduce the frozen MTE-to-ILO treatment classification",
            _python("code/caged/panel/crosswalk.py", "classify"),
            DATA_REBUILT,
            (
                "reconciliation/crosswalk_coverage.json",
                "reconciliation/treatment_classification_validation.json",
            ),
        ),
        DagNode(
            "build_treatment_variants",
            "Rebuild preregistered treatment variants",
            _python("code/caged/panel/treatment_variants.py"),
            DATA_REBUILT,
            (
                "treatment/treatment_variant_comparison.csv",
                "treatment/treatment_variant_support.json",
            ),
        ),
        DagNode(
            "freeze_official_ipca",
            "Download and freeze the registered BCB IPCA series",
            _python("code/caged/panel/build_panel.py", "freeze-ipca"),
            DATA_REBUILT,
        ),
        DagNode(
            "build_national_panel",
            "Rebuild the CBO4-by-month national panel",
            _python("code/caged/panel/build_panel.py", "build"),
            DATA_REBUILT,
            ("reconciliation/painel_nacional_support.json",),
        ),
        DagNode(
            "freeze_official_cnae",
            "Download and freeze the registered IBGE CNAE structure",
            _python("code/caged/panel/build_panel.py", "freeze-cnae"),
            DATA_REBUILT,
        ),
        DagNode(
            "build_sector_panel",
            "Rebuild the CBO4-by-CNAE-by-month panel",
            _python("code/caged/panel/build_panel.py", "build-sector"),
            DATA_REBUILT,
            (
                "reconciliation/painel_cbo_cnae_support.json",
                "reconciliation/cnae_month_treatment_support.csv",
            ),
        ),
    ]


def _phase8b_render_outputs() -> tuple[str, ...]:
    outputs = expected_publication_outputs(
        component="caged",
        include_markdown_pairs=True,
    )
    outputs.remove("figures/figure_5_2_3_3_canaries_22_25_wage.png")
    return (
        *sorted(outputs),
        "backing_data/figure_5_2_6_group_outcome_forest.csv",
        "RENDERIZACAO_8B.md",
    )


def _reproduce_caged_backing_node(data_dir: Path) -> DagNode:
    return DagNode(
        "materialize_caged_construction_backing",
        "Validate and materialize frozen construction backing data",
        _python(
            "code/caged/backing.py",
            "--data-dir",
            str(data_dir),
        ),
        FROZEN_VALIDATED,
        (
            "reconciliation/build_movements_metrics.json",
            "reconciliation/cnae_month_treatment_support.csv",
            "reconciliation/crosswalk_coverage.json",
            "reconciliation/origem_por_competencia.csv",
            "reconciliation/painel_cbo_cnae_support.json",
            "reconciliation/painel_nacional_support.json",
            "reconciliation/treatment_classification_validation.json",
            "treatment/treatment_variant_comparison.csv",
            "treatment/treatment_variant_support.json",
        ),
    )


def _analysis_nodes(mode: str) -> list[DagNode]:
    return [
        DagNode(
            "vintage_completeness_diagnostics",
            "Recompute late-declaration and variable-continuity diagnostics",
            _python("code/caged/ingest/diagnose_vintage.py"),
            DATA_REBUILT,
            (
                "reconciliation/completude_por_competencia.csv",
                "reconciliation/completude_por_grupo_cbo.csv",
                "reconciliation/completude_por_tratamento.csv",
                "reconciliation/continuidade_variaveis.csv",
                "reconciliation/completude_por_competencia.png",
                "reconciliation/diagnostico_vintage_metrics.json",
            ),
        ),
        DagNode(
            "pdet_monthly_reconciliation",
            "Reconcile rebuilt movements with the official adjusted PDET series",
            _python(
                "code/caged/ingest/reconcile_pdet.py",
                "all" if mode == "full" else "reconcile",
            ),
            FROZEN_VALIDATED,
            (
                "reconciliation/pdet_vs_v2_mensal.csv",
                "reconciliation/pdet_vs_v2_support.json",
            ),
        ),
        DagNode(
            "v1_gate_on_v2_panel",
            "Re-estimate the exact V1 model on the V2 panel",
            _python("code/caged/models/gate_v1_model.py"),
            REESTIMATED,
            (
                "reconciliation/gate_modelo_antigo.csv",
                "reconciliation/GATE_MODELO_ANTIGO.md",
            ),
            True,
        ),
        DagNode(
            "national_specification_ladder",
            "Re-estimate PPML, real wage, net flow, and control ladder",
            _python("code/caged/models/specification_ladder.py"),
            REESTIMATED,
            ("models/specification_ladder.csv",),
            True,
        ),
        DagNode(
            "balanced_event_studies",
            "Re-estimate the complete balanced event-study grid",
            _python("code/caged/models/event_study.py"),
            REESTIMATED,
            (
                "models/event_study_coefficients.csv",
                "models/long_run_horizons.csv",
            ),
            True,
        ),
        DagNode(
            "long_run_horizon_estimates",
            "Estimate the four preregistered long-run horizons",
            _python("code/caged/models/long_run_horizons.py"),
            REESTIMATED,
            (
                "models/long_run_horizon_estimates.csv",
                "models/long_run_horizon_reconciliation.csv",
                "models/LONG_RUN_HORIZONS.md",
            ),
            True,
        ),
        DagNode(
            "secondary_log_flow_estimators",
            "Re-estimate the secondary OLS log(1 + flow) models",
            _python("code/caged/models/secondary_flow_models.py"),
            REESTIMATED,
            (
                "models/secondary_log_flow_results.csv",
                "models/secondary_log_flow_support.json",
                "models/SECONDARY_FLOW_ESTIMATORS.md",
            ),
            True,
        ),
        DagNode(
            "sector_fixed_effects",
            "Re-estimate the sector fixed-effect and inference ladder",
            _python("code/caged/models/sector_models.py"),
            REESTIMATED,
            (
                "models/sector_fixed_effect_ladder.csv",
                "models/sector_level1_vs_level2.csv",
            ),
            True,
        ),
        DagNode(
            "exact_pretrends",
            "Re-estimate exact-model pretrends and HonestDiD inputs",
            _python("code/caged/models/pretrends.py"),
            REESTIMATED,
            (
                "diagnostics/pretrend_diagnostics.csv",
                "diagnostics/honest_did_event_coefficients.csv",
                "diagnostics/honest_did_event_vcov_long.csv",
            ),
            True,
        ),
        DagNode(
            "pretrend_national_variants",
            "Diagnose the 2022 sample, ladder steps, and wage coverage",
            _python("code/caged/models/pretrend_national_variants.py"),
            REESTIMATED,
            (
                "diagnostics/pretrend_sample_2022.csv",
                "diagnostics/pretrend_power_check.csv",
                "diagnostics/pretrend_ladder_variants.csv",
                "diagnostics/pretrend_wage_balanced_coverage.csv",
                "diagnostics/pretrend_national_variants_coefficients.csv",
            ),
            True,
        ),
        DagNode(
            "pretrend_sector_level2",
            "Diagnose the co-principal level-2 sector design",
            _python("code/caged/models/pretrend_sector.py"),
            REESTIMATED,
            (
                "diagnostics/pretrend_level2.csv",
                "diagnostics/pretrend_level2_coefficients.csv",
            ),
            True,
        ),
        DagNode(
            "pretrend_control_specification",
            "Estimate DiD specifications that control for the pre-trend",
            _python("code/caged/models/pretrend_control_spec.py"),
            REESTIMATED,
            (
                "models/pretrend_control_specification.csv",
                "models/PRETREND_CONTROL_SPECIFICATION.md",
            ),
            True,
        ),
        DagNode(
            "ddd_heterogeneity",
            "Rebuild and re-estimate the complete DDD family",
            _python("code/caged/models/heterogeneity.py"),
            REESTIMATED,
            (
                "diagnostics/ddd_multiplicity_results.csv",
                "diagnostics/ddd_family_support.csv",
            ),
            True,
        ),
        DagNode(
            "ddd_pretrend_diagnostics",
            "Restore DDD, per-group pretrend, and per-group power columns",
            _python("code/caged/models/ddd_pretrends.py"),
            REESTIMATED,
            (
                "diagnostics/ddd_pretrends.csv",
                "diagnostics/ddd_pretrends_coefficients.csv",
            ),
            True,
        ),
        DagNode(
            "placebo_falsifications",
            "Re-estimate temporal and 500-assignment group placebos",
            _python("code/caged/models/placebos.py"),
            REESTIMATED,
            (
                "diagnostics/temporal_placebo_results.csv",
                "diagnostics/group_placebo_distribution.csv",
                "diagnostics/group_placebo_summary.csv",
            ),
            True,
        ),
        DagNode(
            "separation_mechanisms",
            "Rebuild and re-estimate separation mechanism families",
            _python("code/caged/models/separation_mechanisms.py"),
            REESTIMATED,
            (
                "mechanisms/separation_static_results.csv",
                "mechanisms/separation_event_study.csv",
            ),
            True,
        ),
        DagNode(
            "cumulative_net_flow",
            "Rebuild and re-estimate the cumulative net-flow proxy",
            _python("code/caged/models/stock_proxy.py"),
            REESTIMATED,
            ("mechanisms/stock_proxy_result.csv",),
            True,
        ),
        DagNode(
            "hourly_wage_and_schedules",
            "Rebuild and re-estimate wage and schedule margins",
            _python("code/caged/models/hourly_wage.py"),
            REESTIMATED,
            ("mechanisms/hourly_wage_results.csv",),
            True,
        ),
        DagNode(
            "employer_size",
            "Rebuild and re-estimate employer-size heterogeneity",
            _python("code/caged/models/employer_size.py"),
            REESTIMATED,
            (
                "mechanisms/employer_size_ddd_results.csv",
                "mechanisms/employer_registration_support.csv",
            ),
            True,
        ),
        DagNode(
            "exposure_measure_sensitivity",
            "Re-estimate 2023, model-consensus, and Anthropic measures",
            _python("code/caged/models/exposure_sensitivity.py"),
            REESTIMATED,
            (
                "mechanisms/exposure_sensitivity_results.csv",
                "mechanisms/exposure_rank_correlations.csv",
            ),
            True,
        ),
        DagNode(
            "audit_occupation_concentration",
            "Re-estimate occupation influence and concentration diagnostics",
            _python("code/caged/audit/jackknife_occupations.py"),
            REESTIMATED,
            (
                "audit/b1_concentration.csv",
                "audit/b2_leave_one_out.csv",
                "audit/b3_drop_three_largest.csv",
                "audit/b4_unweighted_comparison.csv",
                "audit/b_jackknife_summary.json",
            ),
            True,
        ),
        DagNode(
            "audit_exposure_and_control",
            "Reconcile score coverage and pre-period control comparability",
            _python("code/caged/audit/exposure_and_control.py"),
            REESTIMATED,
            (
                "audit/c1_score_landscape.csv",
                "audit/c2_unscored_profile.csv",
                "audit/d1_pre_period_comparability.csv",
                "audit/cd_exposure_and_control_summary.json",
            ),
        ),
        DagNode(
            "audit_transfer_share",
            "Verify transfer codes and movement-type coverage",
            _python("code/caged/audit/transfer_share.py"),
            REESTIMATED,
            (
                "audit/e1_transfer_share_by_year.csv",
                "audit/e2_movement_type_distribution.csv",
                "audit/e_transfer_summary.json",
            ),
        ),
        DagNode(
            "gate_8a_pretrend_report",
            "Assemble every pretrend diagnostic into the Gate 8A report",
            _python("code/caged/models/pretrend_report.py"),
            RENDERED,
            (
                "diagnostics/DIAGNOSTICO_PRETRENDS.md",
                "diagnostics/pretrend_master_table.csv",
            ),
        ),
        DagNode(
            "ddd_alternative_partitions",
            "Build and estimate the 30-test alternative-partitions DDD family",
            _python(
                "code/caged/models/heterogeneity.py",
                "--family-id",
                "B",
            ),
            REESTIMATED,
            (
                "diagnostics/ddd_alternative_partitions.csv",
                "diagnostics/ddd_alternative_partitions_support.csv",
                "diagnostics/ddd_alternative_partitions_support.json",
                "diagnostics/DDD_ALTERNATIVE_PARTITIONS.md",
            ),
            True,
        ),
        DagNode(
            "ddd_alternative_partitions_pretrends",
            "Estimate all three diagnostics for DDD Family B",
            _python(
                "code/caged/models/ddd_pretrends.py",
                "--family-id",
                "B",
            ),
            REESTIMATED,
            (
                "diagnostics/ddd_alternative_partitions_pretrends.csv",
                (
                    "diagnostics/ddd_alternative_partitions_"
                    "pretrends_coefficients.csv"
                ),
                (
                    "diagnostics/"
                    "ddd_alternative_partitions_pretrends_support.json"
                ),
                "diagnostics/DDD_ALTERNATIVE_PARTITIONS_PRETRENDS.md",
            ),
            True,
        ),
        DagNode(
            "group_did_family_c",
            "Combine 100 frozen and 30 new group DiDs, then adjust all 130",
            _python("code/caged/models/group_did_results.py"),
            RENDERED,
            (
                "models/group_did_results.csv",
                "models/group_did_results_support.json",
                "models/GROUP_DID_RESULTS.md",
            ),
        ),
        DagNode(
            "audit_wage_composition",
            "Reconcile the admission-wage price and composition channels",
            _python("code/caged/audit/wage_composition.py"),
            REESTIMATED,
            (
                "audit/a1_education_composition_shift.csv",
                "audit/a2_wage_price_composition_split.csv",
                "audit/a3_wage_within_dimension_range.csv",
                "audit/a_wage_composition_summary.json",
            ),
        ),
        DagNode(
            "group_event_studies",
            "Estimate the 30 extended-window group event-study models",
            _python("code/caged/models/group_event_studies.py"),
            REESTIMATED,
            (
                "models/group_event_study_coefficients.csv",
                "models/group_event_study_pre_means.csv",
                "models/group_event_study_models.csv",
                "models/group_event_study_support.json",
                "models/GROUP_EVENT_STUDIES.md",
            ),
            True,
        ),
        DagNode(
            "canaries_wage_event_study",
            "Estimate the 22-25 cohort admission-wage event study",
            _python("code/caged/models/canaries_wage_event_study.py"),
            REESTIMATED,
            (
                "models/canaries_22_25_wage_event_study.csv",
                "models/canaries_22_25_wage_event_study_support.json",
            ),
            True,
        ),
        DagNode(
            "occupation_case_panel",
            "Build the descriptive six-case occupation-by-age panel",
            _python("code/caged/panel/occupation_cases.py"),
            DATA_REBUILT,
            (
                "mechanisms/occupation_case_monthly_coverage.csv",
                "mechanisms/OCCUPATION_CASE_MONTHLY_COVERAGE.md",
                "mechanisms/occupation_case_preperiod_diagnostics.csv",
                "mechanisms/OCCUPATION_CASE_PREPERIOD_DIAGNOSTICS.md",
                "mechanisms/occupation_case_wage_winsor_bounds.csv",
                "mechanisms/occupation_case_panel_support.json",
            ),
        ),
        DagNode(
            "occupation_case_trajectories",
            "Build normalized descriptive occupation-case trajectories",
            _python("code/caged/models/occupation_case_trajectories.py"),
            RENDERED,
            (
                "mechanisms/occupation_case_trajectories.csv",
                "mechanisms/occupation_case_terminal_summary.csv",
                "mechanisms/occupation_case_trajectories_support.json",
                "mechanisms/OCCUPATION_CASE_TRAJECTORIES.md",
            ),
        ),
        DagNode(
            "national_event_study_extended",
            "Estimate national event studies through event time +41",
            _python("code/caged/models/national_event_study_extended.py"),
            REESTIMATED,
            (
                "models/national_event_study_extended_coefficients.csv",
                "models/national_event_study_extended_pre_means.csv",
                "models/national_event_study_extended_models.csv",
                "models/national_event_study_extended_support.json",
                "models/NATIONAL_EVENT_STUDY_EXTENDED.md",
            ),
            True,
        ),
        DagNode(
            "export_complete_r_inputs",
            "Export coefficient-free analytical inputs and model contracts for R",
            _python(
                "code/replication/r_validation.py",
                "export",
                "--data-dir",
                str(PACKAGE_ROOT / "data"),
                "--input-dir",
                str(PACKAGE_ROOT / "data" / "derived" / "r_validation"),
            ),
            DATA_REBUILT,
        ),
        DagNode(
            "complete_r_replication",
            "Independently re-estimate every registered CAGED model in R",
            (
                "Rscript",
                str(PACKAGE_ROOT / "R" / "complete_replication.R"),
                "--contracts",
                str(
                    PACKAGE_ROOT
                    / "data"
                    / "derived"
                    / "r_validation"
                    / "model_contracts.csv"
                ),
                "--input-dir",
                str(PACKAGE_ROOT / "data" / "derived" / "r_validation"),
                "--output-dir",
                str(PACKAGE_ROOT / "results" / "replication" / "complete_r"),
            ),
            REESTIMATED,
            (
                "replication/complete_r/r_model_results.csv",
                "replication/complete_r/r_pretrend_diagnostics.csv",
                "replication/complete_r/r_failures.csv",
                "replication/complete_r/r_status.json",
                (
                    "replication/complete_r/"
                    "honest_did_event_coefficients.csv"
                ),
                (
                    "replication/complete_r/"
                    "honest_did_event_vcov_long.csv"
                ),
            ),
            True,
        ),
        DagNode(
            "compare_complete_r_replication",
            "Compare Python and R by stable model, term, and event-time identifiers",
            _python(
                "code/replication/r_validation.py",
                "compare",
                "--input-dir",
                str(PACKAGE_ROOT / "data" / "derived" / "r_validation"),
                "--results-dir",
                str(PACKAGE_ROOT / "results"),
                "--r-output-dir",
                str(PACKAGE_ROOT / "results" / "replication" / "complete_r"),
            ),
            FROZEN_VALIDATED,
            (
                "replication/complete_r/python_r_model_comparison.csv",
                "replication/complete_r/python_r_pretrend_comparison.csv",
                (
                    "replication/complete_r/"
                    "python_r_honest_did_coefficient_comparison.csv"
                ),
                (
                    "replication/complete_r/"
                    "python_r_honest_did_vcov_comparison.csv"
                ),
                "replication/complete_r/comparison_status.json",
            ),
            False,
        ),
        DagNode(
            "honest_did",
            "Estimate Rambachan-Roth sensitivity from independent R inputs",
            (
                "Rscript",
                str(PACKAGE_ROOT / "R" / "honest_did.R"),
                "--input-dir",
                str(
                    PACKAGE_ROOT
                    / "results"
                    / "replication"
                    / "complete_r"
                ),
            ),
            REESTIMATED,
            (
                "diagnostics/honest_did_sensitivity.csv",
                "diagnostics/honest_did_summary.csv",
                "diagnostics/honest_did_asinh_saldo.png",
                "diagnostics/honest_did_ln_salario_real_adm.png",
            ),
            True,
        ),
        DagNode(
            "honest_did_smoothness",
            "Add the DeltaSD smoothness restriction beside DeltaRM",
            (
                "Rscript",
                str(PACKAGE_ROOT / "R" / "honest_did_sd.R"),
                "--input-dir",
                str(
                    PACKAGE_ROOT
                    / "results"
                    / "replication"
                    / "complete_r"
                ),
            ),
            REESTIMATED,
            (
                "diagnostics/honest_did_sensitivity.csv",
                "diagnostics/honest_did_summary.csv",
                "diagnostics/honest_did_delta_comparison_asinh_saldo.png",
                (
                    "diagnostics/"
                    "honest_did_delta_comparison_ln_salario_real_adm.png"
                ),
            ),
            True,
        ),
        DagNode(
            "canaries_wage_figure",
            "Render the 22-25 cohort admission-wage event-study figure",
            _python("code/render/canaries_wage_figure.py"),
            RENDERED,
            ("figures/figure_5_2_3_3_canaries_22_25_wage.png",),
        ),
        DagNode(
            "phase8b_rendering",
            "Render and audit the 33 CAGED dissertation artifacts",
            _python("code/render/phase8b_render.py"),
            RENDERED,
            _phase8b_render_outputs(),
        ),
    ]


def resolve_target(target: str | None, section: str | None) -> str:
    """Resolve the public target and the backwards-compatible section alias."""
    if target is not None and section is not None:
        raise ValueError("--target and --section cannot be combined")
    if target is not None:
        return target
    if section == "3":
        return "section3"
    if section == "4-5":
        return "all_except_section3"
    return "all"


def _selected_components(target: str) -> tuple[str, ...]:
    if target == "all":
        return COMPONENTS
    if target == "all_except_section3":
        return COMPONENTS[1:]
    if target in COMPONENTS:
        return (target,)
    raise ValueError(f"Unsupported target: {target}")


def _component_pipeline_node(
    component: str,
    *,
    mode: str,
    raw_dir: Path,
    data_dir: Path,
    output_dir: Path,
    billing_project: str | None,
    skip_figures: bool,
) -> DagNode:
    arguments: tuple[str, ...] = (
        "--mode",
        mode,
        "--data-dir",
        str(data_dir),
        "--raw-dir",
        str(raw_dir),
        "--output-dir",
        str(output_dir / component),
    )
    if billing_project:
        arguments = (*arguments, "--billing-project", billing_project)
    if skip_figures:
        arguments = (*arguments, "--skip-figures")
    return DagNode(
        node_id=f"{component}_reproduction",
        description=f"Reproduce the registered {component} evidence",
        command=_python(f"code/{component}/pipeline.py", *arguments),
        disposition=REESTIMATED,
        inferential=component in {"rais", "pnadc"},
        component=component,
    )


def build_dag(
    *,
    target: str | None = None,
    section: str | None = None,
    mode: str,
    raw_dir: Path,
    data_dir: Path = DEFAULT_DATA_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    billing_project: str | None = None,
    skip_figures: bool = False,
) -> list[DagNode]:
    if mode not in {"reproduce", "full"}:
        raise ValueError(f"Unsupported mode: {mode}")
    resolved_target = resolve_target(target, section)
    selected = _selected_components(resolved_target)
    nodes = [_reference_node()]
    for component in selected:
        if component == "caged":
            if mode == "full":
                nodes.extend(_construction_nodes(raw_dir, data_dir))
            else:
                nodes.append(_reproduce_caged_backing_node(data_dir))
            nodes.extend(_analysis_nodes(mode))
            continue
        nodes.append(
            _component_pipeline_node(
                component,
                mode=mode,
                raw_dir=raw_dir,
                data_dir=data_dir,
                output_dir=output_dir,
                billing_project=billing_project,
                skip_figures=skip_figures,
            )
        )
    validate_dag_nodes(
        {node.node_id for node in nodes},
        target=resolved_target,
        mode=mode,
    )
    validate_dag_dependencies(nodes)
    return nodes


def _required_reproduce_inputs(data_dir: Path = DEFAULT_DATA_DIR) -> tuple[Path, ...]:
    return (
        data_dir / "derived" / "painel_nacional.parquet",
        data_dir / "derived" / "painel_cbo_cnae.parquet",
        data_dir / "derived" / "treatment_variants.csv",
        data_dir
        / "derived"
        / "painel_heterogeneity_ddd.parquet",
        data_dir
        / "vintage"
        / "crosswalk"
        / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx",
        data_dir
        / "derived"
        / "external"
        / "anthropic_automation_augmentation_cbo.parquet",
        data_dir
        / "derived"
        / "occupation_cases"
        / "occupation_case_dictionary.csv",
        data_dir
        / "derived"
        / "occupation_cases"
        / "table_c_1_occupation_case_exposure_summary.csv",
    )


def validate_r_environment() -> dict[str, object]:
    """Require the active R runtime to match the complete renv lock exactly."""
    rscript = shutil.which("Rscript")
    if rscript is None:
        raise FileNotFoundError("Rscript executable")
    completed = subprocess.run(
        [
            rscript,
            str(PACKAGE_ROOT / "R" / "validate_environment.R"),
            str(PACKAGE_ROOT / "renv.lock"),
        ],
        cwd=PACKAGE_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"R environment does not match renv.lock: {detail}")
    try:
        status = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        raise RuntimeError("R environment validator returned invalid output") from error
    if status.get("status") != "pass":
        raise RuntimeError("R environment validator did not report pass")
    return status


def preflight(
    *,
    target: str,
    mode: str,
    raw_dir: Path,
    data_dir: Path,
    dag: Sequence[DagNode],
    billing_project: str | None,
) -> dict[str, object]:
    selected = _selected_components(target)
    if mode == "full" and "pnadc" in selected and not billing_project:
        raise ValueError(
            "Full PNADc reconstruction requires --billing-project"
        )
    reference = validate_reference(
        REFERENCE_DIR
    )
    bundle = None
    raw_cache = None
    if mode == "reproduce":
        bundle = validate_analytical_bundle(
            data_dir,
            PACKAGE_ROOT / "config" / "analytical_bundle_manifest.csv",
        )
    else:
        raw_cache = validate_raw_cache(raw_dir)
    missing_scripts = [
        item
        for node in dag
        for item in node.command[1:2]
        if item.endswith((".py", ".R")) and not Path(item).is_file()
    ]
    if missing_scripts:
        raise FileNotFoundError(
            "DAG scripts are missing: " + ", ".join(missing_scripts)
        )
    missing_inputs: list[str] = []
    if "caged" in selected and mode == "reproduce":
        missing_inputs = [
            str(path)
            for path in _required_reproduce_inputs(data_dir)
            if not path.is_file()
        ]
        partitions = len(
            list(
                (data_dir / "interim" / "movimentacoes").glob(
                    "competenciamov=*/part.parquet"
                )
            )
        )
        if partitions != 77:
            missing_inputs.append(
                f"expected 77 signed movement partitions, found {partitions}"
            )
    else:
        partitions = 77
    if "caged" in selected and mode == "full":
        archives = len(list(raw_dir.glob("CAGED*.7z")))
        inventory = raw_dir / "ftp_inventory.csv"
        if not inventory.is_file():
            missing_inputs.append(str(inventory))
        else:
            with inventory.open(encoding="utf-8", newline="") as handle:
                inventory_rows = len(list(csv.DictReader(handle)))
            if inventory_rows != 195:
                missing_inputs.append(
                    "expected 195 frozen inventory rows, found "
                    f"{inventory_rows} in {inventory}"
                )
    else:
        archives = 195
    r_environment: dict[str, object] | None = None
    if shutil.which("Rscript") is None:
        missing_inputs.append("Rscript executable")
    if missing_inputs:
        raise FileNotFoundError(
            "Preflight inputs are missing:\n- "
            + "\n- ".join(missing_inputs)
        )
    r_environment = validate_r_environment()
    return {
        "archives": archives,
        "dag_nodes": len(dag),
        "movement_partitions": partitions,
        "reference_artifacts": reference["artifacts"],
        "reference_signature_valid": reference[
            "manifest_signature_valid"
        ],
        "analytical_bundle_files": (
            int(bundle["files"]) if bundle is not None else "rebuilt_in_full_mode"
        ),
        "analytical_bundle_sha256": (
            str(bundle["manifest_sha256"])
            if bundle is not None
            else "rebuilt_in_full_mode"
        ),
        "r_environment": r_environment,
        "raw_cache": raw_cache,
    }


def _print_dag(dag: Sequence[DagNode], skip_figures: bool) -> None:
    print("DAG:")
    for index, node in enumerate(dag, start=1):
        print(
            f"{index:02d}. [{node.disposition}] {node.node_id}: "
            f"{node.description}"
        )
        print("    COMMAND: " + " ".join(node.command))
        for output in node.outputs:
            if skip_figures and output.endswith(".png"):
                continue
            print(f"    [{RENDERED}] results/{output}")


def _execution_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for variable in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMBA_NUM_THREADS",
    ):
        environment[variable] = "1"
    environment.setdefault("PYTHONUNBUFFERED", "1")
    return environment


def _clone_or_copy(source: str, destination: str) -> str:
    """Use an APFS clone when available and a portable copy otherwise."""
    clone = subprocess.run(
        ["/bin/cp", "-c", source, destination],
        check=False,
        capture_output=True,
    )
    if clone.returncode != 0:
        shutil.copy2(source, destination)
    return destination


def _copy_tree(
    source: Path,
    destination: Path,
    *,
    include_raw_archives: bool = True,
    merge: bool = False,
) -> None:
    ignored = [".DS_Store", ".pytest_cache", "__pycache__", "*.pyc"]
    if not include_raw_archives:
        ignored.append("*.7z")
    shutil.copytree(
        source,
        destination,
        copy_function=_clone_or_copy,
        ignore=shutil.ignore_patterns(*ignored),
        dirs_exist_ok=merge,
    )


def materialize_execution_root(
    *,
    work_dir: Path,
    data_dir: Path,
    reference_dir: Path,
    raw_dir: Path | None = None,
    include_raw_archives: bool = True,
) -> Path:
    """Create a copy-on-write package root for an isolated CAGED run."""
    runtime = work_dir.resolve()
    if runtime.exists():
        raise FileExistsError(runtime)
    runtime.mkdir(parents=True)
    _copy_tree(PACKAGE_ROOT / "code", runtime / "code")
    _copy_tree(
        data_dir.resolve(),
        runtime / "data",
        include_raw_archives=include_raw_archives,
    )
    if raw_dir is not None:
        resolved_raw = raw_dir.resolve()
        bundled_raw = data_dir.resolve() / "vintage"
        if resolved_raw != bundled_raw:
            if not resolved_raw.is_dir():
                raise FileNotFoundError(resolved_raw)
            _copy_tree(
                resolved_raw,
                runtime / "data" / "vintage",
                include_raw_archives=include_raw_archives,
                merge=True,
            )
    if (PACKAGE_ROOT / "R").is_dir():
        _copy_tree(PACKAGE_ROOT / "R", runtime / "R")
    if (PACKAGE_ROOT / "config").is_dir():
        _copy_tree(PACKAGE_ROOT / "config", runtime / "config")
    (runtime / "results").mkdir()
    _copy_tree(reference_dir.resolve(), runtime / "results" / "reference")
    return runtime


def prepare_full_rebuild_runtime(runtime_root: Path) -> tuple[str, ...]:
    """Remove only rebuildable CAGED inputs from the isolated runtime copy."""

    runtime = runtime_root.resolve()
    targets = (
        runtime / "data" / "interim" / "movimentacoes",
        runtime / "data" / "interim" / "movimentacoes.building",
        runtime / "data" / "derived" / "cbo_treatment_classification.csv",
        runtime / "data" / "derived" / "treatment_variants.csv",
        runtime / "data" / "derived" / "ipca_mensal.parquet",
        runtime / "data" / "derived" / "painel_nacional.parquet",
        runtime / "data" / "derived" / "painel_cbo_cnae.parquet",
        runtime / "data" / "derived" / "painel_cbo_divisao.parquet",
        runtime / "data" / "vintage" / "cnae" / "cnae_divisions.csv",
    )
    removed: list[str] = []
    for target in targets:
        target.resolve().relative_to(runtime)
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        elif target.exists() or target.is_symlink():
            target.unlink()
        else:
            continue
        removed.append(target.relative_to(runtime).as_posix())
    return tuple(removed)


def remap_command_to_runtime(
    command: Sequence[str],
    runtime_root: Path,
    *,
    data_dir: Path | None = None,
    raw_dir: Path | None = None,
) -> tuple[str, ...]:
    """Map package and analytical-bundle paths into the execution root."""
    package_root = PACKAGE_ROOT.resolve()
    resolved_data = data_dir.resolve() if data_dir is not None else None
    resolved_raw = raw_dir.resolve() if raw_dir is not None else None
    remapped: list[str] = []
    for item in command:
        candidate = Path(item)
        if not candidate.is_absolute():
            remapped.append(item)
            continue
        resolved = candidate.resolve()
        if resolved_raw is not None:
            try:
                relative_raw = resolved.relative_to(resolved_raw)
            except ValueError:
                pass
            else:
                remapped.append(
                    str(runtime_root / "data" / "vintage" / relative_raw)
                )
                continue
        try:
            relative = resolved.relative_to(package_root)
        except ValueError:
            if resolved_data is None:
                remapped.append(item)
                continue
            try:
                relative_data = resolved.relative_to(resolved_data)
            except ValueError:
                remapped.append(item)
            else:
                remapped.append(str(runtime_root / "data" / relative_data))
        else:
            remapped.append(str(runtime_root / relative))
    return tuple(remapped)


def run_dag(
    dag: Sequence[DagNode],
    *,
    skip_figures: bool,
    runtime_root: Path | None = None,
    data_dir: Path | None = None,
    raw_dir: Path | None = None,
) -> None:
    for index, node in enumerate(dag, start=1):
        environment = _execution_environment()
        print(
            f"[{node.disposition}] START {index}/{len(dag)} "
            f"{node.node_id}",
            flush=True,
        )
        if node.component == "caged" and runtime_root is not None:
            command = remap_command_to_runtime(
                node.command,
                runtime_root,
                data_dir=data_dir,
                raw_dir=raw_dir,
            )
            working_directory = runtime_root
            environment.update(
                ReplicationPaths(
                    package=runtime_root,
                    data=runtime_root / "data",
                    raw=runtime_root / "data" / "vintage",
                    reference=runtime_root / "results" / "reference",
                    reproduced=runtime_root / "results",
                    work=runtime_root / ".replication-work",
                ).environment()
            )
        else:
            command = node.command
            working_directory = PACKAGE_ROOT
        completed = subprocess.run(
            command,
            cwd=working_directory,
            env=environment,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"DAG node failed ({completed.returncode}): "
                f"{node.node_id}"
            )
        print(
            f"[{node.disposition}] DONE {node.node_id}",
            flush=True,
        )
        for output in node.outputs:
            if skip_figures and output.endswith(".png"):
                continue
            result_root = (
                runtime_root / "results"
                if node.component == "caged" and runtime_root is not None
                else LEGACY_RESULTS_DIR
                if node.component == "caged"
                else DEFAULT_OUTPUT_DIR / node.component
            )
            path = result_root / output
            if not path.is_file():
                raise FileNotFoundError(
                    f"Declared node output is missing: {path}"
                )
            print(f"[{RENDERED}] {path}", flush=True)


def render_output_bundle(
    output_dir: Path,
    *,
    skip_figures: bool,
) -> int:
    if output_dir.resolve() == LEGACY_RESULTS_DIR.resolve():
        return len(
            [
                path
                for path in LEGACY_RESULTS_DIR.rglob("*")
                if path.is_file()
                and "reference" not in path.relative_to(LEGACY_RESULTS_DIR).parts
                and not (skip_figures and path.suffix == ".png")
            ]
        )
    copied = 0
    for source in sorted(LEGACY_RESULTS_DIR.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(LEGACY_RESULTS_DIR)
        if "reference" in relative.parts:
            continue
        if skip_figures and source.suffix == ".png":
            continue
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(
            f"{destination.suffix}.tmp"
        )
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
        copied += 1
        print(f"[{RENDERED}] {destination}")
    return copied


def copy_runtime_results(
    runtime_root: Path,
    output_dir: Path,
    *,
    skip_figures: bool,
) -> int:
    """Promote isolated CAGED results without copying the signed reference."""
    source_root = runtime_root / "results"
    copied = 0
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        if "reference" in relative.parts:
            continue
        if source.suffix.lower() == ".md" and relative.parts[0] != "tables":
            continue
        if skip_figures and source.suffix.lower() == ".png":
            continue
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(f"{destination.suffix}.tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
        copied += 1
    return copied


def reconcile_numeric_claims(
    output_dir: Path,
    *,
    components: Sequence[str],
) -> None:
    """Fail the run when a registered manuscript number does not reconcile."""
    destination = (
        output_dir / "validation" / "numeric_claims_reconciliation.csv"
    )
    command = [
        *_python("code/replication/claims.py"),
        "--output-root",
        str(output_dir),
        "--output",
        str(destination),
    ]
    for component in components:
        command.extend(("--component", component))
    completed = subprocess.run(
        command,
        cwd=PACKAGE_ROOT,
        env=_execution_environment(),
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Numeric manuscript claims did not reconcile")


def _paths_overlap(left: Path, right: Path) -> bool:
    """Return whether either resolved path contains the other."""
    return (
        left == right
        or left.is_relative_to(right)
        or right.is_relative_to(left)
    )


def validate_output_dir(
    output_dir: Path,
    *,
    data_dir: Path | None = None,
    raw_dir: Path | None = None,
) -> Path:
    """Reject destinations that can mutate code, inputs, or signed references."""
    destination = output_dir.expanduser().resolve()
    package_root = PACKAGE_ROOT.resolve()
    immutable_descendant_roots = (
        (PACKAGE_ROOT / "code").resolve(),
        (PACKAGE_ROOT / "data").resolve(),
        REFERENCE_DIR.resolve(),
    )
    if destination == package_root or package_root.is_relative_to(destination):
        raise ValueError(
            f"Output destination is an immutable package path: {package_root}"
        )
    for root in immutable_descendant_roots:
        if destination == root or destination.is_relative_to(root):
            raise ValueError(f"Output destination is an immutable package path: {root}")

    external_inputs = (
        ("analytical data directory", data_dir),
        ("raw-source directory", raw_dir),
    )
    for label, path in external_inputs:
        if path is None:
            continue
        root = path.expanduser().resolve()
        if _paths_overlap(destination, root):
            raise ValueError(
                f"Output destination overlaps the external {label}: {root}"
            )
    return destination


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_output_manifest(output_dir: Path) -> bool:
    manifest_path = output_dir / "run_manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return False
    if payload.get("format_version") != 1:
        return False
    if payload.get("package_id") != "dissertation-replication-v2":
        return False
    records = payload.get("artifacts")
    if not isinstance(records, list):
        return False
    declared: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            return False
        relative = Path(str(record.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            return False
        path = output_dir / relative
        if not path.is_file():
            return False
        if path.stat().st_size != record.get("bytes"):
            return False
        if _sha256_file(path) != record.get("sha256"):
            return False
        declared.add(relative.as_posix())
    actual = {
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file() and path != manifest_path
    }
    return actual == declared


def prepare_output_directory(output_dir: Path) -> Path:
    """Create a destination or replace only a verified prior package run."""
    destination = validate_output_dir(output_dir)
    if destination.exists() and any(destination.iterdir()):
        if not _valid_output_manifest(destination):
            raise ValueError(
                "Refusing to replace a non-empty directory without a valid "
                f"package run manifest: {destination}"
            )
        for child in destination.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def write_run_manifest(
    output_dir: Path,
    *,
    target: str,
    mode: str,
    components: Sequence[str],
    status: str = "complete",
) -> Path:
    artifacts = [
        {
            "bytes": path.stat().st_size,
            "path": path.relative_to(output_dir).as_posix(),
            "sha256": _sha256_file(path),
        }
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path != output_dir / "run_manifest.json"
    ]
    payload = {
        "artifacts": artifacts,
        "components": list(components),
        "format_version": 1,
        "mode": mode,
        "package_id": "dissertation-replication-v2",
        "status": status,
        "target": target,
    }
    destination = output_dir / "run_manifest.json"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, destination)
    return destination


def count_output_artifacts(output_dir: Path, *, skip_figures: bool) -> int:
    return len(
        [
            path
            for path in output_dir.rglob("*")
            if path.is_file()
            and path.name != "run_manifest.json"
            and not (skip_figures and path.suffix.lower() == ".png")
        ]
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-estimate the V2 dissertation replication package."
    )
    parser.add_argument("--target", choices=("all", *COMPONENTS))
    parser.add_argument("--section", choices=("all", "3", "4-5"))
    parser.add_argument(
        "--mode",
        choices=("reproduce", "full"),
        default="reproduce",
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument("--billing-project")
    parser.add_argument("--skip-figures", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    raw_dir = args.raw_dir.resolve()
    data_dir = args.data_dir.resolve()
    output_dir = validate_output_dir(
        args.output_dir,
        data_dir=data_dir,
        raw_dir=raw_dir,
    )
    target = resolve_target(args.target, args.section)
    dag = build_dag(
        target=target,
        mode=args.mode,
        raw_dir=raw_dir,
        data_dir=data_dir,
        output_dir=output_dir,
        billing_project=args.billing_project,
        skip_figures=args.skip_figures,
    )
    summary = preflight(
        target=target,
        mode=args.mode,
        raw_dir=raw_dir,
        data_dir=data_dir,
        dag=dag,
        billing_project=args.billing_project,
    )
    print("PREFLIGHT: PASS " + json.dumps(summary, sort_keys=True))
    _print_dag(dag, args.skip_figures)
    if args.dry_run:
        print("DRY RUN: no estimation or rendering executed")
        return 0
    prepare_output_directory(output_dir)
    selected_components = _selected_components(target)
    try:
        if "caged" in selected_components:
            with tempfile.TemporaryDirectory(
                prefix="replication-v2-runtime-",
                dir=output_dir.parent,
            ) as temporary_directory:
                runtime_root = materialize_execution_root(
                    work_dir=Path(temporary_directory) / "package",
                    data_dir=data_dir,
                    reference_dir=REFERENCE_DIR,
                    raw_dir=raw_dir if args.mode == "full" else None,
                    include_raw_archives=args.mode == "full",
                )
                if args.mode == "full":
                    removed = prepare_full_rebuild_runtime(runtime_root)
                    print(
                        "FULL REBUILD: cleared isolated derived inputs "
                        + json.dumps(list(removed)),
                        flush=True,
                    )
                run_dag(
                    dag,
                    skip_figures=args.skip_figures,
                    runtime_root=runtime_root,
                    data_dir=data_dir,
                    raw_dir=raw_dir,
                )
                copy_runtime_results(
                    runtime_root,
                    output_dir / "caged",
                    skip_figures=args.skip_figures,
                )
        else:
            run_dag(dag, skip_figures=args.skip_figures)
    except BaseException:
        write_run_manifest(
            output_dir,
            target=target,
            mode=args.mode,
            components=selected_components,
            status="failed",
        )
        raise
    for component in selected_components:
        validate_publications(
            output_dir / component,
            component=component,
            skip_figures=args.skip_figures,
        )
    reconcile_numeric_claims(
        output_dir,
        components=selected_components,
    )
    componentized_reference = all(
        (REFERENCE_DIR / "artifacts" / component).is_dir()
        for component in selected_components
    )
    if componentized_reference:
        compare_reproduced_components(
            output_root=output_dir,
            reference_dir=REFERENCE_DIR,
            components=selected_components,
            skip_figures=args.skip_figures,
            report_path=output_dir / "validation" / "reference_comparison.csv",
        )
    else:
        print(
            "REFERENCE COMPARISON: DEFERRED until the one-time legacy "
            "reference migration is frozen"
        )
    rendered = count_output_artifacts(
        output_dir,
        skip_figures=args.skip_figures,
    )
    write_run_manifest(
        output_dir,
        target=target,
        mode=args.mode,
        components=selected_components,
        status="complete",
    )
    print(
        "REPLICATION: COMPLETE "
        + json.dumps(
            {
                "artifacts_rendered": rendered,
                "mode": args.mode,
                "output_dir": str(output_dir),
                "target": target,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
