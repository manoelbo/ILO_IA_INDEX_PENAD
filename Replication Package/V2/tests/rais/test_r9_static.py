from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from v2_rais.r9_static import (
    BASE_RESULT_COLUMNS,
    FAMILY_RESULT_COLUMNS,
    MODEL_SPECS,
    attach_pretrends,
    failed_result,
    finalize_family_d,
    reconstruct_inference,
    render_static_report,
)


def _base_result(
    outcome: str,
    p_value: float,
    *,
    n_obs: int = 100,
    clusters: int = 50,
) -> dict[str, object]:
    row = {column: np.nan for column in BASE_RESULT_COLUMNS}
    row.update(
        {
            "model_id": f"rais_static__{outcome}",
            "outcome": outcome,
            "term": "post_treat",
            "estimator": "ols",
            "coefficient": 0.10,
            "standard_error": 0.05,
            "ci_low": 0.001,
            "ci_high": 0.199,
            "p_value": p_value,
            "cluster_df": clusters - 1,
            "cluster_counts": f'{{"cbo_4d": {clusters}}}',
            "minimum_clusters": clusters,
            "n_obs": n_obs,
            "input_cells": n_obs + 1,
            "complete_case_cells": n_obs + 1,
            "cells_dropped": 1,
            "cells_dropped_missing": 0,
            "cells_dropped_estimator": 1,
            "separation_dropped": 0,
            "converged": True,
            "formula": f"{outcome} ~ post_treat | cbo_4d + ano",
            "fixed_effects": "cbo_4d + ano",
            "cluster_variables": "cbo_4d",
            "controls": "",
            "effect_percent": np.nan,
            "result_status": "estimated",
            "error": "",
        }
    )
    return row


def test_base_schema_is_the_current_25_fit_model_keys_plus_status_and_error() -> None:
    assert len(BASE_RESULT_COLUMNS) == 27
    assert BASE_RESULT_COLUMNS[-2:] == ("result_status", "error")
    assert len(FAMILY_RESULT_COLUMNS) >= 6


def test_model_specs_preserve_the_gated_windows_and_estimators() -> None:
    assert [
        (
            spec["outcome"],
            spec["estimator"],
            spec["panel"],
            spec["sample_window"],
        )
        for spec in MODEL_SPECS
    ] == [
        ("estoque_3112", "ppml", "annual", "2019-2024"),
        (
            "ln_taxa_rotatividade",
            "ols",
            "rotation",
            "2021-2024",
        ),
        (
            "ln_tempo_emprego_medio",
            "ols",
            "annual",
            "2019-2024",
        ),
    ]


def test_failed_result_occupies_a_complete_family_slot() -> None:
    row = failed_result(
        MODEL_SPECS[0],
        input_cells=2041,
        error=RuntimeError("did not converge"),
    )

    assert tuple(row) == BASE_RESULT_COLUMNS
    assert row["result_status"] == "failed_estimation"
    assert row["error"] == "did not converge"
    assert np.isnan(row["p_value"])
    assert row["input_cells"] == 2041


def test_reconstruct_inference_uses_the_cluster_t_contract() -> None:
    row = _base_result("y", p_value=0.05, clusters=50)

    reconstructed = reconstruct_inference(row)

    assert reconstructed["cluster_df"] == 49
    assert reconstructed["ci_low"] < 0.10 < reconstructed["ci_high"]
    assert 0 < reconstructed["p_value"] < 1


def test_family_d_bh_keeps_size_three_when_one_model_fails() -> None:
    rows = pd.DataFrame(
        [
            _base_result("y1", 0.01),
            _base_result("y2", np.nan),
            _base_result("y3", 0.20),
        ]
    )

    result = finalize_family_d(rows)

    assert result["family_id"].eq("D").all()
    assert result["family_size"].eq(3).all()
    assert result["multiplicity_method"].eq("Benjamini-Hochberg").all()
    assert result["bh_adjusted_p_value"].iloc[0] == pytest.approx(0.03)
    assert np.isnan(result["bh_adjusted_p_value"].iloc[1])
    assert result["bh_adjusted_p_value"].iloc[2] == pytest.approx(0.30)


def test_attach_pretrends_suppresses_markers_when_pretrend_fails() -> None:
    results = finalize_family_d(
        pd.DataFrame(
            [
                _base_result("fail_outcome", 0.001, n_obs=100),
                _base_result("pass_outcome", 0.001, n_obs=100),
                _base_result("null_outcome", 0.80, n_obs=100),
            ]
        )
    )
    pretrends = pd.DataFrame(
        {
            "outcome": [
                "fail_outcome",
                "pass_outcome",
                "null_outcome",
            ],
            "pretrend_status": ["fail", "pass", "pass"],
            "n_obs": [100, 100, 100],
            "minimum_clusters": [50, 50, 50],
        }
    )

    attached = attach_pretrends(results, pretrends)

    assert attached.loc[
        attached["outcome"].eq("fail_outcome"),
        "significance_marker",
    ].item() == ""
    assert attached.loc[
        attached["outcome"].eq("pass_outcome"),
        "significance_marker",
    ].item() == "*"
    assert attached.loc[
        attached["outcome"].eq("null_outcome"),
        "significance_marker",
    ].item() == ""


def test_attach_pretrends_rejects_a_sample_mismatch() -> None:
    results = finalize_family_d(
        pd.DataFrame(
            [
                _base_result("y1", 0.10, n_obs=100),
                _base_result("y2", 0.20, n_obs=100),
                _base_result("y3", 0.30, n_obs=100),
            ]
        )
    )
    pretrends = pd.DataFrame(
        {
            "outcome": ["y1", "y2", "y3"],
            "pretrend_status": ["pass", "pass", "pass"],
            "n_obs": [99, 100, 100],
            "minimum_clusters": [50, 50, 50],
        }
    )

    with pytest.raises(RuntimeError, match="sample mismatch"):
        attach_pretrends(results, pretrends)


def test_static_report_states_windows_estimands_and_ppml_semielasticity() -> None:
    rows = pd.DataFrame(
        [
            {
                **_base_result("estoque_3112", 0.01, n_obs=100),
                "estimator": "ppml",
                "sample_window": "2019-2024",
                "nominal_p_value": 0.01,
                "bh_adjusted_p_value": 0.03,
                "pretrend_status": "fail",
                "significance_marker": "",
                "effect_percent": 10.517,
            },
            {
                **_base_result(
                    "ln_taxa_rotatividade",
                    0.20,
                    n_obs=100,
                ),
                "sample_window": "2021-2024",
                "nominal_p_value": 0.20,
                "bh_adjusted_p_value": 0.30,
                "pretrend_status": "pass",
                "significance_marker": "",
            },
        ]
    )

    report = render_static_report(rows)

    assert "2019–2024" in report
    assert "2021–2024" in report
    assert "post-2023 treated-control differential" in report
    assert "semi-elasticity" in report
    assert "100 × (exp(beta) - 1)" in report
    assert "not a log-log elasticity" in report
    assert "failed pretrend" in report
