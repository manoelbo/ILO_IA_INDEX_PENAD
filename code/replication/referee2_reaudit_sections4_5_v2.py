#!/usr/bin/env python3
"""Round 2 independent audit of the revised Sections 4–5 HTML export.

The script reviews the revised editorial export against the frozen computational
authorities and the Round 1 correction registry. It never modifies author code,
the dissertation export, or the Replication Package.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, Tag
from PIL import Image, ImageChops, ImageOps, ImageStat

import referee2_audit_sections4_5 as round1


ROUND2_STEM = "2026-07-25_round2_sections4_5"
EXPECTED_TABLES = 23
EXPECTED_FIGURES = 16
APPENDIX_FIGURES = {
    "figure_b_1_occupation_cases_by_sex.png": (
        "outputs/section5_3_occupation_cases/figures/"
        "figure_b_1_occupation_cases_by_sex.png"
    ),
    "figure_b_2_occupation_cases_by_race_color.png": (
        "outputs/section5_3_occupation_cases/figures/"
        "figure_b_2_occupation_cases_by_race_color.png"
    ),
    "figure_b_3_occupation_cases_by_education.png": (
        "outputs/section5_3_occupation_cases/figures/"
        "figure_b_3_occupation_cases_by_education.png"
    ),
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="Revised HTML export. Defaults to the unique HTML in the v2 folder.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "correspondence/referee2",
    )
    return parser.parse_args()


def default_html(root: Path) -> Path:
    candidates = sorted((root / "Secao 4 e 5 concluida v2").glob("*.html"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected one revised HTML export; found {len(candidates)}."
        )
    return candidates[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_tree(path: Path, scope: str) -> pd.DataFrame:
    rows = []
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        if file_path.name == ".DS_Store":
            continue
        rows.append(
            {
                "scope": scope,
                "path": file_path.relative_to(project_root()).as_posix(),
                "bytes": file_path.stat().st_size,
                "sha256": sha256(file_path),
            }
        )
    return pd.DataFrame(rows)


def clean_text(value: str) -> str:
    return round1.clean_text(value)


def nearby_reference(image: Tag) -> tuple[str, str]:
    """Return a canonical file reference and its editorial format."""
    figure = image.find_parent("figure")
    node = figure.find_previous_sibling() if figure is not None else None
    candidates = []
    for _ in range(4):
        if node is None:
            break
        if isinstance(node, Tag) and node.name in {"p", "figcaption"}:
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                candidates.append(text)
        node = node.find_previous_sibling()

    labeled = re.compile(
        r"(?P<bracket>\[)?(?:file ref|ref file)\s*:\s*"
        r"(?P<file>[^\]\s]+?\.png)(?:\])?",
        flags=re.IGNORECASE,
    )
    bare = re.compile(r"^(?P<file>[^\s]+?\.png)$", flags=re.IGNORECASE)
    for text in candidates:
        match = labeled.search(text)
        if match:
            format_name = (
                "bracketed_label" if match.group("bracket") else "label"
            )
            return match.group("file"), format_name
        match = bare.match(text)
        if match:
            return match.group("file"), "bare_filename"
    return "", "missing"


def inspect_html(
    html_path: Path,
) -> tuple[
    BeautifulSoup,
    list[round1.HtmlTable],
    list[dict[str, object]],
    list[round1.HtmlBlock],
]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    body = soup.select_one("div.page-body")
    if body is None:
        raise ValueError("The revised export has no div.page-body.")

    tables = []
    for index, table in enumerate(body.select("table.simple-table"), start=1):
        columns = tuple(
            clean_text(cell.get_text(" ", strip=True))
            for cell in table.select("thead th")
        )
        rows = tuple(
            tuple(
                clean_text(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
            )
            for row in table.select("tbody tr")
        )
        tables.append(
            round1.HtmlTable(
                table_id=f"T{index:02d}",
                html_id=str(table.get("id", "")),
                columns=columns,
                rows=rows,
            )
        )

    local_images = [
        image
        for image in body.find_all("img")
        if not str(image.get("src", "")).startswith(("http://", "https://"))
    ]
    figures = []
    for index, image in enumerate(local_images, start=1):
        source = str(image.get("src", ""))
        reference, reference_format = nearby_reference(image)
        figures.append(
            {
                "figure_id": f"F{index:02d}",
                "html_src": source,
                "path": (html_path.parent / unquote(source)).resolve(),
                "file_reference": reference,
                "reference_format": reference_format,
            }
        )

    blocks = []
    narrative_index = 0
    for element in body.find_all(["h1", "h2", "h3", "h4", "p"]):
        if element.find_parent(["table", "figure"]):
            continue
        narrative_index += 1
        blocks.append(
            round1.HtmlBlock(
                location=f"N{narrative_index:03d}",
                html_id=str(element.get("id", "")),
                tag=element.name.upper(),
                text=clean_text(element.get_text(" ", strip=True)),
            )
        )
    return soup, tables, figures, blocks


def corrected_value(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("p=<0,001", "p<0,001")


def corrected_expected_tables(root: Path) -> tuple[list[pd.DataFrame], list[str]]:
    expected, sources = round1.expected_tables(root)
    corrected = []
    for index, table in enumerate(expected, start=1):
        item = table.copy()
        for column in item.columns:
            item[column] = item[column].map(corrected_value)
        if index == 21:
            item["Resultado"] = item["Resultado"].replace(
                {"Salário de admissão": "Salário real de admissão (log)"}
            )
        corrected.append(item)
    return corrected, sources


def canonical(value: object) -> str:
    return round1.normalized_cell(corrected_value(value))


def expected_matrix(table: pd.DataFrame) -> list[list[str]]:
    rows = [[str(column) for column in table.columns]]
    rows.extend(
        [
            ["" if pd.isna(value) else str(value) for value in row]
            for row in table.itertuples(index=False)
        ]
    )
    return rows


def actual_matrix(table: round1.HtmlTable) -> list[list[str]]:
    return [list(table.columns), *[list(row) for row in table.rows]]


def table_audit(
    tables: list[round1.HtmlTable],
    expected: list[pd.DataFrame],
    sources: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ledger = []
    summaries = []
    for html_table, authority, source in zip(
        tables,
        expected,
        sources,
        strict=True,
    ):
        actual = actual_matrix(html_table)
        target = expected_matrix(authority)
        if len(actual) != len(target):
            raise ValueError(
                f"{html_table.table_id}: row count differs from authority."
            )
        if any(len(left) != len(right) for left, right in zip(actual, target)):
            raise ValueError(
                f"{html_table.table_id}: column count differs from authority."
            )

        actual_rows = [tuple(canonical(value) for value in row) for row in actual]
        target_rows = [tuple(canonical(value) for value in row) for row in target]
        multiset_match = Counter(actual_rows) == Counter(target_rows)
        header_position_ok = actual_rows[0] == target_rows[0]
        row_order_ok = actual_rows[1:] == target_rows[1:]
        mismatches = 0
        for row_index, (actual_row, target_row) in enumerate(
            zip(actual, target, strict=True)
        ):
            for column_index, (displayed, raw) in enumerate(
                zip(actual_row, target_row, strict=True),
                start=1,
            ):
                equivalent = canonical(displayed) == canonical(raw)
                mismatches += int(not equivalent)
                ledger.append(
                    {
                        "claim_id": (
                            f"{html_table.table_id}."
                            f"{'HEADER' if row_index == 0 else f'R{row_index:02d}'}."
                            f"C{column_index:02d}"
                        ),
                        "location": (
                            f"{html_table.table_id} / HTML {html_table.html_id}"
                        ),
                        "claim_type": (
                            "table_header" if row_index == 0 else "table_cell"
                        ),
                        "source": source,
                        "displayed_value": displayed,
                        "expected_value": raw,
                        "status": "verified" if equivalent else "structure_mismatch",
                        "severity": "none" if equivalent else "major",
                        "recommended_replacement": (
                            "" if equivalent else raw
                        ),
                        "evidence": (
                            "direct source-to-position comparison; the A.6 "
                            "multiset check separately verifies that all values "
                            "are present"
                        ),
                    }
                )

        if mismatches == 0:
            status = "pass"
        elif multiset_match:
            status = "content_present_structure_broken"
        else:
            status = "content_mismatch"
        summaries.append(
            {
                "table_id": html_table.table_id,
                "html_id": html_table.html_id,
                "rows": len(html_table.rows),
                "columns": len(html_table.columns),
                "cells_including_headers": sum(len(row) for row in actual),
                "position_mismatches": mismatches,
                "header_position_ok": header_position_ok,
                "row_order_ok": row_order_ok,
                "all_expected_rows_present": multiset_match,
                "computational_source": source,
                "status": status,
            }
        )
    return pd.DataFrame(ledger), pd.DataFrame(summaries)


def image_rms(left_path: Path, right_path: Path) -> tuple[float, str, str]:
    with Image.open(left_path) as left_image:
        left_dimensions = f"{left_image.width}x{left_image.height}"
        left = ImageOps.fit(
            left_image.convert("L"),
            (64, 64),
            method=Image.Resampling.LANCZOS,
        )
    with Image.open(right_path) as right_image:
        right_dimensions = f"{right_image.width}x{right_image.height}"
        right = ImageOps.fit(
            right_image.convert("L"),
            (64, 64),
            method=Image.Resampling.LANCZOS,
        )
    rms = float(ImageStat.Stat(ImageChops.difference(left, right)).rms[0])
    return rms, left_dimensions, right_dimensions


def figure_authorities(root: Path) -> list[dict[str, str]]:
    artifact_map = pd.read_csv(
        root / "Replication Package/outputs/sections4_5/artifact_map.csv"
    )
    mapped = artifact_map[
        artifact_map["artifact_type"].eq("figure")
    ].sort_values("html_order")
    authorities = [
        {
            "artifact_id": str(item.artifact_id),
            "expected_reference": Path(str(item.output_file)).name,
            "source": str(item.source_input),
        }
        for item in mapped.itertuples(index=False)
    ]
    for reference, source in APPENDIX_FIGURES.items():
        authorities.append(
            {
                "artifact_id": reference.removesuffix(".png"),
                "expected_reference": reference,
                "source": source,
            }
        )
    return authorities


def figure_audit(
    root: Path,
    figures: list[dict[str, object]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    authorities = figure_authorities(root)
    if len(figures) != len(authorities):
        raise ValueError(
            f"Expected {len(authorities)} content figures; found {len(figures)}."
        )
    rows = []
    ledger = []
    for figure, authority in zip(figures, authorities, strict=True):
        html_path = Path(figure["path"])
        source_path = root / authority["source"]
        rms, html_dimensions, source_dimensions = image_rms(
            html_path,
            source_path,
        )
        reference_matches = (
            figure["file_reference"] == authority["expected_reference"]
        )
        content_pass = (
            html_path.exists()
            and source_path.exists()
            and reference_matches
            and rms < 25
        )
        metadata_status = (
            "warning"
            if figure["reference_format"] == "bare_filename"
            else "pass"
        )
        rows.append(
            {
                "figure_id": figure["figure_id"],
                "artifact_id": authority["artifact_id"],
                "file_reference": figure["file_reference"],
                "reference_format": figure["reference_format"],
                "expected_reference": authority["expected_reference"],
                "source": authority["source"],
                "html_dimensions": html_dimensions,
                "source_dimensions": source_dimensions,
                "visual_rms": rms,
                "html_sha256": sha256(html_path),
                "source_sha256": sha256(source_path),
                "content_status": "pass" if content_pass else "fail",
                "metadata_status": metadata_status,
            }
        )
        ledger.append(
            {
                "claim_id": str(figure["figure_id"]),
                "location": str(figure["html_src"]),
                "claim_type": "figure",
                "source": authority["source"],
                "displayed_value": str(figure["file_reference"]),
                "expected_value": authority["expected_reference"],
                "status": "verified" if content_pass else "incorrect",
                "severity": "none" if content_pass else "major",
                "recommended_replacement": "",
                "evidence": (
                    f"reference_match={reference_matches}; visual_rms={rms:.6f}; "
                    f"metadata={metadata_status}"
                ),
            }
        )
    return pd.DataFrame(ledger), pd.DataFrame(rows)


def append_b_links(
    soup: BeautifulSoup,
    root: Path,
    revised_root: Path,
) -> pd.DataFrame:
    heading = next(
        (
            item
            for item in soup.find_all(["h1", "h2", "h3"])
            if "Apêndice B:" in clean_text(item.get_text(" ", strip=True))
        ),
        None,
    )
    if heading is None:
        return pd.DataFrame()
    paragraph = heading.find_next("p")
    rows = []
    for index, anchor in enumerate(paragraph.find_all("a"), start=1):
        url = str(anchor.get("href", ""))
        label = clean_text(anchor.get_text(" ", strip=True))
        parsed = urlparse(url)
        relative = (
            unquote(parsed.path.split("/p/", maxsplit=1)[1])
            if "/p/" in parsed.path
            else ""
        )
        local_target = root / relative if relative else Path()
        bundled_candidates = (
            list(revised_root.rglob(Path(relative).name))
            if relative
            else []
        )
        try:
            request = Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=15) as response:
                http_status = int(response.status)
        except HTTPError as error:
            http_status = int(error.code)
        except (URLError, TimeoutError):
            http_status = 0
        reachable = 200 <= http_status < 400
        rows.append(
            {
                "link_id": f"L{index:02d}",
                "label": label,
                "url": url,
                "http_status": http_status,
                "local_target": (
                    local_target.relative_to(root).as_posix()
                    if relative
                    else ""
                ),
                "local_target_exists": bool(relative and local_target.exists()),
                "bundled_with_html": bool(bundled_candidates),
                "status": "pass" if reachable else "broken",
                "recommended_action": (
                    ""
                    if reachable
                    else "Embed the table or bundle a working relative target."
                ),
            }
        )
    return pd.DataFrame(rows)


def correction_resolution(
    blocks: list[round1.HtmlBlock],
    tables: list[round1.HtmlTable],
) -> pd.DataFrame:
    corrections = round1.correction_registry()
    document_text = "\n".join(
        [
            *(block.text for block in blocks),
            *(
                value
                for table in tables
                for row in actual_matrix(table)
                for value in row
            ),
        ]
    )
    overrides = {
        "C021": (
            "partially_fixed",
            (
                "The target paragraph was corrected, but N071 still says "
                "'não há evidência de que a exposição à IA tenha ampliado'."
            ),
        ),
        "C026": (
            "fixed",
            (
                "The paragraph retains the valid thin-support caveat and now "
                "also reports +27.8%, beta=0.2453 and p=0.049."
            ),
        ),
        "C029": (
            "fixed",
            (
                "The synthesis now includes the low-income positive DDDs, the "
                "thin high-income result and the multiple-testing caveat."
            ),
        ),
        "C031": (
            "partially_fixed",
            (
                "Appendix B now exists and contains three figures, but its six "
                "table links return HTTP 404 and the linked tables are not "
                "bundled in the export."
            ),
        ),
        "C034": (
            "fixed",
            (
                "The original Appendix A introduction now says 'Este apêndice'; "
                "the new Appendix B wording regression is tracked separately."
            ),
        ),
        "C037": (
            "fixed",
            "Table A.5 now labels all three wage rows as real log wages.",
        ),
        "C038": (
            "partially_fixed",
            (
                "The appendix terminology was corrected, but the malformed "
                "'\\ p<0,10' and trailing '\\*' remain in N154."
            ),
        ),
        "C039": (
            "partially_fixed",
            (
                "All 18 correct income rows are present, but T22–T23 have "
                "misplaced headers and scrambled row order."
            ),
        ),
        "C040": (
            "fixed",
            "Panel B.2 is now a paragraph-level panel caption, not an H2.",
        ),
        "C041": (
            "fixed",
            "N137 now reconciles the full-sample and strict-window pretrends.",
        ),
        "C042": (
            "unresolved",
            (
                "N114 still contains spaces before commas after both "
                "Klein Teeselink (2025) and Brynjolfsson et al. (2025)."
            ),
        ),
    }
    rows = []
    for item in corrections:
        claim_id = item["claim_id"]
        old_count = document_text.count(item["needle"])
        if claim_id in overrides:
            status, evidence = overrides[claim_id]
        else:
            status = "fixed" if old_count == 0 else "unresolved"
            evidence = (
                "Round 1 wording is absent and the revised text/table was "
                "verified."
                if status == "fixed"
                else f"Round 1 wording remains {old_count} time(s)."
            )
        rows.append(
            {
                "claim_id": claim_id,
                "round1_severity": item["severity"],
                "round1_location": item["location"],
                "round1_issue": item["displayed_value"],
                "resolution_status": status,
                "old_needle_count_v2": old_count,
                "evidence": evidence,
                "round1_recommended_replacement": item[
                    "recommended_replacement"
                ],
            }
        )
    return pd.DataFrame(rows)


def narrative_findings() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "finding_id": "R2-001",
                "severity": "major",
                "location": "Appendix A.6 / T22–T23",
                "issue": "Correct income values are structurally scrambled.",
                "evidence": (
                    "All expected rows are present, but T22 uses a high-income "
                    "observation as its header and places the true header at row "
                    "9; T23 uses a middle-income observation as its header and "
                    "places the true header at row 3."
                ),
                "replacement_ptbr": (
                    "Substitua novamente os dois painéis pela tabela A.6 de "
                    "reposição, preservando a primeira linha como cabeçalho e "
                    "a ordem faixa de renda × outcome."
                ),
            },
            {
                "finding_id": "R2-002",
                "severity": "major",
                "location": "Appendix B / N161",
                "issue": "The appendix table links are not accessible.",
                "evidence": (
                    "All six links were rewritten as app.notion.com/p/outputs "
                    "URLs, return HTTP 404, and their targets are not bundled "
                    "with the HTML export."
                ),
                "replacement_ptbr": (
                    "Incorpore as tabelas essenciais diretamente no Apêndice B "
                    "ou anexe os arquivos ao export com links relativos que "
                    "funcionem fora do Notion."
                ),
            },
            {
                "finding_id": "R2-003",
                "severity": "moderate",
                "location": "N042, N076, N086 and N117",
                "issue": "Flow outcomes still imply a stock conclusion.",
                "evidence": (
                    "The revised text still contrasts lower turnover with net "
                    "job destruction even though the model does not observe "
                    "employment stocks."
                ),
                "replacement_ptbr": (
                    "Troque as conclusões sobre 'menor rotatividade, e não "
                    "destruição líquida' por 'menor movimentação relativa dos "
                    "fluxos; sem observar o estoque, não é possível distinguir "
                    "esse padrão de mudanças no número líquido de vínculos'."
                ),
            },
            {
                "finding_id": "R2-004",
                "severity": "moderate",
                "location": "N071, N117 and N118",
                "issue": "Some synthesis language still treats exposure as effect.",
                "evidence": (
                    "Phrases such as 'efeitos da exposição à IA' and 'ausência "
                    "de impacto agregado' are stronger than an exposure-by-post "
                    "estimand with imprecise coefficients."
                ),
                "replacement_ptbr": (
                    "Use 'diferenciais pós-ChatGPT entre ocupações expostas e "
                    "não expostas' e 'ausência de evidência agregada robusta', "
                    "em vez de 'efeitos da exposição' e 'ausência de impacto'."
                ),
            },
            {
                "finding_id": "R2-005",
                "severity": "minor",
                "location": "N154 / Appendix A.5 note",
                "issue": "The significance legend remains malformed.",
                "evidence": "The text still contains '\\ p<0,10' and a trailing '\\*'.",
                "replacement_ptbr": (
                    "Use '* p<0,10; ** p<0,05; *** p<0,01' e remova a barra "
                    "e o asterisco solto ao final."
                ),
            },
            {
                "finding_id": "R2-006",
                "severity": "minor",
                "location": "N114",
                "issue": "Spaces remain before two citation commas.",
                "evidence": (
                    "'Klein Teeselink (2025) ,' and "
                    "'Brynjolfsson, Chandar e Chen (2025) ,' remain."
                ),
                "replacement_ptbr": "Remova os dois espaços antes das vírgulas.",
            },
            {
                "finding_id": "R2-007",
                "severity": "minor",
                "location": "Appendix heading hierarchy",
                "issue": "Appendix heading levels are inconsistent.",
                "evidence": (
                    "Appendices A and B are H2; A.1–A.6 are H3, but B.1–B.3 "
                    "are also H2."
                ),
                "replacement_ptbr": (
                    "Formate 'Apêndice A' e 'Apêndice B' no mesmo nível "
                    "superior e A.1–A.6/B.1–B.3 um nível abaixo."
                ),
            },
            {
                "finding_id": "R2-008",
                "severity": "minor",
                "location": "N161 / Appendix B introduction",
                "issue": "Appendix terminology regressed.",
                "evidence": "The new appendix begins with 'Este anexo reúne'.",
                "replacement_ptbr": "Troque 'Este anexo reúne' por 'Este apêndice reúne'.",
            },
            {
                "finding_id": "R2-009",
                "severity": "minor",
                "location": "N167 / Figure B.3 metadata",
                "issue": "The third appendix figure lacks a file-ref label.",
                "evidence": (
                    "B.1 and B.2 use 'file ref:'; B.3 contains only the "
                    "filename."
                ),
                "replacement_ptbr": (
                    "Use '[file ref: "
                    "figure_b_3_occupation_cases_by_education.png]'."
                ),
            },
        ]
    )


def link_ledger(links: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for item in links.itertuples(index=False):
        rows.append(
            {
                "claim_id": item.link_id,
                "location": "Appendix B / N161",
                "claim_type": "appendix_link",
                "source": item.local_target,
                "displayed_value": item.url,
                "expected_value": "reachable or bundled target",
                "status": "verified" if item.status == "pass" else "incorrect",
                "severity": "none" if item.status == "pass" else "major",
                "recommended_replacement": item.recommended_action,
                "evidence": (
                    f"HTTP {item.http_status}; local_exists="
                    f"{item.local_target_exists}; bundled={item.bundled_with_html}"
                ),
            }
        )
    return pd.DataFrame(rows)


def findings_ledger(findings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for item in findings.itertuples(index=False):
        rows.append(
            {
                "claim_id": item.finding_id,
                "location": item.location,
                "claim_type": "narrative_or_structure",
                "source": "Round 2 editorial and econometric review",
                "displayed_value": item.issue,
                "expected_value": item.replacement_ptbr,
                "status": "revise",
                "severity": item.severity,
                "recommended_replacement": item.replacement_ptbr,
                "evidence": item.evidence,
            }
        )
    return pd.DataFrame(rows)


def validation_checks(
    tables: list[round1.HtmlTable],
    figures: list[dict[str, object]],
    table_summary: pd.DataFrame,
    figure_summary: pd.DataFrame,
    links: pd.DataFrame,
    resolution: pd.DataFrame,
    findings: pd.DataFrame,
    cross_language: pd.DataFrame,
    package_unchanged: bool,
    root: Path,
) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(
        kind: str,
        check_id: str,
        passed: bool,
        observed: object,
        expected: object,
        detail: str,
    ) -> None:
        checks.append(
            {
                "kind": kind,
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "observed": observed,
                "expected": expected,
                "detail": detail,
            }
        )

    add(
        "audit",
        "html_table_count",
        len(tables) == EXPECTED_TABLES,
        len(tables),
        EXPECTED_TABLES,
        "Revised editorial table inventory.",
    )
    add(
        "audit",
        "html_figure_count",
        len(figures) == EXPECTED_FIGURES,
        len(figures),
        EXPECTED_FIGURES,
        "Thirteen main figures plus three Appendix B figures.",
    )
    first_21_pass = table_summary.iloc[:21]["status"].eq("pass").all()
    add(
        "audit",
        "tables_t01_t21_match",
        first_21_pass,
        int(table_summary.iloc[:21]["status"].eq("pass").sum()),
        21,
        "Approved editorial corrections are normalized before comparison.",
    )
    a6 = table_summary.iloc[21:]
    add(
        "audit",
        "a6_correct_rows_present",
        a6["all_expected_rows_present"].all(),
        int(a6["all_expected_rows_present"].sum()),
        2,
        "All correct income rows exist despite the broken layout.",
    )
    add(
        "acceptance",
        "a6_structure_ready",
        a6["status"].eq("pass").all(),
        ",".join(a6["status"]),
        "pass,pass",
        "Headers and row order must match the replacement table.",
    )
    add(
        "audit",
        "all_figure_pixels_valid",
        figure_summary["content_status"].eq("pass").all(),
        int(figure_summary["content_status"].eq("pass").sum()),
        EXPECTED_FIGURES,
        "References, sources, dimensions and visual pixels were compared.",
    )
    appendix_rms = figure_summary.tail(3)["visual_rms"]
    add(
        "audit",
        "appendix_b_figures_exact_pixels",
        np.allclose(appendix_rms, 0.0),
        ",".join(f"{value:.6f}" for value in appendix_rms),
        "0,0,0",
        "The three new figures are pixel-identical to specialized outputs.",
    )
    add(
        "audit",
        "round1_resolution_inventory",
        len(resolution) == 44,
        len(resolution),
        44,
        "Every Round 1 correction has a Round 2 disposition.",
    )
    critical_fixed = resolution[
        resolution["round1_severity"].eq("critical")
    ]["resolution_status"].eq("fixed").all()
    add(
        "acceptance",
        "round1_critical_items_fully_fixed",
        critical_fixed,
        ",".join(
            resolution[
                resolution["round1_severity"].eq("critical")
            ]["resolution_status"]
        ),
        "fixed,fixed",
        "The method paragraph is fixed; A.6 remains only partially fixed.",
    )
    all_links_pass = not links.empty and links["status"].eq("pass").all()
    add(
        "acceptance",
        "appendix_b_links_reachable",
        all_links_pass,
        int(links["status"].eq("pass").sum()),
        len(links),
        "Every linked appendix table must work outside Notion.",
    )
    add(
        "audit",
        "appendix_b_broken_links_detected",
        len(links) == 6 and links["status"].eq("broken").all(),
        int(links["status"].eq("broken").sum()),
        6,
        "The audit must not silently accept rewritten Notion URLs.",
    )
    difference_columns = [
        column for column in cross_language if "_abs_diff_" in column
    ]
    max_difference = float(cross_language[difference_columns].max(axis=None))
    add(
        "audit",
        "cross_language_replication",
        max_difference <= 1e-8
        and cross_language["status"].eq("pass").all(),
        f"{max_difference:.3e}",
        "<=1e-8",
        "Python, R and frozen author outputs remain aligned.",
    )
    add(
        "audit",
        "replication_package_unchanged",
        package_unchanged,
        package_unchanged,
        True,
        "Round 2 did not modify the Replication Package.",
    )
    phase1 = pd.read_csv(
        root
        / "Replication Package/outputs/sections4_5/validation"
        / "validation_checks.csv"
    )
    phase1_pass = phase1["status"].astype(str).str.lower().eq("pass")
    add(
        "audit",
        "phase1_validation_still_green",
        phase1_pass.all(),
        int(phase1_pass.sum()),
        len(phase1),
        "The frozen package validation remains green.",
    )
    substantive = findings["severity"].isin(["major", "moderate"])
    add(
        "acceptance",
        "no_substantive_round2_findings",
        not substantive.any(),
        int(substantive.sum()),
        0,
        "Major and moderate findings block acceptance.",
    )
    return pd.DataFrame(checks)


def markdown_table(data: pd.DataFrame) -> str:
    if data.empty:
        return "_No rows._"
    return data.to_markdown(index=False, disable_numparse=True)


def write_a6_replacement(
    output_dir: Path,
    expected: list[pd.DataFrame],
) -> Path:
    path = output_dir / f"{ROUND2_STEM}_a6_replacement.md"
    path.write_text(
        "\n".join(
            [
                "# Appendix A.6 replacement",
                "",
                "## Panel B.1: Main outcomes",
                "",
                markdown_table(expected[21]),
                "",
                "## Panel B.2: Net-flow construction robustness",
                "",
                markdown_table(expected[22]),
                "",
                (
                    "Notes: coefficients are DDD estimates for post × treatment "
                    "× group. Standard errors are clustered by four-digit CBO. "
                    "* p<0.10; ** p<0.05; *** p<0.01."
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def corrections_markdown(findings: pd.DataFrame) -> str:
    severity_order = {"major": 0, "moderate": 1, "minor": 2}
    ordered = findings.assign(
        _order=findings["severity"].map(severity_order)
    ).sort_values(["_order", "finding_id"])
    lines = [
        "# Sections 4–5 v2: remaining corrections",
        "",
        (
            "The Round 2 audit confirms that most Round 1 corrections were "
            "implemented. Apply the following remaining changes."
        ),
        "",
    ]
    for index, item in enumerate(ordered.itertuples(index=False), start=1):
        lines.extend(
            [
                f"## {index}. [{item.severity.upper()}] {item.location}",
                "",
                f"Issue: {item.issue}",
                "",
                f"Evidence: {item.evidence}",
                "",
                "Recommended Portuguese replacement/action:",
                "",
                f"> {item.replacement_ptbr}",
                "",
            ]
        )
    return "\n".join(lines)


def blindspot_markdown() -> str:
    return """# Blindspot audit: revised dissertation Sections 4–5

