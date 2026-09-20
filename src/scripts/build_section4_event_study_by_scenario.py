#!/usr/bin/env python3
"""Build Section 4 event studies by treatment contrast.

This script uses the previously generated treatment scenario grid as the
source of truth for CBO-to-ILO gradient assignments. It does not rebuild the
crosswalk or alter the legacy Stage 2b pipeline.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfixest as pf
from scipy.stats import chi2


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)


ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = ROOT / "data" / "output" / "painel_2b_ready.parquet"
SCENARIO_GRID_PATH = ROOT / "outputs" / "treatment_scenario_grid" / "scenario_cbo_classification.csv"
OUTPUT_DIR = ROOT / "outputs" / "dissertation_section4" / "event_study"

EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"
REFERENCE_PERIOD = -1
BIN_MIN = -12
BIN_MAX = 24
VCOV_SPEC = {"CRV1": "cbo_4d"}

OUTCOMES = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Desligamentos (log)",
    "saldo": "Saldo líquido",
    "ln_salario_adm": "Salário de admissão (log)",
}

CONTROL_COLUMNS = [
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
]
CONTROL_TERMS = " + ".join(CONTROL_COLUMNS)

VALID_GRADIENTS = {
    "Not Exposed",
    "Minimal Exposure",
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
    "No score",
}
EXPOSED_G1_G2 = {"Exposed: Gradient 1", "Exposed: Gradient 2"}
EXPOSED_G3_G4 = {"Exposed: Gradient 3", "Exposed: Gradient 4"}
EXPOSED_G1_G4 = EXPOSED_G1_G2 | EXPOSED_G3_G4


@dataclass(frozen=True)
class Contrast:
    scenario_id: str
    label_pt: str
    family: str
    control_type: str
    treatment_definition_pt: str
    control_definition_pt: str
    figure_name: str
    report_name: str
    treatment_gradients: tuple[str, ...] = ()
    control_gradients: tuple[str, ...] = ()
    role_column: str | None = None


CONTRASTS = [
    Contrast(
        scenario_id="baseline_mte2d_top20_vs_rest",
        label_pt="Baseline MTE top 20% vs demais CBOs válidos",
        family="baseline",
        control_type="baseline",
        treatment_definition_pt="CBOs no top 20% do score MTE 2d, usando a definição principal já gerada.",
        control_definition_pt="Demais CBOs com score MTE 2d válido na classificação baseline existente.",
        figure_name="event_study_baseline_mte2d_top20_vs_rest.png",
        report_name="report_baseline_mte2d_top20_vs_rest.md",
        role_column="role__baseline_mte2d_top20_vs_rest",
    ),
    Contrast(
        scenario_id="trat_alta_expo_strict_control",
        label_pt="Alta exposição OIT (G3-G4) vs controle estrito",
        family="trat_alta_expo",
        control_type="strict_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 3 ou Exposed: Gradient 4.",
        control_definition_pt="Controle estrito: CBOs classificados como Not Exposed.",
        figure_name="event_study_trat_alta_expo_strict_control.png",
        report_name="report_trat_alta_expo_strict_control.md",
        treatment_gradients=tuple(sorted(EXPOSED_G3_G4)),
        control_gradients=("Not Exposed",),
    ),
    Contrast(
        scenario_id="trat_alta_expo_broad_control",
        label_pt="Alta exposição OIT (G3-G4) vs controle amplo",
        family="trat_alta_expo",
        control_type="broad_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 3 ou Exposed: Gradient 4.",
        control_definition_pt="Controle amplo: CBOs classificados como Not Exposed ou Minimal Exposure.",
        figure_name="event_study_trat_alta_expo_broad_control.png",
        report_name="report_trat_alta_expo_broad_control.md",
        treatment_gradients=tuple(sorted(EXPOSED_G3_G4)),
        control_gradients=("Not Exposed", "Minimal Exposure"),
    ),
    Contrast(
        scenario_id="trat_media_expo_strict_control",
        label_pt="Média exposição OIT (G1-G2) vs controle estrito",
        family="trat_media_expo",
        control_type="strict_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1 ou Exposed: Gradient 2.",
        control_definition_pt="Controle estrito: CBOs classificados como Not Exposed.",
        figure_name="event_study_trat_media_expo_strict_control.png",
        report_name="report_trat_media_expo_strict_control.md",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G2)),
        control_gradients=("Not Exposed",),
    ),
    Contrast(
        scenario_id="trat_media_expo_broad_control",
        label_pt="Média exposição OIT (G1-G2) vs controle amplo",
        family="trat_media_expo",
        control_type="broad_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1 ou Exposed: Gradient 2.",
        control_definition_pt="Controle amplo: CBOs classificados como Not Exposed ou Minimal Exposure.",
        figure_name="event_study_trat_media_expo_broad_control.png",
        report_name="report_trat_media_expo_broad_control.md",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G2)),
        control_gradients=("Not Exposed", "Minimal Exposure"),
    ),
    Contrast(
        scenario_id="trat_expostos_strict_control",
        label_pt="Expostos OIT (G1-G4) vs controle estrito",
        family="trat_expostos",
        control_type="strict_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1, 2, 3 ou 4.",
        control_definition_pt="Controle estrito: CBOs classificados como Not Exposed.",
        figure_name="event_study_trat_expostos_strict_control.png",
        report_name="report_trat_expostos_strict_control.md",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G4)),
        control_gradients=("Not Exposed",),
    ),
    Contrast(
        scenario_id="trat_expostos_broad_control",
        label_pt="Expostos OIT (G1-G4) vs controle amplo",
        family="trat_expostos",
        control_type="broad_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1, 2, 3 ou 4.",
        control_definition_pt="Controle amplo: CBOs classificados como Not Exposed ou Minimal Exposure.",
        figure_name="event_study_trat_expostos_broad_control.png",
        report_name="report_trat_expostos_broad_control.md",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G4)),
        control_gradients=("Not Exposed", "Minimal Exposure"),
    ),
]

EVENT_TIMES = list(range(BIN_MIN, BIN_MAX + 1))


def log(message: str) -> None:
    print(message, flush=True)


def stars(p_value: float | None) -> str:
    if p_value is None or pd.isna(p_value):
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def fmt_number(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}".replace(".", ",")
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sem linhas disponíveis._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in df[columns].iterrows():
        values = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def event_dummy_name(t: int) -> str:
    return f"did_tm{-t}" if t < 0 else f"did_t{t}"


def required_files() -> list[Path]:
    return [PANEL_PATH, SCENARIO_GRID_PATH]


def ensure_inputs() -> None:
    missing = [str(path) for path in required_files() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def validate_panel(panel: pd.DataFrame) -> None:
    required = [
        "cbo_4d",
        "periodo",
        "tempo_relativo_meses",
        "crosswalk_spec",
        *OUTCOMES.keys(),
        *CONTROL_COLUMNS,
    ]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise RuntimeError(f"Stage 2b panel is missing required columns: {missing}")

    specs = set(panel["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_CROSSWALK_SPEC}:
        raise RuntimeError(f"Stage 2b panel must use {EXPECTED_CROSSWALK_SPEC}; found {sorted(specs)}.")

    for col in CONTROL_COLUMNS:
        values = pd.to_numeric(panel[col], errors="coerce")
        if values.notna().sum() == 0:
            raise RuntimeError(f"Control {col} has no numeric observations.")
    if pd.to_numeric(panel["pct_mulher_adm"], errors="coerce").max(skipna=True) == 0:
        raise RuntimeError("pct_mulher_adm.max() == 0; demographic recoding is not valid.")


def validate_classification(classification: pd.DataFrame) -> None:
    required = [
        "cbo_4d",
        "mte_match_status",
        "cbo_ilo_gradient",
        "role__baseline_mte2d_top20_vs_rest",
    ]
    missing = [col for col in required if col not in classification.columns]
    if missing:
        raise RuntimeError(f"Scenario grid is missing required columns: {missing}")

    observed = set(classification["cbo_ilo_gradient"].dropna().unique())
    required_observed = {"Not Exposed", "Minimal Exposure", "Exposed: Gradient 1", "Exposed: Gradient 2", "Exposed: Gradient 3"}
    missing_gradients = required_observed - observed
    if missing_gradients:
        raise RuntimeError(f"Scenario grid lacks required OIT gradient classes: {sorted(missing_gradients)}")
    unexpected_gradients = observed - VALID_GRADIENTS
    if unexpected_gradients:
        raise RuntimeError(f"Scenario grid has unexpected OIT gradient classes: {sorted(unexpected_gradients)}")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_inputs()
    panel = pd.read_parquet(PANEL_PATH)
    classification = pd.read_csv(SCENARIO_GRID_PATH, dtype={"cbo_4d": str})

    panel["cbo_4d"] = panel["cbo_4d"].astype(str).str.zfill(4)
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    panel["periodo"] = panel["periodo"].astype(str)
    panel["t_binned"] = pd.to_numeric(panel["tempo_relativo_meses"], errors="raise").clip(BIN_MIN, BIN_MAX).astype(int)

    validate_panel(panel)
    validate_classification(classification)
    return panel, classification


def roles_for_contrast(classification: pd.DataFrame, contrast: Contrast) -> pd.DataFrame:
    out = classification[["cbo_4d", "mte_match_status", "cbo_ilo_gradient"]].copy()
    if contrast.role_column:
        role = classification[contrast.role_column].fillna("excluded").astype(str)
    else:
        gradient = classification["cbo_ilo_gradient"].astype(str)
        treat = gradient.isin(contrast.treatment_gradients)
        control = gradient.isin(contrast.control_gradients)
        role = pd.Series(np.select([treat, control], ["treated", "control"], default="excluded"), index=classification.index)

    out["scenario_id"] = contrast.scenario_id
    out["scenario_label"] = contrast.label_pt
    out["family"] = contrast.family
    out["control_type"] = contrast.control_type
    out["scenario_role"] = role
    out["scenario_treat"] = (out["scenario_role"] == "treated").astype(int)
    out["included"] = out["scenario_role"].isin(["treated", "control"]).astype(int)
    out["treatment_definition"] = contrast.treatment_definition_pt
    out["control_definition"] = contrast.control_definition_pt
    return out


def build_role_table(classification: pd.DataFrame) -> pd.DataFrame:
    roles = pd.concat([roles_for_contrast(classification, contrast) for contrast in CONTRASTS], ignore_index=True)
    validate_roles(roles)
    return roles


def validate_roles(roles: pd.DataFrame) -> None:
    bad_no_score = roles[
        roles["scenario_role"].isin(["treated", "control"])
        & roles["cbo_ilo_gradient"].isin(["No score"])
        & roles["scenario_id"].ne("baseline_mte2d_top20_vs_rest")
    ]
    if not bad_no_score.empty:
        raise RuntimeError("No score CBOs entered OIT treatment/control roles.")

    bad_no_mte = roles[
        roles["scenario_role"].isin(["treated", "control"])
        & roles["mte_match_status"].ne("matched_official_mte")
    ]
    if not bad_no_mte.empty:
        raise RuntimeError("No-MTE CBOs entered treatment/control roles.")

    for family in ["trat_alta_expo", "trat_media_expo", "trat_expostos"]:
        strict_id = f"{family}_strict_control"
        broad_id = f"{family}_broad_control"
        strict_control = roles[(roles["scenario_id"] == strict_id) & (roles["scenario_role"] == "control")]
        broad_control = roles[(roles["scenario_id"] == broad_id) & (roles["scenario_role"] == "control")]
        if set(strict_control["cbo_ilo_gradient"].unique()) != {"Not Exposed"}:
            raise RuntimeError(f"{strict_id} control is not exactly Not Exposed.")
        if set(broad_control["cbo_ilo_gradient"].unique()) != {"Not Exposed", "Minimal Exposure"}:
            raise RuntimeError(f"{broad_id} control is not exactly Not Exposed plus Minimal Exposure.")
        if broad_control["cbo_4d"].nunique() <= strict_control["cbo_4d"].nunique():
            raise RuntimeError(f"{broad_id} does not increase control CBO count over {strict_id}.")


def apply_contrast(panel: pd.DataFrame, roles: pd.DataFrame, contrast: Contrast) -> pd.DataFrame:
    role_cols = [
        "cbo_4d",
        "scenario_id",
        "scenario_label",
        "family",
        "control_type",
        "scenario_role",
        "scenario_treat",
        "cbo_ilo_gradient",
        "mte_match_status",
    ]
    role_subset = roles.loc[roles["scenario_id"] == contrast.scenario_id, role_cols].copy()
    merged = panel.merge(role_subset, on="cbo_4d", how="left")
    merged["scenario_role"] = merged["scenario_role"].fillna("excluded")
    out = merged.loc[merged["scenario_role"].isin(["treated", "control"])].copy()
    out["scenario_treat"] = out["scenario_treat"].astype(int)
    return out


def sample_summary(panel: pd.DataFrame, roles: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_cbo = int(roles["cbo_4d"].nunique())
    for contrast in CONTRASTS:
        role_subset = roles[roles["scenario_id"] == contrast.scenario_id].copy()
        d = apply_contrast(panel, roles, contrast)
        treated_cbo = int((role_subset["scenario_role"] == "treated").sum())
        control_cbo = int((role_subset["scenario_role"] == "control").sum())
        excluded_cbo = int((role_subset["scenario_role"] == "excluded").sum())
        rows.append(
            {
                "scenario_id": contrast.scenario_id,
                "scenario_label": contrast.label_pt,
                "family": contrast.family,
                "control_type": contrast.control_type,
                "treatment_definition": contrast.treatment_definition_pt,
                "control_definition": contrast.control_definition_pt,
                "n_cbo_total": total_cbo,
                "n_cbo_treated": treated_cbo,
                "n_cbo_control": control_cbo,
                "n_cbo_excluded": excluded_cbo,
                "n_obs": int(len(d)),
                "n_obs_treated": int((d["scenario_role"] == "treated").sum()),
                "n_obs_control": int((d["scenario_role"] == "control").sum()),
                "n_periods": int(d["periodo"].nunique()),
                "treated_gradients": "; ".join(sorted(role_subset.loc[role_subset["scenario_role"] == "treated", "cbo_ilo_gradient"].dropna().unique())),
                "control_gradients": "; ".join(sorted(role_subset.loc[role_subset["scenario_role"] == "control", "cbo_ilo_gradient"].dropna().unique())),
                "excluded_gradients": "; ".join(sorted(role_subset.loc[role_subset["scenario_role"] == "excluded", "cbo_ilo_gradient"].dropna().unique())),
            }
        )
    out = pd.DataFrame(rows)
    validate_sample_summary(out)
    return out


def validate_sample_summary(summary: pd.DataFrame) -> None:
    expected = {contrast.scenario_id for contrast in CONTRASTS}
    found = set(summary["scenario_id"])
    if found != expected:
        raise RuntimeError(f"Sample summary contrast mismatch. Expected {sorted(expected)}, found {sorted(found)}.")
    for family in ["trat_alta_expo", "trat_media_expo", "trat_expostos"]:
        strict = summary.loc[summary["scenario_id"].eq(f"{family}_strict_control")].iloc[0]
        broad = summary.loc[summary["scenario_id"].eq(f"{family}_broad_control")].iloc[0]
        if int(broad["n_cbo_control"]) <= int(strict["n_cbo_control"]):
            raise RuntimeError(f"{family} broad_control does not increase control CBO count.")
        if "Minimal Exposure" not in str(broad["control_gradients"]):
            raise RuntimeError(f"{family} broad_control does not include Minimal Exposure.")
        if "Minimal Exposure" in str(strict["control_gradients"]):
            raise RuntimeError(f"{family} strict_control includes Minimal Exposure.")


def prepare_event_data(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict[int, str]]:
    out = data.copy()
    dummy_names: list[str] = []
    t_to_name: dict[int, str] = {}
    for t in EVENT_TIMES:
        if t == REFERENCE_PERIOD:
            continue
        name = event_dummy_name(t)
        out[name] = ((out["t_binned"] == t) & (out["scenario_treat"] == 1)).astype(int)
        dummy_names.append(name)
        t_to_name[t] = name
    return out, dummy_names, t_to_name


def parse_wald_result(result: pd.Series) -> tuple[float, float]:
    statistic = np.nan
    p_value = np.nan
    for key, value in result.items():
        text = str(key).lower()
        if "p" in text and "value" in text:
            p_value = float(value)
        if ("stat" in text or "wald" in text) and not pd.isna(value):
            statistic = float(value)
    if pd.isna(p_value):
        for key, value in result.items():
            if "p" in str(key).lower():
                p_value = float(value)
    return statistic, p_value


def joint_pretrend_test(model: object, pre_terms: list[str]) -> tuple[float, float, str]:
    if not pre_terms:
        return np.nan, np.nan, "not_available_no_pre_terms"

    coef_index = list(model.coef().index)
    try:
        r_matrix = np.zeros((len(pre_terms), len(coef_index)))
        for row_idx, term in enumerate(pre_terms):
            r_matrix[row_idx, coef_index.index(term)] = 1.0
        result = model.wald_test(R=r_matrix, q=np.zeros(len(pre_terms)), distribution="chi2")
        statistic, p_value = parse_wald_result(result)
        if not pd.isna(p_value):
            return statistic, p_value, "wald_chi2"
    except Exception:
        pass

    tstats = model.tstat().reindex(pre_terms).dropna()
    if tstats.empty:
        return np.nan, np.nan, "not_available_no_tstats"
    statistic = float(np.square(tstats.astype(float)).sum())
    p_value = float(chi2.sf(statistic, len(tstats)))
    return statistic, p_value, "tstat_chi2_fallback"


def classify_pretrend(n_pre_p_lt_005: int, joint_p_value: float) -> str:
    if pd.isna(joint_p_value):
        return "warning"
    if joint_p_value < 0.05 or n_pre_p_lt_005 >= 2:
        return "fail"
    if n_pre_p_lt_005 == 0 and joint_p_value > 0.10:
        return "pass"
    return "warning"


def estimate_event_study(
    panel: pd.DataFrame,
    roles: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    coef_rows: list[dict[str, object]] = []
    pretrend_rows: list[dict[str, object]] = []

    for contrast in CONTRASTS:
        log(f"Estimating {contrast.scenario_id}...")
        base = apply_contrast(panel, roles, contrast)
        if base.empty:
            raise RuntimeError(f"{contrast.scenario_id} has an empty estimation sample.")
        event_data, dummy_names, t_to_name = prepare_event_data(base)
        did_terms = " + ".join(dummy_names)

        for outcome, outcome_label in OUTCOMES.items():
            d = event_data.dropna(subset=[outcome, *CONTROL_COLUMNS, "cbo_4d", "periodo"]).copy()
            d[outcome] = pd.to_numeric(d[outcome], errors="coerce")
            for col in CONTROL_COLUMNS:
                d[col] = pd.to_numeric(d[col], errors="coerce")
            d = d.dropna(subset=[outcome, *CONTROL_COLUMNS])

            if d.empty or d["scenario_treat"].nunique() < 2 or d["cbo_4d"].nunique() < 2:
                raise RuntimeError(f"{contrast.scenario_id}/{outcome} has insufficient variation.")

            formula = f"{outcome} ~ {did_terms} + {CONTROL_TERMS} | cbo_4d + periodo"
            model = pf.feols(formula, data=d, vcov=VCOV_SPEC)
            coefs = model.coef()
            ses = model.se()
            pvalues = model.pvalue()
            coef_index = set(coefs.index)

            for t in EVENT_TIMES:
                is_reference = t == REFERENCE_PERIOD
                is_pre = t < 0 and not is_reference
                if is_reference:
                    row = {
                        "coef": 0.0,
                        "se": 0.0,
                        "p_value": np.nan,
                        "ci_low": 0.0,
                        "ci_high": 0.0,
                        "coefficient_status": "reference",
                    }
                else:
                    term = t_to_name[t]
                    if term in coef_index:
                        coef = float(coefs.loc[term])
                        se = float(ses.loc[term])
                        p_value = float(pvalues.loc[term])
                        row = {
                            "coef": coef,
                            "se": se,
                            "p_value": p_value,
                            "ci_low": coef - 1.96 * se,
                            "ci_high": coef + 1.96 * se,
                            "coefficient_status": "estimated",
                        }
                    else:
                        row = {
                            "coef": np.nan,
                            "se": np.nan,
                            "p_value": np.nan,
                            "ci_low": np.nan,
                            "ci_high": np.nan,
                            "coefficient_status": "omitted",
                        }

                coef_rows.append(
                    {
                        "scenario_id": contrast.scenario_id,
                        "scenario_label": contrast.label_pt,
                        "family": contrast.family,
                        "control_type": contrast.control_type,
                        "outcome": outcome,
                        "outcome_label": outcome_label,
                        "t": t,
                        "is_reference": is_reference,
                        "is_pre": is_pre,
                        "n_obs": int(len(d)),
                        "n_cbo": int(d["cbo_4d"].nunique()),
                        "n_treated_cbo": int(d.loc[d["scenario_treat"].eq(1), "cbo_4d"].nunique()),
                        "n_control_cbo": int(d.loc[d["scenario_treat"].eq(0), "cbo_4d"].nunique()),
                        **row,
                    }
                )

            pre_terms = [t_to_name[t] for t in EVENT_TIMES if t < 0 and t != REFERENCE_PERIOD and t_to_name[t] in coef_index]
            pre_coef = pd.Series(coefs).reindex(pre_terms).astype(float)
            pre_pvalues = pd.Series(pvalues).reindex(pre_terms).astype(float)
            joint_statistic, joint_p_value, joint_method = joint_pretrend_test(model, pre_terms)
            n_pre_p_lt_005 = int((pre_pvalues < 0.05).sum())
            pretrend_rows.append(
                {
                    "scenario_id": contrast.scenario_id,
                    "scenario_label": contrast.label_pt,
                    "family": contrast.family,
                    "control_type": contrast.control_type,
                    "outcome": outcome,
                    "outcome_label": outcome_label,
                    "n_obs": int(len(d)),
                    "n_cbo": int(d["cbo_4d"].nunique()),
                    "n_pre_coefficients": int(pre_coef.notna().sum()),
                    "n_pre_p_lt_005": n_pre_p_lt_005,
                    "max_abs_pre_coef": float(pre_coef.abs().max()) if not pre_coef.empty else np.nan,
                    "mean_abs_pre_coef": float(pre_coef.abs().mean()) if not pre_coef.empty else np.nan,
                    "joint_statistic": joint_statistic,
                    "joint_p_value": joint_p_value,
                    "joint_test_method": joint_method,
                    "pretrend_status": classify_pretrend(n_pre_p_lt_005, joint_p_value),
                }
            )

    return pd.DataFrame(coef_rows), pd.DataFrame(pretrend_rows)


def plot_contrast(coefficients: pd.DataFrame, contrast: Contrast) -> None:
    d = coefficients[coefficients["scenario_id"] == contrast.scenario_id].copy()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    axes_flat = axes.flatten()
    for ax, (outcome, label) in zip(axes_flat, OUTCOMES.items()):
        view = d[d["outcome"] == outcome].sort_values("t")
        ax.axhline(0, color="#222222", linewidth=0.8)
        ax.axvline(REFERENCE_PERIOD, color="#666666", linewidth=0.8, linestyle="--")
        ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
        estimated = view[view["coefficient_status"].isin(["estimated", "reference"])]
        ax.plot(estimated["t"], estimated["coef"], marker="o", markersize=3, linewidth=1.3, color="#1f77b4")
        band = estimated.dropna(subset=["ci_low", "ci_high"])
        ax.fill_between(band["t"].astype(float), band["ci_low"].astype(float), band["ci_high"].astype(float), color="#1f77b4", alpha=0.18)
        ax.set_title(label)
        ax.set_xlabel("Meses relativos ao ChatGPT")
        ax.set_ylabel("Coeficiente")
        ax.grid(True, alpha=0.2)
    fig.suptitle(contrast.label_pt, fontsize=13)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / contrast.figure_name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_outcome_comparison(coefficients: pd.DataFrame, outcome: str, label: str) -> None:
    d = coefficients[coefficients["outcome"] == outcome].copy()
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.tab10(np.linspace(0, 1, len(CONTRASTS)))
    for color, contrast in zip(colors, CONTRASTS):
        view = d[
            (d["scenario_id"] == contrast.scenario_id)
            & d["coefficient_status"].isin(["estimated", "reference"])
        ].sort_values("t")
        ax.plot(view["t"], view["coef"], marker="o", markersize=2.5, linewidth=1.2, label=contrast.scenario_id, color=color)
    ax.axhline(0, color="#222222", linewidth=0.8)
    ax.axvline(REFERENCE_PERIOD, color="#666666", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
    ax.set_title(f"Comparação dos event studies: {label}")
    ax.set_xlabel("Meses relativos ao ChatGPT")
    ax.set_ylabel("Coeficiente")
    ax.grid(True, alpha=0.2)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"event_study_compare_{outcome}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_all(coefficients: pd.DataFrame) -> None:
    for contrast in CONTRASTS:
        plot_contrast(coefficients, contrast)
    for outcome, label in OUTCOMES.items():
        plot_outcome_comparison(coefficients, outcome, label)


def summarize_post_dynamics(coefficients: pd.DataFrame, scenario_id: str, outcome: str) -> str:
    d = coefficients[
        (coefficients["scenario_id"] == scenario_id)
        & (coefficients["outcome"] == outcome)
        & (coefficients["t"] >= 0)
        & coefficients["coefficient_status"].eq("estimated")
    ].copy()
    if d.empty:
        return "sem coeficientes pós-tratamento estimados"
    mean_coef = float(d["coef"].mean())
    sig_count = int((d["p_value"] < 0.05).sum())
    direction = "positiva" if mean_coef > 0 else "negativa" if mean_coef < 0 else "neutra"
    return f"média pós {direction} ({fmt_number(mean_coef)}), com {sig_count} coeficientes pós significativos a 5%"


def status_score(status: str) -> int:
    return {"pass": 2, "warning": 1, "fail": 0}.get(status, 0)


def contrast_rank(pretrends: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for contrast in CONTRASTS:
        d = pretrends[pretrends["scenario_id"] == contrast.scenario_id]
        rows.append(
            {
                "scenario_id": contrast.scenario_id,
                "scenario_label": contrast.label_pt,
                "family": contrast.family,
                "control_type": contrast.control_type,
                "n_pass": int((d["pretrend_status"] == "pass").sum()),
                "n_warning": int((d["pretrend_status"] == "warning").sum()),
                "n_fail": int((d["pretrend_status"] == "fail").sum()),
                "quality_score": int(d["pretrend_status"].map(status_score).sum()),
                "max_abs_pre_coef": float(d["max_abs_pre_coef"].max()),
                "mean_abs_pre_coef": float(d["mean_abs_pre_coef"].mean()),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["quality_score", "n_fail", "mean_abs_pre_coef"], ascending=[False, True, True])


def recommendation_for(contrast: Contrast, rank_row: pd.Series) -> str:
    if contrast.scenario_id == "baseline_mte2d_top20_vs_rest":
        return "benchmark principal da especificação MTE"
    if contrast.control_type == "strict_control":
        if int(rank_row["n_fail"]) == 0:
            return "candidato principal entre contrastes OIT"
        return "usar com cautela; contraste estrito tem falhas de pre-trend"
    if contrast.control_type == "broad_control":
        if int(rank_row["n_fail"]) == 0:
            return "robustez obrigatória para inclusão de Minimal Exposure no controle"
        return "robustez exploratória; incluir apenas com ressalvas"
    return "exploratório"


def write_contrast_report(
    contrast: Contrast,
    summary: pd.DataFrame,
    pretrends: pd.DataFrame,
    coefficients: pd.DataFrame,
) -> None:
    sample = summary.loc[summary["scenario_id"].eq(contrast.scenario_id)].iloc[0]
    pre = pretrends[pretrends["scenario_id"] == contrast.scenario_id].copy()
    pre_view = pre[
        [
            "outcome_label",
            "n_pre_coefficients",
            "n_pre_p_lt_005",
            "max_abs_pre_coef",
            "mean_abs_pre_coef",
            "joint_p_value",
            "joint_test_method",
            "pretrend_status",
        ]
    ].copy()
    for col in ["max_abs_pre_coef", "mean_abs_pre_coef", "joint_p_value"]:
        pre_view[col] = pre_view[col].map(lambda value: fmt_number(value, 4))

    pass_count = int((pre["pretrend_status"] == "pass").sum())
    warning_count = int((pre["pretrend_status"] == "warning").sum())
    fail_count = int((pre["pretrend_status"] == "fail").sum())
    dynamics = [
        f"- {OUTCOMES[outcome]}: {summarize_post_dynamics(coefficients, contrast.scenario_id, outcome)}."
        for outcome in OUTCOMES
    ]
    text = [
        f"# Event study: {contrast.label_pt}",
        "",
        "## Definição",
        "",
        f"- Tratamento: {contrast.treatment_definition_pt}",
        f"- Controle: {contrast.control_definition_pt}",
        f"- Tipo de controle: `{contrast.control_type}`.",
        "",
        "## Amostra",
        "",
        f"- CBOs tratados: {fmt_number(sample['n_cbo_treated'], 0)}.",
        f"- CBOs controle: {fmt_number(sample['n_cbo_control'], 0)}.",
        f"- CBOs fora do contraste: {fmt_number(sample['n_cbo_excluded'], 0)}.",
        f"- Observações usadas: {fmt_number(sample['n_obs'], 0)}.",
        f"- Gradientes no controle: {sample['control_gradients']}.",
        "",
        "## Pre-trends",
        "",
        markdown_table(
            pre_view,
            [
                "outcome_label",
                "n_pre_coefficients",
                "n_pre_p_lt_005",
                "max_abs_pre_coef",
                "mean_abs_pre_coef",
                "joint_p_value",
                "joint_test_method",
                "pretrend_status",
            ],
        ),
        "",
        "## Figura",
        "",
        f"![Event study {contrast.scenario_id}]({contrast.figure_name})",
        "",
        "## Leitura curta",
        "",
        f"Nos quatro outcomes, o diagnóstico de pre-trends tem {pass_count} `pass`, {warning_count} `warning` e {fail_count} `fail`.",
        "A leitura causal deve ser proporcional a esse diagnóstico: falhas de pre-trend enfraquecem o uso do contraste como evidência principal.",
        "",
        "Dinâmica pós-tratamento:",
        *dynamics,
        "",
    ]
    (OUTPUT_DIR / contrast.report_name).write_text("\n".join(text), encoding="utf-8")


def strict_broad_comparison(summary: pd.DataFrame, pretrends: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family in ["trat_alta_expo", "trat_media_expo", "trat_expostos"]:
        strict_id = f"{family}_strict_control"
        broad_id = f"{family}_broad_control"
        strict_sample = summary.loc[summary["scenario_id"].eq(strict_id)].iloc[0]
        broad_sample = summary.loc[summary["scenario_id"].eq(broad_id)].iloc[0]
        strict_pre = pretrends[pretrends["scenario_id"] == strict_id]
        broad_pre = pretrends[pretrends["scenario_id"] == broad_id]
        rows.append(
            {
                "family": family,
                "strict_control_cbo": int(strict_sample["n_cbo_control"]),
                "broad_control_cbo": int(broad_sample["n_cbo_control"]),
                "added_control_cbo": int(broad_sample["n_cbo_control"] - strict_sample["n_cbo_control"]),
                "strict_pass_warning_fail": f"{(strict_pre['pretrend_status'] == 'pass').sum()}/"
                f"{(strict_pre['pretrend_status'] == 'warning').sum()}/"
                f"{(strict_pre['pretrend_status'] == 'fail').sum()}",
                "broad_pass_warning_fail": f"{(broad_pre['pretrend_status'] == 'pass').sum()}/"
                f"{(broad_pre['pretrend_status'] == 'warning').sum()}/"
                f"{(broad_pre['pretrend_status'] == 'fail').sum()}",
            }
        )
    return pd.DataFrame(rows)


def write_general_report(summary: pd.DataFrame, pretrends: pd.DataFrame, coefficients: pd.DataFrame) -> None:
    rank = contrast_rank(pretrends)
    rank["recommendation"] = [
        recommendation_for(next(c for c in CONTRASTS if c.scenario_id == scenario_id), row)
        for scenario_id, (_, row) in zip(rank["scenario_id"], rank.iterrows())
    ]
    rank_view = rank[
        [
            "scenario_id",
            "n_pass",
            "n_warning",
            "n_fail",
            "quality_score",
            "mean_abs_pre_coef",
            "recommendation",
        ]
    ].copy()
    rank_view["mean_abs_pre_coef"] = rank_view["mean_abs_pre_coef"].map(lambda value: fmt_number(value, 4))

    comparison = strict_broad_comparison(summary, pretrends)
    pre_view = pretrends[["scenario_id", "outcome_label", "pretrend_status", "joint_p_value", "joint_test_method"]].copy()
    pre_view["joint_p_value"] = pre_view["joint_p_value"].map(lambda value: fmt_number(value, 4))

    text = [
        "# Event study por cenário: comparação geral",
        "",
        "## Contrato empírico",
        "",
        "O baseline `baseline_mte2d_top20_vs_rest` permanece como benchmark MTE já definido. Nos contrastes OIT, o tratamento usa os gradientes já calculados no scenario grid: G3-G4 para alta exposição, G1-G2 para média exposição e G1-G4 para expostos. O controle estrito usa apenas `Not Exposed`; o controle amplo adiciona `Minimal Exposure`. CBOs `No score`, sem MTE ou sem classificação válida ficam fora dos contrastes OIT.",
        "",
        "## Strict vs broad",
        "",
        markdown_table(
            comparison,
            [
                "family",
                "strict_control_cbo",
                "broad_control_cbo",
                "added_control_cbo",
                "strict_pass_warning_fail",
                "broad_pass_warning_fail",
            ],
        ),
        "",
        "A coluna `pass/warning/fail` resume os quatro outcomes de cada contraste. O aumento no controle amplo é a inclusão obrigatória de `Minimal Exposure`.",
        "",
        "## Ranking por qualidade dos pre-trends",
        "",
        markdown_table(
            rank_view,
            [
                "scenario_id",
                "n_pass",
                "n_warning",
                "n_fail",
                "quality_score",
                "mean_abs_pre_coef",
                "recommendation",
            ],
        ),
        "",
        "## Tabela geral de pre-trends",
        "",
        markdown_table(
            pre_view,
            ["scenario_id", "outcome_label", "pretrend_status", "joint_p_value", "joint_test_method"],
        ),
        "",
        "## Figuras comparativas",
        "",
        *[f"- ![{label}](event_study_compare_{outcome}.png)" for outcome, label in OUTCOMES.items()],
        "",
        "## Recomendação de uso na dissertação",
        "",
        "A especificação estrita deve continuar sendo a leitura causal principal para os contrastes OIT, porque ela compara gradientes expostos contra `Not Exposed` puro. A versão ampla deve entrar como robustez obrigatória: ela testa se a conclusão sobrevive quando `Minimal Exposure` é incorporado ao grupo de controle. Contrastes com `fail` em pre-trends devem ser apresentados como exploratórios ou problemáticos, não como achado principal.",
        "",
    ]
    (OUTPUT_DIR / "event_study_comparison_report.md").write_text("\n".join(text), encoding="utf-8")


def write_reports(summary: pd.DataFrame, pretrends: pd.DataFrame, coefficients: pd.DataFrame) -> None:
    for contrast in CONTRASTS:
        write_contrast_report(contrast, summary, pretrends, coefficients)
    write_general_report(summary, pretrends, coefficients)


def validate_outputs(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    summary: pd.DataFrame,
    roles: pd.DataFrame,
) -> None:
    expected_scenarios = {contrast.scenario_id for contrast in CONTRASTS}
    expected_outcomes = set(OUTCOMES)
    if set(coefficients["scenario_id"]) != expected_scenarios:
        raise RuntimeError("Coefficient CSV does not contain all expected contrasts.")
    if set(pretrends["scenario_id"]) != expected_scenarios:
        raise RuntimeError("Pretrend CSV does not contain all expected contrasts.")
    for scenario_id in expected_scenarios:
        if set(coefficients.loc[coefficients["scenario_id"].eq(scenario_id), "outcome"]) != expected_outcomes:
            raise RuntimeError(f"{scenario_id} is missing outcomes in coefficients.")
        if set(pretrends.loc[pretrends["scenario_id"].eq(scenario_id), "outcome"]) != expected_outcomes:
            raise RuntimeError(f"{scenario_id} is missing outcomes in pretrend tests.")

    ref = coefficients[coefficients["t"].eq(REFERENCE_PERIOD)]
    if len(ref) != len(expected_scenarios) * len(expected_outcomes):
        raise RuntimeError("Reference period rows are missing.")
    if not (ref["coef"].fillna(999).eq(0).all() and ref["se"].fillna(999).eq(0).all()):
        raise RuntimeError("Reference period rows must have coefficient and standard error equal to zero.")

    required_pretrend_cols = {
        "scenario_id",
        "outcome",
        "n_pre_coefficients",
        "n_pre_p_lt_005",
        "max_abs_pre_coef",
        "mean_abs_pre_coef",
        "joint_p_value",
        "pretrend_status",
        "joint_test_method",
    }
    if not required_pretrend_cols.issubset(pretrends.columns):
        raise RuntimeError("Pretrend tests are missing required columns.")

    validate_roles(roles)
    validate_sample_summary(summary)

    expected_files = [
        OUTPUT_DIR / "event_study_coefficients_long.csv",
        OUTPUT_DIR / "event_study_pretrend_tests.csv",
        OUTPUT_DIR / "event_study_sample_summary.csv",
        OUTPUT_DIR / "event_study_contrast_cbo_roles.csv",
        OUTPUT_DIR / "event_study_comparison_report.md",
        *[OUTPUT_DIR / contrast.figure_name for contrast in CONTRASTS],
        *[OUTPUT_DIR / contrast.report_name for contrast in CONTRASTS],
        *[OUTPUT_DIR / f"event_study_compare_{outcome}.png" for outcome in OUTCOMES],
    ]
    missing_or_empty = [str(path) for path in expected_files if not path.exists() or path.stat().st_size == 0]
    if missing_or_empty:
        raise RuntimeError("Missing or empty expected outputs:\n" + "\n".join(missing_or_empty))

    report = (OUTPUT_DIR / "event_study_comparison_report.md").read_text(encoding="utf-8")
    for required_text in ["controle estrito", "controle amplo", "Minimal Exposure", "robustez", "exploratórios"]:
        if required_text not in report:
            raise RuntimeError(f"General report does not explicitly include: {required_text}")


def main() -> None:
    log("Loading inputs...")
    panel, classification = load_inputs()
    roles = build_role_table(classification)
    summary = sample_summary(panel, roles)
    roles.to_csv(OUTPUT_DIR / "event_study_contrast_cbo_roles.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "event_study_sample_summary.csv", index=False)

    log("Estimating event studies...")
    coefficients, pretrends = estimate_event_study(panel, roles)
    coefficients.to_csv(OUTPUT_DIR / "event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(OUTPUT_DIR / "event_study_pretrend_tests.csv", index=False)

    log("Writing figures...")
    plot_all(coefficients)

    log("Writing reports...")
    write_reports(summary, pretrends, coefficients)

    log("Validating outputs...")
    validate_outputs(coefficients, pretrends, summary, roles)
    log(f"Done. Outputs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
