"""
Estilo visual alinhado a publicações (OIT / IPEA / working papers).
Usado pelos scripts export_fig_distribuicao_exposicao_*.py
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import lines as mlines
from pathlib import Path

# Paleta base (inspirada em guia do usuário)
CORES = {
    "azul": "#1C4E80",
    "laranja": "#E05C1A",
    "cinza": "#6C757D",
    "verde": "#2E7D32",
    "vermelho": "#C62828",
    "azul_claro": "#A8C7E8",
    "fundo_grid": "#E8E8E8",
    "texto_sec": "#555555",
    "texto_fonte": "#666666",
    "linha_sep": "#CCCCCC",
}

# Ciclo principal + extensão para muitas categorias (ex.: 9 grandes grupos)
PALETA_CATEGORICA = [
    CORES["azul"],
    CORES["laranja"],
    CORES["verde"],
    CORES["vermelho"],
    CORES["cinza"],
    "#5C6BC0",
    "#00838F",
    "#6A1B9A",
    "#795548",
]

FONTE_PADRAO = (
    "Elaboracao propria. PNAD Continua (IBGE) e Gmyrek et al. (2025), WP140 — ILO."
)

# Figuras superiores do painel fig_01 (histograma + stack por grupo): mesmo tamanho
# de figura e mesmas margens para eixos alinhados no composito / lado a lado.
FIG01_TOP_FIGSIZE_INCHES = (10.5, 5.8)
FIG01_TOP_LAYOUT = dict(left=0.10, right=0.98, top=0.94, bottom=0.17)

# Blue2DarkRed12Steps (pypalettes) — fallback identico ao cmap discreto
BLUE2DARKRED12_FALLBACK = [
    "#290AD8FF",
    "#264DFFFF",
    "#3FA0FFFF",
    "#72D9FFFF",
    "#AAF7FFFF",
    "#E0FFFFFF",
    "#FFFFBFFF",
    "#FFE099FF",
    "#FFAD72FF",
    "#F76D5EFF",
    "#D82632FF",
    "#A50021FF",
]


def load_blue2dark_red12_colors() -> list[str]:
    """
    12 cores Blue2DarkRed12Steps (hex com alpha, compativel com matplotlib>=3.7).
    Usa pypalettes se disponivel; senao lista fixa acima.
    """
    try:
        from pypalettes import load_cmap

        cmap = load_cmap("Blue2DarkRed12Steps")
        if hasattr(cmap, "colors") and cmap.colors is not None and len(cmap.colors) >= 12:
            return [str(x) for x in cmap.colors[:12]]
    except Exception:
        pass
    return list(BLUE2DARKRED12_FALLBACK)


def palette_il_gradient_6_colors() -> list[str]:
    """
    Seis cores ao longo da rampa para os 6 gradientes ILO em ordem WP140
    (Nao exposto ~ azul ... Gradiente 4 ~ vermelho escuro).
    """
    c = load_blue2dark_red12_colors()
    idx = [0, 2, 4, 6, 9, 11]
    return [c[i] for i in idx]


def palette_blue2red_n_categories(n: int, *, high_first: bool = False) -> list[str]:
    """
    n cores espacadas ao longo da rampa (azul -> vermelho).
    Se high_first=True, inverte (util quando a 1a serie e maior exposicao).
    """
    base = load_blue2dark_red12_colors()
    if n <= 0:
        return []
    if n == 1:
        out = [base[0]]
    else:
        idx = [int(round(i * (len(base) - 1) / (n - 1))) for i in range(n)]
        out = [base[j] for j in idx]
    if high_first:
        out = list(reversed(out))
    return out


def apply_publication_style() -> None:
    """Configura matplotlib globalmente para figuras de dissertacao."""
    plt.rcParams.update(
        {
            # Times New Roman (captions / titulos no LaTeX; figura so com eixos rotulados)
            "font.family": "serif",
            "font.serif": [
                "Times New Roman",
                "Times",
                "Nimbus Roman",
                "DejaVu Serif",
            ],
            "font.size": 11,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelcolor": "#1A1A1A",
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "legend.fontsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.9,
            "axes.edgecolor": "#333333",
            "grid.linewidth": 0.55,
            "grid.color": CORES["fundo_grid"],
            "grid.linestyle": "--",
            "grid.alpha": 0.85,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            # Nao fixar figure.dpi baixo: conflita com savefig(dpi=300) e reduz
            # o tamanho em pixels sem bbox_inches='tight' (figura * dpi != esperado).
            "savefig.dpi": 300,
            "savefig.facecolor": "white",
            "axes.prop_cycle": mpl.cycler(color=PALETA_CATEGORICA),
        }
    )


def style_axes_clean(ax, grid_axis: str = "y") -> None:
    """Grid apenas em um eixo; deixa leitura tipo relatorio."""
    ax.grid(True, axis=grid_axis, linestyle="--", linewidth=0.55, alpha=0.85, color=CORES["fundo_grid"])
    ax.grid(False, axis="x" if grid_axis == "y" else "y")


def layout_figure_no_header(
    fig: mpl.figure.Figure,
    *,
    left: float = 0.1,
    right: float = 0.97,
    top: float = 0.96,
    bottom: float = 0.12,
) -> None:
    """Margens para figura sem titulo na arte (legenda de figura fica no LaTeX)."""
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)


def add_publication_header(
    fig: mpl.figure.Figure,
    title: str,
    subtitle: str | None = None,
    fonte: str | None = None,
    *,
    top: float = 0.88,
    bottom: float = 0.14,
    left: float = 0.09,
    right: float = 0.96,
) -> None:
    """Titulo, subtitulo, linha e nota de fonte em coords da figura."""
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
    fig.text(
        left,
        0.97,
        title,
        fontsize=13,
        fontweight="bold",
        va="top",
        ha="left",
        color="#1A1A1A",
    )
    y_sub = 0.935
    if subtitle:
        fig.text(
            left,
            y_sub,
            subtitle,
            fontsize=10,
            va="top",
            ha="left",
            color=CORES["texto_sec"],
        )
        y_line = y_sub - 0.028
    else:
        y_line = 0.91
    fig.add_artist(
        mlines.Line2D(
            [left, right],
            [y_line, y_line],
            transform=fig.transFigure,
            color=CORES["linha_sep"],
            linewidth=0.85,
            clip_on=False,
        )
    )
    if fonte:
        fig.text(
            left,
            0.03,
            f"Fonte: {fonte}",
            fontsize=8,
            va="bottom",
            ha="left",
            color=CORES["texto_fonte"],
            style="italic",
        )


def save_publication_figure(
    fig: mpl.figure.Figure,
    path: Path,
    dpi: int = 300,
    *,
    bbox_inches: str | None = "tight",
) -> None:
    """
    bbox_inches='tight' recorta cada figura de modo distinto (PNG com tamanhos diferentes).
    Use bbox_inches=None para salvar a figura inteira em figsize*dpi (painel alinhado).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.set_dpi(dpi)
    kw: dict = {"dpi": dpi, "facecolor": "white", "edgecolor": "none"}
    if bbox_inches is not None:
        kw["bbox_inches"] = bbox_inches
        kw["pad_inches"] = 0.18
    fig.savefig(path, **kw)
    plt.close(fig)
