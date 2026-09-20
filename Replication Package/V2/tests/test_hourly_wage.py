from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "models" / "hourly_wage.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "hourly_wage",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load hourly_wage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hourly_wage_uses_220_hour_divisor_for_44_hour_week() -> None:
    module = load_module()

    assert module.monthly_to_hourly_wage(2_200.0, 44.0) == 10.0
    assert np.isnan(module.monthly_to_hourly_wage(2_200.0, 0.0))


def test_continuity_gate_rejects_structural_break_not_small_one_month_dip() -> None:
    module = load_module()
    acceptable = pd.Series([100.0, 100.0, 97.6, 100.0, 99.9])
    broken = pd.Series([100.0, 89.0, 88.0, 87.0, 86.0])

    passed = module.evaluate_hours_continuity(acceptable)
    failed = module.evaluate_hours_continuity(broken)

    assert passed["status"] == "pass"
    assert failed["status"] == "fail"
    assert failed["adjacent_change_above_10pp"] is True
    assert failed["three_consecutive_months_below_95pct"] is True


def test_generated_hourly_family_has_support_and_adjusted_p_values() -> None:
    results = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "mechanisms"
    )
    estimates = pd.read_csv(results / "hourly_wage_results.csv")
    coverage = pd.read_csv(results / "hourly_wage_coverage.csv")
    status = json.loads(
        (results / "hourly_wage_status.json").read_text()
    )

    assert len(estimates) == 5
    assert estimates["bh_adjusted_p_value"].notna().all()
    assert len(coverage) == 65
    assert status["continuity_gate"]["status"] == "pass"
    assert status["model_count"] == 5
