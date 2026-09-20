"""Write Section 4 result evaluation reports."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from section4_results_evaluation.config import JUDGE_POOL_N, MINIMUM_TAG_COUNTS


def fmt_number(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    if isinstance(value, float):
        return f"{value:.{digits}f}".replace(".", ",")
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sem linhas disponíveis._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df[columns].iterrows():
        values = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def recommended_sentence(row: pd.Series) -> str:
    effect = fmt_number(row.get("effect_percent"), 2)
    coef = fmt_number(row.get("coef"), 4)
    p = fmt_number(row.get("p_value"), 3)
    stars = row.get("stars") if pd.notna(row.get("stars")) else ""
    context = row.get("group_label") or row.get("spec_id")
    subgroup = row.get("subgroup_label")
    outcome = row.get("outcome_label")
    pretrend = row.get("pretrend_status")
    tier = row.get("causal_tier")
    if subgroup:
        context = f"{context} / {subgroup}"
    if tier == "causal_headline":
        if pd.isna(row.get("effect_percent")):
            return (
                f"Em {context}, o resultado para {outcome} é {coef}{stars} (p={p}), "
                f"com pretrend {pretrend}."
            )
        return (
            f"Em {context}, o resultado para {outcome} é {coef}{stars} (p={p}), "
            f"equivalente a {effect}% em termos aproximados, com pretrend {pretrend}."
        )
    if "pretrend_limit" in str(tier):
        if pd.isna(row.get("effect_percent")):
            return (
                f"Em {context}, há sinal para {outcome} ({coef}{stars}, p={p}), "
                f"mas a falha de pretrend exige interpretação como evidência sugestiva, não causal forte."
            )
        return (
            f"Em {context}, há sinal para {outcome} ({coef}{stars}, p={p}, efeito aproximado de {effect}%), "
            f"mas a falha de pretrend exige interpretação como evidência sugestiva, não causal forte."
        )
    if tier == "null_context":
        return (
            f"Em {context}, não há evidência estatística clara para {outcome} "
            f"({coef}{stars}, p={p}), o que ajuda a delimitar a narrativa de reconfiguração."
        )
    if tier == "exploratory":
        return (
            f"Em {context}, o resultado para {outcome} ({coef}{stars}, p={p}) deve ficar em apêndice, "
            "pois o grupo é exploratório ou sem suporte integral do crosswalk oficial."
        )
    if tier == "suggestive_no_pretrend_test":
        if pd.isna(row.get("effect_percent")):
            return (
                f"Em {context}, o resultado para {outcome} é {coef}{stars} (p={p}), "
                "mas deve ser tratado como sugestivo porque não há pretrend formal nesse bloco."
            )
        return (
            f"Em {context}, o resultado para {outcome} é {coef}{stars} (p={p}), "
            f"equivalente a {effect}% em termos aproximados, mas deve ser tratado como sugestivo porque não há pretrend formal nesse bloco."
        )
    if pd.isna(row.get("effect_percent")):
        return f"Em {context}, o resultado para {outcome} é {coef}{stars} (p={p})."
    return (
        f"Em {context}, o resultado para {outcome} é {coef}{stars} (p={p}), "
        f"com efeito aproximado de {effect}%."
    )


def interpretation(row: pd.Series) -> str:
    channel = row.get("market_reconfiguration_channel")
    direction = "queda" if row.get("coef", 0) < 0 else "aumento"
    if channel == "admission_flow":
        return f"evidência de {direction} relativa nos fluxos de admissão"
    if channel == "separation_flow":
        return f"evidência de {direction} relativa nos fluxos de desligamento"
    if channel == "net_flow":
        return f"evidência de {direction} no saldo líquido de vínculos formais"
    if channel == "entry_wage":
        return f"evidência de {direction} no salário real de entrada"
    if channel == "exit_wage":
        return f"evidência de {direction} no salário de desligamento"
    if channel == "composition_or_heterogeneity":
        return "evidência de reconfiguração concentrada em perfis específicos"
    if channel == "spatial_connectivity":
        return "evidência de que conectividade municipal altera a intensidade do choque"
    if channel == "occupational_mechanism":
        return "evidência de mecanismo ocupacional associado a grupos expostos"
    return "evidência complementar para a hipótese de reconfiguração"


def risk_note(row: pd.Series) -> str:
    flags = str(row.get("flags", ""))
    if "exploratory" in flags:
        return "Não usar como resultado principal; manter em apêndice/exploração."
    if "pretrend_fail" in flags:
        return "Pretrend falha; interpretar como sugestivo ou limitação causal."
    if "legacy_or_benchmark" in flags:
        return "Resultado legado/benchmark; não substituir o pacote final."
    if row.get("causal_tier") == "suggestive_no_pretrend_test":
        return "Sem pretrend formal no bloco; útil para narrativa, mas não como causalidade forte."
    if "not_statistically_significant" in flags:
        return "Resultado nulo ou impreciso; útil para delimitar onde a hipótese não aparece."
    return "Risco interpretativo baixo dentro das limitações do desenho."


def add_judge_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["mention"] = "yes"
    out["market_reconfiguration_interpretation"] = [interpretation(row) for _, row in out.iterrows()]
    out["risk_note"] = [risk_note(row) for _, row in out.iterrows()]
    out["recommended_sentence_pt"] = [recommended_sentence(row) for _, row in out.iterrows()]
    return out


def write_llm_prompt(path: Path) -> None:
    prompt = """# LLM-as-judge prompt for Section 4 result evaluation

You are reviewing candidate empirical results for a Brazilian master's dissertation.
The hypothesis is broad: generative AI may reconfigure the formal labor market through admissions, separations, wages, composition, spatial connectivity, and occupational mechanisms.

