# PLANNING ETAPA 1 - Implementação de Código

> Guia para implementação no Cursor - Análise Descritiva da Exposição à IA Generativa no Brasil

---

## ESTRUTURA DO PROJETO

```
etapa1_ia_generativa/
│
├── config/
│   └── settings.py              # Configurações e constantes do projeto
│
├── data/
│   ├── raw/                     # Dados brutos (não versionados)
│   │   ├── ilo_scores.xlsx
│   │   └── pnad_2025q3.parquet
│   └── processed/               # Dados processados
│       ├── ilo_exposure_clean.csv
│       ├── pnad_clean.csv
│       └── pnad_ilo_merged.csv
│
├── src/
│   ├── __init__.py
│   ├── 01_download_pnad.py      # Download dados PNAD via BigQuery
│   ├── 02_process_ilo.py        # Processar planilha ILO
│   ├── 03_clean_pnad.py         # Limpeza e variáveis derivadas
│   ├── 04_crosswalk.py          # Correspondência COD-ISCO
│   ├── 05_merge_data.py         # Merge final PNAD + ILO
│   ├── 06_analysis_tables.py    # Geração das 5 tabelas
│   ├── 07_analysis_figures.py   # Geração das 4 figuras
│   └── utils/
│       ├── __init__.py
│       ├── weighted_stats.py    # Funções de estatísticas ponderadas
│       └── validators.py        # Funções de validação
│
├── outputs/
│   ├── tables/                  # Tabelas em CSV e LaTeX
│   │   ├── tabela1_exposicao_grupos.csv
│   │   ├── tabela1_exposicao_grupos.tex
│   │   ├── tabela2_perfil_quintis.csv
│   │   ├── tabela2_perfil_quintis.tex
│   │   ├── tabela3_regiao_setor.csv
│   │   ├── tabela3_regiao_setor.tex
│   │   ├── tabela4_desigualdade.csv
│   │   ├── tabela4_desigualdade.tex
│   │   └── tabela5_comparacao.csv
│   │
│   ├── figures/                 # Gráficos em PNG e PDF
│   │   ├── fig1_distribuicao_exposicao.png
│   │   ├── fig1_distribuicao_exposicao.pdf
│   │   ├── fig2_heatmap_regiao_setor.png
│   │   ├── fig2_heatmap_regiao_setor.pdf
│   │   ├── fig3_renda_exposicao.png
│   │   ├── fig3_renda_exposicao.pdf
│   │   ├── fig4_decomposicao_demografica.png
│   │   └── fig4_decomposicao_demografica.pdf
│   │
│   └── logs/                    # Logs de execução
│       ├── 01_download.log
│       ├── 02_ilo_process.log
│       ├── 03_pnad_clean.log
│       ├── 04_crosswalk.log
│       ├── 05_merge.log
│       ├── 06_tables.log
│       └── 07_figures.log
│
├── tests/                       # Testes de validação
│   ├── test_01_download.py
│   ├── test_02_ilo.py
│   ├── test_03_clean.py
│   ├── test_04_crosswalk.py
│   └── test_05_merge.py
│
├── notebooks/                   # Notebooks exploratórios (opcional)
│   └── exploratory_analysis.ipynb
│
├── RESULTADOS_ETAPA1.md         # Relatório final com análise
├── requirements.txt
└── run_all.py                   # Script master para rodar tudo
```

---

## PARTE 1: CONFIGURAÇÃO GOOGLE CLOUD

### 1.1 Criar Projeto no Google Cloud Console

```
1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto (ex: "dissertacao-ia-br")
3. Anote o PROJECT_ID (vai usar nos scripts)
```

### 1.2 Ativar APIs Necessárias

```
No Cloud Console, ative:
- BigQuery API
- Cloud Storage API (opcional, para cache)
```

### 1.3 Configurar Credenciais

```bash
# Instalar Google Cloud CLI
# Mac: brew install google-cloud-sdk
# Windows: https://cloud.google.com/sdk/docs/install

# Autenticar
gcloud auth login
gcloud auth application-default login

# Definir projeto padrão
gcloud config set project SEU_PROJECT_ID
```

### 1.4 Configurar Billing

```
1. No Cloud Console > Billing
2. Vincule uma conta de faturamento ao projeto
3. IMPORTANTE: BigQuery tem 1TB/mês grátis de queries
4. A query da PNAD usa ~500MB, então está no free tier
```

### 1.5 Testar Conexão

```python
# Executar no Python para validar
import basedosdados as bd

# Teste simples
test = bd.read_sql(
    "SELECT COUNT(*) as n FROM `basedosdados.br_ibge_pnad_continua.microdados` WHERE ano = 2024 LIMIT 1",
    billing_project_id="SEU_PROJECT_ID"
)
print(test)
```

---

## PARTE 2: IMPLEMENTAÇÃO DOS SCRIPTS

### 2.0 config/settings.py

```python
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
GCP_PROJECT_ID = "SEU_PROJECT_ID"  # <-- ALTERAR AQUI

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

RACA_MAP = {
    'Branca': 'Branca',
    'Preta': 'Negra',
    'Parda': 'Negra',
    'Amarela': 'Outras',
    'Indígena': 'Outras'
}

# Faixas etárias
IDADE_BINS = [0, 25, 35, 45, 55, 100]
IDADE_LABELS = ['18-24', '25-34', '35-44', '45-54', '55+']
```

---

### 2.1 src/01_download_pnad.py

```python
"""
Script 01: Download dos microdados PNAD via BigQuery
Entrada: Query BigQuery
Saída: data/raw/pnad_2025q3.parquet
"""

import logging
import basedosdados as bd
import pandas as pd
import sys
sys.path.append('..')
from config.settings import *

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '01_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_pnad():
    """Baixa microdados PNAD do BigQuery"""
    
    logger.info(f"Iniciando download PNAD {PNAD_ANO} Q{PNAD_TRIMESTRE}")
    
    query = f"""
    SELECT 
        ano,
        trimestre,
        sigla_uf,
        v2007 AS sexo,
        v2009 AS idade,
        v2010 AS raca_cor,
        vd3004 AS nivel_instrucao,
        v4010 AS cod_ocupacao,
        v4013 AS grupamento_atividade,
        vd4009 AS posicao_ocupacao,
        vd4020 AS rendimento_habitual,
        vd4016 AS rendimento_todos,
        v4019 AS horas_trabalhadas,
        v1028 AS peso
    FROM `basedosdados.br_ibge_pnad_continua.microdados`
    WHERE ano = {PNAD_ANO} 
        AND trimestre = {PNAD_TRIMESTRE}
        AND v4010 IS NOT NULL
        AND vd4020 > 0
    """
    
    logger.info("Executando query no BigQuery...")
    df = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID)
    
    logger.info(f"Download concluído: {len(df):,} observações")
    logger.info(f"Colunas: {list(df.columns)}")
    
    # Salvar
    output_path = DATA_RAW / f"pnad_{PNAD_ANO}q{PNAD_TRIMESTRE}.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Salvo em: {output_path}")
    
    # Estatísticas básicas
    logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")
    logger.info(f"UFs presentes: {df['sigla_uf'].nunique()}")
    
    return df

if __name__ == "__main__":
    download_pnad()
```

---

### 2.2 src/02_process_ilo.py

