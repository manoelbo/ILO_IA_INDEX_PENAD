#!/usr/bin/env python3
"""Reusable engine for the three named V2 pretrend diagnostics.

The exact-model diagnostics in `pretrends.py` are frozen and run on a single
specification. Phase 8A applies the same three tests to further specifications
that were already estimated but never diagnosed. This module holds the shared
machinery so every Phase 8A diagnostic uses one implementation of the joint
Wald test, the GLS linear slope, and the individual lead inspection.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from estimators import cluster_t_inference, student_t_ppf
from covariance_diagnostics import (
    RANK_DEFICIENT_STATUS,
    lead_covariance_diagnostics,
)
from event_study import (
    EVENT_PERIOD,
    REFERENCE_EVENT_TIME,
    event_time_from_period,
)
from pretrends import classify_pretrend, gls_pretrend_slope


JOINT_TEST_NAME = "cluster_robust_joint_wald_all_leads"
LINEAR_TEST_NAME = "gls_linear_slope_through_reference"
DYNAMIC_TEST_NAME = "individual_cluster_t_lead_inspection"
CLASSIFICATION_NAME = "preregistered_pass_warning_fail"


def event_window_label(minimum: int, maximum: int) -> str:
    return f"{minimum}_to_{maximum}"


def add_event_time(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["event_time"] = event_time_from_period(data["periodo_num"])
    return data


def restrict_event_window(
    frame: pd.DataFrame,
    minimum: int,
    maximum: int,
) -> pd.DataFrame:
    data = frame.loc[
        frame["event_time"].between(minimum, maximum)
    ].copy()
    observed = sorted(data["event_time"].unique().tolist())
    expected = list(range(minimum, maximum + 1))
    if observed != expected:
        missing = sorted(set(expected) - set(observed))
        raise RuntimeError(
            f"Event-time support has a hole: missing {missing}"
        )
    return data


def build_interaction_formula(
    outcome: str,
    interaction: str,
    fixed_effects: Sequence[str],
) -> str:
    fixed = " + ".join(fixed_effects)
    return (
        f"{outcome} ~ i(event_time, {interaction}, ref="
        f"{REFERENCE_EVENT_TIME}) | {fixed}"
    )


def parse_event_time(name: str, interaction: str) -> int:
    match = re.search(
        rf"\[T?\.?(-?\d+)\]:{re.escape(interaction)}$",
        name,
    )
    if not match:
        raise ValueError(f"Not an event-time coefficient: {name}")
    return int(match.group(1))


def event_parameter_frame(
    model: Any,
    interaction: str,
    *,
    expected_event_times: Sequence[int] | None = None,
) -> pd.DataFrame:
    coefficients = model.coef()
    standard_errors = model.se()
    records: list[dict[str, Any]] = []
    for position, name in enumerate(str(item) for item in coefficients.index):
        try:
            event_time = parse_event_time(name, interaction)
        except ValueError:
            continue
        records.append(
            {
                "position": position,
                "term": name,
                "event_time": event_time,
                "coefficient": float(coefficients.iloc[position]),
                "standard_error": float(standard_errors.iloc[position]),
            }
        )
    if not records:
        raise RuntimeError(
            f"No event-time coefficients matched interaction {interaction}"
        )
    frame = pd.DataFrame(records).sort_values("event_time")
    if expected_event_times is not None:
        observed = frame["event_time"].astype(int).tolist()
        if observed != list(expected_event_times):
            raise RuntimeError(
                "Estimated event-time parameter grid is incomplete"
            )
    return frame.reset_index(drop=True)


def registered_event_coefficient_frame(
    model: Any,
    interaction: str,
    *,
    model_id: str,
    outcome: str,
    estimator: str,
    sample_id: str,
    cluster_counts: dict[str, int],
    expected_event_times: Sequence[int],
) -> pd.DataFrame:
    """Return every event coefficient plus the omitted reference row."""

    parameters = event_parameter_frame(
        model,
        interaction,
        expected_event_times=expected_event_times,
    )
    rows = parameters[
        ["term", "event_time", "coefficient", "standard_error"]
    ].copy()
    rows["is_reference"] = False
    rows = pd.concat(
        [
            rows,
            pd.DataFrame(
                [
                    {
                        "term": "reference_event_time",
                        "event_time": REFERENCE_EVENT_TIME,
                        "coefficient": 0.0,
                        "standard_error": 0.0,
                        "is_reference": True,
                    }
                ]
            ),
        ],
        ignore_index=True,
    ).sort_values("event_time")
    rows.insert(0, "model_id", model_id)
    rows.insert(1, "outcome", outcome)
    rows.insert(2, "estimator", estimator)
    rows["n_obs"] = int(model._N)
    rows["minimum_clusters"] = int(min(cluster_counts.values()))
    rows["sample_id"] = sample_id
    rows["status"] = "estimated"
    rows["reference_event_time"] = REFERENCE_EVENT_TIME
    return rows.reset_index(drop=True)


def joint_lead_test(
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


def minimum_detectable_effect(
    standard_error: float,
    cluster_df: int,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """Two-sided MDE at the requested power, using the cluster-t reference.

    The usual normal-approximation formula is applied with Student-t critical
    values so that the reported effect uses the same reference distribution as
    the coefficient's own inference.
    """

    if not np.isfinite(standard_error) or standard_error <= 0:
        return float("nan")
    critical = student_t_ppf(1 - alpha / 2, cluster_df)
    power_quantile = student_t_ppf(power, cluster_df)
    return float((critical + power_quantile) * standard_error)


def diagnose_event_model(
    model: Any,
    *,
    interaction: str,
    cluster_counts: dict[str, int],
    lead_minimum: int,
    lead_maximum: int = REFERENCE_EVENT_TIME - 1,
    expected_event_times: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Run the three named diagnostics on one fitted event-study model."""

    parameters = event_parameter_frame(
        model,
        interaction,
        expected_event_times=expected_event_times,
    )
    leads = parameters.loc[
        parameters["event_time"].between(lead_minimum, lead_maximum)
    ].copy()
    expected_leads = [
        value
        for value in range(lead_minimum, lead_maximum + 1)
        if value != REFERENCE_EVENT_TIME
    ]
    if leads["event_time"].astype(int).tolist() != expected_leads:
        raise RuntimeError(
            "Lead window is incomplete for the requested diagnostic"
        )
    covariance = np.asarray(model._vcov, dtype=float)
    lead_positions = leads["position"].astype(int).to_numpy()
    lead_covariance = covariance[np.ix_(lead_positions, lead_positions)]
    covariance_diagnostics = lead_covariance_diagnostics(lead_covariance)
    covariance_is_full_rank = bool(
        covariance_diagnostics["lead_covariance_full_rank"]
    )
    if covariance_is_full_rank:
        joint = joint_lead_test(model, lead_positions)
        linear = gls_pretrend_slope(
            leads["coefficient"].to_numpy(),
            lead_covariance,
            leads["event_time"].to_numpy(),
            cluster_counts,
        )
    else:
        joint = {
            "statistic": float("nan"),
            "p_value": float("nan"),
            "df": int(len(lead_positions)),
        }
        linear = {
            "coefficient": float("nan"),
            "standard_error": float("nan"),
            "p_value": float("nan"),
        }
    individual = [
        float(
            cluster_t_inference(
                float(record.coefficient),
                float(record.standard_error),
                cluster_counts,
            )["p_value"]
        )
        for record in leads.itertuples()
    ]
    n_individual = int(sum(value < 0.05 for value in individual))
    return {
        "joint_lead_test_name": JOINT_TEST_NAME,
        "joint_lead_window": event_window_label(lead_minimum, lead_maximum),
        "joint_lead_count": int(len(leads)),
        "joint_lead_statistic": joint["statistic"],
        "joint_lead_df": joint["df"],
        "joint_lead_p_value": joint["p_value"],
        **covariance_diagnostics,
        "linear_pretrend_test_name": LINEAR_TEST_NAME,
        "linear_pretrend_coefficient": linear["coefficient"],
        "linear_pretrend_standard_error": linear["standard_error"],
        "linear_pretrend_p_value": linear["p_value"],
        "dynamic_diagnostic_name": DYNAMIC_TEST_NAME,
        "dynamic_pre_coefficients": int(len(leads)),
        "dynamic_pre_p_lt_005": n_individual,
        "dynamic_min_p_value": float(min(individual)),
        "pretrend_classification_name": CLASSIFICATION_NAME,
        "pretrend_status": (
            classify_pretrend(
                float(joint["p_value"]),
                float(linear["p_value"]),
                n_individual,
            )
            if covariance_is_full_rank
            else RANK_DEFICIENT_STATUS
        ),
        "non_rejection_is_proof": False,
        "reference_event_time": REFERENCE_EVENT_TIME,
        "reference_period": EVENT_PERIOD.strftime("%Y-%m"),
    }


