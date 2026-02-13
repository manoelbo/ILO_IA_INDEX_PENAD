import pandas as pd
import numpy as np
import logging
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress

# Adicionar diretório raiz ao path para importações
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from etapa4_automation_augmentation_analysis.config.settings import *
from etapa4_automation_augmentation_analysis.src.utils.weighted_stats import *

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '05_advanced_visualizations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações globais de estilo
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
sns.set_style("whitegrid")

def load_data():
    """Carrega base consolidada da Etapa 4"""
    path = DATA_PROCESSED / "pnad_anthropic_merged.csv"
    df = pd.read_csv(path)
    logger.info(f"Dados carregados: {len(df):,} observações")
    return df

def define_impact_categories(df):
    """
    Define categorias de impacto (bins) para o Automation Index.
    - Alto Aprimoramento: < -0.3
    - Aprimoramento: -0.3 a -0.05
    - Neutro: -0.05 a 0.05
    - Automação: 0.05 a 0.3
    - Alta Automação: > 0.3
    """
    def classify(val):
        if pd.isna(val): return 'Sem Dados'
        if val < -0.3: return 'Alto Aprimoramento'
        if val < -0.05: return 'Aprimoramento'
        if val < 0.05: return 'Neutro'
        if val < 0.3: return 'Automação'
        return 'Alta Automação'
    
    df['ia_impact_category'] = df['automation_index_cai'].apply(classify)
    return df

def figure1_distribuicao_ia(df):
    """FIGURA 1: Distribuição do Impacto IA (Claude.ai)"""
    logger.info("\n=== FIGURA 1: Distribuição do Impacto IA ===")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Painel A: Histograma ponderado
    ax1.hist(
        df['automation_index_cai'].dropna(),
        weights=df.loc[df['automation_index_cai'].notna(), 'peso'] / 1e6,
        bins=40,
        edgecolor='black',
        alpha=0.7,
        color='teal'
    )
    media = weighted_mean(df['automation_index_cai'], df['peso'])
    ax1.axvline(media, color='red', linestyle='--', linewidth=2, label=f'Média: {media:.2f}')
    ax1.axvline(0, color='black', linewidth=1)
    ax1.set_xlabel('Automation Index (Claude.ai)')
    ax1.set_ylabel('Trabalhadores (milhões)')
    ax1.set_title('(A) Distribuição Contínua do Impacto IA')
    ax1.legend()
    
    # Painel B: Dominância por plataforma
    # Comparar Claude.ai vs 1P API (dominant mode)
    # Agrupar por dominante e somar pesos
    cai_dom = df.groupby('dominant_mode_cai')['peso'].sum() / 1e6
    api_dom = df.groupby('dominant_mode_api')['peso'].sum() / 1e6
    
    dom_df = pd.DataFrame({
        'Claude.ai': cai_dom,
        '1P API': api_dom
    }).fillna(0)
    
    dom_df.T.plot(kind='bar', ax=ax2, color=['#2ca02c', '#d62728', '#7f7f7f'], edgecolor='black')
    ax2.set_ylabel('Trabalhadores (milhões)')
    ax2.set_title('(B) Dominância por Plataforma (Consumidor vs Enterprise)')
    ax2.legend(title='Modo Dominante')
    plt.xticks(rotation=0)
    
    plt.suptitle('Distribuição do Impacto da IA Generativa na Força de Trabalho Brasileira', fontsize=16, y=1.02)
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig1_distribuicao_ia.{ext}', dpi=300, bbox_inches='tight')
    plt.close()

