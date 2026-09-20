"""Occupation-group main and heterogeneity tables for Section 5.4."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import CORE_OCCUPATION_GROUPS
from .formatting import fmt_number, fmt_p, markdown_table
from .section5_2_tables import (
    HETEROGENEITY_SPECS,
    NUMERIC_COLUMNS,
    OUTCOME_LABELS,
    OUTCOME_ORDER,
    significance_stars,
)


SECTION5_4_STEMS = [
    "table_5_4_1_occupation_group_main_results",
    "table_5_4_2_occupation_group_heterogeneity_sex",
    "table_5_4_3_occupation_group_heterogeneity_income",
    "table_5_4_4_occupation_group_heterogeneity_age_canaries",
    "table_5_4_5_occupation_group_heterogeneity_race_color",
    "table_5_4_6_occupation_group_heterogeneity_education",
]

SECTION5_4_TABLE_SPECS = {
    "main": {"stem": SECTION5_4_STEMS[0]},
    "sex": {
        **HETEROGENEITY_SPECS["sex"],
        "stem": SECTION5_4_STEMS[1],
        "title": "Tabela 5.4.2: Heterogeneidade por sexo nos núcleos ocupacionais",
    },
    "income": {
        **HETEROGENEITY_SPECS["income"],
        "stem": SECTION5_4_STEMS[2],
        "title": "Tabela 5.4.3: Heterogeneidade por renda pré-tratamento nos núcleos ocupacionais",
    },
    "age_canaries": {
        **HETEROGENEITY_SPECS["age_canaries"],
        "stem": SECTION5_4_STEMS[3],
        "title": "Tabela 5.4.4: Heterogeneidade por idade — coortes Canaries nos núcleos ocupacionais",
    },
    "race_color": {
        **HETEROGENEITY_SPECS["race_color"],
        "stem": SECTION5_4_STEMS[4],
        "title": "Tabela 5.4.5: Heterogeneidade por raça/cor nos núcleos ocupacionais",
    },
    "education": {
        **HETEROGENEITY_SPECS["education"],
        "stem": SECTION5_4_STEMS[5],
        "title": "Tabela 5.4.6: Heterogeneidade por escolaridade nos núcleos ocupacionais",
    },
}

SECTION5_4_EXPECTED_ROWS = {
    SECTION5_4_STEMS[0]: len(CORE_OCCUPATION_GROUPS) * len(OUTCOME_ORDER),
    **{
        SECTION5_4_TABLE_SPECS[table_id]["stem"]: (
            len(CORE_OCCUPATION_GROUPS)
            * len(SECTION5_4_TABLE_SPECS[table_id]["groups"])
            * len(OUTCOME_ORDER)
        )
        for table_id in ["sex", "income", "age_canaries", "race_color", "education"]
    },
}

DEPRECATED_SECTION5_4_STEMS = ["table_5_4_occupation_group_summary"]


def _single_row(data: pd.DataFrame, context: str) -> pd.Series:
    if len(data) != 1:
        raise ValueError(f"Expected exactly one row for {context}; found {len(data)}.")
    return data.iloc[0]


def build_occupation_main_long(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    main = sources["occupation_main"]
    pretrends = sources["occupation_pretrends"]
    rows = []
    for occupation_group_id in CORE_OCCUPATION_GROUPS:
        for outcome in OUTCOME_ORDER:
            raw = _single_row(
                main[main["group_id"].eq(occupation_group_id) & main["outcome"].eq(outcome)],
                f"{occupation_group_id} / {outcome}",
            )
            pretrend = _single_row(
                pretrends[
                    pretrends["group_id"].eq(occupation_group_id)
                    & pretrends["outcome"].eq(outcome)
                ],
                f"pretrend {occupation_group_id} / {outcome}",
            )
            rows.append(
                {
                    "occupation_group_id": occupation_group_id,
                    "occupation_group_label": raw["group_label"],
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "result_status": raw.get("result_status", ""),
                    "coef": pd.to_numeric(raw.get("coef"), errors="coerce"),
                    "se": pd.to_numeric(raw.get("se"), errors="coerce"),
                    "p_value": pd.to_numeric(raw.get("p_value"), errors="coerce"),
                    "stars": significance_stars(raw.get("p_value")),
                    "n_obs": pd.to_numeric(raw.get("n_obs"), errors="coerce"),
                    "n_cbo": pd.to_numeric(raw.get("n_cbo"), errors="coerce"),
                    "treated_cbo": pd.to_numeric(raw.get("treated_cbo_in_sample"), errors="coerce"),
                    "control_cbo": pd.to_numeric(raw.get("control_cbo_in_sample"), errors="coerce"),
                    "pretrend_status": pretrend.get("pretrend_status", "not_available"),
                    "pretrend_p_value": pd.to_numeric(pretrend.get("joint_p_value"), errors="coerce"),
                }
            )
    return pd.DataFrame(rows)


def build_occupation_heterogeneity_long(
    sources: dict[str, pd.DataFrame], table_id: str
) -> pd.DataFrame:
    if table_id not in SECTION5_4_TABLE_SPECS or table_id == "main":
        raise KeyError(f"Unknown Section 5.4 heterogeneity table: {table_id}")
    spec = SECTION5_4_TABLE_SPECS[table_id]
    source_key = "occupation_canaries" if spec["source"] == "canaries_age" else "occupation_demographic"
    source = sources[source_key]
    rows = []
    for occupation_group_id in CORE_OCCUPATION_GROUPS:
        for subgroup_id, subgroup_label in spec["groups"]:
            for outcome in OUTCOME_ORDER:
                raw = _single_row(
                    source[
                        source["group_id"].eq(occupation_group_id)
                        & source["dimension"].eq(spec["dimension"])
                        & source["heterogeneity_group_id"].eq(subgroup_id)
                        & source["outcome"].eq(outcome)
                    ],
                    f"{table_id} / {occupation_group_id} / {subgroup_id} / {outcome}",
                )
                rows.append(
                    {
                        "occupation_group_id": occupation_group_id,
                        "occupation_group_label": raw["occupation_group_label"],
                        "dimension": spec["dimension"],
                        "group_id": subgroup_id,
                        "group_label": subgroup_label,
                        "outcome": outcome,
                        "outcome_label": OUTCOME_LABELS[outcome],
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
    if out.duplicated(["occupation_group_id", "group_id", "outcome"]).any():
        raise ValueError(f"Duplicate occupation-group/subgroup/outcome rows in {table_id}.")
    return out


def _estimate_cell(
    coef: object, se: object, stars: object, status: object = "estimated"
) -> str:
    if coef is None or se is None or pd.isna(coef) or pd.isna(se):
        return "não estimável" if str(status) != "estimated" else ""
    return f"{fmt_number(coef, 4)}{stars or ''}<br>({fmt_number(se, 4)})"


def _status_with_p(status: object, p_value: object) -> str:
    status_text = str(status or "not_available")
    if p_value is None or pd.isna(p_value):
        return status_text
    return f"{status_text} (p={fmt_p(p_value)})"


def _occupation_main_markdown(data: pd.DataFrame) -> str:
    panel_a_rows = []
    for occupation_group_id in CORE_OCCUPATION_GROUPS:
        group = data[data["occupation_group_id"].eq(occupation_group_id)]
        row = {"Núcleo": group["occupation_group_label"].iloc[0]}
        for outcome in OUTCOME_ORDER:
            estimate = _single_row(group[group["outcome"].eq(outcome)], f"{occupation_group_id} / {outcome}")
            row[OUTCOME_LABELS[outcome]] = _estimate_cell(estimate["coef"], estimate["se"], estimate["stars"])
        panel_a_rows.append(row)
    panel_a = pd.DataFrame(panel_a_rows)
    panel_b = pd.DataFrame(
        [
            {
                "Núcleo": row.occupation_group_label,
                "Resultado": row.outcome_label,
                "p-valor": fmt_p(row.p_value),
                "Pretrend": _status_with_p(row.pretrend_status, row.pretrend_p_value),
                "N": fmt_number(row.n_obs, 0),
                "CBOs trat./controle": f"{fmt_number(row.treated_cbo, 0)}/{fmt_number(row.control_cbo, 0)}",
            }
            for row in data.itertuples(index=False)
        ]
    )
    return f"""# Tabela 5.4.1: Resultados principais por núcleo ocupacional

