#!/usr/bin/env python3
"""Registered non-principal sensitivities for PNADc Front 2."""

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

from estimators import cluster_t_inference, fit_model  # noqa: E402
from merge_audit import audited_merge  # noqa: E402
from .panels import (  # noqa: E402
    build_cod3_panel,
    build_individual_quarter,
)
from .pnadc_estimation import (  # noqa: E402
    BASE_RESULT_COLUMNS,
    OUTCOME_SPECS,
    normalize_arm_b_result,
)
from .pnadc_pretrends import _rescale_collapsed_crv1  # noqa: E402
from .stage0 import (  # noqa: E402
    ILO_EXPECTED_SHA256,
    ILO_PATH,
    atomic_csv,
    atomic_json,
    atomic_text,
    build_ilo_crosswalk,
    sha256_file,
)
from .weighted_estimator import fit_weighted_model  # noqa: E402


SENSITIVITY_ORDER = (
    "transition_2022q4_as_pre",
    "without_2020",
    "cod3_threshold_075",
    "arm_a_cod3_treatment",
)

INDIVIDUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_pnadc_individual.parquet"
COD3_PANEL_PATH = FRONT_ROOT / "data" / "painel_pnadc_cod3.parquet"
VINTAGE_DIR = FRONT_ROOT / "data" / "vintage"
TREATMENT_PATH = FRONT_ROOT / "results" / "pnadc_treatment_cod3.csv"
PRETRENDS_PATH = FRONT_ROOT / "results" / "pnadc_pretrends.csv"
P10_RESULTS_PATH = FRONT_ROOT / "results" / "pnadc_results.csv"
P10_STATUS_PATH = FRONT_ROOT / "results" / "pnadc_results_status.json"
SENSITIVITIES_PATH = FRONT_ROOT / "results" / "pnadc_sensitivities.csv"
SENSITIVITIES_REPORT_PATH = (
    FRONT_ROOT / "results" / "PNADC_SENSITIVITIES.md"
)
SENSITIVITIES_STATUS_PATH = (
    FRONT_ROOT / "results" / "pnadc_sensitivities_status.json"
)


def classify_cod3_threshold(
    treatment: pd.DataFrame,
    *,
    threshold: float,
) -> pd.DataFrame:
    """Apply a declared alternative COD3 exposure-share threshold."""
    if not 0 < threshold <= 1:
        raise ValueError("COD3 threshold must be in (0, 1]")
    required = {"cod3", "exposed_employment_share"}
    missing = sorted(required - set(treatment.columns))
    if missing:
        raise ValueError(f"Treatment table is missing columns: {missing}")
    result = treatment.copy()
    result["cod3"] = result["cod3"].astype("string")
    if result["cod3"].duplicated().any():
        raise ValueError("Treatment table contains duplicate COD3")
    shares = pd.to_numeric(
        result["exposed_employment_share"],
        errors="raise",
    )
    if (~np.isfinite(shares) | ~shares.between(0, 1)).any():
        raise ValueError("Exposure shares must be finite and in [0, 1]")
    result["treatment_status"] = "intermediate"
    result.loc[shares.eq(0.0), "treatment_status"] = "control"
    result.loc[shares.ge(threshold), "treatment_status"] = "treated"
    result["treated_cod3"] = result["treatment_status"].map(
        {"treated": 1.0, "control": 0.0}
    )
    return result


def apply_cod3_treatment_to_arm_a(
    individual: pd.DataFrame,
    treatment: pd.DataFrame,
) -> pd.DataFrame:
    """Replace row-level gradient treatment with frozen COD3 treatment."""
    required = {"cod3", "treatment_status", "treated_cod3"}
    missing = sorted(required - set(treatment.columns))
    if missing:
        raise ValueError(f"Treatment table is missing columns: {missing}")
    contract = treatment[
        ["cod3", "treatment_status", "treated_cod3"]
    ].copy()
    contract["cod3"] = contract["cod3"].astype("string")
    data = individual.copy()
    data["cod3"] = data["cod3"].astype("string")
    attached = audited_merge(
        data,
        contract,
        merge_id="pnadc_p11_attach_cod3_treatment_to_arm_a",
        on="cod3",
        how="left",
        validate="many_to_one",
    )
    if attached["treatment_status"].isna().any():
        missing_cod3 = sorted(
            attached.loc[
                attached["treatment_status"].isna(),
                "cod3",
            ].unique()
        )
        raise RuntimeError(
            f"Arm A COD3 treatment is missing for {missing_cod3}"
        )
    result = attached.loc[
        attached["treatment_status"].isin(["treated", "control"])
    ].copy()
    result["treated"] = (
        pd.to_numeric(result["treated_cod3"], errors="raise")
        .astype("int8")
    )
    result["post_treat"] = (
        result["post"].astype("int8") * result["treated"]
    ).astype("int8")
    return result.drop(
        columns=["treatment_status", "treated_cod3"]
    ).reset_index(drop=True)


