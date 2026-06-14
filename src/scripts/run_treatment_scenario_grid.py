#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run a CBO/ISCO-ILO treatment scenario grid.

This script compares the current CAGED treatment definition with alternative
score- and gradient-based rules. It is intentionally self-contained so the
scenario audit can be reproduced without editing the main stage 2 or stage 3
pipelines.
"""

from __future__ import annotations

import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import pyfixest as pf


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)


ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_OUTPUT = ROOT / "data" / "output"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_DIR = ROOT / "outputs" / "treatment_scenario_grid"
CROSSWALK_AUDIT = ROOT / "outputs" / "crosswalk_audit" / "official_mte_bridge"
DISSERTATION_DIR = Path(
    "/Users/manebrasil/Library/Mobile Documents/com~apple~CloudDocs/Documents/Projects/"
    "Dissetação Mestrado/Minha Dissertação Até Agora"
)

ILO_FILE = DATA_PROCESSED / "ilo_exposure_clean.csv"
BRIDGE_FILE = CROSSWALK_AUDIT / "caged_mte_bridge_full.csv"
STAGE2_PANEL = DATA_OUTPUT / "painel_2b_ready.parquet"
STAGE3_PANEL = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
CURRENT_STAGE2_RESULTS = OUTPUT_TABLES / "did_main_results.csv"
CURRENT_STAGE3_RESULTS = OUTPUT_TABLES / "triple_did_main_etapa3b.csv"

EXPECTED_SPEC = "mte_official_no_numeric_fallback"
MATCHED_MTE_STATUS = "matched_official_mte"
BASELINE_TOLERANCE = 1e-6
UNDERPOWERED_TREATED_CBO = 20
UNDERPOWERED_TREATED_ADMISSIONS_SHARE = 0.05
ILO_HIGH_EXPOSURE_BOUNDARY = 0.50
ILO_GRADIENT_4_MEAN_CUTOFF = 0.60
ILO_GRADIENT_3_MEAN_CUTOFF = 0.50
ILO_GRADIENT_2_MEAN_CUTOFF = 0.40
ILO_MINIMAL_EXPOSURE_BOUNDARY = 0.40
STAGE2_CONTROL_COLUMNS = [
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
]
STAGE2_CONTROLS = " + ".join(STAGE2_CONTROL_COLUMNS)

STAGE2_OUTCOMES = {
    "ln_admissoes": "Log(Admissões)",
    "ln_desligamentos": "Log(Desligamentos)",
    "saldo": "Saldo Líquido",
    "ln_salario_adm": "Log(Salário Admissão)",
}

STAGE3_OUTCOMES = {
    "ln_salario_real_adm": "Log(Salário Real Admissão)",
    "ln_admissoes": "Log(Admissões)",
    "ln_desligamentos": "Log(Desligamentos)",
    "saldo": "Saldo Líquido",
    "pct_superior_adm": "% Superior (Admissão)",
    "idade_media_adm": "Idade Média Admissão",
    "ln_salario_mulher": "Log(Salário Mulheres)",
    "ln_salario_homem": "Log(Salário Homens)",
    "ln_salario_jovem": "Log(Salário Jovens)",
}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    label_pt: str
    treatment_pt: str
    control_pt: str
    family: str
    role_builder: Callable[[pd.DataFrame], pd.Series]


def fmt(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}".replace(".", ",")
    return str(value)


def pct(value: object, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{float(value) * 100:.{digits}f}%".replace(".", ",")


def stars(p_value: float | None) -> str:
    if p_value is None or math.isnan(p_value):
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def markdown_table(df: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    if df.empty:
        return "_Sem linhas._"
    view = df.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in view[columns].iterrows():
        values = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def split_codes(value: object, width: int = 4) -> list[str]:
    if pd.isna(value):
        return []
    codes = re.findall(r"\d+", str(value))
    if width:
        codes = [code.zfill(width) for code in codes]
    return sorted(set(codes))


def split_scores(value: object) -> list[float]:
    if pd.isna(value):
        return []
    scores = []
    for raw in re.findall(r"-?\d+(?:\.\d+)?", str(value)):
        try:
            scores.append(float(raw))
        except ValueError:
            continue
    return scores


def gradient_number(label: object) -> int:
    if pd.isna(label):
        return 0
    text = str(label)
    match = re.search(r"Gradient\s+([1-4])", text)
    return int(match.group(1)) if match else 0


def pooled_equal_weight_sd(scores: list[float], sds: list[float]) -> float:
    if not scores or len(scores) != len(sds):
        return np.nan
    mean_score = float(np.mean(scores))
    variances = [(sd**2) + ((score - mean_score) ** 2) for score, sd in zip(scores, sds)]
    return float(np.sqrt(np.mean(variances)))


def classify_ilo_mean_sd(mean_score: float, sd_score: float) -> str:
    if pd.isna(mean_score) or pd.isna(sd_score):
        return "No score"
    if mean_score >= ILO_GRADIENT_4_MEAN_CUTOFF and mean_score - sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 4"
    if ILO_GRADIENT_3_MEAN_CUTOFF <= mean_score < ILO_GRADIENT_4_MEAN_CUTOFF and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 3"
    if ILO_GRADIENT_2_MEAN_CUTOFF <= mean_score < ILO_GRADIENT_3_MEAN_CUTOFF and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 2"
    if mean_score < ILO_GRADIENT_2_MEAN_CUTOFF and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 1"
    if mean_score < ILO_HIGH_EXPOSURE_BOUNDARY and mean_score + sd_score > ILO_MINIMAL_EXPOSURE_BOUNDARY:
        return "Minimal Exposure"
    return "Not Exposed"


def compact_unique(values: list[object]) -> str:
    clean = [str(v) for v in values if v is not None and not pd.isna(v) and str(v) != ""]
    return "; ".join(sorted(set(clean)))


def ensure_inputs() -> None:
    required = [
        ILO_FILE,
        BRIDGE_FILE,
        STAGE2_PANEL,
        STAGE3_PANEL,
        CURRENT_STAGE2_RESULTS,
        CURRENT_STAGE3_RESULTS,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_inputs()
    ilo = pd.read_csv(ILO_FILE)
    bridge = pd.read_csv(BRIDGE_FILE)
    stage2 = pd.read_parquet(STAGE2_PANEL)
    stage3 = pd.read_parquet(STAGE3_PANEL)

    for name, df in [("Stage 2 panel", stage2), ("Stage 3 panel", stage3)]:
        validate_panel(df, name)
        df["cbo_4d"] = df["cbo_4d"].astype(str).str.zfill(4)

    bridge["cbo_4d"] = bridge["cbo_4d"].astype(str).str.zfill(4)
    ilo["isco_08_str"] = ilo["isco_08_str"].astype(str).str.zfill(4)
    return ilo, bridge, stage2, stage3


def validate_panel(df: pd.DataFrame, name: str) -> None:
    if "crosswalk_spec" not in df.columns:
        raise RuntimeError(f"{name} does not contain crosswalk_spec.")
    specs = set(df["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_SPEC}:
        raise RuntimeError(f"{name} must use {EXPECTED_SPEC}; found {sorted(specs)}.")
    if "exposure_score_2d" in df.columns and df["exposure_score_2d"].isna().any():
        raise RuntimeError(f"{name} contains missing exposure_score_2d values.")
    if name == "Stage 2 panel":
        missing = [col for col in STAGE2_CONTROL_COLUMNS if col not in df.columns]
        if missing:
            raise RuntimeError(f"{name} is missing required demographic controls: {missing}.")
        max_negra = pd.to_numeric(df["pct_negra_adm"], errors="coerce").max(skipna=True)
        if pd.isna(max_negra) or float(max_negra) == 0.0:
            raise RuntimeError(f"{name} has pct_negra_adm.max() == {max_negra}.")


def reduce_stage2(stage2: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "cbo_4d",
        "periodo",
        "post",
        "admissoes",
        "idade_media_adm",
        "pct_mulher_adm",
        "pct_superior_adm",
        "pct_negra_adm",
        "exposure_score_2d",
        "exposure_score_4d",
        "alta_exp",
        "alta_exp_4d",
        *STAGE2_OUTCOMES.keys(),
    ]
    return stage2[[c for c in cols if c in stage2.columns]].copy()


def reduce_stage3(stage3: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "cbo_4d",
        "id_municipio",
        "uf_periodo",
        "post",
        "alta_conectividade",
        "post_alta_conect",
        "admissoes",
        "exposure_score_2d",
        "exposure_score_4d",
        "alta_exp",
        "alta_exp_4d",
        *STAGE3_OUTCOMES.keys(),
    ]
    return stage3[[c for c in cols if c in stage3.columns]].copy()


def build_cbo_classification(
    ilo: pd.DataFrame,
    bridge: pd.DataFrame,
    stage2: pd.DataFrame,
    stage3: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    score_map = dict(zip(ilo["isco_08_str"], ilo["exposure_score"]))
    sd_map = dict(zip(ilo["isco_08_str"], pd.to_numeric(ilo["exposure_sd"], errors="coerce")))
    gradient_map = dict(zip(ilo["isco_08_str"], ilo["exposure_gradient"]))
    title_map = dict(zip(ilo["isco_08_str"], ilo["occupation_title"]))

    stage2_cbo = (
        stage2.groupby("cbo_4d")
        .agg(
            exposure_score_2d=("exposure_score_2d", "first"),
            exposure_score_4d=("exposure_score_4d", "first"),
            current_alta_exp=("alta_exp", "first"),
            current_alta_exp_4d=("alta_exp_4d", "first"),
            stage2_panel_rows=("cbo_4d", "size"),
            stage2_admissoes=("admissoes", "sum"),
        )
        .reset_index()
    )
    stage3_cbo = (
        stage3.groupby("cbo_4d")
        .agg(
            stage3_exposure_score_2d=("exposure_score_2d", "first"),
            stage3_exposure_score_4d=("exposure_score_4d", "first"),
            stage3_current_alta_exp=("alta_exp", "first"),
            stage3_current_alta_exp_4d=("alta_exp_4d", "first"),
            stage3_panel_rows=("cbo_4d", "size"),
            stage3_admissoes=("admissoes", "sum"),
        )
        .reset_index()
    )

    bridge_keep = [
        "cbo_4d",
        "source_cbo_title",
        "source_cbo_2d_title",
        "source_cbo_3d_title",
        "mte_match_status",
        "target_isco08_codes",
        "target_isco08_titles",
        "target_isco08_2d_codes",
        "target_isco08_2d_titles",
        "candidate_scores_mte_4d",
        "candidate_scores_mte_2d",
        "exposure_score_mte_4d",
        "exposure_score_mte_2d",
    ]
    out = bridge[bridge_keep].copy()
    out = out.merge(stage2_cbo, on="cbo_4d", how="left")
    out = out.merge(stage3_cbo, on="cbo_4d", how="left")
    out["stage2_panel_rows"] = out["stage2_panel_rows"].fillna(0).astype(int)
    out["stage2_admissoes"] = out["stage2_admissoes"].fillna(0)
    out["stage3_panel_rows"] = out["stage3_panel_rows"].fillna(0).astype(int)
    out["stage3_admissoes"] = out["stage3_admissoes"].fillna(0)

    if stage2["cbo_4d"].nunique() != stage2_cbo["cbo_4d"].nunique():
        raise RuntimeError("Stage 2 CBO aggregation changed the number of CBOs unexpectedly.")

    for col in [
        "exposure_score_2d",
        "exposure_score_4d",
        "stage3_exposure_score_2d",
        "stage3_exposure_score_4d",
        "exposure_score_mte_2d",
        "exposure_score_mte_4d",
        "current_alta_exp",
        "current_alta_exp_4d",
        "stage3_current_alta_exp",
        "stage3_current_alta_exp_4d",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out["exposure_score_2d"] = (
        out["exposure_score_2d"]
        .combine_first(out["stage3_exposure_score_2d"])
        .combine_first(out["exposure_score_mte_2d"])
    )
    out["exposure_score_4d"] = (
        out["exposure_score_4d"]
        .combine_first(out["stage3_exposure_score_4d"])
        .combine_first(out["exposure_score_mte_4d"])
    )
    out["current_alta_exp"] = out["current_alta_exp"].combine_first(out["stage3_current_alta_exp"])
    out["current_alta_exp_4d"] = out["current_alta_exp_4d"].combine_first(out["stage3_current_alta_exp_4d"])

    out["target_isco08_code_list"] = out["target_isco08_codes"].map(split_codes)
    out["scored_target_isco08_code_list"] = out["target_isco08_code_list"].map(
        lambda codes: [code for code in codes if code in score_map]
    )
    out["missing_score_target_isco08_code_list"] = out["target_isco08_code_list"].map(
        lambda codes: [code for code in codes if code not in score_map]
    )
    out["target_isco08_2d_code_list"] = out["target_isco08_2d_codes"].map(lambda v: split_codes(v, width=2))
    out["n_target_isco08_4d"] = out["target_isco08_code_list"].map(len)
    out["n_scored_target_isco08_4d"] = out["scored_target_isco08_code_list"].map(len)
    out["n_missing_score_target_isco08_4d"] = out["missing_score_target_isco08_code_list"].map(len)
    out["n_target_isco08_2d"] = out["target_isco08_2d_code_list"].map(len)
    out["target_scores_list"] = out["scored_target_isco08_code_list"].map(
        lambda codes: [score_map.get(code, np.nan) for code in codes]
    )
    out["target_sds_list"] = out["scored_target_isco08_code_list"].map(
        lambda codes: [sd_map.get(code, np.nan) for code in codes]
    )
    out["target_score_sd_pairs_list"] = out.apply(
        lambda row: [
            (float(score), float(sd))
            for score, sd in zip(row["target_scores_list"], row["target_sds_list"])
            if not pd.isna(score) and not pd.isna(sd)
        ],
        axis=1,
    )
    out["target_gradient_labels_list"] = out["scored_target_isco08_code_list"].map(
        lambda codes: [gradient_map.get(code, "") for code in codes]
    )
    out["target_gradient_numbers_list"] = out["target_gradient_labels_list"].map(
        lambda labels: [gradient_number(label) for label in labels]
    )
    out["target_isco08_titles_from_ilo"] = out["scored_target_isco08_code_list"].map(
        lambda codes: compact_unique([title_map.get(code, "") for code in codes])
    )
    out["target_scores"] = out["target_scores_list"].map(lambda scores: compact_unique([fmt(score, 6) for score in scores]))
    out["target_sds"] = out["target_sds_list"].map(lambda sds: compact_unique([fmt(sd, 6) for sd in sds]))
    out["target_gradients"] = out["target_gradient_labels_list"].map(compact_unique)
    out["min_target_score"] = out["target_scores_list"].map(lambda scores: np.nanmin(scores) if scores else np.nan)
    out["max_target_score"] = out["target_scores_list"].map(lambda scores: np.nanmax(scores) if scores else np.nan)
    out["mean_target_score"] = out["target_scores_list"].map(lambda scores: np.nanmean(scores) if scores else np.nan)
    out["isco08_mean_score"] = out["mean_target_score"]
    out["isco08_pooled_sd"] = out["target_score_sd_pairs_list"].map(
        lambda pairs: pooled_equal_weight_sd([score for score, _ in pairs], [sd for _, sd in pairs])
    )
    out["cbo_ilo_gradient"] = [
        classify_ilo_mean_sd(mean_score, pooled_sd)
        for mean_score, pooled_sd in zip(out["isco08_mean_score"], out["isco08_pooled_sd"])
    ]
    out["cbo_ilo_gradient_number"] = out["cbo_ilo_gradient"].map(gradient_number)
    out["trat_alta_expo"] = out["cbo_ilo_gradient_number"].isin({3, 4})
    out["trat_media_expo"] = out["cbo_ilo_gradient_number"].isin({1, 2})
    out["trat_expostos"] = out["cbo_ilo_gradient_number"].isin({1, 2, 3, 4})
    out["treatment_rule_source"] = np.where(
        out["target_score_sd_pairs_list"].map(len) > 0,
        "ilo_mean_sd_crosswalk",
        "no_scored_isco08",
    )
    out["has_missing_target_score"] = out["n_missing_score_target_isco08_4d"] > 0

    missing_audit = out[out["n_missing_score_target_isco08_4d"] > 0][
        [
            "cbo_4d",
            "source_cbo_title",
            "target_isco08_codes",
            "missing_score_target_isco08_code_list",
            "scored_target_isco08_code_list",
            "stage2_admissoes",
            "stage3_admissoes",
        ]
    ].copy()
    if not missing_audit.empty:
        missing_audit["missing_score_target_isco08_code_list"] = missing_audit[
            "missing_score_target_isco08_code_list"
        ].map(lambda values: "; ".join(values))
        missing_audit["scored_target_isco08_code_list"] = missing_audit[
            "scored_target_isco08_code_list"
        ].map(lambda values: "; ".join(values))
        missing_audit.to_csv(OUTPUT_DIR / "missing_isco08_score_audit.csv", index=False)

    bad_scores = out[
        out["mte_match_status"].eq(MATCHED_MTE_STATUS) & (out["n_scored_target_isco08_4d"] == 0)
    ]
    if not bad_scores.empty:
        bad = bad_scores[["cbo_4d", "source_cbo_title", "target_isco08_codes"]].head(20)
        raise RuntimeError("Some matched CBOs have no scored ISCO destination:\n" + bad.to_string(index=False))

    mte_valid = out["mte_match_status"].eq(MATCHED_MTE_STATUS) & out["exposure_score_mte_2d"].notna()
    thresholds = {
        "mte2d_top20_cutoff": float(stage2_cbo["exposure_score_2d"].quantile(0.80)),
        "n_stage2_cbo": float(stage2_cbo["cbo_4d"].nunique()),
        "n_stage3_cbo": float(stage3_cbo["cbo_4d"].nunique()),
        "n_bridge_cbo": float(out["cbo_4d"].nunique()),
        "n_mte_matched_cbo": float(out["mte_match_status"].eq(MATCHED_MTE_STATUS).sum()),
        "n_mte_unmatched_cbo": float((~out["mte_match_status"].eq(MATCHED_MTE_STATUS)).sum()),
        "n_trat_alta_expo": float(out["trat_alta_expo"].sum()),
        "n_trat_media_expo": float(out["trat_media_expo"].sum()),
        "n_trat_expostos": float(out["trat_expostos"].sum()),
    }
    out["mte2d_valid"] = mte_valid
    out["mte2d_top20_treatment"] = mte_valid & (out["exposure_score_mte_2d"] >= thresholds["mte2d_top20_cutoff"])
    current_mte_top20 = out["current_alta_exp"].eq(1)
    out["baseline_mte2d_top20_treatment"] = np.where(
        out["current_alta_exp"].notna(),
        current_mte_top20,
        out["mte2d_top20_treatment"],
    )
    out["baseline_mte2d_top20_treatment"] = out["baseline_mte2d_top20_treatment"] & mte_valid
    return out, thresholds


def all_scores_at_or_above(scores: list[float], cutoff: float) -> bool:
    return bool(scores) and all(score >= cutoff for score in scores)


def any_score_at_or_above(scores: list[float], cutoff: float) -> bool:
    return bool(scores) and any(score >= cutoff for score in scores)


def all_gradients_in(values: list[int], accepted: set[int]) -> bool:
    return bool(values) and all(v in accepted for v in values)


def any_gradient_in(values: list[int], accepted: set[int]) -> bool:
    return bool(values) and any(v in accepted for v in values)


def roles_from_treat_control(treat: pd.Series, control: pd.Series) -> pd.Series:
    return pd.Series(
        np.select([treat, control], ["treated", "control"], default="excluded"),
        index=treat.index,
    )


def scenario_specs(thresholds: dict[str, float]) -> list[Scenario]:
    return [
        Scenario(
            "baseline_mte2d_top20_vs_rest",
            "MTE 20% vs demais",
            "CBOs no top 20% do score MTE 2d, mantendo a definição principal atual.",
            "Todos os demais CBOs com score MTE 2d válido.",
            "score_mte_2d",
            lambda c: roles_from_treat_control(
                c["baseline_mte2d_top20_treatment"].astype(bool),
                c["mte2d_valid"].astype(bool) & ~c["baseline_mte2d_top20_treatment"].astype(bool),
            ),
        ),
        Scenario(
            "trat_alta_expo",
            "Trat. alta exposição OIT: Gradients 3-4 vs não expostos",
            "CBOs classificados como Exposed: Gradient 3 ou Exposed: Gradient 4 pela regra OIT média + SD agregada.",
            "CBOs classificados como Not Exposed pela regra OIT média + SD agregada.",
            "ilo_mean_sd_gradient",
            lambda c: roles_from_treat_control(
                c["trat_alta_expo"].astype(bool),
                c["cbo_ilo_gradient"].eq("Not Exposed"),
            ),
        ),
        Scenario(
            "trat_media_expo",
            "Trat. média exposição OIT: Gradients 1-2 vs não expostos",
            "CBOs classificados como Exposed: Gradient 1 ou Exposed: Gradient 2 pela regra OIT média + SD agregada.",
            "CBOs classificados como Not Exposed pela regra OIT média + SD agregada.",
            "ilo_mean_sd_gradient",
            lambda c: roles_from_treat_control(
                c["trat_media_expo"].astype(bool),
                c["cbo_ilo_gradient"].eq("Not Exposed"),
            ),
        ),
        Scenario(
            "trat_expostos",
            "Trat. expostos OIT: Gradients 1-4 vs não expostos",
            "CBOs classificados como Exposed: Gradient 1, 2, 3 ou 4 pela regra OIT média + SD agregada.",
            "CBOs classificados como Not Exposed pela regra OIT média + SD agregada.",
            "ilo_mean_sd_gradient",
            lambda c: roles_from_treat_control(
                c["trat_expostos"].astype(bool),
                c["cbo_ilo_gradient"].eq("Not Exposed"),
            ),
        ),
    ]


def add_scenario_roles(classification: pd.DataFrame, scenarios: list[Scenario]) -> pd.DataFrame:
    out = classification.copy()
    for scenario in scenarios:
        role = scenario.role_builder(out)
        out[f"role__{scenario.scenario_id}"] = role
        out[f"treated__{scenario.scenario_id}"] = (role == "treated").astype(int)
        out[f"included__{scenario.scenario_id}"] = role.isin(["treated", "control"]).astype(int)
    return out


def role_map(classification: pd.DataFrame, scenario_id: str) -> dict[str, str]:
    return dict(zip(classification["cbo_4d"], classification[f"role__{scenario_id}"]))


def apply_scenario(panel: pd.DataFrame, classification: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
    roles = role_map(classification, scenario.scenario_id)
    out = panel.copy()
    out["scenario_role"] = out["cbo_4d"].map(roles).fillna("excluded")
    out = out[out["scenario_role"].isin(["treated", "control"])].copy()
    out["scenario_treat"] = (out["scenario_role"] == "treated").astype(int)
    out["post_scenario_treat"] = out["post"].astype(int) * out["scenario_treat"]
    return out


def scenario_sample_stats(
    stage: str,
    panel: pd.DataFrame,
    classification: pd.DataFrame,
    scenario: Scenario,
) -> dict[str, object]:
    df = apply_scenario(panel, classification, scenario)
    total_rows = len(panel)
    total_admissions = float(panel["admissoes"].sum())
    total_cbo = int(panel["cbo_4d"].nunique())

    if df.empty:
        return {
            "stage": stage,
            "scenario_id": scenario.scenario_id,
            "scenario_label": scenario.label_pt,
            "scenario_family": scenario.family,
            "treatment_definition": scenario.treatment_pt,
            "control_definition": scenario.control_pt,
            "scenario_stage_status": "failed_empty_sample",
            "underpowered": True,
            "rows": 0,
            "rows_pct_of_current_mte": 0.0,
            "cbo": 0,
            "treated_cbo": 0,
            "control_cbo": 0,
            "excluded_cbo": total_cbo,
            "admissoes": 0.0,
            "admissoes_pct_of_current_mte": 0.0,
            "treated_admissoes": 0.0,
            "treated_admissoes_pct_of_current_mte": 0.0,
            "treated_admissoes_pct_of_included": np.nan,
            "mean_score_2d_treated": np.nan,
            "mean_score_2d_control": np.nan,
            "mean_score_4d_treated": np.nan,
            "mean_score_4d_control": np.nan,
        }

    cbo = (
        df.groupby("cbo_4d")
        .agg(
            scenario_treat=("scenario_treat", "first"),
            admissoes=("admissoes", "sum"),
            exposure_score_2d=("exposure_score_2d", "first"),
            exposure_score_4d=("exposure_score_4d", "first"),
        )
        .reset_index()
    )
    treated = cbo["scenario_treat"] == 1
    control = cbo["scenario_treat"] == 0
    treated_admissions = float(cbo.loc[treated, "admissoes"].sum())
    included_admissions = float(cbo["admissoes"].sum())
    treated_cbo = int(treated.sum())
    control_cbo = int(control.sum())
    underpowered = (
        treated_cbo < UNDERPOWERED_TREATED_CBO
        or (treated_admissions / total_admissions if total_admissions else 0.0)
        < UNDERPOWERED_TREATED_ADMISSIONS_SHARE
    )
    status = "failed_empty_sample"
    if treated_cbo > 0 and control_cbo > 0:
        status = "underpowered_but_estimated" if underpowered else "estimated"

    return {
        "stage": stage,
        "scenario_id": scenario.scenario_id,
        "scenario_label": scenario.label_pt,
        "scenario_family": scenario.family,
        "treatment_definition": scenario.treatment_pt,
        "control_definition": scenario.control_pt,
        "scenario_stage_status": status,
        "underpowered": underpowered,
        "rows": int(len(df)),
        "rows_pct_of_current_mte": float(len(df) / total_rows),
        "cbo": int(cbo["cbo_4d"].nunique()),
        "treated_cbo": treated_cbo,
        "control_cbo": control_cbo,
        "excluded_cbo": int(total_cbo - cbo["cbo_4d"].nunique()),
        "admissoes": included_admissions,
        "admissoes_pct_of_current_mte": float(included_admissions / total_admissions),
        "treated_admissoes": treated_admissions,
        "treated_admissoes_pct_of_current_mte": float(treated_admissions / total_admissions),
        "treated_admissoes_pct_of_included": float(treated_admissions / included_admissions)
        if included_admissions
        else np.nan,
        "mean_score_2d_treated": float(cbo.loc[treated, "exposure_score_2d"].mean()),
        "mean_score_2d_control": float(cbo.loc[control, "exposure_score_2d"].mean()),
        "mean_score_4d_treated": float(cbo.loc[treated, "exposure_score_4d"].mean()),
        "mean_score_4d_control": float(cbo.loc[control, "exposure_score_4d"].mean()),
    }


def failure_row(
    stage: str,
    scenario: Scenario,
    outcome: str,
    outcome_label: str,
    status: str,
    error: str,
    n_obs: int,
    n_cbo: int,
    n_municipios: int | None = None,
) -> dict[str, object]:
    row = {
        "stage": stage,
        "scenario_id": scenario.scenario_id,
        "scenario_label": scenario.label_pt,
        "scenario_family": scenario.family,
        "outcome": outcome,
        "outcome_label": outcome_label,
        "result_status": status,
        "coef": np.nan,
        "se": np.nan,
        "p_value": np.nan,
        "stars": "",
        "n_obs": n_obs,
        "n_cbo": n_cbo,
        "error": error,
    }
    if n_municipios is not None:
        row["n_municipios"] = n_municipios
    return row


def estimate_stage2(panel: pd.DataFrame, classification: pd.DataFrame, scenario: Scenario) -> list[dict[str, object]]:
    df = apply_scenario(panel, classification, scenario)
    rows: list[dict[str, object]] = []
    for outcome, label in STAGE2_OUTCOMES.items():
        d = df[df[outcome].notna()].copy() if outcome in df.columns else pd.DataFrame()
        n_obs = int(len(d))
        n_cbo = int(d["cbo_4d"].nunique()) if not d.empty else 0
        if d.empty or d["scenario_treat"].nunique() < 2:
            rows.append(
                failure_row(
                    "stage2_did",
                    scenario,
                    outcome,
                    label,
                    "failed_empty_sample",
                    "Empty sample or only one treatment group after applying scenario.",
                    n_obs,
                    n_cbo,
                )
            )
            continue
        formula = (
            f"{outcome} ~ post_scenario_treat + {STAGE2_CONTROLS} "
            f"| cbo_4d + periodo"
        )
        try:
            model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
            if "post_scenario_treat" not in model.coef().index:
                rows.append(
                    failure_row(
                        "stage2_did",
                        scenario,
                        outcome,
                        label,
                        "failed_collinearity",
                        "post_scenario_treat was dropped or not estimated.",
                        n_obs,
                        n_cbo,
                    )
                )
                continue
            p_value = float(model.pvalue().loc["post_scenario_treat"])
            rows.append(
                {
                    "stage": "stage2_did",
                    "scenario_id": scenario.scenario_id,
                    "scenario_label": scenario.label_pt,
                    "scenario_family": scenario.family,
                    "outcome": outcome,
                    "outcome_label": label,
                    "result_status": "estimated",
                    "coef": float(model.coef().loc["post_scenario_treat"]),
                    "se": float(model.se().loc["post_scenario_treat"]),
                    "p_value": p_value,
                    "stars": stars(p_value),
                    "n_obs": n_obs,
                    "n_cbo": n_cbo,
                    "error": "",
                }
            )
        except Exception as exc:  # noqa: BLE001 - record and continue across scenarios
            rows.append(
                failure_row(
                    "stage2_did",
                    scenario,
                    outcome,
                    label,
                    "failed_collinearity",
                    str(exc),
                    n_obs,
                    n_cbo,
                )
            )
    return rows


def estimate_stage3(panel: pd.DataFrame, classification: pd.DataFrame, scenario: Scenario) -> list[dict[str, object]]:
    df = apply_scenario(panel, classification, scenario)
    if not df.empty:
        df["post_scenario_exp"] = df["post"].astype(int) * df["scenario_treat"]
        df["scenario_exp_high_connect"] = df["scenario_treat"] * df["alta_conectividade"].astype(int)
        df["scenario_triple"] = (
            df["post"].astype(int) * df["scenario_treat"] * df["alta_conectividade"].astype(int)
        )

    rows: list[dict[str, object]] = []
    for outcome, label in STAGE3_OUTCOMES.items():
        d = df[df[outcome].notna()].copy() if outcome in df.columns else pd.DataFrame()
        n_obs = int(len(d))
        n_cbo = int(d["cbo_4d"].nunique()) if not d.empty else 0
        n_municipios = int(d["id_municipio"].nunique()) if not d.empty else 0
        if d.empty or d["scenario_treat"].nunique() < 2:
            rows.append(
                failure_row(
                    "stage3_triple_did",
                    scenario,
                    outcome,
                    label,
                    "failed_empty_sample",
                    "Empty sample or only one treatment group after applying scenario.",
                    n_obs,
                    n_cbo,
                    n_municipios,
                )
            )
            continue
        formula = (
            f"{outcome} ~ scenario_triple + post_scenario_exp + post_alta_conect + "
            f"scenario_exp_high_connect | cbo_4d + uf_periodo"
        )
        try:
            model = pf.feols(formula, data=d, vcov={"CRV1": "id_municipio"})
            if "scenario_triple" not in model.coef().index:
                rows.append(
                    failure_row(
                        "stage3_triple_did",
                        scenario,
                        outcome,
                        label,
                        "failed_collinearity",
                        "scenario_triple was dropped or not estimated.",
                        n_obs,
                        n_cbo,
                        n_municipios,
                    )
                )
                continue
            p_value = float(model.pvalue().loc["scenario_triple"])
            rows.append(
                {
                    "stage": "stage3_triple_did",
                    "scenario_id": scenario.scenario_id,
                    "scenario_label": scenario.label_pt,
                    "scenario_family": scenario.family,
                    "outcome": outcome,
                    "outcome_label": label,
                    "result_status": "estimated",
                    "coef": float(model.coef().loc["scenario_triple"]),
                    "se": float(model.se().loc["scenario_triple"]),
                    "p_value": p_value,
                    "stars": stars(p_value),
                    "n_obs": n_obs,
                    "n_cbo": n_cbo,
                    "n_municipios": n_municipios,
                    "error": "",
                }
            )
        except Exception as exc:  # noqa: BLE001 - record and continue across scenarios
            rows.append(
                failure_row(
                    "stage3_triple_did",
                    scenario,
                    outcome,
                    label,
                    "failed_collinearity",
                    str(exc),
                    n_obs,
                    n_cbo,
                    n_municipios,
                )
            )
    return rows


def validate_baseline(stage2_results: pd.DataFrame, stage3_results: pd.DataFrame) -> dict[str, object]:
    current2 = pd.read_csv(CURRENT_STAGE2_RESULTS)
    current2 = current2[current2["model"] == "Model 3: FE + Controls (MAIN)"].copy()
    baseline2 = stage2_results[
        (stage2_results["scenario_id"] == "baseline_mte2d_top20_vs_rest")
        & (stage2_results["result_status"] == "estimated")
    ].copy()
    merged2 = baseline2.merge(current2, on="outcome", suffixes=("_grid", "_saved"))

    current3 = pd.read_csv(CURRENT_STAGE3_RESULTS)
    baseline3 = stage3_results[
        (stage3_results["scenario_id"] == "baseline_mte2d_top20_vs_rest")
        & (stage3_results["result_status"] == "estimated")
    ].copy()
    merged3 = baseline3.merge(current3, on="outcome", suffixes=("_grid", "_saved"))

    diagnostics: list[dict[str, object]] = []
    for stage, merged in [("stage2_did", merged2), ("stage3_triple_did", merged3)]:
        if merged.empty:
            raise RuntimeError(f"Baseline validation failed: no matching rows for {stage}.")
        for _, row in merged.iterrows():
            coef_diff = abs(float(row["coef_grid"]) - float(row["coef_saved"]))
            se_diff = abs(float(row["se_grid"]) - float(row["se_saved"]))
            p_diff = abs(float(row["p_value_grid"]) - float(row["p_value_saved"]))
            diagnostics.append(
                {
                    "stage": stage,
                    "outcome": row["outcome"],
                    "coef_diff": coef_diff,
                    "se_diff": se_diff,
                    "p_value_diff": p_diff,
                    "passed": coef_diff <= BASELINE_TOLERANCE
                    and se_diff <= BASELINE_TOLERANCE
                    and p_diff <= BASELINE_TOLERANCE,
                }
            )

    failed = [d for d in diagnostics if not d["passed"]]
    if failed:
        detail = pd.DataFrame(failed).to_string(index=False)
        raise RuntimeError(
            f"Baseline validation failed beyond tolerance {BASELINE_TOLERANCE}:\n{detail}"
        )
    pd.DataFrame(diagnostics).to_csv(OUTPUT_DIR / "baseline_validation.csv", index=False)
    return {
        "passed": True,
        "tolerance": BASELINE_TOLERANCE,
        "rows_checked": len(diagnostics),
        "max_coef_diff": max(d["coef_diff"] for d in diagnostics),
        "max_se_diff": max(d["se_diff"] for d in diagnostics),
        "max_p_value_diff": max(d["p_value_diff"] for d in diagnostics),
    }


def update_stage_statuses(
    sample: pd.DataFrame,
    stage2_results: pd.DataFrame,
    stage3_results: pd.DataFrame,
) -> pd.DataFrame:
    out = sample.copy()
    result_status = (
        pd.concat([stage2_results, stage3_results], ignore_index=True)
        .groupby(["stage", "scenario_id"])["result_status"]
        .apply(list)
        .reset_index()
    )

    def stage_status(row: pd.Series) -> str:
        statuses = row["result_status"]
        sample_row = out[(out["stage"] == row["stage"]) & (out["scenario_id"] == row["scenario_id"])].iloc[0]
        if any(status == "estimated" for status in statuses):
            return "underpowered_but_estimated" if bool(sample_row["underpowered"]) else "estimated"
        if any(status == "failed_collinearity" for status in statuses):
            return "failed_collinearity"
        return "failed_empty_sample"

    result_status["scenario_stage_status"] = result_status.apply(stage_status, axis=1)
    out = out.drop(columns=["scenario_stage_status"]).merge(
        result_status[["stage", "scenario_id", "scenario_stage_status"]],
        on=["stage", "scenario_id"],
        how="left",
    )

    overall = (
        out.groupby("scenario_id")["scenario_stage_status"]
        .apply(list)
        .reset_index(name="stage_statuses")
    )

    def overall_status(statuses: list[str]) -> str:
        if all(status == "failed_empty_sample" for status in statuses):
            return "failed_empty_sample"
        if all(status in {"failed_empty_sample", "failed_collinearity"} for status in statuses):
            return "failed_collinearity"
        if any(status == "underpowered_but_estimated" for status in statuses):
            return "underpowered_but_estimated"
        return "estimated"

    overall["scenario_status"] = overall["stage_statuses"].map(overall_status)
    out = out.merge(overall[["scenario_id", "scenario_status"]], on="scenario_id", how="left")
    return out


def add_display_columns(sample: pd.DataFrame) -> pd.DataFrame:
    out = sample.copy()
    for col in ["rows", "cbo", "treated_cbo", "control_cbo", "excluded_cbo"]:
        out[f"{col}_fmt"] = out[col].map(lambda v: fmt(int(v)))
    for col in ["admissoes", "treated_admissoes"]:
        out[f"{col}_fmt"] = out[col].map(lambda v: fmt(int(round(v))))
    for col in [
        "rows_pct_of_current_mte",
        "admissoes_pct_of_current_mte",
        "treated_admissoes_pct_of_current_mte",
        "treated_admissoes_pct_of_included",
    ]:
        out[f"{col}_fmt"] = out[col].map(pct)
    for col in [
        "mean_score_2d_treated",
        "mean_score_2d_control",
        "mean_score_4d_treated",
        "mean_score_4d_control",
    ]:
        out[f"{col}_fmt"] = out[col].map(lambda v: fmt(v, 3))
    return out


def add_result_display_columns(results: pd.DataFrame) -> pd.DataFrame:
    out = results.copy()
    out["coef_fmt"] = out["coef"].map(lambda v: fmt(v, 4))
    out["se_fmt"] = out["se"].map(lambda v: fmt(v, 4))
    out["p_value_fmt"] = out["p_value"].map(lambda v: fmt(v, 3))
    out["n_obs_fmt"] = out["n_obs"].map(lambda v: fmt(int(v)))
    out["n_cbo_fmt"] = out["n_cbo"].map(lambda v: fmt(int(v)))
    return out


def compare_against_baseline(results: pd.DataFrame, stage: str) -> pd.DataFrame:
    current = results[
        (results["stage"] == stage)
        & (results["scenario_id"] == "baseline_mte2d_top20_vs_rest")
        & (results["result_status"] == "estimated")
    ].copy()
    alternatives = results[
        (results["stage"] == stage)
        & (results["scenario_id"] != "baseline_mte2d_top20_vs_rest")
        & (results["result_status"] == "estimated")
    ].copy()
    if current.empty or alternatives.empty:
        return pd.DataFrame()
    merged = alternatives.merge(current, on=["stage", "outcome"], suffixes=("_alternative", "_baseline"))
    merged["delta_coef_vs_baseline"] = merged["coef_alternative"] - merged["coef_baseline"]
    merged["abs_delta_coef_vs_baseline"] = merged["delta_coef_vs_baseline"].abs()
    merged["sign_changed_vs_baseline"] = (
        np.sign(merged["coef_alternative"]) != np.sign(merged["coef_baseline"])
    )
    return merged


def duplicate_role_pairs(classification: pd.DataFrame, scenarios: list[Scenario]) -> pd.DataFrame:
    rows = []
    labels = {scenario.scenario_id: scenario.label_pt for scenario in scenarios}
    for i, left in enumerate(scenarios):
        left_col = f"role__{left.scenario_id}"
        for right in scenarios[i + 1 :]:
            right_col = f"role__{right.scenario_id}"
            if classification[left_col].equals(classification[right_col]):
                rows.append(
                    {
                        "scenario_a": left.scenario_id,
                        "scenario_a_label": labels[left.scenario_id],
                        "scenario_b": right.scenario_id,
                        "scenario_b_label": labels[right.scenario_id],
                    }
                )
    return pd.DataFrame(rows)


def dissertation_narrative_note() -> str:
    if not DISSERTATION_DIR.exists():
        return (
            "A pasta da dissertação não foi encontrada no caminho informado; "
            "a recomendação usa apenas os resultados atuais da grade."
        )
    html_files = sorted(DISSERTATION_DIR.glob("*.html"))
    if not html_files:
        return (
            "A pasta da dissertação foi encontrada, mas não havia HTML; "
            "a recomendação usa apenas os resultados atuais da grade."
        )
    text = html_files[0].read_text(encoding="utf-8", errors="ignore")
    headings = re.findall(r"<h[12][^>]*>(.*?)</h[12]>", text, flags=re.IGNORECASE | re.DOTALL)
    clean_headings = []
    for heading in headings:
        cleaned = re.sub(r"<[^>]+>", "", heading)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            clean_headings.append(cleaned)
    selected = [h for h in clean_headings if any(key in h.lower() for key in ["mensuração", "exposição", "empírica", "automação", "complementaridade"])]
    selected = selected[:8] or clean_headings[:8]
    return (
        "A leitura estrutural do HTML atual indica que a narrativa combina mensuração da exposição, "
        "distinção conceitual entre automação/complementaridade e uma seção empírica DiD. "
        "Os números do HTML foram ignorados conforme instrução do usuário. Cabeçalhos relevantes: "
        + "; ".join(selected)
        + "."
    )


def recommendation_from_results(sample: pd.DataFrame, stage2: pd.DataFrame, stage3: pd.DataFrame) -> dict[str, list[str]]:
    status = sample.groupby("scenario_id")["scenario_status"].first().to_dict()
    rec: dict[str, list[str]] = {
        "principal": ["baseline_mte2d_top20_vs_rest"],
        "decomposicao": [],
        "descartar_ou_apenas_mencionar": [],
    }
    for scenario in [
        "trat_alta_expo",
        "trat_media_expo",
        "trat_expostos",
    ]:
        if status.get(scenario) in {"estimated", "underpowered_but_estimated"}:
            rec["decomposicao"].append(scenario)
    for scenario in sample["scenario_id"].drop_duplicates():
        if status.get(scenario) in {"failed_empty_sample", "failed_collinearity"}:
            rec["descartar_ou_apenas_mencionar"].append(scenario)

    # Keep lists unique while preserving order.
    for key, values in rec.items():
        rec[key] = list(dict.fromkeys(values))
    return rec


def write_reports(
    thresholds: dict[str, float],
    classification: pd.DataFrame,
    sample: pd.DataFrame,
    stage2_results: pd.DataFrame,
    stage3_results: pd.DataFrame,
    baseline_validation: dict[str, object],
    scenarios: list[Scenario],
) -> None:
    scenario_labels = {s.scenario_id: s.label_pt for s in scenarios}
    sample_display = add_display_columns(sample)
    stage2_display = add_result_display_columns(stage2_results)
    stage3_display = add_result_display_columns(stage3_results)
    stage2_comp = compare_against_baseline(stage2_results, "stage2_did")
    stage3_comp = compare_against_baseline(stage3_results, "stage3_triple_did")
    duplicate_roles = duplicate_role_pairs(classification, scenarios)
    rec = recommendation_from_results(sample, stage2_results, stage3_results)
    narrative_note = dissertation_narrative_note()
    missing_score_cbo = int((classification["n_missing_score_target_isco08_4d"] > 0).sum())
    missing_score_admissions = float(
        classification.loc[
            classification["n_missing_score_target_isco08_4d"] > 0,
            "stage2_admissoes",
        ].sum()
    )

    summary_rows = (
        sample_display[sample_display["stage"] == "stage2_did"]
        .sort_values(["scenario_status", "scenario_id"])
        .copy()
    )

    stage2_main = stage2_display[
        (stage2_display["outcome"].isin(["ln_admissoes", "ln_salario_adm"]))
        & (stage2_display["result_status"] == "estimated")
    ].copy()
    stage3_main = stage3_display[
        (stage3_display["outcome"].isin(["ln_salario_real_adm", "ln_admissoes", "saldo"]))
        & (stage3_display["result_status"] == "estimated")
    ].copy()

    if not stage2_comp.empty:
        stage2_comp_display = stage2_comp.assign(
            scenario_label=stage2_comp["scenario_id_alternative"].map(scenario_labels),
            coef_baseline_fmt=stage2_comp["coef_baseline"].map(lambda v: fmt(v, 4)),
            coef_alternative_fmt=stage2_comp["coef_alternative"].map(lambda v: fmt(v, 4)),
            delta_fmt=stage2_comp["delta_coef_vs_baseline"].map(lambda v: fmt(v, 4)),
        )
    else:
        stage2_comp_display = pd.DataFrame()
    if not stage3_comp.empty:
        stage3_comp_display = stage3_comp.assign(
            scenario_label=stage3_comp["scenario_id_alternative"].map(scenario_labels),
            coef_baseline_fmt=stage3_comp["coef_baseline"].map(lambda v: fmt(v, 4)),
            coef_alternative_fmt=stage3_comp["coef_alternative"].map(lambda v: fmt(v, 4)),
            delta_fmt=stage3_comp["delta_coef_vs_baseline"].map(lambda v: fmt(v, 4)),
        )
    else:
        stage3_comp_display = pd.DataFrame()

    if duplicate_roles.empty:
        duplicate_text = "_Nenhum par de cenários teve classificação CBO idêntica._"
    else:
        duplicate_text = markdown_table(
            duplicate_roles,
            ["scenario_a", "scenario_a_label", "scenario_b", "scenario_b_label"],
        )

    thresholds_text = "\n".join(
        [
            f"- MTE 2d top 20%: score >= {fmt(thresholds['mte2d_top20_cutoff'], 6)}",
            f"- CBOs na ponte completa: {fmt(thresholds['n_bridge_cbo'], 0)}",
            f"- CBOs com MTE: {fmt(thresholds['n_mte_matched_cbo'], 0)}",
            f"- CBOs sem MTE: {fmt(thresholds['n_mte_unmatched_cbo'], 0)}",
            f"- Trat. alta exposição OIT: {fmt(thresholds['n_trat_alta_expo'], 0)} CBOs",
            f"- Trat. média exposição OIT: {fmt(thresholds['n_trat_media_expo'], 0)} CBOs",
            f"- Trat. expostos OIT: {fmt(thresholds['n_trat_expostos'], 0)} CBOs",
        ]
    )

    report = f"""# Grade De Cenários De Tratamento CBO/ISCO-OIT

