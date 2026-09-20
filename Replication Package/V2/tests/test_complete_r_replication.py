from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = PACKAGE_ROOT / "code" / "replication" / "r_validation.py"
    spec = importlib.util.spec_from_file_location("r_validation", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_caged_r_contract_covers_every_registered_model_family() -> None:
    contracts = load_module().build_caged_model_contracts()

    assert contracts["model_id"].is_unique
    assert {
        "national_static",
        "sector_static",
        "family_a_static",
        "family_b_static",
        "family_c_group_did",
        "national_event",
        "group_event",
        "canary_event",
        "national_pretrend",
        "sector_pretrend",
        "ddd_pretrend",
        "group_pretrend",
    } <= set(contracts["analysis_family"])
    assert len(contracts.loc[contracts["analysis_family"] == "family_a_static"]) == 100
    assert len(contracts.loc[contracts["analysis_family"] == "family_b_static"]) == 30
    assert len(contracts.loc[contracts["analysis_family"] == "family_c_group_did"]) == 130
    assert len(contracts.loc[contracts["analysis_family"] == "group_event"]) == 30
    assert len(contracts.loc[contracts["analysis_family"] == "ddd_pretrend"]) == 130
    assert len(contracts.loc[contracts["analysis_family"] == "group_pretrend"]) == 130
    assert contracts["expected_status"].value_counts().to_dict() == {
        "estimated": len(contracts),
    }
    diagnostic = contracts.loc[contracts["comparison_scope"].eq("diagnostic")]
    assert diagnostic["python_coefficient_source"].notna().all()
    assert diagnostic["python_coefficient_selector"].str.contains(
        '"model_id"',
        regex=False,
    ).all()


def test_r_engine_receives_only_analytical_inputs_and_model_contracts() -> None:
    script = (PACKAGE_ROOT / "R" / "complete_replication.R").read_text(
        encoding="utf-8"
    )

    assert "model_contracts.csv" in script
    assert "results/models" not in script
    assert "results/diagnostics" not in script
    assert "python_path <-" not in script
    assert "Python estimates" in script


def test_r_engine_uses_explicit_cross_language_numerical_tolerances() -> None:
    script = (PACKAGE_ROOT / "R" / "complete_replication.R").read_text(
        encoding="utf-8"
    )

    assert "fixef.tol = 1e-8" in script
    assert "fixef.iter = 100000" in script
    assert "glm.tol = 1e-9" in script
    assert 'contract$expected_status == "failed_estimation"' not in script


def test_public_design_records_the_rank_deficient_high_income_models() -> None:
    design = (PACKAGE_ROOT / "RESEARCH_DESIGN.md").read_text(encoding="utf-8")

    assert "All five outcome models are estimated" in design
    assert "rank 7 in a 22-lead covariance block" in design
    assert "separation-flow model has a registered Python" not in design


def test_r_engine_exports_honest_did_inputs_from_its_own_models() -> None:
    script = (PACKAGE_ROOT / "R" / "complete_replication.R").read_text(
        encoding="utf-8"
    )

    assert "honest_did_event_coefficients.csv" in script
    assert "honest_did_event_vcov_long.csv" in script
    assert "national_event::balanced::" in script


def test_honest_did_reads_only_the_independent_r_input_directory() -> None:
    for name in ("honest_did.R", "honest_did_sd.R"):
        script = (PACKAGE_ROOT / "R" / name).read_text(encoding="utf-8")
        assert 'argument_value("--input-dir")' in script
        assert 'file.path(input_dir, "honest_did_event_coefficients.csv")' in script
        assert 'file.path(input_dir, "honest_did_event_vcov_long.csv")' in script


def test_complete_r_precedes_honest_did_in_the_public_dag() -> None:
    import sys

    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.insert(0, str(PACKAGE_ROOT))
    import run_replication

    node_ids = [
        node.node_id
        for node in run_replication.build_dag(
            target="caged",
            mode="reproduce",
            raw_dir=run_replication.DEFAULT_RAW_DIR,
        )
    ]

    assert node_ids.index("complete_r_replication") < node_ids.index(
        "honest_did"
    )
    assert node_ids.index("compare_complete_r_replication") < node_ids.index(
        "honest_did"
    )


def test_cross_language_comparison_contract_is_strict() -> None:
    module = load_module()

    assert module.NUMERIC_TOLERANCE == 1e-6
    assert module.DIAGNOSTIC_P_VALUE_TOLERANCE == 2e-5
    assert module.DIAGNOSTIC_RELATIVE_TOLERANCE == 1e-3
    assert module.EXACT_FIELDS == (
        "n_obs",
        "minimum_clusters",
        "sample_id",
        "status",
        "reference_event_time",
    )


def test_honest_did_r_inputs_are_compared_before_sensitivity(
    tmp_path: Path,
) -> None:
    module = load_module()
    results = tmp_path / "results"
    diagnostics = results / "diagnostics"
    r_output = tmp_path / "r-output"
    diagnostics.mkdir(parents=True)
    r_output.mkdir()
    coefficients = pd.DataFrame(
        {
            "outcome": ["asinh_saldo", "asinh_saldo"],
            "estimator": ["ols", "ols"],
            "position": [0, 1],
            "event_time": [-2, 0],
            "coefficient": [0.1, 0.2],
            "is_pre": [True, False],
        }
    )
    covariance = pd.DataFrame(
        {
            "outcome": ["asinh_saldo"] * 4,
            "row_position": [0, 0, 1, 1],
            "column_position": [0, 1, 0, 1],
            "row_event_time": [-2, -2, 0, 0],
            "column_event_time": [-2, 0, -2, 0],
            "covariance": [0.04, 0.01, 0.01, 0.09],
        }
    )
    coefficients.to_csv(
        diagnostics / "honest_did_event_coefficients.csv", index=False
    )
    covariance.to_csv(
        diagnostics / "honest_did_event_vcov_long.csv", index=False
    )
    r_coefficients = coefficients.copy()
    r_coefficients.loc[0, "coefficient"] += 5e-7
    r_coefficients.to_csv(
        r_output / "honest_did_event_coefficients.csv", index=False
    )
    covariance.to_csv(
        r_output / "honest_did_event_vcov_long.csv", index=False
    )

    _, _, status = module._compare_honest_did_inputs(results, r_output)

    assert status["status"] == "pass"
    assert status["coefficient_rows"] == 2
    assert status["covariance_rows"] == 4
    assert status["maximum_coefficient_absolute_difference"] < 1e-6
