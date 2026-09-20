from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from v2_rais.r10_sensitivities import (
    DOMAIN_DIAGNOSTIC_QUERY,
    SENSITIVITY_IDS,
    build_sensitivity_grid,
    expected_lead_years,
    not_estimable_pretrend,
    render_sensitivity_report,
    validate_domain_diagnostic,
)


def _domain_diagnostic() -> pd.DataFrame:
    unresolved_start = [
        255483,
        259003,
        283484,
        291431,
        282785,
        357848,
        313180,
        299298,
        407201,
    ]
    unresolved_end = [0, 0, 0, 169047, 121647, 9569, 11290, 4824, 0]
    return pd.DataFrame(
        {
            "ano": list(range(2016, 2025)),
            "start_month_unresolved": unresolved_start,
            "inactive_end_month_unresolved": unresolved_end,
        }
    )


def test_domain_query_is_diagnostic_only_and_contains_no_treatment() -> None:
    assert "mes_admissao" in DOMAIN_DIAGNOSTIC_QUERY
    assert "mes_desligamento" in DOMAIN_DIAGNOSTIC_QUERY
    assert "tempo_emprego" in DOMAIN_DIAGNOSTIC_QUERY
    assert "post_treat" not in DOMAIN_DIAGNOSTIC_QUERY


def test_domain_diagnostic_reproduces_the_nonexecution_counts() -> None:
    diagnostic, support = validate_domain_diagnostic(_domain_diagnostic())

    assert len(diagnostic) == 9
    assert support["start_month_unresolved"] == 2_749_713
    assert support["inactive_end_month_unresolved"] == 316_377
    assert (
        support["annual_average_stock_status"]
        == "not_executable_source_fields_incomplete"
    )
    assert support["treatment_coefficient_estimated"] is False


def test_sensitivity_grid_retains_twelve_positions_and_three_unestimated_rows() -> None:
    grid = build_sensitivity_grid()

    assert len(grid) == 12
    assert set(grid["sensitivity_id"]) == set(SENSITIVITY_IDS)
    assert grid["is_principal"].eq(False).all()
    assert grid["result_status"].eq("not_applicable").sum() == 2
    annual_average = grid[
        grid["sensitivity_id"].eq("annual_average_stock")
    ]
    assert annual_average.loc[
        annual_average["outcome"].eq("estoque_3112"),
        "result_status",
    ].item() == "not_executable_source_fields_incomplete"
    assert annual_average.loc[
        ~annual_average["outcome"].eq("estoque_3112"),
        "result_status",
    ].eq("not_applicable").all()


def test_noop_sensitivities_are_flagged_instead_of_hidden() -> None:
    grid = build_sensitivity_grid()

    short_window = grid[
        grid["sensitivity_id"].eq("window_2019_2024")
    ]
    rotation_excluding_2020 = grid[
        grid["sensitivity_id"].eq("exclude_2020")
        & grid["outcome"].eq("ln_taxa_rotatividade")
    ]
    assert short_window["identical_to_principal"].all()
    assert rotation_excluding_2020["identical_to_principal"].item()


def test_excluding_2022_uses_2021_and_reports_zero_leads() -> None:
    assert expected_lead_years(
        [2021, 2023, 2024],
        reference_year=2021,
    ) == []

    diagnostic = not_estimable_pretrend(
        reference_year=2021,
        reason="no_pre_reference_coefficients",
    )

    assert diagnostic["pretrend_status"] == "not_estimable"
    assert diagnostic["pretrend_reference_year"] == 2021
    assert diagnostic["joint_lead_count"] == 0
    assert np.isnan(diagnostic["joint_lead_p_value"])


def test_report_freezes_hierarchy_and_keeps_sensitivities_outside_family_d() -> None:
    grid = build_sensitivity_grid()
    grid["coefficient"] = np.nan
    grid["standard_error"] = np.nan
    grid["nominal_p_value"] = np.nan
    grid["pretrend_status"] = np.where(
        grid["result_status"].eq("not_applicable"),
        "not_applicable",
        "pass",
    )

    report = render_sensitivity_report(grid)

    assert "never replace the principal specification" in report
    assert "frozen before estimation" in report
    assert "outside family D" in report
    assert "not_executable_source_fields_incomplete" in report
    assert "No remuneration proxy" in report
    assert "not_applicable" in report