## O Que Foi Feito

Este relatório compara a especificação principal MTE 20% com três recortes conceituais baseados na regra OIT de média e desvio-padrão agregados dos destinos ISCO-08. A fonte de exposição continua sendo a ponte oficial:

```text
CBO 4d -> MTE/CIUO88 -> ISCO-88 -> ISCO-08 4d -> score/gradiente OIT
```

Os outputs principais em `outputs/tables/` não foram sobrescritos. Todos os arquivos desta grade foram salvos em `outputs/treatment_scenario_grid/`.

## Validação Do Baseline

A especificação atual foi reestimada dentro deste script e comparada com os CSVs atuais.

- Linhas checadas: {baseline_validation['rows_checked']}
- Tolerância: {baseline_validation['tolerance']}
- Maior diferença em coeficiente: {fmt(baseline_validation['max_coef_diff'], 8)}
- Maior diferença em erro-padrão: {fmt(baseline_validation['max_se_diff'], 8)}
- Maior diferença em p-valor: {fmt(baseline_validation['max_p_value_diff'], 8)}

## Auditoria De Destinos ISCO Sem Score OIT

Foram encontrados {fmt(missing_score_cbo)} CBOs com pelo menos um destino ISCO-08 4d sem score no arquivo limpo da OIT, somando {fmt(int(round(missing_score_admissions)))} admissões na Etapa 2. CBOs sem crosswalk MTE permanecem na classificação como `No score`, mas ficam excluídos das estimações. Destinos sem score são salvos em `missing_isco08_score_audit.csv`.

