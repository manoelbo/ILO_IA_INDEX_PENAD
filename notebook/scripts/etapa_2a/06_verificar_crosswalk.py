"""
Script 06: Verificar crosswalk CBO → ISCO-08 (CHECKPOINT)
Entrada: data/processed/painel_caged_crosswalk.parquet
Saída:   (prints de verificação — nenhum arquivo)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def main():
    print("=" * 60)
    print("CHECKPOINT — Crosswalk CBO → ISCO-08 (Dual)")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_CROSSWALK_FILE)
    print(f"Carregado: {len(painel):,} linhas")

    # ── 1. Cobertura ──
    coverage_2d = painel['exposure_score_2d'].notna().mean()
    coverage_4d = painel['exposure_score_4d'].notna().mean()

    print(f"\n--- Cobertura ---")
    print(f"  2 dígitos (PRINCIPAL): {coverage_2d:.1%}")
    print(f"  4 dígitos (ROBUSTEZ):  {coverage_4d:.1%}")

    if coverage_2d < 0.95:
        print(f"  ALERTA: Cobertura 2d abaixo de 95%!")
    if coverage_4d < 0.80:
        print(f"  AVISO: Cobertura 4d abaixo de 80%.")

    # ── 2. Ocupações sem match ──
    sem_match_2d = painel[painel['exposure_score_2d'].isna()]['cbo_4d'].unique()
    sem_match_4d = painel[painel['exposure_score_4d'].isna()]['cbo_4d'].unique()

    print(f"\n--- Ocupações sem match ---")
    print(f"  Sem match 2d: {len(sem_match_2d)} CBOs")
    print(f"  Sem match 4d: {len(sem_match_4d)} CBOs")

    if len(sem_match_2d) > 0:
        print(f"  CBOs sem match 2d (primeiros 10):")
        for cbo in sem_match_2d[:10]:
            n = (painel['cbo_4d'] == cbo).sum()
            print(f"    CBO {cbo}: {n} linhas")

    # ── 3. Estatísticas dos scores ──
    print(f"\n--- Estatísticas dos scores ---")
    print(f"\nexposure_score_2d (PRINCIPAL):")
    print(painel['exposure_score_2d'].describe().round(4))
    print(f"\nexposure_score_4d (ROBUSTEZ):")
    print(painel['exposure_score_4d'].describe().round(4))

    # ── 4. Correlação 2d vs 4d ──
    mask_both = painel['exposure_score_2d'].notna() & painel['exposure_score_4d'].notna()
    if mask_both.any():
        corr = painel.loc[mask_both, 'exposure_score_2d'].corr(
            painel.loc[mask_both, 'exposure_score_4d']
        )
        print(f"\n--- Correlação 2d vs 4d ---")
        print(f"  Pearson: {corr:.4f}")
        if corr > 0.8:
            print(f"  Alta correlação — bom sinal de consistência.")
        else:
            print(f"  Correlação moderada — as especificações podem divergir.")

    # ── 5. Sanity check por grande grupo CBO ──
    painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]

    print(f"\n--- Exposição por grande grupo CBO ---")
    print(f"{'Grande Grupo':<40} {'Score 2d':>10} {'Score 4d':>10}")
    print("-" * 62)
    for gg, nome in sorted(GRANDES_GRUPOS_CBO.items()):
        mask = painel['grande_grupo_cbo'] == gg
        if mask.any():
            s2d = painel.loc[mask, 'exposure_score_2d'].mean()
            s4d = painel.loc[mask, 'exposure_score_4d'].mean()
            s4d_str = f"{s4d:.3f}" if not np.isnan(s4d) else "N/A"
            flag = " (!)" if not np.isnan(s4d) and abs(s2d - s4d) > 0.1 else ""
            print(f"  {nome:<38} {s2d:>10.3f} {s4d_str:>10}{flag}")

    print(f"\n  (!) = diferença > 0.1 entre 2d e 4d")

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
