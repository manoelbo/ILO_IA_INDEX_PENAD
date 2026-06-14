#!/usr/bin/env python3
"""
Compare empirical results before and after the official MTE CAGED crosswalk.

The "before" specifications are reconstructed from preserved legacy score
columns when possible. The "after" specifications use the official MTE bridge:
MTE CBO2002-CBO94-CIUO88 -> ISCO-88 -> ISCO-08 -> ILO score.
"""

from __future__ import annotations

import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)


ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_OUTPUT = ROOT / "data" / "output"
OUTPUT_DIR = ROOT / "outputs" / "crosswalk_results_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CROSSWALK_PANEL = DATA_PROCESSED / "painel_caged_crosswalk.parquet"
STAGE2_READY = DATA_OUTPUT / "painel_2b_ready.parquet"
STAGE3_OLD = DATA_OUTPUT / "painel_caged_municipio_anatel_v2.parquet"
STAGE3_NEW = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
STAGE2_NEW_RESULTS = ROOT / "outputs" / "tables" / "did_main_results.csv"
STAGE3_NEW_RESULTS = ROOT / "outputs" / "tables" / "triple_did_main_etapa3b.csv"
MTE_SUMMARY = ROOT / "outputs" / "crosswalk_audit" / "official_mte_bridge" / "summary_old_vs_mte.csv"
OLD_VS_MTE_COMPARISON = (
    ROOT / "outputs" / "crosswalk_audit" / "official_mte_bridge" / "caged_old_vs_mte_comparison.csv"
)

EXPECTED_SPEC = "mte_official_no_numeric_fallback"

SALARIO_MINIMO = {
    2021: 1100,
    2022: 1212,
    2023: 1320,
    2024: 1412,
    2025: 1518,
}

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


def clean_stars(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def fmt(value: float | int | None, digits: int = 4) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    return f"{value:.{digits}f}".replace(".", ",")


def pct(value: float | None, digits: int = 2) -> str:
    if value is None or math.isnan(value):
        return ""
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in df[columns].iterrows():
        rows.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in columns) + " |")
    return "\n".join([header, separator, *rows])


def prepare_stage2_panel(df: pd.DataFrame, score_prefix: str, sample: str) -> pd.DataFrame:
    out = df.copy()
    if sample == "common_mte_matched":
        out = out[out["exposure_score_2d"].notna()].copy()

    out["exposure_score_2d_model"] = out[f"exposure_score_2d_{score_prefix}"]
    out["exposure_score_4d_model"] = out[f"exposure_score_4d_{score_prefix}"]
    out = out[out["exposure_score_2d_model"].notna()].copy()

    scores_2d = out.groupby("cbo_4d")["exposure_score_2d_model"].first().dropna()
    thresholds = {
        "alta_exp": scores_2d.quantile(0.80),
        "alta_exp_10": scores_2d.quantile(0.90),
        "alta_exp_25": scores_2d.quantile(0.75),
        "alta_exp_mediana": scores_2d.quantile(0.50),
    }
    for col, threshold in thresholds.items():
        out[col] = (out["exposure_score_2d_model"] >= threshold).astype(int)

    scores_4d = out.groupby("cbo_4d")["exposure_score_4d_model"].first().dropna()
    threshold_4d = scores_4d.quantile(0.80)
    out["alta_exp_4d"] = (out["exposure_score_4d_model"] >= threshold_4d).astype(int)
    out["post_alta"] = out["post"] * out["alta_exp"]
    out["post_alta_4d"] = out["post"] * out["alta_exp_4d"]

    out["sm_ano"] = out["ano"].astype(int).map(SALARIO_MINIMO)
    out["salario_sm"] = out["salario_medio_adm"] / out["sm_ano"]
    for col in ["salario_medio_adm", "salario_sm"]:
        lo = out[col].quantile(0.01)
        hi = out[col].quantile(0.99)
        lower = max(float(lo), 0.01) if lo <= 0 else float(lo)
        out[col] = out[col].clip(lower=lower, upper=hi)
    out["ln_salario_adm"] = np.log(out["salario_medio_adm"].clip(lower=1))
    out["ln_salario_sm"] = np.log(out["salario_sm"].clip(lower=0.1))

    return out


