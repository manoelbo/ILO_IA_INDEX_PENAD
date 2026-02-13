import os
from pathlib import Path

# Caminhos Base
ROOT_DIR = Path(__file__).parent.parent.parent
ETAPA4_DIR = ROOT_DIR / "etapa4_automation_augmentation_analysis"
ETAPA1_DATA = ROOT_DIR / "etapa1_ia_generativa" / "data" / "processed"
ETAPA3_DATA = ROOT_DIR / "etapa3_crosswalk_onet_isco08" / "outputs"
ETAPA1_RAW = ROOT_DIR / "etapa1_ia_generativa" / "data" / "raw"

# Inputs de Dados
PNAD_ILO_MERGED = ETAPA1_DATA / "pnad_ilo_merged.csv"
ANTHROPIC_INDICES = ETAPA3_DATA / "cod_automation_augmentation_index_final.csv"
COD_STRUCTURE = ETAPA1_RAW / "Estrutura Ocupação COD.xls"

# Dados Processados e Outputs
DATA_PROCESSED = ETAPA4_DIR / "data" / "processed"
OUTPUTS_TABLES = ETAPA4_DIR / "outputs" / "tables"
OUTPUTS_FIGURES = ETAPA4_DIR / "outputs" / "figures"
OUTPUTS_REPORTS = ETAPA4_DIR / "outputs" / "reports"
OUTPUTS_LOGS = ETAPA4_DIR / "outputs" / "logs"

# Criar pastas se não existirem
for path in [DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_REPORTS, OUTPUTS_LOGS]:
    path.mkdir(parents=True, exist_ok=True)

# Definições de Grupos Ocupacionais (COD)
GRANDES_GRUPOS = {
    '1': 'Diretores e Gerentes',
    '2': 'Profissionais das Ciências e Intelectuais',
    '3': 'Técnicos e Profissionais de Nível Médio',
    '4': 'Trabalhadores de Apoio Administrativo',
    '5': 'Trabalhadores dos Serviços e Vendedores',
    '6': 'Agricultores e Trabalhadores Florestais',
    '7': 'Trabalhadores da Indústria e Construção',
    '8': 'Operadores de Máquinas e Montadores',
    '9': 'Ocupações Elementares',
    '0': 'Membros das Forças Armadas e Polícia'
}
