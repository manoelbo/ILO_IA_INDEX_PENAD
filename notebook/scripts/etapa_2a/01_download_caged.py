"""
Script 01: Download dos microdados CAGED via BigQuery
Entrada: Query BigQuery (basedosdados.br_me_caged.microdados_movimentacao)
Saída:   data/raw/caged_{ano}.parquet (por ano)

Duas estratégias de download disponíveis:
  ESTRATÉGIA A (RÁPIDA — recomendada): Usa google-cloud-bigquery com Storage API
    (download paralelo via gRPC/Arrow). ~10x mais rápido que basedosdados.
  ESTRATÉGIA B (FALLBACK): Usa basedosdados (REST API). Mais lento, mas funcional.

O script SEMPRE verifica se o parquet já existe antes de baixar.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE ESTRATÉGIA
# ═══════════════════════════════════════════════════════════════════════════
# Trocar para "B" se a estratégia A falhar
ESTRATEGIA = "A"  # "A" = google-cloud-bigquery + bqstorage (rápido)
                   # "B" = basedosdados (lento, fallback)

# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════

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

def main():
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


if __name__ == "__main__":
    df = main()