def estimate_stage2(df: pd.DataFrame, spec: str, model_label: str, treat_col: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for outcome, label in STAGE2_OUTCOMES.items():
        d = df[df[outcome].notna()].copy()
        formula = (
            f"{outcome} ~ {treat_col} + idade_media_adm + pct_mulher_adm + pct_superior_adm "
            f"| cbo_4d + periodo"
        )
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        coef = float(model.coef().loc[treat_col])
        se = float(model.se().loc[treat_col])
        p_value = float(model.pvalue().loc[treat_col])
        rows.append(
            {
                "stage": "stage2_did",
                "spec": spec,
                "model": model_label,
                "outcome": outcome,
                "outcome_label": label,
                "coef": coef,
                "se": se,
                "p_value": p_value,
                "stars": stars(p_value),
                "n_obs": len(d),
                "n_cbo": d["cbo_4d"].nunique(),
            }
        )
    return rows


def read_new_stage2_results() -> list[dict[str, object]]:
    df = pd.read_csv(STAGE2_NEW_RESULTS)
    keep = df[df["model"].isin(["Model 3: FE + Controls (MAIN)", "Model 5: FE + Controls (4d)"])].copy()
    rows: list[dict[str, object]] = []
    for _, row in keep.iterrows():
        model_label = "main_2d" if "MAIN" in row["model"] else "robust_4d"
        rows.append(
            {
                "stage": "stage2_did",
                "spec": "after_mte",
                "model": model_label,
                "outcome": row["outcome"],
                "outcome_label": STAGE2_OUTCOMES.get(row["outcome"], row["outcome"]),
                "coef": float(row["coef"]),
                "se": float(row["se"]),
                "p_value": float(row["p_value"]),
                "stars": clean_stars(row.get("stars", "")),
                "n_obs": int(row["n_obs"]),
                "n_cbo": 436,
            }
        )
    return rows


def estimate_stage3(df: pd.DataFrame, spec: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for outcome, label in STAGE3_OUTCOMES.items():
        if outcome not in df.columns:
            continue
        d = df[df[outcome].notna()].copy()
        formula = (
            f"{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect "
            f"| cbo_4d + uf_periodo"
        )
        model = pf.feols(formula, data=d, vcov={"CRV1": "id_municipio"})
        if "triple_did" not in model.coef().index:
            continue
        coef = float(model.coef().loc["triple_did"])
        se = float(model.se().loc["triple_did"])
        p_value = float(model.pvalue().loc["triple_did"])
        rows.append(
            {
                "stage": "stage3_triple_did",
                "spec": spec,
                "outcome": outcome,
                "outcome_label": label,
                "coef": coef,
                "se": se,
                "p_value": p_value,
                "stars": stars(p_value),
                "n_obs": len(d),
                "n_cbo": d["cbo_4d"].nunique(),
                "n_municipios": d["id_municipio"].nunique(),
            }
        )
    return rows


def read_new_stage3_results() -> list[dict[str, object]]:
    df = pd.read_csv(STAGE3_NEW_RESULTS)
    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "stage": "stage3_triple_did",
                "spec": "after_mte",
                "outcome": row["outcome"],
                "outcome_label": STAGE3_OUTCOMES.get(row["outcome"], row["outcome"]),
                "coef": float(row["coef"]),
                "se": float(row["se"]),
                "p_value": float(row["p_value"]),
                "stars": clean_stars(row.get("stars", stars(float(row["p_value"])))),
                "n_obs": np.nan,
                "n_cbo": 432,
                "n_municipios": 657,
            }
        )
    return rows


def prepare_stage3_common_old(df_new: pd.DataFrame) -> pd.DataFrame:
    out = df_new.copy()
    out["score_old"] = out["exposure_score_2d_old"]
    scores = out.groupby("cbo_4d")["score_old"].first().dropna()
    threshold = scores.quantile(0.80)
    out["alta_exp"] = (out["score_old"] >= threshold).astype(int)
    out["post_alta_exp"] = out["post"] * out["alta_exp"]
    out["alta_exp_alta_conect"] = out["alta_exp"] * out["alta_conectividade"]
    out["triple_did"] = out["post"] * out["alta_exp"] * out["alta_conectividade"]
    return out


