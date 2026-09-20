#!/usr/bin/env python3
"""Run the pre-registered annual RAIS pretrend diagnostics.

The annual event-time reference is base year 2022 (event time 0). This module
reuses the frozen V2 diagnostic and inference functions while keeping the
monthly event-study module untouched. It publishes lead diagnostics only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd


FRONT_ROOT = Path(__file__).resolve().parent.parent
V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
MODELS_DIR = V2_ROOT / "code" / "caged" / "models"
if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

from estimators import cluster_t_inference  # noqa: E402
from pretrend_engine import (  # noqa: E402
    atomic_csv,
    atomic_json,
    atomic_text,
    event_parameter_frame,
    joint_lead_test,
)
from pretrends import classify_pretrend, gls_pretrend_slope  # noqa: E402
from .stage0 import sha256_file  # noqa: E402


ANNUAL_REFERENCE_EVENT_TIME = 0
SHARED_GLS_REFERENCE_EVENT_TIME = -1
REFERENCE_YEAR = 2022
INTERACTION = "treated_main"
FIXED_EFFECTS = ("cbo_4d", "ano")
CLUSTER_VARIABLE = "cbo_4d"

ANNUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_rais_anual.parquet"
ROTATION_PANEL_PATH = (
    FRONT_ROOT / "data" / "painel_rais_rotatividade.parquet"
)
PART1_STATUS_PATH = FRONT_ROOT / "results" / "rais_part1_status.json"
MONTHLY_PRETRENDS_PATH = (
    V2_ROOT / "results" / "diagnostics" / "pretrend_diagnostics.csv"
)
PRETRENDS_PATH = FRONT_ROOT / "results" / "rais_pretrends.csv"
PRETRENDS_SUPPORT_PATH = (
    FRONT_ROOT / "results" / "rais_pretrends_support.json"
)
PRETRENDS_REPORT_PATH = FRONT_ROOT / "results" / "RAIS_PRETRENDS.md"
R8_STATUS_PATH = FRONT_ROOT / "results" / "rais_r8_status.json"

FUTURE_RESULT_PATHS = (
    FRONT_ROOT / "results" / "rais_static_results.csv",
    FRONT_ROOT / "results" / "rais_sensitivities.csv",
)

OUTCOME_SPECS = (
    {
        "outcome": "estoque_3112",
        "estimator": "ppml",
        "panel": "annual",
        "start_year": 2019,
        "end_year": 2024,
    },
    {
        "outcome": "ln_taxa_rotatividade",
        "estimator": "ols",
        "panel": "rotation",
        "start_year": 2021,
        "end_year": 2024,
    },
    {
        "outcome": "ln_tempo_emprego_medio",
        "estimator": "ols",
        "panel": "annual",
        "start_year": 2019,
        "end_year": 2024,
    },
)

DIAGNOSTIC_COLUMNS = (
    "specification_id",
    "outcome",
    "estimator",
    "sample_window",
    "event_window",
    "reference_year",
    "reference_event_time",
    "lead_event_times",
    "formula",
    "fixed_effects",
    "cluster_variables",
    "n_obs",
    "input_cells",
    "complete_case_input",
    "cells_dropped_missing",
    "cells_dropped_estimator",
    "minimum_clusters",
    "cluster_counts",
    "joint_lead_test_name",
    "joint_lead_window",
    "joint_lead_count",
    "joint_lead_statistic",
    "joint_lead_df",
    "joint_lead_p_value",
    "lead_covariance_min_eigenvalue",
    "lead_covariance_positive_semidefinite",
    "linear_pretrend_test_name",
    "linear_pretrend_coefficient",
    "linear_pretrend_standard_error",
    "linear_pretrend_p_value",
    "dynamic_diagnostic_name",
    "dynamic_pre_coefficients",
    "dynamic_pre_p_lt_005",
    "dynamic_min_p_value",
    "pretrend_classification_name",
    "pretrend_status",
    "section_5_1_reading",
    "non_rejection_is_proof",
    "post_event_coefficients_published",
)


def _required_columns(
    frame: pd.DataFrame,
    required: set[str],
    *,
    source_name: str,
) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_name} is missing columns: {missing}")


def expected_event_times(start_year: int, end_year: int) -> list[int]:
    """Return the estimated annual event-time grid, omitting 2022."""
    return [
        event_time
        for event_time in range(
            start_year - REFERENCE_YEAR,
            end_year - REFERENCE_YEAR + 1,
        )
        if event_time != ANNUAL_REFERENCE_EVENT_TIME
    ]


def build_annual_formula(outcome: str) -> str:
    fixed = " + ".join(FIXED_EFFECTS)
    return (
        f"{outcome} ~ i(event_time, {INTERACTION}, "
        f"ref={ANNUAL_REFERENCE_EVENT_TIME}) | {fixed}"
    )


def prepare_annual_event_data(
    panel: pd.DataFrame,
    *,
    outcome: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Create the complete-case annual grid for one outcome."""
    required = {"cbo_4d", "ano", "treated_main", outcome}
    _required_columns(panel, required, source_name=f"RAIS panel for {outcome}")
    source = panel.loc[
        panel["ano"].between(start_year, end_year)
    ].copy()
    source["event_time"] = (
        pd.to_numeric(source["ano"], errors="raise").astype(int)
        - REFERENCE_YEAR
    )
    data = source.dropna(subset=list(required) + ["event_time"]).copy()
    observed_years = sorted(data["ano"].astype(int).unique().tolist())
    expected_years = list(range(start_year, end_year + 1))
    if observed_years != expected_years:
        missing = sorted(set(expected_years) - set(observed_years))
        raise RuntimeError(
            f"Annual event grid has missing years for {outcome}: {missing}"
        )
    invalid_treatment = ~data["treated_main"].isin([0.0, 1.0])
    if invalid_treatment.any():
        raise RuntimeError(f"Invalid treatment values for {outcome}")
    return data.sort_values(["cbo_4d", "ano"]).reset_index(drop=True)


