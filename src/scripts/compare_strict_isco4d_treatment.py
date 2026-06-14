#!/usr/bin/env python3
"""
Compare a strict ISCO-08 4d consensus treatment definition.

The treatment is not based on the CBO-level average score. Instead, it starts
from the ILO ISCO-08 4d distribution:

1. Compute the top 20% cutoff among ISCO-08 4d occupations.
2. For each CBO, inspect all MTE-derived ISCO-08 4d destinations.
3. Mark the CBO as treated only if every destination is in the ISCO-08 4d top 20%.

Two empirical variants are estimated:
- strict_all4d_top20_vs_rest: treated CBOs vs every other matched CBO.
- strict_all4d_top20_vs_none4d_top20: treated CBOs vs CBOs with no top-20 destination;
  mixed CBOs are dropped.
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
OUTPUT_TABLES = ROOT / "outputs" / "tables"
CROSSWALK_AUDIT = ROOT / "outputs" / "crosswalk_audit" / "official_mte_bridge"
OUTPUT_DIR = ROOT / "outputs" / "strict_isco4d_treatment_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ILO_FILE = DATA_PROCESSED / "ilo_exposure_clean.csv"
BRIDGE_FILE = CROSSWALK_AUDIT / "caged_mte_bridge_full.csv"
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
    "current_mte2d_top20_vs_rest": "Atual: score MTE 2d top 20% vs resto",
    "strict_all4d_top20_vs_rest": "Todos os destinos ISCO-08 4d top 20% vs resto",
    "strict_all4d_top20_vs_none4d_top20": "Todos top 20% vs nenhum destino top 20%",
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


def split_codes(value: object) -> list[str]:
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [code.strip().zfill(4) for code in str(value).split(",") if code.strip()]


def load_strict_classification() -> tuple[pd.DataFrame, float]:
    ilo = pd.read_csv(ILO_FILE)
    ilo["isco_08_str"] = ilo["isco_08_str"].astype(str).str.zfill(4)
    isco4d_cutoff = float(ilo["exposure_score"].quantile(0.80))
    isco_scores = dict(zip(ilo["isco_08_str"], ilo["exposure_score"]))

    bridge = pd.read_csv(BRIDGE_FILE)
    bridge["cbo_4d"] = bridge["cbo_4d"].astype(str).str.zfill(4)
    bridge = bridge[bridge["mte_match_status"] == "matched_official_mte"].copy()
    bridge["target_isco08_codes_list"] = bridge["target_isco08_codes"].map(split_codes)
    bridge["target_scores"] = bridge["target_isco08_codes_list"].map(
        lambda codes: [isco_scores[code] for code in codes if code in isco_scores]
    )

    def classify(scores: list[float]) -> str:
        if not scores:
            return "missing_isco4d_score"
        top_flags = [score >= isco4d_cutoff for score in scores]
        if all(top_flags):
            return "all_destinations_top20"
        if any(top_flags):
            return "mixed_some_top20"
        return "none_top20"

    bridge["strict_isco4d_class"] = bridge["target_scores"].map(classify)
    bridge["strict_isco4d_treat"] = (bridge["strict_isco4d_class"] == "all_destinations_top20").astype(int)
    bridge["any_isco4d_top20"] = bridge["strict_isco4d_class"].isin(
        ["all_destinations_top20", "mixed_some_top20"]
    ).astype(int)
    bridge["n_target_isco08_4d"] = bridge["target_isco08_codes_list"].map(lambda codes: len(set(codes)))
    bridge["min_target_score"] = bridge["target_scores"].map(lambda scores: min(scores) if scores else np.nan)
    bridge["max_target_score"] = bridge["target_scores"].map(lambda scores: max(scores) if scores else np.nan)
    bridge["mean_target_score"] = bridge["target_scores"].map(lambda scores: np.mean(scores) if scores else np.nan)

    keep = [
        "cbo_4d",
        "source_cbo_title",
        "target_isco08_codes",
        "target_isco08_titles",
        "candidate_scores_mte_4d",
        "exposure_score_mte_4d",
        "exposure_score_mte_2d",
        "admissoes_total",
        "panel_rows",
        "strict_isco4d_class",
        "strict_isco4d_treat",
        "any_isco4d_top20",
        "n_target_isco08_4d",
        "min_target_score",
        "max_target_score",
        "mean_target_score",
    ]
    return bridge[keep].copy(), isco4d_cutoff


def validate_panel(df: pd.DataFrame, name: str) -> None:
    if "crosswalk_spec" not in df.columns:
        raise RuntimeError(f"{name} does not contain crosswalk_spec.")
    specs = set(df["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_SPEC}:
        raise RuntimeError(f"{name} must use {EXPECTED_SPEC}; found {specs}.")


def attach_classification(panel: pd.DataFrame, classification: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["cbo_4d"] = out["cbo_4d"].astype(str).str.zfill(4)
    return out.merge(
        classification[
            [
                "cbo_4d",
                "strict_isco4d_class",
                "strict_isco4d_treat",
                "any_isco4d_top20",
                "n_target_isco08_4d",
                "mean_target_score",
            ]
        ],
        on="cbo_4d",
        how="left",
    )


def assign_strategy(panel: pd.DataFrame, strategy: str) -> pd.DataFrame:
    out = panel.copy()
    if strategy == "current_mte2d_top20_vs_rest":
        out["strategy_treat"] = out["alta_exp"].astype(int)
    elif strategy == "strict_all4d_top20_vs_rest":
        out["strategy_treat"] = out["strict_isco4d_treat"].astype(int)
    elif strategy == "strict_all4d_top20_vs_none4d_top20":
        out = out[out["strict_isco4d_class"].isin(["all_destinations_top20", "none_top20"])].copy()
        out["strategy_treat"] = out["strict_isco4d_treat"].astype(int)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    out["post_strategy_treat"] = out["post"] * out["strategy_treat"]
    return out


def sample_stats(stage: str, panel: pd.DataFrame, strategy: str) -> dict[str, object]:
    df = assign_strategy(panel, strategy)
    cbo = df.groupby("cbo_4d").agg(
        treat=("strategy_treat", "first"),
        admissoes=("admissoes", "sum"),
        score_2d=("exposure_score_2d", "first"),
        score_4d=("exposure_score_4d", "first"),
    )
    return {
        "stage": stage,
        "strategy": strategy,
        "strategy_label": STRATEGIES[strategy],
        "rows": int(len(df)),
        "rows_pct": float(len(df) / len(panel)),
        "cbo": int(df["cbo_4d"].nunique()),
        "treated_cbo": int((cbo["treat"] == 1).sum()),
        "control_cbo": int((cbo["treat"] == 0).sum()),
        "dropped_cbo": int(panel["cbo_4d"].nunique() - df["cbo_4d"].nunique()),
        "admissoes": float(df["admissoes"].sum()),
        "admissoes_pct": float(df["admissoes"].sum() / panel["admissoes"].sum()),
        "treated_admissoes": float(cbo.loc[cbo["treat"] == 1, "admissoes"].sum()),
        "treated_admissoes_pct": float(cbo.loc[cbo["treat"] == 1, "admissoes"].sum() / cbo["admissoes"].sum()),
        "mean_score_2d_treated": float(cbo.loc[cbo["treat"] == 1, "score_2d"].mean()),
        "mean_score_2d_control": float(cbo.loc[cbo["treat"] == 0, "score_2d"].mean()),
        "mean_score_4d_treated": float(cbo.loc[cbo["treat"] == 1, "score_4d"].mean()),
        "mean_score_4d_control": float(cbo.loc[cbo["treat"] == 0, "score_4d"].mean()),
    }


def read_current_stage2() -> pd.DataFrame:
    df = pd.read_csv(CURRENT_STAGE2_RESULTS)
    df = df[df["model"] == "Model 3: FE + Controls (MAIN)"].copy()
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "stage": "stage2_did",
                "strategy": "current_mte2d_top20_vs_rest",
                "strategy_label": STRATEGIES["current_mte2d_top20_vs_rest"],
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


def estimate_stage2(panel: pd.DataFrame, strategy: str) -> list[dict[str, object]]:
    df = assign_strategy(panel, strategy)
    rows: list[dict[str, object]] = []
    for outcome, label in STAGE2_OUTCOMES.items():
        d = df[df[outcome].notna()].copy()
        formula = (
            f"{outcome} ~ post_strategy_treat + idade_media_adm + pct_mulher_adm + pct_superior_adm "
            f"| cbo_4d + periodo"
        )
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        rows.append(
            {
                "stage": "stage2_did",
                "strategy": strategy,
                "strategy_label": STRATEGIES[strategy],
                "outcome": outcome,
                "outcome_label": label,
                "coef": float(model.coef().loc["post_strategy_treat"]),
                "se": float(model.se().loc["post_strategy_treat"]),
                "p_value": float(model.pvalue().loc["post_strategy_treat"]),
                "stars": stars(float(model.pvalue().loc["post_strategy_treat"])),
                "n_obs": int(len(d)),
                "n_cbo": int(d["cbo_4d"].nunique()),
            }
        )
    return rows


def read_current_stage3(stage3_panel: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(CURRENT_STAGE3_RESULTS)
    rows = []
    for _, row in df.iterrows():
        outcome = row["outcome"]
        d = stage3_panel[stage3_panel[outcome].notna()].copy()
        rows.append(
            {
                "stage": "stage3_triple_did",
                "strategy": "current_mte2d_top20_vs_rest",
                "strategy_label": STRATEGIES["current_mte2d_top20_vs_rest"],
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


def estimate_stage3(panel: pd.DataFrame, strategy: str) -> list[dict[str, object]]:
    d = assign_strategy(panel, strategy)
    d["post_strategy_exp"] = d["post"] * d["strategy_treat"]
    d["strategy_exp_high_connect"] = d["strategy_treat"] * d["alta_conectividade"]
    d["triple_strategy"] = d["post"] * d["strategy_treat"] * d["alta_conectividade"]
    rows: list[dict[str, object]] = []
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
                "strategy_label": STRATEGIES[strategy],
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


def compare_to_current(results: pd.DataFrame) -> pd.DataFrame:
    current = results[results["strategy"] == "current_mte2d_top20_vs_rest"].copy()
    alternatives = results[results["strategy"] != "current_mte2d_top20_vs_rest"].copy()
    out = alternatives.merge(current, on=["stage", "outcome"], suffixes=("_alternative", "_current"))
    out["delta_coef_vs_current"] = out["coef_alternative"] - out["coef_current"]
    out["sign_changed_vs_current"] = np.sign(out["coef_alternative"]) != np.sign(out["coef_current"])
    return out


def display_sample(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        rows_fmt=df["rows"].map(lambda x: fmt(int(x))),
        rows_pct_fmt=df["rows_pct"].map(lambda x: pct(x)),
        cbo_fmt=df["cbo"].map(lambda x: fmt(int(x))),
        treated_cbo_fmt=df["treated_cbo"].map(lambda x: fmt(int(x))),
        control_cbo_fmt=df["control_cbo"].map(lambda x: fmt(int(x))),
        dropped_cbo_fmt=df["dropped_cbo"].map(lambda x: fmt(int(x))),
        admissoes_fmt=df["admissoes"].map(lambda x: fmt(int(round(x)))),
        admissoes_pct_fmt=df["admissoes_pct"].map(lambda x: pct(x)),
        treated_admissoes_pct_fmt=df["treated_admissoes_pct"].map(lambda x: pct(x)),
        mean_score_2d_treated_fmt=df["mean_score_2d_treated"].map(lambda x: fmt(x, 3)),
        mean_score_2d_control_fmt=df["mean_score_2d_control"].map(lambda x: fmt(x, 3)),
        mean_score_4d_treated_fmt=df["mean_score_4d_treated"].map(lambda x: fmt(x, 3)),
        mean_score_4d_control_fmt=df["mean_score_4d_control"].map(lambda x: fmt(x, 3)),
    )


def display_results(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        coef_fmt=df["coef"].map(lambda x: fmt(x)),
        se_fmt=df["se"].map(lambda x: fmt(x)),
        p_fmt=df["p_value"].map(lambda x: fmt(x, 3)),
        stars=df["stars"].map(clean_stars),
        n_obs_fmt=df["n_obs"].map(lambda x: fmt(int(x))),
        n_cbo_fmt=df["n_cbo"].map(lambda x: fmt(int(x))),
    )


def display_comparison(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        coef_current_fmt=df["coef_current"].map(lambda x: fmt(x)),
        p_current_fmt=df["p_value_current"].map(lambda x: fmt(x, 3)),
        coef_alt_fmt=df["coef_alternative"].map(lambda x: fmt(x)),
        p_alt_fmt=df["p_value_alternative"].map(lambda x: fmt(x, 3)),
        delta_fmt=df["delta_coef_vs_current"].map(lambda x: fmt(x)),
    )


def write_report(
    isco4d_cutoff: float,
    classification_summary: pd.DataFrame,
    sample: pd.DataFrame,
    stage2_results: pd.DataFrame,
    stage3_results: pd.DataFrame,
    stage2_comparison: pd.DataFrame,
    stage3_comparison: pd.DataFrame,
    top_examples: pd.DataFrame,
) -> None:
    class_display = classification_summary.assign(
        cbo_fmt=classification_summary["cbo"].map(lambda x: fmt(int(x))),
        cbo_pct_fmt=classification_summary["cbo_pct"].map(lambda x: pct(x)),
        admissoes_fmt=classification_summary["admissoes_total"].map(lambda x: fmt(int(round(x)))),
        admissoes_pct_fmt=classification_summary["admissoes_pct"].map(lambda x: pct(x)),
    )
    sample_display = display_sample(sample)
    stage2_display = display_results(stage2_results)
    stage3_display = display_results(stage3_results)
    stage2_comp = display_comparison(stage2_comparison)
    stage3_comp = display_comparison(stage3_comparison)
    examples = top_examples.assign(
        exposure_score_mte_4d_fmt=top_examples["exposure_score_mte_4d"].map(lambda x: fmt(x, 3)),
        exposure_score_mte_2d_fmt=top_examples["exposure_score_mte_2d"].map(lambda x: fmt(x, 3)),
        admissoes_fmt=top_examples["admissoes_total"].map(lambda x: fmt(int(round(x)))),
    )

    text = f"""# Simulação: Tratamento Por Consenso No ISCO-08 4d

