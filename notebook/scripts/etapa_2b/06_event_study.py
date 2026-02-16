"""
Etapa 2b.6 — Event study: dummies período × tratamento, referência t=-1, binning extremos.
Lê painel_2b_ready, estima por outcome, salva outputs/tables/event_study_{outcome}.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import (
    BIN_MAX,
    BIN_MIN,
    OUTCOMES,
    OUTPUTS_TABLES,
    PAINEL_2B_FILE,
    REFERENCE_PERIOD as REF_T,
    VCOV_SPEC,
)


def main():
    df = pd.read_parquet(PAINEL_2B_FILE)
    df_es = df.copy()

    periodos_relativos = sorted(df_es["tempo_relativo_meses"].unique())
    print(f"Períodos relativos: {periodos_relativos[0]} a {periodos_relativos[-1]}")
    print(f"Referência: t = {REF_T}")

    df_es["t_binned"] = df_es["tempo_relativo_meses"].clip(lower=BIN_MIN, upper=BIN_MAX)

    # Nomes sem '-' para evitar parsing em fórmulas (did_t-12 vira did_tm12)
    def _dummy_name(t):
        return f"did_tm{-t}" if t < 0 else f"did_t{t}"

    did_vars = []
    t_to_name = {}
    for t in sorted(df_es["t_binned"].unique()):
        if t == REF_T:
            continue
        dname = _dummy_name(t)
        t_to_name[t] = dname
        df_es[dname] = ((df_es["t_binned"] == t) & (df_es["alta_exp"] == 1)).astype(int)
        did_vars.append(dname)

    print(f"\nDummies de evento: {len(did_vars)} (excluindo referência t={REF_T})")

    for outcome, label in OUTCOMES.items():
        if outcome not in df_es.columns:
            continue

        df_out = df_es[df_es[outcome].notna()].copy()
        did_terms = " + ".join(did_vars)
        formula = (
            f"{outcome} ~ {did_terms} + idade_media_adm + pct_mulher_adm + pct_superior_adm "
            f"| cbo_4d + periodo"
        )

        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef_index = model.coef().index.tolist()

            coefs = []
            for t in sorted(df_es["t_binned"].unique()):
                if t == REF_T:
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


if __name__ == "__main__":
    main()