def annual_gls_pretrend_slope(
    coefficients: np.ndarray,
    covariance: np.ndarray,
    annual_event_times: np.ndarray,
    cluster_counts: dict[str, int],
) -> dict[str, float | int]:
    """Call the frozen GLS slope after recentering its monthly coordinate."""
    recentered_event_times = (
        np.asarray(annual_event_times, dtype=float) - 1.0
    )
    result = gls_pretrend_slope(
        coefficients,
        covariance,
        recentered_event_times,
        cluster_counts,
    )
    return {
        **result,
        "annual_reference_event_time": ANNUAL_REFERENCE_EVENT_TIME,
        "shared_function_reference_event_time": (
            SHARED_GLS_REFERENCE_EVENT_TIME
        ),
        "coordinate_shift": -1,
    }


def covariance_psd_diagnostic(
    covariance: np.ndarray,
) -> dict[str, float | bool]:
    """Preserve the shared diagnostic engine's PSD tolerance."""
    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Lead covariance matrix must be square")
    if not matrix.size:
        raise ValueError("Lead covariance matrix must not be empty")
    symmetric = 0.5 * (matrix + matrix.T)
    minimum_eigenvalue = float(np.linalg.eigvalsh(symmetric).min())
    scale = float(np.abs(np.diag(symmetric)).max())
    tolerance = -1e-8 * max(scale, 1.0)
    return {
        "lead_covariance_min_eigenvalue": minimum_eigenvalue,
        "lead_covariance_positive_semidefinite": bool(
            minimum_eigenvalue >= tolerance
        ),
    }


def diagnose_annual_model(
    model: Any,
    *,
    expected_times: Sequence[int],
    lead_times: Sequence[int],
    cluster_counts: dict[str, int],
) -> dict[str, Any]:
    """Run the three frozen diagnostics on an annual event-study model."""
    parameters = event_parameter_frame(
        model,
        INTERACTION,
        expected_event_times=expected_times,
    )
    leads = parameters.loc[
        parameters["event_time"].isin(lead_times)
    ].copy()
    if leads["event_time"].astype(int).tolist() != list(lead_times):
        raise RuntimeError("Annual lead parameter grid is incomplete")
    covariance = np.asarray(model._vcov, dtype=float)
    lead_positions = leads["position"].astype(int).to_numpy()
    lead_covariance = covariance[np.ix_(lead_positions, lead_positions)]
    psd = covariance_psd_diagnostic(lead_covariance)
    joint = joint_lead_test(model, lead_positions)
    linear = annual_gls_pretrend_slope(
        leads["coefficient"].to_numpy(),
        lead_covariance,
        leads["event_time"].to_numpy(),
        cluster_counts,
    )
    individual_p_values = [
        float(
            cluster_t_inference(
                float(record.coefficient),
                float(record.standard_error),
                cluster_counts,
            )["p_value"]
        )
        for record in leads.itertuples()
    ]
    n_individual = int(
        sum(p_value < 0.05 for p_value in individual_p_values)
    )
    return {
        "joint_lead_test_name": "cluster_robust_joint_wald_all_leads",
        "joint_lead_count": int(len(leads)),
        "joint_lead_statistic": joint["statistic"],
        "joint_lead_df": joint["df"],
        "joint_lead_p_value": joint["p_value"],
        **psd,
        "linear_pretrend_test_name": (
            "gls_linear_slope_through_annual_reference"
        ),
        "linear_pretrend_coefficient": linear["coefficient"],
        "linear_pretrend_standard_error": linear["standard_error"],
        "linear_pretrend_p_value": linear["p_value"],
        "dynamic_diagnostic_name": (
            "individual_cluster_t_lead_inspection"
        ),
        "dynamic_pre_coefficients": int(len(leads)),
        "dynamic_pre_p_lt_005": n_individual,
        "dynamic_min_p_value": float(min(individual_p_values)),
        "pretrend_classification_name": (
            "preregistered_pass_warning_fail"
        ),
        "pretrend_status": classify_pretrend(
            float(joint["p_value"]),
            float(linear["p_value"]),
            n_individual,
        ),
        "non_rejection_is_proof": False,
        "reference_event_time": ANNUAL_REFERENCE_EVENT_TIME,
    }


