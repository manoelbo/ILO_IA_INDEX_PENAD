#!/usr/bin/env python3
"""Build the corrected CBO4-by-municipality-by-month Anatel panel.

This script reads only the signed V2 movement partitions and the frozen inputs
inside this front. It never reads the legacy municipal panels or connectivity
file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd


V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
FRONT_DIR = Path(__file__).resolve().parents[1]
COMMON_DIR = V2_ROOT / "code" / "common"
PANEL_DIR = V2_ROOT / "code" / "caged" / "panel"
for path in (COMMON_DIR, PANEL_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_panel import _configure_connection  # noqa: E402
from merge_audit import audited_merge  # noqa: E402
from paths import portable_path  # noqa: E402


START_PERIOD = 202101
END_PERIOD = 202605
TRUE_PRE_END = 202211
TREATMENT_PERIOD = 202212
MIN_POPULATION = 50_000
MIN_PRE_MOVEMENTS = 5
WAGE_MIN = 0.0
WAGE_MAX = 1_000_000.0

MOVEMENTS_GLOB = (
    V2_ROOT
    / "data"
    / "interim"
    / "movimentacoes"
    / "competenciamov=*"
    / "part.parquet"
)
CLASSIFICATION_PATH = (
    V2_ROOT / "data" / "derived" / "cbo_treatment_classification.csv"
)
IPCA_PATH = V2_ROOT / "data" / "derived" / "ipca_mensal.parquet"
CONNECTIVITY_PATH = FRONT_DIR / "data" / "anatel_pre_treatment.csv"
PANEL_PATH = FRONT_DIR / "data" / "painel_anatel.parquet"
SUPPORT_CSV = FRONT_DIR / "results" / "painel_anatel_support.csv"
SUPPORT_JSON = FRONT_DIR / "results" / "painel_anatel_support.json"
LATE_DECLARATION_PATH = (
    FRONT_DIR / "results" / "anatel_late_declaration_by_municipality.csv"
)
LATE_BY_CONNECTIVITY_PATH = (
    FRONT_DIR / "results" / "anatel_late_declaration_by_connectivity.csv"
)


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_parquet(temporary, index=False, compression="zstd")
    os.replace(temporary, path)


def prepare_treatment_classification(
    classification: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply the signed 75 exposed versus 266 Not Exposed assignment."""
    required = {"cbo_4d", "cbo_ilo_gradient"}
    missing = sorted(required - set(classification.columns))
    if missing:
        raise ValueError(f"Treatment classification is missing: {missing}")
    source = classification.copy()
    source["cbo_4d"] = source["cbo_4d"].astype(str).str.zfill(4)
    if source["cbo_4d"].duplicated().any():
        raise RuntimeError("Treatment classification has duplicate CBO4 codes")
    exposed = source["cbo_ilo_gradient"].astype(str).str.startswith(
        "Exposed:"
    )
    control = source["cbo_ilo_gradient"].eq("Not Exposed")
    included = source.loc[
        exposed | control,
        ["cbo_4d", "cbo_ilo_gradient"],
    ].copy()
    included["treated"] = exposed.loc[included.index].astype("int8")
    included = included.sort_values("cbo_4d").reset_index(drop=True)
    support = {
        "classification_cbo": int(len(source)),
        "included_cbo": int(len(included)),
        "included_exposed_cbo": int(included["treated"].sum()),
        "included_not_exposed_cbo": int(included["treated"].eq(0).sum()),
        "excluded_cbo": int(len(source) - len(included)),
        "excluded_labels": sorted(
            source.loc[
                ~(exposed | control), "cbo_ilo_gradient"
            ].astype(str).unique().tolist()
        ),
    }
    return included, support


