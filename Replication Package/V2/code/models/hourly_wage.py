#!/usr/bin/env python3
"""Estimate hourly wage and work-schedule margins for Task 25."""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from estimators import fit_model


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MOVEMENTS = (
    PACKAGE_ROOT
    / "data"
    / "interim"
    / "movimentacoes"
    / "competenciamov=*"
    / "part.parquet"
)
DEFAULT_NATIONAL_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
)
DEFAULT_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_hourly_wage.parquet"
)
DEFAULT_RESULTS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "hourly_wage_results.csv"
)
DEFAULT_COVERAGE = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "hourly_wage_coverage.csv"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "hourly_wage_support.csv"
)
DEFAULT_STATUS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "hourly_wage_status.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT / "results" / "mechanisms" / "HOURLY_WAGE.md"
)
DEFAULT_SCRATCH = PACKAGE_ROOT / "data" / "interim"
START_PERIOD = 202101
END_PERIOD = 202605
MONTHLY_HOURS_MULTIPLIER = 5.0
OUTCOMES = (
    ("ln_salario_real_adm", "Log real monthly admission wage"),
    ("ln_salario_hora_real_adm", "Log real hourly admission wage"),
    ("ln_horas_semanais_adm", "Log weekly contracted admission hours"),
    ("pct_parcial_adm", "Partial-work admission share"),
    ("pct_intermitente_adm", "Intermittent-work admission share"),
)


def monthly_to_hourly_wage(
    monthly_wage: float,
    weekly_hours: float,
) -> float:
    if (
        not math.isfinite(monthly_wage)
        or not math.isfinite(weekly_hours)
        or monthly_wage <= 0
        or weekly_hours <= 0
    ):
        return math.nan
    return monthly_wage / (
        MONTHLY_HOURS_MULTIPLIER * weekly_hours
    )


