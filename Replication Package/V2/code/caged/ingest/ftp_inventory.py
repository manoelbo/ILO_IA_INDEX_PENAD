#!/usr/bin/env python3
"""Freeze the fixed January 2021–May 2026 Novo CAGED FTP inventory."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from ftplib import FTP, error_perm
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import quote


HOST = "ftp.mtps.gov.br"
REMOTE_ROOT = "/pdet/microdados/NOVO CAGED"
ARCHIVE_TYPES = ("MOV", "FOR", "EXC")
FIRST_COMPETENCY = "202101"
LAST_COMPETENCY = "202605"
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = PACKAGE_ROOT / "data" / "vintage" / "ftp_inventory.csv"
FIELDNAMES = (
    "competencia",
    "tipo",
    "url",
    "bytes",
    "data_modificacao_ftp",
)


def fixed_competencies() -> list[str]:
    """Return the preregistered continuous competency window."""
    competencies: list[str] = []
    year, month = 2021, 1
    while (year, month) <= (2026, 5):
        competencies.append(f"{year:04d}{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return competencies


def expected_filename(competencia: str, archive_type: str) -> str:
    return f"CAGED{archive_type}{competencia}.7z"


def archive_url(competencia: str, filename: str) -> str:
    path = "/".join(
        (
            "pdet",
            "microdados",
            quote("NOVO CAGED"),
            competencia[:4],
            competencia,
            filename,
        )
    )
    return f"ftp://{HOST}/{path}"


def format_ftp_timestamp(raw_timestamp: str) -> str:
    timestamp = datetime.strptime(raw_timestamp, "%Y%m%d%H%M%S").replace(
        tzinfo=timezone.utc
    )
    return timestamp.isoformat().replace("+00:00", "Z")


def _directory_facts(ftp: FTP, remote_directory: str) -> dict[str, dict[str, str]]:
    ftp.cwd(remote_directory)
    try:
        return {
            name: facts
            for name, facts in ftp.mlsd()
            if facts.get("type") == "file"
        }
    except error_perm:
        facts_by_name: dict[str, dict[str, str]] = {}
        ftp.voidcmd("TYPE I")
        for name in ftp.nlst():
            size = ftp.size(name)
            modified = ftp.sendcmd(f"MDTM {name}")
            facts_by_name[name] = {
                "type": "file",
                "size": str(size),
                "modify": modified.removeprefix("213 ").strip(),
            }
        return facts_by_name


def collect_inventory(*, timeout: float = 30.0) -> list[dict[str, object]]:
    """Read metadata only for the fixed, approved archive set."""
    records: list[dict[str, object]] = []
    with FTP(HOST, timeout=timeout) as ftp:
        ftp.login()
        for competencia in fixed_competencies():
            remote_directory = (
                f"{REMOTE_ROOT}/{competencia[:4]}/{competencia}"
            )
            facts_by_name = _directory_facts(ftp, remote_directory)
            for archive_type in ARCHIVE_TYPES:
                filename = expected_filename(competencia, archive_type)
                if filename not in facts_by_name:
                    raise RuntimeError(
                        f"Missing required FTP archive: {remote_directory}/{filename}"
                    )
                facts = facts_by_name[filename]
                size = int(facts.get("size", "0"))
                modified = facts.get("modify", "")
                if size <= 0 or not modified:
                    raise RuntimeError(
                        f"Incomplete FTP metadata for {remote_directory}/{filename}"
                    )
                records.append(
                    {
                        "competencia": competencia,
                        "tipo": archive_type,
                        "url": archive_url(competencia, filename),
                        "bytes": size,
                        "data_modificacao_ftp": format_ftp_timestamp(modified),
                    }
                )
    validate_inventory(records)
    return records


def validate_inventory(records: Iterable[dict[str, object]]) -> None:
    """Fail fast unless records match the preregistered 195-file contract."""
    materialized = list(records)
    if len(materialized) != 195:
        raise ValueError(
            f"Inventory must contain exactly 195 records; found {len(materialized)}"
        )

    expected_competencies = fixed_competencies()
    observed_competencies = sorted(
        {str(record["competencia"]) for record in materialized}
    )
    if observed_competencies != expected_competencies:
        raise ValueError(
            "Inventory competencies must be continuous from "
            f"{FIRST_COMPETENCY} through {LAST_COMPETENCY}"
        )

    for competencia in expected_competencies:
        month_records = [
            record
            for record in materialized
            if str(record["competencia"]) == competencia
        ]
        observed_types = sorted(str(record["tipo"]) for record in month_records)
        if observed_types != sorted(ARCHIVE_TYPES):
            raise ValueError(
                f"{competencia} must contain exactly MOV, FOR, and EXC"
            )
        for record in month_records:
            archive_type = str(record["tipo"])
            filename = expected_filename(competencia, archive_type)
            if not str(record["url"]).endswith(f"/{filename}"):
                raise ValueError(
                    f"Unexpected filename for {competencia} {archive_type}"
                )
            if int(record["bytes"]) <= 0:
                raise ValueError(
                    f"Archive size must be positive for {competencia} {archive_type}"
                )
            if not str(record["data_modificacao_ftp"]).endswith("Z"):
                raise ValueError(
                    "FTP modification timestamp must be normalized to UTC"
                )


def write_inventory(
    records: Sequence[dict[str, object]],
    output_path: Path = DEFAULT_OUTPUT,
) -> None:
    validate_inventory(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=FIELDNAMES,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze the fixed Novo CAGED FTP inventory through May 2026."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Inventory CSV destination.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="FTP socket timeout in seconds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = collect_inventory(timeout=args.timeout)
    write_inventory(records, args.output)
    print(
        f"Wrote {len(records)} archives across "
        f"{len(fixed_competencies())} competencies to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
