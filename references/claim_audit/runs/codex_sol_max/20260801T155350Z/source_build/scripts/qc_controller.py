#!/usr/bin/env python3
"""Blind second-review controller for the Codex Sol Max claim audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import controller as core


RUN_DIR = core.RUN_DIR
WORKSPACE = core.WORKSPACE
QC_DIR = RUN_DIR / "quality_control"
QC_SCHEMA_PATH = QC_DIR / "qc_result.schema.json"
QC_QUEUE_PATH = QC_DIR / "queue.tsv"
QC_SELECTION_PATH = QC_DIR / "selection_manifest.json"
QC_RESULTS_DIR = QC_DIR / "results"
QC_CANDIDATES_DIR = QC_DIR / "candidates"
QC_EVIDENCE_DIR = QC_DIR / "evidence_pages"
QC_PROMPTS_DIR = QC_DIR / "prompts"
QC_COMPARISONS_DIR = QC_DIR / "comparisons"
QC_LOG_PATH = QC_DIR / "qc_log.jsonl"

MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "max"
SAMPLE_SEED = f"{core.RUN_ID}|SUPPORTED|10pct"
SAMPLE_RATE = 0.10

QC_QUEUE_COLUMNS = [
    "qc_sequence",
    "row_id",
    "claim_id",
    "occurrence_id",
    "citation_key",
    "claim_type",
    "source_type",
    "source_path",
    "claim_row_sha256",
    "bibliography_entry_sha256",
    "source_sha256",
    "primary_prompt_sha256",
    "primary_result_sha256",
    "selection_reasons",
    "qc_status",
    "qc_prompt_path",
    "qc_prompt_sha256",
    "qc_result_sha256",
    "comparison_status",
]


def append_qc_log(event: str, **payload: Any) -> None:
    item = {"timestamp": core.utc_now(), "event": event, **payload}
    QC_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with QC_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def read_qc_queue() -> tuple[list[str], list[dict[str, str]]]:
    if not QC_QUEUE_PATH.is_file():
        raise SystemExit("Quality-control queue does not exist; run init first")
    with QC_QUEUE_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def load_primary_results() -> list[dict[str, Any]]:
    paths = sorted(core.RESULTS_DIR.glob("ROW-*.json"))
    if len(paths) != 227:
        raise SystemExit(f"Expected 227 primary results before QC; found {len(paths)}")
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    expected = [f"ROW-{index:04d}" for index in range(1, 228)]
    actual = [result.get("row_id") for result in results]
    if actual != expected:
        raise SystemExit("Primary results do not form the exact ROW-0001..ROW-0227 sequence")
    return results


def primary_results_digest(results: list[dict[str, Any]]) -> str:
    snapshot = [
        {
            "row_id": result["row_id"],
            "sha256": core.sha256_file(core.RESULTS_DIR / f"{result['row_id']}.json"),
        }
        for result in results
    ]
    return core.canonical_sha(snapshot)


def mark_qc_stale(reason: str, details: Any) -> None:
    manifest = core.load_manifest()
    manifest["audit_phase"] = "QUALITY_CONTROL"
    manifest["audit_status"] = "STALE_INCOMPLETE"
    qc = manifest.setdefault("quality_control", {})
    qc["status"] = "STALE_INCOMPLETE"
    qc["stale_detected_at"] = core.utc_now()
    qc["stale_reason"] = reason
    qc["stale_details"] = details
    core.save_manifest(manifest)
    append_qc_log("qc_stale_detected", reason=reason, details=details)


def verify_qc_invariants(checkpoint: str) -> None:
    core.verify_authoritative_inputs(f"qc_{checkpoint}")
    manifest = core.load_manifest()
    if manifest.get("model") != MODEL or manifest.get("reasoning_effort") != REASONING_EFFORT:
        raise SystemExit("Run manifest runtime differs from gpt-5.6-sol/max")
    if manifest.get("model_fallback_allowed") is not False:
        raise SystemExit("Run manifest permits model fallback")
    if manifest.get("claude_outputs_read") is not False:
        raise SystemExit("Blind-audit flag is not intact")
    if not QC_QUEUE_PATH.is_file():
        return
    _, rows = read_qc_queue()
    differences: list[dict[str, str]] = []
    for row in rows:
        primary_path = core.RESULTS_DIR / f"{row['row_id']}.json"
        if not primary_path.is_file():
            differences.append({"row_id": row["row_id"], "reason": "primary result missing"})
            continue
        actual = core.sha256_file(primary_path)
        if actual != row["primary_result_sha256"]:
            differences.append(
                {
                    "row_id": row["row_id"],
                    "reason": "primary result hash changed",
                    "expected": row["primary_result_sha256"],
                    "actual": actual,
                }
            )
    if differences:
        mark_qc_stale("PRIMARY_RESULT_SNAPSHOT_CHANGED", differences)
        raise SystemExit("Primary result snapshot changed during QC; run marked stale/incomplete")


def build_qc_schema() -> dict[str, Any]:
    schema = json.loads(core.SCHEMA_PATH.read_text(encoding="utf-8"))
    schema["title"] = "Blind Codex quality-control claim result"
    evidence_pattern = r"^quality_control/evidence_pages/ROW-[0-9]{4}\.(pdf|html)$"
    schema["properties"]["evidence_path"]["pattern"] = evidence_pattern
    defs = schema.get("$defs") or schema.get("definitions")
    defs["issue"]["properties"]["evidence_path"]["pattern"] = evidence_pattern
    return schema


def supported_sample(results: list[dict[str, Any]]) -> list[str]:
    supported = [result for result in results if result["fact_checked"] == "SUPPORTED"]
    sample_n = math.ceil(len(supported) * SAMPLE_RATE)

    def score(result: dict[str, Any]) -> str:
        payload = f"{SAMPLE_SEED}|{result['row_id']}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    return [result["row_id"] for result in sorted(supported, key=score)[:sample_n]]


def selection_reasons(result: dict[str, Any], sampled: set[str]) -> list[str]:
    reasons: list[str] = []
    if result["fact_checked"] != "SUPPORTED":
        reasons.append("NON_SUPPORTED")
    if result["confidence"] in {"LOW", "MEDIUM"}:
        reasons.append("LOW_OR_MEDIUM_CONFIDENCE")
    issue_codes = {issue["issue_code"] for issue in result.get("issues", [])}
    if result.get("source_version_match") != "MATCH" or "PDF_VERSION_MISMATCH" in issue_codes:
        reasons.append("SOURCE_VERSION_ISSUE")
    if result["row_id"] in sampled:
        reasons.append("DETERMINISTIC_SUPPORTED_SAMPLE")
    return reasons


def cmd_init() -> None:
    verify_qc_invariants("before_init")
    results = load_primary_results()
    primary_rows = {row["row_id"]: row for row in core.queue_rows()[1]}
    sampled_rows = supported_sample(results)
    sampled = set(sampled_rows)

    QC_DIR.mkdir(parents=True, exist_ok=True)
    for directory in (
        QC_RESULTS_DIR,
        QC_CANDIDATES_DIR,
        QC_EVIDENCE_DIR,
        QC_PROMPTS_DIR,
        QC_COMPARISONS_DIR,
        QC_DIR / "worker_receipts",
        QC_DIR / "aborted_attempts",
        QC_DIR / "renders",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    schema = build_qc_schema()
    core.atomic_write_json(QC_SCHEMA_PATH, schema)
    schema_sha = core.sha256_file(QC_SCHEMA_PATH)

    selected: list[tuple[dict[str, Any], list[str]]] = []
    for result in results:
        reasons = selection_reasons(result, sampled)
        if reasons:
            selected.append((result, reasons))

    if len(sampled_rows) != math.ceil(131 * SAMPLE_RATE):
        raise SystemExit("Deterministic SUPPORTED sample size is inconsistent")

    queue_rows: list[dict[str, str]] = []
    primary_snapshot: list[dict[str, str]] = []
    for sequence, (result, reasons) in enumerate(selected, start=1):
        row_id = result["row_id"]
        primary = primary_rows[row_id]
        primary_result_path = core.RESULTS_DIR / f"{row_id}.json"
        primary_result_sha = core.sha256_file(primary_result_path)
        primary_snapshot.append({"row_id": row_id, "sha256": primary_result_sha})
        queue_rows.append(
            {
                "qc_sequence": str(sequence),
                "row_id": row_id,
                "claim_id": result["claim_id"],
                "occurrence_id": result["occurrence_id"],
                "citation_key": result["citation_key"],
                "claim_type": result["claim_type"],
                "source_type": primary["source_type"],
                "source_path": primary["source_path"],
                "claim_row_sha256": result["claim_row_sha256"],
                "bibliography_entry_sha256": result["bibliography_entry_sha256"],
                "source_sha256": result["source_sha256"],
                "primary_prompt_sha256": primary["worker_prompt_sha256"],
                "primary_result_sha256": primary_result_sha,
                "selection_reasons": ";".join(reasons),
                "qc_status": "PENDING",
                "qc_prompt_path": "",
                "qc_prompt_sha256": "",
                "qc_result_sha256": "",
                "comparison_status": "",
            }
        )

    if QC_QUEUE_PATH.exists():
        _, existing = read_qc_queue()
        frozen_existing = [
            {key: row[key] for key in QC_QUEUE_COLUMNS[:14]}
            for row in existing
        ]
        frozen_new = [
            {key: row[key] for key in QC_QUEUE_COLUMNS[:14]}
            for row in queue_rows
        ]
        if frozen_existing != frozen_new:
            mark_qc_stale("QC_SELECTION_CHANGED", {"existing": len(existing), "new": len(queue_rows)})
            raise SystemExit("Existing QC selection differs from deterministic recomputation")
        queue_rows = existing
    else:
        core.atomic_write_tsv(QC_QUEUE_PATH, queue_rows, QC_QUEUE_COLUMNS)

    reason_counts = {
        reason: sum(reason in reasons for _, reasons in selected)
        for reason in (
            "NON_SUPPORTED",
            "LOW_OR_MEDIUM_CONFIDENCE",
            "SOURCE_VERSION_ISSUE",
            "DETERMINISTIC_SUPPORTED_SAMPLE",
        )
    }
    selection_manifest = {
        "version": "1.0.0",
        "created_at": core.utc_now(),
        "selection_is_hidden_from_workers": True,
        "sample_algorithm": "Sort SUPPORTED rows by SHA-256(seed + '|' + row_id), then take ceil(N * 0.10)",
        "sample_seed": SAMPLE_SEED,
        "sample_rate": SAMPLE_RATE,
        "supported_population": 131,
        "supported_sample_size": len(sampled_rows),
        "supported_sample_rows_in_hash_order": sampled_rows,
        "criteria_counts_before_union": reason_counts,
        "unique_qc_rows": len(queue_rows),
        "primary_results_snapshot": primary_snapshot,
        "primary_results_snapshot_digest": core.canonical_sha(primary_snapshot),
        "qc_schema_path": QC_SCHEMA_PATH.relative_to(RUN_DIR).as_posix(),
        "qc_schema_sha256": schema_sha,
    }
    core.atomic_write_json(QC_SELECTION_PATH, selection_manifest)

    manifest = core.load_manifest()
    completed = len(list(QC_RESULTS_DIR.glob("ROW-*.json")))
    manifest["audit_phase"] = "QUALITY_CONTROL"
    manifest["audit_status"] = "QUALITY_CONTROL_IN_PROGRESS"
    manifest["quality_control"] = {
        "status": "IN_PROGRESS",
        "blind_second_review": True,
        "reviewer_model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "model_fallback_allowed": False,
        "max_concurrent_reviewers": 1,
        "selection_manifest_path": QC_SELECTION_PATH.relative_to(RUN_DIR).as_posix(),
        "selection_manifest_sha256": core.sha256_file(QC_SELECTION_PATH),
        "queue_path": QC_QUEUE_PATH.relative_to(RUN_DIR).as_posix(),
        "qc_schema_path": QC_SCHEMA_PATH.relative_to(RUN_DIR).as_posix(),
        "qc_schema_sha256": schema_sha,
        "unique_rows_selected": len(queue_rows),
        "completed_reviews": completed,
        "remaining_reviews": len(queue_rows) - completed,
        "disagreements": sum(row.get("comparison_status") == "NEEDS_ADJUDICATION" for row in queue_rows),
        "primary_results_snapshot_digest": selection_manifest["primary_results_snapshot_digest"],
        "started_at": manifest.get("quality_control", {}).get("started_at") or core.utc_now(),
        "completed_at": None,
    }
    core.save_manifest(manifest)
    append_qc_log(
        "qc_initialized",
        unique_rows=len(queue_rows),
        reason_counts=reason_counts,
        supported_sample_rows=sampled_rows,
        schema_sha256=schema_sha,
    )
    verify_qc_invariants("after_init")
    print(json.dumps(selection_manifest, ensure_ascii=False, indent=2))


def queue_row(row_id: str) -> tuple[list[str], list[dict[str, str]], dict[str, str]]:
    columns, rows = read_qc_queue()
    matches = [row for row in rows if row["row_id"] == row_id]
    if len(matches) != 1:
        raise SystemExit(f"Row is not selected for QC: {row_id}")
    return columns, rows, matches[0]


def transform_primary_prompt(row_id: str, task_name: str) -> str:
    primary_prompt_path = core.SOURCE_BUILD / "prompts" / f"{row_id}.md"
    if not primary_prompt_path.is_file():
        raise SystemExit(f"Primary blind prompt is missing: {primary_prompt_path}")
    text = primary_prompt_path.read_text(encoding="utf-8")
    if '"fact_checked": ""' not in text or '"pages": ""' not in text:
        raise SystemExit("Primary prompt is not judgment-blind")
    task_match = re.search(r"^- Worker task name: `([^`]+)`$", text, flags=re.MULTILINE)
    if not task_match:
        raise SystemExit("Primary prompt lacks a worker task name")
    old_task_name = task_match.group(1)
    old_schema_sha = core.sha256_file(core.SCHEMA_PATH)
    new_schema_sha = core.sha256_file(QC_SCHEMA_PATH)
    suffix = "html" if "Exact evidence HTML" in text else "pdf"

    text = text.replace(f"# Isolated claim audit task: {row_id}", f"# Blind second-review task: {row_id}")
    text = text.replace(old_task_name, task_name)
    text = text.replace("claim_result.schema.json", "quality_control/qc_result.schema.json")
    text = text.replace(
        f"source_build/prompts/{row_id}.md",
        f"quality_control/prompts/{row_id}.md",
    )
    text = text.replace(
        f"source_build/candidates/{row_id}.candidate.json",
        f"quality_control/candidates/{row_id}.candidate.json",
    )
    text = text.replace(
        f"evidence_pages/{row_id}.{suffix}",
        f"quality_control/evidence_pages/{row_id}.{suffix}",
    )
    text = text.replace(
        f"source_build/renders/{row_id}/",
        f"quality_control/renders/{row_id}/",
    )
    text = text.replace(old_schema_sha, new_schema_sha)
    text = text.replace(
        f"Do not write the final `results/{row_id}.json`; the controller validates and commits it atomically.",
        f"Do not write the final `quality_control/results/{row_id}.json`; the QC controller validates and commits it atomically.",
    )

    blind_gate = f"""