def apply_cod3_treatment_to_arm_b(
    stock: pd.DataFrame,
    treatment: pd.DataFrame,
) -> pd.DataFrame:
    """Replace the principal COD3 status with an alternative threshold."""
    required = {"cod3", "treatment_status", "treated_cod3"}
    missing = sorted(required - set(treatment.columns))
    if missing:
        raise ValueError(f"Treatment table is missing columns: {missing}")
    data = stock.drop(
        columns=["treatment_status", "treated", "post_treat"],
        errors="ignore",
    ).copy()
    data["cod3"] = data["cod3"].astype("string")
    contract = treatment[
        ["cod3", "treatment_status", "treated_cod3"]
    ].copy()
    contract["cod3"] = contract["cod3"].astype("string")
    attached = audited_merge(
        data,
        contract,
        merge_id="pnadc_p11_attach_alternative_cod3_treatment_to_arm_b",
        on="cod3",
        how="left",
        validate="many_to_one",
    )
    if attached["treatment_status"].isna().any():
        raise RuntimeError("Arm B alternative treatment is incomplete")
    result = attached.loc[
        attached["treatment_status"].isin(["treated", "control"])
    ].copy()
    result["treated"] = (
        pd.to_numeric(result["treated_cod3"], errors="raise")
        .astype("int8")
    )
    result["post_treat"] = (
        result["post"].astype("int8") * result["treated"]
    ).astype("int8")
    return result.drop(columns="treated_cod3").reset_index(drop=True)


def build_sensitivity_grid() -> list[dict[str, Any]]:
    """Return only the 18 outcome-sensitivity pairs to which the changes apply."""
    rows: list[dict[str, Any]] = []
    for sensitivity_id in SENSITIVITY_ORDER:
        for specification in OUTCOME_SPECS:
            arm = str(specification["arm"])
            if sensitivity_id == "cod3_threshold_075" and arm != "B":
                continue
            if sensitivity_id == "arm_a_cod3_treatment" and arm != "A":
                continue
            rows.append(
                {
                    "sensitivity_id": sensitivity_id,
                    "arm": arm,
                    "outcome": specification["outcome"],
                    "estimator": specification["estimator"],
                    "is_principal": False,
                    "is_reconciliation": bool(
                        specification["is_reconciliation"]
                    ),
                }
            )
    if len(rows) != 18:
        raise RuntimeError("Registered P11 grid must contain 18 rows")
    return rows