```python
"""
Script 02: Processar planilha ILO com scores de exposição
Entrada: data/raw/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx
Saída: data/processed/ilo_exposure_clean.csv
"""

import logging
import pandas as pd
import requests
import sys
sys.path.append('..')
from config.settings import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '02_ilo_process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_ilo_if_needed():
    """Baixa arquivo ILO do GitHub se não existir"""
    if not ILO_FILE.exists():
        logger.info(f"Baixando arquivo ILO de: {ILO_URL}")
        response = requests.get(ILO_URL)
        with open(ILO_FILE, 'wb') as f:
            f.write(response.content)
        logger.info("Download concluído")

def process_ilo():
    """Processa planilha ILO e extrai scores por ocupação"""
    
    download_ilo_if_needed()
    
    logger.info(f"Lendo arquivo: {ILO_FILE}")
    df_raw = pd.read_excel(ILO_FILE)
    
    logger.info(f"Linhas raw (tarefas): {len(df_raw):,}")
    logger.info(f"Colunas disponíveis: {list(df_raw.columns)}")
    
    # Identificar colunas corretas (podem variar ligeiramente)
    # Ajustar conforme estrutura real do arquivo
    col_mapping = {
        'ISCO_08': 'isco_08',
        'Title': 'occupation_title',
        'mean_score_2025': 'exposure_score',
        'SD_2025': 'exposure_sd',
        'potential25': 'exposure_gradient'
    }
    
    # Verificar se colunas existem
    available_cols = [c for c in col_mapping.keys() if c in df_raw.columns]
    logger.info(f"Colunas encontradas: {available_cols}")
    
    # Renomear
    df = df_raw.rename(columns={k: v for k, v in col_mapping.items() if k in df_raw.columns})
    
    # Agregar por ocupação (arquivo tem múltiplas tarefas por ocupação)
    df_agg = df.groupby('isco_08').agg({
        'occupation_title': 'first',
        'exposure_score': 'mean',
        'exposure_sd': 'mean',
        'exposure_gradient': 'first'
    }).reset_index()
    
    logger.info(f"Ocupações únicas: {len(df_agg):,}")
    logger.info(f"Score médio: {df_agg['exposure_score'].mean():.3f}")
    logger.info(f"Score range: [{df_agg['exposure_score'].min():.3f}, {df_agg['exposure_score'].max():.3f}]")
    
    # Garantir formato string com 4 dígitos
    df_agg['isco_08_str'] = df_agg['isco_08'].astype(str).str.zfill(4)
    
    # Distribuição por gradiente
    logger.info("\nDistribuição por gradiente:")
    for grad, count in df_agg['exposure_gradient'].value_counts().items():
        logger.info(f"  {grad}: {count} ocupações")
    
    # Salvar
    output_path = DATA_PROCESSED / "ilo_exposure_clean.csv"
    df_agg.to_csv(output_path, index=False)
    logger.info(f"\nSalvo em: {output_path}")
    
    return df_agg

if __name__ == "__main__":
    process_ilo()
```

---

### 2.3 src/03_clean_pnad.py

```python
"""
Script 03: Limpeza e criação de variáveis derivadas PNAD
Entrada: data/raw/pnad_2025q3.parquet
Saída: data/processed/pnad_clean.csv
"""

import logging
import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from config.settings import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '03_pnad_clean.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clean_pnad():
    """Limpa e prepara dados PNAD"""
    
    input_path = DATA_RAW / f"pnad_{PNAD_ANO}q{PNAD_TRIMESTRE}.parquet"
    logger.info(f"Lendo: {input_path}")
    df = pd.read_parquet(input_path)
    
    n_inicial = len(df)
    logger.info(f"Observações iniciais: {n_inicial:,}")
    
    # --- LIMPEZA ---
    
    # 1. Converter tipos
    df['cod_ocupacao'] = df['cod_ocupacao'].astype(str).str.zfill(4)
    df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
    df['rendimento_habitual'] = pd.to_numeric(df['rendimento_habitual'], errors='coerce')
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce')
    
    # 2. Remover missings críticos
    df = df.dropna(subset=['cod_ocupacao', 'idade', 'peso'])
    logger.info(f"Após remover missings críticos: {len(df):,} ({len(df)/n_inicial:.1%})")
    
    # 3. Filtrar faixa etária (18-65)
    df = df[(df['idade'] >= 18) & (df['idade'] <= 65)]
    logger.info(f"Após filtrar 18-65 anos: {len(df):,} ({len(df)/n_inicial:.1%})")
    
    # 4. Remover ocupações inválidas (código 0000 ou similar)
    df = df[~df['cod_ocupacao'].isin(['0000', '9999'])]
    logger.info(f"Após remover ocupações inválidas: {len(df):,}")
    
    # --- VARIÁVEIS DERIVADAS ---
    
    # Formalidade
    df['formal'] = df['posicao_ocupacao'].isin(['01', '03', '05']).astype(int)
    logger.info(f"Taxa de formalidade: {df['formal'].mean():.1%}")
    
    # Faixas etárias
    df['faixa_etaria'] = pd.cut(
        df['idade'],
        bins=IDADE_BINS,
        labels=IDADE_LABELS
    )
    
    # Região
    df['regiao'] = df['sigla_uf'].map(REGIAO_MAP)
    
    # Raça agregada
    df['raca_agregada'] = df['raca_cor'].map(RACA_MAP)
    
    # Grande grupo ocupacional
    df['grande_grupo'] = df['cod_ocupacao'].str[0].map(GRANDES_GRUPOS)
    
    # Sexo como texto
    df['sexo_texto'] = df['sexo'].map({1: 'Homem', 2: 'Mulher', '1': 'Homem', '2': 'Mulher'})
    
    # Winsorização de renda (percentil 99)
    p99 = df['rendimento_habitual'].quantile(0.99)
    df['rendimento_winsor'] = df['rendimento_habitual'].clip(upper=p99)
    logger.info(f"Percentil 99 renda: R$ {p99:,.0f}")
    
    # --- VALIDAÇÕES ---
    
    logger.info("\n=== VALIDAÇÕES ===")
    logger.info(f"Ocupações únicas (COD): {df['cod_ocupacao'].nunique()}")
    logger.info(f"UFs: {df['sigla_uf'].nunique()}")
    logger.info(f"Regiões: {df['regiao'].nunique()}")
    logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")
    
    logger.info("\nDistribuição por sexo:")
    for sexo, peso in df.groupby('sexo_texto')['peso'].sum().items():
        logger.info(f"  {sexo}: {peso/1e6:.1f} milhões")
    
    logger.info("\nDistribuição por região:")
    for regiao, peso in df.groupby('regiao')['peso'].sum().sort_values(ascending=False).items():
        logger.info(f"  {regiao}: {peso/1e6:.1f} milhões")
    
    # Salvar
    output_path = DATA_PROCESSED / "pnad_clean.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"\nSalvo em: {output_path}")
    
    return df

if __name__ == "__main__":
    clean_pnad()
```

---

### 2.4 src/04_crosswalk.py

