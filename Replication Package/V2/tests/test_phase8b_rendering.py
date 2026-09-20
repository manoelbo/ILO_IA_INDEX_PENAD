from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = PACKAGE_ROOT / "code" / "render"
MODELS_DIR = PACKAGE_ROOT / "code" / "caged" / "models"
RESULTS_DIR = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "caged"
)


def load_module(directory: Path, filename: str, module_name: str):
    module_path = directory / filename
    sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mandatory_note_reconciles_within_group_and_ddd_wage_results() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_common.py",
        "phase8b_common_note",
    )
    family_c = pd.read_csv(
        RESULTS_DIR / "models" / "group_did_results.csv"
    )
    family_a = pd.read_csv(
        RESULTS_DIR / "diagnostics" / "ddd_multiplicity_results.csv"
    )
    national = pd.read_csv(
        RESULTS_DIR / "models" / "specification_ladder.csv"
    )

    counts = module.interpretation_counts(
        family_c,
        family_a,
        national,
    )
    note = module.mandatory_interpretation_note(counts)

    assert counts["family_c_wage_groups"] == 26
    assert counts["family_c_negative_wage_bh"] == 22
    assert counts["family_a_wage_bh"] == 2
    assert np.isclose(counts["national_wage_coefficient"], -0.050740)
    assert "não medem heterogeneidade" in note
    assert "22 dos 26 grupos" in note
    assert "2 dos 100 contrastes salariais" in note


def test_main_group_tables_use_bh_stars_and_preserve_pretrend_failures() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_tables.py",
        "phase8b_tables_main",
    )
    family_c = pd.read_csv(
        RESULTS_DIR / "models" / "group_did_results.csv"
    )
    diagnostics = pd.read_csv(
        RESULTS_DIR / "diagnostics" / "ddd_pretrends.csv"
    )

    sex = module.build_main_group_table(
        family_c,
        diagnostics,
        dimension="sex",
        groups=("men", "women"),
    )
    income = module.build_main_group_table(
        family_c,
        diagnostics,
        dimension="income",
        groups=("low_income", "middle_income", "high_income"),
    )

    assert len(sex) == 8
    assert sex["family_id"].eq("C").all()
    assert sex["family_size"].eq(130).all()
    assert sex["star_source"].eq("bh_adjusted_p_value").all()
    assert sex["group_pretrend"].notna().all()
    assert sex["group_pretrend"].ne("").all()
    expected_stars = [
        module.significance_stars(value)
        for value in sex["bh_adjusted_p_value"]
    ]
    assert sex["stars"].tolist() == expected_stars

    high_separations = income.loc[
        income["group_id"].eq("high_income")
        & income["outcome"].eq("desligamentos")
    ].iloc[0]
    assert (
        high_separations["group_pretrend"]
        == "not_interpretable_rank_deficient"
    )
    source_diagnostic = diagnostics.loc[
        diagnostics["dimension"].eq("income")
        & diagnostics["group_id"].eq("high_income")
        & diagnostics["outcome"].eq("desligamentos")
    ].iloc[0]
    assert not bool(source_diagnostic["group_pretrend_lead_covariance_full_rank"])
    assert (
        source_diagnostic["group_pretrend_lead_covariance_rank"]
        < source_diagnostic["group_pretrend_lead_covariance_dimension"]
    )
    assert high_separations["support_status"] == "thin"


def test_appendix_tables_have_nine_columns_and_visible_age_families() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_tables.py",
        "phase8b_tables_appendix",
    )
    family_a = pd.read_csv(
        RESULTS_DIR / "diagnostics" / "ddd_pretrends.csv"
    )
    family_b = pd.read_csv(
        RESULTS_DIR
        / "diagnostics"
        / "ddd_alternative_partitions_pretrends.csv"
    )

    age = module.build_appendix_age_table(family_a, family_b)

    assert len(age.columns) == 9
    assert len(age) == 55
    assert age.iloc[:, 0].str.contains("Família A \\(100\\)").any()
    assert age.iloc[:, 0].str.contains("Família B \\(30\\)").any()
    assert not age.columns.str.contains("Painel B.2", regex=False).any()


