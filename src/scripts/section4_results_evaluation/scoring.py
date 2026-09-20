"""Scoring and selection logic for Section 4 result candidates."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd


def stars_from_p(p_value: object) -> str:
    if p_value is None or pd.isna(p_value):
        return ""
    p = float(p_value)
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def is_log_outcome(outcome: object, outcome_label: object) -> bool:
    text = f"{outcome or ''} {outcome_label or ''}".lower()
    return str(outcome or "").startswith("ln_") or "(log" in text or " log" in text


def is_asinh_net_flow(outcome: object, outcome_label: object) -> bool:
    text = f"{outcome or ''} {outcome_label or ''}".lower()
    return "asinh" in text and ("saldo" in text or "net flow" in text or "fluxo líquido" in text)


def effect_percent(coef: object, outcome: object, outcome_label: object) -> float:
    if coef is None or pd.isna(coef):
        return np.nan
    if is_asinh_net_flow(outcome, outcome_label):
        return np.nan
    value = float(coef)
    if is_log_outcome(outcome, outcome_label):
        return (math.exp(value) - 1.0) * 100.0
    return value


def classify_channels(outcome: object, outcome_label: object, source_family: str, model_family: str = "") -> set[str]:
    text = f"{outcome or ''} {outcome_label or ''} {source_family or ''} {model_family or ''}".lower()
    channels: set[str] = set()
    if "connectivity" in source_family:
        channels.add("spatial_connectivity")
    if "manual_occupation" in source_family or "manual_tech" in source_family:
        channels.add("occupational_mechanism")
    if any(token in text for token in ["heterogeneity", "canaries", "cohort", "perfil", "jovem", "mulher", "idade", "renda", "raça", "race", "school", "education"]):
        channels.add("composition_or_heterogeneity")
    if any(token in text for token in ["admissoes", "admissões", "admissao", "admissão"]):
        channels.add("admission_flow")
    if any(token in text for token in ["deslig", "demiss", "separation"]):
        channels.add("separation_flow")
    if any(token in text for token in ["saldo", "net flow", "fluxo líquido", "fluxo liquido"]):
        channels.add("net_flow")
    if any(token in text for token in ["salario_real_adm", "salario_adm", "salário real de admissão", "salário de admissão", "wage adm"]):
        channels.add("entry_wage")
    if any(token in text for token in ["salario_real_desl", "salario_desl", "salário real de demissão", "salário de demissão", "wage desl"]):
        channels.add("exit_wage")
    if "quadruple" in model_family.lower() or "quadruple" in source_family.lower():
        channels.add("composition_or_heterogeneity")
    if not channels:
        channels.add("other_market_reconfiguration")
    return channels


def primary_channel(channels: Iterable[str]) -> str:
    priority = [
        "spatial_connectivity",
        "occupational_mechanism",
        "composition_or_heterogeneity",
        "net_flow",
        "entry_wage",
        "exit_wage",
        "admission_flow",
        "separation_flow",
        "other_market_reconfiguration",
    ]
    channel_set = set(channels)
    for channel in priority:
        if channel in channel_set:
            return channel
    return "other_market_reconfiguration"


def classify_causal_tier(pretrend_status: object, exploratory_only: object, p_value: object, source_family: str) -> str:
    pretrend = str(pretrend_status or "not_available").lower()
    exploratory = bool(exploratory_only)
    p = float(p_value) if p_value is not None and not pd.isna(p_value) else np.nan
    if exploratory:
        return "exploratory"
    if source_family.startswith("legacy"):
        return "benchmark_only"
    if pretrend == "fail":
        return "suggestive_pretrend_limit" if pd.notna(p) and p < 0.10 else "null_or_pretrend_limit"
    if pd.isna(p):
        return "not_classified"
    if p < 0.05 and pretrend in {"pass", "warning"}:
        return "causal_headline"
    if p < 0.05 and pretrend in {"not_available", "nan"}:
        return "suggestive_no_pretrend_test"
    if p < 0.10:
        return "suggestive"
    return "null_context"


def narrative_role(causal_tier: str, channels: set[str], source_family: str, p_value: object, pretrend_status: object) -> str:
    p = float(p_value) if p_value is not None and not pd.isna(p_value) else np.nan
    pretrend = str(pretrend_status or "not_available").lower()
    if causal_tier == "exploratory":
        return "exploratory_mechanism"
    if pretrend == "fail":
        return "limitation_or_suggestive"
    if "spatial_connectivity" in channels:
        return "connectivity_mechanism"
    if "occupational_mechanism" in channels:
        return "occupational_mechanism"
    if "composition_or_heterogeneity" in channels:
        return "heterogeneity"
    if "net_flow" in channels:
        return "net_flow"
    if pd.notna(p) and p >= 0.10:
        return "null_result"
    if source_family == "final_model":
        return "headline"
    return "robustness"


def placement_for(causal_tier: str, role: str, channels: set[str], source_family: str, exploratory_only: bool) -> str:
    if exploratory_only or causal_tier == "exploratory":
        return "apêndice"
    if role == "limitation_or_suggestive":
        return "limitação"
    if "spatial_connectivity" in channels:
        return "conectividade"
    if "occupational_mechanism" in channels:
        return "ocupações"
    if "composition_or_heterogeneity" in channels:
        return "heterogeneidade"
    if "net_flow" in channels:
        return "robustez"
    if source_family == "final_model" and causal_tier == "causal_headline":
        return "texto principal"
    if source_family == "final_model":
        return "robustez"
    if causal_tier == "benchmark_only":
        return "apêndice"
    return "robustez"


def score_candidate(row: pd.Series) -> dict[str, object]:
    source_family = str(row.get("source_family", "unknown"))
    model_family = str(row.get("model_family", ""))
    outcome = row.get("outcome", "")
    outcome_label = row.get("outcome_label", "")
    pretrend_status = row.get("pretrend_status", "not_available")
    p_value = row.get("p_value", np.nan)
    coef = row.get("coef", np.nan)
    exploratory_only = bool(row.get("exploratory_only", False))
    channels = classify_channels(outcome, outcome_label, source_family, model_family)
    if "entry_wage" in channels or "exit_wage" in channels:
        channels.add("wage_any")
    causal_tier = classify_causal_tier(pretrend_status, exploratory_only, p_value, source_family)
    role = narrative_role(causal_tier, channels, source_family, p_value, pretrend_status)
    placement = placement_for(causal_tier, role, channels, source_family, exploratory_only)
    pct = effect_percent(coef, outcome, outcome_label)
    score = 0.0
    p = float(p_value) if p_value is not None and not pd.isna(p_value) else np.nan
    if pd.notna(p):
        if p < 0.01:
            score += 22
        elif p < 0.05:
            score += 18
        elif p < 0.10:
            score += 14
        elif p < 0.20:
            score += 6
        else:
            score += 2
    pretrend = str(pretrend_status or "not_available").lower()
    score += {"pass": 24, "warning": 16, "not_available": 12, "nan": 12, "fail": 2}.get(pretrend, 10)
    magnitude = abs(float(pct)) if pd.notna(pct) else abs(float(coef)) if pd.notna(coef) else 0.0
    score += min(magnitude * 1.3, 16)
    n_obs = row.get("n_obs", np.nan)
    n_clusters = row.get("n_clusters", row.get("n_cbo", np.nan))
    if pd.notna(n_obs):
        score += min(math.log10(float(n_obs) + 1) * 2.0, 8)
    if pd.notna(n_clusters):
        clusters = float(n_clusters)
        if clusters >= 100:
            score += 8
        elif clusters >= 50:
            score += 6
        elif clusters >= 20:
            score += 3
    source_bonus = {
        "final_model": 14,
        "connectivity_extension": 12,
        "manual_occupation_groups": 12,
        "manual_tech_benchmark": 5,
        "legacy_event_profiles": 4,
        "legacy_event_study": 3,
        "legacy_section4": 3,
    }.get(source_family, 2)
    score += source_bonus
    if "composition_or_heterogeneity" in channels:
        score += 5
    if "spatial_connectivity" in channels or "occupational_mechanism" in channels:
        score += 4
    if causal_tier in {"null_context", "null_or_pretrend_limit"}:
        score += 6
    if exploratory_only:
        score -= 18
    if source_family.startswith("legacy"):
        score -= 8
    if "main_results_3plus1.csv" in str(row.get("source_file", "")):
        score -= 5
    power_status = str(row.get("power_status", "not_available")).lower()
    if power_status == "adequate":
        score += 3
    elif power_status == "limited":
        score -= 5
    elif power_status == "thin":
        score -= 12
    subgroup_label = str(row.get("subgroup_label", "")).lower()
    group_label = str(row.get("group_label", "")).lower()
    if "não informada" in subgroup_label or "nao informada" in subgroup_label:
        score -= 22
    if "não informada" in group_label or "nao informada" in group_label:
        score -= 22
    if subgroup_label in {"indígena", "indigena"}:
        score -= 8
    if subgroup_label in {"amarela"}:
        score -= 4
    flags = []
    if pretrend == "fail":
        flags.append("pretrend_fail")
    if exploratory_only:
        flags.append("exploratory")
    if source_family.startswith("legacy"):
        flags.append("legacy_or_benchmark")
    if pd.notna(p) and p >= 0.10:
        flags.append("not_statistically_significant")
    return {
        "effect_percent": pct,
        "market_reconfiguration_channel": primary_channel(channels - {"wage_any"} if len(channels) > 1 else channels),
        "channel_tags": "|".join(sorted(channels)),
        "causal_tier": causal_tier,
        "narrative_role": role,
        "placement": placement,
        "deterministic_score": min(max(score, 0.0), 100.0),
        "flags": "|".join(flags),
    }


def _dedup_key(row: pd.Series) -> str:
    parts = [
        str(row.get("source_family", "")),
        str(row.get("model_family", "")),
        str(row.get("spec_id", "")),
        str(row.get("group_label", "")),
        str(row.get("subgroup_label", "")),
        str(row.get("outcome", "")),
        str(row.get("market_reconfiguration_channel", "")),
    ]
    return "|".join(parts)


def _tag_count(df: pd.DataFrame, tag: str) -> int:
    return int(df["channel_tags"].fillna("").str.contains(tag, regex=False).sum())


def _source_count(rows: list[pd.Series], source_family: str) -> int:
    return sum(1 for row in rows if row.get("source_family") == source_family)


def _concept_key(row: pd.Series) -> str:
    source = str(row.get("source_family", ""))
    model = str(row.get("model_family", ""))
    outcome = str(row.get("outcome", ""))
    outcome_label = str(row.get("outcome_label", ""))
    subgroup = str(row.get("subgroup_label", "")).lower()
    source_file = str(row.get("source_file", ""))
    if "main_connectivity_triple_did.csv" in source_file:
        return "main_connectivity_triple_did"
    if source == "connectivity_extension" and ("adm_age" in outcome or "admissoes_jovem" in outcome):
        return "connectivity_age_admissions"
    if source == "connectivity_extension" and ("sal_real_age" in outcome or "salario_real_jovem" in outcome):
        return "connectivity_age_wages"
    if source == "connectivity_extension" and ("mulher" in outcome or "negro" in outcome):
        return "connectivity_demographic_profile"
    if source == "final_model" and "heterogeneity" in model and "deslig" in outcome_label.lower():
        return "final_heterogeneity_separations"
    if source == "manual_occupation_groups" and subgroup in {"parda", "branca", "preta", "amarela", "indígena", "indigena"}:
        return "manual_occupation_race_profiles"
    return f"{source}|{model}|{outcome_label}"


def _concept_count(rows: list[pd.Series], concept_key: str) -> int:
    return sum(1 for row in rows if _concept_key(row) == concept_key)


def _can_add_concept(rows: list[pd.Series], row: pd.Series, enforce_caps: bool = True) -> bool:
    if not enforce_caps:
        return True
    caps = {
        "connectivity_age_admissions": 2,
        "connectivity_age_wages": 2,
        "connectivity_demographic_profile": 3,
        "final_heterogeneity_separations": 5,
        "manual_occupation_race_profiles": 3,
    }
    key = _concept_key(row)
    cap = caps.get(key)
    if cap is None:
        return True
    return _concept_count(rows, key) < cap


def _can_add_source(rows: list[pd.Series], source_family: str, top_n: int, enforce_caps: bool = True) -> bool:
    if not enforce_caps:
        return True
    caps = {
        "manual_occupation_groups": 10,
        "connectivity_extension": 8,
        "final_model": 14,
        "manual_tech_benchmark": 3,
        "legacy_event_profiles": 2,
        "legacy_event_study": 2,
        "legacy_section4": 2,
    }
    cap = caps.get(source_family)
    if cap is None:
        return True
    if _source_count(rows, source_family) < cap:
        return True
    return len(rows) >= top_n


def _append_first_available(
    selected_rows: list[pd.Series],
    selected_keys: set[str],
    pool: pd.DataFrame,
    top_n: int,
    enforce_caps: bool = True,
) -> bool:
    for _, row in pool.iterrows():
        if row["selection_key"] in selected_keys:
            continue
        if not _can_add_source(selected_rows, row.get("source_family"), top_n, enforce_caps=enforce_caps):
            continue
        if not _can_add_concept(selected_rows, row, enforce_caps=enforce_caps):
            continue
        selected_keys.add(row["selection_key"])
        selected_rows.append(row)
        return True
    return False


def select_top_results(candidates: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    data = candidates.copy()
    data["selection_key"] = data.apply(_dedup_key, axis=1)
    data = data.sort_values(["deterministic_score", "p_value"], ascending=[False, True], na_position="last")
    data = data.drop_duplicates("selection_key", keep="first")
    data.loc[data["exploratory_only"].astype(bool) & data["placement"].eq("texto principal"), "placement"] = "apêndice"

    selected_keys: set[str] = set()
    selected_rows: list[pd.Series] = []

    must_include = data[
        (
            data["source_family"].eq("final_model")
            & data["source_file"].astype(str).str.contains("real_wage_main_results_3plus1.csv", regex=False)
        )
        | data["source_file"].astype(str).str.contains("main_connectivity_triple_did.csv", regex=False)
        | (
            data["source_file"].astype(str).str.contains("occupation_group_main_results.csv", regex=False)
            & data["spec_id"].astype(str).eq("software_it_core")
        )
    ]
    for _, row in must_include.iterrows():
        if row["selection_key"] not in selected_keys and len(selected_rows) < top_n:
            selected_keys.add(row["selection_key"])
            selected_rows.append(row)

    source_minimums = {
        "final_model": 8,
        "connectivity_extension": 5,
        "manual_occupation_groups": 7,
    }
    for source_family, minimum in source_minimums.items():
        while _source_count(selected_rows, source_family) < minimum and len(selected_rows) < top_n:
            pool = data[data["source_family"].eq(source_family) & ~data["selection_key"].isin(selected_keys)]
            if pool.empty:
                break
            if not _append_first_available(selected_rows, selected_keys, pool, top_n, enforce_caps=True):
                break

    quota_tags = {
        "admission_flow": 4,
        "separation_flow": 4,
        "net_flow": 2,
        "wage_any": 6,
        "composition_or_heterogeneity": 5,
        "spatial_connectivity": 3,
        "occupational_mechanism": 3,
    }
    for tag, minimum in quota_tags.items():
        while _tag_count(pd.DataFrame(selected_rows), tag) < minimum if selected_rows else True:
            current_count = _tag_count(pd.DataFrame(selected_rows), tag) if selected_rows else 0
            if current_count >= minimum:
                break
            pool = data[
                data["channel_tags"].fillna("").str.contains(tag, regex=False)
                & ~data["selection_key"].isin(selected_keys)
            ]
            if pool.empty or len(selected_rows) >= top_n:
                break
            if not _append_first_available(selected_rows, selected_keys, pool, top_n, enforce_caps=True):
                if not _append_first_available(selected_rows, selected_keys, pool, top_n, enforce_caps=False):
                    break

    limitation_pool = data[
        data["narrative_role"].isin(["limitation_or_suggestive", "null_result"])
        & ~data["selection_key"].isin(selected_keys)
    ]
    while len(selected_rows) < min(top_n, 30) and len([r for r in selected_rows if r.get("narrative_role") in {"limitation_or_suggestive", "null_result"}]) < 3 and not limitation_pool.empty:
        added = _append_first_available(selected_rows, selected_keys, limitation_pool, top_n, enforce_caps=True)
        if not added:
            added = _append_first_available(selected_rows, selected_keys, limitation_pool, top_n, enforce_caps=False)
        if not added:
            break
        limitation_pool = limitation_pool[~limitation_pool["selection_key"].isin(selected_keys)]

    for _, row in data.iterrows():
        if len(selected_rows) >= top_n:
            break
        if row["selection_key"] in selected_keys:
            continue
        if not _can_add_source(selected_rows, row.get("source_family"), top_n, enforce_caps=True):
            continue
        if not _can_add_concept(selected_rows, row, enforce_caps=True):
            continue
        selected_keys.add(row["selection_key"])
        selected_rows.append(row)

    if len(selected_rows) < top_n:
        for _, row in data.iterrows():
            if len(selected_rows) >= top_n:
                break
            if row["selection_key"] in selected_keys:
                continue
            selected_keys.add(row["selection_key"])
            selected_rows.append(row)

    out = pd.DataFrame(selected_rows).copy()
    out = out.sort_values(["deterministic_score", "p_value"], ascending=[False, True], na_position="last").head(top_n)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out.drop(columns=["selection_key"], errors="ignore")
