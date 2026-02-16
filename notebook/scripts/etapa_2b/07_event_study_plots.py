"""
Etapa 2b.7 — Gráficos do event study.
Lê outputs/tables/event_study_*.csv e gera outputs/figures/event_study_all_outcomes.png.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import COLORS, OUTCOMES, OUTPUTS_FIGURES, OUTPUTS_TABLES


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

    event_study_results = {}
    for outcome in OUTCOMES:
        path = OUTPUTS_TABLES / f"event_study_{outcome}.csv"
        if path.exists():
            event_study_results[outcome] = pd.read_csv(path)

    if not event_study_results:
        print("Nenhum event_study_*.csv encontrado.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, (outcome, label) in enumerate(OUTCOMES.items()):
        if outcome not in event_study_results:
            continue
        ax = axes[i]
        df_coefs = event_study_results[outcome]

        pre = df_coefs[df_coefs["is_pre"] & ~df_coefs["is_reference"]]
        post = df_coefs[~df_coefs["is_pre"] & ~df_coefs["is_reference"]]
        ref = df_coefs[df_coefs["is_reference"]]

        ax.fill_between(
            df_coefs["t"],
            df_coefs["ci_low"],
            df_coefs["ci_high"],
            alpha=0.15,
            color="gray",
        )
        ax.scatter(
            pre["t"], pre["coef"],
            color=COLORS["pre"],
            s=30,
            zorder=5,
            label="Pré-tratamento",
        )
        ax.scatter(
            post["t"], post["coef"],
            color=COLORS["post"],
            s=30,
            zorder=5,
            label="Pós-tratamento",
        )
        ax.scatter(
            ref["t"], ref["coef"],
            color="black",
            s=60,
            marker="D",
            zorder=6,
            label="Referência",
        )
        ax.plot(
            df_coefs["t"],
            df_coefs["coef"],
            color="gray",
            linewidth=0.8,
            alpha=0.5,
        )
        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.axvline(x=0, color="gray", linestyle="--", alpha=0.7)
        ax.set_title(label)
        ax.set_xlabel("Meses relativos ao ChatGPT")
        ax.set_ylabel("Coeficiente DiD")
        ax.legend(fontsize=7)

    plt.suptitle(
        "Event Study: Efeito da IA Generativa sobre Emprego Formal",
        fontsize=14,
        fontweight="bold",
    )
    plt.tight_layout()
    out_path = OUTPUTS_FIGURES / "event_study_all_outcomes.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Gráficos salvos em {out_path}")


if __name__ == "__main__":
    main()
