#!/usr/bin/env python3
"""
Compare alternative treatment/control definitions using the current MTE crosswalk.

The exposure score remains the ILO score imputed to Brazilian CBO occupations
through the official MTE bridge. Only the binary split changes:

1. Current: top 20% vs all remaining occupations.
2. Alternative A: top 20% vs bottom 40%, dropping the middle 40%.
3. Alternative B: top 20% vs bottom 20%, dropping the middle 60%.
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
DATA_OUTPUT = ROOT / "data" / "output"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_DIR = ROOT / "outputs" / "treatment_group_strategy_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STAGE2_PANEL = DATA_OUTPUT / "painel_2b_ready.parquet"
STAGE3_PANEL = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
CURRENT_STAGE2_RESULTS = OUTPUT_TABLES / "did_main_results.csv"
CURRENT_STAGE3_RESULTS = OUTPUT_TABLES / "triple_did_main_etapa3b.csv"

EXPECTED_SPEC = "mte_official_no_numeric_fallback"

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

STRATEGIES = {
    "current_top20_vs_rest": {
        "label": "Atual: top 20% vs resto",
        "control_quantile": None,
        "middle_dropped": "0%",
    },
    "top20_vs_bottom40": {
        "label": "Top 20% vs bottom 40%",
        "control_quantile": 0.40,
        "middle_dropped": "40%",
    },
    "top20_vs_bottom20": {
        "label": "Top 20% vs bottom 20%",
        "control_quantile": 0.20,
        "middle_dropped": "60%",
    },
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


def validate_panel(df: pd.DataFrame, name: str) -> None:
    if "crosswalk_spec" not in df.columns:
        raise RuntimeError(f"{name} does not contain crosswalk_spec.")
    specs = set(df["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_SPEC}:
        raise RuntimeError(f"{name} must use {EXPECTED_SPEC}; found {specs}.")
    if df["exposure_score_2d"].isna().any():
        raise RuntimeError(f"{name} contains missing MTE exposure scores.")


def treatment_thresholds(stage2: pd.DataFrame) -> dict[str, float]:
    scores = stage2.groupby("cbo_4d")["exposure_score_2d"].first().dropna()
    return {
        "q20": float(scores.quantile(0.20)),
        "q40": float(scores.quantile(0.40)),
        "q80": float(scores.quantile(0.80)),
        "n_cbo": int(scores.shape[0]),
    }


def assign_strategy(df: pd.DataFrame, strategy: str, thresholds: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    if strategy == "current_top20_vs_rest":
        out["strategy_treatment"] = out["alta_exp"].astype(int)
        out["post_strategy_treatment"] = out["post"] * out["strategy_treatment"]
        return out

    control_quantile = STRATEGIES[strategy]["control_quantile"]
    if control_quantile == 0.40:
        control_cutoff = thresholds["q40"]
    elif control_quantile == 0.20:
        control_cutoff = thresholds["q20"]
    else:
        raise ValueError(f"Unsupported strategy: {strategy}")

    score = out["exposure_score_2d"]
    treated = score >= thresholds["q80"]
    control = score <= control_cutoff
    out = out[treated | control].copy()
    out["strategy_treatment"] = np.where(out["exposure_score_2d"] >= thresholds["q80"], 1, 0)
    out["post_strategy_treatment"] = out["post"] * out["strategy_treatment"]
    return out


def sample_stats(stage: str, df_base: pd.DataFrame, strategy: str, thresholds: dict[str, float]) -> dict[str, object]:
    df = assign_strategy(df_base, strategy, thresholds)
    total_admissions = df_base["admissoes"].sum()
    cbo_level = df.groupby("cbo_4d").agg(
        treatment=("strategy_treatment", "first"),
        score=("exposure_score_2d", "first"),
        admissoes=("admissoes", "sum"),
    )
    return {
        "stage": stage,
        "strategy": strategy,
        "strategy_label": STRATEGIES[strategy]["label"],
        "rows": int(len(df)),
        "rows_pct_of_current_mte": len(df) / len(df_base),
        "cbo": int(df["cbo_4d"].nunique()),
        "treated_cbo": int((cbo_level["treatment"] == 1).sum()),
        "control_cbo": int((cbo_level["treatment"] == 0).sum()),
        "dropped_cbo": int(df_base["cbo_4d"].nunique() - df["cbo_4d"].nunique()),
        "admissoes": float(df["admissoes"].sum()),
        "admissoes_pct_of_current_mte": float(df["admissoes"].sum() / total_admissions),
        "mean_score_treated": float(cbo_level.loc[cbo_level["treatment"] == 1, "score"].mean()),
        "mean_score_control": float(cbo_level.loc[cbo_level["treatment"] == 0, "score"].mean()),
        "score_gap": float(
            cbo_level.loc[cbo_level["treatment"] == 1, "score"].mean()
            - cbo_level.loc[cbo_level["treatment"] == 0, "score"].mean()
        ),
    }


def estimate_stage2(df: pd.DataFrame, strategy: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for outcome, label in STAGE2_OUTCOMES.items():
        d = df[df[outcome].notna()].copy()
        formula = (
            f"{outcome} ~ post_strategy_treatment + idade_media_adm + pct_mulher_adm + pct_superior_adm "
            f"| cbo_4d + periodo"
        )
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        rows.append(
            {
                "stage": "stage2_did",
                "strategy": strategy,
                "strategy_label": STRATEGIES[strategy]["label"],
                "outcome": outcome,
                "outcome_label": label,
                "coef": float(model.coef().loc["post_strategy_treatment"]),
                "se": float(model.se().loc["post_strategy_treatment"]),
                "p_value": float(model.pvalue().loc["post_strategy_treatment"]),
                "stars": stars(float(model.pvalue().loc["post_strategy_treatment"])),
                "n_obs": int(len(d)),
                "n_cbo": int(d["cbo_4d"].nunique()),
            }
        )
    return rows


def read_current_stage2() -> pd.DataFrame:
    current = pd.read_csv(CURRENT_STAGE2_RESULTS)
    current = current[current["model"] == "Model 3: FE + Controls (MAIN)"].copy()
    rows = []
    for _, row in current.iterrows():
        rows.append(
            {
                "stage": "stage2_did",
                "strategy": "current_top20_vs_rest",
                "strategy_label": STRATEGIES["current_top20_vs_rest"]["label"],
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
    return pd.DataFrame(rows)


def estimate_stage3(df: pd.DataFrame, strategy: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    d = df.copy()
    d["post_strategy_exp"] = d["post"] * d["strategy_treatment"]
    d["strategy_exp_high_connect"] = d["strategy_treatment"] * d["alta_conectividade"]
    d["triple_strategy"] = d["post"] * d["strategy_treatment"] * d["alta_conectividade"]

    for outcome, label in STAGE3_OUTCOMES.items():
        if outcome not in d.columns:
            continue
        dx = d[d[outcome].notna()].copy()
        formula = (
            f"{outcome} ~ triple_strategy + post_strategy_exp + post_alta_conect + "
            f"strategy_exp_high_connect | cbo_4d + uf_periodo"
        )
        model = pf.feols(formula, data=dx, vcov={"CRV1": "id_municipio"})
        rows.append(
            {
                "stage": "stage3_triple_did",
                "strategy": strategy,
                "strategy_label": STRATEGIES[strategy]["label"],
                "outcome": outcome,
                "outcome_label": label,
                "coef": float(model.coef().loc["triple_strategy"]),
                "se": float(model.se().loc["triple_strategy"]),
                "p_value": float(model.pvalue().loc["triple_strategy"]),
                "stars": stars(float(model.pvalue().loc["triple_strategy"])),
                "n_obs": int(len(dx)),
                "n_cbo": int(dx["cbo_4d"].nunique()),
                "n_municipios": int(dx["id_municipio"].nunique()),
            }
        )
    return rows


def read_current_stage3(stage3_panel: pd.DataFrame) -> pd.DataFrame:
    current = pd.read_csv(CURRENT_STAGE3_RESULTS)
    rows = []
    for _, row in current.iterrows():
        outcome = row["outcome"]
        d = stage3_panel[stage3_panel[outcome].notna()].copy()
        rows.append(
            {
                "stage": "stage3_triple_did",
                "strategy": "current_top20_vs_rest",
                "strategy_label": STRATEGIES["current_top20_vs_rest"]["label"],
                "outcome": outcome,
                "outcome_label": STAGE3_OUTCOMES.get(outcome, outcome),
                "coef": float(row["coef"]),
                "se": float(row["se"]),
                "p_value": float(row["p_value"]),
                "stars": stars(float(row["p_value"])),
                "n_obs": int(len(d)),
                "n_cbo": int(d["cbo_4d"].nunique()),
                "n_municipios": int(d["id_municipio"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def comparison_against_current(results: pd.DataFrame) -> pd.DataFrame:
    current = results[results["strategy"] == "current_top20_vs_rest"].copy()
    alternatives = results[results["strategy"] != "current_top20_vs_rest"].copy()
    merged = alternatives.merge(
        current,
        on=["stage", "outcome"],
        suffixes=("_alternative", "_current"),
    )
    merged["delta_coef_vs_current"] = merged["coef_alternative"] - merged["coef_current"]
    merged["abs_delta_coef_vs_current"] = merged["delta_coef_vs_current"].abs()
    merged["sign_changed_vs_current"] = (
        np.sign(merged["coef_alternative"]) != np.sign(merged["coef_current"])
    )
    return merged


def display_results(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        coef_fmt=df["coef"].map(lambda x: fmt(x)),
        se_fmt=df["se"].map(lambda x: fmt(x)),
        p_fmt=df["p_value"].map(lambda x: fmt(x, 3)),
        stars=df["stars"].map(clean_stars),
        n_obs_fmt=df["n_obs"].map(lambda x: fmt(int(x))),
        n_cbo_fmt=df["n_cbo"].map(lambda x: fmt(int(x))),
    )


def display_sample(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        rows_fmt=df["rows"].map(lambda x: fmt(int(x))),
        rows_pct_fmt=df["rows_pct_of_current_mte"].map(lambda x: pct(x)),
        cbo_fmt=df["cbo"].map(lambda x: fmt(int(x))),
        treated_cbo_fmt=df["treated_cbo"].map(lambda x: fmt(int(x))),
        control_cbo_fmt=df["control_cbo"].map(lambda x: fmt(int(x))),
        dropped_cbo_fmt=df["dropped_cbo"].map(lambda x: fmt(int(x))),
        admissoes_fmt=df["admissoes"].map(lambda x: fmt(int(round(x)))),
        admissoes_pct_fmt=df["admissoes_pct_of_current_mte"].map(lambda x: pct(x)),
        mean_score_treated_fmt=df["mean_score_treated"].map(lambda x: fmt(x, 3)),
        mean_score_control_fmt=df["mean_score_control"].map(lambda x: fmt(x, 3)),
        score_gap_fmt=df["score_gap"].map(lambda x: fmt(x, 3)),
    )


def write_report(
    thresholds: dict[str, float],
    sample: pd.DataFrame,
    stage2_results: pd.DataFrame,
    stage3_results: pd.DataFrame,
    stage2_comparison: pd.DataFrame,
    stage3_comparison: pd.DataFrame,
) -> None:
    sample_display = display_sample(sample)
    stage2_display = display_results(stage2_results)
    stage3_display = display_results(stage3_results)

    stage2_comp = stage2_comparison.assign(
        coef_current_fmt=stage2_comparison["coef_current"].map(lambda x: fmt(x)),
        p_current_fmt=stage2_comparison["p_value_current"].map(lambda x: fmt(x, 3)),
        coef_alt_fmt=stage2_comparison["coef_alternative"].map(lambda x: fmt(x)),
        p_alt_fmt=stage2_comparison["p_value_alternative"].map(lambda x: fmt(x, 3)),
        delta_fmt=stage2_comparison["delta_coef_vs_current"].map(lambda x: fmt(x)),
    )
    stage3_comp = stage3_comparison.assign(
        coef_current_fmt=stage3_comparison["coef_current"].map(lambda x: fmt(x)),
        p_current_fmt=stage3_comparison["p_value_current"].map(lambda x: fmt(x, 3)),
        coef_alt_fmt=stage3_comparison["coef_alternative"].map(lambda x: fmt(x)),
        p_alt_fmt=stage3_comparison["p_value_alternative"].map(lambda x: fmt(x, 3)),
        delta_fmt=stage3_comparison["delta_coef_vs_current"].map(lambda x: fmt(x)),
    )

    text = f"""# Comparação de Estratégias de Tratamento e Controle

