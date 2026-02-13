"""
Script 04: Merge com índice de exposição à IA
==============================================

Faz merge do painel PNAD com o índice de exposição à IA Generativa.

Entrada:
- data/processed/pnad_panel_variables.parquet
- ../etapa3_crosswalk_onet_isco08/outputs/cod_automation_augmentation_index_final.csv

Saída: data/processed/pnad_panel_exposure.parquet
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from utils.weighted_stats import weighted_mean

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '04_merge_exposure.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_exposure_index():
    """
    Carrega índice de exposição à IA.

    Usa o output da etapa3 com imputação hierárquica para máxima cobertura.
    """

    logger.info("Carregando índice de exposição...")

    # Caminho do índice (etapa3)
    exposure_path = ROOT_DIR.parent / COD_EXPOSURE_PATH

    if not exposure_path.exists():
        logger.error(f"Arquivo de exposição não encontrado: {exposure_path}")
        logger.error("Verifique se etapa3 foi executada corretamente")
        raise FileNotFoundError(exposure_path)

    # Carregar
    exposure_df = pd.read_csv(exposure_path)

    logger.info(f"Carregado: {len(exposure_df)} ocupações")
    logger.info(f"Colunas: {list(exposure_df.columns)}")

    # Padronizar código para 4 dígitos
    exposure_df['cod_cod'] = exposure_df['cod_cod'].astype(str).str.zfill(4)

    # Extrair colunas relevantes
    cols_needed = ['cod_cod', EXPOSURE_COLUMN]

    # Adicionar augmentation se disponível
    if 'augmentation_index_cai' in exposure_df.columns:
        cols_needed.append('augmentation_index_cai')

    # Adicionar imputation_method se disponível (para diagnóstico)
    if 'imputation_method' in exposure_df.columns:
        cols_needed.append('imputation_method')

    exposure_df = exposure_df[cols_needed].copy()

    # Renomear coluna principal para exposure_score (padronização)
    exposure_df.rename(columns={EXPOSURE_COLUMN: 'exposure_score'}, inplace=True)

    # Estatísticas do índice
    logger.info(f"Exposure score - Min: {exposure_df['exposure_score'].min():.3f}")
    logger.info(f"Exposure score - Média: {exposure_df['exposure_score'].mean():.3f}")
    logger.info(f"Exposure score - Max: {exposure_df['exposure_score'].max():.3f}")

    # Distribuição de imputação (se disponível)
    if 'imputation_method' in exposure_df.columns:
        logger.info("\nMétodos de imputação:")
        for method, count in exposure_df['imputation_method'].value_counts().items():
            pct = count / len(exposure_df) * 100
            logger.info(f"  {method}: {count} ({pct:.1f}%)")

    return exposure_df


def merge_exposure(pnad_df, exposure_df):
    """
    Faz merge do PNAD com exposição.

    Parâmetros:
    -----------
    pnad_df : DataFrame
        Painel PNAD com variáveis criadas
    exposure_df : DataFrame
        Índice de exposição

    Retorna:
    --------
    DataFrame : PNAD com exposure_score
    """

    logger.info("")
    logger.info("="*70)
    logger.info("MERGE PNAD × EXPOSIÇÃO")
    logger.info("="*70)

    n_antes = len(pnad_df)

    # Garantir que códigos estão padronizados
    pnad_df['cod_ocupacao'] = pnad_df['cod_ocupacao'].astype(str).str.zfill(4)
    exposure_df['cod_cod'] = exposure_df['cod_cod'].astype(str).str.zfill(4)

    # Merge (left join para manter todos os registros do PNAD)
    logger.info(f"PNAD observações: {len(pnad_df):,}")
    logger.info(f"Exposure ocupações: {len(exposure_df)}")

    df = pnad_df.merge(
        exposure_df,
        left_on='cod_ocupacao',
        right_on='cod_cod',
        how='left'
    )

    # Verificar que não duplicou observações
    if len(df) != n_antes:
        logger.error(f"ERRO: Merge duplicou observações! {n_antes:,} → {len(df):,}")
        raise ValueError("Merge duplicou observações")

    logger.info(f"Merge concluído: {len(df):,} observações")

    return df


def validate_coverage(df):
    """
    Valida cobertura do merge.

    Verifica:
    - Percentual de observações com exposure_score
    - Cobertura ponderada pela população
    - Ocupações sem match
    """

    logger.info("")
    logger.info("="*70)
    logger.info("VALIDAÇÃO DE COBERTURA")
    logger.info("="*70)

    # Cobertura absoluta (número de observações)
    n_total = len(df)
    n_matched = df['exposure_score'].notna().sum()
    coverage_abs = n_matched / n_total

    logger.info(f"Cobertura absoluta: {n_matched:,}/{n_total:,} ({coverage_abs:.1%})")

    # Cobertura ponderada (população)
    pop_total = df['peso'].sum()
    pop_matched = df[df['exposure_score'].notna()]['peso'].sum()
    coverage_pop = pop_matched / pop_total

    logger.info(f"Cobertura populacional: {pop_matched/1e6:.1f}M/{pop_total/1e6:.1f}M ({coverage_pop:.1%})")

    # Verificar threshold mínimo
    if coverage_pop < MIN_EXPOSURE_COVERAGE:
        logger.warning(f"⚠️ Cobertura populacional ({coverage_pop:.1%}) abaixo do mínimo ({MIN_EXPOSURE_COVERAGE:.1%})")
    else:
        logger.info(f"✓ Cobertura populacional acima do mínimo ({MIN_EXPOSURE_COVERAGE:.1%})")

    # Ocupações sem match
    unmatched = df[df['exposure_score'].isna()]['cod_ocupacao'].unique()

    if len(unmatched) > 0:
        logger.info(f"\nOcupações sem match: {len(unmatched)}")

        # Amostrar populações sem match
        unmatched_stats = (
            df[df['exposure_score'].isna()]
            .groupby('cod_ocupacao')
            .agg({
                'peso': 'sum',
                'grande_grupo': 'first'
            })
            .sort_values('peso', ascending=False)
            .head(10)
        )

        unmatched_stats['pop_milhoes'] = (unmatched_stats['peso'] / 1e6).round(2)

        logger.info("\nTop 10 ocupações sem match (por população):")
        logger.info("\n" + unmatched_stats[['grande_grupo', 'pop_milhoes']].to_string())

        # Salvar lista completa
        unmatched_path = OUTPUTS_TABLES / 'unmatched_occupation_codes.csv'
        unmatched_stats.to_csv(unmatched_path)
        logger.info(f"\nLista completa salva em: {unmatched_path}")

    # Cobertura por trimestre (verificar consistência temporal)
    coverage_by_quarter = (
        df.groupby(['ano', 'trimestre'])
        .apply(lambda x: (x['exposure_score'].notna().sum(), x['peso'][x['exposure_score'].notna()].sum() / x['peso'].sum()))
        .reset_index()
    )
    coverage_by_quarter.columns = ['ano', 'trimestre', 'stats']
    coverage_by_quarter[['n_matched', 'pop_coverage']] = pd.DataFrame(coverage_by_quarter['stats'].tolist(), index=coverage_by_quarter.index)
    coverage_by_quarter.drop('stats', axis=1, inplace=True)

    logger.info("\nCobertura por trimestre:")
    logger.info("\n" + coverage_by_quarter.to_string(index=False))

    # Salvar
    coverage_path = OUTPUTS_TABLES / 'exposure_coverage_report.csv'
    coverage_by_quarter.to_csv(coverage_path, index=False)
    logger.info(f"\nRelatório de cobertura salvo em: {coverage_path}")

    return coverage_pop


if __name__ == "__main__":

    # Carregar dados
    logger.info("Carregando painel PNAD...")
    pnad_df = pd.read_parquet(DATA_PROCESSED / "pnad_panel_variables.parquet")
    logger.info(f"Carregado: {len(pnad_df):,} observações\n")

    # Carregar índice de exposição
    exposure_df = load_exposure_index()

    # Merge
    df = merge_exposure(pnad_df, exposure_df)

    # Validar cobertura
    coverage = validate_coverage(df)

    # Salvar
    output_path = DATA_PROCESSED / "pnad_panel_exposure.parquet"
    logger.info("")
    logger.info(f"Salvando em: {output_path}")
    df.to_parquet(output_path, index=False)

    logger.info("")
    logger.info("="*70)
    logger.info("MERGE CONCLUÍDO")
    logger.info("="*70)
    logger.info(f"Cobertura final: {coverage:.1%}")
    logger.info("Próximo passo: python src/05_create_treatment.py")
