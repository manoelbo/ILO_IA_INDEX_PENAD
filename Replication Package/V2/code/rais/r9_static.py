#!/usr/bin/env python3
"""Estimate the three pre-registered RAIS static models in family D."""

from __future__ import annotations

import argparse
import json
import math
import os
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

from estimators import (  # noqa: E402
    build_formula,
    cluster_t_inference,
    fit_model,
)
from heterogeneity import benjamini_hochberg  # noqa: E402
from merge_audit import audited_merge  # noqa: E402
from pretrend_engine import atomic_csv, atomic_json, atomic_text  # noqa: E402
from .stage0 import sha256_file  # noqa: E402


FAMILY_ID = "D"
FAMILY_SIZE = 3
MULTIPLICITY_METHOD = "Benjamini-Hochberg"
TREATMENT_TERM = "post_treat"
FIXED_EFFECTS = ("cbo_4d", "ano")
CLUSTER_VARIABLES = ("cbo_4d",)

FIT_MODEL_COLUMNS = (
    "model_id",
    "outcome",
    "term",
    "estimator",
    "coefficient",
    "standard_error",
    "ci_low",
    "ci_high",
    "p_value",
    "cluster_df",
    "cluster_counts",
    "minimum_clusters",
    "n_obs",
    "input_cells",
    "complete_case_cells",
    "cells_dropped",
    "cells_dropped_missing",
    "cells_dropped_estimator",
    "separation_dropped",
    "converged",
    "formula",
    "fixed_effects",
    "cluster_variables",
    "controls",
    "effect_percent",
)
BASE_RESULT_COLUMNS = (*FIT_MODEL_COLUMNS, "result_status", "error")
FAMILY_RESULT_COLUMNS = (
    "family_id",
    "family_size",
    "multiplicity_method",
    "nominal_p_value",
    "bh_adjusted_p_value",
    "nominal_significant_005",
    "bh_significant_005",
    "is_principal",
    "sample_window",
    "estimand",
    "pretrend_status",
    "pretrend_n_obs",
    "pretrend_minimum_clusters",
    "sample_matches_pretrend",
    "clusters_match_pretrend",
    "significance_marker",
    "star_source",
)

MODEL_SPECS = (
    {
        "outcome": "estoque_3112",
        "estimator": "ppml",
        "panel": "annual",
        "sample_window": "2019-2024",
        "estimand": (
            "post-2023 treated-control differential in expected active "
            "formal-employment stock at December 31"
        ),
    },
    {
        "outcome": "ln_taxa_rotatividade",
        "estimator": "ols",
        "panel": "rotation",
        "sample_window": "2021-2024",
        "estimand": (
            "post-2023 treated-control differential in log annual rotation "
            "rate"
        ),
    },
    {
        "outcome": "ln_tempo_emprego_medio",
        "estimator": "ols",
        "panel": "annual",
        "sample_window": "2019-2024",
        "estimand": (
            "post-2023 treated-control differential in log average tenure "
            "among active links"
        ),
    },
)

ANNUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_rais_anual.parquet"
ROTATION_PANEL_PATH = (
    FRONT_ROOT / "data" / "painel_rais_rotatividade.parquet"
)
PART1_STATUS_PATH = FRONT_ROOT / "results" / "rais_part1_status.json"
R8_STATUS_PATH = FRONT_ROOT / "results" / "rais_r8_status.json"
PRETRENDS_PATH = FRONT_ROOT / "results" / "rais_pretrends.csv"
SUPPORT_TABLE_PATH = FRONT_ROOT / "results" / "rais_support.csv"
STATIC_RESULTS_PATH = FRONT_ROOT / "results" / "rais_static_results.csv"
STATIC_SUPPORT_PATH = (
    FRONT_ROOT / "results" / "rais_static_results_support.json"
)
STATIC_REPORT_PATH = FRONT_ROOT / "results" / "RAIS_STATIC_RESULTS.md"
R9_STATUS_PATH = FRONT_ROOT / "results" / "rais_r9_status.json"
R10_RESULT_PATH = FRONT_ROOT / "results" / "rais_sensitivities.csv"

