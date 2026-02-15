"""
Script 09: Enriquecer painel e salvar dataset analítico final
Entrada: data/processed/painel_caged_tratamento.parquet
Saída:   data/output/painel_caged_did_ready.parquet + .csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def periodo_num_to_months(pn):
    """Converter periodo_num (YYYYMM) para contagem absoluta de meses."""
    return (pn // 100) * 12 + (pn % 100)


def main():
    print("=" * 60)
    print("ETAPA 2a.6a+7 — Enriquecimento e Salvamento Final")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_TRATAMENTO_FILE)
    print(f"Carregado: {len(painel):,} linhas, {painel.shape[1]} colunas")

    # ══════════════════════════════════════════════════════════════
    # PASSO 1: Tempo relativo ao tratamento
    # ══════════════════════════════════════════════════════════════
    ref_periodo = ANO_TRATAMENTO * 100 + MES_TRATAMENTO
    painel['meses_abs'] = painel['periodo_num'].apply(periodo_num_to_months)
    ref_meses = periodo_num_to_months(ref_periodo)
    painel['tempo_relativo_meses'] = painel['meses_abs'] - ref_meses

    print(f"  Tempo relativo: [{painel['tempo_relativo_meses'].min()}, "
          f"{painel['tempo_relativo_meses'].max()}] meses")
    print(f"  Referência (t=0): {MES_TRATAMENTO}/{ANO_TRATAMENTO}")

    # ══════════════════════════════════════════════════════════════
    # PASSO 2: Tendência temporal e sazonalidade
    # ══════════════════════════════════════════════════════════════
    painel['trend'] = painel['meses_abs'] - painel['meses_abs'].min()
    painel['mes_do_ano'] = painel['mes'].astype(int)

    # ══════════════════════════════════════════════════════════════
    # PASSO 3: Normalização salarial (em salários mínimos)
    # ══════════════════════════════════════════════════════════════
    painel['sm_ano'] = painel['ano'].astype(int).map(SALARIO_MINIMO)
    painel['salario_sm'] = painel['salario_medio_adm'] / painel['sm_ano']
    painel['ln_salario_sm'] = np.log(painel['salario_sm'].clip(lower=0.1))

    # ══════════════════════════════════════════════════════════════
    # PASSO 4: Grande grupo ocupacional
    # ══════════════════════════════════════════════════════════════
    painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]
    painel['grande_grupo_nome'] = painel['grande_grupo_cbo'].map(GRANDES_GRUPOS_CBO)

    # ══════════════════════════════════════════════════════════════
    # PASSO 5: Selecionar colunas finais
    # ══════════════════════════════════════════════════════════════
    cols_finais = [
        # Identificação
        'cbo_4d', 'cbo_2d', 'ano', 'mes', 'periodo', 'periodo_num',
        # Outcomes
        'admissoes', 'desligamentos', 'saldo', 'n_movimentacoes',
        'ln_admissoes', 'ln_desligamentos',
        'salario_medio_adm', 'salario_mediano_adm', 'salario_medio_desl',
        'ln_salario_adm', 'salario_sm', 'ln_salario_sm',
        # Demografia das admissões
        'idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm',
        # Exposição IA — DUAL
        'exposure_score_2d',   # PRINCIPAL
        'exposure_score_4d',   # ROBUSTEZ
        # Tratamento — DUAL
        'alta_exp',            # Top 20% score 2d (PRINCIPAL)
        'alta_exp_10', 'alta_exp_25', 'alta_exp_mediana', 'quintil_exp',
        'alta_exp_4d',         # Top 20% score 4d (ROBUSTEZ)
        # Temporal
        'post', 'did', 'did_4d', 'tempo_relativo_meses', 'trend', 'mes_do_ano',
        # Classificação
        'grande_grupo_cbo', 'grande_grupo_nome',
    ]

    cols_existentes = [c for c in cols_finais if c in painel.columns]
    cols_faltantes = [c for c in cols_finais if c not in painel.columns]
    if cols_faltantes:
        print(f"\n  AVISO: Colunas não encontradas: {cols_faltantes}")

    painel_final = painel[cols_existentes].copy()

    # ══════════════════════════════════════════════════════════════
    # PASSO 6: Remover ocupações sem score principal (2d)
    # ══════════════════════════════════════════════════════════════
    n_antes = len(painel_final)
    painel_final = painel_final[painel_final['exposure_score_2d'].notna()]
    n_depois = len(painel_final)
    if n_antes > n_depois:
        print(f"  Removidas {n_antes - n_depois:,} linhas sem exposure_score_2d "
              f"({(n_antes - n_depois) / n_antes:.1%})")

    # ══════════════════════════════════════════════════════════════
    # PASSO 7: Salvar
    # ══════════════════════════════════════════════════════════════
    painel_final.to_parquet(PAINEL_FINAL_PARQUET, index=False)
    painel_final.to_csv(PAINEL_FINAL_CSV, index=False)

    # ══════════════════════════════════════════════════════════════
    # RESUMO FINAL
    # ══════════════════════════════════════════════════════════════
    n_com_4d = painel_final['exposure_score_4d'].notna().sum()

    print(f"\n{'=' * 60}")
    print("DATASET ANALÍTICO FINAL — ETAPA 2a")
    print(f"{'=' * 60}")
    print(f"  Observações:        {len(painel_final):,}")
    print(f"  Ocupações (CBO 4d): {painel_final['cbo_4d'].nunique()}")
    print(f"  Períodos:           {painel_final['periodo'].nunique()} meses")
    print(f"    Pré-tratamento:   {painel_final[painel_final['post']==0]['periodo'].nunique()}")
    print(f"    Pós-tratamento:   {painel_final[painel_final['post']==1]['periodo'].nunique()}")
    print(f"  Cobertura 2d:       {painel_final['exposure_score_2d'].notna().mean():.1%}")
    print(f"  Cobertura 4d:       {n_com_4d / len(painel_final):.1%}")
    print(f"  Tratamento 2d:      {painel_final['alta_exp'].mean():.1%} das obs")
    print(f"  Tratamento 4d:      {painel_final['alta_exp_4d'].mean():.1%} das obs")
    print(f"  Colunas:            {painel_final.shape[1]}")
    print(f"\n  Salvo em:")
    print(f"    {PAINEL_FINAL_PARQUET}")
    print(f"    {PAINEL_FINAL_CSV}")
    pq_mb = PAINEL_FINAL_PARQUET.stat().st_size / 1e6
    csv_mb = PAINEL_FINAL_CSV.stat().st_size / 1e6
    print(f"    Tamanho: {pq_mb:.1f} MB (parquet), {csv_mb:.1f} MB (csv)")

    print(f"\n  Info:")
    painel_final.info()

    return painel_final


if __name__ == "__main__":
    painel = main()
