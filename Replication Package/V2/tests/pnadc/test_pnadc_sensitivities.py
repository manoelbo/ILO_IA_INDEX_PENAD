from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from v2_pnadc.pnadc_sensitivities import (  # noqa: E402
    apply_cod3_treatment_to_arm_b,
    apply_cod3_treatment_to_arm_a,
    build_sensitivity_grid,
    classify_cod3_threshold,
    fit_collapsed_weighted_static_model,
    render_sensitivities_report,
    validate_sensitivity_results,
)
from v2_pnadc.weighted_estimator import fit_weighted_model  # noqa: E402


def synthetic_static_panel() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    rng = np.random.default_rng(20260730)
    for cluster in range(12):
        treated = int(cluster < 6)
        for quarter in range(8):
            post = int(quarter >= 4)
            for person in range(4):
                rows.append(
                    {
                        "cod3": f"{cluster:03d}",
                        "trimestre_num": quarter + 1,
                        "post_treat": treated * post,
                        "peso": 1.0 + person,
                        "outcome": (
                            1.0
                            + 0.1 * cluster
                            + 0.05 * quarter
                            + 0.4 * treated * post
                            + rng.normal(scale=0.1)
                        ),
                    }
                )
    return pd.DataFrame(rows)


def test_threshold_075_reclassifies_only_arm_b_cod3() -> None:
    treatment = pd.DataFrame(
        {
            "cod3": ["111", "222", "333"],
            "exposed_employment_share": [0.0, 0.6, 0.8],
        }
    )

    classified = classify_cod3_threshold(treatment, threshold=0.75)

    assert classified["treatment_status"].tolist() == [
        "control",
        "intermediate",
        "treated",
    ]
    assert classified["treated_cod3"].tolist()[:1] == [0.0]
    assert np.isnan(classified.loc[1, "treated_cod3"])
    assert classified.loc[2, "treated_cod3"] == 1.0


def test_arm_a_cod3_treatment_drops_intermediate_groups() -> None:
    individual = pd.DataFrame(
        {
            "cod3": ["111", "222", "333"],
            "post": [1, 1, 1],
            "treated": [1, 0, 1],
            "post_treat": [1, 0, 1],
        }
    )
    treatment = pd.DataFrame(
        {
            "cod3": ["111", "222", "333"],
            "treatment_status": ["control", "treated", "intermediate"],
            "treated_cod3": [0.0, 1.0, np.nan],
        }
    )

    result = apply_cod3_treatment_to_arm_a(individual, treatment)

    assert result["cod3"].tolist() == ["111", "222"]
    assert result["treated"].tolist() == [0, 1]
    assert result["post_treat"].tolist() == [0, 1]
    assert not {"cod4", "cod_ocupacao"} & set(result)


def test_arm_b_threshold_drops_new_intermediate_groups() -> None:
    stock = pd.DataFrame(
        {
            "cod3": ["111", "222", "333"],
            "post": [1, 1, 1],
            "treated": [0, 1, 1],
            "post_treat": [0, 1, 1],
            "treatment_status": ["control", "treated", "treated"],
        }
    )
    threshold = pd.DataFrame(
        {
            "cod3": ["111", "222", "333"],
            "treatment_status": ["control", "intermediate", "treated"],
            "treated_cod3": [0.0, np.nan, 1.0],
        }
    )

    result = apply_cod3_treatment_to_arm_b(stock, threshold)

    assert result["cod3"].tolist() == ["111", "333"]
    assert result["treated"].tolist() == [0, 1]
    assert result["post_treat"].tolist() == [0, 1]


def test_sensitivity_grid_contains_only_18_applicable_models() -> None:
    grid = build_sensitivity_grid()
    counts = (
        pd.DataFrame(grid)
        .groupby("sensitivity_id")["outcome"]
        .nunique()
        .to_dict()
    )

    assert len(grid) == 18
    assert counts == {
        "arm_a_cod3_treatment": 3,
        "cod3_threshold_075": 3,
        "transition_2022q4_as_pre": 6,
        "without_2020": 6,
    }
    assert all(not row["is_principal"] for row in grid)


def test_collapsed_static_fit_matches_individual_adapter_to_1e_10() -> None:
    data = synthetic_static_panel()
    row_result, row_model = fit_weighted_model(
        data,
        model_id="row_static",
        outcome="outcome",
        treatment_term="post_treat",
        estimator="ols",
        fixed_effects=("cod3", "trimestre_num"),
        cluster_variables=("cod3",),
        weight_column="peso",
        controls=(),
        principal=False,
    )
    collapsed_result, collapsed_model = (
        fit_collapsed_weighted_static_model(
            data,
            model_id="collapsed_static",
            outcome="outcome",
        )
    )

    assert abs(
        collapsed_result["coefficient"] - row_result["coefficient"]
    ) <= 1e-10
    assert abs(
        collapsed_result["standard_error"] - row_result["standard_error"]
    ) <= 1e-10
    np.testing.assert_allclose(
        collapsed_model._vcov,
        row_model._vcov,
        rtol=0,
        atol=1e-10,
    )
    assert collapsed_result["n_obs"] == len(data)


def test_sensitivity_report_preserves_the_frozen_hierarchy() -> None:
    frame = pd.DataFrame(build_sensitivity_grid())
    frame["coefficient"] = 0.0
    frame["standard_error"] = 1.0
    frame["p_value"] = 1.0
    frame["result_status"] = "estimated"
    report = render_sensitivities_report(frame)

    assert "hierarchy was frozen before estimation" in report
    assert "never promoted" in report
    assert "composition, not individual worker transitions" in report


def test_sensitivity_output_has_no_bh_or_principal_rows() -> None:
    frame = pd.DataFrame(build_sensitivity_grid())
    frame["result_status"] = "estimated"
    frame["family_id"] = "none"
    frame["bh_adjusted_p_value"] = np.nan
    frame["significance_symbol"] = ""
    frame["hierarchy_frozen_before_estimation"] = True

    validation = validate_sensitivity_results(frame)

    assert validation["rows"] == 18
    assert validation["estimated_rows"] == 18
    assert validation["principal_rows"] == 0
    assert validation["stars_published"] == 0
