"""
Script 09: Main DiD Estimation
================================

Estima 4 especificações de Difference-in-Differences com complexidade crescente:
- Model 1: Basic DiD (sem controles, sem FE)
- Model 2: With Fixed Effects (ocupação + período)
- Model 3: FE + Controls (especificação principal)
- Model 4: Continuous Treatment (dose-response)

Outcomes válidos: ln_renda, horas_trabalhadas, informal
(formal e ocupado excluídos por zero variância no pré-período)

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
    OUTCOMES_VALID, PLAUSIBILITY_THRESHOLDS, MIN_CLUSTERS
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '09_regression_did.log'),
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
        logger.error("Install with: pip install pyfixest>=0.11.0")
        return False


def validate_outcome_variance(df, outcome, min_std=0.01):
    """
    Valida se outcome tem variância suficiente para regressão.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Nome da variável dependente
    min_std : float
        Desvio padrão mínimo aceitável

    Returns:
    --------
    tuple (bool, str): (is_valid, message)
    """
    # Remove missing values
    df_clean = df[df[outcome].notna()].copy()

    if len(df_clean) < 1000:
        return False, f"Insufficient observations: {len(df_clean)}"

    # Check overall variance
    std_all = df_clean[outcome].std()
    if std_all < min_std:
        return False, f"Low variance: std={std_all:.6f}"

    # Check pre-period variance
    df_pre = df_clean[df_clean['post'] == 0]
    std_pre = df_pre[outcome].std()
    if std_pre < min_std:
        return False, f"Zero variance in pre-period: std={std_pre:.6f}"

    # Check post-period variance
    df_post = df_clean[df_clean['post'] == 1]
    std_post = df_post[outcome].std()
    if std_post < min_std:
        return False, f"Zero variance in post-period: std={std_post:.6f}"

    # Check treatment/control variance
    for group_name, group_val in [('control', 0), ('treatment', 1)]:
        df_group = df_clean[df_clean['alta_exp'] == group_val]
        if len(df_group) < 100:
            return False, f"Too few observations in {group_name}: {len(df_group)}"
        std_group = df_group[outcome].std()
        if std_group < min_std:
            return False, f"Zero variance in {group_name}: std={std_group:.6f}"

    return True, f"Valid outcome: {len(df_clean):,} obs, std={std_all:.4f}"


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


def flag_implausible_effect(coef, outcome):
    """
    Verifica se efeito estimado é implausível e loga warning.

    Parameters:
    -----------
    coef : float
        Coeficiente estimado
    outcome : str
        Nome do outcome

    Returns:
    --------
    bool: True se implausível, False caso contrário
    """
    threshold = PLAUSIBILITY_THRESHOLDS.get(outcome, 0.20)

    if abs(coef) > threshold:
        logger.warning(f"⚠️  IMPLAUSIBLY LARGE EFFECT for {outcome}: β={coef:.4f}")
        logger.warning(f"    Threshold: |β| < {threshold}")
        logger.warning("    Possible issues:")
        logger.warning("    - Model misspecification")
        logger.warning("    - Outliers in data")
        logger.warning("    - Violation of parallel trends")
        return True

    return False


# ============================================
# MAIN ESTIMATION FUNCTIONS
# ============================================

def estimate_did_model(df, outcome, formula, vcov_spec, weights, model_name):
    """
    Estima um modelo DiD usando pyfixest.

    Parameters:
    -----------
    df : DataFrame
        Dados para estimação
    outcome : str
        Variável dependente
    formula : str
        Fórmula pyfixest (e.g., "Y ~ X | FE")
    vcov_spec : dict or str
        Especificação de erros padrão
    weights : str
        Nome da coluna de pesos
    model_name : str
        Nome do modelo para logging

    Returns:
    --------
    dict: Resultados do modelo {coef, se, t_stat, p_value, ci_low, ci_high, n_obs, r_squared, n_clusters}
    """
    import pyfixest as pf

    logger.info(f"  Estimating {model_name}...")
    logger.info(f"    Formula: {formula}")

    # Prepare data (drop NA in outcome)
    df_reg = df[df[outcome].notna()].copy()
    n_before = len(df_reg)

    # Drop NA in key variables
    key_vars = ['post', 'alta_exp', 'idade', 'mulher', 'negro_pardo', 'superior', 'medio',
                'cod_ocupacao', 'periodo', weights]
    for var in key_vars:
        if var in df_reg.columns:
            df_reg = df_reg[df_reg[var].notna()]

    n_after = len(df_reg)
    if n_after < n_before:
        logger.info(f"    Dropped {n_before - n_after:,} obs with missing values")

    try:
        # Estimate model
        model = pf.feols(
            formula,
            data=df_reg,
            weights=weights,
            vcov=vcov_spec
        )

        # Extract coefficient of interest
        # For DiD models: post:alta_exp or post:exposure_score
        if 'post:alta_exp' in model.coef().index:
            coef_name = 'post:alta_exp'
        elif 'post:exposure_score' in model.coef().index:
            coef_name = 'post:exposure_score'
        else:
            # Fallback: look for any interaction with post
            coef_name = [c for c in model.coef().index if 'post:' in c][0]

        coef = model.coef()[coef_name]
        se = model.se()[coef_name]
        t_stat = model.tstat()[coef_name]
        p_value = model.pvalue()[coef_name]

        ci = model.confint(alpha=0.05)
        ci_low = ci.loc[coef_name, '2.5%']
        ci_high = ci.loc[coef_name, '97.5%']

        # Get model statistics (pyfixest 0.40+ API)
        n_obs = int(model._N)

        # R² (use within R² for FE models, regular R² otherwise)
        if hasattr(model, '_r2_within') and model._r2_within is not None:
            r_squared = model._r2_within
        else:
            r_squared = model._r2 if hasattr(model, '_r2') else np.nan

        # Get number of clusters (if clustered)
        if isinstance(vcov_spec, dict) and 'CRV1' in vcov_spec:
            cluster_var = vcov_spec['CRV1']
            n_clusters = df_reg[cluster_var].nunique()
        else:
            n_clusters = None

        logger.info(f"    ✓ Converged: β={coef:.4f} (SE={se:.4f}, p={p_value:.3f})")

        # Check for implausible effects
        flag_implausible_effect(coef, outcome)

        # Check cluster count
        if n_clusters is not None and n_clusters < MIN_CLUSTERS:
            logger.warning(f"    ⚠️  Few clusters: {n_clusters} < {MIN_CLUSTERS}")

        return {
            'model': model_name,
            'outcome': outcome,
            'coef_name': coef_name,
            'coef': coef,
            'se': se,
            't_stat': t_stat,
            'p_value': p_value,
            'ci_low': ci_low,
            'ci_high': ci_high,
            'stars': add_significance_stars(p_value),
            'n_obs': n_obs,
            'r_squared': r_squared,
            'n_clusters': n_clusters if n_clusters is not None else np.nan
        }

    except Exception as e:
        logger.error(f"    ✗ Estimation failed: {e}")
        return {
            'model': model_name,
            'outcome': outcome,
            'coef_name': np.nan,
            'coef': np.nan,
            'se': np.nan,
            't_stat': np.nan,
            'p_value': np.nan,
            'ci_low': np.nan,
            'ci_high': np.nan,
            'stars': '',
            'n_obs': np.nan,
            'r_squared': np.nan,
            'n_clusters': np.nan,
            'error': str(e)
        }


def estimate_all_specifications(df, outcome):
    """
    Roda todas as 4 especificações DiD para um outcome.

    Parameters:
    -----------
    df : DataFrame
        Dados completos
    outcome : str
        Variável dependente

    Returns:
    --------
    DataFrame: Resultados com uma linha por modelo
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"OUTCOME: {outcome}")
    logger.info(f"{'='*70}")

    # Validate outcome variance
    is_valid, message = validate_outcome_variance(df, outcome)
    logger.info(f"Validation: {message}")

    if not is_valid:
        logger.warning(f"⚠️  Skipping {outcome} - insufficient variance")
        return pd.DataFrame()

    results = []

    # Model 1: Basic DiD (no controls, no FE)
    formula1 = f"{outcome} ~ post:alta_exp + post + alta_exp"
    result1 = estimate_did_model(
        df, outcome, formula1,
        vcov_spec="iid",
        weights="peso",
        model_name="Model 1: Basic"
    )
    results.append(result1)

    # Model 2: With Fixed Effects
    formula2 = f"{outcome} ~ post:alta_exp | cod_ocupacao + periodo"
    result2 = estimate_did_model(
        df, outcome, formula2,
        vcov_spec={"CRV1": "cod_ocupacao"},
        weights="peso",
        model_name="Model 2: FE"
    )
    results.append(result2)

    # Model 3: FE + Controls (MAIN SPECIFICATION)
    formula3 = f"{outcome} ~ post:alta_exp + idade + I(idade**2) + mulher + negro_pardo + superior + medio | cod_ocupacao + periodo"
    result3 = estimate_did_model(
        df, outcome, formula3,
        vcov_spec={"CRV1": "cod_ocupacao"},
        weights="peso",
        model_name="Model 3: FE + Controls (MAIN)"
    )
    results.append(result3)

    # Model 4: Continuous Treatment
    formula4 = f"{outcome} ~ post:exposure_score + idade + I(idade**2) + mulher + negro_pardo + superior + medio | cod_ocupacao + periodo"
    result4 = estimate_did_model(
        df, outcome, formula4,
        vcov_spec={"CRV1": "cod_ocupacao"},
        weights="peso",
        model_name="Model 4: Continuous"
    )
    results.append(result4)

    return pd.DataFrame(results)


