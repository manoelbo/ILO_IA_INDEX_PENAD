#!/usr/bin/env python3
"""Deterministic controller for current primary claim judgments.

Semantic work happens only in isolated Codex workers. This controller prepares
one-row prompts, validates candidate artifacts, commits results atomically, and
rebuilds the working 38-column TSV without interpreting claim content.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PyPDF2 import PdfReader


RUN_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = RUN_DIR.parents[4]
QUEUE_PATH = RUN_DIR / "queue.tsv"
AUDIT_PATH = RUN_DIR / "claim_inventory_audited_current.tsv"
DELTA_PATH = RUN_DIR / "claim_inventory_delta.tsv"
SCHEMA_PATH = RUN_DIR / "claim_result.schema.json"
PROTOCOL_PATH = RUN_DIR / "audit_protocol.txt"
BIB_PATH = PROJECT_DIR / "references/library.bib"
PDF_MANIFEST_PATH = PROJECT_DIR / "references/pdf_manifest.tsv"
NOTION_MANIFEST_PATH = RUN_DIR / "source_snapshot/snapshot_manifest.json"
RESULTS_DIR = RUN_DIR / "results"
CANDIDATES_DIR = RUN_DIR / "source_build/candidates"
PROMPTS_DIR = RUN_DIR / "source_build/prompts"
EVIDENCE_DIR = RUN_DIR / "evidence_pages"
MANIFEST_PATH = RUN_DIR / "run_manifest.json"
LOG_PATH = RUN_DIR / "audit_log.jsonl"

MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "max"
CALIBRATION_RULE_VERSION = "balanced-v1.0-2026-08-07"

BASE_QUEUE_COLUMNS = [
    "row_id", "claim_id", "occurrence_id", "citation_key", "work", "claim_type",
    "affirmation_pt", "source_excerpt", "section", "paragraph",
    "reconciliation_status", "prior_row_id", "current_source_sha256", "source_path",
]
QUEUE_EXTRA_COLUMNS = [
    "queue_status", "claim_row_sha256", "bibliography_entry_sha256", "source_type",
    "worker_prompt_path", "worker_prompt_sha256", "worker_task_name",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def atomic_tsv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def log(event: str, **fields: Any) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": utc_now(), "event": event, **fields}, ensure_ascii=False, sort_keys=True) + "\n")


def parse_bib_entries() -> dict[str, str]:
    text = BIB_PATH.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    entries: dict[str, str] = {}
    index = 0
    while index < len(lines):
        match = re.match(r"^@(\w+)\s*\{\s*([^,]+)\s*,", lines[index])
        if not match:
            index += 1
            continue
        key = match.group(2).strip()
        parts = [lines[index]]
        depth = lines[index].count("{") - lines[index].count("}")
        index += 1
        while index < len(lines) and depth > 0:
            parts.append(lines[index])
            depth += lines[index].count("{") - lines[index].count("}")
            index += 1
        entries[key] = "".join(parts)
    return entries


def queue() -> tuple[list[str], list[dict[str, str]]]:
    return read_tsv(QUEUE_PATH)


def queue_row(row_id: str) -> tuple[list[str], list[dict[str, str]], dict[str, str]]:
    columns, rows = queue()
    matches = [row for row in rows if row["row_id"] == row_id]
    if len(matches) != 1:
        raise SystemExit(f"Unknown or duplicate row_id: {row_id}")
    return columns, rows, matches[0]


def authoritative_snapshot() -> list[dict[str, Any]]:
    paths = [
        RUN_DIR / "claim_inventory_current.tsv",
        DELTA_PATH,
        BIB_PATH,
        PDF_MANIFEST_PATH,
        NOTION_MANIFEST_PATH,
        SCHEMA_PATH,
        PROTOCOL_PATH,
    ]
    _, queue_rows = queue()
    keys = sorted({row["citation_key"] for row in queue_rows})
    for key in keys:
        source_manifest = RUN_DIR / f"source_build/{key}/source_build_manifest.json"
        paths.append(source_manifest)
        manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
        source_path = PROJECT_DIR / manifest["source_path"]
        paths.append(source_path)
        for index_field in ("page_index_path", "search_index_path", "pdfinfo_path", "search_text_path"):
            relative_path = manifest.get(index_field)
            if relative_path:
                paths.append(RUN_DIR / relative_path)
        for split in manifest.get("splits", []):
            paths.append(RUN_DIR / split["path"])
    result = []
    for path in sorted(set(paths)):
        if not path.is_file():
            raise SystemExit(f"Missing authoritative input: {path}")
        result.append({
            "path": path.relative_to(PROJECT_DIR).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    return result


def verify_inputs(checkpoint: str) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    current = authoritative_snapshot()
    if current != manifest["authoritative_inputs"]:
        manifest["status"] = "STALE_INCOMPLETE"
        manifest["stale_checkpoint"] = checkpoint
        manifest["stale_detected_at"] = utc_now()
        atomic_json(MANIFEST_PATH, manifest)
        raise SystemExit(f"Authoritative inputs changed at {checkpoint}")


def cmd_init() -> None:
    columns, rows = queue()
    if columns not in (BASE_QUEUE_COLUMNS, BASE_QUEUE_COLUMNS + QUEUE_EXTRA_COLUMNS):
        raise SystemExit(f"Unexpected queue interface: {columns}")
    bib = parse_bib_entries()
    delta = {row["row_id"]: row for row in read_tsv(DELTA_PATH)[1]}
    for row in rows:
        key = row["citation_key"]
        if key not in bib:
            raise SystemExit(f"Missing bibliography entry: {key}")
        source_manifest = json.loads(
            (RUN_DIR / f"source_build/{key}/source_build_manifest.json").read_text(encoding="utf-8")
        )
        if source_manifest["source_sha256"] != row["current_source_sha256"]:
            raise SystemExit(f"Source packet mismatch for {key}")
        existing = RESULTS_DIR / f"{row['row_id']}.json"
        row["queue_status"] = "COMPLETED" if existing.is_file() else "PENDING"
        row["claim_row_sha256"] = delta[row["row_id"]]["claim_text_sha256"]
        row["bibliography_entry_sha256"] = sha256_bytes(bib[key].encode("utf-8"))
        row["source_type"] = "LEGAL_HTML" if source_manifest.get("source_type") == "LEGAL_HTML" else "PDF"
        row.setdefault("worker_prompt_path", "")
        row.setdefault("worker_prompt_sha256", "")
        row.setdefault("worker_task_name", "")
    atomic_tsv(QUEUE_PATH, BASE_QUEUE_COLUMNS + QUEUE_EXTRA_COLUMNS, rows)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": RUN_DIR.name,
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "fallback": "disabled",
        "calibration_rule_version": CALIBRATION_RULE_VERSION,
        "started_at": utc_now(),
        "status": "PRIMARY_READY",
        "queue_rows": len(rows),
        "reused_exact_rows": 7,
        "authoritative_inputs": [],
        "runtime_preflight": {
            "required_model": MODEL,
            "required_reasoning_effort": REASONING_EFFORT,
            "enforcement": "codex exec --model plus strict explicit model_reasoning_effort",
        },
    }
    atomic_json(MANIFEST_PATH, manifest)
    manifest["authoritative_inputs"] = authoritative_snapshot()
    manifest["authoritative_inputs_digest"] = sha256_bytes(
        json.dumps(manifest["authoritative_inputs"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    atomic_json(MANIFEST_PATH, manifest)
    log("current_run_initialized", queue_rows=len(rows), model=MODEL, reasoning_effort=REASONING_EFFORT)
    print(json.dumps({"status": "PRIMARY_READY", "queue_rows": len(rows)}, indent=2))


def prompt_for(row: dict[str, str], bib_entry: str, source_manifest: dict[str, Any]) -> str:
    row_id = row["row_id"]
    task_name = f"current_claim_row_{row_id.rsplit('-', 1)[1]}"
    prompt_rel = f"source_build/prompts/{row_id}.md"
    candidate_rel = f"source_build/candidates/{row_id}.candidate.json"
    evidence_suffix = "html" if row["source_type"] == "LEGAL_HTML" else "pdf"
    evidence_rel = f"evidence_pages/{row_id}.{evidence_suffix}"
    row_payload = {key: row[key] for key in BASE_QUEUE_COLUMNS[:10]}
    schema_sha = sha256_file(SCHEMA_PATH)
    manifest_path = f"source_build/{row['citation_key']}/source_build_manifest.json"
    manifest_absolute = RUN_DIR / manifest_path
    source_absolute = PROJECT_DIR / source_manifest["source_path"]
    prompt_absolute = RUN_DIR / prompt_rel
    candidate_absolute = RUN_DIR / candidate_rel
    evidence_absolute = RUN_DIR / evidence_rel
    if row["source_type"] == "LEGAL_HTML":
        search_text_absolute = RUN_DIR / source_manifest["search_text_path"]
        source_rules = f"""This is an official legal HTML source. Read only `{source_absolute}` and `{search_text_absolute}` as substantive evidence. Use exact article/paragraph/item locators, set `pdf_page_indices` to `N/A`, set pages/printed_pages to a legal locator ending in `(HTML sem paginação)`, and write a narrow UTF-8 evidence fragment to `{evidence_absolute}`."""
        authorized = f"- `{source_absolute}`\n- `{search_text_absolute}`"
    else:
        page_index_absolute = RUN_DIR / source_manifest["page_index_path"]
        search_index_absolute = RUN_DIR / source_manifest["search_index_path"]
        extraction_script = RUN_DIR / "source_build/scripts/extract_evidence.py"
        python_deps = PROJECT_DIR / "references/claim_audit/runs/codex_sol_max/20260801T155350Z/source_build/python_deps"
        source_rules = f"""Read `/Users/manebrasil/.agents/skills/split-pdf/SKILL.md` completely before source content. Use the page-text/search index only for localization. Never load the complete PDF into context. Open no more than three four-page splits per batch and document each batch. Visually inspect pages containing tables, figures, formulas, footnotes, unusual layout, or questionable OCR. Extract exactly the declared physical pages to `{evidence_absolute}` using `python3` (not `python`) with `{extraction_script}` and `PYTHONPATH={python_deps}`. The final controller, not the worker, performs authoritative JSON Schema validation."""
        authorized = (
            f"- `{page_index_absolute}`\n"
            f"- `{search_index_absolute}`\n"
            f"- four-page splits listed in `{manifest_absolute}`\n"
            f"- original `{source_absolute}` only for selected-page extraction/rendering"
        )
    return f"""# Isolated current claim audit: {row_id}

