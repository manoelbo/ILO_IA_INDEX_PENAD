from __future__ import annotations

from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = PACKAGE_ROOT / "results" / "diagnostics"


def test_honest_did_outputs_cover_frozen_linear_contract() -> None:
    results = pd.read_csv(
        DIAGNOSTICS / "honest_did_sensitivity.csv"
    )
    summary = pd.read_csv(DIAGNOSTICS / "honest_did_summary.csv")

    expected_outcomes = {
        "asinh_saldo",
        "ln_salario_real_adm",
    }
    assert set(results["outcome"]) == expected_outcomes
    assert set(summary["outcome"]) == expected_outcomes
    for _, group in results.groupby("outcome"):
        assert group["M"].tolist() == [
            value / 20 for value in range(41)
        ]
        assert group["method"].eq("C-LF").all()
        assert group["Delta"].eq("DeltaRM").all()
        assert group["target"].eq(
            "average_post_event_time_0_to_23"
        ).all()
        assert (
            group["internal_grid_lower"]
            < group["internal_grid_upper"]
        ).all()


def test_honest_did_summary_matches_sensitivity_grid() -> None:
    results = pd.read_csv(
        DIAGNOSTICS / "honest_did_sensitivity.csv"
    )
    summary = pd.read_csv(DIAGNOSTICS / "honest_did_summary.csv")

    for row in summary.itertuples():
        outcome = results.loc[results["outcome"].eq(row.outcome)]
        robust = outcome.loc[outcome["excludes_zero"]]
        expected = float("nan") if robust.empty else robust["M"].max()
        if robust.empty:
            assert pd.isna(row.largest_evaluated_M_excluding_zero)
        else:
            assert row.largest_evaluated_M_excluding_zero == expected
        assert row.robustness_threshold_precedes_open_grid
        assert (DIAGNOSTICS / row.plot_path).is_file()
