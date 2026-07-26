from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "models" / "stock_proxy.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "stock_proxy",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load stock_proxy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stock_proxy_completes_grid_and_normalizes_base_to_100() -> None:
    module = load_module()
    panel = pd.DataFrame(
        {
            "cbo_4d": ["1111", "1111", "2222", "2222"],
            "periodo_num": [202101, 202103, 202101, 202102],
            "admissoes": [10, 20, 5, 6],
            "desligamentos": [8, 15, 7, 4],
            "included_main": [True] * 4,
            "treated_main": [1, 1, 0, 0],
        }
    )

    result = module.build_stock_proxy(
        panel,
        start_period=202101,
        end_period=202103,
        pre_end_period=202102,
    )

    assert len(result) == 6
    assert result.loc[
        result["periodo_num"].eq(202101),
        "stock_proxy_index",
    ].eq(100.0).all()
    filled = result.loc[
        result["cbo_4d"].eq("1111")
        & result["periodo_num"].eq(202102)
    ].iloc[0]
    assert filled["admissoes"] == 0
    assert filled["desligamentos"] == 0
    assert filled["saldo"] == 0


def test_stock_proxy_uses_total_pretreatment_gross_flow_as_scale() -> None:
    module = load_module()
    panel = pd.DataFrame(
        {
            "cbo_4d": ["1111", "1111", "1111"],
            "periodo_num": [202101, 202102, 202103],
            "admissoes": [10, 10, 10],
            "desligamentos": [8, 5, 4],
            "included_main": [True] * 3,
            "treated_main": [1, 1, 1],
        }
    )

    result = module.build_stock_proxy(
        panel,
        start_period=202101,
        end_period=202103,
        pre_end_period=202102,
    )

    assert result["pre_gross_flow"].eq(33).all()
    assert np.isclose(
        result.loc[
            result["periodo_num"].eq(202103),
            "stock_proxy_index",
        ].item(),
        100 + 100 * 11 / 33,
    )


def test_generated_stock_proxy_reports_single_adjusted_contrast() -> None:
    results = PACKAGE_ROOT / "results" / "mechanisms"
    estimate = pd.read_csv(results / "stock_proxy_result.csv")
    status = json.loads(
        (results / "stock_proxy_status.json").read_text()
    )
    report = (results / "STOCK_PROXY.md").read_text()

    assert len(estimate) == 1
    assert estimate["bh_adjusted_p_value"].notna().all()
    assert np.allclose(
        estimate["p_value"],
        estimate["bh_adjusted_p_value"],
    )
    assert status["balanced_grid"] is True
    assert status["cbo_count"] == 341
    assert "not an employment-stock level" in report
    assert "unregistered exits" in report
