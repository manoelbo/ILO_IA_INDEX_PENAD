from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    path = PACKAGE_ROOT / relative_path
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_gate_01_zero_flow_wages_are_missing() -> None:
    panel = pd.read_parquet(
        PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet",
        columns=[
            "admissoes",
            "desligamentos",
            "salario_medio_adm",
            "salario_medio_desl",
        ],
    )

    assert panel.loc[
        panel["admissoes"].eq(0), "salario_medio_adm"
    ].isna().all()
    assert panel.loc[
        panel["desligamentos"].eq(0), "salario_medio_desl"
    ].isna().all()


def test_gate_02_invalid_salary_is_rejected_before_release() -> None:
    module = load_module("release_build_panel", "code/caged/panel/build_panel.py")
    panel = pd.read_parquet(
        module.DEFAULT_PANEL,
    ).head(1)
    panel.loc[:, "salario_medio_adm"] = module.WAGE_MAX

    with pytest.raises(RuntimeError, match="R\\$1 million bound"):
        module.validate_national_panel(panel)

    support = json.loads(
        (
            PACKAGE_ROOT
            / "results"
            / "reference"
            / "artifacts"
            / "caged"
            / "reconciliation"
            / "painel_nacional_support.json"
        ).read_text(encoding="utf-8")
    )
    assert support["invalid_rows_rejected"] > 0


def test_gate_03_principal_formula_has_no_contemporary_controls() -> None:
    module = load_module(
        "release_estimators",
        "code/caged/models/estimators.py",
    )
    formula = module.build_formula(
        "admissoes",
        "post_treat",
        ("cbo_4d", "periodo"),
    )

    assert not any(
        control in formula for control in module.CONTEMPORARY_CONTROLS
    )
    module.validate_principal_controls(())


def test_gate_04_all_inferential_outputs_have_live_estimators() -> None:
    runner = load_module("release_runner", "run_replication.py")
    dag = runner.build_dag(
        target="caged",
        mode="reproduce",
        raw_dir=runner.DEFAULT_RAW_DIR,
    )
    inferential = [node for node in dag if node.inferential]

    assert inferential
    assert all(node.disposition == runner.REESTIMATED for node in inferential)
    assert all(
        any(
            part.endswith((".py", ".R"))
            for part in node.command
        )
        for node in inferential
    )


def test_phase8b_nodes_are_complete_and_visible_in_dry_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = load_module("phase8b_runner", "run_replication.py")
    dag = runner.build_dag(
        target="caged",
        mode="reproduce",
        raw_dir=runner.DEFAULT_RAW_DIR,
    )
    phase8b_ids = (
        "ddd_alternative_partitions",
        "ddd_alternative_partitions_pretrends",
        "group_did_family_c",
        "group_event_studies",
        "occupation_case_panel",
        "occupation_case_trajectories",
        "national_event_study_extended",
        "phase8b_rendering",
    )

    assert [
        node.node_id for node in dag if node.node_id in phase8b_ids
    ] == list(phase8b_ids)
    render_node = next(
        node for node in dag if node.node_id == "phase8b_rendering"
    )
    assert "RENDERIZACAO_8B.md" in render_node.outputs
    assert sum(path.startswith("tables/") for path in render_node.outputs) == 36
    assert sum(path.startswith("figures/") for path in render_node.outputs) == 14
    assert (
        "backing_data/figure_5_2_6_group_outcome_forest.csv"
        in render_node.outputs
    )
    assert (
        "tables/table_5_1_1_sector_control.csv"
        in render_node.outputs
    )
    assert (
        "tables/table_5_1_1_sector_control.md"
        in render_node.outputs
    )

    runner._print_dag(dag, skip_figures=False)
    dry_run_listing = capsys.readouterr().out
    assert all(node_id in dry_run_listing for node_id in phase8b_ids)


def test_phase8b_external_render_inputs_are_preflighted() -> None:
    runner = load_module("phase8b_inputs", "run_replication.py")
    inputs = set(runner._required_reproduce_inputs())

    assert (
        runner.PACKAGE_ROOT
        / "data"
        / "derived"
        / "occupation_cases"
        / "occupation_case_dictionary.csv"
    ) in inputs
    assert (
        runner.PACKAGE_ROOT
        / "data"
        / "derived"
        / "occupation_cases"
        / "table_c_1_occupation_case_exposure_summary.csv"
    ) in inputs
    assert all(path.is_relative_to(runner.PACKAGE_ROOT) for path in inputs)


def test_gate_05_event_study_grid_is_complete_and_ungrouped() -> None:
    module = load_module(
        "release_event_study",
        "code/caged/models/event_study.py",
    )
    grid = module.build_event_grid()
    module.validate_event_grid(grid)

    assert grid["event_time"].tolist() == list(range(-23, 24))
    assert grid["event_time"].is_unique
    assert grid.loc[grid["is_reference"], "event_time"].tolist() == [-1]


