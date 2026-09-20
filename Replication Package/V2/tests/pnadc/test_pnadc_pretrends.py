from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from v2_pnadc.pnadc_pretrends import (  # noqa: E402
    OUTCOME_SPECS,
    SAMPLE_SPECS,
    attach_timing_readings,
    build_quarterly_event_formula,
    collapse_weighted_event_data,
    covariance_psd_diagnostic,
    derive_pretrend_timing,
    expected_coefficient_event_times,
    fit_collapsed_weighted_event_model,
    fit_quarterly_event_model,
    quarter_event_time,
    render_pretrend_report,
    run_model_diagnostics,
    validate_part1_gate,
    validate_pretrend_output,
)


def synthetic_quarterly_panel() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    rng = np.random.default_rng(20260730)
    event_times = (-4, -3, -2, -1, 1, 2)
    for cluster in range(12):
        treated = int(cluster < 6)
        for event_time in event_times:
            for person in range(3):
                rows.append(
                    {
                        "cod3": f"{cluster:03d}",
                        "trimestre_num": event_time + 44,
                        "event_time": event_time,
                        "treated": treated,
                        "peso": 1.0 + person,
                        "outcome": (
                            2.0
                            + 0.1 * cluster
                            + 0.05 * event_time
                            + 0.02 * treated * event_time
                            + rng.normal(scale=0.1)
                        ),
                    }
                )
    return pd.DataFrame(rows)


def test_quarterly_event_grid_uses_2022q3_as_reference() -> None:
    assert quarter_event_time(1) == -43
    assert quarter_event_time(43) == -1
    assert quarter_event_time(44) == 0
    assert quarter_event_time(45) == 1
    assert expected_coefficient_event_times(False) == [
        *range(-43, -1),
        *range(1, 14),
    ]
    assert expected_coefficient_event_times(True) == [
        *range(-43, -11),
        *range(-7, -1),
        *range(1, 14),
    ]


def test_quarterly_formula_has_unique_time_fixed_effect() -> None:
    assert build_quarterly_event_formula("informal") == (
        "informal ~ i(event_time, treated, ref=-1) "
        "| cod3 + trimestre_num"
    )


def test_covariance_psd_flag_is_not_assumed() -> None:
    positive = covariance_psd_diagnostic(np.eye(2))
    indefinite = covariance_psd_diagnostic(
        np.array([[1.0, 2.0], [2.0, 1.0]])
    )

    assert positive["lead_covariance_positive_semidefinite"] is True
    assert indefinite["lead_covariance_positive_semidefinite"] is False
    assert indefinite["lead_covariance_min_eigenvalue"] == pytest.approx(-1.0)


@pytest.mark.parametrize(
    ("full", "without_2020", "expected"),
    [
        ("fail", "fail", "structural_difference_persists_without_2020"),
        ("fail", "pass", "divergence_concentrated_around_2020"),
        ("pass", "fail", "diagnostic_unstable_to_2020_exclusion"),
        ("warning", "pass", "no_systematic_pretrend_detected_not_proof"),
    ],
)
def test_recent_structural_reading_is_mechanical(
    full: str,
    without_2020: str,
    expected: str,
) -> None:
    assert derive_pretrend_timing(full, without_2020) == expected


def test_weighted_quarterly_model_runs_all_three_diagnostics() -> None:
    data = synthetic_quarterly_panel()
    model, model_data, formula, clusters = fit_quarterly_event_model(
        data,
        outcome="outcome",
        estimator="ols",
        weight_column="peso",
        model_id="synthetic_weighted",
    )
    diagnostics = run_model_diagnostics(
        model,
        expected_event_times=[-4, -3, -2, 1, 2],
        lead_event_times=[-4, -3, -2],
        cluster_counts=clusters,
    )

    assert formula == build_quarterly_event_formula("outcome")
    assert len(model_data) == len(data)
    assert diagnostics["joint_lead_count"] == 3
    assert diagnostics["dynamic_pre_coefficients"] == 3
    assert diagnostics["pretrend_status"] in {"pass", "warning", "fail"}
    assert diagnostics["non_rejection_is_proof"] is False


