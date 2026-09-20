#!/usr/bin/env python3
"""Cross-replicate all principal RAIS models independently in R."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FRONT_ROOT = Path(__file__).resolve().parent.parent
V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
COMMON_DIR = V2_ROOT / "code" / "common"
MODELS_DIR = V2_ROOT / "code" / "caged" / "models"
for module_dir in (COMMON_DIR, MODELS_DIR):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from merge_audit import audited_merge  # noqa: E402
from pretrend_engine import atomic_csv, atomic_json  # noqa: E402
from .stage0 import sha256_file  # noqa: E402


ANNUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_rais_anual.parquet"
ROTATION_PANEL_PATH = (
    FRONT_ROOT / "data" / "painel_rais_rotatividade.parquet"
)
PART1_STATUS_PATH = FRONT_ROOT / "results" / "rais_part1_status.json"
R11_STATUS_PATH = FRONT_ROOT / "results" / "rais_r11_status.json"
STATIC_RESULTS_PATH = FRONT_ROOT / "results" / "rais_static_results.csv"
R_SCRIPT_PATH = Path(__file__).with_name("r12_cross_replication.R")

CROSS_INPUT_PATH = (
    FRONT_ROOT / "data" / "vintage" / "rais_cross_replication_input.csv"
)
CROSS_R_RESULTS_PATH = (
    FRONT_ROOT / "results" / "rais_cross_replication_r.csv"
)
CROSS_COMPARISON_PATH = (
    FRONT_ROOT / "results" / "rais_cross_replication_comparison.csv"
)
CROSS_STATUS_PATH = (
    FRONT_ROOT / "results" / "rais_cross_replication_status.json"
)

MODEL_SPECS = (
    {
        "model_id": "rais_static__estoque_3112",
        "outcome": "estoque_3112",
        "estimator": "ppml",
        "panel": "annual",
    },
    {
        "model_id": "rais_static__ln_taxa_rotatividade",
        "outcome": "ln_taxa_rotatividade",
        "estimator": "ols",
        "panel": "rotation",
    },
    {
        "model_id": "rais_static__ln_tempo_emprego_medio",
        "outcome": "ln_tempo_emprego_medio",
        "estimator": "ols",
        "panel": "annual",
    },
)

PYTHON_RESULT_COLUMNS = (
    "outcome",
    "estimator",
    "coefficient",
    "standard_error",
    "n_obs",
    "minimum_clusters",
)
R_RESULT_COLUMNS = (
    "outcome",
    "estimator",
    "coefficient",
    "standard_error",
    "n_obs",
    "n_clusters",
)


def _prepare_panel(panel: pd.DataFrame, *, label: str) -> pd.DataFrame:
    required = {"cbo_4d", "ano", "post_treat", "included_main"}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")
    prepared = panel.loc[panel["included_main"].astype(bool)].copy()
    prepared["cbo_4d"] = (
        prepared["cbo_4d"].astype("string").str.strip().str.zfill(4)
    )
    prepared["ano"] = pd.to_numeric(
        prepared["ano"], errors="raise"
    ).astype(int)
    prepared["post_treat"] = pd.to_numeric(
        prepared["post_treat"], errors="raise"
    ).astype(int)
    if prepared.duplicated(["cbo_4d", "ano"]).any():
        raise RuntimeError(f"{label} has duplicate CBO4-year cells")
    return prepared


def build_cross_replication_input(
    annual_panel: pd.DataFrame,
    rotation_panel: pd.DataFrame,
) -> pd.DataFrame:
    """Export every principal panel cell before estimator singleton removal."""
    annual = _prepare_panel(annual_panel, label="RAIS annual panel")
    rotation = _prepare_panel(rotation_panel, label="RAIS rotation panel")
    panels = {"annual": annual, "rotation": rotation}
    rows: list[pd.DataFrame] = []
    for spec in MODEL_SPECS:
        panel = panels[str(spec["panel"])]
        outcome = str(spec["outcome"])
        if outcome not in panel.columns:
            raise ValueError(f"Principal panel is missing outcome {outcome}")
        model = panel[
            ["cbo_4d", "ano", "post_treat", outcome]
        ].rename(columns={outcome: "y"})
        if model["y"].isna().any():
            raise RuntimeError(f"Principal outcome {outcome} has missing cells")
        model.insert(0, "estimator", str(spec["estimator"]))
        model.insert(0, "outcome", outcome)
        model.insert(0, "model_id", str(spec["model_id"]))
        rows.append(model)
    exported = pd.concat(rows, ignore_index=True)
    exported["y"] = pd.to_numeric(exported["y"], errors="raise")
    if exported.duplicated(["model_id", "cbo_4d", "ano"]).any():
        raise RuntimeError("Cross-replication input has duplicate model cells")
    expected_counts = {
        "estoque_3112": 2_041,
        "ln_taxa_rotatividade": 1_360,
        "ln_tempo_emprego_medio": 2_041,
    }
    observed_counts = exported.groupby("outcome").size().to_dict()
    if observed_counts != expected_counts:
        raise RuntimeError(
            "Cross-replication panel-cell counts changed: "
            f"{observed_counts}"
        )
    return exported.sort_values(
        ["model_id", "cbo_4d", "ano"]
    ).reset_index(drop=True)


def compare_cross_replication(
    python_results: pd.DataFrame,
    r_results: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare independent estimates, standard errors, samples, and clusters."""
    python_required = set(PYTHON_RESULT_COLUMNS)
    r_required = set(R_RESULT_COLUMNS)
    if missing := sorted(python_required - set(python_results.columns)):
        raise ValueError(f"Python results are missing columns: {missing}")
    if missing := sorted(r_required - set(r_results.columns)):
        raise ValueError(f"R results are missing columns: {missing}")
    python = python_results[list(PYTHON_RESULT_COLUMNS)].rename(
        columns={
            "estimator": "python_estimator",
            "coefficient": "python_coefficient",
            "standard_error": "python_standard_error",
            "n_obs": "python_n_obs",
            "minimum_clusters": "python_n_clusters",
        }
    )
    replicated = r_results[list(R_RESULT_COLUMNS)].rename(
        columns={
            "estimator": "r_estimator",
            "coefficient": "r_coefficient",
            "standard_error": "r_standard_error",
            "n_obs": "r_n_obs",
            "n_clusters": "r_n_clusters",
        }
    )
    comparison = audited_merge(
        python,
        replicated,
        merge_id="rais_python_r_cross_replication",
        validate="one_to_one",
        reporter=None,
        on="outcome",
        how="outer",
        indicator=True,
    )
    if not comparison["_merge"].eq("both").all():
        raise RuntimeError("Python and R principal model sets do not align")
    comparison = comparison.drop(columns="_merge")
    comparison["same_estimator"] = (
        comparison["python_estimator"] == comparison["r_estimator"]
    )
    comparison["coefficient_absolute_difference"] = (
        comparison["python_coefficient"]
        - comparison["r_coefficient"]
    ).abs()
    comparison["standard_error_absolute_difference"] = (
        comparison["python_standard_error"]
        - comparison["r_standard_error"]
    ).abs()
    comparison["same_n"] = (
        pd.to_numeric(comparison["python_n_obs"], errors="raise")
        == pd.to_numeric(comparison["r_n_obs"], errors="raise")
    )
    comparison["same_clusters"] = (
        pd.to_numeric(
            comparison["python_n_clusters"], errors="raise"
        )
        == pd.to_numeric(comparison["r_n_clusters"], errors="raise")
    )
    comparison["coefficient_six_decimals"] = np.round(
        comparison["python_coefficient"].astype(float), 6
    ).eq(np.round(comparison["r_coefficient"].astype(float), 6))
    comparison["standard_error_six_decimals"] = np.round(
        comparison["python_standard_error"].astype(float), 6
    ).eq(np.round(comparison["r_standard_error"].astype(float), 6))
    comparison = comparison.sort_values("outcome").reset_index(drop=True)
    same_n_and_clusters = bool(
        comparison["same_n"].all()
        and comparison["same_clusters"].all()
    )
    six_decimal_agreement = bool(
        comparison["same_estimator"].all()
        and comparison["coefficient_six_decimals"].all()
        and comparison["standard_error_six_decimals"].all()
    )
    status = {
        "models": int(len(comparison)),
        "same_n_and_clusters": same_n_and_clusters,
        "six_decimal_agreement": six_decimal_agreement,
        "max_coefficient_absolute_difference": float(
            comparison["coefficient_absolute_difference"].max()
        ),
        "max_standard_error_absolute_difference": float(
            comparison["standard_error_absolute_difference"].max()
        ),
    }
    return comparison, status


