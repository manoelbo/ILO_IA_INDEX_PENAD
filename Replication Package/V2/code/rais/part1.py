#!/usr/bin/env python3
"""Build and validate the pre-registered RAIS Part 1 panels.

This module reads the frozen 2016-2024 RAIS aggregate and the signed V2
derived inputs. It performs no live query and estimates no treatment
coefficient.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FRONT_ROOT = Path(__file__).resolve().parent.parent
V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
COMMON_DIR = V2_ROOT / "code" / "common"
MODELS_DIR = V2_ROOT / "code" / "caged" / "models"
for module_dir in (COMMON_DIR, MODELS_DIR):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from merge_audit import audited_merge  # noqa: E402
from pretrend_engine import atomic_csv, atomic_json, atomic_text  # noqa: E402
from .stage0 import sha256_file  # noqa: E402


WINDOW_START = 2019
WINDOW_END = 2024
ROTATION_START = 2021
ROTATION_END = 2024
EXPOSED_LABEL_PREFIX = "Exposed:"
CONTROL_LABEL = "Not Exposed"
EXPECTED_TREATED_CBO = 75
EXPECTED_CONTROL_CBO = 266
SUPPORT_ADEQUATE_TREATED = 20
SUPPORT_ADEQUATE_CONTROL = 50
SUPPORT_LIMITED_TREATED = 10
SUPPORT_LIMITED_CONTROL = 25

VINTAGE_PATH = (
    FRONT_ROOT / "data" / "vintage" / "rais_cbo4_ano_2016_2024.csv"
)
VINTAGE_MANIFEST_PATH = FRONT_ROOT / "data" / "vintage" / "manifest.json"
CLASSIFICATION_PATH = (
    V2_ROOT / "data" / "derived" / "cbo_treatment_classification.csv"
)
CAGED_PANEL_PATH = V2_ROOT / "data" / "derived" / "painel_nacional.parquet"
ANNUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_rais_anual.parquet"
ROTATION_PANEL_PATH = (
    FRONT_ROOT / "data" / "painel_rais_rotatividade.parquet"
)
ANNUAL_SUPPORT_PATH = (
    FRONT_ROOT / "results" / "painel_rais_anual_support.json"
)
ROTATION_SUPPORT_PATH = (
    FRONT_ROOT / "results" / "painel_rais_rotatividade_support.json"
)
SUPPORT_TABLE_PATH = FRONT_ROOT / "results" / "rais_support.csv"
SUPPORT_REPORT_PATH = FRONT_ROOT / "results" / "RAIS_SUPORTE.md"
PART1_STATUS_PATH = FRONT_ROOT / "results" / "rais_part1_status.json"

PART2_ARTIFACT_PATTERNS = (
    "rais_pretrend*",
    "rais_results*",
    "rais_sensitivities*",
    "rais_proxy_validation*",
    "RAIS_RELATORIO.md",
)


def _required_columns(
    frame: pd.DataFrame,
    required: set[str],
    *,
    source_name: str,
) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_name} is missing columns: {missing}")


def _normalize_cbo(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip().str.zfill(4)
    invalid = normalized.isna() | ~normalized.str.fullmatch(r"\d{4}")
    if invalid.any():
        observed = sorted(normalized.loc[invalid].astype(str).unique().tolist())
        raise ValueError(f"Invalid CBO4 codes: {observed[:10]}")
    return normalized


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_parquet(temporary, index=False, compression="zstd")
    os.replace(temporary, path)


def _treatment_contract(
    classification: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    _required_columns(
        classification,
        {"cbo_4d", "cbo_ilo_gradient"},
        source_name="Treatment classification",
    )
    classes = classification[["cbo_4d", "cbo_ilo_gradient"]].copy()
    classes["cbo_4d"] = _normalize_cbo(classes["cbo_4d"])
    if classes["cbo_4d"].duplicated().any():
        raise RuntimeError("Treatment classification has duplicate CBO4 keys")
    exposed = classes["cbo_ilo_gradient"].astype(str).str.startswith(
        EXPOSED_LABEL_PREFIX
    )
    control = classes["cbo_ilo_gradient"].eq(CONTROL_LABEL)
    included = classes.loc[exposed | control].copy()
    support = {
        "classification_cbo": int(len(classes)),
        "contract_cbo": int(len(included)),
        "contract_treated_cbo": int(exposed.sum()),
        "contract_control_cbo": int(control.sum()),
        "excluded_cbo": int(len(classes) - len(included)),
        "excluded_labels": sorted(
            classes.loc[
                ~(exposed | control), "cbo_ilo_gradient"
            ].astype(str).unique().tolist()
        ),
    }
    return classes, support


def prepare_rais_panel(
    rais: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    window_start: int = WINDOW_START,
    window_end: int = WINDOW_END,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Attach the signed treatment and construct the annual RAIS panel."""
    _required_columns(
        rais,
        {
            "ano",
            "cbo_4d",
            "vinculos_declarados",
            "estoque_3112",
            "tempo_emprego_medio",
        },
        source_name="Frozen RAIS aggregate",
    )
    source = rais.copy()
    source["cbo_4d"] = _normalize_cbo(source["cbo_4d"])
    source["ano"] = pd.to_numeric(source["ano"], errors="raise").astype(int)
    if source.duplicated(["cbo_4d", "ano"]).any():
        raise RuntimeError("Frozen RAIS aggregate has duplicate CBO4-year keys")
    stock = pd.to_numeric(source["estoque_3112"], errors="raise")
    if stock.lt(0).any():
        raise RuntimeError("Frozen RAIS aggregate contains negative stock")

    classes, contract_support = _treatment_contract(classification)
    merged = audited_merge(
        source,
        classes,
        merge_id="rais_treatment",
        validate="many_to_one",
        on="cbo_4d",
        how="left",
    )
    merge_audit = dict(merged.attrs["merge_audit"])
    unclassified = sorted(
        merged.loc[merged["cbo_ilo_gradient"].isna(), "cbo_4d"]
        .unique()
        .tolist()
    )
    merged["cbo_ilo_gradient"] = merged["cbo_ilo_gradient"].fillna(
        "No score"
    )
    exposed = merged["cbo_ilo_gradient"].astype(str).str.startswith(
        EXPOSED_LABEL_PREFIX
    )
    control = merged["cbo_ilo_gradient"].eq(CONTROL_LABEL)
    merged["treated_main"] = np.where(
        exposed,
        1.0,
        np.where(control, 0.0, np.nan),
    )
    merged["included_main"] = exposed | control
    merged["post"] = merged["ano"].ge(2023).astype("int8")
    merged["post_treat"] = merged["post"] * merged["treated_main"]
    merged["dummy_2020"] = merged["ano"].eq(2020).astype("int8")
    tenure = pd.to_numeric(merged["tempo_emprego_medio"], errors="raise")
    merged["ln_tempo_emprego_medio"] = np.where(
        tenure.gt(0),
        np.log(tenure),
        np.nan,
    )

    panel = merged.loc[
        merged["included_main"]
        & merged["ano"].between(window_start, window_end)
    ].copy()
    panel = panel.sort_values(["cbo_4d", "ano"]).reset_index(drop=True)
    if panel.duplicated(["cbo_4d", "ano"]).any():
        raise RuntimeError("Annual RAIS panel has duplicate CBO4-year keys")
    if panel["estoque_3112"].lt(0).any():
        raise RuntimeError("Annual RAIS panel contains negative stock")

    contract_cbo = set(
        classes.loc[
            classes["cbo_ilo_gradient"].astype(str).str.startswith(
                EXPOSED_LABEL_PREFIX
            )
            | classes["cbo_ilo_gradient"].eq(CONTROL_LABEL),
            "cbo_4d",
        ]
    )
    present_cbo = set(panel["cbo_4d"])
    years = list(range(window_start, window_end + 1))
    absent_by_year = {
        str(year): sorted(
            contract_cbo
            - set(panel.loc[panel["ano"].eq(year), "cbo_4d"])
        )
        for year in years
    }
    support: dict[str, Any] = {
        **contract_support,
        "status": "pass",
        "source_live_query_used": False,
        "treatment_coefficient_estimated": False,
        "window_start": int(window_start),
        "window_end": int(window_end),
        "years": sorted(panel["ano"].unique().astype(int).tolist()),
        "rows": int(len(panel)),
        "cbo": int(panel["cbo_4d"].nunique()),
        "treated_cbo": int(
            panel.loc[panel["treated_main"].eq(1), "cbo_4d"].nunique()
        ),
        "control_cbo": int(
            panel.loc[panel["treated_main"].eq(0), "cbo_4d"].nunique()
        ),
        "rows_by_year": {
            str(int(year)): int(count)
            for year, count in panel.groupby("ano").size().items()
        },
        "absent_contract_cbo": sorted(contract_cbo - present_cbo),
        "absent_contract_cbo_count": int(len(contract_cbo - present_cbo)),
        "absent_contract_cbo_by_year": absent_by_year,
        "missing_balanced_cells": int(
            len(contract_cbo) * len(years) - len(panel)
        ),
        "negative_stock_cells": int(panel["estoque_3112"].lt(0).sum()),
        "zero_stock_cells": int(panel["estoque_3112"].eq(0).sum()),
        "nonpositive_tenure_cells": int(
            pd.to_numeric(
                panel["tempo_emprego_medio"], errors="raise"
            ).le(0).sum()
        ),
        "missing_log_tenure_cells": int(
            panel["ln_tempo_emprego_medio"].isna().sum()
        ),
        "new_unclassified_cbo": unclassified,
        "merge_audit": merge_audit,
    }
    return panel, support


