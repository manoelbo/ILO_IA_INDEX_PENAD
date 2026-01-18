"""
Configurações globais do projeto Etapa 1
"""
import os
from pathlib import Path

# Diretórios
ROOT_DIR = Path(__file__).parent.parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
OUTPUTS_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUTS_FIGURES = ROOT_DIR / "outputs" / "figures"
OUTPUTS_LOGS = ROOT_DIR / "outputs" / "logs"

# Criar diretórios se não existirem
for dir_path in [DATA_RAW, DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Google Cloud
GCP_PROJECT_ID = "mestrado-pnad-2026"

# PNAD
PNAD_ANO = 2025
PNAD_TRIMESTRE = 3

# ILO
ILO_FILE = DATA_RAW / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"
ILO_URL = "https://github.com/pgmyrek/2025_GenAI_scores_ISCO08/raw/main/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"

# Mapeamentos
REGIAO_MAP = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte', 
    'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste',
    'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste'
}

GRANDES_GRUPOS = {
    '1': 'Dirigentes e gerentes',
    '2': 'Profissionais das ciências',
    '3': 'Técnicos nível médio',
    '4': 'Apoio administrativo',
    '5': 'Serviços e vendedores',
    '6': 'Agropecuária qualificada',
    '7': 'Indústria qualificada',
    '8': 'Operadores de máquinas',
    '9': 'Ocupações elementares'
}

# Mapeamentos PNAD (códigos como string)
RACA_MAP = {
    '1': 'Branca',
    '2': 'Preta',
    '3': 'Amarela',
    '4': 'Parda',
    '5': 'Indígena',
    '9': 'Outras'  # Sem declaração
}

# Agregação de raça
RACA_AGREGADA_MAP = {
    '1': 'Branca',
    '2': 'Negra',  # Preta
    '4': 'Negra',  # Parda
    '3': 'Outras',  # Amarela
    '5': 'Outras',  # Indígena
    '9': 'Outras'   # Sem declaração
}

# Posições de ocupação formal (strings)
POSICAO_FORMAL = ['1', '3', '5']  # Empregado c/ carteira, Militar, Empregador

# Faixas etárias
IDADE_BINS = [0, 25, 35, 45, 55, 100]
IDADE_LABELS = ['18-24', '25-34', '35-44', '45-54', '55+']
