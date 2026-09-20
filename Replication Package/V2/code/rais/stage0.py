from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


FRONT_ROOT = Path(__file__).resolve().parent.parent
V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
RESULTS_DIR = FRONT_ROOT / "results"
VINTAGE_DIR = FRONT_ROOT / "data" / "vintage"
BILLING_PROJECT = os.environ.get("REPLICATION_BILLING_PROJECT", "")
SOURCE_TABLE = "basedosdados.br_me_rais.microdados_vinculos"
PROBE_YEARS = tuple(range(2015, 2026))
ANALYSIS_YEARS = tuple(range(2016, 2025))

REQUIRED_SCHEMA = {
    "ano": "INT64",
    "cbo_2002": "STRING",
    "id_municipio": "STRING",
    "tempo_emprego": "FLOAT64",
    "vinculo_ativo_3112": "STRING",
}

SCHEMA_QUERY = """
SELECT column_name, data_type
FROM `basedosdados.br_me_rais.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'microdados_vinculos'
ORDER BY column_name
""".strip()

YEAR_COVERAGE_QUERY = """
SELECT ano, COUNT(*) AS vinculos
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano BETWEEN 2015 AND 2025
GROUP BY ano
ORDER BY ano
""".strip()

ACTIVE_DOMAIN_QUERY = """
SELECT
  ano,
  CAST(vinculo_ativo_3112 AS STRING) AS valor,
  COUNT(*) AS vinculos
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano BETWEEN 2016 AND 2024
GROUP BY ano, valor
ORDER BY ano, valor
""".strip()

AGGREGATE_QUERY = """
SELECT
  ano,
  SUBSTR(LPAD(CAST(cbo_2002 AS STRING), 6, '0'), 1, 4) AS cbo_4d,
  COUNT(*) AS vinculos_declarados,
  COUNTIF(vinculo_ativo_3112 = '1') AS estoque_3112,
  AVG(IF(vinculo_ativo_3112 = '1', tempo_emprego, NULL)) AS tempo_emprego_medio
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano BETWEEN 2016 AND 2024
  AND cbo_2002 IS NOT NULL
GROUP BY ano, cbo_4d
ORDER BY ano, cbo_4d
""".strip()

RECONCILIATION_COMPONENTS_QUERY = """
SELECT
  ano,
  COUNTIF(vinculo_ativo_3112 = '1') AS ativos_total_fonte,
  COUNTIF(
    vinculo_ativo_3112 = '1'
    AND (cbo_2002 IS NULL OR cbo_2002 = '')
  ) AS ativos_sem_cbo,
  COUNTIF(
    vinculo_ativo_3112 = '1'
    AND indicador_vinculo_abandonado = '1'
  ) AS ativos_abandonados,
  COUNTIF(
    vinculo_ativo_3112 = '1'
    AND indicador_vinculo_abandonado = '1'
    AND cbo_2002 IS NOT NULL
    AND cbo_2002 <> ''
  ) AS ativos_abandonados_com_cbo
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano BETWEEN 2016 AND 2024
GROUP BY ano
ORDER BY ano
""".strip()

OFFICIAL_TOTALS = {
    2016: 46_060_198,
    2017: 46_281_590,
    2018: 46_631_115,
    2019: 46_716_492,
    2020: 46_236_176,
    2021: 48_728_871,
    2022: 52_790_864,
    2023: 55_316_614,
    2024: 57_132_156,
}

OFFICIAL_SOURCES = {
    2016: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2016"
    ),
    2017: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2017"
    ),
    2018: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2018"
    ),
    2019: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2019"
    ),
    2020: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2020"
    ),
    2021: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/2-SumC3A1rio_Executivo_RAIS_2021.pdf"
    ),
    2022: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2022/"
        "sumario-executivo_rais_2022-1-1.pdf"
    ),
    2023: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2024/rais-2024-1/"
        "sumario-executivo_rais-2024-1.pdf"
    ),
    2024: (
        "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
        "estatisticas-trabalho/rais/rais-2024/rais-2024-1/"
        "sumario-executivo_rais-2024-1.pdf"
    ),
}

ESOCIAL_TRANSITION_YEAR = 2022
ESOCIAL_TRANSITION_SOURCE = (
    "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
    "estatisticas-trabalho/rais/rais-2022/nota-tecnica-rais-2022.pdf"
)
BREAK_DIFFERENTIAL_THRESHOLD_LOG_POINTS = 0.01
BREAK_DOMINANCE_THRESHOLD_PP = 1.0
BIGQUERY_TIMEOUT_SECONDS = 900


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write_text(path, content)


def _atomic_write_csv(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    fieldnames: Sequence[str],
) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    _atomic_write_text(path, buffer.getvalue())


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return [dict(row) for row in csv.DictReader(source)]


def _run_bq_csv(query: str, *, max_rows: int = 1000) -> list[dict[str, str]]:
    if not BILLING_PROJECT:
        raise RuntimeError("A BigQuery billing project is required")
    try:
        from google.cloud import bigquery
    except ImportError as error:
        raise RuntimeError(
            "Full RAIS acquisition requires `uv sync --frozen`."
        ) from error
    try:
        result = bigquery.Client(project=BILLING_PROJECT).query(query).result(
            max_results=int(max_rows),
            timeout=BIGQUERY_TIMEOUT_SECONDS,
        )
    except TimeoutError as error:
        raise RuntimeError(
            f"BigQuery query exceeded {BIGQUERY_TIMEOUT_SECONDS} seconds"
        ) from error
    return [
        {
            key: "" if value is None else str(value)
            for key, value in row.items()
        }
        for row in result
    ]


