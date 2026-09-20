#!/usr/bin/env python3
"""Validate directional concordance between the V2 proxy and RAIS stock."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

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


YEARS = (2021, 2022, 2023, 2024)
EXCLUDED_CBO = "3227"

PROXY_PANEL_PATH = (
    V2_ROOT / "data" / "derived" / "painel_stock_proxy.parquet"
)
ANNUAL_PANEL_PATH = FRONT_ROOT / "data" / "painel_rais_anual.parquet"
R10_STATUS_PATH = FRONT_ROOT / "results" / "rais_r10_status.json"
STATIC_RESULTS_PATH = FRONT_ROOT / "results" / "rais_static_results.csv"

VINTAGE_INPUT_PATH = (
    FRONT_ROOT / "data" / "vintage" / "rais_proxy_validation_input.csv"
)
VINTAGE_MANIFEST_PATH = (
    FRONT_ROOT
    / "data"
    / "vintage"
    / "rais_proxy_validation_input_manifest.json"
)
VALIDATION_RESULTS_PATH = (
    FRONT_ROOT / "results" / "rais_proxy_validation.csv"
)
VALIDATION_SUPPORT_PATH = (
    FRONT_ROOT / "results" / "rais_proxy_validation_support.json"
)
VALIDATION_REPORT_PATH = (
    FRONT_ROOT / "results" / "RAIS_VALIDACAO_PROXY.md"
)
R11_STATUS_PATH = FRONT_ROOT / "results" / "rais_r11_status.json"


def _require_columns(
    frame: pd.DataFrame,
    columns: set[str],
    *,
    label: str,
) -> None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def _normalized_cbo(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.zfill(4)


def build_comparison_input(
    proxy_panel: pd.DataFrame,
    annual_panel: pd.DataFrame,
    *,
    reporter: Callable[[dict[str, Any]], None] | None = None,
) -> pd.DataFrame:
    """Build the exact balanced December input with the signed normalization."""
    _require_columns(
        proxy_panel,
        {
            "cbo_4d",
            "periodo",
            "periodo_num",
            "pre_gross_flow",
            "stock_proxy_index",
            "valid_pre_flow_scale",
        },
        label="V2 proxy panel",
    )
    _require_columns(
        annual_panel,
        {"cbo_4d", "ano", "estoque_3112"},
        label="RAIS annual panel",
    )

    proxy = proxy_panel.copy()
    proxy["cbo_4d"] = _normalized_cbo(proxy["cbo_4d"])
    proxy["ano"] = (
        pd.to_numeric(proxy["periodo_num"], errors="raise") // 100
    ).astype(int)
    proxy["mes"] = (
        pd.to_numeric(proxy["periodo_num"], errors="raise") % 100
    ).astype(int)
    proxy = proxy.loc[
        proxy["ano"].isin(YEARS) & proxy["mes"].eq(12),
        [
            "cbo_4d",
            "ano",
            "periodo",
            "pre_gross_flow",
            "stock_proxy_index",
            "valid_pre_flow_scale",
        ],
    ].copy()
    if proxy.duplicated(["cbo_4d", "ano"]).any():
        raise RuntimeError("V2 proxy has duplicate December CBO4-year cells")

    excluded_rows = proxy.loc[proxy["cbo_4d"].eq(EXCLUDED_CBO)]
    if len(excluded_rows) != len(YEARS):
        raise RuntimeError("CBO 3227 is not present in all comparison Decembers")
    if pd.to_numeric(
        excluded_rows["pre_gross_flow"], errors="coerce"
    ).ne(0).any():
        raise RuntimeError("CBO 3227 does not have the declared zero scale")
    invalid_cbos = set(
        proxy.loc[
            ~proxy["valid_pre_flow_scale"].astype(bool), "cbo_4d"
        ].unique()
    )
    if invalid_cbos != {EXCLUDED_CBO}:
        raise RuntimeError(
            f"Unexpected invalid pre-flow scales: {sorted(invalid_cbos)}"
        )
    proxy = proxy.loc[
        ~proxy["cbo_4d"].eq(EXCLUDED_CBO)
        & proxy["valid_pre_flow_scale"].astype(bool)
    ].copy()
    if pd.to_numeric(
        proxy["pre_gross_flow"], errors="raise"
    ).le(0).any():
        raise RuntimeError("A retained proxy row has a nonpositive scale")

    annual = annual_panel.copy()
    annual["cbo_4d"] = _normalized_cbo(annual["cbo_4d"])
    annual["ano"] = pd.to_numeric(
        annual["ano"], errors="raise"
    ).astype(int)
    if "included_main" in annual.columns:
        annual = annual.loc[annual["included_main"].astype(bool)].copy()
    annual = annual.loc[
        annual["ano"].isin(YEARS)
        & ~annual["cbo_4d"].eq(EXCLUDED_CBO),
        ["cbo_4d", "ano", "estoque_3112"],
    ].copy()
    if annual.duplicated(["cbo_4d", "ano"]).any():
        raise RuntimeError("RAIS annual panel has duplicate CBO4-year cells")
    baseline = annual.loc[
        annual["ano"].eq(2021), ["cbo_4d", "estoque_3112"]
    ].rename(columns={"estoque_3112": "estoque_3112_2021"})
    annual = audited_merge(
        annual,
        baseline,
        merge_id="rais_proxy_validation_baseline",
        validate="many_to_one",
        reporter=reporter,
        on="cbo_4d",
        how="left",
    )
    if annual["estoque_3112_2021"].isna().any():
        raise RuntimeError("A retained RAIS CBO4 has no 2021 baseline stock")

    comparison = audited_merge(
        proxy,
        annual,
        merge_id="rais_proxy_validation_december",
        validate="one_to_one",
        reporter=reporter,
        on=["cbo_4d", "ano"],
        how="outer",
        indicator=True,
    )
    unmatched = comparison.loc[
        ~comparison["_merge"].eq("both"),
        ["cbo_4d", "ano", "_merge"],
    ]
    if not unmatched.empty:
        raise RuntimeError(
            "Proxy and RAIS December cells do not align: "
            + repr(unmatched.to_dict(orient="records"))
        )
    comparison = comparison.drop(columns="_merge")
    comparison["rais_stock_index"] = 100.0 + 100.0 * (
        pd.to_numeric(comparison["estoque_3112"], errors="raise")
        - pd.to_numeric(
            comparison["estoque_3112_2021"], errors="raise"
        )
    ) / pd.to_numeric(comparison["pre_gross_flow"], errors="raise")
    comparison["proxy_minus_rais"] = (
        pd.to_numeric(comparison["stock_proxy_index"], errors="raise")
        - comparison["rais_stock_index"]
    )
    numeric_columns = [
        "pre_gross_flow",
        "stock_proxy_index",
        "estoque_3112",
        "estoque_3112_2021",
        "rais_stock_index",
        "proxy_minus_rais",
    ]
    if not np.isfinite(comparison[numeric_columns].to_numpy(float)).all():
        raise RuntimeError("The retained comparison input is not finite")
    comparison = comparison.sort_values(["cbo_4d", "ano"]).reset_index(
        drop=True
    )
    expected_rows = comparison["cbo_4d"].nunique() * len(YEARS)
    if len(comparison) != expected_rows:
        raise RuntimeError("The December comparison input is not balanced")
    return comparison[
        [
            "cbo_4d",
            "ano",
            "periodo",
            "pre_gross_flow",
            "stock_proxy_index",
            "estoque_3112",
            "estoque_3112_2021",
            "rais_stock_index",
            "proxy_minus_rais",
            "valid_pre_flow_scale",
        ]
    ]


def _safe_correlation(
    left: pd.Series,
    right: pd.Series,
) -> tuple[float, str]:
    pair = pd.DataFrame(
        {
            "left": pd.to_numeric(left, errors="coerce"),
            "right": pd.to_numeric(right, errors="coerce"),
        }
    ).dropna()
    if (
        len(pair) < 2
        or float(pair["left"].std(ddof=0)) == 0.0
        or float(pair["right"].std(ddof=0)) == 0.0
    ):
        return np.nan, "not_estimable"
    value = float(pair["left"].corr(pair["right"]))
    if not np.isfinite(value):
        return np.nan, "not_estimable"
    return value, "estimated"


def compute_concordance_metrics(
    comparison: pd.DataFrame,
) -> pd.DataFrame:
    """Compute level, consecutive-change, and median-error metrics by year."""
    _require_columns(
        comparison,
        {
            "cbo_4d",
            "ano",
            "stock_proxy_index",
            "rais_stock_index",
            "proxy_minus_rais",
        },
        label="proxy comparison input",
    )
    work = comparison.sort_values(["cbo_4d", "ano"]).copy()
    work["proxy_change"] = work.groupby(
        "cbo_4d", sort=False
    )["stock_proxy_index"].diff()
    work["rais_change"] = work.groupby(
        "cbo_4d", sort=False
    )["rais_stock_index"].diff()
    rows: list[dict[str, Any]] = []
    for year in YEARS:
        yearly = work.loc[work["ano"].eq(year)].copy()
        level_correlation, level_status = _safe_correlation(
            yearly["stock_proxy_index"],
            yearly["rais_stock_index"],
        )
        if year == YEARS[0]:
            change_correlation = np.nan
            change_status = "not_estimable"
        else:
            change_correlation, change_status = _safe_correlation(
                yearly["proxy_change"],
                yearly["rais_change"],
            )
        rows.append(
            {
                "ano": int(year),
                "cbo_count": int(yearly["cbo_4d"].nunique()),
                "level_correlation": level_correlation,
                "level_correlation_status": level_status,
                "change_correlation": change_correlation,
                "change_correlation_status": change_status,
                "median_absolute_error": float(
                    yearly["proxy_minus_rais"].abs().median()
                ),
                "median_signed_error": float(
                    yearly["proxy_minus_rais"].median()
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize_concordance(metrics: pd.DataFrame) -> dict[str, Any]:
    """Apply the decision-log sign-only tracking and bias classifications."""
    level_values = pd.to_numeric(
        metrics["level_correlation"], errors="coerce"
    ).dropna()
    change_values = pd.to_numeric(
        metrics["change_correlation"], errors="coerce"
    ).dropna()
    correlation_values = pd.concat(
        [level_values, change_values], ignore_index=True
    )
    accompanies = (
        not correlation_values.empty
        and bool(correlation_values.gt(0).all())
    )
    signed_errors = pd.to_numeric(
        metrics["median_signed_error"], errors="raise"
    )
    nonzero_errors = signed_errors.loc[signed_errors.ne(0)]
    if nonzero_errors.empty:
        bias_direction = "none"
    elif nonzero_errors.gt(0).all():
        bias_direction = "upward"
    elif nonzero_errors.lt(0).all():
        bias_direction = "downward"
    else:
        bias_direction = "mixed"
    return {
        "tracking_classification": (
            "accompanies_stock_directionally"
            if accompanies
            else "does_not_accompany_stock_directionally"
        ),
        "classification_rule": (
            "every_estimable_level_and_consecutive_december_change_"
            "correlation_strictly_positive"
        ),
        "estimable_level_correlations": int(level_values.size),
        "estimable_change_correlations": int(change_values.size),
        "median_level_correlation": (
            float(level_values.median())
            if not level_values.empty
            else None
        ),
        "median_change_correlation": (
            float(change_values.median())
            if not change_values.empty
            else None
        ),
        "overall_median_absolute_error": float(
            pd.to_numeric(
                metrics["median_absolute_error"], errors="raise"
            ).median()
        ),
        "overall_median_signed_error": float(signed_errors.median()),
        "bias_direction": bias_direction,
        "bias_rule": (
            "common_sign_of_nonzero_annual_median_proxy_minus_rais_errors"
        ),
    }


def _format_metric(value: Any, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def render_proxy_report(
    metrics: pd.DataFrame,
    summary: dict[str, Any],
) -> str:
    """Render the R11 concordance result without changing the V2 label."""
    lines = [
        "# RAIS validation of the cumulative net-flow proxy",
        "",
        "This is a concordance exercise outside family D. No p-value is "
        "calculated, and no treatment coefficient is used.",
        "",
        "The RAIS analogue is `100 + 100 × (December stock_t - December "
        "stock_2021) / pre-treatment gross flow`. CBO 3227 is excluded "
        "because its frozen pre-treatment gross-flow denominator is zero.",
        "",
        "| December | CBO4 | Level correlation | Level status | "
        "Change correlation | Change status | Median absolute error | "
        "Median signed error |",
        "|---:|---:|---:|---|---:|---|---:|---:|",
    ]
    for row in metrics.itertuples(index=False):
        lines.append(
            f"| {int(row.ano)} | {int(row.cbo_count)} | "
            f"{_format_metric(row.level_correlation)} | "
            f"`{row.level_correlation_status}` | "
            f"{_format_metric(row.change_correlation)} | "
            f"`{row.change_correlation_status}` | "
            f"{_format_metric(row.median_absolute_error)} | "
            f"{_format_metric(row.median_signed_error)} |"
        )
    classification = str(summary["tracking_classification"])
    lines.extend(
        [
            "",
            "December 2021 has no prior declared December for a change "
            "correlation. Its RAIS analogue is also constant at 100 by "
            "construction, so its cross-sectional level correlation is not "
            "estimable. Neither position is assigned an artificial value.",
            "",
            "## Conclusion",
            "",
            f"The directional tracking classification is `{classification}`. "
            "This sign-only classification requires every estimable level "
            "and consecutive-December change correlation to be positive; "
            "the magnitudes above remain the substantive concordance "
            "evidence.",
            "",
            f"The annual median signed-error classification is "
            f"`{summary['bias_direction']}`, where signed error is the V2 "
            "proxy minus the RAIS analogue. This describes directional "
            "error in index points and is not an inferential test.",
            "",
            "The V2 cumulative net-flow proxy remains an "
            "occupation-size-normalized cumulative net-flow index, not an "
            "employment-stock index. Table A.1 remains valid and unchanged. "
            "This validation is a new line of evidence and does not rewrite "
            "the existing proxy label.",
            "",
        ]
    )
    return "\n".join(lines)


def run_r11() -> dict[str, Any]:
    """Execute R11 after the complete R10 diagnostic gate."""
    r10_status = json.loads(R10_STATUS_PATH.read_text(encoding="utf-8"))
    if (
        r10_status.get("r10") != "complete"
        or r10_status.get("gate_r_g3") != "open_diagnostics_reported"
    ):
        raise RuntimeError("R10 and R-G3 must be complete before R11")
    family_d_hash_before = sha256_file(STATIC_RESULTS_PATH)
    source_hashes = {
        "v2_proxy_panel_sha256": sha256_file(PROXY_PANEL_PATH),
        "rais_annual_panel_sha256": sha256_file(ANNUAL_PANEL_PATH),
    }
    merge_reports: list[dict[str, Any]] = []
    comparison = build_comparison_input(
        pd.read_parquet(PROXY_PANEL_PATH),
        pd.read_parquet(ANNUAL_PANEL_PATH),
        reporter=merge_reports.append,
    )
    atomic_csv(comparison, VINTAGE_INPUT_PATH)
    input_hash = sha256_file(VINTAGE_INPUT_PATH)
    atomic_json(
        {
            "status": "frozen",
            **source_hashes,
            "comparison_input_sha256": input_hash,
            "rows": int(len(comparison)),
            "cbo_count": int(comparison["cbo_4d"].nunique()),
            "years": list(YEARS),
            "excluded_cbo4": [EXCLUDED_CBO],
            "merge_audits": merge_reports,
        },
        VINTAGE_MANIFEST_PATH,
    )

    metrics = compute_concordance_metrics(comparison)
    summary = summarize_concordance(metrics)
    atomic_csv(metrics, VALIDATION_RESULTS_PATH)
    results_hash = sha256_file(VALIDATION_RESULTS_PATH)
    family_d_hash_after = sha256_file(STATIC_RESULTS_PATH)
    if family_d_hash_after != family_d_hash_before:
        raise RuntimeError("Family D changed during R11")
    atomic_json(
        {
            "status": "pass",
            **summary,
            "comparison_input_sha256": input_hash,
            "validation_results_sha256": results_hash,
            "rows": int(len(comparison)),
            "cbo_count": int(comparison["cbo_4d"].nunique()),
            "metric_rows": int(len(metrics)),
            "excluded_cbo4": [EXCLUDED_CBO],
            "p_value_columns": [
                column for column in metrics.columns if "p_value" in column
            ],
            "outside_family_d": True,
            "family_d_sha256_before": family_d_hash_before,
            "family_d_sha256_after": family_d_hash_after,
            "family_d_unchanged": True,
            "shared_functions": ["merge_audit.audited_merge"],
        },
        VALIDATION_SUPPORT_PATH,
    )
    atomic_text(
        render_proxy_report(metrics, summary),
        VALIDATION_REPORT_PATH,
    )
    status = {
        "status": "complete",
        "r11": "complete",
        "r12": "not_executed",
        "comparison_input_sha256": input_hash,
        "validation_results_sha256": results_hash,
        "tracking_classification": summary["tracking_classification"],
        "bias_direction": summary["bias_direction"],
        "cbo_count": int(comparison["cbo_4d"].nunique()),
        "years": list(YEARS),
        "p_values_created": 0,
        "family_d_unchanged": True,
    }
    atomic_json(status, R11_STATUS_PATH)
    return {
        "metrics": metrics.to_dict(orient="records"),
        "summary": summary,
        "status": status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    print(json.dumps(run_r11(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
