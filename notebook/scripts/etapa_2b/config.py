"""
Configuração compartilhada — Etapa 2b (Análise DiD)
Caminhos, parâmetros de estimação e constantes usadas por todos os scripts.
"""

import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
# Suprimir aviso do pyfixest quando variável é omitida por colinearidade (ex.: pct_mulher_adm)
warnings.filterwarnings("ignore", message=".*dropped due to multicollinearity.*", category=UserWarning)

# ---------------------------------------------------------------------------
# Caminhos (relativos à raiz do repositório)
# ---------------------------------------------------------------------------
# Raiz: scripts/etapa_2b/config.py → etapa_2b → scripts → notebook → repo
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NOTEBOOK_DIR = REPO_ROOT / "notebook"

DATA_OUTPUT = NOTEBOOK_DIR / "data" / "output"
OUTPUTS_TABLES = NOTEBOOK_DIR / "outputs" / "tables"
OUTPUTS_FIGURES = NOTEBOOK_DIR / "outputs" / "figures"
OUTPUTS_LOGS = NOTEBOOK_DIR / "outputs" / "logs"

for d in [DATA_OUTPUT, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

# Arquivos de dados
PAINEL_2A_FILE = DATA_OUTPUT / "painel_caged_did_ready.parquet"
PAINEL_2B_FILE = DATA_OUTPUT / "painel_2b_ready.parquet"

# ---------------------------------------------------------------------------
# Parâmetros de estimação DiD
# ---------------------------------------------------------------------------
TREATMENT_VAR = "alta_exp"  # Especificação principal (top 20%, 2d)
TREATMENT_VAR_4D = "alta_exp_4d"  # Robustez (top 20%, 4d)
CLUSTER_VAR = "cbo_4d"  # Cluster de erros padrão
VCOV_SPEC = {"CRV1": "cbo_4d"}  # Cluster-robust (CRV1)
REFERENCE_PERIOD = -1  # Mês t=-1 como referência no event study
ALPHA = 0.05  # Nível de significância

# Evento: lançamento do ChatGPT (Nov/2022), pós a partir de Dez/2022
ANO_TRATAMENTO = 2022
MES_TRATAMENTO = 12

# Scores contínuos para tratamento contínuo
EXPOSURE_SCORE_MAIN = "exposure_score_2d"
EXPOSURE_SCORE_4D = "exposure_score_4d"

# Outcomes principais
OUTCOMES = {
    "ln_admissoes": "Log(Admissões)",
    "ln_desligamentos": "Log(Desligamentos)",
    "saldo": "Saldo Líquido",
    "ln_salario_adm": "Log(Salário Admissão)",
    # Heterogeneidade demográfica (salários por grupo)
    "ln_salario_mulher": "Log(Salário Mulheres)",
    "ln_salario_homem": "Log(Salário Homens)",
    "ln_salario_jovem": "Log(Salário Jovens)",
    "ln_salario_naojovem": "Log(Salário Não-Jovens)",
    "ln_salario_branco": "Log(Salário Brancos)",
    "ln_salario_negro": "Log(Salário Negros)",
    "ln_salario_superior": "Log(Salário Superior)",
    "ln_salario_medio": "Log(Salário Médio)",
    # Heterogeneidade: volumes
    "ln_admissoes_mulher": "Log(Admissões Mulheres)",
    "ln_admissoes_homem": "Log(Admissões Homens)",
    "ln_admissoes_jovem": "Log(Admissões Jovens)",
    "ln_admissoes_negro": "Log(Admissões Negros)",
}

# Outcomes secundários
OUTCOMES_SECONDARY = {
    "ln_salario_sm": "Log(Salário em SM)",
}

# Event study: binning dos extremos
BIN_MIN = -12  # Agrupar t <= -12 no pré
BIN_MAX = 24   # Agrupar t >= 24 no pós

# Placebo temporal (Teste 2 de robustez)
PLACEBO_ANO = 2021
PLACEBO_MES = 12

# Cores para gráficos
COLORS = {
    "pre": "#1f77b4",
    "post": "#d62728",
    "ci": "#cccccc",
    "treated": "#ff7f0e",
    "control": "#2ca02c",
}


def print_config():
    """Imprime a configuração atual."""
    print("=" * 60)
    print("CONFIGURAÇÃO — Etapa 2b (Análise DiD)")
    print("=" * 60)
    print(f"  Repo root:      {REPO_ROOT}")
    print(f"  Notebook dir:   {NOTEBOOK_DIR}")
    print(f"  Data output:    {DATA_OUTPUT}")
    print(f"  Outputs tables: {OUTPUTS_TABLES}")
    print(f"  Outputs figures:{OUTPUTS_FIGURES}")
    print(f"  Evento:         ChatGPT — Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
    print(f"  Painel 2a:      {PAINEL_2A_FILE} (existe: {PAINEL_2A_FILE.exists()})")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
