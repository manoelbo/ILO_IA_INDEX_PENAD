"""Formatting helpers for final Section 4/5 tables and reports."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


def fmt_number(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")
    try:
        value_f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(value_f):
        return ""
    return f"{value_f:.{digits}f}".replace(".", ",")


def fmt_p(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    value_f = float(value)
    if value_f < 0.001:
        return "<0,001"
    return fmt_number(value_f, 3)


def percent_from_log(coef: float) -> float:
    return (math.exp(float(coef)) - 1.0) * 100.0


def is_log_outcome(outcome: object, outcome_label: object) -> bool:
    text = f"{outcome or ''} {outcome_label or ''}".lower()
    return "ln_" in text or "(log)" in text or "log)" in text


def effect_label(coef: object, outcome: object, outcome_label: object) -> str:
    if coef is None or pd.isna(coef):
        return ""
    if is_log_outcome(outcome, outcome_label):
        return f"{fmt_number(percent_from_log(float(coef)), 2)}%"
    return fmt_number(coef, 4)


def evidence_label(pretrend_status: object, exploratory_only: object = False) -> str:
    if bool(exploratory_only):
        return "Exploratório"
    status = str(pretrend_status or "").lower()
    if status == "pass":
        return "Evidência mais forte"
    if status == "fail":
        return "Sugestivo; pretrend falha"
    if status in {"warning", "warn"}:
        return "Sugestivo; pretrend com alerta"
    return "Sugestivo; sem pretrend formal"


def estimate_with_se(coef: object, se: object, stars: object = "") -> str:
    if coef is None or se is None or pd.isna(coef) or pd.isna(se):
        return ""
    sig = "" if stars is None or pd.isna(stars) else str(stars)
    return f"{fmt_number(coef)}{sig} ({fmt_number(se)})"


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sem linhas disponíveis._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in df[columns].iterrows():
        values = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def write_table_pair(
    csv_path: Path,
    md_path: Path,
    title: str,
    df: pd.DataFrame,
    columns: list[str],
    note: str = "",
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    text = f"# {title}\n\n{markdown_table(df, columns)}\n"
    if note:
        text += f"\nNota: {note}\n"
    md_path.write_text(text, encoding="utf-8")

