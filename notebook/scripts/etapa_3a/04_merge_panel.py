"""
Script 04: Merge painel CAGED municipal + exposição (Etapa 2) + conectividade
Entrada: painel_caged_municipio.parquet, painel_caged_did_ready.parquet (exposure),
         conectividade_municipal.parquet, ipca_mensal.parquet
Saída:   data/output/painel_caged_municipio_anatel.parquet
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    DATA_PROCESSED,
    DATA_OUTPUT,
    PAINEL_CAGED_MUN_FILE,
    PAINEL_ETAPA2_PARQUET,
    IPCA_MENSAL_FILE,
    CONECTIVIDADE_FILE,
    PAINEL_FINAL_PARQUET,
    ANO_TRATAMENTO,
    MES_TRATAMENTO,
    MIN_MOVIMENTACOES_PRE,
    CONECTIVIDADE_CSV,
    OUTPUTS_TABLES,
)
from config import ANO_INICIO, ANO_FIM

INDICE_BASE = 100.0
INDICE_BASE_ANO, INDICE_BASE_MES = 2024, 12


def log(msg):
    print(msg, flush=True)


def main():
    if not PAINEL_CAGED_MUN_FILE.exists():
        raise FileNotFoundError(f"Rodar 03_aggregate_caged_mun.py antes. Falta: {PAINEL_CAGED_MUN_FILE}")
    if not PAINEL_ETAPA2_PARQUET.exists():
        raise FileNotFoundError(f"Painel Etapa 2 não encontrado: {PAINEL_ETAPA2_PARQUET}")
    if not CONECTIVIDADE_FILE.exists():
        raise FileNotFoundError(f"Rodar 03_conectividade.py antes. Falta: {CONECTIVIDADE_FILE}")

    log("  Carregando painel CAGED municipal...")
    df_caged = pd.read_parquet(PAINEL_CAGED_MUN_FILE)
    df_caged["id_municipio"] = df_caged["id_municipio"].astype(str).str.zfill(7)

    log("  Carregando exposição (Etapa 2)...")
    painel2 = pd.read_parquet(PAINEL_ETAPA2_PARQUET)
    cols_exp = [
        "cbo_4d", "exposure_score_2d", "exposure_score_4d", "alta_exp", "alta_exp_4d",
        "alta_exp_10", "alta_exp_25", "alta_exp_mediana", "quintil_exp",
        "grande_grupo_cbo", "grande_grupo_nome",
        "anthropic_automation_index", "is_automation", "is_augmentation",
    ]
    cols_exp = [c for c in cols_exp if c in painel2.columns]
    df_exposure = painel2[cols_exp].drop_duplicates("cbo_4d")

    log("  Carregando conectividade...")
    df_conect = pd.read_parquet(CONECTIVIDADE_FILE)
    df_conect["id_municipio"] = df_conect["id_municipio"].astype(str).str.zfill(7)

    df = df_caged.merge(df_exposure, on="cbo_4d", how="inner")
    df = df.merge(
        df_conect[["id_municipio", "penetracao_bl", "pct_fibra_pre", "alta_conectividade",
                   "conectividade_q75", "conectividade_q25", "pib_per_capita", "populacao"]],
        on="id_municipio",
        how="inner",
    )

    # Variáveis temporais (como Etapa 2a)
    df["periodo_dt"] = pd.to_datetime(df["periodo"] + "-01", errors="coerce")
    df["post"] = (df["periodo_dt"] >= f"{ANO_TRATAMENTO}-{MES_TRATAMENTO:02d}-01").astype(int)
    df["tempo_relativo_meses"] = (
        (df["periodo_dt"].dt.year - ANO_TRATAMENTO) * 12
        + (df["periodo_dt"].dt.month - MES_TRATAMENTO)
    )
    df["uf_periodo"] = df["sigla_uf"].astype(str) + "_" + df["periodo"].astype(str)

    # Interações DDD
    df["post_alta_exp"] = df["post"] * df["alta_exp"]
    df["post_alta_conect"] = df["post"] * df["alta_conectividade"]
    df["alta_exp_alta_conect"] = df["alta_exp"] * df["alta_conectividade"]
    df["triple_did"] = df["post"] * df["alta_exp"] * df["alta_conectividade"]

    # Salário real (IPCA)
    if IPCA_MENSAL_FILE.exists():
        df_ipca = pd.read_parquet(IPCA_MENSAL_FILE)
        df = df.merge(df_ipca[["ano", "mes", "indice"]], on=["ano", "mes"], how="left")
        df["salario_real_adm"] = df["salario_medio_adm"] * (INDICE_BASE / df["indice"].clip(lower=0.01))
        df["ln_salario_real_adm"] = np.log(df["salario_real_adm"].clip(lower=1))
    else:
        df["salario_real_adm"] = df["salario_medio_adm"]
        df["ln_salario_real_adm"] = np.log(df["salario_medio_adm"].clip(lower=1))

    df["ln_pib_pc"] = np.log(df["pib_per_capita"].clip(lower=1))

    # Opcional: filtrar células com poucas movimentações no pré
    if MIN_MOVIMENTACOES_PRE > 0:
        pre = df["post"] == 0
        mov_pre = df.loc[pre].groupby(["cbo_4d", "id_municipio"])["n_movimentacoes"].sum().reset_index()
        mov_pre.columns = ["cbo_4d", "id_municipio", "mov_pre"]
        df = df.merge(mov_pre, on=["cbo_4d", "id_municipio"], how="left")
        n_antes = len(df)
        df = df[df["mov_pre"] >= MIN_MOVIMENTACOES_PRE].drop(columns=["mov_pre"])
        log(f"  Filtro pré movimentações >= {MIN_MOVIMENTACOES_PRE}: {n_antes:,} -> {len(df):,} linhas")

    PAINEL_FINAL_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PAINEL_FINAL_PARQUET, index=False)
    size_mb = PAINEL_FINAL_PARQUET.stat().st_size / 1e6
    log(f"  Salvo: {PAINEL_FINAL_PARQUET.name} ({size_mb:.1f} MB)")
    log(f"  Linhas: {len(df):,} | Ocupações: {df['cbo_4d'].nunique()} | "
        f"Municípios: {df['id_municipio'].nunique()} | Períodos: {df['periodo'].nunique()}")

    OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
    df_conect.to_csv(CONECTIVIDADE_CSV, index=False)
    log(f"  Conectividade CSV: {CONECTIVIDADE_CSV.name}")
    return df


if __name__ == "__main__":
    main()
