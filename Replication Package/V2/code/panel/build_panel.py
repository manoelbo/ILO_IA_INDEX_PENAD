#!/usr/bin/env python3
"""Build the signed national CBO4-by-month analytic panel."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import requests


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
DEFAULT_SCRATCH_PARENT = PACKAGE_ROOT / "data" / "interim"

IPCA_SERIES = 433
IPCA_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    "?formato=json&dataInicial=01/01/2021&dataFinal=31/05/2026"
)
START_PERIOD = 202101
END_PERIOD = 202605
IPCA_BASE_PERIOD = "202412"
WAGE_MIN = 0.0
WAGE_MAX = 1_000_000.0

COMPOSITION_BASES = (
    "idade_media",
    "pct_mulher",
    "pct_superior",
    "pct_negra",
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
            racacor
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
        """
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
                     AND graudeinstrucao IN ('9', '10', '11', '80')
                    THEN peso ELSE 0
                END) AS superior_soma_adm,
                sum(CASE
                    WHEN movimento = -1
                     AND graudeinstrucao IN ('9', '10', '11', '80')
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
    out = panel.merge(
        ipca[["periodo_num", "indice"]],
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
    out = out.merge(
        classes,
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
        choices=("freeze-ipca", "build", "all"),
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command in {"freeze-ipca", "all"}:
        print(json.dumps(freeze_ipca(), sort_keys=True))
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