## Cortes Calculados

{thresholds_text}

## Resumo Da Amostra Por Cenário

{markdown_table(sample_display, ["stage", "scenario_label", "scenario_status", "scenario_stage_status", "cbo_fmt", "treated_cbo_fmt", "control_cbo_fmt", "excluded_cbo_fmt", "admissoes_fmt", "admissoes_pct_of_current_mte_fmt", "treated_admissoes_pct_of_current_mte_fmt"], max_rows=40)}

## Cenários Redundantes

{duplicate_text}

Quando dois cenários têm classificação CBO idêntica, eles não devem ser interpretados como duas evidências independentes. A grade final usa apenas quatro recortes: MTE 20%, alta exposição OIT, média exposição OIT e expostos OIT.

## Etapa 2: DiD Ocupação-Mês

{markdown_table(stage2_main, ["scenario_label", "outcome_label", "result_status", "coef_fmt", "se_fmt", "p_value_fmt", "stars", "n_obs_fmt", "n_cbo_fmt"], max_rows=80)}

## Etapa 3: Triple-DiD Municipal

{markdown_table(stage3_main, ["scenario_label", "outcome_label", "result_status", "coef_fmt", "se_fmt", "p_value_fmt", "stars", "n_obs_fmt", "n_cbo_fmt"], max_rows=100)}

