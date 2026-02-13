#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 15: Create Figures for Heterogeneity Findings
======================================================

Creates professional visualizations for the main heterogeneity findings (age and education).

Outputs:
--------
- figure1_heterogeneity_horas.pdf/png: Bar plot with confidence intervals (horas_trabalhadas)
- figure2_heterogeneity_combined.pdf/png: Combined visualization for both outcomes
- figure3_cancellation_effect.pdf/png: Illustration of effect cancellation

Author: Analysis Pipeline
Date: 2026-02-08
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import OUTPUTS_TABLES, OUTPUTS_LOGS, ROOT_DIR

# Define outputs directory for figures
OUTPUTS_FIGURES = ROOT_DIR / "outputs" / "figures"
OUTPUTS_FIGURES.mkdir(exist_ok=True, parents=True)

# ============================================
# LOGGING SETUP
# ============================================

log_file = OUTPUTS_LOGS / '15_create_figures.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# MATPLOTLIB CONFIGURATION
# ============================================

# Set style for professional academic figures
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("Set2")

# Font sizes for readability
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'font.family': 'serif',
    'text.usetex': False  # Set to True if you have LaTeX installed
})

# Color scheme
COLORS = {
    'negative': '#d62728',  # Red
    'positive': '#2ca02c',  # Green
    'neutral': '#7f7f7f',   # Gray
    'sig': '#1f77b4'        # Blue for significant
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def parse_stars(value_str):
    """
    Extract numeric value and significance level from string like '-0.7473***'.

    Returns:
    --------
    tuple: (float_value, n_stars, p_level)
    """
    value_str = str(value_str).strip()
    stars = 0

    # Count stars at the end
    while value_str and value_str[-1] == '*':
        stars += 1
        value_str = value_str[:-1]

    try:
        value = float(value_str)
    except:
        value = np.nan

    # Map stars to p-value levels
    if stars == 3:
        p_level = 'p<0.01'
    elif stars == 2:
        p_level = 'p<0.05'
    elif stars == 1:
        p_level = 'p<0.10'
    else:
        p_level = 'n.s.'

    return value, stars, p_level


def parse_se(se_str):
    """
    Extract SE value from string like '(0.2646)'.
    """
    se_str = str(se_str).strip()
    se_str = se_str.strip('()')

    try:
        return float(se_str)
    except:
        return np.nan


def get_group_label(group):
    """
    Convert group code to Portuguese label.
    """
    labels = {
        'age': 'Jovens (≤30 anos)',
        'education': 'Ensino Superior',
        'gender': 'Mulheres',
        'race': 'Negros/Pardos'
    }
    return labels.get(group, group)


def get_outcome_label(outcome):
    """
    Convert outcome code to Portuguese label.
    """
    labels = {
        'ln_renda': 'Log(Rendimento)',
        'horas_trabalhadas': 'Horas Trabalhadas'
    }
    return labels.get(outcome, outcome)


# ============================================
# FIGURE 1: HETEROGENEITY BAR PLOT (HORAS)
# ============================================

def create_figure1_heterogeneity_horas(het_df, save_path_pdf, save_path_png):
    """
    Creates bar plot with confidence intervals for horas_trabalhadas heterogeneity.
    Highlights the main findings (age and education).

    Parameters:
    -----------
    het_df : DataFrame
        Heterogeneity results
    save_path_pdf : Path
        Where to save PDF version
    save_path_png : Path
        Where to save PNG version
    """
    logger.info("\nCreating Figure 1: Heterogeneity Effects (Horas Trabalhadas)...")

    # Filter to horas_trabalhadas
    df = het_df[het_df['outcome'] == 'horas_trabalhadas'].copy()

    # Parse values
    df['effect'], df['stars'], df['p_level'] = zip(*df['total_effect'].apply(parse_stars))
    df['se'] = df['total_se'].apply(parse_se)
    df['ci_lower'] = df['effect'] - 1.96 * df['se']
    df['ci_upper'] = df['effect'] + 1.96 * df['se']

    # Create labels
    df['group_label'] = df['group'].apply(get_group_label)

    # Sort by effect size
    df = df.sort_values('effect')

    # Determine colors (significant findings in blue, others in gray)
    df['color'] = df['stars'].apply(lambda x: COLORS['sig'] if x >= 2 else COLORS['neutral'])

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Bar plot with error bars
    y_pos = np.arange(len(df))
    bars = ax.barh(y_pos, df['effect'], xerr=[df['effect'] - df['ci_lower'],
                                                df['ci_upper'] - df['effect']],
                   color=df['color'], alpha=0.7, capsize=5, edgecolor='black', linewidth=1.2)

    # Add vertical line at zero
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['group_label'])
    ax.set_xlabel('Efeito Total (Horas Trabalhadas)', fontsize=12, fontweight='bold')
    ax.set_title('Efeitos Heterogêneos sobre Horas Trabalhadas\n(Impacto da IA Generativa por Grupo Demográfico)',
                 fontsize=13, fontweight='bold', pad=20)

    # Add value labels on bars
    for i, (idx, row) in enumerate(df.iterrows()):
        value = row['effect']
        p_level = row['p_level']
        label = f"{value:.2f}"
        if row['stars'] > 0:
            label += f"\n({p_level})"

        x_pos = value + (0.1 if value > 0 else -0.1)
        ha = 'left' if value > 0 else 'right'
        ax.text(x_pos, i, label, va='center', ha=ha, fontsize=9,
                fontweight='bold' if row['stars'] >= 2 else 'normal')

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS['sig'], alpha=0.7, edgecolor='black', label='Significativo (p<0.05)'),
        Patch(facecolor=COLORS['neutral'], alpha=0.7, edgecolor='black', label='Não Significativo')
    ]
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, fancybox=True)

    # Add note
    fig.text(0.12, 0.02,
             'Nota: Barras mostram efeito total (DiD × Grupo). Linhas horizontais representam intervalos de confiança de 95%.\n'
             'Efeitos significativos destacados em azul.',
             fontsize=8, ha='left', style='italic', color='dimgray')

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    # Save
    fig.savefig(save_path_pdf, dpi=300, bbox_inches='tight')
    fig.savefig(save_path_png, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"✓ Figure 1 saved: {save_path_pdf.name} and {save_path_png.name}")


