import os
from pathlib import Path

# Caminhos Base
ROOT_DIR = Path(__file__).parent.parent.parent
ETAPA3_DIR = ROOT_DIR / "etapa3_crosswalk_onet_isco08"
ETAPA2_OUTPUTS = ROOT_DIR / "etapa2_anthropic_index" / "outputs"
ETAPA1_RAW = ROOT_DIR / "etapa1_ia_generativa" / "data" / "raw"

# Inputs de Dados
DATA_INPUT = ETAPA3_DIR / "data_input"
CROSSWALK_SOC_10_18 = DATA_INPUT / "Crosswalk SOC 2010 a 2018.xlsx"
CROSSWALK_SOC_ISCO = DATA_INPUT / "Crosswalk SOC 2010 ISCO-08.xls"
ANTHROPIC_INDEX_ONET = ETAPA2_OUTPUTS / "onet_automation_augmentation_index.csv"
COD_STRUCTURE = ETAPA1_RAW / "Estrutura Ocupação COD.xls"

# Dados Processados e Outputs
DATA_PROCESSED = ETAPA3_DIR / "data" / "processed"
OUTPUTS_TABLES = ETAPA3_DIR / "outputs"
OUTPUTS_LOGS = ETAPA3_DIR / "outputs" / "logs"

# Criar pastas se não existirem
for path in [DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_LOGS]:
    path.mkdir(parents=True, exist_ok=True)

# Configurações de Crosswalk
# Nota: Os arquivos Excel têm cabeçalhos que precisam ser pulados (skiprows=6 como visto na inspeção)
SKIP_ROWS_EXCEL = 6
