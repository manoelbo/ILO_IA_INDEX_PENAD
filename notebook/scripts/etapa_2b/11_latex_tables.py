"""
Etapa 2b.11 — Tabela LaTeX dos resultados DiD principais (Model 3).
Lê did_main_results.csv, gera table_did_main.tex.
"""

import sys
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import OUTPUTS_TABLES


def main():
    df_results = pd.read_csv(OUTPUTS_TABLES / "did_main_results.csv")
    main = df_results[df_results["model"] == "Model 3: FE + Controls (MAIN)"]

    outcomes_order = ["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_adm"]

    coef_line = r"Post $\times$ Alta Exp."
    se_line = ""
    for outcome in outcomes_order:
        row = main[main["outcome"] == outcome]
        if len(row) > 0:
            r = row.iloc[0]
            stars = r["stars"] if pd.notna(r.get("stars")) else ""
            coef_line += f" & {r['coef']:.4f}{stars}"
            se_line += f" & ({r['se']:.4f})"
        else:
            coef_line += " & —"
            se_line += " & —"

    n_line = "N"
    cl_line = "Clusters"
    for outcome in outcomes_order:
        row = main[main["outcome"] == outcome]
        if len(row) > 0:
            r = row.iloc[0]
            n_line += f" & {int(r['n_obs']):,}"
            ncl = r.get("n_clusters")
            cl_line += f" & {int(ncl) if pd.notna(ncl) and ncl != '' else '—'}"
        else:
            n_line += " & —"
            cl_line += " & —"

    latex_main = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Efeitos DiD sobre Emprego Formal: Resultados Principais}",
        r"\label{tab:did_main}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r" & (1) Log(Adm.) & (2) Log(Desl.) & (3) Saldo & (4) Log(Salário) \\",
        r"\midrule",
        coef_line + r" \\",
        se_line + r" \\",
        r"\midrule",
        n_line + r" \\",
        cl_line + r" \\",
        r"FE Ocupação & \checkmark & \checkmark & \checkmark & \checkmark \\",
        r"FE Período & \checkmark & \checkmark & \checkmark & \checkmark \\",
        r"Controles & \checkmark & \checkmark & \checkmark & \checkmark \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}\small",
        r"\item Erros padrão clusterizados por ocupação (CBO 4d). * $p<0.10$, ** $p<0.05$, *** $p<0.01$.",
        r"\item Controles: idade média, \% mulheres e \% superior completo nas admissões.",
        r"\item Tratamento: top 20\% de exposição à IA (índice ILO, 2 dígitos ISCO-08). Período: Jan/2021–Jun/2025 (54 meses). Salários winsorizados P1/P99.",
        r"\end{tablenotes}",
        r"\end{table}",
    ]

    latex_text = "\n".join(latex_main)
    out_path = OUTPUTS_TABLES / "table_did_main.tex"
    with open(out_path, "w") as f:
        f.write(latex_text)

    print(f"Tabela LaTeX salva: {out_path}")
    print("\nPreview:")
    print(latex_text[:800] + "...")


if __name__ == "__main__":
    main()
