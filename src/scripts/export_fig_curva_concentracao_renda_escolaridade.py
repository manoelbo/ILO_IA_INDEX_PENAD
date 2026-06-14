"""
Curvas de concentracao da exposicao (score ILO) — mesmo grafico, duas ordenacoes.

Alinhado a secao 3.4 do fluxo etapa_1b (curva com populacao ordenada por renda):
  eixo x: fracao acumulada da populacao (ponderada por `peso`);
  eixo y: fracao acumulada da exposicao total (ponderada);
  diagonal: neutralidade (cada fracao da populacao detem a mesma fracao da exposicao).

Curva laranja: ordenacao crescente de rendimento_habitual (mais pobres a esquerda).
Curva azul: ordenacao crescente de nivel_instrucao PNAD (1 = menos escolaridade ... 7).

Subpopulacao comum: tem_renda==1, rendimento_habitual e exposure_score e
nivel_instrucao validos — assim a massa total de exposicao e identica nas duas
curvas; o que muda e apenas a ordem em que os individuos entram no acumulado.

Indice de concentracao (igual etapa_1b): C = 1 - 2 * area sob a curva
(integracao trapezoidal em x = fracao populacional).

Diferente de export_fig_tendencia_alta_exposicao_renda_educacao.py, que mostra
% em G3+G4 por *faixas* discretas de renda/educacao.

Saidas:
  - outputs/figures/etapa_1b/fig_curva_concentracao_renda_escolaridade.png
  - outputs/tables/tab_curva_concentracao_indices.csv

Uso:
  PYTHONPATH=src/scripts python src/scripts/export_fig_curva_concentracao_renda_escolaridade.py
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

ROOT = Path(__file__).parent.parent.parent
DATA_OUTPUT = ROOT / "data" / "output"
DATA_FIGURES = ROOT / "outputs" / "figures" / "etapa_1b"
DATA_TABLES = ROOT / "outputs" / "tables"


def _trapz_area(y: np.ndarray, x: np.ndarray) -> float:
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


def _concentration_curve(
    df: pd.DataFrame, sort_cols: list[str]
) -> tuple[np.ndarray, np.ndarray]:
    """Ordena linhas e retorna (cum_pop, cum_exp) com (0,0) no inicio."""
    d = df.sort_values(sort_cols, kind="mergesort")
    vals = d["exposure_score"].to_numpy(dtype=float)
    wgts = d["peso"].to_numpy(dtype=float)
    tw = wgts.sum()
    te = (wgts * vals).sum()
    if tw <= 0 or te == 0:
        raise ValueError("Peso total ou exposicao total nulos.")
    cum_pop = np.concatenate([[0.0], np.cumsum(wgts) / tw])
    cum_exp = np.concatenate([[0.0], np.cumsum(wgts * vals) / te])
    return cum_pop, cum_exp


def _concentration_index(cum_pop: np.ndarray, cum_exp: np.ndarray) -> float:
    area = _trapz_area(cum_exp, cum_pop)
    return 1.0 - 2.0 * area


def main() -> None:
    csv_in = DATA_OUTPUT / "pnad_ilo_merged.csv"
    if not csv_in.exists():
        raise FileNotFoundError(csv_in)

    df = pd.read_csv(csv_in)
    df = df[
        (df["tem_renda"] == 1)
        & df["exposure_score"].notna()
        & df["rendimento_habitual"].notna()
        & df["nivel_instrucao"].notna()
    ].copy()
    df["nivel_instrucao_num"] = pd.to_numeric(df["nivel_instrucao"], errors="coerce")
    df = df[df["nivel_instrucao_num"].notna()].copy()
    if len(df) < 100:
        raise ValueError("Amostra insuficiente apos filtros.")

    cum_pop_r, cum_exp_r = _concentration_curve(
        df, ["rendimento_habitual", "nivel_instrucao_num"]
    )
    cum_pop_e, cum_exp_e = _concentration_curve(
        df, ["nivel_instrucao_num", "rendimento_habitual"]
    )

    idx_r = _concentration_index(cum_pop_r, cum_exp_r)
    idx_e = _concentration_index(cum_pop_e, cum_exp_e)

    DATA_TABLES.mkdir(parents=True, exist_ok=True)
    tab = pd.DataFrame(
        [
            {
                "ordenacao": "rendimento_habitual_crescente",
                "indice_concentracao": idx_r,
                "n_observacoes": len(df),
            },
            {
                "ordenacao": "nivel_instrucao_crescente",
                "indice_concentracao": idx_e,
                "n_observacoes": len(df),
            },
        ]
    )
    out_csv = DATA_TABLES / "tab_curva_concentracao_indices.csv"
    tab.to_csv(out_csv, index=False)

    sns.set_theme(style="ticks")
    apply_publication_style()
    fig, ax = plt.subplots(figsize=(7.2, 7.2))

    ax.plot(
        cum_pop_r,
        cum_exp_r,
        color=CORES["laranja"],
        linewidth=2.2,
        label=f"Ordenado por renda (C = {idx_r:+.3f})",
    )
    ax.plot(
        cum_pop_e,
        cum_exp_e,
        color=CORES["azul"],
        linewidth=2.2,
        label=f"Ordenado por escolaridade (C = {idx_e:+.3f})",
    )
    ax.plot([0, 1], [0, 1], color="#333333", linestyle="--", linewidth=1.0, label="Igualdade")

    ax.fill_between(cum_pop_r, cum_exp_r, cum_pop_r, alpha=0.12, color=CORES["laranja"])
    ax.fill_between(cum_pop_e, cum_exp_e, cum_pop_e, alpha=0.10, color=CORES["azul"])

    ax.set_xlabel("Fracao acumulada da populacao (ponderada)")
    ax.set_ylabel("Fracao acumulada da exposicao (score)")
    ax.set_title("Curvas de concentracao da exposicao")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    style_axes_clean(ax, grid_axis="both")
    ax.legend(loc="upper left", framealpha=0.95)

    layout_figure_no_header(fig, left=0.12, right=0.98, top=0.94, bottom=0.10)
    DATA_FIGURES.mkdir(parents=True, exist_ok=True)
    out_png = DATA_FIGURES / "fig_curva_concentracao_renda_escolaridade.png"
    save_publication_figure(fig, out_png, bbox_inches=None)

    print(f"Indice concentracao (renda):   {idx_r:+.4f}")
    print(f"Indice concentracao (escol.): {idx_e:+.4f}")
    print(f"Salvo: {out_png}")
    print(f"Salvo: {out_csv}")


if __name__ == "__main__":
    main()
