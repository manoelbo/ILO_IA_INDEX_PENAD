#!/usr/bin/env python3
"""Build normalized descriptive trajectories for the occupation cases."""

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

from pretrend_engine import atomic_csv, atomic_json, atomic_text


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_casos_ocupacionais.parquet"
)
OUTPUT_DIR = PACKAGE_ROOT / "results" / "mechanisms"
DEFAULT_TRAJECTORIES = OUTPUT_DIR / "occupation_case_trajectories.csv"
DEFAULT_TERMINAL = OUTPUT_DIR / "occupation_case_terminal_summary.csv"
DEFAULT_SUMMARY = OUTPUT_DIR / "occupation_case_trajectories_support.json"
DEFAULT_REPORT = OUTPUT_DIR / "OCCUPATION_CASE_TRAJECTORIES.md"

BASELINE_PERIOD = 202211
TERMINAL_START = 202506
TERMINAL_END = 202605
GROUP_KEYS = ["case_id", "age_group"]
OUTCOMES = ("admissions", "real_admission_wage")


def _month_range(start: int, end: int) -> list[int]:
    values: list[int] = []
    year, month = divmod(start, 100)
    end_year, end_month = divmod(end, 100)
    while (year, month) <= (end_year, end_month):
        values.append(year * 100 + month)
        month += 1
        if month == 13:
            year += 1
            month = 1
    return values


TERMINAL_PERIODS = _month_range(TERMINAL_START, TERMINAL_END)


def _baseline_values(
    panel: pd.DataFrame,
    outcome: str,
) -> pd.Series:
    baseline = panel.loc[
        panel["periodo_num"].eq(BASELINE_PERIOD),
        [*GROUP_KEYS, outcome],
    ].copy()
    if baseline.duplicated(GROUP_KEYS).any():
        raise RuntimeError(
            f"Baseline keys are duplicated for {outcome}"
        )
    expected_groups = panel[GROUP_KEYS].drop_duplicates()
    if len(baseline) != len(expected_groups):
        raise RuntimeError(
            f"Baseline coverage is incomplete for {outcome}"
        )
    values = baseline.set_index(GROUP_KEYS)[outcome]
    if values.isna().any() or values.le(0).any():
        raise RuntimeError(
            f"Baseline values must be observed and positive for {outcome}"
        )
    return values


