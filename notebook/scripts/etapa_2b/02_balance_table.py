"""
Etapa 2b.2 — Tabela de balanço (pré-tratamento).
Lê painel_2b_ready.parquet, agrega por ocupação no pré, calcula diferença normalizada.
Saída: outputs/tables/balance_table_pre.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import OUTPUTS_TABLES, PAINEL_2B_FILE

BALANCE_THRESHOLD = 0.25

COVARIATES = {
    "admissoes_media": "Admissões (média mensal)",
    "desligamentos_media": "Desligamentos (média mensal)",
    "saldo_media": "Saldo (média mensal)",
    "salario_media": "Salário médio (R$)",
    "idade_media": "Idade média",
    "pct_mulher": "% Mulheres",
    "pct_superior": "% Superior completo",
    "n_meses": "Meses com dados",
}


def main():
    df = pd.read_parquet(PAINEL_2B_FILE)
    df_pre = df[df["post"] == 0].copy()

    # Agregar por ocupação (médias no pré)
    ocup_pre = df_pre.groupby("cbo_4d").agg(
        exposure_score=("exposure_score_2d", "first"),
        alta_exp=("alta_exp", "first"),
        admissoes_media=("admissoes", "mean"),
        desligamentos_media=("desligamentos", "mean"),
        saldo_media=("saldo", "mean"),
        salario_media=("salario_medio_adm", "mean"),
        idade_media=("idade_media_adm", "mean"),
        pct_mulher=("pct_mulher_adm", "mean"),
        pct_superior=("pct_superior_adm", "mean"),
        n_meses=("periodo", "nunique"),
    ).reset_index()

    results_balance = []
    for var, label in COVARIATES.items():
        treated = ocup_pre[ocup_pre["alta_exp"] == 1][var].dropna()
        control = ocup_pre[ocup_pre["alta_exp"] == 0][var].dropna()

        mean_t = treated.mean()
        mean_c = control.mean()
        diff = mean_t - mean_c

        pooled_std = np.sqrt((treated.var() + control.var()) / 2)
        std_diff = diff / pooled_std if pooled_std > 0 else np.nan

        results_balance.append({
            "Variável": label,
            "Controle": mean_c,
            "Tratamento": mean_t,
            "Diferença": diff,
            "Diff. Normalizada": std_diff,
            "Balanceado": "✓" if abs(std_diff) < BALANCE_THRESHOLD else "⚠️",
        })

    df_balance = pd.DataFrame(results_balance)
    print("\nTabela de Balanço (Pré-Tratamento):")
    print(df_balance.to_string(index=False))

    df_balance.to_csv(OUTPUTS_TABLES / "balance_table_pre.csv", index=False)
    print(f"\nSalvo: {OUTPUTS_TABLES / 'balance_table_pre.csv'}")


if __name__ == "__main__":
    main()
