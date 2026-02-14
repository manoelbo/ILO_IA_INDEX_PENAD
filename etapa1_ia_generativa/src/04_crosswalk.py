"""
Script 04: Crosswalk hierárquico COD → ISCO-08
Entrada: data/processed/pnad_clean.csv, data/processed/ilo_exposure_clean.csv
Saída: Log com estatísticas de match por nível
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '04_crosswalk.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_ilo_aggregations(df_ilo):
    """Cria agregações ILO em diferentes níveis hierárquicos"""

    ilo_4d = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()
    ilo_3d = df_ilo.groupby(df_ilo['isco_08_str'].str[:3])['exposure_score'].mean().to_dict()
    ilo_2d = df_ilo.groupby(df_ilo['isco_08_str'].str[:2])['exposure_score'].mean().to_dict()
    ilo_1d = df_ilo.groupby(df_ilo['isco_08_str'].str[:1])['exposure_score'].mean().to_dict()

    # Lookup do gradiente oficial ILO (potential25) — apenas para match 4-digit
    ilo_gradient_4d = df_ilo.groupby('isco_08_str')['exposure_gradient'].first().to_dict()

    logger.info(f"Códigos ILO 4-digit: {len(ilo_4d)}")
    logger.info(f"Códigos ILO 3-digit: {len(ilo_3d)}")
    logger.info(f"Códigos ILO 2-digit: {len(ilo_2d)}")
    logger.info(f"Códigos ILO 1-digit: {len(ilo_1d)}")

    return ilo_4d, ilo_3d, ilo_2d, ilo_1d, ilo_gradient_4d

def hierarchical_crosswalk(df_pnad, ilo_4d, ilo_3d, ilo_2d, ilo_1d, ilo_gradient_4d):
    """Aplica crosswalk hierárquico em 4 níveis"""

    logger.info("\n=== CROSSWALK HIERÁRQUICO ===")

    # Inicializar colunas
    df_pnad['exposure_score'] = np.nan
    df_pnad['exposure_gradient'] = None
    df_pnad['match_level'] = None

    # Nível 1: 4-digit
    mask_4d = df_pnad['cod_ocupacao'].isin(ilo_4d.keys())
    df_pnad.loc[mask_4d, 'exposure_score'] = df_pnad.loc[mask_4d, 'cod_ocupacao'].map(ilo_4d)
    df_pnad.loc[mask_4d, 'exposure_gradient'] = df_pnad.loc[mask_4d, 'cod_ocupacao'].map(ilo_gradient_4d)
    df_pnad.loc[mask_4d, 'match_level'] = '4-digit'
    logger.info(f"Match 4-digit: {mask_4d.sum():,} ({mask_4d.mean():.1%})")

    # Nível 2: 3-digit
    mask_missing = df_pnad['exposure_score'].isna()
    cod_3d = df_pnad.loc[mask_missing, 'cod_ocupacao'].str[:3]
    mask_3d = cod_3d.isin(ilo_3d.keys())
    idx_3d = mask_missing[mask_missing].index[mask_3d.values]
    df_pnad.loc[idx_3d, 'exposure_score'] = cod_3d[mask_3d].map(ilo_3d).values
    df_pnad.loc[idx_3d, 'exposure_gradient'] = 'Sem classificação'
    df_pnad.loc[idx_3d, 'match_level'] = '3-digit'
    logger.info(f"Match 3-digit: {len(idx_3d):,} ({len(idx_3d)/len(df_pnad):.1%})")

    # Nível 3: 2-digit
    mask_missing = df_pnad['exposure_score'].isna()
    cod_2d = df_pnad.loc[mask_missing, 'cod_ocupacao'].str[:2]
    mask_2d = cod_2d.isin(ilo_2d.keys())
    idx_2d = mask_missing[mask_missing].index[mask_2d.values]
    df_pnad.loc[idx_2d, 'exposure_score'] = cod_2d[mask_2d].map(ilo_2d).values
    df_pnad.loc[idx_2d, 'exposure_gradient'] = 'Sem classificação'
    df_pnad.loc[idx_2d, 'match_level'] = '2-digit'
    logger.info(f"Match 2-digit: {len(idx_2d):,} ({len(idx_2d)/len(df_pnad):.1%})")

    # Nível 4: 1-digit
    mask_missing = df_pnad['exposure_score'].isna()
    cod_1d = df_pnad.loc[mask_missing, 'cod_ocupacao'].str[:1]
    mask_1d = cod_1d.isin(ilo_1d.keys())
    idx_1d = mask_missing[mask_missing].index[mask_1d.values]
    df_pnad.loc[idx_1d, 'exposure_score'] = cod_1d[mask_1d].map(ilo_1d).values
    df_pnad.loc[idx_1d, 'exposure_gradient'] = 'Sem classificação'
    df_pnad.loc[idx_1d, 'match_level'] = '1-digit'
    logger.info(f"Match 1-digit: {len(idx_1d):,} ({len(idx_1d)/len(df_pnad):.1%})")

    # Sem match
    n_sem_match = df_pnad['exposure_score'].isna().sum()
    df_pnad.loc[df_pnad['exposure_score'].isna(), 'exposure_gradient'] = 'Sem classificação'
    logger.info(f"Sem match:     {n_sem_match:,} ({n_sem_match/len(df_pnad):.1%})")

    return df_pnad

def validate_crosswalk(df):
    """Valida resultados do crosswalk"""
    from src.utils.weighted_stats import weighted_mean

    logger.info("\n=== VALIDAÇÃO DO CROSSWALK ===")

    # Cobertura total
    coverage = df['exposure_score'].notna().mean()
    logger.info(f"Cobertura total: {coverage:.1%}")

    # Distribuição por nível
    logger.info("\nDistribuição por nível de match:")
    for level, count in df['match_level'].value_counts().items():
        pct = count / len(df) * 100
        logger.info(f"  {level}: {count:,} ({pct:.1f}%)")

    # Verificar concentração em match genérico
    n_generic = df['match_level'].isin(['1-digit', '2-digit']).sum()
    pct_generic = n_generic / len(df) * 100
    logger.info(f"\nMatch genérico (1-digit + 2-digit): {n_generic:,} ({pct_generic:.1f}%)")

    # Estatísticas de score
    logger.info("\nEstatísticas do score de exposição:")
    logger.info(f"  Média: {df['exposure_score'].mean():.3f}")
    logger.info(f"  Desvio-padrão: {df['exposure_score'].std():.3f}")
    logger.info(f"  Mínimo: {df['exposure_score'].min():.3f}")
    logger.info(f"  Máximo: {df['exposure_score'].max():.3f}")

    # Sanity check: exposição por grande grupo
    logger.info("\nExposição média por grande grupo (sanity check):")
    exp_grupos = df.groupby('grande_grupo').apply(
        lambda x: weighted_mean(x['exposure_score'].dropna(), x.loc[x['exposure_score'].notna(), 'peso'])
    ).sort_values(ascending=False)
    for grupo, score in exp_grupos.items():
        logger.info(f"  {grupo}: {score:.3f}")

    # Validação de sanidade
    logger.info("\nVALIDAÇÃO DE SANIDADE:")
    if 'Profissionais das ciências' in exp_grupos.index:
        val = exp_grupos['Profissionais das ciências']
        if val > 0.30:
            logger.info(f"  OK - Profissionais das ciências com exposição ALTA ({val:.3f})")
        else:
            logger.warning(f"  Profissionais das ciências com exposição BAIXA ({val:.3f}). Esperado > 0.30")

    if 'Ocupações elementares' in exp_grupos.index:
        val = exp_grupos['Ocupações elementares']
        if val < 0.20:
            logger.info(f"  OK - Ocupações elementares com exposição BAIXA ({val:.3f})")
        else:
            logger.warning(f"  Ocupações elementares com exposição ALTA ({val:.3f}). Esperado < 0.20")

    return coverage

def run_crosswalk():
    """Executa crosswalk completo"""

    # Carregar dados
    df_pnad = pd.read_csv(DATA_PROCESSED / "pnad_clean.csv")
    df_ilo = pd.read_csv(DATA_PROCESSED / "ilo_exposure_clean.csv")

    # Garantir que isco_08_str seja string
    df_ilo['isco_08_str'] = df_ilo['isco_08_str'].astype(str).str.zfill(4)

    # Garantir que cod_ocupacao seja string com 4 dígitos
    df_pnad['cod_ocupacao'] = df_pnad['cod_ocupacao'].astype(str).str.zfill(4)

    logger.info(f"PNAD: {len(df_pnad):,} observações")
    logger.info(f"ILO: {len(df_ilo):,} ocupações")

    # Criar agregações
    ilo_4d, ilo_3d, ilo_2d, ilo_1d, ilo_gradient_4d = create_ilo_aggregations(df_ilo)

    # Aplicar crosswalk
    df_result = hierarchical_crosswalk(df_pnad.copy(), ilo_4d, ilo_3d, ilo_2d, ilo_1d, ilo_gradient_4d)

    # Validar
    coverage = validate_crosswalk(df_result)

    return df_result, coverage

if __name__ == "__main__":
    df, coverage = run_crosswalk()
    print(f"\nCrosswalk concluído com {coverage:.1%} de cobertura")
    print(f"Log: {OUTPUTS_LOGS / '04_crosswalk.log'}")
