#!/usr/bin/env python3
"""Controller-side validation and atomic commit of one worker result.

Responsibilities (deliberately kept out of the worker):
  1. re-verify authoritative input hashes -> abort and mark run stale on drift
  2. merge the worker's judgment with immutable inventory fields
  3. validate against claim_result.schema.json
  4. extract the cited page range into evidence_pages/<row_id>.pdf
  5. bounds-check every reported page against the real source
  6. write results/<row_id>.json atomically, append to audit_log.jsonl, advance queue.tsv

Usage: commit_result.py <row_id>
"""
import csv, json, hashlib, os, sys, datetime, tempfile, shutil

ROOT = "/Users/manebrasil/Documents/Projects/Dissetação Mestrado"
RUN = os.path.join(ROOT, "references/claim_audit/runs/claude_opus_5/20260801T160057Z_claude-opus-5_max")
INVENTORY = os.path.join(ROOT, "references/claim_audit/claim_inventory.tsv")
AUDITOR_MODEL = "claude-opus-5"
AUDITOR_EFFORT = "max"

VERDICTS = {"SUPPORTED", "PARTIALLY_SUPPORTED", "OVERSTATED", "CONTRADICTED",
            "NOT_FOUND", "NOT_VERIFIABLE", "SOURCE_BLOCKED"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_input_drift():
    """Abort if any authoritative input changed since the run manifest was written."""
    man = json.load(open(os.path.join(RUN, "run_manifest.json"), encoding="utf-8"))
    drift = []
    for rel, rec in man["authoritative_inputs"].items():
        actual = sha256(os.path.join(ROOT, rel))
        if actual != rec["sha256"]:
            drift.append((rel, rec["sha256"], actual))
    if drift:
        man["audit_status"] = "STALE_INPUT_CHANGED"
        man["stale_detail"] = [{"input": d[0], "expected": d[1], "actual": d[2]} for d in drift]
        man.setdefault("timestamps", {})["stale_detected_at"] = utcnow()
        json.dump(man, open(os.path.join(RUN, "run_manifest.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        sys.exit("ABORT: authoritative input changed mid-run; completed results preserved, "
                 "run marked STALE_INPUT_CHANGED.\n" + "\n".join(d[0] for d in drift))
    return man


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def inventory_row(row_id):
    rows = list(csv.DictReader(open(INVENTORY, newline="", encoding="utf-8"), delimiter="\t"))
    idx = int(row_id[1:]) - 1
    return rows[idx]


def parse_range(spec):
    """'8' or '8-9' or [8,9] -> (first, last)"""
    if isinstance(spec, (list, tuple)):
        return int(spec[0]), int(spec[-1])
    s = str(spec).strip().replace("–", "-")
    parts = [p for p in s.split("-") if p.strip().isdigit()]
    if not parts:
        return None
    return int(parts[0]), int(parts[-1])


def extract_evidence(src_pdf, pages, out_path):
    """pages: explicit list of 1-based physical page numbers (discrete loci allowed)."""
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(src_pdf)
    total = len(reader.pages)
    bad = [p for p in pages if not (1 <= p <= total)]
    if bad:
        sys.exit(f"ABORT: evidence pages {bad} out of bounds (source has {total} pages)")
    w = PdfWriter()
    for i in sorted(set(pages)):
        w.add_page(reader.pages[i - 1])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        w.write(f)
    return total


def main():
    row_id = sys.argv[1]
    man = check_input_drift()

    raw_path = os.path.join(RUN, "source_build/worker_out", f"{row_id}.raw.json")
    raw = json.load(open(raw_path, encoding="utf-8"))
    inv = inventory_row(row_id)

    # --- worker must not be able to silently rewrite immutable identity ---
    for k in ("claim_id", "citation_key", "occurrence_id"):
        if raw.get(k) != inv[k]:
            sys.exit(f"ABORT: worker returned {k}={raw.get(k)!r}, inventory says {inv[k]!r}")
    if raw["fact_checked"] not in VERDICTS:
        sys.exit(f"ABORT: invalid verdict {raw['fact_checked']!r}")

    # --- source identity ---
    pdf_manifest = {r["citation_key"]: r for r in csv.DictReader(
        open(os.path.join(ROOT, "references/pdf_manifest.tsv"), newline="", encoding="utf-8"), delimiter="\t")}
    mrec = pdf_manifest.get(inv["citation_key"])
    src_pdf = os.path.join(ROOT, "references", mrec["pdf_path"]) if mrec else None
    src_sha = mrec["sha256"] if mrec else "N/A"
    if src_pdf and sha256(src_pdf) != src_sha:
        sys.exit("ABORT: stored PDF hash differs from pdf_manifest.tsv — source integrity failure")

    # --- evidence extraction + page bounds check ---
    evidence_path = ""
    if src_pdf and raw.get("evidence_page_range"):
        spec = raw["evidence_page_range"]
        if isinstance(spec, (list, tuple)) and len(spec) > 2:
            pages = [int(x) for x in spec]                 # discrete loci
        else:
            f0, l0 = parse_range(spec)
            pages = list(range(f0, l0 + 1))                # contiguous range
        out = os.path.join(RUN, "evidence_pages", f"{row_id}.pdf")
        total = extract_evidence(src_pdf, pages, out)
        evidence_path = f"evidence_pages/{row_id}.pdf"
        pr = parse_range(raw["pdf_page_indices"])
        if pr and not (1 <= pr[0] <= pr[1] <= total):
            sys.exit(f"ABORT: pdf_page_indices {raw['pdf_page_indices']} out of bounds (1-{total})")

    anchor_words = len(raw["evidence_anchor"].split())
    if anchor_words > 12:
        sys.exit(f"ABORT: evidence_anchor has {anchor_words} words (max 12)")

    # --- USER CALIBRATION RULING (calibration gate): PDF_VERSION_MISMATCH fires per-row ONLY when the
    # BibLaTeX record describes the PUBLISHED article and the stored file is a preprint/working paper.
    # Mere revision drift (bib already types it as a working paper, stored file is a later revision)
    # is recorded as a run-level source-version finding instead of a duplicated per-row issue.
    PUBLISHED_VS_PREPRINT = {
        "goodman_bacon_difference_2021", "callaway_difference_2021", "sun_estimating_2021",
        "de_chaisemartin_two-way_2020", "santos_silva_log_2006", "chen_logs_2024",
    }
    demoted = []
    if inv["citation_key"] not in PUBLISHED_VS_PREPRINT:
        kept = []
        for iss in raw.get("issues", []):
            if iss["issue_code"] == "PDF_VERSION_MISMATCH":
                demoted.append(iss)
            else:
                kept.append(iss)
        raw["issues"] = kept
    if demoted:
        mpath = os.path.join(RUN, "run_manifest.json")
        mm = json.load(open(mpath, encoding="utf-8"))
        mm.setdefault("source_version_findings", []).append({
            "citation_key": inv["citation_key"], "detected_on_row": row_id,
            "classification": "REVISION_DRIFT_not_preprint_vs_published",
            "protocol_trigger_met": False,
            "stored_version": raw.get("source_version", ""),
            "demoted_from_row_issue_per_user_ruling": True,
            "detail_pt": demoted[0].get("mismatch_explanation_pt", ""),
        })
        json.dump(mm, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    issues = []
    for n, iss in enumerate(raw.get("issues", []), 1):
        issues.append({
            "issue_id": f"ISS-{row_id[1:]}-{n:02d}", "row_id": row_id,
            "issue_code": iss["issue_code"], "severity": iss["severity"],
            "claim_as_written_pt": iss["claim_as_written_pt"],
            "source_supports_pt": iss["source_supports_pt"],
            "mismatch_explanation_pt": iss["mismatch_explanation_pt"],
            "printed_pages": raw["printed_pages"], "pdf_page_indices": str(raw["pdf_page_indices"]),
            "source_locator": raw["source_locator"], "evidence_path": evidence_path,
            "recommended_revision_pt": iss["recommended_revision_pt"],
            "needs_new_source": bool(iss["needs_new_source"]),
            "recommended_action": iss["recommended_action"],
        })

    if (raw["fact_checked"] == "SUPPORTED") != (len(issues) == 0):
        sys.exit("ABORT: issue list must be empty iff verdict is SUPPORTED")

    result = {
        "row_id": row_id, "claim_id": inv["claim_id"], "citation_key": inv["citation_key"],
        "occurrence_id": inv["occurrence_id"], "section": inv["section"], "paragraph": inv["paragraph"],
        "work": inv["work"], "claim_type": inv["claim_type"],
        "affirmation_pt": inv["affirmation_pt"], "source_excerpt": inv["source_excerpt"],
        "fact_checked": raw["fact_checked"],
        "audit_status": "COMPLETED" if raw["fact_checked"] != "SOURCE_BLOCKED" else "BLOCKED",
        "pages": raw["printed_pages"],
        "printed_pages": raw["printed_pages"], "pdf_page_indices": str(raw["pdf_page_indices"]),
        "source_locator": raw["source_locator"], "evidence_summary_pt": raw["evidence_summary_pt"],
        "evidence_anchor": raw["evidence_anchor"], "evidence_path": evidence_path,
        "search_coverage": raw["search_coverage"], "source_version": raw["source_version"],
        "source_sha256": src_sha, "confidence": raw["confidence"], "issues": issues,
        "auditor_model": AUDITOR_MODEL, "auditor_reasoning_effort": AUDITOR_EFFORT,
        "audited_at": utcnow(),
    }
    if inv["claim_type"] == "AUTHOR_INFERENCE":
        pa = raw.get("premise_assessment")
        if not pa:
            sys.exit("ABORT: AUTHOR_INFERENCE row requires premise_assessment")
        result["premise_assessment"] = pa

    # --- schema validation ---
    import jsonschema
    schema = json.load(open(os.path.join(RUN, "claim_result.schema.json"), encoding="utf-8"))
    jsonschema.validate(result, schema)

    # --- atomic write ---
    dest = os.path.join(RUN, "results", f"{row_id}.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dest), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, dest)

    with open(os.path.join(RUN, "audit_log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": utcnow(), "row_id": row_id, "claim_id": inv["claim_id"],
            "citation_key": inv["citation_key"], "verdict": raw["fact_checked"],
            "confidence": raw["confidence"], "issue_codes": [i["issue_code"] for i in issues],
            "printed_pages": raw["printed_pages"], "pdf_page_indices": str(raw["pdf_page_indices"]),
            "evidence_path": evidence_path, "auditor_model": AUDITOR_MODEL,
            "input_hashes_verified": True,
        }, ensure_ascii=False) + "\n")

    # --- advance queue ---
    qpath = os.path.join(RUN, "queue.tsv")
    qrows = list(csv.DictReader(open(qpath, newline="", encoding="utf-8"), delimiter="\t"))
    for q in qrows:
        if q["row_id"] == row_id:
            q["status"] = "DONE"
    with open(qpath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(qrows[0].keys()), delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(qrows)

    print(f"COMMITTED {row_id}  verdict={result['fact_checked']}  conf={result['confidence']}  "
          f"printed={result['printed_pages']}  pdf={result['pdf_page_indices']}  "
          f"issues={[i['issue_code'] for i in issues]}  evidence={evidence_path or '(none)'}")


if __name__ == "__main__":
    main()