# ============================================
# FIGURE 2: COMBINED HETEROGENEITY (BOTH OUTCOMES)
# ============================================

def create_figure2_combined_heterogeneity(het_df, save_path_pdf, save_path_png):
    """
    Creates combined figure showing heterogeneity for both outcomes (ln_renda and horas_trabalhadas).

    Parameters:
    -----------
    het_df : DataFrame
        Heterogeneity results
    save_path_pdf : Path
        Where to save PDF version
    save_path_png : Path
        Where to save PNG version
    """
    logger.info("\nCreating Figure 2: Combined Heterogeneity (Both Outcomes)...")

    # Parse values for all rows
    het_df['effect'], het_df['stars'], het_df['p_level'] = zip(*het_df['total_effect'].apply(parse_stars))
    het_df['se'] = het_df['total_se'].apply(parse_se)
    het_df['ci_lower'] = het_df['effect'] - 1.96 * het_df['se']
    het_df['ci_upper'] = het_df['effect'] + 1.96 * het_df['se']
    het_df['group_label'] = het_df['group'].apply(get_group_label)
    het_df['outcome_label'] = het_df['outcome'].apply(get_outcome_label)

    # Create figure with 2 subplots (side by side)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    outcomes = ['ln_renda', 'horas_trabalhadas']

    for i, outcome in enumerate(outcomes):
        ax = axes[i]
        df = het_df[het_df['outcome'] == outcome].copy()
        df = df.sort_values('effect')

        # Colors
        df['color'] = df['stars'].apply(lambda x: COLORS['sig'] if x >= 2 else COLORS['neutral'])

        # Bar plot
        y_pos = np.arange(len(df))
        ax.barh(y_pos, df['effect'], xerr=[df['effect'] - df['ci_lower'],
                                            df['ci_upper'] - df['effect']],
                color=df['color'], alpha=0.7, capsize=5, edgecolor='black', linewidth=1.2)

        # Zero line
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

        # Labels
        if i == 0:
            ax.set_yticks(y_pos)
            ax.set_yticklabels(df['group_label'])

        outcome_label = get_outcome_label(outcome)
        ax.set_xlabel('Efeito Total', fontsize=11, fontweight='bold')
        ax.set_title(outcome_label, fontsize=12, fontweight='bold', pad=10)

        # Value labels
        for j, (idx, row) in enumerate(df.iterrows()):
            value = row['effect']
            if row['stars'] > 0:
                label = f"{value:.2f}*" if row['stars'] == 1 else f"{value:.2f}**" if row['stars'] == 2 else f"{value:.2f}***"
            else:
                label = f"{value:.2f}"

            x_pos = value + (0.05 if value > 0 else -0.05)
            ha = 'left' if value > 0 else 'right'
            ax.text(x_pos, j, label, va='center', ha=ha, fontsize=9,
                    fontweight='bold' if row['stars'] >= 2 else 'normal')

    # Overall title
    fig.suptitle('Efeitos Heterogêneos por Grupo Demográfico\n(Impacto da IA Generativa)',
                 fontsize=14, fontweight='bold', y=0.98)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS['sig'], alpha=0.7, edgecolor='black', label='Significativo (p<0.05)'),
        Patch(facecolor=COLORS['neutral'], alpha=0.7, edgecolor='black', label='Não Significativo')
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2,
               frameon=True, fancybox=True, bbox_to_anchor=(0.5, -0.05))

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    # Save
    fig.savefig(save_path_pdf, dpi=300, bbox_inches='tight')
    fig.savefig(save_path_png, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"✓ Figure 2 saved: {save_path_pdf.name} and {save_path_png.name}")


