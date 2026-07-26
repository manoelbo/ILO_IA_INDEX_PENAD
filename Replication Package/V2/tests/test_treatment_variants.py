from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "panel" / "treatment_variants.py"


def load_variants_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "treatment_variants",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load treatment_variants.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_weighted_dispersion_separates_task_and_destination_parts() -> None:
    module = load_variants_module()
    scores = [0.4, 0.6]
    task_sds = [0.1, 0.2]
    weights = [1.0, 3.0]

    mean = module.weighted_mean(scores, weights)
    task_sd = module.task_only_sd(task_sds, weights)
    between_sd = module.between_destination_sd(
        scores,
        weights,
    )
    pooled_sd = module.pooled_weighted_sd(
        scores,
        task_sds,
        weights,
    )

    assert mean == pytest.approx(0.55)
    assert task_sd == pytest.approx(math.sqrt(0.0325))
    assert between_sd == pytest.approx(math.sqrt(0.0075))
    assert pooled_sd == pytest.approx(
        math.sqrt(task_sd**2 + between_sd**2)
    )


def test_weighted_label_tie_uses_less_exposed_label() -> None:
    module = load_variants_module()

    label = module.weighted_mode_label(
        ["Exposed: Gradient 3", "Minimal Exposure"],
        [5.0, 5.0],
    )

    assert label == "Minimal Exposure"


def test_destination_weights_split_each_cbo6_employment_equally() -> None:
    module = load_variants_module()

    weights = module.split_cbo6_weight(
        admission_weight=12.0,
        destination_count=3,
    )

    assert weights == [4.0, 4.0, 4.0]
    assert sum(weights) == 12.0
