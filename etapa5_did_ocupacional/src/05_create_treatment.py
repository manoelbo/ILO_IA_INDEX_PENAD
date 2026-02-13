"""
Script 05: Criação de variáveis de tratamento para DiD
=======================================================

Cria variáveis de tratamento baseadas na exposição à IA:
- Thresholds de exposição (percentis calculados no período pré)
- Dummies de tratamento (alta_exp, alta_exp_10, alta_exp_25)
- Quintis de exposição
- Interações DiD (post × tratamento)

Entrada: data/processed/pnad_panel_exposure.parquet
Saída: data/processed/pnad_panel_did_ready.parquet (FINAL ANALYTIC DATASET)
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from utils.weighted_stats import weighted_quantile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '05_create_treatment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def compute_treatment_thresholds(df):
    """
    Calcula thresholds de exposição no período pré-tratamento.

    Importante: Thresholds devem ser computados APENAS no período pré,
    usando pesos populacionais, para evitar contaminação pós-tratamento.

    Retorna:
    --------
    dict : Thresholds para cada percentil definido em settings
    """

    logger.info("Computando thresholds de tratamento...")

    # Filtrar período pré-tratamento
    df_pre = df[df['post'] == 0].copy()

    logger.info(f"  Usando período pré-tratamento: {df_pre['post'].sum() == 0}")
    logger.info(f"  N observações pré: {len(df_pre):,}")

    # Remover observações sem exposure_score
    df_pre = df_pre[df_pre['exposure_score'].notna()]

    logger.info(f"  N com exposure_score: {len(df_pre):,}")

    # Computar percentis ponderados
    thresholds = {}

    for name, percentil in PERCENTILE_THRESHOLDS.items():
        threshold = weighted_quantile(
            df_pre['exposure_score'],
            df_pre['peso'],
            percentil
        )
        thresholds[name] = threshold

        # Nome legível
        pct_label = int((1 - percentil) * 100)  # 0.80 → Top 20%
        logger.info(f"  {name} (top {pct_label}%): {threshold:.4f}")

    return thresholds


def create_treatment_dummies(df, thresholds):
    """
    Cria dummies de tratamento baseadas nos thresholds.

    Parâmetros:
    -----------
    df : DataFrame
    thresholds : dict
        Thresholds computados em compute_treatment_thresholds()

    Retorna:
    --------
    DataFrame : Com dummies de tratamento
    """

    logger.info("")
    logger.info("Criando dummies de tratamento...")

    df = df.copy()

    # Criar dummies para cada threshold
    for name, threshold in thresholds.items():
        # Usar o nome diretamente do dicionário
        # name já vem como 'alta_exp_10', 'alta_exp_20', 'alta_exp_25'
        df[name] = (df['exposure_score'] >= threshold).astype(int)

        # Contar
        n_treated = df[name].sum()
        pct_treated = n_treated / len(df) * 100

        logger.info(f"  {name}: {n_treated:,} ({pct_treated:.1f}%)")

    # Criar alias para especificação principal (alta_exp_20 → alta_exp)
    df['alta_exp'] = df['alta_exp_20']

    return df


def create_quintile_categories(df):
    """
    Cria quintis de exposição (ponderados pela população).

    Quintis são categorizados como: Q1 (Baixa), Q2, Q3, Q4, Q5 (Alta)
    """

    logger.info("")
    logger.info("Criando quintis de exposição...")

    df = df.copy()

    # Remover missing antes de criar quintis
    df_with_exposure = df[df['exposure_score'].notna()].copy()

    # Criar quintis ponderados
    # Nota: pd.qcut não suporta pesos nativamente, então usamos weighted_quantile
    from utils.weighted_stats import weighted_quantile

    quintile_thresholds = [
        weighted_quantile(df_with_exposure['exposure_score'], df_with_exposure['peso'], q)
        for q in [0.20, 0.40, 0.60, 0.80]
    ]

    # Criar bins (removendo duplicatas)
    all_bins = [-np.inf] + quintile_thresholds + [np.inf]
    unique_bins = []
    for b in all_bins:
        if not unique_bins or b != unique_bins[-1]:
            unique_bins.append(b)

    # Criar labels dinamicamente baseado no número de bins únicos
    n_categories = len(unique_bins) - 1
    if n_categories == 5:
        labels = ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
    elif n_categories == 4:
        labels = ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4 (Alta)']
    elif n_categories == 3:
        labels = ['Baixa', 'Média', 'Alta']
    elif n_categories == 2:
        labels = ['Baixa', 'Alta']
    else:
        labels = [f'Q{i+1}' for i in range(n_categories)]

    logger.info(f"  Criando {n_categories} categorias de exposição (bins únicos: {len(unique_bins)})")

    # Aplicar thresholds para criar quintis
    df_with_exposure['quintil_exp'] = pd.cut(
        df_with_exposure['exposure_score'],
        bins=unique_bins,
        labels=labels,
        include_lowest=True
    )

    # Merge de volta ao DataFrame completo
    df = df.merge(
        df_with_exposure[['quintil_exp']],
        left_index=True,
        right_index=True,
        how='left',
        suffixes=('', '_new')
    )

    # Se havia quintil_exp antes, remover
    if 'quintil_exp_new' in df.columns:
        df['quintil_exp'] = df['quintil_exp_new']
        df.drop('quintil_exp_new', axis=1, inplace=True)

    # Distribuição
    logger.info("  Distribuição por quintil (população):")
    for quintil in ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']:
        pop = df[df['quintil_exp'] == quintil]['peso'].sum() / 1e6
        pct = pop / (df['peso'].sum() / 1e6) * 100
        logger.info(f"    {quintil}: {pop:.1f}M ({pct:.1f}%)")

    return df


def create_did_interactions(df):
    """
    Cria interações DiD (post × tratamento).

    Estas são as variáveis de interesse na regressão DiD.
    """

    logger.info("")
    logger.info("Criando interações DiD...")

    df = df.copy()

    # Interação principal: post × alta_exp
    df['did'] = df['post'] * df['alta_exp']

    # Interações com thresholds alternativos
    df['did_10'] = df['post'] * df['alta_exp_10']
    df['did_25'] = df['post'] * df['alta_exp_25']

    logger.info("  ✓ Interações DiD criadas")

    return df


def validate_treatment_assignment(df):
    """
    Valida atribuição de tratamento.

    Verificações:
    - Tratamento é constante dentro de ocupação?
    - Há variação suficiente em tratamento?
    - Todas as células (post × tratamento) têm observações?
    """

    logger.info("")
    logger.info("="*70)
    logger.info("VALIDAÇÃO DE TRATAMENTO")
    logger.info("="*70)

    # 1. Tratamento constante dentro de ocupação?
    variation_within_occ = (
        df.groupby('cod_ocupacao')['alta_exp']
        .nunique()
    )

    occ_with_variation = (variation_within_occ > 1).sum()

    if occ_with_variation > 0:
        logger.warning(f"  ⚠️ {occ_with_variation} ocupações com variação em alta_exp")
        logger.warning("     (Tratamento deve ser constante dentro de ocupação!)")
    else:
        logger.info("  ✓ Tratamento constante dentro de todas as ocupações")

    # 2. Cross-tab post × tratamento
    logger.info("")
    logger.info("  Distribuição: post × alta_exp (população em milhões)")

    crosstab_pop = pd.crosstab(
        df['post'],
        df['alta_exp'],
        values=df['peso'],
        aggfunc='sum'
    ) / 1e6

    crosstab_pop.index = ['Pré-tratamento', 'Pós-tratamento']
    crosstab_pop.columns = ['Baixa Exposição', 'Alta Exposição']

    logger.info("\n" + crosstab_pop.round(1).to_string())

    # 3. Verificar se todas as células têm observações suficientes
    min_cell = crosstab_pop.min().min()

    if min_cell < 1:  # Menos de 1M pessoas
        logger.warning(f"  ⚠️ Alguma célula com < 1M pessoas (mínimo: {min_cell:.2f}M)")
    else:
        logger.info(f"  ✓ Todas as células com população suficiente (mínimo: {min_cell:.1f}M)")

    # 4. Salvar cross-tab
    crosstab_path = OUTPUTS_TABLES / 'treatment_definition_summary.csv'
    crosstab_pop.to_csv(crosstab_path)
    logger.info(f"\n  Tabela salva em: {crosstab_path}")

    return crosstab_pop


def save_threshold_table(thresholds):
    """Salva tabela de thresholds"""

    threshold_df = pd.DataFrame([
        {
            'Especificação': name.replace('alta_exp_', 'Top '),
            'Percentil': f"p{int(PERCENTILE_THRESHOLDS[name]*100)}",
            'Threshold': f"{value:.4f}"
        }
        for name, value in thresholds.items()
    ])

    threshold_path = OUTPUTS_TABLES / 'exposure_thresholds.csv'
    threshold_df.to_csv(threshold_path, index=False)

    logger.info("")
    logger.info("Thresholds de exposição:")
    logger.info("\n" + threshold_df.to_string(index=False))
    logger.info(f"\nSalvo em: {threshold_path}")


if __name__ == "__main__":

    # Carregar dados
    logger.info("Carregando painel com exposição...")
    df = pd.read_parquet(DATA_PROCESSED / "pnad_panel_exposure.parquet")
    logger.info(f"Carregado: {len(df):,} observações\n")

    logger.info("="*70)
    logger.info("CRIAÇÃO DE VARIÁVEIS DE TRATAMENTO")
    logger.info("="*70)
    logger.info("")

    # 1. Computar thresholds (no período pré)
    thresholds = compute_treatment_thresholds(df)
    save_threshold_table(thresholds)

    # 2. Criar dummies de tratamento
    df = create_treatment_dummies(df, thresholds)

    # 3. Criar quintis
    df = create_quintile_categories(df)

    # 4. Criar interações DiD
    df = create_did_interactions(df)

    # 5. Validar
    validate_treatment_assignment(df)

    # Salvar dataset final
    output_path = DATA_PROCESSED / "pnad_panel_did_ready.parquet"

    logger.info("")
    logger.info("="*70)
    logger.info("DATASET FINAL PARA ANÁLISE DID")
    logger.info("="*70)
    logger.info(f"Salvando em: {output_path}")

    df.to_parquet(output_path, index=False)

    logger.info("")
    logger.info(f"✓ Dataset pronto: {len(df):,} observações")
    logger.info(f"✓ Variáveis criadas: {len(df.columns)} colunas")
    logger.info("")
    logger.info("="*70)
    logger.info("FASE 2 (DATA PREPARATION) CONCLUÍDA")
    logger.info("="*70)
    logger.info("Próximos passos (Fase 3 - Análise Descritiva):")
    logger.info("  - python src/06_balance_table.py")
    logger.info("  - python src/07_parallel_trends.py")
    logger.info("  - python src/08_quintile_analysis.py")
