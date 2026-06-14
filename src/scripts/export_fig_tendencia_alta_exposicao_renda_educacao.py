"""
Exporta figura 1x2: % da populacao ocupada em ALTA exposicao (ILO G3+G4)
por faixa de renda (salarios minimos) e por escolaridade simplificada.

Definicao de alta exposicao (igual etapa_1b_analise_dados_ilo_pnadc.py):
  exposure_gradient in ['Exposed: Gradient 3', 'Exposed: Gradient 4']

Dados: data/output/pnad_ilo_merged.csv (PNADc + ILO WP140, peso V1028).
Percentuais ponderados por `peso` entre quem tem exposure_score.
Painel renda: apenas tem_renda==1 e faixa_renda_sm valida.

Nota: tendencia ao longo de faixas de renda/educacao reflete composicao
ocupacional e selecao amostral; nao implica causalidade.

Saidas:
  - outputs/figures/etapa_1b/fig_tendencia_alta_exposicao_renda_escolaridade.png
  - outputs/tables/tab_alta_exposicao_renda_educacao.csv

Uso:
  python src/scripts/export_fig_tendencia_alta_exposicao_renda_educacao.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from dissertation_plot_theme import (
    CORES,
    apply_publication_style,
    layout_figure_no_header,
    save_publication_figure,
    style_axes_clean,
)

# Igual src/scripts/etapa_1b_analise_dados_ilo_pnadc.py
HIGH_EXPOSURE_GRADIENTS = ["Exposed: Gradient 3", "Exposed: Gradient 4"]

ROOT = Path(__file__).parent.parent.parent
DATA_OUTPUT = ROOT / "data" / "output"
DATA_FIGURES = ROOT / "outputs" / "figures" / "etapa_1b"
DATA_TABLES = ROOT / "outputs" / "tables"

FAIXA_RENDA_ORDER = ["Até 1 SM", "1-2 SM", "2-3 SM", "3-5 SM", "5+ SM"]

EDU_ORDER = [
    "Sem/Fund.Inc.",
    "Fund.Comp.",
    "Med.Inc.",
    "Med.Comp.",
    "Sup.Inc.",
    "Sup.Comp.",
    "Outros",
]


def _prepare_df() -> pd.DataFrame:
    df = pd.read_csv(DATA_OUTPUT / "pnad_ilo_merged.csv")
    df["cod_ocupacao"] = df["cod_ocupacao"].astype(str).str.zfill(4)
    df = df[df["exposure_score"].notna()].copy()
    edu_map = {
        "1": "Sem/Fund.Inc.",
        "2": "Sem/Fund.Inc.",
        "3": "Fund.Comp.",
        "4": "Med.Inc.",
        "5": "Med.Comp.",
        "6": "Sup.Inc.",
        "7": "Sup.Comp.",
    }
    col_edu = "nivel_instrucao" if "nivel_instrucao" in df.columns else "vd3004"
    df["edu_simples"] = df[col_edu].astype(str).map(edu_map).fillna("Outros")
    return df


def _agg_pct_alta(sub: pd.DataFrame) -> tuple[float, float]:
    if len(sub) == 0 or sub["peso"].sum() <= 0:
        return float("nan"), 0.0
    tw = sub["peso"].sum()
    alta = sub.loc[sub["exposure_gradient"].isin(HIGH_EXPOSURE_GRADIENTS), "peso"].sum()
    return 100.0 * alta / tw, tw / 1e6


def _build_series_renda(
    df: pd.DataFrame,
) -> tuple[list[str], list[float], list[dict]]:
    d = df[(df["tem_renda"] == 1) & df["faixa_renda_sm"].notna()].copy()
    rows_csv: list[dict] = []
    cats: list[str] = []
    pcts: list[float] = []
    pops: list[float] = []
    for faixa in FAIXA_RENDA_ORDER:
        sub = d[d["faixa_renda_sm"] == faixa]
        pct, pop = _agg_pct_alta(sub)
        if np.isnan(pct):
            continue
        cats.append(faixa)
        pcts.append(pct)
        pops.append(pop)
        rows_csv.append(
            {"grupo": "renda_sm", "categoria": faixa, "pct_alta": pct, "pop_milhoes": pop}
        )
    return cats, pcts, rows_csv


def _build_series_edu(df: pd.DataFrame) -> tuple[list[str], list[float], list[dict]]:
    rows_csv: list[dict] = []
    cats: list[str] = []
    pcts: list[float] = []
    pops: list[float] = []
    for edu in EDU_ORDER:
        sub = df[df["edu_simples"] == edu]
        if len(sub) < 1:
            continue
        pct, pop = _agg_pct_alta(sub)
        if np.isnan(pct):
            continue
        cats.append(edu)
        pcts.append(pct)
        pops.append(pop)
        rows_csv.append(
            {"grupo": "escolaridade", "categoria": edu, "pct_alta": pct, "pop_milhoes": pop}
        )
    return cats, pcts, rows_csv


def main() -> None:
    csv_in = DATA_OUTPUT / "pnad_ilo_merged.csv"
    if not csv_in.exists():
        raise FileNotFoundError(csv_in)

    df = _prepare_df()
    cats_r, pct_r, rows_r = _build_series_renda(df)
    cats_e, pct_e, rows_e = _build_series_edu(df)

    DATA_TABLES.mkdir(parents=True, exist_ok=True)
    tab = pd.DataFrame(rows_r + rows_e)
    out_csv = DATA_TABLES / "tab_alta_exposicao_renda_educacao.csv"
    tab.to_csv(out_csv, index=False)

    sns.set_theme(style="ticks")
    apply_publication_style()
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2))

    def _panel(ax, cats, pcts, xlabel: str, title: str) -> None:
        x = np.arange(len(cats))
        ax.plot(
            x,
            pcts,
            "o-",
            color=CORES["azul"],
            linewidth=2.2,
            markersize=8,
            markerfacecolor=CORES["azul_claro"],
            markeredgecolor=CORES["azul"],
            markeredgewidth=1.2,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(cats, rotation=35, ha="right")
        ax.set_ylabel("% em alta exposicao (G3+G4)")
        ax.set_xlabel(xlabel)
        ax.set_title(title)
        ax.set_ylim(0, max(pcts) * 1.15 if pcts else 1)
        style_axes_clean(ax, grid_axis="y")
        for xi, yi in zip(x, pcts):
            ax.annotate(
                f"{yi:.1f}%",
                xy=(xi, yi),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color="#333333",
            )

    _panel(
        axes[0],
        cats_r,
        pct_r,
        "Faixa de rendimento (habitual, SM)",
        "Alta exposicao por faixa de renda",
    )
    _panel(
        axes[1],
        cats_e,
        pct_e,
        "Nivel de instrucao (agregado)",
        "Alta exposicao por escolaridade",
    )

    layout_figure_no_header(fig, left=0.08, right=0.98, top=0.92, bottom=0.22)
    DATA_FIGURES.mkdir(parents=True, exist_ok=True)
    out_png = DATA_FIGURES / "fig_tendencia_alta_exposicao_renda_escolaridade.png"
    save_publication_figure(fig, out_png, bbox_inches=None)

    print(f"Salvo: {out_png}")
    print(f"Salvo: {out_csv}")


if __name__ == "__main__":
    main()
