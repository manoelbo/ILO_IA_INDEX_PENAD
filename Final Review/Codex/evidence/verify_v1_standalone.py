#!/usr/bin/env python3
"""Verify that frozen V1 reproduces from a temporary external copy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_FIELDS = ["relative_path", "bytes", "sha256"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_output_rows(output_dir: Path) -> list[dict[str, object]]:
    """Return a deterministic byte inventory for reproduced outputs."""
    return [
        {
            "relative_path": path.relative_to(output_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(candidate for candidate in output_dir.rglob("*") if candidate.is_file())
    ]


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-files", type=int, default=116)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    log_path = args.log.resolve()
    manifest_path = args.manifest.resolve()
    runner = source / "run_replication.py"
    if not runner.is_file():
        raise SystemExit(f"Missing V1 runner: {runner}")

    started_at = datetime.now(timezone.utc)
    result: subprocess.CompletedProcess[str] | None = None
    command: list[str] = []
    temporary_copy = ""
    rows: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="codex-v1-review-") as temporary:
        temporary_root = Path(temporary)
        copied_source = temporary_root / "V1"
        output_dir = temporary_root / "reproduced"
        shutil.copytree(source, copied_source)
        temporary_copy = copied_source.as_posix()
        command = [
            sys.executable,
            (copied_source / "run_replication.py").as_posix(),
            "--skip-figures",
            "--output-dir",
            output_dir.as_posix(),
        ]
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            command,
            cwd="/tmp",
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        if output_dir.is_dir():
            rows = build_output_rows(output_dir)
        write_manifest(manifest_path, rows)

    assert result is not None
    manifest_digest = sha256_file(manifest_path)
    passed = result.returncode == 0 and len(rows) == args.expected_files
    completed_at = datetime.now(timezone.utc)
    log_lines = [
        "V1 STANDALONE REPRODUCTION",
        f"started_at_utc={started_at.isoformat()}",
        f"completed_at_utc={completed_at.isoformat()}",
        f"source={source.as_posix()}",
        f"temporary_copy={temporary_copy} (deleted after verification)",
        f"cwd=/tmp",
        f"command={shlex.join(command)}",
        f"exit_code={result.returncode}",
        f"expected_output_file_count={args.expected_files}",
        f"actual_output_file_count={len(rows)}",
        f"output_manifest={manifest_path.as_posix()}",
        f"output_manifest_sha256={manifest_digest}",
        f"status={'PASS' if passed else 'FAIL'}",
        "",
        "STDOUT",
        result.stdout.rstrip(),
        "",
        "STDERR",
        result.stderr.rstrip(),
        "",
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(
        f"status={'PASS' if passed else 'FAIL'} "
        f"files={len(rows)} log={log_path}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