You are the sole semantic auditor for exactly one claim-source-occurrence row.

Your working directory is the current run: `{RUN_DIR}`. Do not search for a run
directory and do not enter `20260801T155350Z` or any other historical run. All
relative artifact paths below resolve from `{RUN_DIR}`. The project root is
`{PROJECT_DIR}`.

## Runtime gate

- Required model: `{MODEL}`
- Required reasoning effort: `{REASONING_EFFORT}`
- Fallback: prohibited
- Worker task name: `{task_name}`

If the effective runtime differs, stop without writing artifacts.

## Blindness and scope

Audit only the row below. Do not read or list any old run, any Claude path, `results/`, other prompts/candidates, the consolidated TSV, reports, QC artifacts, or another row's evidence. Do not use a prior verdict or evidence. Read `{PROTOCOL_PATH}` and `{SCHEMA_PATH}` completely. Do not use filesystem search to find alternatives; every authorized path is explicit below.

{source_rules}

Authorized source reads:
- `{manifest_absolute}`
{authorized}
- the exact BibLaTeX entry reproduced below

Authorized writes only:
- `{candidate_absolute}`
- `{evidence_absolute}`
- optional visual renders under `{RUN_DIR / f'source_build/renders/{row_id}'}/`

## Row

```json
{json.dumps(row_payload, ensure_ascii=False, indent=2)}
```

