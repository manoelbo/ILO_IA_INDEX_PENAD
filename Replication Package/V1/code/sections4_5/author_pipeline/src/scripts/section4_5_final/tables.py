"""Curated final tables for Sections 4 and 5."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import CORE_OCCUPATION_GROUPS, CORE_OUTCOMES, TABLE_DIR
from .formatting import effect_label, estimate_with_se, evidence_label, fmt_number, fmt_p, write_table_pair
from .section5_2_tables import write_section5_2_tables


def _stars(value: object) -> str:
    return "" if value is None or pd.isna(value) else str(value)


def _pretrend_lookup(pretrends: pd.DataFrame) -> dict[str, str]:
    mapping = {}
    for _, row in pretrends.iterrows():
        mapping[str(row.get("outcome"))] = str(row.get("pretrend_status", row.get("status", "not_available")))
    if "ln_salario_adm" in mapping:
        mapping.setdefault("ln_salario_real_adm", mapping["ln_salario_adm"])
    if "ln_salario_desl" in mapping:
        mapping.setdefault("ln_salario_real_desl", mapping["ln_salario_desl"])
    return mapping


def _standard_rows(df: pd.DataFrame, pretrend_map: dict[str, str]) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        outcome = str(row["outcome"])
        pretrend = pretrend_map.get(outcome, "not_available")
        rows.append(
            {
                "Resultado": row["outcome_label"],
                "Coeficiente": estimate_with_se(row["coef"], row["se"], _stars(row.get("stars"))),
                "Efeito aprox.": effect_label(row["coef"], row["outcome"], row["outcome_label"]),
                "p-valor": fmt_p(row["p_value"]),
                "N": fmt_number(row.get("n_obs"), 0),
                "CBOs": fmt_number(row.get("n_cbo"), 0),
                "Pretrend": pretrend,
                "Leitura": evidence_label(pretrend, row.get("exploratory_only", False)),
            }
        )
    return pd.DataFrame(rows)


def build_crosswalk_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    source = sources["crosswalk"].copy()
    n_cbo = pd.to_numeric(source["n_cbo"], errors="coerce").fillna(0)
    treated = pd.to_numeric(source["strict_treated"], errors="coerce").fillna(0)
    control = pd.to_numeric(source["strict_control"], errors="coerce").fillna(0)
    excluded = (n_cbo > 0) & treated.eq(0) & control.eq(0)
    out = pd.DataFrame(
        {
            "Categoria OIT": source["gradient"],
            "CBOs": source["n_cbo"].map(lambda v: fmt_number(v, 0)),
            "Match MTE": source["matched_mte"].map(lambda v: fmt_number(v, 0)),
            "Tratamento": treated.map(lambda v: "✓" if int(v) > 0 else ""),
            "Controle": control.map(lambda v: "✓" if int(v) > 0 else ""),
            "Excluído": excluded.map(lambda v: "✓" if bool(v) else ""),
            "Média score": source["mean_score"].map(lambda v: fmt_number(v, 3)),
            "SD pooled": source["pooled_sd"].map(lambda v: fmt_number(v, 3)),
        }
    )
    return out


def _format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def build_panel_descriptive_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    panel = sources["panel"].copy()
    period_start = str(panel["periodo"].min())
    period_end = str(panel["periodo"].max())
    return pd.DataFrame(
        [
            {"Bloco": "Escopo", "Indicador": "Observações CBO-mês", "Valor": fmt_number(len(panel), 0)},
            {"Bloco": "Escopo", "Indicador": "CBOs únicos", "Valor": fmt_number(panel["cbo_4d"].nunique(), 0)},
            {"Bloco": "Escopo", "Indicador": "Meses", "Valor": fmt_number(panel["periodo"].nunique(), 0)},
            {"Bloco": "Escopo", "Indicador": "Janela", "Valor": f"{period_start} a {period_end}"},
        ]
    )


def _coverage_category(gradient: object) -> str:
    text = str(gradient or "")
    if text.startswith("Exposed: Gradient"):
        return "Exposed"
    if text == "Not Exposed":
        return "Not Exposed"
    if text == "Minimal Exposure":
        return "Minimal Exposure"
    if text == "No score":
        return "No score"
    return "Other"


def build_crosswalk_coverage_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    classification = sources["classification"].copy()
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    classification = classification.drop_duplicates(subset=["cbo_4d"]).copy()
    classification["coverage_category"] = classification["cbo_ilo_gradient"].map(_coverage_category)
    panel = sources.get("panel", pd.DataFrame(columns=["cbo_4d"])).copy()
    panel["cbo_4d"] = panel["cbo_4d"].astype(str).str.zfill(4)
    panel = panel.merge(classification[["cbo_4d", "coverage_category"]], on="cbo_4d", how="left")
    total_cbo = len(classification)
    total_obs = len(panel)
    order = ["Exposed", "Not Exposed", "Minimal Exposure", "No score"]
    rows = []
    for category in order:
        view = classification[classification["coverage_category"].eq(category)]
        obs = int(panel["coverage_category"].eq(category).sum())
        n = len(view)
        rows.append(
            {
                "Categoria": category,
                "CBOs": fmt_number(n, 0),
                "% do total": _format_percent(100 * n / total_cbo) if total_cbo else "",
                "Observações CBO-mês": fmt_number(obs, 0),
                "% das observações": _format_percent(100 * obs / total_obs) if total_obs else "",
            }
        )
    return pd.DataFrame(rows)


def build_national_main_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    pretrend_map = _pretrend_lookup(sources["main_pretrends"])
    # Prefer real-wage labels where available, but retain flows from the main model.
    rows = sources["main"].copy()
    real = sources["real_main"].copy()
    real_wages = real[real["outcome"].str.contains("salario", na=False)]
    rows = pd.concat([rows[~rows["outcome"].str.contains("salario", na=False)], real_wages], ignore_index=True)
    return _standard_rows(rows, pretrend_map)


def build_net_flow_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    pretrend_map = _pretrend_lookup(sources["net_flow_pretrends"])
    return _standard_rows(sources["net_flow"], pretrend_map)


def build_software_young_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    canaries = sources["occupation_canaries"].copy()
    demo = sources["occupation_demographic"].copy()
    selected = pd.concat([canaries, demo], ignore_index=True)
    selected = selected[
        selected["group_id"].eq("software_it_core")
        & selected["outcome"].isin(["ln_salario_real_adm", "ln_admissoes", "ln_desligamentos"])
        & selected["heterogeneity_group_id"].isin(["age_22_25", "age_26_30", "age_14_24", "age_25_34"])
    ].copy()
    selected["Painel"] = selected["panel"]
    selected["Coorte/perfil"] = selected["heterogeneity_group_label"]
    selected["Resultado"] = selected["outcome_label"]
    selected["Coeficiente"] = [estimate_with_se(r.coef, r.se, _stars(r.stars)) for r in selected.itertuples()]
    selected["Efeito aprox."] = [effect_label(r.coef, r.outcome, r.outcome_label) for r in selected.itertuples()]
    selected["p-valor"] = selected["p_value"].map(fmt_p)
    selected["Pretrend"] = selected["pretrend_status"]
    selected["Poder"] = selected["power_status"]
    selected["Leitura"] = [evidence_label(r.pretrend_status, r.exploratory_only) for r in selected.itertuples()]
    return selected[
        ["Painel", "Coorte/perfil", "Resultado", "Coeficiente", "Efeito aprox.", "p-valor", "Pretrend", "Poder", "Leitura"]
    ]


def build_occupation_summary_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    summary = sources["occupation_summary"].copy()
    summary = summary[summary["group_id"].isin(CORE_OCCUPATION_GROUPS)].copy()
    summary["Grupo"] = summary["group_label"]
    summary["Papel no texto"] = summary["recommended_location"]
    summary["Coef. salário adm."] = summary["main_real_admission_wage_coef"].map(lambda v: fmt_number(v, 4))
    summary["p-valor"] = summary["main_real_admission_wage_p"].map(fmt_p)
    summary["Pretrend salário"] = summary["main_wage_pretrend"]
    summary["Jovens Canaries"] = summary["young_canaries_signal"].map(lambda v: "sim" if bool(v) else "não")
    summary["Veredito"] = summary["verdict"]
    return summary[["Grupo", "Papel no texto", "Coef. salário adm.", "p-valor", "Pretrend salário", "Jovens Canaries", "Veredito"]]


def build_robustness_limits_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ladder = sources["control_ladder"].copy()
    wage = ladder[ladder["outcome"].eq("ln_salario_adm")].copy()
    wage["Bloco"] = "Controles"
    wage["Teste"] = wage["spec_label"]
    wage["Resultado"] = wage["outcome_label"]
    wage["Coeficiente"] = [estimate_with_se(r.coef, r.se, _stars(r.stars)) for r in wage.itertuples()]
    wage["p-valor"] = wage["p_value"].map(fmt_p)
    wage["Leitura"] = "Mostra sensibilidade a controles de composição"

    robust = sources["robustness"].copy()
    keep_specs = ["broad_control", "continuous_exposure", "placebo_2021", "main_strict_weighted"]
    robust = robust[robust["spec_id"].isin(keep_specs) & robust["outcome"].eq("ln_salario_adm")].copy()
    robust["Bloco"] = "Robustez"
    robust["Teste"] = robust["spec_label"]
    robust["Resultado"] = robust["outcome_label"]
    robust["Coeficiente"] = [estimate_with_se(r.coef, r.se, _stars(r.stars)) for r in robust.itertuples()]
    robust["p-valor"] = robust["p_value"].map(fmt_p)
    robust["Leitura"] = "Robustez relevante para interpretar limites do efeito médio"

    out = pd.concat([wage, robust], ignore_index=True)
    return out[["Bloco", "Teste", "Resultado", "Coeficiente", "p-valor", "Leitura"]]


def build_connectivity_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    pretrend = sources["connectivity_pretrends"].copy()
    pretrend_map = {str(r.outcome): str(r.status) for r in pretrend.itertuples()}
    return _standard_rows(sources["connectivity_main"], pretrend_map)


def build_top30_table(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    top = sources["top30"].copy()
    top = top[~top["source_family"].eq("manual_occupation_groups")].head(30).copy()
    top["Rank"] = top["rank"].astype(int)
    top["Fonte"] = top["source_family"]
    top["Canal"] = top["market_reconfiguration_channel"]
    top["Grupo"] = top["group_label"].fillna("")
    top["Subgrupo"] = top.get("subgroup_label", "").fillna("")
    top["Resultado"] = top["outcome_label"]
    top["Coeficiente"] = [estimate_with_se(r.coef, r.se, _stars(r.stars)) for r in top.itertuples()]
    top["p-valor"] = top["p_value"].map(fmt_p)
    top["Pretrend"] = top["pretrend_status"]
    top["Papel"] = top["placement"]
    return top[["Rank", "Fonte", "Canal", "Grupo", "Subgrupo", "Resultado", "Coeficiente", "p-valor", "Pretrend", "Papel"]]


def _copy_source_table(source_key: str):
    def builder(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
        return sources[source_key].copy()

    return builder


TABLE_BUILDERS = {
    "table_4_1_crosswalk_exposure_summary": (
        "Tabela 4.1: Classificação das CBOs segundo o índice da OIT",
        build_crosswalk_table,
        "A linha de Gradiente 4 é mantida mesmo com zero CBOs na amostra final corrigida.",
    ),
    "table_4_2a_panel_descriptive_summary": (
        "Tabela 4.2.a: Sumário descritivo do painel construído",
        build_panel_descriptive_table,
        "Painel CBO 4 dígitos por mês antes da restrição strict do modelo base.",
    ),
    "table_4_2b_ilo_cbo_classification": (
        "Tabela 4.2.b: Classificação das CBOs segundo o índice da OIT",
        build_crosswalk_table,
        "A linha de Gradiente 4 é mantida mesmo com zero CBOs na amostra final corrigida.",
    ),
    "table_4_2c_crosswalk_coverage": (
        "Tabela 4.2.c: Cobertura do crosswalk por status de exposição",
        build_crosswalk_coverage_table,
        "Exposed agrega os Gradientes 1 a 4; % do total usa o universo de CBOs classificados, enquanto % das observações usa as linhas CBO-mês do painel construído.",
    ),
    "table_5_2_net_flow_results": (
        "Tabela complementar: Saldo líquido",
        build_net_flow_table,
        "`asinh(saldo)` não é interpretado como percentual; saldo é complemento dos fluxos separados.",
    ),
    "table_5_3_1_occupation_case_exposure_summary": (
        "Tabela 5.3.1: Seleção e composição da exposição dos casos ocupacionais",
        _copy_source_table("occupation_case_exposure_summary"),
        "A seleção é semântica em CBO6; a composição OIT é atribuída posteriormente em CBO4 e ponderada pelas admissões pré-tratamento.",
    ),
    "table_5_5_robustness_and_limits": (
        "Tabela 5.7.1: Robustez e limites",
        build_robustness_limits_table,
        "Seleciona apenas checks úteis para a escrita, evitando ruído de especificações redundantes.",
    ),
    "table_a_1_connectivity_extension": (
        "Tabela A.1: Extensão de conectividade municipal",
        build_connectivity_table,
        "Conectividade é evidência espacial sugestiva; pretrends DDD falham nos outcomes principais.",
    ),
    "table_a_2_top_30_results": (
        "Tabela A.2: Top 30 achados para triagem da escrita",
        build_top30_table,
        "Inventário de triagem após excluir os quatro grupos ocupacionais manuais descontinuados do pacote principal.",
    ),
    "table_b_1_occupation_case_age_terminal_matrix": (
        "Tabela B.1: Matriz terminal por caso ocupacional e idade",
        _copy_source_table("occupation_case_age_terminal"),
        "Variação média de janeiro a junho de 2025 em relação a outubro de 2022; resultados descritivos.",
    ),
    "table_b_2_occupation_case_preperiod_diagnostics": (
        "Tabela B.2: Diagnósticos descritivos do período anterior",
        _copy_source_table("occupation_case_preperiod"),
        "Inclinações e coeficientes de variação não são testes causais de tendências paralelas.",
    ),
    "table_b_3_occupation_case_sensitivity_matrix": (
        "Tabela B.3: Sensibilidades dos casos ocupacionais",
        _copy_source_table("occupation_case_sensitivity"),
        "Inclui composição alternativa, normalização alternativa, comparação com o mesmo mês de 2022 e estimadores salariais.",
    ),
    "table_b_4_occupation_case_demographic_terminal_matrix": (
        "Tabela B.4: Matriz demográfica dos casos ocupacionais",
        _copy_source_table("occupation_case_demographic"),
        "Comparações descritivas por sexo, raça/cor e escolaridade; células sem suporte permanecem identificadas.",
    ),
    "table_b_5_legacy_manual_group_diagnostics": (
        "Tabela B.5: Diagnósticos legados dos grupos ocupacionais manuais",
        build_occupation_summary_table,
        "Material legado mantido para auditoria; não integra os resultados principais da Seção 5.3.",
    ),
}


def build_all_tables(sources: dict[str, pd.DataFrame], output_dir: Path = TABLE_DIR) -> dict[str, pd.DataFrame]:
    generated = write_section5_2_tables(sources, output_dir)
    for stem, (title, builder, note) in TABLE_BUILDERS.items():
        table = builder(sources)
        generated[stem] = table
        write_table_pair(
            output_dir / f"{stem}.csv",
            output_dir / f"{stem}.md",
            title,
            table,
            list(table.columns),
            note=note,
        )
    return generated
