"""
Etapa 2a - Preparação de Dados: CAGED + ILO (DiD)

Equivalente Python do notebook etapa_2a_preparacao_dados_did_caged_ilo.ipynb.

Fluxo:
  01. Download CAGED (BigQuery → data/raw/caged_{ano}.parquet)
  02. Verificação dos microdados CAGED
  03. Agregar painel mensal (CBO 4d × mês)
  04. Verificação do painel
  05. Crosswalk CBO 2002 → ISCO-08 + merge ILO exposure
  06. Verificação do crosswalk
  07. Definir variáveis de tratamento (DiD)
  08. Verificação do tratamento
  09. Enriquecer e salvar dataset analítico final

Saída final: data/output/painel_caged_did_ready.parquet

Uso:
  python src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py
"""

"""
Configuração compartilhada — Etapa 2a
Caminhos, parâmetros e constantes usadas por todos os scripts.
"""

import time
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

from caged_mte_crosswalk import CROSSWALK_SPEC, apply_mte_crosswalk

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos (relativos à raiz do repositório)
# ---------------------------------------------------------------------------
# Raiz do repositório (3 níveis acima: scripts/etapa_2a/config.py → notebook → repo)
REPO_ROOT      = Path(__file__).resolve().parent.parent.parent
DATA_INPUT     = REPO_ROOT / "data" / "input"
DATA_RAW       = REPO_ROOT / "data" / "raw"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
DATA_OUTPUT    = REPO_ROOT / "data" / "output"

for d in [DATA_INPUT, DATA_RAW, DATA_PROCESSED, DATA_OUTPUT]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parâmetros do Painel CAGED
# ---------------------------------------------------------------------------
GCP_PROJECT_ID = "mestrado-pnad-2026"

# Período do painel: Jan/2021 — Dez/2025 (60 meses)
# Exclui 2020 para evitar efeitos COVID-19
ANO_INICIO     = 2021
ANO_FIM        = 2025

# Evento: lançamento do ChatGPT (30 de novembro de 2022)
# Pós-tratamento: a partir de dezembro/2022 (mês imediatamente após)
ANO_TRATAMENTO = 2022
MES_TRATAMENTO = 12   # Dezembro/2022 como primeiro mês "pós"

# Salário mínimo por ano (para normalização)
SALARIO_MINIMO = {
    2021: 1100,
    2022: 1212,
    2023: 1320,
    2024: 1412,
    2025: 1518,
}

# ---------------------------------------------------------------------------
# Raw CAGED categorical codes
# ---------------------------------------------------------------------------
CODIGO_SEXO_HOMEM = "1"
CODIGO_SEXO_MULHER = "3"
CODIGOS_SEXO_VALIDOS = {CODIGO_SEXO_HOMEM, CODIGO_SEXO_MULHER, "9"}

CODIGO_RACA_COR_BRANCA = "1"
CODIGO_RACA_COR_PRETA = "2"
CODIGO_RACA_COR_PARDA = "3"
CODIGO_RACA_COR_AMARELA = "4"
CODIGO_RACA_COR_INDIGENA = "5"
CODIGO_RACA_COR_NAO_INFORMADA = "6"
CODIGO_RACA_COR_NAO_IDENTIFICADA = "9"
CODIGOS_RACA_COR_VALIDOS = {
    CODIGO_RACA_COR_BRANCA,
    CODIGO_RACA_COR_PRETA,
    CODIGO_RACA_COR_PARDA,
    CODIGO_RACA_COR_AMARELA,
    CODIGO_RACA_COR_INDIGENA,
    CODIGO_RACA_COR_NAO_INFORMADA,
    CODIGO_RACA_COR_NAO_IDENTIFICADA,
}
CODIGOS_RACA_COR_NEGRA = {CODIGO_RACA_COR_PRETA, CODIGO_RACA_COR_PARDA}
CODIGOS_RACA_COR_NAO_INFORMADA_AGREGADA = {
    CODIGO_RACA_COR_NAO_INFORMADA,
    CODIGO_RACA_COR_NAO_IDENTIFICADA,
}
RACE_SHARE_COLUMNS = [
    "pct_branca_adm",
    "pct_preta_adm",
    "pct_parda_adm",
    "pct_negra_adm",
    "pct_amarela_adm",
    "pct_indigena_adm",
    "pct_raca_nao_informada_adm",
]

CODIGOS_GRAU_INSTRUCAO_VALIDOS = {
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "80", "99"
}
CODIGOS_GRAU_INSTRUCAO_SUPERIOR_COMPLETO_OU_MAIS = {"9", "10", "11", "80"}

# ---------------------------------------------------------------------------
# Colunas a selecionar do CAGED (BigQuery)
# ---------------------------------------------------------------------------
COLUNAS_CAGED = """
    ano,
    mes,
    sigla_uf,
    id_municipio,
    cbo_2002,
    categoria,
    tipo_movimentacao,
    saldo_movimentacao,
    salario_mensal,
    grau_instrucao,
    idade,
    sexo,
    raca_cor,
    cnae_2_secao,
    cnae_2_subclasse,
    tamanho_estabelecimento_janeiro
"""

# ---------------------------------------------------------------------------
# Arquivo ILO (processado na Etapa 1a)
# ---------------------------------------------------------------------------
ILO_FILE = DATA_PROCESSED / "ilo_exposure_clean.csv"

# ---------------------------------------------------------------------------
# Crosswalk CBO → ISCO-08
# ---------------------------------------------------------------------------
# Muendler & Poole (2004): CBO 1994 → ISCO-88 (ATENÇÃO: CBO 1994, NÃO CBO 2002!)
MUENDLER_URL  = "https://econweb.ucsd.edu/~muendler/download/brazil/cbo/cbo-isco-conc.csv"
MUENDLER_FILE = DATA_INPUT / "cbo-isco-conc.csv"

# Correspondência oficial ISCO-08 ↔ ISCO-88 (arquivo local, 678 mapeamentos)
ISCO_08_88_FILE = next(
    iter(sorted(DATA_INPUT.glob("*ISCO*08*a*88.xlsx"))),
    DATA_INPUT / "Correspondência ISCO 08 a 88.xlsx",
)

# Estrutura e definições ISCO-08 (619 ocupações em 4 níveis)
ISCO_08_ESTRUTURA_FILE = DATA_INPUT / "ISCO 08 Estruturas e Definições.xlsx"

# ILO: ISCO-88 → ISCO-08 correspondence (URL legada, pode falhar)
ILO_CORRTAB_URL  = "http://www.ilo.org/public/english/bureau/stat/isco/docs/corrtab88-08.xls"
ILO_CORRTAB_FILE = DATA_INPUT / "corrtab88-08.xls"

# ---------------------------------------------------------------------------
# Arquivos intermediários e de saída
# ---------------------------------------------------------------------------
CAGED_RAW_PATTERN   = str(DATA_RAW / "caged_{ano}.parquet")
CAGED_COMPLETO_FILE = DATA_RAW / "caged_completo.parquet"
PAINEL_MENSAL_FILE  = DATA_PROCESSED / "painel_caged_mensal.parquet"
PAINEL_CROSSWALK_FILE = DATA_PROCESSED / "painel_caged_crosswalk.parquet"
PAINEL_CROSSWALK_CSV = DATA_PROCESSED / "painel_caged_crosswalk.csv"
PAINEL_TRATAMENTO_FILE = DATA_PROCESSED / "painel_caged_tratamento.parquet"
PAINEL_FINAL_PARQUET = DATA_OUTPUT / "painel_caged_did_ready.parquet"
PAINEL_FINAL_CSV     = DATA_OUTPUT / "painel_caged_did_ready.csv"

# Official MTE bridge cache shared with the crosswalk audit.
MTE_BRIDGE_CACHE = REPO_ROOT / "outputs" / "crosswalk_audit" / "source_dictionaries" / "mte_cbo2002_cbo94_ciuo88_by_family.csv"
EXPECTED_MTE_MATCHED_CODES = 436
EXPECTED_MTE_NO_RESULT_CODES = 193

# ---------------------------------------------------------------------------
# Grandes grupos CBO (para sanity checks)
# ---------------------------------------------------------------------------
GRANDES_GRUPOS_CBO = {
    '0': 'Forças Armadas',
    '1': 'Dirigentes',
    '2': 'Profissionais das ciências',
    '3': 'Técnicos nível médio',
    '4': 'Trabalhadores de serv. admin.',
    '5': 'Trabalhadores de serviços/comércio',
    '6': 'Agropecuária',
    '7': 'Produção industrial',
    '8': 'Operadores de máquinas',
    '9': 'Manutenção e reparação',
}


