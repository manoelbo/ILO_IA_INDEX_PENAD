from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = PACKAGE_ROOT / "code" / "replication" / "data_manifest.py"
    spec = importlib.util.spec_from_file_location("data_manifest", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bundle_manifest_records_legacy_csv_encoding_and_validates_hashes(
    tmp_path: Path,
) -> None:
    module = load_module()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    legacy = bundle / "occupations.csv"
    legacy.write_bytes("code,description\n1,Construção\n".encode("cp1252"))
    manifest = tmp_path / "manifest.csv"

    rows = module.build_manifest(bundle, manifest)

    assert rows[0]["encoding"] == "cp1252"
    assert module.validate_manifest(bundle, manifest)["status"] == "pass"

    legacy.write_bytes("code,description\n1,Construction\n".encode("cp1252"))
    with pytest.raises(RuntimeError, match="bytes|sha256"):
        module.validate_manifest(bundle, manifest)


def test_bundle_manifest_rejects_unregistered_files(tmp_path: Path) -> None:
    module = load_module()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "registered.csv").write_text("value\n1\n", encoding="utf-8")
    manifest = tmp_path / "manifest.csv"
    module.build_manifest(bundle, manifest)
    (bundle / "extra.csv").write_text("value\n2\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="file set differs"):
        module.validate_manifest(bundle, manifest)


def test_bundle_manifest_excludes_internal_markdown(tmp_path: Path) -> None:
    module = load_module()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "analytical.csv").write_text("value\n1\n", encoding="utf-8")
    (bundle / "development-notes.md").write_text(
        "# Internal notes\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.csv"

    rows = module.build_manifest(bundle, manifest)

    assert [row["path"] for row in rows] == ["analytical.csv"]
    assert module.validate_manifest(bundle, manifest)["status"] == "pass"


def test_frozen_bundle_manifest_has_the_public_contract_columns() -> None:
    module = load_module()
    with (PACKAGE_ROOT / "config" / "analytical_bundle_manifest.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert tuple(reader.fieldnames or ()) == (
        "path",
        "component",
        "role",
        "source_id",
        "bytes",
        "schema",
        "encoding",
        "sha256",
    )
    paths = [row["path"] for row in rows]
    assert len(paths) == len(set(paths))
    assert all(path and not Path(path).is_absolute() for path in paths)
    assert all(".." not in Path(path).parts for path in paths)
    assert all(int(row["bytes"]) > 0 for row in rows)
    assert all(len(row["sha256"]) == 64 for row in rows)
    assert all(row["schema"] and row["encoding"] for row in rows)
    by_path = {row["path"]: row for row in rows}
    assert not any(path.endswith(".md") for path in by_path)
    assert by_path["vintage/v1/core_model_reestimation.csv"]["source_id"] == (
        "v1_frozen_reference"
    )

    # A public source checkout intentionally contains only the empty data/
    # mount point. When a bundle is mounted there, additionally require the
    # complete signed file set and every byte/hash validation.
    actual_files = module.expected_bundle_files(PACKAGE_ROOT / "data")
    if actual_files:
        assert set(paths) == {
            path.relative_to(PACKAGE_ROOT / "data").as_posix()
            for path in actual_files
        }
        assert module.validate_manifest(
            PACKAGE_ROOT / "data",
            PACKAGE_ROOT / "config" / "analytical_bundle_manifest.csv",
        )["status"] == "pass"
