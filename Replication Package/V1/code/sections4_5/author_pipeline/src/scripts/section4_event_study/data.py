"""Data loading and validation for the final Section 4 event-study package."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    ALL_OUTCOMES,
    CONTROL_COLUMNS,
    EXPECTED_CROSSWALK_SPEC,
    IPCA_PATH,
    MATCHED_MTE_STATUS,
    PANEL_PATH,
    SCENARIO_GRID,
    TREATMENT_PERIOD,
)


def ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def add_continuous_exposure(classification: pd.DataFrame) -> pd.DataFrame:
    out = classification.copy()
    raw = pd.to_numeric(out["isco08_mean_score"], errors="coerce") + pd.to_numeric(
        out["isco08_pooled_sd"], errors="coerce"
    )
    mean = raw.mean(skipna=True)
    sd = raw.std(skipna=True, ddof=0)
    if pd.isna(sd) or sd == 0:
        raise RuntimeError("continuous_exposure cannot be standardized because its standard deviation is zero.")
    out["continuous_exposure_raw"] = raw
    out["continuous_exposure"] = (raw - mean) / sd
    return out


def load_classification() -> pd.DataFrame:
    classification = pd.read_csv(SCENARIO_GRID, dtype={"cbo_4d": str})
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    required = [
        "cbo_4d",
        "mte_match_status",
        "cbo_ilo_gradient",
        "isco08_mean_score",
        "isco08_pooled_sd",
        "role__baseline_mte2d_top20_vs_rest",
    ]
    missing = [col for col in required if col not in classification.columns]
    if missing:
        raise RuntimeError(f"Scenario classification is missing required columns: {missing}")
    return add_continuous_exposure(classification)


def load_ipca() -> pd.DataFrame:
    if not IPCA_PATH.exists():
        raise FileNotFoundError(f"IPCA deflator file not found: {IPCA_PATH}")
    ipca = pd.read_parquet(IPCA_PATH)
    required = ["ano", "mes", "indice"]
    missing = [col for col in required if col not in ipca.columns]
    if missing:
        raise RuntimeError(f"IPCA deflator file is missing required columns: {missing}")
    ipca = ensure_numeric(ipca[required], required)
    if ipca["indice"].isna().any() or (ipca["indice"] <= 0).any():
        raise RuntimeError("IPCA deflator has missing or non-positive index values.")
    return ipca


def add_real_wage_measures(
    panel: pd.DataFrame,
    ipca: pd.DataFrame,
    admission_col: str = "salario_medio_adm",
    dismissal_col: str | None = "salario_medio_desl",
) -> pd.DataFrame:
    out = panel.merge(ipca[["ano", "mes", "indice"]], on=["ano", "mes"], how="left")
    if out["indice"].isna().any():
        missing_periods = out.loc[out["indice"].isna(), ["ano", "mes"]].drop_duplicates().sort_values(["ano", "mes"])
        raise RuntimeError(f"Missing IPCA index for periods:\n{missing_periods.to_string(index=False)}")
    if admission_col not in out.columns:
        raise RuntimeError(f"Cannot compute real admission wage; missing column: {admission_col}")
    out["salario_real_adm"] = pd.to_numeric(out[admission_col], errors="coerce") * (100.0 / out["indice"])
    out["ln_salario_real_adm"] = np.log(out["salario_real_adm"].clip(lower=1))
    if dismissal_col is not None:
        if dismissal_col not in out.columns:
            raise RuntimeError(f"Cannot compute real dismissal wage; missing column: {dismissal_col}")
        out["salario_real_desl"] = pd.to_numeric(out[dismissal_col], errors="coerce") * (100.0 / out["indice"])
        out["ln_salario_real_desl"] = np.log(out["salario_real_desl"].clip(lower=1))
    return out


def add_pre_treatment_control_interactions(
    panel: pd.DataFrame,
    treatment_period: int = TREATMENT_PERIOD,
    control_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Add CBO-level pre-treatment controls interacted with the post period.

    Baseline controls alone are absorbed by CBO fixed effects. The post
    interaction keeps the controls usable without relying on contemporaneous
    composition that may itself be affected by treatment.
    """
    controls = control_columns or CONTROL_COLUMNS
    out = panel.copy()
    pre = out[pd.to_numeric(out["periodo_num"], errors="coerce") < treatment_period].copy()
    if pre.empty:
        raise RuntimeError("Cannot construct pre-treatment controls; no pre-treatment rows found.")
    baseline = (
        pre.groupby("cbo_4d", observed=True)[controls]
        .mean()
        .rename(columns={col: f"pre_{col}" for col in controls})
        .reset_index()
    )
    out = out.merge(baseline, on="cbo_4d", how="left")
    interaction_cols: list[str] = []
    post = pd.to_numeric(out["post"], errors="coerce").fillna(0)
    for col in controls:
        pre_col = f"pre_{col}"
        interaction_col = f"post_pre_{col}"
        out[interaction_col] = post * pd.to_numeric(out[pre_col], errors="coerce")
        interaction_cols.append(interaction_col)
    return out, interaction_cols


