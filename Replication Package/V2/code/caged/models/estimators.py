#!/usr/bin/env python3
"""Shared estimators for the preregistered V2 empirical specifications."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd


CONTEMPORARY_CONTROLS = (
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
)


def _beta_continued_fraction(
    a: float,
    b: float,
    x: float,
) -> float:
    maximum_iterations = 200
    epsilon = 3e-14
    floor = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = floor if abs(d) < floor else d
    d = 1.0 / d
    result = d
    for iteration in range(1, maximum_iterations + 1):
        even = 2 * iteration
        coefficient = (
            iteration
            * (b - iteration)
            * x
            / ((qam + even) * (a + even))
        )
        d = 1.0 + coefficient * d
        d = floor if abs(d) < floor else d
        c = 1.0 + coefficient / c
        c = floor if abs(c) < floor else c
        d = 1.0 / d
        result *= d * c
        coefficient = (
            -(a + iteration)
            * (qab + iteration)
            * x
            / ((a + even) * (qap + even))
        )
        d = 1.0 + coefficient * d
        d = floor if abs(d) < floor else d
        c = 1.0 + coefficient / c
        c = floor if abs(c) < floor else c
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) < epsilon:
            return result
    raise RuntimeError("Incomplete-beta continued fraction did not converge")


def _regularized_incomplete_beta(
    x: float,
    a: float,
    b: float,
) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - (
        front
        * _beta_continued_fraction(b, a, 1.0 - x)
        / b
    )


def student_t_cdf(value: float, degrees_of_freedom: int) -> float:
    if degrees_of_freedom <= 0:
        raise ValueError("Student-t degrees of freedom must be positive")
    if value == 0:
        return 0.5
    x = degrees_of_freedom / (
        degrees_of_freedom + value * value
    )
    tail = 0.5 * _regularized_incomplete_beta(
        x,
        degrees_of_freedom / 2.0,
        0.5,
    )
    return 1.0 - tail if value > 0 else tail


def student_t_ppf(
    probability: float,
    degrees_of_freedom: int,
) -> float:
    if not 0 < probability < 1:
        raise ValueError("Student-t probability must be between zero and one")
    if probability == 0.5:
        return 0.0
    if probability < 0.5:
        return -student_t_ppf(1.0 - probability, degrees_of_freedom)
    lower = 0.0
    upper = 1.0
    while student_t_cdf(upper, degrees_of_freedom) < probability:
        upper *= 2.0
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        if student_t_cdf(midpoint, degrees_of_freedom) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def validate_principal_controls(controls: Sequence[str]) -> None:
    forbidden = sorted(set(controls) & set(CONTEMPORARY_CONTROLS))
    if forbidden:
        raise ValueError(
            "Principal models cannot contain contemporary composition "
            f"controls: {forbidden}"
        )


def build_formula(
    outcome: str,
    treatment_term: str,
    fixed_effects: Sequence[str],
    controls: Sequence[str] = (),
) -> str:
    right_hand_side = " + ".join(
        [treatment_term, *controls]
    )
    fixed = " + ".join(fixed_effects)
    return (
        f"{outcome} ~ {right_hand_side} | {fixed}"
        if fixed
        else f"{outcome} ~ {right_hand_side}"
    )


def cluster_t_inference(
    coefficient: float,
    standard_error: float,
    cluster_counts: dict[str, int],
    *,
    alpha: float = 0.05,
) -> dict[str, float | int]:
    if not cluster_counts:
        raise ValueError("At least one cluster dimension is required")
    minimum_clusters = min(cluster_counts.values())
    if minimum_clusters < 2:
        raise ValueError("Cluster inference requires at least two clusters")
    cluster_df = minimum_clusters - 1
    critical = student_t_ppf(1 - alpha / 2, cluster_df)
    statistic = coefficient / standard_error
    p_value = float(
        2
        * (
            1.0
            - student_t_cdf(abs(statistic), cluster_df)
        )
    )
    return {
        "cluster_df": cluster_df,
        "critical_value": critical,
        "t_statistic": statistic,
        "p_value": p_value,
        "ci_low": coefficient - critical * standard_error,
        "ci_high": coefficient + critical * standard_error,
    }


def _formula_columns(
    outcome: str,
    treatment_term: str,
    controls: Sequence[str],
    fixed_effects: Sequence[str],
    cluster_variables: Sequence[str],
) -> list[str]:
    columns = [outcome, treatment_term, *controls, *cluster_variables]
    for fixed_effect in fixed_effects:
        columns.extend(fixed_effect.split("^"))
    return list(dict.fromkeys(columns))


def fit_model(
    data: pd.DataFrame,
    *,
    model_id: str,
    outcome: str,
    treatment_term: str,
    estimator: str,
    fixed_effects: Sequence[str],
    cluster_variables: Sequence[str],
    controls: Sequence[str] = (),
    principal: bool = False,
    separation_check: Sequence[str] = ("fe", "ir"),
) -> tuple[dict[str, Any], Any]:
    if estimator not in {"ppml", "ols"}:
        raise ValueError(f"Unsupported estimator: {estimator}")
    if principal:
        validate_principal_controls(controls)
    required = _formula_columns(
        outcome,
        treatment_term,
        controls,
        fixed_effects,
        cluster_variables,
    )
    missing_columns = sorted(set(required) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Model data is missing columns: {missing_columns}")
    model_data = data.dropna(subset=required).copy()
    if model_data.empty:
        raise RuntimeError(f"No complete cases for model {model_id}")
    if estimator == "ppml" and (model_data[outcome] < 0).any():
        raise ValueError("PPML outcome must be weakly positive")

    formula = build_formula(
        outcome,
        treatment_term,
        fixed_effects,
        controls,
    )
    vcov = {"CRV1": " + ".join(cluster_variables)}
    import pyfixest as pf

    if estimator == "ppml":
        model = pf.fepois(
            formula,
            data=model_data,
            vcov=vcov,
            separation_check=list(separation_check),
        )
        converged = bool(getattr(model, "_convergence", False))
        if not converged:
            raise RuntimeError(f"PPML did not converge: {model_id}")
    else:
        model = pf.feols(
            formula,
            data=model_data,
            vcov=vcov,
        )
        converged = True

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
        "separation_dropped": int(
            getattr(model, "n_separation_na", 0)
        ),
        "converged": converged,
        "formula": formula,
        "fixed_effects": " + ".join(fixed_effects),
        "cluster_variables": " + ".join(cluster_variables),
        "controls": " + ".join(controls),
        "effect_percent": (
            100.0 * math.expm1(coefficient)
            if estimator == "ppml"
            else np.nan
        ),
    }
    return result, model


def fit_model_grid(
    data: pd.DataFrame,
    specifications: Sequence[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for specification in specifications:
        result, _ = fit_model(data, **specification)
        rows.append(result)
    return pd.DataFrame(rows)
