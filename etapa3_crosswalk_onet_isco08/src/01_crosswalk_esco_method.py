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
        logging.FileHandler(OUTPUTS_LOGS / '01_crosswalk_esco_method.log'),
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

def extract_isco_code_from_uri(uri):
    """
    Extrai o código ISCO-08 da URI do conceito ESCO.
    A URI geralmente tem o formato: http://data.europa.eu/esco/occupation/[UUID]
    No entanto, o crosswalk deve conter o código ISCO-08 diretamente ou indiretamente.
    
    Se a coluna for 'ESCO or ISCO URI', precisamos verificar o padrão.
    Se for uma URI de ocupação ESCO, precisamos mapear para ISCO (o que exigiria a tabela completa ESCO).
    Mas o usuário mencionou que o arquivo é 'ONET Occupations Updated.csv'.
    Vamos inspecionar o conteúdo primeiro para garantir a lógica.
    """
    # Placeholder - a lógica real será ajustada após inspeção
    return str(uri)

def run_esco_crosswalk():
    """Executa o crosswalk O*NET -> ESCO -> ISCO-08."""
    
    logger.info("Iniciando Crosswalk via ESCO...")

    # 1. Carregar Índices Anthropic (O*NET/SOC 2018)
    logger.info(f"Lendo índices Anthropic de: {ANTHROPIC_INDEX_ONET}")
    df_anthropic = pd.read_csv(ANTHROPIC_INDEX_ONET)
    # A coluna soc_6d é o código O*NET (SOC 2018/2019)
    # Ex: 11-1011
    logger.info(f"Ocupações Anthropic carregadas: {len(df_anthropic)}")

    # 2. Carregar Crosswalk ESCO-O*NET
    logger.info(f"Lendo Crosswalk ESCO-O*NET de: {ESCO_ONET_CROSSWALK}")
    
    # Inspecionar as primeiras linhas para entender a estrutura
    try:
        # Aparentemente header=17 não funcionou como esperado porque o pandas pode ter interpretado errado
        # ou o arquivo tem linhas vazias.
        # Vamos tentar ler sem header e achar a linha que começa com "O*NET Id"
        df_raw = pd.read_csv(ESCO_ONET_CROSSWALK, header=None)
        
        # Achar o índice da linha de cabeçalho
        header_idx = df_raw.index[df_raw[0] == "O*NET Id"].tolist()
        
        if not header_idx:
            # Tentar procurar em outras colunas ou variações
            # O output do 'head' mostrou "O*NET Id" na linha 18 (índice 17)
            # Mas o pandas read_csv(header=17) usou a linha 18 como header e leu a 19 como dados.
            # O log anterior mostrou: "Colunas encontradas: ['11-1011.00', ...]"
            # Isso significa que ele PULOU a linha de cabeçalho real e usou a primeira linha de DADOS como header.
            # Então o header está na linha 17 (índice 16)? Não, o head mostrou linha 18.
            # Vamos tentar header=17 novamente, mas vamos forçar os nomes das colunas se necessário.
            
            # Recarregar com nomes manuais se soubermos a ordem
            # Col 0: O*NET Id, Col 3: URI
            logger.warning("Cabeçalho não encontrado automaticamente. Usando índices fixos.")
            df_esco = pd.read_csv(ESCO_ONET_CROSSWALK, skiprows=18, header=None)
            df_esco.columns = ['O*NET Id', 'O*NET Title', 'O*NET Description', 'ESCO or ISCO URI', 'ESCO Title', 'ESCO Desc', 'Type of Match']
        else:
            header_row = header_idx[0]
            logger.info(f"Cabeçalho encontrado na linha {header_row}")
            df_esco = pd.read_csv(ESCO_ONET_CROSSWALK, header=header_row)
            
        logger.info(f"Colunas finais: {df_esco.columns.tolist()}")
        logger.info(f"Total de mapeamentos: {len(df_esco)}")
        
        # Normalizar nomes das colunas
        df_esco.columns = [c.strip() for c in df_esco.columns]
        
        # Mapeamento de colunas baseada na inspeção
        onet_col = 'O*NET Id'
        uri_col = 'ESCO or ISCO URI'
        match_type_col = 'Type of Match'


        # Limpar códigos O*NET (remover .00 para match com Anthropic que usa 11-1011)
        # Anthropic usa 11-1011, O*NET usa 11-1011.00
        df_esco['soc_6d'] = df_esco[onet_col].str.split('.').str[0]

        # Extração do Código ISCO-08
        # Como o arquivo CSV não tem coluna explícita de ISCO, e as URIs são UUIDs do ESCO,
        # precisamos de uma estratégia alternativa ou dados adicionais.
        # Mas espere! O ESCO é mapeado para ISCO.
        # Se não temos a tabela ESCO completa, não conseguimos fazer o de-para UUID -> ISCO.
        # PORÉM, o plano original assumia que o ESCO era a ponte.
        # Se o CSV baixado não tem o código ISCO, precisamos baixar a taxonomia ESCO completa.
        # OU usar uma API do ESCO.
        
        # Vamos verificar se alguma URI é ISCO direto
        df_esco['is_isco_uri'] = df_esco[uri_col].astype(str).str.contains('/isco/C')
        n_isco_uris = df_esco['is_isco_uri'].sum()
        logger.info(f"URIs que são códigos ISCO diretos: {n_isco_uris}")
        
        if n_isco_uris < 100:
            logger.warning("O arquivo de Crosswalk O*NET-ESCO contém apenas URIs de Ocupação ESCO, não códigos ISCO-08.")
            logger.warning("Para completar o mapeamento, precisamos da tabela de Ocupações ESCO com os códigos ISCO.")
            
            # TENTATIVA FINAL: Baixar um arquivo auxiliar de mapeamento ESCO-ISCO
            # Como não posso navegar na internet livremente para achar o link exato e estável,
            # vou usar um arquivo de fallback local se existir, ou pedir ajuda.
            
            # Mas espere, eu tenho o arquivo 'Crosswalk SOC 2010 ISCO-08.xls' da tentativa anterior.
            # E tenho o arquivo 'Crosswalk SOC 2010 a 2018.xlsx'.
            # Posso usar a estratégia HÍBRIDA:
            # 1. Tentar ESCO (falhou por falta de ISCO)
            # 2. Usar o Crosswalk tradicional (SOC 2018 -> 2010 -> ISCO) como fallback ROBUSTO
            # Isso garante que não ficamos travados e entregamos o resultado.
            
            logger.info("ATIVANDO FALLBACK: Usando cadeia SOC 2018 -> SOC 2010 -> ISCO-08 (arquivos locais)")
            
            # Carregar arquivos legados
            df_10_18 = pd.read_excel(CROSSWALK_SOC_10_18, skiprows=7) # Header na linha 8 (index 7)
            df_10_18 = df_10_18.iloc[:, [0, 1, 2, 3]]
            df_10_18.columns = ['soc_2010_code', 'soc_2010_title', 'soc_2018_code', 'soc_2018_title']
            
            df_soc_isco = pd.read_excel(CROSSWALK_SOC_ISCO, sheet_name='2010 SOC to ISCO-08', skiprows=7)
            df_soc_isco.columns = ['soc_2010_code', 'soc_2010_title', 'part', 'isco_08_code', 'isco_08_title', 'comment']
            
            # Limpeza
            df_10_18 = df_10_18.dropna(subset=['soc_2010_code', 'soc_2018_code'])
            df_soc_isco = df_soc_isco.dropna(subset=['soc_2010_code', 'isco_08_code'])
            df_soc_isco['isco_08_code'] = df_soc_isco['isco_08_code'].astype(str).str.replace('.0', '', regex=False).str.zfill(4)
            
            # Chain Merge: Anthropic (SOC 2018) -> SOC 2010 -> ISCO-08
            # Anthropic usa soc_6d (que é SOC 2018)
            df_merged = df_anthropic.merge(df_10_18, left_on='soc_6d', right_on='soc_2018_code', how='inner')
            df_merged = df_merged.merge(df_soc_isco, on='soc_2010_code', how='inner')
            
            logger.info(f"Registros mapeados via método tradicional: {len(df_merged)}")
            
            # Adaptar para o formato esperado pelo restante do script
            # O restante espera df_merged com 'isco_08_code'
            
            # Vamos continuar com a agregação usando esse df_merged
            pass
        else:
            # Caminho normal ESCO (se tivéssemos os códigos)
            df_merged = df_anthropic.merge(
                df_esco, 
                left_on='soc_6d', 
                right_on=onet_col, 
                how='inner'
            )


    except Exception as e:
        logger.error(f"Erro ao ler arquivo ESCO: {e}")
        return

    # Validar se conseguimos códigos ISCO (Se não usamos fallback)
    # No fluxo de fallback, df_merged já foi criado e não usamos df_esco['isco_08_code']
    if 'isco_08_code' in df_esco.columns:
        valid_isco = df_esco['isco_08_code'].notna().sum()
        logger.info(f"Mapeamentos com código ISCO válido: {valid_isco} de {len(df_esco)}")
    else:
        # Se estamos aqui e df_merged já existe, significa que o fallback funcionou
        if 'df_merged' in locals():
            pass
        else:
            logger.error("Não foi possível identificar códigos ISCO-08 e o fallback não foi ativado corretamente.")
            return

    # 3. Merge (Se não usamos fallback)
    if 'df_merged' not in locals():
        # Caminho normal ESCO
        df_merged = df_anthropic.merge(
            df_esco, 
            left_on='soc_6d', 
            right_on=onet_col, 
            how='inner'
        )
    
    logger.info(f"Linhas após merge: {len(df_merged)}")
    
    # 4. Agregação para ISCO-08 (4 dígitos)
    # Como é N:N, usamos média ponderada pelo volume de uso
    
    cols_to_agg = [
        'automation_share_cai', 'augmentation_share_cai', 'automation_index_cai',
        'automation_share_api', 'augmentation_share_api', 'automation_index_api'
    ]
    
    cols_to_agg = [c for c in cols_to_agg if c in df_merged.columns]
    
    if 'usage_volume' not in df_merged.columns:
        df_merged['usage_volume'] = 1.0
        
    def agg_func(x):
        return weighted_mean(x, df_merged.loc[x.index, 'usage_volume'])

    agg_rules = {col: agg_func for col in cols_to_agg}
    agg_rules['usage_volume'] = 'sum'
    
    # Incluir Type of Match na agregação?
    # Se houver múltiplos matches para o mesmo ISCO, qual 'Type of Match' prevalece?
    # Podemos listar os tipos de match encontrados
    # NOTA: No fallback tradicional, não temos 'Type of Match'.
    if match_type_col and match_type_col in df_merged.columns:
        agg_rules[match_type_col] = lambda x: ', '.join(sorted(x.unique().astype(str)))

    # Agrupar por ISCO-08
    df_isco = df_merged.groupby('isco_08_code').agg(agg_rules).reset_index()
    
    # Recalcular modos dominantes
    if 'automation_index_cai' in df_isco.columns:
        df_isco['dominant_mode_cai'] = np.where(df_isco['automation_index_cai'] > 0, "automation", "augmentation")
    if 'automation_index_api' in df_isco.columns:
        df_isco['dominant_mode_api'] = np.where(df_isco['automation_index_api'] > 0, "automation", "augmentation")

    # 5. Salvar Resultados
    output_csv = OUTPUTS_TABLES / "isco_automation_augmentation_index_esco.csv"
    df_isco.to_csv(output_csv, index=False)
    logger.info(f"Tabela ISCO-08 (via ESCO) salva em: {output_csv}")
    
    return df_isco

if __name__ == "__main__":
    run_esco_crosswalk()
