from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
APRESENTACAO_DIR = ROOT / "apresentacao_aula"
TABLES_DIR = APRESENTACAO_DIR / "tables"
FIGURES_DIR = APRESENTACAO_DIR / "figures"
DATA_OUTPUT = ROOT / "data" / "output"


def ensure_dirs() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def latex_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def fmt_decimal(value: float, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "--"
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(value: float) -> str:
    if value is None or pd.isna(value):
        return "--"
    return f"{value:,.0f}".replace(",", ".")


def fmt_pct(value: float, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "--"
    return f"{100 * value:.{digits}f}%".replace(".", ",")


def weighted_mean(x: pd.Series, w: pd.Series) -> float:
    mask = x.notna() & w.notna() & (w > 0)
    if not mask.any():
        return np.nan
    return float(np.average(x[mask], weights=w[mask]))


def weighted_std(x: pd.Series, w: pd.Series) -> float:
    mask = x.notna() & w.notna() & (w > 0)
    if not mask.any():
        return np.nan
    mean = np.average(x[mask], weights=w[mask])
    var = np.average((x[mask] - mean) ** 2, weights=w[mask])
    return float(np.sqrt(var))


def descriptive_table(
    df: pd.DataFrame,
    variables: Iterable[tuple[str, str, str]],
    *,
    weight: str | None = None,
    percent_vars: set[str] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    percent_vars = percent_vars or set()
    weights = df[weight] if weight else None

    for col, label, unit in variables:
        if col not in df.columns:
            continue
        x = pd.to_numeric(df[col], errors="coerce")
        if col in percent_vars:
            x = x * 100

        if weights is not None:
            mean = weighted_mean(x, weights)
            std = weighted_std(x, weights)
        else:
            mean = float(x.mean())
            std = float(x.std())

        rows.append(
            {
                "Variável": label,
                "Unidade": unit,
                "N": int(x.notna().sum()),
                "Média": mean,
                "Desv. Pad.": std,
                "Min": float(x.min()),
                "Max": float(x.max()),
            }
        )
    return pd.DataFrame(rows)


def save_table_outputs(df: pd.DataFrame, stem: str, *, digits: int = 2, max_rows: int | None = None) -> None:
    ensure_dirs()
    out = df.copy()
    if max_rows is not None:
        out = out.head(max_rows)
    out.to_csv(TABLES_DIR / f"{stem}.csv", index=False)
    write_latex_table(out, TABLES_DIR / f"{stem}.tex", digits=digits)


def write_latex_table(df: pd.DataFrame, path: Path, *, digits: int = 2) -> None:
    cols = list(df.columns)
    align = "l" + "r" * (len(cols) - 1)

    lines = [
        r"\scriptsize",
        r"\begin{tabular}{" + align + r"}",
        r"\toprule",
        " & ".join(latex_escape(c) for c in cols) + r" \\",
        r"\midrule",
    ]

    for _, row in df.iterrows():
        vals: list[str] = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                vals.append(fmt_decimal(float(value), digits))
            elif isinstance(value, (int, np.integer)):
                vals.append(fmt_int(float(value)))
            else:
                vals.append(latex_escape(value))
        lines.append(" & ".join(vals) + r" \\")

    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_key_value_table(rows: list[tuple[str, object]], stem: str) -> None:
    df = pd.DataFrame(rows, columns=["Item", "Valor"])
    save_table_outputs(df, stem, digits=2)


def format_descriptive_for_slides(df: pd.DataFrame, *, digits: int = 2) -> pd.DataFrame:
    out = df.copy()
    if "N" in out:
        out["N"] = out["N"].map(fmt_int)
    for col in ["Média", "Desv. Pad.", "Min", "Max"]:
        if col in out:
            out[col] = out[col].map(lambda v: fmt_decimal(v, digits))
    return out

