"""Pipeline for the Section 4 connectivity extension."""

from __future__ import annotations

import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from section4_event_study.formatting import estimate_cell, fmt_number, markdown_table, write_markdown_table

from .config import (
    AUDIT_DIR,
    CANARIES_AGE_OUTCOMES,
    CONNECTIVITY_PANEL_PATH,
    CONNECTIVITY_PROXIES,
    DEMOGRAPHIC_OUTCOMES,
    FE_SPECS,
    FIGURE_DIR,
    FLOW_OUTCOMES,
    LOG_FLOW_OUTCOMES,
    MAIN_OUTCOMES,
    NET_FLOW_OUTCOMES,
    OUTPUT_ROOT,
    PLACEBO_PERIOD,
    REPORT_PATH,
    TABLE_DIR,
    TREATMENT_PERIOD,
    WAGE_OUTCOMES,
)
from .data import build_connectivity_panel
from .estimation import estimate_event_study, estimate_term


ROBUSTNESS_CORE_LOG_OUTCOMES = {
    "ln_admissoes": LOG_FLOW_OUTCOMES["ln_admissoes"],
    "ln_desligamentos": LOG_FLOW_OUTCOMES["ln_desligamentos"],
}

ROBUSTNESS_CORE_WAGE_OUTCOMES = {
    "ln_salario_real_adm": WAGE_OUTCOMES["ln_salario_real_adm"],
}

DIAGNOSTIC_FE_SPEC = "legacy"


def log(message: str) -> None:
    print(message, flush=True)


def prepare_output_dirs() -> None:
    for path in [TABLE_DIR, FIGURE_DIR, AUDIT_DIR]:
        path.mkdir(parents=True, exist_ok=True)
        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)


def result_row(
    spec_id: str,
    spec_label: str,
    outcome: str,
    outcome_label: str,
    estimator: str,
    est: dict[str, object],
    term: str = "post_treat_connect",
) -> dict[str, object]:
    return {
        "spec_id": spec_id,
        "spec_label": spec_label,
        "outcome": outcome,
        "outcome_label": outcome_label,
        "estimator": estimator,
        "term": term,
        **est,
    }


