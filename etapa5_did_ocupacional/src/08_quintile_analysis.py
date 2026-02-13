"""
Script 08: Análise por Quintis de Exposição
============================================

Estatísticas descritivas por quintil de exposição à IA.

Entrada: data/processed/pnad_panel_did_ready.parquet
Saídas:
- outputs/tables/quintile_characteristics_pre.csv
- outputs/tables/quintile_characteristics_pre.tex
- outputs/figures/exposure_distribution_by_quintile.png
- outputs/figures/outcomes_by_quintile.png
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from utils.weighted_stats import weighted_mean

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '08_quintile_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def compute_quintile_statistics(df):
    """Calcula estatísticas por quintil (período pré)"""

    logger.info("Computando estatísticas por quintil...")

    # Filtrar pré
    df_pre = df[df['post'] == 0].copy()

    stats = []

    quintiles = ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']

    for quintil in quintiles:
        subset = df_pre[df_pre['quintil_exp'] == quintil]

        if len(subset) == 0:
            continue

        # Exposição média
        exp_media = weighted_mean(subset['exposure_score'], subset['peso'])

        # População
        pop = subset['peso'].sum() / 1e6

        # Demografia
        idade_media = weighted_mean(subset['idade'], subset['peso'])
        pct_mulher = weighted_mean(subset['mulher'], subset['peso']) * 100
        pct_negro_pardo = weighted_mean(subset['negro_pardo'], subset['peso']) * 100
        pct_superior = weighted_mean(subset['superior'], subset['peso']) * 100

        # Trabalho
        renda_media = weighted_mean(subset['rendimento_habitual'].dropna(),
                                     subset.loc[subset['rendimento_habitual'].notna(), 'peso'])
        horas_medias = weighted_mean(subset['horas_trabalhadas'], subset['peso'])
        pct_formal = weighted_mean(subset['formal'], subset['peso']) * 100
        taxa_ocupacao = weighted_mean(subset['ocupado'], subset['peso']) * 100

        stats.append({
            'Quintil': quintil,
            'Exposição Média': exp_media,
            'População (M)': pop,
            'Idade Média': idade_media,
            '% Mulher': pct_mulher,
            '% Negro/Pardo': pct_negro_pardo,
            '% Superior': pct_superior,
            'Renda Média': renda_media,
            'Horas Médias': horas_medias,
            '% Formal': pct_formal,
            '% Ocupado': taxa_ocupacao
        })

    stats_df = pd.DataFrame(stats)

    logger.info(f"  Estatísticas computadas para {len(stats_df)} quintis")

    return stats_df


def create_quintile_table(stats_df, format='both'):
    """Formata e salva tabela de quintis"""

    logger.info("")
    logger.info("="*70)
    logger.info("CARACTERÍSTICAS POR QUINTIL (PRÉ-TRATAMENTO)")
    logger.info("="*70)

    # Formatar
    display_df = stats_df.copy()
    display_df = display_df.round(2)

    logger.info("\n" + display_df.to_string(index=False))

    # Salvar CSV
    csv_path = OUTPUTS_TABLES / 'quintile_characteristics_pre.csv'
    display_df.to_csv(csv_path, index=False)
    logger.info(f"\nCSV salvo em: {csv_path}")

    # Salvar LaTeX
    if format in ['latex', 'both']:
        latex_path = OUTPUTS_TABLES / 'quintile_characteristics_pre.tex'

        latex_str = display_df.to_latex(index=False, float_format="%.2f",
                                        caption="Características por Quintil de Exposição (Pré-Tratamento)",
                                        label="tab:quintile")

        with open(latex_path, 'w') as f:
            f.write(latex_str)

        logger.info(f"LaTeX salvo em: {latex_path}")


def plot_exposure_by_quintile(df, save_path=None):
    """Box plot de exposição por quintil"""

    logger.info("")
    logger.info("Plotando distribuição de exposição por quintil...")

    fig, ax = plt.subplots(figsize=(10, 6))

    df_plot = df[df['quintil_exp'].notna()].copy()

    sns.boxplot(data=df_plot, x='quintil_exp', y='exposure_score', ax=ax)

    ax.set_xlabel('Quintil de Exposição', fontsize=12)
    ax.set_ylabel('Exposure Score', fontsize=12)
    ax.set_title('Distribuição de Exposure Score por Quintil', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        logger.info(f"  Salvo em: {save_path}")

    return fig


if __name__ == "__main__":

    # Carregar dados
    logger.info("Carregando dataset DiD final...")
    df = pd.read_parquet(DATA_PROCESSED / "pnad_panel_did_ready.parquet")
    logger.info(f"Carregado: {len(df):,} observações\n")

    # Computar estatísticas
    stats_df = compute_quintile_statistics(df)

    # Criar tabela
    create_quintile_table(stats_df)

    # Box plot
    plot_exposure_by_quintile(df, save_path=OUTPUTS_FIGURES / 'exposure_distribution_by_quintile.png')

    logger.info("")
    logger.info("="*70)
    logger.info("ANÁLISE POR QUINTIL CONCLUÍDA")
    logger.info("="*70)
    logger.info("")
    logger.info("FASE 3 (PRÉ-REGRESSÃO) COMPLETA!")
    logger.info("Todos os outputs estão em outputs/")
