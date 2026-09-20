#!/usr/bin/env python3
"""Build immutable source and Notion manifests for the post-edit blind audit."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = RUN_DIR.parents[4]
PDF_MANIFEST = PROJECT_DIR / "references/pdf_manifest.tsv"
LIBRARY_BIB = PROJECT_DIR / "references/library.bib"
SNAPSHOT = RUN_DIR / "source_snapshot/notion_page.md"
PRIOR_LEGAL = (
    PROJECT_DIR
    / "references/claim_audit/runs/codex_sol_max/20260807T141925Z_current"
    / "source_build/brasil_decreto_12342_2024"
)

EXPECTED_PRIOR_NOTION_HASH = (
    "8586595c356286821810d789ad99821b1f6f667933b07abe243afeff3f957efa"
)
CURRENT_NOTION_HASH = (
    "f4718a8410b6deb087247656d798fbe97bc231c9d42a2b59ea661bb533c4fccf"
)
NOTION_FETCHED_AT = "2026-08-08T15:29:44.957Z"

CITED_KEYS = [
    "agarwal_combining_2023",
    "appel_anthropic_2026",
    "autor_skill_2003",
    "benitez_mirror_2024",
    "benjamini_controlling_1995",
    "bick_rapid_2024",
    "brasil_decreto_12342_2024",
    "brynjolfsson_canaries_2025",
    "callaway_difference_2021",
    "de_chaisemartin_two-way_2020",
    "chandar_tracking_2025",
    "chen_logs_2024",
    "eloundou_gpts_2023",
    "gmyrek_generative_2025",
    "hosseini_maasoum_generative_2025",
    "humlum_still_2025",
    "klein_teeselink_generative_2025",
    "osorio_o_2003",
    "rambachan_more_2023",
    "santos_silva_log_2006",
    "sun_estimating_2021",
    "teutloff_winners_2025",
]

SOURCE_VERSIONS = {
    "bick_rapid_2024": "Working Paper 2024-027F, revised 2025-10-27",
    "brynjolfsson_canaries_2025": "Stanford working paper, revised 2025-11-13",
    "chandar_tracking_2025": "SSRN manuscript, revised 2025-08-01",
    "hosseini_maasoum_generative_2025": "SSRN manuscript, revised 2026-06-06",
    "humlum_still_2025": "NBER Working Paper 33777, May 2025, revised March 2026",
    "klein_teeselink_generative_2025": "SSRN manuscript, revised 2025-12-21",
    "callaway_difference_2021": "Official author manuscript dated 2020-12-01",
    "de_chaisemartin_two-way_2020": "Official arXiv manuscript v7 dated 2020-03-05",
    "sun_estimating_2021": "Official arXiv manuscript v2 dated 2020-09-22",
    "chen_logs_2024": "Official arXiv manuscript v7 dated 2023-11-15",
    "santos_silva_log_2006": "CEP Discussion Paper 701 dated 2005-07",
}

SOURCE_URLS = {
    "callaway_difference_2021": "https://psantanna.com/files/Callaway_SantAnna_2020.pdf",
    "de_chaisemartin_two-way_2020": "https://arxiv.org/pdf/1803.08807",
    "sun_estimating_2021": "https://arxiv.org/pdf/1804.05785",
    "chen_logs_2024": "https://arxiv.org/pdf/2212.06080",
    "santos_silva_log_2006": "https://cep.lse.ac.uk/pubs/download/dp0701.pdf",
    "humlum_still_2025": "https://www.nber.org/system/files/working_papers/w33777/w33777.pdf",
    "brasil_decreto_12342_2024": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12342.htm",
}

MANUSCRIPT_FALLBACKS = {
    "callaway_difference_2021",
    "de_chaisemartin_two-way_2020",
    "sun_estimating_2021",
    "chen_logs_2024",
    "santos_silva_log_2006",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonicalize_notion_snapshot(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(r"<content>\s*(.*?)\s*</content>", value, flags=re.S)
    if match:
        value = match.group(1)
    value = re.sub(
        r"(https://prod-files-secure\.s3\.[^?\s)]+)\?[^)\s]+",
        r"\1",
        value,
    )
    lines = [re.sub(r"[\t ]+", " ", line).strip() for line in value.split("\n")]
    value = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", value).rstrip("\n") + "\n"


def parse_bib_entries(text: str) -> dict[str, str]:
    starts = list(re.finditer(r"^@[A-Za-z]+\{([^,\s]+),\s*$", text, flags=re.M))
    entries: dict[str, str] = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        entries[match.group(1)] = text[match.start():end]
    return entries


def bib_field(entry: str, field: str) -> str:
    match = re.search(rf"^\s*{re.escape(field)}\s*=\s*\{{(.*?)\}},\s*$", entry, flags=re.M | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def pdf_pages(path: Path) -> int:
    output = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True
    ).stdout
    match = re.search(r"^Pages:\s+(\d+)\s*$", output, flags=re.M)
    if not match:
        raise SystemExit(f"Could not read page count for {path}")
    return int(match.group(1))


def main() -> None:
    snapshot_raw = SNAPSHOT.read_text(encoding="utf-8")
    semantic = canonicalize_notion_snapshot(snapshot_raw)
    semantic_hash = hashlib.sha256(semantic.encode("utf-8")).hexdigest()
    if semantic_hash != CURRENT_NOTION_HASH:
        raise SystemExit(
            f"Unexpected current Notion hash: {semantic_hash} != {CURRENT_NOTION_HASH}"
        )

    snapshot_manifest = {
        "schema_version": "postedit-blind-snapshot-v1",
        "snapshot_id": "notion-33dcc8ca-4610-82bd-a888-0151f42ba19b-20260808T152944Z",
        "page_id": "33dcc8ca-4610-82bd-a888-0151f42ba19b",
        "page_title": "Dissertação de Mestrado V2 (1)",
        "page_url": "https://app.notion.com/p/33dcc8ca461082bda8880151f42ba19b",
        "fetched_at": NOTION_FETCHED_AT,
        "snapshot_path": SNAPSHOT.relative_to(PROJECT_DIR).as_posix(),
        "raw_sha256": sha256(SNAPSHOT),
        "raw_bytes": SNAPSHOT.stat().st_size,
        "semantic_sha256": semantic_hash,
        "semantic_characters": len(semantic),
        "expected_prior_semantic_sha256": EXPECTED_PRIOR_NOTION_HASH,
        "changed_from_expected": semantic_hash != EXPECTED_PRIOR_NOTION_HASH,
        "normalization": (
            "Notion content body only; signed image query parameters removed; "
            "line endings and horizontal whitespace normalized."
        ),
        "delta_policy": (
            "The current live snapshot is authoritative. The exact prior post-edit body "
            "is unavailable locally, so no prior judgment is reused solely from the old page hash."
        ),
    }
    (RUN_DIR / "source_snapshot/snapshot_manifest.json").write_text(
        json.dumps(snapshot_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest_rows = list(csv.DictReader(PDF_MANIFEST.open(encoding="utf-8"), delimiter="\t"))
    by_key = {row["citation_key"]: row for row in manifest_rows}
    if len(manifest_rows) != 43 or len(by_key) != 43:
        raise SystemExit("PDF manifest must contain 43 unique PDF rows")

    bib_entries = parse_bib_entries(LIBRARY_BIB.read_text(encoding="utf-8"))
    if len(bib_entries) != 44 or len(set(bib_entries)) != 44:
        raise SystemExit("library.bib must contain 44 unique entries")
    if set(CITED_KEYS) - set(bib_entries):
        raise SystemExit(f"Missing cited BibTeX keys: {sorted(set(CITED_KEYS) - set(bib_entries))}")

    legal_destination = RUN_DIR / "source_build/brasil_decreto_12342_2024"
    if legal_destination.exists():
        shutil.rmtree(legal_destination)
    shutil.copytree(PRIOR_LEGAL, legal_destination)
    legal_manifest_path = legal_destination / "source_build_manifest.json"
    legal_manifest = json.loads(legal_manifest_path.read_text(encoding="utf-8"))
    legal_snapshot = legal_destination / "official_snapshot.html"
    if sha256(legal_snapshot) != legal_manifest["source_sha256"]:
        raise SystemExit("Legal snapshot hash does not match its prior immutable manifest")
    legal_manifest["source_path"] = legal_snapshot.relative_to(PROJECT_DIR).as_posix()
    legal_manifest["search_text_path"] = (
        legal_destination / "search_text.txt"
    ).relative_to(RUN_DIR).as_posix()
    legal_manifest_path.write_text(
        json.dumps(legal_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    columns = [
        "citation_key", "bib_title", "bib_date", "doi", "source_type",
        "source_path", "source_sha256", "source_bytes", "physical_pages",
        "source_version", "source_url", "source_alignment_status",
        "notion_reference_status", "gate_status", "notes",
    ]
    output_rows: list[dict[str, object]] = []
    for key in CITED_KEYS:
        entry = bib_entries[key]
        if key == "brasil_decreto_12342_2024":
            source_type = "LEGAL_HTML"
            source_path = legal_snapshot
            source_hash = sha256(source_path)
            source_bytes = source_path.stat().st_size
            pages: int | str = "N/A"
        else:
            row = by_key[key]
            source_type = "PDF"
            source_path = PROJECT_DIR / "references" / row["pdf_path"]
            source_hash = sha256(source_path)
            if source_hash != row["sha256"]:
                raise SystemExit(f"PDF hash mismatch for {key}")
            source_bytes = source_path.stat().st_size
            pages = pdf_pages(source_path)

        if key in MANUSCRIPT_FALLBACKS:
            alignment = "ALIGNED_OFFICIAL_MANUSCRIPT_FALLBACK"
            notion_status = "AUDIT_SOURCE_NOTE_ONLY_IN_BIB"
            gate_status = "PASS_WITH_DECLARED_MANUSCRIPT"
            note = (
                "Use manuscript page labels only. Do not combine them with the journal "
                "page range. The audit-source note is present in library.bib but not in "
                "the current Notion reference entry."
            )
        elif key == "humlum_still_2025":
            alignment = "ALIGNED_CURRENT_NBER_REVISION"
            notion_status = "CONFLICT_PREVIOUS_TITLE_AND_YEAR"
            gate_status = "BLOCKED_NOTION_METADATA_CONFLICT"
            note = (
                "The official March 2026 revision is titled 'Still Waters, Rapid Currents: "
                "Early Labor Market Transformation under Generative AI' and is dated May "
                "2025, revised March 2026. Notion still cites the previous title and 2026."
            )
        else:
            alignment = "ALIGNED"
            notion_status = "ALIGNED"
            gate_status = "PASS"
            note = ""

        output_rows.append({
            "citation_key": key,
            "bib_title": bib_field(entry, "title").replace("{", "").replace("}", ""),
            "bib_date": bib_field(entry, "date"),
            "doi": bib_field(entry, "doi"),
            "source_type": source_type,
            "source_path": source_path.relative_to(PROJECT_DIR).as_posix(),
            "source_sha256": source_hash,
            "source_bytes": source_bytes,
            "physical_pages": pages,
            "source_version": SOURCE_VERSIONS.get(key, "Canonical PDF recorded in pdf_manifest.tsv"),
            "source_url": SOURCE_URLS.get(key, bib_field(entry, "url")),
            "source_alignment_status": alignment,
            "notion_reference_status": notion_status,
            "gate_status": gate_status,
            "notes": note,
        })

    source_manifest_path = RUN_DIR / "source_manifest.tsv"
    with source_manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    blocked = [row["citation_key"] for row in output_rows if str(row["gate_status"]).startswith("BLOCKED")]
    run_manifest = {
        "schema_version": "postedit-blind-run-v1",
        "run_id": RUN_DIR.name,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "SOURCE_GATE_BLOCKED" if blocked else "INVENTORY_READY",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "max",
        "fallback_allowed": False,
        "notion_snapshot_id": snapshot_manifest["snapshot_id"],
        "notion_semantic_sha256": semantic_hash,
        "expected_prior_notion_semantic_sha256": EXPECTED_PRIOR_NOTION_HASH,
        "notion_changed_from_expected": True,
        "library_entries": len(bib_entries),
        "pdf_entries": len(by_key),
        "cited_sources": len(CITED_KEYS),
        "cited_pdfs": len(CITED_KEYS) - 1,
        "cited_legal_sources": 1,
        "blocked_source_keys": blocked,
        "gate_policy": (
            "Inventory reconstruction may continue. Blind claim reading must not start "
            "until every blocked source key is resolved or the author explicitly approves "
            "a documented exception."
        ),
        "historical_runs_immutable": True,
        "notion_edits_allowed": False,
    }
    (RUN_DIR / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "library_entries": len(bib_entries),
        "pdf_entries": len(by_key),
        "cited_sources": len(CITED_KEYS),
        "blocked_source_keys": blocked,
        "notion_semantic_sha256": semantic_hash,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
