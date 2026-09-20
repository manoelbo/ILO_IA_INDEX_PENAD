"""Unit tests for the Phase 8A pretrend machinery."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PACKAGE_ROOT / "code" / "caged" / "models"


def load(name: str):
    if str(MODELS_DIR) not in sys.path:
        sys.path.insert(0, str(MODELS_DIR))
    spec = importlib.util.spec_from_file_location(
        name,
        MODELS_DIR / f"{name}.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_event_time_is_interaction_specific() -> None:
    engine = load("pretrend_engine")

    name = "C(event_time,contr.treatment(base=-1))[T.-11]:treated_main"
    assert engine.parse_event_time(name, "treated_main") == -11
    with pytest.raises(ValueError):
        engine.parse_event_time(name, "exposure_z")

    continuous = "C(event_time,contr.treatment(base=-1))[T.7]:exposure_z"
    assert engine.parse_event_time(continuous, "exposure_z") == 7


def test_restrict_event_window_rejects_holes() -> None:
    engine = load("pretrend_engine")

    complete = pd.DataFrame({"event_time": [-2, -1, 0, 1]})
    assert len(engine.restrict_event_window(complete, -2, 1)) == 4

    with_hole = pd.DataFrame({"event_time": [-2, -1, 1]})
    with pytest.raises(RuntimeError, match="hole"):
        engine.restrict_event_window(with_hole, -2, 1)


def test_minimum_detectable_effect_scales_with_the_standard_error() -> None:
    engine = load("pretrend_engine")

    single = engine.minimum_detectable_effect(0.01, 340)
    double = engine.minimum_detectable_effect(0.02, 340)

    assert np.isclose(double, 2 * single)
    # Two-sided 5% with 80% power is roughly 2.8 standard errors.
    assert 2.7 < single / 0.01 < 2.9
    assert np.isnan(engine.minimum_detectable_effect(0.0, 340))
    assert np.isnan(engine.minimum_detectable_effect(np.nan, 340))


def test_power_reading_distinguishes_the_three_preregistered_cases() -> None:
    variants = load("pretrend_national_variants")

    def reading(full_p: float, restricted_p: float) -> str:
        sample = pd.DataFrame(
            {
                "outcome": ["y"],
                "joint_lead_p_value": [restricted_p],
                "pretrend_status": ["fail"],
                "joint_lead_count": [10],
            }
        )
        power = pd.DataFrame(
            {
                "specification_id": [
                    "balanced_frozen_window",
                    "extended_full_sample",
                    "extended_full_sample",
                ],
                "outcome": ["y", "y", "y"],
                "joint_lead_window": [
                    "-23_to_-2",
                    "-23_to_-2",
                    "-11_to_-2",
                ],
                "joint_lead_p_value": [1e-9, 1e-9, full_p],
                "pretrend_status": ["fail", "fail", "fail"],
                "joint_lead_count": [22, 22, 10],
            }
        )
        return variants.build_power_reading(sample, power)[
            "power_reading"
        ].item()

    assert reading(1e-4, 0.40) == "violation_concentrated_in_2021"
    assert reading(0.40, 0.40) == "gain_is_power_not_substance"
    assert reading(1e-4, 1e-4) == "violation_not_specific_to_2021"


def test_horizon_terms_cover_the_four_preregistered_horizons() -> None:
    horizons = load("long_run_horizons")

    assert horizons.horizon_terms() == (
        "h1_treat",
        "h2_treat",
        "h3_treat",
        "h4_treat",
    )
    partial = [
        key for _, key, is_partial in horizons.HORIZONS if is_partial
    ]
    assert partial == ["h4"]


def test_ddd_pretrend_uses_the_saturated_fixed_effects() -> None:
    ddd = load("ddd_pretrends")

    assert ddd.DDD_FIXED_EFFECTS == (
        "cbo_4d^subgroup",
        "periodo^subgroup",
        "periodo^treatment",
    )
    # Lower-order dynamics must be absorbed, not estimated beside the triple
    # interaction, otherwise the diagnostic is not the DDD pretrend.
    assert "treat_group" not in ddd.DDD_FIXED_EFFECTS


def test_trend_control_specifications_are_never_principal() -> None:
    control = load("pretrend_control_spec")

    roles = {
        item["specification_id"]: item["causal_role"]
        for item in control.SPECIFICATIONS
    }
    assert roles["01_predetermined_pretrend_control"] == "robustness"
    assert roles["02_differential_linear_trend"] == "robustness"
    assert "principal" not in set(roles.values())
