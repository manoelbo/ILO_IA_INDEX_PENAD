#!/usr/bin/env python3
"""Cross-replicate the six principal PNADc models in R fixest."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
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
COMMON_DIR = V2_ROOT / "code" / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from merge_audit import audited_merge  # noqa: E402
from .stage0 import atomic_csv, atomic_json, sha256_file  # noqa: E402


INDIVIDUAL_PANEL_PATH = (
    FRONT_ROOT / "data" / "painel_pnadc_individual.parquet"
)
COD3_PANEL_PATH = FRONT_ROOT / "data" / "painel_pnadc_cod3.parquet"
PYTHON_RESULTS_PATH = FRONT_ROOT / "results" / "pnadc_results.csv"
CROSS_INPUT_PATH = (
    FRONT_ROOT / "data" / "pnadc_cross_replication_input.csv"
)
R_SCRIPT_PATH = Path(__file__).with_name("pnadc_cross_replication.R")
R_RESULTS_PATH = (
    FRONT_ROOT / "results" / "pnadc_cross_replication_results.csv"
)
COMPARISON_PATH = (
    FRONT_ROOT / "results" / "pnadc_cross_replication_comparison.csv"
)
STATUS_PATH = (
    FRONT_ROOT / "results" / "pnadc_cross_replication_status.json"
)

ARM_A_OUTCOMES = ("informal", "conta_propria", "ln_renda")
ARM_B_OUTCOMES = (
    "ocupados_total",
    "ocupados_formais",
    "ocupados_informais",
)
EXPECTED_MODELS = 6


def crv1_standard_error_rescale(
    *,
    original_n: int,
    collapsed_n: int,
    df_k: int,
) -> float:
    """Return the factor replacing collapsed-N CRV1 with original-N CRV1."""
    if original_n <= df_k or collapsed_n <= df_k:
        raise ValueError("CRV1 requires both sample sizes to exceed df_k")
    original_adjustment = (original_n - 1) / (original_n - df_k)
    collapsed_adjustment = (collapsed_n - 1) / (
        collapsed_n - df_k
    )
    return math.sqrt(original_adjustment / collapsed_adjustment)


def _collapse_arm_a_outcome(outcome: str) -> pd.DataFrame:
    panel = pd.read_parquet(
        INDIVIDUAL_PANEL_PATH,
        columns=[
            outcome,
            "post_treat",
            "cod3",
            "trimestre_num",
            "peso",
        ],
    )
    complete = panel.dropna(
        subset=[
            outcome,
            "post_treat",
            "cod3",
            "trimestre_num",
            "peso",
        ]
    ).copy()
    if (complete["peso"] <= 0).any():
        raise RuntimeError(f"{outcome} contains non-positive weights")
    original_n = int(len(complete))
    complete["weighted_outcome"] = (
        complete[outcome].astype(float) * complete["peso"].astype(float)
    )
    collapsed = (
        complete.groupby(
            ["cod3", "trimestre_num", "post_treat"],
            observed=True,
            sort=True,
        )
        .agg(
            weighted_outcome=("weighted_outcome", "sum"),
            regression_weight=("peso", "sum"),
            source_observations=(outcome, "size"),
        )
        .reset_index()
    )
    collapsed["outcome_value"] = (
        collapsed["weighted_outcome"]
        / collapsed["regression_weight"]
    )
    if int(collapsed["source_observations"].sum()) != original_n:
        raise RuntimeError(
            f"{outcome} sufficient statistics lost observations"
        )
    collapsed["model_id"] = f"pnadc_principal_{outcome}"
    collapsed["outcome"] = outcome
    collapsed["arm"] = "A"
    collapsed["original_n"] = original_n
    return collapsed[
        [
            "model_id",
            "outcome",
            "arm",
            "cod3",
            "trimestre_num",
            "post_treat",
            "outcome_value",
            "regression_weight",
            "source_observations",
            "original_n",
        ]
    ]


def _build_arm_b_rows() -> list[pd.DataFrame]:
    panel = pd.read_parquet(
        COD3_PANEL_PATH,
        columns=[
            *ARM_B_OUTCOMES,
            "post_treat",
            "cod3",
            "trimestre_num",
        ],
    )
    rows: list[pd.DataFrame] = []
    for outcome in ARM_B_OUTCOMES:
        complete = panel.dropna(
            subset=[
                outcome,
                "post_treat",
                "cod3",
                "trimestre_num",
            ]
        ).copy()
        frame = complete[
            ["cod3", "trimestre_num", "post_treat"]
        ].copy()
        frame["outcome_value"] = complete[outcome].astype(float)
        frame["regression_weight"] = 1.0
        frame["source_observations"] = 1
        frame["original_n"] = int(len(complete))
        frame["model_id"] = f"pnadc_principal_{outcome}"
        frame["outcome"] = outcome
        frame["arm"] = "B"
        rows.append(
            frame[
                [
                    "model_id",
                    "outcome",
                    "arm",
                    "cod3",
                    "trimestre_num",
                    "post_treat",
                    "outcome_value",
                    "regression_weight",
                    "source_observations",
                    "original_n",
                ]
            ]
        )
    return rows


def build_cross_replication_input() -> pd.DataFrame:
    """Create the exact sufficient-statistic input consumed by R."""
    rows = [
        _collapse_arm_a_outcome(outcome)
        for outcome in ARM_A_OUTCOMES
    ]
    rows.extend(_build_arm_b_rows())
    result = pd.concat(rows, ignore_index=True)
    if result["model_id"].nunique() != EXPECTED_MODELS:
        raise RuntimeError("Cross-replication model grid is incomplete")
    if any("cod4" in column.lower() for column in result.columns):
        raise RuntimeError("COD4 is forbidden in cross-replication input")
    atomic_csv(result, CROSS_INPUT_PATH)
    return result


def _run_r_fixest() -> None:
    rscript = shutil.which("Rscript")
    if rscript is None:
        raise RuntimeError("Rscript is required for P12")
    environment = os.environ.copy()
    environment.update(
        {
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        }
    )
    completed = subprocess.run(
        [
            rscript,
            str(R_SCRIPT_PATH),
            str(CROSS_INPUT_PATH),
            str(R_RESULTS_PATH),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "R cross-replication failed:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


def compare_results(
    python_results: pd.DataFrame,
    r_results: pd.DataFrame,
    *,
    expected_models: int = EXPECTED_MODELS,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare coefficients, clustered SEs, sample sizes, and clusters."""
    python_columns = [
        "model_id",
        "outcome",
        "arm",
        "coefficient",
        "standard_error",
        "n_obs",
        "minimum_clusters",
    ]
    r_columns = [
        "model_id",
        "coefficient",
        "standard_error",
        "n_obs",
        "n_clusters",
    ]
    if not set(python_columns).issubset(python_results.columns):
        raise ValueError("Python principal results have an invalid schema")
    if not set(r_columns).issubset(r_results.columns):
        raise ValueError("R cross-replication results have an invalid schema")
    left = python_results[python_columns].rename(
        columns={
            "coefficient": "python_coefficient",
            "standard_error": "python_standard_error",
            "n_obs": "python_n_obs",
            "minimum_clusters": "python_n_clusters",
        }
    )
    right = r_results[r_columns].rename(
        columns={
            "coefficient": "r_coefficient",
            "standard_error": "r_standard_error",
            "n_obs": "r_n_obs",
            "n_clusters": "r_n_clusters",
        }
    )
    comparison = audited_merge(
        left,
        right,
        merge_id="pnadc_p12_python_r_principal_comparison",
        on="model_id",
        how="inner",
        validate="one_to_one",
    )
    if len(comparison) != expected_models:
        raise RuntimeError(
            "Cross-replication does not cover the expected model grid"
        )
    comparison["coefficient_absolute_difference"] = (
        comparison["python_coefficient"]
        - comparison["r_coefficient"]
    ).abs()
    comparison["standard_error_absolute_difference"] = (
        comparison["python_standard_error"]
        - comparison["r_standard_error"]
    ).abs()
    comparison["coefficient_matches_6_decimals"] = np.isclose(
        comparison["python_coefficient"],
        comparison["r_coefficient"],
        rtol=0,
        atol=5e-7,
    )
    comparison["standard_error_matches_6_decimals"] = np.isclose(
        comparison["python_standard_error"],
        comparison["r_standard_error"],
        rtol=0,
        atol=5e-7,
    )
    comparison["same_n"] = (
        pd.to_numeric(comparison["python_n_obs"], errors="raise")
        == pd.to_numeric(comparison["r_n_obs"], errors="raise")
    )
    comparison["same_clusters"] = (
        pd.to_numeric(
            comparison["python_n_clusters"],
            errors="raise",
        )
        == pd.to_numeric(comparison["r_n_clusters"], errors="raise")
    )
    six_decimal_agreement = bool(
        comparison["coefficient_matches_6_decimals"].all()
        and comparison["standard_error_matches_6_decimals"].all()
    )
    same_n_and_clusters = bool(
        comparison["same_n"].all()
        and comparison["same_clusters"].all()
    )
    status = {
        "status": (
            "pass"
            if six_decimal_agreement and same_n_and_clusters
            else "fail"
        ),
        "models": int(len(comparison)),
        "six_decimal_agreement": six_decimal_agreement,
        "same_n_and_clusters": same_n_and_clusters,
        "maximum_coefficient_absolute_difference": float(
            comparison["coefficient_absolute_difference"].max()
        ),
        "maximum_standard_error_absolute_difference": float(
            comparison["standard_error_absolute_difference"].max()
        ),
    }
    return comparison, status


