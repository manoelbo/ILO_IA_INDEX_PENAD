"""
Etapa 2b.9 — Análise de heterogeneidade (Triple-DiD).
Lê painel_2b_ready, cria variáveis de grupo, estima Triple-DiD, salva heterogeneity_triple_did.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import OUTCOMES, OUTPUTS_TABLES, PAINEL_2B_FILE, VCOV_SPEC

HETEROGENEITY_GROUPS = {
    "jovem_adm": "Idade (jovem ≤ 30)",
    "feminino_adm": "Gênero (feminino)",
    "alta_educ_adm": "Educação (superior)",
}


def main():
    df = pd.read_parquet(PAINEL_2B_FILE)
    df_het = df.copy()

    pre_mask = df_het["post"] == 0
    mediana_mulher = df_het.loc[pre_mask, "pct_mulher_adm"].median()
    mediana_educ = df_het.loc[pre_mask, "pct_superior_adm"].median()

    df_het["jovem_adm"] = (df_het["idade_media_adm"] <= 30).astype(int)
    df_het["feminino_adm"] = (df_het["pct_mulher_adm"] > mediana_mulher).astype(int)
    df_het["alta_educ_adm"] = (df_het["pct_superior_adm"] > mediana_educ).astype(int)

    print("Medianas pré-tratamento:")
    print(f"  % Mulher: {mediana_mulher:.3f}")
    print(f"  % Superior: {mediana_educ:.3f}")

    results_het = []

    for group_var, group_label in HETEROGENEITY_GROUPS.items():
        df_het["post_alta"] = df_het["post"] * df_het["alta_exp"]
        df_het["post_group"] = df_het["post"] * df_het[group_var]
        df_het["alta_group"] = df_het["alta_exp"] * df_het[group_var]
        df_het["post_alta_group"] = (
            df_het["post"] * df_het["alta_exp"] * df_het[group_var]
        )

        for outcome, outcome_label in OUTCOMES.items():
            if outcome not in df_het.columns:
                continue

            df_out = df_het[df_het[outcome].notna()].copy()
            formula = (
                f"{outcome} ~ post_alta_group + post_alta + post_group + alta_group "
                f"+ idade_media_adm + pct_mulher_adm + pct_superior_adm "
                f"| cbo_4d + periodo"
            )

            try:
                model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)

                main_coef = float(model.coef().loc["post_alta"])
                main_se = float(model.se().loc["post_alta"])
                inter_coef = float(model.coef().loc["post_alta_group"])
                inter_se = float(model.se().loc["post_alta_group"])
                inter_pval = float(model.pvalue().loc["post_alta_group"])

                total_effect = main_coef + inter_coef
                total_se = np.sqrt(main_se**2 + inter_se**2)

                stars = (
                    "***"
                    if inter_pval < 0.01
                    else "**"
                    if inter_pval < 0.05
                    else "*"
                    if inter_pval < 0.10
                    else ""
                )

                results_het.append({
                    "outcome": outcome,
                    "outcome_label": outcome_label,
                    "group": group_label,
                    "main_effect": main_coef,
                    "interaction": inter_coef,
                    "interaction_se": inter_se,
                    "interaction_pval": inter_pval,
                    "interaction_stars": stars,
                    "total_effect": total_effect,
                    "total_se": total_se,
                })

                if inter_pval < 0.10:
                    print(
                        f"  ** {outcome_label} × {group_label}: "
                        f"interação = {inter_coef:.4f}{stars} (p={inter_pval:.3f})"
                    )

            except Exception as e:
                print(f"  ERRO: {outcome} × {group_var}: {e}")

    df_het_results = pd.DataFrame(results_het)
    df_het_results.to_csv(OUTPUTS_TABLES / "heterogeneity_triple_did.csv", index=False)

    print("\n\nRESUMO DA HETEROGENEIDADE:")
    sig_results = df_het_results[df_het_results["interaction_pval"] < 0.10]
    if len(sig_results) > 0:
        print(f"Efeitos heterogêneos significativos (p<0.10): {len(sig_results)}")
        for _, row in sig_results.iterrows():
            print(
                f"  {row['outcome_label']} × {row['group']}: "
                f"β_inter = {row['interaction']:.4f}{row['interaction_stars']}"
            )
    else:
        print("Nenhum efeito heterogêneo significativo detectado.")

    print(f"\nSalvo: {OUTPUTS_TABLES / 'heterogeneity_triple_did.csv'}")


if __name__ == "__main__":
    main()