def _collapse_weighted_static_data(
    data: pd.DataFrame,
    *,
    outcome: str,
) -> tuple[pd.DataFrame, int, int]:
    required = {
        "cod3",
        "trimestre_num",
        "post_treat",
        "peso",
        outcome,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Static data is missing columns: {missing}")
    input_observations = int(len(data))
    complete = data.dropna(subset=list(required)).copy()
    weights = pd.to_numeric(complete["peso"], errors="raise")
    if (~np.isfinite(weights) | weights.le(0)).any():
        raise ValueError("Survey weights must be finite and positive")
    complete["_weighted_outcome"] = (
        weights * pd.to_numeric(complete[outcome], errors="raise")
    )
    keys = ["cod3", "trimestre_num", "post_treat"]
    collapsed = (
        complete.groupby(keys, as_index=False, observed=True)
        .agg(
            cell_weight=("peso", "sum"),
            weighted_outcome=("_weighted_outcome", "sum"),
            source_observations=(outcome, "size"),
        )
        .sort_values(["trimestre_num", "cod3", "post_treat"])
        .reset_index(drop=True)
    )
    collapsed[outcome] = (
        collapsed["weighted_outcome"] / collapsed["cell_weight"]
    )
    source_observations = int(collapsed["source_observations"].sum())
    if source_observations != len(complete):
        raise RuntimeError("Static sufficient statistics lost observations")
    return collapsed, input_observations, source_observations


def fit_collapsed_weighted_static_model(
    data: pd.DataFrame,
    *,
    model_id: str,
    outcome: str,
) -> tuple[dict[str, Any], Any]:
    """Fit an exact memory-safe individual WLS sensitivity."""
    collapsed, input_observations, source_observations = (
        _collapse_weighted_static_data(data, outcome=outcome)
    )
    result, model = fit_weighted_model(
        collapsed,
        model_id=model_id,
        outcome=outcome,
        treatment_term="post_treat",
        estimator="ols",
        fixed_effects=("cod3", "trimestre_num"),
        cluster_variables=("cod3",),
        weight_column="cell_weight",
        controls=(),
        principal=False,
    )
    _rescale_collapsed_crv1(
        model,
        source_observations=source_observations,
    )
    tidy = model.tidy()
    if "post_treat" not in tidy.index:
        raise RuntimeError("Static treatment term was not estimated")
    term = tidy.loc["post_treat"]
    coefficient = float(term["Estimate"])
    standard_error = float(term["Std. Error"])
    cluster_counts = {
        "cod3": int(collapsed["cod3"].nunique())
    }
    inference = cluster_t_inference(
        coefficient,
        standard_error,
        cluster_counts,
    )
    result.update(
        {
            "coefficient": coefficient,
            "standard_error": standard_error,
            "ci_low": inference["ci_low"],
            "ci_high": inference["ci_high"],
            "p_value": inference["p_value"],
            "cluster_df": inference["cluster_df"],
            "n_obs": source_observations,
            "input_cells": input_observations,
            "complete_case_cells": source_observations,
            "cells_dropped": input_observations - source_observations,
            "cells_dropped_missing": (
                input_observations - source_observations
            ),
            "cells_dropped_estimator": 0,
            "weight_column": "peso",
            "sum_of_weights": float(collapsed["cell_weight"].sum()),
        }
    )
    if tuple(result) != BASE_RESULT_COLUMNS:
        raise RuntimeError("Sensitivity result schema differs from P10")
    return result, model


def _format_number(value: Any) -> str:
    numeric = float(value)
    return f"{numeric:.6g}" if np.isfinite(numeric) else "NA"


def render_sensitivities_report(frame: pd.DataFrame) -> str:
    """Render P11 without promoting any alternative specification."""
    lines = [
        "# PNADc registered sensitivities",
        "",
        "The sensitivity hierarchy was frozen before estimation. These alternatives are reported beside "
        "the principal Family E results and are never promoted because they appear more favorable. "
        "They remain outside Family E, show nominal p-values only, and publish no significance symbols.",
        "",
        "| Sensitivity | Arm | Outcome | Coefficient | Standard error | Nominal p | Status |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in frame.itertuples():
        lines.append(
            f"| `{row.sensitivity_id}` | {row.arm} | `{row.outcome}` | "
            f"{_format_number(row.coefficient)} | "
            f"{_format_number(row.standard_error)} | "
            f"{_format_number(row.p_value)} | `{row.result_status}` |"
        )
    lines.extend(
        [
            "",
            "The design observes composition, not individual worker transitions. `ln_renda` remains "
            "reconciliation only. No sensitivity changes the registered estimand hierarchy.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_sensitivity_results(frame: pd.DataFrame) -> dict[str, Any]:
    """Validate the complete 18-row P11 output and frozen hierarchy."""
    expected = {
        (row["sensitivity_id"], row["outcome"])
        for row in build_sensitivity_grid()
    }
    observed = set(
        zip(
            frame["sensitivity_id"],
            frame["outcome"],
            strict=True,
        )
    )
    if observed != expected or len(frame) != len(expected):
        raise RuntimeError("P11 sensitivity grid is incomplete")
    if frame.duplicated(["sensitivity_id", "outcome"]).any():
        raise RuntimeError("P11 contains duplicate sensitivity rows")
    if frame["is_principal"].astype(bool).any():
        raise RuntimeError("A P11 row is incorrectly marked principal")
    if not frame["family_id"].eq("none").all():
        raise RuntimeError("Sensitivities cannot enter a BH family")
    if pd.to_numeric(
        frame["bh_adjusted_p_value"],
        errors="coerce",
    ).notna().any():
        raise RuntimeError("A sensitivity has an adjusted p-value")
    if frame["significance_symbol"].fillna("").ne("").any():
        raise RuntimeError("A sensitivity has a significance symbol")
    if not frame["hierarchy_frozen_before_estimation"].astype(bool).all():
        raise RuntimeError("Sensitivity hierarchy is not frozen")
    counts = (
        frame.groupby("sensitivity_id")["outcome"]
        .nunique()
        .sort_index()
    )
    return {
        "rows": int(len(frame)),
        "estimated_rows": int(frame["result_status"].eq("estimated").sum()),
        "failed_estimation_rows": int(
            frame["result_status"].eq("failed_estimation").sum()
        ),
        "principal_rows": int(frame["is_principal"].astype(bool).sum()),
        "stars_published": int(
            frame["significance_symbol"].fillna("").ne("").sum()
        ),
        "models_by_sensitivity": {
            str(key): int(value) for key, value in counts.items()
        },
    }


def _failed_result(
    *,
    sensitivity_id: str,
    arm: str,
    outcome: str,
    estimator: str,
    error: RuntimeError | np.linalg.LinAlgError,
) -> dict[str, Any]:
    result = {column: np.nan for column in BASE_RESULT_COLUMNS}
    result.update(
        {
            "model_id": f"pnadc_{sensitivity_id}_{outcome}",
            "outcome": outcome,
            "term": "post_treat",
            "estimator": estimator,
            "converged": False,
            "fixed_effects": "cod3 + trimestre_num",
            "cluster_variables": "cod3",
            "controls": "",
            "weight_column": "peso" if arm == "A" else "",
        }
    )
    result["result_status"] = "failed_estimation"
    result["result_error"] = f"{type(error).__name__}: {error}"
    return result


def _fit_arm_a_sensitivity(
    data: pd.DataFrame,
    *,
    sensitivity_id: str,
    outcome: str,
) -> dict[str, Any]:
    try:
        result, _ = fit_collapsed_weighted_static_model(
            data,
            model_id=f"pnadc_{sensitivity_id}_{outcome}",
            outcome=outcome,
        )
    except (RuntimeError, np.linalg.LinAlgError) as error:
        return _failed_result(
            sensitivity_id=sensitivity_id,
            arm="A",
            outcome=outcome,
            estimator="ols",
            error=error,
        )
    result["result_status"] = "estimated"
    result["result_error"] = ""
    return result


def _fit_arm_b_sensitivity(
    data: pd.DataFrame,
    *,
    sensitivity_id: str,
    outcome: str,
) -> dict[str, Any]:
    try:
        shared, _ = fit_model(
            data,
            model_id=f"pnadc_{sensitivity_id}_{outcome}",
            outcome=outcome,
            treatment_term="post_treat",
            estimator="ppml",
            fixed_effects=("cod3", "trimestre_num"),
            cluster_variables=("cod3",),
            controls=(),
            principal=False,
        )
        result = normalize_arm_b_result(shared)
    except (RuntimeError, np.linalg.LinAlgError) as error:
        return _failed_result(
            sensitivity_id=sensitivity_id,
            arm="B",
            outcome=outcome,
            estimator="ppml",
            error=error,
        )
    result["result_status"] = "estimated"
    result["result_error"] = ""
    return result


def _decorate_result(
    result: dict[str, Any],
    *,
    sensitivity_id: str,
    arm: str,
    outcome: str,
    pretrend_status: str,
    pretrend_n_obs: float,
) -> dict[str, Any]:
    windows = {
        "transition_2022q4_as_pre": (
            "2012Q1--2026Q1; 2022Q4 assigned to pre"
        ),
        "without_2020": (
            "2012Q1--2026Q1; 2020 and 2022Q4 excluded"
        ),
        "cod3_threshold_075": (
            "2012Q1--2026Q1; 2022Q4 excluded"
        ),
        "arm_a_cod3_treatment": (
            "2012Q1--2026Q1; 2022Q4 excluded"
        ),
    }
    treatment_rules = {
        "transition_2022q4_as_pre": "principal treatment; transition reassigned",
        "without_2020": "principal treatment; 2020 excluded",
        "cod3_threshold_075": "COD3 treated if exposed share >= 0.75",
        "arm_a_cod3_treatment": (
            "Arm A treatment assigned by principal COD3 threshold"
        ),
    }
    row = dict(result)
    row.update(
        {
            "sensitivity_id": sensitivity_id,
            "arm": arm,
            "sample_window": windows[sensitivity_id],
            "treatment_rule": treatment_rules[sensitivity_id],
            "pretrend_status": pretrend_status,
            "pretrend_n_obs": pretrend_n_obs,
            "nominal_p_value": result["p_value"],
            "bh_adjusted_p_value": np.nan,
            "family_id": "none",
            "family_size": 0,
            "multiplicity_method": "not_applied_sensitivity",
            "significance_symbol": "",
            "stars_allowed": False,
            "is_principal": False,
            "is_reconciliation": outcome == "ln_renda",
            "hierarchy_frozen_before_estimation": True,
            "headline_eligible": False,
            "is_causal_effect": False,
            "composition_not_transition": True,
            "computational_sufficient_statistics": arm == "A",
        }
    )
    return row


def _build_transition_samples(
    treatment: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if sha256_file(ILO_PATH) != ILO_EXPECTED_SHA256:
        raise RuntimeError("ILO workbook changed before P11")
    crosswalk = build_ilo_crosswalk(pd.read_excel(ILO_PATH))
    raw = pd.read_parquet(VINTAGE_DIR / "pnadc_2022q4.parquet")
    individual, _ = build_individual_quarter(
        raw,
        crosswalk,
        include_transition_as_pre=True,
    )
    stock = build_cod3_panel(
        individual,
        treatment,
        include_transition_as_pre=True,
    )
    if {"cod4", "cod_ocupacao"} & set(individual.columns):
        raise RuntimeError("COD4 reached the transition sensitivity")
    return individual, stock


def _arm_a_sensitivity_rows(
    *,
    treatment: pd.DataFrame,
    transition: pd.DataFrame,
    pretrend_statuses: dict[str, str],
    pretrend_nobs: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    outcomes = [
        str(specification["outcome"])
        for specification in OUTCOME_SPECS
        if specification["arm"] == "A"
    ]
    for outcome in outcomes:
        print(f"P11 fitting Arm A sensitivities for {outcome}", flush=True)
        columns = [
            "ano",
            "cod3",
            "trimestre_num",
            "post",
            "treated",
            "post_treat",
            "peso",
            outcome,
        ]
        base = pd.read_parquet(INDIVIDUAL_PANEL_PATH, columns=columns)

        transition_sample = pd.concat(
            [base, transition[columns]],
            ignore_index=True,
        )
        fitted = _fit_arm_a_sensitivity(
            transition_sample,
            sensitivity_id="transition_2022q4_as_pre",
            outcome=outcome,
        )
        rows.append(
            _decorate_result(
                fitted,
                sensitivity_id="transition_2022q4_as_pre",
                arm="A",
                outcome=outcome,
                pretrend_status="not_available",
                pretrend_n_obs=np.nan,
            )
        )
        del transition_sample
        gc.collect()

        without_2020 = base.loc[~base["ano"].eq(2020)].copy()
        fitted = _fit_arm_a_sensitivity(
            without_2020,
            sensitivity_id="without_2020",
            outcome=outcome,
        )
        rows.append(
            _decorate_result(
                fitted,
                sensitivity_id="without_2020",
                arm="A",
                outcome=outcome,
                pretrend_status=pretrend_statuses[outcome],
                pretrend_n_obs=pretrend_nobs[outcome],
            )
        )
        del without_2020
        gc.collect()

        cod3_treatment = apply_cod3_treatment_to_arm_a(base, treatment)
        fitted = _fit_arm_a_sensitivity(
            cod3_treatment,
            sensitivity_id="arm_a_cod3_treatment",
            outcome=outcome,
        )
        rows.append(
            _decorate_result(
                fitted,
                sensitivity_id="arm_a_cod3_treatment",
                arm="A",
                outcome=outcome,
                pretrend_status="not_available",
                pretrend_n_obs=np.nan,
            )
        )
        del cod3_treatment
        del base
        gc.collect()
    return rows


def _arm_b_sensitivity_rows(
    *,
    threshold_treatment: pd.DataFrame,
    transition: pd.DataFrame,
    pretrend_statuses: dict[str, str],
    pretrend_nobs: dict[str, int],
) -> list[dict[str, Any]]:
    base = pd.read_parquet(COD3_PANEL_PATH)
    samples = {
        "transition_2022q4_as_pre": pd.concat(
            [base, transition],
            ignore_index=True,
        ),
        "without_2020": base.loc[~base["ano"].eq(2020)].copy(),
        "cod3_threshold_075": apply_cod3_treatment_to_arm_b(
            base,
            threshold_treatment,
        ),
    }
    rows: list[dict[str, Any]] = []
    outcomes = [
        str(specification["outcome"])
        for specification in OUTCOME_SPECS
        if specification["arm"] == "B"
    ]
    for sensitivity_id, sample in samples.items():
        for outcome in outcomes:
            print(
                f"P11 fitting Arm B {sensitivity_id} {outcome}",
                flush=True,
            )
            fitted = _fit_arm_b_sensitivity(
                sample,
                sensitivity_id=sensitivity_id,
                outcome=outcome,
            )
            rows.append(
                _decorate_result(
                    fitted,
                    sensitivity_id=sensitivity_id,
                    arm="B",
                    outcome=outcome,
                    pretrend_status=(
                        pretrend_statuses[outcome]
                        if sensitivity_id == "without_2020"
                        else "not_available"
                    ),
                    pretrend_n_obs=(
                        pretrend_nobs[outcome]
                        if sensitivity_id == "without_2020"
                        else np.nan
                    ),
                )
            )
    return rows


def run_p11() -> dict[str, Any]:
    """Execute all four declared, non-principal sensitivities."""
    if not P10_STATUS_PATH.exists() or not P10_RESULTS_PATH.exists():
        raise FileNotFoundError("P10 outputs are missing")
    p10_status = json.loads(P10_STATUS_PATH.read_text(encoding="utf-8"))
    if p10_status.get("status") != "pass":
        raise RuntimeError("P10 did not pass")
    pretrends = pd.read_csv(PRETRENDS_PATH)
    without = pretrends.loc[
        pretrends["sample"].eq("without_2020")
    ].set_index("outcome")
    pretrend_statuses = without["pretrend_status"].astype(str).to_dict()
    pretrend_nobs = without["n_obs"].astype(int).to_dict()

    treatment = pd.read_csv(TREATMENT_PATH, dtype={"cod3": "string"})
    threshold_treatment = classify_cod3_threshold(
        treatment,
        threshold=0.75,
    )
    transition_a, transition_b = _build_transition_samples(treatment)
    rows = _arm_a_sensitivity_rows(
        treatment=treatment,
        transition=transition_a,
        pretrend_statuses=pretrend_statuses,
        pretrend_nobs=pretrend_nobs,
    )
    rows.extend(
        _arm_b_sensitivity_rows(
            threshold_treatment=threshold_treatment,
            transition=transition_b,
            pretrend_statuses=pretrend_statuses,
            pretrend_nobs=pretrend_nobs,
        )
    )
    results = pd.DataFrame(rows)
    sensitivity_order = {
        value: position
        for position, value in enumerate(SENSITIVITY_ORDER)
    }
    outcome_order = {
        str(specification["outcome"]): position
        for position, specification in enumerate(OUTCOME_SPECS)
    }
    results["_sensitivity_order"] = results["sensitivity_id"].map(
        sensitivity_order
    )
    results["_outcome_order"] = results["outcome"].map(outcome_order)
    results = (
        results.sort_values(["_sensitivity_order", "_outcome_order"])
        .drop(columns=["_sensitivity_order", "_outcome_order"])
        .reset_index(drop=True)
    )
    without_rows = results["sensitivity_id"].eq("without_2020")
    nobs_mismatch = without_rows & (
        pd.to_numeric(results["n_obs"], errors="coerce")
        != pd.to_numeric(results["pretrend_n_obs"], errors="coerce")
    )
    if nobs_mismatch.any():
        raise RuntimeError(
            "P11 without-2020 samples do not match P9 diagnostics"
        )
    validation = validate_sensitivity_results(results)
    atomic_csv(results, SENSITIVITIES_PATH)
    atomic_text(
        render_sensitivities_report(results),
        SENSITIVITIES_REPORT_PATH,
    )
    status = {
        "status": "pass",
        "task": "P11",
        **validation,
        "sensitivity_bh_adjustment_calls": 0,
        "hierarchy_frozen_before_estimation": True,
        "without_2020_samples_match_p9": True,
        "transition_arm_a_rows": int(len(transition_a)),
        "transition_arm_b_cells": int(len(transition_b)),
        "threshold_075_treated_cod3": int(
            threshold_treatment["treatment_status"].eq("treated").sum()
        ),
        "threshold_075_control_cod3": int(
            threshold_treatment["treatment_status"].eq("control").sum()
        ),
        "principal_results_sha256": sha256_file(P10_RESULTS_PATH),
        "sensitivities_sha256": sha256_file(SENSITIVITIES_PATH),
        "treatment_coefficients_computed": True,
    }
    atomic_json(status, SENSITIVITIES_STATUS_PATH)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate registered PNADc sensitivities.",
    )
    return parser.parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(run_p11(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
