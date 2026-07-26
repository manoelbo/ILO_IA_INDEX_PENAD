#!/usr/bin/env python3
"""Build and estimate the frozen V2 DDD multiplicity family."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

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
    PACKAGE_ROOT / "data" / "derived" / "painel_heterogeneity_ddd.parquet"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "ddd_family_support.csv"
)
DEFAULT_RESULTS = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "ddd_multiplicity_results.csv"
)
DEFAULT_SUMMARY = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "ddd_multiplicity_support.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "DDD_MULTIPLICITY_RESULTS.md"
)
DEFAULT_SCRATCH = PACKAGE_ROOT / "data" / "interim"
START_PERIOD = 202101
PRE_END_PERIOD = 202211
END_PERIOD = 202605
WAGE_MIN = 0.0
WAGE_MAX = 1_000_000.0

DIMENSIONS: dict[str, dict[str, Any]] = {
    "sex": {
        "kind": "micro",
        "groups": (
            ("men", "Men"),
            ("women", "Women"),
        ),
    },
    "age_canaries": {
        "kind": "micro",
        "groups": (
            ("age_22_25", "Age 22-25"),
            ("age_26_30", "Age 26-30"),
            ("age_31_34", "Age 31-34"),
            ("age_35_40", "Age 35-40"),
            ("age_41_49", "Age 41-49"),
            ("age_50_plus", "Age 50+"),
        ),
    },
    "race_color": {
        "kind": "micro",
        "groups": (
            ("race_white", "White"),
            ("race_black", "Black"),
            ("race_pardo", "Pardo"),
            ("race_yellow", "Yellow"),
            ("race_indigenous", "Indigenous"),
            ("race_unknown", "Unidentified"),
        ),
    },
    "education": {
        "kind": "micro",
        "groups": (
            ("fundamental_or_less", "Primary or less"),
            ("high_school", "Secondary"),
            ("higher_education", "Higher education"),
        ),
    },
    "income": {
        "kind": "cbo_predetermined",
        "groups": (
            ("low_income", "Up to 2 minimum wages"),
            ("middle_income", "Over 2 through 5 minimum wages"),
            ("high_income", "Over 5 minimum wages"),
        ),
    },
}
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)
PLANNED_FAMILY_SIZE = 100
DDD_TREATMENT_TERM = "post_treat_group"
DDD_LOWER_TERMS = (
    "post_treat",
    "post_group",
    "treat_group",
)
AGGREGATE_COLUMNS = (
    "admissoes",
    "desligamentos",
    "salario_soma_adm",
)


def ddd_formula_contract() -> tuple[str, tuple[str, ...]]:
    return DDD_TREATMENT_TERM, DDD_LOWER_TERMS


def validate_ddd_formula_terms(terms: Sequence[str]) -> None:
    required = {DDD_TREATMENT_TERM, *DDD_LOWER_TERMS}
    missing = sorted(required - set(terms))
    if missing:
        raise ValueError(f"DDD formula is missing required terms: {missing}")


def estimable_lower_terms(
    dimension_kind: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if dimension_kind == "micro":
        return DDD_LOWER_TERMS, ()
    if dimension_kind == "cbo_predetermined":
        return (
            ("post_treat", "post_group"),
            ("treat_group",),
        )
    raise ValueError(f"Unknown DDD dimension kind: {dimension_kind}")


def benjamini_hochberg(
    p_values: np.ndarray,
    *,
    family_size: int,
) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    valid_positions = np.flatnonzero(np.isfinite(values))
    adjusted = np.full(values.shape, np.nan, dtype=float)
    if not len(valid_positions):
        return adjusted
    order = valid_positions[
        np.argsort(values[valid_positions], kind="mergesort")
    ]
    ranked = values[order] * family_size / np.arange(
        1,
        len(order) + 1,
    )
    monotone = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted[order] = np.minimum(monotone, 1.0)
    return adjusted


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _configure_connection(
    connection: duckdb.DuckDBPyConnection,
    scratch: Path,
) -> None:
    connection.execute("SET threads = 1")
    connection.execute("SET memory_limit = '1GB'")
    connection.execute("SET preserve_insertion_order = false")
    connection.execute(
        f"SET temp_directory = {_sql_literal(scratch)}"
    )


def _valid_source_sql(movements_glob: Path) -> str:
    source = _sql_literal(movements_glob)
    return f"""
        SELECT
            CAST(competenciamov AS INTEGER) AS periodo_num,
            substring(CAST(cbo2002ocupacao AS VARCHAR), 1, 4)
                AS cbo_4d,
            CAST(saldomovimentacao AS SMALLINT) AS movimento,
            CAST(peso AS BIGINT) AS peso,
            CAST(salario AS DOUBLE) AS salario,
            CAST(idade AS INTEGER) AS idade,
            CAST(sexo AS VARCHAR) AS sexo,
            CAST(graudeinstrucao AS VARCHAR) AS graudeinstrucao,
            CAST(racacor AS VARCHAR) AS racacor
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
          AND substring(CAST(cbo2002ocupacao AS VARCHAR), 1, 4)
              <> '0000'
          AND CAST(idade AS INTEGER) BETWEEN 14 AND 90
          AND CAST(salario AS DOUBLE) > {WAGE_MIN}
          AND CAST(salario AS DOUBLE) < {WAGE_MAX}
          AND CAST(saldomovimentacao AS INTEGER) IN (-1, 1)
          AND CAST(peso AS INTEGER) IN (-1, 1)
    """


def aggregate_signed_groups(
    movements_glob: Path,
    *,
    scratch_parent: Path = DEFAULT_SCRATCH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scratch_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="t21-duckdb-",
        dir=scratch_parent,
    ) as temporary:
        connection = duckdb.connect()
        try:
            _configure_connection(connection, Path(temporary))
            valid_sql = _valid_source_sql(movements_glob)
            connection.execute(
                f"""
                CREATE TEMP TABLE wage_bounds AS
                SELECT
                    cbo_4d,
                    CAST(floor(periodo_num / 100) AS INTEGER) AS ano,
                    approx_quantile(salario, 0.01) AS wage_p01,
                    approx_quantile(salario, 0.99) AS wage_p99
                FROM ({valid_sql}) AS movement
                WHERE peso = 1
                GROUP BY cbo_4d, ano
                """
            )
            actual = connection.execute(
                f"""
                WITH valid AS ({valid_sql}),
                winsorized AS (
                    SELECT
                        valid.*,
                        greatest(
                            bounds.wage_p01,
                            least(valid.salario, bounds.wage_p99)
                        ) AS salario_winsor
                    FROM valid
                    INNER JOIN wage_bounds AS bounds
                      ON valid.cbo_4d = bounds.cbo_4d
                     AND CAST(floor(valid.periodo_num / 100) AS INTEGER)
                         = bounds.ano
                ),
                categorized AS (
                    SELECT
                        category.dimension,
                        category.actual_group,
                        movement.*
                    FROM winsorized AS movement
                    CROSS JOIN LATERAL (
                        VALUES
                        (
                            'sex',
                            CASE
                                WHEN sexo = '1' THEN 'men'
                                WHEN sexo = '3' THEN 'women'
                            END
                        ),
                        (
                            'age_canaries',
                            CASE
                                WHEN idade BETWEEN 22 AND 25
                                THEN 'age_22_25'
                                WHEN idade BETWEEN 26 AND 30
                                THEN 'age_26_30'
                                WHEN idade BETWEEN 31 AND 34
                                THEN 'age_31_34'
                                WHEN idade BETWEEN 35 AND 40
                                THEN 'age_35_40'
                                WHEN idade BETWEEN 41 AND 49
                                THEN 'age_41_49'
                                WHEN idade >= 50 THEN 'age_50_plus'
                            END
                        ),
                        (
                            'race_color',
                            CASE
                                WHEN racacor = '1' THEN 'race_white'
                                WHEN racacor = '2' THEN 'race_black'
                                WHEN racacor = '3' THEN 'race_pardo'
                                WHEN racacor = '4' THEN 'race_yellow'
                                WHEN racacor = '5' THEN 'race_indigenous'
                                WHEN racacor IN ('6', '9')
                                THEN 'race_unknown'
                            END
                        ),
                        (
                            'education',
                            CASE
                                WHEN graudeinstrucao IN (
                                    '1', '2', '3', '4', '5'
                                ) THEN 'fundamental_or_less'
                                WHEN graudeinstrucao IN ('6', '7')
                                THEN 'high_school'
                                WHEN graudeinstrucao IN (
                                    '8', '9', '10', '11', '80'
                                ) THEN 'higher_education'
                            END
                        )
                    ) AS category(dimension, actual_group)
                    WHERE category.actual_group IS NOT NULL
                )
                SELECT
                    dimension,
                    actual_group,
                    cbo_4d,
                    periodo_num,
                    CAST(sum(
                        CASE WHEN movimento = 1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS admissoes,
                    CAST(sum(
                        CASE WHEN movimento = -1 THEN peso ELSE 0 END
                    ) AS BIGINT) AS desligamentos,
                    sum(
                        CASE
                            WHEN movimento = 1
                            THEN peso * salario_winsor
                            ELSE 0
                        END
                    ) AS salario_soma_adm
                FROM categorized
                GROUP BY
                    dimension,
                    actual_group,
                    cbo_4d,
                    periodo_num
                ORDER BY
                    dimension,
                    actual_group,
                    cbo_4d,
                    periodo_num
                """
            ).df()
            income = connection.execute(
                f"""
                WITH valid AS ({valid_sql})
                SELECT
                    cbo_4d,
                    median(
                        salario
                        / CASE
                            WHEN floor(periodo_num / 100) = 2021
                            THEN 1100.0
                            WHEN floor(periodo_num / 100) = 2022
                            THEN 1212.0
                          END
                    ) AS median_pre_wage_sm
                FROM valid
                WHERE periodo_num <= {PRE_END_PERIOD}
                  AND movimento = 1
                  AND peso = 1
                GROUP BY cbo_4d
                ORDER BY cbo_4d
                """
            ).df()
        finally:
            connection.close()
    return actual, income


def income_group(value: float) -> str | None:
    if not math.isfinite(value) or value <= 0:
        return None
    if value <= 2:
        return "low_income"
    if value <= 5:
        return "middle_income"
    return "high_income"


def _derive_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["admissoes"] = out["admissoes"].astype("int64")
    out["desligamentos"] = out["desligamentos"].astype("int64")
    negative = (
        out["admissoes"].lt(0)
        | out["desligamentos"].lt(0)
    )
    if negative.any():
        examples = out.loc[
            negative,
            [
                "dimension",
                "group_id",
                "subgroup",
                "cbo_4d",
                "periodo_num",
                "admissoes",
                "desligamentos",
            ],
        ].head(10)
        raise RuntimeError(
            "Negative signed subgroup count cells found; refusing to "
            f"clip or drop them:\n{examples.to_string(index=False)}"
        )
    out["saldo"] = out["admissoes"] - out["desligamentos"]
    out["n_movimentacoes"] = (
        out["admissoes"] + out["desligamentos"]
    )
    out["asinh_saldo"] = np.arcsinh(out["saldo"])
    out["salario_medio_adm"] = np.where(
        out["admissoes"].gt(0),
        out["salario_soma_adm"] / out["admissoes"],
        np.nan,
    )
    out["salario_real_adm"] = (
        out["salario_medio_adm"] * 100.0 / out["indice"]
    )
    out["ln_salario_real_adm"] = np.log(
        out["salario_real_adm"]
    )
    return out


def _micro_panels(
    base: pd.DataFrame,
    actual: pd.DataFrame,
) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    support: list[dict[str, Any]] = []
    keys = ["cbo_4d", "periodo_num"]
    for dimension, specification in DIMENSIONS.items():
        if specification["kind"] != "micro":
            continue
        dimension_actual = actual.loc[
            actual["dimension"].eq(dimension)
        ].copy()
        totals = (
            dimension_actual.groupby(keys, as_index=False)[
                list(AGGREGATE_COLUMNS)
            ]
            .sum()
        )
        for group_id, group_label in specification["groups"]:
            target = dimension_actual.loc[
                dimension_actual["actual_group"].eq(group_id),
                [*keys, *AGGREGATE_COLUMNS],
            ].copy()
            values = totals.merge(
                target,
                on=keys,
                how="left",
                suffixes=("_total", "_target"),
                validate="one_to_one",
            )
            for column in AGGREGATE_COLUMNS:
                values[f"{column}_target"] = values[
                    f"{column}_target"
                ].fillna(0)
                values[f"{column}_complement"] = (
                    values[f"{column}_total"]
                    - values[f"{column}_target"]
                )
            comparison_frames = []
            for subgroup in ("target", "complement"):
                selected = values[
                    [
                        *keys,
                        *[
                            f"{column}_{subgroup}"
                            for column in AGGREGATE_COLUMNS
                        ],
                    ]
                ].copy()
                selected.columns = [*keys, *AGGREGATE_COLUMNS]
                selected["subgroup"] = subgroup
                comparison_frames.append(selected)
            values_long = pd.concat(
                comparison_frames,
                ignore_index=True,
            )
            panel = (
                base.merge(
                    values_long,
                    on=keys,
                    how="left",
                    validate="one_to_many",
                )
            )
            panel["subgroup"] = panel["subgroup"].fillna("target")
            missing_values = panel["admissoes"].isna()
            if missing_values.any():
                missing_base = base.loc[
                    ~base.set_index(keys).index.isin(
                        values_long.set_index(keys).index
                    )
                ].copy()
                missing_pair = pd.concat(
                    [
                        missing_base.assign(subgroup="target"),
                        missing_base.assign(subgroup="complement"),
                    ],
                    ignore_index=True,
                )
                for column in AGGREGATE_COLUMNS:
                    missing_pair[column] = 0
                panel = pd.concat(
                    [
                        panel.loc[~missing_values],
                        missing_pair,
                    ],
                    ignore_index=True,
                )
            for column in AGGREGATE_COLUMNS:
                panel[column] = panel[column].fillna(0)
            panel["dimension"] = dimension
            panel["group_id"] = group_id
            panel["group_label"] = group_label
            panel["group_indicator"] = (
                panel["subgroup"].eq("target").astype("int8")
            )
            panel["dimension_kind"] = "micro"
            panel = _derive_outcomes(panel)
            target_flow = panel.loc[
                panel["subgroup"].eq("target")
                & (
                    panel["admissoes"].gt(0)
                    | panel["desligamentos"].gt(0)
                )
            ]
            support.append(
                _support_record(
                    panel,
                    target_flow,
                    dimension,
                    group_id,
                    group_label,
                    "micro",
                )
            )
            frames.append(panel)
    return frames, support


def _income_panels(
    base: pd.DataFrame,
    national: pd.DataFrame,
    medians: pd.DataFrame,
) -> tuple[list[pd.DataFrame], list[dict[str, Any]]]:
    assignments = medians.copy()
    assignments["cbo_4d"] = (
        assignments["cbo_4d"].astype(str).str.zfill(4)
    )
    assignments["income_group"] = assignments[
        "median_pre_wage_sm"
    ].apply(income_group)
    source = national.loc[
        national["included_main"].eq(True)
    ].copy()
    source["cbo_4d"] = source["cbo_4d"].astype(str).str.zfill(4)
    source = source.merge(
        assignments,
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    frames: list[pd.DataFrame] = []
    support: list[dict[str, Any]] = []
    for group_id, group_label in DIMENSIONS["income"]["groups"]:
        panel = source.copy()
        panel["dimension"] = "income"
        panel["group_id"] = group_id
        panel["group_label"] = group_label
        panel["group_indicator"] = (
            panel["income_group"].eq(group_id).astype("int8")
        )
        panel["subgroup"] = np.where(
            panel["group_indicator"].eq(1),
            "target",
            "complement",
        )
        panel["dimension_kind"] = "cbo_predetermined"
        panel["salario_soma_adm"] = (
            panel["salario_medio_adm"] * panel["admissoes"]
        )
        target_flow = panel.loc[
            panel["group_indicator"].eq(1)
            & (
                panel["admissoes"].gt(0)
                | panel["desligamentos"].gt(0)
            )
        ]
        support.append(
            _support_record(
                panel,
                target_flow,
                "income",
                group_id,
                group_label,
                "cbo_predetermined",
            )
        )
        frames.append(panel)
    return frames, support


def _support_record(
    panel: pd.DataFrame,
    target_flow: pd.DataFrame,
    dimension: str,
    group_id: str,
    group_label: str,
    dimension_kind: str,
) -> dict[str, Any]:
    treated = target_flow.loc[
        target_flow["treated_main"].eq(1),
        "cbo_4d",
    ].nunique()
    control = target_flow.loc[
        target_flow["treated_main"].eq(0),
        "cbo_4d",
    ].nunique()
    if treated >= 20 and control >= 50:
        support_status = "adequate"
    elif treated >= 10 and control >= 25:
        support_status = "limited"
    else:
        support_status = "thin"
    return {
        "dimension": dimension,
        "dimension_kind": dimension_kind,
        "group_id": group_id,
        "group_label": group_label,
        "panel_cells": int(len(panel)),
        "target_cells_with_flows": int(len(target_flow)),
        "target_treated_cbo_with_flows": int(treated),
        "target_control_cbo_with_flows": int(control),
        "support_status": support_status,
        "negative_admission_cells": int(
            panel["admissoes"].lt(0).sum()
        ),
        "negative_separation_cells": int(
            panel["desligamentos"].lt(0).sum()
        ),
    }


def build_ddd_panel(
    national: pd.DataFrame,
    actual: pd.DataFrame,
    medians: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    national = national.copy()
    national["cbo_4d"] = (
        national["cbo_4d"].astype(str).str.zfill(4)
    )
    base = national.loc[
        national["included_main"].eq(True),
        [
            "cbo_4d",
            "periodo_num",
            "periodo",
            "post",
            "treated_main",
            "indice",
        ],
    ].copy()
    micro_frames, micro_support = _micro_panels(base, actual)
    income_frames, income_support = _income_panels(
        base,
        national,
        medians,
    )
    panel = pd.concat(
        [*micro_frames, *income_frames],
        ignore_index=True,
        sort=False,
    )
    panel["post"] = panel["post"].astype("int8")
    panel["treatment"] = panel["treated_main"].astype("int8")
    panel["group_indicator"] = panel[
        "group_indicator"
    ].astype("int8")
    panel["post_treat"] = panel["post"] * panel["treatment"]
    panel["post_group"] = (
        panel["post"] * panel["group_indicator"]
    )
    panel["treat_group"] = (
        panel["treatment"] * panel["group_indicator"]
    )
    panel["post_treat_group"] = (
        panel["post"]
        * panel["treatment"]
        * panel["group_indicator"]
    )
    validate_ddd_formula_terms(
        [
            "post_treat_group",
            "post_treat",
            "post_group",
            "treat_group",
        ]
    )
    support = pd.DataFrame(
        [*micro_support, *income_support]
    ).sort_values(["dimension", "group_id"])
    if len(support) != 20:
        raise RuntimeError("DDD support grid must contain 20 groups")
    return panel, support.reset_index(drop=True)


def run_ddd_models(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dimension, specification in DIMENSIONS.items():
        for group_id, group_label in specification["groups"]:
            sample = panel.loc[
                panel["dimension"].eq(dimension)
                & panel["group_id"].eq(group_id)
            ].copy()
            fixed_effects = (
                ("cbo_4d", "periodo", "subgroup")
                if specification["kind"] == "micro"
                else ("cbo_4d", "periodo")
            )
            controls, absorbed_lower_terms = estimable_lower_terms(
                specification["kind"]
            )
            for outcome, estimator in OUTCOMES:
                model_id = f"{dimension}__{group_id}__{outcome}"
                try:
                    result, _ = fit_model(
                        sample,
                        model_id=model_id,
                        outcome=outcome,
                        treatment_term=DDD_TREATMENT_TERM,
                        estimator=estimator,
                        fixed_effects=fixed_effects,
                        cluster_variables=("cbo_4d",),
                        controls=controls,
                        principal=False,
                        separation_check=("fe",),
                    )
                    result_status = "estimated"
                    error = ""
                except Exception as exception:  # noqa: BLE001
                    result = {
                        "model_id": model_id,
                        "outcome": outcome,
                        "estimator": estimator,
                        "term": DDD_TREATMENT_TERM,
                        "coefficient": np.nan,
                        "standard_error": np.nan,
                        "p_value": np.nan,
                        "n_obs": np.nan,
                        "cluster_counts": "",
                        "converged": False,
                        "formula": "",
                    }
                    result_status = "failed_estimation"
                    error = str(exception)
                nominal = result.pop("p_value")
                result.update(
                    {
                        "dimension": dimension,
                        "dimension_kind": specification["kind"],
                        "group_id": group_id,
                        "group_label": group_label,
                        "result_status": result_status,
                        "error": error,
                        "nominal_p_value": nominal,
                        "declared_ddd_terms": json.dumps(
                            [
                                DDD_TREATMENT_TERM,
                                *DDD_LOWER_TERMS,
                            ]
                        ),
                        "absorbed_lower_terms": " + ".join(
                            absorbed_lower_terms
                        ),
                        "full_formula_contract": (
                            f"{outcome} ~ {DDD_TREATMENT_TERM} + "
                            f"{' + '.join(DDD_LOWER_TERMS)} | "
                            f"{' + '.join(fixed_effects)}"
                        ),
                    }
                )
                rows.append(result)
    results = pd.DataFrame(rows)
    if len(results) != PLANNED_FAMILY_SIZE:
        raise RuntimeError("DDD result grid must contain 100 rows")
    results["bh_adjusted_p_value"] = benjamini_hochberg(
        results["nominal_p_value"].to_numpy(),
        family_size=PLANNED_FAMILY_SIZE,
    )
    results["nominal_significant_005"] = (
        results["nominal_p_value"] < 0.05
    )
    results["bh_significant_005"] = (
        results["bh_adjusted_p_value"] < 0.05
    )
    return results


def render_report(
    results: pd.DataFrame,
    support: pd.DataFrame,
) -> str:
    estimated = results.loc[
        results["result_status"].eq("estimated")
    ]
    lines = [
        "# DDD multiplicity results",
        "",
        "The frozen family contains 100 planned target-versus-complement "
        "DDD contrasts. Every formula includes `post × treatment × "
        "subgroup` and all three lower-order two-way interactions. "
        "Nominal and global Benjamini-Hochberg p-values are reported "
        "side by side.",
        "",
        f"- Estimated models: {len(estimated)} / 100",
        f"- Nominal p < 0.05: "
        f"{int(estimated['nominal_significant_005'].sum())}",
        f"- BH-adjusted p < 0.05: "
        f"{int(estimated['bh_significant_005'].sum())}",
        f"- Thin-support groups: "
        f"{int(support['support_status'].eq('thin').sum())}",
        "",
        "## Support",
        "",
        "| Dimension | Group | Treated CBOs with target flows | "
        "Control CBOs with target flows | Support | Cells |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in support.itertuples():
        lines.append(
            f"| {row.dimension} | {row.group_id} | "
            f"{row.target_treated_cbo_with_flows} | "
            f"{row.target_control_cbo_with_flows} | "
            f"{row.support_status} | {row.panel_cells:,} |"
        )
    lines.extend(
        [
            "",
            "The BH adjustment uses the preregistered planned family "
            "size of 100 even if a model is non-estimable. These DDDs "
            "do not repair the failed national pretrend diagnostics.",
            "",
        ]
    )
    return "\n".join(lines)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and estimate the frozen 100-test DDD family."
    )
    parser.add_argument(
        "--movements-glob",
        type=Path,
        default=DEFAULT_MOVEMENTS,
    )
    parser.add_argument(
        "--national-panel",
        type=Path,
        default=DEFAULT_NATIONAL_PANEL,
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--scratch-parent",
        type=Path,
        default=DEFAULT_SCRATCH,
    )
    parser.add_argument(
        "--models-only",
        action="store_true",
        help="Reuse the frozen derived DDD panel and support table.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.models_only:
        panel = pd.read_parquet(args.panel)
        support = pd.read_csv(args.support)
    else:
        national = pd.read_parquet(args.national_panel)
        actual, medians = aggregate_signed_groups(
            args.movements_glob,
            scratch_parent=args.scratch_parent,
        )
        panel, support = build_ddd_panel(national, actual, medians)
        _atomic_parquet(panel, args.panel)
        _atomic_csv(support, args.support)
    print(
        f"support_written={args.support} groups={len(support)}",
        flush=True,
    )
    results = run_ddd_models(panel)
    results = results.merge(
        support[
            [
                "dimension",
                "group_id",
                "support_status",
                "target_treated_cbo_with_flows",
                "target_control_cbo_with_flows",
            ]
        ],
        on=["dimension", "group_id"],
        how="left",
        validate="many_to_one",
    )
    _atomic_csv(results, args.results)
    _atomic_text(render_report(results, support), args.report)
    summary = {
        "planned_family_size": PLANNED_FAMILY_SIZE,
        "estimated_models": int(
            results["result_status"].eq("estimated").sum()
        ),
        "failed_models": int(
            results["result_status"].ne("estimated").sum()
        ),
        "nominal_p_lt_005": int(
            results["nominal_significant_005"].sum()
        ),
        "bh_adjusted_p_lt_005": int(
            results["bh_significant_005"].sum()
        ),
        "multiplicity_method": "Benjamini-Hochberg",
        "family_size_in_adjustment": PLANNED_FAMILY_SIZE,
        "panel_rows": int(len(panel)),
        "panel_bytes": int(args.panel.stat().st_size),
        "panel_sha256": _sha256(args.panel),
        "negative_count_cells": int(
            panel["admissoes"].lt(0).sum()
            + panel["desligamentos"].lt(0).sum()
        ),
        "adequate_support_groups": int(
            support["support_status"].eq("adequate").sum()
        ),
        "limited_support_groups": int(
            support["support_status"].eq("limited").sum()
        ),
        "thin_support_groups": int(
            support["support_status"].eq("thin").sum()
        ),
        "all_formulas_have_complete_ddd_terms": True,
    }
    _atomic_json(summary, args.summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
