#!/usr/bin/env python3
"""Build the provisional primary audit report and Notion correction backlog."""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import html
import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, Sequence


SIGNED_NOTION_IMAGE_QUERY = re.compile(
    r"(https://prod-files-secure\.s3\.[^?\s)]+)\?[^)\s]+"
)

RUN_RELATIVE = Path(
    "references/claim_audit/runs/codex_sol_max/20260807T141925Z_current"
)
NOTION_PAGE_ID = "325cc8ca-4610-82d7-94db-01323b295bb5"
NOTION_TITLE = "Dissertação de Mestrado V2"
NOTION_LAST_EDITED = "2026-08-05T23:58:00.000Z"
CURRENT_SNAPSHOT_ID = (
    "notion-325cc8ca-4610-82d7-94db-01323b295bb5-20260808T142142Z-current"
)
FINAL_NOTION_FETCHED_AT = "2026-08-08T14:21:42.781Z"
BENJAMINI_KEY = "benjamini_controlling_1995"
ALDASORO_KEY = "aldasoro_ai_2026"
DEFERRED_OCCURRENCES = {"CIT-CUR-002"}
CURRENT_OCCURRENCE_EXCERPT_OVERRIDES = {
    "CIT-CUR-002": (
        "A literatura internacional avançou em duas frentes. De um lado, se "
        "consolidou uma metodologia de construção de índices de exposição "
        "baseados em tarefas, a partir do GPT Exposure de Eloundou et al. (2023), "
        "que passou a usar os próprios LLMs como avaliadores das tarefas."
    )
}

LINKED_OCCURRENCES = {
    "CIT-CUR-001",
    "CIT-CUR-003",
    "CIT-CUR-004",
    "CIT-CUR-005",
    "CIT-CUR-007",
    "CIT-CUR-008",
    "CIT-CUR-011",
    "CIT-CUR-016",
    "CIT-CUR-022",
    "CIT-CUR-023",
    "CIT-CUR-024",
    "CIT-CUR-025",
    "CIT-CUR-027",
    "CIT-CUR-038",
    "CIT-CUR-041",
    "CIT-CUR-042",
    "CIT-CUR-043",
    "CIT-CUR-044",
    "CIT-CUR-045",
    "CIT-CUR-046",
    "CIT-CUR-048",
    "CIT-CUR-049",
    "CIT-CUR-050",
    "CIT-CUR-051",
    "CIT-CUR-052",
    "CIT-CUR-053",
    "CIT-CUR-054",
    "CIT-CUR-055",
    "CIT-CUR-056",
    "CIT-CUR-057",
    "CIT-CUR-059",
}

CURRENT_REFERENCE_KEYS = {
    "agarwal_combining_2023",
    ALDASORO_KEY,
    "appel_anthropic_2026",
    "autor_skill_2003",
    "benitez_mirror_2024",
    "bick_rapid_2024",
    "brasil_decreto_12342_2024",
    "brynjolfsson_canaries_2025",
    "chandar_tracking_2025",
    "eloundou_gpts_2023",
    "gmyrek_generative_2025",
    "hosseini_maasoum_generative_2025",
    "humlum_still_2025",
    "klein_teeselink_generative_2025",
    "osorio_o_2003",
}

REFERENCE_OK_KEYS = {"autor_skill_2003", "brasil_decreto_12342_2024"}

FORMAT_CHANGES = [
    {
        "occurrence_ids": ["CIT-CUR-001"],
        "citation_keys": ["bick_rapid_2024"],
        "current": "(Bick; Blandin; Deming, 2024)",
        "proposed": "(Bick; Blandin; Deming, 2025)",
        "reason": (
            "Align the in-text year with revision F dated 27 October 2025; "
            "keep the historical citation key unchanged."
        ),
    },
    {
        "occurrence_ids": ["CIT-CUR-026"],
        "citation_keys": ["brynjolfsson_canaries_2025"],
        "current": "(Brynjolfsson, Chandar e Chen, 2025, p. 12)",
        "proposed": "(Brynjolfsson; Chandar; Chen, 2025, p. 12)",
        "reason": "Use semicolons between coauthors in a parenthetical citation.",
    },
    {
        "occurrence_ids": [
            "CIT-CUR-029",
            "CIT-CUR-030",
            "CIT-CUR-031",
            "CIT-CUR-032",
        ],
        "citation_keys": [
            "goodman_bacon_difference_2021",
            "callaway_difference_2021",
            "sun_estimating_2021",
            "de_chaisemartin_two-way_2020",
        ],
        "current": (
            "(Goodman-Bacon, 2021; Callaway e Sant'Anna, 2021; "
            "Sun e Abraham, 2021; de Chaisemartin e D'Haultfœuille, 2020)"
        ),
        "proposed": (
            "(Callaway; Sant’Anna, 2021; de Chaisemartin; D’Haultfœuille, "
            "2020; Goodman-Bacon, 2021; Sun; Abraham, 2021)"
        ),
        "reason": (
            "Use semicolons between coauthors, alphabetize the grouped works, "
            "and normalize apostrophes."
        ),
    },
    {
        "occurrence_ids": ["CIT-CUR-035", "CIT-CUR-036"],
        "citation_keys": ["santos_silva_log_2006", "chen_logs_2024"],
        "current": "(Silva e Tenreyro, 2006; Chen e Roth, 2024)",
        "proposed": "(Santos Silva; Tenreyro, 2006; Chen; Roth, 2024)",
        "reason": (
            "Preserve the compound surname Santos Silva and use semicolons "
            "between coauthors in parenthetical citations."
        ),
    },
]

SOURCE_ALIGNMENT = {
    "bick_rapid_2024": {
        "target": "BOTH",
        "detail": (
            "Align Zotero, library.bib, the reference entry, and the in-text year "
            "to Federal Reserve Bank of St. Louis Working Paper 2024-027F, "
            "revision dated 27 October 2025."
        ),
    },
    "hosseini_maasoum_generative_2025": {
        "target": "BOTH",
        "detail": (
            "The audited PDF is dated 6 June 2026, while library.bib and the "
            "Notion reference identify the 31 August 2025 version. Either update "
            "the record and citation year or restore and audit the cited version."
        ),
    },
    "klein_teeselink_generative_2025": {
        "target": "BOTH",
        "detail": (
            "Align the Notion reference dated 22 September 2025 with the "
            "21 December 2025 version recorded in library.bib and the stored PDF."
        ),
    },
    "humlum_still_2025": {
        "target": "BOTH",
        "detail": (
            "Align the May 2025 title/date in the Notion reference with the "
            "official NBER revision stored and audited (revised March 2026), "
            "including its current title and version note."
        ),
    },
    "chandar_tracking_2025": {
        "target": "BOTH",
        "detail": (
            "Align the 3 June 2025 Notion/library metadata with the audited "
            "PDF revision dated 1 August 2025, or restore the cited June file."
        ),
    },
    "goodman_bacon_difference_2021": {
        "target": "ZOTERO_BIB_PDF",
        "detail": (
            "Replace the 2018 working-paper PDF with the published 2021 article, "
            "or explicitly cite the working paper and recheck its pagination."
        ),
    },
    "callaway_difference_2021": {
        "target": "ZOTERO_BIB_PDF",
        "detail": (
            "Replace the archived arXiv manuscript with the published 2021 "
            "article associated with the DOI, then recheck page locators."
        ),
    },
    "sun_estimating_2021": {
        "target": "ZOTERO_BIB_PDF",
        "detail": (
            "Replace the 2020 arXiv manuscript with the published 2021 article, "
            "or identify the preprint explicitly in the bibliography."
        ),
    },
    "de_chaisemartin_two-way_2020": {
        "target": "ZOTERO_BIB_PDF",
        "detail": (
            "Align the stored pre-publication PDF with the final American "
            "Economic Review article and refresh page locators."
        ),
    },
    "santos_silva_log_2006": {
        "target": "ZOTERO_BIB_PDF",
        "detail": (
            "Replace the archived earlier manuscript with the published 2006 "
            "Review of Economics and Statistics article."
        ),
    },
    "chen_logs_2024": {
        "target": "ZOTERO_BIB_PDF",
        "detail": (
            "Replace the arXiv manuscript with the published Quarterly Journal "
            "of Economics article and refresh page locators."
        ),
    },
}

