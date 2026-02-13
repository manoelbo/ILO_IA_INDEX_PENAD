"""
Script 06: Tabela de Balanço de Covariáveis (Pré-Tratamento)
=============================================================

Entrada: data/processed/pnad_panel_did_ready.parquet
Saídas:
- outputs/tables/balance_table_pre.csv
- outputs/tables/balance_table_pre.tex
- outputs/figures/love_plot.png
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from utils.weighted_stats import weighted_mean, weighted_std, weighted_diff_normalized
from utils.plotting import plot_love_plot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '06_balance_table.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def compute_balance_statistics(df, treatment_var='alta_exp'):
    """Calcula estatísticas de balanço para período pré-tratamento"""

    logger.info("Computando estatísticas de balanço...")

    # Filtrar período pré
    df_pre = df[df['post'] == 0].copy()

    logger.info(f"  Usando {len(df_pre):,} observações do período pré-tratamento")

    # Covariáveis a comparar
    covariates = {
        'idade': 'Idade (anos)',
        'mulher': 'Mulher (%)',
        'negro_pardo': 'Negro/Pardo (%)',
        'superior': 'Superior completo (%)',
        'medio': 'Médio completo (%)',
        'rendimento_habitual': 'Rendimento (R$)',
        'horas_trabalhadas': 'Horas trabalhadas',
        'formal': 'Formal (%)',
        'ocupado': 'Taxa de ocupação (%)'
    }

    results = []

    for var, label in covariates.items():
        if var not in df_pre.columns:
            continue

        # Remover missing
        df_var = df_pre[[var, treatment_var, 'peso']].dropna()

        # Separar grupos
        treated = df_var[df_var[treatment_var] == 1]
        control = df_var[df_var[treatment_var] == 0]

        # Médias
        mean_t = weighted_mean(treated[var], treated['peso'])
        mean_c = weighted_mean(control[var], control['peso'])

        # Desvios padrão
        std_t = weighted_std(treated[var], treated['peso'])
        std_c = weighted_std(control[var], control['peso'])

        # Diferença normalizada
        std_diff = weighted_diff_normalized(
            treated[var], treated['peso'],
            control[var], control['peso']
        )

        results.append({
            'Variável': label,
            'Controle': mean_c,
            'Tratamento': mean_t,
            'Diferença': mean_t - mean_c,
            'std_diff': std_diff,
            'Balanceado': '✓' if abs(std_diff) < BALANCE_THRESHOLD else '⚠️'
        })

    stats_df = pd.DataFrame(results)

    logger.info(f"  Computadas estatísticas para {len(stats_df)} covariáveis")

    return stats_df


def create_balance_table(stats_df, format='both'):
    """Cria tabela de balanço formatada"""

    logger.info("")
    logger.info("="*70)
    logger.info("TABELA DE BALANÇO - PERÍODO PRÉ-TRATAMENTO")
    logger.info("="*70)

    # Formatar para exibição
    display_df = stats_df.copy()
    display_df['Controle'] = display_df['Controle'].round(2)
    display_df['Tratamento'] = display_df['Tratamento'].round(2)
    display_df['Diferença'] = display_df['Diferença'].round(2)
    display_df['Diff. Normalizada'] = display_df['std_diff'].round(3)

    display_df = display_df[['Variável', 'Controle', 'Tratamento', 'Diferença',
                             'Diff. Normalizada', 'Balanceado']]

    logger.info("\n" + display_df.to_string(index=False))

    logger.info("")
    logger.info("Nota: Diff. Normalizada > |0.25| indica desbalanceamento substancial")

    # Salvar CSV
    csv_path = OUTPUTS_TABLES / 'balance_table_pre.csv'
    display_df.to_csv(csv_path, index=False)
    logger.info(f"\nCSV salvo em: {csv_path}")

    # Salvar LaTeX
    if format in ['latex', 'both']:
        latex_path = OUTPUTS_TABLES / 'balance_table_pre.tex'

        latex_str = display_df.to_latex(index=False, float_format="%.2f",
                                        caption="Tabela de Balanço de Covariáveis (Período Pré-Tratamento)",
                                        label="tab:balance")

        with open(latex_path, 'w') as f:
            f.write(latex_str)

        logger.info(f"LaTeX salvo em: {latex_path}")

    return display_df


if __name__ == "__main__":

    # Carregar dados
    logger.info("Carregando dataset DiD final...")
    df = pd.read_parquet(DATA_PROCESSED / "pnad_panel_did_ready.parquet")
    logger.info(f"Carregado: {len(df):,} observações\n")

    # Computar estatísticas
    stats_df = compute_balance_statistics(df)

    # Criar tabela
    table = create_balance_table(stats_df)

    # Love plot
    logger.info("")
    logger.info("Gerando Love Plot...")
    fig = plot_love_plot(stats_df, save_path=OUTPUTS_FIGURES / 'love_plot.png')

    logger.info("")
    logger.info("="*70)
    logger.info("ANÁLISE DE BALANÇO CONCLUÍDA")
    logger.info("="*70)
    logger.info("Próximo passo: python src/07_parallel_trends.py")