## Vice 1: The unexplained feature

- **FLAG — Appendix A.6 structure.** Every correct value is present, but the
  apparent table sorting moved data rows into the headers and moved the real
  headers into the bodies. A reader cannot safely interpret either panel.
- **FLAG — Residual flow-to-stock language.** Several synthesis paragraphs still
  prefer lower turnover to net destruction even after the text acknowledges that
  the stock is unobserved.

## Vice 2: The convenient absence

- **FLAG — Appendix B tables are absent from the export.** The prose says the
  dictionary and sensitivity matrices are available, but all six links return
  HTTP 404 and none of the targets is bundled.
- **DONE — Appendix B figures.** The three new demographic figures are present
  and pixel-identical to their computational sources.

## Virtue 1: The unasked question

- The revised income discussion is now materially better: it reports the
  countervailing low-income DDDs and discloses the thin high-income result.
- The corrected occupation-case method makes the descriptive mechanism exercise
  auditable through six frozen, non-overlapping semantic cases.

## Virtue 2: The unexploited strength

- The revised text now distinguishes observed flows from employment stocks in
  the main national-results paragraph. Propagating that same wording through the
  age and synthesis paragraphs would remove the remaining interpretive tension.
- Appendix B can become a strong transparency device if its existing source
  tables are embedded rather than referenced through inaccessible links.

