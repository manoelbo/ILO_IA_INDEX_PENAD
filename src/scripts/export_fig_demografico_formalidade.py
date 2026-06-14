"""
Figura individual: formalidade (Formal vs Informal) x exposicao a IA generativa.

Mesmo padrao visual das figuras demograficas (fig_04a..04e): barras
horizontais 100% empilhadas com decomposicao em tres grupos de exposicao
(Baixa = Not Exp + Min Exp; Moderada = G1+G2; Alta = G3+G4), anotacao dual
com % no segmento (>=2,5%) e volume total entre colchetes.

Definicao de formalidade (campo `formal` do PNAD-ILO merged):
  - Formal (1): empregado com carteira (posicao_ocupacao=1), domestico com
    carteira (3), militar/estatutario (5).
  - Informal (0): empregado sem carteira (2), domestico sem carteira (4),
    empregador sem CNPJ (6), conta-propria com (7) ou sem (8) CNPJ,
    sem registro / outro (9), auxiliar familiar (10).

Saida:
  - outputs/figures/etapa_1b/fig_04f_demografico_formalidade.png

Uso:
  python src/scripts/export_fig_demografico_formalidade.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from export_fig_demograficos_exposicao_3grupos import (  # noqa: E402
    GRADIENT_TO_GROUP,
    aggregate_dimension,
    plot_dimension_standalone,
)

DATA_INPUT = ROOT / "data" / "output" / "pnad_ilo_merged.csv"
DIR_FIGURES = ROOT / "outputs" / "figures" / "etapa_1b"

DIMENSION = {
    "label": "FORMALIDADE",
    "col": "formalidade",
    "order": ["Formal", "Informal"],
    "slug": "04f_demografico_formalidade",
    "title_individual": "Exposição à IA generativa por situação de formalidade",
    "subtitle_individual": (
        "Decomposição da força de trabalho ocupada por formalidade — Brasil 3T/2025"
    ),
}


def load_dataframe() -> pd.DataFrame:
    df = pd.read_csv(DATA_INPUT)
    df = df[df["exposure_gradient"].ne("Sem classificação")].copy()
    df["grupo3"] = df["exposure_gradient"].map(GRADIENT_TO_GROUP)
    if df["grupo3"].isna().any():
        raise ValueError("Mapeamento de gradiente -> grupo falhou.")
    fmap = {1: "Formal", 0: "Informal", True: "Formal", False: "Informal"}
    df["formalidade"] = df["formal"].map(fmap)
    if df["formalidade"].isna().any():
        n_na = df["formalidade"].isna().sum()
        print(f"[aviso] {n_na} linhas com formalidade indefinida (descartadas).")
        df = df[df["formalidade"].notna()].copy()
    return df


def main() -> None:
    print(f"[1/3] Carregando {DATA_INPUT.name}...")
    df = load_dataframe()
    print(f"    -> {df['peso'].sum()/1e6:.1f}M ocupados classificáveis com formalidade.")

    print("[2/3] Agregando dimensão de formalidade...")
    df_dim = aggregate_dimension(df, DIMENSION["col"], DIMENSION["order"])
    print(df_dim.to_string(index=False))

    print("[3/3] Renderizando figura individual...")
    out_path = DIR_FIGURES / f"fig_{DIMENSION['slug']}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plot_dimension_standalone(
        df_dim=df_dim,
        label_dim=DIMENSION["label"],
        title=DIMENSION["title_individual"],
        subtitle=DIMENSION["subtitle_individual"],
        out_path=out_path,
    )
    print(f"    -> {out_path.relative_to(ROOT)}")
    print("\nFeito.")


if __name__ == "__main__":
    main()
