"""
Script 03: Limpeza e criação de variáveis derivadas PNAD
Entrada: data/raw/pnad_2025q3.parquet (ou trimestre disponível)
Saída: data/processed/pnad_clean.csv
"""

import logging
import pandas as pd
import numpy as np
import sys
import glob
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *

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
    
    # Pegar o mais recente
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
    
    # --- LIMPEZA ---
    
    # 1. Converter tipos
    df['cod_ocupacao'] = df['cod_ocupacao'].astype(str).str.zfill(4)
    df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
    df['rendimento_habitual'] = pd.to_numeric(df['rendimento_habitual'], errors='coerce')
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce')
    
    # 2. Remover missings críticos
    df = df.dropna(subset=['cod_ocupacao', 'idade', 'peso'])
    logger.info(f"Após remover missings críticos: {len(df):,} ({len(df)/n_inicial:.1%})")
    
    # 3. Filtrar faixa etária (18-65)
    df = df[(df['idade'] >= 18) & (df['idade'] <= 65)]
    logger.info(f"Após filtrar 18-65 anos: {len(df):,} ({len(df)/n_inicial:.1%})")
    
    # 4. Remover ocupações inválidas (código 0000 ou similar)
    df = df[~df['cod_ocupacao'].isin(['0000', '9999'])]
    logger.info(f"Após remover ocupações inválidas: {len(df):,}")
    
    # --- VARIÁVEIS DERIVADAS ---
    
    # Formalidade (códigos são strings)
    df['formal'] = df['posicao_ocupacao'].isin(POSICAO_FORMAL).astype(int)
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
    
    # Winsorização de renda (percentil 99)
    p99 = df['rendimento_habitual'].quantile(0.99)
    df['rendimento_winsor'] = df['rendimento_habitual'].clip(upper=p99)
    logger.info(f"Percentil 99 renda: R$ {p99:,.0f}")
    
    # --- VALIDAÇÕES ---
    
    logger.info("\n=== VALIDAÇÕES ===")
    logger.info(f"Ocupações únicas (COD): {df['cod_ocupacao'].nunique()}")
    logger.info(f"UFs: {df['sigla_uf'].nunique()}")
    logger.info(f"Regiões: {df['regiao'].nunique()}")
    logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")
    
    logger.info("\nDistribuição por sexo:")
    for sexo, peso in df.groupby('sexo_texto')['peso'].sum().items():
        logger.info(f"  {sexo}: {peso/1e6:.1f} milhões")
    
    logger.info("\nDistribuição por região:")
    for regiao, peso in df.groupby('regiao')['peso'].sum().sort_values(ascending=False).items():
        logger.info(f"  {regiao}: {peso/1e6:.1f} milhões")
    
    # Salvar
    output_path = DATA_PROCESSED / "pnad_clean.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"\n✓ Salvo em: {output_path}")
    
    return df

if __name__ == "__main__":
    clean_pnad()
