from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "models" / "heterogeneity.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "heterogeneity",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load heterogeneity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ddd_contract_contains_triple_and_all_lower_terms() -> None:
    module = load_module()

    treatment, lower_terms = module.ddd_formula_contract()

    assert treatment == "post_treat_group"
    assert set(lower_terms) == {
        "post_treat",
        "post_group",
        "treat_group",
    }
    module.validate_ddd_formula_terms(
        [treatment, *lower_terms]
    )


def test_ddd_contract_rejects_missing_lower_term() -> None:
    module = load_module()

    try:
        module.validate_ddd_formula_terms(
            [
                "post_treat_group",
                "post_treat",
                "post_group",
            ]
        )
    except ValueError as error:
        assert "treat_group" in str(error)
    else:
        raise AssertionError("Incomplete DDD formula was accepted")


def test_cbo_level_lower_term_is_declared_but_absorbed() -> None:
    module = load_module()

    controls, absorbed = module.estimable_lower_terms(
        "cbo_predetermined"
    )

    assert controls == ("post_treat", "post_group")
    assert absorbed == ("treat_group",)
    module.validate_ddd_formula_terms(
        [
            module.DDD_TREATMENT_TERM,
            *controls,
            *absorbed,
        ]
    )


def test_bh_uses_frozen_planned_family_size() -> None:
    module = load_module()

    adjusted = module.benjamini_hochberg(
        np.array([0.001, 0.01, np.nan, 0.20]),
        family_size=10,
    )

    assert np.allclose(
        adjusted[[0, 1, 3]],
        [0.01, 0.05, 2 / 3],
    )
    assert np.isnan(adjusted[2])


def test_planned_family_has_100_contrasts() -> None:
    module = load_module()

    assert sum(
        len(spec["groups"])
        for spec in module.DIMENSIONS.values()
    ) == 20
    assert len(module.OUTCOMES) == 5
    assert module.PLANNED_FAMILY_SIZE == 100


def test_alternative_family_has_30_contrasts_without_changing_family_a() -> None:
    module = load_module()

    assert sum(
        len(spec["groups"])
        for spec in module.ALTERNATIVE_DIMENSIONS.values()
    ) == 6
    assert len(module.OUTCOMES) == 5
    assert module.ALTERNATIVE_FAMILY_SIZE == 30
    assert module.PLANNED_FAMILY_SIZE == 100


def test_alternative_partitions_use_pnad_ages_and_negra_aggregation(
    tmp_path: Path,
) -> None:
    module = load_module()
    source = pd.DataFrame(
        {
            "competenciamov": [202201] * 12,
            "cbo2002ocupacao": ["123456"] * 12,
            "saldomovimentacao": [1] * 12,
            "peso": [1] * 12,
            "salario": [1000.0] * 12,
            "idade": [
                17,
                18,
                24,
                25,
                34,
                35,
                44,
                45,
                54,
                55,
                65,
                66,
            ],
            "sexo": ["1"] * 12,
            "graudeinstrucao": ["7"] * 12,
            "racacor": [
                "1",
                "2",
                "3",
                "1",
                "2",
                "3",
                "1",
                "2",
                "3",
                "2",
                "3",
                "1",
            ],
        }
    )
    source.to_parquet(tmp_path / "movements.parquet", index=False)

    actual, _ = module.aggregate_signed_groups(
        tmp_path / "*.parquet",
        scratch_parent=tmp_path,
    )

    age_counts = (
        actual.loc[actual["dimension"].eq("age_pnad")]
        .set_index("actual_group")["admissoes"]
        .to_dict()
    )
    assert age_counts == {
        "age_18_24": 2,
        "age_25_34": 2,
        "age_35_44": 2,
        "age_45_54": 2,
        "age_55_65": 2,
    }
    negra = actual.loc[
        actual["dimension"].eq("race_aggregate")
        & actual["actual_group"].eq("race_negra"),
        "admissoes",
    ].sum()
    black_and_pardo = actual.loc[
        actual["dimension"].eq("race_color")
        & actual["actual_group"].isin(["race_black", "race_pardo"]),
        "admissoes",
    ].sum()
    assert negra == black_and_pardo
    module.validate_negra_admissions_reconciliation(actual)


def test_signed_group_aggregation_scans_only_requested_dimensions(
    tmp_path: Path,
) -> None:
    module = load_module()
    source = pd.DataFrame(
        {
            "competenciamov": [202201, 202201],
            "cbo2002ocupacao": ["123456", "123456"],
            "saldomovimentacao": [1, 1],
            "peso": [1, 1],
            "salario": [1000.0, 1100.0],
            "idade": [22, 35],
            "sexo": ["1", "3"],
            "graudeinstrucao": ["7", "9"],
            "racacor": ["2", "3"],
        }
    )
    source.to_parquet(tmp_path / "movements.parquet", index=False)

    actual, medians = module.aggregate_signed_groups(
        tmp_path / "*.parquet",
        scratch_parent=tmp_path,
        dimension_names=("age_pnad", "race_aggregate"),
        include_income=False,
    )

    assert set(actual["dimension"]) == {"age_pnad", "race_aggregate"}
    assert medians.empty


def test_signed_group_query_avoids_sixfold_microdata_expansion() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "CROSS JOIN LATERAL" not in source
    assert "_aggregate_signed_dimension" in source