def test_weighted_sufficient_statistics_match_row_level_vcov() -> None:
    data = synthetic_quarterly_panel()
    row_model, _, _, _ = fit_quarterly_event_model(
        data,
        outcome="outcome",
        estimator="ols",
        weight_column="peso",
        model_id="row_level",
    )
    collapsed, source_observations = collapse_weighted_event_data(
        data,
        outcome="outcome",
        weight_column="peso",
    )
    collapsed_model, _, _, _ = fit_collapsed_weighted_event_model(
        collapsed,
        outcome="outcome",
        source_observations=source_observations,
        model_id="collapsed_exact",
    )

    np.testing.assert_allclose(
        collapsed_model.coef().to_numpy(),
        row_model.coef().to_numpy(),
        rtol=0,
        atol=1e-10,
    )
    np.testing.assert_allclose(
        collapsed_model._vcov,
        row_model._vcov,
        rtol=0,
        atol=1e-10,
    )
    assert collapsed_model._N == len(data)


def test_p9_output_requires_six_outcomes_in_both_samples() -> None:
    rows = []
    for specification in OUTCOME_SPECS:
        for sample in SAMPLE_SPECS:
            rows.append(
                {
                    "outcome": specification["outcome"],
                    "sample": sample["sample"],
                    "pretrend_status": (
                        "fail"
                        if specification["outcome"] == "informal"
                        else "pass"
                    ),
                    "lead_covariance_positive_semidefinite": True,
                    "post_event_coefficients_published": False,
                    "non_rejection_is_proof": False,
                }
            )
    output = attach_timing_readings(pd.DataFrame(rows))
    validation = validate_pretrend_output(output)

    assert validation["rows"] == 12
    assert validation["outcomes"] == 6
    assert validation["samples"] == 2
    informal = output.loc[output["outcome"].eq("informal")]
    assert informal["pretrend_timing"].eq(
        "structural_difference_persists_without_2020"
    ).all()


def test_pretrend_report_states_identification_limits() -> None:
    rows = []
    for specification in OUTCOME_SPECS:
        for sample in SAMPLE_SPECS:
            rows.append(
                {
                    "outcome": specification["outcome"],
                    "sample": sample["sample"],
                    "pretrend_status": "pass",
                    "pretrend_timing": (
                        "no_systematic_pretrend_detected_not_proof"
                    ),
                    "joint_lead_p_value": 0.5,
                    "linear_pretrend_p_value": 0.5,
                    "dynamic_pre_p_lt_005": 0,
                    "lead_covariance_positive_semidefinite": True,
                }
            )
    report = render_pretrend_report(pd.DataFrame(rows))

    assert "not proof of parallel trends" in report
    assert "composition, not individual worker transitions" in report
    assert "2012Q1--2026Q1" in report
    assert "2022Q4 is excluded" in report
    assert "Section 5.1" in report


def test_part1_gate_is_bound_to_the_exact_analytical_panels(
    tmp_path: Path,
) -> None:
    individual = tmp_path / "individual.parquet"
    stock = tmp_path / "stock.parquet"
    individual.write_bytes(b"registered individual panel")
    stock.write_bytes(b"registered stock panel")

    import hashlib
    import json

    gate = tmp_path / "pnadc_part1_status.json"
    gate.write_text(
        json.dumps(
            {
                "gate": "P-B1",
                "gate_status": "open",
                "individual_panel": {
                    "sha256": hashlib.sha256(individual.read_bytes()).hexdigest()
                },
                "stock_panel": {
                    "sha256": hashlib.sha256(stock.read_bytes()).hexdigest()
                },
                "treatment_coefficients_computed": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert validate_part1_gate(gate, individual, stock)["gate_status"] == "open"

    stock.write_bytes(b"mutated stock panel")
    with pytest.raises(RuntimeError, match="stock panel hash"):
        validate_part1_gate(gate, individual, stock)
