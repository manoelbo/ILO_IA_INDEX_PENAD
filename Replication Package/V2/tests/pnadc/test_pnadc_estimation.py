from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from v2_pnadc.pnadc_estimation import (  # noqa: E402
    BASE_RESULT_COLUMNS,
    FAMILY_E_SIZE,
    OUTCOME_SPECS,
    apply_family_e,
    attach_pretrend_statuses,
    normalize_arm_b_result,
    render_results_report,
    validate_principal_results,
)


def shared_result_stub(outcome: str, p_value: float) -> dict:
    values = {
        column: np.nan
        for column in BASE_RESULT_COLUMNS
        if column not in {"weight_column", "sum_of_weights"}
    }
    values.update(
        {
            "model_id": f"model_{outcome}",
            "outcome": outcome,
            "term": "post_treat",
            "estimator": "ppml",
            "coefficient": 0.1,
            "standard_error": 0.05,
            "p_value": p_value,
            "n_obs": 100,
            "converged": True,
        }
    )
    return values


def principal_result_frame() -> pd.DataFrame:
    p_values = [0.001, 0.01, 0.02, 0.04, 0.06, 0.5]
    rows = []
    for specification, p_value in zip(
        OUTCOME_SPECS,
        p_values,
        strict=True,
    ):
        row = normalize_arm_b_result(
            shared_result_stub(
                str(specification["outcome"]),
                p_value,
            )
        )
        row.update(
            {
                "arm": specification["arm"],
                "result_status": "estimated",
                "pretrend_status_full": "fail",
                "pretrend_status_without_2020": "fail",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def test_arm_b_schema_aligns_to_the_27_column_local_contract() -> None:
    result = normalize_arm_b_result(
        shared_result_stub("ocupados_total", 0.1)
    )

    assert tuple(result) == BASE_RESULT_COLUMNS
    assert len(result) == 27
    assert result["weight_column"] == ""
    assert np.isnan(result["sum_of_weights"])


def test_family_e_is_six_tests_and_failed_pretrends_have_no_stars() -> None:
    adjusted = apply_family_e(principal_result_frame())

    assert len(adjusted) == FAMILY_E_SIZE == 6
    assert adjusted["family_id"].eq("E").all()
    assert adjusted["family_size"].eq(6).all()
    assert adjusted["significance_symbol"].eq("").all()
    assert adjusted["stars_suppressed_by_pretrend"].all()
    assert adjusted.loc[
        adjusted["outcome"].eq("ln_renda"),
        "is_reconciliation",
    ].item()
    assert not adjusted.loc[
        adjusted["outcome"].eq("ln_renda"),
        "is_principal",
    ].item()


def test_principal_grid_contains_each_registered_outcome_once() -> None:
    adjusted = apply_family_e(principal_result_frame())
    validation = validate_principal_results(adjusted)

    assert validation["rows"] == 6
    assert validation["family_id"] == "E"
    assert validation["family_size"] == 6
    assert validation["stars_published"] == 0


def test_each_result_receives_both_exact_sample_pretrends() -> None:
    results = principal_result_frame().drop(
        columns=[
            "pretrend_status_full",
            "pretrend_status_without_2020",
        ]
    )
    pretrends = pd.DataFrame(
        [
            {
                "outcome": specification["outcome"],
                "sample": sample,
                "pretrend_status": "fail",
            }
            for specification in OUTCOME_SPECS
            for sample in ("full", "without_2020")
        ]
    )
    attached = attach_pretrend_statuses(results, pretrends)

    assert attached["pretrend_status_full"].eq("fail").all()
    assert attached["pretrend_status_without_2020"].eq("fail").all()
    assert len(attached) == 6


def test_results_report_states_estimand_and_design_limits() -> None:
    adjusted = apply_family_e(principal_result_frame())
    report = render_results_report(adjusted)

    assert "2012Q1--2026Q1" in report
    assert "2022Q4 is excluded" in report
    assert "composition, not individual worker transitions" in report
    assert "automation_index_cai" in report
    assert "72%" in report
    assert "does not implement the full complex survey design" in report
