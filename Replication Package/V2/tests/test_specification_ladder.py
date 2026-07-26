from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PACKAGE_ROOT / "code" / "models" / "specification_ladder.py"
)


def load_ladder_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "specification_ladder",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load specification_ladder.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ladder_contains_every_preregistered_step_in_order() -> None:
    module = load_ladder_module()

    observed = [step["step_id"] for step in module.ladder_contract()]

    assert observed == [
        "01_no_controls",
        "02_pre_treatment_controls_x_post",
        "03_contemporary_controls",
        "04_include_minimal_as_control",
        "05_continuous_exposure",
        "06_start_2022_01",
        "07_end_2025_12",
    ]


def test_contemporary_controls_are_explicitly_descriptive() -> None:
    module = load_ladder_module()
    steps = {
        step["step_id"]: step for step in module.ladder_contract()
    }

    contemporary = steps["03_contemporary_controls"]

    assert contemporary["controls"] == module.CONTEMPORARY_CONTROLS
    assert contemporary["causal_role"] == "descriptive_post_treatment"
    assert steps["01_no_controls"]["controls"] == ()
    assert steps["01_no_controls"]["causal_role"] == "principal"
