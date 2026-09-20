from __future__ import annotations

import importlib.util
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "backing.py"


def load_module():
    spec = importlib.util.spec_from_file_location("caged_backing", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the CAGED backing module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_caged_backing_validates_against_the_analytical_bundle() -> None:
    module = load_module()
    source = (
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "caged"
        / "construction_outputs"
    )

    summary = module.validate_construction_backing(
        PACKAGE_ROOT / "data",
        source,
    )

    assert summary == {"files": len(module.EXPECTED_FILES), "status": "pass"}


def test_materialization_preserves_the_registered_file_set(tmp_path: Path) -> None:
    module = load_module()
    source = (
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "caged"
        / "construction_outputs"
    )

    module.materialize(source, tmp_path)

    assert {
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    } == module.EXPECTED_FILES
