"""
Etapa 2b - Análise DiD: CAGED + ILO

Fluxo:
  01. Load e preparação do painel
  02. Balance table
  03. Visualização de tendências paralelas
  04. Regressão DiD principal
  05. Checkpoint DiD
  06. Event study
  07. Gráficos event study
  08. Teste formal de tendências paralelas
  09. Análise de heterogeneidade
  10. Robustez
  11. Tabelas LaTeX
  12. Síntese dos resultados

Saída: data/output/did_results*.parquet + tabelas LaTeX

Uso:
  python src/scripts/etapa_2b_analise_did_caged_ilo.py
"""

"""
Configuração compartilhada — Etapa 2b (Análise DiD)
Caminhos, parâmetros de estimação e constantes usadas por todos os scripts.
"""

import sys
import time
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pyfixest as pf
from scipy import stats
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
# Suprimir aviso do pyfixest quando variável é omitida por colinearidade (ex.: pct_mulher_adm)
warnings.filterwarnings("ignore", message=".*dropped due to multicollinearity.*", category=UserWarning)

# ---------------------------------------------------------------------------
# Caminhos (relativos à raiz do repositório)
# ---------------------------------------------------------------------------
# Raiz: scripts/etapa_2b/config.py → etapa_2b → scripts → notebook → repo
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_OUTPUT = REPO_ROOT / "data" / "output"
OUTPUTS_TABLES = REPO_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = REPO_ROOT / "outputs" / "figures"
OUTPUTS_LOGS = REPO_ROOT / "outputs" / "logs"

