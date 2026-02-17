"""
Etapa 3b.2 — Tabela de balanço por alta vs. baixa conectividade (pré-tratamento).
"""

import sys
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from config import PAINEL_3A_FILE, OUTPUTS_TABLES


def main():
    df = pd.read_parquet(PAINEL_3A_FILE)
    pre = df[df["post"] == 0]
    balance = pre.groupby("alta_conectividade").agg(
        n_obs=("cbo_4d", "count"),
        admissoes_media=("admissoes", "mean"),
        salario_medio=("salario_medio_adm", "mean"),
        penetracao_media=("penetracao_bl", "mean"),
        pct_superior_media=("pct_superior_adm", "mean"),
    ).round(4)
    balance.to_csv(OUTPUTS_TABLES / "balance_conectividade_etapa3b.csv")
    print("Balanço por conectividade (pré):")
    print(balance)
    print(f"Salvo: {OUTPUTS_TABLES / 'balance_conectividade_etapa3b.csv'}")
    return balance


if __name__ == "__main__":
    main()
