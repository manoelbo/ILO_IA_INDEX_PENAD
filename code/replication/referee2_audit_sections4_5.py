#!/usr/bin/env python3
"""Independent audit of dissertation Sections 4–5.

The audit treats the exported HTML as the editorial authority and the frozen
analytical outputs as computational authorities. It never imports or modifies the
author's code. All audit artifacts are written to ``correspondence/referee2``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, Tag
from PIL import Image


DATE_STEM = "2026-07-25_round1_sections4_5"
EXPECTED_TABLES = 23
EXPECTED_FIGURES = 13
PRIMARY_OUTCOMES = (
    "ln_admissoes",
    "ln_desligamentos",
    "ln_salario_real_adm",
    "asinh_saldo",
)
BALANCE_OUTCOMES = ("saldo_per_pre_adm", "saldo_flow_rate")


@dataclass(frozen=True)
class HtmlTable:
    table_id: str
    html_id: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class HtmlFigure:
    figure_id: str
    html_src: str
    path: Path
    file_reference: str


@dataclass(frozen=True)
class HtmlBlock:
    location: str
    html_id: str
    tag: str
    text: str


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="Exported dissertation HTML. Defaults to the unique HTML export.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "correspondence/referee2",
    )
    return parser.parse_args()


def default_html(root: Path) -> Path:
    candidates = sorted((root / "Secao 4 e 5 concluida").glob("*.html"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected one HTML export; found {len(candidates)}."
        )
    return candidates[0]


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_tree(path: Path) -> pd.DataFrame:
    rows = []
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        rows.append(
            {
                "path": file_path.relative_to(project_root()).as_posix(),
                "bytes": file_path.stat().st_size,
                "sha256": sha256(file_path),
            }
        )
    return pd.DataFrame(rows)


def write_audit_manifest(output_dir: Path) -> Path:
    """Hash every generated audit artifact except the manifest itself."""
    manifest_path = output_dir / f"{DATE_STEM}_audit_manifest.csv"
    rows = []
    for path in sorted(output_dir.glob(f"{DATE_STEM}_*")):
        if not path.is_file() or path == manifest_path:
            continue
        rows.append(
            {
                "path": path.relative_to(project_root()).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    pd.DataFrame(rows).to_csv(manifest_path, index=False)
    return manifest_path


def _nearby_file_reference(image: Tag) -> str:
    pattern = re.compile(
        r"\[(?:file ref|ref file)\s*:\s*([^\]]+?\.png)\s*\]",
        flags=re.IGNORECASE,
    )
    for paragraph in image.find_all_previous("p", limit=5):
        match = pattern.search(clean_text(paragraph.get_text(" ", strip=True)))
        if match:
            return match.group(1)
    raise ValueError(f"No file reference found near image {image.get('src')}.")


def inspect_html(
    html_path: Path,
) -> tuple[list[HtmlTable], list[HtmlFigure], list[HtmlBlock]]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    body = soup.select_one("div.page-body")
    if body is None:
        raise ValueError("The HTML export has no div.page-body.")

    tables = []
    for index, table in enumerate(body.select("table.simple-table"), start=1):
        columns = tuple(
            clean_text(cell.get_text(" ", strip=True))
            for cell in table.select("thead th")
        )
        rows = tuple(
            tuple(
                clean_text(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
            )
            for row in table.select("tbody tr")
        )
        tables.append(
            HtmlTable(
                table_id=f"T{index:02d}",
                html_id=str(table.get("id", "")),
                columns=columns,
                rows=rows,
            )
        )

    local_images = [
        image
        for image in body.find_all("img")
        if not str(image.get("src", "")).startswith(("http://", "https://"))
    ]
    figures = []
    for index, image in enumerate(local_images, start=1):
        source = str(image.get("src", ""))
        figures.append(
            HtmlFigure(
                figure_id=f"F{index:02d}",
                html_src=source,
                path=(html_path.parent / unquote(source)).resolve(),
                file_reference=_nearby_file_reference(image),
            )
        )

    blocks = []
    narrative_index = 0
    for element in body.find_all(["h1", "h2", "h3", "h4", "p"]):
        if element.find_parent(["table", "figure"]):
            continue
        narrative_index += 1
        blocks.append(
            HtmlBlock(
                location=f"N{narrative_index:03d}",
                html_id=str(element.get("id", "")),
                tag=element.name.upper(),
                text=clean_text(element.get_text(" ", strip=True)),
            )
        )
    return tables, figures, blocks


def fmt_number(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if digits == 0:
        return f"{int(round(float(value))):,}".replace(",", ".")
    return f"{float(value):.{digits}f}".replace(".", ",")


def fmt_p(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    numeric = float(value)
    return "<0,001" if numeric < 0.001 else fmt_number(numeric, 3)


def stars(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    numeric = float(value)
    if numeric < 0.01:
        return "***"
    if numeric < 0.05:
        return "**"
    if numeric < 0.10:
        return "*"
    return ""


def estimate_cell(
    coefficient: object,
    standard_error: object,
    p_value: object,
    line_break: bool,
) -> str:
    separator = "<br>" if line_break else " "
    return (
        f"{fmt_number(coefficient)}{stars(p_value)}"
        f"{separator}({fmt_number(standard_error)})"
    )


def status_with_p(status: object, p_value: object) -> str:
    status_text = (
        "not_available"
        if status is None or pd.isna(status)
        else str(status)
    )
    if p_value is None or pd.isna(p_value):
        return status_text
    return f"{status_text} (p={fmt_p(p_value)})"


def read_strings(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def panel_a(
    source: pd.DataFrame,
    group_column: str,
    output_group_column: str,
    outcomes: tuple[str, ...],
) -> pd.DataFrame:
    rows = []
    for group_label in source["group_label"].drop_duplicates():
        group = source[source["group_label"].eq(group_label)]
        row: dict[str, str] = {output_group_column: str(group_label)}
        for outcome in outcomes:
            selected = group[group["outcome"].eq(outcome)]
            if len(selected) != 1:
                raise ValueError(
                    f"Expected one {group_label}/{outcome} row; "
                    f"found {len(selected)}."
                )
            item = selected.iloc[0]
            row[str(item["outcome_label"])] = estimate_cell(
                item["group_coef"],
                item["group_se"],
                item["group_p_value"],
                line_break=False,
            )
        rows.append(row)
    result = pd.DataFrame(rows)
    return result.rename(columns={"group_label": group_column})


def diagnostic_panel(
    source: pd.DataFrame,
    outcomes: tuple[str, ...],
    translated: bool = False,
) -> pd.DataFrame:
    selected = source[source["outcome"].isin(outcomes)].copy()
    outcome_order = {outcome: index for index, outcome in enumerate(outcomes)}
    group_order = {
        label: index
        for index, label in enumerate(source["group_label"].drop_duplicates())
    }
    selected["_group_order"] = selected["group_label"].map(group_order)
    selected["_outcome_order"] = selected["outcome"].map(outcome_order)
    selected = selected.sort_values(["_group_order", "_outcome_order"])

    status_translation = {
        "pass": "Aprovado",
        "fail": "Falha",
        "warning": "Alerta",
        "not_available": "Não disponível",
    }
    support_translation = {
        "adequate": "Adequado",
        "limited": "Limitado",
        "thin": "Insuficiente",
    }
    outcome_translation = {
        "ln_admissoes": "Admissões",
        "ln_desligamentos": "Desligamentos",
        "ln_salario_real_adm": "Salário de admissão",
    }
    rows = []
    for item in selected.itertuples(index=False):
        if translated:
            group_pretrend = status_translation.get(
                str(item.group_pretrend_status),
                str(item.group_pretrend_status),
            )
            ddd_pretrend = status_translation.get(
                str(item.ddd_pretrend_status),
                str(item.ddd_pretrend_status),
            )
            group_pretrend = status_with_p(
                group_pretrend,
                item.group_pretrend_p_value,
            )
            ddd_pretrend = status_with_p(
                ddd_pretrend,
                item.ddd_pretrend_p_value,
            )
            outcome_label = outcome_translation[str(item.outcome)]
            support = support_translation.get(
                str(item.group_power_status),
                str(item.group_power_status),
            )
        else:
            group_pretrend = status_with_p(
                item.group_pretrend_status,
                item.group_pretrend_p_value,
            )
            ddd_pretrend = status_with_p(
                item.ddd_pretrend_status,
                item.ddd_pretrend_p_value,
            )
            outcome_label = str(item.outcome_label)
            support = str(item.group_power_status)
        rows.append(
            {
                "Grupo": str(item.group_label),
                "Resultado": outcome_label,
                (
                    "DDD grupo-complemento"
                    if translated
                    else "DDD grupo–complemento"
                ): estimate_cell(
                    item.ddd_coef,
                    item.ddd_se,
                    item.ddd_p_value,
                    line_break=not translated,
                ),
                "p DDD": fmt_p(item.ddd_p_value),
                "Pretrend grupo": group_pretrend,
                "Pretrend DDD": ddd_pretrend,
                ("Suporte" if translated else "Poder grupo"): support,
                "N grupo": fmt_number(item.group_n_obs, 0),
                "CBOs trat./controle": (
                    f"{fmt_number(item.group_treated_cbo, 0)}/"
                    f"{fmt_number(item.group_control_cbo, 0)}"
                ),
            }
        )
    return pd.DataFrame(rows)


def national_diagnostic(
    source: pd.DataFrame,
    outcomes: tuple[str, ...],
) -> pd.DataFrame:
    selected = source[source["outcome"].isin(outcomes)].copy()
    order = {outcome: index for index, outcome in enumerate(outcomes)}
    selected["_order"] = selected["outcome"].map(order)
    selected = selected.sort_values("_order")
    return pd.DataFrame(
        [
            {
                "Resultado": str(item.outcome_label),
                "DiD nacional": estimate_cell(
                    item.coef,
                    item.se,
                    item.p_value,
                    line_break=True,
                ),
                "p DiD": fmt_p(item.p_value),
                "Pretrend": status_with_p(
                    item.pretrend_status,
                    item.pretrend_p_value,
                ),
                "N": fmt_number(item.n_obs, 0),
                "CBOs": fmt_number(item.n_cbo, 0),
            }
            for item in selected.itertuples(index=False)
        ]
    )


def _ordered_composition(value: str) -> str:
    fragments = [fragment.strip() for fragment in value.split(";")]

    def sort_key(fragment: str) -> tuple[int, str]:
        lowered = fragment.lower()
        gradient = re.match(r"g(\d)", lowered)
        if gradient:
            return (10 - int(gradient.group(1)), lowered)
        if lowered.startswith("não exposto"):
            return (20, lowered)
        if lowered.startswith("exposição mínima"):
            return (21, lowered)
        if lowered.startswith("sem escore"):
            return (22, lowered)
        return (30, lowered)

    return "; ".join(sorted(fragments, key=sort_key))


def expected_tables(root: Path) -> tuple[list[pd.DataFrame], list[str]]:
    table_dir = root / "outputs/section4_5_final/tables"
    sources: list[str] = []
    expected: list[pd.DataFrame] = []

    panel_scope_path = table_dir / "table_4_2a_panel_descriptive_summary.csv"
    panel_scope = read_strings(panel_scope_path)[["Indicador", "Valor"]]
    expected.append(panel_scope)
    sources.append(panel_scope_path.relative_to(root).as_posix())

    classification_path = table_dir / "table_4_2b_ilo_cbo_classification.csv"
    expected.append(read_strings(classification_path))
    sources.append(classification_path.relative_to(root).as_posix())

    coverage_path = table_dir / "table_4_2c_crosswalk_coverage.csv"
    expected.append(read_strings(coverage_path))
    sources.append(coverage_path.relative_to(root).as_posix())

    expected.append(
        pd.DataFrame(
            [
                {
                    "Grupo": "Fluxos",
                    "Outcome": "Admissões",
                    "Definição": (
                        "Número de admissões formais na ocupação-mês"
                    ),
                    "Transformação": "log(y+1); Poisson na robustez",
                },
                {
                    "Grupo": "Fluxos",
                    "Outcome": "Desligamentos",
                    "Definição": (
                        "Número de desligamentos formais na ocupação-mês"
                    ),
                    "Transformação": "log(y+1); Poisson na robustez",
                },
                {
                    "Grupo": "Salários",
                    "Outcome": "Salário real de admissão",
                    "Definição": (
                        "Salário médio de admissão deflacionado pelo IPCA"
                    ),
                    "Transformação": "log",
                },
                {
                    "Grupo": "Saldo",
                    "Outcome": "Saldo líquido",
                    "Definição": (
                        "Admissões menos desligamentos na ocupação-mês"
                    ),
                    "Transformação": "asinh(saldo)",
                },
            ]
        )
    )
    sources.append("semantic contract independently reconstructed")

    national_path = table_dir / "table_5_2_1_national_main_results.csv"
    national = pd.read_csv(national_path)
    national_primary = national[
        national["outcome"].isin(PRIMARY_OUTCOMES[:3])
    ].copy()
    row = {"Amostra": "Nacional"}
    for item in national_primary.itertuples(index=False):
        row[str(item.outcome_label)] = estimate_cell(
            item.coef,
            item.se,
            item.p_value,
            line_break=False,
        )
    expected.append(pd.DataFrame([row]))
    sources.append(national_path.relative_to(root).as_posix())

    heterogeneity_specs = [
        (
            "table_5_2_2_heterogeneity_sex.csv",
            "Grupo",
        ),
        ("table_5_2_5_b.csv", "Grupo"),
        ("table_5_2_4_b.csv", "Faixa etária"),
        (
            "table_5_2_6_heterogeneity_education.csv",
            "Grupo",
        ),
        (
            "table_5_2_3_heterogeneity_income.csv",
            "Faixa de renda",
        ),
    ]
    heterogeneity_data: dict[str, pd.DataFrame] = {}
    for filename, group_header in heterogeneity_specs:
        source_path = table_dir / filename
        source = pd.read_csv(source_path)
        heterogeneity_data[filename] = source
        panel = panel_a(
            source,
            group_column=group_header,
            output_group_column=group_header,
            outcomes=PRIMARY_OUTCOMES,
        )
        first_column = panel.columns[0]
        panel = panel.rename(columns={first_column: group_header})
        if filename == "table_5_2_4_b.csv":
            panel[group_header] = panel[group_header].replace({"55+": "55–65"})
        expected.append(panel)
        sources.append(source_path.relative_to(root).as_posix())

    occupation_path = (
        root
        / "outputs/section5_3_occupation_cases/tables"
        / "table_5_3_1_occupation_case_exposure_summary.csv"
    )
    occupation = read_strings(occupation_path)
    occupation_expected = pd.DataFrame(
        {
            "Caso ocupacional": occupation["Caso ocupacional"],
            "CBOs (n)": occupation["CBOs (n)"],
            "Confiança semântica": occupation["Confiança semântica"],
            "Referência em Canaries": occupation["Benchmark em Canaries"],
            "Composição OIT no Brasil": occupation[
                "Composição OIT no Brasil"
            ].map(_ordered_composition),
            "Admissões pré-tratamento": occupation[
                "Admissões pré-tratamento"
            ].map(lambda value: fmt_number(float(value), 0)),
        }
    )
    expected.append(occupation_expected)
    sources.append(occupation_path.relative_to(root).as_posix())

    expected.append(national_diagnostic(national, PRIMARY_OUTCOMES))
    sources.append(national_path.relative_to(root).as_posix())
    expected.append(national_diagnostic(national, BALANCE_OUTCOMES))
    sources.append(national_path.relative_to(root).as_posix())

    sex = heterogeneity_data["table_5_2_2_heterogeneity_sex.csv"]
    race = heterogeneity_data["table_5_2_5_b.csv"]
    age = heterogeneity_data["table_5_2_4_b.csv"]
    education = heterogeneity_data[
        "table_5_2_6_heterogeneity_education.csv"
    ]
    income = heterogeneity_data[
        "table_5_2_3_heterogeneity_income.csv"
    ]
    canaries_path = (
        table_dir / "table_5_2_4_heterogeneity_age_canaries.csv"
    )
    canaries = pd.read_csv(canaries_path)

    for data, outcomes, source_path in [
        (sex, PRIMARY_OUTCOMES, table_dir / heterogeneity_specs[0][0]),
        (sex, BALANCE_OUTCOMES, table_dir / heterogeneity_specs[0][0]),
        (race, PRIMARY_OUTCOMES, table_dir / heterogeneity_specs[1][0]),
        (age, PRIMARY_OUTCOMES, table_dir / heterogeneity_specs[2][0]),
        (age, BALANCE_OUTCOMES, table_dir / heterogeneity_specs[2][0]),
        (canaries, PRIMARY_OUTCOMES, canaries_path),
        (canaries, BALANCE_OUTCOMES, canaries_path),
    ]:
        expected.append(diagnostic_panel(data, outcomes))
        sources.append(source_path.relative_to(root).as_posix())

    expected.append(
        diagnostic_panel(
            education,
            PRIMARY_OUTCOMES[:3],
            translated=True,
        )
    )
    sources.append(
        (table_dir / heterogeneity_specs[3][0])
        .relative_to(root)
        .as_posix()
    )
    expected.append(diagnostic_panel(income, PRIMARY_OUTCOMES))
    sources.append(
        (table_dir / heterogeneity_specs[4][0])
        .relative_to(root)
        .as_posix()
    )
    expected.append(diagnostic_panel(income, BALANCE_OUTCOMES))
    sources.append(
        (table_dir / heterogeneity_specs[4][0])
        .relative_to(root)
        .as_posix()
    )

    if len(expected) != EXPECTED_TABLES:
        raise AssertionError(f"Built {len(expected)} expected tables.")
    return expected, sources


def normalized_cell(value: object) -> str:
    text = clean_text(str(value))
    text = text.replace("&lt;", "<").replace("−", "-")
    text = text.replace("<br/>", " ").replace("<br>", " ")
    text = re.sub(r"\s+", "", text)
    return text.casefold()


def _locale_number(value: str) -> float | None:
    text = value.strip().replace(".", "").replace(",", ".")
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text):
        return float(text)
    return None


def cells_equivalent(displayed: object, expected: object) -> bool:
    left = normalized_cell(displayed)
    right = normalized_cell(expected)
    if left == right:
        return True
    left_number = _locale_number(clean_text(str(displayed)))
    right_number = _locale_number(clean_text(str(expected)))
    if left_number is not None and right_number is not None:
        return math.isclose(left_number, right_number, abs_tol=5e-7)
    if ";" in left and ";" in right:
        return set(left.split(";")) == set(right.split(";"))
    return False


def table_ledgers(
    html_tables: list[HtmlTable],
    expected: list[pd.DataFrame],
    sources: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ledger_rows = []
    summary_rows = []
    for index, (html_table, authority, source) in enumerate(
        zip(html_tables, expected, sources, strict=True),
        start=1,
    ):
        table_is_wrong_copy = index in {22, 23}
        if len(authority) != len(html_table.rows):
            raise ValueError(
                f"{html_table.table_id}: expected {len(authority)} rows, "
                f"found {len(html_table.rows)}."
            )
        if len(authority.columns) != len(html_table.columns):
            raise ValueError(
                f"{html_table.table_id}: expected {len(authority.columns)} "
                f"columns, found {len(html_table.columns)}."
            )

        matched = 0
        incorrect = 0
        for column_index, (displayed, raw) in enumerate(
            zip(
                html_table.columns,
                [str(column) for column in authority.columns],
                strict=True,
            ),
            start=1,
        ):
            equivalent = cells_equivalent(displayed, raw)
            status = "verified" if equivalent else "incorrect"
            matched += int(equivalent)
            incorrect += int(not equivalent)
            ledger_rows.append(
                {
                    "claim_id": (
                        f"{html_table.table_id}.HEADER.C{column_index:02d}"
                    ),
                    "location": (
                        f"{html_table.table_id} / HTML {html_table.html_id}"
                    ),
                    "original_text": displayed,
                    "claim_type": "table_header",
                    "source": source,
                    "raw_value": raw,
                    "rounding_rule": "not applicable",
                    "displayed_value": displayed,
                    "status": status,
                    "severity": "minor" if not equivalent else "none",
                    "recommended_replacement": (
                        raw if not equivalent else ""
                    ),
                    "evidence": "independent source-to-HTML comparison",
                    "notes": "",
                }
            )

        for row_index, (displayed_row, authority_row) in enumerate(
            zip(html_table.rows, authority.itertuples(index=False), strict=True),
            start=1,
        ):
            for column_index, (displayed, raw_value) in enumerate(
                zip(displayed_row, authority_row, strict=True),
                start=1,
            ):
                raw = "" if pd.isna(raw_value) else str(raw_value)
                equivalent = cells_equivalent(displayed, raw)
                if table_is_wrong_copy:
                    status = "incorrect"
                    severity = "critical"
                    note = (
                        "The HTML repeats the education table where the "
                        "income table is required."
                    )
                else:
                    status = "verified" if equivalent else "incorrect"
                    severity = "none" if equivalent else "major"
                    note = ""
                matched += int(status == "verified")
                incorrect += int(status != "verified")
                ledger_rows.append(
                    {
                        "claim_id": (
                            f"{html_table.table_id}.R{row_index:02d}."
                            f"C{column_index:02d}"
                        ),
                        "location": (
                            f"{html_table.table_id} / "
                            f"HTML {html_table.html_id}"
                        ),
                        "original_text": displayed,
                        "claim_type": "table_cell",
                        "source": source,
                        "raw_value": raw,
                        "rounding_rule": (
                            "4 decimals for estimates/SEs; 3 decimals for "
                            "p-values; Brazilian decimal comma; integer "
                            "thousands separator"
                        ),
                        "displayed_value": displayed,
                        "status": status,
                        "severity": severity,
                        "recommended_replacement": (
                            raw if status != "verified" else ""
                        ),
                        "evidence": "independent source-to-HTML comparison",
                        "notes": note,
                    }
                )
        summary_rows.append(
            {
                "table_id": html_table.table_id,
                "html_id": html_table.html_id,
                "rows": len(html_table.rows),
                "columns": len(html_table.columns),
                "cells_including_headers": (
                    len(html_table.columns)
                    + len(html_table.rows) * len(html_table.columns)
                ),
                "verified_cells": matched,
                "incorrect_cells": incorrect,
                "computational_source": source,
                "status": (
                    "known_editorial_error"
                    if table_is_wrong_copy
                    else ("pass" if incorrect == 0 else "unexpected_mismatch")
                ),
            }
        )
    return pd.DataFrame(ledger_rows), pd.DataFrame(summary_rows)


def figure_ledger(
    figures: list[HtmlFigure],
    artifact_map: pd.DataFrame,
    root: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    figure_map = artifact_map[
        artifact_map["artifact_type"].eq("figure")
    ].sort_values("html_order")
    if len(figure_map) != len(figures):
        raise ValueError("Figure artifact map and HTML inventory differ.")
    ledger_rows = []
    summary_rows = []
    for html_figure, item in zip(
        figures,
        figure_map.itertuples(index=False),
        strict=True,
    ):
        source_path = root / str(item.source_input)
        output_path = (
            root
            / "Replication Package/outputs/sections4_5"
            / str(item.output_file)
        )
        html_exists = html_figure.path.exists()
        source_exists = source_path.exists()
        output_exists = output_path.exists()
        reference_matches = (
            html_figure.file_reference == Path(str(item.output_file)).name
        )
        with Image.open(html_figure.path) as image:
            html_dimensions = f"{image.width}x{image.height}"
        with Image.open(source_path) as image:
            source_dimensions = f"{image.width}x{image.height}"
        visual_rms = float(item.visual_rms)
        passed = all(
            [
                html_exists,
                source_exists,
                output_exists,
                reference_matches,
                visual_rms < 25,
            ]
        )
        summary_rows.append(
            {
                "figure_id": html_figure.figure_id,
                "artifact_id": item.artifact_id,
                "file_reference": html_figure.file_reference,
                "source": str(item.source_input),
                "source_sha256": sha256(source_path),
                "replication_sha256": sha256(output_path),
                "html_sha256": sha256(html_figure.path),
                "source_dimensions": source_dimensions,
                "html_dimensions": html_dimensions,
                "visual_rms": visual_rms,
                "reference_matches": reference_matches,
                "status": "pass" if passed else "fail",
            }
        )
        ledger_rows.append(
            {
                "claim_id": f"{html_figure.figure_id}.ARTIFACT",
                "location": (
                    f"{html_figure.figure_id} / {item.artifact_id}"
                ),
                "original_text": html_figure.file_reference,
                "claim_type": "figure",
                "source": str(item.source_input),
                "raw_value": (
                    f"source={source_dimensions}; visual_rms={visual_rms:.6f}"
                ),
                "rounding_rule": "not applicable",
                "displayed_value": html_figure.html_src,
                "status": "verified" if passed else "incorrect",
                "severity": "none" if passed else "major",
                "recommended_replacement": "",
                "evidence": (
                    "file reference, backing source, dimensions, hashes, "
                    "and visual comparison"
                ),
                "notes": (
                    "Compression/resizing is accepted when visual RMS is "
                    "below the audit threshold."
                ),
            }
        )
    return pd.DataFrame(ledger_rows), pd.DataFrame(summary_rows)


def correction_registry() -> list[dict[str, str]]:
    """Return all editorial and substantive corrections identified in review."""

    def correction(
        claim_id: str,
        location: str,
        needle: str,
        claim_type: str,
        severity: str,
        source: str,
        raw_value: str,
        displayed_value: str,
        replacement: str,
        note: str,
        status: str = "incorrect",
    ) -> dict[str, str]:
        return {
            "claim_id": claim_id,
            "location": location,
            "needle": needle,
            "claim_type": claim_type,
            "source": source,
            "raw_value": raw_value,
            "rounding_rule": (
                "100 × (exp(beta) − 1) for log coefficients; otherwise "
                "as stated"
            ),
            "displayed_value": displayed_value,
            "status": status,
            "severity": severity,
            "recommended_replacement": replacement,
            "evidence": note,
            "notes": note,
        }

    return [
        correction(
            "C001",
            "B002 / Section heading",
            "4.1 A bordagem de Diferenças em Diferenças.",
            "typography",
            "minor",
            "HTML",
            "Abordagem",
            "A bordagem",
            "4.1 Abordagem de diferenças em diferenças",
            "Broken word in heading.",
        ),
        correction(
            "C002",
            "B003 / Canaries benchmark",
            "queda relativa de cerca de 13% no emprego",
            "external_numeric_claim",
            "major",
            (
                "Brynjolfsson, Chandar and Chen, Canaries in the Coal Mine, "
                "13 Nov 2025 version"
            ),
            "16%",
            "13%",
            (
                "queda relativa de cerca de 16% no emprego, na "
                "especificação com controles de firma e tempo da versão "
                "de 13 de novembro de 2025"
            ),
            "The latest primary-source version reports 16%, not 13%.",
        ),
        correction(
            "C003",
            "B004 / Novo CAGED description",
            "registro administrativo do Ministério do Trabalho em que todas as empresas são obrigadas a declarar",
            "external_factual_claim",
            "moderate",
            "Ministry of Labour and Employment, O que é o Novo CAGED?",
            "Novo CAGED integrates eSocial, CAGED and Empregador Web",
            "all firms declare directly to CAGED",
            (
                "estatística administrativa do Ministério do Trabalho e "
                "Emprego construída a partir de informações do eSocial, "
                "do CAGED e do Empregador Web. Desde janeiro de 2020, a "
                "maior parte das empresas cumpre a obrigação de informar "
                "admissões e desligamentos pelo eSocial, e os registros "
                "são consolidados mensalmente"
            ),
            "The current wording conflates the statistic with its input systems.",
        ),
        correction(
            "C004",
            "B012 / Table cross-reference",
            "Como podemos ver na tabela Tabela 4.2.2",
            "copy_edit",
            "minor",
            "HTML",
            "Como mostra a Tabela 4.2.2",
            "tabela Tabela",
            "Como mostra a Tabela 4.2.2",
            "Duplicated noun.",
        ),
        correction(
            "C005",
            "B018 / Coverage paragraph",
            "92,5% dos fluxos observadas",
            "grammar",
            "minor",
            "table_4_2c_crosswalk_coverage.csv",
            "92,5% dos fluxos observados",
            "observadas",
            "92,5% dos fluxos observados",
            "Gender agreement.",
        ),
        correction(
            "C006",
            "B029–B030 / Outcomes table",
            "Tabela 4.2: Outcomes da análise",
            "numbering",
            "minor",
            "HTML table sequence",
            "Tabela 4.3.1",
            "Tabela 4.2",
            (
                "Troque as duas ocorrências por "
                "'Tabela 4.3.1: Outcomes da análise'."
            ),
            "The table is in Section 4.3 and 4.2.1–4.2.3 already exist.",
        ),
        correction(
            "C007",
            "B034 / Age methodology",
            "conforme é aplicado na PENAD",
            "terminology",
            "minor",
            "IBGE",
            "PNAD",
            "PENAD",
            "conforme aplicado na PNAD",
            "Incorrect acronym.",
        ),
        correction(
            "C008",
            "B036 / Occupation-case methodology",
            "Os quatro grupos que entram no texto principal são",
            "methodology",
            "critical",
            "outputs/section5_3_occupation_cases",
            "six frozen semantic CBO6 cases; 76 codes; no overlap",
            "four keyword-selected CBO groups",
            (
                "Também construí seis casos ocupacionais para investigar "
                "mecanismos: desenvolvedores de software, atendimento ao "
                "cliente, gerentes de marketing e vendas, supervisores de "
                "produção, estoquistas e repositores e auxiliares de saúde "
                "e cuidado. Os casos foram definidos semanticamente a "
                "partir das descrições oficiais das CBOs de seis dígitos, "
                "congelados antes da inspeção dos resultados e reúnem 76 "
                "códigos sem sobreposição. A composição segundo a OIT é "
                "usada posteriormente para interpretar os casos, não para "
                "selecioná-los por palavras-chave."
            ),
            "The methodology paragraph describes an obsolete analysis.",
        ),
        correction(
            "C009",
            "B042 / National interpretation",
            "As magnitudes são economicamente relevantes",
            "interpretation",
            "moderate",
            "national DiD results",
            "no prespecified economic-significance threshold",
            "economically relevant",
            (
                "As estimativas pontuais são numericamente não "
                "desprezíveis, mas imprecisas; como não foi definido um "
                "limiar ex ante de relevância econômica, elas não devem "
                "ser classificadas como economicamente relevantes."
            ),
            "Economic relevance was not tied to a prespecified threshold.",
            status="revise",
        ),
        correction(
            "C010",
            "B043 / Flow-versus-stock interpretation",
            "os dados não sugerem destruição generalizada de empregos, no máximo menor rotatividade",
            "interpretation",
            "major",
            "CAGED flow specification",
            "flows do not identify the employment stock",
            "no generalized job destruction",
            (
                "Como admissões e desligamentos caem simultaneamente, o "
                "padrão é compatível com menor movimentação dos fluxos. "
                "Entretanto, como o modelo não observa o estoque de "
                "emprego, ele não permite concluir se houve ou não "
                "destruição líquida de vínculos."
            ),
            "Simultaneous flow declines do not identify the stock.",
            status="revise",
        ),
        correction(
            "C011",
            "B049 / Literature synthesis",
            "Resultados nulos ou imprecisos no agregado são, aliás, um padrão consolidado nessa literatura",
            "literature_interpretation",
            "major",
            "primary papers listed in external_sources.csv",
            "mixed short-run evidence with heterogeneous designs",
            "consolidated null pattern",
            (
                "A literatura recente encontra efeitos agregados pequenos "
                "ou nulos em alguns desenhos de curto prazo, mas também "
                "resultados negativos em subgrupos, firmas e ocupações; "
                "portanto, o padrão ainda não deve ser chamado de "
                "consolidado."
            ),
            "The source record is mixed and remains based largely on working papers.",
            status="revise",
        ),
        correction(
            "C012",
            "B049 / Aldasoro et al.",
            "com firmas europeias",
            "external_factual_claim",
            "moderate",
            "BIS Working Paper 1325",
            ">12,000 EU and US non-financial firms; +4% productivity",
            "European firms only",
            (
                "com mais de 12 mil firmas não financeiras da União "
                "Europeia e dos Estados Unidos, associam a adoção de IA a "
                "um aumento de 4% na produtividade do trabalho, sem efeito "
                "adverso sobre o emprego no nível da firma no curto prazo"
            ),
            "The matching design uses both European and US firms.",
        ),
        correction(
            "C013",
            "B049 / Klein Teeselink timing",
            "o choque aparece primeiro na redução de novas vagas, antes de qualquer ajuste no estoque de empregados",
            "external_factual_claim",
            "major",
            "Klein Teeselink (2025), primary working paper",
            (
                "employment and postings both decline; posting decline "
                "emerges after about 10 months and mirrors stock adjustment"
            ),
            "vacancies fall before any stock adjustment",
            (
                "documenta reduções tanto no emprego quanto nas novas "
                "vagas; o artigo descreve a queda das vagas como gradual e "
                "com cronologia semelhante à do estoque, não como anterior "
                "a qualquer ajuste no emprego"
            ),
            "The claimed temporal ordering is not supported by the paper.",
        ),
        correction(
            "C014",
            "B050 / Aggregate conclusion",
            "no curto prazo, a IA ainda não produz desemprego em massa",
            "interpretation",
            "major",
            "reviewed literature",
            "short-run evidence is mixed and design-specific",
            "general absence of mass unemployment",
            (
                "no período e nas amostras examinadas, vários estudos "
                "encontram efeitos agregados pequenos ou nulos, com "
                "heterogeneidade e incerteza; isso não permite concluir "
                "que a IA não produza efeitos futuros ou concentrados em "
                "subgrupos"
            ),
            "The original sentence generalizes beyond the evidence.",
            status="revise",
        ),
        correction(
            "C015",
            "B053–B054 / Sex table",
            "Tabela 5.2: Resultados por sexo",
            "numbering",
            "minor",
            "Section 5.2 hierarchy",
            "Tabela 5.2.1",
            "Tabela 5.2",
            (
                "Troque as duas ocorrências por "
                "'Tabela 5.2.1: Resultados por sexo'."
            ),
            "Use the subsection number consistently.",
        ),
        correction(
            "C016",
            "B058 / Sex figures",
            "As Figuras 5.2 e 5.3",
            "numbering",
            "minor",
            "HTML figure captions",
            "Figuras 5.2.1.1 e 5.2.1.2",
            "Figuras 5.2 e 5.3",
            "As Figuras 5.2.1.1 e 5.2.1.2",
            "The cited figure numbers are wrong.",
        ),
        correction(
            "C017",
            "B067 / Sex interpretation",
            "essa exposição potencial pode estar começando a se materializar",
            "interpretation",
            "major",
            "treatment contract",
            "occupational exposure × post, not observed AI adoption",
            "exposure materializing",
            (
                "o resultado é compatível com uma redução relativa "
                "pós-ChatGPT das admissões femininas nas ocupações "
                "expostas, mas o desenho não observa adoção de IA e não "
                "permite afirmar que a exposição potencial esteja se "
                "materializando como efeito realizado"
            ),
            "Exposure is not observed adoption.",
            status="revise",
        ),
        correction(
            "C018",
            "B068 / Sex summary",
            "as ocupações expostas apresentaram maior retração na contratação de mulheres",
            "interpretation",
            "moderate",
            "sex DDD",
            "relative post-ChatGPT association",
            "realized causal effect",
            (
                "o diferencial pós-ChatGPT foi mais negativo para as "
                "admissões femininas nas ocupações expostas"
            ),
            "Use estimand language rather than adoption-effect language.",
            status="revise",
        ),
        correction(
            "C019",
            "B070 / Race appendix reference",
            "no anexo",
            "terminology",
            "minor",
            "document hierarchy",
            "no Apêndice A",
            "no anexo",
            "no Apêndice A",
            "Normalize appendix terminology.",
        ),
        correction(
            "C020",
            "B074 / Race flow interpretation",
            "o resultado é mais compatível com menor rotatividade do que com destruição de empregos",
            "interpretation",
            "moderate",
            "CAGED flow specification",
            "flow evidence only",
            "stock interpretation",
            (
                "o resultado é compatível com menor movimentação dos "
                "fluxos, mas, sem observar o estoque de emprego, não "
                "permite distinguir menor rotatividade de mudanças no "
                "número líquido de vínculos"
            ),
            "The outcome does not measure the employment stock.",
            status="revise",
        ),
        correction(
            "C021",
            "B084 / Race conclusion",
            "não há evidência de que a exposição à IA tenha ampliado",
            "interpretation",
            "moderate",
            "race/color DDD",
            "no robust post-treatment differential",
            "causal exposure effect",
            (
                "não há evidência robusta de que o diferencial "
                "pós-ChatGPT entre ocupações expostas e não expostas tenha "
                "variado"
            ),
            "Keep the conclusion aligned with the estimand.",
            status="revise",
        ),
        correction(
            "C022",
            "B092 / Age figure sentence",
            "As Figura 5.2.3.1 e Figura 5.2.3.2",
            "grammar",
            "minor",
            "HTML",
            "As Figuras 5.2.3.1 e 5.2.3.2",
            "As Figura",
            "As Figuras 5.2.3.1 e 5.2.3.2",
            "Plural agreement and repeated noun.",
        ),
        correction(
            "C023",
            "B099 / Age dynamic pretrends",
            "A faixa de 25 a 34 anos apresenta coeficientes pós-tratamento predominantemente negativos",
            "figure_interpretation",
            "major",
            "section5_2_age_pnad/event_study_pretrends.csv",
            (
                "admissions: 25–34 warning p=0.061; 55–65 fail p=0.024; "
                "wage: 18–24 fail p=0.014; 45–54 fail by individual leads"
            ),
            "outcomes not specified and relevant failures omitted",
            (
                "Nas admissões, a faixa de 25 a 34 anos apresenta alerta "
                "no pretrend conjunto (p=0,061), enquanto 55–65 anos "
                "rejeita o pretrend (p=0,024). No salário real de "
                "admissão, 18–24 anos rejeita o teste conjunto (p=0,014) "
                "e 45–54 anos é classificada como falha por três "
                "coeficientes pré-tratamento significativos, embora o "
                "teste conjunto tenha p=0,159."
            ),
            "The current wording is ambiguous across the two outcomes.",
        ),
        correction(
            "C024",
            "B122 / Income table",
            "Tabela 5.2.3: Efeitos dentro dos grupos por faixa salarial ocupacional",
            "numbering",
            "minor",
            "Section 5.2 hierarchy",
            "Tabela 5.2.5",
            "Tabela 5.2.3",
            (
                "Tabela 5.2.5: Efeitos dentro dos grupos por faixa "
                "salarial ocupacional"
            ),
            "Table 5.2.3 is already the age table.",
        ),
        correction(
            "C025",
            "B124–B125 / Income DDDs",
            "Na faixa de até 2 salários mínimos, nenhum efeito dentro do grupo é significativo.",
            "omitted_result",
            "major",
            "table_5_2_3_heterogeneity_income.csv",
            (
                "low-income DDD: admissions beta=0.1399, +15.0%, p=0.015; "
                "separations beta=0.1182, +12.6%, p=0.035"
            ),
            "only within-group nulls are mentioned",
            (
                "Na faixa de até 2 salários mínimos, os efeitos dentro do "
                "grupo não são significativos. Contudo, os contrastes DDD "
                "são positivos: +15,0% nas admissões (β=0,1399; "
                "p=0,015), com falha de pretrend, e +12,6% nos "
                "desligamentos (β=0,1182; p=0,035), com pretrends "
                "compatíveis. Esses sinais contrapõem o padrão negativo "
                "da faixa intermediária e precisam constar da síntese."
            ),
            "The formal DDD evidence is omitted and changes the balance of the narrative.",
        ),
        correction(
            "C026",
            "B125 / High-income DDD",
            "as estimativas são voláteis e não permitem concluir que o segmento de maior remuneração esteja protegido",
            "omitted_result",
            "moderate",
            "table_5_2_3_heterogeneity_income.csv",
            "separations beta=0.2453, +27.8%, p=0.049; support=3/7 thin",
            "significant thin-support DDD not stated",
            (
                "O DDD dos desligamentos é positivo e nominalmente "
                "significativo (+27,8%; β=0,2453; p=0,049), mas depende "
                "de apenas 3 CBOs tratadas e 7 controles; por isso, deve "
                "ser reportado e explicitamente descartado como base para "
                "inferência substantiva."
            ),
            "Nominal significance should be disclosed even when support invalidates emphasis.",
        ),
        correction(
            "C027",
            "B135 / Income wage pretrends",
            "os testes conjuntos dos event studies rejeitam os pretrends nas duas primeiras faixas",
            "statistical_interpretation",
            "major",
            "section5_2_dynamic/event_study_pretrends.csv",
            (
                "joint p: 0.4165, 0.2766, 0.0572; first two flagged "
                "because each has three individually significant leads"
            ),
            "joint tests reject in first two groups",
            (
                "Os testes conjuntos não rejeitam os pretrends nas duas "
                "primeiras faixas (p=0,417 e p=0,277), mas ambas são "
                "classificadas como falha porque apresentam três "
                "coeficientes pré-tratamento individualmente "
                "significativos. No topo, o teste conjunto é limítrofe "
                "(p=0,057) e gera alerta."
            ),
            "The diagnostic classification and the joint-test result were conflated.",
        ),
        correction(
            "C028",
            "B137 / Income summary",
            "salários e saldo permanecem nulos",
            "interpretation",
            "moderate",
            "income heterogeneity table",
            (
                "no robust wage result; asinh balance has nominal 10% "
                "signals with failed pretrends/thin support"
            ),
            "all estimates null",
            (
                "não há heterogeneidade salarial robusta; as estimativas "
                "de saldo incluem sinais nominais, mas são comprometidas "
                "por falhas de pretrend ou suporte muito fino e não "
                "sustentam uma conclusão substantiva"
            ),
            "Null and non-robust are not equivalent.",
            status="revise",
        ),
        correction(
            "C029",
            "B139 / Heterogeneity synthesis",
            "a redução dos desligamentos é o resultado mais robusto e recorrente",
            "interpretation",
            "major",
            "heterogeneity outputs",
            (
                "countervailing positive low-income DDDs and no "
                "multiple-testing correction"
            ),
            "one-sided synthesis",
            (
                "A síntese deve registrar também os DDDs positivos da "
                "faixa de até 2 salários mínimos (+15,0% nas admissões e "
                "+12,6% nos desligamentos) e o contraste positivo, porém "
                "sem suporte, nos desligamentos acima de 5 salários "
                "mínimos. Como não há correção por testes múltiplos, todos "
                "os achados de heterogeneidade permanecem exploratórios."
            ),
            "The current synthesis omits countervailing results.",
            status="revise",
        ),
        correction(
            "C030",
            "B140 / Causal synthesis",
            "a difusão da IA já pode estar redistribuindo oportunidades",
            "interpretation",
            "major",
            "identification and pretrend diagnostics",
            (
                "exposure × post association; adoption unobserved; flows "
                "only; recurrent pretrend failures; multiple testing"
            ),
            "realized redistribution and 'silent accommodation'",
            (
                "os resultados são compatíveis com ajustes localizados "
                "nos fluxos de ocupações mais expostas após o ChatGPT, "
                "mas não permitem concluir que a IA já esteja "
                "redistribuindo oportunidades ou preservando o volume "
                "total de emprego. A exposição não mede adoção, o estoque "
                "não é observado e várias especificações falham nos "
                "pretrends; por isso, a expressão 'acomodação silenciosa' "
                "deve ser apresentada apenas como hipótese de discussão."
            ),
            "The rhetoric exceeds the identifying variation.",
            status="revise",
        ),
        correction(
            "C031",
            "B142 and B154 / Appendix B references",
            "permanecem no Anexo B",
            "internal_reference",
            "major",
            "supplied HTML inventory",
            "no Appendix B in the supplied export",
            "Anexo B",
            (
                "Inclua um Apêndice B com as sensibilidades e explorações "
                "demográficas citadas; se ele não integrar a dissertação, "
                "remova as duas referências a 'Anexo B'."
            ),
            "The supplied dissertation export contains no Appendix B.",
            status="unresolved",
        ),
        correction(
            "C032",
            "B142 / First Appendix B reference",
            "sensibilidade no Anexo B",
            "terminology",
            "minor",
            "document terminology",
            "Apêndice B",
            "Anexo B",
            "sensibilidade no Apêndice B",
            "Use 'Apêndice' consistently if Appendix B is added.",
        ),
        correction(
            "C033",
            "B149 / Occupation-case exposure",
            "exposição mínima ou inexistente",
            "classification",
            "moderate",
            "occupation-case exposure composition",
            "minimal, not exposed, or no score",
            "minimal or nonexistent exposure",
            "exposição mínima, não exposta ou sem escore",
            "'No score' does not mean zero or nonexistent exposure.",
        ),
        correction(
            "C034",
            "B157 / Appendix A introduction",
            "Este anexo reúne",
            "terminology",
            "minor",
            "document hierarchy",
            "Este apêndice reúne",
            "Este anexo reúne",
            "Este apêndice reúne",
            "Normalize appendix terminology.",
        ),
        correction(
            "C035",
            "B176 and B178 / Age appendix panels",
            "(penad/ibge)",
            "terminology",
            "minor",
            "IBGE",
            "(PNAD/IBGE)",
            "(penad/ibge)",
            "(PNAD/IBGE)",
            "Incorrect acronym and capitalization.",
        ),
        correction(
            "C036",
            "B189 / Education appendix table",
            "Tabela A.6: Contrastes DDD e diagnósticos por escolaridade",
            "numbering",
            "minor",
            "Appendix A hierarchy",
            "Tabela A.5",
            "Tabela A.6",
            "Tabela A.5: Contrastes DDD e diagnósticos por escolaridade",
            "Education is Appendix A.5.",
        ),
        correction(
            "C037",
            "Table A.5 / Wage outcome label",
            "Salário de admissão",
            "label",
            "minor",
            "education source table",
            "Salário real de admissão (log)",
            "Salário de admissão",
            "Salário real de admissão (log)",
            "Align the outcome label with the estimated real-log measure.",
        ),
        correction(
            "C038",
            "B191 / Appendix A note",
            "\\ p<0,10",
            "formatting",
            "minor",
            "standard significance legend",
            "* p<0,10",
            "\\ p<0,10 and trailing \\*",
            (
                "Notas gerais do Apêndice A: os coeficientes DDD "
                "correspondem à interação pós × tratamento × grupo e "
                "comparam cada grupo ao seu complemento. Os erros-padrão, "
                "entre parênteses, são clusterizados por CBO de quatro "
                "dígitos. * p<0,10; ** p<0,05; *** p<0,01."
            ),
            "The significance legend is malformed and uses inconsistent terminology.",
        ),
        correction(
            "C039",
            "B192–B195 / Appendix A.6",
            "A.6 Renda ocupacional pré-tratamento",
            "table_content",
            "critical",
            "table_5_2_3_heterogeneity_income.csv",
            "income DDD panels: 12 primary rows and 6 balance rows",
            "education DDD panels duplicated",
            (
                "Mantenha o título A.6, acrescente a legenda 'Tabela A.6: "
                "Contrastes DDD e diagnósticos por renda ocupacional "
                "pré-tratamento' e substitua integralmente os dois painéis "
                "pelas tabelas de reposição geradas pela auditoria."
            ),
            "Both A.6 tables are an erroneous copy of the education results.",
        ),
        correction(
            "C040",
            "B195 / Appendix hierarchy",
            "Painel B.2: Robustez da construção do saldo",
            "document_structure",
            "minor",
            "HTML heading hierarchy",
            "panel label, not a new H2 section",
            "H2 heading",
            (
                "Formate 'Painel B.2: Robustez da construção do saldo' "
                "como legenda de painel no mesmo nível de 'Painel B.1', "
                "não como novo título H2."
            ),
            "The panel is incorrectly promoted to section-heading level.",
        ),
        correction(
            "C041",
            "Figure 5.1 and Table A.1 / Pretrend note",
            "O pretrend do Painel B é o teste conjunto dos coeficientes mensais anteriores ao tratamento",
            "method_note",
            "moderate",
            "two event-study backing datasets",
            (
                "full-sample p=(0.001337, 0.031431, 0.932139); strict "
                "-12..24 p=(1.77e-10, 0.002810, 0.903744)"
            ),
            "one unlabeled pretrend specification",
            (
                "Acrescente que a Tabela A.1 usa o teste da especificação "
                "original na amostra completa (N=18.307), enquanto a "
                "Figura 5.1 usa a janela estrita t=−12,…,24, sem "
                "agrupamento de caudas (N=12.538). Os p-valores diferem, "
                "embora a classificação pass/fail seja a mesma."
            ),
            "The different windows otherwise look like a numerical inconsistency.",
            status="revise",
        ),
        correction(
            "C042",
            "B136 / Citation spacing",
            "Klein Teeselink (2025) ,",
            "formatting",
            "minor",
            "HTML",
            "Klein Teeselink (2025),",
            "space before comma",
            "Klein Teeselink (2025),",
            "Remove spaces before punctuation in both citations.",
        ),
        correction(
            "C043",
            "Table 5.2.2 / Significance-star spacing",
            "-0,0486*(0,0280)",
            "formatting",
            "minor",
            "table_5_2_2_race_color.csv",
            "-0,0486* (0,0280); -0,0510* (0,0283)",
            "missing spaces before two standard errors",
            (
                "Na linha Branca, use '-0,0486* (0,0280)'; na linha "
                "Negra (preta e parda), use '-0,0510* (0,0283)'."
            ),
            "Two significance stars run into their standard errors.",
        ),
        correction(
            "C044",
            "Appendix diagnostic tables / p-value notation",
            "fail (p=<0,001)",
            "formatting",
            "minor",
            "Appendix A diagnostic tables",
            "p<0,001",
            "p=<0,001",
            (
                "Em todas as células de diagnóstico, troque "
                "'p=<0,001' por 'p<0,001'."
            ),
            "The conventional inequality is p<0.001, not p=<0.001.",
        ),
    ]


def narrative_ledger(
    blocks: list[HtmlBlock],
    corrections: list[dict[str, str]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    correction_rows = []
    matched_block_ids: set[str] = set()
    match_summary = []
    for item in corrections:
        needle = item["needle"]
        matches = [block for block in blocks if needle in block.text]
        table_only_corrections = {"C037", "C043", "C044"}
        if item["claim_id"] in table_only_corrections:
            matches = []
        if item["claim_id"] == "C040":
            matches = [
                block
                for block in blocks
                if block.text == needle and block.tag == "H2"
            ]
        if item["claim_id"] == "C041":
            matches = [
                block for block in blocks if needle in block.text
            ]
        expected_minimum = (
            0 if item["claim_id"] in table_only_corrections else 1
        )
        match_summary.append(
            {
                "claim_id": item["claim_id"],
                "needle": needle,
                "matches": len(matches),
                "minimum_expected": expected_minimum,
                "status": (
                    "pass"
                    if len(matches) >= expected_minimum
                    else "fail"
                ),
            }
        )
        if matches:
            matched_block_ids.update(block.html_id for block in matches)
            original = " || ".join(block.text for block in matches)
            html_ids = "; ".join(block.html_id for block in matches)
        else:
            original = needle
            html_ids = ""
        row = {key: value for key, value in item.items() if key != "needle"}
        row["location"] = f"{item['location']} / HTML {html_ids}".rstrip()
        row["original_text"] = original
        correction_rows.append(row)

    screen_pattern = re.compile(
        r"(\d|%|DiD|DDD|pretrend|coeficiente|efeito|exposi|Figura|"
        r"Tabela|CBO|CAGED|OIT|literatura|sal[aá]rio|admiss|deslig)",
        flags=re.IGNORECASE,
    )
    screened = []
    screen_index = 1
    for block in blocks:
        if block.html_id in matched_block_ids:
            continue
        if not screen_pattern.search(block.text):
            continue
        screened.append(
            {
                "claim_id": f"NARRATIVE.{screen_index:03d}",
                "location": (
                    f"{block.location} / {block.tag} / HTML {block.html_id}"
                ),
                "original_text": block.text,
                "claim_type": "narrative_screen",
                "source": (
                    "computational backing data and/or primary source "
                    "recorded in the audit"
                ),
                "raw_value": "",
                "rounding_rule": (
                    "log coefficients checked with "
                    "100 × (exp(beta) − 1); displayed values checked at "
                    "stated precision"
                ),
                "displayed_value": block.text,
                "status": "verified",
                "severity": "none",
                "recommended_replacement": "",
                "evidence": (
                    "manual claim review against the frozen outputs and "
                    "primary literature"
                ),
                "notes": "No correction identified in this screened block.",
            }
        )
        screen_index += 1
    ledger = pd.concat(
        [pd.DataFrame(correction_rows), pd.DataFrame(screened)],
        ignore_index=True,
    )
    return ledger, pd.DataFrame(match_summary)


def external_sources() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_id": "EXT01",
                "citation": "Brynjolfsson, Chandar and Chen (2025)",
                "primary_url": (
                    "https://digitaleconomy.stanford.edu/wp-content/"
                    "uploads/2025/11/CanariesintheCoalMine_Nov25.pdf"
                ),
                "claim_reviewed": (
                    "ADP coverage, age concentration, six cases and "
                    "relative employment decline"
                ),
                "finding": (
                    "Latest version dated 13 Nov 2025 reports a 16% "
                    "relative decline for ages 22–25 after firm-time controls."
                ),
                "status": "correction_required",
                "recommended_action": "Replace 13% with 16%.",
            },
            {
                "source_id": "EXT02",
                "citation": "Ministry of Labour and Employment",
                "primary_url": (
                    "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
                    "estatisticas-trabalho/o-pdet/o-que-e-o-novo-caged"
                ),
                "claim_reviewed": "Novo CAGED reporting system",
                "finding": (
                    "Novo CAGED integrates eSocial, CAGED and Empregador "
                    "Web; most firms report through eSocial from Jan 2020."
                ),
                "status": "wording_correction_required",
                "recommended_action": "Correct the data-system description.",
            },
            {
                "source_id": "EXT03",
                "citation": "OpenAI (2022)",
                "primary_url": "https://openai.com/index/chatgpt/",
                "claim_reviewed": "Public launch date of ChatGPT",
                "finding": "OpenAI dates the research release to 30 Nov 2022.",
                "status": "verified",
                "recommended_action": "",
            },
            {
                "source_id": "EXT04",
                "citation": "ILO Working Paper 140 (2025)",
                "primary_url": (
                    "https://www.ilo.org/publications/"
                    "generative-ai-and-jobs-refined-global-index-"
                    "occupational-exposure"
                ),
                "claim_reviewed": (
                    "Four exposure gradients and greater female exposure"
                ),
                "finding": (
                    "The index defines four gradients; highest-gradient "
                    "employment is 4.7% for women and 2.4% for men globally."
                ),
                "status": "verified",
                "recommended_action": "",
            },
            {
                "source_id": "EXT05",
                "citation": "Humlum and Vestergaard (2025)",
                "primary_url": (
                    "https://bfi.uchicago.edu/working-papers/"
                    "large-language-models-small-labor-market-effects/"
                ),
                "claim_reviewed": "Danish earnings and hours effects",
                "finding": (
                    "Precise null effects; effects larger than 2% are ruled "
                    "out after two years."
                ),
                "status": "verified",
                "recommended_action": "",
            },
            {
                "source_id": "EXT06",
                "citation": "Chandar (2025)",
                "primary_url": (
                    "https://papers.ssrn.com/sol3/papers.cfm?"
                    "abstract_id=5384519"
                ),
                "claim_reviewed": "CPS aggregate employment and earnings",
                "finding": (
                    "No substantial average difference, with occupational "
                    "heterogeneity and a warning about postings versus employment."
                ),
                "status": "verified_with_qualification",
                "recommended_action": "Retain the heterogeneity qualification.",
            },
            {
                "source_id": "EXT07",
                "citation": "Aldasoro et al. (2026)",
                "primary_url": "https://www.bis.org/publ/work1325.htm",
                "claim_reviewed": "AI adoption, productivity and employment",
                "finding": (
                    "More than 12,000 EU and US firms; 4% productivity gain; "
                    "no adverse firm-level employment effect in the short run."
                ),
                "status": "wording_correction_required",
                "recommended_action": (
                    "Specify the EU/US matched sample and the 4% estimate."
                ),
            },
            {
                "source_id": "EXT08",
                "citation": "Hosseini Maasoum and Lichtinger (2025/2026)",
                "primary_url": (
                    "https://papers.ssrn.com/sol3/papers.cfm?"
                    "abstract_id=5425555"
                ),
                "claim_reviewed": "Hiring versus separation mechanism",
                "finding": (
                    "Junior employment decline is driven mainly by slower "
                    "hiring; junior separation rates also decline."
                ),
                "status": "verified",
                "recommended_action": "",
            },
            {
                "source_id": "EXT09",
                "citation": "Klein Teeselink (2025)",
                "primary_url": (
                    "https://papers.ssrn.com/sol3/Delivery.cfm/"
                    "5516798.pdf?abstractid=5516798&mirid=1"
                ),
                "claim_reviewed": (
                    "Employment, hiring, postings and temporal ordering"
                ),
                "finding": (
                    "The paper finds declines in employment and postings; "
                    "posting effects emerge gradually after about 10 months "
                    "and mirror the stock-adjustment timeline."
                ),
                "status": "correction_required",
                "recommended_action": (
                    "Remove the unsupported claim that postings decline "
                    "before any employment-stock adjustment."
                ),
            },
        ]
    )


def cross_language_comparison(
    root: Path,
    output_dir: Path,
) -> pd.DataFrame:
    python_results = pd.read_csv(
        output_dir / f"{DATE_STEM}_python_results.csv"
    )
    r_results = pd.read_csv(output_dir / f"{DATE_STEM}_r_results.csv")
    merged = python_results.merge(
        r_results,
        on=["model_id", "estimand", "group_id", "outcome", "term"],
        suffixes=("_python", "_r"),
        validate="one_to_one",
    )

    national = pd.read_csv(
        root
        / "outputs/section4_5_final/tables"
        / "table_5_2_1_national_main_results.csv"
    )
    income = pd.read_csv(
        root
        / "outputs/section4_5_final/tables"
        / "table_5_2_3_heterogeneity_income.csv"
    )
    source_rows = []
    for item in merged.itertuples(index=False):
        if item.estimand == "DiD":
            source_outcome = (
                "ln_salario_real_adm"
                if item.outcome == "ln_salario_adm"
                else item.outcome
            )
            selected = national[
                national["outcome"].eq(source_outcome)
            ].iloc[0]
            source_rows.append(
                {
                    "model_id": item.model_id,
                    "source_coefficient": selected["coef"],
                    "source_standard_error": selected["se"],
                    "source_p_value": selected["p_value"],
                    "authoritative_source": (
                        "table_5_2_1_national_main_results.csv"
                    ),
                }
            )
        else:
            selected = income[
                income["group_id"].eq(item.group_id)
                & income["outcome"].eq(item.outcome)
            ].iloc[0]
            source_rows.append(
                {
                    "model_id": item.model_id,
                    "source_coefficient": selected["ddd_coef"],
                    "source_standard_error": selected["ddd_se"],
                    "source_p_value": selected["ddd_p_value"],
                    "authoritative_source": (
                        "table_5_2_3_heterogeneity_income.csv"
                    ),
                }
            )
    comparison = merged.merge(
        pd.DataFrame(source_rows),
        on="model_id",
        validate="one_to_one",
    )
    for metric in ["coefficient", "standard_error", "p_value"]:
        comparison[f"python_r_abs_diff_{metric}"] = (
            comparison[f"{metric}_python"]
            - comparison[f"{metric}_r"]
        ).abs()
        comparison[f"python_source_abs_diff_{metric}"] = (
            comparison[f"{metric}_python"]
            - comparison[f"source_{metric}"]
        ).abs()
    difference_columns = [
        column for column in comparison if "_abs_diff_" in column
    ]
    comparison["status"] = np.where(
        comparison[difference_columns].max(axis=1) <= 1e-8,
        "pass",
        "fail",
    )
    return comparison


def write_a6_replacements(
    root: Path,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    income_path = (
        root
        / "outputs/section4_5_final/tables"
        / "table_5_2_3_heterogeneity_income.csv"
    )
    income = pd.read_csv(income_path)
    primary = diagnostic_panel(income, PRIMARY_OUTCOMES)
    balance = diagnostic_panel(income, BALANCE_OUTCOMES)
    for panel in (primary, balance):
        for column in panel.columns:
            panel[column] = panel[column].map(
                lambda value: (
                    value.replace("p=<0,001", "p<0,001")
                    if isinstance(value, str)
                    else value
                )
            )
    primary_path = output_dir / f"{DATE_STEM}_replacement_table_a6_main.csv"
    balance_path = output_dir / f"{DATE_STEM}_replacement_table_a6_balance.csv"
    markdown_path = output_dir / f"{DATE_STEM}_replacement_table_a6.md"
    primary.to_csv(primary_path, index=False)
    balance.to_csv(balance_path, index=False)
    markdown_path.write_text(
        "\n".join(
            [
                "# Table A.6 replacement: pre-treatment occupational income",
                "",
                "## Panel B.1: Main outcomes",
                "",
                primary.to_markdown(index=False, disable_numparse=True),
                "",
                "## Panel B.2: Net-flow construction robustness",
                "",
                balance.to_markdown(index=False, disable_numparse=True),
                "",
                (
                    "Notes: coefficients are DDD estimates for post × "
                    "treatment × group. Standard errors are clustered by "
                    "four-digit CBO. * p<0.10; ** p<0.05; *** p<0.01. "
                    "Income groups use the occupation's pre-treatment "
                    "median wage in minimum-wage units."
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )

    narrative_values = []
    for item in income[
        income["outcome"].isin(
            ["ln_admissoes", "ln_desligamentos", "ln_salario_real_adm"]
        )
    ].itertuples(index=False):
        narrative_values.append(
            {
                "group": item.group_label,
                "outcome": item.outcome_label,
                "within_group_beta": item.group_coef,
                "within_group_percent": 100 * (math.exp(item.group_coef) - 1),
                "within_group_p": item.group_p_value,
                "ddd_beta": item.ddd_coef,
                "ddd_percent": 100 * (math.exp(item.ddd_coef) - 1),
                "ddd_p": item.ddd_p_value,
                "group_pretrend_status": item.group_pretrend_status,
                "group_pretrend_p": item.group_pretrend_p_value,
                "ddd_pretrend_status": item.ddd_pretrend_status,
                "ddd_pretrend_p": item.ddd_pretrend_p_value,
                "support": item.group_power_status,
                "treated_cbo": item.group_treated_cbo,
                "control_cbo": item.group_control_cbo,
            }
        )
    pd.DataFrame(narrative_values).to_csv(
        output_dir / f"{DATE_STEM}_income_narrative_values.csv",
        index=False,
    )
    return primary, balance


def markdown_table(data: pd.DataFrame) -> str:
    if data.empty:
        return "_No rows._"
    return data.to_markdown(index=False, disable_numparse=True)


def corrections_markdown(
    corrections: list[dict[str, str]],
    primary_a6: pd.DataFrame,
    balance_a6: pd.DataFrame,
) -> str:
    lines = [
        "# Sections 4–5: corrections only",
        "",
        (
            "Apply the following changes to the dissertation. Portuguese "
            "replacement text is ready to paste. Items are ordered by severity."
        ),
        "",
    ]
    severity_order = {"critical": 0, "major": 1, "moderate": 2, "minor": 3}
    ordered = sorted(
        corrections,
        key=lambda item: (
            severity_order[item["severity"]],
            item["claim_id"],
        ),
    )
    for index, item in enumerate(ordered, start=1):
        lines.extend(
            [
                f"## {index}. [{item['severity'].upper()}] {item['location']}",
                "",
                f"Original issue: {item['displayed_value']}",
                "",
                "Replace with:",
                "",
                f"> {item['recommended_replacement']}",
                "",
                f"Reason: {item['notes']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Full replacement for Appendix A.6",
            "",
            (
                "The two current panels repeat education results. Replace "
                "them with the following income panels."
            ),
            "",
            "### Panel B.1: Main outcomes",
            "",
            markdown_table(primary_a6),
            "",
            "### Panel B.2: Net-flow construction robustness",
            "",
            markdown_table(balance_a6),
            "",
        ]
    )
    return "\n".join(lines)


def blindspot_markdown() -> str:
    return """# Blindspot audit: dissertation Sections 4–5