## Regra Testada

A regra proposta calcula primeiro o top 20% da distribuição de scores da OIT no nível ISCO-08 4d. O corte encontrado foi:

```text
ISCO-08 4d top 20%: score >= {fmt(isco4d_cutoff, 6)}
```

Depois, para cada CBO, olhamos todos os destinos ISCO-08 4d gerados pela ponte MTE. O CBO só entra em tratamento se todos os seus destinos ISCO-08 4d estiverem acima desse corte.

Foram estimadas duas versões:

- `strict_all4d_top20_vs_rest`: tratamento = todos os destinos top 20%; controle = todos os demais CBOs com match MTE.
- `strict_all4d_top20_vs_none4d_top20`: tratamento = todos os destinos top 20%; controle = nenhum destino top 20%; CBOs mistos excluídos.

## Classificação Dos CBOs

{markdown_table(class_display, ["strict_isco4d_class", "cbo_fmt", "cbo_pct_fmt", "admissoes_fmt", "admissoes_pct_fmt"])}

## Tamanho Da Amostra

{markdown_table(sample_display, ["stage", "strategy_label", "rows_fmt", "rows_pct_fmt", "cbo_fmt", "treated_cbo_fmt", "control_cbo_fmt", "dropped_cbo_fmt", "admissoes_fmt", "admissoes_pct_fmt", "treated_admissoes_pct_fmt", "mean_score_4d_treated_fmt", "mean_score_4d_control_fmt"])}

