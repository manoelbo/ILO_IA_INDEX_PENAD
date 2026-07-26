from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "models" / "sector_models.py"


def load_sector_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "sector_models",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load sector_models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sector_contract_uses_section_fe_and_division_cluster() -> None:
    module = load_sector_module()
    contracts = {
        item["level_id"]: item for item in module.sector_model_contract()
    }

    assert contracts["level_2"]["fixed_effects"] == (
        "cbo_section",
        "section_period",
    )
    assert contracts["level_2"]["cluster_variables"] == ("cbo_4d",)
    assert contracts["level_2_two_way"]["cluster_variables"] == (
        "cbo_4d",
        "divisao",
    )
    assert contracts["level_3"]["fixed_effects"] == (
        "cbo_section",
        "section_period",
        "cbo2_period",
    )


def test_level_three_is_always_labeled_support_diagnostic() -> None:
    module = load_sector_module()
    level_three = {
        item["level_id"]: item
        for item in module.sector_model_contract()
    }["level_3"]

    assert level_three["role"] == "support_diagnostic"
