#!/usr/bin/env python3
"""Build the preregistered PNADc Part 1 panels without COD4 cells."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


sys.dont_write_bytecode = True

FRONT_ROOT = Path(__file__).resolve().parents[1]
V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
VINTAGE_DIR = FRONT_ROOT / "data" / "vintage"
DATA_DIR = FRONT_ROOT / "data"
RESULTS_DIR = FRONT_ROOT / "results"
INDIVIDUAL_PANEL_PATH = DATA_DIR / "painel_pnadc_individual.parquet"
INDIVIDUAL_SUPPORT_PATH = (
    RESULTS_DIR / "painel_pnadc_individual_support.json"
)
COD3_PANEL_PATH = DATA_DIR / "painel_pnadc_cod3.parquet"
COD3_SUPPORT_PATH = RESULTS_DIR / "painel_pnadc_cod3_support.json"

sys.path.insert(0, str(V2_ROOT / "code" / "common"))

from .stage0 import (  # noqa: E402
    ILO_EXPECTED_SHA256,
    ILO_PATH,
    SECTION3_EXPECTED_POPULATION,
    SECTION3_EXPECTED_ROWS,
    atomic_json,
    attach_crosswalk,
    build_ilo_crosswalk,
    expected_periods,
    formal_indicator,
    section3_anchor,
    sha256_file,
)
from merge_audit import audited_merge  # noqa: E402


INDIVIDUAL_COLUMNS = (
    "ano",
    "trimestre",
    "periodo",
    "trimestre_num",
    "sigla_uf",
    "sexo",
    "idade",
    "raca_cor",
    "nivel_instrucao",
    "grupamento_atividade",
    "posicao_ocupacao",
    "rendimento_habitual",
    "horas_habituais",
    "peso",
    "cod3",
    "exposure_gradient",
    "treated",
    "post",
    "post_treat",
    "formal",
    "informal",
    "conta_propria",
    "ln_renda",
)

COD3_COLUMNS = (
    "ano",
    "trimestre",
    "periodo",
    "trimestre_num",
    "cod3",
    "ocupados_total",
    "ocupados_formais",
    "ocupados_informais",
    "treatment_status",
    "treated",
    "post",
    "post_treat",
)


def _promote_validated_parquet(
    partial_path: Path,
    final_path: Path,
    *,
    expected_rows: int,
) -> None:
    """Validate a temporary panel before atomically promoting it."""
    try:
        parquet = pq.ParquetFile(partial_path)
        if parquet.metadata.num_rows != expected_rows:
            raise RuntimeError(
                "Panel parquet row count mismatch before promotion"
            )
        forbidden = {"cod4", "cod_ocupacao"} & set(
            parquet.schema_arrow.names
        )
        if forbidden:
            raise RuntimeError(
                f"COD4 columns reached the parquet: {sorted(forbidden)}"
            )
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise
    os.replace(partial_path, final_path)


def quarter_number(year: int, quarter: int) -> int:
    """Return the one-based index for the 2012Q1--2026Q1 grid."""
    if quarter not in {1, 2, 3, 4}:
        raise ValueError(f"Invalid quarter: {quarter}")
    return (int(year) - 2012) * 4 + int(quarter)


def _normalized_position(values: pd.Series) -> pd.Series:
    return (
        values.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.lstrip("0")
        .replace("", pd.NA)
    )


def _coerce_individual_schema(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.loc[:, INDIVIDUAL_COLUMNS].copy()
    for column in (
        "periodo",
        "sigla_uf",
        "sexo",
        "raca_cor",
        "nivel_instrucao",
        "grupamento_atividade",
        "posicao_ocupacao",
        "cod3",
        "exposure_gradient",
    ):
        result[column] = result[column].astype("string")
    for column in ("ano", "trimestre", "trimestre_num"):
        result[column] = pd.to_numeric(
            result[column],
            errors="raise",
        ).astype("int16")
    result["idade"] = pd.to_numeric(
        result["idade"],
        errors="raise",
    ).astype("int16")
    for column in (
        "rendimento_habitual",
        "horas_habituais",
        "peso",
        "ln_renda",
    ):
        result[column] = pd.to_numeric(result[column], errors="coerce").astype(
            "float64"
        )
    for column in (
        "treated",
        "post",
        "post_treat",
        "formal",
        "informal",
        "conta_propria",
    ):
        result[column] = result[column].astype("int8")
    return result


def build_individual_quarter(
    raw: pd.DataFrame,
    crosswalk: pd.DataFrame,
    *,
    include_transition_as_pre: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Construct one row-level Arm A quarter from the frozen vintage."""
    periods = raw[["ano", "trimestre"]].drop_duplicates()
    if len(periods) != 1:
        raise ValueError("Individual input must contain exactly one quarter")
    year = int(periods.iloc[0]["ano"])
    quarter = int(periods.iloc[0]["trimestre"])
    if (year, quarter) == (2022, 4) and not include_transition_as_pre:
        raise ValueError("The transition quarter 2022Q4 must be excluded")

    matched = attach_crosswalk(raw, crosswalk)
    exposure = matched["exposure_gradient"].astype("string")
    minimal = exposure.eq("Minimal Exposure")
    unclassified = exposure.eq("Sem classificação")
    treated = exposure.str.startswith("Exposed:", na=False)
    control = exposure.eq("Not Exposed")
    panel = matched.loc[treated | control].copy()

    panel_exposure = panel["exposure_gradient"].astype("string")
    panel["cod3"] = panel["cod4"].astype("string").str[:3]
    panel["periodo"] = f"{year}Q{quarter}"
    panel["trimestre_num"] = quarter_number(year, quarter)
    panel["treated"] = panel_exposure.str.startswith(
        "Exposed:",
        na=False,
    ).astype("int8")
    panel["post"] = int((year, quarter) >= (2023, 1))
    panel["post_treat"] = panel["post"] * panel["treated"]
    panel["formal"] = formal_indicator(
        panel["posicao_ocupacao"]
    ).astype("int8")
    panel["informal"] = (1 - panel["formal"]).astype("int8")
    positions = _normalized_position(panel["posicao_ocupacao"])
    panel["conta_propria"] = positions.eq("9").astype("int8")
    income = pd.to_numeric(
        panel["rendimento_habitual"],
        errors="coerce",
    )
    panel["ln_renda"] = np.nan
    positive_income = income.gt(0)
    panel.loc[positive_income, "ln_renda"] = np.log(
        income.loc[positive_income]
    )
    panel = _coerce_individual_schema(panel)
    validate_individual_chunk(
        panel,
        include_transition_as_pre=include_transition_as_pre,
    )

    diagnostics = {
        "ano": year,
        "trimestre": quarter,
        "periodo": f"{year}Q{quarter}",
        "input_rows": int(len(raw)),
        "valid_occupation_rows": int(len(matched)),
        "panel_rows": int(len(panel)),
        "excluded_minimal_exposure_rows": int(minimal.sum()),
        "excluded_sem_classificacao_rows": int(unclassified.sum()),
    }
    return panel, diagnostics


