#!/usr/bin/env python3
"""Acquire and estimate the four pre-registered RAIS sensitivities."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
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
COMMON_DIR = V2_ROOT / "code" / "common"
MODELS_DIR = V2_ROOT / "code" / "caged" / "models"
for module_dir in (COMMON_DIR, MODELS_DIR):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from estimators import (  # noqa: E402
    build_formula,
    cluster_t_inference,
    fit_model,
)
from pretrend_engine import (  # noqa: E402
    atomic_csv,
    atomic_json,
    atomic_text,
    event_parameter_frame,
    joint_lead_test,
)
from pretrends import classify_pretrend, gls_pretrend_slope  # noqa: E402
from .r8_pretrends import covariance_psd_diagnostic  # noqa: E402
from .r9_static import (  # noqa: E402
    FIT_MODEL_COLUMNS,
    FROZEN_FAMILY_PATHS,
    reconstruct_inference,
)
from .stage0 import (  # noqa: E402
    BILLING_PROJECT,
    SOURCE_TABLE,
    _run_bq_csv,
    sha256_file,
)


TREATMENT_TERM = "post_treat"
FIXED_EFFECTS = ("cbo_4d", "ano")
CLUSTER_VARIABLES = ("cbo_4d",)
INTERACTION = "treated_main"

SENSITIVITY_IDS = (
    "window_2019_2024",
    "exclude_2020",
    "exclude_2022",
    "annual_average_stock",
)

OUTCOME_SPECS = (
    {
        "outcome": "estoque_3112",
        "estimator": "ppml",
        "panel": "annual",
        "principal_years": tuple(range(2019, 2025)),
    },
    {
        "outcome": "ln_taxa_rotatividade",
        "estimator": "ols",
        "panel": "rotation",
        "principal_years": tuple(range(2021, 2025)),
    },
    {
        "outcome": "ln_tempo_emprego_medio",
        "estimator": "ols",
        "panel": "annual",
        "principal_years": tuple(range(2019, 2025)),
    },
)

DOMAIN_DIAGNOSTIC_QUERY = f"""
SELECT
  ano,
  COUNTIF(
    (mes_admissao IS NULL OR mes_admissao NOT BETWEEN 1 AND 12)
    AND NOT (
      tempo_emprego >= CASE
        WHEN CAST(vinculo_ativo_3112 AS STRING) = '1' THEN 12
        ELSE mes_desligamento
      END
    )
  ) AS start_month_unresolved,
  COUNTIF(
    CAST(vinculo_ativo_3112 AS STRING) = '0'
    AND (mes_desligamento IS NULL OR mes_desligamento NOT BETWEEN 1 AND 12)
  ) AS inactive_end_month_unresolved
FROM `{SOURCE_TABLE}`
WHERE ano BETWEEN 2016 AND 2024
  AND cbo_2002 IS NOT NULL
