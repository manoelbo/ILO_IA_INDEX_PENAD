#!/usr/bin/env python3
"""Build and estimate the preregistered separation-mechanism family."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

import duckdb
import numpy as np
import pandas as pd

COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from merge_audit import audited_merge
from estimators import cluster_t_inference, fit_model
from event_study import (
    EVENT_PERIOD,
    EVENT_TIME_MAX,
    EVENT_TIME_MIN,
    REFERENCE_EVENT_TIME,
    build_event_formula,
    parse_event_time_coefficient,
    prepare_balanced_event_data,
)


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
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "painel_desligamentos_tipo.parquet"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "separation_family_support.csv"
)
DEFAULT_RECONCILIATION = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "separation_family_reconciliation.csv"
)
DEFAULT_STATIC = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "separation_static_results.csv"
)
DEFAULT_EVENT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "separation_event_study.csv"
)
DEFAULT_STATUS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "separation_mechanisms_status.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "SEPARATION_MECHANISMS.md"
)
DEFAULT_SCRATCH = PACKAGE_ROOT / "data" / "interim"
START_PERIOD = 202101
END_PERIOD = 202605
WAGE_MIN = 0.0
WAGE_MAX = 1_000_000.0

SEPARATION_FAMILIES: dict[str, dict[str, Any]] = {
    "dismissal_without_cause": {
        "label": "Dismissal without cause",
        "codes": ("31",),
    },
    "resignation": {
        "label": "Resignation",
        "codes": ("40",),
    },
    "contract_end": {
        "label": "Contract termination",
        "codes": ("43", "45"),
    },
    "dismissal_with_cause": {
        "label": "Dismissal with cause or reciprocal fault",
        "codes": ("32", "33"),
    },
    "mutual_agreement": {
        "label": "Mutual agreement",
        "codes": ("90",),
    },
    "unknown_separation": {
        "label": "Unknown separation type",
        "codes": ("98",),
    },
}
EXCLUDED_CODES = ("50", "60", "80")
PLANNED_STATIC_FAMILY_SIZE = len(SEPARATION_FAMILIES)
EVENT_COEFFICIENTS_PER_FAMILY = (
    EVENT_TIME_MAX - EVENT_TIME_MIN
)
PLANNED_EVENT_FAMILY_SIZE = (
    PLANNED_STATIC_FAMILY_SIZE * EVENT_COEFFICIENTS_PER_FAMILY
)


def separation_family(code: str | int) -> str:
    normalized = str(code).strip()
    for family, specification in SEPARATION_FAMILIES.items():
        if normalized in specification["codes"]:
            return family
    if normalized in EXCLUDED_CODES:
        return "excluded"
    raise ValueError(f"Unclassified separation code: {normalized}")


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


def validate_reconciliation(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "periodo_num",
        "panel_total",
        "named_families",
        "excluded",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Reconciliation is missing columns: {missing}")
    result = frame.copy()
    result["named_plus_excluded"] = (
        result["named_families"] + result["excluded"]
    )
    result["difference"] = (
        result["panel_total"] - result["named_plus_excluded"]
    )
    if not result["difference"].eq(0).all():
        failures = result.loc[
            result["difference"].ne(0),
            [
                "periodo_num",
                "panel_total",
                "named_families",
                "excluded",
                "difference",
            ],
        ]
        raise RuntimeError(
            "Separation families do not reconcile to the panel total:\n"
            + failures.head(10).to_string(index=False)
        )
    if "raw_total" in result:
        result["raw_panel_difference"] = (
            result["raw_total"] - result["panel_total"]
        )
        if not result["raw_panel_difference"].eq(0).all():
            raise RuntimeError(
                "Raw separation total does not reconcile to the panel"
            )
    return result


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def aggregate_separation_types(
    movements_glob: Path,
    *,
    scratch_parent: Path = DEFAULT_SCRATCH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scratch_parent.mkdir(parents=True, exist_ok=True)
    source = _sql_literal(movements_glob)
    named_codes = {
        code
        for specification in SEPARATION_FAMILIES.values()
        for code in specification["codes"]
    }
    allowed_codes = sorted(named_codes | set(EXCLUDED_CODES))
    with tempfile.TemporaryDirectory(
        prefix="t23-duckdb-",
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
                CREATE TEMP VIEW valid_separations AS
                SELECT
                    substring(
                        CAST(cbo2002ocupacao AS VARCHAR),
                        1,
                        4
                    ) AS cbo_4d,
                    CAST(competenciamov AS INTEGER) AS periodo_num,
                    CAST(tipomovimentacao AS VARCHAR) AS movement_type,
                    CAST(peso AS BIGINT) AS peso
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
                  AND CAST(salario AS DOUBLE) > {WAGE_MIN}
                  AND CAST(salario AS DOUBLE) < {WAGE_MAX}
                  AND CAST(saldomovimentacao AS INTEGER) = -1
                  AND CAST(peso AS INTEGER) IN (-1, 1)
                """
            )
            code_counts = connection.execute(
                """
                SELECT
                    periodo_num,
                    movement_type,
                    count(*) AS source_rows,
                    CAST(sum(peso) AS BIGINT) AS signed_count
                FROM valid_separations
                GROUP BY periodo_num, movement_type
                ORDER BY periodo_num, movement_type
                """
            ).df()
            observed_codes = set(code_counts["movement_type"].astype(str))
            unexpected = sorted(observed_codes - set(allowed_codes))
            if unexpected:
                raise RuntimeError(
                    "Unclassified valid separation codes found: "
                    f"{unexpected}"
                )
            family_cases = []
            for family, specification in SEPARATION_FAMILIES.items():
                codes = ", ".join(
                    _sql_literal(code)
                    for code in specification["codes"]
                )
                family_cases.append(
                    f"WHEN movement_type IN ({codes}) "
                    f"THEN {_sql_literal(family)}"
                )
            family_counts = connection.execute(
                f"""
                SELECT
                    cbo_4d,
                    periodo_num,
                    CASE
                        {' '.join(family_cases)}
                    END AS family,
                    CAST(sum(peso) AS BIGINT) AS separation_count
                FROM valid_separations
                WHERE movement_type IN (
                    {', '.join(_sql_literal(code) for code in sorted(named_codes))}
                )
                GROUP BY cbo_4d, periodo_num, family
                ORDER BY family, cbo_4d, periodo_num
                """
            ).df()
        finally:
            connection.close()
    return family_counts, code_counts


