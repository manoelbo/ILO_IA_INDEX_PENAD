"""
Etapa 3a - Preparação de Dados: Triple-DiD (Município × Conectividade)

Fluxo:
  01. Download dados Anatel (conectividade municipal)
  02. Download dados IBGE (população municipal)
  03. Agregar CAGED por município
  04. Índice de conectividade municipal
  05. Merge painel tridimensional (Ocupação × Município × Conectividade)

Saída: data/output/painel_triple_did_ready.parquet

Uso:
  python src/scripts/etapa_3a_preparacao_dados_did_municipio_conectividade.py
"""

"""
Configuração compartilhada — Etapa 3a
Preparação do painel CAGED × Município × Conectividade (Anatel).
"""

import time
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos (scripts/etapa_3a/config.py → notebook → repo)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_INPUT = REPO_ROOT / "data" / "input"
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
DATA_OUTPUT = REPO_ROOT / "data" / "output"

for d in [DATA_INPUT, DATA_RAW, DATA_PROCESSED, DATA_OUTPUT]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parâmetros do painel
# ---------------------------------------------------------------------------
GCP_PROJECT_ID = "mestrado-pnad-2026"

# Período: Jan/2021 — Jun/2025 (alinhado à Etapa 2)
ANO_INICIO = 2021
ANO_FIM = 2025
# Evento: ChatGPT Nov/2022; pós a partir de Dez/2022
ANO_TRATAMENTO = 2022
MES_TRATAMENTO = 12

# Pré-tratamento para conectividade: Jan–Out/2022 (evitar endogeneidade)
ANO_PRE_CONECT = 2022
MES_FIM_PRE_CONECT = 10

# Filtros municipais (plano Etapa 3)
MIN_POPULACAO = 50_000
MIN_MOVIMENTACOES_PRE = 5  # células (cbo_4d × município) com ≥ N movimentações no pré

# ---------------------------------------------------------------------------
# Arquivos reutilizados da Etapa 2
# ---------------------------------------------------------------------------
PAINEL_ETAPA2_PARQUET = DATA_OUTPUT / "painel_caged_did_ready.parquet"
IPCA_MENSAL_FILE = DATA_PROCESSED / "ipca_mensal.parquet"

# ---------------------------------------------------------------------------
# Arquivos intermediários e de saída Etapa 3a
# ---------------------------------------------------------------------------
ANATEL_PRE_FILE = DATA_PROCESSED / "anatel_pre_tratamento.parquet"
IBGE_MUNICIPIOS_FILE = DATA_PROCESSED / "ibge_municipios.parquet"
CONECTIVIDADE_FILE = DATA_PROCESSED / "conectividade_municipal.parquet"
PAINEL_CAGED_MUN_FILE = DATA_PROCESSED / "painel_caged_municipio.parquet"
PAINEL_FINAL_PARQUET = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
CONECTIVIDADE_CSV = REPO_ROOT / "outputs" / "tables" / "conectividade_municipal.csv"
EXPECTED_CROSSWALK_SPEC = "mte_official_no_numeric_fallback"

# Outputs/tables (para CSV de conectividade)
OUTPUTS_TABLES = REPO_ROOT / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)