## Principais CBOs Tratados Pela Regra Estrita

{markdown_table(examples, ["cbo_4d", "source_cbo_title", "target_isco08_codes", "exposure_score_mte_4d_fmt", "exposure_score_mte_2d_fmt", "admissoes_fmt"])}

## Etapa 2: DiD Ocupação-Mês

{markdown_table(stage2_display, ["strategy_label", "outcome_label", "coef_fmt", "se_fmt", "p_fmt", "stars", "n_obs_fmt", "n_cbo_fmt"])}

Comparação contra a especificação atual:

{markdown_table(stage2_comp, ["strategy_label_alternative", "outcome_label_alternative", "coef_current_fmt", "p_current_fmt", "coef_alt_fmt", "p_alt_fmt", "delta_fmt", "sign_changed_vs_current"])}

## Etapa 3: Triple-DiD Municipal

{markdown_table(stage3_display, ["strategy_label", "outcome_label", "coef_fmt", "se_fmt", "p_fmt", "stars", "n_obs_fmt", "n_cbo_fmt"])}

Comparação contra a especificação atual:

{markdown_table(stage3_comp, ["strategy_label_alternative", "outcome_label_alternative", "coef_current_fmt", "p_current_fmt", "coef_alt_fmt", "p_alt_fmt", "delta_fmt", "sign_changed_vs_current"])}

