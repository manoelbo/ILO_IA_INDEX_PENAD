#!/usr/bin/env python3
"""Principal Family E estimation for PNADc Front 2."""

from __future__ import annotations

import argparse
import gc
import json
import os
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
MODELS_DIR = V2_ROOT / "code" / "caged" / "models"
COMMON_DIR = V2_ROOT / "code" / "common"
for directory in (MODELS_DIR, COMMON_DIR):
    sys.path.insert(0, str(directory))

from heterogeneity import benjamini_hochberg  # noqa: E402
from estimators import fit_model  # noqa: E402
from merge_audit import audited_merge  # noqa: E402
from .stage0 import (  # noqa: E402
    atomic_csv,
    atomic_json,
    atomic_text,
    sha256_file,
)
from .weighted_estimator import fit_weighted_model  # noqa: E402


FAMILY_E_SIZE = 6
BASE_RESULT_COLUMNS = (
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
    "weight_column",
    "sum_of_weights",
)

OUTCOME_SPECS = (
    {
        "outcome": "informal",
        "arm": "A",
        "estimator": "ols",
        "is_reconciliation": False,
    },
    {
        "outcome": "conta_propria",
        "arm": "A",
        "estimator": "ols",
        "is_reconciliation": False,
    },
    {
        "outcome": "ocupados_total",
        "arm": "B",
        "estimator": "ppml",
        "is_reconciliation": False,
    },
    {
        "outcome": "ocupados_formais",
        "arm": "B",
        "estimator": "ppml",
        "is_reconciliation": False,
    },
    {
        "outcome": "ocupados_informais",
        "arm": "B",
        "estimator": "ppml",
        "is_reconciliation": False,
    },
    {
        "outcome": "ln_renda",
        "arm": "A",
        "estimator": "ols",
        "is_reconciliation": True,
    },
)

INDIVIDUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_pnadc_individual.parquet"
COD3_PANEL_PATH = FRONT_ROOT / "data" / "painel_pnadc_cod3.parquet"
PRETRENDS_PATH = FRONT_ROOT / "results" / "pnadc_pretrends.csv"
PRETRENDS_STATUS_PATH = (
    FRONT_ROOT / "results" / "pnadc_pretrends_status.json"
)
RESULTS_PATH = FRONT_ROOT / "results" / "pnadc_results.csv"
RESULTS_REPORT_PATH = FRONT_ROOT / "results" / "PNADC_RESULTS.md"
RESULTS_STATUS_PATH = FRONT_ROOT / "results" / "pnadc_results_status.json"


def normalize_arm_b_result(result: dict[str, Any]) -> dict[str, Any]:
    """Align the 25-key shared PPML result with the 27-key local contract."""
    unknown = sorted(set(result) - set(BASE_RESULT_COLUMNS))
    if unknown:
        raise ValueError(f"Unexpected shared result columns: {unknown}")
    normalized = {
        column: result.get(column, np.nan)
        for column in BASE_RESULT_COLUMNS
    }
    normalized["weight_column"] = ""
    normalized["sum_of_weights"] = np.nan
    return normalized


def attach_pretrend_statuses(
    results: pd.DataFrame,
    pretrends: pd.DataFrame,
) -> pd.DataFrame:
    """Attach both required exact-sample diagnostics to each P10 row."""
    required = {"outcome", "sample", "pretrend_status", "n_obs"}
    test_required = {"outcome", "sample", "pretrend_status"}
    if not test_required.issubset(pretrends.columns):
        missing = sorted(test_required - set(pretrends.columns))
        raise ValueError(f"Pretrend output is missing columns: {missing}")
    columns = ["outcome", "sample", "pretrend_status"]
    if required.issubset(pretrends.columns):
        columns.append("n_obs")
    source = pretrends[columns].copy()
    if source.duplicated(["outcome", "sample"]).any():
        raise RuntimeError("Pretrend outcome-sample keys are not unique")
    status_wide = source.pivot(
        index="outcome",
        columns="sample",
        values="pretrend_status",
    ).reset_index()
    status_wide = status_wide.rename(
        columns={
            "full": "pretrend_status_full",
            "without_2020": "pretrend_status_without_2020",
        }
    )
    if "n_obs" in source.columns:
        nobs_wide = source.pivot(
            index="outcome",
            columns="sample",
            values="n_obs",
        ).reset_index()
        nobs_wide = nobs_wide.rename(
            columns={
                "full": "pretrend_n_obs_full",
                "without_2020": "pretrend_n_obs_without_2020",
            }
        )
        status_wide = audited_merge(
            status_wide,
            nobs_wide,
            merge_id="pnadc_p10_combine_pretrend_status_and_nobs",
            on="outcome",
            how="left",
            validate="one_to_one",
        )
    attached = audited_merge(
        results,
        status_wide,
        merge_id="pnadc_p10_attach_exact_sample_pretrends",
        on="outcome",
        how="left",
        validate="one_to_one",
    )
    status_columns = [
        "pretrend_status_full",
        "pretrend_status_without_2020",
    ]
    if attached[status_columns].isna().any().any():
        raise RuntimeError("P10 is missing an exact-sample pretrend")
    if "pretrend_n_obs_full" in attached.columns:
        estimated = attached["result_status"].eq("estimated")
        mismatch = estimated & (
            pd.to_numeric(attached["n_obs"], errors="coerce")
            != pd.to_numeric(
                attached["pretrend_n_obs_full"],
                errors="coerce",
            )
        )
        if mismatch.any():
            outcomes = attached.loc[mismatch, "outcome"].tolist()
            raise RuntimeError(
                "P10 and P9 complete-case samples differ for "
                f"{outcomes}"
            )
    return attached


