#!/usr/bin/env python3
"""Build wage event studies by sociodemographic profile for Section 4.

This diagnostic package reconstructs nominal admission wages from raw CAGED
microdata, crosses them with the seven already-defined treatment contrasts,
and estimates dynamic effects only for ``ln_salario_adm``. It intentionally
does not rebuild the treatment scenario grid or alter the Stage 2a/2b panels.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfixest as pf
from scipy.stats import chi2


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)


ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_OUTPUT = ROOT / "data" / "output"
PANEL_PATH = DATA_OUTPUT / "painel_2b_ready.parquet"
SCENARIO_GRID_PATH = ROOT / "outputs" / "treatment_scenario_grid" / "scenario_cbo_classification.csv"
OUTPUT_DIR = ROOT / "outputs" / "dissertation_section4" / "event_study_profiles"

EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"
TREATMENT_YEAR = 2022
TREATMENT_MONTH = 12
REFERENCE_PERIOD = -1
BIN_MIN = -12
BIN_MAX = 24
EVENT_TIMES = list(range(BIN_MIN, BIN_MAX + 1))
VCOV_SPEC = {"CRV1": "cbo_4d"}

OUTCOME = "ln_salario_adm"
OUTCOME_LABEL_PT = "Salário nominal de admissão (log)"
CONTROL_COLUMNS = [
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
]
CONTROL_TERMS = " + ".join(CONTROL_COLUMNS)

SALARIO_MINIMO = {
    2021: 1100,
    2022: 1212,
    2023: 1320,
    2024: 1412,
    2025: 1518,
}

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

PROFILE_DIMENSIONS = {
    "income": {
        "panel": "Painel A: Renda",
        "label_pt": "Renda ocupacional pré-tratamento",
        "groups": [
            ("low_income", "Baixa renda: até 2 salários mínimos"),
            ("middle_income", "Média renda: mais de 2 até 5 salários mínimos"),
            ("high_income", "Alta renda: mais de 5 salários mínimos"),
        ],
    },
    "education": {
        "panel": "Painel B: Escolaridade",
        "label_pt": "Escolaridade",
        "groups": [
            ("fundamental_or_less", "Fundamental ou menos"),
            ("high_school", "Médio"),
            ("higher_education", "Superior"),
        ],
    },
    "age": {
        "panel": "Painel C: Idade",
        "label_pt": "Idade",
        "groups": [
            ("age_14_24", "14-24"),
            ("age_25_34", "25-34"),
            ("age_35_59", "35-59"),
            ("age_60_plus", "60+"),
        ],
    },
    "sex": {
        "panel": "Painel D: Sexo",
        "label_pt": "Sexo",
        "groups": [
            ("men", "Homens"),
            ("women", "Mulheres"),
        ],
    },
    "race_color": {
        "panel": "Painel E: Raça/cor",
        "label_pt": "Raça/cor",
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

VALID_GRADIENTS = {
    "Not Exposed",
    "Minimal Exposure",
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
    "No score",
}
EXPOSED_G1_G2 = {"Exposed: Gradient 1", "Exposed: Gradient 2"}
EXPOSED_G3_G4 = {"Exposed: Gradient 3", "Exposed: Gradient 4"}
EXPOSED_G1_G4 = EXPOSED_G1_G2 | EXPOSED_G3_G4


@dataclass(frozen=True)
class Contrast:
    scenario_id: str
    label_pt: str
    family: str
    control_type: str
    treatment_definition_pt: str
    control_definition_pt: str
    treatment_gradients: tuple[str, ...] = ()
    control_gradients: tuple[str, ...] = ()
    role_column: str | None = None


CONTRASTS = [
    Contrast(
        scenario_id="baseline_mte2d_top20_vs_rest",
        label_pt="Baseline MTE top 20% vs demais CBOs válidos",
        family="baseline",
        control_type="baseline",
        treatment_definition_pt="CBOs no top 20% do score MTE 2d, usando a definição principal já gerada.",
        control_definition_pt="Demais CBOs com score MTE 2d válido na classificação baseline existente.",
        role_column="role__baseline_mte2d_top20_vs_rest",
    ),
    Contrast(
        scenario_id="trat_alta_expo_strict_control",
        label_pt="Alta exposição OIT (G3-G4) vs controle estrito",
        family="trat_alta_expo",
        control_type="strict_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 3 ou Exposed: Gradient 4.",
        control_definition_pt="Controle estrito: CBOs classificados como Not Exposed.",
        treatment_gradients=tuple(sorted(EXPOSED_G3_G4)),
        control_gradients=("Not Exposed",),
    ),
    Contrast(
        scenario_id="trat_alta_expo_broad_control",
        label_pt="Alta exposição OIT (G3-G4) vs controle amplo",
        family="trat_alta_expo",
        control_type="broad_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 3 ou Exposed: Gradient 4.",
        control_definition_pt="Controle amplo: CBOs classificados como Not Exposed ou Minimal Exposure.",
        treatment_gradients=tuple(sorted(EXPOSED_G3_G4)),
        control_gradients=("Not Exposed", "Minimal Exposure"),
    ),
    Contrast(
        scenario_id="trat_media_expo_strict_control",
        label_pt="Média exposição OIT (G1-G2) vs controle estrito",
        family="trat_media_expo",
        control_type="strict_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1 ou Exposed: Gradient 2.",
        control_definition_pt="Controle estrito: CBOs classificados como Not Exposed.",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G2)),
        control_gradients=("Not Exposed",),
    ),
    Contrast(
        scenario_id="trat_media_expo_broad_control",
        label_pt="Média exposição OIT (G1-G2) vs controle amplo",
        family="trat_media_expo",
        control_type="broad_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1 ou Exposed: Gradient 2.",
        control_definition_pt="Controle amplo: CBOs classificados como Not Exposed ou Minimal Exposure.",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G2)),
        control_gradients=("Not Exposed", "Minimal Exposure"),
    ),
    Contrast(
        scenario_id="trat_expostos_strict_control",
        label_pt="Expostos OIT (G1-G4) vs controle estrito",
        family="trat_expostos",
        control_type="strict_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1, 2, 3 ou 4.",
        control_definition_pt="Controle estrito: CBOs classificados como Not Exposed.",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G4)),
        control_gradients=("Not Exposed",),
    ),
    Contrast(
        scenario_id="trat_expostos_broad_control",
        label_pt="Expostos OIT (G1-G4) vs controle amplo",
        family="trat_expostos",
        control_type="broad_control",
        treatment_definition_pt="CBOs classificados como Exposed: Gradient 1, 2, 3 ou 4.",
        control_definition_pt="Controle amplo: CBOs classificados como Not Exposed ou Minimal Exposure.",
        treatment_gradients=tuple(sorted(EXPOSED_G1_G4)),
        control_gradients=("Not Exposed", "Minimal Exposure"),
    ),
]


def log(message: str) -> None:
    print(message, flush=True)


def fmt_number(value: object, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}".replace(".", ",")
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    if df.empty:
        return "_Sem linhas disponíveis._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in df[columns].iterrows():
        values = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def event_dummy_name(t: int) -> str:
    return f"did_tm{-t}" if t < 0 else f"did_t{t}"


def expected_profile_rows() -> list[tuple[str, str, str, str]]:
    rows = []
    for dimension, spec in PROFILE_DIMENSIONS.items():
        for group_id, group_label in spec["groups"]:
            rows.append((dimension, spec["label_pt"], group_id, group_label))
    return rows


def ensure_inputs() -> None:
    required = [
        PANEL_PATH,
        SCENARIO_GRID_PATH,
        *sorted(DATA_RAW.glob("caged_*.parquet")),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    if not sorted(DATA_RAW.glob("caged_*.parquet")):
        raise FileNotFoundError(f"No raw CAGED files found in {DATA_RAW}.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def validate_panel(panel: pd.DataFrame) -> None:
    required = [
        "cbo_4d",
        "ano",
        "mes",
        "periodo",
        "periodo_num",
        "tempo_relativo_meses",
        "crosswalk_spec",
        OUTCOME,
        *CONTROL_COLUMNS,
    ]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise RuntimeError(f"Stage 2b panel is missing required columns: {missing}")

    specs = set(panel["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_CROSSWALK_SPEC}:
        raise RuntimeError(f"Stage 2b panel must use {EXPECTED_CROSSWALK_SPEC}; found {sorted(specs)}.")

    for col in CONTROL_COLUMNS:
        values = pd.to_numeric(panel[col], errors="coerce")
        if values.notna().sum() == 0:
            raise RuntimeError(f"Control {col} has no numeric observations.")
    if pd.to_numeric(panel["pct_mulher_adm"], errors="coerce").max(skipna=True) == 0:
        raise RuntimeError("pct_mulher_adm.max() == 0; demographic recoding is not valid.")
    if pd.to_numeric(panel["pct_negra_adm"], errors="coerce").max(skipna=True) == 0:
        raise RuntimeError("pct_negra_adm.max() == 0; race/color recoding is not valid.")


def validate_classification(classification: pd.DataFrame) -> None:
    required = [
        "cbo_4d",
        "mte_match_status",
        "cbo_ilo_gradient",
        "role__baseline_mte2d_top20_vs_rest",
    ]
    missing = [col for col in required if col not in classification.columns]
    if missing:
        raise RuntimeError(f"Scenario grid is missing required columns: {missing}")

    observed = set(classification["cbo_ilo_gradient"].dropna().unique())
    required_observed = {"Not Exposed", "Minimal Exposure", "Exposed: Gradient 1", "Exposed: Gradient 2", "Exposed: Gradient 3"}
    missing_gradients = required_observed - observed
    if missing_gradients:
        raise RuntimeError(f"Scenario grid lacks required OIT gradient classes: {sorted(missing_gradients)}")
    unexpected_gradients = observed - VALID_GRADIENTS
    if unexpected_gradients:
        raise RuntimeError(f"Scenario grid has unexpected OIT gradient classes: {sorted(unexpected_gradients)}")


def load_stage_panel() -> pd.DataFrame:
    panel = pd.read_parquet(PANEL_PATH)
    panel["cbo_4d"] = panel["cbo_4d"].astype(str).str.zfill(4)
    panel["periodo"] = panel["periodo"].astype(str)
    panel["ano"] = panel["ano"].astype(int)
    panel["mes"] = panel["mes"].astype(int)
    panel["periodo_num"] = panel["periodo_num"].astype(int)
    panel["t_binned"] = pd.to_numeric(panel["tempo_relativo_meses"], errors="raise").clip(BIN_MIN, BIN_MAX).astype(int)
    validate_panel(panel)
    return panel


def load_classification() -> pd.DataFrame:
    classification = pd.read_csv(SCENARIO_GRID_PATH, dtype={"cbo_4d": str})
    classification["cbo_4d"] = classification["cbo_4d"].astype(str).str.zfill(4)
    validate_classification(classification)
    return classification


def roles_for_contrast(classification: pd.DataFrame, contrast: Contrast) -> pd.DataFrame:
    out = classification[["cbo_4d", "mte_match_status", "cbo_ilo_gradient"]].copy()
    if contrast.role_column:
        role = classification[contrast.role_column].fillna("excluded").astype(str)
    else:
        gradient = classification["cbo_ilo_gradient"].astype(str)
        treat = gradient.isin(contrast.treatment_gradients)
        control = gradient.isin(contrast.control_gradients)
        role = pd.Series(np.select([treat, control], ["treated", "control"], default="excluded"), index=classification.index)

    out["scenario_id"] = contrast.scenario_id
    out["scenario_label"] = contrast.label_pt
    out["family"] = contrast.family
    out["control_type"] = contrast.control_type
    out["scenario_role"] = role
    out["scenario_treat"] = (out["scenario_role"] == "treated").astype(int)
    out["included"] = out["scenario_role"].isin(["treated", "control"]).astype(int)
    out["treatment_definition"] = contrast.treatment_definition_pt
    out["control_definition"] = contrast.control_definition_pt
    return out


def build_role_table(classification: pd.DataFrame) -> pd.DataFrame:
    roles = pd.concat([roles_for_contrast(classification, contrast) for contrast in CONTRASTS], ignore_index=True)
    validate_roles(roles)
    return roles


def validate_roles(roles: pd.DataFrame) -> None:
    bad_no_score = roles[
        roles["scenario_role"].isin(["treated", "control"])
        & roles["cbo_ilo_gradient"].isin(["No score"])
        & roles["scenario_id"].ne("baseline_mte2d_top20_vs_rest")
    ]
    if not bad_no_score.empty:
        raise RuntimeError("No score CBOs entered OIT treatment/control roles.")

    bad_no_mte = roles[
        roles["scenario_role"].isin(["treated", "control"])
        & roles["mte_match_status"].ne("matched_official_mte")
    ]
    if not bad_no_mte.empty:
        raise RuntimeError("No-MTE CBOs entered treatment/control roles.")

    for family in ["trat_alta_expo", "trat_media_expo", "trat_expostos"]:
        strict_id = f"{family}_strict_control"
        broad_id = f"{family}_broad_control"
        strict_control = roles[(roles["scenario_id"] == strict_id) & (roles["scenario_role"] == "control")]
        broad_control = roles[(roles["scenario_id"] == broad_id) & (roles["scenario_role"] == "control")]
        if set(strict_control["cbo_ilo_gradient"].unique()) != {"Not Exposed"}:
            raise RuntimeError(f"{strict_id} control is not exactly Not Exposed.")
        if set(broad_control["cbo_ilo_gradient"].unique()) != {"Not Exposed", "Minimal Exposure"}:
            raise RuntimeError(f"{broad_id} control is not exactly Not Exposed plus Minimal Exposure.")
        if broad_control["cbo_4d"].nunique() <= strict_control["cbo_4d"].nunique():
            raise RuntimeError(f"{broad_id} does not increase control CBO count over {strict_id}.")


def build_income_groups() -> dict[str, str]:
    log("Building pre-treatment CBO income groups from nominal raw CAGED admissions...")
    pieces = []
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        df = pd.read_parquet(
            path,
            columns=["ano", "mes", "cbo_2002", "saldo_movimentacao", "salario_mensal"],
        )
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["periodo_num"] = df["ano"] * 100 + df["mes"]
        df["salario_mensal"] = pd.to_numeric(df["salario_mensal"], errors="coerce")
        df["saldo_movimentacao"] = pd.to_numeric(df["saldo_movimentacao"], errors="coerce")
        df = df[
            (df["periodo_num"] < TREATMENT_YEAR * 100 + TREATMENT_MONTH)
            & df["saldo_movimentacao"].eq(1)
            & df["salario_mensal"].notna()
            & (df["salario_mensal"] > 0)
        ].copy()
        if df.empty:
            continue
        df["cbo_4d"] = valid_cbo_4d(df["cbo_2002"])
        df = df[df["cbo_4d"].notna()].copy()
        df["salario_sm"] = df["salario_mensal"] / df["ano"].map(SALARIO_MINIMO)
        pieces.append(df[["cbo_4d", "salario_sm"]])
        del df

    if not pieces:
        raise RuntimeError("Could not build pre-treatment income groups from raw CAGED.")
    wages = pd.concat(pieces, ignore_index=True)
    med = wages.groupby("cbo_4d", observed=True)["salario_sm"].median()

    def bucket(value: float) -> str:
        if value <= 2:
            return "low_income"
        if value <= 5:
            return "middle_income"
        return "high_income"

    return med.map(bucket).to_dict()


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
    raise ValueError(f"Unknown profile dimension: {dimension}")


def reconstruct_nominal_wage_profiles() -> pd.DataFrame:
    log("Reconstructing nominal wage profile panels from raw CAGED microdata...")
    income_groups = build_income_groups()
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
        df["saldo_movimentacao"] = pd.to_numeric(df["saldo_movimentacao"], errors="coerce")
        df["salario_mensal"] = pd.to_numeric(df["salario_mensal"], errors="coerce")
        df = df[
            df["saldo_movimentacao"].eq(1)
            & df["salario_mensal"].notna()
            & (df["salario_mensal"] > 0)
        ].copy()
        if df.empty:
            continue

        base = df[["cbo_4d", "ano", "mes", "periodo", "periodo_num", "salario_mensal"]].copy()
        for dimension, spec in PROFILE_DIMENSIONS.items():
            log(f"    Aggregating {dimension}...")
            group_id = group_series_for_dimension(df, dimension, income_groups)
            mask = group_id.notna()
            if not bool(mask.any()):
                continue
            d = base.loc[mask].copy()
            d["group_id"] = group_id.loc[mask].to_numpy()
            agg = (
                d.groupby(["cbo_4d", "ano", "mes", "periodo", "periodo_num", "group_id"], observed=True)
                .agg(
                    n_admissions_wage=("salario_mensal", "size"),
                    salario_adm=("salario_mensal", "mean"),
                )
                .reset_index()
            )
            agg["dimension"] = dimension
            agg["dimension_label"] = spec["label_pt"]
            pieces.append(agg)
            del d, agg, group_id, mask
        del base, df

    if not pieces:
        raise RuntimeError("Raw CAGED wage profile reconstruction produced no rows.")

    out = pd.concat(pieces, ignore_index=True)
    label_map = {
        (dimension, group_id): group_label
        for dimension, spec in PROFILE_DIMENSIONS.items()
        for group_id, group_label in spec["groups"]
    }
    out["group_label"] = [label_map[(dimension, group_id)] for dimension, group_id in zip(out["dimension"], out["group_id"])]
    out[OUTCOME] = np.log(out["salario_adm"].clip(lower=1))
    return out


def base_controls(panel: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "cbo_4d",
        "ano",
        "mes",
        "periodo",
        "periodo_num",
        "t_binned",
        *CONTROL_COLUMNS,
    ]
    out = panel[cols].copy()
    out["cbo_4d"] = out["cbo_4d"].astype(str).str.zfill(4)
    out["periodo"] = out["periodo"].astype(str)
    return out


def merge_profiles_with_controls(profile_panel: pd.DataFrame, stage_panel: pd.DataFrame) -> pd.DataFrame:
    controls = base_controls(stage_panel)
    out = profile_panel.merge(
        controls,
        on=["cbo_4d", "ano", "mes", "periodo", "periodo_num"],
        how="inner",
    )
    if out.empty:
        raise RuntimeError("Profile wage panel has no overlap with the Stage 2b panel.")
    return out


def prepare_event_data(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict[int, str]]:
    out = data.copy()
    dummy_names: list[str] = []
    t_to_name: dict[int, str] = {}
    for t in EVENT_TIMES:
        if t == REFERENCE_PERIOD:
            continue
        name = event_dummy_name(t)
        out[name] = ((out["t_binned"] == t) & (out["scenario_treat"] == 1)).astype(int)
        dummy_names.append(name)
        t_to_name[t] = name
    return out, dummy_names, t_to_name


def parse_wald_result(result: pd.Series) -> tuple[float, float]:
    statistic = np.nan
    p_value = np.nan
    for key, value in result.items():
        text = str(key).lower()
        if "p" in text and "value" in text:
            p_value = float(value)
        if ("stat" in text or "wald" in text) and not pd.isna(value):
            statistic = float(value)
    if pd.isna(p_value):
        for key, value in result.items():
            if "p" in str(key).lower():
                p_value = float(value)
    return statistic, p_value


def joint_pretrend_test(model: object, pre_terms: list[str]) -> tuple[float, float, str]:
    if not pre_terms:
        return np.nan, np.nan, "not_available_no_pre_terms"

    coef_index = list(model.coef().index)
    try:
        r_matrix = np.zeros((len(pre_terms), len(coef_index)))
        for row_idx, term in enumerate(pre_terms):
            r_matrix[row_idx, coef_index.index(term)] = 1.0
        result = model.wald_test(R=r_matrix, q=np.zeros(len(pre_terms)), distribution="chi2")
        statistic, p_value = parse_wald_result(result)
        if not pd.isna(p_value):
            return statistic, p_value, "wald_chi2"
    except Exception:
        pass

    tstats = model.tstat().reindex(pre_terms).dropna()
    if tstats.empty:
        return np.nan, np.nan, "not_available_no_tstats"
    statistic = float(np.square(tstats.astype(float)).sum())
    p_value = float(chi2.sf(statistic, len(tstats)))
    return statistic, p_value, "tstat_chi2_fallback"


def classify_pretrend(n_pre_p_lt_005: int, joint_p_value: float) -> str:
    if pd.isna(joint_p_value):
        return "warning"
    if joint_p_value < 0.05 or n_pre_p_lt_005 >= 2:
        return "fail"
    if n_pre_p_lt_005 == 0 and joint_p_value > 0.10:
        return "pass"
    return "warning"


def status_reason(status: str, reason: str) -> str:
    if status == "estimated" and not reason:
        return "No treated/control CBO loss for this profile after nominal wage reconstruction."
    return reason or status


def profile_sample(
    profile_panel: pd.DataFrame,
    roles: pd.DataFrame,
    contrast: Contrast,
    dimension: str,
    group_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    role_subset = roles[roles["scenario_id"].eq(contrast.scenario_id)].copy()
    included = role_subset[role_subset["scenario_role"].isin(["treated", "control"])].copy()
    expected_treated = set(included.loc[included["scenario_treat"].eq(1), "cbo_4d"])
    expected_control = set(included.loc[included["scenario_treat"].eq(0), "cbo_4d"])

    base = profile_panel[
        profile_panel["dimension"].eq(dimension) & profile_panel["group_id"].eq(group_id)
    ].copy()
    merged = base.merge(
        included[
            [
                "cbo_4d",
                "scenario_id",
                "scenario_label",
                "family",
                "control_type",
                "scenario_role",
                "scenario_treat",
                "cbo_ilo_gradient",
                "mte_match_status",
            ]
        ],
        on="cbo_4d",
        how="inner",
    )

    d = merged.dropna(subset=[OUTCOME, *CONTROL_COLUMNS, "cbo_4d", "periodo"]).copy()
    d[OUTCOME] = pd.to_numeric(d[OUTCOME], errors="coerce")
    for col in CONTROL_COLUMNS:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna(subset=[OUTCOME, *CONTROL_COLUMNS])

    observed_treated = set(d.loc[d["scenario_treat"].eq(1), "cbo_4d"].unique())
    observed_control = set(d.loc[d["scenario_treat"].eq(0), "cbo_4d"].unique())
    missing_treated = len(expected_treated - observed_treated)
    missing_control = len(expected_control - observed_control)
    meta = {
        "expected_treated_cbo": len(expected_treated),
        "expected_control_cbo": len(expected_control),
        "expected_excluded_cbo": int((role_subset["scenario_role"] == "excluded").sum()),
        "candidate_obs": int(len(merged)),
        "candidate_cbo": int(merged["cbo_4d"].nunique()) if not merged.empty else 0,
        "n_obs": int(len(d)),
        "n_cbo": int(d["cbo_4d"].nunique()) if not d.empty else 0,
        "n_treated_cbo": int(len(observed_treated)),
        "n_control_cbo": int(len(observed_control)),
        "missing_treated_cbo": int(missing_treated),
        "missing_control_cbo": int(missing_control),
        "lost_cbo_total": int(missing_treated + missing_control),
        "n_periods": int(d["periodo"].nunique()) if not d.empty else 0,
        "treated_gradients": "; ".join(
            sorted(role_subset.loc[role_subset["scenario_role"].eq("treated"), "cbo_ilo_gradient"].dropna().unique())
        ),
        "control_gradients": "; ".join(
            sorted(role_subset.loc[role_subset["scenario_role"].eq("control"), "cbo_ilo_gradient"].dropna().unique())
        ),
    }
    return merged, d, meta


def insufficient_sample_reason(d: pd.DataFrame, meta: dict[str, object]) -> str | None:
    if d.empty:
        return "No non-missing nominal admission wage observations for this profile and contrast."
    if int(meta["n_treated_cbo"]) == 0 or int(meta["n_control_cbo"]) == 0:
        return "Missing treated or control CBOs after profile wage reconstruction."
    if d["scenario_treat"].nunique() < 2:
        return "Treatment indicator has no variation in this profile sample."
    if int(meta["n_cbo"]) < 2:
        return "Fewer than two CBO clusters remain in this profile sample."
    if d["periodo"].nunique() < 2:
        return "Fewer than two months remain in this profile sample."
    return None


def sample_summary_row(
    contrast: Contrast,
    dimension: str,
    dimension_label: str,
    group_id: str,
    group_label: str,
    meta: dict[str, object],
    result_status: str,
    sample_loss_reason: str,
) -> dict[str, object]:
    return {
        "scenario_id": contrast.scenario_id,
        "scenario_label": contrast.label_pt,
        "family": contrast.family,
        "control_type": contrast.control_type,
        "dimension": dimension,
        "dimension_label": dimension_label,
        "group_id": group_id,
        "group_label": group_label,
        "outcome": OUTCOME,
        "outcome_label": OUTCOME_LABEL_PT,
        "model": f"{OUTCOME} ~ event_dummies + {CONTROL_TERMS} | cbo_4d + periodo",
        "cluster": "cbo_4d",
        "expected_treated_cbo": meta["expected_treated_cbo"],
        "expected_control_cbo": meta["expected_control_cbo"],
        "expected_excluded_cbo": meta["expected_excluded_cbo"],
        "candidate_obs": meta["candidate_obs"],
        "candidate_cbo": meta["candidate_cbo"],
        "n_obs": meta["n_obs"],
        "n_cbo": meta["n_cbo"],
        "n_treated_cbo": meta["n_treated_cbo"],
        "n_control_cbo": meta["n_control_cbo"],
        "missing_treated_cbo": meta["missing_treated_cbo"],
        "missing_control_cbo": meta["missing_control_cbo"],
        "lost_cbo_total": meta["lost_cbo_total"],
        "n_periods": meta["n_periods"],
        "treated_gradients": meta["treated_gradients"],
        "control_gradients": meta["control_gradients"],
        "result_status": result_status,
        "sample_loss_reason": sample_loss_reason,
        "treatment_definition": contrast.treatment_definition_pt,
        "control_definition": contrast.control_definition_pt,
    }


def failed_coefficient_rows(
    contrast: Contrast,
    dimension: str,
    dimension_label: str,
    group_id: str,
    group_label: str,
    meta: dict[str, object],
    result_status: str,
    sample_loss_reason: str,
) -> list[dict[str, object]]:
    rows = []
    for t in EVENT_TIMES:
        is_reference = t == REFERENCE_PERIOD
        rows.append(
            {
                "scenario_id": contrast.scenario_id,
                "scenario_label": contrast.label_pt,
                "family": contrast.family,
                "control_type": contrast.control_type,
                "dimension": dimension,
                "dimension_label": dimension_label,
                "group_id": group_id,
                "group_label": group_label,
                "outcome": OUTCOME,
                "outcome_label": OUTCOME_LABEL_PT,
                "t": t,
                "is_reference": is_reference,
                "is_pretrend": t < 0 and not is_reference,
                "coef": 0.0 if is_reference else np.nan,
                "se": 0.0 if is_reference else np.nan,
                "p_value": np.nan,
                "ci_low": 0.0 if is_reference else np.nan,
                "ci_high": 0.0 if is_reference else np.nan,
                "coefficient_status": "reference" if is_reference else "not_estimated",
                "result_status": result_status,
                "sample_loss_reason": sample_loss_reason,
                "n_obs": meta["n_obs"],
                "n_cbo": meta["n_cbo"],
                "n_treated_cbo": meta["n_treated_cbo"],
                "n_control_cbo": meta["n_control_cbo"],
            }
        )
    return rows


def failed_pretrend_row(
    contrast: Contrast,
    dimension: str,
    dimension_label: str,
    group_id: str,
    group_label: str,
    meta: dict[str, object],
    result_status: str,
    sample_loss_reason: str,
) -> dict[str, object]:
    return {
        "scenario_id": contrast.scenario_id,
        "scenario_label": contrast.label_pt,
        "family": contrast.family,
        "control_type": contrast.control_type,
        "dimension": dimension,
        "dimension_label": dimension_label,
        "group_id": group_id,
        "group_label": group_label,
        "outcome": OUTCOME,
        "outcome_label": OUTCOME_LABEL_PT,
        "n_obs": meta["n_obs"],
        "n_cbo": meta["n_cbo"],
        "n_treated_cbo": meta["n_treated_cbo"],
        "n_control_cbo": meta["n_control_cbo"],
        "n_pre_coefficients": 0,
        "n_pre_p_lt_005": 0,
        "max_abs_pre_coef": np.nan,
        "mean_abs_pre_coef": np.nan,
        "joint_statistic": np.nan,
        "joint_p_value": np.nan,
        "joint_test_method": "not_estimated",
        "pretrend_status": "not_estimated",
        "result_status": result_status,
        "sample_loss_reason": sample_loss_reason,
    }


def estimate_profile_event_studies(
    profile_panel: pd.DataFrame,
    roles: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coef_rows: list[dict[str, object]] = []
    pretrend_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for contrast in CONTRASTS:
        log(f"Estimating profile event studies for {contrast.scenario_id}...")
        for dimension, dimension_label, group_id, group_label in expected_profile_rows():
            _, d, meta = profile_sample(profile_panel, roles, contrast, dimension, group_id)
            reason = insufficient_sample_reason(d, meta)
            if reason is not None:
                status = "failed_insufficient_sample"
                sample_loss = status_reason(status, reason)
                coef_rows.extend(
                    failed_coefficient_rows(
                        contrast,
                        dimension,
                        dimension_label,
                        group_id,
                        group_label,
                        meta,
                        status,
                        sample_loss,
                    )
                )
                pretrend_rows.append(
                    failed_pretrend_row(
                        contrast,
                        dimension,
                        dimension_label,
                        group_id,
                        group_label,
                        meta,
                        status,
                        sample_loss,
                    )
                )
                summary_rows.append(
                    sample_summary_row(
                        contrast,
                        dimension,
                        dimension_label,
                        group_id,
                        group_label,
                        meta,
                        status,
                        sample_loss,
                    )
                )
                continue

            event_data, dummy_names, t_to_name = prepare_event_data(d)
            formula = f"{OUTCOME} ~ {' + '.join(dummy_names)} + {CONTROL_TERMS} | cbo_4d + periodo"
            try:
                model = pf.feols(formula, data=event_data, vcov=VCOV_SPEC)
            except Exception as exc:
                status = "failed_estimation"
                sample_loss = f"Estimation failed: {type(exc).__name__}: {str(exc).replace(chr(10), ' ')[:300]}"
                coef_rows.extend(
                    failed_coefficient_rows(
                        contrast,
                        dimension,
                        dimension_label,
                        group_id,
                        group_label,
                        meta,
                        status,
                        sample_loss,
                    )
                )
                pretrend_rows.append(
                    failed_pretrend_row(
                        contrast,
                        dimension,
                        dimension_label,
                        group_id,
                        group_label,
                        meta,
                        status,
                        sample_loss,
                    )
                )
                summary_rows.append(
                    sample_summary_row(
                        contrast,
                        dimension,
                        dimension_label,
                        group_id,
                        group_label,
                        meta,
                        status,
                        sample_loss,
                    )
                )
                continue

            coefs = model.coef()
            ses = model.se()
            pvalues = model.pvalue()
            coef_index = set(coefs.index)
            status = "estimated"
            sample_loss = status_reason(status, "")

            for t in EVENT_TIMES:
                is_reference = t == REFERENCE_PERIOD
                is_pretrend = t < 0 and not is_reference
                if is_reference:
                    row = {
                        "coef": 0.0,
                        "se": 0.0,
                        "p_value": np.nan,
                        "ci_low": 0.0,
                        "ci_high": 0.0,
                        "coefficient_status": "reference",
                    }
                else:
                    term = t_to_name[t]
                    if term in coef_index:
                        coef = float(coefs.loc[term])
                        se = float(ses.loc[term])
                        p_value = float(pvalues.loc[term])
                        row = {
                            "coef": coef,
                            "se": se,
                            "p_value": p_value,
                            "ci_low": coef - 1.96 * se,
                            "ci_high": coef + 1.96 * se,
                            "coefficient_status": "estimated",
                        }
                    else:
                        row = {
                            "coef": np.nan,
                            "se": np.nan,
                            "p_value": np.nan,
                            "ci_low": np.nan,
                            "ci_high": np.nan,
                            "coefficient_status": "omitted",
                        }

                coef_rows.append(
                    {
                        "scenario_id": contrast.scenario_id,
                        "scenario_label": contrast.label_pt,
                        "family": contrast.family,
                        "control_type": contrast.control_type,
                        "dimension": dimension,
                        "dimension_label": dimension_label,
                        "group_id": group_id,
                        "group_label": group_label,
                        "outcome": OUTCOME,
                        "outcome_label": OUTCOME_LABEL_PT,
                        "t": t,
                        "is_reference": is_reference,
                        "is_pretrend": is_pretrend,
                        "result_status": status,
                        "sample_loss_reason": sample_loss,
                        "n_obs": meta["n_obs"],
                        "n_cbo": meta["n_cbo"],
                        "n_treated_cbo": meta["n_treated_cbo"],
                        "n_control_cbo": meta["n_control_cbo"],
                        **row,
                    }
                )

            pre_terms = [
                t_to_name[t]
                for t in EVENT_TIMES
                if t < 0 and t != REFERENCE_PERIOD and t_to_name[t] in coef_index
            ]
            pre_coef = pd.Series(coefs).reindex(pre_terms).astype(float)
            pre_pvalues = pd.Series(pvalues).reindex(pre_terms).astype(float)
            joint_statistic, joint_p_value, joint_method = joint_pretrend_test(model, pre_terms)
            n_pre_p_lt_005 = int((pre_pvalues < 0.05).sum())
            pretrend_rows.append(
                {
                    "scenario_id": contrast.scenario_id,
                    "scenario_label": contrast.label_pt,
                    "family": contrast.family,
                    "control_type": contrast.control_type,
                    "dimension": dimension,
                    "dimension_label": dimension_label,
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": OUTCOME,
                    "outcome_label": OUTCOME_LABEL_PT,
                    "n_obs": meta["n_obs"],
                    "n_cbo": meta["n_cbo"],
                    "n_treated_cbo": meta["n_treated_cbo"],
                    "n_control_cbo": meta["n_control_cbo"],
                    "n_pre_coefficients": int(pre_coef.notna().sum()),
                    "n_pre_p_lt_005": n_pre_p_lt_005,
                    "max_abs_pre_coef": float(pre_coef.abs().max()) if not pre_coef.empty else np.nan,
                    "mean_abs_pre_coef": float(pre_coef.abs().mean()) if not pre_coef.empty else np.nan,
                    "joint_statistic": joint_statistic,
                    "joint_p_value": joint_p_value,
                    "joint_test_method": joint_method,
                    "pretrend_status": classify_pretrend(n_pre_p_lt_005, joint_p_value),
                    "result_status": status,
                    "sample_loss_reason": sample_loss,
                }
            )
            summary_rows.append(
                sample_summary_row(
                    contrast,
                    dimension,
                    dimension_label,
                    group_id,
                    group_label,
                    meta,
                    status,
                    sample_loss,
                )
            )

    return pd.DataFrame(coef_rows), pd.DataFrame(pretrend_rows), pd.DataFrame(summary_rows)


def profile_grid_shape(dimension: str) -> tuple[int, int]:
    n_groups = len(PROFILE_DIMENSIONS[dimension]["groups"])
    ncols = 2 if n_groups > 1 else 1
    nrows = int(math.ceil(n_groups / ncols))
    return nrows, ncols


def plot_scenario_dimension(coefficients: pd.DataFrame, pretrends: pd.DataFrame, contrast: Contrast, dimension: str) -> None:
    spec = PROFILE_DIMENSIONS[dimension]
    nrows, ncols = profile_grid_shape(dimension)
    fig, axes = plt.subplots(nrows, ncols, figsize=(6.2 * ncols, 3.8 * nrows), sharex=True, squeeze=False)
    axes_flat = axes.flatten()
    colors = {
        "pass": "#1b9e77",
        "warning": "#d95f02",
        "fail": "#7570b3",
        "not_estimated": "#666666",
    }

    for ax, (group_id, group_label) in zip(axes_flat, spec["groups"]):
        view = coefficients[
            coefficients["scenario_id"].eq(contrast.scenario_id)
            & coefficients["dimension"].eq(dimension)
            & coefficients["group_id"].eq(group_id)
        ].sort_values("t")
        pre = pretrends[
            pretrends["scenario_id"].eq(contrast.scenario_id)
            & pretrends["dimension"].eq(dimension)
            & pretrends["group_id"].eq(group_id)
        ]
        pre_status = "not_estimated" if pre.empty else str(pre["pretrend_status"].iloc[0])
        result_status = "not_estimated" if view.empty else str(view["result_status"].iloc[0])
        color = colors.get(pre_status, "#1f77b4")

        ax.axhline(0, color="#222222", linewidth=0.8)
        ax.axvline(REFERENCE_PERIOD, color="#666666", linewidth=0.8, linestyle="--")
        ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
        ax.set_title(f"{group_label}\npre-trend: {pre_status}", fontsize=10)
        ax.set_xlabel("Meses relativos ao ChatGPT")
        ax.set_ylabel("Coeficiente")
        ax.grid(True, alpha=0.2)

        estimated = view[view["coefficient_status"].isin(["estimated", "reference"])].copy()
        if result_status != "estimated" or estimated.empty:
            ax.text(
                0.5,
                0.5,
                result_status.replace("_", " "),
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=10,
                color="#555555",
            )
            continue

        ax.plot(
            estimated["t"].astype(float).to_numpy(),
            estimated["coef"].astype(float).to_numpy(),
            marker="o",
            markersize=3,
            linewidth=1.3,
            color=color,
        )
        band = estimated.dropna(subset=["ci_low", "ci_high"])
        if not band.empty:
            ax.fill_between(
                band["t"].astype(float).to_numpy(),
                band["ci_low"].astype(float).to_numpy(),
                band["ci_high"].astype(float).to_numpy(),
                color=color,
                alpha=0.18,
            )

    for ax in axes_flat[len(spec["groups"]) :]:
        ax.axis("off")

    fig.suptitle(f"{contrast.label_pt} - {spec['label_pt']}", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"profile_event_study_{contrast.scenario_id}_{dimension}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_all(coefficients: pd.DataFrame, pretrends: pd.DataFrame) -> None:
    for contrast in CONTRASTS:
        for dimension in PROFILE_DIMENSIONS:
            plot_scenario_dimension(coefficients, pretrends, contrast, dimension)


def post_dynamics(coefficients: pd.DataFrame, pretrends: pd.DataFrame) -> pd.DataFrame:
    post = coefficients[
        coefficients["result_status"].eq("estimated")
        & coefficients["coefficient_status"].eq("estimated")
        & coefficients["t"].ge(0)
    ].copy()
    if post.empty:
        return pd.DataFrame()
    out = (
        post.groupby(
            [
                "scenario_id",
                "scenario_label",
                "control_type",
                "dimension",
                "dimension_label",
                "group_id",
                "group_label",
            ],
            observed=True,
        )
        .agg(
            mean_post_coef=("coef", "mean"),
            min_post_coef=("coef", "min"),
            max_post_coef=("coef", "max"),
            n_post_coefficients=("coef", "size"),
            n_post_p_lt_005=("p_value", lambda s: int((s < 0.05).sum())),
        )
        .reset_index()
    )
    pre_cols = [
        "scenario_id",
        "dimension",
        "group_id",
        "pretrend_status",
        "joint_p_value",
        "n_pre_p_lt_005",
        "max_abs_pre_coef",
        "result_status",
    ]
    return out.merge(pretrends[pre_cols], on=["scenario_id", "dimension", "group_id"], how="left")


def status_counts(pretrends: pd.DataFrame) -> pd.DataFrame:
    out = (
        pretrends.groupby(["dimension", "pretrend_status"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["pass", "warning", "fail", "not_estimated"]:
        if col not in out.columns:
            out[col] = 0
    out["dimension_label"] = out["dimension"].map({dim: spec["label_pt"] for dim, spec in PROFILE_DIMENSIONS.items()})
    return out[["dimension", "dimension_label", "pass", "warning", "fail", "not_estimated"]]


def scenario_status_counts(pretrends: pd.DataFrame) -> pd.DataFrame:
    out = (
        pretrends.groupby(["scenario_id", "pretrend_status"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["pass", "warning", "fail", "not_estimated"]:
        if col not in out.columns:
            out[col] = 0
    return out[["scenario_id", "pass", "warning", "fail", "not_estimated"]]


def format_report_table(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in numeric_cols:
        if col in out:
            out[col] = out[col].map(lambda value: fmt_number(value, 4))
    return out


def write_general_report(summary: pd.DataFrame, pretrends: pd.DataFrame, coefficients: pd.DataFrame) -> None:
    dynamics = post_dynamics(coefficients, pretrends)
    passing_negative = dynamics[
        dynamics["pretrend_status"].eq("pass") & dynamics["mean_post_coef"].lt(0)
    ].sort_values("mean_post_coef")
    exploratory = dynamics[
        ~dynamics["pretrend_status"].eq("pass")
    ].sort_values(["pretrend_status", "mean_post_coef"])

    strongest_cols = [
        "scenario_id",
        "dimension_label",
        "group_label",
        "mean_post_coef",
        "min_post_coef",
        "n_post_p_lt_005",
        "pretrend_status",
        "joint_p_value",
    ]
    strongest = format_report_table(passing_negative.head(12)[strongest_cols], ["mean_post_coef", "min_post_coef", "joint_p_value"])

    exploratory_view = format_report_table(
        exploratory.head(18)[
            [
                "scenario_id",
                "dimension_label",
                "group_label",
                "mean_post_coef",
                "pretrend_status",
                "joint_p_value",
            ]
        ],
        ["mean_post_coef", "joint_p_value"],
    )

    dimension_counts = status_counts(pretrends)
    scenario_counts = scenario_status_counts(pretrends)

    estimated_profiles = int(summary["result_status"].eq("estimated").sum())
    failed_profiles = int((~summary["result_status"].eq("estimated")).sum())
    total_profiles = int(len(summary))
    pass_count = int(pretrends["pretrend_status"].eq("pass").sum())
    warning_count = int(pretrends["pretrend_status"].eq("warning").sum())
    fail_count = int(pretrends["pretrend_status"].eq("fail").sum())
    not_estimated_count = int(pretrends["pretrend_status"].eq("not_estimated").sum())

    text = [
        "# Event study salarial por perfil sociodemográfico",
        "",
        "## Contrato empírico",
        "",
        "Este pacote é um diagnóstico separado do event study agregado. Ele estima apenas `ln_salario_adm`, usando salário nominal de admissão da CAGED bruta para manter comparabilidade com o outcome agregado. O painel é reconstruído por `cbo_4d x periodo x dimensão x grupo`, e depois combinado com os mesmos controles agregados do Stage 2b.",
        "",
        "Os sete contrastes vêm diretamente de `outputs/treatment_scenario_grid/scenario_cbo_classification.csv`. Nos contrastes OIT, o controle estrito usa somente `Not Exposed`; o controle amplo adiciona `Minimal Exposure`. CBOs `No score`, sem MTE ou com classificação inválida ficam fora de tratamento e controle.",
        "",
        "O modelo estimado em cada célula é `ln_salario_adm ~ event_dummies + idade_media_adm + pct_mulher_adm + pct_superior_adm + pct_negra_adm | cbo_4d + periodo`, com erro-padrão clusterizado por `cbo_4d`. O período `t = -1` é a referência explícita, com coeficiente zero.",
        "",
        "## Cobertura",
        "",
        f"Foram avaliadas {fmt_number(total_profiles, 0)} células de contraste-perfil: {fmt_number(estimated_profiles, 0)} estimadas e {fmt_number(failed_profiles, 0)} não estimadas por falta de amostra/variação ou falha numérica.",
        "",
        "## Diagnóstico de pre-trends",
        "",
        f"No total, os perfis estimados tiveram {fmt_number(pass_count, 0)} `pass`, {fmt_number(warning_count, 0)} `warning`, {fmt_number(fail_count, 0)} `fail` e {fmt_number(not_estimated_count, 0)} `not_estimated` nos testes de pre-trends.",
        "",
        markdown_table(dimension_counts, ["dimension_label", "pass", "warning", "fail", "not_estimated"]),
        "",
        "Por contraste:",
        "",
        markdown_table(scenario_counts, ["scenario_id", "pass", "warning", "fail", "not_estimated"]),
        "",
        "## Onde o sinal salarial negativo é mais forte",
        "",
    ]

    if strongest.empty:
        text.extend(
            [
                "Nenhum perfil com pre-trends classificados como `pass` apresentou média pós-tratamento negativa estimada. Nesse caso, a heterogeneidade salarial deve ser tratada como evidência exploratória, não como resultado causal por perfil.",
                "",
            ]
        )
    else:
        text.extend(
            [
                "A tabela abaixo lista os perfis com pre-trends `pass` e média pós-tratamento mais negativa. Eles são os candidatos mais defensáveis para discussão substantiva, ainda condicionados ao caráter diagnóstico do pacote.",
                "",
                markdown_table(
                    strongest,
                    [
                        "scenario_id",
                        "dimension_label",
                        "group_label",
                        "mean_post_coef",
                        "min_post_coef",
                        "n_post_p_lt_005",
                        "pretrend_status",
                        "joint_p_value",
                    ],
                ),
                "",
            ]
        )

    text.extend(
        [
            "## Resultados exploratórios ou problemáticos",
            "",
            "Esta seção é deliberadamente exploratória: ela separa sinais descritivos de perfis que não passaram no diagnóstico de pre-trends.",
            "",
            "Nenhum perfil com `warning`, `fail` ou `not_estimated` em pre-trends é tratado aqui como achado causal. Esses recortes servem para mapear heterogeneidade possível e para mostrar onde a leitura dinâmica não sustenta inferência forte.",
            "",
            markdown_table(
                exploratory_view,
                ["scenario_id", "dimension_label", "group_label", "mean_post_coef", "pretrend_status", "joint_p_value"],
            ),
            "",
            "## Figuras",
            "",
        ]
    )
    for contrast in CONTRASTS:
        for dimension, spec in PROFILE_DIMENSIONS.items():
            filename = f"profile_event_study_{contrast.scenario_id}_{dimension}.png"
            text.append(f"- {contrast.label_pt} - {spec['label_pt']}: ![{filename}]({filename})")
    text.extend(
        [
            "",
            "## Leitura para a dissertação",
            "",
            "A mensagem principal deve ser proporcional ao diagnóstico. Se um perfil passa nos pre-trends e mostra queda salarial pós-tratamento, ele pode ser discutido como evidência dinâmica compatível com heterogeneidade salarial. Se o perfil falha, a conclusão correta é metodológica: há sinal exploratório de heterogeneidade, mas o recorte não sustenta uma leitura causal forte.",
            "",
        ]
    )
    (OUTPUT_DIR / "profile_event_study_wage_report.md").write_text("\n".join(text), encoding="utf-8")


def expected_output_files() -> list[Path]:
    return [
        OUTPUT_DIR / "profile_event_study_coefficients_long.csv",
        OUTPUT_DIR / "profile_event_study_pretrend_tests.csv",
        OUTPUT_DIR / "profile_event_study_sample_summary.csv",
        OUTPUT_DIR / "profile_event_study_contrast_cbo_roles.csv",
        OUTPUT_DIR / "profile_event_study_wage_report.md",
        *[
            OUTPUT_DIR / f"profile_event_study_{contrast.scenario_id}_{dimension}.png"
            for contrast in CONTRASTS
            for dimension in PROFILE_DIMENSIONS
        ],
    ]


def validate_outputs(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    summary: pd.DataFrame,
    roles: pd.DataFrame,
) -> None:
    expected_scenarios = {contrast.scenario_id for contrast in CONTRASTS}
    expected_dimensions = set(PROFILE_DIMENSIONS)
    expected_groups = {(dimension, group_id) for dimension, _, group_id, _ in expected_profile_rows()}

    if set(coefficients["scenario_id"]) != expected_scenarios:
        raise RuntimeError("Coefficient CSV does not contain all seven expected contrasts.")
    if set(pretrends["scenario_id"]) != expected_scenarios:
        raise RuntimeError("Pretrend CSV does not contain all seven expected contrasts.")
    if set(summary["scenario_id"]) != expected_scenarios:
        raise RuntimeError("Sample summary does not contain all seven expected contrasts.")
    if set(coefficients["dimension"]) != expected_dimensions:
        raise RuntimeError("Coefficient CSV does not contain all five profile dimensions.")
    if set(pretrends["dimension"]) != expected_dimensions:
        raise RuntimeError("Pretrend CSV does not contain all five profile dimensions.")
    if set(summary["dimension"]) != expected_dimensions:
        raise RuntimeError("Sample summary does not contain all five profile dimensions.")

    for scenario_id in expected_scenarios:
        found_groups = set(
            coefficients.loc[coefficients["scenario_id"].eq(scenario_id), ["dimension", "group_id"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        )
        if found_groups != expected_groups:
            raise RuntimeError(f"{scenario_id} is missing expected profile groups in coefficients.")
        found_pre_groups = set(
            pretrends.loc[pretrends["scenario_id"].eq(scenario_id), ["dimension", "group_id"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        )
        if found_pre_groups != expected_groups:
            raise RuntimeError(f"{scenario_id} is missing expected profile groups in pretrend tests.")

    ref = coefficients[coefficients["t"].eq(REFERENCE_PERIOD)]
    expected_ref_rows = len(expected_scenarios) * len(expected_groups)
    if len(ref) != expected_ref_rows:
        raise RuntimeError(f"Reference period rows are missing. Expected {expected_ref_rows}, found {len(ref)}.")
    if not (ref["coef"].fillna(999).eq(0).all() and ref["se"].fillna(999).eq(0).all()):
        raise RuntimeError("Reference period rows must have coefficient and standard error equal to zero.")

    validate_roles(roles)

    for family in ["trat_alta_expo", "trat_media_expo", "trat_expostos"]:
        strict = summary.loc[summary["scenario_id"].eq(f"{family}_strict_control")].iloc[0]
        broad = summary.loc[summary["scenario_id"].eq(f"{family}_broad_control")].iloc[0]
        if "Minimal Exposure" in str(strict["control_gradients"]):
            raise RuntimeError(f"{family} strict_control includes Minimal Exposure.")
        if "Minimal Exposure" not in str(broad["control_gradients"]):
            raise RuntimeError(f"{family} broad_control does not include Minimal Exposure.")
        if int(broad["expected_control_cbo"]) <= int(strict["expected_control_cbo"]):
            raise RuntimeError(f"{family} broad_control does not increase control CBO count.")

    if coefficients["outcome"].nunique() != 1 or set(coefficients["outcome"]) != {OUTCOME}:
        raise RuntimeError("Coefficient output must contain only ln_salario_adm.")
    if pretrends["outcome"].nunique() != 1 or set(pretrends["outcome"]) != {OUTCOME}:
        raise RuntimeError("Pretrend output must contain only ln_salario_adm.")

    missing_or_empty = [str(path) for path in expected_output_files() if not path.exists() or path.stat().st_size == 0]
    if missing_or_empty:
        raise RuntimeError("Missing or empty expected outputs:\n" + "\n".join(missing_or_empty))

    report = (OUTPUT_DIR / "profile_event_study_wage_report.md").read_text(encoding="utf-8")
    for required_text in ["pre-trends", "Minimal Exposure", "exploratória", "achado causal", "controle estrito"]:
        if required_text not in report:
            raise RuntimeError(f"General report does not explicitly include: {required_text}")


def main() -> None:
    ensure_inputs()
    log("Loading Stage 2b panel and scenario grid...")
    stage_panel = load_stage_panel()
    classification = load_classification()
    roles = build_role_table(classification)

    profile_panel_raw = reconstruct_nominal_wage_profiles()
    profile_panel = merge_profiles_with_controls(profile_panel_raw, stage_panel)
    log(f"Profile wage panel has {len(profile_panel):,} rows after merging controls.".replace(",", "."))

    log("Estimating profile wage event studies...")
    coefficients, pretrends, summary = estimate_profile_event_studies(profile_panel, roles)

    roles.to_csv(OUTPUT_DIR / "profile_event_study_contrast_cbo_roles.csv", index=False)
    coefficients.to_csv(OUTPUT_DIR / "profile_event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(OUTPUT_DIR / "profile_event_study_pretrend_tests.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "profile_event_study_sample_summary.csv", index=False)

    log("Writing figures...")
    plot_all(coefficients, pretrends)

    log("Writing report...")
    write_general_report(summary, pretrends, coefficients)

    log("Validating outputs...")
    validate_outputs(coefficients, pretrends, summary, roles)
    log(f"Done. Outputs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
