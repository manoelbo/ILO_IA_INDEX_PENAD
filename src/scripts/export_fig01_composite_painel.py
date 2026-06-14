"""
Monta um unico PNG (composito) a partir dos tres arquivos ja exportados.

Linha superior: fig_01_histograma_kde_exposicao.png | fig_01_var_hist_empilhado_grande_grupo.png
Linha inferior: fig_01_populacao_por_gradiente_ilo.png (largura = soma das duas de cima + espacamento)

Nao redimensiona as duas de cima entre si: elas devem ter o mesmo tamanho em pixels
(export com bbox_inches=None + FIG01_TOP_* nos scripts de geracao). Se ainda diferirem,
a direita e escalada uma vez para coincidir com a esquerda.

Uso:
  python src/scripts/export_fig01_composite_painel.py

Saida: outputs/figures/etapa_1b/fig_01_composite_exposicao_painel.png
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent.parent.parent
FIG_DIR = ROOT / "outputs" / "figures" / "etapa_1b"
OUT = FIG_DIR / "fig_01_composite_exposicao_painel.png"

TOP_LEFT = FIG_DIR / "fig_01_histograma_kde_exposicao.png"
TOP_RIGHT = FIG_DIR / "fig_01_var_hist_empilhado_grande_grupo.png"
BOTTOM = FIG_DIR / "fig_01_populacao_por_gradiente_ilo.png"

GAP_COL = 24
GAP_ROW = 32


def main() -> None:
    for p in (TOP_LEFT, TOP_RIGHT, BOTTOM):
        if not p.exists():
            raise FileNotFoundError(f"Gere antes a figura: {p}")

    im_l = Image.open(TOP_LEFT).convert("RGB")
    im_r = Image.open(TOP_RIGHT).convert("RGB")

    if im_l.size != im_r.size:
        im_r = im_r.resize(im_l.size, Image.Resampling.LANCZOS)

    w_top, h_top = im_l.size
    full_w = w_top * 2 + GAP_COL

    im_bot = Image.open(BOTTOM).convert("RGB")
    if im_bot.width != full_w:
        nh = max(1, int(round(im_bot.height * full_w / im_bot.width)))
        im_bot = im_bot.resize((full_w, nh), Image.Resampling.LANCZOS)

    total_h = h_top + GAP_ROW + im_bot.height
    canvas = Image.new("RGB", (full_w, total_h), (255, 255, 255))
    canvas.paste(im_l, (0, 0))
    canvas.paste(im_r, (w_top + GAP_COL, 0))
    canvas.paste(im_bot, (0, h_top + GAP_ROW))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, format="PNG", optimize=True)
    print(f"Salvo: {OUT} ({full_w}x{total_h}px)")
    print(f"  Topo: {w_top}x{h_top} + {w_top}x{h_top} (gap {GAP_COL}px)")


if __name__ == "__main__":
    main()
