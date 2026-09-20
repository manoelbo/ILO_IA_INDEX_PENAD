"""Build the manual technology/programming extension for Section 4."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from section4_event_study.config import OUTPUT_ROOT, REAL_ALL_OUTCOMES, REAL_MAIN_OUTCOMES, REFERENCE_PERIOD
from section4_event_study.data import load_analysis_data
from section4_event_study.estimation import estimate_event_study, estimate_term
from section4_event_study.formatting import estimate_cell, fmt_number, write_markdown_table
from section4_event_study.heterogeneity import CANARIES_AGE_DIMENSIONS, DIMENSIONS, estimate_heterogeneity
from section4_event_study.manual_tech import build_manual_tech_roles, classify_manual_tech_cbo
from section4_event_study.treatment import apply_roles


VISUALIZER_CROSSWALK = OUTPUT_ROOT.parents[0] / "crosswalk_visualizer" / "cbo_isco08_crosswalk_visual.csv"
OUT_DIR = OUTPUT_ROOT / "manual_tech_extension"
TABLE_DIR = OUT_DIR / "tables"
FIGURE_DIR = OUT_DIR / "figures"
REPORT_PATH = OUT_DIR / "manual_tech_report.md"


def log(message: str) -> None:
    print(message, flush=True)


def prepare_dirs() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for path in [*TABLE_DIR.glob("*"), *FIGURE_DIR.glob("*")]:
        if path.is_file():
            path.unlink()


def _format_bool(value: object) -> str:
    return "sim" if bool(value) else "não"


def build_keyword_audit(classification: pd.DataFrame, panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    visual = pd.read_csv(VISUALIZER_CROSSWALK, dtype={"cbo_4d": str})
    visual = visual.rename(columns={"cbo_title": "source_cbo_title", "cbo_2d_title": "source_cbo_2d_title"})
    visual["cbo_4d"] = visual["cbo_4d"].astype(str).str.zfill(4)
    classified = classify_manual_tech_cbo(visual)
    panel_cbo = set(panel["cbo_4d"].astype(str).str.zfill(4).unique())
    classified["can_enter_final_mte_panel"] = classified["cbo_4d"].isin(panel_cbo)
    keep_cols = [
        "cbo_4d",
        "source_cbo_title",
        "source_cbo_2d_title",
        "mte_match_status",
        "cbo_ilo_gradient",
        "manual_tech_tier",
        "manual_tech_narrow",
        "manual_tech_broad",
        "manual_tech_keywords",
        "manual_tech_rule",
        "manual_tech_exclusion_reason",
        "can_enter_final_mte_panel",
        "caged_admissions_total",
        "caged_panel_rows",
    ]
    audit = classified[keep_cols].copy()
    audit["caged_admissions_total"] = pd.to_numeric(audit["caged_admissions_total"], errors="coerce").fillna(0)
    audit = audit.sort_values(["manual_tech_tier", "caged_admissions_total"], ascending=[True, False])
    audit.to_csv(TABLE_DIR / "manual_tech_keyword_audit.csv", index=False)

    selected = audit[audit["manual_tech_tier"].ne("not_manual_tech")].copy()
    view = selected.assign(
        CBO=selected["cbo_4d"],
        Titulo=selected["source_cbo_title"].fillna(""),
        Tier=selected["manual_tech_tier"],
        MTE=selected["mte_match_status"],
        Gradiente=selected["cbo_ilo_gradient"],
        Regra=selected["manual_tech_rule"],
        Keywords=selected["manual_tech_keywords"],
        EntraPainel=selected["can_enter_final_mte_panel"].map(_format_bool),
        Admissoes=selected["caged_admissions_total"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "manual_tech_keyword_audit.md",
        "Auditoria da classificação manual de tecnologia/programação",
        view,
        ["CBO", "Titulo", "Tier", "MTE", "Gradiente", "Regra", "Keywords", "EntraPainel", "Admissoes"],
        note=(
            "Tier narrow captura software, programação, TI, desenvolvimento de sistemas, dados e suporte de TI. "
            "Tier broad_only adiciona telecomunicações, infraestrutura digital e P&D tecnológico. "
            "Falsos positivos são listados explicitamente e não entram como tratados."
        ),
    )

    summary = (
        audit[audit["manual_tech_tier"].ne("not_manual_tech")]
        .groupby(["manual_tech_tier", "mte_match_status", "cbo_ilo_gradient", "can_enter_final_mte_panel"], dropna=False, observed=True)
        .agg(cbo=("cbo_4d", "nunique"), admissions=("caged_admissions_total", "sum"))
        .reset_index()
        .sort_values(["manual_tech_tier", "admissions"], ascending=[True, False])
    )
    summary.to_csv(TABLE_DIR / "manual_tech_summary.csv", index=False)
    summary_view = summary.assign(
        Tier=summary["manual_tech_tier"],
        MTE=summary["mte_match_status"],
        Gradiente=summary["cbo_ilo_gradient"],
        EntraPainel=summary["can_enter_final_mte_panel"].map(_format_bool),
        CBOs=summary["cbo"].map(lambda v: fmt_number(v, 0)),
        Admissoes=summary["admissions"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "manual_tech_summary.md",
        "Resumo da classificação manual de tecnologia/programação",
        summary_view,
        ["Tier", "MTE", "Gradiente", "EntraPainel", "CBOs", "Admissoes"],
        note="Admissões são totais do CAGED no painel do visualizador; regressões usam apenas CBOs que entram no painel MTE final.",
    )
    return audit, summary


def _result_row(tier: str, outcome: str, label: str, est: dict[str, object]) -> dict[str, object]:
    return {
        "manual_tech_tier": tier,
        "outcome": outcome,
        "outcome_label": label,
        "estimator": "OLS",
        **est,
    }


def build_manual_tech_sample(panel: pd.DataFrame, classification: pd.DataFrame, tier: str) -> pd.DataFrame:
    roles = build_manual_tech_roles(classification, tier)
    sample = apply_roles(panel, roles)
    return sample[sample["mte_match_status"].eq("matched_official_mte")].copy()


def estimate_manual_tech(panel: pd.DataFrame, classification: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    pretrend_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    for tier in ["narrow", "broad"]:
        sample = build_manual_tech_sample(panel, classification, tier)
        if sample.empty:
            continue
        for outcome, label in REAL_ALL_OUTCOMES.items():
            est = estimate_term(sample, outcome, term="post_treat")
            rows.append(_result_row(tier, outcome, label, est))
        coefs, pretrends = estimate_event_study(sample, REAL_ALL_OUTCOMES)
        coefs["manual_tech_tier"] = tier
        pretrends["manual_tech_tier"] = tier
        coef_rows.append(coefs)
        pretrend_rows.append(pretrends)
    results = pd.DataFrame(rows)
    results.to_csv(TABLE_DIR / "manual_tech_results.csv", index=False)
    view = results.assign(
        Tier=results["manual_tech_tier"],
        Resultado=results["outcome_label"],
        Estimativa=[estimate_cell(row.coef, row.se, row.stars) for row in results.itertuples()],
        p=results["p_value"].map(lambda v: fmt_number(v, 3)),
        N=results["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=results["n_cbo"].map(lambda v: fmt_number(v, 0)),
        Status=results["result_status"],
    )
    write_markdown_table(
        TABLE_DIR / "manual_tech_results.md",
        "Resultados: tecnologia/programação manual vs Not Exposed",
        view,
        ["Tier", "Resultado", "Estimativa", "p", "N", "CBOs", "Status"],
        note="Controle: CBOs Not Exposed com match MTE oficial. CBOs sem match MTE são documentados na auditoria, mas não entram nas regressões.",
    )

    pretrends = pd.concat(pretrend_rows, ignore_index=True) if pretrend_rows else pd.DataFrame()
    pretrends.to_csv(TABLE_DIR / "manual_tech_event_study_pretrends.csv", index=False)
    if not pretrends.empty:
        pre_view = pretrends.assign(
            Tier=pretrends["manual_tech_tier"],
            Resultado=pretrends["outcome_label"],
            CoefsPre=pretrends["n_pre_coefficients"].map(lambda v: fmt_number(v, 0)),
            SigPre=pretrends["n_pre_p_lt_005"].map(lambda v: fmt_number(v, 0)),
            pConjunto=pretrends["joint_p_value"].map(lambda v: fmt_number(v, 4)),
            Status=pretrends["pretrend_status"],
        )
        write_markdown_table(
            TABLE_DIR / "manual_tech_event_study_pretrends.md",
            "Pretrends: tecnologia/programação manual",
            pre_view,
            ["Tier", "Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"],
            note="Referência do event study: t=-1.",
        )

    coefs = pd.concat(coef_rows, ignore_index=True) if coef_rows else pd.DataFrame()
    coefs.to_csv(TABLE_DIR / "manual_tech_event_study_coefficients.csv", index=False)
    plot_event_studies(coefs)
    return results, pretrends


def _write_heterogeneity_table(path: Path, title: str, data: pd.DataFrame, note: str) -> None:
    data = data.copy()
    if data.empty:
        write_markdown_table(path, title, data, ["Tier", "Painel", "Grupo", "Resultado", "Estimativa", "p"], note=note)
        return
    data["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in data.itertuples()]
    view = data.assign(
        Tier=data["manual_tech_tier"],
        Painel=data["panel"],
        Grupo=data["group_label"],
        Resultado=data["outcome_label"],
        Estimativa=data["estimate_se"],
        p=data["p_value"].map(lambda v: fmt_number(v, 3)),
        Pretrend=data["pretrend_status"],
        Poder=data["power_status"],
        N=data["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=data["n_cbo"].map(lambda v: fmt_number(v, 0)),
        Status=data["result_status"],
    )
    write_markdown_table(
        path,
        title,
        view,
        ["Tier", "Painel", "Grupo", "Resultado", "Estimativa", "p", "Pretrend", "Poder", "N", "CBOs", "Status"],
        note=note,
    )


def estimate_manual_tech_heterogeneity(panel: pd.DataFrame, classification: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    demographic_rows: list[pd.DataFrame] = []
    canaries_rows: list[pd.DataFrame] = []
    for tier in ["narrow", "broad"]:
        sample = build_manual_tech_sample(panel, classification, tier)
        if sample.empty:
            continue
        demographic = estimate_heterogeneity(sample, outcomes=REAL_MAIN_OUTCOMES, dimensions=DIMENSIONS)
        demographic["manual_tech_tier"] = tier
        demographic_rows.append(demographic)

        canaries = estimate_heterogeneity(sample, outcomes=REAL_MAIN_OUTCOMES, dimensions=CANARIES_AGE_DIMENSIONS)
        canaries["manual_tech_tier"] = tier
        canaries_rows.append(canaries)

    demographic_out = pd.concat(demographic_rows, ignore_index=True) if demographic_rows else pd.DataFrame()
    canaries_out = pd.concat(canaries_rows, ignore_index=True) if canaries_rows else pd.DataFrame()
    demographic_out.to_csv(TABLE_DIR / "manual_tech_demographic_heterogeneity.csv", index=False)
    canaries_out.to_csv(TABLE_DIR / "manual_tech_canaries_age_heterogeneity.csv", index=False)
    _write_heterogeneity_table(
        TABLE_DIR / "manual_tech_demographic_heterogeneity.md",
        "Heterogeneidade demográfica: tecnologia/programação manual",
        demographic_out,
        (
            "Coeficiente estimado: post × manual tech × grupo. "
            "Cada grupo é comparado ao seu complemento dentro do respectivo tier manual tech vs Not Exposed."
        ),
    )
    _write_heterogeneity_table(
        TABLE_DIR / "manual_tech_canaries_age_heterogeneity.md",
        "Heterogeneidade por idade estilo Canaries: tecnologia/programação manual",
        canaries_out,
        (
            "Coeficiente estimado: post × manual tech × faixa etária. "
            "As faixas 22-25, 26-30, 31-34, 35-40, 41-49 e 50+ seguem a inspiração do artigo de referência."
        ),
    )
    return demographic_out, canaries_out


def plot_event_studies(coefs: pd.DataFrame) -> None:
    if coefs.empty:
        return
    for (tier, outcome), data in coefs.groupby(["manual_tech_tier", "outcome"], observed=True):
        data = data.sort_values("t")
        fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
        ax.axhline(0, color="#333333", linewidth=1)
        ax.axvline(-0.5, color="#777777", linestyle="--", linewidth=1)
        ax.plot(data["t"], data["coef"], marker="o", markersize=3, linewidth=1.6, color="#2f6f9f")
        ax.fill_between(data["t"], data["ci_low"], data["ci_high"], color="#2f6f9f", alpha=0.18)
        ax.set_title(f"{tier}: {data['outcome_label'].iloc[0]}")
        ax.set_xlabel("Meses relativos a dez/2022")
        ax.set_ylabel("Coeficiente")
        ax.grid(True, alpha=0.25)
        fig.savefig(FIGURE_DIR / f"manual_tech_{tier}_{outcome}.png", dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(fig)


def _negative_signals(data: pd.DataFrame, outcome: str, p_threshold: float = 0.10, limit: int = 5) -> str:
    if data.empty or outcome not in set(data.get("outcome", [])):
        return "Nenhum sinal estimado."
    subset = data[
        data["outcome"].eq(outcome)
        & data["result_status"].eq("estimated")
        & pd.to_numeric(data["coef"], errors="coerce").lt(0)
        & pd.to_numeric(data["p_value"], errors="coerce").lt(p_threshold)
    ].copy()
    if subset.empty:
        return "Não há coeficientes negativos com p<0,10 nesse bloco."
    subset = subset.sort_values(["p_value", "coef"]).head(limit)
    parts = []
    for row in subset.itertuples():
        parts.append(
            f"{row.manual_tech_tier}: {row.group_label} em {row.outcome_label} "
            f"({fmt_number(row.coef)}{row.stars}, p={fmt_number(row.p_value, 3)}, pretrend={row.pretrend_status})"
        )
    return "; ".join(parts) + "."


def write_report(
    audit: pd.DataFrame,
    summary: pd.DataFrame,
    results: pd.DataFrame,
    pretrends: pd.DataFrame,
    demographic_heterogeneity: pd.DataFrame,
    canaries_heterogeneity: pd.DataFrame,
) -> None:
    narrow = audit[audit["manual_tech_tier"].eq("narrow")]
    broad = audit[audit["manual_tech_tier"].eq("broad_only")]
    narrow_matched = narrow[narrow["can_enter_final_mte_panel"]]
    no_match = audit[audit["manual_tech_tier"].isin(["narrow", "broad_only"]) & ~audit["can_enter_final_mte_panel"]]
    salary = results[(results["manual_tech_tier"].eq("narrow")) & (results["outcome"].eq("ln_salario_real_adm"))]
    salary_text = "Sem estimação válida para salário real de admissão no recorte estreito."
    if not salary.empty:
        row = salary.iloc[0]
        salary_text = (
            f"No recorte estreito, o coeficiente de salário real de admissão é {fmt_number(row['coef'])} "
            f"({row['stars'] or 'sem estrela'}, p={fmt_number(row['p_value'], 3)})."
        )
    pretrend_failures = int(pretrends["pretrend_status"].eq("fail").sum()) if not pretrends.empty else 0
    sections = [
        "# Extensão Manual De Tecnologia/Programação",
        "## Estratégia de separação",
        (
            "A separação usa exclusivamente palavras-chave nos títulos CBO, antes da leitura dos coeficientes: "
            "`narrow` captura software, programação, tecnologia da informação, computação, desenvolvimento de sistemas, "
            "entrada/transmissão de dados e suporte de TI. `broad_only` adiciona telecomunicações, redes, comunicação de dados "
            "e P&D tecnológico. Falsos positivos semânticos, como programação de produção/manutenção e ensino, são excluídos."
        ),
        "## Diagnóstico de cobertura",
        (
            f"O recorte estreito identifica {narrow['cbo_4d'].nunique()} CBOs, dos quais "
            f"{narrow_matched['cbo_4d'].nunique()} entram no painel MTE final. "
            f"A extensão ampla adiciona {broad['cbo_4d'].nunique()} CBOs. "
            f"Há {no_match['cbo_4d'].nunique()} CBOs tech/digitais sem match MTE oficial; eles ficam documentados, mas fora da regressão."
        ),
        "## Resultado econométrico",
        salary_text,
        (
            f"Os testes de pretrend registram {pretrend_failures} falha(s). "
            "Quando houver falha, a leitura deve ser exploratória e não causal forte."
        ),
        "## Heterogeneidade demográfica",
        (
            "A extensão aplica a mesma lógica de interação tripla da Seção 4 ao recorte manual de tecnologia/programação. "
            "Os outcomes são admissões, demissões e salário real de admissão."
        ),
        (
            "Sinais negativos salariais no desenho demográfico amplo: "
            f"{_negative_signals(demographic_heterogeneity, 'ln_salario_real_adm')}"
        ),
        (
            "Sinais negativos salariais nas faixas estilo Canaries: "
            f"{_negative_signals(canaries_heterogeneity, 'ln_salario_real_adm')}"
        ),
        "## Tabelas",
        "- `tables/manual_tech_keyword_audit.md`",
        "- `tables/manual_tech_summary.md`",
        "- `tables/manual_tech_results.md`",
        "- `tables/manual_tech_event_study_pretrends.md`",
        "- `tables/manual_tech_demographic_heterogeneity.md`",
        "- `tables/manual_tech_canaries_age_heterogeneity.md`",
    ]
    REPORT_PATH.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def run() -> None:
    prepare_dirs()
    log("Loading Section 4 panel and classification...")
    panel, classification = load_analysis_data()
    log("Building manual technology keyword audit...")
    audit, summary = build_keyword_audit(classification, panel)
    log("Estimating manual technology extension...")
    results, pretrends = estimate_manual_tech(panel, classification)
    log("Estimating manual technology demographic heterogeneity...")
    demographic_heterogeneity, canaries_heterogeneity = estimate_manual_tech_heterogeneity(panel, classification)
    log("Writing manual technology report...")
    write_report(audit, summary, results, pretrends, demographic_heterogeneity, canaries_heterogeneity)
    log(f"Done. Report written to {REPORT_PATH}")


if __name__ == "__main__":
    run()
