from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "models" / "pretrends.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "pretrends",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pretrends.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pretrend_classification_contract() -> None:
    module = load_module()

    assert module.classify_pretrend(0.20, 0.30, 0) == "pass"
    assert module.classify_pretrend(0.049, 0.30, 0) == "fail"
    assert module.classify_pretrend(0.20, 0.049, 0) == "fail"
    assert module.classify_pretrend(0.20, 0.30, 2) == "fail"
    assert module.classify_pretrend(0.08, 0.30, 0) == "warning"
    assert module.classify_pretrend(0.20, 0.30, 1) == "warning"


def test_gls_slope_recovers_linear_leads() -> None:
    module = load_module()
    event_times = np.array([-4, -3, -2], dtype=float)
    design = event_times + 1.0
    coefficients = 0.02 * design
    covariance = np.diag([0.04, 0.03, 0.02])

    result = module.gls_pretrend_slope(
        coefficients,
        covariance,
        event_times,
        {"cbo_4d": 341},
    )

    assert np.isclose(result["coefficient"], 0.02)
    assert result["standard_error"] > 0
    assert result["cluster_df"] == 340


def test_honest_did_export_keeps_only_linear_outcomes() -> None:
    module = load_module()
    records = [
        module.HonestDidModel(
            outcome="ln_salario_real_adm",
            estimator="ols",
            event_times=(-2, 0),
            coefficients=np.array([-0.1, 0.2]),
            covariance=np.eye(2),
        ),
        module.HonestDidModel(
            outcome="admissoes",
            estimator="ppml",
            event_times=(-2, 0),
            coefficients=np.array([-0.1, 0.2]),
            covariance=np.eye(2),
        ),
    ]

    coefficients, covariance = module.build_honest_did_exports(records)

    assert coefficients["outcome"].unique().tolist() == [
        "ln_salario_real_adm"
    ]
    assert coefficients["event_time"].tolist() == [-2, 0]
    assert len(covariance) == 4
