"""
Funções de plotagem para análise DiD
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from utils.weighted_stats import weighted_mean, weighted_se


def plot_parallel_trends(df, outcome, treatment='alta_exp', save_path=None):
    """
    Plota tendências paralelas (pré-tratamento) para validação visual do DiD.

    Parâmetros:
    -----------
    df : DataFrame
    outcome : str
        Variável dependente a plotar
    treatment : str
        Variável de tratamento (binary)
    save_path : Path, optional
        Caminho para salvar figura

    Retorna:
    --------
    matplotlib.figure.Figure
    """

    # Configurar estilo
    sns.set_style("whitegrid")
    plt.rcParams['figure.dpi'] = 150

    # Computar médias ponderadas por grupo e período
    trends = []

    for periodo in sorted(df['periodo'].unique()):
        df_period = df[df['periodo'] == periodo]

        # Grupo tratado
        df_treated = df_period[df_period[treatment] == 1]
        mean_treated = weighted_mean(df_treated[outcome], df_treated['peso'])
        se_treated = weighted_se(df_treated[outcome], df_treated['peso'])

        # Grupo controle
        df_control = df_period[df_period[treatment] == 0]
        mean_control = weighted_mean(df_control[outcome], df_control['peso'])
        se_control = weighted_se(df_control[outcome], df_control['peso'])

        trends.append({
            'periodo': periodo,
            'mean_treated': mean_treated,
            'se_treated': se_treated,
            'mean_control': mean_control,
            'se_control': se_control
        })

    trends_df = pd.DataFrame(trends)

    # Criar figura
    fig, ax = plt.subplots(figsize=(14, 7))

    # Plotar linhas
    periodos = trends_df['periodo'].tolist()
    x = range(len(periodos))

    # Linha de controle (baixa exposição)
    ax.plot(x, trends_df['mean_control'],
            'o-', color='#2ecc71', linewidth=2.5, markersize=10,
            label='Baixa Exposição (controle)',
            markeredgecolor='white', markeredgewidth=2)

    # Linha de tratamento (alta exposição)
    ax.plot(x, trends_df['mean_treated'],
            's-', color='#e74c3c', linewidth=2.5, markersize=10,
            label='Alta Exposição (tratamento)',
            markeredgecolor='white', markeredgewidth=2)

    # Intervalos de confiança (95%)
    ax.fill_between(x,
                     trends_df['mean_control'] - 1.96 * trends_df['se_control'],
                     trends_df['mean_control'] + 1.96 * trends_df['se_control'],
                     color='#2ecc71', alpha=0.2)

    ax.fill_between(x,
                     trends_df['mean_treated'] - 1.96 * trends_df['se_treated'],
                     trends_df['mean_treated'] + 1.96 * trends_df['se_treated'],
                     color='#e74c3c', alpha=0.2)

    # Linha vertical no tratamento (2022T4)
    if '2022T4' in periodos:
        idx_chatgpt = periodos.index('2022T4')
    else:
        idx_chatgpt = len(periodos) // 2  # Fallback

    ax.axvline(x=idx_chatgpt + 0.5, color='#34495e', linestyle='--',
               linewidth=2, label='Lançamento ChatGPT (Nov/2022)', alpha=0.7)

    # Sombrear regiões pré e pós
    ax.axvspan(-0.5, idx_chatgpt + 0.5, alpha=0.05, color='blue')
    ax.axvspan(idx_chatgpt + 0.5, len(periodos) - 0.5, alpha=0.05, color='red')

    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels(periodos, rotation=45, ha='right')
    ax.set_xlabel('Período', fontsize=12, fontweight='bold')

    outcome_label = outcome.replace('_', ' ').replace('ln ', 'Log ').title()
    ax.set_ylabel(outcome_label, fontsize=12, fontweight='bold')

    ax.set_title(f'Tendências Paralelas: {outcome_label}\\n(Validação Visual do DiD)',
                fontsize=14, fontweight='bold')

    ax.legend(loc='best', fontsize=10, frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)

    # Anotação
    ax.text(idx_chatgpt/2, ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.05,
            'PRÉ-TRATAMENTO\\n(verificar paralelismo)',
            ha='center', fontsize=9, style='italic', color='#3498db')

    ax.text(idx_chatgpt + (len(periodos) - idx_chatgpt)/2,
            ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.05,
            'PÓS-TRATAMENTO\\n(efeito causal)',
            ha='center', fontsize=9, style='italic', color='#e74c3c')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"Figura salva em: {save_path}")

    return fig


def plot_love_plot(stats_df, save_path=None):
    """
    Plota Love plot (standardized differences) para balance table.

    Parâmetros:
    -----------
    stats_df : DataFrame
        DataFrame com colunas: Variável, std_diff
    save_path : Path, optional
    """

    fig, ax = plt.subplots(figsize=(10, 8))

    # Ordenar por magnitude de std_diff
    stats_df = stats_df.sort_values('std_diff')

    y_pos = range(len(stats_df))

    # Cores baseadas em threshold
    colors = ['red' if abs(x) > 0.25 else 'green' for x in stats_df['std_diff']]

    # Barras horizontais
    ax.barh(y_pos, stats_df['std_diff'], color=colors, alpha=0.6)

    # Linhas de referência (±0.25)
    ax.axvline(x=0.25, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=-0.25, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1)

    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stats_df['Variável'])
    ax.set_xlabel('Diferença Padronizada', fontsize=12)
    ax.set_title('Love Plot: Balanço de Covariáveis\\n(|std_diff| < 0.25 = balanceado)',
                fontsize=14, fontweight='bold')

    # Anotações
    ax.text(0.30, len(stats_df) - 1, 'Desbalanceado',
            color='red', fontsize=9, style='italic')
    ax.text(0.05, len(stats_df) - 1, 'Balanceado',
            color='green', fontsize=9, style='italic')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')

    return fig


def plot_multi_panel_trends(df, outcomes, treatment='alta_exp', save_path=None):
    """
    Cria painel 2×2 com tendências para múltiplos outcomes.

    Parâmetros:
    -----------
    df : DataFrame
    outcomes : list
        Lista de outcomes a plotar (max 4)
    treatment : str
    save_path : Path, optional
    """

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for idx, outcome in enumerate(outcomes[:4]):
        ax = axes[idx]

        # Computar tendências
        trends = []
        for periodo in sorted(df['periodo'].unique()):
            df_period = df[df['periodo'] == periodo]

            mean_treated = weighted_mean(
                df_period[df_period[treatment] == 1][outcome],
                df_period[df_period[treatment] == 1]['peso']
            )
            mean_control = weighted_mean(
                df_period[df_period[treatment] == 0][outcome],
                df_period[df_period[treatment] == 0]['peso']
            )

            trends.append({
                'periodo': periodo,
                'mean_treated': mean_treated,
                'mean_control': mean_control
            })

        trends_df = pd.DataFrame(trends)

        # Plotar
        periodos = trends_df['periodo'].tolist()
        x = range(len(periodos))

        ax.plot(x, trends_df['mean_control'], 'o-', color='#2ecc71',
                linewidth=2, label='Controle')
        ax.plot(x, trends_df['mean_treated'], 's-', color='#e74c3c',
                linewidth=2, label='Tratamento')

        # Linha ChatGPT
        idx_chatgpt = periodos.index('2022T4') if '2022T4' in periodos else len(periodos)//2
        ax.axvline(x=idx_chatgpt + 0.5, color='gray', linestyle='--', alpha=0.7)

        # Labels
        ax.set_xticks(x)
        ax.set_xticklabels(periodos, rotation=45, ha='right', fontsize=8)
        outcome_label = outcome.replace('_', ' ').title()
        ax.set_title(outcome_label, fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.suptitle('Tendências Paralelas: Múltiplos Outcomes', fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')

    return fig
