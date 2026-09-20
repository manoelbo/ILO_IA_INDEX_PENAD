#!/usr/bin/env python3
"""Estimate the preregistered OLS log(1 + flow) secondary models."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from estimators import fit_model_grid


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_RESULTS = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "secondary_log_flow_results.csv"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "secondary_log_flow_support.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "SECONDARY_FLOW_ESTIMATORS.md"
)
FLOW_OUTCOMES = (
    "admissoes",
    "desligamentos",
    "n_movimentacoes",
)


def prepare_secondary_data(panel: pd.DataFrame) -> pd.DataFrame:
    required = {
        "included_main",
        "treated_main",
        "post",
        *FLOW_OUTCOMES,
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"National panel is missing columns: {missing}")
    sample = panel.loc[panel["included_main"].eq(True)].copy()
    sample["treatment"] = sample["treated_main"].astype(int)
    sample["post_treat"] = sample["post"] * sample["treatment"]
    for outcome in FLOW_OUTCOMES:
        if sample[outcome].lt(0).any():
            raise ValueError(f"Negative flow in secondary outcome: {outcome}")
        sample[f"log1p_{outcome}"] = np.log1p(sample[outcome])
    return sample


def secondary_specifications() -> list[dict[str, Any]]:
    return [
        {
            "model_id": f"secondary_log1p__{outcome}",
            "outcome": f"log1p_{outcome}",
            "treatment_term": "post_treat",
            "estimator": "ols",
            "fixed_effects": ("cbo_4d", "periodo"),
            "cluster_variables": ("cbo_4d",),
            "controls": (),
            "principal": False,
        }
        for outcome in FLOW_OUTCOMES
    ]


def estimate_secondary_models(panel: pd.DataFrame) -> pd.DataFrame:
    sample = prepare_secondary_data(panel)
    results = fit_model_grid(sample, secondary_specifications())
    results["flow_outcome"] = results["outcome"].str.removeprefix("log1p_")
    results["role"] = "secondary_estimator"
    return results


def render_report(results: pd.DataFrame) -> str:
    lines = [
        "# Secondary Log-Flow Estimators",
        "",
        "These three models implement the preregistered secondary OLS "
        "`log(1 + y)` estimators on the exact principal sample. They use "
        "CBO4 and month fixed effects, CBO4-clustered CRV1 inference, and "
        "no contemporary controls. PPML remains principal.",
        "",
        "| Flow | Coefficient | SE | p-value | N | CBO clusters |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in results.itertuples(index=False):
        lines.append(
            f"| {row.flow_outcome} | {row.coefficient:.6f} | "
            f"{row.standard_error:.6f} | {row.p_value:.6g} | "
            f"{row.n_obs} | {row.minimum_clusters} |"
        )
    lines.append("")
    return "\n".join(lines)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate secondary OLS log(1 + flow) models."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = estimate_secondary_models(pd.read_parquet(args.panel))
    args.results.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.results.with_suffix(f"{args.results.suffix}.tmp")
    results.to_csv(temporary, index=False)
    os.replace(temporary, args.results)
    support = {
        "all_models_converged": bool(results["converged"].all()),
        "cbo_clusters": int(results["minimum_clusters"].min()),
        "model_count": int(len(results)),
        "outcomes": results["flow_outcome"].tolist(),
        "role": "secondary_estimator",
    }
    _atomic_text(
        json.dumps(support, indent=2, sort_keys=True) + "\n",
        args.support,
    )
    _atomic_text(render_report(results), args.report)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
