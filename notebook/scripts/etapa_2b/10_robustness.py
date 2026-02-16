"""
Etapa 2b.10 — Testes de robustez (cutoffs, placebo, excl. TI, tendências diferenciais, 4d).
Lê painel_2b_ready e did_main_results.csv, salva robustness_results.csv.
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
    PLACEBO_ANO,
    PLACEBO_MES,
    VCOV_SPEC,
)


def main():
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
            formula = f"{outcome} ~ post_{treat_var} + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
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
        formula = f"{outcome} ~ did_placebo + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
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
        formula = f"{outcome} ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
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
        formula = f"{outcome} ~ trend_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
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
    print("\nTESTE 5: Crosswalk 2d vs 4d")
    df_4d = df_reg[df_reg["exposure_score_4d"].notna()].copy()
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_4d.columns:
            continue
        df_out = df_4d[df_4d[outcome].notna()].copy()
        formula = f"{outcome} ~ post_alta_4d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef = float(model.coef().loc["post_alta_4d"])
            se = float(model.se().loc["post_alta_4d"])
            pval = float(model.pvalue().loc["post_alta_4d"])
            stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
            results_robust.append({
                "outcome": outcome,
                "test_type": "Crosswalk 4d",
                "specification": "Score 4d (fallback hierárquico 6 níveis)",
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
    df_robust.to_csv(OUTPUTS_TABLES / "robustness_results.csv", index=False)
    print(f"\nResultados de robustez salvos: {OUTPUTS_TABLES / 'robustness_results.csv'}")


if __name__ == "__main__":
    main()
