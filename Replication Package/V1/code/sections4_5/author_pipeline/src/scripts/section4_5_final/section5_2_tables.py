"""National and sociodemographic heterogeneity tables for Section 5.2."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .formatting import fmt_number, fmt_p, markdown_table


OUTCOME_ORDER = ["ln_admissoes", "ln_desligamentos", "ln_salario_real_adm"]
OUTCOME_LABELS = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Desligamentos (log)",
    "ln_salario_real_adm": "Salário real de admissão (log)",
    "asinh_saldo": "Saldo líquido (asinh)",
    "saldo_per_pre_adm": "Saldo líquido / admissões pré",
    "saldo_flow_rate": "Saldo líquido / fluxo total",
}
PRIMARY_OUTCOME_ORDER = [*OUTCOME_ORDER, "asinh_saldo"]
BALANCE_ROBUSTNESS_OUTCOME_ORDER = ["saldo_per_pre_adm", "saldo_flow_rate"]
SECTION5_2_OUTCOME_ORDER = [*PRIMARY_OUTCOME_ORDER, *BALANCE_ROBUSTNESS_OUTCOME_ORDER]

HETEROGENEITY_SPECS = {
    "sex": {
        "stem": "table_5_2_2_heterogeneity_sex",
        "title": "Tabela 5.2.2: Heterogeneidade por sexo",
        "dimension": "sex",
        "source": "general",
        "groups": [("men", "Homens"), ("women", "Mulheres")],
    },
    "income": {
        "stem": "table_5_2_3_heterogeneity_income",
        "title": "Tabela 5.2.3: Heterogeneidade por renda pré-tratamento",
        "dimension": "income",
        "source": "general",
        "dimension_note": "As faixas usam a mediana salarial pré-tratamento da CBO, expressa em salários mínimos; não representam a renda individual corrente.",
        "groups": [
            ("low_income", "Até 2 salários mínimos"),
            ("middle_income", "Mais de 2 até 5 salários mínimos"),
            ("high_income", "Mais de 5 salários mínimos"),
        ],
    },
    "age_canaries": {
        "stem": "table_5_2_4_heterogeneity_age_canaries",
        "title": "Tabela 5.2.4: Heterogeneidade por idade — coortes Canaries",
        "dimension": "canaries_age",
        "source": "canaries_age",
        "groups": [
            ("age_22_25", "22–25"),
            ("age_26_30", "26–30"),
            ("age_31_34", "31–34"),
            ("age_35_40", "35–40"),
            ("age_41_49", "41–49"),
            ("age_50_plus", "50+"),
        ],
    },
    "race_color": {
        "stem": "table_5_2_5_heterogeneity_race_color",
        "title": "Tabela 5.2.5: Heterogeneidade por raça/cor",
        "dimension": "race_color",
        "source": "general",
        "groups": [
            ("race_white", "Branca"),
            ("race_black", "Preta"),
            ("race_pardo", "Parda"),
            ("race_yellow", "Amarela"),
            ("race_indigenous", "Indígena"),
            ("race_unknown", "Não informada/identificada"),
        ],
    },
    "education": {
        "stem": "table_5_2_6_heterogeneity_education",
        "title": "Tabela 5.2.6: Heterogeneidade por escolaridade",
        "dimension": "education",
        "source": "general",
        "groups": [
            ("fundamental_or_less", "Fundamental ou menos"),
            ("high_school", "Médio"),
            ("higher_education", "Superior"),
        ],
    },
}

SECTION5_2_ADDITIONAL_SPECS = {
    "income_pnad": {
        "stem": "table_5_2_3_b",
        "title": "Tabela 5.2.3.b: Heterogeneidade por renda pré-tratamento — faixas PNAD/IBGE",
        "dimension": "income_pnad",
        "source": "general",
        "allow_non_estimable": True,
        "dimension_note": (
            "As faixas reproduzem os cortes da PNAD, mas continuam usando a mediana salarial "
            "pré-tratamento da CBO, expressa em salários mínimos do respectivo ano; não representam "
            "a renda individual corrente."
        ),
        "groups": [
            ("income_up_to_1sm", "Até 1 salário mínimo"),
            ("income_1_2sm", "Mais de 1 até 2 salários mínimos"),
            ("income_2_3sm", "Mais de 2 até 3 salários mínimos"),
            ("income_3_5sm", "Mais de 3 até 5 salários mínimos"),
            ("income_5_plus_sm", "Mais de 5 salários mínimos"),
        ],
    },
    "age_pnad": {
        "stem": "table_5_2_4_b",
        "title": "Tabela 5.2.4.b: Heterogeneidade por idade — faixas PNAD/IBGE",
        "dimension": "age_pnad",
        "source": "general",
        "allow_non_estimable": True,
        "dimension_note": (
            "A amostra desta alternativa é restrita a trabalhadores de 18 a 65 anos; portanto, "
            "a faixa exibida como 55+ corresponde a 55–65 anos."
        ),
        "groups": [
            ("age_18_24", "18–24"),
            ("age_25_34", "25–34"),
            ("age_35_44", "35–44"),
            ("age_45_54", "45–54"),
            ("age_55_plus", "55+"),
        ],
    },
    "race_color_b": {
        "stem": "table_5_2_5_b",
        "title": "Tabela 5.2.5.b: Heterogeneidade por raça/cor — Branca e Negra",
        "dimension": "race_color_b",
        "source": "general",
        "dimension_note": (
            "A amostra desta alternativa inclui apenas trabalhadores classificados como brancos, "
            "pretos ou pardos; a categoria Negra agrega pretos e pardos. Amarela, Indígena e "
            "registros sem raça/cor identificada são excluídos. Assim, o DDD é um contraste direto "
            "entre Branca e Negra."
        ),
        "groups": [
            ("race_white", "Branca"),
            ("race_black_combined", "Negra (preta e parda)"),
        ],
    },
}

SECTION5_2_TABLE_SPECS = {
    "sex": HETEROGENEITY_SPECS["sex"],
    "income": HETEROGENEITY_SPECS["income"],
    "income_pnad": SECTION5_2_ADDITIONAL_SPECS["income_pnad"],
    "age_canaries": HETEROGENEITY_SPECS["age_canaries"],
    "age_pnad": SECTION5_2_ADDITIONAL_SPECS["age_pnad"],
    "race_color": HETEROGENEITY_SPECS["race_color"],
    "race_color_b": SECTION5_2_ADDITIONAL_SPECS["race_color_b"],
    "education": HETEROGENEITY_SPECS["education"],
}

SECTION5_2_EXPECTED_ROWS = {
    "table_5_2_1_national_main_results": len(SECTION5_2_OUTCOME_ORDER),
    **{
        spec["stem"]: len(spec["groups"]) * len(SECTION5_2_OUTCOME_ORDER)
        for spec in SECTION5_2_TABLE_SPECS.values()
    },
}

DEPRECATED_SECTION5_2_STEMS = ["table_5_1_national_main_results"]

NUMERIC_COLUMNS = [
    "group_coef",
    "group_se",
    "group_p_value",
    "group_n_obs",
    "group_n_cbo",
    "group_pretrend_p_value",
    "group_treated_cbo",
    "group_control_cbo",
    "ddd_coef",
    "ddd_se",
    "ddd_p_value",
    "ddd_n_obs",
    "ddd_n_cbo",
    "ddd_pretrend_p_value",
    "ddd_wald_statistic",
    "target_cbo_with_flows",
]


def significance_stars(p_value: object) -> str:
    if p_value is None or pd.isna(p_value):
        return ""
    value = float(p_value)
    if value < 0.01:
        return "***"
    if value < 0.05:
        return "**"
    if value < 0.10:
        return "*"
    return ""


def _single_row(data: pd.DataFrame, outcome: str, context: str) -> pd.Series:
    selected = data[data["outcome"].eq(outcome)]
    if len(selected) != 1:
        raise ValueError(f"Expected exactly one row for {context} / {outcome}; found {len(selected)}.")
    return selected.iloc[0]


def _pretrend_row(pretrends: pd.DataFrame, outcome: str) -> pd.Series | None:
    candidates = [outcome]
    if outcome == "ln_salario_real_adm":
        candidates.append("ln_salario_adm")
    for candidate in candidates:
        selected = pretrends[pretrends["outcome"].eq(candidate)]
        if len(selected) == 1:
            return selected.iloc[0]
    return None


def _outcome_role(outcome: str) -> str:
    return "primary" if outcome in PRIMARY_OUTCOME_ORDER else "balance_robustness"


def _national_source(sources: dict[str, pd.DataFrame], outcome: str) -> pd.DataFrame:
    if outcome in ["asinh_saldo", *BALANCE_ROBUSTNESS_OUTCOME_ORDER]:
        return sources["net_flow"]
    if outcome == "ln_salario_real_adm":
        return sources["real_main"]
    return sources["main"]


def _national_pretrend_source(sources: dict[str, pd.DataFrame], outcome: str) -> pd.DataFrame:
    if outcome in ["asinh_saldo", *BALANCE_ROBUSTNESS_OUTCOME_ORDER]:
        return sources["net_flow_pretrends"]
    return sources["main_pretrends"]


def build_national_long(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for outcome in SECTION5_2_OUTCOME_ORDER:
        source = _national_source(sources, outcome)
        row = _single_row(source, outcome, "national")
        pretrend = _pretrend_row(_national_pretrend_source(sources, outcome), outcome)
        rows.append(
            {
                "dimension": "national",
                "group_id": "national",
                "group_label": "Nacional",
                "outcome": outcome,
                "outcome_label": OUTCOME_LABELS[outcome],
                "outcome_role": _outcome_role(outcome),
                "result_status": row.get("result_status", ""),
                "coef": pd.to_numeric(row.get("coef"), errors="coerce"),
                "se": pd.to_numeric(row.get("se"), errors="coerce"),
                "p_value": pd.to_numeric(row.get("p_value"), errors="coerce"),
                "stars": significance_stars(row.get("p_value")),
                "n_obs": pd.to_numeric(row.get("n_obs"), errors="coerce"),
                "n_cbo": pd.to_numeric(row.get("n_cbo"), errors="coerce"),
                "pretrend_status": "not_available" if pretrend is None else pretrend.get("pretrend_status", "not_available"),
                "pretrend_p_value": pd.NA if pretrend is None else pd.to_numeric(pretrend.get("joint_p_value"), errors="coerce"),
            }
        )
    return pd.DataFrame(rows)


def _heterogeneity_source(sources: dict[str, pd.DataFrame], spec: dict[str, object], outcome: str) -> pd.DataFrame:
    if outcome in ["asinh_saldo", *BALANCE_ROBUSTNESS_OUTCOME_ORDER]:
        return sources["net_flow_heterogeneity"]
    if spec["source"] == "canaries_age":
        return sources["canaries_age"]
    if outcome == "ln_salario_real_adm":
        return sources["heterogeneity_real_wage"]
    return sources["heterogeneity"]


def build_heterogeneity_long(sources: dict[str, pd.DataFrame], table_id: str) -> pd.DataFrame:
    if table_id not in SECTION5_2_TABLE_SPECS:
        raise KeyError(f"Unknown Section 5.2 heterogeneity table: {table_id}")
    spec = SECTION5_2_TABLE_SPECS[table_id]
    rows = []
    for group_id, group_label in spec["groups"]:
        for outcome in SECTION5_2_OUTCOME_ORDER:
            source = _heterogeneity_source(sources, spec, outcome)
            selected = source[
                source["dimension"].eq(spec["dimension"])
                & source["group_id"].eq(group_id)
                & source["outcome"].eq(outcome)
            ]
            if len(selected) != 1:
                raise ValueError(
                    f"Expected exactly one row for {table_id} / {group_id} / {outcome}; found {len(selected)}."
                )
            raw = selected.iloc[0]
            rows.append(
                {
                    "dimension": spec["dimension"],
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "outcome_role": _outcome_role(outcome),
                    "comparison": raw.get("comparison", "target_vs_complement"),
                    "group_result_status": raw.get("group_result_status", ""),
                    "group_coef": raw.get("group_coef"),
                    "group_se": raw.get("group_se"),
                    "group_p_value": raw.get("group_p_value"),
                    "group_stars": significance_stars(raw.get("group_p_value")),
                    "group_n_obs": raw.get("group_n_obs"),
                    "group_n_cbo": raw.get("group_n_cbo"),
                    "group_error": raw.get("group_error", ""),
                    "group_model": raw.get("group_model", ""),
                    "group_pretrend_status": raw.get("group_pretrend_status", "not_available"),
                    "group_pretrend_p_value": raw.get("group_pretrend_p_value"),
                    "group_pretrend_error": raw.get("group_pretrend_error", ""),
                    "group_power_status": raw.get("group_power_status", "not_available"),
                    "group_treated_cbo": raw.get("group_treated_cbo"),
                    "group_control_cbo": raw.get("group_control_cbo"),
                    "ddd_result_status": raw.get("result_status", ""),
                    "ddd_coef": raw.get("coef"),
                    "ddd_se": raw.get("se"),
                    "ddd_p_value": raw.get("p_value"),
                    "ddd_stars": significance_stars(raw.get("p_value")),
                    "ddd_n_obs": raw.get("n_obs"),
                    "ddd_n_cbo": raw.get("n_cbo"),
                    "ddd_error": raw.get("error", ""),
                    "ddd_model": raw.get("model", ""),
                    "ddd_pretrend_status": raw.get("pretrend_status", "not_available"),
                    "ddd_pretrend_p_value": raw.get("pretrend_p_value"),
                    "ddd_pretrend_error": raw.get("pretrend_error", ""),
                    "ddd_power_status": raw.get("power_status", "not_available"),
                    "ddd_wald_statistic": raw.get("wald_statistic"),
                    "ddd_wald_test_method": raw.get("wald_test_method", ""),
                    "target_cbo_with_flows": raw.get("target_cbo_with_flows"),
                }
            )
    out = pd.DataFrame(rows)
    for column in NUMERIC_COLUMNS:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if out.duplicated(["group_id", "outcome"]).any():
        raise ValueError(f"Duplicate group-outcome rows in {table_id}.")
    return out


def _estimate_cell(coef: object, se: object, stars: object) -> str:
    if coef is None or se is None or pd.isna(coef) or pd.isna(se):
        return "não estimável"
    return f"{fmt_number(coef, 4)}{stars or ''}<br>({fmt_number(se, 4)})"


def _status_with_p(status: object, p_value: object) -> str:
    status_text = str(status or "not_available")
    if p_value is None or pd.isna(p_value):
        return status_text
    return f"{status_text} (p={fmt_p(p_value)})"


def _national_diagnostic_panel(data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Resultado": data["outcome_label"],
            "DiD nacional": [
                _estimate_cell(row.coef, row.se, row.stars)
                for row in data.itertuples(index=False)
            ],
            "p DiD": data["p_value"].map(fmt_p),
            "Pretrend": [
                _status_with_p(row.pretrend_status, row.pretrend_p_value)
                for row in data.itertuples(index=False)
            ],
            "N": data["n_obs"].map(lambda value: fmt_number(value, 0)),
            "CBOs": data["n_cbo"].map(lambda value: fmt_number(value, 0)),
        }
    )


def _national_markdown(data: pd.DataFrame) -> str:
    primary = data[data["outcome_role"].eq("primary")].copy()
    robustness = data[data["outcome_role"].eq("balance_robustness")].copy()
    panel_a_row = {"Amostra": "Nacional"}
    panel_a_row.update(
        {
            row.outcome_label: _estimate_cell(row.coef, row.se, row.stars)
            for row in primary.itertuples(index=False)
        }
    )
    panel_a = pd.DataFrame([panel_a_row])
    panel_b_primary = _national_diagnostic_panel(primary)
    panel_b_robustness = _national_diagnostic_panel(robustness)
    return f"""# Tabela 5.2.1: Resultados médios nacionais