def print_config():
    """Imprime a configuração atual."""
    print("=" * 60)
    print("CONFIGURAÇÃO — Etapa 3a")
    print("=" * 60)
    print(f"  Notebook dir: {REPO_ROOT}")
    print(f"  Período:      {ANO_INICIO}–{ANO_FIM}")
    print(f"  Evento:       Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
    print(f"  Pré conect.:  até {MES_FIM_PRE_CONECT}/{ANO_PRE_CONECT}")
    print(f"  MIN_POPULACAO: {MIN_POPULACAO:,}")
    print(f"  MIN_MOVIMENTACOES_PRE: {MIN_MOVIMENTACOES_PRE}")
    print(f"  Painel final: {PAINEL_FINAL_PARQUET.name}")
    print("=" * 60)


# if __name__ == "__main__":
#     print_config()



# # ============================================================
# # 01_anatel.py
# # ============================================================

# """
# Script 01: Download Anatel — Banda Larga Fixa (pré-tratamento)
# Fonte: Base dos Dados br_anatel_banda_larga_fixa
# Período pré-tratamento: 2021 + Jan–Out/2022 (evitar endogeneidade)
# Saída: data/processed/anatel_pre_tratamento.parquet
# """

# import time
# from pathlib import Path

# import numpy as np

# from config import (
#     GCP_PROJECT_ID,
#     ANO_PRE_CONECT,
#     MES_FIM_PRE_CONECT,
#     ANATEL_PRE_FILE,
# )


def log(msg):
    print(msg, flush=True)


def download_anatel():
    """Query BigQuery Anatel e salva agregado por município (média pré-tratamento)."""
    # Nome da tabela no Base dos Dados pode variar; usar microdados
    # Se falhar, verificar: bd.list_tables(dataset_id='br_anatel_banda_larga_fixa')
    query = f"""
    SELECT
        ano,
        mes,
        id_municipio,
        SUM(acessos) AS total_acessos,
        SUM(CASE WHEN LOWER(SAFE_CAST(tecnologia AS STRING)) LIKE '%fibra%' THEN acessos ELSE 0 END) AS acessos_fibra
    FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
    WHERE ano IN (2021, {ANO_PRE_CONECT})
      AND (ano < {ANO_PRE_CONECT} OR mes <= {MES_FIM_PRE_CONECT})
    GROUP BY ano, mes, id_municipio
    """
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT_ID)
        log("  Executando query Anatel (BigQuery)...")
        t0 = time.time()
        df = client.query(query).to_dataframe(create_bqstorage_client=True)
        log(f"  Linhas: {len(df):,} em {time.time()-t0:.0f}s")
    except Exception as e:
        log(f"  BigQuery falhou: {e}")
        try:
            import basedosdados as bd
            df = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID)
        except Exception as e2:
            raise RuntimeError(f"Anatel: BigQuery e basedosdados falharam. {e2}") from e2

    # Agregar por município: média mensal de acessos no pré; % fibra = soma(fibra)/soma(total)
    out = df.groupby("id_municipio").agg(
        media_acessos_pre=("total_acessos", "mean"),
        soma_acessos=("total_acessos", "sum"),
        soma_fibra=("acessos_fibra", "sum"),
    ).reset_index()
    out["pct_fibra_pre"] = out["soma_fibra"] / out["soma_acessos"].clip(lower=1)
    out = out[["id_municipio", "media_acessos_pre", "pct_fibra_pre"]]
    out.to_parquet(ANATEL_PRE_FILE, index=False)
    log(f"  Salvo: {ANATEL_PRE_FILE.name} — {len(out):,} municípios")
    return out


# if __name__ == "__main__":
#     download_anatel()

# # ============================================================
# # 02_ibge.py
# # ============================================================

# """
# Script 02: Download IBGE — Domicílios, PIB, População por município
# Fonte: Base dos Dados (Censo 2022, PIB, População)
# Saída: data/processed/ibge_municipios.parquet
# """

# import time
# from pathlib import Path

# import pandas as pd

# from config import GCP_PROJECT_ID, IBGE_MUNICIPIOS_FILE, MIN_POPULACAO


def log(msg):
    print(msg, flush=True)


