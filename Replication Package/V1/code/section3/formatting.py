"""Numeric and text formatting shared by Section 3 outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    numeric_values = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    numeric_weights = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    valid = (
        np.isfinite(numeric_values)
        & np.isfinite(numeric_weights)
        & (numeric_weights > 0)
    )
    if not valid.any():
        return float("nan")
    return float(
        np.average(numeric_values[valid], weights=numeric_weights[valid])
    )


def safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def fmt_int(value: float | int) -> str:
    return f"{int(round(float(value))):,}".replace(",", ".")


def fmt_m(value: float) -> str:
    return f"{value:.1f}"


def fmt_m2(value: float) -> str:
    return f"{value:.2f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}"


def fmt_score3(value: float) -> str:
    return f"{value:.3f}"


def fmt_score2(value: float) -> str:
    return f"{value:.2f}"


def markdown_table(
    headers: list[str],
    rows: Iterable[Iterable[object]],
) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
