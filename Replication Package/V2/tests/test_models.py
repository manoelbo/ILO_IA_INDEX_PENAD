from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "models" / "estimators.py"


def load_estimators_module():
    spec = importlib.util.spec_from_file_location(
        "estimators",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load estimators.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_principal_formula_excludes_contemporary_composition() -> None:
    module = load_estimators_module()

    formula = module.build_formula(
        outcome="admissoes",
        treatment_term="post_treat",
        fixed_effects=("cbo_4d", "periodo"),
        controls=(),
    )

    assert formula == "admissoes ~ post_treat | cbo_4d + periodo"
    for forbidden in module.CONTEMPORARY_CONTROLS:
        assert forbidden not in formula


def test_principal_spec_rejects_contemporary_composition() -> None:
    module = load_estimators_module()

    with pytest.raises(ValueError, match="contemporary composition"):
        module.validate_principal_controls(("pct_mulher_adm",))


def test_cluster_interval_uses_cluster_t_degrees_of_freedom() -> None:
    module = load_estimators_module()

    inference = module.cluster_t_inference(
        coefficient=1.0,
        standard_error=0.5,
        cluster_counts={"cbo_4d": 10},
    )
    critical = 2.2621571627409915

    assert inference["cluster_df"] == 9
    assert inference["ci_low"] == pytest.approx(1.0 - critical * 0.5)
    assert inference["ci_high"] == pytest.approx(1.0 + critical * 0.5)
    assert inference["critical_value"] != pytest.approx(1.96)


def test_two_way_cluster_df_uses_smaller_cluster_dimension() -> None:
    module = load_estimators_module()

    inference = module.cluster_t_inference(
        coefficient=0.1,
        standard_error=0.02,
        cluster_counts={"cbo_4d": 341, "divisao": 87},
    )

    assert inference["cluster_df"] == 86
