#!/usr/bin/env python3
"""Build dissertation Section 4 empirical result artifacts.

The script intentionally depends on the regenerated Stage 2a, Stage 2b, and
treatment-scenario-grid outputs. It also rebuilds the sociodemographic
heterogeneity panels from raw CAGED microdata.
"""

from __future__ import annotations

import math
import shutil
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfixest as pf


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)


ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_OUTPUT = ROOT / "data" / "output"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_FIGURES = ROOT / "outputs" / "figures"
SCENARIO_DIR = ROOT / "outputs" / "treatment_scenario_grid"
SECTION4_DIR = ROOT / "outputs" / "dissertation_section4"
SECTION4_FIGURES = SECTION4_DIR / "figures"
SECTION4_TABLES = SECTION4_DIR / "tables"

EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"
ANO_TRATAMENTO = 2022
MES_TRATAMENTO = 12
INDICE_BASE = 100.0

SALARIO_MINIMO = {
    2021: 1100,
    2022: 1212,
    2023: 1320,
    2024: 1412,
    2025: 1518,
}

REQUIRED_SCENARIOS = [
    "baseline_mte2d_top20_vs_rest",
    "trat_alta_expo",
    "trat_media_expo",
    "trat_expostos",
]

SCENARIO_LABELS_PT = {
    "baseline_mte2d_top20_vs_rest": "MTE 20% vs demais",
    "trat_alta_expo": "Trat. alta exposição OIT (G3-G4) vs não expostos",
    "trat_media_expo": "Trat. média exposição OIT (G1-G2) vs não expostos",
    "trat_expostos": "Trat. expostos OIT (G1-G4) vs não expostos",
}

OUTCOME_ORDER = [
    "ln_admissoes",
    "ln_desligamentos",
    "saldo",
    "ln_salario_real_adm",
]

OUTCOME_LABELS_PT = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Desligamentos (log)",
    "saldo": "Saldo líquido",
    "ln_salario_adm": "Salário de admissão (log)",
    "ln_salario_real_adm": "Salário real de admissão (log)",
    "mean_log_wage_adm": "Média do log do salário de admissão",
    "ln_median_wage_adm": "Mediana salarial de admissão (log)",
    "saldo_per_pre_adm": "Saldo / admissões médias pré",
    "saldo_flow_rate": "Saldo / fluxo total",
    "asinh_saldo": "asinh(saldo)",
}

STAGE2_OUTCOME_MAP = {
    "ln_admissoes": "ln_admissoes",
    "ln_desligamentos": "ln_desligamentos",
    "saldo": "saldo",
    "ln_salario_real_adm": "ln_salario_adm",
}

SECTION4_CONTROL_COLUMNS = [
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
]
SECTION4_CONTROLS = " + ".join(SECTION4_CONTROL_COLUMNS)

SEX_VALID_CODES = {"1", "3", "9"}
RACE_COLOR_CODE_TO_GROUP = {
    "1": "race_white",
    "2": "race_black",
    "3": "race_pardo",
    "4": "race_yellow",
    "5": "race_indigenous",
    "6": "race_unknown",
    "9": "race_unknown",
}
RACE_COLOR_VALID_CODES = set(RACE_COLOR_CODE_TO_GROUP)
EDUCATION_VALID_CODES = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "80", "99"}

DIMENSIONS_MAIN = {
    "income": {
        "panel": "Painel A: Renda",
        "groups": [
            ("low_income", "Baixa renda: até 2 salários mínimos"),
            ("middle_income", "Média renda: mais de 2 até 5 salários mínimos"),
            ("high_income", "Alta renda: mais de 5 salários mínimos"),
        ],
    },
    "education": {
        "panel": "Painel B: Escolaridade",
        "groups": [
            ("fundamental_or_less", "Fundamental ou menos"),
            ("high_school", "Médio"),
            ("higher_education", "Superior"),
        ],
    },
    "age": {
        "panel": "Painel C: Idade",
        "groups": [
            ("age_14_24", "14-24"),
            ("age_25_34", "25-34"),
            ("age_35_59", "35-59"),
            ("age_60_plus", "60+"),
        ],
    },
    "sex": {
        "panel": "Painel D: Sexo",
        "groups": [
            ("men", "Homens"),
            ("women", "Mulheres"),
        ],
    },
    "race_color": {
        "panel": "Painel E: Raça/cor",
        "groups": [
            ("race_white", "Branca"),
            ("race_black", "Preta"),
            ("race_pardo", "Parda"),
            ("race_yellow", "Amarela"),
            ("race_indigenous", "Indígena"),
            ("race_unknown", "Não informada/identificada"),
        ],
    },
}

DIMENSIONS_AUDIT = DIMENSIONS_MAIN

TABLE4_WAGE_OUTCOMES = [
    ("ln_salario_adm", "log(mean wage)", "Baseline: log da média salarial agregada após winsorização P1/P99."),
    ("mean_log_wage_adm", "mean(log wage)", "Média do log individual entre admissões com salário positivo."),
    ("ln_median_wage_adm", "log(median wage)", "Log da mediana salarial de admissão por CBO-mês."),
]

TABLE4_SALDO_OUTCOMES = [
    ("saldo", "Saldo em nível", "Admissões menos desligamentos."),
    ("saldo_per_pre_adm", "Saldo / admissões pré", "Saldo dividido pela média pré-tratamento de admissões do CBO."),
    ("saldo_flow_rate", "Saldo / fluxo total", "Saldo dividido por admissões mais desligamentos no CBO-mês."),
    ("asinh_saldo", "asinh(saldo)", "Transformação simétrica que aceita valores negativos."),
]

AGE_BINARY_SPECS = [
    {
        "definition": "young_14_24",
        "definition_label": "Jovem 14-24 vs 25+",
        "young_group": "young_14_24",
        "young_label": "14-24",
        "non_young_group": "non_young_25_plus",
        "non_young_label": "25+",
        "young_min": 14,
        "young_max": 24,
        "non_young_min": 25,
    },
    {
        "definition": "young_14_30",
        "definition_label": "Jovem 14-30 vs 31+",
        "young_group": "young_14_30",
        "young_label": "14-30",
        "non_young_group": "non_young_31_plus",
        "non_young_label": "31+",
        "young_min": 14,
        "young_max": 30,
        "non_young_min": 31,
    },
]

TABLE4_AGE_OUTCOMES = [
    "ln_admissoes",
    "ln_desligamentos",
    "saldo_per_pre_adm",
    "ln_salario_real_adm",
]


def log(message: str) -> None:
    print(message, flush=True)


def stars(p_value: float | None) -> str:
    if p_value is None or pd.isna(p_value):
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def fmt_number(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}".replace(".", ",")
    return str(value)


def estimate_cell(coef: object, se: object, sig: object) -> str:
    if pd.isna(coef) or pd.isna(se):
        return ""
    return f"{fmt_number(coef)}{'' if pd.isna(sig) else sig}<br>({fmt_number(se)})"


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sem estimativas disponíveis._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in df[columns].iterrows():
        values = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def write_markdown_table(path: Path, title: str, df: pd.DataFrame, columns: list[str]) -> None:
    text = (
        f"# {title}\n\n"
        + markdown_table(df, columns)
        + "\n\nNotas: erros-padrão clusterizados por CBO 4 dígitos entre parênteses. "
        + "* p<0.10; ** p<0.05; *** p<0.01.\n"
    )
    path.write_text(text, encoding="utf-8")


def bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.lower().isin(["true", "1", "1.0", "yes"])


def ensure_directories() -> None:
    SECTION4_FIGURES.mkdir(parents=True, exist_ok=True)
    SECTION4_TABLES.mkdir(parents=True, exist_ok=True)


