"""
Configurações globais do projeto Etapa 5 - DiD Ocupacional
Análise do impacto da IA Generativa no mercado de trabalho brasileiro
"""
import os
from pathlib import Path

# Diretórios
ROOT_DIR = Path(__file__).parent.parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
DATA_EXTERNAL = ROOT_DIR / "data" / "external"
OUTPUTS_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUTS_FIGURES = ROOT_DIR / "outputs" / "figures"
OUTPUTS_LOGS = ROOT_DIR / "outputs" / "logs"

# Criar diretórios se não existirem
for dir_path in [DATA_RAW, DATA_PROCESSED, DATA_EXTERNAL, OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================
# GOOGLE CLOUD
# ============================================
GCP_PROJECT_ID = "mestrado-pnad-2026"

# ============================================
# DID TEMPORAL CONFIGURATION
# ============================================

# Todos os trimestres para download (16 total)
QUARTERS = [(ano, tri) for ano in range(2021, 2025) for tri in range(1, 5)]

# Períodos críticos para DiD
PERIODO_REFERENCIA = 20224  # 2022Q4 (último trimestre antes do ChatGPT)
PERIODO_TRATAMENTO = 20231  # 2023Q1 (primeiro trimestre pós-ChatGPT)

# Data de lançamento do ChatGPT para referência
CHATGPT_LAUNCH_DATE = "2022-11-30"

# ============================================
# PNAD VARIABLES
# ============================================

# Variáveis a serem baixadas do BigQuery
PNAD_VARS = [
    # Identificação
    'ano', 'trimestre', 'sigla_uf',

    # Demográficas
    'v2007',  # sexo
    'v2009',  # idade
    'v2010',  # raca

    # Educação
    'vd3004',  # nivel_instrucao
    'vd3005',  # anos_estudo

    # Trabalho
    'v4010',   # cod_ocupacao (4 dígitos COD)
    'vd4002',  # condicao_ocupacao (ocupado/desocupado)
    'vd4008',  # posicao_ocupacao
    'vd4009',  # tipo_vinculo (formal/informal)
    'vd4016',  # rendimento_habitual
    'vd4035',  # horas_trabalhadas

    # Peso amostral
    'v1028'    # peso
]

# ============================================
# EXPOSURE INDEX
# ============================================

# Caminho para o índice de exposição (etapa3 com imputação hierárquica)
COD_EXPOSURE_PATH = Path("etapa3_crosswalk_onet_isco08/outputs/cod_automation_augmentation_index_final.csv")

# Nome da coluna de exposição principal (será renomeada para exposure_score)
EXPOSURE_COLUMN = 'automation_index_cai'

# ============================================
# TREATMENT DEFINITION
# ============================================

# Thresholds de percentil para definição de tratamento
# Serão computados no período pré-tratamento com pesos populacionais
PERCENTILE_THRESHOLDS = {
    'alta_exp_10': 0.90,  # Top 10%
    'alta_exp_20': 0.80,  # Top 20% (especificação principal)
    'alta_exp_25': 0.75,  # Top 25%
}

# Especificação principal
MAIN_TREATMENT = 'alta_exp_20'

# ============================================
# MAPPINGS - Reusados da etapa1
# ============================================

# Mapeamento de UF para Região
REGIAO_MAP = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte',
    'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste',
    'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste'
}

# Grandes grupos ocupacionais (primeiro dígito do COD/ISCO-08)
GRANDES_GRUPOS = {
    '1': 'Dirigentes e gerentes',
    '2': 'Profissionais das ciências',
    '3': 'Técnicos nível médio',
    '4': 'Apoio administrativo',
    '5': 'Serviços e vendedores',
    '6': 'Agropecuária qualificada',
    '7': 'Indústria qualificada',
    '8': 'Operadores de máquinas',
    '9': 'Ocupações elementares',
    '0': 'Forças armadas'
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

# Agregação de raça (Negro = Preta + Parda)
RACA_AGREGADA_MAP = {
    '1': 'Branca',
    '2': 'Negra',  # Preta
    '4': 'Negra',  # Parda
    '3': 'Outras',  # Amarela
    '5': 'Outras',  # Indígena
    '9': 'Outras'   # Sem declaração
}

# Posições de ocupação formal (strings)
# VD4009: 01=Empregado c/ carteira, 02=Militar, 03=Estatutário, 04=Empregador
POSICAO_FORMAL = ['01', '02', '03', '04']

# Faixas etárias para análise
IDADE_BINS = [18, 25, 30, 40, 50, 65]
IDADE_LABELS = ['18-25', '26-30', '31-40', '41-50', '51-65']

# Definição de jovem (para heterogeneidade)
IDADE_JOVEM = 30  # idade <= 30
IDADE_JOVEM_ESTRITO = (22, 25)  # Brynjolfsson specification

# ============================================
# OUTCOME VARIABLES
# ============================================

# Variáveis dependentes para análise DiD
OUTCOMES = ['ocupado', 'formal', 'ln_renda', 'horas_trabalhadas', 'informal']

# Controles demográficos
DEMOGRAPHICS = ['mulher', 'negro_pardo', 'jovem', 'superior', 'medio']

# ============================================
# VALIDATION PARAMETERS
# ============================================

# Mínimo de observações por trimestre
MIN_OBS_PER_QUARTER = 150000

# Número de UFs esperadas
N_UFS = 27

# Cobertura mínima de exposição (ponderada pela população)
MIN_EXPOSURE_COVERAGE = 0.95

# Threshold para desbalanceamento de covariáveis (standardized difference)
BALANCE_THRESHOLD = 0.25

# ============================================
# PLOTTING PARAMETERS
# ============================================

# Cores para gráficos
COLOR_TREATMENT = '#e74c3c'  # Vermelho para grupo de tratamento
COLOR_CONTROL = '#2ecc71'    # Verde para grupo de controle
COLOR_PRE = '#3498db'        # Azul para período pré
COLOR_POST = '#e74c3c'       # Vermelho para período pós

# Estilo de gráficos
PLOT_STYLE = 'seaborn-v0_8-whitegrid'
FIGURE_DPI = 200

# ============================================
# PHASE 4: REGRESSION ANALYSIS
# ============================================

# Outcomes válidos para regressão (excluindo formal/ocupado devido a zero variância)
OUTCOMES_VALID = ['ln_renda', 'horas_trabalhadas', 'informal']

# Período de referência para Event Study (último pré-tratamento)
EVENT_STUDY_REFERENCE = '2022T4'

# Grupos demográficos para análise de heterogeneidade
HETEROGENEITY_GROUPS = {
    'age': 'jovem',        # idade <= 30 anos
    'gender': 'mulher',    # mulher vs. homem
    'education': 'superior',  # superior completo vs. não
    'race': 'negro_pardo'  # negro/pardo vs. outros
}

# Períodos para testes de placebo (tratamento fictício)
PLACEBO_PERIODS = ['2021T4', '2022T2']

# Cutoffs alternativos para robustez (variáveis já criadas na Fase 3)
ROBUSTNESS_CUTOFFS = ['alta_exp_10', 'alta_exp', 'alta_exp_25', 'exposure_score']

# Thresholds para plausibilidade de efeitos (flag warnings se excedido)
PLAUSIBILITY_THRESHOLDS = {
    'ln_renda': 0.30,           # 35% mudança na renda
    'horas_trabalhadas': 10.0,  # 10 horas por semana
    'ocupado': 0.20,            # 20 pontos percentuais
    'formal': 0.20,
    'informal': 0.20
}

# Mínimo de clusters para CRV1 (cluster-robust standard errors)
MIN_CLUSTERS = 50
