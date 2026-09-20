#!/usr/bin/env python3
"""Download the frozen Novo CAGED vintage with resume and SHA-256 checks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from ftplib import FTP
from pathlib import Path
from typing import Callable, Iterable, Sequence
from urllib.parse import unquote, urlparse


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INVENTORY = PACKAGE_ROOT / "data" / "vintage" / "ftp_inventory.csv"
DEFAULT_DATA_DIR = PACKAGE_ROOT / "data" / "vintage"
DEFAULT_MANIFEST = DEFAULT_DATA_DIR / "manifest.json"
TransferFunction = Callable[[str, Path, int, float], None]


def archive_manifest_count(
    manifest: dict[str, dict[str, object]],
) -> int:
    """Count only Novo CAGED archives in the extensible vintage manifest."""
    return sum(
        Path(relative_path).name.endswith(".7z")
        for relative_path in manifest
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def archive_filename(record: dict[str, object]) -> str:
    filename = Path(urlparse(str(record["url"])).path).name
    if not filename.endswith(".7z"):
        raise ValueError(f"Inventory URL does not name a .7z archive: {record['url']}")
    return filename


def ftp_transfer(
    url: str,
    part_path: Path,
    offset: int,
    timeout: float,
) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "ftp" or not parsed.hostname:
        raise ValueError(f"Expected an FTP URL, found: {url}")
    remote_path = unquote(parsed.path)
    with FTP(parsed.hostname, timeout=timeout) as ftp:
        ftp.login()
        ftp.voidcmd("TYPE I")
        with part_path.open("ab") as handle:
            ftp.retrbinary(
                f"RETR {remote_path}",
                handle.write,
                blocksize=1024 * 1024,
                rest=offset or None,
            )


def download_archive(
    record: dict[str, object],
    data_dir: Path,
    *,
    transfer: TransferFunction = ftp_transfer,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    timeout: float = 60.0,
) -> dict[str, object]:
    """Download one archive and return its immutable manifest entry."""
    data_dir.mkdir(parents=True, exist_ok=True)
    filename = archive_filename(record)
    final_path = data_dir / filename
    part_path = data_dir / f"{filename}.part"
    expected_bytes = int(record["bytes"])

    if final_path.exists():
        if final_path.stat().st_size != expected_bytes:
            raise RuntimeError(
                f"Existing final archive has wrong size: {final_path}"
            )
        downloaded_at = datetime.fromtimestamp(
            final_path.stat().st_mtime,
            tz=timezone.utc,
        )
        return manifest_entry(record, final_path, downloaded_at)

    for attempt in range(3):
        offset = part_path.stat().st_size if part_path.exists() else 0
        if offset > expected_bytes:
            part_path.unlink()
            offset = 0
        try:
            transfer(str(record["url"]), part_path, offset, timeout)
            observed_bytes = part_path.stat().st_size
            if observed_bytes != expected_bytes:
                raise OSError(
                    f"incomplete archive: expected {expected_bytes} bytes, "
                    f"found {observed_bytes}"
                )
            os.replace(part_path, final_path)
            return manifest_entry(record, final_path, now())
        except Exception:
            if attempt == 2:
                raise
            sleep(float(2**attempt))

    raise AssertionError("unreachable")


def manifest_entry(
    record: dict[str, object],
    final_path: Path,
    downloaded_at: datetime,
) -> dict[str, object]:
    return {
        "url": str(record["url"]),
        "bytes": int(record["bytes"]),
        "sha256": sha256_file(final_path),
        "data_modificacao_ftp": str(record["data_modificacao_ftp"]),
        "baixado_em": utc_iso(downloaded_at),
    }


def read_manifest(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Download manifest must be a JSON object")
    return payload


def write_manifest(
    manifest: dict[str, dict[str, object]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def _manifest_metadata_matches(
    entry: dict[str, object] | None,
    record: dict[str, object],
) -> bool:
    if not entry:
        return False
    return (
        entry.get("url") == str(record["url"])
        and entry.get("bytes") == int(record["bytes"])
        and entry.get("data_modificacao_ftp")
        == str(record["data_modificacao_ftp"])
        and isinstance(entry.get("sha256"), str)
        and len(str(entry["sha256"])) == 64
        and isinstance(entry.get("baixado_em"), str)
    )


def download_inventory(
    records: Sequence[dict[str, object]],
    data_dir: Path,
    manifest_path: Path,
    *,
    transfer: TransferFunction = ftp_transfer,
    timeout: float = 60.0,
) -> dict[str, dict[str, object]]:
    manifest = read_manifest(manifest_path)
    changed = False
    for index, record in enumerate(records, start=1):
        filename = archive_filename(record)
        final_path = data_dir / filename
        entry = manifest.get(filename)
        if (
            final_path.is_file()
            and final_path.stat().st_size == int(record["bytes"])
            and _manifest_metadata_matches(entry, record)
        ):
            print(f"[{index}/{len(records)}] skip {filename}")
            continue

        print(f"[{index}/{len(records)}] download {filename}")
        new_entry = download_archive(
            record,
            data_dir,
            transfer=transfer,
            timeout=timeout,
        )
        manifest[filename] = new_entry
        changed = True
        write_manifest(manifest, manifest_path)

    if changed is False and not manifest_path.exists():
        write_manifest(manifest, manifest_path)
    return manifest


def verify_inventory(
    records: Iterable[dict[str, object]],
    data_dir: Path,
    manifest: dict[str, dict[str, object]],
) -> list[str]:
    divergences: list[str] = []
    for record in records:
        filename = archive_filename(record)
        final_path = data_dir / filename
        entry = manifest.get(filename)
        if not final_path.is_file():
            divergences.append(f"{filename}: missing")
            continue
        if final_path.stat().st_size != int(record["bytes"]):
            divergences.append(f"{filename}: size mismatch")
            continue
        if not _manifest_metadata_matches(entry, record):
            divergences.append(f"{filename}: manifest metadata mismatch")
            continue
        if sha256_file(final_path) != entry["sha256"]:
            divergences.append(f"{filename}: sha256 mismatch")
    for part_path in sorted(data_dir.glob("*.part")):
        divergences.append(f"{part_path.name}: unfinished partial download")
    return divergences


def read_inventory(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    for record in records:
        record["bytes"] = int(record["bytes"])
    if len(records) != 195:
        raise ValueError(
            f"Inventory must contain exactly 195 records; found {len(records)}"
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and verify the frozen Novo CAGED vintage."
    )
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Hash every archive and report divergences without downloading.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = read_inventory(args.inventory)
    if args.verify_only:
        divergences = verify_inventory(
            records,
            args.data_dir,
            read_manifest(args.manifest),
        )
        for divergence in divergences:
            print(divergence)
        print(f"{len(divergences)} divergences")
        return 1 if divergences else 0

    manifest = download_inventory(
        records,
        args.data_dir,
        args.manifest,
        timeout=args.timeout,
    )
    archive_count = archive_manifest_count(manifest)
    if archive_count != len(records):
        raise RuntimeError(
            f"Manifest has {archive_count} archive entries; "
            f"expected {len(records)}"
        )
    unfinished = list(args.data_dir.glob("*.part"))
    if unfinished:
        raise RuntimeError(f"Unfinished partial downloads: {unfinished}")
    print(f"Downloaded and recorded {archive_count} archives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
