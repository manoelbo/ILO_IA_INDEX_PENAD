#!/usr/bin/env python3
"""Build the descriptive V2 occupation-case panel for Section 5.3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
COMMON_DIR = Path(__file__).resolve().parents[2] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from merge_audit import audited_merge
from paths import portable_path


DEFAULT_DICTIONARY = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "occupation_cases"
    / "occupation_case_dictionary.csv"
)
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
    / "painel_casos_ocupacionais.parquet"
)
DEFAULT_COVERAGE = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "occupation_case_monthly_coverage.csv"
)
DEFAULT_COVERAGE_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "OCCUPATION_CASE_MONTHLY_COVERAGE.md"
)
DEFAULT_DIAGNOSTICS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "occupation_case_preperiod_diagnostics.csv"
)
DEFAULT_DIAGNOSTICS_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "OCCUPATION_CASE_PREPERIOD_DIAGNOSTICS.md"
)
DEFAULT_WAGE_BOUNDS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "occupation_case_wage_winsor_bounds.csv"
)
DEFAULT_SUMMARY = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "occupation_case_panel_support.json"
)
DEFAULT_SCRATCH = PACKAGE_ROOT / "data" / "interim"
DICTIONARY_SHA256 = (
    "b8d0310606c37ed32decf4cb46a9088632f9c1409c837d869a2c33d4ac8aa4b2"
)
START_PERIOD = 202101
END_PERIOD = 202605
BASELINE_PERIOD = 202211
TERMINAL_START = 202506
TERMINAL_END = 202605
CASE_SIZES = {
    "customer_service": 2,
    "health_care_aides": 7,
    "marketing_sales_managers": 2,
    "production_supervisors": 53,
    "software_developers": 7,
    "stock_clerks": 5,
}
AGE_GROUPS = (
    ("age_22_25", "Age 22-25"),
    ("age_26_30", "Age 26-30"),
    ("age_31_34", "Age 31-34"),
    ("age_35_40", "Age 35-40"),
    ("age_41_49", "Age 41-49"),
    ("age_50_plus", "Age 50+"),
)
AGGREGATE_COLUMNS = (
    "admissions",
    "wage_sum",
    "wage_count",
    "n_cbo_observed",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def month_range(start_period: int, end_period: int) -> list[int]:
    periods = pd.period_range(
        str(start_period),
        str(end_period),
        freq="M",
    )
    return [int(period.strftime("%Y%m")) for period in periods]


def assign_age_group(age: pd.Series) -> pd.Series:
    values = pd.to_numeric(age, errors="coerce")
    groups = pd.Series(pd.NA, index=age.index, dtype="string")
    groups.loc[values.between(22, 25, inclusive="both")] = (
        "age_22_25"
    )
    groups.loc[values.between(26, 30, inclusive="both")] = (
        "age_26_30"
    )
    groups.loc[values.between(31, 34, inclusive="both")] = (
        "age_31_34"
    )
    groups.loc[values.between(35, 40, inclusive="both")] = (
        "age_35_40"
    )
    groups.loc[values.between(41, 49, inclusive="both")] = (
        "age_41_49"
    )
    groups.loc[values.ge(50)] = "age_50_plus"
    return groups


def load_frozen_dictionary(
    path: Path = DEFAULT_DICTIONARY,
) -> pd.DataFrame:
    if _sha256(path) != DICTIONARY_SHA256:
        raise RuntimeError(
            "Frozen occupation-case dictionary SHA-256 mismatch"
        )
    dictionary = pd.read_csv(path, dtype={"cbo_6d": "string"})
    required = {
        "case_id",
        "case_label_pt",
        "cbo_6d",
        "primary_included",
        "variant_membership",
        "mapping_confidence",
        "semantic_rationale",
    }
    missing = sorted(required - set(dictionary.columns))
    if missing:
        raise RuntimeError(
            f"Occupation-case dictionary is missing columns: {missing}"
        )
    dictionary["cbo_6d"] = (
        dictionary["cbo_6d"].astype("string").str.zfill(6)
    )
    if not dictionary["cbo_6d"].str.fullmatch(
        r"\d{6}",
        na=False,
    ).all():
        raise RuntimeError(
            "Occupation-case dictionary contains an invalid CBO6 code"
        )
    dictionary["primary_included"] = (
        dictionary["primary_included"]
        .astype("string")
        .str.lower()
        .map({"true": True, "false": False})
    )
    if dictionary["primary_included"].isna().any():
        raise RuntimeError(
            "primary_included must contain only True or False"
        )
    primary = dictionary.loc[dictionary["primary_included"]]
    if primary["cbo_6d"].duplicated().any():
        raise RuntimeError(
            "Primary occupation cases contain overlapping CBO6 codes"
        )
    observed_sizes = primary.groupby("case_id").size().to_dict()
    if observed_sizes != CASE_SIZES:
        raise RuntimeError(
            "Frozen occupation-case composition mismatch: "
            f"{observed_sizes}"
        )
    return dictionary


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


def aggregate_case_cells(
    movements_glob: Path,
    primary_dictionary: pd.DataFrame,
    *,
    scratch_parent: Path,
    start_period: int = START_PERIOD,
    end_period: int = END_PERIOD,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    membership = primary_dictionary[
        ["case_id", "case_label_pt", "cbo_6d"]
    ].copy()
    membership["cbo_6d"] = (
        membership["cbo_6d"].astype("string").str.zfill(6)
    )
    if membership["cbo_6d"].duplicated().any():
        raise RuntimeError(
            "Primary occupation-case membership contains duplicate CBO6 codes"
        )
    scratch_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="t8b-occupation-cases-",
        dir=scratch_parent,
    ) as temporary:
        connection = duckdb.connect()
        try:
            _configure_connection(connection, Path(temporary))
            connection.register("case_membership", membership)
            source = _sql_literal(movements_glob)
            valid_sql = f"""
                SELECT
                    CAST(movement.competenciamov AS INTEGER)
                        AS periodo_num,
                    CAST(
                        floor(
                            CAST(movement.competenciamov AS INTEGER)
                            / 100
                        )
                        AS INTEGER
                    ) AS year,
                    CAST(movement.cbo2002ocupacao AS VARCHAR) AS cbo_6d,
                    membership.case_id,
                    membership.case_label_pt,
                    CAST(movement.peso AS BIGINT) AS peso,
                    CAST(movement.salario AS DOUBLE) AS salario,
                    CAST(movement.idade AS INTEGER) AS idade
                FROM read_parquet(
                    {source},
                    hive_partitioning = true,
                    union_by_name = true
                ) AS movement
                INNER JOIN case_membership AS membership
                  ON CAST(movement.cbo2002ocupacao AS VARCHAR)
                     = membership.cbo_6d
                WHERE CAST(movement.competenciamov AS INTEGER)
                      BETWEEN {start_period} AND {end_period}
                  AND CAST(movement.saldomovimentacao AS INTEGER) = 1
                  AND CAST(movement.peso AS INTEGER) IN (-1, 1)
                  AND CAST(movement.idade AS INTEGER) BETWEEN 14 AND 90
            """
            connection.execute(
                f"""
                CREATE TEMP TABLE wage_bounds AS
                SELECT
                    cbo_6d,
                    year,
                    count(*) AS positive_wage_records,
                    quantile_cont(salario, 0.01) AS wage_p01,
                    quantile_cont(salario, 0.99) AS wage_p99
                FROM ({valid_sql}) AS valid
                WHERE peso = 1
                  AND salario > 0
                  AND isfinite(salario)
                GROUP BY cbo_6d, year
                """
            )
            bounds = connection.execute(
                """
                SELECT *
                FROM wage_bounds
                ORDER BY cbo_6d, year
                """
            ).df()
            cells = connection.execute(
                f"""
                WITH valid AS ({valid_sql}),
                categorized AS (
                    SELECT
                        *,
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
                            WHEN idade >= 50
                            THEN 'age_50_plus'
                        END AS age_group
                    FROM valid
                ),
                winsorized AS (
                    SELECT
                        categorized.*,
                        CASE
                            WHEN categorized.salario > 0
                             AND isfinite(categorized.salario)
                            THEN greatest(
                                bounds.wage_p01,
                                least(
                                    categorized.salario,
                                    bounds.wage_p99
                                )
                            )
                        END AS winsorized_wage
                    FROM categorized
                    LEFT JOIN wage_bounds AS bounds
                      ON categorized.cbo_6d = bounds.cbo_6d
                     AND categorized.year = bounds.year
                    WHERE categorized.age_group IS NOT NULL
                )
                SELECT
                    case_id,
                    case_label_pt,
                    age_group,
                    periodo_num,
                    CAST(sum(peso) AS BIGINT) AS admissions,
                    sum(
                        CASE
                            WHEN winsorized_wage IS NOT NULL
                            THEN peso * winsorized_wage
                            ELSE 0
                        END
                    ) AS wage_sum,
                    CAST(sum(
                        CASE
                            WHEN winsorized_wage IS NOT NULL
                            THEN peso
                            ELSE 0
                        END
                    ) AS BIGINT) AS wage_count,
                    count(DISTINCT cbo_6d) AS n_cbo_observed
                FROM winsorized
                GROUP BY
                    case_id,
                    case_label_pt,
                    age_group,
                    periodo_num
                ORDER BY
                    case_id,
                    age_group,
                    periodo_num
                """
            ).df()
        finally:
            connection.close()
    if cells.empty:
        raise RuntimeError(
            "No admissions matched the frozen occupation-case dictionary"
        )
    negative = cells["admissions"].lt(0) | cells["wage_count"].lt(0)
    if negative.any():
        raise RuntimeError(
            "Negative signed occupation-case cells found:\n"
            f"{cells.loc[negative].head(10).to_string(index=False)}"
        )
    cells["admissions"] = cells["admissions"].astype("int64")
    cells["wage_count"] = cells["wage_count"].astype("int64")
    cells["n_cbo_observed"] = cells["n_cbo_observed"].astype("int64")
    return cells, bounds


def validate_case_code_reconciliation(
    primary_dictionary: pd.DataFrame,
    bounds: pd.DataFrame,
) -> None:
    expected = set(
        primary_dictionary["cbo_6d"].astype("string").str.zfill(6)
    )
    observed = set(bounds["cbo_6d"].astype("string").str.zfill(6))
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing:
        raise RuntimeError(
            f"Occupation-case inputs are missing frozen CBO6 codes: {missing}"
        )
    if extra:
        raise RuntimeError(
            f"Occupation-case inputs contain unexpected CBO6 codes: {extra}"
        )


def complete_case_panel(
    cells: pd.DataFrame,
    primary_dictionary: pd.DataFrame,
    ipca: pd.DataFrame,
    *,
    start_period: int = START_PERIOD,
    end_period: int = END_PERIOD,
) -> pd.DataFrame:
    cases = (
        primary_dictionary[
            ["case_id", "case_label_pt"]
        ]
        .drop_duplicates()
        .sort_values("case_id")
    )
    age_groups = [group_id for group_id, _ in AGE_GROUPS]
    grid = pd.MultiIndex.from_product(
        [
            cases["case_id"].tolist(),
            age_groups,
            month_range(start_period, end_period),
        ],
        names=["case_id", "age_group", "periodo_num"],
    ).to_frame(index=False)
    grid = audited_merge(
        grid,
        cases,
        merge_id="occupation_cases_attach_case_labels",
        on="case_id",
        how="left",
        validate="many_to_one",
    )
    values = cells.drop(columns=["case_label_pt"])
    panel = audited_merge(
        grid,
        values,
        merge_id="occupation_cases_complete_monthly_grid",
        on=["case_id", "age_group", "periodo_num"],
        how="left",
        validate="one_to_one",
    )
    for column in AGGREGATE_COLUMNS:
        panel[column] = panel[column].fillna(0)
    panel["admissions"] = panel["admissions"].astype("int64")
    panel["wage_count"] = panel["wage_count"].astype("int64")
    panel["n_cbo_observed"] = panel["n_cbo_observed"].astype("int64")
    price_index = (
        ipca[["periodo_num", "indice"]]
        .drop_duplicates()
        .sort_values("periodo_num")
    )
    if price_index["periodo_num"].duplicated().any():
        raise RuntimeError("IPCA contains duplicate months")
    panel = audited_merge(
        panel,
        price_index,
        merge_id="occupation_cases_attach_ipca",
        on="periodo_num",
        how="left",
        validate="many_to_one",
    )
    if panel["indice"].isna().any():
        raise RuntimeError("IPCA is missing occupation-case months")
    panel["nominal_admission_wage"] = np.where(
        panel["wage_count"].gt(0),
        panel["wage_sum"] / panel["wage_count"],
        np.nan,
    )
    panel["real_admission_wage"] = (
        panel["nominal_admission_wage"] * 100.0 / panel["indice"]
    )
    panel["period"] = pd.to_datetime(
        panel["periodo_num"].astype(str),
        format="%Y%m",
    ).dt.to_period("M").astype(str)
    panel["dictionary_sha256"] = DICTIONARY_SHA256
    panel["is_descriptive"] = True
    panel["has_counterfactual"] = False
    panel = panel.sort_values(
        ["case_id", "age_group", "periodo_num"]
    ).reset_index(drop=True)
    if panel.duplicated(
        ["case_id", "age_group", "periodo_num"]
    ).any():
        raise RuntimeError("Occupation-case panel key is not unique")
    return panel


def build_monthly_coverage(
    panel: pd.DataFrame,
    *,
    expected_months: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (case_id, case_label, age_group), view in panel.groupby(
        ["case_id", "case_label_pt", "age_group"],
        observed=True,
    ):
        total_admissions = int(view["admissions"].sum())
        wage_count = int(view["wage_count"].sum())
        rows.append(
            {
                "case_id": case_id,
                "case_label_pt": case_label,
                "age_group": age_group,
                "expected_months": expected_months,
                "panel_months": int(view["periodo_num"].nunique()),
                "months_with_admissions": int(
                    view["admissions"].gt(0).sum()
                ),
                "months_with_wage": int(
                    view["wage_count"].gt(0).sum()
                ),
                "total_admissions": total_admissions,
                "valid_wage_records": wage_count,
                "wage_record_coverage_pct": (
                    100.0 * wage_count / total_admissions
                    if total_admissions > 0
                    else np.nan
                ),
                "is_descriptive": True,
                "has_counterfactual": False,
            }
        )
    coverage = pd.DataFrame(rows)
    if not coverage["panel_months"].eq(expected_months).all():
        raise RuntimeError(
            "Occupation-case monthly coverage is incomplete"
        )
    return coverage.sort_values(
        ["case_id", "age_group"]
    ).reset_index(drop=True)


def _linear_slope(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.notna()
    if int(valid.sum()) < 2:
        return np.nan
    x = np.arange(len(numeric), dtype=float)[valid.to_numpy()]
    return float(np.polyfit(x, numeric.loc[valid], 1)[0])


def _annualized_log_slope(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.gt(0) & numeric.notna()
    if int(valid.sum()) < 2:
        return np.nan
    x = np.arange(len(numeric), dtype=float)[valid.to_numpy()]
    monthly = np.polyfit(x, np.log(numeric.loc[valid]), 1)[0]
    return float(100.0 * np.expm1(monthly * 12.0))


def build_preperiod_diagnostics(
    panel: pd.DataFrame,
    *,
    pre_start: int = START_PERIOD,
    pre_end: int = BASELINE_PERIOD,
) -> pd.DataFrame:
    preperiod = panel.loc[
        panel["periodo_num"].between(pre_start, pre_end)
    ].copy()
    expected_months = len(month_range(pre_start, pre_end))
    rows: list[dict[str, object]] = []
    for (case_id, case_label, age_group), view in preperiod.groupby(
        ["case_id", "case_label_pt", "age_group"],
        observed=True,
    ):
        view = view.sort_values("periodo_num")
        total_admissions = int(view["admissions"].sum())
        total_wage_records = int(view["wage_count"].sum())
        wage_coverage = (
            100.0 * total_wage_records / total_admissions
            if total_admissions > 0
            else np.nan
        )
        for outcome, column in (
            ("admissions", "admissions"),
            ("real_admission_wage", "real_admission_wage"),
        ):
            values = pd.to_numeric(view[column], errors="coerce")
            observed = values.dropna()
            mean = float(observed.mean()) if not observed.empty else np.nan
            rows.append(
                {
                    "case_id": case_id,
                    "case_label_pt": case_label,
                    "age_group": age_group,
                    "outcome": outcome,
                    "pre_start": pre_start,
                    "pre_end": pre_end,
                    "pre_months_expected": expected_months,
                    "pre_months_observed": int(observed.size),
                    "pre_admissions": total_admissions,
                    "pre_wage_records": total_wage_records,
                    "wage_record_coverage_pct": wage_coverage,
                    "pre_mean": mean,
                    "pre_standard_deviation": (
                        float(observed.std(ddof=0))
                        if not observed.empty
                        else np.nan
                    ),
                    "monthly_linear_slope": _linear_slope(values),
                    "annualized_log_slope_pct": (
                        _annualized_log_slope(values)
                    ),
                    "coefficient_of_variation": (
                        float(observed.std(ddof=0) / mean)
                        if not observed.empty and mean != 0
                        else np.nan
                    ),
                    "diagnostic_type": "descriptive_preperiod",
                    "is_causal_test": False,
                    "has_counterfactual": False,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["case_id", "age_group", "outcome"]
    ).reset_index(drop=True)


def render_preperiod_report(diagnostics: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Occupation-case pre-period diagnostics",
            "",
            "These diagnostics summarize coverage, slope, and volatility "
            "before December 2022. They are descriptive: there is no "
            "case-specific control group or counterfactual.",
            "",
            "This is not a parallel-trends test. No p-value, pass/fail "
            "classification, or causal interpretation is produced.",
            "",
            f"- Diagnostic rows: {len(diagnostics)}",
            f"- Cases: {diagnostics['case_id'].nunique()}",
            f"- Age groups: {diagnostics['age_group'].nunique()}",
            "- National Phase 8A diagnostic: fail in 51 of 51 cells.",
            "",
        ]
    )


def render_coverage_report(coverage: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Occupation-case monthly coverage",
            "",
            "Coverage is reported before any trajectory normalization. "
            "The panel is descriptive and has no case-specific control "
            "group or counterfactual.",
            "",
            f"- Case-age cells: {len(coverage)}",
            f"- Cases: {coverage['case_id'].nunique()}",
            f"- Age groups: {coverage['age_group'].nunique()}",
            f"- Expected months per cell: "
            f"{int(coverage['expected_months'].iloc[0])}",
            "- National Phase 8A diagnostic: fail in 51 of 51 cells.",
            "",
        ]
    )


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _atomic_json(payload: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the descriptive V2 occupation-case panel and "
            "pre-period diagnostics."
        )
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
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=DEFAULT_DICTIONARY,
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument(
        "--coverage",
        type=Path,
        default=DEFAULT_COVERAGE,
    )
    parser.add_argument(
        "--coverage-report",
        type=Path,
        default=DEFAULT_COVERAGE_REPORT,
    )
    parser.add_argument(
        "--diagnostics",
        type=Path,
        default=DEFAULT_DIAGNOSTICS,
    )
    parser.add_argument(
        "--diagnostics-report",
        type=Path,
        default=DEFAULT_DIAGNOSTICS_REPORT,
    )
    parser.add_argument(
        "--wage-bounds",
        type=Path,
        default=DEFAULT_WAGE_BOUNDS,
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
    )
    parser.add_argument(
        "--scratch-parent",
        type=Path,
        default=DEFAULT_SCRATCH,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dictionary = load_frozen_dictionary(args.dictionary)
    primary = dictionary.loc[dictionary["primary_included"]].copy()
    cells, bounds = aggregate_case_cells(
        args.movements_glob,
        primary,
        scratch_parent=args.scratch_parent,
    )
    validate_case_code_reconciliation(primary, bounds)
    national = pd.read_parquet(
        args.national_panel,
        columns=["periodo_num", "indice"],
    )
    panel = complete_case_panel(cells, primary, national)
    coverage = build_monthly_coverage(
        panel,
        expected_months=len(month_range(START_PERIOD, END_PERIOD)),
    )
    _atomic_parquet(panel, args.panel)
    _atomic_csv(bounds, args.wage_bounds)
    _atomic_csv(coverage, args.coverage)
    _atomic_text(
        render_coverage_report(coverage),
        args.coverage_report,
    )
    print(
        f"coverage_written={args.coverage} cells={len(coverage)}",
        flush=True,
    )
    diagnostics = build_preperiod_diagnostics(panel)
    _atomic_csv(diagnostics, args.diagnostics)
    _atomic_text(
        render_preperiod_report(diagnostics),
        args.diagnostics_report,
    )
    summary = {
        "dictionary_path": portable_path(
            args.dictionary,
            relative_to=PACKAGE_ROOT,
        ),
        "dictionary_sha256": DICTIONARY_SHA256,
        "primary_cbo6_codes": int(primary["cbo_6d"].nunique()),
        "cases": int(primary["case_id"].nunique()),
        "age_groups": len(AGE_GROUPS),
        "months": len(month_range(START_PERIOD, END_PERIOD)),
        "panel_rows": len(panel),
        "panel_key_unique": not panel.duplicated(
            ["case_id", "age_group", "periodo_num"]
        ).any(),
        "wage_bound_cells": len(bounds),
        "codes_with_wage_bounds": int(bounds["cbo_6d"].nunique()),
        "coverage_rows": len(coverage),
        "diagnostic_rows": len(diagnostics),
        "baseline_period": BASELINE_PERIOD,
        "terminal_start": TERMINAL_START,
        "terminal_end": TERMINAL_END,
        "is_descriptive": True,
        "has_counterfactual": False,
        "national_phase_8a_diagnostic": "fail_51_of_51",
        "panel_sha256": _sha256(args.panel),
    }
    _atomic_json(summary, args.summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