def fit_event_model(
    data: pd.DataFrame,
    *,
    outcome: str,
    estimator: str,
    interaction: str,
    fixed_effects: Sequence[str],
    cluster_variables: Sequence[str],
    model_id: str,
) -> tuple[Any, pd.DataFrame, str, dict[str, int]]:
    import pyfixest as pf

    required = [outcome, "event_time", interaction, *cluster_variables]
    for fixed_effect in fixed_effects:
        required.extend(fixed_effect.split("^"))
    required = list(dict.fromkeys(required))
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Model data is missing columns: {missing}")
    model_data = data.dropna(subset=required).copy()
    if model_data.empty:
        raise RuntimeError(f"No complete cases for model {model_id}")
    formula = build_interaction_formula(outcome, interaction, fixed_effects)
    vcov = {"CRV1": " + ".join(cluster_variables)}
    if estimator == "ppml":
        model = pf.fepois(
            formula,
            data=model_data,
            vcov=vcov,
            separation_check=["fe"],
        )
        if not bool(getattr(model, "_convergence", False)):
            raise RuntimeError(f"Event-study PPML did not converge: {model_id}")
    elif estimator == "ols":
        model = pf.feols(formula, data=model_data, vcov=vcov)
    else:
        raise ValueError(f"Unsupported estimator: {estimator}")
    used = getattr(model, "_data", model_data)
    cluster_counts = {
        variable: int(used[variable].nunique())
        for variable in cluster_variables
    }
    return model, model_data, formula, cluster_counts


