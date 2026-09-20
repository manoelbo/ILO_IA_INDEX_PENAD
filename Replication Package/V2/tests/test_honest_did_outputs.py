from __future__ import annotations

from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CAGED_REFERENCE = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "caged"
)
DIAGNOSTICS = CAGED_REFERENCE / "diagnostics"


def test_honest_did_parallel_map_keeps_explicit_deterministic_seeds() -> None:
    for name in ("honest_did.R", "honest_did_sd.R"):
        script = (PACKAGE_ROOT / "R" / name).read_text(encoding="utf-8")
        assert "parallel::mclapply(" in script
        assert "mc.set.seed = FALSE" in script
        assert 'Sys.getenv("REPLICATION_R_WORKERS", unset = "4")' in script
        assert "seed = 20260726" in script
EXPECTED_OUTCOMES = {"asinh_saldo", "ln_salario_real_adm"}
# Phase 8A added Delta^SD beside the released Delta^RM. The two restrictions
# measure M on incomparable scales — a ratio against the largest pre-period
# violation, and an absolute bound on the curvature — so every contract below
# is checked within a restriction, never across them.
RESTRICTIONS = {"DeltaRM", "DeltaSD"}


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        pd.read_csv(DIAGNOSTICS / "honest_did_sensitivity.csv"),
        pd.read_csv(DIAGNOSTICS / "honest_did_summary.csv"),
    )


def test_honest_did_outputs_cover_frozen_linear_contract() -> None:
    results, summary = load()

    assert set(results["outcome"]) == EXPECTED_OUTCOMES
    assert set(summary["outcome"]) == EXPECTED_OUTCOMES
    assert set(results["Delta"]) == RESTRICTIONS
    assert set(summary["Delta"]) == RESTRICTIONS
    assert results["method"].eq("C-LF").all()
    assert results["target"].eq("average_post_event_time_0_to_23").all()

    relative = results.loc[results["Delta"].eq("DeltaRM")]
    for _, group in relative.groupby("outcome"):
        assert group["M"].tolist() == [value / 20 for value in range(41)]
        assert (
            group["internal_grid_lower"] < group["internal_grid_upper"]
        ).all()

    smoothness = results.loc[results["Delta"].eq("DeltaSD")]
    for _, group in smoothness.groupby("outcome"):
        assert group["M"].is_monotonic_increasing
        assert group["M"].min() == 0
        assert group["M"].is_unique
        # The grid ends at the largest absolute second difference actually
        # observed in the pre-period, so the reader can locate the estimated
        # wiggle against the breakdown point.
        assert (
            group["M"].max()
            == group["observed_pre_period_curvature"].iloc[0]
        )


def test_honest_did_summary_matches_sensitivity_grid() -> None:
    results, summary = load()

    for row in summary.itertuples():
        cell = results.loc[
            results["outcome"].eq(row.outcome)
            & results["Delta"].eq(row.Delta)
        ]
        assert not cell.empty
        robust = cell.loc[cell["excludes_zero"]]
        if robust.empty:
            assert pd.isna(row.largest_evaluated_M_excluding_zero)
            assert row.threshold_status == "not_robust_at_M_0"
        else:
            assert (
                row.largest_evaluated_M_excluding_zero
                == robust["M"].max()
            )


def test_relative_magnitude_summary_keeps_its_released_fields() -> None:
    _, summary = load()
    relative = summary.loc[summary["Delta"].eq("DeltaRM")]

    assert len(relative) == 2
    for row in relative.itertuples():
        assert row.robustness_threshold_precedes_open_grid
        assert (DIAGNOSTICS / row.plot_path).is_file()


def test_smoothness_summary_declares_its_own_grid() -> None:
    _, summary = load()
    smoothness = summary.loc[summary["Delta"].eq("DeltaSD")]

    assert len(smoothness) == 2
    for row in smoothness.itertuples():
        assert row.m_units == (
            "absolute_second_difference_of_the_differential_trend"
        )
        assert row.search_half_width_in_target_se == 20
        assert row.coarse_grid_points == 25
        assert row.refined_grid_points == 201
        assert row.num_pre_periods == 22
        assert row.num_post_periods == 24
        comparison = DIAGNOSTICS / (
            f"honest_did_delta_comparison_{row.outcome}.png"
        )
        assert comparison.is_file()
