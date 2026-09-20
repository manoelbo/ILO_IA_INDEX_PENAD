from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "models" / "event_study.py"


def load_event_module():
    spec = importlib.util.spec_from_file_location(
        "event_study",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load event_study.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_balanced_event_grid_is_complete_and_has_november_reference() -> None:
    module = load_event_module()

    grid = module.build_event_grid()
    module.validate_event_grid(grid)

    assert grid["event_time"].tolist() == list(range(-23, 24))
    assert grid.loc[grid["is_reference"], "event_time"].tolist() == [-1]
    assert grid.loc[grid["event_time"].eq(-1), "periodo"].item() == "2022-11"


def test_event_grid_rejects_holes() -> None:
    module = load_event_module()
    grid = module.build_event_grid()
    with_hole = grid.loc[grid["event_time"].ne(4)].copy()

    with pytest.raises(RuntimeError, match="complete"):
        module.validate_event_grid(with_hole)


def test_event_time_maps_december_2022_to_zero() -> None:
    module = load_event_module()
    periods = pd.Series([202101, 202211, 202212, 202411])

    observed = module.event_time_from_period(periods)

    assert observed.tolist() == [-23, -1, 0, 23]


def test_pyfixest_event_coefficient_name_is_parsed() -> None:
    module = load_event_module()
    name = (
        "C(event_time, contr.treatment(base=-1))"
        "[-23]:treated_main"
    )

    assert module.parse_event_time_coefficient(name) == -23
