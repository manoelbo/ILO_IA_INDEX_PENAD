#!/usr/bin/env python3
"""Renderiza a Figura 5.2.3.3 — salário na coorte Canaries de 22 a 25 anos.

Usa as mesmas convenções visuais das demais figuras de grupo: banda de intervalo
de confiança, linha tracejada na média dos coeficientes pré, referência marcada
em novembro de 2022 e fronteira da janela congelada em +23.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

RENDER_DIR = Path(__file__).resolve().parent
if str(RENDER_DIR) not in sys.path:
    sys.path.insert(0, str(RENDER_DIR))

from phase8b_figures import (  # noqa: E402
    COLORS,
    DECIMAL_TICK_FORMATTER,
    GROUP_CI_ALPHA,
    _event_markers,
    _save_figure,
    _setup_style,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
COEFFICIENTS_PATH = (
    PACKAGE_ROOT / "results" / "models" / "canaries_22_25_wage_event_study.csv"
)
FIGURE_PATH = (
    PACKAGE_ROOT
    / "results"
    / "figures"
    / "figure_5_2_3_3_canaries_22_25_wage.png"
)


def render() -> None:
    data = pd.read_csv(COEFFICIENTS_PATH).sort_values("event_time")
    _setup_style()
    figure, axes = plt.subplots(figsize=(10.0, 6.4))
    figure.subplots_adjust(left=0.09, right=0.98, top=0.90, bottom=0.29)

    color = COLORS[0]
    axes.fill_between(
        data["event_time"],
        data["ci_low"],
        data["ci_high"],
        color=color,
        alpha=GROUP_CI_ALPHA,
        linewidth=0,
    )
    axes.plot(
        data["event_time"],
        data["coefficient"],
        color=color,
        linewidth=1.5,
        label="22 a 25 anos",
    )
    pre_mean = float(data["pre_coefficient_mean"].iloc[0])
    axes.axhline(
        pre_mean,
        color=color,
        linestyle="--",
        linewidth=0.9,
        alpha=0.9,
    )

    axes.set_xlim(-23.5, 41.5)
    axes.set_xticks([-23, -12, -1, 12, 23, 41])
    axes.set_xlabel("Meses relativos ao lançamento do ChatGPT")
    axes.set_ylabel("Coeficiente")
    axes.yaxis.set_major_formatter(DECIMAL_TICK_FORMATTER)
    _event_markers(axes)
    axes.set_title(
        "Figura 5.2.3.3 — Coorte de 22 a 25 anos — "
        "Salário real de admissão",
        loc="left",
        fontweight="bold",
    )

    handles, labels = axes.get_legend_handles_labels()
    conventions = [
        Line2D(
            [0],
            [0],
            color="#555555",
            linestyle="--",
            label=f"Média pré do grupo ({pre_mean:+.4f})".replace(".", ","),
        ),
        Line2D(
            [0],
            [0],
            color="#333333",
            linestyle="--",
            label="Referência nov/2022",
        ),
        Line2D(
            [0],
            [0],
            color="#777777",
            linestyle=":",
            label="Fronteira da janela congelada (+23)",
        ),
    ]
    figure.legend(
        [*handles, *conventions],
        [*labels, *[handle.get_label() for handle in conventions]],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.065),
        ncol=2,
        frameon=False,
    )
    figure.text(
        0.01,
        0.018,
        (
            "Nota: é o único contraste da dissertação cujo teste conjunto de "
            "tendências paralelas não é rejeitado (Wald sobre os 22 leads, "
            "p = 0,585; nenhum lead individualmente significativo a 5%). "
            "Trata-se de 1 entre 100 contrastes de diagnóstico, sem ajuste de "
            "multiplicidade sobre a família de pretrends: a figura exibe a "
            "exceção, não a comprova."
        ),
        ha="left",
        fontsize=7.5,
    )
    _save_figure(figure, FIGURE_PATH)
    print(f"[canaries-wage-figure] {FIGURE_PATH}", flush=True)


if __name__ == "__main__":
    render()
