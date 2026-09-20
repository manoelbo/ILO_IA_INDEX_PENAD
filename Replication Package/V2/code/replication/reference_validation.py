#!/usr/bin/env python3
"""Freeze and compare the component-organized public reference bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = PACKAGE_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from common.artifacts import compare_png
from replication.contracts import freeze_reference, sha256_file
from replication.registry import COMPONENTS, manuscript_artifacts


REFERENCE_DIR = PACKAGE_ROOT / "results" / "reference"
REPRODUCED_DIR = PACKAGE_ROOT / "results" / "reproduced"
IGNORED_COMPONENT_FILES = frozenset(
    {
        "INDEX.md",
        "artifact_manifest.csv",
        "run_manifest.json",
        "validation_checks.csv",
        "validation_checks.md",
    }
)
PUBLICATION_FIELDS = (
    "artifact_id",
    "caption",
    "component",
    "producer",
    "input_contract",
    "reference_path",
    "command",
    "bytes",
    "sha256",
)


def _component_files(root: Path, component: str) -> dict[str, Path]:
    component_root = root / component
    if not component_root.is_dir():
        raise FileNotFoundError(f"Missing reproduced component: {component_root}")
    return {
        path.relative_to(component_root).as_posix(): path
        for path in sorted(component_root.rglob("*"))
        if path.is_file() and path.name not in IGNORED_COMPONENT_FILES
    }


def _atomic_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    fieldnames = list(rows[0]) if rows else [
        "component",
        "path",
        "status",
        "comparison",
        "reference_sha256",
        "reproduced_sha256",
    ]
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def compare_reproduced_components(
    *,
    output_root: Path,
    reference_dir: Path,
    components: Sequence[str],
    skip_figures: bool,
    report_path: Path,
) -> dict[str, Any]:
    """Require the reproduced component sets to match the signed reference."""
    reference_root = reference_dir / "artifacts"
    rows: list[dict[str, Any]] = []
    for component in components:
        expected = _component_files(reference_root, component)
        observed = _component_files(output_root, component)
        if skip_figures:
            expected = {
                path: value
                for path, value in expected.items()
                if not path.endswith(".png")
            }
            observed = {
                path: value
                for path, value in observed.items()
                if not path.endswith(".png")
            }
        for relative in sorted(set(expected) | set(observed)):
            reference = expected.get(relative)
            reproduced = observed.get(relative)
            if reference is None:
                status, comparison = "FAIL", "unexpected reproduced artifact"
            elif reproduced is None:
                status, comparison = "FAIL", "missing reproduced artifact"
            elif reference.suffix.lower() == ".png":
                matches, comparison = compare_png(reference, reproduced)
                status = "PASS" if matches else "FAIL"
            else:
                matches = reference.read_bytes() == reproduced.read_bytes()
                status = "PASS" if matches else "FAIL"
                comparison = "byte-identical" if matches else "bytes differ"
            rows.append(
                {
                    "component": component,
                    "path": relative,
                    "status": status,
                    "comparison": comparison,
                    "reference_sha256": sha256_file(reference) if reference else "",
                    "reproduced_sha256": sha256_file(reproduced) if reproduced else "",
                }
            )
    _atomic_csv(rows, report_path)
    failures = sum(row["status"] != "PASS" for row in rows)
    summary = {
        "artifacts": len(rows),
        "components": list(components),
        "failures": failures,
        "status": "pass" if failures == 0 else "fail",
    }
    if failures:
        raise RuntimeError(
            f"Reproduced artifacts differ from the signed reference; "
            f"see {report_path}"
        )
    return summary


def _valid_reproduced_manifest(root: Path) -> bool:
    manifest_path = root / "run_manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return False
    if (
        payload.get("package_id") != "dissertation-replication-v2"
        or payload.get("status") != "complete"
        or set(payload.get("components", [])) != set(COMPONENTS)
    ):
        return False
    declared = payload.get("artifacts")
    if not isinstance(declared, list):
        return False
    expected: set[str] = set()
    for record in declared:
        relative = Path(str(record.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            return False
        path = root / relative
        if (
            not path.is_file()
            or path.stat().st_size != record.get("bytes")
            or sha256_file(path) != record.get("sha256")
        ):
            return False
        expected.add(relative.as_posix())
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    return actual == expected


def _public_markdown(relative: Path) -> bool:
    if relative == Path("INDEX.md"):
        return True
    return len(relative.parts) >= 2 and relative.parts[1] == "tables"


def _write_publication_index(staging: Path) -> None:
    rows: list[dict[str, Any]] = []
    for record in manuscript_artifacts():
        path = staging / record.reference_path
        if not path.is_file():
            raise FileNotFoundError(
                f"Registered publication is absent from the freeze: {path}"
            )
        rows.append(
            {
                "artifact_id": record.artifact_id,
                "caption": record.caption,
                "component": record.component,
                "producer": record.producer,
                "input_contract": record.input_contract,
                "reference_path": record.reference_path,
                "command": record.command,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    index_csv = staging / "publication_index.csv"
    with index_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=PUBLICATION_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Signed reference index",
        "",
        "This index maps every computational table and figure in the manuscript "
        "to its signed reference artifact and public reproduction command.",
        "",
        "[Machine-readable publication index](publication_index.csv)",
        "",
        "| Component | Artifact | Caption | Reference | Command |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        path = row["reference_path"]
        lines.append(
            f"| {row['component']} | `{row['artifact_id']}` | {row['caption']} | "
            f"[{path}]({path}) | `{row['command']}` |"
        )
    lines.append("")
    (staging / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def freeze_from_reproduced(
    *, reproduced_dir: Path, reference_dir: Path
) -> dict[str, Any]:
    """Create a signed reference only from a verified, complete public run."""
    reproduced_dir = reproduced_dir.resolve()
    reference_dir = reference_dir.resolve()
    if not _valid_reproduced_manifest(reproduced_dir):
        raise RuntimeError("The source is not a valid complete five-component run")
    if reference_dir.exists() and any(reference_dir.iterdir()):
        raise RuntimeError(
            "Reference destination is not empty; archive the prior signed freeze first"
        )
    reference_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="reference-freeze-", dir=reference_dir.parent
    ) as temporary_directory:
        staging = Path(temporary_directory)
        for component in COMPONENTS:
            for relative, source in _component_files(
                reproduced_dir, component
            ).items():
                component_relative = Path(component) / relative
                if source.suffix.lower() == ".md" and not _public_markdown(
                    component_relative
                ):
                    continue
                destination = staging / component_relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        claims = reproduced_dir / "validation" / "numeric_claims_reconciliation.csv"
        if not claims.is_file():
            raise FileNotFoundError(claims)
        destination = staging / "validation" / claims.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(claims, destination)
        _write_publication_index(staging)
        return freeze_reference(staging, reference_dir)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--output-root", type=Path, default=REPRODUCED_DIR)
    compare.add_argument("--reference-dir", type=Path, default=REFERENCE_DIR)
    compare.add_argument("--component", action="append", choices=COMPONENTS)
    compare.add_argument("--skip-figures", action="store_true")
    compare.add_argument("--report", type=Path)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--reproduced-dir", type=Path, default=REPRODUCED_DIR)
    freeze.add_argument("--reference-dir", type=Path, default=REFERENCE_DIR)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.action == "freeze":
        summary = freeze_from_reproduced(
            reproduced_dir=args.reproduced_dir,
            reference_dir=args.reference_dir,
        )
    else:
        components = tuple(args.component or COMPONENTS)
        report = args.report or (
            args.output_root / "validation" / "reference_comparison.csv"
        )
        summary = compare_reproduced_components(
            output_root=args.output_root.resolve(),
            reference_dir=args.reference_dir.resolve(),
            components=components,
            skip_figures=args.skip_figures,
            report_path=report.resolve(),
        )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
