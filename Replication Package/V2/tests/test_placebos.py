from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "models" / "placebos.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "placebos",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load placebos.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_placebo_contract_is_frozen() -> None:
    module = load_module()

    assert module.TRUE_PRE_START == 202101
    assert module.FALSE_EVENT_PERIOD == 202112
    assert module.TRUE_PRE_END == 202211
    assert module.GROUP_PLACEBO_REPETITIONS == 500
    assert module.GROUP_PLACEBO_SEED == 20260726
    assert len(module.OUTCOMES) == 5


def test_temporal_placebo_uses_only_true_pre_and_false_event() -> None:
    module = load_module()
    panel = pd.DataFrame(
        {
            "cbo_4d": ["1111"] * 5,
            "periodo_num": [
                202012,
                202101,
                202111,
                202112,
                202212,
            ],
            "included_main": [True] * 5,
            "treated_main": [1] * 5,
            "periodo": ["2020-12", "2021-01", "2021-11", "2021-12", "2022-12"],
            "post": [0, 0, 0, 0, 1],
            "admissoes": [1] * 5,
            "desligamentos": [1] * 5,
            "n_movimentacoes": [2] * 5,
            "ln_salario_real_adm": [1.0] * 5,
            "asinh_saldo": [0.0] * 5,
        }
    )

    result = module.prepare_temporal_placebo(panel)

    assert result["periodo_num"].tolist() == [
        202101,
        202111,
        202112,
    ]
    assert result["post_placebo"].tolist() == [0, 0, 1]
    assert result["placebo_time_treat"].tolist() == [0, 0, 1]


def test_temporal_gate_fails_if_any_outcome_is_significant() -> None:
    module = load_module()
    results = pd.DataFrame(
        {
            "outcome": [outcome for outcome, _ in module.OUTCOMES],
            "p_value": [0.20, 0.049, 0.30, 0.80, 0.11],
        }
    )

    gate = module.evaluate_temporal_gate(results)

    assert gate["status"] == "fail"
    assert gate["may_proceed_to_group_placebo"] is False
    assert gate["significant_outcomes"] == ["desligamentos"]


def test_temporal_gate_passes_only_when_all_outcomes_are_nonsignificant() -> None:
    module = load_module()
    results = pd.DataFrame(
        {
            "outcome": [outcome for outcome, _ in module.OUTCOMES],
            "p_value": [0.20, 0.05, 0.30, 0.80, 0.11],
        }
    )

    gate = module.evaluate_temporal_gate(results)

    assert gate["status"] == "pass"
    assert gate["may_proceed_to_group_placebo"] is True
    assert gate["significant_outcomes"] == []


def test_random_assignments_are_seeded_and_preserve_treated_count() -> None:
    module = load_module()
    cbos = [f"{value:04d}" for value in range(10)]

    first = module.random_treatment_assignments(
        cbos,
        treated_count=3,
        repetitions=4,
        seed=123,
    )
    second = module.random_treatment_assignments(
        cbos,
        treated_count=3,
        repetitions=4,
        seed=123,
    )

    assert np.array_equal(first, second)
    assert first.shape == (4, 10)
    assert np.all(first.sum(axis=1) == 3)


def test_randomization_summary_reports_percentile_and_two_sided_p() -> None:
    module = load_module()

    result = module.summarize_randomization_distribution(
        observed_coefficient=1.5,
        placebo_coefficients=np.array([-2.0, -1.0, 0.0, 1.0, 2.0]),
    )

    assert result["observed_percentile"] == 80.0
    assert result["empirical_two_sided_p_value"] == 0.5
    assert result["repetitions"] == 5


