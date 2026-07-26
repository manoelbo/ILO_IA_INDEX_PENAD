#!/usr/bin/env python3
"""Estimate Task 26 size heterogeneity and audit nature fields."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from estimators import fit_model
from heterogeneity import benjamini_hochberg


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
    PACKAGE_ROOT / "data" / "derived" / "painel_employer_size.parquet"
)
DEFAULT_RESULTS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "employer_size_ddd_results.csv"
)
DEFAULT_SIZE_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "employer_size_support.csv"
)
DEFAULT_NATURE_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "employer_registration_support.csv"
)
DEFAULT_STATUS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "employer_size_status.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT / "results" / "mechanisms" / "EMPLOYER_SIZE.md"
)
DEFAULT_SCRATCH = PACKAGE_ROOT / "data" / "interim"
START_PERIOD = 202101
END_PERIOD = 202605

SIZE_CATEGORIES = {
    "1": "Zero employees",
    "2": "1-4 employees",
    "3": "5-9 employees",
    "4": "10-19 employees",
    "5": "20-49 employees",
    "6": "50-99 employees",
    "7": "100-249 employees",
    "8": "250-499 employees",
    "9": "500-999 employees",
    "10": "1,000 or more",
}
EMPLOYER_TYPE_LABELS = {
    "0": "CNPJ root",
    "2": "CPF",
    "9": "Not identified",
    "1": "Undocumented preserved code",
}
ESTABLISHMENT_TYPE_LABELS = {
    "1": "CNPJ",
    "3": "CAEPF",
    "4": "CNO",
    "5": "CEI",
    "9": "Not identified",
    "-1": "Undocumented preserved code",
}
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)
PLANNED_FAMILY_SIZE = len(SIZE_CATEGORIES) * len(OUTCOMES)


def public_private_identification_assessment() -> dict[str, Any]:
    return {
        "identified": False,
        "status": "not_executed_nonidentifying_fields",
        "reason": (
            "tipoempregador and tipoestabelecimento encode registration "
            "form, not public-versus-private ownership"
        ),
    }


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def aggregate_size_and_nature(
    movements_glob: Path,
    *,
    scratch_parent: Path = DEFAULT_SCRATCH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = _sql_literal(movements_glob)
    scratch_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="t26-duckdb-",
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
                CREATE TEMP VIEW valid_movements AS
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
                    CAST(saldomovimentacao AS INTEGER) AS movement,
                    CAST(peso AS BIGINT) AS peso,
                    CAST(salario AS DOUBLE) AS salario,
                    CAST(tamestabjan AS VARCHAR) AS size_code,
                    CAST(tipoempregador AS VARCHAR) AS employer_type,
                    CAST(tipoestabelecimento AS VARCHAR)
                        AS establishment_type
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
                  AND CAST(saldomovimentacao AS INTEGER) IN (-1, 1)
                  AND CAST(peso AS INTEGER) IN (-1, 1)
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
            allowed_sizes = ", ".join(
                _sql_literal(code) for code in SIZE_CATEGORIES
            )
            size_counts = connection.execute(
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
                    WHERE movement.size_code IN ({allowed_sizes})
                )
                SELECT
                    size_code,
                    cbo_4d,
                    periodo_num,
                    CAST(sum(
                        CASE WHEN movement = 1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS admissoes,
                    CAST(sum(
                        CASE WHEN movement = -1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS desligamentos,
                    sum(
                        CASE
                            WHEN movement = 1
                            THEN peso * salario_winsor ELSE 0
                        END
                    ) AS salario_soma_adm
                FROM winsorized
                GROUP BY size_code, cbo_4d, periodo_num
                ORDER BY size_code, cbo_4d, periodo_num
                """
            ).df()
            nature = connection.execute(
                """
                SELECT
                    'tipoempregador' AS dimension,
                    employer_type AS code,
                    count(*) AS physical_rows,
                    CAST(sum(peso) AS BIGINT) AS signed_rows,
                    CAST(sum(
                        CASE WHEN movement = 1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS signed_admissions,
                    CAST(sum(
                        CASE WHEN movement = -1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS signed_separations
                FROM valid_movements
                GROUP BY employer_type
                UNION ALL
                SELECT
                    'tipoestabelecimento' AS dimension,
                    establishment_type AS code,
                    count(*) AS physical_rows,
                    CAST(sum(peso) AS BIGINT) AS signed_rows,
                    CAST(sum(
                        CASE WHEN movement = 1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS signed_admissions,
                    CAST(sum(
                        CASE WHEN movement = -1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS signed_separations
                FROM valid_movements
                GROUP BY establishment_type
                ORDER BY dimension, code
                """
            ).df()
        finally:
            connection.close()
    nature["label"] = [
        (
            EMPLOYER_TYPE_LABELS.get(str(code), "Unmapped")
            if dimension == "tipoempregador"
            else ESTABLISHMENT_TYPE_LABELS.get(str(code), "Unmapped")
        )
        for dimension, code in zip(
            nature["dimension"],
            nature["code"],
        )
    ]
    if nature["label"].eq("Unmapped").any():
        raise RuntimeError("Employer nature support contains unmapped codes")
    return size_counts, nature


