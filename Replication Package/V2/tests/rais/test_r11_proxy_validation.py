from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
def load_module():
    return importlib.import_module("v2_rais.r11_proxy_validation")


def synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    proxy_rows: list[dict[str, object]] = []
    stock_paths = {
        "1111": [100, 110, 120, 130],
        "2222": [100, 120, 135, 150],
        "3333": [100, 130, 150, 180],
        "3227": [np.nan, np.nan, np.nan, np.nan],
    }
    rais_stocks = {
        "1111": [100, 112, 124, 136],
        "2222": [200, 222, 240, 262],
        "3333": [300, 334, 360, 394],
        "3227": [10, 11, 12, 13],
    }
    scales = {
        "1111": 100,
        "2222": 200,
        "3333": 300,
        "3227": 0,
    }
    annual_rows: list[dict[str, object]] = []
    for cbo, proxy_values in stock_paths.items():
        for year, proxy_value in zip(range(2021, 2025), proxy_values):
            proxy_rows.append(
                {
                    "cbo_4d": cbo,
                    "periodo": f"{year}-12",
                    "periodo_num": year * 100 + 12,
                    "pre_gross_flow": scales[cbo],
                    "stock_proxy_index": proxy_value,
                    "valid_pre_flow_scale": scales[cbo] > 0,
                }
            )
            annual_rows.append(
                {
                    "cbo_4d": cbo,
                    "ano": year,
                    "estoque_3112": rais_stocks[cbo][year - 2021],
                }
            )
    return pd.DataFrame(proxy_rows), pd.DataFrame(annual_rows)


def test_build_comparison_input_excludes_zero_scale_and_normalizes_rais() -> None:
    module = load_module()
    proxy, annual = synthetic_inputs()

    comparison = module.build_comparison_input(proxy, annual)

    assert len(comparison) == 12
    assert set(comparison["cbo_4d"]) == {"1111", "2222", "3333"}
    assert comparison["pre_gross_flow"].gt(0).all()
    assert comparison.loc[
        comparison["ano"].eq(2021), "rais_stock_index"
    ].eq(100).all()
    assert comparison.duplicated(["cbo_4d", "ano"]).sum() == 0


def test_metrics_report_level_change_and_error_without_p_values() -> None:
    module = load_module()
    proxy, annual = synthetic_inputs()
    comparison = module.build_comparison_input(proxy, annual)

    metrics = module.compute_concordance_metrics(comparison)

    assert list(metrics["ano"]) == [2021, 2022, 2023, 2024]
    first = metrics.loc[metrics["ano"].eq(2021)].iloc[0]
    assert first["level_correlation_status"] == "not_estimable"
    assert first["change_correlation_status"] == "not_estimable"
    assert pd.isna(first["level_correlation"])
    assert pd.isna(first["change_correlation"])
    assert metrics.loc[
        metrics["ano"].gt(2021), "change_correlation_status"
    ].eq("estimated").all()
    assert not any("p_value" in column for column in metrics.columns)


def test_summary_requires_every_estimable_correlation_to_be_positive() -> None:
    module = load_module()
    positive = pd.DataFrame(
        {
            "ano": [2021, 2022, 2023, 2024],
            "level_correlation": [np.nan, 0.8, 0.7, 0.6],
            "change_correlation": [np.nan, 0.5, 0.4, 0.3],
            "median_absolute_error": [1.0, 2.0, 3.0, 4.0],
            "median_signed_error": [1.0, 2.0, 3.0, 4.0],
        }
    )

    positive_summary = module.summarize_concordance(positive)
    assert (
        positive_summary["tracking_classification"]
        == "accompanies_stock_directionally"
    )
    assert positive_summary["bias_direction"] == "upward"

    negative = positive.copy()
    negative.loc[negative["ano"].eq(2023), "change_correlation"] = -0.1
    negative.loc[negative["ano"].eq(2024), "median_signed_error"] = -1.0
    negative_summary = module.summarize_concordance(negative)
    assert (
        negative_summary["tracking_classification"]
        == "does_not_accompany_stock_directionally"
    )
    assert negative_summary["bias_direction"] == "mixed"


def test_actual_comparison_contract_has_340_cbos_in_four_decembers() -> None:
    module = load_module()
    proxy = pd.read_parquet(module.PROXY_PANEL_PATH)
    annual = pd.read_parquet(
        PACKAGE_ROOT / "data" / "derived" / "rais" / "painel_rais_anual.parquet"
    )

    comparison = module.build_comparison_input(proxy, annual)

    assert len(comparison) == 1_360
    assert comparison["cbo_4d"].nunique() == 340
    assert comparison.groupby("ano")["cbo_4d"].nunique().eq(340).all()
    assert "3227" not in set(comparison["cbo_4d"])
    assert comparison["valid_pre_flow_scale"].all()


def test_report_preserves_the_v2_proxy_label_and_family_boundary() -> None:
    module = load_module()
    metrics = pd.DataFrame(
        {
            "ano": [2021, 2022],
            "level_correlation": [np.nan, 0.8],
            "level_correlation_status": ["not_estimable", "estimated"],
            "change_correlation": [np.nan, 0.5],
            "change_correlation_status": ["not_estimable", "estimated"],
            "median_absolute_error": [1.0, 2.0],
            "median_signed_error": [1.0, 2.0],
            "cbo_count": [340, 340],
        }
    )
    summary = module.summarize_concordance(metrics)

    report = module.render_proxy_report(metrics, summary)

    assert "not an employment-stock index" in report
    assert "Table A.1 remains valid and unchanged" in report
    assert "outside family D" in report
    assert "No p-value" in report