def test_exported_group_inputs_preserve_every_assignment(tmp_path: Path) -> None:
    module = load_module()
    cbos = ["1111", "2222", "3333", "4444"]
    panel = pd.DataFrame(
        [
            {
                "cbo_4d": cbo,
                "periodo_num": period,
                "periodo": str(period),
                "post": int(period >= 202301),
                "included_main": True,
                "treated_main": int(cbo == "1111"),
                "admissoes": 1,
                "desligamentos": 1,
                "n_movimentacoes": 2,
                "ln_salario_real_adm": 1.0,
                "asinh_saldo": 0.0,
            }
            for cbo in cbos
            for period in (202211, 202301)
        ]
    )
    panel_path = tmp_path / "panel.csv"
    assignments_path = tmp_path / "assignments.csv"

    support = module.export_group_placebo_inputs(
        panel,
        panel_path=panel_path,
        assignments_path=assignments_path,
        repetitions=3,
        seed=123,
    )

    exported_panel = pd.read_csv(panel_path, dtype={"cbo_4d": str})
    assignments = pd.read_csv(
        assignments_path,
        dtype={"cbo_4d": str},
    )
    assert len(exported_panel) == 8
    assert len(assignments) == 12
    assert assignments.groupby("repetition")["assigned"].sum().eq(1).all()
    assert support["treated_cbo_count"] == 1
    assert support["control_cbo_count"] == 3


def test_two_way_residualization_is_orthogonal_to_both_fixed_effects() -> None:
    module = load_module()
    values = np.array([1.0, 2.0, 4.0, 8.0])
    row_codes = np.array([0, 0, 1, 1])
    column_codes = np.array([0, 1, 0, 1])

    residual = module.two_way_residualize(
        values,
        row_codes,
        column_codes,
    )

    for codes in (row_codes, column_codes):
        sums = np.bincount(codes, weights=residual)
        assert np.allclose(sums, 0.0, atol=1e-12)


def test_lightweight_ppml_matches_closed_form_two_by_two_did() -> None:
    module = load_module()
    outcome = np.array(
        [
            [10.0, 20.0],
            [10.0, 40.0],
        ]
    )
    mask = np.ones_like(outcome, dtype=bool)

    coefficient = module.ppml_two_way_coefficient(
        outcome,
        mask,
        treatment=np.array([0, 1]),
        post=np.array([0, 1]),
    )

    assert np.isclose(coefficient, np.log(2.0), atol=1e-10)


def test_generated_placebo_family_is_complete_and_passes_gate() -> None:
    diagnostics = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "diagnostics"
    )
    temporal = pd.read_csv(
        diagnostics / "temporal_placebo_results.csv"
    )
    gate = json.loads(
        (diagnostics / "temporal_placebo_gate.json").read_text()
    )
    distribution = pd.read_csv(
        diagnostics / "group_placebo_distribution.csv"
    )
    summary = pd.read_csv(
        diagnostics / "group_placebo_summary.csv"
    )
    status = json.loads(
        (diagnostics / "group_placebo_status.json").read_text()
    )
    assert len(temporal) == 5
    assert temporal["p_value"].ge(0.05).all()
    assert gate["status"] == "pass"
    assert len(distribution) == 2_500
    assert distribution["repetition"].nunique() == 500
    assert distribution["outcome"].nunique() == 5
    assert distribution["treated_cbo_count"].eq(75).all()
    assert len(summary) == 5
    assert status["status"] == "completed"
    assert status["model_count"] == 2_500
    assert status["backend"] == "ppml_ipf_and_ols_fwl"

    module = load_module()
    panel = pd.read_parquet(
        PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
    )
    ladder = pd.read_csv(
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "models"
        / "specification_ladder.csv"
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        lightweight, _, _ = module.run_group_placebo(
            panel,
            ladder,
            repetitions=1,
            seed=module.GROUP_PLACEBO_SEED,
        )
        reference, _, _ = module.run_group_placebo_reference(
            panel,
            ladder,
            repetitions=1,
            seed=module.GROUP_PLACEBO_SEED,
        )
    comparison = reference[["outcome", "estimator", "coefficient"]].merge(
        lightweight[["outcome", "estimator", "coefficient"]],
        on=["outcome", "estimator"],
        suffixes=("_reference", "_lightweight"),
        validate="one_to_one",
    )
    difference = (
        comparison["coefficient_reference"]
        - comparison["coefficient_lightweight"]
    ).abs()
    assert difference.max() < 1e-8