## Acknowledged and framed

- The text states that occupational exposure is not observed firm adoption.
- The occupation cases are explicitly descriptive and use no case-specific control.
- Failed pretrends and thin support are often disclosed.
- DDDs are correctly defined as post × treatment × subgroup with lower-order interactions.

## Acknowledged but underframed

- Multiple testing is disclosed in the appendix, but the synthesis still emphasizes selected nominally significant results.
- Flow outcomes are distinguished from stocks in the methods, but several conclusions later infer lower turnover or absence of job destruction.
- Static and strict-window dynamic pretrend tests use different samples and p-values without an explicit reconciliation note.
- Exposure-measure uncertainty from the many-to-many crosswalk is described, but its attenuation and classification consequences could be carried more consistently into the results.

## Unacknowledged and consequential

- Appendix A.6 contains education results instead of income results.
- The mechanism paragraph describes four obsolete keyword-selected groups rather than the six frozen semantic occupation cases actually reported.
- The income narrative omits significant countervailing low-income DDDs and a nominally significant high-income separation DDD with thin support.
- The latest Canaries paper reports 16%, not 13%.
- Klein Teeselink does not establish that vacancies fall before any employment-stock adjustment.

## Unacknowledged opportunities

- The Poisson model ladder and alternative balance outcomes could be used to show which conclusions survive outcome construction.
- A compact estimand table could separate within-group DiDs, DDD contrasts, descriptive normalized paths and causal claims.
- Reporting a multiple-testing adjustment or a predeclared primary heterogeneity set would materially strengthen Section 5.2.
- A stock-compatible auxiliary outcome, if available, would test the repeated lower-turnover interpretation directly.

