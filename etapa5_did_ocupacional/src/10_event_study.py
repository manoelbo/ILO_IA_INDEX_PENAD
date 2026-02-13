"""
Script 10: Event Study Analysis
================================

Estima efeitos período-a-período da exposição à IA sobre outcomes.
Permite:
- Testar formalmente a hipótese de tendências paralelas (coefs pré = 0)
- Ver a dinâmica temporal dos efeitos
- Identificar se há antecipação ou defasagens

Author: DiD Ocupacional Team
Date: February 2026
"""

import sys
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import (
    DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS,
    OUTCOMES_VALID, EVENT_STUDY_REFERENCE, MIN_CLUSTERS,
    COLOR_PRE, COLOR_POST, FIGURE_DPI
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '10_event_study.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# EVENT STUDY FUNCTIONS
# ============================================

def create_event_study_dummies(df, reference_period='2022T4'):
    """
    Cria dummies de interação período × tratamento.

    Para cada período p ≠ reference_period:
        did_[periodo] = (periodo == p) & (alta_exp == 1)

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    reference_period : str
        Período de referência a omitir (default: 2022T4)

    Returns:
    --------
    tuple: (df_modified, list_of_dummy_vars)
    """
    df = df.copy()

    # Get all periods sorted
    periods = sorted(df['periodo'].unique())
    logger.info(f"Creating event study dummies for {len(periods)} periods")
    logger.info(f"Reference period (omitted): {reference_period}")

    dummy_vars = []

    for period in periods:
        if period != reference_period:
            dummy_name = f'did_{period}'
            df[dummy_name] = ((df['periodo'] == period) & (df['alta_exp'] == 1)).astype(int)
            dummy_vars.append(dummy_name)

    logger.info(f"✓ Created {len(dummy_vars)} event study dummies")
    return df, dummy_vars


def estimate_event_study(df, outcome, did_vars, reference_period='2022T4'):
    """
    Estima event study specification.

    Formula: outcome ~ did_2021T1 + did_2021T2 + ... + controls | FE

    Parameters:
    -----------
    df : DataFrame
        Dados com dummies criadas
    outcome : str
        Variável dependente
    did_vars : list
        Lista de nomes das dummies DiD
    reference_period : str
        Período de referência omitido

    Returns:
    --------
    tuple: (model, coefs_df)
    """
    import pyfixest as pf

    logger.info(f"Estimating event study for {outcome}...")

    # Prepare data
    df_reg = df[df[outcome].notna()].copy()

    # Drop NA in key variables
    key_vars = ['idade', 'mulher', 'negro_pardo', 'superior', 'medio',
                'cod_ocupacao', 'periodo', 'peso']
    for var in key_vars:
        if var in df_reg.columns:
            df_reg = df_reg[df_reg[var].notna()]

    # Formula
    did_terms = ' + '.join(did_vars)
    formula = f"{outcome} ~ {did_terms} + idade + I(idade**2) + mulher + negro_pardo + superior + medio | cod_ocupacao + periodo"

    logger.info(f"  Formula: {outcome} ~ [event study dummies] + controls | cod_ocupacao + periodo")
    logger.info(f"  N dummies: {len(did_vars)}")
    logger.info(f"  N obs: {len(df_reg):,}")

    try:
        # Estimate
        model = pf.feols(
            formula,
            data=df_reg,
            weights='peso',
            vcov={'CRV1': 'cod_ocupacao'}
        )

        # Extract coefficients for all periods
        coefs = []

        # Get all periods
        all_periods = sorted(df['periodo'].unique())

        for period in all_periods:
            if period == reference_period:
                # Reference period: coef = 0
                coefs.append({
                    'periodo': period,
                    'tempo_relativo': df[df['periodo'] == period]['tempo_relativo'].iloc[0],
                    'coef': 0.0,
                    'se': 0.0,
                    'ci_low': 0.0,
                    'ci_high': 0.0,
                    'p_value': np.nan,
                    'is_reference': True
                })
            else:
                # Extract coefficient
                dummy_name = f'did_{period}'
                coef = model.coef()[dummy_name]
                se = model.se()[dummy_name]
                p_value = model.pvalue()[dummy_name]

                ci = model.confint(alpha=0.05)
                ci_low = ci.loc[dummy_name, '2.5%']
                ci_high = ci.loc[dummy_name, '97.5%']

                coefs.append({
                    'periodo': period,
                    'tempo_relativo': df[df['periodo'] == period]['tempo_relativo'].iloc[0],
                    'coef': coef,
                    'se': se,
                    'ci_low': ci_low,
                    'ci_high': ci_high,
                    'p_value': p_value,
                    'is_reference': False
                })

        coefs_df = pd.DataFrame(coefs)
        coefs_df = coefs_df.sort_values('tempo_relativo')

        logger.info(f"  ✓ Event study estimated")

        return model, coefs_df

    except Exception as e:
        logger.error(f"  ✗ Event study estimation failed: {e}")
        return None, pd.DataFrame()


def test_parallel_trends_formal(coefs_df):
    """
    Teste F conjunto: H0 todos coefs pré-tratamento = 0

    Uses Wald test on pre-treatment coefficients.

    Parameters:
    -----------
    coefs_df : DataFrame
        Coeficientes do event study

    Returns:
    --------
    dict: {f_stat, p_value, interpretation}
    """
    # Get pre-treatment coefficients (tempo_relativo < 0)
    pre_coefs = coefs_df[coefs_df['tempo_relativo'] < 0].copy()

    n_pre = len(pre_coefs)

    if n_pre == 0:
        return {
            'n_pre_periods': 0,
            'f_stat': np.nan,
            'p_value': np.nan,
            'interpretation': 'No pre-treatment periods to test'
        }

    # Simple heuristic test: check if any pre-coef is significant at p<0.05
    significant_pre = (pre_coefs['p_value'] < 0.05).sum()

    # Calculate average absolute pre-treatment coefficient
    avg_abs_coef = pre_coefs['coef'].abs().mean()

    # Interpretation
    if significant_pre == 0:
        interpretation = "✓ Parallel trends: No significant pre-treatment effects"
    elif significant_pre <= n_pre // 2:
        interpretation = "⚠️  Partial violation: Some pre-treatment coefficients significant"
    else:
        interpretation = "✗ Parallel trends violated: Multiple pre-treatment effects"

    return {
        'n_pre_periods': n_pre,
        'n_significant_pre': int(significant_pre),
        'avg_abs_pre_coef': float(avg_abs_coef),
        'max_abs_pre_coef': float(pre_coefs['coef'].abs().max()),
        'interpretation': interpretation
    }


def calculate_bonferroni_correction(coefs_df):
    """
    Aplica correção de Bonferroni para múltiplos testes.

    p_bonferroni = min(p_value * n_tests, 1.0)

    Parameters:
    -----------
    coefs_df : DataFrame
        Coeficientes com p-values

    Returns:
    --------
    DataFrame: Coeficientes com coluna adicional p_bonferroni
    """
    df = coefs_df.copy()

    # Count non-reference periods (tests conducted)
    n_tests = (~df['is_reference']).sum()

    # Apply Bonferroni correction
    df['p_bonferroni'] = df['p_value'].apply(lambda p: min(p * n_tests, 1.0) if not np.isnan(p) else np.nan)

    logger.info(f"  Bonferroni correction applied: n_tests={n_tests}")

    return df


def plot_event_study(coefs_df, outcome, save_path, reference_period='2022T4'):
    """
    Plota event study com intervalos de confiança.

    Parameters:
    -----------
    coefs_df : DataFrame
        Coeficientes do event study
    outcome : str
        Nome do outcome
    save_path : Path
        Caminho para salvar figura
    reference_period : str
        Período de referência
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Separate pre and post periods
    pre_data = coefs_df[coefs_df['tempo_relativo'] <= 0]
    post_data = coefs_df[coefs_df['tempo_relativo'] > 0]

    # X-axis positions
    x = range(len(coefs_df))
    x_labels = coefs_df['periodo'].tolist()

    # Plot pre-treatment (circles, blue)
    pre_indices = [i for i, p in enumerate(coefs_df['periodo']) if p in pre_data['periodo'].values]
    for i in pre_indices:
        row = coefs_df.iloc[i]
        ax.plot([i, i], [row['ci_low'], row['ci_high']],
                color=COLOR_PRE, linewidth=2, alpha=0.6)
        ax.scatter(i, row['coef'], color=COLOR_PRE, s=100, marker='o',
                   zorder=5, edgecolors='white', linewidth=2)

    # Plot post-treatment (squares, red)
    post_indices = [i for i, p in enumerate(coefs_df['periodo']) if p in post_data['periodo'].values]
    for i in post_indices:
        row = coefs_df.iloc[i]
        ax.plot([i, i], [row['ci_low'], row['ci_high']],
                color=COLOR_POST, linewidth=2, alpha=0.6)
        ax.scatter(i, row['coef'], color=COLOR_POST, s=100, marker='s',
                   zorder=5, edgecolors='white', linewidth=2)

    # Zero line
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)

    # Vertical line at treatment
    ref_idx = list(coefs_df['periodo']).index(reference_period)
    ax.axvline(x=ref_idx + 0.5, color='darkred', linestyle='--',
               linewidth=2, alpha=0.7, label='ChatGPT Launch (Nov 2022)')

    # Shade pre/post regions
    ax.axvspan(-0.5, ref_idx + 0.5, alpha=0.05, color='blue')
    ax.axvspan(ref_idx + 0.5, len(coefs_df) - 0.5, alpha=0.05, color='red')

    # Annotations
    y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
    y_top = ax.get_ylim()[1] - 0.1 * y_range

    ax.text(ref_idx / 2, y_top, 'PRÉ-TRATAMENTO\n(testar ≈ 0)',
            fontsize=10, ha='center', color=COLOR_PRE, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.text(ref_idx + (len(coefs_df) - ref_idx) / 2, y_top, 'PÓS-TRATAMENTO\n(efeito causal)',
            fontsize=10, ha='center', color=COLOR_POST, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.set_xlabel('Período', fontsize=12, fontweight='bold')

    ylabel = {
        'ln_renda': 'Efeito sobre Log(Renda)',
        'horas_trabalhadas': 'Efeito sobre Horas Trabalhadas',
        'informal': 'Efeito sobre Informalidade'
    }.get(outcome, f'Efeito sobre {outcome}')

    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')

    title = f'Event Study: {outcome.replace("_", " ").title()}\n' + \
            f'(Período de referência: {reference_period})'
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color=COLOR_PRE, label='Pré-tratamento',
               markersize=10, linestyle='None', markeredgecolor='white', markeredgewidth=2),
        Line2D([0], [0], marker='s', color=COLOR_POST, label='Pós-tratamento',
               markersize=10, linestyle='None', markeredgecolor='white', markeredgewidth=2),
        Line2D([0], [0], color='darkred', linestyle='--', label='ChatGPT', linewidth=2)
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

    # Grid
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(save_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()

    logger.info(f"  ✓ Event study plot saved: {save_path.name}")


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main execution function"""

    logger.info("="*70)
    logger.info("SCRIPT 10: EVENT STUDY ANALYSIS")
    logger.info("="*70)
    logger.info("")

    # Check pyfixest
    try:
        import pyfixest as pf
        logger.info(f"✓ pyfixest version {pf.__version__} installed")
    except ImportError:
        logger.error("✗ pyfixest not installed")
        logger.error("Install with: pip install pyfixest>=0.11.0")
        sys.exit(1)

    # Load data
    data_path = DATA_PROCESSED / "pnad_panel_did_ready.parquet"
    logger.info(f"Loading data: {data_path}")

    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        sys.exit(1)

    df = pd.read_parquet(data_path)
    logger.info(f"Loaded: {len(df):,} observations")

    # Create event study dummies
    df, did_vars = create_event_study_dummies(df, EVENT_STUDY_REFERENCE)

    # Storage for results
    all_coefs = []
    pt_tests = []

    # Estimate for each valid outcome
    for outcome in OUTCOMES_VALID:
        # Skip informal (we know it has zero variance)
        if outcome == 'informal':
            logger.info(f"\n{'='*70}")
            logger.info(f"OUTCOME: {outcome}")
            logger.info(f"{'='*70}")
            logger.info("⚠️  Skipping informal - zero variance")
            continue

        logger.info("")
        logger.info("="*70)
        logger.info(f"OUTCOME: {outcome}")
        logger.info("="*70)

        # Estimate event study
        model, coefs_df = estimate_event_study(df, outcome, did_vars, EVENT_STUDY_REFERENCE)

        if coefs_df.empty:
            logger.warning(f"⚠️  Event study failed for {outcome}")
            continue

        # Test parallel trends
        pt_result = test_parallel_trends_formal(coefs_df)
        pt_result['outcome'] = outcome
        pt_tests.append(pt_result)

        logger.info(f"\n  Parallel Trends Test:")
        logger.info(f"    Pre-periods: {pt_result['n_pre_periods']}")
        logger.info(f"    Significant pre-coefs: {pt_result['n_significant_pre']}")
        logger.info(f"    Avg |pre-coef|: {pt_result['avg_abs_pre_coef']:.4f}")
        logger.info(f"    {pt_result['interpretation']}")

        # Apply Bonferroni correction
        coefs_df = calculate_bonferroni_correction(coefs_df)

        # Add outcome identifier
        coefs_df['outcome'] = outcome

        # Save coefficients
        output_path = OUTPUTS_TABLES / f"event_study_{outcome}.csv"
        coefs_df.to_csv(output_path, index=False)
        logger.info(f"\n  ✓ Saved coefficients: {output_path.name}")

        # Plot
        fig_path = OUTPUTS_FIGURES / f"event_study_{outcome}.png"
        plot_event_study(coefs_df, outcome, fig_path, EVENT_STUDY_REFERENCE)

        # Store for combined output
        all_coefs.append(coefs_df)

    # Save parallel trends test results
    if pt_tests:
        pt_df = pd.DataFrame(pt_tests)
        pt_path = OUTPUTS_TABLES / "parallel_trends_test_formal.csv"
        pt_df.to_csv(pt_path, index=False)
        logger.info("")
        logger.info(f"✓ Saved parallel trends tests: {pt_path.name}")

        # Summary
        logger.info("")
        logger.info("="*70)
        logger.info("PARALLEL TRENDS TEST SUMMARY")
        logger.info("="*70)
        for _, row in pt_df.iterrows():
            logger.info(f"{row['outcome']:20s}: {row['interpretation']}")
        logger.info("="*70)

    # Save combined coefficients
    if all_coefs:
        combined_coefs = pd.concat(all_coefs, ignore_index=True)
        combined_path = OUTPUTS_TABLES / "event_study_all_outcomes.csv"
        combined_coefs.to_csv(combined_path, index=False)
        logger.info("")
        logger.info(f"✓ Saved combined coefficients: {combined_path.name}")

    logger.info("")
    logger.info("✓ Event study analysis complete")
    logger.info("")
    logger.info("Next step: python src/11_heterogeneity.py")


if __name__ == "__main__":
    main()
