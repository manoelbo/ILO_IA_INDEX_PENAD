from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PACKAGE_ROOT / "code" / "caged" / "models"
RESULTS_DIR = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "caged"
)


def load_module(filename: str, module_name: str):
    module_path = MODELS_DIR / filename
    sys.path.insert(0, str(module_path.parent))
    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_family_b_pretrend_configuration_uses_separate_outputs() -> None:
    module = load_module("ddd_pretrends.py", "ddd_pretrends_phase8b")

    configuration = module.diagnostic_configuration("B")

    assert configuration["family_id"] == "B"
    assert configuration["family_size"] == 30
    assert sum(
        len(specification["groups"])
        for specification in configuration["dimensions"].values()
    ) == 6
    assert configuration["panel"].name == (
        "painel_heterogeneity_ddd_alternative_partitions.parquet"
    )
    assert configuration["ddd_results"].name == (
        "ddd_alternative_partitions.csv"
    )
    assert configuration["output"].name == (
        "ddd_alternative_partitions_pretrends.csv"
    )


def test_alternative_age_comparison_places_both_partitions_together() -> None:
    module = load_module("ddd_pretrends.py", "ddd_pretrends_age_comparison")
    outcomes = [
        "admissoes",
        "desligamentos",
        "fluxo_bruto",
        "saldo",
        "salario_real_admissao",
    ]

    def rows(dimension: str, group_id: str, offset: float):
        return [
            {
                "dimension": dimension,
                "group_id": group_id,
                "outcome": outcome,
                "ddd_coefficient": offset + index,
                "ddd_bh_adjusted_p_value": 0.10 + index / 100,
                "group_pretrend_pretrend_status": "fail",
                "ddd_pretrend_status": "warning",
                "group_mde_80_power": 0.25 + index / 100,
            }
            for index, outcome in enumerate(outcomes)
        ]

    alternative = pd.DataFrame(rows("age_pnad", "age_18_24", 1.0))
    frozen = pd.DataFrame(rows("age_canaries", "age_22_25", 2.0))

    report = module.render_alternative_age_comparison(
        alternative,
        frozen,
    )

    assert "age_18_24" in report
    assert "age_22_25" in report
    assert "PNAD/IBGE 18–24" in report
    assert "Canaries 22–25" in report
    for outcome in outcomes:
        assert outcome in report


def test_group_did_family_c_uses_one_bh_pass_and_preserves_frozen_values() -> None:
    module = load_module("group_did_results.py", "group_did_results_phase8b")
    outcomes = [f"outcome_{index}" for index in range(5)]

    def diagnostic_rows(
        dimensions: list[tuple[str, int]],
        offset: int,
    ) -> pd.DataFrame:
        rows = []
        position = offset
        for dimension, group_count in dimensions:
            for group_index in range(group_count):
                group_id = f"{dimension}_{group_index}"
                for outcome in outcomes:
                    rows.append(
                        {
                            "dimension": dimension,
                            "dimension_kind": "micro",
                            "group_id": group_id,
                            "group_label": group_id,
                            "outcome": outcome,
                            "estimator": "ols",
                            "group_did_status": "estimated",
                            "group_did_error": "",
                            "group_did_coefficient": position / 7,
                            "group_did_standard_error": 0.1,
                            "group_did_p_value": (position + 1) / 1000,
                            "group_did_n_obs": 1000 + position,
                            "group_did_clusters": 50,
                            "group_mde_80_power": 0.28,
                            "group_pretrend_pretrend_status": "fail",
                            "group_pretrend_joint_lead_p_value": 0.001,
                            "ddd_pretrend_status": "warning",
                        }
                    )
                    position += 1
        return pd.DataFrame(rows)

    def supports(dimensions: list[tuple[str, int]]) -> pd.DataFrame:
        rows = []
        for dimension, group_count in dimensions:
            for group_index in range(group_count):
                group_id = f"{dimension}_{group_index}"
                rows.append(
                    {
                        "dimension": dimension,
                        "group_id": group_id,
                        "support_status": "adequate",
                        "target_treated_cbo_with_flows": 20,
                        "target_control_cbo_with_flows": 30,
                    }
                )
        return pd.DataFrame(rows)

    frozen_dimensions = [("frozen", 20)]
    alternative_dimensions = [("alternative", 6)]
    frozen = diagnostic_rows(frozen_dimensions, 0)
    alternative = diagnostic_rows(alternative_dimensions, 100)

    result = module.build_group_did_results(
        frozen,
        alternative,
        supports(frozen_dimensions),
        supports(alternative_dimensions),
    )

    assert len(result) == 130
    assert result["family_id"].eq("C").all()
    assert result["family_size"].eq(130).all()
    assert result["multiplicity_method"].eq("Benjamini-Hochberg").all()
    assert np.array_equal(
        result.iloc[:100]["coefficient"].to_numpy(),
        frozen["group_did_coefficient"].to_numpy(),
    )
    expected = module.benjamini_hochberg(
        np.concatenate(
            [
                frozen["group_did_p_value"].to_numpy(),
                alternative["group_did_p_value"].to_numpy(),
            ]
        ),
        family_size=130,
    )
    assert np.array_equal(
        result["bh_adjusted_p_value"].to_numpy(),
        expected,
    )
    assert result["interpretation"].eq("reportable").all()

    report = module.render_report(result)
    assert "DDD" in report
    assert "Family A" in report
    assert "Family C" in report
    assert "not comparable" in report


