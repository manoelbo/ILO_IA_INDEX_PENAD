"""
Script 07: Geração das 4 figuras principais
Entrada: data/processed/pnad_ilo_merged.csv
Saída: outputs/figures/*.png e *.pdf
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from src.utils.weighted_stats import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '07_figures.log'),
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
    """Carrega base consolidada"""
    df = pd.read_csv(DATA_PROCESSED / "pnad_ilo_merged.csv")
    logger.info(f"Dados carregados: {len(df):,} observações")
    return df

def figure1_distribuicao(df):
    """FIGURA 1: Distribuição da Exposição (dois painéis)"""
    
    logger.info("\n=== FIGURA 1: Distribuição da Exposição ===")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    mask = df['exposure_score'].notna()
    subset = df[mask]
    
    # Painel A: Histograma ponderado
    ax1.hist(
        subset['exposure_score'], 
        weights=subset['peso'] / 1e6,  # Em milhões
        bins=50, 
        edgecolor='black', 
        alpha=0.7, 
        color='steelblue'
    )
    
    media = weighted_mean(subset['exposure_score'], subset['peso'])
    ax1.axvline(media, color='red', linestyle='--', linewidth=2, 
                label=f'Média: {media:.3f}')
    
    ax1.set_xlabel('Score de Exposição à IA Generativa')
    ax1.set_ylabel('Trabalhadores (milhões)')
    ax1.set_title('(A) Distribuição Contínua da Exposição')
    ax1.legend()
    
    # Painel B: Barras por gradiente
    gradient_counts = subset.groupby('exposure_gradient')['peso'].sum() / 1e6
    gradient_order = ['Not Exposed', 'Minimal Exposure', 'Gradient 1-2', 'Gradient 3', 'Gradient 4 (Alta)']
    gradient_counts = gradient_counts.reindex([g for g in gradient_order if g in gradient_counts.index])
    
    colors = ['#2ca02c', '#98df8a', '#ffbb78', '#ff7f0e', '#d62728'][:len(gradient_counts)]
    ax2.barh(range(len(gradient_counts)), gradient_counts.values, 
             color=colors, edgecolor='black')
    ax2.set_yticks(range(len(gradient_counts)))
    ax2.set_yticklabels(gradient_counts.index)
    ax2.set_xlabel('Trabalhadores (milhões)')
    ax2.set_title('(B) Distribuição por Gradiente ILO')
    
    # Adicionar valores nas barras
    for i, v in enumerate(gradient_counts.values):
        ax2.text(v + 0.5, i, f'{v:.1f}M', va='center')
    
    plt.suptitle('Distribuição da Exposição à IA Generativa na Força de Trabalho Brasileira\n3º Trimestre 2025', 
                 fontsize=14, y=1.02)
    plt.tight_layout()
    
    # Salvar
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig1_distribuicao_exposicao.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"✓ Figura 1 salva em {OUTPUTS_FIGURES}")
    plt.close()

def figure2_heatmap(df):
    """FIGURA 2: Heatmap Região x Setor"""
    
    logger.info("\n=== FIGURA 2: Heatmap Região x Setor ===")
    
    def calc_weighted_mean(group):
        return weighted_mean(group['exposure_score'], group['peso'])
    
    pivot = df.groupby(['regiao', 'setor_agregado']).apply(calc_weighted_mean).unstack()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    sns.heatmap(
        pivot, 
        annot=True, 
        fmt='.3f', 
        cmap='YlOrRd',
        cbar_kws={'label': 'Score de Exposição'},
        ax=ax,
        linewidths=0.5
    )
    
    ax.set_title('Exposição à IA Generativa por Região e Setor\nBrasil - 3º Trimestre 2025', fontsize=14)
    ax.set_xlabel('Setor de Atividade')
    ax.set_ylabel('Região')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig2_heatmap_regiao_setor.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"✓ Figura 2 salva em {OUTPUTS_FIGURES}")
    plt.close()

def figure3_renda(df):
    """FIGURA 3: Perfil Salarial por Decil de Exposição"""
    
    logger.info("\n=== FIGURA 3: Renda por Exposição ===")
    
    mask = df['decil_exposure'].notna()
    subset = df[mask]
    
    renda_decil = subset.groupby('decil_exposure').apply(
        lambda x: weighted_mean(x['rendimento_habitual'], x['peso'])
    )
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(range(len(renda_decil)), renda_decil.values, 
                  color='teal', edgecolor='black', alpha=0.8)
    
    ax.set_xticks(range(len(renda_decil)))
    ax.set_xticklabels(renda_decil.index, rotation=0)
    ax.set_xlabel('Decil de Exposição à IA')
    ax.set_ylabel('Rendimento Médio Mensal (R$)')
    ax.set_title('Rendimento Médio por Decil de Exposição à IA Generativa\nBrasil - 3º Trimestre 2025')
    
    # Linha de tendência
    x_numeric = np.arange(1, len(renda_decil) + 1)
    slope, intercept, r_value, p_value, std_err = linregress(x_numeric, renda_decil.values)
    
    trend_line = slope * x_numeric + intercept
    ax.plot(range(len(renda_decil)), trend_line, 'r--', linewidth=2,
            label=f'Tendência (R² = {r_value**2:.3f})')
    
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Formatar valores no eixo Y
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
    
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig3_renda_exposicao.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"✓ Figura 3 salva em {OUTPUTS_FIGURES}")
    logger.info(f"Correlação exposição-renda: R² = {r_value**2:.3f}")
    plt.close()

def figure4_decomposicao(df):
    """FIGURA 4: Decomposição Demográfica (4 painéis)"""
    
    logger.info("\n=== FIGURA 4: Decomposição Demográfica ===")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    mask = df['exposure_gradient'].notna()
    subset = df[mask]
    
    gradient_order = ['Not Exposed', 'Minimal Exposure', 'Gradient 1-2', 'Gradient 3', 'Gradient 4 (Alta)']
    
    # Painel A: Por gênero
    gender_comp = subset.groupby(['exposure_gradient', 'sexo_texto'])['peso'].sum().unstack(fill_value=0)
    gender_comp = gender_comp.reindex([g for g in gradient_order if g in gender_comp.index])
    gender_pct = gender_comp.div(gender_comp.sum(axis=1), axis=0)
    
    gender_pct.plot(kind='barh', stacked=True, ax=axes[0,0], 
                   color=['lightblue', 'lightpink'], edgecolor='black')
    axes[0,0].set_title('(A) Composição por Gênero')
    axes[0,0].set_xlabel('Proporção')
    axes[0,0].legend(title='Sexo')
    
    # Painel B: Por raça
    race_comp = subset.groupby(['exposure_gradient', 'raca_agregada'])['peso'].sum().unstack(fill_value=0)
    race_comp = race_comp.reindex([g for g in gradient_order if g in race_comp.index])
    race_pct = race_comp.div(race_comp.sum(axis=1), axis=0)
    
    race_pct.plot(kind='barh', stacked=True, ax=axes[0,1], 
                 color=['#d4a574', '#8b6914', '#a9a9a9'], edgecolor='black')
    axes[0,1].set_title('(B) Composição por Raça')
    axes[0,1].set_xlabel('Proporção')
    axes[0,1].legend(title='Raça')
    
    # Painel C: Por formalidade
    formal_comp = subset.groupby(['exposure_gradient', 'formal'])['peso'].sum().unstack(fill_value=0)
    formal_comp = formal_comp.reindex([g for g in gradient_order if g in formal_comp.index])
    formal_comp.columns = ['Informal', 'Formal']
    formal_pct = formal_comp.div(formal_comp.sum(axis=1), axis=0)
    
    formal_pct.plot(kind='barh', stacked=True, ax=axes[1,0], 
                   color=['lightcoral', 'lightgreen'], edgecolor='black')
    axes[1,0].set_title('(C) Composição por Formalidade')
    axes[1,0].set_xlabel('Proporção')
    axes[1,0].legend(title='Vínculo')
    
    # Painel D: Por faixa etária
    age_comp = subset.groupby(['exposure_gradient', 'faixa_etaria'])['peso'].sum().unstack(fill_value=0)
    age_comp = age_comp.reindex([g for g in gradient_order if g in age_comp.index])
    age_pct = age_comp.div(age_comp.sum(axis=1), axis=0)
    
    cmap = plt.cm.viridis(np.linspace(0.2, 0.8, len(age_pct.columns)))
    age_pct.plot(kind='barh', stacked=True, ax=axes[1,1], 
                color=cmap, edgecolor='black')
    axes[1,1].set_title('(D) Composição por Faixa Etária')
    axes[1,1].set_xlabel('Proporção')
    axes[1,1].legend(title='Idade', bbox_to_anchor=(1.05, 1))
    
    plt.suptitle('Composição Demográfica por Gradiente de Exposição à IA\nBrasil - 3º Trimestre 2025', 
                 fontsize=14, y=1.02)
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig4_decomposicao_demografica.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"✓ Figura 4 salva em {OUTPUTS_FIGURES}")
    plt.close()

def generate_all_figures():
    """Gera todas as figuras"""
    
    logger.info("=" * 60)
    logger.info("GERAÇÃO DE FIGURAS - ETAPA 1")
    logger.info("=" * 60)
    
    df = load_data()
    
    figure1_distribuicao(df)
    figure2_heatmap(df)
    figure3_renda(df)
    figure4_decomposicao(df)
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ FIGURAS GERADAS COM SUCESSO!")
    logger.info(f"Arquivos salvos em: {OUTPUTS_FIGURES}")
    logger.info("=" * 60)

if __name__ == "__main__":
    generate_all_figures()