def download_ibge():
    """Busca população (2022), PIB (2021) e domicílios (Censo 2022) por município."""
    # População: br_ibge_populacao.municipio (ano, id_municipio, populacao)
    query_pop = """
    SELECT id_municipio, populacao
    FROM `basedosdados.br_ibge_populacao.municipio`
    WHERE ano = 2022
    """
    # PIB: br_ibge_pib.municipio (não tem coluna populacao; usamos df_pop para PIB per capita)
    query_pib = """
    SELECT id_municipio, pib
    FROM `basedosdados.br_ibge_pib.municipio`
    WHERE ano = 2021
    """
    use_bq = True
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT_ID)
        log("  Query população (2022)...")
        df_pop = client.query(query_pop).to_dataframe(create_bqstorage_client=True)
        log("  Query PIB (2021)...")
        df_pib = client.query(query_pib).to_dataframe(create_bqstorage_client=True)
    except Exception as e:
        log(f"  BigQuery falhou: {e}")
        use_bq = False
        try:
            import basedosdados as bd
            df_pop = bd.read_sql(query_pop, billing_project_id=GCP_PROJECT_ID)
            df_pib = bd.read_sql(query_pib, billing_project_id=GCP_PROJECT_ID)
        except Exception as e2:
            raise RuntimeError(f"IBGE: {e2}") from e2

    # Merge população + PIB
    df = df_pop.merge(
        df_pib[["id_municipio", "pib"]],
        on="id_municipio",
        how="outer",
    )
    df["pib_per_capita"] = df["pib"] / df["populacao"].clip(lower=1)
    # Domicílios: tentar Censo 2022; se não existir, usar população/3 como proxy
    if use_bq:
        try:
            query_dom = """
            SELECT id_municipio, SUM(domicilios_particulares_ocupados) AS domicilios
            FROM `basedosdados.br_ibge_censo_2022.setor_censitario`
            GROUP BY id_municipio
            """
            df_dom = client.query(query_dom).to_dataframe(create_bqstorage_client=True)
            df = df.merge(df_dom, on="id_municipio", how="left")
        except Exception:
            pass
    if "domicilios" not in df.columns or df["domicilios"].isna().all():
        df["domicilios"] = (df["populacao"] / 3).round().clip(lower=1)
        log("  AVISO: domicílios não encontrados; usando proxy populacao/3")

    df = df.rename(columns={"populacao": "populacao_2022"})
    df = df[["id_municipio", "populacao_2022", "domicilios", "pib", "pib_per_capita"]].copy()
    df.columns = ["id_municipio", "populacao", "domicilios", "pib", "pib_per_capita"]
    df.to_parquet(IBGE_MUNICIPIOS_FILE, index=False)
    log(f"  Salvo: {IBGE_MUNICIPIOS_FILE.name} — {len(df):,} municípios")
    return df


# if __name__ == "__main__":
#     download_ibge()

# # ============================================================
# # 03_aggregate_caged_mun.py
# # ============================================================

# """
# Script 03: Agregar CAGED por ocupação × município × período
# Entrada: data/raw/caged_{ano}.parquet
# Saída:   data/processed/painel_caged_municipio.parquet

# Agregação (cbo_4d, id_municipio, ano, mes) — mesmas métricas da Etapa 2a.
# Sexo: 1=Masculino, 3=Feminino (CAGED/Base dos Dados).
# """

# import time
# import argparse
# from pathlib import Path

# import pandas as pd
# import numpy as np

# from config import (
#     DATA_RAW,
#     DATA_PROCESSED,
#     ANO_INICIO,
#     ANO_FIM,
#     ANO_TRATAMENTO,
#     MES_TRATAMENTO,
#     PAINEL_CAGED_MUN_FILE,
# )

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


def aggregate_main(anos=None):
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


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Agregar CAGED por cbo_4d x id_municipio x periodo")
#     parser.add_argument("--ano", type=int, default=None, help="Processar só um ano (ex.: 2022)")
#     args = parser.parse_args()
#     anos = [args.ano] if args.ano else None
#     main(anos=anos)

# # ============================================================
# # 03_conectividade.py
# # ============================================================

# """
# Script 03: Construir índice de conectividade municipal
# Entrada: anatel_pre_tratamento.parquet, ibge_municipios.parquet
# Saída:   data/processed/conectividade_municipal.parquet

