#!/usr/bin/env python3
"""Quarterly exact-model pretrend diagnostics for PNADc Front 2."""

from __future__ import annotations

import argparse
import gc
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


sys.dont_write_bytecode = True

FRONT_ROOT = Path(__file__).resolve().parents[1]
V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
MODELS_DIR = V2_ROOT / "code" / "caged" / "models"
sys.path.insert(0, str(MODELS_DIR))

from estimators import cluster_t_inference  # noqa: E402
from pretrends import classify_pretrend, gls_pretrend_slope  # noqa: E402
from .stage0 import (  # noqa: E402
    atomic_csv,
    atomic_json,
    atomic_text,
    sha256_file,
)


EVENT_QUARTER_NUMBER = 44
REFERENCE_EVENT_TIME = -1
INTERACTION = "treated"
FIXED_EFFECTS = ("cod3", "trimestre_num")
CLUSTER_VARIABLES = ("cod3",)

INDIVIDUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_pnadc_individual.parquet"
COD3_PANEL_PATH = FRONT_ROOT / "data" / "painel_pnadc_cod3.parquet"
PART1_STATUS_PATH = FRONT_ROOT / "results" / "pnadc_part1_status.json"
PRETRENDS_PATH = FRONT_ROOT / "results" / "pnadc_pretrends.csv"
PRETRENDS_REPORT_PATH = FRONT_ROOT / "results" / "PNADC_PRETRENDS.md"
PRETRENDS_STATUS_PATH = (
    FRONT_ROOT / "results" / "pnadc_pretrends_status.json"
)

OUTCOME_SPECS = (
    {
        "outcome": "informal",
        "arm": "A",
        "estimator": "ols",
        "weight_column": "peso",
    },
    {
        "outcome": "conta_propria",
        "arm": "A",
        "estimator": "ols",
        "weight_column": "peso",
    },
    {
        "outcome": "ocupados_total",
        "arm": "B",
        "estimator": "ppml",
        "weight_column": None,
    },
    {
        "outcome": "ocupados_formais",
        "arm": "B",
        "estimator": "ppml",
        "weight_column": None,
    },
    {
        "outcome": "ocupados_informais",
        "arm": "B",
        "estimator": "ppml",
        "weight_column": None,
    },
    {
        "outcome": "ln_renda",
        "arm": "A",
        "estimator": "ols",
        "weight_column": "peso",
    },
)

SAMPLE_SPECS = (
    {"sample": "full", "exclude_2020": False},
    {"sample": "without_2020", "exclude_2020": True},
)


def quarter_event_time(trimestre_num: int) -> int:
    """Map the one-based PNADc quarter index to the frozen event coordinate."""
    return int(trimestre_num) - EVENT_QUARTER_NUMBER


def expected_coefficient_event_times(exclude_2020: bool) -> list[int]:
    """Return the coefficient grid, excluding the reference and transition."""
    observed_quarters = [
        quarter
        for quarter in range(1, 58)
        if quarter != EVENT_QUARTER_NUMBER
        and not (exclude_2020 and 33 <= quarter <= 36)
    ]
    return [
        quarter_event_time(quarter)
        for quarter in observed_quarters
        if quarter_event_time(quarter) != REFERENCE_EVENT_TIME
    ]


def build_quarterly_event_formula(outcome: str) -> str:
    """Build the registered quarterly interaction and fixed-effect formula."""
    fixed_effects = " + ".join(FIXED_EFFECTS)
    return (
        f"{outcome} ~ i(event_time, {INTERACTION}, "
        f"ref={REFERENCE_EVENT_TIME}) | {fixed_effects}"
    )


def covariance_psd_diagnostic(
    covariance: np.ndarray,
) -> dict[str, float | bool]:
    """Report, rather than assume, positive semidefiniteness."""
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


