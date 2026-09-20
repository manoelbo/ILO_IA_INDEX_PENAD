#!/usr/bin/env python3
"""Prepare the current claim-audit reconciliation and primary queue.

This script is deliberately deterministic. It reuses a prior primary judgment only
when citation key, claim type, normalized claim text, normalized dissertation excerpt,
and source hash are all identical. Evidence is copied into the current run so the new
run never depends on mutable paths in a historical run.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = RUN_DIR.parents[4]
PRIOR_RUN = PROJECT_DIR / "references/claim_audit/runs/codex_sol_max/20260801T155350Z"
CURRENT_INVENTORY = RUN_DIR / "claim_inventory_current.tsv"
PRIOR_AUDIT = PRIOR_RUN / "claim_inventory_audited.tsv"
PDF_MANIFEST = PROJECT_DIR / "references/pdf_manifest.tsv"
DELTA_PATH = RUN_DIR / "claim_inventory_delta.tsv"
AUDIT_PATH = RUN_DIR / "claim_inventory_audited_current.tsv"
QUEUE_PATH = RUN_DIR / "queue.tsv"
EVIDENCE_DIR = RUN_DIR / "evidence_pages"
RESULTS_DIR = RUN_DIR / "results"

CALIBRATION_VERSION = "balanced-v1.0-2026-08-07"
SOURCE_SNAPSHOT_ID = "notion-325cc8ca-4610-82d7-94db-01323b295bb5-20260805T235800Z"
FORCED_SOURCE_CHANGES = {"brynjolfsson_canaries_2025", "humlum_still_2025"}

OLD_COLUMNS = [
    "claim_id", "occurrence_id", "section", "paragraph", "citation_key", "work",
    "claim_type", "affirmation_pt", "source_excerpt", "fact_checked", "pages",
    "row_id", "audit_status", "source_version", "source_sha256", "printed_pages",
    "pdf_page_indices", "source_locator", "evidence_summary_pt", "evidence_anchor",
    "evidence_path", "search_coverage", "confidence", "issue_codes",
    "issue_severity", "issue_detail_pt", "recommended_revision_pt",
    "needs_new_source", "auditor_model", "audited_at",
]

ADDITIONAL_COLUMNS = [
    "prior_claim_id", "prior_occurrence_id", "prior_row_id", "reconciliation_status",
    "audit_origin", "calibration_rule_version", "source_snapshot_id",
    "claim_text_sha256",
]

DELTA_COLUMNS = [
    "row_id", "claim_id", "occurrence_id", "citation_key", "prior_row_id",
    "prior_claim_id", "prior_occurrence_id", "reconciliation_status",
    "matching_basis", "current_source_sha256", "prior_source_sha256",
    "claim_text_sha256",
]

QUEUE_COLUMNS = [
    "row_id", "claim_id", "occurrence_id", "citation_key", "work", "claim_type",
    "affirmation_pt", "source_excerpt", "section", "paragraph",
    "reconciliation_status", "prior_row_id", "current_source_sha256", "source_path",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def claim_hash(row: dict[str, str]) -> str:
    payload = "\n".join(
        normalize_text(row.get(field, ""))
        for field in ("citation_key", "claim_type", "affirmation_pt", "source_excerpt")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evidence_destination(row_id: str, prior_path: str) -> Path:
    suffix = Path(prior_path).suffix or ".bin"
    return EVIDENCE_DIR / f"{row_id}{suffix}"


def load_current_hashes() -> dict[str, str]:
    rows = read_tsv(PDF_MANIFEST)
    return {row["citation_key"]: row["sha256"] for row in rows if row.get("sha256")}


def choose_prior(
    current: dict[str, str],
    candidates: list[dict[str, str]],
    used_prior_ids: set[str],
) -> tuple[dict[str, str] | None, str]:
    available = [row for row in candidates if row["row_id"] not in used_prior_ids]
    if not available:
        return None, "NONE"

    current_claim = normalize_text(current["affirmation_pt"])
    current_excerpt = normalize_text(current["source_excerpt"])

    exact = [
        row for row in available
        if normalize_text(row["affirmation_pt"]) == current_claim
        and normalize_text(row["source_excerpt"]) == current_excerpt
    ]
    if exact:
        same_location = [
            row for row in exact
            if normalize_text(row["section"]) == normalize_text(current["section"])
            and normalize_text(row["paragraph"]) == normalize_text(current["paragraph"])
        ]
        return (same_location or exact)[0], "EXACT_CLAIM_AND_EXCERPT"

    same_claim = [row for row in available if normalize_text(row["affirmation_pt"]) == current_claim]
    if same_claim:
        return same_claim[0], "EXACT_CLAIM_TEXT_CHANGED_EXCERPT"

    same_excerpt = [row for row in available if normalize_text(row["source_excerpt"]) == current_excerpt]
    if same_excerpt:
        return same_excerpt[0], "EXACT_EXCERPT_TEXT_CHANGED_CLAIM"

    return None, "NONE"


def main() -> None:
    current_rows = read_tsv(CURRENT_INVENTORY)
    prior_rows = read_tsv(PRIOR_AUDIT)
    current_hashes = load_current_hashes()

    if list(prior_rows[0]) != OLD_COLUMNS:
        raise SystemExit("Prior audited TSV does not have the expected 30-column interface")

    prior_by_key_type: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in prior_rows:
        prior_by_key_type[(row["citation_key"], row["claim_type"])].append(row)

    for rows in prior_by_key_type.values():
        rows.sort(key=lambda row: int(row["row_id"].split("-")[-1]))

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    used_prior_ids: set[str] = set()
    delta_rows: list[dict[str, str]] = []
    audit_rows: list[dict[str, str]] = []
    queue_rows: list[dict[str, str]] = []

    for current in current_rows:
        candidates = prior_by_key_type[(current["citation_key"], current["claim_type"])]
        prior, matching_basis = choose_prior(current, candidates, used_prior_ids)
        if prior:
            used_prior_ids.add(prior["row_id"])

        current_sha = current_hashes.get(current["citation_key"], "")
        if not current_sha and prior:
            # The only expected no-PDF source is the legal HTML source. Its immutable
            # prior snapshot remains authoritative unless the citation text changes.
            current_sha = prior["source_sha256"]

        prior_sha = prior["source_sha256"] if prior else ""
        source_changed = (
            current["citation_key"] in FORCED_SOURCE_CHANGES
            or not prior
            or not current_sha
            or current_sha != prior_sha
        )
        text_exact = matching_basis == "EXACT_CLAIM_AND_EXCERPT"

        if not prior:
            reconciliation_status = "AUDITED_NEW"
        elif text_exact and not source_changed:
            reconciliation_status = "REUSED_EXACT"
        elif text_exact and source_changed:
            reconciliation_status = "REAUDITED_SOURCE_CHANGED"
        elif source_changed:
            reconciliation_status = "REAUDITED_TEXT_AND_SOURCE_CHANGED"
        else:
            reconciliation_status = "REAUDITED_TEXT_CHANGED"

        row_hash = claim_hash(current)
        delta = {
            "row_id": current["row_id"],
            "claim_id": current["claim_id"],
            "occurrence_id": current["occurrence_id"],
            "citation_key": current["citation_key"],
            "prior_row_id": prior["row_id"] if prior else "",
            "prior_claim_id": prior["claim_id"] if prior else "",
            "prior_occurrence_id": prior["occurrence_id"] if prior else "",
            "reconciliation_status": reconciliation_status,
            "matching_basis": matching_basis,
            "current_source_sha256": current_sha,
            "prior_source_sha256": prior_sha,
            "claim_text_sha256": row_hash,
        }
        delta_rows.append(delta)

        audit = {column: "" for column in OLD_COLUMNS + ADDITIONAL_COLUMNS}
        for field in (
            "claim_id", "occurrence_id", "section", "paragraph", "citation_key", "work",
            "claim_type", "affirmation_pt", "source_excerpt", "row_id",
        ):
            audit[field] = current[field]

        if reconciliation_status == "REUSED_EXACT":
            for field in OLD_COLUMNS[9:]:
                if field != "row_id":
                    audit[field] = prior[field]
            audit["audit_status"] = "COMPLETED"
            audit["source_sha256"] = current_sha
            audit["audit_origin"] = "REUSED_PRIOR_PRIMARY"

            prior_evidence = PRIOR_RUN / prior["evidence_path"]
            if not prior_evidence.is_file():
                raise SystemExit(f"Missing prior evidence for {prior['row_id']}: {prior_evidence}")
            destination = evidence_destination(current["row_id"], prior["evidence_path"])
            shutil.copy2(prior_evidence, destination)
            audit["evidence_path"] = destination.relative_to(RUN_DIR).as_posix()

            result_receipt = {
                "row_id": current["row_id"],
                "audit_origin": "REUSED_PRIOR_PRIMARY",
                "prior_row_id": prior["row_id"],
                "source_sha256": current_sha,
                "claim_text_sha256": row_hash,
                "evidence_path": audit["evidence_path"],
                "evidence_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "fact_checked": audit["fact_checked"],
                "pages": audit["pages"],
            }
            (RESULTS_DIR / f"{current['row_id']}.json").write_text(
                json.dumps(result_receipt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            audit["audit_status"] = "PENDING"
            audit["source_sha256"] = current_sha
            audit["audit_origin"] = "PENDING_PRIMARY"
            source_path = (
                f"references/pdfs/{current['citation_key']}.pdf"
                if current["citation_key"] in current_hashes
                else ""
            )
            queue_rows.append({
                **{field: current[field] for field in (
                    "row_id", "claim_id", "occurrence_id", "citation_key", "work",
                    "claim_type", "affirmation_pt", "source_excerpt", "section", "paragraph",
                )},
                "reconciliation_status": reconciliation_status,
                "prior_row_id": prior["row_id"] if prior else "",
                "current_source_sha256": current_sha,
                "source_path": source_path,
            })

        audit["prior_claim_id"] = prior["claim_id"] if prior else ""
        audit["prior_occurrence_id"] = prior["occurrence_id"] if prior else ""
        audit["prior_row_id"] = prior["row_id"] if prior else ""
        audit["reconciliation_status"] = reconciliation_status
        audit["calibration_rule_version"] = CALIBRATION_VERSION
        audit["source_snapshot_id"] = SOURCE_SNAPSHOT_ID
        audit["claim_text_sha256"] = row_hash
        audit_rows.append(audit)

    triples = [(row["claim_id"], row["citation_key"], row["occurrence_id"]) for row in audit_rows]
    if len(triples) != len(set(triples)):
        raise SystemExit("Duplicate (claim_id, citation_key, occurrence_id) triples")

    write_tsv(DELTA_PATH, DELTA_COLUMNS, delta_rows)
    write_tsv(AUDIT_PATH, OLD_COLUMNS + ADDITIONAL_COLUMNS, audit_rows)
    write_tsv(QUEUE_PATH, QUEUE_COLUMNS, queue_rows)

    counts: dict[str, int] = defaultdict(int)
    for row in delta_rows:
        counts[row["reconciliation_status"]] += 1
    print(json.dumps({
        "current_rows": len(current_rows),
        "prior_rows": len(prior_rows),
        "primary_queue": len(queue_rows),
        "reconciliation": dict(sorted(counts.items())),
        "reused_evidence": len(list(EVIDENCE_DIR.iterdir())),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