```python
"""
Script 04: Crosswalk hierárquico COD → ISCO-08
Entrada: data/processed/pnad_clean.csv, data/processed/ilo_exposure_clean.csv
Saída: Log com estatísticas de match por nível
"""

import logging
import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from config.settings import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '04_crosswalk.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_ilo_aggregations(df_ilo):
    """Cria agregações ILO em diferentes níveis hierárquicos"""
    
    ilo_4d = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()
    ilo_3d = df_ilo.groupby(df_ilo['isco_08_str'].str[:3])['exposure_score'].mean().to_dict()
    ilo_2d = df_ilo.groupby(df_ilo['isco_08_str'].str[:2])['exposure_score'].mean().to_dict()
    ilo_1d = df_ilo.groupby(df_ilo['isco_08_str'].str[:1])['exposure_score'].mean().to_dict()
    
    logger.info(f"Códigos ILO 4-digit: {len(ilo_4d)}")
    logger.info(f"Códigos ILO 3-digit: {len(ilo_3d)}")
    logger.info(f"Códigos ILO 2-digit: {len(ilo_2d)}")
    logger.info(f"Códigos ILO 1-digit: {len(ilo_1d)}")
    
    return ilo_4d, ilo_3d, ilo_2d, ilo_1d

def hierarchical_crosswalk(df_pnad, ilo_4d, ilo_3d, ilo_2d, ilo_1d):
    """Aplica crosswalk hierárquico em 4 níveis"""
    
    logger.info("\n=== CROSSWALK HIERÁRQUICO ===")
    
    # Inicializar colunas
    df_pnad['exposure_score'] = np.nan
    df_pnad['match_level'] = None
    
    # Nível 1: 4-digit
    mask_4d = df_pnad['cod_ocupacao'].isin(ilo_4d.keys())
    df_pnad.loc[mask_4d, 'exposure_score'] = df_pnad.loc[mask_4d, 'cod_ocupacao'].map(ilo_4d)
    df_pnad.loc[mask_4d, 'match_level'] = '4-digit'
    logger.info(f"Match 4-digit: {mask_4d.sum():,} ({mask_4d.mean():.1%})")
    
    # Nível 2: 3-digit
    mask_missing = df_pnad['exposure_score'].isna()
    cod_3d = df_pnad.loc[mask_missing, 'cod_ocupacao'].str[:3]
    mask_3d = cod_3d.isin(ilo_3d.keys())
    idx_3d = mask_missing[mask_missing].index[mask_3d.values]
    df_pnad.loc[idx_3d, 'exposure_score'] = cod_3d[mask_3d].map(ilo_3d).values
    df_pnad.loc[idx_3d, 'match_level'] = '3-digit'
    logger.info(f"Match 3-digit: {len(idx_3d):,} ({len(idx_3d)/len(df_pnad):.1%})")
    
    # Nível 3: 2-digit
    mask_missing = df_pnad['exposure_score'].isna()
    cod_2d = df_pnad.loc[mask_missing, 'cod_ocupacao'].str[:2]
    mask_2d = cod_2d.isin(ilo_2d.keys())
    idx_2d = mask_missing[mask_missing].index[mask_2d.values]
    df_pnad.loc[idx_2d, 'exposure_score'] = cod_2d[mask_2d].map(ilo_2d).values
    df_pnad.loc[idx_2d, 'match_level'] = '2-digit'
    logger.info(f"Match 2-digit: {len(idx_2d):,} ({len(idx_2d)/len(df_pnad):.1%})")
    
    # Nível 4: 1-digit
    mask_missing = df_pnad['exposure_score'].isna()
    cod_1d = df_pnad.loc[mask_missing, 'cod_ocupacao'].str[:1]
    mask_1d = cod_1d.isin(ilo_1d.keys())
    idx_1d = mask_missing[mask_missing].index[mask_1d.values]
    df_pnad.loc[idx_1d, 'exposure_score'] = cod_1d[mask_1d].map(ilo_1d).values
    df_pnad.loc[idx_1d, 'match_level'] = '1-digit'
    logger.info(f"Match 1-digit: {len(idx_1d):,} ({len(idx_1d)/len(df_pnad):.1%})")
    
    # Sem match
    mask_no_match = df_pnad['exposure_score'].isna()
    logger.info(f"Sem match: {mask_no_match.sum():,} ({mask_no_match.mean():.1%})")
    
    return df_pnad

def validate_crosswalk(df):
    """Valida resultados do crosswalk"""
    
    logger.info("\n=== VALIDAÇÃO DO CROSSWALK ===")
    
    # Cobertura total
    coverage = df['exposure_score'].notna().mean()
    logger.info(f"Cobertura total: {coverage:.1%}")
    
    # Distribuição por nível
    logger.info("\nDistribuição por nível de match:")
    for level, count in df['match_level'].value_counts().items():
        pct = count / len(df) * 100
        logger.info(f"  {level}: {count:,} ({pct:.1f}%)")
    
    # Estatísticas de score
    logger.info("\nEstatísticas do score de exposição:")
    logger.info(f"  Média: {df['exposure_score'].mean():.3f}")
    logger.info(f"  Desvio-padrão: {df['exposure_score'].std():.3f}")
    logger.info(f"  Mínimo: {df['exposure_score'].min():.3f}")
    logger.info(f"  Máximo: {df['exposure_score'].max():.3f}")
    
    # Sanity check: exposição por grande grupo
    logger.info("\nExposição média por grande grupo (sanity check):")
    exp_grupos = df.groupby('grande_grupo').apply(
        lambda x: np.average(x['exposure_score'].dropna(), weights=x.loc[x['exposure_score'].notna(), 'peso'])
    ).sort_values(ascending=False)
    for grupo, score in exp_grupos.items():
        logger.info(f"  {grupo}: {score:.3f}")
    
    return coverage

def run_crosswalk():
    """Executa crosswalk completo"""
    
    # Carregar dados
    df_pnad = pd.read_csv(DATA_PROCESSED / "pnad_clean.csv")
    df_ilo = pd.read_csv(DATA_PROCESSED / "ilo_exposure_clean.csv")
    
    logger.info(f"PNAD: {len(df_pnad):,} observações")
    logger.info(f"ILO: {len(df_ilo):,} ocupações")
    
    # Criar agregações
    ilo_4d, ilo_3d, ilo_2d, ilo_1d = create_ilo_aggregations(df_ilo)
    
    # Aplicar crosswalk
    df_result = hierarchical_crosswalk(df_pnad.copy(), ilo_4d, ilo_3d, ilo_2d, ilo_1d)
    
    # Validar
    coverage = validate_crosswalk(df_result)
    
    # Retornar para uso no próximo script
    return df_result, coverage

if __name__ == "__main__":
    df, coverage = run_crosswalk()
    print(f"\n✓ Crosswalk concluído com {coverage:.1%} de cobertura")
```

---

### 2.5 src/05_merge_data.py

