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
        logging.FileHandler(OUTPUTS_LOGS / '01_crosswalk_soc_isco.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def weighted_mean(values, weights):
    """Calcula a média ponderada de uma série de valores."""
    valid = ~(pd.isna(values) | pd.isna(weights))
    if valid.sum() == 0:
        return np.nan
    v = values[valid]
    w = weights[valid]
    if w.sum() == 0:
        return v.mean()
    return np.average(v, weights=w)

def run_soc_isco_crosswalk():
    """Executa a cadeia de mapeamento SOC 2018 -> SOC 2010 -> ISCO-08."""
    
    logger.info("Iniciando Crosswalk SOC -> ISCO-08...")

    # 1. Carregar Índices Anthropic (O*NET/SOC 2018)
    logger.info(f"Lendo índices Anthropic de: {ANTHROPIC_INDEX_ONET}")
    df_anthropic = pd.read_csv(ANTHROPIC_INDEX_ONET)
    # soc_6d no arquivo é SOC 2018
    df_anthropic = df_anthropic.rename(columns={'soc_6d': 'soc_2018_code'})
    logger.info(f"Ocupações Anthropic carregadas: {len(df_anthropic)}")

    # 2. Carregar Crosswalk SOC 2010 a 2018
    logger.info(f"Lendo Crosswalk SOC 2010-2018 de: {CROSSWALK_SOC_10_18}")
    # O arquivo tem cabeçalhos que precisam ser pulados. A inspeção mostrou que a linha real de dados começa após o skip.
    df_10_18 = pd.read_excel(CROSSWALK_SOC_10_18, skiprows=SKIP_ROWS_EXCEL + 1) # +1 porque o header é a linha 7
    # Renomear colunas baseadas na inspeção: Unnamed: 0 (2010), Unnamed: 2 (2018)
    df_10_18 = df_10_18.iloc[:, [0, 1, 2, 3]]
    df_10_18.columns = ['soc_2010_code', 'soc_2010_title', 'soc_2018_code', 'soc_2018_title']
    df_10_18 = df_10_18.dropna(subset=['soc_2010_code', 'soc_2018_code'])
    logger.info(f"Mapeamentos SOC 2010-2018 carregados: {len(df_10_18)}")

    # 3. Carregar Crosswalk SOC 2010 a ISCO-08
    logger.info(f"Lendo Crosswalk SOC 2010-ISCO de: {CROSSWALK_SOC_ISCO}")
    # Usar a aba '2010 SOC to ISCO-08'
    df_soc_isco = pd.read_excel(CROSSWALK_SOC_ISCO, sheet_name='2010 SOC to ISCO-08', skiprows=SKIP_ROWS_EXCEL + 1)
    df_soc_isco.columns = ['soc_2010_code', 'soc_2010_title', 'part', 'isco_08_code', 'isco_08_title', 'comment']
    df_soc_isco = df_soc_isco.dropna(subset=['soc_2010_code', 'isco_08_code'])
    
    # Garantir que isco_08_code seja string de 4 dígitos
    df_soc_isco['isco_08_code'] = df_soc_isco['isco_08_code'].astype(str).str.replace('.0', '', regex=False).str.zfill(4)
    logger.info(f"Mapeamentos SOC 2010-ISCO carregados: {len(df_soc_isco)}")

    # 4. Encadeamento de Joins
    logger.info("Realizando merges...")
    
    # Passo A: Anthropic (SOC 2018) -> SOC 2010
    df_merged = df_anthropic.merge(df_10_18[['soc_2018_code', 'soc_2010_code']], on='soc_2018_code', how='inner')
    logger.info(f"Após merge SOC 2018 -> 2010: {len(df_merged)} linhas")
    
    # Passo B: SOC 2010 -> ISCO-08
    df_merged = df_merged.merge(df_soc_isco[['soc_2010_code', 'isco_08_code', 'isco_08_title']], on='soc_2010_code', how='inner')
    logger.info(f"Após merge SOC 2010 -> ISCO-08: {len(df_merged)} linhas")

    # 5. Agregação por ISCO-08
    logger.info("Agregando resultados por ISCO-08...")
    
    # Vamos agregar as colunas de CAI e API separadamente
    cols_to_agg = [
        'automation_share_cai', 'augmentation_share_cai', 'automation_index_cai',
        'automation_share_api', 'augmentation_share_api', 'automation_index_api'
    ]
    
    # Filtrar colunas que existem (algumas podem estar faltando se o arquivo de entrada mudar)
    cols_to_agg = [c for c in cols_to_agg if c in df_merged.columns]
    
    # Precisamos de um volume de uso para ponderar. No arquivo original, tínhamos usage_volume.
    # Mas ao passar pelo crosswalk, o usage_volume pode ser redistribuído.
    # Como simplificação, usaremos o usage_volume original da Anthropic (se disponível).
    # Se não houver usage_volume, usaremos média simples (peso 1).
    if 'usage_volume' not in df_merged.columns:
        df_merged['usage_volume'] = 1.0
    
    def agg_func(x):
        return weighted_mean(x, df_merged.loc[x.index, 'usage_volume'])

    agg_rules = {col: agg_func for col in cols_to_agg}
    agg_rules['usage_volume'] = 'sum'
    agg_rules['isco_08_title'] = 'first'

    df_isco = df_merged.groupby('isco_08_code').agg(agg_rules).reset_index()
    
    # Recalcular modos dominantes
    if 'automation_index_cai' in df_isco.columns:
        df_isco['dominant_mode_cai'] = np.where(df_isco['automation_index_cai'] > 0, "automation", "augmentation")
    if 'automation_index_api' in df_isco.columns:
        df_isco['dominant_mode_api'] = np.where(df_isco['automation_index_api'] > 0, "automation", "augmentation")

    # 6. Salvar Resultados
    output_csv = OUTPUTS_TABLES / "isco_automation_augmentation_index.csv"
    df_isco.to_csv(output_csv, index=False)
    logger.info(f"Tabela ISCO-08 salva com sucesso em: {output_csv}")
    
    return df_isco

if __name__ == "__main__":
    run_soc_isco_crosswalk()
