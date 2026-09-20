"""Gate 8A acceptance checks.

These test the *artefacts*, not the code: they fail if a required diagnostic
is missing, if the January 2022 result is ever published without its power
check beside it, if the horizon table degrades back into a period mapping, or
if the report starts recommending a principal specification.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CAGED_REFERENCE = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "caged"
)
DIAGNOSTICS = CAGED_REFERENCE / "diagnostics"
MODELS = CAGED_REFERENCE / "models"
OUTCOMES = {
    "admissoes",
    "desligamentos",
    "n_movimentacoes",
    "ln_salario_real_adm",
    "asinh_saldo",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        pytest.fail(f"Gate 8A requires this artefact: {path}")
    return pd.read_csv(path)


def test_every_required_diagnostic_exists() -> None:
    required = (
        DIAGNOSTICS / "pretrend_sample_2022.csv",
        DIAGNOSTICS / "pretrend_power_check.csv",
        DIAGNOSTICS / "pretrend_ladder_variants.csv",
        DIAGNOSTICS / "pretrend_level2.csv",
        DIAGNOSTICS / "pretrend_wage_balanced_coverage.csv",
        DIAGNOSTICS / "ddd_pretrends.csv",
        DIAGNOSTICS / "pretrend_master_table.csv",
        MODELS / "long_run_horizon_estimates.csv",
        MODELS / "pretrend_control_specification.csv",
    )
    missing = [str(path) for path in required if not path.is_file()]
    assert not missing, f"missing Gate 8A artefacts: {missing}"


def test_2022_sample_never_travels_without_its_power_check() -> None:
    sample = read_csv(DIAGNOSTICS / "pretrend_sample_2022.csv")
    power = read_csv(DIAGNOSTICS / "pretrend_power_check.csv")

    assert set(sample["outcome"]) == OUTCOMES
    for column in (
        "full_sample_matched_leads_p",
        "power_reading",
        "interpretation_rule",
    ):
        assert column in sample.columns, (
            "the restricted-sample result must carry its matched-lead "
            f"comparison in the same file; missing {column}"
        )
        assert sample[column].notna().all()

    matched = power.loc[power["joint_lead_window"].eq("-11_to_-2")]
    assert set(matched["outcome"]) == OUTCOMES
    assert (sample["joint_lead_count"] == 10).all()
    assert set(power["joint_lead_window"]) == {"-23_to_-2", "-11_to_-2"}


def test_power_check_reproduces_the_frozen_joint_test() -> None:
    frozen = read_csv(DIAGNOSTICS / "pretrend_diagnostics.csv")
    power = read_csv(DIAGNOSTICS / "pretrend_power_check.csv")
    rerun = power.loc[
        power["specification_id"].eq("balanced_frozen_window")
        & power["joint_lead_window"].eq("-23_to_-2")
    ]
    merged = frozen[["outcome", "joint_lead_statistic", "n_obs"]].merge(
        rerun[["outcome", "joint_lead_statistic", "n_obs"]],
        on="outcome",
        suffixes=("_frozen", "_rerun"),
        validate="one_to_one",
    )
    assert len(merged) == 5
    assert (merged["n_obs_frozen"] == merged["n_obs_rerun"]).all()
    gap = (
        merged["joint_lead_statistic_frozen"]
        - merged["joint_lead_statistic_rerun"]
    ).abs().max()
    assert gap < 1e-6, f"frozen joint test not reproduced, gap {gap}"


def test_horizons_carry_coefficients_not_only_a_period_mapping() -> None:
    horizons = read_csv(MODELS / "long_run_horizon_estimates.csv")

    assert len(horizons) == 20
    assert set(horizons["outcome"]) == OUTCOMES
    for column in ("coefficient", "standard_error", "p_value"):
        assert horizons[column].notna().all()
    partial = horizons.loc[horizons["partial_horizon"].astype(bool)]
    assert set(partial["horizon"]) == {"2025-12_to_cutoff"}
    assert (partial["horizon_months"] == 6).all()
    assert (
        horizons.loc[~horizons["partial_horizon"].astype(bool)][
            "horizon_months"
        ]
        == 12
    ).all()


def test_horizons_reconcile_with_the_static_coefficient() -> None:
    comparison = read_csv(MODELS / "long_run_horizon_reconciliation.csv")
    gap = comparison["static_minus_cell_weighted_average"].abs().max()
    assert gap < 1e-3, (
        "horizon estimates must partition the post period, so their "
        f"cell-weighted average must track the static coefficient; gap {gap}"
    )


def test_ddd_pretrends_restore_the_three_v1_columns() -> None:
    ddd = read_csv(DIAGNOSTICS / "ddd_pretrends.csv")

    assert len(ddd) == 100
    for column in (
        "ddd_pretrend_status",
        "group_pretrend_pretrend_status",
        "group_mde_80_power",
        "ddd_mde_80_power",
    ):
        assert column in ddd.columns
    assert not ddd["multiplicity_adjusted"].astype(bool).any()
    assert (ddd["interpretation"] == "diagnostic_only").all()


def test_honest_did_reports_both_restrictions() -> None:
    sensitivity = read_csv(DIAGNOSTICS / "honest_did_sensitivity.csv")
    summary = read_csv(DIAGNOSTICS / "honest_did_summary.csv")

    assert set(sensitivity["Delta"]) == {"DeltaRM", "DeltaSD"}
    assert set(summary["Delta"]) == {"DeltaRM", "DeltaSD"}
    # Both restrictions, both linear outcomes.
    assert len(summary) == 4
    assert set(summary["outcome"]) == {"asinh_saldo", "ln_salario_real_adm"}
    assert (
        summary["target"] == "average_post_event_time_0_to_23"
    ).all(), "the sensitivity target must be the event-study estimand"

    smoothness = sensitivity.loc[sensitivity["Delta"].eq("DeltaSD")]
    # These columns only exist for DeltaSD, so pandas reads them as object
    # with NaN on the DeltaRM rows. `astype(bool)` would turn those NaN into
    # True, so the comparison is explicit.
    open_below = smoothness["ci_open_below"] == True  # noqa: E712
    open_above = smoothness["ci_open_above"] == True  # noqa: E712
    uninformative = smoothness["interval_uninformative"] == True  # noqa: E712
    assert open_below.notna().all() and len(smoothness) > 0
    # An interval that reaches the search boundary on both sides is not a
    # bound and must be labelled as such rather than published as one.
    assert uninformative[open_below & open_above].all()
    # A one-sided open interval keeps a real bound on the closed side, so it
    # must have gone through the refinement stage.
    one_sided = (open_below ^ open_above)
    assert (
        smoothness.loc[one_sided, "grid_stage"]
        .str.startswith("refined")
        .all()
    )
    assert smoothness["grid_stage"].notna().all()


def test_deltarm_rows_survive_the_deltasd_append() -> None:
    """The smoothness node must not recompute or drop the released DeltaRM."""

    sensitivity = read_csv(DIAGNOSTICS / "honest_did_sensitivity.csv")
    relative = sensitivity.loc[sensitivity["Delta"].eq("DeltaRM")]
    counts = relative.groupby("outcome").size()
    assert set(counts.index) == {"asinh_saldo", "ln_salario_real_adm"}
    assert (counts == 41).all(), (
        "DeltaRM must keep its released 0-to-2 grid in steps of 0.05"
    )


def test_gate_report_does_not_recommend_a_principal_specification() -> None:
    support_path = DIAGNOSTICS / "pretrend_master_support.json"
    support = json.loads(support_path.read_text(encoding="utf-8"))
    assert support["recommends_principal_specification"] is False

    for source in (
        "pretrend_sample_2022.csv",
        "pretrend_power_check.csv",
        "pretrend_level2.csv",
    ):
        assert source in support["sources_present"]


def test_master_table_covers_every_diagnosed_specification() -> None:
    table = read_csv(DIAGNOSTICS / "pretrend_master_table.csv")
    expected = {
        "00_frozen_exact_model",
        "balanced_frozen_window",
        "extended_full_sample",
        "sample_2022_01",
        "04_include_minimal_as_control",
        "05_continuous_exposure",
        "level_2",
        "level_2_two_way",
        "wage_complete_coverage",
    }
    assert expected <= set(table["specification_id"])
    assert table["pretrend_status"].notna().all()


def test_non_psd_covariance_is_flagged_rather_than_hidden() -> None:
    level2 = read_csv(DIAGNOSTICS / "pretrend_level2.csv")
    assert "lead_covariance_positive_semidefinite" in level2.columns
    two_way = level2.loc[level2["specification_id"].eq("level_2_two_way")]
    assert len(two_way) == 5
    # Two-way clustering is not guaranteed positive semi-definite. Whether it
    # happens to be here or not, the column must exist and be populated.
    assert two_way["lead_covariance_positive_semidefinite"].notna().all()