## Blind second-review gate

This is an independent second assessment. Before issuing your own judgment, do not read or list any primary result, primary evidence file, primary render, issue table, audited inventory, calibration receipt, report, audit log, quality-control queue, selection manifest, comparison, or another QC result. In particular, do not access `results/`, `evidence_pages/`, `source_build/renders/`, `issues.tsv`, `claim_inventory_audited.tsv`, `AUDIT_REPORT.md`, `audit_log.jsonl`, or any path under `quality_control/` except this prompt, `quality_control/qc_result.schema.json`, and your three authorized write locations.

You are not told why this row was selected. Selection conveys no information about the primary verdict. Form an independent verdict from the claim, exact stored source, frozen bibliography entry, claim-neutral source-wide index, and four-page splits only. Do not mention or attempt to infer a primary assessment.

For a PDF row, physical indices are 1-based and range endpoints are inclusive. Immediately before finishing, expand the unique physical indices declared in pdf_page_indices and count the pages in the written QC evidence PDF. The two counts must be identical. Do not include an adjacent context page unless it is both genuinely evidentiary and declared in pdf_page_indices.
"""
    marker = "## Mandatory runtime\n"
    if marker not in text:
        raise SystemExit("Prompt transformation marker is missing")
    text = text.replace(marker, blind_gate + "\n" + marker, 1)
    text = text.replace(
        "The controller already generated new run-specific four-page splits and a run-specific page-text index. Do not use any preexisting extract, split, summary, candidate page, or other auditor's work.",
        "The controller already generated claim-neutral, run-specific four-page splits and a source-wide page-text index. These contain no row verdict or rationale and are authorized for location only. Do not read any per-row primary evidence, render, summary, candidate, or result.",
    )
    text = text.replace(
        "Do not read `results/`, other prompts, other candidates, `issues.tsv`, `claim_inventory_audited.tsv`, `AUDIT_REPORT.md`, or any Claude path.",
        "Do not read primary `results/`, primary `evidence_pages/`, primary renders, other prompts, other candidates, `issues.tsv`, `claim_inventory_audited.tsv`, `AUDIT_REPORT.md`, QC selection/comparison/result files, or any Claude path.",
    )
    text = text.replace(
        "Produce one JSON object conforming exactly to `quality_control/qc_result.schema.json`.",
        "Produce one independent JSON object conforming exactly to `quality_control/qc_result.schema.json`.",
    )
    return text


def cmd_make_prompt(row_id: str) -> None:
    verify_qc_invariants(f"before_prompt_{row_id}")
    columns, rows, selected = queue_row(row_id)
    if (QC_RESULTS_DIR / f"{row_id}.json").exists():
        raise SystemExit(f"QC result already exists: {row_id}")
    task_name = f"qc_row_{int(row_id.split('-')[1]):04d}"
    prompt_text = transform_primary_prompt(row_id, task_name)
    prompt_path = QC_PROMPTS_DIR / f"{row_id}.md"
    core.atomic_write_text(prompt_path, prompt_text)
    prompt_sha = core.sha256_file(prompt_path)
    for row in rows:
        if row["row_id"] == row_id:
            row["qc_status"] = "PROMPT_READY"
            row["qc_prompt_path"] = prompt_path.relative_to(RUN_DIR).as_posix()
            row["qc_prompt_sha256"] = prompt_sha
    core.atomic_write_tsv(QC_QUEUE_PATH, rows, columns)
    append_qc_log(
        "qc_prompt_created",
        row_id=row_id,
        task_name=task_name,
        prompt_path=prompt_path.relative_to(RUN_DIR).as_posix(),
        prompt_sha256=prompt_sha,
    )
    verify_qc_invariants(f"after_prompt_{row_id}")
    print(json.dumps({"row_id": row_id, "task_name": task_name, "prompt_sha256": prompt_sha}, indent=2))


def cmd_retask_prompt(row_id: str, task_name: str) -> None:
    verify_qc_invariants(f"before_retask_{row_id}")
    if not re.fullmatch(r"[a-z0-9_]+", task_name):
        raise SystemExit("Invalid QC worker task name")
    columns, rows, selected = queue_row(row_id)
    prompt_path = QC_PROMPTS_DIR / f"{row_id}.md"
    if not prompt_path.is_file():
        raise SystemExit("QC prompt does not exist")
    text = prompt_path.read_text(encoding="utf-8")
    match = re.search(r"^- Worker task name: `([^`]+)`$", text, flags=re.MULTILINE)
    if not match:
        raise SystemExit("QC prompt lacks worker task name")
    text = text.replace(match.group(1), task_name)
    retry_note = """