def diagnostic_row(
    *,
    model: Any,
    model_data: pd.DataFrame,
    formula: str,
    cluster_counts: dict[str, int],
    interaction: str,
    lead_minimum: int,
    event_minimum: int,
    event_maximum: int,
    expected_event_times: Sequence[int] | None = None,
    **labels: Any,
) -> dict[str, Any]:
    diagnostics = diagnose_event_model(
        model,
        interaction=interaction,
        cluster_counts=cluster_counts,
        lead_minimum=lead_minimum,
        expected_event_times=expected_event_times,
    )
    return {
        **labels,
        "interaction": interaction,
        "formula": formula,
        "event_window": event_window_label(event_minimum, event_maximum),
        "n_obs": int(model._N),
        "cluster_counts": json.dumps(cluster_counts, sort_keys=True),
        "minimum_clusters": int(min(cluster_counts.values())),
        "complete_case_input": int(len(model_data)),
        **diagnostics,
    }


DIAGNOSTIC_COLUMN_ORDER = (
    "specification_id",
    "specification_label",
    "outcome",
    "estimator",
    "sample",
    "event_window",
    "joint_lead_window",
    "joint_lead_count",
    "joint_lead_statistic",
    "joint_lead_df",
    "joint_lead_p_value",
    "lead_covariance_positive_semidefinite",
    "lead_covariance_min_eigenvalue",
    "lead_covariance_dimension",
    "lead_covariance_rank",
    "lead_covariance_full_rank",
    "lead_covariance_condition_number",
    "lead_covariance_rank_tolerance",
    "lead_covariance_psd_tolerance",
    "linear_pretrend_coefficient",
    "linear_pretrend_standard_error",
    "linear_pretrend_p_value",
    "dynamic_pre_coefficients",
    "dynamic_pre_p_lt_005",
    "dynamic_min_p_value",
    "pretrend_status",
    "n_obs",
    "minimum_clusters",
    "cluster_counts",
    "interaction",
    "formula",
    "reference_event_time",
    "reference_period",
    "joint_lead_test_name",
    "linear_pretrend_test_name",
    "dynamic_diagnostic_name",
    "pretrend_classification_name",
    "non_rejection_is_proof",
    "complete_case_input",
)


def order_diagnostic_columns(frame: pd.DataFrame) -> pd.DataFrame:
    leading = [
        column
        for column in DIAGNOSTIC_COLUMN_ORDER
        if column in frame.columns
    ]
    trailing = [column for column in frame.columns if column not in leading]
    return frame[[*leading, *trailing]]


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)
