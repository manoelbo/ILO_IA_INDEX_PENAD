"""
Script 02: Download IBGE — Domicílios, PIB, População por município
Fonte: Base dos Dados (Censo 2022, PIB, População)
Saída: data/processed/ibge_municipios.parquet
"""

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import GCP_PROJECT_ID, IBGE_MUNICIPIOS_FILE, MIN_POPULACAO


def log(msg):
    print(msg, flush=True)


def download_ibge():
    """Busca população (2022), PIB (2021) e domicílios (Censo 2022) por município."""
    # População: br_ibge_populacao.municipio (ano, id_municipio, populacao)
    query_pop = """
    SELECT id_municipio, populacao
    FROM `basedosdados.br_ibge_populacao.municipio`
    WHERE ano = 2022
    """
    # PIB: br_ibge_pib.municipio (não tem coluna populacao; usamos df_pop para PIB per capita)
    query_pib = """
    SELECT id_municipio, pib
    FROM `basedosdados.br_ibge_pib.municipio`
    WHERE ano = 2021
    """
    use_bq = True
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT_ID)
        log("  Query população (2022)...")
        df_pop = client.query(query_pop).to_dataframe(create_bqstorage_client=True)
        log("  Query PIB (2021)...")
        df_pib = client.query(query_pib).to_dataframe(create_bqstorage_client=True)
    except Exception as e:
        log(f"  BigQuery falhou: {e}")
        use_bq = False
        try:
            import basedosdados as bd
            df_pop = bd.read_sql(query_pop, billing_project_id=GCP_PROJECT_ID)
            df_pib = bd.read_sql(query_pib, billing_project_id=GCP_PROJECT_ID)
        except Exception as e2:
            raise RuntimeError(f"IBGE: {e2}") from e2

    # Merge população + PIB
    df = df_pop.merge(
        df_pib[["id_municipio", "pib"]],
        on="id_municipio",
        how="outer",
    )
    df["pib_per_capita"] = df["pib"] / df["populacao"].clip(lower=1)
    # Domicílios: tentar Censo 2022; se não existir, usar população/3 como proxy
    if use_bq:
        try:
            query_dom = """
            SELECT id_municipio, SUM(domicilios_particulares_ocupados) AS domicilios
            FROM `basedosdados.br_ibge_censo_2022.setor_censitario`
            GROUP BY id_municipio
            """
            df_dom = client.query(query_dom).to_dataframe(create_bqstorage_client=True)
            df = df.merge(df_dom, on="id_municipio", how="left")
        except Exception:
            pass
    if "domicilios" not in df.columns or df["domicilios"].isna().all():
        df["domicilios"] = (df["populacao"] / 3).round().clip(lower=1)
        log("  AVISO: domicílios não encontrados; usando proxy populacao/3")

    df = df.rename(columns={"populacao": "populacao_2022"})
    df = df[["id_municipio", "populacao_2022", "domicilios", "pib", "pib_per_capita"]].copy()
    df.columns = ["id_municipio", "populacao", "domicilios", "pib", "pib_per_capita"]
    df.to_parquet(IBGE_MUNICIPIOS_FILE, index=False)
    log(f"  Salvo: {IBGE_MUNICIPIOS_FILE.name} — {len(df):,} municípios")
    return df


if __name__ == "__main__":
    download_ibge()
