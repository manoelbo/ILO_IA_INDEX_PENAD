"""
Script 05: Merge final e criação da base consolidada
Entrada: Dados do crosswalk (scripts 03 + 04)
Saída: data/output/pnad_ilo_merged.csv
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from src.utils.weighted_stats import weighted_mean, weighted_qcut

# Importar crosswalk
import importlib.util
spec = importlib.util.spec_from_file_location("crosswalk", Path(__file__).parent / "04_crosswalk.py")
crosswalk_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crosswalk_module)
run_crosswalk = crosswalk_module.run_crosswalk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '05_merge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def add_weighted_quintiles(df):
    """Adiciona quintis e decis de exposição ponderados por peso amostral.

    Usa weighted_qcut para que cada faixa represente ~20% (quintis)
    ou ~10% (decis) da POPULAÇÃO, não da amostra.
    """

    mask_valid = df['exposure_score'].notna()

    df.loc[mask_valid, 'quintil_exposure'] = weighted_qcut(
        df.loc[mask_valid, 'exposure_score'],
        df.loc[mask_valid, 'peso'],
        q=5,
        labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)'],
    )

    df.loc[mask_valid, 'decil_exposure'] = weighted_qcut(
        df.loc[mask_valid, 'exposure_score'],
        df.loc[mask_valid, 'peso'],
        q=10,
        labels=[f'D{i}' for i in range(1, 11)],
    )

    # Verificar distribuição populacional dos quintis
    logger.info("\nPopulação por quintil de exposição (deve ser ~20% cada):")
    for q, peso in df.groupby('quintil_exposure')['peso'].sum().items():
        pct = peso / df.loc[mask_valid, 'peso'].sum() * 100
        logger.info(f"  {q}: {peso/1e6:.1f} milhões ({pct:.1f}%)")

    return df

def add_sector_aggregation(df):
    """Agrega setores CNAE Domiciliar 2.0 (Seções A-T, IBGE) e flag de setor crítico IA."""

    df['cnae_2d'] = df['grupamento_atividade'].astype(str).str[:2]
    df['setor_agregado'] = df['cnae_2d'].map(CNAE_SETOR_MAP).fillna('Outros Serviços')

    # Flag de setores críticos para IA
    df['setor_critico_ia'] = df['setor_agregado'].isin(SETORES_CRITICOS_IA).astype(int)

    logger.info(f"\nSetores: {df['setor_agregado'].nunique()} categorias")
    logger.info(f"Trabalhadores em setores críticos IA: "
                f"{df.loc[df['setor_critico_ia']==1, 'peso'].sum()/1e6:.1f} milhões")

    logger.info("\nDistribuição por setor:")
    for setor, peso in df.groupby('setor_agregado')['peso'].sum().sort_values(ascending=False).items():
        flag = " *" if setor in SETORES_CRITICOS_IA else ""
        logger.info(f"  {setor}: {peso/1e6:.1f} milhões{flag}")

    return df

def merge_and_finalize():
    """Executa merge final e salva base consolidada"""

    logger.info("=== MERGE FINAL ===\n")

    # Executar crosswalk
    df, coverage = run_crosswalk()

    # Checkpoint de qualidade do merge
    n_com_score = df['exposure_score'].notna().sum()
    n_sem_score = df['exposure_score'].isna().sum()
    pct_pop_perdida = df.loc[df['exposure_score'].isna(), 'peso'].sum() / df['peso'].sum() * 100

    logger.info("=== CHECKPOINT - Qualidade do Merge ===")
    logger.info(f"Observações totais:     {len(df):,}")
    logger.info(f"Com score de exposição: {n_com_score:,}")
    logger.info(f"Sem score (NaN):        {n_sem_score:,}")
    logger.info(f"% pop. sem score:       {pct_pop_perdida:.1f}%")

    # Distribuição por gradiente ILO (potential25)
    logger.info("\nDistribuição por gradiente ILO (potential25):")
    for grad, peso in df.groupby('exposure_gradient')['peso'].sum().sort_values(ascending=False).items():
        logger.info(f"  {grad}: {peso/1e6:.1f} milhões")

    # Quintis e decis ponderados
    df = add_weighted_quintiles(df)

    # Agregação setorial
    df = add_sector_aggregation(df)

    # Colunas finais
    cols_output = [
        'ano', 'trimestre', 'sigla_uf', 'regiao',
        'sexo', 'sexo_texto', 'idade', 'faixa_etaria',
        'raca_cor', 'raca_agregada', 'nivel_instrucao',
        'cod_ocupacao', 'grande_grupo',
        'grupamento_atividade', 'setor_agregado', 'setor_critico_ia',
        'posicao_ocupacao', 'formal', 'tem_renda',
        'rendimento_habitual', 'rendimento_winsor', 'rendimento_efetivo',
        'horas_habituais', 'horas_efetivas',
        'faixa_renda_sm',
        'peso',
        'exposure_score', 'exposure_gradient', 'match_level',
        'quintil_exposure', 'decil_exposure',
    ]

    df_final = df[[c for c in cols_output if c in df.columns]]

    # Salvar
    output_path = DATA_OUTPUT / "pnad_ilo_merged.csv"
    df_final.to_csv(output_path, index=False)

    # Resumo final
    logger.info(f"\n{'=' * 60}")
    logger.info("BASE FINAL CONSOLIDADA")
    logger.info(f"{'=' * 60}")
    logger.info(f"Observações:       {len(df_final):,}")
    logger.info(f"Com score:         {df_final['exposure_score'].notna().sum():,}")
    logger.info(f"Cobertura:         {df_final['exposure_score'].notna().mean():.1%}")
    logger.info(f"Colunas:           {df_final.shape[1]}")
    logger.info(f"População total:   {df_final['peso'].sum()/1e6:.1f} milhões")
    logger.info(f"  com renda:       {df_final.loc[df_final['tem_renda']==1, 'peso'].sum()/1e6:.1f} milhões")
    logger.info(f"  sem renda:       {df_final.loc[df_final['tem_renda']==0, 'peso'].sum()/1e6:.1f} milhões")
    logger.info(f"Setores:           {df_final['setor_agregado'].nunique()} categorias")
    logger.info(f"Setor crítico IA:  {df_final['setor_critico_ia'].sum():,} obs")
    logger.info(f"Salvo em:          {output_path}")
    logger.info(f"Tamanho em disco:  {output_path.stat().st_size / 1e6:.1f} MB")

    return df_final

if __name__ == "__main__":
    df = merge_and_finalize()
    print("\nMerge concluído com sucesso!")
