"""Exact cross-language equality helpers."""

from __future__ import annotations

import pandas as pd


def same_exact_integer(
    left: pd.Series,
    right: pd.Series,
    *,
    field: str,
) -> pd.Series:
    """Compare integer metadata without depending on CSV dtype inference.

    A CSV reader represents an integer column containing missing values as
    floats. The same omitted reference period can therefore arrive as ``-1``
    on one side and ``-1.0`` on the other. The public contract is exact on the
    integer value and missingness, not on that incidental representation.
    """
    numeric_left = pd.to_numeric(left, errors="raise")
    numeric_right = pd.to_numeric(right, errors="raise")
    for side, values in (("Python", numeric_left), ("R", numeric_right)):
        observed = values.dropna()
        if not observed.mod(1).eq(0).all():
            raise RuntimeError(
                f"{field} contains non-integer {side} metadata"
            )
    return numeric_left.eq(numeric_right) | (
        numeric_left.isna() & numeric_right.isna()
    )
