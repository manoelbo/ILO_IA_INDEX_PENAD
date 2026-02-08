import os
from pathlib import Path

# Caminhos Base
ROOT_DIR = Path(__file__).parent.parent.parent
ETAPA2_DIR = ROOT_DIR / "etapa2_anthropic_index"
ECONOMIC_INDEX_DIR = ROOT_DIR / "EconomicIndex" / "release_2026_01_15"

# Dados de Entrada (V4 - Jan 2026)
DATA_INPUT = ECONOMIC_INDEX_DIR / "data" / "intermediate"
CLAUDE_AI_RAW = DATA_INPUT / "aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv"
API_1P_RAW = DATA_INPUT / "aei_raw_1p_api_2025-11-13_to_2025-11-20.csv"

# Dados O*NET / SOC (usando os mais recentes do repo)
ONET_SOC_DATA = ROOT_DIR / "EconomicIndex" / "release_2025_09_15" / "data" / "intermediate"
ONET_TASK_STATEMENTS = ONET_SOC_DATA / "onet_task_statements.csv"
SOC_STRUCTURE = ONET_SOC_DATA / "soc_structure.csv"

# Dados Processados
DATA_PROCESSED = ETAPA2_DIR / "data" / "processed"
OUTPUTS_TABLES = ETAPA2_DIR / "outputs"
OUTPUTS_LOGS = ETAPA2_DIR / "outputs" / "logs"

# Criar pastas se não existirem
for path in [DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_LOGS]:
    path.mkdir(parents=True, exist_ok=True)

# Definições Metodológicas Anthropic
# Automation: Modos focado em tarefa direta (delegada)
AUTOMATION_MODES = ["directive", "feedback loop"]

# Augmentation: Modos focados em colaboração, aprendizado e refinamento
AUGMENTATION_MODES = ["learning", "task iteration", "validation"]

# Configurações de Agregação
MIN_TASK_COUNT = 15  # Filtro de privacidade/estabilidade da Anthropic
DEFAULT_PLATFORM = "Claude AI (Free and Pro)"