def validate_individual_chunk(
    frame: pd.DataFrame,
    *,
    include_transition_as_pre: bool = False,
) -> dict[str, Any]:
    """Validate one or more individual-panel quarters."""
    forbidden = sorted(
        {"cod4", "cod_ocupacao"} & set(frame.columns)
    )
    if forbidden:
        raise ValueError(f"COD4 columns are forbidden in the panel: {forbidden}")
    missing = sorted(set(INDIVIDUAL_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Individual panel is missing columns: {missing}")
    if frame.empty:
        raise ValueError("Individual panel chunk is empty")
    if not frame["cod3"].astype("string").str.fullmatch(
        r"[0-9]{3}",
        na=False,
    ).all():
        raise ValueError("cod3 must contain exactly three digits")
    if frame["exposure_gradient"].isin(
        ["Minimal Exposure", "Sem classificação"]
    ).any():
        raise ValueError("Excluded exposure categories remain in the panel")
    expected_treated = frame["exposure_gradient"].astype(
        "string"
    ).str.startswith("Exposed:", na=False).astype("int8")
    if not frame["treated"].eq(expected_treated).all():
        raise ValueError("treated does not match the exposure gradient")
    if not (frame["formal"] + frame["informal"]).eq(1).all():
        raise ValueError("formal and informal must be exact complements")
    for column in (
        "treated",
        "post",
        "post_treat",
        "formal",
        "informal",
        "conta_propria",
    ):
        if not frame[column].isin([0, 1]).all():
            raise ValueError(f"{column} must be binary")
    if not frame["post_treat"].eq(
        frame["post"] * frame["treated"]
    ).all():
        raise ValueError("post_treat must equal post times treated")
    expected_numbers = (
        (frame["ano"].astype(int) - 2012) * 4
        + frame["trimestre"].astype(int)
    )
    if not frame["trimestre_num"].astype(int).eq(expected_numbers).all():
        raise ValueError("trimestre_num does not match the quarter grid")
    if (
        frame["ano"].eq(2022) & frame["trimestre"].eq(4)
    ).any() and not include_transition_as_pre:
        raise ValueError("The transition quarter 2022Q4 is present")
    expected_post = (
        frame["ano"].astype(int) * 10 + frame["trimestre"].astype(int)
    ).ge(20231).astype("int8")
    if not frame["post"].eq(expected_post).all():
        raise ValueError("post does not start in 2023Q1")
    weights = pd.to_numeric(frame["peso"], errors="coerce")
    if (~np.isfinite(weights) | weights.le(0)).any():
        raise ValueError("peso must be finite and strictly positive")
    income = pd.to_numeric(
        frame["rendimento_habitual"],
        errors="coerce",
    )
    invalid_income = income.isna() | income.le(0)
    if frame.loc[invalid_income, "ln_renda"].notna().any():
        raise ValueError("ln_renda must be missing for nonpositive income")
    positive = ~invalid_income
    if positive.any() and not np.allclose(
        frame.loc[positive, "ln_renda"],
        np.log(income.loc[positive]),
        rtol=0,
        atol=1e-12,
    ):
        raise ValueError("ln_renda does not equal log positive income")
    return {
        "rows": int(len(frame)),
        "weighted_population": float(weights.sum()),
        "cod3": int(frame["cod3"].nunique()),
        "quarters": int(
            frame[["ano", "trimestre"]].drop_duplicates().shape[0]
        ),
    }


def build_individual_panel() -> dict[str, Any]:
    """Execute P7 and publish the individual-panel support contract."""
    observed_hash = sha256_file(ILO_PATH)
    if observed_hash != ILO_EXPECTED_SHA256:
        raise RuntimeError(
            "ILO workbook SHA-256 mismatch: "
            f"expected {ILO_EXPECTED_SHA256}, observed {observed_hash}"
        )
    crosswalk = build_ilo_crosswalk(pd.read_excel(ILO_PATH))
    temp_path = INDIVIDUAL_PANEL_PATH.with_suffix(".parquet.partial")
    temp_path.unlink(missing_ok=True)

    writer: pq.ParquetWriter | None = None
    schema: pa.Schema | None = None
    total_rows = 0
    weighted_population = 0.0
    cod3_values: set[str] = set()
    quarters: list[str] = []
    exclusion_totals = {
        "excluded_minimal_exposure_rows": 0,
        "excluded_sem_classificacao_rows": 0,
    }
    groups = {
        "treated": {
            "rows": 0,
            "weighted_population": 0.0,
            "cod3": set(),
        },
        "control": {
            "rows": 0,
            "weighted_population": 0.0,
            "cod3": set(),
        },
    }

    try:
        for year, quarter in expected_periods():
            if (year, quarter) == (2022, 4):
                continue
            raw = pd.read_parquet(
                VINTAGE_DIR / f"pnadc_{year}q{quarter}.parquet"
            )
            panel, diagnostics = build_individual_quarter(raw, crosswalk)
            table = pa.Table.from_pandas(panel, preserve_index=False)
            if writer is None:
                schema = table.schema
                writer = pq.ParquetWriter(
                    temp_path,
                    schema,
                    compression="zstd",
                    use_dictionary=True,
                )
            elif table.schema != schema:
                table = table.cast(schema)
            writer.write_table(table)

            total_rows += len(panel)
            weighted_population += float(panel["peso"].sum())
            cod3_values.update(panel["cod3"].astype(str))
            quarters.append(str(diagnostics["periodo"]))
            for key in exclusion_totals:
                exclusion_totals[key] += int(diagnostics[key])
            for label, value in (("treated", 1), ("control", 0)):
                subset = panel.loc[panel["treated"].eq(value)]
                groups[label]["rows"] += int(len(subset))
                groups[label]["weighted_population"] += float(
                    subset["peso"].sum()
                )
                groups[label]["cod3"].update(
                    subset["cod3"].astype(str)
                )
    except Exception:
        if writer is not None:
            writer.close()
        temp_path.unlink(missing_ok=True)
        raise
    else:
        if writer is None:
            raise RuntimeError("No individual-panel rows were written")
        try:
            writer.close()
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
    expected_quarters = [
        f"{year}Q{quarter}"
        for year, quarter in expected_periods()
        if (year, quarter) != (2022, 4)
    ]
    if quarters != expected_quarters:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError("Individual-panel quarter grid is incomplete")
    _promote_validated_parquet(
        temp_path,
        INDIVIDUAL_PANEL_PATH,
        expected_rows=total_rows,
    )

    serializable_groups = {
        label: {
            "rows": int(values["rows"]),
            "weighted_population": float(
                values["weighted_population"]
            ),
            "cod3": int(len(values["cod3"])),
        }
        for label, values in groups.items()
    }
    status = {
        "status": "pass",
        "panel": str(INDIVIDUAL_PANEL_PATH.relative_to(FRONT_ROOT)),
        "sha256": sha256_file(INDIVIDUAL_PANEL_PATH),
        "bytes": int(INDIVIDUAL_PANEL_PATH.stat().st_size),
        "rows": int(total_rows),
        "weighted_population": float(weighted_population),
        "cod3": int(len(cod3_values)),
        "quarters": int(len(quarters)),
        "first_period": quarters[0],
        "last_period": quarters[-1],
        "excluded_transition_period": "2022Q4",
        "no_cod4_columns": True,
        "formal_informal_complement_violations": 0,
        "invalid_income_log_violations": 0,
        "groups": serializable_groups,
        **exclusion_totals,
        "treatment_coefficients_computed": False,
    }
    atomic_json(status, INDIVIDUAL_SUPPORT_PATH)
    return status


def _aggregate_cod3_counts(individual: pd.DataFrame) -> pd.DataFrame:
    required = {
        "ano",
        "trimestre",
        "periodo",
        "trimestre_num",
        "cod3",
        "peso",
        "formal",
        "informal",
    }
    missing = sorted(required - set(individual.columns))
    if missing:
        raise ValueError(f"Individual data is missing columns: {missing}")
    data = individual.copy()
    data["peso"] = pd.to_numeric(data["peso"], errors="raise")
    data["formal_weight"] = data["peso"] * data["formal"]
    data["informal_weight"] = data["peso"] * data["informal"]
    keys = [
        "ano",
        "trimestre",
        "periodo",
        "trimestre_num",
        "cod3",
    ]
    return (
        data.groupby(keys, as_index=False, observed=True)
        .agg(
            ocupados_total=("peso", "sum"),
            ocupados_formais=("formal_weight", "sum"),
            ocupados_informais=("informal_weight", "sum"),
        )
        .sort_values(["trimestre_num", "cod3"])
        .reset_index(drop=True)
    )


def _attach_cod3_treatment(
    aggregated: pd.DataFrame,
    treatment: pd.DataFrame,
) -> pd.DataFrame:
    required = {"cod3", "treatment_status", "treated_cod3"}
    missing = sorted(required - set(treatment.columns))
    if missing:
        raise ValueError(f"Treatment data is missing columns: {missing}")
    treatment_contract = treatment[
        ["cod3", "treatment_status", "treated_cod3"]
    ].copy()
    treatment_contract["cod3"] = treatment_contract["cod3"].astype("string")
    data = aggregated.copy()
    data["cod3"] = data["cod3"].astype("string")
    result = audited_merge(
        data,
        treatment_contract,
        merge_id="pnadc_attach_cod3_treatment_to_arm_b_panel",
        on="cod3",
        how="left",
        validate="many_to_one",
    )
    missing_treatment = result["treatment_status"].isna()
    if missing_treatment.any():
        missing_cod3 = sorted(
            result.loc[missing_treatment, "cod3"].astype(str).unique()
        )
        raise ValueError(
            "COD3 groups are missing treatment classification: "
            f"{missing_cod3}"
        )
    allowed_statuses = {"treated", "control", "intermediate"}
    invalid_statuses = sorted(
        set(result["treatment_status"].astype(str)) - allowed_statuses
    )
    if invalid_statuses:
        raise ValueError(
            f"Unknown treatment_status values: {invalid_statuses}"
        )
    treated_cod3 = pd.to_numeric(
        result["treated_cod3"],
        errors="coerce",
    )
    inconsistent_treatment = (
        result["treatment_status"].eq("treated")
        & treated_cod3.ne(1.0)
    ) | (
        result["treatment_status"].eq("control")
        & treated_cod3.ne(0.0)
    ) | (
        result["treatment_status"].eq("intermediate")
        & treated_cod3.notna()
    )
    if inconsistent_treatment.any():
        inconsistent_cod3 = sorted(
            result.loc[inconsistent_treatment, "cod3"]
            .astype(str)
            .unique()
        )
        raise ValueError(
            "treatment_status and treated_cod3 are inconsistent for COD3: "
            f"{inconsistent_cod3}"
        )
    result = result.loc[
        result["treatment_status"].isin(["treated", "control"])
    ].copy()
    result["treated"] = result["treatment_status"].eq("treated").astype("int8")
    result["post"] = (
        result["ano"].astype(int) * 10
        + result["trimestre"].astype(int)
    ).ge(20231).astype("int8")
    result["post_treat"] = (
        result["post"] * result["treated"]
    ).astype("int8")
    result = result.loc[:, COD3_COLUMNS].sort_values(
        ["trimestre_num", "cod3"]
    )
    return result.reset_index(drop=True)


def build_cod3_panel(
    individual: pd.DataFrame,
    treatment: pd.DataFrame,
    *,
    include_transition_as_pre: bool = False,
) -> pd.DataFrame:
    """Aggregate individual rows and apply the frozen Arm B treatment."""
    panel = _attach_cod3_treatment(
        _aggregate_cod3_counts(individual),
        treatment,
    )
    validate_cod3_panel(
        panel,
        include_transition_as_pre=include_transition_as_pre,
    )
    return panel


def validate_cod3_panel(
    frame: pd.DataFrame,
    *,
    include_transition_as_pre: bool = False,
) -> dict[str, Any]:
    """Validate the COD3-by-quarter Arm B panel."""
    forbidden = sorted(
        {"cod4", "cod_ocupacao"} & set(frame.columns)
    )
    if forbidden:
        raise ValueError(f"COD4 columns are forbidden in the panel: {forbidden}")
    missing = sorted(set(COD3_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"COD3 panel is missing columns: {missing}")
    if frame.empty:
        raise ValueError("COD3 panel is empty")
    if frame.duplicated(["cod3", "trimestre_num"]).any():
        raise ValueError("COD3 panel contains duplicate cells")
    if not frame["cod3"].astype("string").str.fullmatch(
        r"[0-9]{3}",
        na=False,
    ).all():
        raise ValueError("cod3 must contain exactly three digits")
    if not frame["treatment_status"].isin(["treated", "control"]).all():
        raise ValueError("Intermediate COD3 groups remain in Arm B")
    expected_treated = frame["treatment_status"].eq("treated").astype("int8")
    if not frame["treated"].eq(expected_treated).all():
        raise ValueError("treated does not match treatment_status")
    expected_post = (
        frame["ano"].astype(int) * 10 + frame["trimestre"].astype(int)
    ).ge(20231).astype("int8")
    if not frame["post"].eq(expected_post).all():
        raise ValueError("post does not start in 2023Q1")
    if not frame["post_treat"].eq(
        frame["post"] * frame["treated"]
    ).all():
        raise ValueError("post_treat must equal post times treated")
    if (
        frame["ano"].eq(2022) & frame["trimestre"].eq(4)
    ).any() and not include_transition_as_pre:
        raise ValueError("The transition quarter 2022Q4 is present")
    expected_numbers = (
        (frame["ano"].astype(int) - 2012) * 4
        + frame["trimestre"].astype(int)
    )
    if not frame["trimestre_num"].astype(int).eq(expected_numbers).all():
        raise ValueError("trimestre_num does not match the quarter grid")
    count_columns = [
        "ocupados_total",
        "ocupados_formais",
        "ocupados_informais",
    ]
    for column in count_columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        if (~np.isfinite(values) | values.lt(0)).any():
            raise ValueError(f"{column} must be finite and nonnegative")
    total_from_parts = (
        frame["ocupados_formais"] + frame["ocupados_informais"]
    )
    identity = np.isclose(
        total_from_parts,
        frame["ocupados_total"],
        rtol=1e-12,
        atol=1e-6,
    )
    if not identity.all():
        raise ValueError(
            "Formal and informal counts do not reproduce total employment"
        )
    return {
        "cells": int(len(frame)),
        "cod3": int(frame["cod3"].nunique()),
        "quarters": int(
            frame[["ano", "trimestre"]].drop_duplicates().shape[0]
        ),
        "maximum_formal_informal_identity_difference": float(
            (
                total_from_parts - frame["ocupados_total"]
            ).abs().max()
        ),
    }


def build_cod3_panel_from_parquet() -> dict[str, Any]:
    """Execute P8 and publish the Arm B support contract."""
    if not INDIVIDUAL_PANEL_PATH.exists():
        raise FileNotFoundError(
            f"Missing P7 panel: {INDIVIDUAL_PANEL_PATH}"
        )
    import duckdb

    with tempfile.TemporaryDirectory(
        prefix=".duckdb-p8-",
        dir=DATA_DIR,
    ) as temp_dir:
        connection = duckdb.connect()
        try:
            connection.execute("SET threads = 1")
            connection.execute("SET memory_limit = '768MB'")
            escaped_temp = temp_dir.replace("'", "''")
            connection.execute(f"SET temp_directory = '{escaped_temp}'")
            aggregated = connection.execute(
                """
                SELECT
                    ano,
                    trimestre,
                    periodo,
                    trimestre_num,
                    cod3,
                    sum(peso) AS ocupados_total,
                    sum(peso * formal) AS ocupados_formais,
                    sum(peso * informal) AS ocupados_informais
                FROM read_parquet(?)
                GROUP BY
                    ano,
                    trimestre,
                    periodo,
                    trimestre_num,
                    cod3
                ORDER BY trimestre_num, cod3
                """,
                [str(INDIVIDUAL_PANEL_PATH)],
            ).df()
        finally:
            connection.close()

    treatment = pd.read_csv(
        RESULTS_DIR / "pnadc_treatment_cod3.csv",
        dtype={"cod3": "string"},
    )
    panel = _attach_cod3_treatment(aggregated, treatment)
    validation = validate_cod3_panel(panel)
    if validation["quarters"] != 56:
        raise RuntimeError(
            f"Arm B has {validation['quarters']} quarters; expected 56"
        )

    anchor_frame = pd.read_parquet(
        VINTAGE_DIR / "pnadc_2025q3.parquet",
        columns=["ano", "trimestre", "cod_ocupacao", "idade", "peso"],
    )
    anchor = section3_anchor(anchor_frame)
    anchor_rows_match = int(anchor["rows"]) == SECTION3_EXPECTED_ROWS
    anchor_population_match = (
        abs(
            float(anchor["population"])
            - SECTION3_EXPECTED_POPULATION
        )
        <= 1e-6
    )
    if not anchor_rows_match or not anchor_population_match:
        raise RuntimeError("Section 3 anchor failed during P8")

    panel_2025q3 = panel.loc[
        panel["ano"].eq(2025) & panel["trimestre"].eq(3)
    ]
    identity_difference = (
        panel["ocupados_formais"]
        + panel["ocupados_informais"]
        - panel["ocupados_total"]
    ).abs()
    group_support: dict[str, dict[str, Any]] = {}
    for label in ("treated", "control"):
        subset = panel.loc[panel["treatment_status"].eq(label)]
        cells_per_cod3 = subset.groupby("cod3").size()
        group_support[label] = {
            "cod3": int(subset["cod3"].nunique()),
            "cells": int(len(subset)),
            "minimum_cells_per_cod3": int(cells_per_cod3.min()),
            "maximum_cells_per_cod3": int(cells_per_cod3.max()),
            "weighted_employment_all_quarters": float(
                subset["ocupados_total"].sum()
            ),
        }

    temp_path = COD3_PANEL_PATH.with_suffix(".parquet.partial")
    temp_path.unlink(missing_ok=True)
    try:
        panel.to_parquet(
            temp_path,
            index=False,
            compression="zstd",
        )
        _promote_validated_parquet(
            temp_path,
            COD3_PANEL_PATH,
            expected_rows=len(panel),
        )
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    status = {
        "status": "pass",
        "panel": str(COD3_PANEL_PATH.relative_to(FRONT_ROOT)),
        "sha256": sha256_file(COD3_PANEL_PATH),
        "bytes": int(COD3_PANEL_PATH.stat().st_size),
        **validation,
        "duplicate_cells": 0,
        "negative_count_cells": 0,
        "formal_informal_identity_violations": 0,
        "maximum_formal_informal_identity_difference": float(
            identity_difference.max()
        ),
        "no_cod4_columns": True,
        "excluded_transition_period": "2022Q4",
        "groups": group_support,
        "section3_anchor_rows": int(anchor["rows"]),
        "section3_anchor_population": float(anchor["population"]),
        "section3_anchor_rows_match": anchor_rows_match,
        "section3_anchor_population_match_1e_6": anchor_population_match,
        "arm_b_2025q3_weighted_employment": float(
            panel_2025q3["ocupados_total"].sum()
        ),
        "individual_panel_sha256": sha256_file(INDIVIDUAL_PANEL_PATH),
        "treatment_coefficients_computed": False,
    }
    atomic_json(status, COD3_SUPPORT_PATH)
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build preregistered PNADc Part 1 panels.",
    )
    parser.add_argument(
        "task",
        choices=("individual", "cod3"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.task == "individual":
        import json

        print(
            json.dumps(
                build_individual_panel(),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.task == "cod3":
        import json

        print(
            json.dumps(
                build_cod3_panel_from_parquet(),
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