## O que foi testado

A fonte da exposição não mudou: todos os modelos usam o score da OIT imputado à CBO via crosswalk oficial MTE. A única coisa que muda é a regra binária para separar tratamento e controle.

- `current_top20_vs_rest`: tratamento = top 20%; controle = demais CBOs.
- `top20_vs_bottom40`: tratamento = top 20%; controle = bottom 40%; CBOs intermediários excluídos.
- `top20_vs_bottom20`: tratamento = top 20%; controle = bottom 20%; CBOs intermediários excluídos.

Os cortes foram calculados sobre CBOs únicos com score MTE válido:

- p20 = {fmt(thresholds["q20"], 6)}
- p40 = {fmt(thresholds["q40"], 6)}
- p80 = {fmt(thresholds["q80"], 6)}

## Tamanho da amostra

{markdown_table(sample_display, ["stage", "strategy_label", "rows_fmt", "rows_pct_fmt", "cbo_fmt", "treated_cbo_fmt", "control_cbo_fmt", "dropped_cbo_fmt", "admissoes_fmt", "admissoes_pct_fmt", "mean_score_treated_fmt", "mean_score_control_fmt", "score_gap_fmt"])}

## Etapa 2: DiD ocupação-mês

{markdown_table(stage2_display, ["strategy_label", "outcome_label", "coef_fmt", "se_fmt", "p_fmt", "stars", "n_obs_fmt", "n_cbo_fmt"])}