def build_sample_comparison(crosswalk: pd.DataFrame, stage3_old: pd.DataFrame, stage3_new: pd.DataFrame) -> pd.DataFrame:
    old_total_adm = crosswalk["admissoes"].sum()
    mte_mask = crosswalk["exposure_score_2d"].notna()
    rows = [
        {
            "level": "stage2_cbo_month",
            "spec": "before_old_numeric",
            "rows": len(crosswalk),
            "cbo": crosswalk["cbo_4d"].nunique(),
            "admissoes": old_total_adm,
            "admissoes_pct": 1.0,
        },
        {
            "level": "stage2_cbo_month",
            "spec": "after_mte",
            "rows": int(mte_mask.sum()),
            "cbo": crosswalk.loc[mte_mask, "cbo_4d"].nunique(),
            "admissoes": crosswalk.loc[mte_mask, "admissoes"].sum(),
            "admissoes_pct": crosswalk.loc[mte_mask, "admissoes"].sum() / old_total_adm,
        },
        {
            "level": "stage3_municipal",
            "spec": "before_old_numeric_v2",
            "rows": len(stage3_old),
            "cbo": stage3_old["cbo_4d"].nunique(),
            "admissoes": stage3_old["admissoes"].sum(),
            "admissoes_pct": 1.0,
        },
        {
            "level": "stage3_municipal",
            "spec": "after_mte",
            "rows": len(stage3_new),
            "cbo": stage3_new["cbo_4d"].nunique(),
            "admissoes": stage3_new["admissoes"].sum(),
            "admissoes_pct": stage3_new["admissoes"].sum() / stage3_old["admissoes"].sum(),
        },
    ]
    return pd.DataFrame(rows)


