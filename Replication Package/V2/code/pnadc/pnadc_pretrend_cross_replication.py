#!/usr/bin/env python3
"""Independently replicate all twelve PNADc pretrend models in R."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

from common.merge_audit import audited_merge
from .pnadc_pretrends import (
    OUTCOME_SPECS,
    PRETRENDS_PATH,
    REFERENCE_EVENT_TIME,
    SAMPLE_SPECS,
    _load_outcome_panel,
    _prepare_event_sample,
    collapse_weighted_event_data,
)
from .stage0 import atomic_csv, atomic_json


FRONT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = FRONT_ROOT / "data" / "pnadc_pretrend_cross_input.csv"
R_RESULTS_PATH = FRONT_ROOT / "results" / "pnadc_pretrend_cross_results.csv"
R_STATUS_PATH = FRONT_ROOT / "results" / "pnadc_pretrend_r_engine_status.json"
COMPARISON_PATH = FRONT_ROOT / "results" / "pnadc_pretrend_cross_comparison.csv"
STATUS_PATH = FRONT_ROOT / "results" / "pnadc_pretrend_cross_status.json"
R_SCRIPT = Path(__file__).with_name("pnadc_pretrend_cross_replication.R")
TOLERANCE = 1e-6
JOINT_STATISTIC_RELATIVE_TOLERANCE = 1e-6
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
    pieces: list[pd.DataFrame] = []
    for specification in OUTCOME_SPECS:
        outcome = str(specification["outcome"])
        panel = _load_outcome_panel(dict(specification))
        for sample_specification in SAMPLE_SPECS:
            sample_name = str(sample_specification["sample"])
            prepared = _prepare_event_sample(
                panel,
                exclude_2020=bool(sample_specification["exclude_2020"]),
            )
            if specification["arm"] == "A":
                collapsed, original_n = collapse_weighted_event_data(
                    prepared,
                    outcome=outcome,
                    weight_column=str(specification["weight_column"]),
                )
                exported = collapsed[
                    [
                        "cod3",
                        "trimestre_num",
                        "event_time",
                        "treated",
                        outcome,
                        "cell_weight",
                    ]
                ].rename(
                    columns={outcome: "y", "cell_weight": "regression_weight"}
                )
            else:
                complete = prepared.dropna(
                    subset=[outcome, "cod3", "trimestre_num", "event_time", "treated"]
                )
                original_n = len(complete)
                exported = complete[
                    ["cod3", "trimestre_num", "event_time", "treated", outcome]
                ].rename(columns={outcome: "y"})
                exported["regression_weight"] = 1.0
            model_id = f"pnadc_pretrend_{outcome}_{sample_name}"
            exported.insert(0, "original_n", int(original_n))
            exported.insert(0, "reference_event_time", REFERENCE_EVENT_TIME)
            exported.insert(0, "arm", str(specification["arm"]))
            exported.insert(0, "sample", sample_name)
            exported.insert(0, "outcome", outcome)
            exported.insert(0, "model_id", model_id)
            pieces.append(exported)
    result = pd.concat(pieces, ignore_index=True).sort_values(
        ["model_id", "trimestre_num", "cod3", "treated"]
    )
    if result["model_id"].nunique() != 12:
        raise RuntimeError("PNADc pretrend R model grid is incomplete")
    atomic_csv(result, INPUT_PATH)
    return result


def compare(python: pd.DataFrame, r: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    comparison = audited_merge(
        python,
        r,
        merge_id="pnadc_pretrend_python_r",
        on=["model_id", "outcome", "sample", "arm"],
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
        threshold = TOLERANCE
        if field == "joint_lead_statistic":
            threshold = TOLERANCE + (
                JOINT_STATISTIC_RELATIVE_TOLERANCE
                * comparison[f"{field}_python"].abs()
            )
        comparison[passed] = comparison[difference].le(threshold)
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
    difference_columns = [
        f"{field}_absolute_difference" for field in NUMERIC_FIELDS
    ]
    failed = int((~comparison["comparison_pass"]).sum())
    status = {
        "models": int(len(comparison)),
        "failed_models": failed,
        "maximum_absolute_difference": float(
            comparison[difference_columns].max(axis=1).max()
        ),
        "numeric_tolerance": TOLERANCE,
        "joint_statistic_relative_tolerance": (
            JOINT_STATISTIC_RELATIVE_TOLERANCE
        ),
        "status": "pass" if failed == 0 and len(comparison) == 12 else "fail",
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
        env=environment,
        cwd=FRONT_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Independent PNADc R pretrend replication failed")
    comparison, status = compare(
        pd.read_csv(PRETRENDS_PATH),
        pd.read_csv(R_RESULTS_PATH),
    )
    status["input_rows"] = int(len(exported))
    atomic_csv(comparison, COMPARISON_PATH)
    atomic_json(status, STATUS_PATH)
    print(json.dumps(status, sort_keys=True))
    if status["status"] != "pass":
        raise RuntimeError("PNADc pretrend Python-R comparison failed")


if __name__ == "__main__":
    main()