def test_national_appendix_keeps_wage_pretrend_fail_and_stock_warning() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_tables.py",
        "phase8b_tables_national_appendix",
    )
    ladder = pd.read_csv(
        RESULTS_DIR / "models" / "specification_ladder.csv"
    )
    diagnostics = pd.read_csv(
        RESULTS_DIR / "diagnostics" / "pretrend_diagnostics.csv"
    )
    stock = pd.read_csv(
        RESULTS_DIR / "mechanisms" / "stock_proxy_result.csv"
    )

    table = module.build_national_appendix(
        ladder,
        diagnostics,
        stock,
    )
    wage = table.loc[
        table["outcome_id"].eq("ln_salario_real_adm")
    ].iloc[0]
    proxy = table.loc[table["panel"].eq("B.2")].iloc[0]

    assert wage["pretrend_status"] == "fail"
    assert np.isclose(wage["pretrend_p_value"], 1.580098e-04)
    assert "not employment stock" in proxy["interpretation"]


def test_render_registry_contains_the_33_caged_manuscript_artifacts() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_render.py",
        "phase8b_render_registry",
    )

    registry = module.artifact_registry()
    tables = [row for row in registry if row["artifact_type"] == "table"]
    figures = [row for row in registry if row["artifact_type"] == "figure"]

    assert len(registry) == 33
    assert len(tables) == 18
    assert len(figures) == 15
    assert any(
        row["artifact_id"] == "Tabela 5.1.1"
        and row["csv_path"].endswith(
            "table_5_1_1_sector_control.csv"
        )
        for row in tables
    )
    assert any(
        row["artifact_id"] == "Tabela C.1"
        and row["csv_path"].endswith("table_c_1_occupation_cases.csv")
        for row in tables
    )
    assert {
        row["artifact_id"]
        for row in figures
        if row["artifact_id"].startswith("Figura C.")
    } == {"Figura C.1", "Figura C.2"}
    assert all(row["csv_path"].endswith(".csv") for row in tables)
    assert all(row["md_path"].endswith(".md") for row in tables)
    assert all(row["png_path"].endswith(".png") for row in figures)
    assert any(
        row["artifact_id"] == "Figura 5.2.6"
        and row["png_path"].endswith(
            "figure_5_2_6_group_outcome_forest.png"
        )
        for row in figures
    )
    assert not any(row["artifact_id"].startswith(("B.", "Figure B.")) for row in registry)


def test_figure_5_2_6_reuses_the_single_family_c_bh_adjustment() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_tables.py",
        "phase8b_forest_backing_contract",
    )
    source = pd.DataFrame(
        {
            "dimension": ["dimension"] * 130,
            "group_id": [f"group_{index // 5}" for index in range(130)],
            "group_label": [f"Group {index // 5}" for index in range(130)],
            "outcome": [f"outcome_{index % 5}" for index in range(130)],
            "coefficient": np.linspace(-0.2, 0.2, 130),
            "standard_error": np.repeat(0.05, 130),
            "nominal_p_value": np.linspace(0.001, 0.9, 130),
            "bh_adjusted_p_value": np.linspace(0.01, 0.99, 130),
            "bh_significant_005": [index < 40 for index in range(130)],
            "cluster_df": np.repeat(340.0, 130),
            "support_status": np.repeat("adequate", 130),
            "target_treated_cbo_with_flows": np.repeat(75, 130),
            "target_control_cbo_with_flows": np.repeat(266, 130),
            "family_id": np.repeat("C", 130),
            "family_size": np.repeat(130, 130),
            "multiplicity_method": np.repeat("Benjamini-Hochberg", 130),
        }
    )

    forest = module.build_group_outcome_forest_table(source)

    assert len(forest) == 130
    assert forest["family_id"].eq("C").all()
    assert forest["family_size"].eq(130).all()
    assert np.array_equal(
        forest["bh_adjusted_p_value"].to_numpy(),
        source["bh_adjusted_p_value"].to_numpy(),
    )
    assert np.array_equal(
        forest["bh_significant_005"].to_numpy(),
        source["bh_significant_005"].to_numpy(),
    )
    expected_alpha = (
        0.05 * int(source["bh_significant_005"].sum()) / len(source)
    )
    assert forest["bh_discovery_alpha"].eq(expected_alpha).all()


