"""
Etapa 3b.5 — Event study por grupo de conectividade (alta vs. baixa).
Estima dummies (tempo_relativo × alta_exp) separadamente para cada grupo.
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import pyfixest as pf

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from config import PAINEL_3A_FILE, OUTPUTS_TABLES, VCOV_SPEC, BIN_MIN, BIN_MAX, REFERENCE_PERIOD


def main():
    df = pd.read_parquet(PAINEL_3A_FILE)
    df["t_binned"] = df["tempo_relativo_meses"].clip(lower=BIN_MIN, upper=BIN_MAX)
    outcome = "ln_salario_real_adm"
    if outcome not in df.columns:
        outcome = "ln_salario_adm"
    results = []
    for conn_val, conn_label in [(1, "alta"), (0, "baixa")]:
        d = df[(df["alta_conectividade"] == conn_val) & df[outcome].notna()].copy()
        if len(d) < 500:
            continue
        ts = sorted(d["t_binned"].unique())
        ts = [t for t in ts if t != REFERENCE_PERIOD]
        did_vars = []
        for t in ts:
            v = f"did_t{t}"
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
                v = f"did_t{t}"
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
    out.to_csv(OUTPUTS_TABLES / "event_study_by_connect_etapa3b.csv", index=False)
    print(f"Event study por conectividade salvo: {len(out)} linhas")
    return out


if __name__ == "__main__":
    main()