def clean_generated_section4_tables() -> None:
    for pattern in [
        "table2_exposure_types.*",
        "table3_heterogeneity_*.csv",
        "table3_heterogeneity_*.md",
        "table4*_*.csv",
        "table4*_*.md",
    ]:
        for path in SECTION4_TABLES.glob(pattern):
            path.unlink()


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = [
        DATA_OUTPUT / "painel_2b_ready.parquet",
        OUTPUT_TABLES / "did_main_results.csv",
        SCENARIO_DIR / "scenario_cbo_classification.csv",
        SCENARIO_DIR / "stage2_scenario_results.csv",
        SCENARIO_DIR / "baseline_validation.csv",
    ]
    for path in required:
        require_file(path)

    panel = pd.read_parquet(DATA_OUTPUT / "painel_2b_ready.parquet")
    did = pd.read_csv(OUTPUT_TABLES / "did_main_results.csv")
    classification = pd.read_csv(SCENARIO_DIR / "scenario_cbo_classification.csv")
    scenario_results = pd.read_csv(SCENARIO_DIR / "stage2_scenario_results.csv")
    baseline_validation = pd.read_csv(SCENARIO_DIR / "baseline_validation.csv")

    validate_core_inputs(panel, did, classification, scenario_results, baseline_validation)
    return panel, did, classification, scenario_results, baseline_validation


def validate_core_inputs(
    panel: pd.DataFrame,
    did: pd.DataFrame,
    classification: pd.DataFrame,
    scenario_results: pd.DataFrame,
    baseline_validation: pd.DataFrame,
) -> None:
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    if set(panel["crosswalk_spec"].dropna().unique()) != {EXPECTED_CROSSWALK_SPEC}:
        raise RuntimeError("Stage 2 panel crosswalk_spec is not mte_official_no_numeric_fallback.")
    if "crosswalk_spec" not in did or set(did["crosswalk_spec"].dropna().unique()) != {EXPECTED_CROSSWALK_SPEC}:
        raise RuntimeError("did_main_results.csv crosswalk_spec is not mte_official_no_numeric_fallback.")
    if float(panel["pct_mulher_adm"].max()) == 0.0:
        raise RuntimeError("Stage 2 panel still has pct_mulher_adm.max() == 0.")
    missing_controls = [col for col in SECTION4_CONTROL_COLUMNS if col not in panel.columns]
    if missing_controls:
        raise RuntimeError(f"Stage 2 panel is missing required controls: {missing_controls}.")
    max_negra = pd.to_numeric(panel["pct_negra_adm"], errors="coerce").max(skipna=True)
    if pd.isna(max_negra) or float(max_negra) == 0.0:
        raise RuntimeError(f"Stage 2 panel still has pct_negra_adm.max() == {max_negra}.")
    required_classification_cols = [
        "isco08_mean_score",
        "isco08_pooled_sd",
        "cbo_ilo_gradient",
        "trat_alta_expo",
        "trat_media_expo",
        "trat_expostos",
        "treatment_rule_source",
    ]
    missing_classification_cols = [
        col for col in required_classification_cols if col not in classification.columns
    ]
    if missing_classification_cols:
        raise RuntimeError(f"Classification is missing OIT mean+SD columns: {missing_classification_cols}.")
    expected_counts = {
        "trat_alta_expo": 31,
        "trat_media_expo": 44,
        "trat_expostos": 75,
    }
    observed_counts = {
        col: int(bool_series(classification[col]).sum())
        for col in expected_counts
    }
    if observed_counts != expected_counts:
        raise RuntimeError(
            f"OIT treatment counts changed. Expected {expected_counts}; found {observed_counts}."
        )
    if len(classification) != 629:
        raise RuntimeError(f"Classification should contain 629 CBO rows; found {len(classification)}.")
    matched_count = int(classification["mte_match_status"].eq("matched_official_mte").sum())
    unmatched_count = int(classification["mte_match_status"].eq("sem_match_mte_no_result").sum())
    if (matched_count, unmatched_count) != (436, 193):
        raise RuntimeError(
            f"Expected 436 matched and 193 unmatched MTE CBOs; found {matched_count} and {unmatched_count}."
        )
    case_rows = classification.set_index("cbo_4d", drop=False)
    if "7841" not in case_rows.index:
        raise RuntimeError("Critical CBO 7841 is missing from classification.")
    cbo_7841 = case_rows.loc["7841"]
    if cbo_7841["cbo_ilo_gradient"] != "Minimal Exposure":
        raise RuntimeError(f"CBO 7841 should be Minimal Exposure; found {cbo_7841['cbo_ilo_gradient']}.")
    if (
        bool_series(pd.Series([cbo_7841["trat_media_expo"]])).iloc[0]
        or bool_series(pd.Series([cbo_7841["trat_expostos"]])).iloc[0]
    ):
        raise RuntimeError("CBO 7841 should be outside trat_media_expo and trat_expostos.")
    if "1425" not in case_rows.index:
        raise RuntimeError("Critical CBO 1425 is missing from classification.")
    if case_rows.loc["1425", "mte_match_status"] != "sem_match_mte_no_result":
        raise RuntimeError("CBO 1425 should remain sem_match_mte_no_result.")
    for scenario in REQUIRED_SCENARIOS:
        required_cols = [
            f"role__{scenario}",
            f"treated__{scenario}",
            f"included__{scenario}",
        ]
        missing = [col for col in required_cols if col not in classification.columns]
        if missing:
            raise RuntimeError(f"Scenario {scenario} is missing from classification columns: {missing}")
        rows = scenario_results[
            (scenario_results["scenario_id"] == scenario)
            & (scenario_results["outcome"].isin(list(STAGE2_OUTCOME_MAP.values())))
        ]
        if set(rows["outcome"]) != set(STAGE2_OUTCOME_MAP.values()):
            raise RuntimeError(f"Scenario {scenario} does not have all four Stage 2 outcomes.")
    if not bool(baseline_validation["passed"].all()):
        raise RuntimeError("Treatment scenario baseline_validation.csv contains failed rows.")
    validate_baseline_parity(did, scenario_results)


def validate_baseline_parity(did: pd.DataFrame, scenario_results: pd.DataFrame) -> None:
    main = did[did["model"] == "Model 3: FE + Controls (MAIN)"].copy()
    base = scenario_results[
        (scenario_results["scenario_id"] == "baseline_mte2d_top20_vs_rest")
        & (scenario_results["result_status"] == "estimated")
    ].copy()
    merged = base.merge(main, on="outcome", suffixes=("_scenario", "_did"))
    if merged.empty:
        raise RuntimeError("Could not compare baseline scenario rows against Stage 2b Model 3 rows.")
    for col in ["coef", "se", "p_value"]:
        diff = (merged[f"{col}_scenario"] - merged[f"{col}_did"]).abs().max()
        if diff > 1e-6:
            raise RuntimeError(f"Baseline parity failed for {col}: max diff {diff}")


