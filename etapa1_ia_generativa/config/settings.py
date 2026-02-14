"""
Configurações globais do projeto Etapa 1
"""
import os
from pathlib import Path

# Diretórios
ROOT_DIR = Path(__file__).parent.parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
DATA_OUTPUT = ROOT_DIR / "data" / "output"
OUTPUTS_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUTS_FIGURES = ROOT_DIR / "outputs" / "figures"
OUTPUTS_LOGS = ROOT_DIR / "outputs" / "logs"

# Criar diretórios se não existirem
for dir_path in [DATA_RAW, DATA_PROCESSED, DATA_OUTPUT, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Google Cloud
GCP_PROJECT_ID = "mestrado-pnad-2026"

# PNAD
PNAD_ANO = 2025
PNAD_TRIMESTRE = 3
SALARIO_MINIMO = 1518  # Valor vigente em Q3/2025 (R$)

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

# ---------------------------------------------------------------------------
# Mapeamento CNAE Domiciliar 2.0 → Setor agregado
# Seções A-T conforme classificação oficial IBGE.
# Fonte: IBGE, Classificação Nacional de Atividades Econômicas (CNAE 2.0)
# ---------------------------------------------------------------------------
CNAE_SETOR_MAP = {
    # A - Agropecuária
    '01': 'Agropecuária', '02': 'Agropecuária', '03': 'Agropecuária',
    # B - Indústria Extrativa
    '05': 'Ind. Extrativa', '06': 'Ind. Extrativa', '07': 'Ind. Extrativa',
    '08': 'Ind. Extrativa', '09': 'Ind. Extrativa',
    # C - Indústria de Transformação
    '10': 'Ind. Transformação', '11': 'Ind. Transformação', '12': 'Ind. Transformação',
    '13': 'Ind. Transformação', '14': 'Ind. Transformação', '15': 'Ind. Transformação',
    '16': 'Ind. Transformação', '17': 'Ind. Transformação', '18': 'Ind. Transformação',
    '19': 'Ind. Transformação', '20': 'Ind. Transformação', '21': 'Ind. Transformação',
    '22': 'Ind. Transformação', '23': 'Ind. Transformação', '24': 'Ind. Transformação',
    '25': 'Ind. Transformação', '26': 'Ind. Transformação', '27': 'Ind. Transformação',
    '28': 'Ind. Transformação', '29': 'Ind. Transformação', '30': 'Ind. Transformação',
    '31': 'Ind. Transformação', '32': 'Ind. Transformação', '33': 'Ind. Transformação',
    # D+E - Utilidades (Eletricidade, Gás, Água, Esgoto, Resíduos)
    '35': 'Utilidades', '36': 'Utilidades', '37': 'Utilidades',
    '38': 'Utilidades', '39': 'Utilidades',
    # F - Construção
    '41': 'Construção', '42': 'Construção', '43': 'Construção',
    # G - Comércio
    '45': 'Comércio', '46': 'Comércio', '47': 'Comércio',
    # H - Transporte, Armazenagem e Correio
    '49': 'Transporte', '50': 'Transporte', '51': 'Transporte',
    '52': 'Transporte', '53': 'Transporte',
    # I - Alojamento e Alimentação
    '55': 'Alojamento e Alimentação', '56': 'Alojamento e Alimentação',
    # J - Informação e Comunicação
    '58': 'Informação e Comunicação', '59': 'Informação e Comunicação',
    '60': 'Informação e Comunicação', '61': 'Informação e Comunicação',
    '62': 'Informação e Comunicação', '63': 'Informação e Comunicação',
    # K - Atividades Financeiras
    '64': 'Finanças e Seguros', '65': 'Finanças e Seguros', '66': 'Finanças e Seguros',
    # L - Atividades Imobiliárias
    '68': 'Atividades Imobiliárias',
    # M - Atividades Profissionais, Científicas e Técnicas
    '69': 'Serviços Profissionais', '70': 'Serviços Profissionais',
    '71': 'Serviços Profissionais', '72': 'Serviços Profissionais',
    '73': 'Serviços Profissionais', '74': 'Serviços Profissionais',
    '75': 'Serviços Profissionais',
    # N - Atividades Administrativas e Serviços Complementares
    '77': 'Serviços Administrativos', '78': 'Serviços Administrativos',
    '79': 'Serviços Administrativos', '80': 'Serviços Administrativos',
    '81': 'Serviços Administrativos', '82': 'Serviços Administrativos',
    # O - Administração Pública
    '84': 'Administração Pública',
    # P - Educação
    '85': 'Educação',
    # Q - Saúde Humana e Serviços Sociais
    '86': 'Saúde', '87': 'Saúde', '88': 'Saúde',
    # R - Artes, Cultura, Esporte e Recreação
    '90': 'Artes e Cultura', '91': 'Artes e Cultura',
    '92': 'Artes e Cultura', '93': 'Artes e Cultura',
    # S - Outras Atividades de Serviços
    '94': 'Outros Serviços', '95': 'Outros Serviços', '96': 'Outros Serviços',
    # T - Serviços Domésticos
    '97': 'Serviços Domésticos',
}

# Setores com maior proporção de tarefas expostas à IA generativa
# Ref: Gmyrek et al. (2024); Eloundou et al. (2023)
SETORES_CRITICOS_IA = [
    'Informação e Comunicação',
    'Finanças e Seguros',
    'Serviços Profissionais',
]

# ---------------------------------------------------------------------------
# Constantes para análise (scripts 06-09)
# ---------------------------------------------------------------------------

# Ordem oficial dos gradientes ILO (potential25)
GRADIENT_ORDER = [
    'Not Exposed', 'Minimal Exposure',
    'Exposed: Gradient 1', 'Exposed: Gradient 2',
    'Exposed: Gradient 3', 'Exposed: Gradient 4',
    'Sem classificação',
]

GRADIENT_COLORS = {
    'Not Exposed':          '#2ca02c',
    'Minimal Exposure':     '#98df8a',
    'Exposed: Gradient 1':  '#aec7e8',
    'Exposed: Gradient 2':  '#ffbb78',
    'Exposed: Gradient 3':  '#ff7f0e',
    'Exposed: Gradient 4':  '#d62728',
    'Sem classificação':    '#d9d9d9',
}

GRADIENT_LABELS_PT = {
    'Not Exposed':          'Não Exposto',
    'Minimal Exposure':     'Exposição Mínima',
    'Exposed: Gradient 1':  'Gradiente 1',
    'Exposed: Gradient 2':  'Gradiente 2',
    'Exposed: Gradient 3':  'Gradiente 3',
    'Exposed: Gradient 4':  'Gradiente 4',
    'Sem classificação':    'Sem Classificação',
}

HIGH_EXPOSURE_GRADIENTS = ['Exposed: Gradient 3', 'Exposed: Gradient 4']
QUINTIL_ORDER = ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
DECIL_ORDER = [f'D{i}' for i in range(1, 11)]

NIVEL_INSTRUCAO_MAP = {
    1: 'Sem instrução',
    2: 'Fundamental incompleto',
    3: 'Fundamental completo',
    4: 'Médio incompleto',
    5: 'Médio completo',
    6: 'Superior incompleto',
    7: 'Superior completo',
}