GROUP BY ano
ORDER BY ano
""".strip()

ANNUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_rais_anual.parquet"
ROTATION_PANEL_PATH = (
    FRONT_ROOT / "data" / "painel_rais_rotatividade.parquet"
)
PART1_STATUS_PATH = FRONT_ROOT / "results" / "rais_part1_status.json"
R9_STATUS_PATH = FRONT_ROOT / "results" / "rais_r9_status.json"
R9_RESULTS_PATH = FRONT_ROOT / "results" / "rais_static_results.csv"
DOMAIN_DIAGNOSTIC_PATH = (
    FRONT_ROOT
    / "data"
    / "vintage"
    / "rais_annual_average_stock_domain_diagnostic.csv"
)
DOMAIN_DIAGNOSTIC_MANIFEST_PATH = (
    FRONT_ROOT
    / "data"
    / "vintage"
    / "rais_annual_average_stock_domain_manifest.json"
)
DOMAIN_DIAGNOSTIC_SUPPORT_PATH = (
    FRONT_ROOT
    / "results"
    / "rais_annual_average_stock_not_executable.json"
)
SENSITIVITY_RESULTS_PATH = (
    FRONT_ROOT / "results" / "rais_sensitivities.csv"
)
SENSITIVITY_SUPPORT_PATH = (
    FRONT_ROOT / "results" / "rais_sensitivities_support.json"
)
SENSITIVITY_REPORT_PATH = (
    FRONT_ROOT / "results" / "RAIS_SENSITIVITIES.md"
)
R10_STATUS_PATH = FRONT_ROOT / "results" / "rais_r10_status.json"
R11_RESULT_PATHS = (
    FRONT_ROOT / "results" / "rais_proxy_validation.csv",
    FRONT_ROOT / "results" / "RAIS_RELATORIO.md",
)

PRETREND_COLUMNS = (
    "pretrend_status",
    "pretrend_reason",
    "pretrend_formula",
    "pretrend_reference_year",
    "pretrend_reference_event_time",
    "pretrend_lead_years",
    "pretrend_lead_event_times",
    "pretrend_n_obs",
    "pretrend_minimum_clusters",
    "pretrend_sample_matches_result",
    "pretrend_clusters_match_result",
    "joint_lead_count",
    "joint_lead_statistic",
    "joint_lead_df",
    "joint_lead_p_value",
    "linear_pretrend_coefficient",
    "linear_pretrend_standard_error",
    "linear_pretrend_p_value",
    "dynamic_pre_p_lt_005",
    "dynamic_min_p_value",
    "lead_covariance_min_eigenvalue",
    "lead_covariance_positive_semidefinite",
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


def validate_domain_diagnostic(
    diagnostic: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate and summarize the frozen non-execution diagnostic."""
    required = {
        "ano",
        "start_month_unresolved",
        "inactive_end_month_unresolved",
    }
    _required_columns(
        diagnostic,
        required,
        source_name="Annual-average-stock domain diagnostic",
    )
    frame = diagnostic[
        [
            "ano",
            "start_month_unresolved",
            "inactive_end_month_unresolved",
        ]
    ].copy()
    for column in frame.columns:
        frame[column] = pd.to_numeric(
            frame[column], errors="raise"
        ).astype(int)
    expected_years = list(range(2016, 2025))
    observed_years = frame["ano"].tolist()
    if observed_years != expected_years:
        raise RuntimeError(
            "Annual-average-stock diagnostic years differ from "
            f"{expected_years}: {observed_years}"
        )
    if (
        frame[
            [
                "start_month_unresolved",
                "inactive_end_month_unresolved",
            ]
        ]
        .lt(0)
        .any(axis=None)
    ):
        raise RuntimeError(
            "Annual-average-stock diagnostic contains negative counts"
        )
    unresolved_start = int(frame["start_month_unresolved"].sum())
    unresolved_end = int(
        frame["inactive_end_month_unresolved"].sum()
    )
    if unresolved_start == 0 and unresolved_end == 0:
        raise RuntimeError(
            "Source fields unexpectedly support the rejected construction"
        )
    support = {
        "status": "diagnostic_complete",
        "annual_average_stock_status": (
            "not_executable_source_fields_incomplete"
        ),
        "start_month_unresolved": unresolved_start,
        "inactive_end_month_unresolved": unresolved_end,
        "proxy_substituted": False,
        "monthly_stock_vintage_created": False,
        "treatment_coefficient_estimated": False,
    }
    return frame, support


def build_sensitivity_grid() -> pd.DataFrame:
    """Return the frozen four-by-three sensitivity grid."""
    rows: list[dict[str, Any]] = []
    for sensitivity_id in SENSITIVITY_IDS:
        for spec in OUTCOME_SPECS:
            outcome = str(spec["outcome"])
            principal_years = list(spec["principal_years"])
            excluded_years: list[int] = []
            reference_year = 2022
            model_outcome = outcome
            applicable = True
            initial_status = "pending"
            identical = sensitivity_id == "window_2019_2024"
            if sensitivity_id == "exclude_2020":
                excluded_years = [2020]
                identical = 2020 not in principal_years
            elif sensitivity_id == "exclude_2022":
                excluded_years = [2022]
                reference_year = 2021
                identical = False
            elif sensitivity_id == "annual_average_stock":
                applicable = False
                model_outcome = (
                    "estoque_medio_ano"
                    if outcome == "estoque_3112"
                    else outcome
                )
                initial_status = (
                    "not_executable_source_fields_incomplete"
                    if outcome == "estoque_3112"
                    else "not_applicable"
                )
                identical = False
            sample_years = [
                year
                for year in principal_years
                if year not in excluded_years
            ]
            rows.append(
                {
                    "sensitivity_id": sensitivity_id,
                    "outcome": outcome,
                    "model_outcome": model_outcome,
                    "estimator": str(spec["estimator"]),
                    "panel": str(spec["panel"]),
                    "sample_years": json.dumps(sample_years),
                    "sample_window": (
                        f"{min(sample_years)}-{max(sample_years)}"
                        + (
                            " excluding "
                            + ",".join(map(str, excluded_years))
                            if excluded_years
                            else ""
                        )
                    ),
                    "excluded_years": json.dumps(excluded_years),
                    "reference_year": reference_year,
                    "applicable": applicable,
                    "result_status": initial_status,
                    "is_principal": False,
                    "identical_to_principal": identical,
                }
            )
    return pd.DataFrame(rows)


