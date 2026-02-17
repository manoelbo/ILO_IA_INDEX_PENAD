"""
Script 03: Agregar CAGED por ocupação × município × período
Entrada: data/raw/caged_{ano}.parquet
Saída:   data/processed/painel_caged_municipio.parquet

Agregação (cbo_4d, id_municipio, ano, mes) — mesmas métricas da Etapa 2a.
Sexo: 1=Masculino, 3=Feminino (CAGED/Base dos Dados).
"""

import sys
import time
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    DATA_RAW,
    DATA_PROCESSED,
    ANO_INICIO,
    ANO_FIM,
    ANO_TRATAMENTO,
    MES_TRATAMENTO,
    PAINEL_CAGED_MUN_FILE,
)

# Constantes alinhadas ao notebook 2a
CODIGO_SEXO_MULHER = 3
CODIGOS_RACA_BRANCA, CODIGOS_RACA_NEGRA = [1], [2, 4]
IDADE_CORTE_JOVEM = 29
CODIGOS_ESCOLARIDADE_SUPERIOR = ["9", "10", "11", "12", "13"]
CNAE_SECOES_TECNOLOGICO = ["J"]
SETOR_TECNOLOGICO_LIMIAR = 0.5


def log(msg):
    print(msg, flush=True)


def processar_ano(ano: int) -> pd.DataFrame:
    """Agrega um ano de CAGED por (cbo_4d, id_municipio, ano, mes)."""
    t0 = time.time()
    df = pd.read_parquet(DATA_RAW / f"caged_{ano}.parquet")
    log(f"  [{ano}] Carregado: {len(df):,} registros ({time.time()-t0:.0f}s)")

    df["cbo_2002"] = df["cbo_2002"].astype(str).str.strip()
    df["cbo_4d"] = df["cbo_2002"].str[:4]
    df = df[df["cbo_4d"].str.len() == 4]
    df = df[df["cbo_4d"].str.isdigit()]
    df = df[~df["cbo_4d"].isin(["0000", "nan", ""])]

    df["is_mulher"] = (df["sexo"].astype(str) == str(CODIGO_SEXO_MULHER)).astype(float)
    raca_str = df["raca_cor"].astype(str)
    df["is_branco"] = raca_str.isin([str(c) for c in CODIGOS_RACA_BRANCA]).astype(float)
    df["is_negro"] = raca_str.isin([str(c) for c in CODIGOS_RACA_NEGRA]).astype(float)
    df["is_jovem"] = (df["idade"] <= IDADE_CORTE_JOVEM).astype(float)
    df["is_superior"] = (
        df["grau_instrucao"].astype(str).isin(CODIGOS_ESCOLARIDADE_SUPERIOR).astype(float)
    )
    df["is_setor_tech"] = (
        df["cnae_2_secao"].astype(str).str.strip().isin(CNAE_SECOES_TECNOLOGICO).astype(float)
    )

    df_adm = df[df["saldo_movimentacao"] == 1].copy()
    df_desl = df[df["saldo_movimentacao"] == -1]
    log(f"  [{ano}] Admissões: {len(df_adm):,} | Desligamentos: {len(df_desl):,}")

    df_adm["sal_mulher"] = np.where(df_adm["is_mulher"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_homem"] = np.where(df_adm["is_mulher"] == 0, df_adm["salario_mensal"], np.nan)
    df_adm["sal_branco"] = np.where(df_adm["is_branco"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_negro"] = np.where(df_adm["is_negro"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_jovem"] = np.where(df_adm["is_jovem"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_naojovem"] = np.where(df_adm["is_jovem"] == 0, df_adm["salario_mensal"], np.nan)
    df_adm["sal_sup"] = np.where(df_adm["is_superior"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_med"] = np.where(df_adm["is_superior"] == 0, df_adm["salario_mensal"], np.nan)
    df_adm["is_homem"] = 1 - df_adm["is_mulher"]

    grp = ["cbo_4d", "id_municipio", "ano", "mes"]
    painel_adm = df_adm.groupby(grp).agg(
        sigla_uf=("sigla_uf", "first"),
        admissoes=("saldo_movimentacao", "count"),
        salario_medio_adm=("salario_mensal", "mean"),
        idade_media_adm=("idade", "mean"),
        pct_mulher_adm=("is_mulher", "mean"),
        pct_superior_adm=("is_superior", "mean"),
        pct_branco_adm=("is_branco", "mean"),
        pct_negro_adm=("is_negro", "mean"),
        pct_jovem_adm=("is_jovem", "mean"),
        pct_tecnologico_adm=("is_setor_tech", "mean"),
        salario_medio_mulher=("sal_mulher", "mean"),
        salario_medio_homem=("sal_homem", "mean"),
        salario_medio_branco=("sal_branco", "mean"),
        salario_medio_negro=("sal_negro", "mean"),
        salario_medio_jovem=("sal_jovem", "mean"),
        salario_medio_naojovem=("sal_naojovem", "mean"),
        salario_medio_superior=("sal_sup", "mean"),
        salario_medio_medio=("sal_med", "mean"),
        admissoes_mulher=("is_mulher", "sum"),
        admissoes_homem=("is_homem", "sum"),
        admissoes_jovem=("is_jovem", "sum"),
        admissoes_negro=("is_negro", "sum"),
    ).reset_index()

    mediana = (
        df_adm.groupby(grp)["salario_mensal"]
        .median()
        .reset_index()
        .rename(columns={"salario_mensal": "salario_mediano_adm"})
    )
    painel_adm = painel_adm.merge(mediana, on=grp, how="left")

    painel_desl = df_desl.groupby(grp).agg(
        desligamentos=("saldo_movimentacao", "count"),
        salario_medio_desl=("salario_mensal", "mean"),
    ).reset_index()

    p = painel_adm.merge(painel_desl, on=grp, how="outer").fillna(0)
    p["saldo"] = p["admissoes"] - p["desligamentos"]
    p["n_movimentacoes"] = p["admissoes"] + p["desligamentos"]
    p["setor_tecnologico"] = (p["pct_tecnologico_adm"] >= SETOR_TECNOLOGICO_LIMIAR).astype(int)
    p["periodo"] = (
        p["ano"].astype(int).astype(str)
        + "-"
        + p["mes"].astype(int).astype(str).str.zfill(2)
    )
    p["periodo_num"] = p["ano"].astype(int) * 100 + p["mes"].astype(int)
    p["post"] = (
        (p["periodo_num"] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)
    )
    p["ln_admissoes"] = np.log(p["admissoes"] + 1)
    p["ln_desligamentos"] = np.log(p["desligamentos"] + 1)
    p["ln_salario_adm"] = np.log(p["salario_medio_adm"].clip(lower=1))
    p["cbo_2d"] = p["cbo_4d"].str[:2]
    for grp_name in ["mulher", "homem", "branco", "negro", "jovem", "naojovem", "superior", "medio"]:
        col = f"salario_medio_{grp_name}"
        if col in p.columns:
            p[f"ln_salario_{grp_name}"] = np.log(p[col].clip(lower=1))
    for grp_name in ["mulher", "homem", "jovem", "negro"]:
        col = f"admissoes_{grp_name}"
        if col in p.columns:
            p[f"ln_admissoes_{grp_name}"] = np.log(p[col].astype(float) + 1)

    log(f"  [{ano}] Painel: {len(p):,} linhas ({time.time()-t0:.0f}s)")
    del df, df_adm, df_desl
    return p


def main(anos=None):
    """Agrega CAGED por (cbo_4d, id_municipio, ano, mes). anos=None usa ANO_INICIO..ANO_FIM."""
    if anos is None:
        anos = list(range(ANO_INICIO, ANO_FIM + 1))
    log("=" * 60)
    log("ETAPA 3a — Agregação CAGED por ocupação × município × período")
    log("=" * 60)
    t0 = time.time()
    paineis = []
    for ano in anos:
        paineis.append(processar_ano(ano))
    painel = pd.concat(paineis, ignore_index=True)
    painel.to_parquet(PAINEL_CAGED_MUN_FILE, index=False)
    size_mb = PAINEL_CAGED_MUN_FILE.stat().st_size / 1e6
    log(f"\nTotal: {len(painel):,} linhas | {painel['cbo_4d'].nunique()} ocupações | "
        f"{painel['id_municipio'].nunique()} municípios | {painel['periodo'].nunique()} períodos")
    log(f"Salvo: {PAINEL_CAGED_MUN_FILE.name} ({size_mb:.1f} MB) em {time.time()-t0:.0f}s")
    return painel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agregar CAGED por cbo_4d x id_municipio x periodo")
    parser.add_argument("--ano", type=int, default=None, help="Processar só um ano (ex.: 2022)")
    args = parser.parse_args()
    anos = [args.ano] if args.ano else None
    main(anos=anos)
