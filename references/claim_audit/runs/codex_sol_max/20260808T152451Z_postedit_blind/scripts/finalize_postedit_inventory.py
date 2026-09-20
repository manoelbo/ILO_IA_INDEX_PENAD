#!/usr/bin/env python3
"""Validate, identify, and reconcile the post-edit claim inventory."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = RUN_DIR.parents[4]
CANDIDATE = RUN_DIR / "inventory_extraction_candidate.tsv"
OCCURRENCES = RUN_DIR / "citation_occurrences_postedit.tsv"
SOURCE_MANIFEST = RUN_DIR / "source_manifest.tsv"
INVENTORY = RUN_DIR / "claim_inventory_postedit.tsv"
RECONCILIATION = RUN_DIR / "claim_reconciliation.tsv"
RUN_MANIFEST = RUN_DIR / "run_manifest.json"
PRIOR_AUDIT = (
    PROJECT_DIR
    / "references/claim_audit/runs/codex_sol_max/20260807T141925Z_current"
    / "claim_inventory_audited_current.tsv"
)

INVENTORY_COLUMNS = [
    "claim_id", "occurrence_id", "section", "paragraph", "citation_key",
    "work", "claim_type", "affirmation_pt", "source_excerpt",
    "fact_checked", "pages", "row_id",
]

RECONCILIATION_COLUMNS = [
    "current_row_id", "current_claim_id", "current_occurrence_id", "citation_key",
    "prior_row_id", "prior_claim_id", "prior_occurrence_id",
    "reconciliation_status", "matching_basis", "current_source_sha256",
    "prior_source_sha256", "claim_text_sha256", "source_excerpt_sha256",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", value).strip()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def numeric_id(value: str) -> int:
    return int(value.rsplit("-", 1)[-1])


def main() -> None:
    candidate = read_tsv(CANDIDATE)
    occurrences = read_tsv(OCCURRENCES)
    occurrence_by_id = {row["occurrence_id"]: row for row in occurrences}
    source_rows = read_tsv(SOURCE_MANIFEST)
    source_hashes = {row["citation_key"]: row["source_sha256"] for row in source_rows}

    expected_candidate_columns = [
        "occurrence_id", "context_id", "document_line", "section", "paragraph",
        "citation_key", "work", "claim_type", "affirmation_pt", "source_excerpt",
        "extraction_note",
    ]
    if not candidate or list(candidate[0]) != expected_candidate_columns:
        raise SystemExit("Candidate TSV does not have the expected interface")
    if len(candidate) != 207:
        raise SystemExit(f"Expected 207 candidate rows, found {len(candidate)}")
    if len(occurrence_by_id) != 61:
        raise SystemExit("Expected 61 unique formal citation occurrences")

    seen_pairs: set[tuple[str, str]] = set()
    for row in candidate:
        occurrence = occurrence_by_id.get(row["occurrence_id"])
        if not occurrence:
            raise SystemExit(f"Unknown occurrence in candidate: {row['occurrence_id']}")
        for field in (
            "context_id", "document_line", "section", "paragraph", "citation_key", "work"
        ):
            if row[field] != occurrence[field]:
                raise SystemExit(f"Metadata mismatch for {row['occurrence_id']}: {field}")
        expected_excerpt = occurrence["source_context"].replace("\r", " ").replace("\n", " ")
        if row["source_excerpt"] != expected_excerpt:
            raise SystemExit(f"Source excerpt mismatch for {row['occurrence_id']}")
        if row["claim_type"] not in {"DIRECT", "AUTHOR_INFERENCE"}:
            raise SystemExit(f"Invalid claim type for {row['occurrence_id']}")
        pair = (row["occurrence_id"], normalize(row["affirmation_pt"]).casefold())
        if pair in seen_pairs:
            raise SystemExit(f"Duplicate occurrence/claim pair: {row['occurrence_id']}")
        seen_pairs.add(pair)

    if set(occurrence_by_id) != {row["occurrence_id"] for row in candidate}:
        raise SystemExit("Not every current occurrence has at least one claim")
    if {row["citation_key"] for row in candidate} != set(source_hashes):
        raise SystemExit("Claim inventory keys do not match the 22-source manifest")

    calibration = [
        (row["claim_type"], row["affirmation_pt"])
        for row in candidate if row["occurrence_id"] == "CIT-REV-001"
    ]
    expected_calibration = [
        ("DIRECT", "Estima-se que 32,1% dos trabalhadores dos Estados Unidos já integravam ferramentas de IA às suas rotinas até o final de 2024."),
        ("DIRECT", "O ritmo de adoção de ferramentas de IA nos Estados Unidos era comparável ao do computador pessoal na década de 1980."),
        ("DIRECT", "A difusão das ferramentas de IA nos Estados Unidos era superior, em termos populacionais, à da internet."),
        ("AUTHOR_INFERENCE", "A combinação do alcance ocupacional com a velocidade de difusão justifica tratar essa geração de inteligência artificial como um problema econômico, e não apenas tecnológico."),
    ]
    if calibration != expected_calibration:
        raise SystemExit("Bick calibration claims do not match the approved contract")

    claim_ids: dict[tuple[str, str, str], str] = {}
    inventory_rows: list[dict[str, str]] = []
    for row_number, row in enumerate(candidate, 1):
        group_key = (
            row["context_id"],
            normalize(row["affirmation_pt"]).casefold(),
            row["claim_type"],
        )
        if group_key not in claim_ids:
            claim_ids[group_key] = f"CLM-REV-{len(claim_ids) + 1:03d}"
        inventory_rows.append({
            "claim_id": claim_ids[group_key],
            "occurrence_id": row["occurrence_id"],
            "section": row["section"],
            "paragraph": row["paragraph"],
            "citation_key": row["citation_key"],
            "work": row["work"],
            "claim_type": row["claim_type"],
            "affirmation_pt": row["affirmation_pt"],
            "source_excerpt": row["source_excerpt"],
            "fact_checked": "",
            "pages": "",
            "row_id": f"ROW-REV-{row_number:04d}",
        })

    triples = [
        (row["claim_id"], row["citation_key"], row["occurrence_id"])
        for row in inventory_rows
    ]
    if len(triples) != len(set(triples)):
        raise SystemExit("Duplicate (claim_id, citation_key, occurrence_id) triple")

    prior_rows = read_tsv(PRIOR_AUDIT)
    prior_candidates: defaultdict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in prior_rows:
        key = (
            row["citation_key"], row["claim_type"],
            normalize(row["affirmation_pt"]).casefold(),
        )
        prior_candidates[key].append(row)
    for values in prior_candidates.values():
        values.sort(key=lambda item: numeric_id(item["row_id"]))

    used_prior: set[str] = set()
    reconciliation_rows: list[dict[str, str]] = []
    for current in inventory_rows:
        key = (
            current["citation_key"], current["claim_type"],
            normalize(current["affirmation_pt"]).casefold(),
        )
        candidates = [row for row in prior_candidates[key] if row["row_id"] not in used_prior]
        exact_excerpt = [
            row for row in candidates
            if normalize(row["source_excerpt"]) == normalize(current["source_excerpt"])
        ]
        prior = (exact_excerpt or candidates or [None])[0]
        current_sha = source_hashes[current["citation_key"]]
        if prior:
            used_prior.add(prior["row_id"])
            prior_sha = prior.get("source_sha256", "")
            text_exact = normalize(prior["source_excerpt"]) == normalize(current["source_excerpt"])
            source_exact = prior_sha == current_sha
            if text_exact and source_exact:
                status = "REUSED_EXACT_AS_PRIMARY_A"
                basis = "EXACT_KEY_TYPE_CLAIM_EXCERPT_AND_SOURCE_HASH"
            elif text_exact:
                status = "REAUDIT_REQUIRED_SOURCE_CHANGED"
                basis = "EXACT_KEY_TYPE_CLAIM_EXCERPT_SOURCE_HASH_CHANGED"
            elif source_exact:
                status = "REAUDIT_REQUIRED_TEXT_CHANGED"
                basis = "EXACT_KEY_TYPE_CLAIM_SOURCE_HASH_EXCERPT_CHANGED"
            else:
                status = "REAUDIT_REQUIRED_TEXT_AND_SOURCE_CHANGED"
                basis = "EXACT_KEY_TYPE_CLAIM_ONLY"
        else:
            prior_sha = ""
            status = "AUDITED_NEW_OR_REWRITTEN"
            basis = "NO_EXACT_PRIOR_CLAIM_MATCH"

        reconciliation_rows.append({
            "current_row_id": current["row_id"],
            "current_claim_id": current["claim_id"],
            "current_occurrence_id": current["occurrence_id"],
            "citation_key": current["citation_key"],
            "prior_row_id": prior["row_id"] if prior else "",
            "prior_claim_id": prior["claim_id"] if prior else "",
            "prior_occurrence_id": prior["occurrence_id"] if prior else "",
            "reconciliation_status": status,
            "matching_basis": basis,
            "current_source_sha256": current_sha,
            "prior_source_sha256": prior_sha,
            "claim_text_sha256": digest(normalize(current["affirmation_pt"])),
            "source_excerpt_sha256": digest(normalize(current["source_excerpt"])),
        })

    for prior in prior_rows:
        if prior["row_id"] in used_prior:
            continue
        reconciliation_rows.append({
            "current_row_id": "",
            "current_claim_id": "",
            "current_occurrence_id": "",
            "citation_key": prior["citation_key"],
            "prior_row_id": prior["row_id"],
            "prior_claim_id": prior["claim_id"],
            "prior_occurrence_id": prior["occurrence_id"],
            "reconciliation_status": "REMOVED_AFTER_PRIMARY_EDIT",
            "matching_basis": "NO_CURRENT_EXACT_CLAIM_MATCH",
            "current_source_sha256": source_hashes.get(prior["citation_key"], ""),
            "prior_source_sha256": prior.get("source_sha256", ""),
            "claim_text_sha256": digest(normalize(prior["affirmation_pt"])),
            "source_excerpt_sha256": digest(normalize(prior["source_excerpt"])),
        })

    write_tsv(INVENTORY, INVENTORY_COLUMNS, inventory_rows)
    write_tsv(RECONCILIATION, RECONCILIATION_COLUMNS, reconciliation_rows)

    statuses = Counter(row["reconciliation_status"] for row in reconciliation_rows)
    extraction_receipt = {
        "schema_version": "postedit-inventory-extraction-receipt-v1",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "max",
        "session_id": "019fe209-d18a-72f0-9245-b4afff9f0b85",
        "tokens_used_reported_by_runtime": 152925,
        "prompt_path": "inventory_extraction_prompt.md",
        "candidate_path": "inventory_extraction_candidate.tsv",
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "candidate_rows": len(candidate),
        "unique_claims": len(claim_ids),
        "occurrences": len(occurrence_by_id),
        "citation_keys": len(source_hashes),
        "no_verifiable_proposition_occurrences": [],
        "validated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    (RUN_DIR / "runtime/inventory_extraction_receipt.json").write_text(
        json.dumps(extraction_receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    preflight = {
        "schema_version": "runtime-preflight-v1",
        "required_response": "RUNTIME_OK gpt-5.6-sol max",
        "observed_response": (RUN_DIR / "runtime/preflight.txt").read_text(encoding="utf-8").strip(),
        "model": "gpt-5.6-sol",
        "reasoning_effort": "max",
        "fallback_allowed": False,
        "session_id": "019fe209-03be-7b83-9f00-ce603a11dd87",
    }
    preflight["passed"] = preflight["observed_response"] == preflight["required_response"]
    if not preflight["passed"]:
        raise SystemExit("Exact-model runtime preflight did not pass")
    (RUN_DIR / "runtime/preflight.json").write_text(
        json.dumps(preflight, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    run_manifest = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
    run_manifest.update({
        "status": "SOURCE_GATE_BLOCKED_INVENTORY_READY",
        "runtime_preflight_passed": True,
        "inventory_rows": len(inventory_rows),
        "inventory_claims": len(claim_ids),
        "inventory_occurrences": len(occurrence_by_id),
        "inventory_citation_keys": len(source_hashes),
        "reconciliation": dict(sorted(statuses.items())),
        "blind_review_started": False,
        "blind_review_blocker": (
            "humlum_still_2025 has a current-source title/year conflict with the frozen Notion reference."
        ),
        "bick_source_packet_ready": True,
        "bick_source_packet_splits": 14,
        "bick_blind_judgments_started": False,
    })
    RUN_MANIFEST.write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "inventory_rows": len(inventory_rows),
        "unique_claims": len(claim_ids),
        "occurrences": len(occurrence_by_id),
        "citation_keys": len(source_hashes),
        "reconciliation": dict(sorted(statuses.items())),
        "source_gate_blocked": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