## Comparação Contra O Baseline

### Etapa 2

{markdown_table(stage2_comp_display, ["scenario_label", "outcome_label_alternative", "coef_baseline_fmt", "coef_alternative_fmt", "delta_fmt", "sign_changed_vs_baseline"], max_rows=80) if not stage2_comp_display.empty else "_Sem comparação disponível._"}

### Etapa 3

{markdown_table(stage3_comp_display, ["scenario_label", "outcome_label_alternative", "coef_baseline_fmt", "coef_alternative_fmt", "delta_fmt", "sign_changed_vs_baseline"], max_rows=100) if not stage3_comp_display.empty else "_Sem comparação disponível._"}

## Leitura Da Narrativa Da Dissertação

{narrative_note}

## Interpretação Curta

A grade confirma que existem duas perguntas diferentes. A primeira é a pergunta principal da dissertação: ocupações muito expostas pela medida OIT/MTE se comportam de forma diferente das demais depois do ChatGPT? Para essa pergunta, o baseline `baseline_mte2d_top20_vs_rest` continua sendo a definição mais simples e defensável.

A segunda pergunta é conceitual: os efeitos mudam quando o tratamento é definido por tipo de exposição OIT? Para isso, os cenários `trat_alta_expo`, `trat_media_expo` e `trat_expostos` usam o gradiente CBO agregado pela própria regra OIT. `Minimal Exposure`, `No score` e CBOs sem MTE ficam fora dessas comparações; o controle é apenas `Not Exposed`.
"""
    (OUTPUT_DIR / "scenario_comparison_report.md").write_text(report, encoding="utf-8")

    rec_text = f"""# Recomendação Para A Dissertação