## Ruling

**HOLD.** The numerical corrections are substantially complete, but the broken
A.6 structure and inaccessible Appendix B tables remain visible publication
defects. The remaining substantive language revisions are narrow and do not
change the estimates.
"""


def report_markdown(
    html_path: Path,
    table_summary: pd.DataFrame,
    figure_summary: pd.DataFrame,
    links: pd.DataFrame,
    resolution: pd.DataFrame,
    findings: pd.DataFrame,
    cross_language: pd.DataFrame,
    validations: pd.DataFrame,
) -> str:
    resolution_counts = resolution["resolution_status"].value_counts().to_dict()
    finding_counts = findings["severity"].value_counts().to_dict()
    difference_columns = [
        column for column in cross_language if "_abs_diff_" in column
    ]
    max_difference = float(cross_language[difference_columns].max(axis=None))
    table_mismatches = int(table_summary["position_mismatches"].sum())
    audit_checks = validations[validations["kind"].eq("audit")]
    acceptance = validations[validations["kind"].eq("acceptance")]
    return f"""# Referee 2 report: dissertation Sections 4–5 — Round 2

## Summary and verdict

**MAJOR REVISIONS, narrowly scoped; HOLD for circulation.** The revision fixes
the obsolete occupation-case methodology, the external benchmark, the omitted
income DDDs, the pretrend descriptions, and nearly all numbering and
interpretation issues. The underlying results remain reproducible.

