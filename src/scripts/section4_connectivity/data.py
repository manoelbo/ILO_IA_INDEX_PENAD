"""Data preparation for the Section 4 connectivity extension."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from section4_event_study.data import add_continuous_exposure
from section4_event_study.treatment import assign_roles

from .config import (
    CANARIES_AGE_CACHE,
    CANARIES_AGE_GROUPS,
    DATA_RAW,
    EXPECTED_CROSSWALK_SPEC,
    IPCA_PATH,
    MATCHED_MTE_STATUS,
    MUNICIPAL_PANEL_PATH,
    SCENARIO_GRID,
)


EXPOSURE_COLUMNS = [
    "mte_match_status",
    "cbo_ilo_gradient",
    "isco08_mean_score",
    "isco08_pooled_sd",
    "continuous_exposure_raw",
    "continuous_exposure",
    "role__baseline_mte2d_top20_vs_rest",
]

RAW_BATCH_SIZE = 500_000


def load_ipca() -> pd.DataFrame:
    ipca = pd.read_parquet(IPCA_PATH)
    required = ["ano", "mes", "indice"]
    missing = [col for col in required if col not in ipca.columns]
    if missing:
        raise RuntimeError(f"IPCA file is missing required columns: {missing}")
    out = ipca[required].copy()
    out["indice"] = pd.to_numeric(out["indice"], errors="coerce")
    if out["indice"].isna().any() or out["indice"].le(0).any():
        raise RuntimeError("IPCA index must be non-missing and positive.")
    return out


def load_classification() -> pd.DataFrame:
    classification = pd.read_csv(SCENARIO_GRID, dtype={"cbo_4d": str})
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    required = ["cbo_4d", "mte_match_status", "cbo_ilo_gradient", "isco08_mean_score", "isco08_pooled_sd"]
    missing = [col for col in required if col not in classification.columns]
    if missing:
        raise RuntimeError(f"Scenario classification is missing required columns: {missing}")
    if "role__baseline_mte2d_top20_vs_rest" not in classification.columns:
        classification["role__baseline_mte2d_top20_vs_rest"] = "excluded"
    return add_continuous_exposure(classification)


def _validate_crosswalk(panel: pd.DataFrame) -> None:
    if "crosswalk_spec" not in panel.columns:
        raise RuntimeError("Municipal panel is missing crosswalk_spec.")
    specs = set(panel["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_CROSSWALK_SPEC}:
        raise RuntimeError(f"Municipal panel must use {EXPECTED_CROSSWALK_SPEC}; found {sorted(specs)}.")


def _safe_log_for_positive_flow(
    df: pd.DataFrame,
    flow_col: str,
    wage_col: str,
    out_col: str,
    ipca_index: pd.Series,
) -> pd.Series:
    flow = pd.to_numeric(df[flow_col], errors="coerce")
    wage = pd.to_numeric(df[wage_col], errors="coerce")
    real = wage * (100.0 / ipca_index)
    return np.log(real.where(flow.gt(0) & wage.gt(0)))


def add_connectivity_terms(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["scenario_treat"] = pd.to_numeric(out["scenario_treat"], errors="coerce").fillna(0).astype(int)
    out["post"] = pd.to_numeric(out["post"], errors="coerce").fillna(0).astype(int)
    out["high_connect"] = pd.to_numeric(out["alta_conectividade"], errors="coerce").fillna(0).astype(int)
    out["high_connect_q75"] = pd.to_numeric(out.get("conectividade_q75", 0), errors="coerce").fillna(0).astype(int)
    q25 = pd.to_numeric(out.get("conectividade_q25", 0), errors="coerce").fillna(0).astype(int)
    out["low_connect_q25"] = 1 - q25
    out["connectivity_extreme_sample"] = out["high_connect_q75"].eq(1) | out["low_connect_q25"].eq(1)
    if "alta_fibra" in out.columns:
        out["high_fiber"] = pd.to_numeric(out["alta_fibra"], errors="coerce").fillna(0).astype(int)
    elif "pct_fibra_pre" in out.columns:
        median_fiber = pd.to_numeric(out["pct_fibra_pre"], errors="coerce").median()
        out["high_fiber"] = pd.to_numeric(out["pct_fibra_pre"], errors="coerce").gt(median_fiber).astype(int)
    else:
        out["high_fiber"] = 0
    penetration = pd.to_numeric(out["penetracao_bl"], errors="coerce")
    sd = penetration.std(ddof=0)
    out["connectivity_z"] = (penetration - penetration.mean()) / sd if sd and not pd.isna(sd) else np.nan
    out["post_treat"] = out["post"] * out["scenario_treat"]
    out["post_high_connect"] = out["post"] * out["high_connect"]
    out["treat_high_connect"] = out["scenario_treat"] * out["high_connect"]
    out["post_treat_connect"] = out["post"] * out["scenario_treat"] * out["high_connect"]
    out["post_treat_connect_q75"] = out["post"] * out["scenario_treat"] * out["high_connect_q75"]
    out["post_high_connect_q75"] = out["post"] * out["high_connect_q75"]
    out["treat_high_connect_q75"] = out["scenario_treat"] * out["high_connect_q75"]
    out["post_treat_fiber"] = out["post"] * out["scenario_treat"] * out["high_fiber"]
    out["post_high_fiber"] = out["post"] * out["high_fiber"]
    out["treat_high_fiber"] = out["scenario_treat"] * out["high_fiber"]
    out["post_treat_connect_z"] = out["post"] * out["scenario_treat"] * out["connectivity_z"]
    out["post_connectivity_z"] = out["post"] * out["connectivity_z"]
    out["treat_connectivity_z"] = out["scenario_treat"] * out["connectivity_z"]
    out["cbo_municipio"] = out["cbo_4d"].astype(str) + "_" + out["id_municipio"].astype(str)
    out["cbo_periodo"] = out["cbo_4d"].astype(str) + "_" + out["periodo"].astype(str)
    out["uf_periodo"] = out.get("sigla_uf", "").astype(str) + "_" + out["periodo"].astype(str)
    return out


def add_pre_cell_weights(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    pre = out[out["post"].eq(0)].copy()
    weights = (
        pre.groupby(["cbo_4d", "id_municipio"], observed=True)["admissoes"]
        .mean()
        .rename("pre_cell_adm_weight")
        .reset_index()
    )
    out = out.merge(weights, on=["cbo_4d", "id_municipio"], how="left")
    out["pre_cell_adm_weight"] = pd.to_numeric(out["pre_cell_adm_weight"], errors="coerce")
    return out


def add_net_flow_measures(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    admissions = pd.to_numeric(out["admissoes"], errors="coerce")
    dismissals = pd.to_numeric(out["desligamentos"], errors="coerce")
    pre_cell_admissions = pd.to_numeric(out["pre_cell_adm_weight"], errors="coerce")
    out["saldo"] = admissions - dismissals
    out["asinh_saldo"] = np.arcsinh(out["saldo"])
    pre_mask = pre_cell_admissions.gt(0).fillna(False)
    out["saldo_per_pre_cell_adm"] = np.where(pre_mask, out["saldo"] / pre_cell_admissions, np.nan)
    total_flow = admissions + dismissals
    flow_mask = total_flow.gt(0).fillna(False)
    out["saldo_flow_rate"] = np.where(flow_mask, out["saldo"] / total_flow, np.nan)
    return out


def add_real_subgroup_wages(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    subgroup_wage_cols = {
        "jovem": "salario_medio_jovem",
        "naojovem": "salario_medio_naojovem",
        "intermediario": "salario_medio_intermediario",
        "senior": "salario_medio_senior",
        "mulher": "salario_medio_mulher",
        "homem": "salario_medio_homem",
        "negro": "salario_medio_negro",
        "branco": "salario_medio_branco",
        "superior": "salario_medio_superior",
        "medio": "salario_medio_medio",
    }
    for group, wage_col in subgroup_wage_cols.items():
        if wage_col not in out.columns:
            continue
        wage = pd.to_numeric(out[wage_col], errors="coerce")
        real = wage * (100.0 / pd.to_numeric(out["indice"], errors="coerce"))
        out[f"ln_salario_real_{group}"] = np.log(real.where(wage.gt(0)))
    return out


def _valid_cbo_4d(series: pd.Series) -> pd.Series:
    codes = series.astype("string").str.strip().str[:4]
    return codes.where(codes.str.fullmatch(r"\d{4}", na=False))


def _age_group(age: pd.Series, group: str) -> pd.Series:
    low, high = CANARIES_AGE_GROUPS[group]
    numeric = pd.to_numeric(age, errors="coerce")
    if high is None:
        return numeric.ge(low)
    return numeric.ge(low) & numeric.le(high)


def build_canaries_age_cache() -> pd.DataFrame:
    if CANARIES_AGE_CACHE.exists():
        return pd.read_parquet(CANARIES_AGE_CACHE)
    pieces = []
    columns = ["ano", "mes", "id_municipio", "cbo_2002", "saldo_movimentacao", "salario_mensal", "idade"]
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        print(f"  Reading connectivity age microdata: {path.name}", flush=True)
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=RAW_BATCH_SIZE, columns=columns):
            df = batch.to_pandas()
            df["cbo_4d"] = _valid_cbo_4d(df["cbo_2002"])
            valid = df["cbo_4d"].notna()
            if not bool(valid.any()):
                continue
            df = df.loc[valid].copy()
            df["id_municipio"] = df["id_municipio"].astype(str).str.zfill(7)
            df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int16")
            df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int8")
            df["periodo"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
            saldo = pd.to_numeric(df["saldo_movimentacao"], errors="coerce")
            wage = pd.to_numeric(df["salario_mensal"], errors="coerce")
            for group in CANARIES_AGE_GROUPS:
                mask = _age_group(df["idade"], group)
                if not bool(mask.any()):
                    continue
                d = df.loc[mask, ["cbo_4d", "id_municipio", "ano", "mes", "periodo"]].copy()
                d["age_group"] = group
                d["is_adm"] = saldo.loc[mask].eq(1).astype("int8").to_numpy()
                d["is_des"] = saldo.loc[mask].eq(-1).astype("int8").to_numpy()
                d["salario_adm"] = np.where(d["is_adm"].eq(1) & wage.loc[mask].gt(0), wage.loc[mask], np.nan)
                agg = (
                    d.groupby(["age_group", "cbo_4d", "id_municipio", "ano", "mes", "periodo"], observed=True)
                    .agg(
                        adm=("is_adm", "sum"),
                        deslig=("is_des", "sum"),
                        salario_sum=("salario_adm", "sum"),
                        salario_count=("salario_adm", "count"),
                    )
                    .reset_index()
                )
                pieces.append(agg)
    if not pieces:
        raise RuntimeError("Could not build Canaries age cache from raw CAGED.")
    long = (
        pd.concat(pieces, ignore_index=True)
        .groupby(["age_group", "cbo_4d", "id_municipio", "ano", "mes", "periodo"], observed=True)
        .agg(
            adm=("adm", "sum"),
            deslig=("deslig", "sum"),
            salario_sum=("salario_sum", "sum"),
            salario_count=("salario_count", "sum"),
        )
        .reset_index()
    )
    long["salario_medio_adm"] = long["salario_sum"] / long["salario_count"].replace(0, np.nan)
    wide = long.pivot_table(
        index=["cbo_4d", "id_municipio", "ano", "mes", "periodo"],
        columns="age_group",
        values=["adm", "deslig", "salario_medio_adm"],
        aggfunc="first",
    )
    wide.columns = [f"{metric}_{group}" for metric, group in wide.columns]
    wide = wide.reset_index()
    CANARIES_AGE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(CANARIES_AGE_CACHE, index=False)
    return wide


def add_canaries_age_outcomes(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    age = build_canaries_age_cache()
    age["cbo_4d"] = age["cbo_4d"].astype(str).str.zfill(4)
    age["id_municipio"] = age["id_municipio"].astype(str).str.zfill(7)
    out = out.merge(age, on=["cbo_4d", "id_municipio", "ano", "mes", "periodo"], how="left")
    for group in CANARIES_AGE_GROUPS:
        adm_col = f"adm_{group}"
        wage_col = f"salario_medio_adm_{group}"
        if adm_col in out.columns:
            out[f"ln_adm_{group}"] = np.log(pd.to_numeric(out[adm_col], errors="coerce").fillna(0) + 1)
        if wage_col in out.columns:
            wage = pd.to_numeric(out[wage_col], errors="coerce")
            real = wage * (100.0 / pd.to_numeric(out["indice"], errors="coerce"))
            out[f"ln_sal_real_{group}"] = np.log(real.where(wage.gt(0)))
    return out


def prepare_connectivity_panel(
    municipal_panel: pd.DataFrame,
    classification: pd.DataFrame,
    ipca: pd.DataFrame,
    include_canaries_age: bool = False,
) -> pd.DataFrame:
    panel = municipal_panel.copy()
    panel["cbo_4d"] = panel["cbo_4d"].astype(str).str.zfill(4)
    panel["id_municipio"] = panel["id_municipio"].astype(str).str.zfill(7)
    panel["periodo"] = panel["periodo"].astype(str)
    _validate_crosswalk(panel)
    if "indice" in panel.columns:
        panel = panel.drop(columns=["indice"])

    classification = classification.copy()
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    roles = assign_roles(classification, "main_strict")
    role_cols = ["cbo_4d", "scenario_id", "scenario_role", "scenario_treat"]
    keep_exposure = ["cbo_4d", *[col for col in EXPOSURE_COLUMNS if col in classification.columns]]

    drop_cols = [col for col in EXPOSURE_COLUMNS + ["scenario_id", "scenario_role", "scenario_treat"] if col in panel.columns]
    if drop_cols:
        panel = panel.drop(columns=drop_cols)
    panel = panel.merge(classification[keep_exposure], on="cbo_4d", how="left")
    panel = panel.merge(roles[role_cols], on="cbo_4d", how="left")
    panel["scenario_role"] = panel["scenario_role"].fillna("excluded")
    out = panel[panel["scenario_role"].isin(["treated", "control"])].copy()
    out = out[out["mte_match_status"].eq(MATCHED_MTE_STATUS)].copy()

    out = out.merge(ipca[["ano", "mes", "indice"]], on=["ano", "mes"], how="left")
    if out["indice"].isna().any():
        missing = out.loc[out["indice"].isna(), ["ano", "mes"]].drop_duplicates()
        raise RuntimeError(f"Missing IPCA for municipal periods:\n{missing.to_string(index=False)}")
    out["ln_salario_real_adm"] = _safe_log_for_positive_flow(out, "admissoes", "salario_medio_adm", "ln_salario_real_adm", out["indice"])
    out["ln_salario_real_desl"] = _safe_log_for_positive_flow(
        out, "desligamentos", "salario_medio_desl", "ln_salario_real_desl", out["indice"]
    )
    salario_adm = pd.to_numeric(out["salario_medio_adm"], errors="coerce")
    salario_desl = pd.to_numeric(out["salario_medio_desl"], errors="coerce")
    out["ln_salario_adm"] = np.log(
        salario_adm.where(pd.to_numeric(out["admissoes"], errors="coerce").gt(0) & salario_adm.gt(0))
    )
    out["ln_salario_desl"] = np.log(
        salario_desl.where(pd.to_numeric(out["desligamentos"], errors="coerce").gt(0) & salario_desl.gt(0))
    )
    out["ln_admissoes"] = np.log(pd.to_numeric(out["admissoes"], errors="coerce").fillna(0) + 1)
    out["ln_desligamentos"] = np.log(pd.to_numeric(out["desligamentos"], errors="coerce").fillna(0) + 1)
    out = add_real_subgroup_wages(out)
    if include_canaries_age:
        out = add_canaries_age_outcomes(out)
    out = add_connectivity_terms(out)
    out = add_pre_cell_weights(out)
    out = add_net_flow_measures(out)
    return out


def load_connectivity_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return pd.read_parquet(MUNICIPAL_PANEL_PATH), load_classification(), load_ipca()


def build_connectivity_panel() -> pd.DataFrame:
    municipal_panel, classification, ipca = load_connectivity_inputs()
    return prepare_connectivity_panel(municipal_panel, classification, ipca, include_canaries_age=True)