def build_figure1() -> None:
    fig_path = SECTION4_FIGURES / "figure1_event_study_aggregate.png"
    event_files = {
        "ln_admissoes": OUTPUT_TABLES / "event_study_ln_admissoes.csv",
        "ln_desligamentos": OUTPUT_TABLES / "event_study_ln_desligamentos.csv",
        "saldo": OUTPUT_TABLES / "event_study_saldo.csv",
        "ln_salario_adm": OUTPUT_TABLES / "event_study_ln_salario_adm.csv",
    }
    for path in event_files.values():
        require_file(path)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), sharex=True)
    axes = axes.ravel()
    titles = {
        "ln_admissoes": "Admissões",
        "ln_desligamentos": "Desligamentos",
        "saldo": "Saldo líquido",
        "ln_salario_adm": "Salário de admissão",
    }
    for ax, (outcome, path) in zip(axes, event_files.items(), strict=True):
        df = pd.read_csv(path)
        if set(df["crosswalk_spec"].dropna().unique()) != {EXPECTED_CROSSWALK_SPEC}:
            raise RuntimeError(f"{path} has wrong crosswalk_spec.")
        ax.axhline(0, color="#333333", linewidth=0.8)
        ax.axvline(0, color="#b22222", linestyle="--", linewidth=0.9)
        ax.fill_between(df["t"], df["ci_low"], df["ci_high"], color="#c8d3e6", alpha=0.7)
        ax.plot(df["t"], df["coef"], color="#1f4e79", marker="o", linewidth=1.5, markersize=3)
        ax.set_title(titles[outcome])
        ax.grid(True, axis="y", alpha=0.25)
    fig.supxlabel("Meses em relação a dezembro de 2022")
    fig.supylabel("Coeficiente relativo ao mês -1")
    fig.suptitle("Figura 1. Estudo de eventos agregado", y=0.98)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_table1(did: pd.DataFrame) -> pd.DataFrame:
    main = did[did["model"] == "Model 3: FE + Controls (MAIN)"].copy()
    main = main[main["outcome"].isin(["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_adm"])].copy()
    order = ["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_adm"]
    main["outcome_order"] = main["outcome"].map({name: i for i, name in enumerate(order)})
    main = main.sort_values("outcome_order")
    main["outcome_label"] = main["outcome"].map(OUTCOME_LABELS_PT)
    main["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in main.itertuples()]
    main["p_value_fmt"] = main["p_value"].map(lambda v: fmt_number(v, 3))
    main["n_obs_fmt"] = main["n_obs"].map(lambda v: fmt_number(v, 0))
    out = main[
        ["outcome", "outcome_label", "coef", "se", "p_value", "stars", "n_obs", "crosswalk_spec", "estimate_se"]
    ].copy()
    out.to_csv(SECTION4_TABLES / "table1_main_effects.csv", index=False)
    md = out.assign(
        Resultado=out["outcome_label"],
        Estimativa=out["estimate_se"],
        p=out["p_value"].map(lambda v: fmt_number(v, 3)),
        N=out["n_obs"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        SECTION4_TABLES / "table1_main_effects.md",
        "Tabela 1. Resultado principal agregado",
        md,
        ["Resultado", "Estimativa", "p", "N"],
    )
    return out


def build_table2(scenario_results: pd.DataFrame) -> pd.DataFrame:
    rows = scenario_results[
        (scenario_results["scenario_id"].isin(REQUIRED_SCENARIOS))
        & (scenario_results["outcome"].isin(["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_adm"]))
    ].copy()
    rows["scenario_label_pt"] = rows["scenario_id"].map(SCENARIO_LABELS_PT)
    rows["outcome_label_pt"] = rows["outcome"].map(OUTCOME_LABELS_PT)
    rows["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in rows.itertuples()]
    rows["scenario_order"] = rows["scenario_id"].map({name: i for i, name in enumerate(REQUIRED_SCENARIOS)})
    rows["outcome_order"] = rows["outcome"].map({name: i for i, name in enumerate(STAGE2_OUTCOME_MAP.values())})
    rows = rows.sort_values(["scenario_order", "outcome_order"])
    rows.to_csv(SECTION4_TABLES / "table2_exposure_types.csv", index=False)
    md = rows.assign(
        Cenario=rows["scenario_label_pt"],
        Resultado=rows["outcome_label_pt"],
        Estimativa=rows["estimate_se"],
        p=rows["p_value"].map(lambda v: fmt_number(v, 3)),
        N=rows["n_obs"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        SECTION4_TABLES / "table2_exposure_types.md",
        "Tabela 2. Decomposição conceitual por definição de exposição",
        md,
        ["Cenario", "Resultado", "Estimativa", "p", "N"],
    )
    return rows


def normalize_codes(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def validate_allowed_codes(df: pd.DataFrame, column: str, allowed_codes: set[str], context: str) -> None:
    if column not in df.columns:
        raise RuntimeError(f"{context}: missing raw CAGED column {column!r}.")
    observed = set(normalize_codes(df[column]).dropna().unique())
    unexpected = sorted(observed - allowed_codes)
    if unexpected:
        raise RuntimeError(
            f"{context}: unexpected values in raw CAGED column {column!r}: "
            f"{unexpected}. Expected subset: {sorted(allowed_codes)}."
        )


def validate_raw_caged_codes(df: pd.DataFrame, context: str) -> None:
    validate_allowed_codes(df, "sexo", SEX_VALID_CODES, context)
    validate_allowed_codes(df, "raca_cor", RACE_COLOR_VALID_CODES, context)
    validate_allowed_codes(df, "grau_instrucao", EDUCATION_VALID_CODES, context)


def valid_cbo_4d(series: pd.Series) -> pd.Series:
    codes = normalize_codes(series).str[:4]
    return codes.where(codes.str.fullmatch(r"\d{4}", na=False))


def build_income_groups() -> dict[str, str]:
    log("Building pre-treatment CBO income groups from raw CAGED admissions...")
    pieces = []
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        df = pd.read_parquet(
            path,
            columns=["ano", "mes", "cbo_2002", "saldo_movimentacao", "salario_mensal"],
        )
        df["periodo_num"] = df["ano"].astype(int) * 100 + df["mes"].astype(int)
        df = df[
            (df["periodo_num"] < ANO_TRATAMENTO * 100 + MES_TRATAMENTO)
            & (df["saldo_movimentacao"] == 1)
            & df["salario_mensal"].notna()
            & (df["salario_mensal"] > 0)
        ].copy()
        if df.empty:
            continue
        df["cbo_4d"] = valid_cbo_4d(df["cbo_2002"])
        df = df[df["cbo_4d"].notna()].copy()
        df["salario_sm"] = df["salario_mensal"] / df["ano"].astype(int).map(SALARIO_MINIMO)
        pieces.append(df[["cbo_4d", "salario_sm"]])
    if not pieces:
        raise RuntimeError("Could not build pre-treatment income groups from raw CAGED.")
    all_wages = pd.concat(pieces, ignore_index=True)
    med = all_wages.groupby("cbo_4d", observed=True)["salario_sm"].median()

    def bucket(value: float) -> str:
        if value <= 2:
            return "low_income"
        if value <= 5:
            return "middle_income"
        return "high_income"

    return med.map(bucket).to_dict()


def load_ipca_map() -> dict[int, float]:
    path = DATA_PROCESSED / "ipca_mensal.parquet"
    require_file(path)
    df = pd.read_parquet(path)
    return {int(r.ano) * 100 + int(r.mes): float(r.indice) for r in df.itertuples()}


def empty_group_series(index: pd.Index) -> pd.Series:
    return pd.Series(pd.NA, index=index, dtype="string")


def group_series_for_dimension(df: pd.DataFrame, dimension: str, income_groups: dict[str, str]) -> pd.Series:
    group = empty_group_series(df.index)
    if dimension == "income":
        return df["cbo_4d"].map(income_groups).astype("string")
    if dimension == "education":
        edu = normalize_codes(df["grau_instrucao"])
        group.loc[edu.isin(["1", "2", "3", "4", "5"])] = "fundamental_or_less"
        group.loc[edu.isin(["6", "7"])] = "high_school"
        group.loc[edu.isin(["8", "9", "10", "11", "80"])] = "higher_education"
        return group
    if dimension == "age":
        age = pd.to_numeric(df["idade"], errors="coerce")
        group.loc[(age >= 14) & (age <= 24)] = "age_14_24"
        group.loc[(age >= 25) & (age <= 34)] = "age_25_34"
        group.loc[(age >= 35) & (age <= 59)] = "age_35_59"
        group.loc[age >= 60] = "age_60_plus"
        return group
    if dimension == "sex":
        sex = normalize_codes(df["sexo"])
        group.loc[sex == "1"] = "men"
        group.loc[sex == "3"] = "women"
        return group
    if dimension == "race_color":
        race = normalize_codes(df["raca_cor"])
        mapped = race.map(RACE_COLOR_CODE_TO_GROUP)
        group.loc[mapped.notna()] = mapped.loc[mapped.notna()]
        return group
    raise ValueError(f"Unknown heterogeneity dimension: {dimension}")


def assign_groups(df: pd.DataFrame, income_groups: dict[str, str]) -> pd.DataFrame:
    def bool_array(mask: pd.Series) -> np.ndarray:
        return mask.fillna(False).to_numpy(dtype=bool)

    out = df.copy()
    out["income_group"] = out["cbo_4d"].map(income_groups)
    edu = normalize_codes(out["grau_instrucao"])
    out["education_group"] = np.select(
        [
            bool_array(edu.isin(["1", "2", "3", "4", "5"])),
            bool_array(edu.isin(["6", "7"])),
            bool_array(edu.isin(["8", "9", "10", "11", "80"])),
        ],
        ["fundamental_or_less", "high_school", "higher_education"],
        default=None,
    )
    age = pd.to_numeric(out["idade"], errors="coerce")
    out["age_group"] = np.select(
        [
            bool_array((age >= 14) & (age <= 24)),
            bool_array((age >= 25) & (age <= 34)),
            bool_array((age >= 35) & (age <= 59)),
            bool_array(age >= 60),
        ],
        ["age_14_24", "age_25_34", "age_35_59", "age_60_plus"],
        default=None,
    )
    sex = normalize_codes(out["sexo"])
    out["sex_group"] = np.select(
        [bool_array(sex == "1"), bool_array(sex == "3")],
        ["men", "women"],
        default=None,
    )
    race = normalize_codes(out["raca_cor"])
    out["race_color_group"] = race.map(RACE_COLOR_CODE_TO_GROUP)
    return out


def aggregate_raw_heterogeneity() -> pd.DataFrame:
    log("Reconstructing heterogeneity panels from raw CAGED microdata...")
    income_groups = build_income_groups()
    ipca_map = load_ipca_map()
    raw_cols = [
        "ano",
        "mes",
        "cbo_2002",
        "saldo_movimentacao",
        "salario_mensal",
        "grau_instrucao",
        "idade",
        "sexo",
        "raca_cor",
    ]
    pieces = []
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        log(f"  Reading {path.name}")
        df = pd.read_parquet(path, columns=raw_cols)
        validate_raw_caged_codes(df, path.name)
        df["cbo_4d"] = valid_cbo_4d(df["cbo_2002"])
        df = df[df["cbo_4d"].notna()].copy()
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["periodo"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
        df["periodo_num"] = df["ano"] * 100 + df["mes"]
        df["post"] = (df["periodo_num"] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)
        df["ipca_indice"] = df["periodo_num"].map(ipca_map)
        if df["ipca_indice"].isna().any():
            raise RuntimeError(f"Missing IPCA index while processing {path.name}.")
        df["salario_real"] = df["salario_mensal"] * (INDICE_BASE / df["ipca_indice"].clip(lower=0.01))
        df["is_adm"] = (df["saldo_movimentacao"] == 1).astype(int)
        df["is_des"] = (df["saldo_movimentacao"] == -1).astype(int)
        df["salario_real_adm"] = np.where(df["saldo_movimentacao"] == 1, df["salario_real"], np.nan)
        base = df[
            [
                "cbo_4d",
                "ano",
                "mes",
                "periodo",
                "periodo_num",
                "post",
                "is_adm",
                "is_des",
                "saldo_movimentacao",
                "salario_real_adm",
            ]
        ]
        for dimension in DIMENSIONS_AUDIT:
            log(f"    Aggregating {dimension}...")
            group_id = group_series_for_dimension(df, dimension, income_groups)
            mask = group_id.notna()
            if not bool(mask.any()):
                continue
            d = base.loc[mask].copy()
            d["group_id"] = group_id.loc[mask].to_numpy()
            agg = (
                d.groupby(["cbo_4d", "ano", "mes", "periodo", "periodo_num", "post", "group_id"], observed=True)
                .agg(
                    admissoes=("is_adm", "sum"),
                    desligamentos=("is_des", "sum"),
                    saldo=("saldo_movimentacao", "sum"),
                    salario_real_adm=("salario_real_adm", "mean"),
                )
                .reset_index()
            )
            agg["dimension"] = dimension
            pieces.append(agg)
            del d, agg, group_id, mask
        del base
        del df
    if not pieces:
        raise RuntimeError("Raw CAGED heterogeneity reconstruction produced no rows.")
    out = pd.concat(pieces, ignore_index=True)
    out["ln_admissoes"] = np.log(out["admissoes"] + 1)
    out["ln_desligamentos"] = np.log(out["desligamentos"] + 1)
    out["ln_salario_real_adm"] = np.log(out["salario_real_adm"].clip(lower=1))
    return out


def base_controls(panel: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "cbo_4d",
        "ano",
        "mes",
        "periodo",
        "periodo_num",
        "post",
        "idade_media_adm",
        "pct_mulher_adm",
        "pct_superior_adm",
        "pct_negra_adm",
    ]
    out = panel[cols].copy()
    out["cbo_4d"] = out["cbo_4d"].astype(str).str.zfill(4)
    return out


def scenario_assignments(classification: pd.DataFrame, scenario: str) -> pd.DataFrame:
    role_col = f"role__{scenario}"
    if role_col not in classification.columns:
        raise RuntimeError(f"Classification is missing {role_col}.")
    out = classification[classification[role_col].isin(["treated", "control"])][["cbo_4d", role_col]].copy()
    out = out.rename(columns={role_col: "scenario_role"})
    out["cbo_4d"] = out["cbo_4d"].astype(str).str.zfill(4)
    out["scenario_treat"] = (out["scenario_role"] == "treated").astype(int)
    return out


def apply_scenario_to_panel(panel: pd.DataFrame, classification: pd.DataFrame, scenario: str) -> pd.DataFrame:
    assignments = scenario_assignments(classification, scenario)
    out = panel.merge(assignments, on="cbo_4d", how="inner")
    out["post_treat"] = out["post"].astype(int) * out["scenario_treat"].astype(int)
    return out


def build_mean_log_wage_panel() -> pd.DataFrame:
    log("Building mean(log wage) from raw CAGED admissions...")
    pieces = []
    raw_cols = ["ano", "mes", "cbo_2002", "saldo_movimentacao", "salario_mensal"]
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        df = pd.read_parquet(path, columns=raw_cols)
        df = df[
            (df["saldo_movimentacao"] == 1)
            & df["salario_mensal"].notna()
            & (df["salario_mensal"] > 0)
        ].copy()
        if df.empty:
            continue
        df["cbo_4d"] = valid_cbo_4d(df["cbo_2002"])
        df = df[df["cbo_4d"].notna()].copy()
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["log_wage_adm"] = np.log(df["salario_mensal"])
        agg = (
            df.groupby(["cbo_4d", "ano", "mes"], observed=True)
            .agg(
                mean_log_wage_adm=("log_wage_adm", "mean"),
                positive_wage_admissions=("log_wage_adm", "size"),
            )
            .reset_index()
        )
        pieces.append(agg)
    if not pieces:
        raise RuntimeError("Could not build mean_log_wage_adm from raw CAGED.")
    return pd.concat(pieces, ignore_index=True)


def build_table4_base_panel(panel: pd.DataFrame) -> pd.DataFrame:
    required = [
        "admissoes",
        "desligamentos",
        "saldo",
        "ln_salario_adm",
        "salario_mediano_adm",
    ]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise RuntimeError(f"Stage 2 panel is missing Table 4 base columns: {missing}.")

    out = base_controls(panel)
    extra = panel[
        [
            "cbo_4d",
            "ano",
            "mes",
            "admissoes",
            "desligamentos",
            "saldo",
            "ln_salario_adm",
            "salario_mediano_adm",
        ]
    ].copy()
    extra["cbo_4d"] = extra["cbo_4d"].astype(str).str.zfill(4)
    out = out.merge(extra, on=["cbo_4d", "ano", "mes"], how="left")

    mean_log = build_mean_log_wage_panel()
    out = out.merge(mean_log, on=["cbo_4d", "ano", "mes"], how="left")
    out["ln_median_wage_adm"] = np.log(pd.to_numeric(out["salario_mediano_adm"], errors="coerce").clip(lower=1))
    for col in ["admissoes", "desligamentos", "saldo"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    pre = (
        out[out["periodo_num"] < ANO_TRATAMENTO * 100 + MES_TRATAMENTO]
        .groupby("cbo_4d", observed=True)["admissoes"]
        .mean()
        .rename("pre_adm_mean")
        .reset_index()
    )
    out = out.merge(pre, on="cbo_4d", how="left")
    if (out["pre_adm_mean"].dropna() <= 0).any():
        bad = out.loc[out["pre_adm_mean"].le(0), "cbo_4d"].drop_duplicates().head(20).tolist()
        raise RuntimeError(f"saldo_per_pre_adm would use zero/nonpositive denominators for CBOs: {bad}")
    pre_values = pd.to_numeric(out["pre_adm_mean"], errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    saldo_values = pd.to_numeric(out["saldo"], errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    adm_values = pd.to_numeric(out["admissoes"], errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    des_values = pd.to_numeric(out["desligamentos"], errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    out["saldo_per_pre_adm"] = np.where(
        pre_values > 0,
        saldo_values / pre_values,
        np.nan,
    )
    flow = adm_values + des_values
    out["saldo_flow_rate"] = np.where(flow > 0, saldo_values / flow, np.nan)
    out["asinh_saldo"] = np.arcsinh(saldo_values)

    if out["mean_log_wage_adm"].notna().any() and out.loc[out["mean_log_wage_adm"].notna(), "positive_wage_admissions"].le(0).any():
        raise RuntimeError("mean_log_wage_adm contains rows without positive-wage admissions.")
    return out


def age_binary_group(age: pd.Series, spec: dict[str, object]) -> pd.Series:
    group = empty_group_series(age.index)
    young_min = int(spec["young_min"])
    young_max = int(spec["young_max"])
    non_young_min = int(spec["non_young_min"])
    group.loc[(age >= young_min) & (age <= young_max)] = str(spec["young_group"])
    group.loc[age >= non_young_min] = str(spec["non_young_group"])
    return group


def aggregate_raw_age_binary_robustness() -> tuple[pd.DataFrame, pd.DataFrame]:
    log("Building binary youth robustness panels from raw CAGED microdata...")
    ipca_map = load_ipca_map()
    raw_cols = [
        "ano",
        "mes",
        "cbo_2002",
        "saldo_movimentacao",
        "salario_mensal",
        "idade",
    ]
    pieces = []
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        df = pd.read_parquet(path, columns=raw_cols)
        df["cbo_4d"] = valid_cbo_4d(df["cbo_2002"])
        df = df[df["cbo_4d"].notna()].copy()
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["periodo"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
        df["periodo_num"] = df["ano"] * 100 + df["mes"]
        df["post"] = (df["periodo_num"] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)
        df["ipca_indice"] = df["periodo_num"].map(ipca_map)
        if df["ipca_indice"].isna().any():
            raise RuntimeError(f"Missing IPCA index while processing {path.name}.")
        df["idade_num"] = pd.to_numeric(df["idade"], errors="coerce")
        df["is_adm"] = (df["saldo_movimentacao"] == 1).astype(int)
        df["is_des"] = (df["saldo_movimentacao"] == -1).astype(int)
        df["salario_real"] = df["salario_mensal"] * (INDICE_BASE / df["ipca_indice"].clip(lower=0.01))
        df["salario_real_adm"] = np.where(df["saldo_movimentacao"] == 1, df["salario_real"], np.nan)
        base = df[
            [
                "cbo_4d",
                "ano",
                "mes",
                "periodo",
                "periodo_num",
                "post",
                "is_adm",
                "is_des",
                "saldo_movimentacao",
                "salario_real_adm",
                "idade_num",
            ]
        ].copy()
        for spec in AGE_BINARY_SPECS:
            group_id = age_binary_group(base["idade_num"], spec)
            mask = group_id.notna()
            if not bool(mask.any()):
                continue
            d = base.loc[mask].copy()
            d["age_definition"] = str(spec["definition"])
            d["age_definition_label"] = str(spec["definition_label"])
            d["group_id"] = group_id.loc[mask].to_numpy()
            agg = (
                d.groupby(
                    [
                        "cbo_4d",
                        "ano",
                        "mes",
                        "periodo",
                        "periodo_num",
                        "post",
                        "age_definition",
                        "age_definition_label",
                        "group_id",
                    ],
                    observed=True,
                )
                .agg(
                    admissoes=("is_adm", "sum"),
                    desligamentos=("is_des", "sum"),
                    saldo=("saldo_movimentacao", "sum"),
                    salario_real_adm=("salario_real_adm", "mean"),
                )
                .reset_index()
            )
            pieces.append(agg)
            del d, agg, group_id, mask
        del base, df
    if not pieces:
        raise RuntimeError("Binary youth robustness reconstruction produced no rows.")
    out = pd.concat(pieces, ignore_index=True)
    out["ln_admissoes"] = np.log(out["admissoes"] + 1)
    out["ln_desligamentos"] = np.log(out["desligamentos"] + 1)
    out["ln_salario_real_adm"] = np.log(out["salario_real_adm"].clip(lower=1))
    pre = (
        out[out["periodo_num"] < ANO_TRATAMENTO * 100 + MES_TRATAMENTO]
        .groupby(["cbo_4d", "age_definition", "group_id"], observed=True)["admissoes"]
        .mean()
        .rename("age_pre_adm_mean")
        .reset_index()
    )
    nonpositive = pre[pre["age_pre_adm_mean"] <= 0].copy()
    if not nonpositive.empty:
        nonpositive.to_csv(SECTION4_TABLES / "table4c_age_binary_zero_pre_adm_audit.csv", index=False)
    return out, pre


def estimate_one(data: pd.DataFrame, outcome: str) -> dict[str, object]:
    d = data.dropna(
        subset=[outcome, "post_treat", *SECTION4_CONTROL_COLUMNS]
    ).copy()
    n_cbo = int(d["cbo_4d"].nunique())
    if d.empty or n_cbo < 2 or d["scenario_treat"].nunique() < 2:
        return {
            "result_status": "failed_insufficient_sample",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": n_cbo,
            "error": "Empty sample, fewer than two CBOs, or only one treatment group.",
        }
    formula = f"{outcome} ~ post_treat + {SECTION4_CONTROLS} | cbo_4d + periodo"
    try:
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        if "post_treat" not in model.coef().index:
            raise RuntimeError("post_treat was dropped or not estimated.")
        p_value = float(model.pvalue().loc["post_treat"])
        return {
            "result_status": "estimated",
            "coef": float(model.coef().loc["post_treat"]),
            "se": float(model.se().loc["post_treat"]),
            "p_value": p_value,
            "stars": stars(p_value),
            "n_obs": int(len(d)),
            "n_cbo": n_cbo,
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001 - keep audit rows for failed groups
        return {
            "result_status": "failed_estimation",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": n_cbo,
            "error": str(exc),
        }


def robustness_row(
    scenario: str,
    robustness_panel: str,
    outcome: str,
    outcome_label: str,
    construction: str,
    data: pd.DataFrame,
    group_id: str = "all",
    group_label: str = "Todos",
    age_definition: str = "",
    age_definition_label: str = "",
) -> dict[str, object]:
    est = estimate_one(data, outcome)
    return {
        "scenario_id": scenario,
        "scenario_label": SCENARIO_LABELS_PT[scenario],
        "robustness_panel": robustness_panel,
        "age_definition": age_definition,
        "age_definition_label": age_definition_label,
        "group_id": group_id,
        "group_label": group_label,
        "outcome": outcome,
        "outcome_label": outcome_label,
        "construction": construction,
        "model": f"Y_ot ~ post_treat + {SECTION4_CONTROLS} | cbo_4d + periodo",
        "cluster": "cbo_4d",
        **est,
    }


def build_table4(panel: pd.DataFrame, classification: pd.DataFrame, table1: pd.DataFrame) -> pd.DataFrame:
    log("Building Table 4 outcome-construction robustness...")
    base = build_table4_base_panel(panel)
    classification = classification.copy()
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    rows = []

    for scenario in REQUIRED_SCENARIOS:
        scenario_base = apply_scenario_to_panel(base, classification, scenario)
        for outcome, label, note in TABLE4_WAGE_OUTCOMES:
            rows.append(
                robustness_row(
                    scenario,
                    "Painel A: Salário",
                    outcome,
                    label,
                    note,
                    scenario_base,
                )
            )
        for outcome, label, note in TABLE4_SALDO_OUTCOMES:
            rows.append(
                robustness_row(
                    scenario,
                    "Painel B: Saldo",
                    outcome,
                    label,
                    note,
                    scenario_base,
                )
            )

    age_raw, age_pre = aggregate_raw_age_binary_robustness()
    controls = base_controls(panel)
    group_labels = {
        str(spec["young_group"]): str(spec["young_label"])
        for spec in AGE_BINARY_SPECS
    }
    group_labels.update(
        {
            str(spec["non_young_group"]): str(spec["non_young_label"])
            for spec in AGE_BINARY_SPECS
        }
    )

    for scenario in REQUIRED_SCENARIOS:
        assignments = scenario_assignments(classification, scenario)
        scenario_base = controls.merge(assignments, on="cbo_4d", how="inner")
        for spec in AGE_BINARY_SPECS:
            definition = str(spec["definition"])
            definition_label = str(spec["definition_label"])
            for group_id in [str(spec["young_group"]), str(spec["non_young_group"])]:
                group_raw = age_raw[
                    (age_raw["age_definition"].eq(definition))
                    & (age_raw["group_id"].eq(group_id))
                ].copy()
                group_pre = age_pre[
                    (age_pre["age_definition"].eq(definition))
                    & (age_pre["group_id"].eq(group_id))
                ][["cbo_4d", "age_pre_adm_mean"]].copy()
                merged = scenario_base.merge(
                    group_raw[
                        [
                            "cbo_4d",
                            "ano",
                            "mes",
                            "admissoes",
                            "desligamentos",
                            "saldo",
                            "ln_admissoes",
                            "ln_desligamentos",
                            "ln_salario_real_adm",
                        ]
                    ],
                    on=["cbo_4d", "ano", "mes"],
                    how="left",
                )
                for col in ["admissoes", "desligamentos", "saldo", "ln_admissoes", "ln_desligamentos"]:
                    merged[col] = merged[col].fillna(0)
                for col in ["admissoes", "desligamentos", "saldo"]:
                    merged[col] = pd.to_numeric(merged[col], errors="coerce")
                merged = merged.merge(group_pre, on="cbo_4d", how="left")
                age_pre_values = pd.to_numeric(merged["age_pre_adm_mean"], errors="coerce").to_numpy(
                    dtype=float,
                    na_value=np.nan,
                )
                age_saldo_values = pd.to_numeric(merged["saldo"], errors="coerce").to_numpy(
                    dtype=float,
                    na_value=np.nan,
                )
                merged["saldo_per_pre_adm"] = np.where(
                    age_pre_values > 0,
                    age_saldo_values / age_pre_values,
                    np.nan,
                )
                merged["post_treat"] = merged["post"].astype(int) * merged["scenario_treat"].astype(int)
                for outcome in TABLE4_AGE_OUTCOMES:
                    rows.append(
                        robustness_row(
                            scenario,
                            "Painel C: Idade binária",
                            outcome,
                            OUTCOME_LABELS_PT[outcome],
                            "Outcome reconstruído nos microdados por definição binária de idade.",
                            merged,
                            group_id=group_id,
                            group_label=group_labels[group_id],
                            age_definition=definition,
                            age_definition_label=definition_label,
                        )
                    )

    results = pd.DataFrame(rows)
    results["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in results.itertuples()]
    results["scenario_order"] = results["scenario_id"].map({name: i for i, name in enumerate(REQUIRED_SCENARIOS)})
    panel_order = {
        "Painel A: Salário": 1,
        "Painel B: Saldo": 2,
        "Painel C: Idade binária": 3,
    }
    results["robustness_panel_order"] = results["robustness_panel"].map(panel_order)
    outcome_order = {
        ("Painel A: Salário", outcome): i
        for i, (outcome, _label, _note) in enumerate(TABLE4_WAGE_OUTCOMES)
    }
    outcome_order.update(
        {
            ("Painel B: Saldo", outcome): i
            for i, (outcome, _label, _note) in enumerate(TABLE4_SALDO_OUTCOMES)
        }
    )
    outcome_order.update(
        {
            ("Painel C: Idade binária", outcome): i
            for i, outcome in enumerate(TABLE4_AGE_OUTCOMES)
        }
    )
    age_definition_order = {
        str(spec["definition"]): i
        for i, spec in enumerate(AGE_BINARY_SPECS)
    }
    age_group_order = {}
    for spec in AGE_BINARY_SPECS:
        age_group_order[str(spec["young_group"])] = 0
        age_group_order[str(spec["non_young_group"])] = 1
    results["robustness_outcome_order"] = [
        outcome_order.get((r.robustness_panel, r.outcome), 999)
        for r in results.itertuples()
    ]
    results["age_definition_order"] = results["age_definition"].map(age_definition_order).fillna(999).astype(int)
    results["age_group_order"] = results["group_id"].map(age_group_order).fillna(999).astype(int)
    results.to_csv(SECTION4_TABLES / "table4_outcome_robustness_long.csv", index=False)
    validate_table4(results, table1)
    write_table4_outputs(results)
    return results


def write_table4_outputs(results: pd.DataFrame) -> None:
    table4a = results[results["robustness_panel"].eq("Painel A: Salário")].copy()
    table4a = table4a.sort_values(["scenario_order", "robustness_outcome_order"])
    table4a.to_csv(SECTION4_TABLES / "table4a_wage_construction.csv", index=False)
    md4a = table4a.assign(
        Cenario=table4a["scenario_label"],
        Construcao=table4a["outcome_label"],
        Estimativa=table4a["estimate_se"],
        p=table4a["p_value"].map(lambda v: fmt_number(v, 3)),
        N=table4a["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=table4a["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        SECTION4_TABLES / "table4a_wage_construction.md",
        "Tabela 4A. Robustez de construção salarial",
        md4a,
        ["Cenario", "Construcao", "Estimativa", "p", "N", "CBOs"],
    )

    table4b = results[results["robustness_panel"].eq("Painel B: Saldo")].copy()
    table4b = table4b.sort_values(["scenario_order", "robustness_outcome_order"])
    table4b.to_csv(SECTION4_TABLES / "table4b_saldo_scaling.csv", index=False)
    md4b = table4b.assign(
        Cenario=table4b["scenario_label"],
        Construcao=table4b["outcome_label"],
        Estimativa=table4b["estimate_se"],
        p=table4b["p_value"].map(lambda v: fmt_number(v, 3)),
        N=table4b["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=table4b["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        SECTION4_TABLES / "table4b_saldo_scaling.md",
        "Tabela 4B. Robustez de escala do saldo",
        md4b,
        ["Cenario", "Construcao", "Estimativa", "p", "N", "CBOs"],
    )

    table4c = results[results["robustness_panel"].eq("Painel C: Idade binária")].copy()
    table4c = table4c.sort_values(
        ["scenario_order", "age_definition_order", "age_group_order", "robustness_outcome_order"]
    )
    table4c.to_csv(SECTION4_TABLES / "table4c_age_binary_robustness.csv", index=False)
    md4c = table4c.assign(
        Cenario=table4c["scenario_label"],
        Definicao=table4c["age_definition_label"],
        Grupo=table4c["group_label"],
        Resultado=table4c["outcome_label"],
        Estimativa=table4c["estimate_se"],
        p=table4c["p_value"].map(lambda v: fmt_number(v, 3)),
        N=table4c["n_obs"].map(lambda v: fmt_number(v, 0)),
        CBOs=table4c["n_cbo"].map(lambda v: fmt_number(v, 0)),
    )
    write_markdown_table(
        SECTION4_TABLES / "table4c_age_binary_robustness.md",
        "Tabela 4C. Robustez de idade binária",
        md4c,
        ["Cenario", "Definicao", "Grupo", "Resultado", "Estimativa", "p", "N", "CBOs"],
    )


def validate_table4(results: pd.DataFrame, table1: pd.DataFrame) -> None:
    required_cols = {"stars", "p_value", "coef", "se", "n_obs", "n_cbo"}
    missing_cols = sorted(required_cols - set(results.columns))
    if missing_cols:
        raise RuntimeError(f"Table 4 is missing required columns: {missing_cols}.")
    if set(results["scenario_id"].dropna().unique()) != set(REQUIRED_SCENARIOS):
        raise RuntimeError("Table 4 does not contain exactly the four required scenarios.")

    expected_rows = len(REQUIRED_SCENARIOS) * (
        len(TABLE4_WAGE_OUTCOMES)
        + len(TABLE4_SALDO_OUTCOMES)
        + len(AGE_BINARY_SPECS) * 2 * len(TABLE4_AGE_OUTCOMES)
    )
    if len(results) != expected_rows:
        raise RuntimeError(f"Table 4 should contain {expected_rows} rows; found {len(results)}.")
    if not results["result_status"].eq("estimated").all():
        failed = results.loc[
            ~results["result_status"].eq("estimated"),
            ["scenario_id", "robustness_panel", "outcome", "group_id", "result_status", "error"],
        ]
        raise RuntimeError("Table 4 contains failed estimations:\n" + failed.to_string(index=False))

    baseline_salary = results[
        results["scenario_id"].eq("baseline_mte2d_top20_vs_rest")
        & results["robustness_panel"].eq("Painel A: Salário")
        & results["outcome"].eq("ln_salario_adm")
    ]
    table1_salary = table1[table1["outcome"].eq("ln_salario_adm")]
    if baseline_salary.empty or table1_salary.empty:
        raise RuntimeError("Could not validate Table 4 baseline wage against Table 1.")
    for col in ["coef", "se", "p_value"]:
        diff = abs(float(baseline_salary[col].iloc[0]) - float(table1_salary[col].iloc[0]))
        if diff > 1e-6:
            raise RuntimeError(f"Table 4 baseline wage parity failed for {col}: {diff}")


def build_table3(panel: pd.DataFrame, classification: pd.DataFrame) -> pd.DataFrame:
    raw = aggregate_raw_heterogeneity()
    controls = base_controls(panel)
    classification = classification.copy()
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    all_results = []

    for scenario in REQUIRED_SCENARIOS:
        role_col = f"role__{scenario}"
        included = classification[classification[role_col].isin(["treated", "control"])][["cbo_4d", role_col]].copy()
        included = included.rename(columns={role_col: "scenario_role"})
        included["scenario_treat"] = (included["scenario_role"] == "treated").astype(int)
        scenario_base = controls.merge(included, on="cbo_4d", how="inner")
        expected_treated = set(included.loc[included["scenario_treat"] == 1, "cbo_4d"])
        expected_control = set(included.loc[included["scenario_treat"] == 0, "cbo_4d"])

        for dimension, spec in DIMENSIONS_AUDIT.items():
            for group_id, group_label in spec["groups"]:
                group_raw = raw[(raw["dimension"] == dimension) & (raw["group_id"] == group_id)].copy()
                merged = scenario_base.merge(
                    group_raw[
                        [
                            "cbo_4d",
                            "ano",
                            "mes",
                            "admissoes",
                            "desligamentos",
                            "saldo",
                            "salario_real_adm",
                            "ln_admissoes",
                            "ln_desligamentos",
                            "ln_salario_real_adm",
                        ]
                    ],
                    on=["cbo_4d", "ano", "mes"],
                    how="left",
                )
                for col in ["admissoes", "desligamentos", "saldo", "ln_admissoes", "ln_desligamentos"]:
                    merged[col] = merged[col].fillna(0)
                merged["post_treat"] = merged["post"].astype(int) * merged["scenario_treat"].astype(int)

                for outcome in OUTCOME_ORDER:
                    est = estimate_one(merged, outcome)
                    used = merged.dropna(
                        subset=[outcome, "post_treat", *SECTION4_CONTROL_COLUMNS]
                    )
                    observed = set(used["cbo_4d"].unique())
                    missing_treated = len(expected_treated - observed)
                    missing_control = len(expected_control - observed)
                    if missing_treated or missing_control:
                        reason = (
                            f"{missing_treated} treated and {missing_control} control CBOs have no non-missing "
                            f"{OUTCOME_LABELS_PT[outcome]} observations for {group_label} after raw reconstruction."
                        )
                    else:
                        reason = "No treated/control CBO loss for this outcome and group."
                    all_results.append(
                        {
                            "scenario_id": scenario,
                            "scenario_label": SCENARIO_LABELS_PT[scenario],
                            "dimension": dimension,
                            "panel": spec["panel"],
                            "group_id": group_id,
                            "group_label": group_label,
                            "outcome": outcome,
                            "outcome_label": OUTCOME_LABELS_PT[outcome],
                            "model": f"Y_ogt ~ post_treat + {SECTION4_CONTROLS} | cbo_4d + periodo",
                            "cluster": "cbo_4d",
                            "expected_treated_cbo": len(expected_treated),
                            "expected_control_cbo": len(expected_control),
                            "missing_treated_cbo": missing_treated,
                            "missing_control_cbo": missing_control,
                            "sample_loss_reason": reason,
                            **est,
                        }
                    )

    results = pd.DataFrame(all_results)
    results["estimate_se"] = [estimate_cell(r.coef, r.se, r.stars) for r in results.itertuples()]
    results.to_csv(SECTION4_TABLES / "table3_heterogeneity_all_scenarios_long.csv", index=False)
    validate_table3(results)
    for scenario in REQUIRED_SCENARIOS:
        scenario_results = results[
            (results["scenario_id"] == scenario)
            & (results["dimension"].isin(DIMENSIONS_MAIN.keys()))
        ].copy()
        out_base = SECTION4_TABLES / f"table3_heterogeneity_{scenario}"
        scenario_results.to_csv(out_base.with_suffix(".csv"), index=False)
        md = scenario_results.assign(
            Painel=scenario_results["panel"],
            Grupo=scenario_results["group_label"],
            Resultado=scenario_results["outcome_label"],
            Estimativa=scenario_results["estimate_se"],
            p=scenario_results["p_value"].map(lambda v: fmt_number(v, 3)),
            N=scenario_results["n_obs"].map(lambda v: fmt_number(v, 0)),
            CBOs=scenario_results["n_cbo"].map(lambda v: fmt_number(v, 0)),
        )
        write_markdown_table(
            out_base.with_suffix(".md"),
            f"Tabela 3. Heterogeneidade sociodemográfica - {SCENARIO_LABELS_PT[scenario]}",
            md,
            ["Painel", "Grupo", "Resultado", "Estimativa", "p", "N", "CBOs"],
        )
    return results


def validate_table3(results: pd.DataFrame) -> None:
    main = results[results["dimension"].isin(DIMENSIONS_MAIN.keys())]
    for scenario in REQUIRED_SCENARIOS:
        rows = main[main["scenario_id"] == scenario]
        outcomes = set(rows["outcome"].dropna().unique())
        if outcomes != set(OUTCOME_ORDER):
            raise RuntimeError(f"Table 3 for {scenario} does not contain all four outcomes.")
    lost = results[(results["missing_treated_cbo"] > 0) | (results["missing_control_cbo"] > 0)]
    if not lost.empty and lost["sample_loss_reason"].isna().any():
        raise RuntimeError("Some raw-reconstruction CBO loss rows lack sample_loss_reason.")
    if "race_color" not in set(main["dimension"]):
        raise RuntimeError("Main heterogeneity package does not include race_color.")


def write_report(table1: pd.DataFrame, table2: pd.DataFrame, table4: pd.DataFrame) -> None:
    report_path = SECTION4_DIR / "section4_results_report.md"
    table1_md = (SECTION4_TABLES / "table1_main_effects.md").read_text(encoding="utf-8")
    table2_md = (SECTION4_TABLES / "table2_exposure_types.md").read_text(encoding="utf-8")
    table4a_md = (SECTION4_TABLES / "table4a_wage_construction.md").read_text(encoding="utf-8")
    table4b_md = (SECTION4_TABLES / "table4b_saldo_scaling.md").read_text(encoding="utf-8")
    table4c_md = (SECTION4_TABLES / "table4c_age_binary_robustness.md").read_text(encoding="utf-8")
    table3_sections = []
    for scenario in REQUIRED_SCENARIOS:
        path = SECTION4_TABLES / f"table3_heterogeneity_{scenario}.md"
        table3_sections.append(path.read_text(encoding="utf-8"))

    text = f"""# Pacote De Resultados Da Seção 4

Este relatório consolida os resultados empíricos gerados por `src/scripts/build_dissertation_section4_results.py`.
A especificação principal é `baseline_mte2d_top20_vs_rest` (MTE 20% vs demais). As decomposições conceituais usam a nova regra OIT média + SD agregada dos destinos ISCO-08: `trat_alta_expo` inclui Gradients 3-4, `trat_media_expo` inclui Gradients 1-2 e `trat_expostos` inclui Gradients 1-4. Nesses três recortes, o controle é `Not Exposed`; `Minimal Exposure`, `No score` e CBOs sem MTE ficam fora da estimação.

## 4.1 Resultado Principal Agregado

![Figura 1. Estudo de eventos agregado](figures/figure1_event_study_aggregate.png)

{table1_md}

## 4.2 Decomposição Conceitual

{table2_md}

## 4.3 Robustez De Construção Dos Outcomes

As tabelas abaixo testam se os resultados dependem da construção dos outcomes. A Tabela 4A compara `log(mean wage)`, `mean(log wage)` e `log(median wage)`; a Tabela 4B compara saldo em nível com saldo normalizado e `asinh(saldo)`; a Tabela 4C compara a divisão etária em dois cortes binários. Essas estimativas são tratadas como robustez metodológica, não como nova especificação principal.

{table4a_md}

{table4b_md}

{table4c_md}

## 4.4 Heterogeneidade Sociodemográfica

As tabelas abaixo são estimadas a partir dos microdados CAGED brutos reconstruídos por CBO, período, dimensão sociodemográfica e grupo. Cada tabela contém os painéis A-E: renda, escolaridade, idade, sexo e raça/cor. Os controles gerais são idade média, percentual de mulheres, percentual com superior e percentual de trabalhadores negros (pretos+pardos) nas admissões do painel agregado.

A codificação de raça/cor segue o leiaute eSocial/Novo CAGED observado nos microdados: 1 = branca, 2 = preta, 3 = parda, 4 = amarela, 5 = indígena, 6 = não informada. O código 9, quando aparece nos microdados locais, é tratado como não identificado e agregado a "não informada/identificada".

{chr(10).join(table3_sections)}

## Arquivos De Auditoria

- `tables/table3_heterogeneity_all_scenarios_long.csv` inclui todos os cenários e todas as dimensões principais, inclusive raça/cor.
- `tables/table4_outcome_robustness_long.csv` inclui as robustezes de salário, saldo e idade binária.
- Linhas com perda de CBO tratado ou controle registram o motivo em `sample_loss_reason`.
- Todas as tabelas usam a convenção: * p<0.10; ** p<0.05; *** p<0.01.
"""
    report_path.write_text(text, encoding="utf-8")


def validate_outputs() -> None:
    required = [
        SECTION4_DIR / "section4_results_report.md",
        SECTION4_FIGURES / "figure1_event_study_aggregate.png",
        SECTION4_TABLES / "table1_main_effects.md",
        SECTION4_TABLES / "table1_main_effects.csv",
        SECTION4_TABLES / "table2_exposure_types.md",
        SECTION4_TABLES / "table2_exposure_types.csv",
        SECTION4_TABLES / "table3_heterogeneity_all_scenarios_long.csv",
        SECTION4_TABLES / "table4_outcome_robustness_long.csv",
        SECTION4_TABLES / "table4a_wage_construction.md",
        SECTION4_TABLES / "table4a_wage_construction.csv",
        SECTION4_TABLES / "table4b_saldo_scaling.md",
        SECTION4_TABLES / "table4b_saldo_scaling.csv",
        SECTION4_TABLES / "table4c_age_binary_robustness.md",
        SECTION4_TABLES / "table4c_age_binary_robustness.csv",
    ]
    for scenario in REQUIRED_SCENARIOS:
        required.extend(
            [
                SECTION4_TABLES / f"table3_heterogeneity_{scenario}.md",
                SECTION4_TABLES / f"table3_heterogeneity_{scenario}.csv",
            ]
        )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing required Section 4 artifacts:\n" + "\n".join(missing))

    markdown_tables = [path for path in required if path.suffix == ".md"]
    for path in markdown_tables:
        text = path.read_text(encoding="utf-8")
        if "* p<0.10" not in text or "** p<0.05" not in text or "*** p<0.01" not in text:
            raise RuntimeError(f"{path} does not contain the significance-star legend.")

    csv_tables = [path for path in required if path.suffix == ".csv" and "table3_heterogeneity_all" not in path.name]
    for path in csv_tables:
        df = pd.read_csv(path)
        if "stars" not in df.columns:
            raise RuntimeError(f"{path} has no stars column.")
    long = pd.read_csv(SECTION4_TABLES / "table3_heterogeneity_all_scenarios_long.csv")
    validate_table3(long)
    table1 = pd.read_csv(SECTION4_TABLES / "table1_main_effects.csv")
    table4 = pd.read_csv(SECTION4_TABLES / "table4_outcome_robustness_long.csv")
    validate_table4(table4, table1)
    report = (SECTION4_DIR / "section4_results_report.md").read_text(encoding="utf-8")
    for required_text in [
        "## 4.3 Robustez De Construção Dos Outcomes",
        "Tabela 4A. Robustez de construção salarial",
        "Tabela 4B. Robustez de escala do saldo",
        "Tabela 4C. Robustez de idade binária",
        "## 4.4 Heterogeneidade Sociodemográfica",
    ]:
        if required_text not in report:
            raise RuntimeError(f"Section 4 report is missing required Table 4 text: {required_text}")


def main() -> None:
    ensure_directories()
    clean_generated_section4_tables()
    panel, did, classification, scenario_results, _baseline_validation = load_inputs()
    log("Building Figure 1...")
    build_figure1()
    log("Building Tables 1 and 2...")
    table1 = build_table1(did)
    table2 = build_table2(scenario_results)
    log("Building Table 4 outcome-construction robustness...")
    table4 = build_table4(panel, classification, table1)
    log("Building Table 3 heterogeneity package from raw CAGED...")
    build_table3(panel, classification)
    log("Writing Portuguese report...")
    write_report(table1, table2, table4)
    validate_outputs()
    log(f"Section 4 package written to {SECTION4_DIR}")


if __name__ == "__main__":
    main()
