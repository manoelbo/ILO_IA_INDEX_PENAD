"""
Script 01: Processa dados Anthropic para criar índice por ocupação SOC
Entrada: EconomicIndex/release_2025_03_27/*.csv
Saída: data/processed/anthropic_index_soc6.csv
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar as configurações
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from src.utils.aggregation import (
    normalize_task_name, 
    extract_soc_6digit,
    calculate_automation_score,
    aggregate_to_occupation
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '01_process_anthropic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_anthropic_tasks() -> pd.DataFrame:
    """Carrega dados de automação/aumentação por tarefa."""
    logger.info(f"Carregando: {ANTHROPIC_TASKS_FILE}")
    
    df = pd.read_csv(ANTHROPIC_TASKS_FILE)
    logger.info(f"  Tarefas carregadas: {len(df):,}")
    
    # Verificar colunas
    expected_cols = ['task_name'] + AUTOMATION_COLS + AUGMENTATION_COLS + ['filtered']
    for col in expected_cols:
        if col not in df.columns:
            logger.warning(f"  Coluna ausente: {col}")
    
    return df


def load_onet_statements() -> pd.DataFrame:
    """Carrega mapeamento tarefa → ocupação O*NET."""
    logger.info(f"Carregando: {ONET_STATEMENTS_FILE}")
    
    df = pd.read_csv(ONET_STATEMENTS_FILE)
    logger.info(f"  Registros tarefa-ocupação: {len(df):,}")
    logger.info(f"  Ocupações únicas: {df['O*NET-SOC Code'].nunique()}")
    
    # Normalizar nome da tarefa para matching
    df['task_normalized'] = df['Task'].apply(normalize_task_name)
    
    # Extrair código SOC 6 dígitos
    df['soc_code'] = df['O*NET-SOC Code'].apply(extract_soc_6digit)
    
    return df


def merge_datasets(df_anthropic: pd.DataFrame, 
                   df_onet: pd.DataFrame) -> pd.DataFrame:
    """Faz join entre tarefas Anthropic e O*NET."""
    logger.info("\n=== MERGE DATASETS ===")
    
    # Merge por nome da tarefa normalizado
    df_merged = df_onet.merge(
        df_anthropic,
        left_on='task_normalized',
        right_on='task_name',
        how='left'
    )
    
    # Estatísticas de match
    n_total = len(df_onet)
    n_matched = df_merged['task_name'].notna().sum()
    coverage = n_matched / n_total * 100
    
    logger.info(f"  Total de registros O*NET: {n_total:,}")
    logger.info(f"  Registros com match: {n_matched:,} ({coverage:.1f}%)")
    logger.info(f"  Registros sem match: {n_total - n_matched:,}")
    
    return df_merged


def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula scores de automação e aumentação."""
    logger.info("\n=== CALCULANDO SCORES ===")
    
    # Calcular scores para cada linha
    scores = df.apply(
        lambda row: calculate_automation_score(row, AUTOMATION_COLS, AUGMENTATION_COLS),
        axis=1
    )
    scores_df = pd.DataFrame(scores.tolist())
    
    # Adicionar ao dataframe
    for col in scores_df.columns:
        df[col] = scores_df[col]
    
    # Estatísticas
    mask_valid = df['automation_score'].notna()
    logger.info(f"  Tarefas com scores válidos: {mask_valid.sum():,}")
    logger.info(f"  Automação média: {df.loc[mask_valid, 'automation_score'].mean():.3f}")
    logger.info(f"  Aumentação média: {df.loc[mask_valid, 'augmentation_score'].mean():.3f}")
    
    return df