def run_cross_replication() -> dict[str, Any]:
    """Freeze the exact input, run R, and require six-decimal agreement."""
    r11_status = json.loads(R11_STATUS_PATH.read_text(encoding="utf-8"))
    if r11_status.get("r11") != "complete":
        raise RuntimeError("R11 must be complete before cross-replication")
    part1_status = json.loads(
        PART1_STATUS_PATH.read_text(encoding="utf-8")
    )
    expected_hashes = {
        ANNUAL_PANEL_PATH: str(part1_status["annual_panel_sha256"]),
        ROTATION_PANEL_PATH: str(part1_status["rotation_panel_sha256"]),
    }
    for path, expected in expected_hashes.items():
        observed = sha256_file(path)
        if observed != expected:
            raise RuntimeError(
                f"Panel SHA-256 mismatch for {path.name}: "
                f"expected {expected}, observed {observed}"
            )
    exported = build_cross_replication_input(
        pd.read_parquet(ANNUAL_PANEL_PATH),
        pd.read_parquet(ROTATION_PANEL_PATH),
    )
    atomic_csv(exported, CROSS_INPUT_PATH)
    input_hash = sha256_file(CROSS_INPUT_PATH)

    environment = os.environ.copy()
    environment.update(
        {
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        }
    )
    subprocess.run(
        ["Rscript", str(R_SCRIPT_PATH)],
        cwd=V2_ROOT,
        env=environment,
        check=True,
    )
    r_results = pd.read_csv(CROSS_R_RESULTS_PATH)
    python_results = pd.read_csv(STATIC_RESULTS_PATH)
    comparison, comparison_status = compare_cross_replication(
        python_results,
        r_results,
    )
    atomic_csv(comparison, CROSS_COMPARISON_PATH)
    status = {
        **comparison_status,
        "status": (
            "pass"
            if comparison_status["same_n_and_clusters"]
            and comparison_status["six_decimal_agreement"]
            and comparison_status["models"] == 3
            else "fail"
        ),
        "input_rows": int(len(exported)),
        "input_sha256": input_hash,
        "python_results_sha256": sha256_file(STATIC_RESULTS_PATH),
        "r_results_sha256": sha256_file(CROSS_R_RESULTS_PATH),
        "comparison_sha256": sha256_file(CROSS_COMPARISON_PATH),
        "p_values_created": 0,
        "r_backend": "fixest",
        "r_script": str(R_SCRIPT_PATH.relative_to(FRONT_ROOT)),
    }
    atomic_json(status, CROSS_STATUS_PATH)
    if status["status"] != "pass":
        raise RuntimeError(
            "Independent R replication failed the six-decimal contract"
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