def build_family_panel(
    national_panel: pd.DataFrame,
    family_counts: pd.DataFrame,
) -> pd.DataFrame:
    base = national_panel.loc[
        national_panel["included_main"].eq(True),
        [
            "cbo_4d",
            "periodo_num",
            "periodo",
            "post",
            "treated_main",
            "desligamentos",
        ],
    ].copy()
    base["cbo_4d"] = base["cbo_4d"].astype(str).str.zfill(4)
    families = pd.DataFrame(
        {
            "family": list(SEPARATION_FAMILIES),
            "family_label": [
                specification["label"]
                for specification in SEPARATION_FAMILIES.values()
            ],
        }
    )
    base["_join"] = 1
    families["_join"] = 1
    panel = audited_merge(
        base,
        families,
        merge_id="separation_expand_families",
        on="_join",
        how="inner",
        validate="many_to_many",
    ).drop(columns="_join")
    counts = family_counts.copy()
    counts["cbo_4d"] = counts["cbo_4d"].astype(str).str.zfill(4)
    panel = audited_merge(
        panel,
        counts,
        merge_id="separation_attach_family_counts",
        on=["cbo_4d", "periodo_num", "family"],
        how="left",
        validate="one_to_one",
    )
    panel["separation_count"] = (
        panel["separation_count"].fillna(0).astype("int64")
    )
    if panel["separation_count"].lt(0).any():
        raise RuntimeError(
            "Negative signed type-specific separation cells found"
        )
    panel["post_treat"] = (
        panel["post"] * panel["treated_main"]
    ).astype("int8")
    return panel.sort_values(
        ["family", "cbo_4d", "periodo_num"]
    ).reset_index(drop=True)


