"""
Etapa 2b.4 — Estimação DiD principal (6 modelos por outcome).
Lê painel_2b_ready, prepara df_reg, estima com pyfixest, salva did_main_results.csv.
"""

import sys
from pathlib import Path

import pandas as pd
import pyfixest as pf

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config import (
    OUTCOMES,
    OUTPUTS_TABLES,
    PAINEL_2B_FILE,
    VCOV_SPEC,
)


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


def main():
    df = pd.read_parquet(PAINEL_2B_FILE)
    df_reg = df.copy()

    numeric_cols = [
        "admissoes", "desligamentos", "saldo", "ln_admissoes",
        "ln_desligamentos", "ln_salario_adm", "salario_medio_adm",
        "idade_media_adm", "pct_mulher_adm", "pct_superior_adm",
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
            f"{outcome} ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
            "Model 3: FE + Controls (MAIN)",
        )
        r4 = estimate_did(
            df_out, outcome,
            f"{outcome} ~ post_exposure_2d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
            "Model 4: Continuous (2d)",
        )

        df_out_4d = df_out[df_out["exposure_score_4d"].notna()].copy()
        r5 = estimate_did(
            df_out_4d, outcome,
            f"{outcome} ~ post_alta_4d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
            "Model 5: FE + Controls (4d)",
        )
        r6 = estimate_did(
            df_out_4d, outcome,
            f"{outcome} ~ post_exposure_4d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
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
            f"{outcome} ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
            f"FE+Controls (cluster cbo_2d)",
            vcov_spec=vcov_2d,
        )
        if r:
            r["vcov"] = "cbo_2d"
            robustez_results.append(r)
    if robustez_results:
        pd.DataFrame(robustez_results).to_csv(OUTPUTS_TABLES / "did_robustez_cbo2d.csv", index=False)
        print(f"Robustez (cluster cbo_2d) salva em: {OUTPUTS_TABLES / 'did_robustez_cbo2d.csv'}")


if __name__ == "__main__":
    main()