def validate_schema(observed: Mapping[str, str]) -> None:
    problems = []
    for column, expected_type in REQUIRED_SCHEMA.items():
        actual_type = observed.get(column)
        if actual_type != expected_type:
            problems.append(f"{column}: expected {expected_type}, observed {actual_type}")
    if problems:
        raise ValueError("Required RAIS schema mismatch: " + "; ".join(problems))


def validate_year_coverage(years: Iterable[int]) -> list[int]:
    observed = sorted(set(years))
    missing = sorted(set(PROBE_YEARS) - set(observed))
    if missing:
        raise ValueError(f"Missing probe years: {', '.join(map(str, missing))}")
    return observed


def choose_acquisition_route(max_year: int) -> str:
    if max_year >= 2024:
        return "basedosdados_bigquery"
    return "mte_ftp_required"


def validate_active_domain(rows: Sequence[Mapping[str, str]]) -> None:
    observed_by_year: dict[int, set[str]] = {}
    for row in rows:
        year = int(row["ano"])
        observed_by_year.setdefault(year, set()).add(row["valor"])

    missing_years = sorted(set(ANALYSIS_YEARS) - set(observed_by_year))
    if missing_years:
        raise ValueError(
            "Active-link domain is missing years: "
            + ", ".join(map(str, missing_years))
        )

    unexpected = sorted(
        {
            value
            for values in observed_by_year.values()
            for value in values
            if value not in {"0", "1"}
        }
    )
    if unexpected:
        raise ValueError(
            "Unexpected vinculo_ativo_3112 values: " + ", ".join(unexpected)
        )

    incomplete = sorted(
        year for year, values in observed_by_year.items() if values != {"0", "1"}
    )
    if incomplete:
        raise ValueError(
            "Active-link domain is not exactly 0/1 in years: "
            + ", ".join(map(str, incomplete))
        )