def build_reconciliation(
    national_panel: pd.DataFrame,
    code_counts: pd.DataFrame,
) -> pd.DataFrame:
    panel_total = (
        national_panel.groupby("periodo_num", as_index=False)[
            "desligamentos"
        ]
        .sum()
        .rename(columns={"desligamentos": "panel_total"})
    )
    counts = code_counts.copy()
    counts["movement_type"] = counts["movement_type"].astype(str)
    named_codes = {
        code
        for specification in SEPARATION_FAMILIES.values()
        for code in specification["codes"]
    }
    counts["is_named"] = counts["movement_type"].isin(named_codes)
    counts["is_excluded"] = counts["movement_type"].isin(
        EXCLUDED_CODES
    )
    monthly = (
        counts.groupby("periodo_num", as_index=False)
        .agg(
            raw_total=("signed_count", "sum"),
            named_families=(
                "signed_count",
                lambda values: int(
                    values[counts.loc[values.index, "is_named"]].sum()
                ),
            ),
            excluded=(
                "signed_count",
                lambda values: int(
                    values[
                        counts.loc[values.index, "is_excluded"]
                    ].sum()
                ),
            ),
        )
    )
    reconciliation = audited_merge(
        panel_total,
        monthly,
        merge_id="separation_reconcile_monthly_totals",
        on="periodo_num",
        how="outer",
        validate="one_to_one",
    ).fillna(0)
    for column in (
        "panel_total",
        "raw_total",
        "named_families",
        "excluded",
    ):
        reconciliation[column] = reconciliation[column].astype("int64")
    reconciliation = validate_reconciliation(reconciliation)
    total = {
        "periodo_num": 0,
        "panel_total": int(reconciliation["panel_total"].sum()),
        "raw_total": int(reconciliation["raw_total"].sum()),
        "named_families": int(
            reconciliation["named_families"].sum()
        ),
        "excluded": int(reconciliation["excluded"].sum()),
    }
    total_frame = validate_reconciliation(pd.DataFrame([total]))
    reconciliation["scope"] = "monthly"
    total_frame["scope"] = "total"
    return pd.concat(
        [reconciliation, total_frame],
        ignore_index=True,
    )


def build_support(
    panel: pd.DataFrame,
    reconciliation: pd.DataFrame,
) -> pd.DataFrame:
    total_named = int(
        reconciliation.loc[
            reconciliation["scope"].eq("total"),
            "named_families",
        ].item()
    )
    rows = []
    for family, group in panel.groupby("family", sort=False):
        positive = group.loc[group["separation_count"].gt(0)]
        treated = positive.loc[positive["treated_main"].eq(1)]
        control = positive.loc[positive["treated_main"].eq(0)]
        rows.append(
            {
                "family": family,
                "family_label": group["family_label"].iloc[0],
                "codes": " + ".join(
                    SEPARATION_FAMILIES[family]["codes"]
                ),
                "signed_total_main_sample": int(
                    group["separation_count"].sum()
                ),
                "share_of_named_main_pct": (
                    100.0
                    * group["separation_count"].sum()
                    / panel["separation_count"].sum()
                ),
                "positive_cells": int(len(positive)),
                "input_cells": int(len(group)),
                "months_with_positive_flow": int(
                    positive["periodo_num"].nunique()
                ),
                "treated_cbo_with_positive_flow": int(
                    treated["cbo_4d"].nunique()
                ),
                "control_cbo_with_positive_flow": int(
                    control["cbo_4d"].nunique()
                ),
                "all_sample_named_total_reference": total_named,
            }
        )
    return pd.DataFrame(rows)


