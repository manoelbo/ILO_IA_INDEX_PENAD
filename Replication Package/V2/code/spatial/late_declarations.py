#!/usr/bin/env python3
"""Build the Anatel Stage 0 late-declaration diagnostic from signed V2 data."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
FRONT_ROOT = Path(__file__).resolve().parents[1]
MOVEMENTS_GLOB = (
    V2_ROOT
    / "data"
    / "interim"
    / "movimentacoes"
    / "competenciamov=*"
    / "part.parquet"
)
DEFAULT_OUTPUT = (
    FRONT_ROOT
    / "results"
    / "anatel_late_declaration_by_municipality.csv"
)
DEFAULT_SUPPORT = (
    FRONT_ROOT
    / "results"
    / "anatel_late_declaration_support.json"
)
KNOWN_NATIONAL_SHARES = {2021: 0.0861, 2024: 0.0129}

module_paths = (
    V2_ROOT / "code" / "caged" / "models",
    V2_ROOT / "code" / "caged" / "panel",
    V2_ROOT / "code" / "common",
)
for path in module_paths:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_panel import _configure_connection  # noqa: E402
from paths import portable_path  # noqa: E402
from pretrend_engine import atomic_csv, atomic_json  # noqa: E402


def aggregate_late_declarations(movements: pd.DataFrame) -> pd.DataFrame:
    """Aggregate signed MOV/FOR/EXC counts by municipality and year."""
    municipality_column = (
        "municipio_caged_6d"
        if "municipio_caged_6d" in movements.columns
        else "municipio"
    )
    required = {
        municipality_column,
        "ano",
        "origem",
        "peso",
        "indicadordeforadoprazo",
    }
    missing = sorted(required - set(movements.columns))
    if missing:
        raise ValueError(f"Late-declaration data is missing columns: {missing}")
    data = movements.copy()
    data["origem"] = data["origem"].astype(str).str.upper()
    data["peso"] = pd.to_numeric(data["peso"], errors="raise")
    data["_mov"] = data["peso"].where(data["origem"].eq("MOV"), 0)
    data["_for"] = data["peso"].where(data["origem"].eq("FOR"), 0)
    data["_exc"] = data["peso"].where(data["origem"].eq("EXC"), 0)
    data["_flag"] = data["peso"].where(
        data["indicadordeforadoprazo"].astype(str).eq("1"),
        0,
    )
    grouped = (
        data.groupby([municipality_column, "ano"], observed=True)
        .agg(
            mov_liquido=("_mov", "sum"),
            for_liquido=("_for", "sum"),
            exc_liquido=("_exc", "sum"),
            flag_liquido=("_flag", "sum"),
            total_liquido=("peso", "sum"),
        )
        .reset_index()
    )
    analytic_denominator = grouped["mov_liquido"] + grouped["for_liquido"]
    grouped["share_for"] = grouped["for_liquido"] / analytic_denominator.where(
        analytic_denominator.ne(0)
    )
    grouped["share_flag"] = grouped["flag_liquido"] / grouped[
        "total_liquido"
    ].where(grouped["total_liquido"].ne(0))
    return grouped.sort_values(
        [municipality_column, "ano"]
    ).reset_index(drop=True)


def national_from_municipal(municipal: pd.DataFrame) -> pd.DataFrame:
    totals = (
        municipal.groupby("ano", observed=True)[
            [
                "mov_liquido",
                "for_liquido",
                "exc_liquido",
                "flag_liquido",
                "total_liquido",
            ]
        ]
        .sum()
        .reset_index()
    )
    denominator = totals["mov_liquido"] + totals["for_liquido"]
    totals["share_for"] = totals["for_liquido"] / denominator.where(
        denominator.ne(0)
    )
    totals["share_flag"] = totals["flag_liquido"] / totals[
        "total_liquido"
    ].where(totals["total_liquido"].ne(0))
    return totals


def validate_national_benchmarks(
    national: pd.DataFrame,
    *,
    tolerance_percentage_points: float,
) -> dict[str, Any]:
    by_year = national.set_index("ano")
    audit: dict[str, Any] = {"years": {}}
    all_within = True
    for year, expected in KNOWN_NATIONAL_SHARES.items():
        if year not in by_year.index:
            raise RuntimeError(f"National late-declaration share missing {year}")
        observed = float(by_year.loc[year, "share_for"])
        difference_pp = abs(observed - expected) * 100
        within = difference_pp <= tolerance_percentage_points
        audit["years"][str(year)] = {
            "expected_share": expected,
            "observed_share": observed,
            "absolute_difference_percentage_points": difference_pp,
            "within_tolerance": bool(within),
        }
        all_within = all_within and within
    audit["tolerance_percentage_points"] = tolerance_percentage_points
    audit["all_within_tolerance"] = bool(all_within)
    return audit


def _aggregate_from_parquet(
    movements_glob: Path,
) -> tuple[pd.DataFrame, int]:
    source = str(movements_glob).replace("'", "''")
    with tempfile.TemporaryDirectory(prefix="anatel-a2-") as scratch:
        connection = duckdb.connect()
        try:
            _configure_connection(connection, Path(scratch))
            connection.execute(
                f"""
                CREATE TEMP VIEW valid AS
                SELECT
                    CAST(municipio AS VARCHAR) AS municipio_caged_6d,
                    CAST(floor(CAST(competenciamov AS INTEGER) / 100)
                         AS INTEGER) AS ano,
                    upper(CAST(origem AS VARCHAR)) AS origem,
                    CAST(peso AS BIGINT) AS peso,
                    CAST(indicadordeforadoprazo AS VARCHAR)
                        AS indicadordeforadoprazo
                FROM read_parquet(
                    '{source}',
                    hive_partitioning = true,
                    union_by_name = true
                )
                WHERE regexp_full_match(
                          CAST(cbo2002ocupacao AS VARCHAR),
                          '[0-9]{{4,6}}'
                      )
                  AND substring(CAST(cbo2002ocupacao AS VARCHAR), 1, 4)
                      <> '0000'
                  AND CAST(idade AS DOUBLE) BETWEEN 14 AND 90
                  AND CAST(salario AS DOUBLE) > 0.0
                  AND CAST(salario AS DOUBLE) < 1000000.0
                  AND CAST(saldomovimentacao AS INTEGER) IN (-1, 1)
                  AND CAST(peso AS INTEGER) IN (-1, 1)
                """
            )
            valid_records = int(
                connection.execute("SELECT count(*) FROM valid").fetchone()[0]
            )
            municipal = connection.execute(
                """
                WITH totals AS (
                    SELECT
                        municipio_caged_6d,
                        ano,
                        sum(CASE WHEN origem = 'MOV' THEN peso ELSE 0 END)
                            AS mov_liquido,
                        sum(CASE WHEN origem = 'FOR' THEN peso ELSE 0 END)
                            AS for_liquido,
                        sum(CASE WHEN origem = 'EXC' THEN peso ELSE 0 END)
                            AS exc_liquido,
                        sum(CASE
                            WHEN indicadordeforadoprazo = '1' THEN peso
                            ELSE 0
                        END) AS flag_liquido,
                        sum(peso) AS total_liquido
                    FROM valid
                    GROUP BY municipio_caged_6d, ano
                )
                SELECT
                    *,
                    for_liquido
                        / nullif(mov_liquido + for_liquido, 0)
                        AS share_for,
                    flag_liquido / nullif(total_liquido, 0)
                        AS share_flag
                FROM totals
                ORDER BY municipio_caged_6d, ano
                """
            ).df()
            return municipal, valid_records
        finally:
            connection.close()


def run_a2(
    *,
    movements_glob: Path = MOVEMENTS_GLOB,
    output_path: Path = DEFAULT_OUTPUT,
    support_path: Path = DEFAULT_SUPPORT,
    acknowledge_incompatible_benchmark: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    municipal, valid_records = _aggregate_from_parquet(movements_glob)
    national = national_from_municipal(municipal)
    benchmark = validate_national_benchmarks(
        national,
        tolerance_percentage_points=0.01,
    )
    support = {
        "status": (
            "pass"
            if benchmark["all_within_tolerance"]
            else (
                "completed_benchmark_incompatible"
                if acknowledge_incompatible_benchmark
                else "fail_reconciliation"
            )
        ),
        "source": portable_path(movements_glob, relative_to=V2_ROOT),
        "valid_records": valid_records,
        "municipality_year_rows": int(len(municipal)),
        "municipalities": int(
            municipal["municipio_caged_6d"].nunique()
        ),
        "years": sorted(int(value) for value in municipal["ano"].unique()),
        "national": json.loads(national.to_json(orient="records")),
        "benchmark": benchmark,
        "benchmark_incompatibility_acknowledged": bool(
            acknowledge_incompatible_benchmark
        ),
        "benchmark_investigation": (
            "The legacy 8.61% benchmark mixes declaration-year and "
            "fact-month axes. The registered construct therefore uses "
            "the signed fact-month definition without modifying the "
            "incompatible benchmark."
        ),
        "treatment_coefficient_estimated": False,
    }
    atomic_csv(municipal, output_path)
    atomic_json(support, support_path)
    if (
        not benchmark["all_within_tolerance"]
        and not acknowledge_incompatible_benchmark
    ):
        raise RuntimeError(
            "A2 national late-declaration shares failed reconciliation"
        )
    return municipal, support


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--movements-glob", type=Path, default=MOVEMENTS_GLOB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument(
        "--acknowledge-incompatible-benchmark",
        action="store_true",
    )
    args = parser.parse_args()
    _, support = run_a2(
        movements_glob=args.movements_glob,
        output_path=args.output,
        support_path=args.support,
        acknowledge_incompatible_benchmark=(
            args.acknowledge_incompatible_benchmark
        ),
    )
    print(json.dumps(support, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