def aggregate_by_occupation(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega scores para nível de ocupação SOC 6-dígitos."""
    logger.info("\n=== AGREGANDO POR OCUPAÇÃO ===")
    
    # Filtrar apenas registros com match
    df_matched = df[df['task_name'].notna()].copy()
    
    # Renomear para agregação
    df_matched['soc_title'] = df_matched['Title']
    
    # Agregar
    df_agg = aggregate_to_occupation(df_matched, 'soc_code')
    
    # Contar total de tarefas por ocupação (incluindo não-matched)
    total_tasks = df.groupby('soc_code').size().reset_index(name='n_tasks_total')
    df_agg = df_agg.merge(total_tasks, on='soc_code', how='left')
    
    # Calcular cobertura
    df_agg['coverage'] = df_agg['n_tasks_matched'] / df_agg['n_tasks_total']
    
    logger.info(f"  Ocupações com dados: {len(df_agg):,}")
    logger.info(f"  Cobertura média: {df_agg['coverage'].mean():.1%}")
    
    return df_agg


def add_missing_occupations(df_agg: pd.DataFrame, 
                            df_onet: pd.DataFrame) -> pd.DataFrame:
    """Adiciona ocupações sem nenhuma tarefa matched."""
    logger.info("\n=== ADICIONANDO OCUPAÇÕES FALTANTES ===")
    
    # Todas as ocupações únicas
    all_occupations = df_onet.groupby('soc_code').agg({
        'Title': 'first',
        'O*NET-SOC Code': 'count'
    }).reset_index()
    all_occupations = all_occupations.rename(columns={
        'Title': 'soc_title', 
        'O*NET-SOC Code': 'n_tasks_total'
    })
    
    # Merge com agregação
    df_final = all_occupations.merge(
        df_agg[['soc_code', 'automation_score', 'augmentation_score', 
                'automation_raw', 'augmentation_raw', 'filtered_ratio',
                'n_tasks_matched', 'coverage']],
        on='soc_code',
        how='left'
    )
    
    # Preencher valores faltantes
    df_final['n_tasks_matched'] = df_final['n_tasks_matched'].fillna(0).astype(int)
    df_final['coverage'] = df_final['coverage'].fillna(0)
    
    n_without_data = df_final['automation_score'].isna().sum()
    logger.info(f"  Ocupações sem dados Anthropic: {n_without_data}")
    
    return df_final


def validate_results(df: pd.DataFrame):
    """Validações de sanidade dos resultados."""
    logger.info("\n=== VALIDAÇÕES ===")
    
    # 1. Ocupações de TI devem ter alta automação
    ti_codes = df[df['soc_code'].str.startswith('15-')]  # Computer occupations
    if len(ti_codes) > 0:
        ti_automation = ti_codes['automation_score'].mean()
        logger.info(f"  TI (15-*) automação média: {ti_automation:.3f}")
    
    # 2. Ocupações de educação devem ter alta aumentação
    edu_codes = df[df['soc_code'].str.startswith('25-')]  # Education occupations
    if len(edu_codes) > 0:
        edu_augmentation = edu_codes['augmentation_score'].mean()
        logger.info(f"  Educação (25-*) aumentação média: {edu_augmentation:.3f}")
    
    # 3. Distribuição geral
    logger.info(f"\nDistribuição de scores:")
    logger.info(f"  Automação - min: {df['automation_score'].min():.3f}, "
                f"max: {df['automation_score'].max():.3f}, "
                f"média: {df['automation_score'].mean():.3f}")
    logger.info(f"  Aumentação - min: {df['augmentation_score'].min():.3f}, "
                f"max: {df['augmentation_score'].max():.3f}, "
                f"média: {df['augmentation_score'].mean():.3f}")


def save_results(df: pd.DataFrame):
    """Salva tabela final."""
    # Ordenar colunas
    cols_output = [
        'soc_code', 'soc_title',
        'automation_score', 'augmentation_score',
        'automation_raw', 'augmentation_raw', 'filtered_ratio',
        'n_tasks_total', 'n_tasks_matched', 'coverage'
    ]
    
    df_output = df[[c for c in cols_output if c in df.columns]]
    df_output = df_output.sort_values('soc_code')
    
    # Salvar
    output_path = DATA_PROCESSED / "anthropic_index_soc6.csv"
    df_output.to_csv(output_path, index=False)
    logger.info(f"\n✓ Tabela salva em: {output_path}")
    logger.info(f"  Total de ocupações: {len(df_output):,}")
    
    # Também salvar em outputs/tables
    df_output.to_csv(OUTPUTS_TABLES / "anthropic_index_soc6.csv", index=False)
    
    return df_output


def main():
    """Pipeline principal."""
    logger.info("=" * 60)
    logger.info("ETAPA 2: Processamento Índice Anthropic")
    logger.info("=" * 60)
    
    # 1. Carregar dados
    df_anthropic = load_anthropic_tasks()
    df_onet = load_onet_statements()
    
    # 2. Merge datasets
    df_merged = merge_datasets(df_anthropic, df_onet)
    
    # 3. Calcular scores
    df_scores = calculate_scores(df_merged)
    
    # 4. Agregar por ocupação
    df_agg = aggregate_by_occupation(df_scores)
    
    # 5. Adicionar ocupações faltantes
    df_final = add_missing_occupations(df_agg, df_onet)
    
    # 6. Validar
    validate_results(df_final)
    
    # 7. Salvar
    df_output = save_results(df_final)
    
    logger.info("\n" + "=" * 60)
    logger.info("PROCESSAMENTO CONCLUÍDO")
    logger.info("=" * 60)
    
    return df_output


if __name__ == "__main__":
    main()
