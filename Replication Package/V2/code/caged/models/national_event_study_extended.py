#!/usr/bin/env python3
"""Persist the already-diagnosed extended national event-study coefficients."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent
if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

from event_study import REFERENCE_EVENT_TIME
from group_event_studies import (
    complete_coefficient_grid,
    expected_estimated_event_times,
)
from pretrend_engine import (
    add_event_time,
    atomic_csv,
    atomic_json,
    atomic_text,
    event_parameter_frame,
    fit_event_model,
    restrict_event_window,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
OUTPUT_DIR = PACKAGE_ROOT / "results" / "models"
DEFAULT_COEFFICIENTS = (
    OUTPUT_DIR / "national_event_study_extended_coefficients.csv"
)
DEFAULT_PRE_MEANS = (
    OUTPUT_DIR / "national_event_study_extended_pre_means.csv"
)
DEFAULT_MODELS = OUTPUT_DIR / "national_event_study_extended_models.csv"
DEFAULT_SUPPORT = (
    OUTPUT_DIR / "national_event_study_extended_support.json"
)
DEFAULT_REPORT = OUTPUT_DIR / "NATIONAL_EVENT_STUDY_EXTENDED.md"

WINDOW = (-23, 41)
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)
FIXED_EFFECTS = ("cbo_4d", "periodo")
CLUSTERS = ("cbo_4d",)


def load_sample(path: Path) -> pd.DataFrame:
    columns = [
        "cbo_4d",
        "periodo_num",
        "periodo",
        "included_main",
        "treated_main",
        *[outcome for outcome, _ in OUTCOMES],
    ]
    panel = pd.read_parquet(path, columns=columns)
    sample = panel.loc[panel["included_main"].eq(True)].copy()
    sample = add_event_time(sample)
    sample = restrict_event_window(sample, *WINDOW)
    sample["treated_main"] = pd.to_numeric(
        sample["treated_main"],
        errors="raise",
    )
    return sample


def run_models(
    sample: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coefficient_frames: list[pd.DataFrame] = []
    pre_means: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    for outcome, estimator in OUTCOMES:
        model_id = f"national_extended__{outcome}"
        labels = {
            "model_id": model_id,
            "outcome": outcome,
            "estimator": estimator,
            "event_window": "-23_to_41",
            "reference_event_time": REFERENCE_EVENT_TIME,
            "reference_period": "2022-11",
            "is_causal_effect": False,
        }
        try:
            model, model_data, formula, cluster_counts = fit_event_model(
                sample,
                outcome=outcome,
                estimator=estimator,
                interaction="treated_main",
                fixed_effects=FIXED_EFFECTS,
                cluster_variables=CLUSTERS,
                model_id=model_id,
            )
            minimum_clusters = int(min(cluster_counts.values()))
            parameters = event_parameter_frame(
                model,
                "treated_main",
                expected_event_times=expected_estimated_event_times(),
            )
            complete = complete_coefficient_grid(
                parameters,
                minimum_clusters=minimum_clusters,
            )
            for key, value in labels.items():
                complete[key] = value
            complete["formula"] = formula
            complete["n_obs"] = int(model._N)
            complete["minimum_clusters"] = minimum_clusters
            coefficient_frames.append(complete)
            pre_mean = float(complete["pre_coefficient_mean"].iloc[0])
            pre_means.append(
                {
                    **labels,
                    "pre_window": "-23_to_-2",
                    "pre_coefficient_count": 22,
                    "pre_coefficient_mean": pre_mean,
                }
            )
            model_rows.append(
                {
                    **labels,
                    "status": "estimated",
                    "converged": True,
                    "error": "",
                    "formula": formula,
                    "n_obs": int(model._N),
                    "complete_case_input": int(len(model_data)),
                    "minimum_clusters": minimum_clusters,
                    "coefficient_rows": int(len(complete)),
                    "pre_coefficient_mean": pre_mean,
                }
            )
        except Exception as exception:  # noqa: BLE001
            model_rows.append(
                {
                    **labels,
                    "status": "failed_estimation",
                    "converged": False,
                    "error": str(exception)[:800],
                    "formula": "",
                    "n_obs": np.nan,
                    "complete_case_input": np.nan,
                    "minimum_clusters": np.nan,
                    "coefficient_rows": 0,
                    "pre_coefficient_mean": np.nan,
                }
            )
        print(
            f"[national-extended] {outcome} "
            f"{model_rows[-1]['status']}",
            flush=True,
        )
    coefficients = (
        pd.concat(coefficient_frames, ignore_index=True)
        if coefficient_frames
        else pd.DataFrame()
    )
    return coefficients, pd.DataFrame(pre_means), pd.DataFrame(model_rows)


def summarize(
    coefficients: pd.DataFrame,
    pre_means: pd.DataFrame,
    models: pd.DataFrame,
) -> dict[str, Any]:
    estimated = int(models["status"].eq("estimated").sum())
    return {
        "task": "T8B.13",
        "models": int(len(models)),
        "estimated_models": estimated,
        "failed_models": int(len(models) - estimated),
        "coefficient_rows": int(len(coefficients)),
        "expected_coefficient_rows": 4 * 65,
        "pre_mean_rows": int(len(pre_means)),
        "event_window": "-23_to_41",
        "reference_event_time": REFERENCE_EVENT_TIME,
        "principal_specification_changed": False,
        "frozen_event_study_overwritten": False,
        "all_models_complete": bool(
            len(models) == 4
            and estimated == 4
            and len(coefficients) == 260
            and len(pre_means) == 4
        ),
    }


def render_report(
    coefficients: pd.DataFrame,
    pre_means: pd.DataFrame,
    models: pd.DataFrame,
) -> str:
    support = summarize(coefficients, pre_means, models)
    return "\n".join(
        [
            "# Extended national event study",
            "",
            "This file persists the coefficients from the full-sample "
            "extended-window specification already used by the Phase 8A "
            "diagnostics. It does not replace the frozen -23 to +23 result.",
            "",
            f"- Estimated models: {support['estimated_models']} / 4",
            f"- Coefficient rows: {support['coefficient_rows']} / 260",
            f"- Pre-period means: {support['pre_mean_rows']} / 4",
            "",
            "All four national pretrend diagnostics fail. The figure inputs "
            "are therefore not interpreted as identified causal effects.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Persist extended national event-study coefficients."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument(
        "--coefficients",
        type=Path,
        default=DEFAULT_COEFFICIENTS,
    )
    parser.add_argument(
        "--pre-means",
        type=Path,
        default=DEFAULT_PRE_MEANS,
    )
    parser.add_argument("--models", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    coefficients, pre_means, models = run_models(
        load_sample(args.panel)
    )
    atomic_csv(coefficients, args.coefficients)
    atomic_csv(pre_means, args.pre_means)
    atomic_csv(models, args.models)
    support = summarize(coefficients, pre_means, models)
    atomic_json(support, args.support)
    atomic_text(
        render_report(coefficients, pre_means, models),
        args.report,
    )
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
