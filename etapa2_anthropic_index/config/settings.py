"""
Configurações do projeto Etapa 2 - Índice Anthropic
"""
from pathlib import Path

# Diretórios
ROOT_DIR = Path(__file__).parent.parent
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
OUTPUTS_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUTS_FIGURES = ROOT_DIR / "outputs" / "figures"
OUTPUTS_LOGS = ROOT_DIR / "outputs" / "logs"

# Criar diretórios
for d in [DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

# Dados Anthropic (release 2025-03-27)
# O ROOT_DIR é etapa2_anthropic_index, o EconomicIndex está no nível acima
ANTHROPIC_DATA_DIR = ROOT_DIR.parent / "EconomicIndex" / "release_2025_03_27"
ANTHROPIC_TASKS_FILE = ANTHROPIC_DATA_DIR / "automation_vs_augmentation_by_task.csv"
ONET_STATEMENTS_FILE = ANTHROPIC_DATA_DIR / "onet_task_statements.csv"

# Colunas de padrões de colaboração
AUTOMATION_COLS = ['directive', 'feedback_loop']
AUGMENTATION_COLS = ['validation', 'task_iteration', 'learning']