```python
"""
Script 05: Merge final e criação da base consolidada
Entrada: Dados do crosswalk
Saída: data/processed/pnad_ilo_merged.csv
"""

import logging
import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from config.settings import *
from src.s04_crosswalk import run_crosswalk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '05_merge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def add_gradient_classification(df):
    """Adiciona classificação por gradiente ILO"""
    
    # Definir thresholds baseados na metodologia ILO
    def classify_gradient(score):
        if pd.isna(score):
            return 'Sem classificação'
        elif score < 0.22:
            return 'Not Exposed'
        elif score < 0.36:
            return 'Minimal Exposure'
        elif score < 0.45:
            return 'Gradient 1-2'
        elif score < 0.55:
            return 'Gradient 3'
        else:
            return 'Gradient 4 (Alta)'
    
    df['exposure_gradient'] = df['exposure_score'].apply(classify_gradient)
    
    logger.info("\nDistribuição por gradiente:")
    for grad, peso in df.groupby('exposure_gradient')['peso'].sum().sort_values(ascending=False).items():
        logger.info(f"  {grad}: {peso/1e6:.1f} milhões")
    
    return df

def add_quintiles(df):
    """Adiciona quintis e decis de exposição"""
    
    # Filtrar apenas com score válido
    mask = df['exposure_score'].notna()
    
    # Quintis
    df.loc[mask, 'quintil_exposure'] = pd.qcut(
        df.loc[mask, 'exposure_score'],
        q=5,
        labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)'],
        duplicates='drop'
    )
    
    # Decis
    df.loc[mask, 'decil_exposure'] = pd.qcut(
        df.loc[mask, 'exposure_score'],
        q=10,
        labels=[f'D{i}' for i in range(1, 11)],
        duplicates='drop'
    )
    
    return df

def create_sector_aggregation(df):
    """Cria agregação setorial simplificada"""
    
    # Mapear CNAE para setores agregados (ajustar conforme códigos reais)
    setor_map = {
        # Agricultura
        '01': 'Agropecuária', '02': 'Agropecuária', '03': 'Agropecuária',
        # Indústria
        '05': 'Indústria', '06': 'Indústria', '07': 'Indústria', '08': 'Indústria',
        '10': 'Indústria', '11': 'Indústria', '12': 'Indústria', '13': 'Indústria',
        '14': 'Indústria', '15': 'Indústria', '16': 'Indústria', '17': 'Indústria',
        '18': 'Indústria', '19': 'Indústria', '20': 'Indústria', '21': 'Indústria',
        '22': 'Indústria', '23': 'Indústria', '24': 'Indústria', '25': 'Indústria',
        '26': 'Indústria', '27': 'Indústria', '28': 'Indústria', '29': 'Indústria',
        '30': 'Indústria', '31': 'Indústria', '32': 'Indústria', '33': 'Indústria',
        # Construção
        '41': 'Construção', '42': 'Construção', '43': 'Construção',
        # Comércio
        '45': 'Comércio', '46': 'Comércio', '47': 'Comércio',
        # Serviços
        '49': 'Serviços', '50': 'Serviços', '51': 'Serviços', '52': 'Serviços',
        '53': 'Serviços', '55': 'Serviços', '56': 'Serviços',
        # TIC / Serviços especializados
        '58': 'TIC e Serviços Prof.', '59': 'TIC e Serviços Prof.', '60': 'TIC e Serviços Prof.',
        '61': 'TIC e Serviços Prof.', '62': 'TIC e Serviços Prof.', '63': 'TIC e Serviços Prof.',
        '64': 'TIC e Serviços Prof.', '65': 'TIC e Serviços Prof.', '66': 'TIC e Serviços Prof.',
        '69': 'TIC e Serviços Prof.', '70': 'TIC e Serviços Prof.', '71': 'TIC e Serviços Prof.',
        '72': 'TIC e Serviços Prof.', '73': 'TIC e Serviços Prof.', '74': 'TIC e Serviços Prof.',
        '75': 'TIC e Serviços Prof.',
        # Administração pública
        '84': 'Administração Pública',
        # Educação
        '85': 'Educação',
        # Saúde
        '86': 'Saúde', '87': 'Saúde', '88': 'Saúde',
    }
    
    # Extrair 2 primeiros dígitos do grupamento de atividade
    if df['grupamento_atividade'].dtype == 'object':
        df['cnae_2d'] = df['grupamento_atividade'].astype(str).str[:2]
    else:
        df['cnae_2d'] = df['grupamento_atividade'].astype(str).str[:2]
    
    df['setor_agregado'] = df['cnae_2d'].map(setor_map).fillna('Outros Serviços')
    
    return df

def merge_and_finalize():
    """Executa merge final e salva base consolidada"""
    
    logger.info("=== MERGE FINAL ===\n")
    
    # Executar crosswalk
    df, coverage = run_crosswalk()
    
    # Adicionar classificações
    df = add_gradient_classification(df)
    df = add_quintiles(df)
    df = create_sector_aggregation(df)
    
    # Estatísticas finais
    logger.info("\n=== BASE FINAL ===")
    logger.info(f"Total de observações: {len(df):,}")
    logger.info(f"Com score de exposição: {df['exposure_score'].notna().sum():,}")
    logger.info(f"Cobertura: {df['exposure_score'].notna().mean():.1%}")
    logger.info(f"População representada: {df['peso'].sum()/1e6:.1f} milhões")
    
    # Colunas finais
    cols_output = [
        'ano', 'trimestre', 'sigla_uf', 'regiao',
        'sexo', 'sexo_texto', 'idade', 'faixa_etaria',
        'raca_cor', 'raca_agregada', 'nivel_instrucao',
        'cod_ocupacao', 'grande_grupo',
        'grupamento_atividade', 'setor_agregado',
        'posicao_ocupacao', 'formal',
        'rendimento_habitual', 'rendimento_winsor', 'rendimento_todos',
        'horas_trabalhadas', 'peso',
        'exposure_score', 'exposure_gradient', 'match_level',
        'quintil_exposure', 'decil_exposure'
    ]
    
    df_final = df[[c for c in cols_output if c in df.columns]]
    
    # Salvar
    output_path = DATA_PROCESSED / "pnad_ilo_merged.csv"
    df_final.to_csv(output_path, index=False)
    logger.info(f"\nBase final salva em: {output_path}")
    logger.info(f"Tamanho: {df_final.memory_usage(deep=True).sum()/1e6:.1f} MB")
    
    return df_final

if __name__ == "__main__":
    df = merge_and_finalize()
    print("\n✓ Merge concluído com sucesso!")
```

---

### 2.6 src/utils/weighted_stats.py

```python
"""
Funções utilitárias para estatísticas ponderadas
"""

import numpy as np
import pandas as pd

def weighted_mean(values, weights):
    """Calcula média ponderada"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    return np.average(values[mask], weights=weights[mask])

def weighted_std(values, weights):
    """Calcula desvio-padrão ponderado"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    avg = np.average(values[mask], weights=weights[mask])
    variance = np.average((values[mask] - avg) ** 2, weights=weights[mask])
    return np.sqrt(variance)

def weighted_quantile(values, weights, quantile):
    """Calcula quantil ponderado"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    
    sorted_idx = np.argsort(values[mask])
    sorted_values = values[mask].iloc[sorted_idx]
    sorted_weights = weights[mask].iloc[sorted_idx]
    
    cumsum = np.cumsum(sorted_weights)
    cutoff = quantile * cumsum.iloc[-1]
    
    return sorted_values.iloc[np.searchsorted(cumsum, cutoff)]

def gini_coefficient(values, weights):
    """Calcula coeficiente de Gini ponderado"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() < 2:
        return np.nan
    
    x = np.array(values[mask])
    w = np.array(weights[mask])
    
    sorted_idx = np.argsort(x)
    sorted_x = x[sorted_idx]
    sorted_w = w[sorted_idx]
    
    cumsum_w = np.cumsum(sorted_w)
    cumsum_wx = np.cumsum(sorted_w * sorted_x)
    
    total_w = cumsum_w[-1]
    total_wx = cumsum_wx[-1]
    
    # Área sob curva de Lorenz
    B = np.sum(cumsum_wx[:-1] * sorted_w[1:]) / (total_w * total_wx)
    
    return 1 - 2 * B

def weighted_stats_summary(values, weights):
    """Retorna dicionário com estatísticas resumidas"""
    return {
        'mean': weighted_mean(values, weights),
        'std': weighted_std(values, weights),
        'p25': weighted_quantile(values, weights, 0.25),
        'p50': weighted_quantile(values, weights, 0.50),
        'p75': weighted_quantile(values, weights, 0.75),
        'n': (~pd.isna(values)).sum(),
        'population': weights[~pd.isna(values)].sum()
    }
```

