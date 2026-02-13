"""
Script 02: Limpeza de dados do painel PNAD
===========================================

Entrada: data/raw/pnad_panel_2021q1_2024q4.parquet
Saída: data/processed/pnad_panel_clean.parquet
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '02_clean_panel.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_panel():
    """Carrega painel bruto"""
    logger.info("Carregando painel PNAD...")
    path = DATA_RAW / "pnad_panel_2021q1_2024q4.parquet"

    if not path.exists():
        logger.error(f"Arquivo não encontrado: {path}")
        logger.error("Execute primeiro: python src/01_download_panel_pnad.py")
        raise FileNotFoundError(path)

    df = pd.read_parquet(path)
    logger.info(f"Carregado: {len(df):,} observações")
    return df


def clean_panel_data(df):
    """
    Limpa e prepara dados do painel.

    Operações:
    - Conversão de tipos
    - Filtros de qualidade
    - Padronização de códigos
    """

    logger.info("")
    logger.info("="*70)
    logger.info("LIMPEZA DE DADOS DO PAINEL")
    logger.info("="*70)

    n_inicial = len(df)
    df = df.copy()

    # =========================================
    # 1. CONVERSÃO DE TIPOS
    # =========================================

    logger.info("Convertendo tipos...")

    # Numéricas
    vars_numericas = ['idade', 'anos_estudo', 'rendimento_habitual',
                      'horas_trabalhadas', 'peso']
    for var in vars_numericas:
        if var in df.columns:
            df[var] = pd.to_numeric(df[var], errors='coerce')

    # Strings (para códigos)
    vars_string = ['cod_ocupacao', 'sigla_uf', 'sexo', 'raca',
                   'condicao_ocupacao', 'tipo_vinculo', 'posicao_ocupacao']
    for var in vars_string:
        if var in df.columns:
            df[var] = df[var].astype(str).str.strip()

    logger.info("  ✓ Tipos convertidos")

    # =========================================
    # 2. FILTROS DE QUALIDADE
    # =========================================

    logger.info("")
    logger.info("Aplicando filtros de qualidade...")

    # Idade válida (18-65)
    n_before = len(df)
    df = df[(df['idade'] >= 18) & (df['idade'] <= 65)]
    logger.info(f"  Filtro idade (18-65): {n_before:,} → {len(df):,} ({len(df)/n_before:.1%})")

    # Peso válido
    n_before = len(df)
    df = df[df['peso'] > 0]
    logger.info(f"  Filtro peso > 0: {n_before:,} → {len(df):,} ({len(df)/n_before:.1%})")

    # Ocupação válida (não missing, não "0000", não "nan")
    n_before = len(df)
    df = df[df['cod_ocupacao'].notna()]
    df = df[df['cod_ocupacao'] != '']
    df = df[df['cod_ocupacao'] != '0000']
    df = df[df['cod_ocupacao'] != 'nan']
    logger.info(f"  Filtro ocupação válida: {n_before:,} → {len(df):,} ({len(df)/n_before:.1%})")

    # =========================================
    # 3. PADRONIZAÇÃO DE CÓDIGOS
    # =========================================

    logger.info("")
    logger.info("Padronizando códigos...")

    # COD ocupação: garantir 4 dígitos
    df['cod_ocupacao'] = df['cod_ocupacao'].str[:4].str.zfill(4)

    # UF: uppercase
    df['sigla_uf'] = df['sigla_uf'].str.upper()

    logger.info("  ✓ Códigos padronizados")

    # =========================================
    # 4. SUMÁRIO
    # =========================================

    logger.info("")
    logger.info("="*70)
    logger.info("SUMÁRIO DA LIMPEZA")
    logger.info("="*70)
    logger.info(f"Observações iniciais: {n_inicial:,}")
    logger.info(f"Observações finais: {len(df):,}")
    logger.info(f"Taxa de retenção: {len(df)/n_inicial:.1%}")
    logger.info("")

    return df


def validate_panel_structure(df):
    """Valida estrutura do painel"""

    logger.info("Validando estrutura do painel...")

    # Verificar trimestres
    quarters_present = df.groupby(['ano', 'trimestre']).size()
    logger.info(f"  Trimestres presentes: {len(quarters_present)}/16")

    # Observações por trimestre
    obs_per_quarter = df.groupby(['ano', 'trimestre']).size()
    min_obs = obs_per_quarter.min()
    max_obs = obs_per_quarter.max()

    logger.info(f"  Obs por trimestre: {min_obs:,} a {max_obs:,}")

    if min_obs < MIN_OBS_PER_QUARTER:
        logger.warning(f"  ⚠️ Algum trimestre com < {MIN_OBS_PER_QUARTER:,} obs")

    # UFs por trimestre
    ufs_per_quarter = df.groupby(['ano', 'trimestre'])['sigla_uf'].nunique()
    min_ufs = ufs_per_quarter.min()

    logger.info(f"  UFs por trimestre: {min_ufs} a {ufs_per_quarter.max()}")

    if min_ufs < N_UFS:
        logger.warning(f"  ⚠️ Algum trimestre com < {N_UFS} UFs")

    # População por trimestre
    pop_per_quarter = df.groupby(['ano', 'trimestre'])['peso'].sum() / 1e6

    logger.info("")
    logger.info("  População por trimestre (milhões):")
    for (ano, tri), pop in pop_per_quarter.items():
        logger.info(f"    {ano}Q{tri}: {pop:.1f}M")

    logger.info("")

    return quarters_present


if __name__ == "__main__":

    # Carregar dados brutos
    df = load_panel()

    # Limpar
    df = clean_panel_data(df)

    # Validar estrutura
    validate_panel_structure(df)

    # Salvar
    output_path = DATA_PROCESSED / "pnad_panel_clean.parquet"
    logger.info(f"Salvando dados limpos em: {output_path}")
    df.to_parquet(output_path, index=False)

    logger.info("")
    logger.info("="*70)
    logger.info("LIMPEZA CONCLUÍDA")
    logger.info("="*70)
    logger.info(f"Próximo passo: python src/03_create_variables.py")