def build_classification_comparison(crosswalk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cbo = (
        crosswalk.groupby("cbo_4d")
        .agg(
            cbo_2d=("cbo_2d", "first"),
            score_old=("exposure_score_2d_old", "first"),
            score_mte=("exposure_score_2d", "first"),
            admissoes=("admissoes", "sum"),
            mte_match_status=("mte_match_status", "first"),
        )
        .reset_index()
    )
    cbo["cbo_4d"] = cbo["cbo_4d"].astype(str).str.zfill(4)
    old_threshold = cbo["score_old"].quantile(0.80)
    mte_threshold = cbo.loc[cbo["score_mte"].notna(), "score_mte"].quantile(0.80)
    cbo["high_old"] = (cbo["score_old"] >= old_threshold).astype(int)
    cbo["high_mte"] = np.where(cbo["score_mte"].notna(), (cbo["score_mte"] >= mte_threshold).astype(int), np.nan)
    cbo["abs_score_diff"] = (cbo["score_old"] - cbo["score_mte"]).abs()
    if OLD_VS_MTE_COMPARISON.exists():
        title_cols = [
            "cbo_4d",
            "source_cbo_title",
            "source_cbo_2d_title",
            "old_target_2d_title",
            "mte_target_isco08_2d_titles",
            "mte_target_isco08_titles",
        ]
        titles = pd.read_csv(OLD_VS_MTE_COMPARISON, usecols=title_cols)
        titles["cbo_4d"] = titles["cbo_4d"].astype(str).str.zfill(4)
        cbo = cbo.merge(titles.drop_duplicates("cbo_4d"), on="cbo_4d", how="left")

    matched = cbo[cbo["score_mte"].notna()].copy()
    changed = matched[matched["high_old"] != matched["high_mte"]].copy()

    summary = pd.DataFrame(
        [
            {
                "metric": "matched_cbo",
                "value": len(matched),
                "admissoes": matched["admissoes"].sum(),
                "share_admissoes_matched": matched["admissoes"].sum() / cbo["admissoes"].sum(),
            },
            {
                "metric": "classification_changed_among_matched",
                "value": len(changed),
                "admissoes": changed["admissoes"].sum(),
                "share_admissoes_matched": changed["admissoes"].sum() / matched["admissoes"].sum(),
            },
            {
                "metric": "score_abs_diff_ge_0_05_among_matched",
                "value": int((matched["abs_score_diff"] >= 0.05).sum()),
                "admissoes": matched.loc[matched["abs_score_diff"] >= 0.05, "admissoes"].sum(),
                "share_admissoes_matched": matched.loc[matched["abs_score_diff"] >= 0.05, "admissoes"].sum() / matched["admissoes"].sum(),
            },
            {
                "metric": "score_abs_diff_ge_0_10_among_matched",
                "value": int((matched["abs_score_diff"] >= 0.10).sum()),
                "admissoes": matched.loc[matched["abs_score_diff"] >= 0.10, "admissoes"].sum(),
                "share_admissoes_matched": matched.loc[matched["abs_score_diff"] >= 0.10, "admissoes"].sum() / matched["admissoes"].sum(),
            },
        ]
    )
    return cbo, summary


def build_top_classification_tables(cbo_classification: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base_cols = [
        "cbo_4d",
        "source_cbo_title",
        "source_cbo_2d_title",
        "score_old",
        "score_mte",
        "abs_score_diff",
        "high_old",
        "high_mte",
        "mte_match_status",
        "old_target_2d_title",
        "mte_target_isco08_2d_titles",
        "admissoes",
    ]
    available_cols = [col for col in base_cols if col in cbo_classification.columns]
    matched = cbo_classification[cbo_classification["score_mte"].notna()].copy()
    changed = matched[matched["high_old"] != matched["high_mte"]].sort_values(
        "admissoes", ascending=False
    )
    shifted = matched.sort_values(["abs_score_diff", "admissoes"], ascending=False)
    unmatched = cbo_classification[cbo_classification["score_mte"].isna()].sort_values(
        "admissoes", ascending=False
    )
    return {
        "treatment_changed_top": changed[available_cols].head(25),
        "score_shift_top": shifted[available_cols].head(25),
        "unmatched_top": unmatched[available_cols].head(25),
    }


def add_comparison_columns(df: pd.DataFrame, baseline_spec: str, after_spec: str, keys: list[str]) -> pd.DataFrame:
    baseline = df[df["spec"] == baseline_spec]
    after = df[df["spec"] == after_spec]
    merged = baseline.merge(after, on=keys, suffixes=("_before", "_after"))
    merged["delta_coef"] = merged["coef_after"] - merged["coef_before"]
    merged["abs_delta_coef"] = merged["delta_coef"].abs()
    merged["sign_changed"] = np.sign(merged["coef_before"]) != np.sign(merged["coef_after"])
    return merged


def write_report(
    sample: pd.DataFrame,
    class_summary: pd.DataFrame,
    stage2: pd.DataFrame,
    stage2_change: pd.DataFrame,
    stage2_change_common: pd.DataFrame,
    stage3: pd.DataFrame,
    stage3_change: pd.DataFrame,
    stage3_change_common: pd.DataFrame,
    top_tables: dict[str, pd.DataFrame],
) -> None:
    mte_summary = pd.read_csv(MTE_SUMMARY)
    coverage_rows = mte_summary[mte_summary["section"].isin(["coverage", "mte_status"])].copy()

    stage2_main = stage2[stage2["model"] == "main_2d"].copy()
    stage2_main_display = stage2_main.assign(
        stars=stage2_main["stars"].map(clean_stars),
        coef_fmt=stage2_main["coef"].map(lambda x: fmt(x)),
        se_fmt=stage2_main["se"].map(lambda x: fmt(x)),
        p_fmt=stage2_main["p_value"].map(lambda x: fmt(x, 3)),
        n_obs_fmt=stage2_main["n_obs"].map(lambda x: fmt(int(x))),
    )
    stage3_display = stage3.assign(
        stars=stage3["stars"].map(clean_stars),
        coef_fmt=stage3["coef"].map(lambda x: fmt(x)),
        se_fmt=stage3["se"].map(lambda x: fmt(x)),
        p_fmt=stage3["p_value"].map(lambda x: fmt(x, 3)),
    )

    stage2_change_display = stage2_change.assign(
        coef_before_fmt=stage2_change["coef_before"].map(lambda x: fmt(x)),
        coef_after_fmt=stage2_change["coef_after"].map(lambda x: fmt(x)),
        delta_fmt=stage2_change["delta_coef"].map(lambda x: fmt(x)),
        p_before_fmt=stage2_change["p_value_before"].map(lambda x: fmt(x, 3)),
        p_after_fmt=stage2_change["p_value_after"].map(lambda x: fmt(x, 3)),
    )
    stage3_change_display = stage3_change.assign(
        coef_before_fmt=stage3_change["coef_before"].map(lambda x: fmt(x)),
        coef_after_fmt=stage3_change["coef_after"].map(lambda x: fmt(x)),
        delta_fmt=stage3_change["delta_coef"].map(lambda x: fmt(x)),
        p_before_fmt=stage3_change["p_value_before"].map(lambda x: fmt(x, 3)),
        p_after_fmt=stage3_change["p_value_after"].map(lambda x: fmt(x, 3)),
    )
    stage2_change_common_display = stage2_change_common.assign(
        coef_before_fmt=stage2_change_common["coef_before"].map(lambda x: fmt(x)),
        coef_after_fmt=stage2_change_common["coef_after"].map(lambda x: fmt(x)),
        delta_fmt=stage2_change_common["delta_coef"].map(lambda x: fmt(x)),
        p_before_fmt=stage2_change_common["p_value_before"].map(lambda x: fmt(x, 3)),
        p_after_fmt=stage2_change_common["p_value_after"].map(lambda x: fmt(x, 3)),
    )
    stage3_change_common_display = stage3_change_common.assign(
        coef_before_fmt=stage3_change_common["coef_before"].map(lambda x: fmt(x)),
        coef_after_fmt=stage3_change_common["coef_after"].map(lambda x: fmt(x)),
        delta_fmt=stage3_change_common["delta_coef"].map(lambda x: fmt(x)),
        p_before_fmt=stage3_change_common["p_value_before"].map(lambda x: fmt(x, 3)),
        p_after_fmt=stage3_change_common["p_value_after"].map(lambda x: fmt(x, 3)),
    )

    sample_display = sample.assign(
        rows_fmt=sample["rows"].map(lambda x: fmt(int(x))),
        cbo_fmt=sample["cbo"].map(lambda x: fmt(int(x))),
        admissoes_fmt=sample["admissoes"].map(lambda x: fmt(int(round(x)))),
        admissoes_pct_fmt=sample["admissoes_pct"].map(lambda x: pct(x)),
    )
    class_display = class_summary.assign(
        value_fmt=class_summary["value"].map(lambda x: fmt(int(x))),
        admissoes_fmt=class_summary["admissoes"].map(lambda x: fmt(int(round(x)))),
        share_fmt=class_summary["share_admissoes_matched"].map(lambda x: pct(x)),
    )
    top_changed = top_tables["treatment_changed_top"].copy()
    if not top_changed.empty:
        top_changed = top_changed.assign(
            score_old_fmt=top_changed["score_old"].map(lambda x: fmt(x, 3)),
            score_mte_fmt=top_changed["score_mte"].map(lambda x: fmt(x, 3)),
            abs_score_diff_fmt=top_changed["abs_score_diff"].map(lambda x: fmt(x, 3)),
            admissoes_fmt=top_changed["admissoes"].map(lambda x: fmt(int(round(x)))),
            tratamento_antigo=top_changed["high_old"].map(lambda x: "alto" if int(x) == 1 else "baixo"),
            tratamento_mte=top_changed["high_mte"].map(lambda x: "alto" if int(x) == 1 else "baixo"),
        )
    top_unmatched = top_tables["unmatched_top"].copy()
    if not top_unmatched.empty:
        top_unmatched = top_unmatched.assign(
            score_old_fmt=top_unmatched["score_old"].map(lambda x: fmt(x, 3)),
            admissoes_fmt=top_unmatched["admissoes"].map(lambda x: fmt(int(round(x)))),
        )

    text = f"""# Comparação Antes e Depois do Crosswalk MTE

## Leitura curta

Sim, os resultados mudam, mas a mudança não é uniforme. O novo crosswalk MTE altera três coisas ao mesmo tempo: a cobertura da amostra, o score de exposição e a classificação de tratamento.

Na Etapa 2, a mudança é substantiva: o efeito em salário de admissão deixa de ser significativo, `ln_admissoes` fica mais negativo e passa a ser marginalmente significativo, e `ln_desligamentos` muda de sinal. Na Etapa 3, a história é diferente: os sinais e a significância são bastante estáveis. A diferença entre a amostra antiga completa e o MTE vem mais da retirada das ocupações sem ponte oficial do que de uma virada causada pelo novo score entre os CBOs pareados.

## Cobertura e amostra

{markdown_table(sample_display, ["level", "spec", "rows_fmt", "cbo_fmt", "admissoes_fmt", "admissoes_pct_fmt"])}

## Auditoria do crosswalk

{markdown_table(coverage_rows, ["section", "metric", "codes", "codes_pct", "panel_rows", "panel_rows_pct", "admissoes_total", "admissoes_pct"])}

## Mudança de classificação de tratamento

{markdown_table(class_display, ["metric", "value_fmt", "admissoes_fmt", "share_fmt"])}

Entre os CBOs com match MTE, 37 mudam de classificação de tratamento alto/baixo. Eles representam 4,51% das admissões pareadas. O score muda em pelo menos 0,05 para 37,53% das admissões pareadas, então o crosswalk novo não é uma troca neutra de nomes.

Principais CBOs que mudam de grupo de tratamento, ordenados por admissões:

{markdown_table(top_changed.head(15), ["cbo_4d", "source_cbo_title", "score_old_fmt", "score_mte_fmt", "abs_score_diff_fmt", "tratamento_antigo", "tratamento_mte", "admissoes_fmt"])}

Maiores CBOs sem match oficial MTE:

{markdown_table(top_unmatched.head(15), ["cbo_4d", "source_cbo_title", "score_old_fmt", "mte_match_status", "admissoes_fmt"])}

## Etapa 2: DiD ocupação-mês

Tabela com a especificação principal, `Model 3: FE + Controls`, para três versões:

- `before_old_full`: crosswalk antigo, amostra completa antiga.
- `before_old_common`: crosswalk antigo, mas restrito à amostra com match MTE.
- `after_mte`: crosswalk novo MTE.

{markdown_table(stage2_main_display, ["spec", "outcome_label", "coef_fmt", "se_fmt", "p_fmt", "stars", "n_obs_fmt"])}

Mudança direta entre `before_old_full` e `after_mte`:

{markdown_table(stage2_change_display, ["outcome_label_before", "coef_before_fmt", "p_before_fmt", "coef_after_fmt", "p_after_fmt", "delta_fmt", "sign_changed"])}

Mudança isolando a amostra comum, isto é, `before_old_common` contra `after_mte`:

{markdown_table(stage2_change_common_display, ["outcome_label_before", "coef_before_fmt", "p_before_fmt", "coef_after_fmt", "p_after_fmt", "delta_fmt", "sign_changed"])}

## Etapa 3: Triple-DiD municipal

{markdown_table(stage3_display, ["spec", "outcome_label", "coef_fmt", "se_fmt", "p_fmt", "stars"])}

Mudança direta entre `before_old_full_v2` e `after_mte`:

{markdown_table(stage3_change_display, ["outcome_label_before", "coef_before_fmt", "p_before_fmt", "coef_after_fmt", "p_after_fmt", "delta_fmt", "sign_changed"])}

Mudança isolando a amostra comum:

{markdown_table(stage3_change_common_display, ["outcome_label_before", "coef_before_fmt", "p_before_fmt", "coef_after_fmt", "p_after_fmt", "delta_fmt", "sign_changed"])}

## Interpretação

O resultado principal é que o novo crosswalk não só remove falsos matches: ele redefine quem é tratado e reduz a amostra para ocupações com ponte oficial. A Etapa 2 é mais sensível à mudança de crosswalk. A Etapa 3 parece mais robusta nos sinais e na significância, mas a amostra MTE muda o nível de alguns coeficientes.

Para escrever a dissertação, eu trataria a especificação MTE como principal, mas apresentaria o crosswalk antigo como benchmark. Também destacaria que a comparação `before_old_common` ajuda a separar mudança de score de mudança de amostra.
"""
    (OUTPUT_DIR / "before_after_crosswalk_results.md").write_text(text, encoding="utf-8")


def main() -> None:
    crosswalk = pd.read_parquet(CROSSWALK_PANEL)
    crosswalk = crosswalk.rename(
        columns={
            "exposure_score_2d_old": "exposure_score_2d_old",
            "exposure_score_4d_old": "exposure_score_4d_old",
        }
    )
    if not {"exposure_score_2d_old", "exposure_score_4d_old", "exposure_score_2d"}.issubset(crosswalk.columns):
        raise RuntimeError("Crosswalk panel must contain old and MTE exposure score columns.")

    stage2_rows: list[dict[str, object]] = []
    before_full = prepare_stage2_panel(crosswalk, "old", "full")
    before_common = prepare_stage2_panel(crosswalk, "old", "common_mte_matched")
    stage2_rows.extend(estimate_stage2(before_full, "before_old_full", "main_2d", "post_alta"))
    stage2_rows.extend(estimate_stage2(before_full, "before_old_full", "robust_4d", "post_alta_4d"))
    stage2_rows.extend(estimate_stage2(before_common, "before_old_common", "main_2d", "post_alta"))
    stage2_rows.extend(estimate_stage2(before_common, "before_old_common", "robust_4d", "post_alta_4d"))
    stage2_rows.extend(read_new_stage2_results())
    stage2 = pd.DataFrame(stage2_rows)
    stage2.to_csv(OUTPUT_DIR / "stage2_did_before_after.csv", index=False)

    print("Stage 2 comparison estimated.")

    stage3_old = pd.read_parquet(STAGE3_OLD)
    stage3_new = pd.read_parquet(STAGE3_NEW)
    if "crosswalk_spec" not in stage3_new.columns or set(stage3_new["crosswalk_spec"].dropna().unique()) != {EXPECTED_SPEC}:
        raise RuntimeError("Stage 3 new panel does not use the expected MTE crosswalk spec.")

    stage3_rows: list[dict[str, object]] = []
    stage3_rows.extend(estimate_stage3(stage3_old, "before_old_full_v2"))
    print("Stage 3 old full comparison estimated.")
    stage3_old_common = prepare_stage3_common_old(stage3_new)
    stage3_rows.extend(estimate_stage3(stage3_old_common, "before_old_common"))
    print("Stage 3 old common-sample comparison estimated.")
    stage3_rows.extend(read_new_stage3_results())
    stage3 = pd.DataFrame(stage3_rows)
    stage3.to_csv(OUTPUT_DIR / "stage3_triple_did_before_after.csv", index=False)

    sample = build_sample_comparison(crosswalk, stage3_old, stage3_new)
    sample.to_csv(OUTPUT_DIR / "sample_before_after.csv", index=False)
    cbo_classification, class_summary = build_classification_comparison(crosswalk)
    cbo_classification.to_csv(OUTPUT_DIR / "cbo_treatment_classification_before_after.csv", index=False)
    class_summary.to_csv(OUTPUT_DIR / "classification_summary.csv", index=False)

    stage2_change = add_comparison_columns(
        stage2[stage2["model"] == "main_2d"],
        "before_old_full",
        "after_mte",
        ["stage", "model", "outcome"],
    )
    stage2_change.to_csv(OUTPUT_DIR / "stage2_main_before_full_vs_after_mte.csv", index=False)
    stage2_change_common = add_comparison_columns(
        stage2[stage2["model"] == "main_2d"],
        "before_old_common",
        "after_mte",
        ["stage", "model", "outcome"],
    )
    stage2_change_common.to_csv(
        OUTPUT_DIR / "stage2_main_before_common_vs_after_mte.csv", index=False
    )
    stage3_change = add_comparison_columns(
        stage3,
        "before_old_full_v2",
        "after_mte",
        ["stage", "outcome"],
    )
    stage3_change.to_csv(OUTPUT_DIR / "stage3_before_full_vs_after_mte.csv", index=False)
    stage3_change_common = add_comparison_columns(
        stage3,
        "before_old_common",
        "after_mte",
        ["stage", "outcome"],
    )
    stage3_change_common.to_csv(OUTPUT_DIR / "stage3_before_common_vs_after_mte.csv", index=False)

    top_tables = build_top_classification_tables(cbo_classification)
    for name, table in top_tables.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)

    write_report(
        sample,
        class_summary,
        stage2,
        stage2_change,
        stage2_change_common,
        stage3,
        stage3_change,
        stage3_change_common,
        top_tables,
    )
    print(f"Comparison report written to {OUTPUT_DIR / 'before_after_crosswalk_results.md'}")


if __name__ == "__main__":
    main()
