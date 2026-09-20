#!/usr/bin/env python3
"""Safely freeze the current replication-package payload as generation V1."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Mapping


VERSION_DIRECTORIES = {"V1", "V2"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_baseline_hashes(manifest_path: Path) -> dict[str, str]:
    """Load path-to-SHA-256 mappings from the frozen baseline manifest."""
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"path", "sha256"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(
                "baseline manifest must contain path and sha256 columns"
            )
        return {
            row["path"]: row["sha256"]
            for row in reader
            if row["path"] and row["sha256"]
        }


def _package_prefix(package_root: Path) -> str:
    return f"{package_root.name}/"


def _current_files(package_root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in package_root.rglob("*"):
        relative = path.relative_to(package_root)
        if relative.parts and relative.parts[0] in VERSION_DIRECTORIES:
            continue
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed in frozen payload: {path}")
        if path.is_file():
            files[relative.as_posix()] = path
    return files


def verify_payload(
    *,
    package_root: Path,
    baseline_hashes: Mapping[str, str],
) -> list[str]:
    """Verify that the complete current payload matches the frozen manifest."""
    package_root = package_root.resolve()
    if not package_root.is_dir():
        raise ValueError(f"package root does not exist: {package_root}")
    if package_root.joinpath("V1").exists():
        raise ValueError("V1 already exists; refusing to version the package")

    prefix = _package_prefix(package_root)
    expected = {
        path.removeprefix(prefix): digest
        for path, digest in baseline_hashes.items()
        if path.startswith(prefix)
        and path.removeprefix(prefix).split("/", 1)[0]
        not in VERSION_DIRECTORIES
    }
    current = _current_files(package_root)

    missing = sorted(set(expected) - set(current))
    unexpected = sorted(set(current) - set(expected))
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing files: {missing}")
        if unexpected:
            details.append(f"unexpected files: {unexpected}")
        raise ValueError("payload does not match manifest; " + "; ".join(details))

    mismatches = [
        relative
        for relative, path in sorted(current.items())
        if sha256_file(path) != expected[relative]
    ]
    if mismatches:
        raise ValueError(f"hash mismatch for files: {mismatches}")

    return sorted(
        entry.name
        for entry in package_root.iterdir()
        if entry.name not in VERSION_DIRECTORIES
    )


def version_package(
    *,
    package_root: Path,
    baseline_hashes: Mapping[str, str],
    execute: bool = False,
) -> list[str]:
    """Verify the package and, when requested, atomically rename payload into V1."""
    package_root = package_root.resolve()
    entries = verify_payload(
        package_root=package_root,
        baseline_hashes=baseline_hashes,
    )
    if not execute:
        return entries

    v1_root = package_root / "V1"
    v1_root.mkdir()
    moved: list[str] = []
    try:
        for name in entries:
            package_root.joinpath(name).rename(v1_root / name)
            moved.append(name)
    except Exception:
        for name in reversed(moved):
            v1_root.joinpath(name).rename(package_root / name)
        v1_root.rmdir()
        raise
    return entries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Rename the verified current payload into V1.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    moved = version_package(
        package_root=args.package_root,
        baseline_hashes=load_baseline_hashes(args.baseline_manifest),
        execute=args.execute,
    )
    action = "Moved" if args.execute else "Verified"
    print(f"{action} {len(moved)} top-level entries: {', '.join(moved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
