import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para importações
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from etapa4_automation_augmentation_analysis.config.settings import *

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '01_merge_pnad_indices.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_merge():
    """Unifica PNAD+ILO com os índices Anthropic (Automation/Augmentation)."""
    
    logger.info("Iniciando unificação das bases...")

    # 1. Carregar Base PNAD+ILO (Etapa 1)
    if not PNAD_ILO_MERGED.exists():
        logger.error(f"Arquivo PNAD+ILO não encontrado: {PNAD_ILO_MERGED}")
        return
    
    logger.info(f"Lendo PNAD+ILO de: {PNAD_ILO_MERGED}")
    df_pnad = pd.read_csv(PNAD_ILO_MERGED)
    df_pnad['cod_ocupacao'] = df_pnad['cod_ocupacao'].astype(str).str.zfill(4)
    logger.info(f"PNAD carregada: {len(df_pnad):,} linhas")

    # 2. Carregar Índices Anthropic (Etapa 3)
    if not ANTHROPIC_INDICES.exists():
        logger.error(f"Arquivo de índices Anthropic não encontrado: {ANTHROPIC_INDICES}")
        return
    
    logger.info(f"Lendo índices Anthropic de: {ANTHROPIC_INDICES}")
    df_indices = pd.read_csv(ANTHROPIC_INDICES)
    df_indices['cod_cod'] = df_indices['cod_cod'].astype(str).str.zfill(4)
    
    # Selecionar colunas de interesse para o merge (evitar duplicatas de nomes)
    cols_to_merge = [
        'cod_cod', 'automation_share_cai', 'augmentation_share_cai', 'automation_index_cai',
        'automation_share_api', 'augmentation_share_api', 'automation_index_api',
        'dominant_mode_cai', 'dominant_mode_api', 'imputation_method', 'imputation_note'
    ]
    df_indices = df_indices[cols_to_merge]
    logger.info(f"Índices carregados: {len(df_indices)} ocupações")

    # 3. Realizar o Merge
    # Join por cod_ocupacao (PNAD) e cod_cod (Indices)
    df_merged = df_pnad.merge(df_indices, left_on='cod_ocupacao', right_on='cod_cod', how='left')
    
    # Remover coluna redundante
    if 'cod_cod' in df_merged.columns:
        df_merged = df_merged.drop(columns=['cod_cod'])

    # 4. Estatísticas de Cobertura
    # Como a imputação hierárquica foi feita para 100% da estrutura COD, 
    # a cobertura na PNAD deve ser de quase 100% para os códigos que existem na estrutura.
    coverage = df_merged['automation_index_cai'].notna().mean()
    logger.info(f"Cobertura dos índices na PNAD: {coverage:.1%}")

    # 5. Salvar Resultado Consolidado
    output_path = DATA_PROCESSED / "pnad_anthropic_merged.csv"
    df_merged.to_csv(output_path, index=False)
    logger.info(f"Base consolidada salva em: {output_path}")
    logger.info(f"Colunas finais: {df_merged.columns.tolist()}")

if __name__ == "__main__":
    run_merge()
