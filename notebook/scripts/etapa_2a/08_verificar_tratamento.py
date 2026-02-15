"""
Script 08: Verificar definição de tratamento (CHECKPOINT)
Entrada: data/processed/painel_caged_tratamento.parquet
Saída:   (prints de verificação — nenhum arquivo)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def main():
    print("=" * 60)
    print("CHECKPOINT — Definição de Tratamento")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_TRATAMENTO_FILE)
    print(f"Carregado: {len(painel):,} linhas")

    # ── Top 10 ocupações mais expostas ──
    print(f"\n--- Top 10 ocupações MAIS expostas ---")
    top10 = painel.groupby('cbo_4d').agg(
        exposure=('exposure_score', 'first'),
        admissoes_total=('admissoes', 'sum'),
    ).nlargest(10, 'exposure')
    for cbo, row in top10.iterrows():
        print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}")

    # ── Bottom 10 ocupações menos expostas ──
    print(f"\n--- 10 ocupações MENOS expostas ---")
    bot10 = painel.groupby('cbo_4d').agg(
        exposure=('exposure_score', 'first'),
        admissoes_total=('admissoes', 'sum'),
    ).nsmallest(10, 'exposure')
    for cbo, row in bot10.iterrows():
        print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}")

    # ── Distribuição por quintil ──
    print(f"\n--- Estatísticas por quintil de exposição ---")
    for q in ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']:
        sub = painel[painel['quintil_exp'] == q]
        if len(sub) > 0:
            print(f"  {q}: n={len(sub):,}, "
                  f"exposure={sub['exposure_score'].mean():.3f}, "
                  f"adm_mean={sub['admissoes'].mean():.0f}, "
                  f"sal_medio={sub['salario_medio_adm'].mean():,.0f}")

    # ── Concordância 2d vs 4d ──
    mask_valid = painel['exposure_score_4d'].notna()
    if mask_valid.any():
        concordancia = (painel.loc[mask_valid, 'alta_exp'] ==
                        painel.loc[mask_valid, 'alta_exp_4d']).mean()
        print(f"\n--- Concordância 2d vs 4d: {concordancia:.1%} ---")

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