## Painel A: Efeitos médios por núcleo

{markdown_table(panel_a, list(panel_a.columns))}

## Painel B: Diagnósticos do desenho

{markdown_table(panel_b, list(panel_b.columns))}

Notas: as células do Painel A apresentam o coeficiente e, entre parênteses, o erro-padrão. Os erros-padrão são clusterizados por CBO de quatro dígitos. * p<0,10; ** p<0,05; *** p<0,01. Em cada núcleo, o tratamento reúne as CBOs explicitamente auditadas para aquele grupo e o controle reúne CBOs `Not Exposed` com match MTE oficial; `Minimal Exposure` não integra o controle. O pretrend do Painel B é o teste conjunto dos coeficientes mensais anteriores ao tratamento. Os p-valores são convencionais e não recebem correção por testes múltiplos. N denota observações CBO-mês, não trabalhadores.
"""


def _occupation_heterogeneity_markdown(data: pd.DataFrame, spec: dict[str, object]) -> str:
    panel_a_rows = []
    for occupation_group_id in CORE_OCCUPATION_GROUPS:
        occupation = data[data["occupation_group_id"].eq(occupation_group_id)]
        occupation_label = occupation["occupation_group_label"].iloc[0]
        for subgroup_id, subgroup_label in spec["groups"]:
            subgroup = occupation[occupation["group_id"].eq(subgroup_id)]
            row = {"Núcleo": occupation_label, "Grupo": subgroup_label}
            for outcome in OUTCOME_ORDER:
                estimate = _single_row(
                    subgroup[subgroup["outcome"].eq(outcome)],
                    f"{occupation_group_id} / {subgroup_id} / {outcome}",
                )
                row[OUTCOME_LABELS[outcome]] = _estimate_cell(
                    estimate["group_coef"],
                    estimate["group_se"],
                    estimate["group_stars"],
                    estimate["group_result_status"],
                )
            panel_a_rows.append(row)
    panel_a = pd.DataFrame(panel_a_rows)
    panel_b = pd.DataFrame(
        [
            {
                "Núcleo": row.occupation_group_label,
                "Grupo": row.group_label,
                "Resultado": row.outcome_label,
                "DDD grupo–complemento": _estimate_cell(
                    row.ddd_coef, row.ddd_se, row.ddd_stars, row.ddd_result_status
                ),
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
    binary_note = (
        " Em dimensões binárias, os DDDs dos dois grupos são espelhados por construção e não constituem testes independentes."
        if len(spec["groups"]) == 2
        else ""
    )
    dimension_note = f" {spec['dimension_note']}" if spec.get("dimension_note") else ""
    return f"""# {spec['title']}