def build_trajectories(panel: pd.DataFrame) -> pd.DataFrame:
    required = {
        *GROUP_KEYS,
        "case_label_pt",
        "periodo_num",
        "period",
        "dictionary_sha256",
        *OUTCOMES,
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Occupation-case panel is missing: {missing}")
    if panel.duplicated([*GROUP_KEYS, "periodo_num"]).any():
        raise RuntimeError("Occupation-case panel keys are duplicated")

    key_index = pd.MultiIndex.from_frame(panel[GROUP_KEYS])
    frames: list[pd.DataFrame] = []
    for outcome in OUTCOMES:
        baseline = _baseline_values(panel, outcome)
        baseline_values = baseline.reindex(key_index).to_numpy()
        if np.isnan(baseline_values).any():
            raise RuntimeError(
                f"Baseline mapping is incomplete for {outcome}"
            )
        frame = panel[
            [
                "case_id",
                "case_label_pt",
                "age_group",
                "periodo_num",
                "period",
                "dictionary_sha256",
            ]
        ].copy()
        frame["outcome"] = outcome
        frame["observed_value"] = panel[outcome].to_numpy()
        frame["baseline_period"] = BASELINE_PERIOD
        frame["baseline_value"] = baseline_values
        frame["normalized_value"] = (
            frame["observed_value"] / frame["baseline_value"]
        )
        frame["is_descriptive"] = True
        frame["has_counterfactual"] = False
        frame["analysis_type"] = "normalized_monthly_trajectory"
        frames.append(frame)
    trajectories = pd.concat(frames, ignore_index=True)
    return trajectories.sort_values(
        ["case_id", "age_group", "outcome", "periodo_num"]
    ).reset_index(drop=True)


def build_terminal_summary(
    trajectories: pd.DataFrame,
) -> pd.DataFrame:
    observed_periods = sorted(
        trajectories.loc[
            trajectories["periodo_num"].between(
                TERMINAL_START,
                TERMINAL_END,
            ),
            "periodo_num",
        ]
        .unique()
        .tolist()
    )
    if observed_periods != TERMINAL_PERIODS:
        raise RuntimeError("Terminal twelve-month window is incomplete")
    terminal = trajectories.loc[
        trajectories["periodo_num"].isin(TERMINAL_PERIODS)
    ].copy()
    summary = (
        terminal.groupby(
            [
                "case_id",
                "case_label_pt",
                "age_group",
                "outcome",
                "dictionary_sha256",
            ],
            as_index=False,
            observed=True,
        )
        .agg(
            terminal_mean_index=("normalized_value", "mean"),
            terminal_observed_months=("normalized_value", "count"),
        )
        .sort_values(["case_id", "age_group", "outcome"])
        .reset_index(drop=True)
    )
    summary["terminal_mean_index"] = summary[
        "terminal_mean_index"
    ].round(12)
    summary["terminal_change_from_base_pct"] = (
        (summary["terminal_mean_index"] - 1.0) * 100.0
    ).round(10)
    summary["terminal_start"] = TERMINAL_START
    summary["terminal_end"] = TERMINAL_END
    summary["baseline_period"] = BASELINE_PERIOD
    summary["is_descriptive"] = True
    summary["has_counterfactual"] = False
    summary["analysis_type"] = "terminal_twelve_month_mean"
    return summary


def summarize(
    trajectories: pd.DataFrame,
    terminal: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "task": "T8B.7",
        "analysis_type": "descriptive_normalized_trajectories",
        "cases": int(trajectories["case_id"].nunique()),
        "age_groups": int(trajectories["age_group"].nunique()),
        "outcomes": int(trajectories["outcome"].nunique()),
        "trajectory_rows": int(len(trajectories)),
        "terminal_rows": int(len(terminal)),
        "baseline_period": BASELINE_PERIOD,
        "terminal_start": TERMINAL_START,
        "terminal_end": TERMINAL_END,
        "terminal_months": len(TERMINAL_PERIODS),
        "terminal_complete_rows": int(
            terminal["terminal_observed_months"].eq(12).sum()
        ),
        "has_counterfactual": False,
    }


def render_report(
    trajectories: pd.DataFrame,
    terminal: pd.DataFrame,
) -> str:
    support = summarize(trajectories, terminal)
    return "\n".join(
        [
            "# Occupation-case trajectories",
            "",
            "The monthly admissions and real admission-wage series are "
            "normalized within each occupation-case and age-group pair. "
            "November 2022 equals 1 in every series.",
            "",
            f"- Cases: {support['cases']}",
            f"- Age groups: {support['age_groups']}",
            f"- Monthly trajectory rows: {support['trajectory_rows']}",
            f"- Terminal summary rows: {support['terminal_rows']}",
            "",
            "The terminal measure is the arithmetic mean of the normalized "
            "index from June 2025 through May 2026. Observed-month counts "
            "are exported with every row. These are descriptive series "
            "without a case-specific comparison group or model-based "
            "inference.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build normalized occupation-case trajectories."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument(
        "--trajectories",
        type=Path,
        default=DEFAULT_TRAJECTORIES,
    )
    parser.add_argument(
        "--terminal",
        type=Path,
        default=DEFAULT_TERMINAL,
    )
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    panel = pd.read_parquet(args.panel)
    trajectories = build_trajectories(panel)
    terminal = build_terminal_summary(trajectories)
    atomic_csv(trajectories, args.trajectories)
    atomic_csv(terminal, args.terminal)
    support = summarize(trajectories, terminal)
    atomic_json(support, args.summary)
    atomic_text(render_report(trajectories, terminal), args.report)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