## Painel A: Efeitos DiD nacionais

{markdown_table(panel_a, list(panel_a.columns))}

## Painel B.1: Estimativas DiD e diagnósticos dos outcomes principais

{markdown_table(panel_b_primary, list(panel_b_primary.columns))}

## Painel B.2: Robustez da construção do saldo

{markdown_table(panel_b_robustness, list(panel_b_robustness.columns))}

Notas: as células do Painel A apresentam o coeficiente DiD nacional e, entre parênteses, o erro-padrão. O Painel B.1 repete essas estimativas para reunir p-valores, pretrends e suporte da amostra; não se trata de um contraste DDD, pois não há divisão por subgrupo. Os erros-padrão são clusterizados por CBO de quatro dígitos. * p<0,10; ** p<0,05; *** p<0,01. O tratamento compara CBOs expostas nos gradientes da OIT a CBOs `Not Exposed`; `Minimal Exposure` não integra o controle principal. O pretrend do Painel B é o teste conjunto dos coeficientes mensais anteriores ao tratamento; `not_available` indica que o teste conjunto não foi estimado para aquela construção. `asinh(saldo)` aceita valores negativos e zero e não deve ser interpretado como percentual. `Saldo/admissões pré` normaliza pelo porte pré-tratamento da CBO; `saldo/fluxo total` divide o saldo por admissões mais desligamentos no mês. As duas medidas do Painel B.2 são checagens de robustez, não outcomes principais. Os p-valores são convencionais e não recebem correção por testes múltiplos. N denota observações CBO-mês, não trabalhadores.
"""


def _heterogeneity_diagnostic_panel(data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Grupo": row.group_label,
                "Resultado": row.outcome_label,
                "DDD grupo–complemento": _estimate_cell(row.ddd_coef, row.ddd_se, row.ddd_stars),
                "p DDD": fmt_p(row.ddd_p_value),
                "Pretrend grupo": _status_with_p(row.group_pretrend_status, row.group_pretrend_p_value),
                "Pretrend DDD": _status_with_p(row.ddd_pretrend_status, row.ddd_pretrend_p_value),
                "Poder grupo": row.group_power_status,
                "N grupo": fmt_number(row.group_n_obs, 0),
                "CBOs trat./controle": f"{fmt_number(row.group_treated_cbo, 0)}/{fmt_number(row.group_control_cbo, 0)}",
            }
            for row in data.itertuples(index=False)
        ]
    )


def _heterogeneity_markdown(data: pd.DataFrame, spec: dict[str, object]) -> str:
    panel_a_rows = []
    for _group_id, group_label in spec["groups"]:
        group = data[data["group_label"].eq(group_label)]
        row = {"Grupo": group_label}
        for outcome in PRIMARY_OUTCOME_ORDER:
            estimate = _single_row(group, outcome, str(group_label))
            row[OUTCOME_LABELS[outcome]] = _estimate_cell(
                estimate["group_coef"], estimate["group_se"], estimate["group_stars"]
            )
        panel_a_rows.append(row)
    panel_a = pd.DataFrame(panel_a_rows)

    panel_b_primary = _heterogeneity_diagnostic_panel(
        data[data["outcome_role"].eq("primary")]
    )
    panel_b_robustness = _heterogeneity_diagnostic_panel(
        data[data["outcome_role"].eq("balance_robustness")]
    )
    binary_note = " Em dimensões binárias, os DDDs dos dois grupos são espelhados por construção e não constituem testes independentes." if len(spec["groups"]) == 2 else ""
    dimension_note = f" {spec['dimension_note']}" if spec.get("dimension_note") else ""
    return f"""# {spec['title']}

