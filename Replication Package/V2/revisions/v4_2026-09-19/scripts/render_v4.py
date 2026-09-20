"""Render a separate V4 presentation from frozen estimates; never fit models."""
from pathlib import Path
import hashlib
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
REF = ROOT / "results/reference/artifacts/caged"
sys.path.insert(0, str(ROOT / "code/render"))
from phase8b_figures import FOREST_GROUP_ORDER, GROUP_LABELS, DIMENSION_LABELS

LABELS = {"admissoes": "Admissões", "desligamentos": "Desligamentos", "n_movimentacoes": "Fluxo bruto", "ln_salario_real_adm": "Salário real (log)", "asinh_saldo": "Saldo (asinh)"}
KEYS = ["dimension", "group_id", "outcome"]

def fmt(x, digits=4):
    return "—" if pd.isna(x) else f"{float(x):.{digits}f}".replace("-", "−").replace(".", ",")

def pv(x):
    return "—" if pd.isna(x) else "\\<0,001" if float(x) < .001 else fmt(x, 3)

def stars(p):
    return r"\*\*\*" if p < .01 else r"\*\*" if p < .05 else r"\*" if p < .1 else ""

def table(headers, rows):
    def row(cells):
        return "\t<tr>\n" + "".join(f"\t\t<td>{x}</td>\n" for x in cells) + "\t</tr>\n"
    return '<table header-row="true">\n' + row(headers) + "".join(row(r) for r in rows) + "</table>\n"

def save(name, text):
    (OUT / "tables" / f"{name}.md").write_text(text)

