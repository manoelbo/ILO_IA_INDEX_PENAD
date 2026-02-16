"""
Etapa 2b.3 — Tendências paralelas (inspeção visual).
Lê painel_2b_ready, agrega por periodo_num e alta_exp, gera gráficos 2x2.
Saída: outputs/figures/parallel_trends_all_outcomes.png
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import (
    ANO_TRATAMENTO,
    COLORS,
    MES_TRATAMENTO,
    OUTPUTS_FIGURES,
    PAINEL_2B_FILE,
)


def main():
    plt.style.use("seaborn-v0_8-paper")
    sns.set_palette("Set2")
    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "figure.titlesize": 14,
        "font.family": "serif",
        "figure.dpi": 150,
    })

    df = pd.read_parquet(PAINEL_2B_FILE)

    ts_grupo = df.groupby(["periodo_num", "alta_exp"]).agg(
        admissoes_total=("admissoes", "sum"),
        desligamentos_total=("desligamentos", "sum"),
        saldo_total=("saldo", "sum"),
        salario_medio=("salario_medio_adm", "mean"),
        n_ocupacoes=("cbo_4d", "nunique"),
    ).reset_index()

    for col in ["admissoes_total", "desligamentos_total", "saldo_total"]:
        ts_grupo[f"{col}_per_ocup"] = ts_grupo[col] / ts_grupo["n_ocupacoes"]

    ts_grupo["grupo"] = ts_grupo["alta_exp"].map({
        0: "Controle (Baixa Exp.)",
        1: "Tratamento (Alta Exp.)",
    })

    outcomes_plot = {
        "admissoes_total_per_ocup": "Admissões médias por ocupação",
        "desligamentos_total_per_ocup": "Desligamentos médios por ocupação",
        "saldo_total_per_ocup": "Saldo médio por ocupação",
        "salario_medio": "Salário médio de admissão (R$)",
    }

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    evento_periodo = ANO_TRATAMENTO * 100 + MES_TRATAMENTO  # 202212

    for i, (var, title) in enumerate(outcomes_plot.items()):
        ax = axes[i]
        for grupo in ["Controle (Baixa Exp.)", "Tratamento (Alta Exp.)"]:
            data = ts_grupo[ts_grupo["grupo"] == grupo]
            color = COLORS["control"] if "Controle" in grupo else COLORS["treated"]
            ax.plot(data["periodo_num"], data[var], label=grupo, color=color, linewidth=1.5)

        ax.axvline(
            x=evento_periodo,
            color="gray",
            linestyle="--",
            alpha=0.7,
            label="ChatGPT (Nov/2022)",
        )
        ax.set_title(title)
        ax.set_xlabel("Período")
        ax.legend(fontsize=8)
        ax.tick_params(axis="x", rotation=45)

    plt.suptitle(
        "Tendências Paralelas: Tratamento vs. Controle",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()
    out_path = OUTPUTS_FIGURES / "parallel_trends_all_outcomes.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Gráficos salvos em {out_path}")


if __name__ == "__main__":
    main()
