#!/usr/bin/env python3
"""Define the single balanced V2 event-time convention."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENT_GRID = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "event_study_grid.csv"
)
DEFAULT_HORIZONS = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "long_run_horizons.csv"
)
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_COEFFICIENTS = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "event_study_coefficients.csv"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "event_study_support.json"
)
EVENT_PERIOD = pd.Period("2022-12", freq="M")
REFERENCE_EVENT_TIME = -1
EVENT_TIME_MIN = -23
EVENT_TIME_MAX = 23
FINAL_PERIOD = pd.Period("2026-05", freq="M")


def event_time_from_period(periods: pd.Series) -> pd.Series:
    period_index = pd.PeriodIndex(
        periods.astype(str),
        freq="M",
    )
    values = [
        period.year * 12
        + period.month
        - (EVENT_PERIOD.year * 12 + EVENT_PERIOD.month)
        for period in period_index
    ]
    return pd.Series(values, index=periods.index, dtype="int64")


def _period_label(period: pd.Period) -> str:
    return period.strftime("%Y-%m")


def build_event_grid() -> pd.DataFrame:
    records = []
    for event_time in range(EVENT_TIME_MIN, EVENT_TIME_MAX + 1):
        period = EVENT_PERIOD + event_time
        records.append(
            {
                "event_time": event_time,
                "periodo": _period_label(period),
                "periodo_num": int(period.strftime("%Y%m")),
                "is_reference": event_time == REFERENCE_EVENT_TIME,
            }
        )
    return pd.DataFrame(records)


def validate_event_grid(grid: pd.DataFrame) -> None:
    expected = list(range(EVENT_TIME_MIN, EVENT_TIME_MAX + 1))
    observed = sorted(grid["event_time"].astype(int).tolist())
    if observed != expected:
        raise RuntimeError(
            "Event-time grid must be complete from -23 through +23"
        )
    references = grid.loc[
        grid["is_reference"].astype(bool),
        "event_time",
    ].astype(int).tolist()
    if references != [REFERENCE_EVENT_TIME]:
        raise RuntimeError("Event-time reference must be t = -1")
    reference_period = grid.loc[
        grid["event_time"].eq(REFERENCE_EVENT_TIME),
        "periodo",
    ].item()
    if reference_period != "2022-11":
        raise RuntimeError("Event-time reference must be November 2022")


def horizon_name(event_time: int) -> tuple[str | None, bool]:
    if 0 <= event_time <= 11:
        return "2022-12_to_2023-11", False
    if 12 <= event_time <= 23:
        return "2023-12_to_2024-11", False
    if 24 <= event_time <= 35:
        return "2024-12_to_2025-11", False
    if event_time >= 36:
        return "2025-12_to_cutoff", True
    return None, False


def build_horizon_grid(
    final_period: pd.Period = FINAL_PERIOD,
) -> pd.DataFrame:
    final_event_time = (
        final_period.year * 12
        + final_period.month
        - (EVENT_PERIOD.year * 12 + EVENT_PERIOD.month)
    )
    records = []
    for event_time in range(0, final_event_time + 1):
        period = EVENT_PERIOD + event_time
        horizon, partial = horizon_name(event_time)
        records.append(
            {
                "event_time": event_time,
                "periodo": _period_label(period),
                "periodo_num": int(period.strftime("%Y%m")),
                "horizon": horizon,
                "partial_horizon": partial,
            }
        )
    return pd.DataFrame(records)


def prepare_balanced_event_data(panel: pd.DataFrame) -> pd.DataFrame:
    data = panel.copy()
    data["event_time"] = event_time_from_period(data["periodo_num"])
    data = data.loc[
        data["event_time"].between(EVENT_TIME_MIN, EVENT_TIME_MAX)
    ].copy()
    observed = sorted(data["event_time"].unique().tolist())
    expected = list(range(EVENT_TIME_MIN, EVENT_TIME_MAX + 1))
    if observed != expected:
        raise RuntimeError("Panel event-time support has a hole")
    return data


def build_event_formula(
    outcome: str,
    fixed_effects: tuple[str, ...] = ("cbo_4d", "periodo"),
) -> str:
    fixed = " + ".join(fixed_effects)
    return (
        f"{outcome} ~ i(event_time, treated_main, ref=-1) | {fixed}"
    )


def parse_event_time_coefficient(name: str) -> int:
    match = re.search(
        r"\[(-?\d+)\]:treated_main$",
        name,
    )
    if not match:
        raise ValueError(f"Not an event-time coefficient: {name}")
    return int(match.group(1))


def estimate_event_studies(
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    from estimators import cluster_t_inference
    import pyfixest as pf

    data = panel.loc[panel["included_main"].eq(True)].copy()
    data = prepare_balanced_event_data(data)
    specifications = (
        ("admissoes", "ppml"),
        ("desligamentos", "ppml"),
        ("n_movimentacoes", "ppml"),
        ("ln_salario_real_adm", "ols"),
        ("asinh_saldo", "ols"),
    )
    rows: list[dict[str, Any]] = []
    model_support: dict[str, Any] = {}
    for outcome, estimator in specifications:
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
            converged = bool(getattr(model, "_convergence", False))
            if not converged:
                raise RuntimeError(
                    f"Event-study PPML did not converge: {outcome}"
                )
        else:
            model = pf.feols(
                formula,
                data=model_data,
                vcov={"CRV1": "cbo_4d"},
            )
            converged = True
        tidy = model.tidy()
        used_data = getattr(model, "_data", model_data)
        cluster_counts = {
            "cbo_4d": int(used_data["cbo_4d"].nunique())
        }
        for name, term in tidy.iterrows():
            event_time = parse_event_time_coefficient(str(name))
            coefficient = float(term["Estimate"])
            standard_error = float(term["Std. Error"])
            inference = cluster_t_inference(
                coefficient,
                standard_error,
                cluster_counts,
            )
            rows.append(
                {
                    "outcome": outcome,
                    "estimator": estimator,
                    "event_time": event_time,
                    "periodo": _period_label(
                        EVENT_PERIOD + event_time
                    ),
                    "is_reference": False,
                    "coefficient": coefficient,
                    "standard_error": standard_error,
                    "ci_low": inference["ci_low"],
                    "ci_high": inference["ci_high"],
                    "p_value": inference["p_value"],
                    "cluster_df": inference["cluster_df"],
                    "n_obs": int(model._N),
                    "n_clusters": cluster_counts["cbo_4d"],
                    "effect_percent": (
                        100.0 * math.expm1(coefficient)
                        if estimator == "ppml"
                        else math.nan
                    ),
                }
            )
        rows.append(
            {
                "outcome": outcome,
                "estimator": estimator,
                "event_time": REFERENCE_EVENT_TIME,
                "periodo": "2022-11",
                "is_reference": True,
                "coefficient": 0.0,
                "standard_error": math.nan,
                "ci_low": math.nan,
                "ci_high": math.nan,
                "p_value": math.nan,
                "cluster_df": cluster_counts["cbo_4d"] - 1,
                "n_obs": int(model._N),
                "n_clusters": cluster_counts["cbo_4d"],
                "effect_percent": (
                    0.0 if estimator == "ppml" else math.nan
                ),
            }
        )
        model_support[outcome] = {
            "estimator": estimator,
            "formula": formula,
            "n_obs": int(model._N),
            "n_clusters": cluster_counts["cbo_4d"],
            "converged": converged,
            "input_cells": int(len(data)),
            "complete_case_cells": int(len(model_data)),
            "cells_dropped": int(len(data) - int(model._N)),
            "separation_dropped": int(
                getattr(model, "n_separation_na", 0)
            ),
        }
    coefficients = pd.DataFrame(rows).sort_values(
        ["outcome", "event_time"]
    )
    expected = list(range(EVENT_TIME_MIN, EVENT_TIME_MAX + 1))
    for outcome, group in coefficients.groupby("outcome"):
        observed = group["event_time"].astype(int).tolist()
        if observed != expected:
            raise RuntimeError(
                f"Estimated event-time grid is incomplete: {outcome}"
            )
        if group["is_reference"].sum() != 1:
            raise RuntimeError(
                f"Estimated event-time reference is invalid: {outcome}"
            )
    support = {
        "event_time_min": EVENT_TIME_MIN,
        "event_time_max": EVENT_TIME_MAX,
        "reference_event_time": REFERENCE_EVENT_TIME,
        "reference_period": "2022-11",
        "tail_grouping": False,
        "models": model_support,
    }
    return coefficients.reset_index(drop=True), support


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the frozen balanced event-time convention."
    )
    parser.add_argument(
        "--event-grid",
        type=Path,
        default=DEFAULT_EVENT_GRID,
    )
    parser.add_argument(
        "--horizons",
        type=Path,
        default=DEFAULT_HORIZONS,
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument(
        "--coefficients",
        type=Path,
        default=DEFAULT_COEFFICIENTS,
    )
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--definitions-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    event_grid = build_event_grid()
    validate_event_grid(event_grid)
    _atomic_csv(event_grid, args.event_grid)
    _atomic_csv(build_horizon_grid(), args.horizons)
    if not args.definitions_only:
        coefficients, support = estimate_event_studies(
            pd.read_parquet(args.panel)
        )
        _atomic_csv(coefficients, args.coefficients)
        _atomic_json(support, args.support)
    print(
        "event_grid=-23:23 reference=-1 "
        "horizons=4 final_period=2026-05"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