for d in [DATA_OUTPUT, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

# Arquivos de dados
PAINEL_2A_FILE = DATA_OUTPUT / "painel_caged_did_ready.parquet"
PAINEL_2B_FILE = DATA_OUTPUT / "painel_2b_ready.parquet"
EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"
GENERAL_CONTROL_COLUMNS = [
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
]
GENERAL_CONTROLS = " + ".join(GENERAL_CONTROL_COLUMNS)

# ---------------------------------------------------------------------------
# Parâmetros de estimação DiD
# ---------------------------------------------------------------------------
TREATMENT_VAR = "alta_exp"  # Especificação principal: MTE agregado para ISCO-08 2d
TREATMENT_VAR_4D = "alta_exp_4d"  # Robustez: MTE em destinos ISCO-08 4d
CLUSTER_VAR = "cbo_4d"  # Cluster de erros padrão
VCOV_SPEC = {"CRV1": "cbo_4d"}  # Cluster-robust (CRV1)
REFERENCE_PERIOD = -1  # Mês t=-1 como referência no event study
ALPHA = 0.05  # Nível de significância

# Evento: lançamento do ChatGPT (Nov/2022), pós a partir de Dez/2022
ANO_TRATAMENTO = 2022
MES_TRATAMENTO = 12

# Scores contínuos para tratamento contínuo
EXPOSURE_SCORE_MAIN = "exposure_score_2d"  # MTE -> ISCO-08 2d, sem fallback numerico
EXPOSURE_SCORE_4D = "exposure_score_4d"  # MTE -> ISCO-08 4d, sem fallback numerico

# Outcomes principais
OUTCOMES = {
    "ln_admissoes": "Log(Admissões)",
    "ln_desligamentos": "Log(Desligamentos)",
    "saldo": "Saldo Líquido",
    "ln_salario_adm": "Log(Salário Admissão)",
    # Heterogeneidade demográfica (salários por grupo)
    "ln_salario_mulher": "Log(Salário Mulheres)",
    "ln_salario_homem": "Log(Salário Homens)",
    "ln_salario_jovem": "Log(Salário Jovens)",
    "ln_salario_naojovem": "Log(Salário Não-Jovens)",
    "ln_salario_branco": "Log(Salário Brancos)",
    "ln_salario_negro": "Log(Salário Negros)",
    "ln_salario_superior": "Log(Salário Superior)",
    "ln_salario_medio": "Log(Salário Médio)",
    # Heterogeneidade: volumes
    "ln_admissoes_mulher": "Log(Admissões Mulheres)",
    "ln_admissoes_homem": "Log(Admissões Homens)",
    "ln_admissoes_jovem": "Log(Admissões Jovens)",
    "ln_admissoes_negro": "Log(Admissões Negros)",
}

# Outcomes secundários
OUTCOMES_SECONDARY = {
    "ln_salario_sm": "Log(Salário em SM)",
}

# Event study: binning dos extremos
BIN_MIN = -12  # Agrupar t <= -12 no pré
BIN_MAX = 24   # Agrupar t >= 24 no pós

# Placebo temporal (Teste 2 de robustez)
PLACEBO_ANO = 2021
PLACEBO_MES = 12

# Cores para gráficos
COLORS = {
    "pre": "#1f77b4",
    "post": "#d62728",
    "ci": "#cccccc",
    "treated": "#ff7f0e",
    "control": "#2ca02c",
}


def print_config():
    """Imprime a configuração atual."""
    print("=" * 60)
    print("CONFIGURAÇÃO — Etapa 2b (Análise DiD)")
    print("=" * 60)
    print(f"  Repo root:      {REPO_ROOT}")
    print(f"  Notebook dir:   {REPO_ROOT}")
    print(f"  Data output:    {DATA_OUTPUT}")
    print(f"  Outputs tables: {OUTPUTS_TABLES}")
    print(f"  Outputs figures:{OUTPUTS_FIGURES}")
    print(f"  Evento:         ChatGPT — Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
    print(f"  Painel 2a:      {PAINEL_2A_FILE} (existe: {PAINEL_2A_FILE.exists()})")
    print("=" * 60)


# if __name__ == "__main__":
#     print_config()


def validate_crosswalk_spec(df, source_label):
    """Fail early if the panel was not built with the official MTE crosswalk."""
    if "crosswalk_spec" not in df.columns:
        raise ValueError(f"{source_label} não tem coluna crosswalk_spec. Regerar a Etapa 2a.")
    specs = set(df["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_CROSSWALK_SPEC}:
        raise ValueError(
            f"{source_label} usa especificação de crosswalk inesperada: {sorted(specs)}. "
            f"Esperado: {EXPECTED_CROSSWALK_SPEC}"
        )


def validate_demographic_controls(df, source_label):
    """Fail early when the analytic panel was built without required controls."""
    missing = [col for col in GENERAL_CONTROL_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"{source_label} não tem controles demográficos obrigatórios: {missing}.")
    max_negra = pd.to_numeric(df["pct_negra_adm"], errors="coerce").max(skipna=True)
    if pd.isna(max_negra) or float(max_negra) == 0.0:
        raise ValueError(f"{source_label}: pct_negra_adm.max() == {max_negra}. Regerar a Etapa 2a.")



# # ============================================================
# # 01_load_and_prepare.py
# # ============================================================

# """
# Etapa 2b.1 — Carregar painel do 2a, winsorizar salários e salvar painel pronto para DiD.
# Saída: data/output/painel_2b_ready.parquet
# """

# from pathlib import Path

# import numpy as np
# import pandas as pd

# # Permitir importar config quando executado do repo root ou do notebook
# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_01():
    # ---------------------------------------------------------------------------
    # Carregar painel
    # ---------------------------------------------------------------------------
    df = pd.read_parquet(PAINEL_2A_FILE)
    validate_crosswalk_spec(df, str(PAINEL_2A_FILE))
    validate_demographic_controls(df, str(PAINEL_2A_FILE))

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


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 02_balance_table.py
# # ============================================================

# """
# Etapa 2b.2 — Tabela de balanço (pré-tratamento).
# Lê painel_2b_ready.parquet, agrega por ocupação no pré, calcula diferença normalizada.
# Saída: outputs/tables/balance_table_pre.csv
# """

# from pathlib import Path

# import numpy as np
# import pandas as pd

# SCRIPTS_DIR = Path(__file__).resolve().parent


BALANCE_THRESHOLD = 0.25

COVARIATES = {
    "admissoes_media": "Admissões (média mensal)",
    "desligamentos_media": "Desligamentos (média mensal)",
    "saldo_media": "Saldo (média mensal)",
    "salario_media": "Salário médio (R$)",
    "idade_media": "Idade média",
    "pct_mulher": "% Mulheres",
    "pct_superior": "% Superior completo",
    "pct_negra": "% Negros (pretos+pardos)",
    "n_meses": "Meses com dados",
}


def step_02():
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
        pct_negra=("pct_negra_adm", "mean"),
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
    if not df_balance.empty:
        df_balance["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    print("\nTabela de Balanço (Pré-Tratamento):")
    print(df_balance.to_string(index=False))

    df_balance.to_csv(OUTPUTS_TABLES / "balance_table_pre.csv", index=False)
    print(f"\nSalvo: {OUTPUTS_TABLES / 'balance_table_pre.csv'}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 03_parallel_trends_visual.py
# # ============================================================

# """
# Etapa 2b.3 — Tendências paralelas (inspeção visual).
# Lê painel_2b_ready, agrega por periodo_num e alta_exp, gera gráficos 2x2.
# Saída: outputs/figures/parallel_trends_all_outcomes.png
# """

# from pathlib import Path

# import matplotlib.pyplot as plt
# import pandas as pd
# import seaborn as sns

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_03():
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


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 04_did_main.py
# # ============================================================

# """
# Etapa 2b.4 — Estimação DiD principal (6 modelos por outcome).
# Lê painel_2b_ready, prepara df_reg, estima com pyfixest, salva did_main_results.csv.
# """

# from pathlib import Path

# import pandas as pd
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent



def estimate_did(df, outcome, formula, label, vcov_spec=None):
    """Estima um modelo DiD e retorna resultados formatados."""
    vcov_spec = vcov_spec or VCOV_SPEC
    try:
        model = pf.feols(formula, data=df, vcov=vcov_spec)
        coef_names = model.coef().index.tolist()
        did_coef_name = [
            c
            for c in coef_names
            if "post" in c.lower()
            and ("alta" in c.lower() or "exposure" in c.lower())
        ]
        if not did_coef_name:
            did_coef_name = [coef_names[0]]

        name = did_coef_name[0]
        coef = float(model.coef().loc[name])
        se = float(model.se().loc[name])
        pval = float(model.pvalue().loc[name])
        n_obs = len(df)
        n_clusters = getattr(model, "_N_clusters", None)

        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""

        return {
            "model": label,
            "outcome": outcome,
            "crosswalk_spec": (
                df["crosswalk_spec"].dropna().iloc[0]
                if "crosswalk_spec" in df.columns and df["crosswalk_spec"].notna().any()
                else EXPECTED_CROSSWALK_SPEC
            ),
            "coef": coef,
            "se": se,
            "p_value": pval,
            "stars": stars,
            "n_obs": n_obs,
            "n_clusters": n_clusters,
        }
    except Exception as e:
        print(f"  ERRO em {label}/{outcome}: {e}")
        return None


def step_04():
    df = pd.read_parquet(PAINEL_2B_FILE)
    df_reg = df.copy()

    numeric_cols = [
        "admissoes", "desligamentos", "saldo", "ln_admissoes",
        "ln_desligamentos", "ln_salario_adm", "salario_medio_adm",
        "idade_media_adm", "pct_mulher_adm", "pct_superior_adm", "pct_negra_adm",
        "post", "alta_exp", "exposure_score_2d", "exposure_score_4d",
        "ln_salario_mulher", "ln_salario_homem", "ln_salario_jovem", "ln_salario_naojovem",
        "ln_salario_branco", "ln_salario_negro", "ln_salario_superior", "ln_salario_medio",
        "ln_admissoes_mulher", "ln_admissoes_homem", "ln_admissoes_jovem", "ln_admissoes_negro",
    ]
    for col in numeric_cols:
        if col in df_reg.columns:
            df_reg[col] = pd.to_numeric(df_reg[col], errors="coerce")

    df_reg["post_alta"] = df_reg["post"] * df_reg["alta_exp"]
    df_reg["post_exposure_2d"] = df_reg["post"] * df_reg["exposure_score_2d"]
    df_reg["post_alta_4d"] = df_reg["post"] * df_reg["alta_exp_4d"]
    df_reg["post_exposure_4d"] = df_reg["post"] * df_reg["exposure_score_4d"]

    print("Variância dos outcomes:")
    for var in OUTCOMES:
        if var in df_reg.columns:
            v = df_reg[var].var()
            print(f"  {var}: {v:.4f} {'(OK)' if v > 0.001 else '(WARNING: variância muito baixa)'}")

    all_results = []

    for outcome, label in OUTCOMES.items():
        if outcome not in df_reg.columns:
            print(f"SKIP: {outcome} não encontrado")
            continue

        print(f"\n{'='*40}")
        print(f"Outcome: {label} ({outcome})")
        print(f"{'='*40}")

        df_out = df_reg[df_reg[outcome].notna()].copy()

        r1 = estimate_did(
            df_out, outcome,
            f"{outcome} ~ post_alta + post + alta_exp",
            "Model 1: Basic",
        )
        r2 = estimate_did(
            df_out, outcome,
            f"{outcome} ~ post_alta | cbo_4d + periodo",
            "Model 2: FE",
        )
        r3 = estimate_did(
            df_out, outcome,
            f"{outcome} ~ post_alta + {GENERAL_CONTROLS} | cbo_4d + periodo",
            "Model 3: FE + Controls (MAIN)",
        )
        r4 = estimate_did(
            df_out, outcome,
            f"{outcome} ~ post_exposure_2d + {GENERAL_CONTROLS} | cbo_4d + periodo",
            "Model 4: Continuous (2d)",
        )

        df_out_4d = df_out[df_out["exposure_score_4d"].notna()].copy()
        r5 = estimate_did(
            df_out_4d, outcome,
            f"{outcome} ~ post_alta_4d + {GENERAL_CONTROLS} | cbo_4d + periodo",
            "Model 5: FE + Controls (4d)",
        )
        r6 = estimate_did(
            df_out_4d, outcome,
            f"{outcome} ~ post_exposure_4d + {GENERAL_CONTROLS} | cbo_4d + periodo",
            "Model 6: Continuous (4d)",
        )

        for r in [r1, r2, r3, r4, r5, r6]:
            if r:
                all_results.append(r)
                print(f"  {r['model']}: β={r['coef']:.4f}{r['stars']} (SE={r['se']:.4f}, p={r['p_value']:.3f}, N={r['n_obs']:,})")

    df_results = pd.DataFrame(all_results)
    out_path = OUTPUTS_TABLES / "did_main_results.csv"
    df_results.to_csv(out_path, index=False)
    print(f"\nResultados salvos em: {out_path}")

    # Robustez: cluster em cbo_2d (mesma especificação principal)
    vcov_2d = {"CRV1": "cbo_2d"}
    robustez_results = []
    for outcome, label in OUTCOMES.items():
        if outcome not in df_reg.columns:
            continue
        if outcome not in ("ln_salario_adm", "ln_salario_jovem"):
            continue
        df_out = df_reg[df_reg[outcome].notna()].copy()
        r = estimate_did(
            df_out, outcome,
            f"{outcome} ~ post_alta + {GENERAL_CONTROLS} | cbo_4d + periodo",
            f"FE+Controls (cluster cbo_2d)",
            vcov_spec=vcov_2d,
        )
        if r:
            r["vcov"] = "cbo_2d"
            robustez_results.append(r)
    if robustez_results:
        pd.DataFrame(robustez_results).to_csv(OUTPUTS_TABLES / "did_robustez_cbo2d.csv", index=False)
        print(f"Robustez (cluster cbo_2d) salva em: {OUTPUTS_TABLES / 'did_robustez_cbo2d.csv'}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 05_checkpoint_did.py
# # ============================================================

# """
# Etapa 2b.5 — CHECKPOINT: resumo dos resultados DiD principais.
# Lê did_main_results.csv e imprime Model 3, Model 5, consistência 2d vs 4d, comparação PNAD.
# """

# from pathlib import Path

# import pandas as pd

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_05():
    df_results = pd.read_csv(OUTPUTS_TABLES / "did_main_results.csv")

    print("=" * 60)
    print("CHECKPOINT — Resultados DiD Principais")
    print("=" * 60)

    print("\nResultados Model 3 (FE + Controls, MTE 2d — PRINCIPAL):")
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


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 06_event_study.py
# # ============================================================

# """
# Etapa 2b.6 — Event study: dummies período × tratamento, referência t=-1, binning extremos.
# Lê painel_2b_ready, estima por outcome, salva outputs/tables/event_study_{outcome}.csv.
# """

# from pathlib import Path

# import numpy as np
# import pandas as pd
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_06():
    df = pd.read_parquet(PAINEL_2B_FILE)
    df_es = df.copy()
    ref_t = REFERENCE_PERIOD

    periodos_relativos = sorted(df_es["tempo_relativo_meses"].unique())
    print(f"Períodos relativos: {periodos_relativos[0]} a {periodos_relativos[-1]}")
    print(f"Referência: t = {ref_t}")

    df_es["t_binned"] = df_es["tempo_relativo_meses"].clip(lower=BIN_MIN, upper=BIN_MAX)

    # Nomes sem '-' para evitar parsing em fórmulas (did_t-12 vira did_tm12)
    def _dummy_name(t):
        return f"did_tm{-t}" if t < 0 else f"did_t{t}"

    did_vars = []
    t_to_name = {}
    for t in sorted(df_es["t_binned"].unique()):
        if t == ref_t:
            continue
        dname = _dummy_name(t)
        t_to_name[t] = dname
        df_es[dname] = ((df_es["t_binned"] == t) & (df_es["alta_exp"] == 1)).astype(int)
        did_vars.append(dname)

    print(f"\nDummies de evento: {len(did_vars)} (excluindo referência t={ref_t})")

    for outcome, label in OUTCOMES.items():
        if outcome not in df_es.columns:
            continue

        df_out = df_es[df_es[outcome].notna()].copy()
        did_terms = " + ".join(did_vars)
        formula = (
            f"{outcome} ~ {did_terms} + {GENERAL_CONTROLS} "
            f"| cbo_4d + periodo"
        )

        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef_index = model.coef().index.tolist()

            coefs = []
            for t in sorted(df_es["t_binned"].unique()):
                if t == ref_t:
                    coefs.append({
                        "t": t,
                        "coef": 0.0,
                        "se": 0.0,
                        "p_value": np.nan,
                        "is_reference": True,
                        "is_pre": t < 0,
                    })
                else:
                    dname = t_to_name.get(t, _dummy_name(t))
                    if dname in coef_index:
                        coefs.append({
                            "t": t,
                            "coef": float(model.coef().loc[dname]),
                            "se": float(model.se().loc[dname]),
                            "p_value": float(model.pvalue().loc[dname]),
                            "is_reference": False,
                            "is_pre": t < 0,
                        })

            df_coefs = pd.DataFrame(coefs)
            df_coefs["ci_low"] = df_coefs["coef"] - 1.96 * df_coefs["se"]
            df_coefs["ci_high"] = df_coefs["coef"] + 1.96 * df_coefs["se"]
            df_coefs["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC

            out_path = OUTPUTS_TABLES / f"event_study_{outcome}.csv"
            df_coefs.to_csv(out_path, index=False)

            pre_sig = ((df_coefs["is_pre"]) & (df_coefs["p_value"] < 0.05)).sum()
            post_sig = (
                (~df_coefs["is_pre"])
                & (~df_coefs["is_reference"])
                & (df_coefs["p_value"] < 0.05)
            ).sum()
            print(f"\n{label}:")
            print(f"  Coeficientes pré significativos (p<0.05): {pre_sig}")
            print(f"  Coeficientes pós significativos (p<0.05): {post_sig}")

        except Exception as e:
            print(f"  ERRO em {outcome}: {e}")

    print(f"\nArquivos salvos em {OUTPUTS_TABLES}/event_study_*.csv")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 07_event_study_plots.py
# # ============================================================

# """
# Etapa 2b.7 — Gráficos do event study.
# Lê outputs/tables/event_study_*.csv e gera outputs/figures/event_study_all_outcomes.png.
# """

# from pathlib import Path

# import matplotlib.pyplot as plt
# import pandas as pd
# import seaborn as sns

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_07():
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


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 08_parallel_trends_test.py
# # ============================================================

# """
# Etapa 2b.8 — Teste formal de tendências paralelas (H0: todos coefs pré = 0).
# Lê event_study_*.csv, calcula teste conjunto e salva outputs/tables/parallel_trends_test.csv.
# """

# from pathlib import Path

# import numpy as np
# import pandas as pd
# from scipy import stats

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_08():
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
    if not df_pt.empty:
        df_pt["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    df_pt.to_csv(OUTPUTS_TABLES / "parallel_trends_test.csv", index=False)
    print(f"\nSalvo: {OUTPUTS_TABLES / 'parallel_trends_test.csv'}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 09_heterogeneity.py
# # ============================================================

# """
# Etapa 2b.9 — Análise de heterogeneidade (Triple-DiD).
# Lê painel_2b_ready, cria variáveis de grupo, estima Triple-DiD, salva heterogeneity_triple_did.csv.
# """

# from pathlib import Path

# import numpy as np
# import pandas as pd
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent


HETEROGENEITY_GROUPS = {
    "jovem_adm": "Idade (jovem ≤ 30)",
    "feminino_adm": "Gênero (feminino)",
    "alta_educ_adm": "Educação (superior)",
}


def step_09():
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
                f"+ {GENERAL_CONTROLS} "
                f"| cbo_4d + periodo"
            )

            try:
                model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
                required_terms = {"post_alta", "post_alta_group"}
                missing_terms = required_terms - set(model.coef().index)
                if missing_terms:
                    print(
                        f"  SKIP: {outcome} × {group_var}: termos removidos por colinearidade "
                        f"({sorted(missing_terms)})"
                    )
                    continue

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
    if not df_het_results.empty:
        df_het_results["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
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


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 10_robustness.py
# # ============================================================

# """
# Etapa 2b.10 — Testes de robustez (cutoffs, placebo, excl. TI, tendências diferenciais, 4d).
# Lê painel_2b_ready e did_main_results.csv, salva robustness_results.csv.
# """

# from pathlib import Path

# import pandas as pd
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_10():
    df = pd.read_parquet(PAINEL_2B_FILE)
    df_reg = df.copy()
    df_reg["post_alta"] = df_reg["post"] * df_reg["alta_exp"]
    df_reg["post_alta_4d"] = df_reg["post"] * df_reg["alta_exp_4d"]

    df_results = pd.read_csv(OUTPUTS_TABLES / "did_main_results.csv")
    results_robust = []

    # TESTE 1: Cutoffs alternativos
    print("TESTE 1: Cutoffs alternativos")
    cutoff_vars = {
        "alta_exp": "Top 20% (MAIN)",
        "alta_exp_10": "Top 10%",
        "alta_exp_25": "Top 25%",
        "alta_exp_mediana": "Mediana",
    }
    for treat_var, treat_label in cutoff_vars.items():
        if treat_var not in df_reg.columns:
            continue
        df_reg[f"post_{treat_var}"] = df_reg["post"] * df_reg[treat_var]
        for outcome, out_label in OUTCOMES.items():
            if outcome not in df_reg.columns:
                continue
            df_out = df_reg[df_reg[outcome].notna()].copy()
            formula = f"{outcome} ~ post_{treat_var} + {GENERAL_CONTROLS} | cbo_4d + periodo"
            try:
                model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
                cname = f"post_{treat_var}"
                coef = float(model.coef().loc[cname])
                se = float(model.se().loc[cname])
                pval = float(model.pvalue().loc[cname])
                stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
                results_robust.append({
                    "outcome": outcome,
                    "test_type": "Alternative Cutoff",
                    "specification": treat_label,
                    "coef": coef,
                    "se": se,
                    "p_value": pval,
                    "stars": stars,
                })
            except Exception as e:
                print(f"  Erro: {outcome}/{treat_label}: {e}")

    # TESTE 2: Placebo temporal
    print("\nTESTE 2: Placebo temporal (evento fictício Dez/2021)")
    df_placebo = df_reg[df_reg["post"] == 0].copy()
    placebo_ref = PLACEBO_ANO * 100 + PLACEBO_MES
    df_placebo["post_placebo"] = (df_placebo["periodo_num"] >= placebo_ref).astype(int)
    df_placebo["did_placebo"] = df_placebo["post_placebo"] * df_placebo["alta_exp"]
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_placebo.columns:
            continue
        df_out = df_placebo[df_placebo[outcome].notna()].copy()
        formula = f"{outcome} ~ did_placebo + {GENERAL_CONTROLS} | cbo_4d + periodo"
        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef = float(model.coef().loc["did_placebo"])
            se = float(model.se().loc["did_placebo"])
            pval = float(model.pvalue().loc["did_placebo"])
            stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
            results_robust.append({
                "outcome": outcome,
                "test_type": "Placebo",
                "specification": f"Placebo ({PLACEBO_MES}/{PLACEBO_ANO})",
                "coef": coef,
                "se": se,
                "p_value": pval,
                "stars": stars,
            })
            status = "PASS" if pval > 0.10 else "FAIL"
            print(f"  {out_label}: β={coef:.4f}{stars} (p={pval:.3f}) → {status}")
        except Exception as e:
            print(f"  Erro: {outcome}: {e}")

    # TESTE 3: Exclusão TI
    print("\nTESTE 3: Exclusão de ocupações de TI")
    df_no_it = df_reg[~df_reg["cbo_4d"].astype(str).str.startswith("21")].copy()
    print(f"  Registros sem TI: {len(df_no_it):,} (removidos: {len(df_reg)-len(df_no_it):,})")
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_no_it.columns:
            continue
        df_out = df_no_it[df_no_it[outcome].notna()].copy()
        formula = f"{outcome} ~ post_alta + {GENERAL_CONTROLS} | cbo_4d + periodo"
        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef = float(model.coef().loc["post_alta"])
            se = float(model.se().loc["post_alta"])
            pval = float(model.pvalue().loc["post_alta"])
            stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
            results_robust.append({
                "outcome": outcome,
                "test_type": "Excl. TI",
                "specification": "Sem ocupações TI",
                "coef": coef,
                "se": se,
                "p_value": pval,
                "stars": stars,
            })
        except Exception as e:
            print(f"  Erro: {outcome}: {e}")

    # TESTE 4: Tendências diferenciais pré
    print("\nTESTE 4: Tendências diferenciais pré-tratamento")
    df_pre_trend = df_reg[df_reg["post"] == 0].copy()
    df_pre_trend["trend_alta"] = df_pre_trend["trend"] * df_pre_trend["alta_exp"]
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_pre_trend.columns:
            continue
        df_out = df_pre_trend[df_pre_trend[outcome].notna()].copy()
        formula = f"{outcome} ~ trend_alta + {GENERAL_CONTROLS} | cbo_4d + periodo"
        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef = float(model.coef().loc["trend_alta"])
            se = float(model.se().loc["trend_alta"])
            pval = float(model.pvalue().loc["trend_alta"])
            stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
            results_robust.append({
                "outcome": outcome,
                "test_type": "Differential Trends",
                "specification": "Trend × Tratamento (pré)",
                "coef": coef,
                "se": se,
                "p_value": pval,
                "stars": stars,
            })
            status = "OK" if pval > 0.10 else "PREOCUPAÇÃO"
            print(f"  {out_label}: β_trend={coef:.6f}{stars} (p={pval:.3f}) → {status}")
        except Exception as e:
            print(f"  Erro: {outcome}: {e}")

    # TESTE 5: Crosswalk 4d
    print("\nTESTE 5: Crosswalk MTE 2d vs MTE 4d")
    df_4d = df_reg[df_reg["exposure_score_4d"].notna()].copy()
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_4d.columns:
            continue
        df_out = df_4d[df_4d[outcome].notna()].copy()
        formula = f"{outcome} ~ post_alta_4d + {GENERAL_CONTROLS} | cbo_4d + periodo"
        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef = float(model.coef().loc["post_alta_4d"])
            se = float(model.se().loc["post_alta_4d"])
            pval = float(model.pvalue().loc["post_alta_4d"])
            stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
            results_robust.append({
                "outcome": outcome,
                "test_type": "Crosswalk 4d",
                "specification": "Score MTE 4d",
                "coef": coef,
                "se": se,
                "p_value": pval,
                "stars": stars,
            })
            r_2d = df_results[
                (df_results["model"] == "Model 3: FE + Controls (MAIN)")
                & (df_results["outcome"] == outcome)
            ]
            if len(r_2d) > 0:
                same_sign = (coef * r_2d.iloc[0]["coef"]) > 0
                status = "CONSISTENTE" if same_sign else "DIVERGE"
                print(f"  {out_label}: 4d β={coef:.4f}{stars} vs 2d β={r_2d.iloc[0]['coef']:.4f} → {status}")
        except Exception as e:
            print(f"  Erro: {outcome}: {e}")

    df_robust = pd.DataFrame(results_robust)
    if not df_robust.empty:
        df_robust["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    df_robust.to_csv(OUTPUTS_TABLES / "robustness_results.csv", index=False)
    print(f"\nResultados de robustez salvos: {OUTPUTS_TABLES / 'robustness_results.csv'}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 11_latex_tables.py
# # ============================================================

# """
# Etapa 2b.11 — Tabela LaTeX dos resultados DiD principais (Model 3).
# Lê did_main_results.csv, gera table_did_main.tex.
# """

# from pathlib import Path

# import pandas as pd

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_11():
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


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 12_synthesis.py
# # ============================================================

# """
# Etapa 2b.12 — Síntese dos achados: resultados principais, event study, heterogeneidade, robustez.
# Lê CSVs gerados pelos scripts anteriores e imprime resumo.
# """

# from pathlib import Path

# import pandas as pd

# SCRIPTS_DIR = Path(__file__).resolve().parent



def step_12():
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
        "6. Crosswalk MTE 2d: cobre 436 CBOs; ocupações sem ponte oficial ficam fora da amostra principal.",
        "7. Crosswalk MTE 4d: robustez granular, ainda sujeita a ambiguidade muitos-para-muitos da ponte MTE/ISCO.",
        "8. Outliers salariais: winsorização P1/P99 aplicada.",
    ]
    for lim in limitacoes:
        print(f"  {lim}")

    print(f"\n{'=' * 70}")
    print("FIM DA ETAPA 2b")
    print(f"{'=' * 70}")


# if __name__ == "__main__":
#     main()


# # =============================================================================
# # MAIN
# # =============================================================================

def main():
    print("=" * 60)
    print("Etapa 2b - Análise DiD: CAGED + ILO")
    print("=" * 60)

    print(f"\n[1/12] step_01..."); step_01()
    print(f"\n[2/12] step_02..."); step_02()
    print(f"\n[3/12] step_03..."); step_03()
    print(f"\n[4/12] step_04..."); step_04()
    print(f"\n[5/12] step_05..."); step_05()
    print(f"\n[6/12] step_06..."); step_06()
    print(f"\n[7/12] step_07..."); step_07()
    print(f"\n[8/12] step_08..."); step_08()
    print(f"\n[9/12] step_09..."); step_09()
    print(f"\n[10/12] step_10..."); step_10()
    print(f"\n[11/12] step_11..."); step_11()
    print(f"\n[12/12] step_12..."); step_12()

    print("\n" + "=" * 60)
    print("Pipeline concluído.")
    print("=" * 60)


if __name__ == "__main__":
    main()
