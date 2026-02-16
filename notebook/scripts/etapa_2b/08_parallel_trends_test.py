"""
Etapa 2b.8 — Teste formal de tendências paralelas (H0: todos coefs pré = 0).
Lê event_study_*.csv, calcula teste conjunto e salva outputs/tables/parallel_trends_test.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import OUTCOMES, OUTPUTS_TABLES


def main():
    print("=" * 60)
    print("TESTE FORMAL DE TENDÊNCIAS PARALELAS")
    print("=" * 60)

    results_pt = []

    for outcome, label in OUTCOMES.items():
        path = OUTPUTS_TABLES / f"event_study_{outcome}.csv"
        if not path.exists():
            continue

        df_coefs = pd.read_csv(path)
        pre_coefs = df_coefs[df_coefs["is_pre"] & ~df_coefs["is_reference"]]

        if len(pre_coefs) == 0:
            continue

        n_sig = (pre_coefs["p_value"] < 0.05).sum()
        max_abs_coef = pre_coefs["coef"].abs().max()
        se_nonzero = pre_coefs["se"].replace(0, np.nan)
        max_abs_t = (pre_coefs["coef"] / se_nonzero).abs().max()
        if pd.isna(max_abs_t):
            max_abs_t = 0.0

        pre_t_stats = (pre_coefs["coef"] / pre_coefs["se"].replace(0, np.nan)).fillna(0).values
        n_pre = len(pre_t_stats)
        f_stat = np.mean(pre_t_stats**2)
        p_joint = 1 - stats.chi2.cdf(f_stat * n_pre, df=n_pre)

        status = "PARALELAS" if n_sig == 0 and p_joint > 0.10 else "PREOCUPAÇÃO"

        results_pt.append({
            "Outcome": label,
            "N coefs pré": n_pre,
            "Sig. individuais (p<0.05)": int(n_sig),
            "Max |t-stat|": f"{max_abs_t:.2f}",
            "p-valor conjunto": f"{p_joint:.3f}",
            "Status": status,
        })

        print(f"\n{label}:")
        print(f"  Coefs pré: {n_pre}")
        print(f"  Significativos (p<0.05): {n_sig}")
        print(f"  Max |coef|: {max_abs_coef:.4f}")
        print(f"  Teste conjunto p-valor: {p_joint:.3f}")
        print(f"  → {status}")

    df_pt = pd.DataFrame(results_pt)
    df_pt.to_csv(OUTPUTS_TABLES / "parallel_trends_test.csv", index=False)
    print(f"\nSalvo: {OUTPUTS_TABLES / 'parallel_trends_test.csv'}")


if __name__ == "__main__":
    main()
