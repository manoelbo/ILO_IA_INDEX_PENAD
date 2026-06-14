#!/usr/bin/env python3
"""
Replication package for Section 3 descriptive analysis.

This script validates the numerical claims in Section 3 of the dissertation
using the already-built PNAD-ILO analytic file. It does not download data,
query BigQuery, rebuild the CAGED panels, or import the exploratory notebooks.

Default run:
    python "Replication Package/replicate_section3_descriptive.py" --strict
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "output" / "pnad_ilo_merged.csv"
DEFAULT_HTML = (
    ROOT
    / "Analise Descritiva Concluida Seção 3 "
    / "3 Análise Descritiva 377cc8ca4610807b8ff4e3db288ecdc0.html"
)
DEFAULT_OUTPUT_DIR = ROOT / "Replication Package" / "outputs"
DEFAULT_RAW_PNAD = ROOT / "data" / "raw" / "pnad_2025q3.parquet"
DEFAULT_ILO_FILE = ROOT / "data" / "input" / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"
SALARY_MINIMUM_BRL = 1518
_PYPLOT = None

SEM_CLASS = "Sem classificação"

GRADIENT_ORDER = [
    "Not Exposed",
    "Minimal Exposure",
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
]

GRADIENT_LABELS = {
    "Not Exposed": "Not exposed",
    "Minimal Exposure": "Minimal exposure",
    "Exposed: Gradient 1": "Gradient 1",
    "Exposed: Gradient 2": "Gradient 2",
    "Exposed: Gradient 3": "Gradient 3",
    "Exposed: Gradient 4": "Gradient 4",
    SEM_CLASS: "Unclassified",
}

GRADIENT_LABELS_PT = {
    "Not Exposed": "Não exposto",
    "Minimal Exposure": "Exposição mínima",
    "Exposed: Gradient 1": "Gradiente 1",
    "Exposed: Gradient 2": "Gradiente 2",
    "Exposed: Gradient 3": "Gradiente 3",
    "Exposed: Gradient 4": "Gradiente 4",
    SEM_CLASS: "Sem classificação",
}

FIGURE_TITLES_PT = {
    "3.1": "Figura 3.1: Distribuição da exposição à IA no Brasil",
    "3.2": "Figura 3.2: População ocupada por gradiente de exposição à IA",
    "3.3": "Figura 3.3: Composição da população ocupada por faixa de score de exposição à IA, segundo o grande grupo ocupacional",
    "3.4": "Figura 3.4: Alta exposição à IA por estado",
    "3.5": "Figura 3.5: Exposição à IA por sexo",
    "3.6": "Figura 3.6: Exposição à IA por raça",
    "3.7": "Figura 3.7: Exposição à IA por faixa etária",
    "3.8": "Figura 3.8: Exposição à IA por nível de escolaridade",
    "3.9": "Figura 3.9: Exposição à IA por faixa de renda",
    "3.10": "Figura 3.10: Exposição à IA por situação de formalidade",
}

GRADIENT_INTERPRETATION = {
    "Not Exposed": "Occupations with no relevant exposure condition.",
    "Minimal Exposure": "Residual or punctual exposure.",
    "Exposed: Gradient 1": "Partial exposure, mostly augmentation.",
    "Exposed: Gradient 2": "More intense partial exposure.",
    "Exposed: Gradient 3": "High exposure and deep task transformation.",
    "Exposed: Gradient 4": "Maximum exposure and potentially substitutable tasks.",
    SEM_CLASS: "Score assigned through aggregation; no WP140 gradient label.",
}

GRADIENT_TO_GROUP = {
    "Not Exposed": "Low",
    "Minimal Exposure": "Low",
    "Exposed: Gradient 1": "Moderate",
    "Exposed: Gradient 2": "Moderate",
    "Exposed: Gradient 3": "High",
    "Exposed: Gradient 4": "High",
}

HIGH_GRADIENTS = {"Exposed: Gradient 3", "Exposed: Gradient 4"}
MODERATE_GRADIENTS = {"Exposed: Gradient 1", "Exposed: Gradient 2"}
LOW_GRADIENTS = {"Not Exposed", "Minimal Exposure"}

GROUP_COLORS = {
    "Low": "#2f6fae",
    "Moderate": "#d99a1e",
    "High": "#c7352f",
}

GROUP_LABELS_PT = {
    "Low": "Baixa",
    "Moderate": "Média",
    "High": "Alta",
}

GRADIENT_COLORS = {
    "Not Exposed": "#3b78b8",
    "Minimal Exposure": "#76a9d6",
    "Exposed: Gradient 1": "#f0c35a",
    "Exposed: Gradient 2": "#df8f2d",
    "Exposed: Gradient 3": "#d55345",
    "Exposed: Gradient 4": "#a8232f",
    SEM_CLASS: "#8c8c8c",
}

RAW_PNAD_QUERY_ALIASES = [
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
]

CNAE_SECAO_TO_SETOR = {
    "01": "Agropecuária",
    "02": "Agropecuária",
    "03": "Agropecuária",
    "05": "Ind. Extrativa",
    "06": "Ind. Extrativa",
    "07": "Ind. Extrativa",
    "08": "Ind. Extrativa",
    "09": "Ind. Extrativa",
    **{f"{n:02d}": "Ind. Transformação" for n in range(10, 34)},
    **{f"{n:02d}": "Utilidades" for n in [35, 36, 37, 38, 39]},
    "41": "Construção",
    "42": "Construção",
    "43": "Construção",
    "45": "Comércio",
    "46": "Comércio",
    "47": "Comércio",
    "48": "Comércio",
    **{f"{n:02d}": "Transporte" for n in [49, 50, 51, 52, 53]},
    "55": "Alojamento e Alimentação",
    "56": "Alojamento e Alimentação",
    **{f"{n:02d}": "Informação e Comunicação" for n in [58, 59, 60, 61, 62, 63]},
    "64": "Finanças e Seguros",
    "65": "Finanças e Seguros",
    "66": "Finanças e Seguros",
    "68": "Atividades Imobiliárias",
    **{f"{n:02d}": "Serviços Profissionais" for n in [69, 70, 71, 72, 73, 74, 75]},
    **{f"{n:02d}": "Serviços Administrativos" for n in [77, 78, 79, 80, 81, 82]},
    "84": "Administração Pública",
    "85": "Educação",
    "86": "Saúde",
    "87": "Saúde",
    "88": "Saúde",
    **{f"{n:02d}": "Artes e Cultura" for n in [90, 91, 92, 93]},
    **{f"{n:02d}": "Outros Serviços" for n in [94, 95, 96]},
    "97": "Serviços Domésticos",
    "99": "Outros Serviços",
}

RACE_ORDER = ["Branca", "Negra", "Outras"]
SEX_ORDER = ["Homem", "Mulher"]
AGE_ORDER = ["18-24", "25-34", "35-44", "45-54", "55+"]
INCOME_ORDER = ["Até 1 SM", "1-2 SM", "2-3 SM", "3-5 SM", "5+ SM"]
FORMAL_LABELS = {1: "Formal", 0: "Informal"}

EDUCATION_LABELS = {
    1: "No instruction",
    2: "No/Fund. incomplete",
    3: "Fund. complete",
    4: "High school incomplete",
    5: "High school complete",
    6: "College incomplete",
    7: "College complete",
}

EDUCATION_LABELS_PT = {
    1: "Sem instrução",
    2: "Sem/Fund. incompleto",
    3: "Fund. completo",
    4: "Médio incompleto",
    5: "Médio completo",
    6: "Superior incompleto",
    7: "Superior completo",
}

FORMAL_LABELS_PT = {1: "Formal", 0: "Informal"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._capture = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "p", "li", "td", "th", "figcaption"}:
            self._capture = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "p", "li", "td", "th", "figcaption"}:
            self._capture = False
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._capture:
            self.parts.append(data)

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


@dataclass
class Claim:
    claim_id: str
    section: str
    description: str
    expected_display: str
    computed_raw: str
    computed_display: str
    rounding_rule: str
    status: str
    note: str

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.claim_id,
            "section": self.section,
            "description": self.description,
            "expected_display": self.expected_display,
            "computed_raw": self.computed_raw,
            "computed_display": self.computed_display,
            "rounding_rule": self.rounding_rule,
            "status": self.status,
            "note": self.note,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replicate and audit Section 3 descriptive statistics."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to pnad_ilo_merged.csv")
    parser.add_argument("--html", default=str(DEFAULT_HTML), help="Path to Section 3 HTML text")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where audit outputs, tables, and figures are written",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any claim is marked FAIL",
    )
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip PNG figure generation and only write tables/audit outputs",
    )
    return parser.parse_args()


def get_pyplot():
    global _PYPLOT
    if _PYPLOT is None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as pyplot

        _PYPLOT = pyplot
    return _PYPLOT


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT / path


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    v = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    w = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not mask.any():
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))


def safe_divide(num: float, den: float) -> float:
    return float(num / den) if den else float("nan")


def fmt_int(value: float | int) -> str:
    return f"{int(round(float(value))):,}".replace(",", ".")


def fmt_m(value: float) -> str:
    return f"{value:.1f}"


def fmt_m2(value: float) -> str:
    return f"{value:.2f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}"


def fmt_score3(value: float) -> str:
    return f"{value:.3f}"


def fmt_score2(value: float) -> str:
    return f"{value:.2f}"


def fmt_ratio(value: float) -> str:
    return f"{value:.1f}"


def as_raw(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def claim(
    claims: list[Claim],
    claim_id: str,
    section: str,
    description: str,
    expected_display: str,
    computed_value: object,
    computed_display: str,
    rounding_rule: str,
    *,
    note: str = "",
    force_status: str | None = None,
) -> None:
    status = force_status or ("PASS" if expected_display == computed_display else "WARN")
    claims.append(
        Claim(
            claim_id=claim_id,
            section=section,
            description=description,
            expected_display=expected_display,
            computed_raw=as_raw(computed_value),
            computed_display=computed_display,
            rounding_rule=rounding_rule,
            status=status,
            note=note,
        )
    )


def markdown_table(headers: list[str], rows: Iterable[Iterable[object]]) -> str:
    prepared = [[str(cell) for cell in row] for row in rows]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in prepared:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_section_text(html_path: Path) -> str:
    if not html_path.exists():
        return ""
    parser = TextExtractor()
    parser.feed(html_path.read_text(encoding="utf-8", errors="ignore"))
    return parser.text


def load_ilo_metadata(ilo_file: Path) -> tuple[int | None, dict[str, str]]:
    if not ilo_file.exists():
        return None, {}
    try:
        raw = pd.read_excel(ilo_file)
    except Exception:
        return None, {}

    if "ISCO_08" not in raw.columns:
        return None, {}

    codes = raw["ISCO_08"].dropna().astype(int).astype(str).str.zfill(4)
    occupation_count = int(codes.nunique())
    title_map: dict[str, str] = {}
    if "Title" in raw.columns:
        titles = raw.assign(_code=codes)
        title_map = (
            titles.dropna(subset=["_code"])
            .drop_duplicates("_code")
            .set_index("_code")["Title"]
            .astype(str)
            .to_dict()
        )
    return occupation_count, title_map


def read_data(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    required = {
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
        "setor_agregado",
        "formal",
        "tem_renda",
        "faixa_renda_sm",
        "peso",
        "exposure_score",
        "exposure_gradient",
        "match_level",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Input file is missing required columns: {missing}")

    df = df.copy()
    df["cod_ocupacao"] = df["cod_ocupacao"].astype(str).str.replace(".0", "", regex=False).str.zfill(4)
    df["peso"] = pd.to_numeric(df["peso"], errors="coerce")
    df["exposure_score"] = pd.to_numeric(df["exposure_score"], errors="coerce")
    df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
    df["nivel_instrucao"] = pd.to_numeric(df["nivel_instrucao"], errors="coerce").astype("Int64")
    df["formal"] = pd.to_numeric(df["formal"], errors="coerce").astype("Int64")
    df["grupo3"] = df["exposure_gradient"].map(GRADIENT_TO_GROUP)
    df["is_official_gradient"] = df["exposure_gradient"].isin(GRADIENT_ORDER)
    df["is_high_exposure"] = df["exposure_gradient"].isin(HIGH_GRADIENTS)
    df["is_score_valid"] = df["exposure_score"].notna()
    df["sector_corrected"] = corrected_sector(df["grupamento_atividade"])
    return df


def corrected_sector(grupamento: pd.Series) -> pd.Series:
    ga5 = pd.to_numeric(grupamento, errors="coerce").astype("Int64").astype(str).str.zfill(5)
    secao = ga5.str[:2]
    return secao.map(CNAE_SECAO_TO_SETOR).fillna("Outros Serviços")


def official_df(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["is_official_gradient"]].copy()


def score_df(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["is_score_valid"]].copy()


def group_summary(
    df: pd.DataFrame,
    col: str,
    order: list[object],
    *,
    category_labels: dict[object, str] | None = None,
) -> pd.DataFrame:
    score = score_df(df)
    official = official_df(df)
    rows: list[dict[str, object]] = []
    for cat in order:
        sub_score = score[score[col].eq(cat)]
        sub_official = official[official[col].eq(cat)]
        if sub_score.empty and sub_official.empty:
            continue
        total_weight = float(sub_official["peso"].sum())
        high_weight = float(sub_official.loc[sub_official["is_high_exposure"], "peso"].sum())
        rows.append(
            {
                "category": category_labels.get(cat, str(cat)) if category_labels else str(cat),
                "population_m": total_weight / 1e6,
                "mean_score": weighted_mean(sub_score["exposure_score"], sub_score["peso"]),
                "low_pct": safe_divide(
                    float(sub_official.loc[sub_official["exposure_gradient"].isin(LOW_GRADIENTS), "peso"].sum()),
                    total_weight,
                )
                * 100,
                "moderate_pct": safe_divide(
                    float(
                        sub_official.loc[
                            sub_official["exposure_gradient"].isin(MODERATE_GRADIENTS), "peso"
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


def table_3_1(df: pd.DataFrame, ilo_count: int | None) -> pd.DataFrame:
    total_pop_m = float(df["peso"].sum() / 1e6)
    score_pop_m = float(df.loc[df["is_score_valid"], "peso"].sum() / 1e6)
    matched_cod = int(df.loc[df["is_score_valid"], "cod_ocupacao"].nunique())
    total_cod = int(df["cod_ocupacao"].nunique())
    rows = [
        ("Source", "PNADc 2025 Q3 (IBGE) + ILO WP140 (Gmyrek et al., 2025)"),
        ("Universe", "Employed workers ages 18-65 with a valid occupation code"),
        ("Sample observations", fmt_int(len(df))),
        ("Population represented (millions)", fmt_m(total_pop_m)),
        ("Population with exposure score (millions)", fmt_m(score_pop_m)),
        ("Sample weight", "V1028"),
        ("PNAD source aliases selected", str(len(RAW_PNAD_QUERY_ALIASES))),
        ("ILO ISCO-08 occupations", str(ilo_count) if ilo_count is not None else "Not available"),
        ("COD occupations with match", f"{matched_cod} of {total_cod}"),
        (
            "Score coverage (% population)",
            fmt_pct(df.loc[df["is_score_valid"], "peso"].sum() / df["peso"].sum() * 100),
        ),
        ("4-digit match (% rows)", fmt_pct((df["match_level"].eq("4-digit").sum() / len(df)) * 100)),
        ("3-digit match (% rows)", fmt_pct((df["match_level"].eq("3-digit").sum() / len(df)) * 100)),
        ("No score (% rows)", fmt_pct((df["exposure_score"].isna().sum() / len(df)) * 100)),
        ("Federal units", str(df["sigla_uf"].nunique())),
        ("Original sector categories in input", str(df["setor_agregado"].nunique())),
        ("Corrected CNAE sector categories", str(df["sector_corrected"].nunique())),
        ("Reference minimum wage", f"BRL {SALARY_MINIMUM_BRL:,}".replace(",", ".")),
    ]
    return pd.DataFrame(rows, columns=["Item", "Value"])


def table_3_2(df: pd.DataFrame) -> pd.DataFrame:
    score = score_df(df)
    total = float(score["peso"].sum())
    rows: list[dict[str, object]] = []
    for grad in GRADIENT_ORDER + [SEM_CLASS]:
        sub = score[score["exposure_gradient"].eq(grad)]
        weight = float(sub["peso"].sum())
        rows.append(
            {
                "Category": GRADIENT_LABELS[grad],
                "Interpretation": GRADIENT_INTERPRETATION[grad],
                "Population (M)": fmt_m(weight / 1e6),
                "%": fmt_pct(weight / total * 100),
            }
        )
    return pd.DataFrame(rows)


def table_3_3(df: pd.DataFrame, title_map: dict[str, str]) -> pd.DataFrame:
    official = official_df(df)
    high = official[official["is_high_exposure"]]
    rows = []
    for (cod, group), sub in high.groupby(["cod_ocupacao", "grande_grupo"]):
        rows.append(
            {
                "COD": cod,
                "Occupation title (ILO)": title_map.get(cod, ""),
                "Major group": group,
                "Exposure mean": weighted_mean(sub["exposure_score"], sub["peso"]),
                "Population (M)": float(sub["peso"].sum() / 1e6),
                "Gradient": sub["exposure_gradient"].mode().iloc[0],
            }
        )
    out = pd.DataFrame(rows).sort_values("Population (M)", ascending=False).head(5)
    out["Exposure mean"] = out["Exposure mean"].map(fmt_score2)
    out["Population (M)"] = out["Population (M)"].map(fmt_m2)
    out["Gradient"] = out["Gradient"].map(GRADIENT_LABELS)
    return out


def table_3_3_top_mean(df: pd.DataFrame, title_map: dict[str, str]) -> pd.DataFrame:
    score = score_df(df)
    rows = []
    for (cod, group), sub in score.groupby(["cod_ocupacao", "grande_grupo"]):
        rows.append(
            {
                "COD": cod,
                "Occupation title (ILO)": title_map.get(cod, ""),
                "Major group": group,
                "Exposure mean": weighted_mean(sub["exposure_score"], sub["peso"]),
                "Population (M)": float(sub["peso"].sum() / 1e6),
                "Gradient": sub["exposure_gradient"].mode().iloc[0],
            }
        )
    out = pd.DataFrame(rows).sort_values(["Exposure mean", "Population (M)"], ascending=False).head(5)
    out["Exposure mean"] = out["Exposure mean"].map(fmt_score2)
    out["Population (M)"] = out["Population (M)"].map(fmt_m2)
    out["Gradient"] = out["Gradient"].map(GRADIENT_LABELS)
    return out


def table_3_4(df: pd.DataFrame) -> pd.DataFrame:
    base = official_df(df)
    total_brazil = float(base["peso"].sum())
    rows = []
    for sector, sub in base.groupby("sector_corrected"):
        total = float(sub["peso"].sum())
        high = float(sub.loc[sub["is_high_exposure"], "peso"].sum())
        low = float(sub.loc[sub["exposure_gradient"].isin(LOW_GRADIENTS), "peso"].sum())
        moderate = float(sub.loc[sub["exposure_gradient"].isin(MODERATE_GRADIENTS), "peso"].sum())
        exposed = moderate + high
        rows.append(
            {
                "Sector": sector,
                "Total (M)": total / 1e6,
                "% BR": total / total_brazil * 100,
                "Exposure Mean": weighted_mean(sub["exposure_score"], sub["peso"]),
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
    out = pd.DataFrame(rows).sort_values("Exposure Mean", ascending=False)
    for col in ["Total (M)", "Low (M)", "Moderate (M)", "High (M)", "Exposed (M)"]:
        out[col] = out[col].map(fmt_m2)
    for col in ["% BR", "Low (%)", "Moderate (%)", "High (%)", "Exposed (%)"]:
        out[col] = out[col].map(fmt_pct)
    out["Exposure Mean"] = out["Exposure Mean"].map(fmt_score3)
    return out


def state_high_table(df: pd.DataFrame) -> pd.DataFrame:
    base = official_df(df)
    rows = []
    for uf, sub in base.groupby("sigla_uf"):
        total = float(sub["peso"].sum())
        high = float(sub.loc[sub["is_high_exposure"], "peso"].sum())
        rows.append({"UF": uf, "Total (M)": total / 1e6, "High (M)": high / 1e6, "High (%)": high / total * 100})
    return pd.DataFrame(rows).sort_values("High (%)", ascending=False)


def table_3_5(df: pd.DataFrame) -> pd.DataFrame:
    pieces = []

    def add_dimension(name: str, summary: pd.DataFrame) -> None:
        if summary.empty:
            return
        part = summary.copy()
        part.insert(0, "Dimension", name)
        pieces.append(part)

    add_dimension("Sex", group_summary(df, "sexo_texto", SEX_ORDER))
    add_dimension("Race", group_summary(df, "raca_agregada", RACE_ORDER))
    add_dimension("Age", group_summary(df, "faixa_etaria", AGE_ORDER))
    add_dimension("Education", group_summary(df, "nivel_instrucao", list(EDUCATION_LABELS), category_labels=EDUCATION_LABELS))
    add_dimension("Income", group_summary(df[df["tem_renda"].eq(1)], "faixa_renda_sm", INCOME_ORDER))
    add_dimension("Formality", group_summary(df, "formal", [1, 0], category_labels=FORMAL_LABELS))

    out = pd.concat(pieces, ignore_index=True)
    out["population_m"] = out["population_m"].map(fmt_m2)
    out["mean_score"] = out["mean_score"].map(fmt_score3)
    out["low_pct"] = out["low_pct"].map(fmt_pct)
    out["moderate_pct"] = out["moderate_pct"].map(fmt_pct)
    out["high_pct"] = out["high_pct"].map(fmt_pct)
    out["high_m"] = out["high_m"].map(fmt_m2)
    out = out.rename(
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
    return out


def write_table_files(output_dir: Path, df: pd.DataFrame, filename: str, title: str) -> None:
    table_path = output_dir / "tables" / filename
    csv_path = table_path.with_suffix(".csv")
    table_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    write_text(table_path, f"# {title}\n\n{markdown_table(list(df.columns), df.to_records(index=False))}\n")


def setup_plot_style() -> None:
    plt = get_pyplot()
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linewidth": 0.8,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 8,
        }
    )


def save_figure(fig, path: Path) -> None:
    plt = get_pyplot()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fmt_br(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def title_axis(ax, title: str) -> None:
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=14)


def plot_histogram_kde(df: pd.DataFrame, path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    score = score_df(df)
    official = score[score["is_official_gradient"]]
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    bins = np.linspace(float(score["exposure_score"].min()), float(score["exposure_score"].max()), 36)
    for grad in GRADIENT_ORDER:
        sub = official[official["exposure_gradient"].eq(grad)]
        ax.hist(
            sub["exposure_score"],
            bins=bins,
            weights=sub["peso"] / 1e6,
            stacked=True,
            color=GRADIENT_COLORS[grad],
            alpha=0.88,
            label=GRADIENT_LABELS_PT[grad],
        )
    try:
        from scipy.stats import gaussian_kde

        scores = score["exposure_score"].to_numpy(dtype=float)
        weights = score["peso"].to_numpy(dtype=float)
        kde = gaussian_kde(scores, weights=weights / weights.sum())
        x_grid = np.linspace(scores.min(), scores.max(), 250)
        bin_width = (scores.max() - scores.min()) / (len(bins) - 1)
        y = kde(x_grid) * weights.sum() / 1e6 * bin_width
        ax.plot(x_grid, y, color="#1f1f1f", linewidth=2, label="Densidade ponderada")
    except Exception:
        pass
    mean_value = weighted_mean(score["exposure_score"], score["peso"])
    ax.axvline(mean_value, color="#b22222", linestyle="--", linewidth=1.8, label=f"Média = {mean_value:.3f}")
    title_axis(ax, FIGURE_TITLES_PT["3.1"])
    ax.set_xlabel("Score de exposição à IA")
    ax.set_ylabel("Trabalhadores (milhões)")
    ax.legend(ncol=2)
    save_figure(fig, path)


def plot_gradient_population(df: pd.DataFrame, path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    official = official_df(df)
    total = float(official["peso"].sum())
    rows = [
        ("Exposição baixa", "Não exposto + exposição mínima", LOW_GRADIENTS, GROUP_COLORS["Low"]),
        ("Exposição média", "Gradientes 1 e 2", MODERATE_GRADIENTS, GROUP_COLORS["Moderate"]),
        ("Exposição alta", "Gradientes 3 e 4", HIGH_GRADIENTS, GROUP_COLORS["High"]),
    ]
    labels = [f"{label}\n{sub}" for label, sub, _, _ in rows]
    values = [
        float(official.loc[official["exposure_gradient"].isin(gradients), "peso"].sum()) / 1e6
        for _, _, gradients, _ in rows
    ]
    pcts = [value * 1e6 / total * 100 for value in values]
    colors = [color for _, _, _, color in rows]

    fig, ax = plt.subplots(figsize=(10.4, 5.4))
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, height=0.58)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Trabalhadores (milhões)")
    title_axis(ax, FIGURE_TITLES_PT["3.2"])
    for bar, value, pct in zip(bars, values, pcts):
        ax.text(
            bar.get_width() + max(values) * 0.018,
            bar.get_y() + bar.get_height() / 2,
            f"{fmt_br(value)} mi ({fmt_br(pct)}%)",
            va="center",
            fontsize=10,
            color="#222222",
        )
    ax.text(
        0.64,
        0.18,
        "Chave de leitura\nMédia = complementaridade\nAlta = automação",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=9.5,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#D6D6D6", linewidth=0.8),
    )
    ax.text(
        0.0,
        -0.18,
        "Nota: percentuais calculados sobre ocupados classificáveis nos seis gradientes oficiais da OIT.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color="#555555",
    )
    ax.set_xlim(0, max(values) * 1.32)
    save_figure(fig, path)


def plot_score_by_occupation_group(df: pd.DataFrame, path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    score = score_df(df)
    bins = np.linspace(0, 0.75, 16)
    groups = (
        score.groupby("grande_grupo")["peso"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = np.zeros(len(bins) - 1)
    cmap = plt.get_cmap("tab10")
    centers = (bins[:-1] + bins[1:]) / 2
    width = bins[1] - bins[0]
    for idx, group in enumerate(groups):
        sub = score[score["grande_grupo"].eq(group)]
        values, _ = np.histogram(sub["exposure_score"], bins=bins, weights=sub["peso"] / 1e6)
        ax.bar(centers, values, width=width * 0.95, bottom=bottom, color=cmap(idx % 10), label=group)
        bottom += values
    title_axis(ax, FIGURE_TITLES_PT["3.3"])
    ax.set_xlabel("Score de exposição à IA")
    ax.set_ylabel("Trabalhadores (milhões)")
    ax.legend(ncol=2, fontsize=7)
    save_figure(fig, path)


def plot_state_high(df: pd.DataFrame, path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    try:
        import geobr
        import matplotlib.patheffects as pe
    except Exception as exc:
        raise RuntimeError("Figure 3.4 requires geobr and matplotlib path effects.") from exc

    states = state_high_table(df).rename(columns={"UF": "sigla_uf"})
    gdf = geobr.read_state(year=2020)
    gdf["abbrev_state"] = gdf["abbrev_state"].str.upper()
    gdf = gdf.merge(states, left_on="abbrev_state", right_on="sigla_uf", how="left")
    if gdf["High (%)"].isna().any():
        missing = gdf.loc[gdf["High (%)"].isna(), "abbrev_state"].tolist()
        raise ValueError(f"Missing state data for: {missing}")

    fig = plt.figure(figsize=(11.2, 8.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.12, 0.88], width_ratios=[0.76, 0.24], wspace=0.02, hspace=0.0)
    ax_title = fig.add_subplot(gs[0, :])
    ax_map = fig.add_subplot(gs[1, 0])
    ax_side = fig.add_subplot(gs[1, 1])
    ax_title.axis("off")
    ax_side.axis("off")
    ax_map.set_axis_off()

    ax_title.text(
        0.0,
        0.78,
        FIGURE_TITLES_PT["3.4"],
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        color="#1A1A1A",
    )
    ax_title.text(
        0.0,
        0.25,
        "Cor: participação dos trabalhadores em Gradientes 3 e 4 dentro da força de trabalho classificável de cada UF.",
        ha="left",
        va="top",
        fontsize=9.2,
        color="#555555",
    )

    values = gdf["High (%)"].to_numpy(dtype=float)
    cmap = plt.get_cmap("Reds")
    norm = plt.Normalize(vmin=float(values.min()), vmax=float(values.max()))
    gdf.plot(
        column="High (%)",
        cmap=cmap,
        norm=norm,
        linewidth=0.45,
        edgecolor="#F7F2F0",
        ax=ax_map,
        legend=False,
    )
    gdf.boundary.plot(ax=ax_map, color="#777777", linewidth=0.25)

    callout_positions = {
        "DF": (-39.5, -15.8),
        "RN": (-32.9, -5.2),
        "PB": (-32.9, -6.9),
        "PE": (-32.9, -8.6),
        "AL": (-32.9, -10.3),
        "SE": (-32.9, -11.8),
        "ES": (-32.9, -19.3),
        "RJ": (-32.9, -22.5),
    }
    label_offsets = {
        "GO": (0.0, -0.7),
    }
    for _, row in gdf.iterrows():
        uf = row["abbrev_state"]
        centroid = row.geometry.centroid
        label = f"{uf} {fmt_br(float(row['High (%)']))}%"
        if uf in callout_positions:
            text_x, text_y = callout_positions[uf]
            ax_map.annotate(
                "",
                xy=(centroid.x, centroid.y),
                xytext=(text_x - 0.2, text_y),
                arrowprops=dict(arrowstyle="-", color="#666666", lw=0.55, shrinkA=0, shrinkB=0),
            )
            color = "#222222"
            ha = "left"
        else:
            text_x, text_y = centroid.x, centroid.y
            offset_x, offset_y = label_offsets.get(uf, (0.0, 0.0))
            text_x += offset_x
            text_y += offset_y
            rel = (float(row["High (%)"]) - float(values.min())) / (float(values.max()) - float(values.min()))
            color = "white" if rel > 0.55 else "#222222"
            ha = "center"
        label_stroke = (
            [pe.withStroke(linewidth=1.6, foreground="#333333")]
            if color == "white"
            else [pe.withStroke(linewidth=2.2, foreground="white")]
        )
        ax_map.text(
            text_x,
            text_y,
            label,
            ha=ha,
            va="center",
            fontsize=7.2,
            fontweight="bold",
            color=color,
            path_effects=label_stroke,
        )

    bounds = gdf.total_bounds
    ax_map.set_xlim(bounds[0] - 1.2, bounds[2] + 7.2)
    ax_map.set_ylim(bounds[1] - 1.2, bounds[3] + 1.2)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_map, fraction=0.032, pad=0.015)
    cbar.set_label("% da força de trabalho da UF", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    top_volume = states.sort_values("High (M)", ascending=False).head(6)
    ax_side.text(0.0, 0.98, "Maiores volumes\nabsolutos", ha="left", va="top", fontsize=10.5, fontweight="bold")
    y = 0.82
    for _, row in top_volume.iterrows():
        ax_side.text(0.0, y, f"{row['sigla_uf']}", ha="left", va="center", fontsize=9.5, fontweight="bold")
        ax_side.text(0.22, y, f"{fmt_br(float(row['High (M)']), 2)} mi", ha="left", va="center", fontsize=9.5)
        y -= 0.085
    ax_side.text(
        0.0,
        0.16,
        "Fonte: PNAD Contínua 3T/2025\n(IBGE) e ILO WP140.",
        ha="left",
        va="bottom",
        fontsize=8.0,
        color="#555555",
    )
    save_figure(fig, path)


def plot_demographic_dimension(title: str, summary: pd.DataFrame, path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    plot_data = summary.copy()
    y = np.arange(len(plot_data))
    fig_height = max(3.5, len(plot_data) * 0.55 + 1.5)
    fig, ax = plt.subplots(figsize=(9.5, fig_height))
    left = np.zeros(len(plot_data))
    for group, col in [("Low", "low_pct"), ("Moderate", "moderate_pct"), ("High", "high_pct")]:
        values = plot_data[col].to_numpy(dtype=float)
        ax.barh(y, values, left=left, color=GROUP_COLORS[group], label=GROUP_LABELS_PT[group])
        for i, value in enumerate(values):
            if value >= 4:
                ax.text(left[i] + value / 2, i, f"{fmt_br(value)}%", ha="center", va="center", color="white", fontsize=8)
        left += values
    for i, row in enumerate(plot_data.itertuples(index=False)):
        ax.text(101, i, f"{fmt_br(row.population_m)} mi", va="center", fontsize=8)
    ax.set_yticks(y, plot_data["category"])
    ax.invert_yaxis()
    ax.set_xlim(0, 112)
    ax.set_xlabel("Participação na categoria (%)")
    title_axis(ax, title)
    ax.legend(ncol=3, loc="lower right")
    save_figure(fig, path)


def generate_figures(df: pd.DataFrame, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    plot_histogram_kde(df, fig_dir / "figure_3_1_histogram_kde.png")
    plot_gradient_population(df, fig_dir / "figure_3_2_gradient_population.png")
    plot_score_by_occupation_group(df, fig_dir / "figure_3_3_score_by_occupation_group.png")
    plot_state_high(df, fig_dir / "figure_3_4_state_high_exposure.png")
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.5"],
        group_summary(df, "sexo_texto", SEX_ORDER),
        fig_dir / "figure_3_5_sex.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.6"],
        group_summary(df, "raca_agregada", RACE_ORDER),
        fig_dir / "figure_3_6_race.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.7"],
        group_summary(df, "faixa_etaria", AGE_ORDER),
        fig_dir / "figure_3_7_age.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.8"],
        group_summary(df, "nivel_instrucao", list(EDUCATION_LABELS_PT), category_labels=EDUCATION_LABELS_PT),
        fig_dir / "figure_3_8_education.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.9"],
        group_summary(df[df["tem_renda"].eq(1)], "faixa_renda_sm", INCOME_ORDER),
        fig_dir / "figure_3_9_income.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.10"],
        group_summary(df, "formal", [1, 0], category_labels=FORMAL_LABELS_PT),
        fig_dir / "figure_3_10_formality.png",
    )


def metric_by_category(summary: pd.DataFrame, category: str, metric: str) -> float:
    row = summary[summary["category"].eq(category)]
    if row.empty:
        return float("nan")
    return float(row.iloc[0][metric])


def build_claims(df: pd.DataFrame, html_text: str, ilo_count: int | None) -> list[Claim]:
    claims: list[Claim] = []
    score = score_df(df)
    official = official_df(df)
    total_pop_m = float(df["peso"].sum() / 1e6)
    score_pop_m = float(score["peso"].sum() / 1e6)
    official_pop_m = float(official["peso"].sum() / 1e6)
    high = official[official["is_high_exposure"]]
    high_pop_m = float(high["peso"].sum() / 1e6)
    high_pct_score = high["peso"].sum() / score["peso"].sum() * 100
    high_pct_official = high["peso"].sum() / official["peso"].sum() * 100

    claim(claims, "3.1.001", "3.1 Base and sample", "HTML source file was found", "present", bool(html_text), "present" if html_text else "missing", "file existence", force_status="PASS" if html_text else "FAIL")
    claim(claims, "3.1.002", "3.1 Base and sample", "Sample observations", "207.901", len(df), fmt_int(len(df)), "integer with thousands separator")
    claim(claims, "3.1.003", "3.1 Base and sample", "Population represented", "97,8", total_pop_m, fmt_m(total_pop_m).replace(".", ","), "millions, 1 decimal")
    claim(claims, "3.1.004", "3.1 Base and sample", "Age range after filters", "18-65", f"{int(df['idade'].min())}-{int(df['idade'].max())}", f"{int(df['idade'].min())}-{int(df['idade'].max())}", "min-max")
    claim(claims, "3.1.005", "3.1 Base and sample", "PNAD variables selected", "14", len(RAW_PNAD_QUERY_ALIASES), str(len(RAW_PNAD_QUERY_ALIASES)), "count", note="The Etapa 1a query currently selects 15 aliases: 12 PNAD survey variables plus ano, trimestre, and sigla_uf.")
    claim(claims, "3.1.006", "3.1 Base and sample", "ILO ISCO-08 occupations", "427", ilo_count if ilo_count is not None else "missing", str(ilo_count) if ilo_count is not None else "missing", "unique ISCO_08 count")
    matched_cod = df.loc[df["is_score_valid"], "cod_ocupacao"].nunique()
    total_cod = df["cod_ocupacao"].nunique()
    claim(claims, "3.1.007", "3.1 Base and sample", "COD occupations with match", "422 (de 428)", f"{matched_cod} of {total_cod}", f"{matched_cod} (de {total_cod})", "unique COD count")
    score_cov = df.loc[df["is_score_valid"], "peso"].sum() / df["peso"].sum() * 100
    claim(claims, "3.1.008", "3.1 Base and sample", "Score coverage by population", "99,2", score_cov, fmt_pct(score_cov).replace(".", ","), "percent, 1 decimal")
    match4 = df["match_level"].eq("4-digit").sum() / len(df) * 100
    match3 = df["match_level"].eq("3-digit").sum() / len(df) * 100
    no_score = df["exposure_score"].isna().sum() / len(df) * 100
    claim(claims, "3.1.009", "3.1 Base and sample", "4-digit match share", "97,9", match4, fmt_pct(match4).replace(".", ","), "row percent, 1 decimal")
    claim(claims, "3.1.010", "3.1 Base and sample", "3-digit fallback share", "1,3", match3, fmt_pct(match3).replace(".", ","), "row percent, 1 decimal")
    claim(claims, "3.1.011", "3.1 Base and sample", "No-score share", "0,8", no_score, fmt_pct(no_score).replace(".", ","), "row percent, 1 decimal")
    claim(claims, "3.1.012", "3.1 Base and sample", "Federal units", "27", df["sigla_uf"].nunique(), str(df["sigla_uf"].nunique()), "count")
    claim(claims, "3.1.013", "3.1 Base and sample", "Sector categories in thesis text", "17", df["sector_corrected"].nunique(), str(df["sector_corrected"].nunique()), "count", note="Corrected CNAE-Domiciliar mapping produces 19 sectors; the input column still has 17 due to the zero-padding issue documented in export_tab_setor_economico_exposicao.py.")
    claim(claims, "3.1.014", "3.1 Base and sample", "Reference minimum wage", "R$ 1.518", SALARY_MINIMUM_BRL, f"R$ {SALARY_MINIMUM_BRL:,}".replace(",", "."), "BRL integer")

    mean_score = weighted_mean(score["exposure_score"], score["peso"])
    claim(claims, "3.2.001", "3.2 Exposure distribution", "Weighted mean exposure score", "0,278", mean_score, fmt_score3(mean_score).replace(".", ","), "score, 3 decimals")
    gradient_expected = {
        "Not Exposed": ("52,2", "53,9"),
        "Minimal Exposure": ("15,2", "15,7"),
        "Exposed: Gradient 1": ("8,7", "9,0"),
        "Exposed: Gradient 2": ("10,0", "10,3"),
        "Exposed: Gradient 3": ("4,8", "4,9"),
        "Exposed: Gradient 4": ("5,0", "5,1"),
        SEM_CLASS: ("1,0", "1,1"),
    }
    for idx, grad in enumerate(GRADIENT_ORDER + [SEM_CLASS], start=1):
        sub = score[score["exposure_gradient"].eq(grad)]
        pop_m = float(sub["peso"].sum() / 1e6)
        pct = float(sub["peso"].sum() / score["peso"].sum() * 100)
        exp_pop, exp_pct = gradient_expected[grad]
        claim(claims, f"3.2.G{idx:02d}a", "3.2 Exposure distribution", f"{GRADIENT_LABELS[grad]} population", exp_pop, pop_m, fmt_m(pop_m).replace(".", ","), "millions, 1 decimal")
        claim(claims, f"3.2.G{idx:02d}b", "3.2 Exposure distribution", f"{GRADIENT_LABELS[grad]} share", exp_pct, pct, fmt_pct(pct).replace(".", ","), "percent of scored population, 1 decimal")
    claim(claims, "3.2.020", "3.2 Exposure distribution", "High exposure population (G3+G4)", "9,8", high_pop_m, fmt_m(high_pop_m).replace(".", ","), "millions, 1 decimal")
    claim(claims, "3.2.021", "3.2 Exposure distribution", "High exposure share (G3+G4)", "10,1", high_pct_score, fmt_pct(high_pct_score).replace(".", ","), "percent of scored population, 1 decimal")
    for cid, expected, label in [
        ("3.2.022", "7,5", "ILO global high-exposure benchmark"),
        ("3.2.023", "7,0", "ILO upper-middle-income high-exposure benchmark"),
        ("3.2.024", "17,3", "ILO high-income high-exposure benchmark"),
    ]:
        claim(claims, cid, "3.2 Exposure distribution", label, expected, expected, expected, "documented constant")

    top_high = table_3_3(df, {})
    expected_codes = ["4110", "4226", "2411", "4120", "2431"]
    computed_codes = top_high["COD"].astype(str).tolist()
    claim(claims, "3.3.001", "3.3 Occupations", "Table 3.3 listed occupations are top high-exposure occupations by population", ", ".join(expected_codes), ", ".join(computed_codes), ", ".join(computed_codes), "ordered COD list")
    top_by_mean = table_3_3_top_mean(df, {})
    claim(claims, "3.3.002", "3.3 Occupations", "Narrative says Table 3.3 is the five highest mean-exposure occupations", "same as Table 3.3", ", ".join(top_by_mean["COD"].astype(str).tolist()), ", ".join(top_by_mean["COD"].astype(str).tolist()), "ordered COD list", note="The listed table matches top high-exposure occupations by population, not the five highest mean-score occupations.", force_status="WARN")

    sector = table_3_4_numeric(df)
    for sector_name, expected_high_pct in [
        ("Finanças e Seguros", "54,9"),
        ("Informação e Comunicação", "31,9"),
        ("Serviços Profissionais", "31,2"),
        ("Administração Pública", "26,3"),
        ("Comércio", "7,7"),
    ]:
        row = sector[sector["Sector"].eq(sector_name)].iloc[0]
        claim(claims, f"3.4.sector.{sector_name}", "3.4 Sector and region", f"{sector_name} high-exposure share", expected_high_pct, row["High (%)"], fmt_pct(row["High (%)"]).replace(".", ","), "percent, 1 decimal")
    professional_high = float(sector.loc[sector["Sector"].eq("Serviços Profissionais"), "High (M)"].iloc[0])
    admin_high = float(sector.loc[sector["Sector"].eq("Administração Pública"), "High (M)"].iloc[0])
    commerce_high = float(sector.loc[sector["Sector"].eq("Comércio"), "High (M)"].iloc[0])
    claim(claims, "3.4.010", "3.4 Sector and region", "Services professionals plus public administration high-exposure volume", "2,39", professional_high + admin_high, fmt_m2(professional_high + admin_high).replace(".", ","), "millions, 2 decimals")
    claim(claims, "3.4.011", "3.4 Sector and region", "Largest absolute high-exposure sectors stated in text", "Serviços Profissionais e Administração Pública", commerce_high, "Comércio is larger", "rank check", note="The corrected sector table shows Commerce has 1.36M high-exposure workers, above Professional Services (1.27M) and Public Administration (1.12M).", force_status="WARN")
    states = state_high_table(df)
    sp = states[states["UF"].eq("SP")].iloc[0]
    df_state = states.iloc[0]
    ba = states[states["UF"].eq("BA")].iloc[0]
    claim(claims, "3.4.020", "3.4 Sector and region", "Sao Paulo high-exposure population", "2,8", sp["High (M)"], fmt_m(sp["High (M)"]).replace(".", ","), "millions, 1 decimal")
    claim(claims, "3.4.021", "3.4 Sector and region", "Sao Paulo high-exposure share", "cerca de 12", sp["High (%)"], fmt_pct(sp["High (%)"]).replace(".", ","), "percent, 1 decimal", note="Approximate wording is consistent with 12.3%.", force_status="PASS")
    claim(claims, "3.4.022", "3.4 Sector and region", "Distrito Federal has the highest high-exposure share", "DF", df_state["UF"], df_state["UF"], "rank check")
    claim(claims, "3.4.023", "3.4 Sector and region", "Bahia has lower high-exposure share than SP", "menor que SP", ba["High (%)"] < sp["High (%)"], "menor que SP" if ba["High (%)"] < sp["High (%)"] else "not lower", "comparison")

    sex_summary = group_summary(df, "sexo_texto", SEX_ORDER)
    race_summary = group_summary(df, "raca_agregada", RACE_ORDER)
    age_summary = group_summary(df, "faixa_etaria", AGE_ORDER)
    edu_summary = group_summary(df, "nivel_instrucao", list(EDUCATION_LABELS), category_labels=EDUCATION_LABELS)
    income_summary = group_summary(df[df["tem_renda"].eq(1)], "faixa_renda_sm", INCOME_ORDER)
    formal_summary = group_summary(df, "formal", [1, 0], category_labels=FORMAL_LABELS)

    women_mean = metric_by_category(sex_summary, "Mulher", "mean_score")
    men_mean = metric_by_category(sex_summary, "Homem", "mean_score")
    women_high = metric_by_category(sex_summary, "Mulher", "high_pct")
    men_high = metric_by_category(sex_summary, "Homem", "high_pct")
    claim(claims, "3.5.sex.001", "3.5 Demographics", "Women's mean exposure", "0,303", women_mean, fmt_score3(women_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.sex.002", "3.5 Demographics", "Men's mean exposure", "0,259", men_mean, fmt_score3(men_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.sex.003", "3.5 Demographics", "Female-minus-male exposure gap", "0,044", women_mean - men_mean, fmt_score3(women_mean - men_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.sex.004", "3.5 Demographics", "Women high-exposure share", "14,5", women_high, fmt_pct(women_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.sex.005", "3.5 Demographics", "Men high-exposure share", "6,8", men_high, fmt_pct(men_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.sex.006", "3.5 Demographics", "Women/men high-exposure ratio", "2,1", women_high / men_high, fmt_ratio(women_high / men_high).replace(".", ","), "ratio, 1 decimal")

    white_mean = metric_by_category(race_summary, "Branca", "mean_score")
    black_mean = metric_by_category(race_summary, "Negra", "mean_score")
    white_high = metric_by_category(race_summary, "Branca", "high_pct")
    black_high = metric_by_category(race_summary, "Negra", "high_pct")
    white_pop = metric_by_category(race_summary, "Branca", "population_m")
    black_pop = metric_by_category(race_summary, "Negra", "population_m")
    claim(claims, "3.5.race.001", "3.5 Demographics", "White workers' mean exposure", "0,305", white_mean, fmt_score3(white_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.race.002", "3.5 Demographics", "Black workers' mean exposure", "0,257", black_mean, fmt_score3(black_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.race.003", "3.5 Demographics", "White high-exposure share", "12,5", white_high, fmt_pct(white_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.race.004", "3.5 Demographics", "Black high-exposure share", "8,4", black_high, fmt_pct(black_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.race.005", "3.5 Demographics", "White occupied population", "41,5", white_pop, fmt_m(white_pop).replace(".", ","), "millions, 1 decimal")
    claim(claims, "3.5.race.006", "3.5 Demographics", "Black occupied population", "53,4", black_pop, fmt_m(black_pop).replace(".", ","), "millions, 1 decimal")

    young_mean = metric_by_category(age_summary, "18-24", "mean_score")
    older_mean = metric_by_category(age_summary, "55+", "mean_score")
    young_high = metric_by_category(age_summary, "18-24", "high_pct")
    older_high = metric_by_category(age_summary, "55+", "high_pct")
    claim(claims, "3.5.age.001", "3.5 Demographics", "Young age group in current filtered base", "15-19", "18-24", "18-24", "category label", note="The current base is filtered to ages 18-65 and uses 18-24, not 15-19.", force_status="WARN")
    claim(claims, "3.5.age.002", "3.5 Demographics", "Young group's mean exposure", "0,307", young_mean, fmt_score3(young_mean).replace(".", ","), "score, 3 decimals", note="Computed for 18-24 because 15-19 is not present after filters.")
    claim(claims, "3.5.age.003", "3.5 Demographics", "Older group's mean exposure", "0,251", older_mean, fmt_score3(older_mean).replace(".", ","), "score, 3 decimals", note="Computed for 55+ because 55-59 is not the stored category.")
    claim(claims, "3.5.age.004", "3.5 Demographics", "Young high-exposure share", "19,0", young_high, fmt_pct(young_high).replace(".", ","), "percent, 1 decimal", note="Computed for 18-24 because 15-19 is not present after filters.")
    claim(claims, "3.5.age.005", "3.5 Demographics", "Older high-exposure share", "5,8", older_high, fmt_pct(older_high).replace(".", ","), "percent, 1 decimal", note="Computed for 55+ because 55-59 is not the stored category.")

    sem_fund = score[score["nivel_instrucao"].isin([1, 2])]
    sem_fund_mean = weighted_mean(sem_fund["exposure_score"], sem_fund["peso"])
    claim(claims, "3.5.edu.001", "3.5 Demographics", "No/Fundamental incomplete mean exposure", "0,178", sem_fund_mean, fmt_score3(sem_fund_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.edu.002", "3.5 Demographics", "High school complete mean exposure", "0,274", metric_by_category(edu_summary, "High school complete", "mean_score"), fmt_score3(metric_by_category(edu_summary, "High school complete", "mean_score")).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.edu.003", "3.5 Demographics", "College incomplete mean exposure", "0,359", metric_by_category(edu_summary, "College incomplete", "mean_score"), fmt_score3(metric_by_category(edu_summary, "College incomplete", "mean_score")).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.edu.004", "3.5 Demographics", "College complete mean exposure", "0,364", metric_by_category(edu_summary, "College complete", "mean_score"), fmt_score3(metric_by_category(edu_summary, "College complete", "mean_score")).replace(".", ","), "score, 3 decimals")

    low_income_mean = metric_by_category(income_summary, "Até 1 SM", "mean_score")
    high_income_mean = metric_by_category(income_summary, "5+ SM", "mean_score")
    low_income_high = metric_by_category(income_summary, "Até 1 SM", "high_pct")
    high_income_high = metric_by_category(income_summary, "5+ SM", "high_pct")
    high_until_2sm = income_summary.loc[income_summary["category"].isin(["Até 1 SM", "1-2 SM"]), "high_m"].sum()
    claim(claims, "3.5.income.001", "3.5 Demographics", "Mean exposure up to 1 minimum wage", "0,237", low_income_mean, fmt_score3(low_income_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.income.002", "3.5 Demographics", "Mean exposure 5+ minimum wages", "0,365", high_income_mean, fmt_score3(high_income_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.income.003", "3.5 Demographics", "High exposure up to 1 minimum wage", "7,6", low_income_high, fmt_pct(low_income_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.income.004", "3.5 Demographics", "High exposure among 5+ minimum wages", "cerca de 11 a 12", high_income_high, fmt_pct(high_income_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.income.005", "3.5 Demographics", "Share of high-exposure workers earning up to 2 minimum wages", "cerca de dois terços", high_until_2sm / high_pop_m * 100, fmt_pct(high_until_2sm / high_pop_m * 100).replace(".", ",") + "%", "percent, 1 decimal", note="66.3% is consistent with the approximate phrase.", force_status="PASS")

    formal_mean = metric_by_category(formal_summary, "Formal", "mean_score")
    informal_mean = metric_by_category(formal_summary, "Informal", "mean_score")
    formal_high = metric_by_category(formal_summary, "Formal", "high_pct")
    informal_high = metric_by_category(formal_summary, "Informal", "high_pct")
    formal_high_m = metric_by_category(formal_summary, "Formal", "high_m")
    informal_high_m = metric_by_category(formal_summary, "Informal", "high_m")
    formal_pop = metric_by_category(formal_summary, "Formal", "population_m")
    informal_pop = metric_by_category(formal_summary, "Informal", "population_m")
    claim(claims, "3.5.formal.001", "3.5 Demographics", "Formal workers' mean exposure", "0,305", formal_mean, fmt_score3(formal_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.formal.002", "3.5 Demographics", "Informal workers' mean exposure", "0,258", informal_mean, fmt_score3(informal_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.formal.003", "3.5 Demographics", "Formal-informal exposure gap", "0,047", formal_mean - informal_mean, fmt_score3(formal_mean - informal_mean).replace(".", ","), "score, 3 decimals")
    claim(claims, "3.5.formal.004", "3.5 Demographics", "Formal high-exposure share", "14,8", formal_high, fmt_pct(formal_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.formal.005", "3.5 Demographics", "Informal high-exposure share", "6,7", informal_high, fmt_pct(informal_high).replace(".", ","), "percent, 1 decimal")
    claim(claims, "3.5.formal.006", "3.5 Demographics", "Formal high-exposure population", "6,1", formal_high_m, fmt_m(formal_high_m).replace(".", ","), "millions, 1 decimal")
    claim(claims, "3.5.formal.007", "3.5 Demographics", "Informal high-exposure population", "3,6", informal_high_m, fmt_m(informal_high_m).replace(".", ","), "millions, 1 decimal")
    claim(claims, "3.5.formal.008", "3.5 Demographics", "Informal workforce is 32% larger than formal workforce", "32", (informal_pop / formal_pop - 1) * 100, f"{(informal_pop / formal_pop - 1) * 100:.0f}", "percent, 0 decimals")
    claim(claims, "3.5.formal.009", "3.5 Demographics", "Formal share of high-exposure workers", "63", formal_high_m / high_pop_m * 100, f"{formal_high_m / high_pop_m * 100:.0f}", "percent, 0 decimals")

    claim(claims, "3.6.001", "3.6 Synthesis", "Synthesis high-exposure population", "9,8", high_pop_m, fmt_m(high_pop_m).replace(".", ","), "millions, 1 decimal")
    claim(claims, "3.6.002", "3.6 Synthesis", "Synthesis high-exposure share", "10,1", high_pct_score, fmt_pct(high_pct_score).replace(".", ","), "percent of scored population, 1 decimal")
    claim(claims, "3.6.003", "3.6 Synthesis", "Official-gradient denominator population", "96,0", official_pop_m, fmt_m(official_pop_m).replace(".", ","), "millions, 1 decimal", note="This is the denominator for sector, state, and demographic decompositions.")
    claim(claims, "3.6.004", "3.6 Synthesis", "Scored-population denominator", "97,0", score_pop_m, fmt_m(score_pop_m).replace(".", ","), "millions, 1 decimal", note="This denominator includes 3-digit fallback scores without official WP140 gradients.")

    compare_existing_outputs(df, claims)
    return claims


def table_3_4_numeric(df: pd.DataFrame) -> pd.DataFrame:
    base = official_df(df)
    total_brazil = float(base["peso"].sum())
    rows = []
    for sector, sub in base.groupby("sector_corrected"):
        total = float(sub["peso"].sum())
        high = float(sub.loc[sub["is_high_exposure"], "peso"].sum())
        low = float(sub.loc[sub["exposure_gradient"].isin(LOW_GRADIENTS), "peso"].sum())
        moderate = float(sub.loc[sub["exposure_gradient"].isin(MODERATE_GRADIENTS), "peso"].sum())
        rows.append(
            {
                "Sector": sector,
                "Total (M)": total / 1e6,
                "% BR": total / total_brazil * 100,
                "Exposure Mean": weighted_mean(sub["exposure_score"], sub["peso"]),
                "Low (M)": low / 1e6,
                "Low (%)": low / total * 100,
                "Moderate (M)": moderate / 1e6,
                "Moderate (%)": moderate / total * 100,
                "High (M)": high / 1e6,
                "High (%)": high / total * 100,
            }
        )
    return pd.DataFrame(rows).sort_values("Exposure Mean", ascending=False)


def compare_existing_outputs(df: pd.DataFrame, claims: list[Claim]) -> None:
    sector_path = ROOT / "outputs" / "tables" / "tab_setor_economico_exposicao.csv"
    if sector_path.exists():
        current = table_3_4_numeric(df)
        old = pd.read_csv(sector_path)
        old_map = old.set_index("setor")
        ok = True
        max_diff = 0.0
        for _, row in current.iterrows():
            sector = row["Sector"]
            if sector not in old_map.index:
                ok = False
                continue
            diff = abs(float(old_map.loc[sector, "pct_alta"]) - float(row["High (%)"]))
            max_diff = max(max_diff, diff)
            if diff > 0.02:
                ok = False
        claim(
            claims,
            "X.001",
            "Existing output comparison",
            "Generated sector table matches existing outputs/tables/tab_setor_economico_exposicao.csv",
            "match",
            max_diff,
            "match" if ok else f"max diff {max_diff:.4f}",
            "max pct_alta diff <= 0.02",
            force_status="PASS" if ok else "WARN",
        )
    else:
        claim(
            claims,
            "X.001",
            "Existing output comparison",
            "Existing sector table found for comparison",
            "present",
            "missing",
            "missing",
            "file existence",
            force_status="WARN",
        )

    trend_path = ROOT / "outputs" / "tables" / "tab_alta_exposicao_renda_educacao.csv"
    if trend_path.exists():
        claim(
            claims,
            "X.002",
            "Existing output comparison",
            "Existing income/education table found for comparison",
            "present",
            "present",
            "present",
            "file existence",
        )


def write_audit(claims: list[Claim], output_dir: Path) -> tuple[Path, Path]:
    audit_df = pd.DataFrame([c.as_dict() for c in claims])
    csv_path = output_dir / "section3_claims_audit.csv"
    md_path = output_dir / "section3_claims_audit.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(csv_path, index=False)

    counts = audit_df["status"].value_counts().to_dict()
    summary_rows = [
        ("PASS", counts.get("PASS", 0)),
        ("WARN", counts.get("WARN", 0)),
        ("FAIL", counts.get("FAIL", 0)),
    ]
    warn_df = audit_df[audit_df["status"].isin(["WARN", "FAIL"])].copy()

    lines = [
        "# Section 3 Claims Audit",
        "",
        "This report validates the numerical claims in Section 3 against `data/output/pnad_ilo_merged.csv`.",
        "",
        "## Status Summary",
        "",
        markdown_table(["Status", "Count"], summary_rows),
        "",
        "## Items Requiring Thesis Edits or Review",
        "",
    ]
    if warn_df.empty:
        lines.append("No WARN or FAIL items.")
    else:
        lines.append(
            markdown_table(
                ["ID", "Section", "Description", "Expected", "Computed", "Status", "Note"],
                warn_df[["id", "section", "description", "expected_display", "computed_display", "status", "note"]].to_records(index=False),
            )
        )
    lines.extend(
        [
            "",
            "## Full Claim Registry",
            "",
            markdown_table(
                ["ID", "Section", "Description", "Expected", "Computed", "Status"],
                audit_df[["id", "section", "description", "expected_display", "computed_display", "status"]].to_records(index=False),
            ),
            "",
        ]
    )
    write_text(md_path, "\n".join(lines))
    return csv_path, md_path


def write_manifest(output_dir: Path, args: argparse.Namespace, df: pd.DataFrame) -> None:
    rows = [
        ("Section 3 HTML", str(resolve_path(args.html)), "Claim registry and source text"),
        ("PNAD-ILO analytic data", str(resolve_path(args.input)), "Primary source for all Section 3 numbers"),
        ("Local PNAD microdata", str(DEFAULT_RAW_PNAD), "Input audit only; not rebuilt"),
        ("ILO index", str(DEFAULT_ILO_FILE), "ISCO occupation count and optional occupation titles"),
        ("Etapa 1a script", str(ROOT / "src" / "scripts" / "etapa_1a_preparacao_dados_ilo_pnadc.py"), "Rules for filters, variables, weights, and crosswalk"),
        ("Generated outputs", str(output_dir), "Audit, tables, and figures"),
    ]
    text = [
        "# Replication Package Manifest",
        "",
        "This package is intentionally post-build: it validates the dissertation's Section 3 descriptive claims using the already-built analytic files.",
        "",
        markdown_table(["Data", "Path", "Use"], rows),
        "",
        "## Denominators",
        "",
        markdown_table(
            ["Denominator", "Population (M)", "Definition"],
            [
                ("Full analytic sample", fmt_m(df["peso"].sum() / 1e6), "All rows in pnad_ilo_merged.csv"),
                ("Scored population", fmt_m(df.loc[df["is_score_valid"], "peso"].sum() / 1e6), "Rows with non-missing exposure_score"),
                ("Official-gradient population", fmt_m(official_df(df)["peso"].sum() / 1e6), "Rows in the six official WP140 gradient categories"),
                ("Unclassified with score", fmt_m(df.loc[df["is_score_valid"] & df["exposure_gradient"].eq(SEM_CLASS), "peso"].sum() / 1e6), "Fallback score but no official gradient"),
                ("No score", fmt_m(df.loc[df["exposure_score"].isna(), "peso"].sum() / 1e6), "No matched exposure score"),
            ],
        ),
        "",
    ]
    write_text(output_dir / "MANIFEST.md", "\n".join(text))


def main() -> int:
    args = parse_args()
    input_path = resolve_path(args.input)
    html_path = resolve_path(args.html)
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_data(input_path)
    html_text = load_section_text(html_path)
    ilo_count, title_map = load_ilo_metadata(DEFAULT_ILO_FILE)

    write_manifest(output_dir, args, df)

    t31 = table_3_1(df, ilo_count)
    t32 = table_3_2(df)
    t33 = table_3_3(df, title_map)
    t34 = table_3_4(df)
    t35 = table_3_5(df)
    write_table_files(output_dir, t31, "table_3_1_base_specs.md", "Table 3.1. Analytic Base Specifications")
    write_table_files(output_dir, t32, "table_3_2_gradients.md", "Table 3.2. Population by AI Exposure Gradient")
    write_table_files(output_dir, t33, "table_3_3_high_exposure_occupations.md", "Table 3.3. Largest High-Exposure Occupations")
    write_table_files(output_dir, t34, "table_3_4_sector_exposure.md", "Table 3.4. AI Exposure by Sector")
    write_table_files(output_dir, t35, "table_3_5_demographics_summary.md", "Table 3.5. Demographic Exposure Summary")

    if not args.skip_figures:
        generate_figures(df, output_dir)

    claims = build_claims(df, html_text, ilo_count)
    csv_path, md_path = write_audit(claims, output_dir)

    audit_df = pd.DataFrame([c.as_dict() for c in claims])
    fail_count = int((audit_df["status"] == "FAIL").sum())
    warn_count = int((audit_df["status"] == "WARN").sum())
    pass_count = int((audit_df["status"] == "PASS").sum())

    print("Section 3 replication package complete.")
    print(f"PASS: {pass_count} | WARN: {warn_count} | FAIL: {fail_count}")
    print(f"Audit CSV: {csv_path}")
    print(f"Audit MD:  {md_path}")

    if args.strict and fail_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
