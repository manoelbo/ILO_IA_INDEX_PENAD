"""Formatting helpers for tables and reports."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def stars(p_value: float | None) -> str:
    if p_value is None or pd.isna(p_value) or math.isnan(float(p_value)):
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def fmt_number(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}".replace(".", ",")
    return str(value)


def estimate_cell(coef: object, se: object, sig: object) -> str:
    if pd.isna(coef) or pd.isna(se):
        return ""
    return f"{fmt_number(coef)}{'' if pd.isna(sig) else sig}<br>({fmt_number(se)})"


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


def write_markdown_table(path, title: str, df: pd.DataFrame, columns: list[str], note: str = "") -> None:
    legend = "Notas: erros-padrão clusterizados entre parênteses. * p<0.10; ** p<0.05; *** p<0.01."
    text = f"# {title}\n\n{markdown_table(df, columns)}\n\n{legend}"
    if note:
        text += f"\n{note}"
    text += "\n"
    path.write_text(text, encoding="utf-8")

