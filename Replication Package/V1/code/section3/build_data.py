"""Build the Section 3 PNAD–ILO analytic cross-section from source data."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common.files import sha256_file
from .constants import CNAE_SECAO_TO_SETOR, SALARY_MINIMUM_BRL


EXPECTED_YEAR = 2025
EXPECTED_QUARTER = 3
EXPECTED_ILO_SHA256 = (
    "c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a"
)
PNAD_FILENAME = "pnad_2025q3.parquet"
ILO_FILENAME = "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"

PNAD_COLUMNS = (
    "ano",
    "trimestre",
    "sigla_uf",
    "sexo",
    "idade",
    "raca_cor",
    "nivel_instrucao",
    "cod_ocupacao",
    "grupamento_atividade",
    "posicao_ocupacao",
    "rendimento_habitual",
    "rendimento_efetivo",
    "horas_habituais",
    "horas_efetivas",
    "peso",
)

ILO_COLUMNS = (
    "ISCO_08",
    "Title",
    "mean_score_2025",
    "SD_2025",
    "potential25",
)

REGION_BY_STATE = {
    "RO": "Norte",
    "AC": "Norte",
    "AM": "Norte",
    "RR": "Norte",
    "PA": "Norte",
    "AP": "Norte",
    "TO": "Norte",
    "MA": "Nordeste",
    "PI": "Nordeste",
    "CE": "Nordeste",
    "RN": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "AL": "Nordeste",
    "SE": "Nordeste",
    "BA": "Nordeste",
    "MG": "Sudeste",
    "ES": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    "PR": "Sul",
    "SC": "Sul",
    "RS": "Sul",
    "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "DF": "Centro-Oeste",
}

MAJOR_OCCUPATION_GROUPS = {
    "1": "Dirigentes e gerentes",
    "2": "Profissionais das ciências",
    "3": "Técnicos nível médio",
    "4": "Apoio administrativo",
    "5": "Serviços e vendedores",
    "6": "Agropecuária qualificada",
    "7": "Indústria qualificada",
    "8": "Operadores de máquinas",
    "9": "Ocupações elementares",
}

AGGREGATED_RACE = {
    "1": "Branca",
    "2": "Negra",
    "4": "Negra",
    "3": "Outras",
    "5": "Outras",
    "9": "Outras",
}

FORMAL_POSITIONS = {"1", "3", "5"}
AGE_BINS = [0, 25, 35, 45, 55, 100]
AGE_LABELS = ["18-24", "25-34", "35-44", "45-54", "55+"]
CRITICAL_AI_SECTORS = {
    "Informação e Comunicação",
    "Finanças e Seguros",
    "Serviços Profissionais",
}


def validate_pnad_period(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("PNAD input is empty; expected 2025 Q3.")
    year = pd.to_numeric(frame["ano"], errors="coerce")
    quarter = pd.to_numeric(frame["trimestre"], errors="coerce")
    observed = set(zip(year.dropna().astype(int), quarter.dropna().astype(int)))
    if observed != {(EXPECTED_YEAR, EXPECTED_QUARTER)}:
        raise ValueError(
            "PNAD input must contain exactly 2025 Q3; "
            f"observed periods: {sorted(observed)}"
        )


def load_pnad(raw_dir: Path, billing_project: str | None) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    local_path = raw_dir / PNAD_FILENAME
    if local_path.exists():
        frame = pd.read_parquet(local_path)
        validate_pnad_period(frame)
        return frame
    if not billing_project:
        raise FileNotFoundError(
            f"Missing {local_path}. Provide --billing-project to download "
            "the exact PNAD 2025 Q3 extract."
        )

    try:
        import basedosdados as bd
    except ImportError as exc:
        raise RuntimeError(
            "Full Section 3 download requires requirements-full.txt."
        ) from exc

    query = f"""
    SELECT
        ano, trimestre, sigla_uf,
        v2007 AS sexo,
        v2009 AS idade,
        v2010 AS raca_cor,
        vd3004 AS nivel_instrucao,
        v4010 AS cod_ocupacao,
        v4013 AS grupamento_atividade,
        vd4009 AS posicao_ocupacao,
        vd4016 AS rendimento_habitual,
        vd4020 AS rendimento_efetivo,
        vd4031 AS horas_habituais,
        vd4035 AS horas_efetivas,
        v1028 AS peso
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano = {EXPECTED_YEAR}
      AND trimestre = {EXPECTED_QUARTER}
      AND v4010 IS NOT NULL
    """
    frame = bd.read_sql(query, billing_project_id=billing_project)
    validate_pnad_period(frame)
    frame.to_parquet(local_path, index=False, compression="zstd")
    return frame


def load_ilo(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / ILO_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Missing ILO workbook: {path}. See README.md for the exact source."
        )
    observed_hash = sha256_file(path)
    if observed_hash != EXPECTED_ILO_SHA256:
        raise ValueError(
            "ILO workbook SHA-256 differs from the dissertation source. "
            f"Expected {EXPECTED_ILO_SHA256}; observed {observed_hash}."
        )
    return pd.read_excel(path)


def process_ilo(raw: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(ILO_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"ILO workbook is missing required columns: {missing}")
    renamed = raw.rename(
        columns={
            "ISCO_08": "isco_08",
            "Title": "occupation_title",
            "mean_score_2025": "exposure_score",
            "SD_2025": "exposure_sd",
            "potential25": "exposure_gradient",
        }
    )
    result = (
        renamed.groupby("isco_08", dropna=False)
        .agg(
            occupation_title=("occupation_title", "first"),
            exposure_score=("exposure_score", "mean"),
            exposure_sd=("exposure_sd", "mean"),
            exposure_gradient=("exposure_gradient", "first"),
        )
        .reset_index()
    )
    result["isco_08_str"] = (
        pd.to_numeric(result["isco_08"], errors="raise")
        .astype(int)
        .astype(str)
        .str.zfill(4)
    )
    return result


def clean_pnad(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    missing = sorted(set(PNAD_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"PNAD input is missing required columns: {missing}")
    validate_pnad_period(raw)

    frame = raw.copy()
    initial_rows = len(frame)
    frame["cod_ocupacao"] = normalize_code(frame["cod_ocupacao"], 4)
    numeric_columns = [
        "idade",
        "rendimento_habitual",
        "rendimento_efetivo",
        "horas_habituais",
        "horas_efetivas",
        "peso",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["cod_ocupacao", "idade", "peso"])
    frame = frame[frame["idade"].between(18, 65)]
    frame = frame[~frame["cod_ocupacao"].isin(["0000", "9999"])].copy()

    frame["tem_renda"] = (
        frame["rendimento_habitual"].notna()
        & frame["rendimento_habitual"].gt(0)
    ).astype(int)
    frame["formal"] = (
        frame["posicao_ocupacao"].astype("string").isin(FORMAL_POSITIONS)
    ).astype(int)
    frame["faixa_etaria"] = pd.cut(
        frame["idade"],
        bins=AGE_BINS,
        labels=AGE_LABELS,
    )
    frame["regiao"] = frame["sigla_uf"].map(REGION_BY_STATE)
    frame["raca_agregada"] = (
        frame["raca_cor"].astype("string").map(AGGREGATED_RACE)
    )
    frame["grande_grupo"] = (
        frame["cod_ocupacao"].str[0].map(MAJOR_OCCUPATION_GROUPS)
    )
    frame["sexo_texto"] = (
        frame["sexo"].astype("string").map({"1": "Homem", "2": "Mulher"})
    )

    income = frame["tem_renda"].eq(1)
    p01 = weighted_quantile(
        frame.loc[income, "rendimento_habitual"],
        frame.loc[income, "peso"],
        0.01,
    )
    p99 = weighted_quantile(
        frame.loc[income, "rendimento_habitual"],
        frame.loc[income, "peso"],
        0.99,
    )
    frame["rendimento_winsor"] = frame["rendimento_habitual"].clip(p01, p99)
    frame["faixa_renda_sm"] = pd.cut(
        frame["rendimento_habitual"] / SALARY_MINIMUM_BRL,
        bins=[0, 1, 2, 3, 5, float("inf")],
        labels=["Até 1 SM", "1-2 SM", "2-3 SM", "3-5 SM", "5+ SM"],
        right=True,
        include_lowest=True,
    )
    return frame, {
        "initial_rows": initial_rows,
        "after_filters": len(frame),
    }


def apply_hierarchical_crosswalk(
    pnad: pd.DataFrame,
    ilo: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    frame = pnad.copy()
    ilo = ilo.copy()
    ilo["isco_08_str"] = normalize_code(ilo["isco_08_str"], 4)

    score_maps = {
        digits: ilo.groupby(ilo["isco_08_str"].str[:digits])[
            "exposure_score"
        ].mean()
        for digits in (4, 3, 2, 1)
    }
    gradient_4d = (
        ilo.groupby("isco_08_str")["exposure_gradient"].first().to_dict()
    )
    frame["exposure_score"] = np.nan
    frame["exposure_gradient"] = None
    frame["match_level"] = None

    for digits in (4, 3, 2, 1):
        missing = frame["exposure_score"].isna()
        keys = frame.loc[missing, "cod_ocupacao"].str[:digits]
        mapped = keys.map(score_maps[digits])
        matched_index = mapped[mapped.notna()].index
        frame.loc[matched_index, "exposure_score"] = mapped.loc[matched_index]
        frame.loc[matched_index, "match_level"] = f"{digits}-digit"
        if digits == 4:
            frame.loc[matched_index, "exposure_gradient"] = frame.loc[
                matched_index, "cod_ocupacao"
            ].map(gradient_4d)
        else:
            frame.loc[matched_index, "exposure_gradient"] = "Sem classificação"

    frame.loc[
        frame["exposure_score"].isna(), "exposure_gradient"
    ] = "Sem classificação"
    coverage: dict[str, float | int] = {}
    total_weight = float(frame["peso"].sum())
    for digits in (4, 3, 2, 1):
        label = f"{digits}-digit"
        mask = frame["match_level"].eq(label)
        coverage[f"rows_{digits}_digit"] = int(mask.sum())
        coverage[f"population_{digits}_digit"] = float(
            frame.loc[mask, "peso"].sum()
        )
    unmatched = frame["exposure_score"].isna()
    coverage["rows_unmatched"] = int(unmatched.sum())
    coverage["population_unmatched"] = float(
        frame.loc[unmatched, "peso"].sum()
    )
    coverage["population_total"] = total_weight
    return frame, coverage


def finalize_analytic_data(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    valid = result["exposure_score"].notna()
    result.loc[valid, "quintil_exposure"] = weighted_qcut(
        result.loc[valid, "exposure_score"],
        result.loc[valid, "peso"],
        q=5,
        labels=["Q1 (Baixa)", "Q2", "Q3", "Q4", "Q5 (Alta)"],
    )
    result.loc[valid, "decil_exposure"] = weighted_qcut(
        result.loc[valid, "exposure_score"],
        result.loc[valid, "peso"],
        q=10,
        labels=[f"D{number}" for number in range(1, 11)],
    )
    legacy_activity = (
        pd.to_numeric(result["grupamento_atividade"], errors="coerce")
        .astype("Int64")
        .astype("string")
    )
    normalized_activity = legacy_activity.str.zfill(5)
    result["setor_agregado_original"] = (
        legacy_activity.str[:2]
        .map(CNAE_SECAO_TO_SETOR)
        .fillna("Outros Serviços")
    )
    result["setor_agregado"] = (
        normalized_activity.str[:2]
        .map(CNAE_SECAO_TO_SETOR)
        .fillna("Outros Serviços")
    )
    result["setor_critico_ia"] = (
        result["setor_agregado"].isin(CRITICAL_AI_SECTORS).astype(int)
    )
    columns = [
        "ano",
        "trimestre",
        "sigla_uf",
        "regiao",
        "sexo",
        "sexo_texto",
        "idade",
        "faixa_etaria",
        "raca_cor",
        "raca_agregada",
        "nivel_instrucao",
        "cod_ocupacao",
        "grande_grupo",
        "grupamento_atividade",
        "setor_agregado_original",
        "setor_agregado",
        "setor_critico_ia",
        "posicao_ocupacao",
        "formal",
        "tem_renda",
        "rendimento_habitual",
        "rendimento_winsor",
        "rendimento_efetivo",
        "horas_habituais",
        "horas_efetivas",
        "faixa_renda_sm",
        "peso",
        "exposure_score",
        "exposure_gradient",
        "match_level",
        "quintil_exposure",
        "decil_exposure",
    ]
    return result[[column for column in columns if column in result.columns]]


def build_section3_data(
    *,
    raw_dir: Path,
    derived_dir: Path,
    billing_project: str | None,
) -> tuple[Path, Path, Path]:
    pnad_raw = load_pnad(raw_dir, billing_project)
    ilo_raw = load_ilo(raw_dir)
    pnad, filter_diagnostics = clean_pnad(pnad_raw)
    ilo = process_ilo(ilo_raw)
    matched, coverage = apply_hierarchical_crosswalk(pnad, ilo)
    final = finalize_analytic_data(matched)

    derived_dir.mkdir(parents=True, exist_ok=True)
    analytic_path = derived_dir / "pnad_ilo_merged.parquet"
    ilo_path = derived_dir / "ilo_exposure_clean.parquet"
    diagnostic_path = derived_dir / "data_build_diagnostics.csv"
    final.to_parquet(analytic_path, index=False, compression="zstd")
    ilo.to_parquet(ilo_path, index=False, compression="zstd")
    diagnostics: dict[str, Any] = {
        **filter_diagnostics,
        **coverage,
        "final_rows": len(final),
        "final_population": float(final["peso"].sum()),
        "final_states": int(final["sigla_uf"].nunique()),
        "year": EXPECTED_YEAR,
        "quarter": EXPECTED_QUARTER,
    }
    with diagnostic_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["metric", "value"])
        writer.writerows(sorted(diagnostics.items()))
    return analytic_path, ilo_path, diagnostic_path


def normalize_code(values: pd.Series, width: int) -> pd.Series:
    return (
        values.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(width)
    )


def weighted_quantile(
    values: pd.Series,
    weights: pd.Series,
    quantile: float,
) -> float:
    numeric_values = pd.to_numeric(values, errors="coerce")
    numeric_weights = pd.to_numeric(weights, errors="coerce")
    valid = numeric_values.notna() & numeric_weights.notna() & numeric_weights.gt(0)
    if not valid.any():
        return float("nan")
    order = np.argsort(numeric_values.loc[valid].to_numpy(dtype=float))
    sorted_values = numeric_values.loc[valid].to_numpy(dtype=float)[order]
    sorted_weights = numeric_weights.loc[valid].to_numpy(dtype=float)[order]
    cutoff = quantile * sorted_weights.sum()
    return float(sorted_values[np.searchsorted(np.cumsum(sorted_weights), cutoff)])


def weighted_qcut(
    values: pd.Series,
    weights: pd.Series,
    q: int,
    labels: list[str],
) -> pd.Series:
    breakpoints = [float(values.min()) - 1e-10]
    breakpoints.extend(
        weighted_quantile(values, weights, index / q) for index in range(1, q)
    )
    breakpoints.append(float(values.max()) + 1e-10)
    unique = sorted(set(breakpoints))
    selected_labels = labels if len(labels) == len(unique) - 1 else None
    return pd.cut(
        values,
        bins=unique,
        labels=selected_labels,
        include_lowest=True,
    )