def test_part2_group_did_and_alternative_pretrend_artifacts() -> None:
    module = load_module(
        "group_did_results.py",
        "group_did_results_artifacts_phase8b",
    )
    diagnostics = RESULTS_DIR / "diagnostics"
    models = RESULTS_DIR / "models"
    frozen = pd.read_csv(diagnostics / "ddd_pretrends.csv")
    alternative = pd.read_csv(
        diagnostics / "ddd_alternative_partitions_pretrends.csv"
    )
    family_c = pd.read_csv(models / "group_did_results.csv")

    assert len(alternative) == 30
    assert alternative["family_id"].eq("B").all()
    assert alternative["family_size"].eq(30).all()
    for column in (
        "group_pretrend_pretrend_status",
        "ddd_pretrend_status",
        "group_mde_80_power",
    ):
        assert alternative[column].notna().all()

    assert len(family_c) == 130
    assert family_c["family_id"].eq("C").all()
    assert family_c["family_size"].eq(130).all()
    assert np.array_equal(
        family_c.iloc[:100]["coefficient"].to_numpy(),
        frozen["group_did_coefficient"].to_numpy(),
    )
    expected_bh = module.benjamini_hochberg(
        family_c["nominal_p_value"].to_numpy(),
        family_size=130,
    )
    assert np.allclose(
        family_c["bh_adjusted_p_value"].to_numpy(),
        expected_bh,
        rtol=0,
        atol=1e-15,
    )
    pretrend_module = load_module(
        "ddd_pretrends.py",
        "ddd_pretrends_public_report_contract",
    )
    comparison = pretrend_module.render_alternative_age_comparison(
        alternative,
        frozen,
    )
    assert "PNAD/IBGE 18–24" in comparison
    assert "Canaries 22–25" in comparison
    family_b_support = json.loads(
        (
            diagnostics / "ddd_alternative_partitions_support.json"
        ).read_text(encoding="utf-8")
    )
    assert family_b_support["negra_reconciliation_cells"] == 22049
    assert family_b_support["negra_reconciliation_basis"] == (
        "complete main-sample CBO-month grid"
    )


def test_group_event_study_contract_has_main_partitions_and_full_grid() -> None:
    module = load_module(
        "group_event_studies.py",
        "group_event_studies_contract_phase8b",
    )

    assert sum(
        len(specification["groups"])
        for specification in module.DIMENSIONS.values()
    ) == 15
    assert module.DIMENSIONS["race"]["groups"] == (
        ("race_white", "White"),
        ("race_negra", "Black or Pardo"),
    )
    assert tuple(
        group_id
        for group_id, _ in module.DIMENSIONS["age"]["groups"]
    ) == (
        "age_18_24",
        "age_25_34",
        "age_35_44",
        "age_45_54",
        "age_55_65",
    )
    assert module.OUTCOMES == (
        ("admissoes", "ppml"),
        ("ln_salario_real_adm", "ols"),
    )
    assert module.expected_estimated_event_times() == [
        value for value in range(-23, 42) if value != -1
    ]

    parameters = pd.DataFrame(
        {
            "term": [
                f"event_time::{event_time}"
                for event_time in module.expected_estimated_event_times()
            ],
            "event_time": module.expected_estimated_event_times(),
            "coefficient": np.arange(64, dtype=float),
            "standard_error": np.repeat(0.25, 64),
        }
    )
    complete = module.complete_coefficient_grid(
        parameters,
        minimum_clusters=50,
    )

    assert complete["event_time"].tolist() == list(range(-23, 42))
    reference = complete.loc[complete["event_time"].eq(-1)]
    assert len(reference) == 1
    assert bool(reference.iloc[0]["is_reference"])
    assert reference.iloc[0]["coefficient"] == 0
    assert complete.loc[
        complete["event_time"].gt(23),
        "beyond_frozen_window",
    ].all()
    assert not complete.loc[
        complete["event_time"].le(23),
        "beyond_frozen_window",
    ].any()
    expected_pre_mean = parameters.loc[
        parameters["event_time"].between(-23, -2),
        "coefficient",
    ].mean()
    assert complete["pre_coefficient_mean"].nunique() == 1
    assert complete["pre_coefficient_mean"].iloc[0] == expected_pre_mean


