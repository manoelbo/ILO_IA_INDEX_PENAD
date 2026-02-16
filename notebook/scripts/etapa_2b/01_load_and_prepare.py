"""
Etapa 2b.1 — Carregar painel do 2a, winsorizar salários e salvar painel pronto para DiD.
Saída: data/output/painel_2b_ready.parquet
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Permitir importar config quando executado do repo root ou do notebook
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import (
    DATA_OUTPUT,
    OUTCOMES,
    OUTCOMES_SECONDARY,
    PAINEL_2A_FILE,
    PAINEL_2B_FILE,
    TREATMENT_VAR,
)


def main():
    # ---------------------------------------------------------------------------
    # Carregar painel
    # ---------------------------------------------------------------------------
    df = pd.read_parquet(PAINEL_2A_FILE)

    print(f"Painel carregado: {len(df):,} observações")
    print(f"Ocupações: {df['cbo_4d'].nunique()}")
    print(f"Períodos: {df['periodo'].nunique()} meses")
    print(f"Período: {df['periodo'].min()} a {df['periodo'].max()}")
    print(f"\nTratamento ({TREATMENT_VAR}):")
    print(f"  Alta exposição: {df[TREATMENT_VAR].mean():.1%}")
    print(f"  Pré: {df[df['post'] == 0].shape[0]:,} obs")
    print(f"  Pós: {df[df['post'] == 1].shape[0]:,} obs")

    # ---------------------------------------------------------------------------
    # Winsorização de salários (outliers — ver nota no Notebook 2a)
    # ---------------------------------------------------------------------------
    for col_sal in ["salario_medio_adm", "salario_sm"]:
        if col_sal in df.columns:
            p1 = df[col_sal].quantile(0.01)
            p99 = df[col_sal].quantile(0.99)
            # Garantir limite inferior positivo para log (evitar log(0) = -inf)
            lower = max(float(p1), 0.01) if p1 <= 0 else float(p1)
            n_clip = ((df[col_sal] < lower) | (df[col_sal] > p99)).sum()
            df[col_sal] = df[col_sal].clip(lower=lower, upper=p99)
            print(
                f"\nWinsorização {col_sal}: [{p1:.2f}, {p99:.2f}], "
                f"{n_clip} obs clipped ({100 * n_clip / len(df):.1f}%)"
            )

    # Recalcular logs após winsorização
    df["ln_salario_adm"] = np.log(df["salario_medio_adm"])
    df["ln_salario_sm"] = np.log(df["salario_sm"])

    print("Logs salariais recalculados após winsorização.")

    # ---------------------------------------------------------------------------
    # Estatísticas descritivas dos outcomes
    # ---------------------------------------------------------------------------
    all_outcomes = {**OUTCOMES, **OUTCOMES_SECONDARY}
    print("\nEstatísticas descritivas dos outcomes:")
    for var, label in all_outcomes.items():
        if var in df.columns:
            print(f"\n  {label} ({var}):")
            print(f"    N: {df[var].notna().sum():,}")
            print(f"    Média: {df[var].mean():.3f}")
            print(f"    Std: {df[var].std():.3f}")
            print(f"    Min: {df[var].min():.3f}, Max: {df[var].max():.3f}")

    # ---------------------------------------------------------------------------
    # Salvar painel pronto para scripts 02+
    # ---------------------------------------------------------------------------
    df.to_parquet(PAINEL_2B_FILE, index=False)
    print(f"\nPainel salvo: {PAINEL_2B_FILE}")


if __name__ == "__main__":
    main()
