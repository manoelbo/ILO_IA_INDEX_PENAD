#!/usr/bin/env python3
"""Run exact-model pretrend diagnostics for the balanced event studies."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, NamedTuple

import numpy as np
import pandas as pd

from covariance_diagnostics import (
    RANK_DEFICIENT_STATUS,
    lead_covariance_diagnostics,
)
from estimators import cluster_t_inference
from event_study import (
    REFERENCE_EVENT_TIME,
    build_event_formula,
    parse_event_time_coefficient,
    prepare_balanced_event_data,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_EVENT_SUPPORT = (
    PACKAGE_ROOT / "results" / "models" / "event_study_support.json"
)
DEFAULT_DIAGNOSTICS = (
    PACKAGE_ROOT / "results" / "diagnostics" / "pretrend_diagnostics.csv"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "pretrend_diagnostics_support.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "PRETREND_DIAGNOSTICS.md"
)
DEFAULT_HONEST_COEFFICIENTS = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "honest_did_event_coefficients.csv"
)
DEFAULT_HONEST_VCOV = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "honest_did_event_vcov_long.csv"
)
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)


class HonestDidModel(NamedTuple):
    outcome: str
    estimator: str
    event_times: tuple[int, ...]
    coefficients: np.ndarray
    covariance: np.ndarray


def classify_pretrend(
    joint_p_value: float,
    linear_p_value: float,
    n_individual_p_lt_005: int,
) -> str:
    if (
        joint_p_value < 0.05
        or linear_p_value < 0.05
        or n_individual_p_lt_005 >= 2
    ):
        return "fail"
    if (
        joint_p_value > 0.10
        and linear_p_value > 0.10
        and n_individual_p_lt_005 == 0
    ):
        return "pass"
    return "warning"


def gls_pretrend_slope(
    coefficients: np.ndarray,
    covariance: np.ndarray,
    event_times: np.ndarray,
    cluster_counts: dict[str, int],
) -> dict[str, float | int]:
    coefficients = np.asarray(coefficients, dtype=float)
    covariance = np.asarray(covariance, dtype=float)
    event_times = np.asarray(event_times, dtype=float)
    if coefficients.ndim != 1:
        raise ValueError("Lead coefficients must be one-dimensional")
    if covariance.shape != (len(coefficients), len(coefficients)):
        raise ValueError("Lead covariance matrix has the wrong shape")
    if event_times.shape != coefficients.shape:
        raise ValueError("Event times and coefficients must align")
    design = event_times - REFERENCE_EVENT_TIME
    precision = np.linalg.pinv(covariance)
    denominator = float(design @ precision @ design)
    if denominator <= 0:
        raise RuntimeError("GLS pretrend slope is not identified")
    coefficient = float(
        design @ precision @ coefficients / denominator
    )
    standard_error = math.sqrt(1.0 / denominator)
    inference = cluster_t_inference(
        coefficient,
        standard_error,
        cluster_counts,
    )
    return {
        "coefficient": coefficient,
        "standard_error": standard_error,
        **inference,
    }


def _fit_event_model(
    panel: pd.DataFrame,
    outcome: str,
    estimator: str,
) -> tuple[Any, pd.DataFrame, str]:
    import pyfixest as pf

    data = panel.loc[panel["included_main"].eq(True)].copy()
    data = prepare_balanced_event_data(data)
    model_data = data.dropna(
        subset=[
            outcome,
            "event_time",
            "treated_main",
            "cbo_4d",
            "periodo",
        ]
    ).copy()
    formula = build_event_formula(outcome)
    if estimator == "ppml":
        model = pf.fepois(
            formula,
            data=model_data,
            vcov={"CRV1": "cbo_4d"},
            separation_check=["fe"],
        )
        if not bool(getattr(model, "_convergence", False)):
            raise RuntimeError(
                f"Exact-model PPML did not converge: {outcome}"
            )
    elif estimator == "ols":
        model = pf.feols(
            formula,
            data=model_data,
            vcov={"CRV1": "cbo_4d"},
        )
    else:
        raise ValueError(f"Unsupported estimator: {estimator}")
    return model, model_data, formula


def _event_parameter_frame(
    model: Any,
) -> pd.DataFrame:
    names = [str(name) for name in model.coef().index]
    records = []
    for position, name in enumerate(names):
        try:
            event_time = parse_event_time_coefficient(name)
        except ValueError:
            continue
        records.append(
            {
                "position": position,
                "term": name,
                "event_time": event_time,
                "coefficient": float(model.coef().iloc[position]),
                "standard_error": float(model.se().iloc[position]),
            }
        )
    frame = pd.DataFrame(records).sort_values("event_time")
    expected = [
        value for value in range(-23, 24)
        if value != REFERENCE_EVENT_TIME
    ]
    if frame["event_time"].astype(int).tolist() != expected:
        raise RuntimeError("Exact event-study parameter grid is incomplete")
    return frame.reset_index(drop=True)


def _joint_lead_test(
    model: Any,
    positions: np.ndarray,
) -> dict[str, float | int]:
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


def build_honest_did_exports(
    models: list[HonestDidModel],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefficient_rows: list[dict[str, Any]] = []
    covariance_rows: list[dict[str, Any]] = []
    for model in models:
        if model.estimator != "ols":
            continue
        for position, (event_time, coefficient) in enumerate(
            zip(
                model.event_times,
                model.coefficients,
                strict=True,
            )
        ):
            coefficient_rows.append(
                {
                    "outcome": model.outcome,
                    "estimator": model.estimator,
                    "position": position,
                    "event_time": event_time,
                    "coefficient": float(coefficient),
                    "is_pre": event_time < REFERENCE_EVENT_TIME,
                }
            )
        for row_position, row_event_time in enumerate(model.event_times):
            for column_position, column_event_time in enumerate(
                model.event_times
            ):
                covariance_rows.append(
                    {
                        "outcome": model.outcome,
                        "row_position": row_position,
                        "column_position": column_position,
                        "row_event_time": row_event_time,
                        "column_event_time": column_event_time,
                        "covariance": float(
                            model.covariance[
                                row_position,
                                column_position,
                            ]
                        ),
                    }
                )
    return (
        pd.DataFrame(coefficient_rows),
        pd.DataFrame(covariance_rows),
    )


def run_pretrend_diagnostics(
    panel: pd.DataFrame,
    expected_support: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
]:
    rows: list[dict[str, Any]] = []
    honest_models: list[HonestDidModel] = []
    for outcome, estimator in OUTCOMES:
        model, model_data, formula = _fit_event_model(
            panel,
            outcome,
            estimator,
        )
        parameters = _event_parameter_frame(model)
        covariance = np.asarray(model._vcov, dtype=float)
        event_positions = parameters["position"].astype(int).to_numpy()
        event_covariance = covariance[
            np.ix_(event_positions, event_positions)
        ]
        event_coefficients = parameters["coefficient"].to_numpy()
        event_times = parameters["event_time"].astype(int).to_numpy()
        leads = parameters.loc[
            parameters["event_time"].lt(REFERENCE_EVENT_TIME)
        ].copy()
        lead_positions_in_event = np.flatnonzero(
            event_times < REFERENCE_EVENT_TIME
        )
        lead_covariance = event_covariance[
            np.ix_(lead_positions_in_event, lead_positions_in_event)
        ]
        cluster_counts = {
            "cbo_4d": int(model._data["cbo_4d"].nunique())
        }
        covariance_diagnostics = lead_covariance_diagnostics(
            lead_covariance
        )
        covariance_is_full_rank = bool(
            covariance_diagnostics["lead_covariance_full_rank"]
        )
        if covariance_is_full_rank:
            joint = _joint_lead_test(
                model,
                leads["position"].astype(int).to_numpy(),
            )
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
                "df": int(len(leads)),
            }
            linear = {
                "coefficient": float("nan"),
                "standard_error": float("nan"),
                "p_value": float("nan"),
            }
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
        n_individual = sum(
            p_value < 0.05 for p_value in individual_p_values
        )
        n_obs = int(model._N)
        n_clusters = cluster_counts["cbo_4d"]
        expected = expected_support["models"][outcome]
        n_matches = n_obs == int(expected["n_obs"])
        clusters_match = n_clusters == int(expected["n_clusters"])
        if not n_matches or not clusters_match:
            raise RuntimeError(
                "Pretrend model does not match the reported event-study "
                f"sample for {outcome}"
            )
        rows.append(
            {
                "outcome": outcome,
                "estimator": estimator,
                "model_name": "balanced_dynamic_exact_model",
                "formula": formula,
                "event_window": "-23_to_23",
                "reference_event_time": REFERENCE_EVENT_TIME,
                "n_obs": n_obs,
                "n_clusters": n_clusters,
                "reported_event_study_n_obs": int(expected["n_obs"]),
                "reported_event_study_n_clusters": int(
                    expected["n_clusters"]
                ),
                "n_matches_reported": n_matches,
                "clusters_match_reported": clusters_match,
                "joint_lead_test_name": (
                    "cluster_robust_joint_wald_all_leads"
                ),
                "joint_lead_window": "-23_to_-2",
                "joint_lead_count": int(len(leads)),
                "joint_lead_statistic": joint["statistic"],
                "joint_lead_df": joint["df"],
                "joint_lead_p_value": joint["p_value"],
                **covariance_diagnostics,
                "linear_pretrend_test_name": (
                    "gls_linear_slope_through_reference"
                ),
                "linear_pretrend_coefficient": linear["coefficient"],
                "linear_pretrend_standard_error": linear[
                    "standard_error"
                ],
                "linear_pretrend_p_value": linear["p_value"],
                "dynamic_diagnostic_name": (
                    "individual_cluster_t_lead_inspection"
                ),
                "dynamic_pre_coefficients": int(len(leads)),
                "dynamic_pre_p_lt_005": int(n_individual),
                "dynamic_min_p_value": float(min(individual_p_values)),
                "pretrend_classification_name": (
                    "preregistered_pass_warning_fail"
                ),
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
                "complete_case_input": int(len(model_data)),
            }
        )
        honest_models.append(
            HonestDidModel(
                outcome=outcome,
                estimator=estimator,
                event_times=tuple(event_times.tolist()),
                coefficients=event_coefficients,
                covariance=event_covariance,
            )
        )
    diagnostics = pd.DataFrame(rows)
    honest_coefficients, honest_vcov = build_honest_did_exports(
        honest_models
    )
    support = {
        "outcome_count": int(len(diagnostics)),
        "all_n_match_reported_event_study": bool(
            diagnostics["n_matches_reported"].all()
        ),
        "all_cluster_counts_match_reported_event_study": bool(
            diagnostics["clusters_match_reported"].all()
        ),
        "joint_lead_window": "-23_to_-2",
        "joint_lead_count": 22,
        "reference_event_time": REFERENCE_EVENT_TIME,
        "diagnostics_named_distinctly": [
            "cluster_robust_joint_wald_all_leads",
            "gls_linear_slope_through_reference",
            "individual_cluster_t_lead_inspection",
        ],
        "classification_counts": {
            str(key): int(value)
            for key, value in diagnostics[
                "pretrend_status"
            ].value_counts().sort_index().items()
        },
        "non_rejection_is_proof": False,
        "honest_did_linear_outcomes": sorted(
            honest_coefficients["outcome"].unique().tolist()
        ),
    }
    return diagnostics, support, honest_coefficients, honest_vcov


def render_report(diagnostics: pd.DataFrame) -> str:
    lines = [
        "# Exact-model pretrend diagnostics",
        "",
        "All diagnostics use the exact balanced dynamic model, sample, "
        "fixed effects, reference month, and CBO4 clustering reported in "
        "the event-study output.",
        "",
        "| Outcome | Estimator | Joint-lead p | Linear-slope p | "
        "Individual leads p<0.05 | Status | N | Clusters |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in diagnostics.itertuples():
        lines.append(
            f"| {row.outcome} | {row.estimator} | "
            f"{row.joint_lead_p_value:.6g} | "
            f"{row.linear_pretrend_p_value:.6g} | "
            f"{row.dynamic_pre_p_lt_005} | "
            f"{row.pretrend_status} | {row.n_obs:,} | "
            f"{row.n_clusters} |"
        )
    lines.extend(
        [
            "",
            "The three named diagnostics are not interchangeable: the "
            "joint Wald test evaluates all leads simultaneously, the GLS "
            "linear test evaluates a single differential slope, and the "
            "dynamic inspection counts individually unusual leads.",
            "",
            "A non-significant pretrend diagnostic is not proof of "
            "parallel trends. Failed and warning results remain visible "
            "and require appropriately non-causal narrative language.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run exact-model balanced-event pretrend diagnostics."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument(
        "--event-support",
        type=Path,
        default=DEFAULT_EVENT_SUPPORT,
    )
    parser.add_argument(
        "--diagnostics",
        type=Path,
        default=DEFAULT_DIAGNOSTICS,
    )
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--honest-coefficients",
        type=Path,
        default=DEFAULT_HONEST_COEFFICIENTS,
    )
    parser.add_argument(
        "--honest-vcov",
        type=Path,
        default=DEFAULT_HONEST_VCOV,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected_support = json.loads(
        args.event_support.read_text(encoding="utf-8")
    )
    diagnostics, support, honest_coefficients, honest_vcov = (
        run_pretrend_diagnostics(
            pd.read_parquet(args.panel),
            expected_support,
        )
    )
    _atomic_csv(diagnostics, args.diagnostics)
    _atomic_json(support, args.support)
    _atomic_text(render_report(diagnostics), args.report)
    _atomic_csv(honest_coefficients, args.honest_coefficients)
    _atomic_csv(honest_vcov, args.honest_vcov)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
