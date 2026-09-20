#!/usr/bin/env python3
"""Independently replicate all RAIS pretrend diagnostics in R."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common.merge_audit import audited_merge
from .r8_pretrends import (
    ANNUAL_PANEL_PATH,
    ANNUAL_REFERENCE_EVENT_TIME,
    OUTCOME_SPECS,
    PRETRENDS_PATH,
    ROTATION_PANEL_PATH,
    prepare_annual_event_data,
)
from pretrend_engine import atomic_csv, atomic_json


FRONT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = FRONT_ROOT / "data" / "vintage" / "rais_pretrend_r_input.csv"
R_RESULTS_PATH = FRONT_ROOT / "results" / "rais_pretrend_r_results.csv"
COMPARISON_PATH = FRONT_ROOT / "results" / "rais_pretrend_r_comparison.csv"
STATUS_PATH = FRONT_ROOT / "results" / "rais_pretrend_r_status.json"
R_STATUS_PATH = FRONT_ROOT / "results" / "rais_pretrend_r_engine_status.json"
R_SCRIPT = Path(__file__).with_name("r_pretrends.R")
TOLERANCE = 1e-6
NUMERIC_FIELDS = (
    "joint_lead_count",
    "joint_lead_statistic",
    "joint_lead_p_value",
    "lead_covariance_min_eigenvalue",
    "linear_pretrend_coefficient",
    "linear_pretrend_standard_error",
    "linear_pretrend_p_value",
    "dynamic_pre_p_lt_005",
    "dynamic_min_p_value",
)


def build_input() -> pd.DataFrame:
    panels = {
        "annual": pd.read_parquet(ANNUAL_PANEL_PATH),
        "rotation": pd.read_parquet(ROTATION_PANEL_PATH),
    }
    pieces: list[pd.DataFrame] = []
    for specification in OUTCOME_SPECS:
        outcome = str(specification["outcome"])
        sample = prepare_annual_event_data(
            panels[str(specification["panel"])],
            outcome=outcome,
            start_year=int(specification["start_year"]),
            end_year=int(specification["end_year"]),
        )
        exported = sample[
            ["cbo_4d", "ano", "event_time", "treated_main", outcome]
        ].rename(columns={outcome: "y"})
        exported.insert(0, "reference_event_time", ANNUAL_REFERENCE_EVENT_TIME)
        exported.insert(0, "estimator", str(specification["estimator"]))
        exported.insert(0, "outcome", outcome)
        exported.insert(0, "model_id", f"rais_pretrend__{outcome}")
        pieces.append(exported)
    result = pd.concat(pieces, ignore_index=True).sort_values(
        ["model_id", "cbo_4d", "ano"]
    )
    atomic_csv(result, INPUT_PATH)
    return result


def compare(python: pd.DataFrame, r: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    left = python.copy()
    left["model_id"] = "rais_pretrend__" + left["outcome"].astype(str)
    comparison = audited_merge(
        left,
        r,
        merge_id="rais_pretrend_python_r",
        on=["model_id", "outcome", "estimator"],
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    pass_columns: list[str] = []
    for field in NUMERIC_FIELDS:
        difference = f"{field}_absolute_difference"
        comparison[difference] = (
            comparison[f"{field}_python"] - comparison[f"{field}_r"]
        ).abs()
        passed = f"{field}_pass"
        comparison[passed] = comparison[difference].le(TOLERANCE)
        pass_columns.append(passed)
    for field in (
        "lead_covariance_positive_semidefinite",
        "pretrend_status",
        "n_obs",
        "minimum_clusters",
        "reference_event_time",
    ):
        passed = f"same_{field}"
        comparison[passed] = comparison[f"{field}_python"].astype(str).eq(
            comparison[f"{field}_r"].astype(str)
        )
        pass_columns.append(passed)
    comparison["comparison_pass"] = (
        comparison["_merge"].eq("both") & comparison[pass_columns].all(axis=1)
    )
    numeric_differences = [
        f"{field}_absolute_difference" for field in NUMERIC_FIELDS
    ]
    failed = int((~comparison["comparison_pass"]).sum())
    status = {
        "models": int(len(comparison)),
        "failed_models": failed,
        "maximum_absolute_difference": float(
            comparison[numeric_differences].max(axis=1).max()
        ),
        "numeric_tolerance": TOLERANCE,
        "status": "pass" if failed == 0 and len(comparison) == 3 else "fail",
    }
    return comparison.sort_values("model_id"), status


def main() -> None:
    exported = build_input()
    environment = os.environ.copy()
    for variable in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
    ):
        environment[variable] = "1"
    completed = subprocess.run(
        [
            "Rscript",
            str(R_SCRIPT),
            str(INPUT_PATH),
            str(R_RESULTS_PATH),
            str(R_STATUS_PATH),
        ],
        cwd=FRONT_ROOT,
        env=environment,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Independent RAIS R pretrend replication failed")
    comparison, status = compare(
        pd.read_csv(PRETRENDS_PATH),
        pd.read_csv(R_RESULTS_PATH),
    )
    status["input_rows"] = int(len(exported))
    atomic_csv(comparison, COMPARISON_PATH)
    atomic_json(status, STATUS_PATH)
    print(json.dumps(status, sort_keys=True))
    if status["status"] != "pass":
        raise RuntimeError("RAIS pretrend Python-R comparison failed")


if __name__ == "__main__":
    main()
