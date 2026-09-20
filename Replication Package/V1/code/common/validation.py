"""Machine- and human-readable replication checks."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    status: str
    observed: object
    expected: object
    detail: str


def check_equal(
    check_id: str,
    observed: object,
    expected: object,
    detail: str,
) -> ValidationCheck:
    return ValidationCheck(
        check_id=check_id,
        status="PASS" if observed == expected else "FAIL",
        observed=observed,
        expected=expected,
        detail=detail,
    )


def write_validation_reports(
    checks: Iterable[ValidationCheck],
    output_dir: Path,
    *,
    title: str,
) -> tuple[Path, Path]:
    rows = list(checks)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "validation_checks.csv"
    md_path = output_dir / "validation_checks.md"

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["check_id", "status", "observed", "expected", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            record = asdict(row)
            record["observed"] = _display(record["observed"])
            record["expected"] = _display(record["expected"])
            writer.writerow(record)

    lines = [
        f"# {title}",
        "",
        "| Check | Status | Observed | Expected | Detail |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(row.check_id),
                    _escape(row.status),
                    _escape(_display(row.observed)),
                    _escape(_display(row.expected)),
                    _escape(row.detail),
                ]
            )
            + " |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def _display(value: object) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        normalized = sorted(value) if isinstance(value, set) else value
        return json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            default=_json_default,
        )
    return str(value)


def _json_default(value: object) -> object:
    """Convert NumPy-style scalars without coupling this module to NumPy."""
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