def build_size_panel(
    national_panel: pd.DataFrame,
    size_counts: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = national_panel.loc[
        national_panel["included_main"].eq(True),
        [
            "cbo_4d",
            "periodo_num",
            "periodo",
            "post",
            "treated_main",
            "indice",
        ],
    ].copy()
    base["cbo_4d"] = base["cbo_4d"].astype(str).str.zfill(4)
    counts = size_counts.copy()
    counts["cbo_4d"] = counts["cbo_4d"].astype(str).str.zfill(4)
    keys = ["cbo_4d", "periodo_num"]
    totals = (
        counts.groupby(keys, as_index=False)[
            ["admissoes", "desligamentos", "salario_soma_adm"]
        ]
        .sum()
    )
    panels = []
    support = []
    for size_code, size_label in SIZE_CATEGORIES.items():
        target = counts.loc[
            counts["size_code"].eq(size_code),
            [
                *keys,
                "admissoes",
                "desligamentos",
                "salario_soma_adm",
            ],
        ]
        values = totals.merge(
            target,
            on=keys,
            how="left",
            suffixes=("_total", "_target"),
            validate="one_to_one",
        )
        for column in (
            "admissoes",
            "desligamentos",
            "salario_soma_adm",
        ):
            values[f"{column}_target"] = values[
                f"{column}_target"
            ].fillna(0)
            values[f"{column}_complement"] = (
                values[f"{column}_total"]
                - values[f"{column}_target"]
            )
        subgroup_frames = []
        for subgroup in ("target", "complement"):
            part = values[
                [
                    *keys,
                    f"admissoes_{subgroup}",
                    f"desligamentos_{subgroup}",
                    f"salario_soma_adm_{subgroup}",
                ]
            ].copy()
            part.columns = [
                *keys,
                "admissoes",
                "desligamentos",
                "salario_soma_adm",
            ]
            part["subgroup"] = subgroup
            subgroup_frames.append(part)
        long = pd.concat(subgroup_frames, ignore_index=True)
        grid = pd.concat(
            [
                base.assign(subgroup="target"),
                base.assign(subgroup="complement"),
            ],
            ignore_index=True,
        )
        panel = grid.merge(
            long,
            on=[*keys, "subgroup"],
            how="left",
            validate="one_to_one",
        )
        for column in (
            "admissoes",
            "desligamentos",
            "salario_soma_adm",
        ):
            panel[column] = panel[column].fillna(0)
        if (
            panel["admissoes"].lt(0).any()
            or panel["desligamentos"].lt(0).any()
        ):
            raise RuntimeError("Negative signed size cells found")
        panel["saldo"] = (
            panel["admissoes"] - panel["desligamentos"]
        )
        panel["n_movimentacoes"] = (
            panel["admissoes"] + panel["desligamentos"]
        )
        panel["asinh_saldo"] = np.arcsinh(panel["saldo"])
        panel["salario_medio_adm"] = np.where(
            panel["admissoes"].gt(0),
            panel["salario_soma_adm"] / panel["admissoes"],
            np.nan,
        )
        panel["ln_salario_real_adm"] = np.log(
            panel["salario_medio_adm"] * 100.0 / panel["indice"]
        )
        panel["size_code"] = size_code
        panel["size_label"] = size_label
        panel["group_indicator"] = (
            panel["subgroup"].eq("target").astype("int8")
        )
        panel["treatment"] = panel["treated_main"].astype("int8")
        panel["post_treat"] = panel["post"] * panel["treatment"]
        panel["post_group"] = panel["post"] * panel["group_indicator"]
        panel["treat_group"] = (
            panel["treatment"] * panel["group_indicator"]
        )
        panel["post_treat_group"] = (
            panel["post"]
            * panel["treatment"]
            * panel["group_indicator"]
        )
        positive = panel.loc[
            panel["subgroup"].eq("target")
            & (
                panel["admissoes"].gt(0)
                | panel["desligamentos"].gt(0)
            )
        ]
        support.append(
            {
                "size_code": size_code,
                "size_label": size_label,
                "signed_admissions_target": int(
                    panel.loc[
                        panel["subgroup"].eq("target"),
                        "admissoes",
                    ].sum()
                ),
                "signed_separations_target": int(
                    panel.loc[
                        panel["subgroup"].eq("target"),
                        "desligamentos",
                    ].sum()
                ),
                "positive_cells": int(len(positive)),
                "treated_cbo_with_positive_flow": int(
                    positive.loc[
                        positive["treated_main"].eq(1),
                        "cbo_4d",
                    ].nunique()
                ),
                "control_cbo_with_positive_flow": int(
                    positive.loc[
                        positive["treated_main"].eq(0),
                        "cbo_4d",
                    ].nunique()
                ),
            }
        )
        panels.append(panel)
    return (
        pd.concat(panels, ignore_index=True),
        pd.DataFrame(support),
    )


def estimate_size_ddd(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for size_code, group in panel.groupby("size_code", sort=False):
        for outcome, estimator in OUTCOMES:
            result, _ = fit_model(
                group,
                model_id=f"size_{size_code}__{outcome}",
                outcome=outcome,
                treatment_term="post_treat_group",
                estimator=estimator,
                fixed_effects=("cbo_4d", "periodo", "subgroup"),
                cluster_variables=("cbo_4d",),
                controls=("post_treat", "post_group", "treat_group"),
                principal=True,
                separation_check=("fe",),
            )
            result.update(
                {
                    "size_code": size_code,
                    "size_label": group["size_label"].iloc[0],
                }
            )
            rows.append(result)
    results = pd.DataFrame(rows)
    if len(results) != PLANNED_FAMILY_SIZE:
        raise RuntimeError("Employer-size DDD family is incomplete")
    results["bh_adjusted_p_value"] = benjamini_hochberg(
        results["p_value"].to_numpy(),
        family_size=PLANNED_FAMILY_SIZE,
    )
    results["multiplicity_family_size"] = PLANNED_FAMILY_SIZE
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
    support: pd.DataFrame,
    nature: pd.DataFrame,
    path: Path,
) -> None:
    lines = [
        "# Task 26 establishment size and registration nature",
        "",
        "## Establishment-size support",
        "",
        "| Size | Admissions | Separations | Treated CBOs | Control CBOs |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in support.itertuples(index=False):
        lines.append(
            f"| {row.size_label} | {row.signed_admissions_target:,} | "
            f"{row.signed_separations_target:,} | "
            f"{row.treated_cbo_with_positive_flow} | "
            f"{row.control_cbo_with_positive_flow} |"
        )
    lines.extend(
        [
            "",
            "## Multiplicity",
            "",
            (
                f"All {len(results)} preregistered size-by-outcome DDD "
                "contrasts are reported with nominal and global "
                "BH-adjusted p-values."
            ),
            "",
            (
                f"BH-adjusted p < 0.05: "
                f"{int(results['bh_adjusted_p_value'].lt(0.05).sum())}."
            ),
            "",
            "## Public-versus-private falsification",
            "",
            (
                "**NOT EXECUTED: non-identifying source fields.** The "
                "official employer and establishment fields encode "
                "registration form, not public/private ownership. Their "
                "code-level support is exported without semantic relabeling."
            ),
            "",
            f"Registration support rows: {len(nature)}.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Task 26 employer-size heterogeneity."
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
    parser.add_argument(
        "--size-support",
        type=Path,
        default=DEFAULT_SIZE_SUPPORT,
    )
    parser.add_argument(
        "--nature-support",
        type=Path,
        default=DEFAULT_NATURE_SUPPORT,
    )
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    size_counts, nature = aggregate_size_and_nature(args.movements)
    panel, support = build_size_panel(
        pd.read_parquet(args.national_panel),
        size_counts,
    )
    _atomic_parquet(panel, args.panel)
    _atomic_csv(support, args.size_support)
    _atomic_csv(nature, args.nature_support)
    results = estimate_size_ddd(panel)
    _atomic_csv(results, args.results)
    status = {
        "status": "completed_with_declared_nonexecution",
        "size_group_count": len(SIZE_CATEGORIES),
        "outcome_count": len(OUTCOMES),
        "model_count": int(len(results)),
        "family_size": PLANNED_FAMILY_SIZE,
        "bh_significant_count": int(
            results["bh_adjusted_p_value"].lt(0.05).sum()
        ),
        "public_private_falsification": (
            public_private_identification_assessment()
        ),
        "panel_rows": int(len(panel)),
    }
    _atomic_json(status, args.status)
    write_report(results, support, nature, args.report)
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