def create_regression_table(results_df, outcome):
    """
    Formata resultados em tabela side-by-side para um outcome.

    Parameters:
    -----------
    results_df : DataFrame
        Resultados dos 4 modelos
    outcome : str
        Nome do outcome

    Returns:
    --------
    DataFrame: Tabela formatada
    """
    if results_df.empty:
        return pd.DataFrame()

    # Create formatted table
    table = pd.DataFrame({
        'Variable': ['Coefficient', 'Std. Error', 'Significance', 'N', 'R²', 'Clusters']
    })

    for _, row in results_df.iterrows():
        model = row['model']
        table[model] = [
            f"{row['coef']:.4f}",
            f"({row['se']:.4f})",
            row['stars'],
            f"{row['n_obs']:.0f}" if not pd.isna(row['n_obs']) else '',
            f"{row['r_squared']:.3f}" if not pd.isna(row['r_squared']) else '',
            f"{row['n_clusters']:.0f}" if not pd.isna(row['n_clusters']) else ''
        ]

    return table


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main execution function"""

    logger.info("="*70)
    logger.info("SCRIPT 09: MAIN DiD ESTIMATION")
    logger.info("="*70)
    logger.info("")

    # Check pyfixest
    if not check_pyfixest_installed():
        logger.error("Cannot proceed without pyfixest. Exiting.")
        sys.exit(1)

    # Load data
    data_path = DATA_PROCESSED / "pnad_panel_did_ready.parquet"
    logger.info(f"Loading data: {data_path}")

    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        logger.error("Run Phase 3 scripts first (01-08)")
        sys.exit(1)

    df = pd.read_parquet(data_path)
    logger.info(f"Loaded: {len(df):,} observations")
    logger.info(f"Columns: {list(df.columns)}")

    # Check required variables
    required_vars = ['post', 'alta_exp', 'exposure_score', 'peso', 'cod_ocupacao', 'periodo',
                     'idade', 'mulher', 'negro_pardo', 'superior', 'medio']
    missing = [v for v in required_vars if v not in df.columns]
    if missing:
        logger.error(f"Missing required variables: {missing}")
        sys.exit(1)

    logger.info(f"✓ All required variables present")

    # Estimate for each valid outcome
    all_results = []

    for outcome in OUTCOMES_VALID:
        logger.info("")
        results_df = estimate_all_specifications(df, outcome)

        if not results_df.empty:
            all_results.append(results_df)

            # Save individual outcome results
            output_path = OUTPUTS_TABLES / f"did_{outcome}.csv"
            results_df.to_csv(output_path, index=False)
            logger.info(f"✓ Saved: {output_path}")

            # Create and save formatted table
            table = create_regression_table(results_df, outcome)
            if not table.empty:
                table_path = OUTPUTS_TABLES / f"did_{outcome}_formatted.csv"
                table.to_csv(table_path, index=False)
                logger.info(f"✓ Saved formatted table: {table_path}")

    # Combine all results
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        combined_path = OUTPUTS_TABLES / "did_main_results.csv"
        combined_results.to_csv(combined_path, index=False)
        logger.info("")
        logger.info(f"✓ Saved combined results: {combined_path}")

        # Summary statistics
        logger.info("")
        logger.info("="*70)
        logger.info("SUMMARY OF MAIN RESULTS (Model 3: FE + Controls)")
        logger.info("="*70)

        main_results = combined_results[combined_results['model'] == 'Model 3: FE + Controls (MAIN)']
        for _, row in main_results.iterrows():
            outcome = row['outcome']
            coef = row['coef']
            se = row['se']
            p_val = row['p_value']
            stars = row['stars']

            logger.info(f"{outcome:20s}: β={coef:7.4f}{stars:3s} (SE={se:.4f}, p={p_val:.3f})")

        logger.info("="*70)
        logger.info("")
        logger.info("✓ DiD estimation complete")
        logger.info("")
        logger.info("Next step: python src/10_event_study.py")
    else:
        logger.warning("⚠️  No valid outcomes estimated")
        logger.warning("Check outcome variance and data quality")


if __name__ == "__main__":
    main()
