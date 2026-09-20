#!/usr/bin/env python3
"""Independently replicate spatial diagnostics and support in R."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

from common.equality import same_exact_integer
from common.merge_audit import audited_merge
from .diagnostics import (
    OUTCOMES,
    PLACEBO_OLD_PATH,
    PLACEBO_PATH,
    PRETREND_COEFFICIENTS_OLD_PATH,
    PRETREND_COEFFICIENTS_PATH,
    PRETRENDS_OLD_PATH,
    PRETRENDS_PATH,
)
from pretrend_engine import atomic_csv, atomic_json
from .support import (
    CLUSTER_PATH,
    FAMILY_PATH,
    PANEL_PATH,
    PROXY_ASSIGNMENTS_PATH,
)


FRONT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = FRONT_ROOT / "data" / "spatial_r_validation"
STAGE0_INPUT = INPUT_DIR / "stage0.csv.gz"
SUPPORT_INPUT = INPUT_DIR / "support.csv.gz"
CONTRACTS_PATH = INPUT_DIR / "model_contracts.csv"
R_MODEL_RESULTS = FRONT_ROOT / "results" / "spatial_r_model_results.csv"
R_PRETREND_RESULTS = FRONT_ROOT / "results" / "spatial_r_pretrend_results.csv"
R_SUPPORT_RESULTS = FRONT_ROOT / "results" / "spatial_r_support_results.csv"
R_ENGINE_STATUS = FRONT_ROOT / "results" / "spatial_r_engine_status.json"
MODEL_COMPARISON = FRONT_ROOT / "results" / "spatial_r_model_comparison.csv"
PRETREND_COMPARISON = (
    FRONT_ROOT / "results" / "spatial_r_pretrend_comparison.csv"
)
SUPPORT_COMPARISON = FRONT_ROOT / "results" / "spatial_r_support_comparison.csv"
STATUS_PATH = FRONT_ROOT / "results" / "spatial_r_status.json"
R_SCRIPT = Path(__file__).with_name("spatial_replication.R")
TOLERANCE = 1e-6
JOINT_STATISTIC_RELATIVE_TOLERANCE = 1e-6


def _atomic_gzip_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    frame.to_csv(
        temporary,
        index=False,
        lineterminator="\n",
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    os.replace(temporary, path)


def build_inputs() -> dict[str, int]:
    stage_columns = [
        "id_municipio",
        "periodo_num",
        "event_time",
        "treated",
        "high_connectivity",
        "high_connectivity_old_national",
        "cbo_municipio",
        "cbo_periodo",
        "uf_periodo",
        *OUTCOMES,
    ]
    stage = pd.read_parquet(PANEL_PATH, columns=stage_columns)
    stage = stage.loc[stage["periodo_num"].between(202101, 202211)].copy()
    stage = stage.sort_values(
        ["periodo_num", "cbo_municipio", "id_municipio"]
    )
    _atomic_gzip_csv(stage, STAGE0_INPUT)

    support_columns = [
        "id_municipio",
        "uf_code",
        "post",
        "treated",
        "cbo_municipio",
        "cbo_periodo",
        "uf_periodo",
        "penetracao_bl",
        "high_connectivity",
    ]
    support = pd.read_parquet(PANEL_PATH, columns=support_columns)
    assignments = pd.read_csv(
        PROXY_ASSIGNMENTS_PATH,
        dtype={"id_municipio": "string", "uf_code": "string"},
    )
    assignments["id_municipio"] = assignments["id_municipio"].str.zfill(7)
    support["id_municipio"] = support["id_municipio"].astype(str).str.zfill(7)
    support = audited_merge(
        support,
        assignments[
            [
                "id_municipio",
                "digital_admission_share",
                "high_digital_admission_share",
                "internet_use_pct",
                "high_pnad_internet_use",
            ]
        ],
        merge_id="spatial_r_support_assignments",
        on="id_municipio",
        how="left",
        validate="many_to_one",
    )
    if support.isna().any().any():
        raise RuntimeError("Spatial R support input contains missing values")
    support = support.sort_values(
        ["cbo_periodo", "cbo_municipio", "id_municipio"]
    )
    _atomic_gzip_csv(support, SUPPORT_INPUT)

    rows: list[dict[str, str]] = []
    for cut, high in (
        ("within_sample", "high_connectivity"),
        ("old_national", "high_connectivity_old_national"),
    ):
        for outcome in OUTCOMES:
            for kind in ("placebo", "pretrend"):
                rows.append(
                    {
                        "model_id": f"spatial_{kind}__{cut}__{outcome}",
                        "kind": kind,
                        "cut": cut,
                        "high_column": high,
                        "outcome": outcome,
                    }
                )
    contracts = pd.DataFrame(rows).sort_values("model_id")
    atomic_csv(contracts, CONTRACTS_PATH)
    return {
        "contracts": int(len(contracts)),
        "stage0_rows": int(len(stage)),
        "support_rows": int(len(support)),
    }


def _compare_models(r_results: pd.DataFrame) -> pd.DataFrame:
    placebo = []
    for cut, path in (
        ("within_sample", PLACEBO_PATH),
        ("old_national", PLACEBO_OLD_PATH),
    ):
        frame = pd.read_csv(path)
        frame["model_id"] = (
            "spatial_placebo__" + cut + "__" + frame["outcome"].astype(str)
        )
        frame["event_time"] = float("nan")
        frame["reference_event_time"] = float("nan")
        frame["status"] = "estimated"
        placebo.append(frame)
    coefficients = []
    for path in (PRETREND_COEFFICIENTS_PATH, PRETREND_COEFFICIENTS_OLD_PATH):
        coefficients.append(pd.read_csv(path))
    python = pd.concat([*placebo, *coefficients], ignore_index=True, sort=False)
    keys = ["model_id", "event_time"]
    comparison = audited_merge(
        python,
        r_results,
        merge_id="spatial_r_model_coefficients",
        on=keys,
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    for field in ("coefficient", "standard_error"):
        comparison[f"{field}_absolute_difference"] = (
            comparison[f"{field}_python"] - comparison[f"{field}_r"]
        ).abs()
    exact = []
    for field in ("n_obs", "minimum_clusters", "reference_event_time"):
        name = f"same_{field}"
        comparison[name] = same_exact_integer(
            comparison[f"{field}_python"],
            comparison[f"{field}_r"],
            field=field,
        )
        exact.append(name)
    comparison["same_status"] = comparison["status_python"].eq(
        comparison["status_r"]
    )
    exact.append("same_status")
    comparison["comparison_pass"] = (
        comparison["_merge"].eq("both")
        & comparison["coefficient_absolute_difference"].le(TOLERANCE)
        & comparison["standard_error_absolute_difference"].le(TOLERANCE)
        & comparison[exact].all(axis=1)
    )
    return comparison.sort_values(keys, na_position="first")


def _compare_pretrends(r_results: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for cut, path in (
        ("within_sample", PRETRENDS_PATH),
        ("old_national", PRETRENDS_OLD_PATH),
    ):
        frame = pd.read_csv(path)
        frame["model_id"] = (
            "spatial_pretrend__" + cut + "__" + frame["outcome"].astype(str)
        )
        frame["status"] = "estimated"
        pieces.append(frame)
    python = pd.concat(pieces, ignore_index=True)
    comparison = audited_merge(
        python,
        r_results,
        merge_id="spatial_r_pretrend_diagnostics",
        on="model_id",
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    numeric_fields = (
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
    pass_columns = []
    for field in numeric_fields:
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
        "status",
    ):
        passed = f"same_{field}"
        comparison[passed] = comparison[f"{field}_python"].astype(str).eq(
            comparison[f"{field}_r"].astype(str)
        )
        pass_columns.append(passed)
    for field in ("n_obs", "minimum_clusters", "reference_event_time"):
        passed = f"same_{field}"
        comparison[passed] = same_exact_integer(
            comparison[f"{field}_python"],
            comparison[f"{field}_r"],
            field=field,
        )
        pass_columns.append(passed)
    comparison["comparison_pass"] = (
        comparison["_merge"].eq("both") & comparison[pass_columns].all(axis=1)
    )
    return comparison.sort_values("model_id")


def _compare_support(r_results: pd.DataFrame) -> pd.DataFrame:
    python = pd.read_csv(CLUSTER_PATH)
    comparison = audited_merge(
        python,
        r_results,
        merge_id="spatial_r_support_diagnostics",
        on="proxy",
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    numeric = (
        "effective_municipality_clusters",
        "effective_uf_clusters",
        "largest_uf_leverage_share",
    )
    pass_columns = []
    for field in numeric:
        difference = f"{field}_absolute_difference"
        comparison[difference] = (
            comparison[f"{field}_python"] - comparison[f"{field}_r"]
        ).abs()
        passed = f"{field}_pass"
        comparison[passed] = comparison[difference].le(TOLERANCE)
        pass_columns.append(passed)
    for field in (
        "municipality_clusters_nominal",
        "uf_clusters_nominal",
        "continuous_proxy_distinct_values",
        "split_proxy_distinct_values",
        "largest_uf_leverage_code",
        "classification",
    ):
        passed = f"same_{field}"
        comparison[passed] = comparison[f"{field}_python"].astype(str).eq(
            comparison[f"{field}_r"].astype(str)
        )
        pass_columns.append(passed)
    comparison["comparison_pass"] = (
        comparison["_merge"].eq("both") & comparison[pass_columns].all(axis=1)
    )
    return comparison.sort_values("proxy")


def main() -> None:
    inputs = build_inputs()
    environment = os.environ.copy()
    for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        environment[variable] = "1"
    completed = subprocess.run(
        [
            "Rscript",
            str(R_SCRIPT),
            str(STAGE0_INPUT),
            str(SUPPORT_INPUT),
            str(CONTRACTS_PATH),
            str(R_MODEL_RESULTS),
            str(R_PRETREND_RESULTS),
            str(R_SUPPORT_RESULTS),
            str(R_ENGINE_STATUS),
        ],
        cwd=FRONT_ROOT,
        env=environment,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Independent spatial R replication failed")
    engine = json.loads(R_ENGINE_STATUS.read_text(encoding="utf-8"))
    model = _compare_models(pd.read_csv(R_MODEL_RESULTS))
    pretrend = _compare_pretrends(pd.read_csv(R_PRETREND_RESULTS))
    support = _compare_support(pd.read_csv(R_SUPPORT_RESULTS, dtype={"largest_uf_leverage_code": str}))
    family = pd.read_csv(FAMILY_PATH)
    family_stop = bool(
        len(family) == 12
        and family["coefficient"].isna().all()
        and family[["p_value", "bh_adjusted_p_value"]].isna().all().all()
        and engine.get("family_f_declared_slots") == 12
        and engine.get("family_f_coefficients_created") == 0
        and engine.get("family_f_p_values_created") == 0
    )
    failed_models = int((~model["comparison_pass"]).sum())
    failed_pretrends = int((~pretrend["comparison_pass"]).sum())
    failed_support = int((~support["comparison_pass"]).sum())
    status: dict[str, Any] = {
        **inputs,
        "coefficient_rows": int(len(model)),
        "failed_coefficient_rows": failed_models,
        "failed_pretrend_models": failed_pretrends,
        "failed_support_proxies": failed_support,
        "family_f_support_stop_replicated": family_stop,
        "maximum_coefficient_absolute_difference": float(
            model["coefficient_absolute_difference"].max()
        ),
        "maximum_standard_error_absolute_difference": float(
            model["standard_error_absolute_difference"].max()
        ),
        "numeric_tolerance": TOLERANCE,
        "r_version": engine.get("r_version"),
        "status": (
            "pass"
            if failed_models == 0
            and failed_pretrends == 0
            and failed_support == 0
            and family_stop
            else "fail"
        ),
    }
    atomic_csv(model, MODEL_COMPARISON)
    atomic_csv(pretrend, PRETREND_COMPARISON)
    atomic_csv(support, SUPPORT_COMPARISON)
    atomic_json(status, STATUS_PATH)
    print(json.dumps(status, sort_keys=True))
    if status["status"] != "pass":
        raise RuntimeError("Spatial Python-R comparison failed")


if __name__ == "__main__":
    main()