def test_gate_06_every_merge_reports_uniqueness_and_row_delta() -> None:
    raw_merge_calls = []
    for path in (PACKAGE_ROOT / "code").rglob("*.py"):
        if path.name == "merge_audit.py":
            continue
        if ".merge(" in path.read_text(encoding="utf-8"):
            raw_merge_calls.append(str(path.relative_to(PACKAGE_ROOT)))
    assert raw_merge_calls == []

    module = load_module(
        "release_merge_audit",
        "code/common/merge_audit.py",
    )
    reports: list[dict[str, object]] = []
    result = module.audited_merge(
        pd.DataFrame({"id": [1, 2]}),
        pd.DataFrame({"id": [1, 2], "value": ["a", "b"]}),
        merge_id="release_gate_fixture",
        on="id",
        how="left",
        validate="one_to_one",
        reporter=reports.append,
    )

    assert len(result) == 2
    assert reports == [
        {
            "after_rows": 2,
            "delta_vs_left_rows": 0,
            "left_key_unique": True,
            "left_rows": 2,
            "merge_id": "release_gate_fixture",
            "right_key_unique": True,
            "right_rows": 2,
            "validate": "one_to_one",
        }
    ]


def test_gate_07_demographic_fixtures_cover_unknown_and_missing() -> None:
    module = load_module("release_parse", "code/caged/ingest/parse.py")
    fixture = pd.DataFrame(
        {
            "sexo": ["9", ""],
            "racacor": ["9", ""],
            "graudeinstrucao": ["99", ""],
        }
    )

    module.validate_domains(fixture)
    assert {"9", ""} == set(fixture["sexo"])
    assert {"9", ""} == set(fixture["racacor"])
    assert {"99", ""} == set(fixture["graudeinstrucao"])


def test_gate_08_reference_files_match_signed_manifest() -> None:
    module = load_module(
        "release_contracts",
        "code/replication/contracts.py",
    )
    registry = load_module(
        "release_registry",
        "code/replication/registry.py",
    )
    reference = PACKAGE_ROOT / "results" / "reference"

    summary = module.validate_reference(reference)
    manifest = json.loads(
        (reference / "manifest.json").read_text(encoding="utf-8")
    )
    publication_index = pd.read_csv(
        reference / "artifacts" / "publication_index.csv"
    )
    expected_publications = {
        record.artifact_id for record in registry.manuscript_artifacts()
    }

    assert summary["artifacts"] == len(manifest["artifacts"])
    assert set(publication_index["artifact_id"]) == expected_publications
    assert set(publication_index["reference_path"]) == {
        record.reference_path for record in registry.manuscript_artifacts()
    }
    assert summary["manifest_signature_valid"]
    assert summary["semantic_contracts_valid"]


def test_phase8a_and_8b_reference_candidates_have_declared_sources() -> None:
    module = load_module(
        "phase8b_contracts",
        "code/replication/contracts.py",
    )
    artifact_root = (
        PACKAGE_ROOT / "results" / "reference" / "artifacts"
    )
    artifacts = module._result_artifacts(artifact_root)
    relative_paths = [
        path.relative_to(artifact_root).as_posix()
        for path in artifacts
    ]

    manifest = json.loads(
        (
            PACKAGE_ROOT / "results" / "reference" / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert set(relative_paths) == {
        record["path"] for record in manifest["artifacts"]
    }
    assert not any(
        part.startswith(".")
        for path in relative_paths
        for part in Path(path).parts
    )
    assert all(module.source_id_for(path) for path in relative_paths)
    assert (
        module.source_id_for(
            "caged/diagnostics/DIAGNOSTICO_PRETRENDS.md"
        )
        == "code.caged.models.pretrend_report"
    )
    assert (
        module.source_id_for("caged/models/group_did_results.csv")
        == "code.caged.models.group_did_results"
    )
    assert (
        module.source_id_for("caged/tables/table_5_2_1_sex.csv")
        == "code.render.phase8b_tables"
    )
    assert (
        "caged/figures/figure_5_2_6_group_outcome_forest.png"
        in relative_paths
    )
    assert module.source_id_for(
        "caged/figures/figure_5_2_6_group_outcome_forest.png"
    ) == "code.render.phase8b_figures"


def test_gate_09_monthly_totals_match_official_adjusted_series() -> None:
    comparison = pd.read_csv(
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "reconciliation"
        / "pdet_vs_v2_mensal.csv"
    )
    difference_columns = [
        "diferenca_admissoes_abs",
        "diferenca_desligamentos_abs",
        "diferenca_saldo_abs",
    ]

    assert len(comparison) == 65
    assert comparison[difference_columns].to_numpy().sum() == 0


def test_gate_10_complete_higher_education_excludes_code_8() -> None:
    module = load_module(
        "release_build_panel_codes",
        "code/caged/panel/build_panel.py",
    )

    assert module.COMPLETE_HIGHER_EDUCATION_CODES == {
        "9",
        "10",
        "11",
        "80",
    }
    assert "8" not in module.COMPLETE_HIGHER_EDUCATION_CODES
