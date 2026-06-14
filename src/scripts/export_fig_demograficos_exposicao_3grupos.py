"""
Painel composto: Sexo, Raca, Faixa Etaria, Escolaridade e Renda x Exposicao a IA.

Cinco sub-graficos verticais com barras horizontais 100% empilhadas: cada
barra representa a decomposicao da forca de trabalho da categoria nos tres
grupos de exposicao (Baixa = Not Exp + Min Exp; Moderada = G1+G2; Alta =
G3+G4) — mesmas cores semaforicas dos mapas UF (azul/amarelo/vermelho).

Anotacoes em cada barra:
  - % de cada segmento (apenas se >= 4% para nao poluir)
  - Volume total da categoria entre colchetes a direita do label

Saidas:
  - outputs/figures/etapa_1b/fig_04_demograficos_exposicao_3grupos.png   (painel composto)
  - outputs/figures/etapa_1b/fig_04a_demografico_sexo.png                (individual)
  - outputs/figures/etapa_1b/fig_04b_demografico_raca.png                (individual)
  - outputs/figures/etapa_1b/fig_04c_demografico_faixa_etaria.png        (individual)
  - outputs/figures/etapa_1b/fig_04d_demografico_escolaridade.png        (individual)
  - outputs/figures/etapa_1b/fig_04e_demografico_renda.png               (individual)

Uso:
  python src/scripts/export_fig_demograficos_exposicao_3grupos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from dissertation_plot_theme import apply_publication_style  # noqa: E402

DATA_INPUT = ROOT / "data" / "output" / "pnad_ilo_merged.csv"
DIR_FIGURES = ROOT / "outputs" / "figures" / "etapa_1b"

# ----------------------------------------------------------------------
# Configuracao
# ----------------------------------------------------------------------
GRADIENT_TO_GROUP = {
    "Not Exposed": "baixa",
    "Minimal Exposure": "baixa",
    "Exposed: Gradient 1": "moderada",
    "Exposed: Gradient 2": "moderada",
    "Exposed: Gradient 3": "alta",
    "Exposed: Gradient 4": "alta",
}

GRUPOS = ["baixa", "moderada", "alta"]

# Cores semaforicas, harmonizadas com os mapas UF (Blues / YlOrBr / Reds)
# e com a paleta institucional do dissertation_plot_theme (#1C4E80, #C62828)
GROUP_COLORS = {
    "baixa": "#3373B5",      # azul medio (Blues @ 0.65)
    "moderada": "#E5A41A",   # amarelo dourado (YlOrBr @ 0.55)
    "alta": "#C72A2A",       # vermelho medio (Reds @ 0.65)
}

GROUP_LABELS = {
    "baixa": "Baixa (Não Exposto + Mín. Exposição)",
    "moderada": "Moderada (Gradientes 1 + 2)",
    "alta": "Alta (Gradientes 3 + 4)",
}

EDU_MAP = {
    "1": "Sem/Fund.Inc.", "2": "Sem/Fund.Inc.",
    "3": "Fund.Comp.",
    "4": "Med.Comp.", "5": "Med.Comp.",
    "6": "Sup.Comp.", "7": "Sup.Comp.",
}

DIMENSIONS = [
    {
        "label": "SEXO",
        "col": "sexo_texto",
        "order": ["Homem", "Mulher"],
        "slug": "04a_demografico_sexo",
        "title_individual": "Exposição à IA generativa por sexo",
        "subtitle_individual": "Decomposição da força de trabalho ocupada por sexo — Brasil 3T/2025",
    },
    {
        "label": "RAÇA",
        "col": "raca_agregada",
        "order": ["Branca", "Negra", "Outras"],
        "slug": "04b_demografico_raca",
        "title_individual": "Exposição à IA generativa por raça/cor",
        "subtitle_individual": "Decomposição da força de trabalho ocupada por raça/cor (agregada conforme Osório, 2003) — Brasil 3T/2025",
    },
    {
        "label": "FAIXA ETÁRIA",
        "col": "faixa_etaria",
        "order": ["18-24", "25-34", "35-44", "45-54", "55+"],
        "slug": "04c_demografico_faixa_etaria",
        "title_individual": "Exposição à IA generativa por faixa etária",
        "subtitle_individual": "Decomposição da força de trabalho ocupada por faixa etária — Brasil 3T/2025",
    },
    {
        "label": "ESCOLARIDADE",
        "col": "edu_simples",
        "order": ["Sem/Fund.Inc.", "Fund.Comp.", "Med.Comp.", "Sup.Comp."],
        "slug": "04d_demografico_escolaridade",
        "title_individual": "Exposição à IA generativa por nível de escolaridade",
        "subtitle_individual": "Decomposição da força de trabalho ocupada por nível de escolaridade — Brasil 3T/2025",
    },
    {
        "label": "FAIXA DE RENDA",
        "col": "faixa_renda_sm",
        "order": ["Até 1 SM", "1-2 SM", "2-3 SM", "3-5 SM", "5+ SM"],
        "slug": "04e_demografico_renda",
        "title_individual": "Exposição à IA generativa por faixa de renda",
        "subtitle_individual": "Decomposição da força de trabalho ocupada por faixa de renda (em salários mínimos) — Brasil 3T/2025",
    },
]

FONTE = (
    "Fonte: PNAD Contínua 3T/2025 (IBGE) e Índice Global de Exposição Ocupacional à IAG "
    "(Gmyrek et al. 2025, OIT WP140)."
)


# ----------------------------------------------------------------------
# Agregacao
# ----------------------------------------------------------------------
def load_dataframe() -> pd.DataFrame:
    df = pd.read_csv(DATA_INPUT)
    df = df[df["exposure_gradient"].ne("Sem classificação")].copy()
    df["grupo3"] = df["exposure_gradient"].map(GRADIENT_TO_GROUP)
    if df["grupo3"].isna().any():
        raise ValueError("Mapeamento de gradiente -> grupo falhou.")
    df["edu_simples"] = df["nivel_instrucao"].astype(str).map(EDU_MAP).fillna("Outros")
    df = df[df["edu_simples"].ne("Outros")].copy()
    return df


def aggregate_dimension(df: pd.DataFrame, col: str, order: list[str]) -> pd.DataFrame:
    """Para cada categoria, retorna volume total e % de baixa/moderada/alta."""
    rows = []
    for cat in order:
        sub = df[df[col] == cat]
        peso_total = float(sub["peso"].sum())
        if peso_total <= 0:
            continue
        row = {
            "categoria": cat,
            "vol_total_milhoes": peso_total / 1e6,
        }
        for g in GRUPOS:
            peso_g = float(sub.loc[sub["grupo3"].eq(g), "peso"].sum())
            row[f"pct_{g}"] = peso_g / peso_total * 100
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Plotagem
# ----------------------------------------------------------------------
def plot_dimension(ax: plt.Axes, df_dim: pd.DataFrame, label_dim: str) -> None:
    """Desenha um sub-painel: barras horizontais 100% empilhadas para uma dimensao."""
    n = len(df_dim)
    y_pos = np.arange(n)[::-1]  # primeira categoria no topo

    cumul = np.zeros(n)
    for g in GRUPOS:
        widths = df_dim[f"pct_{g}"].to_numpy()
        ax.barh(
            y_pos, widths, left=cumul,
            color=GROUP_COLORS[g],
            edgecolor="white", linewidth=0.8,
            height=0.72,
        )
        for i, w in enumerate(widths):
            if w >= 2.5:
                xpos = cumul[i] + w / 2
                ax.text(
                    xpos, y_pos[i], f"{w:.1f}%",
                    ha="center", va="center",
                    fontsize=8.0 if w < 4.0 else 8.5,
                    fontweight="bold", color="white",
                )
        cumul += widths

    # Volume absoluto a direita
    for i, vol in enumerate(df_dim["vol_total_milhoes"].to_numpy()):
        ax.text(
            101.5, y_pos[i], f"[{vol:.1f}M]",
            ha="left", va="center",
            fontsize=8.5, color="#444444", style="italic",
        )

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels([f"{x}%" for x in [0, 25, 50, 75, 100]], fontsize=8.5, color="#666666")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_dim["categoria"].tolist(), fontsize=10)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=2)

    # Bordas: so eixo inferior visivel
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.spines["bottom"].set_linewidth(0.8)

    # Grid leve no eixo X
    ax.grid(axis="x", color="#E8E8E8", linestyle="--", linewidth=0.55, alpha=0.85)
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)

    # Label da dimensao (titulo do painel)
    ax.set_title(label_dim, fontsize=11, fontweight="bold", loc="left", pad=8, color="#1A1A1A")


def plot_dimension_standalone(
    df_dim: pd.DataFrame,
    label_dim: str,
    title: str,
    subtitle: str,
    out_path: Path,
) -> None:
    """Renderiza uma figura PNG individual para uma dimensao."""
    apply_publication_style()

    n = len(df_dim)
    # Altura proporcional ao numero de barras + slack para header/legenda/rodape
    height_panel = n * 0.55 + 0.4
    height_header = 0.95
    height_legend = 0.45
    height_footer = 0.50
    fig_height = height_header + height_panel + height_legend + height_footer
    fig_width = 11.5

    fig = plt.figure(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor("white")

    gs = gridspec.GridSpec(
        4, 1,
        height_ratios=[height_header, height_panel, height_legend, height_footer],
        hspace=0.35,
    )

    ax_header = fig.add_subplot(gs[0])
    ax_header.axis("off")
    ax_header.text(
        0.0, 0.85,
        title,
        ha="left", va="top", fontsize=14, fontweight="bold", color="#1A1A1A",
    )
    ax_header.text(
        0.0, 0.45,
        subtitle,
        ha="left", va="top", fontsize=10.5, color="#555555",
    )

    ax_plot = fig.add_subplot(gs[1])
    plot_dimension(ax_plot, df_dim, label_dim)

    ax_legend = fig.add_subplot(gs[2])
    ax_legend.axis("off")
    handles = [
        mpatches.Patch(color=GROUP_COLORS[g], label=GROUP_LABELS[g])
        for g in GRUPOS
    ]
    ax_legend.legend(
        handles=handles, loc="center", fontsize=9.5, frameon=False,
        handlelength=1.6, handleheight=0.9, ncol=3, borderpad=0.3, columnspacing=2.5,
    )

    ax_footer = fig.add_subplot(gs[3])
    ax_footer.axis("off")
    ax_footer.text(
        0.0, 0.65,
        "Cor: % da categoria em cada nível de exposição. Texto: % dentro do segmento (≥2,5%) e volume total da categoria entre colchetes.",
        ha="left", va="center", fontsize=8, color="#666666", style="italic",
    )
    ax_footer.text(
        0.0, 0.10,
        FONTE,
        ha="left", va="center", fontsize=8, color="#666666", style="italic",
    )

    fig.subplots_adjust(left=0.13, right=0.92, top=0.96, bottom=0.03)
    fig.savefig(out_path, dpi=300, facecolor="white")
    plt.close(fig)


def main() -> None:
    print(f"[1/3] Carregando {DATA_INPUT.name}...")
    df = load_dataframe()
    print(f"    -> {df['peso'].sum()/1e6:.1f}M ocupados classificaveis com escolaridade definida.")

    print("[2/4] Agregando 5 dimensoes...")
    aggregations = []
    for dim in DIMENSIONS:
        agg = aggregate_dimension(df, dim["col"], dim["order"])
        if agg.empty:
            raise RuntimeError(f"Nenhum dado para dimensao {dim['label']}.")
        aggregations.append((dim, agg))
        print(f"    [{dim['label']}] {len(agg)} categorias.")

    print("[3/4] Renderizando painel composto...")
    apply_publication_style()

    n_categorias = [len(agg) for _, agg in aggregations]  # [2, 3, 5, 4, 5]

    # Altura proporcional ao numero de barras + slack para titulos
    heights_panel = [n + 0.9 for n in n_categorias]
    height_header = 1.0
    height_footer = 0.4
    fig_height = sum(heights_panel) + height_header + height_footer
    fig_width = 12.0

    fig = plt.figure(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor("white")

    gs = gridspec.GridSpec(
        2 + len(aggregations), 1,
        height_ratios=[height_header] + heights_panel + [height_footer],
        hspace=0.55,
    )

    # Header
    ax_header = fig.add_subplot(gs[0])
    ax_header.axis("off")
    ax_header.text(
        0.0, 0.85,
        "Distribuição da força de trabalho ocupada por nível de exposição à IA generativa",
        ha="left", va="top", fontsize=14, fontweight="bold", color="#1A1A1A",
    )
    ax_header.text(
        0.0, 0.50,
        "Decomposição em Sexo, Raça, Faixa Etária, Escolaridade e Faixa de Renda — Brasil 3T/2025",
        ha="left", va="top", fontsize=10.5, color="#555555",
    )
    # Legenda manual em cima
    handles = [
        mpatches.Patch(color=GROUP_COLORS[g], label=GROUP_LABELS[g])
        for g in GRUPOS
    ]
    ax_header.legend(
        handles=handles, loc="upper right", bbox_to_anchor=(1.0, 0.85),
        fontsize=9, frameon=False, handlelength=1.4, handleheight=0.9,
        ncol=1, borderpad=0.3, labelspacing=0.4,
    )

    # 5 sub-paineis
    for i, (dim_meta, df_dim) in enumerate(aggregations):
        ax = fig.add_subplot(gs[i + 1])
        plot_dimension(ax, df_dim, dim_meta["label"])

    # Footer
    ax_footer = fig.add_subplot(gs[-1])
    ax_footer.axis("off")
    ax_footer.text(
        0.0, 0.5,
        "Cor: % da categoria em cada nível de exposição. Texto: % dentro do segmento (≥2,5%) e volume total da categoria entre colchetes.",
        ha="left", va="center", fontsize=8, color="#666666", style="italic",
    )
    ax_footer.text(
        0.0, 0.0,
        FONTE,
        ha="left", va="center", fontsize=8, color="#666666", style="italic",
    )

    fig.subplots_adjust(left=0.13, right=0.92, top=0.97, bottom=0.025)

    out_path = DIR_FIGURES / "fig_04_demograficos_exposicao_3grupos.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"    -> {out_path.relative_to(ROOT)}")

    print("[4/4] Renderizando 5 figuras individuais...")
    for dim_meta, df_dim in aggregations:
        out_individual = DIR_FIGURES / f"fig_{dim_meta['slug']}.png"
        plot_dimension_standalone(
            df_dim=df_dim,
            label_dim=dim_meta["label"],
            title=dim_meta["title_individual"],
            subtitle=dim_meta["subtitle_individual"],
            out_path=out_individual,
        )
        print(f"    -> {out_individual.relative_to(ROOT)}")

    print("\nFeito.")


if __name__ == "__main__":
    main()