def derive_pretrend_timing(
    full_status: str,
    without_2020_status: str,
) -> str:
    """Apply the precommitted recent-versus-structural decision table."""
    allowed = {"pass", "warning", "fail"}
    if full_status not in allowed or without_2020_status not in allowed:
        raise ValueError("Unknown pretrend status")
    if full_status == "fail" and without_2020_status == "fail":
        return "structural_difference_persists_without_2020"
    if full_status == "fail":
        return "divergence_concentrated_around_2020"
    if without_2020_status == "fail":
        return "diagnostic_unstable_to_2020_exclusion"
    return "no_systematic_pretrend_detected_not_proof"


def _parse_event_time(term: str) -> int:
    match = re.search(
        rf"\[T?\.?(-?\d+)\]:{re.escape(INTERACTION)}$",
        term,
    )
    if not match:
        raise ValueError(f"Not a quarterly event-time term: {term}")
    return int(match.group(1))


def _event_parameter_frame(
    model: Any,
    expected_event_times: Sequence[int],
) -> pd.DataFrame:
    coefficients = model.coef()
    standard_errors = model.se()
    rows: list[dict[str, Any]] = []
    for position, name in enumerate(str(value) for value in coefficients.index):
        try:
            event_time = _parse_event_time(name)
        except ValueError:
            continue
        rows.append(
            {
                "position": position,
                "term": name,
                "event_time": event_time,
                "coefficient": float(coefficients.iloc[position]),
                "standard_error": float(standard_errors.iloc[position]),
            }
        )
    if not rows:
        raise RuntimeError("No quarterly event-time coefficients were found")
    parameters = pd.DataFrame(rows).sort_values("event_time")
    observed = parameters["event_time"].astype(int).tolist()
    if observed != list(expected_event_times):
        raise RuntimeError(
            "Estimated quarterly event-time parameter grid is incomplete: "
            f"expected {list(expected_event_times)}, observed {observed}"
        )
    return parameters.reset_index(drop=True)


def _joint_lead_test(
    model: Any,
    positions: np.ndarray,
) -> dict[str, float | int]:
    if not len(positions):
        raise ValueError("The joint lead test requires at least one lead")
    restriction = np.zeros((len(positions), len(model.coef())))
    for row, position in enumerate(positions):
        restriction[row, int(position)] = 1.0
    result = model.wald_test(
        R=restriction,
        q=np.zeros(len(positions)),
        distribution="chi2",
    )
    return {
        "statistic": float(result["statistic"]),
        "p_value": float(result["pvalue"]),
        "df": int(len(positions)),
    }


def fit_quarterly_event_model(
    data: pd.DataFrame,
    *,
    outcome: str,
    estimator: str,
    weight_column: str | None,
    model_id: str,
) -> tuple[Any, pd.DataFrame, str, dict[str, int]]:
    """Fit one exact quarterly dynamic counterpart of a static result."""
    required = [
        outcome,
        "event_time",
        INTERACTION,
        *FIXED_EFFECTS,
        *CLUSTER_VARIABLES,
    ]
    if weight_column is not None:
        required.append(weight_column)
    required = list(dict.fromkeys(required))
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Model data is missing columns: {missing}")
    model_data = data.dropna(subset=required).copy()
    if model_data.empty:
        raise RuntimeError(f"No complete cases for model {model_id}")
    if 0 in model_data["event_time"].astype(int).unique():
        raise ValueError("Transition event_time zero must be excluded")
    if REFERENCE_EVENT_TIME not in model_data["event_time"].astype(int).unique():
        raise ValueError("Reference quarter 2022Q3 is missing")
    if not model_data[INTERACTION].isin([0, 1]).all():
        raise ValueError("treated must be binary")
    if weight_column is not None:
        weights = pd.to_numeric(model_data[weight_column], errors="raise")
        if (~np.isfinite(weights) | weights.le(0)).any():
            raise ValueError("Analytic weights must be finite and positive")
    if estimator == "ppml" and model_data[outcome].lt(0).any():
        raise ValueError("PPML outcome must be weakly positive")

    formula = build_quarterly_event_formula(outcome)
    vcov = {"CRV1": " + ".join(CLUSTER_VARIABLES)}
    import pyfixest as pf

    if estimator == "ols":
        arguments: dict[str, Any] = {
            "fml": formula,
            "data": model_data,
            "vcov": vcov,
        }
        if weight_column is not None:
            arguments["weights"] = weight_column
        model = pf.feols(**arguments)
    elif estimator == "ppml":
        if weight_column is not None:
            raise ValueError("Weighted PPML is not registered")
        model = pf.fepois(
            formula,
            data=model_data,
            vcov=vcov,
            separation_check=["fe", "ir"],
        )
        if not bool(getattr(model, "_convergence", False)):
            raise RuntimeError(
                f"Quarterly PPML did not converge: {model_id}"
            )
    else:
        raise ValueError(f"Unsupported estimator: {estimator}")

    used_data = getattr(model, "_data", model_data)
    cluster_counts = {
        variable: int(used_data[variable].nunique())
        for variable in CLUSTER_VARIABLES
    }
    return model, model_data, formula, cluster_counts


