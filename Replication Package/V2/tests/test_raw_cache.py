from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPLICATION_CODE = PACKAGE_ROOT / "code" / "replication"
if str(REPLICATION_CODE) not in sys.path:
    sys.path.insert(0, str(REPLICATION_CODE))

from raw_cache import CACHE_ID, validate_raw_cache


def _write_cache(tmp_path: Path) -> Path:
    source = tmp_path / "component" / "source.bin"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"official source")
    manifest = {
        "cache_id": CACHE_ID,
        "file_count": 1,
        "files": [
            {
                "bytes": source.stat().st_size,
                "cache_path": "component/source.bin",
                "operation": "copy",
                "original_path": "source.bin",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        ],
        "format_version": 1,
        "total_bytes": source.stat().st_size,
    }
    (tmp_path / "raw_cache_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return source


def test_raw_cache_validates_the_exact_registered_set(tmp_path: Path) -> None:
    _write_cache(tmp_path)

    assert validate_raw_cache(tmp_path) == {
        "declared_files": 1,
        "missing_files": 0,
        "present_files": 1,
        "status": "pass",
    }


def test_raw_cache_rejects_tampering_and_unregistered_files(
    tmp_path: Path,
) -> None:
    source = _write_cache(tmp_path)
    source.write_bytes(b"changed source")

    with pytest.raises(RuntimeError, match="SHA-256|byte-size"):
        validate_raw_cache(tmp_path)

    source.write_bytes(b"official source")
    (tmp_path / "extra.txt").write_text("extra", encoding="utf-8")
    with pytest.raises(RuntimeError, match="unregistered"):
        validate_raw_cache(tmp_path)


def test_unregistered_raw_directory_is_reported_without_mutation(
    tmp_path: Path,
) -> None:
    assert validate_raw_cache(tmp_path)["status"] == "not_registered"
