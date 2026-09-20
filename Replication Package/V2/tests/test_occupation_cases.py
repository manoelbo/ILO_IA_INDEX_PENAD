from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "panel" / "occupation_cases.py"
DICTIONARY_PATH = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "occupation_cases"
    / "occupation_case_dictionary.csv"
)


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "occupation_cases",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load occupation_cases.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_dictionary_hash_and_composition() -> None:
    module = load_module()

    dictionary = module.load_frozen_dictionary(DICTIONARY_PATH)
    primary = dictionary.loc[dictionary["primary_included"]]

    assert module.DICTIONARY_SHA256 == (
        "b8d0310606c37ed32decf4cb46a9088632f9c1409c837d869a2c33d4ac8aa4b2"
    )
    assert len(dictionary) == 80
    assert len(primary) == 76
    assert not primary["cbo_6d"].duplicated().any()
    assert primary.groupby("case_id").size().to_dict() == {
        "customer_service": 2,
        "health_care_aides": 7,
        "marketing_sales_managers": 2,
        "production_supervisors": 53,
        "software_developers": 7,
        "stock_clerks": 5,
    }


def test_canaries_age_groups_preserve_boundaries() -> None:
    module = load_module()
    ages = pd.Series(
        [21, 22, 25, 26, 30, 31, 34, 35, 40, 41, 49, 50, 90]
    )

    observed = module.assign_age_group(ages).tolist()

    assert pd.isna(observed[0])
    assert observed[1:] == [
        "age_22_25",
        "age_22_25",
        "age_26_30",
        "age_26_30",
        "age_31_34",
        "age_31_34",
        "age_35_40",
        "age_35_40",
        "age_41_49",
        "age_41_49",
        "age_50_plus",
        "age_50_plus",
    ]


def test_temporal_contract_uses_november_and_terminal_twelve_months() -> None:
    module = load_module()

    assert module.BASELINE_PERIOD == 202211
    assert module.TERMINAL_START == 202506
    assert module.TERMINAL_END == 202605
    assert len(
        module.month_range(
            module.TERMINAL_START,
            module.TERMINAL_END,
        )
    ) == 12


def test_signed_case_panel_is_complete_and_uses_cbo_year_winsorization(
    tmp_path: Path,
) -> None:
    module = load_module()
    movements = pd.DataFrame(
        {
            "competenciamov": [
                202211,
                202211,
                202211,
                202211,
                202211,
                202211,
                202212,
            ],
            "cbo2002ocupacao": ["123456"] * 7,
            "saldomovimentacao": [1, 1, 1, 1, 1, -1, 1],
            "peso": [1, 1, -1, 1, 1, 1, 1],
            "salario": [
                1000.0,
                1000.0,
                1000.0,
                2000.0,
                900.0,
                1000.0,
                1200.0,
            ],
            "idade": [22, 22, 22, 50, 21, 22, 26],
        }
    )
    movements.to_parquet(
        tmp_path / "movements.parquet",
        index=False,
    )
    dictionary = pd.DataFrame(
        {
            "case_id": ["example_case"],
            "case_label_pt": ["Caso de exemplo"],
            "cbo_6d": ["123456"],
        }
    )

    cells, bounds = module.aggregate_case_cells(
        tmp_path / "*.parquet",
        dictionary,
        scratch_parent=tmp_path,
        start_period=202211,
        end_period=202212,
    )
    ipca = pd.DataFrame(
        {"periodo_num": [202211, 202212], "indice": [100.0, 100.0]}
    )
    panel = module.complete_case_panel(
        cells,
        dictionary,
        ipca,
        start_period=202211,
        end_period=202212,
    )
    coverage = module.build_monthly_coverage(
        panel,
        expected_months=2,
    )

    assert len(bounds) == 1
    assert bounds.loc[0, "cbo_6d"] == "123456"
    assert bounds.loc[0, "year"] == 2022
    assert len(panel) == 12
    assert not panel.duplicated(
        ["case_id", "age_group", "periodo_num"]
    ).any()
    age_22_november = panel.loc[
        panel["case_id"].eq("example_case")
        & panel["age_group"].eq("age_22_25")
        & panel["periodo_num"].eq(202211)
    ].iloc[0]
    assert age_22_november["admissions"] == 1
    assert age_22_november["wage_count"] == 1
    assert age_22_november["real_admission_wage"] == 1000.0
    age_50_november = panel.loc[
        panel["age_group"].eq("age_50_plus")
        & panel["periodo_num"].eq(202211)
    ].iloc[0]
    assert age_50_november["admissions"] == 1
    assert len(coverage) == 6
    age_22_coverage = coverage.loc[
        coverage["age_group"].eq("age_22_25")
    ].iloc[0]
    assert age_22_coverage["expected_months"] == 2
    assert age_22_coverage["months_with_admissions"] == 1
    assert age_22_coverage["months_with_wage"] == 1


