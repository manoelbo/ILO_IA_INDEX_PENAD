"""Validate an optional separately stored official-source cache."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


MANIFEST_NAME = "raw_cache_manifest.json"
CACHE_ID = "dissertation-replication-v2-official-raw-cache"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_raw_cache(root: Path) -> dict[str, Any]:
    """Validate every present registered file and reject unregistered extras."""
    root = root.resolve()
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        return {
            "declared_files": 0,
            "missing_files": 0,
            "present_files": 0,
            "status": "not_registered",
        }

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Raw-cache manifest must be a JSON object")
    if payload.get("cache_id") != CACHE_ID or payload.get("format_version") != 1:
        raise RuntimeError("Raw-cache identity or format version is invalid")
    records = payload.get("files")
    if not isinstance(records, list):
        raise RuntimeError("Raw-cache manifest has no file registry")

    declared: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise RuntimeError("Raw-cache record must be a JSON object")
        relative = Path(str(record.get("cache_path", "")))
        relative_text = relative.as_posix()
        if (
            not relative_text
            or relative.is_absolute()
            or ".." in relative.parts
            or relative_text == MANIFEST_NAME
        ):
            raise RuntimeError(f"Unsafe raw-cache path: {relative_text}")
        if relative_text in declared:
            raise RuntimeError(f"Duplicate raw-cache path: {relative_text}")
        declared[relative_text] = record

    if int(payload.get("file_count", -1)) != len(declared):
        raise RuntimeError("Raw-cache declared file count is inconsistent")
    expected_bytes = sum(int(record["bytes"]) for record in declared.values())
    if int(payload.get("total_bytes", -1)) != expected_bytes:
        raise RuntimeError("Raw-cache declared byte total is inconsistent")

    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    extras = sorted(set(actual) - set(declared))
    if extras:
        raise RuntimeError(f"Raw cache contains unregistered files: {extras}")

    missing = sorted(set(declared) - set(actual))
    for relative, path in actual.items():
        record = declared[relative]
        observed_bytes = path.stat().st_size
        if observed_bytes != int(record["bytes"]):
            raise RuntimeError(
                f"Raw-cache byte-size mismatch for {relative}: "
                f"expected {record['bytes']}, observed {observed_bytes}"
            )
        observed_sha256 = _sha256(path)
        if observed_sha256 != record.get("sha256"):
            raise RuntimeError(f"Raw-cache SHA-256 mismatch for {relative}")

    return {
        "declared_files": len(declared),
        "missing_files": len(missing),
        "present_files": len(actual),
        "status": "pass" if not missing else "pass_with_missing_sources",
    }
