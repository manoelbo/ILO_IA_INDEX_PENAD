"""Load and summarize the frozen Section 3 analytic cross-section."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import (
    GRADIENT_ORDER,
    GRADIENT_TO_GROUP,
    HIGH_GRADIENTS,
    LOW_GRADIENTS,
    MODERATE_GRADIENTS,
)
from .formatting import safe_divide, weighted_mean


REQUIRED_ANALYTIC_COLUMNS = {
    "ano",
    "trimestre",
    "sigla_uf",
    "sexo_texto",
    "idade",
    "faixa_etaria",
    "raca_agregada",
    "nivel_instrucao",
    "cod_ocupacao",
    "grande_grupo",
    "grupamento_atividade",
    "setor_agregado_original",
    "setor_agregado",
    "formal",
    "tem_renda",
    "faixa_renda_sm",
    "peso",
    "exposure_score",
    "exposure_gradient",
    "match_level",
}


def load_ilo_metadata(ilo_file: Path) -> tuple[int | None, dict[str, str]]:
    if not ilo_file.is_file():
        return None, {}
    raw = (
        pd.read_parquet(ilo_file)
        if ilo_file.suffix.lower() == ".parquet"
        else pd.read_excel(ilo_file)
    )
    code_column = "ISCO_08" if "ISCO_08" in raw.columns else "isco_08"
    title_column = "Title" if "Title" in raw.columns else "occupation_title"
    if code_column not in raw.columns:
        raise ValueError(f"ILO metadata has no occupation-code column: {ilo_file}")

    codes = raw[code_column].dropna().astype(int).astype(str).str.zfill(4)
    occupation_count = int(codes.nunique())
    title_map: dict[str, str] = {}
    if title_column in raw.columns:
        titles = raw.assign(_code=codes)
        title_map = (
            titles.dropna(subset=["_code"])
            .drop_duplicates("_code")
            .set_index("_code")[title_column]
            .astype(str)
            .to_dict()
        )
    return occupation_count, title_map


def read_data(input_path: Path) -> pd.DataFrame:
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    frame = (
        pd.read_parquet(input_path)
        if input_path.suffix.lower() == ".parquet"
        else pd.read_csv(input_path)
    )
    missing = sorted(REQUIRED_ANALYTIC_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Input file is missing required columns: {missing}")

    frame = frame.copy()
    frame["cod_ocupacao"] = (
        frame["cod_ocupacao"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.zfill(4)
    )
    frame["peso"] = pd.to_numeric(frame["peso"], errors="coerce")
    frame["exposure_score"] = pd.to_numeric(
        frame["exposure_score"],
        errors="coerce",
    )
    frame["idade"] = pd.to_numeric(frame["idade"], errors="coerce")
    frame["nivel_instrucao"] = pd.to_numeric(
        frame["nivel_instrucao"],
        errors="coerce",
    ).astype("Int64")
    frame["formal"] = pd.to_numeric(
        frame["formal"],
        errors="coerce",
    ).astype("Int64")
    frame["grupo3"] = frame["exposure_gradient"].map(GRADIENT_TO_GROUP)
    frame["is_official_gradient"] = frame["exposure_gradient"].isin(
        GRADIENT_ORDER
    )
    frame["is_high_exposure"] = frame["exposure_gradient"].isin(
        HIGH_GRADIENTS
    )
    frame["is_score_valid"] = frame["exposure_score"].notna()
    frame["sector_corrected"] = frame["setor_agregado"]
    return frame


def official_data(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["is_official_gradient"]].copy()


def scored_data(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["is_score_valid"]].copy()


def group_summary(
    frame: pd.DataFrame,
    column: str,
    order: list[object],
    *,
    category_labels: dict[object, str] | None = None,
) -> pd.DataFrame:
    score = scored_data(frame)
    official = official_data(frame)
    rows: list[dict[str, object]] = []
    for category in order:
        score_group = score[score[column].eq(category)]
        official_group = official[official[column].eq(category)]
        if score_group.empty and official_group.empty:
            continue
        total_weight = float(official_group["peso"].sum())
        high_weight = float(
            official_group.loc[
                official_group["is_high_exposure"],
                "peso",
            ].sum()
        )
        rows.append(
            {
                "category": (
                    category_labels.get(category, str(category))
                    if category_labels
                    else str(category)
                ),
                "population_m": total_weight / 1e6,
                "mean_score": weighted_mean(
                    score_group["exposure_score"],
                    score_group["peso"],
                ),
                "low_pct": safe_divide(
                    float(
                        official_group.loc[
                            official_group["exposure_gradient"].isin(
                                LOW_GRADIENTS
                            ),
                            "peso",
                        ].sum()
                    ),
                    total_weight,
                )
                * 100,
                "moderate_pct": safe_divide(
                    float(
                        official_group.loc[
                            official_group["exposure_gradient"].isin(
                                MODERATE_GRADIENTS
                            ),
                            "peso",
                        ].sum()
                    ),
                    total_weight,
                )
                * 100,
                "high_pct": safe_divide(high_weight, total_weight) * 100,
                "high_m": high_weight / 1e6,
            }
        )
    return pd.DataFrame(rows)


def state_high_table(frame: pd.DataFrame) -> pd.DataFrame:
    base = official_data(frame)
    rows = []
    for state, group in base.groupby("sigla_uf"):
        total = float(group["peso"].sum())
        high = float(group.loc[group["is_high_exposure"], "peso"].sum())
        rows.append(
            {
                "UF": state,
                "Total (M)": total / 1e6,
                "High (M)": high / 1e6,
                "High (%)": high / total * 100,
            }
        )
    return pd.DataFrame(rows).sort_values("High (%)", ascending=False)
