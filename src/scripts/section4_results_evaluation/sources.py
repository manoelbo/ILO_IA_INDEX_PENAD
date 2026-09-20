"""Load and standardize generated Section 4 result files."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from section4_results_evaluation.config import ROOT, SECTION4_ROOT, SKIP_FILE_PATTERNS, SOURCE_DIRS
from section4_results_evaluation.scoring import score_candidate, stars_from_p


def infer_source_family(path: Path) -> str:
    text = path.as_posix()
    if "final_event_study" in text:
        return "final_model"
    if "connectivity_extension" in text:
        return "connectivity_extension"
    if "manual_occupation_groups_extension" in text:
        return "manual_occupation_groups"
    if "manual_tech_extension" in text:
        return "manual_tech_benchmark"
    if "event_study_profiles" in text:
        return "legacy_event_profiles"
    if "/event_study/" in text:
        return "legacy_event_study"
    if "/tables/" in text:
        return "legacy_section4"
    return "other"


def discover_result_files() -> list[Path]:
    files: list[Path] = []
    for directory in SOURCE_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.csv")):
            name = path.name.lower()
            if any(pattern in name for pattern in SKIP_FILE_PATTERNS):
                continue
            files.append(path)
    return files


def _as_bool(value: object) -> bool:
    if value is None or pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "sim"}


def _first_present(row: pd.Series, names: list[str], default: object = "") -> object:
    for name in names:
        if name in row.index and pd.notna(row[name]) and str(row[name]) != "":
            return row[name]
    return default


def _result_status(row: pd.Series) -> str:
    return str(row.get("result_status", "estimated") if pd.notna(row.get("result_status", "estimated")) else "estimated")


def _pretrend_alias(outcome: str) -> str:
    aliases = {
        "ln_salario_real_adm": "ln_salario_adm",
        "ln_salario_real_desl": "ln_salario_desl",
    }
    return aliases.get(outcome, outcome)


def load_pretrend_maps() -> dict[str, dict[tuple[str, ...], str]]:
    maps: dict[str, dict[tuple[str, ...], str]] = {}
    final_path = SECTION4_ROOT / "final_event_study" / "tables" / "event_study_pretrend_tests.csv"
    if final_path.exists():
        df = pd.read_csv(final_path)
        mapping = {}
        for row in df.itertuples(index=False):
            mapping[(str(row.outcome),)] = str(row.pretrend_status)
        maps["final_model"] = mapping
    connectivity_path = SECTION4_ROOT / "connectivity_extension" / "tables" / "connectivity_event_study_pretrends.csv"
    if connectivity_path.exists():
        df = pd.read_csv(connectivity_path)
        maps["connectivity_extension"] = {(str(r.outcome),): str(r.status) for r in df.itertuples(index=False)}
    occ_path = SECTION4_ROOT / "manual_occupation_groups_extension" / "tables" / "occupation_group_event_study_pretrends.csv"
    if occ_path.exists():
        df = pd.read_csv(occ_path)
        maps["manual_occupation_groups"] = {
            (str(r.group_id), str(r.outcome)): str(r.pretrend_status) for r in df.itertuples(index=False)
        }
    tech_path = SECTION4_ROOT / "manual_tech_extension" / "tables" / "manual_tech_event_study_pretrends.csv"
    if tech_path.exists():
        df = pd.read_csv(tech_path)
        maps["manual_tech_benchmark"] = {
            (str(r.manual_tech_tier), str(r.outcome)): str(r.pretrend_status) for r in df.itertuples(index=False)
        }
    return maps


def infer_pretrend_status(row: pd.Series, source_family: str, maps: dict[str, dict[tuple[str, ...], str]]) -> str:
    if "pretrend_status" in row.index and pd.notna(row["pretrend_status"]):
        return str(row["pretrend_status"])
    if "status" in row.index and pd.notna(row["status"]):
        return str(row["status"])
    outcome = str(row.get("outcome", ""))
    outcome_alias = _pretrend_alias(outcome)
    if source_family == "manual_occupation_groups":
        group_id = str(row.get("group_id", ""))
        return maps.get(source_family, {}).get((group_id, outcome), maps.get(source_family, {}).get((group_id, outcome_alias), "not_available"))
    if source_family == "manual_tech_benchmark":
        tier = str(row.get("manual_tech_tier", ""))
        return maps.get(source_family, {}).get((tier, outcome), maps.get(source_family, {}).get((tier, outcome_alias), "not_available"))
    return maps.get(source_family, {}).get((outcome,), maps.get(source_family, {}).get((outcome_alias,), "not_available"))


def standardize_row(path: Path, row_index: int, row: pd.Series, pretrend_maps: dict[str, dict[tuple[str, ...], str]]) -> dict[str, object] | None:
    if "coef" not in row.index or "p_value" not in row.index:
        return None
    coef = pd.to_numeric(row.get("coef"), errors="coerce")
    p_value = pd.to_numeric(row.get("p_value"), errors="coerce")
    se = pd.to_numeric(row.get("se"), errors="coerce") if "se" in row.index else np.nan
    if pd.isna(coef) or pd.isna(p_value):
        return None
    status = _result_status(row)
    if status != "estimated":
        return None
    source_family = infer_source_family(path)
    source_file = path.relative_to(ROOT).as_posix()
    outcome = str(row.get("outcome", ""))
    outcome_label = str(row.get("outcome_label", outcome))
    group_label = _first_present(
        row,
        ["occupation_group_label", "group_label", "spec_label", "scenario_label", "manual_tech_tier", "panel"],
        path.stem,
    )
    subgroup_label = _first_present(row, ["heterogeneity_group_label", "dimension_label", "comparison"], "")
    spec_id = _first_present(row, ["spec_id", "scenario_id", "manual_tech_tier", "group_id"], path.stem)
    model_family = path.stem
    exploratory = _as_bool(row.get("exploratory_only", False))
    if str(row.get("group_id", "")) == "clear_tech_no_mte":
        exploratory = True
    candidate = {
        "result_id": f"{path.stem}:{row_index}",
        "source_family": source_family,
        "source_file": source_file,
        "row_index": row_index,
        "model_family": model_family,
        "spec_id": str(spec_id),
        "group_label": str(group_label),
        "subgroup_label": str(subgroup_label),
        "outcome": outcome,
        "outcome_label": outcome_label,
        "coef": float(coef),
        "se": float(se) if pd.notna(se) else np.nan,
        "p_value": float(p_value),
        "stars": str(row.get("stars", "")) if pd.notna(row.get("stars", "")) else stars_from_p(p_value),
        "n_obs": pd.to_numeric(row.get("n_obs", np.nan), errors="coerce"),
        "n_cbo": pd.to_numeric(row.get("n_cbo", np.nan), errors="coerce"),
        "n_clusters": pd.to_numeric(row.get("n_clusters", row.get("n_cbo", np.nan)), errors="coerce"),
        "pretrend_status": infer_pretrend_status(row, source_family, pretrend_maps),
        "power_status": str(row.get("power_status", "not_available")) if pd.notna(row.get("power_status", "not_available")) else "not_available",
        "exploratory_only": exploratory,
        "result_status": status,
    }
    candidate.update(score_candidate(pd.Series(candidate)))
    return candidate


def load_candidate_universe() -> pd.DataFrame:
    pretrend_maps = load_pretrend_maps()
    rows: list[dict[str, object]] = []
    for path in discover_result_files():
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if "coef" not in df.columns or "p_value" not in df.columns:
            continue
        for row_index, row in df.iterrows():
            candidate = standardize_row(path, int(row_index), row, pretrend_maps)
            if candidate is not None:
                rows.append(candidate)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["result_id"] = [f"r{i + 1:04d}" for i in range(len(out))]
    return out