def test_occupation_case_trajectories_use_november_base_and_terminal_mean() -> None:
    module = load_module(
        "occupation_case_trajectories.py",
        "occupation_case_trajectories_phase8b",
    )
    terminal_periods = [
        202506,
        202507,
        202508,
        202509,
        202510,
        202511,
        202512,
        202601,
        202602,
        202603,
        202604,
        202605,
    ]
    periods = [202211, *terminal_periods]
    panel = pd.DataFrame(
        {
            "case_id": ["example"] * len(periods),
            "case_label_pt": ["Exemplo"] * len(periods),
            "age_group": ["age_22_25"] * len(periods),
            "periodo_num": periods,
            "period": [str(period) for period in periods],
            "admissions": [10, *([20] * 12)],
            "real_admission_wage": [1000, *([1100] * 12)],
            "dictionary_sha256": ["signed"] * len(periods),
        }
    )

    trajectories = module.build_trajectories(panel)
    terminal = module.build_terminal_summary(trajectories)
    report = module.render_report(trajectories, terminal)

    base = trajectories.loc[trajectories["periodo_num"].eq(202211)]
    assert base["normalized_value"].eq(1).all()
    admissions = terminal.loc[terminal["outcome"].eq("admissions")].iloc[0]
    wage = terminal.loc[
        terminal["outcome"].eq("real_admission_wage")
    ].iloc[0]
    assert admissions["terminal_mean_index"] == 2
    assert admissions["terminal_change_from_base_pct"] == 100
    assert wage["terminal_mean_index"] == 1.1
    assert wage["terminal_change_from_base_pct"] == 10
    assert terminal["terminal_observed_months"].eq(12).all()

    serialized_contract = " ".join(
        [*map(str.lower, trajectories.columns), report.lower()]
    )
    for forbidden in (
        r"\bp[_-]?value\b",
        r"\bstars?\b",
        r"\bcausal\b",
        r"\bsignificant\b",
    ):
        assert re.search(forbidden, serialized_contract) is None


def test_part2_event_study_and_trajectory_artifacts_are_complete() -> None:
    models = RESULTS_DIR / "models"
    mechanisms = RESULTS_DIR / "mechanisms"
    coefficients = pd.read_csv(
        models / "group_event_study_coefficients.csv"
    )
    pre_means = pd.read_csv(
        models / "group_event_study_pre_means.csv"
    )
    model_status = pd.read_csv(
        models / "group_event_study_models.csv"
    )

    assert len(coefficients) == 1950
    assert len(pre_means) == 30
    assert len(model_status) == 30
    assert model_status["status"].eq("estimated").all()
    assert model_status["converged"].all()
    for _, model_frame in coefficients.groupby(
        "model_id",
        sort=False,
    ):
        assert model_frame["event_time"].tolist() == list(range(-23, 42))
        assert model_frame["is_reference"].sum() == 1
        assert model_frame.loc[
            model_frame["event_time"].eq(-1),
            "coefficient",
        ].iloc[0] == 0
        assert model_frame.loc[
            model_frame["event_time"].gt(23),
            "beyond_frozen_window",
        ].all()
        assert not model_frame.loc[
            model_frame["event_time"].le(23),
            "beyond_frozen_window",
        ].any()
        observed_pre_mean = model_frame.loc[
            model_frame["event_time"].between(-23, -2),
            "coefficient",
        ].mean()
        assert np.isclose(
            model_frame["pre_coefficient_mean"].iloc[0],
            observed_pre_mean,
            rtol=0,
            atol=1e-15,
        )

    trajectories_path = (
        mechanisms / "occupation_case_trajectories.csv"
    )
    terminal_path = (
        mechanisms / "occupation_case_terminal_summary.csv"
    )
    trajectories = pd.read_csv(trajectories_path)
    terminal = pd.read_csv(terminal_path)
    assert len(trajectories) == 4680
    assert len(terminal) == 72
    assert trajectories.loc[
        trajectories["periodo_num"].eq(202211),
        "normalized_value",
    ].eq(1).all()
    assert terminal["terminal_observed_months"].eq(12).all()
    trajectory_module = load_module(
        "occupation_case_trajectories.py",
        "occupation_case_trajectories_public_contract",
    )
    report = trajectory_module.render_report(trajectories, terminal)
    serialized = " ".join(
        [
            trajectories_path.read_text(encoding="utf-8").lower(),
            terminal_path.read_text(encoding="utf-8").lower(),
            report.lower(),
        ]
    )
    for forbidden in (
        r"\bp[_-]?value\b",
        r"\bstars?\b",
        r"\bcausal\b",
        r"\bsignificant\b",
    ):
        assert re.search(forbidden, serialized) is None
