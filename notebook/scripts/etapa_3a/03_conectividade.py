"""
Script 03: Construir índice de conectividade municipal
Entrada: anatel_pre_tratamento.parquet, ibge_municipios.parquet
Saída:   data/processed/conectividade_municipal.parquet

penetracao_bl = media_acessos_pre / domicilios
alta_conectividade = 1 se penetracao_bl > mediana
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    ANATEL_PRE_FILE,
    IBGE_MUNICIPIOS_FILE,
    CONECTIVIDADE_FILE,
    MIN_POPULACAO,
)


def log(msg):
    print(msg, flush=True)


def build_conectividade():
    """Merge Anatel + IBGE, calcula penetração e dummies de conectividade."""
    if not ANATEL_PRE_FILE.exists():
        raise FileNotFoundError(f"Rodar 01_anatel.py antes. Falta: {ANATEL_PRE_FILE}")
    if not IBGE_MUNICIPIOS_FILE.exists():
        raise FileNotFoundError(f"Rodar 02_ibge.py antes. Falta: {IBGE_MUNICIPIOS_FILE}")

    df_anatel = pd.read_parquet(ANATEL_PRE_FILE)
    df_ibge = pd.read_parquet(IBGE_MUNICIPIOS_FILE)

    df_ibge["id_municipio"] = df_ibge["id_municipio"].astype(str).str.zfill(7)
    df_anatel["id_municipio"] = df_anatel["id_municipio"].astype(str).str.zfill(7)

    df = df_anatel.merge(df_ibge, on="id_municipio", how="inner")
    df["penetracao_bl"] = df["media_acessos_pre"] / df["domicilios"].clip(lower=1)

    mediana = df["penetracao_bl"].median()
    q25 = df["penetracao_bl"].quantile(0.25)
    q75 = df["penetracao_bl"].quantile(0.75)
    df["alta_conectividade"] = (df["penetracao_bl"] > mediana).astype(int)
    df["conectividade_q75"] = (df["penetracao_bl"] > q75).astype(int)
    df["conectividade_q25"] = (df["penetracao_bl"] > q25).astype(int)

    # Apenas municípios com população >= MIN_POPULACAO (para alinhar com filtro do painel)
    df = df[df["populacao"] >= MIN_POPULACAO].copy()
    df.to_parquet(CONECTIVIDADE_FILE, index=False)
    log(f"  Mediana penetração: {mediana:.4f}")
    log(f"  Alta conectividade: {df['alta_conectividade'].sum():,} municípios")
    log(f"  Salvo: {CONECTIVIDADE_FILE.name} — {len(df):,} municípios")
    return df


if __name__ == "__main__":
    build_conectividade()
