"""
Etapa 3b - Análise Triple-DiD: Município × Conectividade

Fluxo:
  01. Load e preparação do painel Triple-DiD
  02. Balance table por conectividade
  03. DiD por subgrupo de conectividade
  04. Triple-DiD principal
  05. Event study por nível de conectividade
  06. Análise de robustez

Saída: data/output/triple_did_results*.parquet

Uso:
  python src/scripts/etapa_3b_analise_did_municipio_conectividade.py
"""

"""
Configuração compartilhada — Etapa 3b (Análise Triple-DiD)
"""

import warnings
import pandas as pd
import numpy as np
import pyfixest as pf
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*dropped due to multicollinearity.*", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_OUTPUT = REPO_ROOT / "data" / "output"
OUTPUTS_TABLES = REPO_ROOT / "outputs" / "tables"
OUTPUTS_FIGURES = REPO_ROOT / "outputs" / "figures"
OUTPUTS_LOGS = REPO_ROOT / "outputs" / "logs"

for d in [DATA_OUTPUT, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

PAINEL_3A_FILE = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"

# Triple-DiD: cluster por município
CLUSTER_VAR = "id_municipio"
VCOV_SPEC = {"CRV1": "id_municipio"}
REFERENCE_PERIOD = -1
BIN_MIN, BIN_MAX = -12, 24
ANO_TRATAMENTO, MES_TRATAMENTO = 2022, 12

OUTCOMES = {
    "ln_salario_real_adm": "Log(Salário Real Admissão)",
    "ln_admissoes": "Log(Admissões)",
    "ln_desligamentos": "Log(Desligamentos)",
    "saldo": "Saldo Líquido",
    "pct_superior_adm": "% Superior (Admissão)",
    "idade_media_adm": "Idade Média Admissão",
    "ln_salario_mulher": "Log(Salário Mulheres)",
    "ln_salario_homem": "Log(Salário Homens)",
    "ln_salario_jovem": "Log(Salário Jovens)",
}

COLORS = {"pre": "#1f77b4", "post": "#d62728", "ci": "#cccccc", "treated": "#ff7f0e", "control": "#2ca02c"}

REQUIRED = [
    "triple_did",
    "post_alta_exp",
    "post_alta_conect",
    "alta_exp_alta_conect",
    "uf_periodo",
    "cbo_4d",
    "id_municipio",
    "post",
    "alta_exp",
    "alta_conectividade",
]


def print_config():
    print("=" * 60)
    print("CONFIGURAÇÃO — Etapa 3b (Triple-DiD)")
    print("=" * 60)
    print(f"  Painel 3a: {PAINEL_3A_FILE} (existe: {PAINEL_3A_FILE.exists()})")
    print("=" * 60)


# if __name__ == "__main__":
#     print_config()


def validate_crosswalk_spec(df, source_label):
    if "crosswalk_spec" not in df.columns:
        raise ValueError(f"{source_label} não tem coluna crosswalk_spec. Regerar Etapas 2a e 3a.")
    specs = set(df["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_CROSSWALK_SPEC}:
        raise ValueError(
            f"{source_label} usa especificação de crosswalk inesperada: {sorted(specs)}. "
            f"Esperado: {EXPECTED_CROSSWALK_SPEC}"
        )



# # ============================================================
# # 01_load_and_prepare.py
# # ============================================================

# """
# Etapa 3b.1 — Carregar painel 3a, winsorizar salários (P1/P99), checar colunas obrigatórias.
# """

# from pathlib import Path

# import pandas as pd
# import numpy as np

# SCRIPTS_DIR = Path(__file__).resolve().parent
# from config import PAINEL_3A_FILE, OUTCOMES

# REQUIRED = ["triple_did", "post_alta_exp", "post_alta_conect", "alta_exp_alta_conect", "uf_periodo", "cbo_4d", "id_municipio", "post", "alta_exp", "alta_conectividade"]


def step_01():
    if not PAINEL_3A_FILE.exists():
        raise FileNotFoundError(f"Rodar Etapa 3a antes. Falta: {PAINEL_3A_FILE}")
    df = pd.read_parquet(PAINEL_3A_FILE)
    validate_crosswalk_spec(df, str(PAINEL_3A_FILE))
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")
    for c in ["salario_medio_adm", "salario_real_adm"]:
        if c in df.columns:
            lo, hi = df[c].quantile(0.01), df[c].quantile(0.99)
            df[c] = df[c].clip(lo, hi)
    if "ln_salario_real_adm" in df.columns:
        df["ln_salario_real_adm"] = np.log(df["salario_real_adm"].clip(lower=1))
    print(f"Painel carregado: {len(df):,} obs | {df['id_municipio'].nunique():,} municípios | {df['cbo_4d'].nunique()} ocupações")
    return df


# if __name__ == "__main__":
#     df = main()

# # ============================================================
# # 02_balance_conectividade.py
# # ============================================================

# """
# Etapa 3b.2 — Tabela de balanço por alta vs. baixa conectividade (pré-tratamento).
# """

# from pathlib import Path

# import pandas as pd

# SCRIPTS_DIR = Path(__file__).resolve().parent
# from config import PAINEL_3A_FILE, OUTPUTS_TABLES


def step_02():
    df = pd.read_parquet(PAINEL_3A_FILE)
    pre = df[df["post"] == 0]
    balance = pre.groupby("alta_conectividade").agg(
        n_obs=("cbo_4d", "count"),
        admissoes_media=("admissoes", "mean"),
        salario_medio=("salario_medio_adm", "mean"),
        penetracao_media=("penetracao_bl", "mean"),
        pct_superior_media=("pct_superior_adm", "mean"),
    ).round(4)
    balance["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    balance.to_csv(OUTPUTS_TABLES / "balance_conectividade_etapa3b.csv")
    print("Balanço por conectividade (pré):")
    print(balance)
    print(f"Salvo: {OUTPUTS_TABLES / 'balance_conectividade_etapa3b.csv'}")
    return balance


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 03_did_by_subgroup.py
# # ============================================================

# """
# Etapa 3b.3 — DiD simples (post × alta_exp) separado para alta e baixa conectividade (motivação Triple-DiD).
# """

# from pathlib import Path

# import pandas as pd
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent
# from config import PAINEL_3A_FILE, OUTPUTS_TABLES, VCOV_SPEC, OUTCOMES


def step_03():
    df = pd.read_parquet(PAINEL_3A_FILE)
    df["post_alta_exp"] = df["post"] * df["alta_exp"]
    results = []
    for outcome, label in list(OUTCOMES.items())[:5]:
        if outcome not in df.columns:
            continue
        for conn_name, sub in [("alta_conect", df["alta_conectividade"] == 1), ("baixa_conect", df["alta_conectividade"] == 0)]:
            d = df.loc[sub].dropna(subset=[outcome])
            if len(d) < 100:
                continue
            try:
                m = pf.feols(
                    f"{outcome} ~ post_alta_exp | cbo_4d + uf_periodo",
                    data=d,
                    vcov=VCOV_SPEC,
                )
                coef = m.coef().get("post_alta_exp", m.coef().iloc[0])
                se = m.se().get("post_alta_exp", m.se().iloc[0])
                pval = m.pvalue().get("post_alta_exp", m.pvalue().iloc[0])
                results.append({"outcome": outcome, "grupo": conn_name, "coef": float(coef), "se": float(se), "p_value": float(pval)})
            except Exception as e:
                print(f"  Erro {outcome} {conn_name}: {e}")
    out = pd.DataFrame(results)
    if not out.empty:
        out["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    out.to_csv(OUTPUTS_TABLES / "did_by_subgroup_etapa3b.csv", index=False)
    print("DiD por subgrupo de conectividade:")
    print(out.to_string(index=False))
    return out


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 04_triple_did_main.py
# # ============================================================

# """
# Etapa 3b.4 — Triple-DiD principal: outcome ~ triple_did + duplas | cbo_4d + uf_periodo.
# """

# from pathlib import Path

# import pandas as pd
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent
# from config import PAINEL_3A_FILE, OUTPUTS_TABLES, VCOV_SPEC, OUTCOMES


def step_04():
    df = pd.read_parquet(PAINEL_3A_FILE)
    for c in ["triple_did", "post_alta_exp", "post_alta_conect", "alta_exp_alta_conect", "ln_pib_pc"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    results = []
    for outcome, label in OUTCOMES.items():
        if outcome not in df.columns:
            continue
        d = df.dropna(subset=[outcome])
        try:
            # Modelo principal: FE cbo_4d + uf_periodo
            m = pf.feols(
                f"{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo",
                data=d,
                vcov=VCOV_SPEC,
            )
            c_triple = m.coef().get("triple_did")
            if c_triple is not None:
                results.append({
                    "outcome": outcome,
                    "coef": float(c_triple),
                    "se": float(m.se().loc["triple_did"]),
                    "p_value": float(m.pvalue().loc["triple_did"]),
                })
        except Exception as e:
            print(f"  Erro {outcome}: {e}")
    out = pd.DataFrame(results)
    if not out.empty:
        out["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    out.to_csv(OUTPUTS_TABLES / "triple_did_main_etapa3b.csv", index=False)
    print("Triple-DiD (coef. triple_did):")
    print(out.to_string(index=False))
    return out


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 05_event_study_by_connect.py
# # ============================================================

# """
# Etapa 3b.5 — Event study por grupo de conectividade (alta vs. baixa).
# Estima dummies (tempo_relativo × alta_exp) separadamente para cada grupo.
# """

# from pathlib import Path

# import pandas as pd
# import numpy as np
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent
# from config import PAINEL_3A_FILE, OUTPUTS_TABLES, VCOV_SPEC, BIN_MIN, BIN_MAX, REFERENCE_PERIOD


def step_05():
    df = pd.read_parquet(PAINEL_3A_FILE)
    df["t_binned"] = df["tempo_relativo_meses"].clip(lower=BIN_MIN, upper=BIN_MAX)
    outcome = "ln_salario_real_adm"
    if outcome not in df.columns:
        outcome = "ln_salario_adm"
    results = []

    def dummy_name(t):
        t_int = int(t)
        return f"did_tm{-t_int}" if t_int < 0 else f"did_t{t_int}"

    for conn_val, conn_label in [(1, "alta"), (0, "baixa")]:
        d = df[(df["alta_conectividade"] == conn_val) & df[outcome].notna()].copy()
        if len(d) < 500:
            continue
        ts = sorted(d["t_binned"].unique())
        ts = [t for t in ts if t != REFERENCE_PERIOD]
        did_vars = []
        for t in ts:
            v = dummy_name(t)
            d[v] = ((d["t_binned"] == t) & (d["alta_exp"] == 1)).astype(int)
            did_vars.append(v)
        if not did_vars:
            continue
        try:
            m = pf.feols(
                f"{outcome} ~ {' + '.join(did_vars)} | cbo_4d + uf_periodo",
                data=d,
                vcov=VCOV_SPEC,
            )
            for t in ts:
                v = dummy_name(t)
                if v in m.coef().index:
                    results.append({
                        "grupo": conn_label,
                        "t": int(t),
                        "coef": float(m.coef().loc[v]),
                        "se": float(m.se().loc[v]),
                    })
        except Exception as e:
            print(f"  Erro event study {conn_label}: {e}")
    out = pd.DataFrame(results)
    if not out.empty:
        out["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    out.to_csv(OUTPUTS_TABLES / "event_study_by_connect_etapa3b.csv", index=False)
    print(f"Event study por conectividade salvo: {len(out)} linhas")
    return out


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 06_robustness.py
# # ============================================================

# """
# Etapa 3b.6 — Testes de robustez: placebo temporal (Dez/2021) e cutoff Q75 conectividade.
# """

# from pathlib import Path

# import pandas as pd
# import pyfixest as pf

# SCRIPTS_DIR = Path(__file__).resolve().parent
# from config import PAINEL_3A_FILE, OUTPUTS_TABLES, VCOV_SPEC


def step_06():
    df = pd.read_parquet(PAINEL_3A_FILE)
    results = []
    # Placebo: post = 1 a partir de Dez/2021
    df_placebo = df.copy()
    df_placebo["post_placebo"] = ((df_placebo["ano"] == 2021) & (df_placebo["mes"] >= 12)) | (df_placebo["ano"] > 2021)
    df_placebo["triple_did_placebo"] = df_placebo["post_placebo"].astype(int) * df_placebo["alta_exp"] * df_placebo["alta_conectividade"]
    df_placebo["post_alta_exp_placebo"] = df_placebo["post_placebo"].astype(int) * df_placebo["alta_exp"]
    try:
        m = pf.feols(
            "ln_salario_real_adm ~ triple_did_placebo + post_alta_exp_placebo | cbo_4d + uf_periodo",
            data=df_placebo.dropna(subset=["ln_salario_real_adm"]),
            vcov=VCOV_SPEC,
        )
        c = m.coef().get("triple_did_placebo")
        if c is not None:
            results.append({"teste": "placebo_dez2021", "coef": float(c), "p_value": float(m.pvalue().loc["triple_did_placebo"])})
    except Exception as e:
        print(f"  Placebo: {e}")
    # Cutoff Q75: usar conectividade_q75 em vez de alta_conectividade
    if "conectividade_q75" in df.columns:
        df_q75 = df.copy()
        df_q75["triple_did_q75"] = df_q75["post"] * df_q75["alta_exp"] * df_q75["conectividade_q75"]
        df_q75["post_alta_conect_q75"] = df_q75["post"] * df_q75["conectividade_q75"]
        df_q75["alta_exp_alta_conect_q75"] = df_q75["alta_exp"] * df_q75["conectividade_q75"]
        try:
            m2 = pf.feols(
                "ln_salario_real_adm ~ triple_did_q75 + post_alta_exp + post_alta_conect_q75 + alta_exp_alta_conect_q75 | cbo_4d + uf_periodo",
                data=df_q75.dropna(subset=["ln_salario_real_adm"]),
                vcov=VCOV_SPEC,
            )
            c2 = m2.coef().get("triple_did_q75")
            if c2 is not None:
                results.append({"teste": "cutoff_q75", "coef": float(c2), "p_value": float(m2.pvalue().loc["triple_did_q75"])})
        except Exception as e:
            print(f"  Q75: {e}")
    out = pd.DataFrame(results)
    if not out.empty:
        out["crosswalk_spec"] = EXPECTED_CROSSWALK_SPEC
    out.to_csv(OUTPUTS_TABLES / "robustness_etapa3b.csv", index=False)
    print("Robustez:")
    print(out.to_string(index=False))
    return out


# if __name__ == "__main__":
#     main()


# # =============================================================================
# # MAIN
# # =============================================================================

def main():
    print("=" * 60)
    print("Etapa 3b - Análise Triple-DiD: Município × Conectividade")
    print("=" * 60)

    print(f"\n[1/6] step_01..."); step_01()
    print(f"\n[2/6] step_02..."); step_02()
    print(f"\n[3/6] step_03..."); step_03()
    print(f"\n[4/6] step_04..."); step_04()
    print(f"\n[5/6] step_05..."); step_05()
    print(f"\n[6/6] step_06..."); step_06()

    print("\n" + "=" * 60)
    print("Pipeline concluído.")
    print("=" * 60)


if __name__ == "__main__":
    main()