def add_net_flow_measures(
    panel: pd.DataFrame,
    pre_adm_col: str = "pre_adm_weight",
) -> pd.DataFrame:
    out = panel.copy()
    required = ["admissoes", "desligamentos", pre_adm_col]
    missing = [col for col in required if col not in out.columns]
    if missing:
        raise RuntimeError(f"Cannot compute net-flow measures; missing columns: {missing}")
    admissions = pd.to_numeric(out["admissoes"], errors="coerce")
    dismissals = pd.to_numeric(out["desligamentos"], errors="coerce")
    pre_admissions = pd.to_numeric(out[pre_adm_col], errors="coerce")
    out["saldo"] = admissions - dismissals
    out["asinh_saldo"] = np.arcsinh(out["saldo"])
    pre_mask = pre_admissions.gt(0).fillna(False)
    out["saldo_per_pre_adm"] = np.where(pre_mask, out["saldo"] / pre_admissions, np.nan)
    total_flow = admissions + dismissals
    flow_mask = total_flow.gt(0).fillna(False)
    out["saldo_flow_rate"] = np.where(flow_mask, out["saldo"] / total_flow, np.nan)
    return out


def load_panel() -> pd.DataFrame:
    panel = pd.read_parquet(PANEL_PATH)
    panel["cbo_4d"] = panel["cbo_4d"].astype(str).str.zfill(4)
    panel["periodo"] = panel["periodo"].astype(str)
    if set(panel["crosswalk_spec"].dropna().unique()) != {EXPECTED_CROSSWALK_SPEC}:
        raise RuntimeError(f"Stage 2 panel must use {EXPECTED_CROSSWALK_SPEC}.")
    required = [
        "cbo_4d",
        "cbo_2d",
        "ano",
        "mes",
        "periodo",
        "periodo_num",
        "post",
        "tempo_relativo_meses",
        "admissoes",
        "desligamentos",
        "salario_medio_adm",
        "salario_medio_desl",
        *CONTROL_COLUMNS,
        *[col for col in ALL_OUTCOMES if col != "ln_salario_desl"],
    ]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise RuntimeError(f"Stage 2 panel is missing required columns: {missing}")
    panel = ensure_numeric(
        panel,
        [
            "ano",
            "mes",
            "periodo_num",
            "post",
            "tempo_relativo_meses",
            "admissoes",
            "desligamentos",
            "salario_medio_adm",
            "salario_medio_desl",
            *CONTROL_COLUMNS,
            *[col for col in ALL_OUTCOMES if col != "ln_salario_desl"],
        ],
    )
    if pd.to_numeric(panel["pct_mulher_adm"], errors="coerce").max(skipna=True) == 0:
        raise RuntimeError("pct_mulher_adm.max() == 0; demographic recoding is invalid.")
    if pd.to_numeric(panel["pct_negra_adm"], errors="coerce").max(skipna=True) == 0:
        raise RuntimeError("pct_negra_adm.max() == 0; race/color recoding is invalid.")
    panel["ln_salario_desl"] = np.log(pd.to_numeric(panel["salario_medio_desl"], errors="coerce").clip(lower=1))
    panel = add_real_wage_measures(panel, load_ipca())
    pre = (
        panel[panel["periodo_num"] < TREATMENT_PERIOD]
        .groupby("cbo_4d", observed=True)["admissoes"]
        .mean()
        .rename("pre_adm_weight")
        .reset_index()
    )
    panel = panel.merge(pre, on="cbo_4d", how="left")
    panel["pre_adm_weight"] = pd.to_numeric(panel["pre_adm_weight"], errors="coerce")
    panel = add_net_flow_measures(panel)
    panel, _interaction_cols = add_pre_treatment_control_interactions(panel)
    return panel


def load_analysis_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = load_panel()
    classification = load_classification()
    keep = [
        "cbo_4d",
        "mte_match_status",
        "cbo_ilo_gradient",
        "isco08_mean_score",
        "isco08_pooled_sd",
        "continuous_exposure_raw",
        "continuous_exposure",
        "role__baseline_mte2d_top20_vs_rest",
    ]
    overlap = [col for col in keep if col != "cbo_4d" and col in panel.columns]
    if overlap:
        panel = panel.drop(columns=overlap)
    panel = panel.merge(classification[keep], on="cbo_4d", how="left")
    if panel.loc[panel["mte_match_status"].eq(MATCHED_MTE_STATUS), "continuous_exposure"].isna().any():
        raise RuntimeError("Matched MTE rows should have continuous exposure values.")
    return panel, classification
