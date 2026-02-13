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
        logging.FileHandler(OUTPUTS_LOGS / '03_hierarchical_imputation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def weighted_mean(values, weights):
    """Calcula a média ponderada segura."""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    v = values[mask]
    w = weights[mask]
    if w.sum() == 0:
        return v.mean()
    return np.average(v, weights=w)

def run_hierarchical_imputation():
    """
    Realiza a imputação hierárquica para preencher lacunas nos índices ISCO-08/COD.
    
    Estratégia:
    1. Match direto (já existente)
    2. Imputação pelo "Pai" (Subgrupo Principal - 3 dígitos)
    3. Imputação pelo "Avô" (Grande Grupo - 2 dígitos)
    4. Imputação de Zeros para grupos manuais/elementares específicos sem dados
    """
    logger.info("Iniciando Imputação Hierárquica...")
    
    # 1. Carregar Tabela COD com Matches Parciais (Output da Etapa 3)
    # Vamos usar o arquivo gerado via metodologia ESCO/Híbrida
    input_file = OUTPUTS_TABLES / "cod_automation_augmentation_index_esco.csv"
    if not input_file.exists():
        logger.error(f"Arquivo de input não encontrado: {input_file}")
        return

    df = pd.read_csv(input_file)
    logger.info(f"Total de ocupações COD carregadas: {len(df)}")
    
    # Adicionar colunas de controle se não existirem
    if 'imputation_method' not in df.columns:
        df['imputation_method'] = 'direct_match'
        # Se automation_index_cai for NaN, então não houve match direto válido
        df.loc[df['automation_index_cai'].isna(), 'imputation_method'] = 'missing'
    
    # Colunas de métricas que precisam ser imputadas
    metrics_cols = [
        'automation_share_cai', 'augmentation_share_cai', 'automation_index_cai',
        'automation_share_api', 'augmentation_share_api', 'automation_index_api'
    ]
    
    # Preparar dados para agregação
    # Precisamos da base ISCO original completa para calcular médias de grupos
    # O arquivo isco_automation_augmentation_index_esco.csv tem os dados por ISCO-08 4d
    isco_file = OUTPUTS_TABLES / "isco_automation_augmentation_index_esco.csv"
    df_isco = pd.read_csv(isco_file)
    df_isco['isco_08_code'] = df_isco['isco_08_code'].astype(str).str.zfill(4)
    
    # Criar colunas de grupos hierárquicos no ISCO
    df_isco['isco_3d'] = df_isco['isco_08_code'].str[:3]
    df_isco['isco_2d'] = df_isco['isco_08_code'].str[:2]
    
    # Calcular médias agregadas por nível (ponderadas pelo volume se possível)
    if 'usage_volume' not in df_isco.columns:
        df_isco['usage_volume'] = 1.0
        
    def get_group_averages(group_col):
        """Calcula médias ponderadas para um nível de agrupamento."""
        grouped = df_isco.groupby(group_col)
        results = {}
        for col in metrics_cols:
            if col in df_isco.columns:
                # Usar lambda para aplicar weighted_mean
                results[col] = grouped.apply(lambda x: weighted_mean(x[col], x['usage_volume']))
        return pd.DataFrame(results)

    logger.info("Calculando médias de grupos hierárquicos...")
    avg_3d = get_group_averages('isco_3d')
    avg_2d = get_group_averages('isco_2d')
    
    # --- PROCESSO DE IMPUTAÇÃO ---
    
    # Identificar linhas que precisam de imputação (sem dados em automation_index_cai)
    # Nota: Usamos 'cod_cod' para extrair a hierarquia, pois o 'isco_08_code' pode estar vazio
    df['cod_cod'] = df['cod_cod'].astype(str).str.zfill(4)
    df['cod_3d'] = df['cod_cod'].str[:3]
    df['cod_2d'] = df['cod_cod'].str[:2]
    
    mask_missing = df['automation_index_cai'].isna()
    logger.info(f"Ocupações sem dados diretos: {mask_missing.sum()} ({mask_missing.mean():.1%})")
    
    # Passo 2: Imputação Nível 3 Dígitos (Pai)
    # Iterar sobre os missing e tentar buscar no avg_3d
    logger.info("Executando imputação Nível 3 (Subgrupo)...")
    
    count_imp_3d = 0
    for idx in df[mask_missing].index:
        cod_3d = df.loc[idx, 'cod_3d']
        
        if cod_3d in avg_3d.index:
            # Temos média para este grupo!
            for col in metrics_cols:
                if col in avg_3d.columns:
                    df.loc[idx, col] = avg_3d.loc[cod_3d, col]
            
            df.loc[idx, 'imputation_method'] = 'hierarchical_3d_mean'
            df.loc[idx, 'imputation_note'] = f'Media do subgrupo {cod_3d}'
            count_imp_3d += 1
            
    logger.info(f"Imputados via Nível 3: {count_imp_3d}")
    
    # Atualizar máscara de missing
    mask_missing = df['automation_index_cai'].isna()
    
    # Passo 3: Imputação Nível 2 Dígitos (Avô)
    logger.info("Executando imputação Nível 2 (Grande Grupo)...")
    
    count_imp_2d = 0
    for idx in df[mask_missing].index:
        cod_2d = df.loc[idx, 'cod_2d']
        
        if cod_2d in avg_2d.index:
            for col in metrics_cols:
                if col in avg_2d.columns:
                    df.loc[idx, col] = avg_2d.loc[cod_2d, col]
            
            df.loc[idx, 'imputation_method'] = 'hierarchical_2d_mean'
            df.loc[idx, 'imputation_note'] = f'Media do grande grupo {cod_2d}'
            count_imp_2d += 1
            
    logger.info(f"Imputados via Nível 2: {count_imp_2d}")
    
    # Passo 4: Imputação de Zeros (Ocupações Elementares/Manuais sem dados)
    # Se ainda faltar dado e for de grupos tipicamente manuais (ex: 7, 8, 9, 6), assumir zero.
    # Grupos 1-5 tendem a ser mais cognitivos. Se não tiver dado lá, é estranho, mas também pode ser zero.
    # Vamos aplicar zero para todos os restantes, mas marcar como 'zero_imputation'
    
    mask_still_missing = df['automation_index_cai'].isna()
    count_zeros = mask_still_missing.sum()
    
    if count_zeros > 0:
        logger.info(f"Aplicando imputação de Zeros para {count_zeros} ocupações restantes...")
        # Preencher métricas com 0.0
        for col in metrics_cols:
            df.loc[mask_still_missing, col] = 0.0
            
        df.loc[mask_still_missing, 'imputation_method'] = 'zero_imputation_no_data'
        df.loc[mask_still_missing, 'imputation_note'] = 'Sem dados hierarquicos - Assumido impacto nulo'
        
        # Ajustar dominant_mode para 'none'
        df.loc[mask_still_missing, 'dominant_mode_cai'] = 'none'
        df.loc[mask_still_missing, 'dominant_mode_api'] = 'none'

    # Recalcular dominant_mode para os imputados (se não for zero)
    # Apenas para garantir consistência
    mask_imputed = df['imputation_method'].str.contains('hierarchical')
    if mask_imputed.sum() > 0:
        df.loc[mask_imputed, 'dominant_mode_cai'] = np.where(df.loc[mask_imputed, 'automation_index_cai'] > 0, "automation", "augmentation")
        df.loc[mask_imputed, 'dominant_mode_api'] = np.where(df.loc[mask_imputed, 'automation_index_api'] > 0, "automation", "augmentation")

    # Limpeza final
    # Preencher notas para match direto
    df.loc[df['imputation_method'] == 'direct_match', 'imputation_note'] = 'Match direto (4 digitos)'
    
    # Salvar Resultado Final Completo
    output_path = OUTPUTS_TABLES / "cod_automation_augmentation_index_final.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Tabela FINAL (100% Cobertura) salva em: {output_path}")
    
    # Estatísticas Finais
    stats = df['imputation_method'].value_counts()
    logger.info("\nResumo da Imputação:")
    for method, count in stats.items():
        logger.info(f"  {method}: {count} ({count/len(df):.1%})")

if __name__ == "__main__":
    run_hierarchical_imputation()
