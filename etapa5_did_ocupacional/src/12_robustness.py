"""
Script 12: Robustness Checks
=============================

Testa sensibilidade dos resultados principais a especificações alternativas.

4 testes de robustez essenciais:
1. Alternative Treatment Cutoffs (Top 10%, 20%, 25%, Continuous)
2. Placebo Test (tratamento fictício em 2021T4)
3. Exclude IT Occupations (remover profissionais de TI)
4. Occupation-Specific Trends (tendências diferenciais por ocupação)

Author: DiD Ocupacional Team
Date: February 2026
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import (
    DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_LOGS,
    OUTCOMES_VALID, ROBUSTNESS_CUTOFFS, PLACEBO_PERIODS,
    PLAUSIBILITY_THRESHOLDS, MIN_CLUSTERS
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '12_robustness.log'),
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


def estimate_did_spec(df, outcome, treatment_var, vcov_spec='CRV1', cluster_var='cod_ocupacao'):
    """
    Estima especificação DiD padrão (FE + Controls) com tratamento customizável.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente
    treatment_var : str
        Nome da variável de tratamento (ex: 'alta_exp', 'alta_exp_10', etc.)
    vcov_spec : str or dict
        Especificação de erro padrão
    cluster_var : str
        Variável de cluster

    Returns:
    --------
    dict: Resultados da estimação
    """
    import pyfixest as pf

    # Prepare data
    cols = [outcome, 'post', treatment_var, 'cod_ocupacao', 'periodo',
            'idade', 'mulher', 'negro_pardo', 'superior', 'medio', 'peso']
    cols = list(dict.fromkeys(cols))  # Remove duplicates
    df_reg = df[cols].dropna()

    # Create interaction
    df_reg['post_treatment'] = df_reg['post'].values * df_reg[treatment_var].values

    # Formula (same as Model 3)
    formula = f"""
    {outcome} ~ post_treatment +
                idade + I(idade**2) + mulher + negro_pardo + superior + medio |
                cod_ocupacao + periodo
    """

    try:
        # Estimate
        if vcov_spec == 'CRV1':
            vcov = {'CRV1': cluster_var}
        else:
            vcov = vcov_spec

        model = pf.feols(
            formula,
            data=df_reg,
            weights='peso',
            vcov=vcov
        )

        # Extract results
        coef_df = model.coef()
        se_df = model.se()
        pval_df = model.pvalue()

        coef = coef_df.loc['post_treatment']
        se = se_df.loc['post_treatment']
        p_value = pval_df.loc['post_treatment']

        # Calculate CI
        ci_low = coef - 1.96 * se
        ci_high = coef + 1.96 * se

        return {
            'outcome': outcome,
            'treatment_var': treatment_var,
            'coef': coef,
            'se': se,
            'p_value': p_value,
            'ci_low': ci_low,
            'ci_high': ci_high,
            'stars': add_significance_stars(p_value),
            'n_obs': model._N,
            'r2_within': model._r2_within,
            'n_clusters': len(df_reg[cluster_var].unique())
        }

    except Exception as e:
        logger.error(f"✗ Estimation failed: {str(e)}")
        return None


def assess_robustness(main_coef, robustness_coefs, threshold=0.5):
    """
    Avalia estabilidade dos resultados através de especificações alternativas.

    Critérios:
    - Consistência de sinal (todos mesmo sinal?)
    - Range relativo: (max-min)/|main| < threshold?

    Parameters:
    -----------
    main_coef : float
        Coeficiente da especificação principal
    robustness_coefs : list of float
        Coeficientes das especificações alternativas
    threshold : float
        Limite para range relativo (default: 0.5 = 50%)

    Returns:
    --------
    tuple: (assessment, details_dict)
        assessment: 'ROBUST', 'MODERATELY ROBUST', 'NOT ROBUST'
    """
    # Check sign consistency
    main_sign = np.sign(main_coef)
    all_coefs = [main_coef] + robustness_coefs
    signs = [np.sign(c) for c in all_coefs]
    sign_consistent = all(s == main_sign for s in signs)

    # Calculate range
    coef_min = min(all_coefs)
    coef_max = max(all_coefs)
    coef_range = coef_max - coef_min

    if abs(main_coef) < 1e-6:
        # Main effect is essentially zero
        relative_range = float('inf') if coef_range > 1e-6 else 0
    else:
        relative_range = coef_range / abs(main_coef)

    # Assessment
    if sign_consistent and relative_range < threshold:
        assessment = 'ROBUST'
    elif sign_consistent or relative_range < threshold * 2:
        assessment = 'MODERATELY ROBUST'
    else:
        assessment = 'NOT ROBUST'

    details = {
        'sign_consistent': sign_consistent,
        'relative_range': relative_range,
        'range': coef_range,
        'min_coef': coef_min,
        'max_coef': coef_max,
        'n_specs': len(all_coefs)
    }

    return assessment, details


# ============================================
# ROBUSTNESS TEST FUNCTIONS
# ============================================

def test_alternative_cutoffs(df, outcome):
    """
    Testa sensibilidade a diferentes definições de tratamento.

    Tests:
    - alta_exp_10 (Top 10%)
    - alta_exp (Top 20%, MAIN)
    - alta_exp_25 (Top 25%)
    - exposure_score (Continuous)

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente

    Returns:
    --------
    DataFrame: Resultados com uma linha por cutoff
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Test 1: Alternative Treatment Cutoffs - {outcome}")
    logger.info(f"{'='*60}")

    results = []

    for cutoff_var in ROBUSTNESS_CUTOFFS:
        logger.info(f"\n--- Testing: {cutoff_var} ---")

        # Check if variable exists
        if cutoff_var not in df.columns:
            logger.warning(f"⚠️  Variable {cutoff_var} not found in data, skipping")
            continue

        # For continuous exposure, handle differently
        if cutoff_var == 'exposure_score':
            # Continuous treatment
            result = estimate_did_spec(df, outcome, cutoff_var)
            if result:
                result['cutoff_type'] = 'Continuous'
                results.append(result)
                logger.info(f"  β={result['coef']:.4f}{result['stars']} (SE={result['se']:.4f})")
        else:
            # Binary treatment
            result = estimate_did_spec(df, outcome, cutoff_var)
            if result:
                # Extract cutoff percentage from variable name
                if '10' in cutoff_var:
                    cutoff_type = 'Top 10%'
                elif '25' in cutoff_var:
                    cutoff_type = 'Top 25%'
                else:
                    cutoff_type = 'Top 20% (MAIN)'

                result['cutoff_type'] = cutoff_type
                results.append(result)
                logger.info(f"  β={result['coef']:.4f}{result['stars']} (SE={result['se']:.4f})")

    results_df = pd.DataFrame(results) if results else pd.DataFrame()

    if not results_df.empty:
        logger.info("\n✓ Alternative cutoffs test completed")
        logger.info(f"  Tested {len(results_df)} specifications")
    else:
        logger.warning("⚠️  No valid cutoff tests completed")

    return results_df