def estimate_static(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family, group in panel.groupby("family", sort=False):
        result, _ = fit_model(
            group,
            model_id=f"separation_static__{family}",
            outcome="separation_count",
            treatment_term="post_treat",
            estimator="ppml",
            fixed_effects=("cbo_4d", "periodo"),
            cluster_variables=("cbo_4d",),
            controls=(),
            principal=True,
            separation_check=("fe",),
        )
        result.update(
            {
                "family": family,
                "family_label": group["family_label"].iloc[0],
            }
        )
        rows.append(result)
    results = pd.DataFrame(rows)
    if len(results) != PLANNED_STATIC_FAMILY_SIZE:
        raise RuntimeError("Static separation family is incomplete")
    results["bh_adjusted_p_value"] = benjamini_hochberg(
        results["p_value"].to_numpy(),
        family_size=PLANNED_STATIC_FAMILY_SIZE,
    )
    return results


def estimate_event_studies(
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    import pyfixest as pf

    data = prepare_balanced_event_data(panel)
    rows: list[dict[str, Any]] = []
    support: dict[str, Any] = {}
    for family, group in data.groupby("family", sort=False):
        formula = build_event_formula("separation_count")
        model = pf.fepois(
            formula,
            data=group,
            vcov={"CRV1": "cbo_4d"},
            separation_check=["fe"],
        )
        if not bool(getattr(model, "_convergence", False)):
            raise RuntimeError(
                f"Separation event-study PPML did not converge: {family}"
            )
        used_data = getattr(model, "_data", group)
        cluster_counts = {
            "cbo_4d": int(used_data["cbo_4d"].nunique())
        }
        for name, term in model.tidy().iterrows():
            event_time = parse_event_time_coefficient(str(name))
            coefficient = float(term["Estimate"])
            standard_error = float(term["Std. Error"])
            inference = cluster_t_inference(
                coefficient,
                standard_error,
                cluster_counts,
            )
            rows.append(
                {
                    "family": family,
                    "family_label": group["family_label"].iloc[0],
                    "event_time": event_time,
                    "periodo": (EVENT_PERIOD + event_time).strftime(
                        "%Y-%m"
                    ),
                    "is_reference": False,
                    "coefficient": coefficient,
                    "standard_error": standard_error,
                    "ci_low": inference["ci_low"],
                    "ci_high": inference["ci_high"],
                    "p_value": inference["p_value"],
                    "cluster_df": inference["cluster_df"],
                    "n_obs": int(model._N),
                    "n_clusters": cluster_counts["cbo_4d"],
                    "effect_percent": 100.0 * math.expm1(coefficient),
                }
            )
        rows.append(
            {
                "family": family,
                "family_label": group["family_label"].iloc[0],
                "event_time": REFERENCE_EVENT_TIME,
                "periodo": "2022-11",
                "is_reference": True,
                "coefficient": 0.0,
                "standard_error": math.nan,
                "ci_low": math.nan,
                "ci_high": math.nan,
                "p_value": math.nan,
                "cluster_df": cluster_counts["cbo_4d"] - 1,
                "n_obs": int(model._N),
                "n_clusters": cluster_counts["cbo_4d"],
                "effect_percent": 0.0,
            }
        )
        support[family] = {
            "n_obs": int(model._N),
            "n_clusters": cluster_counts["cbo_4d"],
            "separation_dropped": int(
                getattr(model, "n_separation_na", 0)
            ),
            "converged": True,
        }
        del model
    coefficients = pd.DataFrame(rows).sort_values(
        ["family", "event_time"]
    ).reset_index(drop=True)
    expected = list(range(EVENT_TIME_MIN, EVENT_TIME_MAX + 1))
    for family, group in coefficients.groupby("family"):
        if group["event_time"].astype(int).tolist() != expected:
            raise RuntimeError(
                f"Separation event grid is incomplete: {family}"
            )
    non_reference = coefficients["is_reference"].eq(False)
    coefficients["bh_adjusted_p_value"] = np.nan
    coefficients.loc[
        non_reference,
        "bh_adjusted_p_value",
    ] = benjamini_hochberg(
        coefficients.loc[non_reference, "p_value"].to_numpy(),
        family_size=PLANNED_EVENT_FAMILY_SIZE,
    )
    return coefficients, support


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


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def write_report(
    support: pd.DataFrame,
    reconciliation: pd.DataFrame,
    static: pd.DataFrame,
    event: pd.DataFrame,
    path: Path,
) -> None:
    total = reconciliation.loc[
        reconciliation["scope"].eq("total")
    ].iloc[0]
    lines = [
        "# Task 23 separation mechanisms",
        "",
        "## Reconciliation and support",
        "",
        (
            f"The six named families sum to "
            f"{int(total.named_families):,} signed separations. The "
            f"excluded retirement, death, and transfer codes sum to "
            f"{int(total.excluded):,}. Together they reproduce the "
            f"national-panel total of {int(total.panel_total):,} exactly."
        ),
        "",
        (
            "| Family | Codes | Signed total in main sample | Share (%) | "
            "Positive cells | Treated CBOs | Control CBOs |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in support.itertuples(index=False):
        lines.append(
            f"| {row.family_label} | {row.codes} | "
            f"{row.signed_total_main_sample:,} | "
            f"{row.share_of_named_main_pct:.3f} | "
            f"{row.positive_cells:,} | "
            f"{row.treated_cbo_with_positive_flow} | "
            f"{row.control_cbo_with_positive_flow} |"
        )
    lines.extend(
        [
            "",
            "## Static principal specification",
            "",
            (
                "| Family | Coefficient | Effect (%) | SE | Nominal p | "
                "BH-adjusted p | N | CBO clusters |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    merged = static.sort_values("family")
    for row in merged.itertuples(index=False):
        lines.append(
            f"| {row.family_label} | {row.coefficient:.6f} | "
            f"{row.effect_percent:.3f} | {row.standard_error:.6f} | "
            f"{row.p_value:.6g} | {row.bh_adjusted_p_value:.6g} | "
            f"{row.n_obs:,} | {row.minimum_clusters} |"
        )
    lines.extend(
        [
            "",
            "## Event study",
            "",
            (
                "The machine-readable event-study table contains all six "
                "families on the frozen ungrouped -23 through +23 grid "
                "with November 2022 as the reference. BH adjustment is "
                "reported across all non-reference dynamic coefficients."
            ),
            "",
            (
                f"Rows: {len(event):,}; non-reference tests: "
                f"{int(event['is_reference'].eq(False).sum()):,}."
            ),
            "",
            (
                "Mechanism labels remain descriptive because the national "
                "exact-model pretrend diagnostics fail."
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
        description="Run Task 23 separation-mechanism models."
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
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument(
        "--reconciliation",
        type=Path,
        default=DEFAULT_RECONCILIATION,
    )
    parser.add_argument("--static", type=Path, default=DEFAULT_STATIC)
    parser.add_argument("--event", type=Path, default=DEFAULT_EVENT)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    national = pd.read_parquet(args.national_panel)
    family_counts, code_counts = aggregate_separation_types(
        args.movements
    )
    panel = build_family_panel(national, family_counts)
    reconciliation = build_reconciliation(national, code_counts)
    support = build_support(panel, reconciliation)
    _atomic_parquet(panel, args.panel)
    _atomic_csv(support, args.support)
    _atomic_csv(reconciliation, args.reconciliation)

    static = estimate_static(panel)
    event, event_support = estimate_event_studies(panel)
    _atomic_csv(static, args.static)
    _atomic_csv(event, args.event)
    status = {
        "status": "completed",
        "family_count": len(SEPARATION_FAMILIES),
        "static_model_count": int(len(static)),
        "event_model_count": len(event_support),
        "event_rows": int(len(event)),
        "static_family_size": PLANNED_STATIC_FAMILY_SIZE,
        "event_family_size": PLANNED_EVENT_FAMILY_SIZE,
        "reconciliation_exact": bool(
            reconciliation["difference"].eq(0).all()
        ),
        "panel_rows": int(len(panel)),
        "panel_sha256": _sha256(args.panel),
        "event_support": event_support,
    }
    _atomic_json(status, args.status)
    write_report(
        support,
        reconciliation,
        static,
        event,
        args.report,
    )
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
