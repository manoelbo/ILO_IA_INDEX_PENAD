"""
Configuração compartilhada — Etapa 3a
Preparação do painel CAGED × Município × Conectividade (Anatel).
"""

import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos (scripts/etapa_3a/config.py → notebook → repo)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NOTEBOOK_DIR = REPO_ROOT / "notebook"

DATA_INPUT = NOTEBOOK_DIR / "data" / "input"
DATA_RAW = NOTEBOOK_DIR / "data" / "raw"
DATA_PROCESSED = NOTEBOOK_DIR / "data" / "processed"
DATA_OUTPUT = NOTEBOOK_DIR / "data" / "output"

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
CONECTIVIDADE_CSV = NOTEBOOK_DIR / "outputs" / "tables" / "conectividade_municipal.csv"

# Outputs/tables (para CSV de conectividade)
OUTPUTS_TABLES = NOTEBOOK_DIR / "outputs" / "tables"
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)


def print_config():
    """Imprime a configuração atual."""
    print("=" * 60)
    print("CONFIGURAÇÃO — Etapa 3a")
    print("=" * 60)
    print(f"  Notebook dir: {NOTEBOOK_DIR}")
    print(f"  Período:      {ANO_INICIO}–{ANO_FIM}")
    print(f"  Evento:       Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
    print(f"  Pré conect.:  até {MES_FIM_PRE_CONECT}/{ANO_PRE_CONECT}")
    print(f"  MIN_POPULACAO: {MIN_POPULACAO:,}")
    print(f"  MIN_MOVIMENTACOES_PRE: {MIN_MOVIMENTACOES_PRE}")
    print(f"  Painel final: {PAINEL_FINAL_PARQUET.name}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