def placebo_test(df, outcome, fake_period='2021T4'):
    """
    Teste de placebo: tratamento fictício em período pré-tratamento.

    Se design DiD é válido, não deve haver efeito em período anterior ao tratamento real.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente
    fake_period : str
        Período do tratamento fictício (ex: '2021T4')

    Returns:
    --------
    dict: Resultados do teste de placebo
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Test 2: Placebo Test - {outcome}")
    logger.info(f"{'='*60}")
    logger.info(f"Fake treatment period: {fake_period}")

    import pyfixest as pf

    # Create fake post indicator
    fake_period_num = int(fake_period.replace('T', ''))
    df_placebo = df.copy()
    df_placebo['post_placebo'] = (df_placebo['periodo_num'] >= fake_period_num).astype(int)

    # Filter to pre-treatment period only (before actual treatment)
    actual_treatment = 20224  # 2022T4
    df_placebo = df_placebo[df_placebo['periodo_num'] < actual_treatment].copy()

    logger.info(f"Using {len(df_placebo):,} observations from pre-treatment period")

    # Prepare data
    cols = [outcome, 'post_placebo', 'alta_exp', 'cod_ocupacao', 'periodo',
            'idade', 'mulher', 'negro_pardo', 'superior', 'medio', 'peso']
    cols = list(dict.fromkeys(cols))
    df_reg = df_placebo[cols].dropna()

    # Create placebo interaction
    df_reg['placebo_did'] = df_reg['post_placebo'].values * df_reg['alta_exp'].values

    # Formula
    formula = f"""
    {outcome} ~ placebo_did +
                idade + I(idade**2) + mulher + negro_pardo + superior + medio |
                cod_ocupacao + periodo
    """

    try:
        model = pf.feols(
            formula,
            data=df_reg,
            weights='peso',
            vcov={'CRV1': 'cod_ocupacao'}
        )

        coef_df = model.coef()
        se_df = model.se()
        pval_df = model.pvalue()

        coef = coef_df.loc['placebo_did']
        se = se_df.loc['placebo_did']
        p_value = pval_df.loc['placebo_did']

        # Interpretation
        if p_value < 0.10:
            logger.warning(f"⚠️  PLACEBO TEST FAILED!")
            logger.warning(f"    Found significant effect in pre-period: β={coef:.4f}{add_significance_stars(p_value)}")
            logger.warning(f"    This suggests violation of parallel trends assumption")
            placebo_pass = False
        else:
            logger.info(f"✓ PLACEBO TEST PASSED")
            logger.info(f"  No significant effect in pre-period: β={coef:.4f} (p={p_value:.4f})")
            placebo_pass = True

        return {
            'outcome': outcome,
            'test': 'Placebo',
            'fake_period': fake_period,
            'coef': coef,
            'se': se,
            'p_value': p_value,
            'stars': add_significance_stars(p_value),
            'placebo_pass': placebo_pass,
            'n_obs': model._N,
            'n_clusters': len(df_reg['cod_ocupacao'].unique())
        }

    except Exception as e:
        logger.error(f"✗ Placebo test failed: {str(e)}")
        return None


def exclude_it_occupations(df, outcome):
    """
    Testa robustez excluindo profissionais de TI (cod_ocupacao começando com '25').

    Motivação: TI pode responder diferentemente à IA generativa.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente

    Returns:
    --------
    dict: Resultados sem ocupações de TI
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Test 3: Exclude IT Occupations - {outcome}")
    logger.info(f"{'='*60}")

    # Filter out IT occupations (COD starting with '25')
    df_no_it = df[~df['cod_ocupacao'].str.startswith('25')].copy()

    n_dropped = len(df) - len(df_no_it)
    pct_dropped = (n_dropped / len(df)) * 100

    logger.info(f"Dropped {n_dropped:,} observations ({pct_dropped:.1f}%) from IT occupations")
    logger.info(f"Remaining: {len(df_no_it):,} observations")

    # Estimate main specification without IT
    result = estimate_did_spec(df_no_it, outcome, 'alta_exp')

    if result:
        result['test'] = 'Exclude IT'
        result['n_dropped'] = n_dropped
        result['pct_dropped'] = pct_dropped
        logger.info(f"  β={result['coef']:.4f}{result['stars']} (SE={result['se']:.4f})")
        logger.info(f"  Compare to main result to assess IT influence")
    else:
        logger.warning("⚠️  Estimation without IT failed")

    return result


