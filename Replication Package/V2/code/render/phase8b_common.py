"""Shared contracts and formatting for Phase 8B dissertation artifacts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = PACKAGE_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"

OUTCOME_LABELS = {
    "admissoes": "Admissões (PPML, nível)",
    "desligamentos": "Desligamentos (PPML, nível)",
    "n_movimentacoes": "Fluxo bruto (PPML, nível)",
    "ln_salario_real_adm": "Salário real de admissão (log)",
    "asinh_saldo": "Saldo líquido (asinh)",
    "admissions": "Admissões",
    "real_admission_wage": "Salário real de admissão",
}
SHORT_OUTCOME_LABELS = {
    "admissoes": "Admissões",
    "desligamentos": "Desligamentos",
    "n_movimentacoes": "Fluxo bruto",
    "ln_salario_real_adm": "Salário real de admissão",
    "asinh_saldo": "Saldo líquido (asinh)",
}


def atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def significance_stars(p_value: float) -> str:
    if not np.isfinite(p_value):
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def format_number(value: Any, digits: int = 4) -> str:
    if pd.isna(value):
        return "—"
    return (
        f"{float(value):.{digits}f}"
        .replace("-", "−")
        .replace(".", ",")
    )


def format_integer(value: Any) -> str:
    if pd.isna(value):
        return "—"
    return f"{int(value):,}".replace(",", ".")


def format_p_value(value: Any) -> str:
    if pd.isna(value):
        return "—"
    numeric = float(value)
    if numeric < 0.001:
        return "<0,001"
    return f"{numeric:.3f}".replace(".", ",")


def interpretation_counts(
    family_c: pd.DataFrame,
    family_a: pd.DataFrame,
    national: pd.DataFrame,
) -> dict[str, Any]:
    wage_c = family_c.loc[
        family_c["outcome"].eq("ln_salario_real_adm")
    ]
    wage_a = family_a.loc[
        family_a["outcome"].eq("ln_salario_real_adm")
    ]
    principal_wage = national.loc[
        national["step_id"].eq("01_no_controls")
        & national["outcome"].eq("ln_salario_real_adm")
    ]
    if len(principal_wage) != 1:
        raise RuntimeError(
            "The national principal wage coefficient must be unique"
        )
    return {
        "family_c_wage_groups": int(len(wage_c)),
        "family_c_negative_wage_bh": int(
            (
                wage_c["bh_significant_005"].astype(bool)
                & wage_c["coefficient"].lt(0)
            ).sum()
        ),
        "family_a_wage_tests": int(len(wage_a)),
        "family_a_wage_bh": int(
            wage_a["bh_significant_005"].astype(bool).sum()
        ),
        "national_wage_coefficient": float(
            principal_wage["coefficient"].iloc[0]
        ),
    }


def mandatory_interpretation_note(counts: dict[str, Any]) -> str:
    coefficient = format_number(
        counts["national_wage_coefficient"],
        digits=4,
    )
    return (
        "As células deste painel reportam o DiD estimado dentro da "
        "amostra do próprio grupo; elas não medem heterogeneidade. Como "
        "o diferencial nacional de salário real de admissão é de "
        f"{coefficient} e rejeita a 5%, ele reaparece dentro de "
        "praticamente todo grupo: "
        f"{counts['family_c_negative_wage_bh']} dos "
        f"{counts['family_c_wage_groups']} grupos da família de 130 "
        "testes apresentam queda salarial significativa após ajuste de "
        "Benjamini-Hochberg. O teste de que os grupos diferem entre si é "
        "o contraste DDD do Apêndice A, no qual "
        f"{counts['family_a_wage_bh']} dos "
        f"{counts['family_a_wage_tests'] * 5} contrastes salariais "
        "sobrevivem ao mesmo ajuste. As duas leituras são compatíveis: "
        "o diferencial é generalizado e a diferença entre grupos não é "
        "detectável."
    )


def short_interpretation_note(counts: dict[str, Any]) -> str:
    return (
        "DiD dentro do grupo não mede heterogeneidade: "
        f"{counts['family_c_negative_wage_bh']}/"
        f"{counts['family_c_wage_groups']} quedas salariais sobrevivem "
        "ao BH na Família C, enquanto "
        f"{counts['family_a_wage_bh']}/"
        f"{counts['family_a_wage_tests'] * 5} DDD salariais sobrevivem "
        "na Família A."
    )


def _markdown_cell(value: Any) -> str:
    if pd.isna(value):
        return "—"
    return (
        str(value)
        .replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
    )


def markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append(
            "| " + " | ".join(_markdown_cell(value) for value in row) + " |"
        )
    return "\n".join(lines)


def save_table_pair(
    audit_frame: pd.DataFrame,
    display_frame: pd.DataFrame,
    *,
    csv_path: Path,
    md_path: Path,
    title: str,
    notes: list[str],
) -> None:
    atomic_csv(audit_frame, csv_path)
    body = [f"# {title}", "", markdown_table(display_frame), ""]
    body.extend(f"- {note}" for note in notes)
    body.append("")
    atomic_text("\n".join(body), md_path)
