#!/usr/bin/env python3
"""Execute the preregistered PNADc Stage 0 without treatment coefficients."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd


sys.dont_write_bytecode = True

FRONT_ROOT = Path(__file__).resolve().parents[1]
V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
sys.path.insert(0, str(V2_ROOT / "code" / "common"))

from merge_audit import audited_merge  # noqa: E402

VINTAGE_DIR = FRONT_ROOT / "data" / "vintage"
RESULTS_DIR = FRONT_ROOT / "results"
MANIFEST_PATH = VINTAGE_DIR / "manifest.json"
ACQUISITION_STATUS_PATH = RESULTS_DIR / "pnadc_acquisition_status.json"
RECONCILIATION_PATH = RESULTS_DIR / "pnadc_reconciliation.csv"
RECONCILIATION_STATUS_PATH = RESULTS_DIR / "pnadc_reconciliation_status.json"
RECONCILIATION_REPORT_PATH = RESULTS_DIR / "PNADC_RECONCILIACAO.md"
SIDRA_VINTAGE_PATH = VINTAGE_DIR / "sidra_6463.json"
CROSSWALK_COVERAGE_PATH = RESULTS_DIR / "pnadc_crosswalk_coverage.csv"
CROSSWALK_STATUS_PATH = RESULTS_DIR / "pnadc_crosswalk_status.json"
CROSSWALK_REPORT_PATH = RESULTS_DIR / "PNADC_CROSSWALK.md"
SUPPORT_PATH = RESULTS_DIR / "pnadc_support.csv"
TREATMENT_COD3_PATH = RESULTS_DIR / "pnadc_treatment_cod3.csv"
SUPPORT_STATUS_PATH = RESULTS_DIR / "pnadc_support_status.json"
SUPPORT_REPORT_PATH = RESULTS_DIR / "PNADC_SUPORTE.md"
BREAK_2020_PATH = RESULTS_DIR / "pnadc_2020_break.csv"
BREAK_2020_STATUS_PATH = RESULTS_DIR / "pnadc_2020_break_status.json"
BREAK_2020_REPORT_PATH = RESULTS_DIR / "PNADC_QUEBRA_2020.md"

BILLING_PROJECT = os.environ.get("REPLICATION_BILLING_PROJECT", "")
SOURCE_TABLE = "basedosdados.br_ibge_pnadc.microdados"
MINIMUM_QUARTER_ROWS = 100_000
EXPECTED_STATE_COUNT = 27
BIGQUERY_TIMEOUT_SECONDS = 900
FTP_BASE_URL = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/"
    "Microdados"
)
FTP_DICTIONARY_URL = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/"
    "Microdados/Documentacao/Dicionario_e_input_20221031.zip"
)
FTP_DICTIONARY_PATH = VINTAGE_DIR / "pnadc_dictionary_20221031.zip"
SIDRA_6463_URL = (
    "https://apisidra.ibge.gov.br/values/t/6463/n1/1/v/1641/"
    "p/all/c629/32385,32387?formato=json"
)
SECTION3_EXPECTED_ROWS = 207_901
SECTION3_EXPECTED_POPULATION = 97_783_776.1804
ILO_PATH = (
    V2_ROOT
    / "data"
    / "vintage"
    / "crosswalk"
    / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"
)
ILO_EXPECTED_SHA256 = (
    "c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a"
)

P1_COLUMNS = (
    "ano",
    "trimestre",
    "sigla_uf",
    "sexo",
    "idade",
    "raca_cor",
    "nivel_instrucao",
    "cod_ocupacao",
    "grupamento_atividade",
    "posicao_ocupacao",
    "rendimento_habitual",
    "horas_habituais",
    "peso",
)

CODE_COLUMNS = (
    "sigla_uf",
    "sexo",
    "raca_cor",
    "nivel_instrucao",
    "cod_ocupacao",
    "grupamento_atividade",
    "posicao_ocupacao",
)

UF_CODE_TO_SIGLA = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}

FTP_COLUMNS = (
    "ano",
    "trimestre",
    "uf_code",
    "peso",
    "sexo",
    "idade",
    "raca_cor",
    "cod_ocupacao",
    "grupamento_atividade",
    "nivel_instrucao",
    "vd4002",
    "posicao_ocupacao",
    "rendimento_habitual",
    "horas_habituais",
)

FTP_COLSPECS = (
    (0, 4),
    (4, 5),
    (5, 7),
    (49, 64),
    (94, 95),
    (103, 106),
    (106, 107),
    (151, 155),
    (157, 162),
    (404, 405),
    (409, 410),
    (416, 418),
    (426, 434),
    (461, 464),
)

OFFICIAL_FTP_PERIODS = {
    *{
        (year, quarter)
        for year in range(2012, 2025)
        for quarter in range(1, 5)
    },
    (2025, 4),
}
FTP_URL_CACHE: dict[tuple[int, int], str] = {}


def expected_periods() -> list[tuple[int, int]]:
    """Return the frozen 2012Q1--2026Q1 quarterly grid."""
    return [
        (year, quarter)
        for year in range(2012, 2027)
        for quarter in range(1, 5)
        if (year, quarter) <= (2026, 1)
    ]


def build_extract_query(year: int, quarter: int) -> str:
    """Build the exact P1 microdata query for one quarter."""
    return f"""
SELECT
  ano,
  trimestre,
  sigla_uf,
  v2007 AS sexo,
  v2009 AS idade,
  v2010 AS raca_cor,
  vd3004 AS nivel_instrucao,
  v4010 AS cod_ocupacao,
  v4013 AS grupamento_atividade,
  vd4009 AS posicao_ocupacao,
  vd4016 AS rendimento_habitual,
  vd4031 AS horas_habituais,
  v1028 AS peso
FROM `{SOURCE_TABLE}`
WHERE ano = {int(year)}
  AND trimestre = {int(quarter)}
  AND v4010 IS NOT NULL
  AND v2009 BETWEEN 18 AND 65
""".strip()


def build_reference_population_query() -> str:
    """Build the P2 aggregates matching SIDRA plus the analytic age window."""
    return f"""
SELECT
  ano,
  trimestre,
  COUNTIF(v2009 >= 14) AS bq_rows_14plus,
  SUM(IF(v2009 >= 14, v1028, 0.0)) AS bq_population_14plus,
  COUNTIF(v2009 >= 14 AND vd4002 = '1') AS bq_occupied_rows_14plus,
  SUM(
    IF(v2009 >= 14 AND vd4002 = '1', v1028, 0.0)
  ) AS bq_occupied_population_14plus,
  COUNTIF(
    v2009 BETWEEN 18 AND 65
    AND v4010 IS NOT NULL
    AND v4010 NOT IN ('0000', '9999')
  ) AS analytic_rows_18_65,
  SUM(
    IF(
      v2009 BETWEEN 18 AND 65
      AND v4010 IS NOT NULL
      AND v4010 NOT IN ('0000', '9999'),
      v1028,
      0.0
    )
  ) AS analytic_population_18_65
FROM `{SOURCE_TABLE}`
WHERE (
    ano BETWEEN 2012 AND 2025
    OR (ano = 2026 AND trimestre = 1)
  )
