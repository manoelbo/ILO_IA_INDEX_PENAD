"""
Script 05: Merge final e criação da base consolidada
Entrada: Dados do crosswalk
Saída: data/processed/pnad_ilo_merged.csv
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

# Importar módulo local
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("crosswalk", Path(__file__).parent / "04_crosswalk.py")
crosswalk_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crosswalk_module)
run_crosswalk = crosswalk_module.run_crosswalk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '05_merge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def add_gradient_classification(df):
    """Adiciona classificação por gradiente ILO"""
    
    # Definir thresholds baseados na metodologia ILO
    def classify_gradient(score):
        if pd.isna(score):
            return 'Sem classificação'
        elif score < 0.22:
            return 'Not Exposed'
        elif score < 0.36:
            return 'Minimal Exposure'
        elif score < 0.45:
            return 'Gradient 1-2'
        elif score < 0.55:
            return 'Gradient 3'
        else:
            return 'Gradient 4 (Alta)'
    
    df['exposure_gradient'] = df['exposure_score'].apply(classify_gradient)
    
    logger.info("\nDistribuição por gradiente:")
    for grad, peso in df.groupby('exposure_gradient')['peso'].sum().sort_values(ascending=False).items():
        logger.info(f"  {grad}: {peso/1e6:.1f} milhões")
    
    return df

def add_quintiles(df):
    """Adiciona quintis e decis de exposição"""
    
    # Filtrar apenas com score válido
    mask = df['exposure_score'].notna()
    
    # Quintis
    df.loc[mask, 'quintil_exposure'] = pd.qcut(
        df.loc[mask, 'exposure_score'],
        q=5,
        labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)'],
        duplicates='drop'
    )
    
    # Decis
    df.loc[mask, 'decil_exposure'] = pd.qcut(
        df.loc[mask, 'exposure_score'],
        q=10,
        labels=[f'D{i}' for i in range(1, 11)],
        duplicates='drop'
    )
    
    return df

def create_sector_aggregation(df):
    """Cria agregação setorial simplificada"""
    
    # Mapear CNAE para setores agregados (ajustar conforme códigos reais)
    setor_map = {
        # Agricultura
        '01': 'Agropecuária', '02': 'Agropecuária', '03': 'Agropecuária',
        # Indústria
        '05': 'Indústria', '06': 'Indústria', '07': 'Indústria', '08': 'Indústria',
        '10': 'Indústria', '11': 'Indústria', '12': 'Indústria', '13': 'Indústria',
        '14': 'Indústria', '15': 'Indústria', '16': 'Indústria', '17': 'Indústria',
        '18': 'Indústria', '19': 'Indústria', '20': 'Indústria', '21': 'Indústria',
        '22': 'Indústria', '23': 'Indústria', '24': 'Indústria', '25': 'Indústria',
        '26': 'Indústria', '27': 'Indústria', '28': 'Indústria', '29': 'Indústria',
        '30': 'Indústria', '31': 'Indústria', '32': 'Indústria', '33': 'Indústria',
        # Construção
        '41': 'Construção', '42': 'Construção', '43': 'Construção',
        # Comércio
        '45': 'Comércio', '46': 'Comércio', '47': 'Comércio',
        # Serviços
        '49': 'Serviços', '50': 'Serviços', '51': 'Serviços', '52': 'Serviços',
        '53': 'Serviços', '55': 'Serviços', '56': 'Serviços',
        # TIC / Serviços especializados
        '58': 'TIC e Serviços Prof.', '59': 'TIC e Serviços Prof.', '60': 'TIC e Serviços Prof.',
        '61': 'TIC e Serviços Prof.', '62': 'TIC e Serviços Prof.', '63': 'TIC e Serviços Prof.',
        '64': 'TIC e Serviços Prof.', '65': 'TIC e Serviços Prof.', '66': 'TIC e Serviços Prof.',
        '69': 'TIC e Serviços Prof.', '70': 'TIC e Serviços Prof.', '71': 'TIC e Serviços Prof.',
        '72': 'TIC e Serviços Prof.', '73': 'TIC e Serviços Prof.', '74': 'TIC e Serviços Prof.',
        '75': 'TIC e Serviços Prof.',
        # Administração pública
        '84': 'Administração Pública',
        # Educação
        '85': 'Educação',
        # Saúde
        '86': 'Saúde', '87': 'Saúde', '88': 'Saúde',
    }
    
    # Extrair 2 primeiros dígitos do grupamento de atividade
    if df['grupamento_atividade'].dtype == 'object':
        df['cnae_2d'] = df['grupamento_atividade'].astype(str).str[:2]
    else:
        df['cnae_2d'] = df['grupamento_atividade'].astype(str).str[:2]
    
    df['setor_agregado'] = df['cnae_2d'].map(setor_map).fillna('Outros Serviços')
    
    return df

def merge_and_finalize():
    """Executa merge final e salva base consolidada"""
    
    logger.info("=== MERGE FINAL ===\n")
    
    # Executar crosswalk
    df, coverage = run_crosswalk()
    
    # Adicionar classificações
    df = add_gradient_classification(df)
    df = add_quintiles(df)
    df = create_sector_aggregation(df)
    
    # Estatísticas finais
    logger.info("\n=== BASE FINAL ===")
    logger.info(f"Total de observações: {len(df):,}")
    logger.info(f"Com score de exposição: {df['exposure_score'].notna().sum():,}")
    logger.info(f"Cobertura: {df['exposure_score'].notna().mean():.1%}")
    logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")
    
    # Colunas finais
    cols_output = [
        'ano', 'trimestre', 'sigla_uf', 'regiao',
        'sexo', 'sexo_texto', 'idade', 'faixa_etaria',
        'raca_cor', 'raca_agregada', 'nivel_instrucao',
        'cod_ocupacao', 'grande_grupo',
        'grupamento_atividade', 'setor_agregado',
        'posicao_ocupacao', 'formal',
        'rendimento_habitual', 'rendimento_winsor', 'rendimento_todos',
        'horas_trabalhadas', 'peso',
        'exposure_score', 'exposure_gradient', 'match_level',
        'quintil_exposure', 'decil_exposure'
    ]
    
    df_final = df[[c for c in cols_output if c in df.columns]]
    
    # Salvar
    output_path = DATA_PROCESSED / "pnad_ilo_merged.csv"
    df_final.to_csv(output_path, index=False)
    logger.info(f"\n✓ Base final salva em: {output_path}")
    logger.info(f"Tamanho: {df_final.memory_usage(deep=True).sum()/1e6:.1f} MB")
    
    return df_final

if __name__ == "__main__":
    df = merge_and_finalize()
    print("\n✓ Merge concluído com sucesso!")
