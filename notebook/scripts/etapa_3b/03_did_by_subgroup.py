"""
Etapa 3b.3 — DiD simples (post × alta_exp) separado para alta e baixa conectividade (motivação Triple-DiD).
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
    out.to_csv(OUTPUTS_TABLES / "did_by_subgroup_etapa3b.csv", index=False)
    print("DiD por subgrupo de conectividade:")
    print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    main()