Comparação das alternativas contra a especificação atual:

{markdown_table(stage2_comp, ["strategy_label_alternative", "outcome_label_alternative", "coef_current_fmt", "p_current_fmt", "coef_alt_fmt", "p_alt_fmt", "delta_fmt", "sign_changed_vs_current"])}

## Etapa 3: Triple-DiD municipal

{markdown_table(stage3_display, ["strategy_label", "outcome_label", "coef_fmt", "se_fmt", "p_fmt", "stars", "n_obs_fmt", "n_cbo_fmt"])}

Comparação das alternativas contra a especificação atual:

{markdown_table(stage3_comp, ["strategy_label_alternative", "outcome_label_alternative", "coef_current_fmt", "p_current_fmt", "coef_alt_fmt", "p_alt_fmt", "delta_fmt", "sign_changed_vs_current"])}

## Leitura metodológica

A estratégia `top20_vs_bottom40` melhora a separação conceitual entre tratamento e controle sem destruir a amostra. Ela troca a pergunta "alta exposição contra todo o resto" por "alta exposição contra baixa exposição". O custo é perder cerca de um quarto das admissões MTE e deixar a Etapa 2 menos precisa.

A estratégia `top20_vs_bottom20` cria o contraste mais limpo, mas perde muita amostra e deixa os resultados mais dependentes de um subconjunto pequeno de ocupações de baixa exposição.

