#!/usr/bin/env python3
"""Build immutable four-page source packets for the current claim audit.

Unchanged packets are copied from the authoritative prior Codex run only after
their source hashes match the current PDF manifest. Changed PDFs are rebuilt
from the current portable reference files. The script never reads or mutates
Zotero's database.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter


RUN_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = RUN_DIR.parents[4]
SOURCE_BUILD = RUN_DIR / "source_build"
PRIOR_BUILD = (
    PROJECT_DIR
    / "references/claim_audit/runs/codex_sol_max/20260801T155350Z/source_build"
)
QUEUE_PATH = RUN_DIR / "queue.tsv"
PDF_MANIFEST = PROJECT_DIR / "references/pdf_manifest.tsv"
CHANGED_KEYS = {"brynjolfsson_canaries_2025", "humlum_still_2025"}
LEGAL_KEY = "brasil_decreto_12342_2024"
PAGES_PER_SPLIT = 4


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def current_hashes() -> dict[str, str]:
    return {
        row["citation_key"]: row["sha256"]
        for row in read_tsv(PDF_MANIFEST)
        if row.get("sha256")
    }


def copy_unchanged(key: str, expected_sha: str) -> None:
    source = PRIOR_BUILD / key
    manifest_path = source / "source_build_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Missing prior source manifest for {key}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_sha256") != expected_sha:
        raise SystemExit(
            f"Hash mismatch prevents packet reuse for {key}: "
            f"{manifest.get('source_sha256')} != {expected_sha}"
        )
    destination = SOURCE_BUILD / key
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def extract_page_text(pdf_path: Path, page_number: int) -> str:
    completed = subprocess.run(
        [
            "pdftotext",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-layout",
            str(pdf_path),
            "-",
        ],
        check=True,
        capture_output=True,
    )
    return completed.stdout.decode("utf-8", errors="replace").replace("\f", "").rstrip() + "\n"


def build_pdf(key: str, expected_sha: str) -> None:
    relative_pdf = Path("references/pdfs") / f"{key}.pdf"
    pdf_path = PROJECT_DIR / relative_pdf
    if not pdf_path.is_file():
        raise SystemExit(f"Missing current PDF for {key}: {pdf_path}")
    actual_sha = sha256(pdf_path)
    if actual_sha != expected_sha:
        raise SystemExit(f"Current PDF hash mismatch for {key}: {actual_sha} != {expected_sha}")

    destination = SOURCE_BUILD / key
    if destination.exists():
        shutil.rmtree(destination)
    splits_dir = destination / "splits"
    text_dir = destination / "page_text"
    splits_dir.mkdir(parents=True)
    text_dir.mkdir(parents=True)

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    split_entries: list[dict[str, object]] = []
    split_for_page: dict[int, str] = {}

    for start_zero in range(0, page_count, PAGES_PER_SPLIT):
        end_zero = min(start_zero + PAGES_PER_SPLIT, page_count)
        start = start_zero + 1
        end = end_zero
        split_name = f"{key}_pdfpp{start:04d}-{end:04d}.pdf"
        split_path = splits_dir / split_name
        writer = PdfWriter()
        for page_zero in range(start_zero, end_zero):
            writer.add_page(reader.pages[page_zero])
        with split_path.open("wb") as handle:
            writer.write(handle)
        relative_split = f"source_build/{key}/splits/{split_name}"
        for page_number in range(start, end + 1):
            split_for_page[page_number] = relative_split
        split_entries.append(
            {
                "pdf_page_indices": f"{start}-{end}",
                "path": relative_split,
                "sha256": sha256(split_path),
                "bytes": split_path.stat().st_size,
            }
        )

    page_entries: list[dict[str, object]] = []
    search_rows: list[tuple[int, str]] = []
    for page_number in range(1, page_count + 1):
        text = extract_page_text(pdf_path, page_number)
        text_name = f"pdf-{page_number:04d}.txt"
        text_path = text_dir / text_name
        text_path.write_text(text, encoding="utf-8")
        flattened = re.sub(r"\s+", " ", text).strip()
        search_rows.append((page_number, flattened))
        page_entries.append(
            {
                "pdf_page_index": page_number,
                "text_path": f"source_build/{key}/page_text/{text_name}",
                "text_sha256": sha256(text_path),
                "text_characters": len(text),
                "split_path": split_for_page[page_number],
            }
        )

    search_index = destination / "search_index.tsv"
    with search_index.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["pdf_page_index", "text"])
        writer.writerows(search_rows)

    page_index = {
        "citation_key": key,
        "source_path": relative_pdf.as_posix(),
        "source_sha256": actual_sha,
        "physical_pdf_pages": page_count,
        "extraction_method": "pdftotext -layout",
        "pages": page_entries,
    }
    (destination / "page_index.json").write_text(
        json.dumps(page_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    pdfinfo = subprocess.run(
        ["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True
    ).stdout
    (destination / "pdfinfo.txt").write_text(pdfinfo, encoding="utf-8")

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = {
        "citation_key": key,
        "source_path": relative_pdf.as_posix(),
        "source_sha256": actual_sha,
        "source_bytes": pdf_path.stat().st_size,
        "physical_pdf_pages": page_count,
        "pages_per_split": PAGES_PER_SPLIT,
        "split_count": len(split_entries),
        "splits": split_entries,
        "page_index_path": f"source_build/{key}/page_index.json",
        "search_index_path": f"source_build/{key}/search_index.tsv",
        "pdfinfo_path": f"source_build/{key}/pdfinfo.txt",
        "created_at": created_at,
    }
    (destination / "source_build_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def copy_legal_snapshot() -> None:
    source = PRIOR_BUILD / LEGAL_KEY
    manifest = json.loads((source / "source_build_manifest.json").read_text(encoding="utf-8"))
    snapshot = source / "official_snapshot.html"
    if sha256(snapshot) != manifest["source_sha256"]:
        raise SystemExit("Prior official legal snapshot hash no longer matches its manifest")
    destination = SOURCE_BUILD / LEGAL_KEY
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    copied_manifest_path = destination / "source_build_manifest.json"
    copied_manifest = json.loads(copied_manifest_path.read_text(encoding="utf-8"))
    copied_manifest["source_path"] = (
        destination / "official_snapshot.html"
    ).relative_to(PROJECT_DIR).as_posix()
    copied_manifest["search_text_path"] = (
        destination / "search_text.txt"
    ).relative_to(RUN_DIR).as_posix()
    copied_manifest_path.write_text(
        json.dumps(copied_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    keys = sorted({row["citation_key"] for row in read_tsv(QUEUE_PATH)})
    hashes = current_hashes()
    for key in keys:
        if key == LEGAL_KEY:
            copy_legal_snapshot()
        elif key in CHANGED_KEYS:
            build_pdf(key, hashes[key])
        else:
            copy_unchanged(key, hashes[key])

    summary = {
        "source_count": len(keys),
        "rebuilt_from_current_pdf": sorted(CHANGED_KEYS & set(keys)),
        "copied_after_hash_match": sorted(set(keys) - CHANGED_KEYS - {LEGAL_KEY}),
        "copied_immutable_legal_snapshot": LEGAL_KEY if LEGAL_KEY in keys else None,
        "pages_per_split": PAGES_PER_SPLIT,
    }
    (SOURCE_BUILD / "current_source_build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
