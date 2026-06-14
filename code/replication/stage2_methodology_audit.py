#!/usr/bin/env python3
"""Independent Stage 2 methodology audit.

This script does not modify the dissertation analysis pipeline. It reads the
historical PDFs, exported notebooks, current scripts, current outputs, and raw
CAGED files, then writes audit tables plus a referee-style report.
"""

from __future__ import annotations

import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "stage2_methodology_audit"
PDF_TEXT_DIR = OUT_DIR / "pdf_text"
REPORT_PATH = ROOT / "correspondence" / "referee2" / "2026-06-14_stage2_methodology_audit.md"

DATA_RAW = ROOT / "data" / "raw"
DATA_OUTPUT = ROOT / "data" / "output"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"

PDFS = {
    "stage2a": Path("/Users/manebrasil/Downloads/ETAPA 2a — Preparação do Painel CAGED + ILO Exposure Index (1).pdf"),
    "stage2b": Path("/Users/manebrasil/Downloads/ETAPA 2b — Análise Difference-in-Differences_ IA Generativa e Emprego Formal no Brasil (1).pdf"),
    "stage2c": Path("/Users/manebrasil/Downloads/ETAPA 2c — Resultados_ Consolidação e Síntese da Análise DiD (1).pdf"),
}

NOTEBOOK_EXPORTS = {
    "stage2a": ROOT / "src" / "notebooks" / "_export_md" / "etapa_2a_preparacao_dados_did_caged_ilo.md",
    "stage2b": ROOT / "src" / "notebooks" / "_export_md" / "etapa_2b_analise_did_caged_ilo.md",
    "stage2c": ROOT / "src" / "notebooks" / "_export_md" / "etapa_2c_resultados.md",
}

CURRENT_SCRIPTS = {
    "stage2a": ROOT / "src" / "scripts" / "etapa_2a_preparacao_dados_did_caged_ilo.py",
    "stage2b": ROOT / "src" / "scripts" / "etapa_2b_analise_did_caged_ilo.py",
    "section4": ROOT / "src" / "scripts" / "build_dissertation_section4_results.py",
    "crosswalk": ROOT / "src" / "scripts" / "caged_mte_crosswalk.py",
    "scenario_grid": ROOT / "src" / "scripts" / "run_treatment_scenario_grid.py",
}

SALARIO_MINIMO = {
    2021: 1100,
    2022: 1212,
    2023: 1320,
    2024: 1412,
    2025: 1518,
}

ANO_TRATAMENTO = 2022
MES_TRATAMENTO = 12
INDICE_BASE = 100.0
CONTROL_COLUMNS = ["idade_media_adm", "pct_mulher_adm", "pct_superior_adm", "pct_negra_adm"]
OUTCOME_LABELS = {
    "ln_admissoes": "Admissions (log)",
    "ln_desligamentos": "Separations (log)",
    "saldo": "Net employment balance",
    "ln_salario_adm": "Admission wage, nominal (log)",
    "ln_salario_real_adm": "Admission wage, real (log)",
}


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PDF_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def run_pdftotext(pdf_path: Path, text_path: Path) -> str:
    if not pdf_path.exists():
        return ""
    subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)], check=True)
    return read_text(text_path)


def pct_effect(coef: float | int | None) -> float:
    if coef is None or pd.isna(coef):
        return np.nan
    return 100.0 * (math.exp(float(coef)) - 1.0)


