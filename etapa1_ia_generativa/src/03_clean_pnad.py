"""
Script 03: Limpeza e criação de variáveis derivadas PNAD
Entrada: data/raw/pnad_2025q3.parquet (ou trimestre disponível)
Saída: data/processed/pnad_clean.csv
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
from src.utils.weighted_stats import weighted_quantile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '03_pnad_clean.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_pnad_file():
    """Encontra o arquivo PNAD mais recente na pasta raw"""
    pnad_files = list(DATA_RAW.glob("pnad_*.parquet"))
    if not pnad_files:
        raise FileNotFoundError(f"Nenhum arquivo PNAD encontrado em {DATA_RAW}")

    latest_file = sorted(pnad_files)[-1]
    logger.info(f"Usando arquivo: {latest_file.name}")
    return latest_file

def clean_pnad():
    """Limpa e prepara dados PNAD"""

    input_path = find_pnad_file()
    logger.info(f"Lendo: {input_path}")
    df = pd.read_parquet(input_path)

    n_inicial = len(df)
    logger.info(f"Observações iniciais: {n_inicial:,}")

    # --- LIMPEZA - Conversão de tipos ---
    df['cod_ocupacao'] = df['cod_ocupacao'].astype(str).str.zfill(4)
    df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
    df['rendimento_habitual'] = pd.to_numeric(df['rendimento_habitual'], errors='coerce')
    df['rendimento_efetivo'] = pd.to_numeric(df['rendimento_efetivo'], errors='coerce')
    df['horas_habituais'] = pd.to_numeric(df['horas_habituais'], errors='coerce')
    df['horas_efetivas'] = pd.to_numeric(df['horas_efetivas'], errors='coerce')
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce')

    # --- LIMPEZA - Filtros ---

    # Remover missings críticos (ocupação, idade, peso — NÃO renda)
    df = df.dropna(subset=['cod_ocupacao', 'idade', 'peso'])
    logger.info(f"Após remover missings críticos: {len(df):,} ({len(df)/n_inicial:.1%})")

    # Filtrar faixa etária (18-65)
    df = df[(df['idade'] >= 18) & (df['idade'] <= 65)]
    logger.info(f"Após filtrar 18-65 anos: {len(df):,} ({len(df)/n_inicial:.1%})")

    # Remover ocupações inválidas
    df = df[~df['cod_ocupacao'].isin(['0000', '9999'])]
    logger.info(f"Após remover ocupações inválidas: {len(df):,}")

    # --- VARIÁVEIS DERIVADAS ---

    # Flag de renda (em vez de excluir sem renda)
    df['tem_renda'] = (df['rendimento_habitual'].notna() & (df['rendimento_habitual'] > 0)).astype(int)
    n_sem_renda = (df['tem_renda'] == 0).sum()
    pop_sem_renda = df.loc[df['tem_renda'] == 0, 'peso'].sum() / 1e6
    logger.info(f"Trabalhadores sem renda declarada: {n_sem_renda:,} obs ({pop_sem_renda:.1f} milhões)")

    # Formalidade (códigos são strings)
    df['formal'] = df['posicao_ocupacao'].astype(str).isin(POSICAO_FORMAL).astype(int)
    logger.info(f"Taxa de formalidade: {df['formal'].mean():.1%}")

    # Faixas etárias
    df['faixa_etaria'] = pd.cut(
        df['idade'],
        bins=IDADE_BINS,
        labels=IDADE_LABELS
    )

    # Região
    df['regiao'] = df['sigla_uf'].map(REGIAO_MAP)

    # Raça agregada (códigos são strings)
    df['raca_agregada'] = df['raca_cor'].astype(str).map(RACA_AGREGADA_MAP)

    # Grande grupo ocupacional
    df['grande_grupo'] = df['cod_ocupacao'].str[0].map(GRANDES_GRUPOS)

    # Sexo como texto
    df['sexo_texto'] = df['sexo'].map({1: 'Homem', 2: 'Mulher', '1': 'Homem', '2': 'Mulher'})

    # Winsorização de renda (percentis ponderados 1 e 99) — APENAS para quem tem renda
    mask_renda = df['tem_renda'] == 1
    p01 = weighted_quantile(
        df.loc[mask_renda, 'rendimento_habitual'],
        df.loc[mask_renda, 'peso'], 0.01
    )
    p99 = weighted_quantile(
        df.loc[mask_renda, 'rendimento_habitual'],
        df.loc[mask_renda, 'peso'], 0.99
    )
    df['rendimento_winsor'] = df['rendimento_habitual'].clip(lower=p01, upper=p99)
    logger.info(f"Winsorização ponderada: P1 = R$ {p01:,.0f}, P99 = R$ {p99:,.0f}")

    # Faixas de renda em salários mínimos
    df['faixa_renda_sm'] = pd.cut(
        df['rendimento_habitual'] / SALARIO_MINIMO,
        bins=[0, 1, 2, 3, 5, float('inf')],
        labels=['Até 1 SM', '1-2 SM', '2-3 SM', '3-5 SM', '5+ SM'],
        right=True,
        include_lowest=True,
    )
    logger.info(f"Distribuição por faixa de renda (SM = R$ {SALARIO_MINIMO}):")
    for faixa, peso in df[df['tem_renda'] == 1].groupby('faixa_renda_sm')['peso'].sum().items():
        pct = peso / df.loc[mask_renda, 'peso'].sum() * 100
        logger.info(f"  {faixa}: {peso/1e6:.1f} milhões ({pct:.1f}%)")

    # --- VALIDAÇÕES ---

    logger.info("\n=== VALIDAÇÕES ===")
    logger.info(f"Ocupações únicas (COD): {df['cod_ocupacao'].nunique()}")
    logger.info(f"UFs: {df['sigla_uf'].nunique()}")
    logger.info(f"Regiões: {df['regiao'].nunique()}")
    logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")

    # Verificar missings em variáveis derivadas
    for col in ['regiao', 'raca_agregada', 'grande_grupo', 'faixa_etaria', 'sexo_texto']:
        n_miss = df[col].isna().sum()
        if n_miss > 0:
            logger.warning(f"  {col} tem {n_miss:,} valores faltantes")

    logger.info("\nDistribuição por sexo:")
    for sexo, peso in df.groupby('sexo_texto')['peso'].sum().items():
        logger.info(f"  {sexo}: {peso/1e6:.1f} milhões")

    logger.info("\nDistribuição por região:")
    for regiao, peso in df.groupby('regiao')['peso'].sum().sort_values(ascending=False).items():
        logger.info(f"  {regiao}: {peso/1e6:.1f} milhões")

    # Verificar preenchimento de horas
    n_horas_hab = df['horas_habituais'].notna().sum()
    n_horas_efe = df['horas_efetivas'].notna().sum()
    logger.info(f"\nHoras habituais: {n_horas_hab:,} ({n_horas_hab/len(df):.1%})")
    logger.info(f"Horas efetivas:  {n_horas_efe:,} ({n_horas_efe/len(df):.1%})")

    # Salvar
    output_path = DATA_PROCESSED / "pnad_clean.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"\nSalvo em: {output_path}")
    logger.info(f"df_pnad: {df.shape[0]:,} linhas x {df.shape[1]} colunas")

    return df

if __name__ == "__main__":
    clean_pnad()
