"""
Etapa 3b.4 — Triple-DiD principal: outcome ~ triple_did + duplas | cbo_4d + uf_periodo.
"""

import sys
from pathlib import Path

import pandas as pd
import pyfixest as pf

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from config import PAINEL_3A_FILE, OUTPUTS_TABLES, VCOV_SPEC, OUTCOMES


def main():
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
    out.to_csv(OUTPUTS_TABLES / "triple_did_main_etapa3b.csv", index=False)
    print("Triple-DiD (coef. triple_did):")
    print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    main()