## Painel A: Efeitos DiD dentro de cada grupo

{markdown_table(panel_a, list(panel_a.columns))}

## Painel B.1: Contrastes DDD e diagnósticos dos outcomes principais

{markdown_table(panel_b_primary, list(panel_b_primary.columns))}

## Painel B.2: Robustez da construção do saldo

{markdown_table(panel_b_robustness, list(panel_b_robustness.columns))}

Notas: as células apresentam o coeficiente e, entre parênteses, o erro-padrão. Os erros-padrão são clusterizados por CBO de quatro dígitos. * p<0,10; ** p<0,05; *** p<0,01. O Painel A estima o DiD na amostra do próprio grupo. O Painel B usa o DDD `pós × tratamento × grupo` e um teste de Wald qui-quadrado para verificar formalmente se esse efeito difere do complemento. Os diagnósticos de pretrend das heterogeneidades testam uma tendência linear no período pré-tratamento; não são o teste conjunto do event study nacional. `asinh(saldo)` aceita valores negativos e zero e não deve ser interpretado como percentual. `Saldo/admissões pré` e `saldo/fluxo total` aparecem no Painel B.2 apenas como checagens de robustez. `N grupo` denota observações CBO-mês, não trabalhadores. O poder é um diagnóstico de suporte por CBOs tratadas/controle: `adequate` requer pelo menos 20/50, `limited` requer 10/25 e `thin` indica suporte inferior. Os p-valores são convencionais, sem correção por testes múltiplos; por isso, as heterogeneidades são exploratórias. Resultados com pretrend falho ou poder `thin` exigem cautela.{dimension_note}{binary_note}
"""


def write_section5_2_tables(
    sources: dict[str, pd.DataFrame], output_dir: Path
) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for stem in DEPRECATED_SECTION5_2_STEMS:
        for suffix in [".csv", ".md"]:
            (output_dir / f"{stem}{suffix}").unlink(missing_ok=True)
    generated: dict[str, pd.DataFrame] = {}

    national_stem = "table_5_2_1_national_main_results"
    national = build_national_long(sources)
    national.to_csv(output_dir / f"{national_stem}.csv", index=False)
    (output_dir / f"{national_stem}.md").write_text(_national_markdown(national), encoding="utf-8")
    generated[national_stem] = national

    for table_id, spec in SECTION5_2_TABLE_SPECS.items():
        table = write_heterogeneity_table(sources, table_id, output_dir)
        stem = str(spec["stem"])
        generated[stem] = table
    return generated


def write_heterogeneity_table(
    sources: dict[str, pd.DataFrame],
    table_id: str,
    output_dir: Path,
) -> pd.DataFrame:
    """Write one Section 5.2 heterogeneity table without rebuilding its peers."""
    if table_id not in SECTION5_2_TABLE_SPECS:
        raise KeyError(f"Unknown Section 5.2 heterogeneity table: {table_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    spec = SECTION5_2_TABLE_SPECS[table_id]
    table = build_heterogeneity_long(sources, table_id)
    stem = str(spec["stem"])
    table.to_csv(output_dir / f"{stem}.csv", index=False)
    (output_dir / f"{stem}.md").write_text(
        _heterogeneity_markdown(table, spec),
        encoding="utf-8",
    )
    return table


def validate_section5_2_outputs(output_dir: Path) -> pd.DataFrame:
    required_heterogeneity_columns = {
        "dimension",
        "group_id",
        "group_label",
        "outcome",
        "outcome_role",
        "group_result_status",
        "group_error",
        "group_coef",
        "group_se",
        "group_p_value",
        "group_pretrend_status",
        "group_pretrend_p_value",
        "group_power_status",
        "group_n_obs",
        "group_n_cbo",
        "group_treated_cbo",
        "group_control_cbo",
        "ddd_coef",
        "ddd_se",
        "ddd_p_value",
        "ddd_result_status",
        "ddd_error",
        "ddd_pretrend_status",
        "ddd_pretrend_p_value",
        "ddd_power_status",
        "ddd_wald_statistic",
        "ddd_wald_test_method",
    }
    checks = []
    for stem, expected_rows in SECTION5_2_EXPECTED_ROWS.items():
        csv_path = output_dir / f"{stem}.csv"
        md_path = output_dir / f"{stem}.md"
        if not csv_path.exists() or not md_path.exists():
            raise RuntimeError(f"Missing Section 5.2 table pair for {stem}.")
        data = pd.read_csv(csv_path)
        if len(data) != expected_rows:
            raise RuntimeError(f"Unexpected row count for {stem}: expected {expected_rows}, found {len(data)}.")
        artifact_text = csv_path.read_text(encoding="utf-8") + "\n" + md_path.read_text(encoding="utf-8")
        lowered = artifact_text.lower()
        if "ln_salario_real_desl" in lowered or "salário real de desligamento" in lowered:
            raise RuntimeError(f"Forbidden dismissal-wage outcome found in {stem}.")
        if data["outcome"].tolist() != SECTION5_2_OUTCOME_ORDER * (
            expected_rows // len(SECTION5_2_OUTCOME_ORDER)
        ):
            raise RuntimeError(f"Unexpected outcome order for {stem}.")
        expected_roles = [_outcome_role(outcome) for outcome in SECTION5_2_OUTCOME_ORDER] * (
            expected_rows // len(SECTION5_2_OUTCOME_ORDER)
        )
        if data["outcome_role"].tolist() != expected_roles:
            raise RuntimeError(f"Unexpected outcome roles for {stem}.")
        markdown = md_path.read_text(encoding="utf-8")
        if (
            "Painel A" not in markdown
            or "Painel B.1" not in markdown
            or "Painel B.2" not in markdown
            or "* p<0,10; ** p<0,05; *** p<0,01" not in markdown
        ):
            raise RuntimeError(f"Incomplete Markdown panels or significance legend in {stem}.")
        if stem == "table_5_2_1_national_main_results":
            if len(data) != len(SECTION5_2_OUTCOME_ORDER) or set(data["outcome"]) != set(
                SECTION5_2_OUTCOME_ORDER
            ):
                raise RuntimeError("National Section 5.2 table must contain all primary and balance outcomes.")
            national_numeric = ["coef", "se", "p_value", "n_obs", "n_cbo"]
            if not data["result_status"].eq("estimated").all() or data[national_numeric].isna().any().any():
                raise RuntimeError("Missing or failed estimates in the national Section 5.2 table.")
            pretrend_available = data["pretrend_status"].isin(["pass", "warning", "fail"])
            if data.loc[pretrend_available, "pretrend_p_value"].isna().any():
                raise RuntimeError("Missing available pretrend diagnostics in the national Section 5.2 table.")
            expected_stars = data["p_value"].map(significance_stars)
            if not data["stars"].fillna("").astype(str).eq(expected_stars).all():
                raise RuntimeError(f"Inconsistent significance stars in {stem}.")
        else:
            spec = next(item for item in SECTION5_2_TABLE_SPECS.values() if item["stem"] == stem)
            missing_columns = required_heterogeneity_columns - set(data.columns)
            if missing_columns:
                raise RuntimeError(f"Missing heterogeneity diagnostics in {stem}: {sorted(missing_columns)}.")
            if data.duplicated(["group_id", "outcome"]).any():
                raise RuntimeError(f"Duplicate group-outcome rows in {stem}.")
            group_estimate_columns = [
                "group_coef",
                "group_se",
                "group_p_value",
                "group_n_obs",
                "group_n_cbo",
                "group_treated_cbo",
                "group_control_cbo",
            ]
            ddd_estimate_columns = [
                "ddd_coef",
                "ddd_se",
                "ddd_p_value",
                "ddd_n_obs",
                "ddd_n_cbo",
                "ddd_wald_statistic",
            ]
            group_estimated = data["group_result_status"].eq("estimated")
            ddd_estimated = data["ddd_result_status"].eq("estimated")
            if spec.get("allow_non_estimable", False):
                valid_group_status = group_estimated | data["group_result_status"].astype(str).str.startswith("failed_")
                valid_ddd_status = ddd_estimated | data["ddd_result_status"].astype(str).str.startswith("failed_")
                if not valid_group_status.all() or not valid_ddd_status.all():
                    raise RuntimeError(f"Unexpected estimation status in {stem}.")
                if data.loc[group_estimated, group_estimate_columns].isna().any().any() or data.loc[
                    ddd_estimated, ddd_estimate_columns
                ].isna().any().any():
                    raise RuntimeError(f"Missing numeric values for estimated rows in {stem}.")
                missing_group_errors = data.loc[~group_estimated, "group_error"].fillna("").astype(str).str.strip().eq("")
                missing_ddd_errors = data.loc[~ddd_estimated, "ddd_error"].fillna("").astype(str).str.strip().eq("")
                if missing_group_errors.any() or missing_ddd_errors.any():
                    raise RuntimeError(f"Failed estimates lack auditable errors in {stem}.")
            elif (
                not (group_estimated & ddd_estimated).all()
                or data[group_estimate_columns + ddd_estimate_columns].isna().any().any()
            ):
                raise RuntimeError(f"Missing or failed estimates in {stem}.")
            if not data["ddd_wald_test_method"].eq("wald_test_R_beta_eq_q_chi2").all():
                raise RuntimeError(f"Unexpected DDD hypothesis-test method in {stem}.")
            expected_group_stars = data["group_p_value"].map(significance_stars)
            expected_ddd_stars = data["ddd_p_value"].map(significance_stars)
            group_stars_match = data["group_stars"].fillna("").astype(str).eq(expected_group_stars)
            ddd_stars_match = data["ddd_stars"].fillna("").astype(str).eq(expected_ddd_stars)
            if not group_stars_match.all() or not ddd_stars_match.all():
                raise RuntimeError(f"Inconsistent significance stars in {stem}.")
            group_pre_available = data["group_pretrend_status"].isin(["pass", "warning", "fail"])
            ddd_pre_available = data["ddd_pretrend_status"].isin(["pass", "warning", "fail"])
            if data.loc[group_pre_available, "group_pretrend_p_value"].isna().any() or data.loc[
                ddd_pre_available, "ddd_pretrend_p_value"
            ].isna().any():
                raise RuntimeError(f"Missing pretrend diagnostics in {stem}.")
            flow_support = pd.to_numeric(data["target_cbo_with_flows"], errors="coerce")
            model_cbo = pd.to_numeric(data["group_n_cbo"], errors="coerce")
            max_group_cbo = model_cbo.groupby(data["group_id"]).transform("max")
            if flow_support.gt(max_group_cbo).fillna(False).any():
                raise RuntimeError(f"Flow-support CBO count exceeds the model sample in {stem}.")
            expected_groups = [
                group_id
                for group_id, _label in spec["groups"]
                for _outcome in SECTION5_2_OUTCOME_ORDER
            ]
            if data["group_id"].tolist() != expected_groups:
                raise RuntimeError(f"Unexpected group order for {stem}.")
        checks.append({"check": stem, "status": "pass", "count": len(data)})
    return pd.DataFrame(checks)