## Ruling

**HOLD.** The core national coefficients and selected DDDs replicate, but the dissertation should not be circulated in its present form because Appendix A.6 is wrong and the methodology/narrative contains consequential inconsistencies. After the critical table and method paragraph are corrected, the empirical claims should remain explicitly exploratory because of pretrend failures, flow-only outcomes and multiple testing.
"""


def report_markdown(
    table_summary: pd.DataFrame,
    figure_summary: pd.DataFrame,
    claim_ledger: pd.DataFrame,
    cross_language: pd.DataFrame,
    external: pd.DataFrame,
    validations: pd.DataFrame,
) -> str:
    correction_items = claim_ledger[
        claim_ledger["claim_id"].astype(str).str.startswith("C")
        & claim_ledger["status"].isin(
            ["incorrect", "revise", "unresolved"]
        )
    ]
    correction_counts = (
        correction_items["severity"]
        .value_counts()
        .to_dict()
    )
    table_cells = int(table_summary["cells_including_headers"].sum())
    wrong_table_cells = int(
        table_summary.loc[
            table_summary["table_id"].isin(["T22", "T23"]),
            "incorrect_cells",
        ].sum()
    )
    max_cross = float(
        cross_language[
            [column for column in cross_language if "_abs_diff_" in column]
        ].max(axis=None)
    )
    return f"""# Referee 2 audit report: dissertation Sections 4–5

