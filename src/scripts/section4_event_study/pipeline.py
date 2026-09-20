"""Pipeline for the final Section 4 event-study package."""

from __future__ import annotations

from functools import lru_cache
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import (
    ALL_OUTCOMES,
    AUDIT_DIR,
    COMPLEMENTARY_OUTCOMES,
    CONTROL_COLUMNS,
    DATA_PROCESSED,
    FIGURE_DIR,
    FINAL_OUTPUT,
    MAIN_OUTCOMES,
    MAIN_SCENARIO,
    NET_FLOW_EVENT_OUTCOMES,
    NET_FLOW_OUTCOMES,
    PLACEBO_PERIOD,
    REAL_ALL_OUTCOMES,
    REAL_HETEROGENEITY_OUTCOMES,
    REAL_MAIN_OUTCOMES,
    REAL_WAGE_REPORT_PATH,
    REPORT_PATH,
    TABLE_DIR,
    TREATMENT_PERIOD,
)
from .data import load_analysis_data
from .estimation import estimate_event_study, estimate_poisson_term, estimate_term
from .formatting import estimate_cell, fmt_number, markdown_table, write_markdown_table
from .heterogeneity import (
    CANARIES_AGE_DIMENSIONS,
    build_pre_treatment_income_group_assignments,
    estimate_heterogeneity,
    iter_raw_batches,
    valid_cbo_4d,
)
from .treatment import (
    apply_roles,
    assign_roles,
    assign_single_gradient_roles,
    continuous_sample,
    role_summary,
    validate_base_and_broad_roles,
)


ROBUSTNESS_SCENARIOS = {
    "main_strict": "Base sem peso",
    "main_strict_weighted": "Base com peso pré-admissões",
    "main_broad_control": "Minimal Exposure no controle",
    "main_broad_control_weighted": "Minimal Exposure no controle, com peso",
    "continuous": "Exposição contínua média + dispersão",
    "continuous_weighted": "Exposição contínua, com peso",
    "exclude_it": "Exclui CBO 21xx",
    "placebo_2021_12": "Placebo temporal dez/2021",
    "pretrend_linear": "Tendência diferencial no pré",
    "cluster_cbo2d": "Cluster alternativo CBO 2d",
    "high_exposure_strict": "Benchmark G3-G4 vs Not Exposed",
    "medium_exposure_strict": "Benchmark G1-G2 vs Not Exposed",
    "mte_top20_benchmark": "Benchmark MTE top 20%",
}

FLOW_COUNT_OUTCOMES = {
    "admissoes": "Admissões",
    "desligamentos": "Demissões",
}

CANARIES_AGE_OUTCOMES = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Demissões (log)",
    "ln_salario_real_adm": "Salário real de admissão (log)",
}

GRADIENT_DECOMPOSITION = [
    ("minimal_vs_not_exposed", "Minimal Exposure vs Not Exposed", "Minimal Exposure"),
    ("g1_vs_not_exposed", "G1 vs Not Exposed", "Exposed: Gradient 1"),
    ("g2_vs_not_exposed", "G2 vs Not Exposed", "Exposed: Gradient 2"),
    ("g3_vs_not_exposed", "G3 vs Not Exposed", "Exposed: Gradient 3"),
    ("g4_vs_not_exposed", "G4 vs Not Exposed", "Exposed: Gradient 4"),
]

TECH_CNAE_SECTION = "J"
TECH_CNAE_PRE_ADM_SHARE_THRESHOLD = 0.50


def log(message: str) -> None:
    print(message, flush=True)


def prepare_output_dirs() -> None:
    for path in [TABLE_DIR, FIGURE_DIR, AUDIT_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    for path in [TABLE_DIR, FIGURE_DIR, AUDIT_DIR]:
        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)


def result_row(spec_id: str, spec_label: str, outcome: str, outcome_label: str, est: dict[str, object], weight: str | None, cluster: str) -> dict[str, object]:
    return {
        "spec_id": spec_id,
        "spec_label": spec_label,
        "outcome": outcome,
        "outcome_label": outcome_label,
        "weight": weight or "none",
        "cluster": cluster,
        **est,
    }


def estimate_outcomes(
    spec_id: str,
    spec_label: str,
    data: pd.DataFrame,
    outcomes: dict[str, str],
    term: str = "post_treat",
    weight: str | None = None,
    cluster: str = "cbo_4d",
    fe: str = "cbo_4d + periodo",
    extra_terms: list[str] | None = None,
    extra_required: list[str] | None = None,
    controls: list[str] | None = None,
) -> list[dict[str, object]]:
    rows = []
    for outcome, outcome_label in outcomes.items():
        est = estimate_term(
            data,
            outcome,
            term=term,
            cluster=cluster,
            weight=weight,
            fe=fe,
            extra_terms=extra_terms,
            extra_required=extra_required,
            controls=controls,
        )
        rows.append(result_row(spec_id, spec_label, outcome, outcome_label, est, weight, cluster))
    return rows


def estimate_poisson_outcomes(
    spec_id: str,
    spec_label: str,
    data: pd.DataFrame,
    outcomes: dict[str, str],
    controls: list[str] | None = None,
    extra_terms: list[str] | None = None,
    extra_required: list[str] | None = None,
    cluster: str = "cbo_4d",
    fe: str = "cbo_4d + periodo",
) -> list[dict[str, object]]:
    rows = []
    for outcome, outcome_label in outcomes.items():
        est = estimate_poisson_term(
            data,
            outcome,
            cluster=cluster,
            fe=fe,
            controls=controls,
            extra_terms=extra_terms,
            extra_required=extra_required,
        )
        rows.append(result_row(spec_id, spec_label, outcome, outcome_label, est, None, cluster))
    return rows


def build_crosswalk_table(classification: pd.DataFrame, strict_roles: pd.DataFrame, broad_roles: pd.DataFrame) -> pd.DataFrame:
    strict = strict_roles[["cbo_4d", "scenario_role"]].rename(columns={"scenario_role": "strict_role"})
    broad = broad_roles[["cbo_4d", "scenario_role"]].rename(columns={"scenario_role": "broad_role"})
    d = classification.merge(strict, on="cbo_4d", how="left").merge(broad, on="cbo_4d", how="left")
    order = {
        "Exposed: Gradient 4": 1,
        "Exposed: Gradient 3": 2,
        "Exposed: Gradient 2": 3,
        "Exposed: Gradient 1": 4,
        "Minimal Exposure": 5,
        "Not Exposed": 6,
        "No score": 7,
    }
    summary = (
        d.groupby("cbo_ilo_gradient", dropna=False)
        .agg(
            n_cbo=("cbo_4d", "nunique"),
            matched_mte=("mte_match_status", lambda s: int(s.eq("matched_official_mte").sum())),
            strict_treated=("strict_role", lambda s: int(s.eq("treated").sum())),
            strict_control=("strict_role", lambda s: int(s.eq("control").sum())),
            broad_control=("broad_role", lambda s: int(s.eq("control").sum())),
            mean_score=("isco08_mean_score", "mean"),
            pooled_sd=("isco08_pooled_sd", "mean"),
        )
        .reset_index()
        .rename(columns={"cbo_ilo_gradient": "gradient"})
    )
    expected = pd.DataFrame({"gradient": list(order)})
    summary = expected.merge(summary, on="gradient", how="left")
    count_columns = ["n_cbo", "matched_mte", "strict_treated", "strict_control", "broad_control"]
    summary[count_columns] = summary[count_columns].fillna(0).astype(int)
    summary["order"] = summary["gradient"].map(order).fillna(99)
    summary = summary.sort_values("order").drop(columns="order")
    summary.to_csv(TABLE_DIR / "crosswalk_exposure_summary.csv", index=False)
    md = summary.assign(
        Gradiente=summary["gradient"],
        CBOs=summary["n_cbo"].map(lambda v: fmt_number(v, 0)),
        MTE=summary["matched_mte"].map(lambda v: fmt_number(v, 0)),
        Tratados=summary["strict_treated"].map(lambda v: fmt_number(v, 0)),
        ControleBase=summary["strict_control"].map(lambda v: fmt_number(v, 0)),
        ControleAmplo=summary["broad_control"].map(lambda v: fmt_number(v, 0)),
        Media=summary["mean_score"].map(lambda v: fmt_number(v, 3)),
        Dispersao=summary["pooled_sd"].map(lambda v: fmt_number(v, 3)),
    )
    write_markdown_table(
        TABLE_DIR / "crosswalk_exposure_summary.md",
        "Tabela de crosswalk e exposição",
        md,
        ["Gradiente", "CBOs", "MTE", "Tratados", "ControleBase", "ControleAmplo", "Media", "Dispersao"],
        note=(
            "ControleBase usa apenas Not Exposed; ControleAmplo adiciona Minimal Exposure. "
            "A linha G4 é mantida mesmo se a classificação final CBO 4d não tiver observações nesse gradiente."
        ),
    )
    return summary


