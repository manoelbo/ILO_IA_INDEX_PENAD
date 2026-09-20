#!/usr/bin/env python3
"""Deterministic controller for the Codex Sol Max claim audit run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from PyPDF2 import PdfReader, PdfWriter


RUN_DIR = Path(__file__).resolve().parents[2]
WORKSPACE = RUN_DIR.parents[4]
REFERENCES = WORKSPACE / "references"
INVENTORY_PATH = REFERENCES / "claim_audit" / "claim_inventory.tsv"
INVENTORY_MD_PATH = REFERENCES / "claim_audit" / "CLAIM_INVENTORY.md"
BIB_PATH = REFERENCES / "library.bib"
PDF_MANIFEST_PATH = REFERENCES / "pdf_manifest.tsv"
PDF_DIR = REFERENCES / "pdfs"
PROMPT_PATH = RUN_DIR / "audit_protocol.txt"
SCHEMA_PATH = RUN_DIR / "claim_result.schema.json"
MANIFEST_PATH = RUN_DIR / "run_manifest.json"
QUEUE_PATH = RUN_DIR / "queue.tsv"
AUDITED_PATH = RUN_DIR / "claim_inventory_audited.tsv"
ISSUES_PATH = RUN_DIR / "issues.tsv"
LOG_PATH = RUN_DIR / "audit_log.jsonl"
RESULTS_DIR = RUN_DIR / "results"
SOURCE_BUILD = RUN_DIR / "source_build"
EVIDENCE_DIR = RUN_DIR / "evidence_pages"

MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "max"
RUN_ID = RUN_DIR.name
STARTED_AT = "2026-08-01T15:53:50Z"

ORIGINAL_COLUMNS = [
    "claim_id",
    "occurrence_id",
    "section",
    "paragraph",
    "citation_key",
    "work",
    "claim_type",
    "affirmation_pt",
    "source_excerpt",
    "fact_checked",
    "pages",
]

APPENDED_COLUMNS = [
    "row_id",
    "audit_status",
    "source_version",
    "source_sha256",
    "printed_pages",
    "pdf_page_indices",
    "source_locator",
    "evidence_summary_pt",
    "evidence_anchor",
    "evidence_path",
    "search_coverage",
    "confidence",
    "issue_codes",
    "issue_severity",
    "issue_detail_pt",
    "recommended_revision_pt",
    "needs_new_source",
    "auditor_model",
    "audited_at",
]

QUEUE_EXTRA_COLUMNS = [
    "row_id",
    "queue_status",
    "claim_row_sha256",
    "bibliography_entry_sha256",
    "source_type",
    "source_path",
    "source_sha256",
    "worker_prompt_path",
    "worker_prompt_sha256",
]

ISSUE_COLUMNS = [
    "issue_id",
    "row_id",
    "claim_id",
    "citation_key",
    "occurrence_id",
    "issue_code",
    "severity",
    "claim_as_written_pt",
    "source_supports_pt",
    "mismatch_explanation_pt",
    "printed_pages",
    "pdf_page_indices",
    "source_locator",
    "evidence_path",
    "recommended_revision_pt",
    "needs_new_source",
    "recommended_action",
]

CALIBRATION_TRIPLES = [
    ("CLM-001", "bick_rapid_2024", "CIT-001"),
    ("CLM-002", "bick_rapid_2024", "CIT-001"),
    ("CLM-003", "bick_rapid_2024", "CIT-001"),
    ("CLM-004", "bick_rapid_2024", "CIT-001"),
]


class VisibleHTMLTextExtractor(HTMLParser):
    """Minimal deterministic HTML-to-text extractor for the official legal snapshot."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.hidden_depth += 1
        elif tag.lower() in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1
        elif tag.lower() in {"p", "div", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(data)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def atomic_write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def append_log(event: str, **payload: Any) -> None:
    record = {"timestamp": utc_now(), "event": event, **payload}
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def parse_bib_entries(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    lines = text.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        match = re.match(r"^@(\w+)\s*\{\s*([^,]+)\s*,", lines[index])
        if not match:
            index += 1
            continue
        entry_type, key = match.group(1).lower(), match.group(2).strip()
        parts = [lines[index]]
        depth = lines[index].count("{") - lines[index].count("}")
        index += 1
        while index < len(lines) and depth > 0:
            parts.append(lines[index])
            depth += lines[index].count("{") - lines[index].count("}")
            index += 1
        raw = "".join(parts)
        entries[key] = {"entry_type": entry_type, "raw": raw, "sha256": sha256_bytes(raw.encode("utf-8"))}
    return entries


def authoritative_snapshot() -> list[dict[str, Any]]:
    paths = [INVENTORY_PATH, INVENTORY_MD_PATH, BIB_PATH, PDF_MANIFEST_PATH]
    paths.extend(sorted(path for path in PDF_DIR.iterdir() if path.is_file()))
    result = []
    for path in paths:
        result.append({
            "path": path.relative_to(WORKSPACE).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    return result


def snapshot_digest(snapshot: list[dict[str, Any]]) -> str:
    return canonical_sha([{key: item[key] for key in ("path", "sha256", "bytes")} for item in snapshot])


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    atomic_write_json(MANIFEST_PATH, manifest)


def mark_stale(manifest: dict[str, Any], differences: list[dict[str, Any]], checkpoint: str) -> None:
    manifest["audit_status"] = "STALE_INCOMPLETE"
    manifest["stale_detected_at"] = utc_now()
    manifest["stale_checkpoint"] = checkpoint
    manifest["authoritative_input_differences"] = differences
    save_manifest(manifest)
    append_log("authoritative_inputs_changed", checkpoint=checkpoint, differences=differences)


def verify_authoritative_inputs(checkpoint: str) -> None:
    manifest = load_manifest()
    initial = {item["path"]: item for item in manifest["authoritative_inputs_initial"]}
    current_items = authoritative_snapshot()
    current = {item["path"]: item for item in current_items}
    differences: list[dict[str, Any]] = []
    for path in sorted(set(initial) | set(current)):
        if initial.get(path) != current.get(path):
            differences.append({"path": path, "initial": initial.get(path), "current": current.get(path)})
    if differences:
        mark_stale(manifest, differences, checkpoint)
        raise SystemExit(f"Authoritative inputs changed at {checkpoint}; run marked STALE_INCOMPLETE")
    manifest["authoritative_inputs_last_verified_at"] = utc_now()
    manifest["authoritative_inputs_last_digest"] = snapshot_digest(current_items)
    save_manifest(manifest)
    append_log("authoritative_inputs_verified", checkpoint=checkpoint, digest=snapshot_digest(current_items))


def baseline_and_registry() -> tuple[dict[str, Any], list[dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    inventory_columns, rows = read_tsv(INVENTORY_PATH)
    if inventory_columns != ORIGINAL_COLUMNS:
        raise SystemExit(f"Unexpected inventory columns: {inventory_columns}")
    if any(row["fact_checked"].strip() or row["pages"].strip() for row in rows):
        raise SystemExit("Inventory fact_checked/pages baseline is not blank")
    triples = [(row["claim_id"], row["citation_key"], row["occurrence_id"]) for row in rows]
    counts = {
        "atomic_claim_ids": len({row["claim_id"] for row in rows}),
        "claim_source_occurrence_rows": len(rows),
        "unique_claim_source_occurrence_triples": len(set(triples)),
        "citation_occurrences": len({row["occurrence_id"] for row in rows}),
        "cited_works": len({row["citation_key"] for row in rows}),
        "direct_rows": sum(row["claim_type"] == "DIRECT" for row in rows),
        "author_inference_rows": sum(row["claim_type"] == "AUTHOR_INFERENCE" for row in rows),
    }
    expected_core = {
        "atomic_claim_ids": 186,
        "claim_source_occurrence_rows": 227,
        "unique_claim_source_occurrence_triples": 227,
        "citation_occurrences": 58,
        "cited_works": 24,
    }
    for key, expected in expected_core.items():
        if counts[key] != expected:
            raise SystemExit(f"Baseline mismatch for {key}: expected {expected}, got {counts[key]}")

    markdown = INVENTORY_MD_PATH.read_text(encoding="utf-8")
    markdown_rows = [line for line in markdown.splitlines() if line.startswith("| `CLM-")]
    markdown_ids, markdown_occurrences, markdown_keys = [], [], []
    for line in markdown_rows:
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        markdown_ids.append(cells[0])
        markdown_occurrences.append(cells[1])
        markdown_keys.append(cells[3])
    markdown_counts = {
        "rows": len(markdown_rows),
        "atomic_claim_ids": len(set(markdown_ids)),
        "citation_occurrences": len(set(markdown_occurrences)),
        "cited_works": len(set(markdown_keys)),
    }
    if markdown_counts != {"rows": 227, "atomic_claim_ids": 186, "citation_occurrences": 58, "cited_works": 24}:
        raise SystemExit(f"Markdown inventory mismatch: {markdown_counts}")

    manifest_columns, pdf_manifest_rows = read_tsv(PDF_MANIFEST_PATH)
    expected_manifest_columns = ["citation_key", "date", "title", "doi", "pdf_path", "sha256", "bytes"]
    if manifest_columns != expected_manifest_columns:
        raise SystemExit(f"Unexpected PDF manifest columns: {manifest_columns}")
    pdf_registry = {row["citation_key"]: row for row in pdf_manifest_rows}
    if len(pdf_registry) != len(pdf_manifest_rows):
        raise SystemExit("Duplicate citation_key in PDF manifest")
    for key, row in pdf_registry.items():
        path = REFERENCES / row["pdf_path"]
        if not path.is_file():
            raise SystemExit(f"Missing manifested PDF: {path}")
        actual_sha = sha256_file(path)
        actual_bytes = path.stat().st_size
        if actual_sha != row["sha256"] or actual_bytes != int(row["bytes"]):
            raise SystemExit(f"PDF manifest mismatch for {key}")

    bib_entries = parse_bib_entries(BIB_PATH.read_text(encoding="utf-8"))
    cited_keys = sorted({row["citation_key"] for row in rows})
    cited_pdf_keys = sorted(set(cited_keys) & set(pdf_registry))
    cited_without_pdf = sorted(set(cited_keys) - set(pdf_registry))
    if len(cited_pdf_keys) != 23 or len(cited_without_pdf) != 1:
        raise SystemExit(f"Expected 23 cited PDFs and one cited no-PDF work; got {len(cited_pdf_keys)} and {cited_without_pdf}")
    legal_key = cited_without_pdf[0]
    legal_entry = bib_entries.get(legal_key)
    if not legal_entry or legal_entry["entry_type"] != "legislation" or "www.planalto.gov.br" not in legal_entry["raw"]:
        raise SystemExit(f"The no-PDF cited work is not a verified official Planalto legislation record: {legal_key}")
    counts.update({
        "cited_pdfs": len(cited_pdf_keys),
        "cited_legal_web_sources_without_pdf": 1,
        "legal_web_citation_key": legal_key,
        "pdf_manifest_rows": len(pdf_manifest_rows),
        "pdf_files_in_directory": len([p for p in PDF_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]),
        "markdown_rows": markdown_counts["rows"],
    })

    for triple in CALIBRATION_TRIPLES:
        if triple not in set(triples):
            raise SystemExit(f"Missing calibration triple: {triple}")
    if triples[:4] != CALIBRATION_TRIPLES:
        raise SystemExit("The four calibration rows are not the first four queue rows")

    return counts, rows, bib_entries, pdf_registry


def cmd_init() -> None:
    if MANIFEST_PATH.exists():
        raise SystemExit("Run is already initialized")
    counts, inventory_rows, bib_entries, pdf_registry = baseline_and_registry()
    prompt_sha = sha256_file(PROMPT_PATH)
    schema_sha = sha256_file(SCHEMA_PATH)
    snapshot = authoritative_snapshot()
    snapshot_sha = snapshot_digest(snapshot)

    queue_rows: list[dict[str, str]] = []
    audited_rows: list[dict[str, str]] = []
    for index, row in enumerate(inventory_rows, start=1):
        row_id = f"ROW-{index:04d}"
        triple = (row["claim_id"], row["citation_key"], row["occurrence_id"])
        bib_entry = bib_entries[row["citation_key"]]
        pdf_record = pdf_registry.get(row["citation_key"])
        source_type = "PDF" if pdf_record else "LEGAL_HTML"
        source_path = f"references/{pdf_record['pdf_path']}" if pdf_record else ""
        source_sha = pdf_record["sha256"] if pdf_record else ""
        queue_row = dict(row)
        queue_row.update({
            "row_id": row_id,
            "queue_status": "CALIBRATION_PENDING" if triple in CALIBRATION_TRIPLES else "HELD_FOR_APPROVAL",
            "claim_row_sha256": canonical_sha({key: row[key] for key in ORIGINAL_COLUMNS}),
            "bibliography_entry_sha256": bib_entry["sha256"],
            "source_type": source_type,
            "source_path": source_path,
            "source_sha256": source_sha,
            "worker_prompt_path": "",
            "worker_prompt_sha256": "",
        })
        queue_rows.append(queue_row)
        audited_row = dict(row)
        audited_row.update({column: "" for column in APPENDED_COLUMNS})
        audited_row["row_id"] = row_id
        audited_row["audit_status"] = "CALIBRATION_PENDING" if triple in CALIBRATION_TRIPLES else "HELD_FOR_APPROVAL"
        audited_rows.append(audited_row)

    atomic_write_tsv(QUEUE_PATH, queue_rows, ORIGINAL_COLUMNS + QUEUE_EXTRA_COLUMNS)
    atomic_write_tsv(AUDITED_PATH, audited_rows, ORIGINAL_COLUMNS + APPENDED_COLUMNS)
    atomic_write_tsv(ISSUES_PATH, [], ISSUE_COLUMNS)
    atomic_write_text(LOG_PATH, "")

    manifest = {
        "manifest_version": "1.0.0",
        "run_id": RUN_ID,
        "workspace": str(WORKSPACE),
        "authorized_write_root": str(RUN_DIR),
        "blind_audit": True,
        "claude_outputs_read": False,
        "claude_output_path_forbidden": "references/claim_audit/runs/claude_opus_5/",
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "model_fallback_allowed": False,
        "runtime_verification": {
            "status": "MATCH",
            "verified_at": utc_now(),
            "verification_source": "/Users/manebrasil/.codex/config.toml",
            "model_line": "model = \"gpt-5.6-sol\"",
            "reasoning_line": "model_reasoning_effort = \"max\"",
        },
        "worker_runtime_policy": {
            "model": MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "fork_turns": "none",
            "no_fallback": True,
            "max_concurrent_claim_workers": 1,
        },
        "split_pdf_skill": {
            "path": "/Users/manebrasil/.agents/skills/split-pdf/SKILL.md",
            "sha256": sha256_file(Path("/Users/manebrasil/.agents/skills/split-pdf/SKILL.md")),
            "read_completely_before_pdf_access": True,
        },
        "prompt": {
            "path": PROMPT_PATH.relative_to(RUN_DIR).as_posix(),
            "sha256": prompt_sha,
            "hash_scope": "UTF-8 bytes of the audit protocol user message, stored with one final newline",
        },
        "schema": {
            "path": SCHEMA_PATH.relative_to(RUN_DIR).as_posix(),
            "sha256": schema_sha,
        },
        "expected_baseline": {
            "atomic_claim_ids": 186,
            "claim_source_occurrence_rows": 227,
            "citation_occurrences": 58,
            "cited_works": 24,
            "cited_pdfs": 23,
            "cited_legal_web_sources_without_pdf": 1,
        },
        "verified_baseline": counts,
        "baseline_status": "RECONCILED",
        "authoritative_inputs_initial": snapshot,
        "authoritative_inputs_initial_digest": snapshot_sha,
        "authoritative_inputs_last_verified_at": utc_now(),
        "authoritative_inputs_last_digest": snapshot_sha,
        "audit_phase": "CALIBRATION",
        "audit_status": "CALIBRATION_PREFLIGHT_COMPLETE",
        "completed_primary_results": 0,
        "completed_calibration_results": 0,
        "remaining_results": 227,
        "timestamps": {
            "run_started_at": STARTED_AT,
            "preflight_completed_at": utc_now(),
            "calibration_completed_at": None,
            "approval_received_at": None,
            "primary_completed_at": None,
            "quality_control_completed_at": None,
            "audit_completed_at": None,
        },
        "source_builds": {},
        "limitations": [
            "This manifest records the configured runtime available to the controller and the explicit runtime requested for isolated workers.",
            "The run is intentionally incomplete until calibration approval and all primary plus quality-control judgments are complete."
        ],
    }
    atomic_write_json(MANIFEST_PATH, manifest)
    append_log("runtime_verified", model=MODEL, reasoning_effort=REASONING_EFFORT, fallback=False)
    append_log("split_pdf_skill_read", path=manifest["split_pdf_skill"]["path"], sha256=manifest["split_pdf_skill"]["sha256"])
    append_log("baseline_reconciled", counts=counts)
    append_log("run_initialized", prompt_sha256=prompt_sha, schema_sha256=schema_sha, authoritative_inputs_digest=snapshot_sha)
    atomic_write_text(
        RUN_DIR / "AUDIT_REPORT.md",
        "# Source-to-Claim Fact-Check Audit\n\n"
        "> Status: calibration preflight complete; final audit report is intentionally pending.\n\n"
        "## Input and model manifest\n\n"
        f"- Run ID: `{RUN_ID}`\n"
        f"- Model: `{MODEL}`\n"
        f"- Reasoning effort: `{REASONING_EFFORT}`\n"
        f"- Baseline: 186 claims, 227 rows, 58 occurrences, 24 works, 23 PDFs, 1 legal web source\n"
        f"- Manifest: [`run_manifest.json`](run_manifest.json)\n\n"
        "## Scope and limitations\n\n"
        "Only the four required Bick calibration relationships may be processed before explicit user approval.\n"
    )
    print(json.dumps({"status": "initialized", "run_id": RUN_ID, "counts": counts, "snapshot_sha256": snapshot_sha}, ensure_ascii=False, indent=2))


def source_record_for_key(citation_key: str) -> dict[str, str]:
    _, rows = read_tsv(PDF_MANIFEST_PATH)
    registry = {row["citation_key"]: row for row in rows}
    return registry[citation_key]


def cmd_prepare_legal_source(citation_key: str) -> None:
    manifest = load_manifest()
    expected_key = manifest.get("verified_baseline", {}).get("legal_web_citation_key", "brasil_decreto_12342_2024")
    if citation_key != expected_key:
        raise SystemExit(f"Unknown legal source: {citation_key}")
    build_dir = SOURCE_BUILD / citation_key
    snapshot_path = build_dir / "official_snapshot.html"
    if not snapshot_path.is_file() or snapshot_path.stat().st_size == 0:
        raise SystemExit(f"Official legal snapshot is missing or empty: {snapshot_path}")
    bib_entry = find_bib_entry(citation_key)
    url_match = re.search(r"^\s*url\s*=\s*\{([^}]+)\}", bib_entry["raw"], flags=re.MULTILINE | re.IGNORECASE)
    if not url_match:
        raise SystemExit(f"Official URL is absent from the BibLaTeX entry: {citation_key}")
    official_url = url_match.group(1).strip()
    source_sha = sha256_file(snapshot_path)
    source_relative = snapshot_path.relative_to(WORKSPACE).as_posix()
    build_manifest_path = build_dir / "source_build_manifest.json"
    search_text_path = build_dir / "search_text.txt"
    if build_manifest_path.is_file():
        existing = json.loads(build_manifest_path.read_text(encoding="utf-8"))
        if existing.get("source_sha256") != source_sha or existing.get("official_url") != official_url:
            raise SystemExit(f"Existing legal source build is incompatible for {citation_key}")
    else:
        snapshot_text = snapshot_path.read_bytes().decode("latin-1")
        extractor = VisibleHTMLTextExtractor()
        extractor.feed(snapshot_text)
        normalized_lines = []
        for line in "".join(extractor.parts).splitlines():
            normalized = re.sub(r"\s+", " ", line).strip()
            if normalized:
                normalized_lines.append(normalized)
        atomic_write_text(search_text_path, "\n".join(normalized_lines) + "\n")
        retrieved_at = datetime.fromtimestamp(snapshot_path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        atomic_write_json(build_manifest_path, {
            "citation_key": citation_key,
            "source_type": "LEGAL_HTML",
            "official_url": official_url,
            "source_path": source_relative,
            "source_sha256": source_sha,
            "source_bytes": snapshot_path.stat().st_size,
            "snapshot_retrieved_at": retrieved_at,
            "search_text_path": search_text_path.relative_to(RUN_DIR).as_posix(),
            "search_text_sha256": sha256_file(search_text_path),
            "created_at": utc_now(),
        })
    queue_columns, rows = queue_rows()
    matched = False
    for row in rows:
        if row["citation_key"] == citation_key:
            row["source_type"] = "LEGAL_HTML"
            row["source_path"] = source_relative
            row["source_sha256"] = source_sha
            matched = True
    if not matched:
        raise SystemExit(f"No queue rows cite legal source: {citation_key}")
    atomic_write_tsv(QUEUE_PATH, rows, queue_columns)
    manifest = load_manifest()
    manifest["source_builds"][citation_key] = {
        "path": build_dir.relative_to(RUN_DIR).as_posix(),
        "source_type": "LEGAL_HTML",
        "official_url": official_url,
        "source_sha256": source_sha,
        "source_bytes": snapshot_path.stat().st_size,
        "status": "READY",
        "created_at": json.loads(build_manifest_path.read_text(encoding="utf-8"))["created_at"],
    }
    save_manifest(manifest)
    append_log(
        "legal_source_build_ready",
        citation_key=citation_key,
        official_url=official_url,
        source_path=source_relative,
        source_sha256=source_sha,
        source_bytes=snapshot_path.stat().st_size,
    )
    verify_authoritative_inputs(f"after_source_build_{citation_key}")
    print(json.dumps({
        "status": "ready",
        "citation_key": citation_key,
        "source_type": "LEGAL_HTML",
        "official_url": official_url,
        "source_sha256": source_sha,
        "build_dir": str(build_dir),
    }, indent=2))


def cmd_prepare_source(citation_key: str) -> None:
    verify_authoritative_inputs(f"before_source_build_{citation_key}")
    manifest = load_manifest()
    legal_key = manifest.get("verified_baseline", {}).get("legal_web_citation_key", "brasil_decreto_12342_2024")
    if citation_key == legal_key:
        cmd_prepare_legal_source(citation_key)
        return
    record = source_record_for_key(citation_key)
    source_path = REFERENCES / record["pdf_path"]
    if sha256_file(source_path) != record["sha256"]:
        raise SystemExit(f"Source hash mismatch for {citation_key}")
    build_dir = SOURCE_BUILD / citation_key
    split_dir = build_dir / "splits"
    text_dir = build_dir / "page_text"
    if build_dir.exists():
        build_manifest_path = build_dir / "source_build_manifest.json"
        if not build_manifest_path.is_file():
            raise SystemExit(f"Incomplete existing source build for {citation_key}; refusing to overwrite")
        existing = json.loads(build_manifest_path.read_text(encoding="utf-8"))
        if existing.get("source_sha256") != record["sha256"] or existing.get("pages_per_split") != 4:
            raise SystemExit(f"Existing source build is incompatible for {citation_key}")
        print(json.dumps({
            "status": "already_ready",
            "citation_key": citation_key,
            "page_count": existing["physical_pdf_pages"],
            "split_count": existing["split_count"],
            "build_dir": str(build_dir),
        }, indent=2))
        return
    split_dir.mkdir(parents=True)
    text_dir.mkdir(parents=True)

    reader = PdfReader(str(source_path))
    page_count = len(reader.pages)
    split_records = []
    for start in range(0, page_count, 4):
        end = min(start + 4, page_count)
        writer = PdfWriter()
        for page_index in range(start, end):
            writer.add_page(reader.pages[page_index])
        split_name = f"{citation_key}_pdfpp{start + 1:04d}-{end:04d}.pdf"
        split_path = split_dir / split_name
        with split_path.open("wb") as handle:
            writer.write(handle)
        split_records.append({
            "pdf_page_indices": f"{start + 1}-{end}",
            "path": split_path.relative_to(RUN_DIR).as_posix(),
            "sha256": sha256_file(split_path),
            "bytes": split_path.stat().st_size,
        })

    pdftotext = shutil.which("pdftotext")
    page_records = []
    search_rows = []
    extraction_method = "pdftotext -layout" if pdftotext else "PyPDF2.extract_text fallback"
    for physical_index, page in enumerate(reader.pages, start=1):
        text_path = text_dir / f"pdf-{physical_index:04d}.txt"
        if pdftotext:
            subprocess.run(
                [pdftotext, "-layout", "-f", str(physical_index), "-l", str(physical_index), str(source_path), str(text_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            page_text = text_path.read_text(encoding="utf-8", errors="replace")
        else:
            page_text = page.extract_text() or ""
            atomic_write_text(text_path, page_text)
        split_number = ((physical_index - 1) // 4) + 1
        split_path = split_dir / f"{citation_key}_pdfpp{((split_number - 1) * 4) + 1:04d}-{min(split_number * 4, page_count):04d}.pdf"
        page_records.append({
            "pdf_page_index": physical_index,
            "text_path": text_path.relative_to(RUN_DIR).as_posix(),
            "text_sha256": sha256_file(text_path),
            "text_characters": len(page_text),
            "split_path": split_path.relative_to(RUN_DIR).as_posix(),
        })
        normalized = re.sub(r"\s+", " ", page_text).strip()
        search_rows.append({"pdf_page_index": str(physical_index), "text": normalized})

    atomic_write_json(build_dir / "page_index.json", {
        "citation_key": citation_key,
        "source_path": source_path.relative_to(WORKSPACE).as_posix(),
        "source_sha256": record["sha256"],
        "physical_pdf_pages": page_count,
        "extraction_method": extraction_method,
        "pages": page_records,
    })
    atomic_write_tsv(build_dir / "search_index.tsv", search_rows, ["pdf_page_index", "text"])
    pdfinfo_path = build_dir / "pdfinfo.txt"
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        completed = subprocess.run([pdfinfo, str(source_path)], check=True, capture_output=True, text=True)
        atomic_write_text(pdfinfo_path, completed.stdout)
    else:
        atomic_write_text(pdfinfo_path, f"Pages: {page_count}\n")
    atomic_write_json(build_dir / "source_build_manifest.json", {
        "citation_key": citation_key,
        "source_path": source_path.relative_to(WORKSPACE).as_posix(),
        "source_sha256": record["sha256"],
        "source_bytes": source_path.stat().st_size,
        "physical_pdf_pages": page_count,
        "pages_per_split": 4,
        "split_count": len(split_records),
        "splits": split_records,
        "page_index_path": (build_dir / "page_index.json").relative_to(RUN_DIR).as_posix(),
        "search_index_path": (build_dir / "search_index.tsv").relative_to(RUN_DIR).as_posix(),
        "pdfinfo_path": pdfinfo_path.relative_to(RUN_DIR).as_posix(),
        "created_at": utc_now(),
    })
    manifest = load_manifest()
    manifest["source_builds"][citation_key] = {
        "path": build_dir.relative_to(RUN_DIR).as_posix(),
        "source_sha256": record["sha256"],
        "physical_pdf_pages": page_count,
        "pages_per_split": 4,
        "split_count": len(split_records),
        "status": "READY",
        "created_at": utc_now(),
    }
    save_manifest(manifest)
    append_log("source_build_created", citation_key=citation_key, page_count=page_count, split_count=len(split_records), extraction_method=extraction_method)
    verify_authoritative_inputs(f"after_source_build_{citation_key}")
    print(json.dumps({"status": "ready", "citation_key": citation_key, "page_count": page_count, "split_count": len(split_records), "build_dir": str(build_dir)}, indent=2))


def cmd_prepare_bick() -> None:
    cmd_prepare_source("bick_rapid_2024")


def find_bib_entry(citation_key: str) -> dict[str, str]:
    entries = parse_bib_entries(BIB_PATH.read_text(encoding="utf-8"))
    return entries[citation_key]


def queue_rows() -> tuple[list[str], list[dict[str, str]]]:
    return read_tsv(QUEUE_PATH)


def cmd_approve(approval_text: str) -> None:
    verify_authoritative_inputs("before_calibration_approval")
    manifest = load_manifest()
    if manifest.get("completed_calibration_results") != 4:
        raise SystemExit("Calibration approval requires four committed calibration results")
    if manifest.get("audit_status") not in {"CALIBRATION_COMPLETE_AWAITING_APPROVAL", "PRIMARY_IN_PROGRESS"}:
        raise SystemExit(f"Unexpected audit status for approval: {manifest.get('audit_status')}")
    columns, rows = queue_rows()
    for row in rows:
        index = int(row["row_id"].split("-")[1])
        if index > 4 and row["queue_status"] == "HELD_FOR_APPROVAL":
            row["queue_status"] = "PENDING"
    atomic_write_tsv(QUEUE_PATH, rows, columns)
    rebuild_derived_outputs()
    approved_at = manifest.get("timestamps", {}).get("approval_received_at") or utc_now()
    manifest["audit_phase"] = "PRIMARY_JUDGMENTS"
    manifest["audit_status"] = "PRIMARY_IN_PROGRESS"
    manifest["timestamps"]["approval_received_at"] = approved_at
    manifest["calibration_approval"] = {
        "status": "APPROVED",
        "approval_text": approval_text,
        "approval_text_sha256": sha256_bytes(approval_text.encode("utf-8")),
        "received_at": approved_at,
    }
    save_manifest(manifest)
    append_log(
        "calibration_approved",
        approval_text_sha256=manifest["calibration_approval"]["approval_text_sha256"],
        received_at=approved_at,
        released_rows=223,
    )
    atomic_write_text(
        RUN_DIR / "AUDIT_REPORT.md",
        "# Source-to-Claim Fact-Check Audit\n\n"
        "> Status: primary judgments in progress after explicit calibration approval. This is not the final audit report.\n\n"
        "## Input and model manifest\n\n"
        f"- Run ID: `{RUN_ID}`\n"
        f"- Model: `{MODEL}`\n"
        f"- Reasoning effort: `{REASONING_EFFORT}`\n"
        "- Model fallback: disabled\n"
        "- Baseline: 186 claims, 227 rows, 58 occurrences, 24 works, 23 PDFs, 1 legal web source\n"
        "- Authoritative input hashes: [`run_manifest.json`](run_manifest.json)\n\n"
        "## Calibration\n\n"
        "The four Bick calibration rows were approved by the user. See [`CALIBRATION_RECEIPT.md`](CALIBRATION_RECEIPT.md).\n\n"
        "## Current phase\n\n"
        "The remaining 223 primary judgments are being processed strictly sequentially. Quality control and the final aggregate report remain pending.\n"
    )
    verify_authoritative_inputs("after_calibration_approval")
    print(json.dumps({
        "status": "PRIMARY_IN_PROGRESS",
        "approval_received_at": approved_at,
        "released_rows": 223,
        "next_row": "ROW-0005",
    }, indent=2))


def cmd_make_legal_prompt(
    row_id: str,
    columns: list[str],
    rows: list[dict[str, str]],
    row: dict[str, str],
    index: int,
) -> None:
    build_manifest_path = SOURCE_BUILD / row["citation_key"] / "source_build_manifest.json"
    if not build_manifest_path.is_file():
        raise SystemExit(f"Legal source build is not ready: {row['citation_key']}")
    source_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    if source_manifest.get("source_sha256") != row["source_sha256"]:
        raise SystemExit(f"Legal source build hash mismatch for {row['citation_key']}")
    bib_entry = find_bib_entry(row["citation_key"])
    schema_sha = sha256_file(SCHEMA_PATH)
    worker_task_name = f"claim_row_{index:04d}"
    prompt_relative = f"source_build/prompts/{row_id}.md"
    candidate_relative = f"source_build/candidates/{row_id}.candidate.json"
    evidence_relative = f"evidence_pages/{row_id}.html"
    row_payload = {key: row[key] for key in ORIGINAL_COLUMNS}
    prompt = f"""# Isolated legal-source claim audit task: {row_id}

You are the sole active semantic claim worker for exactly one claim-source-occurrence relationship. Do not inspect any other row result, candidate, prompt, calibration receipt, or report. Never read or list anything under `references/claim_audit/runs/claude_opus_5/`.

## Mandatory runtime

- Model: `{MODEL}`
- Reasoning effort: `{REASONING_EFFORT}`
- Fallback: prohibited
- Worker task name: `{worker_task_name}`

If your runtime differs, stop without producing a candidate.

## Legal HTML protocol

This row cites an official Brazilian legal HTML source, not an academic PDF. Audit the exact run-specific snapshot of the cited Planalto page. Do not invent a page number and do not create a PDF. Use the exact legal hierarchy (article, paragraph, item, letter, or annex entry) as the locator. Web access may be used only to confirm identity/version; the frozen official snapshot below is the substantive evidence source.

## Authorized reads

- This prompt: `{prompt_relative}`
- Schema: `claim_result.schema.json`
- Audit protocol: `audit_protocol.txt`
- Legal source build manifest: `{build_manifest_path.relative_to(RUN_DIR).as_posix()}`
- Official frozen HTML snapshot: `{source_manifest['source_path']}`
- Run-specific search text: `{source_manifest['search_text_path']}`
- BibLaTeX entry reproduced below

Do not read `results/`, other prompts, other candidates, `issues.tsv`, `claim_inventory_audited.tsv`, `AUDIT_REPORT.md`, or any Claude path.

## Authorized writes

- Candidate JSON only: `{candidate_relative}`
- Exact legal evidence fragment only: `{evidence_relative}`

The evidence file must be a small valid UTF-8 HTML document containing only the exact official heading and legal provision(s) needed for this row, copied faithfully from the frozen snapshot, plus a source URL comment. Do not write the final `results/{row_id}.json`; the controller validates and commits it atomically.

## Audit row

```json
{json.dumps(row_payload, ensure_ascii=False, indent=2)}
```

Technical identity:

- row_id: `{row_id}`
- claim_row_sha256: `{row['claim_row_sha256']}`
- bibliography_entry_sha256: `{row['bibliography_entry_sha256']}`
- source_sha256: `{row['source_sha256']}`
- schema_sha256: `{schema_sha}`

Compute the SHA-256 of this prompt file after reading it and place that value in `worker_prompt_sha256`.

## Stored legal source registry record

```json
{json.dumps(source_manifest, ensure_ascii=False, indent=2)}
```

## Exact BibLaTeX entry

```bibtex
{bib_entry['raw'].rstrip()}
```

## Judgment contract

Audit only whether this exact official legal source supports this exact Portuguese claim. Use one substantive verdict: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, `NOT_VERIFIABLE`, or `SOURCE_BLOCKED`. Only `SUPPORTED` is a full pass. Every other verdict requires at least one complete structured issue.

For `AUTHOR_INFERENCE`, separately assess: (1) support for the factual premises; (2) whether the inference reasonably follows; and (3) whether the legal source itself explicitly states the inference. Never attribute an interpretation to the decree merely because it is reasonable.

Set `printed_pages` and `pages` to an exact form such as `art. X, § Y (HTML sem paginação)`. Set `pdf_page_indices` to exactly `N/A`. Set `source_locator` to the exact official legal hierarchy. The evidence anchor must reproduce no more than 12 source words. Evidence summary, mismatch explanation, inference assessment, and recommended dissertation revision must be in PT-BR. Preserve the claim and dissertation excerpt in Portuguese.

The `search_coverage` object must name every search term and legal hierarchy examined and record visual inspection as the frozen official HTML snapshot. For `NOT_FOUND`, search the complete snapshot and document all terms and relevant provisions examined.

Produce one JSON object conforming exactly to `claim_result.schema.json`. Set:

- `schema_version`: `1.0.0`
- `row_id`: `{row_id}`
- `worker_task_name`: `{worker_task_name}`
- `auditor_model`: `{MODEL}`
- `reasoning_effort`: `{REASONING_EFFORT}`
- `claim_row_sha256`: `{row['claim_row_sha256']}`
- `bibliography_entry_sha256`: `{row['bibliography_entry_sha256']}`
- `source_sha256`: `{row['source_sha256']}`
- `schema_sha256`: `{schema_sha}`
- `evidence_path`: `{evidence_relative}`
- `audit_status`: `COMPLETED` unless truly blocked
- `pdf_page_indices`: `N/A`
- `pages`: exactly the same string as `printed_pages`

For a DIRECT row, set `author_inference_assessment` to `null`. For an AUTHOR_INFERENCE row, fill the full object. Use RFC 3339 UTC for `audited_at`.

Before finishing, validate semantic accuracy, all hashes, exact row identity, legal locator, anchor length, evidence existence, and schema shape. Report only that the candidate is ready; do not include the verdict or evidence in your return message, so the controller carries no informal evidence into the next worker context.
"""
    prompt_path = RUN_DIR / prompt_relative
    atomic_write_text(prompt_path, prompt)
    prompt_sha = sha256_file(prompt_path)
    for item in rows:
        if item["row_id"] == row_id:
            item["worker_prompt_path"] = prompt_relative
            item["worker_prompt_sha256"] = prompt_sha
            item["queue_status"] = "PROMPT_READY"
    atomic_write_tsv(QUEUE_PATH, rows, columns)
    append_log(
        "legal_worker_prompt_created",
        row_id=row_id,
        prompt_path=prompt_relative,
        prompt_sha256=prompt_sha,
        worker_task_name=worker_task_name,
        source_sha256=row["source_sha256"],
    )
    print(json.dumps({
        "row_id": row_id,
        "prompt_path": str(prompt_path),
        "prompt_sha256": prompt_sha,
        "worker_task_name": worker_task_name,
        "source_type": "LEGAL_HTML",
    }, indent=2))


def cmd_make_prompt(row_id: str) -> None:
    verify_authoritative_inputs(f"before_prompt_{row_id}")
    columns, rows = queue_rows()
    matches = [row for row in rows if row["row_id"] == row_id]
    if len(matches) != 1:
        raise SystemExit(f"Unknown row_id: {row_id}")
    row = matches[0]
    index = int(row_id.split("-")[1])
    manifest = load_manifest()
    if index > 4 and not manifest.get("timestamps", {}).get("approval_received_at"):
        raise SystemExit("Calibration approval is required before ROW-0005")
    completed = sorted(path.stem for path in RESULTS_DIR.glob("ROW-*.json"))
    expected_previous = [f"ROW-{i:04d}" for i in range(1, index)]
    if completed != expected_previous:
        raise SystemExit(f"Strict sequential execution violation: completed={completed}, expected={expected_previous}")
    if row["queue_status"] not in {"CALIBRATION_PENDING", "PENDING", "PROMPT_READY"}:
        raise SystemExit(f"Row is not eligible for a primary prompt: {row['queue_status']}")
    if row["source_type"] == "LEGAL_HTML":
        cmd_make_legal_prompt(row_id, columns, rows, row, index)
        return
    if row["source_type"] != "PDF":
        raise SystemExit(f"Use the legal-source prompt path for {row_id}")
    source_manifest_path = SOURCE_BUILD / row["citation_key"] / "source_build_manifest.json"
    if not source_manifest_path.is_file():
        raise SystemExit(f"Source build is not ready: {row['citation_key']}")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if source_manifest.get("source_sha256") != row["source_sha256"]:
        raise SystemExit(f"Source build hash mismatch for {row['citation_key']}")
    bib_entry = find_bib_entry(row["citation_key"])
    schema_sha = sha256_file(SCHEMA_PATH)
    source_record = source_record_for_key(row["citation_key"])
    worker_task_name = f"bick_row_{index:04d}" if index <= 4 else f"claim_row_{index:04d}"
    prompt_relative = f"source_build/prompts/{row_id}.md"
    candidate_relative = f"source_build/candidates/{row_id}.candidate.json"
    evidence_relative = f"evidence_pages/{row_id}.pdf"
    row_payload = {key: row[key] for key in ORIGINAL_COLUMNS}
    prompt = f"""# Isolated claim audit task: {row_id}

You are the sole active semantic claim worker for exactly one claim-source-occurrence relationship. Do not inspect any other row result, candidate, prompt, calibration receipt, or report. Never read or list anything under `references/claim_audit/runs/claude_opus_5/`.

## Mandatory runtime

- Model: `{MODEL}`
- Reasoning effort: `{REASONING_EFFORT}`
- Fallback: prohibited
- Worker task name: `{worker_task_name}`

If your runtime differs, stop without producing a candidate.

## Required PDF protocol

Before opening any PDF split or rendered page, read `/Users/manebrasil/.agents/skills/split-pdf/SKILL.md` completely. The controller already generated new run-specific four-page splits and a run-specific page-text index. Do not use any preexisting extract, split, summary, candidate page, or other auditor's work.

- Never load the complete source PDF into model context.
- Use extracted text only to locate candidate evidence.
- Inspect no more than three four-page splits in one batch.
- If another batch is needed, finish and record the first batch before opening the next bounded batch.
- Do not use an abstract, web snippet, secondary source, or another paper as claim evidence.
- Render and visually inspect the actual physical PDF page whenever evidence involves a figure, table, equation, footnote, unusual layout, or questionable OCR.
- Use web access only if necessary to verify publication identity/version, never as substantive claim evidence.
- Preserve the original PDF unchanged.

## Authorized reads

- This prompt: `{prompt_relative}`
- Schema: `claim_result.schema.json`
- Audit protocol: `audit_protocol.txt`
- Source build manifest: `{source_manifest['page_index_path'].rsplit('/', 1)[0]}/source_build_manifest.json`
- Page index: `{source_manifest['page_index_path']}`
- Search index: `{source_manifest['search_index_path']}`
- Four-page split files listed in the source build manifest
- Original source only for selected-page extraction or rendering: `{source_manifest['source_path']}`
- BibLaTeX entry reproduced below

Do not read `results/`, other prompts, other candidates, `issues.tsv`, `claim_inventory_audited.tsv`, `AUDIT_REPORT.md`, or any Claude path.

## Authorized writes

- Candidate JSON only: `{candidate_relative}`
- Exact evidence PDF only: `{evidence_relative}`
- Optional selected-page PNG renders only inside: `source_build/renders/{row_id}/`

Do not write the final `results/{row_id}.json`; the controller validates and commits it atomically.

## Audit row

```json
{json.dumps(row_payload, ensure_ascii=False, indent=2)}
```

Technical identity:

- row_id: `{row_id}`
- claim_row_sha256: `{row['claim_row_sha256']}`
- bibliography_entry_sha256: `{row['bibliography_entry_sha256']}`
- source_sha256: `{row['source_sha256']}`
- schema_sha256: `{schema_sha}`

Compute the SHA-256 of this prompt file after reading it and place that value in `worker_prompt_sha256`.

## Stored source registry record

```json
{json.dumps(source_record, ensure_ascii=False, indent=2)}
```

## Exact BibLaTeX entry

```bibtex
{bib_entry['raw'].rstrip()}
```

## Judgment contract

Audit only whether this exact stored source supports this exact Portuguese claim. Reinspect source identity/version before judging. Record the exact stored version and date. If the bibliography describes a published article but the stored file is a working paper, discussion paper, or preprint, add a `PDF_VERSION_MISMATCH` issue without letting that issue mechanically determine the substantive verdict.

The package was previously suspected of containing non-final attachments for `goodman_bacon_difference_2021`, `callaway_difference_2021`, `sun_estimating_2021`, `de_chaisemartin_two-way_2020`, `santos_silva_log_2006`, and `chen_logs_2024`. Treat that list only as a warning, not as a conclusion: inspect the actual stored file and frozen BibLaTeX record independently for this row.

Use exactly one substantive verdict: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, `NOT_VERIFIABLE`, or `SOURCE_BLOCKED`. Only `SUPPORTED` is a full pass. Every other verdict requires at least one complete structured issue.

For `AUTHOR_INFERENCE`, separately assess: (1) support for the factual premises; (2) whether the inference reasonably follows; and (3) whether the source itself explicitly states the inference. Never attribute the dissertation author's interpretation to the source merely because it is reasonable.

Record printed pagination separately from physical one-based PDF indices. The evidence anchor must reproduce no more than 12 source words. Evidence summary, mismatch explanation, inference assessment, and recommended dissertation revision must be in PT-BR. Preserve the claim and dissertation excerpt in Portuguese.

The `search_coverage` object must name every search term, physical range, printed range, split file, and visual inspection used. For `NOT_FOUND`, continue through sufficiently exhaustive bounded batches and document all of them.

Extract only the exact supporting, conflicting, or diagnostic page range into `{evidence_relative}`. Use PyPDF2 with the physical one-based indices and preserve source pages without modification. Expand every range and discrete value in `pdf_page_indices`, then verify that the evidence PDF contains exactly one page for each unique declared physical index. Do not include a title, identity, cover, or adjacent page unless that page is also declared in `pdf_page_indices`. The evidence file must exist even for a non-pass result.

Produce one JSON object conforming exactly to `claim_result.schema.json`. Set:

- `schema_version`: `1.0.0`
- `row_id`: `{row_id}`
- `worker_task_name`: `{worker_task_name}`
- `auditor_model`: `{MODEL}`
- `reasoning_effort`: `{REASONING_EFFORT}`
- `claim_row_sha256`: `{row['claim_row_sha256']}`
- `bibliography_entry_sha256`: `{row['bibliography_entry_sha256']}`
- `source_sha256`: `{row['source_sha256']}`
- `schema_sha256`: `{schema_sha}`
- `evidence_path`: `{evidence_relative}`
- `audit_status`: `COMPLETED` unless truly blocked
- `pages`: exactly the same string as `printed_pages`

For a DIRECT row, set `author_inference_assessment` to `null`. For an AUTHOR_INFERENCE row, fill the full object. Use RFC 3339 UTC for `audited_at`.

Before finishing, validate semantic accuracy, all hashes, exact row identity, evidence existence, physical page bounds, anchor length, and schema shape. Report only that the candidate is ready; do not include the verdict or evidence in your return message, so the controller carries no informal evidence into the next worker context.
"""
    prompt_path = RUN_DIR / prompt_relative
    atomic_write_text(prompt_path, prompt)
    prompt_sha = sha256_file(prompt_path)
    for item in rows:
        if item["row_id"] == row_id:
            item["worker_prompt_path"] = prompt_relative
            item["worker_prompt_sha256"] = prompt_sha
            item["queue_status"] = "PROMPT_READY"
    atomic_write_tsv(QUEUE_PATH, rows, columns)
    append_log("worker_prompt_created", row_id=row_id, prompt_path=prompt_relative, prompt_sha256=prompt_sha, worker_task_name=worker_task_name)
    print(json.dumps({"row_id": row_id, "prompt_path": str(prompt_path), "prompt_sha256": prompt_sha, "worker_task_name": worker_task_name}, indent=2))


def cmd_retask_prompt(row_id: str, worker_task_name: str) -> None:
    verify_authoritative_inputs(f"before_retask_prompt_{row_id}")
    if not re.fullmatch(r"[a-z0-9_]+", worker_task_name):
        raise SystemExit("Retry worker task name must contain only lowercase letters, digits, and underscores")
    columns, rows = queue_rows()
    matches = [row for row in rows if row["row_id"] == row_id]
    if len(matches) != 1:
        raise SystemExit(f"Unknown row_id: {row_id}")
    row = matches[0]
    if (RESULTS_DIR / f"{row_id}.json").exists():
        raise SystemExit(f"Cannot retask an already committed row: {row_id}")
    candidate_path = RUN_DIR / f"source_build/candidates/{row_id}.candidate.json"
    if candidate_path.exists():
        raise SystemExit(f"Move or remove the incomplete candidate before retasking: {candidate_path}")
    prompt_relative = row.get("worker_prompt_path", "")
    prompt_path = RUN_DIR / prompt_relative
    if not prompt_relative or not prompt_path.is_file():
        raise SystemExit(f"Prompt is not ready for retasking: {row_id}")
    prompt_text = prompt_path.read_text(encoding="utf-8")
    task_match = re.search(r"^- Worker task name: `([^`]+)`$", prompt_text, flags=re.MULTILINE)
    if not task_match:
        raise SystemExit("Prompt does not declare a worker task name")
    previous_task_name = task_match.group(1)
    updated_prompt = prompt_text.replace(f"`{previous_task_name}`", f"`{worker_task_name}`")
    if updated_prompt == prompt_text:
        raise SystemExit("Prompt retask replacement made no change")
    retry_guard = """

## Retry validation guard

Before writing the candidate JSON, choose a deliberately short verbatim `evidence_anchor` of at most 8 whitespace-delimited source tokens. This conservative retry limit is stricter than the schema maximum of 12 words and avoids punctuation/tokenization ambiguity. Count the tokens explicitly, shorten again if needed, and do not finish until the anchor contains 8 or fewer tokens. For PDF evidence, expand every range and discrete value in `pdf_page_indices` and verify that the evidence PDF contains exactly one page for each unique declared physical index; never package an undeclared adjacent page.
"""
    retry_marker = "\n\n## Retry validation guard\n"
    if retry_marker in updated_prompt:
        updated_prompt = updated_prompt.split(retry_marker, 1)[0] + retry_guard
    else:
        updated_prompt += retry_guard
    atomic_write_text(prompt_path, updated_prompt)
    prompt_sha = sha256_file(prompt_path)
    for item in rows:
        if item["row_id"] == row_id:
            item["worker_prompt_sha256"] = prompt_sha
            item["queue_status"] = "PROMPT_READY"
    atomic_write_tsv(QUEUE_PATH, rows, columns)
    append_log(
        "worker_prompt_retasked",
        row_id=row_id,
        prompt_path=prompt_relative,
        previous_worker_task_name=previous_task_name,
        worker_task_name=worker_task_name,
        prompt_sha256=prompt_sha,
    )
    verify_authoritative_inputs(f"after_retask_prompt_{row_id}")
    print(json.dumps({
        "row_id": row_id,
        "prompt_path": str(prompt_path),
        "prompt_sha256": prompt_sha,
        "previous_worker_task_name": previous_task_name,
        "worker_task_name": worker_task_name,
    }, indent=2))


def cmd_normalize_source_version_date(row_id: str) -> None:
    verify_authoritative_inputs(f"before_source_version_date_normalization_{row_id}")
    candidate_path = RUN_DIR / f"source_build/candidates/{row_id}.candidate.json"
    if not candidate_path.is_file():
        raise SystemExit(f"Candidate is missing: {candidate_path}")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    prior_same_source = []
    for prior_path in sorted(RESULTS_DIR.glob("ROW-*.json")):
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        if prior.get("citation_key") == candidate.get("citation_key"):
            prior_same_source.append(prior)
    if not prior_same_source:
        print(json.dumps({
            "status": "source_version_date_reference_unavailable",
            "row_id": row_id,
            "citation_key": candidate.get("citation_key"),
            "source_version_date": candidate.get("source_version_date"),
        }, ensure_ascii=False, indent=2))
        return
    reference = prior_same_source[0]
    if reference.get("source_sha256") != candidate.get("source_sha256"):
        raise SystemExit("Cannot normalize identity across different source hashes")
    if reference.get("source_version_match") != candidate.get("source_version_match"):
        raise SystemExit("Source version classification differs substantively; manual review is required")
    previous_date = candidate.get("source_version_date")
    normalized_date = reference.get("source_version_date")
    if previous_date == normalized_date:
        print(json.dumps({
            "status": "source_version_date_already_normalized",
            "row_id": row_id,
            "source_version_date": normalized_date,
            "reference_row_id": reference.get("row_id"),
        }, ensure_ascii=False, indent=2))
        return
    candidate["source_version_date"] = normalized_date
    atomic_write_text(candidate_path, json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
    append_log(
        "candidate_source_version_date_normalized",
        row_id=row_id,
        citation_key=candidate.get("citation_key"),
        source_sha256=candidate.get("source_sha256"),
        previous_source_version_date=previous_date,
        normalized_source_version_date=normalized_date,
        reference_row_id=reference.get("row_id"),
    )
    verify_authoritative_inputs(f"after_source_version_date_normalization_{row_id}")
    print(json.dumps({
        "status": "source_version_date_normalized",
        "row_id": row_id,
        "previous_source_version_date": previous_date,
        "source_version_date": normalized_date,
        "reference_row_id": reference.get("row_id"),
    }, ensure_ascii=False, indent=2))


def validate_result_semantics(result: dict[str, Any], queue_row: dict[str, str]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise SystemExit("jsonschema is required for validated atomic commits") from exc
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(result), key=lambda item: list(item.path))
    if errors:
        details = "\n".join(f"{list(error.path)}: {error.message}" for error in errors)
        raise SystemExit(f"Schema validation failed:\n{details}")
    prompt_path = RUN_DIR / queue_row["worker_prompt_path"]
    if not prompt_path.is_file():
        raise SystemExit(f"Worker prompt is missing: {prompt_path}")
    prompt_text = prompt_path.read_text(encoding="utf-8")
    task_match = re.search(r"^- Worker task name: `([^`]+)`$", prompt_text, flags=re.MULTILINE)
    if not task_match:
        raise SystemExit("Worker prompt does not declare a task name")
    expected_worker_task_name = task_match.group(1)
    mappings = {
        "row_id": queue_row["row_id"],
        "claim_id": queue_row["claim_id"],
        "occurrence_id": queue_row["occurrence_id"],
        "citation_key": queue_row["citation_key"],
        "work": queue_row["work"],
        "section": queue_row["section"],
        "paragraph": queue_row["paragraph"],
        "claim_type": queue_row["claim_type"],
        "claim_as_written_pt": queue_row["affirmation_pt"],
        "source_excerpt_pt": queue_row["source_excerpt"],
        "claim_row_sha256": queue_row["claim_row_sha256"],
        "worker_prompt_sha256": queue_row["worker_prompt_sha256"],
        "bibliography_entry_sha256": queue_row["bibliography_entry_sha256"],
        "source_sha256": queue_row["source_sha256"],
        "schema_sha256": sha256_file(SCHEMA_PATH),
        "auditor_model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "worker_task_name": expected_worker_task_name,
    }
    mismatches = {key: {"expected": value, "actual": result.get(key)} for key, value in mappings.items() if result.get(key) != value}
    if mismatches:
        raise SystemExit(f"Result identity/hash mismatch: {json.dumps(mismatches, ensure_ascii=False, indent=2)}")
    if result["pages"] != result["printed_pages"]:
        raise SystemExit("pages must exactly equal printed_pages")
    anchor_words = re.findall(r"\b[\wÀ-ÿ’'-]+\b", result["evidence_anchor"], flags=re.UNICODE)
    if len(anchor_words) > 12:
        raise SystemExit(f"Evidence anchor has {len(anchor_words)} words; maximum is 12")
    if result["fact_checked"] != "SUPPORTED" and not result["issues"]:
        raise SystemExit("Every non-SUPPORTED result requires a structured issue")
    issue_codes = {issue["issue_code"] for issue in result["issues"]}
    if result["source_version_match"] == "PDF_VERSION_MISMATCH" and "PDF_VERSION_MISMATCH" not in issue_codes:
        raise SystemExit("PDF_VERSION_MISMATCH source identity requires a matching structured issue")
    if result["claim_type"] == "AUTHOR_INFERENCE" and result["author_inference_assessment"] is None:
        raise SystemExit("AUTHOR_INFERENCE requires the three-part assessment")
    if result["claim_type"] == "DIRECT" and result["author_inference_assessment"] is not None:
        raise SystemExit("DIRECT result must set author_inference_assessment to null")
    prior_same_source = []
    for prior_path in sorted(RESULTS_DIR.glob("ROW-*.json")):
        if prior_path.stem == result["row_id"]:
            continue
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        if prior.get("citation_key") == result["citation_key"]:
            prior_same_source.append(prior)
    if prior_same_source:
        identity_reference = prior_same_source[0]
        identity_fields = ("source_version_date", "source_version_match")
        identity_mismatches = {
            field: {"prior": identity_reference.get(field), "candidate": result.get(field)}
            for field in identity_fields
            if identity_reference.get(field) != result.get(field)
        }
        if identity_mismatches:
            raise SystemExit(
                "Source identity classification conflicts with an earlier independently audited row for the same stored file: "
                + json.dumps(identity_mismatches, ensure_ascii=False, indent=2)
            )
    for issue in result["issues"]:
        if issue["row_id"] != result["row_id"] or issue["evidence_path"] != result["evidence_path"]:
            raise SystemExit("Issue row/evidence identity mismatch")
    evidence_path = RUN_DIR / result["evidence_path"]
    try:
        evidence_path.resolve().relative_to(RUN_DIR.resolve())
    except ValueError as exc:
        raise SystemExit("Evidence path escapes run directory") from exc
    if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
        raise SystemExit(f"Evidence file is missing or empty: {evidence_path}")
    if queue_row["source_type"] == "LEGAL_HTML":
        if evidence_path.suffix.lower() != ".html":
            raise SystemExit("Legal HTML evidence must use the .html extension")
        if result["pdf_page_indices"] != "N/A":
            raise SystemExit("Legal HTML evidence must set pdf_page_indices to N/A")
        if "HTML sem paginação" not in result["printed_pages"]:
            raise SystemExit("Legal HTML printed_pages must state HTML sem paginação")
        if not re.search(r"\bart\.?\s*\d+", result["source_locator"], flags=re.IGNORECASE):
            raise SystemExit("Legal HTML source_locator must identify an exact article")
        evidence_text = evidence_path.read_text(encoding="utf-8", errors="strict")
        if not re.search(r"<html\b", evidence_text, flags=re.IGNORECASE):
            raise SystemExit("Legal evidence fragment must be a valid HTML document")
        if len(evidence_text.encode("utf-8")) > 100_000:
            raise SystemExit("Legal evidence fragment is not narrowly extracted")
    if evidence_path.suffix.lower() == ".pdf":
        evidence_reader = PdfReader(str(evidence_path))
        if not evidence_reader.pages:
            raise SystemExit("Evidence PDF has no pages")
        source_path = WORKSPACE / queue_row["source_path"]
        source_page_count = len(PdfReader(str(source_path)).pages)
        index_text = result["pdf_page_indices"]
        expanded_indices: set[int] = set()
        range_spans: list[tuple[int, int]] = []
        for match in re.finditer(r"(\d+)\s*[-\u2013\u2014]\s*(\d+)", index_text):
            start, end = (int(match.group(1)), int(match.group(2)))
            if end < start:
                raise SystemExit("Physical PDF page range is descending")
            expanded_indices.update(range(start, end + 1))
            range_spans.append(match.span())
        residual = index_text
        for start, end in reversed(range_spans):
            residual = residual[:start] + " " * (end - start) + residual[end:]
        expanded_indices.update(int(value) for value in re.findall(r"\d+", residual))
        if not expanded_indices or min(expanded_indices) < 1 or max(expanded_indices) > source_page_count:
            raise SystemExit(f"Physical PDF page indices outside source bounds 1-{source_page_count}")
        expected_evidence_pages = len(expanded_indices)
        if len(evidence_reader.pages) != expected_evidence_pages:
            raise SystemExit(f"Evidence PDF page count {len(evidence_reader.pages)} does not match stated physical range ({expected_evidence_pages})")


def rebuild_derived_outputs() -> None:
    queue_columns, qrows = queue_rows()
    original_columns, original_rows = read_tsv(INVENTORY_PATH)
    qmap = {row["row_id"]: row for row in qrows}
    result_map: dict[str, dict[str, Any]] = {}
    for path in sorted(RESULTS_DIR.glob("ROW-*.json")):
        result_map[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    audited_rows = []
    issue_rows = []
    for index, original in enumerate(original_rows, start=1):
        row_id = f"ROW-{index:04d}"
        item = dict(original)
        item.update({column: "" for column in APPENDED_COLUMNS})
        item["row_id"] = row_id
        result = result_map.get(row_id)
        if result:
            issues = result["issues"]
            item.update({
                "fact_checked": result["fact_checked"],
                "pages": result["pages"],
                "audit_status": result["audit_status"],
                "source_version": result["source_version"],
                "source_sha256": result["source_sha256"],
                "printed_pages": result["printed_pages"],
                "pdf_page_indices": result["pdf_page_indices"],
                "source_locator": result["source_locator"],
                "evidence_summary_pt": result["evidence_summary_pt"],
                "evidence_anchor": result["evidence_anchor"],
                "evidence_path": result["evidence_path"],
                "search_coverage": json.dumps(result["search_coverage"], ensure_ascii=False, separators=(",", ":")),
                "confidence": result["confidence"],
                "issue_codes": ";".join(issue["issue_code"] for issue in issues),
                "issue_severity": ";".join(issue["severity"] for issue in issues),
                "issue_detail_pt": " | ".join(issue["mismatch_explanation_pt"] for issue in issues),
                "recommended_revision_pt": result["recommended_revision_pt"],
                "needs_new_source": "true" if result["needs_new_source"] else "false",
                "auditor_model": result["auditor_model"],
                "audited_at": result["audited_at"],
            })
            for issue in issues:
                issue_rows.append({
                    "issue_id": issue["issue_id"],
                    "row_id": row_id,
                    "claim_id": result["claim_id"],
                    "citation_key": result["citation_key"],
                    "occurrence_id": result["occurrence_id"],
                    **{key: issue[key] for key in ISSUE_COLUMNS if key in issue},
                    "needs_new_source": "true" if issue["needs_new_source"] else "false",
                })
        else:
            item["audit_status"] = qmap[row_id]["queue_status"]
        audited_rows.append(item)
    atomic_write_tsv(AUDITED_PATH, audited_rows, original_columns + APPENDED_COLUMNS)
    atomic_write_tsv(ISSUES_PATH, issue_rows, ISSUE_COLUMNS)
    atomic_write_tsv(QUEUE_PATH, qrows, queue_columns)


def cmd_commit(row_id: str) -> None:
    verify_authoritative_inputs(f"before_commit_{row_id}")
    queue_columns, rows = queue_rows()
    matches = [row for row in rows if row["row_id"] == row_id]
    if len(matches) != 1:
        raise SystemExit(f"Unknown row_id: {row_id}")
    queue_row = matches[0]
    index = int(row_id.split("-")[1])
    completed = sorted(path.stem for path in RESULTS_DIR.glob("ROW-*.json"))
    expected_previous = [f"ROW-{i:04d}" for i in range(1, index)]
    if completed != expected_previous:
        raise SystemExit(f"Strict sequential execution violation: completed={completed}, expected={expected_previous}")
    manifest = load_manifest()
    if index > 4 and not manifest.get("timestamps", {}).get("approval_received_at"):
        raise SystemExit("Calibration approval is required before committing ROW-0005")
    if queue_row["queue_status"] != "PROMPT_READY":
        raise SystemExit(f"Row candidate is not eligible for commit: {queue_row['queue_status']}")
    candidate_path = SOURCE_BUILD / "candidates" / f"{row_id}.candidate.json"
    if not candidate_path.is_file():
        raise SystemExit(f"Candidate does not exist: {candidate_path}")
    result = json.loads(candidate_path.read_text(encoding="utf-8"))
    validate_result_semantics(result, queue_row)
    result_path = RESULTS_DIR / f"{row_id}.json"
    atomic_write_json(result_path, result)
    for row in rows:
        if row["row_id"] == row_id:
            row["queue_status"] = "COMPLETED"
    atomic_write_tsv(QUEUE_PATH, rows, queue_columns)
    rebuild_derived_outputs()
    manifest = load_manifest()
    result_count = len(list(RESULTS_DIR.glob("ROW-*.json")))
    manifest["completed_primary_results"] = result_count
    manifest["completed_calibration_results"] = min(result_count, 4)
    manifest["remaining_results"] = 227 - result_count
    if result_count < 4:
        manifest["audit_phase"] = "CALIBRATION"
        manifest["audit_status"] = "CALIBRATION_IN_PROGRESS"
    elif result_count == 4 and not manifest.get("timestamps", {}).get("approval_received_at"):
        manifest["audit_phase"] = "CALIBRATION_GATE"
        manifest["audit_status"] = "CALIBRATION_COMPLETE_AWAITING_APPROVAL"
    elif result_count < 227:
        manifest["audit_phase"] = "PRIMARY_JUDGMENTS"
        manifest["audit_status"] = "PRIMARY_IN_PROGRESS"
    else:
        manifest["audit_phase"] = "QUALITY_CONTROL_PREPARATION"
        manifest["audit_status"] = "PRIMARY_COMPLETE_PENDING_QC"
        manifest["timestamps"]["primary_completed_at"] = utc_now()
    if result_count == 4 and not manifest["timestamps"].get("calibration_completed_at"):
        manifest["timestamps"]["calibration_completed_at"] = utc_now()
    save_manifest(manifest)
    append_log(
        "result_validated_and_committed",
        row_id=row_id,
        result_path=result_path.relative_to(RUN_DIR).as_posix(),
        result_sha256=sha256_file(result_path),
        evidence_path=result["evidence_path"],
        evidence_sha256=sha256_file(RUN_DIR / result["evidence_path"]),
    )
    verify_authoritative_inputs(f"after_commit_{row_id}")
    print(json.dumps({"status": "committed", "row_id": row_id, "result_sha256": sha256_file(result_path), "completed": result_count}, indent=2))


def cmd_recommit(row_id: str) -> None:
    verify_authoritative_inputs(f"before_recommit_{row_id}")
    queue_columns, rows = queue_rows()
    matches = [row for row in rows if row["row_id"] == row_id]
    if len(matches) != 1:
        raise SystemExit(f"Unknown row_id: {row_id}")
    queue_row = matches[0]
    result_path = RESULTS_DIR / f"{row_id}.json"
    candidate_path = SOURCE_BUILD / "candidates" / f"{row_id}.candidate.json"
    if not result_path.is_file() or not candidate_path.is_file():
        raise SystemExit("Recommit requires both an existing committed result and a revised candidate")
    result = json.loads(candidate_path.read_text(encoding="utf-8"))
    validate_result_semantics(result, queue_row)
    previous_sha = sha256_file(result_path)
    revision_dir = SOURCE_BUILD / "revisions" / row_id
    revision_dir.mkdir(parents=True, exist_ok=True)
    archived_result = revision_dir / f"result_before_{previous_sha}.json"
    if not archived_result.exists():
        shutil.copy2(result_path, archived_result)
    atomic_write_json(result_path, result)
    rebuild_derived_outputs()
    manifest = load_manifest()
    result_count = len(list(RESULTS_DIR.glob("ROW-*.json")))
    manifest["completed_primary_results"] = result_count
    manifest["completed_calibration_results"] = min(result_count, 4)
    manifest["remaining_results"] = 227 - result_count
    if result_count < 4:
        manifest["audit_phase"] = "CALIBRATION"
        manifest["audit_status"] = "CALIBRATION_IN_PROGRESS"
    elif result_count == 4 and not manifest.get("timestamps", {}).get("approval_received_at"):
        manifest["audit_phase"] = "CALIBRATION_GATE"
        manifest["audit_status"] = "CALIBRATION_COMPLETE_AWAITING_APPROVAL"
    elif result_count < 227:
        manifest["audit_phase"] = "PRIMARY_JUDGMENTS"
        manifest["audit_status"] = "PRIMARY_IN_PROGRESS"
    else:
        manifest["audit_phase"] = "QUALITY_CONTROL_PREPARATION"
        manifest["audit_status"] = "PRIMARY_COMPLETE_PENDING_QC"
    save_manifest(manifest)
    append_log(
        "result_revalidated_and_recommitted",
        row_id=row_id,
        previous_result_sha256=previous_sha,
        archived_result_path=archived_result.relative_to(RUN_DIR).as_posix(),
        revised_result_sha256=sha256_file(result_path),
        evidence_path=result["evidence_path"],
        evidence_sha256=sha256_file(RUN_DIR / result["evidence_path"]),
    )
    verify_authoritative_inputs(f"after_recommit_{row_id}")
    print(json.dumps({
        "status": "recommitted",
        "row_id": row_id,
        "previous_result_sha256": previous_sha,
        "revised_result_sha256": sha256_file(result_path),
        "completed": result_count,
    }, indent=2))


def cmd_verify() -> None:
    verify_authoritative_inputs("manual_verification")
    manifest = load_manifest()
    _, qrows = queue_rows()
    results = sorted(RESULTS_DIR.glob("ROW-*.json"))
    committed = []
    for path in results:
        result = json.loads(path.read_text(encoding="utf-8"))
        queue_row = next(row for row in qrows if row["row_id"] == result["row_id"])
        try:
            validate_result_semantics(result, queue_row)
        except SystemExit as exc:
            raise SystemExit(f"{path.stem}: {exc}") from exc
        committed.append(result["row_id"])
    print(json.dumps({
        "run_id": RUN_ID,
        "audit_status": manifest["audit_status"],
        "baseline_status": manifest["baseline_status"],
        "committed_results": committed,
        "claude_outputs_read": manifest["claude_outputs_read"],
        "authoritative_inputs_digest": manifest["authoritative_inputs_last_digest"],
    }, indent=2))


def cmd_record_evidence_repair(row_id: str, archived_evidence_path: str) -> None:
    verify_authoritative_inputs(f"before_evidence_repair_record_{row_id}")
    result_path = RESULTS_DIR / f"{row_id}.json"
    if not result_path.is_file():
        raise SystemExit(f"Committed result is missing: {row_id}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    _, qrows = queue_rows()
    queue_row = next((row for row in qrows if row["row_id"] == row_id), None)
    if queue_row is None:
        raise SystemExit(f"Queue row is missing: {row_id}")
    archive_path = RUN_DIR / archived_evidence_path
    try:
        archive_path.resolve().relative_to(RUN_DIR.resolve())
    except ValueError as exc:
        raise SystemExit("Archived evidence path escapes run directory") from exc
    if not archive_path.is_file() or archive_path.stat().st_size == 0:
        raise SystemExit(f"Archived evidence is missing or empty: {archive_path}")
    validate_result_semantics(result, queue_row)
    current_evidence_path = RUN_DIR / result["evidence_path"]
    append_log(
        "evidence_selection_repaired",
        row_id=row_id,
        reason="Evidence package contained a continuous range while pdf_page_indices declared discrete pages",
        pdf_page_indices=result["pdf_page_indices"],
        archived_evidence_path=archive_path.relative_to(RUN_DIR).as_posix(),
        archived_evidence_sha256=sha256_file(archive_path),
        evidence_path=result["evidence_path"],
        evidence_sha256=sha256_file(current_evidence_path),
    )
    verify_authoritative_inputs(f"after_evidence_repair_record_{row_id}")
    print(json.dumps({
        "status": "evidence_repair_recorded",
        "row_id": row_id,
        "archived_evidence_path": archive_path.relative_to(RUN_DIR).as_posix(),
        "archived_evidence_sha256": sha256_file(archive_path),
        "evidence_path": result["evidence_path"],
        "evidence_sha256": sha256_file(current_evidence_path),
    }, indent=2))


def cmd_record_runner_termination(row_id: str, pids: str, elapsed: str, signal_name: str, reason: str) -> None:
    verify_authoritative_inputs(f"before_runner_termination_record_{row_id}")
    result_path = RESULTS_DIR / f"{row_id}.json"
    candidate_path = RUN_DIR / f"source_build/candidates/{row_id}.candidate.json"
    if not result_path.is_file() or not candidate_path.is_file():
        raise SystemExit("Runner termination may be recorded only after a candidate was validated and committed")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    evidence_path = RUN_DIR / result["evidence_path"]
    append_log(
        "isolated_runner_terminated_after_artifact_write",
        row_id=row_id,
        runner="codex-cli 0.146.0 ephemeral",
        model=MODEL,
        reasoning_effort=REASONING_EFFORT,
        pids=pids,
        observed_elapsed=elapsed,
        signal=signal_name,
        reason=reason,
        candidate_sha256=sha256_file(candidate_path),
        result_sha256=sha256_file(result_path),
        evidence_sha256=sha256_file(evidence_path),
    )
    verify_authoritative_inputs(f"after_runner_termination_record_{row_id}")
    print(json.dumps({
        "status": "runner_termination_recorded",
        "row_id": row_id,
        "signal": signal_name,
        "reason": reason,
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")
    subparsers.add_parser("prepare-bick")
    source_parser = subparsers.add_parser("prepare-source")
    source_parser.add_argument("citation_key")
    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("--text", required=True)
    prompt_parser = subparsers.add_parser("make-prompt")
    prompt_parser.add_argument("row_id")
    retask_parser = subparsers.add_parser("retask-prompt")
    retask_parser.add_argument("row_id")
    retask_parser.add_argument("worker_task_name")
    normalize_date_parser = subparsers.add_parser("normalize-source-version-date")
    normalize_date_parser.add_argument("row_id")
    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("row_id")
    recommit_parser = subparsers.add_parser("recommit")
    recommit_parser.add_argument("row_id")
    evidence_repair_parser = subparsers.add_parser("record-evidence-repair")
    evidence_repair_parser.add_argument("row_id")
    evidence_repair_parser.add_argument("archived_evidence_path")
    runner_termination_parser = subparsers.add_parser("record-runner-termination")
    runner_termination_parser.add_argument("row_id")
    runner_termination_parser.add_argument("--pids", required=True)
    runner_termination_parser.add_argument("--elapsed", required=True)
    runner_termination_parser.add_argument("--signal", required=True)
    runner_termination_parser.add_argument("--reason", required=True)
    subparsers.add_parser("verify")
    args = parser.parse_args()
    if args.command == "init":
        cmd_init()
    elif args.command == "prepare-bick":
        cmd_prepare_bick()
    elif args.command == "prepare-source":
        cmd_prepare_source(args.citation_key)
    elif args.command == "approve":
        cmd_approve(args.text)
    elif args.command == "make-prompt":
        cmd_make_prompt(args.row_id)
    elif args.command == "retask-prompt":
        cmd_retask_prompt(args.row_id, args.worker_task_name)
    elif args.command == "normalize-source-version-date":
        cmd_normalize_source_version_date(args.row_id)
    elif args.command == "commit":
        cmd_commit(args.row_id)
    elif args.command == "recommit":
        cmd_recommit(args.row_id)
    elif args.command == "record-evidence-repair":
        cmd_record_evidence_repair(args.row_id, args.archived_evidence_path)
    elif args.command == "record-runner-termination":
        cmd_record_runner_termination(args.row_id, args.pids, args.elapsed, args.signal, args.reason)
    elif args.command == "verify":
        cmd_verify()


if __name__ == "__main__":
    main()