FROZEN_FAMILY_PATHS = {
    "A": V2_ROOT / "results" / "diagnostics" / "ddd_multiplicity_results.csv",
    "B": (
        V2_ROOT
        / "results"
        / "diagnostics"
        / "ddd_alternative_partitions.csv"
    ),
    "C": V2_ROOT / "results" / "models" / "group_did_results.csv",
}


def failed_result(
    spec: dict[str, Any],
    *,
    input_cells: int,
    error: Exception,
) -> dict[str, Any]:
    """Return a full 27-column failed-estimation family member."""
    outcome = str(spec["outcome"])
    estimator = str(spec["estimator"])
    row: dict[str, Any] = {
        "model_id": f"rais_static__{outcome}",
        "outcome": outcome,
        "term": TREATMENT_TERM,
        "estimator": estimator,
        "coefficient": np.nan,
        "standard_error": np.nan,
        "ci_low": np.nan,
        "ci_high": np.nan,
        "p_value": np.nan,
        "cluster_df": np.nan,
        "cluster_counts": "",
        "minimum_clusters": np.nan,
        "n_obs": np.nan,
        "input_cells": int(input_cells),
        "complete_case_cells": np.nan,
        "cells_dropped": np.nan,
        "cells_dropped_missing": np.nan,
        "cells_dropped_estimator": np.nan,
        "separation_dropped": np.nan,
        "converged": False,
        "formula": build_formula(
            outcome,
            TREATMENT_TERM,
            FIXED_EFFECTS,
            (),
        ),
        "fixed_effects": " + ".join(FIXED_EFFECTS),
        "cluster_variables": " + ".join(CLUSTER_VARIABLES),
        "controls": "",
        "effect_percent": np.nan,
        "result_status": "failed_estimation",
        "error": str(error),
    }
    return {column: row[column] for column in BASE_RESULT_COLUMNS}