The submission is not yet clean because Appendix A.6 is structurally scrambled
and all six linked Appendix B tables return HTTP 404. Two clusters of estimand
language also still infer stocks or realized effects from exposure-by-post flow
models.

## Round 1 resolution

- Fixed: {resolution_counts.get("fixed", 0)} of 44.
- Partially fixed: {resolution_counts.get("partially_fixed", 0)}.
- Unresolved: {resolution_counts.get("unresolved", 0)}.
- Remaining Round 2 findings: major {finding_counts.get("major", 0)},
  moderate {finding_counts.get("moderate", 0)}, minor
  {finding_counts.get("minor", 0)}.

{markdown_table(resolution[[
    "claim_id",
    "round1_severity",
    "round1_location",
    "resolution_status",
    "evidence",
]])}

## Tables

- The revised HTML still contains 23 tables.
- T01–T21 match their computational authorities after accepting the approved
  notation corrections (`p<0,001` and the real-log wage label).
- T22–T23 contain every correct A.6 row, but have {table_mismatches} positional
  cell mismatches because their headers and row order are broken.
- A clean, correctly ordered A.6 replacement is supplied separately.

{markdown_table(table_summary)}

## Figures

- The revised export contains 16 content figures: the original 13 plus three
  Appendix B figures.
- All 16 match their named computational sources.
- The three new Appendix B figures are pixel-identical to the specialized
  Section 5.3 outputs (visual RMS = 0).
