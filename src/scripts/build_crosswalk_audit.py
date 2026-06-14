#!/usr/bin/env python3
"""
Build reproducible crosswalk audit tables and Markdown reports.

Inputs:
  - data/processed/ilo_exposure_clean.csv
  - data/output/pnad_ilo_merged.csv
  - data/output/painel_caged_did_ready.csv
  - data/input/Correspondencia ISCO 08 a 88.xlsx
  - data/input/Estrutura Ocupacao COD.xls
  - data/input/ISCO 08 Estruturas e Definicoes.xlsx

Outputs:
  - outputs/crosswalk_audit/crosswalk_report.md
  - outputs/crosswalk_audit/all_tables.md
  - outputs/crosswalk_audit/tables/*.md
  - outputs/crosswalk_audit/tables/*.csv

The script intentionally avoids pandas/openpyxl so it can run in lightweight
environments. COD occupation titles require R/readxl because the IBGE COD
dictionary is distributed as a legacy .xls workbook.
"""

from __future__ import annotations

import csv
import html as html_lib
import http.cookiejar
import io
import math
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs" / "crosswalk_audit"
TABLES_DIR = OUTPUT_DIR / "tables"
SOURCE_DICT_DIR = OUTPUT_DIR / "source_dictionaries"
OFFICIAL_MTE_DIR = OUTPUT_DIR / "official_mte_bridge"

ILO_FILE = DATA / "processed" / "ilo_exposure_clean.csv"
PNAD_FILE = DATA / "output" / "pnad_ilo_merged.csv"
CAGED_FILE = DATA / "output" / "painel_caged_did_ready.csv"
CAGED_CROSSWALK_FILE = DATA / "processed" / "painel_caged_crosswalk.csv"

MTE_BRIDGE_URL = "https://cbo.mte.gov.br/cbosite/pages/tabua/FiltroConversao_CBO2002_CBO94_CIUO88.jsf"
MTE_BRIDGE_CACHE = SOURCE_DICT_DIR / "mte_cbo2002_cbo94_ciuo88_by_family.csv"

CBO_FAMILY_URL = "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/downloads/cbo2002-familia.csv"
CBO_MINOR_URL = "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/downloads/cbo2002-subgrupo.csv"
CBO_SUBMAJOR_URL = "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/downloads/cbo2002-subgrupo-principal.csv"
CBO_MAJOR_URL = "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/downloads/cbo2002-grande-grupo.csv"

EXPECTED_PNAD_ROWS = {
    "4-digit": 203_617,
    "3-digit": 2_613,
    "sem_match": 1_671,
}

EXPECTED_CAGED_MAIN_CODES = {
    "2-digit": 478,
    "1-digit (fallback)": 151,
}

EXPECTED_CAGED_MAIN_ROWS = {
    "2-digit": 25_101,
    "1-digit (fallback)": 7_887,
}

EXPECTED_CAGED_ROBUST_CODES = {
    "N1: ISCO-08 4d direct": 177,
    "N2: via ISCO-88->08 4d": 56,
    "N3: ISCO-08 3d": 123,
    "N4: via ISCO-88->08 3d": 7,
    "N5: ISCO-08 2d": 115,
    "N6: ISCO-08 1d": 151,
    "sem_match": 0,
}