def print_config():
    """Imprime a configuração atual."""
    print("=" * 60)
    print("CONFIGURAÇÃO — Etapa 2a")
    print("=" * 60)
    print(f"  Repo root:    {REPO_ROOT}")
    print(f"  Notebook dir: {REPO_ROOT}")
    print(f"  Período:      {ANO_INICIO}–{ANO_FIM} ({(ANO_FIM - ANO_INICIO + 1) * 12} meses)")
    print(f"  Evento:       ChatGPT — Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
    print(f"  Projeto GCP:  {GCP_PROJECT_ID}")
    print(f"  ILO file:     {ILO_FILE} (existe: {ILO_FILE.exists()})")
    print(f"  Data input:   {DATA_INPUT}")
    print(f"  Data raw:     {DATA_RAW}")
    print(f"  Data processed: {DATA_PROCESSED}")
    print(f"  Data output:  {DATA_OUTPUT}")
    print("=" * 60)


# if __name__ == "__main__":
#     print_config()


def normalize_categorical_codes(series):
    """Normalize raw CAGED categorical codes to stable string values."""
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def validate_allowed_codes(df, column, allowed_codes, context):
    """Fail early when raw CAGED categorical codes drift from known values."""
    if column not in df.columns:
        raise ValueError(f"{context}: missing required raw CAGED column {column!r}.")
    codes = normalize_categorical_codes(df[column])
    observed = set(codes.dropna().unique())
    unexpected = sorted(observed - set(allowed_codes), key=str)
    if unexpected:
        raise ValueError(
            f"{context}: unexpected values in raw CAGED column {column!r}: "
            f"{unexpected}. Expected subset: {sorted(allowed_codes, key=str)}."
        )
    return observed


def validate_raw_caged_codes(df, context):
    """Validate raw sex, race/color, and education codes before recoding."""
    sexo_codes = validate_allowed_codes(df, "sexo", CODIGOS_SEXO_VALIDOS, context)
    validate_allowed_codes(df, "raca_cor", CODIGOS_RACA_COR_VALIDOS, context)
    validate_allowed_codes(df, "grau_instrucao", CODIGOS_GRAU_INSTRUCAO_VALIDOS, context)
    if CODIGO_SEXO_MULHER not in sexo_codes:
        raise ValueError(
            f"{context}: female sex code {CODIGO_SEXO_MULHER!r} not found in raw CAGED."
        )


def validate_pct_mulher_adm(painel, context):
    """Fail if the aggregated female share is still all zero or unavailable."""
    if "pct_mulher_adm" not in painel.columns:
        raise ValueError(f"{context}: missing pct_mulher_adm column.")
    max_value = painel["pct_mulher_adm"].max(skipna=True)
    if pd.isna(max_value) or float(max_value) == 0.0:
        raise ValueError(
            f"{context}: pct_mulher_adm.max() == {max_value}. "
            "The CAGED monthly panel must be rebuilt with CODIGO_SEXO_MULHER = 3."
        )


def validate_raca_cor_adm(painel, context):
    """Fail if race/color admission shares are missing, invalid, or all zero."""
    missing = [col for col in RACE_SHARE_COLUMNS if col not in painel.columns]
    if missing:
        raise ValueError(f"{context}: missing race/color admission share columns: {missing}.")
    for col in RACE_SHARE_COLUMNS:
        values = pd.to_numeric(painel[col], errors="coerce")
        if ((values < 0) | (values > 1)).any():
            raise ValueError(f"{context}: {col} has values outside [0, 1].")
    max_negra = pd.to_numeric(painel["pct_negra_adm"], errors="coerce").max(skipna=True)
    if pd.isna(max_negra) or float(max_negra) == 0.0:
        raise ValueError(
            f"{context}: pct_negra_adm.max() == {max_negra}. "
            "Race/color admission shares must be rebuilt from raw CAGED raca_cor."
        )


def monthly_panel_cache_is_stale():
    """Return True when the cached monthly panel carries stale demographic mappings."""
    if not PAINEL_MENSAL_FILE.exists():
        return False
    try:
        painel_check = pd.read_parquet(
            PAINEL_MENSAL_FILE,
            columns=["pct_mulher_adm", *RACE_SHARE_COLUMNS],
        )
        validate_pct_mulher_adm(painel_check, str(PAINEL_MENSAL_FILE))
        validate_raca_cor_adm(painel_check, str(PAINEL_MENSAL_FILE))
    except Exception as exc:
        print(
            f"  Cache mensal inválido ou stale ({exc}). Reagregando microdados CAGED."
        )
        return True
    return False



# # ============================================================
# # 01_download_caged.py
# # ============================================================

# """
# Script 01: Download dos microdados CAGED via BigQuery
# Entrada: Query BigQuery (basedosdados.br_me_caged.microdados_movimentacao)
# Saída:   data/raw/caged_{ano}.parquet (por ano)

# Duas estratégias de download disponíveis:
#   ESTRATÉGIA A (RÁPIDA — recomendada): Usa google-cloud-bigquery com Storage API
#     (download paralelo via gRPC/Arrow). ~10x mais rápido que basedosdados.
#   ESTRATÉGIA B (FALLBACK): Usa basedosdados (REST API). Mais lento, mas funcional.

# O script SEMPRE verifica se o parquet já existe antes de baixar.
# """



# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE ESTRATÉGIA
# ═══════════════════════════════════════════════════════════════════════════
# Trocar para "B" se a estratégia A falhar
ESTRATEGIA = "A"  # "A" = google-cloud-bigquery + bqstorage (rápido)
                   # "B" = basedosdados (lento, fallback)

# # ═══════════════════════════════════════════════════════════════════════════
# # FUNÇÕES DE DOWNLOAD
# # ═══════════════════════════════════════════════════════════════════════════

def download_bigquery_rapido(query, descricao=""):
    """
    Estratégia A: google-cloud-bigquery + BigQuery Storage API.
    Usa download paralelo via gRPC/Arrow — muito mais rápido para grandes volumes.
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=GCP_PROJECT_ID)
    print(f"  Executando query{f' ({descricao})' if descricao else ''}...")
    t0 = time.time()

    # create_bqstorage_client=True ativa a Storage Read API (download paralelo)
    df = client.query(query).to_dataframe(create_bqstorage_client=True)

    elapsed = time.time() - t0
    print(f"  Concluído em {elapsed:.0f}s — {len(df):,} linhas")
    return df


def download_basedosdados(query, descricao=""):
    """
    Estratégia B (fallback): basedosdados (REST API). Funcional mas lento.
    """
    import basedosdados as bd

    print(f"  Executando query via basedosdados{f' ({descricao})' if descricao else ''}...")
    t0 = time.time()

    df = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID)

    elapsed = time.time() - t0
    print(f"  Concluído em {elapsed:.0f}s — {len(df):,} linhas")
    return df


def download(query, descricao=""):
    """Dispatcher: escolhe estratégia A ou B."""
    if ESTRATEGIA == "A":
        try:
            return download_bigquery_rapido(query, descricao)
        except Exception as e:
            print(f"  AVISO: Estratégia A falhou ({e}). Tentando fallback (basedosdados)...")
            return download_basedosdados(query, descricao)
    else:
        return download_basedosdados(query, descricao)


# ═══════════════════════════════════════════════════════════════════════════
# VERIFICAÇÕES
# ═══════════════════════════════════════════════════════════════════════════

def verificar_tabelas():
    """Listar tabelas disponíveis no dataset CAGED."""
    query = """
    SELECT table_name
    FROM `basedosdados.br_me_caged.INFORMATION_SCHEMA.TABLES`
    """
    df = download(query, "listar tabelas")
    tabelas = df['table_name'].tolist()
    print(f"  Tabelas: {tabelas}")
    return tabelas


def verificar_colunas():
    """Verificar colunas da tabela microdados_movimentacao."""
    query = """
    SELECT column_name, data_type
    FROM `basedosdados.br_me_caged.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'microdados_movimentacao'
    ORDER BY ordinal_position
    """
    df = download(query, "listar colunas")
    print(f"  Colunas ({len(df)}):")
    for _, row in df.iterrows():
        print(f"    {row['column_name']}: {row['data_type']}")
    return df


def verificar_cobertura():
    """Verificar anos/meses disponíveis e volume por ano."""
    query = f"""
    SELECT ano, COUNT(DISTINCT mes) as n_meses, COUNT(*) as n_registros
    FROM `basedosdados.br_me_caged.microdados_movimentacao`
    WHERE ano BETWEEN {ANO_INICIO} AND {ANO_FIM}
    GROUP BY ano
    ORDER BY ano
    """
    df = download(query, "cobertura temporal")
    print(f"\n  Cobertura temporal:")
    for _, row in df.iterrows():
        print(f"    {int(row['ano'])}: {int(row['n_meses'])} meses, {int(row['n_registros']):,} registros")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# DOWNLOAD ANO A ANO
# ═══════════════════════════════════════════════════════════════════════════

def download_caged_ano(ano):
    """Baixar microdados de um ano. Pula se parquet já existe."""
    parquet_path = DATA_RAW / f"caged_{ano}.parquet"

    # ── Caminho rápido: já existe ──
    if parquet_path.exists():
        size_mb = parquet_path.stat().st_size / 1e6
        print(f"\n  [{ano}] JÁ EXISTE: {parquet_path.name} ({size_mb:.1f} MB)")
        df_ano = pd.read_parquet(parquet_path)
        print(f"  [{ano}] Carregado do disco: {len(df_ano):,} registros")
        return df_ano

    # ── Download do BigQuery ──
    print(f"\n  [{ano}] Iniciando download...")

    query = f"""
    SELECT {COLUNAS_CAGED}
    FROM `basedosdados.br_me_caged.microdados_movimentacao`
    WHERE ano = {ano}
    """

    t0 = time.time()
    df_ano = download(query, f"CAGED {ano}")
    elapsed = time.time() - t0

    # Salvar
    df_ano.to_parquet(parquet_path, index=False)
    size_mb = parquet_path.stat().st_size / 1e6
    print(f"  [{ano}] Salvo: {parquet_path.name} ({size_mb:.1f} MB, {elapsed:.0f}s)")

    return df_ano


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def step_01():
    print("=" * 60)
    print("ETAPA 2a.2a — Download dos microdados CAGED")
    print("=" * 60)
    print(f"  Período: {ANO_INICIO}–{ANO_FIM}")
    print(f"  Projeto GCP: {GCP_PROJECT_ID}")
    print(f"  Estratégia: {'A (BigQuery Storage API — rápido)' if ESTRATEGIA == 'A' else 'B (basedosdados — fallback)'}")
    print(f"  Destino: {DATA_RAW}")

    # ── Verificar o que já foi baixado ──
    existentes = []
    faltantes = []
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        p = DATA_RAW / f"caged_{ano}.parquet"
        if p.exists():
            existentes.append(ano)
        else:
            faltantes.append(ano)

    print(f"\n  Já baixados: {existentes if existentes else 'nenhum'}")
    print(f"  Faltantes:   {faltantes if faltantes else 'nenhum (tudo pronto!)'}")

    # ── Se precisa baixar, verificar BigQuery ──
    if faltantes:
        print(f"\n--- Verificando BigQuery ---")
        verificar_tabelas()
        verificar_colunas()
        verificar_cobertura()

    # ── Download ano a ano ──
    print(f"\n--- Download dos microdados ---")
    dfs_anuais = []
    t_total = time.time()

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        df_ano = download_caged_ano(ano)
        dfs_anuais.append(df_ano)

    elapsed_total = time.time() - t_total

    # ── Resumo (SEM concatenar — evita OOM com ~180M linhas) ──
    print(f"\n{'=' * 60}")
    print(f"RESUMO — Download CAGED")
    print(f"{'=' * 60}")
    total_linhas = sum(len(df) for df in dfs_anuais)
    print(f"  Total: {total_linhas:,} movimentações ({ANO_INICIO}–{ANO_FIM})")
    print(f"  Tempo total: {elapsed_total:.0f}s")
    for df_ano in dfs_anuais:
        ano = int(df_ano['ano'].iloc[0])
        print(f"    {ano}: {len(df_ano):,}")
    print(f"  Colunas: {list(dfs_anuais[0].columns)}")
    total_mb = sum((DATA_RAW / f"caged_{a}.parquet").stat().st_size for a in range(ANO_INICIO, ANO_FIM + 1)) / 1e6
    print(f"  Total em disco: {total_mb:.0f} MB ({len(dfs_anuais)} arquivos)")
    print(f"\n  NOTA: Arquivos mantidos separados por ano para evitar OOM na concatenação.")
    print(f"  Scripts downstream carregam ano a ano e processam incrementalmente.")

    return dfs_anuais


# if __name__ == "__main__":
#     df = main()

# # ============================================================
# # 02_verificar_caged.py
# # ============================================================

# """
# Script 02: Verificar dados CAGED (CHECKPOINT)
# Entrada: data/raw/caged_{ano}.parquet
# Saída:   (prints de verificação — nenhum arquivo)

# Carrega ano a ano para evitar OOM.
# """




def step_02():
    print("=" * 60)
    print("CHECKPOINT — Microdados CAGED")
    print("=" * 60)

    # ── Verificar arquivos ──
    total_registros = 0
    registros_por_ano = {}

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        p = DATA_RAW / f"caged_{ano}.parquet"
        if not p.exists():
            print(f"  ERRO: {p.name} não encontrado!")
            return
        size_mb = p.stat().st_size / 1e6
        df = pd.read_parquet(p)
        registros_por_ano[ano] = len(df)
        total_registros += len(df)
        print(f"  {ano}: {len(df):,} registros ({size_mb:.0f} MB)")

        # Liberar memória
        del df

    print(f"\n  Total: {total_registros:,} registros")

    # ── Verificação detalhada ano a ano ──
    print(f"\n--- Verificação detalhada ---")

    todas_colunas = None
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        df = pd.read_parquet(DATA_RAW / f"caged_{ano}.parquet")
        print(f"\n  [{ano}]")

        # Colunas
        if todas_colunas is None:
            todas_colunas = set(df.columns)
            print(f"    Colunas: {list(df.columns)}")
        else:
            if set(df.columns) != todas_colunas:
                print(f"    AVISO: Colunas diferentes! {set(df.columns) - todas_colunas}")

        # Meses cobertos
        meses = sorted(df['mes'].dropna().unique())
        print(f"    Meses: {len(meses)} — {list(meses)}")
        if len(meses) != 12:
            print(f"    WARNING: Esperado 12 meses, encontrado {len(meses)}")

        # Preenchimento
        for col in ['cbo_2002', 'saldo_movimentacao', 'salario_mensal', 'idade', 'sexo']:
            if col in df.columns:
                n_valid = df[col].notna().sum()
                pct = n_valid / len(df) * 100
                flag = "" if pct > 95 else " WARNING" if pct > 80 else " CRÍTICO"
                print(f"    {col}: {pct:.1f}%{flag}")

        # Saldo movimentação
        if 'saldo_movimentacao' in df.columns:
            saldo_vals = df['saldo_movimentacao'].value_counts()
            for val, count in saldo_vals.items():
                print(f"    saldo={val}: {count:,} ({count/len(df):.1%})")

        # CBO
        if 'cbo_2002' in df.columns:
            n_cbo = df['cbo_2002'].nunique()
            sample = df['cbo_2002'].dropna().astype(str).head(5).tolist()
            print(f"    CBOs únicos: {n_cbo:,}, amostra: {sample}")

        del df

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 03_agregar_painel.py
# # ============================================================

# """
# Script 03: Agregar microdados CAGED em painel mensal por ocupação
# Entrada: data/raw/caged_{ano}.parquet
# Saída:   data/processed/painel_caged_mensal.parquet

# Processa ano a ano para evitar OOM, agrega por CBO 4 dígitos × mês.
# OTIMIZADO: evita lambdas no groupby (que são ~100x mais lentos).
# """




def log(msg):
    """Print com flush imediato para feedback em tempo real."""
    print(msg, flush=True)


def processar_ano(ano):
    """Carrega um ano e retorna painéis de admissões e desligamentos."""
    t0 = time.time()
    df = pd.read_parquet(DATA_RAW / f"caged_{ano}.parquet")
    log(f"  [{ano}] Carregado: {len(df):,} registros ({time.time()-t0:.0f}s)")

    validate_raw_caged_codes(df, f"CAGED {ano}")

    # ── CBO 4 dígitos ──
    df['cbo_2002'] = df['cbo_2002'].astype(str).str.strip()
    df['cbo_4d'] = df['cbo_2002'].str[:4]

    # Remover CBO inválidos
    cbo_invalidos = ['0000', 'nan', '', 'None']
    n_antes = len(df)
    df = df[~df['cbo_4d'].isin(cbo_invalidos)]
    df = df[df['cbo_4d'].str.len() == 4]
    df = df[df['cbo_4d'].str.isdigit()]
    n_depois = len(df)
    log(f"  [{ano}] CBOs válidos: {n_depois:,} / {n_antes:,} ({n_depois/n_antes:.1%})")

    # ── PRÉ-COMPUTAR flags booleanas (VETORIZADO — muito mais rápido que lambda) ──
    df['sexo_code'] = normalize_categorical_codes(df['sexo'])
    df['grau_instrucao_code'] = normalize_categorical_codes(df['grau_instrucao'])
    df['is_mulher'] = (df['sexo_code'] == CODIGO_SEXO_MULHER).astype(float)
    df['is_superior'] = df['grau_instrucao_code'].isin(
        CODIGOS_GRAU_INSTRUCAO_SUPERIOR_COMPLETO_OU_MAIS
    ).astype(float)
    df['raca_cor_code'] = normalize_categorical_codes(df['raca_cor'])
    df['is_raca_branca'] = (df['raca_cor_code'] == CODIGO_RACA_COR_BRANCA).astype(float)
    df['is_raca_preta'] = (df['raca_cor_code'] == CODIGO_RACA_COR_PRETA).astype(float)
    df['is_raca_parda'] = (df['raca_cor_code'] == CODIGO_RACA_COR_PARDA).astype(float)
    df['is_raca_negra'] = df['raca_cor_code'].isin(CODIGOS_RACA_COR_NEGRA).astype(float)
    df['is_raca_amarela'] = (df['raca_cor_code'] == CODIGO_RACA_COR_AMARELA).astype(float)
    df['is_raca_indigena'] = (df['raca_cor_code'] == CODIGO_RACA_COR_INDIGENA).astype(float)
    df['is_raca_nao_informada'] = df['raca_cor_code'].isin(
        CODIGOS_RACA_COR_NAO_INFORMADA_AGREGADA
    ).astype(float)

    # ── Separar admissões e desligamentos ──
    df_adm = df[df['saldo_movimentacao'] == 1]
    df_des = df[df['saldo_movimentacao'] == -1]
    log(f"  [{ano}] Admissões: {len(df_adm):,} | Desligamentos: {len(df_des):,}")

    # ── Agregar admissões ──
    # NOTA: 'median' removida do agg para performance (~10x mais rápido).
    # Calculada separadamente depois via quantile.
    t1 = time.time()
    painel_adm = df_adm.groupby(['cbo_4d', 'ano', 'mes']).agg(
        admissoes=('saldo_movimentacao', 'count'),
        salario_medio_adm=('salario_mensal', 'mean'),
        idade_media_adm=('idade', 'mean'),
        pct_mulher_adm=('is_mulher', 'mean'),
        pct_superior_adm=('is_superior', 'mean'),
        pct_branca_adm=('is_raca_branca', 'mean'),
        pct_preta_adm=('is_raca_preta', 'mean'),
        pct_parda_adm=('is_raca_parda', 'mean'),
        pct_negra_adm=('is_raca_negra', 'mean'),
        pct_amarela_adm=('is_raca_amarela', 'mean'),
        pct_indigena_adm=('is_raca_indigena', 'mean'),
        pct_raca_nao_informada_adm=('is_raca_nao_informada', 'mean'),
    ).reset_index()
    log(f"  [{ano}] Admissões agregadas: {len(painel_adm):,} ({time.time()-t1:.0f}s)")

    # Mediana salarial (separada — mais rápida que dentro do agg)
    t1 = time.time()
    mediana = df_adm.groupby(['cbo_4d', 'ano', 'mes'])['salario_mensal'].median().reset_index()
    mediana.columns = ['cbo_4d', 'ano', 'mes', 'salario_mediano_adm']
    painel_adm = painel_adm.merge(mediana, on=['cbo_4d', 'ano', 'mes'], how='left')
    log(f"  [{ano}] Mediana salarial: ({time.time()-t1:.0f}s)")
    validate_pct_mulher_adm(painel_adm, f"CAGED {ano} monthly admissions aggregation")
    validate_raca_cor_adm(painel_adm, f"CAGED {ano} monthly admissions aggregation")

    # ── Agregar desligamentos ──
    t1 = time.time()
    painel_des = df_des.groupby(['cbo_4d', 'ano', 'mes']).agg(
        desligamentos=('saldo_movimentacao', 'count'),
        salario_medio_desl=('salario_mensal', 'mean'),
    ).reset_index()
    log(f"  [{ano}] Desligamentos agregados: {len(painel_des):,} ({time.time()-t1:.0f}s)")

    elapsed = time.time() - t0
    log(f"  [{ano}] Total: {elapsed:.0f}s")

    # Liberar memória
    del df, df_adm, df_des

    return painel_adm, painel_des


def step_03():
    print("=" * 60)
    print("ETAPA 2a.3a — Agregação: Microdados → Painel Mensal")
    print("=" * 60)

    t_total = time.time()

    # ── Processar ano a ano ──
    paineis_adm = []
    paineis_des = []

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        p_adm, p_des = processar_ano(ano)
        paineis_adm.append(p_adm)
        paineis_des.append(p_des)

    # ── Concatenar os painéis anuais (pequenos, ~7k linhas cada) ──
    painel_adm = pd.concat(paineis_adm, ignore_index=True)
    painel_des = pd.concat(paineis_des, ignore_index=True)
    print(f"\nPainel admissões (total): {len(painel_adm):,}")
    print(f"Painel desligamentos (total): {len(painel_des):,}")

    # ── Merge admissões + desligamentos ──
    painel = painel_adm.merge(
        painel_des,
        on=['cbo_4d', 'ano', 'mes'],
        how='outer'
    ).fillna(0)

    # ── Variáveis derivadas ──
    painel['saldo'] = painel['admissoes'] - painel['desligamentos']
    painel['n_movimentacoes'] = painel['admissoes'] + painel['desligamentos']

    # Temporal
    painel['periodo'] = (painel['ano'].astype(int).astype(str) + '-' +
                         painel['mes'].astype(int).astype(str).str.zfill(2))
    painel['periodo_num'] = painel['ano'].astype(int) * 100 + painel['mes'].astype(int)
    painel['post'] = (painel['periodo_num'] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)

    # Log-transformações
    painel['ln_admissoes'] = np.log(painel['admissoes'] + 1)
    painel['ln_desligamentos'] = np.log(painel['desligamentos'] + 1)
    painel['ln_salario_adm'] = np.log(painel['salario_medio_adm'].clip(lower=1))

    # CBO 2 dígitos
    painel['cbo_2d'] = painel['cbo_4d'].str[:2]
    validate_pct_mulher_adm(painel, str(PAINEL_MENSAL_FILE))
    validate_raca_cor_adm(painel, str(PAINEL_MENSAL_FILE))

    # ── Salvar ──
    painel.to_parquet(PAINEL_MENSAL_FILE, index=False)
    size_mb = PAINEL_MENSAL_FILE.stat().st_size / 1e6

    elapsed_total = time.time() - t_total

    # ── Resumo ──
    print(f"\n{'=' * 60}")
    print(f"PAINEL MENSAL CONSTRUÍDO")
    print(f"{'=' * 60}")
    print(f"  Linhas: {len(painel):,} (ocupação × mês)")
    print(f"  Ocupações CBO 4d: {painel['cbo_4d'].nunique()}")
    print(f"  Períodos: {painel['periodo'].nunique()} meses")
    print(f"  Períodos pré:  {painel[painel['post']==0]['periodo'].nunique()}")
    print(f"  Períodos pós:  {painel[painel['post']==1]['periodo'].nunique()}")
    print(f"  Colunas: {list(painel.columns)}")
    print(f"  Salvo: {PAINEL_MENSAL_FILE.name} ({size_mb:.1f} MB)")
    print(f"  Tempo total: {elapsed_total:.0f}s ({elapsed_total/60:.1f} min)")

    return painel


# if __name__ == "__main__":
#     painel = main()

# # ============================================================
# # 04_verificar_painel.py
# # ============================================================

# """
# Script 04: Verificar painel agregado (CHECKPOINT)
# Entrada: data/processed/painel_caged_mensal.parquet
# Saída:   (prints de verificação — nenhum arquivo)
# """




def step_04():
    print("=" * 60)
    print("CHECKPOINT — Painel Ocupação × Mês")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_MENSAL_FILE)
    print(f"Carregado: {len(painel):,} linhas")
    validate_pct_mulher_adm(painel, str(PAINEL_MENSAL_FILE))
    validate_raca_cor_adm(painel, str(PAINEL_MENSAL_FILE))

    # ── Dimensões ──
    n_ocup = painel['cbo_4d'].nunique()
    n_periodos = painel['periodo'].nunique()
    print(f"\n--- Dimensões ---")
    print(f"  Ocupações CBO 4d: {n_ocup}")
    print(f"  Períodos: {n_periodos}")
    print(f"  Painel teórico (balanceado): {n_ocup * n_periodos:,}")
    print(f"  Painel real: {len(painel):,}")
    print(f"  Balanceamento: {len(painel) / (n_ocup * n_periodos):.1%}")

    # ── Ocupações com poucos meses ──
    ocup_meses = painel.groupby('cbo_4d')['periodo'].nunique()
    print(f"\n--- Meses por ocupação ---")
    print(f"  Min: {ocup_meses.min()}, Max: {ocup_meses.max()}, Média: {ocup_meses.mean():.1f}")
    print(f"  Com < 12 meses: {(ocup_meses < 12).sum()}")
    print(f"  Com todos os {n_periodos} meses: {(ocup_meses == n_periodos).sum()}")

    # ── Estatísticas descritivas ──
    print(f"\n--- Estatísticas descritivas ---")
    cols_stats = ['admissoes', 'desligamentos', 'saldo', 'salario_medio_adm']
    cols_disponíveis = [c for c in cols_stats if c in painel.columns]
    print(painel[cols_disponíveis].describe().round(2))

    # ── Série temporal ──
    ts = painel.groupby('periodo_num').agg(
        total_admissoes=('admissoes', 'sum'),
        total_desligamentos=('desligamentos', 'sum'),
        salario_medio=('salario_medio_adm', 'mean'),
    ).reset_index()

    print(f"\n--- Série temporal (primeiros e últimos 3 meses) ---")
    print(ts.head(3).to_string(index=False))
    print("...")
    print(ts.tail(3).to_string(index=False))

    # ── Verificação pré/pós ──
    n_pre = painel[painel['post'] == 0]['periodo'].nunique()
    n_pos = painel[painel['post'] == 1]['periodo'].nunique()
    print(f"\n--- Pré/Pós tratamento ---")
    print(f"  Meses pré:  {n_pre}")
    print(f"  Meses pós:  {n_pos}")

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 05_crosswalk_cbo_isco.py
# # ============================================================

# """
# Script 05: Crosswalk CBO 2002 → ISCO-08 (dual: 2d principal + 4d robustez)
# Entrada: data/processed/painel_caged_mensal.parquet, data/processed/ilo_exposure_clean.csv
# Saída:   data/processed/painel_caged_crosswalk.parquet

# ═══════════════════════════════════════════════════════════════════════════
# CONTEXTO METODOLÓGICO
# ═══════════════════════════════════════════════════════════════════════════
# A CBO 2002 (Classificação Brasileira de Ocupações) foi construída com base
# na ISCO-88 e na ISCO-08, compartilhando a mesma estrutura hierárquica:
#   • 1 dígito (Grande Grupo)  — alinhamento perfeito com ISCO-08 Major Group
#   • 2 dígitos (Subgrupo Principal) — bom alinhamento com ISCO-08 Sub-major Group
#   • 3 dígitos (Subgrupo) — alinhamento parcial com ISCO-08 Minor Group
#   • 4 dígitos (Família) — divergência significativa com ISCO-08 Unit Group

# NOTA: A tabela Muendler (cbo-isco-conc.csv) mapeia CBO *1994* → ISCO-88,
# NÃO a CBO 2002 usada no CAGED. Portanto, o match 4d via Muendler é limitado
# e serve apenas como fonte auxiliar.

# ESTRATÉGIA
# ═══════════════════════════════════════════════════════════════════════════
# PARTE A (Principal — 2 dígitos):
#   CBO 2d → ISCO-08 2d (direto) → fallback CBO 1d → ISCO-08 Major Group

# PARTE B (Robustez — 4 dígitos, fallback hierárquico em 6 níveis):
#   Nível 1: CBO 4d = ISCO-08 4d  (match direto, ~28%)
#   Nível 2: CBO 4d = ISCO-88 4d → ISCO-08 4d via tabela de correspondência (~+9%)
#   Nível 3: CBO 3d = ISCO-08 3d → média do Minor Group (~+15%)
#   Nível 4: CBO 3d = ISCO-88 3d → ISCO-08 3d via correspondência (~+5%)
#   Nível 5: CBO 2d = ISCO-08 2d → média do Sub-major Group (= spec principal)
#   Nível 6: CBO 1d = ISCO-08 1d → média do Major Group (sempre funciona)
# """




def log(msg):
    print(msg, flush=True)


# ─────────────────────────────────────────────────────────────────────────
# Funções auxiliares
# ─────────────────────────────────────────────────────────────────────────

def carregar_ilo():
    """Carregar índice ILO processado na Etapa 1a."""
    if not ILO_FILE.exists():
        log(f"ERRO: {ILO_FILE} não encontrado! Execute a Etapa 1a primeiro.")
        sys.exit(1)

    df_ilo = pd.read_csv(ILO_FILE)
    df_ilo['isco_08_str'] = df_ilo['isco_08'].astype(str).str.zfill(4)
    log(f"Índice ILO carregado: {len(df_ilo)} ocupações ISCO-08")
    log(f"  Score range: [{df_ilo['exposure_score'].min():.3f}, {df_ilo['exposure_score'].max():.3f}]")
    return df_ilo


def carregar_correspondencia_isco():
    """
    Carregar tabela de correspondência ISCO-08 ↔ ISCO-88 (arquivo local).
    Retorna dict ISCO-88 4d → lista de ISCO-08 4d.
    """
    if not ISCO_08_88_FILE.exists():
        log(f"AVISO: {ISCO_08_88_FILE} não encontrado.")
        return {}, {}

    df = pd.read_excel(ISCO_08_88_FILE, sheet_name='ISCO-08 to 88')
    df['isco08_4d'] = df['ISCO-08 code'].astype(str).str.strip().str.zfill(4)
    df['isco88_4d'] = df['ISCO-88 code'].astype(str).str.strip().str.zfill(4)

    # ISCO-88 4d → lista de ISCO-08 4d (muitos-para-muitos)
    isco88_to_08 = df.groupby('isco88_4d')['isco08_4d'].apply(list).to_dict()

    # ISCO-88 3d → lista de ISCO-08 3d (agregação por 3 dígitos)
    df['isco88_3d'] = df['isco88_4d'].str[:3]
    df['isco08_3d'] = df['isco08_4d'].str[:3]
    isco88_3d_to_08_3d = df.groupby('isco88_3d')['isco08_3d'].apply(
        lambda x: list(set(x))
    ).to_dict()

    log(f"  Correspondência ISCO carregada: {len(df)} mapeamentos")
    log(f"    ISCO-88 4d → ISCO-08: {len(isco88_to_08)} códigos")
    log(f"    ISCO-88 3d → ISCO-08 3d: {len(isco88_3d_to_08_3d)} grupos")

    return isco88_to_08, isco88_3d_to_08_3d


def construir_dicts_ilo(df_ilo):
    """Construir dicionários de lookup ILO em múltiplos níveis."""
    codes = df_ilo['isco_08_str']
    scores = df_ilo['exposure_score']

    # 4d: score exato por unit group
    ilo_4d = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()

    # 3d: média do minor group
    ilo_3d = df_ilo.assign(g=codes.str[:3]).groupby('g')['exposure_score'].mean().to_dict()

    # 2d: média do sub-major group
    ilo_2d = df_ilo.assign(g=codes.str[:2]).groupby('g')['exposure_score'].mean().to_dict()

    # 1d: média do major group
    ilo_1d = df_ilo.assign(g=codes.str[:1]).groupby('g')['exposure_score'].mean().to_dict()

    log(f"  Dicts ILO construídos: 4d={len(ilo_4d)}, 3d={len(ilo_3d)}, "
        f"2d={len(ilo_2d)}, 1d={len(ilo_1d)}")

    return ilo_4d, ilo_3d, ilo_2d, ilo_1d


# ─────────────────────────────────────────────────────────────────────────
# PARTE A: Crosswalk 2 dígitos (PRINCIPAL)
# ─────────────────────────────────────────────────────────────────────────

def crosswalk_2d(painel, df_ilo, ilo_2d, ilo_1d):
    """
    Match a 2 dígitos com fallback a 1 dígito.

    A CBO 2002 e a ISCO-08 compartilham os 9 major groups (1 dígito),
    mas NEM TODOS os sub-major groups (2 dígitos) coincidem.
    Ex: CBO 78 (produção industrial) não existe na ISCO-08.

    Estratégia: 2d direto → fallback 1d (média do major group).
    """
    log(f"\n{'=' * 60}")
    log(f"PARTE A: Crosswalk 2 dígitos (PRINCIPAL)")
    log(f"{'=' * 60}")

    # Match 2d direto
    painel['exposure_score_2d'] = painel['cbo_2d'].map(ilo_2d)
    painel['match_level_2d'] = np.where(painel['exposure_score_2d'].notna(), '2-digit', None)

    n_2d = painel['exposure_score_2d'].notna().sum()
    log(f"\n  Match 2d direto: {n_2d:,} / {len(painel):,} ({n_2d/len(painel):.1%})")

    # CBOs sem match 2d
    sem_match_2d = sorted(painel[painel['exposure_score_2d'].isna()]['cbo_2d'].unique())
    if sem_match_2d:
        log(f"  CBO 2d sem match ISCO-08 2d: {sem_match_2d}")

    # Fallback a 1d para linhas sem match 2d
    mask_na = painel['exposure_score_2d'].isna()
    if mask_na.any():
        cbo_1d = painel.loc[mask_na, 'cbo_4d'].str[:1]
        painel.loc[mask_na, 'exposure_score_2d'] = cbo_1d.map(ilo_1d).values
        painel.loc[mask_na, 'match_level_2d'] = '1-digit (fallback)'

        n_1d = painel.loc[mask_na, 'exposure_score_2d'].notna().sum()
        log(f"  Fallback 1d: {n_1d:,} linhas adicionais")

    # Reportar CBOs sem match em nenhum nível
    sem_match = painel[painel['exposure_score_2d'].isna()]['cbo_2d'].unique()
    if len(sem_match) > 0:
        log(f"  SEM MATCH (nenhum nível): {sorted(sem_match)}")

    coverage = painel['exposure_score_2d'].notna().mean()
    log(f"\n  COBERTURA FINAL 2d: {coverage:.1%}")

    # Distribuição por match level
    log(f"  Match levels:")
    for level, count in painel['match_level_2d'].value_counts().items():
        log(f"    {level}: {count:,} ({count/len(painel):.1%})")

    # Score principal = score 2d
    painel['exposure_score'] = painel['exposure_score_2d']

    # Top/Bottom
    log(f"\n  Top 5 CBO 2d mais expostos:")
    top = painel.groupby('cbo_2d')['exposure_score_2d'].first().nlargest(5)
    for cbo, score in top.items():
        nome = GRANDES_GRUPOS_CBO.get(cbo[0], '')
        log(f"    CBO {cbo}: {score:.3f}  ({nome})")

    log(f"\n  Bottom 5 CBO 2d menos expostos:")
    bot = painel.groupby('cbo_2d')['exposure_score_2d'].first().nsmallest(5)
    for cbo, score in bot.items():
        nome = GRANDES_GRUPOS_CBO.get(cbo[0], '')
        log(f"    CBO {cbo}: {score:.3f}  ({nome})")

    return painel


# ─────────────────────────────────────────────────────────────────────────
# PARTE B: Crosswalk 4 dígitos (ROBUSTEZ) — fallback hierárquico 6 níveis
# ─────────────────────────────────────────────────────────────────────────

def crosswalk_4d(painel, df_ilo, ilo_4d, ilo_3d, ilo_2d, ilo_1d,
                 isco88_to_08, isco88_3d_to_08_3d):
    """
    Robustez a 4 dígitos com fallback hierárquico em 6 níveis.

    Usa a estrutura compartilhada entre CBO 2002 e ISCO-08/ISCO-88,
    mais a tabela de correspondência oficial ISCO-08 ↔ ISCO-88.
    """
    log(f"\n{'=' * 60}")
    log(f"PARTE B: Crosswalk 4 dígitos (ROBUSTEZ)")
    log(f"{'=' * 60}")

    cbos_unicos = sorted(painel['cbo_4d'].unique())
    log(f"  CBOs 4d únicos no painel: {len(cbos_unicos)}")

    # --- Construir score 4d para cada CBO 4d ---
    cbo_score_4d = {}
    cbo_match_level = {}

    # Contadores por nível
    counts = {
        'N1_isco08_4d': 0,
        'N2_via_isco88_4d': 0,
        'N3_isco08_3d': 0,
        'N4_via_isco88_3d': 0,
        'N5_isco08_2d': 0,
        'N6_isco08_1d': 0,
        'sem_match': 0,
    }

    for cbo in cbos_unicos:
        score = None
        level = None

        # ── Nível 1: CBO 4d = ISCO-08 4d (match direto) ──
        if cbo in ilo_4d:
            score = ilo_4d[cbo]
            level = 'N1: ISCO-08 4d direto'
            counts['N1_isco08_4d'] += 1

        # ── Nível 2: CBO 4d = ISCO-88 4d → ISCO-08 via correspondência ──
        if score is None and cbo in isco88_to_08:
            isco08_candidates = isco88_to_08[cbo]
            # Média dos scores dos candidatos ISCO-08 presentes no ILO
            scores_cand = [ilo_4d[c] for c in isco08_candidates if c in ilo_4d]
            if scores_cand:
                score = np.mean(scores_cand)
                level = 'N2: via ISCO-88→08 4d'
                counts['N2_via_isco88_4d'] += 1

        # ── Nível 3: CBO 3d = ISCO-08 3d (média do Minor Group) ──
        if score is None:
            cbo_3d = cbo[:3]
            if cbo_3d in ilo_3d:
                score = ilo_3d[cbo_3d]
                level = 'N3: ISCO-08 3d'
                counts['N3_isco08_3d'] += 1

        # ── Nível 4: CBO 3d = ISCO-88 3d → ISCO-08 3d via correspondência ──
        if score is None:
            cbo_3d = cbo[:3]
            if cbo_3d in isco88_3d_to_08_3d:
                isco08_3d_candidates = isco88_3d_to_08_3d[cbo_3d]
                scores_cand = [ilo_3d[c] for c in isco08_3d_candidates if c in ilo_3d]
                if scores_cand:
                    score = np.mean(scores_cand)
                    level = 'N4: via ISCO-88→08 3d'
                    counts['N4_via_isco88_3d'] += 1

        # ── Nível 5: CBO 2d = ISCO-08 2d (média do Sub-major Group) ──
        if score is None:
            cbo_2d = cbo[:2]
            if cbo_2d in ilo_2d:
                score = ilo_2d[cbo_2d]
                level = 'N5: ISCO-08 2d'
                counts['N5_isco08_2d'] += 1

        # ── Nível 6: CBO 1d = ISCO-08 1d (média do Major Group) ──
        if score is None:
            cbo_1d = cbo[:1]
            if cbo_1d in ilo_1d:
                score = ilo_1d[cbo_1d]
                level = 'N6: ISCO-08 1d'
                counts['N6_isco08_1d'] += 1

        if score is not None:
            cbo_score_4d[cbo] = score
            cbo_match_level[cbo] = level
        else:
            counts['sem_match'] += 1
            cbo_match_level[cbo] = 'sem match'

    # ── Reportar resultados ──
    log(f"\n  Fallback hierárquico — distribuição por nível:")
    total = len(cbos_unicos)
    log(f"    {'Nível':<30} {'Ocup':>6} {'%':>8}")
    log(f"    {'-'*46}")
    log(f"    {'N1: ISCO-08 4d direto':<30} {counts['N1_isco08_4d']:>6} "
        f"{counts['N1_isco08_4d']/total:>8.1%}")
    log(f"    {'N2: via ISCO-88→08 4d':<30} {counts['N2_via_isco88_4d']:>6} "
        f"{counts['N2_via_isco88_4d']/total:>8.1%}")
    log(f"    {'N3: ISCO-08 3d':<30} {counts['N3_isco08_3d']:>6} "
        f"{counts['N3_isco08_3d']/total:>8.1%}")
    log(f"    {'N4: via ISCO-88→08 3d':<30} {counts['N4_via_isco88_3d']:>6} "
        f"{counts['N4_via_isco88_3d']/total:>8.1%}")
    log(f"    {'N5: ISCO-08 2d':<30} {counts['N5_isco08_2d']:>6} "
        f"{counts['N5_isco08_2d']/total:>8.1%}")
    log(f"    {'N6: ISCO-08 1d':<30} {counts['N6_isco08_1d']:>6} "
        f"{counts['N6_isco08_1d']/total:>8.1%}")
    log(f"    {'Sem match':<30} {counts['sem_match']:>6} "
        f"{counts['sem_match']/total:>8.1%}")
    log(f"    {'-'*46}")

    matched = sum(v for k, v in counts.items() if k != 'sem_match')
    log(f"    {'TOTAL COM SCORE':<30} {matched:>6} {matched/total:>8.1%}")

    # Granularidade: % com informação genuinamente 4d (N1 + N2)
    n_4d_genuine = counts['N1_isco08_4d'] + counts['N2_via_isco88_4d']
    log(f"\n  Informação genuinamente 4d: {n_4d_genuine}/{total} ({n_4d_genuine/total:.1%})")
    log(f"  Informação ≤3d (fallback): {matched - n_4d_genuine}/{total} "
        f"({(matched - n_4d_genuine)/total:.1%})")

    # Aplicar ao painel
    painel['exposure_score_4d'] = painel['cbo_4d'].map(cbo_score_4d)
    painel['match_level_4d'] = painel['cbo_4d'].map(cbo_match_level)

    coverage_4d = painel['exposure_score_4d'].notna().mean()
    log(f"\n  COBERTURA FINAL 4d (linhas no painel): {coverage_4d:.1%}")

    # Distribuição de match levels no painel (ponderado por linhas)
    log(f"\n  Match levels (ponderados por linhas no painel):")
    for level, count in painel['match_level_4d'].value_counts().items():
        log(f"    {level}: {count:,} ({count/len(painel):.1%})")

    # CBOs sem match
    sem = sorted(painel[painel['exposure_score_4d'].isna()]['cbo_4d'].unique())
    if sem:
        log(f"\n  CBOs sem match 4d ({len(sem)}): {sem[:20]}{'...' if len(sem) > 20 else ''}")

    return painel


# ─────────────────────────────────────────────────────────────────────────
# Diagnóstico: concordância 2d vs 4d
# ─────────────────────────────────────────────────────────────────────────

def diagnostico_concordancia(painel):
    """Comparar scores 2d e 4d para verificar consistência."""
    log(f"\n{'=' * 60}")
    log(f"DIAGNÓSTICO: Concordância 2d vs 4d")
    log(f"{'=' * 60}")

    mask = painel['exposure_score_2d'].notna() & painel['exposure_score_4d'].notna()
    df = painel.loc[mask, ['cbo_4d', 'exposure_score_2d', 'exposure_score_4d']].drop_duplicates(
        subset='cbo_4d'
    )

    if len(df) < 2:
        log("  Insuficiente para calcular correlação.")
        return

    corr = df['exposure_score_2d'].corr(df['exposure_score_4d'])
    log(f"  Ocupações com ambos os scores: {len(df)}")
    log(f"  Correlação Pearson (2d vs 4d): {corr:.4f}")

    diff = (df['exposure_score_4d'] - df['exposure_score_2d']).abs()
    log(f"  Diferença absoluta: média={diff.mean():.4f}, max={diff.max():.4f}")

    # Quantos mudam de ranking significativamente?
    # (score 4d difere >0.05 do score 2d)
    n_diff = (diff > 0.05).sum()
    log(f"  Ocupações com |diff| > 0.05: {n_diff} ({n_diff/len(df):.1%})")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def step_05():
    log("=" * 60)
    log("ETAPA 2a.4a — Crosswalk CBO 2002 → ISCO-08")
    log("=" * 60)

    # Carregar dados
    painel = pd.read_parquet(PAINEL_MENSAL_FILE)
    log(f"Painel carregado: {len(painel):,} linhas, {painel['cbo_4d'].nunique()} CBOs 4d")

    df_ilo = carregar_ilo()

    # Construir dicts de lookup em múltiplos níveis
    log(f"\nConstruindo dicionários de lookup ILO...")
    ilo_4d, ilo_3d, ilo_2d, ilo_1d = construir_dicts_ilo(df_ilo)

    # Carregar tabela de correspondência ISCO-08 ↔ ISCO-88
    log(f"\nCarregando correspondência ISCO-08 ↔ ISCO-88...")
    isco88_to_08, isco88_3d_to_08_3d = carregar_correspondencia_isco()

    # Legacy benchmark: numeric CBO=ISCO crosswalk kept only for audit.
    painel = crosswalk_2d(painel, df_ilo, ilo_2d, ilo_1d)
    painel = crosswalk_4d(painel, df_ilo, ilo_4d, ilo_3d, ilo_2d, ilo_1d,
                          isco88_to_08, isco88_3d_to_08_3d)

    painel = painel.rename(columns={
        'exposure_score_2d': 'exposure_score_2d_old',
        'exposure_score_4d': 'exposure_score_4d_old',
        'exposure_score': 'exposure_score_old',
        'match_level_2d': 'match_level_2d_old',
        'match_level_4d': 'match_level_4d_old',
    })

    log(f"\n{'=' * 60}")
    log("PARTE C: Crosswalk oficial MTE (PRINCIPAL)")
    log(f"{'=' * 60}")
    log("  Fluxo: CBO 2002 -> CIUO88/ISCO-88 -> ISCO-08 -> score OIT")
    log("  Regra: sem fallback por igualdade numérica CBO=ISCO.")
    painel = apply_mte_crosswalk(
        painel,
        ilo_file=ILO_FILE,
        isco_file=ISCO_08_88_FILE,
        cache_path=MTE_BRIDGE_CACHE,
        expected_matched_codes=EXPECTED_MTE_MATCHED_CODES,
        expected_no_result_codes=EXPECTED_MTE_NO_RESULT_CODES,
    )

    cbo_mte = painel.drop_duplicates('cbo_4d')
    status_counts = cbo_mte['mte_match_status'].value_counts()
    log("\n  Status MTE por CBO 4d:")
    for status, count in status_counts.items():
        log(f"    {status}: {count:,} ({count / len(cbo_mte):.1%})")

    matched_mask = painel['mte_match_status'] == 'matched_official_mte'
    log("\n  Cobertura MTE:")
    log(f"    CBOs com match: {cbo_mte[cbo_mte['mte_match_status'] == 'matched_official_mte'].shape[0]:,} / {len(cbo_mte):,}")
    log(f"    Linhas painel:  {matched_mask.sum():,} / {len(painel):,} ({matched_mask.mean():.1%})")
    if 'admissoes' in painel.columns:
        adm_total = painel['admissoes'].sum()
        adm_match = painel.loc[matched_mask, 'admissoes'].sum()
        log(f"    Admissões:      {adm_match:,.0f} / {adm_total:,.0f} ({adm_match / adm_total:.2%})")

    # Diagnóstico de concordância dos scores MTE 2d vs 4d.
    diagnostico_concordancia(painel)

    # Salvar
    painel.to_parquet(PAINEL_CROSSWALK_FILE, index=False)
    painel.to_csv(PAINEL_CROSSWALK_CSV, index=False)
    size_mb = PAINEL_CROSSWALK_FILE.stat().st_size / 1e6
    log(f"\nSalvo: {PAINEL_CROSSWALK_FILE.name} ({size_mb:.1f} MB)")
    log(f"Salvo: {PAINEL_CROSSWALK_CSV.name}")
    log(f"Colunas: {list(painel.columns)}")

    return painel


# if __name__ == "__main__":
#     painel = main()

# # ============================================================
# # 06_verificar_crosswalk.py
# # ============================================================

# """
# Script 06: Verificar crosswalk CBO → ISCO-08 (CHECKPOINT)
# Entrada: data/processed/painel_caged_crosswalk.parquet
# Saída:   (prints de verificação — nenhum arquivo)
# """




def step_06():
    print("=" * 60)
    print("CHECKPOINT — Crosswalk CBO → ISCO-08 (MTE official)")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_CROSSWALK_FILE)
    print(f"Carregado: {len(painel):,} linhas")
    if "crosswalk_spec" not in painel.columns or set(painel["crosswalk_spec"].dropna().unique()) != {CROSSWALK_SPEC}:
        raise ValueError(f"Painel não está na especificação esperada: {CROSSWALK_SPEC}")

    # ── 1. Cobertura ──
    coverage_2d = painel['exposure_score_2d'].notna().mean()
    coverage_4d = painel['exposure_score_4d'].notna().mean()

    print(f"\n--- Cobertura ---")
    print(f"  2 dígitos MTE (PRINCIPAL): {coverage_2d:.1%}")
    print(f"  4 dígitos MTE (ROBUSTEZ):  {coverage_4d:.1%}")
    print(f"  Especificação: {CROSSWALK_SPEC}")

    mte_by_cbo = painel.drop_duplicates('cbo_4d')
    print(f"\n--- Status MTE por CBO 4d ---")
    status_counts = mte_by_cbo['mte_match_status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count:,} CBOs ({count / len(mte_by_cbo):.1%})")

    # ── 2. Ocupações sem match ──
    sem_match_2d = painel[painel['exposure_score_2d'].isna()]['cbo_4d'].unique()
    sem_match_4d = painel[painel['exposure_score_4d'].isna()]['cbo_4d'].unique()

    print(f"\n--- Ocupações sem match ---")
    print(f"  Sem match 2d: {len(sem_match_2d)} CBOs")
    print(f"  Sem match 4d: {len(sem_match_4d)} CBOs")

    if len(sem_match_2d) > 0:
        print(f"  CBOs sem match 2d (primeiros 10):")
        for cbo in sem_match_2d[:10]:
            n = (painel['cbo_4d'] == cbo).sum()
            adm = painel.loc[painel['cbo_4d'] == cbo, 'admissoes'].sum()
            print(f"    CBO {cbo}: {n} linhas, {adm:,.0f} admissões")

    # ── 3. Estatísticas dos scores ──
    print(f"\n--- Estatísticas dos scores ---")
    print(f"\nexposure_score_2d (PRINCIPAL):")
    print(painel['exposure_score_2d'].describe().round(4))
    print(f"\nexposure_score_4d (ROBUSTEZ):")
    print(painel['exposure_score_4d'].describe().round(4))

    # ── 4. Correlação 2d vs 4d ──
    mask_both = painel['exposure_score_2d'].notna() & painel['exposure_score_4d'].notna()
    if mask_both.any():
        corr = painel.loc[mask_both, 'exposure_score_2d'].corr(
            painel.loc[mask_both, 'exposure_score_4d']
        )
        print(f"\n--- Correlação 2d vs 4d ---")
        print(f"  Pearson: {corr:.4f}")
        if corr > 0.8:
            print(f"  Alta correlação — bom sinal de consistência.")
        else:
            print(f"  Correlação moderada — as especificações podem divergir.")

    # ── 5. Sanity check por grande grupo CBO ──
    painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]

    print(f"\n--- Exposição por grande grupo CBO ---")
    print(f"{'Grande Grupo':<40} {'Score 2d':>10} {'Score 4d':>10}")
    print("-" * 62)
    for gg, nome in sorted(GRANDES_GRUPOS_CBO.items()):
        mask = painel['grande_grupo_cbo'] == gg
        if mask.any():
            s2d = painel.loc[mask, 'exposure_score_2d'].mean()
            s4d = painel.loc[mask, 'exposure_score_4d'].mean()
            s2d_str = f"{s2d:.3f}" if not np.isnan(s2d) else "N/A"
            s4d_str = f"{s4d:.3f}" if not np.isnan(s4d) else "N/A"
            flag = " (!)" if not np.isnan(s2d) and not np.isnan(s4d) and abs(s2d - s4d) > 0.1 else ""
            print(f"  {nome:<38} {s2d_str:>10} {s4d_str:>10}{flag}")

    print(f"\n  (!) = diferença > 0.1 entre 2d e 4d")

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 07_definir_tratamento.py
# # ============================================================

# """
# Script 07: Definir variáveis de tratamento para DiD
# Entrada: data/processed/painel_caged_crosswalk.parquet
# Saída:   data/processed/painel_caged_tratamento.parquet
# """




def step_07():
    print("=" * 60)
    print("ETAPA 2a.5a — Definição de Tratamento")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_CROSSWALK_FILE)
    print(f"Carregado: {len(painel):,} linhas")

    if "crosswalk_spec" not in painel.columns or set(painel["crosswalk_spec"].dropna().unique()) != {CROSSWALK_SPEC}:
        raise ValueError(f"Painel não está na especificação esperada: {CROSSWALK_SPEC}")

    # ══════════════════════════════════════════════════════════════
    # PASSO 1: Thresholds sobre ocupações com score MTE válido (2d)
    # ══════════════════════════════════════════════════════════════
    # Uma obs por CBO — cada ocupação tem peso igual
    ocup_scores_2d = painel.groupby('cbo_4d')['exposure_score_2d'].first().dropna()
    if len(ocup_scores_2d) == 0:
        raise ValueError("Nenhuma ocupação com exposure_score_2d MTE válido.")

    thresholds_2d = {
        'alta_exp_10':      ocup_scores_2d.quantile(0.90),
        'alta_exp':         ocup_scores_2d.quantile(0.80),  # PRINCIPAL
        'alta_exp_25':      ocup_scores_2d.quantile(0.75),
        'alta_exp_mediana':  ocup_scores_2d.quantile(0.50),
    }

    print(f"\nThresholds de exposição (2d, PRINCIPAL):")
    for name, val in thresholds_2d.items():
        n_above = (ocup_scores_2d >= val).sum()
        pct = n_above / len(ocup_scores_2d) * 100
        print(f"  {name}: {val:.4f} ({n_above} ocupações, {pct:.0f}%)")

    # ══════════════════════════════════════════════════════════════
    # PASSO 2: Dummies de tratamento 2d
    # ══════════════════════════════════════════════════════════════
    valid_2d = painel['exposure_score_2d'].notna()
    for name, threshold in thresholds_2d.items():
        painel[name] = np.where(valid_2d, (painel['exposure_score_2d'] >= threshold).astype(int), np.nan)

    # Quintis (2d)
    painel['quintil_exp'] = pd.NA
    painel.loc[valid_2d, 'quintil_exp'] = pd.qcut(
        painel.loc[valid_2d, 'exposure_score_2d'].rank(method='first'),
        q=5,
        labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
    ).astype(str)

    # ══════════════════════════════════════════════════════════════
    # PASSO 3: Dummies 4d (ROBUSTEZ)
    # ══════════════════════════════════════════════════════════════
    ocup_scores_4d = painel.groupby('cbo_4d')['exposure_score_4d'].first().dropna()
    if len(ocup_scores_4d) > 0:
        threshold_4d_80 = ocup_scores_4d.quantile(0.80)
        valid_4d = painel['exposure_score_4d'].notna()
        painel['alta_exp_4d'] = np.where(valid_4d, (painel['exposure_score_4d'] >= threshold_4d_80).astype(int), np.nan)
        print(f"\nThreshold 4d (p80): {threshold_4d_80:.4f}")
        print(f"  ({(ocup_scores_4d >= threshold_4d_80).sum()} ocupações acima)")
    else:
        painel['alta_exp_4d'] = np.nan
        print(f"\nAVISO: Sem scores 4d disponíveis.")

    # ══════════════════════════════════════════════════════════════
    # PASSO 4: Interações DiD
    # ══════════════════════════════════════════════════════════════
    painel['did'] = painel['post'] * painel['alta_exp']
    painel['did_4d'] = painel['post'] * painel['alta_exp_4d']

    # ══════════════════════════════════════════════════════════════
    # RESUMO
    # ══════════════════════════════════════════════════════════════
    print(f"\n--- Distribuição de tratamento ---")
    print(f"  Alta exp 2d (top 20%): {painel.loc[valid_2d, 'alta_exp'].mean():.1%} das obs com match MTE")
    print(f"  Alta exp 4d (top 20%): {painel['alta_exp_4d'].mean():.1%} das obs com match MTE")
    print(f"  Períodos pré:  {painel[painel['post']==0].shape[0]:,}")
    print(f"  Períodos pós:  {painel[painel['post']==1].shape[0]:,}")

    # Concordância 2d vs 4d
    mask_valid = painel['exposure_score_2d'].notna() & painel['exposure_score_4d'].notna()
    if mask_valid.any():
        concordancia = (painel.loc[mask_valid, 'alta_exp'] ==
                        painel.loc[mask_valid, 'alta_exp_4d']).mean()
        print(f"  Concordância 2d vs 4d: {concordancia:.1%}")

    # Tabela de contingência
    ct = pd.crosstab(
        painel['post'].map({0: 'Pré', 1: 'Pós'}),
        painel['alta_exp'].map({0: 'Controle', 1: 'Tratamento'}),
        margins=True
    )
    print(f"\nTabela de contingência (2d, principal):")
    print(ct)

    # Salvar
    painel.to_parquet(PAINEL_TRATAMENTO_FILE, index=False)
    size_mb = PAINEL_TRATAMENTO_FILE.stat().st_size / 1e6
    print(f"\nSalvo: {PAINEL_TRATAMENTO_FILE.name} ({size_mb:.1f} MB)")

    return painel


# if __name__ == "__main__":
#     painel = main()

# # ============================================================
# # 08_verificar_tratamento.py
# # ============================================================

# """
# Script 08: Verificar definição de tratamento (CHECKPOINT)
# Entrada: data/processed/painel_caged_tratamento.parquet
# Saída:   (prints de verificação — nenhum arquivo)
# """




def step_08():
    print("=" * 60)
    print("CHECKPOINT — Definição de Tratamento")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_TRATAMENTO_FILE)
    print(f"Carregado: {len(painel):,} linhas")

    # ── Top 10 ocupações mais expostas ──
    print(f"\n--- Top 10 ocupações MAIS expostas ---")
    top10 = painel.groupby('cbo_4d').agg(
        exposure=('exposure_score', 'first'),
        admissoes_total=('admissoes', 'sum'),
    ).nlargest(10, 'exposure')
    for cbo, row in top10.iterrows():
        print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}")

    # ── Bottom 10 ocupações menos expostas ──
    print(f"\n--- 10 ocupações MENOS expostas ---")
    bot10 = painel.groupby('cbo_4d').agg(
        exposure=('exposure_score', 'first'),
        admissoes_total=('admissoes', 'sum'),
    ).nsmallest(10, 'exposure')
    for cbo, row in bot10.iterrows():
        print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}")

    # ── Distribuição por quintil ──
    print(f"\n--- Estatísticas por quintil de exposição ---")
    for q in ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']:
        sub = painel[painel['quintil_exp'] == q]
        if len(sub) > 0:
            print(f"  {q}: n={len(sub):,}, "
                  f"exposure={sub['exposure_score'].mean():.3f}, "
                  f"adm_mean={sub['admissoes'].mean():.0f}, "
                  f"sal_medio={sub['salario_medio_adm'].mean():,.0f}")

    # ── Concordância 2d vs 4d ──
    mask_valid = painel['exposure_score_4d'].notna()
    if mask_valid.any():
        concordancia = (painel.loc[mask_valid, 'alta_exp'] ==
                        painel.loc[mask_valid, 'alta_exp_4d']).mean()
        print(f"\n--- Concordância 2d vs 4d: {concordancia:.1%} ---")

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


# if __name__ == "__main__":
#     main()

# # ============================================================
# # 09_enriquecer_e_salvar.py
# # ============================================================

# """
# Script 09: Enriquecer painel e salvar dataset analítico final
# Entrada: data/processed/painel_caged_tratamento.parquet
# Saída:   data/output/painel_caged_did_ready.parquet + .csv
# """




def periodo_num_to_months(pn):
    """Converter periodo_num (YYYYMM) para contagem absoluta de meses."""
    return (pn // 100) * 12 + (pn % 100)


def step_09():
    print("=" * 60)
    print("ETAPA 2a.6a+7 — Enriquecimento e Salvamento Final")
    print("=" * 60)

    painel = pd.read_parquet(PAINEL_TRATAMENTO_FILE)
    print(f"Carregado: {len(painel):,} linhas, {painel.shape[1]} colunas")
    validate_pct_mulher_adm(painel, str(PAINEL_TRATAMENTO_FILE))
    validate_raca_cor_adm(painel, str(PAINEL_TRATAMENTO_FILE))

    # ══════════════════════════════════════════════════════════════
    # PASSO 1: Tempo relativo ao tratamento
    # ══════════════════════════════════════════════════════════════
    ref_periodo = ANO_TRATAMENTO * 100 + MES_TRATAMENTO
    painel['meses_abs'] = painel['periodo_num'].apply(periodo_num_to_months)
    ref_meses = periodo_num_to_months(ref_periodo)
    painel['tempo_relativo_meses'] = painel['meses_abs'] - ref_meses

    print(f"  Tempo relativo: [{painel['tempo_relativo_meses'].min()}, "
          f"{painel['tempo_relativo_meses'].max()}] meses")
    print(f"  Referência (t=0): {MES_TRATAMENTO}/{ANO_TRATAMENTO}")

    # ══════════════════════════════════════════════════════════════
    # PASSO 2: Tendência temporal e sazonalidade
    # ══════════════════════════════════════════════════════════════
    painel['trend'] = painel['meses_abs'] - painel['meses_abs'].min()
    painel['mes_do_ano'] = painel['mes'].astype(int)

    # ══════════════════════════════════════════════════════════════
    # PASSO 3: Normalização salarial (em salários mínimos)
    # ══════════════════════════════════════════════════════════════
    painel['sm_ano'] = painel['ano'].astype(int).map(SALARIO_MINIMO)
    painel['salario_sm'] = painel['salario_medio_adm'] / painel['sm_ano']
    painel['ln_salario_sm'] = np.log(painel['salario_sm'].clip(lower=0.1))

    # ══════════════════════════════════════════════════════════════
    # PASSO 4: Grande grupo ocupacional
    # ══════════════════════════════════════════════════════════════
    painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]
    painel['grande_grupo_nome'] = painel['grande_grupo_cbo'].map(GRANDES_GRUPOS_CBO)

    # ══════════════════════════════════════════════════════════════
    # PASSO 5: Selecionar colunas finais
    # ══════════════════════════════════════════════════════════════
    cols_finais = [
        # Identificação
        'cbo_4d', 'cbo_2d', 'ano', 'mes', 'periodo', 'periodo_num',
        # Outcomes
        'admissoes', 'desligamentos', 'saldo', 'n_movimentacoes',
        'ln_admissoes', 'ln_desligamentos',
        'salario_medio_adm', 'salario_mediano_adm', 'salario_medio_desl',
        'ln_salario_adm', 'salario_sm', 'ln_salario_sm',
        # Demografia das admissões
        'idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm',
        'pct_branca_adm', 'pct_preta_adm', 'pct_parda_adm', 'pct_negra_adm',
        'pct_amarela_adm', 'pct_indigena_adm', 'pct_raca_nao_informada_adm',
        # Exposição IA — DUAL
        'exposure_score_2d',   # PRINCIPAL
        'exposure_score_4d',   # ROBUSTEZ
        'exposure_score_mte_2d', 'exposure_score_mte_4d',
        'exposure_score_2d_old', 'exposure_score_4d_old',
        'match_level_2d_old', 'match_level_4d_old',
        'mte_match_status', 'mte_cache_statuses',
        'mte_ciuo88_codes', 'mte_target_isco08_codes', 'mte_target_isco08_2d_codes',
        'mte_cbo2002_6d_codes', 'mte_cbo94_codes',
        'crosswalk_spec',
        # Tratamento — DUAL
        'alta_exp',            # Top 20% score 2d (PRINCIPAL)
        'alta_exp_10', 'alta_exp_25', 'alta_exp_mediana', 'quintil_exp',
        'alta_exp_4d',         # Top 20% score 4d (ROBUSTEZ)
        # Temporal
        'post', 'did', 'did_4d', 'tempo_relativo_meses', 'trend', 'mes_do_ano',
        # Classificação
        'grande_grupo_cbo', 'grande_grupo_nome',
    ]

    cols_existentes = [c for c in cols_finais if c in painel.columns]
    cols_faltantes = [c for c in cols_finais if c not in painel.columns]
    if cols_faltantes:
        print(f"\n  AVISO: Colunas não encontradas: {cols_faltantes}")

    painel_final = painel[cols_existentes].copy()
    validate_pct_mulher_adm(painel_final, "painel_final before filtering")
    validate_raca_cor_adm(painel_final, "painel_final before filtering")

    # ══════════════════════════════════════════════════════════════
    # PASSO 6: Remover ocupações sem score principal (2d)
    # ══════════════════════════════════════════════════════════════
    n_antes = len(painel_final)
    painel_final = painel_final[painel_final['exposure_score_2d'].notna()]
    n_depois = len(painel_final)
    if n_antes > n_depois:
        print(f"  Removidas {n_antes - n_depois:,} linhas sem exposure_score_2d "
              f"({(n_antes - n_depois) / n_antes:.1%})")
    validate_pct_mulher_adm(painel_final, str(PAINEL_FINAL_PARQUET))
    validate_raca_cor_adm(painel_final, str(PAINEL_FINAL_PARQUET))

    if "crosswalk_spec" not in painel_final.columns or set(painel_final["crosswalk_spec"].dropna().unique()) != {CROSSWALK_SPEC}:
        raise ValueError(f"Painel final não está na especificação esperada: {CROSSWALK_SPEC}")

    for col in ['alta_exp', 'alta_exp_10', 'alta_exp_25', 'alta_exp_mediana', 'alta_exp_4d', 'did', 'did_4d']:
        if col in painel_final.columns:
            painel_final[col] = painel_final[col].astype(int)

    matched_cbo = painel_final['cbo_4d'].nunique()
    if matched_cbo != EXPECTED_MTE_MATCHED_CODES:
        raise ValueError(
            f"Número inesperado de CBOs com match MTE no painel final: "
            f"{matched_cbo} != {EXPECTED_MTE_MATCHED_CODES}"
        )

    # ══════════════════════════════════════════════════════════════
    # PASSO 7: Salvar
    # ══════════════════════════════════════════════════════════════
    painel_final.to_parquet(PAINEL_FINAL_PARQUET, index=False)
    painel_final.to_csv(PAINEL_FINAL_CSV, index=False)

    # ══════════════════════════════════════════════════════════════
    # RESUMO FINAL
    # ══════════════════════════════════════════════════════════════
    n_com_4d = painel_final['exposure_score_4d'].notna().sum()

    print(f"\n{'=' * 60}")
    print("DATASET ANALÍTICO FINAL — ETAPA 2a")
    print(f"{'=' * 60}")
    print(f"  Observações:        {len(painel_final):,}")
    print(f"  Ocupações (CBO 4d): {painel_final['cbo_4d'].nunique()}")
    print(f"  Períodos:           {painel_final['periodo'].nunique()} meses")
    print(f"    Pré-tratamento:   {painel_final[painel_final['post']==0]['periodo'].nunique()}")
    print(f"    Pós-tratamento:   {painel_final[painel_final['post']==1]['periodo'].nunique()}")
    print(f"  Cobertura 2d:       {painel_final['exposure_score_2d'].notna().mean():.1%}")
    print(f"  Cobertura 4d:       {n_com_4d / len(painel_final):.1%}")
    print(f"  Tratamento 2d:      {painel_final['alta_exp'].mean():.1%} das obs")
    print(f"  Tratamento 4d:      {painel_final['alta_exp_4d'].mean():.1%} das obs")
    print(f"  Crosswalk:          {CROSSWALK_SPEC}")
    print(f"  Colunas:            {painel_final.shape[1]}")
    print(f"\n  Salvo em:")
    print(f"    {PAINEL_FINAL_PARQUET}")
    print(f"    {PAINEL_FINAL_CSV}")
    pq_mb = PAINEL_FINAL_PARQUET.stat().st_size / 1e6
    csv_mb = PAINEL_FINAL_CSV.stat().st_size / 1e6
    print(f"    Tamanho: {pq_mb:.1f} MB (parquet), {csv_mb:.1f} MB (csv)")

    print(f"\n  Info:")
    painel_final.info()

    return painel_final


# if __name__ == "__main__":
#     painel = main()


# # =============================================================================
# # MAIN
# # =============================================================================

def main():
    print("=" * 60)
    print("ETAPA 2a — Pipeline Completo: CAGED + ILO")
    print("=" * 60)
    print(f"  ROOT: {REPO_ROOT}")
    print(f"  DATA: {DATA_OUTPUT}")

    raw_ready = all((DATA_RAW / f"caged_{ano}.parquet").exists() for ano in range(ANO_INICIO, ANO_FIM + 1))
    if raw_ready:
        print(f"\n[1/9] step_01... cache CAGED raw encontrado; pulando download.")
        print(f"\n[2/9] step_02... cache CAGED raw encontrado; pulando verificação pesada.")
    else:
        print(f"\n[1/9] step_01..."); step_01()
        print(f"\n[2/9] step_02..."); step_02()

    if PAINEL_MENSAL_FILE.exists() and not monthly_panel_cache_is_stale():
        print(f"\n[3/9] step_03... cache mensal encontrado ({PAINEL_MENSAL_FILE.name}); pulando agregação.")
    else:
        print(f"\n[3/9] step_03..."); step_03()
    print(f"\n[4/9] step_04..."); step_04()
    print(f"\n[5/9] step_05..."); step_05()
    print(f"\n[6/9] step_06..."); step_06()
    print(f"\n[7/9] step_07..."); step_07()
    print(f"\n[8/9] step_08..."); step_08()
    print(f"\n[9/9] step_09..."); step_09()

    print("\n" + "=" * 60)
    print("ETAPA 2a CONCLUÍDA")
    print("=" * 60)


if __name__ == "__main__":
    main()