def test_family_b_aggregation_includes_negra_validation_components() -> None:
    module = load_module()

    assert module.aggregation_dimensions(
        "B", module.ALTERNATIVE_DIMENSIONS
    ) == ("age_pnad", "race_aggregate", "race_color")
    assert module.aggregation_dimensions("A", module.DIMENSIONS) == (
        "sex",
        "age_canaries",
        "race_color",
        "education",
    )


def test_negra_reconciliation_fails_on_cell_mismatch() -> None:
    module = load_module()
    actual = pd.DataFrame(
        {
            "dimension": [
                "race_color",
                "race_color",
                "race_aggregate",
            ],
            "actual_group": [
                "race_black",
                "race_pardo",
                "race_negra",
            ],
            "cbo_4d": ["1234", "1234", "1234"],
            "periodo_num": [202201, 202201, 202201],
            "admissoes": [2, 3, 4],
        }
    )

    try:
        module.validate_negra_admissions_reconciliation(actual)
    except RuntimeError as error:
        assert "Negra admissions reconciliation failed" in str(error)
    else:
        raise AssertionError("A mismatched Negra cell was accepted")


def test_alternative_results_declare_family_b(
    monkeypatch,
) -> None:
    module = load_module()
    panel = pd.DataFrame(
        [
            {"dimension": dimension, "group_id": group_id}
            for dimension, specification in (
                module.ALTERNATIVE_DIMENSIONS.items()
            )
            for group_id, _ in specification["groups"]
        ]
    )

    def fake_fit_model(
        sample,
        *,
        model_id,
        outcome,
        treatment_term,
        estimator,
        fixed_effects,
        cluster_variables,
        controls,
        principal,
        separation_check,
    ):
        return (
            {
                "model_id": model_id,
                "outcome": outcome,
                "estimator": estimator,
                "term": treatment_term,
                "coefficient": 0.0,
                "standard_error": 1.0,
                "p_value": 0.5,
                "n_obs": len(sample),
                "cluster_counts": "1",
                "converged": True,
                "formula": "",
            },
            None,
        )

    monkeypatch.setattr(module, "fit_model", fake_fit_model)
    results = module.run_ddd_models(
        panel,
        dimensions=module.ALTERNATIVE_DIMENSIONS,
        family_id="B",
        family_size=module.ALTERNATIVE_FAMILY_SIZE,
    )

    assert len(results) == 30
    assert results["family_id"].eq("B").all()
    assert results["family_size"].eq(30).all()
    assert results["bh_adjusted_p_value"].notna().all()


def test_family_b_uses_separate_outputs() -> None:
    module = load_module()

    configuration = module.family_configuration("B")

    assert configuration["dimensions"] is module.ALTERNATIVE_DIMENSIONS
    assert configuration["family_size"] == 30
    assert configuration["panel"].name == (
        "painel_heterogeneity_ddd_alternative_partitions.parquet"
    )
    assert configuration["support"].name == (
        "ddd_alternative_partitions_support.csv"
    )
    assert configuration["results"].name == (
        "ddd_alternative_partitions.csv"
    )


def test_support_thresholds_are_encoded_in_source() -> None:
    module = load_module()

    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "treated >= 20 and control >= 50" in source
    assert "treated >= 10 and control >= 25" in source


def test_generated_family_is_complete_and_reports_both_p_values() -> None:
    results = pd.read_csv(
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "diagnostics"
        / "ddd_multiplicity_results.csv"
    )

    assert len(results) == 100
    assert results["result_status"].eq("estimated").all()
    assert results["nominal_p_value"].notna().all()
    assert results["bh_adjusted_p_value"].notna().all()
    assert {
        "post_treat_group",
        "post_treat",
        "post_group",
        "treat_group",
    } == set(
        __import__("json").loads(
            results["declared_ddd_terms"].iloc[0]
        )
    )
    assert set(results["support_status"]) <= {
        "adequate",
        "limited",
        "thin",
    }


def test_generated_alternative_family_is_complete_and_separate() -> None:
    diagnostics = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "diagnostics"
    )
    results = pd.read_csv(
        diagnostics / "ddd_alternative_partitions.csv"
    )
    support = pd.read_csv(
        diagnostics / "ddd_alternative_partitions_support.csv"
    )

    assert len(results) == 30
    assert results["result_status"].eq("estimated").all()
    assert results["family_id"].eq("B").all()
    assert results["family_size"].eq(30).all()
    assert results["bh_adjusted_p_value"].notna().all()
    assert results.groupby("dimension").size().to_dict() == {
        "age_pnad": 25,
        "race_aggregate": 5,
    }
    assert len(support) == 6
    assert support["family_id"].eq("B").all()
    assert support["family_size"].eq(30).all()


def test_alternative_report_explains_negra_component_contrasts() -> None:
    module = load_module()
    diagnostics = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "diagnostics"
    )
    results = pd.read_csv(
        diagnostics / "ddd_alternative_partitions.csv"
    )
    support = pd.read_csv(
        diagnostics / "ddd_alternative_partitions_support.csv"
    )
    report = module.render_report(results, support)

    assert "race_negra" in report
    assert "race_pardo" in report
    assert "race_black" in report
    assert "different target-versus-complement contrasts" in report
    assert "not an inconsistency" in report
