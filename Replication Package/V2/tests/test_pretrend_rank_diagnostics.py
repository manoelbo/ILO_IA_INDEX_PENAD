from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODELS_ROOT = PACKAGE_ROOT / "code" / "caged" / "models"
COMMON_ROOT = PACKAGE_ROOT / "code" / "common"
for directory in (MODELS_ROOT, COMMON_ROOT):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from pretrend_engine import (  # noqa: E402
    diagnose_event_model,
    registered_event_coefficient_frame,
)


class RankDeficientEventModel:
    def __init__(self) -> None:
        names = [
            "C(event_time, contr.treatment(base=-1))[T.-3]:treated_main",
            "C(event_time, contr.treatment(base=-1))[T.-2]:treated_main",
            "C(event_time, contr.treatment(base=-1))[T.0]:treated_main",
        ]
        self._coefficients = pd.Series([0.1, 0.2, 0.0], index=names)
        self._standard_errors = pd.Series([0.1, 0.1, 0.1], index=names)
        self._vcov = np.array(
            [
                [0.01, 0.01, 0.0],
                [0.01, 0.01, 0.0],
                [0.0, 0.0, 0.01],
            ]
        )
        self._N = 300

    def coef(self) -> pd.Series:
        return self._coefficients

    def se(self) -> pd.Series:
        return self._standard_errors

    def wald_test(self, **_: object) -> dict[str, float]:
        raise AssertionError("A singular lead covariance must not be inverted")


def test_rank_deficient_lead_covariance_is_not_classified() -> None:
    result = diagnose_event_model(
        RankDeficientEventModel(),
        interaction="treated_main",
        cluster_counts={"cbo_4d": 100},
        lead_minimum=-3,
        expected_event_times=[-3, -2, 0],
    )

    assert result["lead_covariance_dimension"] == 2
    assert result["lead_covariance_rank"] == 1
    assert result["lead_covariance_full_rank"] is False
    assert np.isinf(result["lead_covariance_condition_number"])
    assert np.isnan(result["joint_lead_statistic"])
    assert np.isnan(result["joint_lead_p_value"])
    assert np.isnan(result["linear_pretrend_coefficient"])
    assert result["pretrend_status"] == "not_interpretable_rank_deficient"
    assert result["dynamic_pre_coefficients"] == 2


def test_registered_event_coefficients_include_the_reference_cell() -> None:
    frame = registered_event_coefficient_frame(
        RankDeficientEventModel(),
        "treated_main",
        model_id="registered::model",
        outcome="outcome",
        estimator="ols",
        sample_id="frozen_sample",
        cluster_counts={"cbo_4d": 100},
        expected_event_times=[-3, -2, 0],
    )

    assert frame["event_time"].tolist() == [-3, -2, -1, 0]
    reference = frame.loc[frame["event_time"].eq(-1)].iloc[0]
    assert reference["coefficient"] == 0
    assert reference["standard_error"] == 0
    assert bool(reference["is_reference"]) is True
    assert frame["model_id"].eq("registered::model").all()
    assert frame["n_obs"].eq(300).all()
    assert frame["minimum_clusters"].eq(100).all()