def test_extended_national_event_study_has_four_outcomes_and_full_grid() -> None:
    module = load_module(
        MODELS_DIR,
        "national_event_study_extended.py",
        "national_event_study_extended_contract",
    )

    assert module.OUTCOMES == (
        ("admissoes", "ppml"),
        ("desligamentos", "ppml"),
        ("ln_salario_real_adm", "ols"),
        ("asinh_saldo", "ols"),
    )
    assert module.expected_estimated_event_times() == [
        value for value in range(-23, 42) if value != -1
    ]
    parameters = pd.DataFrame(
        {
            "term": [
                f"event_time::{value}"
                for value in module.expected_estimated_event_times()
            ],
            "event_time": module.expected_estimated_event_times(),
            "coefficient": np.linspace(-0.2, 0.2, 64),
            "standard_error": np.repeat(0.05, 64),
        }
    )

    complete = module.complete_coefficient_grid(
        parameters,
        minimum_clusters=341,
    )

    assert complete["event_time"].tolist() == list(range(-23, 42))
    assert complete["is_reference"].sum() == 1
    assert complete.loc[
        complete["event_time"].eq(-1),
        "coefficient",
    ].iloc[0] == 0
    assert complete["beyond_frozen_window"].eq(
        complete["event_time"].gt(23)
    ).all()
    assert complete["pre_coefficient_mean"].nunique() == 1


def test_sector_control_table_uses_frozen_co_principal_results() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_tables.py",
        "phase8b_tables_sector_control",
    )
    models = RESULTS_DIR / "models"
    diagnostics = RESULTS_DIR / "diagnostics"

    table = module.build_sector_control_table(
        pd.read_csv(models / "specification_ladder.csv"),
        pd.read_csv(models / "sector_fixed_effect_ladder.csv"),
        pd.read_csv(models / "sector_level1_vs_level2.csv"),
        pd.read_csv(diagnostics / "pretrend_diagnostics.csv"),
        pd.read_csv(diagnostics / "pretrend_level2.csv"),
    )

    assert len(table) == 5
    assert table["outcome"].tolist() == list(module.OUTCOME_ORDER)
    assert table["level_1_role"].eq("principal").all()
    assert table["level_2_role"].eq("co_principal_sector").all()
    assert table["level_1_pretrend_status"].eq("fail").all()
    assert table["level_2_pretrend_status"].eq("fail").all()
    assert table["two_way_pretrend_status"].eq("fail").all()
    assert table["two_way_minimum_clusters"].eq(87).all()
    assert set(
        table.loc[
            ~table["two_way_lead_covariance_positive_semidefinite"],
            "outcome",
        ]
    ) == {
        "admissoes",
        "desligamentos",
        "n_movimentacoes",
    }
    assert table.loc[
        ~table["two_way_lead_covariance_positive_semidefinite"],
        "two_way_pretrend_interpretation",
    ].eq("not_interpretable_non_psd_lead_covariance").all()

    admissions = table.loc[table["outcome"].eq("admissoes")].iloc[0]
    assert admissions["level_1_p_value"] > 0.05
    assert admissions["level_2_p_value"] < 0.05
    assert np.isclose(
        admissions["coefficient_delta_level_2_minus_level_1"],
        admissions["level_2_coefficient"]
        - admissions["level_1_coefficient"],
    )
    assert "level_3" not in table.to_string()


def test_rendered_sector_control_table_has_required_warnings() -> None:
    csv_path = (
        RESULTS_DIR / "tables" / "table_5_1_1_sector_control.csv"
    )
    markdown_path = (
        RESULTS_DIR / "tables" / "table_5_1_1_sector_control.md"
    )

    assert csv_path.is_file()
    assert markdown_path.is_file()
    assert len(pd.read_csv(csv_path)) == 5
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Painel A — Especificações co-principais" in markdown
    assert "Painel B — Robustez de inferência do nível 2" in markdown
    assert "0,269†" in markdown
    assert "0,555†" in markdown
    assert (
        "admissões, desligamentos e fluxo bruto"
        in markdown
    )
    assert "não são interpretáveis" in markdown
    assert "Os pretrends de ambas falham nos cinco outcomes." in markdown
    assert "support_diagnostic" in markdown
    assert "55 CBOs tratadas" in markdown
    assert "level_3__" not in markdown
    assert "p=<" not in markdown