# penetracao_bl = media_acessos_pre / domicilios
# alta_conectividade = 1 se penetracao_bl > mediana
# """

# from pathlib import Path

# import pandas as pd
# import numpy as np

# from config import (
#     ANATEL_PRE_FILE,
#     IBGE_MUNICIPIOS_FILE,
#     CONECTIVIDADE_FILE,
#     MIN_POPULACAO,
# )


def log(msg):
    print(msg, flush=True)


def build_conectividade():
    """Merge Anatel + IBGE, calcula penetração e dummies de conectividade."""
    if not ANATEL_PRE_FILE.exists():
        raise FileNotFoundError(f"Rodar 01_anatel.py antes. Falta: {ANATEL_PRE_FILE}")
    if not IBGE_MUNICIPIOS_FILE.exists():
        raise FileNotFoundError(f"Rodar 02_ibge.py antes. Falta: {IBGE_MUNICIPIOS_FILE}")

    df_anatel = pd.read_parquet(ANATEL_PRE_FILE)
    df_ibge = pd.read_parquet(IBGE_MUNICIPIOS_FILE)

    df_ibge["id_municipio"] = df_ibge["id_municipio"].astype(str).str.zfill(7)
    df_anatel["id_municipio"] = df_anatel["id_municipio"].astype(str).str.zfill(7)

    df = df_anatel.merge(df_ibge, on="id_municipio", how="inner")
    df["penetracao_bl"] = df["media_acessos_pre"] / df["domicilios"].clip(lower=1)

    mediana = df["penetracao_bl"].median()
    q25 = df["penetracao_bl"].quantile(0.25)
    q75 = df["penetracao_bl"].quantile(0.75)
    df["alta_conectividade"] = (df["penetracao_bl"] > mediana).astype(int)
    df["conectividade_q75"] = (df["penetracao_bl"] > q75).astype(int)
    df["conectividade_q25"] = (df["penetracao_bl"] > q25).astype(int)

    # Apenas municípios com população >= MIN_POPULACAO (para alinhar com filtro do painel)
    df = df[df["populacao"] >= MIN_POPULACAO].copy()
    df.to_parquet(CONECTIVIDADE_FILE, index=False)
    log(f"  Mediana penetração: {mediana:.4f}")
    log(f"  Alta conectividade: {df['alta_conectividade'].sum():,} municípios")
    log(f"  Salvo: {CONECTIVIDADE_FILE.name} — {len(df):,} municípios")
    return df


# if __name__ == "__main__":
#     build_conectividade()

# # ============================================================
# # 04_merge_panel.py
# # ============================================================

# """
# Script 04: Merge painel CAGED municipal + exposição (Etapa 2) + conectividade
# Entrada: painel_caged_municipio.parquet, painel_caged_did_ready.parquet (exposure),
#          conectividade_municipal.parquet, ipca_mensal.parquet
# Saída:   data/output/painel_caged_municipio_anatel.parquet
# """

# from pathlib import Path

# import pandas as pd
# import numpy as np

# from config import (
#     DATA_PROCESSED,
#     DATA_OUTPUT,
#     PAINEL_CAGED_MUN_FILE,
#     PAINEL_ETAPA2_PARQUET,
#     IPCA_MENSAL_FILE,
#     CONECTIVIDADE_FILE,
#     PAINEL_FINAL_PARQUET,
#     ANO_TRATAMENTO,
#     MES_TRATAMENTO,
#     MIN_MOVIMENTACOES_PRE,
#     CONECTIVIDADE_CSV,
#     OUTPUTS_TABLES,
# )
# from config import ANO_INICIO, ANO_FIM

INDICE_BASE = 100.0
INDICE_BASE_ANO, INDICE_BASE_MES = 2024, 12


def log(msg):
    print(msg, flush=True)