def reconstruct_inference(row: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct all coefficient inference with the shared cluster-t."""
    result = dict(row)
    if result.get("result_status") != "estimated":
        return result
    cluster_counts = {
        str(key): int(value)
        for key, value in json.loads(
            str(result["cluster_counts"])
        ).items()
    }
    inference = cluster_t_inference(
        float(result["coefficient"]),
        float(result["standard_error"]),
        cluster_counts,
    )
    result.update(
        {
            "ci_low": inference["ci_low"],
            "ci_high": inference["ci_high"],
            "p_value": inference["p_value"],
            "cluster_df": inference["cluster_df"],
            "minimum_clusters": min(cluster_counts.values()),
        }
    )
    return result


def _fit_one(
    panel: pd.DataFrame,
    spec: dict[str, Any],
) -> dict[str, Any]:
    outcome = str(spec["outcome"])
    try:
        shared_result, _ = fit_model(
            panel,
            model_id=f"rais_static__{outcome}",
            outcome=outcome,
            treatment_term=TREATMENT_TERM,
            estimator=str(spec["estimator"]),
            fixed_effects=FIXED_EFFECTS,
            cluster_variables=CLUSTER_VARIABLES,
            controls=(),
            principal=True,
        )
        if tuple(shared_result) != FIT_MODEL_COLUMNS:
            raise RuntimeError(
                "Shared fit_model schema differs from the frozen local "
                f"25-column contract: {tuple(shared_result)}"
            )
        original_inference = {
            key: shared_result[key]
            for key in ("ci_low", "ci_high", "p_value", "cluster_df")
        }
        row = {
            **shared_result,
            "result_status": "estimated",
            "error": "",
        }
        row = reconstruct_inference(row)
        for key, original in original_inference.items():
            reconstructed = row[key]
            if not math.isclose(
                float(original),
                float(reconstructed),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise RuntimeError(
                    f"Cluster-t reconstruction mismatch for {outcome}: {key}"
                )
        return {column: row[column] for column in BASE_RESULT_COLUMNS}
    except Exception as error:  # noqa: BLE001
        return failed_result(
            spec,
            input_cells=int(len(panel)),
            error=error,
        )


def finalize_family_d(results: pd.DataFrame) -> pd.DataFrame:
    """Apply the single pre-registered BH adjustment for family D."""
    if len(results) != FAMILY_SIZE:
        raise RuntimeError(
            f"Family D must contain exactly {FAMILY_SIZE} rows"
        )
    if results["outcome"].duplicated().any():
        raise RuntimeError("Family D outcomes must be unique")
    output = results.copy()
    output["family_id"] = FAMILY_ID
    output["family_size"] = FAMILY_SIZE
    output["multiplicity_method"] = MULTIPLICITY_METHOD
    output["nominal_p_value"] = pd.to_numeric(
        output["p_value"], errors="coerce"
    )
    output["bh_adjusted_p_value"] = benjamini_hochberg(
        output["nominal_p_value"].to_numpy(),
        family_size=FAMILY_SIZE,
    )
    output["nominal_significant_005"] = (
        output["nominal_p_value"] < 0.05
    )
    output["bh_significant_005"] = (
        output["bh_adjusted_p_value"] < 0.05
    )
    output["is_principal"] = True
    return output


def attach_pretrends(
    results: pd.DataFrame,
    pretrends: pd.DataFrame,
) -> pd.DataFrame:
    """Attach the already published R8 classification and validate samples."""
    required = {
        "outcome",
        "pretrend_status",
        "n_obs",
        "minimum_clusters",
    }
    missing = sorted(required - set(pretrends.columns))
    if missing:
        raise ValueError(f"R8 pretrends are missing columns: {missing}")
    diagnostic = pretrends[
        [
            "outcome",
            "pretrend_status",
            "n_obs",
            "minimum_clusters",
        ]
    ].rename(
        columns={
            "n_obs": "pretrend_n_obs",
            "minimum_clusters": "pretrend_minimum_clusters",
        }
    )
    attached = audited_merge(
        results,
        diagnostic,
        merge_id="rais_static_pretrends",
        validate="one_to_one",
        on="outcome",
        how="left",
    )
    if attached["pretrend_status"].isna().any():
        missing_outcomes = attached.loc[
            attached["pretrend_status"].isna(), "outcome"
        ].tolist()
        raise RuntimeError(f"Missing R8 pretrends: {missing_outcomes}")
    estimated = attached["result_status"].eq("estimated")
    attached["sample_matches_pretrend"] = (
        pd.to_numeric(attached["n_obs"], errors="coerce")
        == pd.to_numeric(attached["pretrend_n_obs"], errors="coerce")
    )
    attached["clusters_match_pretrend"] = (
        pd.to_numeric(attached["minimum_clusters"], errors="coerce")
        == pd.to_numeric(
            attached["pretrend_minimum_clusters"], errors="coerce"
        )
    )
    mismatch = attached.loc[
        estimated
        & (
            ~attached["sample_matches_pretrend"]
            | ~attached["clusters_match_pretrend"]
        ),
        [
            "outcome",
            "n_obs",
            "pretrend_n_obs",
            "minimum_clusters",
            "pretrend_minimum_clusters",
        ],
    ]
    if not mismatch.empty:
        raise RuntimeError(
            "Static model and R8 sample mismatch: "
            + mismatch.to_dict(orient="records").__repr__()
        )
    attached["significance_marker"] = np.where(
        attached["bh_significant_005"]
        & attached["pretrend_status"].eq("pass")
        & estimated,
        "*",
        "",
    )
    attached["star_source"] = (
        "bh_adjusted_p_value_and_pretrend_pass"
    )
    return attached


def _format_number(value: Any, digits: int = 4) -> str:
    numeric = float(value)
    if not np.isfinite(numeric):
        return "NA"
    return f"{numeric:.{digits}f}"


def _format_p_value(value: Any) -> str:
    numeric = float(value)
    if not np.isfinite(numeric):
        return "NA"
    if numeric < 0.001:
        return "<0.001"
    return f"{numeric:.3f}"


def render_static_report(results: pd.DataFrame) -> str:
    """Render the R9 estimands, windows, multiplicity, and causal limits."""
    lines = [
        "# RAIS static results — family D",
        "",
        "All three specifications were frozen before estimation. The "
        "coefficient is the post-2023 treated-control differential with CBO4 "
        "and year fixed effects, clustered by CBO4. Nominal and "
        "Benjamini-Hochberg adjusted p-values are shown side by side.",
        "",
        "| Outcome | Window | Estimator | Coefficient | SE | 95% CI | "
        "Nominal p | BH p | Pretrend | Marker |",
        "|---|---|---|---:|---:|---|---:|---:|---|---|",
    ]
    for row in results.itertuples(index=False):
        window = str(row.sample_window).replace("-", "–")
        interval = (
            f"[{_format_number(row.ci_low)}; "
            f"{_format_number(row.ci_high)}]"
        )
        lines.append(
            f"| `{row.outcome}` | {window} | {row.estimator.upper()} | "
            f"{_format_number(row.coefficient)} | "
            f"{_format_number(row.standard_error)} | {interval} | "
            f"{_format_p_value(row.nominal_p_value)} | "
            f"{_format_p_value(row.bh_adjusted_p_value)} | "
            f"`{row.pretrend_status}` | {row.significance_marker} |"
        )
    lines.extend(
        [
            "",
            "## Estimands and interpretation",
            "",
            "- `estoque_3112`, 2019–2024: post-2023 treated-control "
            "differential in expected active formal-employment stock at "
            "December 31. The PPML coefficient is a semi-elasticity; its "
            "implicit percentage change is `100 × (exp(beta) - 1)`. It is "
            "not a log-log elasticity.",
            "- `ln_taxa_rotatividade`, 2021–2024: post-2023 "
            "treated-control differential in the log annual rotation rate.",
            "- `ln_tempo_emprego_medio`, 2019–2024: post-2023 "
            "treated-control differential in log average tenure among active "
            "links.",
            "",
            "A failed pretrend removes the significance marker and prevents a "
            "causal reading, regardless of the nominal or adjusted p-value. A "
            "passing non-significant pretrend diagnostic is also not proof of "
            "parallel trends.",
            "",
            "Family D contains exactly three members and is adjusted once. "
            "Families A, B, and C are unchanged.",
            "",
        ]
    )
    return "\n".join(lines)


def _frozen_family_hashes() -> dict[str, str]:
    return {
        family_id: sha256_file(path)
        for family_id, path in FROZEN_FAMILY_PATHS.items()
    }


def run_r9() -> dict[str, Any]:
    """Execute R9 and stop before the declared R10 sensitivities."""
    if R10_RESULT_PATH.exists():
        raise RuntimeError("R10 results already exist before R9")
    if not SUPPORT_TABLE_PATH.exists():
        raise RuntimeError("The support table must exist before R9")
    r8_status = json.loads(R8_STATUS_PATH.read_text(encoding="utf-8"))
    if r8_status.get("r8") != "complete":
        raise RuntimeError("R8 must be complete before R9")
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
    family_hashes_before = _frozen_family_hashes()

    annual = pd.read_parquet(ANNUAL_PANEL_PATH)
    rotation = pd.read_parquet(ROTATION_PANEL_PATH)
    panels = {"annual": annual, "rotation": rotation}
    rows: list[dict[str, Any]] = []
    for spec in MODEL_SPECS:
        row = _fit_one(panels[str(spec["panel"])], dict(spec))
        row["sample_window"] = str(spec["sample_window"])
        row["estimand"] = str(spec["estimand"])
        rows.append(row)
    base_results = pd.DataFrame(rows)
    if list(base_results.columns[: len(BASE_RESULT_COLUMNS)]) != list(
        BASE_RESULT_COLUMNS
    ):
        raise RuntimeError("R9 base result column order is invalid")
    family = finalize_family_d(base_results)
    pretrends = pd.read_csv(PRETRENDS_PATH)
    results = attach_pretrends(family, pretrends)
    result_columns = [
        *BASE_RESULT_COLUMNS,
        *FAMILY_RESULT_COLUMNS,
    ]
    results = results[result_columns]

    family_hashes_after = _frozen_family_hashes()
    if family_hashes_after != family_hashes_before:
        raise RuntimeError("A frozen A/B/C family changed during R9")
    if results["family_size"].ne(FAMILY_SIZE).any():
        raise RuntimeError("Family D size changed")
    if len(results) != FAMILY_SIZE:
        raise RuntimeError("R9 did not retain all family D members")
    failed_pretrend_markers = results.loc[
        results["pretrend_status"].eq("fail"), "significance_marker"
    ]
    if failed_pretrend_markers.ne("").any():
        raise RuntimeError("A failed-pretrend result received a marker")

    atomic_csv(results, STATIC_RESULTS_PATH)
    atomic_json(
        {
            "status": "pass",
            "family_id": FAMILY_ID,
            "family_size": FAMILY_SIZE,
            "multiplicity_method": MULTIPLICITY_METHOD,
            "bh_application_count": 1,
            "models": int(len(results)),
            "estimated_models": int(
                results["result_status"].eq("estimated").sum()
            ),
            "failed_models": int(
                results["result_status"].eq("failed_estimation").sum()
            ),
            "all_samples_match_r8": bool(
                results.loc[
                    results["result_status"].eq("estimated"),
                    "sample_matches_pretrend",
                ].all()
            ),
            "all_clusters_match_r8": bool(
                results.loc[
                    results["result_status"].eq("estimated"),
                    "clusters_match_pretrend",
                ].all()
            ),
            "failed_pretrend_markers": int(
                results.loc[
                    results["pretrend_status"].eq("fail"),
                    "significance_marker",
                ].ne("").sum()
            ),
            "support_published_before_static_results": bool(
                SUPPORT_TABLE_PATH.stat().st_mtime
                <= STATIC_RESULTS_PATH.stat().st_mtime
            ),
            "family_abc_sha256_before": family_hashes_before,
            "family_abc_sha256_after": family_hashes_after,
            "family_abc_unchanged": True,
            "shared_functions": [
                "estimators.fit_model",
                "estimators.cluster_t_inference",
                "heterogeneity.benjamini_hochberg",
                "merge_audit.audited_merge",
            ],
            "r10_executed": False,
        },
        STATIC_SUPPORT_PATH,
    )
    atomic_text(render_static_report(results), STATIC_REPORT_PATH)
    status = {
        "status": "complete",
        "r9": "complete",
        "r10": "not_executed",
        "full_part2_gate": "pending_r10",
        "family_id": FAMILY_ID,
        "family_size": FAMILY_SIZE,
        "estimated_models": int(
            results["result_status"].eq("estimated").sum()
        ),
        "failed_models": int(
            results["result_status"].eq("failed_estimation").sum()
        ),
        "nominal_significant_models": int(
            results["nominal_significant_005"].sum()
        ),
        "bh_significant_models": int(
            results["bh_significant_005"].sum()
        ),
        "display_markers": int(
            results["significance_marker"].ne("").sum()
        ),
        "static_results_sha256": sha256_file(STATIC_RESULTS_PATH),
    }
    atomic_json(status, R9_STATUS_PATH)
    return {
        "results": results.to_dict(orient="records"),
        "status": status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(run_r9(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