# ============================================
# FIGURE 3: EFFECT CANCELLATION ILLUSTRATION
# ============================================

def create_figure3_cancellation(het_df, save_path_pdf, save_path_png):
    """
    Creates illustration of how opposite effects cancel out in the aggregate mean.
    Shows age (negative) and education (positive) effects for horas_trabalhadas.

    Parameters:
    -----------
    het_df : DataFrame
        Heterogeneity results
    save_path_pdf : Path
        Where to save PDF version
    save_path_png : Path
        Where to save PNG version
    """
    logger.info("\nCreating Figure 3: Effect Cancellation Illustration...")

    # Get horas_trabalhadas effects for age and education
    df_horas = het_df[het_df['outcome'] == 'horas_trabalhadas'].copy()

    # Parse values
    df_horas['effect'], df_horas['stars'], df_horas['p_level'] = zip(*df_horas['total_effect'].apply(parse_stars))

    # Get specific effects
    age_effect = df_horas[df_horas['group'] == 'age']['effect'].values[0]
    edu_effect = df_horas[df_horas['group'] == 'education']['effect'].values[0]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))

    # Data for visualization
    groups = ['Jovens\n(≤30 anos)', 'Ensino\nSuperior', 'Efeito\nMédio']
    effects = [age_effect, edu_effect, (age_effect + edu_effect) / 2]
    colors_list = [COLORS['negative'], COLORS['positive'], COLORS['neutral']]

    # Bar plot
    bars = ax.bar(groups, effects, color=colors_list, alpha=0.7, edgecolor='black', linewidth=2)

    # Zero line
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5)

    # Labels on bars
    for i, (group, effect, color) in enumerate(zip(groups, effects, colors_list)):
        label = f"{effect:.2f}"
        y_offset = 0.05 if effect > 0 else -0.05
        va = 'bottom' if effect > 0 else 'top'
        ax.text(i, effect + y_offset, label, ha='center', va=va,
                fontsize=13, fontweight='bold', color=color)

    # Add arrows showing cancellation
    # Arrow from age to average
    ax.annotate('', xy=(2, effects[2]), xytext=(0, effects[0]),
                arrowprops=dict(arrowstyle='->', lw=2, color='dimgray', linestyle='--', alpha=0.6))

    # Arrow from education to average
    ax.annotate('', xy=(2, effects[2]), xytext=(1, effects[1]),
                arrowprops=dict(arrowstyle='->', lw=2, color='dimgray', linestyle='--', alpha=0.6))

    # Add text explaining cancellation
    ax.text(1, -0.5, 'Efeitos opostos se\nCANCELAM na média',
            ha='center', va='top', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))

    # Labels
    ax.set_ylabel('Efeito sobre Horas Trabalhadas', fontsize=12, fontweight='bold')
    ax.set_title('Por Que o Efeito Médio é Próximo de Zero?\n(Cancelamento de Efeitos Heterogêneos)',
                 fontsize=13, fontweight='bold', pad=20)

    ax.set_ylim(-1, 0.5)

    # Grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Note
    fig.text(0.12, 0.02,
             'Nota: O efeito médio agregado (próximo de zero) NÃO significa ausência de impactos.\n'
             'Jovens são afetados negativamente (-0.66 horas), enquanto trabalhadores com ensino superior são afetados positivamente (+0.17 horas).\n'
             'Esses efeitos opostos se cancelam quando calculamos a média agregada.',
             fontsize=9, ha='left', style='italic', color='dimgray')

    plt.tight_layout(rect=[0, 0.08, 1, 1])

    # Save
    fig.savefig(save_path_pdf, dpi=300, bbox_inches='tight')
    fig.savefig(save_path_png, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"✓ Figure 3 saved: {save_path_pdf.name} and {save_path_png.name}")