For each candidate, decide whether it should be mentioned, where it belongs, how it supports or limits the market-reconfiguration narrative, and what risk note must accompany it.

Hard gates:
- Never classify a result with failed pretrend as strong causal evidence.
- Never place an exploratory-only result in the main text.
- Do not let salary-admission results crowd out admissions, separations, and other wage outcomes.
- Prefer final/current packages over legacy packages when they measure the same concept.
"""
    path.write_text(prompt, encoding="utf-8")


def write_judge_decisions(path: Path, candidates: pd.DataFrame) -> None:
    pool = add_judge_fields(
        candidates.sort_values(["deterministic_score", "p_value"], ascending=[False, True], na_position="last").head(JUDGE_POOL_N)
    )
    payload = {
        "judge_mode": "codex_rule_based_judge_with_saved_prompt",
        "note": "Decisions are reproducible rule-based codifications of the Codex judge criteria; the saved prompt can be reused for manual LLM review.",
        "n_candidates_reviewed": int(len(pool)),
        "decisions": pool[
            [
                "result_id",
                "mention",
                "placement",
                "market_reconfiguration_interpretation",
                "risk_note",
                "recommended_sentence_pt",
            ]
        ].to_dict(orient="records"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_top_results(path: Path, top: pd.DataFrame) -> None:
    view = top.copy()
    view["EfeitoPercentual"] = view["effect_percent"].map(lambda v: fmt_number(v, 2))
    view["Coef"] = view["coef"].map(lambda v: fmt_number(v, 4))
    view["p"] = view["p_value"].map(lambda v: fmt_number(v, 3))
    view["Score"] = view["deterministic_score"].map(lambda v: fmt_number(v, 1))
    view["Frase"] = view["recommended_sentence_pt"]
    columns = [
        "rank",
        "placement",
        "market_reconfiguration_channel",
        "group_label",
        "subgroup_label",
        "outcome_label",
        "Coef",
        "EfeitoPercentual",
        "p",
        "stars",
        "pretrend_status",
        "causal_tier",
        "Score",
        "Frase",
    ]
    text = "# Top 30 resultados para mencionar\n\n" + markdown_table(view, columns) + "\n"
    path.write_text(text, encoding="utf-8")


def write_dissertation_report(path: Path, top: pd.DataFrame) -> None:
    sections = [
        "# Top 30 Achados Para A Dissertação",
        "## Leitura geral",
        (
            "A hipótese orientadora é ampla: a IA generativa pode estar associada a uma reconfiguração do mercado formal, "
            "visível em admissões, desligamentos, salários, composição dos trabalhadores, conectividade municipal e mecanismos ocupacionais."
        ),
    ]
    order = [
        ("Achados centrais do modelo nacional", ["final_model"]),
        ("Mudanças em admissões e demissões", ["admission_flow", "separation_flow"]),
        ("Fluxo líquido", ["net_flow"]),
        ("Mudanças salariais", ["entry_wage", "exit_wage"]),
        ("Heterogeneidade jovem e perfis demográficos", ["composition_or_heterogeneity"]),
        ("Conectividade", ["spatial_connectivity"]),
        ("Núcleo de Software e TI e grupos ocupacionais", ["occupational_mechanism"]),
        ("Robustez, resultados nulos e limitações", ["limitation_or_suggestive", "null_result"]),
    ]
    for title, tags in order:
        if title == "Achados centrais do modelo nacional":
            subset = top[top["source_family"].eq("final_model")]
        elif title == "Robustez, resultados nulos e limitações":
            subset = top[top["narrative_role"].isin(tags)]
        else:
            mask = top["channel_tags"].fillna("").apply(lambda value: any(tag in value for tag in tags))
            subset = top[mask]
        if subset.empty:
            continue
        sections.append(f"## {title}")
        for row in subset.sort_values("rank").itertuples(index=False):
            sections.append(f"{int(row.rank)}. {row.recommended_sentence_pt}")
    path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def write_audit(path: Path, universe: pd.DataFrame, scores: pd.DataFrame, top: pd.DataFrame) -> None:
    counts = top["channel_tags"].fillna("")
    rows = []
    for tag, minimum in MINIMUM_TAG_COUNTS.items():
        if tag == "wage_any":
            count = int(counts.str.contains("entry_wage|exit_wage|wage_any", regex=True).sum())
        else:
            count = int(counts.str.contains(tag, regex=False).sum())
        rows.append({"Canal": tag, "Minimo": minimum, "Selecionado": count, "Status": "ok" if count >= minimum else "insuficiente"})
    diversity = pd.DataFrame(rows)
    sections = [
        "# Auditoria Da Avaliação Dos Resultados",
        "## Universo",
        f"- Candidatos ingeridos: {len(universe)}",
        f"- Candidatos pontuados: {len(scores)}",
        f"- Resultados selecionados: {len(top)}",
        "## Diversidade mínima",
        markdown_table(diversity, ["Canal", "Minimo", "Selecionado", "Status"]),
        "## Blindspot",
        "- Vice 1: há vários coeficientes fortes com pretrend falha; eles foram preservados, mas rebaixados para evidência sugestiva/limitação.",
        "- Vice 2: resultados nulos do modelo nacional foram mantidos para evitar narrativa baseada apenas em subgrupos significativos.",
        "- Virtue 1: a heterogeneidade jovem e os mecanismos ocupacionais são mais informativos do que o efeito médio isolado.",
        "- Virtue 2: conectividade e ocupações ajudam a contar uma história de reconfiguração, não apenas de salário de admissão.",
        "## Hard gates",
        "- Resultados exploratórios não podem entrar no texto principal.",
        "- Pretrend fail não pode ser causal headline.",
        "- Todo resultado selecionado deve ter canal, fonte, coeficiente, p-valor e frase sugerida.",
    ]
    path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
