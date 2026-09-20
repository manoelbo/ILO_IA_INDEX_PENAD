"""Build manual occupation-group extensions for Section 4."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from section4_event_study.config import (
    CONTROL_COLUMNS,
    NET_FLOW_EVENT_OUTCOMES,
    NET_FLOW_OUTCOMES,
    OUTPUT_ROOT,
    REAL_ALL_OUTCOMES,
    REAL_MAIN_OUTCOMES,
    TREATMENT_PERIOD,
)
from section4_event_study.data import add_net_flow_measures, add_real_wage_measures, load_analysis_data, load_ipca
from section4_event_study.estimation import estimate_event_study, estimate_term
from section4_event_study.formatting import estimate_cell, fmt_number, write_markdown_table
from section4_event_study.heterogeneity import (
    CANARIES_AGE_DIMENSIONS,
    DIMENSIONS,
    aggregate_micro_group_pairs,
    build_pre_treatment_income_groups,
    estimate_heterogeneity,
    iter_raw_batches,
    normalize_codes,
    valid_cbo_4d,
)
from section4_event_study.manual_occupation_groups import (
    EXPLORATORY_GROUP_IDS,
    GROUP_SPEC_BY_ID,
    GROUP_SPECS,
    build_manual_group_roles,
    manual_group_audit,
    official_group_ids,
)
from section4_event_study.treatment import apply_roles


OUT_DIR = OUTPUT_ROOT / "manual_occupation_groups_extension"
TABLE_DIR = OUT_DIR / "tables"
FIGURE_DIR = OUT_DIR / "figures"
AUDIT_DIR = OUT_DIR / "audit"
REPORT_PATH = OUT_DIR / "occupation_groups_report.md"
VISUALIZER_CROSSWALK = OUTPUT_ROOT.parents[0] / "crosswalk_visualizer" / "cbo_isco08_crosswalk_visual.csv"
RESULT_OUTCOMES = REAL_ALL_OUTCOMES
MARKDOWN_OUTPUTS = [
    ("Resultados principais", TABLE_DIR / "occupation_group_main_results.md", TABLE_DIR / "occupation_group_main_results.csv"),
    ("Event study e pretrends", TABLE_DIR / "occupation_group_event_study_pretrends.md", TABLE_DIR / "occupation_group_event_study_pretrends.csv"),
    ("Heterogeneidade demografica", TABLE_DIR / "occupation_group_demographic_heterogeneity.md", TABLE_DIR / "occupation_group_demographic_heterogeneity.csv"),
    ("Heterogeneidade etaria Canaries", TABLE_DIR / "occupation_group_canaries_age_heterogeneity.md", TABLE_DIR / "occupation_group_canaries_age_heterogeneity.csv"),
    ("Saldo liquido por grupo", TABLE_DIR / "occupation_group_net_flow_results.md", TABLE_DIR / "occupation_group_net_flow_results.csv"),
    ("Pretrends do saldo liquido", TABLE_DIR / "occupation_group_net_flow_pretrends.md", TABLE_DIR / "occupation_group_net_flow_pretrends.csv"),
    ("Heterogeneidade do saldo liquido", TABLE_DIR / "occupation_group_net_flow_heterogeneity.md", TABLE_DIR / "occupation_group_net_flow_heterogeneity.csv"),
    ("Resumo interpretativo", TABLE_DIR / "occupation_group_evidence_summary.md", TABLE_DIR / "occupation_group_evidence_summary.csv"),
    ("Auditoria dos CBOs manuais", AUDIT_DIR / "manual_group_cbo_audit.md", AUDIT_DIR / "manual_group_cbo_audit.csv"),
    ("Auditoria CBOs sem MTE", AUDIT_DIR / "clear_tech_no_mte_loss_audit.md", AUDIT_DIR / "clear_tech_no_mte_loss_audit.csv"),
]


def log(message: str) -> None:
    print(message, flush=True)


def prepare_dirs() -> None:
    for directory in [TABLE_DIR, FIGURE_DIR, AUDIT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        for path in directory.glob("*"):
            if path.is_file():
                path.unlink()


def _format_bool(value: object) -> str:
    return "sim" if bool(value) else "não"


def _normal_p(value: object) -> str:
    return fmt_number(value, 3)


def _link(path: Path, label: str | None = None) -> str:
    return f"[{label or path.name}](<{path.resolve()}>)"


def _relative_to_out(path: Path) -> str:
    return path.relative_to(OUT_DIR).as_posix()


def _navigation_rows() -> pd.DataFrame:
    rows = []
    for label, md_path, csv_path in MARKDOWN_OUTPUTS:
        rows.append(
            {
                "Arquivo": label,
                "Markdown": _link(md_path, _relative_to_out(md_path)),
                "CSV": _link(csv_path, _relative_to_out(csv_path)),
            }
        )
    return pd.DataFrame(rows)


def _add_file_context(path: Path, csv_path: Path | None = None) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if "## Onde encontrar este arquivo" in text:
        return
    lines = text.splitlines()
    context = [
        "",
        "## Onde encontrar este arquivo",
        "",
        f"- Markdown: `{path.resolve()}`",
        f"- Pasta da extensao: `{OUT_DIR.resolve()}`",
        f"- Relatorio principal: {_link(REPORT_PATH, 'occupation_groups_report.md')}",
    ]
    if csv_path is not None:
        context.append(f"- CSV auditavel: `{csv_path.resolve()}`")
    insert_at = 1 if lines and lines[0].startswith("# ") else 0
    updated = "\n".join(lines[:insert_at] + context + lines[insert_at:]) + "\n"
    path.write_text(updated, encoding="utf-8")


def write_navigation_files() -> None:
    navigation = _navigation_rows()
    table = "| Arquivo | Markdown | CSV |\n| --- | --- | --- |\n" + "\n".join(
        f"| {row.Arquivo} | {row.Markdown} | {row.CSV} |"
        for row in navigation.itertuples()
    )
    readme = "\n\n".join(
        [
            "# Manual Occupation Groups Extension",
            "Este diretorio contem a extensao da Secao 4 para grupos ocupacionais manuais.",
            f"Pasta absoluta: `{OUT_DIR.resolve()}`",
            "## Arquivos principais",
            table,
            f"Relatorio principal: {_link(REPORT_PATH, 'occupation_groups_report.md')}",
        ]
    )
    (OUT_DIR / "README.md").write_text(readme + "\n", encoding="utf-8")
    (TABLE_DIR / "README.md").write_text(
        "# Tabelas da extensao de grupos ocupacionais\n\n"
        + table
        + f"\n\nRelatorio principal: {_link(REPORT_PATH, 'occupation_groups_report.md')}\n",
        encoding="utf-8",
    )
    audit_rows = navigation[navigation["Arquivo"].str.contains("Auditoria", case=False, na=False)]
    audit_table = "| Arquivo | Markdown | CSV |\n| --- | --- | --- |\n" + "\n".join(
        f"| {row.Arquivo} | {row.Markdown} | {row.CSV} |"
        for row in audit_rows.itertuples()
    )
    (AUDIT_DIR / "README.md").write_text(
        "# Auditorias da extensao de grupos ocupacionais\n\n"
        + audit_table
        + f"\n\nRelatorio principal: {_link(REPORT_PATH, 'occupation_groups_report.md')}\n",
        encoding="utf-8",
    )
    for _label, md_path, csv_path in MARKDOWN_OUTPUTS:
        _add_file_context(md_path, csv_path)


def _result_row(group_id: str, outcome: str, label: str, est: dict[str, object], sample: pd.DataFrame) -> dict[str, object]:
    spec = GROUP_SPEC_BY_ID[group_id]
    treated_cbo = sample.loc[sample["scenario_treat"].eq(1), "cbo_4d"].nunique()
    control_cbo = sample.loc[sample["scenario_treat"].eq(0), "cbo_4d"].nunique()
    return {
        "group_id": group_id,
        "group_label": spec.label_pt,
        "short_label": spec.short_label_pt,
        "exploratory_only": spec.exploratory_only,
        "outcome": outcome,
        "outcome_label": label,
        "treated_cbo_in_sample": int(treated_cbo),
        "control_cbo_in_sample": int(control_cbo),
        "estimator": "OLS",
        **est,
    }


def build_group_audit(classification: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    visual = pd.read_csv(VISUALIZER_CROSSWALK, dtype={"cbo_4d": str})
    visual["cbo_4d"] = visual["cbo_4d"].astype(str).str.zfill(4)
    visual_cols = ["cbo_4d", "caged_admissions_total", "caged_panel_rows"]
    audit = manual_group_audit(classification)
    audit = audit.merge(visual[visual_cols], on="cbo_4d", how="left")
    audit["in_official_panel"] = audit["cbo_4d"].isin(panel["cbo_4d"].astype(str).str.zfill(4).unique())
    audit["caged_admissions_total"] = pd.to_numeric(audit["caged_admissions_total"], errors="coerce").fillna(0)
    audit.to_csv(AUDIT_DIR / "manual_group_cbo_audit.csv", index=False)
    view = audit.assign(
        Grupo=audit["group_label"],
        CBO=audit["cbo_4d"],
        Titulo=audit["cbo_title"].fillna(""),
        MTE=audit["mte_match_status"],
        Gradiente=audit["cbo_ilo_gradient"],
        Oficial=audit["official_model_eligible"].map(_format_bool),
        Exploratorio=audit["exploratory_only"].map(_format_bool),
        Painel=audit["in_official_panel"].map(_format_bool),
        Admissoes=audit["caged_admissions_total"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        AUDIT_DIR / "manual_group_cbo_audit.md",
        "Auditoria dos grupos ocupacionais manuais",
        view,
        ["Grupo", "CBO", "Titulo", "MTE", "Gradiente", "Oficial", "Exploratorio", "Painel", "Admissoes"],
        note=(
            "Grupos oficiais entram apenas quando o CBO tem match MTE oficial. "
            "CBOs sem MTE são mantidos em bloco exploratório separado."
        ),
    )
    loss = audit[audit["exploratory_only"] | (~audit["in_official_panel"])].copy()
    loss.to_csv(AUDIT_DIR / "clear_tech_no_mte_loss_audit.csv", index=False)
    loss_view = loss.assign(
        Grupo=loss["group_label"],
        CBO=loss["cbo_4d"],
        Titulo=loss["cbo_title"].fillna(""),
        MTE=loss["mte_match_status"],
        Painel=loss["in_official_panel"].map(_format_bool),
        Exploratorio=loss["exploratory_only"].map(_format_bool),
        Admissoes=loss["caged_admissions_total"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        AUDIT_DIR / "clear_tech_no_mte_loss_audit.md",
        "Auditoria de CBOs sem MTE ou fora do painel oficial",
        loss_view,
        ["Grupo", "CBO", "Titulo", "MTE", "Painel", "Exploratorio", "Admissoes"],
        note="Essas linhas documentam perda amostral e o bloco exploratório de tecnologia sem MTE.",
    )
    return audit


def build_clear_tech_no_mte_auxiliary_panel(panel: pd.DataFrame, classification: pd.DataFrame) -> pd.DataFrame:
    target_cbo = EXPLORATORY_GROUP_IDS["clear_tech_no_mte"]
    raw_cols = [
        "ano",
        "mes",
        "cbo_2002",
        "saldo_movimentacao",
        "salario_mensal",
        "idade",
        "sexo",
        "grau_instrucao",
        "raca_cor",
    ]
    pieces: list[pd.DataFrame] = []
    for _path, df in iter_raw_batches(raw_cols):
        df = df.copy()
        df["cbo_4d"] = valid_cbo_4d(df["cbo_2002"])
        df = df[df["cbo_4d"].isin(target_cbo)].copy()
        if df.empty:
            continue
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int16")
        df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int8")
        df["periodo"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
        df["periodo_num"] = df["ano"].astype("Int32") * 100 + df["mes"].astype("Int32")
        saldo = pd.to_numeric(df["saldo_movimentacao"], errors="coerce")
        wage = pd.to_numeric(df["salario_mensal"], errors="coerce")
        is_adm = saldo.eq(1)
        is_des = saldo.eq(-1)
        sex = normalize_codes(df["sexo"])
        edu = normalize_codes(df["grau_instrucao"])
        race = normalize_codes(df["raca_cor"])
        df["is_adm"] = is_adm.astype(int)
        df["is_des"] = is_des.astype(int)
        df["salario_adm_sum"] = np.where(is_adm & wage.gt(0), wage, 0.0)
        df["salario_adm_count"] = np.where(is_adm & wage.gt(0), 1, 0)
        df["salario_desl_sum"] = np.where(is_des & wage.gt(0), wage, 0.0)
        df["salario_desl_count"] = np.where(is_des & wage.gt(0), 1, 0)
        df["idade_adm_sum"] = np.where(is_adm, pd.to_numeric(df["idade"], errors="coerce"), 0.0)
        df["mulher_adm_sum"] = np.where(is_adm & sex.eq("3"), 1, 0)
        df["superior_adm_sum"] = np.where(is_adm & edu.isin(["8", "9", "10", "11", "80"]), 1, 0)
        df["negra_adm_sum"] = np.where(is_adm & race.isin(["2", "3"]), 1, 0)
        agg = (
            df.groupby(["cbo_4d", "ano", "mes", "periodo", "periodo_num"], observed=True)
            .agg(
                admissoes=("is_adm", "sum"),
                desligamentos=("is_des", "sum"),
                salario_adm_sum=("salario_adm_sum", "sum"),
                salario_adm_count=("salario_adm_count", "sum"),
                salario_desl_sum=("salario_desl_sum", "sum"),
                salario_desl_count=("salario_desl_count", "sum"),
                idade_adm_sum=("idade_adm_sum", "sum"),
                mulher_adm_sum=("mulher_adm_sum", "sum"),
                superior_adm_sum=("superior_adm_sum", "sum"),
                negra_adm_sum=("negra_adm_sum", "sum"),
            )
            .reset_index()
        )
        pieces.append(agg)
    if not pieces:
        return pd.DataFrame()
    raw = (
        pd.concat(pieces, ignore_index=True)
        .groupby(["cbo_4d", "ano", "mes", "periodo", "periodo_num"], observed=True)
        .sum(numeric_only=True)
        .reset_index()
    )
    periods = panel[["ano", "mes", "periodo", "periodo_num", "post", "tempo_relativo_meses"]].drop_duplicates()
    calendar = pd.MultiIndex.from_product(
        [sorted(target_cbo), sorted(periods["periodo"].unique())],
        names=["cbo_4d", "periodo"],
    ).to_frame(index=False)
    calendar = calendar.merge(periods, on="periodo", how="left")
    out = calendar.merge(raw, on=["cbo_4d", "ano", "mes", "periodo", "periodo_num"], how="left")
    for col in [
        "admissoes",
        "desligamentos",
        "salario_adm_sum",
        "salario_adm_count",
        "salario_desl_sum",
        "salario_desl_count",
        "idade_adm_sum",
        "mulher_adm_sum",
        "superior_adm_sum",
        "negra_adm_sum",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    adm = out["admissoes"].replace(0, np.nan)
    out["salario_medio_adm"] = np.where(out["salario_adm_count"] > 0, out["salario_adm_sum"] / out["salario_adm_count"], np.nan)
    out["salario_medio_desl"] = np.where(out["salario_desl_count"] > 0, out["salario_desl_sum"] / out["salario_desl_count"], np.nan)
    out["idade_media_adm"] = out["idade_adm_sum"] / adm
    out["pct_mulher_adm"] = out["mulher_adm_sum"] / adm
    out["pct_superior_adm"] = out["superior_adm_sum"] / adm
    out["pct_negra_adm"] = out["negra_adm_sum"] / adm
    out["ln_admissoes"] = np.log(out["admissoes"] + 1)
    out["ln_desligamentos"] = np.log(out["desligamentos"] + 1)
    out["ln_salario_adm"] = np.log(pd.to_numeric(out["salario_medio_adm"], errors="coerce").clip(lower=1))
    out["ln_salario_desl"] = np.log(pd.to_numeric(out["salario_medio_desl"], errors="coerce").clip(lower=1))
    out["cbo_2d"] = out["cbo_4d"].str[:2]
    out["crosswalk_spec"] = "manual_no_mte_auxiliary"
    out = add_real_wage_measures(out, load_ipca())
    pre = (
        out[out["periodo_num"] < TREATMENT_PERIOD]
        .groupby("cbo_4d", observed=True)["admissoes"]
        .mean()
        .rename("pre_adm_weight")
        .reset_index()
    )
    out = out.merge(pre, on="cbo_4d", how="left")
    out["pre_adm_weight"] = pd.to_numeric(out["pre_adm_weight"], errors="coerce")
    out = add_net_flow_measures(out)
    class_cols = ["cbo_4d", "mte_match_status", "cbo_ilo_gradient", "continuous_exposure", "continuous_exposure_raw"]
    available = [col for col in class_cols if col in classification.columns]
    out = out.merge(classification[available].drop_duplicates("cbo_4d"), on="cbo_4d", how="left")
    out["mte_match_status"] = out["mte_match_status"].fillna("sem_match_mte_no_result")
    out["cbo_ilo_gradient"] = out["cbo_ilo_gradient"].fillna("No score")
    return out[[col for col in panel.columns if col in out.columns] + [col for col in out.columns if col not in panel.columns]]


def apply_group_sample(panel: pd.DataFrame, classification: pd.DataFrame, group_id: str, allow_exploratory: bool = False) -> pd.DataFrame:
    roles = build_manual_group_roles(classification, group_id, allow_exploratory_treated=allow_exploratory)
    sample = apply_roles(panel, roles)
    return sample.copy()


def estimate_group_results(panel: pd.DataFrame, classification: pd.DataFrame, group_ids: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    pretrend_rows: list[pd.DataFrame] = []
    coef_rows: list[pd.DataFrame] = []
    for group_id in group_ids:
        spec = GROUP_SPEC_BY_ID[group_id]
        log(f"Estimating main effects and event studies for {group_id}...")
        sample = apply_group_sample(panel, classification, group_id, allow_exploratory=spec.exploratory_only)
        if sample.empty or sample["scenario_treat"].nunique() < 2:
            for outcome, label in RESULT_OUTCOMES.items():
                rows.append(
                    {
                        "group_id": group_id,
                        "group_label": spec.label_pt,
                        "short_label": spec.short_label_pt,
                        "exploratory_only": spec.exploratory_only,
                        "outcome": outcome,
                        "outcome_label": label,
                        "treated_cbo_in_sample": 0,
                        "control_cbo_in_sample": 0,
                        "estimator": "OLS",
                        "result_status": "skipped_insufficient_variation",
                        "coef": np.nan,
                        "se": np.nan,
                        "p_value": np.nan,
                        "stars": "",
                        "n_obs": int(len(sample)),
                        "n_cbo": int(sample["cbo_4d"].nunique()) if "cbo_4d" in sample else 0,
                        "n_clusters": 0,
                        "error": "No treated/control variation after sample construction.",
                    }
                )
            continue
        for outcome, label in RESULT_OUTCOMES.items():
            est = estimate_term(sample, outcome, term="post_treat")
            rows.append(_result_row(group_id, outcome, label, est, sample))
        coefs, pretrends = estimate_event_study(sample, RESULT_OUTCOMES)
        coefs["group_id"] = group_id
        coefs["group_label"] = spec.label_pt
        coefs["short_label"] = spec.short_label_pt
        coefs["exploratory_only"] = spec.exploratory_only
        pretrends["group_id"] = group_id
        pretrends["group_label"] = spec.label_pt
        pretrends["short_label"] = spec.short_label_pt
        pretrends["exploratory_only"] = spec.exploratory_only
        coef_rows.append(coefs)
        pretrend_rows.append(pretrends)
    results = pd.DataFrame(rows)
    pretrends = pd.concat(pretrend_rows, ignore_index=True) if pretrend_rows else pd.DataFrame()
    coefficients = pd.concat(coef_rows, ignore_index=True) if coef_rows else pd.DataFrame()
    return results, pretrends, coefficients


def _write_result_table(results: pd.DataFrame) -> None:
    results.to_csv(TABLE_DIR / "occupation_group_main_results.csv", index=False)
    view = results.assign(
        Grupo=results["group_label"],
        Resultado=results["outcome_label"],
        Estimativa=[estimate_cell(row.coef, row.se, row.stars) for row in results.itertuples()],
        p=results["p_value"].map(_normal_p),
        Tratados=results["treated_cbo_in_sample"].map(lambda v: fmt_number(v, 0)),
        Controle=results["control_cbo_in_sample"].map(lambda v: fmt_number(v, 0)),
        N=results["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=results["n_cbo"].map(lambda v: fmt_number(v, 0)),
        Status=results["result_status"],
        Exploratorio=results["exploratory_only"].map(_format_bool),
    )
    write_markdown_table(
        TABLE_DIR / "occupation_group_main_results.md",
        "Resultados principais por grupo ocupacional manual",
        view,
        ["Grupo", "Resultado", "Estimativa", "p", "Tratados", "Controle", "N", "CBOs", "Status", "Exploratorio"],
        note="Controle: CBOs Not Exposed com match MTE oficial. O bloco sem MTE é explicitamente exploratório.",
    )


def _write_pretrend_table(pretrends: pd.DataFrame) -> None:
    pretrends.to_csv(TABLE_DIR / "occupation_group_event_study_pretrends.csv", index=False)
    if pretrends.empty:
        return
    view = pretrends.assign(
        Grupo=pretrends["group_label"],
        Resultado=pretrends["outcome_label"],
        CoefsPre=pretrends["n_pre_coefficients"].map(lambda v: fmt_number(v, 0)),
        SigPre=pretrends["n_pre_p_lt_005"].map(lambda v: fmt_number(v, 0)),
        pConjunto=pretrends["joint_p_value"].map(lambda v: fmt_number(v, 4)),
        Status=pretrends["pretrend_status"],
        Exploratorio=pretrends["exploratory_only"].map(_format_bool),
    )
    write_markdown_table(
        TABLE_DIR / "occupation_group_event_study_pretrends.md",
        "Pretrends do event study por grupo ocupacional",
        view,
        ["Grupo", "Resultado", "CoefsPre", "SigPre", "pConjunto", "Status", "Exploratorio"],
        note="Referência do event study: t=-1. Falhas de pretrend reduzem a força causal da interpretação.",
    )


def plot_event_studies(coefficients: pd.DataFrame) -> None:
    if coefficients.empty:
        return
    coefficients.to_csv(TABLE_DIR / "occupation_group_event_study_coefficients.csv", index=False)
    for (group_id, outcome), data in coefficients.groupby(["group_id", "outcome"], observed=True):
        data = data.sort_values("t")
        fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
        ax.axhline(0, color="#333333", linewidth=1)
        ax.axvline(-0.5, color="#777777", linestyle="--", linewidth=1)
        ax.plot(data["t"], data["coef"], marker="o", markersize=3, linewidth=1.6, color="#2f6f9f")
        ax.fill_between(data["t"], data["ci_low"], data["ci_high"], color="#2f6f9f", alpha=0.18)
        ax.set_title(f"{data['short_label'].iloc[0]}: {data['outcome_label'].iloc[0]}")
        ax.set_xlabel("Meses relativos a dez/2022")
        ax.set_ylabel("Coeficiente")
        ax.grid(True, alpha=0.25)
        fig.savefig(FIGURE_DIR / f"{group_id}_{outcome}.png", dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(fig)


def estimate_group_heterogeneity(panel: pd.DataFrame, classification: pd.DataFrame, group_ids: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    demographic_rows: list[pd.DataFrame] = []
    canaries_rows: list[pd.DataFrame] = []
    for group_id in group_ids:
        spec = GROUP_SPEC_BY_ID[group_id]
        log(f"Estimating mandatory heterogeneity for {group_id}...")
        sample = apply_group_sample(panel, classification, group_id, allow_exploratory=spec.exploratory_only)
        if sample.empty or sample["scenario_treat"].nunique() < 2:
            continue
        demographic = estimate_heterogeneity(sample, outcomes=REAL_MAIN_OUTCOMES, dimensions=DIMENSIONS)
        demographic = demographic.rename(columns={"group_id": "heterogeneity_group_id", "group_label": "heterogeneity_group_label"})
        demographic["group_id"] = group_id
        demographic["occupation_group_label"] = spec.label_pt
        demographic["short_label"] = spec.short_label_pt
        demographic["exploratory_only"] = spec.exploratory_only
        demographic_rows.append(demographic)
        canaries = estimate_heterogeneity(sample, outcomes=REAL_MAIN_OUTCOMES, dimensions=CANARIES_AGE_DIMENSIONS)
        canaries = canaries.rename(columns={"group_id": "heterogeneity_group_id", "group_label": "heterogeneity_group_label"})
        canaries["group_id"] = group_id
        canaries["occupation_group_label"] = spec.label_pt
        canaries["short_label"] = spec.short_label_pt
        canaries["exploratory_only"] = spec.exploratory_only
        canaries_rows.append(canaries)
    demographic_out = pd.concat(demographic_rows, ignore_index=True) if demographic_rows else pd.DataFrame()
    canaries_out = pd.concat(canaries_rows, ignore_index=True) if canaries_rows else pd.DataFrame()
    return demographic_out, canaries_out


def write_heterogeneity_tables(demographic: pd.DataFrame, canaries: pd.DataFrame) -> None:
    demographic.to_csv(TABLE_DIR / "occupation_group_demographic_heterogeneity.csv", index=False)
    canaries.to_csv(TABLE_DIR / "occupation_group_canaries_age_heterogeneity.csv", index=False)
    for path, title, data, note in [
        (
            TABLE_DIR / "occupation_group_demographic_heterogeneity.md",
            "Heterogeneidade demográfica por grupo ocupacional",
            demographic,
            "Coeficiente: post × grupo ocupacional tratado × perfil demográfico.",
        ),
        (
            TABLE_DIR / "occupation_group_canaries_age_heterogeneity.md",
            "Heterogeneidade por idade estilo Canaries por grupo ocupacional",
            canaries,
            "Coeficiente: post × grupo ocupacional tratado × faixa etária Canaries.",
        ),
    ]:
        if data.empty:
            write_markdown_table(path, title, data, ["Grupo", "Painel", "Perfil", "Resultado", "Estimativa", "p"], note=note)
            continue
        data = data.copy()
        data["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in data.itertuples()]
        view = data.assign(
            Grupo=data["occupation_group_label"],
            Painel=data["panel"],
            Perfil=data["heterogeneity_group_label"],
            Resultado=data["outcome_label"],
            Estimativa=data["estimate_se"],
            p=data["p_value"].map(_normal_p),
            Pretrend=data["pretrend_status"],
            Poder=data["power_status"],
            N=data["n_obs"].map(lambda v: fmt_number(v, 0)),
            CBOs=data["n_cbo"].map(lambda v: fmt_number(v, 0)),
            Status=data["result_status"],
            Exploratorio=data["exploratory_only"].map(_format_bool),
        )
        write_markdown_table(
            path,
            title,
            view,
            ["Grupo", "Painel", "Perfil", "Resultado", "Estimativa", "p", "Pretrend", "Poder", "N", "CBOs", "Status", "Exploratorio"],
            note=note,
        )


def estimate_group_net_flow(panel: pd.DataFrame, classification: pd.DataFrame, group_ids: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_rows: list[dict[str, object]] = []
    pretrend_rows: list[pd.DataFrame] = []
    coefficient_rows: list[pd.DataFrame] = []
    heterogeneity_rows: list[pd.DataFrame] = []
    net_dimensions = {**DIMENSIONS, **CANARIES_AGE_DIMENSIONS}
    for group_id in group_ids:
        spec = GROUP_SPEC_BY_ID[group_id]
        log(f"Estimating net-flow outcomes for {group_id}...")
        sample = apply_group_sample(panel, classification, group_id, allow_exploratory=spec.exploratory_only)
        if sample.empty or sample["scenario_treat"].nunique() < 2:
            continue
        for outcome, label in NET_FLOW_OUTCOMES.items():
            est = estimate_term(sample, outcome, term="post_treat")
            result_rows.append(_result_row(group_id, outcome, label, est, sample))
        coefs, pretrends = estimate_event_study(sample, NET_FLOW_EVENT_OUTCOMES)
        coefs["group_id"] = group_id
        coefs["group_label"] = spec.label_pt
        coefs["short_label"] = spec.short_label_pt
        coefs["exploratory_only"] = spec.exploratory_only
        pretrends["group_id"] = group_id
        pretrends["group_label"] = spec.label_pt
        pretrends["short_label"] = spec.short_label_pt
        pretrends["exploratory_only"] = spec.exploratory_only
        coefficient_rows.append(coefs)
        pretrend_rows.append(pretrends)
        heterogeneity = estimate_heterogeneity(sample, outcomes=NET_FLOW_OUTCOMES, dimensions=net_dimensions)
        heterogeneity = heterogeneity.rename(columns={"group_id": "heterogeneity_group_id", "group_label": "heterogeneity_group_label"})
        heterogeneity["group_id"] = group_id
        heterogeneity["occupation_group_label"] = spec.label_pt
        heterogeneity["short_label"] = spec.short_label_pt
        heterogeneity["exploratory_only"] = spec.exploratory_only
        heterogeneity_rows.append(heterogeneity)
    results = pd.DataFrame(result_rows)
    pretrends = pd.concat(pretrend_rows, ignore_index=True) if pretrend_rows else pd.DataFrame()
    coefficients = pd.concat(coefficient_rows, ignore_index=True) if coefficient_rows else pd.DataFrame()
    heterogeneity = pd.concat(heterogeneity_rows, ignore_index=True) if heterogeneity_rows else pd.DataFrame()
    coefficients.to_csv(TABLE_DIR / "occupation_group_net_flow_event_study_coefficients.csv", index=False)
    return results, pretrends, heterogeneity


def write_net_flow_tables(results: pd.DataFrame, pretrends: pd.DataFrame, heterogeneity: pd.DataFrame) -> None:
    results.to_csv(TABLE_DIR / "occupation_group_net_flow_results.csv", index=False)
    if results.empty:
        write_markdown_table(
            TABLE_DIR / "occupation_group_net_flow_results.md",
            "Saldo líquido por grupo ocupacional",
            pd.DataFrame(columns=["Grupo", "Resultado", "Estimativa", "p", "Status"]),
            ["Grupo", "Resultado", "Estimativa", "p", "Status"],
            note="Sem estimações de saldo líquido.",
        )
    else:
        view = results.assign(
            Grupo=results["group_label"],
            Resultado=results["outcome_label"],
            Estimativa=[estimate_cell(row.coef, row.se, row.stars) for row in results.itertuples()],
            p=results["p_value"].map(_normal_p),
            Tratados=results["treated_cbo_in_sample"].map(lambda v: fmt_number(v, 0)),
            Controle=results["control_cbo_in_sample"].map(lambda v: fmt_number(v, 0)),
            N=results["n_obs"].map(lambda v: fmt_number(v, 0)),
            CBOs=results["n_cbo"].map(lambda v: fmt_number(v, 0)),
            Status=results["result_status"],
            Exploratorio=results["exploratory_only"].map(_format_bool),
        )
        write_markdown_table(
            TABLE_DIR / "occupation_group_net_flow_results.md",
            "Saldo líquido por grupo ocupacional",
            view,
            ["Grupo", "Resultado", "Estimativa", "p", "Tratados", "Controle", "N", "CBOs", "Status", "Exploratorio"],
            note="Saldo líquido é complementar a admissões e demissões separadas; `asinh(saldo)` aceita valores negativos e zero.",
        )

    pretrends.to_csv(TABLE_DIR / "occupation_group_net_flow_pretrends.csv", index=False)
    if pretrends.empty:
        write_markdown_table(
            TABLE_DIR / "occupation_group_net_flow_pretrends.md",
            "Pretrends do saldo líquido por grupo ocupacional",
            pd.DataFrame(columns=["Grupo", "Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"]),
            ["Grupo", "Resultado", "CoefsPre", "SigPre", "pConjunto", "Status"],
            note="Sem pretrends de saldo líquido estimados.",
        )
    else:
        pre_view = pretrends.assign(
            Grupo=pretrends["group_label"],
            Resultado=pretrends["outcome_label"],
            CoefsPre=pretrends["n_pre_coefficients"].map(lambda v: fmt_number(v, 0)),
            SigPre=pretrends["n_pre_p_lt_005"].map(lambda v: fmt_number(v, 0)),
            pConjunto=pretrends["joint_p_value"].map(lambda v: fmt_number(v, 4)),
            Status=pretrends["pretrend_status"],
            Exploratorio=pretrends["exploratory_only"].map(_format_bool),
        )
        write_markdown_table(
            TABLE_DIR / "occupation_group_net_flow_pretrends.md",
            "Pretrends do saldo líquido por grupo ocupacional",
            pre_view,
            ["Grupo", "Resultado", "CoefsPre", "SigPre", "pConjunto", "Status", "Exploratorio"],
            note="Referência do event study: t=-1. Falhas de pretrend reduzem a força causal da leitura do saldo.",
        )

    heterogeneity.to_csv(TABLE_DIR / "occupation_group_net_flow_heterogeneity.csv", index=False)
    if heterogeneity.empty:
        write_markdown_table(
            TABLE_DIR / "occupation_group_net_flow_heterogeneity.md",
            "Heterogeneidade do saldo líquido por grupo ocupacional",
            pd.DataFrame(columns=["Grupo", "Painel", "Perfil", "Resultado", "Estimativa", "p"]),
            ["Grupo", "Painel", "Perfil", "Resultado", "Estimativa", "p"],
            note="Sem heterogeneidade de saldo líquido estimada.",
        )
        return
    heterogeneity = heterogeneity.copy()
    heterogeneity["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in heterogeneity.itertuples()]
    het_view = heterogeneity.assign(
        Grupo=heterogeneity["occupation_group_label"],
        Painel=heterogeneity["panel"],
        Perfil=heterogeneity["heterogeneity_group_label"],
        Resultado=heterogeneity["outcome_label"],
        Estimativa=heterogeneity["estimate_se"],
        p=heterogeneity["p_value"].map(_normal_p),
        Pretrend=heterogeneity["pretrend_status"],
        Poder=heterogeneity["power_status"],
        N=heterogeneity["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=heterogeneity["n_cbo"].map(lambda v: fmt_number(v, 0)),
        Status=heterogeneity["result_status"],
        Exploratorio=heterogeneity["exploratory_only"].map(_format_bool),
    )
    write_markdown_table(
        TABLE_DIR / "occupation_group_net_flow_heterogeneity.md",
        "Heterogeneidade do saldo líquido por grupo ocupacional",
        het_view,
        ["Grupo", "Painel", "Perfil", "Resultado", "Estimativa", "p", "Pretrend", "Poder", "N", "CBOs", "Status", "Exploratorio"],
        note="Coeficiente: post × grupo ocupacional tratado × perfil demográfico; saldo reconstruído dos microdados.",
    )


def group_evidence_summary(results: pd.DataFrame, pretrends: pd.DataFrame, demographic: pd.DataFrame, canaries: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in GROUP_SPECS:
        main_wage = results[
            results["group_id"].eq(spec.group_id)
            & results["outcome"].eq("ln_salario_real_adm")
            & results["result_status"].eq("estimated")
        ]
        wage_pre = pretrends[pretrends["group_id"].eq(spec.group_id) & pretrends["outcome"].eq("ln_salario_real_adm")]
        youth = canaries[
            canaries["group_id"].eq(spec.group_id)
            & canaries["outcome"].eq("ln_salario_real_adm")
            & canaries["heterogeneity_group_id"].eq("age_22_25")
        ] if not canaries.empty else pd.DataFrame()
        demo_young = demographic[
            demographic["group_id"].eq(spec.group_id)
            & demographic["outcome"].eq("ln_salario_real_adm")
            & demographic["heterogeneity_group_label"].isin(["14-24", "25-34"])
        ] if not demographic.empty else pd.DataFrame()
        main_coef = float(main_wage["coef"].iloc[0]) if not main_wage.empty and pd.notna(main_wage["coef"].iloc[0]) else np.nan
        main_p = float(main_wage["p_value"].iloc[0]) if not main_wage.empty and pd.notna(main_wage["p_value"].iloc[0]) else np.nan
        pre_status = wage_pre["pretrend_status"].iloc[0] if not wage_pre.empty else "not_available"
        youth_signal = False
        if not youth.empty:
            youth_signal = bool(((youth["coef"] < 0) & (youth["p_value"] < 0.10) & youth["pretrend_status"].isin(["pass", "warning"])).any())
        demo_young_signal = False
        if not demo_young.empty:
            demo_young_signal = bool(((demo_young["coef"] < 0) & (demo_young["p_value"] < 0.10) & demo_young["pretrend_status"].isin(["pass", "warning"])).any())
        main_signal = pd.notna(main_coef) and main_coef < 0 and pd.notna(main_p) and main_p < 0.10
        if spec.exploratory_only:
            verdict = "exploratório"
        elif main_signal and pre_status == "pass":
            verdict = "evidência média com pretrend favorável"
        elif youth_signal or demo_young_signal:
            verdict = "evidência concentrada em jovens"
        elif main_signal:
            verdict = "sinal médio com limitação de pretrend"
        else:
            verdict = "sem evidência salarial clara"
        rows.append(
            {
                "group_id": spec.group_id,
                "group_label": spec.label_pt,
                "short_label": spec.short_label_pt,
                "recommended_location": spec.recommended_location_pt,
                "exploratory_only": spec.exploratory_only,
                "main_real_admission_wage_coef": main_coef,
                "main_real_admission_wage_p": main_p,
                "main_wage_pretrend": pre_status,
                "young_canaries_signal": youth_signal,
                "young_project_age_signal": demo_young_signal,
                "verdict": verdict,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "occupation_group_evidence_summary.csv", index=False)
    view = out.assign(
        Grupo=out["group_label"],
        Local=out["recommended_location"],
        CoefSalario=out["main_real_admission_wage_coef"].map(lambda v: fmt_number(v, 4)),
        p=out["main_real_admission_wage_p"].map(_normal_p),
        Pretrend=out["main_wage_pretrend"],
        JovensCanaries=out["young_canaries_signal"].map(_format_bool),
        JovensProjeto=out["young_project_age_signal"].map(_format_bool),
        Veredito=out["verdict"],
        Exploratorio=out["exploratory_only"].map(_format_bool),
    )
    write_markdown_table(
        TABLE_DIR / "occupation_group_evidence_summary.md",
        "Resumo interpretativo dos grupos ocupacionais",
        view,
        ["Grupo", "Local", "CoefSalario", "p", "Pretrend", "JovensCanaries", "JovensProjeto", "Veredito", "Exploratorio"],
        note="CoefSalario refere-se ao efeito médio em salário real de admissão. Heterogeneidade jovem é avaliada separadamente.",
    )
    return out


def _format_signal(data: pd.DataFrame, group_id: str, outcome: str = "ln_salario_real_adm") -> str:
    if data.empty:
        return "sem heterogeneidade estimada."
    subset = data[
        data["group_id"].eq(group_id)
        & data["outcome"].eq(outcome)
        & data["result_status"].eq("estimated")
        & (data["coef"] < 0)
        & (data["p_value"] < 0.10)
    ].copy()
    if subset.empty:
        return "sem sinal negativo com p<0,10."
    subset = subset.sort_values(["p_value", "coef"]).head(5)
    return "; ".join(
        f"{row.heterogeneity_group_label}: {fmt_number(row.coef)}{row.stars} (p={fmt_number(row.p_value, 3)}, pretrend={row.pretrend_status})"
        for row in subset.itertuples()
    )


def write_report(
    summary: pd.DataFrame,
    results: pd.DataFrame,
    pretrends: pd.DataFrame,
    demographic: pd.DataFrame,
    canaries: pd.DataFrame,
    net_flow: pd.DataFrame,
    net_flow_pretrends: pd.DataFrame,
    net_flow_heterogeneity: pd.DataFrame,
    audit: pd.DataFrame,
) -> None:
    software = summary[summary["group_id"].eq("software_it_core")].iloc[0]
    digital = summary[summary["group_id"].eq("digital_it_with_data_entry")].iloc[0]
    official_groups = ", ".join(spec.label_pt for spec in GROUP_SPECS if not spec.exploratory_only)
    exploratory_groups = ", ".join(spec.label_pt for spec in GROUP_SPECS if spec.exploratory_only)
    navigation_table = "| Arquivo | Markdown | CSV |\n| --- | --- | --- |\n" + "\n".join(
        f"| {row.Arquivo} | {row.Markdown} | {row.CSV} |"
        for row in _navigation_rows().itertuples()
    )
    sections = [
        "# Extensão De Grupos Ocupacionais Manuais",
        "## Leitura principal",
        (
            "Esta extensão não substitui o modelo nacional base G1-G4 vs Not Exposed. "
            "Ela testa mecanismos ocupacionais definidos manualmente e sempre reporta heterogeneidade."
        ),
        (
            f"O grupo principal é **Núcleo de Software e TI**. O efeito médio em salário real de admissão é "
            f"{fmt_number(software['main_real_admission_wage_coef'])} "
            f"(p={fmt_number(software['main_real_admission_wage_p'], 3)}, pretrend={software['main_wage_pretrend']}). "
            f"Veredito: {software['verdict']}."
        ),
        (
            "Nas faixas Canaries para Núcleo de Software e TI: "
            f"{_format_signal(canaries, 'software_it_core')}"
        ),
        (
            "Na heterogeneidade demográfica ampla para Núcleo de Software e TI: "
            f"{_format_signal(demographic, 'software_it_core')}"
        ),
        "## Robustez com entrada de dados",
        (
            f"A versão **Ocupações Digitais e de TI com Entrada de Dados** adiciona o CBO 4121. "
            f"O efeito médio em salário real de admissão é {fmt_number(digital['main_real_admission_wage_coef'])} "
            f"(p={fmt_number(digital['main_real_admission_wage_p'], 3)}, pretrend={digital['main_wage_pretrend']}). "
            f"Veredito: {digital['verdict']}."
        ),
        (
            "Sinais salariais jovens nessa robustez: "
            f"{_format_signal(canaries, 'digital_it_with_data_entry')}"
        ),
        "## Triagem dos demais grupos",
        (
            f"Grupos oficiais triados: {official_groups}. "
            f"Grupo exploratório sem MTE: {exploratory_groups}."
        ),
        "A tabela `tables/occupation_group_evidence_summary.md` resume se cada grupo deve ir ao texto principal, apêndice ou auditoria.",
        "## Saldo líquido",
        (
            "O saldo líquido é reportado como complemento de fluxo para todos os grupos estimados. "
            "Ele deve ser lido junto com admissões e demissões separadas."
        ),
        (TABLE_DIR / "occupation_group_net_flow_results.md").read_text(encoding="utf-8")
        if not net_flow.empty
        else "_Sem saldo líquido estimado._",
        "## Pretrends e heterogeneidade do saldo líquido",
        (TABLE_DIR / "occupation_group_net_flow_pretrends.md").read_text(encoding="utf-8")
        if not net_flow_pretrends.empty
        else "_Sem pretrends de saldo líquido._",
        (TABLE_DIR / "occupation_group_net_flow_heterogeneity.md").read_text(encoding="utf-8")
        if not net_flow_heterogeneity.empty
        else "_Sem heterogeneidade de saldo líquido._",
        "## Amostra e auditoria",
        (
            f"A auditoria cobre {audit['cbo_4d'].nunique()} CBOs em grupos manuais. "
            "CBOs sem match MTE são documentados e rotulados como exploratórios."
        ),
        "## Onde estão os arquivos",
        f"Pasta da extensão: `{OUT_DIR.resolve()}`",
        f"Índice navegável: {_link(OUT_DIR / 'README.md', 'README.md')}",
        navigation_table,
    ]
    REPORT_PATH.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def validate_outputs(
    group_ids: list[str],
    results: pd.DataFrame,
    pretrends: pd.DataFrame,
    demographic: pd.DataFrame,
    canaries: pd.DataFrame,
    net_flow: pd.DataFrame,
    net_flow_pretrends: pd.DataFrame,
    net_flow_heterogeneity: pd.DataFrame,
) -> None:
    required_paths = [REPORT_PATH, OUT_DIR / "README.md", TABLE_DIR / "README.md", AUDIT_DIR / "README.md"]
    required_paths.extend(md_path for _label, md_path, _csv_path in MARKDOWN_OUTPUTS)
    for path in required_paths:
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Required output is missing or empty: {path}")
    if "4121" in GROUP_SPEC_BY_ID["software_it_core"].cbo_codes:
        raise RuntimeError("software_it_core must not contain 4121.")
    if "4121" not in GROUP_SPEC_BY_ID["digital_it_with_data_entry"].cbo_codes:
        raise RuntimeError("digital_it_with_data_entry must contain 4121.")
    estimated = set(results.loc[results["result_status"].eq("estimated"), "group_id"].unique())
    for group_id in sorted(estimated):
        if demographic[demographic["group_id"].eq(group_id)].empty:
            raise RuntimeError(f"Missing demographic heterogeneity for estimated group: {group_id}")
        if canaries[canaries["group_id"].eq(group_id)].empty:
            raise RuntimeError(f"Missing Canaries heterogeneity for estimated group: {group_id}")
        if pretrends[pretrends["group_id"].eq(group_id)].empty:
            raise RuntimeError(f"Missing pretrend rows for estimated group: {group_id}")
        if net_flow[net_flow["group_id"].eq(group_id)].empty:
            raise RuntimeError(f"Missing net-flow rows for estimated group: {group_id}")
        if net_flow_pretrends[net_flow_pretrends["group_id"].eq(group_id)].empty:
            raise RuntimeError(f"Missing net-flow pretrend rows for estimated group: {group_id}")
        if net_flow_heterogeneity[net_flow_heterogeneity["group_id"].eq(group_id)].empty:
            raise RuntimeError(f"Missing net-flow heterogeneity for estimated group: {group_id}")


def run() -> None:
    prepare_dirs()
    log("Loading Section 4 panel and classification...")
    panel, classification = load_analysis_data()
    log("Building manual occupation-group audit...")
    audit = build_group_audit(classification, panel)

    log("Building exploratory no-MTE auxiliary panel...")
    auxiliary = build_clear_tech_no_mte_auxiliary_panel(panel, classification)
    if not auxiliary.empty:
        panel = pd.concat([panel, auxiliary], ignore_index=True, sort=False)
    group_ids = [*official_group_ids(), "clear_tech_no_mte"]

    log("Estimating occupation-group main effects and event studies...")
    results, pretrends, coefficients = estimate_group_results(panel, classification, group_ids)
    _write_result_table(results)
    _write_pretrend_table(pretrends)
    plot_event_studies(coefficients)

    log("Clearing cached heterogeneity inputs before mandatory heterogeneity block...")
    aggregate_micro_group_pairs.cache_clear()
    build_pre_treatment_income_groups.cache_clear()
    log("Estimating occupation-group heterogeneity...")
    demographic, canaries = estimate_group_heterogeneity(panel, classification, group_ids)
    write_heterogeneity_tables(demographic, canaries)

    log("Estimating occupation-group net-flow block...")
    net_flow, net_flow_pretrends, net_flow_heterogeneity = estimate_group_net_flow(panel, classification, group_ids)
    write_net_flow_tables(net_flow, net_flow_pretrends, net_flow_heterogeneity)

    log("Writing evidence summary and report...")
    summary = group_evidence_summary(results, pretrends, demographic, canaries)
    write_report(summary, results, pretrends, demographic, canaries, net_flow, net_flow_pretrends, net_flow_heterogeneity, audit)
    write_navigation_files()
    validate_outputs(group_ids, results, pretrends, demographic, canaries, net_flow, net_flow_pretrends, net_flow_heterogeneity)
    log(f"Done. Report written to {REPORT_PATH}")


if __name__ == "__main__":
    run()