def test_rendered_artifacts_and_audit_report_close_gate_b3_contract() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_render.py",
        "phase8b_render_outputs",
    )
    registry = module.artifact_registry()

    for row in registry:
        for field in ("csv_path", "md_path", "png_path"):
            relative_path = row[field]
            if relative_path:
                public_relative = Path(relative_path).relative_to("results")
                assert (RESULTS_DIR / public_relative).is_file()

    table_files = sorted((RESULTS_DIR / "tables").glob("*"))
    figure_files = sorted((RESULTS_DIR / "figures").glob("*.png"))
    public_table_files = [
        path
        for path in table_files
        if "group_outcome_forest" not in path.name
    ]
    public_figure_files = figure_files
    assert len([path for path in public_table_files if path.suffix == ".csv"]) == 18
    assert len([path for path in public_table_files if path.suffix == ".md"]) == 18
    assert len(public_figure_files) == 15

    for path in public_figure_files:
        with Image.open(path) as image:
            horizontal_dpi, vertical_dpi = image.info["dpi"]
            assert horizontal_dpi >= 299
            assert vertical_dpi >= 299
            assert image.width >= 2500
            assert image.height >= 1500

    assert not (RESULTS_DIR / "RENDERIZACAO_8B.md").exists()


def test_all_main_group_table_notes_block_heterogeneity_reading() -> None:
    stems = (
        "table_5_2_1_sex",
        "table_5_2_2_race",
        "table_5_2_3_age",
        "table_5_2_4_education",
        "table_5_2_5_income",
    )
    for stem in stems:
        markdown = (
            RESULTS_DIR / "tables" / f"{stem}.md"
        ).read_text(encoding="utf-8")
        assert "Família C: 130 testes" in markdown
        assert "não medem heterogeneidade" in markdown
        assert "22 dos 26 grupos" in markdown
        assert "2 dos 100 contrastes salariais" in markdown
        assert "Família C: 100 testes" not in markdown

    sex_markdown = (
        RESULTS_DIR / "tables" / "table_5_2_1_sex.md"
    ).read_text(encoding="utf-8")
    age_appendix = (
        RESULTS_DIR / "tables" / "table_a_4_age.md"
    ).read_text(encoding="utf-8")
    assert "| Homens |" in sex_markdown
    assert "| Mulheres |" in sex_markdown
    assert "Família A (100)" in age_appendix
    assert "Família B (30)" in age_appendix


def test_portuguese_display_uses_decimal_commas_everywhere() -> None:
    common = load_module(
        RENDER_DIR,
        "phase8b_common.py",
        "phase8b_common_decimal_comma",
    )
    figures = load_module(
        RENDER_DIR,
        "phase8b_figures.py",
        "phase8b_figures_decimal_comma",
    )

    assert common.format_number(-0.0538) == "−0,0538"
    assert common.format_number(0.0221) == "0,0221"
    assert figures.format_decimal_tick(-0.05) == "−0,05"
    assert figures.format_decimal_tick(0.10) == "0,1"


def test_main_group_tables_keep_four_v1_outcomes_only() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_tables.py",
        "phase8b_tables_four_main_outcomes",
    )
    family_c = pd.read_csv(
        RESULTS_DIR / "models" / "group_did_results.csv"
    )
    diagnostics = pd.read_csv(
        RESULTS_DIR / "diagnostics" / "ddd_pretrends.csv"
    )
    sex = module.build_main_group_table(
        family_c,
        diagnostics,
        dimension="sex",
        groups=("men", "women"),
    )

    assert len(sex) == 8
    assert set(sex["outcome"]) == {
        "admissoes",
        "desligamentos",
        "ln_salario_real_adm",
        "asinh_saldo",
    }
    assert "n_movimentacoes" not in set(sex["outcome"])


def test_group_confidence_bands_use_reduced_opacity() -> None:
    module = load_module(
        RENDER_DIR,
        "phase8b_figures.py",
        "phase8b_figures_group_band_opacity",
    )

    assert module.GROUP_CI_ALPHA == 0.035