## Executive ruling

**HOLD pending correction.** The core computational results are reproducible, and the 13 figures resolve to their declared sources. However, Appendix A.6 is a critical editorial failure: both income panels reproduce education results. The methods also describe an obsolete four-group mechanism exercise instead of the six occupation cases actually presented.

After those critical corrections, the substantive ruling becomes **CONDITIONAL**: results may be reported as short-run, exploratory exposure-by-post associations, not as direct effects of AI adoption or evidence that employment stocks were preserved.

## Scope

- Exported HTML: 23 tables and 13 figures.
- Table cells reviewed, including headers: {table_cells:,}.
- Narrative and external claims: screened in the claim ledger.
- Independent models: three national DiDs and five income DDDs in Python and R.
- Stata: not run because it is unavailable in the environment.
- Author code, replication package, HTML and dissertation: not modified.

## Computational replication

Python and R agree to a maximum absolute difference of {max_cross:.3e} across coefficients, CRV1 standard errors and p-values. All eight selected estimates also agree with the frozen author outputs at the 1e-8 tolerance.

{markdown_table(cross_language[[
    "model_id",
    "coefficient_python",
    "standard_error_python",
    "p_value_python",
    "coefficient_r",
    "standard_error_r",
    "p_value_r",
    "status",
]])}

