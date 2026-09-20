#!/usr/bin/env python3
"""Build a consolidated inventory of package and manuscript artifacts."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote


FIELDNAMES = [
    "inventory_id",
    "scope",
    "artifact_type",
    "artifact_id",
    "manuscript_line",
    "artifact_path",
    "producer",
    "input_path",
    "sha256",
    "status",
    "note",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_package_manifest(
    manifest_path: Path,
    reference_root: Path,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        for source in csv.DictReader(handle):
            artifact_path = reference_root / source["reference_path"]
            rows.append(
                {
                    "scope": f"V1 section {source['section']}",
                    "artifact_type": source["artifact_type"],
                    "artifact_id": source["artifact_id"],
                    "manuscript_line": "",
                    "artifact_path": artifact_path.as_posix(),
                    "producer": source["producer"],
                    "input_path": source["input_path"],
                    "sha256": source["reference_sha256"],
                    "status": source["status"],
                    "note": source["comparison"],
                }
            )
    return rows


def _last_caption(lines: list[str], index: int, prefix: str) -> str:
    for prior in reversed(lines[:index]):
        stripped = prior.strip().strip("*")
        if stripped.startswith(prefix):
            return stripped
    return ""


def inventory_manuscript(manuscript: Path) -> list[dict[str, object]]:
    lines = manuscript.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, object]] = []
    image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    link_pattern = re.compile(r"(?<!!)\[([^\]]+)\]\((https?://[^)]+)\)")
    table_pattern = re.compile(r"^\*\*(Tabela\s+.+?)\*\*\s*$")
    marker_pattern = re.compile(
        r"(?:file ref|ref file)\s*:|^figure_b_\d",
        flags=re.IGNORECASE,
    )

    for index, line in enumerate(lines):
        line_number = index + 1
        for match in image_pattern.finditer(line):
            target = unquote(match.group(2))
            if target.startswith(("http://", "https://", "data:")):
                resolved = None
            else:
                resolved = (manuscript.parent / target).resolve()
            exists = bool(resolved and resolved.is_file())
            rows.append(
                {
                    "scope": "canonical manuscript",
                    "artifact_type": "image",
                    "artifact_id": _last_caption(lines, index, "Figura"),
                    "manuscript_line": line_number,
                    "artifact_path": (
                        resolved.as_posix() if resolved else target
                    ),
                    "producer": "",
                    "input_path": "",
                    "sha256": sha256_file(resolved) if exists else "",
                    "status": "present" if exists else "missing",
                    "note": match.group(1),
                }
            )

        if "](data:image/" in line:
            payload = line.split("base64,", 1)[1].rsplit(")", 1)[0]
            binary = base64.b64decode(payload)
            rows.append(
                {
                    "scope": "canonical manuscript",
                    "artifact_type": "embedded_image",
                    "artifact_id": _last_caption(lines, index, "Figura"),
                    "manuscript_line": line_number,
                    "artifact_path": "embedded:data-uri",
                    "producer": "",
                    "input_path": "",
                    "sha256": hashlib.sha256(binary).hexdigest(),
                    "status": "embedded",
                    "note": f"{len(binary)} decoded bytes",
                }
            )

        table_match = table_pattern.match(line.strip())
        if table_match:
            rows.append(
                {
                    "scope": "canonical manuscript",
                    "artifact_type": "manuscript_table",
                    "artifact_id": table_match.group(1),
                    "manuscript_line": line_number,
                    "artifact_path": manuscript.as_posix(),
                    "producer": "",
                    "input_path": "",
                    "sha256": "",
                    "status": "embedded",
                    "note": "Source mapping is recorded in claim_artifact_matrix.csv",
                }
            )

        for match in link_pattern.finditer(line):
            target = match.group(2)
            if "app.notion.com/p/outputs/" not in target:
                continue
            rows.append(
                {
                    "scope": "canonical manuscript",
                    "artifact_type": "artifact_link",
                    "artifact_id": match.group(1),
                    "manuscript_line": line_number,
                    "artifact_path": target,
                    "producer": "",
                    "input_path": "",
                    "sha256": "",
                    "status": "broken",
                    "note": "HTTP 404 in the 25 July 2026 audit",
                }
            )

        if marker_pattern.search(line.strip()):
            rows.append(
                {
                    "scope": "canonical manuscript",
                    "artifact_type": "export_marker",
                    "artifact_id": line.strip()[:160],
                    "manuscript_line": line_number,
                    "artifact_path": manuscript.as_posix(),
                    "producer": "",
                    "input_path": "",
                    "sha256": "",
                    "status": "remove",
                    "note": "Visible export debris",
                }
            )

    image_rows = [
        row
        for row in rows
        if row["artifact_type"] in {"image", "embedded_image"}
        and row["sha256"]
    ]
    counts: dict[str, int] = {}
    for row in image_rows:
        digest = str(row["sha256"])
        counts[digest] = counts.get(digest, 0) + 1
    for row in image_rows:
        count = counts[str(row["sha256"])]
        if count > 1:
            note = str(row["note"])
            row["note"] = f"{note}; duplicate hash appears {count} times"
            row["status"] = "duplicate"
    return rows


def write_inventory(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            writer.writerow({"inventory_id": f"A{index:04d}", **row})


def relativize_workspace_paths(
    rows: list[dict[str, object]],
    workspace_root: Path,
) -> None:
    """Replace local absolute artifact paths with workspace-relative paths."""
    root_prefix = workspace_root.resolve().as_posix().rstrip("/") + "/"
    for row in rows:
        artifact_path = str(row["artifact_path"])
        if artifact_path.startswith(root_prefix):
            row["artifact_path"] = artifact_path[len(root_prefix) :]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.workspace_root.resolve()
    package_reference = root / "Replication Package" / "V1" / "results" / "reference"
    rows: list[dict[str, object]] = []
    rows.extend(
        inventory_package_manifest(
            package_reference / "section3" / "artifact_manifest.csv",
            package_reference / "section3",
        )
    )
    rows.extend(
        inventory_package_manifest(
            package_reference / "sections4_5" / "artifact_manifest.csv",
            package_reference / "sections4_5",
        )
    )
    rows.extend(inventory_manuscript(args.manuscript.resolve()))
    relativize_workspace_paths(rows, root)
    write_inventory(args.output, rows)
    print(f"Wrote {len(rows)} artifact records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
