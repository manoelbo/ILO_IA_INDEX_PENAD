from __future__ import annotations

import importlib
import json
import math
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "pnadc" / "backing_data"
)


def load_module():
    return importlib.import_module("v2_pnadc.pnadc_cross_replication")


def test_crv1_rescaling_replaces_collapsed_n_with_original_n() -> None:
    module = load_module()

    observed = module.crv1_standard_error_rescale(
        original_n=100,
        collapsed_n=20,
        df_k=5,
    )
    expected = math.sqrt(((100 - 1) / (100 - 5)) / ((20 - 1) / (20 - 5)))

    assert math.isclose(observed, expected, rel_tol=0, abs_tol=1e-15)


def test_comparison_requires_six_decimal_agreement_and_same_samples() -> None:
    module = load_module()
    python_rows = pd.DataFrame(
        {
            "model_id": ["m1", "m2"],
            "outcome": ["informal", "ocupados_total"],
            "arm": ["A", "B"],
            "coefficient": [0.1, -0.2],
            "standard_error": [0.03, 0.04],
            "n_obs": [100, 200],
            "minimum_clusters": [10, 20],
        }
    )
    r_rows = pd.DataFrame(
        {
            "model_id": ["m1", "m2"],
            "coefficient": [0.1000000001, -0.1999999999],
            "standard_error": [0.0300000001, 0.0400000001],
            "n_obs": [100, 200],
            "n_clusters": [10, 20],
        }
    )

    comparison, status = module.compare_results(
        python_rows,
        r_rows,
        expected_models=2,
    )

    assert len(comparison) == 2
    assert status["six_decimal_agreement"] is True
    assert status["same_n_and_clusters"] is True
    assert status["status"] == "pass"


def test_actual_cross_replication_covers_all_family_e_models() -> None:
    status = json.loads(
        (
            RESULTS_DIR / "pnadc_cross_replication_status.json"
        ).read_text(encoding="utf-8")
    )
    comparison = pd.read_csv(
        RESULTS_DIR / "pnadc_cross_replication_comparison.csv"
    )

    assert status["status"] == "pass"
    assert status["models"] == 6
    assert status["six_decimal_agreement"] is True
    assert status["same_n_and_clusters"] is True
    assert status["r_fixest_models"] == 6
    assert len(comparison) == 6
    assert comparison["coefficient_matches_6_decimals"].all()
    assert comparison["standard_error_matches_6_decimals"].all()
    assert comparison["same_n"].all()
    assert comparison["same_clusters"].all()
    assert set(comparison["arm"]) == {"A", "B"}
    assert not comparison["outcome"].eq("horas_trabalhadas").any()
    assert not any(
        "cod4" in column.lower() for column in comparison.columns
    )