def pretrend_comparison_reading(status: str) -> str:
    mapping = {
        "pass": "seasonality_attenuation_compatible_not_proven",
        "warning": "annual_diagnostic_inconclusive",
        "fail": "structural_difference_persists_after_aggregation",
    }
    try:
        return mapping[status]
    except KeyError as error:
        raise ValueError(f"Unsupported pretrend status: {status}") from error


def _fit_annual_event_model(
    panel: pd.DataFrame,
    *,
    outcome: str,
    estimator: str,
    start_year: int,
    end_year: int,
) -> tuple[Any, pd.DataFrame, str, dict[str, int]]:
    data = prepare_annual_event_data(
        panel,
        outcome=outcome,
        start_year=start_year,
        end_year=end_year,
    )
    formula = build_annual_formula(outcome)
    import pyfixest as pf

    vcov = {"CRV1": CLUSTER_VARIABLE}
    if estimator == "ppml":
        if (data[outcome] < 0).any():
            raise ValueError("PPML outcome must be weakly positive")
        model = pf.fepois(
            formula,
            data=data,
            vcov=vcov,
            separation_check=["fe", "ir"],
        )
        if not bool(getattr(model, "_convergence", False)):
            raise RuntimeError(f"Annual PPML did not converge: {outcome}")
    elif estimator == "ols":
        model = pf.feols(formula, data=data, vcov=vcov)
    else:
        raise ValueError(f"Unsupported estimator: {estimator}")
    used = getattr(model, "_data", data)
    cluster_counts = {
        CLUSTER_VARIABLE: int(used[CLUSTER_VARIABLE].nunique())
    }
    return model, data, formula, cluster_counts


def _event_window_label(start_year: int, end_year: int) -> str:
    return (
        f"{start_year - REFERENCE_YEAR}_to_"
        f"{end_year - REFERENCE_YEAR}"
    )


def _lead_window_label(lead_times: Sequence[int]) -> str:
    return f"{min(lead_times)}_to_{max(lead_times)}"


def _run_outcome(
    panel: pd.DataFrame,
    spec: dict[str, Any],
) -> dict[str, Any]:
    outcome = str(spec["outcome"])
    estimator = str(spec["estimator"])
    start_year = int(spec["start_year"])
    end_year = int(spec["end_year"])
    model, model_data, formula, cluster_counts = _fit_annual_event_model(
        panel,
        outcome=outcome,
        estimator=estimator,
        start_year=start_year,
        end_year=end_year,
    )
    expected_times = expected_event_times(start_year, end_year)
    lead_times = [
        event_time for event_time in expected_times if event_time < 0
    ]
    diagnostics = diagnose_annual_model(
        model,
        expected_times=expected_times,
        lead_times=lead_times,
        cluster_counts=cluster_counts,
    )
    input_cells = int(
        panel.loc[panel["ano"].between(start_year, end_year)].shape[0]
    )
    row = {
        "specification_id": "annual_dynamic_exact_model",
        "outcome": outcome,
        "estimator": estimator,
        "sample_window": f"{start_year}-{end_year}",
        "event_window": _event_window_label(start_year, end_year),
        "reference_year": REFERENCE_YEAR,
        "reference_event_time": ANNUAL_REFERENCE_EVENT_TIME,
        "lead_event_times": json.dumps(lead_times),
        "formula": formula,
        "fixed_effects": " + ".join(FIXED_EFFECTS),
        "cluster_variables": CLUSTER_VARIABLE,
        "n_obs": int(model._N),
        "input_cells": input_cells,
        "complete_case_input": int(len(model_data)),
        "cells_dropped_missing": int(input_cells - len(model_data)),
        "cells_dropped_estimator": int(len(model_data) - int(model._N)),
        "minimum_clusters": int(min(cluster_counts.values())),
        "cluster_counts": json.dumps(cluster_counts, sort_keys=True),
        "joint_lead_window": _lead_window_label(lead_times),
        **diagnostics,
        "section_5_1_reading": pretrend_comparison_reading(
            str(diagnostics["pretrend_status"])
        ),
        "post_event_coefficients_published": False,
    }
    return row


