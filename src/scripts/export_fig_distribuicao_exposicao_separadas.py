"""
Exporta a Figura 3.1 (distribuição da exposição) em duas figuras separadas:
  1) histograma ponderado empilhado por gradiente ILO + KDE + media
  2) barras horizontais — populacao por gradiente ILO (cores Blue2DarkRed)

Estilo: Times New Roman, sem titulo na figura (caption no LaTeX).

Entrada: data/output/pnad_ilo_merged.csv
Saída:  outputs/figures/etapa_1b/fig_01_histograma_kde_exposicao.png
         outputs/figures/etapa_1b/fig_01_populacao_por_gradiente_ilo.png

Uso:
  python src/scripts/export_fig_distribuicao_exposicao_separadas.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import gaussian_kde

from dissertation_plot_theme import (
    CORES,
    FIG01_TOP_FIGSIZE_INCHES,
    FIG01_TOP_LAYOUT,
    apply_publication_style,
    layout_figure_no_header,
    palette_il_gradient_6_colors,
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

GRADIENT_LABELS_PT = {
    "Not Exposed": "Nao exposto",
    "Minimal Exposure": "Exposicao minima",
    "Exposed: Gradient 1": "Gradiente 1 (complementacao)",
    "Exposed: Gradient 2": "Gradiente 2",
    "Exposed: Gradient 3": "Gradiente 3",
    "Exposed: Gradient 4": "Gradiente 4 (automacao)",
}


def weighted_mean(values, weights):
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    return np.average(values[mask], weights=weights[mask])


def plot_histograma_kde(df_score: pd.DataFrame, out_path: Path) -> None:
    """
    Histograma empilhado por gradiente ILO: em cada faixa de score ve-se
    qual gradiente concentra massa (mesma rampa Blue2DarkRed das barras).
    """
    sns.set_theme(style="ticks")
    apply_publication_style()
    fig, ax = plt.subplots(figsize=FIG01_TOP_FIGSIZE_INCHES)

    bins = np.linspace(df_score["exposure_score"].min(), df_score["exposure_score"].max(), 41)
    w_m = df_score["peso"].values / 1e6
    total_por_faixa, _ = np.histogram(df_score["exposure_score"].values, bins=bins, weights=w_m)
    ymax = float(np.max(total_por_faixa) * 1.06) if len(total_por_faixa) else 15.0
    colors_grad = palette_il_gradient_6_colors()

    hist_data = []
    hist_weights = []
    hist_labels = []
    hist_colors = []
    for i, grad in enumerate(GRADIENT_ORDER):
        sub = df_score[df_score["exposure_gradient"] == grad]
        if len(sub) == 0:
            continue
        hist_data.append(sub["exposure_score"].values)
        hist_weights.append(sub["peso"].values / 1e6)
        hist_labels.append(GRADIENT_LABELS_PT.get(grad, grad))
        hist_colors.append(colors_grad[i])

    ax.hist(
        hist_data,
        bins=bins,
        weights=hist_weights,
        stacked=True,
        label=hist_labels,
        color=hist_colors,
        edgecolor="white",
        linewidth=0.35,
        zorder=1,
    )

    scores = df_score["exposure_score"].values
    pesos = df_score["peso"].values
    kde = gaussian_kde(scores, weights=pesos / pesos.sum())
    x_kde = np.linspace(scores.min(), scores.max(), 256)
    bin_width = (scores.max() - scores.min()) / 40
    kde_scaled = kde(x_kde) * (pesos.sum() / 1e6) * bin_width
    ax.plot(
        x_kde,
        kde_scaled,
        color="#1A1A1A",
        linewidth=2.2,
        label="Densidade (KDE), total",
        zorder=4,
    )

    media_exp = weighted_mean(df_score["exposure_score"], df_score["peso"])
    ax.axvline(
        media_exp,
        color=CORES["vermelho"],
        linestyle="--",
        linewidth=2,
        label=f"Media ponderada = {media_exp:.3f}",
        zorder=5,
    )
    ax.set_xlabel("Score de exposicao a IA generativa (ILO WP140)")
    ax.set_ylabel("Trabalhadores (milhoes)")
    ax.set_ylim(0, ymax)
    style_axes_clean(ax, grid_axis="y")
    ax.legend(
        loc="upper right",
        frameon=True,
        fancybox=False,
        framealpha=0.96,
        edgecolor="#CCCCCC",
        fontsize=8,
        ncol=1,
    )

    layout_figure_no_header(fig, **FIG01_TOP_LAYOUT)
    # Sem 'tight': mesmo figsize*dpi que o stack por grande grupo (composito alinhado)
    save_publication_figure(fig, out_path, bbox_inches=None)


def plot_gradientes(df_score: pd.DataFrame, out_path: Path) -> None:
    sns.set_theme(style="ticks")
    apply_publication_style()
    fig, ax = plt.subplots(figsize=(10, 5.8))

    colors_grad = palette_il_gradient_6_colors()
    color_by_grad = dict(zip(GRADIENT_ORDER, colors_grad))

    total_w = df_score["peso"].sum()
    grad_data = []
    for grad in GRADIENT_ORDER:
        sub = df_score[df_score["exposure_gradient"] == grad]
        if len(sub) > 0:
            pop = sub["peso"].sum() / 1e6
            pct = sub["peso"].sum() / total_w * 100
            grad_data.append(
                {
                    "Gradiente": GRADIENT_LABELS_PT.get(grad, grad),
                    "Pop": pop,
                    "Pct": pct,
                    "Color": color_by_grad.get(grad, "#999999"),
                }
            )

    grad_df = pd.DataFrame(grad_data)
    bars = ax.barh(
        grad_df["Gradiente"],
        grad_df["Pop"],
        color=grad_df["Color"],
        edgecolor="white",
        linewidth=0.65,
        height=0.62,
        zorder=3,
    )
    xmax = grad_df["Pop"].max()
    for bar, row in zip(bars, grad_df.itertuples()):
        ax.text(
            bar.get_width() + xmax * 0.018,
            bar.get_y() + bar.get_height() / 2,
            f"{row.Pop:.1f} M  ({row.Pct:.1f}%)",
            va="center",
            fontsize=9.5,
            color="#333333",
        )
    ax.set_xlabel("Trabalhadores (milhoes)")
    style_axes_clean(ax, grid_axis="x")
    ax.set_xlim(0, xmax * 1.22)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0)

    layout_figure_no_header(fig)
    save_publication_figure(fig, out_path)


def main():
    csv_path = DATA_OUTPUT / "pnad_ilo_merged.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {csv_path}")

    df = pd.read_csv(csv_path)
    df["cod_ocupacao"] = df["cod_ocupacao"].astype(str).str.zfill(4)
    df_score = df[df["exposure_score"].notna()].copy()

    out_hist = DATA_FIGURES / "fig_01_histograma_kde_exposicao.png"
    out_grad = DATA_FIGURES / "fig_01_populacao_por_gradiente_ilo.png"

    plot_histograma_kde(df_score, out_hist)
    plot_gradientes(df_score, out_grad)

    print(f"Salvo: {out_hist}")
    print(f"Salvo: {out_grad}")


if __name__ == "__main__":
    main()