# ============================================
# FIGURE 4: COEFFICIENT PLOT (FOREST PLOT STYLE)
# ============================================

def create_figure4_forest_plot(het_df, save_path_pdf, save_path_png):
    """
    Creates forest plot showing all heterogeneity effects with confidence intervals.
    Professional academic style.

    Parameters:
    -----------
    het_df : DataFrame
        Heterogeneity results
    save_path_pdf : Path
        Where to save PDF version
    save_path_png : Path
        Where to save PNG version
    """
    logger.info("\nCreating Figure 4: Forest Plot (Coefficient Plot)...")

    # Focus on horas_trabalhadas (main finding)
    df = het_df[het_df['outcome'] == 'horas_trabalhadas'].copy()

    # Parse values
    df['effect'], df['stars'], df['p_level'] = zip(*df['total_effect'].apply(parse_stars))
    df['se'] = df['total_se'].apply(parse_se)
    df['ci_lower'] = df['effect'] - 1.96 * df['se']
    df['ci_upper'] = df['effect'] + 1.96 * df['se']
    df['group_label'] = df['group'].apply(get_group_label)

    # Sort by effect size
    df = df.sort_values('effect', ascending=True)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Y positions
    y_pos = np.arange(len(df))

    # Plot points and error bars
    for i, (idx, row) in enumerate(df.iterrows()):
        color = COLORS['sig'] if row['stars'] >= 2 else COLORS['neutral']
        marker_size = 150 if row['stars'] >= 2 else 100

        # Error bar
        ax.plot([row['ci_lower'], row['ci_upper']], [i, i],
                color=color, linewidth=2.5, alpha=0.7, zorder=1)

        # Point estimate
        ax.scatter(row['effect'], i, s=marker_size, color=color,
                   edgecolor='black', linewidth=1.5, alpha=0.9, zorder=2)

    # Zero line
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1.5, alpha=0.6)

    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['group_label'])
    ax.set_xlabel('Efeito sobre Horas Trabalhadas (95% IC)', fontsize=12, fontweight='bold')
    ax.set_title('Efeitos Heterogêneos sobre Horas Trabalhadas\n(Forest Plot com Intervalos de Confiança)',
                 fontsize=13, fontweight='bold', pad=20)

    # Add value labels
    for i, (idx, row) in enumerate(df.iterrows()):
        label = f"{row['effect']:.2f}"
        if row['stars'] >= 2:
            label += "**" if row['stars'] == 2 else "***"

        x_pos = row['ci_upper'] + 0.05
        ax.text(x_pos, i, label, va='center', ha='left', fontsize=10,
                fontweight='bold' if row['stars'] >= 2 else 'normal')

    # Grid
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['sig'],
               markersize=10, markeredgecolor='black', label='Significativo (p<0.05)', alpha=0.9),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['neutral'],
               markersize=8, markeredgecolor='black', label='Não Significativo', alpha=0.9)
    ]
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, fancybox=True)

    # Note
    fig.text(0.12, 0.02,
             'Nota: Pontos mostram efeitos totais estimados. Linhas horizontais representam intervalos de confiança de 95%.\n'
             'Efeitos estatisticamente significativos (p<0.05) destacados com pontos maiores.',
             fontsize=8, ha='left', style='italic', color='dimgray')

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    # Save
    fig.savefig(save_path_pdf, dpi=300, bbox_inches='tight')
    fig.savefig(save_path_png, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"✓ Figure 4 saved: {save_path_pdf.name} and {save_path_png.name}")


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """
    Main execution function.
    """
    logger.info("="*70)
    logger.info("SCRIPT 15: CREATE HETEROGENEITY FIGURES")
    logger.info("="*70)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ============================================
    # LOAD DATA
    # ============================================

    logger.info("Loading heterogeneity data...")

    het_path = OUTPUTS_TABLES / 'heterogeneity_summary.csv'

    try:
        het_df = pd.read_csv(het_path)
        logger.info(f"✓ Loaded: {het_path.name} ({len(het_df)} rows)")
    except Exception as e:
        logger.error(f"✗ Failed to load heterogeneity data: {e}")
        return

    # ============================================
    # CREATE FIGURES
    # ============================================

    logger.info("\n" + "="*70)
    logger.info("GENERATING FIGURES")
    logger.info("="*70)

    figures_created = []

    # Figure 1: Heterogeneity bar plot (horas_trabalhadas only)
    fig1_pdf = OUTPUTS_FIGURES / 'figure1_heterogeneity_horas.pdf'
    fig1_png = OUTPUTS_FIGURES / 'figure1_heterogeneity_horas.png'
    try:
        create_figure1_heterogeneity_horas(het_df, fig1_pdf, fig1_png)
        figures_created.append(('Figure 1', fig1_pdf.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Figure 1: {e}")

    # Figure 2: Combined heterogeneity (both outcomes)
    fig2_pdf = OUTPUTS_FIGURES / 'figure2_heterogeneity_combined.pdf'
    fig2_png = OUTPUTS_FIGURES / 'figure2_heterogeneity_combined.png'
    try:
        create_figure2_combined_heterogeneity(het_df, fig2_pdf, fig2_png)
        figures_created.append(('Figure 2', fig2_pdf.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Figure 2: {e}")

    # Figure 3: Effect cancellation illustration
    fig3_pdf = OUTPUTS_FIGURES / 'figure3_cancellation.pdf'
    fig3_png = OUTPUTS_FIGURES / 'figure3_cancellation.png'
    try:
        create_figure3_cancellation(het_df, fig3_pdf, fig3_png)
        figures_created.append(('Figure 3', fig3_pdf.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Figure 3: {e}")

    # Figure 4: Forest plot
    fig4_pdf = OUTPUTS_FIGURES / 'figure4_forest_plot.pdf'
    fig4_png = OUTPUTS_FIGURES / 'figure4_forest_plot.png'
    try:
        create_figure4_forest_plot(het_df, fig4_pdf, fig4_png)
        figures_created.append(('Figure 4', fig4_pdf.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Figure 4: {e}")

    # ============================================
    # SUMMARY
    # ============================================

    logger.info("\n" + "="*70)
    logger.info("FIGURE GENERATION COMPLETE")
    logger.info("="*70)

    logger.info(f"\nFigures generated ({len(figures_created)}):")
    for fig_name, fig_file in figures_created:
        logger.info(f"  ✓ {fig_name}: {fig_file}")

    logger.info(f"\n📁 All figures saved to: {OUTPUTS_FIGURES}")
    logger.info(f"   - PDF versions (for LaTeX): *.pdf")
    logger.info(f"   - PNG versions (for presentations): *.png")
    logger.info(f"\n📄 Log saved to: {log_file}")

    logger.info(f"\n✓ Script completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ============================================
    # INSTRUCTIONS FOR LATEX
    # ============================================

    logger.info("\n" + "="*70)
    logger.info("HOW TO INCLUDE FIGURES IN LATEX")
    logger.info("="*70)
    logger.info("\nAdd the following to your LaTeX document:\n")
    logger.info("\\usepackage{graphicx}")
    logger.info("\\usepackage{float}\n")
    logger.info("Then, to insert a figure:\n")
    logger.info("\\begin{figure}[H]")
    logger.info("  \\centering")
    logger.info("  \\includegraphics[width=0.9\\textwidth]{figure1_heterogeneity_horas.pdf}")
    logger.info("  \\caption{Efeitos Heterogêneos sobre Horas Trabalhadas}")
    logger.info("  \\label{fig:het_horas}")
    logger.info("\\end{figure}\n")


if __name__ == '__main__':
    main()
