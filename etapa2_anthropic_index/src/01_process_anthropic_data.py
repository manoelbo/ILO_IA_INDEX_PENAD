import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para importações
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from etapa2_anthropic_index.config.settings import *
from etapa2_anthropic_index.src.utils.aggregation import calculate_indices, weighted_mean

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '01_process_anthropic_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_lfs_pointer(file_path):
    """Verifica se o arquivo é um ponteiro Git LFS."""
    if not file_path.exists():
        return False
    with open(file_path, 'r') as f:
        first_line = f.readline()
        return first_line.startswith("version https://git-lfs.github.com/spec/v1")

def load_anthropic_v4_data(platform="claude_ai", task_mapping=None):
    """
    Carrega os dados brutos da V4 da Anthropic.
    Foca na interseção onet_task::collaboration.
    """
    file_path = CLAUDE_AI_RAW if platform == "claude_ai" else API_1P_RAW
    
    if check_lfs_pointer(file_path):
        logger.error(f"ERRO: O arquivo {file_path.name} é um ponteiro Git LFS.")
        logger.error("Por favor, execute 'git lfs pull' no diretório EconomicIndex ou baixe os dados reais.")
        return None

    logger.info(f"Carregando dados da Anthropic ({platform})...")
    # O arquivo AEI Raw é no formato long
    df = pd.read_csv(file_path)
    
    # Filtrar para a faceta de interseção onet_task::collaboration no nível GLOBAL
    mask = (df['facet'] == 'onet_task::collaboration') & (df['geo_id'] == 'GLOBAL')
    df_collab = df[mask].copy()
    
    if df_collab.empty:
        logger.warning(f"Nenhum dado de colaboração encontrado para a plataforma {platform}.")
        return None
        
    # cluster_name no formato 'task_description::collaboration_mode'
    # Ex: 'act as advisers to student organizations.::directive'
    # Usar rsplit para pegar apenas o último :: como separador do modo
    df_collab[['task_desc', 'mode']] = df_collab['cluster_name'].str.rsplit('::', n=1, expand=True)
    
    # Limpar descrição da tarefa para matching
    df_collab['task_desc_clean'] = df_collab['task_desc'].str.strip().str.lower().str.rstrip('.')
    
    # Pivotar para ter modos como colunas
    df_pivot = df_collab.pivot_table(
        index='task_desc_clean', 
        columns='mode', 
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Adicionar o código SOC usando o mapeamento fornecido
    if task_mapping is not None:
        df_pivot = df_pivot.merge(task_mapping, on='task_desc_clean', how='inner')
    
    # Também precisamos do volume (onet_task_count) para cada tarefa
    mask_count = (df['facet'] == 'onet_task') & (df['variable'] == 'onet_task_count') & (df['geo_id'] == 'GLOBAL')
    df_counts = df[mask_count][['cluster_name', 'value']].rename(columns={'cluster_name': 'task_desc', 'value': 'usage_volume'})
    df_counts['task_desc_clean'] = df_counts['task_desc'].str.strip().str.lower().str.rstrip('.')
    df_counts = df_counts.groupby('task_desc_clean')['usage_volume'].sum().reset_index()
    
    df_result = df_pivot.merge(df_counts, on='task_desc_clean', how='inner')
    
    logger.info(f"Total de tarefas carregadas ({platform}): {len(df_result)}")
    return df_result

def process_occupations():
    """Processa dados Anthropic V4 e gera o índice O*NET SOC 6-digit."""
    
    # 1. Carregar Mapeamentos O*NET
    logger.info("Carregando mapeamentos O*NET/SOC...")
    try:
        if check_lfs_pointer(ONET_TASK_STATEMENTS):
            logger.error(f"Ponteiro LFS detectado em {ONET_TASK_STATEMENTS}")
            return
            
        df_onet = pd.read_csv(ONET_TASK_STATEMENTS)
        
        # Criar mapeamento Descrição -> Código
        # Normalizar descrição para matching
        df_onet['task_desc_clean'] = df_onet['Task'].str.strip().str.lower().str.rstrip('.')
        
        # Mapeamento Task Desc -> Codes
        task_mapping = df_onet[['task_desc_clean', 'O*NET-SOC Code']].drop_duplicates()
        task_mapping.columns = ['task_desc_clean', 'onet_soc_code']
        
        # SOC Mapping para títulos e agregação
        df_onet['soc_6d'] = df_onet['O*NET-SOC Code'].str.split('.').str[0]
        soc_mapping = df_onet[['O*NET-SOC Code', 'soc_6d', 'Title']].drop_duplicates()
        soc_mapping.columns = ['onet_soc_code', 'soc_6d', 'occupation_title']
        
    except Exception as e:
        logger.error(f"Erro ao carregar mapeamentos O*NET: {e}")
        return

    # 2. Carregar e Processar Dados Anthropic (Claude.ai e API)
    logger.info("Processando dados Claude.ai...")
    df_cai = load_anthropic_v4_data(platform="claude_ai", task_mapping=task_mapping)
    
    logger.info("Processando dados 1P API...")
    df_api = load_anthropic_v4_data(platform="api_1p", task_mapping=task_mapping)
    
    # 3. Calcular Índices e Agregar
    results = {}
    for name, df_platform in [("claude_ai", df_cai), ("api_1p", df_api)]:
        if df_platform is None or df_platform.empty:
            continue
            
        logger.info(f"Calculando índices para {name}...")
        df_platform = calculate_indices(df_platform)
        df_merged = df_platform.merge(soc_mapping, on='onet_soc_code', how='inner')
        
        # Agregação ponderada
        def agg_weighted_mean(x):
            return weighted_mean(x, df_merged.loc[x.index, 'usage_volume'])

        agg_rules = {
            'automation_share': agg_weighted_mean,
            'augmentation_share': agg_weighted_mean,
            'usage_volume': 'sum'
        }
        
        df_soc = df_merged.groupby(['soc_6d', 'occupation_title']).agg(agg_rules).reset_index()
        df_soc['automation_index'] = df_soc['automation_share'] - df_soc['augmentation_share']
        df_soc['dominant_mode'] = np.where(df_soc['automation_index'] > 0, "automation", "augmentation")
        
        results[name] = df_soc

    # 4. Combinar ou Salvar Separado
    # O usuário quer uma tabela final. Vamos fornecer uma com prefixos para cada plataforma
    # e uma versão combinada (média ponderada se desejar, mas melhor manter separado para clareza)
    
    if "claude_ai" in results and "api_1p" in results:
        df_final = results["claude_ai"].merge(
            results["api_1p"], on=['soc_6d', 'occupation_title'], 
            how='outer', suffixes=('_cai', '_api')
        )
        # Criar uma média geral (opcional)
        # ...
    elif "claude_ai" in results:
        df_final = results["claude_ai"]
    else:
        logger.error("Nenhum dado processado com sucesso.")
        return

    # 5. Salvar Resultados
    output_path = DATA_PROCESSED / "anthropic_index_soc6_v4.csv"
    df_final.to_csv(output_path, index=False)
    
    final_output = OUTPUTS_TABLES / "onet_automation_augmentation_index.csv"
    # Se tiver ambas, vamos exportar as colunas principais de ambas
    cols = ['soc_6d', 'occupation_title']
    if 'automation_share_cai' in df_final.columns:
        cols += ['automation_share_cai', 'augmentation_share_cai', 'automation_index_cai', 'dominant_mode_cai']
    if 'automation_share_api' in df_final.columns:
        cols += ['automation_share_api', 'augmentation_share_api', 'automation_index_api', 'dominant_mode_api']
    
    # Se só tiver uma (como estava antes), usa os nomes originais
    if 'automation_share' in df_final.columns:
        cols = ['soc_6d', 'occupation_title', 'automation_share', 'augmentation_share', 'automation_index', 'dominant_mode', 'usage_volume']

    df_final[cols].to_csv(final_output, index=False)
    logger.info(f"Tabela final gerada em: {final_output}")

if __name__ == "__main__":
    process_occupations()