## Retry validation note

This is a fully fresh blind assessment. Do not inspect any archived attempt. Before writing, choose an evidence anchor of at most 8 whitespace-delimited source tokens. For PDF evidence, expand every physical range and verify that the QC evidence PDF contains exactly one page per unique declared physical index. Recheck all identity hashes and authorized paths.

Physical PDF indices are 1-based and range endpoints are inclusive. Do not add an adjacent context page to the evidence PDF unless that physical index is also declared in the pdf_page_indices field and genuinely belongs to the evidence range. Immediately before finishing, count the pages in the written evidence PDF and compare that integer with the number of unique expanded physical indices; if they differ, rebuild the evidence PDF or correct the declared range before writing the candidate JSON.
"""
    text = text.rstrip() + retry_note + "\n"
    core.atomic_write_text(prompt_path, text)
    prompt_sha = core.sha256_file(prompt_path)
    for row in rows:
        if row["row_id"] == row_id:
            row["qc_status"] = "PROMPT_READY"
            row["qc_prompt_sha256"] = prompt_sha
    core.atomic_write_tsv(QC_QUEUE_PATH, rows, columns)
    append_qc_log("qc_prompt_retasked", row_id=row_id, task_name=task_name, prompt_sha256=prompt_sha)
    verify_qc_invariants(f"after_retask_{row_id}")
    print(json.dumps({"row_id": row_id, "task_name": task_name, "prompt_sha256": prompt_sha}, indent=2))


def expand_pdf_indices(index_text: str) -> set[int]:
    indices: set[int] = set()
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"(\d+)\s*[-\u2013\u2014]\s*(\d+)", index_text):
        start, end = int(match.group(1)), int(match.group(2))
        if end < start:
            raise SystemExit("Physical PDF page range is descending")
        indices.update(range(start, end + 1))
        spans.append(match.span())
    residual = index_text
    for start, end in reversed(spans):
        residual = residual[:start] + " " * (end - start) + residual[end:]
    indices.update(int(value) for value in re.findall(r"\d+", residual))
    return indices


def validate_qc_result(result: dict[str, Any], selected: dict[str, str]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise SystemExit("jsonschema is required for QC validation") from exc

    schema = json.loads(QC_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(result), key=lambda item: list(item.path))
    if errors:
        details = "\n".join(f"{list(error.path)}: {error.message}" for error in errors)
        raise SystemExit(f"QC schema validation failed:\n{details}")

    primary = json.loads((core.RESULTS_DIR / f"{selected['row_id']}.json").read_text(encoding="utf-8"))
    prompt_path = RUN_DIR / selected["qc_prompt_path"]
    prompt_text = prompt_path.read_text(encoding="utf-8")
    task_match = re.search(r"^- Worker task name: `([^`]+)`$", prompt_text, flags=re.MULTILINE)
    if not task_match:
        raise SystemExit("QC prompt does not declare a task name")
    mappings = {
        "row_id": selected["row_id"],
        "claim_id": selected["claim_id"],
        "occurrence_id": selected["occurrence_id"],
        "citation_key": selected["citation_key"],
        "work": primary["work"],
        "section": primary["section"],
        "paragraph": primary["paragraph"],
        "claim_type": selected["claim_type"],
        "claim_as_written_pt": primary["claim_as_written_pt"],
        "source_excerpt_pt": primary["source_excerpt_pt"],
        "claim_row_sha256": selected["claim_row_sha256"],
        "worker_prompt_sha256": selected["qc_prompt_sha256"],
        "bibliography_entry_sha256": selected["bibliography_entry_sha256"],
        "source_sha256": selected["source_sha256"],
        "schema_sha256": core.sha256_file(QC_SCHEMA_PATH),
        "auditor_model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "worker_task_name": task_match.group(1),
    }
    mismatches = {
        key: {"expected": expected, "actual": result.get(key)}
        for key, expected in mappings.items()
        if result.get(key) != expected
    }
    if mismatches:
        raise SystemExit(f"QC identity/hash mismatch: {json.dumps(mismatches, ensure_ascii=False, indent=2)}")
    if result["pages"] != result["printed_pages"]:
        raise SystemExit("QC pages must exactly equal printed_pages")
    anchor_words = re.findall(r"\b[\wÀ-ÿ’'-]+\b", result["evidence_anchor"], flags=re.UNICODE)
    if len(anchor_words) > 12:
        raise SystemExit(f"QC evidence anchor has {len(anchor_words)} words; maximum is 12")
    if result["fact_checked"] != "SUPPORTED" and not result["issues"]:
        raise SystemExit("Every non-SUPPORTED QC result requires a structured issue")
    issue_codes = {issue["issue_code"] for issue in result["issues"]}
    if result["source_version_match"] == "PDF_VERSION_MISMATCH" and "PDF_VERSION_MISMATCH" not in issue_codes:
        raise SystemExit("QC PDF_VERSION_MISMATCH classification requires a matching issue")
    if result["claim_type"] == "AUTHOR_INFERENCE" and result["author_inference_assessment"] is None:
        raise SystemExit("QC AUTHOR_INFERENCE requires the three-part assessment")
    if result["claim_type"] == "DIRECT" and result["author_inference_assessment"] is not None:
        raise SystemExit("QC DIRECT result must set author_inference_assessment to null")

    suffix = "html" if selected["source_type"] == "LEGAL_HTML" else "pdf"
    expected_evidence = f"quality_control/evidence_pages/{selected['row_id']}.{suffix}"
    if result["evidence_path"] != expected_evidence:
        raise SystemExit(f"Unexpected QC evidence path: {result['evidence_path']}")
    for issue in result["issues"]:
        if issue["row_id"] != result["row_id"] or issue["evidence_path"] != result["evidence_path"]:
            raise SystemExit("QC issue row/evidence identity mismatch")

    evidence_path = RUN_DIR / result["evidence_path"]
    try:
        evidence_path.resolve().relative_to(QC_DIR.resolve())
    except ValueError as exc:
        raise SystemExit("QC evidence path escapes quality_control") from exc
    if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
        raise SystemExit(f"QC evidence file is missing or empty: {evidence_path}")

    if selected["source_type"] == "LEGAL_HTML":
        if result["pdf_page_indices"] != "N/A":
            raise SystemExit("Legal QC evidence must set pdf_page_indices to N/A")
        if "HTML sem paginação" not in result["printed_pages"]:
            raise SystemExit("Legal QC printed_pages must state HTML sem paginação")
        if not re.search(r"\bart\.?\s*\d+", result["source_locator"], flags=re.IGNORECASE):
            raise SystemExit("Legal QC source_locator must identify an exact article")
        evidence_text = evidence_path.read_text(encoding="utf-8", errors="strict")
        if not re.search(r"<html\b", evidence_text, flags=re.IGNORECASE):
            raise SystemExit("Legal QC evidence must be a valid HTML document")
    else:
        evidence_reader = core.PdfReader(str(evidence_path))
        source_path = WORKSPACE / selected["source_path"]
        source_page_count = len(core.PdfReader(str(source_path)).pages)
        indices = expand_pdf_indices(result["pdf_page_indices"])
        if not indices or min(indices) < 1 or max(indices) > source_page_count:
            raise SystemExit(f"QC physical indices outside source bounds 1-{source_page_count}")
        if len(evidence_reader.pages) != len(indices):
            raise SystemExit(
                f"QC evidence PDF page count {len(evidence_reader.pages)} does not match declared indices ({len(indices)})"
            )


def compare_assessments(primary: dict[str, Any], qc: dict[str, Any]) -> dict[str, Any]:
    disagreements: list[dict[str, Any]] = []

    def add(code: str, primary_value: Any, qc_value: Any) -> None:
        if primary_value != qc_value:
            disagreements.append({"code": code, "primary": primary_value, "qc": qc_value})

    add("VERDICT_DISAGREEMENT", primary["fact_checked"], qc["fact_checked"])
    add("CONFIDENCE_DISAGREEMENT", primary["confidence"], qc["confidence"])
    add("SOURCE_VERSION_CLASS_DISAGREEMENT", primary["source_version_match"], qc["source_version_match"])
    primary_date_tokens = tuple(sorted(set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", primary["source_version_date"]))))
    qc_date_tokens = tuple(sorted(set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", qc["source_version_date"]))))
    dates_equivalent = bool(primary_date_tokens) and primary_date_tokens == qc_date_tokens
    if not dates_equivalent:
        add("SOURCE_VERSION_DATE_DISAGREEMENT", primary["source_version_date"], qc["source_version_date"])
    add(
        "ISSUE_CODE_DISAGREEMENT",
        sorted({issue["issue_code"] for issue in primary.get("issues", [])}),
        sorted({issue["issue_code"] for issue in qc.get("issues", [])}),
    )
    add("NEEDS_NEW_SOURCE_DISAGREEMENT", primary["needs_new_source"], qc["needs_new_source"])
    if primary["claim_type"] == "AUTHOR_INFERENCE":
        primary_inference = primary["author_inference_assessment"] or {}
        qc_inference = qc["author_inference_assessment"] or {}
        for field in (
            "factual_premises_supported",
            "inference_reasonably_follows",
            "source_explicitly_states_inference",
        ):
            add(f"AUTHOR_INFERENCE_{field.upper()}_DISAGREEMENT", primary_inference.get(field), qc_inference.get(field))

    status = "NEEDS_ADJUDICATION" if disagreements else "AGREES"
    return {
        "row_id": primary["row_id"],
        "compared_at": core.utc_now(),
        "comparison_status": status,
        "primary_result_sha256": core.sha256_file(core.RESULTS_DIR / f"{primary['row_id']}.json"),
        "qc_result_sha256": core.sha256_file(QC_RESULTS_DIR / f"{primary['row_id']}.json"),
        "primary_verdict": primary["fact_checked"],
        "qc_verdict": qc["fact_checked"],
        "disagreements": disagreements,
    }


def cmd_rebuild_comparisons() -> None:
    """Recompute completed comparisons without exposing primary results to reviewers."""
    verify_qc_invariants("before_rebuild_comparisons")
    columns, rows = read_qc_queue()
    completed = 0
    disagreements = 0
    for row in rows:
        row_id = row["row_id"]
        result_path = QC_RESULTS_DIR / f"{row_id}.json"
        if not result_path.is_file():
            continue
        primary = json.loads((core.RESULTS_DIR / f"{row_id}.json").read_text(encoding="utf-8"))
        review = json.loads(result_path.read_text(encoding="utf-8"))
        comparison = compare_assessments(primary, review)
        core.atomic_write_json(QC_COMPARISONS_DIR / f"{row_id}.json", comparison)
        row["comparison_status"] = comparison["comparison_status"]
        row["qc_result_sha256"] = core.sha256_file(result_path)
        completed += 1
        disagreements += comparison["comparison_status"] == "NEEDS_ADJUDICATION"
    core.atomic_write_tsv(QC_QUEUE_PATH, rows, columns)
    manifest = core.load_manifest()
    qc_manifest = manifest.setdefault("quality_control", {})
    qc_manifest["completed_reviews"] = completed
    qc_manifest["remaining_reviews"] = len(rows) - completed
    qc_manifest["disagreements"] = disagreements
    qc_manifest["comparison_policy"] = {
        "version": "1.1.0",
        "date_equivalence": "Equal non-empty sets of ISO YYYY-MM-DD tokens are treated as equivalent regardless of explanatory text order.",
        "controller_sha256": core.sha256_file(Path(__file__)),
    }
    core.save_manifest(manifest)
    append_qc_log(
        "qc_comparisons_rebuilt",
        completed=completed,
        disagreements=disagreements,
        rule="ISO date token sets are equivalent regardless of explanatory text order",
    )
    verify_qc_invariants("after_rebuild_comparisons")
    print(
        json.dumps(
            {
                "status": "comparisons_rebuilt",
                "completed": completed,
                "disagreements": disagreements,
            },
            indent=2,
        )
    )


def cmd_commit(row_id: str) -> None:
    verify_qc_invariants(f"before_commit_{row_id}")
    columns, rows, selected = queue_row(row_id)
    sequence = int(selected["qc_sequence"])
    expected_previous = [row["row_id"] for row in rows if int(row["qc_sequence"]) < sequence]
    completed = [path.stem for path in sorted(QC_RESULTS_DIR.glob("ROW-*.json"))]
    if completed != expected_previous:
        raise SystemExit(f"Strict QC sequence violation: completed={completed}, expected={expected_previous}")
    if selected["qc_status"] != "PROMPT_READY":
        raise SystemExit(f"QC candidate is not eligible for commit: {selected['qc_status']}")
    candidate_path = QC_CANDIDATES_DIR / f"{row_id}.candidate.json"
    if not candidate_path.is_file():
        raise SystemExit(f"QC candidate does not exist: {candidate_path}")
    result = json.loads(candidate_path.read_text(encoding="utf-8"))
    validate_qc_result(result, selected)

    result_path = QC_RESULTS_DIR / f"{row_id}.json"
    core.atomic_write_json(result_path, result)
    primary = json.loads((core.RESULTS_DIR / f"{row_id}.json").read_text(encoding="utf-8"))
    comparison = compare_assessments(primary, result)
    comparison_path = QC_COMPARISONS_DIR / f"{row_id}.json"
    core.atomic_write_json(comparison_path, comparison)

    for row in rows:
        if row["row_id"] == row_id:
            row["qc_status"] = "COMPLETED"
            row["qc_result_sha256"] = core.sha256_file(result_path)
            row["comparison_status"] = comparison["comparison_status"]
    core.atomic_write_tsv(QC_QUEUE_PATH, rows, columns)

    completed_count = len(list(QC_RESULTS_DIR.glob("ROW-*.json")))
    disagreements = sum(row["comparison_status"] == "NEEDS_ADJUDICATION" for row in rows)
    manifest = core.load_manifest()
    qc_manifest = manifest.setdefault("quality_control", {})
    qc_manifest["completed_reviews"] = completed_count
    qc_manifest["remaining_reviews"] = len(rows) - completed_count
    qc_manifest["disagreements"] = disagreements
    if completed_count == len(rows):
        qc_manifest["status"] = "COMPLETE"
        qc_manifest["completed_at"] = core.utc_now()
        manifest["audit_phase"] = "FINALIZATION"
        manifest["audit_status"] = (
            "QUALITY_CONTROL_COMPLETE_NEEDS_ADJUDICATION" if disagreements else "QUALITY_CONTROL_COMPLETE"
        )
        manifest["timestamps"]["quality_control_completed_at"] = qc_manifest["completed_at"]
    core.save_manifest(manifest)
    append_qc_log(
        "qc_result_validated_and_committed",
        row_id=row_id,
        sequence=sequence,
        result_sha256=core.sha256_file(result_path),
        evidence_path=result["evidence_path"],
        evidence_sha256=core.sha256_file(RUN_DIR / result["evidence_path"]),
        comparison_status=comparison["comparison_status"],
        disagreement_codes=[item["code"] for item in comparison["disagreements"]],
        completed=completed_count,
        total=len(rows),
    )
    verify_qc_invariants(f"after_commit_{row_id}")
    print(
        json.dumps(
            {
                "status": "committed",
                "row_id": row_id,
                "completed": completed_count,
                "total": len(rows),
                "comparison_status": comparison["comparison_status"],
            },
            indent=2,
        )
    )


def cmd_verify() -> None:
    verify_qc_invariants("manual_verify")
    _, rows = read_qc_queue()
    completed: list[str] = []
    disagreements: list[str] = []
    for row in rows:
        result_path = QC_RESULTS_DIR / f"{row['row_id']}.json"
        if not result_path.is_file():
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        validate_qc_result(result, row)
        comparison_path = QC_COMPARISONS_DIR / f"{row['row_id']}.json"
        if not comparison_path.is_file():
            raise SystemExit(f"QC comparison is missing: {row['row_id']}")
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        if comparison["qc_result_sha256"] != core.sha256_file(result_path):
            raise SystemExit(f"QC comparison hash mismatch: {row['row_id']}")
        completed.append(row["row_id"])
        if comparison["comparison_status"] == "NEEDS_ADJUDICATION":
            disagreements.append(row["row_id"])
    print(
        json.dumps(
            {
                "selected": len(rows),
                "completed": len(completed),
                "remaining": len(rows) - len(completed),
                "disagreements": len(disagreements),
                "disagreement_rows": disagreements,
                "claude_outputs_read": core.load_manifest()["claude_outputs_read"],
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")
    make_parser = subparsers.add_parser("make-prompt")
    make_parser.add_argument("row_id")
    retask_parser = subparsers.add_parser("retask-prompt")
    retask_parser.add_argument("row_id")
    retask_parser.add_argument("task_name")
    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("row_id")
    subparsers.add_parser("rebuild-comparisons")
    subparsers.add_parser("verify")
    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "make-prompt":
        cmd_make_prompt(args.row_id)
    elif args.command == "retask-prompt":
        cmd_retask_prompt(args.row_id, args.task_name)
    elif args.command == "commit":
        cmd_commit(args.row_id)
    elif args.command == "rebuild-comparisons":
        cmd_rebuild_comparisons()
    elif args.command == "verify":
        cmd_verify()


if __name__ == "__main__":
    main()
