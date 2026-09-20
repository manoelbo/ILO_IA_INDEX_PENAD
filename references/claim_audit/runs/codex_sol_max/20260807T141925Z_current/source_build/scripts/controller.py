#!/usr/bin/env python3
"""Compatibility facade for current-run quality-control tooling.

The historical blind-QC controller expects the original audit controller API.
This module exposes only its deterministic filesystem helpers while delegating
all authoritative-input checks to ``current_controller``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PyPDF2 import PdfReader

import current_controller as _current


RUN_DIR = _current.RUN_DIR
RUN_ID = RUN_DIR.name
WORKSPACE = _current.PROJECT_DIR
SOURCE_BUILD = RUN_DIR / "source_build"
RESULTS_DIR = _current.RESULTS_DIR
SCHEMA_PATH = _current.SCHEMA_PATH


utc_now = _current.utc_now
sha256_file = _current.sha256_file
atomic_write_json = _current.atomic_json
atomic_write_text = _current.atomic_text


def canonical_sha(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def atomic_write_tsv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    _current.atomic_tsv(path, columns, rows)


def queue_rows() -> tuple[list[str], list[dict[str, str]]]:
    return _current.queue()


def load_manifest() -> dict[str, Any]:
    manifest = json.loads(_current.MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest.setdefault("model_fallback_allowed", False)
    manifest.setdefault("claude_outputs_read", False)
    manifest.setdefault("timestamps", {})
    return manifest


def save_manifest(manifest: dict[str, Any]) -> None:
    _current.atomic_json(_current.MANIFEST_PATH, manifest)


def verify_authoritative_inputs(checkpoint: str) -> None:
    _current.verify_inputs(checkpoint)

