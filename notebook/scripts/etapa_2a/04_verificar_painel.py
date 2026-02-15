"""
Script 04: Verificar painel agregado (CHECKPOINT)
Entrada: data/processed/painel_caged_mensal.parquet
Saída:   (prints de verificação — nenhum arquivo)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def main():
    print("=" * 60)
    print("CHECKPOINT — Painel Ocupação × Mês")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_MENSAL_FILE)
    print(f"Carregado: {len(painel):,} linhas")

    # ── Dimensões ──
    n_ocup = painel['cbo_4d'].nunique()
    n_periodos = painel['periodo'].nunique()
    print(f"\n--- Dimensões ---")
    print(f"  Ocupações CBO 4d: {n_ocup}")
    print(f"  Períodos: {n_periodos}")
    print(f"  Painel teórico (balanceado): {n_ocup * n_periodos:,}")
    print(f"  Painel real: {len(painel):,}")
    print(f"  Balanceamento: {len(painel) / (n_ocup * n_periodos):.1%}")

    # ── Ocupações com poucos meses ──
    ocup_meses = painel.groupby('cbo_4d')['periodo'].nunique()
    print(f"\n--- Meses por ocupação ---")
    print(f"  Min: {ocup_meses.min()}, Max: {ocup_meses.max()}, Média: {ocup_meses.mean():.1f}")
    print(f"  Com < 12 meses: {(ocup_meses < 12).sum()}")
    print(f"  Com todos os {n_periodos} meses: {(ocup_meses == n_periodos).sum()}")

    # ── Estatísticas descritivas ──
    print(f"\n--- Estatísticas descritivas ---")
    cols_stats = ['admissoes', 'desligamentos', 'saldo', 'salario_medio_adm']
    cols_disponíveis = [c for c in cols_stats if c in painel.columns]
    print(painel[cols_disponíveis].describe().round(2))

    # ── Série temporal ──
    ts = painel.groupby('periodo_num').agg(
        total_admissoes=('admissoes', 'sum'),
        total_desligamentos=('desligamentos', 'sum'),
        salario_medio=('salario_medio_adm', 'mean'),
    ).reset_index()

    print(f"\n--- Série temporal (primeiros e últimos 3 meses) ---")
    print(ts.head(3).to_string(index=False))
    print("...")
    print(ts.tail(3).to_string(index=False))

    # ── Verificação pré/pós ──
    n_pre = painel[painel['post'] == 0]['periodo'].nunique()
    n_pos = painel[painel['post'] == 1]['periodo'].nunique()
    print(f"\n--- Pré/Pós tratamento ---")
    print(f"  Meses pré:  {n_pre}")
    print(f"  Meses pós:  {n_pos}")

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
