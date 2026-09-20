from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "pnadc" / "backing_data"
)
V2_MODELS = PACKAGE_ROOT / "code" / "caged" / "models"
sys.path.insert(0, str(V2_MODELS))

from heterogeneity import benjamini_hochberg  # noqa: E402
from v2_pnadc.pnadc_estimation import BASE_RESULT_COLUMNS  # noqa: E402
from v2_pnadc.pnadc_sensitivities import build_sensitivity_grid  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_p9_reports_all_three_diagnostics_in_both_samples() -> None:
    pretrends = pd.read_csv(RESULTS_DIR / "pnadc_pretrends.csv")

    assert len(pretrends) == 12
    assert pretrends["outcome"].nunique() == 6
    assert set(pretrends["sample"]) == {"full", "without_2020"}
    assert pretrends["pretrend_status"].eq("fail").all()
    assert pretrends["lead_covariance_positive_semidefinite"].all()
    assert pretrends["post_event_coefficients_published"].eq(False).all()
    assert pretrends["non_rejection_is_proof"].eq(False).all()
    assert pretrends["pretrend_timing"].eq(
        "structural_difference_persists_without_2020"
    ).all()


def test_p10_family_e_is_complete_and_adjusted_once() -> None:
    results = pd.read_csv(RESULTS_DIR / "pnadc_results.csv")
    pretrends = pd.read_csv(RESULTS_DIR / "pnadc_pretrends.csv")

    assert len(results) == 6
    assert set(BASE_RESULT_COLUMNS).issubset(results.columns)
    assert results["family_id"].eq("E").all()
    assert results["family_size"].eq(6).all()
    expected_bh = benjamini_hochberg(
        results["nominal_p_value"].to_numpy(),
        family_size=6,
    )
    np.testing.assert_allclose(
        results["bh_adjusted_p_value"],
        expected_bh,
        rtol=0,
        atol=1e-15,
    )
    assert results["significance_symbol"].fillna("").eq("").all()
    assert results["pretrend_status_full"].eq("fail").all()
    assert results["pretrend_status_without_2020"].eq("fail").all()
    assert results.loc[
        results["outcome"].eq("ln_renda"),
        "is_reconciliation",
    ].item()
    assert not results.loc[
        results["outcome"].eq("ln_renda"),
        "is_principal",
    ].item()
    full_nobs = (
        pretrends.loc[pretrends["sample"].eq("full")]
        .set_index("outcome")["n_obs"]
    )
    result_nobs = results.set_index("outcome")["n_obs"]
    pd.testing.assert_series_equal(
        result_nobs.sort_index(),
        full_nobs.sort_index(),
        check_names=False,
        check_dtype=False,
    )


def test_p11_contains_only_the_18_nonprincipal_sensitivities() -> None:
    sensitivities = pd.read_csv(
        RESULTS_DIR / "pnadc_sensitivities.csv"
    )
    pretrends = pd.read_csv(RESULTS_DIR / "pnadc_pretrends.csv")
    expected = {
        (row["sensitivity_id"], row["outcome"])
        for row in build_sensitivity_grid()
    }
    observed = set(
        zip(
            sensitivities["sensitivity_id"],
            sensitivities["outcome"],
            strict=True,
        )
    )

    assert len(sensitivities) == 18
    assert observed == expected
    assert sensitivities["result_status"].eq("estimated").all()
    assert not sensitivities["is_principal"].any()
    assert sensitivities["family_id"].eq("none").all()
    assert sensitivities["bh_adjusted_p_value"].isna().all()
    assert sensitivities["significance_symbol"].fillna("").eq("").all()
    without = sensitivities.loc[
        sensitivities["sensitivity_id"].eq("without_2020")
    ].set_index("outcome")
    p9_without = pretrends.loc[
        pretrends["sample"].eq("without_2020")
    ].set_index("outcome")
    pd.testing.assert_series_equal(
        without["n_obs"].sort_index(),
        p9_without["n_obs"].sort_index(),
        check_names=False,
        check_dtype=False,
    )


def test_cross_language_receipts_cover_static_and_pretrend_models() -> None:
    static = read_json(RESULTS_DIR / "pnadc_cross_replication_status.json")
    pretrends = read_json(RESULTS_DIR / "pnadc_pretrend_cross_status.json")

    assert static["status"] == "pass"
    assert static["models"] == 6
    assert pretrends["status"] == "pass"
    assert pretrends["models"] == 12
    assert pretrends["failed_models"] == 0


def test_part2_reports_state_composition_not_transition() -> None:
    text = (PACKAGE_ROOT / "RESEARCH_DESIGN.md").read_text(encoding="utf-8")
    assert "composition is not a worker transition" in text
    assert "complementary measurement exercises" in text
