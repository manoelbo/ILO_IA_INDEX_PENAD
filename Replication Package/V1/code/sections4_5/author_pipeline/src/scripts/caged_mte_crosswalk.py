#!/usr/bin/env python3
"""
Official MTE bridge for CAGED CBO 2002 exposure scores.

The bridge is intentionally conservative:
  CBO 2002 -> MTE CBO2002-CBO94-CIUO88 -> ISCO-88 -> ISCO-08 -> ILO score

It does not use numeric equality between CBO and ISCO as a fallback. Families
without an official MTE bridge remain unmatched.
"""

from __future__ import annotations

import csv
import html as html_lib
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


CROSSWALK_SPEC = "mte_official_no_numeric_fallback"
MTE_BRIDGE_URL = "https://cbo.mte.gov.br/cbosite/pages/tabua/FiltroConversao_CBO2002_CBO94_CIUO88.jsf"


def normalize_code(value: Any, width: int) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(width)


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


def read_ilo_lookups(ilo_file: Path) -> dict[str, dict[str, float]]:
    if not ilo_file.exists():
        raise FileNotFoundError(f"ILO exposure file not found: {ilo_file}")

    df_ilo = pd.read_csv(ilo_file)
    code_col = "isco_08_str" if "isco_08_str" in df_ilo.columns else "isco_08"
    df_ilo["isco_08_str"] = df_ilo[code_col].map(lambda value: normalize_code(value, 4))
    df_ilo["exposure_score"] = pd.to_numeric(df_ilo["exposure_score"], errors="coerce")
    df_ilo = df_ilo.dropna(subset=["exposure_score"])

    ilo_4d = df_ilo.groupby("isco_08_str")["exposure_score"].mean().to_dict()

    def grouped(prefix_len: int) -> dict[str, float]:
        grouped_scores: dict[str, list[float]] = defaultdict(list)
        for code, score in ilo_4d.items():
            grouped_scores[code[:prefix_len]].append(float(score))
        return {code: float(np.mean(scores)) for code, scores in grouped_scores.items()}

    return {
        "ilo_4d": {code: float(score) for code, score in ilo_4d.items()},
        "ilo_2d": grouped(2),
    }


