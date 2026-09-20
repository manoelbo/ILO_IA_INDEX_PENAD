from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    PACKAGE_ROOT / "code" / "caged" / "models" / "separation_mechanisms.py"
)


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "separation_mechanisms",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load separation_mechanisms.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_separation_code_families_are_mutually_exclusive() -> None:
    module = load_module()

    observed = {
        code: module.separation_family(code)
        for code in ("31", "40", "43", "45", "32", "33", "90", "98")
    }

    assert observed["31"] == "dismissal_without_cause"
    assert observed["40"] == "resignation"
    assert observed["43"] == "contract_end"
    assert observed["45"] == "contract_end"
    assert observed["32"] == "dismissal_with_cause"
    assert observed["33"] == "dismissal_with_cause"
    assert observed["90"] == "mutual_agreement"
    assert observed["98"] == "unknown_separation"
    assert module.EXCLUDED_CODES == ("50", "60", "80")
    assert len(module.SEPARATION_FAMILIES) == 6


def test_unknown_separation_code_fails_fast() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="Unclassified"):
        module.separation_family("99")


def test_reconciliation_requires_named_plus_excluded_to_equal_total() -> None:
    module = load_module()
    frame = pd.DataFrame(
        {
            "periodo_num": [202101, 202102],
            "panel_total": [100, 120],
            "named_families": [95, 110],
            "excluded": [5, 10],
        }
    )

    result = module.validate_reconciliation(frame)

    assert result["difference"].eq(0).all()


def test_reconciliation_rejects_silent_gap() -> None:
    module = load_module()
    frame = pd.DataFrame(
        {
            "periodo_num": [202101],
            "panel_total": [100],
            "named_families": [94],
            "excluded": [5],
        }
    )

    with pytest.raises(RuntimeError, match="reconcile"):
        module.validate_reconciliation(frame)


def test_bh_adjustment_uses_frozen_six_outcome_family() -> None:
    module = load_module()

    adjusted = module.benjamini_hochberg(
        np.array([0.001, 0.01, 0.20]),
        family_size=6,
    )

    assert np.allclose(adjusted, [0.006, 0.03, 0.4])


def test_generated_mechanism_family_is_complete_and_reconciled() -> None:
    results = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "mechanisms"
    )
    reconciliation = pd.read_csv(
        results / "separation_family_reconciliation.csv"
    )
    support = pd.read_csv(
        results / "separation_family_support.csv"
    )
    static = pd.read_csv(
        results / "separation_static_results.csv"
    )
    event = pd.read_csv(
        results / "separation_event_study.csv"
    )
    status = json.loads(
        (
            results / "separation_mechanisms_status.json"
        ).read_text()
    )

    assert reconciliation["difference"].eq(0).all()
    assert reconciliation["raw_panel_difference"].eq(0).all()
    assert len(support) == 6
    assert len(static) == 6
    assert static["bh_adjusted_p_value"].notna().all()
    assert len(event) == 282
    assert event.groupby("family")["event_time"].apply(
        lambda values: sorted(values.tolist()) == list(range(-23, 24))
    ).all()
    assert event.loc[
        event["is_reference"].eq(False),
        "bh_adjusted_p_value",
    ].notna().all()
    assert status["reconciliation_exact"] is True
    assert status["event_family_size"] == 276