def differential_trends_test(df, outcome):
    """
    Testa se tratados e controles tinham tendências diferenciadas no pré-período.

    Approach: Include alta_exp × periodo_num interaction in pre-period only.
    If coefficient is significant, suggests pre-existing differential trends.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente

    Returns:
    --------
    dict: Resultados do teste de differential trends
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Test 4: Differential Pre-Trends - {outcome}")
    logger.info(f"{'='*60}")

    import pyfixest as pf

    # Filter to pre-period only
    actual_treatment = 20224  # 2022T4
    df_pre = df[df['periodo_num'] < actual_treatment].copy()

    logger.info(f"Using {len(df_pre):,} observations from pre-treatment period")

    # Prepare data
    cols = [outcome, 'periodo_num', 'alta_exp', 'cod_ocupacao', 'periodo',
            'idade', 'mulher', 'negro_pardo', 'superior', 'medio', 'peso']
    cols = list(dict.fromkeys(cols))
    df_reg = df_pre[cols].dropna()

    # Scale periodo_num
    df_reg['periodo_scaled'] = (df_reg['periodo_num'] - df_reg['periodo_num'].mean()) / df_reg['periodo_num'].std()

    # Create differential trend: alta_exp × periodo_scaled
    df_reg['alta_trend'] = df_reg['alta_exp'].values * df_reg['periodo_scaled'].values

    # Formula
    formula = f"""
    {outcome} ~ alta_trend + alta_exp +
                idade + I(idade**2) + mulher + negro_pardo + superior + medio |
                cod_ocupacao + periodo
    """

    logger.info("Testing for differential pre-trends between treatment and control...")

    try:
        model = pf.feols(
            formula,
            data=df_reg,
            weights='peso',
            vcov={'CRV1': 'cod_ocupacao'}
        )

        coef_df = model.coef()
        se_df = model.se()
        pval_df = model.pvalue()

        coef = coef_df.loc['alta_trend']
        se = se_df.loc['alta_trend']
        p_value = pval_df.loc['alta_trend']

        # Interpretation
        if p_value < 0.10:
            logger.warning(f"⚠️  DIFFERENTIAL TRENDS DETECTED!")
            logger.warning(f"    Treatment and control had different pre-trends: β={coef:.4f}{add_significance_stars(p_value)}")
            logger.warning(f"    This may bias DiD estimates")
            trends_ok = False
        else:
            logger.info(f"✓ No significant differential pre-trends")
            logger.info(f"  β={coef:.4f} (p={p_value:.4f})")
            trends_ok = True

        return {
            'outcome': outcome,
            'test': 'Differential Trends',
            'coef': coef,
            'se': se,
            'p_value': p_value,
            'stars': add_significance_stars(p_value),
            'trends_ok': trends_ok,
            'n_obs': model._N,
            'n_clusters': len(df_reg['cod_ocupacao'].unique())
        }

    except Exception as e:
        logger.error(f"✗ Differential trends test failed: {str(e)}")
        return None


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """
    Executa todos os testes de robustez.
    """
    logger.info("="*80)
    logger.info("SCRIPT 12: ROBUSTNESS CHECKS")
    logger.info("="*80)

    # Check pyfixest
    if not check_pyfixest_installed():
        return

    # Load data
    logger.info("\nLoading data...")
    data_path = DATA_PROCESSED / 'pnad_panel_did_ready.parquet'
    df = pd.read_parquet(data_path)
    logger.info(f"✓ Loaded {len(df):,} observations")

    # Only use valid outcomes
    outcomes_to_use = [o for o in OUTCOMES_VALID if o in ['ln_renda', 'horas_trabalhadas']]
    logger.info(f"\nOutcomes to test: {outcomes_to_use}")

    # Get main results for comparison (from script 09)
    logger.info("\nLoading main results from script 09...")
    try:
        main_results_path = OUTPUTS_TABLES / 'did_main_results.csv'
        main_results = pd.read_csv(main_results_path)
        # Filter to Model 3 (main specification)
        main_results = main_results[main_results['model_name'].str.contains('Model 3', na=False)]
        logger.info(f"✓ Loaded main results for comparison")
    except Exception as e:
        logger.warning(f"⚠️  Could not load main results: {e}")
        main_results = None

    # Storage for all results
    all_cutoffs_results = []
    all_placebo_results = []
    all_no_it_results = []
    all_trends_results = []

    # ============================================
    # MAIN ROBUSTNESS LOOP
    # ============================================

    for outcome in outcomes_to_use:
        logger.info("\n" + "="*80)
        logger.info(f"OUTCOME: {outcome}")
        logger.info("="*80)

        # Get main coefficient for comparison
        main_coef = None
        if main_results is not None:
            main_row = main_results[main_results['outcome'] == outcome]
            if not main_row.empty:
                main_coef = main_row['coef'].values[0]
                logger.info(f"Main result (Model 3): β={main_coef:.4f}")

        # 1. Alternative cutoffs
        cutoffs_df = test_alternative_cutoffs(df, outcome)
        if not cutoffs_df.empty:
            all_cutoffs_results.append(cutoffs_df)
            logger.info(f"\n✓ Test 1 complete: {len(cutoffs_df)} cutoffs tested")

        # 2. Placebo test
        placebo_result = placebo_test(df, outcome, fake_period='2021T4')
        if placebo_result:
            all_placebo_results.append(placebo_result)
            logger.info(f"✓ Test 2 complete: Placebo {'PASSED' if placebo_result['placebo_pass'] else 'FAILED'}")

        # 3. Exclude IT
        no_it_result = exclude_it_occupations(df, outcome)
        if no_it_result:
            all_no_it_results.append(no_it_result)
            logger.info(f"✓ Test 3 complete: Estimated without IT occupations")

        # 4. Differential trends
        trends_result = differential_trends_test(df, outcome)
        if trends_result:
            all_trends_results.append(trends_result)
            logger.info(f"✓ Test 4 complete: Differential trends {'OK' if trends_result['trends_ok'] else 'DETECTED'}")

        # Assess robustness for this outcome
        if main_coef is not None and not cutoffs_df.empty:
            logger.info(f"\n{'='*60}")
            logger.info(f"Robustness Assessment: {outcome}")
            logger.info(f"{'='*60}")

            robustness_coefs = cutoffs_df['coef'].tolist()
            assessment, details = assess_robustness(main_coef, robustness_coefs)

            logger.info(f"Assessment: {assessment}")
            logger.info(f"  Coefficient range: [{details['min_coef']:.4f}, {details['max_coef']:.4f}]")
            logger.info(f"  Relative range: {details['relative_range']:.2f}")
            logger.info(f"  Sign consistent: {details['sign_consistent']}")

    # ============================================
    # SAVE COMPREHENSIVE RESULTS
    # ============================================

    logger.info("\n" + "="*80)
    logger.info("SAVING COMPREHENSIVE RESULTS")
    logger.info("="*80)

    # 1. Alternative cutoffs
    if all_cutoffs_results:
        all_cutoffs_df = pd.concat(all_cutoffs_results, ignore_index=True)
        save_path = OUTPUTS_TABLES / 'robustness_cutoffs.csv'
        all_cutoffs_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # 2. Placebo tests
    if all_placebo_results:
        placebo_df = pd.DataFrame(all_placebo_results)
        save_path = OUTPUTS_TABLES / 'robustness_placebo.csv'
        placebo_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # 3. No IT results
    if all_no_it_results:
        no_it_df = pd.DataFrame(all_no_it_results)
        save_path = OUTPUTS_TABLES / 'robustness_no_it.csv'
        no_it_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # 4. Differential trends
    if all_trends_results:
        trends_df = pd.DataFrame(all_trends_results)
        save_path = OUTPUTS_TABLES / 'robustness_trends.csv'
        trends_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # 5. Create comprehensive summary table
    logger.info("\nCreating robustness summary table...")

    summary_records = []

    for outcome in outcomes_to_use:
        # Main result
        if main_results is not None:
            main_row = main_results[main_results['outcome'] == outcome]
            if not main_row.empty:
                summary_records.append({
                    'outcome': outcome,
                    'specification': 'Main (Model 3)',
                    'coef': main_row['coef'].values[0],
                    'se': main_row['se'].values[0],
                    'p_value': main_row['p_value'].values[0],
                    'stars': add_significance_stars(main_row['p_value'].values[0]),
                    'test_type': 'Main'
                })

        # Cutoffs
        if all_cutoffs_results:
            outcome_cutoffs = [df for df in all_cutoffs_results if df['outcome'].iloc[0] == outcome]
            if outcome_cutoffs:
                cutoffs_df = outcome_cutoffs[0]
                for _, row in cutoffs_df.iterrows():
                    summary_records.append({
                        'outcome': outcome,
                        'specification': row['cutoff_type'],
                        'coef': row['coef'],
                        'se': row['se'],
                        'p_value': row['p_value'],
                        'stars': row['stars'],
                        'test_type': 'Alternative Cutoff'
                    })

        # Placebo
        outcome_placebo = [r for r in all_placebo_results if r['outcome'] == outcome]
        if outcome_placebo:
            r = outcome_placebo[0]
            summary_records.append({
                'outcome': outcome,
                'specification': f"Placebo ({r['fake_period']})",
                'coef': r['coef'],
                'se': r['se'],
                'p_value': r['p_value'],
                'stars': r['stars'],
                'test_type': 'Placebo'
            })

        # No IT
        outcome_no_it = [r for r in all_no_it_results if r['outcome'] == outcome]
        if outcome_no_it:
            r = outcome_no_it[0]
            summary_records.append({
                'outcome': outcome,
                'specification': 'Exclude IT',
                'coef': r['coef'],
                'se': r['se'],
                'p_value': r['p_value'],
                'stars': r['stars'],
                'test_type': 'Exclude IT'
            })

        # Differential trends
        outcome_trends = [r for r in all_trends_results if r['outcome'] == outcome]
        if outcome_trends:
            r = outcome_trends[0]
            summary_records.append({
                'outcome': outcome,
                'specification': 'Diff. Pre-Trends',
                'coef': r['coef'],
                'se': r['se'],
                'p_value': r['p_value'],
                'stars': r['stars'],
                'test_type': 'Differential Trends'
            })

    if summary_records:
        summary_df = pd.DataFrame(summary_records)
        save_path = OUTPUTS_TABLES / 'robustness_summary.csv'
        summary_df.to_csv(save_path, index=False)
        logger.info(f"✓ Saved: {save_path.name}")

    # ============================================
    # FINAL SUMMARY
    # ============================================

    logger.info("\n" + "="*80)
    logger.info("ANALYSIS COMPLETE")
    logger.info("="*80)

    logger.info(f"\nRobustness tests completed:")
    logger.info(f"  - Alternative cutoffs: {len(all_cutoffs_results)} outcomes tested")
    logger.info(f"  - Placebo tests: {len(all_placebo_results)}")
    logger.info(f"  - Exclude IT tests: {len(all_no_it_results)}")
    logger.info(f"  - Differential trends tests: {len(all_trends_results)}")

    # Flag critical issues
    logger.info("\n" + "="*60)
    logger.info("CRITICAL ROBUSTNESS FLAGS")
    logger.info("="*60)

    # Placebo failures
    placebo_failures = [r for r in all_placebo_results if not r['placebo_pass']]
    if placebo_failures:
        logger.warning(f"\n⚠️  {len(placebo_failures)} PLACEBO TEST(S) FAILED:")
        for r in placebo_failures:
            logger.warning(f"  - {r['outcome']}: β={r['coef']:.4f}{r['stars']} (suggests PT violation)")
    else:
        logger.info("\n✓ All placebo tests passed")

    # Differential trends detected
    trends_issues = [r for r in all_trends_results if not r['trends_ok']]
    if trends_issues:
        logger.warning(f"\n⚠️  {len(trends_issues)} DIFFERENTIAL PRE-TREND(S) DETECTED:")
        for r in trends_issues:
            logger.warning(f"  - {r['outcome']}: β={r['coef']:.4f}{r['stars']} (may bias DiD)")
    else:
        logger.info("✓ No differential pre-trends detected")

    logger.info("\n✓ All outputs saved to:")
    logger.info(f"  - Tables: {OUTPUTS_TABLES}")
    logger.info(f"  - Log: {OUTPUTS_LOGS / '12_robustness.log'}")


if __name__ == '__main__':
    main()
