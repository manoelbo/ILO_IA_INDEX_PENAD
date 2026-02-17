"""
Configuração compartilhada — Etapa 3b (Análise Triple-DiD)
"""

import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*dropped due to multicollinearity.*", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NOTEBOOK_DIR = REPO_ROOT / "notebook"

DATA_OUTPUT = NOTEBOOK_DIR / "data" / "output"
OUTPUTS_TABLES = NOTEBOOK_DIR / "outputs" / "tables"
OUTPUTS_FIGURES = NOTEBOOK_DIR / "outputs" / "figures"
OUTPUTS_LOGS = NOTEBOOK_DIR / "outputs" / "logs"

for d in [DATA_OUTPUT, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

PAINEL_3A_FILE = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"

# Triple-DiD: cluster por município
CLUSTER_VAR = "id_municipio"
VCOV_SPEC = {"CRV1": "id_municipio"}
REFERENCE_PERIOD = -1
BIN_MIN, BIN_MAX = -12, 24
ANO_TRATAMENTO, MES_TRATAMENTO = 2022, 12

OUTCOMES = {
    "ln_salario_real_adm": "Log(Salário Real Admissão)",
    "ln_admissoes": "Log(Admissões)",
    "ln_desligamentos": "Log(Desligamentos)",
    "saldo": "Saldo Líquido",
    "pct_superior_adm": "% Superior (Admissão)",
    "idade_media_adm": "Idade Média Admissão",
    "ln_salario_mulher": "Log(Salário Mulheres)",
    "ln_salario_homem": "Log(Salário Homens)",
    "ln_salario_jovem": "Log(Salário Jovens)",
}

COLORS = {"pre": "#1f77b4", "post": "#d62728", "ci": "#cccccc", "treated": "#ff7f0e", "control": "#2ca02c"}


def print_config():
    print("=" * 60)
    print("CONFIGURAÇÃO — Etapa 3b (Triple-DiD)")
    print("=" * 60)
    print(f"  Painel 3a: {PAINEL_3A_FILE} (existe: {PAINEL_3A_FILE.exists()})")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