def read_isco88_to_isco08(isco_file: Path) -> dict[str, list[str]]:
    if not isco_file.exists():
        raise FileNotFoundError(f"ISCO-88 to ISCO-08 correspondence file not found: {isco_file}")

    df = pd.read_excel(isco_file, sheet_name="ISCO-08 to 88")
    required = {"ISCO-08 code", "ISCO-88 code"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns in ISCO correspondence: {missing}")

    df["isco08_4d"] = df["ISCO-08 code"].map(lambda value: normalize_code(value, 4))
    df["isco88_4d"] = df["ISCO-88 code"].map(lambda value: normalize_code(value, 4))
    df = df[(df["isco08_4d"] != "") & (df["isco88_4d"] != "")]
    return df.groupby("isco88_4d")["isco08_4d"].apply(lambda values: unique_preserve(list(values))).to_dict()


class MTEBridgeClient:
    """Small JSF client for the official MTE CBO2002-CBO94-CIUO88 table."""

    def __init__(self, url: str = MTE_BRIDGE_URL) -> None:
        self.url = url
        cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        self.view_state = ""
        self.dtpinfra_token = ""
        self.refresh_form_state()

    def refresh_form_state(self) -> None:
        request = urllib.request.Request(self.url, headers={"User-Agent": "Mozilla/5.0"})
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
            raise RuntimeError("Could not read JSF ViewState from MTE conversion page.")

    def query_family(self, cbo_4d: str) -> list[dict[str, str]]:
        payload = {
            "formSite038": "formSite038",
            "DTPINFRA_TOKEN": self.dtpinfra_token,
            "formSite038:j_idt83": cbo_4d,
            "formSite038:j_idt85": "Consultar",
            "javax.faces.ViewState": self.view_state,
        }
        request = urllib.request.Request(
            self.url,
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
        return [no_result_row(cbo_4d, "No MTE result table for this CBO 4d family.")]

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
        return [no_result_row(cbo_4d, "MTE result table had no parseable conversion rows.")]
    return rows


def no_result_row(cbo_4d: str, note: str) -> dict[str, str]:
    return {
        "source_cbo_4d": cbo_4d,
        "status": "no_result",
        "cbo2002_6d": "",
        "cbo2002_title": "",
        "cbo94_code": "",
        "ciuo88_code": "",
        "query_note": note,
    }


def read_bridge_cache(cache_path: Path) -> list[dict[str, str]]:
    if not cache_path.exists():
        return []
    with cache_path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_bridge_cache(cache_path: Path, rows: list[dict[str, str]]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "source_cbo_4d",
        "status",
        "cbo2002_6d",
        "cbo2002_title",
        "cbo94_code",
        "ciuo88_code",
        "query_note",
    ]
    with cache_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def build_mte_bridge_cache(cbo_codes: list[str], cache_path: Path) -> list[dict[str, str]]:
    cache_rows = read_bridge_cache(cache_path)
    cached_codes = {row.get("source_cbo_4d", "") for row in cache_rows}
    missing_codes = [code for code in sorted(cbo_codes) if code not in cached_codes]

    if missing_codes:
        try:
            client = MTEBridgeClient()
        except Exception as exc:
            raise RuntimeError(
                f"Could not consult the official MTE bridge and cache is incomplete. "
                f"Missing {len(missing_codes)} CBO families. Error: {exc}"
            ) from exc

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
                write_bridge_cache(cache_path, cache_rows)
        write_bridge_cache(cache_path, cache_rows)

    requested_rows = [row for row in cache_rows if row.get("source_cbo_4d") in set(cbo_codes)]
    query_errors = [row for row in requested_rows if row.get("status") == "query_error"]
    if query_errors:
        examples = ", ".join(row.get("source_cbo_4d", "") for row in query_errors[:10])
        raise RuntimeError(f"MTE bridge has query_error rows for requested CBO families: {examples}")

    cached_codes = {row.get("source_cbo_4d", "") for row in requested_rows}
    missing_after_cache = sorted(set(cbo_codes) - cached_codes)
    if missing_after_cache:
        raise RuntimeError(f"MTE bridge cache is missing CBO 4d families: {missing_after_cache[:10]}")

    return requested_rows


def score_from_distinct_targets(codes: list[str], lookup: dict[str, float]) -> float | None:
    scores = [lookup[code] for code in unique_preserve(codes) if code in lookup]
    if not scores:
        return None
    return float(np.mean(scores))


def build_mte_score_table(
    cbo_codes: list[str],
    ilo_file: Path,
    isco_file: Path,
    cache_path: Path,
) -> pd.DataFrame:
    lookups = read_ilo_lookups(ilo_file)
    isco88_to_08 = read_isco88_to_isco08(isco_file)
    cache_rows = build_mte_bridge_cache(cbo_codes, cache_path)

    cache_by_cbo: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in cache_rows:
        cache_by_cbo[row["source_cbo_4d"]].append(row)

    rows: list[dict[str, Any]] = []
    for cbo in sorted(cbo_codes):
        bridge_rows = cache_by_cbo.get(cbo, [])
        matched_rows = [
            row for row in bridge_rows
            if row.get("status") == "matched" and row.get("ciuo88_code")
        ]
        cache_statuses = unique_preserve([row.get("status", "") for row in bridge_rows])
        ciuo88_codes = unique_preserve([row["ciuo88_code"] for row in matched_rows])
        target_isco08_codes = unique_preserve(
            [isco08 for ciuo88 in ciuo88_codes for isco08 in isco88_to_08.get(ciuo88, [])]
        )
        target_isco08_2d_codes = unique_preserve([code[:2] for code in target_isco08_codes])

        score_mte_4d = score_from_distinct_targets(target_isco08_codes, lookups["ilo_4d"])
        score_mte_2d = score_from_distinct_targets(target_isco08_2d_codes, lookups["ilo_2d"])

        if score_mte_4d is not None and score_mte_2d is not None:
            status = "matched_official_mte"
        elif "query_error" in cache_statuses:
            status = "query_error"
        elif not matched_rows:
            status = "sem_match_mte_no_result"
        elif not target_isco08_codes:
            status = "sem_match_ciuo88_without_isco08"
        else:
            status = "sem_match_isco08_without_ilo_score"

        rows.append(
            {
                "cbo_4d": cbo,
                "mte_cache_statuses": ", ".join(cache_statuses),
                "mte_match_status": status,
                "mte_ciuo88_codes": ", ".join(ciuo88_codes),
                "mte_target_isco08_codes": ", ".join(target_isco08_codes),
                "mte_target_isco08_2d_codes": ", ".join(target_isco08_2d_codes),
                "mte_cbo2002_6d_codes": ", ".join(unique_preserve([row.get("cbo2002_6d", "") for row in matched_rows])),
                "mte_cbo94_codes": ", ".join(unique_preserve([row.get("cbo94_code", "") for row in matched_rows])),
                "exposure_score_mte_4d": score_mte_4d,
                "exposure_score_mte_2d": score_mte_2d,
            }
        )

    return pd.DataFrame(rows)


def apply_mte_crosswalk(
    painel: pd.DataFrame,
    ilo_file: Path,
    isco_file: Path,
    cache_path: Path,
    expected_matched_codes: int | None = None,
    expected_no_result_codes: int | None = None,
) -> pd.DataFrame:
    cbo_codes = sorted(painel["cbo_4d"].astype(str).unique())
    mte_scores = build_mte_score_table(cbo_codes, ilo_file, isco_file, cache_path)
    status_counts = mte_scores["mte_match_status"].value_counts().to_dict()

    if expected_matched_codes is not None:
        actual = int(status_counts.get("matched_official_mte", 0))
        if actual != expected_matched_codes:
            raise RuntimeError(
                f"Unexpected MTE matched CBO count: expected {expected_matched_codes}, got {actual}"
            )
    if expected_no_result_codes is not None:
        actual = int(status_counts.get("sem_match_mte_no_result", 0))
        if actual != expected_no_result_codes:
            raise RuntimeError(
                f"Unexpected MTE no-result CBO count: expected {expected_no_result_codes}, got {actual}"
            )

    out = painel.merge(mte_scores, on="cbo_4d", how="left")
    out["crosswalk_spec"] = CROSSWALK_SPEC
    out["exposure_score_2d"] = out["exposure_score_mte_2d"]
    out["exposure_score_4d"] = out["exposure_score_mte_4d"]
    out["exposure_score"] = out["exposure_score_2d"]
    out["match_level_2d"] = out["mte_match_status"]
    out["match_level_4d"] = out["mte_match_status"]
    return out
