from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "models" / "employer_size.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "employer_size",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load employer_size.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_official_size_categories_are_complete() -> None:
    module = load_module()

    assert list(module.SIZE_CATEGORIES) == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
    ]
    assert module.SIZE_CATEGORIES["1"] == "Zero employees"
    assert module.SIZE_CATEGORIES["10"] == "1,000 or more"


def test_registration_fields_do_not_identify_public_private() -> None:
    module = load_module()

    assessment = module.public_private_identification_assessment()

    assert assessment["identified"] is False
    assert assessment["status"] == "not_executed_nonidentifying_fields"
    assert "public" not in set(module.EMPLOYER_TYPE_LABELS.values())
    assert "private" not in set(module.EMPLOYER_TYPE_LABELS.values())


def test_generated_size_family_and_nature_support_are_complete() -> None:
    results = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "mechanisms"
    )
    estimates = pd.read_csv(results / "employer_size_ddd_results.csv")
    size_support = pd.read_csv(results / "employer_size_support.csv")
    nature_support = pd.read_csv(
        results / "employer_registration_support.csv"
    )
    status = json.loads(
        (results / "employer_size_status.json").read_text()
    )

    assert len(estimates) == 50
    assert estimates["bh_adjusted_p_value"].notna().all()
    assert size_support["size_code"].nunique() == 10
    assert {
        "tipoempregador",
        "tipoestabelecimento",
    } == set(nature_support["dimension"])
    assert (
        status["public_private_falsification"]["identified"]
        is False
    )