def main():
    inputs = [REF / "models/group_did_results.csv", REF / "diagnostics/ddd_multiplicity_results.csv", REF / "diagnostics/ddd_alternative_partitions.csv", REF / "diagnostics/ddd_pretrends.csv", REF / "diagnostics/ddd_alternative_partitions_pretrends.csv", REF / "backing_data/figure_5_2_6_group_outcome_forest.csv", REF / "tables/table_5_1_national_results.csv", REF / "tables/table_5_1_1_sector_control.csv"]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (OUT / "evidence/source_hashes.json").write_text(json.dumps(hashes, indent=2))
    a, b = [pd.read_csv(REF / "diagnostics" / f) for f in ["ddd_multiplicity_results.csv", "ddd_alternative_partitions.csv"]]
    c = pd.read_csv(REF / "models/group_did_results.csv")
    ddd = pd.concat([a,b], ignore_index=True)
    diagnostics = pd.concat([pd.read_csv(REF / "diagnostics" / f) for f in ["ddd_pretrends.csv", "ddd_alternative_partitions_pretrends.csv"]], ignore_index=True)
    ddd = ddd.merge(diagnostics[KEYS + ["ddd_pretrend_status", "group_pretrend_pretrend_status", "group_mde_80_power", "ddd_mde_80_power", "group_pretrend_n_obs", "ddd_n_obs"]], on=KEYS, validate="one_to_one")
    assert len(a)==100 and len(b)==30 and len(c)==130
    assert len(a[a.outcome.eq("ln_salario_real_adm")])==20
    counts = {"A": {"tests": len(a), "nominal": int(a.nominal_significant_005.sum()), "BH":int(a.bh_significant_005.sum())}, "B": {"tests":len(b),"nominal":int(b.nominal_significant_005.sum()),"BH":int(b.bh_significant_005.sum())}, "C":{"tests":len(c),"nominal":int(c.nominal_significant_005.sum()),"BH":int(c.bh_significant_005.sum())}, "A_wage_tests":20, "A_wage_BH":int(a.loc[a.outcome.eq("ln_salario_real_adm"),"bh_significant_005"].sum())}
    (OUT / "evidence/multiplicity_counts.json").write_text(json.dumps(counts,indent=2))
    national=pd.read_csv(inputs[-2]); sector=pd.read_csv(inputs[-1])
    save("national", table(["Resultado","Estimador","Coeficiente","EP","IC 95%","p nominal","Pré-tendência","N"],[[LABELS[r.outcome],r.estimator.upper(),fmt(r.coefficient)+stars(r.p_value),fmt(r.standard_error),f"[{fmt(r.ci_low)}; {fmt(r.ci_high)}]",pv(r.p_value),"falha",f"{r.n_obs:,}".replace(",",".")] for r in national.itertuples()]))
    save("sector",table(["Resultado","Nível 1 (EP)","p nominal","Nível 2 (EP)","p nominal","N2 − N1"],[[LABELS[r.outcome],f"{fmt(r.level_1_coefficient)}{stars(r.level_1_p_value)} ({fmt(r.level_1_standard_error)})",pv(r.level_1_p_value),f"{fmt(r.level_2_coefficient)}{stars(r.level_2_p_value)} ({fmt(r.level_2_standard_error)})",pv(r.level_2_p_value),fmt(r.coefficient_delta_level_2_minus_level_1)] for r in sector.itertuples()]))
    short_status={"fail":"falha","warning":"alerta","pass":"não rejeitada","not_interpretable_rank_deficient":"indefinido: posto"}
    blocks={"sex":["sex"],"race":["race_color","race_aggregate"],"age":["age_canaries","age_pnad"],"education":["education"],"income":["income"]}
    for block,dims in blocks.items():
        dd=ddd[ddd.dimension.isin(dims)]
        cc=c[c.dimension.isin(dims)]
        primary=dd[dd.outcome.isin(["admissoes","desligamentos","ln_salario_real_adm"])]
        if block=="age":primary=primary[primary.dimension.eq("age_canaries")]
        save("main_"+block,table(["Grupo (família)","Resultado","DDD (EP)","p BH","Pré-tendência DDD","Suporte"],[[GROUP_LABELS[r.group_id]+f" ({r.family_id})",LABELS[r.outcome],f"{fmt(r.coefficient)}{stars(r.bh_adjusted_p_value)} ({fmt(r.standard_error)})",pv(r.bh_adjusted_p_value),short_status.get(r.ddd_pretrend_status,r.ddd_pretrend_status),r.support_status] for r in primary.itertuples()]))
        save("ddd_"+block,table(["Grupo (família)","Resultado","DDD (EP)","p nominal / BH","Pré-tendência grupo / DDD","N estático DDD","N evento grupo / DDD","CBOs alvo T/C · suporte","MDE 80% grupo / DDD"],[[GROUP_LABELS[r.group_id]+f" ({r.family_id})",LABELS[r.outcome],f"{fmt(r.coefficient)}{stars(r.bh_adjusted_p_value)} ({fmt(r.standard_error)})",pv(r.nominal_p_value)+" / "+pv(r.bh_adjusted_p_value),short_status.get(r.group_pretrend_pretrend_status,r.group_pretrend_pretrend_status)+" / "+short_status.get(r.ddd_pretrend_status,r.ddd_pretrend_status),str(int(r.n_obs)),f"{int(r.group_pretrend_n_obs)} / {int(r.ddd_n_obs)}",f"{int(r.target_treated_cbo_with_flows)}/{int(r.target_control_cbo_with_flows)} · {r.support_status}",fmt(r.group_mde_80_power)+" / "+fmt(r.ddd_mde_80_power)] for r in dd.itertuples()]))
        save("did_"+block,table(["Grupo","Resultado","DiD (EP)","p nominal / BH","Pré-tendência grupo","N","CBOs T/C · suporte"],[[GROUP_LABELS[r.group_id],LABELS[r.outcome],f"{fmt(r.coefficient)}{stars(r.bh_adjusted_p_value)} ({fmt(r.standard_error)})",pv(r.nominal_p_value)+" / "+pv(r.bh_adjusted_p_value),short_status.get(r.group_pretrend_status,r.group_pretrend_status),str(int(r.n_obs)),f"{int(r.target_treated_cbo_with_flows)}/{int(r.target_control_cbo_with_flows)} · {r.support_status}"] for r in cc.itertuples()]))
        dd.to_csv(OUT/"tables"/f"ddd_{block}.csv",index=False)
        cc.to_csv(OUT/"tables"/f"did_{block}.csv",index=False)
    forest=pd.read_csv(inputs[5])
    merged=forest.merge(c,on=KEYS,suffixes=("_fig","_source"),validate="one_to_one")
    for col in ["coefficient","standard_error","bh_adjusted_p_value"]:
        assert np.allclose(merged[col+"_fig"],merged[col+"_source"],atol=1e-14,rtol=0)
    alpha=.05*int(c.bh_significant_005.sum())/len(c)
    critical=stats.t.ppf(1-alpha/2,merged.cluster_df)
    assert np.allclose(merged.adjusted_ci_low,merged.coefficient_source-critical*merged.standard_error_source,atol=1e-10,rtol=0)
    assert np.allclose(merged.adjusted_ci_high,merged.coefficient_source+critical*merged.standard_error_source,atol=1e-10,rtol=0)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.spines.top":False,"axes.spines.right":False,"axes.spines.left":False,"axes.titleweight":"bold","savefig.facecolor":"white"})
    for num,outcome in enumerate(["admissoes","desligamentos","ln_salario_real_adm"],1):
        part=forest[forest.outcome.eq(outcome)].set_index(["dimension","group_id"])
        fig,ax=plt.subplots(figsize=(8.3,11.7))
        fig.subplots_adjust(left=.39,right=.97,bottom=.22,top=.90)
        positions=[]; labels=[]; last=None; y=0
        for dimension,group in FOREST_GROUP_ORDER:
            if dimension!=last:
                if last is not None:y+=.65
                ax.text(-.015,y-.63,DIMENSION_LABELS[dimension],transform=ax.get_yaxis_transform(),ha="right",va="center",fontsize=9,fontweight="bold",color="#555555")
            row=part.loc[(dimension,group)]; color="#156082"; discovery=bool(row.bh_significant_005)
            marker={"adequate":"o","limited":"^","thin":"X"}[row.support_status]
            ax.errorbar(row.coefficient,y,xerr=[[row.coefficient-row.adjusted_ci_low],[row.adjusted_ci_high-row.coefficient]],fmt=marker,markersize=6,markerfacecolor=color if discovery else "white",markeredgecolor=color,ecolor=color if discovery else "#A0A0A0",elinewidth=1.5,capsize=2)
            positions.append(y);labels.append(GROUP_LABELS[group]);last=dimension;y+=1
        ax.set_yticks(positions,labels);ax.tick_params(axis="y",length=0,pad=9)
        ax.set_ylim(y-.1,-1.25);ax.axvline(0,color="#555555",lw=.9)
        ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{x:.2f}".replace(".",",")))
        ax.set_xlabel("Coeficiente DiD e intervalo no limiar BH",labelpad=12)
        fig.suptitle(f"Figura A.8.{num} — {"Salário real de admissão" if outcome.startswith("ln_") else LABELS[outcome]}",x=.06,ha="left",y=.97,fontsize=15.5,fontweight="bold")
        fig.text(.06,.94,"DiDs dentro dos grupos · "+("MQO em log" if outcome.startswith("ln_") else "PPML em nível"),fontsize=11)
        handles=[Line2D([0],[0],marker="o",color="none",markerfacecolor="#156082",markeredgecolor="#156082",label="p BH < 0,05"),Line2D([0],[0],marker="o",color="none",markerfacecolor="white",markeredgecolor="#156082",label="p BH ≥ 0,05"),Line2D([0],[0],marker="^",color="none",markerfacecolor="white",markeredgecolor="#156082",label="Suporte limitado"),Line2D([0],[0],marker="X",color="none",markerfacecolor="white",markeredgecolor="#156082",label="Suporte baixo")]
        fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,.09),ncol=2,frameon=False,fontsize=10)
        fig.text(.06,.074,"Família C: 130 testes; ajuste BH original preservado (40 rejeições a 5%).",fontsize=9)
        fig.text(.06,.055,"Intervalos cluster-t no limiar q × k / m = 0,0153846; não são ICs simultâneos de 95%.",fontsize=9)
        fig.text(.06,.036,"Pré-tendências e suporte limitam a interpretação. DiD no grupo não testa diferenças entre grupos.",fontsize=8.8)
        for ext,dpi in [("png",220),("pdf",300)]:fig.savefig(OUT/"figures"/f"figure_a_8_{num}_{outcome}.{ext}",dpi=dpi)
        plt.close(fig)
        part.reset_index().to_csv(OUT/"figures"/f"figure_a_8_{num}_{outcome}.csv",index=False)
    (OUT/"evidence/render_verification.json").write_text(json.dumps({"source_rows":130,"figure_rows":78,"figures":3,"coefficients_unchanged":True,"BH_unchanged":True,"intervals_preserved":True,"BH_cutoff":alpha,"regressions_run":0},indent=2))
    print(json.dumps(counts,indent=2))

if __name__=="__main__":main()
