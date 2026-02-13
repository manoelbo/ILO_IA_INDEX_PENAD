"""
Script 11: Heterogeneity Analysis
==================================

Testa se os efeitos da IA variam por grupos demográficos usando Triple-DiD.

Grupos analisados:
- Idade: jovem (≤30 anos) vs experiente
- Gênero: mulher vs homem
- Educação: superior completo vs não
- Raça: negro/pardo vs outros

Para cada grupo, estima:
1. Triple-DiD: post × alta_exp × grupo
2. Event study separado por subgrupo
3. Gráficos comparativos

Author: DiD Ocupacional Team
Date: February 2026
"""

import sys
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import (
    DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS,
    OUTCOMES_VALID, HETEROGENEITY_GROUPS, EVENT_STUDY_REFERENCE,
    PLAUSIBILITY_THRESHOLDS, MIN_CLUSTERS
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '11_heterogeneity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# AUXILIARY FUNCTIONS
# ============================================

def check_pyfixest_installed():
    """
    Verifica se pyfixest está instalado.

    Returns:
        bool: True se instalado, False caso contrário
    """
    try:
        import pyfixest as pf
        logger.info(f"✓ pyfixest version {pf.__version__} installed")
        return True
    except ImportError:
        logger.error("✗ pyfixest not installed")
        logger.error("Install with: pip install pyfixest>=0.40.0")
        return False


def add_significance_stars(p_value):
    """
    Adiciona estrelas de significância baseado em p-value.

    Parameters:
    -----------
    p_value : float
        P-valor do teste

    Returns:
    --------
    str: '', '*', '**', ou '***'
    """
    if p_value < 0.01:
        return '***'
    elif p_value < 0.05:
        return '**'
    elif p_value < 0.10:
        return '*'
    else:
        return ''


def validate_subgroup_size(df, group_var, min_n=1000):
    """
    Valida se há observações suficientes em cada subgrupo.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    group_var : str
        Nome da variável de grupo (ex: 'jovem', 'mulher')
    min_n : int
        Número mínimo de observações por célula

    Returns:
    --------
    tuple: (is_valid, message)
    """
    # Count by group
    group_counts = df[group_var].value_counts()

    logger.info(f"\n{'='*60}")
    logger.info(f"Validation: {group_var}")
    logger.info(f"{'='*60}")
    for val, count in group_counts.items():
        logger.info(f"  {group_var}={val}: {count:,} obs")

    # Check minimum
    min_count = group_counts.min()
    if min_count < min_n:
        return False, f"Insufficient observations: min={min_count:,} < {min_n:,}"

    # Check treatment × group cells
    logger.info("\nTreatment × Group cells:")
    cross_tab = pd.crosstab(df['alta_exp'], df[group_var])
    logger.info(f"\n{cross_tab}")

    min_cell = cross_tab.min().min()
    if min_cell < min_n:
        return False, f"Insufficient cell size: min={min_cell:,} < {min_n:,}"

    return True, f"Valid subgroups: min_cell={min_cell:,}"


def flag_implausible_interaction(coef_interaction, se_interaction, outcome):
    """
    Verifica se termo de interação é implausível ou mal identificado.

    Parameters:
    -----------
    coef_interaction : float
        Coeficiente do termo de interação
    se_interaction : float
        Erro padrão do termo de interação
    outcome : str
        Nome do outcome

    Returns:
    --------
    bool: True se problemático, False caso contrário
    """
    # Check if SE is very large (poorly identified)
    if se_interaction > abs(coef_interaction) * 5:
        logger.warning(f"⚠️  POORLY IDENTIFIED interaction for {outcome}")
        logger.warning(f"    SE/|coef| = {se_interaction/abs(coef_interaction):.2f} > 5")
        logger.warning("    Interaction term may not be well identified")
        return True

    # Check if interaction is implausibly large
    threshold = PLAUSIBILITY_THRESHOLDS.get(outcome, 0.20)
    if abs(coef_interaction) > threshold:
        logger.warning(f"⚠️  IMPLAUSIBLY LARGE INTERACTION for {outcome}")
        logger.warning(f"    β_interaction={coef_interaction:.4f}, threshold={threshold}")
        return True

    return False


def calculate_total_effect(coef_main, coef_interaction, se_main, se_interaction, cov_matrix=None):
    """
    Calcula efeito total e seu erro padrão usando delta method.

    Para Triple-DiD:
    - Efeito para grupo=0: coef_main
    - Efeito para grupo=1: coef_main + coef_interaction

    SE(total) = sqrt(var_main + var_interaction + 2*cov)

    Parameters:
    -----------
    coef_main : float
        Coeficiente do efeito principal (post:alta_exp)
    coef_interaction : float
        Coeficiente da interação (post:alta_exp:group)
    se_main : float
        Erro padrão do efeito principal
    se_interaction : float
        Erro padrão da interação
    cov_matrix : np.ndarray, optional
        Matriz de covariância completa (se disponível)

    Returns:
    --------
    tuple: (total_effect, se_total, p_value)
    """
    total_effect = coef_main + coef_interaction

    # Conservative approach: assume zero covariance if not provided
    if cov_matrix is not None:
        # Extract covariance between main and interaction
        # (requires knowing their position in coef vector)
        # For now, use conservative approximation
        cov = 0
    else:
        cov = 0

    # Delta method for sum
    var_total = se_main**2 + se_interaction**2 + 2*cov
    se_total = np.sqrt(var_total)

    # T-test for total effect
    t_stat = total_effect / se_total
    p_value = 2 * (1 - np.abs(t_stat))  # Approximation; proper would use t-distribution

    return total_effect, se_total, p_value


# ============================================
# MAIN ESTIMATION FUNCTIONS
# ============================================

def triple_did(df, outcome, group_var, group_label):
    """
    Estima Triple-DiD: post × alta_exp × group

    Formula: outcome ~ post:alta_exp:group + post:alta_exp + post:group +
                       alta_exp:group + controls | FE

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente
    group_var : str
        Nome da variável binária de grupo (ex: 'jovem')
    group_label : str
        Label descritivo (ex: 'age', 'gender')

    Returns:
    --------
    dict: Resultados com coef_main, coef_interaction, coef_total, etc.
    """
    import pyfixest as pf

    logger.info(f"\n{'='*60}")
    logger.info(f"Triple-DiD: {outcome} × {group_label} ({group_var})")
    logger.info(f"{'='*60}")

    # Validate subgroup sizes
    is_valid, msg = validate_subgroup_size(df, group_var)
    if not is_valid:
        logger.warning(f"⚠️  {msg}")
        logger.warning("    Proceeding with estimation, but results may be unreliable")
    else:
        logger.info(f"✓ {msg}")

    # Prepare data (using same controls as Model 3 from script 09)
    # Build column list, avoiding duplicates if group_var is one of the controls
    cols = [outcome, 'post', 'alta_exp', group_var, 'cod_ocupacao', 'periodo',
            'idade', 'mulher', 'negro_pardo', 'superior', 'medio', 'peso']
    cols = list(dict.fromkeys(cols))  # Remove duplicates while preserving order
    df_reg = df[cols].dropna()

    n_before = len(df)
    n_after = len(df_reg)
    if n_after < n_before:
        logger.info(f"Dropped {n_before - n_after:,} obs with missing values")

    # Create interaction terms explicitly for pyfixest (using .values to avoid index issues)
    df_reg['post_alta'] = df_reg['post'].values * df_reg['alta_exp'].values
    df_reg['post_group'] = df_reg['post'].values * df_reg[group_var].values
    df_reg['alta_group'] = df_reg['alta_exp'].values * df_reg[group_var].values
    df_reg['post_alta_group'] = df_reg['post'].values * df_reg['alta_exp'].values * df_reg[group_var].values

    # Formula with Triple-DiD interaction (same controls as Model 3)
    formula = f"""
    {outcome} ~ post_alta_group + post_alta + post_group + alta_group +
                idade + I(idade**2) + mulher + negro_pardo + superior + medio |
                cod_ocupacao + periodo
    """

    try:
        # Estimate model
        model = pf.feols(
            formula,
            data=df_reg,
            weights='peso',
            vcov={'CRV1': 'cod_ocupacao'}
        )

        # Extract coefficients
        coef_df = model.coef()
        se_df = model.se()
        pval_df = model.pvalue()

        # Get main effect and interaction
        coef_main = coef_df.loc['post_alta']
        se_main = se_df.loc['post_alta']
        pval_main = pval_df.loc['post_alta']

        coef_interaction = coef_df.loc['post_alta_group']
        se_interaction = se_df.loc['post_alta_group']
        pval_interaction = pval_df.loc['post_alta_group']

        # Calculate total effect for group=1
        coef_total, se_total, pval_total = calculate_total_effect(
            coef_main, coef_interaction, se_main, se_interaction
        )

        # Get model fit statistics
        n_obs = model._N
        r2_within = model._r2_within
        n_clusters = len(df_reg['cod_ocupacao'].unique())

        # Log results
        logger.info(f"\nResults:")
        logger.info(f"  Main effect (group=0): {coef_main:.4f} ({se_main:.4f}) {add_significance_stars(pval_main)}")
        logger.info(f"  Interaction (group=1 diff): {coef_interaction:.4f} ({se_interaction:.4f}) {add_significance_stars(pval_interaction)}")
        logger.info(f"  Total effect (group=1): {coef_total:.4f} ({se_total:.4f}) {add_significance_stars(pval_total)}")
        logger.info(f"  N={n_obs:,}, R²_within={r2_within:.4f}, Clusters={n_clusters}")

        # Flag potential issues
        flag_implausible_interaction(coef_interaction, se_interaction, outcome)

        # Return results dictionary
        return {
            'outcome': outcome,
            'group_label': group_label,
            'group_var': group_var,
            'coef_main': coef_main,
            'se_main': se_main,
            'pval_main': pval_main,
            'stars_main': add_significance_stars(pval_main),
            'coef_interaction': coef_interaction,
            'se_interaction': se_interaction,
            'pval_interaction': pval_interaction,
            'stars_interaction': add_significance_stars(pval_interaction),
            'coef_total': coef_total,
            'se_total': se_total,
            'pval_total': pval_total,
            'stars_total': add_significance_stars(pval_total),
            'n_obs': n_obs,
            'r2_within': r2_within,
            'n_clusters': n_clusters
        }

    except Exception as e:
        logger.error(f"✗ Estimation failed for {outcome} × {group_label}")
        logger.error(f"  Error: {str(e)}")
        return None


def event_study_by_group(df, outcome, group_var, group_label):
    """
    Estima event studies separados para cada valor do grupo.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente
    group_var : str
        Nome da variável binária de grupo
    group_label : str
        Label descritivo do grupo

    Returns:
    --------
    DataFrame: Coeficientes de event study com colunas adicionais: group_value
    """
    import pyfixest as pf

    logger.info(f"\n{'='*60}")
    logger.info(f"Event Study by Group: {outcome} × {group_label}")
    logger.info(f"{'='*60}")

    # Get reference period number
    ref_period_num = int(EVENT_STUDY_REFERENCE.replace('T', ''))

    all_results = []

    # Estimate event study for each group value
    for group_val in [0, 1]:
        logger.info(f"\n--- Group: {group_var}={group_val} ---")

        # Filter to this group
        df_group = df[df[group_var] == group_val].copy()
        logger.info(f"N={len(df_group):,} observations")

        # Prepare data (no need to worry about duplicates here since group is already filtered)
        df_reg = df_group[[outcome, 'periodo_num', 'alta_exp', 'cod_ocupacao', 'periodo',
                            'idade', 'mulher', 'negro_pardo', 'superior', 'medio', 'peso']].dropna()

        # Create period dummies (excluding reference period)
        periods = sorted(df_reg['periodo_num'].unique())
        period_dummies = [p for p in periods if p != ref_period_num]

        # Create interaction dummies: period_dummy × alta_exp (using .values to avoid index issues)
        for p in period_dummies:
            df_reg[f'lead_lag_{p}'] = ((df_reg['periodo_num'] == p).astype(int).values *
                                       df_reg['alta_exp'].values)

        # Build formula
        interaction_terms = ' + '.join([f'lead_lag_{p}' for p in period_dummies])
        formula = f"""
        {outcome} ~ {interaction_terms} +
                    idade + I(idade**2) + mulher + negro_pardo + superior + medio |
                    cod_ocupacao + periodo
        """

        try:
            # Estimate
            model = pf.feols(
                formula,
                data=df_reg,
                weights='peso',
                vcov={'CRV1': 'cod_ocupacao'}
            )

            # Extract coefficients for lead/lag terms
            coef_df = model.coef()
            se_df = model.se()
            pval_df = model.pvalue()

            for p in period_dummies:
                var_name = f'lead_lag_{p}'
                if var_name in coef_df.index:
                    all_results.append({
                        'outcome': outcome,
                        'group_label': group_label,
                        'group_var': group_var,
                        'group_value': group_val,
                        'periodo_num': p,
                        'relative_period': p - ref_period_num,
                        'coef': coef_df.loc[var_name],
                        'se': se_df.loc[var_name],
                        'p_value': pval_df.loc[var_name],
                        'ci_low': coef_df.loc[var_name] - 1.96 * se_df.loc[var_name],
                        'ci_high': coef_df.loc[var_name] + 1.96 * se_df.loc[var_name],
                        'stars': add_significance_stars(pval_df.loc[var_name])
                    })

            # Add reference period (coef = 0 by construction)
            all_results.append({
                'outcome': outcome,
                'group_label': group_label,
                'group_var': group_var,
                'group_value': group_val,
                'periodo_num': ref_period_num,
                'relative_period': 0,
                'coef': 0.0,
                'se': 0.0,
                'p_value': 1.0,
                'ci_low': 0.0,
                'ci_high': 0.0,
                'stars': ''
            })

            logger.info(f"✓ Event study estimated successfully")

        except Exception as e:
            logger.error(f"✗ Estimation failed for {group_var}={group_val}")
            logger.error(f"  Error: {str(e)}")

    results_df = pd.DataFrame(all_results)
    results_df = results_df.sort_values(['group_value', 'periodo_num'])

    return results_df


def plot_event_study_comparison(coefs_df, outcome, group_var, group_label, save_path):
    """
    Plota event studies dos dois grupos no mesmo gráfico para comparação.

    Parameters:
    -----------
    coefs_df : DataFrame
        Resultados de event_study_by_group()
    outcome : str
        Nome do outcome
    group_var : str
        Nome da variável de grupo
    group_label : str
        Label descritivo
    save_path : Path
        Caminho para salvar figura
    """
    logger.info(f"\nCreating comparative event study plot: {outcome} × {group_label}")

    # Setup plot
    fig, ax = plt.subplots(figsize=(14, 8))
    colors = ['#2E86AB', '#A23B72']  # Blue for group=0, Purple for group=1
    labels = {0: f'{group_var}=0', 1: f'{group_var}=1'}

    # Plot each group
    for group_val, color in zip([0, 1], colors):
        df_group = coefs_df[coefs_df['group_value'] == group_val].copy()
        df_group = df_group.sort_values('relative_period')

        ax.plot(df_group['relative_period'], df_group['coef'],
                marker='o', color=color, linewidth=2, markersize=6,
                label=labels[group_val])

        # Add confidence intervals
        ax.fill_between(df_group['relative_period'],
                        df_group['ci_low'], df_group['ci_high'],
                        color=color, alpha=0.2)

    # Add reference line at y=0
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    # Add treatment period vertical line
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7,
               label='Treatment (ChatGPT Release)')

    # Labels and formatting
    ax.set_xlabel('Quarters Relative to Treatment', fontsize=12, fontweight='bold')
    ax.set_ylabel('Coefficient', fontsize=12, fontweight='bold')
    ax.set_title(f'Event Study: {outcome} by {group_label}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    plt.close()

    logger.info(f"✓ Plot saved: {save_path.name}")


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """
    Executa análise completa de heterogeneidade.
    """
    logger.info("="*80)
    logger.info("SCRIPT 11: HETEROGENEITY ANALYSIS")
    logger.info("="*80)

    # Check pyfixest
    if not check_pyfixest_installed():
        return

    # Load data
    logger.info("\nLoading data...")
    data_path = DATA_PROCESSED / 'pnad_panel_did_ready.parquet'
    df = pd.read_parquet(data_path)
    logger.info(f"✓ Loaded {len(df):,} observations")

    # Note: Only use valid outcomes (informal excluded after script 09 found zero variance)
    outcomes_to_use = [o for o in OUTCOMES_VALID if o in ['ln_renda', 'horas_trabalhadas']]
    logger.info(f"\nOutcomes to analyze: {outcomes_to_use}")
    logger.info(f"Groups to analyze: {list(HETEROGENEITY_GROUPS.keys())}")

    # Storage for all results
    all_triple_did_results = []
    all_event_study_results = []

    # ============================================
    # MAIN ANALYSIS LOOP
    # ============================================

    for outcome in outcomes_to_use:
        logger.info("\n" + "="*80)
        logger.info(f"OUTCOME: {outcome}")
        logger.info("="*80)

        outcome_triple_did = []
        outcome_event_study = []

        for group_label, group_var in HETEROGENEITY_GROUPS.items():
            logger.info(f"\n{'-'*70}")
            logger.info(f"GROUP: {group_label} ({group_var})")
            logger.info(f"{'-'*70}")

            # 1. Triple-DiD estimation
            result = triple_did(df, outcome, group_var, group_label)

            if result:
                all_triple_did_results.append(result)
                outcome_triple_did.append(result)
            else:
                logger.warning(f"⚠️  Skipping {group_label} - estimation failed")
                continue

            # 2. Event Study by Group
            event_results = event_study_by_group(df, outcome, group_var, group_label)

            if not event_results.empty:
                all_event_study_results.append(event_results)
                outcome_event_study.append(event_results)

                # 3. Create comparison plot
                plot_path = OUTPUTS_FIGURES / f'event_study_by_{group_label}.png'
                plot_event_study_comparison(event_results, outcome, group_var, group_label, plot_path)
            else:
                logger.warning(f"⚠️  Event study failed for {group_label}")

        # Save outcome-specific results
        if outcome_triple_did:
            outcome_df = pd.DataFrame(outcome_triple_did)
            save_path = OUTPUTS_TABLES / f'heterogeneity_triple_did_{outcome}.csv'
            outcome_df.to_csv(save_path, index=False)
            logger.info(f"\n✓ Saved Triple-DiD results: {save_path.name}")

    # ============================================
    # SAVE COMPREHENSIVE RESULTS
    # ============================================

    logger.info("\n" + "="*80)
    logger.info("SAVING COMPREHENSIVE RESULTS")
    logger.info("="*80)

    # 1. All Triple-DiD results
    if all_triple_did_results:
        all_triple_df = pd.DataFrame(all_triple_did_results)
        save_path = OUTPUTS_TABLES / 'heterogeneity_all_triple_did.csv'
        all_triple_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # 2. Results by group (all outcomes together)
    for group_label in HETEROGENEITY_GROUPS.keys():
        group_results = [r for r in all_triple_did_results if r['group_label'] == group_label]
        if group_results:
            group_df = pd.DataFrame(group_results)
            save_path = OUTPUTS_TABLES / f'heterogeneity_by_{group_label}.csv'
            group_df.to_csv(save_path, index=False)
            logger.info(f"✓ Saved: {save_path.name}")

    # 3. All Event Study results
    if all_event_study_results:
        all_event_df = pd.concat(all_event_study_results, ignore_index=True)
        save_path = OUTPUTS_TABLES / 'heterogeneity_event_study_all.csv'
        all_event_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # 4. Create summary table
    if all_triple_did_results:
        summary_records = []
        for r in all_triple_did_results:
            summary_records.append({
                'outcome': r['outcome'],
                'group': r['group_label'],
                'main_effect': f"{r['coef_main']:.4f}{r['stars_main']}",
                'main_se': f"({r['se_main']:.4f})",
                'interaction': f"{r['coef_interaction']:.4f}{r['stars_interaction']}",
                'interaction_se': f"({r['se_interaction']:.4f})",
                'total_effect': f"{r['coef_total']:.4f}{r['stars_total']}",
                'total_se': f"({r['se_total']:.4f})",
                'n_obs': r['n_obs'],
                'n_clusters': r['n_clusters']
            })

        summary_df = pd.DataFrame(summary_records)
        save_path = OUTPUTS_TABLES / 'heterogeneity_summary.csv'
        summary_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # ============================================
    # FINAL SUMMARY
    # ============================================

    logger.info("\n" + "="*80)
    logger.info("ANALYSIS COMPLETE")
    logger.info("="*80)

    logger.info(f"\nTriple-DiD estimations: {len(all_triple_did_results)}")
    logger.info(f"Event studies completed: {len(all_event_study_results)}")
    logger.info(f"Figures created: {len(list(OUTPUTS_FIGURES.glob('event_study_by_*.png')))}")

    # Flag significant interactions
    sig_interactions = [r for r in all_triple_did_results if r['pval_interaction'] < 0.10]
    if sig_interactions:
        logger.info(f"\n🎯 {len(sig_interactions)} SIGNIFICANT INTERACTIONS (p<0.10):")
        for r in sig_interactions:
            logger.info(f"  - {r['outcome']} × {r['group_label']}: "
                       f"β={r['coef_interaction']:.4f}{r['stars_interaction']} "
                       f"(p={r['pval_interaction']:.4f})")
    else:
        logger.info("\nNo statistically significant interactions found (all p>=0.10)")

    logger.info("\n✓ All outputs saved to:")
    logger.info(f"  - Tables: {OUTPUTS_TABLES}")
    logger.info(f"  - Figures: {OUTPUTS_FIGURES}")
    logger.info(f"  - Log: {OUTPUTS_LOGS / '11_heterogeneity.log'}")


if __name__ == '__main__':
    main()
