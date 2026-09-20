"""Isolated six-stage raw-data DAG for Sections 4–5."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from common.files import copy_file, sha256_file
from .contracts import BACKING_DATA_FILES


@dataclass(frozen=True)
class FullStage:
    stage_id: str
    description: str
    commands: tuple[tuple[str, ...], ...]


REQUIRED_RAW_FILENAMES = (
    "caged_2021.parquet",
    "caged_2022.parquet",
    "caged_2023.parquet",
    "caged_2024.parquet",
    "caged_2025.parquet",
    "cbo-isco-conc.csv",
    "isco_08_to_88.xlsx",
    "isco_08_structure.xlsx",
)

OPTIONAL_CROSSWALK_CACHE_FILENAMES = (
    "mte_cbo2002_cbo94_ciuo88_by_family.csv",
    "caged_mte_bridge_full.csv",
)

FULL_DAG = (
    FullStage(
        "01_panel",
        "Aggregate raw CAGED records into the CBO-month panel.",
        (("etapa_2a_preparacao_dados_did_caged_ilo.py",),),
    ),
    FullStage(
        "02_crosswalk_treatment",
        "Apply the official crosswalk and build strict treatment roles.",
        (("build_treatment_classification.py",),),
    ),
    FullStage(
        "03_analysis_panel",
        "Create the analytic panel and controls.",
        (("etapa_2b_analise_did_caged_ilo.py",),),
    ),
    FullStage(
        "04_models",
        "Estimate national DiD, DDD, event studies, and robustness models.",
        (("build_section4_final_event_study_package.py",),),
    ),
    FullStage(
        "05_extensions",
        "Estimate demographic and occupation-case extensions in separate outputs.",
        (
            ("section4_5_final/section5_2_dynamic_figures.py",),
            ("section4_5_final/section5_2_combined_figures.py",),
            ("section4_5_final/section5_2_age_pnad_figures.py",),
            ("build_section5_2_race_color_b.py",),
            ("build_section5_2_income_pnad.py",),
            ("build_section5_3_occupation_cases.py",),
        ),
    ),
    FullStage(
        "06_artifacts",
        "Build curated sources and hand control to the public artifact renderer.",
        (("build_replication_curated_tables.py",),),
    ),
)


def full_input_status(raw_dir: Path) -> list[tuple[str, bool]]:
    """Return the expected user-supplied files and their current status."""
    return [
        (filename, (raw_dir / filename).is_file())
        for filename in REQUIRED_RAW_FILENAMES
    ]


def optional_cache_status(raw_dir: Path) -> list[tuple[str, bool]]:
    """Return optional, version-pinning crosswalk caches."""
    return [
        (filename, (raw_dir / filename).is_file())
        for filename in OPTIONAL_CROSSWALK_CACHE_FILENAMES
    ]


def validate_full_inputs(
    raw_dir: Path,
    billing_project: str | None = None,
) -> list[Path]:
    paths = [raw_dir / filename for filename in REQUIRED_RAW_FILENAMES]
    missing = [
        path
        for path in paths
        if not path.is_file()
        and not (
            billing_project
            and path.name.startswith("caged_")
            and path.suffix == ".parquet"
        )
    ]
    if missing:
        rendered = "\n".join(f"- {path.name}" for path in missing)
        raise FileNotFoundError(
            "Missing raw inputs for the Sections 4–5 full DAG:\n"
            f"{rendered}\nSee README.md for sources and expected filenames."
        )
    return paths


def run_full_rebuild(
    *,
    package_root: Path,
    raw_dir: Path,
    billing_project: str | None,
) -> Path:
    """Run author scripts in an isolated workspace and return its data root."""
    validate_full_inputs(raw_dir, billing_project)
    workspace = package_root / "work" / "sections4_5"
    _prepare_workspace(workspace, package_root)
    _stage_author_code(package_root, workspace)
    _stage_raw_and_auxiliary_inputs(
        package_root=package_root,
        raw_dir=raw_dir,
        workspace=workspace,
    )
    _write_workspace_manifest(
        workspace,
        raw_dir,
        _manifest_input_paths(workspace, raw_dir),
        status="running",
    )

    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["MPLBACKEND"] = "Agg"
    environment["PYTHONPATH"] = str(workspace / "src" / "scripts")
    if billing_project:
        environment["REPLICATION_BILLING_PROJECT"] = billing_project
    scripts = workspace / "src" / "scripts"
    for stage in FULL_DAG:
        print(f"[sections4_5/full] {stage.stage_id}: {stage.description}", flush=True)
        for command in stage.commands:
            subprocess.run(
                [sys.executable, str(scripts / command[0]), *command[1:]],
                cwd=workspace,
                env=environment,
                check=True,
            )

    _collect_backing_data(workspace)
    _write_workspace_manifest(
        workspace,
        raw_dir,
        _manifest_input_paths(workspace, raw_dir),
        status="complete",
    )
    return workspace


def _manifest_input_paths(workspace: Path, raw_dir: Path) -> list[Path]:
    paths = [
        workspace / "data" / "raw" / f"caged_{year}.parquet"
        for year in range(2021, 2026)
    ]
    paths.extend(
        raw_dir / filename
        for filename in REQUIRED_RAW_FILENAMES
        if not filename.startswith("caged_")
    )
    paths.extend(
        raw_dir / filename
        for filename in OPTIONAL_CROSSWALK_CACHE_FILENAMES
    )
    paths.extend(
        [
            workspace / "data" / "input" / filename
            for filename in (
                "occupation_case_dictionary.csv",
                "occupation_case_official_metadata.csv",
                "occupation_case_dictionary_source_manifest.csv",
            )
        ]
    )
    paths.extend(
        [
            workspace / "data" / "processed" / filename
            for filename in (
                "ilo_exposure_clean.csv",
                "ipca_mensal.parquet",
                "section5_2_dynamic_micro_pairs.parquet",
                "section5_2_dynamic_age_pnad_pairs.parquet",
            )
        ]
    )
    return [path for path in paths if path.is_file()]


def _prepare_workspace(workspace: Path, package_root: Path) -> None:
    workspace = workspace.resolve()
    expected = (package_root / "work" / "sections4_5").resolve()
    if workspace != expected:
        raise ValueError(f"Unexpected full-pipeline workspace: {workspace}")
    marker = workspace / "full_run_manifest.json"
    if workspace.exists() and any(workspace.iterdir()):
        if not marker.is_file():
            raise ValueError(
                "Refusing to replace a non-empty Sections 4–5 workspace "
                "without full_run_manifest.json."
            )
        for child in workspace.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    workspace.mkdir(parents=True, exist_ok=True)


def _stage_author_code(package_root: Path, workspace: Path) -> None:
    source = (
        package_root
        / "code"
        / "sections4_5"
        / "author_pipeline"
        / "src"
    )
    if not source.is_dir():
        raise FileNotFoundError(f"Missing packaged author pipeline: {source}")
    shutil.copytree(source, workspace / "src")


def _stage_raw_and_auxiliary_inputs(
    *,
    package_root: Path,
    raw_dir: Path,
    workspace: Path,
) -> None:
    data_raw = workspace / "data" / "raw"
    data_input = workspace / "data" / "input"
    data_processed = workspace / "data" / "processed"
    data_output = workspace / "data" / "output"
    for directory in (data_raw, data_input, data_processed, data_output):
        directory.mkdir(parents=True, exist_ok=True)

    for year in range(2021, 2026):
        source = raw_dir / f"caged_{year}.parquet"
        if source.is_file():
            copy_file(source, data_raw / source.name)
    copy_file(raw_dir / "cbo-isco-conc.csv", data_input / "cbo-isco-conc.csv")
    copy_file(
        raw_dir / "isco_08_to_88.xlsx",
        data_input / "Correspondência ISCO 08 a 88.xlsx",
    )
    copy_file(
        raw_dir / "isco_08_structure.xlsx",
        data_input / "ISCO 08 Estruturas e Definições.xlsx",
    )

    section3_ilo = (
        package_root / "data" / "derived" / "section3" / "ilo_exposure_clean.parquet"
    )
    _parquet_to_csv(section3_ilo, data_processed / "ilo_exposure_clean.csv")
    frozen = package_root / "data" / "derived" / "sections4_5"
    for filename in (
        "ipca_mensal.parquet",
        "section5_2_dynamic_micro_pairs.parquet",
        "section5_2_dynamic_age_pnad_pairs.parquet",
    ):
        copy_file(
            frozen / "data" / "processed" / filename,
            data_processed / filename,
        )
    copy_file(
        frozen
        / "backing_data"
        / "section5_3_occupation_cases"
        / "occupation_case_dictionary.csv",
        data_input / "occupation_case_dictionary.csv",
    )
    for filename in (
        "occupation_case_official_metadata.csv",
        "occupation_case_dictionary_source_manifest.csv",
    ):
        copy_file(
            frozen / "data" / "input" / filename,
            data_input / filename,
        )

    optional_targets = {
        "mte_cbo2002_cbo94_ciuo88_by_family.csv": (
            workspace
            / "outputs"
            / "crosswalk_audit"
            / "source_dictionaries"
            / "mte_cbo2002_cbo94_ciuo88_by_family.csv"
        ),
        "caged_mte_bridge_full.csv": (
            workspace
            / "outputs"
            / "crosswalk_audit"
            / "official_mte_bridge"
            / "caged_mte_bridge_full.csv"
        ),
    }
    for filename, target in optional_targets.items():
        source = raw_dir / filename
        if source.is_file():
            copy_file(source, target)
def _parquet_to_csv(source: Path, target: Path) -> None:
    import pandas as pd

    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.read_parquet(source).to_csv(target, index=False, lineterminator="\n")


def _collect_backing_data(workspace: Path) -> None:
    target = workspace / "backing_data"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    sources = (
        (
            workspace / "outputs" / "section4_5_final" / "tables",
            target / "curated_tables",
        ),
        (
            workspace
            / "outputs"
            / "dissertation_section4"
            / "final_event_study"
            / "tables",
            target / "national_event_study",
        ),
        (
            workspace
            / "outputs"
            / "section4_5_final"
            / "section5_2_dynamic_combined"
            / "tables",
            target / "section5_2_dynamic",
        ),
        (
            workspace
            / "outputs"
            / "section4_5_final"
            / "section5_2_age_pnad_combined"
            / "tables",
            target / "section5_2_age_pnad",
        ),
        (
            workspace / "outputs" / "section5_3_occupation_cases" / "tables",
            target / "section5_3_occupation_cases",
        ),
    )
    for source_dir, target_dir in sources:
        if not source_dir.is_dir():
            raise FileNotFoundError(
                f"Full DAG did not produce required directory: {source_dir}"
            )
        target_dir.mkdir(parents=True, exist_ok=True)
        for source in source_dir.glob("*.csv"):
            copy_file(source, target_dir / source.name)
    missing = [
        relative
        for relative in BACKING_DATA_FILES
        if not (target / relative).is_file()
    ]
    if missing:
        rendered = "\n".join(f"- {relative}" for relative in missing)
        raise FileNotFoundError(
            "Full DAG did not generate the public backing-data contract:\n"
            f"{rendered}"
        )


def _write_workspace_manifest(
    workspace: Path,
    raw_dir: Path,
    raw_inputs: list[Path],
    *,
    status: str,
) -> None:
    payload = {
        "schema_version": "sections4_5_full_workspace_v1",
        "status": status,
        "raw_input_directory": f"<external>/{raw_dir.name}",
        "raw_inputs": [
            {
                "path": path.name,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in raw_inputs
        ],
        "stages": [
            {
                "id": stage.stage_id,
                "description": stage.description,
                "commands": [" ".join(command) for command in stage.commands],
            }
            for stage in FULL_DAG
        ],
    }
    (workspace / "full_run_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
