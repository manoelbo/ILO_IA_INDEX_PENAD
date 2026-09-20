"""Configuration for the final Section 4 event-study package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = ROOT / "data" / "raw"
DATA_OUTPUT = ROOT / "data" / "output"
DATA_PROCESSED = ROOT / "data" / "processed"
SCENARIO_GRID = ROOT / "outputs" / "treatment_scenario_grid" / "scenario_cbo_classification.csv"
PANEL_PATH = DATA_OUTPUT / "painel_2b_ready.parquet"
IPCA_PATH = DATA_PROCESSED / "ipca_mensal.parquet"
OUTPUT_ROOT = ROOT / "outputs" / "dissertation_section4"
FINAL_OUTPUT = OUTPUT_ROOT / "final_event_study"
TABLE_DIR = FINAL_OUTPUT / "tables"
FIGURE_DIR = FINAL_OUTPUT / "figures"
AUDIT_DIR = FINAL_OUTPUT / "audit"
REPORT_PATH = OUTPUT_ROOT / "section4_event_study_final_report.md"
REAL_WAGE_REPORT_PATH = OUTPUT_ROOT / "section4_real_wage_results.md"

EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"
MATCHED_MTE_STATUS = "matched_official_mte"
REFERENCE_PERIOD = -1
BIN_MIN = -12
BIN_MAX = 24
TREATMENT_PERIOD = 2022 * 100 + 12
PLACEBO_PERIOD = 2021 * 100 + 12
VCOV = {"CRV1": "cbo_4d"}

CONTROL_COLUMNS = [
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
]
CONTROL_TERMS = " + ".join(CONTROL_COLUMNS)

MAIN_OUTCOMES = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Demissões (log)",
    "ln_salario_adm": "Salário de admissão (log)",
}
COMPLEMENTARY_OUTCOMES = {
    "ln_salario_desl": "Salário de demissão (log)",
}
ALL_OUTCOMES = {**MAIN_OUTCOMES, **COMPLEMENTARY_OUTCOMES}
REAL_MAIN_OUTCOMES = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Demissões (log)",
    "ln_salario_real_adm": "Salário real de admissão (log)",
}
REAL_COMPLEMENTARY_OUTCOMES = {
    "ln_salario_real_desl": "Salário real de demissão (log)",
}
REAL_ALL_OUTCOMES = {**REAL_MAIN_OUTCOMES, **REAL_COMPLEMENTARY_OUTCOMES}
REAL_HETEROGENEITY_OUTCOMES = {
    "ln_salario_real_adm": "Salário real de admissão (log)",
}
NET_FLOW_OUTCOMES = {
    "asinh_saldo": "Saldo líquido (asinh)",
    "saldo_per_pre_adm": "Saldo líquido / admissões pré",
    "saldo_flow_rate": "Saldo líquido / fluxo total",
}
NET_FLOW_EVENT_OUTCOMES = {
    "asinh_saldo": "Saldo líquido (asinh)",
    "saldo_per_pre_adm": "Saldo líquido / admissões pré",
}

SALARIO_MINIMO = {
    2021: 1100,
    2022: 1212,
    2023: 1320,
    2024: 1412,
    2025: 1518,
}


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    label: str
    treatment: str
    control: str
    term: str = "post_treat"
    weight: str | None = None
    cluster: str = "cbo_4d"
    sample_kind: str = "binary"


MAIN_SCENARIO = ScenarioSpec(
    scenario_id="main_strict",
    label="Modelo base: expostos OIT (G1-G4) vs Not Exposed",
    treatment="Exposed: Gradient 1-4",
    control="Not Exposed",
)
