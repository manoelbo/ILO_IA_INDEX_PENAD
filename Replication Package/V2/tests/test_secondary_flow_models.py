from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PACKAGE_ROOT / "code" / "models" / "secondary_flow_models.py"
)


def load_module():
    sys.path.insert(0, str(PACKAGE_ROOT / "code" / "models"))
    spec = importlib.util.spec_from_file_location(
        "secondary_flow_models",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load secondary_flow_models.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_secondary_outcomes_are_log_one_plus_flow() -> None:
    module = load_module()
    panel = pd.DataFrame(
        {
            "included_main": [True, True, False],
            "treated_main": [1, 0, 1],
            "post": [1, 0, 1],
            "admissoes": [0, 9, 99],
            "desligamentos": [3, 0, 99],
            "n_movimentacoes": [3, 9, 198],
        }
    )

    sample = module.prepare_secondary_data(panel)

    assert len(sample) == 2
    assert sample["log1p_admissoes"].tolist() == [0.0, np.log(10)]
    assert sample["log1p_desligamentos"].tolist() == [np.log(4), 0.0]
    assert sample["post_treat"].tolist() == [1, 0]


def test_secondary_contract_has_three_ols_models() -> None:
    module = load_module()

    specifications = module.secondary_specifications()

    assert len(specifications) == 3
    assert {item["estimator"] for item in specifications} == {"ols"}
    assert {item["treatment_term"] for item in specifications} == {
        "post_treat"
    }
    assert not any(item["principal"] for item in specifications)