## Recomendação Principal

Eu manteria `baseline_mte2d_top20_vs_rest` como especificação principal.

Motivo: ela é a regra mais alinhada com a narrativa atual da dissertação, preserva a maior amostra, usa a ponte MTE/OIT já auditada e evita escolher uma regra nova depois de olhar os resultados. O 2d continua funcionando como uma agregação conservadora do score imputado ao CBO, não como a unidade de tratamento.

## Decomposição Conceitual Recomendada

Usaria como decomposição conceitual:

{chr(10).join(f'- `{scenario}`: {scenario_labels.get(scenario, scenario)}' for scenario in rec['decomposicao']) or '- Nenhum cenário de decomposição foi estimado com amostra utilizável.'}

Esses cenários testam se os resultados mudam quando a exposição é separada pelo gradiente CBO agregado pela regra OIT de média + SD. O controle desses recortes é apenas `Not Exposed`; `Minimal Exposure`, `No score` e CBOs sem MTE ficam fora.

## Interpretação Dos Recortes OIT

Os recortes OIT não substituem automaticamente a especificação principal. Eles respondem a uma pergunta diferente: entre ocupações com classificação agregada de exposição pela OIT, os efeitos aparecem em alta exposição, média exposição ou em qualquer exposição?

## Cenários Fracos Ou Subdimensionados