def evaluate_hours_continuity(
    coverage_pct: pd.Series,
) -> dict[str, Any]:
    values = pd.to_numeric(coverage_pct, errors="raise")
    adjacent_break = bool(values.diff().abs().gt(10.0).any())
    low = values.lt(95.0).astype(int)
    three_low = bool(
        low.rolling(3, min_periods=3).sum().eq(3).any()
    )
    passed = not adjacent_break and not three_low
    return {
        "status": "pass" if passed else "fail",
        "minimum_coverage_pct": float(values.min()),
        "maximum_coverage_pct": float(values.max()),
        "maximum_adjacent_change_pp": float(
            values.diff().abs().max()
        ),
        "adjacent_change_above_10pp": adjacent_break,
        "three_consecutive_months_below_95pct": three_low,
    }


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranked = values[order] * len(values) / np.arange(
        1,
        len(values) + 1,
    )
    monotone = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted = np.empty_like(values)
    adjusted[order] = np.minimum(monotone, 1.0)
    return adjusted


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def aggregate_hourly_measures(
    movements_glob: Path,
    *,
    scratch_parent: Path = DEFAULT_SCRATCH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scratch_parent.mkdir(parents=True, exist_ok=True)
    source = _sql_literal(movements_glob)
    with tempfile.TemporaryDirectory(
        prefix="t25-duckdb-",
        dir=scratch_parent,
    ) as temporary:
        connection = duckdb.connect()
        try:
            connection.execute("SET threads = 1")
            connection.execute("SET memory_limit = '768MB'")
            connection.execute("SET preserve_insertion_order = false")
            connection.execute(
                f"SET temp_directory = {_sql_literal(temporary)}"
            )
            connection.execute(
                f"""
                CREATE TEMP VIEW valid_admissions AS
                SELECT
                    substring(
                        CAST(cbo2002ocupacao AS VARCHAR),
                        1,
                        4
                    ) AS cbo_4d,
                    CAST(competenciamov AS INTEGER) AS periodo_num,
                    CAST(floor(
                        CAST(competenciamov AS INTEGER) / 100
                    ) AS INTEGER) AS ano,
                    CAST(peso AS BIGINT) AS peso,
                    CAST(salario AS DOUBLE) AS salario,
                    CAST(horascontratuais AS DOUBLE) AS weekly_hours,
                    CAST(indtrabparcial AS VARCHAR) AS partial_code,
                    CAST(indtrabintermitente AS VARCHAR)
                        AS intermittent_code
                FROM read_parquet(
                    {source},
                    hive_partitioning = true,
                    union_by_name = true
                )
                WHERE CAST(competenciamov AS INTEGER)
                      BETWEEN {START_PERIOD} AND {END_PERIOD}
                  AND regexp_full_match(
                      CAST(cbo2002ocupacao AS VARCHAR),
                      '[0-9]{{4,6}}'
                  )
                  AND substring(
                      CAST(cbo2002ocupacao AS VARCHAR),
                      1,
                      4
                  ) <> '0000'
                  AND CAST(idade AS INTEGER) BETWEEN 14 AND 90
                  AND CAST(salario AS DOUBLE) > 0
                  AND CAST(salario AS DOUBLE) < 1000000
                  AND CAST(saldomovimentacao AS INTEGER) = 1
                  AND CAST(peso AS INTEGER) IN (-1, 1)
                """
            )
            connection.execute(
                f"""
                CREATE TEMP TABLE hourly_bounds AS
                SELECT
                    cbo_4d,
                    ano,
                    approx_quantile(
                        salario / ({MONTHLY_HOURS_MULTIPLIER}
                            * weekly_hours),
                        0.01
                    ) AS hourly_p01,
                    approx_quantile(
                        salario / ({MONTHLY_HOURS_MULTIPLIER}
                            * weekly_hours),
                        0.99
                    ) AS hourly_p99
                FROM valid_admissions
                WHERE peso = 1
                  AND weekly_hours > 0
                  AND weekly_hours <= 99
                GROUP BY cbo_4d, ano
                """
            )
            measures = connection.execute(
                f"""
                WITH enriched AS (
                    SELECT
                        admission.*,
                        CASE
                            WHEN weekly_hours > 0
                             AND weekly_hours <= 99
                            THEN greatest(
                                bounds.hourly_p01,
                                least(
                                    admission.salario
                                    / (
                                        {MONTHLY_HOURS_MULTIPLIER}
                                        * admission.weekly_hours
                                    ),
                                    bounds.hourly_p99
                                )
                            )
                        END AS hourly_wage
                    FROM valid_admissions AS admission
                    LEFT JOIN hourly_bounds AS bounds
                      USING (cbo_4d, ano)
                )
                SELECT
                    cbo_4d,
                    periodo_num,
                    CAST(sum(
                        CASE
                            WHEN weekly_hours > 0
                             AND weekly_hours <= 99
                            THEN peso ELSE 0
                        END
                    ) AS BIGINT) AS valid_hours_admissions,
                    sum(
                        CASE
                            WHEN weekly_hours > 0
                             AND weekly_hours <= 99
                            THEN peso * weekly_hours ELSE 0
                        END
                    ) AS weekly_hours_sum,
                    sum(
                        CASE
                            WHEN hourly_wage IS NOT NULL
                            THEN peso * hourly_wage ELSE 0
                        END
                    ) AS hourly_wage_sum,
                    CAST(sum(
                        CASE
                            WHEN partial_code IN ('0', '1')
                            THEN peso ELSE 0
                        END
                    ) AS BIGINT) AS partial_known,
                    CAST(sum(
                        CASE WHEN partial_code = '1'
                             THEN peso ELSE 0 END
                    ) AS BIGINT) AS partial_yes,
                    CAST(sum(
                        CASE
                            WHEN intermittent_code IN ('0', '1')
                            THEN peso ELSE 0
                        END
                    ) AS BIGINT) AS intermittent_known,
                    CAST(sum(
                        CASE WHEN intermittent_code = '1'
                             THEN peso ELSE 0 END
                    ) AS BIGINT) AS intermittent_yes,
                    CAST(sum(peso) AS BIGINT) AS total_admissions
                FROM enriched
                GROUP BY cbo_4d, periodo_num
                ORDER BY cbo_4d, periodo_num
                """
            ).df()
            coverage = connection.execute(
                """
                SELECT
                    periodo_num,
                    CAST(sum(peso) AS BIGINT) AS total_admissions,
                    CAST(sum(
                        CASE
                            WHEN weekly_hours > 0
                             AND weekly_hours <= 99
                            THEN peso ELSE 0
                        END
                    ) AS BIGINT) AS valid_hours_admissions,
                    CAST(sum(
                        CASE
                            WHEN partial_code IN ('0', '1')
                            THEN peso ELSE 0
                        END
                    ) AS BIGINT) AS partial_known,
                    CAST(sum(
                        CASE
                            WHEN intermittent_code IN ('0', '1')
                            THEN peso ELSE 0
                        END
                    ) AS BIGINT) AS intermittent_known
                FROM valid_admissions
                GROUP BY periodo_num
                ORDER BY periodo_num
                """
            ).df()
        finally:
            connection.close()
    for numerator in (
        "valid_hours_admissions",
        "partial_known",
        "intermittent_known",
    ):
        coverage[f"{numerator}_pct"] = (
            100.0
            * coverage[numerator]
            / coverage["total_admissions"]
        )
    return measures, coverage


def build_hourly_panel(
    national_panel: pd.DataFrame,
    measures: pd.DataFrame,
) -> pd.DataFrame:
    base = national_panel.loc[
        national_panel["included_main"].eq(True)
    ].copy()
    base["cbo_4d"] = base["cbo_4d"].astype(str).str.zfill(4)
    metrics = measures.copy()
    metrics["cbo_4d"] = metrics["cbo_4d"].astype(str).str.zfill(4)
    panel = base.merge(
        metrics,
        on=["cbo_4d", "periodo_num"],
        how="left",
        validate="one_to_one",
    )
    panel["weekly_hours_adm"] = np.where(
        panel["valid_hours_admissions"].gt(0),
        panel["weekly_hours_sum"]
        / panel["valid_hours_admissions"],
        np.nan,
    )
    panel["salario_hora_adm"] = np.where(
        panel["valid_hours_admissions"].gt(0),
        panel["hourly_wage_sum"]
        / panel["valid_hours_admissions"],
        np.nan,
    )
    panel["salario_hora_real_adm"] = (
        panel["salario_hora_adm"] * 100.0 / panel["indice"]
    )
    panel["ln_salario_hora_real_adm"] = np.log(
        panel["salario_hora_real_adm"]
    )
    panel["ln_horas_semanais_adm"] = np.log(
        panel["weekly_hours_adm"]
    )
    panel["pct_parcial_adm"] = np.where(
        panel["partial_known"].gt(0),
        panel["partial_yes"] / panel["partial_known"],
        np.nan,
    )
    panel["pct_intermitente_adm"] = np.where(
        panel["intermittent_known"].gt(0),
        panel["intermittent_yes"] / panel["intermittent_known"],
        np.nan,
    )
    panel["post_treat"] = (
        panel["post"] * panel["treated_main"]
    ).astype("int8")
    return panel


def estimate_outcomes(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome, label in OUTCOMES:
        result, _ = fit_model(
            panel,
            model_id=f"hourly_wage__{outcome}",
            outcome=outcome,
            treatment_term="post_treat",
            estimator="ols",
            fixed_effects=("cbo_4d", "periodo"),
            cluster_variables=("cbo_4d",),
            controls=(),
            principal=True,
        )
        result["outcome_label"] = label
        rows.append(result)
    results = pd.DataFrame(rows)
    results["bh_adjusted_p_value"] = benjamini_hochberg(
        results["p_value"].to_numpy()
    )
    results["multiplicity_family_size"] = len(OUTCOMES)
    return results


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def write_report(
    results: pd.DataFrame,
    coverage: pd.DataFrame,
    gate: dict[str, Any],
    path: Path,
) -> None:
    lines = [
        "# Task 25 hourly wage and work-schedule margins",
        "",
        "## Continuity gate",
        "",
        (
            f"**PASS.** Valid contracted hours cover at least "
            f"{gate['minimum_coverage_pct']:.2f}% of signed admissions. "
            f"The largest adjacent change is "
            f"{gate['maximum_adjacent_change_pp']:.2f} percentage points."
        ),
        "",
        (
            "The monthly wage is the declared monthly salary. Hourly wage "
            "divides it by five times contracted weekly hours and applies "
            "CBO4-year P1/P99 winsorization before IPCA deflation."
        ),
        "",
        "## Principal outcome family",
        "",
        (
            "| Outcome | Coefficient | SE | Nominal p | BH-adjusted p | "
            "N | CBO clusters |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results.itertuples(index=False):
        lines.append(
            f"| {row.outcome_label} | {row.coefficient:.6f} | "
            f"{row.standard_error:.6f} | {row.p_value:.6g} | "
            f"{row.bh_adjusted_p_value:.6g} | {row.n_obs:,} | "
            f"{row.minimum_clusters} |"
        )
    lines.extend(
        [
            "",
            (
                "Partial and intermittent indicators exclude unknown code "
                "9 from their denominators. All results remain descriptive "
                "because the national pretrend diagnostics fail."
            ),
            "",
            (
                f"Coverage rows: {len(coverage)} "
                f"({int(coverage.periodo_num.min())}-"
                f"{int(coverage.periodo_num.max())})."
            ),
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Task 25 hourly wage models."
    )
    parser.add_argument(
        "--movements",
        type=Path,
        default=DEFAULT_MOVEMENTS,
    )
    parser.add_argument(
        "--national-panel",
        type=Path,
        default=DEFAULT_NATIONAL_PANEL,
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    measures, coverage = aggregate_hourly_measures(args.movements)
    gate = evaluate_hours_continuity(
        coverage["valid_hours_admissions_pct"]
    )
    _atomic_csv(coverage, args.coverage)
    if gate["status"] != "pass":
        status = {
            "status": "not_executed_structural_break",
            "continuity_gate": gate,
        }
        _atomic_json(status, args.status)
        print(json.dumps(status, sort_keys=True))
        return 2
    panel = build_hourly_panel(
        pd.read_parquet(args.national_panel),
        measures,
    )
    results = estimate_outcomes(panel)
    support = results[
        [
            "outcome",
            "outcome_label",
            "input_cells",
            "complete_case_cells",
            "n_obs",
            "cells_dropped",
            "minimum_clusters",
        ]
    ].copy()
    _atomic_parquet(panel, args.panel)
    _atomic_csv(results, args.results)
    _atomic_csv(support, args.support)
    status = {
        "status": "completed",
        "continuity_gate": gate,
        "model_count": int(len(results)),
        "family_size": len(OUTCOMES),
        "panel_rows": int(len(panel)),
        "coverage_months": int(len(coverage)),
    }
    _atomic_json(status, args.status)
    write_report(results, coverage, gate, args.report)
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
