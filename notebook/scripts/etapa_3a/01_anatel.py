"""
Script 01: Download Anatel — Banda Larga Fixa (pré-tratamento)
Fonte: Base dos Dados br_anatel_banda_larga_fixa
Período pré-tratamento: 2021 + Jan–Out/2022 (evitar endogeneidade)
Saída: data/processed/anatel_pre_tratamento.parquet
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    GCP_PROJECT_ID,
    ANO_PRE_CONECT,
    MES_FIM_PRE_CONECT,
    ANATEL_PRE_FILE,
)


def log(msg):
    print(msg, flush=True)


def download_anatel():
    """Query BigQuery Anatel e salva agregado por município (média pré-tratamento)."""
    # Nome da tabela no Base dos Dados pode variar; usar microdados
    # Se falhar, verificar: bd.list_tables(dataset_id='br_anatel_banda_larga_fixa')
    query = f"""
    SELECT
        ano,
        mes,
        id_municipio,
        SUM(acessos) AS total_acessos,
        SUM(CASE WHEN LOWER(SAFE_CAST(tecnologia AS STRING)) LIKE '%fibra%' THEN acessos ELSE 0 END) AS acessos_fibra
    FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
    WHERE ano IN (2021, {ANO_PRE_CONECT})
      AND (ano < {ANO_PRE_CONECT} OR mes <= {MES_FIM_PRE_CONECT})
    GROUP BY ano, mes, id_municipio
    """
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT_ID)
        log("  Executando query Anatel (BigQuery)...")
        t0 = time.time()
        df = client.query(query).to_dataframe(create_bqstorage_client=True)
        log(f"  Linhas: {len(df):,} em {time.time()-t0:.0f}s")
    except Exception as e:
        log(f"  BigQuery falhou: {e}")
        try:
            import basedosdados as bd
            df = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID)
        except Exception as e2:
            raise RuntimeError(f"Anatel: BigQuery e basedosdados falharam. {e2}") from e2

    # Agregar por município: média mensal de acessos no pré; % fibra = soma(fibra)/soma(total)
    out = df.groupby("id_municipio").agg(
        media_acessos_pre=("total_acessos", "mean"),
        soma_acessos=("total_acessos", "sum"),
        soma_fibra=("acessos_fibra", "sum"),
    ).reset_index()
    out["pct_fibra_pre"] = out["soma_fibra"] / out["soma_acessos"].clip(lower=1)
    out = out[["id_municipio", "media_acessos_pre", "pct_fibra_pre"]]
    out.to_parquet(ANATEL_PRE_FILE, index=False)
    log(f"  Salvo: {ANATEL_PRE_FILE.name} — {len(out):,} municípios")
    return out


if __name__ == "__main__":
    download_anatel()
