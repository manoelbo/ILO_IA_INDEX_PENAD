import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para importações
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from etapa4_automation_augmentation_analysis.config.settings import *
from etapa4_automation_augmentation_analysis.src.utils.weighted_stats import weighted_mean

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '02_generate_tables.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_summary_table(df, group_col, group_label):
    """Gera tabela resumo por um grupamento específico."""
    logger.info(f"Gerando resumo por {group_label}...")
    
    # Calcular médias ponderadas
    def agg_weighted(x):
        return weighted_mean(x, df.loc[x.index, 'peso'])

    summary = df.groupby(group_col).agg({
        'automation_index_cai': agg_weighted,
        'automation_share_cai': agg_weighted,
        'augmentation_share_cai': agg_weighted,
        'exposure_score': agg_weighted, # ILO score para comparação
        'rendimento_todos': agg_weighted,
        'peso': 'sum'
    }).reset_index()
    
    # Renomear colunas
    summary.columns = [
        group_label, 'Automation Index (Cai)', 'Automation Share %', 'Augmentation Share %',
        'ILO Exposure Score', 'Rendimento Médio', 'População Representada'
    ]
    
    # Ordenar por Automation Index descrescente
    summary = summary.sort_values('Automation Index (Cai)', ascending=False)
    
    return summary

def run_tables():
    """Gera todas as tabelas estatísticas da Etapa 4."""
    
    # 1. Carregar Dados Unificados
    merged_path = DATA_PROCESSED / "pnad_anthropic_merged.csv"
    if not merged_path.exists():
        logger.error(f"Base consolidada não encontrada: {merged_path}. Execute o Script 01 primeiro.")
        return
    
    df = pd.read_csv(merged_path)
    logger.info(f"Dados carregados: {len(df):,} observações")

    # 2. Tabela por Perfil Demográfico
    # Gênero
    demog_sexo = generate_summary_table(df, 'sexo_texto', 'Sexo')
    demog_sexo.to_csv(OUTPUTS_TABLES / "tabela_por_sexo.csv", index=False)
    
    # Raça
    demog_raca = generate_summary_table(df, 'raca_agregada', 'Raça/Cor')
    demog_raca.to_csv(OUTPUTS_TABLES / "tabela_por_raca.csv", index=False)
    
    # Escolaridade
    demog_educ = generate_summary_table(df, 'nivel_instrucao', 'Nível de Instrução')
    demog_educ.to_csv(OUTPUTS_TABLES / "tabela_por_escolaridade.csv", index=False)

    # 3. Tabela por Região
    regiao_uf = generate_summary_table(df, 'regiao', 'Região')
    regiao_uf.to_csv(OUTPUTS_TABLES / "tabela_por_regiao.csv", index=False)

    # 4. Tabela por Grande Grupo Ocupacional
    # Criar coluna de nome do grupo
    df['grande_grupo_nome'] = df['cod_ocupacao'].astype(str).str[0].map(GRANDES_GRUPOS)
    gg_table = generate_summary_table(df, 'grande_grupo_nome', 'Grande Grupo Ocupacional')
    gg_table.to_csv(OUTPUTS_TABLES / "tabela_por_grande_grupo.csv", index=False)

    # 5. Tabela Detalhada por Ocupação (Similar ao Script 08 da Etapa 1)
    # Aqui unificamos as informações de Automação/Aumentação com as de Exposição ILO
    logger.info("Gerando tabela detalhada por ocupação...")
    
    # Precisamos das descrições das ocupações da estrutura COD
    # (Para simplificar, usaremos as que já estão no df ou carregaremos a estrutura)
    # Vamos agrupar por cod_ocupacao e pegar as médias
    
    occ_detailed = df.groupby('cod_ocupacao').agg({
        'automation_index_cai': agg_weighted_mean_local(df),
        'automation_share_cai': agg_weighted_mean_local(df),
        'augmentation_share_cai': agg_weighted_mean_local(df),
        'exposure_score': agg_weighted_mean_local(df),
        'rendimento_todos': agg_weighted_mean_local(df),
        'peso': 'sum',
        'imputation_method': 'first'
    }).reset_index()
    
    occ_detailed.to_csv(OUTPUTS_TABLES / "tabela_detalhada_ocupacoes_ia.csv", index=False)
    
    logger.info("Tabelas geradas com sucesso!")

def agg_weighted_mean_local(df):
    return lambda x: weighted_mean(x, df.loc[x.index, 'peso'])

if __name__ == "__main__":
    run_tables()