def _municipality_crosswalk(
    connectivity: pd.DataFrame,
) -> pd.DataFrame:
    required = {"id_municipio"}
    missing = sorted(required - set(connectivity.columns))
    if missing:
        raise ValueError(f"Connectivity is missing: {missing}")
    crosswalk = connectivity[["id_municipio"]].copy()
    crosswalk["id_municipio"] = (
        crosswalk["id_municipio"].astype(str).str.strip()
    )
    if not crosswalk["id_municipio"].str.fullmatch(r"\d{7}").all():
        raise RuntimeError("Anatel municipality identifiers must have 7 digits")
    crosswalk["municipio_caged_6d"] = crosswalk[
        "id_municipio"
    ].str[:6]
    if crosswalk["municipio_caged_6d"].duplicated().any():
        duplicates = sorted(
            crosswalk.loc[
                crosswalk["municipio_caged_6d"].duplicated(False),
                "municipio_caged_6d",
            ].unique().tolist()
        )
        raise RuntimeError(
            f"IBGE 6-to-7 digit crosswalk is not unique: {duplicates[:10]}"
        )
    return crosswalk


def map_caged_municipalities(
    panel: pd.DataFrame,
    connectivity: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Map the six-digit CAGED code to the seven-digit IBGE identifier."""
    if "municipio_caged_6d" not in panel.columns:
        raise ValueError("Panel is missing municipio_caged_6d")
    source = panel.copy()
    source["municipio_caged_6d"] = (
        source["municipio_caged_6d"].astype(str).str.strip()
    )
    crosswalk = _municipality_crosswalk(connectivity)
    merged = audited_merge(
        source,
        crosswalk,
        merge_id="a4_caged_six_to_ibge_seven",
        validate="many_to_one",
        on="municipio_caged_6d",
        how="left",
    )
    unmatched = sorted(
        merged.loc[
            merged["id_municipio"].isna(), "municipio_caged_6d"
        ].unique().tolist()
    )
    matched = merged.loc[merged["id_municipio"].notna()].copy()
    support = {
        "input_rows": int(len(source)),
        "matched_rows": int(len(matched)),
        "unmatched_rows": int(len(source) - len(matched)),
        "input_caged_codes": int(source["municipio_caged_6d"].nunique()),
        "matched_caged_codes": int(
            matched["municipio_caged_6d"].nunique()
        ),
        "unmatched_caged_codes": unmatched,
        "mapping_rule": (
            "municipio_caged_6d equals the first six digits of the frozen "
            "seven-digit IBGE municipality identifier; no zero padding"
        ),
    }
    return matched, support


def filter_estimation_sample(
    panel: pd.DataFrame,
    *,
    minimum_population: int = MIN_POPULATION,
    minimum_pre_movements: int = MIN_PRE_MOVEMENTS,
    pre_end: int = TRUE_PRE_END,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply the signed population and pre-cell movement support filters."""
    required = {
        "cbo_4d",
        "id_municipio",
        "periodo_num",
        "populacao",
        "n_movimentacoes",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Sample filtering is missing columns: {missing}")
    population = pd.to_numeric(panel["populacao"], errors="raise")
    after_population = panel.loc[
        population.ge(minimum_population)
    ].copy()
    pre_support = (
        after_population.loc[
            after_population["periodo_num"].le(pre_end)
        ]
        .groupby(["cbo_4d", "id_municipio"], as_index=False)[
            "n_movimentacoes"
        ]
        .sum()
        .rename(columns={"n_movimentacoes": "pre_movements_cell"})
    )
    attached = audited_merge(
        after_population,
        pre_support,
        merge_id="a4_pre_cell_movement_support",
        validate="many_to_one",
        on=["cbo_4d", "id_municipio"],
        how="left",
    )
    result = attached.loc[
        pd.to_numeric(
            attached["pre_movements_cell"], errors="coerce"
        ).ge(minimum_pre_movements)
    ].copy()
    support = {
        "minimum_population": int(minimum_population),
        "minimum_pre_movements": int(minimum_pre_movements),
        "pre_support_end": int(pre_end),
        "rows_input": int(len(panel)),
        "rows_after_population": int(len(after_population)),
        "rows_after_pre_cell": int(len(result)),
        "cells_after_population": int(
            after_population[
                ["cbo_4d", "id_municipio"]
            ].drop_duplicates().shape[0]
        ),
        "cells_after_pre_cell": int(
            result[
                ["cbo_4d", "id_municipio"]
            ].drop_duplicates().shape[0]
        ),
    }
    return result, support


def assign_connectivity_split(
    panel: pd.DataFrame,
    *,
    connectivity_column: str = "penetracao_bl",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Split unique surviving municipalities at their within-sample median."""
    required = {"id_municipio", connectivity_column}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Connectivity split is missing columns: {missing}")
    municipality = panel[
        ["id_municipio", connectivity_column]
    ].drop_duplicates()
    if municipality["id_municipio"].duplicated().any():
        raise RuntimeError(
            "Connectivity must be constant within surviving municipality"
        )
    values = pd.to_numeric(
        municipality[connectivity_column],
        errors="raise",
    )
    if values.isna().any():
        raise RuntimeError("Connectivity is missing for a municipality")
    threshold = float(values.median())
    municipality["high_connectivity"] = values.gt(threshold).astype("int8")
    out = audited_merge(
        panel.drop(columns=["high_connectivity"], errors="ignore"),
        municipality[["id_municipio", "high_connectivity"]],
        merge_id="a4_within_sample_connectivity_split",
        validate="many_to_one",
        on="id_municipio",
        how="left",
    )
    total = int(len(municipality))
    high = int(municipality["high_connectivity"].sum())
    low = total - high
    support = {
        "threshold": threshold,
        "municipalities_total": total,
        "municipalities_high": high,
        "municipalities_low": low,
        "high_share": high / total,
        "low_share": low / total,
        "minimum_low_share": 0.30,
        "passes_minimum_low_share": bool(low / total >= 0.30),
    }
    return out, support


def _aggregate_movements(
    classification: pd.DataFrame,
    connectivity: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Aggregate signed V2 movements after dimension-only semijoins."""
    eligible_municipalities = _municipality_crosswalk(
        connectivity.loc[
            pd.to_numeric(
                connectivity["populacao"], errors="raise"
            ).ge(MIN_POPULATION)
        ]
    )[["municipio_caged_6d"]]
    eligible_cbo = classification[["cbo_4d"]].copy()
    FRONT_DIR.joinpath("data").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="a4-duckdb-",
        dir=FRONT_DIR / "data",
    ) as temporary_name:
        temporary = Path(temporary_name)
        aggregate_path = temporary / "caged_municipal_aggregate.parquet"
        connection = duckdb.connect()
        try:
            _configure_connection(connection, temporary)
            connection.register("eligible_cbo_input", eligible_cbo)
            connection.register(
                "eligible_municipality_input",
                eligible_municipalities,
            )
            source = _sql_literal(MOVEMENTS_GLOB)
            connection.execute(
                f"""
                CREATE TEMP VIEW valid_movements AS
                SELECT
                    CAST(competenciamov AS INTEGER) AS periodo_num,
                    substring(
                        CAST(cbo2002ocupacao AS VARCHAR), 1, 4
                    ) AS cbo_4d,
                    trim(CAST(municipio AS VARCHAR))
                        AS municipio_caged_6d,
                    CAST(saldomovimentacao AS SMALLINT) AS movimento,
                    CAST(peso AS BIGINT) AS peso,
                    CAST(salario AS DOUBLE) AS salario
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
                      CAST(cbo2002ocupacao AS VARCHAR), 1, 4
                  ) <> '0000'
                  AND CAST(idade AS INTEGER) BETWEEN 14 AND 90
                  AND CAST(salario AS DOUBLE) > {WAGE_MIN}
                  AND CAST(salario AS DOUBLE) < {WAGE_MAX}
                  AND CAST(saldomovimentacao AS INTEGER) IN (-1, 1)
                  AND CAST(peso AS INTEGER) IN (-1, 1)
                """
            )
            observed_codes = connection.execute(
                """
                SELECT DISTINCT municipio_caged_6d
                FROM valid_movements
                ORDER BY municipio_caged_6d
                """
            ).df()
            _, mapping_support = map_caged_municipalities(
                observed_codes,
                connectivity,
            )
            connection.execute(
                """
                CREATE TEMP TABLE wage_bounds AS
                SELECT
                    cbo_4d,
                    CAST(floor(periodo_num / 100) AS INTEGER) AS ano,
                    approx_quantile(salario, 0.01) AS wage_p01,
                    approx_quantile(salario, 0.99) AS wage_p99
                FROM valid_movements
                WHERE peso = 1
                  AND cbo_4d IN (
                      SELECT cbo_4d FROM eligible_cbo_input
                  )
                GROUP BY cbo_4d, ano
                """
            )
            output = _sql_literal(aggregate_path)
            connection.execute(
                f"""
                COPY (
                    WITH eligible AS (
                        SELECT movement.*
                        FROM valid_movements AS movement
                        WHERE movement.cbo_4d IN (
                            SELECT cbo_4d FROM eligible_cbo_input
                        )
                          AND movement.municipio_caged_6d IN (
                            SELECT municipio_caged_6d
                            FROM eligible_municipality_input
                        )
                    ),
                    winsorized AS (
                        SELECT
                            movement.*,
                            greatest(
                                bounds.wage_p01,
                                least(
                                    movement.salario,
                                    bounds.wage_p99
                                )
                            ) AS salario_winsor
                        FROM eligible AS movement
                        INNER JOIN wage_bounds AS bounds
                          ON movement.cbo_4d = bounds.cbo_4d
                         AND CAST(
                             floor(movement.periodo_num / 100)
                             AS INTEGER
                         ) = bounds.ano
                    ),
                    totals AS (
                        SELECT
                            cbo_4d,
                            municipio_caged_6d,
                            periodo_num,
                            CAST(sum(
                                CASE
                                    WHEN movimento = 1 THEN peso
                                    ELSE 0
                                END
                            ) AS BIGINT) AS admissoes,
                            CAST(sum(
                                CASE
                                    WHEN movimento = -1 THEN peso
                                    ELSE 0
                                END
                            ) AS BIGINT) AS desligamentos,
                            sum(
                                CASE
                                    WHEN movimento = 1
                                    THEN peso * salario_winsor
                                    ELSE 0
                                END
                            ) AS salario_soma_adm
                        FROM winsorized
                        GROUP BY
                            cbo_4d,
                            municipio_caged_6d,
                            periodo_num
                    )
                    SELECT
                        cbo_4d,
                        municipio_caged_6d,
                        CAST(
                            floor(periodo_num / 100) AS INTEGER
                        ) AS ano,
                        CAST(periodo_num % 100 AS INTEGER) AS mes,
                        periodo_num,
                        admissoes,
                        desligamentos,
                        admissoes + desligamentos AS n_movimentacoes,
                        CASE
                            WHEN admissoes > 0
                            THEN salario_soma_adm / admissoes
                        END AS salario_medio_adm
                    FROM totals
                    WHERE admissoes >= 0
                      AND desligamentos >= 0
                      AND (admissoes > 0 OR desligamentos > 0)
                    ORDER BY
                        cbo_4d,
                        municipio_caged_6d,
                        periodo_num
                )
                TO {output}
                (FORMAT PARQUET, COMPRESSION ZSTD)
                """
            )
            aggregate = pd.read_parquet(aggregate_path)
        finally:
            connection.close()
    mapping_support["eligible_population_municipalities"] = int(
        len(eligible_municipalities)
    )
    return aggregate, mapping_support


def _attach_dimensions(
    aggregate: pd.DataFrame,
    classification: pd.DataFrame,
    connectivity: pd.DataFrame,
    ipca: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    panel = audited_merge(
        aggregate,
        classification,
        merge_id="a4_treatment_classification",
        validate="many_to_one",
        on="cbo_4d",
        how="left",
    )
    if panel["treated"].isna().any():
        raise RuntimeError("An included CBO4 lacks treatment assignment")
    panel, mapping_support = map_caged_municipalities(
        panel,
        connectivity,
    )
    connectivity_columns = [
        "id_municipio",
        "penetracao_bl",
        "densidade_oficial",
        "pct_fibra",
        "pct_fiber_technology_check",
        "high_connectivity_old_national",
        "populacao",
        "domicilios",
    ]
    panel = audited_merge(
        panel,
        connectivity[connectivity_columns],
        merge_id="a4_frozen_anatel_connectivity",
        validate="many_to_one",
        on="id_municipio",
        how="left",
    )
    if panel[connectivity_columns[1:]].isna().any().any():
        raise RuntimeError("Frozen connectivity merge produced missing values")
    ipca_input = ipca[["ano", "mes", "indice"]].copy()
    panel = audited_merge(
        panel,
        ipca_input,
        merge_id="a4_v2_ipca",
        validate="many_to_one",
        on=["ano", "mes"],
        how="left",
    )
    if panel["indice"].isna().any() or panel["indice"].le(0).any():
        raise RuntimeError("IPCA merge produced missing or invalid indices")
    return panel, mapping_support


def _add_analysis_columns(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["treated"] = out["treated"].astype("int8")
    out["high_connectivity"] = out["high_connectivity"].astype("int8")
    out["high_connectivity_old_national"] = out[
        "high_connectivity_old_national"
    ].astype("int8")
    out["periodo"] = (
        out["ano"].astype(int).astype(str)
        + "-"
        + out["mes"].astype(int).astype(str).str.zfill(2)
    )
    out["post"] = out["periodo_num"].ge(TREATMENT_PERIOD).astype("int8")
    out["event_time"] = (
        (out["ano"].astype(int) - 2022) * 12
        + out["mes"].astype(int)
        - 12
    ).astype("int16")
    out["ln_admissoes"] = np.log1p(out["admissoes"].astype(float))
    out["ln_desligamentos"] = np.log1p(
        out["desligamentos"].astype(float)
    )
    out["saldo"] = out["admissoes"] - out["desligamentos"]
    out["asinh_saldo"] = np.arcsinh(out["saldo"].astype(float))
    out["salario_real_adm"] = (
        out["salario_medio_adm"] * (100.0 / out["indice"])
    )
    positive_wage = (
        out["admissoes"].gt(0)
        & out["salario_real_adm"].gt(0)
    )
    out["ln_salario_real_adm"] = np.log(
        out["salario_real_adm"].where(positive_wage)
    )
    out["uf_code"] = out["id_municipio"].astype(str).str[:2]
    out["cbo_municipio"] = (
        out["cbo_4d"].astype(str)
        + "_"
        + out["id_municipio"].astype(str)
    )
    out["cbo_periodo"] = (
        out["cbo_4d"].astype(str) + "_" + out["periodo"]
    )
    out["uf_periodo"] = out["uf_code"] + "_" + out["periodo"]
    split_columns = {
        "": "high_connectivity",
        "_old_cut": "high_connectivity_old_national",
    }
    for suffix, high_column in split_columns.items():
        out[f"post_treated{suffix}"] = (
            out["post"] * out["treated"]
        ).astype("int8")
        out[f"post_high{suffix}"] = (
            out["post"] * out[high_column]
        ).astype("int8")
        out[f"treated_high{suffix}"] = (
            out["treated"] * out[high_column]
        ).astype("int8")
        out[f"stage0_triple{suffix}"] = (
            out["post"] * out["treated"] * out[high_column]
        ).astype("int8")
    return out


def _cut_support_rows(
    panel: pd.DataFrame,
    corrected_support: dict[str, Any],
) -> pd.DataFrame:
    municipalities = panel[
        [
            "id_municipio",
            "high_connectivity_old_national",
            "high_connectivity",
        ]
    ].drop_duplicates()
    if municipalities["id_municipio"].duplicated().any():
        raise RuntimeError("Municipality cut assignments are not constant")
    old_high = int(
        municipalities["high_connectivity_old_national"].sum()
    )
    old_total = int(len(municipalities))
    old_low = old_total - old_high
    common = {
        "panel_rows": int(len(panel)),
        "cbo": int(panel["cbo_4d"].nunique()),
        "periods": int(panel["periodo_num"].nunique()),
    }
    return pd.DataFrame(
        [
            {
                "construction": "legacy_reported_v1",
                "threshold": np.nan,
                "municipalities": 657,
                "high_municipalities": 529,
                "low_municipalities": 128,
                "high_share": 529 / 657,
                "low_share": 128 / 657,
                **common,
            },
            {
                "construction": "corrected_v2_old_national_cut",
                "threshold": np.nan,
                "municipalities": old_total,
                "high_municipalities": old_high,
                "low_municipalities": old_low,
                "high_share": old_high / old_total,
                "low_share": old_low / old_total,
                **common,
            },
            {
                "construction": "corrected_v2_within_sample_cut",
                "threshold": corrected_support["threshold"],
                "municipalities": corrected_support[
                    "municipalities_total"
                ],
                "high_municipalities": corrected_support[
                    "municipalities_high"
                ],
                "low_municipalities": corrected_support[
                    "municipalities_low"
                ],
                "high_share": corrected_support["high_share"],
                "low_share": corrected_support["low_share"],
                **common,
            },
        ]
    )


def _late_declarations_by_connectivity(
    panel: pd.DataFrame,
    late_declarations: pd.DataFrame,
) -> pd.DataFrame:
    assignments = panel[
        [
            "municipio_caged_6d",
            "id_municipio",
            "high_connectivity",
            "high_connectivity_old_national",
        ]
    ].drop_duplicates()
    if assignments["municipio_caged_6d"].duplicated().any():
        raise RuntimeError("Late-declaration municipality assignment repeats")
    late = late_declarations.copy()
    late["municipio_caged_6d"] = (
        late["municipio_caged_6d"].astype(str).str.strip()
    )
    attached = audited_merge(
        assignments,
        late,
        merge_id="a4_late_declarations_by_connectivity",
        validate="one_to_many",
        on="municipio_caged_6d",
        how="left",
    )
    if attached["ano"].isna().any():
        raise RuntimeError("A surviving municipality lacks A2 diagnostics")
    rows: list[pd.DataFrame] = []
    for cut, column in (
        ("old_national", "high_connectivity_old_national"),
        ("within_sample", "high_connectivity"),
    ):
        grouped = (
            attached.groupby(["ano", column], as_index=False)[
                [
                    "mov_liquido",
                    "for_liquido",
                    "exc_liquido",
                    "flag_liquido",
                    "total_liquido",
                ]
            ]
            .sum()
            .rename(columns={column: "high_connectivity"})
        )
        grouped["cut"] = cut
        grouped["connectivity_group"] = np.where(
            grouped["high_connectivity"].eq(1), "high", "low"
        )
        grouped["share_for"] = grouped["for_liquido"] / (
            grouped["mov_liquido"] + grouped["for_liquido"]
        )
        grouped["share_flag"] = (
            grouped["flag_liquido"] / grouped["total_liquido"]
        )
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True).sort_values(
        ["cut", "ano", "high_connectivity"]
    )


def build_panel() -> dict[str, Any]:
    classification_source = pd.read_csv(
        CLASSIFICATION_PATH,
        dtype={"cbo_4d": str},
    )
    classification, classification_support = (
        prepare_treatment_classification(classification_source)
    )
    if (
        classification_support["included_exposed_cbo"] != 75
        or classification_support["included_not_exposed_cbo"] != 266
    ):
        raise RuntimeError(
            "Signed treatment family must contain 75 exposed and "
            "266 Not Exposed CBO4 codes"
        )
    connectivity = pd.read_csv(
        CONNECTIVITY_PATH,
        dtype={"id_municipio": str},
    )
    ipca = pd.read_parquet(IPCA_PATH)
    aggregate, source_mapping_support = _aggregate_movements(
        classification,
        connectivity,
    )
    panel, panel_mapping_support = _attach_dimensions(
        aggregate,
        classification,
        connectivity,
        ipca,
    )
    panel, sample_support = filter_estimation_sample(panel)
    panel, cut_support = assign_connectivity_split(panel)
    panel = _add_analysis_columns(panel)
    if set(panel["cbo_ilo_gradient"].unique()).difference(
        {
            "Not Exposed",
            "Exposed: Gradient 1",
            "Exposed: Gradient 2",
            "Exposed: Gradient 3",
        }
    ):
        raise RuntimeError("Panel retained a prohibited treatment class")
    if panel.duplicated(
        ["cbo_4d", "id_municipio", "periodo_num"]
    ).any():
        raise RuntimeError("Final panel has duplicate panel cells")
    support_table = _cut_support_rows(panel, cut_support)
    late = pd.read_csv(
        LATE_DECLARATION_PATH,
        dtype={"municipio_caged_6d": str},
    )
    late_by_connectivity = _late_declarations_by_connectivity(panel, late)
    support = {
        "status": "pass",
        "source": portable_path(MOVEMENTS_GLOB, relative_to=V2_ROOT),
        "legacy_municipal_panel_read": False,
        "legacy_connectivity_file_read": False,
        "treatment_coefficient_estimated": False,
        "period_start": START_PERIOD,
        "period_end": END_PERIOD,
        "true_pre_end": TRUE_PRE_END,
        "classification": classification_support,
        "source_municipality_mapping": source_mapping_support,
        "panel_municipality_mapping": panel_mapping_support,
        "sample_filters": sample_support,
        "connectivity_cut": cut_support,
        "panel": {
            "rows": int(len(panel)),
            "cbo": int(panel["cbo_4d"].nunique()),
            "municipalities": int(panel["id_municipio"].nunique()),
            "periods": int(panel["periodo_num"].nunique()),
            "cells": int(
                panel[
                    ["cbo_4d", "id_municipio"]
                ].drop_duplicates().shape[0]
            ),
            "treated_cbo": int(
                panel.loc[panel["treated"].eq(1), "cbo_4d"].nunique()
            ),
            "control_cbo": int(
                panel.loc[panel["treated"].eq(0), "cbo_4d"].nunique()
            ),
            "minimum_period": int(panel["periodo_num"].min()),
            "maximum_period": int(panel["periodo_num"].max()),
            "fiber_share_minimum": float(panel["pct_fibra"].min()),
            "fiber_share_maximum": float(panel["pct_fibra"].max()),
        },
        "interaction_terms_constructed_not_estimated": [
            "post_treated",
            "post_high",
            "treated_high",
            "stage0_triple",
            "post_treated_old_cut",
            "post_high_old_cut",
            "treated_high_old_cut",
            "stage0_triple_old_cut",
        ],
    }
    _atomic_parquet(panel, PANEL_PATH)
    _atomic_csv(support_table, SUPPORT_CSV)
    _atomic_csv(late_by_connectivity, LATE_BY_CONNECTIVITY_PATH)
    _atomic_json(support, SUPPORT_JSON)
    return support


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    support = build_panel()
    print(json.dumps(support, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
