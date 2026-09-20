"""Deterministic run manifest generation."""

from __future__ import annotations

import importlib.metadata
import json
import platform
from pathlib import Path
from typing import Iterable

from .files import display_path, sha256_file


PACKAGES = (
    "basedosdados",
    "geopandas",
    "google-cloud-bigquery",
    "google-cloud-bigquery-storage",
    "matplotlib",
    "numpy",
    "openpyxl",
    "pandas",
    "Pillow",
    "pyarrow",
    "pyogrio",
    "pyfixest",
    "scipy",
    "seaborn",
    "shapely",
)


def write_run_manifest(
    *,
    package_root: Path,
    output_dir: Path,
    section: str,
    mode: str,
    inputs: Iterable[Path],
    failure_count: int,
) -> Path:
    input_records = [
        {
            "path": display_path(path, package_root),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in inputs
        if path.exists() and path.is_file()
    ]
    artifacts = [
        {
            "path": path.relative_to(output_dir).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "run_manifest.json"
    ]
    code_roots = [package_root / "code" / "common"]
    if section == "3":
        code_roots.append(package_root / "code" / "section3")
    elif section == "4-5":
        code_roots.append(package_root / "code" / "sections4_5")
    else:
        code_roots.append(package_root / "code")
    code_files = [
        path
        for path in [
            package_root / "run_replication.py",
            package_root / "requirements.txt",
            package_root / "requirements-full.txt",
            *[
                source
                for code_root in code_roots
                for source in sorted(code_root.rglob("*.py"))
            ],
        ]
        if path.is_file()
    ]
    manifest = {
        "schema_version": "dissertation_replication_v2",
        "section": section,
        "mode": mode,
        "failure_count": failure_count,
        "software": {
            "python": platform.python_version(),
            **{name: _version(name) for name in PACKAGES},
        },
        "code": [
            {
                "path": path.relative_to(package_root).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in code_files
        ],
        "inputs": input_records,
        "artifacts": artifacts,
    }
    path = output_dir / "run_manifest.json"
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"
