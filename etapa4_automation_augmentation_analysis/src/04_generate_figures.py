import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

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
        logging.FileHandler(OUTPUTS_LOGS / '04_generate_figures.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Estilo Global
sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 300

def plot_automation_augmentation_distribution(df):
    """Cria gráfico de barras mostrando a dualidade por Grande Grupo."""
    logger.info("Plotando distribuição por Grande Grupo...")
    
    # Criar coluna de nome do grupo
    df['grande_grupo_nome'] = df['cod_ocupacao'].astype(str).str[0].map(GRANDES_GRUPOS)
    
    # Calcular médias ponderadas
    def agg_weighted(x):
        return weighted_mean(x, df.loc[x.index, 'peso'])

    summary = df.groupby('grande_grupo_nome').agg({
        'automation_share_cai': agg_weighted,
        'augmentation_share_cai': agg_weighted
    }).reset_index()
    
    # Derreter para formato long para o seaborn
    plot_df = summary.melt(id_vars='grande_grupo_nome', 
                          value_vars=['automation_share_cai', 'augmentation_share_cai'],
                          var_name='Tipo', value_name='Share')
    
    plot_df['Tipo'] = plot_df['Tipo'].map({
        'automation_share_cai': 'Automação (Substituição)',
        'augmentation_share_cai': 'Aprimoramento (Augmentation)'
    })

    plt.figure(figsize=(12, 8))
    sns.barplot(data=plot_df, y='grande_grupo_nome', x='Share', hue='Tipo', palette='RdYlGn_r')
    plt.title('Potencial de Automação vs. Aprimoramento por Grande Grupo Ocupacional\nBrasil - PNAD 2025', fontsize=14)
    plt.xlabel('Participação Média nas Tarefas (%)')
    plt.ylabel('')
    plt.legend(title='Impacto IA', loc='lower right')
    plt.tight_layout()
    plt.savefig(OUTPUTS_FIGURES / "distribuicao_ia_grande_grupo.png")
    plt.close()

def plot_salary_vs_ia(df):
    """Scatterplot de Salário vs. Automation Index."""
    logger.info("Plotando Salário vs. Impacto IA...")
    
    # Agrupar por ocupação para não poluir o scatterplot individual
    def agg_weighted(x):
        return weighted_mean(x, df.loc[x.index, 'peso'])

    occ_df = df.groupby('cod_ocupacao').agg({
        'automation_index_cai': agg_weighted,
        'rendimento_todos': agg_weighted,
        'peso': 'sum'
    }).reset_index()
    
    # Filtrar rendimentos muito baixos ou NaNs
    occ_df = occ_df[occ_df['rendimento_todos'] > 0]

    plt.figure(figsize=(10, 7))
    sns.scatterplot(data=occ_df, x='automation_index_cai', y='rendimento_todos', 
                    size='peso', sizes=(20, 500), alpha=0.6, color='teal')
    
    # Linha de tendência
    sns.regplot(data=occ_df, x='automation_index_cai', y='rendimento_todos', 
                scatter=False, color='red', line_kws={"linestyle": "--"})
    
    plt.yscale('log') # Escala logarítmica para salário
    plt.title('Relação entre Rendimento Médio e Índice de Automação\n(Nível de Ocupação COD)', fontsize=14)
    plt.xlabel('Automation Index (Negativo = Aprimoramento | Positivo = Automação)')
    plt.ylabel('Rendimento Médio (Escala Log)')
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.tight_layout()
    plt.savefig(OUTPUTS_FIGURES / "salario_vs_ia_index.png")
    plt.close()

def plot_regional_impact(df):
    """Mapa de calor regional do impacto IA."""
    logger.info("Plotando impacto regional...")
    
    def agg_weighted(x):
        return weighted_mean(x, df.loc[x.index, 'peso'])

    regiao_df = df.groupby('regiao').agg({
        'automation_index_cai': agg_weighted
    }).sort_values('automation_index_cai').reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(data=regiao_df, x='automation_index_cai', y='regiao', palette='coolwarm')
    plt.axvline(0, color='black', lw=1)
    plt.title('Índice de Automação por Região do Brasil', fontsize=14)
    plt.xlabel('Automation Index Médio')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(OUTPUTS_FIGURES / "impacto_ia_por_regiao.png")
    plt.close()

def run_figures():
    """Gera todos os gráficos da Etapa 4."""
    merged_path = DATA_PROCESSED / "pnad_anthropic_merged.csv"
    if not merged_path.exists():
        logger.error(f"Base consolidada não encontrada: {merged_path}")
        return
    
    df = pd.read_csv(merged_path)
    
    plot_automation_augmentation_distribution(df)
    plot_salary_vs_ia(df)
    plot_regional_impact(df)
    
    logger.info("Gráficos gerados com sucesso!")

if __name__ == "__main__":
    run_figures()
