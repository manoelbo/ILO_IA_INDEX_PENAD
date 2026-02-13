"""
Script 07: Análise de Tendências Paralelas
===========================================

Validação visual e estatística da hipótese de tendências paralelas.

Entrada: data/processed/pnad_panel_did_ready.parquet
Saídas:
- outputs/figures/parallel_trends_*.png (individual por outcome)
- outputs/figures/parallel_trends_all_outcomes.png (painel)
- outputs/tables/parallel_trends_test_results.csv
"""

import logging
import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from utils.plotting import plot_parallel_trends, plot_multi_panel_trends
from utils.validators import validate_parallel_trends_assumption

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '07_parallel_trends.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_all_trend_plots(df, outcomes=None, treatment='alta_exp'):
    """Gera gráficos individuais para cada outcome"""

    if outcomes is None:
        outcomes = OUTCOMES

    logger.info("Gerando gráficos de tendências paralelas...")

    for outcome in outcomes:
        logger.info(f"  Plotando: {outcome}")

        save_path = OUTPUTS_FIGURES / f"parallel_trends_{outcome}.png"

        try:
            plot_parallel_trends(df, outcome, treatment, save_path=save_path)
        except Exception as e:
            logger.error(f"  Erro ao plotar {outcome}: {e}")

    logger.info(f"  ✓ {len(outcomes)} gráficos individuais gerados")


def generate_multi_panel(df, outcomes=None, treatment='alta_exp'):
    """Gera painel 2×2 com múltiplos outcomes"""

    if outcomes is None:
        outcomes = OUTCOMES[:4]  # Max 4

    logger.info("")
    logger.info("Gerando painel multi-outcome...")

    save_path = OUTPUTS_FIGURES / "parallel_trends_all_outcomes.png"

    plot_multi_panel_trends(df, outcomes, treatment, save_path=save_path)

    logger.info(f"  ✓ Painel salvo em: {save_path}")


def statistical_test_parallel_trends(df, outcomes=None, treatment='alta_exp'):
    """Testa estatisticamente tendências paralelas"""

    if outcomes is None:
        outcomes = OUTCOMES

    logger.info("")
    logger.info("Testando tendências paralelas (estatístico)...")

    results = []

    for outcome in outcomes:
        logger.info(f"  Testando: {outcome}")

        p_value, message = validate_parallel_trends_assumption(df, outcome, treatment)

        results.append({
            'Outcome': outcome,
            'p_value': p_value if p_value is not None else np.nan,
            'Resultado': message,
            'Interpretação': 'Paralelas' if (p_value is not None and p_value > 0.10) else 'Não-paralelas'
        })

        logger.info(f"    {message}")

    results_df = pd.DataFrame(results)

    # Salvar
    results_path = OUTPUTS_TABLES / 'parallel_trends_test_results.csv'
    results_df.to_csv(results_path, index=False)

    logger.info(f"\n  Resultados salvos em: {results_path}")

    return results_df


if __name__ == "__main__":

    # Carregar dados
    logger.info("Carregando dataset DiD final...")
    df = pd.read_parquet(DATA_PROCESSED / "pnad_panel_did_ready.parquet")
    logger.info(f"Carregado: {len(df):,} observações\n")

    logger.info("="*70)
    logger.info("ANÁLISE DE TENDÊNCIAS PARALELAS")
    logger.info("="*70)
    logger.info("")

    # Gráficos individuais
    generate_all_trend_plots(df)

    # Painel multi-outcome
    generate_multi_panel(df)

    # Testes estatísticos
    test_results = statistical_test_parallel_trends(df)

    logger.info("")
    logger.info("="*70)
    logger.info("SUMÁRIO DOS TESTES")
    logger.info("="*70)
    logger.info("\n" + test_results.to_string(index=False))

    logger.info("")
    logger.info("="*70)
    logger.info("ANÁLISE DE TENDÊNCIAS PARALELAS CONCLUÍDA")
    logger.info("="*70)
    logger.info("Próximo passo: python src/08_quintile_analysis.py")