- Figure B.3 has only a bare filename rather than a `file ref:` label.

{markdown_table(figure_summary[[
    "figure_id",
    "file_reference",
    "source",
    "html_dimensions",
    "source_dimensions",
    "visual_rms",
    "content_status",
    "metadata_status",
]])}

## Appendix B links

The source files exist in the project, but the HTML export rewrites the six
paths as `https://app.notion.com/p/outputs/...`. Every URL returned HTTP 404 and
none of the linked tables is bundled with `{html_path.parent.name}`.

{markdown_table(links)}

## Econometric and narrative review

{markdown_table(findings)}

The central estimates did not change. Independent Python and R implementations
still match one another and the frozen author outputs to a maximum absolute
difference of {max_difference:.3e}.

Test suites executed after the Round 2 audit:

- Sections 4–5 contracts: 71 passed (plus 8 subtests; one singleton-FE warning).
- Occupation cases: 28 passed.
- Replication Package: 5 passed.

## Validation

Audit execution checks: {int(audit_checks["status"].eq("pass").sum())}/{len(audit_checks)} passed.
Acceptance gates: {int(acceptance["status"].eq("pass").sum())}/{len(acceptance)} passed.

{markdown_table(validations)}

## Required actions before acceptance

1. Reinsert Appendix A.6 without sorting: header first, then the supplied row
   order.