---

### 2.7 src/06_analysis_tables.py

```python
"""
Script 06: Geração das 5 tabelas principais
Entrada: data/processed/pnad_ilo_merged.csv
Saída: outputs/tables/*.csv e *.tex
"""

import logging
import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from config.settings import *
from src.utils.weighted_stats import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '06_tables.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_data():
    """Carrega base consolidada"""
    df = pd.read_csv(DATA_PROCESSED / "pnad_ilo_merged.csv")
    logger.info(f"Dados carregados: {len(df):,} observações")
    return df

def table1_exposicao_grupos(df):
    """TABELA 1: Exposição por Grande Grupo Ocupacional"""
    
    logger.info("\n=== TABELA 1: Exposição por Grande Grupo ===")
    
    results = []
    for grupo in df['grande_grupo'].dropna().unique():
        mask = df['grande_grupo'] == grupo
        subset = df[mask]
        
        results.append({
            'Grande Grupo': grupo,
            'Exposição Média': weighted_mean(subset['exposure_score'], subset['peso']),
            'Desvio-Padrão': weighted_std(subset['exposure_score'], subset['peso']),
            'Trabalhadores (milhões)': subset['peso'].sum() / 1e6,
            '% Força de Trabalho': subset['peso'].sum() / df['peso'].sum() * 100
        })
    
    tabela1 = pd.DataFrame(results)
    tabela1 = tabela1.sort_values('Exposição Média', ascending=False)
    tabela1 = tabela1.round(3)
    
    # Salvar CSV
    tabela1.to_csv(OUTPUTS_TABLES / "tabela1_exposicao_grupos.csv", index=False)
    
    # Salvar LaTeX
    latex = tabela1.to_latex(
        index=False,
        caption='Exposição à IA Generativa por Grande Grupo Ocupacional - Brasil 3º Tri 2025',
        label='tab:exposicao_grupos',
        column_format='lrrrr'
    )
    with open(OUTPUTS_TABLES / "tabela1_exposicao_grupos.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela1.to_string())
    return tabela1

def table2_perfil_quintis(df):
    """TABELA 2: Perfil Socioeconômico por Quintil de Exposição"""
    
    logger.info("\n=== TABELA 2: Perfil por Quintil ===")
    
    results = []
    for quintil in df['quintil_exposure'].dropna().unique():
        mask = df['quintil_exposure'] == quintil
        subset = df[mask]
        
        results.append({
            'Quintil': quintil,
            'Rendimento Médio (R$)': weighted_mean(subset['rendimento_habitual'], subset['peso']),
            '% Formal': weighted_mean(subset['formal'], subset['peso']) * 100,
            '% Mulheres': weighted_mean(subset['sexo_texto'] == 'Mulher', subset['peso']) * 100,
            '% Negros': weighted_mean(subset['raca_agregada'] == 'Negra', subset['peso']) * 100,
            'Idade Média': weighted_mean(subset['idade'], subset['peso']),
            'Pop. (milhões)': subset['peso'].sum() / 1e6
        })
    
    tabela2 = pd.DataFrame(results)
    tabela2 = tabela2.sort_values('Quintil')
    tabela2 = tabela2.round(2)
    
    # Salvar
    tabela2.to_csv(OUTPUTS_TABLES / "tabela2_perfil_quintis.csv", index=False)
    
    latex = tabela2.to_latex(
        index=False,
        caption='Perfil Socioeconômico por Quintil de Exposição à IA - Brasil 3º Tri 2025',
        label='tab:perfil_quintis'
    )
    with open(OUTPUTS_TABLES / "tabela2_perfil_quintis.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela2.to_string())
    return tabela2

def table3_regiao_setor(df):
    """TABELA 3: Exposição por Região e Setor (matriz)"""
    
    logger.info("\n=== TABELA 3: Região x Setor ===")
    
    # Calcular médias ponderadas por célula
    def calc_weighted_mean(group):
        return weighted_mean(group['exposure_score'], group['peso'])
    
    tabela3 = df.groupby(['regiao', 'setor_agregado']).apply(calc_weighted_mean).unstack(fill_value=np.nan)
    tabela3 = tabela3.round(3)
    
    # Adicionar médias marginais
    tabela3['Média Região'] = df.groupby('regiao').apply(calc_weighted_mean)
    
    setor_means = df.groupby('setor_agregado').apply(calc_weighted_mean)
    tabela3.loc['Média Setor'] = setor_means
    tabela3.loc['Média Setor', 'Média Região'] = weighted_mean(df['exposure_score'], df['peso'])
    
    # Salvar
    tabela3.to_csv(OUTPUTS_TABLES / "tabela3_regiao_setor.csv")
    
    latex = tabela3.to_latex(
        caption='Exposição Média à IA por Região e Setor - Brasil 3º Tri 2025',
        label='tab:regiao_setor'
    )
    with open(OUTPUTS_TABLES / "tabela3_regiao_setor.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela3.to_string())
    return tabela3

def table4_desigualdade(df):
    """TABELA 4: Decomposição da Desigualdade de Exposição"""
    
    logger.info("\n=== TABELA 4: Desigualdade ===")
    
    mask = df['exposure_score'].notna()
    subset = df[mask]
    
    results = {
        'Métrica': [],
        'Valor': []
    }
    
    # Gini total
    gini = gini_coefficient(subset['exposure_score'], subset['peso'])
    results['Métrica'].append('Coeficiente de Gini')
    results['Valor'].append(gini)
    
    # Razão P90/P10
    p90 = weighted_quantile(subset['exposure_score'], subset['peso'], 0.90)
    p10 = weighted_quantile(subset['exposure_score'], subset['peso'], 0.10)
    results['Métrica'].append('Razão P90/P10')
    results['Valor'].append(p90 / p10 if p10 > 0 else np.nan)
    
    # Razão Q5/Q1
    q5_mean = weighted_mean(
        subset[subset['quintil_exposure'] == 'Q5 (Alta)']['exposure_score'],
        subset[subset['quintil_exposure'] == 'Q5 (Alta)']['peso']
    )
    q1_mean = weighted_mean(
        subset[subset['quintil_exposure'] == 'Q1 (Baixa)']['exposure_score'],
        subset[subset['quintil_exposure'] == 'Q1 (Baixa)']['peso']
    )
    results['Métrica'].append('Razão Média Q5/Q1')
    results['Valor'].append(q5_mean / q1_mean if q1_mean > 0 else np.nan)
    
    # % em alta exposição (Gradient 4)
    alta_exp = subset[subset['exposure_gradient'] == 'Gradient 4 (Alta)']['peso'].sum()
    results['Métrica'].append('% Alta Exposição (G4)')
    results['Valor'].append(alta_exp / subset['peso'].sum() * 100)
    
    tabela4 = pd.DataFrame(results)
    tabela4 = tabela4.round(4)
    
    # Salvar
    tabela4.to_csv(OUTPUTS_TABLES / "tabela4_desigualdade.csv", index=False)
    
    latex = tabela4.to_latex(
        index=False,
        caption='Métricas de Desigualdade na Exposição à IA - Brasil 3º Tri 2025',
        label='tab:desigualdade'
    )
    with open(OUTPUTS_TABLES / "tabela4_desigualdade.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela4.to_string())
    return tabela4

def table5_comparacao(df):
    """TABELA 5: Comparação com Literatura"""
    
    logger.info("\n=== TABELA 5: Comparação ===")
    
    mask = df['exposure_score'].notna()
    media_br = weighted_mean(df[mask]['exposure_score'], df[mask]['peso'])
    
    # Alta exposição (score >= 0.45)
    alta_exp = df[df['exposure_score'] >= 0.45]['peso'].sum() / df[mask]['peso'].sum() * 100
    
    tabela5 = pd.DataFrame({
        'Estudo': [
            'Presente estudo (ILO 2025)',
            'Imaizumi et al. (LCA, 2024)*',
            'Gmyrek et al. (ILO, 2023)*',
            'Eloundou et al. (OpenAI, 2023)*'
        ],
        'Metodologia': [
            'ILO refined index 2025',
            'ILO 2023 + PNAD',
            'ILO 2023 global',
            'GPT exposure rubrics'
        ],
        'País/Região': [
            'Brasil',
            'Brasil',
            'Global',
            'EUA'
        ],
        'Exposição Média': [
            media_br,
            np.nan,  # Preencher manualmente após consultar literatura
            0.30,    # Valor aproximado ILO 2023
            np.nan   # Diferente metodologia
        ],
        '% Alta Exposição': [
            alta_exp,
            np.nan,
            np.nan,
            np.nan
        ]
    })
    
    tabela5.to_csv(OUTPUTS_TABLES / "tabela5_comparacao.csv", index=False)
    
    logger.info("* Valores a serem preenchidos após consulta à literatura")
    logger.info(tabela5.to_string())
    return tabela5

def generate_all_tables():
    """Gera todas as tabelas"""
    
    logger.info("=" * 60)
    logger.info("GERAÇÃO DE TABELAS - ETAPA 1")
    logger.info("=" * 60)
    
    df = load_data()
    
    t1 = table1_exposicao_grupos(df)
    t2 = table2_perfil_quintis(df)
    t3 = table3_regiao_setor(df)
    t4 = table4_desigualdade(df)
    t5 = table5_comparacao(df)
    
    logger.info("\n" + "=" * 60)
    logger.info("TABELAS GERADAS COM SUCESSO!")
    logger.info(f"Arquivos salvos em: {OUTPUTS_TABLES}")
    logger.info("=" * 60)
    
    return {'t1': t1, 't2': t2, 't3': t3, 't4': t4, 't5': t5}

if __name__ == "__main__":
    generate_all_tables()
```