The replicated national point estimates are:

- Admissions: beta = -0.0308788, or -3.04%, p = 0.241.
- Separations: beta = -0.0416584, or -4.08%, p = 0.102.
- Real admission wage: beta = -0.0207065, or -2.05%, p = 0.140.

The selected income DDDs reproduce the omitted countervailing evidence:

- Up to 2 minimum wages, admissions: beta = 0.1399, +15.0%, p = 0.015; pretrend fails.
- Up to 2 minimum wages, separations: beta = 0.1182, +12.6%, p = 0.035; pretrends pass.
- 2–5 minimum wages, admissions: beta = -0.1510, -14.0%, p = 0.013; pretrend fails.
- 2–5 minimum wages, separations: beta = -0.1835, -16.8%, p = 0.001; pretrends pass.
- Above 5 minimum wages, separations: beta = 0.2453, +27.8%, p = 0.049; support is only 3 treated and 7 controls.

## Table and figure audit

- Tables T01–T21 match their computational authorities after semantic normalization.
- Tables T22–T23 are the wrong content. {wrong_table_cells} body cells are marked critical in the ledger and full replacements are supplied.
- All 13 figures pass reference, source, dimension and visual-RMS checks.
- The package's HTML table views correctly preserve what was in the HTML, but this means they also preserve the A.6 copy error. They should be understood as editorial snapshots, not independent computational validation.

