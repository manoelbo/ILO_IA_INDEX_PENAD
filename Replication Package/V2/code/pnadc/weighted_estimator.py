#!/usr/bin/env python3
"""Local weighted OLS adapter for the preregistered PNADc models."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


sys.dont_write_bytecode = True

V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
sys.path.insert(0, str(V2_ROOT / "code" / "caged" / "models"))

from estimators import (  # noqa: E402
    _formula_columns,
    build_formula,
    cluster_t_inference,
    validate_principal_controls,
)


def fit_weighted_model(
    data: pd.DataFrame,
    *,
    model_id: str,
    outcome: str,
    treatment_term: str,
    estimator: str,
    fixed_effects: Sequence[str],
    cluster_variables: Sequence[str],
    weight_column: str,
    controls: Sequence[str] = (),
    principal: bool = False,
    separation_check: Sequence[str] = ("fe", "ir"),
) -> tuple[dict[str, Any], Any]:
    """Fit the preregistered weighted OLS model with the shared result schema."""
    del separation_check
    if estimator == "ppml":
        raise ValueError(
            "Weighted PPML is not supported by pyfixest 0.40.1; "
            "use the shared unweighted fit_model path preregistered for Arm B."
        )
    if estimator != "ols":
        raise ValueError(f"Unsupported weighted estimator: {estimator}")
    if principal:
        validate_principal_controls(controls)

    required = [
        *_formula_columns(
            outcome,
            treatment_term,
            controls,
            fixed_effects,
            cluster_variables,
        ),
        weight_column,
    ]
    required = list(dict.fromkeys(required))
    missing_columns = sorted(set(required) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Model data is missing columns: {missing_columns}")

    model_data = data.dropna(subset=required).copy()
    if model_data.empty:
        raise RuntimeError(f"No complete cases for model {model_id}")
    model_data[weight_column] = pd.to_numeric(
        model_data[weight_column],
        errors="raise",
    )
    if (
        ~np.isfinite(model_data[weight_column])
        | model_data[weight_column].le(0)
    ).any():
        raise ValueError("Analytic weights must be finite and strictly positive")

    formula = build_formula(
        outcome,
        treatment_term,
        fixed_effects,
        controls,
    )
    vcov = {"CRV1": " + ".join(cluster_variables)}

    import pyfixest as pf

    model = pf.feols(
        formula,
        data=model_data,
        vcov=vcov,
        weights=weight_column,
    )
    tidy = model.tidy()
    if treatment_term not in tidy.index:
        raise RuntimeError(
            f"Treatment term was not estimated: {treatment_term}"
        )

    term = tidy.loc[treatment_term]
    coefficient = float(term["Estimate"])
    standard_error = float(term["Std. Error"])
    used_data = getattr(model, "_data", model_data)
    cluster_counts = {
        variable: int(used_data[variable].nunique())
        for variable in cluster_variables
    }
    inference = cluster_t_inference(
        coefficient,
        standard_error,
        cluster_counts,
    )
    n_obs = int(model._N)
    complete_cases = int(len(model_data))
    result: dict[str, Any] = {
        "model_id": model_id,
        "outcome": outcome,
        "term": treatment_term,
        "estimator": estimator,
        "coefficient": coefficient,
        "standard_error": standard_error,
        "ci_low": inference["ci_low"],
        "ci_high": inference["ci_high"],
        "p_value": inference["p_value"],
        "cluster_df": inference["cluster_df"],
        "cluster_counts": json.dumps(
            cluster_counts,
            sort_keys=True,
        ),
        "minimum_clusters": min(cluster_counts.values()),
        "n_obs": n_obs,
        "input_cells": int(len(data)),
        "complete_case_cells": complete_cases,
        "cells_dropped": int(len(data) - n_obs),
        "cells_dropped_missing": int(len(data) - complete_cases),
        "cells_dropped_estimator": int(complete_cases - n_obs),
        "separation_dropped": 0,
        "converged": True,
        "formula": formula,
        "fixed_effects": " + ".join(fixed_effects),
        "cluster_variables": " + ".join(cluster_variables),
        "controls": " + ".join(controls),
        "effect_percent": np.nan,
        "weight_column": weight_column,
        "sum_of_weights": float(used_data[weight_column].sum()),
    }
    return result, model