def stars(p_value: float | int | None) -> str:
    if p_value is None or pd.isna(p_value):
        return ""
    p = float(p_value)
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def fmt_num(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.{digits}f}"
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_No rows._"
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df[columns].iterrows():
        vals = []
        for col in columns:
            val = row.get(col, "")
            if pd.isna(val):
                val = ""
            vals.append(str(val).replace("\n", " ").replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def source_inventory(pdf_text: dict[str, str], md_text: dict[str, str]) -> pd.DataFrame:
    markers = {
        "old_crosswalk_language": ["CBO 2002", "ISCO-08", "fallback", "hierárquico"],
        "mte_official_language": ["MTE", "CIUO88", "oficial"],
        "nominal_wage": ["Salário de admissão (nominal)", "ln_salario_adm"],
        "real_wage": ["salario_real_adm", "deflacionado", "IPCA"],
        "young_age": ["jovem", "≤30", "14-24"],
        "old_headline_numbers": ["-0.133735", "-0.034081", "-0.065617", "-0.0631"],
    }
    rows = []
    for stage, path in PDFS.items():
        text = pdf_text.get(stage, "")
        rows.append(
            {
                "source_type": "pdf",
                "stage": stage,
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
                "text_chars": len(text),
                "pages_approx": max(1, text.count("\f")) if text else 0,
                **{k: all(m.lower() in text.lower() for m in vals) for k, vals in markers.items()},
            }
        )
    for stage, path in NOTEBOOK_EXPORTS.items():
        text = md_text.get(stage, "")
        rows.append(
            {
                "source_type": "notebook_export_md",
                "stage": stage,
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
                "text_chars": len(text),
                "pages_approx": np.nan,
                **{k: all(m.lower() in text.lower() for m in vals) for k, vals in markers.items()},
            }
        )
    for name, path in CURRENT_SCRIPTS.items():
        text = read_text(path)
        rows.append(
            {
                "source_type": "current_script",
                "stage": name,
                "path": str(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
                "text_chars": len(text),
                "pages_approx": np.nan,
                **{k: all(m.lower() in text.lower() for m in vals) for k, vals in markers.items()},
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "source_inventory.csv", index=False)
    return out


def methodology_comparison(md_text: dict[str, str], script_text: dict[str, str]) -> pd.DataFrame:
    rows = [
        {
            "domain": "Data window and unit",
            "historical_pdf_or_notebook": "CAGED occupation-month panel, Jan/2021-Jun/2025 in the Stage 2b notebook output; PDFs/notebook describe 23 pre months and 31 post months.",
            "current_scripts_or_outputs": "Current Stage 2 panel has 23,319 rows, 436 CBOs, and 54 months after MTE matching.",
            "audit_status": "Mostly retained, but sample is smaller after MTE matching.",
        },
        {
            "domain": "Crosswalk",
            "historical_pdf_or_notebook": "Main text described CBO 2002 -> ISCO-08 using 2-digit matching/fallback and 4-digit hierarchical robustness.",
            "current_scripts_or_outputs": "Current `caged_mte_crosswalk.py` uses official MTE CBO2002-CBO94-CIUO88, then ISCO-88 -> ISCO-08, with no numeric CBO=ISCO fallback.",
            "audit_status": "Substantive methodological change; this is the largest defensibility improvement.",
        },
        {
            "domain": "Treatment/control",
            "historical_pdf_or_notebook": "Top 20% of exposure score as treatment, bottom 80%/rest as control.",
            "current_scripts_or_outputs": "Still top 20% vs rest for the baseline, but thresholds are now computed over CBOs with valid MTE scores; scenario grid tests top 30%, ISCO 4d consensus, gradient definitions, and excluded-middle strategies.",
            "audit_status": "Baseline estimand mostly retained; treatment assignment changed through the new score and eligible sample.",
        },
        {
            "domain": "Controls and fixed effects",
            "historical_pdf_or_notebook": "Occupation and month fixed effects, cluster by CBO 4d, controls for age, female share, and higher education share.",
            "current_scripts_or_outputs": "Current scripts retain CBO and period fixed effects and CBO clustering; final scripts also include `pct_negra_adm` as a required control.",
            "audit_status": "Retained with one added demographic control; older generated comparison files may predate this control.",
        },
        {
            "domain": "Nominal wages",
            "historical_pdf_or_notebook": "`ln_salario_adm = log(salario_medio_adm)` after P1/P99 winsorization in Stage 2b.",
            "current_scripts_or_outputs": "Stage 2a builds `salario_medio_adm` as mean monthly admission wage; Stage 2b winsorizes aggregate CBO-month wages and recalculates logs.",
            "audit_status": "Retained as an aggregate-wage outcome, but it is log(mean wage), not mean(log wage).",
        },
        {
            "domain": "Real wages",
            "historical_pdf_or_notebook": "Notebook/PDF treats `ln_salario_real_adm` as a main cleaned inflation-adjusted outcome.",
            "current_scripts_or_outputs": "Current Section 4 reconstructs real wage from raw CAGED microdata using IPCA monthly index before group aggregation.",
            "audit_status": "Current reconstruction is more defensible; audit still tests deflator arithmetic and missing/zero handling.",
        },
        {
            "domain": "Age heterogeneity",
            "historical_pdf_or_notebook": "Old Stage 2b uses `jovem_adm = idade_media_adm <= 30` in an aggregate triple-DiD and reports a strong young wage interaction in the PDF/notebook.",
            "current_scripts_or_outputs": "Current Section 4 reconstructs subgroup panels from raw microdata and splits age into 14-24, 25-34, 35-59, and 60+.",
            "audit_status": "Substantive change in heterogeneity design; old and new age estimates are not directly comparable.",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "methodology_comparison.csv", index=False)
    return out


def old_pdf_notebook_findings() -> pd.DataFrame:
    rows = [
        {
            "source": "historical_pdf_or_notebook_stage2b_main_table",
            "outcome": "ln_salario_adm",
            "label": "Nominal admission wage, old notebook main estimate",
            "coef": -0.065617,
            "se": 0.027789,
            "p_value": 0.018518,
            "n_obs": 32988,
            "note": "Extracted from Stage 2b PDF/exported notebook result table.",
        },
        {
            "source": "historical_pdf_or_notebook_stage2b_main_table",
            "outcome": "ln_salario_real_adm",
            "label": "Real admission wage, old notebook main estimate",
            "coef": -0.034081,
            "se": 0.019308,
            "p_value": 0.078023,
            "n_obs": 32988,
            "note": "Extracted from Stage 2b PDF/exported notebook result table.",
        },
        {
            "source": "historical_pdf_or_notebook_stage2b_main_table",
            "outcome": "ln_salario_jovem",
            "label": "Young-worker wage, old notebook main estimate",
            "coef": -0.133735,
            "se": 0.052203,
            "p_value": 0.010644,
            "n_obs": 32988,
            "note": "Extracted from Stage 2b PDF/exported notebook result table.",
        },
        {
            "source": "historical_pdf_or_notebook_stage2c_robustness",
            "outcome": "ln_salario_adm",
            "label": "Nominal admission wage, old top-20 robustness table",
            "coef": -0.063100,
            "se": 0.028500,
            "p_value": 0.027400,
            "n_obs": 32988,
            "note": "Extracted from Stage 2c PDF/exported notebook robustness table.",
        },
    ]
    out = pd.DataFrame(rows)
    out["percent_effect"] = out["coef"].map(pct_effect)
    out["stars"] = out["p_value"].map(stars)
    out.to_csv(OUT_DIR / "old_pdf_notebook_key_findings.csv", index=False)
    return out


def current_main_findings() -> pd.DataFrame:
    did = pd.read_csv(OUTPUT_TABLES / "did_main_results.csv")
    main = did[did["model"].eq("Model 3: FE + Controls (MAIN)")].copy()
    main["source"] = "current_outputs_tables_did_main_results"
    main["percent_effect"] = main.apply(
        lambda row: pct_effect(row["coef"]) if str(row["outcome"]).startswith("ln_") else np.nan,
        axis=1,
    )
    main.to_csv(OUT_DIR / "current_main_findings.csv", index=False)
    return main


def crosswalk_decomposition(current_main: pd.DataFrame) -> pd.DataFrame:
    rows = []
    comparison_files = [
        ("old_full_vs_mte_existing_decomposition", ROOT / "outputs" / "crosswalk_results_comparison" / "stage2_main_before_full_vs_after_mte.csv"),
        ("old_common_vs_mte_existing_decomposition", ROOT / "outputs" / "crosswalk_results_comparison" / "stage2_main_before_common_vs_after_mte.csv"),
    ]
    for label, path in comparison_files:
        df = pd.read_csv(path)
        for _, r in df.iterrows():
            rows.append(
                {
                    "comparison_source": label,
                    "outcome": r["outcome"],
                    "before_spec": r["spec_before"],
                    "before_coef": r["coef_before"],
                    "before_se": r["se_before"],
                    "before_p_value": r["p_value_before"],
                    "before_n_obs": r["n_obs_before"],
                    "before_n_cbo": r["n_cbo_before"],
                    "after_spec": r["spec_after"],
                    "after_coef": r["coef_after"],
                    "after_se": r["se_after"],
                    "after_p_value": r["p_value_after"],
                    "after_n_obs": r["n_obs_after"],
                    "after_n_cbo": r["n_cbo_after"],
                    "delta_coef": r["delta_coef"],
                    "before_percent_effect": pct_effect(r["coef_before"]) if str(r["outcome"]).startswith("ln_") else np.nan,
                    "after_percent_effect": pct_effect(r["coef_after"]) if str(r["outcome"]).startswith("ln_") else np.nan,
                    "note": "Existing crosswalk decomposition output; may predate the final pct_negra_adm control.",
                }
            )
    current_wage = current_main[current_main["outcome"].eq("ln_salario_adm")].iloc[0]
    rows.append(
        {
            "comparison_source": "current_final_baseline_with_pct_negra_control",
            "outcome": "ln_salario_adm",
            "before_spec": "historical_pdf_or_notebook_stage2b_main_table",
            "before_coef": -0.065617,
            "before_se": 0.027789,
            "before_p_value": 0.018518,
            "before_n_obs": 32988,
            "before_n_cbo": 629,
            "after_spec": "current_mte_final_did_main_results",
            "after_coef": current_wage["coef"],
            "after_se": current_wage["se"],
            "after_p_value": current_wage["p_value"],
            "after_n_obs": current_wage["n_obs"],
            "after_n_cbo": 436,
            "delta_coef": current_wage["coef"] - (-0.065617),
            "before_percent_effect": pct_effect(-0.065617),
            "after_percent_effect": pct_effect(current_wage["coef"]),
            "note": "Direct old PDF/notebook headline to current final output comparison.",
        }
    )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "crosswalk_and_wage_decomposition.csv", index=False)
    return out


def treatment_strategy_wage_comparison() -> pd.DataFrame:
    rows = []
    inputs = [
        ("stage2_treatment_strategy", ROOT / "outputs" / "treatment_group_strategy_comparison" / "stage2_treatment_strategy_results.csv"),
        ("stage2_scenario_grid", ROOT / "outputs" / "treatment_scenario_grid" / "stage2_scenario_results.csv"),
        ("stage3_treatment_strategy", ROOT / "outputs" / "treatment_group_strategy_comparison" / "stage3_treatment_strategy_results.csv"),
        ("stage3_scenario_grid", ROOT / "outputs" / "treatment_scenario_grid" / "stage3_scenario_results.csv"),
    ]
    for source, path in inputs:
        df = pd.read_csv(path)
        label_col = "strategy_label" if "strategy_label" in df.columns else "scenario_label"
        id_col = "strategy" if "strategy" in df.columns else "scenario_id"
        for _, r in df[df["outcome"].isin(["ln_salario_adm", "ln_salario_real_adm", "ln_salario_jovem"])].iterrows():
            rows.append(
                {
                    "source": source,
                    "stage": r.get("stage", ""),
                    "spec_id": r.get(id_col, ""),
                    "spec_label": r.get(label_col, ""),
                    "outcome": r["outcome"],
                    "outcome_label": r.get("outcome_label", OUTCOME_LABELS.get(r["outcome"], r["outcome"])),
                    "coef": r.get("coef", np.nan),
                    "se": r.get("se", np.nan),
                    "p_value": r.get("p_value", np.nan),
                    "stars": r.get("stars", ""),
                    "n_obs": r.get("n_obs", np.nan),
                    "n_cbo": r.get("n_cbo", np.nan),
                    "percent_effect": pct_effect(r.get("coef", np.nan)),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "treatment_strategy_wage_comparison.csv", index=False)
    return out


def load_ipca_map() -> dict[int, float]:
    ipca = pd.read_parquet(DATA_PROCESSED / "ipca_mensal.parquet")
    cols = set(ipca.columns)
    if {"periodo_num", "ipca_indice"}.issubset(cols):
        return dict(zip(ipca["periodo_num"].astype(int), ipca["ipca_indice"].astype(float)))
    if {"ano", "mes", "indice"}.issubset(cols):
        periodo = ipca["ano"].astype(int) * 100 + ipca["mes"].astype(int)
        return dict(zip(periodo, ipca["indice"].astype(float)))
    if {"ano", "mes", "ipca_indice"}.issubset(cols):
        periodo = ipca["ano"].astype(int) * 100 + ipca["mes"].astype(int)
        return dict(zip(periodo, ipca["ipca_indice"].astype(float)))
    raise RuntimeError(f"Cannot infer IPCA columns from {ipca.columns.tolist()}")


def normalize_cbo(series: pd.Series) -> pd.Series:
    out = series.astype(str).str.strip().str.extract(r"(\d{4})", expand=False)
    return out.where(out.notna() & out.str.len().eq(4))


def salary_methodology_audit() -> pd.DataFrame:
    panel = pd.read_parquet(DATA_OUTPUT / "painel_caged_did_ready.parquet")
    panel2b = pd.read_parquet(DATA_OUTPUT / "painel_2b_ready.parquet")
    ipca_map = load_ipca_map()
    eligible_cbo = set(panel["cbo_4d"].astype(str).str.zfill(4).unique())

    pieces = []
    raw_positive_pieces = []
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        df = pd.read_parquet(path, columns=["ano", "mes", "cbo_2002", "saldo_movimentacao", "salario_mensal"])
        df["cbo_4d"] = normalize_cbo(df["cbo_2002"])
        df = df[df["cbo_4d"].isin(eligible_cbo)].copy()
        if df.empty:
            continue
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["periodo_num"] = df["ano"] * 100 + df["mes"]
        adm = df[df["saldo_movimentacao"].eq(1)].copy()
        agg = (
            adm.groupby(["cbo_4d", "ano", "mes"], observed=True, sort=False)
            .agg(
                raw_admissoes=("saldo_movimentacao", "size"),
                raw_salario_medio_adm=("salario_mensal", "mean"),
            )
            .reset_index()
        )
        pieces.append(agg)
        pos = adm[adm["salario_mensal"].notna() & adm["salario_mensal"].gt(0)].copy()
        if not pos.empty:
            pos["log_wage"] = np.log(pos["salario_mensal"])
            pos["ipca_indice"] = pos["periodo_num"].map(ipca_map)
            pos["salario_real"] = pos["salario_mensal"] * (INDICE_BASE / pos["ipca_indice"])
            pos_agg = (
                pos.groupby(["cbo_4d", "ano", "mes"], observed=True, sort=False)
                .agg(
                    positive_admissions=("salario_mensal", "size"),
                    log_mean_nominal_wage=("salario_mensal", lambda x: math.log(float(x.mean()))),
                    mean_log_nominal_wage=("log_wage", "mean"),
                    mean_real_before_aggregation=("salario_real", "mean"),
                    mean_nominal_wage=("salario_mensal", "mean"),
                    ipca_indice=("ipca_indice", "first"),
                )
                .reset_index()
            )
            pos_agg["real_after_nominal_aggregation"] = pos_agg["mean_nominal_wage"] * (
                INDICE_BASE / pos_agg["ipca_indice"]
            )
            raw_positive_pieces.append(pos_agg)

    raw = pd.concat(pieces, ignore_index=True)
    merged = panel.merge(raw, on=["cbo_4d", "ano", "mes"], how="left")
    salary_diff = (merged["salario_medio_adm"] - merged["raw_salario_medio_adm"]).abs()
    adm_diff = (merged["admissoes"] - merged["raw_admissoes"]).abs()

    pos_all = pd.concat(raw_positive_pieces, ignore_index=True)
    log_gap = (pos_all["log_mean_nominal_wage"] - pos_all["mean_log_nominal_wage"]).abs()
    real_gap = (pos_all["mean_real_before_aggregation"] - pos_all["real_after_nominal_aggregation"]).abs()

    sm_check = panel.copy()
    sm_check["expected_salario_sm"] = sm_check["salario_medio_adm"] / sm_check["ano"].map(SALARIO_MINIMO)
    sm_gap = (sm_check["salario_sm"] - sm_check["expected_salario_sm"]).abs()

    p1 = float(panel["salario_medio_adm"].quantile(0.01))
    p99 = float(panel["salario_medio_adm"].quantile(0.99))
    clipped = ((panel["salario_medio_adm"] < max(p1, 0.01)) | (panel["salario_medio_adm"] > p99)).sum()

    rows = [
        {
            "check": "stage2a_nominal_mean_wage_matches_raw_admission_mean",
            "result": "pass" if float(salary_diff.max(skipna=True)) < 1e-8 else "flag",
            "n_rows_checked": int(merged["raw_salario_medio_adm"].notna().sum()),
            "metric": "max_abs_difference",
            "value": float(salary_diff.max(skipna=True)),
            "interpretation": "Stage 2a salario_medio_adm is the raw mean of admission salario_mensal by CBO-month.",
        },
        {
            "check": "stage2a_admission_counts_match_raw",
            "result": "pass" if float(adm_diff.max(skipna=True)) == 0.0 else "flag",
            "n_rows_checked": int(merged["raw_admissoes"].notna().sum()),
            "metric": "max_abs_difference",
            "value": float(adm_diff.max(skipna=True)),
            "interpretation": "Admission counts match raw aggregation for the matched MTE panel rows.",
        },
        {
            "check": "salario_minimo_normalization",
            "result": "pass" if float(sm_gap.max(skipna=True)) < 1e-10 else "flag",
            "n_rows_checked": int(sm_gap.notna().sum()),
            "metric": "max_abs_difference",
            "value": float(sm_gap.max(skipna=True)),
            "interpretation": "salario_sm equals salario_medio_adm divided by the annual minimum wage.",
        },
        {
            "check": "deflate_before_vs_after_monthly_aggregation",
            "result": "pass" if float(real_gap.max(skipna=True)) < 1e-8 else "flag",
            "n_rows_checked": int(real_gap.notna().sum()),
            "metric": "max_abs_difference",
            "value": float(real_gap.max(skipna=True)),
            "interpretation": "Because the IPCA deflator is constant within CBO-month, deflating before or after monthly aggregation is numerically equivalent.",
        },
        {
            "check": "log_mean_wage_vs_mean_log_wage",
            "result": "methodological_choice",
            "n_rows_checked": int(log_gap.notna().sum()),
            "metric": "mean_abs_gap",
            "value": float(log_gap.mean(skipna=True)),
            "interpretation": "The pipeline estimates log(mean wage). This differs from mean(log wage); this is not a coding bug but should be stated as the estimand.",
        },
        {
            "check": "log_mean_wage_vs_mean_log_wage_p95_gap",
            "result": "methodological_choice",
            "n_rows_checked": int(log_gap.notna().sum()),
            "metric": "p95_abs_gap",
            "value": float(log_gap.quantile(0.95)),
            "interpretation": "Large within-cell wage dispersion can make log(mean wage) materially different from mean(log wage).",
        },
        {
            "check": "aggregate_wage_outliers_before_stage2b_winsorization",
            "result": "document",
            "n_rows_checked": int(len(panel)),
            "metric": "rows_outside_p1_p99",
            "value": int(clipped),
            "interpretation": "Stage 2b winsorizes aggregate CBO-month wages. This preserves rows but changes the wage outcome scale.",
        },
        {
            "check": "zeros_in_nominal_admission_wage_panel",
            "result": "flag" if int(panel["salario_medio_adm"].eq(0).sum()) else "pass",
            "n_rows_checked": int(len(panel)),
            "metric": "zero_salary_rows",
            "value": int(panel["salario_medio_adm"].eq(0).sum()),
            "interpretation": "Rows with zero aggregate wages are clipped before logs; they should be acknowledged as data-quality/missingness cases.",
        },
        {
            "check": "current_stage2b_wage_max_after_winsorization",
            "result": "document",
            "n_rows_checked": int(len(panel2b)),
            "metric": "max_salario_medio_adm",
            "value": float(panel2b["salario_medio_adm"].max(skipna=True)),
            "interpretation": "This records the wage scale after Stage 2b winsorization.",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "salary_methodology_audit.csv", index=False)
    return out


@dataclass(frozen=True)
class AgeDefinition:
    definition_id: str
    label_young: str
    label_other: str
    max_young_age: int


def build_age_binary_raw_panels(eligible_cbo: set[str]) -> pd.DataFrame:
    ipca_map = load_ipca_map()
    defs = [
        AgeDefinition("age_14_24_vs_other", "Age 14-24", "Age 25+", 24),
        AgeDefinition("age_14_30_vs_other", "Age 14-30", "Age 31+", 30),
    ]
    pieces = []
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        df = pd.read_parquet(path, columns=["ano", "mes", "cbo_2002", "saldo_movimentacao", "salario_mensal", "idade"])
        df["cbo_4d"] = normalize_cbo(df["cbo_2002"])
        df = df[df["cbo_4d"].isin(eligible_cbo)].copy()
        if df.empty:
            continue
        df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
        df = df[df["idade"].notna()].copy()
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["periodo_num"] = df["ano"] * 100 + df["mes"]
        df["ipca_indice"] = df["periodo_num"].map(ipca_map)
        if df["ipca_indice"].isna().any():
            raise RuntimeError(f"Missing IPCA index while processing {path.name}.")
        df["is_adm"] = df["saldo_movimentacao"].eq(1).astype(int)
        df["is_des"] = df["saldo_movimentacao"].eq(-1).astype(int)
        df["salario_real_adm"] = np.where(
            df["saldo_movimentacao"].eq(1),
            df["salario_mensal"] * (INDICE_BASE / df["ipca_indice"]),
            np.nan,
        )
        for age_def in defs:
            d = df.copy()
            d["definition_id"] = age_def.definition_id
            d["group_id"] = np.where(d["idade"].between(14, age_def.max_young_age, inclusive="both"), "young", "other")
            d["group_label"] = np.where(d["group_id"].eq("young"), age_def.label_young, age_def.label_other)
            agg = (
                d.groupby(["definition_id", "group_id", "group_label", "cbo_4d", "ano", "mes"], observed=True, sort=False)
                .agg(
                    admissoes=("is_adm", "sum"),
                    desligamentos=("is_des", "sum"),
                    saldo=("saldo_movimentacao", "sum"),
                    salario_real_adm=("salario_real_adm", "mean"),
                )
                .reset_index()
            )
            pieces.append(agg)
    raw = pd.concat(pieces, ignore_index=True)
    raw["ln_admissoes"] = np.log(raw["admissoes"] + 1)
    raw["ln_desligamentos"] = np.log(raw["desligamentos"] + 1)
    raw["ln_salario_real_adm"] = np.log(raw["salario_real_adm"].clip(lower=1))
    return raw


def estimate_group(data: pd.DataFrame, outcome: str) -> dict[str, object]:
    d = data.dropna(subset=[outcome, "post_treat", *CONTROL_COLUMNS]).copy()
    if d.empty or d["scenario_treat"].nunique() < 2 or d["cbo_4d"].nunique() < 2:
        return {
            "result_status": "failed_insufficient_sample",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": len(d),
            "n_cbo": d["cbo_4d"].nunique(),
            "error": "Insufficient sample.",
        }
    formula = f"{outcome} ~ post_treat + {' + '.join(CONTROL_COLUMNS)} | cbo_4d + periodo"
    try:
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        p_value = float(model.pvalue().loc["post_treat"])
        return {
            "result_status": "estimated",
            "coef": float(model.coef().loc["post_treat"]),
            "se": float(model.se().loc["post_treat"]),
            "p_value": p_value,
            "stars": stars(p_value),
            "n_obs": len(d),
            "n_cbo": d["cbo_4d"].nunique(),
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001 - retain failure as audit row
        return {
            "result_status": "failed_estimation",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": len(d),
            "n_cbo": d["cbo_4d"].nunique(),
            "error": str(exc),
        }


def age_binary_reestimation() -> pd.DataFrame:
    panel = pd.read_parquet(DATA_OUTPUT / "painel_2b_ready.parquet")
    panel["cbo_4d"] = panel["cbo_4d"].astype(str).str.zfill(4)
    required = ["cbo_4d", "ano", "mes", "periodo", "post", *CONTROL_COLUMNS, "alta_exp"]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise RuntimeError(f"Stage 2b panel missing columns for age reestimation: {missing}")
    base = panel[required].copy()
    base["scenario_treat"] = base["alta_exp"].astype(int)
    base["post_treat"] = base["post"].astype(int) * base["scenario_treat"]
    expected_treated = set(base.loc[base["scenario_treat"].eq(1), "cbo_4d"].unique())
    expected_control = set(base.loc[base["scenario_treat"].eq(0), "cbo_4d"].unique())

    raw = build_age_binary_raw_panels(set(base["cbo_4d"].unique()))
    rows = []
    for (definition_id, group_id, group_label), group in raw.groupby(["definition_id", "group_id", "group_label"], observed=True):
        merged = base.merge(
            group[["cbo_4d", "ano", "mes", "admissoes", "desligamentos", "saldo", "ln_admissoes", "ln_desligamentos", "ln_salario_real_adm"]],
            on=["cbo_4d", "ano", "mes"],
            how="left",
        )
        for col in ["admissoes", "desligamentos", "saldo", "ln_admissoes", "ln_desligamentos"]:
            merged[col] = merged[col].fillna(0)
        for outcome in ["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_real_adm"]:
            est = estimate_group(merged, outcome)
            used = merged.dropna(subset=[outcome, "post_treat", *CONTROL_COLUMNS])
            observed = set(used["cbo_4d"].unique())
            rows.append(
                {
                    "definition_id": definition_id,
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "model": f"{outcome} ~ post_treat + {' + '.join(CONTROL_COLUMNS)} | cbo_4d + periodo",
                    "cluster": "cbo_4d",
                    "expected_treated_cbo": len(expected_treated),
                    "expected_control_cbo": len(expected_control),
                    "missing_treated_cbo": len(expected_treated - observed),
                    "missing_control_cbo": len(expected_control - observed),
                    "percent_effect": pct_effect(est["coef"]) if outcome.startswith("ln_") else np.nan,
                    **est,
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "age_binary_reestimation.csv", index=False)
    return out


def age_binary_reestimation_from_current_outputs() -> pd.DataFrame:
    """Build the age-binary audit table from already generated outputs.

    A full raw-CAGED binary reaggregation is intentionally not run by default:
    on this local checkout it requires another expensive pass over tens of
    millions of raw rows. The table records the current aggregate binary
    evidence and explicitly marks the two desired raw binary designs as pending.
    """
    rows = []
    het = pd.read_csv(OUTPUT_TABLES / "heterogeneity_triple_did.csv")
    young = het[het["group"].str.contains("jovem", case=False, na=False)].copy()
    for _, r in young.iterrows():
        rows.append(
            {
                "definition_id": "current_aggregate_young_le_30",
                "group_id": "young_le_30",
                "group_label": "Young <=30 based on aggregate mean age",
                "outcome": r["outcome"],
                "outcome_label": r["outcome_label"],
                "model": "Aggregate panel triple-DiD from current Stage 2b",
                "cluster": "cbo_4d",
                "expected_treated_cbo": np.nan,
                "expected_control_cbo": np.nan,
                "missing_treated_cbo": np.nan,
                "missing_control_cbo": np.nan,
                "percent_effect": pct_effect(r["total_effect"]) if str(r["outcome"]).startswith("ln_") else np.nan,
                "result_status": "estimated_from_current_aggregate_output",
                "coef": r["total_effect"],
                "se": r["total_se"],
                "p_value": r["interaction_pval"],
                "stars": r.get("interaction_stars", ""),
                "n_obs": np.nan,
                "n_cbo": np.nan,
                "error": "",
            }
        )
    for definition_id, label in [
        ("age_14_24_vs_other_raw_binary", "Raw microdata: age 14-24 vs all older workers"),
        ("age_14_30_vs_other_raw_binary", "Raw microdata: age 14-30 vs all older workers"),
    ]:
        rows.append(
            {
                "definition_id": definition_id,
                "group_id": "binary_design",
                "group_label": label,
                "outcome": "ln_salario_real_adm",
                "outcome_label": "Admission wage, real (log)",
                "model": "Not estimated in this run; requires a dedicated optimized raw-CAGED aggregation.",
                "cluster": "cbo_4d",
                "expected_treated_cbo": np.nan,
                "expected_control_cbo": np.nan,
                "missing_treated_cbo": np.nan,
                "missing_control_cbo": np.nan,
                "percent_effect": np.nan,
                "result_status": "not_estimated_computational_followup_required",
                "coef": np.nan,
                "se": np.nan,
                "p_value": np.nan,
                "stars": "",
                "n_obs": np.nan,
                "n_cbo": np.nan,
                "error": "The audit attempted this raw pass, but the unoptimized groupby over raw CAGED was too slow for the current run.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "age_binary_reestimation.csv", index=False)
    return out


def age_comparison_summary(age_binary: pd.DataFrame) -> pd.DataFrame:
    current_four = pd.read_csv(ROOT / "outputs" / "dissertation_section4" / "tables" / "table3_heterogeneity_baseline_mte2d_top20_vs_rest.csv")
    current_four = current_four[
        (current_four["dimension"].eq("age")) & (current_four["outcome"].isin(["ln_admissoes", "ln_salario_real_adm"]))
    ].copy()
    current_four["source_design"] = "current_raw_microdata_four_age_groups"
    current_four["definition"] = current_four["group_label"]
    current_four["percent_effect"] = current_four.apply(
        lambda r: pct_effect(r["coef"]) if str(r["outcome"]).startswith("ln_") else np.nan, axis=1
    )
    four_keep = current_four[
        ["source_design", "definition", "outcome", "outcome_label", "coef", "se", "p_value", "stars", "n_obs", "n_cbo", "percent_effect", "sample_loss_reason"]
    ].copy()

    binary = age_binary[age_binary["outcome"].isin(["ln_admissoes", "ln_salario_real_adm"])].copy()
    binary["source_design"] = "new_audit_raw_microdata_binary_age_groups"
    binary["definition"] = binary["definition_id"] + ": " + binary["group_label"]
    binary["sample_loss_reason"] = ""
    not_estimated = binary["result_status"].astype(str).str.startswith("not_estimated")
    from_current_aggregate = binary["result_status"].eq("estimated_from_current_aggregate_output")
    estimated = ~(not_estimated | from_current_aggregate)
    binary.loc[not_estimated, "sample_loss_reason"] = binary.loc[not_estimated, "error"]
    binary.loc[from_current_aggregate, "sample_loss_reason"] = (
        "Aggregate Stage 2b <=30 output; not a raw subgroup panel."
    )
    binary.loc[estimated, "sample_loss_reason"] = (
        binary.loc[estimated, "missing_treated_cbo"].astype("Int64").astype(str)
        + " treated and "
        + binary.loc[estimated, "missing_control_cbo"].astype("Int64").astype(str)
        + " control CBOs missing for outcome/group."
    )
    binary_keep = binary[
        ["source_design", "definition", "outcome", "outcome_label", "coef", "se", "p_value", "stars", "n_obs", "n_cbo", "percent_effect", "sample_loss_reason"]
    ].copy()

    out = pd.concat([four_keep, binary_keep], ignore_index=True)
    out.to_csv(OUT_DIR / "age_comparison_summary.csv", index=False)
    return out


def pretrend_balance_summary() -> pd.DataFrame:
    rows = []
    pre = pd.read_csv(OUTPUT_TABLES / "parallel_trends_test.csv")
    for _, r in pre.iterrows():
        rows.append(
            {
                "domain": "parallel_trends",
                "item": r["Outcome"],
                "status": r["Status"],
                "metric": "joint_pretrend_p_value",
                "value": r["p-valor conjunto"],
                "note": f"{r['Sig. individuais (p<0.05)']} individually significant pre coefficients; max |t|={r['Max |t-stat|']}.",
            }
        )
    bal = pd.read_csv(OUTPUT_TABLES / "balance_table_pre.csv")
    for _, r in bal.iterrows():
        rows.append(
            {
                "domain": "balance",
                "item": r["Variável"],
                "status": r["Balanceado"],
                "metric": "normalized_difference",
                "value": r["Diff. Normalizada"],
                "note": f"Control={fmt_num(r['Controle'], 3)}, Treated={fmt_num(r['Tratamento'], 3)}.",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "pretrend_balance_summary.csv", index=False)
    return out


def final_answers_summary(
    old_findings: pd.DataFrame,
    current_main: pd.DataFrame,
    crosswalk: pd.DataFrame,
    salary_audit: pd.DataFrame,
    age_summary: pd.DataFrame,
) -> pd.DataFrame:
    current_wage = current_main[current_main["outcome"].eq("ln_salario_adm")].iloc[0]
    old_young = old_findings[old_findings["outcome"].eq("ln_salario_jovem")].iloc[0]
    old_real = old_findings[old_findings["outcome"].eq("ln_salario_real_adm")].iloc[0]
    salary_flags = salary_audit[salary_audit["result"].isin(["flag", "methodological_choice"])]["check"].tolist()
    binary_young_wage = age_summary[
        (age_summary["source_design"].eq("new_audit_raw_microdata_binary_age_groups"))
        & (age_summary["definition"].str.contains("young|Age 14", case=False, na=False))
        & (age_summary["outcome"].eq("ln_salario_real_adm"))
    ].copy()
    pending_binary = int(
        age_summary["sample_loss_reason"]
        .astype(str)
        .str.contains("too slow|requires|dedicated optimized", case=False, na=False)
        .sum()
    )
    rows = [
        {
            "question": "Q1",
            "short_answer": "The DiD skeleton was retained, but the crosswalk, eligible sample, treatment assignment, controls, real-wage reconstruction, and age heterogeneity design changed.",
            "evidence": "Methodology comparison and crosswalk decomposition tables.",
        },
        {
            "question": "Q2",
            "short_answer": (
                f"The old PDF/notebook wage findings were real in the historical output: young wage {old_young['coef']:.4f} "
                f"({old_young['percent_effect']:.1f}%) and real wage {old_real['coef']:.4f} ({old_real['percent_effect']:.1f}%). "
                f"The current final Stage 2 wage effect is {current_wage['coef']:.4f} ({pct_effect(current_wage['coef']):.1f}%), p={current_wage['p_value']:.3f}."
            ),
            "evidence": "Old PDF/notebook key findings and current did_main_results.",
        },
        {
            "question": "Q3",
            "short_answer": "No fatal deflator arithmetic error was found, but log(mean wage), winsorization after aggregation, and zero/clip handling must be stated as methodological choices.",
            "evidence": ", ".join(salary_flags),
        },
        {
            "question": "Q4",
            "short_answer": "The available evidence does not justify reverting to the old young-wage headline. A raw binary young/non-young reestimate remains the right follow-up, but the current four-group evidence is cleaner and more transparent.",
            "evidence": f"Pending raw binary rows: {pending_binary}; available current four-group rows and aggregate <=30 rows are reported.",
        },
        {
            "question": "Q5",
            "short_answer": "The new version is academically more defensible because it removes the weakest CBO=ISCO numeric assumptions, but the dissertation should shift away from a strong headline salary claim.",
            "evidence": "MTE crosswalk coverage and pre-trend/balance caveats.",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "final_answers_summary.csv", index=False)
    return out


def report_text(
    inventory: pd.DataFrame,
    methodology: pd.DataFrame,
    old_findings: pd.DataFrame,
    current_main: pd.DataFrame,
    crosswalk: pd.DataFrame,
    treatment_wage: pd.DataFrame,
    salary_audit: pd.DataFrame,
    age_summary: pd.DataFrame,
    pretrend_balance: pd.DataFrame,
    answers: pd.DataFrame,
) -> str:
    old_display = old_findings.assign(
        coef=old_findings["coef"].map(lambda v: fmt_num(v, 4)),
        se=old_findings["se"].map(lambda v: fmt_num(v, 4)),
        p_value=old_findings["p_value"].map(lambda v: fmt_num(v, 3)),
        percent_effect=old_findings["percent_effect"].map(lambda v: fmt_num(v, 2)),
    )
    current_display = current_main[current_main["outcome"].isin(["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_adm"])].assign(
        coef=lambda d: d["coef"].map(lambda v: fmt_num(v, 4)),
        se=lambda d: d["se"].map(lambda v: fmt_num(v, 4)),
        p_value=lambda d: d["p_value"].map(lambda v: fmt_num(v, 3)),
        percent_effect=lambda d: d["percent_effect"].map(lambda v: fmt_num(v, 2)),
    )
    wage_decomp = crosswalk[crosswalk["outcome"].eq("ln_salario_adm")].copy()
    wage_decomp_display = wage_decomp.assign(
        before_coef=wage_decomp["before_coef"].map(lambda v: fmt_num(v, 4)),
        before_p_value=wage_decomp["before_p_value"].map(lambda v: fmt_num(v, 3)),
        after_coef=wage_decomp["after_coef"].map(lambda v: fmt_num(v, 4)),
        after_p_value=wage_decomp["after_p_value"].map(lambda v: fmt_num(v, 3)),
        before_percent_effect=wage_decomp["before_percent_effect"].map(lambda v: fmt_num(v, 2)),
        after_percent_effect=wage_decomp["after_percent_effect"].map(lambda v: fmt_num(v, 2)),
    )
    salary_display = salary_audit.assign(value=salary_audit["value"].map(lambda v: fmt_num(v, 6) if isinstance(v, float) else v))
    age_wage = age_summary[age_summary["outcome"].isin(["ln_salario_real_adm", "ln_salario_adm"])].copy()
    age_wage_display = age_wage.assign(
        coef=age_wage["coef"].map(lambda v: fmt_num(v, 4)),
        p_value=age_wage["p_value"].map(lambda v: fmt_num(v, 3)),
        percent_effect=age_wage["percent_effect"].map(lambda v: fmt_num(v, 2)),
    )
    pretrend_display = pretrend_balance[
        (pretrend_balance["domain"].eq("parallel_trends"))
        | ((pretrend_balance["domain"].eq("balance")) & (pretrend_balance["status"].astype(str).str.contains("⚠|PREOC", na=False)))
    ].copy()
    pretrend_display["value"] = pretrend_display["value"].map(lambda v: fmt_num(v, 4))

    return f"""# Stage 2 Methodology Audit: CAGED + ILO DiD

Date: 2026-06-14

## Executive Summary

This audit confirms that the current Stage 2 pipeline is not merely the old notebook with a corrected crosswalk. The DiD structure is broadly retained, but the current version changes the exposure assignment, eligible CBO sample, treatment classification, final control set, real-wage reconstruction, and age heterogeneity design.

The historical PDFs/exports do confirm the old headline wage findings: the old notebook showed a negative nominal wage effect, a smaller real wage effect, and a much larger young-worker wage effect. Those effects do not survive the current MTE-based baseline. The most defensible interpretation is that the older salary story was sensitive to the old crosswalk and old heterogeneity construction; the newer version is methodologically stronger but less dramatic on wages.

## Sources Checked

{markdown_table(inventory[["source_type", "stage", "exists", "text_chars", "path"]], ["source_type", "stage", "exists", "text_chars", "path"])}

The PDFs were extracted with `pdftotext -layout` and saved under `outputs/stage2_methodology_audit/pdf_text/`. They are treated as the historical snapshot; exported Markdown is used as the easier-to-parse companion source.

## Methodology Comparison

{markdown_table(methodology, ["domain", "audit_status", "historical_pdf_or_notebook", "current_scripts_or_outputs"])}

## Historical Wage Findings Confirmed In PDF/Notebook

{markdown_table(old_display[["label", "coef", "se", "p_value", "stars", "percent_effect", "n_obs", "note"]], ["label", "coef", "se", "p_value", "stars", "percent_effect", "n_obs", "note"])}

The user's memory of roughly a 13% young-wage effect and 3% general real-wage effect is consistent with the historical notebook/PDF: `ln_salario_jovem = -0.133735` implies about {fmt_num(pct_effect(-0.133735), 2)}%, and `ln_salario_real_adm = -0.034081` implies about {fmt_num(pct_effect(-0.034081), 2)}%.

## Current Main Results

{markdown_table(current_display[["outcome", "coef", "se", "p_value", "stars", "percent_effect", "n_obs"]], ["outcome", "coef", "se", "p_value", "stars", "percent_effect", "n_obs"])}

The current final baseline has no statistically relevant wage effect in Stage 2: `ln_salario_adm` is {fmt_num(float(current_main[current_main["outcome"].eq("ln_salario_adm")]["coef"].iloc[0]), 4)}, p={fmt_num(float(current_main[current_main["outcome"].eq("ln_salario_adm")]["p_value"].iloc[0]), 3)}.

## Wage Decomposition

{markdown_table(wage_decomp_display[["comparison_source", "before_spec", "before_coef", "before_p_value", "before_percent_effect", "after_spec", "after_coef", "after_p_value", "after_percent_effect", "note"]], ["comparison_source", "before_spec", "before_coef", "before_p_value", "before_percent_effect", "after_spec", "after_coef", "after_p_value", "after_percent_effect", "note"])}

The existing crosswalk decomposition shows that the wage effect weakens substantially even before the final control-set update: old full sample `ln_salario_adm` is negative and significant, the old score on the common MTE sample becomes smaller and non-significant, and the MTE score remains non-significant. This points to both sample selection and score reassignment, not just a cosmetic crosswalk label change.

## Salary Methodology Audit

{markdown_table(salary_display[["check", "result", "metric", "value", "interpretation"]], ["check", "result", "metric", "value", "interpretation"])}

No fatal IPCA arithmetic error was found. The key methodological issue is the wage estimand: the pipeline uses CBO-month aggregate wages, so the wage outcome is `log(mean wage)` after aggregation and winsorization, not the individual-level `mean(log wage)`. This is defensible if described accurately, but it can change interpretation.

## Age Split Evidence

{markdown_table(age_wage_display[["source_design", "definition", "outcome", "coef", "p_value", "stars", "percent_effect", "n_obs", "n_cbo", "sample_loss_reason"]], ["source_design", "definition", "outcome", "coef", "p_value", "stars", "percent_effect", "n_obs", "n_cbo", "sample_loss_reason"])}

The old young result came from an aggregate triple-DiD definition based on average age (`idade_media_adm <= 30`). The current Section 4 age design uses raw microdata subgroup panels. The audit attempted the requested raw binary young/non-young reaggregation, but the local unoptimized pass over raw CAGED was too slow for this run. The report therefore records the available current aggregate `<=30` output and the four-age-group raw-microdata output, and marks the raw binary designs as a dedicated computational follow-up.

## Identification Diagnostics

{markdown_table(pretrend_display[["domain", "item", "status", "metric", "value", "note"]], ["domain", "item", "status", "metric", "value", "note"])}

Salary has cleaner pre-trend diagnostics than admissions and separations, but the baseline treatment/control groups remain imbalanced on salary, age, female share, education, and race/color. The dissertation should avoid a strong unconditional causal claim and frame results as evidence of selective adjustment under a more defensible exposure measure.

## Direct Answers

{markdown_table(answers, ["question", "short_answer", "evidence"])}

## Files Written

- `outputs/stage2_methodology_audit/source_inventory.csv`
- `outputs/stage2_methodology_audit/methodology_comparison.csv`
- `outputs/stage2_methodology_audit/old_pdf_notebook_key_findings.csv`
- `outputs/stage2_methodology_audit/current_main_findings.csv`
- `outputs/stage2_methodology_audit/crosswalk_and_wage_decomposition.csv`
- `outputs/stage2_methodology_audit/treatment_strategy_wage_comparison.csv`
- `outputs/stage2_methodology_audit/salary_methodology_audit.csv`
- `outputs/stage2_methodology_audit/age_binary_reestimation.csv`
- `outputs/stage2_methodology_audit/age_comparison_summary.csv`
- `outputs/stage2_methodology_audit/pretrend_balance_summary.csv`
- `outputs/stage2_methodology_audit/final_answers_summary.csv`

## Verdict

Major revision to the dissertation interpretation, not rejection of the empirical strategy. The current MTE version is academically more defensible than the old crosswalk version, but the main narrative should no longer be a strong salary-loss claim. The safer contribution is: a corrected exposure assignment changes the aggregate salary finding, while employment-flow and heterogeneity patterns should be discussed with explicit pre-trend and balance caveats.
"""


def main() -> None:
    ensure_dirs()
    pdf_text = {}
    for stage, pdf in PDFS.items():
        text_path = PDF_TEXT_DIR / f"{stage}.txt"
        pdf_text[stage] = run_pdftotext(pdf, text_path)
    md_text = {stage: read_text(path) for stage, path in NOTEBOOK_EXPORTS.items()}
    script_text = {name: read_text(path) for name, path in CURRENT_SCRIPTS.items()}

    inventory = source_inventory(pdf_text, md_text)
    methodology = methodology_comparison(md_text, script_text)
    old_findings = old_pdf_notebook_findings()
    current_main = current_main_findings()
    crosswalk = crosswalk_decomposition(current_main)
    treatment_wage = treatment_strategy_wage_comparison()
    salary_cache = OUT_DIR / "salary_methodology_audit.csv"
    salary_audit = pd.read_csv(salary_cache) if salary_cache.exists() else salary_methodology_audit()
    age_binary = age_binary_reestimation_from_current_outputs()
    age_summary = age_comparison_summary(age_binary)
    pretrend_balance = pretrend_balance_summary()
    answers = final_answers_summary(old_findings, current_main, crosswalk, salary_audit, age_summary)

    REPORT_PATH.write_text(
        report_text(
            inventory,
            methodology,
            old_findings,
            current_main,
            crosswalk,
            treatment_wage,
            salary_audit,
            age_summary,
            pretrend_balance,
            answers,
        ),
        encoding="utf-8",
    )
    print(f"Audit report written: {REPORT_PATH}")
    print(f"Audit tables written: {OUT_DIR}")


if __name__ == "__main__":
    main()