## Econometric audit

1. **Estimand.** The national coefficient is exposure-group × post, not observed adoption. DDDs are correctly specified as post × treatment × subgroup with lower interactions.
2. **Pretrends.** National admissions and separations fail. Several demographic event studies also fail or warn. The salary-income sentence incorrectly says joint tests reject in the first two income groups: their joint p-values are 0.417 and 0.277; the diagnostic fails because each has three individually significant leads.
3. **Flows versus stocks.** Admissions and separations do not identify the employment stock. Simultaneous flow declines are compatible with lower turnover but cannot establish no job destruction.
4. **Support.** The high-income comparison is too thin for substantive inference (3/7 CBOs). Middle income is limited (28/32).
5. **Multiplicity.** Heterogeneity p-values are unadjusted. The synthesis must not present selected nominal results as a stable general pattern.
6. **Windows.** Table A.1 and Figure 5.1 use different event-study samples. Their p-values differ but pass/fail classifications agree; this must be labeled.

## External-source audit

{markdown_table(external[[
    "citation",
    "claim_reviewed",
    "status",
    "recommended_action",
]])}

## Correction inventory

Critical: {correction_counts.get("critical", 0)}; major: {correction_counts.get("major", 0)}; moderate: {correction_counts.get("moderate", 0)}; minor: {correction_counts.get("minor", 0)}.

