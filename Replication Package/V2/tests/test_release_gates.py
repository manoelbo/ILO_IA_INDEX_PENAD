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
    module = load_module("release_build_panel", "code/panel/build_panel.py")
    panel = pd.read_parquet(
        module.DEFAULT_PANEL,
    ).head(1)
    panel.loc[:, "salario_medio_adm"] = module.WAGE_MAX

    with pytest.raises(RuntimeError, match="R\\$1 million bound"):
        module.validate_national_panel(panel)

    support = json.loads(
        module.DEFAULT_SUPPORT.read_text(encoding="utf-8")
    )
    assert support["invalid_rows_rejected"] > 0


def test_gate_03_principal_formula_has_no_contemporary_controls() -> None:
    module = load_module(
        "release_estimators",
        "code/models/estimators.py",
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
        section="4-5",
        mode="reproduce",
        raw_dir=runner.DEFAULT_RAW_DIR,
    )
    inferential = [node for node in dag if node.inferential]

    assert len(inferential) == 14
    assert all(node.disposition == runner.REESTIMATED for node in inferential)
    assert all(
        any(
            part.endswith((".py", ".R"))
            for part in node.command
        )
        for node in inferential
    )


def test_gate_05_event_study_grid_is_complete_and_ungrouped() -> None:
    module = load_module(
        "release_event_study",
        "code/models/event_study.py",
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
    module = load_module("release_parse", "code/ingest/parse.py")
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

    summary = module.validate_reference(
        PACKAGE_ROOT / "results" / "reference"
    )

    assert summary["artifacts"] == 81
    assert summary["manifest_signature_valid"]
    assert summary["semantic_contracts_valid"]


def test_gate_09_monthly_totals_match_official_adjusted_series() -> None:
    comparison = pd.read_csv(
        PACKAGE_ROOT
        / "results"
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
        "code/panel/build_panel.py",
    )

    assert module.COMPLETE_HIGHER_EDUCATION_CODES == {
        "9",
        "10",
        "11",
        "80",
    }
    assert "8" not in module.COMPLETE_HIGHER_EDUCATION_CODES
