from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "models" / "heterogeneity.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "heterogeneity",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load heterogeneity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ddd_contract_contains_triple_and_all_lower_terms() -> None:
    module = load_module()

    treatment, lower_terms = module.ddd_formula_contract()

    assert treatment == "post_treat_group"
    assert set(lower_terms) == {
        "post_treat",
        "post_group",
        "treat_group",
    }
    module.validate_ddd_formula_terms(
        [treatment, *lower_terms]
    )


def test_ddd_contract_rejects_missing_lower_term() -> None:
    module = load_module()

    try:
        module.validate_ddd_formula_terms(
            [
                "post_treat_group",
                "post_treat",
                "post_group",
            ]
        )
    except ValueError as error:
        assert "treat_group" in str(error)
    else:
        raise AssertionError("Incomplete DDD formula was accepted")


def test_cbo_level_lower_term_is_declared_but_absorbed() -> None:
    module = load_module()

    controls, absorbed = module.estimable_lower_terms(
        "cbo_predetermined"
    )

    assert controls == ("post_treat", "post_group")
    assert absorbed == ("treat_group",)
    module.validate_ddd_formula_terms(
        [
            module.DDD_TREATMENT_TERM,
            *controls,
            *absorbed,
        ]
    )


def test_bh_uses_frozen_planned_family_size() -> None:
    module = load_module()

    adjusted = module.benjamini_hochberg(
        np.array([0.001, 0.01, np.nan, 0.20]),
        family_size=10,
    )

    assert np.allclose(
        adjusted[[0, 1, 3]],
        [0.01, 0.05, 2 / 3],
    )
    assert np.isnan(adjusted[2])


def test_planned_family_has_100_contrasts() -> None:
    module = load_module()

    assert sum(
        len(spec["groups"])
        for spec in module.DIMENSIONS.values()
    ) == 20
    assert len(module.OUTCOMES) == 5
    assert module.PLANNED_FAMILY_SIZE == 100


def test_support_thresholds_are_encoded_in_source() -> None:
    module = load_module()

    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "treated >= 20 and control >= 50" in source
    assert "treated >= 10 and control >= 25" in source


def test_generated_family_is_complete_and_reports_both_p_values() -> None:
    results = pd.read_csv(
        PACKAGE_ROOT
        / "results"
        / "diagnostics"
        / "ddd_multiplicity_results.csv"
    )

    assert len(results) == 100
    assert results["result_status"].eq("estimated").all()
    assert results["nominal_p_value"].notna().all()
    assert results["bh_adjusted_p_value"].notna().all()
    assert {
        "post_treat_group",
        "post_treat",
        "post_group",
        "treat_group",
    } == set(
        __import__("json").loads(
            results["declared_ddd_terms"].iloc[0]
        )
    )
    assert set(results["support_status"]) <= {
        "adequate",
        "limited",
        "thin",
    }