---

### 2.8 src/07_analysis_figures.py

```python
"""
Script 07: Geração das 4 figuras principais
Entrada: data/processed/pnad_ilo_merged.csv
Saída: outputs/figures/*.png e *.pdf
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress
import sys
sys.path.append('..')
from config.settings import *
from src.utils.weighted_stats import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '07_figures.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações globais de estilo
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
sns.set_style("whitegrid")

def load_data():
    """Carrega base consolidada"""
    df = pd.read_csv(DATA_PROCESSED / "pnad_ilo_merged.csv")
    logger.info(f"Dados carregados: {len(df):,} observações")
    return df

def figure1_distribuicao(df):
    """FIGURA 1: Distribuição da Exposição (dois painéis)"""
    
    logger.info("\n=== FIGURA 1: Distribuição da Exposição ===")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    mask = df['exposure_score'].notna()
    subset = df[mask]
    
    # Painel A: Histograma ponderado
    ax1.hist(
        subset['exposure_score'], 
        weights=subset['peso'] / 1e6,  # Em milhões
        bins=50, 
        edgecolor='black', 
        alpha=0.7, 
        color='steelblue'
    )
    
    media = weighted_mean(subset['exposure_score'], subset['peso'])
    ax1.axvline(media, color='red', linestyle='--', linewidth=2, 
                label=f'Média: {media:.3f}')
    
    ax1.set_xlabel('Score de Exposição à IA Generativa')
    ax1.set_ylabel('Trabalhadores (milhões)')
    ax1.set_title('(A) Distribuição Contínua da Exposição')
    ax1.legend()
    
    # Painel B: Barras por gradiente
    gradient_counts = subset.groupby('exposure_gradient')['peso'].sum() / 1e6
    gradient_order = ['Not Exposed', 'Minimal Exposure', 'Gradient 1-2', 'Gradient 3', 'Gradient 4 (Alta)']
    gradient_counts = gradient_counts.reindex([g for g in gradient_order if g in gradient_counts.index])
    
    colors = ['#2ca02c', '#98df8a', '#ffbb78', '#ff7f0e', '#d62728'][:len(gradient_counts)]
    ax2.barh(range(len(gradient_counts)), gradient_counts.values, 
             color=colors, edgecolor='black')
    ax2.set_yticks(range(len(gradient_counts)))
    ax2.set_yticklabels(gradient_counts.index)
    ax2.set_xlabel('Trabalhadores (milhões)')
    ax2.set_title('(B) Distribuição por Gradiente ILO')
    
    # Adicionar valores nas barras
    for i, v in enumerate(gradient_counts.values):
        ax2.text(v + 0.5, i, f'{v:.1f}M', va='center')
    
    plt.suptitle('Distribuição da Exposição à IA Generativa na Força de Trabalho Brasileira\n3º Trimestre 2025', 
                 fontsize=14, y=1.02)
    plt.tight_layout()
    
    # Salvar
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig1_distribuicao_exposicao.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"Figura 1 salva em {OUTPUTS_FIGURES}")
    plt.close()

def figure2_heatmap(df):
    """FIGURA 2: Heatmap Região x Setor"""
    
    logger.info("\n=== FIGURA 2: Heatmap Região x Setor ===")
    
    def calc_weighted_mean(group):
        return weighted_mean(group['exposure_score'], group['peso'])
    
    pivot = df.groupby(['regiao', 'setor_agregado']).apply(calc_weighted_mean).unstack()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    sns.heatmap(
        pivot, 
        annot=True, 
        fmt='.3f', 
        cmap='YlOrRd',
        cbar_kws={'label': 'Score de Exposição'},
        ax=ax,
        linewidths=0.5
    )
    
    ax.set_title('Exposição à IA Generativa por Região e Setor\nBrasil - 3º Trimestre 2025', fontsize=14)
    ax.set_xlabel('Setor de Atividade')
    ax.set_ylabel('Região')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig2_heatmap_regiao_setor.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"Figura 2 salva em {OUTPUTS_FIGURES}")
    plt.close()

def figure3_renda(df):
    """FIGURA 3: Perfil Salarial por Decil de Exposição"""
    
    logger.info("\n=== FIGURA 3: Renda por Exposição ===")
    
    mask = df['decil_exposure'].notna()
    subset = df[mask]
    
    renda_decil = subset.groupby('decil_exposure').apply(
        lambda x: weighted_mean(x['rendimento_habitual'], x['peso'])
    )
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(range(len(renda_decil)), renda_decil.values, 
                  color='teal', edgecolor='black', alpha=0.8)
    
    ax.set_xticks(range(len(renda_decil)))
    ax.set_xticklabels(renda_decil.index, rotation=0)
    ax.set_xlabel('Decil de Exposição à IA')
    ax.set_ylabel('Rendimento Médio Mensal (R$)')
    ax.set_title('Rendimento Médio por Decil de Exposição à IA Generativa\nBrasil - 3º Trimestre 2025')
    
    # Linha de tendência
    x_numeric = np.arange(1, len(renda_decil) + 1)
    slope, intercept, r_value, p_value, std_err = linregress(x_numeric, renda_decil.values)
    
    trend_line = slope * x_numeric + intercept
    ax.plot(range(len(renda_decil)), trend_line, 'r--', linewidth=2,
            label=f'Tendência (R² = {r_value**2:.3f})')
    
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Formatar valores no eixo Y
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
    
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig3_renda_exposicao.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"Figura 3 salva em {OUTPUTS_FIGURES}")
    logger.info(f"Correlação exposição-renda: R² = {r_value**2:.3f}")
    plt.close()

def figure4_decomposicao(df):
    """FIGURA 4: Decomposição Demográfica (4 painéis)"""
    
    logger.info("\n=== FIGURA 4: Decomposição Demográfica ===")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    mask = df['exposure_gradient'].notna()
    subset = df[mask]
    
    gradient_order = ['Not Exposed', 'Minimal Exposure', 'Gradient 1-2', 'Gradient 3', 'Gradient 4 (Alta)']
    
    # Painel A: Por gênero
    gender_comp = subset.groupby(['exposure_gradient', 'sexo_texto'])['peso'].sum().unstack(fill_value=0)
    gender_comp = gender_comp.reindex([g for g in gradient_order if g in gender_comp.index])
    gender_pct = gender_comp.div(gender_comp.sum(axis=1), axis=0)
    
    gender_pct.plot(kind='barh', stacked=True, ax=axes[0,0], 
                   color=['lightblue', 'lightpink'], edgecolor='black')
    axes[0,0].set_title('(A) Composição por Gênero')
    axes[0,0].set_xlabel('Proporção')
    axes[0,0].legend(title='Sexo')
    
    # Painel B: Por raça
    race_comp = subset.groupby(['exposure_gradient', 'raca_agregada'])['peso'].sum().unstack(fill_value=0)
    race_comp = race_comp.reindex([g for g in gradient_order if g in race_comp.index])
    race_pct = race_comp.div(race_comp.sum(axis=1), axis=0)
    
    race_pct.plot(kind='barh', stacked=True, ax=axes[0,1], 
                 color=['#d4a574', '#8b6914', '#a9a9a9'], edgecolor='black')
    axes[0,1].set_title('(B) Composição por Raça')
    axes[0,1].set_xlabel('Proporção')
    axes[0,1].legend(title='Raça')
    
    # Painel C: Por formalidade
    formal_comp = subset.groupby(['exposure_gradient', 'formal'])['peso'].sum().unstack(fill_value=0)
    formal_comp = formal_comp.reindex([g for g in gradient_order if g in formal_comp.index])
    formal_comp.columns = ['Informal', 'Formal']
    formal_pct = formal_comp.div(formal_comp.sum(axis=1), axis=0)
    
    formal_pct.plot(kind='barh', stacked=True, ax=axes[1,0], 
                   color=['lightcoral', 'lightgreen'], edgecolor='black')
    axes[1,0].set_title('(C) Composição por Formalidade')
    axes[1,0].set_xlabel('Proporção')
    axes[1,0].legend(title='Vínculo')
    
    # Painel D: Por faixa etária
    age_comp = subset.groupby(['exposure_gradient', 'faixa_etaria'])['peso'].sum().unstack(fill_value=0)
    age_comp = age_comp.reindex([g for g in gradient_order if g in age_comp.index])
    age_pct = age_comp.div(age_comp.sum(axis=1), axis=0)
    
    cmap = plt.cm.viridis(np.linspace(0.2, 0.8, len(age_pct.columns)))
    age_pct.plot(kind='barh', stacked=True, ax=axes[1,1], 
                color=cmap, edgecolor='black')
    axes[1,1].set_title('(D) Composição por Faixa Etária')
    axes[1,1].set_xlabel('Proporção')
    axes[1,1].legend(title='Idade', bbox_to_anchor=(1.05, 1))
    
    plt.suptitle('Composição Demográfica por Gradiente de Exposição à IA\nBrasil - 3º Trimestre 2025', 
                 fontsize=14, y=1.02)
    plt.tight_layout()
    
    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig4_decomposicao_demografica.{ext}', 
                   dpi=300, bbox_inches='tight')
    
    logger.info(f"Figura 4 salva em {OUTPUTS_FIGURES}")
    plt.close()

def generate_all_figures():
    """Gera todas as figuras"""
    
    logger.info("=" * 60)
    logger.info("GERAÇÃO DE FIGURAS - ETAPA 1")
    logger.info("=" * 60)
    
    df = load_data()
    
    figure1_distribuicao(df)
    figure2_heatmap(df)
    figure3_renda(df)
    figure4_decomposicao(df)
    
    logger.info("\n" + "=" * 60)
    logger.info("FIGURAS GERADAS COM SUCESSO!")
    logger.info(f"Arquivos salvos em: {OUTPUTS_FIGURES}")
    logger.info("=" * 60)

if __name__ == "__main__":
    generate_all_figures()
```