def _significance_symbol(adjusted_p_value: float) -> str:
    if not np.isfinite(adjusted_p_value):
        return ""
    if adjusted_p_value < 0.001:
        return "***"
    if adjusted_p_value < 0.01:
        return "**"
    if adjusted_p_value < 0.05:
        return "*"
    return ""


def apply_family_e(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply BH exactly once to the complete registered six-test family."""
    if len(frame) != FAMILY_E_SIZE:
        raise RuntimeError(
            f"Family E requires {FAMILY_E_SIZE} rows; found {len(frame)}"
        )
    expected = {
        str(specification["outcome"]) for specification in OUTCOME_SPECS
    }
    if set(frame["outcome"]) != expected:
        raise RuntimeError("Family E outcome grid is incomplete")
    if frame["outcome"].duplicated().any():
        raise RuntimeError("Family E contains duplicate outcomes")

    result = frame.copy()
    result["nominal_p_value"] = pd.to_numeric(
        result["p_value"],
        errors="coerce",
    )
    result["bh_adjusted_p_value"] = benjamini_hochberg(
        result["nominal_p_value"].to_numpy(),
        family_size=FAMILY_E_SIZE,
    )
    result["family_id"] = "E"
    result["family_size"] = FAMILY_E_SIZE
    result["multiplicity_method"] = "Benjamini-Hochberg"
    result["multiplicity_scope"] = (
        "single adjustment over all six registered PNADc outcomes"
    )
    result["nominal_significant_005"] = (
        result["nominal_p_value"] < 0.05
    )
    result["bh_significant_005"] = (
        result["bh_adjusted_p_value"] < 0.05
    )
    result["stars_suppressed_by_pretrend"] = (
        result["pretrend_status_full"].eq("fail")
        | result["pretrend_status_without_2020"].eq("fail")
    )
    result["stars_allowed"] = (
        ~result["stars_suppressed_by_pretrend"]
        & result["result_status"].eq("estimated")
    )
    result["significance_symbol"] = [
        _significance_symbol(float(p_value)) if allowed else ""
        for p_value, allowed in zip(
            result["bh_adjusted_p_value"],
            result["stars_allowed"],
            strict=True,
        )
    ]
    result["is_reconciliation"] = result["outcome"].eq("ln_renda")
    result["is_principal"] = ~result["is_reconciliation"]
    result["headline_eligible"] = (
        result["is_principal"]
        & result["stars_allowed"]
        & result["bh_significant_005"]
    )
    result["sample_window"] = "2012Q1--2026Q1"
    result["pre_period"] = "2012Q1--2022Q3"
    result["post_period"] = "2023Q1--2026Q1"
    result["excluded_transition_period"] = "2022Q4"
    result["estimand"] = np.where(
        result["arm"].eq("A"),
        (
            "survey-weighted exposed-minus-control post-period "
            "composition differential conditional on COD3 and quarter FE"
        ),
        (
            "treated-minus-control COD3 post-period multiplicative "
            "employment-stock differential conditional on COD3 and quarter FE"
        ),
    )
    result["is_causal_effect"] = False
    return result


def validate_principal_results(frame: pd.DataFrame) -> dict[str, Any]:
    """Validate the complete P10 output contract."""
    expected_outcomes = {
        str(specification["outcome"]) for specification in OUTCOME_SPECS
    }
    if len(frame) != FAMILY_E_SIZE:
        raise RuntimeError("P10 must contain exactly six rows")
    if set(frame["outcome"]) != expected_outcomes:
        raise RuntimeError("P10 outcome grid is incomplete")
    if frame["outcome"].duplicated().any():
        raise RuntimeError("P10 contains duplicate outcomes")
    if not frame["family_id"].eq("E").all():
        raise RuntimeError("P10 contains a non-E multiplicity family")
    if not frame["family_size"].eq(FAMILY_E_SIZE).all():
        raise RuntimeError("P10 family size is not six")
    if not frame.loc[
        frame["outcome"].eq("ln_renda"),
        "is_reconciliation",
    ].all():
        raise RuntimeError("ln_renda is not marked as reconciliation")
    if frame.loc[
        frame["outcome"].eq("ln_renda"),
        "is_principal",
    ].any():
        raise RuntimeError("ln_renda cannot be principal")
    invalid_stars = frame[
        frame["stars_suppressed_by_pretrend"]
        & frame["significance_symbol"].ne("")
    ]
    if not invalid_stars.empty:
        raise RuntimeError("A failed pretrend row contains significance stars")
    return {
        "rows": int(len(frame)),
        "family_id": "E",
        "family_size": FAMILY_E_SIZE,
        "estimated_rows": int(frame["result_status"].eq("estimated").sum()),
        "failed_estimation_rows": int(
            frame["result_status"].eq("failed_estimation").sum()
        ),
        "nominal_rejections_005": int(
            frame["nominal_significant_005"].sum()
        ),
        "bh_rejections_005": int(frame["bh_significant_005"].sum()),
        "stars_published": int(frame["significance_symbol"].ne("").sum()),
    }


def _format_number(value: Any) -> str:
    numeric = float(value)
    return f"{numeric:.6g}" if np.isfinite(numeric) else "NA"


def render_results_report(frame: pd.DataFrame) -> str:
    """Render P10 results with the registered identification limits."""
    lines = [
        "# PNADc Family E principal results",
        "",
        "## Contract",
        "",
        "The estimand is the average post-period exposed--control differential over "
        "2012Q1--2026Q1 with COD3 and calendar-quarter fixed effects and COD3 clustering. "
        "The pre-period is 2012Q1--2022Q3, the post-period is 2023Q1--2026Q1, and "
        "2022Q4 is excluded. This quarterly window differs from every V2 monthly estimand.",
        "",
        "Family E contains six tests. Benjamini--Hochberg is applied once across all six, with nominal "
        "and adjusted p-values shown side by side. Every outcome failed the registered pretrend in "
        "both required samples, so no significance symbol is published and no row is interpreted "
        "causally.",
        "",
        "## Estimates",
        "",
        "| Arm | Outcome | Coefficient | Standard error | Nominal p | Family E BH p | Reconciliation |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in frame.itertuples():
        lines.append(
            f"| {row.arm} | `{row.outcome}` | "
            f"{_format_number(row.coefficient)} | "
            f"{_format_number(row.standard_error)} | "
            f"{_format_number(row.nominal_p_value)} | "
            f"{_format_number(row.bh_adjusted_p_value)} | "
            f"{str(bool(row.is_reconciliation)).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Measurement and reconciliation limits",
            "",
            "The design observes formal--informal composition, not individual worker transitions. "
            "COD3-cluster inference does not implement the full complex survey design, so precision "
            "does not incorporate PNADc strata and primary sampling units.",
            "",
            "`ln_renda` is reconciliation only and is never a principal or headline outcome. The archived "
            "exercise under `archive/etapa5_did_ocupacional/` used `automation_index_cai`, whose 80th "
            "percentile was zero and which classified about 72% of the population as treated. It is not "
            "evidence about the ILO exposure measure used here.",
            "",
        ]
    )
    return "\n".join(lines)


def _failed_result(
    specification: dict[str, Any],
    error: RuntimeError | np.linalg.LinAlgError,
) -> dict[str, Any]:
    outcome = str(specification["outcome"])
    result = {column: np.nan for column in BASE_RESULT_COLUMNS}
    result.update(
        {
            "model_id": f"pnadc_principal_{outcome}",
            "outcome": outcome,
            "term": "post_treat",
            "estimator": specification["estimator"],
            "converged": False,
            "fixed_effects": "cod3 + trimestre_num",
            "cluster_variables": "cod3",
            "controls": "",
            "weight_column": (
                "peso" if specification["arm"] == "A" else ""
            ),
        }
    )
    result["arm"] = specification["arm"]
    result["result_status"] = "failed_estimation"
    result["result_error"] = f"{type(error).__name__}: {error}"
    return result


def _fit_principal_outcome(
    specification: dict[str, Any],
) -> dict[str, Any]:
    outcome = str(specification["outcome"])
    arm = str(specification["arm"])
    if arm == "A":
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
        panel["cod3"] = panel["cod3"].astype("category")
        try:
            fitted, _ = fit_weighted_model(
                panel,
                model_id=f"pnadc_principal_{outcome}",
                outcome=outcome,
                treatment_term="post_treat",
                estimator="ols",
                fixed_effects=("cod3", "trimestre_num"),
                cluster_variables=("cod3",),
                weight_column="peso",
                controls=(),
                principal=True,
            )
            if tuple(fitted) != BASE_RESULT_COLUMNS:
                raise RuntimeError(
                    "Weighted estimator result schema changed before P10"
                )
            result = dict(fitted)
        except (RuntimeError, np.linalg.LinAlgError) as error:
            return _failed_result(specification, error)
        finally:
            del panel
            gc.collect()
    elif arm == "B":
        panel = pd.read_parquet(
            COD3_PANEL_PATH,
            columns=[
                outcome,
                "post_treat",
                "cod3",
                "trimestre_num",
            ],
        )
        panel["cod3"] = panel["cod3"].astype("category")
        try:
            fitted, _ = fit_model(
                panel,
                model_id=f"pnadc_principal_{outcome}",
                outcome=outcome,
                treatment_term="post_treat",
                estimator="ppml",
                fixed_effects=("cod3", "trimestre_num"),
                cluster_variables=("cod3",),
                controls=(),
                principal=True,
            )
            result = normalize_arm_b_result(fitted)
        except (RuntimeError, np.linalg.LinAlgError) as error:
            return _failed_result(specification, error)
        finally:
            del panel
            gc.collect()
    else:
        raise ValueError(f"Unknown PNADc arm: {arm}")
    result["arm"] = arm
    result["result_status"] = "estimated"
    result["result_error"] = ""
    return result


def run_p10() -> dict[str, Any]:
    """Execute P10, apply Family E once, and publish principal results."""
    if not PRETRENDS_PATH.exists() or not PRETRENDS_STATUS_PATH.exists():
        raise FileNotFoundError("P9 outputs are missing")
    pretrend_status = json.loads(
        PRETRENDS_STATUS_PATH.read_text(encoding="utf-8")
    )
    if pretrend_status.get("status") != "pass":
        raise RuntimeError("P9 did not pass its reporting contract")
    pretrends = pd.read_csv(PRETRENDS_PATH)

    rows: list[dict[str, Any]] = []
    for specification in OUTCOME_SPECS:
        print(
            f"P10 fitting {specification['arm']} "
            f"{specification['outcome']}",
            flush=True,
        )
        rows.append(_fit_principal_outcome(specification))
    results = pd.DataFrame(rows)
    results = attach_pretrend_statuses(results, pretrends)
    results = apply_family_e(results)
    order = {
        str(specification["outcome"]): position
        for position, specification in enumerate(OUTCOME_SPECS)
    }
    results["_registered_order"] = results["outcome"].map(order)
    results = (
        results.sort_values("_registered_order")
        .drop(columns="_registered_order")
        .reset_index(drop=True)
    )
    validation = validate_principal_results(results)
    atomic_csv(results, RESULTS_PATH)
    atomic_text(render_results_report(results), RESULTS_REPORT_PATH)
    status = {
        "status": "pass",
        "task": "P10",
        **validation,
        "family_e_adjustment_calls": 1,
        "all_required_pretrends_attached": True,
        "all_pretrends_fail": bool(
            results["pretrend_status_full"].eq("fail").all()
            and results["pretrend_status_without_2020"].eq("fail").all()
        ),
        "treatment_coefficients_computed": True,
        "individual_panel_sha256": sha256_file(INDIVIDUAL_PANEL_PATH),
        "cod3_panel_sha256": sha256_file(COD3_PANEL_PATH),
        "results_sha256": sha256_file(RESULTS_PATH),
    }
    atomic_json(status, RESULTS_STATUS_PATH)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate PNADc Family E principal models.",
    )
    return parser.parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(run_p10(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