## Painel A: Efeitos DiD dentro de cada grupo e núcleo

{markdown_table(panel_a, list(panel_a.columns))}

## Painel B: Contrastes DDD e diagnósticos

{markdown_table(panel_b, list(panel_b.columns))}

Notas: as células apresentam o coeficiente e, entre parênteses, o erro-padrão; `não estimável` identifica células sem variação ou amostra suficiente, preservadas no CSV com status e erro de estimação. Os erros-padrão são clusterizados por CBO de quatro dígitos. * p<0,10; ** p<0,05; *** p<0,01. O Painel A estima o DiD na amostra do grupo demográfico dentro de cada desenho ocupacional. O Painel B usa o DDD `pós × núcleo tratado × grupo demográfico` e um teste de Wald qui-quadrado para verificar formalmente se o efeito do grupo difere do complemento. Em cada núcleo, o controle reúne CBOs `Not Exposed` com match MTE oficial. Os diagnósticos de pretrend testam uma tendência linear no período pré-tratamento; não são o teste conjunto do event study do Painel B da Tabela 5.4.1. `N grupo` denota observações CBO-mês, não trabalhadores. O poder é um diagnóstico de suporte por CBOs tratadas/controle: `adequate` requer pelo menos 20/50, `limited` requer 10/25 e `thin` indica suporte inferior. Os p-valores são convencionais, sem correção por testes múltiplos; por isso, as heterogeneidades são exploratórias. Resultados com pretrend falho ou poder `thin` exigem cautela.{dimension_note}{binary_note}
"""


def write_section5_4_tables(
    sources: dict[str, pd.DataFrame], output_dir: Path
) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for stem in DEPRECATED_SECTION5_4_STEMS:
        for suffix in [".csv", ".md"]:
            (output_dir / f"{stem}{suffix}").unlink(missing_ok=True)
    generated: dict[str, pd.DataFrame] = {}
    main_stem = SECTION5_4_STEMS[0]
    main = build_occupation_main_long(sources)
    main.to_csv(output_dir / f"{main_stem}.csv", index=False)
    (output_dir / f"{main_stem}.md").write_text(_occupation_main_markdown(main), encoding="utf-8")
    generated[main_stem] = main
    for table_id in ["sex", "income", "age_canaries", "race_color", "education"]:
        spec = SECTION5_4_TABLE_SPECS[table_id]
        table = build_occupation_heterogeneity_long(sources, table_id)
        stem = str(spec["stem"])
        table.to_csv(output_dir / f"{stem}.csv", index=False)
        (output_dir / f"{stem}.md").write_text(
            _occupation_heterogeneity_markdown(table, spec), encoding="utf-8"
        )
        generated[stem] = table
    return generated


def validate_section5_4_outputs(output_dir: Path) -> pd.DataFrame:
    required_heterogeneity_columns = {
        "occupation_group_id",
        "dimension",
        "group_id",
        "outcome",
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
        "ddd_pretrend_status",
        "ddd_pretrend_p_value",
        "ddd_power_status",
        "ddd_wald_statistic",
        "ddd_wald_test_method",
    }
    checks = []
    for stem, expected_rows in SECTION5_4_EXPECTED_ROWS.items():
        csv_path = output_dir / f"{stem}.csv"
        md_path = output_dir / f"{stem}.md"
        if not csv_path.exists() or not md_path.exists():
            raise RuntimeError(f"Missing Section 5.4 table pair for {stem}.")
        data = pd.read_csv(csv_path)
        if len(data) != expected_rows:
            raise RuntimeError(f"Unexpected row count for {stem}: expected {expected_rows}, found {len(data)}.")
        artifact_text = csv_path.read_text(encoding="utf-8") + "\n" + md_path.read_text(encoding="utf-8")
        lowered = artifact_text.lower()
        if "ln_salario_real_desl" in lowered or "salário real de desligamento" in lowered:
            raise RuntimeError(f"Forbidden dismissal-wage outcome found in {stem}.")
        markdown = md_path.read_text(encoding="utf-8")
        if (
            "Painel A" not in markdown
            or "Painel B" not in markdown
            or "* p<0,10; ** p<0,05; *** p<0,01" not in markdown
        ):
            raise RuntimeError(f"Incomplete Markdown panels or significance legend in {stem}.")
        if any(label not in markdown for label in data["occupation_group_label"].drop_duplicates()):
            raise RuntimeError(f"Occupation-group labels missing from Markdown in {stem}.")
        if stem == SECTION5_4_STEMS[0]:
            expected_keys = [
                (occupation_group_id, outcome)
                for occupation_group_id in CORE_OCCUPATION_GROUPS
                for outcome in OUTCOME_ORDER
            ]
            if list(data[["occupation_group_id", "outcome"]].itertuples(index=False, name=None)) != expected_keys:
                raise RuntimeError("Unexpected occupation-group/outcome order in Section 5.4.1.")
            numeric = ["coef", "se", "p_value", "n_obs", "n_cbo", "treated_cbo", "control_cbo", "pretrend_p_value"]
            if not data["result_status"].eq("estimated").all() or data[numeric].isna().any().any():
                raise RuntimeError("Missing or failed estimates in the Section 5.4.1 table.")
            expected_stars = data["p_value"].map(significance_stars)
            if not data["stars"].fillna("").astype(str).eq(expected_stars).all():
                raise RuntimeError(f"Inconsistent significance stars in {stem}.")
        else:
            missing_columns = required_heterogeneity_columns - set(data.columns)
            if missing_columns:
                raise RuntimeError(f"Missing heterogeneity diagnostics in {stem}: {sorted(missing_columns)}.")
            if data.duplicated(["occupation_group_id", "group_id", "outcome"]).any():
                raise RuntimeError(f"Duplicate occupation-group/subgroup/outcome rows in {stem}.")
            allowed_statuses = {"estimated", "failed_insufficient_sample", "failed_estimation"}
            if not data["group_result_status"].isin(allowed_statuses).all() or not data[
                "ddd_result_status"
            ].isin(allowed_statuses).all():
                raise RuntimeError(f"Unexpected estimation status in {stem}.")
            group_estimated = data["group_result_status"].eq("estimated")
            ddd_estimated = data["ddd_result_status"].eq("estimated")
            group_numeric = [
                "group_coef",
                "group_se",
                "group_p_value",
                "group_n_obs",
                "group_n_cbo",
                "group_treated_cbo",
                "group_control_cbo",
            ]
            ddd_numeric = [
                "ddd_coef",
                "ddd_se",
                "ddd_p_value",
                "ddd_n_obs",
                "ddd_n_cbo",
                "ddd_wald_statistic",
            ]
            if data.loc[group_estimated, group_numeric].isna().any().any() or data.loc[
                ddd_estimated, ddd_numeric
            ].isna().any().any():
                raise RuntimeError(f"Missing numeric values for estimated rows in {stem}.")
            if not data["ddd_wald_test_method"].eq("wald_test_R_beta_eq_q_chi2").all():
                raise RuntimeError(f"Unexpected DDD hypothesis-test method in {stem}.")
            if not data["group_stars"].fillna("").astype(str).eq(data["group_p_value"].map(significance_stars)).all():
                raise RuntimeError(f"Inconsistent group significance stars in {stem}.")
            if not data["ddd_stars"].fillna("").astype(str).eq(data["ddd_p_value"].map(significance_stars)).all():
                raise RuntimeError(f"Inconsistent DDD significance stars in {stem}.")
            group_pre_available = data["group_pretrend_status"].isin(["pass", "warning", "fail"])
            ddd_pre_available = data["ddd_pretrend_status"].isin(["pass", "warning", "fail"])
            if data.loc[group_pre_available, "group_pretrend_p_value"].isna().any() or data.loc[
                ddd_pre_available, "ddd_pretrend_p_value"
            ].isna().any():
                raise RuntimeError(f"Missing pretrend diagnostics in {stem}.")
            flow_support = pd.to_numeric(data["target_cbo_with_flows"], errors="coerce")
            model_cbo = pd.to_numeric(data["group_n_cbo"], errors="coerce")
            max_group_cbo = model_cbo.groupby([data["occupation_group_id"], data["group_id"]]).transform("max")
            if flow_support.gt(max_group_cbo).fillna(False).any():
                raise RuntimeError(f"Flow-support CBO count exceeds the model sample in {stem}.")
            spec = next(item for item in SECTION5_4_TABLE_SPECS.values() if item["stem"] == stem)
            expected_keys = [
                (occupation_group_id, subgroup_id, outcome)
                for occupation_group_id in CORE_OCCUPATION_GROUPS
                for subgroup_id, _label in spec["groups"]
                for outcome in OUTCOME_ORDER
            ]
            actual_keys = list(
                data[["occupation_group_id", "group_id", "outcome"]].itertuples(index=False, name=None)
            )
            if actual_keys != expected_keys:
                raise RuntimeError(f"Unexpected occupation-group/subgroup/outcome order in {stem}.")
        checks.append({"check": stem, "status": "pass", "count": len(data)})
    return pd.DataFrame(checks)
