"""Build the five published Section 3 tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import (
    AGE_ORDER,
    EDUCATION_LABELS,
    FORMAL_LABELS,
    GRADIENT_INTERPRETATION,
    GRADIENT_LABELS,
    GRADIENT_ORDER,
    INCOME_ORDER,
    LOW_GRADIENTS,
    MODERATE_GRADIENTS,
    RACE_ORDER,
    RAW_PNAD_QUERY_ALIASES,
    SALARY_MINIMUM_BRL,
    SEM_CLASS,
    SEX_ORDER,
)
from .data import group_summary, official_data, scored_data
from .formatting import (
    fmt_int,
    fmt_m,
    fmt_m2,
    fmt_pct,
    fmt_score2,
    fmt_score3,
    markdown_table,
    weighted_mean,
    write_text,
)


TABLE_SPECS = (
    (
        "table_3_1_base_specs.md",
        "Table 3.1. Analytic Base Specifications",
    ),
    (
        "table_3_2_gradients.md",
        "Table 3.2. Population by AI Exposure Gradient",
    ),
    (
        "table_3_3_high_exposure_occupations.md",
        "Table 3.3. Largest High-Exposure Occupations",
    ),
    (
        "table_3_4_sector_exposure.md",
        "Table 3.4. AI Exposure by Sector",
    ),
    (
        "table_3_5_demographics_summary.md",
        "Table 3.5. Demographic Exposure Summary",
    ),
)


def build_base_specs(
    frame: pd.DataFrame,
    ilo_count: int | None,
) -> pd.DataFrame:
    total_population = float(frame["peso"].sum() / 1e6)
    score_population = float(
        frame.loc[frame["is_score_valid"], "peso"].sum() / 1e6
    )
    matched_occupations = int(
        frame.loc[frame["is_score_valid"], "cod_ocupacao"].nunique()
    )
    total_occupations = int(frame["cod_ocupacao"].nunique())
    rows = [
        ("Source", "PNADc 2025 Q3 (IBGE) + ILO WP140 (Gmyrek et al., 2025)"),
        (
            "Universe",
            "Employed workers ages 18-65 with a valid occupation code",
        ),
        ("Sample observations", fmt_int(len(frame))),
        ("Population represented (millions)", fmt_m(total_population)),
        (
            "Population with exposure score (millions)",
            fmt_m(score_population),
        ),
        ("Sample weight", "V1028"),
        (
            "PNAD source aliases selected",
            str(len(RAW_PNAD_QUERY_ALIASES)),
        ),
        (
            "ILO ISCO-08 occupations",
            str(ilo_count) if ilo_count is not None else "Not available",
        ),
        (
            "COD occupations with match",
            f"{matched_occupations} of {total_occupations}",
        ),
        (
            "Score coverage (% population)",
            fmt_pct(
                frame.loc[frame["is_score_valid"], "peso"].sum()
                / frame["peso"].sum()
                * 100
            ),
        ),
        (
            "4-digit match (% rows)",
            fmt_pct(
                frame["match_level"].eq("4-digit").sum() / len(frame) * 100
            ),
        ),
        (
            "3-digit match (% rows)",
            fmt_pct(
                frame["match_level"].eq("3-digit").sum() / len(frame) * 100
            ),
        ),
        (
            "No score (% rows)",
            fmt_pct(frame["exposure_score"].isna().sum() / len(frame) * 100),
        ),
        ("Federal units", str(frame["sigla_uf"].nunique())),
        (
            "Original sector categories in input",
            str(frame["setor_agregado_original"].nunique()),
        ),
        (
            "Corrected CNAE sector categories",
            str(frame["sector_corrected"].nunique()),
        ),
        (
            "Reference minimum wage",
            f"BRL {SALARY_MINIMUM_BRL:,}".replace(",", "."),
        ),
    ]
    return pd.DataFrame(rows, columns=["Item", "Value"])


def build_gradients(frame: pd.DataFrame) -> pd.DataFrame:
    score = scored_data(frame)
    total = float(score["peso"].sum())
    rows: list[dict[str, object]] = []
    for gradient in [*GRADIENT_ORDER, SEM_CLASS]:
        group = score[score["exposure_gradient"].eq(gradient)]
        weight = float(group["peso"].sum())
        rows.append(
            {
                "Category": GRADIENT_LABELS[gradient],
                "Interpretation": GRADIENT_INTERPRETATION[gradient],
                "Population (M)": fmt_m(weight / 1e6),
                "%": fmt_pct(weight / total * 100),
            }
        )
    return pd.DataFrame(rows)


def build_high_exposure_occupations(
    frame: pd.DataFrame,
    title_map: dict[str, str],
) -> pd.DataFrame:
    official = official_data(frame)
    high = official[official["is_high_exposure"]]
    rows = []
    for (code, major_group), group in high.groupby(
        ["cod_ocupacao", "grande_grupo"]
    ):
        rows.append(
            {
                "COD": code,
                "Occupation title (ILO)": title_map.get(code, ""),
                "Major group": major_group,
                "Exposure mean": weighted_mean(
                    group["exposure_score"],
                    group["peso"],
                ),
                "Population (M)": float(group["peso"].sum() / 1e6),
                "Gradient": group["exposure_gradient"].mode().iloc[0],
            }
        )
    output = (
        pd.DataFrame(rows)
        .sort_values("Population (M)", ascending=False)
        .head(5)
    )
    output["Exposure mean"] = output["Exposure mean"].map(fmt_score2)
    output["Population (M)"] = output["Population (M)"].map(fmt_m2)
    output["Gradient"] = output["Gradient"].map(GRADIENT_LABELS)
    return output


def build_sector_exposure(frame: pd.DataFrame) -> pd.DataFrame:
    base = official_data(frame)
    total_brazil = float(base["peso"].sum())
    rows = []
    for sector, group in base.groupby("sector_corrected"):
        total = float(group["peso"].sum())
        high = float(group.loc[group["is_high_exposure"], "peso"].sum())
        low = float(
            group.loc[
                group["exposure_gradient"].isin(LOW_GRADIENTS),
                "peso",
            ].sum()
        )
        moderate = float(
            group.loc[
                group["exposure_gradient"].isin(MODERATE_GRADIENTS),
                "peso",
            ].sum()
        )
        exposed = moderate + high
        rows.append(
            {
                "Sector": sector,
                "Total (M)": total / 1e6,
                "% BR": total / total_brazil * 100,
                "Exposure Mean": weighted_mean(
                    group["exposure_score"],
                    group["peso"],
                ),
                "Low (M)": low / 1e6,
                "Low (%)": low / total * 100,
                "Moderate (M)": moderate / 1e6,
                "Moderate (%)": moderate / total * 100,
                "High (M)": high / 1e6,
                "High (%)": high / total * 100,
                "Exposed (M)": exposed / 1e6,
                "Exposed (%)": exposed / total * 100,
            }
        )
    output = pd.DataFrame(rows).sort_values(
        "Exposure Mean",
        ascending=False,
    )
    for column in [
        "Total (M)",
        "Low (M)",
        "Moderate (M)",
        "High (M)",
        "Exposed (M)",
    ]:
        output[column] = output[column].map(fmt_m2)
    for column in [
        "% BR",
        "Low (%)",
        "Moderate (%)",
        "High (%)",
        "Exposed (%)",
    ]:
        output[column] = output[column].map(fmt_pct)
    output["Exposure Mean"] = output["Exposure Mean"].map(fmt_score3)
    return output


def build_demographics(frame: pd.DataFrame) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []

    def add_dimension(name: str, summary: pd.DataFrame) -> None:
        if summary.empty:
            return
        part = summary.copy()
        part.insert(0, "Dimension", name)
        pieces.append(part)

    add_dimension("Sex", group_summary(frame, "sexo_texto", SEX_ORDER))
    add_dimension("Race", group_summary(frame, "raca_agregada", RACE_ORDER))
    add_dimension("Age", group_summary(frame, "faixa_etaria", AGE_ORDER))
    add_dimension(
        "Education",
        group_summary(
            frame,
            "nivel_instrucao",
            list(EDUCATION_LABELS),
            category_labels=EDUCATION_LABELS,
        ),
    )
    add_dimension(
        "Income",
        group_summary(
            frame[frame["tem_renda"].eq(1)],
            "faixa_renda_sm",
            INCOME_ORDER,
        ),
    )
    add_dimension(
        "Formality",
        group_summary(
            frame,
            "formal",
            [1, 0],
            category_labels=FORMAL_LABELS,
        ),
    )

    output = pd.concat(pieces, ignore_index=True)
    output["population_m"] = output["population_m"].map(fmt_m2)
    output["mean_score"] = output["mean_score"].map(fmt_score3)
    output["low_pct"] = output["low_pct"].map(fmt_pct)
    output["moderate_pct"] = output["moderate_pct"].map(fmt_pct)
    output["high_pct"] = output["high_pct"].map(fmt_pct)
    output["high_m"] = output["high_m"].map(fmt_m2)
    return output.rename(
        columns={
            "category": "Category",
            "population_m": "Population (M)",
            "mean_score": "Exposure Mean",
            "low_pct": "Low (%)",
            "moderate_pct": "Moderate (%)",
            "high_pct": "High (%)",
            "high_m": "High (M)",
        }
    )


def write_tables(
    frame: pd.DataFrame,
    output_dir: Path,
    *,
    ilo_count: int | None,
    title_map: dict[str, str],
) -> list[Path]:
    tables = [
        build_base_specs(frame, ilo_count),
        build_gradients(frame),
        build_high_exposure_occupations(frame, title_map),
        build_sector_exposure(frame),
        build_demographics(frame),
    ]
    written: list[Path] = []
    for (filename, title), table in zip(TABLE_SPECS, tables, strict=True):
        markdown_path = output_dir / "tables" / filename
        csv_path = markdown_path.with_suffix(".csv")
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(csv_path, index=False, lineterminator="\n")
        write_text(
            markdown_path,
            f"# {title}\n\n"
            f"{markdown_table(list(table.columns), table.to_records(index=False))}\n",
        )
        written.extend([csv_path, markdown_path])
    return written