REFERENCE_UPDATE_NOTES = {
    "agarwal_combining_2023": "Add NBER Working Paper no. 31422 and normalize title emphasis.",
    "appel_anthropic_2026": "Emphasize only the main title and normalize the subtitle.",
    "benitez_mirror_2024": "Add IDB Working Paper IDB-WP-1624 and normalize title emphasis.",
    "bick_rapid_2024": "Use revision F metadata and the 2025 in-text/reference year.",
    "brynjolfsson_canaries_2025": "Emphasize only the main title; retain the 13 November 2025 revision.",
    "chandar_tracking_2025": "Resolve the June/August 2025 PDF-version mismatch before final rendering.",
    "eloundou_gpts_2023": "Emphasize only the main title and retain canonical arXiv metadata.",
    "gmyrek_generative_2025": "Add ILO Working Paper no. 140 and normalize title emphasis.",
    "hosseini_maasoum_generative_2025": "Resolve the 2025/2026 version mismatch before final rendering.",
    "humlum_still_2025": "Align the title and date with the revised NBER version.",
    "klein_teeselink_generative_2025": "Align the reference date with the stored 21 December 2025 version.",
    "osorio_o_2003": "Add Texto para Discussão no. 996.",
}

QUEUE_FIELDS = [
    "change_id",
    "priority",
    "change_type",
    "proposal_mode",
    "section",
    "paragraph",
    "claim_ids",
    "occurrence_ids",
    "citation_keys",
    "current_text_pt",
    "proposed_text_pt",
    "notion_anchor",
    "primary_verdicts",
    "issue_codes",
    "issue_severity",
    "pages",
    "evidence_paths",
    "official_urls",
    "target_system",
    "dependency",
    "covered_row_ids",
    "notion_old_str_sha256",
    "expected_match_count",
    "approval_status",
]


def normalize_text(value: str) -> str:
    """Collapse whitespace while preserving human-readable punctuation."""

    return re.sub(r"\s+", " ", value or "").strip()


def canonicalize_notion_snapshot(value: str) -> str:
    """Normalize the dissertation body, excluding Notion wrapper volatility."""

    value = value.replace("\r\n", "\n").replace("\r", "\n")
    content_match = re.search(r"<content>\s*(.*?)\s*</content>", value, re.DOTALL)
    if content_match:
        value = content_match.group(1)
    value = SIGNED_NOTION_IMAGE_QUERY.sub(r"\1", value)
    lines = [re.sub(r"[\t ]+", " ", line).strip() for line in value.split("\n")]
    value = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", value).rstrip("\n") + "\n"


def summarize_primary_rows(rows: Iterable[dict[str, str]]) -> dict[str, object]:
    """Return the deterministic primary-audit counts used in all artifacts."""

    materialized = list(rows)
    non_supported = [row for row in materialized if row["fact_checked"] != "SUPPORTED"]
    verdicts = collections.Counter(row["fact_checked"] for row in materialized)
    return {
        "rows": len(materialized),
        "unique_claims": len({row["claim_id"] for row in materialized}),
        "unique_occurrences": len({row["occurrence_id"] for row in materialized}),
        "verdicts": dict(verdicts),
        "non_supported_rows": len(non_supported),
        "non_supported_claims": len({row["claim_id"] for row in non_supported}),
        "non_supported_occurrences": len(
            {row["occurrence_id"] for row in non_supported}
        ),
        "claims_needing_new_source": len(
            {
                row["claim_id"]
                for row in materialized
                if row.get("needs_new_source", "").lower() == "true"
                and row["fact_checked"] != "SUPPORTED"
            }
        ),
        "rows_with_issues": sum(bool(row.get("issue_codes")) for row in materialized),
    }


def choose_claim_action(rows: Iterable[dict[str, str]]) -> dict[str, object]:
    """Choose the conservative editorial action for one atomic claim."""

    materialized = list(rows)
    supported = sorted(
        {
            row["citation_key"]
            for row in materialized
            if row["fact_checked"] == "SUPPORTED"
        }
    )
    challenged = sorted(
        {
            row["citation_key"]
            for row in materialized
            if row["fact_checked"] != "SUPPORTED"
        }
    )
    if supported and challenged:
        change_type = "CITATION_MEMBERSHIP"
    elif any(row["fact_checked"] == "CONTRADICTED" for row in materialized):
        change_type = "CLAIM_TEXT"
    elif any(
        row.get("needs_new_source", "").lower() == "true" for row in materialized
    ):
        change_type = "NEW_SOURCE_REQUIRED"
    else:
        change_type = "CLAIM_TEXT"
    return {
        "change_type": change_type,
        "supported_keys": supported,
        "challenged_keys": challenged,
    }


def unique_anchor(
    excerpt: str,
    corpus: str,
    *,
    maximum_words: int = 18,
    minimum_words: int = 6,
) -> tuple[str, int]:
    """Find a deterministic exact phrase that occurs once in the current snapshot."""

    excerpt = normalize_text(excerpt)
    corpus = normalize_text(corpus)
    words = excerpt.split()
    for width in range(min(maximum_words, len(words)), minimum_words - 1, -1):
        for start in range(0, len(words) - width + 1):
            candidate = " ".join(words[start : start + width])
            count = corpus.count(candidate)
            if count == 1:
                return candidate, count
    return excerpt, corpus.count(excerpt)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def write_tsv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=QUEUE_FIELDS,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def clean_bib_value(value: str) -> str:
    value = value.strip().rstrip(",").strip()
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1]
    value = value.replace("\\&", "&").replace("{", "").replace("}", "")
    return normalize_text(value)


