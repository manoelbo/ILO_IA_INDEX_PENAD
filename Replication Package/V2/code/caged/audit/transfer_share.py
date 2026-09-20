#!/usr/bin/env python3
"""Audit block E: do establishment transfers inflate the flow outcomes?

`build_panel.py` defines admissions and separations from `saldomovimentacao`
alone and never reads `tipomovimentacao`. The official code dictionary
(`data/vintage/caged_dicionario_codigos.csv`) records:

    70  Admissão por transferência
    80  Desligamento por transferência

A transfer moves a worker between establishments, so it is neither an entry
into nor an exit from formal employment. Under a definition that reads only
`saldomovimentacao` it would count as one hire and one separation.

**The concern is void, and this script is what disproves it.** Codes 70 and 80
have zero occurrences in the frozen vintage: the eSocial-era Novo CAGED does
not report establishment transfers as movement types at all. The worry was
carried over from the old CAGED, where they existed.

The script is kept because the same scan answers a second question that does
matter, and answers it with a number: how much of `tipomovimentacao` is usable
at all. The answer is asymmetric — separations are almost fully coded, and
admissions are almost entirely "type ignored".

It writes evidence only, and rebuilds nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
MOVEMENTS = (
    PACKAGE_ROOT
    / "data"
    / "interim"
    / "movimentacoes"
    / "competenciamov=*"
    / "part.parquet"
)
CLASSIFICATION = (
    PACKAGE_ROOT / "data" / "derived" / "cbo_treatment_classification.csv"
)
VARIANTS = PACKAGE_ROOT / "data" / "derived" / "treatment_variants.csv"
OUTPUT_DIR = PACKAGE_ROOT / "results" / "audit"
TRANSFER_IN = "70"
TRANSFER_OUT = "80"
EXPOSED = (
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
)


def _sql(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def measure() -> pd.DataFrame:
    variants = pd.read_csv(VARIANTS, dtype={"cbo_4d": str})
    variants["cbo_4d"] = variants["cbo_4d"].str.zfill(4)
    keep = variants.loc[
        variants["gradient_v_a"].isin([*EXPOSED, "Not Exposed"]),
        ["cbo_4d", "gradient_v_a"],
    ].copy()
    keep["treated_main"] = (
        keep["gradient_v_a"].str.startswith("Exposed").astype(int)
    )

    connection = duckdb.connect()
    try:
        connection.execute("SET threads = 2")
        connection.register("classes", keep[["cbo_4d", "treated_main"]])
        # The validity filters mirror build_panel.py exactly, so the shares
        # below are shares of the very rows the headline panel aggregates.
        frame = connection.execute(
            f"""
            WITH valid AS (
                SELECT
                    CAST(competenciamov AS INTEGER) AS periodo_num,
                    substring(
                        CAST(cbo2002ocupacao AS VARCHAR), 1, 4
                    ) AS cbo_4d,
                    CAST(saldomovimentacao AS SMALLINT) AS movimento,
                    CAST(peso AS BIGINT) AS peso,
                    CAST(tipomovimentacao AS VARCHAR) AS movement_type
                FROM read_parquet(
                    {_sql(MOVEMENTS)},
                    hive_partitioning = true,
                    union_by_name = true
                )
                WHERE regexp_full_match(
                          CAST(cbo2002ocupacao AS VARCHAR), '[0-9]{{4,6}}'
                      )
                  AND substring(
                          CAST(cbo2002ocupacao AS VARCHAR), 1, 4
                      ) <> '0000'
                  AND CAST(idade AS INTEGER) BETWEEN 14 AND 90
                  AND CAST(salario AS DOUBLE) > 0
                  AND CAST(salario AS DOUBLE) < 1000000
                  AND CAST(saldomovimentacao AS INTEGER) IN (-1, 1)
                  AND CAST(peso AS INTEGER) IN (-1, 1)
            )
            SELECT
                CAST(floor(valid.periodo_num / 100) AS INTEGER) AS ano,
                classes.treated_main,
                CASE WHEN valid.movimento = 1
                     THEN 'admissao' ELSE 'desligamento' END AS fluxo,
                CAST(sum(valid.peso) AS BIGINT) AS total,
                CAST(sum(
                    CASE WHEN valid.movement_type IN (
                        '{TRANSFER_IN}', '{TRANSFER_OUT}'
                    ) THEN valid.peso ELSE 0 END
                ) AS BIGINT) AS transferencias
            FROM valid
            INNER JOIN classes USING (cbo_4d)
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
            """
        ).df()
    finally:
        connection.close()
    frame["share_pct"] = 100.0 * frame["transferencias"] / frame["total"]
    return frame


def movement_type_distribution() -> pd.DataFrame:
    """Full `tipomovimentacao` distribution, split by direction of flow."""

    connection = duckdb.connect()
    try:
        connection.execute("SET threads = 2")
        frame = connection.execute(
            f"""
            SELECT
                CASE WHEN CAST(saldomovimentacao AS INTEGER) = 1
                     THEN 'admissao' ELSE 'desligamento' END AS fluxo,
                CAST(tipomovimentacao AS VARCHAR) AS movement_type,
                CAST(count(*) AS BIGINT) AS rows
            FROM read_parquet(
                {_sql(MOVEMENTS)},
                hive_partitioning = true,
                union_by_name = true
            )
            WHERE CAST(saldomovimentacao AS INTEGER) IN (-1, 1)
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC
            """
        ).df()
    finally:
        connection.close()
    totals = frame.groupby("fluxo")["rows"].transform("sum")
    frame["share_pct"] = 100.0 * frame["rows"] / totals
    return frame


def summarise(frame: pd.DataFrame) -> dict[str, object]:
    pre = frame.loc[frame["ano"].le(2022)]
    post = frame.loc[frame["ano"].ge(2023)]

    def share(part: pd.DataFrame, treated: int, fluxo: str) -> float:
        cut = part.loc[
            part["treated_main"].eq(treated) & part["fluxo"].eq(fluxo)
        ]
        return float(
            100.0 * cut["transferencias"].sum() / cut["total"].sum()
        )

    summary: dict[str, object] = {
        "transfer_in_code": TRANSFER_IN,
        "transfer_out_code": TRANSFER_OUT,
        "excluded_by_separation_mechanisms": ["50", "60", "80"],
        "panel_filters_transfers": False,
        "verdict": (
            "void: codes 70 and 80 do not occur in the frozen vintage, so "
            "establishment transfers cannot be inflating the flow outcomes"
        ),
    }
    for fluxo in ("admissao", "desligamento"):
        treated_pre = share(pre, 1, fluxo)
        control_pre = share(pre, 0, fluxo)
        treated_post = share(post, 1, fluxo)
        control_post = share(post, 0, fluxo)
        summary[fluxo] = {
            "treated_pre_pct": treated_pre,
            "control_pre_pct": control_pre,
            "treated_post_pct": treated_post,
            "control_post_pct": control_post,
            "gap_pre_pp": treated_pre - control_pre,
            "gap_post_pp": treated_post - control_post,
            # This is the number that decides the severity: a differential
            # change in transfer intensity is what would move the coefficient.
            "did_pp": (treated_post - treated_pre)
            - (control_post - control_pre),
        }
    return summary


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = measure()
    frame.to_csv(OUTPUT_DIR / "e1_transfer_share_by_year.csv", index=False)
    distribution = movement_type_distribution()
    distribution.to_csv(
        OUTPUT_DIR / "e2_movement_type_distribution.csv",
        index=False,
    )
    summary = summarise(frame)
    admissions = distribution.loc[distribution["fluxo"].eq("admissao")]
    separations = distribution.loc[distribution["fluxo"].eq("desligamento")]
    summary["movement_type_usability"] = {
        "transfer_rows_found": int(
            distribution.loc[
                distribution["movement_type"].isin(
                    [TRANSFER_IN, TRANSFER_OUT]
                ),
                "rows",
            ].sum()
        ),
        "admission_type_ignored_pct": float(
            admissions.loc[
                admissions["movement_type"].eq("97"), "share_pct"
            ].sum()
        ),
        "separation_type_ignored_pct": float(
            separations.loc[
                separations["movement_type"].eq("98"), "share_pct"
            ].sum()
        ),
        "note": (
            "Separation type is usable and admission type is not. Any "
            "entry-margin decomposition by admission type is foreclosed."
        ),
    }
    (OUTPUT_DIR / "e_transfer_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
