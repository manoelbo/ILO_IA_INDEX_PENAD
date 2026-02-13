"""
Script 01: Download dos microdados PNAD (painel 2021-2024) via BigQuery
===========================================================================

Este script baixa 16 trimestres de dados da PNAD Contínua (2021Q1 a 2024Q4)
para análise Difference-in-Differences do impacto da IA Generativa no mercado
de trabalho brasileiro.

Entrada: Query BigQuery
Saída: data/raw/pnad_panel_2021q1_2024q4.parquet
Dependências: basedosdados, config/settings.py
"""

import logging
import basedosdados as bd
import pandas as pd
import sys
from pathlib import Path
from tqdm import tqdm

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '01_download_panel.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def download_all_quarters(reauth=False, save_individual=True):
    """
    Baixa todos os 16 trimestres (2021Q1-2024Q4) em uma única query do BigQuery.

    Parâmetros:
    -----------
    reauth : bool
        Se True, força reautenticação com Google Cloud
    save_individual : bool
        Se True, salva arquivos parquet individuais por trimestre (além do painel completo)

    Retorna:
    --------
    DataFrame : Dados do painel completo
    """

    logger.info("="*70)
    logger.info("DOWNLOAD DE PAINEL PNAD CONTÍNUA (2021Q1 - 2024Q4)")
    logger.info("="*70)
    logger.info(f"Projeto GCP: {GCP_PROJECT_ID}")
    logger.info(f"Total de trimestres: {len(QUARTERS)}")
    logger.info(f"Período: 2021Q1 a 2024Q4 (pré e pós ChatGPT)")
    logger.info("")

    # Construir query única para todos os trimestres
    query = """
    SELECT
        ano,
        trimestre,
        sigla_uf,
        v2007 AS sexo,
        v2009 AS idade,
        v2010 AS raca,
        vd3004 AS nivel_instrucao,
        vd3005 AS anos_estudo,
        v4010 AS cod_ocupacao,
        vd4002 AS condicao_ocupacao,
        vd4008 AS posicao_ocupacao,
        vd4009 AS tipo_vinculo,
        vd4016 AS rendimento_habitual,
        vd4035 AS horas_trabalhadas,
        v1028 AS peso
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano BETWEEN 2021 AND 2024
      AND v2009 >= 18 AND v2009 <= 65  -- Idade trabalhadora
      AND v4010 IS NOT NULL             -- Código de ocupação válido
    ORDER BY ano, trimestre
    """

    logger.info("Executando query no BigQuery...")
    logger.info("⏳ Isso pode demorar 3-7 minutos para ~70-80M observações, aguarde...")

    try:
        df = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID, reauth=reauth)
        logger.info(f"✓ Download concluído: {len(df):,} observações")
    except Exception as e:
        logger.error(f"Erro no download: {e}")
        logger.error("Dica: Se erro de autenticação, execute com --reauth")
        raise

    # Validação básica
    logger.info("")
    logger.info("Validando download...")
    validate_download(df)

    # Salvar painel completo
    output_path = DATA_RAW / "pnad_panel_2021q1_2024q4.parquet"
    logger.info(f"Salvando painel completo em: {output_path}")
    df.to_parquet(output_path, index=False)

    # Salvar trimestres individuais (opcional, para debug)
    if save_individual:
        logger.info("Salvando trimestres individuais...")
        for (ano, tri) in tqdm(QUARTERS, desc="Salvando arquivos"):
            df_quarter = df[(df['ano'] == ano) & (df['trimestre'] == tri)]
            if len(df_quarter) > 0:
                quarter_path = DATA_RAW / f"pnad_{ano}q{tri}.parquet"
                df_quarter.to_parquet(quarter_path, index=False)

    logger.info("")
    logger.info("="*70)
    logger.info("DOWNLOAD CONCLUÍDO COM SUCESSO")
    logger.info("="*70)

    return df


def validate_download(df):
    """
    Valida qualidade do download.

    Verificações:
    - Todos os 16 trimestres presentes
    - Mínimo de observações por trimestre
    - Todas as 27 UFs presentes
    - População representada razoável
    """

    # Verificar trimestres presentes
    quarters_present = df.groupby(['ano', 'trimestre']).size()
    n_quarters = len(quarters_present)

    logger.info(f"  Trimestres baixados: {n_quarters}/16")

    if n_quarters < 16:
        missing = set(QUARTERS) - set(quarters_present.index)
        logger.warning(f"  ⚠️ Trimestres ausentes: {missing}")
    else:
        logger.info(f"  ✓ Todos os 16 trimestres presentes")

    # Verificar observações por trimestre
    logger.info("")
    logger.info("  Observações por trimestre:")
    for (ano, tri), count in quarters_present.items():
        status = "✓" if count >= MIN_OBS_PER_QUARTER else "⚠️"
        logger.info(f"    {status} {ano}Q{tri}: {count:,}")

    # Verificar UFs
    ufs_present = df['sigla_uf'].nunique()
    logger.info(f"  UFs presentes: {ufs_present}/{N_UFS}")

    if ufs_present < N_UFS:
        missing_ufs = set(REGIAO_MAP.keys()) - set(df['sigla_uf'].unique())
        logger.warning(f"  ⚠️ UFs ausentes: {missing_ufs}")
    else:
        logger.info(f"  ✓ Todas as {N_UFS} UFs presentes")

    # População representada
    pop_total = df['peso'].sum() / 1e6
    pop_per_quarter = df.groupby(['ano', 'trimestre'])['peso'].sum().mean() / 1e6

    logger.info(f"  População total representada: {pop_total:.1f} milhões")
    logger.info(f"  População média por trimestre: {pop_per_quarter:.1f} milhões")

    # Verificar valores missing críticos
    logger.info("")
    logger.info("  Valores missing em variáveis críticas:")
    critical_vars = ['cod_ocupacao', 'idade', 'sexo', 'peso']
    for var in critical_vars:
        missing_pct = df[var].isna().mean() * 100
        status = "✓" if missing_pct < 1 else "⚠️"
        logger.info(f"    {status} {var}: {missing_pct:.2f}%")

    logger.info("")

    # Retornar tabela de resumo
    summary = df.groupby(['ano', 'trimestre']).agg({
        'peso': ['count', 'sum'],
        'sigla_uf': 'nunique'
    }).round(0)

    summary.columns = ['n_obs', 'populacao', 'n_ufs']
    summary['populacao'] = (summary['populacao'] / 1e6).round(1)

    summary_path = OUTPUTS_TABLES / 'download_summary.csv'
    summary.to_csv(summary_path)
    logger.info(f"  Resumo salvo em: {summary_path}")

    return summary


if __name__ == "__main__":
    import sys

    # Usar reauth=True se passar argumento --reauth
    reauth = '--reauth' in sys.argv

    if reauth:
        logger.info("🔐 Modo reauth ativado - será solicitada autenticação Google Cloud")

    # Executar download
    df = download_all_quarters(reauth=reauth, save_individual=True)

    logger.info(f"Arquivo principal: {DATA_RAW / 'pnad_panel_2021q1_2024q4.parquet'}")
    logger.info("Próximo passo: python src/02_clean_panel_data.py")