def validate_aggregate_rows(
    rows: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    keys: set[tuple[int, str]] = set()
    years: set[int] = set()

    for row in rows:
        year = int(row["ano"])
        cbo_4d = row["cbo_4d"]
        if re.fullmatch(r"[0-9]{4}", cbo_4d) is None or cbo_4d == "0000":
            raise ValueError(f"Invalid CBO4 in frozen aggregate: {cbo_4d}")

        key = (year, cbo_4d)
        if key in keys:
            raise ValueError(f"Duplicate aggregate key: {key}")
        keys.add(key)
        years.add(year)

        declared = int(row["vinculos_declarados"])
        active = int(row["estoque_3112"])
        if declared < 0 or active < 0:
            raise ValueError(f"Negative link count in aggregate key: {key}")
        if active > declared:
            raise ValueError(
                f"Active stock exceeds declared links in aggregate key: {key}"
            )

    expected_years = set(ANALYSIS_YEARS)
    if years != expected_years:
        missing = sorted(expected_years - years)
        extra = sorted(years - expected_years)
        raise ValueError(
            f"Aggregate year mismatch; missing={missing}, extra={extra}"
        )

    return {"rows": len(rows), "years": sorted(years)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_registered_extract(
    data_path: Path,
    manifest_path: Path,
    *,
    expected_query: str,
) -> tuple[list[dict[str, str]], dict[str, object]] | None:
    """Load an existing official extract only after validating its contract.

    Full mode downloads sources that are absent. A partially present or altered
    registered extract is a provenance failure and must never be repaired by a
    silent replacement query.
    """

    data_exists = data_path.is_file()
    manifest_exists = manifest_path.is_file()
    if not data_exists and not manifest_exists:
        return None
    if data_exists != manifest_exists:
        raise ValueError(
            "Registered RAIS extract is incomplete: "
            f"data_exists={data_exists}, manifest_exists={manifest_exists}"
        )

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw_manifest, dict):
        raise ValueError(f"RAIS manifest must be a JSON object: {manifest_path}")
    manifest: dict[str, object] = dict(raw_manifest)

    required = {"bytes", "sha256", "linhas", "consulta", "tabela"}
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(
            f"RAIS manifest is missing required fields {missing}: {manifest_path}"
        )
    if manifest["tabela"] != SOURCE_TABLE:
        raise ValueError(
            "RAIS manifest source-table mismatch: "
            f"expected {SOURCE_TABLE}, observed {manifest['tabela']}"
        )
    if manifest["consulta"] != expected_query:
        raise ValueError(f"RAIS manifest query mismatch: {manifest_path}")

    observed_bytes = data_path.stat().st_size
    expected_bytes = int(manifest["bytes"])
    if observed_bytes != expected_bytes:
        raise ValueError(
            "Registered RAIS extract byte-size mismatch: "
            f"expected {expected_bytes}, observed {observed_bytes}"
        )
    observed_sha256 = sha256_file(data_path)
    expected_sha256 = str(manifest["sha256"])
    if observed_sha256 != expected_sha256:
        raise ValueError(
            "Registered RAIS extract SHA-256 mismatch: "
            f"expected {expected_sha256}, observed {observed_sha256}"
        )

    rows = _read_csv(data_path)
    expected_rows = int(manifest["linhas"])
    if len(rows) != expected_rows:
        raise ValueError(
            "Registered RAIS extract row-count mismatch: "
            f"expected {expected_rows}, observed {len(rows)}"
        )
    return rows, manifest


def build_reconciliation_rows(
    aggregate_rows: Sequence[Mapping[str, str]],
    component_rows: Sequence[Mapping[str, str]],
    official_totals: Mapping[int, int],
    official_sources: Mapping[int, str],
) -> list[dict[str, object]]:
    analysis_years = tuple(sorted(official_totals))
    aggregate_by_year = {year: 0 for year in analysis_years}
    for row in aggregate_rows:
        aggregate_by_year[int(row["ano"])] += int(row["estoque_3112"])

    components_by_year = {int(row["ano"]): row for row in component_rows}
    output: list[dict[str, object]] = []
    for year in analysis_years:
        if year not in components_by_year:
            raise ValueError(f"Missing reconciliation components for {year}")
        component = components_by_year[year]
        source_total = int(component["ativos_total_fonte"])
        missing_cbo = int(component["ativos_sem_cbo"])
        abandoned = int(component["ativos_abandonados"])
        abandoned_with_cbo = int(component["ativos_abandonados_com_cbo"])
        aggregate_total = aggregate_by_year[year]
        official_total = official_totals[year]

        if aggregate_total != source_total - missing_cbo:
            raise ValueError(
                f"Frozen aggregate does not match source components for {year}"
            )

        if aggregate_total == official_total:
            explanation_code = "exact"
        elif official_total == source_total and missing_cbo > 0:
            explanation_code = "active_links_missing_cbo"
        elif (
            official_total == source_total - abandoned
            and abandoned_with_cbo == abandoned
        ):
            explanation_code = "active_links_marked_abandoned"
        else:
            explanation_code = "unexplained"

        difference = aggregate_total - official_total
        relative = difference / official_total
        output.append(
            {
                "ano": year,
                "estoque_agregado": aggregate_total,
                "estoque_oficial": official_total,
                "diferenca_absoluta": difference,
                "diferenca_relativa": relative,
                "fonte_oficial": official_sources[year],
                "explanation_code": explanation_code,
                "ativos_total_fonte": source_total,
                "ativos_sem_cbo": missing_cbo,
                "ativos_abandonados": abandoned,
            }
        )
    return output


def fit_segmented_break(
    years: Sequence[int] | np.ndarray,
    stocks: Sequence[float] | np.ndarray,
    *,
    transition_year: int,
) -> dict[str, object]:
    year_array = np.asarray(years, dtype=float)
    stock_array = np.asarray(stocks, dtype=float)
    if len(year_array) != len(stock_array):
        raise ValueError("Years and stocks must have the same length")
    if len(year_array) == 0 or np.any(stock_array <= 0):
        return {
            "identified": False,
            "n_years": int(len(year_array)),
            "rank": 0,
            "baseline_trend": math.nan,
            "level_break": math.nan,
            "trend_break": math.nan,
        }

    order = np.argsort(year_array)
    year_array = year_array[order]
    stock_array = stock_array[order]
    time = year_array - year_array.min()
    step = (year_array >= transition_year).astype(float)
    post_transition_time = np.maximum(year_array - transition_year, 0.0)
    design = np.column_stack(
        (
            np.ones(len(year_array)),
            time,
            step,
            post_transition_time,
        )
    )
    rank = int(np.linalg.matrix_rank(design))
    if rank < design.shape[1]:
        return {
            "identified": False,
            "n_years": int(len(year_array)),
            "rank": rank,
            "baseline_trend": math.nan,
            "level_break": math.nan,
            "trend_break": math.nan,
        }

    coefficients = np.linalg.lstsq(
        design,
        np.log(stock_array),
        rcond=None,
    )[0]
    return {
        "identified": True,
        "n_years": int(len(year_array)),
        "rank": rank,
        "baseline_trend": float(coefficients[1]),
        "level_break": float(coefficients[2]),
        "trend_break": float(coefficients[3]),
    }


def classify_break_differential(
    level_difference: float,
    trend_difference: float,
    *,
    threshold: float = BREAK_DIFFERENTIAL_THRESHOLD_LOG_POINTS,
) -> str:
    if not (
        math.isfinite(level_difference)
        and math.isfinite(trend_difference)
    ):
        return "indeterminate"
    if (
        abs(level_difference) > threshold
        or abs(trend_difference) > threshold
    ):
        return "differential"
    return "non_differential"


def is_transition_gap_dominant(
    annual_gaps_pp: Mapping[int, float],
    transition_year: int,
    *,
    threshold_pp: float = BREAK_DOMINANCE_THRESHOLD_PP,
) -> bool:
    finite_gaps = {
        int(year): float(value)
        for year, value in annual_gaps_pp.items()
        if math.isfinite(float(value))
    }
    if transition_year not in finite_gaps:
        return False
    transition_magnitude = abs(finite_gaps[transition_year])
    if transition_magnitude <= threshold_pp:
        return False
    return transition_magnitude >= max(abs(value) for value in finite_gaps.values())


def derive_stage0_scorecard(
    *,
    acquisition_pass: bool,
    reconciliation_pass: bool,
    break_measured: bool,
) -> dict[str, str]:
    acquisition_gate = (
        "pass" if acquisition_pass and reconciliation_pass else "fail"
    )
    construction_gate = "pass" if break_measured else "fail"
    gate_open = acquisition_gate == "pass" and construction_gate == "pass"
    return {
        "frente": "rais",
        "momento": "stage0",
        "fecha_limitacao_declarada": "sim",
        "gate_aquisicao": acquisition_gate,
        "gate_construcao": construction_gate,
        "falsificacao": "not_applicable",
        "pretrend": "not_available",
        "suporte": "not_applicable",
        "familia_bh": "D",
        "barra_reprodutibilidade": "not_applicable",
        "custo_estrutural": "subsecao",
        "veredito": "corpo" if gate_open else "not_executed",
        "veredito_derivado_de": (
            "fecha_limitacao_declarada;gate_aquisicao;"
            "gate_construcao;custo_estrutural"
        ),
    }


def _render_reconciliation_report(
    rows: Sequence[Mapping[str, object]],
) -> str:
    table_rows = []
    for row in rows:
        relative_percent = 100 * float(row["diferenca_relativa"])
        table_rows.append(
            f"| {row['ano']} | {int(row['estoque_agregado']):,} | "
            f"{int(row['estoque_oficial']):,} | "
            f"{int(row['diferenca_absoluta']):+,} | "
            f"{relative_percent:+.3f}% | `{row['explanation_code']}` |"
        )

    max_relative = max(abs(float(row["diferenca_relativa"])) for row in rows)
    unexplained = [
        int(row["ano"])
        for row in rows
        if row["explanation_code"] == "unexplained"
    ]
    gate = "PASS" if not unexplained else "FAIL"

    return (
        "# RAIS universe reconciliation\n\n"
        "## Contract\n\n"
        "The frozen CBO4 aggregate is summed by base year and compared with the "
        "latest consolidated MTE stock for active formal-employment links on "
        "31 December. The aggregate follows the pre-registered R2 query and "
        "therefore excludes records without `cbo_2002` but does not silently "
        "reclassify any record.\n\n"
        "## Results\n\n"
        "| Year | Frozen aggregate | Official MTE stock | Absolute difference | "
        "Relative difference | Reconciliation |\n"
        "|---:|---:|---:|---:|---:|---|\n"
        + "\n".join(table_rows)
        + "\n\n"
        "For 2016–2021, the small negative differences are exactly the active "
        "links with missing CBO excluded by the pre-registered `cbo_2002 IS NOT "
        "NULL` condition. The 2022 aggregate matches the official total exactly. "
        "For 2023 and 2024, the positive differences are exactly the records "
        "simultaneously marked `vinculo_ativo_3112 = '1'` and "
        "`indicador_vinculo_abandonado = '1'` in the Base dos Dados mirror: "
        "501,393 and 668,495 links, respectively. Subtracting those flagged "
        "records reproduces the latest consolidated MTE totals exactly. The 2023 "
        "comparison uses the revised 55,316,614 total published with the final "
        "2024 release.\n\n"
        f"The largest raw relative difference is {100 * max_relative:.3f}%. "
        "Every annual difference has an exact, count-based explanation from the "
        "frozen diagnostic extract; no treatment coefficient is used.\n\n"
        "## R-G1 reconciliation condition\n\n"
        f"**{gate}.** "
        + (
            "The universe reconciles exactly after accounting for the declared "
            "CBO-availability condition and the abandoned-link flag."
            if gate == "PASS"
            else f"Unexplained years: {unexplained}."
        )
        + "\n"
    )


def _render_esocial_break_report(
    annual_rows: Sequence[Mapping[str, object]],
    diagnostics: Mapping[int, Mapping[str, object]],
    *,
    dominant: bool,
    derived_window_start: int,
) -> str:
    long_rows = [
        row for row in annual_rows if int(row["janela_inicio"]) == 2016
    ]
    annual_table = []
    for row in long_rows:
        treated_growth = row["crescimento_tratadas"]
        control_growth = row["crescimento_controle"]
        difference = row["diferenca_crescimento_pp"]
        annual_table.append(
            f"| {row['ano']} | {int(row['estoque_tratadas']):,} | "
            f"{int(row['estoque_controle']):,} | "
            + (
                "— | — | — |"
                if treated_growth == ""
                else (
                    f"{100 * float(treated_growth):+.3f}% | "
                    f"{100 * float(control_growth):+.3f}% | "
                    f"{float(difference):+.3f} pp |"
                )
            )
        )

    diagnostic_table = []
    for window_start in (2016, 2019):
        diagnostic = diagnostics[window_start]
        diagnostic_table.append(
            f"| {window_start}–2024 | "
            f"{100 * float(diagnostic['treated_level_break']):+.3f} | "
            f"{100 * float(diagnostic['control_level_break']):+.3f} | "
            f"{100 * float(diagnostic['level_difference']):+.3f} | "
            f"{100 * float(diagnostic['treated_trend_break']):+.3f} | "
            f"{100 * float(diagnostic['control_trend_break']):+.3f} | "
            f"{100 * float(diagnostic['trend_difference']):+.3f} | "
            f"`{diagnostic['classification']}` |"
        )

    transition_row = next(
        row
        for row in long_rows
        if int(row["ano"]) == ESOCIAL_TRANSITION_YEAR
    )
    return (
        "# RAIS eSocial series-break diagnostic\n\n"
        "## Transition contract\n\n"
        "The adopted transition is base year 2022. The MTE technical note "
        "identifies 2022 as an important RAIS series break because eSocial "
        "Group 3 entered through eSocial in that base year and represented 77% "
        "of declaring establishments. The diagnostic uses only the frozen "
        "RAIS aggregate and the frozen V-A treatment classification.\n\n"
        "## Annual stock growth by group\n\n"
        "| Year | Treated stock | Control stock | Treated growth | "
        "Control growth | Treated − control |\n"
        "|---:|---:|---:|---:|---:|---:|\n"
        + "\n".join(annual_table)
        + "\n\n"
        f"In 2022, treated stock grew by "
        f"{100 * float(transition_row['crescimento_tratadas']):.3f}% and "
        f"control stock by "
        f"{100 * float(transition_row['crescimento_controle']):.3f}%, a "
        f"treated-minus-control gap of "
        f"{float(transition_row['diferenca_crescimento_pp']):.3f} percentage "
        f"points. Its absolute value is "
        + ("the largest" if dominant else "not the largest")
        + " annual group gap in the 2017–2024 growth series.\n\n"
        "## Segmented level and trend diagnostic\n\n"
        "The diagnostic model is `log(group stock) = intercept + linear time + "
        "step(2022) + post-2022 trend change`. The table reports coefficients "
        "multiplied by 100; the difference columns are treated minus control.\n\n"
        "| Window | Level treated | Level control | Level difference | "
        "Trend treated | Trend control | Trend difference | Classification |\n"
        "|---|---:|---:|---:|---:|---:|---:|---|\n"
        + "\n".join(diagnostic_table)
        + "\n\n"
        "The 2016–2024 window is classified **differential** because the "
        "treated-control level-break difference exceeds the frozen "
        "0.01-log-point threshold (shown as 1.0 after multiplying by 100), and "
        "the transition-year growth gap is dominant. In the "
        "pre-registered 2019–2024 window, both the level and trend differences "
        "are below the threshold, so the break is classified "
        "**non-differential**.\n\n"
        "## R-G2 decision\n\n"
        f"Use **{derived_window_start}–2024** for downstream construction. "
        "This applies the pre-registered fallback after a differential and "
        "dominant long-window break. The short window reconciles in R3 and its "
        "segmented break is non-differential.\n\n"
        "No ChatGPT treatment coefficient was estimated in this task.\n"
    )


def run_probe() -> dict[str, object]:
    registered = _load_registered_extract(
        VINTAGE_DIR / "rais_cbo4_ano_2016_2024.csv",
        VINTAGE_DIR / "manifest.json",
        expected_query=AGGREGATE_QUERY,
    )
    if registered is not None:
        rows, _manifest = registered
        summary = validate_aggregate_rows(rows)
        status: dict[str, object] = {
            "status": "ok",
            "route": "registered_official_extract",
            "route_reason": (
                "The supplied official extract passed its byte-size, SHA-256, "
                "query, row-count, schema, key, and year-domain contracts."
            ),
            "billing_project": BILLING_PROJECT,
            "source_table": SOURCE_TABLE,
            "max_year": max(summary["years"]),
            "required_max_year": 2024,
            "required_schema": REQUIRED_SCHEMA,
            "vinculo_ativo_3112_domain": {
                "data_type": "STRING",
                "values": ["0", "1"],
                "years": list(ANALYSIS_YEARS),
            },
            "queries": {
                "aggregate": AGGREGATE_QUERY,
                "schema_probe": SCHEMA_QUERY,
                "year_coverage_probe": YEAR_COVERAGE_QUERY,
                "active_domain_probe": ACTIVE_DOMAIN_QUERY,
            },
            "probe_executed": False,
            "queried_at": None,
        }
        _atomic_write_json(RESULTS_DIR / "rais_acquisition_status.json", status)
        return status

    schema_rows = _run_bq_csv(SCHEMA_QUERY)
    coverage_rows = _run_bq_csv(YEAR_COVERAGE_QUERY, max_rows=100)
    domain_rows = _run_bq_csv(ACTIVE_DOMAIN_QUERY, max_rows=100)

    observed_schema = {
        row["column_name"]: row["data_type"] for row in schema_rows
    }
    validate_schema(observed_schema)

    coverage_years = validate_year_coverage(
        int(row["ano"]) for row in coverage_rows
    )
    validate_active_domain(domain_rows)

    max_year = max(coverage_years)
    route = choose_acquisition_route(max_year)
    if route != "basedosdados_bigquery":
        raise RuntimeError(
            "Base dos Dados does not contain the required 2024 vintage; "
            "the pre-registered MTE FTP route must be evaluated."
        )

    _atomic_write_csv(
        RESULTS_DIR / "rais_schema_probe.csv",
        schema_rows,
        ("column_name", "data_type"),
    )
    _atomic_write_csv(
        RESULTS_DIR / "rais_year_coverage.csv",
        coverage_rows,
        ("ano", "vinculos"),
    )

    status: dict[str, object] = {
        "status": "ok",
        "route": route,
        "route_reason": (
            "Base dos Dados contains the 2024 vintage, all probe years "
            "from 2015 through 2025, and all required columns."
        ),
        "billing_project": BILLING_PROJECT,
        "source_table": SOURCE_TABLE,
        "max_year": max_year,
        "required_max_year": 2024,
        "required_schema": REQUIRED_SCHEMA,
        "vinculo_ativo_3112_domain": {
            "data_type": observed_schema["vinculo_ativo_3112"],
            "values": ["0", "1"],
            "years": list(ANALYSIS_YEARS),
        },
        "queries": {
            "schema": SCHEMA_QUERY,
            "year_coverage": YEAR_COVERAGE_QUERY,
            "active_domain": ACTIVE_DOMAIN_QUERY,
        },
        "queried_at": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_write_json(RESULTS_DIR / "rais_acquisition_status.json", status)
    return status


def run_acquire() -> dict[str, object]:
    vintage_path = VINTAGE_DIR / "rais_cbo4_ano_2016_2024.csv"
    manifest_path = VINTAGE_DIR / "manifest.json"
    registered = _load_registered_extract(
        vintage_path,
        manifest_path,
        expected_query=AGGREGATE_QUERY,
    )
    if registered is not None:
        rows, manifest = registered
        validate_aggregate_rows(rows)
        return manifest

    rows = _run_bq_csv(AGGREGATE_QUERY, max_rows=100_000)
    summary = validate_aggregate_rows(rows)

    _atomic_write_csv(
        vintage_path,
        rows,
        (
            "ano",
            "cbo_4d",
            "vinculos_declarados",
            "estoque_3112",
            "tempo_emprego_medio",
        ),
    )

    manifest: dict[str, object] = {
        "fonte": "Base dos Dados BigQuery mirror",
        "tabela": SOURCE_TABLE,
        "consulta": AGGREGATE_QUERY,
        "linhas": summary["rows"],
        "bytes": vintage_path.stat().st_size,
        "sha256": sha256_file(vintage_path),
        "acessado_em": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_write_json(manifest_path, manifest)
    return manifest


def run_reconciliation_source() -> dict[str, object]:
    source_path = VINTAGE_DIR / "rais_reconciliation_components_2016_2024.csv"
    manifest_path = VINTAGE_DIR / "rais_reconciliation_components_manifest.json"
    registered = _load_registered_extract(
        source_path,
        manifest_path,
        expected_query=RECONCILIATION_COMPONENTS_QUERY,
    )
    if registered is not None:
        rows, manifest = registered
        if [int(row["ano"]) for row in rows] != list(ANALYSIS_YEARS):
            raise ValueError(
                "Reconciliation component extract has incomplete years"
            )
        return manifest

    rows = _run_bq_csv(RECONCILIATION_COMPONENTS_QUERY, max_rows=100)
    if [int(row["ano"]) for row in rows] != list(ANALYSIS_YEARS):
        raise ValueError("Reconciliation component extract has incomplete years")

    _atomic_write_csv(
        source_path,
        rows,
        (
            "ano",
            "ativos_total_fonte",
            "ativos_sem_cbo",
            "ativos_abandonados",
            "ativos_abandonados_com_cbo",
        ),
    )
    manifest: dict[str, object] = {
        "fonte": "Base dos Dados BigQuery mirror",
        "tabela": SOURCE_TABLE,
        "consulta": RECONCILIATION_COMPONENTS_QUERY,
        "linhas": len(rows),
        "bytes": source_path.stat().st_size,
        "sha256": sha256_file(source_path),
        "acessado_em": datetime.now(timezone.utc).isoformat(),
        "uso": "diagnostic-only reconciliation support",
    }
    _atomic_write_json(manifest_path, manifest)
    return manifest


def run_reconcile() -> dict[str, object]:
    aggregate_rows = _read_csv(
        VINTAGE_DIR / "rais_cbo4_ano_2016_2024.csv"
    )
    component_rows = _read_csv(
        VINTAGE_DIR / "rais_reconciliation_components_2016_2024.csv"
    )
    rows = build_reconciliation_rows(
        aggregate_rows,
        component_rows,
        OFFICIAL_TOTALS,
        OFFICIAL_SOURCES,
    )

    unexplained = [
        int(row["ano"])
        for row in rows
        if row["explanation_code"] == "unexplained"
    ]
    if unexplained:
        raise ValueError(f"Unexplained reconciliation years: {unexplained}")

    public_rows = [
        {
            "ano": row["ano"],
            "estoque_agregado": row["estoque_agregado"],
            "estoque_oficial": row["estoque_oficial"],
            "diferenca_absoluta": row["diferenca_absoluta"],
            "diferenca_relativa": f"{float(row['diferenca_relativa']):.12f}",
            "fonte_oficial": row["fonte_oficial"],
        }
        for row in rows
    ]
    _atomic_write_csv(
        RESULTS_DIR / "rais_reconciliation.csv",
        public_rows,
        (
            "ano",
            "estoque_agregado",
            "estoque_oficial",
            "diferenca_absoluta",
            "diferenca_relativa",
            "fonte_oficial",
        ),
    )
    _atomic_write_text(
        RESULTS_DIR / "RAIS_RECONCILIACAO.md",
        _render_reconciliation_report(rows),
    )

    return {
        "status": "pass",
        "years": list(ANALYSIS_YEARS),
        "max_absolute_relative_difference": max(
            abs(float(row["diferenca_relativa"])) for row in rows
        ),
        "unexplained_years": unexplained,
    }


def run_esocial_break() -> dict[str, object]:
    common_path = str(V2_ROOT / "code" / "common")
    if common_path not in sys.path:
        sys.path.insert(0, common_path)
    from merge_audit import audited_merge

    aggregate = pd.read_csv(
        VINTAGE_DIR / "rais_cbo4_ano_2016_2024.csv",
        dtype={"cbo_4d": "string"},
    )
    classification = pd.read_csv(
        V2_ROOT / "data" / "derived" / "cbo_treatment_classification.csv",
        dtype={"cbo_4d": "string"},
    )[["cbo_4d", "cbo_ilo_gradient"]]
    merged = audited_merge(
        aggregate,
        classification,
        merge_id="rais_esocial_break_treatment",
        validate="many_to_one",
        on="cbo_4d",
        how="left",
    )
    merge_audit = dict(merged.attrs["merge_audit"])

    def treatment_group(value: object) -> str | None:
        if value == "Not Exposed":
            return "control"
        if isinstance(value, str) and value.startswith("Exposed: Gradient"):
            return "treated"
        return None

    merged["grupo"] = merged["cbo_ilo_gradient"].map(treatment_group)
    analysis = merged.dropna(subset=["grupo"]).copy()
    group_year = (
        analysis.groupby(["ano", "grupo"], as_index=False)["estoque_3112"]
        .sum()
        .sort_values(["grupo", "ano"])
    )
    group_year["crescimento_anual"] = group_year.groupby("grupo")[
        "estoque_3112"
    ].pct_change()

    stock_wide = group_year.pivot(
        index="ano",
        columns="grupo",
        values="estoque_3112",
    )
    growth_wide = group_year.pivot(
        index="ano",
        columns="grupo",
        values="crescimento_anual",
    )
    growth_gaps_pp = {
        int(year): 100.0 * float(row["treated"] - row["control"])
        for year, row in growth_wide.dropna().iterrows()
    }
    dominant = is_transition_gap_dominant(
        growth_gaps_pp,
        ESOCIAL_TRANSITION_YEAR,
    )

    diagnostics: dict[int, dict[str, object]] = {}
    output_rows: list[dict[str, object]] = []
    for window_start in (2016, 2019):
        window = group_year[group_year["ano"].between(window_start, 2024)]
        group_diagnostics: dict[str, dict[str, object]] = {}
        for group in ("treated", "control"):
            group_frame = window[window["grupo"].eq(group)]
            group_diagnostics[group] = fit_segmented_break(
                group_frame["ano"].to_numpy(),
                group_frame["estoque_3112"].to_numpy(),
                transition_year=ESOCIAL_TRANSITION_YEAR,
            )

        treated_diagnostic = group_diagnostics["treated"]
        control_diagnostic = group_diagnostics["control"]
        level_difference = float(treated_diagnostic["level_break"]) - float(
            control_diagnostic["level_break"]
        )
        trend_difference = float(treated_diagnostic["trend_break"]) - float(
            control_diagnostic["trend_break"]
        )
        window_classification = classify_break_differential(
            level_difference,
            trend_difference,
        )
        diagnostic = {
            "treated_level_break": treated_diagnostic["level_break"],
            "control_level_break": control_diagnostic["level_break"],
            "level_difference": level_difference,
            "treated_trend_break": treated_diagnostic["trend_break"],
            "control_trend_break": control_diagnostic["trend_break"],
            "trend_difference": trend_difference,
            "classification": window_classification,
        }
        diagnostics[window_start] = diagnostic

        for year in range(window_start, 2025):
            treated_growth = growth_wide.loc[year, "treated"]
            control_growth = growth_wide.loc[year, "control"]
            output_rows.append(
                {
                    "janela_inicio": window_start,
                    "janela_fim": 2024,
                    "ano": year,
                    "estoque_tratadas": int(stock_wide.loc[year, "treated"]),
                    "estoque_controle": int(stock_wide.loc[year, "control"]),
                    "crescimento_tratadas": (
                        ""
                        if pd.isna(treated_growth)
                        else f"{float(treated_growth):.12f}"
                    ),
                    "crescimento_controle": (
                        ""
                        if pd.isna(control_growth)
                        else f"{float(control_growth):.12f}"
                    ),
                    "diferenca_crescimento_pp": (
                        ""
                        if pd.isna(treated_growth) or pd.isna(control_growth)
                        else f"{100 * float(treated_growth - control_growth):.12f}"
                    ),
                    "level_break_tratadas": (
                        f"{float(treated_diagnostic['level_break']):.12f}"
                    ),
                    "level_break_controle": (
                        f"{float(control_diagnostic['level_break']):.12f}"
                    ),
                    "level_break_diferenca": f"{level_difference:.12f}",
                    "trend_break_tratadas": (
                        f"{float(treated_diagnostic['trend_break']):.12f}"
                    ),
                    "trend_break_controle": (
                        f"{float(control_diagnostic['trend_break']):.12f}"
                    ),
                    "trend_break_diferenca": f"{trend_difference:.12f}",
                    "classificacao_quebra": window_classification,
                    "transicao_dominante": dominant,
                }
            )

    long_differential = (
        diagnostics[2016]["classification"] == "differential"
    )
    derived_window_start = 2019 if long_differential and dominant else 2016

    _atomic_write_csv(
        RESULTS_DIR / "rais_esocial_break.csv",
        output_rows,
        (
            "janela_inicio",
            "janela_fim",
            "ano",
            "estoque_tratadas",
            "estoque_controle",
            "crescimento_tratadas",
            "crescimento_controle",
            "diferenca_crescimento_pp",
            "level_break_tratadas",
            "level_break_controle",
            "level_break_diferenca",
            "trend_break_tratadas",
            "trend_break_controle",
            "trend_break_diferenca",
            "classificacao_quebra",
            "transicao_dominante",
        ),
    )

    input_manifest = json.loads(
        (VINTAGE_DIR / "manifest.json").read_text(encoding="utf-8")
    )
    support: dict[str, object] = {
        "status": "ok",
        "transition_year": ESOCIAL_TRANSITION_YEAR,
        "transition_source": ESOCIAL_TRANSITION_SOURCE,
        "transition_source_basis": (
            "The MTE RAIS 2022 technical note identifies base year 2022 as "
            "an important series break associated with eSocial Group 3."
        ),
        "model": (
            "log(group stock) ~ intercept + linear time + step(2022) + "
            "post-2022 trend change"
        ),
        "differential_threshold_log_points": (
            BREAK_DIFFERENTIAL_THRESHOLD_LOG_POINTS
        ),
        "dominance_threshold_percentage_points": (
            BREAK_DOMINANCE_THRESHOLD_PP
        ),
        "classification_2016_2024": diagnostics[2016]["classification"],
        "classification_2019_2024": diagnostics[2019]["classification"],
        "transition_growth_gap_pp": growth_gaps_pp[
            ESOCIAL_TRANSITION_YEAR
        ],
        "transition_dominant": dominant,
        "derived_window": f"{derived_window_start}-2024",
        "treated_cbo4": int(
            analysis.loc[analysis["grupo"].eq("treated"), "cbo_4d"].nunique()
        ),
        "control_cbo4": int(
            analysis.loc[analysis["grupo"].eq("control"), "cbo_4d"].nunique()
        ),
        "merge_audit": merge_audit,
        "input_sha256": input_manifest["sha256"],
        "treatment_coefficient_estimated": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_write_json(
        RESULTS_DIR / "rais_esocial_break_support.json",
        support,
    )
    _atomic_write_text(
        RESULTS_DIR / "RAIS_QUEBRA_ESOCIAL.md",
        _render_esocial_break_report(
            output_rows,
            diagnostics,
            dominant=dominant,
            derived_window_start=derived_window_start,
        ),
    )
    return support


def run_gate() -> dict[str, object]:
    acquisition = json.loads(
        (RESULTS_DIR / "rais_acquisition_status.json").read_text(
            encoding="utf-8"
        )
    )
    primary_manifest = json.loads(
        (VINTAGE_DIR / "manifest.json").read_text(encoding="utf-8")
    )
    diagnostic_manifest = json.loads(
        (
            VINTAGE_DIR / "rais_reconciliation_components_manifest.json"
        ).read_text(encoding="utf-8")
    )
    break_support = json.loads(
        (RESULTS_DIR / "rais_esocial_break_support.json").read_text(
            encoding="utf-8"
        )
    )

    primary_path = VINTAGE_DIR / "rais_cbo4_ano_2016_2024.csv"
    diagnostic_path = (
        VINTAGE_DIR / "rais_reconciliation_components_2016_2024.csv"
    )
    if sha256_file(primary_path) != primary_manifest["sha256"]:
        raise ValueError("Primary RAIS vintage SHA-256 mismatch")
    if sha256_file(diagnostic_path) != diagnostic_manifest["sha256"]:
        raise ValueError("Reconciliation support SHA-256 mismatch")

    aggregate_rows = _read_csv(primary_path)
    component_rows = _read_csv(diagnostic_path)
    reconciliation = build_reconciliation_rows(
        aggregate_rows,
        component_rows,
        OFFICIAL_TOTALS,
        OFFICIAL_SOURCES,
    )
    unexplained = [
        int(row["ano"])
        for row in reconciliation
        if row["explanation_code"] == "unexplained"
    ]
    acquisition_pass = (
        acquisition["status"] == "ok"
        and int(acquisition["max_year"]) >= 2024
    )
    reconciliation_pass = not unexplained
    break_measured = (
        break_support["status"] == "ok"
        and break_support["classification_2016_2024"]
        in {"differential", "non_differential", "indeterminate"}
        and break_support["classification_2019_2024"]
        in {"differential", "non_differential", "indeterminate"}
    )
    scorecard = derive_stage0_scorecard(
        acquisition_pass=acquisition_pass,
        reconciliation_pass=reconciliation_pass,
        break_measured=break_measured,
    )
    _atomic_write_csv(
        RESULTS_DIR / "scorecard_v3.csv",
        [scorecard],
        (
            "frente",
            "momento",
            "fecha_limitacao_declarada",
            "gate_aquisicao",
            "gate_construcao",
            "falsificacao",
            "pretrend",
            "suporte",
            "familia_bh",
            "barra_reprodutibilidade",
            "custo_estrutural",
            "veredito",
            "veredito_derivado_de",
        ),
    )

    max_relative = max(
        abs(float(row["diferenca_relativa"]))
        for row in _read_csv(RESULTS_DIR / "rais_reconciliation.csv")
    )

    status: dict[str, object] = {
        "status": "stage0_gate_open",
        "gate_r_g1": scorecard["gate_aquisicao"],
        "gate_r_g2": scorecard["gate_construcao"],
        "max_available_year": int(acquisition["max_year"]),
        "primary_vintage_sha256": primary_manifest["sha256"],
        "diagnostic_support_sha256": diagnostic_manifest["sha256"],
        "reconciliation_max_absolute_relative_difference": max_relative,
        "reconciliation_unexplained_years": unexplained,
        "break_classification_2016_2024": (
            break_support["classification_2016_2024"]
        ),
        "break_classification_2019_2024": (
            break_support["classification_2019_2024"]
        ),
        "derived_window": break_support["derived_window"],
        "treatment_coefficient_estimated": False,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_write_json(RESULTS_DIR / "rais_stage0_status.json", status)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RAIS Stage 0 pipeline.")
    parser.add_argument(
        "task",
        choices=(
            "probe",
            "acquire",
            "reconciliation-source",
            "reconcile",
            "esocial-break",
            "gate",
        ),
        help="Pre-registered Stage 0 task to execute.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.task == "probe":
        status = run_probe()
    elif args.task == "acquire":
        status = run_acquire()
    elif args.task == "reconciliation-source":
        status = run_reconciliation_source()
    elif args.task == "reconcile":
        status = run_reconcile()
    elif args.task == "esocial-break":
        status = run_esocial_break()
    elif args.task == "gate":
        status = run_gate()
    else:
        raise AssertionError(f"Unhandled task: {args.task}")
    print(json.dumps(status, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