def expected_lead_years(
    sample_years: Sequence[int],
    *,
    reference_year: int,
) -> list[int]:
    """Return available years strictly before the event-study reference."""
    return sorted(
        int(year)
        for year in sample_years
        if int(year) < int(reference_year)
    )


def not_estimable_pretrend(
    *,
    reference_year: int,
    reason: str,
    n_obs: float = np.nan,
    minimum_clusters: float = np.nan,
    sample_matches: bool = False,
    clusters_match: bool = False,
) -> dict[str, Any]:
    """Return an explicit empty diagnostic without fabricating a test."""
    return {
        "pretrend_status": "not_estimable",
        "pretrend_reason": reason,
        "pretrend_formula": "",
        "pretrend_reference_year": int(reference_year),
        "pretrend_reference_event_time": 0,
        "pretrend_lead_years": "[]",
        "pretrend_lead_event_times": "[]",
        "pretrend_n_obs": n_obs,
        "pretrend_minimum_clusters": minimum_clusters,
        "pretrend_sample_matches_result": sample_matches,
        "pretrend_clusters_match_result": clusters_match,
        "joint_lead_count": 0,
        "joint_lead_statistic": np.nan,
        "joint_lead_df": np.nan,
        "joint_lead_p_value": np.nan,
        "linear_pretrend_coefficient": np.nan,
        "linear_pretrend_standard_error": np.nan,
        "linear_pretrend_p_value": np.nan,
        "dynamic_pre_p_lt_005": 0,
        "dynamic_min_p_value": np.nan,
        "lead_covariance_min_eigenvalue": np.nan,
        "lead_covariance_positive_semidefinite": np.nan,
    }


def _not_applicable_pretrend() -> dict[str, Any]:
    row = not_estimable_pretrend(
        reference_year=2022,
        reason="outcome_not_applicable_to_stock_measure_sensitivity",
    )
    row["pretrend_status"] = "not_applicable"
    return row


def _not_executable_pretrend() -> dict[str, Any]:
    row = not_estimable_pretrend(
        reference_year=2022,
        reason="annual_average_stock_source_fields_incomplete",
    )
    row["pretrend_status"] = (
        "not_executable_source_fields_incomplete"
    )
    return row


def _failed_fit_row(
    grid_row: dict[str, Any],
    *,
    input_cells: int,
    error: Exception,
) -> dict[str, Any]:
    model_outcome = str(grid_row["model_outcome"])
    row: dict[str, Any] = {
        column: np.nan for column in FIT_MODEL_COLUMNS
    }
    row.update(
        {
            "model_id": (
                f"rais_sensitivity__{grid_row['sensitivity_id']}__"
                f"{grid_row['outcome']}"
            ),
            "outcome": model_outcome,
            "term": TREATMENT_TERM,
            "estimator": str(grid_row["estimator"]),
            "input_cells": int(input_cells),
            "converged": False,
            "formula": build_formula(
                model_outcome,
                TREATMENT_TERM,
                FIXED_EFFECTS,
                (),
            ),
            "fixed_effects": " + ".join(FIXED_EFFECTS),
            "cluster_variables": " + ".join(CLUSTER_VARIABLES),
            "controls": "",
            "result_status": "failed_estimation",
            "error": str(error),
        }
    )
    return row


