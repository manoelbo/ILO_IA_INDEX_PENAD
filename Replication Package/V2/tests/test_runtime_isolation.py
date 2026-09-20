from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RUNNER = PACKAGE_ROOT / "run_replication.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("runtime_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load replication runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_runtime_data_and_reference_are_independent_copies(tmp_path: Path) -> None:
    module = _load_runner()
    data_dir = tmp_path / "bundle"
    reference_dir = tmp_path / "reference"
    data_dir.mkdir()
    reference_dir.mkdir()
    (data_dir / "input.txt").write_text("frozen input", encoding="utf-8")
    (reference_dir / "manifest.json").write_text("signed", encoding="utf-8")

    runtime = module.materialize_execution_root(
        work_dir=tmp_path / "runtime",
        data_dir=data_dir,
        reference_dir=reference_dir,
    )
    (runtime / "data" / "input.txt").write_text("changed", encoding="utf-8")
    (runtime / "results" / "reference" / "manifest.json").write_text(
        "changed",
        encoding="utf-8",
    )

    assert (data_dir / "input.txt").read_text(encoding="utf-8") == "frozen input"
    assert (
        reference_dir / "manifest.json"
    ).read_text(encoding="utf-8") == "signed"
    assert (runtime / "code" / "caged" / "models" / "event_study.py").is_file()


def test_caged_commands_are_remapped_to_the_runtime_root(tmp_path: Path) -> None:
    module = _load_runner()
    runtime = tmp_path / "runtime"
    command = (
        sys.executable,
        str(PACKAGE_ROOT / "code" / "caged" / "models" / "event_study.py"),
    )

    remapped = module.remap_command_to_runtime(command, runtime)

    assert remapped[0] == sys.executable
    assert remapped[1] == str(runtime / "code" / "caged" / "models" / "event_study.py")


def test_external_raw_cache_is_copied_and_remapped_inside_runtime(
    tmp_path: Path,
) -> None:
    module = _load_runner()
    data_dir = tmp_path / "bundle"
    raw_dir = tmp_path / "raw-cache"
    reference_dir = tmp_path / "reference"
    (data_dir / "vintage" / "crosswalk").mkdir(parents=True)
    raw_dir.mkdir()
    reference_dir.mkdir()
    (data_dir / "vintage" / "crosswalk" / "metadata.csv").write_text(
        "value\n1\n", encoding="utf-8"
    )
    (raw_dir / "CAGEDMOV202101.7z").write_bytes(b"archive")
    (reference_dir / "manifest.json").write_text("signed", encoding="utf-8")

    runtime = module.materialize_execution_root(
        work_dir=tmp_path / "runtime-raw",
        data_dir=data_dir,
        raw_dir=raw_dir,
        reference_dir=reference_dir,
    )
    command = (sys.executable, str(raw_dir / "CAGEDMOV202101.7z"))
    remapped = module.remap_command_to_runtime(
        command,
        runtime,
        data_dir=data_dir,
        raw_dir=raw_dir,
    )

    assert (
        runtime / "data" / "vintage" / "crosswalk" / "metadata.csv"
    ).is_file()
    assert (
        runtime / "data" / "vintage" / "CAGEDMOV202101.7z"
    ).read_bytes() == b"archive"
    assert remapped[1] == str(
        runtime / "data" / "vintage" / "CAGEDMOV202101.7z"
    )


def test_caged_promotion_excludes_internal_markdown_and_keeps_public_forest(
    tmp_path: Path,
) -> None:
    module = _load_runner()
    runtime = tmp_path / "runtime"
    results = runtime / "results"
    (results / "tables").mkdir(parents=True)
    (results / "figures").mkdir()
    (results / "diagnostics").mkdir()
    (results / "tables" / "table_5_1.md").write_text(
        "# Published table\n", encoding="utf-8"
    )
    (results / "diagnostics" / "INTERNAL_VERDICT.md").write_text(
        "internal\n", encoding="utf-8"
    )
    (results / "figures" / "figure_5_2_6_group_outcome_forest.png").write_bytes(
        b"published"
    )

    module.copy_runtime_results(
        runtime,
        tmp_path / "public" / "caged",
        skip_figures=False,
    )

    assert (tmp_path / "public" / "caged" / "tables" / "table_5_1.md").is_file()
    assert not (
        tmp_path / "public" / "caged" / "diagnostics" / "INTERNAL_VERDICT.md"
    ).exists()
    assert (
        tmp_path
        / "public"
        / "caged"
        / "figures"
        / "figure_5_2_6_group_outcome_forest.png"
    ).read_bytes() == b"published"