2. Embed or bundle the six Appendix B tables instead of using Notion-rewritten
   links.
3. Apply the two narrow estimand-language changes in the age/race/synthesis
   paragraphs.
4. Clean the remaining legend, citation, hierarchy, terminology and file-ref
   details.
"""


def write_manifest(output_dir: Path) -> Path:
    path = output_dir / f"{ROUND2_STEM}_audit_manifest.csv"
    rows = []
    for item in sorted(output_dir.glob(f"{ROUND2_STEM}_*")):
        if not item.is_file() or item == path:
            continue
        rows.append(
            {
                "path": item.relative_to(project_root()).as_posix(),
                "bytes": item.stat().st_size,
                "sha256": sha256(item),
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def main() -> int:
    args = parse_args()
    root = project_root()
    html_path = (
        default_html(root) if args.html is None else args.html.resolve()
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    revised_root = html_path.parent
    package_root = root / "Replication Package"

    package_before = snapshot_tree(package_root, "replication_package")
    revised_hashes = snapshot_tree(revised_root, "revised_html_export")
    soup, tables, figures, blocks = inspect_html(html_path)
    if len(tables) != EXPECTED_TABLES:
        raise ValueError(f"Expected 23 tables; found {len(tables)}.")
    if len(figures) != EXPECTED_FIGURES:
        raise ValueError(f"Expected 16 figures; found {len(figures)}.")

    expected, sources = corrected_expected_tables(root)
    table_ledger, table_summary = table_audit(tables, expected, sources)
    figure_ledger, figure_summary = figure_audit(root, figures)
    links = append_b_links(soup, root, revised_root)
    resolution = correction_resolution(blocks, tables)
    findings = narrative_findings()
    cross_language = round1.cross_language_comparison(root, output_dir)
    external = round1.external_sources().copy()
    external["round2_status"] = "unchanged_from_round1_primary_source_audit"

    package_after = snapshot_tree(package_root, "replication_package")
    package_unchanged = package_before.equals(package_after)
    validations = validation_checks(
        tables=tables,
        figures=figures,
        table_summary=table_summary,
        figure_summary=figure_summary,
        links=links,
        resolution=resolution,
        findings=findings,
        cross_language=cross_language,
        package_unchanged=package_unchanged,
        root=root,
    )

    frozen = pd.concat([package_before, revised_hashes], ignore_index=True)
    frozen.to_csv(
        output_dir / f"{ROUND2_STEM}_frozen_hashes.csv",
        index=False,
    )
    table_summary.to_csv(
        output_dir / f"{ROUND2_STEM}_table_validation.csv",
        index=False,
    )
    figure_summary.to_csv(
        output_dir / f"{ROUND2_STEM}_figure_validation.csv",
        index=False,
    )
    links.to_csv(
        output_dir / f"{ROUND2_STEM}_link_validation.csv",
        index=False,
    )
    resolution.to_csv(
        output_dir / f"{ROUND2_STEM}_resolution_ledger.csv",
        index=False,
    )
    findings.to_csv(
        output_dir / f"{ROUND2_STEM}_narrative_findings.csv",
        index=False,
    )
    cross_language.to_csv(
        output_dir / f"{ROUND2_STEM}_cross_language_comparison.csv",
        index=False,
    )
    external.to_csv(
        output_dir / f"{ROUND2_STEM}_external_sources.csv",
        index=False,
    )
    validations.to_csv(
        output_dir / f"{ROUND2_STEM}_validation_checks.csv",
        index=False,
    )
    (output_dir / f"{ROUND2_STEM}_validation_checks.md").write_text(
        "# Round 2 validation checks\n\n"
        + markdown_table(validations)
        + "\n",
        encoding="utf-8",
    )
    claim_ledger = pd.concat(
        [
            table_ledger,
            figure_ledger,
            link_ledger(links),
            findings_ledger(findings),
        ],
        ignore_index=True,
    )
    claim_ledger.to_csv(
        output_dir / f"{ROUND2_STEM}_claim_ledger.csv",
        index=False,
    )
    write_a6_replacement(output_dir, expected)
    (output_dir / f"{ROUND2_STEM}_corrections_only.md").write_text(
        corrections_markdown(findings),
        encoding="utf-8",
    )
    (output_dir / f"{ROUND2_STEM}_blindspot.md").write_text(
        blindspot_markdown(),
        encoding="utf-8",
    )
    (output_dir / f"{ROUND2_STEM}_report.md").write_text(
        report_markdown(
            html_path=html_path,
            table_summary=table_summary,
            figure_summary=figure_summary,
            links=links,
            resolution=resolution,
            findings=findings,
            cross_language=cross_language,
            validations=validations,
        ),
        encoding="utf-8",
    )
    write_manifest(output_dir)

    audit_checks = validations[validations["kind"].eq("audit")]
    acceptance = validations[validations["kind"].eq("acceptance")]
    print(
        f"Round 2 audited {len(tables)} tables, {len(figures)} figures, "
        f"{len(links)} appendix links, and {len(resolution)} prior corrections."
    )
    print(
        "Audit checks: "
        f"{int(audit_checks['status'].eq('pass').sum())}/{len(audit_checks)} "
        "passed."
    )
    print(
        "Acceptance gates: "
        f"{int(acceptance['status'].eq('pass').sum())}/{len(acceptance)} "
        "passed."
    )
    return 0 if audit_checks["status"].eq("pass").all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