def build_main_table(base: pd.DataFrame) -> pd.DataFrame:
    rows = estimate_outcomes("main_strict", MAIN_SCENARIO.label, base, ALL_OUTCOMES)
    out = pd.DataFrame(rows)
    out["panel"] = np.where(out["outcome"].isin(MAIN_OUTCOMES), "Principal", "Complementar")
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "main_results_3plus1.csv", index=False)
    view = out.assign(
        Painel=out["panel"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=out["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "main_results_3plus1.md",
        "Tabela principal 3+1",
        view,
        ["Painel", "Resultado", "Estimativa", "p", "N", "CBOs"],
        note="O painel complementar traz salário de demissão por ter interpretação menos direta.",
    )
    return out


def build_real_wage_main_table(base: pd.DataFrame) -> pd.DataFrame:
    rows = estimate_outcomes("main_strict_real_wage", MAIN_SCENARIO.label, base, REAL_ALL_OUTCOMES)
    out = pd.DataFrame(rows)
    out["panel"] = np.where(out["outcome"].isin(REAL_MAIN_OUTCOMES), "Principal", "Complementar")
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "real_wage_main_results_3plus1.csv", index=False)
    view = out.assign(
        Painel=out["panel"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=out["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "real_wage_main_results_3plus1.md",
        "Tabela principal com salários reais IPCA",
        view,
        ["Painel", "Resultado", "Estimativa", "p", "N", "CBOs"],
        note="Salários reais deflacionados pelo IPCA mensal, base dez/2024 = 100.",
    )
    return out


def pre_treatment_interaction_columns(data: pd.DataFrame) -> list[str]:
    columns = [f"post_pre_{col}" for col in CONTROL_COLUMNS]
    missing = [col for col in columns if col not in data.columns]
    if missing:
        raise RuntimeError(f"Missing pre-treatment control interaction columns: {missing}")
    return columns


def build_model_ladder_table(base: pd.DataFrame) -> pd.DataFrame:
    pre_terms = pre_treatment_interaction_columns(base)
    specs = [
        ("no_controls", "Sem controles", [], []),
        ("pre_treatment_controls", "Controles pré-tratamento × pós", [], pre_terms),
        ("contemporary_controls", "Controles contemporâneos completos", CONTROL_COLUMNS, []),
    ]
    rows: list[dict[str, object]] = []
    for spec_id, label, controls, extra_terms in specs:
        spec_rows = estimate_outcomes(
            spec_id,
            label,
            base,
            ALL_OUTCOMES,
            controls=controls,
            extra_terms=extra_terms,
            extra_required=extra_terms,
        )
        for row in spec_rows:
            row["control_set"] = spec_id
        rows.extend(spec_rows)
    out = pd.DataFrame(rows)
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "model_ladder_controls.csv", index=False)
    view = out.assign(
        Modelo=out["spec_label"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=out["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "model_ladder_controls.md",
        "Ladder de controles do modelo base",
        view,
        ["Modelo", "Resultado", "Estimativa", "p", "N", "CBOs"],
        note=(
            "Controles pré-tratamento entram interagidos com o pós; os níveis pré-tratamento puros "
            "são absorvidos pelos efeitos fixos de CBO."
        ),
    )
    return out


def build_poisson_flow_table(base: pd.DataFrame) -> pd.DataFrame:
    pre_terms = pre_treatment_interaction_columns(base)
    specs = [
        ("poisson_no_controls", "Poisson sem controles", [], []),
        ("poisson_pre_treatment_controls", "Poisson controles pré-tratamento × pós", [], pre_terms),
        ("poisson_contemporary_controls", "Poisson controles contemporâneos completos", CONTROL_COLUMNS, []),
    ]
    rows: list[dict[str, object]] = []
    for spec_id, label, controls, extra_terms in specs:
        spec_rows = estimate_poisson_outcomes(
            spec_id,
            label,
            base,
            FLOW_COUNT_OUTCOMES,
            controls=controls,
            extra_terms=extra_terms,
            extra_required=extra_terms,
        )
        for row in spec_rows:
            row["control_set"] = spec_id
        rows.extend(spec_rows)
    out = pd.DataFrame(rows)
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "poisson_flow_results.csv", index=False)
    view = out.assign(
        Modelo=out["spec_label"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=out["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "poisson_flow_results.md",
        "Poisson para outcomes de fluxo",
        view,
        ["Modelo", "Resultado", "Estimativa", "p", "N", "CBOs"],
        note="Robustez para contagens de admissões e demissões, evitando a transformação log(y+1).",
    )
    return out


def plot_net_flow_event_studies(coefficients: pd.DataFrame) -> None:
    for outcome, label in NET_FLOW_EVENT_OUTCOMES.items():
        view = coefficients[
            (coefficients["outcome"] == outcome)
            & coefficients["coefficient_status"].isin(["estimated", "reference"])
        ].sort_values("t")
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.axhline(0, color="#222222", linewidth=0.8)
        ax.axvline(-1, color="#666666", linewidth=0.8, linestyle="--")
        ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
        ax.plot(view["t"], view["coef"], marker="o", markersize=3, linewidth=1.3, color="#7a3b2e")
        band = view.dropna(subset=["ci_low", "ci_high"])
        ax.fill_between(
            band["t"].astype(float),
            band["ci_low"].astype(float),
            band["ci_high"].astype(float),
            color="#7a3b2e",
            alpha=0.18,
        )
        ax.set_title(label)
        ax.set_xlabel("Meses relativos ao ChatGPT")
        ax.set_ylabel("Coeficiente")
        ax.grid(True, alpha=0.2)
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / f"event_study_{outcome}.png", dpi=180, bbox_inches="tight")
        plt.close(fig)


def build_net_flow_outputs(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = estimate_outcomes("net_flow_main", "Fluxo líquido no modelo base", base, NET_FLOW_OUTCOMES)
    results = pd.DataFrame(rows)
    results["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in results.itertuples()]
    results.to_csv(TABLE_DIR / "net_flow_results.csv", index=False)
    view = results.assign(
        Resultado=results["outcome_label"],
        Estimativa=results["estimate_se"],
        p=results["p_value"].map(lambda v: fmt_number(v, 3)),
        N=results["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=results["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "net_flow_results.md",
        "Resultados de saldo líquido",
        view,
        ["Resultado", "Estimativa", "p", "N", "CBOs"],
        note=(
            "`asinh(saldo)` é a transformação preferida para regressão porque aceita valores negativos e zero. "
            "`saldo_per_pre_adm` normaliza o saldo pelo tamanho pré-tratamento da ocupação."
        ),
    )

    coefficients, pretrends = estimate_event_study(base, NET_FLOW_EVENT_OUTCOMES)
    coefficients.to_csv(TABLE_DIR / "net_flow_event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(TABLE_DIR / "net_flow_event_study_pretrends.csv", index=False)
    plot_net_flow_event_studies(coefficients)
    pretrend_view = pretrends.assign(
        Resultado=pretrends["outcome_label"],
        CoefsPre=pretrends["n_pre_coefficients"].map(lambda v: fmt_number(v, 0)),
        SigPre=pretrends["n_pre_p_lt_005"].map(lambda v: fmt_number(v, 0)),
        pConjunto=pretrends["joint_p_value"].map(lambda v: fmt_number(v, 4)),
        Status=pretrends["pretrend_status"],
    )
    write_markdown_table(
        TABLE_DIR / "net_flow_event_study_pretrends.md",
        "Pretrends do event study de saldo líquido",
        pretrend_view,
        ["Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"],
        note="Referência do event study: t=-1. Falhas de pretrend reduzem a força causal da leitura do saldo.",
    )

    heterogeneity = estimate_heterogeneity(base, NET_FLOW_OUTCOMES, dimensions={**CANARIES_AGE_DIMENSIONS})
    demographic = estimate_heterogeneity(base, NET_FLOW_OUTCOMES)
    heterogeneity = pd.concat([demographic, heterogeneity], ignore_index=True)
    heterogeneity["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in heterogeneity.itertuples()]
    heterogeneity.to_csv(TABLE_DIR / "net_flow_heterogeneity_long.csv", index=False)
    het_view = heterogeneity.assign(
        Painel=heterogeneity["panel"],
        Grupo=heterogeneity["group_label"],
        Resultado=heterogeneity["outcome_label"],
        Estimativa=heterogeneity["estimate_se"],
        p=heterogeneity["p_value"].map(lambda v: fmt_number(v, 3)),
        Pretrend=heterogeneity["pretrend_status"],
        Poder=heterogeneity["power_status"],
        N=heterogeneity["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=heterogeneity["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "net_flow_heterogeneity.md",
        "Heterogeneidade do saldo líquido",
        het_view,
        ["Painel", "Grupo", "Resultado", "Estimativa", "p", "Pretrend", "Poder", "N", "CBOs"],
        note="Coeficiente estimado: post × tratamento × grupo; o saldo é reconstruído a partir dos microdados para cada perfil.",
    )

    preferred = results[results["outcome"].eq("asinh_saldo")]
    preferred_text = "sem estimativa disponível"
    if not preferred.empty:
        row = preferred.iloc[0]
        preferred_text = f"{fmt_number(row['coef'])}{row['stars'] or ''} (p={fmt_number(row['p_value'], 3)})"
    failed_pretrends = int(pretrends["pretrend_status"].eq("fail").sum())
    text = f"""# Resumo Do Saldo Líquido

O saldo líquido é definido como admissões menos desligamentos. Ele resume a direção líquida do fluxo formal, mas não substitui admissões e demissões separadas, porque combina dois mecanismos distintos.

No modelo base, a estimativa preferida para `asinh(saldo)` é {preferred_text}. O event study de saldo teve {failed_pretrends} falhas de pretrend entre os outcomes líquidos testados.

Arquivos auditáveis:

- `final_event_study/tables/net_flow_results.csv`
- `final_event_study/tables/net_flow_event_study_coefficients_long.csv`
- `final_event_study/tables/net_flow_event_study_pretrends.csv`
- `final_event_study/tables/net_flow_heterogeneity_long.csv`
"""
    (TABLE_DIR / "net_flow_summary.md").write_text(text, encoding="utf-8")
    return results, coefficients, pretrends, heterogeneity


def build_robustness_table(panel: pd.DataFrame, classification: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    rows.extend(estimate_outcomes("main_strict", ROBUSTNESS_SCENARIOS["main_strict"], base, ALL_OUTCOMES))
    rows.extend(
        estimate_outcomes(
            "main_strict_weighted",
            ROBUSTNESS_SCENARIOS["main_strict_weighted"],
            base,
            ALL_OUTCOMES,
            weight="pre_adm_weight",
        )
    )

    broad = apply_roles(panel, assign_roles(classification, "main_broad_control"))
    rows.extend(estimate_outcomes("main_broad_control", ROBUSTNESS_SCENARIOS["main_broad_control"], broad, ALL_OUTCOMES))
    rows.extend(
        estimate_outcomes(
            "main_broad_control_weighted",
            ROBUSTNESS_SCENARIOS["main_broad_control_weighted"],
            broad,
            ALL_OUTCOMES,
            weight="pre_adm_weight",
        )
    )

    continuous = continuous_sample(panel)
    rows.extend(
        estimate_outcomes(
            "continuous",
            ROBUSTNESS_SCENARIOS["continuous"],
            continuous,
            ALL_OUTCOMES,
            term="post_continuous_exposure",
        )
    )
    rows.extend(
        estimate_outcomes(
            "continuous_weighted",
            ROBUSTNESS_SCENARIOS["continuous_weighted"],
            continuous,
            ALL_OUTCOMES,
            term="post_continuous_exposure",
            weight="pre_adm_weight",
        )
    )

    no_it = base[~base["cbo_4d"].astype(str).str.startswith("21")].copy()
    rows.extend(estimate_outcomes("exclude_it", ROBUSTNESS_SCENARIOS["exclude_it"], no_it, ALL_OUTCOMES))

    placebo = base[base["post"].eq(0)].copy()
    placebo["post_placebo"] = (placebo["periodo_num"] >= PLACEBO_PERIOD).astype(int)
    placebo["did_placebo"] = placebo["post_placebo"] * placebo["scenario_treat"].astype(int)
    rows.extend(
        estimate_outcomes(
            "placebo_2021_12",
            ROBUSTNESS_SCENARIOS["placebo_2021_12"],
            placebo,
            ALL_OUTCOMES,
            term="did_placebo",
        )
    )

    pre = base[base["post"].eq(0)].copy()
    pre["trend_treat"] = pd.to_numeric(pre["trend"], errors="coerce") * pre["scenario_treat"].astype(int)
    rows.extend(
        estimate_outcomes(
            "pretrend_linear",
            ROBUSTNESS_SCENARIOS["pretrend_linear"],
            pre,
            ALL_OUTCOMES,
            term="trend_treat",
        )
    )

    rows.extend(
        estimate_outcomes(
            "cluster_cbo2d",
            ROBUSTNESS_SCENARIOS["cluster_cbo2d"],
            base,
            ALL_OUTCOMES,
            cluster="cbo_2d",
        )
    )

    for scenario_id in ["high_exposure_strict", "medium_exposure_strict", "mte_top20_benchmark"]:
        d = apply_roles(panel, assign_roles(classification, scenario_id))
        rows.extend(estimate_outcomes(scenario_id, ROBUSTNESS_SCENARIOS[scenario_id], d, ALL_OUTCOMES))

    out = pd.DataFrame(rows)
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "robustness_results_long.csv", index=False)
    view = out.assign(
        Especificacao=out["spec_label"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=out["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "robustness_results.md",
        "Tabela de robustez",
        view,
        ["Especificacao", "Resultado", "Estimativa", "p", "N", "CBOs"],
    )
    return out


def build_gradient_decomposition_table(panel: pd.DataFrame, classification: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for scenario_id, label, gradient_label in GRADIENT_DECOMPOSITION:
        roles = assign_single_gradient_roles(classification, gradient_label, scenario_id)
        d = apply_roles(panel, roles)
        spec_rows = estimate_outcomes(scenario_id, label, d, ALL_OUTCOMES)
        for row in spec_rows:
            row["gradient"] = gradient_label
            row["treated_cbo"] = int(roles["scenario_role"].eq("treated").sum())
            row["control_cbo"] = int(roles["scenario_role"].eq("control").sum())
        rows.extend(spec_rows)
    out = pd.DataFrame(rows)
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "gradient_decomposition_results.csv", index=False)
    view = out.assign(
        Especificacao=out["spec_label"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        Tratados=out["treated_cbo"].map(lambda v: fmt_number(v, 0)),
        Controle=out["control_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "gradient_decomposition_results.md",
        "Decomposição por gradiente",
        view,
        ["Especificacao", "Resultado", "Estimativa", "p", "Tratados", "Controle"],
        note="Cada gradiente é comparado separadamente contra Not Exposed; G4 pode aparecer sem amostra tratada no nível CBO final.",
    )
    return out


@lru_cache(maxsize=1)
def build_pre_treatment_cnae_j_share() -> pd.DataFrame:
    pieces = []
    columns = ["ano", "mes", "cbo_2002", "saldo_movimentacao", "cnae_2_secao"]
    for _path, df in iter_raw_batches(columns):
        ano = pd.to_numeric(df["ano"], errors="coerce")
        mes = pd.to_numeric(df["mes"], errors="coerce")
        periodo_num = ano * 100 + mes
        saldo = pd.to_numeric(df["saldo_movimentacao"], errors="coerce")
        d = df[(periodo_num < TREATMENT_PERIOD) & saldo.eq(1)].copy()
        if d.empty:
            continue
        d["cbo_4d"] = valid_cbo_4d(d["cbo_2002"])
        d = d[d["cbo_4d"].notna()].copy()
        d["is_cnae_j"] = d["cnae_2_secao"].astype("string").str.strip().eq(TECH_CNAE_SECTION).astype(int)
        agg = d.groupby("cbo_4d", observed=True).agg(total_adm=("is_cnae_j", "size"), cnae_j_adm=("is_cnae_j", "sum")).reset_index()
        pieces.append(agg)
    if not pieces:
        raise RuntimeError("Could not compute pre-treatment CNAE J shares from raw CAGED.")
    out = (
        pd.concat(pieces, ignore_index=True)
        .groupby("cbo_4d", observed=True)
        .agg(total_adm=("total_adm", "sum"), cnae_j_adm=("cnae_j_adm", "sum"))
        .reset_index()
    )
    out["pre_cnae_j_adm_share"] = out["cnae_j_adm"] / out["total_adm"].replace(0, np.nan)
    out["is_cnae_j_tech_cbo"] = out["pre_cnae_j_adm_share"].ge(TECH_CNAE_PRE_ADM_SHARE_THRESHOLD)
    out.to_csv(AUDIT_DIR / "pre_treatment_cnae_j_technology_share.csv", index=False)
    return out


def build_technology_exclusion_table(base: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    samples = [
        ("exclude_cbo21", "Exclui CBO 21xx", base[~base["cbo_4d"].astype(str).str.startswith("21")].copy()),
    ]
    cnae_j = build_pre_treatment_cnae_j_share()[["cbo_4d", "pre_cnae_j_adm_share", "is_cnae_j_tech_cbo"]]
    with_cnae = base.merge(cnae_j, on="cbo_4d", how="left")
    samples.append(
        (
            "exclude_cnae_j_pre50",
            "Exclui CBOs com ≥50% das admissões pré em CNAE J",
            with_cnae[~with_cnae["is_cnae_j_tech_cbo"].fillna(False)].copy(),
        )
    )
    for spec_id, label, data in samples:
        spec_rows = estimate_outcomes(spec_id, label, data, ALL_OUTCOMES)
        for row in spec_rows:
            row["excluded_cbo"] = int(base["cbo_4d"].nunique() - data["cbo_4d"].nunique())
        rows.extend(spec_rows)
    out = pd.DataFrame(rows)
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "technology_exclusion_results.csv", index=False)
    view = out.assign(
        Especificacao=out["spec_label"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        CBOsExcluidos=out["excluded_cbo"].map(lambda v: fmt_number(v, 0)),
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "technology_exclusion_results.md",
        "Robustez excluindo tecnologia",
        view,
        ["Especificacao", "Resultado", "Estimativa", "p", "CBOsExcluidos", "N"],
        note="A exclusão CNAE J usa participação pré-tratamento de admissões em Informação e Comunicação por CBO.",
    )
    return out


def build_canaries_age_outputs(base: pd.DataFrame) -> pd.DataFrame:
    out = estimate_heterogeneity(base, CANARIES_AGE_OUTCOMES, dimensions=CANARIES_AGE_DIMENSIONS)
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "age_cohort_canaries_results.csv", index=False)
    view = out.assign(
        Painel=out["panel"],
        Grupo=out["group_label"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        Pretrend=out["pretrend_status"],
        Poder=out["power_status"],
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=out["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "age_cohort_canaries_results.md",
        "Heterogeneidade por idade no estilo Canaries",
        view,
        ["Painel", "Grupo", "Resultado", "Estimativa", "p", "Pretrend", "Poder", "N", "CBOs"],
        note="Coeficiente estimado: post × tratamento × grupo; cada faixa etária é comparada ao respectivo complemento.",
    )
    return out


def build_automation_augmentation_table(base: pd.DataFrame) -> pd.DataFrame:
    path = DATA_PROCESSED / "anthropic_automation_augmentation_cbo.parquet"
    if not path.exists():
        out = pd.DataFrame(
            [
                {
                    "spec_id": "automation_augmentation_unavailable",
                    "spec_label": "Índice Anthropic indisponível",
                    "result_status": "skipped_missing_input",
                    "error": str(path),
                }
            ]
        )
        out.to_csv(TABLE_DIR / "automation_augmentation_results.csv", index=False)
        (TABLE_DIR / "automation_augmentation_results.md").write_text(
            "# Automação vs augmentação\n\nÍndice Anthropic não encontrado; teste não estimado.\n",
            encoding="utf-8",
        )
        return out
    index = pd.read_parquet(path)
    index["cbo_4d"] = index["cbo_4d"].astype(str).str.zfill(4)
    cols = ["cbo_4d", "anthropic_automation_index", "dominant_mode_cai", "imputation_method"]
    d = base.merge(index[cols], on="cbo_4d", how="left")
    samples = [
        ("automation_sample", "Amostra com automação dominante", d[pd.to_numeric(d["anthropic_automation_index"], errors="coerce").gt(0)].copy()),
        ("augmentation_sample", "Amostra com augmentação/sem uso dominante", d[pd.to_numeric(d["anthropic_automation_index"], errors="coerce").le(0)].copy()),
    ]
    rows: list[dict[str, object]] = []
    for spec_id, label, data in samples:
        spec_rows = estimate_outcomes(spec_id, label, data, ALL_OUTCOMES)
        for row in spec_rows:
            row["sample_cbo"] = int(data["cbo_4d"].nunique())
        rows.extend(spec_rows)
    out = pd.DataFrame(rows)
    out["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in out.itertuples()]
    out.to_csv(TABLE_DIR / "automation_augmentation_results.csv", index=False)
    view = out.assign(
        Amostra=out["spec_label"],
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        CBOsAmostra=out["sample_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "automation_augmentation_results.md",
        "Automação vs augmentação",
        view,
        ["Amostra", "Resultado", "Estimativa", "p", "CBOsAmostra"],
        note="Teste exploratório; o índice Anthropic é reaproveitado como mecanismo, não como definição principal de tratamento.",
    )
    return out


def plot_event_studies(coefficients: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    axes_flat = axes.flatten()
    for ax, (outcome, label) in zip(axes_flat, ALL_OUTCOMES.items(), strict=True):
        view = coefficients[
            (coefficients["outcome"] == outcome)
            & coefficients["coefficient_status"].isin(["estimated", "reference"])
        ].sort_values("t")
        ax.axhline(0, color="#222222", linewidth=0.8)
        ax.axvline(-1, color="#666666", linewidth=0.8, linestyle="--")
        ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
        ax.plot(view["t"], view["coef"], marker="o", markersize=3, linewidth=1.3, color="#1f4e79")
        band = view.dropna(subset=["ci_low", "ci_high"])
        ax.fill_between(
            band["t"].astype(float),
            band["ci_low"].astype(float),
            band["ci_high"].astype(float),
            color="#1f4e79",
            alpha=0.18,
        )
        ax.set_title(label)
        ax.set_xlabel("Meses relativos ao ChatGPT")
        ax.set_ylabel("Coeficiente")
        ax.grid(True, alpha=0.2)
    fig.suptitle("Event study: modelo base G1-G4 vs Not Exposed", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "event_study_main_3plus1.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    for outcome, label in ALL_OUTCOMES.items():
        view = coefficients[
            (coefficients["outcome"] == outcome)
            & coefficients["coefficient_status"].isin(["estimated", "reference"])
        ].sort_values("t")
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.axhline(0, color="#222222", linewidth=0.8)
        ax.axvline(-1, color="#666666", linewidth=0.8, linestyle="--")
        ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
        ax.plot(view["t"], view["coef"], marker="o", markersize=3, linewidth=1.3, color="#1f4e79")
        band = view.dropna(subset=["ci_low", "ci_high"])
        ax.fill_between(band["t"].astype(float), band["ci_low"].astype(float), band["ci_high"].astype(float), color="#1f4e79", alpha=0.18)
        ax.set_title(label)
        ax.set_xlabel("Meses relativos ao ChatGPT")
        ax.set_ylabel("Coeficiente")
        ax.grid(True, alpha=0.2)
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / f"event_study_{outcome}.png", dpi=180, bbox_inches="tight")
        plt.close(fig)


def build_event_study_outputs(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefficients, pretrends = estimate_event_study(base, ALL_OUTCOMES)
    coefficients.to_csv(TABLE_DIR / "event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(TABLE_DIR / "event_study_pretrend_tests.csv", index=False)
    plot_event_studies(coefficients)
    view = pretrends.assign(
        Resultado=pretrends["outcome_label"],
        CoefsPre=pretrends["n_pre_coefficients"].map(lambda v: fmt_number(v, 0)),
        SigPre=pretrends["n_pre_p_lt_005"].map(lambda v: fmt_number(v, 0)),
        pConjunto=pretrends["joint_p_value"].map(lambda v: fmt_number(v, 4)),
        Status=pretrends["pretrend_status"],
    )
    write_markdown_table(
        TABLE_DIR / "event_study_pretrend_tests.md",
        "Testes de pre-trends do event study",
        view,
        ["Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"],
        note="Falhas de pre-trend reduzem a força causal da leitura do respectivo outcome.",
    )
    return coefficients, pretrends


def build_heterogeneity_outputs(base: pd.DataFrame) -> pd.DataFrame:
    heterogeneity = estimate_heterogeneity(base)
    heterogeneity["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in heterogeneity.itertuples()]
    heterogeneity.to_csv(TABLE_DIR / "heterogeneity_triple_did_long.csv", index=False)
    view = heterogeneity.assign(
        Painel=heterogeneity["panel"],
        Grupo=heterogeneity["group_label"],
        Resultado=heterogeneity["outcome_label"],
        Estimativa=heterogeneity["estimate_se"],
        p=heterogeneity["p_value"].map(lambda v: fmt_number(v, 3)),
        Pretrend=heterogeneity["pretrend_status"],
        Poder=heterogeneity["power_status"],
        N=heterogeneity["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=heterogeneity["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "heterogeneity_triple_did.md",
        "Tabela de heterogeneidade por interação tripla",
        view,
        ["Painel", "Grupo", "Resultado", "Estimativa", "p", "Pretrend", "Poder", "N", "CBOs"],
        note="Coeficiente estimado: post × tratamento × grupo, sempre no modelo base G1-G4 vs Not Exposed.",
    )
    return heterogeneity


def build_real_wage_heterogeneity_outputs(base: pd.DataFrame) -> pd.DataFrame:
    heterogeneity = estimate_heterogeneity(base, REAL_HETEROGENEITY_OUTCOMES)
    heterogeneity["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in heterogeneity.itertuples()]
    heterogeneity.to_csv(TABLE_DIR / "heterogeneity_real_wage_triple_did_long.csv", index=False)
    view = heterogeneity.assign(
        Painel=heterogeneity["panel"],
        Grupo=heterogeneity["group_label"],
        Resultado=heterogeneity["outcome_label"],
        Estimativa=heterogeneity["estimate_se"],
        p=heterogeneity["p_value"].map(lambda v: fmt_number(v, 3)),
        Pretrend=heterogeneity["pretrend_status"],
        Poder=heterogeneity["power_status"],
        N=heterogeneity["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=heterogeneity["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "heterogeneity_real_wage_triple_did.md",
        "Tabela de heterogeneidade com salário real",
        view,
        ["Painel", "Grupo", "Resultado", "Estimativa", "p", "Pretrend", "Poder", "N", "CBOs"],
        note="Coeficiente estimado: post × tratamento × grupo; outcome deflacionado por IPCA mensal.",
    )
    return heterogeneity


def write_role_audit(strict_roles: pd.DataFrame, broad_roles: pd.DataFrame) -> pd.DataFrame:
    rows = [
        role_summary(strict_roles, "Base strict: G1-G4 vs Not Exposed"),
        role_summary(broad_roles, "Broad robustness: G1-G4 vs Not Exposed + Minimal Exposure"),
    ]
    out = pd.DataFrame(rows)
    out.to_csv(AUDIT_DIR / "treatment_role_summary.csv", index=False)
    return out


def write_income_group_audit(base: pd.DataFrame) -> pd.DataFrame:
    assignments = build_pre_treatment_income_group_assignments()
    roles = base[["cbo_4d", "scenario_role", "scenario_treat"]].drop_duplicates("cbo_4d").copy()
    roles["cbo_4d"] = roles["cbo_4d"].astype(str).str.zfill(4)
    out = assignments.merge(roles, on="cbo_4d", how="inner", validate="one_to_one")
    out = out.sort_values("cbo_4d").reset_index(drop=True)
    out.to_csv(AUDIT_DIR / "pre_treatment_income_group_assignments.csv", index=False)
    return out


def write_referee_audit(main: pd.DataFrame, robustness: pd.DataFrame, pretrends: pd.DataFrame, heterogeneity: pd.DataFrame) -> None:
    failed_main = main[(main["panel"].eq("Principal")) & ~main["result_status"].eq("estimated")]
    failed_robust = robustness[~robustness["result_status"].eq("estimated")]
    pretrend_fail = pretrends[pretrends["pretrend_status"].eq("fail")]
    thin_het = heterogeneity[heterogeneity["power_status"].eq("thin")]
    text = [
        "# Auditoria estilo Referee 2",
        "",
        "## Veredito curto",
        "",
        "O pacote é reprodutível e programático se os hard gates passaram. A leitura causal deve ser proporcional aos diagnósticos de pre-trend e poder amostral abaixo.",
        "",
        "## Code audit",
        "",
        f"- Estimativas principais com falha: {len(failed_main)}.",
        f"- Estimativas de robustez com falha registrada: {len(failed_robust)}.",
        "- Tabelas, figuras e estatísticas são geradas por código; não há edição manual das tabelas finais.",
        "",
        "## Econometrics audit",
        "",
        f"- Outcomes com falha de pre-trend no event study: {len(pretrend_fail)}.",
        f"- Células de heterogeneidade com poder `thin`: {len(thin_het)}.",
        "- Erros padrão clusterizados por CBO 4d no modelo principal; robustez inclui cluster CBO 2d.",
        "- A variável contínua usa a mesma lógica média + dispersão que define os gradientes.",
        "",
        "## Residual risk",
        "",
        "- Heterogeneidade amplia o número de testes; interpretar como evidência de padrões, não como multiplicidade de efeitos principais.",
        "- Salário de demissão permanece complementar pela interpretação econômica menos direta.",
        "- Falhas de pre-trend devem ser descritas explicitamente no texto da dissertação.",
        "",
    ]
    (AUDIT_DIR / "referee2_style_audit.md").write_text("\n".join(text), encoding="utf-8")


def write_report(
    crosswalk: pd.DataFrame,
    main: pd.DataFrame,
    robustness: pd.DataFrame,
    pretrends: pd.DataFrame,
    heterogeneity: pd.DataFrame,
    net_flow: pd.DataFrame,
    net_flow_pretrends: pd.DataFrame,
) -> None:
    crosswalk_md = (TABLE_DIR / "crosswalk_exposure_summary.md").read_text(encoding="utf-8")
    main_md = (TABLE_DIR / "main_results_3plus1.md").read_text(encoding="utf-8")
    net_flow_md = (TABLE_DIR / "net_flow_results.md").read_text(encoding="utf-8")
    net_flow_pretrend_md = (TABLE_DIR / "net_flow_event_study_pretrends.md").read_text(encoding="utf-8")
    robustness_md = (TABLE_DIR / "robustness_results.md").read_text(encoding="utf-8")
    pretrend_md = (TABLE_DIR / "event_study_pretrend_tests.md").read_text(encoding="utf-8")
    heterogeneity_md = (TABLE_DIR / "heterogeneity_triple_did.md").read_text(encoding="utf-8")

    main_salary = main[main["outcome"].eq("ln_salario_adm")].iloc[0]
    salary_phrase = (
        f"O efeito estimado para salário de admissão no modelo base é {fmt_number(main_salary['coef'])}"
        f" ({main_salary['stars'] or 'sem estrela'}, p={fmt_number(main_salary['p_value'], 3)})."
    )
    failed_pretrends = int(pretrends["pretrend_status"].eq("fail").sum())
    failed_net_flow_pretrends = int(net_flow_pretrends["pretrend_status"].eq("fail").sum())
    failed_het_pretrends = int(heterogeneity["pretrend_status"].eq("fail").sum())
    net_flow_asinh = net_flow[net_flow["outcome"].eq("asinh_saldo")]
    net_flow_phrase = "sem estimativa disponível"
    if not net_flow_asinh.empty:
        net_row = net_flow_asinh.iloc[0]
        net_flow_phrase = f"{fmt_number(net_row['coef'])}{net_row['stars'] or ''} (p={fmt_number(net_row['p_value'], 3)})"
    g4_count = int(crosswalk.loc[crosswalk["gradient"].eq("Exposed: Gradient 4"), "n_cbo"].sum())
    g4_note = ""
    if g4_count == 0:
        g4_note = (
            "\nNota de classificação: o conjunto tratado aceita G1-G4, mas nesta versão do "
            "`cbo_ilo_gradient` nenhum CBO 4 dígitos recebeu classificação final `Exposed: Gradient 4`; "
            "a definição efetiva observada é G1-G3 vs `Not Exposed`.\n"
        )
    text = f"""# Relatório Final Do Event Study Da Seção 4

Este relatório consolida o pacote final gerado por `src/scripts/build_section4_final_event_study_package.py`.
A especificação principal compara CBOs expostos nos gradientes OIT 1 a 4 contra CBOs `Not Exposed`.
O grupo `Minimal Exposure` fica fora do controle no modelo base e entra apenas como robustez.

## Descrição Dos Dados E Do Desenho

- Painel: CBO 4 dígitos por mês, a partir de `data/output/painel_2b_ready.parquet`.
- Janela: meses disponíveis no painel Stage 2b, com pós-tratamento a partir de dezembro de 2022.
- Tratamento principal: `Exposed: Gradient 1`, `2`, `3` ou `4`.
- Controle principal: somente `Not Exposed`.
- Controles: idade média, percentual de mulheres, percentual com superior e percentual de trabalhadores negros nas admissões.
- Erros padrão: clusterizados por CBO 4 dígitos no modelo principal.
- Pesos: robustez ponderada por média mensal pré-ChatGPT de admissões por CBO.
{g4_note}

{crosswalk_md}

## Resultados Principais

{salary_phrase}

{main_md}

## Saldo Líquido

O saldo líquido é uma variável complementar de fluxo, definida como admissões menos desligamentos.
Ele resume a direção líquida da reconfiguração, mas não substitui admissões e demissões separadas.
A estimativa base para `asinh(saldo)` é {net_flow_phrase}.

{net_flow_md}

{net_flow_pretrend_md}

No event study de saldo líquido, {failed_net_flow_pretrends} outcomes foram classificados como `fail` em pre-trends.

## Event Study E Pre-Trends

![Event study principal](final_event_study/figures/event_study_main_3plus1.png)

{pretrend_md}

No event study, {failed_pretrends} outcomes foram classificados como `fail` em pre-trends. Esses casos devem ser descritos como limitação à leitura causal.

## Robustez

{robustness_md}

## Heterogeneidade

A heterogeneidade abaixo usa apenas o modelo base novo e estima `post × tratamento × grupo`.
Cada grupo é comparado ao respectivo complemento. O bloco inclui renda, idade, sexo, escolaridade e raça/cor.
Há {failed_het_pretrends} células de heterogeneidade com falha no teste de tendência diferencial pré-tratamento.

{heterogeneity_md}

## Arquivos Auditáveis

- `final_event_study/tables/main_results_3plus1.csv`
- `final_event_study/tables/event_study_coefficients_long.csv`
- `final_event_study/tables/event_study_pretrend_tests.csv`
- `final_event_study/tables/robustness_results_long.csv`
- `final_event_study/tables/heterogeneity_triple_did_long.csv`
- `final_event_study/audit/treatment_role_summary.csv`
- `final_event_study/audit/referee2_style_audit.md`
"""
    REPORT_PATH.write_text(text, encoding="utf-8")


def write_real_wage_report(real_main: pd.DataFrame, real_heterogeneity: pd.DataFrame) -> None:
    real_main_md = (TABLE_DIR / "real_wage_main_results_3plus1.md").read_text(encoding="utf-8")
    real_het_md = (TABLE_DIR / "heterogeneity_real_wage_triple_did.md").read_text(encoding="utf-8")
    salary = real_main[real_main["outcome"].eq("ln_salario_real_adm")].iloc[0]
    star_label = salary["stars"] if isinstance(salary["stars"], str) and salary["stars"] else "sem estrela"
    text = f"""# Resultados Com Salário Real Da Seção 4

Este suplemento estima a especificação base final da Seção 4 com salários deflacionados pelo IPCA mensal, base dezembro de 2024 = 100. A definição de tratamento e controle permanece igual: gradientes expostos contra `Not Exposed`, com `Minimal Exposure` fora do controle base.

Como as regressões incluem efeito fixo de mês, deflacionar salários por um índice mensal comum não deve alterar materialmente o coeficiente de tratamento em relação ao log do salário nominal. A tabela fica registrada como robustez explícita.

O coeficiente base para salário real de admissão é {fmt_number(salary['coef'])} ({star_label}, p={fmt_number(salary['p_value'], 3)}).

{real_main_md}

## Heterogeneidade Com Salário Real

A tabela de heterogeneidade abaixo substitui salários nominais de admissão por salários de admissão deflacionados pelo IPCA. Outcomes de fluxo não são repetidos aqui porque não dependem do deflator salarial.

{real_het_md}
"""
    REAL_WAGE_REPORT_PATH.write_text(text, encoding="utf-8")


def _compact_effects(rows: pd.DataFrame, outcome: str) -> str:
    view = rows[rows["outcome"].eq(outcome)].copy()
    if view.empty:
        return "sem estimativa"
    parts = []
    for row in view.itertuples():
        label = getattr(row, "spec_label", getattr(row, "group_label", "spec"))
        parts.append(f"{label}: {fmt_number(row.coef)}{row.stars or ''} (p={fmt_number(row.p_value, 3)})")
    return "; ".join(parts)


def write_final_model_decision_report(
    main: pd.DataFrame,
    model_ladder: pd.DataFrame,
    poisson: pd.DataFrame,
    gradient: pd.DataFrame,
    technology: pd.DataFrame,
    canaries_age: pd.DataFrame,
    automation: pd.DataFrame,
    pretrends: pd.DataFrame,
) -> pd.DataFrame:
    salary_ladder = _compact_effects(model_ladder, "ln_salario_adm")
    admissions_poisson = _compact_effects(poisson, "admissoes")
    dismissals_poisson = _compact_effects(poisson, "desligamentos")
    canaries_sig = canaries_age[
        canaries_age["result_status"].eq("estimated")
        & pd.to_numeric(canaries_age["p_value"], errors="coerce").lt(0.10)
    ].copy()
    canaries_sig_text = "nenhuma célula p<0,10"
    if not canaries_sig.empty:
        canaries_sig_text = "; ".join(
            f"{r.group_label} / {r.outcome_label}: {fmt_number(r.coef)}{r.stars or ''} (p={fmt_number(r.p_value, 3)}, pretrend={r.pretrend_status})"
            for r in canaries_sig.head(8).itertuples()
        )
    flow_pretrend_fail = pretrends[pretrends["outcome"].isin(["ln_admissoes", "ln_desligamentos"])]["pretrend_status"].eq("fail").sum()
    salary_pretrend = pretrends.loc[pretrends["outcome"].eq("ln_salario_adm"), "pretrend_status"]
    salary_pretrend_text = salary_pretrend.iloc[0] if not salary_pretrend.empty else "not_available"
    automation_status = "estimado" if not automation.empty and "skipped" not in str(automation.get("result_status", pd.Series(dtype=str)).iloc[0]) else "não estimado"

    decisions = pd.DataFrame(
        [
            {
                "decision_area": "Base de dados e tratamento",
                "recommendation": "Usar painel corrigido com crosswalk MTE oficial e tratamento G1-G4 vs Not Exposed.",
                "evidence": "Minimal Exposure fica fora da base e entra só como controle amplo; No score e sem MTE ficam fora.",
                "text_placement": "Texto principal",
            },
            {
                "decision_area": "Controles",
                "recommendation": "Apresentar a tabela principal com controles contemporâneos e uma tabela curta de ladder; discutir risco de bad controls.",
                "evidence": salary_ladder,
                "text_placement": "Texto principal + nota metodológica",
            },
            {
                "decision_area": "Fluxos de emprego",
                "recommendation": "Manter admissões e demissões como outcomes centrais, mas reportar Poisson como robustez Canaries.",
                "evidence": f"Poisson admissões: {admissions_poisson}. Poisson demissões: {dismissals_poisson}. Pretrend fail em {flow_pretrend_fail} outcomes de fluxo.",
                "text_placement": "Texto principal com cautela causal",
            },
            {
                "decision_area": "Salário",
                "recommendation": "Reportar salário de admissão como margem complementar importante, não como único headline forte.",
                "evidence": f"Ladder salário: {salary_ladder}. Pretrend salário admissão: {salary_pretrend_text}.",
                "text_placement": "Texto principal",
            },
            {
                "decision_area": "Idade estilo Canaries",
                "recommendation": "Usar apenas se os resultados por coorte forem estáveis e com pretrend aceitável; caso contrário deixar como heterogeneidade exploratória.",
                "evidence": canaries_sig_text,
                "text_placement": "Tabela de heterogeneidade ou anexo",
            },
            {
                "decision_area": "Robustez que entra",
                "recommendation": "Incluir Poisson, controle amplo com Minimal, placebo, pretrends, cluster CBO2d, exclusão tecnológica e ladder de controles.",
                "evidence": "Esses testes respondem diretamente a críticas de contagem zero, grupo de controle, timing, inferência e choque tech.",
                "text_placement": "Texto principal ou apêndice curto",
            },
            {
                "decision_area": "Robustez que fica em anexo",
                "recommendation": "Deixar pesos, contínua média+dispersão, decomposição por gradiente, MTE top20 e automação/augmentação como tabelas auditáveis.",
                "evidence": f"Automação/augmentação: {automation_status}; decomposição por gradiente e pesos ajudam auditoria, mas geram ruído como narrativa principal.",
                "text_placement": "Anexo/auditoria",
            },
        ]
    )
    decisions.to_csv(TABLE_DIR / "final_model_decision_table.csv", index=False)
    view = decisions.rename(
        columns={
            "decision_area": "Decisao",
            "recommendation": "Recomendacao",
            "evidence": "Evidencia",
            "text_placement": "OndeEntrar",
        }
    )
    write_markdown_table(
        TABLE_DIR / "final_model_decision_table.md",
        "Tabela de decisão do modelo final",
        view,
        ["Decisao", "Recomendacao", "Evidencia", "OndeEntrar"],
        note="A decisão prioriza defensibilidade metodológica, não apenas significância estatística.",
    )

    ladder_md = (TABLE_DIR / "model_ladder_controls.md").read_text(encoding="utf-8")
    poisson_md = (TABLE_DIR / "poisson_flow_results.md").read_text(encoding="utf-8")
    canaries_md = (TABLE_DIR / "age_cohort_canaries_results.md").read_text(encoding="utf-8")
    gradient_md = (TABLE_DIR / "gradient_decomposition_results.md").read_text(encoding="utf-8")
    technology_md = (TABLE_DIR / "technology_exclusion_results.md").read_text(encoding="utf-8")
    decision_md = (TABLE_DIR / "final_model_decision_table.md").read_text(encoding="utf-8")
    text = f"""# Relatório De Decisão Do Modelo Final Da Seção 4

## Veredito

A versão base recomendada continua sendo o painel corrigido com crosswalk MTE oficial e o contraste `G1-G4 vs Not Exposed`, com `Minimal Exposure` fora do controle principal. A dissertação deve apresentar os resultados como uma adaptação ao desenho de `Canaries in the Coal Mine` para fluxos formais do CAGED, não como réplica exata do painel firma-estoque do artigo.

O resultado deve ser escrito com cautela: os fluxos são a margem mais comparável ao artigo, mas têm falhas de pretrend; salário de admissão tem pretrend mais limpo, mas magnitude e significância são sensíveis. O pacote novo deve substituir os notebooks antigos como fonte de verdade.

{decision_md}

## Ladder De Controles

{ladder_md}

## Poisson Para Contagens

{poisson_md}

## Idade No Estilo Canaries

{canaries_md}

## Decomposição Por Gradiente

{gradient_md}

## Exclusão Tecnológica

{technology_md}

## Arquivos Complementares

- `final_event_study/tables/automation_augmentation_results.md`
- `final_event_study/tables/gradient_decomposition_results.csv`
- `final_event_study/tables/age_cohort_canaries_results.csv`
- `final_event_study/audit/pre_treatment_cnae_j_technology_share.csv`
"""
    (FINAL_OUTPUT.parent / "section4_final_model_decision_report.md").write_text(text, encoding="utf-8")
    return decisions


def validate_outputs(
    strict_roles: pd.DataFrame,
    broad_roles: pd.DataFrame,
    main: pd.DataFrame,
    robustness: pd.DataFrame,
    coefficients: pd.DataFrame,
    net_flow: pd.DataFrame,
    net_flow_coefficients: pd.DataFrame,
) -> None:
    validate_base_and_broad_roles(strict_roles, broad_roles)
    required_files = [
        REPORT_PATH,
        TABLE_DIR / "crosswalk_exposure_summary.csv",
        TABLE_DIR / "crosswalk_exposure_summary.md",
        TABLE_DIR / "main_results_3plus1.csv",
        TABLE_DIR / "main_results_3plus1.md",
        TABLE_DIR / "event_study_coefficients_long.csv",
        TABLE_DIR / "event_study_pretrend_tests.csv",
        TABLE_DIR / "net_flow_results.csv",
        TABLE_DIR / "net_flow_results.md",
        TABLE_DIR / "net_flow_event_study_coefficients_long.csv",
        TABLE_DIR / "net_flow_event_study_pretrends.csv",
        TABLE_DIR / "net_flow_event_study_pretrends.md",
        TABLE_DIR / "net_flow_heterogeneity_long.csv",
        TABLE_DIR / "net_flow_heterogeneity.md",
        TABLE_DIR / "net_flow_summary.md",
        TABLE_DIR / "robustness_results_long.csv",
        TABLE_DIR / "heterogeneity_triple_did_long.csv",
        FIGURE_DIR / "event_study_main_3plus1.png",
        FIGURE_DIR / "event_study_asinh_saldo.png",
        FIGURE_DIR / "event_study_saldo_per_pre_adm.png",
        AUDIT_DIR / "treatment_role_summary.csv",
        AUDIT_DIR / "pre_treatment_income_group_assignments.csv",
        AUDIT_DIR / "referee2_style_audit.md",
    ]
    missing = [str(path) for path in required_files if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("Missing or empty final event-study artifacts:\n" + "\n".join(missing))
    main_principal = main[main["panel"].eq("Principal")]
    if set(main_principal["outcome"]) != set(MAIN_OUTCOMES):
        raise RuntimeError("Main table does not contain all three principal outcomes.")
    if not main_principal["result_status"].eq("estimated").all():
        raise RuntimeError("At least one principal outcome failed estimation.")
    if "ln_salario_desl" not in set(main["outcome"]):
        raise RuntimeError("Complementary dismissal wage outcome is missing.")
    ref = coefficients[coefficients["t"].eq(-1)]
    if set(ref["outcome"]) != set(ALL_OUTCOMES):
        raise RuntimeError("Event study reference-period rows are incomplete.")
    if not (ref["coef"].eq(0).all() and ref["se"].eq(0).all()):
        raise RuntimeError("Event study reference period must have coefficient and standard error equal to zero.")
    if set(net_flow["outcome"]) != set(NET_FLOW_OUTCOMES):
        raise RuntimeError("Net-flow table does not contain all expected outcomes.")
    if not net_flow["result_status"].eq("estimated").all():
        raise RuntimeError("At least one net-flow outcome failed estimation.")
    net_ref = net_flow_coefficients[net_flow_coefficients["t"].eq(-1)]
    if set(net_ref["outcome"]) != set(NET_FLOW_EVENT_OUTCOMES):
        raise RuntimeError("Net-flow event study reference-period rows are incomplete.")
    if not (net_ref["coef"].eq(0).all() and net_ref["se"].eq(0).all()):
        raise RuntimeError("Net-flow event study reference period must have coefficient and standard error equal to zero.")
    if robustness["stars"].isna().all():
        raise RuntimeError("Robustness table has no significance-star column values.")
    real_files = [
        REAL_WAGE_REPORT_PATH,
        FINAL_OUTPUT.parent / "section4_final_model_decision_report.md",
        TABLE_DIR / "real_wage_main_results_3plus1.csv",
        TABLE_DIR / "real_wage_main_results_3plus1.md",
        TABLE_DIR / "heterogeneity_real_wage_triple_did_long.csv",
        TABLE_DIR / "heterogeneity_real_wage_triple_did.md",
        TABLE_DIR / "model_ladder_controls.csv",
        TABLE_DIR / "model_ladder_controls.md",
        TABLE_DIR / "poisson_flow_results.csv",
        TABLE_DIR / "poisson_flow_results.md",
        TABLE_DIR / "age_cohort_canaries_results.csv",
        TABLE_DIR / "age_cohort_canaries_results.md",
        TABLE_DIR / "gradient_decomposition_results.csv",
        TABLE_DIR / "gradient_decomposition_results.md",
        TABLE_DIR / "technology_exclusion_results.csv",
        TABLE_DIR / "technology_exclusion_results.md",
        TABLE_DIR / "final_model_decision_table.csv",
        TABLE_DIR / "final_model_decision_table.md",
    ]
    missing_real = [str(path) for path in real_files if not path.exists() or path.stat().st_size == 0]
    if missing_real:
        raise RuntimeError("Missing or empty real-wage artifacts:\n" + "\n".join(missing_real))
    report = REPORT_PATH.read_text(encoding="utf-8")
    for required_text in ["Resultados Principais", "Saldo Líquido", "Event Study", "Robustez", "Heterogeneidade", "Minimal Exposure"]:
        if required_text not in report:
            raise RuntimeError(f"Final report is missing required text: {required_text}")


def run_pipeline() -> None:
    prepare_output_dirs()
    log("Loading Stage 2 panel and scenario classification...")
    panel, classification = load_analysis_data()

    strict_roles = assign_roles(classification, "main_strict")
    broad_roles = assign_roles(classification, "main_broad_control")
    validate_base_and_broad_roles(strict_roles, broad_roles)
    write_role_audit(strict_roles, broad_roles)

    log("Applying main strict treatment definition...")
    base = apply_roles(panel, strict_roles)
    base.to_csv(AUDIT_DIR / "main_strict_estimation_sample.csv", index=False)
    write_income_group_audit(base)

    log("Building crosswalk/exposure table...")
    crosswalk = build_crosswalk_table(classification, strict_roles, broad_roles)

    log("Estimating main 3+1 table...")
    main = build_main_table(base)

    log("Estimating real-wage main 3+1 table...")
    real_main = build_real_wage_main_table(base)

    log("Estimating control ladder table...")
    model_ladder = build_model_ladder_table(base)

    log("Estimating Poisson flow robustness...")
    poisson = build_poisson_flow_table(base)

    log("Estimating net-flow balance outcomes...")
    net_flow, net_flow_coefficients, net_flow_pretrends, net_flow_heterogeneity = build_net_flow_outputs(base)

    log("Estimating robustness table...")
    robustness = build_robustness_table(panel, classification, base)

    log("Estimating gradient decomposition table...")
    gradient = build_gradient_decomposition_table(panel, classification)

    log("Estimating technology exclusion robustness...")
    technology = build_technology_exclusion_table(base)

    log("Estimating event studies...")
    coefficients, pretrends = build_event_study_outputs(base)

    log("Estimating heterogeneity triple-DiD block...")
    heterogeneity = build_heterogeneity_outputs(base)

    log("Estimating real-wage heterogeneity triple-DiD block...")
    real_heterogeneity = build_real_wage_heterogeneity_outputs(base)

    log("Estimating Canaries-style age cohort block...")
    canaries_age = build_canaries_age_outputs(base)

    log("Estimating automation vs augmentation exploratory block...")
    automation = build_automation_augmentation_table(base)

    log("Writing final report and audit...")
    write_referee_audit(main, robustness, pretrends, heterogeneity)
    write_report(crosswalk, main, robustness, pretrends, heterogeneity, net_flow, net_flow_pretrends)
    write_real_wage_report(real_main, real_heterogeneity)
    write_final_model_decision_report(
        main,
        model_ladder,
        poisson,
        gradient,
        technology,
        canaries_age,
        automation,
        pretrends,
    )

    log("Validating final outputs...")
    validate_outputs(strict_roles, broad_roles, main, robustness, coefficients, net_flow, net_flow_coefficients)
    log(f"Done. Final report written to {REPORT_PATH}")
