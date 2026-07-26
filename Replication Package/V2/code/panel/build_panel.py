#!/usr/bin/env python3
"""Build the signed national CBO4-by-month analytic panel."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import sys
import tempfile
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import requests
import xlrd

COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from merge_audit import audited_merge


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MOVEMENTS_GLOB = (
    PACKAGE_ROOT
    / "data"
    / "interim"
    / "movimentacoes"
    / "competenciamov=*"
    / "part.parquet"
)
DEFAULT_CLASSIFICATION = (
    PACKAGE_ROOT / "data" / "derived" / "cbo_treatment_classification.csv"
)
DEFAULT_IPCA_RAW = (
    PACKAGE_ROOT
    / "data"
    / "vintage"
    / "ipca"
    / "sgs_433_202101_202605.json"
)
DEFAULT_IPCA = PACKAGE_ROOT / "data" / "derived" / "ipca_mensal.parquet"
DEFAULT_MANIFEST = PACKAGE_ROOT / "data" / "vintage" / "manifest.json"
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "painel_nacional_support.json"
)
DEFAULT_CNAE_RAW = (
    PACKAGE_ROOT
    / "data"
    / "vintage"
    / "cnae"
    / "cnae2.0_subclasses.zip"
)
DEFAULT_CNAE_DICTIONARY = (
    PACKAGE_ROOT
    / "data"
    / "vintage"
    / "cnae"
    / "cnae_divisions.csv"
)
DEFAULT_SECTOR_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_cbo_cnae.parquet"
)
DEFAULT_CNAE_MONTH_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "cnae_month_treatment_support.csv"
)
DEFAULT_SECTOR_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "painel_cbo_cnae_support.json"
)
DEFAULT_SCRATCH_PARENT = PACKAGE_ROOT / "data" / "interim"

IPCA_SERIES = 433
IPCA_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    "?formato=json&dataInicial=01/01/2021&dataFinal=31/05/2026"
)
START_PERIOD = 202101
END_PERIOD = 202605
IPCA_BASE_PERIOD = "202412"
CNAE_URL = (
    "https://ftp.ibge.gov.br/Informacoes_Gerais_e_Referencia/"
    "Classificacoes/CNAE/cnae2.0_subclasses.zip"
)
WAGE_MIN = 0.0
WAGE_MAX = 1_000_000.0

COMPOSITION_BASES = (
    "idade_media",
    "pct_mulher",
    "pct_superior",
    "pct_negra",
)
COMPLETE_HIGHER_EDUCATION_CODES = frozenset({"9", "10", "11", "80"})
COMPLETE_HIGHER_EDUCATION_SQL = ", ".join(
    f"'{code}'" for code in sorted(COMPLETE_HIGHER_EDUCATION_CODES)
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_manifest(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Vintage manifest must be a JSON object")
    return payload


def _write_manifest(
    manifest: dict[str, dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def build_ipca_frame(
    payload: bytes,
    *,
    expected_start: str = str(START_PERIOD),
    expected_end: str = str(END_PERIOD),
    base_period: str = IPCA_BASE_PERIOD,
) -> pd.DataFrame:
    records = json.loads(payload.decode("utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("BCB SGS response must be a non-empty JSON list")
    frame = pd.DataFrame(records)
    required = {"data", "valor"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"BCB SGS response is missing fields: {missing}")
    frame["date"] = pd.to_datetime(
        frame["data"], format="%d/%m/%Y", errors="raise"
    )
    frame["variacao_mensal"] = pd.to_numeric(
        frame["valor"], errors="raise"
    )
    frame["periodo_num"] = (
        frame["date"].dt.year * 100 + frame["date"].dt.month
    ).astype(int)
    frame = frame.sort_values("periodo_num").reset_index(drop=True)
    expected = pd.period_range(
        pd.Period(expected_start, freq="M"),
        pd.Period(expected_end, freq="M"),
        freq="M",
    ).strftime("%Y%m")
    observed = frame["periodo_num"].astype(str).tolist()
    if observed != expected.tolist():
        raise RuntimeError(
            "IPCA monthly coverage mismatch: "
            f"expected {expected_start}..{expected_end}, "
            f"found {observed[0]}..{observed[-1]} with "
            f"{len(observed)} rows"
        )
    cumulative = (1.0 + frame["variacao_mensal"] / 100.0).cumprod()
    base_matches = frame["periodo_num"].eq(int(base_period))
    if int(base_matches.sum()) != 1:
        raise RuntimeError(f"IPCA base period is unavailable: {base_period}")
    base_value = float(cumulative.loc[base_matches].iloc[0])
    frame["indice"] = cumulative / base_value * 100.0
    frame["ano"] = frame["date"].dt.year.astype(int)
    frame["mes"] = frame["date"].dt.month.astype(int)
    frame["periodo"] = frame["date"].dt.strftime("%Y-%m")
    return frame[
        [
            "ano",
            "mes",
            "periodo",
            "periodo_num",
            "variacao_mensal",
            "indice",
        ]
    ]


def _fetch_url(url: str) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def freeze_ipca(
    raw_path: Path = DEFAULT_IPCA_RAW,
    derived_path: Path = DEFAULT_IPCA,
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    fetch: Callable[[str], bytes] = _fetch_url,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    payload = fetch(IPCA_URL)
    frame = build_ipca_frame(payload)
    frozen_at = utc_iso(now())
    _atomic_bytes(raw_path, payload)
    derived_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = derived_path.with_suffix(f"{derived_path.suffix}.tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, derived_path)

    manifest = _read_manifest(manifest_path)
    manifest[f"ipca/{raw_path.name}"] = {
        "accessed_at": frozen_at,
        "bytes": raw_path.stat().st_size,
        "series": IPCA_SERIES,
        "sha256": sha256_file(raw_path),
        "url": IPCA_URL,
    }
    manifest["derived/ipca_mensal.parquet"] = {
        "base_period": IPCA_BASE_PERIOD,
        "bytes": derived_path.stat().st_size,
        "generated_at": frozen_at,
        "sha256": sha256_file(derived_path),
        "source": f"ipca/{raw_path.name}",
    }
    _write_manifest(manifest, manifest_path)
    return {
        "rows": int(len(frame)),
        "start_period": int(frame["periodo_num"].min()),
        "end_period": int(frame["periodo_num"].max()),
        "base_period": int(IPCA_BASE_PERIOD),
        "raw_sha256": sha256_file(raw_path),
        "derived_sha256": sha256_file(derived_path),
    }


def _normalize_division(value: Any) -> str:
    if isinstance(value, (int, float)) and not pd.isna(value):
        number = int(value)
        if float(value) == number and 1 <= number <= 99:
            return f"{number:02d}"
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(2) if text.isdigit() and len(text) <= 2 else ""


def build_cnae_divisions(payload: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        workbook_bytes = archive.read("estrutura.xls")
    workbook = xlrd.open_workbook(
        file_contents=workbook_bytes,
        on_demand=True,
        formatting_info=False,
    )
    sheet = workbook.sheet_by_index(0)
    current_section = ""
    current_section_title = ""
    records: list[dict[str, str]] = []
    for row_index in range(sheet.nrows):
        values = [
            str(sheet.cell_value(row_index, column)).strip()
            for column in range(sheet.ncols)
        ]
        section_candidate = values[1]
        if (
            len(section_candidate) == 1
            and "A" <= section_candidate <= "U"
        ):
            current_section = section_candidate
            current_section_title = values[6]
        division = _normalize_division(
            sheet.cell_value(row_index, 2)
        )
        if division:
            if not current_section:
                raise RuntimeError(
                    f"CNAE division {division} has no section context"
                )
            records.append(
                {
                    "divisao": division,
                    "secao": current_section,
                    "divisao_descricao": values[6],
                    "secao_descricao": current_section_title,
                }
            )
    workbook.release_resources()
    divisions = (
        pd.DataFrame(records)
        .drop_duplicates("divisao")
        .sort_values("divisao")
        .reset_index(drop=True)
    )
    if (
        len(divisions) != 87
        or divisions["divisao"].nunique() != 87
        or divisions["secao"].nunique() != 21
    ):
        raise RuntimeError(
            "Official CNAE structure must contain 87 divisions in "
            "21 sections"
        )
    return divisions


def freeze_cnae(
    raw_path: Path = DEFAULT_CNAE_RAW,
    dictionary_path: Path = DEFAULT_CNAE_DICTIONARY,
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    fetch: Callable[[str], bytes] = _fetch_url,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    payload = fetch(CNAE_URL)
    divisions = build_cnae_divisions(payload)
    frozen_at = utc_iso(now())
    _atomic_bytes(raw_path, payload)
    dictionary_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = dictionary_path.with_suffix(
        f"{dictionary_path.suffix}.tmp"
    )
    divisions.to_csv(temporary, index=False)
    os.replace(temporary, dictionary_path)

    manifest = _read_manifest(manifest_path)
    manifest[f"cnae/{raw_path.name}"] = {
        "accessed_at": frozen_at,
        "bytes": raw_path.stat().st_size,
        "sha256": sha256_file(raw_path),
        "url": CNAE_URL,
    }
    manifest[f"cnae/{dictionary_path.name}"] = {
        "bytes": dictionary_path.stat().st_size,
        "generated_at": frozen_at,
        "sha256": sha256_file(dictionary_path),
        "source": f"cnae/{raw_path.name}",
    }
    _write_manifest(manifest, manifest_path)
    return {
        "sections": int(divisions["secao"].nunique()),
        "divisions": int(divisions["divisao"].nunique()),
        "raw_sha256": sha256_file(raw_path),
        "dictionary_sha256": sha256_file(dictionary_path),
    }


def load_cnae_divisions(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        dtype={
            "divisao": str,
            "secao": str,
            "divisao_descricao": str,
            "secao_descricao": str,
        },
    )
    frame["divisao"] = frame["divisao"].str.zfill(2)
    if (
        len(frame) != 87
        or frame["divisao"].nunique() != 87
        or frame["secao"].nunique() != 21
    ):
        raise RuntimeError(
            "Frozen CNAE dictionary must contain 87 divisions in "
            "21 sections"
        )
    return frame


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _configure_connection(
    connection: duckdb.DuckDBPyConnection,
    temp_directory: Path,
) -> None:
    connection.execute("SET threads = 1")
    connection.execute("SET memory_limit = '768MB'")
    connection.execute("SET preserve_insertion_order = false")
    connection.execute(
        f"SET temp_directory = {_sql_literal(temp_directory)}"
    )


def _create_movement_views(
    connection: duckdb.DuckDBPyConnection,
    movements_glob: Path,
    start_period: int,
    end_period: int,
) -> None:
    source = _sql_literal(movements_glob)
    connection.execute(
        f"""
        CREATE TEMP VIEW analytic_source AS
        SELECT
            CAST(competenciamov AS INTEGER) AS periodo_num,
            CAST(cbo2002ocupacao AS VARCHAR) AS cbo2002ocupacao,
            CAST(saldomovimentacao AS SMALLINT) AS movimento,
            CAST(peso AS BIGINT) AS peso,
            CAST(salario AS DOUBLE) AS salario,
            CAST(idade AS DOUBLE) AS idade,
            CAST(sexo AS VARCHAR) AS sexo,
            CAST(graudeinstrucao AS VARCHAR) AS graudeinstrucao,
            CAST(racacor AS VARCHAR) AS racacor
            ,CAST(secao AS VARCHAR) AS secao_raw
            ,lpad(CAST(subclasse AS VARCHAR), 7, '0') AS subclasse
        FROM read_parquet(
            {source},
            hive_partitioning = true,
            union_by_name = true
        )
        WHERE CAST(competenciamov AS INTEGER)
              BETWEEN {int(start_period)} AND {int(end_period)}
        """
    )
    connection.execute(
        f"""
        CREATE TEMP VIEW valid_movements AS
        SELECT
            substring(cbo2002ocupacao, 1, 4) AS cbo_4d,
            periodo_num,
            CAST(floor(periodo_num / 100) AS INTEGER) AS ano,
            movimento,
            peso,
            salario,
            idade,
            sexo,
            graudeinstrucao,
            racacor,
            secao_raw,
            subclasse
        FROM analytic_source
        WHERE regexp_full_match(cbo2002ocupacao, '[0-9]{{4,6}}')
          AND substring(cbo2002ocupacao, 1, 4) <> '0000'
          AND idade BETWEEN 14 AND 90
          AND salario > {WAGE_MIN}
          AND salario < {WAGE_MAX}
          AND movimento IN (-1, 1)
          AND peso IN (-1, 1)
        """
    )


def _aggregate_national(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    connection.execute(
        """
        CREATE TEMP TABLE wage_bounds AS
        SELECT
            cbo_4d,
            ano,
            approx_quantile(salario, 0.01) AS wage_p01,
            approx_quantile(salario, 0.99) AS wage_p99
        FROM valid_movements
        WHERE peso = 1
        GROUP BY cbo_4d, ano
        """
    )
    return connection.execute(
        f"""
        WITH winsorized AS (
            SELECT
                movement.*,
                greatest(
                    bounds.wage_p01,
                    least(movement.salario, bounds.wage_p99)
                ) AS salario_winsor
            FROM valid_movements AS movement
            INNER JOIN wage_bounds AS bounds
              USING (cbo_4d, ano)
        ),
        totals AS (
            SELECT
                cbo_4d,
                periodo_num,
                CAST(sum(
                    CASE WHEN movimento = 1 THEN peso ELSE 0 END
                ) AS BIGINT) AS admissoes,
                CAST(sum(
                    CASE WHEN movimento = -1 THEN peso ELSE 0 END
                ) AS BIGINT) AS desligamentos,
                sum(CASE
                    WHEN movimento = 1
                    THEN peso * salario_winsor
                    ELSE 0
                END) AS salario_soma_adm,
                sum(CASE
                    WHEN movimento = -1
                    THEN peso * salario_winsor
                    ELSE 0
                END) AS salario_soma_desl,
                sum(CASE
                    WHEN movimento = 1 THEN peso * idade ELSE 0
                END) AS idade_soma_adm,
                sum(CASE
                    WHEN movimento = -1 THEN peso * idade ELSE 0
                END) AS idade_soma_desl,
                sum(CASE
                    WHEN movimento = 1 AND sexo = '3' THEN peso
                    ELSE 0
                END) AS mulher_soma_adm,
                sum(CASE
                    WHEN movimento = -1 AND sexo = '3' THEN peso
                    ELSE 0
                END) AS mulher_soma_desl,
                sum(CASE
                    WHEN movimento = 1
                     AND graudeinstrucao IN ({COMPLETE_HIGHER_EDUCATION_SQL})
                    THEN peso ELSE 0
                END) AS superior_soma_adm,
                sum(CASE
                    WHEN movimento = -1
                     AND graudeinstrucao IN ({COMPLETE_HIGHER_EDUCATION_SQL})
                    THEN peso ELSE 0
                END) AS superior_soma_desl,
                sum(CASE
                    WHEN movimento = 1 AND racacor IN ('2', '3')
                    THEN peso ELSE 0
                END) AS negra_soma_adm,
                sum(CASE
                    WHEN movimento = -1 AND racacor IN ('2', '3')
                    THEN peso ELSE 0
                END) AS negra_soma_desl
            FROM winsorized
            GROUP BY cbo_4d, periodo_num
        )
        SELECT
            cbo_4d,
            CAST(floor(periodo_num / 100) AS INTEGER) AS ano,
            CAST(periodo_num % 100 AS INTEGER) AS mes,
            periodo_num,
            admissoes,
            desligamentos,
            admissoes - desligamentos AS saldo,
            admissoes + desligamentos AS n_movimentacoes,
            CASE WHEN admissoes > 0
                 THEN salario_soma_adm / admissoes END
                AS salario_medio_adm,
            CASE WHEN desligamentos > 0
                 THEN salario_soma_desl / desligamentos END
                AS salario_medio_desl,
            CASE WHEN admissoes > 0
                 THEN idade_soma_adm / admissoes END
                AS idade_media_adm,
            CASE WHEN desligamentos > 0
                 THEN idade_soma_desl / desligamentos END
                AS idade_media_desl,
            CASE WHEN admissoes > 0
                 THEN mulher_soma_adm / admissoes END
                AS pct_mulher_adm,
            CASE WHEN desligamentos > 0
                 THEN mulher_soma_desl / desligamentos END
                AS pct_mulher_desl,
            CASE WHEN admissoes > 0
                 THEN superior_soma_adm / admissoes END
                AS pct_superior_adm,
            CASE WHEN desligamentos > 0
                 THEN superior_soma_desl / desligamentos END
                AS pct_superior_desl,
            CASE WHEN admissoes > 0
                 THEN negra_soma_adm / admissoes END
                AS pct_negra_adm,
            CASE WHEN desligamentos > 0
                 THEN negra_soma_desl / desligamentos END
                AS pct_negra_desl
        FROM totals
        WHERE admissoes >= 0
          AND desligamentos >= 0
          AND (admissoes > 0 OR desligamentos > 0)
        ORDER BY cbo_4d, periodo_num
        """
    ).df()


def _sector_output_sql() -> str:
    return f"""
        WITH winsorized AS (
            SELECT
                movement.*,
                greatest(
                    bounds.wage_p01,
                    least(movement.salario, bounds.wage_p99)
                ) AS salario_winsor
            FROM sector_movements AS movement
            INNER JOIN wage_bounds AS bounds
              USING (cbo_4d, ano)
        ),
        totals AS (
            SELECT
                cbo_4d,
                subclasse,
                secao,
                divisao,
                cnae_status,
                periodo_num,
                CAST(sum(
                    CASE WHEN movimento = 1 THEN peso ELSE 0 END
                ) AS BIGINT) AS admissoes,
                CAST(sum(
                    CASE WHEN movimento = -1 THEN peso ELSE 0 END
                ) AS BIGINT) AS desligamentos,
                sum(CASE
                    WHEN movimento = 1
                    THEN peso * salario_winsor ELSE 0
                END) AS salario_soma_adm,
                sum(CASE
                    WHEN movimento = -1
                    THEN peso * salario_winsor ELSE 0
                END) AS salario_soma_desl,
                sum(CASE
                    WHEN movimento = 1 THEN peso * idade ELSE 0
                END) AS idade_soma_adm,
                sum(CASE
                    WHEN movimento = -1 THEN peso * idade ELSE 0
                END) AS idade_soma_desl,
                sum(CASE
                    WHEN movimento = 1 AND sexo = '3' THEN peso
                    ELSE 0
                END) AS mulher_soma_adm,
                sum(CASE
                    WHEN movimento = -1 AND sexo = '3' THEN peso
                    ELSE 0
                END) AS mulher_soma_desl,
                sum(CASE
                    WHEN movimento = 1
                     AND graudeinstrucao IN ({COMPLETE_HIGHER_EDUCATION_SQL})
                    THEN peso ELSE 0
                END) AS superior_soma_adm,
                sum(CASE
                    WHEN movimento = -1
                     AND graudeinstrucao IN ({COMPLETE_HIGHER_EDUCATION_SQL})
                    THEN peso ELSE 0
                END) AS superior_soma_desl,
                sum(CASE
                    WHEN movimento = 1 AND racacor IN ('2', '3')
                    THEN peso ELSE 0
                END) AS negra_soma_adm,
                sum(CASE
                    WHEN movimento = -1 AND racacor IN ('2', '3')
                    THEN peso ELSE 0
                END) AS negra_soma_desl
            FROM winsorized
            GROUP BY
                cbo_4d,
                subclasse,
                secao,
                divisao,
                cnae_status,
                periodo_num
        ),
        cells AS (
            SELECT
                cbo_4d,
                subclasse,
                secao,
                divisao,
                cnae_status,
                CAST(floor(periodo_num / 100) AS INTEGER) AS ano,
                CAST(periodo_num % 100 AS INTEGER) AS mes,
                periodo_num,
                admissoes,
                desligamentos,
                admissoes - desligamentos AS saldo,
                admissoes + desligamentos AS n_movimentacoes,
                CASE WHEN admissoes > 0
                     THEN salario_soma_adm / admissoes END
                    AS salario_medio_adm,
                CASE WHEN desligamentos > 0
                     THEN salario_soma_desl / desligamentos END
                    AS salario_medio_desl,
                CASE WHEN admissoes > 0
                     THEN idade_soma_adm / admissoes END
                    AS idade_media_adm,
                CASE WHEN desligamentos > 0
                     THEN idade_soma_desl / desligamentos END
                    AS idade_media_desl,
                CASE WHEN admissoes > 0
                     THEN mulher_soma_adm / admissoes END
                    AS pct_mulher_adm,
                CASE WHEN desligamentos > 0
                     THEN mulher_soma_desl / desligamentos END
                    AS pct_mulher_desl,
                CASE WHEN admissoes > 0
                     THEN superior_soma_adm / admissoes END
                    AS pct_superior_adm,
                CASE WHEN desligamentos > 0
                     THEN superior_soma_desl / desligamentos END
                    AS pct_superior_desl,
                CASE WHEN admissoes > 0
                     THEN negra_soma_adm / admissoes END
                    AS pct_negra_adm,
                CASE WHEN desligamentos > 0
                     THEN negra_soma_desl / desligamentos END
                    AS pct_negra_desl
            FROM totals
            WHERE admissoes >= 0
              AND desligamentos >= 0
              AND (admissoes > 0 OR desligamentos > 0)
        )
        SELECT
            cells.*,
            ipca.indice,
            coalesce(
                classification.cbo_ilo_gradient,
                'No score'
            ) AS cbo_ilo_gradient,
            CASE
                WHEN classification.cbo_ilo_gradient IN (
                    'Exposed: Gradient 1',
                    'Exposed: Gradient 2',
                    'Exposed: Gradient 3',
                    'Exposed: Gradient 4'
                ) THEN 1.0
                WHEN classification.cbo_ilo_gradient = 'Not Exposed'
                THEN 0.0
                ELSE NULL
            END AS treated_main,
            coalesce(
                classification.cbo_ilo_gradient IN (
                    'Exposed: Gradient 1',
                    'Exposed: Gradient 2',
                    'Exposed: Gradient 3',
                    'Exposed: Gradient 4',
                    'Not Exposed'
                ),
                false
            ) AS included_main,
            printf('%04d-%02d', cells.ano, cells.mes) AS periodo,
            CAST(cells.periodo_num >= 202212 AS TINYINT) AS post,
            cells.salario_medio_adm * 100.0 / ipca.indice
                AS salario_real_adm,
            cells.salario_medio_desl * 100.0 / ipca.indice
                AS salario_real_desl,
            ln(1 + cells.admissoes) AS ln_admissoes,
            ln(1 + cells.desligamentos) AS ln_desligamentos,
            ln(cells.salario_medio_adm * 100.0 / ipca.indice)
                AS ln_salario_real_adm,
            ln(cells.salario_medio_desl * 100.0 / ipca.indice)
                AS ln_salario_real_desl,
            asinh(cells.saldo) AS asinh_saldo
        FROM cells
        INNER JOIN ipca_table AS ipca
          USING (periodo_num)
        LEFT JOIN classification_table AS classification
          USING (cbo_4d)
    """


def build_sector_panel(
    movements_glob: Path,
    ipca: pd.DataFrame,
    classification: pd.DataFrame,
    cnae_divisions: pd.DataFrame,
    national_panel_path: Path,
    sector_panel_path: Path,
    coexistence_path: Path,
    *,
    start_period: int = START_PERIOD,
    end_period: int = END_PERIOD,
    scratch_parent: Path = DEFAULT_SCRATCH_PARENT,
) -> dict[str, Any]:
    scratch_parent.mkdir(parents=True, exist_ok=True)
    sector_panel_path.parent.mkdir(parents=True, exist_ok=True)
    coexistence_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_panel = sector_panel_path.with_suffix(
        f"{sector_panel_path.suffix}.tmp"
    )
    with tempfile.TemporaryDirectory(
        prefix="t13-duckdb-",
        dir=scratch_parent,
    ) as temporary:
        connection = duckdb.connect()
        try:
            _configure_connection(connection, Path(temporary))
            _create_movement_views(
                connection,
                movements_glob,
                start_period,
                end_period,
            )
            divisions = cnae_divisions[
                ["divisao", "secao"]
            ].copy()
            divisions["divisao"] = (
                divisions["divisao"].astype(str).str.zfill(2)
            )
            connection.register("cnae_input", divisions)
            connection.execute(
                """
                CREATE TEMP TABLE cnae_divisions AS
                SELECT
                    CAST(divisao AS VARCHAR) AS divisao,
                    CAST(secao AS VARCHAR) AS secao
                FROM cnae_input
                """
            )
            connection.execute(
                """
                CREATE TEMP VIEW sector_joined AS
                SELECT
                    movement.*,
                    CASE
                        WHEN movement.secao_raw = 'Z'
                         AND movement.subclasse = '9999999'
                        THEN 'Z'
                        ELSE dictionary.secao
                    END AS secao,
                    CASE
                        WHEN movement.secao_raw = 'Z'
                         AND movement.subclasse = '9999999'
                        THEN 'ZZ'
                        ELSE dictionary.divisao
                    END AS divisao,
                    CASE
                        WHEN movement.secao_raw = 'Z'
                         AND movement.subclasse = '9999999'
                        THEN 'undocumented_preserved'
                        ELSE 'official'
                    END AS cnae_status,
                    dictionary.secao AS dictionary_section
                FROM valid_movements AS movement
                LEFT JOIN cnae_divisions AS dictionary
                  ON substring(movement.subclasse, 1, 2)
                   = dictionary.divisao
                """
            )
            invalid_industry = int(
                connection.execute(
                    """
                    SELECT count(*)
                    FROM sector_joined
                    WHERE cnae_status = 'official'
                      AND (
                          dictionary_section IS NULL
                          OR dictionary_section <> secao_raw
                      )
                    """
                ).fetchone()[0]
            )
            if invalid_industry:
                raise RuntimeError(
                    "Valid national rows fail CNAE division-section "
                    f"validation: {invalid_industry}"
                )
            connection.execute(
                """
                CREATE TEMP VIEW sector_movements AS
                SELECT * EXCLUDE (dictionary_section)
                FROM sector_joined
                """
            )
            connection.execute(
                """
                CREATE TEMP TABLE wage_bounds AS
                SELECT
                    cbo_4d,
                    ano,
                    approx_quantile(salario, 0.01) AS wage_p01,
                    approx_quantile(salario, 0.99) AS wage_p99
                FROM valid_movements
                WHERE peso = 1
                GROUP BY cbo_4d, ano
                """
            )
            ipca_input = ipca[["periodo_num", "indice"]].copy()
            classes = classification[
                ["cbo_4d", "cbo_ilo_gradient"]
            ].copy()
            classes["cbo_4d"] = (
                classes["cbo_4d"].astype(str).str.zfill(4)
            )
            connection.register("ipca_input", ipca_input)
            connection.register("classification_input", classes)
            connection.execute(
                """
                CREATE TEMP TABLE ipca_table AS
                SELECT
                    CAST(periodo_num AS INTEGER) AS periodo_num,
                    CAST(indice AS DOUBLE) AS indice
                FROM ipca_input
                """
            )
            connection.execute(
                """
                CREATE TEMP TABLE classification_table AS
                SELECT
                    CAST(cbo_4d AS VARCHAR) AS cbo_4d,
                    CAST(cbo_ilo_gradient AS VARCHAR)
                        AS cbo_ilo_gradient
                FROM classification_input
                """
            )
            connection.execute(
                f"""
                COPY ({_sector_output_sql()})
                TO {_sql_literal(temporary_panel)}
                (FORMAT PARQUET, COMPRESSION ZSTD)
                """
            )
            os.replace(temporary_panel, sector_panel_path)
            sector_source = _sql_literal(sector_panel_path)
            national_source = _sql_literal(national_panel_path)

            validation = connection.execute(
                f"""
                SELECT
                    count(*) AS cells,
                    count(*) - count(DISTINCT (
                        cbo_4d, subclasse, periodo_num
                    )) AS duplicate_cells,
                    count(*) FILTER (
                        WHERE admissoes = 0 AND (
                            salario_medio_adm IS NOT NULL
                            OR idade_media_adm IS NOT NULL
                            OR pct_mulher_adm IS NOT NULL
                            OR pct_superior_adm IS NOT NULL
                            OR pct_negra_adm IS NOT NULL
                        )
                    ) AS bad_admission_missingness,
                    count(*) FILTER (
                        WHERE desligamentos = 0 AND (
                            salario_medio_desl IS NOT NULL
                            OR idade_media_desl IS NOT NULL
                            OR pct_mulher_desl IS NOT NULL
                            OR pct_superior_desl IS NOT NULL
                            OR pct_negra_desl IS NOT NULL
                        )
                    ) AS bad_separation_missingness,
                    max(salario_medio_adm) AS max_admission_wage,
                    max(salario_medio_desl) AS max_separation_wage,
                    quantile_cont(n_movimentacoes, 0.10)
                        AS cell_size_p10,
                    count(DISTINCT secao) AS sections,
                    count(DISTINCT divisao) AS divisions
                FROM read_parquet({sector_source})
                """
            ).fetchone()
            divergences = int(
                connection.execute(
                    f"""
                    WITH sector AS (
                        SELECT
                            cbo_4d,
                            periodo_num,
                            sum(admissoes) AS admissoes,
                            sum(desligamentos) AS desligamentos
                        FROM read_parquet({sector_source})
                        GROUP BY cbo_4d, periodo_num
                    ),
                    comparison AS (
                        SELECT
                            coalesce(s.cbo_4d, n.cbo_4d) AS cbo_4d,
                            coalesce(
                                s.periodo_num, n.periodo_num
                            ) AS periodo_num,
                            s.admissoes AS sector_admissions,
                            n.admissoes AS national_admissions,
                            s.desligamentos AS sector_separations,
                            n.desligamentos AS national_separations
                        FROM sector AS s
                        FULL OUTER JOIN read_parquet(
                            {national_source}
                        ) AS n
                          USING (cbo_4d, periodo_num)
                    )
                    SELECT count(*)
                    FROM comparison
                    WHERE sector_admissions IS DISTINCT FROM
                          national_admissions
                       OR sector_separations IS DISTINCT FROM
                          national_separations
                    """
                ).fetchone()[0]
            )
            coexistence_temporary = coexistence_path.with_suffix(
                f"{coexistence_path.suffix}.tmp"
            )
            connection.execute(
                f"""
                COPY (
                    SELECT
                        subclasse,
                        secao,
                        divisao,
                        periodo_num,
                        count(DISTINCT cbo_4d) FILTER (
                            WHERE treated_main = 1
                        ) AS treated_cbo_families,
                        count(DISTINCT cbo_4d) FILTER (
                            WHERE treated_main = 0
                        ) AS control_cbo_families,
                        treated_cbo_families > 0
                          AND control_cbo_families > 0
                          AS has_treated_control_coexistence
                    FROM read_parquet({sector_source})
                    GROUP BY
                        subclasse, secao, divisao, periodo_num
                    ORDER BY subclasse, periodo_num
                )
                TO {_sql_literal(coexistence_temporary)}
                (FORMAT CSV, HEADER)
                """
            )
            os.replace(coexistence_temporary, coexistence_path)
            coexistence = connection.execute(
                f"""
                SELECT
                    count(*) AS cnae_month_cells,
                    count(*) FILTER (
                        WHERE has_treated_control_coexistence
                    ) AS coexisting_cells
                FROM read_csv_auto(
                    {_sql_literal(coexistence_path)},
                    header = true
                )
                """
            ).fetchone()
            undocumented = connection.execute(
                """
                SELECT count(*), coalesce(sum(peso), 0)
                FROM sector_movements
                WHERE cnae_status = 'undocumented_preserved'
                """
            ).fetchone()
        finally:
            connection.close()

    metrics = {
        "cells": int(validation[0]),
        "sector_panel_bytes": sector_panel_path.stat().st_size,
        "sector_panel_sha256": sha256_file(sector_panel_path),
        "coexistence_bytes": coexistence_path.stat().st_size,
        "coexistence_sha256": sha256_file(coexistence_path),
        "duplicate_cells": int(validation[1]),
        "bad_admission_missingness": int(validation[2]),
        "bad_separation_missingness": int(validation[3]),
        "max_admission_wage": float(validation[4]),
        "max_separation_wage": float(validation[5]),
        "cell_size_p10": float(validation[6]),
        "sections": int(validation[7]),
        "divisions_including_undocumented": int(validation[8]),
        "official_divisions": int(cnae_divisions["divisao"].nunique()),
        "national_count_divergences": divergences,
        "cnae_month_cells": int(coexistence[0]),
        "coexisting_treated_control_cells": int(coexistence[1]),
        "coexisting_treated_control_share": (
            float(coexistence[1] / coexistence[0])
            if coexistence[0]
            else math.nan
        ),
        "undocumented_cnae_rows": int(undocumented[0]),
        "undocumented_cnae_signed_weight": int(undocumented[1]),
    }
    blocking = {
        "duplicate_cells": metrics["duplicate_cells"],
        "bad_admission_missingness": metrics[
            "bad_admission_missingness"
        ],
        "bad_separation_missingness": metrics[
            "bad_separation_missingness"
        ],
        "national_count_divergences": metrics[
            "national_count_divergences"
        ],
    }
    if any(blocking.values()):
        raise RuntimeError(f"Sector-panel validation failed: {blocking}")
    return metrics


def _attach_panel_fields(
    panel: pd.DataFrame,
    ipca: pd.DataFrame,
    classification: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    required_ipca = {"periodo_num", "indice"}
    missing_ipca = sorted(required_ipca - set(ipca.columns))
    if missing_ipca:
        raise ValueError(f"IPCA input is missing columns: {missing_ipca}")
    if ipca["periodo_num"].duplicated().any():
        raise RuntimeError("IPCA input has duplicate months")
    out = audited_merge(
        panel,
        ipca[["periodo_num", "indice"]],
        merge_id="national_panel_attach_ipca",
        on="periodo_num",
        how="left",
        validate="many_to_one",
    )
    if out["indice"].isna().any() or (out["indice"] <= 0).any():
        missing = sorted(
            out.loc[out["indice"].isna(), "periodo_num"].unique()
        )
        raise RuntimeError(f"Missing IPCA for panel months: {missing}")

    required_classification = {"cbo_4d", "cbo_ilo_gradient"}
    missing_classification = sorted(
        required_classification - set(classification.columns)
    )
    if missing_classification:
        raise ValueError(
            "Classification input is missing columns: "
            f"{missing_classification}"
        )
    classes = classification[
        ["cbo_4d", "cbo_ilo_gradient"]
    ].copy()
    classes["cbo_4d"] = classes["cbo_4d"].astype(str).str.zfill(4)
    out = audited_merge(
        out,
        classes,
        merge_id="national_panel_attach_treatment",
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    new_unclassified = sorted(
        out.loc[out["cbo_ilo_gradient"].isna(), "cbo_4d"].unique()
    )
    out["cbo_ilo_gradient"] = out["cbo_ilo_gradient"].fillna("No score")

    exposed = out["cbo_ilo_gradient"].isin(
        [
            "Exposed: Gradient 1",
            "Exposed: Gradient 2",
            "Exposed: Gradient 3",
            "Exposed: Gradient 4",
        ]
    )
    control = out["cbo_ilo_gradient"].eq("Not Exposed")
    out["treated_main"] = np.where(
        exposed, 1.0, np.where(control, 0.0, np.nan)
    )
    out["included_main"] = exposed | control
    out["periodo"] = (
        out["ano"].astype(str)
        + "-"
        + out["mes"].astype(str).str.zfill(2)
    )
    out["post"] = out["periodo_num"].ge(202212).astype("int8")
    out["salario_real_adm"] = (
        out["salario_medio_adm"] * 100.0 / out["indice"]
    )
    out["salario_real_desl"] = (
        out["salario_medio_desl"] * 100.0 / out["indice"]
    )
    out["ln_admissoes"] = np.log1p(out["admissoes"])
    out["ln_desligamentos"] = np.log1p(out["desligamentos"])
    out["ln_salario_real_adm"] = np.log(out["salario_real_adm"])
    out["ln_salario_real_desl"] = np.log(out["salario_real_desl"])
    out["asinh_saldo"] = np.arcsinh(out["saldo"])
    return (
        out.sort_values(["cbo_4d", "periodo_num"]).reset_index(drop=True),
        new_unclassified,
    )


def build_national_panel(
    movements_glob: Path,
    ipca: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    start_period: int = START_PERIOD,
    end_period: int = END_PERIOD,
    scratch_parent: Path = DEFAULT_SCRATCH_PARENT,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    scratch_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="t12-duckdb-",
        dir=scratch_parent,
    ) as temporary:
        temp_directory = Path(temporary)
        connection = duckdb.connect()
        try:
            _configure_connection(connection, temp_directory)
            _create_movement_views(
                connection,
                movements_glob,
                start_period,
                end_period,
            )
            counts = connection.execute(
                """
                SELECT
                    (SELECT count(*) FROM analytic_source) AS raw_rows,
                    (SELECT count(*) FROM valid_movements) AS valid_rows
                """
            ).fetchone()
            bounds_count = connection.execute(
                """
                SELECT count(*) FROM (
                    SELECT cbo_4d, ano
                    FROM valid_movements
                    WHERE peso = 1
                    GROUP BY cbo_4d, ano
                )
                """
            ).fetchone()[0]
            panel = _aggregate_national(connection)
        finally:
            connection.close()

    panel, new_unclassified = _attach_panel_fields(
        panel, ipca, classification
    )
    validate_national_panel(panel)
    months_by_cbo = panel.groupby("cbo_4d")["periodo_num"].nunique()
    metrics = {
        "raw_rows": int(counts[0]),
        "valid_rows": int(counts[1]),
        "invalid_rows_rejected": int(counts[0] - counts[1]),
        "cells": int(len(panel)),
        "cbo_families": int(panel["cbo_4d"].nunique()),
        "new_unclassified_cbo_families": new_unclassified,
        "months": int(panel["periodo_num"].nunique()),
        "months_per_cbo_min": int(months_by_cbo.min()),
        "months_per_cbo_max": int(months_by_cbo.max()),
        "zero_admission_cells": int(panel["admissoes"].eq(0).sum()),
        "zero_separation_cells": int(
            panel["desligamentos"].eq(0).sum()
        ),
        "max_admission_wage": float(
            panel["salario_medio_adm"].max(skipna=True)
        ),
        "max_separation_wage": float(
            panel["salario_medio_desl"].max(skipna=True)
        ),
        "wage_bound_groups": int(bounds_count),
        "wage_winsorization": (
            "record-level DuckDB approx_quantile P1/P99 "
            "within CBO4 x year, positive-weight records"
        ),
    }
    return panel, metrics


def validate_national_panel(panel: pd.DataFrame) -> None:
    keys = ["cbo_4d", "periodo_num"]
    missing = sorted(set(keys) - set(panel.columns))
    if missing:
        raise RuntimeError(f"National panel is missing keys: {missing}")
    if panel.duplicated(keys).any():
        raise RuntimeError("National panel has duplicate CBO4-month cells")
    for suffix, flow in (
        ("adm", "admissoes"),
        ("desl", "desligamentos"),
    ):
        salary = f"salario_medio_{suffix}"
        zero_flow = panel[flow].eq(0)
        if panel.loc[zero_flow, salary].notna().any():
            side = "admission" if suffix == "adm" else "separation"
            raise RuntimeError(
                f"National panel has a non-null wage in a zero-flow {side} cell"
            )
        for base in COMPOSITION_BASES:
            column = f"{base}_{suffix}"
            if column not in panel.columns:
                raise RuntimeError(
                    f"National panel is missing composition column: {column}"
                )
            if panel.loc[zero_flow, column].notna().any():
                side = "admission" if suffix == "adm" else "separation"
                raise RuntimeError(
                    "National panel has non-null composition in a "
                    f"zero-flow {side} cell: {column}"
                )
        if panel[salary].max(skipna=True) >= WAGE_MAX:
            raise RuntimeError(
                f"National panel {salary} reaches the R$1 million bound"
            )
    if (panel[["admissoes", "desligamentos"]] < 0).any().any():
        raise RuntimeError("National panel has negative flow counts")


def write_panel_artifacts(
    panel: pd.DataFrame,
    metrics: dict[str, Any],
    panel_path: Path = DEFAULT_PANEL,
    support_path: Path = DEFAULT_SUPPORT,
) -> None:
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = panel_path.with_suffix(f"{panel_path.suffix}.tmp")
    panel.to_parquet(temporary, index=False)
    os.replace(temporary, panel_path)
    support_path.parent.mkdir(parents=True, exist_ok=True)
    support_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze IPCA and build the national V2 panel."
    )
    parser.add_argument(
        "command",
        choices=(
            "freeze-ipca",
            "build",
            "all",
            "freeze-cnae",
            "build-sector",
            "all-sector",
        ),
    )
    parser.add_argument(
        "--movements-glob",
        type=Path,
        default=DEFAULT_MOVEMENTS_GLOB,
    )
    parser.add_argument(
        "--classification",
        type=Path,
        default=DEFAULT_CLASSIFICATION,
    )
    parser.add_argument("--ipca", type=Path, default=DEFAULT_IPCA)
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument(
        "--cnae-dictionary",
        type=Path,
        default=DEFAULT_CNAE_DICTIONARY,
    )
    parser.add_argument(
        "--sector-panel",
        type=Path,
        default=DEFAULT_SECTOR_PANEL,
    )
    parser.add_argument(
        "--cnae-month-support",
        type=Path,
        default=DEFAULT_CNAE_MONTH_SUPPORT,
    )
    parser.add_argument(
        "--sector-support",
        type=Path,
        default=DEFAULT_SECTOR_SUPPORT,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command in {"freeze-ipca", "all"}:
        print(json.dumps(freeze_ipca(), sort_keys=True))
    if args.command in {"freeze-cnae", "all-sector"}:
        print(json.dumps(freeze_cnae(), sort_keys=True))
    if args.command in {"build", "all"}:
        if not args.ipca.is_file():
            raise FileNotFoundError(f"Frozen IPCA input not found: {args.ipca}")
        if not args.classification.is_file():
            raise FileNotFoundError(
                f"Treatment classification not found: {args.classification}"
            )
        panel, metrics = build_national_panel(
            args.movements_glob,
            pd.read_parquet(args.ipca),
            pd.read_csv(args.classification, dtype={"cbo_4d": str}),
        )
        write_panel_artifacts(panel, metrics, args.panel, args.support)
        print(json.dumps(metrics, sort_keys=True))
    if args.command in {"build-sector", "all-sector"}:
        required = [
            args.ipca,
            args.classification,
            args.cnae_dictionary,
            args.panel,
        ]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                "Sector-panel inputs are missing:\n" + "\n".join(missing)
            )
        metrics = build_sector_panel(
            args.movements_glob,
            pd.read_parquet(args.ipca),
            pd.read_csv(args.classification, dtype={"cbo_4d": str}),
            load_cnae_divisions(args.cnae_dictionary),
            args.panel,
            args.sector_panel,
            args.cnae_month_support,
        )
        args.sector_support.parent.mkdir(parents=True, exist_ok=True)
        args.sector_support.write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(metrics, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