def _format_p_value(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def render_pretrend_report(
    diagnostics: pd.DataFrame,
    monthly: pd.DataFrame,
) -> str:
    """Render the required annual-versus-monthly diagnostic comparison."""
    monthly_fail = int(monthly["pretrend_status"].eq("fail").sum())
    monthly_total = int(len(monthly))
    lines = [
        "# RAIS annual pretrend diagnostics",
        "",
        "## Annual diagnostics",
        "",
        "Annual event time is `year - 2022`; 2022 (event time 0) is the "
        "omitted reference. Models use CBO4 and year fixed effects and "
        "cluster by CBO4.",
        "",
        "| Outcome | Window | Leads | Joint p | Linear p | Individual leads "
        "p<0.05 | Lead covariance PSD | Classification |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for row in diagnostics.itertuples(index=False):
        lines.append(
            f"| `{row.outcome}` | {row.sample_window} | "
            f"{row.joint_lead_window} | "
            f"{_format_p_value(float(row.joint_lead_p_value))} | "
            f"{_format_p_value(float(row.linear_pretrend_p_value))} | "
            f"{row.dynamic_pre_p_lt_005} | "
            f"`{str(row.lead_covariance_positive_semidefinite).lower()}` | "
            f"`{row.pretrend_status}` |"
        )
    lines.extend(
        [
            "",
            "## Comparison with monthly CAGED",
            "",
            f"{monthly_fail} of {monthly_total} monthly CAGED diagnostics "
            "are `fail`. Those monthly diagnostics cover admissions, "
            "separations, gross movements, admission wages, and net balance; "
            "the RAIS diagnostics cover stock, rotation, and average tenure. "
            "They are different outcomes, so this is a diagnostic comparison "
            "rather than an equivalence claim.",
            "",
            "Section 5.1 line 519 attributes the monthly failure to two "
            "related possibilities: seasonal differences that annual "
            "aggregation may attenuate, and deeper structural cyclical "
            "differences between the treated and control occupation groups.",
            "",
        ]
    )
    for row in diagnostics.itertuples(index=False):
        reading = str(row.section_5_1_reading)
        if reading == "seasonality_attenuation_compatible_not_proven":
            explanation = (
                "is compatible with attenuation of monthly seasonality, "
                "without proving parallel trends"
            )
        elif reading == "annual_diagnostic_inconclusive":
            explanation = (
                "is inconclusive between seasonal attenuation and a "
                "remaining structural difference"
            )
        else:
            explanation = (
                "indicates that a treated-control pretrend difference "
                "remains detectable after annual aggregation"
            )
        lines.append(f"- `{row.outcome}`: `{row.pretrend_status}`; {explanation}.")
    if diagnostics["pretrend_status"].eq("fail").any():
        overall = (
            "At least one annual outcome fails, so annual aggregation does "
            "not remove all detectable treated-control pretrend differences."
        )
    elif diagnostics["pretrend_status"].eq("warning").any():
        overall = (
            "No annual outcome fails, but at least one warning leaves the "
            "seasonality-versus-structure comparison inconclusive."
        )
    else:
        overall = (
            "All annual outcomes pass, which is compatible with attenuation "
            "of monthly seasonality but does not establish parallel trends."
        )
    lines.extend(
        [
            "",
            overall,
            "",
            "A non-significant pretrend diagnostic is not proof of parallel "
            "trends.",
            "",
            "No post-event coefficient is published or used in this report. "
            "R-G3 is non-blocking by design; omitting these diagnostics would "
            "be blocking.",
            "",
        ]
    )
    return "\n".join(lines)


def _future_results_present() -> list[str]:
    return [
        str(path.relative_to(FRONT_ROOT))
        for path in FUTURE_RESULT_PATHS
        if path.exists()
    ]


def run_r8() -> dict[str, Any]:
    """Execute R8 and stop before the static models in R9."""
    part1_status = json.loads(
        PART1_STATUS_PATH.read_text(encoding="utf-8")
    )
    if part1_status.get("gate_r_b1") != "open":
        raise RuntimeError("R-B1 must be open before R8")
    expected_hashes = {
        ANNUAL_PANEL_PATH: str(part1_status["annual_panel_sha256"]),
        ROTATION_PANEL_PATH: str(part1_status["rotation_panel_sha256"]),
    }
    for path, expected in expected_hashes.items():
        observed = sha256_file(path)
        if observed != expected:
            raise RuntimeError(
                f"Panel SHA-256 mismatch for {path.name}: "
                f"expected {expected}, observed {observed}"
            )
    future_before = _future_results_present()
    if future_before:
        raise RuntimeError(
            f"R9/R10 results exist before R8: {future_before}"
        )

    annual = pd.read_parquet(ANNUAL_PANEL_PATH)
    rotation = pd.read_parquet(ROTATION_PANEL_PATH)
    panels = {"annual": annual, "rotation": rotation}
    rows = [
        _run_outcome(panels[str(spec["panel"])], dict(spec))
        for spec in OUTCOME_SPECS
    ]
    diagnostics = pd.DataFrame(rows)[list(DIAGNOSTIC_COLUMNS)]
    monthly = pd.read_csv(MONTHLY_PRETRENDS_PATH)
    report = render_pretrend_report(diagnostics, monthly)

    future_after = _future_results_present()
    if future_after:
        raise RuntimeError(
            f"R9/R10 results appeared during R8: {future_after}"
        )
    classification_counts = {
        str(status): int(count)
        for status, count in diagnostics[
            "pretrend_status"
        ].value_counts().sort_index().items()
    }
    support = {
        "status": "pass",
        "outcome_count": int(len(diagnostics)),
        "classification_counts": classification_counts,
        "all_three_diagnostics_reported": bool(
            diagnostics[
                [
                    "joint_lead_p_value",
                    "linear_pretrend_p_value",
                    "dynamic_min_p_value",
                ]
            ].notna().all().all()
        ),
        "lead_covariance_psd_counts": {
            str(bool(status)).lower(): int(count)
            for status, count in diagnostics[
                "lead_covariance_positive_semidefinite"
            ].value_counts().sort_index().items()
        },
        "monthly_caged_classification_counts": {
            str(status): int(count)
            for status, count in monthly[
                "pretrend_status"
            ].value_counts().sort_index().items()
        },
        "shared_functions": [
            "pretrend_engine.joint_lead_test",
            "pretrends.gls_pretrend_slope",
            "estimators.cluster_t_inference",
            "pretrends.classify_pretrend",
        ],
        "annual_gls_coordinate_shift": -1,
        "annual_reference_event_time": ANNUAL_REFERENCE_EVENT_TIME,
        "future_results_before": future_before,
        "future_results_after": future_after,
        "post_event_coefficients_published": False,
        "non_rejection_is_proof": False,
        "annual_panel_sha256": expected_hashes[ANNUAL_PANEL_PATH],
        "rotation_panel_sha256": expected_hashes[ROTATION_PANEL_PATH],
        "monthly_pretrends_sha256": sha256_file(MONTHLY_PRETRENDS_PATH),
    }
    status = {
        "status": "complete",
        "r8": "complete",
        "r_g3_pretrend_condition": "satisfied",
        "full_part2_gate": "pending_r9_r10",
        "outcomes": int(len(diagnostics)),
        "classification_counts": classification_counts,
        "all_lead_covariances_positive_semidefinite": bool(
            diagnostics[
                "lead_covariance_positive_semidefinite"
            ].all()
        ),
        "post_event_coefficients_published": False,
        "r9_executed": False,
        "r10_executed": False,
    }
    atomic_csv(diagnostics, PRETRENDS_PATH)
    atomic_json(support, PRETRENDS_SUPPORT_PATH)
    atomic_text(report, PRETRENDS_REPORT_PATH)
    atomic_json(status, R8_STATUS_PATH)
    return {
        "diagnostics": diagnostics.to_dict(orient="records"),
        "support": support,
        "status": status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    result = run_r8()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
