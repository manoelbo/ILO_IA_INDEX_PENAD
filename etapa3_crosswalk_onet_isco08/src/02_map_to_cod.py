import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para importações
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from etapa3_crosswalk_onet_isco08.config.settings import *

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '02_map_to_cod.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def read_cod_structure(path):
    """Lê a estrutura COD e retorna um mapeamento de códigos e denominações."""
    logger.info(f"Lendo estrutura COD de: {path}")
    # Mesma lógica do Script 08 da Etapa 1
    try:
        df_cod = pd.read_excel(path, sheet_name='Estrutura COD', engine='xlrd', header=1)
    except Exception as e:
        logger.warning(f"Erro com xlrd, tentando openpyxl: {e}")
        df_cod = pd.read_excel(path, sheet_name='Estrutura COD', engine='openpyxl', header=1)
    
    df_cod.columns = ['grande_grupo', 'subgrupo_principal', 'subgrupo', 'grupo_base', 'denominacao']
    
    # Extrair mapeamento de código de 4 dígitos (grupo_base)
    df_gb = df_cod.dropna(subset=['grupo_base'])[['grupo_base', 'denominacao']].copy()
    df_gb['cod_cod'] = df_gb['grupo_base'].astype(str).str.replace('.0', '', regex=False).str.zfill(4)
    
    return df_gb[['cod_cod', 'denominacao']]

def run_map_to_cod():
    """Mapeia os índices ISCO-08 para a classificação COD brasileira."""
    
    logger.info("Iniciando mapeamento ISCO-08 -> COD (Metodologia ESCO)...")

    # 1. Carregar Índices ISCO-08 (Gerados no passo anterior via ESCO)
    # Ajustado para ler o arquivo novo com sufixo _esco
    isco_csv = OUTPUTS_TABLES / "isco_automation_augmentation_index_esco.csv"
    if not isco_csv.exists():
        logger.error(f"Arquivo ISCO não encontrado: {isco_csv}")
        # Fallback para o arquivo anterior se necessário, ou abortar
        isco_csv_legacy = OUTPUTS_TABLES / "isco_automation_augmentation_index.csv"
        if isco_csv_legacy.exists():
            logger.warning(f"Usando arquivo legado como fallback: {isco_csv_legacy}")
            isco_csv = isco_csv_legacy
        else:
            return
    
    df_isco = pd.read_csv(isco_csv)
    df_isco['isco_08_code'] = df_isco['isco_08_code'].astype(str).str.zfill(4)
    logger.info(f"Índices ISCO-08 carregados: {len(df_isco)}")

    # 2. Carregar Estrutura COD
    df_cod = read_cod_structure(COD_STRUCTURE)
    logger.info(f"Estrutura COD carregada: {len(df_cod)} ocupações")

    # 3. Realizar o Match (Crosswalk Direto ISCO-08 4d <-> COD 4d)
    # Como a COD é baseada na ISCO-08, os códigos de 4 dígitos são equivalentes.
    df_final = df_cod.merge(df_isco, left_on='cod_cod', right_on='isco_08_code', how='left')
    
    # 4. Estatísticas de Cobertura
    coverage = df_final['automation_index_cai'].notna().mean()
    logger.info(f"Cobertura dos índices Anthropic na estrutura COD: {coverage:.1%}")

    # 5. Salvar Resultados
    output_path = OUTPUTS_TABLES / "cod_automation_augmentation_index_esco.csv"
    df_final.to_csv(output_path, index=False)
    logger.info(f"Tabela final COD salva em: {output_path}")

if __name__ == "__main__":
    run_map_to_cod()