Technical identity:
- row_id: `{row_id}`
- claim_row_sha256: `{row['claim_row_sha256']}`
- bibliography_entry_sha256: `{row['bibliography_entry_sha256']}`
- source_sha256: `{row['current_source_sha256']}`
- schema_sha256: `{schema_sha}`
- reconciliation_status: `{row['reconciliation_status']}`

Compute `{prompt_absolute}`'s SHA-256 after reading it and store it as `worker_prompt_sha256`.

## Exact BibLaTeX entry

```bibtex
{bib_entry.rstrip()}
```

## Judgment requirements

Use only `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, or `NOT_VERIFIABLE`. Apply the balanced calibration in `audit_protocol.txt`. Every non-SUPPORTED verdict requires at least one complete structured issue. An AUTHOR_INFERENCE must separately assess factual premises, reasonableness, and whether the source explicitly states the inference.

Record printed pages and one-based physical PDF indices separately. `pages` must equal `printed_pages` and may never be blank. `N/A` requires a structured justification. Choose a deliberately short verbatim evidence anchor of no more than 8 whitespace-delimited words (stricter than the 12-word schema ceiling) and count it before writing. Search coverage must list every search term, page range, split, and visual check actually used. Do not use abstracts or outside sources as substantive evidence.

Work efficiently without reducing rigor: once unambiguous evidence and source identity are established, do not open merely confirmatory extra pages. Expand the search only when the first bounded batch leaves a material component unresolved or when a non-pass verdict requires broader documented coverage.

After writing the candidate and evidence, perform only one quick local check of the declared hashes and evidence-page count, then finish immediately. Do not install packages, troubleshoot `jsonschema`, or repeat controller-level validation; the controller validates the full schema and all identity fields after your process exits.

Write one JSON object conforming exactly to `claim_result.schema.json` at `{candidate_rel}`. Use:
- `schema_version`: `1.0.0`
- `row_id`: `{row_id}`
- `claim_id`: `{row['claim_id']}`
- `occurrence_id`: `{row['occurrence_id']}`
- `worker_task_name`: `{task_name}`
- `auditor_model`: `{MODEL}`
- `reasoning_effort`: `{REASONING_EFFORT}`
- `claim_row_sha256`: `{row['claim_row_sha256']}`
- `bibliography_entry_sha256`: `{row['bibliography_entry_sha256']}`
- `source_sha256`: `{row['current_source_sha256']}`
- `schema_sha256`: `{schema_sha}`
- `evidence_path`: `{evidence_rel}`
- `audit_status`: `COMPLETED`

For DIRECT, set `author_inference_assessment` to null. For AUTHOR_INFERENCE, fill the object. Use RFC 3339 UTC. Validate identity, hashes, evidence existence, page bounds, evidence-page count, and schema before finishing. Your final chat response must only say that the candidate is ready; do not reveal the verdict there.
"""


def cmd_make_prompt(row_id: str) -> None:
    verify_inputs(f"before_prompt_{row_id}")
    columns, rows, row = queue_row(row_id)
    if row["queue_status"] == "COMPLETED":
        print(json.dumps({"status": "already_completed", "row_id": row_id}))
        return
    pending_ids = [r["row_id"] for r in rows if r["queue_status"] != "COMPLETED"]
    if not pending_ids or pending_ids[0] != row_id:
        raise SystemExit(f"Strict sequential violation: next row is {pending_ids[0] if pending_ids else 'none'}")
    bib_entry = parse_bib_entries()[row["citation_key"]]
    source_manifest = json.loads(
        (RUN_DIR / f"source_build/{row['citation_key']}/source_build_manifest.json").read_text(encoding="utf-8")
    )
    prompt = prompt_for(row, bib_entry, source_manifest)
    prompt_path = PROMPTS_DIR / f"{row_id}.md"
    atomic_text(prompt_path, prompt)
    row["worker_prompt_path"] = prompt_path.relative_to(RUN_DIR).as_posix()
    row["worker_prompt_sha256"] = sha256_file(prompt_path)
    row["worker_task_name"] = f"current_claim_row_{row_id.rsplit('-', 1)[1]}"
    row["queue_status"] = "PROMPT_READY"
    atomic_tsv(QUEUE_PATH, columns, rows)
    log("primary_prompt_created", row_id=row_id, prompt_sha256=row["worker_prompt_sha256"])
    print(json.dumps({"row_id": row_id, "prompt": row["worker_prompt_path"], "task": row["worker_task_name"]}, indent=2))


def expanded_page_indices(value: str) -> set[int]:
    indices: set[int] = set()
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"(\d+)\s*[-–—]\s*(\d+)", value):
        start, end = int(match.group(1)), int(match.group(2))
        if end < start:
            raise SystemExit("Descending physical-page range")
        indices.update(range(start, end + 1))
        spans.append(match.span())
    residual = value
    for start, end in reversed(spans):
        residual = residual[:start] + " " * (end - start) + residual[end:]
    indices.update(int(item) for item in re.findall(r"\d+", residual))
    return indices


def validate_candidate(result: dict[str, Any], row: dict[str, str]) -> None:
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(result), key=lambda error: list(error.path))
    if errors:
        raise SystemExit("Schema validation failed:\n" + "\n".join(f"{list(e.path)}: {e.message}" for e in errors))

    mappings = {
        "row_id": row["row_id"],
        "claim_id": row["claim_id"],
        "occurrence_id": row["occurrence_id"],
        "citation_key": row["citation_key"],
        "work": row["work"],
        "section": row["section"],
        "paragraph": row["paragraph"],
        "claim_type": row["claim_type"],
        "claim_as_written_pt": row["affirmation_pt"],
        "source_excerpt_pt": row["source_excerpt"],
        "claim_row_sha256": row["claim_row_sha256"],
        "worker_prompt_sha256": row["worker_prompt_sha256"],
        "bibliography_entry_sha256": row["bibliography_entry_sha256"],
        "source_sha256": row["current_source_sha256"],
        "schema_sha256": sha256_file(SCHEMA_PATH),
        "auditor_model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "worker_task_name": row["worker_task_name"],
        "audit_status": "COMPLETED",
    }
    mismatches = {key: {"expected": expected, "actual": result.get(key)} for key, expected in mappings.items() if result.get(key) != expected}
    if mismatches:
        raise SystemExit("Identity mismatch: " + json.dumps(mismatches, ensure_ascii=False))
    if result["pages"] != result["printed_pages"] or not result["pages"].strip():
        raise SystemExit("pages must be non-empty and exactly equal printed_pages")
    if len(re.findall(r"\b[\wÀ-ÿ’'-]+\b", result["evidence_anchor"])) > 12:
        raise SystemExit("Evidence anchor exceeds 12 words")
    if result["fact_checked"] != "SUPPORTED" and not result["issues"]:
        raise SystemExit("Non-SUPPORTED result lacks structured issue")
    if result["claim_type"] == "DIRECT" and result["author_inference_assessment"] is not None:
        raise SystemExit("DIRECT result must use null author_inference_assessment")
    if result["claim_type"] == "AUTHOR_INFERENCE" and result["author_inference_assessment"] is None:
        raise SystemExit("AUTHOR_INFERENCE result lacks assessment")
    for issue in result["issues"]:
        if issue["row_id"] != result["row_id"] or issue["evidence_path"] != result["evidence_path"]:
            raise SystemExit("Issue identity/evidence mismatch")

    evidence = RUN_DIR / result["evidence_path"]
    evidence.resolve().relative_to(RUN_DIR.resolve())
    if not evidence.is_file() or evidence.stat().st_size == 0:
        raise SystemExit(f"Missing evidence: {evidence}")
    source_manifest = json.loads(
        (RUN_DIR / f"source_build/{row['citation_key']}/source_build_manifest.json").read_text(encoding="utf-8")
    )
    source = PROJECT_DIR / source_manifest["source_path"]
    if sha256_file(source) != row["current_source_sha256"]:
        raise SystemExit("Source hash changed")

    if row["source_type"] == "LEGAL_HTML":
        if evidence.suffix != ".html" or result["pdf_page_indices"] != "N/A":
            raise SystemExit("Legal evidence must be HTML with N/A PDF indices")
        if "HTML sem paginação" not in result["printed_pages"]:
            raise SystemExit("Legal pages must state HTML sem paginação")
        evidence.read_text(encoding="utf-8")
    else:
        if evidence.suffix != ".pdf":
            raise SystemExit("PDF source requires PDF evidence")
        source_reader = PdfReader(str(source))
        evidence_reader = PdfReader(str(evidence))
        indices = expanded_page_indices(result["pdf_page_indices"])
        if not indices or min(indices) < 1 or max(indices) > len(source_reader.pages):
            raise SystemExit("Physical indices outside source bounds")
        if len(evidence_reader.pages) != len(indices):
            raise SystemExit("Evidence page count does not equal declared unique physical indices")


def rebuild_audit() -> None:
    columns, rows = read_tsv(AUDIT_PATH)
    result_map: dict[str, dict[str, Any]] = {}
    for path in RESULTS_DIR.glob("ROW-CUR-*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "schema_version" in data:
            result_map[path.stem] = data
    for row in rows:
        result = result_map.get(row["row_id"])
        if not result:
            continue
        issues = result["issues"]
        row.update({
            "fact_checked": result["fact_checked"],
            "pages": result["pages"],
            "audit_status": "COMPLETED",
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
            "audit_origin": "REAUDITED_SOL_MAX_PRIMARY",
        })
    atomic_tsv(AUDIT_PATH, columns, rows)


def cmd_commit(row_id: str) -> None:
    verify_inputs(f"before_commit_{row_id}")
    columns, rows, row = queue_row(row_id)
    if row["queue_status"] != "PROMPT_READY":
        raise SystemExit(f"Row not prompt-ready: {row['queue_status']}")
    candidate_path = CANDIDATES_DIR / f"{row_id}.candidate.json"
    if not candidate_path.is_file():
        raise SystemExit(f"Missing candidate: {candidate_path}")
    result = json.loads(candidate_path.read_text(encoding="utf-8"))
    validate_candidate(result, row)
    atomic_json(RESULTS_DIR / f"{row_id}.json", result)
    row["queue_status"] = "COMPLETED"
    atomic_tsv(QUEUE_PATH, columns, rows)
    rebuild_audit()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    completed = sum(r["queue_status"] == "COMPLETED" for r in rows)
    manifest["completed_primary_rows"] = completed
    manifest["remaining_primary_rows"] = len(rows) - completed
    manifest["status"] = "PRIMARY_COMPLETE" if completed == len(rows) else "PRIMARY_IN_PROGRESS"
    manifest["updated_at"] = utc_now()
    atomic_json(MANIFEST_PATH, manifest)
    log("primary_result_committed", row_id=row_id, completed=completed, remaining=len(rows) - completed)
    verify_inputs(f"after_commit_{row_id}")
    print(json.dumps({"row_id": row_id, "status": "COMPLETED", "remaining": len(rows) - completed}, indent=2))


def cmd_verify() -> None:
    verify_inputs("verify")
    columns, rows = queue()
    audit_columns, audit_rows = read_tsv(AUDIT_PATH)
    errors: list[str] = []
    if len(audit_rows) != 213 or len(audit_columns) != 38:
        errors.append("Working audit must contain 213 rows and 38 columns")
    for row in rows:
        path = RESULTS_DIR / f"{row['row_id']}.json"
        if row["queue_status"] == "COMPLETED":
            if not path.is_file():
                errors.append(f"Missing committed result {row['row_id']}")
            elif "schema_version" in json.loads(path.read_text(encoding="utf-8")):
                validate_candidate(json.loads(path.read_text(encoding="utf-8")), row)
    print(json.dumps({
        "queue_rows": len(rows),
        "completed": sum(r["queue_status"] == "COMPLETED" for r in rows),
        "pending": sum(r["queue_status"] != "COMPLETED" for r in rows),
        "errors": errors,
    }, indent=2))
    if errors:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    prompt = sub.add_parser("make-prompt")
    prompt.add_argument("row_id")
    commit = sub.add_parser("commit")
    commit.add_argument("row_id")
    sub.add_parser("verify")
    args = parser.parse_args()
    if args.command == "init":
        cmd_init()
    elif args.command == "make-prompt":
        cmd_make_prompt(args.row_id)
    elif args.command == "commit":
        cmd_commit(args.row_id)
    else:
        cmd_verify()


if __name__ == "__main__":
    main()