def figure2_heatmaps_setor_regiao(df):
    """FIGURA 2: Heatmaps Regionais e Setoriais"""
    logger.info("\n=== FIGURA 2: Heatmaps Regionais e Setoriais ===")
    
    def calc_weighted_mean_auto(group):
        return weighted_mean(group['automation_index_cai'], group['peso'])
    
    def calc_weighted_mean_aug(group):
        return weighted_mean(group['augmentation_share_cai'], group['peso'])

    pivot_auto = df.groupby(['regiao', 'setor_agregado']).apply(calc_weighted_mean_auto, include_groups=False).unstack()
    pivot_aug = df.groupby(['regiao', 'setor_agregado']).apply(calc_weighted_mean_aug, include_groups=False).unstack()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 16))
    
    sns.heatmap(pivot_auto, annot=True, fmt='.2f', cmap='RdYlGn_r', ax=ax1, linewidths=0.5, cbar_kws={'label': 'Automation Index'})
    ax1.set_title('(A) Índice de Automação Médio por Região e Setor')
    ax1.set_xlabel('')
    
    sns.heatmap(pivot_aug, annot=True, fmt='.1%', cmap='Greens', ax=ax2, linewidths=0.5, cbar_kws={'label': 'Augmentation Share'})
    ax2.set_title('(B) Participação de Aprimoramento (Augmentation) por Região e Setor')
    ax2.set_xlabel('Setor de Atividade')
    
    plt.suptitle('Mapas de Calor do Impacto IA no Brasil', fontsize=18, y=1.01)
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig2_heatmaps_ia.{ext}', dpi=300, bbox_inches='tight')
    plt.close()

def figure3_renda_decil_ia(df):
    """FIGURA 3: Rendimento Médio por Decil de Impacto IA"""
    logger.info("\n=== FIGURA 3: Renda por Decil de IA ===")
    
    # Criar decit de Automation Index
    df_valid = df[df['automation_index_cai'].notna()].copy()
    
    # Usar qcut com tratamento para duplicatas e rótulos
    try:
        # Tentar criar 10 decis
        res, bins = pd.qcut(df_valid['automation_index_cai'], 10, retbins=True, duplicates='drop')
        n_bins = len(bins) - 1
        labels = [f'D{i}' for i in range(1, n_bins + 1)]
        df_valid['decil_auto'] = pd.qcut(df_valid['automation_index_cai'], 10, labels=labels, duplicates='drop')
    except Exception as e:
        logger.warning(f"Erro ao criar decis: {e}. Usando quartis como fallback.")
        res, bins = pd.qcut(df_valid['automation_index_cai'], 4, retbins=True, duplicates='drop')
        n_bins = len(bins) - 1
        labels = [f'Q{i}' for i in range(1, n_bins + 1)]
        df_valid['decil_auto'] = pd.qcut(df_valid['automation_index_cai'], 4, labels=labels, duplicates='drop')
    
    renda_decil = df_valid.groupby('decil_auto', observed=True).apply(
        lambda x: weighted_mean(x['rendimento_todos'], x['peso']),
        include_groups=False
    )
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=renda_decil.index, y=renda_decil.values, color='steelblue', edgecolor='black', alpha=0.8, ax=ax)
    
    # Linha de tendência
    x_numeric = np.arange(len(renda_decil))
    slope, intercept, r_value, p_value, std_err = linregress(x_numeric, renda_decil.values)
    ax.plot(x_numeric, slope * x_numeric + intercept, 'r--', linewidth=2, label=f'Tendência (R² = {r_value**2:.3f})')
    
    ax.set_xlabel('Decis do Índice de Automação (D1=Mais Aprimoramento, D10=Mais Automação)')
    ax.set_ylabel('Rendimento Médio Mensal (R$)')
    ax.set_title('Rendimento Médio por Decil de Automação IA\nBrasil - PNAD 2025')
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
    
    plt.tight_layout()
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig3_renda_decil_ia.{ext}', dpi=300, bbox_inches='tight')
    plt.close()