## Conclusão

Eu não substituiria a especificação atual por nenhuma dessas alternativas como especificação principal.

A especificação atual, `top 20% vs resto`, é melhor como principal porque preserva a amostra, mantém a narrativa mais simples e não depende de excluir ocupações intermediárias. Ela estima a pergunta mais ampla: ocupações muito expostas se comportam de forma diferente das demais?

A especificação `top20_vs_bottom40` é a melhor robustez. Ela aumenta a distância média de exposição entre tratamento e controle, preserva 76,09% das admissões da Etapa 2 e 74,72% da Etapa 3, e mantém os principais resultados da Etapa 3 para admissões, desligamentos, saldo e escolaridade. Porém, ela enfraquece a Etapa 2 e elimina o efeito em salário real na Etapa 3.

A especificação `top20_vs_bottom20` é útil como teste de extremos, mas é agressiva demais para virar principal: mantém só 56,60% das admissões na Etapa 2 e 56,19% na Etapa 3. Ela melhora o contraste estatístico, mas muda bastante o estimando e torna os resultados mais dependentes de uma amostra selecionada.

Minha recomendação é: manter `top 20% vs resto` como principal; adicionar `top 20% vs bottom 40%` como robustez; tratar `top 20% vs bottom 20%` apenas como teste exploratório de extremos, se for usado.
"""
    (OUTPUT_DIR / "treatment_group_strategy_report.md").write_text(text, encoding="utf-8")


def main() -> None:
    stage2 = pd.read_parquet(STAGE2_PANEL)
    stage3 = pd.read_parquet(STAGE3_PANEL)
    for df in [stage2, stage3]:
        df["cbo_4d"] = df["cbo_4d"].astype(str).str.zfill(4)

    validate_panel(stage2, "Stage 2 panel")
    validate_panel(stage3, "Stage 3 panel")

    thresholds = treatment_thresholds(stage2)
    strategies = list(STRATEGIES)

    sample_rows = []
    for stage_name, panel in [("stage2_did", stage2), ("stage3_triple_did", stage3)]:
        for strategy in strategies:
            sample_rows.append(sample_stats(stage_name, panel, strategy, thresholds))
    sample = pd.DataFrame(sample_rows)
    sample.to_csv(OUTPUT_DIR / "treatment_strategy_sample.csv", index=False)

    stage2_rows = [read_current_stage2()]
    for strategy in ["top20_vs_bottom40", "top20_vs_bottom20"]:
        panel = assign_strategy(stage2, strategy, thresholds)
        stage2_rows.append(pd.DataFrame(estimate_stage2(panel, strategy)))
        print(f"Stage 2 estimated: {strategy}")
    stage2_results = pd.concat(stage2_rows, ignore_index=True)
    stage2_results.to_csv(OUTPUT_DIR / "stage2_treatment_strategy_results.csv", index=False)

    stage3_rows = [read_current_stage3(stage3)]
    for strategy in ["top20_vs_bottom40", "top20_vs_bottom20"]:
        panel = assign_strategy(stage3, strategy, thresholds)
        stage3_rows.append(pd.DataFrame(estimate_stage3(panel, strategy)))
        print(f"Stage 3 estimated: {strategy}")
    stage3_results = pd.concat(stage3_rows, ignore_index=True)
    stage3_results.to_csv(OUTPUT_DIR / "stage3_treatment_strategy_results.csv", index=False)

    stage2_comparison = comparison_against_current(stage2_results)
    stage2_comparison.to_csv(OUTPUT_DIR / "stage2_vs_current.csv", index=False)
    stage3_comparison = comparison_against_current(stage3_results)
    stage3_comparison.to_csv(OUTPUT_DIR / "stage3_vs_current.csv", index=False)

    write_report(thresholds, sample, stage2_results, stage3_results, stage2_comparison, stage3_comparison)
    print(f"Report written to {OUTPUT_DIR / 'treatment_group_strategy_report.md'}")


if __name__ == "__main__":
    main()