---

## PARTE 3: TESTES INTERMEDIÁRIOS

### 3.1 tests/test_01_download.py

```python
"""
Teste: Validar download PNAD
Executar após: 01_download_pnad.py
"""

import pandas as pd
import sys
sys.path.append('..')
from config.settings import *

def test_download():
    """Testa se download foi bem sucedido"""
    
    file_path = DATA_RAW / f"pnad_{PNAD_ANO}q{PNAD_TRIMESTRE}.parquet"
    
    # Teste 1: Arquivo existe
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    print("✓ Arquivo existe")
    
    # Teste 2: Carregar e verificar tamanho
    df = pd.read_parquet(file_path)
    assert len(df) > 100000, f"Dados insuficientes: {len(df)} linhas"
    print(f"✓ {len(df):,} observações carregadas")
    
    # Teste 3: Colunas esperadas
    expected_cols = ['cod_ocupacao', 'peso', 'rendimento_habitual', 'idade', 'sigla_uf']
    for col in expected_cols:
        assert col in df.columns, f"Coluna ausente: {col}"
    print(f"✓ Colunas esperadas presentes")
    
    # Teste 4: Todas UFs presentes
    ufs = df['sigla_uf'].nunique()
    assert ufs == 27, f"UFs incompletas: {ufs}/27"
    print(f"✓ Todas 27 UFs presentes")
    
    # Teste 5: Peso válido
    assert df['peso'].sum() > 50e6, "Peso total muito baixo"
    print(f"✓ População: {df['peso'].sum()/1e6:.1f} milhões")
    
    print("\n🎉 TODOS OS TESTES PASSARAM - DOWNLOAD OK!")
    return True

if __name__ == "__main__":
    test_download()
```

### 3.2 tests/test_04_crosswalk.py

```python
"""
Teste: Validar crosswalk COD-ISCO
Executar após: 04_crosswalk.py
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from config.settings import *

def test_crosswalk():
    """Testa qualidade do crosswalk"""
    
    df = pd.read_csv(DATA_PROCESSED / "pnad_clean.csv")
    
    # Simular crosswalk ou carregar resultado
    # (ajustar conforme implementação)
    
    # Teste 1: Cobertura mínima 90%
    # coverage = df['exposure_score'].notna().mean()
    # assert coverage >= 0.90, f"Cobertura baixa: {coverage:.1%}"
    
    # Teste 2: Sanity check - grupos manuais devem ter exposição esperada
    # Ex: Apoio administrativo > Agropecuária
    
    print("✓ Testes de crosswalk definidos")
    print("⚠ Executar após script 04_crosswalk.py")
    
    return True

if __name__ == "__main__":
    test_crosswalk()
```

