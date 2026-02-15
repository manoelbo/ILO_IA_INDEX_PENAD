"""
Configuração compartilhada — Etapa 2a
Caminhos, parâmetros e constantes usadas por todos os scripts.
"""

import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos (relativos à raiz do repositório)
# ---------------------------------------------------------------------------
# Raiz do repositório (3 níveis acima: scripts/etapa_2a/config.py → notebook → repo)
REPO_ROOT      = Path(__file__).resolve().parent.parent.parent.parent
NOTEBOOK_DIR   = REPO_ROOT / "notebook"

DATA_INPUT     = NOTEBOOK_DIR / "data" / "input"
DATA_RAW       = NOTEBOOK_DIR / "data" / "raw"
DATA_PROCESSED = NOTEBOOK_DIR / "data" / "processed"
DATA_OUTPUT    = NOTEBOOK_DIR / "data" / "output"

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
ISCO_08_88_FILE = DATA_INPUT / "Correspondência ISCO 08 a 88.xlsx"

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
PAINEL_TRATAMENTO_FILE = DATA_PROCESSED / "painel_caged_tratamento.parquet"
PAINEL_FINAL_PARQUET = DATA_OUTPUT / "painel_caged_did_ready.parquet"
PAINEL_FINAL_CSV     = DATA_OUTPUT / "painel_caged_did_ready.csv"

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
    print(f"  Notebook dir: {NOTEBOOK_DIR}")
    print(f"  Período:      {ANO_INICIO}–{ANO_FIM} ({(ANO_FIM - ANO_INICIO + 1) * 12} meses)")
    print(f"  Evento:       ChatGPT — Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
    print(f"  Projeto GCP:  {GCP_PROJECT_ID}")
    print(f"  ILO file:     {ILO_FILE} (existe: {ILO_FILE.exists()})")
    print(f"  Data input:   {DATA_INPUT}")
    print(f"  Data raw:     {DATA_RAW}")
    print(f"  Data processed: {DATA_PROCESSED}")
    print(f"  Data output:  {DATA_OUTPUT}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
