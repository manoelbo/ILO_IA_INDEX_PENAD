"""
Etapa 2b.12 — Síntese dos achados: resultados principais, event study, heterogeneidade, robustez.
Lê CSVs gerados pelos scripts anteriores e imprime resumo.
"""

import sys
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import OUTCOMES, OUTPUTS_TABLES


def main():
    print("=" * 70)
    print("SÍNTESE DOS PRINCIPAIS ACHADOS — ETAPA 2b")
    print("=" * 70)

    df_results = pd.read_csv(OUTPUTS_TABLES / "did_main_results.csv")

    print("\n1. RESULTADOS DiD PRINCIPAIS (Model 3: FE + Controls)")
    print("-" * 50)
    main = df_results[df_results["model"] == "Model 3: FE + Controls (MAIN)"]
    for _, row in main.iterrows():
        label = OUTCOMES.get(row["outcome"], row["outcome"])
        sig = "SIGNIFICATIVO" if row["p_value"] < 0.05 else "não significativo"
        stars = row["stars"] if pd.notna(row.get("stars")) else ""
        print(
            f"  {label}: β = {row['coef']:.4f}{stars} "
            f"(SE = {row['se']:.4f}, p = {row['p_value']:.3f}) — {sig}"
        )

    print("\n2. EVENT STUDY")
    print("-" * 50)
    for outcome, label in OUTCOMES.items():
        path = OUTPUTS_TABLES / f"event_study_{outcome}.csv"
        if path.exists():
            df_c = pd.read_csv(path)
            pre_sig = ((df_c["is_pre"]) & (df_c["p_value"] < 0.05)).sum()
            post_sig = (
                (~df_c["is_pre"]) & (~df_c["is_reference"]) & (df_c["p_value"] < 0.05)
            ).sum()
            print(f"  {label}: {pre_sig} coefs pré sig., {post_sig} coefs pós sig.")

    print("\n3. HETEROGENEIDADE (Triple-DiD)")
    print("-" * 50)
    het_path = OUTPUTS_TABLES / "heterogeneity_triple_did.csv"
    if het_path.exists():
        df_het = pd.read_csv(het_path)
        sig_results = df_het[df_het["interaction_pval"] < 0.10]
        if len(sig_results) > 0:
            for _, row in sig_results.iterrows():
                print(
                    f"  {row['outcome_label']} × {row['group']}: "
                    f"β_inter = {row['interaction']:.4f}{row.get('interaction_stars','')} "
                    f"(total = {row['total_effect']:.4f})"
                )
        else:
            print("  Nenhum efeito heterogêneo significativo (p<0.10)")
    else:
        print("  (Arquivo não encontrado)")

    print("\n4. ROBUSTEZ")
    print("-" * 50)
    rob_path = OUTPUTS_TABLES / "robustness_results.csv"
    if rob_path.exists():
        df_robust = pd.read_csv(rob_path)
        for test_type in df_robust["test_type"].unique():
            sub = df_robust[df_robust["test_type"] == test_type]
            n_sig = (sub["p_value"] < 0.10).sum()
            n_total = len(sub)
            print(f"  {test_type}: {n_sig}/{n_total} significativos")
    else:
        print("  (Arquivo não encontrado)")

    print("\n5. COMPARAÇÃO COM ETAPA ANTERIOR (PNAD)")
    print("-" * 50)
    print("  PNAD (DiD antigo): efeito médio n.s. em renda e horas")
    print("  PNAD (heterogeneidade): jovens -0.75*** horas, superior +0.45** horas")
    print("  CAGED (esta etapa): ver resultados acima")
    print("  Nota: dados e outcomes diferentes — PNAD mede estoques, CAGED mede fluxos")

    print("\n6. LIMITAÇÕES")
    print("-" * 50)
    limitacoes = [
        "1. CAGED cobre apenas emprego formal (CLT); informalidade não capturada.",
        "2. Fluxos ≠ estoques: queda em admissões pode indicar menor rotatividade.",
        "3. Índice ILO é global; pode não capturar especificidades brasileiras.",
        "4. Janela Jan/2021–Jun/2025 (54 meses): exclui 2020 (COVID); 2025 limitado a 6 meses.",
        "5. ChatGPT como proxy de IA generativa; difusão gradual, não instantânea.",
        "6. Crosswalk 2d: agregação em 43 sub-major groups perde variação intragrupo.",
        "7. Crosswalk 4d: erro de medição possível (fallback hierárquico 6 níveis).",
        "8. Outliers salariais: winsorização P1/P99 aplicada.",
    ]
    for lim in limitacoes:
        print(f"  {lim}")

    print(f"\n{'=' * 70}")
    print("FIM DA ETAPA 2b")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