## Conclusão

Essa regra é conceitualmente interessante porque exige consenso entre todos os destinos ISCO-08 4d. Ela reduz falsos positivos: um CBO só é tratado se todas as suas possíveis correspondências internacionais forem altamente expostas.

Mas ela é restritiva demais para virar especificação principal. Apenas 45 CBOs entram no tratamento na Etapa 2, contra 92 na regra atual. Eles representam 14,48% das admissões pareadas. Além disso, a lista de tratados fica dominada por ocupações administrativas, atendimento, vendas e TI, porque o top 20% no ISCO-08 4d favorece tarefas de escritório e informação.

Minha leitura é:

- Não substituir a especificação principal atual por essa regra.
- Usar essa regra como robustez conservadora, se quiser mostrar que os resultados de fluxo da Etapa 3 não dependem de uma definição permissiva de tratamento.
- Ter cautela para interpretar salário real e escolaridade com essa regra: salário real fica apenas marginalmente significativo e o efeito em escolaridade perde força.
"""
    (OUTPUT_DIR / "strict_isco4d_treatment_report.md").write_text(text, encoding="utf-8")


def main() -> None:
    classification, isco4d_cutoff = load_strict_classification()
    classification.to_csv(OUTPUT_DIR / "strict_isco4d_cbo_classification.csv", index=False)

    class_summary = (
        classification.groupby("strict_isco4d_class")
        .agg(
            cbo=("cbo_4d", "nunique"),
            panel_rows=("panel_rows", "sum"),
            admissoes_total=("admissoes_total", "sum"),
        )
        .reset_index()
    )
    class_summary["cbo_pct"] = class_summary["cbo"] / classification["cbo_4d"].nunique()
    class_summary["admissoes_pct"] = (
        class_summary["admissoes_total"] / classification["admissoes_total"].sum()
    )
    class_summary.to_csv(OUTPUT_DIR / "strict_isco4d_class_summary.csv", index=False)

    stage2 = pd.read_parquet(STAGE2_PANEL)
    stage3 = pd.read_parquet(STAGE3_PANEL)
    validate_panel(stage2, "Stage 2 panel")
    validate_panel(stage3, "Stage 3 panel")
    stage2 = attach_classification(stage2, classification)
    stage3 = attach_classification(stage3, classification)

    strategies = [
        "current_mte2d_top20_vs_rest",
        "strict_all4d_top20_vs_rest",
        "strict_all4d_top20_vs_none4d_top20",
    ]

    sample = pd.DataFrame(
        [
            sample_stats(stage_name, panel, strategy)
            for stage_name, panel in [("stage2_did", stage2), ("stage3_triple_did", stage3)]
            for strategy in strategies
        ]
    )
    sample.to_csv(OUTPUT_DIR / "strict_isco4d_sample.csv", index=False)

    stage2_rows = [read_current_stage2()]
    for strategy in strategies[1:]:
        stage2_rows.append(pd.DataFrame(estimate_stage2(stage2, strategy)))
        print(f"Stage 2 estimated: {strategy}")
    stage2_results = pd.concat(stage2_rows, ignore_index=True)
    stage2_results.to_csv(OUTPUT_DIR / "stage2_strict_isco4d_results.csv", index=False)

    stage3_rows = [read_current_stage3(stage3)]
    for strategy in strategies[1:]:
        stage3_rows.append(pd.DataFrame(estimate_stage3(stage3, strategy)))
        print(f"Stage 3 estimated: {strategy}")
    stage3_results = pd.concat(stage3_rows, ignore_index=True)
    stage3_results.to_csv(OUTPUT_DIR / "stage3_strict_isco4d_results.csv", index=False)

    stage2_comparison = compare_to_current(stage2_results)
    stage2_comparison.to_csv(OUTPUT_DIR / "stage2_strict_isco4d_vs_current.csv", index=False)
    stage3_comparison = compare_to_current(stage3_results)
    stage3_comparison.to_csv(OUTPUT_DIR / "stage3_strict_isco4d_vs_current.csv", index=False)

    top_examples = classification[classification["strict_isco4d_treat"] == 1].sort_values(
        "admissoes_total", ascending=False
    ).head(20)
    top_examples.to_csv(OUTPUT_DIR / "strict_isco4d_treated_examples.csv", index=False)

    write_report(
        isco4d_cutoff,
        class_summary,
        sample,
        stage2_results,
        stage3_results,
        stage2_comparison,
        stage3_comparison,
        top_examples,
    )
    print(f"Report written to {OUTPUT_DIR / 'strict_isco4d_treatment_report.md'}")


if __name__ == "__main__":
    main()