def write_result_table(path, title: str, data: pd.DataFrame, note: str = "") -> None:
    if data.empty:
        path.write_text(f"# {title}\n\n_Sem resultados estimados._\n", encoding="utf-8")
        return
    view = data.assign(
        Especificacao=data["spec_label"],
        Resultado=data["outcome_label"],
        Estimador=data["estimator"],
        Estimativa=[estimate_cell(r.coef, r.se, r.stars) for r in data.itertuples()],
        p=data["p_value"].map(lambda v: fmt_number(v, 3)),
        N=data["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=data["n_cbo"].map(lambda v: fmt_number(v, 0)),
        Municipios=data["n_municipios"].map(lambda v: fmt_number(v, 0)),
        Status=data["result_status"],
    )
    write_markdown_table(
        path,
        title,
        view,
        ["Especificacao", "Resultado", "Estimador", "Estimativa", "p", "N", "CBOs", "Municipios", "Status"],
        note=note,
    )


def build_sample_audit(panel: pd.DataFrame) -> pd.DataFrame:
    audit = pd.DataFrame(
        [
            {
                "metric": "rows",
                "value": len(panel),
            },
            {"metric": "cbo", "value": panel["cbo_4d"].nunique()},
            {"metric": "municipios", "value": panel["id_municipio"].nunique()},
            {"metric": "periodos", "value": panel["periodo"].nunique()},
            {"metric": "treated_cbo", "value": panel.loc[panel["scenario_treat"].eq(1), "cbo_4d"].nunique()},
            {"metric": "control_cbo", "value": panel.loc[panel["scenario_role"].eq("control"), "cbo_4d"].nunique()},
            {"metric": "minimal_rows", "value": int(panel["cbo_ilo_gradient"].eq("Minimal Exposure").sum())},
            {"metric": "no_score_rows", "value": int(panel["cbo_ilo_gradient"].eq("No score").sum())},
            {"metric": "wage_adm_missing", "value": int(panel["ln_salario_real_adm"].isna().sum())},
            {"metric": "wage_desl_missing", "value": int(panel["ln_salario_real_desl"].isna().sum())},
        ]
    )
    audit.to_csv(AUDIT_DIR / "sample_validation.csv", index=False)
    roles = (
        panel[["cbo_4d", "scenario_role", "scenario_treat", "cbo_ilo_gradient", "mte_match_status"]]
        .drop_duplicates()
        .sort_values(["scenario_role", "cbo_4d"])
    )
    roles.to_csv(AUDIT_DIR / "treatment_roles.csv", index=False)
    return audit


def build_connectivity_balance(panel: pd.DataFrame) -> pd.DataFrame:
    pre = panel[panel["post"].eq(0)].copy()
    balance = (
        pre.groupby("high_connect", observed=True)
        .agg(
            rows=("cbo_4d", "size"),
            municipios=("id_municipio", "nunique"),
            cbo=("cbo_4d", "nunique"),
            admissoes=("admissoes", "sum"),
            desligamentos=("desligamentos", "sum"),
            salario_real_adm=("ln_salario_real_adm", lambda s: float(np.exp(s.dropna()).mean()) if s.notna().any() else np.nan),
            penetracao_bl=("penetracao_bl", "mean"),
            pct_fibra_pre=("pct_fibra_pre", "mean"),
            pib_per_capita=("pib_per_capita", "mean"),
            populacao=("populacao", "mean"),
        )
        .reset_index()
    )
    balance.to_csv(TABLE_DIR / "connectivity_balance.csv", index=False)
    view = balance.assign(
        Grupo=np.where(balance["high_connect"].eq(1), "Alta conectividade", "Baixa conectividade"),
        Linhas=balance["rows"].map(lambda v: fmt_number(v, 0)),
        Municipios=balance["municipios"].map(lambda v: fmt_number(v, 0)),
        CBOs=balance["cbo"].map(lambda v: fmt_number(v, 0)),
        Admissoes=balance["admissoes"].map(lambda v: fmt_number(v, 0)),
        Desligamentos=balance["desligamentos"].map(lambda v: fmt_number(v, 0)),
        Penetracao=balance["penetracao_bl"].map(lambda v: fmt_number(v, 3)),
        Fibra=balance["pct_fibra_pre"].map(lambda v: fmt_number(v, 3)),
        PIBpc=balance["pib_per_capita"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        TABLE_DIR / "connectivity_balance.md",
        "Balanço pré-tratamento por conectividade",
        view,
        ["Grupo", "Linhas", "Municipios", "CBOs", "Admissoes", "Desligamentos", "Penetracao", "Fibra", "PIBpc"],
        note="Conectividade é definida com informação pré-ChatGPT.",
    )
    return balance


def estimate_main(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome, label in LOG_FLOW_OUTCOMES.items():
        est = estimate_term(panel, outcome, fe_spec="strong", model_type="ols")
        rows.append(result_row("main_strong_log_ols", FE_SPECS["strong"]["label"], outcome, label, "OLS log", est))
    for outcome, label in WAGE_OUTCOMES.items():
        est = estimate_term(panel, outcome, fe_spec="strong", model_type="ols")
        rows.append(result_row("main_strong_ols", FE_SPECS["strong"]["label"], outcome, label, "OLS", est))
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "main_connectivity_triple_did.csv", index=False)
    write_result_table(
        TABLE_DIR / "main_connectivity_triple_did.md",
        "Triple-DID principal de conectividade",
        out,
        note="Coeficiente de interesse: post x exposto x alta conectividade.",
    )
    return out


def build_model_ladder(panel: pd.DataFrame, main: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    for fe_spec in ["legacy", "cell_local"]:
        spec = FE_SPECS[fe_spec]
        for outcome, label in LOG_FLOW_OUTCOMES.items():
            est = estimate_term(panel, outcome, fe_spec=fe_spec, model_type="ols")
            rows.append(result_row(fe_spec, spec["label"], outcome, label, "OLS log", est))
        for outcome, label in WAGE_OUTCOMES.items():
            est = estimate_term(panel, outcome, fe_spec=fe_spec, model_type="ols")
            rows.append(result_row(fe_spec, spec["label"], outcome, label, "OLS", est))
    out = pd.DataFrame(rows)
    if main is not None and not main.empty:
        out = pd.concat([out, main.assign(spec_id="strong_main_reused")], ignore_index=True)
    out.to_csv(TABLE_DIR / "model_ladder_connectivity.csv", index=False)
    write_result_table(
        TABLE_DIR / "model_ladder_connectivity.md",
        "Ladder de especificações de conectividade",
        out,
        note="A especificação forte é preferida se convergir e passar nos diagnósticos de pretrend.",
    )
    return out


def build_pre_treatment_technology_share(panel: pd.DataFrame) -> pd.DataFrame:
    if "pct_tecnologico_adm" not in panel.columns:
        return pd.DataFrame(columns=["cbo_4d", "pre_tech_admission_share", "is_high_tech_cbo"])
    pre = panel[panel["post"].eq(0)].copy()
    pre["tech_adm"] = pd.to_numeric(pre["pct_tecnologico_adm"], errors="coerce").fillna(0) * pd.to_numeric(
        pre["admissoes"], errors="coerce"
    ).fillna(0)
    share = (
        pre.groupby("cbo_4d", observed=True)
        .agg(tech_adm=("tech_adm", "sum"), admissoes=("admissoes", "sum"))
        .reset_index()
    )
    share["pre_tech_admission_share"] = share["tech_adm"] / share["admissoes"].replace(0, np.nan)
    share["is_high_tech_cbo"] = share["pre_tech_admission_share"].ge(0.50)
    share.to_csv(AUDIT_DIR / "pre_treatment_technology_share_by_cbo.csv", index=False)
    return share[["cbo_4d", "pre_tech_admission_share", "is_high_tech_cbo"]]


def _rows_for_robust_spec(
    panel: pd.DataFrame,
    spec_id: str,
    spec_label: str,
    term: str,
    extra_terms: list[str],
    sample_filter: pd.Series | None = None,
    cluster: str | None = None,
    weight: str | None = None,
    fe_spec: str = DIAGNOSTIC_FE_SPEC,
    log_outcomes: dict[str, str] | None = None,
    wage_outcomes: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    d = panel.loc[sample_filter] if sample_filter is not None else panel
    rows = []
    selected_log_outcomes = ROBUSTNESS_CORE_LOG_OUTCOMES if log_outcomes is None else log_outcomes
    selected_wage_outcomes = ROBUSTNESS_CORE_WAGE_OUTCOMES if wage_outcomes is None else wage_outcomes
    for outcome, label in selected_log_outcomes.items():
        est = estimate_term(d, outcome, term=term, fe_spec=fe_spec, model_type="ols", extra_terms=extra_terms, cluster=cluster)
        rows.append(result_row(spec_id, spec_label, outcome, label, "OLS log", est, term=term))
    for outcome, label in selected_wage_outcomes.items():
        est = estimate_term(
            d,
            outcome,
            term=term,
            fe_spec=fe_spec,
            model_type="ols",
            extra_terms=extra_terms,
            cluster=cluster,
            weight=weight,
        )
        rows.append(result_row(spec_id, spec_label, outcome, label, "OLS", est, term=term))
    return rows


def build_robustness(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    log("  Robustness: connectivity Q75 vs Q25")
    rows.extend(
        _rows_for_robust_spec(
            panel,
            "connectivity_q75_q25",
            "Conectividade extrema Q75 vs Q25 (FE diagnóstico)",
            "post_treat_connect_q75",
            ["post_treat", "post_high_connect_q75"],
            sample_filter=panel["connectivity_extreme_sample"].eq(True),
        )
    )
    log("  Robustness: continuous connectivity")
    rows.extend(
        _rows_for_robust_spec(
            panel,
            "connectivity_continuous",
            "Conectividade contínua z-score (FE diagnóstico)",
            "post_treat_connect_z",
            ["post_treat", "post_connectivity_z"],
        )
    )
    log("  Robustness: fiber proxy")
    rows.extend(
        _rows_for_robust_spec(
            panel,
            "fiber_proxy",
            "Alta fibra (FE diagnóstico)",
            "post_treat_fiber",
            ["post_treat", "post_high_fiber"],
        )
    )
    log("  Robustness: placebo")
    placebo = panel[panel["periodo_num"].lt(TREATMENT_PERIOD)].copy()
    placebo["post_placebo"] = placebo["periodo_num"].ge(PLACEBO_PERIOD).astype(int)
    placebo["placebo_treat_connect"] = placebo["post_placebo"] * placebo["scenario_treat"] * placebo["high_connect"]
    placebo["placebo_high_connect"] = placebo["post_placebo"] * placebo["high_connect"]
    rows.extend(
        _rows_for_robust_spec(
            placebo,
            "placebo_2021_12",
            "Placebo temporal dez/2021 (FE diagnóstico)",
            "placebo_treat_connect",
            ["post_treat", "placebo_high_connect"],
        )
    )
    log("  Robustness: cluster CBO 4d")
    rows.extend(
        _rows_for_robust_spec(
            panel,
            "cluster_cbo4d",
            "Cluster alternativo CBO 4d (FE diagnóstico)",
            "post_treat_connect",
            ["post_treat", "post_high_connect"],
            cluster="cbo_4d",
        )
    )
    log("  Robustness: weighted wage models")
    rows.extend(
        _rows_for_robust_spec(
            panel,
            "weighted_wages",
            "Salários ponderados por admissões pré da célula (FE diagnóstico)",
            "post_treat_connect",
            ["post_treat", "post_high_connect"],
            weight="pre_cell_adm_weight",
            log_outcomes={},
            wage_outcomes=WAGE_OUTCOMES,
        )
    )
    log("  Robustness: exclude CBO 21xx")
    no_21xx = ~panel["cbo_4d"].astype(str).str.startswith("21")
    rows.extend(
        _rows_for_robust_spec(
            panel,
            "exclude_cbo_21xx",
            "Exclui CBO 21xx (FE diagnóstico)",
            "post_treat_connect",
            ["post_treat", "post_high_connect"],
            sample_filter=no_21xx,
        )
    )
    log("  Robustness: exclude high-tech CBOs")
    tech_share = build_pre_treatment_technology_share(panel)
    if not tech_share.empty:
        high_tech = set(tech_share.loc[tech_share["is_high_tech_cbo"], "cbo_4d"].astype(str))
        rows.extend(
            _rows_for_robust_spec(
                panel,
                "exclude_high_tech_cbo",
                "Exclui CBOs com >=50% das admissões pré em CNAE J (FE diagnóstico)",
                "post_treat_connect",
                ["post_treat", "post_high_connect"],
                sample_filter=~panel["cbo_4d"].astype(str).isin(high_tech),
            )
        )
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "connectivity_robustness.csv", index=False)
    write_result_table(
        TABLE_DIR / "connectivity_robustness.md",
        "Robustez da extensão de conectividade",
        out,
        note=(
            "Estas robustezes usam a especificação diagnóstica legado comparável para manter o pacote reprodutível. "
            "Pesos são aplicados apenas aos modelos OLS de salário."
        ),
    )
    return out


def build_demographic_heterogeneity(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome, label in {**DEMOGRAPHIC_OUTCOMES, **CANARIES_AGE_OUTCOMES}.items():
        if outcome not in panel.columns:
            continue
        log(f"  Heterogeneity: {outcome}")
        est = estimate_term(panel, outcome, fe_spec=DIAGNOSTIC_FE_SPEC, model_type="ols")
        rows.append(result_row("demographic_outcome", "Triple-DID por outcome demográfico", outcome, label, "OLS", est))
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "connectivity_demographic_heterogeneity.csv", index=False)
    write_result_table(
        TABLE_DIR / "connectivity_demographic_heterogeneity.md",
        "Heterogeneidade demográfica da conectividade",
        out,
        note="Cada linha estima o triple-DID usando um outcome demográfico específico em especificação diagnóstica.",
    )
    return out


def _quad_pair(panel: pd.DataFrame, group_id: str, group_label: str, target_col: str, complement_col: str) -> pd.DataFrame:
    pieces = []
    for subgroup, group_value, source_col in [("grupo", 1, target_col), ("complemento", 0, complement_col)]:
        if source_col not in panel.columns:
            continue
        d = panel.copy()
        d["quad_group_id"] = group_id
        d["quad_group_label"] = group_label
        d["quad_subgroup"] = subgroup
        d["quad_group"] = group_value
        d["quad_outcome"] = d[source_col]
        pieces.append(d)
    if not pieces:
        return pd.DataFrame()
    out = pd.concat(pieces, ignore_index=True)
    out["quad_did"] = out["post"] * out["scenario_treat"] * out["high_connect"] * out["quad_group"]
    out["post_treat_group"] = out["post"] * out["scenario_treat"] * out["quad_group"]
    out["post_connect_group"] = out["post"] * out["high_connect"] * out["quad_group"]
    out["post_group"] = out["post"] * out["quad_group"]
    out["quad_subgroup_fe"] = out["quad_group_id"] + "_" + out["quad_subgroup"]
    return out


def build_quadruple_exploratory(panel: pd.DataFrame) -> pd.DataFrame:
    pairs = [
        ("young", "Jovens vs não jovens", "ln_salario_real_jovem", "ln_salario_real_naojovem"),
        ("women", "Mulheres vs homens", "ln_salario_real_mulher", "ln_salario_real_homem"),
        ("black", "Pretos/pardos vs brancos", "ln_salario_real_negro", "ln_salario_real_branco"),
        ("higher", "Superior vs médio", "ln_salario_real_superior", "ln_salario_real_medio"),
    ]
    rows = []
    for group_id, group_label, target_col, complement_col in pairs:
        d = _quad_pair(panel, group_id, group_label, target_col, complement_col)
        if d.empty:
            continue
        est = estimate_term(
            d,
            "quad_outcome",
            term="quad_did",
            fe_spec=DIAGNOSTIC_FE_SPEC,
            model_type="ols",
            extra_terms=["post_treat_connect", "post_treat_group", "post_connect_group", "post_group"],
            extra_required=["quad_subgroup_fe"],
        )
        rows.append(result_row(group_id, group_label, "quad_outcome", group_label, "OLS", est, term="quad_did"))
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "connectivity_quadruple_did_exploratory.csv", index=False)
    write_result_table(
        TABLE_DIR / "connectivity_quadruple_did_exploratory.md",
        "Quadruple-DID exploratório",
        out,
        note="Coeficiente: post x exposto x alta conectividade x grupo. Especificação diagnóstica; usar como anexo, não como headline.",
    )
    return out


def plot_event_study(coefs: pd.DataFrame) -> None:
    if coefs.empty:
        return
    for outcome, d in coefs.groupby("outcome", observed=True):
        d = d.sort_values("t")
        fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
        ax.axhline(0, color="#333333", linewidth=1)
        ax.axvline(-0.5, color="#777777", linestyle="--", linewidth=1)
        ax.plot(d["t"], d["coef"], color="#2f6f9f", linewidth=1.8, marker="o", markersize=3)
        ax.fill_between(d["t"], d["ci_low"], d["ci_high"], color="#2f6f9f", alpha=0.18)
        ax.set_title(str(d["outcome_label"].iloc[0]))
        ax.set_xlabel("Meses relativos a dez/2022")
        ax.set_ylabel("Coeficiente DDD")
        ax.grid(True, alpha=0.25)
        fig.savefig(FIGURE_DIR / f"connectivity_event_study_{outcome}.png", dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(fig)


def build_event_studies(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_outcomes = {**LOG_FLOW_OUTCOMES, **WAGE_OUTCOMES}
    coefs, pretrends = estimate_event_study(panel, event_outcomes, fe_spec=DIAGNOSTIC_FE_SPEC)
    coefs.to_csv(TABLE_DIR / "connectivity_event_study_coefficients.csv", index=False)
    pretrends.to_csv(TABLE_DIR / "connectivity_event_study_pretrends.csv", index=False)
    if not pretrends.empty:
        view = pretrends.assign(
            Resultado=pretrends["outcome_label"],
            CoefsPre=pretrends["coefs_pre"].map(lambda v: fmt_number(v, 0)),
            SigPre=pretrends["sig_pre"].map(lambda v: fmt_number(v, 0)),
            pConjunto=pretrends["joint_p_value"].map(lambda v: fmt_number(v, 4)),
            Status=pretrends["status"],
        )
        write_markdown_table(
            TABLE_DIR / "connectivity_event_study_pretrends.md",
            "Pretrends do event study DDD",
            view,
            ["Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"],
            note="Pretrends em especificação diagnóstica. Falhas de pretrend reduzem a força causal da extensão de conectividade.",
        )
    plot_event_study(coefs)
    return coefs, pretrends


def build_net_flow(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    for outcome, label in NET_FLOW_OUTCOMES.items():
        est = estimate_term(panel, outcome, fe_spec="strong", model_type="ols")
        rows.append(result_row("net_flow_strong", FE_SPECS["strong"]["label"], outcome, label, "OLS", est))
    results = pd.DataFrame(rows)
    results.to_csv(TABLE_DIR / "connectivity_net_flow_results.csv", index=False)
    write_result_table(
        TABLE_DIR / "connectivity_net_flow_results.md",
        "Saldo líquido na extensão de conectividade",
        results,
        note="Coeficiente de interesse: post x exposto x alta conectividade. O saldo é complementar a admissões e demissões separadas.",
    )

    coefs, pretrends = estimate_event_study(panel, NET_FLOW_OUTCOMES, fe_spec=DIAGNOSTIC_FE_SPEC)
    coefs.to_csv(TABLE_DIR / "connectivity_net_flow_event_study_coefficients.csv", index=False)
    pretrends.to_csv(TABLE_DIR / "connectivity_net_flow_event_study_pretrends.csv", index=False)
    if not pretrends.empty:
        view = pretrends.assign(
            Resultado=pretrends["outcome_label"],
            CoefsPre=pretrends["coefs_pre"].map(lambda v: fmt_number(v, 0)),
            SigPre=pretrends["sig_pre"].map(lambda v: fmt_number(v, 0)),
            pConjunto=pretrends["joint_p_value"].map(lambda v: fmt_number(v, 4)),
            Status=pretrends["status"],
        )
        write_markdown_table(
            TABLE_DIR / "connectivity_net_flow_event_study_pretrends.md",
            "Pretrends do saldo líquido na conectividade",
            view,
            ["Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"],
            note="Pretrends em especificação diagnóstica. Falhas são reportadas como limitação causal.",
        )
    else:
        write_markdown_table(
            TABLE_DIR / "connectivity_net_flow_event_study_pretrends.md",
            "Pretrends do saldo líquido na conectividade",
            pd.DataFrame(columns=["Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"]),
            ["Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"],
            note="Nenhuma estimação de pretrend foi produzida; registrar como limitação.",
        )
    plot_event_study(coefs)

    heterogeneity_rows = []
    specs = [
        ("median", "Alta conectividade mediana", "post_treat_connect", ["post_treat", "post_high_connect"], None),
        (
            "q75_q25",
            "Conectividade extrema Q75 vs Q25",
            "post_treat_connect_q75",
            ["post_treat", "post_high_connect_q75"],
            panel["connectivity_extreme_sample"].eq(True),
        ),
        ("fiber", "Alta fibra", "post_treat_fiber", ["post_treat", "post_high_fiber"], None),
        ("continuous", "Conectividade contínua z-score", "post_treat_connect_z", ["post_treat", "post_connectivity_z"], None),
    ]
    for spec_id, spec_label, term, extra_terms, sample_filter in specs:
        d = panel.loc[sample_filter].copy() if sample_filter is not None else panel
        for outcome, label in NET_FLOW_OUTCOMES.items():
            est = estimate_term(d, outcome, term=term, fe_spec=DIAGNOSTIC_FE_SPEC, model_type="ols", extra_terms=extra_terms)
            heterogeneity_rows.append(result_row(spec_id, spec_label, outcome, label, "OLS", est, term=term))
    heterogeneity = pd.DataFrame(heterogeneity_rows)
    heterogeneity.to_csv(TABLE_DIR / "connectivity_net_flow_heterogeneity.csv", index=False)
    write_result_table(
        TABLE_DIR / "connectivity_net_flow_heterogeneity.md",
        "Heterogeneidade espacial do saldo líquido",
        heterogeneity,
        note="Variações por proxy de conectividade: mediana, extremos Q75/Q25, fibra e medida contínua.",
    )
    return results, pretrends, heterogeneity


def _decision_text(main: pd.DataFrame, pretrends: pd.DataFrame) -> str:
    if main.empty:
        return "A extensão não produziu estimações principais válidas."
    failures = int(pretrends["status"].eq("fail").sum()) if not pretrends.empty and "status" in pretrends else 0
    wage = main[main["outcome"].eq("ln_salario_real_adm")]
    wage_text = ""
    if not wage.empty:
        r = wage.iloc[0]
        wage_text = f" Para salário real de admissão, o coeficiente principal é {fmt_number(r['coef'], 4)} (p={fmt_number(r['p_value'], 3)})."
    if failures:
        return (
            "A extensão deve ser apresentada como evidência sugestiva, não como resultado causal central, "
            f"porque {failures} outcome(s) falharam nos pretrends do event study DDD."
            + wage_text
        )
    return "A extensão passa nos diagnósticos automáticos de pretrend e pode entrar como evidência espacial complementar." + wage_text


def write_report(
    main: pd.DataFrame,
    ladder: pd.DataFrame,
    robustness: pd.DataFrame,
    heterogeneity: pd.DataFrame,
    quadruple: pd.DataFrame,
    pretrends: pd.DataFrame,
    net_flow: pd.DataFrame,
    net_flow_pretrends: pd.DataFrame,
    net_flow_heterogeneity: pd.DataFrame,
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        "# Extensão De Conectividade Da Seção 4",
        "## Veredito",
        _decision_text(main, pretrends),
        "## Tabela Principal",
        (TABLE_DIR / "main_connectivity_triple_did.md").read_text(encoding="utf-8"),
        "## Ladder De Especificações",
        (TABLE_DIR / "model_ladder_connectivity.md").read_text(encoding="utf-8"),
        "## Pretrends",
        (TABLE_DIR / "connectivity_event_study_pretrends.md").read_text(encoding="utf-8")
        if (TABLE_DIR / "connectivity_event_study_pretrends.md").exists()
        else "_Sem tabela de pretrend._",
        "## Saldo Líquido",
        (TABLE_DIR / "connectivity_net_flow_results.md").read_text(encoding="utf-8")
        if not net_flow.empty
        else "_Sem saldo líquido estimado._",
        "## Pretrends Do Saldo Líquido",
        (TABLE_DIR / "connectivity_net_flow_event_study_pretrends.md").read_text(encoding="utf-8")
        if not net_flow_pretrends.empty and (TABLE_DIR / "connectivity_net_flow_event_study_pretrends.md").exists()
        else "_Sem pretrends de saldo líquido._",
        "## Heterogeneidade Espacial Do Saldo Líquido",
        (TABLE_DIR / "connectivity_net_flow_heterogeneity.md").read_text(encoding="utf-8")
        if not net_flow_heterogeneity.empty
        else "_Sem heterogeneidade espacial de saldo líquido._",
        "## Robustez",
        (TABLE_DIR / "connectivity_robustness.md").read_text(encoding="utf-8"),
        "## Heterogeneidade",
        (TABLE_DIR / "connectivity_demographic_heterogeneity.md").read_text(encoding="utf-8")
        if not heterogeneity.empty
        else "_Sem heterogeneidade estimada._",
        "## Quadruple-DID Exploratório",
        (TABLE_DIR / "connectivity_quadruple_did_exploratory.md").read_text(encoding="utf-8")
        if not quadruple.empty
        else "_Sem quadruple-DID estimado._",
        "## Interpretação",
        (
            "Esta extensão não substitui o modelo nacional da Seção 4. Ela testa se a conectividade prévia "
            "amplifica o efeito ocupacional da exposição à IA generativa. A tabela principal usa a "
            "especificação forte; ladder, robustez, event study e heterogeneidade são diagnósticos "
            "operacionais em especificações mais leves quando necessário para manter o pacote reprodutível. "
            "Resultados que sobrevivem apenas no modelo legado, mas não na especificação forte ou nos "
            "pretrends, devem ser descritos como padrões espaciais sugestivos."
        ),
    ]
    REPORT_PATH.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def validate_outputs(panel: pd.DataFrame) -> None:
    if panel["cbo_ilo_gradient"].eq("Minimal Exposure").any():
        raise RuntimeError("Minimal Exposure entered the strict connectivity sample.")
    if panel["cbo_ilo_gradient"].eq("No score").any():
        raise RuntimeError("No score entered the strict connectivity sample.")
    if panel.loc[panel["admissoes"].eq(0), "ln_salario_real_adm"].notna().any():
        raise RuntimeError("Admission wages are non-missing in cells with zero admissions.")
    if panel.loc[panel["desligamentos"].eq(0), "ln_salario_real_desl"].notna().any():
        raise RuntimeError("Dismissal wages are non-missing in cells with zero dismissals.")
    required = [
        REPORT_PATH,
        TABLE_DIR / "main_connectivity_triple_did.md",
        TABLE_DIR / "model_ladder_connectivity.md",
        TABLE_DIR / "connectivity_balance.md",
        TABLE_DIR / "connectivity_event_study_pretrends.md",
        TABLE_DIR / "connectivity_net_flow_results.csv",
        TABLE_DIR / "connectivity_net_flow_results.md",
        TABLE_DIR / "connectivity_net_flow_event_study_pretrends.csv",
        TABLE_DIR / "connectivity_net_flow_event_study_pretrends.md",
        TABLE_DIR / "connectivity_net_flow_heterogeneity.csv",
        TABLE_DIR / "connectivity_net_flow_heterogeneity.md",
        TABLE_DIR / "connectivity_robustness.md",
        TABLE_DIR / "connectivity_demographic_heterogeneity.md",
        TABLE_DIR / "connectivity_quadruple_did_exploratory.md",
        AUDIT_DIR / "sample_validation.csv",
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Missing or empty connectivity outputs: {missing}")


def run_pipeline() -> None:
    prepare_output_dirs()
    log("Building corrected municipal connectivity panel...")
    panel = build_connectivity_panel()
    CONNECTIVITY_PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(CONNECTIVITY_PANEL_PATH, index=False)
    log(f"Panel rows: {len(panel):,}; CBOs: {panel['cbo_4d'].nunique():,}; municipalities: {panel['id_municipio'].nunique():,}")

    log("Writing sample audit and connectivity balance...")
    build_sample_audit(panel)
    build_connectivity_balance(panel)

    log("Estimating main connectivity triple-DID...")
    main = estimate_main(panel)

    log("Estimating model ladder...")
    ladder = build_model_ladder(panel, main)

    log("Estimating robustness...")
    robustness = build_robustness(panel)

    log("Estimating event studies and pretrends...")
    _coefs, pretrends = build_event_studies(panel)

    log("Estimating net-flow connectivity outcomes...")
    net_flow, net_flow_pretrends, net_flow_heterogeneity = build_net_flow(panel)

    log("Estimating demographic heterogeneity...")
    heterogeneity = build_demographic_heterogeneity(panel)

    log("Estimating exploratory quadruple-DID...")
    quadruple = build_quadruple_exploratory(panel)

    log("Writing report...")
    write_report(main, ladder, robustness, heterogeneity, quadruple, pretrends, net_flow, net_flow_pretrends, net_flow_heterogeneity)

    log("Validating outputs...")
    validate_outputs(panel)
    log(f"Done. Connectivity report written to {REPORT_PATH}")


if __name__ == "__main__":
    run_pipeline()
