"""
Etapa 3b.6 — Testes de robustez: placebo temporal (Dez/2021) e cutoff Q75 conectividade.
"""

import sys
from pathlib import Path

import pandas as pd
import pyfixest as pf

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from config import PAINEL_3A_FILE, OUTPUTS_TABLES, VCOV_SPEC


def main():
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
    out.to_csv(OUTPUTS_TABLES / "robustness_etapa3b.csv", index=False)
    print("Robustez:")
    print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    main()