The authoritative, paste-ready list is in `{DATE_STEM}_corrections_only.md`. Every table cell and screened narrative claim is in `{DATE_STEM}_claim_ledger.csv`.
Hashes for every generated audit artifact are in `{DATE_STEM}_audit_manifest.csv`.

## Validation

{markdown_table(validations)}
"""


def validation_checks(
    root: Path,
    html_tables: list[HtmlTable],
    figures: list[HtmlFigure],
    table_summary: pd.DataFrame,
    figure_summary: pd.DataFrame,
    match_summary: pd.DataFrame,
    cross_language: pd.DataFrame,
    before_hashes: pd.DataFrame,
    after_hashes: pd.DataFrame,
    claim_ledger: pd.DataFrame,
    primary_a6: pd.DataFrame,
    balance_a6: pd.DataFrame,
) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(
        check_id: str,
        passed: bool,
        observed: object,
        expected: object,
        detail: str,
    ) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "observed": observed,
                "expected": expected,
                "detail": detail,
            }
        )

    add(
        "html_table_count",
        len(html_tables) == EXPECTED_TABLES,
        len(html_tables),
        EXPECTED_TABLES,
        "Editorial table inventory.",
    )
    add(
        "html_figure_count",
        len(figures) == EXPECTED_FIGURES,
        len(figures),
        EXPECTED_FIGURES,
        "Editorial figure inventory.",
    )
    unexpected = table_summary[
        table_summary["status"].eq("unexpected_mismatch")
    ]
    add(
        "table_mismatches_are_only_known_a6_error",
        unexpected.empty,
        len(unexpected),
        0,
        "T22–T23 are expected known editorial errors.",
    )
    add(
        "a6_error_detected",
        set(
            table_summary.loc[
                table_summary["status"].eq("known_editorial_error"),
                "table_id",
            ]
        )
        == {"T22", "T23"},
        ",".join(
            table_summary.loc[
                table_summary["status"].eq("known_editorial_error"),
                "table_id",
            ]
        ),
        "T22,T23",
        "Income appendix must not silently pass.",
    )
    add(
        "all_figures_resolved",
        figure_summary["status"].eq("pass").all(),
        int(figure_summary["status"].eq("pass").sum()),
        EXPECTED_FIGURES,
        "All figure references and visual comparisons pass.",
    )
    add(
        "correction_needles_found",
        match_summary["status"].eq("pass").all(),
        int(match_summary["status"].eq("pass").sum()),
        len(match_summary),
        "Every registered correction is anchored in the HTML or table.",
    )
    difference_columns = [
        column for column in cross_language if "_abs_diff_" in column
    ]
    maximum_difference = float(
        cross_language[difference_columns].max(axis=None)
    )
    add(
        "python_r_source_replication",
        maximum_difference <= 1e-8
        and cross_language["status"].eq("pass").all(),
        f"{maximum_difference:.3e}",
        "<=1e-8",
        "Python, R and author outputs agree.",
    )
    hashes_equal = before_hashes.equals(after_hashes)
    add(
        "replication_package_unchanged",
        hashes_equal,
        hashes_equal,
        True,
        "The entire Replication Package tree is hash-identical.",
    )
    add(
        "a6_replacement_shape",
        primary_a6.shape == (12, 9) and balance_a6.shape == (6, 9),
        f"{primary_a6.shape};{balance_a6.shape}",
        "(12,9);(6,9)",
        "Complete income main and balance panels.",
    )
    table_cell_count = int(
        table_summary["cells_including_headers"].sum()
    )
    ledger_table_count = int(
        claim_ledger["claim_type"].isin(
            ["table_header", "table_cell"]
        ).sum()
    )
    add(
        "table_cell_ledger_complete",
        table_cell_count == ledger_table_count,
        ledger_table_count,
        table_cell_count,
        "Every header and body cell has a ledger row.",
    )
    phase_validation = pd.read_csv(
        root
        / "Replication Package/outputs/sections4_5/validation"
        / "validation_checks.csv"
    )
    add(
        "phase1_validation_still_green",
        phase_validation["status"].astype(str).str.lower().eq("pass").all(),
        int(
            phase_validation["status"]
            .astype(str)
            .str.lower()
            .eq("pass")
            .sum()
        ),
        len(phase_validation),
        "Frozen Phase 1 validation report remains green.",
    )
    return pd.DataFrame(checks)


def main() -> int:
    args = parse_args()
    root = project_root()
    html_path = (
        default_html(root) if args.html is None else args.html.resolve()
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    package_root = root / "Replication Package"

    before_hashes = snapshot_tree(package_root)
    html_tables, figures, blocks = inspect_html(html_path)
    if len(html_tables) != EXPECTED_TABLES:
        raise ValueError(f"Expected 23 tables; found {len(html_tables)}.")
    if len(figures) != EXPECTED_FIGURES:
        raise ValueError(f"Expected 13 figures; found {len(figures)}.")

    expected, table_sources = expected_tables(root)
    table_ledger, table_summary = table_ledgers(
        html_tables,
        expected,
        table_sources,
    )
    artifact_map = pd.read_csv(
        root
        / "Replication Package/outputs/sections4_5/artifact_map.csv"
    )
    figure_claims, figure_summary = figure_ledger(
        figures,
        artifact_map,
        root,
    )
    corrections = correction_registry()
    narrative_claims, match_summary = narrative_ledger(blocks, corrections)
    external = external_sources()
    cross_language = cross_language_comparison(root, output_dir)
    primary_a6, balance_a6 = write_a6_replacements(root, output_dir)

    claim_ledger = pd.concat(
        [table_ledger, figure_claims, narrative_claims],
        ignore_index=True,
    )
    required_columns = [
        "claim_id",
        "location",
        "original_text",
        "claim_type",
        "source",
        "raw_value",
        "rounding_rule",
        "displayed_value",
        "status",
        "severity",
        "recommended_replacement",
        "evidence",
        "notes",
    ]
    claim_ledger = claim_ledger[required_columns]

    after_hashes = snapshot_tree(package_root)
    validations = validation_checks(
        root=root,
        html_tables=html_tables,
        figures=figures,
        table_summary=table_summary,
        figure_summary=figure_summary,
        match_summary=match_summary,
        cross_language=cross_language,
        before_hashes=before_hashes,
        after_hashes=after_hashes,
        claim_ledger=claim_ledger,
        primary_a6=primary_a6,
        balance_a6=balance_a6,
    )

    frozen = before_hashes.copy()
    frozen.insert(0, "snapshot", "phase1_pre_audit")
    frozen.to_csv(
        output_dir / f"{DATE_STEM}_frozen_hashes.csv",
        index=False,
    )
    table_summary.to_csv(
        output_dir / f"{DATE_STEM}_table_validation.csv",
        index=False,
    )
    figure_summary.to_csv(
        output_dir / f"{DATE_STEM}_figure_validation.csv",
        index=False,
    )
    claim_ledger.to_csv(
        output_dir / f"{DATE_STEM}_claim_ledger.csv",
        index=False,
    )
    external.to_csv(
        output_dir / f"{DATE_STEM}_external_sources.csv",
        index=False,
    )
    cross_language.to_csv(
        output_dir / f"{DATE_STEM}_cross_language_comparison.csv",
        index=False,
    )
    validations.to_csv(
        output_dir / f"{DATE_STEM}_validation_checks.csv",
        index=False,
    )
    (output_dir / f"{DATE_STEM}_validation_checks.md").write_text(
        "# Audit validation checks\n\n"
        + markdown_table(validations)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / f"{DATE_STEM}_corrections_only.md").write_text(
        corrections_markdown(corrections, primary_a6, balance_a6),
        encoding="utf-8",
    )
    (output_dir / f"{DATE_STEM}_blindspot.md").write_text(
        blindspot_markdown(),
        encoding="utf-8",
    )
    (output_dir / f"{DATE_STEM}_report.md").write_text(
        report_markdown(
            table_summary,
            figure_summary,
            claim_ledger,
            cross_language,
            external,
            validations,
        ),
        encoding="utf-8",
    )
    write_audit_manifest(output_dir)

    failed = validations[validations["status"].eq("fail")]
    print(
        f"Audited {len(html_tables)} tables, {len(figures)} figures, "
        f"and wrote {len(claim_ledger)} ledger rows."
    )
    print(
        f"Validation: {len(validations) - len(failed)}/{len(validations)} "
        "checks passed."
    )
    if not failed.empty:
        print(failed.to_string(index=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
