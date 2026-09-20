from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from v2_rais.r8_pretrends import (
    annual_gls_pretrend_slope,
    build_annual_formula,
    covariance_psd_diagnostic,
    diagnose_annual_model,
    expected_event_times,
    pretrend_comparison_reading,
    prepare_annual_event_data,
    render_pretrend_report,
)


class FakeEventModel:
    def __init__(
        self,
        event_times: list[int],
        coefficients: list[float],
        standard_errors: list[float],
        covariance: np.ndarray,
        *,
        joint_p_value: float,
        n_obs: int = 500,
    ) -> None:
        names = [
            (
                "C(event_time, contr.treatment(base=0))"
                f"[T.{event_time}]:treated_main"
            )
            for event_time in event_times
        ]
        self._coefficients = pd.Series(coefficients, index=names)
        self._standard_errors = pd.Series(standard_errors, index=names)
        self._vcov = covariance
        self._joint_p_value = joint_p_value
        self._N = n_obs
        self._data = pd.DataFrame(
            {
                "cbo_4d": [
                    f"{1000 + position:04d}" for position in range(100)
                ]
            }
        )

    def coef(self) -> pd.Series:
        return self._coefficients

    def se(self) -> pd.Series:
        return self._standard_errors

    def wald_test(
        self,
        *,
        R: np.ndarray,
        q: np.ndarray,
        distribution: str,
    ) -> dict[str, float]:
        assert distribution == "chi2"
        assert R.shape[0] == len(q)
        return {
            "statistic": 1.25,
            "pvalue": self._joint_p_value,
        }


def test_prepare_annual_event_data_uses_2022_as_the_omitted_reference() -> None:
    panel = pd.DataFrame(
        {
            "cbo_4d": ["1111"] * 6,
            "ano": [2019, 2020, 2021, 2022, 2023, 2024],
            "treated_main": [1.0] * 6,
            "estoque_3112": [10, 11, 12, 13, 14, 15],
        }
    )

    data = prepare_annual_event_data(
        panel,
        outcome="estoque_3112",
        start_year=2019,
        end_year=2024,
    )

    assert data["event_time"].tolist() == [-3, -2, -1, 0, 1, 2]
    assert expected_event_times(2019, 2024) == [-3, -2, -1, 1, 2]
    assert build_annual_formula("estoque_3112") == (
        "estoque_3112 ~ i(event_time, treated_main, ref=0) | "
        "cbo_4d + ano"
    )


def test_prepare_annual_event_data_rejects_a_hole_in_the_year_grid() -> None:
    panel = pd.DataFrame(
        {
            "cbo_4d": ["1111"] * 5,
            "ano": [2019, 2020, 2022, 2023, 2024],
            "treated_main": [1.0] * 5,
            "estoque_3112": [10, 11, 13, 14, 15],
        }
    )

    with pytest.raises(RuntimeError, match="missing years"):
        prepare_annual_event_data(
            panel,
            outcome="estoque_3112",
            start_year=2019,
            end_year=2024,
        )


def test_annual_gls_adapter_recovers_a_slope_through_reference_zero() -> None:
    annual_event_times = np.array([-3, -2, -1], dtype=float)
    coefficients = 0.02 * annual_event_times
    covariance = np.diag([0.04, 0.03, 0.02])

    result = annual_gls_pretrend_slope(
        coefficients,
        covariance,
        annual_event_times,
        {"cbo_4d": 100},
    )

    assert result["coefficient"] == pytest.approx(0.02)
    assert result["annual_reference_event_time"] == 0
    assert result["shared_function_reference_event_time"] == -1
    assert result["coordinate_shift"] == -1


def test_covariance_psd_diagnostic_preserves_an_indefinite_flag() -> None:
    result = covariance_psd_diagnostic(
        np.array([[1.0, 2.0], [2.0, 1.0]])
    )

    assert result["lead_covariance_min_eigenvalue"] == pytest.approx(-1.0)
    assert result["lead_covariance_positive_semidefinite"] is False


def test_diagnose_annual_model_runs_all_three_frozen_diagnostics() -> None:
    event_times = [-3, -2, -1, 1, 2]
    model = FakeEventModel(
        event_times,
        coefficients=[0.0] * 5,
        standard_errors=[0.1] * 5,
        covariance=np.eye(5) * 0.01,
        joint_p_value=0.25,
    )

    result = diagnose_annual_model(
        model,
        expected_times=event_times,
        lead_times=[-3, -2, -1],
        cluster_counts={"cbo_4d": 100},
    )

    assert result["joint_lead_count"] == 3
    assert result["joint_lead_p_value"] == pytest.approx(0.25)
    assert result["linear_pretrend_p_value"] == pytest.approx(1.0)
    assert result["dynamic_pre_p_lt_005"] == 0
    assert result["pretrend_status"] == "pass"
    assert result["reference_event_time"] == 0
    assert result["non_rejection_is_proof"] is False
    assert "post_event_coefficients" not in result


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("pass", "seasonality_attenuation_compatible_not_proven"),
        ("warning", "annual_diagnostic_inconclusive"),
        ("fail", "structural_difference_persists_after_aggregation"),
    ],
)
def test_pretrend_comparison_reading_is_fixed_before_results(
    status: str,
    expected: str,
) -> None:
    assert pretrend_comparison_reading(status) == expected


def test_report_compares_annual_and_monthly_diagnostics_without_claiming_proof() -> None:
    diagnostics = pd.DataFrame(
        {
            "outcome": [
                "estoque_3112",
                "ln_taxa_rotatividade",
                "ln_tempo_emprego_medio",
            ],
            "sample_window": ["2019-2024", "2021-2024", "2019-2024"],
            "joint_lead_window": ["-3_to_-1", "-1_to_-1", "-3_to_-1"],
            "joint_lead_p_value": [0.20, 0.08, 0.01],
            "linear_pretrend_p_value": [0.30, 0.20, 0.02],
            "dynamic_pre_p_lt_005": [0, 0, 2],
            "lead_covariance_positive_semidefinite": [True, True, True],
            "pretrend_status": ["pass", "warning", "fail"],
            "section_5_1_reading": [
                "seasonality_attenuation_compatible_not_proven",
                "annual_diagnostic_inconclusive",
                "structural_difference_persists_after_aggregation",
            ],
            "n_obs": [2041, 1360, 2041],
            "minimum_clusters": [341, 341, 341],
        }
    )
    monthly = pd.DataFrame(
        {
            "outcome": ["admissoes", "desligamentos"],
            "pretrend_status": ["fail", "fail"],
        }
    )

    report = render_pretrend_report(diagnostics, monthly)

    assert "2 of 2 monthly CAGED diagnostics are `fail`" in report
    assert "Section 5.1 line 519" in report
    assert (
        "A non-significant pretrend diagnostic is not proof of parallel "
        "trends."
    ) in report
    assert "different outcomes" in report
