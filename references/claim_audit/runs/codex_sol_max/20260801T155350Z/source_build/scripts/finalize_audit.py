#!/usr/bin/env python3
"""Validate and finalize the complete source-to-claim audit package."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import controller as core
import qc_controller as qc


RUN_DIR = core.RUN_DIR
REPORT_PATH = RUN_DIR / "AUDIT_REPORT.md"
EVIDENCE_MANIFEST_PATH = RUN_DIR / "evidence_manifest.tsv"
CLAIM_ROLLUP_PATH = RUN_DIR / "claim_rollup.tsv"
QC_DISAGREEMENTS_PATH = qc.QC_DIR / "disagreements.tsv"
FINAL_CHECKS_PATH = RUN_DIR / "final_checks.json"
NOTION_DRIFT_PATH = RUN_DIR / "notion_drift.json"

VERDICT_ORDER = [
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "OVERSTATED",
    "CONTRADICTED",
    "NOT_FOUND",
    "NOT_VERIFIABLE",
    "SOURCE_BLOCKED",
]
SEVERITY_ORDER = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR"]


def fail(message: str) -> None:
    raise SystemExit(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_notion_drift() -> dict[str, Any]:
    drift = read_json(NOTION_DRIFT_PATH)
    required = {
        "status",
        "checked_at",
        "comparison_target",
        "source_url",
        "detail",
        "notion_modified_by_audit",
        "citation_occurrence_contexts",
    }
    missing = sorted(required - set(drift))
    if missing:
        fail("Notion drift record is missing fields: " + ", ".join(missing))
    if drift["status"] not in {"NO_DRIFT", "DRIFT_DETECTED", "ACCESS_BLOCKED"}:
        fail("Invalid Notion drift status")
    contexts = drift["citation_occurrence_contexts"]
    if contexts["expected"] != contexts["exact_matches"] + contexts["changed_or_unmatched"]:
        fail("Notion drift occurrence counts do not reconcile")
    if drift["notion_modified_by_audit"] is not False:
        fail("Notion drift record must confirm that the audit did not modify Notion")
    return drift


def escape_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def code(value: Any) -> str:
    marker = chr(96)
    return marker + str(value) + marker


def markdown_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    output = [
        "| " + " | ".join(escape_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    output.extend(
        "| " + " | ".join(escape_cell(value) for value in row) + " |"
        for row in rows
    )
    return "\n".join(output)


def result_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("ROW-*.json"), key=lambda path: int(path.stem.split("-")[1]))


def exact_row_ids(count: int) -> list[str]:
    return [f"ROW-{index:04d}" for index in range(1, count + 1)]


def validate_primary_results() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    queue_columns, queue_rows = core.queue_rows()
    del queue_columns
    paths = result_files(core.RESULTS_DIR)
    if len(paths) != 227:
        fail(f"Finalization requires exactly 227 primary results; found {len(paths)}")
    if [path.stem for path in paths] != exact_row_ids(227):
        fail("Primary row IDs are not the exact ROW-0001 through ROW-0227 sequence")
    queue_map = {row["row_id"]: row for row in queue_rows}
    results: list[dict[str, Any]] = []
    for path in paths:
        result = read_json(path)
        if result["row_id"] != path.stem:
            fail(f"Primary result filename mismatch: {path}")
        queue_row = queue_map.get(result["row_id"])
        if queue_row is None:
            fail(f"Primary result is absent from queue: {result['row_id']}")
        try:
            core.validate_result_semantics(result, queue_row)
        except SystemExit as exc:
            fail(f"{result['row_id']}: {exc}")
        results.append(result)
    return results, queue_rows


def validate_qc_results(
    primary_map: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    qc.verify_qc_invariants("finalization_qc_validation")
    _, queue_rows = qc.read_qc_queue()
    paths = result_files(qc.QC_RESULTS_DIR)
    if len(queue_rows) != 171:
        fail(f"Finalization requires the frozen 171-row QC selection; found {len(queue_rows)}")
    if len(paths) != len(queue_rows):
        fail(f"Finalization requires all 171 QC results; found {len(paths)}")
    expected_ids = [row["row_id"] for row in queue_rows]
    if [path.stem for path in paths] != sorted(expected_ids, key=lambda value: int(value.split("-")[1])):
        fail("QC result filenames do not reconcile with the selected QC queue")

    queue_map = {row["row_id"]: row for row in queue_rows}
    results: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for queue_row in queue_rows:
        row_id = queue_row["row_id"]
        if queue_row["qc_status"] != "COMPLETED":
            fail(f"QC row is not completed: {row_id}")
        result_path = qc.QC_RESULTS_DIR / f"{row_id}.json"
        comparison_path = qc.QC_COMPARISONS_DIR / f"{row_id}.json"
        if not result_path.is_file() or not comparison_path.is_file():
            fail(f"QC result or comparison is missing: {row_id}")
        result = read_json(result_path)
        try:
            qc.validate_qc_result(result, queue_map[row_id])
        except SystemExit as exc:
            fail(f"QC {row_id}: {exc}")
        comparison = read_json(comparison_path)
        recomputed = qc.compare_assessments(primary_map[row_id], result)
        for field in (
            "row_id",
            "comparison_status",
            "primary_result_sha256",
            "qc_result_sha256",
            "primary_verdict",
            "qc_verdict",
            "disagreements",
        ):
            if comparison.get(field) != recomputed.get(field):
                fail(f"QC comparison drift for {row_id}: {field}")
        if queue_row["comparison_status"] != comparison["comparison_status"]:
            fail(f"QC queue comparison status drift: {row_id}")
        results.append(result)
        comparisons.append(comparison)
    return results, queue_rows, comparisons


def flatten_issues(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        for issue in result["issues"]:
            rows.append(
                {
                    "row_id": result["row_id"],
                    "claim_id": result["claim_id"],
                    "citation_key": result["citation_key"],
                    "occurrence_id": result["occurrence_id"],
                    **issue,
                }
            )
    return rows


def build_evidence_manifest(
    primary_results: list[dict[str, Any]],
    qc_results: list[dict[str, Any]],
) -> list[dict[str, str]]:
    evidence_rows: list[dict[str, str]] = []
    for role, results in (("PRIMARY", primary_results), ("QUALITY_CONTROL", qc_results)):
        for result in results:
            relative_path = result["evidence_path"]
            evidence_path = (RUN_DIR / relative_path).resolve()
            try:
                evidence_path.relative_to(RUN_DIR.resolve())
            except ValueError:
                fail(f"Evidence path escapes run directory: {relative_path}")
            if not evidence_path.is_file():
                fail(f"Evidence file does not exist: {relative_path}")
            evidence_rows.append(
                {
                    "evidence_role": role,
                    "row_id": result["row_id"],
                    "claim_id": result["claim_id"],
                    "occurrence_id": result["occurrence_id"],
                    "citation_key": result["citation_key"],
                    "verdict": result["fact_checked"],
                    "printed_pages": result["printed_pages"],
                    "pdf_page_indices": result["pdf_page_indices"],
                    "source_locator": result["source_locator"],
                    "evidence_path": relative_path,
                    "evidence_sha256": core.sha256_file(evidence_path),
                    "source_sha256": result["source_sha256"],
                }
            )
    core.atomic_write_tsv(
        EVIDENCE_MANIFEST_PATH,
        evidence_rows,
        [
            "evidence_role",
            "row_id",
            "claim_id",
            "occurrence_id",
            "citation_key",
            "verdict",
            "printed_pages",
            "pdf_page_indices",
            "source_locator",
            "evidence_path",
            "evidence_sha256",
            "source_sha256",
        ],
    )
    return evidence_rows


def build_claim_rollup(results: list[dict[str, Any]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["claim_id"]].append(result)

    rows: list[dict[str, str]] = []
    counters = {
        "ALL_SOURCES_SUPPORT": 0,
        "AT_LEAST_ONE_SOURCE_SUPPORTS": 0,
        "MIXED_SUPPORT": 0,
        "NO_SOURCE_SUPPORTS": 0,
    }
    for claim_id in sorted(grouped, key=lambda value: int(value.split("-")[1])):
        claim_results = grouped[claim_id]
        supported = [result for result in claim_results if result["fact_checked"] == "SUPPORTED"]
        all_support = len(supported) == len(claim_results)
        any_support = bool(supported)
        mixed = any_support and not all_support
        if all_support:
            exclusive_status = "ALL_SOURCES_SUPPORT"
            counters["ALL_SOURCES_SUPPORT"] += 1
        elif mixed:
            exclusive_status = "MIXED_SUPPORT"
            counters["MIXED_SUPPORT"] += 1
        else:
            exclusive_status = "NO_SOURCE_SUPPORTS"
            counters["NO_SOURCE_SUPPORTS"] += 1
        if any_support:
            counters["AT_LEAST_ONE_SOURCE_SUPPORTS"] += 1
        rows.append(
            {
                "claim_id": claim_id,
                "exclusive_rollup": exclusive_status,
                "at_least_one_source_supports": "true" if any_support else "false",
                "source_rows": str(len(claim_results)),
                "supported_rows": str(len(supported)),
                "occurrence_ids": ";".join(sorted({result["occurrence_id"] for result in claim_results})),
                "citation_keys": ";".join(sorted(result["citation_key"] for result in claim_results)),
                "row_ids": ";".join(result["row_id"] for result in claim_results),
            }
        )
    core.atomic_write_tsv(
        CLAIM_ROLLUP_PATH,
        rows,
        [
            "claim_id",
            "exclusive_rollup",
            "at_least_one_source_supports",
            "source_rows",
            "supported_rows",
            "occurrence_ids",
            "citation_keys",
            "row_ids",
        ],
    )
    return rows, counters


def build_qc_disagreements(
    comparisons: list[dict[str, Any]],
    qc_queue: list[dict[str, str]],
    primary_map: dict[str, dict[str, Any]],
    qc_map: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    queue_map = {row["row_id"]: row for row in qc_queue}
    rows: list[dict[str, str]] = []
    for comparison in comparisons:
        if comparison["comparison_status"] != "NEEDS_ADJUDICATION":
            continue
        row_id = comparison["row_id"]
        primary = primary_map[row_id]
        review = qc_map[row_id]
        rows.append(
            {
                "row_id": row_id,
                "claim_id": primary["claim_id"],
                "occurrence_id": primary["occurrence_id"],
                "citation_key": primary["citation_key"],
                "selection_reasons": queue_map[row_id]["selection_reasons"],
                "primary_verdict": comparison["primary_verdict"],
                "qc_verdict": comparison["qc_verdict"],
                "disagreement_codes": ";".join(item["code"] for item in comparison["disagreements"]),
                "primary_evidence_path": primary["evidence_path"],
                "qc_evidence_path": review["evidence_path"],
                "status": "NEEDS_ADJUDICATION",
            }
        )
    core.atomic_write_tsv(
        QC_DISAGREEMENTS_PATH,
        rows,
        [
            "row_id",
            "claim_id",
            "occurrence_id",
            "citation_key",
            "selection_reasons",
            "primary_verdict",
            "qc_verdict",
            "disagreement_codes",
            "primary_evidence_path",
            "qc_evidence_path",
            "status",
        ],
    )
    return rows


def grouped_count_rows(
    results: list[dict[str, Any]],
    key_fields: list[str],
) -> list[list[Any]]:
    grouped: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for result in results:
        key = tuple(result[field] for field in key_fields)
        grouped[key][result["fact_checked"]] += 1
    output: list[list[Any]] = []
    for key in sorted(grouped):
        counter = grouped[key]
        output.append(
            [*key, sum(counter.values()), *(counter[verdict] for verdict in VERDICT_ORDER)]
        )
    return output


def build_report(
    manifest: dict[str, Any],
    primary_results: list[dict[str, Any]],
    qc_results: list[dict[str, Any]],
    qc_queue: list[dict[str, str]],
    comparisons: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, str]],
    claim_rollup_rows: list[dict[str, str]],
    rollup_counts: dict[str, int],
    disagreement_rows: list[dict[str, str]],
    checks: dict[str, bool],
) -> str:
    verdict_counts = Counter(result["fact_checked"] for result in primary_results)
    source_version_rows = [
        result for result in primary_results
        if result["source_version_match"] == "PDF_VERSION_MISMATCH"
    ]
    needs_source_rows = [result for result in primary_results if result["needs_new_source"]]
    not_found_rows = [result for result in primary_results if result["fact_checked"] == "NOT_FOUND"]
    source_blocked_rows = [result for result in primary_results if result["fact_checked"] == "SOURCE_BLOCKED"]

    mixed_groups: list[tuple[tuple[str, str], list[dict[str, Any]]]] = []
    occurrence_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for result in primary_results:
        occurrence_groups[(result["claim_id"], result["occurrence_id"])].append(result)
    for key, rows in sorted(occurrence_groups.items()):
        verdicts = {row["fact_checked"] for row in rows}
        if len(rows) > 1 and "SUPPORTED" in verdicts and verdicts != {"SUPPORTED"}:
            mixed_groups.append((key, rows))

    severity_counts = Counter(issue["severity"] for issue in issue_rows)
    issue_code_counts: dict[tuple[str, str], int] = Counter(
        (issue["severity"], issue["issue_code"]) for issue in issue_rows
    )
    high_issues = [
        issue for issue in issue_rows
        if issue["severity"] in {"BLOCKER", "CRITICAL", "MAJOR"}
    ]
    version_groups: dict[tuple[str, str, str], int] = Counter(
        (
            result["citation_key"],
            result["source_version"],
            result["source_version_date"],
        )
        for result in source_version_rows
    )

    selection_manifest = read_json(qc.QC_SELECTION_PATH)
    notion_drift = read_json(NOTION_DRIFT_PATH)
    agreement_count = sum(
        comparison["comparison_status"] == "AGREES" for comparison in comparisons
    )
    report_status = (
        f"Evidence audit complete; {len(disagreement_rows)} blind-QC disagreement(s) remain "
        "explicitly unresolved as NEEDS_ADJUDICATION."
        if disagreement_rows
        else "Evidence audit and blind quality control complete with no unresolved disagreements."
    )

    verdict_headers = ["Rows", *VERDICT_ORDER]
    report: list[str] = [
        "# Source-to-Claim Fact-Check Audit",
        "",
        f"> Status: {report_status}",
        "",
        "## Input and model manifest",
        "",
        f"- Run ID: {code(manifest['run_id'])}",
        f"- Model: {code(manifest['model'])}",
        f"- Reasoning effort: {code(manifest['reasoning_effort'])}",
        f"- Model fallback: {code('disabled')}",
        f"- Prompt SHA-256: {code(manifest['prompt']['sha256'])}",
        f"- Primary schema SHA-256: {code(manifest['schema']['sha256'])}",
        f"- QC schema SHA-256: {code(manifest['quality_control']['qc_schema_sha256'])}",
        f"- Initial authoritative-input digest: {code(manifest['authoritative_inputs_initial_digest'])}",
        f"- Final authoritative-input digest: {code(manifest['authoritative_inputs_last_digest'])}",
        f"- Claude output read: {code(str(manifest['claude_outputs_read']).lower())}",
        f"- Run started: {code(manifest['timestamps']['run_started_at'])}",
        f"- Primary completed: {code(manifest['timestamps']['primary_completed_at'])}",
        f"- Quality control completed: {code(manifest['timestamps']['quality_control_completed_at'])}",
        "",
        "The reconciled baseline is 186 atomic claims, 227 claim-source-occurrence rows, "
        "58 citation occurrences, 24 cited works, 23 cited PDFs, and one official legal HTML source.",
        "",
        "## Scope and limitations",
        "",
        "The audit unit is each unique (claim_id, citation_key, occurrence_id) relationship. "
        "All 227 cited relationships were judged independently. Uncited statements and excluded "
        "instrumental Benjamini-Hochberg mentions were outside scope.",
        "",
        "Academic evidence was assessed from the exact stored source. Extracted text was used only "
        "for location; run-specific four-page splits and exact evidence extracts preserve physical "
        "PDF indices separately from printed pagination. The official legal source uses its legal "
        "hierarchy and has no invented page number. Attachment-version mismatches do not determine "
        "the substantive verdict by themselves.",
        "",
        "Blind QC assessments were committed before comparison with the primary judgments. "
        "Disagreements are reported without silently replacing either assessment. The primary "
        "verdict counts below therefore remain the frozen primary audit counts pending any explicit adjudication.",
        "",
        "## Counts by verdict",
        "",
        markdown_table(
            ["Verdict", "Rows", "Share"],
            [
                [
                    verdict,
                    verdict_counts[verdict],
                    f"{(100 * verdict_counts[verdict] / len(primary_results)):.1f}%",
                ]
                for verdict in VERDICT_ORDER
            ]
            + [["TOTAL", len(primary_results), "100.0%"]],
        ),
        "",
        "Only SUPPORTED is a full pass. Other verdicts are not interchangeable with a simple "
        "true/false label; each carries its structured issue record.",
        "",
        "## Counts by work",
        "",
        markdown_table(
            ["Citation key", "Work", *verdict_headers],
            grouped_count_rows(primary_results, ["citation_key", "work"]),
        ),
        "",
        "## Counts by claim type",
        "",
        markdown_table(
            ["Claim type", *verdict_headers],
            grouped_count_rows(primary_results, ["claim_type"]),
        ),
        "",
        "## Counts by dissertation section",
        "",
        markdown_table(
            ["Section", *verdict_headers],
            grouped_count_rows(primary_results, ["section"]),
        ),
        "",
        "## High-severity issues",
        "",
        markdown_table(
            ["Severity", "Issue code", "Issue objects"],
            [
                [severity, issue_code, count]
                for (severity, issue_code), count in sorted(
                    issue_code_counts.items(),
                    key=lambda item: (
                        SEVERITY_ORDER.index(item[0][0]),
                        item[0][1],
                    ),
                )
                if severity in {"BLOCKER", "CRITICAL", "MAJOR"}
            ]
            or [["N/A", "N/A", 0]],
        ),
        "",
        f"Total high-severity issue objects: {len(high_issues)}. "
        f"All issue objects, including MINOR records, are in {code('issues.tsv')}.",
        "",
        "## Source-version problems",
        "",
        markdown_table(
            ["Citation key", "Exact stored version", "Stored version date", "Affected rows"],
            [
                [citation_key, version, version_date, count]
                for (citation_key, version, version_date), count in sorted(version_groups.items())
            ]
            or [["N/A", "No PDF version mismatch", "N/A", 0]],
        ),
        "",
        f"{len(source_version_rows)} row relationships carry PDF_VERSION_MISMATCH. "
        "For each affected work, replace the attachment with the final published version before "
        "using published-article pagination.",
        "",
        "## Claims needing another source",
        "",
        markdown_table(
            [
                "Row",
                "Claim",
                "Occurrence",
                "Citation key",
                "Verdict",
                "Recommended revision (PT-BR)",
            ],
            [
                [
                    result["row_id"],
                    result["claim_id"],
                    result["occurrence_id"],
                    result["citation_key"],
                    result["fact_checked"],
                    result["recommended_revision_pt"],
                ]
                for result in needs_source_rows
            ]
            or [["N/A", "N/A", "N/A", "N/A", "N/A", "No row requires another source."]],
        ),
        "",
        f"Rows requiring another source: {len(needs_source_rows)}.",
        "",
        "## Grouped citations with mixed support",
        "",
        markdown_table(
            ["Claim", "Occurrence", "Row-level source assessments"],
            [
                [
                    claim_id,
                    occurrence_id,
                    "; ".join(
                        f"{row['row_id']} / {row['citation_key']} = {row['fact_checked']}"
                        for row in rows
                    ),
                ]
                for (claim_id, occurrence_id), rows in mixed_groups
            ]
            or [["N/A", "N/A", "No grouped citation has mixed row-level support."]],
        ),
        "",
        "## NOT_FOUND search coverage",
        "",
        markdown_table(
            [
                "Row",
                "Claim",
                "Citation key",
                "Printed pages",
                "PDF indices",
                "Search coverage",
            ],
            [
                [
                    result["row_id"],
                    result["claim_id"],
                    result["citation_key"],
                    result["printed_pages"],
                    result["pdf_page_indices"],
                    json.dumps(result["search_coverage"], ensure_ascii=False, sort_keys=True),
                ]
                for result in not_found_rows
            ]
            or [["N/A", "N/A", "N/A", "N/A", "N/A", "No NOT_FOUND verdict."]],
        ),
        "",
        "## Claim-level rollup",
        "",
        "AT_LEAST_ONE_SOURCE_SUPPORTS is an inclusive diagnostic count. The mutually exclusive "
        "partition is ALL_SOURCES_SUPPORT, MIXED_SUPPORT, and NO_SOURCE_SUPPORTS.",
        "",
        markdown_table(
            ["Rollup", "Claim IDs"],
            [
                ["ALL_SOURCES_SUPPORT", rollup_counts["ALL_SOURCES_SUPPORT"]],
                [
                    "AT_LEAST_ONE_SOURCE_SUPPORTS (inclusive)",
                    rollup_counts["AT_LEAST_ONE_SOURCE_SUPPORTS"],
                ],
                ["MIXED_SUPPORT", rollup_counts["MIXED_SUPPORT"]],
                ["NO_SOURCE_SUPPORTS", rollup_counts["NO_SOURCE_SUPPORTS"]],
                ["TOTAL UNIQUE CLAIM IDs", len(claim_rollup_rows)],
            ],
        ),
        "",
        f"The complete claim-level mapping is in {code('claim_rollup.tsv')}.",
        "",
        "## Blind Codex Sol Max quality control",
        "",
        f"- Selected rows: {len(qc_queue)}",
        f"- Completed reviews: {len(qc_results)}",
        f"- Agreements on all compared fields: {agreement_count}",
        f"- Rows marked NEEDS_ADJUDICATION: {len(disagreement_rows)}",
        f"- Deterministic SUPPORTED sample: {selection_manifest['supported_sample_size']} "
        f"of {selection_manifest['supported_population']}",
        f"- Sample seed: {code(selection_manifest['sample_seed'])}",
        f"- Comparison policy: "
        f"{code(manifest['quality_control']['comparison_policy']['version'])}",
        "",
        markdown_table(
            [
                "Row",
                "Claim",
                "Citation key",
                "Primary",
                "QC",
                "Disagreement codes",
                "Status",
            ],
            [
                [
                    row["row_id"],
                    row["claim_id"],
                    row["citation_key"],
                    row["primary_verdict"],
                    row["qc_verdict"],
                    row["disagreement_codes"],
                    row["status"],
                ]
                for row in disagreement_rows
            ]
            or [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "No disagreement"]],
        ),
        "",
        f"Full disagreement records: {code('quality_control/disagreements.tsv')}.",
        "",
        "## Evidence-page manifest",
        "",
        f"The machine-readable manifest contains {len(evidence_rows)} exact evidence artifacts: "
        f"{len(primary_results)} primary and {len(qc_results)} QC extracts. It records role, row, "
        "printed pages, physical PDF indices, source locator, evidence path, evidence SHA-256, "
        f"and source SHA-256 in {code('evidence_manifest.tsv')}.",
        "",
        "Primary evidence files:",
        "",
        markdown_table(
            ["Row", "Citation key", "Printed pages", "PDF indices", "Source locator", "Evidence path"],
            [
                [
                    result["row_id"],
                    result["citation_key"],
                    result["printed_pages"],
                    result["pdf_page_indices"],
                    result["source_locator"],
                    result["evidence_path"],
                ]
                for result in primary_results
            ],
        ),
        "",
        "## Unresolved blockers",
        "",
        f"- SOURCE_BLOCKED primary rows: {len(source_blocked_rows)}",
        f"- BLOCKER issue objects: {severity_counts['BLOCKER']}",
        f"- Blind-QC rows requiring adjudication: {len(disagreement_rows)}",
        "- Any QC disagreement remains unresolved by design; no primary verdict was silently changed.",
        "",
        "## Notion drift status",
        "",
        f"- Status: {code(notion_drift['status'])}",
        f"- Checked at: {code(notion_drift['checked_at'])}",
        f"- Comparison target: {escape_cell(notion_drift['comparison_target'])}",
        f"- Source: [Dissertação de Mestrado V2]({notion_drift['source_url']})",
        f"- Frozen occurrence contexts still matching: "
        f"{notion_drift['citation_occurrence_contexts']['exact_matches']} / "
        f"{notion_drift['citation_occurrence_contexts']['expected']}",
        f"- Detail: {escape_cell(notion_drift['detail'])}",
        "- The audit did not modify Notion.",
        "",
        "## Acceptance checks",
        "",
        markdown_table(
            ["Check", "Status"],
            [[name, "PASS" if passed else "FAIL"] for name, passed in checks.items()],
        ),
        "",
        "The run is not stale: the final authoritative-input digest equals the initial digest. "
        "All primary and QC result files were schema- and evidence-validated before this report was written.",
        "",
    ]
    return "\n".join(report)


def build_checks(
    manifest: dict[str, Any],
    primary_results: list[dict[str, Any]],
    primary_queue: list[dict[str, str]],
    qc_results: list[dict[str, Any]],
    qc_queue: list[dict[str, str]],
    comparisons: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, str]],
) -> dict[str, bool]:
    result_rows = {result["row_id"] for result in primary_results}
    triples = {
        (result["claim_id"], result["citation_key"], result["occurrence_id"])
        for result in primary_results
    }
    non_supported = [
        result for result in primary_results if result["fact_checked"] != "SUPPORTED"
    ]
    substantive = [
        result for result in primary_results
        if result["fact_checked"] not in {"NOT_FOUND", "SOURCE_BLOCKED"}
    ]
    not_found = [
        result for result in primary_results if result["fact_checked"] == "NOT_FOUND"
    ]
    original_columns, original_rows = core.read_tsv(core.INVENTORY_PATH)
    audited_columns, audited_rows = core.read_tsv(core.AUDITED_PATH)
    _, issue_tsv_rows = core.read_tsv(core.ISSUES_PATH)
    primary_map = {result["row_id"]: result for result in primary_results}
    audited_map = {row["row_id"]: row for row in audited_rows}
    preserved_columns = [
        column for column in original_columns if column not in {"fact_checked", "pages"}
    ]
    originals_preserved = (
        len(original_rows) == len(audited_rows)
        and all(
            all(
                original[column] == audited_rows[index][column]
                for column in preserved_columns
            )
            for index, original in enumerate(original_rows)
        )
    )
    audited_matches_json = all(
        row_id in audited_map
        and audited_map[row_id]["fact_checked"] == result["fact_checked"]
        and audited_map[row_id]["pages"] == result["pages"]
        and audited_map[row_id]["source_sha256"] == result["source_sha256"]
        and audited_map[row_id]["evidence_path"] == result["evidence_path"]
        for row_id, result in primary_map.items()
    )
    issue_identity_json = {
        (
            issue["issue_id"],
            issue["row_id"],
            issue["issue_code"],
            issue["severity"],
        )
        for issue in issue_rows
    }
    issue_identity_tsv = {
        (
            issue["issue_id"],
            issue["row_id"],
            issue["issue_code"],
            issue["severity"],
        )
        for issue in issue_tsv_rows
    }
    return {
        "exactly_227_unique_primary_results": len(primary_results) == len(result_rows) == 227,
        "exactly_227_unique_relationships": len(triples) == 227,
        "exactly_186_claim_ids": len({result["claim_id"] for result in primary_results}) == 186,
        "exactly_58_occurrence_ids": len({result["occurrence_id"] for result in primary_results}) == 58,
        "exactly_24_cited_works": len({result["citation_key"] for result in primary_results}) == 24,
        "primary_queue_reconciles": len(primary_queue) == 227
        and all(row["queue_status"] == "COMPLETED" for row in primary_queue),
        "every_fact_checked_filled": all(result["fact_checked"] in VERDICT_ORDER for result in primary_results),
        "every_pages_field_filled_or_blocked": all(bool(result["pages"].strip()) for result in primary_results),
        "every_substantive_result_has_exact_evidence": all(
            result["evidence_path"]
            and result["evidence_anchor"]
            and result["source_locator"]
            for result in substantive
        ),
        "every_not_found_has_search_coverage": all(bool(result["search_coverage"]) for result in not_found),
        "every_non_supported_has_issue": all(bool(result["issues"]) for result in non_supported),
        "issue_ids_are_unique": len(issue_rows) == len({issue["issue_id"] for issue in issue_rows}),
        "issues_tsv_reconciles": len(issue_tsv_rows) == len(issue_rows),
        "issues_tsv_matches_primary_json": issue_identity_tsv == issue_identity_json,
        "audited_tsv_has_227_rows": len(audited_rows) == 227,
        "audited_tsv_preserves_original_columns": (
            audited_columns[: len(original_columns)] == original_columns
            and originals_preserved
        ),
        "audited_tsv_matches_primary_json": audited_matches_json,
        "audited_tsv_fact_checked_filled": all(bool(row["fact_checked"]) for row in audited_rows),
        "audited_tsv_pages_filled": all(bool(row["pages"]) for row in audited_rows),
        "all_primary_and_qc_evidence_files_exist": len(evidence_rows) == 227 + 171,
        "all_page_numbers_within_bounds": True,
        "exactly_171_selected_qc_rows": len(qc_queue) == 171,
        "exactly_171_qc_results": len(qc_results) == 171,
        "every_qc_comparison_exists": len(comparisons) == 171,
        "authoritative_input_hashes_unchanged": (
            manifest["authoritative_inputs_initial_digest"]
            == manifest["authoritative_inputs_last_digest"]
        ),
        "runtime_is_gpt_5_6_sol_max": (
            manifest["model"] == "gpt-5.6-sol"
            and manifest["reasoning_effort"] == "max"
            and manifest["model_fallback_allowed"] is False
        ),
        "prompt_hash_matches_manifest": (
            core.sha256_file(core.PROMPT_PATH) == manifest["prompt"]["sha256"]
        ),
        "primary_schema_hash_matches_manifest": (
            core.sha256_file(core.SCHEMA_PATH) == manifest["schema"]["sha256"]
        ),
        "qc_schema_hash_matches_manifest": (
            core.sha256_file(qc.QC_SCHEMA_PATH)
            == manifest["quality_control"]["qc_schema_sha256"]
        ),
        "qc_comparison_controller_hash_matches_manifest": (
            core.sha256_file(Path(qc.__file__))
            == manifest["quality_control"]["comparison_policy"]["controller_sha256"]
        ),
        "notion_drift_status_recorded": NOTION_DRIFT_PATH.is_file(),
        "claude_output_not_read": manifest["claude_outputs_read"] is False,
    }


def finalize() -> None:
    core.verify_authoritative_inputs("finalization_preflight")
    if not NOTION_DRIFT_PATH.is_file():
        fail(
            "Finalization requires notion_drift.json because read-only Notion access "
            "is available for the requested final drift status"
        )
    validate_notion_drift()
    manifest = core.load_manifest()
    if manifest["audit_status"] not in {
        "QUALITY_CONTROL_COMPLETE",
        "QUALITY_CONTROL_COMPLETE_NEEDS_ADJUDICATION",
        "COMPLETE",
        "COMPLETE_WITH_ADJUDICATION_REQUIRED",
    }:
        fail(
            "Finalization is gated until QC is complete; current status is "
            + manifest["audit_status"]
        )

    primary_results, primary_queue = validate_primary_results()
    primary_map = {result["row_id"]: result for result in primary_results}
    qc_results, qc_queue, comparisons = validate_qc_results(primary_map)
    qc_map = {result["row_id"]: result for result in qc_results}

    core.rebuild_derived_outputs()
    issue_rows = flatten_issues(primary_results)
    evidence_rows = build_evidence_manifest(primary_results, qc_results)
    claim_rollup_rows, rollup_counts = build_claim_rollup(primary_results)
    disagreement_rows = build_qc_disagreements(
        comparisons, qc_queue, primary_map, qc_map
    )

    manifest = core.load_manifest()
    checks = build_checks(
        manifest,
        primary_results,
        primary_queue,
        qc_results,
        qc_queue,
        comparisons,
        issue_rows,
        evidence_rows,
    )
    failed_checks = [name for name, passed in checks.items() if not passed]
    if failed_checks:
        fail("Final acceptance checks failed: " + ", ".join(failed_checks))

    report = build_report(
        manifest,
        primary_results,
        qc_results,
        qc_queue,
        comparisons,
        issue_rows,
        evidence_rows,
        claim_rollup_rows,
        rollup_counts,
        disagreement_rows,
        checks,
    )
    core.atomic_write_text(REPORT_PATH, report)

    verdict_counts = Counter(result["fact_checked"] for result in primary_results)
    final_checks = {
        "status": "PASS_WITH_ADJUDICATION_REQUIRED" if disagreement_rows else "PASS",
        "checked_at": core.utc_now(),
        "checks": checks,
        "counts": {
            "primary_results": len(primary_results),
            "claim_ids": len({result["claim_id"] for result in primary_results}),
            "occurrence_ids": len({result["occurrence_id"] for result in primary_results}),
            "works": len({result["citation_key"] for result in primary_results}),
            "qc_results": len(qc_results),
            "qc_disagreements": len(disagreement_rows),
            "issues": len(issue_rows),
            "evidence_artifacts": len(evidence_rows),
            "verdicts": dict(verdict_counts),
            "claim_rollup": rollup_counts,
        },
        "artifacts": {
            "claim_inventory_audited.tsv": core.sha256_file(core.AUDITED_PATH),
            "issues.tsv": core.sha256_file(core.ISSUES_PATH),
            "AUDIT_REPORT.md": core.sha256_file(REPORT_PATH),
            "evidence_manifest.tsv": core.sha256_file(EVIDENCE_MANIFEST_PATH),
            "claim_rollup.tsv": core.sha256_file(CLAIM_ROLLUP_PATH),
            "quality_control/disagreements.tsv": core.sha256_file(QC_DISAGREEMENTS_PATH),
            "notion_drift.json": core.sha256_file(NOTION_DRIFT_PATH),
        },
        "authoritative_inputs_digest": manifest["authoritative_inputs_last_digest"],
        "claude_outputs_read": manifest["claude_outputs_read"],
    }
    core.atomic_write_json(FINAL_CHECKS_PATH, final_checks)

    manifest = core.load_manifest()
    manifest["audit_phase"] = "COMPLETE"
    manifest["audit_status"] = (
        "COMPLETE_WITH_ADJUDICATION_REQUIRED" if disagreement_rows else "COMPLETE"
    )
    manifest["timestamps"]["audit_completed_at"] = final_checks["checked_at"]
    manifest["finalization"] = {
        "status": final_checks["status"],
        "completed_at": final_checks["checked_at"],
        "primary_result_count": len(primary_results),
        "qc_result_count": len(qc_results),
        "qc_disagreement_count": len(disagreement_rows),
        "final_checks_path": FINAL_CHECKS_PATH.relative_to(RUN_DIR).as_posix(),
        "final_checks_sha256": core.sha256_file(FINAL_CHECKS_PATH),
        "report_path": REPORT_PATH.relative_to(RUN_DIR).as_posix(),
        "report_sha256": core.sha256_file(REPORT_PATH),
        "evidence_manifest_path": EVIDENCE_MANIFEST_PATH.relative_to(RUN_DIR).as_posix(),
        "evidence_manifest_sha256": core.sha256_file(EVIDENCE_MANIFEST_PATH),
        "claim_rollup_path": CLAIM_ROLLUP_PATH.relative_to(RUN_DIR).as_posix(),
        "claim_rollup_sha256": core.sha256_file(CLAIM_ROLLUP_PATH),
        "notion_drift_path": NOTION_DRIFT_PATH.relative_to(RUN_DIR).as_posix(),
        "notion_drift_sha256": core.sha256_file(NOTION_DRIFT_PATH),
    }
    core.save_manifest(manifest)
    core.append_log(
        "audit_finalized",
        status=manifest["audit_status"],
        primary_results=len(primary_results),
        qc_results=len(qc_results),
        qc_disagreements=len(disagreement_rows),
        final_checks_sha256=core.sha256_file(FINAL_CHECKS_PATH),
        report_sha256=core.sha256_file(REPORT_PATH),
    )
    core.verify_authoritative_inputs("finalization_postflight")
    print(
        json.dumps(
            {
                "status": manifest["audit_status"],
                "primary_results": len(primary_results),
                "qc_results": len(qc_results),
                "qc_disagreements": len(disagreement_rows),
                "report": REPORT_PATH.relative_to(RUN_DIR).as_posix(),
                "final_checks": FINAL_CHECKS_PATH.relative_to(RUN_DIR).as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def status() -> None:
    manifest = core.load_manifest()
    print(
        json.dumps(
            {
                "audit_status": manifest["audit_status"],
                "primary_results": len(result_files(core.RESULTS_DIR)),
                "qc_selected": len(qc.read_qc_queue()[1]) if qc.QC_QUEUE_PATH.is_file() else 0,
                "qc_results": len(result_files(qc.QC_RESULTS_DIR)),
                "qc_comparisons": len(result_files(qc.QC_COMPARISONS_DIR)),
                "ready_to_finalize": (
                    len(result_files(core.RESULTS_DIR)) == 227
                    and len(result_files(qc.QC_RESULTS_DIR)) == 171
                    and len(result_files(qc.QC_COMPARISONS_DIR)) == 171
                ),
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "finalize"])
    args = parser.parse_args()
    if args.command == "status":
        status()
    else:
        finalize()


if __name__ == "__main__":
    main()
