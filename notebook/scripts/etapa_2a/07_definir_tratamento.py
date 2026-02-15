"""
Script 07: Definir variáveis de tratamento para DiD
Entrada: data/processed/painel_caged_crosswalk.parquet
Saída:   data/processed/painel_caged_tratamento.parquet
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def main():
    print("=" * 60)
    print("ETAPA 2a.5a — Definição de Tratamento")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_CROSSWALK_FILE)
    print(f"Carregado: {len(painel):,} linhas")

    # ══════════════════════════════════════════════════════════════
    # PASSO 1: Thresholds sobre a distribuição de OCUPAÇÕES (2d)
    # ══════════════════════════════════════════════════════════════
    # Uma obs por CBO — cada ocupação tem peso igual
    ocup_scores_2d = painel.groupby('cbo_4d')['exposure_score_2d'].first().dropna()

    thresholds_2d = {
        'alta_exp_10':      ocup_scores_2d.quantile(0.90),
        'alta_exp':         ocup_scores_2d.quantile(0.80),  # PRINCIPAL
        'alta_exp_25':      ocup_scores_2d.quantile(0.75),
        'alta_exp_mediana':  ocup_scores_2d.quantile(0.50),
    }

    print(f"\nThresholds de exposição (2d, PRINCIPAL):")
    for name, val in thresholds_2d.items():
        n_above = (ocup_scores_2d >= val).sum()
        pct = n_above / len(ocup_scores_2d) * 100
        print(f"  {name}: {val:.4f} ({n_above} ocupações, {pct:.0f}%)")

    # ══════════════════════════════════════════════════════════════
    # PASSO 2: Dummies de tratamento 2d
    # ══════════════════════════════════════════════════════════════
    for name, threshold in thresholds_2d.items():
        painel[name] = (painel['exposure_score_2d'] >= threshold).astype(int)

    # Quintis (2d)
    painel['quintil_exp'] = pd.qcut(
        painel['exposure_score_2d'].rank(method='first'),
        q=5,
        labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
    )

    # ══════════════════════════════════════════════════════════════
    # PASSO 3: Dummies 4d (ROBUSTEZ)
    # ══════════════════════════════════════════════════════════════
    ocup_scores_4d = painel.groupby('cbo_4d')['exposure_score_4d'].first().dropna()
    if len(ocup_scores_4d) > 0:
        threshold_4d_80 = ocup_scores_4d.quantile(0.80)
        painel['alta_exp_4d'] = (painel['exposure_score_4d'] >= threshold_4d_80).astype(int)
        print(f"\nThreshold 4d (p80): {threshold_4d_80:.4f}")
        print(f"  ({(ocup_scores_4d >= threshold_4d_80).sum()} ocupações acima)")
    else:
        painel['alta_exp_4d'] = 0
        print(f"\nAVISO: Sem scores 4d disponíveis.")

    # ══════════════════════════════════════════════════════════════
    # PASSO 4: Interações DiD
    # ══════════════════════════════════════════════════════════════
    painel['did'] = painel['post'] * painel['alta_exp']
    painel['did_4d'] = painel['post'] * painel['alta_exp_4d']

    # ══════════════════════════════════════════════════════════════
    # RESUMO
    # ══════════════════════════════════════════════════════════════
    print(f"\n--- Distribuição de tratamento ---")
    print(f"  Alta exp 2d (top 20%): {painel['alta_exp'].mean():.1%} das obs")
    print(f"  Alta exp 4d (top 20%): {painel['alta_exp_4d'].mean():.1%} das obs")
    print(f"  Períodos pré:  {painel[painel['post']==0].shape[0]:,}")
    print(f"  Períodos pós:  {painel[painel['post']==1].shape[0]:,}")

    # Concordância 2d vs 4d
    mask_valid = painel['exposure_score_4d'].notna()
    if mask_valid.any():
        concordancia = (painel.loc[mask_valid, 'alta_exp'] ==
                        painel.loc[mask_valid, 'alta_exp_4d']).mean()
        print(f"  Concordância 2d vs 4d: {concordancia:.1%}")

    # Tabela de contingência
    ct = pd.crosstab(
        painel['post'].map({0: 'Pré', 1: 'Pós'}),
        painel['alta_exp'].map({0: 'Controle', 1: 'Tratamento'}),
        margins=True
    )
    print(f"\nTabela de contingência (2d, principal):")
    print(ct)

    # Salvar
    painel.to_parquet(PAINEL_TRATAMENTO_FILE, index=False)
    size_mb = PAINEL_TRATAMENTO_FILE.stat().st_size / 1e6
    print(f"\nSalvo: {PAINEL_TRATAMENTO_FILE.name} ({size_mb:.1f} MB)")

    return painel


if __name__ == "__main__":
    painel = main()
