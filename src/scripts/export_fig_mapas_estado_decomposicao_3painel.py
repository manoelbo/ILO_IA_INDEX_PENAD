"""
Mapas coropletas UF — Decomposicao em 3 grupos de exposicao a IA generativa.

Tres mapas semaforicos (azul / amarelo / vermelho) que decompoem a forca de
trabalho brasileira em tres grupos OIT:
  - Baixa: Not Exposed + Minimal Exposure
  - Moderada: Gradient 1 + 2
  - Alta: Gradient 3 + 4

Cor encoda % intra-UF; texto mostra sigla + volume absoluto (milhoes) + %.

Saidas (8 PNG + 1 markdown):
  - outputs/figures/etapa_1b/fig_03_mapa_uf_{baixa|media|alta}_{continuo|quantil}.png
  - outputs/figures/etapa_1b/fig_03_painel_uf_decomposicao_{continuo|quantil}.png
  - outputs/tables/tab_decomposicao_uf_exposicao.md

Uso:
  python src/scripts/export_fig_mapas_estado_decomposicao_3painel.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import geobr
import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec
from matplotlib.colors import BoundaryNorm, Normalize

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from dissertation_plot_theme import apply_publication_style  # noqa: E402

# ----------------------------------------------------------------------
# Constantes
# ----------------------------------------------------------------------
DATA_INPUT = ROOT / "data" / "output" / "pnad_ilo_merged.csv"
DIR_FIGURES = ROOT / "outputs" / "figures" / "etapa_1b"
DIR_TABLES = ROOT / "outputs" / "tables"

GRUPOS = ["baixa", "media", "alta"]

GRADIENT_TO_GROUP = {
    "Not Exposed": "baixa",
    "Minimal Exposure": "baixa",
    "Exposed: Gradient 1": "media",
    "Exposed: Gradient 2": "media",
    "Exposed: Gradient 3": "alta",
    "Exposed: Gradient 4": "alta",
}

GROUP_META = {
    "baixa": {
        "titulo": "Baixa exposicao",
        "subtitulo": "Nao exposto + Exposicao minima",
        "cmap": "Blues",
    },
    "media": {
        "titulo": "Exposicao moderada",
        "subtitulo": "Gradientes 1 e 2",
        "cmap": "YlOrBr",
    },
    "alta": {
        "titulo": "Alta exposicao",
        "subtitulo": "Gradientes 3 e 4",
        "cmap": "Reds",
    },
}

# UFs pequenas que se beneficiam de callouts externos.
# Offsets em graus (lon, lat). Escolhidos para evitar sobreposicao com vizinhos.
UF_CALLOUT_OFFSETS = {
    "DF": (5.5, -3.5),
    "AL": (5.5, -1.8),
    "SE": (5.5, -0.5),
    "RJ": (5.5, -2.5),
    "ES": (5.5, 0.5),
    "PB": (6.0, 1.5),
    "RN": (6.0, 2.8),
    "PE": (6.5, -0.2),
}

FONTE = (
    "PNAD Continua 3T/2025 (IBGE) e Indice Global de Exposicao Ocupacional a IAG "
    "(Gmyrek et al. 2025, OIT WP140)."
)


# ----------------------------------------------------------------------
# Agregacao
# ----------------------------------------------------------------------
def load_and_aggregate() -> pd.DataFrame:
    """Le PNAD-ILO, exclui 'Sem classificacao' e agrega por UF em 3 grupos."""
    df = pd.read_csv(DATA_INPUT)
    df = df[df["exposure_gradient"].ne("Sem classificação")].copy()
    df["grupo3"] = df["exposure_gradient"].map(GRADIENT_TO_GROUP)
    if df["grupo3"].isna().any():
        faltando = df.loc[df["grupo3"].isna(), "exposure_gradient"].unique().tolist()
        raise ValueError(f"Categorias nao mapeadas: {faltando}")

    rows = []
    for uf, sub in df.groupby("sigla_uf"):
        peso_total = float(sub["peso"].sum())
        row = {
            "sigla_uf": uf,
            "peso_total": peso_total,
            "vol_total_milhoes": peso_total / 1e6,
        }
        for g in GRUPOS:
            peso_g = float(sub.loc[sub["grupo3"].eq(g), "peso"].sum())
            row[f"vol_{g}_milhoes"] = peso_g / 1e6
            row[f"pct_{g}"] = (peso_g / peso_total * 100) if peso_total > 0 else 0.0
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("sigla_uf").reset_index(drop=True)

    soma_pct = out[[f"pct_{g}" for g in GRUPOS]].sum(axis=1)
    if not np.allclose(soma_pct, 100.0, atol=0.05):
        raise AssertionError(f"Somatorio das % por UF nao bate 100: min={soma_pct.min()}, max={soma_pct.max()}")
    return out


# ----------------------------------------------------------------------
# Geometrias
# ----------------------------------------------------------------------
def load_geometries(df_agg: pd.DataFrame) -> gpd.GeoDataFrame:
    """Carrega malha de estados via geobr e faz merge com a tabela agregada."""
    states = geobr.read_state(year=2020)
    states["abbrev_state"] = states["abbrev_state"].str.upper()
    gdf = states.merge(df_agg, left_on="abbrev_state", right_on="sigla_uf", how="left")
    if gdf["sigla_uf"].isna().any():
        faltando = gdf.loc[gdf["sigla_uf"].isna(), "abbrev_state"].tolist()
        raise ValueError(f"UFs sem dados agregados: {faltando}")
    return gdf


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _text_color(value: float, vmin: float, vmax: float) -> str:
    if vmax <= vmin:
        return "black"
    norm = (value - vmin) / (vmax - vmin)
    return "white" if norm > 0.55 else "black"


def _annotate_uf(
    ax: plt.Axes,
    gdf: gpd.GeoDataFrame,
    group: str,
    vmin: float,
    vmax: float,
    *,
    fontsize_sigla: float = 9.0,
    fontsize_vol: float = 8.5,
    fontsize_pct: float = 7.5,
) -> None:
    """Anota cada UF com sigla (negrito), volume em milhoes e %."""
    pct_col = f"pct_{group}"
    vol_col = f"vol_{group}_milhoes"

    for _, row in gdf.iterrows():
        uf = row["abbrev_state"]
        c = row.geometry.centroid
        v = float(row[pct_col])
        vol = float(row[vol_col])

        if uf in UF_CALLOUT_OFFSETS:
            dx, dy = UF_CALLOUT_OFFSETS[uf]
            text_x, text_y = c.x + dx, c.y + dy
            ax.annotate(
                "",
                xy=(c.x, c.y),
                xytext=(text_x, text_y),
                arrowprops=dict(arrowstyle="-", color="0.35", lw=0.5),
            )
            tcol = "black"
        else:
            text_x, text_y = c.x, c.y
            tcol = _text_color(v, vmin, vmax)

        stroke_fg = "white" if tcol == "black" else "black"

        ax.text(
            text_x, text_y + 0.45, uf,
            ha="center", va="center",
            fontsize=fontsize_sigla, fontweight="bold", color=tcol,
            path_effects=[pe.withStroke(linewidth=2.0, foreground=stroke_fg)],
        )
        ax.text(
            text_x, text_y - 0.05, f"{vol:.1f}M",
            ha="center", va="center",
            fontsize=fontsize_vol, color=tcol,
            path_effects=[pe.withStroke(linewidth=2.0, foreground=stroke_fg)],
        )
        ax.text(
            text_x, text_y - 0.55, f"{v:.1f}%",
            ha="center", va="center",
            fontsize=fontsize_pct, fontstyle="italic", color=tcol,
            path_effects=[pe.withStroke(linewidth=1.5, foreground=stroke_fg)],
        )


def _build_norm_and_cmap(values: np.ndarray, cmap_name: str, scale: str):
    """Retorna (cmap, norm, edges_or_None) conforme tipo de escala."""
    if scale == "continuo":
        norm = Normalize(vmin=float(values.min()), vmax=float(values.max()))
        return plt.get_cmap(cmap_name), norm, None
    if scale == "quantil":
        edges = np.unique(np.quantile(values, np.linspace(0.0, 1.0, 7)))
        if len(edges) < 3:
            norm = Normalize(vmin=float(values.min()), vmax=float(values.max()))
            return plt.get_cmap(cmap_name), norm, None
        cmap = plt.get_cmap(cmap_name, len(edges) - 1)
        norm = BoundaryNorm(edges, cmap.N)
        return cmap, norm, edges
    raise ValueError(f"Escala desconhecida: {scale}")


# ----------------------------------------------------------------------
# Plot individual
# ----------------------------------------------------------------------
def plot_mapa_uf(gdf: gpd.GeoDataFrame, group: str, scale: str, output_path: Path) -> None:
    apply_publication_style()

    pct_col = f"pct_{group}"
    cmap_name = GROUP_META[group]["cmap"]
    titulo = GROUP_META[group]["titulo"]
    subtitulo = GROUP_META[group]["subtitulo"]
    vol_total = float(gdf[f"vol_{group}_milhoes"].sum())
    pct_total = vol_total / float(gdf["vol_total_milhoes"].sum()) * 100

    fig = plt.figure(figsize=(11, 11))
    fig.patch.set_facecolor("white")

    gs = gridspec.GridSpec(3, 1, height_ratios=[0.10, 0.82, 0.08], hspace=0.0)
    ax_header = fig.add_subplot(gs[0])
    ax_map = fig.add_subplot(gs[1])
    ax_footer = fig.add_subplot(gs[2])
    ax_header.axis("off")
    ax_footer.axis("off")
    ax_map.set_axis_off()

    values = gdf[pct_col].to_numpy()
    cmap, norm, edges = _build_norm_and_cmap(values, cmap_name, scale)

    gdf.plot(
        column=pct_col, cmap=cmap, norm=norm, linewidth=0.8,
        ax=ax_map, edgecolor="0.3", legend=False,
    )

    vmin, vmax = float(values.min()), float(values.max())
    _annotate_uf(ax_map, gdf, group, vmin, vmax)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_map, shrink=0.55, aspect=22, pad=0.02)
    cbar.set_label("% da forca de trabalho da UF", fontsize=10)
    if edges is not None:
        cbar.set_ticks(edges)
        cbar.set_ticklabels([f"{x:.1f}%" for x in edges])

    ax_header.text(0.0, 0.85, titulo, fontsize=15, fontweight="bold", ha="left", va="top")
    ax_header.text(0.0, 0.50, subtitulo, fontsize=11, ha="left", va="top", color="#555555")
    ax_header.text(
        0.0, 0.20,
        f"Brasil: {vol_total:.1f}M trabalhadores ({pct_total:.1f}% dos ocupados classificaveis).",
        fontsize=10, ha="left", va="top", color="#1A1A1A",
    )

    ax_footer.text(
        0.0, 0.6,
        "Cor: % da forca de trabalho da UF na categoria. Texto: sigla, volume absoluto (milhoes) e %.",
        fontsize=8, ha="left", va="top", color="#666666", style="italic",
    )
    ax_footer.text(0.0, 0.15, f"Fonte: {FONTE}", fontsize=8, ha="left", va="top", color="#666666", style="italic")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------
# Painel composto 1x3
# ----------------------------------------------------------------------
def plot_panel_1x3(gdf: gpd.GeoDataFrame, scale: str, output_path: Path) -> None:
    apply_publication_style()

    fig = plt.figure(figsize=(20, 10))
    fig.patch.set_facecolor("white")

    gs = gridspec.GridSpec(3, 3, height_ratios=[0.18, 0.74, 0.08], hspace=0.18, wspace=0.04)

    ax_global_header = fig.add_subplot(gs[0, :])
    ax_global_header.axis("off")
    ax_global_header.text(
        0.5, 0.95,
        "Distribuicao da forca de trabalho ocupada por nivel de exposicao a IA generativa — Brasil 3T/2025",
        ha="center", va="top", fontsize=15, fontweight="bold",
    )
    ax_global_header.text(
        0.5, 0.55,
        "Decomposicao das UFs em tres grupos: baixa (azul), moderada (amarelo) e alta (vermelho) exposicao.",
        ha="center", va="top", fontsize=10.5, color="#555555",
    )

    for idx, group in enumerate(GRUPOS):
        ax_map = fig.add_subplot(gs[1, idx])
        ax_map.set_axis_off()

        pct_col = f"pct_{group}"
        cmap_name = GROUP_META[group]["cmap"]
        values = gdf[pct_col].to_numpy()
        cmap, norm, edges = _build_norm_and_cmap(values, cmap_name, scale)

        gdf.plot(
            column=pct_col, cmap=cmap, norm=norm, linewidth=0.5,
            ax=ax_map, edgecolor="0.3", legend=False,
        )

        vmin, vmax = float(values.min()), float(values.max())
        _annotate_uf(
            ax_map, gdf, group, vmin, vmax,
            fontsize_sigla=7.5, fontsize_vol=7.0, fontsize_pct=6.2,
        )

        vol_total = float(gdf[f"vol_{group}_milhoes"].sum())
        pct_total = vol_total / float(gdf["vol_total_milhoes"].sum()) * 100
        title = f"{GROUP_META[group]['titulo']} — {GROUP_META[group]['subtitulo']}"
        sub = f"Brasil: {vol_total:.1f}M ({pct_total:.1f}%)"
        ax_map.set_title(f"{title}\n{sub}", fontsize=11, fontweight="bold", pad=6)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax_map, orientation="horizontal", shrink=0.85, aspect=30, pad=0.02)
        cbar.set_label("% da UF", fontsize=8.5)
        cbar.ax.tick_params(labelsize=7)
        if edges is not None:
            cbar.set_ticks(edges)
            cbar.set_ticklabels([f"{x:.1f}" for x in edges])

    ax_footer = fig.add_subplot(gs[2, :])
    ax_footer.axis("off")
    ax_footer.text(
        0.5, 0.6,
        "Cor: % dos ocupados da UF na categoria. Texto: sigla, volume absoluto (milhoes) e percentual intra-estado.",
        ha="center", va="top", fontsize=8, color="#666666", style="italic",
    )
    ax_footer.text(
        0.5, 0.15,
        f"Fonte: {FONTE} N=94.0M ocupados classificaveis (excluindo 'Sem classificacao').",
        ha="center", va="top", fontsize=8, color="#666666", style="italic",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------
# Tabela de apoio
# ----------------------------------------------------------------------
def export_table(df_agg: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = df_agg.copy().sort_values("pct_alta", ascending=False)

    cols = [
        ("UF", "sigla_uf"),
        ("Total (M)", "vol_total_milhoes"),
        ("Baixa (M)", "vol_baixa_milhoes"),
        ("Baixa (%)", "pct_baixa"),
        ("Moderada (M)", "vol_media_milhoes"),
        ("Moderada (%)", "pct_media"),
        ("Alta (M)", "vol_alta_milhoes"),
        ("Alta (%)", "pct_alta"),
    ]

    lines = [
        "# Decomposicao da forca de trabalho ocupada por nivel de exposicao a IA — UF (PNADC 3T/2025)",
        "",
        "Universo: ocupados classificaveis (~94.0M, excluindo 'Sem classificacao').",
        "Grupos OIT: Baixa = Not Exposed + Minimal Exposure; Moderada = Gradients 1+2; Alta = Gradients 3+4.",
        "Ordenado por % de alta exposicao (decrescente).",
        "",
        "| " + " | ".join(name for name, _ in cols) + " |",
        "|" + "|".join(["---"] * len(cols)) + "|",
    ]
    for _, row in df.iterrows():
        cells: list[str] = []
        for _name, col in cols:
            v = row[col]
            if col == "sigla_uf":
                cells.append(str(v))
            elif col.endswith("_milhoes"):
                cells.append(f"{v:.2f}")
            else:
                cells.append(f"{v:.1f}")
        lines.append("| " + " | ".join(cells) + " |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    print(f"[1/4] Carregando e agregando dados de {DATA_INPUT.name}...")
    df_agg = load_and_aggregate()
    print(f"    -> {len(df_agg)} UFs. Total: {df_agg['vol_total_milhoes'].sum():.1f}M ocupados classificaveis.")

    print("[2/4] Carregando geometrias dos estados via geobr...")
    gdf = load_geometries(df_agg)
    print(f"    -> {len(gdf)} estados merged.")

    print("[3/4] Gerando mapas individuais e paineis 1x3...")
    for scale in ("continuo", "quantil"):
        for group in GRUPOS:
            out = DIR_FIGURES / f"fig_03_mapa_uf_{group}_{scale}.png"
            plot_mapa_uf(gdf, group, scale, out)
            print(f"    [{scale}/{group}] -> {out.name}")
        out_panel = DIR_FIGURES / f"fig_03_painel_uf_decomposicao_{scale}.png"
        plot_panel_1x3(gdf, scale, out_panel)
        print(f"    [{scale}/painel] -> {out_panel.name}")

    print("[4/4] Exportando tabela de apoio...")
    out_tab = DIR_TABLES / "tab_decomposicao_uf_exposicao.md"
    export_table(df_agg, out_tab)
    print(f"    -> {out_tab.name}")

    print("\nTop 5 UFs por % alta exposicao:")
    print(df_agg.nlargest(5, "pct_alta")[["sigla_uf", "vol_alta_milhoes", "pct_alta"]].to_string(index=False))

    print("\nFeito.")


if __name__ == "__main__":
    main()
