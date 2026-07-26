#!/usr/bin/env python3
"""Run the preregistered sector fixed-effect and inference ladder."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from merge_audit import audited_merge
from estimators import fit_model


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUBCLASS_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_cbo_cnae.parquet"
)
DEFAULT_DIVISION_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_cbo_divisao.parquet"
)
DEFAULT_NATIONAL_LADDER = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "specification_ladder.csv"
)
DEFAULT_SUPPORT_TABLE = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "01_sector_fixed_effect_support.csv"
)
DEFAULT_RESULTS = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "sector_fixed_effect_ladder.csv"
)
DEFAULT_COMPARISON = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "sector_level1_vs_level2.csv"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "SECTOR_FIXED_EFFECT_RESULTS.md"
)
DEFAULT_SUPPORT_JSON = (
    PACKAGE_ROOT
    / "results"
    / "models"
    / "sector_fixed_effect_support.json"
)
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)


def sector_model_contract() -> list[dict[str, Any]]:
    return [
        {
            "level_id": "level_2",
            "role": "co_principal_sector",
            "fixed_effects": ("cbo_section", "section_period"),
            "cluster_variables": ("cbo_4d",),
        },
        {
            "level_id": "level_2_two_way",
            "role": "inference_robustness",
            "fixed_effects": ("cbo_section", "section_period"),
            "cluster_variables": ("cbo_4d", "divisao"),
        },
        {
            "level_id": "level_3",
            "role": "support_diagnostic",
            "fixed_effects": (
                "cbo_section",
                "section_period",
                "cbo2_period",
            ),
            "cluster_variables": ("cbo_4d",),
        },
    ]


def _sql_path(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_division_panel(
    subclass_panel: Path,
    division_panel: Path,
) -> dict[str, Any]:
    division_panel.parent.mkdir(parents=True, exist_ok=True)
    temporary = division_panel.with_suffix(
        f"{division_panel.suffix}.tmp"
    )
    connection = duckdb.connect()
    try:
        connection.execute(
            f"""
            COPY (
                WITH grouped AS (
                    SELECT
                        cbo_4d,
                        secao,
                        divisao,
                        periodo_num,
                        min(ano) AS ano,
                        min(mes) AS mes,
                        min(periodo) AS periodo,
                        min(post) AS post,
                        min(cbo_ilo_gradient) AS cbo_ilo_gradient,
                        min(treated_main) AS treated_main,
                        min(included_main) AS included_main,
                        min(indice) AS indice,
                        sum(admissoes) AS admissoes,
                        sum(desligamentos) AS desligamentos,
                        sum(saldo) AS saldo,
                        sum(n_movimentacoes) AS n_movimentacoes,
                        sum(
                            salario_medio_adm * admissoes
                        ) / nullif(sum(admissoes), 0)
                            AS salario_medio_adm,
                        sum(
                            salario_medio_desl * desligamentos
                        ) / nullif(sum(desligamentos), 0)
                            AS salario_medio_desl
                    FROM read_parquet(
                        {_sql_path(subclass_panel)}
                    )
                    WHERE cnae_status = 'official'
                    GROUP BY
                        cbo_4d, secao, divisao, periodo_num
                )
                SELECT
                    *,
                    salario_medio_adm * 100.0 / indice
                        AS salario_real_adm,
                    salario_medio_desl * 100.0 / indice
                        AS salario_real_desl,
                    ln(salario_medio_adm * 100.0 / indice)
                        AS ln_salario_real_adm,
                    ln(salario_medio_desl * 100.0 / indice)
                        AS ln_salario_real_desl,
                    asinh(saldo) AS asinh_saldo
                FROM grouped
            )
            TO {_sql_path(temporary)}
            (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
        os.replace(temporary, division_panel)
        metrics = connection.execute(
            f"""
            SELECT
                count(*) AS cells,
                count(*) - count(DISTINCT (
                    cbo_4d, divisao, periodo_num
                )) AS duplicates,
                count(DISTINCT secao) AS sections,
                count(DISTINCT divisao) AS divisions,
                sum(admissoes) AS admissions,
                sum(desligamentos) AS separations
            FROM read_parquet({_sql_path(division_panel)})
            """
        ).fetchone()
    finally:
        connection.close()
    if int(metrics[1]) != 0:
        raise RuntimeError("Division panel contains duplicate keys")
    return {
        "division_panel_cells": int(metrics[0]),
        "division_panel_bytes": division_panel.stat().st_size,
        "division_panel_sha256": sha256_file(division_panel),
        "duplicate_cells": int(metrics[1]),
        "official_sections": int(metrics[2]),
        "official_divisions": int(metrics[3]),
        "admissions": int(metrics[4]),
        "separations": int(metrics[5]),
    }


def build_support_table(division_panel: Path) -> pd.DataFrame:
    connection = duckdb.connect()
    try:
        source = _sql_path(division_panel)
        connection.execute(
            f"""
            CREATE TEMP VIEW sample AS
            SELECT
                *,
                substring(cbo_4d, 1, 2) AS cbo_2d
            FROM read_parquet({source})
            WHERE included_main
            """
        )
        records = []
        for level_id, group_columns in (
            ("level_1", ["periodo"]),
            ("level_2", ["secao", "periodo"]),
            ("level_3", ["secao", "periodo", "cbo_2d"]),
        ):
            group_sql = ", ".join(group_columns)
            connection.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE support_cells AS
                SELECT
                    {group_sql},
                    count(*) AS observations,
                    count(DISTINCT cbo_4d) FILTER (
                        WHERE treated_main = 1
                    ) AS treated_cbos,
                    count(DISTINCT cbo_4d) FILTER (
                        WHERE treated_main = 0
                    ) AS control_cbos
                FROM sample
                GROUP BY {group_sql}
                """
            )
            summary = connection.execute(
                """
                SELECT
                    count(*),
                    quantile_cont(observations, 0.10),
                    min(observations),
                    median(treated_cbos),
                    median(control_cbos),
                    count(*) FILTER (
                        WHERE treated_cbos > 0 AND control_cbos > 0
                    )
                FROM support_cells
                """
            ).fetchone()
            participating = connection.execute(
                f"""
                SELECT
                    count(DISTINCT cbo_4d) FILTER (
                        WHERE treated_main = 1
                    ),
                    count(DISTINCT cbo_4d) FILTER (
                        WHERE treated_main = 0
                    )
                FROM sample
                INNER JOIN support_cells USING ({group_sql})
                WHERE treated_cbos > 0 AND control_cbos > 0
                """
            ).fetchone()
            records.append(
                {
                    "level_id": level_id,
                    "fixed_effect_cell": "^".join(group_columns),
                    "cells": int(summary[0]),
                    "observations_per_cell_p10": float(summary[1]),
                    "observations_per_cell_min": int(summary[2]),
                    "median_treated_cbos_per_cell": float(summary[3]),
                    "median_control_cbos_per_cell": float(summary[4]),
                    "coexisting_cells": int(summary[5]),
                    "coexisting_cell_share": float(
                        summary[5] / summary[0]
                    ),
                    "treated_cbos_in_coexisting_cells": int(
                        participating[0]
                    ),
                    "control_cbos_in_coexisting_cells": int(
                        participating[1]
                    ),
                }
            )
    finally:
        connection.close()
    return pd.DataFrame(records)


def load_model_data(path: Path) -> pd.DataFrame:
    columns = [
        "cbo_4d",
        "secao",
        "divisao",
        "periodo",
        "post",
        "treated_main",
        "included_main",
        *[outcome for outcome, _ in OUTCOMES],
    ]
    data = pd.read_parquet(path, columns=columns)
    data = data.loc[data["included_main"].eq(True)].copy()
    data["cbo_2d"] = data["cbo_4d"].str[:2]
    data["treated_main"] = pd.to_numeric(
        data["treated_main"],
        errors="raise",
    )
    data["post_treat"] = (
        pd.to_numeric(data["post"], errors="raise")
        * data["treated_main"]
    ).astype(float)
    data["cbo_section"] = (
        data["cbo_4d"].astype(str) + "::" + data["secao"].astype(str)
    ).astype("category")
    data["section_period"] = (
        data["secao"].astype(str) + "::" + data["periodo"].astype(str)
    ).astype("category")
    data["cbo2_period"] = (
        data["cbo_2d"].astype(str) + "::" + data["periodo"].astype(str)
    ).astype("category")
    for column in ("cbo_4d", "secao", "divisao", "periodo"):
        data[column] = data[column].astype("category")
    return data


def run_sector_models(
    data: pd.DataFrame,
    support: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    level_three_support = int(
        support.loc[
            support["level_id"].eq("level_3"),
            "treated_cbos_in_coexisting_cells",
        ].item()
    )
    for contract in sector_model_contract():
        for outcome, estimator in OUTCOMES:
            result, _ = fit_model(
                data,
                model_id=f"{contract['level_id']}__{outcome}",
                outcome=outcome,
                treatment_term="post_treat",
                estimator=estimator,
                fixed_effects=contract["fixed_effects"],
                cluster_variables=contract["cluster_variables"],
                principal=contract["level_id"] == "level_2",
                separation_check=("fe",),
            )
            result.update(
                {
                    "level_id": contract["level_id"],
                    "role": contract["role"],
                    "substantive_interpretation_allowed": (
                        contract["level_id"] != "level_3"
                        or level_three_support >= 20
                    ),
                }
            )
            rows.append(result)
    results = pd.DataFrame(rows)
    support_json = {
        "model_count": int(len(results)),
        "all_models_converged": bool(results["converged"].all()),
        "level_3_treated_cbo_support": level_three_support,
        "level_3_minimum_required": 20,
        "level_3_substantive_interpretation_allowed": (
            level_three_support >= 20
        ),
        "two_way_division_clusters": int(
            data["divisao"].nunique()
        ),
        "cbo_clusters": int(data["cbo_4d"].nunique()),
    }
    return results, support_json


def compare_levels(
    sector_results: pd.DataFrame,
    national_ladder: pd.DataFrame,
) -> pd.DataFrame:
    level_one = national_ladder.loc[
        national_ladder["step_id"].eq("01_no_controls"),
        ["outcome", "coefficient", "standard_error", "p_value"],
    ].rename(
        columns={
            "coefficient": "level_1_coefficient",
            "standard_error": "level_1_standard_error",
            "p_value": "level_1_p_value",
        }
    )
    level_two = sector_results.loc[
        sector_results["level_id"].eq("level_2"),
        ["outcome", "coefficient", "standard_error", "p_value"],
    ].rename(
        columns={
            "coefficient": "level_2_coefficient",
            "standard_error": "level_2_standard_error",
            "p_value": "level_2_p_value",
        }
    )
    comparison = audited_merge(
        level_one,
        level_two,
        merge_id="sector_models_level_one_to_level_two",
        on="outcome",
        validate="one_to_one",
    )
    comparison["coefficient_delta_level_2_minus_level_1"] = (
        comparison["level_2_coefficient"]
        - comparison["level_1_coefficient"]
    )
    return comparison


def render_report(
    comparison: pd.DataFrame,
    support_json: dict[str, Any],
) -> str:
    lines = [
        "# Sector Fixed-Effect Ladder",
        "",
        "The support table was generated before coefficient estimation. "
        "Level 1 and level 2 are co-principal estimands; level 3 is a "
        "support diagnostic. The undocumented Z/ZZ industry bucket is "
        "excluded rather than assigned an official sector.",
        "",
        "| Outcome | Level 1 | Level 2 | Level 2 - Level 1 |",
        "|---|---:|---:|---:|",
    ]
    for row in comparison.itertuples(index=False):
        lines.append(
            f"| {row.outcome} | {row.level_1_coefficient:.6f} | "
            f"{row.level_2_coefficient:.6f} | "
            f"{row.coefficient_delta_level_2_minus_level_1:+.6f} |"
        )
    lines.extend(
        [
            "",
            f"Two-way robustness uses "
            f"{support_json['cbo_clusters']} CBO4 clusters and "
            f"{support_json['two_way_division_clusters']} official "
            "CNAE-division clusters. Level 3 substantive interpretation "
            f"is {'allowed' if support_json['level_3_substantive_interpretation_allowed'] else 'not allowed'} "
            "under the preregistered 20-treated-CBO support rule.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the sector fixed-effect ladder."
    )
    parser.add_argument(
        "--subclass-panel",
        type=Path,
        default=DEFAULT_SUBCLASS_PANEL,
    )
    parser.add_argument(
        "--division-panel",
        type=Path,
        default=DEFAULT_DIVISION_PANEL,
    )
    parser.add_argument(
        "--national-ladder",
        type=Path,
        default=DEFAULT_NATIONAL_LADDER,
    )
    parser.add_argument(
        "--support-table",
        type=Path,
        default=DEFAULT_SUPPORT_TABLE,
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument(
        "--comparison",
        type=Path,
        default=DEFAULT_COMPARISON,
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--support-json",
        type=Path,
        default=DEFAULT_SUPPORT_JSON,
    )
    parser.add_argument("--support-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    panel_metrics = build_division_panel(
        args.subclass_panel,
        args.division_panel,
    )
    support = build_support_table(args.division_panel)
    _atomic_csv(support, args.support_table)
    if args.support_only:
        print(json.dumps(panel_metrics, sort_keys=True))
        return 0
    data = load_model_data(args.division_panel)
    results, support_json = run_sector_models(data, support)
    support_json.update(panel_metrics)
    comparison = compare_levels(
        results,
        pd.read_csv(args.national_ladder),
    )
    _atomic_csv(results, args.results)
    _atomic_csv(comparison, args.comparison)
    _atomic_text(
        render_report(comparison, support_json),
        args.report,
    )
    _atomic_text(
        json.dumps(support_json, indent=2, sort_keys=True) + "\n",
        args.support_json,
    )
    print(json.dumps(support_json, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