def aggregate_caged_flows(
    monthly: pd.DataFrame,
    *,
    start_year: int = ROTATION_START,
    end_year: int = ROTATION_END,
) -> pd.DataFrame:
    """Aggregate the signed V2 monthly flows to CBO4 by calendar year."""
    _required_columns(
        monthly,
        {
            "cbo_4d",
            "ano",
            "admissoes",
            "desligamentos",
            "included_main",
        },
        source_name="V2 national panel",
    )
    source = monthly.loc[
        monthly["included_main"]
        & monthly["ano"].between(start_year, end_year)
    ].copy()
    source["cbo_4d"] = _normalize_cbo(source["cbo_4d"])
    annual = (
        source.groupby(["cbo_4d", "ano"], as_index=False, sort=True)[
            ["admissoes", "desligamentos"]
        ]
        .sum()
        .sort_values(["cbo_4d", "ano"])
        .reset_index(drop=True)
    )
    if annual.duplicated(["cbo_4d", "ano"]).any():
        raise RuntimeError("Annual CAGED flow aggregate has duplicate keys")
    return annual


def build_rotation_panel(
    monthly: pd.DataFrame,
    rais_panel: pd.DataFrame,
    *,
    start_year: int = ROTATION_START,
    end_year: int = ROTATION_END,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Combine annual CAGED flows with the RAIS stock denominator."""
    annual = aggregate_caged_flows(
        monthly,
        start_year=start_year,
        end_year=end_year,
    )
    required_rais = {
        "cbo_4d",
        "ano",
        "estoque_3112",
        "treated_main",
        "included_main",
        "post",
        "post_treat",
        "dummy_2020",
    }
    _required_columns(
        rais_panel,
        required_rais,
        source_name="Annual RAIS panel",
    )
    stock = rais_panel.loc[
        rais_panel["ano"].between(start_year, end_year),
        sorted(required_rais),
    ].copy()
    stock["cbo_4d"] = _normalize_cbo(stock["cbo_4d"])
    if stock.duplicated(["cbo_4d", "ano"]).any():
        raise RuntimeError("Annual RAIS stock has duplicate CBO4-year keys")

    merged = audited_merge(
        annual,
        stock,
        merge_id="rais_rotation_stock",
        validate="one_to_one",
        on=["cbo_4d", "ano"],
        how="outer",
        indicator=True,
    )
    merge_audit = dict(merged.attrs["merge_audit"])
    cells_missing_rais = int(merged["_merge"].eq("left_only").sum())
    cells_missing_caged = int(merged["_merge"].eq("right_only").sum())
    panel = merged.loc[merged["_merge"].eq("both")].drop(
        columns="_merge"
    ).copy()
    stock_values = pd.to_numeric(panel["estoque_3112"], errors="raise")
    total_flows = (
        pd.to_numeric(panel["admissoes"], errors="raise")
        + pd.to_numeric(panel["desligamentos"], errors="raise")
    )
    panel["taxa_rotatividade"] = np.where(
        stock_values.gt(0),
        total_flows / stock_values,
        np.nan,
    )
    panel["ln_taxa_rotatividade"] = np.where(
        panel["taxa_rotatividade"].gt(0),
        np.log(panel["taxa_rotatividade"]),
        np.nan,
    )
    panel = panel.sort_values(["cbo_4d", "ano"]).reset_index(drop=True)
    zero_numeric = int(
        (
            panel["estoque_3112"].eq(0)
            & panel["taxa_rotatividade"].notna()
        ).sum()
    )
    if zero_numeric:
        raise RuntimeError("A zero-stock cell received a numeric rotation rate")
    support = {
        "status": "pass",
        "source_live_query_used": False,
        "treatment_coefficient_estimated": False,
        "window_start": int(start_year),
        "window_end": int(end_year),
        "years": sorted(panel["ano"].unique().astype(int).tolist()),
        "rows": int(len(panel)),
        "cbo": int(panel["cbo_4d"].nunique()),
        "treated_cbo": int(
            panel.loc[panel["treated_main"].eq(1), "cbo_4d"].nunique()
        ),
        "control_cbo": int(
            panel.loc[panel["treated_main"].eq(0), "cbo_4d"].nunique()
        ),
        "cells_missing_rais": cells_missing_rais,
        "cells_missing_caged": cells_missing_caged,
        "cells_missing_either_base": int(
            cells_missing_rais + cells_missing_caged
        ),
        "cells_zero_stock": int(panel["estoque_3112"].eq(0).sum()),
        "cells_zero_flow": int(total_flows.eq(0).sum()),
        "zero_stock_cells_with_numeric_rate": zero_numeric,
        "missing_rotation_rate_cells": int(
            panel["taxa_rotatividade"].isna().sum()
        ),
        "missing_log_rotation_cells": int(
            panel["ln_taxa_rotatividade"].isna().sum()
        ),
        "merge_audit": merge_audit,
    }
    return panel, support


def classify_support(treated_cbo: int, control_cbo: int) -> str:
    """Apply the frozen V2 support thresholds."""
    if (
        treated_cbo >= SUPPORT_ADEQUATE_TREATED
        and control_cbo >= SUPPORT_ADEQUATE_CONTROL
    ):
        return "adequate"
    if (
        treated_cbo >= SUPPORT_LIMITED_TREATED
        and control_cbo >= SUPPORT_LIMITED_CONTROL
    ):
        return "limited"
    return "thin"


def _outcome_support_rows(
    frame: pd.DataFrame,
    outcome: str,
) -> list[dict[str, Any]]:
    _required_columns(
        frame,
        {"cbo_4d", "ano", "treated_main", outcome},
        source_name=f"Support input for {outcome}",
    )
    rows: list[dict[str, Any]] = []
    for year in sorted(frame["ano"].unique()):
        annual = frame.loc[frame["ano"].eq(year)].copy()
        values = pd.to_numeric(annual[outcome], errors="coerce")
        nonmissing = values.notna() & np.isfinite(values)
        treated = int(
            annual.loc[
                nonmissing & annual["treated_main"].eq(1), "cbo_4d"
            ].nunique()
        )
        control = int(
            annual.loc[
                nonmissing & annual["treated_main"].eq(0), "cbo_4d"
            ].nunique()
        )
        rows.append(
            {
                "outcome": outcome,
                "ano": int(year),
                "treated_cbo": treated,
                "control_cbo": control,
                "total_cbo": int(treated + control),
                "support_status": classify_support(treated, control),
            }
        )
    return rows


def build_support_table(
    annual_panel: pd.DataFrame,
    rotation_panel: pd.DataFrame,
) -> pd.DataFrame:
    """Count non-missing treated and control CBO4 cells by outcome-year."""
    rows = [
        *_outcome_support_rows(annual_panel, "estoque_3112"),
        *_outcome_support_rows(rotation_panel, "ln_taxa_rotatividade"),
        *_outcome_support_rows(
            annual_panel,
            "ln_tempo_emprego_medio",
        ),
    ]
    support = pd.DataFrame(rows)
    outcome_order = {
        "estoque_3112": 0,
        "ln_taxa_rotatividade": 1,
        "ln_tempo_emprego_medio": 2,
    }
    support["_outcome_order"] = support["outcome"].map(outcome_order)
    return (
        support.sort_values(["_outcome_order", "ano"])
        .drop(columns="_outcome_order")
        .reset_index(drop=True)
    )


def _render_support_report(support: pd.DataFrame) -> str:
    lines = [
        "# RAIS support before treatment coefficients",
        "",
        "This table was produced before any Part 2 result. Counts are unique "
        "CBO4 codes with a finite outcome in each year and treatment arm.",
        "",
        "| Outcome | Year | Treated CBO4 | Control CBO4 | Total | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in support.itertuples(index=False):
        lines.append(
            f"| `{row.outcome}` | {row.ano} | {row.treated_cbo} | "
            f"{row.control_cbo} | {row.total_cbo} | `{row.support_status}` |"
        )
    lines.extend(
        [
            "",
            "Thresholds: `adequate` requires at least 20 treated and 50 "
            "control CBO4 codes; `limited` requires at least 10 treated and "
            "25 controls; otherwise support is `thin`.",
            "",
            "No treatment coefficient was estimated to construct or classify "
            "this table.",
            "",
        ]
    )
    return "\n".join(lines)


def _part2_artifacts() -> list[str]:
    found: set[str] = set()
    results_dir = FRONT_ROOT / "results"
    for pattern in PART2_ARTIFACT_PATTERNS:
        found.update(
            str(path.relative_to(FRONT_ROOT))
            for path in results_dir.glob(pattern)
            if path.is_file()
        )
    return sorted(found)


def _validate_real_inputs(
    annual_support: dict[str, Any],
    rotation_support: dict[str, Any],
    monthly: pd.DataFrame,
) -> dict[str, Any]:
    if (
        annual_support["contract_treated_cbo"] != EXPECTED_TREATED_CBO
        or annual_support["contract_control_cbo"] != EXPECTED_CONTROL_CBO
    ):
        raise RuntimeError(
            "Signed treatment family must contain 75 exposed and "
            "266 Not Exposed CBO4 codes"
        )
    expected_annual_years = list(range(WINDOW_START, WINDOW_END + 1))
    if annual_support["years"] != expected_annual_years:
        raise RuntimeError(
            f"Annual RAIS panel years differ: {annual_support['years']}"
        )
    expected_rotation_years = list(range(ROTATION_START, ROTATION_END + 1))
    if rotation_support["years"] != expected_rotation_years:
        raise RuntimeError(
            f"Rotation panel years differ: {rotation_support['years']}"
        )
    sample = monthly.loc[
        monthly["included_main"]
        & monthly["ano"].between(ROTATION_START, ROTATION_END)
    ]
    months_by_year = {
        str(int(year)): sorted(group["mes"].astype(int).unique().tolist())
        for year, group in sample.groupby("ano")
    }
    incomplete = {
        year: months
        for year, months in months_by_year.items()
        if months != list(range(1, 13))
    }
    if incomplete:
        raise RuntimeError(f"Incomplete CAGED calendar years: {incomplete}")
    return {
        "months_by_year": months_by_year,
        "all_calendar_years_complete": True,
    }


def run_part1() -> dict[str, Any]:
    """Execute R5, R6, and R7 in order and stop before Part 2."""
    manifest = json.loads(VINTAGE_MANIFEST_PATH.read_text(encoding="utf-8"))
    observed_vintage_sha = sha256_file(VINTAGE_PATH)
    expected_vintage_sha = str(manifest["sha256"])
    if observed_vintage_sha != expected_vintage_sha:
        raise RuntimeError(
            "Frozen RAIS vintage SHA-256 mismatch: "
            f"expected {expected_vintage_sha}, observed {observed_vintage_sha}"
        )
    part2_before = _part2_artifacts()
    if part2_before:
        raise RuntimeError(
            "Part 2 artifacts already exist before support publication: "
            f"{part2_before}"
        )

    rais = pd.read_csv(VINTAGE_PATH, dtype={"cbo_4d": "string"})
    classification = pd.read_csv(
        CLASSIFICATION_PATH,
        dtype={"cbo_4d": "string"},
    )

    # R5
    annual_panel, annual_support = prepare_rais_panel(
        rais,
        classification,
        window_start=WINDOW_START,
        window_end=WINDOW_END,
    )
    annual_support["vintage_sha256"] = observed_vintage_sha
    annual_support["classification_sha256"] = sha256_file(
        CLASSIFICATION_PATH
    )
    _atomic_parquet(annual_panel, ANNUAL_PANEL_PATH)
    atomic_json(annual_support, ANNUAL_SUPPORT_PATH)

    # R6
    monthly = pd.read_parquet(CAGED_PANEL_PATH)
    rotation_panel, rotation_support = build_rotation_panel(
        monthly,
        annual_panel,
        start_year=ROTATION_START,
        end_year=ROTATION_END,
    )
    rotation_support["caged_panel_sha256"] = sha256_file(CAGED_PANEL_PATH)
    coverage = _validate_real_inputs(
        annual_support,
        rotation_support,
        monthly,
    )
    rotation_support.update(coverage)
    reconciliation_year = 2022
    monthly_totals = (
        monthly.loc[
            monthly["included_main"]
            & monthly["ano"].eq(reconciliation_year),
            ["admissoes", "desligamentos"],
        ]
        .sum()
        .astype(int)
    )
    annual_totals = (
        rotation_panel.loc[
            rotation_panel["ano"].eq(reconciliation_year),
            ["admissoes", "desligamentos"],
        ]
        .sum()
        .astype(int)
    )
    rotation_support["annual_flux_reconciliation"] = {
        "year": reconciliation_year,
        "monthly_admissions": int(monthly_totals["admissoes"]),
        "annual_admissions": int(annual_totals["admissoes"]),
        "monthly_separations": int(monthly_totals["desligamentos"]),
        "annual_separations": int(annual_totals["desligamentos"]),
        "exact_match": bool(monthly_totals.equals(annual_totals)),
    }
    if not rotation_support["annual_flux_reconciliation"]["exact_match"]:
        raise RuntimeError("Annual CAGED flows do not match monthly V2 totals")
    _atomic_parquet(rotation_panel, ROTATION_PANEL_PATH)
    atomic_json(rotation_support, ROTATION_SUPPORT_PATH)

    # R7
    support = build_support_table(annual_panel, rotation_panel)
    if support.empty:
        raise RuntimeError("RAIS support table is empty")
    support_published_at = datetime.now(timezone.utc).isoformat()
    atomic_csv(support, SUPPORT_TABLE_PATH)
    atomic_text(_render_support_report(support), SUPPORT_REPORT_PATH)
    part2_after = _part2_artifacts()
    if part2_after:
        raise RuntimeError(
            "Part 2 artifacts appeared during support publication: "
            f"{part2_after}"
        )

    outcome_summary = {
        outcome: {
            "years": sorted(group["ano"].astype(int).tolist()),
            "minimum_treated_cbo": int(group["treated_cbo"].min()),
            "minimum_control_cbo": int(group["control_cbo"].min()),
            "statuses": sorted(group["support_status"].unique().tolist()),
        }
        for outcome, group in support.groupby("outcome", sort=True)
    }
    thin_outcomes = sorted(
        support.loc[
            support["support_status"].eq("thin"), "outcome"
        ].unique().tolist()
    )
    gate_open = bool(
        not thin_outcomes
        and annual_support["negative_stock_cells"] == 0
        and rotation_support["zero_stock_cells_with_numeric_rate"] == 0
        and not part2_after
    )
    status = {
        "status": "pass" if gate_open else "fail",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "support_published_at": support_published_at,
        "derived_rais_window": f"{WINDOW_START}-{WINDOW_END}",
        "rotation_window": f"{ROTATION_START}-{ROTATION_END}",
        "year_2025_included": False,
        "vintage_sha256": observed_vintage_sha,
        "annual_panel_sha256": sha256_file(ANNUAL_PANEL_PATH),
        "rotation_panel_sha256": sha256_file(ROTATION_PANEL_PATH),
        "annual_panel_rows": int(len(annual_panel)),
        "rotation_panel_rows": int(len(rotation_panel)),
        "annual_duplicate_keys": int(
            annual_panel.duplicated(["cbo_4d", "ano"]).sum()
        ),
        "rotation_duplicate_keys": int(
            rotation_panel.duplicated(["cbo_4d", "ano"]).sum()
        ),
        "support_rows": int(len(support)),
        "outcome_support": outcome_summary,
        "thin_outcomes": thin_outcomes,
        "part2_artifacts_before_support": part2_before,
        "part2_artifacts_after_support": part2_after,
        "treatment_coefficient_estimated": False,
        "gate_r_b1": "open" if gate_open else "closed",
    }
    atomic_json(status, PART1_STATUS_PATH)
    return {
        "annual_panel": annual_support,
        "rotation_panel": rotation_support,
        "support": support.to_dict(orient="records"),
        "status": status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    result = run_part1()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
