"""
Etapa 2b.5 — CHECKPOINT: resumo dos resultados DiD principais.
Lê did_main_results.csv e imprime Model 3, Model 5, consistência 2d vs 4d, comparação PNAD.
"""

import sys
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import ALPHA, OUTCOMES, OUTPUTS_TABLES


def main():
    df_results = pd.read_csv(OUTPUTS_TABLES / "did_main_results.csv")

    print("=" * 60)
    print("CHECKPOINT — Resultados DiD Principais")
    print("=" * 60)

    print("\nResultados Model 3 (FE + Controls, 2d — PRINCIPAL):")
    main_results = df_results[df_results["model"] == "Model 3: FE + Controls (MAIN)"]
    for _, row in main_results.iterrows():
        sig = "SIG" if row["p_value"] < ALPHA else "n.s."
        stars = row["stars"] if pd.notna(row.get("stars")) else ""
        print(
            f"  {OUTCOMES.get(row['outcome'], row['outcome'])}: "
            f"β = {row['coef']:.4f}{stars} "
            f"(SE = {row['se']:.4f}, p = {row['p_value']:.3f}) [{sig}]"
        )

    print("\nResultados Model 5 (FE + Controls, 4d — ROBUSTEZ):")
    rob_4d = df_results[df_results["model"] == "Model 5: FE + Controls (4d)"]
    for _, row in rob_4d.iterrows():
        sig = "SIG" if row["p_value"] < ALPHA else "n.s."
        stars = row['stars'] if pd.notna(row.get('stars')) else ''
        print(
            f"  {OUTCOMES.get(row['outcome'], row['outcome'])}: "
            f"β = {row['coef']:.4f}{stars} "
            f"(SE = {row['se']:.4f}, p = {row['p_value']:.3f}) [{sig}]"
        )

    print("\n--- Consistência 2d vs 4d ---")
    for outcome in OUTCOMES:
        r_2d = main_results[main_results["outcome"] == outcome]
        r_4d = rob_4d[rob_4d["outcome"] == outcome]
        if len(r_2d) > 0 and len(r_4d) > 0:
            same_sign = (r_2d.iloc[0]["coef"] * r_4d.iloc[0]["coef"]) > 0
            print(
                f"  {outcome}: {'✓ mesma direção' if same_sign else '⚠ direções opostas'} "
                f"(2d: {r_2d.iloc[0]['coef']:.4f}, 4d: {r_4d.iloc[0]['coef']:.4f})"
            )

    print("\n--- Comparação com Etapa antiga (PNAD, ref.) ---")
    print("  PNAD Model 3: ln_renda β = -0.003 (n.s.), horas β = -0.136 (n.s.)")
    print("  CAGED Model 3: ver resultados acima")
    print("  Nota: outcomes diferentes — CAGED mede fluxos (admissões/demissões),")
    print("  PNAD media estoques (renda/horas de todos os ocupados).")


if __name__ == "__main__":
    main()