def run_cross_replication() -> dict[str, Any]:
    """Prepare the input, run R fixest, compare, and publish a receipt."""
    build_cross_replication_input()
    _run_r_fixest()
    python_results = pd.read_csv(PYTHON_RESULTS_PATH)
    r_results = pd.read_csv(R_RESULTS_PATH)
    comparison, comparison_status = compare_results(
        python_results,
        r_results,
    )
    atomic_csv(comparison, COMPARISON_PATH)
    status = {
        **comparison_status,
        "task": "P12_cross_replication",
        "r_engine": "fixest",
        "r_fixest_models": int(
            r_results["engine"].eq("fixest").sum()
        ),
        "cross_replication_input_sha256": sha256_file(
            CROSS_INPUT_PATH
        ),
        "r_results_sha256": sha256_file(R_RESULTS_PATH),
        "comparison_sha256": sha256_file(COMPARISON_PATH),
        "python_results_sha256": sha256_file(PYTHON_RESULTS_PATH),
        "individual_panel_sha256": sha256_file(
            INDIVIDUAL_PANEL_PATH
        ),
        "cod3_panel_sha256": sha256_file(COD3_PANEL_PATH),
        "contains_cod4_cells": False,
        "family_e_reestimated_or_adjusted": False,
    }
    atomic_json(status, STATUS_PATH)
    if status["status"] != "pass":
        raise RuntimeError(
            "R cross-replication failed the six-decimal contract"
        )
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    print(
        json.dumps(
            run_cross_replication(),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