Eu evitaria usar como evidência principal:

{chr(10).join(f'- `{scenario}`: {scenario_labels.get(scenario, scenario)}' for scenario in rec['descartar_ou_apenas_mencionar']) or '- Nenhum cenário caiu automaticamente nesta categoria.'}

Quando um cenário falhar ou ficar subdimensionado, ele não deve ser usado como evidência principal. A comparação mais defensável fica entre MTE 20% e os três recortes OIT estimados com amostra suficiente.

## Conclusão

O caminho mais interessante para a dissertação é uma hierarquia em dois níveis:

1. **Principal:** MTE 2d top 20% vs demais.
2. **Decomposição conceitual:** `trat_alta_expo`, `trat_media_expo` e `trat_expostos`, usando a regra OIT média + SD.

Essa hierarquia protege a dissertação de dois riscos: trocar a medida principal depois de ver os resultados e confundir exposição ocupacional com impacto causal direto. A medida principal continua respondendo à pergunta ampla de exposição; os gradientes entram depois, como leitura substantiva dos tipos de exposição.
"""
    (OUTPUT_DIR / "dissertation_recommendation.md").write_text(rec_text, encoding="utf-8")


def write_classification_csv(classification: pd.DataFrame) -> None:
    out = classification.copy()
    list_cols = [
        "target_isco08_code_list",
        "scored_target_isco08_code_list",
        "missing_score_target_isco08_code_list",
        "target_isco08_2d_code_list",
        "target_scores_list",
        "target_gradient_labels_list",
        "target_gradient_numbers_list",
    ]
    for col in list_cols:
        out[col] = out[col].map(lambda values: "; ".join(map(str, values)) if isinstance(values, list) else values)
    sort_cols = ["stage2_admissoes", "cbo_4d"]
    out.sort_values(sort_cols, ascending=[False, True]).to_csv(
        OUTPUT_DIR / "scenario_cbo_classification.csv",
        index=False,
    )


def main() -> None:
    ilo, bridge, stage2_raw, stage3_raw = load_inputs()
    stage2 = reduce_stage2(stage2_raw)
    stage3 = reduce_stage3(stage3_raw)
    print(f"Stage 2 panel: {len(stage2):,} rows | {stage2['cbo_4d'].nunique()} CBOs", flush=True)
    print(f"Stage 3 panel: {len(stage3):,} rows | {stage3['cbo_4d'].nunique()} CBOs", flush=True)

    classification, thresholds = build_cbo_classification(ilo, bridge, stage2, stage3)
    scenarios = scenario_specs(thresholds)
    classification = add_scenario_roles(classification, scenarios)
    write_classification_csv(classification)
    print(f"CBO classification written: {OUTPUT_DIR / 'scenario_cbo_classification.csv'}", flush=True)

    sample_rows = []
    for scenario in scenarios:
        sample_rows.append(scenario_sample_stats("stage2_did", stage2, classification, scenario))
        sample_rows.append(scenario_sample_stats("stage3_triple_did", stage3, classification, scenario))
    sample = pd.DataFrame(sample_rows)

    stage2_rows: list[dict[str, object]] = []
    stage3_rows: list[dict[str, object]] = []
    for scenario in scenarios:
        print(f"Estimating scenario: {scenario.scenario_id}", flush=True)
        stage2_rows.extend(estimate_stage2(stage2, classification, scenario))
        stage3_rows.extend(estimate_stage3(stage3, classification, scenario))

    stage2_results = pd.DataFrame(stage2_rows)
    stage3_results = pd.DataFrame(stage3_rows)
    baseline_validation = validate_baseline(stage2_results, stage3_results)
    sample = update_stage_statuses(sample, stage2_results, stage3_results)

    sample.to_csv(OUTPUT_DIR / "scenario_sample_summary.csv", index=False)
    stage2_results.to_csv(OUTPUT_DIR / "stage2_scenario_results.csv", index=False)
    stage3_results.to_csv(OUTPUT_DIR / "stage3_scenario_results.csv", index=False)

    write_reports(
        thresholds,
        classification,
        sample,
        stage2_results,
        stage3_results,
        baseline_validation,
        scenarios,
    )
    print(f"Scenario sample written: {OUTPUT_DIR / 'scenario_sample_summary.csv'}", flush=True)
    print(f"Stage 2 results written: {OUTPUT_DIR / 'stage2_scenario_results.csv'}", flush=True)
    print(f"Stage 3 results written: {OUTPUT_DIR / 'stage3_scenario_results.csv'}", flush=True)
    print(f"Reports written under: {OUTPUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
