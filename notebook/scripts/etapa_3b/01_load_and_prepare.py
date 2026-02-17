"""
Etapa 3b.1 — Carregar painel 3a, winsorizar salários (P1/P99), checar colunas obrigatórias.
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from config import PAINEL_3A_FILE, OUTCOMES

REQUIRED = ["triple_did", "post_alta_exp", "post_alta_conect", "alta_exp_alta_conect", "uf_periodo", "cbo_4d", "id_municipio", "post", "alta_exp", "alta_conectividade"]


def main():
    if not PAINEL_3A_FILE.exists():
        raise FileNotFoundError(f"Rodar Etapa 3a antes. Falta: {PAINEL_3A_FILE}")
    df = pd.read_parquet(PAINEL_3A_FILE)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")
    for c in ["salario_medio_adm", "salario_real_adm"]:
        if c in df.columns:
            lo, hi = df[c].quantile(0.01), df[c].quantile(0.99)
            df[c] = df[c].clip(lo, hi)
    if "ln_salario_real_adm" in df.columns:
        df["ln_salario_real_adm"] = np.log(df["salario_real_adm"].clip(lower=1))
    print(f"Painel carregado: {len(df):,} obs | {df['id_municipio'].nunique():,} municípios | {df['cbo_4d'].nunique()} ocupações")
    return df


if __name__ == "__main__":
    df = main()
