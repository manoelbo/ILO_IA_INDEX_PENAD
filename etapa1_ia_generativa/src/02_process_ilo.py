"""
Script 02: Processar planilha ILO com scores de exposição
Entrada: data/raw/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx
Saída: data/processed/ilo_exposure_clean.csv
"""

import logging
import pandas as pd
import requests
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
        logging.FileHandler(OUTPUTS_LOGS / '02_ilo_process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_ilo_if_needed():
    """Baixa arquivo ILO do GitHub se não existir"""
    if not ILO_FILE.exists():
        logger.info(f"Baixando arquivo ILO de: {ILO_URL}")
        response = requests.get(ILO_URL)
        with open(ILO_FILE, 'wb') as f:
            f.write(response.content)
        logger.info("Download concluído")

def process_ilo():
    """Processa planilha ILO e extrai scores por ocupação"""
    
    download_ilo_if_needed()
    
    logger.info(f"Lendo arquivo: {ILO_FILE}")
    df_raw = pd.read_excel(ILO_FILE)
    
    logger.info(f"Linhas raw (tarefas): {len(df_raw):,}")
    logger.info(f"Colunas disponíveis: {list(df_raw.columns)}")
    
    # Identificar colunas corretas (podem variar ligeiramente)
    # Ajustar conforme estrutura real do arquivo
    col_mapping = {
        'ISCO_08': 'isco_08',
        'Title': 'occupation_title',
        'mean_score_2025': 'exposure_score',
        'SD_2025': 'exposure_sd',
        'potential25': 'exposure_gradient'
    }
    
    # Verificar se colunas existem
    available_cols = [c for c in col_mapping.keys() if c in df_raw.columns]
    logger.info(f"Colunas encontradas: {available_cols}")
    
    # Renomear
    df = df_raw.rename(columns={k: v for k, v in col_mapping.items() if k in df_raw.columns})
    
    # Agregar por ocupação (arquivo tem múltiplas tarefas por ocupação)
    df_agg = df.groupby('isco_08').agg({
        'occupation_title': 'first',
        'exposure_score': 'mean',
        'exposure_sd': 'mean',
        'exposure_gradient': 'first'
    }).reset_index()
    
    logger.info(f"Ocupações únicas: {len(df_agg):,}")
    logger.info(f"Score médio: {df_agg['exposure_score'].mean():.3f}")
    logger.info(f"Score range: [{df_agg['exposure_score'].min():.3f}, {df_agg['exposure_score'].max():.3f}]")
    
    # Garantir formato string com 4 dígitos
    df_agg['isco_08_str'] = df_agg['isco_08'].astype(str).str.zfill(4)
    
    # Distribuição por gradiente
    logger.info("\nDistribuição por gradiente:")
    for grad, count in df_agg['exposure_gradient'].value_counts().items():
        logger.info(f"  {grad}: {count} ocupações")
    
    # Salvar
    output_path = DATA_PROCESSED / "ilo_exposure_clean.csv"
    df_agg.to_csv(output_path, index=False)
    logger.info(f"\n✓ Salvo em: {output_path}")
    
    return df_agg

if __name__ == "__main__":
    process_ilo()