def step_04():
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
    if "crosswalk_spec" not in painel2.columns:
        raise ValueError("Painel Etapa 2 não tem crosswalk_spec. Regerar Etapa 2a.")
    specs = set(painel2["crosswalk_spec"].dropna().unique())
    if specs != {EXPECTED_CROSSWALK_SPEC}:
        raise ValueError(
            f"Painel Etapa 2 usa crosswalk inesperado: {sorted(specs)}. "
            f"Esperado: {EXPECTED_CROSSWALK_SPEC}"
        )
    cols_exp = [
        "cbo_4d", "exposure_score_2d", "exposure_score_4d", "alta_exp", "alta_exp_4d",
        "alta_exp_10", "alta_exp_25", "alta_exp_mediana", "quintil_exp",
        "grande_grupo_cbo", "grande_grupo_nome",
        "crosswalk_spec", "mte_match_status", "mte_ciuo88_codes",
        "mte_target_isco08_codes", "mte_target_isco08_2d_codes",
        "exposure_score_2d_old", "exposure_score_4d_old",
        "anthropic_automation_index", "is_automation", "is_augmentation",
    ]
    cols_exp = [c for c in cols_exp if c in painel2.columns]
    df_exposure = painel2[cols_exp].drop_duplicates("cbo_4d")

    log("  Carregando conectividade...")
    df_conect = pd.read_parquet(CONECTIVIDADE_FILE)
    df_conect["id_municipio"] = df_conect["id_municipio"].astype(str).str.zfill(7)

    df = df_caged.merge(df_exposure, on="cbo_4d", how="left")
    missing_exp = df["exposure_score_2d"].isna()
    if missing_exp.any():
        missing_rows = int(missing_exp.sum())
        missing_cbo = int(df.loc[missing_exp, "cbo_4d"].nunique())
        missing_adm = float(df.loc[missing_exp, "admissoes"].sum()) if "admissoes" in df.columns else np.nan
        total_adm = float(df["admissoes"].sum()) if "admissoes" in df.columns else np.nan
        adm_msg = (
            f", admissões={missing_adm:,.0f} ({missing_adm / total_adm:.2%})"
            if total_adm and not np.isnan(total_adm)
            else ""
        )
        log(
            f"  Exposição MTE sem match no painel municipal: "
            f"{missing_rows:,} linhas, {missing_cbo:,} CBOs{adm_msg}"
        )
    n_before_exp_filter = len(df)
    df = df[~missing_exp].copy()
    log(f"  Filtro exposição MTE válida: {n_before_exp_filter:,} -> {len(df):,} linhas")
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


# if __name__ == "__main__":
#     main()


# # =============================================================================
# # MAIN
# # =============================================================================

def main():
    """Executa o pipeline completo da Etapa 3a."""
    print("=" * 60)
    print("ETAPA 3a — Triple-DiD: Preparação de Dados (Município × Conectividade)")
    print("=" * 60)

    print("\n[1/5] Download Anatel (conectividade)...")
    if ANATEL_PRE_FILE.exists():
        print(f"  Cache encontrado: {ANATEL_PRE_FILE}")
    else:
        download_anatel()

    print("\n[2/5] Download IBGE (municípios)...")
    if IBGE_MUNICIPIOS_FILE.exists():
        print(f"  Cache encontrado: {IBGE_MUNICIPIOS_FILE}")
    else:
        download_ibge()

    print("\n[3/5] Agregar CAGED por município...")
    if PAINEL_CAGED_MUN_FILE.exists():
        print(f"  Cache encontrado: {PAINEL_CAGED_MUN_FILE}")
    else:
        aggregate_main()

    print("\n[4/5] Índice de conectividade...")
    if CONECTIVIDADE_FILE.exists():
        print(f"  Cache encontrado: {CONECTIVIDADE_FILE}")
    else:
        build_conectividade()

    print("\n[5/5] Merge painel tridimensional...")
    step_04()

    print("\n" + "=" * 60)
    print("ETAPA 3a CONCLUÍDA.")
    print("=" * 60)


if __name__ == "__main__":
    main()