GROUP BY ano, trimestre
ORDER BY ano, trimestre
""".strip()


def probe_query() -> str:
    """Return the required LIMIT 5 availability probe."""
    return build_extract_query(2026, 1) + "\nLIMIT 5"


def _bigquery_client():
    if not BILLING_PROJECT:
        raise RuntimeError("A BigQuery billing project is required")
    try:
        from google.cloud import bigquery
    except ImportError as error:
        raise RuntimeError(
            "Full PNADc acquisition requires `uv sync --frozen`."
        ) from error
    return bigquery.Client(project=BILLING_PROJECT)


def run_bq_csv(query: str, *, maximum_rows: int) -> pd.DataFrame:
    """Run Standard SQL through the locked authenticated Python client."""
    try:
        rows = _bigquery_client().query(query).result(
            max_results=int(maximum_rows),
            timeout=BIGQUERY_TIMEOUT_SECONDS,
        )
    except TimeoutError as error:
        raise RuntimeError(
            f"BigQuery query exceeded {BIGQUERY_TIMEOUT_SECONDS} seconds"
        ) from error
    frame = rows.to_dataframe(create_bqstorage_client=True)
    if frame.empty:
        raise RuntimeError("BigQuery returned an empty response.")
    return frame


def normalize_quarter_extract(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize BigQuery CSV types without changing the P1 row universe."""
    missing = sorted(set(P1_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Quarter extract is missing columns: {missing}")
    result = frame.loc[:, P1_COLUMNS].copy()
    for column in CODE_COLUMNS:
        result[column] = result[column].astype("string")
    for column in (
        "ano",
        "trimestre",
        "idade",
        "rendimento_habitual",
        "horas_habituais",
        "peso",
    ):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result["ano"] = result["ano"].astype("Int64")
    result["trimestre"] = result["trimestre"].astype("Int64")
    result["idade"] = result["idade"].astype("Int64")
    return result.sort_values(list(P1_COLUMNS), kind="stable").reset_index(drop=True)


def normalize_ftp_extract(
    frame: pd.DataFrame,
    *,
    year: int,
    quarter: int,
) -> pd.DataFrame:
    """Translate the official fixed-width fields to the exact P1 schema."""
    missing = sorted(set(FTP_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"FTP extract is missing columns: {missing}")
    result = frame.copy()
    result["idade"] = pd.to_numeric(result["idade"], errors="coerce")
    result = result.loc[
        result["cod_ocupacao"].notna()
        & result["idade"].between(18, 65)
    ].copy()
    result["sigla_uf"] = result["uf_code"].astype("string").map(UF_CODE_TO_SIGLA)
    if result["sigla_uf"].isna().any():
        unknown = sorted(result.loc[result["sigla_uf"].isna(), "uf_code"].unique())
        raise ValueError(f"Unknown IBGE UF codes in FTP extract: {unknown}")
    result["ano"] = int(year)
    result["trimestre"] = int(quarter)
    return normalize_quarter_extract(result)


def _download_atomic(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with urlopen(url) as response, temporary.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)
    os.replace(temporary, path)


def select_ftp_archive_name(html: str, *, year: int, quarter: int) -> str:
    prefix = f"PNADC_{int(quarter):02d}{int(year)}"
    candidates = sorted(
        set(
            re.findall(
                rf'href="({re.escape(prefix)}[^"]*\.zip)"',
                html,
                flags=re.IGNORECASE,
            )
        )
    )
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected one FTP archive for {year}Q{quarter}; found {candidates}"
        )
    return candidates[0]


def ftp_quarter_url(year: int, quarter: int) -> str:
    period = (int(year), int(quarter))
    if period in FTP_URL_CACHE:
        return FTP_URL_CACHE[period]
    directory_url = f"{FTP_BASE_URL}/{period[0]}/"
    with urlopen(directory_url) as response:
        html = response.read().decode("latin-1")
    archive_name = select_ftp_archive_name(
        html,
        year=period[0],
        quarter=period[1],
    )
    url = f"{directory_url}{archive_name}"
    FTP_URL_CACHE[period] = url
    return url


def ftp_quarter_path(year: int, quarter: int) -> Path:
    return VINTAGE_DIR / ftp_quarter_url(year, quarter).rsplit("/", 1)[-1]


def ftp_reconciliation_path(year: int, quarter: int) -> Path:
    return VINTAGE_DIR / f"pnadc_{int(year)}q{int(quarter)}_reconciliation.json"


def _add_reconciliation_chunk(
    totals: dict[str, float | int],
    chunk: pd.DataFrame,
) -> None:
    weights = pd.to_numeric(chunk["peso"], errors="coerce")
    ages = pd.to_numeric(chunk["idade"], errors="coerce")
    codes = chunk["cod_ocupacao"].astype("string").str.strip()
    age14 = ages.ge(14) & weights.notna()
    occupied14 = age14 & chunk["vd4002"].eq("1")
    analytic = (
        ages.between(18, 65)
        & codes.notna()
        & ~codes.isin(["0000", "9999"])
        & weights.notna()
    )
    totals["bq_rows_14plus"] += int(age14.sum())
    totals["bq_population_14plus"] += float(weights.loc[age14].sum())
    totals["bq_occupied_rows_14plus"] += int(occupied14.sum())
    totals["bq_occupied_population_14plus"] += float(
        weights.loc[occupied14].sum()
    )
    totals["analytic_rows_18_65"] += int(analytic.sum())
    totals["analytic_population_18_65"] += float(weights.loc[analytic].sum())


def read_ftp_quarter(*, year: int, quarter: int) -> pd.DataFrame:
    """Stream one official FTP quarter and freeze its P1/P2 extracts."""
    if (year, quarter) not in OFFICIAL_FTP_PERIODS:
        raise ValueError(f"FTP is not the registered route for {year}Q{quarter}.")
    archive_path = ftp_quarter_path(year, quarter)
    archive_url = ftp_quarter_url(year, quarter)
    if not archive_path.exists():
        _download_atomic(archive_url, archive_path)
    if not FTP_DICTIONARY_PATH.exists():
        _download_atomic(FTP_DICTIONARY_URL, FTP_DICTIONARY_PATH)

    chunks: list[pd.DataFrame] = []
    reconciliation: dict[str, float | int] = {
        "bq_rows_14plus": 0,
        "bq_population_14plus": 0.0,
        "bq_occupied_rows_14plus": 0,
        "bq_occupied_population_14plus": 0.0,
        "analytic_rows_18_65": 0,
        "analytic_population_18_65": 0.0,
    }
    member = f"PNADC_{int(quarter):02d}{int(year)}.txt"
    with ZipFile(archive_path) as archive:
        members = [
            name
            for name in archive.namelist()
            if name.upper().endswith(".TXT")
        ]
        if members != [member]:
            raise RuntimeError(f"Unexpected PNADc FTP archive members: {members}")
        with archive.open(member) as handle:
            reader = pd.read_fwf(
                handle,
                colspecs=FTP_COLSPECS,
                names=FTP_COLUMNS,
                dtype="string",
                encoding="latin-1",
                chunksize=100_000,
            )
            for raw_chunk in reader:
                _add_reconciliation_chunk(reconciliation, raw_chunk)
                normalized = normalize_ftp_extract(
                    raw_chunk,
                    year=year,
                    quarter=quarter,
                )
                if not normalized.empty:
                    chunks.append(normalized)
    if not chunks:
        raise RuntimeError(
            f"The official {year}Q{quarter} FTP archive yielded no P1 rows."
        )
    atomic_json(
        {
            "archive_bytes": int(archive_path.stat().st_size),
            "archive_sha256": sha256_file(archive_path),
            "archive_source": archive_url,
            "metrics": reconciliation,
            "period": f"{year}Q{quarter}",
        },
        ftp_reconciliation_path(year, quarter),
    )
    return (
        pd.concat(chunks, ignore_index=True)
        .sort_values(list(P1_COLUMNS), kind="stable")
        .reset_index(drop=True)
    )


def validate_quarter_extract(
    frame: pd.DataFrame,
    *,
    year: int,
    quarter: int,
) -> dict[str, int]:
    """Validate the three binary P1 acquisition gates for one quarter."""
    missing = sorted(set(P1_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Quarter extract is missing columns: {missing}")
    observed_periods = set(
        zip(
            pd.to_numeric(frame["ano"], errors="coerce").dropna().astype(int),
            pd.to_numeric(frame["trimestre"], errors="coerce").dropna().astype(int),
        )
    )
    expected_period = {(int(year), int(quarter))}
    if observed_periods != expected_period:
        raise ValueError(
            f"Quarter extract has unexpected periods: {sorted(observed_periods)}"
        )
    rows = int(len(frame))
    if rows < MINIMUM_QUARTER_ROWS:
        raise ValueError(
            f"Quarter {year}Q{quarter} has fewer than 100,000 rows: {rows}"
        )
    states = int(frame["sigla_uf"].nunique(dropna=True))
    if states != EXPECTED_STATE_COUNT:
        raise ValueError(
            f"Quarter {year}Q{quarter} has {states} UFs; expected 27 UFs"
        )
    return {
        "year": int(year),
        "quarter": int(quarter),
        "rows": rows,
        "states": states,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_parquet(temporary, index=False, compression="zstd")
    os.replace(temporary, path)


def _existing_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {}
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"PNADc manifest must be a JSON object: {MANIFEST_PATH}")
    return payload


def _existing_manifest_entries(
    payload: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    payload = _existing_manifest() if payload is None else payload
    return {
        str(entry["trimestre"]): entry
        for entry in payload.get("entries", [])
    }


def validate_registered_asset(
    path: Path,
    metadata: dict[str, Any],
    *,
    label: str,
) -> None:
    """Reject a changed cached source instead of silently replacing it."""
    required = {"bytes", "sha256"}
    missing = sorted(required - set(metadata))
    if missing:
        raise ValueError(
            f"Registered {label} metadata is missing fields {missing}"
        )
    if not path.is_file():
        raise FileNotFoundError(f"Registered {label} is missing: {path}")
    observed_bytes = int(path.stat().st_size)
    expected_bytes = int(metadata["bytes"])
    if observed_bytes != expected_bytes:
        raise ValueError(
            f"Registered {label} byte-size mismatch: expected "
            f"{expected_bytes}, observed {observed_bytes}"
        )
    observed_sha256 = sha256_file(path)
    expected_sha256 = str(metadata["sha256"])
    if observed_sha256 != expected_sha256:
        raise ValueError(
            f"Registered {label} SHA-256 mismatch: expected "
            f"{expected_sha256}, observed {observed_sha256}"
        )


def registered_manifest_is_complete(payload: dict[str, Any]) -> bool:
    """Validate the header and period grid of a completed PNADc cache."""
    if not payload or payload.get("status") != "complete":
        return False
    if payload.get("source") != SOURCE_TABLE:
        raise ValueError("Registered PNADc source table does not match")
    if payload.get("route") != "mixed_bigquery_cli_ibge_ftp":
        raise ValueError("Registered PNADc acquisition route does not match")
    if int(payload.get("expected_quarters", -1)) != len(expected_periods()):
        raise ValueError("Registered PNADc expected-quarter count does not match")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Registered PNADc manifest entries are invalid")
    periods = [str(entry.get("trimestre")) for entry in entries]
    expected = [f"{year}Q{quarter}" for year, quarter in expected_periods()]
    if periods != expected:
        raise ValueError("Registered PNADc period grid does not match")
    return True


def _manifest_entry(
    path: Path,
    *,
    year: int,
    quarter: int,
    rows: int,
    query: str,
    accessed_at: str,
    route: str,
    source: str,
) -> dict[str, Any]:
    return {
        "acessado_em": accessed_at,
        "bytes": int(path.stat().st_size),
        "fonte": source,
        "linhas": int(rows),
        "consulta": query,
        "sha256": sha256_file(path),
        "trimestre": f"{year}Q{quarter}",
        "arquivo": path.name,
        "rota": route,
    }


def acquire_vintage() -> dict[str, Any]:
    """Download, freeze, validate, and manifest all 57 P1 extracts."""
    prior_manifest = _existing_manifest()
    cache_complete = registered_manifest_is_complete(prior_manifest)
    if not cache_complete:
        probe = run_bq_csv(probe_query(), maximum_rows=5)
        missing_probe = sorted(set(P1_COLUMNS) - set(probe.columns))
        if len(probe) != 5 or missing_probe:
            raise RuntimeError(
                "The LIMIT 5 probe did not return the full P1 schema: "
                f"rows={len(probe)}, missing={missing_probe}"
            )

    prior_entries = _existing_manifest_entries(prior_manifest)
    prior_ftp_assets = dict(prior_manifest.get("ftp_assets", {}))
    entries: list[dict[str, Any]] = []
    quarter_metrics: list[dict[str, int]] = []
    try:
        for year, quarter in expected_periods():
            period = f"{year}Q{quarter}"
            path = VINTAGE_DIR / f"pnadc_{year}q{quarter}.parquet"
            query = build_extract_query(year, quarter)
            prior = prior_entries.get(period)
            target_route = (
                "ibge_ftp"
                if (year, quarter) in OFFICIAL_FTP_PERIODS
                else "bigquery_cli"
            )
            prior_route = (
                str(prior.get("rota", "bigquery_cli"))
                if prior is not None
                else None
            )
            registered_ftp_url = (
                str(prior.get("fonte"))
                if prior is not None and prior_route == "ibge_ftp"
                else None
            )
            if target_route == "ibge_ftp":
                quarter_url = (
                    registered_ftp_url
                    if registered_ftp_url
                    else ftp_quarter_url(year, quarter)
                )
                if not quarter_url.startswith(f"{FTP_BASE_URL}/{year}/"):
                    raise ValueError(
                        f"Registered PNADc FTP source mismatch for {period}: "
                        f"{quarter_url}"
                    )
                FTP_URL_CACHE[(year, quarter)] = quarter_url
                archive_path = VINTAGE_DIR / quarter_url.rsplit("/", 1)[-1]
            else:
                quarter_url = ""
                archive_path = None
            needs_ftp_refresh = (
                target_route == "ibge_ftp"
                and (
                    prior_route != "ibge_ftp"
                    or archive_path is None
                    or not archive_path.exists()
                    or not FTP_DICTIONARY_PATH.exists()
                    or not ftp_reconciliation_path(year, quarter).exists()
                )
            )
            if path.exists() and not needs_ftp_refresh:
                if prior is None:
                    raise ValueError(
                        f"Unregistered PNADc extract already exists: {path}"
                    )
                validate_registered_asset(
                    path,
                    prior,
                    label=f"PNADc analytical extract {period}",
                )
                if str(prior.get("arquivo")) != path.name:
                    raise ValueError(
                        f"Registered PNADc filename mismatch for {period}"
                    )
                if prior_route != target_route:
                    raise ValueError(
                        f"Registered PNADc route mismatch for {period}: "
                        f"expected {target_route}, observed {prior_route}"
                    )
                if target_route == "ibge_ftp":
                    if archive_path is None:
                        raise AssertionError("FTP archive path was not resolved")
                    archive_metadata = prior_ftp_assets.get(archive_path.name)
                    if archive_metadata is None:
                        raise ValueError(
                            f"Registered PNADc FTP asset is missing from the "
                            f"manifest: {archive_path.name}"
                        )
                    validate_registered_asset(
                        archive_path,
                        archive_metadata,
                        label=f"PNADc FTP archive {period}",
                    )
                frame = pd.read_parquet(path)
                metrics = validate_quarter_extract(
                    frame,
                    year=year,
                    quarter=quarter,
                )
                if int(prior.get("linhas", -1)) != metrics["rows"]:
                    raise ValueError(
                        f"Registered PNADc row-count mismatch for {period}"
                    )
                accessed_at = (
                    str(prior["acessado_em"])
                    if prior is not None
                    else datetime.fromtimestamp(
                        path.stat().st_mtime,
                        tz=timezone.utc,
                    ).isoformat()
                )
            else:
                if target_route == "ibge_ftp":
                    frame = read_ftp_quarter(year=year, quarter=quarter)
                else:
                    raw = run_bq_csv(query, maximum_rows=1_000_000)
                    frame = normalize_quarter_extract(raw)
                metrics = validate_quarter_extract(
                    frame,
                    year=year,
                    quarter=quarter,
                )
                atomic_parquet(frame, path)
                accessed_at = datetime.now(timezone.utc).isoformat()
            route = target_route
            quarter_url = (
                quarter_url
                if route == "ibge_ftp"
                else ""
            )
            entry_query = (
                query
                if route == "bigquery_cli"
                else (
                    f"fixed-width parse of {quarter_url}; "
                    f"dictionary={FTP_DICTIONARY_URL}"
                )
            )
            entry_source = (
                SOURCE_TABLE
                if route == "bigquery_cli"
                else quarter_url
            )
            quarter_metrics.append(metrics)
            entries.append(
                _manifest_entry(
                    path,
                    year=year,
                    quarter=quarter,
                    rows=metrics["rows"],
                    query=entry_query,
                    accessed_at=accessed_at,
                    route=route,
                    source=entry_source,
                )
            )
            print(
                f"P1 {period}: {metrics['rows']} rows, "
                f"{metrics['states']} UFs, sha256={entries[-1]['sha256'][:12]}…",
                flush=True,
            )
            atomic_json(
                {
                    "billing_project": BILLING_PROJECT,
                    "entries": entries,
                    "expected_quarters": 57,
                    "route": "mixed_bigquery_cli_ibge_ftp",
                    "source": SOURCE_TABLE,
                    "status": "in_progress",
                },
                MANIFEST_PATH,
            )
    except ValueError as exc:
        status = {
            "error": str(exc),
            "route": "bigquery_cli",
            "status": "not_executed_pnadc_vintage_incomplete",
        }
        atomic_json(status, ACQUISITION_STATUS_PATH)
        raise

    ftp_assets: dict[str, dict[str, Any]] = {
        FTP_DICTIONARY_PATH.name: {
            "bytes": int(FTP_DICTIONARY_PATH.stat().st_size),
            "sha256": sha256_file(FTP_DICTIONARY_PATH),
            "source": FTP_DICTIONARY_URL,
        }
    }
    dictionary_metadata = prior_ftp_assets.get(FTP_DICTIONARY_PATH.name)
    if dictionary_metadata is not None:
        validate_registered_asset(
            FTP_DICTIONARY_PATH,
            dictionary_metadata,
            label="PNADc FTP dictionary",
        )
    elif prior_manifest.get("status") == "complete":
        raise ValueError("Registered PNADc FTP dictionary metadata is missing")
    for entry in entries:
        if entry["rota"] != "ibge_ftp":
            continue
        year = int(str(entry["trimestre"])[:4])
        quarter = int(str(entry["trimestre"])[-1])
        archive_path = VINTAGE_DIR / str(entry["fonte"]).rsplit("/", 1)[-1]
        archive_metadata = prior_ftp_assets.get(archive_path.name)
        if archive_metadata is not None:
            validate_registered_asset(
                archive_path,
                archive_metadata,
                label=f"PNADc FTP archive {year}Q{quarter}",
            )
        elif prior_manifest.get("status") == "complete":
            raise ValueError(
                f"Registered PNADc FTP asset metadata is missing: "
                f"{archive_path.name}"
            )
        ftp_assets[archive_path.name] = {
            "bytes": int(archive_path.stat().st_size),
            "sha256": sha256_file(archive_path),
            "source": entry["fonte"],
        }
    route_counts = {
        route: sum(entry["rota"] == route for entry in entries)
        for route in ("bigquery_cli", "ibge_ftp")
    }
    manifest = {
        "billing_project": BILLING_PROJECT,
        "entries": entries,
        "expected_quarters": 57,
        "ftp_assets": ftp_assets,
        "route": "mixed_bigquery_cli_ibge_ftp",
        "source": SOURCE_TABLE,
        "status": "complete",
    }
    atomic_json(manifest, MANIFEST_PATH)
    status = {
        "first_period": "2012Q1",
        "last_period": "2026Q1",
        "minimum_rows": min(item["rows"] for item in quarter_metrics),
        "quarters_expected": 57,
        "quarters_present": len(quarter_metrics),
        "probe_executed": not cache_complete,
        "route": "mixed_bigquery_cli_ibge_ftp",
        "route_counts": route_counts,
        "states_each_quarter": 27,
        "status": "pass",
    }
    atomic_json(status, ACQUISITION_STATUS_PATH)
    return status


def parse_sidra_6463(payload: list[dict[str, str]]) -> pd.DataFrame:
    """Parse the official total and occupied 14+ series from SIDRA."""
    if len(payload) < 3:
        raise ValueError("SIDRA table 6463 returned too few records.")
    records = pd.DataFrame(payload[1:])
    required = {"V", "D3C", "D4C"}
    missing = sorted(required - set(records.columns))
    if missing:
        raise ValueError(f"SIDRA table 6463 is missing fields: {missing}")
    records = records.loc[records["D4C"].isin(["32385", "32387"])].copy()
    records["value"] = pd.to_numeric(records["V"], errors="raise") * 1_000.0
    records["ano"] = records["D3C"].str[:4].astype(int)
    records["trimestre"] = records["D3C"].str[-2:].astype(int)
    records["metric"] = records["D4C"].map(
        {
            "32385": "sidra_population_14plus",
            "32387": "sidra_occupied_14plus",
        }
    )
    result = (
        records.pivot(
            index=["ano", "trimestre"],
            columns="metric",
            values="value",
        )
        .reset_index()
        .rename_axis(columns=None)
        .sort_values(["ano", "trimestre"])
        .reset_index(drop=True)
    )
    if result.duplicated(["ano", "trimestre"]).any():
        raise ValueError("SIDRA table 6463 has duplicate quarters.")
    return result[
        [
            "ano",
            "trimestre",
            "sidra_population_14plus",
            "sidra_occupied_14plus",
        ]
    ]


def section3_anchor(frame: pd.DataFrame) -> dict[str, float | int]:
    """Apply only the frozen Section 3 age and invalid-code filters."""
    data = frame.copy()
    codes = (
        data["cod_ocupacao"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(4)
    )
    ages = pd.to_numeric(data["idade"], errors="coerce")
    weights = pd.to_numeric(data["peso"], errors="coerce")
    valid = (
        ages.between(18, 65)
        & codes.notna()
        & ~codes.isin(["0000", "9999"])
        & weights.notna()
    )
    return {
        "rows": int(valid.sum()),
        "population": round(float(weights.loc[valid].sum()), 4),
    }


def build_ilo_crosswalk(raw: pd.DataFrame) -> pd.DataFrame:
    """Collapse the task-level ILO workbook to one exact ISCO-08 code."""
    required = {"ISCO_08", "potential25"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"ILO workbook is missing columns: {missing}")
    data = raw.loc[:, ["ISCO_08", "potential25"]].copy()
    numeric_codes = pd.to_numeric(data["ISCO_08"], errors="raise").astype(int)
    data["cod4"] = numeric_codes.astype(str).str.zfill(4)
    conflicts = (
        data.groupby("cod4")["potential25"]
        .nunique(dropna=True)
        .gt(1)
    )
    if conflicts.any():
        raise ValueError(
            "ILO potential25 conflicts within ISCO-08 codes: "
            f"{conflicts[conflicts].index.tolist()}"
        )
    result = (
        data.groupby("cod4", as_index=False)
        .agg(exposure_gradient=("potential25", "first"))
        .sort_values("cod4")
        .reset_index(drop=True)
    )
    result["ilo_exact_match"] = True
    return result


def attach_crosswalk(
    frame: pd.DataFrame,
    crosswalk: pd.DataFrame,
) -> pd.DataFrame:
    """Attach exact gradients and label numeric hierarchical fallbacks."""
    data = frame.copy()
    data["cod4"] = (
        data["cod_ocupacao"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(4)
    )
    valid = (
        data["cod4"].str.fullmatch(r"[0-9]{4}", na=False)
        & ~data["cod4"].isin(["0000", "9999"])
    )
    data = data.loc[valid].copy()
    result = audited_merge(
        data,
        crosswalk,
        merge_id="pnadc_attach_exact_ilo_gradient",
        on="cod4",
        how="left",
        validate="many_to_one",
    )
    exact = result["ilo_exact_match"].eq(True)
    crosswalk_codes = crosswalk["cod4"].astype("string")
    prefix_sets = {
        digits: set(crosswalk_codes.str[:digits])
        for digits in (3, 2, 1)
    }
    result["match_type"] = "unmatched"
    result.loc[
        ~exact & result["cod4"].str[:1].isin(prefix_sets[1]),
        "match_type",
    ] = "fallback_1_digit"
    result.loc[
        ~exact & result["cod4"].str[:2].isin(prefix_sets[2]),
        "match_type",
    ] = "fallback_2_digit"
    result.loc[
        ~exact & result["cod4"].str[:3].isin(prefix_sets[3]),
        "match_type",
    ] = "fallback_3_digit"
    result.loc[exact, "match_type"] = "exact_4_digit"
    result.loc[~exact, "exposure_gradient"] = "Sem classificação"
    result["exposure_gradient"] = result["exposure_gradient"].fillna(
        "Sem classificação"
    )
    result["estimation_eligible_exact_match"] = (
        result["match_type"].eq("exact_4_digit")
        & result["exposure_gradient"].ne("Sem classificação")
    )
    return result.drop(columns=["ilo_exact_match"])


def classify_support(treated_cod3: int, control_cod3: int) -> str:
    """Apply the frozen 20/50 and 10/25 support thresholds."""
    if treated_cod3 >= 20 and control_cod3 >= 50:
        return "adequate"
    if treated_cod3 >= 10 and control_cod3 >= 25:
        return "limited"
    return "thin"


def classify_2020_break(
    gap_changes: pd.Series,
    *,
    complete: bool,
) -> str:
    """Apply the registered completeness and one-percentage-point rule."""
    values = pd.to_numeric(gap_changes, errors="coerce")
    if not complete or values.empty or values.isna().any():
        return "indeterminate"
    if values.abs().gt(1.0).any():
        return "differential"
    return "non_differential"


def formal_indicator(values: pd.Series) -> pd.Series:
    """Apply the frozen Section 3 formal-position map across source encodings."""
    normalized = (
        pd.to_numeric(values, errors="coerce")
        .astype("Int64")
        .astype("string")
    )
    return normalized.isin(["1", "3", "5"])


def _assign_cod3_treatment_status(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["exposed_employment_share"] = (
        result["exposed_employment_weight"]
        / result["total_employment_weight"]
    )
    result["treatment_status"] = "intermediate"
    result.loc[
        result["exposed_employment_share"].eq(0.0),
        "treatment_status",
    ] = "control"
    result.loc[
        result["exposed_employment_share"].ge(0.50),
        "treatment_status",
    ] = "treated"
    result["treated_cod3"] = result["treatment_status"].map(
        {"treated": 1, "control": 0}
    )
    return result


def derive_cod3_treatment(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive the preregistered pre-period employment-weighted COD3 rule."""
    data = frame.copy()
    data["cod3"] = data["cod4"].astype("string").str[:3]
    data["peso"] = pd.to_numeric(data["peso"], errors="raise")
    data["exposed_weight"] = data["peso"].where(
        data["exposure_gradient"].astype("string").str.startswith("Exposed:"),
        0.0,
    )
    summary = (
        data.groupby("cod3", as_index=False)
        .agg(
            total_employment_weight=("peso", "sum"),
            exposed_employment_weight=("exposed_weight", "sum"),
            pre_observations=("cod4", "size"),
            exact_cod4_count=("cod4", "nunique"),
        )
        .sort_values("cod3")
        .reset_index(drop=True)
    )
    return _assign_cod3_treatment_status(summary)


def fetch_sidra_6463() -> tuple[list[dict[str, str]], str]:
    """Fetch and freeze the exact official SIDRA reconciliation slice."""
    if SIDRA_VINTAGE_PATH.is_file():
        frozen = json.loads(SIDRA_VINTAGE_PATH.read_text(encoding="utf-8"))
        if not isinstance(frozen, dict):
            raise ValueError("Frozen SIDRA source must be a JSON object")
        if frozen.get("source") != SIDRA_6463_URL:
            raise ValueError("Frozen SIDRA source URL does not match the contract")
        records = frozen.get("records")
        accessed_at = frozen.get("accessed_at")
        if not isinstance(records, list) or not isinstance(accessed_at, str):
            raise ValueError("Frozen SIDRA source has an invalid schema")
        return records, accessed_at

    with urlopen(SIDRA_6463_URL) as response:
        payload = json.loads(response.read().decode("utf-8-sig"))
    accessed_at = datetime.now(timezone.utc).isoformat()
    atomic_json(
        {
            "accessed_at": accessed_at,
            "records": payload,
            "source": SIDRA_6463_URL,
        },
        SIDRA_VINTAGE_PATH,
    )
    return payload, accessed_at


def ftp_reconciliation(year: int, quarter: int) -> dict[str, float | int]:
    """Load the frozen P2 aggregates created with an FTP quarter."""
    path = ftp_reconciliation_path(year, quarter)
    if not path.exists():
        read_ftp_quarter(year=year, quarter=quarter)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload["metrics"])


def _reconciliation_markdown(
    frame: pd.DataFrame,
    *,
    anchor_rows: int,
    anchor_population: float,
) -> str:
    divergences = frame.loc[
        frame[
            [
                "population_14plus_absolute_relative_difference",
                "occupied_14plus_absolute_relative_difference",
            ]
        ]
        .max(axis=1)
        .gt(0.01)
    ]
    if divergences.empty:
        divergence_text = (
            "No quarter differs by more than 1% from the official SIDRA release."
        )
    else:
        periods = ", ".join(
            f"{int(row.ano)}T{int(row.trimestre)}"
            for row in divergences.itertuples()
        )
        divergence_text = (
            "Differences above 1% require further investigation in: "
            f"{periods}."
        )
    maximum_total = float(
        frame["population_14plus_absolute_relative_difference"].max()
    )
    maximum_occupied = float(
        frame["occupied_14plus_absolute_relative_difference"].max()
    )
    return f"""# PNADc reconciliation

## Contract

The reconciliation compares microdata weights with official SIDRA table 6463, variable 1641, for
the total and employed populations aged 14 or older. The employed population aged 18--65 is reported
separately because it is the preregistered analytical universe. SIDRA publishes values in thousands
of persons.

## Result

- Quarters reconciled: {len(frame)}.
- Maximum absolute relative difference, population aged 14+: {maximum_total:.6%}.
- Maximum absolute relative difference, employed population aged 14+: {maximum_occupied:.6%}.
- {divergence_text}

## Section 3 anchor

For 2025Q3, the frozen filters reproduce {anchor_rows:,} observations and
{anchor_population:.4f} weighted persons. The frozen constants are
{SECTION3_EXPECTED_ROWS:,} and {SECTION3_EXPECTED_POPULATION:.4f}, with an absolute population
tolerance of 1e-6.

This reconciliation estimates no treatment coefficient. The design measures formal--informal
composition, not individual worker transitions.
"""


def reconcile_vintage() -> dict[str, Any]:
    """Execute P2 against SIDRA and the frozen Section 3 constants."""
    payload, accessed_at = fetch_sidra_6463()
    official = parse_sidra_6463(payload)
    if len(official) != 57:
        raise RuntimeError(f"SIDRA table 6463 has {len(official)} quarters; expected 57.")

    micro = run_bq_csv(build_reference_population_query(), maximum_rows=100)
    for column in micro.columns:
        micro[column] = pd.to_numeric(micro[column], errors="raise")
    ftp_records = [
        {
            "ano": year,
            "trimestre": quarter,
            **ftp_reconciliation(year, quarter),
        }
        for year, quarter in sorted(OFFICIAL_FTP_PERIODS)
    ]
    ftp_period_ids = {
        year * 10 + quarter
        for year, quarter in OFFICIAL_FTP_PERIODS
    }
    micro_period_ids = (
        micro["ano"].astype(int) * 10 + micro["trimestre"].astype(int)
    )
    micro = micro.loc[~micro_period_ids.isin(ftp_period_ids)].copy()
    micro = pd.concat([micro, pd.DataFrame(ftp_records)], ignore_index=True)
    micro = micro.sort_values(["ano", "trimestre"]).reset_index(drop=True)
    if len(micro) != 57:
        raise RuntimeError(f"Microdata reconciliation has {len(micro)} quarters; expected 57.")

    merged = audited_merge(
        official,
        micro,
        merge_id="pnadc_reconciliation_sidra_microdata",
        on=["ano", "trimestre"],
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != 57:
        raise RuntimeError("SIDRA and microdata period grids do not match.")
    merged["population_14plus_difference"] = (
        merged["bq_population_14plus"] - merged["sidra_population_14plus"]
    )
    merged["population_14plus_relative_difference"] = (
        merged["population_14plus_difference"] / merged["sidra_population_14plus"]
    )
    merged["population_14plus_absolute_relative_difference"] = merged[
        "population_14plus_relative_difference"
    ].abs()
    merged["occupied_14plus_difference"] = (
        merged["bq_occupied_population_14plus"]
        - merged["sidra_occupied_14plus"]
    )
    merged["occupied_14plus_relative_difference"] = (
        merged["occupied_14plus_difference"]
        / merged["sidra_occupied_14plus"]
    )
    merged["occupied_14plus_absolute_relative_difference"] = merged[
        "occupied_14plus_relative_difference"
    ].abs()

    anchor_frame = pd.read_parquet(VINTAGE_DIR / "pnadc_2025q3.parquet")
    anchor = section3_anchor(anchor_frame)
    anchor_rows_match = int(anchor["rows"]) == SECTION3_EXPECTED_ROWS
    anchor_population_match = (
        abs(float(anchor["population"]) - SECTION3_EXPECTED_POPULATION) <= 1e-6
    )
    official_match = bool(
        merged[
            [
                "population_14plus_absolute_relative_difference",
                "occupied_14plus_absolute_relative_difference",
            ]
        ]
        .le(0.01)
        .all()
        .all()
    )

    atomic_csv(merged, RECONCILIATION_PATH)
    atomic_text(
        _reconciliation_markdown(
            merged,
            anchor_rows=int(anchor["rows"]),
            anchor_population=float(anchor["population"]),
        ),
        RECONCILIATION_REPORT_PATH,
    )
    status = {
        "anchor_population": float(anchor["population"]),
        "anchor_population_match_1e_6": anchor_population_match,
        "anchor_rows": int(anchor["rows"]),
        "anchor_rows_match": anchor_rows_match,
        "maximum_occupied_14plus_absolute_relative_difference": float(
            merged["occupied_14plus_absolute_relative_difference"].max()
        ),
        "maximum_population_14plus_absolute_relative_difference": float(
            merged["population_14plus_absolute_relative_difference"].max()
        ),
        "official_reconciliation_within_1pct": official_match,
        "sidra_accessed_at": accessed_at,
        "sidra_sha256": sha256_file(SIDRA_VINTAGE_PATH),
        "status": (
            "pass"
            if official_match and anchor_rows_match and anchor_population_match
            else "fail"
        ),
        "quarters": int(len(merged)),
    }
    atomic_json(status, RECONCILIATION_STATUS_PATH)
    return status


def diagnose_crosswalk() -> dict[str, Any]:
    """Execute P3 coverage without constructing a COD4 cell."""
    observed_hash = sha256_file(ILO_PATH)
    if observed_hash != ILO_EXPECTED_SHA256:
        raise RuntimeError(
            "ILO workbook SHA-256 mismatch: "
            f"expected {ILO_EXPECTED_SHA256}, observed {observed_hash}"
        )
    crosswalk = build_ilo_crosswalk(pd.read_excel(ILO_PATH))
    records: list[dict[str, Any]] = []
    for year, quarter in expected_periods():
        frame = pd.read_parquet(
            VINTAGE_DIR / f"pnadc_{year}q{quarter}.parquet"
        )
        matched = attach_crosswalk(frame, crosswalk)
        total_rows = int(len(matched))
        total_population = float(
            pd.to_numeric(matched["peso"], errors="coerce").sum()
        )
        grouped = (
            matched.groupby("match_type", dropna=False)
            .agg(
                observations=("cod4", "size"),
                weighted_population=("peso", "sum"),
            )
            .reset_index()
        )
        for row in grouped.itertuples(index=False):
            records.append(
                {
                    "ano": year,
                    "trimestre": quarter,
                    "periodo": f"{year}Q{quarter}",
                    "match_type": str(row.match_type),
                    "observations": int(row.observations),
                    "weighted_population": float(row.weighted_population),
                    "observation_share": (
                        float(row.observations) / total_rows
                        if total_rows
                        else float("nan")
                    ),
                    "population_share": (
                        float(row.weighted_population) / total_population
                        if total_population
                        else float("nan")
                    ),
                    "estimation_eligible": (
                        str(row.match_type) == "exact_4_digit"
                    ),
                }
            )
    coverage = pd.DataFrame(records).sort_values(
        ["ano", "trimestre", "match_type"]
    )
    anchor = coverage.loc[
        coverage["ano"].eq(2025)
        & coverage["trimestre"].eq(3)
        & coverage["match_type"].eq("exact_4_digit")
    ].iloc[0]
    exact_rows_percent = 100.0 * float(anchor["observation_share"])
    exact_population_percent = 100.0 * float(anchor["population_share"])
    atomic_csv(coverage, CROSSWALK_COVERAGE_PATH)
    report = f"""# PNADc COD--ISCO-08 crosswalk

## Rule

The frozen ILO file was verified with SHA-256
`{observed_hash}`. Each PNADc observation has its occupation code normalized to four digits, but no
COD4 cell is formed. Only an exact four-digit match inherits `potential25`. Three-, two-, and
one-digit fallbacks and unmatched codes receive `Sem classificação` and are excluded from the
estimation sample.

This rule avoids conflict with `mte_official_no_numeric_fallback`: fallbacks are measured for
coverage but never receive a numerical or categorical gradient.

## Coverage in 2025Q3

- Exact match, unweighted: {exact_rows_percent:.6f}%.
- Exact match, weighted: {exact_population_percent:.6f}%.
- Section 3 reference: approximately 97.9% on the unweighted indicator.

The diagnostic measures crosswalk coverage and estimates no treatment coefficient. The design
measures formal--informal composition, not individual worker transitions.
"""
    atomic_text(report, CROSSWALK_REPORT_PATH)
    status = {
        "anchor_2025q3_exact_observation_share": float(
            anchor["observation_share"]
        ),
        "anchor_2025q3_exact_population_share": float(
            anchor["population_share"]
        ),
        "ilo_sha256": observed_hash,
        "quarters": int(coverage[["ano", "trimestre"]].drop_duplicates().shape[0]),
        "sem_classificacao_estimation_eligible": False,
        "status": "pass",
    }
    atomic_json(status, CROSSWALK_STATUS_PATH)
    return status


def _cell_support_records(
    cells: pd.DataFrame,
    *,
    arm: str,
    group_column: str,
    treated_label: str,
    control_label: str,
    arm_status: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for group in (treated_label, control_label):
        subset = cells.loc[cells[group_column].eq(group)].copy()
        clusters = int(subset["cod3"].nunique())
        observed_cells = int(len(subset))
        expected_cells = clusters * 57
        missing_cells = expected_cells - observed_cells
        observations = subset["observations"].astype(float)
        records.append(
            {
                "arm": arm,
                "group": (
                    "treated" if group == treated_label else "control"
                ),
                "cod3_clusters": clusters,
                "observed_cod3_quarter_cells": observed_cells,
                "expected_cod3_quarter_cells": expected_cells,
                "missing_cod3_quarter_cells": missing_cells,
                "minimum_observations_observed_cell": (
                    float(observations.min()) if observed_cells else float("nan")
                ),
                "p10_observations_observed_cell": (
                    float(observations.quantile(0.10))
                    if observed_cells
                    else float("nan")
                ),
                "median_observations_observed_cell": (
                    float(observations.median())
                    if observed_cells
                    else float("nan")
                ),
                "minimum_observations_complete_grid": (
                    0.0
                    if missing_cells > 0
                    else (
                        float(observations.min())
                        if observed_cells
                        else float("nan")
                    )
                ),
                "support_status": arm_status,
            }
        )
    return records


def diagnose_support() -> dict[str, Any]:
    """Execute P4 and publish COD3 support before any coefficient."""
    observed_hash = sha256_file(ILO_PATH)
    if observed_hash != ILO_EXPECTED_SHA256:
        raise RuntimeError("ILO workbook changed before P4.")
    crosswalk = build_ilo_crosswalk(pd.read_excel(ILO_PATH))
    pre_summaries: list[pd.DataFrame] = []
    pre_cod4_pairs: list[pd.DataFrame] = []
    arm_a_cells: list[pd.DataFrame] = []
    arm_b_cells: list[pd.DataFrame] = []

    for year, quarter in expected_periods():
        frame = pd.read_parquet(
            VINTAGE_DIR / f"pnadc_{year}q{quarter}.parquet"
        )
        matched = attach_crosswalk(frame, crosswalk)
        matched["cod3"] = matched["cod4"].str[:3]
        matched["periodo"] = f"{year}Q{quarter}"
        exact = matched.loc[
            matched["match_type"].eq("exact_4_digit")
        ].copy()

        if (year, quarter) <= (2022, 3):
            exact["peso_numeric"] = pd.to_numeric(
                exact["peso"],
                errors="raise",
            )
            exact["exposed_weight"] = exact["peso_numeric"].where(
                exact["exposure_gradient"]
                .astype("string")
                .str.startswith("Exposed:"),
                0.0,
            )
            pre_summaries.append(
                exact.groupby("cod3", as_index=False).agg(
                    total_employment_weight=("peso_numeric", "sum"),
                    exposed_employment_weight=("exposed_weight", "sum"),
                    pre_observations=("cod4", "size"),
                )
            )
            pre_cod4_pairs.append(exact[["cod3", "cod4"]].drop_duplicates())

        estimation_gradients = exact.loc[
            exact["exposure_gradient"]
            .astype("string")
            .str.startswith("Exposed:")
            | exact["exposure_gradient"].eq("Not Exposed")
        ].copy()
        estimation_gradients["arm_a_group"] = "control"
        estimation_gradients.loc[
            estimation_gradients["exposure_gradient"]
            .astype("string")
            .str.startswith("Exposed:"),
            "arm_a_group",
        ] = "treated"
        arm_a_cells.append(
            estimation_gradients.groupby(
                ["arm_a_group", "cod3", "periodo"],
                as_index=False,
            ).agg(observations=("cod4", "size"))
        )
        arm_b_cells.append(
            estimation_gradients.groupby(
                ["cod3", "periodo"],
                as_index=False,
            ).agg(observations=("cod4", "size"))
        )

    pre_summary = (
        pd.concat(pre_summaries, ignore_index=True)
        .groupby("cod3", as_index=False)
        .agg(
            total_employment_weight=("total_employment_weight", "sum"),
            exposed_employment_weight=("exposed_employment_weight", "sum"),
            pre_observations=("pre_observations", "sum"),
        )
    )
    cod4_counts = (
        pd.concat(pre_cod4_pairs, ignore_index=True)
        .drop_duplicates()
        .groupby("cod3", as_index=False)
        .agg(exact_cod4_count=("cod4", "nunique"))
    )
    treatment = audited_merge(
        pre_summary,
        cod4_counts,
        merge_id="pnadc_attach_preperiod_exact_cod4_counts",
        on="cod3",
        how="left",
        validate="one_to_one",
    )
    treatment = _assign_cod3_treatment_status(treatment)
    treatment = treatment[
        [
            "cod3",
            "total_employment_weight",
            "exposed_employment_weight",
            "exposed_employment_share",
            "pre_observations",
            "exact_cod4_count",
            "treatment_status",
            "treated_cod3",
        ]
    ].sort_values("cod3")

    arm_a = pd.concat(arm_a_cells, ignore_index=True)
    arm_a_counts = arm_a.groupby("arm_a_group")["cod3"].nunique()
    arm_a_treated = int(arm_a_counts.get("treated", 0))
    arm_a_control = int(arm_a_counts.get("control", 0))
    arm_a_status = classify_support(arm_a_treated, arm_a_control)

    arm_b = audited_merge(
        pd.concat(arm_b_cells, ignore_index=True),
        treatment[["cod3", "treatment_status"]],
        merge_id="pnadc_attach_cod3_treatment_to_support_cells",
        on="cod3",
        how="left",
        validate="many_to_one",
    )
    arm_b = arm_b.loc[
        arm_b["treatment_status"].isin(["treated", "control"])
    ].copy()
    arm_b_counts = arm_b.groupby("treatment_status")["cod3"].nunique()
    arm_b_treated = int(arm_b_counts.get("treated", 0))
    arm_b_control = int(arm_b_counts.get("control", 0))
    arm_b_status = classify_support(arm_b_treated, arm_b_control)

    support_records = [
        *_cell_support_records(
            arm_a,
            arm="A_individual",
            group_column="arm_a_group",
            treated_label="treated",
            control_label="control",
            arm_status=arm_a_status,
        ),
        *_cell_support_records(
            arm_b,
            arm="B_cod3_stock",
            group_column="treatment_status",
            treated_label="treated",
            control_label="control",
            arm_status=arm_b_status,
        ),
    ]
    support = pd.DataFrame(support_records)
    treatment_counts = treatment["treatment_status"].value_counts()
    treated_cod3 = int(treatment_counts.get("treated", 0))
    control_cod3 = int(treatment_counts.get("control", 0))
    intermediate_cod3 = int(treatment_counts.get("intermediate", 0))

    atomic_csv(treatment, TREATMENT_COD3_PATH)
    atomic_csv(support, SUPPORT_PATH)
    report = f"""# PNADc support by COD3

## Rule published before coefficients

COD3 treatment uses the pre-period (2012Q1--2022Q3) employment-weighted mean of the exposure
indicator among exact matches: treated if the mean is at least 0.50, control if it is exactly zero,
and intermediate if it falls between those values. No COD4 cell is formed.

## Counts

- Arm B COD3 rule: {treated_cod3} treated, {control_cod3} control, and
  {intermediate_cod3} excluded intermediate COD3 groups.
- Individual Arm A: {arm_a_treated} COD3 groups with exposed observations and {arm_a_control} COD3
  groups with `Not Exposed` observations; support is `{arm_a_status}`.
- Stock Arm B: {arm_b_treated} treated and {arm_b_control} control COD3 groups; support is
  `{arm_b_status}`.

The cell statistics in `pnadc_support.csv` cover all 57 acquisition quarters. Quarter 2022Q4 remains
defined as the transition period and will only be excluded during panel construction, after this
gate. Support was published before any treatment coefficient.

The design measures formal--informal composition, not individual worker transitions.
"""
    atomic_text(report, SUPPORT_REPORT_PATH)
    both_thin = arm_a_status == "thin" and arm_b_status == "thin"
    status = {
        "arm_a_control_cod3": arm_a_control,
        "arm_a_support_status": arm_a_status,
        "arm_a_treated_cod3": arm_a_treated,
        "arm_b_control_cod3": arm_b_control,
        "arm_b_support_status": arm_b_status,
        "arm_b_treated_cod3": arm_b_treated,
        "both_arms_thin": both_thin,
        "cod3_control": control_cod3,
        "cod3_intermediate": intermediate_cod3,
        "cod3_treated": treated_cod3,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "status": "fail" if both_thin else "pass",
        "treatment_coefficients_computed": False,
    }
    atomic_json(status, SUPPORT_STATUS_PATH)
    return status


def _append_distribution_records(
    records: list[dict[str, Any]],
    frame: pd.DataFrame,
    *,
    year: int,
    quarter: int,
    group: str,
    domain: str,
    column: str,
) -> None:
    weights = pd.to_numeric(frame["peso"], errors="raise")
    categories = frame[column].astype("string").fillna("<missing>")
    total = float(weights.sum())
    grouped = (
        pd.DataFrame({"category": categories, "weight": weights})
        .groupby("category", as_index=False)
        .agg(weight=("weight", "sum"))
    )
    for row in grouped.itertuples(index=False):
        category = str(row.category)
        records.append(
            {
                "ano": year,
                "trimestre": quarter,
                "periodo": f"{year}Q{quarter}",
                "group": group,
                "domain": domain,
                "category": category,
                "metric": f"{domain}_share_{category}",
                "unit": "percentage_points",
                "raw_value": (
                    100.0 * float(row.weight) / total
                    if total > 0
                    else float("nan")
                ),
            }
        )


def diagnose_2020_break() -> dict[str, Any]:
    """Execute the P5 coverage/composition break diagnostic only."""
    observed_hash = sha256_file(ILO_PATH)
    if observed_hash != ILO_EXPECTED_SHA256:
        raise RuntimeError("ILO workbook changed before P5.")
    crosswalk = build_ilo_crosswalk(pd.read_excel(ILO_PATH))
    records: list[dict[str, Any]] = []
    periods = [
        (year, quarter)
        for year in range(2019, 2022)
        for quarter in range(1, 5)
    ]
    for year, quarter in periods:
        frame = pd.read_parquet(
            VINTAGE_DIR / f"pnadc_{year}q{quarter}.parquet"
        )
        matched = attach_crosswalk(frame, crosswalk)
        exact = matched.loc[
            matched["match_type"].eq("exact_4_digit")
            & (
                matched["exposure_gradient"]
                .astype("string")
                .str.startswith("Exposed:")
                | matched["exposure_gradient"].eq("Not Exposed")
            )
        ].copy()
        exact["break_group"] = "control"
        exact.loc[
            exact["exposure_gradient"]
            .astype("string")
            .str.startswith("Exposed:"),
            "break_group",
        ] = "treated"
        exact["formal"] = formal_indicator(
            exact["posicao_ocupacao"]
        ).map(
            {True: "formal", False: "informal"}
        )

        for group in ("treated", "control"):
            subset = exact.loc[exact["break_group"].eq(group)].copy()
            weights = pd.to_numeric(subset["peso"], errors="raise")
            base = {
                "ano": year,
                "trimestre": quarter,
                "periodo": f"{year}Q{quarter}",
                "group": group,
                "category": "all",
            }
            records.extend(
                [
                    {
                        **base,
                        "domain": "coverage",
                        "metric": "effective_observations",
                        "unit": "index_2019_mean_100",
                        "raw_value": float(len(subset)),
                    },
                    {
                        **base,
                        "domain": "coverage",
                        "metric": "weighted_population",
                        "unit": "index_2019_mean_100",
                        "raw_value": float(weights.sum()),
                    },
                ]
            )
            _append_distribution_records(
                records,
                subset,
                year=year,
                quarter=quarter,
                group=group,
                domain="sex",
                column="sexo",
            )
            _append_distribution_records(
                records,
                subset,
                year=year,
                quarter=quarter,
                group=group,
                domain="education",
                column="nivel_instrucao",
            )
            _append_distribution_records(
                records,
                subset,
                year=year,
                quarter=quarter,
                group=group,
                domain="formality",
                column="formal",
            )

    observed = pd.DataFrame(records)
    metric_definitions = observed[
        ["domain", "category", "metric", "unit"]
    ].drop_duplicates()
    template_records: list[dict[str, Any]] = []
    for year, quarter in periods:
        for group in ("treated", "control"):
            for definition in metric_definitions.itertuples(index=False):
                template_records.append(
                    {
                        "ano": year,
                        "trimestre": quarter,
                        "periodo": f"{year}Q{quarter}",
                        "group": group,
                        "domain": str(definition.domain),
                        "category": str(definition.category),
                        "metric": str(definition.metric),
                        "unit": str(definition.unit),
                    }
                )
    template = pd.DataFrame(template_records)
    metrics = audited_merge(
        template,
        observed,
        merge_id="pnadc_complete_2020_break_metric_grid",
        on=[
            "ano",
            "trimestre",
            "periodo",
            "group",
            "domain",
            "category",
            "metric",
            "unit",
        ],
        how="left",
        validate="one_to_one",
    )
    share_metric = metrics["unit"].eq("percentage_points")
    metrics.loc[share_metric, "raw_value"] = metrics.loc[
        share_metric,
        "raw_value",
    ].fillna(0.0)
    metrics["normalized_value"] = metrics["raw_value"]
    coverage_metric = metrics["unit"].eq("index_2019_mean_100")
    for key, positions in metrics.loc[coverage_metric].groupby(
        ["group", "metric"]
    ).groups.items():
        subset = metrics.loc[positions]
        baseline = float(subset.loc[subset["ano"].eq(2019), "raw_value"].mean())
        metrics.loc[positions, "normalized_value"] = (
            100.0 * subset["raw_value"] / baseline
            if baseline > 0
            else float("nan")
        )

    keys = [
        "ano",
        "trimestre",
        "periodo",
        "domain",
        "category",
        "metric",
        "unit",
    ]
    treated = metrics.loc[
        metrics["group"].eq("treated"),
        [*keys, "raw_value", "normalized_value"],
    ].rename(
        columns={
            "raw_value": "treated_raw_value",
            "normalized_value": "treated_value",
        }
    )
    control = metrics.loc[
        metrics["group"].eq("control"),
        [*keys, "raw_value", "normalized_value"],
    ].rename(
        columns={
            "raw_value": "control_raw_value",
            "normalized_value": "control_value",
        }
    )
    comparison = audited_merge(
        treated,
        control,
        merge_id="pnadc_pair_2020_break_groups",
        on=keys,
        how="inner",
        validate="one_to_one",
    )
    comparison["treated_control_difference"] = (
        comparison["treated_value"] - comparison["control_value"]
    )
    metric_keys = ["domain", "category", "metric", "unit"]
    baseline = (
        comparison.loc[comparison["ano"].eq(2019)]
        .groupby(metric_keys, as_index=False)
        .agg(
            baseline_2019_treated_control_gap=(
                "treated_control_difference",
                "mean",
            )
        )
    )
    phone_window = (
        comparison.loc[
            comparison.apply(
                lambda row: (2020, 2)
                <= (int(row["ano"]), int(row["trimestre"]))
                <= (2021, 2),
                axis=1,
            )
        ]
        .groupby(metric_keys, as_index=False)
        .agg(
            telephone_window_treated_control_gap=(
                "treated_control_difference",
                "mean",
            )
        )
    )
    comparison = audited_merge(
        comparison,
        baseline,
        merge_id="pnadc_attach_2019_break_baseline",
        on=metric_keys,
        how="left",
        validate="many_to_one",
    )
    comparison = audited_merge(
        comparison,
        phone_window,
        merge_id="pnadc_attach_telephone_break_gap",
        on=metric_keys,
        how="left",
        validate="many_to_one",
    )
    comparison["telephone_minus_baseline_gap"] = (
        comparison["telephone_window_treated_control_gap"]
        - comparison["baseline_2019_treated_control_gap"]
    )
    comparison["differential_above_1pp"] = comparison[
        "telephone_minus_baseline_gap"
    ].abs().gt(1.0)

    unique_metrics = comparison[
        [*metric_keys, "telephone_minus_baseline_gap"]
    ].drop_duplicates()
    complete = bool(
        comparison[["treated_value", "control_value"]].notna().all().all()
        and comparison.groupby(metric_keys)["periodo"].nunique().eq(12).all()
    )
    classification = classify_2020_break(
        unique_metrics["telephone_minus_baseline_gap"],
        complete=complete,
    )
    maximum_index = unique_metrics[
        "telephone_minus_baseline_gap"
    ].abs().idxmax()
    maximum = unique_metrics.loc[maximum_index]

    atomic_csv(
        comparison.sort_values(
            ["domain", "category", "ano", "trimestre"]
        ),
        BREAK_2020_PATH,
    )
    report = f"""# 2020 collection-break diagnostic

## Contract

The diagnostic compares the exposed--control gap in individual Arm A between the 2019 average and
the exclusively telephone collection window, 2020Q2--2021Q2. Effective counts and weighted
population are indices with a 2019 mean of 100 within each group. Sex, education, and formality are
weighted percentage-point distributions. An absolute gap change above 1 point classifies the break
as differential.

## Result

- Classification: `{classification}`.
- Complete grid: `{str(complete).lower()}`.
- Largest absolute gap change: {abs(float(maximum["telephone_minus_baseline_gap"])):.6f} points.
- Metric with the largest change: `{maximum["metric"]}` (category `{maximum["category"]}`).

This is a descriptive coverage and composition diagnostic. No treatment coefficient was estimated.
The design measures formal--informal composition, not individual worker transitions. The
sensitivity excluding 2020 remains mandatory if the front proceeds.
"""
    atomic_text(report, BREAK_2020_REPORT_PATH)
    status = {
        "classification": classification,
        "complete_metric_grid": complete,
        "maximum_absolute_gap_change_pp": abs(
            float(maximum["telephone_minus_baseline_gap"])
        ),
        "maximum_gap_change_category": str(maximum["category"]),
        "maximum_gap_change_metric": str(maximum["metric"]),
        "metrics": int(len(unique_metrics)),
        "periods": 12,
        "status": "pass",
        "treatment_coefficients_computed": False,
    }
    atomic_json(status, BREAK_2020_STATUS_PATH)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the preregistered PNADc Stage 0.",
    )
    parser.add_argument(
        "task",
        choices=("acquire", "reconcile", "crosswalk", "support", "break-2020"),
        help="Stage 0 task to execute.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.task == "acquire":
        print(json.dumps(acquire_vintage(), indent=2, sort_keys=True))
    elif args.task == "reconcile":
        print(json.dumps(reconcile_vintage(), indent=2, sort_keys=True))
    elif args.task == "crosswalk":
        print(json.dumps(diagnose_crosswalk(), indent=2, sort_keys=True))
    elif args.task == "support":
        print(json.dumps(diagnose_support(), indent=2, sort_keys=True))
    elif args.task == "break-2020":
        print(json.dumps(diagnose_2020_break(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
