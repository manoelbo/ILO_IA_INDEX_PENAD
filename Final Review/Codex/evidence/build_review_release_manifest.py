#!/usr/bin/env python3
"""Build a portable integrity anchor for the final-review deliverables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


FIELDNAMES = ["path", "bytes", "sha256"]
VERDICT = "DO NOT CIRCULATE"
REVIEW_ROOT = Path("Final Review/Codex")
BASELINE_MANIFEST = REVIEW_ROOT / "evidence/baseline_manifest.csv"
SUPPLEMENTARY_PATHS = (
    Path("Replication Package/README.md"),
    Path("Replication Package/.gitignore"),
    Path("Replication Package/V2/README.md"),
)
EXCLUDED_PARTS = {
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_exclude(
    path: Path,
    *,
    output: Path,
    context_output: Path,
) -> bool:
    resolved = path.resolve()
    if resolved in {output.resolve(), context_output.resolve()}:
        return True
    return (
        any(part in EXCLUDED_PARTS for part in path.parts)
        or path.suffix in {".pyc", ".pyo"}
    )


def iter_release_files(
    *,
    root: Path,
    output: Path,
    context_output: Path,
) -> Iterable[Path]:
    review_root = root / REVIEW_ROOT
    candidates: list[Path] = []
    if review_root.is_dir():
        candidates.extend(review_root.rglob("*"))
    candidates.extend(root / relative for relative in SUPPLEMENTARY_PATHS)

    seen: set[Path] = set()
    for candidate in candidates:
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        if resolved in seen or should_exclude(
            candidate,
            output=output,
            context_output=context_output,
        ):
            continue
        resolved.relative_to(root)
        seen.add(resolved)
        yield resolved


def inventory_release(
    *,
    root: Path,
    output: Path,
    context_output: Path,
) -> list[dict[str, object]]:
    root = root.resolve()
    rows = [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in iter_release_files(
            root=root,
            output=output,
            context_output=context_output,
        )
    ]
    return sorted(rows, key=lambda row: str(row["path"]))


def write_manifest(output: Path, rows: list[dict[str, object]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def summarize_git_status(status: str) -> dict[str, object]:
    summary = {
        "is_dirty": False,
        "entries": 0,
        "staged": 0,
        "unstaged": 0,
        "untracked": 0,
        "deleted": 0,
        "renamed": 0,
        "porcelain_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
    }
    for line in status.splitlines():
        if len(line) < 2:
            continue
        index_status, worktree_status = line[0], line[1]
        summary["entries"] += 1
        if index_status == "?" and worktree_status == "?":
            summary["untracked"] += 1
            continue
        if index_status not in {" ", "?"}:
            summary["staged"] += 1
        if worktree_status not in {" ", "?"}:
            summary["unstaged"] += 1
        if "D" in {index_status, worktree_status}:
            summary["deleted"] += 1
        if "R" in {index_status, worktree_status}:
            summary["renamed"] += 1
    summary["is_dirty"] = bool(summary["entries"])
    return summary


def build_context(
    *,
    root: Path,
    manifest: Path,
    generated_at_utc: str | None = None,
) -> dict[str, object]:
    status = run_git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    baseline = root / BASELINE_MANIFEST
    return {
        "generated_at_utc": generated_at_utc
        or datetime.now(timezone.utc).isoformat(),
        "git_head": run_git(root, "rev-parse", "HEAD").strip(),
        "git_status_summary": summarize_git_status(status),
        "manifest_sha256": sha256_file(manifest),
        "baseline_manifest_sha256": (
            sha256_file(baseline) if baseline.is_file() else None
        ),
        "verdict": VERDICT,
    }


def write_context(output: Path, context: dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(context, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--context-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.workspace_root.resolve()
    output = args.output.resolve()
    context_output = args.context_output.resolve()
    rows = inventory_release(
        root=root,
        output=output,
        context_output=context_output,
    )
    write_manifest(output, rows)
    write_context(
        context_output,
        build_context(root=root, manifest=output),
    )
    print(
        f"Wrote {len(rows)} files "
        f"({sum(int(row['bytes']) for row in rows)} bytes) "
        f"to {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
