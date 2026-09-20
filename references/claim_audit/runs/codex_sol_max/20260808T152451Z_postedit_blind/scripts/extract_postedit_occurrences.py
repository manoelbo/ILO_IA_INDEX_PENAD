#!/usr/bin/env python3
"""Extract formal citation occurrences from the frozen post-edit Notion snapshot."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parents[1]
SNAPSHOT = RUN_DIR / "source_snapshot/notion_page.md"
SOURCE_MANIFEST = RUN_DIR / "source_manifest.tsv"

URL_MARKERS = {
    "10.20955/wp.2024.027": "bick_rapid_2024",
    "arxiv.2303.10130": "eloundou_gpts_2023",
    "canaries-in-the-coal-mine": "brynjolfsson_canaries_2025",
    "5425555": "hosseini_maasoum_generative_2025",
    "5516798": "klein_teeselink_generative_2025",
    "10.54394/hetp0387": "gmyrek_generative_2025",
    "10.1162/003355303322552801": "autor_skill_2003",
    "10.3386/w31422": "agarwal_combining_2023",
    "0013125": "benitez_mirror_2024",
    "mirror-mirror-wall": "benitez_mirror_2024",
    "economic-index-primitives": "appel_anthropic_2026",
    "d12342": "brasil_decreto_12342_2024",
    "e09cc868": "osorio_o_2003",
    "10.3386/w33777": "humlum_still_2025",
    "10.1016/j.jeconom.2020.12.001": "callaway_difference_2021",
    "10.1257/aer.20181169": "de_chaisemartin_two-way_2020",
    "10.1016/j.jeconom.2020.09.006": "sun_estimating_2021",
    "10.1093/qje/qjad054": "chen_logs_2024",
    "10.1162/rest.88.4.641": "santos_silva_log_2006",
    "10.1111/j.2517-6161.1995.tb02031.x": "benjamini_controlling_1995",
    "10.1016/j.jebo.2024.106845": "teutloff_winners_2025",
    "10.1093/restud/rdad018": "rambachan_more_2023",
    "10.2139/ssrn.5384519": "chandar_tracking_2025",
}

LINK_PATTERN = re.compile(r"(?<!!)\[([^\]]+)\]\((https?://[^)]+)\)")


def map_url(url: str) -> str | None:
    lowered = url.lower()
    for marker, key in URL_MARKERS.items():
        if marker in lowered:
            return key
    return None


def content_body(raw: str) -> str:
    return raw.split("<content>", 1)[1].split("</content>", 1)[0]


def row_context(lines: list[str], index: int) -> tuple[str, int, int]:
    if not lines[index].lstrip().startswith("<td>"):
        return lines[index].strip(), index, index
    start = index
    while start >= 0 and lines[start].strip() != "<tr>":
        start -= 1
    end = index
    while end < len(lines) and lines[end].strip() != "</tr>":
        end += 1
    if start < 0 or end >= len(lines):
        return lines[index].strip(), index, index
    return "\n".join(lines[start:end + 1]).strip(), start, end


def main() -> None:
    manifest_rows = list(csv.DictReader(SOURCE_MANIFEST.open(encoding="utf-8"), delimiter="\t"))
    works = {row["citation_key"]: row["bib_title"] for row in manifest_rows}

    body = content_body(SNAPSHOT.read_text(encoding="utf-8"))
    body = body.split("# **REFERÊNCIAS**", 1)[0]
    lines = body.splitlines()

    section = "Front matter"
    paragraph_counters: defaultdict[str, int] = defaultdict(int)
    line_locations: dict[int, tuple[str, str]] = {}
    in_table = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            section = re.sub(r"^#+\s*", "", stripped).replace("**", "").strip()
            continue
        if stripped.startswith("<table"):
            in_table = True
        if stripped == "</table>":
            in_table = False
        if stripped and not stripped.startswith(("<", "!", "$$")) and not stripped.startswith("-"):
            paragraph_counters[section] += 1
        if stripped:
            label = f"table-row-near-{index + 1}" if in_table else str(paragraph_counters[section])
            line_locations[index] = (section, label)

    raw_occurrences: list[dict[str, object]] = []
    context_numbers: dict[tuple[int, int], int] = {}
    for index, line in enumerate(lines):
        matches = []
        for match in LINK_PATTERN.finditer(line):
            key = map_url(match.group(2))
            if key:
                matches.append((match.start(), match.end(), match.group(1), match.group(2), key))
        if not matches:
            continue

        groups: list[list[tuple[int, int, str, str, str]]] = []
        for item in matches:
            if (
                groups
                and item[4] == groups[-1][-1][4]
                and re.fullmatch(r"[\s*_]*", line[groups[-1][-1][1]:item[0]])
            ):
                groups[-1].append(item)
            else:
                groups.append([item])

        context, start, end = row_context(lines, index)
        context_key = (start, end)
        if context_key not in context_numbers:
            context_numbers[context_key] = len(context_numbers) + 1
        context_id = f"CTX-REV-{context_numbers[context_key]:03d}"
        section_name, paragraph = line_locations.get(index, (section, "N/A"))

        for group in groups:
            key = group[0][4]
            raw_occurrences.append({
                "occurrence_id": "",
                "context_id": context_id,
                "document_line": index + 1,
                "section": section_name,
                "paragraph": paragraph,
                "citation_key": key,
                "work": works[key],
                "citation_text": "".join(item[2] for item in group).strip(),
                "citation_url": group[0][3],
                "citation_start": group[0][0],
                "citation_end": group[-1][1],
                "source_context": context,
            })

    for number, row in enumerate(raw_occurrences, 1):
        row["occurrence_id"] = f"CIT-REV-{number:03d}"

    expected_keys = set(works)
    actual_keys = {str(row["citation_key"]) for row in raw_occurrences}
    if expected_keys != actual_keys:
        raise SystemExit(
            f"Occurrence/source key mismatch: missing={sorted(expected_keys-actual_keys)}, "
            f"extra={sorted(actual_keys-expected_keys)}"
        )
    if len(raw_occurrences) != 61:
        raise SystemExit(f"Expected 61 current formal occurrences, found {len(raw_occurrences)}")

    columns = [
        "occurrence_id", "context_id", "document_line", "section", "paragraph",
        "citation_key", "work", "citation_text", "citation_url",
        "citation_start", "citation_end", "source_context",
    ]
    tsv_path = RUN_DIR / "citation_occurrences_postedit.tsv"
    with tsv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(raw_occurrences)

    packet = {
        "schema_version": "postedit-occurrence-packets-v1",
        "snapshot_id": "notion-33dcc8ca-4610-82bd-a888-0151f42ba19b-20260808T152944Z",
        "rules": {
            "unit": "one formal citation occurrence",
            "include": "all atomic propositions in the sentence containing the citation; explicit immediate anaphora only",
            "exclude": "reference list and merely instrumental uncited mentions",
        },
        "occurrences": raw_occurrences,
    }
    (RUN_DIR / "source_snapshot/occurrence_packets.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "occurrences": len(raw_occurrences),
        "contexts": len({row["context_id"] for row in raw_occurrences}),
        "keys": len(actual_keys),
        "by_key": dict(sorted(Counter(str(row["citation_key"]) for row in raw_occurrences).items())),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