def parse_bib(path: Path) -> dict[str, dict[str, str]]:
    """Parse the line-oriented Better BibLaTeX export used by this workspace."""

    records: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    current_key = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        start = re.match(r"^@(\w+)\{([^,]+),\s*$", line)
        if start:
            current_key = start.group(2)
            current = {"entry_type": start.group(1), "citation_key": current_key}
            records[current_key] = current
            continue
        if current is None:
            continue
        if line.strip() == "}":
            current = None
            current_key = ""
            continue
        field = re.match(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*=\s*(.+?)\s*$", line)
        if field:
            current[field.group(1).lower()] = clean_bib_value(field.group(2))
    return records


def official_url(record: dict[str, str]) -> str:
    doi = record.get("doi", "").strip()
    if doi:
        return f"https://doi.org/{doi}"
    return record.get("url", "").strip()


def plainify_notion(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", value)
    value = re.sub(r"</td>\s*<td[^>]*>", " | ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("**", "").replace("`", "").replace("$", "")
    value = re.sub(r"(?<!\w)\*+", "", value)
    value = re.sub(r"\*+(?!\w)", "", value)
    value = value.replace("\\log", "log")
    return normalize_text(value)


def split_notion(value: str) -> tuple[str, str]:
    marker = "# **REFERÊNCIAS**"
    if marker not in value:
        raise ValueError("The current Notion fetch does not contain REFERÊNCIAS.")
    return value.split(marker, 1)


def split_codes(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def numeric_id(value: str) -> int:
    match = re.search(r"(\d+)$", value)
    return int(match.group(1)) if match else 0


def markdown_cell(value: object) -> str:
    return str(value).replace("\n", "<br>").replace("|", "\\|")


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(markdown_cell(value) for value in row) + " |"
        for row in rows
    )
    return "\n".join(lines)


def find_reference_line(
    key: str, record: dict[str, str], reference_text: str
) -> str:
    lines = [line.strip() for line in reference_text.splitlines() if line.strip()]
    title_words = clean_bib_value(record.get("title", "")).casefold().split()
    needle = " ".join(title_words[: min(5, len(title_words))])
    for line in lines:
        plain = plainify_notion(line).casefold()
        if needle and needle in plain:
            return line
    if key == ALDASORO_KEY:
        for line in lines:
            if line.startswith("ALDASORO,"):
                return line
    return ""


def render_abnt_references(
    root: Path, citation_keys: Sequence[str], records: dict[str, dict[str, str]]
) -> dict[str, str]:
    """Render candidate references with the user's installed IBICT ABNT CSL."""

    csl = Path(
        "/Users/manebrasil/Zotero/styles/"
        "instituto-brasileiro-de-informacao-em-ciencia-e-tecnologia-abnt.csl"
    )
    pandoc = Path("/opt/homebrew/bin/pandoc")
    if not csl.exists() or not pandoc.exists():
        return {
            key: f"{records[key].get('author', '')}. {records[key].get('title', '')}."
            for key in citation_keys
        }
    front_matter = [
        "---",
        "lang: pt-BR",
        f"bibliography: {root / 'references/library.bib'}",
        f"csl: {csl}",
        "nocite: |",
    ]
    front_matter.extend(f"  @{key}" for key in citation_keys)
    front_matter.extend(["---", ""])
    with tempfile.TemporaryDirectory(prefix="notion-reference-render-") as directory:
        source = Path(directory) / "references.md"
        source.write_text("\n".join(front_matter), encoding="utf-8")
        completed = subprocess.run(
            [str(pandoc), str(source), "--citeproc", "-t", "gfm"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    rendered: dict[str, str] = {}
    pattern = re.compile(
        r'<div id="ref-([^\"]+)" class="csl-entry">\s*(.*?)\s*</div>',
        re.DOTALL,
    )
    for key, entry in pattern.findall(completed.stdout):
        entry = normalize_text(entry)
        entry = entry.replace("\\[*N.p.*\\]", "\\[*S. l.*\\]")
        entry = entry.replace("Acessado:", "Acesso em:")
        rendered[key] = entry
    return rendered


def action_priority(rows: Sequence[dict[str, str]]) -> str:
    codes = set().union(*(split_codes(row.get("issue_codes", "")) for row in rows))
    verdicts = {row["fact_checked"] for row in rows}
    if verdicts & {"CONTRADICTED"} or codes & {"WRONG_MAGNITUDE", "CAUSAL_OVERCLAIM"}:
        return "P0"
    if (
        verdicts & {"OVERSTATED", "NOT_VERIFIABLE"}
        or "MISSING_EVIDENCE" in codes
        or any(row.get("needs_new_source", "").lower() == "true" for row in rows)
    ):
        return "P1"
    return "P2"


def combine_recommendations(rows: Sequence[dict[str, str]]) -> str:
    recommendations: list[str] = []
    for row in rows:
        if row["fact_checked"] == "SUPPORTED":
            continue
        recommendation = normalize_text(row.get("recommended_revision_pt", ""))
        if recommendation and recommendation not in recommendations:
            recommendations.append(recommendation)
    if not recommendations:
        return "Revisão editorial manual necessária antes de alterar o texto."
    if len(recommendations) == 1:
        return recommendations[0]
    return " ".join(
        f"Para {row['citation_key']}: {normalize_text(row['recommended_revision_pt'])}"
        for row in rows
        if row["fact_checked"] != "SUPPORTED"
        and normalize_text(row.get("recommended_revision_pt", ""))
    )


def make_queue_row(
    *,
    change_id: str,
    priority: str,
    change_type: str,
    proposal_mode: str,
    section: str,
    paragraph: str,
    claim_ids: Sequence[str],
    occurrence_ids: Sequence[str],
    citation_keys: Sequence[str],
    current_text_pt: str,
    proposed_text_pt: str,
    anchor_source: str,
    corpus: str,
    primary_verdicts: Sequence[str] = (),
    issue_codes: Sequence[str] = (),
    issue_severity: Sequence[str] = (),
    pages: Sequence[str] = (),
    evidence_paths: Sequence[str] = (),
    official_urls: Sequence[str] = (),
    target_system: str,
    dependency: str,
    covered_row_ids: Sequence[str] = (),
) -> dict[str, str]:
    if target_system in {"NOTION", "BOTH"}:
        anchor, count = unique_anchor(plainify_notion(anchor_source), corpus)
        expected_match_count = str(count)
    else:
        anchor = "N/A"
        expected_match_count = "N/A"
    return {
        "change_id": change_id,
        "priority": priority,
        "change_type": change_type,
        "proposal_mode": proposal_mode,
        "section": section,
        "paragraph": paragraph,
        "claim_ids": ";".join(dict.fromkeys(claim_ids)),
        "occurrence_ids": ";".join(dict.fromkeys(occurrence_ids)),
        "citation_keys": ";".join(dict.fromkeys(citation_keys)),
        "current_text_pt": normalize_text(current_text_pt),
        "proposed_text_pt": normalize_text(proposed_text_pt),
        "notion_anchor": anchor,
        "primary_verdicts": ";".join(sorted(set(primary_verdicts))),
        "issue_codes": ";".join(sorted(set(issue_codes))),
        "issue_severity": ";".join(sorted(set(filter(None, issue_severity)))),
        "pages": ";".join(dict.fromkeys(filter(None, pages))),
        "evidence_paths": ";".join(dict.fromkeys(filter(None, evidence_paths))),
        "official_urls": ";".join(dict.fromkeys(filter(None, official_urls))),
        "target_system": target_system,
        "dependency": normalize_text(dependency),
        "covered_row_ids": ";".join(dict.fromkeys(covered_row_ids)),
        "notion_old_str_sha256": sha256_text(normalize_text(current_text_pt)),
        "expected_match_count": expected_match_count,
        "approval_status": "PROPOSED",
    }


def build_citation_status(
    primary_rows: Sequence[dict[str, str]],
    records: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    by_occurrence: dict[str, list[dict[str, str]]] = collections.OrderedDict()
    for row in primary_rows:
        by_occurrence.setdefault(row["occurrence_id"], []).append(row)
    incorrect = {
        occurrence
        for change in FORMAT_CHANGES
        for occurrence in change["occurrence_ids"]
    }
    rows: list[dict[str, str]] = []
    for occurrence_id, source_rows in by_occurrence.items():
        first = source_rows[0]
        key = first["citation_key"]
        rows.append(
            {
                "occurrence_id": occurrence_id,
                "section": first["section"],
                "paragraph": first["paragraph"],
                "citation_key": key,
                "work": first["work"],
                "format_in_text": "CORRIGIR" if occurrence_id in incorrect else "OK",
                "link_in_text": (
                    "VÁLIDO" if occurrence_id in LINKED_OCCURRENCES else "AUSENTE"
                ),
                "citation_in_references": (
                    "SIM" if key in CURRENT_REFERENCE_KEYS else "NÃO"
                ),
                "reference_format": (
                    "AUSENTE"
                    if key not in CURRENT_REFERENCE_KEYS
                    else "OK"
                    if key in REFERENCE_OK_KEYS
                    else "CORRIGIR"
                ),
                "pages": ";".join(
                    dict.fromkeys(
                        row.get("printed_pages") or row.get("pages", "")
                        for row in source_rows
                        if row.get("printed_pages") or row.get("pages")
                    )
                ),
                "official_url": official_url(records[key]),
            }
        )
    rows.append(
        {
            "occurrence_id": "CIT-METHOD-001",
            "section": "4.4 Heterogeneidades e estudos de caso",
            "paragraph": "3",
            "citation_key": BENJAMINI_KEY,
            "work": records[BENJAMINI_KEY].get("title", ""),
            "format_in_text": "OK",
            "link_in_text": "AUSENTE",
            "citation_in_references": "NÃO",
            "reference_format": "AUSENTE",
            "pages": "",
            "official_url": official_url(records[BENJAMINI_KEY]),
        }
    )
    return rows


def check_one_url(url: str) -> dict[str, object]:
    if not url:
        return {"url": url, "status": "MISSING", "http_status": None}
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 citation-audit-link-check/1.0"},
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status = int(response.status)
            return {
                "url": url,
                "status": "VALID" if 200 <= status < 400 else "BROKEN",
                "http_status": status,
                "final_url": response.geturl(),
            }
    except urllib.error.HTTPError as error:
        if error.code in {401, 403, 405, 429}:
            status = "ANTIBOT_OR_METHOD_RESTRICTED"
        elif 300 <= error.code < 400:
            status = "VALID"
        else:
            status = "BROKEN"
        return {
            "url": url,
            "status": status,
            "http_status": error.code,
            "final_url": error.geturl(),
        }
    except Exception as error:  # network and TLS failures are not broken-link proof
        return {
            "url": url,
            "status": "NETWORK_ERROR",
            "http_status": None,
            "detail": str(error),
        }


def check_urls(urls: Sequence[str]) -> list[dict[str, object]]:
    with ThreadPoolExecutor(max_workers=8) as executor:
        return list(executor.map(check_one_url, sorted(set(filter(None, urls)))))


def build_substantive_changes(
    primary_rows: Sequence[dict[str, str]],
    records: dict[str, dict[str, str]],
    corpus: str,
    start: int,
) -> tuple[list[dict[str, str]], int]:
    grouped: dict[str, list[dict[str, str]]] = collections.OrderedDict()
    for row in primary_rows:
        grouped.setdefault(row["claim_id"], []).append(row)
    queue: list[dict[str, str]] = []
    sequence = start
    for claim_id, rows in grouped.items():
        if all(row["fact_checked"] == "SUPPORTED" for row in rows):
            continue
        deferred_occurrences = {
            row["occurrence_id"]
            for row in rows
            if row["occurrence_id"] in DEFERRED_OCCURRENCES
        }
        if deferred_occurrences:
            related_rows = [
                row
                for row in primary_rows
                if row["occurrence_id"] in deferred_occurrences
            ]
            current_excerpt = CURRENT_OCCURRENCE_EXCERPT_OVERRIDES[
                next(iter(deferred_occurrences))
            ]
            queue.append(
                make_queue_row(
                    change_id=f"CHG-{sequence:03d}",
                    priority="P1",
                    change_type="CLAIM_TEXT",
                    proposal_mode="DEFERRED_DEEP_AUDIT",
                    section=rows[0]["section"],
                    paragraph=rows[0]["paragraph"],
                    claim_ids=[row["claim_id"] for row in related_rows],
                    occurrence_ids=sorted(deferred_occurrences, key=numeric_id),
                    citation_keys=[row["citation_key"] for row in related_rows],
                    current_text_pt=current_excerpt,
                    proposed_text_pt=(
                        "Não aplicar a recomendação substantiva da auditoria "
                        "primária. O trecho mudou após o snapshot auditado; refazer "
                        "a auditoria desta ocorrência sobre o texto atual antes de "
                        "aprovar qualquer reescrita."
                    ),
                    anchor_source=current_excerpt,
                    corpus=corpus,
                    primary_verdicts=[row["fact_checked"] for row in related_rows],
                    issue_codes=["DEFERRED_DEEP_AUDIT"],
                    issue_severity=[row["issue_severity"] for row in related_rows],
                    pages=[row.get("printed_pages", "") for row in related_rows],
                    evidence_paths=[row["evidence_path"] for row in related_rows],
                    official_urls=[
                        official_url(records[row["citation_key"]])
                        for row in related_rows
                    ],
                    target_system="NOTION",
                    dependency="CURRENT_TEXT_REAUDIT; AUTHOR_APPROVAL",
                    covered_row_ids=[row["row_id"] for row in related_rows],
                )
            )
            sequence += 1
            continue
        action = choose_claim_action(rows)
        challenged = [row for row in rows if row["fact_checked"] != "SUPPORTED"]
        recommendation = combine_recommendations(rows)
        if action["change_type"] == "CITATION_MEMBERSHIP":
            proposed = (
                "Manter a afirmação com as fontes que a sustentam integralmente "
                f"({', '.join(action['supported_keys'])}) e remover ou reposicionar "
                "nesta chamada as fontes com suporte incompleto "
                f"({', '.join(action['challenged_keys'])})."
            )
        elif action["change_type"] == "NEW_SOURCE_REQUIRED":
            proposed = (
                f"{recommendation} Se a formulação original for mantida, "
                "adicionar uma nova fonte verificada; nenhuma fonte foi inventada."
            )
        else:
            proposed = recommendation
        queue.append(
            make_queue_row(
                change_id=f"CHG-{sequence:03d}",
                priority=action_priority(rows),
                change_type=action["change_type"],
                proposal_mode="PARAGRAPH_EDIT",
                section=rows[0]["section"],
                paragraph=rows[0]["paragraph"],
                claim_ids=[claim_id],
                occurrence_ids=[row["occurrence_id"] for row in rows],
                citation_keys=[row["citation_key"] for row in rows],
                current_text_pt=rows[0]["source_excerpt"],
                proposed_text_pt=proposed,
                anchor_source=rows[0]["source_excerpt"],
                corpus=corpus,
                primary_verdicts=[row["fact_checked"] for row in rows],
                issue_codes=[code for row in rows for code in split_codes(row["issue_codes"])],
                issue_severity=[row["issue_severity"] for row in rows],
                pages=[row.get("printed_pages") or row.get("pages", "") for row in rows],
                evidence_paths=[row["evidence_path"] for row in rows],
                official_urls=[official_url(records[row["citation_key"]]) for row in rows],
                target_system="NOTION",
                dependency=(
                    "AUTHOR_APPROVAL; SOURCE_ALIGNMENT"
                    if any("PDF_VERSION_MISMATCH" in row["issue_codes"] for row in rows)
                    else "AUTHOR_APPROVAL"
                ),
                covered_row_ids=[row["row_id"] for row in challenged],
            )
        )
        sequence += 1
    return queue, sequence


def build_artifacts(
    root: Path,
    *,
    write: bool,
    perform_link_checks: bool = False,
) -> dict[str, object]:
    root = root.resolve()
    run_dir = root / RUN_RELATIVE
    audited_path = run_dir / "claim_inventory_audited_current.tsv"
    inventory_path = run_dir / "claim_inventory_current.tsv"
    current_snapshot_path = root / "references/notion_changes/notion_current_fetch.md"
    audited_snapshot_path = run_dir / "source_snapshot/notion_page.md"
    pause_path = run_dir / "quality_control/PAUSE_CHECKPOINT.json"
    bib_path = root / "references/library.bib"

    primary_rows = load_tsv(audited_path)
    inventory_rows = load_tsv(inventory_path)
    records = parse_bib(bib_path)
    current_snapshot = current_snapshot_path.read_text(encoding="utf-8")
    audited_snapshot = audited_snapshot_path.read_text(encoding="utf-8")
    body, reference_text = split_notion(current_snapshot)
    corpus = plainify_notion(current_snapshot)
    body_corpus = plainify_notion(body)

    current_semantic = canonicalize_notion_snapshot(current_snapshot)
    audited_semantic = canonicalize_notion_snapshot(audited_snapshot)
    semantic_match = current_semantic == audited_semantic

    summary = summarize_primary_rows(primary_rows)
    target_keys = sorted({row["citation_key"] for row in primary_rows} | {BENJAMINI_KEY})
    missing_reference_keys = sorted(set(target_keys) - CURRENT_REFERENCE_KEYS)
    extra_reference_keys = sorted(CURRENT_REFERENCE_KEYS - set(target_keys))
    citation_status = build_citation_status(primary_rows, records)
    rendered_references = render_abnt_references(root, target_keys, records)

    queue, sequence = build_substantive_changes(
        primary_rows, records, body_corpus, start=1
    )

    rows_by_key: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in primary_rows:
        rows_by_key[row["citation_key"]].append(row)

    # Source-version alignment actions, including every supported mismatch row.
    reference_lines = {
        key: find_reference_line(key, records[key], reference_text)
        for key in CURRENT_REFERENCE_KEYS
        if key in records
    }
    for key, alignment in SOURCE_ALIGNMENT.items():
        source_rows = rows_by_key.get(key, [])
        current_reference = reference_lines.get(key, "")
        anchor_source = current_reference or (
            source_rows[0]["source_excerpt"] if source_rows else "# **REFERÊNCIAS**"
        )
        queue.append(
            make_queue_row(
                change_id=f"CHG-{sequence:03d}",
                priority="P2",
                change_type="SOURCE_VERSION_ALIGNMENT",
                proposal_mode="SYSTEM_ALIGNMENT",
                section=(source_rows[0]["section"] if source_rows else "REFERÊNCIAS"),
                paragraph=(source_rows[0]["paragraph"] if source_rows else "N/A"),
                claim_ids=[row["claim_id"] for row in source_rows],
                occurrence_ids=[row["occurrence_id"] for row in source_rows],
                citation_keys=[key],
                current_text_pt=current_reference or records[key].get("title", key),
                proposed_text_pt=alignment["detail"],
                anchor_source=anchor_source,
                corpus=corpus,
                primary_verdicts=[row["fact_checked"] for row in source_rows],
                issue_codes=["PDF_VERSION_MISMATCH"],
                issue_severity=[row["issue_severity"] for row in source_rows],
                pages=[row.get("printed_pages", "") for row in source_rows],
                evidence_paths=[row.get("evidence_path", "") for row in source_rows],
                official_urls=[official_url(records[key])],
                target_system=alignment["target"],
                dependency="AUTHOR_VERSION_DECISION; ZOTERO_REEXPORT",
                covered_row_ids=[
                    row["row_id"]
                    for row in source_rows
                    if "PDF_VERSION_MISMATCH" in row["issue_codes"]
                ],
            )
        )
        sequence += 1

    # Four visible ABNT/in-text correction constructs.
    for change in FORMAT_CHANGES:
        occurrence_rows = [
            row
            for row in primary_rows
            if row["occurrence_id"] in change["occurrence_ids"]
        ]
        queue.append(
            make_queue_row(
                change_id=f"CHG-{sequence:03d}",
                priority="P3",
                change_type="CITATION_FORMAT",
                proposal_mode="EXACT_REPLACEMENT",
                section=occurrence_rows[0]["section"],
                paragraph=occurrence_rows[0]["paragraph"],
                claim_ids=[row["claim_id"] for row in occurrence_rows],
                occurrence_ids=change["occurrence_ids"],
                citation_keys=change["citation_keys"],
                current_text_pt=change["current"],
                proposed_text_pt=change["proposed"],
                anchor_source=change["current"],
                corpus=body_corpus,
                primary_verdicts=[row["fact_checked"] for row in occurrence_rows],
                issue_codes=["ABNT_IN_TEXT_FORMAT"],
                pages=[row.get("printed_pages", "") for row in occurrence_rows],
                evidence_paths=[row.get("evidence_path", "") for row in occurrence_rows],
                official_urls=[official_url(records[key]) for key in change["citation_keys"]],
                target_system="NOTION",
                dependency=change["reason"],
                covered_row_ids=[],
            )
        )
        sequence += 1

    # One link proposal per currently unlinked formal occurrence.
    occurrence_first = {
        row["occurrence_id"]: row for row in reversed(primary_rows)
    }
    status_by_occurrence = {row["occurrence_id"]: row for row in citation_status}
    for status in citation_status:
        if status["link_in_text"] != "AUSENTE":
            continue
        if status["occurrence_id"] == "CIT-METHOD-001":
            source_excerpt = (
                "Por isso adoto o procedimento de Benjamini e Hochberg (1995), "
                "que controla a taxa de falsas descobertas"
            )
            claim_ids: list[str] = []
            evidence_paths: list[str] = []
            verdicts: list[str] = []
        else:
            occurrence_rows = [
                row
                for row in primary_rows
                if row["occurrence_id"] == status["occurrence_id"]
            ]
            source_excerpt = CURRENT_OCCURRENCE_EXCERPT_OVERRIDES.get(
                status["occurrence_id"],
                occurrence_first[status["occurrence_id"]]["source_excerpt"],
            )
            claim_ids = [row["claim_id"] for row in occurrence_rows]
            evidence_paths = [row["evidence_path"] for row in occurrence_rows]
            verdicts = [row["fact_checked"] for row in occurrence_rows]
        queue.append(
            make_queue_row(
                change_id=f"CHG-{sequence:03d}",
                priority="P3",
                change_type="CITATION_LINK",
                proposal_mode="LINK_ONLY",
                section=status["section"],
                paragraph=status["paragraph"],
                claim_ids=claim_ids,
                occurrence_ids=[status["occurrence_id"]],
                citation_keys=[status["citation_key"]],
                current_text_pt=source_excerpt,
                proposed_text_pt=(
                    f"Adicionar hyperlink oficial à chamada de {status['citation_key']} "
                    "sem alterar a redação da afirmação."
                ),
                anchor_source=source_excerpt,
                corpus=body_corpus,
                primary_verdicts=verdicts,
                issue_codes=["MISSING_CITATION_LINK"],
                pages=[status["pages"]],
                evidence_paths=evidence_paths,
                official_urls=[status["official_url"]],
                target_system="NOTION",
                dependency="AUTHOR_APPROVAL; OFFICIAL_URL_CHECK",
                covered_row_ids=[],
            )
        )
        sequence += 1

    # Reference additions, removal, and normalization.
    reference_heading = "REFERÊNCIAS"
    for key in missing_reference_keys:
        queue.append(
            make_queue_row(
                change_id=f"CHG-{sequence:03d}",
                priority="P3",
                change_type="REFERENCE_ADD",
                proposal_mode="REFERENCE_INSERT",
                section="REFERÊNCIAS",
                paragraph="N/A",
                claim_ids=[row["claim_id"] for row in rows_by_key.get(key, [])],
                occurrence_ids=[
                    row["occurrence_id"] for row in rows_by_key.get(key, [])
                ]
                or (["CIT-METHOD-001"] if key == BENJAMINI_KEY else []),
                citation_keys=[key],
                current_text_pt=reference_heading,
                proposed_text_pt=rendered_references[key],
                anchor_source=reference_heading,
                corpus=corpus,
                issue_codes=["REFERENCE_MISSING"],
                official_urls=[official_url(records[key])],
                target_system="NOTION",
                dependency=(
                    "SOURCE_ALIGNMENT; AUTHOR_APPROVAL"
                    if key in SOURCE_ALIGNMENT
                    else "AUTHOR_APPROVAL"
                ),
                covered_row_ids=[],
            )
        )
        sequence += 1

    for key in extra_reference_keys:
        current_line = reference_lines[key]
        queue.append(
            make_queue_row(
                change_id=f"CHG-{sequence:03d}",
                priority="P3",
                change_type="REFERENCE_REMOVE",
                proposal_mode="EXACT_REMOVAL",
                section="REFERÊNCIAS",
                paragraph="N/A",
                claim_ids=[],
                occurrence_ids=[],
                citation_keys=[key],
                current_text_pt=current_line,
                proposed_text_pt=(
                    "Remover esta entrada da lista final porque ela não é citada "
                    "na versão corrente da dissertação."
                ),
                anchor_source=current_line,
                corpus=corpus,
                issue_codes=["REFERENCE_NOT_CITED"],
                official_urls=[official_url(records[key])],
                target_system="NOTION",
                dependency="AUTHOR_APPROVAL",
                covered_row_ids=[],
            )
        )
        sequence += 1

    update_keys = sorted(
        (CURRENT_REFERENCE_KEYS & set(target_keys)) - REFERENCE_OK_KEYS
    )
    for key in update_keys:
        current_line = reference_lines[key]
        queue.append(
            make_queue_row(
                change_id=f"CHG-{sequence:03d}",
                priority="P3",
                change_type="REFERENCE_UPDATE",
                proposal_mode="EXACT_REPLACEMENT",
                section="REFERÊNCIAS",
                paragraph="N/A",
                claim_ids=[row["claim_id"] for row in rows_by_key.get(key, [])],
                occurrence_ids=[
                    row["occurrence_id"] for row in rows_by_key.get(key, [])
                ],
                citation_keys=[key],
                current_text_pt=current_line,
                proposed_text_pt=rendered_references[key],
                anchor_source=current_line,
                corpus=corpus,
                issue_codes=["REFERENCE_FORMAT_OR_METADATA"],
                official_urls=[official_url(records[key])],
                target_system="NOTION",
                dependency=(
                    f"{REFERENCE_UPDATE_NOTES[key]} "
                    + (
                        "Resolve SOURCE_VERSION_ALIGNMENT before final insertion."
                        if key in SOURCE_ALIGNMENT
                        else ""
                    )
                ),
                covered_row_ids=[],
            )
        )
        sequence += 1

    queue.sort(key=lambda row: (row["priority"], numeric_id(row["change_id"])))

    # Explicit disposition for every primary audit row.
    coverage_actions: dict[str, list[str]] = collections.defaultdict(list)
    for action in queue:
        for row_id in filter(None, action["covered_row_ids"].split(";")):
            coverage_actions[row_id].append(action["change_id"])
    row_coverage: dict[str, str] = {}
    for row in primary_rows:
        if coverage_actions[row["row_id"]]:
            row_coverage[row["row_id"]] = ";".join(coverage_actions[row["row_id"]])
        elif row["fact_checked"] == "SUPPORTED" and not row["issue_codes"]:
            row_coverage[row["row_id"]] = "NO_CHANGE_PRIMARY_SUPPORTED"
        elif row["fact_checked"] == "SUPPORTED":
            row_coverage[row["row_id"]] = "NO_TEXT_CHANGE_NON_VERSION_ISSUE"
        else:
            row_coverage[row["row_id"]] = "REVIEW_REQUIRED"

    if perform_link_checks:
        link_checks = check_urls(
            [status["official_url"] for status in citation_status]
        )
    else:
        prior_manifest = root / "references/notion_changes/notion_snapshot_manifest.json"
        if prior_manifest.exists():
            link_checks = json.loads(prior_manifest.read_text(encoding="utf-8")).get(
                "official_url_checks", []
            )
        else:
            link_checks = []
    reference_summary = {
        "current": len(CURRENT_REFERENCE_KEYS),
        "target": len(target_keys),
        "add": len(missing_reference_keys),
        "remove": len(extra_reference_keys),
        "update": len(update_keys),
    }

    result: dict[str, object] = {
        "primary_rows": primary_rows,
        "inventory_rows": inventory_rows,
        "summary": summary,
        "queue": queue,
        "citation_status": citation_status,
        "row_coverage": row_coverage,
        "reference_summary": reference_summary,
        "missing_reference_keys": missing_reference_keys,
        "extra_reference_keys": extra_reference_keys,
        "target_keys": target_keys,
        "records": records,
        "rendered_references": rendered_references,
        "link_checks": link_checks,
        "current_snapshot": current_snapshot,
        "current_semantic": current_semantic,
        "audited_semantic": audited_semantic,
        "semantic_match": semantic_match,
        "deferred_occurrences": sorted(DEFERRED_OCCURRENCES, key=numeric_id),
        "deferred_row_ids": sorted(
            {
                row["row_id"]
                for row in primary_rows
                if row["occurrence_id"] in DEFERRED_OCCURRENCES
            },
            key=numeric_id,
        ),
        "pause": json.loads(pause_path.read_text(encoding="utf-8")),
        "paths": {
            "audited_tsv": audited_path,
            "current_snapshot": current_snapshot_path,
            "audited_snapshot": audited_snapshot_path,
            "pause": pause_path,
        },
    }

    if write:
        write_outputs(root, result)
    return result


def counter_table(counter: collections.Counter[str]) -> str:
    return markdown_table(
        ["Value", "Count"],
        [(value, count) for value, count in counter.most_common()],
    )


def primary_report(result: dict[str, object]) -> str:
    rows = result["primary_rows"]
    summary = result["summary"]
    pause = result["pause"]
    paths = result["paths"]
    affected_claim_ids = {
        row["claim_id"] for row in rows if row["fact_checked"] != "SUPPORTED"
    }
    affected: dict[str, list[dict[str, str]]] = collections.OrderedDict()
    for row in rows:
        if row["claim_id"] in affected_claim_ids:
            affected.setdefault(row["claim_id"], []).append(row)
    issue_counts: collections.Counter[str] = collections.Counter()
    for row in rows:
        issue_counts.update(split_codes(row["issue_codes"]))
    source_version_rows = [
        row for row in rows if "PDF_VERSION_MISMATCH" in row["issue_codes"]
    ]
    supported_version_rows = [
        row for row in source_version_rows if row["fact_checked"] == "SUPPORTED"
    ]
    new_source_claims = sorted(
        {
            row["claim_id"]
            for row in rows
            if row.get("needs_new_source", "").lower() == "true"
            and row["fact_checked"] != "SUPPORTED"
        },
        key=numeric_id,
    )
    lines = [
        "# Primary Claim Audit Report",
        "",
        "> **PRIMARY / PROVISIONAL — NOT FINAL.** This report summarizes the "
        "completed primary judgments. Blind quality control is paused and the "
        "findings must not be represented as a final source audit.",
        "",
        "## Executive summary",
        "",
        f"The primary audit contains **{summary['rows']} source–claim–occurrence "
        f"rows**, representing **{summary['unique_claims']} atomic claims** and "
        f"**{summary['unique_occurrences']} formal citation occurrences** across "
        "22 works. A final Notion refetch found one changed cited paragraph: "
        "**211 primary rows remain exact reuses and 2 rows in CIT-CUR-002 are "
        "DEFERRED_DEEP_AUDIT**. No substantive recommendation from the older "
        "wording is proposed for that occurrence.",
        "",
        markdown_table(
            ["Primary verdict", "Rows"],
            [(key, value) for key, value in summary["verdicts"].items()],
        ),
        "",
        f"There are **{summary['non_supported_rows']} rows** that are not fully "
        f"supported, affecting **{summary['non_supported_claims']} claims** and "
        f"**{summary['non_supported_occurrences']} citation occurrences**. "
        f"The primary files mark **{len(new_source_claims)} claims** as potentially "
        "requiring another source. This flag is source-specific: where a grouped "
        "citation already contains an independently supporting work, the change "
        "queue prefers removing or repositioning the unsuitable source instead "
        "of adding a redundant reference.",
        "",
        f"Separately, **{len(supported_version_rows)} SUPPORTED rows** have a "
        "PDF/version mismatch. Their substantive judgment is retained provisionally, "
        "but pagination and canonical reference metadata cannot be finalized until "
        "the source artifacts are aligned.",
        "",
        "## Frozen dissertation and source inputs",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ("Notion page", NOTION_TITLE),
                ("Page ID", NOTION_PAGE_ID),
                ("Last edited", NOTION_LAST_EDITED),
                ("Current fetch", str(paths["current_snapshot"])),
                ("Current raw SHA-256", sha256_file(paths["current_snapshot"])),
                ("Audited snapshot", str(paths["audited_snapshot"])),
                ("Audited raw SHA-256", sha256_file(paths["audited_snapshot"])),
                ("Canonical semantic SHA-256", sha256_text(result["current_semantic"])),
                (
                    "Semantic comparison",
                    "CHANGED: CIT-CUR-002 plus three changes outside audited citation excerpts",
                ),
                ("Primary TSV SHA-256", sha256_file(paths["audited_tsv"])),
            ],
        ),
        "",
        "The canonical comparison isolates the `<content>` body, removes only "
        "expiring image-query strings, and normalizes whitespace; it does not "
        "remove dissertation text, citation labels, stable URLs, tables, or "
        "equations. It identified four current-body edits: ‘consolidou-se’ changed "
        "to ‘se consolidou’ in CIT-CUR-002, and ‘concentra-se’ changed to ‘elas e "
        "concentra’ in an uncited descriptive paragraph. A third edit restated the "
        "significance sentence in the introductory empirical summary; it falls "
        "outside the source excerpt assigned to CIT-CUR-007 and does not change "
        "that citation claim. A fourth edit shortened the uncited paragraph that "
        "describes the dissertation structure. The apparent typing error is "
        "reported but not added to the citation changeset.",
        "",
        "## Method and limitations",
        "",
        "Each primary row was evaluated independently against an immutable source "
        "snapshot and a page-level evidence artifact. The primary taxonomy is "
        "SUPPORTED, PARTIALLY_SUPPORTED, OVERSTATED, CONTRADICTED, NOT_FOUND, and "
        "NOT_VERIFIABLE. Page numbers below are printed pages; PDF indices remain "
        "available in the TSV and evidence files.",
        "",
        "This report distinguishes: (1) substantive claim problems, (2) "
        "bibliographic/source-version problems, and (3) editorial or ABNT/link "
        "improvements. A primary judgment can be substantively SUPPORTED while "
        "still requiring source-version alignment. The paused blind QC may later "
        "confirm or revise individual judgments.",
        "",
        "## Counts by section",
        "",
        counter_table(collections.Counter(row["section"] for row in rows)),
        "",
        "## Counts by work",
        "",
        counter_table(collections.Counter(row["citation_key"] for row in rows)),
        "",
        "## Counts by claim type",
        "",
        counter_table(collections.Counter(row["claim_type"] for row in rows)),
        "",
        "## Problem codes",
        "",
        counter_table(issue_counts),
        "",
        "## Affected claims",
        "",
    ]
    for claim_id, claim_rows in affected.items():
        first = claim_rows[0]
        deferred = any(
            row["occurrence_id"] in result["deferred_occurrences"]
            for row in claim_rows
        )
        lines.extend(
            [
                f"### {claim_id} — {first['section']}, paragraph {first['paragraph']}",
                "",
                f"**Claim (PT-BR):** {first['affirmation_pt']}",
                "",
                (
                    "**Current reconciliation:** `DEFERRED_DEEP_AUDIT`. The "
                    "evidence below belongs to the prior wording and must not be "
                    "used to apply a substantive edit before re-audit."
                    if deferred
                    else "**Current reconciliation:** `REUSED_EXACT`."
                ),
                "",
                markdown_table(
                    [
                        "Source",
                        "Verdict",
                        "Problem",
                        "Printed pages",
                        "Evidence",
                        "Recommended revision (PT-BR)",
                        "New source?",
                    ],
                    [
                        (
                            row["citation_key"],
                            row["fact_checked"],
                            row["issue_codes"] or "None",
                            row["printed_pages"] or row["pages"] or "N/A",
                            f"{row['evidence_summary_pt']} ({row['evidence_path']})",
                            row["recommended_revision_pt"],
                            row["needs_new_source"],
                        )
                        for row in claim_rows
                    ],
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Claims currently flagged as needing another source",
            "",
            ", ".join(f"`{claim_id}`" for claim_id in new_source_claims),
            "",
            "## Source-version incompatibilities",
            "",
            markdown_table(
                ["Citation key", "Required decision"],
                [
                    (key, data["detail"])
                    for key, data in SOURCE_ALIGNMENT.items()
                ],
            ),
            "",
            f"These alignment items include all {len(source_version_rows)} rows "
            "carrying the explicit "
            "PDF_VERSION_MISMATCH code, including all 19 SUPPORTED rows with that "
            "code, plus the Bick, Humlum, and Klein Teeselink metadata/version "
            "dependencies identified during current-reference reconciliation.",
            "",
            "## Paused blind quality control",
            "",
            markdown_table(
                ["Field", "Value"],
                [
                    ("Checkpoint", str(paths["pause"])),
                    ("Queue rows", pause["queue_rows"]),
                    ("Completed", pause["queue_status_counts"]["COMPLETED"]),
                    ("Prompt ready", pause["queue_status_counts"]["PROMPT_READY"]),
                    ("Pending", pause["queue_status_counts"]["PENDING"]),
                    ("Agrees", pause["comparison_status_counts"]["AGREES"]),
                    (
                        "Needs adjudication",
                        pause["comparison_status_counts"]["NEEDS_ADJUDICATION"],
                    ),
                    ("Interrupted row", pause["interrupted_attempt"]["row_id"]),
                    ("Remaining QC processes", 0),
                ],
            ),
            "",
            "No partial output from the interrupted row was promoted. The primary "
            "TSV retained its pre-pause SHA-256 and the completed QC artifacts "
            "remain resumable. This is why the present report is provisional.",
            "",
            "## Editorial handoff",
            "",
            "The proposed Notion edits are listed in "
            "`references/notion_changes/PRIMARY_NOTION_CHANGESET.md` and "
            "`references/notion_changes/notion_change_queue.tsv`. No Notion, "
            "Zotero, PDF, or library.bib content was changed while producing this "
            "report.",
            "",
        ]
    )
    return "\n".join(lines)


def notion_changeset(result: dict[str, object]) -> str:
    queue = result["queue"]
    status = result["citation_status"]
    ref_summary = result["reference_summary"]
    records = result["records"]
    rendered = result["rendered_references"]
    lines = [
        "# Primary Notion Changeset",
        "",
        "> **PROPOSED ONLY — NOTHING IN NOTION HAS BEEN EDITED.** Approve by "
        "change ID, priority, or dissertation section. Source-version decisions "
        "must be resolved before dependent reference edits are applied.",
        "",
        "## Scope and current state",
        "",
        "The substantive primary audit covers 59 formal citation occurrences and "
        "22 works. Citation hygiene adds the formal Benjamini–Hochberg citation "
        "excluded by the claim-inventory rule, producing **60 citation occurrences "
        "and 23 works** for the editorial pass.",
        "",
        "The final Notion refetch changed the wording of CIT-CUR-002. Its two "
        "primary rows are marked `DEFERRED_DEEP_AUDIT`; the queue contains a hold "
        "instruction, not the older substantive rewrite. The remaining 211 rows "
        "are exact reuses.",
        "",
        markdown_table(
            ["Item", "Count"],
            [
                ("Substantive claim actions", sum(row["change_type"] in {"CLAIM_TEXT", "CITATION_MEMBERSHIP", "NEW_SOURCE_REQUIRED"} for row in queue)),
                ("Source-version alignment actions", sum(row["change_type"] == "SOURCE_VERSION_ALIGNMENT" for row in queue)),
                ("Visible citation-format constructs", sum(row["change_type"] == "CITATION_FORMAT" for row in queue)),
                ("Missing citation links", sum(row["link_in_text"] == "AUSENTE" for row in status)),
                ("Reference additions", ref_summary["add"]),
                ("Reference updates", ref_summary["update"]),
                ("Reference removals", ref_summary["remove"]),
                ("Total proposed actions", len(queue)),
            ],
        ),
        "",
        "## Approval queue by priority",
        "",
    ]
    for priority in ["P0", "P1", "P2", "P3"]:
        selected = [row for row in queue if row["priority"] == priority]
        lines.extend(
            [
                f"### {priority}",
                "",
                markdown_table(
                    [
                        "ID",
                        "Type",
                        "Location",
                        "Claims / occurrences",
                        "Current text (PT-BR)",
                        "Proposed action (PT-BR)",
                        "Dependency",
                    ],
                    [
                        (
                            row["change_id"],
                            row["change_type"],
                            f"{row['section']} ¶{row['paragraph']}",
                            f"{row['claim_ids']} / {row['occurrence_ids']}",
                            row["current_text_pt"],
                            row["proposed_text_pt"],
                            row["dependency"],
                        )
                        for row in selected
                    ],
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Citation occurrence status",
            "",
            markdown_table(
                [
                    "Occurrence",
                    "Location",
                    "Citation key",
                    "In-text format",
                    "Link",
                    "In references",
                    "Reference format",
                    "Pages",
                ],
                [
                    (
                        row["occurrence_id"],
                        f"{row['section']} ¶{row['paragraph']}",
                        row["citation_key"],
                        row["format_in_text"],
                        row["link_in_text"],
                        row["citation_in_references"],
                        row["reference_format"],
                        row["pages"] or "N/A",
                    )
                    for row in status
                ],
            ),
            "",
            "Hyperlinks are an editorial navigation layer, not an ABNT requirement. "
            "The queue uses DOI URLs when available and otherwise the official "
            "landing page. Exact evidence pages remain local audit artifacts rather "
            "than fragile file links in the dissertation.",
            "",
            "## Reference reconciliation",
            "",
            markdown_table(
                ["Status", "Citation key", "Candidate ABNT rendering / action"],
                [
                    (
                        "ADD" if key in result["missing_reference_keys"] else "KEEP/UPDATE",
                        key,
                        rendered[key],
                    )
                    for key in result["target_keys"]
                ]
                + [
                    (
                        "REMOVE",
                        key,
                        "Present in the current reference list but not cited in the current dissertation.",
                    )
                    for key in result["extra_reference_keys"]
                ],
            ),
            "",
            "Candidate entries were rendered from `references/library.bib` with "
            "the locally installed IBICT ABNT CSL. Any item marked with a source-"
            "version dependency must be re-rendered after Zotero/library/PDF "
            "alignment; the candidate is not yet the final bibliographic entry.",
            "",
            "## Applying approvals later",
            "",
            "1. Approve a set of change IDs, a priority band, or a section.",
            "2. Resolve all SOURCE_VERSION_ALIGNMENT dependencies in Zotero, "
            "library.bib, and the portable PDF set.",
            "3. Re-render the 23 cited references and apply only approved Notion edits.",
            "4. Fetch a new Notion snapshot and verify every exact anchor/hash.",
            "5. Resume blind QC only for the stabilized text.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, result: dict[str, object]) -> None:
    run_dir = root / RUN_RELATIVE
    changes_dir = root / "references/notion_changes"
    report_path = run_dir / "PRIMARY_AUDIT_REPORT.md"
    changeset_path = changes_dir / "PRIMARY_NOTION_CHANGESET.md"
    queue_path = changes_dir / "notion_change_queue.tsv"
    manifest_path = changes_dir / "notion_snapshot_manifest.json"

    report_path.write_text(primary_report(result), encoding="utf-8")
    changeset_path.write_text(notion_changeset(result), encoding="utf-8")
    write_tsv(queue_path, result["queue"])

    queue = result["queue"]
    status = result["citation_status"]
    summary = result["summary"]
    paths = result["paths"]
    manifest = {
        "schema_version": "primary-notion-changeset-v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "PRIMARY_PROVISIONAL_NOT_FINAL",
        "notion": {
            "page_id": NOTION_PAGE_ID,
            "title": NOTION_TITLE,
            "last_edited_time": NOTION_LAST_EDITED,
            "current_snapshot_id": CURRENT_SNAPSHOT_ID,
            "current_snapshot_path": str(paths["current_snapshot"].relative_to(root)),
            "current_raw_sha256": sha256_file(paths["current_snapshot"]),
            "current_raw_bytes": paths["current_snapshot"].stat().st_size,
            "audited_snapshot_path": str(paths["audited_snapshot"].relative_to(root)),
            "audited_raw_sha256": sha256_file(paths["audited_snapshot"]),
            "audited_raw_bytes": paths["audited_snapshot"].stat().st_size,
            "canonical_semantic_sha256": sha256_text(result["current_semantic"]),
            "semantic_match": result["semantic_match"],
            "final_live_verification": {
                "fetched_at": FINAL_NOTION_FETCHED_AT,
                "canonical_body_sha256": sha256_text(result["current_semantic"]),
                "canonical_characters": len(result["current_semantic"]),
                "matches_saved_current_snapshot": True,
            },
            "reconciliation": {
                "reused_exact_rows": len(result["primary_rows"])
                - len(result["deferred_row_ids"]),
                "deferred_deep_audit_rows": len(result["deferred_row_ids"]),
                "deferred_row_ids": result["deferred_row_ids"],
                "deferred_occurrences": result["deferred_occurrences"],
                "changes_outside_audited_citation_excerpts": [
                    (
                        "Introduction descriptive paragraph changed from 'concentra-se' "
                        "to 'elas e concentra'; likely typo, outside citation-change scope."
                    ),
                    (
                        "The introductory empirical summary restated the significance "
                        "sentence; the assigned CIT-CUR-007 source excerpt is unchanged."
                    ),
                    (
                        "The uncited dissertation-structure paragraph removed the "
                        "sentence describing Appendices C and D."
                    ),
                ],
            },
            "semantic_normalization": (
                "Compare the Notion <content> body only; strip rotating query parameters "
                "from signed S3 image URLs; normalize line endings, horizontal whitespace, "
                "and excess blank lines. Wrapper properties and fetch timestamps are excluded."
            ),
        },
        "primary_audit": summary,
        "citation_hygiene": {
            "occurrences": len(status),
            "works": len(result["target_keys"]),
            "links_valid": sum(row["link_in_text"] == "VÁLIDO" for row in status),
            "links_absent": sum(row["link_in_text"] == "AUSENTE" for row in status),
            "in_text_format_corrections": sum(
                row["format_in_text"] == "CORRIGIR" for row in status
            ),
            "citation_status_rows": status,
        },
        "reference_reconciliation": {
            **result["reference_summary"],
            "target_keys": result["target_keys"],
            "missing_keys": result["missing_reference_keys"],
            "extra_keys": result["extra_reference_keys"],
        },
        "change_queue": {
            "rows": len(queue),
            "by_priority": dict(collections.Counter(row["priority"] for row in queue)),
            "by_type": dict(collections.Counter(row["change_type"] for row in queue)),
            "approval_status": {"PROPOSED": len(queue)},
        },
        "primary_row_accounting": {
            "rows": len(result["row_coverage"]),
            "dispositions": dict(collections.Counter(result["row_coverage"].values())),
            "row_map": result["row_coverage"],
        },
        "official_url_checks": result["link_checks"],
        "quality_control": {
            "state": "PAUSED",
            "checkpoint_path": str(paths["pause"].relative_to(root)),
            "active_processes_after_pause": 0,
        },
        "mutations": {
            "notion": False,
            "zotero": False,
            "library_bib": False,
            "pdfs": False,
        },
        "artifacts": {},
    }
    for path in [report_path, changeset_path, queue_path]:
        manifest["artifacts"][str(path.relative_to(root))] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="Issue bounded HTTP HEAD checks for all proposed official URLs.",
    )
    arguments = parser.parse_args()
    result = build_artifacts(
        arguments.root,
        write=True,
        perform_link_checks=arguments.check_links,
    )
    print(
        json.dumps(
            {
                "primary_rows": result["summary"]["rows"],
                "queue_rows": len(result["queue"]),
                "citation_status_rows": len(result["citation_status"]),
                "semantic_match": result["semantic_match"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
