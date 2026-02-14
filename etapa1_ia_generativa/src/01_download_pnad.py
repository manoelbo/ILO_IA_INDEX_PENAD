"""
Script 01: Download dos microdados PNAD via BigQuery
Entrada: Query BigQuery
Saída: data/raw/pnad_2025q3.parquet
"""

import logging
import pandas as pd
import re
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '01_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_pnad(reauth=False):
    """Baixa microdados PNAD do BigQuery.

    Se o parquet já existir em data/raw/, carrega direto.
    Senão, baixa do BigQuery.
    """

    # --- Caminho rápido: arquivo local já disponível ---
    pnad_files = sorted(DATA_RAW.glob("pnad_*.parquet"))

    if pnad_files:
        pnad_path = pnad_files[-1]
        logger.info(f"Arquivo PNAD encontrado localmente: {pnad_path.name}")
        df = pd.read_parquet(pnad_path)
        logger.info(f"Carregado: {len(df):,} observações")

        # Validar que o arquivo corresponde à configuração
        match = re.search(r"pnad_(\d{4})q(\d)", pnad_path.name)
        if match:
            ano_arquivo, trim_arquivo = int(match.group(1)), int(match.group(2))
            if ano_arquivo != PNAD_ANO or trim_arquivo != PNAD_TRIMESTRE:
                logger.warning(f"Arquivo é {ano_arquivo} Q{trim_arquivo}, "
                              f"mas config diz {PNAD_ANO} Q{PNAD_TRIMESTRE}!")

        logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")
        logger.info(f"UFs presentes: {df['sigla_uf'].nunique()}")
        return df

    # --- Caminho completo: download via BigQuery ---
    logger.info("Nenhum arquivo PNAD local encontrado. Iniciando download do BigQuery...")
    import basedosdados as bd

    logger.info(f"Projeto GCP: {GCP_PROJECT_ID}")

    # Verificar trimestres disponíveis
    logger.info("Verificando trimestres disponíveis...")
    query_check = """
    SELECT DISTINCT ano, trimestre, COUNT(*) as n_obs
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano >= 2024
    GROUP BY ano, trimestre
    ORDER BY ano DESC, trimestre DESC
    LIMIT 5
    """

    try:
        df_check = bd.read_sql(query_check, billing_project_id=GCP_PROJECT_ID, reauth=reauth)
        logger.info(f"Trimestres disponíveis:\n{df_check}")

        trimestre_existe = len(
            df_check[(df_check['ano'] == PNAD_ANO) & (df_check['trimestre'] == PNAD_TRIMESTRE)]
        ) > 0

        if trimestre_existe:
            ano_usar, trim_usar = PNAD_ANO, PNAD_TRIMESTRE
        else:
            ano_usar = int(df_check.iloc[0]['ano'])
            trim_usar = int(df_check.iloc[0]['trimestre'])
            logger.warning(f"AVISO: {PNAD_ANO} Q{PNAD_TRIMESTRE} indisponível. Usando {ano_usar} Q{trim_usar}")

    except Exception as e:
        logger.error(f"Erro ao verificar trimestres: {e}")
        ano_usar = PNAD_ANO
        trim_usar = PNAD_TRIMESTRE

    # Query principal — inclui TODOS ocupados com código de ocupação válido
    query = f"""
    SELECT
        ano,
        trimestre,
        sigla_uf,
        v2007  AS sexo,
        v2009  AS idade,
        v2010  AS raca_cor,
        vd3004 AS nivel_instrucao,
        v4010  AS cod_ocupacao,
        v4013  AS grupamento_atividade,
        vd4009 AS posicao_ocupacao,
        vd4016 AS rendimento_habitual,
        vd4020 AS rendimento_efetivo,
        vd4031 AS horas_habituais,
        vd4035 AS horas_efetivas,
        v1028  AS peso
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano = {ano_usar}
      AND trimestre = {trim_usar}
      AND v4010 IS NOT NULL
    """

    logger.info(f"Executando query para {ano_usar} Q{trim_usar} (pode demorar 2-5 min)...")
    df = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID, reauth=reauth)

    logger.info(f"Download concluído: {len(df):,} observações")
    logger.info(f"Colunas: {list(df.columns)}")

    # Salvar
    ano_real = int(df['ano'].iloc[0])
    trim_real = int(df['trimestre'].iloc[0])
    output_path = DATA_RAW / f"pnad_{ano_real}q{trim_real}.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Salvo em: {output_path}")

    # Estatísticas básicas
    logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")
    logger.info(f"UFs presentes: {df['sigla_uf'].nunique()}")

    return df

if __name__ == "__main__":
    import sys
    reauth = '--reauth' in sys.argv
    if reauth:
        logger.info("Modo reauth ativado - será solicitada autenticação")
    download_pnad(reauth=reauth)