### 3.3 tests/test_05_merge.py

```python
"""
Teste: Validar base final merged
Executar após: 05_merge_data.py
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from config.settings import *

def test_merged_data():
    """Testa integridade da base final"""
    
    file_path = DATA_PROCESSED / "pnad_ilo_merged.csv"
    
    # Teste 1: Arquivo existe
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    print("✓ Arquivo existe")
    
    df = pd.read_csv(file_path)
    
    # Teste 2: Colunas essenciais
    required = [
        'exposure_score', 'exposure_gradient', 'quintil_exposure',
        'grande_grupo', 'regiao', 'setor_agregado', 'peso',
        'rendimento_habitual', 'sexo_texto', 'raca_agregada', 'formal'
    ]
    for col in required:
        assert col in df.columns, f"Coluna ausente: {col}"
    print("✓ Colunas essenciais presentes")
    
    # Teste 3: Cobertura de exposure_score
    coverage = df['exposure_score'].notna().mean()
    assert coverage >= 0.85, f"Cobertura de score baixa: {coverage:.1%}"
    print(f"✓ Cobertura de scores: {coverage:.1%}")
    
    # Teste 4: Score no range válido [0, 1]
    scores = df['exposure_score'].dropna()
    assert scores.min() >= 0, f"Score mínimo inválido: {scores.min()}"
    assert scores.max() <= 1, f"Score máximo inválido: {scores.max()}"
    print(f"✓ Scores no range [0, 1]: [{scores.min():.3f}, {scores.max():.3f}]")
    
    # Teste 5: Gradientes atribuídos
    grad_coverage = df['exposure_gradient'].notna().mean()
    assert grad_coverage >= 0.85, f"Gradientes incompletos: {grad_coverage:.1%}"
    print(f"✓ Gradientes atribuídos: {grad_coverage:.1%}")
    
    # Teste 6: Quintis balanceados
    quintil_counts = df['quintil_exposure'].value_counts()
    min_pct = quintil_counts.min() / len(df) * 100
    max_pct = quintil_counts.max() / len(df) * 100
    assert max_pct - min_pct < 10, "Quintis muito desbalanceados"
    print(f"✓ Quintis balanceados ({min_pct:.1f}% - {max_pct:.1f}%)")
    
    # Teste 7: Peso total consistente
    pop = df['peso'].sum() / 1e6
    assert 50 < pop < 150, f"População fora do esperado: {pop:.1f}M"
    print(f"✓ População: {pop:.1f} milhões")
    
    print("\n🎉 TODOS OS TESTES PASSARAM - BASE FINAL OK!")
    return True

if __name__ == "__main__":
    test_merged_data()
```

---

## PARTE 4: SCRIPT MASTER

### run_all.py

```python
"""
Script Master: Executa todo o pipeline da Etapa 1
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_script(script_name):
    """Executa um script e retorna status"""
    print(f"\n{'='*60}")
    print(f"EXECUTANDO: {script_name}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        [sys.executable, f"src/{script_name}"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ ERRO em {script_name}:")
        print(result.stderr)
        return False
    
    print(result.stdout)
    print(f"✓ {script_name} concluído com sucesso")
    return True

def run_test(test_name):
    """Executa um teste"""
    print(f"\n>>> Executando teste: {test_name}")
    result = subprocess.run(
        [sys.executable, f"tests/{test_name}"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    return result.returncode == 0

def main():
    """Pipeline completo"""
    
    start_time = datetime.now()
    print("=" * 60)
    print("ETAPA 1 - PIPELINE COMPLETO")
    print(f"Início: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Etapa 1: Download PNAD
    if not run_script("01_download_pnad.py"):
        return False
    run_test("test_01_download.py")
    
    # Etapa 2: Processar ILO
    if not run_script("02_process_ilo.py"):
        return False
    
    # Etapa 3: Limpar PNAD
    if not run_script("03_clean_pnad.py"):
        return False
    
    # Etapa 4: Crosswalk (validação manual recomendada)
    print("\n⚠ ATENÇÃO: Revise o log de crosswalk antes de prosseguir")
    input("Pressione ENTER para continuar...")
    
    # Etapa 5: Merge
    if not run_script("05_merge_data.py"):
        return False
    run_test("test_05_merge.py")
    
    # Etapa 6: Gerar Tabelas
    if not run_script("06_analysis_tables.py"):
        return False
    
    # Etapa 7: Gerar Figuras
    if not run_script("07_analysis_figures.py"):
        return False
    
    # Finalização
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    print("\n" + "=" * 60)
    print("🎉 PIPELINE CONCLUÍDO COM SUCESSO!")
    print(f"Duração total: {duration:.1f} minutos")
    print(f"Fim: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n📁 OUTPUTS GERADOS:")
    print("  - data/processed/pnad_ilo_merged.csv")
    print("  - outputs/tables/*.csv e *.tex")
    print("  - outputs/figures/*.png e *.pdf")
    print("  - outputs/logs/*.log")
    
    return True

if __name__ == "__main__":
    main()
```

---

## PARTE 5: REQUIREMENTS.TXT

```
# Core
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=12.0.0

# BigQuery / Google Cloud
basedosdados>=1.6.0
google-cloud-bigquery>=3.0.0
google-auth>=2.0.0

# Visualização
matplotlib>=3.7.0
seaborn>=0.12.0

# Estatística
scipy>=1.10.0
statsmodels>=0.14.0

# Excel
openpyxl>=3.1.0
xlrd>=2.0.0

# Utilitários
requests>=2.28.0
tqdm>=4.65.0

# Opcional - NLP para crosswalk avançado
# sentence-transformers>=2.2.0
```

---

## CHECKLIST DE EXECUÇÃO

### Antes de começar
- [ ] Criar projeto no Google Cloud Console
- [ ] Configurar billing (free tier é suficiente)
- [ ] Instalar Google Cloud SDK e autenticar
- [ ] Baixar arquivo ILO do GitHub
- [ ] Instalar dependências: `pip install -r requirements.txt`

### Execução sequencial
- [ ] 01: Baixar PNAD → Testar com `test_01_download.py`
- [ ] 02: Processar ILO → Verificar log `02_ilo_process.log`
- [ ] 03: Limpar PNAD → Verificar estatísticas no log
- [ ] 04: Crosswalk → **REVISAR LOG CUIDADOSAMENTE** (ponto crítico)
- [ ] 05: Merge → Testar com `test_05_merge.py`
- [ ] 06: Tabelas → Verificar `outputs/tables/`
- [ ] 07: Figuras → Verificar `outputs/figures/`

### Após conclusão
- [ ] Revisar todos os logs em `outputs/logs/`
- [ ] Verificar se tabelas estão coerentes
- [ ] Verificar se figuras estão legíveis
- [ ] Preencher RESULTADOS_ETAPA1.md

---

## PONTOS DE ATENÇÃO

1. **Crosswalk é o ponto crítico** - Taxa de match 4-digit deve ser >60%, total >95%
2. **Sempre usar pesos** - Nunca calcular média/contagem sem ponderar
3. **Validar sanidade** - Grupo 4 (administrativo) deve ter exposição alta, Grupo 9 (elementares) baixa
4. **Documentar decisões** - Anotar qualquer ajuste feito nos scripts

---

*Arquivo criado em: Janeiro 2026*
*Para uso com Cursor AI*
