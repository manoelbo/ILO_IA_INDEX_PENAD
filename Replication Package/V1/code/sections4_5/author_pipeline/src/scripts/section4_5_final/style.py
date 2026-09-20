"""Matplotlib style aligned with the Section 3 replication package."""

from __future__ import annotations

from pathlib import Path

_PYPLOT = None

LOW_BLUE = "#2f6fae"
MODERATE_YELLOW = "#d99a1e"
HIGH_RED = "#c7352f"
TEXT_DARK = "#1A1A1A"
TEXT_MUTED = "#555555"
GRID = "#D8D8D8"

GROUP_COLORS = {
    "Núcleo de Software e TI": HIGH_RED,
    "Atendimento e Contato com Cliente": MODERATE_YELLOW,
    "Finanças, Contabilidade e Administração": LOW_BLUE,
    "Comunicação, Linguagem e Conteúdo": "#7a4fa3",
    "Ocupações Digitais e de TI com Entrada de Dados": "#a8232f",
}

OUTCOME_COLORS = {
    "ln_admissoes": LOW_BLUE,
    "ln_desligamentos": MODERATE_YELLOW,
    "ln_salario_real_adm": HIGH_RED,
    "ln_salario_real_desl": "#7a4fa3",
    "asinh_saldo": "#6e6e6e",
    "saldo_per_pre_adm": "#8f5b2e",
}


def get_pyplot():
    global _PYPLOT
    if _PYPLOT is None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        _PYPLOT = plt
    return _PYPLOT


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
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
        }
    )


def save_figure(fig, path: Path) -> None:
    plt = get_pyplot()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def title_axis(ax, title: str, subtitle: str | None = None) -> None:
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=14, color=TEXT_DARK)
    if subtitle:
        ax.text(0.0, 1.015, subtitle, transform=ax.transAxes, ha="left", va="bottom", fontsize=9, color=TEXT_MUTED)

