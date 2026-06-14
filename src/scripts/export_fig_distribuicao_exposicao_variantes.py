"""
Exporta variantes visuais da Figura 3.1 — uma figura PNG por variante.

Figura 1 (score contínuo):
  - ECDF ponderada + percentis e média
  - Histograma empilhado por grande grupo ocupacional
  - KDE + faixas de quartis ponderados (P10–P90)

Figura 2 (gradientes ILO):
  - Waffle 10×10 (1 célula ≈ 1% da população)
  - Lollipop horizontal + destaque G3+G4
  - Barra horizontal 100% empilhada

Entrada: data/output/pnad_ilo_merged.csv
Saída:  outputs/figures/etapa_1b/fig_01_var_*.png, fig_02_var_*.png

Uso:
  python src/scripts/export_fig_distribuicao_exposicao_variantes.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import ticker
from scipy.stats import gaussian_kde

from dissertation_plot_theme import (
    FIG01_TOP_FIGSIZE_INCHES,
    FIG01_TOP_LAYOUT,
    apply_publication_style,
    layout_figure_no_header,
    palette_blue2red_n_categories,
    save_publication_figure,
    style_axes_clean,
)

ROOT = Path(__file__).parent.parent.parent
DATA_OUTPUT = ROOT / "data" / "output"
DATA_FIGURES = ROOT / "outputs" / "figures" / "etapa_1b"
DATA_FIGURES.mkdir(parents=True, exist_ok=True)

GRADIENT_ORDER = [
    "Not Exposed",
    "Minimal Exposure",
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
]

GRADIENT_COLORS = {
    "Not Exposed": "#2ca02c",
    "Minimal Exposure": "#98df8a",
    "Exposed: Gradient 1": "#aec7e8",
    "Exposed: Gradient 2": "#ffbb78",
    "Exposed: Gradient 3": "#ff7f0e",
    "Exposed: Gradient 4": "#d62728",
    "Sem classificacao": "#d9d9d9",
}

GRADIENT_LABELS_PT = {
    "Not Exposed": "Nao Exposto",
    "Minimal Exposure": "Exposicao Minima",
    "Exposed: Gradient 1": "Gradiente 1",
    "Exposed: Gradient 2": "Gradiente 2",
    "Exposed: Gradient 3": "Gradiente 3",
    "Exposed: Gradient 4": "Gradiente 4",
}

HIGH_G = ["Exposed: Gradient 3", "Exposed: Gradient 4"]


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return float("nan")
    return float(np.average(values[mask].values, weights=weights[mask].values))


def weighted_quantile(values: pd.Series, weights: pd.Series, q: float) -> float:
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return float("nan")
    v = values[mask].values
    w = weights[mask].values
    order = np.argsort(v)
    v = v[order]
    w = w[order]
    cw = np.cumsum(w)
    target = q * cw[-1]
    idx = int(np.searchsorted(cw, target, side="left"))
    idx = min(idx, len(v) - 1)
    return float(v[idx])


def _style():
    sns.set_style("whitegrid")
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
        }
    )


def plot_ecdf_percentis(df_score: pd.DataFrame, path: Path, dpi: int = 150) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(8, 5))
    v = df_score["exposure_score"].values
    w = df_score["peso"].values
    mask = ~(np.isnan(v) | np.isnan(w))
    v, w = v[mask], w[mask]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cum = np.cumsum(w) / np.sum(w)
    ax.step(v, cum * 100, where="post", color="#1f77b4", linewidth=2, label="ECDF (ponderada)")
    ax.set_xlabel("Score de exposicao")
    ax.set_ylabel("Populacao acumulada (%)")
    ax.set_title("Distribuicao acumulada do score (ECDF ponderada)")

    media = weighted_mean(df_score["exposure_score"], df_score["peso"])
    for q, lab, sty in [
        (0.10, "P10", ":"),
        (0.50, "P50 (mediana)", "-"),
        (0.90, "P90", ":"),
    ]:
        xq = weighted_quantile(df_score["exposure_score"], df_score["peso"], q)
        ax.axvline(xq, color="gray", linestyle=sty, linewidth=1.2, alpha=0.8)
        ax.scatter([xq], [q * 100], s=40, zorder=5)
        ax.annotate(f"{lab}\n{xq:.2f}", xy=(xq, q * 100), xytext=(8, 8), textcoords="offset points", fontsize=8)

    ax.axvline(media, color="crimson", linestyle="--", linewidth=1.5, label=f"Media {media:.3f}")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100))
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_hist_stacked_grupo(df_score: pd.DataFrame, path: Path, dpi: int = 300) -> None:
    sns.set_theme(style="ticks")
    apply_publication_style()
    scores = df_score["exposure_score"].values
    pesos = df_score["peso"].values / 1e6
    grupos = df_score["grande_grupo"].fillna("Outros").astype(str)
    n_bins = 40
    bins = np.linspace(scores.min(), scores.max(), n_bins + 1)
    centers = (bins[:-1] + bins[1:]) / 2
    uniq = sorted(grupos.unique())
    medias = {
        g: weighted_mean(df_score.loc[grupos == g, "exposure_score"], df_score.loc[grupos == g, "peso"])
        for g in uniq
    }
    uniq = sorted(uniq, key=lambda g: medias.get(g, 0), reverse=True)

    H = np.zeros((len(uniq), n_bins))
    for i, g in enumerate(uniq):
        m = grupos == g
        H[i], _ = np.histogram(scores[m], bins=bins, weights=pesos[m])

    fig, ax = plt.subplots(figsize=FIG01_TOP_FIGSIZE_INCHES)
    # uniq ordenado por exposicao media decrescente: vermelho = maior exposicao
    colors = palette_blue2red_n_categories(len(uniq), high_first=True)
    ax.stackplot(
        centers,
        *H,
        labels=uniq,
        colors=colors,
        alpha=0.92,
        linewidth=0.35,
        edgecolor="white",
    )
    ymax = float(np.max(H.sum(axis=0)) * 1.06) if H.size else 15.0
    ax.set_xlabel("Score de exposicao a IA generativa (ILO WP140)")
    ax.set_ylabel("Trabalhadores (milhoes) por faixa de score")
    ax.set_ylim(0, ymax)
    ax.margins(x=0.01)
    style_axes_clean(ax, grid_axis="y")
    # Legenda 1 coluna, sobreposta no canto superior direito (mesmo layout/margens que o histograma)
    leg = ax.legend(
        loc="upper right",
        bbox_to_anchor=(0.99, 0.99),
        bbox_transform=ax.transAxes,
        borderaxespad=0.35,
        frameon=True,
        fancybox=False,
        framealpha=0.9,
        edgecolor="#BBBBBB",
        facecolor="white",
        fontsize=7.5,
        ncol=1,
        handlelength=1.05,
        labelspacing=0.35,
    )
    leg.set_zorder(100)

    layout_figure_no_header(fig, **FIG01_TOP_LAYOUT)
    save_publication_figure(fig, path, dpi=dpi, bbox_inches=None)


def plot_kde_quartis(df_score: pd.DataFrame, path: Path, dpi: int = 150) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(8, 5))
    scores = df_score["exposure_score"].values
    pesos = df_score["peso"].values
    kde = gaussian_kde(scores, weights=pesos / pesos.sum())
    x = np.linspace(scores.min(), scores.max(), 300)
    y = kde(x)
    scale = pesos.sum() / 1e6
    bin_w = (scores.max() - scores.min()) / 40
    y_m = y * scale * bin_w

    q10 = weighted_quantile(df_score["exposure_score"], df_score["peso"], 0.10)
    q25 = weighted_quantile(df_score["exposure_score"], df_score["peso"], 0.25)
    q50 = weighted_quantile(df_score["exposure_score"], df_score["peso"], 0.50)
    q75 = weighted_quantile(df_score["exposure_score"], df_score["peso"], 0.75)
    q90 = weighted_quantile(df_score["exposure_score"], df_score["peso"], 0.90)
    media = weighted_mean(df_score["exposure_score"], df_score["peso"])

    ax.fill_between(x, 0, y_m, where=(x >= q25) & (x <= q75), alpha=0.35, color="steelblue", label="IQR (P25–P75)")
    ax.fill_between(x, 0, y_m, where=(x >= q10) & (x <= q90), alpha=0.15, color="steelblue", label="P10–P90")
    ax.plot(x, y_m, color="darkred", linewidth=2, label="KDE (escala em milhoes)")
    ax.axvline(q50, color="black", linestyle="-", linewidth=1.2, label=f"Mediana {q50:.3f}")
    ax.axvline(media, color="crimson", linestyle="--", linewidth=1.2, label=f"Media {media:.3f}")
    ax.set_xlabel("Score de exposicao")
    ax.set_ylabel("Densidade x milhoes (alinhada ao histograma 40 faixas)")
    ax.set_title("Densidade (KDE) com faixas de dispersao ponderadas")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _allocate_waffle_cells(df_score: pd.DataFrame, n_cells: int = 100) -> list[tuple[str, str]]:
    """Largest remainder: n_cells inteiros por gradiente, soma = n_cells."""
    total_w = df_score["peso"].sum()
    exact = []
    for grad in GRADIENT_ORDER:
        w = df_score.loc[df_score["exposure_gradient"] == grad, "peso"].sum()
        exact.append((grad, w / total_w * n_cells))
    floors = [int(np.floor(e[1])) for e in exact]
    rem = n_cells - sum(floors)
    frac = [(e[0], e[1] - np.floor(e[1])) for e in exact]
    frac.sort(key=lambda t: -t[1])
    counts = dict(zip([e[0] for e in exact], floors))
    for i in range(rem):
        counts[frac[i][0]] += 1
    seq = []
    for grad in GRADIENT_ORDER:
        c = GRADIENT_COLORS.get(grad, "#999")
        for _ in range(counts.get(grad, 0)):
            seq.append((grad, c))
    while len(seq) < n_cells:
        seq.append(("Sem classificacao", "#ddd"))
    return seq[:n_cells]


def plot_waffle(df_score: pd.DataFrame, path: Path, dpi: int = 150) -> None:
    _style()
    cells = _allocate_waffle_cells(df_score, 100)
    n_rows, n_cols = 10, 10
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_aspect("equal")
    ax.axis("off")
    for k, (_, color) in enumerate(cells):
        row, col = divmod(k, n_cols)
        row = n_rows - 1 - row
        rect = mpatches.Rectangle((col, row), 0.95, 0.95, facecolor=color, edgecolor="white", linewidth=0.6)
        ax.add_patch(rect)
    ax.set_title("Composicao por gradiente ILO (100 celulas ≈ 1% cada)")

    handles = [
        mpatches.Patch(color=GRADIENT_COLORS[g], label=GRADIENT_LABELS_PT.get(g, g))
        for g in GRADIENT_ORDER
    ]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_lollipop_g34(df_score: pd.DataFrame, path: Path, dpi: int = 150) -> None:
    _style()
    rows = []
    total_w = df_score["peso"].sum()
    for grad in GRADIENT_ORDER:
        pop = df_score.loc[df_score["exposure_gradient"] == grad, "peso"].sum() / 1e6
        pct = df_score.loc[df_score["exposure_gradient"] == grad, "peso"].sum() / total_w * 100
        rows.append(
            {
                "lab": GRADIENT_LABELS_PT.get(grad, grad),
                "pop": pop,
                "pct": pct,
                "color": GRADIENT_COLORS.get(grad, "#999"),
                "grad": grad,
            }
        )
    gdf = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8, 5))
    y = np.arange(len(gdf))
    ax.hlines(y, 0, gdf["pop"], color=gdf["color"], linewidth=4, alpha=0.85)
    ax.scatter(gdf["pop"], y, color=gdf["color"], s=80, zorder=3, edgecolors="white")
    for i, r in gdf.iterrows():
        ax.text(r["pop"] + 0.35, i, f"{r['pop']:.1f}M ({r['pct']:.1f}%)", va="center", fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels(gdf["lab"])
    ax.invert_yaxis()
    ax.set_xlabel("Trabalhadores (milhoes)")
    ax.set_title("Populacao por gradiente ILO (lollipop)")

    pop_g34 = df_score.loc[df_score["exposure_gradient"].isin(HIGH_G), "peso"].sum()
    pct_g34 = pop_g34 / total_w * 100
    ax.axvspan(0, gdf["pop"].max() * 1.12, ymin=0.02, ymax=0.18, color="none")
    fig.text(
        0.12,
        0.02,
        f"Alta exposicao (G3+G4): {pop_g34/1e6:.1f} milhoes ({pct_g34:.1f}% da forca de trabalho)",
        fontsize=9,
        style="italic",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_barra_100pct(df_score: pd.DataFrame, path: Path, dpi: int = 150) -> None:
    _style()
    total_w = df_score["peso"].sum()
    left = 0.0
    fig, ax = plt.subplots(figsize=(9, 2.2))
    for grad in GRADIENT_ORDER:
        w = df_score.loc[df_score["exposure_gradient"] == grad, "peso"].sum()
        p = w / total_w
        if p <= 0:
            continue
        ax.barh(0, p, left=left, height=0.5, color=GRADIENT_COLORS.get(grad, "#999"), edgecolor="white", linewidth=1)
        mid = left + p / 2
        lab = GRADIENT_LABELS_PT.get(grad, grad)
        if p >= 0.06:
            ax.text(mid, 0, f"{p*100:.1f}%\n{w/1e6:.1f}M", ha="center", va="center", fontsize=8, color="black")
        else:
            ax.text(mid, 0.35, f"{p*100:.1f}%", ha="center", va="bottom", fontsize=7, rotation=0)
        left += p
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Proporcao da populacao ocupada (100%)")
    ax.set_title("Composicao por gradiente ILO (barra empilhada 100%)")
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0))
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main():
    csv_path = DATA_OUTPUT / "pnad_ilo_merged.csv"
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)
    df["cod_ocupacao"] = df["cod_ocupacao"].astype(str).str.zfill(4)
    df_score = df[df["exposure_score"].notna()].copy()

    outs = [
        (plot_ecdf_percentis, DATA_FIGURES / "fig_01_var_ecdf_percentis.png"),
        (plot_hist_stacked_grupo, DATA_FIGURES / "fig_01_var_hist_empilhado_grande_grupo.png"),
        (plot_kde_quartis, DATA_FIGURES / "fig_01_var_kde_faixas_quartis.png"),
        (plot_waffle, DATA_FIGURES / "fig_02_var_waffle_100.png"),
        (plot_lollipop_g34, DATA_FIGURES / "fig_02_var_lollipop_destaque_g34.png"),
        (plot_barra_100pct, DATA_FIGURES / "fig_02_var_barra_100pct.png"),
    ]
    for fn, p in outs:
        fn(df_score, p)
        print(f"Salvo: {p}")


if __name__ == "__main__":
    main()
