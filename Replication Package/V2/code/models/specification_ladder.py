#!/usr/bin/env python3
"""Estimate the complete preregistered national specification ladder."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from estimators import (
    CONTEMPORARY_CONTROLS,
    fit_model,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_VARIANTS = (
    PACKAGE_ROOT / "data" / "derived" / "treatment_variants.csv"
)
DEFAULT_OUTPUT = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "specification_ladder.csv"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "specification_ladder_support.json"
)
PRE_END = 202211
PRE_INTERACTIONS = tuple(
    f"pre_{control}_x_post"
    for control in CONTEMPORARY_CONTROLS
)
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)


def ladder_contract() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "01_no_controls",
            "label": "No contemporaneous controls",
            "controls": (),
            "sample": "v_a",
            "start_period": 202101,
            "end_period": 202605,
            "treatment_term": "post_treat",
            "causal_role": "principal",
        },
        {
            "step_id": "02_pre_treatment_controls_x_post",
            "label": "Pre-treatment composition interacted with post",
            "controls": PRE_INTERACTIONS,
            "sample": "v_a",
            "start_period": 202101,
            "end_period": 202605,
            "treatment_term": "post_treat",
            "causal_role": "robustness",
        },
        {
            "step_id": "03_contemporary_controls",
            "label": "Contemporary composition",
            "controls": CONTEMPORARY_CONTROLS,
            "sample": "v_a",
            "start_period": 202101,
            "end_period": 202605,
            "treatment_term": "post_treat",
            "causal_role": "descriptive_post_treatment",
        },
        {
            "step_id": "04_include_minimal_as_control",
            "label": "Minimal Exposure included as control",
            "controls": (),
            "sample": "expanded_minimal",
            "start_period": 202101,
            "end_period": 202605,
            "treatment_term": "post_treat",
            "causal_role": "robustness",
        },
        {
            "step_id": "05_continuous_exposure",
            "label": "Standardized continuous exposure",
            "controls": (),
            "sample": "continuous",
            "start_period": 202101,
            "end_period": 202605,
            "treatment_term": "post_exposure_z",
            "causal_role": "co_reported_exposure_measure",
        },
        {
            "step_id": "06_start_2022_01",
            "label": "Sample starts January 2022",
            "controls": (),
            "sample": "v_a",
            "start_period": 202201,
            "end_period": 202605,
            "treatment_term": "post_treat",
            "causal_role": "sample_sensitivity",
        },
        {
            "step_id": "07_end_2025_12",
            "label": "Sample ends December 2025",
            "controls": (),
            "sample": "v_a",
            "start_period": 202101,
            "end_period": 202512,
            "treatment_term": "post_treat",
            "causal_role": "sample_sensitivity",
        },
    ]


def _weighted_pre_control(
    group: pd.DataFrame,
    control: str,
) -> float:
    valid = group[control].notna() & group["admissoes"].gt(0)
    if not valid.any():
        return np.nan
    return float(
        np.average(
            group.loc[valid, control],
            weights=group.loc[valid, "admissoes"],
        )
    )


def prepare_ladder_data(
    panel: pd.DataFrame,
    variants: pd.DataFrame,
) -> pd.DataFrame:
    variant_columns = [
        "cbo_4d",
        "gradient_v_a",
        "isco08_mean_score",
    ]
    classes = variants[variant_columns].copy()
    classes["cbo_4d"] = classes["cbo_4d"].astype(str).str.zfill(4)
    data = panel.copy()
    data["cbo_4d"] = data["cbo_4d"].astype(str).str.zfill(4)
    data = data.drop(
        columns=[
            column
            for column in ("isco08_mean_score", "gradient_v_a")
            if column in data
        ]
    ).merge(
        classes,
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    pre = data.loc[data["periodo_num"].le(PRE_END)].copy()
    pre_records = []
    for cbo_4d, group in pre.groupby("cbo_4d", sort=True):
        record: dict[str, Any] = {"cbo_4d": cbo_4d}
        for control in CONTEMPORARY_CONTROLS:
            record[f"pre_{control}"] = _weighted_pre_control(
                group,
                control,
            )
        pre_records.append(record)
    data = data.merge(
        pd.DataFrame(pre_records),
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    for control in CONTEMPORARY_CONTROLS:
        data[f"pre_{control}_x_post"] = (
            data[f"pre_{control}"] * data["post"]
        )
    unique_scores = (
        classes.loc[classes["isco08_mean_score"].notna()]
        .drop_duplicates("cbo_4d")
        ["isco08_mean_score"]
    )
    score_mean = float(unique_scores.mean())
    score_sd = float(unique_scores.std(ddof=0))
    data["exposure_z"] = (
        data["isco08_mean_score"] - score_mean
    ) / score_sd
    data["post_exposure_z"] = data["post"] * data["exposure_z"]
    return data


def data_for_step(
    data: pd.DataFrame,
    step: dict[str, Any],
) -> pd.DataFrame:
    sample = data.loc[
        data["periodo_num"].between(
            step["start_period"],
            step["end_period"],
        )
    ].copy()
    if step["sample"] == "v_a":
        sample = sample.loc[
            sample["gradient_v_a"].isin(
                [
                    "Exposed: Gradient 1",
                    "Exposed: Gradient 2",
                    "Exposed: Gradient 3",
                    "Exposed: Gradient 4",
                    "Not Exposed",
                ]
            )
        ].copy()
        sample["treatment"] = sample[
            "gradient_v_a"
        ].str.startswith("Exposed").astype(int)
        sample["post_treat"] = sample["post"] * sample["treatment"]
    elif step["sample"] == "expanded_minimal":
        sample = sample.loc[
            sample["gradient_v_a"].isin(
                [
                    "Exposed: Gradient 1",
                    "Exposed: Gradient 2",
                    "Exposed: Gradient 3",
                    "Exposed: Gradient 4",
                    "Minimal Exposure",
                    "Not Exposed",
                ]
            )
        ].copy()
        sample["treatment"] = sample[
            "gradient_v_a"
        ].str.startswith("Exposed").astype(int)
        sample["post_treat"] = sample["post"] * sample["treatment"]
    elif step["sample"] == "continuous":
        sample = sample.loc[sample["exposure_z"].notna()].copy()
    else:
        raise ValueError(f"Unknown ladder sample: {step['sample']}")
    return sample


def run_ladder(
    panel: pd.DataFrame,
    variants: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    data = prepare_ladder_data(panel, variants)
    rows = []
    completed_steps = []
    for step in ladder_contract():
        sample = data_for_step(data, step)
        for outcome, estimator in OUTCOMES:
            result, _ = fit_model(
                sample,
                model_id=f"{step['step_id']}__{outcome}",
                outcome=outcome,
                treatment_term=step["treatment_term"],
                estimator=estimator,
                fixed_effects=("cbo_4d", "periodo"),
                cluster_variables=("cbo_4d",),
                controls=step["controls"],
                principal=step["causal_role"] == "principal",
                separation_check=("fe",),
            )
            result.update(
                {
                    "step_id": step["step_id"],
                    "step_label": step["label"],
                    "causal_role": step["causal_role"],
                    "sample": step["sample"],
                    "start_period": step["start_period"],
                    "end_period": step["end_period"],
                }
            )
            rows.append(result)
        completed_steps.append(step["step_id"])
    results = pd.DataFrame(rows)
    expected_rows = len(ladder_contract()) * len(OUTCOMES)
    if len(results) != expected_rows:
        raise RuntimeError("Specification ladder is incomplete")
    support = {
        "steps": completed_steps,
        "step_count": len(completed_steps),
        "outcomes_per_step": len(OUTCOMES),
        "model_count": int(len(results)),
        "all_models_converged": bool(results["converged"].all()),
        "omitted_steps": [],
        "continuous_exposure_cbo_families": int(
            variants["isco08_mean_score"].notna().sum()
        ),
    }
    return results, support


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
        description="Run the complete national specification ladder."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results, support = run_ladder(
        pd.read_parquet(args.panel),
        pd.read_csv(args.variants, dtype={"cbo_4d": str}),
    )
    _atomic_csv(results, args.output)
    _atomic_json(support, args.support)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
