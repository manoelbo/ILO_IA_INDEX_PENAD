"""Configuration for the Section 4 connectivity extension."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATA_OUTPUT = ROOT / "data" / "output"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_RAW = ROOT / "data" / "raw"

MUNICIPAL_PANEL_PATH = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
CONNECTIVITY_PANEL_PATH = DATA_OUTPUT / "painel_section4_connectivity_ready.parquet"
SCENARIO_GRID = ROOT / "outputs" / "treatment_scenario_grid" / "scenario_cbo_classification.csv"
IPCA_PATH = DATA_PROCESSED / "ipca_mensal.parquet"
CANARIES_AGE_CACHE = DATA_PROCESSED / "section4_connectivity_canaries_age_outcomes.parquet"

OUTPUT_ROOT = ROOT / "outputs" / "dissertation_section4" / "connectivity_extension"
TABLE_DIR = OUTPUT_ROOT / "tables"
FIGURE_DIR = OUTPUT_ROOT / "figures"
AUDIT_DIR = OUTPUT_ROOT / "audit"
REPORT_PATH = OUTPUT_ROOT / "section4_connectivity_report.md"

EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"
MATCHED_MTE_STATUS = "matched_official_mte"
TREATMENT_PERIOD = 2022 * 100 + 12
PLACEBO_PERIOD = 2021 * 100 + 12
REFERENCE_PERIOD = -1
BIN_MIN = -12
BIN_MAX = 24

MAIN_SCENARIO_ID = "connectivity_main_strict"

FLOW_OUTCOMES = {
    "admissoes": "Admissões",
    "desligamentos": "Demissões",
}

WAGE_OUTCOMES = {
    "ln_salario_real_adm": "Salário real de admissão (log)",
    "ln_salario_real_desl": "Salário real de demissão (log)",
}

LOG_FLOW_OUTCOMES = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Demissões (log)",
}

NET_FLOW_OUTCOMES = {
    "asinh_saldo": "Saldo líquido (asinh)",
    "saldo_per_pre_cell_adm": "Saldo líquido / admissões pré da célula",
}

MAIN_OUTCOMES = {**FLOW_OUTCOMES, **WAGE_OUTCOMES}

FE_SPECS = {
    "legacy": {
        "label": "Legado comparável: CBO + UF-mês",
        "fe": "cbo_4d + uf_periodo",
        "extra_terms": ["post_treat", "post_high_connect", "treat_high_connect"],
        "cluster": "id_municipio",
    },
    "cell_local": {
        "label": "Célula local: CBO-município + mês",
        "fe": "cbo_municipio + periodo",
        "extra_terms": ["post_treat", "post_high_connect"],
        "cluster": "id_municipio",
    },
    "strong": {
        "label": "Forte: CBO-município + CBO-mês + UF-mês",
        "fe": "cbo_municipio + cbo_periodo + uf_periodo",
        "extra_terms": ["post_high_connect"],
        "cluster": "id_municipio",
    },
}

CONNECTIVITY_PROXIES = {
    "median": {
        "label": "Alta conectividade: penetração acima da mediana",
        "high_col": "high_connect",
        "sample_filter": None,
    },
    "q75_q25": {
        "label": "Extremos de conectividade: Q75 vs Q25",
        "high_col": "high_connect_q75",
        "sample_filter": "connectivity_extreme_sample",
    },
    "fiber": {
        "label": "Alta fibra: % fibra acima da mediana",
        "high_col": "high_fiber",
        "sample_filter": None,
    },
}

DEMOGRAPHIC_OUTCOMES = {
    "ln_salario_real_jovem": "Salário real admissão: jovens <=29",
    "ln_salario_real_intermediario": "Salário real admissão: 30-49",
    "ln_salario_real_senior": "Salário real admissão: 50+",
    "ln_salario_real_mulher": "Salário real admissão: mulheres",
    "ln_salario_real_homem": "Salário real admissão: homens",
    "ln_salario_real_negro": "Salário real admissão: pretos/pardos",
    "ln_salario_real_superior": "Salário real admissão: superior",
    "ln_admissoes_jovem": "Admissões jovens <=29 (log)",
    "ln_admissoes_mulher": "Admissões mulheres (log)",
    "ln_admissoes_negro": "Admissões pretos/pardos (log)",
}

CANARIES_AGE_OUTCOMES = {
    "ln_adm_age_22_25": "Admissões 22-25 (log)",
    "ln_sal_real_age_22_25": "Salário real admissão 22-25 (log)",
    "ln_adm_age_26_30": "Admissões 26-30 (log)",
    "ln_sal_real_age_26_30": "Salário real admissão 26-30 (log)",
    "ln_adm_age_31_34": "Admissões 31-34 (log)",
    "ln_sal_real_age_31_34": "Salário real admissão 31-34 (log)",
    "ln_adm_age_35_40": "Admissões 35-40 (log)",
    "ln_sal_real_age_35_40": "Salário real admissão 35-40 (log)",
    "ln_adm_age_41_49": "Admissões 41-49 (log)",
    "ln_sal_real_age_41_49": "Salário real admissão 41-49 (log)",
    "ln_adm_age_50_plus": "Admissões 50+ (log)",
    "ln_sal_real_age_50_plus": "Salário real admissão 50+ (log)",
}

CANARIES_AGE_GROUPS = {
    "age_22_25": (22, 25),
    "age_26_30": (26, 30),
    "age_31_34": (31, 34),
    "age_35_40": (35, 40),
    "age_41_49": (41, 49),
    "age_50_plus": (50, None),
}