def test_preperiod_diagnostics_are_descriptive_without_counterfactual() -> None:
    module = load_module()
    panel = pd.DataFrame(
        {
            "case_id": ["example_case"] * 3,
            "case_label_pt": ["Caso de exemplo"] * 3,
            "age_group": ["age_22_25"] * 3,
            "periodo_num": [202209, 202210, 202211],
            "admissions": [10, 12, 14],
            "wage_count": [9, 11, 13],
            "real_admission_wage": [1000.0, 1010.0, 1020.0],
        }
    )

    diagnostics = module.build_preperiod_diagnostics(
        panel,
        pre_start=202209,
        pre_end=202211,
    )
    report = module.render_preperiod_report(diagnostics)

    assert len(diagnostics) == 2
    assert diagnostics["is_causal_test"].eq(False).all()
    assert diagnostics["has_counterfactual"].eq(False).all()
    assert "p_value" not in diagnostics.columns
    assert {
        "monthly_linear_slope",
        "annualized_log_slope_pct",
        "coefficient_of_variation",
    } <= set(diagnostics.columns)
    assert "no case-specific control group" in report
    assert "not a parallel-trends test" in report


def test_default_outputs_stay_inside_v2() -> None:
    module = load_module()

    assert module.DEFAULT_PANEL == (
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "painel_casos_ocupacionais.parquet"
    )
    for path in (
        module.DEFAULT_COVERAGE,
        module.DEFAULT_COVERAGE_REPORT,
        module.DEFAULT_DIAGNOSTICS,
        module.DEFAULT_DIAGNOSTICS_REPORT,
        module.DEFAULT_WAGE_BOUNDS,
    ):
        assert path.is_relative_to(PACKAGE_ROOT)
        assert "Replication Package/V1" not in str(path)
    assert module.portable_path(
        module.DEFAULT_DICTIONARY,
        relative_to=PACKAGE_ROOT,
    ) == "data/derived/occupation_cases/occupation_case_dictionary.csv"


def test_case_code_reconciliation_rejects_missing_cbo() -> None:
    module = load_module()
    primary = pd.DataFrame(
        {
            "case_id": ["case_a", "case_b"],
            "cbo_6d": ["111111", "222222"],
        }
    )
    bounds = pd.DataFrame(
        {
            "cbo_6d": ["111111"],
            "year": [2022],
        }
    )

    try:
        module.validate_case_code_reconciliation(primary, bounds)
    except RuntimeError as error:
        assert "missing frozen CBO6 codes" in str(error)
        assert "222222" in str(error)
    else:
        raise AssertionError("Missing occupation-case CBO6 was accepted")


def test_generated_case_panel_and_diagnostics_close_part_one() -> None:
    module = load_module()
    panel = pd.read_parquet(
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "painel_casos_ocupacionais.parquet"
    )
    mechanisms = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "mechanisms"
    )
    coverage = pd.read_csv(
        mechanisms / "occupation_case_monthly_coverage.csv"
    )
    diagnostics = pd.read_csv(
        mechanisms / "occupation_case_preperiod_diagnostics.csv"
    )
    summary = json.loads(
        (
            mechanisms / "occupation_case_panel_support.json"
        ).read_text(encoding="utf-8")
    )
    diagnostic_report = module.render_preperiod_report(diagnostics)

    assert len(panel) == 6 * 6 * 65
    assert panel["case_id"].nunique() == 6
    assert panel["age_group"].nunique() == 6
    assert panel["periodo_num"].nunique() == 65
    assert not panel.duplicated(
        ["case_id", "age_group", "periodo_num"]
    ).any()
    assert len(coverage) == 36
    assert coverage["panel_months"].eq(65).all()
    assert len(diagnostics) == 72
    assert diagnostics["is_causal_test"].eq(False).all()
    assert diagnostics["has_counterfactual"].eq(False).all()
    assert "p_value" not in diagnostics.columns
    assert summary["primary_cbo6_codes"] == 76
    assert summary["codes_with_wage_bounds"] == 76
    assert summary["dictionary_sha256"] == (
        "b8d0310606c37ed32decf4cb46a9088632f9c1409c837d869a2c33d4ac8aa4b2"
    )
    assert "no case-specific control group" in diagnostic_report
    assert "not a parallel-trends test" in diagnostic_report