def figure4_decomposicao_demografica_ia(df):
    """FIGURA 4: Decomposição Demográfica por Categoria de Impacto"""
    logger.info("\n=== FIGURA 4: Decomposição Demográfica IA ===")
    
    df = define_impact_categories(df)
    cat_order = ['Alto Aprimoramento', 'Aprimoramento', 'Neutro', 'Automação', 'Alta Automação']
    df_subset = df[df['ia_impact_category'] != 'Sem Dados'].copy()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Painel A: Gênero
    gender = df_subset.groupby(['ia_impact_category', 'sexo_texto'], observed=True)['peso'].sum().unstack()
    gender = gender.reindex(cat_order)
    gender_pct = gender.div(gender.sum(axis=1), axis=0)
    gender_pct.plot(kind='barh', stacked=True, ax=axes[0,0], color=['lightblue', 'lightpink'], edgecolor='black')
    axes[0,0].set_title('(A) Composição por Gênero')
    axes[0,0].legend(title='Sexo')
    
    # Painel B: Escolaridade
    educ = df_subset.groupby(['ia_impact_category', 'nivel_instrucao'], observed=True)['peso'].sum().unstack()
    educ = educ.reindex(cat_order)
    educ_pct = educ.div(educ.sum(axis=1), axis=0)
    educ_pct.plot(kind='barh', stacked=True, ax=axes[0,1], cmap='viridis', edgecolor='black')
    axes[0,1].set_title('(B) Composição por Nível de Instrução')
    axes[0,1].legend(title='Escolaridade', bbox_to_anchor=(1.05, 1))
    
    # Painel C: Raça
    race = df_subset.groupby(['ia_impact_category', 'raca_agregada'], observed=True)['peso'].sum().unstack()
    race = race.reindex(cat_order)
    race_pct = race.div(race.sum(axis=1), axis=0)
    race_pct.plot(kind='barh', stacked=True, ax=axes[1,0], color=['#d4a574', '#8b6914', '#a9a9a9'], edgecolor='black')
    axes[1,0].set_title('(C) Composição por Raça')
    axes[1,0].legend(title='Raça')
    
    # Painel D: Formalidade
    formal = df_subset.groupby(['ia_impact_category', 'formal'], observed=True)['peso'].sum().unstack()
    formal = formal.reindex(cat_order)
    formal.columns = ['Informal', 'Formal']
    formal_pct = formal.div(formal.sum(axis=1), axis=0)
    formal_pct.plot(kind='barh', stacked=True, ax=axes[1,1], color=['lightcoral', 'lightgreen'], edgecolor='black')
    axes[1,1].set_title('(D) Composição por Formalidade')
    axes[1,1].legend(title='Vínculo')
    
    plt.suptitle('Perfil Demográfico por Categoria de Impacto IA Generativa', fontsize=18, y=1.02)
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig4_decomposicao_ia.{ext}', dpi=300, bbox_inches='tight')
    plt.close()

def figure5_comparativo_ilo_anthropic(df):
    """FIGURA 5: Anthropic vs ILO (Validação)"""
    logger.info("\n=== FIGURA 5: Anthropic vs ILO ===")
    
    # Agrupar por ocupação para scatterplot
    occ_df = df.groupby('cod_ocupacao').agg({
        'automation_index_cai': lambda x: weighted_mean(x, df.loc[x.index, 'peso']),
        'exposure_score': lambda x: weighted_mean(x, df.loc[x.index, 'peso']),
        'peso': 'sum'
    }).dropna().reset_index()
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=occ_df, x='exposure_score', y='automation_index_cai', size='peso', sizes=(20, 500), alpha=0.5, color='purple')
    
    # Regressão
    slope, intercept, r_value, p_value, std_err = linregress(occ_df['exposure_score'], occ_df['automation_index_cai'])
    plt.plot(occ_df['exposure_score'], slope * occ_df['exposure_score'] + intercept, 'r--', label=f'Ajuste Linear (R = {r_value:.2f})')
    
    plt.axhline(0, color='black', linewidth=1, alpha=0.3)
    plt.xlabel('ILO Exposure Score (Potencial de Exposição)')
    plt.ylabel('Anthropic Automation Index (Tipo de Impacto)')
    plt.title('Validação Cruzada: Exposição Geral (ILO) vs. Tipo de Impacto (Anthropic)', fontsize=14)
    plt.legend()
    
    plt.tight_layout()
    for ext in ['png', 'pdf']:
        plt.savefig(OUTPUTS_FIGURES / f'fig5_validacao_ilo_anthropic.{ext}', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    logger.info("=" * 60)
    logger.info("GERAÇÃO DE VISUALIZAÇÕES AVANÇADAS - ETAPA 4")
    logger.info("=" * 60)
    
    df = load_data()
    
    figure1_distribuicao_ia(df)
    figure2_heatmaps_setor_regiao(df)
    figure3_renda_decil_ia(df)
    figure4_decomposicao_demografica_ia(df)
    figure5_comparativo_ilo_anthropic(df)
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ VISUALIZAÇÕES GERADAS COM SUCESSO!")
    logger.info(f"Arquivos salvos em: {OUTPUTS_FIGURES}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
