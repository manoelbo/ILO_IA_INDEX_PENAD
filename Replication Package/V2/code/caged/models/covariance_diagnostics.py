#!/usr/bin/env python3
"""Numerical diagnostics shared by event-study pretrend estimators."""

from __future__ import annotations

import numpy as np


RANK_DEFICIENT_STATUS = "not_interpretable_rank_deficient"


def lead_covariance_diagnostics(
    covariance: np.ndarray,
) -> dict[str, float | int | bool]:
    """Describe whether a lead-covariance block supports inversion.

    Positive semidefiniteness and numerical rank answer different questions.
    A matrix can be PSD but singular, in which case a Wald statistic based on
    a direct inverse is not identified. The rank tolerance is stated rather
    than delegated to a library default so Python and R apply the same rule.
    """

    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Lead covariance must be a square matrix")
    if matrix.shape[0] == 0 or not np.isfinite(matrix).all():
        raise ValueError("Lead covariance must be finite and non-empty")
    symmetric = 0.5 * (matrix + matrix.T)
    eigenvalues = np.linalg.eigvalsh(symmetric)
    singular_values = np.linalg.svd(symmetric, compute_uv=False)
    maximum_singular_value = float(singular_values.max())
    rank_tolerance = float(
        max(symmetric.shape)
        * np.finfo(float).eps
        * maximum_singular_value
    )
    rank = int(np.sum(singular_values > rank_tolerance))
    dimension = int(symmetric.shape[0])
    full_rank = bool(rank == dimension)
    condition_number = (
        float(maximum_singular_value / singular_values.min())
        if full_rank
        else float("inf")
    )
    minimum_eigenvalue = float(eigenvalues.min())
    scale = float(np.abs(np.diag(symmetric)).max())
    psd_tolerance = float(-1e-8 * max(scale, 1.0))
    return {
        "lead_covariance_dimension": dimension,
        "lead_covariance_rank": rank,
        "lead_covariance_rank_tolerance": rank_tolerance,
        "lead_covariance_full_rank": full_rank,
        "lead_covariance_condition_number": condition_number,
        "lead_covariance_min_eigenvalue": minimum_eigenvalue,
        "lead_covariance_psd_tolerance": psd_tolerance,
        "lead_covariance_positive_semidefinite": bool(
            minimum_eigenvalue >= psd_tolerance
        ),
    }