def collapse_weighted_event_data(
    data: pd.DataFrame,
    *,
    outcome: str,
    weight_column: str,
) -> tuple[pd.DataFrame, int]:
    """Collapse individual WLS score equations to exact sufficient statistics."""
    required = {
        "cod3",
        "trimestre_num",
        "event_time",
        "treated",
        outcome,
        weight_column,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Weighted event data is missing columns: {missing}")
    complete = data.dropna(subset=list(required)).copy()
    weights = pd.to_numeric(complete[weight_column], errors="raise")
    if (~np.isfinite(weights) | weights.le(0)).any():
        raise ValueError("Analytic weights must be finite and positive")
    complete["_weighted_outcome"] = (
        weights * pd.to_numeric(complete[outcome], errors="raise")
    )
    keys = ["cod3", "trimestre_num", "event_time", "treated"]
    collapsed = (
        complete.groupby(keys, as_index=False, observed=True)
        .agg(
            cell_weight=(weight_column, "sum"),
            weighted_outcome=("_weighted_outcome", "sum"),
            source_observations=(outcome, "size"),
        )
        .sort_values(["trimestre_num", "cod3", "treated"])
        .reset_index(drop=True)
    )
    collapsed[outcome] = (
        collapsed["weighted_outcome"] / collapsed["cell_weight"]
    )
    source_observations = int(collapsed["source_observations"].sum())
    if source_observations != len(complete):
        raise RuntimeError("Collapsed observations do not reproduce input")
    return collapsed, source_observations


def _rescale_collapsed_crv1(
    model: Any,
    *,
    source_observations: int,
) -> None:
    """Replace the cell-count CRV1 factor with the individual-count factor."""
    if source_observations < int(model._N):
        raise ValueError("Source observations cannot be fewer than cells")
    import pyfixest as pf

    fixed_effect_counts = model._k_fe
    nested_fixed_effects = int(
        fixed_effect_counts.get(CLUSTER_VARIABLES[0], 0)
    )
    fully_nested_dimensions = int(nested_fixed_effects > 0)
    target_ssc, df_k, df_t = pf.get_ssc(
        ssc_dict=model._ssc_dict,
        N=int(source_observations),
        k=int(model._k),
        k_fe=int(fixed_effect_counts.sum()),
        k_fe_nested=nested_fixed_effects,
        n_fe=int(model._n_fe),
        n_fe_fully_nested=fully_nested_dimensions,
        G=int(min(model._G)),
        vcov_sign=1,
        vcov_type="CRV",
    )
    current_factor = float(np.asarray(model._ssc).reshape(-1)[0])
    target_factor = float(np.asarray(target_ssc).reshape(-1)[0])
    if current_factor <= 0 or target_factor <= 0:
        raise RuntimeError("CRV1 small-sample factor must be positive")
    model._vcov = model._vcov * (target_factor / current_factor)
    model._ssc = np.array([[target_factor]])
    model._df_k = int(df_k)
    model._df_t = int(df_t)
    model._N = int(source_observations)
    model._N_rows = int(source_observations)
    model.get_inference()


def fit_collapsed_weighted_event_model(
    collapsed: pd.DataFrame,
    *,
    outcome: str,
    source_observations: int,
    model_id: str,
) -> tuple[Any, pd.DataFrame, str, dict[str, int]]:
    """Fit the memory-safe exact counterpart of an individual weighted model."""
    model, model_data, formula, cluster_counts = (
        fit_quarterly_event_model(
            collapsed,
            outcome=outcome,
            estimator="ols",
            weight_column="cell_weight",
            model_id=model_id,
        )
    )
    _rescale_collapsed_crv1(
        model,
        source_observations=source_observations,
    )
    return model, model_data, formula, cluster_counts


def run_model_diagnostics(
    model: Any,
    *,
    expected_event_times: Sequence[int],
    lead_event_times: Sequence[int],
    cluster_counts: dict[str, int],
) -> dict[str, Any]:
    """Run the three frozen diagnostics on one quarterly event model."""
    parameters = _event_parameter_frame(model, expected_event_times)
    leads = parameters.loc[
        parameters["event_time"].isin(lead_event_times)
    ].copy()
    if leads["event_time"].astype(int).tolist() != list(lead_event_times):
        raise RuntimeError("Quarterly lead parameter grid is incomplete")
    covariance = np.asarray(model._vcov, dtype=float)
    lead_positions = leads["position"].astype(int).to_numpy()
    lead_covariance = covariance[np.ix_(lead_positions, lead_positions)]
    psd = covariance_psd_diagnostic(lead_covariance)
    joint = _joint_lead_test(model, lead_positions)
    linear = gls_pretrend_slope(
        leads["coefficient"].to_numpy(),
        lead_covariance,
        leads["event_time"].to_numpy(),
        cluster_counts,
    )
    individual_p_values = [
        float(
            cluster_t_inference(
                float(row.coefficient),
                float(row.standard_error),
                cluster_counts,
            )["p_value"]
        )
        for row in leads.itertuples()
    ]
    individual_rejections = int(
        sum(p_value < 0.05 for p_value in individual_p_values)
    )
    return {
        "joint_lead_test_name": "cluster_robust_joint_wald_all_leads",
        "joint_lead_count": int(len(leads)),
        "joint_lead_statistic": joint["statistic"],
        "joint_lead_df": joint["df"],
        "joint_lead_p_value": joint["p_value"],
        **psd,
        "joint_lead_p_value_interpretable": bool(
            psd["lead_covariance_positive_semidefinite"]
        ),
        "linear_pretrend_test_name": (
            "gls_linear_slope_through_reference"
        ),
        "linear_pretrend_coefficient": linear["coefficient"],
        "linear_pretrend_standard_error": linear["standard_error"],
        "linear_pretrend_p_value": linear["p_value"],
        "dynamic_diagnostic_name": (
            "individual_cluster_t_lead_inspection"
        ),
        "dynamic_pre_coefficients": int(len(leads)),
        "dynamic_pre_p_lt_005": individual_rejections,
        "dynamic_min_p_value": float(min(individual_p_values)),
        "pretrend_classification_name": (
            "preregistered_pass_warning_fail"
        ),
        "pretrend_status": classify_pretrend(
            float(joint["p_value"]),
            float(linear["p_value"]),
            individual_rejections,
        ),
        "non_rejection_is_proof": False,
    }


def _load_outcome_panel(specification: dict[str, Any]) -> pd.DataFrame:
    outcome = str(specification["outcome"])
    arm = str(specification["arm"])
    path = INDIVIDUAL_PANEL_PATH if arm == "A" else COD3_PANEL_PATH
    columns = [
        "ano",
        "trimestre_num",
        "cod3",
        "treated",
        outcome,
    ]
    if specification["weight_column"] is not None:
        columns.append(str(specification["weight_column"]))
    frame = pd.read_parquet(path, columns=columns)
    frame["cod3"] = frame["cod3"].astype("category")
    frame["event_time"] = (
        pd.to_numeric(frame["trimestre_num"], errors="raise").astype("int16")
        - EVENT_QUARTER_NUMBER
    ).astype("int16")
    return frame


def _prepare_event_sample(
    panel: pd.DataFrame,
    *,
    exclude_2020: bool,
) -> pd.DataFrame:
    data = (
        panel.loc[~panel["ano"].eq(2020)].copy()
        if exclude_2020
        else panel
    )
    observed_quarters = sorted(
        data["trimestre_num"].astype(int).unique().tolist()
    )
    expected_quarters = [
        quarter
        for quarter in range(1, 58)
        if quarter != EVENT_QUARTER_NUMBER
        and not (exclude_2020 and 33 <= quarter <= 36)
    ]
    if observed_quarters != expected_quarters:
        missing = sorted(set(expected_quarters) - set(observed_quarters))
        unexpected = sorted(set(observed_quarters) - set(expected_quarters))
        raise RuntimeError(
            "Quarterly event sample does not match the registered grid: "
            f"missing={missing}, unexpected={unexpected}"
        )
    return data


def _window_label(values: Sequence[int]) -> str:
    return f"{min(values)}_to_{max(values)}"


def _run_outcome_sample(
    panel: pd.DataFrame,
    specification: dict[str, Any],
    sample: dict[str, Any],
) -> dict[str, Any]:
    outcome = str(specification["outcome"])
    sample_name = str(sample["sample"])
    exclude_2020 = bool(sample["exclude_2020"])
    data = _prepare_event_sample(panel, exclude_2020=exclude_2020)
    expected_times = expected_coefficient_event_times(exclude_2020)
    lead_times = [value for value in expected_times if value < -1]
    model_id = f"pnadc_pretrend_{outcome}_{sample_name}"
    input_observations = int(len(data))
    if specification["arm"] == "A":
        model_input, source_observations = collapse_weighted_event_data(
            data,
            outcome=outcome,
            weight_column=str(specification["weight_column"]),
        )
        model, model_data, formula, cluster_counts = (
            fit_collapsed_weighted_event_model(
                model_input,
                outcome=outcome,
                source_observations=source_observations,
                model_id=model_id,
            )
        )
        complete_case_input = source_observations
        computational_rows = int(len(model_input))
        sum_of_weights = float(model_input["cell_weight"].sum())
    else:
        model, model_data, formula, cluster_counts = (
            fit_quarterly_event_model(
                data,
                outcome=outcome,
                estimator=str(specification["estimator"]),
                weight_column=None,
                model_id=model_id,
            )
        )
        complete_case_input = int(len(model_data))
        computational_rows = int(len(model_data))
        sum_of_weights = float("nan")
    diagnostics = run_model_diagnostics(
        model,
        expected_event_times=expected_times,
        lead_event_times=lead_times,
        cluster_counts=cluster_counts,
    )
    weight_column = specification["weight_column"]
    return {
        "specification_id": "quarterly_dynamic_exact_model",
        "model_id": model_id,
        "arm": specification["arm"],
        "outcome": outcome,
        "estimator": specification["estimator"],
        "sample": sample_name,
        "sample_window": "2012Q1--2026Q1",
        "exclude_2020": exclude_2020,
        "excluded_transition_period": "2022Q4",
        "reference_period": "2022Q3",
        "reference_event_time": REFERENCE_EVENT_TIME,
        "event_window": "-43_to_13_with_0_excluded",
        "lead_event_times": json.dumps(lead_times),
        "joint_lead_window": _window_label(lead_times),
        "formula": formula,
        "fixed_effects": " + ".join(FIXED_EFFECTS),
        "cluster_variables": " + ".join(CLUSTER_VARIABLES),
        "weight_column": weight_column or "",
        "sum_of_weights": sum_of_weights,
        "n_obs": int(model._N),
        "input_observations": input_observations,
        "complete_case_input": complete_case_input,
        "computational_sufficient_statistic_rows": computational_rows,
        "individual_score_equations_preserved": (
            specification["arm"] == "A"
        ),
        "observations_dropped_missing": int(
            input_observations - complete_case_input
        ),
        "observations_dropped_estimator": int(
            complete_case_input - int(model._N)
        ),
        "minimum_clusters": int(min(cluster_counts.values())),
        "cluster_counts": json.dumps(cluster_counts, sort_keys=True),
        **diagnostics,
        "post_event_coefficients_published": False,
    }


def attach_timing_readings(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach the preregistered two-sample timing reading by outcome."""
    result = frame.copy()
    readings: dict[str, str] = {}
    for outcome, group in result.groupby("outcome", sort=False):
        statuses = group.set_index("sample")["pretrend_status"].to_dict()
        if set(statuses) != {"full", "without_2020"}:
            raise RuntimeError(
                f"Pretrend samples are incomplete for {outcome}"
            )
        readings[str(outcome)] = derive_pretrend_timing(
            str(statuses["full"]),
            str(statuses["without_2020"]),
        )
    result["pretrend_timing"] = result["outcome"].map(readings)
    return result


def validate_pretrend_output(frame: pd.DataFrame) -> dict[str, Any]:
    """Validate the complete P9 diagnostic grid."""
    expected_outcomes = {
        str(specification["outcome"]) for specification in OUTCOME_SPECS
    }
    expected_samples = {
        str(specification["sample"]) for specification in SAMPLE_SPECS
    }
    if len(frame) != len(expected_outcomes) * len(expected_samples):
        raise RuntimeError("P9 must contain exactly 12 diagnostic rows")
    if set(frame["outcome"]) != expected_outcomes:
        raise RuntimeError("P9 outcome grid is incomplete")
    if set(frame["sample"]) != expected_samples:
        raise RuntimeError("P9 sample grid is incomplete")
    if frame.duplicated(["outcome", "sample"]).any():
        raise RuntimeError("P9 contains duplicate outcome-sample rows")
    if not frame["pretrend_status"].isin(
        ["pass", "warning", "fail"]
    ).all():
        raise RuntimeError("P9 contains an invalid pretrend classification")
    if frame["post_event_coefficients_published"].astype(bool).any():
        raise RuntimeError("P9 must not publish post-event coefficients")
    if frame["non_rejection_is_proof"].astype(bool).any():
        raise RuntimeError("P9 cannot treat non-rejection as proof")
    return {
        "rows": int(len(frame)),
        "outcomes": int(frame["outcome"].nunique()),
        "samples": int(frame["sample"].nunique()),
        "classification_counts": {
            str(key): int(value)
            for key, value in frame["pretrend_status"]
            .value_counts()
            .sort_index()
            .items()
        },
        "non_psd_rows": int(
            (~frame["lead_covariance_positive_semidefinite"].astype(bool)).sum()
        ),
    }


def render_pretrend_report(frame: pd.DataFrame) -> str:
    """Render the P9 diagnostic without any post-treatment interpretation."""
    full = frame.loc[frame["sample"].eq("full")].set_index("outcome")
    without = frame.loc[
        frame["sample"].eq("without_2020")
    ].set_index("outcome")
    lines = [
        "# PNADc quarterly pretrend diagnostics",
        "",
        "## Contract",
        "",
        "The diagnostic uses the exact estimator, fixed effects, cluster, weights, and outcome-specific "
        "complete-case sample corresponding to each registered result. The window is "
        "2012Q1--2026Q1; 2022Q4 is excluded, 2022Q3 is the omitted reference, and 2023Q1 begins the "
        "post period. The complete sample and the sample excluding 2020 are reported side by side.",
        "",
        "The three diagnostics are the joint Wald test over all leads, the frozen GLS linear slope, "
        "and individual lead inspection under shared cluster-t inference. A non-significant "
        "diagnostic is not proof of parallel trends. A joint p-value whose lead covariance is not "
        "positive semidefinite is retained but is not interpreted as approval.",
        "",
        "## Results",
        "",
        "| Outcome | Full sample | Without 2020 | Timing diagnostic | Full joint p | Without-2020 joint p |",
        "|---|---|---|---|---:|---:|",
    ]
    for specification in OUTCOME_SPECS:
        outcome = str(specification["outcome"])
        full_row = full.loc[outcome]
        without_row = without.loc[outcome]
        lines.append(
            f"| `{outcome}` | `{full_row['pretrend_status']}` | "
            f"`{without_row['pretrend_status']}` | "
            f"`{full_row['pretrend_timing']}` | "
            f"{float(full_row['joint_lead_p_value']):.6g} | "
            f"{float(without_row['joint_lead_p_value']):.6g} |"
        )
    lines.extend(
        [
            "",
            "## Section 5.1 reading",
            "",
            "These rows determine whether the exposed--control divergence is persistent before the event, "
            "concentrated around the 2020 collection disruption, unstable to its exclusion, or not detected "
            "by the registered diagnostics. They govern the permissible reading of the limitation stated in "
            "Section 5.1; they do not establish a treatment effect.",
            "",
            "The design observes formal--informal composition, not individual worker transitions. No "
            "post-event dynamic coefficient is published in this diagnostic.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_part1_gate(
    status_path: Path = PART1_STATUS_PATH,
    individual_panel_path: Path = INDIVIDUAL_PANEL_PATH,
    stock_panel_path: Path = COD3_PANEL_PATH,
) -> dict[str, Any]:
    """Bind the frozen P-B1 authorization gate to the exact input panels."""
    if not status_path.is_file():
        raise FileNotFoundError("P-B1 status is missing")
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("gate") != "P-B1" or status.get("gate_status") != "open":
        raise RuntimeError("P-B1 is not open")
    if status.get("treatment_coefficients_computed") is not False:
        raise RuntimeError(
            "P-B1 contains an invalid treatment-computation state"
        )

    expected_individual = str(
        status.get("individual_panel", {}).get("sha256", "")
    )
    expected_stock = str(
        status.get("stock_panel", {}).get("sha256", "")
    )
    if sha256_file(individual_panel_path) != expected_individual:
        raise RuntimeError("P-B1 individual panel hash does not match")
    if sha256_file(stock_panel_path) != expected_stock:
        raise RuntimeError("P-B1 stock panel hash does not match")
    return status


def run_p9() -> dict[str, Any]:
    """Execute P9 and publish the complete two-sample diagnostic grid."""
    validate_part1_gate()

    rows: list[dict[str, Any]] = []
    for specification in OUTCOME_SPECS:
        panel = _load_outcome_panel(specification)
        for sample in SAMPLE_SPECS:
            rows.append(
                _run_outcome_sample(panel, specification, sample)
            )
        del panel
        gc.collect()
    diagnostics = attach_timing_readings(pd.DataFrame(rows))
    validation = validate_pretrend_output(diagnostics)
    atomic_csv(diagnostics, PRETRENDS_PATH)
    atomic_text(render_pretrend_report(diagnostics), PRETRENDS_REPORT_PATH)
    status = {
        "status": "pass",
        "task": "P9",
        **validation,
        "full_sample_leads": 42,
        "without_2020_leads": 38,
        "individual_panel_sha256": sha256_file(INDIVIDUAL_PANEL_PATH),
        "cod3_panel_sha256": sha256_file(COD3_PANEL_PATH),
        "post_event_coefficients_published": False,
        "treatment_coefficients_computed": False,
    }
    atomic_json(status, PRETRENDS_STATUS_PATH)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run quarterly PNADc pretrend diagnostics.",
    )
    return parser.parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(run_p9(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