def _fit_sensitivity(
    panel: pd.DataFrame,
    grid_row: dict[str, Any],
) -> dict[str, Any]:
    model_outcome = str(grid_row["model_outcome"])
    years = [int(year) for year in json.loads(grid_row["sample_years"])]
    sample = panel.loc[panel["ano"].isin(years)].copy()
    try:
        shared, _ = fit_model(
            sample,
            model_id=(
                f"rais_sensitivity__{grid_row['sensitivity_id']}__"
                f"{grid_row['outcome']}"
            ),
            outcome=model_outcome,
            treatment_term=TREATMENT_TERM,
            estimator=str(grid_row["estimator"]),
            fixed_effects=FIXED_EFFECTS,
            cluster_variables=CLUSTER_VARIABLES,
            controls=(),
            principal=False,
        )
        if tuple(shared) != FIT_MODEL_COLUMNS:
            raise RuntimeError(
                "Shared fit_model schema differs from the frozen R10 contract"
            )
        original = {
            key: shared[key]
            for key in ("ci_low", "ci_high", "p_value", "cluster_df")
        }
        reconstructed = reconstruct_inference(
            {**shared, "result_status": "estimated", "error": ""}
        )
        for key, value in original.items():
            if not math.isclose(
                float(value),
                float(reconstructed[key]),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise RuntimeError(
                    f"Cluster-t reconstruction mismatch: {key}"
                )
        return {
            **reconstructed,
            "result_status": "estimated",
            "error": "",
        }
    except Exception as error:  # noqa: BLE001
        return _failed_fit_row(
            grid_row,
            input_cells=int(len(sample)),
            error=error,
        )


def _build_event_formula(outcome: str) -> str:
    return (
        f"{outcome} ~ i(event_time, {INTERACTION}, ref=0) | "
        + " + ".join(FIXED_EFFECTS)
    )


def _fit_exact_pretrend(
    panel: pd.DataFrame,
    grid_row: dict[str, Any],
    static_result: dict[str, Any],
) -> dict[str, Any]:
    years = [int(year) for year in json.loads(grid_row["sample_years"])]
    reference_year = int(grid_row["reference_year"])
    lead_years = expected_lead_years(
        years,
        reference_year=reference_year,
    )
    if not lead_years:
        return not_estimable_pretrend(
            reference_year=reference_year,
            reason="no_pre_reference_coefficients",
            n_obs=float(static_result["n_obs"]),
            minimum_clusters=float(static_result["minimum_clusters"]),
            sample_matches=True,
            clusters_match=True,
        )
    outcome = str(grid_row["model_outcome"])
    required = {"cbo_4d", "ano", "treated_main", outcome}
    _required_columns(
        panel,
        required,
        source_name=f"R10 pretrend panel for {outcome}",
    )
    data = panel.loc[panel["ano"].isin(years)].copy()
    data["event_time"] = (
        pd.to_numeric(data["ano"], errors="raise").astype(int)
        - reference_year
    )
    data = data.dropna(subset=list(required) + ["event_time"]).copy()
    observed_years = sorted(data["ano"].astype(int).unique().tolist())
    if observed_years != sorted(years):
        raise RuntimeError(
            f"R10 event grid has missing years for {outcome}: "
            f"expected {years}, observed {observed_years}"
        )
    formula = _build_event_formula(outcome)
    import pyfixest as pf

    vcov = {"CRV1": "cbo_4d"}
    if str(grid_row["estimator"]) == "ppml":
        if (data[outcome] < 0).any():
            raise ValueError("PPML pretrend outcome must be weakly positive")
        model = pf.fepois(
            formula,
            data=data,
            vcov=vcov,
            separation_check=["fe", "ir"],
        )
        if not bool(getattr(model, "_convergence", False)):
            raise RuntimeError(f"R10 PPML pretrend did not converge: {outcome}")
    else:
        model = pf.feols(formula, data=data, vcov=vcov)
    used = getattr(model, "_data", data)
    cluster_counts = {"cbo_4d": int(used["cbo_4d"].nunique())}
    expected_times = sorted(
        year - reference_year
        for year in years
        if year != reference_year
    )
    lead_times = sorted(year - reference_year for year in lead_years)
    parameters = event_parameter_frame(
        model,
        INTERACTION,
        expected_event_times=expected_times,
    )
    leads = parameters.loc[
        parameters["event_time"].isin(lead_times)
    ].copy()
    if leads["event_time"].astype(int).tolist() != lead_times:
        raise RuntimeError("R10 lead parameter grid is incomplete")
    covariance = np.asarray(model._vcov, dtype=float)
    positions = leads["position"].astype(int).to_numpy()
    lead_covariance = covariance[np.ix_(positions, positions)]
    psd = covariance_psd_diagnostic(lead_covariance)
    joint = joint_lead_test(model, positions)
    linear = gls_pretrend_slope(
        leads["coefficient"].to_numpy(),
        lead_covariance,
        leads["event_time"].to_numpy(dtype=float) - 1.0,
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
    n_obs = int(model._N)
    minimum_clusters = int(min(cluster_counts.values()))
    sample_matches = n_obs == int(static_result["n_obs"])
    clusters_match = minimum_clusters == int(
        static_result["minimum_clusters"]
    )
    if not sample_matches or not clusters_match:
        raise RuntimeError(
            "R10 sensitivity/pretrend sample mismatch: "
            f"{grid_row['sensitivity_id']} {grid_row['outcome']}"
        )
    return {
        "pretrend_status": classify_pretrend(
            float(joint["p_value"]),
            float(linear["p_value"]),
            n_individual,
        ),
        "pretrend_reason": "estimated_exact_static_sample",
        "pretrend_formula": formula,
        "pretrend_reference_year": reference_year,
        "pretrend_reference_event_time": 0,
        "pretrend_lead_years": json.dumps(lead_years),
        "pretrend_lead_event_times": json.dumps(lead_times),
        "pretrend_n_obs": n_obs,
        "pretrend_minimum_clusters": minimum_clusters,
        "pretrend_sample_matches_result": sample_matches,
        "pretrend_clusters_match_result": clusters_match,
        "joint_lead_count": int(len(leads)),
        "joint_lead_statistic": float(joint["statistic"]),
        "joint_lead_df": int(joint["df"]),
        "joint_lead_p_value": float(joint["p_value"]),
        "linear_pretrend_coefficient": float(linear["coefficient"]),
        "linear_pretrend_standard_error": float(
            linear["standard_error"]
        ),
        "linear_pretrend_p_value": float(linear["p_value"]),
        "dynamic_pre_p_lt_005": n_individual,
        "dynamic_min_p_value": float(min(individual_p_values)),
        **psd,
    }


def _format_number(value: Any, digits: int = 4) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "NA"
    if not np.isfinite(numeric):
        return "NA"
    return f"{numeric:.{digits}f}"


def _format_p_value(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "NA"
    if not np.isfinite(numeric):
        return "NA"
    if numeric < 0.001:
        return "<0.001"
    return f"{numeric:.3f}"


def render_sensitivity_report(results: pd.DataFrame) -> str:
    """Render the frozen hierarchy and all twelve grid positions."""
    lines = [
        "# RAIS declared sensitivities",
        "",
        "The sensitivity hierarchy was frozen before estimation. These "
        "specifications never replace the principal specification, are "
        "outside family D, and receive no new multiplicity family.",
        "",
        "| Sensitivity | Outcome | Years | Status | Coefficient | SE | "
        "Nominal p | Pretrend | Identical to principal |",
        "|---|---|---|---|---:|---:|---:|---|---|",
    ]
    for row in results.itertuples(index=False):
        lines.append(
            f"| `{row.sensitivity_id}` | `{row.outcome}` | "
            f"{row.sample_window} | `{row.result_status}` | "
            f"{_format_number(getattr(row, 'coefficient', np.nan))} | "
            f"{_format_number(getattr(row, 'standard_error', np.nan))} | "
            f"{_format_p_value(getattr(row, 'nominal_p_value', np.nan))} | "
            f"`{row.pretrend_status}` | "
            f"`{str(row.identical_to_principal).lower()}` |"
        )
    lines.extend(
        [
            "",
            "The 2019–2024 window rows are exact no-op replications because "
            "R-G2 already shortened the principal window. Excluding 2020 is "
            "also a no-op for rotation, whose panel begins in 2021. These "
            "positions remain visible rather than being silently dropped.",
            "",
            "The annual-average-stock sensitivity is "
            "`not_executable_source_fields_incomplete`: admission and "
            "separation months do not identify all monthly link statuses. "
            "No remuneration proxy or other unsigned stock measure replaces "
            "it. Rotation and average tenure are `not_applicable` to that "
            "stock-definition change.",
            "",
            "When 2022 is excluded, 2021 is the pretrend reference. Rotation "
            "then has no earlier pre-reference coefficient, so its diagnostic "
            "is explicitly `not_estimable`; no p-value is invented.",
            "",
            "Sensitivity p-values are nominal diagnostics. The frozen family "
            "D remains the three principal R9 outcomes with its single BH "
            "adjustment.",
            "",
        ]
    )
    return "\n".join(lines)


def _frozen_family_hashes() -> dict[str, str]:
    return {
        family_id: sha256_file(path)
        for family_id, path in FROZEN_FAMILY_PATHS.items()
    }


def run_diagnose() -> dict[str, Any]:
    """Freeze the domain evidence that prevents annual-average estimation."""
    if SENSITIVITY_RESULTS_PATH.exists():
        raise RuntimeError("R10 results already exist before diagnosis")
    rows = _run_bq_csv(DOMAIN_DIAGNOSTIC_QUERY, max_rows=100)
    diagnostic, support = validate_domain_diagnostic(pd.DataFrame(rows))
    atomic_csv(diagnostic, DOMAIN_DIAGNOSTIC_PATH)
    manifest = {
        "fonte": "Base dos Dados BigQuery mirror",
        "tabela": SOURCE_TABLE,
        "billing_project": BILLING_PROJECT,
        "consulta": DOMAIN_DIAGNOSTIC_QUERY,
        "linhas": int(len(diagnostic)),
        "bytes": DOMAIN_DIAGNOSTIC_PATH.stat().st_size,
        "sha256": sha256_file(DOMAIN_DIAGNOSTIC_PATH),
        "acessado_em": datetime.now(timezone.utc).isoformat(),
        "use": "diagnostic-only evidence for R10 non-execution",
        "treatment_coefficient_estimated": False,
    }
    atomic_json(manifest, DOMAIN_DIAGNOSTIC_MANIFEST_PATH)
    payload = {
        **support,
        "diagnostic_sha256": manifest["sha256"],
        "live_query_used_only_for_diagnostic": True,
        "remaining_estimation_reads_frozen_inputs_only": True,
    }
    atomic_json(payload, DOMAIN_DIAGNOSTIC_SUPPORT_PATH)
    return {"manifest": manifest, "support": payload}


def run_replay_diagnostic() -> dict[str, Any]:
    """Validate and publish the frozen diagnostic without network access."""
    if SENSITIVITY_RESULTS_PATH.exists():
        raise RuntimeError("R10 results already exist before diagnosis")
    if not DOMAIN_DIAGNOSTIC_PATH.is_file():
        raise FileNotFoundError(DOMAIN_DIAGNOSTIC_PATH)
    if not DOMAIN_DIAGNOSTIC_MANIFEST_PATH.is_file():
        raise FileNotFoundError(DOMAIN_DIAGNOSTIC_MANIFEST_PATH)

    manifest = json.loads(
        DOMAIN_DIAGNOSTIC_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    observed_hash = sha256_file(DOMAIN_DIAGNOSTIC_PATH)
    if observed_hash != str(manifest.get("sha256", "")):
        raise RuntimeError(
            "Annual-average-stock domain diagnostic SHA-256 mismatch"
        )
    if str(manifest.get("consulta", "")).strip() != DOMAIN_DIAGNOSTIC_QUERY:
        raise RuntimeError("Frozen domain diagnostic query contract mismatch")
    if bool(manifest.get("treatment_coefficient_estimated", True)):
        raise RuntimeError("Frozen domain diagnostic contains a treatment estimate")

    diagnostic, support = validate_domain_diagnostic(
        pd.read_csv(DOMAIN_DIAGNOSTIC_PATH)
    )
    if len(diagnostic) != int(manifest.get("linhas", -1)):
        raise RuntimeError("Frozen domain diagnostic row-count mismatch")
    payload = {
        **support,
        "diagnostic_sha256": observed_hash,
        "live_query_used_only_for_diagnostic": True,
        "current_run_used_network": False,
        "remaining_estimation_reads_frozen_inputs_only": True,
    }
    atomic_json(payload, DOMAIN_DIAGNOSTIC_SUPPORT_PATH)
    return {"manifest": manifest, "support": payload}


def _unestimated_result(grid_row: dict[str, Any]) -> dict[str, Any]:
    status = str(grid_row["result_status"])
    if status == "not_applicable":
        error = (
            "stock-definition sensitivity does not apply to "
            "this non-stock outcome"
        )
    elif status == "not_executable_source_fields_incomplete":
        error = (
            "admission and separation fields do not identify all "
            "monthly employment statuses"
        )
    else:
        raise ValueError(f"Unsupported unestimated status: {status}")
    result = {
        column: np.nan for column in FIT_MODEL_COLUMNS
    }
    result.update(
        {
            "model_id": (
                f"rais_sensitivity__{grid_row['sensitivity_id']}__"
                f"{grid_row['outcome']}"
            ),
            "outcome": str(grid_row["model_outcome"]),
            "term": TREATMENT_TERM,
            "estimator": str(grid_row["estimator"]),
            "converged": False,
            "fixed_effects": " + ".join(FIXED_EFFECTS),
            "cluster_variables": " + ".join(CLUSTER_VARIABLES),
            "controls": "",
            "result_status": status,
            "error": error,
        }
    )
    return result


def run_estimate() -> dict[str, Any]:
    """Estimate R10 from frozen inputs and stop before R11."""
    if any(path.exists() for path in R11_RESULT_PATHS):
        raise RuntimeError("A Part 3 artifact exists before R10")
    r9_status = json.loads(R9_STATUS_PATH.read_text(encoding="utf-8"))
    if r9_status.get("r9") != "complete":
        raise RuntimeError("R9 must be complete before R10")
    if sha256_file(R9_RESULTS_PATH) != str(
        r9_status["static_results_sha256"]
    ):
        raise RuntimeError("R9 result SHA-256 mismatch")
    if not DOMAIN_DIAGNOSTIC_SUPPORT_PATH.exists():
        raise RuntimeError(
            "The annual-average-stock non-execution diagnostic must be "
            "published before R10 estimation"
        )
    domain_manifest = json.loads(
        DOMAIN_DIAGNOSTIC_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    observed_domain_hash = sha256_file(DOMAIN_DIAGNOSTIC_PATH)
    if observed_domain_hash != str(domain_manifest["sha256"]):
        raise RuntimeError(
            "Annual-average-stock domain diagnostic SHA-256 mismatch"
        )
    part1_status = json.loads(
        PART1_STATUS_PATH.read_text(encoding="utf-8")
    )
    panel_hashes = {
        ANNUAL_PANEL_PATH: str(part1_status["annual_panel_sha256"]),
        ROTATION_PANEL_PATH: str(part1_status["rotation_panel_sha256"]),
    }
    for path, expected in panel_hashes.items():
        observed = sha256_file(path)
        if observed != expected:
            raise RuntimeError(
                f"Panel SHA-256 mismatch for {path.name}: "
                f"expected {expected}, observed {observed}"
            )
    family_hashes_before = _frozen_family_hashes()
    r9_hash_before = sha256_file(R9_RESULTS_PATH)

    annual = pd.read_parquet(ANNUAL_PANEL_PATH)
    rotation = pd.read_parquet(ROTATION_PANEL_PATH)
    panels = {"annual": annual, "rotation": rotation}

    output_rows: list[dict[str, Any]] = []
    for grid_record in build_sensitivity_grid().to_dict(orient="records"):
        grid_row = dict(grid_record)
        if not bool(grid_row["applicable"]):
            fitted = _unestimated_result(grid_row)
            if (
                fitted["result_status"]
                == "not_executable_source_fields_incomplete"
            ):
                pretrend = _not_executable_pretrend()
            else:
                pretrend = _not_applicable_pretrend()
        else:
            panel = panels[str(grid_row["panel"])]
            fitted = _fit_sensitivity(panel, grid_row)
            if fitted["result_status"] == "estimated":
                pretrend = _fit_exact_pretrend(panel, grid_row, fitted)
            else:
                pretrend = not_estimable_pretrend(
                    reference_year=int(grid_row["reference_year"]),
                    reason="static_sensitivity_failed_estimation",
                )
        shared_outcome = fitted.pop("outcome")
        row = {
            **grid_row,
            **fitted,
            "outcome": str(grid_row["outcome"]),
            "model_outcome": str(shared_outcome),
            "nominal_p_value": fitted.get("p_value", np.nan),
            "bh_adjusted_p_value": np.nan,
            "family_id": "",
            "family_size": np.nan,
            "multiplicity_method": "",
            "multiplicity_status": (
                "not_applicable"
                if fitted["result_status"]
                in {
                    "not_applicable",
                    "not_executable_source_fields_incomplete",
                }
                else "not_applicable_nonprincipal_sensitivity"
            ),
            "significance_marker": "",
            "star_source": "none_nonprincipal_sensitivity",
            **pretrend,
        }
        output_rows.append(row)
    results = pd.DataFrame(output_rows)
    if len(results) != 12:
        raise RuntimeError("R10 sensitivity grid must contain 12 rows")
    if not results["is_principal"].eq(False).all():
        raise RuntimeError("A sensitivity was marked principal")
    if results["result_status"].eq("not_applicable").sum() != 2:
        raise RuntimeError("R10 must retain exactly two not-applicable rows")
    if (
        results["result_status"]
        .eq("not_executable_source_fields_incomplete")
        .sum()
        != 1
    ):
        raise RuntimeError(
            "R10 must retain exactly one source-field non-execution row"
        )
    if results["significance_marker"].ne("").any():
        raise RuntimeError("Sensitivity results must not display stars")
    estimated = results["result_status"].eq("estimated")
    estimable_pretrend = estimated & ~results["pretrend_status"].eq(
        "not_estimable"
    )
    if not results.loc[
        estimable_pretrend,
        [
            "pretrend_sample_matches_result",
            "pretrend_clusters_match_result",
        ],
    ].all(axis=None):
        raise RuntimeError("An estimable R10 pretrend sample does not match")
    not_estimable = results["pretrend_status"].eq("not_estimable")
    expected_not_estimable = (
        results["sensitivity_id"].eq("exclude_2022")
        & results["outcome"].eq("ln_taxa_rotatividade")
    )
    if not not_estimable.equals(expected_not_estimable):
        raise RuntimeError(
            "Unexpected set of non-estimable R10 pretrends"
        )
    family_hashes_after = _frozen_family_hashes()
    r9_hash_after = sha256_file(R9_RESULTS_PATH)
    if family_hashes_after != family_hashes_before:
        raise RuntimeError("A frozen A/B/C family changed during R10")
    if r9_hash_after != r9_hash_before:
        raise RuntimeError("Frozen family D changed during R10")

    preferred_columns = [
        "sensitivity_id",
        "outcome",
        "model_outcome",
        "model_id",
        "result_status",
        "error",
        "is_principal",
        "applicable",
        "identical_to_principal",
        "sample_years",
        "sample_window",
        "excluded_years",
        "reference_year",
        "term",
        "estimator",
        "coefficient",
        "standard_error",
        "ci_low",
        "ci_high",
        "p_value",
        "nominal_p_value",
        "bh_adjusted_p_value",
        "family_id",
        "family_size",
        "multiplicity_method",
        "multiplicity_status",
        "cluster_df",
        "cluster_counts",
        "minimum_clusters",
        "n_obs",
        "input_cells",
        "complete_case_cells",
        "cells_dropped",
        "cells_dropped_missing",
        "cells_dropped_estimator",
        "separation_dropped",
        "converged",
        "formula",
        "fixed_effects",
        "cluster_variables",
        "controls",
        "effect_percent",
        "significance_marker",
        "star_source",
        *PRETREND_COLUMNS,
    ]
    results = results[preferred_columns]
    atomic_csv(results, SENSITIVITY_RESULTS_PATH)
    atomic_text(
        render_sensitivity_report(results),
        SENSITIVITY_REPORT_PATH,
    )
    pretrend_counts = {
        str(status): int(count)
        for status, count in results["pretrend_status"].value_counts().items()
    }
    support = {
        "status": "pass",
        "grid_rows": int(len(results)),
        "estimated_rows": int(estimated.sum()),
        "failed_estimation_rows": int(
            results["result_status"].eq("failed_estimation").sum()
        ),
        "not_applicable_rows": int(
            results["result_status"].eq("not_applicable").sum()
        ),
        "not_executable_rows": int(
            results["result_status"]
            .eq("not_executable_source_fields_incomplete")
            .sum()
        ),
        "identical_to_principal_rows": int(
            results["identical_to_principal"].sum()
        ),
        "pretrend_status_counts": pretrend_counts,
        "all_estimable_pretrends_match_static_samples": True,
        "non_estimable_pretrends_reported": int(not_estimable.sum()),
        "display_markers": int(
            results["significance_marker"].ne("").sum()
        ),
        "is_principal_true_rows": int(results["is_principal"].sum()),
        "r10_bh_application_count": 0,
        "sensitivities_outside_family_d": True,
        "family_abc_sha256_before": family_hashes_before,
        "family_abc_sha256_after": family_hashes_after,
        "family_abc_unchanged": True,
        "family_d_sha256_before": r9_hash_before,
        "family_d_sha256_after": r9_hash_after,
        "family_d_unchanged": True,
        "annual_average_domain_diagnostic_sha256": (
            observed_domain_hash
        ),
        "domain_diagnostic_published_before_results": bool(
            DOMAIN_DIAGNOSTIC_SUPPORT_PATH.stat().st_mtime
            <= SENSITIVITY_RESULTS_PATH.stat().st_mtime
        ),
        "annual_average_stock_status": (
            "not_executable_source_fields_incomplete"
        ),
        "annual_average_proxy_substituted": False,
        "shared_functions": [
            "estimators.fit_model",
            "estimators.cluster_t_inference",
            "pretrends.classify_pretrend",
            "pretrends.gls_pretrend_slope",
            "pretrend_engine.joint_lead_test",
        ],
        "hierarchy_frozen_before_estimation": True,
        "sensitivity_promoted_to_principal": False,
        "r11_executed": False,
    }
    atomic_json(support, SENSITIVITY_SUPPORT_PATH)
    status = {
        "status": "complete",
        "r10": "complete",
        "r11": "not_executed",
        "gate_r_g3": "open_diagnostics_reported",
        "gate_r_g3_blocking_failure": False,
        "grid_rows": int(len(results)),
        "estimated_rows": int(estimated.sum()),
        "not_applicable_rows": int(
            results["result_status"].eq("not_applicable").sum()
        ),
        "not_executable_rows": int(
            results["result_status"]
            .eq("not_executable_source_fields_incomplete")
            .sum()
        ),
        "not_estimable_pretrends": int(not_estimable.sum()),
        "sensitivities_sha256": sha256_file(SENSITIVITY_RESULTS_PATH),
        "annual_average_domain_diagnostic_sha256": (
            observed_domain_hash
        ),
    }
    atomic_json(status, R10_STATUS_PATH)
    return {
        "results": results.to_dict(orient="records"),
        "support": support,
        "status": status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("diagnose", "replay-diagnostic", "estimate"),
        help=(
            "Acquire the annual-average non-execution diagnostic, validate "
            "its frozen copy offline, or estimate the remaining sensitivities."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.action == "diagnose":
        result = run_diagnose()
    elif args.action == "replay-diagnostic":
        result = run_replay_diagnostic()
    else:
        result = run_estimate()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
