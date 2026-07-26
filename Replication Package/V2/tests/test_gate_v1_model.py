from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "models" / "gate_v1_model.py"


def load_gate_module():
    spec = importlib.util.spec_from_file_location(
        "gate_v1_model",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gate_v1_model.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_gate_data_keeps_exact_v1_window_and_contrast() -> None:
    module = load_gate_module()
    panel = pd.DataFrame(
        {
            "cbo_4d": ["1111", "1111", "2222", "3333"],
            "periodo_num": [202012, 202212, 202301, 202401],
            "periodo": ["2020-12", "2022-12", "2023-01", "2024-01"],
            "post": [0, 1, 1, 1],
            "included_main": [True, True, True, False],
            "treated_main": [1.0, 1.0, 0.0, None],
        }
    )

    prepared = module.prepare_gate_data(panel)

    assert prepared["cbo_4d"].tolist() == ["1111", "2222"]
    assert prepared["post_treat"].tolist() == [1.0, 0.0]


def test_comparison_flags_sign_and_significance_changes() -> None:
    module = load_gate_module()
    reference = pd.DataFrame(
        {
            "outcome": ["ln_admissoes"],
            "v1_outcome": ["ln_admissoes"],
            "v1_coef": [-0.03],
            "v1_se": [0.02],
            "v1_p_value": [0.13],
        }
    )
    estimates = pd.DataFrame(
        {
            "outcome": ["ln_admissoes"],
            "v2_coef": [0.05],
            "v2_se": [0.01],
            "v2_p_value": [0.001],
            "n_obs": [100],
            "n_cbo": [10],
        }
    )

    comparison = module.build_comparison(reference, estimates)
    row = comparison.iloc[0]

    assert row["delta"] == 0.08
    assert row["delta_abs"] == 0.08
    assert row["changed_sign"]
    assert row["crossed_significance_5pct"]
    assert not row["v1_significant_5pct"]
    assert row["v2_significant_5pct"]


def test_v1_reference_matches_preregistered_coefficients() -> None:
    module = load_gate_module()

    reference = module.load_v1_reference(module.DEFAULT_V1_REFERENCE)

    observed = reference.set_index("outcome")["v1_coef"].to_dict()
    assert observed == pytest.approx(
        {
            "ln_admissoes": -0.03087879481033855,
            "ln_desligamentos": -0.04165839040785939,
            "ln_salario_real_adm": -0.020706489590455807,
            "asinh_saldo": -0.6596605902038598,
        }
    )
