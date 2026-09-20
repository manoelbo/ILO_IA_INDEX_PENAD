#!/usr/bin/env python3
"""Build a stable SHA-256 manifest for the final-review baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


FIELDNAMES = [
    "path",
    "bytes",
    "mtime_utc",
    "sha256",
    "tracked",
    "git_status",
]

EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_exclude(relative_path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in relative_path.parts):
        return True
    posix = relative_path.as_posix()
    return (
        posix.startswith("Final Review/Codex/")
        or "/results/reproduced/" in f"/{posix}/"
        or "/work/" in f"/{posix}/"
    )


def iter_files(root: Path, include_paths: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for include_path in include_paths:
        absolute = (root / include_path).resolve()
        if not absolute.exists():
            continue
        candidates = [absolute] if absolute.is_file() else absolute.rglob("*")
        for candidate in candidates:
            if not candidate.is_file():
                continue
            relative = candidate.relative_to(root)
            if should_exclude(relative) or relative in seen:
                continue
            seen.add(relative)
            yield candidate


def inventory_paths(
    *,
    root: Path,
    include_paths: Iterable[Path],
    tracked_paths: set[str],
    status_by_path: dict[str, str],
) -> list[dict[str, object]]:
    root = root.resolve()
    rows: list[dict[str, object]] = []
    for path in iter_files(root, include_paths):
        relative = path.relative_to(root).as_posix()
        stat = path.stat()
        rows.append(
            {
                "path": relative,
                "bytes": stat.st_size,
                "mtime_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
                "sha256": sha256_file(path),
                "tracked": "true" if relative in tracked_paths else "false",
                "git_status": status_by_path.get(relative, ""),
            }
        )
    return sorted(rows, key=lambda row: str(row["path"]))


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def git_metadata(root: Path) -> tuple[set[str], dict[str, str]]:
    tracked = {
        path
        for path in run_git(root, "ls-files").splitlines()
        if path
    }
    status_by_path: dict[str, str] = {}
    for line in run_git(
        root, "status", "--porcelain=v1", "--untracked-files=all"
    ).splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        status_by_path[path] = status
    return tracked, status_by_path


def write_manifest(output: Path, rows: list[dict[str, object]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_status_snapshot(output: Path, status: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(status, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--git-status-output", type=Path)
    parser.add_argument(
        "--include",
        action="append",
        type=Path,
        required=True,
        dest="include_paths",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    tracked_paths, status_by_path = git_metadata(root)
    rows = inventory_paths(
        root=root,
        include_paths=args.include_paths,
        tracked_paths=tracked_paths,
        status_by_path=status_by_path,
    )
    write_manifest(args.output, rows)
    if args.git_status_output:
        write_status_snapshot(
            args.git_status_output,
            run_git(
                root,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            ),
        )
    print(
        f"Wrote {len(rows)} files "
        f"({sum(int(row['bytes']) for row in rows)} bytes) "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
