#!/usr/bin/env python3
"""Build calibration-only artifacts from four validated row results."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PyPDF2 import PdfReader


RUN_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = RUN_DIR / "results"
TABLE_PATH = RUN_DIR / "calibration_table.tsv"
RECEIPT_PATH = RUN_DIR / "CALIBRATION_RECEIPT.md"
REPORT_PATH = RUN_DIR / "AUDIT_REPORT.md"
MANIFEST_PATH = RUN_DIR / "run_manifest.json"
LOG_PATH = RUN_DIR / "audit_log.jsonl"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, content: str) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def atomic_json(path: Path, value: object) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> None:
    expected = [f"ROW-{number:04d}" for number in range(1, 5)]
    result_paths = sorted(RESULTS_DIR.glob("ROW-*.json"))
    if [path.stem for path in result_paths] != expected:
        raise SystemExit(f"Expected exactly {expected}, found {[path.stem for path in result_paths]}")
    results = [json.loads(path.read_text(encoding="utf-8")) for path in result_paths]
    if any(result["audit_status"] != "COMPLETED" for result in results):
        raise SystemExit("All calibration results must be COMPLETED")
    if any(result["citation_key"] != "bick_rapid_2024" or result["occurrence_id"] != "CIT-001" for result in results):
        raise SystemExit("Unexpected relationship in calibration results")
    if any(result["source_version_match"] != "PDF_VERSION_MISMATCH" for result in results):
        raise SystemExit("Bick source-version classification is inconsistent across calibration rows")
    row4 = next(result for result in results if result["row_id"] == "ROW-0004")
    if row4["pdf_page_indices"] != "1, 3–4":
        raise SystemExit("ROW-0004 evidence must exclude the physical abstract page")

    table_fields = [
        "row_id", "claim_id", "citation_key", "occurrence_id", "claim_type", "verdict", "confidence",
        "printed_pages", "pdf_page_indices", "source_locator", "source_version", "source_version_match",
        "evidence_anchor", "evidence_summary_pt", "direct_evidence_vs_inference_pt", "issue_codes",
        "issue_severities", "evidence_path", "recommended_revision_pt",
    ]
    table_rows = []
    for result in results:
        table_rows.append({
            "row_id": result["row_id"],
            "claim_id": result["claim_id"],
            "citation_key": result["citation_key"],
            "occurrence_id": result["occurrence_id"],
            "claim_type": result["claim_type"],
            "verdict": result["fact_checked"],
            "confidence": result["confidence"],
            "printed_pages": result["printed_pages"],
            "pdf_page_indices": result["pdf_page_indices"],
            "source_locator": result["source_locator"],
            "source_version": result["source_version"],
            "source_version_match": result["source_version_match"],
            "evidence_anchor": result["evidence_anchor"],
            "evidence_summary_pt": result["evidence_summary_pt"],
            "direct_evidence_vs_inference_pt": result["direct_evidence_vs_inference_pt"],
            "issue_codes": ";".join(issue["issue_code"] for issue in result["issues"]),
            "issue_severities": ";".join(issue["severity"] for issue in result["issues"]),
            "evidence_path": result["evidence_path"],
            "recommended_revision_pt": result["recommended_revision_pt"],
        })
    fd, temp_name = tempfile.mkstemp(prefix=f".{TABLE_PATH.name}.", dir=TABLE_PATH.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, delimiter="\t", fieldnames=table_fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(table_rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, TABLE_PATH)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise

    verdict_counts = Counter(result["fact_checked"] for result in results)
    evidence_manifest = []
    for result in results:
        evidence_path = RUN_DIR / result["evidence_path"]
        evidence_manifest.append({
            "row_id": result["row_id"],
            "path": result["evidence_path"],
            "sha256": sha(evidence_path),
            "bytes": evidence_path.stat().st_size,
            "pages": len(PdfReader(str(evidence_path)).pages),
            "source_pdf_page_indices": result["pdf_page_indices"],
        })

    lines = [
        "# Bick Calibration Receipt",
        "",
        "> Status: calibration complete; remaining 223 rows are blocked pending explicit user approval.",
        "",
        "## Runtime and integrity",
        "",
        "- Model: `gpt-5.6-sol`",
        "- Reasoning effort: `max`",
        "- Model fallback: disabled",
        "- Semantic workers: four fresh contexts, one active at a time",
        "- Authoritative inputs: unchanged at the final calibration checkpoint",
        "- Claude audit outputs read: no",
        "",
        "## Source version gate",
        "",
        "The stored file is **Federal Reserve Bank of St. Louis Working Paper 2024-027F, revised 27 October 2025**. The frozen BibLaTeX entry records Working Paper `2024-027` with date `2024`. All four rows therefore carry `PDF_VERSION_MISMATCH`; substantive support was judged separately against the stored 2025 revision and its own pagination.",
        "",
        "## Calibration table",
        "",
        "| Row | Claim | Type | Verdict | Printed pages | PDF pages | Confidence | Issues |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        issues = ", ".join(f"{issue['issue_code']} ({issue['severity']})" for issue in result["issues"]) or "None"
        lines.append(
            f"| `{result['row_id']}` | `{result['claim_id']}` | `{result['claim_type']}` | `{result['fact_checked']}` | "
            f"{escape_md(result['printed_pages'])} | {escape_md(result['pdf_page_indices'])} | `{result['confidence']}` | {escape_md(issues)} |"
        )
    lines.extend(["", "Full temporary table: [`calibration_table.tsv`](calibration_table.tsv)", ""])

    for result in results:
        lines.extend([
            f"## {result['row_id']} / {result['claim_id']}",
            "",
            f"- **Claim (PT-BR):** {result['claim_as_written_pt']}",
            f"- **Verdict:** `{result['fact_checked']}` (`{result['confidence']}` confidence)",
            f"- **Evidence (PT-BR):** {result['evidence_summary_pt']}",
            f"- **Anchor:** “{result['evidence_anchor']}”",
            f"- **Printed pages:** {result['printed_pages']}",
            f"- **Physical PDF pages:** {result['pdf_page_indices']}",
            f"- **Locator:** {result['source_locator']}",
            f"- **Source version:** {result['source_version']} (`{result['source_version_match']}`)",
            f"- **Direct evidence vs inference (PT-BR):** {result['direct_evidence_vs_inference_pt']}",
            f"- **Evidence file:** [`{result['evidence_path']}`]({result['evidence_path']})",
        ])
        if result["author_inference_assessment"]:
            assessment = result["author_inference_assessment"]
            lines.extend([
                f"- **Factual premises supported:** `{assessment['factual_premises_supported']}`",
                f"- **Inference reasonably follows:** `{assessment['inference_reasonably_follows']}`",
                f"- **Source explicitly states inference:** `{assessment['source_explicitly_states_inference']}`",
                f"- **Inference assessment (PT-BR):** {assessment['assessment_pt']}",
            ])
        if result["issues"]:
            lines.append("- **Structured issues:**")
            for issue in result["issues"]:
                lines.append(
                    f"  - `{issue['issue_code']}` / `{issue['severity']}` — {issue['mismatch_explanation_pt']} "
                    f"Action: `{issue['recommended_action']}`."
                )
        else:
            lines.append("- **Structured issues:** none")
        lines.extend([
            f"- **Recommended revision (PT-BR):** {result['recommended_revision_pt']}",
            "",
        ])

    lines.extend([
        "## Calibration summary",
        "",
        f"- Verdicts: {', '.join(f'`{key}` = {value}' for key, value in sorted(verdict_counts.items()))}",
        f"- Structured issues: {sum(len(result['issues']) for result in results)}",
        f"- Source-version issues: {sum(any(issue['issue_code'] == 'PDF_VERSION_MISMATCH' for issue in result['issues']) for result in results)} of 4 rows",
        f"- Claims needing a new source: {sum(result['needs_new_source'] for result in results)}",
        "- Direct claims: three; author inference: one",
        "- The author-inference row supports its factual premises and a reasonable economic interpretation, but the contrastive wording belongs to the dissertation author rather than the cited source.",
        "",
        "## Evidence-page manifest",
        "",
        "| Row | Evidence path | SHA-256 | Extracted pages | Source PDF indices |",
        "|---|---|---|---:|---|",
    ])
    for item in evidence_manifest:
        lines.append(f"| `{item['row_id']}` | `{item['path']}` | `{item['sha256']}` | {item['pages']} | {item['source_pdf_page_indices']} |")
    lines.extend([
        "",
        "## Gate",
        "",
        "No row after `ROW-0004` has been audited. The controller must stop here until explicit user approval is received.",
        "",
    ])
    atomic_text(RECEIPT_PATH, "\n".join(lines))

    report = [
        "# Source-to-Claim Fact-Check Audit",
        "",
        "> Status: calibration complete; awaiting explicit approval. This is not the final audit report.",
        "",
        "## Input and model manifest",
        "",
        "- Run ID: `20260801T155350Z`",
        "- Model: `gpt-5.6-sol`",
        "- Reasoning effort: `max`",
        "- Model fallback: disabled",
        "- Baseline: 186 claims, 227 rows, 58 occurrences, 24 works, 23 PDFs, 1 legal web source",
        "- Authoritative input hashes: [`run_manifest.json`](run_manifest.json)",
        "",
        "## Scope and limitations",
        "",
        "Only the four required Bick calibration relationships have been audited. The remaining 223 primary judgments, blind second review, adjudication, Notion drift check, and final aggregate tables have not begun.",
        "",
        "## Calibration",
        "",
        "See [`CALIBRATION_RECEIPT.md`](CALIBRATION_RECEIPT.md) and [`calibration_table.tsv`](calibration_table.tsv).",
        "",
        f"Calibration verdict counts: {', '.join(f'`{key}` = {value}' for key, value in sorted(verdict_counts.items()))}.",
        "",
        "All four rows were audited against the stored Working Paper 2024-027F revision dated 27 October 2025. Each result flags the mismatch against the frozen 2024 BibLaTeX record.",
        "",
        "## Gate",
        "",
        "STOP. Explicit user approval is required before `ROW-0005` or any later row may be processed.",
        "",
    ]
    atomic_text(REPORT_PATH, "\n".join(report))

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["audit_status"] = "CALIBRATION_COMPLETE_AWAITING_APPROVAL"
    manifest["audit_phase"] = "CALIBRATION_GATE"
    manifest["calibration"] = {
        "result_rows": expected,
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "structured_issue_count": sum(len(result["issues"]) for result in results),
        "source_version_issue_rows": 4,
        "needs_new_source_rows": sum(result["needs_new_source"] for result in results),
        "table_path": TABLE_PATH.relative_to(RUN_DIR).as_posix(),
        "table_sha256": sha(TABLE_PATH),
        "receipt_path": RECEIPT_PATH.relative_to(RUN_DIR).as_posix(),
        "receipt_sha256": sha(RECEIPT_PATH),
        "evidence_manifest": evidence_manifest,
        "gate": "AWAITING_EXPLICIT_USER_APPROVAL",
    }
    manifest["timestamps"]["calibration_artifacts_finalized_at"] = now()
    manifest["updated_at"] = now()
    atomic_json(MANIFEST_PATH, manifest)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "timestamp": now(),
            "event": "calibration_artifacts_finalized",
            "table_sha256": sha(TABLE_PATH),
            "receipt_sha256": sha(RECEIPT_PATH),
            "report_sha256": sha(REPORT_PATH),
            "verdict_counts": dict(sorted(verdict_counts.items())),
            "gate": "AWAITING_EXPLICIT_USER_APPROVAL",
        }, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({
        "status": "CALIBRATION_COMPLETE_AWAITING_APPROVAL",
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "issues": sum(len(result["issues"]) for result in results),
        "receipt": str(RECEIPT_PATH),
        "table": str(TABLE_PATH),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
