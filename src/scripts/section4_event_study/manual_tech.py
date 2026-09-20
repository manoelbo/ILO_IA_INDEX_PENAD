"""Manual technology/programming CBO classification helpers."""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd


NARROW_TECH_PATTERNS = {
    "information_technology": r"\btecnologia da informacao\b|\bti\b",
    "software": r"\bsoftware\b",
    "systems_development": r"\bdesenvolvimento de sistemas\b|\bsistemas e aplicacoes\b|\baplicacoes?\b",
    "computing": r"\bcomputacao\b|\bcomputadores?\b|\binformatica\b",
    "programming": r"\bprogramadores?\b|\bprogramacao\b|\bdesenvolvedores?\b",
    "data_operations": r"\bentrada e transmissao de dados\b",
    "it_support": r"\bsuporte e monitoracao\b|\bmonitoracao ao usuario de tecnologia da informacao\b",
}

BROAD_ONLY_TECH_PATTERNS = {
    "telecommunications": r"\btelecomunicacoes?\b|\bteleprocessamento\b|\bcomunicacao de dados\b",
    "digital_networks": r"\brede\b|\bcabos eletricos, telefonicos e de comunicacao de dados\b",
    "technology_rd": r"\bpesquisa e desenvolvimento\b|\bengenharia e tecnologia\b|\bbiotecnologia\b",
}

SEMANTIC_EXCLUSION_PATTERNS = {
    "production_planning_not_software": r"\bprogramadores? e controladores de producao\b|\bproducao e manutencao\b",
    "teaching_not_software": r"\borientadores de ensino\b|\bprofessores? .*informatica\b|\bensino\b",
    "logistics_not_software": r"\blogistic",
    "mechanical_or_security_systems_not_software": (
        r"\bmaquinas, sistemas e instrumentos\b|"
        r"\bsistemas e estruturas de aeronaves\b|"
        r"\bsistemas eletroeletronicos de seguranca\b"
    ),
}

TITLE_COLUMNS = ["source_cbo_title", "source_cbo_2d_title", "source_cbo_3d_title", "cbo_title", "cbo_2d_title"]


def normalize_text(value: object) -> str:
    text = "" if value is None or pd.isna(value) else str(value).lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _match_patterns(text: str, patterns: dict[str, str]) -> list[str]:
    return [name for name, pattern in patterns.items() if re.search(pattern, text)]


def classify_manual_tech_cbo(classification: pd.DataFrame) -> pd.DataFrame:
    """Classify CBOs into narrow and broad manual tech groups from titles only.

    The narrow group is intended to capture software, programming, IT analysis,
    IT administration, systems development, data-entry/transmission, and IT
    support. The broad group adds adjacent digital infrastructure and
    technology R&D titles. Semantic exclusions override keyword hits.
    """
    out = classification.copy()
    title_cols = [col for col in TITLE_COLUMNS if col in out.columns]
    if not title_cols:
        raise RuntimeError("Manual tech classification requires at least one CBO title column.")
    out["manual_tech_text"] = out[title_cols].fillna("").agg(" ".join, axis=1).map(normalize_text)
    out["manual_tech_narrow_matches"] = out["manual_tech_text"].map(lambda text: _match_patterns(text, NARROW_TECH_PATTERNS))
    out["manual_tech_broad_matches"] = out["manual_tech_text"].map(lambda text: _match_patterns(text, BROAD_ONLY_TECH_PATTERNS))
    out["manual_tech_exclusion_matches"] = out["manual_tech_text"].map(
        lambda text: _match_patterns(text, SEMANTIC_EXCLUSION_PATTERNS)
    )
    has_keyword = out["manual_tech_narrow_matches"].map(bool) | out["manual_tech_broad_matches"].map(bool)
    has_exclusion = out["manual_tech_exclusion_matches"].map(bool) & has_keyword
    narrow_matches = out["manual_tech_narrow_matches"].map(set)
    broad_matches = out["manual_tech_broad_matches"].map(set)
    rd_only_development = narrow_matches.eq({"programming"}) & broad_matches.map(lambda matches: "technology_rd" in matches)
    has_narrow = out["manual_tech_narrow_matches"].map(bool) & ~has_exclusion & ~rd_only_development
    has_broad_only = out["manual_tech_broad_matches"].map(bool) & ~has_exclusion
    out["manual_tech_narrow"] = has_narrow
    out["manual_tech_broad"] = has_narrow | has_broad_only
    out["manual_tech_tier"] = np.select(
        [out["manual_tech_narrow"], out["manual_tech_broad"], has_exclusion],
        ["narrow", "broad_only", "excluded_keyword_false_positive"],
        default="not_manual_tech",
    )
    out["manual_tech_keywords"] = out.apply(
        lambda row: "; ".join(row["manual_tech_narrow_matches"] + row["manual_tech_broad_matches"]),
        axis=1,
    )
    out["manual_tech_exclusion_reason"] = out["manual_tech_exclusion_matches"].map(
        lambda matches: "; ".join([f"semantic_exclusion:{match}" for match in matches])
    )
    out["manual_tech_rule"] = np.select(
        [
            out["manual_tech_narrow"],
            out["manual_tech_broad"],
            has_exclusion,
        ],
        [
            "narrow: software/programming/IT keyword in CBO title",
            "broad: adjacent digital infrastructure/R&D keyword in CBO title",
            "excluded: keyword is not software/programming in context",
        ],
        default="not selected by manual tech keywords",
    )
    for col in ["manual_tech_narrow_matches", "manual_tech_broad_matches", "manual_tech_exclusion_matches"]:
        out[col] = out[col].map(lambda values: "; ".join(values))
    return out


def build_manual_tech_roles(classification: pd.DataFrame, tier: str) -> pd.DataFrame:
    if tier not in {"narrow", "broad"}:
        raise ValueError("tier must be 'narrow' or 'broad'.")
    classified = classify_manual_tech_cbo(classification)
    flag = "manual_tech_narrow" if tier == "narrow" else "manual_tech_broad"
    matched = classified["mte_match_status"].eq("matched_official_mte")
    control = matched & classified["cbo_ilo_gradient"].eq("Not Exposed") & ~classified[flag]
    treated = matched & classified[flag]
    roles = classified[
        [
            "cbo_4d",
            "mte_match_status",
            "cbo_ilo_gradient",
            "manual_tech_narrow",
            "manual_tech_broad",
            "manual_tech_tier",
            "manual_tech_keywords",
            "manual_tech_rule",
            "manual_tech_exclusion_reason",
        ]
    ].copy()
    roles["scenario_id"] = f"manual_tech_{tier}_vs_not_exposed"
    roles["scenario_role"] = np.select([treated, control], ["treated", "control"], default="excluded")
    roles["scenario_treat"] = roles["scenario_role"].eq("treated").astype(int)
    return roles