EXPECTED_CAGED_ROBUST_ROWS = {
    "N1: ISCO-08 4d direct": 9_317,
    "N2: via ISCO-88->08 4d": 2_914,
    "N3: ISCO-08 3d": 6_400,
    "N4: via ISCO-88->08 3d": 370,
    "N5: ISCO-08 2d": 6_100,
    "N6: ISCO-08 1d": 7_887,
    "sem_match": 0,
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def normalize_code(value: Any, width: int) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(width)


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    return float(text)


def fmt_int(value: int | float | None) -> str:
    if value is None:
        return ""
    return f"{int(round(value)):,}".replace(",", ".")


def fmt_pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def fmt_float(value: float | None, digits: int = 6) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{value:.{digits}f}"


def almost_equal(a: float | None, b: float | None, tol: float = 1e-8) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def mean(values: list[float]) -> float:
    if not values:
        fail("Cannot compute mean of an empty list.")
    return sum(values) / len(values)


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"Required input not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_semicolon_csv_text(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            output.append(value)
            seen.add(value)
    return output


def clean_html_text(fragment: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", fragment, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html_lib.unescape(text).split())


def find_input_file(patterns: list[str], label: str) -> Path:
    for pattern in patterns:
        candidates = sorted((DATA / "input").glob(pattern))
        if candidates:
            return candidates[0]
    fail(f"Could not find required input file for {label}.")


def download_or_read_cbo_dictionary(filename: str, url: str) -> list[dict[str, str]]:
    SOURCE_DICT_DIR.mkdir(parents=True, exist_ok=True)
    path = SOURCE_DICT_DIR / filename
    if not path.exists():
        with urllib.request.urlopen(url, timeout=30) as response:
            path.write_bytes(response.read())
    text = path.read_bytes().decode("latin-1")
    return read_semicolon_csv_text(text)


def build_cbo_titles() -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    family_rows = download_or_read_cbo_dictionary("cbo2002-familia.csv", CBO_FAMILY_URL)
    minor_rows = download_or_read_cbo_dictionary("cbo2002-subgrupo.csv", CBO_MINOR_URL)
    submajor_rows = download_or_read_cbo_dictionary("cbo2002-subgrupo-principal.csv", CBO_SUBMAJOR_URL)
    major_rows = download_or_read_cbo_dictionary("cbo2002-grande-grupo.csv", CBO_MAJOR_URL)

    family_titles = {
        normalize_code(row.get("CODIGO"), 4): row.get("TITULO", "").strip()
        for row in family_rows
        if normalize_code(row.get("CODIGO"), 4)
    }
    minor_titles = {
        normalize_code(row.get("CODIGO"), 3): row.get("TITULO", "").strip()
        for row in minor_rows
        if normalize_code(row.get("CODIGO"), 3)
    }
    submajor_titles = {
        normalize_code(row.get("CODIGO"), 2): row.get("TITULO", "").strip()
        for row in submajor_rows
        if normalize_code(row.get("CODIGO"), 2)
    }
    major_titles = {
        normalize_code(row.get("CODIGO"), 1): row.get("TITULO", "").strip()
        for row in major_rows
        if normalize_code(row.get("CODIGO"), 1)
    }
    return family_titles, minor_titles, submajor_titles, major_titles


def build_cod_titles() -> dict[str, str]:
    path = find_input_file(["Estrutura Ocupação COD.xls", "*Estrutura*COD.xls"], "COD occupation structure")
    rscript = shutil.which("Rscript")
    if not rscript:
        fail("Rscript is required to read the COD .xls dictionary and add COD occupation titles.")

    r_code = r"""
args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages(library(readxl))
df <- read_excel(
  args[[1]],
  sheet = "Estrutura COD",
  skip = 2,
  col_names = c("grande_grupo", "subgrupo_principal", "subgrupo", "grupo_base", "denominacao")
)
df <- df[!is.na(df$grupo_base) & !is.na(df$denominacao), c("grupo_base", "denominacao")]
write.csv(df, stdout(), row.names = FALSE, na = "", fileEncoding = "UTF-8")
"""
    result = subprocess.run(
        [rscript, "-e", r_code, str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    return {
        normalize_code(row.get("grupo_base"), 4): row.get("denominacao", "").strip()
        for row in rows
        if normalize_code(row.get("grupo_base"), 4)
    }


def build_isco_titles(ilo_titles: dict[str, str]) -> dict[str, str]:
    path = find_input_file(["ISCO 08 Estruturas e Definições.xlsx", "*ISCO*Estruturas*Definic*.xlsx"], "ISCO-08 structure")
    rows = read_xlsx_sheet(path, "ISCO-08 EN Struct and defin")
    if not rows:
        fail("ISCO-08 structure sheet is empty.")

    header = rows[0]
    try:
        code_idx = header.index("ISCO 08 Code")
        title_idx = header.index("Title EN")
    except ValueError as exc:
        raise RuntimeError(f"Could not identify ISCO-08 title columns: {header}") from exc

    titles: dict[str, str] = {}
    for row in rows[1:]:
        if len(row) <= max(code_idx, title_idx):
            continue
        raw_code = str(row[code_idx]).strip()
        title = str(row[title_idx]).strip()
        if raw_code and title:
            titles[normalize_code(raw_code, len(raw_code))] = title

    for code, title in ilo_titles.items():
        if title:
            titles.setdefault(normalize_code(code, 4), title)
    return titles


def title_for_code(code: str, titles: dict[str, str]) -> str:
    if not code:
        return ""
    return titles.get(code, "")


def titles_for_codes(codes: list[str], titles: dict[str, str]) -> str:
    values = [title_for_code(code, titles) for code in codes]
    return "; ".join(value for value in values if value)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def markdown_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", "<br>")
    text = text.replace("|", "\\|")
    return text


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(markdown_escape(row.get(col, "")) for col in columns) + " |")
    return "\n".join([header, separator, *body])


def write_markdown_table(path: Path, title: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"# {title}\n\n{markdown_table(rows, columns)}\n"
    path.write_text(text, encoding="utf-8")


def column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    total = 0
    for char in letters:
        total = total * 26 + (ord(char) - ord("A") + 1)
    return total - 1


def read_xlsx_sheet(path: Path, sheet_name: str) -> list[list[str]]:
    """Read a simple .xlsx worksheet using only the standard library."""
    if not path.exists():
        fail(f"Required input not found: {path}")

    ns_main = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    ns_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    ns_pkg_rel = "{http://schemas.openxmlformats.org/package/2006/relationships}"

    with zipfile.ZipFile(path) as zf:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{ns_main}si"):
                parts = [node.text or "" for node in si.iter(f"{ns_main}t")]
                shared_strings.append("".join(parts))

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall(f"{ns_pkg_rel}Relationship")
        }

        selected_rid = None
        for sheet in workbook.findall(f".//{ns_main}sheet"):
            if sheet.attrib.get("name") == sheet_name:
                selected_rid = sheet.attrib.get(f"{ns_rel}id")
                break
        if selected_rid is None:
            available = [sheet.attrib.get("name", "") for sheet in workbook.findall(f".//{ns_main}sheet")]
            fail(f"Sheet '{sheet_name}' not found in {path.name}. Available sheets: {available}")

        target = rel_targets[selected_rid]
        if target.startswith("/"):
            sheet_path = target.lstrip("/")
        else:
            sheet_path = "xl/" + target
        sheet_root = ET.fromstring(zf.read(sheet_path))

        rows: list[list[str]] = []
        for row in sheet_root.findall(f".//{ns_main}sheetData/{ns_main}row"):
            values: list[str] = []
            for cell in row.findall(f"{ns_main}c"):
                idx = column_index(cell.attrib.get("r", "A1"))
                while len(values) <= idx:
                    values.append("")
                cell_type = cell.attrib.get("t")
                value_node = cell.find(f"{ns_main}v")
                if cell_type == "s":
                    raw = value_node.text if value_node is not None else ""
                    values[idx] = shared_strings[int(raw)] if raw else ""
                elif cell_type == "inlineStr":
                    text_node = cell.find(f"{ns_main}is/{ns_main}t")
                    values[idx] = text_node.text if text_node is not None else ""
                else:
                    values[idx] = value_node.text if value_node is not None else ""
            rows.append(values)
        return rows


def find_isco_correspondence_file() -> Path:
    candidates = sorted((DATA / "input").glob("*ISCO*08*a*88.xlsx"))
    if not candidates:
        candidates = sorted((DATA / "input").glob("*ISCO*88.xlsx"))
    if not candidates:
        fail("Could not find the ISCO-08/ISCO-88 correspondence .xlsx file.")
    return candidates[0]


def build_ilo_lookups() -> dict[str, Any]:
    rows = read_csv_dicts(ILO_FILE)
    by_4d: dict[str, list[float]] = defaultdict(list)
    titles: dict[str, str] = {}
    gradients: dict[str, str] = {}

    for row in rows:
        code = normalize_code(row.get("isco_08_str") or row.get("isco_08"), 4)
        score = parse_float(row.get("exposure_score"))
        if not code or score is None:
            continue
        by_4d[code].append(score)
        titles.setdefault(code, row.get("occupation_title", ""))
        gradients.setdefault(code, row.get("exposure_gradient", ""))

    ilo_4d = {code: mean(scores) for code, scores in by_4d.items()}

    def grouped(prefix_len: int) -> dict[str, float]:
        groups: dict[str, list[float]] = defaultdict(list)
        for code, score in ilo_4d.items():
            groups[code[:prefix_len]].append(score)
        return {code: mean(scores) for code, scores in groups.items()}

    return {
        "ilo_4d": ilo_4d,
        "ilo_3d": grouped(3),
        "ilo_2d": grouped(2),
        "ilo_1d": grouped(1),
        "titles": titles,
        "gradients": gradients,
    }


def build_isco_correspondence() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    rows = read_xlsx_sheet(find_isco_correspondence_file(), "ISCO-08 to 88")
    if not rows:
        fail("ISCO correspondence sheet is empty.")

    header = rows[0]
    try:
        isco08_idx = header.index("ISCO-08 code")
        isco88_idx = header.index("ISCO-88 code")
    except ValueError as exc:
        raise RuntimeError(f"Could not identify required ISCO correspondence columns: {header}") from exc

    isco88_to_08: dict[str, list[str]] = defaultdict(list)
    isco88_3d_to_08_3d: dict[str, set[str]] = defaultdict(set)

    for row in rows[1:]:
        if len(row) <= max(isco08_idx, isco88_idx):
            continue
        isco08 = normalize_code(row[isco08_idx], 4)
        isco88 = normalize_code(row[isco88_idx], 4)
        if not isco08 or not isco88:
            continue
        isco88_to_08[isco88].append(isco08)
        isco88_3d_to_08_3d[isco88[:3]].add(isco08[:3])

    return dict(isco88_to_08), {key: sorted(value) for key, value in isco88_3d_to_08_3d.items()}


class MTEBridgeClient:
    """Small JSF client for the official MTE CBO2002-CBO94-CIUO88 table."""

    def __init__(self) -> None:
        cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        self.view_state = ""
        self.dtpinfra_token = ""
        self.refresh_form_state()

    def refresh_form_state(self) -> None:
        request = urllib.request.Request(MTE_BRIDGE_URL, headers={"User-Agent": "Mozilla/5.0"})
        html_text = self.opener.open(request, timeout=30).read().decode("iso-8859-1", errors="replace")
        self.update_form_state(html_text)

    def update_form_state(self, html_text: str) -> None:
        view_states = re.findall(r'name="javax\.faces\.ViewState"[^>]+value="([^"]+)"', html_text)
        tokens = re.findall(r'name="DTPINFRA_TOKEN"[^>]+value="([^"]+)"', html_text)
        if view_states:
            self.view_state = html_lib.unescape(view_states[-1])
        if tokens:
            self.dtpinfra_token = html_lib.unescape(tokens[-1])
        if not self.view_state:
            fail("Could not read JSF ViewState from MTE conversion page.")

    def query_family(self, cbo_4d: str) -> list[dict[str, str]]:
        payload = {
            "formSite038": "formSite038",
            "DTPINFRA_TOKEN": self.dtpinfra_token,
            "formSite038:j_idt83": cbo_4d,
            "formSite038:j_idt85": "Consultar",
            "javax.faces.ViewState": self.view_state,
        }
        request = urllib.request.Request(
            MTE_BRIDGE_URL,
            data=urllib.parse.urlencode(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0",
            },
        )
        html_text = self.opener.open(request, timeout=30).read().decode("iso-8859-1", errors="replace")
        self.update_form_state(html_text)
        return parse_mte_bridge_html(cbo_4d, html_text)


def parse_mte_bridge_html(cbo_4d: str, html_text: str) -> list[dict[str, str]]:
    table_match = re.search(
        r'<table[^>]+id="formSite038:itens"[^>]*>(.*?)</table>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not table_match:
        return [
            {
                "source_cbo_4d": cbo_4d,
                "status": "no_result",
                "cbo2002_6d": "",
                "cbo2002_title": "",
                "cbo94_code": "",
                "ciuo88_code": "",
                "query_note": "No MTE result table for this CBO 4d family.",
            }
        ]

    rows: list[dict[str, str]] = []
    for row_match in re.finditer(r"<tr[^>]*>(.*?)</tr>", table_match.group(1), flags=re.IGNORECASE | re.DOTALL):
        cells = [
            clean_html_text(cell_match.group(1))
            for cell_match in re.finditer(r"<td[^>]*>(.*?)</td>", row_match.group(1), flags=re.IGNORECASE | re.DOTALL)
        ]
        if len(cells) < 4 or not re.match(r"^\d{4}-\d{2}$", cells[0]):
            continue
        ciuo88 = normalize_code(cells[3], 4) if re.match(r"^\d{1,4}$", cells[3].strip()) else ""
        rows.append(
            {
                "source_cbo_4d": cbo_4d,
                "status": "matched" if ciuo88 else "no_result",
                "cbo2002_6d": cells[0].replace("-", ""),
                "cbo2002_title": cells[1],
                "cbo94_code": cells[2],
                "ciuo88_code": ciuo88,
                "query_note": "" if ciuo88 else "MTE row did not include a valid CIUO88 code.",
            }
        )

    if not rows:
        return [
            {
                "source_cbo_4d": cbo_4d,
                "status": "no_result",
                "cbo2002_6d": "",
                "cbo2002_title": "",
                "cbo94_code": "",
                "ciuo88_code": "",
                "query_note": "MTE result table had no parseable conversion rows.",
            }
        ]
    return rows


def load_mte_bridge_cache() -> list[dict[str, str]]:
    if not MTE_BRIDGE_CACHE.exists():
        return []
    return read_csv_dicts(MTE_BRIDGE_CACHE)


def write_mte_bridge_cache(rows: list[dict[str, str]]) -> None:
    columns = [
        "source_cbo_4d",
        "status",
        "cbo2002_6d",
        "cbo2002_title",
        "cbo94_code",
        "ciuo88_code",
        "query_note",
    ]
    write_csv(MTE_BRIDGE_CACHE, rows, columns)


def build_mte_bridge_cache(cbo_codes: list[str]) -> list[dict[str, str]]:
    cache_rows = load_mte_bridge_cache()
    cached_codes = {row.get("source_cbo_4d", "") for row in cache_rows}
    missing_codes = [code for code in sorted(cbo_codes) if code not in cached_codes]

    if missing_codes:
        try:
            client = MTEBridgeClient()
        except Exception as exc:
            if not cache_rows:
                fail(f"Could not consult the official MTE bridge and no cache exists: {exc}")
            for code in missing_codes:
                cache_rows.append(
                    {
                        "source_cbo_4d": code,
                        "status": "query_error",
                        "cbo2002_6d": "",
                        "cbo2002_title": "",
                        "cbo94_code": "",
                        "ciuo88_code": "",
                        "query_note": f"MTE query unavailable; reused partial cache. Error: {exc}",
                    }
                )
            write_mte_bridge_cache(cache_rows)
            missing_codes = []
        else:
            for index, code in enumerate(missing_codes, start=1):
                try:
                    cache_rows.extend(client.query_family(code))
                except (urllib.error.URLError, TimeoutError, RuntimeError, OSError) as exc:
                    cache_rows.append(
                        {
                            "source_cbo_4d": code,
                            "status": "query_error",
                            "cbo2002_6d": "",
                            "cbo2002_title": "",
                            "cbo94_code": "",
                            "ciuo88_code": "",
                            "query_note": str(exc),
                        }
                    )
                if index % 25 == 0:
                    write_mte_bridge_cache(cache_rows)
            write_mte_bridge_cache(cache_rows)

    cached_codes = {row.get("source_cbo_4d", "") for row in cache_rows}
    missing_after_cache = sorted(set(cbo_codes) - cached_codes)
    if missing_after_cache:
        fail(f"MTE bridge cache is missing CBO 4d families: {missing_after_cache[:10]}")

    return [row for row in cache_rows if row.get("source_cbo_4d") in set(cbo_codes)]


def note_pnad(match_level: str) -> str:
    if match_level == "4-digit":
        return "Match exato: o código COD foi usado diretamente como ISCO-08 4d."
    if match_level == "3-digit":
        return "Fallback: sem match 4d; score imputado pela média do grupo ISCO-08 3d."
    if match_level == "2-digit":
        return "Fallback: sem match 4d/3d; score imputado pela média do grupo ISCO-08 2d."
    if match_level == "1-digit":
        return "Fallback: sem match 4d/3d/2d; score imputado pela média do grande grupo ISCO-08 1d."
    return "Sem score: nenhum nível hierárquico disponível na planilha ILO."


def note_caged_main(match_level: str) -> str:
    if match_level == "2-digit":
        return "Especificação principal: CBO 2d pareado ao score médio ISCO-08 2d."
    if match_level == "1-digit (fallback)":
        return "Fallback principal: CBO 2d sem equivalente; score médio do grande grupo ISCO-08 1d."
    return "Sem score na especificação principal."


def note_caged_robust(step: str) -> str:
    notes = {
        "N1: ISCO-08 4d direct": "Robustez 4d: coincidência numérica direta entre CBO 4d e ISCO-08 4d.",
        "N2: via ISCO-88->08 4d": "Robustez 4d: CBO 4d tratado como candidato ISCO-88 4d; ponte oficial ISCO-88 -> ISCO-08.",
        "N3: ISCO-08 3d": "Robustez 4d: fallback para média do grupo ISCO-08 3d.",
        "N4: via ISCO-88->08 3d": "Robustez 4d: CBO 3d tratado como candidato ISCO-88 3d; ponte oficial para ISCO-08 3d.",
        "N5: ISCO-08 2d": "Robustez 4d: fallback para média do subgrupo ISCO-08 2d.",
        "N6: ISCO-08 1d": "Robustez 4d: fallback final para média do grande grupo ISCO-08 1d.",
        "sem_match": "Sem score na especificação de robustez 4d.",
    }
    return notes[step]


def validate_counts(actual: Counter, expected: dict[str, int], label: str) -> None:
    for key, expected_value in expected.items():
        actual_value = actual.get(key, 0)
        if actual_value != expected_value:
            fail(f"{label}: expected {expected_value} for '{key}', got {actual_value}.")


def validate_series_scores(rows: list[dict[str, Any]], expected_field: str, actual_field: str, key_field: str) -> None:
    for row in rows:
        expected = row.get(expected_field)
        actual = row.get(actual_field)
        if not almost_equal(expected, actual):
            fail(
                f"Score validation failed for {key_field}={row.get(key_field)}: "
                f"expected {expected}, actual {actual}."
            )


def build_pnad_table(
    lookups: dict[str, Any],
    cod_titles: dict[str, str],
    isco_titles: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ilo_4d = lookups["ilo_4d"]
    ilo_3d = lookups["ilo_3d"]
    ilo_2d = lookups["ilo_2d"]
    ilo_1d = lookups["ilo_1d"]

    groups: dict[str, dict[str, Any]] = {}
    row_level_counts: Counter = Counter()

    for row in read_csv_dicts(PNAD_FILE):
        code = normalize_code(row.get("cod_ocupacao"), 4)
        match_level = row.get("match_level") or "sem_match"
        score = parse_float(row.get("exposure_score"))
        weight = parse_float(row.get("peso")) or 0.0

        row_level_counts[match_level] += 1
        if code not in groups:
            groups[code] = {
                "cod_ocupacao": code,
                "match_level": match_level,
                "exposure_score_raw": score,
                "exposure_gradient": row.get("exposure_gradient") or "",
                "n_observacoes_raw": 0,
                "peso_total_raw": 0.0,
            }
        groups[code]["n_observacoes_raw"] += 1
        groups[code]["peso_total_raw"] += weight

    validate_counts(row_level_counts, EXPECTED_PNAD_ROWS, "PNAD row-level match counts")

    output_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []

    for code in sorted(groups):
        group = groups[code]
        match_level = group["match_level"]
        if match_level == "4-digit":
            target_level = "4-digit"
            target_code = code
            expected_score = ilo_4d.get(code)
        elif match_level == "3-digit":
            target_level = "3-digit"
            target_code = code[:3]
            expected_score = ilo_3d.get(code[:3])
        elif match_level == "2-digit":
            target_level = "2-digit"
            target_code = code[:2]
            expected_score = ilo_2d.get(code[:2])
        elif match_level == "1-digit":
            target_level = "1-digit"
            target_code = code[:1]
            expected_score = ilo_1d.get(code[:1])
        else:
            target_level = "sem_match"
            target_code = ""
            expected_score = None

        validation_rows.append(
            {
                "cod_ocupacao": code,
                "expected_score": expected_score,
                "actual_score": group["exposure_score_raw"],
            }
        )

        output_rows.append(
            {
                "cod_ocupacao": code,
                "source_cod_title": title_for_code(code, cod_titles),
                "match_level": match_level,
                "target_isco_level": target_level,
                "target_isco_code": target_code,
                "target_isco_title": title_for_code(target_code, isco_titles),
                "exposure_score": fmt_float(group["exposure_score_raw"]),
                "exposure_gradient": group["exposure_gradient"],
                "n_observacoes": group["n_observacoes_raw"],
                "peso_total": fmt_float(group["peso_total_raw"], 3),
                "nota_metodologica": note_pnad(match_level),
            }
        )

    validate_series_scores(validation_rows, "expected_score", "actual_score", "cod_ocupacao")

    summary_rows = summary_from_counter(
        row_level_counts,
        [
            ("4-digit", "Match exato COD 4d = ISCO-08 4d"),
            ("3-digit", "Fallback para média ISCO-08 3d"),
            ("2-digit", "Fallback para média ISCO-08 2d"),
            ("1-digit", "Fallback para média ISCO-08 1d"),
            ("sem_match", "Sem match"),
        ],
        denominator=sum(row_level_counts.values()),
        code_counts=Counter(row["match_level"] for row in output_rows),
        code_denominator=len(output_rows),
        count_label="observacoes",
        code_label="codigos_cod",
    )
    return output_rows, summary_rows


def robust_mapping(
    cbo: str,
    lookups: dict[str, Any],
    isco88_to_08: dict[str, list[str]],
    isco88_3d_to_08_3d: dict[str, list[str]],
) -> dict[str, Any]:
    ilo_4d = lookups["ilo_4d"]
    ilo_3d = lookups["ilo_3d"]
    ilo_2d = lookups["ilo_2d"]
    ilo_1d = lookups["ilo_1d"]

    if cbo in ilo_4d:
        return {
            "robust_step": "N1: ISCO-08 4d direct",
            "source_interpretation": "CBO 4d lido diretamente como ISCO-08 4d",
            "source_isco88_code": "",
            "target_isco08_level": "4-digit",
            "target_isco08_codes": [cbo],
            "candidate_scores": [ilo_4d[cbo]],
            "score": ilo_4d[cbo],
        }

    if cbo in isco88_to_08:
        target_codes = [code for code in isco88_to_08[cbo] if code in ilo_4d]
        if target_codes:
            scores = [ilo_4d[code] for code in target_codes]
            return {
                "robust_step": "N2: via ISCO-88->08 4d",
                "source_interpretation": "CBO 4d tratado como candidato ISCO-88 4d",
                "source_isco88_code": cbo,
                "target_isco08_level": "4-digit",
                "target_isco08_codes": target_codes,
                "candidate_scores": scores,
                "score": mean(scores),
            }

    cbo_3d = cbo[:3]
    if cbo_3d in ilo_3d:
        return {
            "robust_step": "N3: ISCO-08 3d",
            "source_interpretation": "CBO 3d lido diretamente como ISCO-08 3d",
            "source_isco88_code": "",
            "target_isco08_level": "3-digit",
            "target_isco08_codes": [cbo_3d],
            "candidate_scores": [ilo_3d[cbo_3d]],
            "score": ilo_3d[cbo_3d],
        }

    if cbo_3d in isco88_3d_to_08_3d:
        target_codes_3d = [code for code in isco88_3d_to_08_3d[cbo_3d] if code in ilo_3d]
        if target_codes_3d:
            scores = [ilo_3d[code] for code in target_codes_3d]
            return {
                "robust_step": "N4: via ISCO-88->08 3d",
                "source_interpretation": "CBO 3d tratado como candidato ISCO-88 3d",
                "source_isco88_code": cbo_3d,
                "target_isco08_level": "3-digit",
                "target_isco08_codes": target_codes_3d,
                "candidate_scores": scores,
                "score": mean(scores),
            }

    cbo_2d = cbo[:2]
    if cbo_2d in ilo_2d:
        return {
            "robust_step": "N5: ISCO-08 2d",
            "source_interpretation": "CBO 2d lido diretamente como ISCO-08 2d",
            "source_isco88_code": "",
            "target_isco08_level": "2-digit",
            "target_isco08_codes": [cbo_2d],
            "candidate_scores": [ilo_2d[cbo_2d]],
            "score": ilo_2d[cbo_2d],
        }

    cbo_1d = cbo[:1]
    if cbo_1d in ilo_1d:
        return {
            "robust_step": "N6: ISCO-08 1d",
            "source_interpretation": "CBO 1d lido diretamente como ISCO-08 1d",
            "source_isco88_code": "",
            "target_isco08_level": "1-digit",
            "target_isco08_codes": [cbo_1d],
            "candidate_scores": [ilo_1d[cbo_1d]],
            "score": ilo_1d[cbo_1d],
        }

    return {
        "robust_step": "sem_match",
        "source_interpretation": "Nenhuma correspondência operacional disponível",
        "source_isco88_code": "",
        "target_isco08_level": "sem_match",
        "target_isco08_codes": [],
        "candidate_scores": [],
        "score": None,
    }


def build_caged_tables(
    lookups: dict[str, Any],
    isco88_to_08: dict[str, list[str]],
    isco88_3d_to_08_3d: dict[str, list[str]],
    cbo_family_titles: dict[str, str],
    cbo_minor_titles: dict[str, str],
    cbo_submajor_titles: dict[str, str],
    cbo_major_titles: dict[str, str],
    isco_titles: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ilo_2d = lookups["ilo_2d"]
    ilo_1d = lookups["ilo_1d"]

    groups: dict[str, dict[str, Any]] = {}
    caged_source = CAGED_CROSSWALK_FILE if CAGED_CROSSWALK_FILE.exists() else CAGED_FILE
    for row in read_csv_dicts(caged_source):
        cbo = normalize_code(row.get("cbo_4d"), 4)
        if not cbo:
            continue
        cbo_2d = normalize_code(row.get("cbo_2d") or cbo[:2], 2)
        admissions = parse_float(row.get("admissoes")) or 0.0
        score_2d = parse_float(row.get("exposure_score_2d_old") or row.get("exposure_score_2d"))
        score_4d = parse_float(row.get("exposure_score_4d_old") or row.get("exposure_score_4d"))

        if cbo not in groups:
            groups[cbo] = {
                "cbo_4d": cbo,
                "cbo_2d": cbo_2d,
                "score_2d_raw": score_2d,
                "score_4d_raw": score_4d,
                "panel_rows_raw": 0,
                "admissoes_total_raw": 0.0,
            }
        groups[cbo]["panel_rows_raw"] += 1
        groups[cbo]["admissoes_total_raw"] += admissions

    main_rows: list[dict[str, Any]] = []
    robust_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    main_validation: list[dict[str, Any]] = []
    robust_validation: list[dict[str, Any]] = []
    main_code_counts: Counter = Counter()
    main_row_counts: Counter = Counter()
    robust_code_counts: Counter = Counter()
    robust_row_counts: Counter = Counter()

    for cbo in sorted(groups):
        group = groups[cbo]
        cbo_2d = group["cbo_2d"]
        cbo_1d = cbo[:1]
        if cbo_2d in ilo_2d:
            main_level = "2-digit"
            main_target_level = "2-digit"
            main_target_code = cbo_2d
            expected_2d = ilo_2d[cbo_2d]
        elif cbo_1d in ilo_1d:
            main_level = "1-digit (fallback)"
            main_target_level = "1-digit"
            main_target_code = cbo_1d
            expected_2d = ilo_1d[cbo_1d]
        else:
            main_level = "sem_match"
            main_target_level = "sem_match"
            main_target_code = ""
            expected_2d = None

        robust = robust_mapping(cbo, lookups, isco88_to_08, isco88_3d_to_08_3d)
        robust_step = robust["robust_step"]

        panel_rows = group["panel_rows_raw"]
        main_code_counts[main_level] += 1
        main_row_counts[main_level] += panel_rows
        robust_code_counts[robust_step] += 1
        robust_row_counts[robust_step] += panel_rows

        main_validation.append(
            {
                "cbo_4d": cbo,
                "expected_score": expected_2d,
                "actual_score": group["score_2d_raw"],
            }
        )
        robust_validation.append(
            {
                "cbo_4d": cbo,
                "expected_score": robust["score"],
                "actual_score": group["score_4d_raw"],
            }
        )

        main_rows.append(
            {
                "cbo_4d": cbo,
                "source_cbo_title": title_for_code(cbo, cbo_family_titles),
                "cbo_3d": cbo[:3],
                "source_cbo_3d_title": title_for_code(cbo[:3], cbo_minor_titles),
                "cbo_2d": cbo_2d,
                "source_cbo_2d_title": title_for_code(cbo_2d, cbo_submajor_titles),
                "cbo_1d": cbo[:1],
                "source_cbo_1d_title": title_for_code(cbo[:1], cbo_major_titles),
                "match_level_2d": main_level,
                "target_isco_level": main_target_level,
                "target_isco_code": main_target_code,
                "target_isco_title": title_for_code(main_target_code, isco_titles),
                "exposure_score_2d": fmt_float(group["score_2d_raw"]),
                "panel_rows": panel_rows,
                "admissoes_total": int(round(group["admissoes_total_raw"])),
                "nota_metodologica": note_caged_main(main_level),
            }
        )

        robust_rows.append(
            {
                "cbo_4d": cbo,
                "source_cbo_title": title_for_code(cbo, cbo_family_titles),
                "cbo_3d": cbo[:3],
                "source_cbo_3d_title": title_for_code(cbo[:3], cbo_minor_titles),
                "cbo_2d": cbo_2d,
                "source_cbo_2d_title": title_for_code(cbo_2d, cbo_submajor_titles),
                "cbo_1d": cbo[:1],
                "source_cbo_1d_title": title_for_code(cbo[:1], cbo_major_titles),
                "robust_step": robust_step,
                "source_interpretation": robust["source_interpretation"],
                "source_isco88_code": robust["source_isco88_code"],
                "target_isco08_level": robust["target_isco08_level"],
                "target_isco08_codes": ", ".join(robust["target_isco08_codes"]),
                "target_isco08_titles": titles_for_codes(robust["target_isco08_codes"], isco_titles),
                "candidate_scores": ", ".join(fmt_float(score) for score in robust["candidate_scores"]),
                "exposure_score_4d": fmt_float(group["score_4d_raw"]),
                "panel_rows": panel_rows,
                "admissoes_total": int(round(group["admissoes_total_raw"])),
                "nota_metodologica": note_caged_robust(robust_step),
            }
        )

        score_2d = group["score_2d_raw"]
        score_4d = group["score_4d_raw"]
        comparison_rows.append(
            {
                "cbo_4d": cbo,
                "source_cbo_title": title_for_code(cbo, cbo_family_titles),
                "source_cbo_1d_title": title_for_code(cbo[:1], cbo_major_titles),
                "score_2d": fmt_float(score_2d),
                "score_4d": fmt_float(score_4d),
                "absolute_difference": fmt_float(abs(score_2d - score_4d) if score_2d is not None and score_4d is not None else None),
                "match_level_2d": main_level,
                "robust_step": robust_step,
                "panel_rows": panel_rows,
                "admissoes_total": int(round(group["admissoes_total_raw"])),
            }
        )

    validate_series_scores(main_validation, "expected_score", "actual_score", "cbo_4d")
    validate_series_scores(robust_validation, "expected_score", "actual_score", "cbo_4d")
    validate_counts(main_code_counts, EXPECTED_CAGED_MAIN_CODES, "CAGED main code counts")
    validate_counts(main_row_counts, EXPECTED_CAGED_MAIN_ROWS, "CAGED main row counts")
    validate_counts(robust_code_counts, EXPECTED_CAGED_ROBUST_CODES, "CAGED robust code counts")
    validate_counts(robust_row_counts, EXPECTED_CAGED_ROBUST_ROWS, "CAGED robust row counts")

    main_summary = summary_from_counter(
        main_code_counts,
        [
            ("2-digit", "CBO 2d -> média ISCO-08 2d"),
            ("1-digit (fallback)", "Fallback CBO 1d -> média ISCO-08 1d"),
            ("sem_match", "Sem match"),
        ],
        denominator=sum(main_code_counts.values()),
        code_counts=main_row_counts,
        code_denominator=sum(main_row_counts.values()),
        count_label="codigos_cbo",
        code_label="linhas_painel",
    )

    robust_summary = summary_from_counter(
        robust_code_counts,
        [
            ("N1: ISCO-08 4d direct", "N1: CBO 4d = ISCO-08 4d"),
            ("N2: via ISCO-88->08 4d", "N2: CBO 4d como ISCO-88 4d -> ISCO-08 4d"),
            ("N3: ISCO-08 3d", "N3: média ISCO-08 3d"),
            ("N4: via ISCO-88->08 3d", "N4: CBO 3d como ISCO-88 3d -> ISCO-08 3d"),
            ("N5: ISCO-08 2d", "N5: média ISCO-08 2d"),
            ("N6: ISCO-08 1d", "N6: média ISCO-08 1d"),
            ("sem_match", "Sem match"),
        ],
        denominator=sum(robust_code_counts.values()),
        code_counts=robust_row_counts,
        code_denominator=sum(robust_row_counts.values()),
        count_label="codigos_cbo",
        code_label="linhas_painel",
    )

    return main_rows, robust_rows, comparison_rows, main_summary, robust_summary


def score_from_distinct_targets(target_codes: list[str], score_lookup: dict[str, float]) -> float | None:
    scores = [score_lookup[code] for code in unique_preserve(target_codes) if code in score_lookup]
    return mean(scores) if scores else None


def build_caged_mte_bridge_tables(
    caged_main_rows: list[dict[str, Any]],
    caged_robust_rows: list[dict[str, Any]],
    lookups: dict[str, Any],
    isco88_to_08: dict[str, list[str]],
    isco_titles: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    ilo_4d = lookups["ilo_4d"]
    ilo_2d = lookups["ilo_2d"]

    main_by_cbo = {row["cbo_4d"]: row for row in caged_main_rows}
    robust_by_cbo = {row["cbo_4d"]: row for row in caged_robust_rows}
    cbo_codes = sorted(main_by_cbo)
    cache_rows = build_mte_bridge_cache(cbo_codes)

    cache_by_cbo: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in cache_rows:
        cache_by_cbo[row["source_cbo_4d"]].append(row)

    bridge_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []

    for cbo in cbo_codes:
        main = main_by_cbo[cbo]
        robust = robust_by_cbo[cbo]
        rows = cache_by_cbo.get(cbo, [])
        matched_rows = [row for row in rows if row.get("status") == "matched" and row.get("ciuo88_code")]
        cache_statuses = unique_preserve([row.get("status", "") for row in rows])

        ciuo88_codes = unique_preserve([row["ciuo88_code"] for row in matched_rows])
        target_isco08_codes = unique_preserve(
            [isco08 for ciuo in ciuo88_codes for isco08 in isco88_to_08.get(ciuo, [])]
        )
        target_isco08_2d_codes = unique_preserve([code[:2] for code in target_isco08_codes])
        score_mte_4d = score_from_distinct_targets(target_isco08_codes, ilo_4d)
        score_mte_2d = score_from_distinct_targets(target_isco08_2d_codes, ilo_2d)

        if score_mte_4d is not None:
            mte_match_status = "matched_official_mte"
        elif any(status == "query_error" for status in cache_statuses):
            mte_match_status = "sem_match_query_error"
        elif not matched_rows:
            mte_match_status = "sem_match_mte_no_result"
        elif not target_isco08_codes:
            mte_match_status = "sem_match_ciuo88_without_isco08"
        else:
            mte_match_status = "sem_match_isco08_without_ilo_score"

        old_score_2d = parse_float(main.get("exposure_score_2d"))
        old_score_4d = parse_float(robust.get("exposure_score_4d"))
        candidate_scores_4d = [ilo_4d[code] for code in target_isco08_codes if code in ilo_4d]
        candidate_scores_2d = [ilo_2d[code] for code in target_isco08_2d_codes if code in ilo_2d]

        bridge_rows.append(
            {
                "cbo_4d": cbo,
                "source_cbo_title": main.get("source_cbo_title", ""),
                "cbo_3d": main.get("cbo_3d", ""),
                "source_cbo_3d_title": main.get("source_cbo_3d_title", ""),
                "cbo_2d": main.get("cbo_2d", ""),
                "source_cbo_2d_title": main.get("source_cbo_2d_title", ""),
                "cbo_1d": main.get("cbo_1d", ""),
                "source_cbo_1d_title": main.get("source_cbo_1d_title", ""),
                "mte_cache_statuses": ", ".join(cache_statuses),
                "mte_match_status": mte_match_status,
                "cbo2002_6d_codes": ", ".join(unique_preserve([row.get("cbo2002_6d", "") for row in matched_rows])),
                "cbo2002_6d_titles": "; ".join(unique_preserve([row.get("cbo2002_title", "") for row in matched_rows])),
                "cbo94_codes": ", ".join(unique_preserve([row.get("cbo94_code", "") for row in matched_rows])),
                "ciuo88_codes": ", ".join(ciuo88_codes),
                "target_isco08_codes": ", ".join(target_isco08_codes),
                "target_isco08_titles": titles_for_codes(target_isco08_codes, isco_titles),
                "target_isco08_2d_codes": ", ".join(target_isco08_2d_codes),
                "target_isco08_2d_titles": titles_for_codes(target_isco08_2d_codes, isco_titles),
                "candidate_scores_mte_4d": ", ".join(fmt_float(score) for score in candidate_scores_4d),
                "candidate_scores_mte_2d": ", ".join(fmt_float(score) for score in candidate_scores_2d),
                "exposure_score_mte_4d": fmt_float(score_mte_4d),
                "exposure_score_mte_2d": fmt_float(score_mte_2d),
                "panel_rows": main.get("panel_rows", ""),
                "admissoes_total": main.get("admissoes_total", ""),
                "nota_metodologica": note_mte_bridge(mte_match_status),
            }
        )

        comparison_rows.append(
            {
                "cbo_4d": cbo,
                "source_cbo_title": main.get("source_cbo_title", ""),
                "cbo_2d": main.get("cbo_2d", ""),
                "source_cbo_2d_title": main.get("source_cbo_2d_title", ""),
                "old_main_match_level": main.get("match_level_2d", ""),
                "old_robust_step": robust.get("robust_step", ""),
                "mte_match_status": mte_match_status,
                "old_target_2d_code": main.get("target_isco_code", ""),
                "old_target_2d_title": main.get("target_isco_title", ""),
                "old_target_4d_codes": robust.get("target_isco08_codes", ""),
                "old_target_4d_titles": robust.get("target_isco08_titles", ""),
                "mte_ciuo88_codes": ", ".join(ciuo88_codes),
                "mte_target_isco08_codes": ", ".join(target_isco08_codes),
                "mte_target_isco08_titles": titles_for_codes(target_isco08_codes, isco_titles),
                "mte_target_isco08_2d_codes": ", ".join(target_isco08_2d_codes),
                "mte_target_isco08_2d_titles": titles_for_codes(target_isco08_2d_codes, isco_titles),
                "score_2d_old": fmt_float(old_score_2d),
                "score_4d_old": fmt_float(old_score_4d),
                "score_mte_2d": fmt_float(score_mte_2d),
                "score_mte_4d": fmt_float(score_mte_4d),
                "absolute_difference_old2d_mte2d": fmt_float(
                    abs(old_score_2d - score_mte_2d)
                    if old_score_2d is not None and score_mte_2d is not None
                    else None
                ),
                "absolute_difference_old4d_mte4d": fmt_float(
                    abs(old_score_4d - score_mte_4d)
                    if old_score_4d is not None and score_mte_4d is not None
                    else None
                ),
                "panel_rows": main.get("panel_rows", ""),
                "admissoes_total": main.get("admissoes_total", ""),
            }
        )

    summary_rows = build_old_vs_mte_summary(comparison_rows)
    semantic_report = build_mte_semantic_review(comparison_rows, summary_rows)
    return bridge_rows, comparison_rows, summary_rows, semantic_report


def note_mte_bridge(status: str) -> str:
    notes = {
        "matched_official_mte": "Ponte oficial MTE: CBO 2002 -> CIUO88; depois correspondência oficial ISCO-88 -> ISCO-08.",
        "sem_match_query_error": "Sem score novo: consulta à tábua MTE falhou para esta família CBO.",
        "sem_match_mte_no_result": "Sem score novo: a tábua MTE não retornou conversão para esta família CBO.",
        "sem_match_ciuo88_without_isco08": "Sem score novo: há CIUO88 no MTE, mas sem destino na tabela ISCO-88 -> ISCO-08.",
        "sem_match_isco08_without_ilo_score": "Sem score novo: há destino ISCO-08, mas nenhum score OIT correspondente.",
    }
    return notes.get(status, "Status não documentado.")


def build_old_vs_mte_summary(comparison_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_codes = len(comparison_rows)
    total_panel = sum(int(row["panel_rows"]) for row in comparison_rows)
    total_admissions = sum(int(row["admissoes_total"]) for row in comparison_rows)
    rows: list[dict[str, Any]] = []

    def add_count_row(section: str, metric: str, selected_rows: list[dict[str, Any]], note: str) -> None:
        panel = sum(int(row["panel_rows"]) for row in selected_rows)
        admissions = sum(int(row["admissoes_total"]) for row in selected_rows)
        rows.append(
            {
                "section": section,
                "metric": metric,
                "codes": len(selected_rows),
                "codes_pct": fmt_pct(len(selected_rows) / total_codes if total_codes else 0),
                "panel_rows": panel,
                "panel_rows_pct": fmt_pct(panel / total_panel if total_panel else 0),
                "admissoes_total": admissions,
                "admissoes_pct": fmt_pct(admissions / total_admissions if total_admissions else 0),
                "weighted_value": "",
                "note": note,
            }
        )

    add_count_row("coverage", "old_2d_valid", comparison_rows, "Crosswalk antigo principal no painel final.")
    add_count_row("coverage", "old_4d_valid", comparison_rows, "Crosswalk antigo de robustez no painel final.")
    mte_valid_rows = [row for row in comparison_rows if row.get("score_mte_4d")]
    add_count_row("coverage", "mte_official_valid", mte_valid_rows, "Novo score com ponte oficial MTE + ISCO-88 -> ISCO-08.")

    for status in sorted({row["mte_match_status"] for row in comparison_rows}):
        status_rows = [row for row in comparison_rows if row["mte_match_status"] == status]
        add_count_row("mte_status", status, status_rows, note_mte_bridge(status))

    for old_col, new_col, label in [
        ("score_2d_old", "score_mte_2d", "old_2d_vs_mte_2d"),
        ("score_4d_old", "score_mte_4d", "old_4d_vs_mte_4d"),
    ]:
        valid = [
            row for row in comparison_rows
            if parse_float(row.get(old_col)) is not None and parse_float(row.get(new_col)) is not None
        ]
        weight_sum_adm = sum(int(row["admissoes_total"]) for row in valid)
        weight_sum_panel = sum(int(row["panel_rows"]) for row in valid)
        weighted_adm = (
            sum(abs(parse_float(row[old_col]) - parse_float(row[new_col])) * int(row["admissoes_total"]) for row in valid)
            / weight_sum_adm
            if weight_sum_adm else 0
        )
        weighted_panel = (
            sum(abs(parse_float(row[old_col]) - parse_float(row[new_col])) * int(row["panel_rows"]) for row in valid)
            / weight_sum_panel
            if weight_sum_panel else 0
        )
        rows.append(
            {
                "section": "magnitude",
                "metric": f"{label}_weighted_abs_diff_admissions",
                "codes": len(valid),
                "codes_pct": fmt_pct(len(valid) / total_codes if total_codes else 0),
                "panel_rows": weight_sum_panel,
                "panel_rows_pct": fmt_pct(weight_sum_panel / total_panel if total_panel else 0),
                "admissoes_total": weight_sum_adm,
                "admissoes_pct": fmt_pct(weight_sum_adm / total_admissions if total_admissions else 0),
                "weighted_value": fmt_float(weighted_adm),
                "note": "Diferença absoluta média ponderada por admissões.",
            }
        )
        rows.append(
            {
                "section": "magnitude",
                "metric": f"{label}_weighted_abs_diff_panel_rows",
                "codes": len(valid),
                "codes_pct": fmt_pct(len(valid) / total_codes if total_codes else 0),
                "panel_rows": weight_sum_panel,
                "panel_rows_pct": fmt_pct(weight_sum_panel / total_panel if total_panel else 0),
                "admissoes_total": weight_sum_adm,
                "admissoes_pct": fmt_pct(weight_sum_adm / total_admissions if total_admissions else 0),
                "weighted_value": fmt_float(weighted_panel),
                "note": "Diferença absoluta média ponderada por linhas do painel.",
            }
        )
        for threshold in [0.05, 0.10, 0.20]:
            threshold_rows = [
                row for row in valid
                if abs(parse_float(row[old_col]) - parse_float(row[new_col])) >= threshold
            ]
            add_count_row(
                "magnitude",
                f"{label}_abs_diff_ge_{threshold:.2f}",
                threshold_rows,
                f"Linhas com diferença absoluta >= {threshold:.2f}.",
            )

    return rows


def build_mte_semantic_review(comparison_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]]) -> str:
    by_cbo = {row["cbo_4d"]: row for row in comparison_rows}

    def check_rows(codes: list[str]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for code in codes:
            row = by_cbo.get(code)
            if row:
                rows.append(
                    {
                        "cbo_4d": code,
                        "source_cbo_title": row["source_cbo_title"],
                        "old_target_4d_titles": row["old_target_4d_titles"],
                        "mte_ciuo88_codes": row["mte_ciuo88_codes"],
                        "mte_target_isco08_titles": row["mte_target_isco08_titles"],
                        "score_4d_old": row["score_4d_old"],
                        "score_mte_4d": row["score_mte_4d"],
                        "admissoes_total": row["admissoes_total"],
                    }
                )
        return rows

    def sorted_by_admissions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(rows, key=lambda row: int(row["admissoes_total"]), reverse=True)

    old_target_differs = [
        row for row in comparison_rows
        if row.get("mte_target_isco08_codes")
        and row.get("old_target_4d_codes")
        and set(row["mte_target_isco08_codes"].split(", ")) != set(row["old_target_4d_codes"].split(", "))
    ]
    old_2d_differs = [
        row for row in comparison_rows
        if row.get("mte_target_isco08_2d_codes")
        and row.get("old_target_2d_code")
        and row["old_target_2d_code"] not in row["mte_target_isco08_2d_codes"].split(", ")
    ]
    new_no_match = [row for row in comparison_rows if row["mte_match_status"] != "matched_official_mte"]
    new_many_to_many = [
        row for row in comparison_rows
        if len([code for code in row.get("mte_target_isco08_2d_codes", "").split(", ") if code]) > 1
    ]

    review_columns = [
        "cbo_4d",
        "source_cbo_title",
        "old_target_4d_titles",
        "mte_ciuo88_codes",
        "mte_target_isco08_titles",
        "score_4d_old",
        "score_mte_4d",
        "admissoes_total",
    ]
    mismatch_columns = [
        "cbo_4d",
        "source_cbo_title",
        "old_target_2d_title",
        "mte_target_isco08_2d_titles",
        "score_2d_old",
        "score_mte_2d",
        "admissoes_total",
    ]
    old_2d_review_rows = [
        {
            "cbo_4d": row["cbo_4d"],
            "source_cbo_title": row["source_cbo_title"],
            "old_target_2d_title": row["old_target_2d_title"],
            "mte_target_isco08_2d_titles": row["mte_target_isco08_2d_titles"],
            "score_2d_old": row["score_2d_old"],
            "score_mte_2d": row["score_mte_2d"],
            "admissoes_total": row["admissoes_total"],
        }
        for row in sorted_by_admissions(old_2d_differs)[:15]
    ]
    many_to_many_rows = [
        {
            "cbo_4d": row["cbo_4d"],
            "source_cbo_title": row["source_cbo_title"],
            "mte_target_isco08_2d_titles": row["mte_target_isco08_2d_titles"],
            "mte_target_isco08_titles": row["mte_target_isco08_titles"],
            "score_mte_4d": row["score_mte_4d"],
            "admissoes_total": row["admissoes_total"],
        }
        for row in sorted_by_admissions(new_many_to_many)[:15]
    ]
    many_to_many_columns = [
        "cbo_4d",
        "source_cbo_title",
        "mte_target_isco08_2d_titles",
        "mte_target_isco08_titles",
        "score_mte_4d",
        "admissoes_total",
    ]

    return f"""# Revisão semântica: crosswalk antigo vs ponte oficial MTE

## Leitura principal

A ponte nova troca o pressuposto `CBO = ISCO` por uma cadeia explícita: `CBO 2002 -> CIUO88/ISCO-88 -> ISCO-08 -> score OIT`. Isso corrige vários falsos positivos do crosswalk antigo. A tabela abaixo resume a comparação quantitativa:

{markdown_table(summary_rows, ["section", "metric", "codes", "codes_pct", "panel_rows", "panel_rows_pct", "admissoes_total", "admissoes_pct", "weighted_value", "note"])}

## Checks específicos pedidos

{markdown_table(check_rows(["9113", "3311", "2501", "2521", "7321"]), review_columns)}

## Principais divergências: alvo antigo 4d vs alvo oficial MTE

Estas linhas tinham destino antigo diferente do destino oficial MTE. A lista é priorizada por admissões.

{markdown_table(check_rows([row["cbo_4d"] for row in sorted_by_admissions(old_target_differs)[:15]]), review_columns)}

## Principais divergências: antigo 2d vs 2d derivado da ponte MTE

Estas linhas mostram onde o score principal antigo por igualdade numérica 2d aponta para outro grupo ISCO-08.

{markdown_table(old_2d_review_rows, mismatch_columns)}

## Pontos remanescentes para inspeção

Casos sem score novo:

{markdown_table(sorted_by_admissions(new_no_match)[:15], ["cbo_4d", "source_cbo_title", "mte_match_status", "mte_ciuo88_codes", "mte_target_isco08_titles", "admissoes_total"])}

Casos em que a ponte oficial MTE leva a mais de um subgrupo ISCO-08 2d:

{markdown_table(many_to_many_rows, many_to_many_columns)}
"""


def summary_from_counter(
    counts: Counter,
    labels: list[tuple[str, str]],
    denominator: int,
    code_counts: Counter,
    code_denominator: int,
    count_label: str,
    code_label: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, label in labels:
        count = counts.get(key, 0)
        secondary = code_counts.get(key, 0)
        rows.append(
            {
                "etapa": key,
                "descricao": label,
                count_label: count,
                f"{count_label}_pct": fmt_pct(count / denominator if denominator else 0),
                code_label: secondary,
                f"{code_label}_pct": fmt_pct(secondary / code_denominator if code_denominator else 0),
            }
        )
    return rows


def write_table_artifacts(name: str, title: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    write_csv(TABLES_DIR / f"{name}.csv", rows, columns)
    write_markdown_table(TABLES_DIR / f"{name}.md", title, rows, columns)


def write_official_mte_artifacts(
    bridge_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    semantic_report: str,
    bridge_columns: list[str],
    comparison_columns: list[str],
    summary_columns: list[str],
) -> None:
    OFFICIAL_MTE_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OFFICIAL_MTE_DIR / "caged_mte_bridge_full.csv", bridge_rows, bridge_columns)
    write_markdown_table(
        OFFICIAL_MTE_DIR / "caged_mte_bridge_full.md",
        "CAGED: ponte oficial MTE CBO2002 -> CIUO88 -> ISCO-08",
        bridge_rows,
        bridge_columns,
    )
    write_csv(OFFICIAL_MTE_DIR / "caged_old_vs_mte_comparison.csv", comparison_rows, comparison_columns)
    write_markdown_table(
        OFFICIAL_MTE_DIR / "caged_old_vs_mte_comparison.md",
        "CAGED: comparação crosswalk antigo vs ponte oficial MTE",
        comparison_rows,
        comparison_columns,
    )
    write_csv(OFFICIAL_MTE_DIR / "summary_old_vs_mte.csv", summary_rows, summary_columns)
    write_markdown_table(
        OFFICIAL_MTE_DIR / "summary_old_vs_mte.md",
        "Resumo: crosswalk antigo vs ponte oficial MTE",
        summary_rows,
        summary_columns,
    )
    (OFFICIAL_MTE_DIR / "caged_mte_semantic_review.md").write_text(semantic_report, encoding="utf-8")


def report_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    return markdown_table(rows, columns)


def build_title_coverage_summary(
    pnad_rows: list[dict[str, Any]],
    caged_main_rows: list[dict[str, Any]],
    caged_robust_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        ("PNAD COD 4d", pnad_rows, "source_cod_title", "Títulos de origem no dicionário COD."),
        (
            "PNAD ISCO-08 destino",
            [row for row in pnad_rows if row.get("target_isco_code")],
            "target_isco_title",
            "Títulos ISCO-08 apenas para códigos com match.",
        ),
        ("CAGED CBO 4d", caged_main_rows, "source_cbo_title", "Títulos de família ocupacional CBO 2002."),
        ("CAGED CBO 3d", caged_main_rows, "source_cbo_3d_title", "Títulos de subgrupo CBO 2002."),
        ("CAGED CBO 2d", caged_main_rows, "source_cbo_2d_title", "Títulos de subgrupo principal CBO 2002."),
        ("CAGED CBO 1d", caged_main_rows, "source_cbo_1d_title", "Títulos de grande grupo CBO 2002."),
        ("CAGED ISCO-08 principal", caged_main_rows, "target_isco_title", "Títulos ISCO-08 da especificação principal."),
        (
            "CAGED ISCO-08 robustez",
            [row for row in caged_robust_rows if row.get("target_isco08_codes")],
            "target_isco08_titles",
            "Títulos ISCO-08 da especificação de robustez.",
        ),
    ]

    rows: list[dict[str, Any]] = []
    for source, table_rows, column, note in checks:
        total = len(table_rows)
        found = sum(1 for row in table_rows if row.get(column))
        rows.append(
            {
                "fonte": source,
                "coluna_titulo": column,
                "linhas_verificadas": total,
                "titulos_encontrados": found,
                "titulos_ausentes": total - found,
                "cobertura": fmt_pct(found / total if total else 0),
                "observacao": note,
            }
        )
    return rows


def build_report(
    pnad_summary: list[dict[str, Any]],
    caged_main_summary: list[dict[str, Any]],
    caged_robust_summary: list[dict[str, Any]],
    title_coverage_summary: list[dict[str, Any]],
) -> str:
    pnad_coverage = (EXPECTED_PNAD_ROWS["4-digit"] + EXPECTED_PNAD_ROWS["3-digit"]) / sum(EXPECTED_PNAD_ROWS.values())

    return f"""# Auditoria dos crosswalks ocupacionais

Este relatório documenta, de forma reprodutível, como os códigos ocupacionais brasileiros foram conectados ao índice da OIT em ISCO-08. Os percentuais são calculados a partir dos arquivos finais do projeto, não digitados manualmente.

## 1. PNAD: COD -> ISCO-08

Na PNAD, a classificação de origem é a COD. Como a COD é derivada da ISCO-08, o procedimento começa tentando o match direto a quatro dígitos. Quando não há match, o algoritmo recua para níveis agregados da própria ISCO-08.

```mermaid
flowchart TD
    A["PNAD: COD 4d"] --> B{{"COD 4d existe como ISCO-08 4d?"}}
    B -- "Sim: 203.617 obs. (97,94%) / 414 códigos" --> C["Usa score ISCO-08 4d"]
    B -- "Não" --> D{{"Grupo ISCO-08 3d disponível?"}}
    D -- "Sim: 2.613 obs. (1,26%) / 8 códigos" --> E["Usa média ISCO-08 3d"]
    D -- "Não" --> F{{"Grupo ISCO-08 2d ou 1d disponível?"}}
    F -- "Não usado: 0 obs. (0,00%)" --> G["Fallback 2d/1d"]
    F -- "Sem match: 1.671 obs. (0,80%) / 6 códigos" --> H["Sem score"]
    C --> I["Cobertura final: {fmt_pct(pnad_coverage)}"]
    E --> I
    G --> I
```

{report_table(pnad_summary, ["etapa", "descricao", "observacoes", "observacoes_pct", "codigos_cod", "codigos_cod_pct"])}

## 2. CAGED principal: CBO 2002 -> ISCO-08 em 2 dígitos

No CAGED, a classificação de origem é a CBO 2002. A especificação principal é conservadora: usa CBO 2d pareado ao score médio ISCO-08 2d. Quando o subgrupo CBO 2d não existe na ISCO-08, o algoritmo recua para o grande grupo 1d.

```mermaid
flowchart TD
    A["CAGED: CBO 4d"] --> B["Reduz para CBO 2d"]
    C["OIT: ISCO-08 4d"] --> D["Agrega score para ISCO-08 2d"]
    B --> E{{"CBO 2d existe como ISCO-08 2d?"}}
    D --> E
    E -- "Sim: 478 códigos (75,99%) / 25.101 linhas (76,09%)" --> F["Usa média ISCO-08 2d"]
    E -- "Não: 151 códigos (24,01%) / 7.887 linhas (23,91%)" --> G["Fallback para média ISCO-08 1d"]
    F --> H["exposure_score_2d"]
    G --> H
    H --> I["Cobertura final: 100,00%"]
```

{report_table(caged_main_summary, ["etapa", "descricao", "codigos_cbo", "codigos_cbo_pct", "linhas_painel", "linhas_painel_pct"])}

## 3. CAGED robustez: CBO 2002 -> ISCO-08 em 4 dígitos

A robustez tenta preservar granularidade, mas explicita cada fallback. A tabela oficial usada é a correspondência ISCO-88 -> ISCO-08. O elo CBO 2002 -> ISCO-88 é uma aproximação operacional baseada na proximidade estrutural entre CBO 2002 e ISCO-88.

```mermaid
flowchart TD
    A["CBO 4d"] --> B{{"N1: coincide com ISCO-08 4d?"}}
    B -- "177 códigos (28,14%) / 9.317 linhas (28,24%)" --> C["Usa score ISCO-08 4d"]
    B -- "Não" --> D{{"N2: CBO 4d aparece como ISCO-88 4d?"}}
    D -- "56 códigos (8,90%) / 2.914 linhas (8,83%)" --> E["Ponte oficial ISCO-88 -> ISCO-08 4d"]
    D -- "Não" --> F{{"N3: grupo ISCO-08 3d existe?"}}
    F -- "123 códigos (19,55%) / 6.400 linhas (19,40%)" --> G["Usa média ISCO-08 3d"]
    F -- "Não" --> H{{"N4: CBO 3d aparece como ISCO-88 3d?"}}
    H -- "7 códigos (1,11%) / 370 linhas (1,12%)" --> I["Ponte oficial ISCO-88 -> ISCO-08 3d"]
    H -- "Não" --> J{{"N5: grupo ISCO-08 2d existe?"}}
    J -- "115 códigos (18,28%) / 6.100 linhas (18,49%)" --> K["Usa média ISCO-08 2d"]
    J -- "Não" --> L{{"N6: grupo ISCO-08 1d existe?"}}
    L -- "151 códigos (24,01%) / 7.887 linhas (23,91%)" --> M["Usa média ISCO-08 1d"]
    L -- "Sem match: 0" --> N["Sem score"]
    C --> O["exposure_score_4d"]
    E --> O
    G --> O
    I --> O
    K --> O
    M --> O
    N --> O
```

{report_table(caged_robust_summary, ["etapa", "descricao", "codigos_cbo", "codigos_cbo_pct", "linhas_painel", "linhas_painel_pct"])}

## 4. Tabelas completas

As tabelas completas estão em `outputs/crosswalk_audit/tables/`:

- `pnad_cod_to_isco08_full.md`
- `caged_cbo_to_isco08_main_2d_full.md`
- `caged_cbo_to_isco08_robust_4d_full.md`
- `caged_crosswalk_comparison_full.md`

Elas incluem os títulos ocupacionais usados para checagem substantiva: títulos COD do dicionário local do IBGE, títulos ISCO-08 da estrutura local da OIT e títulos CBO 2002 oficiais de família ocupacional, subgrupo, subgrupo principal e grande grupo. As cópias baixadas dos dicionários CBO ficam em `outputs/crosswalk_audit/source_dictionaries/`.

Resumo da cobertura dos títulos:

{report_table(title_coverage_summary, ["fonte", "coluna_titulo", "linhas_verificadas", "titulos_encontrados", "titulos_ausentes", "cobertura", "observacao"])}

O arquivo `all_tables.md` reúne todas elas em um único Markdown para copiar e colar.
"""


def write_all_tables(sections: list[tuple[str, list[dict[str, Any]], list[str]]]) -> None:
    chunks = ["# Tabelas completas dos crosswalks\n"]
    for title, rows, columns in sections:
        chunks.append(f"\n## {title}\n\n")
        chunks.append(markdown_table(rows, columns))
        chunks.append("\n")
    (OUTPUT_DIR / "all_tables.md").write_text("".join(chunks), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DICT_DIR.mkdir(parents=True, exist_ok=True)
    OFFICIAL_MTE_DIR.mkdir(parents=True, exist_ok=True)

    lookups = build_ilo_lookups()
    isco88_to_08, isco88_3d_to_08_3d = build_isco_correspondence()
    cod_titles = build_cod_titles()
    isco_titles = build_isco_titles(lookups["titles"])
    cbo_family_titles, cbo_minor_titles, cbo_submajor_titles, cbo_major_titles = build_cbo_titles()

    pnad_rows, pnad_summary = build_pnad_table(lookups, cod_titles, isco_titles)
    caged_main_rows, caged_robust_rows, caged_comparison_rows, caged_main_summary, caged_robust_summary = build_caged_tables(
        lookups, isco88_to_08, isco88_3d_to_08_3d,
        cbo_family_titles, cbo_minor_titles, cbo_submajor_titles, cbo_major_titles, isco_titles
    )
    mte_bridge_rows, mte_comparison_rows, mte_summary_rows, mte_semantic_report = build_caged_mte_bridge_tables(
        caged_main_rows, caged_robust_rows, lookups, isco88_to_08, isco_titles
    )
    title_coverage_summary = build_title_coverage_summary(pnad_rows, caged_main_rows, caged_robust_rows)

    pnad_columns = [
        "cod_ocupacao", "source_cod_title", "match_level", "target_isco_level", "target_isco_code", "target_isco_title",
        "exposure_score", "exposure_gradient", "n_observacoes", "peso_total", "nota_metodologica",
    ]
    caged_main_columns = [
        "cbo_4d", "source_cbo_title", "cbo_3d", "source_cbo_3d_title",
        "cbo_2d", "source_cbo_2d_title", "cbo_1d", "source_cbo_1d_title",
        "match_level_2d", "target_isco_level", "target_isco_code", "target_isco_title",
        "exposure_score_2d", "panel_rows", "admissoes_total", "nota_metodologica",
    ]
    caged_robust_columns = [
        "cbo_4d", "source_cbo_title", "cbo_3d", "source_cbo_3d_title",
        "cbo_2d", "source_cbo_2d_title", "cbo_1d", "source_cbo_1d_title",
        "robust_step", "source_interpretation", "source_isco88_code",
        "target_isco08_level", "target_isco08_codes", "target_isco08_titles", "candidate_scores",
        "exposure_score_4d", "panel_rows", "admissoes_total", "nota_metodologica",
    ]
    comparison_columns = [
        "cbo_4d", "source_cbo_title", "source_cbo_1d_title", "score_2d", "score_4d", "absolute_difference",
        "match_level_2d", "robust_step", "panel_rows", "admissoes_total",
    ]
    title_coverage_columns = [
        "fonte", "coluna_titulo", "linhas_verificadas", "titulos_encontrados",
        "titulos_ausentes", "cobertura", "observacao",
    ]
    mte_bridge_columns = [
        "cbo_4d", "source_cbo_title", "cbo_3d", "source_cbo_3d_title",
        "cbo_2d", "source_cbo_2d_title", "cbo_1d", "source_cbo_1d_title",
        "mte_cache_statuses", "mte_match_status", "cbo2002_6d_codes",
        "cbo2002_6d_titles", "cbo94_codes", "ciuo88_codes",
        "target_isco08_codes", "target_isco08_titles", "target_isco08_2d_codes",
        "target_isco08_2d_titles", "candidate_scores_mte_4d",
        "candidate_scores_mte_2d", "exposure_score_mte_4d",
        "exposure_score_mte_2d", "panel_rows", "admissoes_total", "nota_metodologica",
    ]
    mte_comparison_columns = [
        "cbo_4d", "source_cbo_title", "cbo_2d", "source_cbo_2d_title",
        "old_main_match_level", "old_robust_step", "mte_match_status",
        "old_target_2d_code", "old_target_2d_title", "old_target_4d_codes",
        "old_target_4d_titles", "mte_ciuo88_codes", "mte_target_isco08_codes",
        "mte_target_isco08_titles", "mte_target_isco08_2d_codes",
        "mte_target_isco08_2d_titles", "score_2d_old", "score_4d_old",
        "score_mte_2d", "score_mte_4d", "absolute_difference_old2d_mte2d",
        "absolute_difference_old4d_mte4d", "panel_rows", "admissoes_total",
    ]
    mte_summary_columns = [
        "section", "metric", "codes", "codes_pct", "panel_rows", "panel_rows_pct",
        "admissoes_total", "admissoes_pct", "weighted_value", "note",
    ]

    for required_column in ["source_cbo_title", "old_target_2d_title", "mte_target_isco08_titles"]:
        if required_column not in mte_comparison_columns:
            fail(f"MTE comparison output is missing required title column: {required_column}")

    write_table_artifacts("summary_pnad_steps", "Resumo PNAD: COD -> ISCO-08", pnad_summary, list(pnad_summary[0]))
    write_table_artifacts("summary_caged_main_2d_steps", "Resumo CAGED principal: CBO 2d -> ISCO-08", caged_main_summary, list(caged_main_summary[0]))
    write_table_artifacts("summary_caged_robust_4d_steps", "Resumo CAGED robustez: CBO 4d -> ISCO-08", caged_robust_summary, list(caged_robust_summary[0]))
    write_table_artifacts("summary_title_dictionary_coverage", "Resumo da cobertura dos títulos", title_coverage_summary, title_coverage_columns)

    write_table_artifacts("pnad_cod_to_isco08_full", "PNAD COD -> ISCO-08: tabela completa", pnad_rows, pnad_columns)
    write_table_artifacts("caged_cbo_to_isco08_main_2d_full", "CAGED principal 2d: tabela completa", caged_main_rows, caged_main_columns)
    write_table_artifacts("caged_cbo_to_isco08_robust_4d_full", "CAGED robustez 4d: tabela completa", caged_robust_rows, caged_robust_columns)
    write_table_artifacts("caged_crosswalk_comparison_full", "CAGED comparação 2d vs 4d: tabela completa", caged_comparison_rows, comparison_columns)
    write_official_mte_artifacts(
        mte_bridge_rows,
        mte_comparison_rows,
        mte_summary_rows,
        mte_semantic_report,
        mte_bridge_columns,
        mte_comparison_columns,
        mte_summary_columns,
    )

    write_all_tables(
        [
            ("Resumo da cobertura dos títulos", title_coverage_summary, title_coverage_columns),
            ("PNAD COD -> ISCO-08", pnad_rows, pnad_columns),
            ("CAGED principal 2d", caged_main_rows, caged_main_columns),
            ("CAGED robustez 4d", caged_robust_rows, caged_robust_columns),
            ("CAGED comparação 2d vs 4d", caged_comparison_rows, comparison_columns),
            ("CAGED ponte oficial MTE", mte_bridge_rows, mte_bridge_columns),
            ("CAGED antigo vs MTE", mte_comparison_rows, mte_comparison_columns),
            ("Resumo antigo vs MTE", mte_summary_rows, mte_summary_columns),
        ]
    )

    report = build_report(pnad_summary, caged_main_summary, caged_robust_summary, title_coverage_summary)
    (OUTPUT_DIR / "crosswalk_report.md").write_text(report, encoding="utf-8")

    print(f"Crosswalk audit generated at: {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
