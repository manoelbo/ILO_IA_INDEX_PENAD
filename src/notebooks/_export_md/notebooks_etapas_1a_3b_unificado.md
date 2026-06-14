# Compilação unificada — etapas 1a a 3b

_Gerado com Quarto (`quarto render … --to gfm --no-execute`). As figuras usam caminhos relativos às pastas `*_files` neste mesmo diretório._


---

<!-- fonte: etapa_1a_preparacao_dados_ilo_pnadc.ipynb -->

# ETAPA 1 - Análise Descritiva da Exposição de IA Generativa com ILO
Index e PNADc


## PREPARAÇÃO DOS DADOS

**Dissertação:** Inteligência Artificial Generativa e o Mercado de
Trabalho Brasileiro: Uma Análise de Exposição Ocupacional e seus Efeitos
Distributivos.

**Aluno:** Manoel Brasil Orlandi

### Contextualização

A rápida difusão de modelos de IA generativa (LLMs, geradores de
imagem/código) levanta questões centrais sobre seus impactos no mercado
de trabalho. Para mensurar esse potencial de impacto, a Organização
Internacional do Trabalho (OIT) criou índice de exposição ocupacional à
IA generativa, publicado como *Working Paper* 140 (WP140). O índice
atribui scores de exposição a cada ocupação da classificação ISCO-08,
com base na avaliação de suas tarefas constituintes por modelos de
linguagem e validação humana.

Este notebook prepara uma base de dados que junta os microdados da
**PNAD Contínua** (Pesquisa Nacional por Amostra de Domicílios Contínua,
IBGE, 3º trimestre de 2025) ao **índice de exposição à IA generativa da
OIT**, para depois ser aplicada para caracterizar a exposição do mercado
de trabalho brasileiro a essa tecnologia.

### Objetivo

Construir a base analítica que une PNAD Contínua e o índice de exposição
à IA (ILO), com ocupações em COD e ISCO-08.

**Entradas:** Microdados PNAD (BigQuery), planilha ILO (Gmyrek et al.,
2025), estrutura COD.  
**Saída principal:** `data/output/pnad_ilo_merged.csv`

### Referências principais

- Gmyrek, P., Berg, J. & Cappelli, D. (2025). *Generative AI and Jobs:
  An updated global assessment of potential effects on job quantity and
  quality*. ILO Working Paper 140.
- IBGE. *Pesquisa Nacional por Amostra de Domicílios Contínua* (PNADc),
  3º trimestre de 2025.

### 1. Configuração do ambiente

Definir caminhos, importar bibliotecas e configurar logs.

``` python
# Instalar dependências no kernel atual (executar apenas uma vez)
%pip install pandas numpy pyarrow openpyxl basedosdados --quiet
```


    [notice] A new release of pip is available: 24.2 -> 26.0.1
    [notice] To update, run: python3.10 -m pip install --upgrade pip
    Note: you may need to restart the kernel to use updated packages.

``` python
# Etapa 1.1 - Preparação de Dados - Configuração do ambiente

import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import re

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos (relativos ao diretório do notebook)
# ---------------------------------------------------------------------------
DATA_INPUT     = Path("../../data/input")
DATA_RAW       = Path("../../data/raw")
DATA_PROCESSED = Path("../../data/processed")
DATA_OUTPUT    = Path("../../data/output")

for d in [DATA_RAW, DATA_PROCESSED, DATA_OUTPUT]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parâmetros PNAD / GCP
# ---------------------------------------------------------------------------
GCP_PROJECT_ID  = "mestrado-pnad-2026"
PNAD_ANO        = 2025
PNAD_TRIMESTRE  = 3  
SALARIO_MINIMO  = 1518  # Valor vigente em Q3/2025 (R$)

# ---------------------------------------------------------------------------
# Arquivo ILO (já copiado para data/input)
# ---------------------------------------------------------------------------
ILO_FILE = DATA_INPUT / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"

# ---------------------------------------------------------------------------
# Mapeamentos
# ---------------------------------------------------------------------------
REGIAO_MAP = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte',
    'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste',
    'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste',
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
    '9': 'Ocupações elementares',
}

RACA_AGREGADA_MAP = {
    '1': 'Branca',
    '2': 'Negra',   # Preta
    '4': 'Negra',   # Parda
    '3': 'Outras',  # Amarela
    '5': 'Outras',  # Indígena
    '9': 'Outras',  # Sem declaração
}

POSICAO_FORMAL = ['1', '3', '5']  # Empregado c/ carteira, Militar, Empregador

IDADE_BINS   = [0, 25, 35, 45, 55, 100]
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
# Funções utilitárias – estatísticas ponderadas
# ---------------------------------------------------------------------------
def weighted_mean(values, weights):
    """Média ponderada (ignora NaN)."""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    return np.average(values[mask], weights=weights[mask])

def weighted_std(values, weights):
    """Desvio-padrão ponderado (ignora NaN)."""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    avg = np.average(values[mask], weights=weights[mask])
    variance = np.average((values[mask] - avg) ** 2, weights=weights[mask])
    return np.sqrt(variance)

def weighted_quantile(values, weights, quantile):
    """Quantil ponderado por pesos amostrais (ignora NaN).
    Fonte: adaptado de etapa1_ia_generativa/src/utils/weighted_stats.py
    """
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    sorted_idx = np.argsort(values[mask])
    sorted_values = values[mask].iloc[sorted_idx]
    sorted_weights = weights[mask].iloc[sorted_idx]
    cumsum = np.cumsum(sorted_weights)
    cutoff = quantile * cumsum.iloc[-1]
    return sorted_values.iloc[np.searchsorted(cumsum, cutoff)]

def weighted_qcut(values, weights, q, labels=None):
    """Classificação em quantis ponderados por peso amostral.

    Diferente de pd.qcut (que divide por contagem de linhas), esta função
    calcula os breakpoints de modo que cada faixa represente ~1/q da
    POPULAÇÃO (soma dos pesos), não da amostra.

    Parâmetros:
        values  : pd.Series com os valores a classificar
        weights : pd.Series com os pesos amostrais
        q       : int, número de quantis (5 = quintis, 10 = decis)
        labels  : lista de labels (len == q), ou None para retornar inteiros 1..q

    Retorna:
        pd.Series (Categorical) com os labels atribuídos
    """
    mask = values.notna() & weights.notna()
    breakpoints = [values[mask].min() - 1e-10]  # incluir mínimo
    for i in range(1, q):
        bp = weighted_quantile(values[mask], weights[mask], i / q)
        breakpoints.append(bp)
    breakpoints.append(values[mask].max() + 1e-10)  # incluir máximo

    # Remover duplicatas mantendo ordem (pode acontecer com valores concentrados)
    breakpoints = sorted(set(breakpoints))

    if labels is not None and len(labels) != len(breakpoints) - 1:
        labels = None  # fallback se breakpoints colapsaram

    result = pd.cut(values, bins=breakpoints, labels=labels, include_lowest=True)
    return result

print("Configuração carregada com sucesso.")
print(f"  PNAD: {PNAD_ANO} Q{PNAD_TRIMESTRE}")
print(f"  Projeto GCP: {GCP_PROJECT_ID}")
print(f"  Salário mínimo: R$ {SALARIO_MINIMO}")
print(f"  ILO file: {ILO_FILE} (existe: {ILO_FILE.exists()})")
print(f"  Setores CNAE mapeados: {len(set(CNAE_SETOR_MAP.values()))} categorias")
print(f"  Setores críticos IA: {SETORES_CRITICOS_IA}")
```

    Configuração carregada com sucesso.
      PNAD: 2025 Q3
      Projeto GCP: mestrado-pnad-2026
      Salário mínimo: R$ 1518
      ILO file: data/input/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx (existe: True)
      Setores CNAE mapeados: 19 categorias
      Setores críticos IA: ['Informação e Comunicação', 'Finanças e Seguros', 'Serviços Profissionais']

### 2a. Download dos microdados PNAD

Extrair da PNAD Contínua (BigQuery) as variáveis necessárias para o
trimestre/ano definido. **Saída:** `data/raw/pnad_*.parquet`

#### Ficha técnica dos dados

| Item              | Descrição                                            |
|-------------------|------------------------------------------------------|
| **Fonte**         | PNAD Contínua (PNADc), IBGE                          |
| **Período**       | 3º trimestre de 2025                                 |
| **Acesso**        | Base dos Dados (BigQuery)                            |
| **Peso amostral** | V1028 (projeção de população para dados trimestrais) |
| **Universo**      | População ocupada com código de ocupação válido      |

#### Variáveis selecionadas

| Variável IBGE | Nome no dataset | Descrição |
|----|----|----|
| V2007 | `sexo` | Sexo biológico |
| V2009 | `idade` | Idade em anos |
| V2010 | `raca_cor` | Cor ou raça (autoclassificação) |
| VD3004 | `nivel_instrucao` | Nível de instrução mais elevado alcançado |
| V4010 | `cod_ocupacao` | Código de ocupação (COD, 4 dígitos) |
| V4013 | `grupamento_atividade` | Grupamento de atividade (CNAE Domiciliar 2.0) |
| VD4009 | `posicao_ocupacao` | Posição na ocupação |
| VD4016 | `rendimento_habitual` | Rendimento mensal habitual do trabalho principal |
| VD4020 | `rendimento_efetivo` | Rendimento mensal efetivo do trabalho principal |
| VD4031 | `horas_habituais` | Horas habitualmente trabalhadas (todos os trabalhos) |
| VD4035 | `horas_efetivas` | Horas efetivamente trabalhadas na semana de referência |
| V1028 | `peso` | Peso amostral (projeção de população) |

> **Nota metodológica — Variáveis de renda:** O rendimento mensal
> habitual (`VD4016`) é a variável primária para análises estruturais de
> exposição ocupacional, por ser menos volátil que o rendimento efetivo
> (`VD4020`), que captura flutuações mensais por horas extras, bônus,
> etc. (Cf. IBGE, Notas Metodológicas PNAD Contínua, 2023). Ambas são
> mantidas na base.

> **Nota metodológica — Horas trabalhadas:** Utiliza-se `VD4031` (horas
> habitualmente trabalhadas em todos os trabalhos, variável derivada
> IBGE) como variável principal de jornada, por ter cobertura superior à
> variável bruta `V4019` (~30% de preenchimento na versão anterior).
> `VD4035` (horas efetivamente trabalhadas na semana de referência) é
> incluída para análises de sazonalidade e produtividade.

> **Nota metodológica — Inclusão de todos os ocupados:** A query inclui
> **todos os ocupados com código de ocupação válido**, independentemente
> de terem renda declarada. O filtro de renda é aplicado via flag
> `tem_renda` na etapa de limpeza (4a).

> **Nota metodológica — Variáveis indisponíveis:** As variáveis `V4040`
> (tempo no emprego atual) e `V4018` (porte da empresa) não estão
> populadas na fonte utilizada (Base dos Dados/BigQuery) para o período
> analisado (Q3/2025), sendo portanto excluídas desta análise.

``` python
# Etapa 1.2a - Preparação de Dados - Download dos microdados PNAD
# Lógica: se o parquet já existe em data/raw/, carrega direto; senão, baixa do BigQuery.

pnad_files = sorted(DATA_RAW.glob("pnad_*.parquet"))

if pnad_files:
    # --- Caminho rápido: arquivo local já disponível ---
    pnad_path = pnad_files[-1]  # mais recente
    print(f"Arquivo PNAD encontrado localmente: {pnad_path.name}")
    df_pnad_raw = pd.read_parquet(pnad_path)
    print(f"Carregado: {len(df_pnad_raw):,} observações")

    # Validar que o arquivo corresponde à configuração
    match = re.search(r"pnad_(\d{4})q(\d)", pnad_path.name)
    if match:
        ano_arquivo, trim_arquivo = int(match.group(1)), int(match.group(2))
        if ano_arquivo != PNAD_ANO or trim_arquivo != PNAD_TRIMESTRE:
            print(f"  WARNING: Arquivo é {ano_arquivo} Q{trim_arquivo}, "
                  f"mas config diz {PNAD_ANO} Q{PNAD_TRIMESTRE}!")
            print(f"  Atualizando variáveis de config para corresponder aos dados.")
            PNAD_ANO = ano_arquivo
            PNAD_TRIMESTRE = trim_arquivo
        else:
            print(f"  OK: Arquivo corresponde à configuração ({PNAD_ANO} Q{PNAD_TRIMESTRE})")

else:
    # --- Caminho completo: download via BigQuery ---
    print("Nenhum arquivo PNAD local encontrado. Iniciando download do BigQuery...")
    import basedosdados as bd

    # Verificar trimestres disponíveis
    query_check = """
    SELECT DISTINCT ano, trimestre, COUNT(*) as n_obs
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano >= 2024
    GROUP BY ano, trimestre
    ORDER BY ano DESC, trimestre DESC
    LIMIT 5
    """
    df_check = bd.read_sql(query_check, billing_project_id=GCP_PROJECT_ID)
    print(f"Trimestres disponíveis:\n{df_check}")

    trimestre_existe = len(
        df_check[(df_check['ano'] == PNAD_ANO) & (df_check['trimestre'] == PNAD_TRIMESTRE)]
    ) > 0

    if trimestre_existe:
        ano_usar, trim_usar = PNAD_ANO, PNAD_TRIMESTRE
    else:
        ano_usar = int(df_check.iloc[0]['ano'])
        trim_usar = int(df_check.iloc[0]['trimestre'])
        print(f"AVISO: {PNAD_ANO} Q{PNAD_TRIMESTRE} indisponível. Usando {ano_usar} Q{trim_usar}")
        PNAD_ANO = ano_usar
        PNAD_TRIMESTRE = trim_usar

    query = f"""
    SELECT
        ano,
        trimestre,
        sigla_uf,
        v2007  AS sexo,
        v2009  AS idade,
        v2010  AS raca_cor,
        vd3004 AS nivel_instrucao,
        v4010  AS cod_ocupacao,
        v4013  AS grupamento_atividade,
        vd4009 AS posicao_ocupacao,
        vd4016 AS rendimento_habitual,
        vd4020 AS rendimento_efetivo,
        vd4031 AS horas_habituais,
        vd4035 AS horas_efetivas,
        v1028  AS peso
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano = {ano_usar}
      AND trimestre = {trim_usar}
      AND v4010 IS NOT NULL
    """

    print(f"Executando query para {ano_usar} Q{trim_usar} (pode demorar 2-5 min)...")
    df_pnad_raw = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID)

    # Salvar parquet
    ano_real = int(df_pnad_raw['ano'].iloc[0])
    trim_real = int(df_pnad_raw['trimestre'].iloc[0])
    output_path = DATA_RAW / f"pnad_{ano_real}q{trim_real}.parquet"
    df_pnad_raw.to_parquet(output_path, index=False)
    print(f"Salvo em: {output_path}")

print(f"\ndf_pnad_raw: {df_pnad_raw.shape[0]:,} linhas x {df_pnad_raw.shape[1]} colunas")
print(f"Período: {PNAD_ANO} Q{PNAD_TRIMESTRE}")
```

    Arquivo PNAD encontrado localmente: pnad_2025q3.parquet
    Carregado: 220,091 observações
      OK: Arquivo corresponde à configuração (2025 Q3)

    df_pnad_raw: 220,091 linhas x 15 colunas
    Período: 2025 Q3

### 2b. Verificar dados microdados PNAD (CHECKPOINT)

Verificar dados gerados

``` python
# Etapa 1.2b - Preparação de Dados - Verificar dados microdados PNAD

print("=" * 60)
print("CHECKPOINT - Microdados PNAD")
print("=" * 60)

print(f"\nShape: {df_pnad_raw.shape}")
print(f"Colunas: {list(df_pnad_raw.columns)}")

# UFs
n_ufs = df_pnad_raw['sigla_uf'].nunique()
print(f"\nUFs presentes: {n_ufs}")
if n_ufs != 27:
    print(f"  WARNING: Esperado 27 UFs, encontrado {n_ufs}")

# População
pop_milhoes = df_pnad_raw['peso'].sum() / 1e6
print(f"População representada: {pop_milhoes:.1f} milhões")

# Linhas
if len(df_pnad_raw) < 100_000:
    print(f"  WARNING: Apenas {len(df_pnad_raw):,} linhas (esperado > 100.000)")

# Verificar preenchimento das variáveis-chave
print(f"\nPreenchimento das variáveis:")
for col in df_pnad_raw.columns:
    n_valid = df_pnad_raw[col].notna().sum()
    pct = n_valid / len(df_pnad_raw) * 100
    flag = "  " if pct > 80 else "  WARNING -" if pct > 50 else "  CRITICO -"
    print(f"{flag} {col}: {n_valid:,} ({pct:.1f}%)")

# Tipos
print(f"\nDtypes:\n{df_pnad_raw.dtypes}")

# Amostra
print("\nPrimeiras linhas:")
df_pnad_raw.head()
```

    ============================================================
    CHECKPOINT - Microdados PNAD
    ============================================================

    Shape: (220091, 15)
    Colunas: ['ano', 'trimestre', 'sigla_uf', 'sexo', 'idade', 'raca_cor', 'nivel_instrucao', 'cod_ocupacao', 'grupamento_atividade', 'posicao_ocupacao', 'rendimento_habitual', 'rendimento_efetivo', 'horas_habituais', 'horas_efetivas', 'peso']

    UFs presentes: 27
    População representada: 102.4 milhões

    Preenchimento das variáveis:
       ano: 220,091 (100.0%)
       trimestre: 220,091 (100.0%)
       sigla_uf: 220,091 (100.0%)
       sexo: 220,091 (100.0%)
       idade: 220,091 (100.0%)
       raca_cor: 220,091 (100.0%)
       nivel_instrucao: 220,091 (100.0%)
       cod_ocupacao: 220,091 (100.0%)
       grupamento_atividade: 220,091 (100.0%)
       posicao_ocupacao: 220,091 (100.0%)
       rendimento_habitual: 215,370 (97.9%)
       rendimento_efetivo: 215,405 (97.9%)
       horas_habituais: 220,091 (100.0%)
       horas_efetivas: 220,091 (100.0%)
       peso: 220,091 (100.0%)

    Dtypes:
    ano                       Int64
    trimestre                 Int64
    sigla_uf                 object
    sexo                     object
    idade                     Int64
    raca_cor                 object
    nivel_instrucao          object
    cod_ocupacao             object
    grupamento_atividade     object
    posicao_ocupacao         object
    rendimento_habitual     float64
    rendimento_efetivo      float64
    horas_habituais           Int64
    horas_efetivas            Int64
    peso                    float64
    dtype: object

    Primeiras linhas:

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | ano | trimestre | sigla_uf | sexo | idade | raca_cor | nivel_instrucao | cod_ocupacao | grupamento_atividade | posicao_ocupacao | rendimento_habitual | rendimento_efetivo | horas_habituais | horas_efetivas | peso |
|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
| 0 | 2025 | 3 | RR | 1 | 47 | 4 | 4 | 8322 | 49030 | 9 | 3000.0 | 2800.0 | 28 | 22 | 80.230030 |
| 1 | 2025 | 3 | DF | 2 | 35 | 1 | 5 | 4120 | 78000 | 1 | 2000.0 | 3600.0 | 80 | 80 | 273.396289 |
| 2 | 2025 | 3 | SE | 1 | 62 | 4 | 2 | 5414 | 85012 | 7 | 2000.0 | 2000.0 | 18 | 18 | 216.050334 |
| 3 | 2025 | 3 | SE | 2 | 40 | 4 | 5 | 5221 | 56011 | 8 | 5000.0 | 5000.0 | 52 | 52 | 275.005513 |
| 4 | 2025 | 3 | SE | 2 | 34 | 4 | 5 | 5212 | 56020 | 9 | 1200.0 | 1200.0 | 26 | 26 | 201.275603 |

</div>

### 3a. Processar índice de exposição ILO

Lê a planilha ILO com scores de exposição por ISCO-08, padroniza e gera
níveis

``` python
# Etapa 1.3a - Preparação de Dados - Processar índice de exposição ILO

print(f"Lendo arquivo ILO: {ILO_FILE}")
df_ilo_raw = pd.read_excel(ILO_FILE)
print(f"Linhas raw (tarefas): {len(df_ilo_raw):,}")
print(f"Colunas disponíveis: {list(df_ilo_raw.columns)}")

# Mapeamento de colunas
col_mapping = {
    'ISCO_08': 'isco_08',
    'Title': 'occupation_title',
    'mean_score_2025': 'exposure_score',
    'SD_2025': 'exposure_sd',
    'potential25': 'exposure_gradient',
}

available_cols = [c for c in col_mapping.keys() if c in df_ilo_raw.columns]
print(f"Colunas mapeadas: {available_cols}")

df_ilo_renamed = df_ilo_raw.rename(
    columns={k: v for k, v in col_mapping.items() if k in df_ilo_raw.columns}
)

# Agregar por ocupação (arquivo original tem múltiplas tarefas por ocupação)
df_ilo = df_ilo_renamed.groupby('isco_08').agg({
    'occupation_title': 'first',
    'exposure_score': 'mean',
    'exposure_sd': 'mean',
    'exposure_gradient': 'first',
}).reset_index()

# Garantir formato string com 4 dígitos
df_ilo['isco_08_str'] = df_ilo['isco_08'].astype(str).str.zfill(4)

print(f"\nOcupações únicas: {len(df_ilo):,}")
print(f"Score médio: {df_ilo['exposure_score'].mean():.3f}")
print(f"Score range: [{df_ilo['exposure_score'].min():.3f}, {df_ilo['exposure_score'].max():.3f}]")

# Salvar processado
ilo_output = DATA_PROCESSED / "ilo_exposure_clean.csv"
df_ilo.to_csv(ilo_output, index=False)
print(f"\nSalvo em: {ilo_output}")
```

    Lendo arquivo ILO: data/input/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx
    Linhas raw (tarefas): 3,265
    Colunas disponíveis: ['label4d', 'label1d', 'ISCO_08', 'Title', 'taskID', 'Task_ISCO', 'score_2023', 'Weaviate Status', 'predicted_score_2025_gpt4o', 'prediction_justification_gpt4o', 'weaviate_status_gemini', 'predicted_score_2025_gemini', 'prediction_justification_gemini', 'score_2025', 'source', 'mean_score_2023', 'mean_score_2025', 'SD_2023', 'SD_2025', 'potential25', 'potential23']
    Colunas mapeadas: ['ISCO_08', 'Title', 'mean_score_2025', 'SD_2025', 'potential25']

    Ocupações únicas: 427
    Score médio: 0.297
    Score range: [0.090, 0.700]

    Salvo em: data/processed/ilo_exposure_clean.csv

### 3b. Verificar índice de exposição ILO

Verificar: número de ocupações, coluna de score, distribuição por
gradiente

``` python
# Etapa 1.3b - Preparação de Dados - Verificar índice de exposição ILO

print("=" * 60)
print("CHECKPOINT - Índice ILO")
print("=" * 60)

# Número de ocupações
n_ocup = len(df_ilo)
print(f"\nOcupações: {n_ocup}")
if n_ocup < 400:
    print(f"  WARNING: Poucas ocupações ({n_ocup}). Esperado ~427.")

# Range de scores
score_min = df_ilo['exposure_score'].min()
score_max = df_ilo['exposure_score'].max()
print(f"Score range: [{score_min:.3f}, {score_max:.3f}]")
if score_min < 0 or score_max > 1:
    print(f"  WARNING: Scores fora do intervalo [0, 1]")

# Distribuição por gradiente
print("\nDistribuição por gradiente:")
for grad, count in df_ilo['exposure_gradient'].value_counts().items():
    print(f"  {grad}: {count} ocupações")

# Amostra
print("\nAmostra (5 maiores scores):")
df_ilo.nlargest(5, 'exposure_score')[['isco_08_str', 'occupation_title', 'exposure_score']]
```

    ============================================================
    CHECKPOINT - Índice ILO
    ============================================================

    Ocupações: 427
    Score range: [0.090, 0.700]

    Distribuição por gradiente:
      Not Exposed: 231 ocupações
      Minimal Exposure: 84 ocupações
      Exposed: Gradient 2: 44 ocupações
      Exposed: Gradient 3: 38 ocupações
      Exposed: Gradient 1: 17 ocupações
      Exposed: Gradient 4: 13 ocupações

    Amostra (5 maiores scores):

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | isco_08_str | occupation_title                           | exposure_score |
|-----|-------------|--------------------------------------------|----------------|
| 207 | 4132        | Data Entry Clerks                          | 0.70           |
| 206 | 4131        | Typists and Word Processing Operators      | 0.65           |
| 220 | 4311        | Accounting and Bookkeeping Clerks          | 0.64           |
| 221 | 4312        | Statistical, Finance and Insurance Clerks  | 0.64           |
| 164 | 3311        | Securities and Finance Dealers and Brokers | 0.63           |

</div>

### Notas sobre terminologia

> **Sobre sexo:** A PNADc coleta a variável V2007 (sexo biológico:
> masculino/feminino). Esta pesquisa não coleta identidade de gênero.
> Utilizamos o termo “sexo” ao longo desta análise, em conformidade com
> a terminologia do IBGE.

> **Sobre raça/cor:** Utilizamos a variável V2010 (autoclassificação de
> cor ou raça) com as cinco categorias do IBGE: Branca, Preta, Parda,
> Amarela e Indígena. Quando apresentamos resultados agregados em
> “Negros” (Pretos + Pardos), seguimos a convenção amplamente adotada na
> sociologia e economia do trabalho brasileira (Osorio, 2003; Soares,
> 2008). Resultados desagregados estão disponíveis nos apêndices.

> **Sobre “exposição”:** O índice da OIT mede o potencial de que tarefas
> ocupacionais sejam afetadas pela IA generativa — seja por automação,
> seja por complementação/aumento de produtividade. “Exposição” não é
> sinônimo de “risco de desemprego” ou “ameaça”. Ocupações altamente
> expostas podem tanto perder tarefas quanto ganhar produtividade,
> dependendo do contexto institucional, regulatório e organizacional.

### 4a. Limpeza e variáveis derivadas – PNAD

Filtra população de interesse, cria variáveis derivadas (região, grandes
grupos COD, faixas de renda, etc.) e padroniza códigos de ocupação.

**Entrada:** `data/raw/pnad_*.parquet`.  
**Saída:** `data/processed/pnad_clean.csv`

> **Nota metodológica — Inclusão de todos os ocupados:** A análise de
> exposição inclui todos os ocupados com código de ocupação válido,
> **independentemente de terem renda declarada**. A variável `tem_renda`
> sinaliza trabalhadores com rendimento habitual positivo. Para análises
> de rendimento (tabelas salariais, faixas de renda), filtrar por
> `tem_renda == 1`.

> **Nota metodológica — Faixas de renda em salários mínimos:** Optamos
> por classificar a renda em faixas de salários mínimos (até 1 SM, 1-2
> SM, 2-3 SM, 3-5 SM, 5+ SM) em vez de quintis populacionais. Esta
> escolha se justifica por: (1) a elevada concentração de rendimentos em
> torno de 1 SM no Brasil gera empates que distorcem os quintis (Q1
> absorveria ~31% da população); (2) faixas em SM são mais
> interpretáveis e amplamente utilizadas na literatura brasileira de
> economia do trabalho.

> **Nota metodológica — Winsorização:** Aplicamos winsorização nos
> percentis 1 e 99 da distribuição de rendimento habitual, calculados
> com pesos amostrais (V1028), para limitar a influência de valores
> extremos preservando o tamanho amostral. Esta técnica é preferível ao
> trimming (que descarta observações) e é prática padrão em análises de
> renda com dados de survey.

``` python
# Etapa 1.4a - Preparação de Dados - Limpeza e variáveis derivadas

df_pnad = df_pnad_raw.copy()
n_inicial = len(df_pnad)
print(f"Observações iniciais: {n_inicial:,}")

# ---------------------------------------------------------------------------
# LIMPEZA - Conversão de tipos
# ---------------------------------------------------------------------------
df_pnad['cod_ocupacao'] = df_pnad['cod_ocupacao'].astype(str).str.zfill(4)
df_pnad['idade'] = pd.to_numeric(df_pnad['idade'], errors='coerce')
df_pnad['rendimento_habitual'] = pd.to_numeric(df_pnad['rendimento_habitual'], errors='coerce')
df_pnad['rendimento_efetivo'] = pd.to_numeric(df_pnad['rendimento_efetivo'], errors='coerce')
df_pnad['horas_habituais'] = pd.to_numeric(df_pnad['horas_habituais'], errors='coerce')
df_pnad['horas_efetivas'] = pd.to_numeric(df_pnad['horas_efetivas'], errors='coerce')
df_pnad['peso'] = pd.to_numeric(df_pnad['peso'], errors='coerce')

# ---------------------------------------------------------------------------
# LIMPEZA - Filtros
# ---------------------------------------------------------------------------

# Remover missings críticos (ocupação, idade, peso — NÃO renda)
df_pnad = df_pnad.dropna(subset=['cod_ocupacao', 'idade', 'peso'])
print(f"Após remover missings críticos: {len(df_pnad):,} ({len(df_pnad)/n_inicial:.1%})")

# Filtrar faixa etária (18-65)
df_pnad = df_pnad[(df_pnad['idade'] >= 18) & (df_pnad['idade'] <= 65)]
print(f"Após filtrar 18-65 anos: {len(df_pnad):,} ({len(df_pnad)/n_inicial:.1%})")

# Remover ocupações inválidas
df_pnad = df_pnad[~df_pnad['cod_ocupacao'].isin(['0000', '9999'])]
print(f"Após remover ocupações inválidas: {len(df_pnad):,}")

# ---------------------------------------------------------------------------
# VARIÁVEIS DERIVADAS
# ---------------------------------------------------------------------------

# Flag de renda (em vez de excluir sem renda)
df_pnad['tem_renda'] = (df_pnad['rendimento_habitual'].notna() & (df_pnad['rendimento_habitual'] > 0)).astype(int)
n_sem_renda = (df_pnad['tem_renda'] == 0).sum()
pop_sem_renda = df_pnad.loc[df_pnad['tem_renda'] == 0, 'peso'].sum() / 1e6
print(f"\nTrabalhadores sem renda declarada: {n_sem_renda:,} obs ({pop_sem_renda:.1f} milhões)")

# Formalidade
df_pnad['formal'] = df_pnad['posicao_ocupacao'].astype(str).isin(POSICAO_FORMAL).astype(int)
print(f"Taxa de formalidade: {df_pnad['formal'].mean():.1%}")

# Faixas etárias
df_pnad['faixa_etaria'] = pd.cut(
    df_pnad['idade'], bins=IDADE_BINS, labels=IDADE_LABELS
)

# Região
df_pnad['regiao'] = df_pnad['sigla_uf'].map(REGIAO_MAP)

# Raça agregada
df_pnad['raca_agregada'] = df_pnad['raca_cor'].astype(str).map(RACA_AGREGADA_MAP)

# Grande grupo ocupacional
df_pnad['grande_grupo'] = df_pnad['cod_ocupacao'].str[0].map(GRANDES_GRUPOS)

# Sexo como texto
df_pnad['sexo_texto'] = df_pnad['sexo'].map({1: 'Homem', 2: 'Mulher', '1': 'Homem', '2': 'Mulher'})

# Winsorização de renda (percentis ponderados 1 e 99) — APENAS para quem tem renda
mask_renda = df_pnad['tem_renda'] == 1
p01 = weighted_quantile(
    df_pnad.loc[mask_renda, 'rendimento_habitual'],
    df_pnad.loc[mask_renda, 'peso'], 0.01
)
p99 = weighted_quantile(
    df_pnad.loc[mask_renda, 'rendimento_habitual'],
    df_pnad.loc[mask_renda, 'peso'], 0.99
)
df_pnad['rendimento_winsor'] = df_pnad['rendimento_habitual'].clip(lower=p01, upper=p99)
print(f"Winsorização ponderada: P1 = R$ {p01:,.0f}, P99 = R$ {p99:,.0f}")

# Faixas de renda em salários mínimos
df_pnad['faixa_renda_sm'] = pd.cut(
    df_pnad['rendimento_habitual'] / SALARIO_MINIMO,
    bins=[0, 1, 2, 3, 5, float('inf')],
    labels=['Até 1 SM', '1-2 SM', '2-3 SM', '3-5 SM', '5+ SM'],
    right=True,
    include_lowest=True,
)
print(f"\nDistribuição por faixa de renda (SM = R$ {SALARIO_MINIMO}):")
for faixa, peso in df_pnad[df_pnad['tem_renda'] == 1].groupby('faixa_renda_sm')['peso'].sum().items():
    pct = peso / df_pnad.loc[mask_renda, 'peso'].sum() * 100
    print(f"  {faixa}: {peso/1e6:.1f} milhões ({pct:.1f}%)")

# Verificar preenchimento de horas
n_horas_hab = df_pnad['horas_habituais'].notna().sum()
n_horas_efe = df_pnad['horas_efetivas'].notna().sum()
print(f"\nHoras habituais: {n_horas_hab:,} ({n_horas_hab/len(df_pnad):.1%})")
print(f"Horas efetivas:  {n_horas_efe:,} ({n_horas_efe/len(df_pnad):.1%})")

# ---------------------------------------------------------------------------
# SALVAR
# ---------------------------------------------------------------------------
pnad_clean_path = DATA_PROCESSED / "pnad_clean.csv"
df_pnad.to_csv(pnad_clean_path, index=False)
print(f"\nSalvo em: {pnad_clean_path}")
print(f"df_pnad: {df_pnad.shape[0]:,} linhas x {df_pnad.shape[1]} colunas")
```

    Observações iniciais: 220,091
    Após remover missings críticos: 220,091 (100.0%)
    Após filtrar 18-65 anos: 207,919 (94.5%)
    Após remover ocupações inválidas: 207,901

    Trabalhadores sem renda declarada: 3,759 obs (1.1 milhões)
    Taxa de formalidade: 37.0%
    Winsorização ponderada: P1 = R$ 200, P99 = R$ 21,000

    Distribuição por faixa de renda (SM = R$ 1518):
      Até 1 SM: 30.3 milhões (31.3%)
      1-2 SM: 39.0 milhões (40.4%)
      2-3 SM: 10.1 milhões (10.5%)
      3-5 SM: 9.5 milhões (9.8%)
      5+ SM: 7.8 milhões (8.0%)

    Horas habituais: 207,901 (100.0%)
    Horas efetivas:  207,901 (100.0%)

    Salvo em: data/processed/pnad_clean.csv
    df_pnad: 207,901 linhas x 24 colunas

### 4b. Verificar Limpeza e variáveis derivadas – PNAD

Verificar: número de linhas, colunas criadas, valores faltantes em COD.

``` python
# Etapa 1.4b - Preparação de Dados - Verificar Limpeza e variáveis derivadas

print("=" * 60)
print("CHECKPOINT - Limpeza PNAD")
print("=" * 60)

# Perda de observações
pct_perda = 1 - len(df_pnad) / n_inicial
print(f"\nObservações: {n_inicial:,} -> {len(df_pnad):,} (perda: {pct_perda:.1%})")
if pct_perda > 0.20:
    print(f"  WARNING: Perda de {pct_perda:.1%} das observações (> 20%)")

# Missings em variáveis derivadas
for col in ['regiao', 'raca_agregada', 'grande_grupo', 'faixa_etaria', 'sexo_texto']:
    n_miss = df_pnad[col].isna().sum()
    if n_miss > 0:
        print(f"  WARNING: {col} tem {n_miss:,} valores faltantes")

print(f"\nOcupações únicas (COD): {df_pnad['cod_ocupacao'].nunique()}")
print(f"UFs: {df_pnad['sigla_uf'].nunique()}")
print(f"População representada: {df_pnad['peso'].sum()/1e6:.1f} milhões")

print("\nDistribuição por sexo:")
for sexo, peso in df_pnad.groupby('sexo_texto')['peso'].sum().items():
    print(f"  {sexo}: {peso/1e6:.1f} milhões")

print("\nDistribuição por região:")
for regiao, peso in df_pnad.groupby('regiao')['peso'].sum().sort_values(ascending=False).items():
    print(f"  {regiao}: {peso/1e6:.1f} milhões")

print("\nDistribuição por faixa etária:")
print(df_pnad['faixa_etaria'].value_counts().sort_index())

print("\nDistribuição por faixa de renda (SM):")
print(df_pnad['faixa_renda_sm'].value_counts().sort_index())
```

    ============================================================
    CHECKPOINT - Limpeza PNAD
    ============================================================

    Observações: 220,091 -> 207,901 (perda: 5.5%)
      WARNING: grande_grupo tem 1,671 valores faltantes

    Ocupações únicas (COD): 428
    UFs: 27
    População representada: 97.8 milhões

    Distribuição por sexo:
      Homem: 55.0 milhões
      Mulher: 42.8 milhões

    Distribuição por região:
      Sudeste: 43.4 milhões
      Nordeste: 22.3 milhões
      Sul: 15.7 milhões
      Centro-Oeste: 8.5 milhões
      Norte: 7.8 milhões

    Distribuição por faixa etária:
    faixa_etaria
    18-24    29595
    25-34    48629
    35-44    55588
    45-54    46136
    55+      27953
    Name: count, dtype: int64

    Distribuição por faixa de renda (SM):
    faixa_renda_sm
    Até 1 SM    74904
    1-2 SM      77010
    2-3 SM      19520
    3-5 SM      18120
    5+ SM       14588
    Name: count, dtype: int64

### 5a. Crosswalk COD → ISCO-08

Mapear códigos de ocupação COD (PNAD) para ISCO-08 para permitir o merge
com o índice ILO.

#### Estratégia de correspondência

A COD (Classificação de Ocupações para Pesquisas Domiciliares) do IBGE é
derivada diretamente da ISCO-08 da OIT. Os códigos compartilham a mesma
estrutura hierárquica de 4 dígitos, com o primeiro dígito representando
os mesmos 9 grandes grupos ocupacionais (Fonte: IBGE, Nota Técnica COD
2010). Isso permite um match direto de string entre COD e ISCO-08 na
maioria dos casos.

Adotamos uma estratégia de correspondência hierárquica para maximizar a
cobertura:

1.  **4 dígitos (exato):** match direto COD ↔ ISCO-08. Cobre ~98% das
    observações.
2.  **3 dígitos (subgrupo):** para códigos COD sem equivalente exato na
    ISCO-08, atribui-se a média do subgrupo (3 primeiros dígitos). Cobre
    ~1-2% adicional.
3.  **2 dígitos (grupo menor):** fallback para o grupo de 2 dígitos.
4.  **1 dígito (grande grupo):** fallback final para o grande grupo
    ocupacional.

**Limitação:** Não há validação semântica título-a-título; possíveis
“falsos cognatos numéricos” são mitigados pelos sanity checks por grande
grupo (verificação de que a ordenação de exposição por grande grupo é
coerente com a literatura).

``` python
# Etapa 1.5a - Preparação de Dados - Crosswalk COD → ISCO-08

# Garantir formatos string
df_ilo['isco_08_str'] = df_ilo['isco_08_str'].astype(str).str.zfill(4)
df_pnad['cod_ocupacao'] = df_pnad['cod_ocupacao'].astype(str).str.zfill(4)

print(f"PNAD: {len(df_pnad):,} observações")
print(f"ILO:  {len(df_ilo):,} ocupações ISCO-08")

# ---------------------------------------------------------------------------
# Criar dicionários de lookup em cada nível hierárquico
# ---------------------------------------------------------------------------
ilo_4d = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()
ilo_3d = df_ilo.groupby(df_ilo['isco_08_str'].str[:3])['exposure_score'].mean().to_dict()
ilo_2d = df_ilo.groupby(df_ilo['isco_08_str'].str[:2])['exposure_score'].mean().to_dict()
ilo_1d = df_ilo.groupby(df_ilo['isco_08_str'].str[:1])['exposure_score'].mean().to_dict()

# Lookup do gradiente oficial ILO (potential25) — apenas para match 4-digit
ilo_gradient_4d = df_ilo.groupby('isco_08_str')['exposure_gradient'].first().to_dict()

print(f"\nCódigos ILO: 4d={len(ilo_4d)}, 3d={len(ilo_3d)}, 2d={len(ilo_2d)}, 1d={len(ilo_1d)}")

# ---------------------------------------------------------------------------
# Crosswalk hierárquico (4 → 3 → 2 → 1 dígito)
# ---------------------------------------------------------------------------
df_crosswalked = df_pnad.copy()
df_crosswalked['exposure_score'] = np.nan
df_crosswalked['exposure_gradient'] = None
df_crosswalked['match_level'] = None

# Nível 4-digit
mask_4d = df_crosswalked['cod_ocupacao'].isin(ilo_4d.keys())
df_crosswalked.loc[mask_4d, 'exposure_score'] = df_crosswalked.loc[mask_4d, 'cod_ocupacao'].map(ilo_4d)
df_crosswalked.loc[mask_4d, 'exposure_gradient'] = df_crosswalked.loc[mask_4d, 'cod_ocupacao'].map(ilo_gradient_4d)
df_crosswalked.loc[mask_4d, 'match_level'] = '4-digit'
print(f"\nMatch 4-digit: {mask_4d.sum():,} ({mask_4d.mean():.1%})")

# Nível 3-digit
mask_missing = df_crosswalked['exposure_score'].isna()
cod_3d = df_crosswalked.loc[mask_missing, 'cod_ocupacao'].str[:3]
mask_3d = cod_3d.isin(ilo_3d.keys())
idx_3d = mask_missing[mask_missing].index[mask_3d.values]
df_crosswalked.loc[idx_3d, 'exposure_score'] = cod_3d[mask_3d].map(ilo_3d).values
df_crosswalked.loc[idx_3d, 'exposure_gradient'] = 'Sem classificação'
df_crosswalked.loc[idx_3d, 'match_level'] = '3-digit'
print(f"Match 3-digit: {len(idx_3d):,} ({len(idx_3d)/len(df_crosswalked):.1%})")

# Nível 2-digit
mask_missing = df_crosswalked['exposure_score'].isna()
cod_2d = df_crosswalked.loc[mask_missing, 'cod_ocupacao'].str[:2]
mask_2d = cod_2d.isin(ilo_2d.keys())
idx_2d = mask_missing[mask_missing].index[mask_2d.values]
df_crosswalked.loc[idx_2d, 'exposure_score'] = cod_2d[mask_2d].map(ilo_2d).values
df_crosswalked.loc[idx_2d, 'exposure_gradient'] = 'Sem classificação'
df_crosswalked.loc[idx_2d, 'match_level'] = '2-digit'
print(f"Match 2-digit: {len(idx_2d):,} ({len(idx_2d)/len(df_crosswalked):.1%})")

# Nível 1-digit
mask_missing = df_crosswalked['exposure_score'].isna()
cod_1d = df_crosswalked.loc[mask_missing, 'cod_ocupacao'].str[:1]
mask_1d = cod_1d.isin(ilo_1d.keys())
idx_1d = mask_missing[mask_missing].index[mask_1d.values]
df_crosswalked.loc[idx_1d, 'exposure_score'] = cod_1d[mask_1d].map(ilo_1d).values
df_crosswalked.loc[idx_1d, 'exposure_gradient'] = 'Sem classificação'
df_crosswalked.loc[idx_1d, 'match_level'] = '1-digit'
print(f"Match 1-digit: {len(idx_1d):,} ({len(idx_1d)/len(df_crosswalked):.1%})")

# Sem match
n_sem_match = df_crosswalked['exposure_score'].isna().sum()
df_crosswalked.loc[df_crosswalked['exposure_score'].isna(), 'exposure_gradient'] = 'Sem classificação'
print(f"Sem match:     {n_sem_match:,} ({n_sem_match/len(df_crosswalked):.1%})")
```

    PNAD: 207,901 observações
    ILO:  427 ocupações ISCO-08

    Códigos ILO: 4d=427, 3d=127, 2d=40, 1d=9

    Match 4-digit: 203,617 (97.9%)
    Match 3-digit: 2,613 (1.3%)
    Match 2-digit: 0 (0.0%)
    Match 1-digit: 0 (0.0%)
    Sem match:     1,671 (0.8%)

### 5a. Verificar Crosswalk COD → ISCO-08

Verificar: cobertura do crosswalk (percentual de linhas com ISCO
preenchido).

``` python
# Etapa 1.5b - Preparação de Dados - Verificar Crosswalk COD → ISCO-08

print("=" * 60)
print("CHECKPOINT - Crosswalk COD → ISCO-08")
print("=" * 60)

# Cobertura total
coverage = df_crosswalked['exposure_score'].notna().mean()
print(f"\nCobertura total: {coverage:.1%}")
if coverage < 0.90:
    print(f"  WARNING: Cobertura {coverage:.1%} abaixo de 90%")

# Distribuição por nível de match
print("\nDistribuição por nível de match:")
for level, count in df_crosswalked['match_level'].value_counts().items():
    pct = count / len(df_crosswalked) * 100
    print(f"  {level}: {count:,} ({pct:.1f}%)")

# FIX 3: Verificar concentração em match genérico (fallback)
n_total = len(df_crosswalked)
n_generic = df_crosswalked['match_level'].isin(['1-digit', '2-digit']).sum()
pct_generic = n_generic / n_total * 100
print(f"\nMatch genérico (1-digit + 2-digit): {n_generic:,} ({pct_generic:.1f}%)")
if pct_generic > 5:
    print(f"  WARNING: {pct_generic:.1f}% caiu em match genérico (>5%). "
          "Scores podem não refletir a ocupação real.")
else:
    print(f"  OK: Apenas {pct_generic:.1f}% em match genérico.")

# Estatísticas de score
print(f"\nEstatísticas do exposure_score:")
print(f"  Média:  {df_crosswalked['exposure_score'].mean():.3f}")
print(f"  Std:    {df_crosswalked['exposure_score'].std():.3f}")
print(f"  Min:    {df_crosswalked['exposure_score'].min():.3f}")
print(f"  Max:    {df_crosswalked['exposure_score'].max():.3f}")

# Sanity check: exposição por grande grupo
print("\nExposição média por grande grupo (sanity check):")
exp_grupos = df_crosswalked.groupby('grande_grupo').apply(
    lambda x: weighted_mean(x['exposure_score'].dropna(), x.loc[x['exposure_score'].notna(), 'peso'])
).sort_values(ascending=False)

for grupo, score in exp_grupos.items():
    print(f"  {grupo}: {score:.3f}")

# Validações de sanidade
print("\nVALIDAÇÃO DE SANIDADE:")
if 'Profissionais das ciências' in exp_grupos.index:
    val = exp_grupos['Profissionais das ciências']
    if val > 0.30:
        print(f"  OK - Profissionais das ciências com exposição ALTA ({val:.3f})")
    else:
        print(f"  WARNING: Profissionais das ciências com exposição BAIXA ({val:.3f}). Esperado > 0.30")

if 'Ocupações elementares' in exp_grupos.index:
    val = exp_grupos['Ocupações elementares']
    if val < 0.20:
        print(f"  OK - Ocupações elementares com exposição BAIXA ({val:.3f})")
    else:
        print(f"  WARNING: Ocupações elementares com exposição ALTA ({val:.3f}). Esperado < 0.20")
```

    ============================================================
    CHECKPOINT - Crosswalk COD → ISCO-08
    ============================================================

    Cobertura total: 99.2%

    Distribuição por nível de match:
      4-digit: 203,617 (97.9%)
      3-digit: 2,613 (1.3%)

    Match genérico (1-digit + 2-digit): 0 (0.0%)
      OK: Apenas 0.0% em match genérico.

    Estatísticas do exposure_score:
      Média:  0.265
      Std:    0.144
      Min:    0.090
      Max:    0.700

    Exposição média por grande grupo (sanity check):
      Apoio administrativo: 0.554
      Dirigentes e gerentes: 0.400
      Profissionais das ciências: 0.353
      Técnicos nível médio: 0.345
      Serviços e vendedores: 0.305
      Operadores de máquinas: 0.223
      Agropecuária qualificada: 0.174
      Indústria qualificada: 0.151
      Ocupações elementares: 0.130

    VALIDAÇÃO DE SANIDADE:
      OK - Profissionais das ciências com exposição ALTA (0.353)
      OK - Ocupações elementares com exposição BAIXA (0.130)

### 6. Merge final – PNAD + índice ILO

Juntar a base PNAD (com ISCO-08) ao índice ILO por código de ocupação.
Gera a base analítica final da Etapa 1. **Saída:**
`data/output/pnad_ilo_merged.csv`

#### Classificação de exposição

Utilizamos a classificação oficial do WP140 da OIT (Tabela 5), que
categoriza ocupações em 6 níveis de exposição com base em critérios
bivariados — a média (μ) e o desvio-padrão (σ) dos scores de tarefa:

| Categoria | Descrição |
|----|----|
| Not Exposed | Exposição negligenciável |
| Minimal Exposure | Exposição mínima |
| Gradient 1 | Exposição baixa (alto potencial de aumento de produtividade) |
| Gradient 2 | Exposição moderada-baixa |
| Gradient 3 | Exposição moderada-alta |
| Gradient 4 | Exposição alta (maior potencial de automação) |

Esta classificação vem pré-computada na coluna `potential25` do dataset
publicado pela OIT (Gmyrek, Berg & Cappelli, 2025). Verificamos a
consistência reproduzindo a lógica bivariada da Tabela 5, obtendo 99,1%
de concordância (423/427 ocupações). Os 4 mismatches são casos de
fronteira.

Para ocupações com match hierárquico (3 dígitos), onde não há
classificação individual disponível, atribuímos a categoria “Sem
classificação”. O score numérico (`exposure_score`) permanece disponível
para essas ocupações.

``` python
# Etapa 1.6 - Preparação de Dados - Merge final PNAD + ILO

df_final = df_crosswalked.copy()

# ---------------------------------------------------------------------------
# Checkpoint de qualidade do merge
# ---------------------------------------------------------------------------
n_com_score = df_final['exposure_score'].notna().sum()
n_sem_score = df_final['exposure_score'].isna().sum()
pct_pop_perdida = df_final.loc[df_final['exposure_score'].isna(), 'peso'].sum() / df_final['peso'].sum() * 100

print("=" * 60)
print("CHECKPOINT - Qualidade do Merge")
print("=" * 60)
print(f"Observações totais:     {len(df_final):,}")
print(f"Com score de exposição: {n_com_score:,}")
print(f"Sem score (NaN):        {n_sem_score:,}")
print(f"% pop. sem score:       {pct_pop_perdida:.1f}%")

# ---------------------------------------------------------------------------
# Distribuição por gradiente ILO (potential25)
# ---------------------------------------------------------------------------
print("\nDistribuição por gradiente ILO (potential25):")
for grad, peso in df_final.groupby('exposure_gradient')['peso'].sum().sort_values(ascending=False).items():
    print(f"  {grad}: {peso/1e6:.1f} milhões")

# ---------------------------------------------------------------------------
# Quintis e decis de EXPOSIÇÃO — ponderados por peso amostral
# Usa weighted_qcut (definida na célula 1) para que cada faixa represente
# ~20% (quintis) ou ~10% (decis) da POPULAÇÃO, não da amostra.
# ---------------------------------------------------------------------------
mask_valid = df_final['exposure_score'].notna()

df_final.loc[mask_valid, 'quintil_exposure'] = weighted_qcut(
    df_final.loc[mask_valid, 'exposure_score'],
    df_final.loc[mask_valid, 'peso'],
    q=5,
    labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)'],
)

df_final.loc[mask_valid, 'decil_exposure'] = weighted_qcut(
    df_final.loc[mask_valid, 'exposure_score'],
    df_final.loc[mask_valid, 'peso'],
    q=10,
    labels=[f'D{i}' for i in range(1, 11)],
)

# Verificar distribuição populacional dos quintis de exposição
print("\nPopulação por quintil de exposição (deve ser ~20% cada):")
for q, peso in df_final.groupby('quintil_exposure')['peso'].sum().items():
    pct = peso / df_final.loc[mask_valid, 'peso'].sum() * 100
    print(f"  {q}: {peso/1e6:.1f} milhões ({pct:.1f}%)")

# ---------------------------------------------------------------------------
# Agregação setorial — CNAE Domiciliar 2.0, Seções A-T (IBGE)
# Usa CNAE_SETOR_MAP definido na célula de configuração.
# ---------------------------------------------------------------------------
df_final['cnae_2d'] = df_final['grupamento_atividade'].astype(str).str[:2]
df_final['setor_agregado'] = df_final['cnae_2d'].map(CNAE_SETOR_MAP).fillna('Outros Serviços')

# Flag de setores críticos para IA
# Ref: Gmyrek et al. (2024); Eloundou et al. (2023)
df_final['setor_critico_ia'] = df_final['setor_agregado'].isin(SETORES_CRITICOS_IA).astype(int)

print(f"\nSetores: {df_final['setor_agregado'].nunique()} categorias")
print(f"Trabalhadores em setores críticos IA: {df_final.loc[df_final['setor_critico_ia']==1, 'peso'].sum()/1e6:.1f} milhões")

print("\nDistribuição por setor:")
for setor, peso in df_final.groupby('setor_agregado')['peso'].sum().sort_values(ascending=False).items():
    flag = " *" if setor in SETORES_CRITICOS_IA else ""
    print(f"  {setor}: {peso/1e6:.1f} milhões{flag}")

# ---------------------------------------------------------------------------
# Selecionar colunas finais e salvar
# ---------------------------------------------------------------------------
cols_output = [
    'ano', 'trimestre', 'sigla_uf', 'regiao',
    'sexo', 'sexo_texto', 'idade', 'faixa_etaria',
    'raca_cor', 'raca_agregada', 'nivel_instrucao',
    'cod_ocupacao', 'grande_grupo',
    'grupamento_atividade', 'setor_agregado', 'setor_critico_ia',
    'posicao_ocupacao', 'formal', 'tem_renda',
    'rendimento_habitual', 'rendimento_winsor', 'rendimento_efetivo',
    'horas_habituais', 'horas_efetivas',
    'faixa_renda_sm',
    'peso',
    'exposure_score', 'exposure_gradient', 'match_level',
    'quintil_exposure', 'decil_exposure',
]

df_final = df_final[[c for c in cols_output if c in df_final.columns]]

output_path = DATA_OUTPUT / "pnad_ilo_merged.csv"
df_final.to_csv(output_path, index=False)

# ---------------------------------------------------------------------------
# Resumo final
# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
print("BASE FINAL CONSOLIDADA")
print(f"{'=' * 60}")
print(f"Observações:       {len(df_final):,}")
print(f"Com score:         {df_final['exposure_score'].notna().sum():,}")
print(f"Cobertura:         {df_final['exposure_score'].notna().mean():.1%}")
print(f"Colunas:           {df_final.shape[1]}")
print(f"População total:   {df_final['peso'].sum()/1e6:.1f} milhões")
print(f"  com renda:       {df_final.loc[df_final['tem_renda']==1, 'peso'].sum()/1e6:.1f} milhões")
print(f"  sem renda:       {df_final.loc[df_final['tem_renda']==0, 'peso'].sum()/1e6:.1f} milhões")
print(f"Setores:           {df_final['setor_agregado'].nunique()} categorias")
print(f"Setor crítico IA:  {df_final['setor_critico_ia'].sum():,} obs")
print(f"Salvo em:          {output_path}")
print(f"Tamanho em disco:  {output_path.stat().st_size / 1e6:.1f} MB")

df_final.info()
```

    ============================================================
    CHECKPOINT - Qualidade do Merge
    ============================================================
    Observações totais:     207,901
    Com score de exposição: 206,230
    Sem score (NaN):        1,671
    % pop. sem score:       0.8%

    Distribuição por gradiente ILO (potential25):
      Not Exposed: 52.2 milhões
      Minimal Exposure: 15.2 milhões
      Exposed: Gradient 2: 10.0 milhões
      Exposed: Gradient 1: 8.7 milhões
      Exposed: Gradient 4: 5.0 milhões
      Exposed: Gradient 3: 4.8 milhões
      Sem classificação: 1.8 milhões

    População por quintil de exposição (deve ser ~20% cada):
      Q1 (Baixa): 20.8 milhões (21.5%)
      Q2: 18.1 milhões (18.7%)
      Q3: 21.4 milhões (22.0%)
      Q4: 17.4 milhões (17.9%)
      Q5 (Alta): 19.3 milhões (19.9%)

    Setores: 17 categorias
    Trabalhadores em setores críticos IA: 7.8 milhões

    Distribuição por setor:
      Outros Serviços: 19.1 milhões
      Ind. Transformação: 18.7 milhões
      Construção: 7.2 milhões
      Educação: 7.2 milhões
      Saúde: 6.2 milhões
      Transporte: 5.7 milhões
      Serviços Domésticos: 5.3 milhões
      Alojamento e Alimentação: 5.1 milhões
      Administração Pública: 5.0 milhões
      Serviços Administrativos: 4.6 milhões
      Serviços Profissionais: 4.3 milhões *
      Comércio: 3.2 milhões
      Informação e Comunicação: 1.9 milhões *
      Finanças e Seguros: 1.6 milhões *
      Artes e Cultura: 1.2 milhões
      Utilidades: 0.7 milhões
      Atividades Imobiliárias: 0.7 milhões

    ============================================================
    BASE FINAL CONSOLIDADA
    ============================================================
    Observações:       207,901
    Com score:         206,230
    Cobertura:         99.2%
    Colunas:           31
    População total:   97.8 milhões
      com renda:       96.7 milhões
      sem renda:       1.1 milhões
    Setores:           17 categorias
    Setor crítico IA:  13,427 obs
    Salvo em:          data/output/pnad_ilo_merged.csv
    Tamanho em disco:  40.0 MB
    <class 'pandas.core.frame.DataFrame'>
    Index: 207901 entries, 0 to 220090
    Data columns (total 31 columns):
     #   Column                Non-Null Count   Dtype   
    ---  ------                --------------   -----   
     0   ano                   207901 non-null  Int64   
     1   trimestre             207901 non-null  Int64   
     2   sigla_uf              207901 non-null  object  
     3   regiao                207901 non-null  object  
     4   sexo                  207901 non-null  object  
     5   sexo_texto            207901 non-null  object  
     6   idade                 207901 non-null  Int64   
     7   faixa_etaria          207901 non-null  category
     8   raca_cor              207901 non-null  object  
     9   raca_agregada         207901 non-null  object  
     10  nivel_instrucao       207901 non-null  object  
     11  cod_ocupacao          207901 non-null  object  
     12  grande_grupo          206230 non-null  object  
     13  grupamento_atividade  207901 non-null  object  
     14  setor_agregado        207901 non-null  object  
     15  setor_critico_ia      207901 non-null  int64   
     16  posicao_ocupacao      207901 non-null  object  
     17  formal                207901 non-null  int64   
     18  tem_renda             207901 non-null  int64   
     19  rendimento_habitual   204142 non-null  float64 
     20  rendimento_winsor     204142 non-null  float64 
     21  rendimento_efetivo    204171 non-null  float64 
     22  horas_habituais       207901 non-null  Int64   
     23  horas_efetivas        207901 non-null  Int64   
     24  faixa_renda_sm        204142 non-null  category
     25  peso                  207901 non-null  float64 
     26  exposure_score        206230 non-null  float64 
     27  exposure_gradient     207901 non-null  object  
     28  match_level           206230 non-null  object  
     29  quintil_exposure      206230 non-null  category
     30  decil_exposure        206230 non-null  category
    dtypes: Int64(5), category(4), float64(5), int64(3), object(14)
    memory usage: 54.3+ MB

### Limitações desta etapa

1.  **Crosswalk hierárquico:** O match a 3 dígitos (subgrupo) suaviza
    diferenças entre ocupações dentro do mesmo subgrupo, afetando ~1,3%
    das observações. O score atribuído é a média do subgrupo, não o
    score específico da ocupação.

2.  **Trimestre único:** Os dados referem-se a um único trimestre
    (Q3/2025). Resultados podem variar sazonalmente, especialmente em
    setores com forte sazonalidade (agropecuária, comércio).

3.  **Variáveis indisponíveis:** As variáveis de tempo no emprego
    (`V4040`) e porte da empresa (`V4018`) não estão populadas na fonte
    utilizada (Base dos Dados/BigQuery) para o período analisado,
    limitando análises de estabilidade ocupacional e adoção de IA por
    tamanho de empresa.

4.  **Índice global aplicado ao Brasil:** O índice da OIT foi
    desenvolvido com foco global e pode não capturar especificidades do
    mercado de trabalho brasileiro, como a elevada informalidade (~40%
    da força de trabalho) e diferenças na adoção tecnológica entre
    setores formais e informais.

5.  **Exposição ≠ impacto:** O índice mede potencial de exposição das
    tarefas à IA generativa, não o impacto efetivo. A materialização do
    impacto depende de fatores como velocidade de adoção tecnológica,
    regulação, custos de implementação e respostas institucionais.

---

<!-- fonte: etapa_1b_analise_dados_ilo_pnadc.ipynb -->

# ETAPA 1 - Análise Descritiva da Exposição de IA Generativa com ILO
Index e PNADc


## ANÁLISE DOS DADOS

**Dissertação:** Inteligência Artificial Generativa e o Mercado de
Trabalho Brasileiro: Uma Análise de Exposição Ocupacional e seus Efeitos
Distributivos.

**Aluno:** Manoel Brasil Orlandi

### Contextualização

A rápida difusão de modelos de IA generativa (LLMs, geradores de
imagem/código) levanta questões centrais sobre seus impactos no mercado
de trabalho. Para mensurar esse potencial de impacto, a Organização
Internacional do Trabalho (OIT) criou índice de exposição ocupacional à
IA generativa, publicado como *Working Paper* 140 (WP140). O índice
atribui scores de exposição a cada ocupação da classificação ISCO-08,
com base na avaliação de suas tarefas constituintes por modelos de
linguagem e validação humana.

Este notebook faz a análise e descrição populacional usando como base os
dados `pnad_ilo_merged.csv` que junta os microdados da **PNAD Contínua**
(Pesquisa Nacional por Amostra de Domicílios Contínua, IBGE, 3º
trimestre de 2025) ao \*\*índice de exposição à IA generativa da OIT\* e
foram preparados no notebook
`etapa_1a_preparacao_dados_ilo_pnadc.ipynb`.

> **Nota:** O salário mínimo vigente de R\$ 1.518 segue o Decreto nº
> 12.342/2025. Os dados da PNADc referem-se ao 3º trimestre de 2025 e
> são combinados ao índice de exposição ILO WP140 (versão 2025). Como o
> índice foi construído para a classificação ISCO-08, utilizou-se um
> crosswalk COD→ISCO-08 que introduz potencial erro de medida (ver
> Limitações, Seção 9).

### Objetivo da Análise

**Perfil da exposição**: Distribuição da população por quintil/decil de
exposição; média ponderada de exposure_score por grupo.

**Desigualdade e renda**: Rendimento médio (e mediano) ponderado por
quintil de exposição; razão renda Q5/Q1 de exposição.

**Gênero e raça**: % de mulheres e de negros por quintil de exposição;
exposição média por sexo e raça

**Formalidade**: % formal por quintil de exposição; exposição média no
formal vs informal

**Setor e ocupação**: Exposição média por setor_agregado e por
grande_grupo; concentração em setores críticos IA.

**Região**: Exposição média por região; população em alta exposição por
UF/região.

**Idade e instrução**: Exposição média por faixa etária e nível de
instrução.

**Augmentation vs. Automação**: Comparação entre trabalhadores em
gradientes de complementaridade (G1-G2) e transformação (G3-G4).

### Referências principais

- Gmyrek, P., Berg, J. & Cappelli, D. (2025). *Generative AI and Jobs:
  An updated global assessment of potential effects on job quantity and
  quality*. ILO Working Paper 140.
- IBGE. *Pesquisa Nacional por Amostra de Domicílios Contínua* (PNADc),
  3º trimestre de 2025.

> **Conexão com WP140:** O índice de exposição da OIT segue a abordagem
> task-based (Autor, 2015; Acemoglu & Restrepo, 2019), onde cada
> ocupação é decomposta em tarefas e cada tarefa é avaliada quanto à
> capacidade de modelos de IA generativa de realizá-la. O WP140 estende
> trabalhos anteriores (Felten et al., 2021; Eloundou et al., 2023) ao
> incorporar validação humana e distinguir entre potencial de automação
> e de complementaridade (augmentation).

### 1. Configuração do ambiente

Definir caminhos, importar bibliotecas e configurar logs.

``` python
# Instalar dependencias no kernel atual (executar apenas uma vez)
%pip install pandas numpy pyarrow openpyxl statsmodels scipy matplotlib seaborn --quiet
```


    [notice] A new release of pip is available: 24.2 -> 26.0.1
    [notice] To update, run: python3.10 -m pip install --upgrade pip
    Note: you may need to restart the kernel to use updated packages.

``` python
# Etapa 1b.1 - Analise de Dados - Configuracao do ambiente

import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy.stats import gaussian_kde, ks_2samp, linregress
from statsmodels.stats.weightstats import DescrStatsW, CompareMeans
import statsmodels.formula.api as smf
import statsmodels.api as sm

warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option('display.max_columns', 40)
pd.set_option('display.float_format', '{:.3f}'.format)

# ---------------------------------------------------------------------------
# Estilo visual
# ---------------------------------------------------------------------------
sns.set_style("whitegrid")
plt.rcParams.update({
    'figure.figsize': (12, 7),
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'figure.dpi': 100,
})

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATA_OUTPUT = Path("../../data/output")
DATA_INPUT  = Path("../../data/input")

# ---------------------------------------------------------------------------
# Parametros
# ---------------------------------------------------------------------------
SALARIO_MINIMO = 1518
PNAD_ANO       = 2025
PNAD_TRIMESTRE = 3

# ---------------------------------------------------------------------------
# Mapeamentos e constantes (replicados de settings.py)
# ---------------------------------------------------------------------------
REGIAO_MAP = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte',
    'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste',
    'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste',
}

GRANDES_GRUPOS = {
    '1': 'Dirigentes e gerentes',
    '2': 'Profissionais das ciencias',
    '3': 'Tecnicos nivel medio',
    '4': 'Apoio administrativo',
    '5': 'Servicos e vendedores',
    '6': 'Agropecuaria qualificada',
    '7': 'Industria qualificada',
    '8': 'Operadores de maquinas',
    '9': 'Ocupacoes elementares',
}

GRADIENT_ORDER = [
    'Not Exposed', 'Minimal Exposure',
    'Exposed: Gradient 1', 'Exposed: Gradient 2',
    'Exposed: Gradient 3', 'Exposed: Gradient 4',
]

GRADIENT_COLORS = {
    'Not Exposed':          '#2ca02c',
    'Minimal Exposure':     '#98df8a',
    'Exposed: Gradient 1':  '#aec7e8',
    'Exposed: Gradient 2':  '#ffbb78',
    'Exposed: Gradient 3':  '#ff7f0e',
    'Exposed: Gradient 4':  '#d62728',
    'Sem classificacao':    '#d9d9d9',
}

GRADIENT_LABELS_PT = {
    'Not Exposed':          'Nao Exposto',
    'Minimal Exposure':     'Exposicao Minima',
    'Exposed: Gradient 1':  'Gradiente 1 (Aumento)',
    'Exposed: Gradient 2':  'Gradiente 2',
    'Exposed: Gradient 3':  'Gradiente 3',
    'Exposed: Gradient 4':  'Gradiente 4 (Automacao)',
}

HIGH_EXPOSURE_GRADIENTS = ['Exposed: Gradient 3', 'Exposed: Gradient 4']
QUINTIL_ORDER = ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
DECIL_ORDER = [f'D{i}' for i in range(1, 11)]

NIVEL_INSTRUCAO_ORDER = [
    'Sem instrucao', 'Fundamental incompleto', 'Fundamental completo',
    'Medio incompleto', 'Medio completo', 'Superior incompleto', 'Superior completo',
]

SETORES_CRITICOS_IA = [
    'Informacao e Comunicacao', 'Financas e Seguros', 'Servicos Profissionais',
]

# ---------------------------------------------------------------------------
# Funcoes utilitarias - estatisticas ponderadas
# ---------------------------------------------------------------------------
def weighted_mean(values, weights):
    """Media ponderada (ignora NaN)."""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    return np.average(values[mask], weights=weights[mask])

def weighted_std(values, weights):
    """Desvio-padrao ponderado (ignora NaN)."""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    avg = np.average(values[mask], weights=weights[mask])
    variance = np.average((values[mask] - avg) ** 2, weights=weights[mask])
    return np.sqrt(variance)

def weighted_quantile(values, weights, quantile):
    """Quantil ponderado por pesos amostrais (ignora NaN)."""
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
    """Coeficiente de Gini ponderado."""
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
    B = np.sum(cumsum_wx[:-1] * sorted_w[1:]) / (total_w * total_wx)
    return 1 - 2 * B

def weighted_ci(values, weights, alpha=0.05):
    """Retorna (media, IC_inferior, IC_superior) usando DescrStatsW."""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() < 2:
        return np.nan, np.nan, np.nan
    d = DescrStatsW(data=np.array(values[mask]), weights=np.array(weights[mask]))
    ci = d.tconfint_mean(alpha=alpha)
    return d.mean, ci[0], ci[1]

def weighted_ttest_2groups(vals_a, weights_a, vals_b, weights_b):
    """Teste t ponderado para duas amostras independentes. Retorna (t_stat, p_value)."""
    mask_a = ~(pd.isna(vals_a) | pd.isna(weights_a))
    mask_b = ~(pd.isna(vals_b) | pd.isna(weights_b))
    d_a = DescrStatsW(data=np.array(vals_a[mask_a]), weights=np.array(weights_a[mask_a]))
    d_b = DescrStatsW(data=np.array(vals_b[mask_b]), weights=np.array(weights_b[mask_b]))
    cm = CompareMeans(d_a, d_b)
    t_stat, p_value, df = cm.ttest_ind()
    return t_stat, p_value

def weighted_cohen_d(x1, w1, x2, w2):
    """d de Cohen ponderado para dois grupos."""
    m1 = np.average(x1, weights=w1)
    m2 = np.average(x2, weights=w2)
    v1 = np.average((x1 - m1)**2, weights=w1)
    v2 = np.average((x2 - m2)**2, weights=w2)
    n1, n2 = w1.sum(), w2.sum()
    pooled_sd = np.sqrt((n1 * v1 + n2 * v2) / (n1 + n2))
    return (m1 - m2) / pooled_sd if pooled_sd > 0 else 0.0

def sig_stars(p):
    """Retorna estrelas de significancia."""
    if p < 0.001: return '***'
    if p < 0.01:  return '**'
    if p < 0.05:  return '*'
    return ''

# ---------------------------------------------------------------------------
# Carregar dados
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA_OUTPUT / "pnad_ilo_merged.csv")

# Garantir tipos corretos
df['cod_ocupacao'] = df['cod_ocupacao'].astype(str).str.zfill(4)
df['quintil_exposure'] = pd.Categorical(df['quintil_exposure'], categories=QUINTIL_ORDER, ordered=True)
df['decil_exposure'] = pd.Categorical(df['decil_exposure'], categories=DECIL_ORDER, ordered=True)

# Subsets uteis
df_score = df[df['exposure_score'].notna()].copy()  # com score de exposicao
df_renda = df[(df['tem_renda'] == 1) & df['exposure_score'].notna()].copy()  # com renda + score

# Criar edu_simples para uso nas analises (escolaridade simplificada)
edu_map = {'1': 'Sem/Fund.Inc.', '2': 'Sem/Fund.Inc.', '3': 'Fund.Comp.', '4': 'Med.Inc.', '5': 'Med.Comp.', '6': 'Sup.Inc.', '7': 'Sup.Comp.'}
col_edu = 'nivel_instrucao' if 'nivel_instrucao' in df_score.columns else 'vd3004'
df_score['edu_simples'] = df_score[col_edu].astype(str).map(edu_map).fillna('Outros')

print("=" * 60)
print("CONFIGURACAO CARREGADA")
print("=" * 60)
print(f"  Observacoes totais:    {len(df):,}")
print(f"  Com score exposicao:   {len(df_score):,}")
print(f"  Com renda + score:     {len(df_renda):,}")
print(f"  Populacao total:       {df['peso'].sum()/1e6:.1f} milhoes")
print(f"  Periodo: {PNAD_ANO} Q{PNAD_TRIMESTRE}")

# Nota metodologica
print("\n" + "-" * 60)
print("NOTA METODOLOGICA sobre erros-padrao:")
print("Erros-padrao e ICs tratam a amostra como aleatoria simples")
print("reponderada por V1028. A PNADc usa desenho complexo com")
print("estratificacao e conglomeracao; SEs podem ser subestimados.")
print("-" * 60)
```

    ============================================================
    CONFIGURACAO CARREGADA
    ============================================================
      Observacoes totais:    207,901
      Com score exposicao:   206,230
      Com renda + score:     202,471
      Populacao total:       97.8 milhoes
      Periodo: 2025 Q3

    ------------------------------------------------------------
    NOTA METODOLOGICA sobre erros-padrao:
    Erros-padrao e ICs tratam a amostra como aleatoria simples
    reponderada por V1028. A PNADc usa desenho complexo com
    estratificacao e conglomeracao; SEs podem ser subestimados.
    ------------------------------------------------------------

### 2. Perfil da exposicao

Distribuicao da populacao por quintil/decil de exposicao; media
ponderada de exposure_score por grupo.

**Analises:** - Histograma + KDE da distribuicao de exposicao com
overlay de gradientes ILO - Tabela-resumo por gradiente ILO com top 5
ocupacoes COD - Geracao de `cod_ilo_merged.csv` - Medidas de
desigualdade: Gini, P90/P10, curva de Lorenz - Comparacao com literatura
internacional (com ICs)

> **Nota sobre intervalos de confiança:** Os ICs reportados nesta seção
> tratam a amostra como aleatória simples reponderada (SRS com pesos
> V1028). Como a PNADc utiliza desenho amostral complexo
> (estratificação + conglomeração), os ICs reais são mais amplos. Os
> valores reportados devem ser interpretados como limites inferiores da
> incerteza.

> **Nota sobre gradientes ILO:** Os thresholds de classificação dos
> gradientes de exposição (Not Exposed, Minimal Exposure, Gradients 1-4)
> seguem exatamente a definição do WP140 (Gmyrek et al., 2025, Tabela 1,
> p. 14), baseada nos scores de exposição e nos indicadores SML (Save,
> Modify, Learn).

> **Sobre os gradientes (WP140, Seção 2.3):** Os gradientes de exposição
> refletem não apenas o nível de exposição mas o TIPO de impacto
> esperado. Gradientes 1-2 indicam que a IA é mais propensa a
> complementar o trabalho humano (augmentation), enquanto Gradientes 3-4
> indicam maior potencial de transformação das tarefas ou substituição.
> Essa distinção é fundamental para políticas públicas: o mesmo nível de
> exposição pode representar oportunidade (augmentation) ou risco
> (automação), dependendo do contexto ocupacional. Referência: WP140,
> Figura 2 (p. 14) e Tabela 1 (p. 13).

``` python
# Etapa 1b.2 - Analise de Dados - Perfil da exposicao

# ======================================================================
# 2.1 - Distribuicao da exposicao: histograma + KDE + gradientes
# ======================================================================

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# --- Painel A: Histograma ponderado com KDE ---
ax = axes[0]
scores = df_score['exposure_score'].values
pesos = df_score['peso'].values
ax.hist(scores, bins=40, weights=pesos/1e6, color='steelblue', alpha=0.7,
        edgecolor='white', linewidth=0.5)

# KDE ponderado
kde = gaussian_kde(scores, weights=pesos/pesos.sum())
x_kde = np.linspace(scores.min(), scores.max(), 200)
# Escalar KDE para a mesma area do histograma
bin_width = (scores.max() - scores.min()) / 40
kde_scaled = kde(x_kde) * (pesos.sum()/1e6) * bin_width
ax.plot(x_kde, kde_scaled, color='darkred', linewidth=2, label='KDE')

media_exp = weighted_mean(df_score['exposure_score'], df_score['peso'])
ax.axvline(media_exp, color='red', linestyle='--', linewidth=1.5,
           label=f'Media = {media_exp:.3f}')
ax.set_xlabel('Score de Exposicao')
ax.set_ylabel('Trabalhadores (milhoes)')
ax.set_title('(A) Distribuicao da Exposicao a IA Generativa')
ax.legend()

# --- Painel B: Populacao por gradiente ILO ---
ax = axes[1]
grad_data = []
for grad in GRADIENT_ORDER:
    sub = df_score[df_score['exposure_gradient'] == grad]
    if len(sub) > 0:
        pop = sub['peso'].sum() / 1e6
        grad_data.append({
            'Gradiente': GRADIENT_LABELS_PT.get(grad, grad),
            'Pop': pop,
            'Color': GRADIENT_COLORS.get(grad, '#999999'),
        })

grad_df = pd.DataFrame(grad_data)
bars = ax.barh(grad_df['Gradiente'], grad_df['Pop'], color=grad_df['Color'],
               edgecolor='white', linewidth=0.5)
for bar, pop in zip(bars, grad_df['Pop']):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{pop:.1f}M', va='center', fontsize=10)
ax.set_xlabel('Trabalhadores (milhoes)')
ax.set_title('(B) Populacao por Gradiente ILO')
ax.invert_yaxis()

plt.tight_layout()
plt.show()

# ======================================================================
# 2.2 - Tabela-resumo por gradiente ILO + top 5 ocupacoes
# ======================================================================
print("=" * 70)
print("PERFIL DA EXPOSICAO POR GRADIENTE ILO")
print("=" * 70)

total_pop = df_score['peso'].sum()
for grad in GRADIENT_ORDER:
    sub = df_score[df_score['exposure_gradient'] == grad]
    if len(sub) == 0:
        continue
    pop = sub['peso'].sum()
    pct = pop / total_pop * 100
    mean_exp, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    sub_renda = sub[sub['tem_renda'] == 1]
    mean_renda = weighted_mean(sub_renda['rendimento_habitual'], sub_renda['peso']) if len(sub_renda) > 0 else np.nan
    pct_formal = weighted_mean(sub['formal'], sub['peso']) * 100
    pct_mulher = weighted_mean((sub['sexo_texto'] == 'Mulher').astype(int), sub['peso']) * 100

    label = GRADIENT_LABELS_PT.get(grad, grad)
    print(f"\n--- {label} ({grad}) ---")
    print(f"  Populacao: {pop/1e6:.1f} milhoes ({pct:.1f}%)")
    print(f"  Exposicao media: {mean_exp:.3f} [IC 95%: {ci_lo:.3f} - {ci_hi:.3f}]")
    print(f"  Renda media: R$ {mean_renda:,.0f}" if not np.isnan(mean_renda) else "  Renda media: N/D")
    print(f"  % Formal: {pct_formal:.1f}% | % Mulheres: {pct_mulher:.1f}%")

    # Top 5 ocupacoes por populacao neste gradiente
    top5 = (sub.groupby('cod_ocupacao')
            .agg(pop_ocu=('peso', 'sum'), exp_mean=('exposure_score', 'mean'))
            .sort_values('pop_ocu', ascending=False)
            .head(5))
    print(f"  Top 5 ocupacoes (COD):")
    for cod, row in top5.iterrows():
        gg = GRANDES_GRUPOS.get(cod[0], '')
        # Lookup nome da ocupacao se disponivel
        nome_ocup = ''
        if 'descricao_ocupacao' in df_score.columns:
            match = df_score[df_score['cod_ocupacao'] == cod]['descricao_ocupacao']
            nome_ocup = match.iloc[0] if len(match) > 0 else ''
        if nome_ocup:
            print(f"    {cod} - {nome_ocup} ({gg}): {row['pop_ocu']/1e6:.2f}M trabalhadores, score={row['exp_mean']:.3f}")
        else:
            print(f"    {cod} ({gg}): {row['pop_ocu']/1e6:.2f}M trabalhadores, score={row['exp_mean']:.3f}")

# ======================================================================
# 2.3 - Gerar cod_ilo_merged.csv
# ======================================================================
cod_summary = (df_score.groupby('cod_ocupacao')
    .agg(
        grande_grupo=('grande_grupo', 'first'),
        exposure_score=('exposure_score', 'mean'),
        exposure_gradient=('exposure_gradient', 'first'),
        n_obs=('peso', 'count'),
        pop_milhoes=('peso', lambda x: x.sum()/1e6),
        renda_media=('rendimento_habitual', lambda x: weighted_mean(x, df_score.loc[x.index, 'peso'])),
        pct_formal=('formal', lambda x: weighted_mean(x, df_score.loc[x.index, 'peso']) * 100),
    )
    .sort_values('pop_milhoes', ascending=False)
    .round(3)
)

cod_output = DATA_OUTPUT / "cod_ilo_merged.csv"
cod_summary.to_csv(cod_output)
print(f"\nTabela cod_ilo_merged.csv salva em: {cod_output}")
print(f"  {len(cod_summary)} ocupacoes | Top 5:")
display(cod_summary.head())

# ======================================================================
# 2.4 - Desigualdade: Gini, P90/P10, Curva de Lorenz
# ======================================================================
gini_exp = gini_coefficient(df_score['exposure_score'], df_score['peso'])
p90 = weighted_quantile(df_score['exposure_score'], df_score['peso'], 0.90)
p10 = weighted_quantile(df_score['exposure_score'], df_score['peso'], 0.10)
p50 = weighted_quantile(df_score['exposure_score'], df_score['peso'], 0.50)
ratio_p90_p10 = p90 / p10 if p10 > 0 else np.nan

# Media geral com IC
mean_geral, ci_lo_geral, ci_hi_geral = weighted_ci(df_score['exposure_score'], df_score['peso'])

print("\n" + "=" * 70)
print("METRICAS DE DESIGUALDADE NA EXPOSICAO")
print("=" * 70)
print(f"  Media: {mean_geral:.3f} [IC 95%: {ci_lo_geral:.3f} - {ci_hi_geral:.3f}]")
print(f"  Mediana: {p50:.3f}")
print(f"  Gini: {gini_exp:.4f}")
print(f"  P90/P10: {ratio_p90_p10:.2f} (P90={p90:.3f}, P10={p10:.3f})")

# Curva de Lorenz
vals = np.array(df_score['exposure_score'])
wgts = np.array(df_score['peso'])
sorted_idx = np.argsort(vals)
sorted_vals = vals[sorted_idx]
sorted_wgts = wgts[sorted_idx]
cum_pop = np.concatenate([[0], np.cumsum(sorted_wgts) / sorted_wgts.sum()])
cum_exp = np.concatenate([[0], np.cumsum(sorted_wgts * sorted_vals) / (sorted_wgts * sorted_vals).sum()])

fig, ax = plt.subplots(figsize=(7, 7))
ax.plot(cum_pop, cum_exp, color='steelblue', linewidth=2,
        label=f'Lorenz (Gini = {gini_exp:.3f})')
ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Igualdade perfeita')
ax.fill_between(cum_pop, cum_exp, cum_pop, alpha=0.15, color='steelblue')
ax.set_xlabel('Fracao acumulada da populacao')
ax.set_ylabel('Fracao acumulada da exposicao')
ax.set_title('Curva de Lorenz da Exposicao a IA Generativa')
ax.legend(loc='upper left')
ax.set_aspect('equal')
plt.tight_layout()
plt.show()

# ======================================================================
# 2.5 - Comparacao com literatura internacional
# ======================================================================
n_alta = df_score[df_score['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
pct_alta = n_alta / df_score['peso'].sum() * 100

print("\n" + "=" * 70)
print("COMPARACAO COM LITERATURA INTERNACIONAL")
print("=" * 70)
print(f"{'Estudo':<32} {'Grupo':<22} {'Media':<12} {'% Alta Exp.':<12}")
print("-" * 78)
print(f"{'Presente (ILO 2025)':<32} {'Brasil':<22} {mean_geral:.3f}{'':>5} {pct_alta:.1f}%")
print(f"{'Gmyrek et al. (2025)':<32} {'Upper-middle-income':<22} {'~0.29':<12} {'--':<12}")
print(f"{'Gmyrek et al. (2025)':<32} {'High-income':<22} {'~0.36':<12} {'--':<12}")
print(f"{'Gmyrek et al. (2025)':<32} {'Global':<22} {'0.30':<12} {'--':<12}")
print(f"{'Eloundou et al. (2023)':<32} {'EUA':<22} {'--':<12} {'19.0%':<12}")
print(f"\nNota: O Brasil ({mean_geral:.3f}) se posiciona dentro do esperado para")
print(f"paises de renda media-alta (upper-middle-income ~ 0.29, WP140 Tabela 4).")
```

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-4-output-1.png)

    ======================================================================
    PERFIL DA EXPOSICAO POR GRADIENTE ILO
    ======================================================================

    --- Nao Exposto (Not Exposed) ---
      Populacao: 52.2 milhoes (53.9%)
      Exposicao media: 0.169 [IC 95%: 0.169 - 0.169]
      Renda media: R$ 2,736
      % Formal: 36.7% | % Mulheres: 41.2%
      Top 5 ocupacoes (COD):
        9111 (Ocupacoes elementares): 3.87M trabalhadores, score=0.140
        9112 (Ocupacoes elementares): 2.69M trabalhadores, score=0.120
        7112 (Industria qualificada): 2.60M trabalhadores, score=0.090
        6111 (Agropecuaria qualificada): 2.00M trabalhadores, score=0.180
        9313 (Ocupacoes elementares): 1.67M trabalhadores, score=0.090

    --- Exposicao Minima (Minimal Exposure) ---
      Populacao: 15.2 milhoes (15.7%)
      Exposicao media: 0.306 [IC 95%: 0.306 - 0.306]
      Renda media: R$ 4,449
      % Formal: 51.2% | % Mulheres: 37.7%
      Top 5 ocupacoes (COD):
        8332 (Operadores de maquinas): 1.97M trabalhadores, score=0.240
        3221 (Tecnicos nivel medio): 1.17M trabalhadores, score=0.220
        8321 (Operadores de maquinas): 1.16M trabalhadores, score=0.250
        4321 (Apoio administrativo): 1.07M trabalhadores, score=0.370
        2611 (Profissionais das ciencias): 1.02M trabalhadores, score=0.360

    --- Gradiente 1 (Aumento) (Exposed: Gradient 1) ---
      Populacao: 8.7 milhoes (9.0%)
      Exposicao media: 0.357 [IC 95%: 0.357 - 0.357]
      Renda media: R$ 2,755
      % Formal: 51.2% | % Mulheres: 52.3%
      Top 5 ocupacoes (COD):
        5223 (Servicos e vendedores): 3.54M trabalhadores, score=0.380
        8322 (Operadores de maquinas): 2.09M trabalhadores, score=0.280
        5230 (Servicos e vendedores): 1.08M trabalhadores, score=0.390
        3411 (Tecnicos nivel medio): 0.43M trabalhadores, score=0.390
        2634 (Profissionais das ciencias): 0.40M trabalhadores, score=0.390

    --- Gradiente 2 (Exposed: Gradient 2) ---
      Populacao: 10.0 milhoes (10.3%)
      Exposicao media: 0.444 [IC 95%: 0.444 - 0.444]
      Renda media: R$ 5,400
      % Formal: 37.8% | % Mulheres: 42.6%
      Top 5 ocupacoes (COD):
        5221 (Servicos e vendedores): 2.88M trabalhadores, score=0.430
        5243 (Servicos e vendedores): 1.12M trabalhadores, score=0.460
        1420 (Dirigentes e gerentes): 0.56M trabalhadores, score=0.440
        1219 (Dirigentes e gerentes): 0.54M trabalhadores, score=0.420
        2421 (Profissionais das ciencias): 0.50M trabalhadores, score=0.460

    --- Gradiente 3 (Exposed: Gradient 3) ---
      Populacao: 4.8 milhoes (4.9%)
      Exposicao media: 0.551 [IC 95%: 0.551 - 0.551]
      Renda media: R$ 4,347
      % Formal: 60.6% | % Mulheres: 62.3%
      Top 5 ocupacoes (COD):
        4226 (Apoio administrativo): 1.04M trabalhadores, score=0.570
        2411 (Profissionais das ciencias): 0.59M trabalhadores, score=0.510
        4120 (Apoio administrativo): 0.50M trabalhadores, score=0.580
        2431 (Profissionais das ciencias): 0.43M trabalhadores, score=0.550
        4222 (Apoio administrativo): 0.40M trabalhadores, score=0.580

    --- Gradiente 4 (Automacao) (Exposed: Gradient 4) ---
      Populacao: 5.0 milhoes (5.1%)
      Exposicao media: 0.606 [IC 95%: 0.606 - 0.606]
      Renda media: R$ 3,257
      % Formal: 64.9% | % Mulheres: 63.4%
      Top 5 ocupacoes (COD):
        4110 (Apoio administrativo): 3.75M trabalhadores, score=0.600
        5244 (Servicos e vendedores): 0.31M trabalhadores, score=0.610
        4311 (Apoio administrativo): 0.30M trabalhadores, score=0.640
        2413 (Profissionais das ciencias): 0.19M trabalhadores, score=0.620
        3311 (Tecnicos nivel medio): 0.11M trabalhadores, score=0.630

    Tabela cod_ilo_merged.csv salva em: data/output/cod_ilo_merged.csv
      422 ocupacoes | Top 5:

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | grande_grupo | exposure_score | exposure_gradient | n_obs | pop_milhoes | renda_media | pct_formal |
|----|----|----|----|----|----|----|----|
| cod_ocupacao |  |  |  |  |  |  |  |
| 9111 | Ocupações elementares | 0.140 | Not Exposed | 9432 | 3.866 | 1303.005 | 24.289 |
| 4110 | Apoio administrativo | 0.600 | Exposed: Gradient 4 | 7532 | 3.752 | 2823.199 | 65.708 |
| 5223 | Serviços e vendedores | 0.380 | Exposed: Gradient 1 | 6825 | 3.541 | 2091.706 | 74.294 |
| 5221 | Serviços e vendedores | 0.430 | Exposed: Gradient 2 | 6337 | 2.880 | 4071.596 | 0.000 |
| 9112 | Ocupações elementares | 0.120 | Not Exposed | 5947 | 2.688 | 1733.183 | 67.528 |

</div>


    ======================================================================
    METRICAS DE DESIGUALDADE NA EXPOSICAO
    ======================================================================
      Media: 0.278 [IC 95%: 0.278 - 0.278]
      Mediana: 0.240
      Gini: 0.2947
      P90/P10: 4.17 (P90=0.500, P10=0.120)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-4-output-5.png)


    ======================================================================
    COMPARACAO COM LITERATURA INTERNACIONAL
    ======================================================================
    Estudo                           Grupo                  Media        % Alta Exp. 
    ------------------------------------------------------------------------------
    Presente (ILO 2025)              Brasil                 0.278      10.1%
    Gmyrek et al. (2025)             Upper-middle-income    ~0.29        --          
    Gmyrek et al. (2025)             High-income            ~0.36        --          
    Gmyrek et al. (2025)             Global                 0.30         --          
    Eloundou et al. (2023)           EUA                    --           19.0%       

    Nota: O Brasil (0.278) se posiciona dentro do esperado para
    paises de renda media-alta (upper-middle-income ~ 0.29, WP140 Tabela 4).

### 3. Desigualdade e renda

Rendimento medio (e mediano) ponderado por quintil de exposicao; razao
renda Q5/Q1 de exposicao.

**Analises:** - Perfil de renda por quintil/decil com ICs 95% - Grafico
renda x decil com LOWESS + linear + barras de erro - KDE de renda por
quintil de exposicao - Curva de concentracao da exposicao ordenada por
renda - Regressao quantilica: coeficiente de exposicao em tau = 0.10,
0.25, 0.50, 0.75, 0.90

> **Atenção interpretativa:** A relação entre exposição e renda NÃO é
> monotônica — o quintil Q4 apresenta renda média superior ao Q5. Isso
> ocorre porque o Q5 concentra ocupações administrativas e de saúde com
> alta exposição mas renda relativamente moderada, enquanto o Q4 inclui
> gerentes e profissionais liberais de setores menos expostos mas com
> remuneração elevada.
>
> O R² individual da regressão renda~exposição é muito baixo (0.034),
> enquanto o R² agregado por decis é alto (0.653). Essa diferença
> ilustra a falácia ecológica: padrões de grupo não se traduzem
> automaticamente em padrões individuais (Robinson, 1950).

> **Conexão com WP140:** O WP140 encontra que, globalmente, ocupações de
> maior exposição tendem a ser de maior renda (Tabela 2, p. 20), o que é
> consistente com a hipótese de complementaridade. Para países de renda
> média-alta como o Brasil, esse padrão é esperado mas menos pronunciado
> do que em países de alta renda, onde o setor de serviços profissionais
> é proporcionalmente maior. A razão Q5/Q1 de 2.23x encontrada aqui está
> alinhada com essa expectativa.

``` python
# Etapa 1b.3 - Analise de Dados - Desigualdade e renda

# ======================================================================
# 3.1 - Perfil de renda por quintil de exposicao com ICs
# ======================================================================
print("=" * 70)
print("PERFIL DE RENDA POR QUINTIL DE EXPOSICAO")
print("=" * 70)

rows_quintil = []
for q in QUINTIL_ORDER:
    sub = df_renda[df_renda['quintil_exposure'] == q]
    if len(sub) == 0:
        continue
    mean_r, ci_lo, ci_hi = weighted_ci(sub['rendimento_habitual'], sub['peso'])
    median_r = weighted_quantile(sub['rendimento_habitual'], sub['peso'], 0.50)
    rows_quintil.append({
        'Quintil': q,
        'Renda Media (R$)': mean_r,
        'IC 95% Inf': ci_lo,
        'IC 95% Sup': ci_hi,
        'Renda Mediana (R$)': median_r,
        'Exp. Media': weighted_mean(sub['exposure_score'], sub['peso']),
        '% Formal': weighted_mean(sub['formal'], sub['peso']) * 100,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })

tab_quintil = pd.DataFrame(rows_quintil).set_index('Quintil')
display(tab_quintil.round(1))

# Razao Q5/Q1
renda_q5 = tab_quintil.loc['Q5 (Alta)', 'Renda Media (R$)']
renda_q1 = tab_quintil.loc['Q1 (Baixa)', 'Renda Media (R$)']
print(f"\nRazao renda Q5/Q1: {renda_q5/renda_q1:.2f}x")
print(f"  Q1 (Baixa exposicao): R$ {renda_q1:,.0f}")
print(f"  Q5 (Alta exposicao):  R$ {renda_q5:,.0f}")

# Verificar nao-monotonicidade Q4 > Q5
renda_q4 = tab_quintil.loc['Q4', 'Renda Media (R$)']
if renda_q4 > renda_q5:
    print(f"\n  \u26a0 ATENCAO: Q4 (R$ {renda_q4:,.0f}) > Q5 (R$ {renda_q5:,.0f})")
    print(f"  A relacao exposicao-renda NAO e monotonica.")
    print(f"  Q4 concentra gerentes e profissionais liberais de alta renda")
    print(f"  em setores de exposicao moderada.")

# ======================================================================
# 3.2 - Grafico renda x decil com LOWESS + linear + barras de erro
# ======================================================================
decil_data = []
for d in DECIL_ORDER:
    sub = df_renda[df_renda['decil_exposure'] == d]
    if len(sub) == 0:
        continue
    mean_r, ci_lo, ci_hi = weighted_ci(sub['rendimento_habitual'], sub['peso'])
    decil_data.append({
        'Decil': d, 'Renda': mean_r, 'CI_lo': ci_lo, 'CI_hi': ci_hi,
        'Exp_media': weighted_mean(sub['exposure_score'], sub['peso']),
    })

dd = pd.DataFrame(decil_data)

fig, ax = plt.subplots(figsize=(12, 6))
x_pos = range(len(dd))
yerr = [dd['Renda'] - dd['CI_lo'], dd['CI_hi'] - dd['Renda']]
ax.bar(x_pos, dd['Renda'], yerr=yerr, capsize=4, color='steelblue', alpha=0.8,
       edgecolor='white', linewidth=0.5, error_kw={'linewidth': 1.5})

# Tendencia linear
slope, intercept, r_val, p_val, se = linregress(range(len(dd)), dd['Renda'])
ax.plot(x_pos, intercept + slope * np.array(x_pos), 'r--', linewidth=2,
        label=f'Linear (R²={r_val**2:.3f}, p={p_val:.4f})')

# LOWESS
try:
    from statsmodels.nonparametric.smoothers_lowess import lowess
    lowess_fit = lowess(dd['Renda'].values, np.array(x_pos), frac=0.6)
    ax.plot(lowess_fit[:, 0], lowess_fit[:, 1], 'g-', linewidth=2.5, label='LOWESS')
except ImportError:
    pass

ax.set_xticks(x_pos)
ax.set_xticklabels(dd['Decil'], rotation=45)
ax.set_ylabel('Rendimento Habitual Medio (R$)')
ax.set_xlabel('Decil de Exposicao a IA')
ax.set_title('Rendimento Medio por Decil de Exposicao (com IC 95%)')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
ax.legend()
plt.tight_layout()
plt.show()

# R² individual (WLS) para comparacao
model_ind = smf.wls('rendimento_habitual ~ exposure_score',
                     data=df_renda, weights=df_renda['peso']).fit()
print(f"\nR² individual (WLS renda ~ exposicao): {model_ind.rsquared:.4f}")
print(f"R² agregado (decis): {r_val**2:.4f}")
print("Nota: R² agregado e artificialmente inflado por suavizar variancia individual.")

# ======================================================================
# 3.3 - KDE de renda por quintil de exposicao
# ======================================================================
fig, ax = plt.subplots(figsize=(12, 6))
colors_q = ['#2ca02c', '#aec7e8', '#ffbb78', '#ff7f0e', '#d62728']
for i, q in enumerate(QUINTIL_ORDER):
    sub = df_renda[(df_renda['quintil_exposure'] == q) & (df_renda['rendimento_habitual'] <= 15000)]
    if len(sub) < 10:
        continue
    try:
        kde = gaussian_kde(sub['rendimento_habitual'].values,
                          weights=sub['peso'].values / sub['peso'].sum())
        x = np.linspace(0, 15000, 300)
        ax.plot(x, kde(x), color=colors_q[i], linewidth=2, label=q)
    except Exception:
        pass

ax.set_xlabel('Rendimento Habitual (R$)')
ax.set_ylabel('Densidade')
ax.set_title('Distribuicao de Renda por Quintil de Exposicao (KDE ponderado)')
ax.legend()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
plt.tight_layout()
plt.show()

# ======================================================================
# 3.4 - Curva de concentracao (exposicao ordenada por renda)
# ======================================================================
df_conc = df_renda.sort_values('rendimento_habitual').copy()
vals_c = np.array(df_conc['exposure_score'])
wgts_c = np.array(df_conc['peso'])
cum_pop_c = np.concatenate([[0], np.cumsum(wgts_c) / wgts_c.sum()])
cum_exp_c = np.concatenate([[0], np.cumsum(wgts_c * vals_c) / (wgts_c * vals_c).sum()])

fig, ax = plt.subplots(figsize=(7, 7))
ax.plot(cum_pop_c, cum_exp_c, color='darkorange', linewidth=2,
        label='Concentracao (exposicao | renda)')
ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Linha de igualdade')
ax.fill_between(cum_pop_c, cum_exp_c, np.linspace(0, 1, len(cum_pop_c)),
                alpha=0.1, color='darkorange')
ax.set_xlabel('Fracao acumulada da populacao (ordenada por renda)')
ax.set_ylabel('Fracao acumulada da exposicao')
ax.set_title('Curva de Concentracao: Exposicao ordenada por Renda')
ax.legend(loc='upper left')
ax.set_aspect('equal')

# Indice de concentracao
conc_area = np.trapz(cum_exp_c, cum_pop_c)
conc_index = 1 - 2 * conc_area
print(f"\nIndice de concentracao: {conc_index:.4f}")
if conc_index > 0:
    print("  > 0: exposicao concentrada entre os mais ricos")
elif conc_index < 0:
    print("  < 0: exposicao concentrada entre os mais pobres")

plt.tight_layout()
plt.show()

# ======================================================================
# 3.5 - Regressao quantilica
# ======================================================================
print("\n" + "=" * 70)
print("REGRESSAO QUANTILICA: log(renda) ~ exposicao + controles")
print("=" * 70)
print("\n  NOTA: QuantReg do statsmodels nao suporta pesos amostrais")
print("  nativamente. Os coeficientes podem diferir de uma estimacao")
print("  ponderada. Limitacao declarada.")

df_qreg = df_renda[['rendimento_habitual', 'exposure_score', 'sexo_texto',
                      'raca_agregada', 'idade', 'formal']].dropna().copy()
df_qreg['log_renda'] = np.log(df_qreg['rendimento_habitual'].clip(lower=1))

quantiles = [0.10, 0.25, 0.50, 0.75, 0.90]
qreg_results = []

for tau in quantiles:
    try:
        qr = smf.quantreg(
            'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + idade + I(idade**2) + formal',
            data=df_qreg
        ).fit(q=tau, max_iter=1000)
        coef = qr.params['exposure_score']
        se = qr.bse['exposure_score']
        ci = qr.conf_int().loc['exposure_score']
        pval = qr.pvalues['exposure_score']
        qreg_results.append({
            'Quantil': f'{tau:.2f}',
            'Coef. Exposicao': coef,
            'SE': se,
            'IC 95% Inf': ci[0],
            'IC 95% Sup': ci[1],
            'p-valor': pval,
            'Sig.': sig_stars(pval),
        })
        print(f"  tau={tau:.2f}: coef={coef:.4f} (SE={se:.4f}) {sig_stars(pval)}")
    except Exception as e:
        print(f"  tau={tau:.2f}: ERRO - {e}")

if qreg_results:
    tab_qreg = pd.DataFrame(qreg_results).set_index('Quantil')
    display(tab_qreg.round(4))

    # Grafico do processo quantilico
    fig, ax = plt.subplots(figsize=(10, 5))
    coefs = [r['Coef. Exposicao'] for r in qreg_results]
    ci_lo = [r['IC 95% Inf'] for r in qreg_results]
    ci_hi = [r['IC 95% Sup'] for r in qreg_results]
    ax.plot(quantiles, coefs, 'o-', color='steelblue', linewidth=2, markersize=8)
    ax.fill_between(quantiles, ci_lo, ci_hi, alpha=0.2, color='steelblue')
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)

    # Adicionar coeficiente OLS como referencia
    ols_model = smf.wls(
        'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + idade + I(idade**2) + formal',
        data=df_qreg, weights=df_renda.loc[df_qreg.index, 'peso']
    ).fit()
    ax.axhline(ols_model.params['exposure_score'], color='red', linestyle='--',
               linewidth=1.5, label=f'WLS media = {ols_model.params["exposure_score"]:.3f}')

    ax.set_xlabel('Quantil da Distribuicao de Renda')
    ax.set_ylabel('Coeficiente de Exposicao (log-renda)')
    ax.set_title('Processo Quantilico: Efeito da Exposicao ao Longo da Distribuicao de Renda')
    ax.legend()
    plt.tight_layout()
    plt.show()
    print("\nInterpretacao: Se o coeficiente cresce com o quantil, a exposicao")
    print("beneficia mais os trabalhadores de maior renda (complementaridade).")
    print("Se decresce, os de menor renda sao mais afetados (substituicao).")

# ======================================================================
# 3.X - Tabela Comparativa Brasil vs. WP140
# ======================================================================
print("\n" + "=" * 90)
print("COMPARACAO ESTRUTURADA: BRASIL vs. WP140 (por grupo de renda)")
print("=" * 90)

pct_nao_exposto = df_score[df_score['exposure_gradient'] == 'Not Exposed']['peso'].sum() / df_score['peso'].sum() * 100

comparacao = pd.DataFrame({
    'Indicador': [
        'Exposicao media',
        '% Nao Exposto',
        '% Alta Exposicao (G3-G4)',
        'Setor mais exposto',
        'Ocupacao mais exposta',
        'Gap genero (M-H)',
    ],
    'Brasil (este estudo)': [
        f'{mean_geral:.3f}',
        f'{pct_nao_exposto:.1f}%',
        f'{pct_alta:.1f}%',
        'Financas e Seguros',
        'Apoio administrativo',
        f'+{gap_sexo:.3f}' if 'gap_sexo' in dir() else 'ver secao 4',
    ],
    'Upper-Middle (WP140)': [
        '~0.29', '~52%', '~11%',
        'Financial services', 'Clerical support',
        'Mulheres > Homens',
    ],
    'High-Income (WP140)': [
        '~0.36', '~35%', '~20%',
        'Financial services', 'Clerical support',
        'Mulheres > Homens',
    ],
    'Global (WP140)': [
        '0.30', '~50%', '~12%',
        'Financial services', 'Clerical support',
        'Mulheres > Homens',
    ],
})
display(comparacao.set_index('Indicador'))

# ======================================================================
# 3.Y - Heatmap bidimensional exposicao x renda
# ======================================================================
print("\n" + "=" * 70)
print("HEATMAP: DISTRIBUICAO CONJUNTA EXPOSICAO x RENDA")
print("=" * 70)

df_renda['decil_renda'] = pd.qcut(
    df_renda['rendimento_habitual'], 10,
    labels=[f'R{i}' for i in range(1, 11)])

cross = df_renda.groupby(['decil_exposure', 'decil_renda'])['peso'].sum().unstack(fill_value=0)
cross = cross / 1e6  # em milhoes

fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(cross, cmap='YlOrRd', annot=True, fmt='.1f', ax=ax,
            cbar_kws={'label': 'Trabalhadores (milhoes)'})
ax.set_xlabel('Decil de Renda')
ax.set_ylabel('Decil de Exposicao')
ax.set_title('Distribuicao Conjunta: Exposicao a IA x Renda')
plt.tight_layout()
plt.show()

# ======================================================================
# 3.Z - Scatter plot de ocupacoes (bubble chart)
# ======================================================================
print("\n" + "=" * 70)
print("BUBBLE CHART: OCUPACOES (EXPOSICAO vs. RENDA)")
print("=" * 70)

ocup_agg = df_renda.groupby('cod_ocupacao').apply(lambda g: pd.Series({
    'exp_media': weighted_mean(g['exposure_score'], g['peso']),
    'renda_media': weighted_mean(g['rendimento_habitual'], g['peso']),
    'pop': g['peso'].sum() / 1e6,
    'grande_grupo': g['grande_grupo'].mode().iloc[0] if len(g['grande_grupo'].mode()) > 0 else 'Outros',
})).reset_index()

fig, ax = plt.subplots(figsize=(14, 9))
grupos = sorted(ocup_agg['grande_grupo'].unique())
cores_gg = plt.cm.tab10(np.linspace(0, 1, len(grupos)))
for grupo, cor in zip(grupos, cores_gg):
    sub = ocup_agg[ocup_agg['grande_grupo'] == grupo]
    ax.scatter(sub['exp_media'], sub['renda_media'],
               s=sub['pop']*50, alpha=0.6, color=cor, label=grupo, edgecolor='white')
ax.set_xlabel('Exposicao Media')
ax.set_ylabel('Renda Media (R$)')
ax.set_title('Ocupacoes: Exposicao vs. Renda (tamanho = populacao)')
ax.legend(fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))
plt.tight_layout()
plt.show()

# ======================================================================
# 3.W - Regressao quantilica continua (tau 0.05 a 0.95)
# ======================================================================
print("\n" + "=" * 70)
print("REGRESSAO QUANTILICA CONTINUA (tau 0.05 a 0.95)")
print("=" * 70)

df_quant = df_renda[['rendimento_habitual', 'exposure_score', 'sexo_texto',
                      'raca_agregada', 'idade', 'formal', 'nivel_instrucao']].dropna().copy()
df_quant['log_renda'] = np.log(df_quant['rendimento_habitual'].clip(lower=1))

taus = np.arange(0.05, 0.96, 0.05)
coefs_qr = []
for tau in taus:
    try:
        mod = smf.quantreg(
            'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
            'idade + I(idade**2) + C(nivel_instrucao) + formal',
            data=df_quant
        ).fit(q=tau, max_iter=1000)
        coefs_qr.append({
            'tau': tau,
            'coef': mod.params['exposure_score'],
            'ci_lo': mod.conf_int().loc['exposure_score', 0],
            'ci_hi': mod.conf_int().loc['exposure_score', 1],
        })
    except Exception as e:
        print(f"  tau={tau:.2f}: ERRO - {e}")

if coefs_qr:
    qr_df = pd.DataFrame(coefs_qr)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(qr_df['tau'], qr_df['ci_lo'], qr_df['ci_hi'],
                    alpha=0.2, color='steelblue')
    ax.plot(qr_df['tau'], qr_df['coef'], 'o-', color='steelblue', linewidth=2, markersize=4)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
    # OLS para referencia
    coef_ols_ref = mincer2.params['exposure_score'] if 'mincer2' in dir() else ols_model.params['exposure_score']
    ax.axhline(coef_ols_ref, color='red', linestyle='--', linewidth=1, label=f'OLS = {coef_ols_ref:.3f}')
    ax.set_xlabel('Quantil (tau)')
    ax.set_ylabel('Coeficiente de Exposicao')
    ax.set_title('Regressao Quantilica: Efeito da Exposicao ao Longo da Distribuicao de Renda')
    ax.legend()
    plt.tight_layout()
    plt.show()

    print("\n  NOTA: QuantReg nao suporta pesos amostrais nativamente.")
    print("  Coeficientes podem diferir de estimacao ponderada.")
```

    ======================================================================
    PERFIL DE RENDA POR QUINTIL DE EXPOSICAO
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | Renda Media (R\$) | IC 95% Inf | IC 95% Sup | Renda Mediana (R\$) | Exp. Media | % Formal | Pop. (milhoes) |
|----|----|----|----|----|----|----|----|
| Quintil |  |  |  |  |  |  |  |
| Q1 (Baixa) | 2000.000 | 1999.100 | 2000.900 | 1600.000 | 0.100 | 37.400 | 20.500 |
| Q2 | 2439.000 | 2437.600 | 2440.400 | 1900.000 | 0.200 | 30.000 | 17.700 |
| Q3 | 3290.400 | 3288.600 | 3292.200 | 2500.000 | 0.200 | 46.300 | 21.300 |
| Q4 | 4928.600 | 4925.400 | 4931.900 | 2900.000 | 0.400 | 52.300 | 17.200 |
| Q5 (Alta) | 4468.600 | 4466.000 | 4471.200 | 2900.000 | 0.500 | 50.100 | 19.200 |

</div>


    Razao renda Q5/Q1: 2.23x
      Q1 (Baixa exposicao): R$ 2,000
      Q5 (Alta exposicao):  R$ 4,469

      ⚠ ATENCAO: Q4 (R$ 4,929) > Q5 (R$ 4,469)
      A relacao exposicao-renda NAO e monotonica.
      Q4 concentra gerentes e profissionais liberais de alta renda
      em setores de exposicao moderada.

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-5-output-4.png)


    R² individual (WLS renda ~ exposicao): 0.0340
    R² agregado (decis): 0.6526
    Nota: R² agregado e artificialmente inflado por suavizar variancia individual.

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-5-output-6.png)

    /var/folders/9l/bxkb7j2s259_jlrwc_dnrklr0000gn/T/ipykernel_32166/213812379.py:145: DeprecationWarning: `trapz` is deprecated. Use `trapezoid` instead, or one of the numerical integration functions in `scipy.integrate`.
      conc_area = np.trapz(cum_exp_c, cum_pop_c)


    Indice de concentracao: 0.0810
      > 0: exposicao concentrada entre os mais ricos

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-5-output-9.png)


    ======================================================================
    REGRESSAO QUANTILICA: log(renda) ~ exposicao + controles
    ======================================================================

      NOTA: QuantReg do statsmodels nao suporta pesos amostrais
      nativamente. Os coeficientes podem diferir de uma estimacao
      ponderada. Limitacao declarada.
      tau=0.10: coef=0.6177 (SE=0.0130) ***
      tau=0.25: coef=0.9900 (SE=0.0138) ***
      tau=0.50: coef=1.2090 (SE=0.0109) ***
      tau=0.75: coef=1.8282 (SE=0.0139) ***
      tau=0.90: coef=2.4992 (SE=0.0186) ***

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|         | Coef. Exposicao | SE    | IC 95% Inf | IC 95% Sup | p-valor | Sig.   |
|---------|-----------------|-------|------------|------------|---------|--------|
| Quantil |                 |       |            |            |         |        |
| 0.10    | 0.618           | 0.013 | 0.592      | 0.643      | 0.000   | \*\*\* |
| 0.25    | 0.990           | 0.014 | 0.963      | 1.017      | 0.000   | \*\*\* |
| 0.50    | 1.209           | 0.011 | 1.188      | 1.230      | 0.000   | \*\*\* |
| 0.75    | 1.828           | 0.014 | 1.801      | 1.856      | 0.000   | \*\*\* |
| 0.90    | 2.499           | 0.019 | 2.463      | 2.536      | 0.000   | \*\*\* |

</div>

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-5-output-12.png)


    Interpretacao: Se o coeficiente cresce com o quantil, a exposicao
    beneficia mais os trabalhadores de maior renda (complementaridade).
    Se decresce, os de menor renda sao mais afetados (substituicao).

    ==========================================================================================
    COMPARACAO ESTRUTURADA: BRASIL vs. WP140 (por grupo de renda)
    ==========================================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | Brasil (este estudo) | Upper-Middle (WP140) | High-Income (WP140) | Global (WP140) |
|----|----|----|----|----|
| Indicador |  |  |  |  |
| Exposicao media | 0.278 | ~0.29 | ~0.36 | 0.30 |
| % Nao Exposto | 53.9% | ~52% | ~35% | ~50% |
| % Alta Exposicao (G3-G4) | 10.1% | ~11% | ~20% | ~12% |
| Setor mais exposto | Financas e Seguros | Financial services | Financial services | Financial services |
| Ocupacao mais exposta | Apoio administrativo | Clerical support | Clerical support | Clerical support |
| Gap genero (M-H) | +0.044 | Mulheres \> Homens | Mulheres \> Homens | Mulheres \> Homens |

</div>


    ======================================================================
    HEATMAP: DISTRIBUICAO CONJUNTA EXPOSICAO x RENDA
    ======================================================================

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-5-output-16.png)


    ======================================================================
    BUBBLE CHART: OCUPACOES (EXPOSICAO vs. RENDA)
    ======================================================================

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-5-output-18.png)


    ======================================================================
    REGRESSAO QUANTILICA CONTINUA (tau 0.05 a 0.95)
    ======================================================================

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-5-output-20.png)


      NOTA: QuantReg nao suporta pesos amostrais nativamente.
      Coeficientes podem diferir de estimacao ponderada.

### 4. Genero e raca

% de mulheres e de negros por quintil de exposicao; exposicao media por
sexo e raca.

**Analises:** - Exposicao por sexo e raca com ICs e testes t
ponderados - KDE comparativo: homens vs mulheres, brancos vs negros -
Exposicao por sexo x raca x quintil - Decomposicao Oaxaca-Blinder do gap
de genero - Decomposicao Oaxaca-Blinder do gap racial

> **Nota sobre categorias raciais:** Seguindo convenção estabelecida na
> literatura brasileira de desigualdade (Osorio, 2003; Soares, 2000), as
> categorias Preta e Parda do IBGE foram agregadas em “Negra”. A
> categoria “Outras” agrega Amarelos e Indígenas (1.0M de
> trabalhadores). Embora esses grupos tenham realidades socioeconômicas
> distintas, o tamanho amostral reduzido de cada um individualmente
> limita análises desagregadas robustas. Resultados para “Outras” devem
> ser interpretados com cautela.

> **Conexão com WP140 (gênero):** O WP140 (Seção 3.2, p. 24-26) encontra
> que mulheres estão sistematicamente mais expostas à IA generativa em
> todas as regiões do mundo, principalmente pela concentração feminina
> em trabalho clerical (ISCO Major Group 4). No Brasil, confirmamos esse
> padrão (gap de +0.044). O WP140 destaca que esse resultado pode ter
> implicações distributivas ambíguas: se a IA complementa o trabalho
> clerical, mulheres se beneficiam; se automatiza, mulheres são mais
> vulneráveis. A decomposição Oaxaca-Blinder que realizamos aprofunda
> essa análise para além do que o WP140 oferece.
>
> **Contribuição original (raça):** A análise por raça não é contemplada
> no WP140, que trabalha com dados globais sem essa desagregação. O gap
> racial de exposição (+0.048 para brancos) é uma contribuição
> específica desta dissertação ao debate sobre IA e desigualdade no
> Brasil.

``` python
# Etapa 1b.4 - Analise de Dados - Genero e raca

# ======================================================================
# 4.1 - Exposicao por sexo e raca com ICs e testes t
# ======================================================================
print("=" * 70)
print("EXPOSICAO POR GENERO E RACA")
print("=" * 70)

# --- Por sexo ---
print("\n--- Por Sexo ---")
rows_sexo = []
for sexo in ['Homem', 'Mulher']:
    sub = df_score[df_score['sexo_texto'] == sexo]
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
    rows_sexo.append({
        'Grupo': sexo,
        'Exp. Media': mean_e, 'IC Inf': ci_lo, 'IC Sup': ci_hi,
        '% Alta Exp.': n_alta / sub['peso'].sum() * 100,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })
    print(f"  {sexo}: {mean_e:.3f} [IC: {ci_lo:.3f} - {ci_hi:.3f}] | Pop: {sub['peso'].sum()/1e6:.1f}M")

# Teste t genero
sub_h = df_score[df_score['sexo_texto'] == 'Homem']
sub_m = df_score[df_score['sexo_texto'] == 'Mulher']
t_sexo, p_sexo = weighted_ttest_2groups(
    sub_h['exposure_score'], sub_h['peso'],
    sub_m['exposure_score'], sub_m['peso']
)
gap_sexo = rows_sexo[1]['Exp. Media'] - rows_sexo[0]['Exp. Media']
print(f"  Gap (M-H): {gap_sexo:+.3f} | t={t_sexo:.2f}, p={p_sexo:.4f} {sig_stars(p_sexo)}")

# d de Cohen ponderado para genero
d_sexo = weighted_cohen_d(
    sub_h['exposure_score'].values, sub_h['peso'].values,
    sub_m['exposure_score'].values, sub_m['peso'].values
)
print(f"  d de Cohen (H-M): {d_sexo:.3f} ({'pequeno' if abs(d_sexo)<0.5 else 'medio' if abs(d_sexo)<0.8 else 'grande'})")

# --- Por raca ---
print("\n--- Por Raca ---")
rows_raca = []
for raca in ['Branca', 'Negra', 'Outras']:
    sub = df_score[df_score['raca_agregada'] == raca]
    if len(sub) < 10:
        continue
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
    rows_raca.append({
        'Grupo': raca,
        'Exp. Media': mean_e, 'IC Inf': ci_lo, 'IC Sup': ci_hi,
        '% Alta Exp.': n_alta / sub['peso'].sum() * 100,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })
    print(f"  {raca}: {mean_e:.3f} [IC: {ci_lo:.3f} - {ci_hi:.3f}] | Pop: {sub['peso'].sum()/1e6:.1f}M")

# Teste t raca (Branca vs Negra)
sub_br = df_score[df_score['raca_agregada'] == 'Branca']
sub_ne = df_score[df_score['raca_agregada'] == 'Negra']
t_raca, p_raca = weighted_ttest_2groups(
    sub_br['exposure_score'], sub_br['peso'],
    sub_ne['exposure_score'], sub_ne['peso']
)
gap_raca = rows_raca[0]['Exp. Media'] - rows_raca[1]['Exp. Media']
print(f"  Gap (Branca-Negra): {gap_raca:+.3f} | t={t_raca:.2f}, p={p_raca:.4f} {sig_stars(p_raca)}")

# d de Cohen ponderado para raca
d_raca = weighted_cohen_d(
    sub_br['exposure_score'].values, sub_br['peso'].values,
    sub_ne['exposure_score'].values, sub_ne['peso'].values
)
print(f"  d de Cohen (B-N): {d_raca:.3f} ({'pequeno' if abs(d_raca)<0.5 else 'medio' if abs(d_raca)<0.8 else 'grande'})")

# Tabela consolidada
tab_genero_raca = pd.DataFrame(rows_sexo + rows_raca).set_index('Grupo')
display(tab_genero_raca.round(3))

# ======================================================================
# 4.2 - KDE comparativo por sexo e raca
# ======================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Painel A: Sexo
ax = axes[0]
for sexo, cor in [('Homem', 'steelblue'), ('Mulher', 'coral')]:
    sub = df_score[df_score['sexo_texto'] == sexo]
    kde = gaussian_kde(sub['exposure_score'].values,
                      weights=sub['peso'].values / sub['peso'].sum())
    x = np.linspace(0.05, 0.75, 200)
    ax.plot(x, kde(x), color=cor, linewidth=2, label=sexo)
ax.set_xlabel('Score de Exposicao')
ax.set_ylabel('Densidade')
ax.set_title(f'(A) Distribuicao por Sexo (p={p_sexo:.4f}{sig_stars(p_sexo)})')
ax.legend()

# Painel B: Raca
ax = axes[1]
for raca, cor in [('Branca', 'steelblue'), ('Negra', 'coral')]:
    sub = df_score[df_score['raca_agregada'] == raca]
    kde = gaussian_kde(sub['exposure_score'].values,
                      weights=sub['peso'].values / sub['peso'].sum())
    x = np.linspace(0.05, 0.75, 200)
    ax.plot(x, kde(x), color=cor, linewidth=2, label=raca)
ax.set_xlabel('Score de Exposicao')
ax.set_ylabel('Densidade')
ax.set_title(f'(B) Distribuicao por Raca (p={p_raca:.4f}{sig_stars(p_raca)})')
ax.legend()

plt.tight_layout()
plt.show()

# ======================================================================
# 4.3 - Exposicao por sexo x quintil
# ======================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Painel A: Sexo x Quintil
ax = axes[0]
data_sq = []
for q in QUINTIL_ORDER:
    for sexo in ['Homem', 'Mulher']:
        sub = df_score[(df_score['quintil_exposure'] == q) & (df_score['sexo_texto'] == sexo)]
        if len(sub) > 0:
            data_sq.append({'Quintil': q, 'Sexo': sexo, 'Pop': sub['peso'].sum() / 1e6})

df_sq = pd.DataFrame(data_sq)
df_pivot = df_sq.pivot(index='Quintil', columns='Sexo', values='Pop')
df_pivot.plot(kind='bar', ax=ax, color=['steelblue', 'coral'], edgecolor='white')
ax.set_ylabel('Populacao (milhoes)')
ax.set_title('(A) Populacao por Sexo e Quintil de Exposicao')
ax.tick_params(axis='x', rotation=45)
ax.legend(title='Sexo')

# Painel B: Raca x Quintil
ax = axes[1]
data_rq = []
for q in QUINTIL_ORDER:
    for raca in ['Branca', 'Negra']:
        sub = df_score[(df_score['quintil_exposure'] == q) & (df_score['raca_agregada'] == raca)]
        if len(sub) > 0:
            data_rq.append({'Quintil': q, 'Raca': raca, 'Pop': sub['peso'].sum() / 1e6})

df_rq = pd.DataFrame(data_rq)
df_pivot_r = df_rq.pivot(index='Quintil', columns='Raca', values='Pop')
df_pivot_r.plot(kind='bar', ax=ax, color=['steelblue', 'coral'], edgecolor='white')
ax.set_ylabel('Populacao (milhoes)')
ax.set_title('(B) Populacao por Raca e Quintil de Exposicao')
ax.tick_params(axis='x', rotation=45)
ax.legend(title='Raca')

plt.tight_layout()
plt.show()

# ======================================================================
# 4.4 - Decomposicao Oaxaca-Blinder do gap de genero
# ======================================================================
print("\n" + "=" * 70)
print("DECOMPOSICAO OAXACA-BLINDER DO GAP DE GENERO NA EXPOSICAO")
print("=" * 70)

# Preparar dados para decomposicao
df_ob = df_score[['exposure_score', 'sexo_texto', 'raca_agregada', 'idade',
                    'nivel_instrucao', 'grande_grupo', 'regiao', 'formal', 'peso']].dropna().copy()

# Criar dummies manualmente para controle total
formula_ob = 'exposure_score ~ C(raca_agregada) + idade + I(idade**2) + C(nivel_instrucao) + C(grande_grupo) + C(regiao) + formal'

df_h = df_ob[df_ob['sexo_texto'] == 'Homem']
df_m = df_ob[df_ob['sexo_texto'] == 'Mulher']

reg_h = smf.wls(formula_ob, data=df_h, weights=df_h['peso']).fit()
reg_m = smf.wls(formula_ob, data=df_m, weights=df_m['peso']).fit()

# Media das variaveis explicativas
import patsy
y_h, X_h = patsy.dmatrices(formula_ob, data=df_h, return_type='dataframe')
y_m, X_m = patsy.dmatrices(formula_ob, data=df_m, return_type='dataframe')

# Medias ponderadas das Xs
mean_X_h = np.average(X_h.values, axis=0, weights=df_h['peso'].values)
mean_X_m = np.average(X_m.values, axis=0, weights=df_m['peso'].values)

# Medias das Ys
mean_y_h = weighted_mean(df_h['exposure_score'], df_h['peso'])
mean_y_m = weighted_mean(df_m['exposure_score'], df_m['peso'])

# Decomposicao (referencia: coeficientes dos homens)
gap_total = mean_y_m - mean_y_h
explicado = (mean_X_m - mean_X_h) @ reg_h.params.values
nao_explicado = gap_total - explicado

print(f"\n  Exposicao media homens:   {mean_y_h:.4f}")
print(f"  Exposicao media mulheres: {mean_y_m:.4f}")
print(f"  Gap total (M - H):        {gap_total:+.4f}")
print(f"  Explicado (caracteristicas): {explicado:+.4f} ({explicado/gap_total*100:.1f}%)")
print(f"  Nao explicado (coeficientes): {nao_explicado:+.4f} ({nao_explicado/gap_total*100:.1f}%)")
pct_explicado = explicado/gap_total*100
print(f"\n  Interpretacao: {pct_explicado:.0f}% do gap de genero e explicado por")
print(f"  diferencas em escolaridade, ocupacao, regiao e formalidade.")
if pct_explicado > 100:
    print(f"  O componente explicado > 100% indica que, se mulheres tivessem")
    print(f"  a mesma composicao ocupacional que homens, seu gap de exposicao")
    print(f"  seria AINDA MAIOR. Mulheres estao sub-representadas nas ocupacoes")
    print(f"  de alta exposicao apesar de possuirem caracteristicas (escolaridade)")
    print(f"  que predizem maior exposicao — evidencia de segregacao ocupacional.")
else:
    print(f"  Os {abs(nao_explicado/gap_total*100):.0f}% restantes refletem segregacao ocupacional")
    print(f"  e diferente valoracao das mesmas caracteristicas.")

# ======================================================================
# 4.5 - Decomposicao Oaxaca-Blinder do gap racial
# ======================================================================
print("\n" + "=" * 70)
print("DECOMPOSICAO OAXACA-BLINDER DO GAP RACIAL NA EXPOSICAO")
print("=" * 70)

formula_ob_raca = 'exposure_score ~ C(sexo_texto) + idade + I(idade**2) + C(nivel_instrucao) + C(grande_grupo) + C(regiao) + formal'

df_br = df_ob[df_ob['raca_agregada'] == 'Branca']
df_ne = df_ob[df_ob['raca_agregada'] == 'Negra']

reg_br = smf.wls(formula_ob_raca, data=df_br, weights=df_br['peso']).fit()
reg_ne = smf.wls(formula_ob_raca, data=df_ne, weights=df_ne['peso']).fit()

y_br, X_br = patsy.dmatrices(formula_ob_raca, data=df_br, return_type='dataframe')
y_ne, X_ne = patsy.dmatrices(formula_ob_raca, data=df_ne, return_type='dataframe')

mean_X_br = np.average(X_br.values, axis=0, weights=df_br['peso'].values)
mean_X_ne = np.average(X_ne.values, axis=0, weights=df_ne['peso'].values)

mean_y_br = weighted_mean(df_br['exposure_score'], df_br['peso'])
mean_y_ne = weighted_mean(df_ne['exposure_score'], df_ne['peso'])

gap_raca_total = mean_y_br - mean_y_ne
explicado_raca = (mean_X_br - mean_X_ne) @ reg_ne.params.values
nao_explicado_raca = gap_raca_total - explicado_raca

print(f"\n  Exposicao media brancos: {mean_y_br:.4f}")
print(f"  Exposicao media negros:  {mean_y_ne:.4f}")
print(f"  Gap total (B - N):       {gap_raca_total:+.4f}")
print(f"  Explicado (caracteristicas): {explicado_raca:+.4f} ({explicado_raca/gap_raca_total*100:.1f}%)")
print(f"  Nao explicado (coeficientes): {nao_explicado_raca:+.4f} ({nao_explicado_raca/gap_raca_total*100:.1f}%)")
print(f"\n  Interpretacao: Trabalhadores brancos tem maior exposicao a IA")
print(f"  ({gap_raca_total:+.3f}), refletindo concentracao em ocupacoes")
print(f"  de maior qualificacao e setores mais tecnologicos.")
```

    ======================================================================
    EXPOSICAO POR GENERO E RACA
    ======================================================================

    --- Por Sexo ---
      Homem: 0.259 [IC: 0.259 - 0.259] | Pop: 54.3M
      Mulher: 0.303 [IC: 0.303 - 0.303] | Pop: 42.7M
      Gap (M-H): +0.044 | t=-1473.74, p=0.0000 ***
      d de Cohen (H-M): -0.301 (pequeno)

    --- Por Raca ---
      Branca: 0.305 [IC: 0.305 - 0.305] | Pop: 41.9M
      Negra: 0.257 [IC: 0.257 - 0.257] | Pop: 54.0M
      Outras: 0.301 [IC: 0.301 - 0.302] | Pop: 1.0M
      Gap (Branca-Negra): +0.048 | t=1601.17, p=0.0000 ***
      d de Cohen (B-N): 0.330 (pequeno)

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|        | Exp. Media | IC Inf | IC Sup | % Alta Exp. | Pop. (milhoes) |
|--------|------------|--------|--------|-------------|----------------|
| Grupo  |            |        |        |             |                |
| Homem  | 0.259      | 0.259  | 0.259  | 6.688       | 54.292         |
| Mulher | 0.303      | 0.303  | 0.303  | 14.397      | 42.674         |
| Branca | 0.305      | 0.305  | 0.305  | 12.403      | 41.881         |
| Negra  | 0.257      | 0.257  | 0.257  | 8.255       | 54.046         |
| Outras | 0.301      | 0.301  | 0.302  | 11.432      | 1.039          |

</div>

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-6-output-3.png)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-6-output-4.png)


    ======================================================================
    DECOMPOSICAO OAXACA-BLINDER DO GAP DE GENERO NA EXPOSICAO
    ======================================================================

      Exposicao media homens:   0.2589
      Exposicao media mulheres: 0.3028
      Gap total (M - H):        +0.0439
      Explicado (caracteristicas): +0.0542 (123.3%)
      Nao explicado (coeficientes): -0.0103 (-23.3%)

      Interpretacao: 123% do gap de genero e explicado por
      diferencas em escolaridade, ocupacao, regiao e formalidade.
      O componente explicado > 100% indica que, se mulheres tivessem
      a mesma composicao ocupacional que homens, seu gap de exposicao
      seria AINDA MAIOR. Mulheres estao sub-representadas nas ocupacoes
      de alta exposicao apesar de possuirem caracteristicas (escolaridade)
      que predizem maior exposicao — evidencia de segregacao ocupacional.

    ======================================================================
    DECOMPOSICAO OAXACA-BLINDER DO GAP RACIAL NA EXPOSICAO
    ======================================================================

      Exposicao media brancos: 0.3050
      Exposicao media negros:  0.2571
      Gap total (B - N):       +0.0479
      Explicado (caracteristicas): +0.0355 (74.1%)
      Nao explicado (coeficientes): +0.0124 (25.9%)

      Interpretacao: Trabalhadores brancos tem maior exposicao a IA
      (+0.048), refletindo concentracao em ocupacoes
      de maior qualificacao e setores mais tecnologicos.

### 4b. Idade e escolaridade

Exposicao media por faixa etaria e por nivel de instrucao.

**Analises:** - Exposicao media por faixa etaria (5 em 5 anos) com ICs -
Exposicao media por nivel de instrucao com ICs - KDE sobrepostas por
nivel de instrucao - Cross-tab: faixa etaria x nivel de instrucao x
exposicao media

``` python
# Etapa 1b.4b - Idade e Escolaridade

# ======================================================================
# 4b.1 - Exposicao por faixa etaria
# ======================================================================
print("=" * 70)
print("EXPOSICAO POR FAIXA ETARIA")
print("=" * 70)

bins_idade = [14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 100]
labels_idade = ['15-19', '20-24', '25-29', '30-34', '35-39',
                '40-44', '45-49', '50-54', '55-59', '60-64', '65+']
df_score['faixa_etaria'] = pd.cut(df_score['idade'], bins=bins_idade, labels=labels_idade)

rows_idade = []
for faixa in labels_idade:
    sub = df_score[df_score['faixa_etaria'] == faixa]
    if len(sub) < 10:
        continue
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    rows_idade.append({
        'Faixa': faixa, 'Exp. Media': mean_e,
        'IC Inf': ci_lo, 'IC Sup': ci_hi,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })

tab_idade = pd.DataFrame(rows_idade).set_index('Faixa')
display(tab_idade.round(3))

fig, ax = plt.subplots(figsize=(12, 5))
ax.errorbar(range(len(tab_idade)), tab_idade['Exp. Media'],
            yerr=[tab_idade['Exp. Media']-tab_idade['IC Inf'],
                  tab_idade['IC Sup']-tab_idade['Exp. Media']],
            fmt='o-', capsize=4, color='steelblue', linewidth=2)
ax.set_xticks(range(len(tab_idade)))
ax.set_xticklabels(tab_idade.index, rotation=45)
ax.set_ylabel('Exposicao Media')
ax.set_xlabel('Faixa Etaria')
ax.set_title('Exposicao a IA Generativa por Faixa Etaria')
plt.tight_layout()
plt.show()

# ======================================================================
# 4b.2 - Exposicao por nivel de instrucao
# ======================================================================
print("\n" + "=" * 70)
print("EXPOSICAO POR NIVEL DE INSTRUCAO")
print("=" * 70)

# Usar edu_simples se disponivel, senao nivel_instrucao
edu_col = 'edu_simples' if 'edu_simples' in df_score.columns else 'nivel_instrucao'
rows_edu = []
for edu in df_score[edu_col].dropna().unique():
    sub = df_score[df_score[edu_col] == edu]
    if len(sub) < 10:
        continue
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    rows_edu.append({
        'Nivel': edu, 'Exp. Media': mean_e,
        'IC Inf': ci_lo, 'IC Sup': ci_hi,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })

tab_edu = pd.DataFrame(rows_edu).sort_values('Exp. Media').set_index('Nivel')
display(tab_edu.round(3))

fig, ax = plt.subplots(figsize=(12, 5))
tab_edu_plot = tab_edu.sort_values('Exp. Media')
ax.barh(range(len(tab_edu_plot)), tab_edu_plot['Exp. Media'], color='steelblue',
        xerr=[tab_edu_plot['Exp. Media']-tab_edu_plot['IC Inf'],
              tab_edu_plot['IC Sup']-tab_edu_plot['Exp. Media']],
        capsize=3, edgecolor='white')
ax.set_yticks(range(len(tab_edu_plot)))
ax.set_yticklabels(tab_edu_plot.index)
ax.set_xlabel('Exposicao Media')
ax.set_title('Exposicao a IA Generativa por Nivel de Instrucao')
plt.tight_layout()
plt.show()

# ======================================================================
# 4b.3 - KDE sobrepostas por nivel de instrucao
# ======================================================================
if 'edu_simples' in df_score.columns:
    fig, ax = plt.subplots(figsize=(10, 5))
    edu_order_kde = ['Sem/Fund.Inc.', 'Fund.Comp.', 'Med.Comp.', 'Sup.Comp.']
    cores_edu = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']
    for edu, cor in zip(edu_order_kde, cores_edu):
        sub = df_score[df_score['edu_simples'] == edu]
        if len(sub) < 100:
            continue
        kde = gaussian_kde(sub['exposure_score'].values,
                           weights=sub['peso'].values / sub['peso'].sum())
        x = np.linspace(0.05, 0.75, 200)
        ax.plot(x, kde(x), color=cor, linewidth=2, label=edu)
    ax.set_xlabel('Score de Exposicao')
    ax.set_ylabel('Densidade')
    ax.set_title('Distribuicao de Exposicao por Nivel de Instrucao')
    ax.legend()
    plt.tight_layout()
    plt.show()

# ======================================================================
# 4b.4 - Cross-tab: faixa etaria x nivel de instrucao x exposicao
# ======================================================================
if 'edu_simples' in df_score.columns:
    print("\n" + "=" * 70)
    print("CROSS-TAB: FAIXA ETARIA x EDUCACAO x EXPOSICAO MEDIA")
    print("=" * 70)

    pivot_idade_edu = df_score.groupby(['faixa_etaria', 'edu_simples']).apply(
        lambda x: weighted_mean(x['exposure_score'], x['peso'])
    ).unstack(fill_value=np.nan)

    edu_order_ct = ['Sem/Fund.Inc.', 'Fund.Comp.', 'Med.Comp.', 'Sup.Comp.']
    cols_available = [c for c in edu_order_ct if c in pivot_idade_edu.columns]
    if cols_available:
        pivot_idade_edu = pivot_idade_edu[cols_available]
    display(pivot_idade_edu.round(3))
```

    ======================================================================
    EXPOSICAO POR FAIXA ETARIA
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|       | Exp. Media | IC Inf | IC Sup | Pop. (milhoes) |
|-------|------------|--------|--------|----------------|
| Faixa |            |        |        |                |
| 15-19 | 0.306      | 0.306  | 0.306  | 2.555          |
| 20-24 | 0.304      | 0.304  | 0.305  | 10.157         |
| 25-29 | 0.297      | 0.297  | 0.297  | 12.220         |
| 30-34 | 0.291      | 0.291  | 0.291  | 12.475         |
| 35-39 | 0.284      | 0.284  | 0.284  | 12.754         |
| 40-44 | 0.273      | 0.273  | 0.273  | 12.948         |
| 45-49 | 0.263      | 0.263  | 0.263  | 11.682         |
| 50-54 | 0.255      | 0.255  | 0.255  | 9.415          |
| 55-59 | 0.251      | 0.251  | 0.252  | 7.297          |
| 60-64 | 0.253      | 0.253  | 0.253  | 4.828          |
| 65+   | 0.260      | 0.260  | 0.261  | 0.637          |

</div>

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-7-output-3.png)


    ======================================================================
    EXPOSICAO POR NIVEL DE INSTRUCAO
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|               | Exp. Media | IC Inf | IC Sup | Pop. (milhoes) |
|---------------|------------|--------|--------|----------------|
| Nivel         |            |        |        |                |
| Sem/Fund.Inc. | 0.179      | 0.179  | 0.179  | 16.721         |
| Fund.Comp.    | 0.204      | 0.204  | 0.204  | 6.040          |
| Med.Inc.      | 0.218      | 0.218  | 0.218  | 5.959          |
| Med.Comp.     | 0.275      | 0.275  | 0.275  | 37.561         |
| Sup.Inc.      | 0.359      | 0.359  | 0.359  | 6.464          |
| Sup.Comp.     | 0.364      | 0.364  | 0.364  | 24.221         |

</div>

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-7-output-6.png)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-7-output-7.png)


    ======================================================================
    CROSS-TAB: FAIXA ETARIA x EDUCACAO x EXPOSICAO MEDIA
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

| edu_simples  | Sem/Fund.Inc. | Fund.Comp. | Med.Comp. | Sup.Comp. |
|--------------|---------------|------------|-----------|-----------|
| faixa_etaria |               |            |           |           |
| 15-19        | 0.173         | 0.202      | 0.333     | 0.386     |
| 20-24        | 0.181         | 0.200      | 0.297     | 0.383     |
| 25-29        | 0.172         | 0.190      | 0.279     | 0.376     |
| 30-34        | 0.173         | 0.196      | 0.270     | 0.374     |
| 35-39        | 0.174         | 0.193      | 0.269     | 0.368     |
| 40-44        | 0.173         | 0.199      | 0.260     | 0.358     |
| 45-49        | 0.177         | 0.215      | 0.257     | 0.359     |
| 50-54        | 0.180         | 0.211      | 0.264     | 0.347     |
| 55-59        | 0.185         | 0.215      | 0.269     | 0.350     |
| 60-64        | 0.187         | 0.220      | 0.277     | 0.357     |
| 65+          | 0.204         | 0.243      | 0.285     | 0.349     |

</div>

### 5. Formalidade

% formal por quintil de exposicao; exposicao media no formal vs
informal.

**Analises:** - Exposicao por formalidade com ICs e teste t ponderado -
Investigacao do “paradoxo da formalidade”: cross-tab quintil x
formalidade x renda + regressao com interacao - KDE: formal vs informal

> **Interpretação da interação:** O coeficiente da interação
> exposição×formalidade é **negativo** (-1.21, p\<0.001). Isso significa
> que o retorno da exposição sobre a renda é MENOR para trabalhadores
> formais do que para informais. Profissionais liberais informais de
> alta exposição (consultores, advogados autônomos, médicos com CNPJ)
> capturam mais retorno da exposição à IA do que empregados formais
> equivalentes.

> **Contribuição original (formalidade):** A distinção formal/informal
> não aparece no WP140 (irrelevante em países de alta renda onde a
> informalidade é marginal). No Brasil, onde ~57% da força de trabalho é
> informal, essa dimensão é central. A OIT tem interesse particular na
> questão (ILO, 2018 — Women and Men in the Informal Economy) e esta
> análise conecta dois temas prioritários da agenda OIT: IA generativa e
> informalidade.

``` python
# Etapa 1b.5 - Analise de Dados - Formalidade

# ======================================================================
# 5.1 - Exposicao por formalidade com ICs e teste t
# ======================================================================
print("=" * 70)
print("EXPOSICAO: FORMAL vs INFORMAL")
print("=" * 70)

rows_formal = []
for val, label in [(1, 'Formal'), (0, 'Informal')]:
    sub = df_score[df_score['formal'] == val]
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
    sub_r = sub[sub['tem_renda'] == 1]
    mean_renda = weighted_mean(sub_r['rendimento_habitual'], sub_r['peso']) if len(sub_r) > 0 else np.nan
    rows_formal.append({
        'Tipo': label,
        'Exp. Media': mean_e, 'IC Inf': ci_lo, 'IC Sup': ci_hi,
        '% Alta Exp.': n_alta / sub['peso'].sum() * 100,
        'Renda Media (R$)': mean_renda,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })
    print(f"  {label}: Exp={mean_e:.3f} [IC: {ci_lo:.3f}-{ci_hi:.3f}] | "
          f"Renda=R${mean_renda:,.0f} | Pop={sub['peso'].sum()/1e6:.1f}M")

# Teste t
sub_f = df_score[df_score['formal'] == 1]
sub_i = df_score[df_score['formal'] == 0]
t_form, p_form = weighted_ttest_2groups(
    sub_f['exposure_score'], sub_f['peso'],
    sub_i['exposure_score'], sub_i['peso']
)
print(f"  Gap (F-I): {rows_formal[0]['Exp. Media']-rows_formal[1]['Exp. Media']:+.3f} | "
      f"t={t_form:.2f}, p={p_form:.4f} {sig_stars(p_form)}")

tab_formal = pd.DataFrame(rows_formal).set_index('Tipo')
display(tab_formal.round(3))

# ======================================================================
# 5.2 - KDE formal vs informal
# ======================================================================
fig, ax = plt.subplots(figsize=(10, 5))
for val, label, cor in [(1, 'Formal', 'steelblue'), (0, 'Informal', 'coral')]:
    sub = df_score[df_score['formal'] == val]
    kde = gaussian_kde(sub['exposure_score'].values,
                      weights=sub['peso'].values / sub['peso'].sum())
    x = np.linspace(0.05, 0.75, 200)
    ax.plot(x, kde(x), color=cor, linewidth=2, label=label)
ax.set_xlabel('Score de Exposicao')
ax.set_ylabel('Densidade')
ax.set_title(f'Distribuicao de Exposicao: Formal vs Informal (p={p_form:.4f}{sig_stars(p_form)})')
ax.legend()
plt.tight_layout()
plt.show()

# ======================================================================
# 5.3 - Investigacao do "paradoxo": quintil x formalidade x renda
# ======================================================================
print("\n" + "=" * 70)
print("INVESTIGACAO: RENDA POR QUINTIL DE EXPOSICAO E FORMALIDADE")
print("=" * 70)

rows_qf = []
for q in QUINTIL_ORDER:
    for val, label in [(1, 'Formal'), (0, 'Informal')]:
        sub = df_renda[(df_renda['quintil_exposure'] == q) & (df_renda['formal'] == val)]
        if len(sub) < 10:
            continue
        mean_r = weighted_mean(sub['rendimento_habitual'], sub['peso'])
        rows_qf.append({
            'Quintil': q, 'Tipo': label, 'Renda Media': mean_r,
            'Pop (milhoes)': sub['peso'].sum()/1e6,
        })

tab_qf = pd.DataFrame(rows_qf)
tab_qf_pivot = tab_qf.pivot(index='Quintil', columns='Tipo', values='Renda Media')
display(tab_qf_pivot.round(0))

# Grafico
fig, ax = plt.subplots(figsize=(10, 5))
tab_qf_pivot.plot(kind='bar', ax=ax, color=['coral', 'steelblue'], edgecolor='white')
ax.set_ylabel('Renda Media (R$)')
ax.set_title('Renda por Quintil de Exposicao e Formalidade')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
ax.tick_params(axis='x', rotation=45)
ax.legend(title='')
plt.tight_layout()
plt.show()

# ======================================================================
# 5.4 - Regressao com interacao exposicao x formalidade
# ======================================================================
print("\n--- Regressao: log(renda) ~ exposicao * formalidade + controles ---")

df_reg_formal = df_renda[['rendimento_habitual', 'exposure_score', 'formal',
                            'sexo_texto', 'raca_agregada', 'idade', 'regiao']].dropna().copy()
df_reg_formal['log_renda'] = np.log(df_reg_formal['rendimento_habitual'].clip(lower=1))

model_formal = smf.wls(
    'log_renda ~ exposure_score * formal + C(sexo_texto) + C(raca_agregada) + idade + I(idade**2) + C(regiao)',
    data=df_reg_formal,
    weights=df_renda.loc[df_reg_formal.index, 'peso']
).fit(cov_type='HC1')

print(f"\n  exposure_score:         {model_formal.params['exposure_score']:+.4f} "
      f"(p={model_formal.pvalues['exposure_score']:.4f}{sig_stars(model_formal.pvalues['exposure_score'])})")
print(f"  formal:                 {model_formal.params['formal']:+.4f} "
      f"(p={model_formal.pvalues['formal']:.4f}{sig_stars(model_formal.pvalues['formal'])})")
print(f"  exposure_score:formal:  {model_formal.params['exposure_score:formal']:+.4f} "
      f"(p={model_formal.pvalues['exposure_score:formal']:.4f}{sig_stars(model_formal.pvalues['exposure_score:formal'])})")
print(f"  R²: {model_formal.rsquared:.4f} | N: {int(model_formal.nobs):,}")

coef_interacao = model_formal.params['exposure_score:formal']
direcao = "MENOR" if coef_interacao < 0 else "MAIOR"
beneficiario = "informais" if coef_interacao < 0 else "formais"

print(f"\n  Interpretacao: A interacao exposicao:formal e significativa")
print(f"  (coef = {coef_interacao:.4f}, p<0.001).")
print(f"  O retorno da exposicao sobre a renda e {direcao} para trabalhadores")
print(f"  formais do que para informais.")
print(f"  Trabalhadores {beneficiario} de alta exposicao capturam mais retorno,")
print(f"  possivelmente refletindo profissionais liberais autonomos (consultores,")
print(f"  advogados, medicos com CNPJ) que operam na informalidade mas em")
print(f"  ocupacoes de alta qualificacao e alta exposicao a IA.")
```

    ======================================================================
    EXPOSICAO: FORMAL vs INFORMAL
    ======================================================================
      Formal: Exp=0.305 [IC: 0.305-0.305] | Renda=R$3,216 | Pop=41.4M
      Informal: Exp=0.258 [IC: 0.258-0.259] | Renda=R$3,519 | Pop=55.5M
      Gap (F-I): +0.046 | t=1549.24, p=0.0000 ***

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|          | Exp. Media | IC Inf | IC Sup | % Alta Exp. | Renda Media (R\$) | Pop. (milhoes) |
|----------|------------|--------|--------|-------------|-------------------|----------------|
| Tipo     |            |        |        |             |                   |                |
| Formal   | 0.305      | 0.305  | 0.305  | 14.804      | 3216.103          | 41.442         |
| Informal | 0.258      | 0.258  | 0.259  | 6.555       | 3518.691          | 55.525         |

</div>

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-8-output-3.png)


    ======================================================================
    INVESTIGACAO: RENDA POR QUINTIL DE EXPOSICAO E FORMALIDADE
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

| Tipo       | Formal   | Informal |
|------------|----------|----------|
| Quintil    |          |          |
| Q1 (Baixa) | 2135.000 | 1919.000 |
| Q2         | 2545.000 | 2394.000 |
| Q3         | 2972.000 | 3565.000 |
| Q4         | 3898.000 | 6058.000 |
| Q5 (Alta)  | 4058.000 | 4881.000 |

</div>

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-8-output-6.png)


    --- Regressao: log(renda) ~ exposicao * formalidade + controles ---

      exposure_score:         +2.1301 (p=0.0000***)
      formal:                 +0.4471 (p=0.0000***)
      exposure_score:formal:  -1.2137 (p=0.0000***)
      R²: 0.2485 | N: 202,471

      Interpretacao: A interacao exposicao:formal e significativa
      (coef = -1.2137, p<0.001).
      O retorno da exposicao sobre a renda e MENOR para trabalhadores
      formais do que para informais.
      Trabalhadores informais de alta exposicao capturam mais retorno,
      possivelmente refletindo profissionais liberais autonomos (consultores,
      advogados, medicos com CNPJ) que operam na informalidade mas em
      ocupacoes de alta qualificacao e alta exposicao a IA.

### 5b. Augmentation vs. Automacao

Comparacao entre trabalhadores em gradientes de complementaridade
(G1-G2) e de transformacao radical (G3-G4), seguindo a distincao central
do WP140.

**Analises:** - Perfil comparativo: renda, genero, raca, escolaridade,
formalidade, setor - Grafico de barras agrupadas lado a lado - Testes de
diferenca entre os dois grupos

> **Referencia WP140:** “The results suggest that most occupations and
> industries are more likely to be transformed through augmentation
> rather than automation” (Gmyrek et al., 2025, p.1). Esta secao
> investiga se esse padrao se confirma para o Brasil.

``` python
# Etapa 1b.5b - Augmentation vs. Automacao

AUGMENTATION = ['Exposed: Gradient 1', 'Exposed: Gradient 2']
HIGH_TRANSFORM = ['Exposed: Gradient 3', 'Exposed: Gradient 4']

df_score['tipo_exposicao'] = np.where(
    df_score['exposure_gradient'].isin(AUGMENTATION), 'Augmentation (G1-G2)',
    np.where(df_score['exposure_gradient'].isin(HIGH_TRANSFORM), 'Alta Transformacao (G3-G4)',
    'Nao/Minima Exposicao'))

# Apenas os dois grupos de interesse
df_aug = df_score[df_score['tipo_exposicao'].isin(
    ['Augmentation (G1-G2)', 'Alta Transformacao (G3-G4)'])]

print("=" * 70)
print("AUGMENTATION vs. ALTA TRANSFORMACAO")
print("=" * 70)

rows_tipo = []
for tipo in ['Augmentation (G1-G2)', 'Alta Transformacao (G3-G4)']:
    sub = df_aug[df_aug['tipo_exposicao'] == tipo]
    sub_r = sub[sub['tem_renda'] == 1]
    rows_tipo.append({
        'Tipo': tipo,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
        'Exp. Media': weighted_mean(sub['exposure_score'], sub['peso']),
        'Renda Media': weighted_mean(sub_r['rendimento_habitual'], sub_r['peso']) if len(sub_r) > 0 else np.nan,
        '% Mulheres': weighted_mean((sub['sexo_texto']=='Mulher').astype(int), sub['peso'])*100,
        '% Formal': weighted_mean(sub['formal'], sub['peso'])*100,
        '% Sup. Completo': weighted_mean(
            (sub['edu_simples']=='Sup.Comp.').astype(int), sub['peso'])*100 if 'edu_simples' in sub.columns else np.nan,
    })

tab_tipo = pd.DataFrame(rows_tipo).set_index('Tipo')
display(tab_tipo.round(1))

# Grafico de barras agrupadas
metricas = ['Renda Media', '% Mulheres', '% Formal', '% Sup. Completo']
fig, axes = plt.subplots(1, len(metricas), figsize=(16, 5))
for ax, met in zip(axes, metricas):
    vals = [tab_tipo.loc[t, met] for t in tab_tipo.index]
    bars = ax.bar(range(len(vals)), vals, color=['steelblue', '#d62728'])
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(['Augment.', 'Alta Transf.'], fontsize=9)
    ax.set_title(met, fontsize=10)
    for b, v in zip(bars, vals):
        if not np.isnan(v):
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                    f'{v:.1f}', ha='center', fontsize=9)
plt.suptitle('Augmentation vs. Alta Transformacao: Perfil Comparativo', fontsize=13)
plt.tight_layout()
plt.show()

# Teste de diferenca
sub_aug = df_aug[df_aug['tipo_exposicao'] == 'Augmentation (G1-G2)']
sub_ht = df_aug[df_aug['tipo_exposicao'] == 'Alta Transformacao (G3-G4)']
sub_aug_r = sub_aug[sub_aug['tem_renda'] == 1]
sub_ht_r = sub_ht[sub_ht['tem_renda'] == 1]

if len(sub_aug_r) > 10 and len(sub_ht_r) > 10:
    t_aug, p_aug = weighted_ttest_2groups(
        sub_aug_r['rendimento_habitual'], sub_aug_r['peso'],
        sub_ht_r['rendimento_habitual'], sub_ht_r['peso'])
    d_aug = weighted_cohen_d(
        sub_aug_r['rendimento_habitual'].values, sub_aug_r['peso'].values,
        sub_ht_r['rendimento_habitual'].values, sub_ht_r['peso'].values)
    print(f"\nDiferenca de renda (Aug vs HT): t={t_aug:.2f}, p={p_aug:.4f} {sig_stars(p_aug)}")
    print(f"d de Cohen: {d_aug:.3f}")
```

    ======================================================================
    AUGMENTATION vs. ALTA TRANSFORMACAO
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | Pop. (milhoes) | Exp. Media | Renda Media | % Mulheres | % Formal | % Sup. Completo |
|----|----|----|----|----|----|----|
| Tipo |  |  |  |  |  |  |
| Augmentation (G1-G2) | 18.700 | 0.400 | 4179.200 | 47.100 | 44.000 | 31.900 |
| Alta Transformacao (G3-G4) | 9.800 | 0.600 | 3793.100 | 62.900 | 62.800 | 44.300 |

</div>

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-9-output-3.png)


    Diferenca de renda (Aug vs HT): t=181.00, p=0.0000 ***
    d de Cohen: 0.072

### 6. Setor e ocupacao

Exposicao media por setor_agregado e por grande_grupo; concentracao em
setores criticos IA.

**Analises:** - Exposicao por setor com ICs e ANOVA ponderada -
Exposicao por grupo ocupacional com ICs e ANOVA ponderada - Educacao
DENTRO de grupos ocupacionais (cross-tab) - Heatmap regiao x setor

> **Nota metodológica:** O R² elevado da ANOVA por grupo ocupacional
> (≈0.68) é em grande parte um artefato da construção do índice ILO, que
> atribui scores por ocupação ISCO a 4 dígitos. Como os grandes grupos
> são agrupamentos a 1 dígito dessas ocupações, a alta explicação é
> esperada e não constitui um achado empírico.
>
> A variação de exposição DENTRO dos grupos, observada na cross-tab com
> educação, é mínima — confirmando que o índice é uma propriedade da
> ocupação, não do indivíduo. A correlação exposição-escolaridade no
> nível individual opera via sorting: trabalhadores mais educados
> acessam ocupações de maior exposição.

> **Conexão com WP140 (Tabela 2):** O ranking ocupacional brasileiro
> replica a hierarquia global do WP140: Clerical Support Workers (Apoio
> Administrativo) é o grupo mais exposto, seguido de Professionals e
> Managers. Elementary Occupations está na base. A única diferença
> notável é que no Brasil, “Serviços e Vendedores” tem exposição
> relativamente alta (0.305 vs ~0.25 global), possivelmente pela
> estrutura do comércio brasileiro que incorpora mais tarefas
> administrativas/digitais nas funções de venda.

``` python
# Etapa 1b.6 - Analise de Dados - Setor e ocupacao

# ======================================================================
# 6.1 - Exposicao por setor com ICs e ANOVA
# ======================================================================
print("=" * 70)
print("EXPOSICAO POR SETOR ECONOMICO")
print("=" * 70)

rows_setor = []
for setor in sorted(df_score['setor_agregado'].unique()):
    sub = df_score[df_score['setor_agregado'] == setor]
    if len(sub) < 10:
        continue
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
    is_critico = setor in SETORES_CRITICOS_IA
    rows_setor.append({
        'Setor': setor,
        'Exp. Media': mean_e, 'IC Inf': ci_lo, 'IC Sup': ci_hi,
        '% Alta Exp.': n_alta / sub['peso'].sum() * 100,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
        'Critico IA': '*' if is_critico else '',
    })

tab_setor = pd.DataFrame(rows_setor).sort_values('Exp. Media', ascending=False).set_index('Setor')
display(tab_setor.round(3))

# ANOVA ponderada via WLS
model_anova_setor = smf.wls(
    'exposure_score ~ C(setor_agregado)',
    data=df_score, weights=df_score['peso']
).fit()
f_stat = model_anova_setor.fvalue
f_pval = model_anova_setor.f_pvalue
print(f"\nANOVA ponderada (setores): F={f_stat:.1f}, p={f_pval:.2e} {sig_stars(f_pval)}")
print(f"R²: {model_anova_setor.rsquared:.4f} (variacao explicada pelos setores)")

# Grafico setores
fig, ax = plt.subplots(figsize=(12, 7))
tab_plot = tab_setor.reset_index().sort_values('Exp. Media')
colors = ['#d62728' if c == '*' else 'steelblue' for c in tab_plot['Critico IA']]
yerr = [tab_plot['Exp. Media'] - tab_plot['IC Inf'], tab_plot['IC Sup'] - tab_plot['Exp. Media']]
ax.barh(tab_plot['Setor'], tab_plot['Exp. Media'], xerr=yerr, color=colors,
        edgecolor='white', linewidth=0.5, capsize=3)
for i, (_, row) in enumerate(tab_plot.iterrows()):
    ax.text(row['Exp. Media'] + 0.01, i, f"{row['Pop. (milhoes)']:.1f}M",
            va='center', fontsize=9, color='gray')
ax.set_xlabel('Exposicao Media (com IC 95%)')
ax.set_title(f'Exposicao por Setor (ANOVA: F={f_stat:.0f}, p<0.001)')
ax.axvline(weighted_mean(df_score['exposure_score'], df_score['peso']),
           color='gray', linestyle='--', linewidth=1, alpha=0.5)
plt.tight_layout()
plt.show()

# ======================================================================
# 6.2 - Exposicao por grupo ocupacional com ICs e ANOVA
# ======================================================================
print("\n" + "=" * 70)
print("EXPOSICAO POR GRANDE GRUPO OCUPACIONAL")
print("=" * 70)

df_gg = df_score[df_score['grande_grupo'].notna()]
rows_grupo = []
for grupo in sorted(df_gg['grande_grupo'].unique()):
    sub = df_gg[df_gg['grande_grupo'] == grupo]
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    rows_grupo.append({
        'Grande Grupo': grupo,
        'Exp. Media': mean_e, 'IC Inf': ci_lo, 'IC Sup': ci_hi,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })

tab_grupo = pd.DataFrame(rows_grupo).sort_values('Exp. Media', ascending=False).set_index('Grande Grupo')
display(tab_grupo.round(3))

model_anova_grupo = smf.wls(
    'exposure_score ~ C(grande_grupo)',
    data=df_gg, weights=df_gg['peso']
).fit()
print(f"\nANOVA ponderada (grupos): F={model_anova_grupo.fvalue:.1f}, "
      f"p={model_anova_grupo.f_pvalue:.2e} {sig_stars(model_anova_grupo.f_pvalue)}")
print(f"R²: {model_anova_grupo.rsquared:.4f}")

# ======================================================================
# 6.3 - Educacao DENTRO de grupos ocupacionais
# ======================================================================
print("\n" + "=" * 70)
print("EXPOSICAO MEDIA POR EDUCACAO DENTRO DE CADA GRUPO OCUPACIONAL")
print("=" * 70)

df_edu_gg = df_gg.copy()
# Usar niveis de instrucao simplificados para legibilidade
edu_map_simples = {
    '1': 'Sem/Fund.Inc.', '2': 'Sem/Fund.Inc.',
    '3': 'Fund.Comp.', '4': 'Med.Inc.',
    '5': 'Med.Comp.', '6': 'Sup.Inc.', '7': 'Sup.Comp.',
}
df_edu_gg['edu_simples'] = df_edu_gg['nivel_instrucao'].astype(str).map(edu_map_simples)

pivot_edu = df_edu_gg.groupby(['grande_grupo', 'edu_simples']).apply(
    lambda x: weighted_mean(x['exposure_score'], x['peso'])
).unstack(fill_value=np.nan)

# Reordenar colunas
edu_order = ['Sem/Fund.Inc.', 'Fund.Comp.', 'Med.Inc.', 'Med.Comp.', 'Sup.Inc.', 'Sup.Comp.']
cols_available = [c for c in edu_order if c in pivot_edu.columns]
pivot_edu = pivot_edu[cols_available]

display(pivot_edu.round(3))

print("\nInterpretacao: Dentro do mesmo grupo ocupacional, a exposicao")
print("tende a ser similar independente da escolaridade, pois o indice")
print("e atribuido por ocupacao (ISCO-08), nao por individuo.")

# Verificar matching dos setores criticos
setores_no_df = sorted(df_score['setor_agregado'].unique())
matched_setores = [s for s in SETORES_CRITICOS_IA if s in setores_no_df]
if len(matched_setores) < len(SETORES_CRITICOS_IA):
    unmatched = [s for s in SETORES_CRITICOS_IA if s not in setores_no_df]
    print(f"\n  \u26a0 Setores criticos sem match no df: {unmatched}")
    print(f"  Setores disponiveis no df: {setores_no_df}")
else:
    print(f"\n  Setores criticos IA: todos {len(matched_setores)} encontrados no dataframe.")

# ======================================================================
# 6.4 - Heatmap regiao x setor
# ======================================================================
pivot_rs = df_score.groupby(['regiao', 'setor_agregado']).apply(
    lambda x: weighted_mean(x['exposure_score'], x['peso'])
).unstack(fill_value=np.nan)

# Ordenar setores por media
setor_order = pivot_rs.mean().sort_values(ascending=False).index
pivot_rs = pivot_rs[setor_order]

fig, ax = plt.subplots(figsize=(16, 6))
sns.heatmap(pivot_rs, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax,
            linewidths=0.5, linecolor='white', cbar_kws={'label': 'Exposicao Media'})
ax.set_title('Exposicao Media: Regiao x Setor')
ax.set_ylabel('')
ax.set_xlabel('')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
```

    ======================================================================
    EXPOSICAO POR SETOR ECONOMICO
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | Exp. Media | IC Inf | IC Sup | % Alta Exp. | Pop. (milhoes) | Critico IA |
|----|----|----|----|----|----|----|
| Setor |  |  |  |  |  |  |
| Finanças e Seguros | 0.509 | 0.509 | 0.509 | 53.496 | 1.566 |  |
| Informação e Comunicação | 0.445 | 0.445 | 0.445 | 30.028 | 1.891 |  |
| Serviços Profissionais | 0.409 | 0.409 | 0.410 | 29.587 | 4.322 |  |
| Atividades Imobiliárias | 0.384 | 0.384 | 0.384 | 17.071 | 0.727 |  |
| Administração Pública | 0.352 | 0.352 | 0.352 | 26.280 | 4.274 |  |
| Outros Serviços | 0.331 | 0.331 | 0.331 | 7.279 | 19.114 |  |
| Artes e Cultura | 0.317 | 0.316 | 0.317 | 9.281 | 1.153 |  |
| Saúde | 0.300 | 0.300 | 0.300 | 13.714 | 6.196 |  |
| Utilidades | 0.293 | 0.293 | 0.294 | 15.105 | 0.727 |  |
| Serviços Administrativos | 0.292 | 0.292 | 0.292 | 18.234 | 4.558 |  |
| Educação | 0.290 | 0.290 | 0.290 | 9.013 | 7.186 |  |
| Transporte | 0.280 | 0.280 | 0.280 | 7.951 | 5.741 |  |
| Alojamento e Alimentação | 0.266 | 0.266 | 0.266 | 4.414 | 5.109 |  |
| Comércio | 0.256 | 0.256 | 0.256 | 7.156 | 3.158 |  |
| Ind. Transformação | 0.210 | 0.210 | 0.210 | 4.374 | 18.697 |  |
| Serviços Domésticos | 0.160 | 0.160 | 0.160 | 0.000 | 5.302 |  |
| Construção | 0.146 | 0.146 | 0.147 | 2.494 | 7.244 |  |

</div>


    ANOVA ponderada (setores): F=5031.9, p=0.00e+00 ***
    R²: 0.2808 (variacao explicada pelos setores)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-10-output-4.png)


    ======================================================================
    EXPOSICAO POR GRANDE GRUPO OCUPACIONAL
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|                            | Exp. Media | IC Inf | IC Sup | Pop. (milhoes) |
|----------------------------|------------|--------|--------|----------------|
| Grande Grupo               |            |        |        |                |
| Apoio administrativo       | 0.554      | 0.554  | 0.554  | 8.197          |
| Dirigentes e gerentes      | 0.400      | 0.400  | 0.400  | 3.543          |
| Profissionais das ciências | 0.353      | 0.353  | 0.354  | 13.239         |
| Técnicos nível médio       | 0.345      | 0.345  | 0.345  | 8.990          |
| Serviços e vendedores      | 0.305      | 0.305  | 0.305  | 21.275         |
| Operadores de máquinas     | 0.223      | 0.223  | 0.223  | 9.427          |
| Agropecuária qualificada   | 0.174      | 0.174  | 0.174  | 4.442          |
| Indústria qualificada      | 0.151      | 0.151  | 0.151  | 12.711         |
| Ocupações elementares      | 0.130      | 0.130  | 0.130  | 15.144         |

</div>


    ANOVA ponderada (grupos): F=53767.9, p=0.00e+00 ***
    R²: 0.6759

    ======================================================================
    EXPOSICAO MEDIA POR EDUCACAO DENTRO DE CADA GRUPO OCUPACIONAL
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

| edu_simples | Sem/Fund.Inc. | Fund.Comp. | Med.Inc. | Med.Comp. | Sup.Inc. | Sup.Comp. |
|----|----|----|----|----|----|----|
| grande_grupo |  |  |  |  |  |  |
| Agropecuária qualificada | 0.174 | 0.174 | 0.173 | 0.175 | 0.176 | 0.176 |
| Apoio administrativo | 0.497 | 0.494 | 0.505 | 0.542 | 0.569 | 0.582 |
| Dirigentes e gerentes | 0.373 | 0.388 | 0.385 | 0.401 | 0.404 | 0.401 |
| Indústria qualificada | 0.131 | 0.143 | 0.147 | 0.159 | 0.175 | 0.181 |
| Ocupações elementares | 0.125 | 0.128 | 0.128 | 0.136 | 0.144 | 0.137 |
| Operadores de máquinas | 0.209 | 0.219 | 0.219 | 0.226 | 0.240 | 0.238 |
| Profissionais das ciências | 0.316 | 0.343 | 0.379 | 0.371 | 0.368 | 0.352 |
| Serviços e vendedores | 0.293 | 0.292 | 0.293 | 0.306 | 0.312 | 0.321 |
| Técnicos nível médio | 0.354 | 0.359 | 0.368 | 0.321 | 0.354 | 0.366 |

</div>


    Interpretacao: Dentro do mesmo grupo ocupacional, a exposicao
    tende a ser similar independente da escolaridade, pois o indice
    e atribuido por ocupacao (ISCO-08), nao por individuo.

      ⚠ Setores criticos sem match no df: ['Informacao e Comunicacao', 'Financas e Seguros', 'Servicos Profissionais']
      Setores disponiveis no df: ['Administração Pública', 'Alojamento e Alimentação', 'Artes e Cultura', 'Atividades Imobiliárias', 'Comércio', 'Construção', 'Educação', 'Finanças e Seguros', 'Ind. Transformação', 'Informação e Comunicação', 'Outros Serviços', 'Saúde', 'Serviços Administrativos', 'Serviços Domésticos', 'Serviços Profissionais', 'Transporte', 'Utilidades']

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-10-output-10.png)

### 6b. Fluxo: Escolaridade -\> Ocupacao -\> Gradiente de Exposicao

Diagrama de fluxo mostrando o sorting educacao -\> ocupacao -\>
exposicao.

``` python
# Etapa 1b.6b - Sankey: Escolaridade -> Grupo Ocupacional -> Gradiente

# ======================================================================
# 6b - Sankey: Escolaridade -> Grupo Ocupacional -> Gradiente
# ======================================================================

# Garantir edu_simples em df_score
if 'edu_simples' not in df_score.columns:
    edu_map_simples = {'1': 'Sem/Fund.Inc.', '2': 'Sem/Fund.Inc.', '3': 'Fund.Comp.', '4': 'Med.Inc.', '5': 'Med.Comp.', '6': 'Sup.Inc.', '7': 'Sup.Comp.'}
    col_edu = 'nivel_instrucao' if 'nivel_instrucao' in df_score.columns else 'vd3004'
    df_score['edu_simples'] = df_score[col_edu].astype(str).map(edu_map_simples).fillna('Outros')

# Agregar fluxos
flows = df_score.groupby(['edu_simples', 'grande_grupo', 'exposure_gradient'])['peso'].sum().reset_index()
flows = flows[flows['peso'] > 500000]  # filtrar fluxos pequenos

# Usar plotly para Sankey
try:
    import plotly.graph_objects as go

    # Construir nos e links
    edu_cats = sorted(flows['edu_simples'].unique())
    gg_cats = sorted(flows['grande_grupo'].unique())
    grad_cats = [g for g in GRADIENT_ORDER if g in flows['exposure_gradient'].unique()]
    all_nodes = list(edu_cats) + list(gg_cats) + list(grad_cats)

    sources, targets, values = [], [], []
    # Edu -> GG
    for _, row in flows.groupby(['edu_simples', 'grande_grupo'])['peso'].sum().reset_index().iterrows():
        sources.append(all_nodes.index(row['edu_simples']))
        targets.append(all_nodes.index(row['grande_grupo']))
        values.append(row['peso'] / 1e6)
    # GG -> Gradiente
    for _, row in flows.groupby(['grande_grupo', 'exposure_gradient'])['peso'].sum().reset_index().iterrows():
        sources.append(all_nodes.index(row['grande_grupo']))
        targets.append(all_nodes.index(row['exposure_gradient']))
        values.append(row['peso'] / 1e6)

    fig = go.Figure(go.Sankey(
        node=dict(label=all_nodes, pad=15, thickness=20),
        link=dict(source=sources, target=targets, value=values)))
    fig.update_layout(title='Fluxo: Escolaridade -> Ocupacao -> Gradiente de Exposicao',
                      font_size=10, width=1200, height=700)
    fig.show()
except ImportError:
    print("plotly nao instalado. Instalar com: %pip install plotly")
```

    plotly nao instalado. Instalar com: %pip install plotly

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

> **Conexão com WP140 (dimensão geográfica):** O WP140 analisa variação
> entre países (Figura 6, p. 22-23) e encontra que países de maior renda
> per capita têm maior exposição, refletindo sua estrutura produtiva
> mais intensiva em serviços. Replicamos esse padrão DENTRO do Brasil:
> regiões de maior PIB per capita (Sudeste, Sul, Centro-Oeste)
> apresentam maior exposição. O DF (0.326) supera inclusive a média de
> high-income countries (~0.36 no WP140), refletindo a concentração de
> serviços públicos e profissionais qualificados.

``` python
# Etapa 1b.7 - Analise de Dados - Regiao

# ======================================================================
# 7.1 - Exposicao por regiao com ICs e ANOVA
# ======================================================================
print("=" * 70)
print("EXPOSICAO POR REGIAO")
print("=" * 70)

rows_regiao = []
for regiao in ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']:
    sub = df_score[df_score['regiao'] == regiao]
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
    n_nao = sub[sub['exposure_gradient'] == 'Not Exposed']['peso'].sum()
    rows_regiao.append({
        'Regiao': regiao,
        'Exp. Media': mean_e, 'IC Inf': ci_lo, 'IC Sup': ci_hi,
        '% Alta Exp.': n_alta / sub['peso'].sum() * 100,
        '% Nao Exposto': n_nao / sub['peso'].sum() * 100,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })
    print(f"  {regiao}: {mean_e:.3f} [IC: {ci_lo:.3f}-{ci_hi:.3f}] | "
          f"Alta: {n_alta/sub['peso'].sum()*100:.1f}% | Pop: {sub['peso'].sum()/1e6:.1f}M")

tab_regiao = pd.DataFrame(rows_regiao).set_index('Regiao')
display(tab_regiao.round(3))

# ANOVA
model_anova_reg = smf.wls(
    'exposure_score ~ C(regiao)',
    data=df_score, weights=df_score['peso']
).fit()
print(f"\nANOVA ponderada (regioes): F={model_anova_reg.fvalue:.1f}, "
      f"p={model_anova_reg.f_pvalue:.2e} {sig_stars(model_anova_reg.f_pvalue)}")
print(f"R²: {model_anova_reg.rsquared:.4f} (pouca variacao explicada apenas por regiao)")

# Grafico regioes
fig, ax = plt.subplots(figsize=(10, 5))
tab_r = tab_regiao.reset_index().sort_values('Exp. Media')
yerr_r = [tab_r['Exp. Media'] - tab_r['IC Inf'], tab_r['IC Sup'] - tab_r['Exp. Media']]
ax.barh(tab_r['Regiao'], tab_r['Exp. Media'], xerr=yerr_r, color='steelblue',
        edgecolor='white', capsize=4)
for i, (_, row) in enumerate(tab_r.iterrows()):
    ax.text(row['Exp. Media'] + 0.003, i, f"{row['Pop. (milhoes)']:.1f}M",
            va='center', fontsize=10, color='gray')
ax.set_xlabel('Exposicao Media (com IC 95%)')
ax.set_title(f'Exposicao por Regiao (ANOVA: F={model_anova_reg.fvalue:.0f}, p={model_anova_reg.f_pvalue:.2e})')
plt.tight_layout()
plt.show()

# ======================================================================
# 7.2 - Ranking estadual (UF)
# ======================================================================
print("\n" + "=" * 70)
print("RANKING ESTADUAL DE EXPOSICAO")
print("=" * 70)

rows_uf = []
for uf in sorted(df_score['sigla_uf'].unique()):
    sub = df_score[df_score['sigla_uf'] == uf]
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    rows_uf.append({
        'UF': uf,
        'Regiao': REGIAO_MAP.get(uf, ''),
        'Exp. Media': mean_e, 'IC Inf': ci_lo, 'IC Sup': ci_hi,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })

tab_uf = pd.DataFrame(rows_uf).sort_values('Exp. Media', ascending=False).set_index('UF')
display(tab_uf.round(3))

print("\nTop 5 UFs (maior exposicao):")
for uf in tab_uf.head(5).index:
    row = tab_uf.loc[uf]
    print(f"  {uf} ({row['Regiao']}): {row['Exp. Media']:.3f}")

print("\nBottom 5 UFs (menor exposicao):")
for uf in tab_uf.tail(5).index:
    row = tab_uf.loc[uf]
    print(f"  {uf} ({row['Regiao']}): {row['Exp. Media']:.3f}")

print("\nNota: Mapas coropletas detalhados foram gerados pelo script 09")
print("(etapa1_ia_generativa/outputs/figures/mapa_c*.png)")
```

    ======================================================================
    EXPOSICAO POR REGIAO
    ======================================================================
      Norte: 0.258 [IC: 0.258-0.258] | Alta: 8.4% | Pop: 7.7M
      Nordeste: 0.261 [IC: 0.261-0.261] | Alta: 8.0% | Pop: 22.2M
      Centro-Oeste: 0.282 [IC: 0.282-0.282] | Alta: 10.7% | Pop: 8.4M
      Sudeste: 0.289 [IC: 0.289-0.289] | Alta: 11.2% | Pop: 43.1M
      Sul: 0.282 [IC: 0.282-0.282] | Alta: 10.5% | Pop: 15.7M

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|              | Exp. Media | IC Inf | IC Sup | % Alta Exp. | % Nao Exposto | Pop. (milhoes) |
|--------------|------------|--------|--------|-------------|---------------|----------------|
| Regiao       |            |        |        |             |               |                |
| Norte        | 0.258      | 0.258  | 0.258  | 8.376       | 59.352        | 7.722          |
| Nordeste     | 0.261      | 0.261  | 0.261  | 8.020       | 58.641        | 22.152         |
| Centro-Oeste | 0.282      | 0.282  | 0.282  | 10.712      | 53.201        | 8.353          |
| Sudeste      | 0.289      | 0.289  | 0.289  | 11.171      | 50.751        | 43.088         |
| Sul          | 0.282      | 0.282  | 0.282  | 10.502      | 53.312        | 15.652         |

</div>


    ANOVA ponderada (regioes): F=373.9, p=1.89e-321 ***
    R²: 0.0072 (pouca variacao explicada apenas por regiao)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-12-output-4.png)


    ======================================================================
    RANKING ESTADUAL DE EXPOSICAO
    ======================================================================

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | Regiao       | Exp. Media | IC Inf | IC Sup | Pop. (milhoes) |
|-----|--------------|------------|--------|--------|----------------|
| UF  |              |            |        |        |                |
| DF  | Centro-Oeste | 0.326      | 0.326  | 0.326  | 1.434          |
| RJ  | Sudeste      | 0.301      | 0.300  | 0.301  | 7.663          |
| SP  | Sudeste      | 0.297      | 0.297  | 0.297  | 23.175         |
| SC  | Sul          | 0.283      | 0.283  | 0.283  | 4.278          |
| RR  | Norte        | 0.282      | 0.282  | 0.283  | 0.270          |
| PR  | Sul          | 0.282      | 0.282  | 0.282  | 5.925          |
| RS  | Sul          | 0.281      | 0.281  | 0.281  | 5.449          |
| GO  | Centro-Oeste | 0.275      | 0.275  | 0.276  | 3.659          |
| AP  | Norte        | 0.275      | 0.274  | 0.275  | 0.325          |
| RN  | Nordeste     | 0.271      | 0.271  | 0.271  | 1.344          |
| MT  | Centro-Oeste | 0.270      | 0.269  | 0.270  | 1.898          |
| ES  | Sudeste      | 0.269      | 0.269  | 0.269  | 1.935          |
| AC  | Norte        | 0.269      | 0.268  | 0.269  | 0.315          |
| SE  | Nordeste     | 0.268      | 0.268  | 0.269  | 0.874          |
| MS  | Centro-Oeste | 0.268      | 0.268  | 0.269  | 1.362          |
| TO  | Norte        | 0.268      | 0.268  | 0.268  | 0.755          |
| AM  | Norte        | 0.268      | 0.268  | 0.268  | 1.761          |
| PE  | Nordeste     | 0.267      | 0.267  | 0.267  | 3.565          |
| CE  | Nordeste     | 0.267      | 0.267  | 0.267  | 3.555          |
| MG  | Sudeste      | 0.267      | 0.267  | 0.267  | 10.315         |
| PB  | Nordeste     | 0.262      | 0.262  | 0.262  | 1.614          |
| AL  | Nordeste     | 0.258      | 0.258  | 0.258  | 1.169          |
| RO  | Norte        | 0.256      | 0.256  | 0.257  | 0.733          |
| MA  | Nordeste     | 0.255      | 0.255  | 0.256  | 2.586          |
| BA  | Nordeste     | 0.254      | 0.254  | 0.254  | 6.141          |
| PI  | Nordeste     | 0.253      | 0.253  | 0.254  | 1.306          |
| PA  | Norte        | 0.248      | 0.248  | 0.248  | 3.562          |

</div>


    Top 5 UFs (maior exposicao):
      DF (Centro-Oeste): 0.326
      RJ (Sudeste): 0.301
      SP (Sudeste): 0.297
      SC (Sul): 0.283
      RR (Norte): 0.282

    Bottom 5 UFs (menor exposicao):
      RO (Norte): 0.256
      MA (Nordeste): 0.255
      BA (Nordeste): 0.254
      PI (Nordeste): 0.253
      PA (Norte): 0.248

    Nota: Mapas coropletas detalhados foram gerados pelo script 09
    (etapa1_ia_generativa/outputs/figures/mapa_c*.png)

### 7. Regiao

Exposicao media por regiao; populacao em alta exposicao por UF/regiao.

**Analises:** - Exposicao por regiao/UF com ICs e ANOVA ponderada -
Referencia aos mapas coropletas (script 09) - Ranking estadual

### 7c. Decomposicao Shift-Share Regional

Decomposicao da diferenca de exposicao entre regioes em efeito
composicao (diferenca na estrutura setorial) e residual (diferenca
dentro dos setores).

``` python
# Etapa 1b.7c - Decomposicao Shift-Share Regional

# ======================================================================
# 7c - Decomposicao Shift-Share: Regioes
# ======================================================================
print("=" * 70)
print("DECOMPOSICAO SHIFT-SHARE REGIONAL")
print("=" * 70)

def shift_share(df, regiao_a, regiao_b, var_grupo='setor_agregado'):
    """Decompoe diferenca de exposicao entre duas regioes."""
    da = df[df['regiao'] == regiao_a]
    db = df[df['regiao'] == regiao_b]
    total_a, total_b = da['peso'].sum(), db['peso'].sum()

    grupos = set(da[var_grupo].unique()) | set(db[var_grupo].unique())
    composicao = 0
    for g in grupos:
        sa = da[da[var_grupo]==g]
        sb = db[db[var_grupo]==g]
        share_a = sa['peso'].sum() / total_a if total_a > 0 else 0
        share_b = sb['peso'].sum() / total_b if total_b > 0 else 0
        exp_g = weighted_mean(df[df[var_grupo]==g]['exposure_score'],
                              df[df[var_grupo]==g]['peso'])
        composicao += (share_a - share_b) * exp_g

    exp_a = weighted_mean(da['exposure_score'], da['peso'])
    exp_b = weighted_mean(db['exposure_score'], db['peso'])
    total_diff = exp_a - exp_b
    residual = total_diff - composicao

    return total_diff, composicao, residual

for par in [('Sudeste', 'Nordeste'), ('Sudeste', 'Norte'), ('Sul', 'Nordeste')]:
    diff, comp, resid = shift_share(df_score, par[0], par[1])
    print(f"\n{par[0]} vs {par[1]}:")
    print(f"  Diferenca total: {diff:+.4f}")
    if diff != 0:
        print(f"  Efeito composicao (setor): {comp:+.4f} ({comp/diff*100:.1f}%)")
        print(f"  Residual: {resid:+.4f} ({resid/diff*100:.1f}%)")
    else:
        print(f"  Efeito composicao (setor): {comp:+.4f}")
        print(f"  Residual: {resid:+.4f}")
```

    ======================================================================
    DECOMPOSICAO SHIFT-SHARE REGIONAL
    ======================================================================

    Sudeste vs Nordeste:
      Diferenca total: +0.0283
      Efeito composicao (setor): +0.0111 (39.4%)
      Residual: +0.0171 (60.6%)

    Sudeste vs Norte:
      Diferenca total: +0.0306
      Efeito composicao (setor): +0.0121 (39.5%)
      Residual: +0.0185 (60.5%)

    Sul vs Nordeste:
      Diferenca total: +0.0214
      Efeito composicao (setor): +0.0031 (14.4%)
      Residual: +0.0183 (85.6%)

### 7b. Região (Mapas)

Mapas coropléticos do Brasil por estado (UF) com base nos dados da PNADc
e no índice de exposição à IA generativa (ILO WP140).

**Mapas:** 1. **Exposição média por estado** — score médio de exposição
à IA por UF. 2. **População não exposta** — gradiente “Not Exposed” e
volume estimado (milhões) por estado. 3. **População em maior
exposição** — gradiente 4 (Exposed: Gradient 4) e volume estimado
(milhões) por estado.

Fonte: PNAD Contínua 3º trimestre/2025 + ILO GenAI Scores (Gmyrek et
al., 2025).

``` python
# Etapa 1b.7b - Analise de Dados - Regiao (Mapas)
# Instalar dependencias para mapas (executar apenas uma vez)
%pip install geobr geopandas --quiet

import geobr
import geopandas as gpd
from matplotlib.colors import Normalize
import matplotlib.patheffects as pe

# ======================================================================
# 7b.1 - Dados geograficos e agregacao por estado
# ======================================================================
# Carregar malha de estados (Brasil)
states_gdf = geobr.read_state(year=2020)
states_gdf['abbrev_state'] = states_gdf['abbrev_state'].str.upper()

# Agregar por sigla_uf (usar df_score ja carregado no notebook)
rows_estado = []
for uf in df_score['sigla_uf'].unique():
    sub = df_score[df_score['sigla_uf'] == uf]
    total = sub['peso'].sum()
    exp_media = weighted_mean(sub['exposure_score'], sub['peso'])
    peso_not = sub[sub['exposure_gradient'] == 'Not Exposed']['peso'].sum()
    peso_g4 = sub[sub['exposure_gradient'] == 'Exposed: Gradient 4']['peso'].sum()
    rows_estado.append({
        'sigla_uf': uf,
        'exposicao_media': exp_media,
        'pct_not_exposed': (peso_not / total * 100) if total > 0 else 0,
        'vol_not_exposed_mil': peso_not / 1e6,
        'pct_grad4': (peso_g4 / total * 100) if total > 0 else 0,
        'vol_grad4_mil': peso_g4 / 1e6,
    })
agg_estado = pd.DataFrame(rows_estado)
gdf = states_gdf.merge(agg_estado, left_on='abbrev_state', right_on='sigla_uf')

# Funcao auxiliar para desenhar um mapa (exibicao no notebook)
def _plot_map(gdf, metric, title, cmap, label_col, fmt='.1f', pct=True, extra_label=None):
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    ax.set_axis_off()
    vmin, vmax = gdf[metric].min(), gdf[metric].max()
    gdf.plot(column=metric, cmap=cmap, linewidth=0.8, ax=ax,
             edgecolor='0.3', legend=False, vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
    cbar.set_label('% Força de Trabalho' if pct else 'Score', fontsize=12)
    for _, row in gdf.iterrows():
        c = row.geometry.centroid
        v = row[metric]
        vs = f"{v:{fmt}}%" if pct else f"{v:{fmt}}"
        txt = f"{row[label_col]}\n{vs}"
        if extra_label is not None and extra_label in row:
            txt += f"\n({row[extra_label]:.1f}M)"
        nv = (v - vmin) / (vmax - vmin) if vmax > vmin else 0.5
        tc = 'white' if nv > 0.6 else 'black'
        ax.annotate(txt, xy=(c.x, c.y), ha='center', va='center',
                    fontsize=9, fontweight='bold', color=tc,
                    path_effects=[pe.withStroke(linewidth=2, foreground='white' if tc == 'black' else 'black')])
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    fig.text(0.5, 0.02, 'Fonte: PNAD 3T/2025 + ILO GenAI Scores', ha='center', fontsize=10, style='italic')
    plt.tight_layout()
    plt.show()

# ======================================================================
# 7b.2 - Mapa 1: Exposicao media por estado
# ======================================================================
_plot_map(gdf, 'exposicao_media',
          'Exposição Média à IA por Estado – Brasil 3T/2025',
          'YlOrRd', 'abbrev_state', '.3f', pct=False)

# ======================================================================
# 7b.3 - Mapa 2: Gradiente "Nao exposto" e volume por estado
# ======================================================================
_plot_map(gdf, 'pct_not_exposed',
          'População Não Exposta à IA por Estado (%) e Volume (milhões) – Brasil 3T/2025',
          'Greens', 'abbrev_state', '.1f', pct=True, extra_label='vol_not_exposed_mil')

# ======================================================================
# 7b.4 - Mapa 3: Gradiente 4 (maior exposicao) e volume por estado
# ======================================================================
_plot_map(gdf, 'pct_grad4',
          'População em Maior Exposição (Gradiente 4) por Estado (%) e Volume (milhões) – Brasil 3T/2025',
          'Reds', 'abbrev_state', '.1f', pct=True, extra_label='vol_grad4_mil')
```


    [notice] A new release of pip is available: 24.2 -> 26.0.1
    [notice] To update, run: python3.10 -m pip install --upgrade pip
    Note: you may need to restart the kernel to use updated packages.

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-14-output-2.png)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-14-output-3.png)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-14-output-4.png)

### 7d. Indice de Vulnerabilidade Composta

Trabalhadores em situacao de vulnerabilidade composta: alta exposicao +
baixa escolaridade + informalidade + baixa renda.

> Este indicador sintetico identifica o grupo mais vulneravel aos
> impactos da IA generativa, combinando multiplas dimensoes de
> desvantagem.

``` python
# Etapa 1b.7d - Indice de Vulnerabilidade Composta

# ======================================================================
# 7d - Indice de Vulnerabilidade Composta
# ======================================================================
print("=" * 70)
print("INDICE DE VULNERABILIDADE COMPOSTA A IA")
print("=" * 70)

mediana_renda_vuln = weighted_quantile(df_renda['rendimento_habitual'], df_renda['peso'], 0.5)

df_score['vulneravel'] = (
    df_score['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS) &
    df_score['edu_simples'].isin(['Sem/Fund.Inc.', 'Fund.Comp.']) &
    (df_score['formal'] == 0)
).astype(int)

# Se renda disponivel, adicionar criterio
mask_renda = df_score['tem_renda'] == 1
df_score.loc[mask_renda, 'vulneravel'] = (
    df_score.loc[mask_renda, 'vulneravel'] &
    (df_score.loc[mask_renda, 'rendimento_habitual'] < mediana_renda_vuln)
).astype(int)

pop_vuln = df_score[df_score['vulneravel']==1]['peso'].sum() / 1e6
pct_vuln = pop_vuln / (df_score['peso'].sum()/1e6) * 100

print(f"\nTrabalhadores em vulnerabilidade composta: {pop_vuln:.2f}M ({pct_vuln:.1f}%)")
print("(Alta exposicao + Baixa escolaridade + Informalidade + Baixa renda)")

# Tabela por UF
vuln_uf = df_score.groupby('sigla_uf').apply(lambda g: pd.Series({
    'pct_vulneravel': g[g['vulneravel']==1]['peso'].sum() / g['peso'].sum() * 100 if g['peso'].sum() > 0 else 0,
    'vol_vulneravel': g[g['vulneravel']==1]['peso'].sum() / 1e6,
})).reset_index()

vuln_uf = vuln_uf.sort_values('pct_vulneravel', ascending=False)
print("\nTop 10 UFs por % de vulnerabilidade composta:")
for _, row in vuln_uf.head(10).iterrows():
    print(f"  {row['sigla_uf']}: {row['pct_vulneravel']:.1f}% ({row['vol_vulneravel']:.2f}M)")

# Mapa (se gdf disponivel da secao 7b)
try:
    gdf_vuln = gdf.merge(vuln_uf, left_on='abbrev_state', right_on='sigla_uf')
    _plot_map(gdf_vuln, 'pct_vulneravel',
              'Vulnerabilidade Composta a IA por Estado\n(Alta exposicao + Baixa escolaridade + Informal + Baixa renda)',
              'Reds', 'abbrev_state', fmt='.1f', pct=True, extra_label='vol_vulneravel')
except NameError:
    print("\n  (Mapa nao disponivel - executar secao 7b primeiro)")
```

    ======================================================================
    INDICE DE VULNERABILIDADE COMPOSTA A IA
    ======================================================================

    Trabalhadores em vulnerabilidade composta: 0.06M (0.1%)
    (Alta exposicao + Baixa escolaridade + Informalidade + Baixa renda)

    Top 10 UFs por % de vulnerabilidade composta:
      PB: 0.2% (0.00M)
      BA: 0.2% (0.01M)
      PI: 0.2% (0.00M)
      AM: 0.1% (0.00M)
      CE: 0.1% (0.00M)
      PE: 0.1% (0.00M)
      SE: 0.1% (0.00M)
      MS: 0.1% (0.00M)
      RO: 0.1% (0.00M)
      MA: 0.1% (0.00M)

![](etapa_1b_analise_dados_ilo_pnadc_files/figure-commonmark/cell-15-output-2.png)

### 8. Analise multivariada

Regressoes WLS, equacao de Mincer aumentada e testes de robustez.

**Analises:** - WLS: Determinantes da exposicao (3 especificacoes com
controles progressivos) - WLS Mincer: log(renda) ~ exposicao + controles
(com interacoes) - Robustez: sensibilidade ao crosswalk (excluir matches
3-digit)

> **Nota metodologica:** Todas as regressoes usam WLS (Weighted Least
> Squares) com pesos amostrais V1028 e erros-padrao robustos a
> heterocedasticidade (HC1). Ref: Wooldridge (2020), Cap. 8.

> **Extensão do WP140:** O WP140 trabalha exclusivamente com dados
> agregados por ocupação e não realiza análise no nível individual. A
> equação de Mincer aumentada com o score de exposição como regressor é
> uma extensão metodológica que permite: (1) controlar por
> características individuais (sexo, raça, idade, escolaridade); (2)
> estimar o “prêmio” de exposição na renda condicionando na composição
> da força de trabalho; (3) testar interações (exposição×formalidade,
> exposição×gênero). Essa abordagem segue a sugestão implícita do WP140
> de que pesquisas futuras devem “explore the relationship between
> exposure and labour market outcomes at the individual level” (p. 39).

``` python
# Etapa 1b.8 - Analise de Dados - Analise multivariada

# ======================================================================
# 8.1 - WLS: Determinantes da exposicao (3 especificacoes)
# ======================================================================
print("=" * 70)
print("REGRESSAO WLS: DETERMINANTES DA EXPOSICAO A IA")
print("=" * 70)

df_reg = df_score[['exposure_score', 'sexo_texto', 'raca_agregada', 'idade',
                     'nivel_instrucao', 'grande_grupo', 'regiao', 'formal',
                     'setor_agregado', 'peso']].dropna().copy()

print(f"Amostra para regressao: {len(df_reg):,} observacoes")

# Modelo 1: apenas demografia
m1 = smf.wls(
    'exposure_score ~ C(sexo_texto, Treatment("Homem")) + C(raca_agregada, Treatment("Negra")) + '
    'idade + I(idade**2) + C(nivel_instrucao)',
    data=df_reg, weights=df_reg['peso']
).fit(cov_type='HC1')

# Modelo 2: + ocupacao e regiao
m2 = smf.wls(
    'exposure_score ~ C(sexo_texto, Treatment("Homem")) + C(raca_agregada, Treatment("Negra")) + '
    'idade + I(idade**2) + C(nivel_instrucao) + C(grande_grupo) + C(regiao)',
    data=df_reg, weights=df_reg['peso']
).fit(cov_type='HC1')

# Modelo 3: + setor e formalidade
m3 = smf.wls(
    'exposure_score ~ C(sexo_texto, Treatment("Homem")) + C(raca_agregada, Treatment("Negra")) + '
    'idade + I(idade**2) + C(nivel_instrucao) + C(grande_grupo) + C(regiao) + '
    'C(setor_agregado) + formal',
    data=df_reg, weights=df_reg['peso']
).fit(cov_type='HC1')

# Tabela comparativa dos 3 modelos
def extract_key_params(model, label):
    """Extrai coeficientes-chave de um modelo."""
    params = {}
    for var in model.params.index:
        coef = model.params[var]
        se = model.bse[var]
        pval = model.pvalues[var]
        params[var] = f"{coef:+.4f} ({se:.4f}){sig_stars(pval)}"
    return params

# Variaveis-chave para reportar
key_vars = [
    ('C(sexo_texto, Treatment("Homem"))[T.Mulher]', 'Mulher (ref: Homem)'),
    ('C(raca_agregada, Treatment("Negra"))[T.Branca]', 'Branca (ref: Negra)'),
    ('idade', 'Idade'),
    ('formal', 'Formal'),
]

print("\n{:<30} {:<25} {:<25} {:<25}".format('Variavel', 'M1 (Demog.)', 'M2 (+Ocup.)', 'M3 (Completo)'))
print("-" * 105)

for var_name, var_label in key_vars:
    vals = []
    for m in [m1, m2, m3]:
        if var_name in m.params.index:
            coef = m.params[var_name]
            pval = m.pvalues[var_name]
            vals.append(f"{coef:+.4f}{sig_stars(pval)}")
        else:
            vals.append("--")
    print(f"{var_label:<30} {vals[0]:<25} {vals[1]:<25} {vals[2]:<25}")

print("-" * 105)
print(f"{'R²':<30} {m1.rsquared:.4f}{'':<20} {m2.rsquared:.4f}{'':<20} {m3.rsquared:.4f}")
print(f"{'N':<30} {int(m1.nobs):,}{'':<20} {int(m2.nobs):,}{'':<20} {int(m3.nobs):,}")
print(f"\nSignificancia: * p<0.05, ** p<0.01, *** p<0.001")

print("\n--- Modelo completo (M3) - Resumo ---")
print(m3.summary().tables[1])

# ======================================================================
# 8.2 - Equacao de Mincer com exposicao
# ======================================================================
print("\n" + "=" * 70)
print("EQUACAO DE MINCER AUMENTADA: log(renda) ~ exposicao + controles")
print("=" * 70)

df_mincer = df_renda[['rendimento_habitual', 'exposure_score', 'sexo_texto',
                        'raca_agregada', 'idade', 'nivel_instrucao', 'formal',
                        'regiao', 'setor_agregado', 'peso']].dropna().copy()
df_mincer['log_renda'] = np.log(df_mincer['rendimento_habitual'].clip(lower=1))

print(f"Amostra Mincer: {len(df_mincer):,} observacoes")

# Mincer 1: exposicao + capital humano basico
mincer1 = smf.wls(
    'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
    'idade + I(idade**2) + C(nivel_instrucao) + formal',
    data=df_mincer, weights=df_mincer['peso']
).fit(cov_type='HC1')

# Mincer 2: + controles regionais e setoriais
mincer2 = smf.wls(
    'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
    'idade + I(idade**2) + C(nivel_instrucao) + formal + C(regiao) + C(setor_agregado)',
    data=df_mincer, weights=df_mincer['peso']
).fit(cov_type='HC1')

# Mincer 3: + exposicao quadratica + interacoes
mincer3 = smf.wls(
    'log_renda ~ exposure_score + I(exposure_score**2) + '
    'exposure_score:C(sexo_texto) + exposure_score:formal + '
    'C(sexo_texto) + C(raca_agregada) + '
    'idade + I(idade**2) + C(nivel_instrucao) + formal + C(regiao) + C(setor_agregado)',
    data=df_mincer, weights=df_mincer['peso']
).fit(cov_type='HC1')

print("\n{:<40} {:<20} {:<20} {:<20}".format('Variavel', 'Mincer 1', 'Mincer 2', 'Mincer 3'))
print("-" * 100)

mincer_vars = [
    ('exposure_score', 'Exposicao'),
    ('I(exposure_score ** 2)', 'Exposicao²'),
    ('exposure_score:C(sexo_texto)[T.Mulher]', 'Exposicao x Mulher'),
    ('exposure_score:formal', 'Exposicao x Formal'),
    ('C(sexo_texto)[T.Mulher]', 'Mulher'),
    ('formal', 'Formal'),
]

for var_name, var_label in mincer_vars:
    vals = []
    for m in [mincer1, mincer2, mincer3]:
        if var_name in m.params.index:
            coef = m.params[var_name]
            pval = m.pvalues[var_name]
            vals.append(f"{coef:+.4f}{sig_stars(pval)}")
        else:
            vals.append("--")
    print(f"{var_label:<40} {vals[0]:<20} {vals[1]:<20} {vals[2]:<20}")

print("-" * 100)
print(f"{'R²':<40} {mincer1.rsquared:.4f}{'':<15} {mincer2.rsquared:.4f}{'':<15} {mincer3.rsquared:.4f}")
print(f"{'N':<40} {int(mincer1.nobs):,}{'':<15} {int(mincer2.nobs):,}{'':<15} {int(mincer3.nobs):,}")

# Interpretacao
coef_exp = mincer2.params['exposure_score']
pval_exp = mincer2.pvalues['exposure_score']
print(f"\nInterpretacao (Mincer 2):")
print(f"  Coeficiente de exposicao: {coef_exp:+.4f} {sig_stars(pval_exp)}")
if coef_exp > 0:
    pct_effect = (np.exp(coef_exp) - 1) * 100
    print(f"  Um aumento de 0.1 no score de exposicao esta associado a")
    print(f"  {pct_effect/10:.1f}% de aumento na renda, ceteris paribus.")
else:
    print(f"  Exposicao nao apresenta associacao significativa com renda")
    print(f"  apos controlar por ocupacao, setor e outras caracteristicas.")

print("\n  ATENCAO: Esta analise e cross-sectional e nao permite")
print("  inferencia causal. A correlacao entre exposicao e renda")
print("  reflete sorting ocupacional, nao efeito causal da IA.")

# ======================================================================
# 8.3 - Robustez: sensibilidade ao crosswalk
# ======================================================================
print("\n" + "=" * 70)
print("ANALISE DE ROBUSTEZ: SENSIBILIDADE AO CROSSWALK")
print("=" * 70)

# Amostra restrita: apenas matches 4-digit
df_4d = df_score[df_score['match_level'] == '4-digit'].copy()
df_4d_renda = df_4d[(df_4d['tem_renda'] == 1)].copy()

mean_full, ci_lo_f, ci_hi_f = weighted_ci(df_score['exposure_score'], df_score['peso'])
mean_4d, ci_lo_4, ci_hi_4 = weighted_ci(df_4d['exposure_score'], df_4d['peso'])

print(f"\n  Amostra completa:    N={len(df_score):,} | Media={mean_full:.4f} [IC: {ci_lo_f:.4f}-{ci_hi_f:.4f}]")
print(f"  Apenas match 4-digit: N={len(df_4d):,} | Media={mean_4d:.4f} [IC: {ci_lo_4:.4f}-{ci_hi_4:.4f}]")
print(f"  Diferenca: {mean_full - mean_4d:+.4f}")

# Re-rodar Mincer 2 com amostra restrita
df_mincer_4d = df_4d_renda[['rendimento_habitual', 'exposure_score', 'sexo_texto',
                              'raca_agregada', 'idade', 'nivel_instrucao', 'formal',
                              'regiao', 'setor_agregado', 'peso']].dropna().copy()
df_mincer_4d['log_renda'] = np.log(df_mincer_4d['rendimento_habitual'].clip(lower=1))

if len(df_mincer_4d) > 100:
    mincer_4d = smf.wls(
        'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
        'idade + I(idade**2) + C(nivel_instrucao) + formal + C(regiao) + C(setor_agregado)',
        data=df_mincer_4d, weights=df_mincer_4d['peso']
    ).fit(cov_type='HC1')

    coef_full = mincer2.params['exposure_score']
    coef_4d = mincer_4d.params['exposure_score']
    print(f"\n  Coef. exposicao (amostra completa): {coef_full:+.4f}{sig_stars(mincer2.pvalues['exposure_score'])}")
    print(f"  Coef. exposicao (apenas 4-digit):   {coef_4d:+.4f}{sig_stars(mincer_4d.pvalues['exposure_score'])}")
    print(f"  Diferenca: {abs(coef_full - coef_4d):.4f}")

    if abs(coef_full - coef_4d) < 0.05:
        print("\n  CONCLUSAO: Resultados robustos a exclusao dos matches 3-digit.")
    else:
        print("\n  ATENCAO: Sensibilidade detectada ao crosswalk. Reportar ambos.")
else:
    print("\n  Amostra 4-digit insuficiente para regressao.")

# ======================================================================
# 8.4 - Robustez 2: Winzorizacao da renda (P1-P99)
# ======================================================================
print("\n" + "=" * 70)
print("ROBUSTEZ 2: WINZORIZACAO DA RENDA (P1-P99)")
print("=" * 70)

p1 = df_mincer['rendimento_habitual'].quantile(0.01)
p99 = df_mincer['rendimento_habitual'].quantile(0.99)
df_winsor = df_mincer.copy()
df_winsor['renda_winsor'] = df_winsor['rendimento_habitual'].clip(lower=p1, upper=p99)
df_winsor['log_renda_w'] = np.log(df_winsor['renda_winsor'].clip(lower=1))

mincer_winsor = smf.wls(
    'log_renda_w ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
    'idade + I(idade**2) + C(nivel_instrucao) + formal + C(regiao) + C(setor_agregado)',
    data=df_winsor, weights=df_winsor['peso']
).fit(cov_type='HC1')

coef_orig = mincer2.params['exposure_score']
coef_winsor = mincer_winsor.params['exposure_score']
print(f"  Coef. exposicao (original):     {coef_orig:+.4f}")
print(f"  Coef. exposicao (winsorizado):  {coef_winsor:+.4f}")
print(f"  Diferenca: {abs(coef_orig - coef_winsor):.4f}")

if abs(coef_orig - coef_winsor) < 0.05:
    print("\n  CONCLUSAO: Resultados robustos a winzorizacao da renda.")
else:
    print("\n  ATENCAO: Sensibilidade detectada. Reportar ambos os resultados.")

# ======================================================================
# 8.5 - Robustez 3: Cluster por UPA (se disponivel)
# ======================================================================
print("\n" + "=" * 70)
print("ROBUSTEZ 3: ERROS-PADRAO CLUSTERIZADOS POR UPA")
print("=" * 70)

if 'upa' in df_mincer.columns or 'UPA' in df_mincer.columns:
    upa_col = 'upa' if 'upa' in df_mincer.columns else 'UPA'
    mincer_cluster = smf.wls(
        'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
        'idade + I(idade**2) + C(nivel_instrucao) + formal + C(regiao) + C(setor_agregado)',
        data=df_mincer, weights=df_mincer['peso']
    ).fit(cov_type='cluster', cov_kwds={'groups': df_mincer[upa_col]})

    print(f"\n  SE (HC1):    {mincer2.bse['exposure_score']:.4f}")
    print(f"  SE (Cluster): {mincer_cluster.bse['exposure_score']:.4f}")
    print(f"  Razao: {mincer_cluster.bse['exposure_score']/mincer2.bse['exposure_score']:.2f}x")

    if mincer_cluster.bse['exposure_score'] > mincer2.bse['exposure_score'] * 1.5:
        print("\n  ATENCAO: SEs clusterizados substancialmente maiores.")
        print("  HC1 subestima incerteza. Reportar ambos.")
    else:
        print("\n  SEs clusterizados similares aos HC1. Resultados robustos.")
else:
    print("\n  \u26a0 Variavel UPA nao encontrada no dataframe.")
    print("  Adicionar na etapa 1a (preparacao de dados) para permitir")
    print("  clusterizacao dos erros-padrao.")
```

    ======================================================================
    REGRESSAO WLS: DETERMINANTES DA EXPOSICAO A IA
    ======================================================================
    Amostra para regressao: 206,230 observacoes

    Variavel                       M1 (Demog.)               M2 (+Ocup.)               M3 (Completo)            
    ---------------------------------------------------------------------------------------------------------
    Mulher (ref: Homem)            +0.0215***                -0.0098***                +0.0008                  
    Branca (ref: Negra)            +0.0207***                +0.0114***                +0.0076***               
    Idade                          -0.0056***                -0.0015***                -0.0010***               
    Formal                         --                        --                        +0.0024***               
    ---------------------------------------------------------------------------------------------------------
    R²                             0.2255                     0.6832                     0.7430
    N                              206,230                     206,230                     206,230

    Significancia: * p<0.05, ** p<0.01, *** p<0.001

    --- Modelo completo (M3) - Resumo ---
    ==================================================================================================================
                                                         coef    std err          z      P>|z|      [0.025      0.975]
    ------------------------------------------------------------------------------------------------------------------
    Intercept                                          0.1863      0.003     56.111      0.000       0.180       0.193
    C(sexo_texto, Treatment("Homem"))[T.Mulher]        0.0008      0.001      1.276      0.202      -0.000       0.002
    C(raca_agregada, Treatment("Negra"))[T.Branca]     0.0076      0.001     14.084      0.000       0.007       0.009
    C(raca_agregada, Treatment("Negra"))[T.Outras]     0.0081      0.003      3.207      0.001       0.003       0.013
    C(nivel_instrucao)[T.2]                           -0.0012      0.001     -0.803      0.422      -0.004       0.002
    C(nivel_instrucao)[T.3]                            0.0006      0.002      0.361      0.718      -0.003       0.004
    C(nivel_instrucao)[T.4]                           -0.0001      0.002     -0.072      0.943      -0.003       0.003
    C(nivel_instrucao)[T.5]                            0.0083      0.002      5.488      0.000       0.005       0.011
    C(nivel_instrucao)[T.6]                            0.0236      0.002     12.571      0.000       0.020       0.027
    C(nivel_instrucao)[T.7]                            0.0272      0.002     15.756      0.000       0.024       0.031
    C(grande_grupo)[T.Apoio administrativo]            0.3551      0.001    248.030      0.000       0.352       0.358
    C(grande_grupo)[T.Dirigentes e gerentes]           0.1805      0.001    162.184      0.000       0.178       0.183
    C(grande_grupo)[T.Indústria qualificada]          -0.0281      0.001    -41.772      0.000      -0.029      -0.027
    C(grande_grupo)[T.Ocupações elementares]          -0.0461      0.001    -72.707      0.000      -0.047      -0.045
    C(grande_grupo)[T.Operadores de máquinas]          0.0277      0.001     32.260      0.000       0.026       0.029
    C(grande_grupo)[T.Profissionais das ciências]      0.1687      0.002    110.685      0.000       0.166       0.172
    C(grande_grupo)[T.Serviços e vendedores]           0.0995      0.001     93.891      0.000       0.097       0.102
    C(grande_grupo)[T.Técnicos nível médio]            0.1545      0.001    121.685      0.000       0.152       0.157
    C(regiao)[T.Nordeste]                              0.0015      0.001      2.052      0.040    6.63e-05       0.003
    C(regiao)[T.Norte]                                -0.0001      0.001     -0.123      0.902      -0.002       0.002
    C(regiao)[T.Sudeste]                              -0.0003      0.001     -0.381      0.703      -0.002       0.001
    C(regiao)[T.Sul]                                  -0.0016      0.001     -2.034      0.042      -0.003   -5.74e-05
    C(setor_agregado)[T.Alojamento e Alimentação]      0.0044      0.002      2.623      0.009       0.001       0.008
    C(setor_agregado)[T.Artes e Cultura]              -0.0355      0.003    -13.931      0.000      -0.041      -0.031
    C(setor_agregado)[T.Atividades Imobiliárias]       0.0219      0.003      7.121      0.000       0.016       0.028
    C(setor_agregado)[T.Comércio]                      0.0337      0.002     19.883      0.000       0.030       0.037
    C(setor_agregado)[T.Construção]                   -0.0300      0.001    -21.076      0.000      -0.033      -0.027
    C(setor_agregado)[T.Educação]                     -0.0599      0.001    -40.005      0.000      -0.063      -0.057
    C(setor_agregado)[T.Finanças e Seguros]            0.1069      0.003     37.617      0.000       0.101       0.112
    C(setor_agregado)[T.Ind. Transformação]           -0.0025      0.001     -1.759      0.079      -0.005       0.000
    C(setor_agregado)[T.Informação e Comunicação]      0.0863      0.002     39.678      0.000       0.082       0.091
    C(setor_agregado)[T.Outros Serviços]               0.0461      0.001     31.649      0.000       0.043       0.049
    C(setor_agregado)[T.Saúde]                        -0.0662      0.002    -40.158      0.000      -0.069      -0.063
    C(setor_agregado)[T.Serviços Administrativos]     -0.0012      0.002     -0.719      0.472      -0.004       0.002
    C(setor_agregado)[T.Serviços Domésticos]          -0.0069      0.001     -4.990      0.000      -0.010      -0.004
    C(setor_agregado)[T.Serviços Profissionais]        0.0335      0.002     18.265      0.000       0.030       0.037
    C(setor_agregado)[T.Transporte]                    0.0282      0.002     16.360      0.000       0.025       0.032
    C(setor_agregado)[T.Utilidades]                    0.0152      0.003      4.819      0.000       0.009       0.021
    idade                                             -0.0010      0.000     -7.505      0.000      -0.001      -0.001
    I(idade ** 2)                                   1.266e-05   1.56e-06      8.136      0.000    9.61e-06    1.57e-05
    formal                                             0.0024      0.001      4.422      0.000       0.001       0.003
    ==================================================================================================================

    ======================================================================
    EQUACAO DE MINCER AUMENTADA: log(renda) ~ exposicao + controles
    ======================================================================
    Amostra Mincer: 202,471 observacoes

    Variavel                                 Mincer 1             Mincer 2             Mincer 3            
    ----------------------------------------------------------------------------------------------------
    Exposicao                                +0.5248***           +0.3927***           +3.6870***          
    Exposicao²                               --                   --                   -4.1069***          
    Exposicao x Mulher                       --                   --                   -0.0581             
    Exposicao x Formal                       --                   --                   -0.8083***          
    Mulher                                   -0.3688***           -0.3248***           -0.2784***          
    Formal                                   +0.2030***           +0.1667***           +0.3952***          
    ----------------------------------------------------------------------------------------------------
    R²                                       0.3425                0.4078                0.4222
    N                                        202,471                202,471                202,471

    Interpretacao (Mincer 2):
      Coeficiente de exposicao: +0.3927 ***
      Um aumento de 0.1 no score de exposicao esta associado a
      4.8% de aumento na renda, ceteris paribus.

      ATENCAO: Esta analise e cross-sectional e nao permite
      inferencia causal. A correlacao entre exposicao e renda
      reflete sorting ocupacional, nao efeito causal da IA.

    ======================================================================
    ANALISE DE ROBUSTEZ: SENSIBILIDADE AO CROSSWALK
    ======================================================================

      Amostra completa:    N=206,230 | Media=0.2783 [IC: 0.2782-0.2783]
      Apenas match 4-digit: N=203,617 | Media=0.2781 [IC: 0.2781-0.2782]
      Diferenca: +0.0001

      Coef. exposicao (amostra completa): +0.3927***
      Coef. exposicao (apenas 4-digit):   +0.3970***
      Diferenca: 0.0043

      CONCLUSAO: Resultados robustos a exclusao dos matches 3-digit.

    ======================================================================
    ROBUSTEZ 2: WINZORIZACAO DA RENDA (P1-P99)
    ======================================================================
      Coef. exposicao (original):     +0.3927
      Coef. exposicao (winsorizado):  +0.3842
      Diferenca: 0.0085

      CONCLUSAO: Resultados robustos a winzorizacao da renda.

    ======================================================================
    ROBUSTEZ 3: ERROS-PADRAO CLUSTERIZADOS POR UPA
    ======================================================================

      ⚠ Variavel UPA nao encontrada no dataframe.
      Adicionar na etapa 1a (preparacao de dados) para permitir
      clusterizacao dos erros-padrao.

### 9. Sintese e conclusoes

Resumo dos principais achados, comparacao com a literatura e limitacoes.

> **Limitações adicionais identificadas:** 7. Crosswalk COD→ISCO-08
> introduz erro de medida; o índice ILO foi construído para ISCO-08 e a
> conversão pode gerar mismatches (teste de robustez com matches 4-digit
> mitiga parcialmente) 8. O índice ILO reflete a capacidade tecnológica
> de 2024/2025; a rápida evolução da IA generativa pode torná-lo
> defasado 9. Erros-padrão tratam amostra como SRS; valores reais podem
> ser maiores com desenho amostral complexo

> **Posicionamento do Brasil no contexto global (WP140):** O Brasil se
> posiciona como caso típico de país de renda média-alta: exposição
> média (0.278) ligeiramente inferior à média global (0.30) e
> consistente com o grupo upper-middle-income (~0.29). A proporção de
> trabalhadores em alta exposição (10.1%) está abaixo de países de alta
> renda (~20%) mas acima de países de baixa renda (~5%). As extensões
> originais desta dissertação — raça, formalidade, análise regional e
> equação de Mincer — preenchem lacunas deixadas pelo WP140 para o
> contexto de países em desenvolvimento.

``` python
# Etapa 1b.9 - Sintese e conclusoes

print("=" * 70)
print("SINTESE DOS PRINCIPAIS ACHADOS")
print("=" * 70)

print(f"""
ETAPA 1 - Analise Descritiva da Exposicao a IA Generativa no Brasil
=====================================================================
Dados: PNADc Q3/{PNAD_ANO} | {len(df):,} observacoes | {df['peso'].sum()/1e6:.1f} milhoes de trabalhadores
Indice: ILO WP140 (Gmyrek, Berg & Cappelli, 2025) | 427 ocupacoes ISCO-08

1. PERFIL DA EXPOSICAO
   - Exposicao media: {mean_geral:.3f} [IC 95%: {ci_lo_geral:.3f}-{ci_hi_geral:.3f}]
   - Inferior a media global (0.30), refletindo estrutura ocupacional brasileira
   - {pct_alta:.1f}% da forca de trabalho em alta exposicao (Gradientes 3-4)
   - Gini da exposicao: {gini_exp:.3f} (desigualdade moderada)

2. DESIGUALDADE E RENDA
   - Trabalhadores mais expostos ganham mais (razao Q5/Q1 = {renda_q5/renda_q1:.2f}x)
   - ATENCAO: relacao nao-monotonica (Q4 > Q5 em renda)
   - Relacao exposicao-renda nao-linear (LOWESS revela curvatura)
   - Indice de concentracao: {conc_index:+.4f} (exposicao concentrada nos mais ricos)
   - Regressao quantilica sugere efeito heterogeneo ao longo da distribuicao

3. GENERO E RACA
   - Mulheres mais expostas que homens ({gap_sexo:+.3f}, p<0.001)
   - Brancos mais expostos que negros ({gap_raca:+.3f}, p<0.001)
   - Oaxaca-Blinder: gaps explicados principalmente por segregacao ocupacional

4. FORMALIDADE
   - Formais mais expostos que informais (gap significativo)
   - Interacao exposicao x formalidade: retorno MENOR para formais
   - Informais de alta exposicao capturam mais retorno (profissionais liberais)

5. SETOR E OCUPACAO
   - Setores criticos: Financas, TI, Servicos Profissionais
   - Apoio administrativo e mais exposto dos grandes grupos
   - ANOVA confirma: setor e ocupacao explicam maior parte da variancia

6. REGIAO
   - Sudeste lidera, Norte menor exposicao
   - Variacao regional modesta (R² baixo na ANOVA por regiao)

7. ANALISE MULTIVARIADA
   - WLS: sexo, escolaridade e ocupacao sao os principais preditores
   - Mincer: exposicao associada positivamente a renda (ceteris paribus)
   - Robustez: resultados estaveis excluindo matches 3-digit

LIMITACOES
----------
1. Analise cross-sectional (Q3/{PNAD_ANO}) - nao permite inferencia causal
2. Indice global (OIT) aplicado ao Brasil - pode nao capturar especificidades locais
3. Exposicao != impacto - mede potencial, nao efeito realizado
4. Erros-padrao podem ser subestimados (amostra tratada como SRS)
5. 0.8% das observacoes sem match no crosswalk COD-ISCO08
6. Variavel de renda ausente para ~1.1 milhao de trabalhadores
7. Crosswalk COD->ISCO-08 introduz erro de medida; teste com matches 4-digit mitiga parcialmente
8. Indice ILO reflete capacidade tecnologica de 2024/2025; pode estar defasado
9. Erros-padrao tratam amostra como SRS; valores reais podem ser maiores
""")

print("=" * 70)
print("FIM DA ETAPA 1b - ANALISE DESCRITIVA")
print("=" * 70)
```

    ======================================================================
    SINTESE DOS PRINCIPAIS ACHADOS
    ======================================================================

    ETAPA 1 - Analise Descritiva da Exposicao a IA Generativa no Brasil
    =====================================================================
    Dados: PNADc Q3/2025 | 207,901 observacoes | 97.8 milhoes de trabalhadores
    Indice: ILO WP140 (Gmyrek, Berg & Cappelli, 2025) | 427 ocupacoes ISCO-08

    1. PERFIL DA EXPOSICAO
       - Exposicao media: 0.278 [IC 95%: 0.278-0.278]
       - Inferior a media global (0.30), refletindo estrutura ocupacional brasileira
       - 10.1% da forca de trabalho em alta exposicao (Gradientes 3-4)
       - Gini da exposicao: 0.295 (desigualdade moderada)

    2. DESIGUALDADE E RENDA
       - Trabalhadores mais expostos ganham mais (razao Q5/Q1 = 2.23x)
       - ATENCAO: relacao nao-monotonica (Q4 > Q5 em renda)
       - Relacao exposicao-renda nao-linear (LOWESS revela curvatura)
       - Indice de concentracao: +0.0810 (exposicao concentrada nos mais ricos)
       - Regressao quantilica sugere efeito heterogeneo ao longo da distribuicao

    3. GENERO E RACA
       - Mulheres mais expostas que homens (+0.044, p<0.001)
       - Brancos mais expostos que negros (+0.048, p<0.001)
       - Oaxaca-Blinder: gaps explicados principalmente por segregacao ocupacional

    4. FORMALIDADE
       - Formais mais expostos que informais (gap significativo)
       - Interacao exposicao x formalidade: retorno MENOR para formais
       - Informais de alta exposicao capturam mais retorno (profissionais liberais)

    5. SETOR E OCUPACAO
       - Setores criticos: Financas, TI, Servicos Profissionais
       - Apoio administrativo e mais exposto dos grandes grupos
       - ANOVA confirma: setor e ocupacao explicam maior parte da variancia

    6. REGIAO
       - Sudeste lidera, Norte menor exposicao
       - Variacao regional modesta (R² baixo na ANOVA por regiao)

    7. ANALISE MULTIVARIADA
       - WLS: sexo, escolaridade e ocupacao sao os principais preditores
       - Mincer: exposicao associada positivamente a renda (ceteris paribus)
       - Robustez: resultados estaveis excluindo matches 3-digit

    LIMITACOES
    ----------
    1. Analise cross-sectional (Q3/2025) - nao permite inferencia causal
    2. Indice global (OIT) aplicado ao Brasil - pode nao capturar especificidades locais
    3. Exposicao != impacto - mede potencial, nao efeito realizado
    4. Erros-padrao podem ser subestimados (amostra tratada como SRS)
    5. 0.8% das observacoes sem match no crosswalk COD-ISCO08
    6. Variavel de renda ausente para ~1.1 milhao de trabalhadores
    7. Crosswalk COD->ISCO-08 introduz erro de medida; teste com matches 4-digit mitiga parcialmente
    8. Indice ILO reflete capacidade tecnologica de 2024/2025; pode estar defasado
    9. Erros-padrao tratam amostra como SRS; valores reais podem ser maiores

    ======================================================================
    FIM DA ETAPA 1b - ANALISE DESCRITIVA
    ======================================================================

---

<!-- fonte: etapa_2a_preparacao_dados_did_caged_ilo.ipynb -->

# ETAPA 2a — Preparação do Painel CAGED + ILO Exposure Index


**Dissertação:** Inteligência Artificial Generativa e o Mercado de
Trabalho Brasileiro: Uma Análise de Exposição Ocupacional e seus Efeitos
Distributivos.

**Aluno:** Manoel Brasil Orlandi

------------------------------------------------------------------------

### Contextualização

A rápida difusão de modelos de IA generativa (LLMs, geradores de
imagem/código) levanta questões centrais sobre seus impactos no mercado
de trabalho. Para mensurar esse potencial de impacto, a Organização
Internacional do Trabalho (OIT) criou um índice de exposição ocupacional
à IA generativa, publicado como *Working Paper* 140 (WP140). O índice
atribui scores de exposição a cada ocupação da classificação ISCO-08,
com base na avaliação de suas tarefas constituintes por modelos de
linguagem e validação humana.

Este notebook prepara uma base de dados que junta os dados do **Novo
CAGED** (Cadastro Geral de Empregados e Desempregados) ao **índice de
exposição à IA generativa da OIT**, para ser usado em um modelo de
Diferenças-em-Diferenças (DiD) no Notebook 2b.

### Objetivo

Construir o **painel mensal de ocupações formais brasileiras
(2021–2025)** a partir do Novo CAGED, realizar o **crosswalk CBO 2002 →
ISCO-08** (especificação dual: 2 dígitos como principal, 4 dígitos para
robustez), e fazer o merge com o índice de exposição à IA generativa da
OIT (Gmyrek, Berg & Cappelli, 2025). O output final é um dataset
analítico pronto para a estimação DiD.

**Estratégia de crosswalk:** Análise principal a **2 dígitos** ISCO-08
(match por Sub-major Group com fallback hierárquico a Major Group), com
robustez a **4 dígitos** via correspondência ISCO-88 ↔ ISCO-08 +
fallback hierárquico em 6 níveis.

**Inspiração metodológica:** Hui, Reshef & Zhou (2024), “The Short-Term
Effects of Generative Artificial Intelligence on Employment: Evidence
from an Online Labor Market” — adaptado para dados administrativos
brasileiros (CAGED) com o índice ILO de exposição ocupacional.

### Ficha Técnica dos Dados

| Item | Descrição |
|----|----|
| **Fonte CAGED** | Ministério do Trabalho e Emprego (MTE), via Base dos Dados (BigQuery) |
| **Dataset BigQuery** | `basedosdados.br_me_caged.microdados_movimentacao` |
| **Período** | Janeiro/2021 — Dezembro/2025 (60 meses) |
| **Unidade** | Movimentação individual (admissão ou desligamento) |
| **Cobertura** | Emprego formal (CLT) em todo o Brasil |
| **Índice ILO** | `ilo_exposure_clean.csv` — 427 ocupações ISCO-08 com exposure scores |
| **Classificação** | CBO 2002 (CAGED) → ISCO-08 (ILO) via crosswalk hierárquico |

### Referências principais

- Gmyrek, P., Berg, J. & Cappelli, D. (2025). *Generative AI and Jobs:
  An updated global assessment*. ILO Working Paper 140.
- Hui, X., Reshef, O. & Zhou, L. (2024). *The Short-Term Effects of
  Generative AI on Employment*. Organization Science, 35(6).
- Brynjolfsson, E., Chandar, P. & Chen, J. (2025). *Canaries in the Coal
  Mine? Six Facts about the Recent Employment Effects of AI*.
- Callaway, B. & Sant’Anna, P. (2021). *Difference-in-differences with
  multiple time periods*. Journal of Econometrics, 225(2).
- Muendler, M.-A. & Poole, J.P. (2004). *Job Concordances for Brazil:
  Mapping CBO to ISCO-88*. UC San Diego.

### 1. Configuração do ambiente

Definir caminhos, importar bibliotecas e configurar parâmetros do
painel. Todos os caminhos são relativos ao diretório `notebook/`.

> **Nota sobre a janela temporal:** Excluímos 2020 para evitar os
> efeitos distorcivos da pandemia de COVID-19 sobre o mercado de
> trabalho formal. O ano de 2020 apresentou quedas e recuperações
> atípicas que contaminariam o período pré-tratamento do DiD. A janela
> Jan/2021–Dez/2025 oferece 23 meses pré-ChatGPT e 31 meses pós.

> **Nota sobre o Novo CAGED:** A partir de janeiro/2020, o CAGED foi
> substituído pelo sistema eSocial (Portaria SEPRT 1.127/2019). Usamos
> dados de 2021+ para consistência metodológica (eSocial já
> estabilizado).

``` python
# Verificar dependências e instalar apenas o que faltar (rode esta célula primeiro)
import importlib.util
import subprocess
import sys

# (nome para import, nome para pip install)
PACOTES = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("pyarrow", "pyarrow"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("scipy", "scipy"),
    ("pyfixest", "pyfixest"),
    ("bcb", "python-bcb"),  # IPCA Banco Central; import: from bcb import sgs
    ("xlrd", "xlrd"),  # Leitura de .xls (Crosswalk SOC/ISCO, Estrutura COD) — Anexo 1
    ("openpyxl", "openpyxl"),  # Leitura de .xlsx (Crosswalk SOC 2010 a 2018) — Anexo 1
    ("google.cloud.bigquery", "google-cloud-bigquery"),
]

def ja_instalado(nome_import):
    return importlib.util.find_spec(nome_import) is not None

faltando = [pip for imp, pip in PACOTES if not ja_instalado(imp)]
if faltando:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + faltando)
    print("Instalado:", ", ".join(faltando))
else:
    print("Todas as dependências já estão instaladas.")
```

    Instalado: xlrd


    [notice] A new release of pip is available: 24.2 -> 26.0.1
    [notice] To update, run: python3.10 -m pip install --upgrade pip

``` python
# Etapa 2a.1 — Configuração do ambiente

import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos (relativos ao diretório do notebook)
# ---------------------------------------------------------------------------
DATA_INPUT     = Path("../../data/input")
DATA_RAW       = Path("../../data/raw")
DATA_PROCESSED = Path("../../data/processed")
DATA_OUTPUT    = Path("../../data/output")

for d in [DATA_INPUT, DATA_RAW, DATA_PROCESSED, DATA_OUTPUT]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parâmetros do Painel CAGED
# ---------------------------------------------------------------------------
GCP_PROJECT_ID = "mestrado-pnad-2026"

ANO_INICIO     = 2021
ANO_FIM        = 2025
ANO_TRATAMENTO = 2022
MES_TRATAMENTO = 12   # Dezembro/2022 como primeiro mês "pós"

SALARIO_MINIMO = {
    2021: 1100, 2022: 1212, 2023: 1320, 2024: 1412, 2025: 1518
}

# ---------------------------------------------------------------------------
# Colunas a selecionar do CAGED (BigQuery)
# ---------------------------------------------------------------------------
COLUNAS_CAGED = """
    ano, mes, sigla_uf, id_municipio, cbo_2002,
    categoria, tipo_movimentacao, saldo_movimentacao,
    salario_mensal, grau_instrucao, idade, sexo, raca_cor,
    cnae_2_secao, cnae_2_subclasse, tamanho_estabelecimento_janeiro
"""

# ---------------------------------------------------------------------------
# Arquivos de referência
# ---------------------------------------------------------------------------
ILO_FILE               = DATA_PROCESSED / "ilo_exposure_clean.csv"
ISCO_08_88_FILE        = DATA_INPUT / "Correspondência ISCO 08 a 88.xlsx"
ISCO_08_ESTRUTURA_FILE = DATA_INPUT / "ISCO 08 Estruturas e Definições.xlsx"
MUENDLER_FILE          = DATA_INPUT / "cbo-isco-conc.csv"

# ---------------------------------------------------------------------------
# Checkpoints intermediários
# ---------------------------------------------------------------------------
PAINEL_MENSAL_FILE     = DATA_PROCESSED / "painel_caged_mensal.parquet"
PAINEL_CROSSWALK_FILE  = DATA_PROCESSED / "painel_caged_crosswalk.parquet"
PAINEL_TRATAMENTO_FILE = DATA_PROCESSED / "painel_caged_tratamento.parquet"
PAINEL_FINAL_PARQUET   = DATA_OUTPUT / "painel_caged_did_ready.parquet"
PAINEL_FINAL_CSV       = DATA_OUTPUT / "painel_caged_did_ready.csv"

# ---------------------------------------------------------------------------
# Cache: quando False, arquivos são deletados antes de (re)gerar (força reprocessamento)
# ---------------------------------------------------------------------------
KEEP_CAGED_RAW         = True   # data/raw/caged_*.parquet
KEEP_PANEL_MENSAL      = True   # painel_caged_mensal.parquet
KEEP_PANEL_CROSSWALK   = True   # painel_caged_crosswalk.parquet
KEEP_PANEL_TRATAMENTO  = False   # painel_caged_tratamento.parquet
KEEP_PANEL_FINAL       = False   # painel_caged_did_ready.parquet/csv
KEEP_ANTHROPIC_INDEX   = True    # anthropic_automation_augmentation_cbo.parquet (Anexo 1)

# Cache do índice Anthropic (Automation vs Augmentation) — Anexo 1
ANTHROPIC_INDEX_CACHE  = DATA_PROCESSED / "anthropic_automation_augmentation_cbo.parquet"

# ---------------------------------------------------------------------------
# Deflator (salário real): índice base para IPCA
# ---------------------------------------------------------------------------
INDICE_BASE_ANO = 2024
INDICE_BASE_MES = 12   # Dez/2024 = 100
INDICE_BASE     = 100.0
IPCA_MENSAL_FILE = DATA_PROCESSED / "ipca_mensal.parquet"

# ---------------------------------------------------------------------------
# Setor tecnológico (CNAE 2.0 seção): J = Informação e comunicação; M = Atividades profissionais/científicas
# ---------------------------------------------------------------------------
CNAE_SECOES_TECNOLOGICO = ['J']   # ou ['J', 'M'] para incluir atividades profissionais/científicas
SETOR_TECNOLOGICO_LIMIAR = 0.5    # setor_tecnologico=1 quando pct_tecnologico_adm >= este limiar

# ---------------------------------------------------------------------------
# Grandes grupos CBO (para sanity checks)
# ---------------------------------------------------------------------------
GRANDES_GRUPOS_CBO = {
    '0': 'Forças Armadas',
    '1': 'Dirigentes',
    '2': 'Profissionais das ciências',
    '3': 'Técnicos nível médio',
    '4': 'Trabalhadores de serv. admin.',
    '5': 'Trabalhadores de serviços/comércio',
    '6': 'Agropecuária',
    '7': 'Produção industrial',
    '8': 'Operadores de máquinas',
    '9': 'Manutenção e reparação',
}

print("Configuração carregada.")
print(f"  Período: {ANO_INICIO}–{ANO_FIM} ({(ANO_FIM - ANO_INICIO + 1) * 12} meses)")
print(f"  Evento: ChatGPT — Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
print(f"  Projeto GCP: {GCP_PROJECT_ID}")
print(f"  ILO file: {ILO_FILE} (existe: {ILO_FILE.exists()})")
```

    Configuração carregada.
      Período: 2021–2025 (60 meses)
      Evento: ChatGPT — Nov/2022 (pós a partir de 12/2022)
      Projeto GCP: mestrado-pnad-2026
      ILO file: data/processed/ilo_exposure_clean.csv (existe: True)

### 2. Índice IPCA (deflator para salário real)

Carregar série mensal do IPCA (Banco Central SGS) e construir índice com
base Dez/2024 = 100, para deflacionar salários nominais no
enriquecimento do painel.

``` python
# Etapa 2a.2 — Índice IPCA mensal (base Dez/2024 = 100)
# Fonte: Banco Central SGS (série 433 = variação mensal IPCA). Índice construído por acumulação.

if IPCA_MENSAL_FILE.exists():
    df_ipca = pd.read_parquet(IPCA_MENSAL_FILE)
    print(f"Índice IPCA carregado do cache: {IPCA_MENSAL_FILE.name}")
    print(f"  Período: {df_ipca['ano'].min():.0f}-{df_ipca['mes'].min():.0f} a {df_ipca['ano'].max():.0f}-{df_ipca['mes'].max():.0f}, base {INDICE_BASE_ANO}/{INDICE_BASE_MES} = {INDICE_BASE}")
else:
    from bcb import sgs
    # Série 433 = IPCA - Variação mensal (%)
    start = f"{ANO_INICIO}-01-01"
    end = f"{ANO_FIM}-12-31"
    raw = sgs.get({"IPCA_var": 433}, start=start, end=end)
    raw = raw.reset_index()
    raw.columns = ["data", "variacao"]
    raw["ano"] = raw["data"].dt.year
    raw["mes"] = raw["data"].dt.month
    # Ordenar por tempo e construir índice: base = 100 no mês INDICE_BASE_ANO/INDICE_BASE_MES
    raw = raw.sort_values(["ano", "mes"]).reset_index(drop=True)
    raw["fator"] = 1 + raw["variacao"] / 100.0
    # Índice em cadeia: 100 no mês base; para trás divide pelo fator do mês seguinte; para frente multiplica
    base_idx = raw[(raw["ano"] == INDICE_BASE_ANO) & (raw["mes"] == INDICE_BASE_MES)].index
    if len(base_idx) == 0:
        raise ValueError(f"Mês base {INDICE_BASE_ANO}/{INDICE_BASE_MES} não encontrado na série IPCA.")
    base_idx = base_idx[0]
    indice = np.ones(len(raw)) * np.nan
    indice[base_idx] = INDICE_BASE
    for i in range(base_idx - 1, -1, -1):
        indice[i] = indice[i + 1] / raw.loc[i + 1, "fator"]
    for i in range(base_idx + 1, len(raw)):
        indice[i] = indice[i - 1] * raw.loc[i, "fator"]
    raw["indice"] = indice
    df_ipca = raw[["ano", "mes", "indice"]].copy()
    df_ipca.to_parquet(IPCA_MENSAL_FILE, index=False)
    print(f"Índice IPCA construído e salvo: {IPCA_MENSAL_FILE.name}")
    print(f"  Período: {df_ipca['ano'].min():.0f}-{df_ipca['mes'].min():.0f} a {df_ipca['ano'].max():.0f}-{df_ipca['mes'].max():.0f}, base {INDICE_BASE_ANO}/{INDICE_BASE_MES} = {INDICE_BASE}")
```

    Índice IPCA carregado do cache: ipca_mensal.parquet
      Período: 2021-1 a 2025-12, base 2024/12 = 100.0

### 2a. Download dos microdados CAGED

Extrair do Novo CAGED (BigQuery/Base dos Dados) todas as movimentações
de emprego formal no período 2021–2025.

| Item | Descrição |
|----|----|
| **Tabela BigQuery** | `basedosdados.br_me_caged.microdados_movimentacao` |
| **Período** | 2021-01 a 2025-12 |
| **Filtros** | `ano BETWEEN 2021 AND 2025` |
| **Volume estimado** | ~20-30M de registros por ano, ~100-150M total |
| **Estratégia** | Download ano a ano via `google-cloud-bigquery` (Storage API) com fallback para `basedosdados` |

> **Nota metodológica — Volume de dados:** O CAGED registra ~20-25
> milhões de movimentações/ano. Para 5 anos, esperamos ~100-125M de
> registros. O download é feito ano a ano para evitar OOM e timeout, com
> salvamento em parquets individuais (`caged_{ano}.parquet`).

> **Nota sobre otimização:** Usamos a BigQuery Storage API
> (`create_bqstorage_client=True`) que transfere dados via gRPC/Arrow,
> sendo 2-5x mais rápida que o método padrão REST. Se o arquivo parquet
> já existir, o download é pulado automaticamente.

``` python
# Etapa 2a.2a — Download dos microdados CAGED
# Estratégia: download ano a ano via BigQuery Storage API, com cache local em parquet.

if not KEEP_CAGED_RAW:
    for f in DATA_RAW.glob("caged_*.parquet"):
        f.unlink()
        print(f"Cache CAGED removido: {f.name}")

from google.cloud import bigquery

def download_caged_ano(ano):
    """Baixar microdados CAGED de um ano via BigQuery Storage API."""
    parquet_path = DATA_RAW / f"caged_{ano}.parquet"

    if parquet_path.exists():
        size_mb = parquet_path.stat().st_size / 1e6
        df = pd.read_parquet(parquet_path)
        print(f"  {ano}: Carregado do cache — {len(df):,} registros ({size_mb:.0f} MB)")
        return df

    print(f"  {ano}: Baixando do BigQuery...", end="", flush=True)
    query = f"""
    SELECT {COLUNAS_CAGED}
    FROM `basedosdados.br_me_caged.microdados_movimentacao`
    WHERE ano = {ano}
    """
    client = bigquery.Client(project=GCP_PROJECT_ID)
    df = client.query(query).to_dataframe(create_bqstorage_client=True)
    df.to_parquet(parquet_path, index=False)
    size_mb = parquet_path.stat().st_size / 1e6
    print(f" {len(df):,} registros ({size_mb:.0f} MB)")
    return df

# ---------------------------------------------------------------------------
# Download ano a ano
# ---------------------------------------------------------------------------
print("Download dos microdados CAGED:")
dfs_anuais = []
for ano in range(ANO_INICIO, ANO_FIM + 1):
    df_ano = download_caged_ano(ano)
    dfs_anuais.append(df_ano)

# Resumo (sem concatenar em memória para evitar OOM)
total = sum(len(df) for df in dfs_anuais)
print(f"\nTotal: {total:,} movimentações ({ANO_INICIO}–{ANO_FIM})")
print(f"Colunas: {list(dfs_anuais[0].columns)}")
```

    Download dos microdados CAGED:
      2021: Carregado do cache — 36,554,795 registros (380 MB)
      2022: Carregado do cache — 42,475,516 registros (441 MB)
      2023: Carregado do cache — 44,485,982 registros (469 MB)
      2024: Carregado do cache — 48,996,040 registros (510 MB)
      2025: Carregado do cache — 26,312,103 registros (269 MB)

    Total: 198,824,436 movimentações (2021–2025)
    Colunas: ['ano', 'mes', 'sigla_uf', 'id_municipio', 'cbo_2002', 'categoria', 'tipo_movimentacao', 'saldo_movimentacao', 'salario_mensal', 'grau_instrucao', 'idade', 'sexo', 'raca_cor', 'cnae_2_secao', 'cnae_2_subclasse', 'tamanho_estabelecimento_janeiro']

### 2b. Verificar dados CAGED (CHECKPOINT)

Verificar integridade dos dados baixados: cobertura temporal (12
meses/ano), volume por ano, preenchimento de variáveis-chave, e formato
dos códigos CBO.

**Critérios de aceite:** - Todos os meses cobertos (Jan–Dez) para cada
ano - CBO com \>95% de preenchimento - ~20-30M registros por ano

``` python
# Etapa 2a.2b — CHECKPOINT: Verificar dados CAGED
# Carrega cada parquet individualmente (para evitar OOM)

print("=" * 60)
print("CHECKPOINT — Microdados CAGED")
print("=" * 60)

total_registros = 0
for ano in range(ANO_INICIO, ANO_FIM + 1):
    parquet_path = DATA_RAW / f"caged_{ano}.parquet"
    df = pd.read_parquet(parquet_path)

    # Volume
    print(f"\n--- {ano}: {len(df):,} movimentações ---")
    total_registros += len(df)

    # Cobertura mensal
    meses = sorted(df['mes'].dropna().unique())
    status = "OK" if len(meses) == 12 else f"ALERTA: {len(meses)} meses"
    print(f"  Meses: {len(meses)} ({status})")

    # Preenchimento CBO
    cbo_pct = df['cbo_2002'].notna().mean()
    print(f"  CBO preenchido: {cbo_pct:.1%}")

    # CBOs únicos
    cbos = df['cbo_2002'].dropna().astype(str).str[:4].nunique()
    print(f"  Famílias CBO 4d únicas: {cbos}")

    # Admissões vs desligamentos
    if 'saldo_movimentacao' in df.columns:
        adm = (df['saldo_movimentacao'] == 1).sum()
        desl = (df['saldo_movimentacao'] == -1).sum()
        print(f"  Admissões: {adm:,} | Desligamentos: {desl:,} | Saldo: {adm-desl:+,}")

print(f"\n{'=' * 60}")
print(f"TOTAL: {total_registros:,} movimentações ({ANO_INICIO}–{ANO_FIM})")
print(f"{'=' * 60}")
```

    ============================================================
    CHECKPOINT — Microdados CAGED
    ============================================================

    --- 2021: 36,554,795 movimentações ---
      Meses: 12 (OK)
      CBO preenchido: 100.0%
      Famílias CBO 4d únicas: 626
      Admissões: 19,703,604 | Desligamentos: 16,851,191 | Saldo: +2,852,413

    --- 2022: 42,475,516 movimentações ---
      Meses: 12 (OK)
      CBO preenchido: 100.0%
      Famílias CBO 4d únicas: 624
      Admissões: 22,243,441 | Desligamentos: 20,232,075 | Saldo: +2,011,366

    --- 2023: 44,485,982 movimentações ---
      Meses: 12 (OK)
      CBO preenchido: 100.0%
      Famílias CBO 4d únicas: 626
      Admissões: 22,982,161 | Desligamentos: 21,503,821 | Saldo: +1,478,340

    --- 2024: 48,996,040 movimentações ---
      Meses: 12 (OK)
      CBO preenchido: 100.0%
      Famílias CBO 4d únicas: 625
      Admissões: 25,336,277 | Desligamentos: 23,659,763 | Saldo: +1,676,514

    --- 2025: 26,312,103 movimentações ---
      Meses: 6 (ALERTA: 6 meses)
      CBO preenchido: 100.0%
      Famílias CBO 4d únicas: 622
      Admissões: 13,763,059 | Desligamentos: 12,549,044 | Saldo: +1,214,015

    ============================================================
    TOTAL: 198,824,436 movimentações (2021–2025)
    ============================================================

### 3a. Agregação: Microdados → Painel Mensal por Ocupação

Agregar os microdados de movimentação (nível individual) em um painel
mensal por ocupação CBO (4 dígitos). Cada linha do painel representará
uma ocupação-mês com métricas agregadas.

#### Estratégia de agregação

Seguindo a abordagem de Hui, Reshef & Zhou (2024), construímos um painel
ao nível de **ocupação × mês** com as seguintes métricas:

| Métrica | Cálculo | Descrição |
|----|----|----|
| `admissoes` | Contagem de `saldo_movimentacao == 1` | Fluxo de contratação |
| `desligamentos` | Contagem de `saldo_movimentacao == -1` | Fluxo de demissão |
| `saldo` | `admissoes - desligamentos` | Criação líquida de empregos |
| `salario_medio_adm` | Média do `salario_mensal` (admissões) | Nível salarial |
| `salario_mediano_adm` | Mediana do `salario_mensal` (admissões) | Robustez a outliers |
| `pct_mulher_adm` | % de `sexo == 3` nas admissões | Composição de gênero |
| `pct_superior_adm` | % com `grau_instrucao >= 9` | Composição educacional |

> **Nota — CBO 4 dígitos:** A CBO tem 6 dígitos (XXXX-XX), onde os 4
> primeiros definem a “família” ocupacional. Para o crosswalk com
> ISCO-08, usamos os 4 primeiros dígitos (família CBO ≈ unit group
> ISCO-08).

> **Nota — Otimização de memória:** O processamento é feito ano a ano
> para evitar OOM (Out-of-Memory) com ~100M+ registros. Flags booleanos
> são pré-computados como float para permitir agregação vetorizada
> (evitando lambdas lentas). A mediana é calculada separadamente por ser
> computacionalmente cara.

**Validação da codificação `sexo` (CAGED/Base dos Dados):** Confirmar
que os valores são 1 = Masculino e 3 = Feminino (não há código 2). O
agregado `pct_mulher_adm` usa `sexo == 3`.

``` python
# Conferir codificação de sexo nos microdados CAGED (um ano como amostra)
_ano_amostra = 2024
_path_amostra = DATA_RAW / f"caged_{_ano_amostra}.parquet"
if not _path_amostra.exists():
    _ano_amostra = ANO_INICIO
    _path_amostra = DATA_RAW / f"caged_{_ano_amostra}.parquet"
if _path_amostra.exists():
    _df_sexo = pd.read_parquet(_path_amostra, columns=["sexo"])
    print(f"sexo — value_counts (ano {_ano_amostra}):")
    print(_df_sexo["sexo"].value_counts().sort_index())
    print("  Esperado: 1 = Masculino, 3 = Feminino (Base dos Dados/CAGED).")
else:
    print("Nenhum parquet de microdados encontrado para verificar sexo.")
```

    sexo — value_counts (ano 2024):
    sexo
    1    28494836
    3    20500968
    9         236
    Name: count, dtype: int64
      Esperado: 1 = Masculino, 3 = Feminino (Base dos Dados/CAGED).

``` python
# Etapa 2a.3a — Agregação: Microdados → Painel Mensal por Ocupação
# Checkpoint: se o painel já existe, carrega direto.

if not KEEP_PANEL_MENSAL and PAINEL_MENSAL_FILE.exists():
    PAINEL_MENSAL_FILE.unlink()
    print(f"Cache removido: {PAINEL_MENSAL_FILE.name}")

if PAINEL_MENSAL_FILE.exists():
    painel = pd.read_parquet(PAINEL_MENSAL_FILE)
    print(f"Painel carregado do checkpoint: {PAINEL_MENSAL_FILE.name}")
    print(f"  {len(painel):,} linhas, {painel['cbo_4d'].nunique()} ocupações, "
          f"{painel['periodo'].nunique()} períodos")
else:
    print("Construindo painel a partir dos microdados (ano a ano)...")
    paineis_anuais = []

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        print(f"\n  Processando {ano}...", flush=True)
        df = pd.read_parquet(DATA_RAW / f"caged_{ano}.parquet")

        # CBO 4 dígitos
        df['cbo_2002'] = df['cbo_2002'].astype(str).str.strip()
        df['cbo_4d'] = df['cbo_2002'].str[:4]
        df = df[df['cbo_4d'].str.len() == 4]
        df = df[df['cbo_4d'].str.isdigit()]
        df = df[~df['cbo_4d'].isin(['0000'])]

        # Variáveis temporais
        df['periodo'] = df['ano'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2)
        df['periodo_num'] = df['ano'].astype(int) * 100 + df['mes'].astype(int)
        df['post'] = (df['periodo_num'] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)

        # Flags booleanos (CAGED: sexo 1=Masc, 3=Fem; alinhado à Etapa 1a)
        CODIGO_SEXO_MULHER = 3
        CODIGOS_RACA_BRANCA, CODIGOS_RACA_NEGRA = [1], [2, 4]
        IDADE_CORTE_JOVEM = 29
        CODIGOS_ESCOLARIDADE_SUPERIOR = ['9', '10', '11', '12', '13']
        df['is_mulher'] = (df['sexo'].astype(str) == str(CODIGO_SEXO_MULHER)).astype(float)
        raca_str = df['raca_cor'].astype(str)
        df['is_branco'] = raca_str.isin([str(c) for c in CODIGOS_RACA_BRANCA]).astype(float)
        df['is_negro'] = raca_str.isin([str(c) for c in CODIGOS_RACA_NEGRA]).astype(float)
        df['is_jovem'] = (df['idade'] <= IDADE_CORTE_JOVEM).astype(float)
        df['is_superior'] = df['grau_instrucao'].astype(str).isin(CODIGOS_ESCOLARIDADE_SUPERIOR).astype(float)
        # Setor tecnológico (CNAE 2.0 seção: J = Informação e comunicação, etc.)
        df['is_setor_tech'] = df['cnae_2_secao'].astype(str).str.strip().isin(CNAE_SECOES_TECNOLOGICO).astype(float)

        # Separar admissões e desligamentos
        df_adm = df[df['saldo_movimentacao'] == 1].copy()
        df_desl = df[df['saldo_movimentacao'] == -1]
        print(f"    {ano}: {len(df_adm):,} admissões, {len(df_desl):,} desligamentos", flush=True)

        # Colunas de salário mascaradas (média condicional por grupo)
        df_adm['sal_mulher'] = np.where(df_adm['is_mulher'] == 1, df_adm['salario_mensal'], np.nan)
        df_adm['sal_homem'] = np.where(df_adm['is_mulher'] == 0, df_adm['salario_mensal'], np.nan)
        df_adm['sal_branco'] = np.where(df_adm['is_branco'] == 1, df_adm['salario_mensal'], np.nan)
        df_adm['sal_negro'] = np.where(df_adm['is_negro'] == 1, df_adm['salario_mensal'], np.nan)
        df_adm['sal_jovem'] = np.where(df_adm['is_jovem'] == 1, df_adm['salario_mensal'], np.nan)
        df_adm['sal_naojovem'] = np.where(df_adm['is_jovem'] == 0, df_adm['salario_mensal'], np.nan)
        df_adm['sal_sup'] = np.where(df_adm['is_superior'] == 1, df_adm['salario_mensal'], np.nan)
        df_adm['sal_med'] = np.where(df_adm['is_superior'] == 0, df_adm['salario_mensal'], np.nan)
        df_adm['is_homem'] = 1 - df_adm['is_mulher']

        # Agregar admissões + heterogeneidade demográfica
        painel_adm = df_adm.groupby(['cbo_4d', 'ano', 'mes']).agg(
            admissoes=('saldo_movimentacao', 'count'),
            salario_medio_adm=('salario_mensal', 'mean'),
            idade_media_adm=('idade', 'mean'),
            pct_mulher_adm=('is_mulher', 'mean'),
            pct_superior_adm=('is_superior', 'mean'),
            pct_branco_adm=('is_branco', 'mean'),
            pct_negro_adm=('is_negro', 'mean'),
            pct_jovem_adm=('is_jovem', 'mean'),
            pct_tecnologico_adm=('is_setor_tech', 'mean'),
            salario_medio_mulher=('sal_mulher', 'mean'),
            salario_medio_homem=('sal_homem', 'mean'),
            salario_medio_branco=('sal_branco', 'mean'),
            salario_medio_negro=('sal_negro', 'mean'),
            salario_medio_jovem=('sal_jovem', 'mean'),
            salario_medio_naojovem=('sal_naojovem', 'mean'),
            salario_medio_superior=('sal_sup', 'mean'),
            salario_medio_medio=('sal_med', 'mean'),
            admissoes_mulher=('is_mulher', 'sum'),
            admissoes_homem=('is_homem', 'sum'),
            admissoes_jovem=('is_jovem', 'sum'),
            admissoes_negro=('is_negro', 'sum'),
        ).reset_index()

        # Mediana separada (performance)
        mediana = df_adm.groupby(['cbo_4d', 'ano', 'mes'])['salario_mensal'].median().reset_index()
        mediana.columns = ['cbo_4d', 'ano', 'mes', 'salario_mediano_adm']
        painel_adm = painel_adm.merge(mediana, on=['cbo_4d', 'ano', 'mes'], how='left')

        # Agregar desligamentos
        painel_desl = df_desl.groupby(['cbo_4d', 'ano', 'mes']).agg(
            desligamentos=('saldo_movimentacao', 'count'),
            salario_medio_desl=('salario_mensal', 'mean'),
        ).reset_index()

        # Merge
        p = painel_adm.merge(painel_desl, on=['cbo_4d', 'ano', 'mes'], how='outer').fillna(0)
        p['saldo'] = p['admissoes'] - p['desligamentos']
        p['n_movimentacoes'] = p['admissoes'] + p['desligamentos']
        p['setor_tecnologico'] = (p['pct_tecnologico_adm'] >= SETOR_TECNOLOGICO_LIMIAR).astype(int)
        p['periodo'] = p['ano'].astype(int).astype(str) + '-' + p['mes'].astype(int).astype(str).str.zfill(2)
        p['periodo_num'] = p['ano'].astype(int) * 100 + p['mes'].astype(int)
        p['post'] = (p['periodo_num'] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)
        p['ln_admissoes'] = np.log(p['admissoes'] + 1)
        p['ln_desligamentos'] = np.log(p['desligamentos'] + 1)
        p['ln_salario_adm'] = np.log(p['salario_medio_adm'].clip(lower=1))
        p['cbo_2d'] = p['cbo_4d'].str[:2]
        # Logs de heterogeneidade (salários e admissões por grupo)
        for grp in ['mulher', 'homem', 'branco', 'negro', 'jovem', 'naojovem', 'superior', 'medio']:
            col = f'salario_medio_{grp}'
            if col in p.columns:
                p[f'ln_salario_{grp}'] = np.log(p[col].clip(lower=1))
        for grp in ['mulher', 'homem', 'jovem', 'negro']:
            col = f'admissoes_{grp}'
            if col in p.columns:
                p[f'ln_admissoes_{grp}'] = np.log(p[col].astype(float) + 1)

        paineis_anuais.append(p)
        print(f"    → {len(p):,} linhas no painel", flush=True)

    painel = pd.concat(paineis_anuais, ignore_index=True)
    painel.to_parquet(PAINEL_MENSAL_FILE, index=False)
    print(f"\nPainel salvo: {PAINEL_MENSAL_FILE.name}")

print(f"\nPainel final: {len(painel):,} linhas")
print(f"  Ocupações: {painel['cbo_4d'].nunique()}, Períodos: {painel['periodo'].nunique()}")
print(f"  Shape: {painel.shape}")
```

    Painel carregado do checkpoint: painel_caged_mensal.parquet
      32,988 linhas, 629 ocupações, 54 períodos

    Painel final: 32,988 linhas
      Ocupações: 629, Períodos: 54
      Shape: (32988, 49)

### 3b. Verificar painel agregado (CHECKPOINT)

Verificar integridade do painel: dimensões, balanceamento (ocupações ×
períodos), cobertura temporal, distribuição de variáveis-chave e série
temporal agregada.

``` python
# Etapa 2a.3b — CHECKPOINT: Verificar painel agregado

print("=" * 60)
print("CHECKPOINT — Painel Ocupação × Mês")
print("=" * 60)

# 1. Dimensões
n_ocup = painel['cbo_4d'].nunique()
n_periodos = painel['periodo'].nunique()
print(f"\nOcupações: {n_ocup}")
print(f"Períodos: {n_periodos}")
print(f"Painel teórico (balanceado): {n_ocup * n_periodos:,}")
print(f"Painel real: {len(painel):,}")
print(f"Balanceamento: {len(painel) / (n_ocup * n_periodos):.1%}")

# 2. Ocupações com poucos meses
ocup_meses = painel.groupby('cbo_4d')['periodo'].nunique()
print(f"\nMeses por ocupação:")
print(f"  Min: {ocup_meses.min()}, Max: {ocup_meses.max()}, Média: {ocup_meses.mean():.1f}")
print(f"  Ocupações com < 12 meses: {(ocup_meses < 12).sum()}")
print(f"  Ocupações com todos os {n_periodos} meses: {(ocup_meses == n_periodos).sum()}")

# 3. Estatísticas descritivas
print("\nEstatísticas descritivas:")
print(painel[['admissoes', 'desligamentos', 'saldo', 'salario_medio_adm']].describe().round(1))

# 4. Série temporal agregada
ts = painel.groupby('periodo_num').agg(
    total_adm=('admissoes', 'sum'),
    total_desl=('desligamentos', 'sum'),
    sal_medio=('salario_medio_adm', 'mean'),
).reset_index()
print("\nSérie temporal (primeiros e últimos 3 meses):")
print(ts.head(3).to_string(index=False))
print("...")
print(ts.tail(3).to_string(index=False))
```

    ============================================================
    CHECKPOINT — Painel Ocupação × Mês
    ============================================================

    Ocupações: 629
    Períodos: 54
    Painel teórico (balanceado): 33,966
    Painel real: 32,988
    Balanceamento: 97.1%

    Meses por ocupação:
      Min: 2, Max: 54, Média: 52.4
      Ocupações com < 12 meses: 9
      Ocupações com todos os 54 meses: 589

    Estatísticas descritivas:
           admissoes  desligamentos    saldo  salario_medio_adm
    count    32988.0        32988.0  32988.0            32988.0
    mean      3153.5         2873.6    279.9             6131.1
    std      13880.0        12450.5   2323.0           158475.4
    min          0.0            0.0 -46650.0                0.0
    25%         60.0           60.0    -16.0             1782.8
    50%        293.0          289.0      7.0             2371.3
    75%       1338.0         1264.0    107.0             3811.2
    max     289900.0       284338.0  90556.0         18799538.2

    Série temporal (primeiros e últimos 3 meses):
     periodo_num  total_adm  total_desl   sal_medio
          202101    1550075     1293016 3697.157086
          202102    1715425     1317510 3723.743109
          202103    1626885     1450555 3252.934263
    ...
     periodo_num  total_adm  total_desl    sal_medio
          202504    2282187     2024659  4011.260301
          202505    2256225     2107233  4441.730675
          202506    2139182     1972561 11519.380585

#### Verificação: outlier salarial em Jun/2025

A série temporal agregada no checkpoint acima pode mostrar salário médio
elevado em Jun/2025 (~3× os meses anteriores). Abaixo verificamos se
isso reflete **(i)** poucas células ocupação×mês com salário muito alto
e/ou poucas movimentações, **(ii)** possível publicação parcial do mês,
ou **(iii)** padrão real dos dados. Conforme o diagnóstico, pode-se
documentar, filtrar células com poucas movimentações ou truncar a janela
em Mai/2025.

``` python
# Diagnóstico: Jun/2025 — distribuição de salario_medio_adm e células extremas
jun = painel[painel['periodo_num'] == 202506].copy()
print("Jun/2025 — Distribuição de salario_medio_adm (células ocupação×mês):")
print(jun['salario_medio_adm'].describe(percentiles=[0.5, 0.9, 0.95, 0.99]).round(2))
print()

# Células com poucas movimentações e salário alto
limiar_mov = 50
limiar_sal = 10_000
mask_extremo = (jun['n_movimentacoes'] < limiar_mov) & (jun['salario_medio_adm'] > limiar_sal)
n_extremo = mask_extremo.sum()
adm_jun_total = jun['admissoes'].sum()
adm_extremo = jun.loc[mask_extremo, 'admissoes'].sum()
print(f"Células com n_movimentacoes < {limiar_mov} e salario_medio_adm > R$ {limiar_sal:,.0f}: {n_extremo}")
print(f"  Admissões nessas células: {adm_extremo:,} ({100*adm_extremo/adm_jun_total:.2f}% do total de Jun/2025)")
if n_extremo > 0:
    print(jun.loc[mask_extremo, ['cbo_4d', 'admissoes', 'n_movimentacoes', 'salario_medio_adm']].sort_values('salario_medio_adm', ascending=False).head(15).to_string(index=False))
print()

# Comparação com Mai/2025 e média 2025
mai = painel[painel['periodo_num'] == 202505]
ano2025 = painel[painel['periodo_num'] // 100 == 2025]
print("Comparativo 2025:")
print(f"  Mai/2025: células={len(mai)}, total_adm={mai['admissoes'].sum():,.0f}, sal_medio(agg)={mai['salario_medio_adm'].mean():,.0f}")
print(f"  Jun/2025: células={len(jun)}, total_adm={adm_jun_total:,.0f}, sal_medio(agg)={jun['salario_medio_adm'].mean():,.0f}")
print(f"  Média mensal 2025: células~{len(ano2025)//12:.0f}, total_adm~{ano2025.groupby('periodo_num')['admissoes'].sum().mean():,.0f}")
```

    Jun/2025 — Distribuição de salario_medio_adm (células ocupação×mês):
    count        615.00
    mean       11519.38
    std       170295.09
    min            0.00
    50%         2647.30
    90%         7652.32
    95%        10449.24
    99%        38462.94
    max      4216672.39
    Name: salario_medio_adm, dtype: float64

    Células com n_movimentacoes < 50 e salario_medio_adm > R$ 10,000: 9
      Admissões nessas células: 125 (0.01% do total de Jun/2025)
    cbo_4d  admissoes  n_movimentacoes  salario_medio_adm
      2423          1                1       80466.670000
      1237         22               48       43743.163182
      1222         19               49       41853.112105
      1234         15               36       38843.381333
      1221          6               15       35815.645000
      1223         19               36       14490.656842
      2422          1                1       14097.220000
      2622         24               48       12752.264583
      1031         18               20       10953.792222

    Comparativo 2025:
      Mai/2025: células=614, total_adm=2,256,225, sal_medio(agg)=4,442
      Jun/2025: células=615, total_adm=2,139,182, sal_medio(agg)=11,519
      Média mensal 2025: células~306, total_adm~2,293,843

### 4a. Crosswalk CBO 2002 → ISCO-08

Mapear os códigos CBO 2002 (usados no CAGED) para ISCO-08 (usados no
índice ILO). **Esta é a etapa metodologicamente mais delicada do
pipeline.**

#### Contexto

A CBO 2002 foi construída com base na ISCO-88/ISCO-08, compartilhando a
mesma estrutura hierárquica:

| Nível | CBO 2002 | ISCO-08 | Alinhamento |
|----|----|----|----|
| 1 dígito | Grande Grupo (10) | Major Group (10) | Perfeito |
| 2 dígitos | Subgrupo Principal (~46) | Sub-major Group (43) | Bom (14 CBOs sem match direto) |
| 3 dígitos | Subgrupo (~194) | Minor Group (130) | Parcial (~45% direto) |
| 4 dígitos | Família (~629) | Unit Group (427) | Divergente (~28% direto) |

#### Estratégia adotada: Dual (2d principal + 4d robustez)

**PARTE A — Especificação PRINCIPAL (2 dígitos):** - CBO 2d → ISCO-08
Sub-major Group (match direto) - Fallback: CBO 1d → ISCO-08 Major Group
(média) - Cobertura esperada: **100%**

**PARTE B — Especificação de ROBUSTEZ (4 dígitos, fallback hierárquico
em 6 níveis):**

| Nível | Estratégia | Cobertura esperada |
|----|----|----|
| N1 | CBO 4d = ISCO-08 4d (match direto) | ~28% |
| N2 | CBO 4d = ISCO-88 4d → ISCO-08 via correspondência oficial | ~+9% |
| N3 | CBO 3d = ISCO-08 3d (média Minor Group) | ~+20% |
| N4 | CBO 3d = ISCO-88 3d → ISCO-08 via correspondência | ~+1% |
| N5 | CBO 2d = ISCO-08 2d (= especificação principal) | ~+18% |
| N6 | CBO 1d = ISCO-08 1d (média Major Group) | ~+24% |

> **Nota — Muendler (CBO 1994):** O arquivo `cbo-isco-conc.csv` de
> Muendler & Poole (2004) mapeia CBO **1994** → ISCO-88, NÃO a CBO 2002
> usada no CAGED. Por isso, o match 4d via Muendler é limitado. A
> estratégia principal utiliza a similaridade estrutural entre CBO 2002
> e ISCO-08/88 com fallback hierárquico.

> **Nota sobre atenuação:** Se o crosswalk a 4 dígitos introduz erro de
> medição, o efeito típico é **atenuação** (viés em direção a zero).
> Encontrar efeito significativo mesmo com erro de medição sugere que o
> efeito real é provavelmente maior.

**Validação do crosswalk:** O notebook não usa Muendler para o match
principal; utiliza a correspondência oficial ISCO-08↔88 e fallback
hierárquico. Na especificação 2d: match direto CBO 2d → ISCO-08
Sub-major Group, com fallback a 1 dígito (Major Group). Na 4d: fallback
em 6 níveis (N1→N6). Resultado verificado: cobertura 100% em 2d e 4d,
correlação entre exposure_score_2d e exposure_score_4d ~0,915 —
consistente com o planejamento e pronto para o DiD no Notebook 2b.

``` python
# Etapa 2a.4a — Crosswalk CBO 2002 → ISCO-08 (Dual: 2d principal + 4d robustez)
# Checkpoint: se o painel com crosswalk já existe, carrega direto.

if not KEEP_PANEL_CROSSWALK and PAINEL_CROSSWALK_FILE.exists():
    PAINEL_CROSSWALK_FILE.unlink()
    print(f"Cache removido: {PAINEL_CROSSWALK_FILE.name}")

if PAINEL_CROSSWALK_FILE.exists():
    painel = pd.read_parquet(PAINEL_CROSSWALK_FILE)
    print(f"Crosswalk carregado do checkpoint: {PAINEL_CROSSWALK_FILE.name}")
    print(f"  {len(painel):,} linhas, cobertura 2d: {painel['exposure_score_2d'].notna().mean():.1%}, "
          f"4d: {painel['exposure_score_4d'].notna().mean():.1%}")
else:
    # ══════════════════════════════════════════════════════════════════════
    # Carregar dados de referência
    # ══════════════════════════════════════════════════════════════════════
    df_ilo = pd.read_csv(ILO_FILE)
    df_ilo['isco_08_str'] = df_ilo['isco_08'].astype(str).str.zfill(4)
    print(f"Índice ILO carregado: {len(df_ilo)} ocupações ISCO-08")
    print(f"  Score range: [{df_ilo['exposure_score'].min():.3f}, {df_ilo['exposure_score'].max():.3f}]")

    # Dicts ILO em múltiplos níveis
    codes = df_ilo['isco_08_str']
    ilo_4d = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()
    ilo_3d = df_ilo.assign(g=codes.str[:3]).groupby('g')['exposure_score'].mean().to_dict()
    ilo_2d = df_ilo.assign(g=codes.str[:2]).groupby('g')['exposure_score'].mean().to_dict()
    ilo_1d = df_ilo.assign(g=codes.str[:1]).groupby('g')['exposure_score'].mean().to_dict()

    # Correspondência ISCO-08 ↔ ISCO-88 (arquivo local)
    isco88_to_08 = {}
    isco88_3d_to_08_3d = {}
    if ISCO_08_88_FILE.exists():
        df_corr = pd.read_excel(ISCO_08_88_FILE, sheet_name='ISCO-08 to 88')
        df_corr['isco08_4d'] = df_corr['ISCO-08 code'].astype(str).str.strip().str.zfill(4)
        df_corr['isco88_4d'] = df_corr['ISCO-88 code'].astype(str).str.strip().str.zfill(4)
        isco88_to_08 = df_corr.groupby('isco88_4d')['isco08_4d'].apply(list).to_dict()
        df_corr['isco88_3d'] = df_corr['isco88_4d'].str[:3]
        df_corr['isco08_3d'] = df_corr['isco08_4d'].str[:3]
        isco88_3d_to_08_3d = df_corr.groupby('isco88_3d')['isco08_3d'].apply(
            lambda x: list(set(x))).to_dict()
        print(f"  Correspondência ISCO-08↔88: {len(df_corr)} mapeamentos")

    # ══════════════════════════════════════════════════════════════════════
    # PARTE A: 2 dígitos (PRINCIPAL)
    # ══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}\nPARTE A: Crosswalk 2 dígitos (PRINCIPAL)\n{'='*60}")

    painel['exposure_score_2d'] = painel['cbo_2d'].map(ilo_2d)
    painel['match_level_2d'] = np.where(painel['exposure_score_2d'].notna(), '2-digit', None)

    # Fallback a 1 dígito
    mask_na = painel['exposure_score_2d'].isna()
    if mask_na.any():
        cbo_1d = painel.loc[mask_na, 'cbo_4d'].str[:1]
        painel.loc[mask_na, 'exposure_score_2d'] = cbo_1d.map(ilo_1d).values
        painel.loc[mask_na, 'match_level_2d'] = '1-digit (fallback)'

    painel['exposure_score'] = painel['exposure_score_2d']
    cov_2d = painel['exposure_score_2d'].notna().mean()
    print(f"  COBERTURA 2d: {cov_2d:.1%}")
    for lvl, cnt in painel['match_level_2d'].value_counts().items():
        print(f"    {lvl}: {cnt:,} ({cnt/len(painel):.1%})")

    # ══════════════════════════════════════════════════════════════════════
    # PARTE B: 4 dígitos (ROBUSTEZ) — fallback hierárquico 6 níveis
    # ══════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}\nPARTE B: Crosswalk 4 dígitos (ROBUSTEZ)\n{'='*60}")

    cbos_unicos = sorted(painel['cbo_4d'].unique())
    cbo_score_4d = {}
    cbo_match_level = {}
    counts = {'N1': 0, 'N2': 0, 'N3': 0, 'N4': 0, 'N5': 0, 'N6': 0, 'sem': 0}

    for cbo in cbos_unicos:
        score, level = None, None

        # N1: CBO 4d = ISCO-08 4d
        if cbo in ilo_4d:
            score, level = ilo_4d[cbo], 'N1: ISCO-08 4d direto'
            counts['N1'] += 1
        # N2: CBO 4d = ISCO-88 4d → ISCO-08
        if score is None and cbo in isco88_to_08:
            scores_c = [ilo_4d[c] for c in isco88_to_08[cbo] if c in ilo_4d]
            if scores_c:
                score, level = np.mean(scores_c), 'N2: via ISCO-88→08 4d'
                counts['N2'] += 1
        # N3: CBO 3d = ISCO-08 3d
        if score is None and cbo[:3] in ilo_3d:
            score, level = ilo_3d[cbo[:3]], 'N3: ISCO-08 3d'
            counts['N3'] += 1
        # N4: CBO 3d = ISCO-88 3d → ISCO-08 3d
        if score is None and cbo[:3] in isco88_3d_to_08_3d:
            scores_c = [ilo_3d[c] for c in isco88_3d_to_08_3d[cbo[:3]] if c in ilo_3d]
            if scores_c:
                score, level = np.mean(scores_c), 'N4: via ISCO-88→08 3d'
                counts['N4'] += 1
        # N5: CBO 2d = ISCO-08 2d
        if score is None and cbo[:2] in ilo_2d:
            score, level = ilo_2d[cbo[:2]], 'N5: ISCO-08 2d'
            counts['N5'] += 1
        # N6: CBO 1d = ISCO-08 1d
        if score is None and cbo[:1] in ilo_1d:
            score, level = ilo_1d[cbo[:1]], 'N6: ISCO-08 1d'
            counts['N6'] += 1

        if score is not None:
            cbo_score_4d[cbo] = score
            cbo_match_level[cbo] = level
        else:
            counts['sem'] += 1

    painel['exposure_score_4d'] = painel['cbo_4d'].map(cbo_score_4d)
    painel['match_level_4d'] = painel['cbo_4d'].map(cbo_match_level)

    total = len(cbos_unicos)
    print(f"  CBOs 4d únicos: {total}")
    for k, v in counts.items():
        if v > 0:
            print(f"    {k}: {v} ({v/total:.1%})")
    print(f"  COBERTURA 4d: {painel['exposure_score_4d'].notna().mean():.1%}")

    # Correlação 2d vs 4d
    df_check = painel[['cbo_4d', 'exposure_score_2d', 'exposure_score_4d']].drop_duplicates('cbo_4d')
    corr = df_check['exposure_score_2d'].corr(df_check['exposure_score_4d'])
    print(f"\n  Correlação Pearson (2d vs 4d): {corr:.4f}")

    painel.to_parquet(PAINEL_CROSSWALK_FILE, index=False)
    print(f"\nSalvo: {PAINEL_CROSSWALK_FILE.name}")
```

    Crosswalk carregado do checkpoint: painel_caged_crosswalk.parquet
      32,988 linhas, cobertura 2d: 100.0%, 4d: 100.0%

**CBOs 2 dígitos sem match direto em ISCO-08:** Subgrupos principais CBO
que não possuem equivalente direto em Sub-major Group ISCO-08; recebem
score via fallback a 1 dígito (Major Group). Lista abaixo (a partir do
painel com crosswalk).

``` python
# Listar CBO 2d que caem no fallback a 1 dígito (sem match direto em ISCO-08 Sub-major Group)
if 'match_level_2d' in painel.columns:
    fallback_2d = painel[painel['match_level_2d'] == '1-digit (fallback)']['cbo_2d'].unique()
    fallback_2d = sorted(fallback_2d)
    print(f"CBOs 2d sem match direto (fallback a Major Group): {len(fallback_2d)}")
    print("Códigos:", fallback_2d)
    # Opcional: exemplos de cbo_4d por um desses 2d
    if len(fallback_2d) > 0:
        ex = painel[painel['cbo_2d'] == fallback_2d[0]][['cbo_2d', 'cbo_4d']].drop_duplicates()
        print(f"\nExemplo (cbo_2d={fallback_2d[0]}): cbo_4d presentes: {ex['cbo_4d'].tolist()[:8]}...")
else:
    print("Coluna match_level_2d não encontrada (crosswalk pode ter sido carregado sem essa coluna).")
```

    CBOs 2d sem match direto (fallback a Major Group): 14
    Códigos: ['10', '20', '27', '30', '37', '39', '64', '76', '77', '78', '79', '84', '86', '99']

    Exemplo (cbo_2d=10): cbo_4d presentes: ['1010', '1011', '1020', '1021', '1030', '1031']...

### 4b. Verificar crosswalk (CHECKPOINT)

Validar qualidade do crosswalk nas DUAS especificações: principal (2
dígitos) e robustez (4 dígitos). Verificar cobertura, distribuição de
scores, correlação entre especificações e sanity check por grande grupo
CBO.

**Critérios de aceite:** - Cobertura 2d ≥ 95% (esperado ~100%) -
Cobertura 4d ≥ 80% (esperado ~100% com fallback) - Correlação 2d vs 4d
\> 0.8 (consistência entre especificações)

``` python
# Etapa 2a.4b — CHECKPOINT: Verificar crosswalk CBO → ISCO-08

print("=" * 60)
print("CHECKPOINT — Crosswalk CBO → ISCO-08 (Dual)")
print("=" * 60)

# 1. Cobertura
coverage_2d = painel['exposure_score_2d'].notna().mean()
coverage_4d = painel['exposure_score_4d'].notna().mean()
print(f"\n--- Cobertura ---")
print(f"  2 dígitos (PRINCIPAL): {coverage_2d:.1%}")
print(f"  4 dígitos (ROBUSTEZ):  {coverage_4d:.1%}")
if coverage_2d < 0.95:
    print(f"  ALERTA: Cobertura 2d abaixo de 95%!")
if coverage_4d < 0.80:
    print(f"  AVISO: Cobertura 4d abaixo de 80%.")

# 2. Estatísticas dos scores
print(f"\n--- Estatísticas dos scores ---")
print(f"\nexposure_score_2d (PRINCIPAL):")
print(painel['exposure_score_2d'].describe().round(4))
print(f"\nexposure_score_4d (ROBUSTEZ):")
print(painel['exposure_score_4d'].describe().round(4))

# 3. Correlação
mask_both = painel['exposure_score_2d'].notna() & painel['exposure_score_4d'].notna()
if mask_both.any():
    corr = painel.loc[mask_both, 'exposure_score_2d'].corr(
        painel.loc[mask_both, 'exposure_score_4d'])
    print(f"\n--- Correlação 2d vs 4d ---")
    print(f"  Pearson: {corr:.4f}")
    print(f"  {'Alta correlação — bom sinal de consistência.' if corr > 0.8 else 'Correlação moderada.'}")

# 4. Sanity check por grande grupo CBO
painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]
print(f"\n--- Exposição por grande grupo CBO ---")
print(f"{'Grande Grupo':<40} {'Score 2d':>10} {'Score 4d':>10}")
print("-" * 62)
for gg, nome in sorted(GRANDES_GRUPOS_CBO.items()):
    mask = painel['grande_grupo_cbo'] == gg
    if mask.any():
        s2d = painel.loc[mask, 'exposure_score_2d'].mean()
        s4d = painel.loc[mask, 'exposure_score_4d'].mean()
        s4d_str = f"{s4d:.3f}" if not np.isnan(s4d) else "N/A"
        flag = " (!)" if not np.isnan(s4d) and abs(s2d - s4d) > 0.1 else ""
        print(f"  {nome:<38} {s2d:>10.3f} {s4d_str:>10}{flag}")
print(f"  (!) = diferença > 0.1 entre 2d e 4d")
```

    ============================================================
    CHECKPOINT — Crosswalk CBO → ISCO-08 (Dual)
    ============================================================

    --- Cobertura ---
      2 dígitos (PRINCIPAL): 100.0%
      4 dígitos (ROBUSTEZ):  100.0%

    --- Estatísticas dos scores ---

    exposure_score_2d (PRINCIPAL):
    count    32988.0000
    mean         0.2778
    std          0.1243
    min          0.1167
    25%          0.1658
    50%          0.2459
    75%          0.3725
    max          0.6325
    Name: exposure_score_2d, dtype: float64

    exposure_score_4d (ROBUSTEZ):
    count    32988.0000
    mean         0.2830
    std          0.1315
    min          0.0900
    25%          0.1658
    50%          0.2500
    75%          0.3650
    max          0.7000
    Name: exposure_score_4d, dtype: float64

    --- Correlação 2d vs 4d ---
      Pearson: 0.9150
      Alta correlação — bom sinal de consistência.

    --- Exposição por grande grupo CBO ---
    Grande Grupo                               Score 2d   Score 4d
    --------------------------------------------------------------
      Dirigentes                                  0.367      0.375
      Profissionais das ciências                  0.393      0.396
      Técnicos nível médio                        0.334      0.338
      Trabalhadores de serv. admin.               0.580      0.557
      Trabalhadores de serviços/comércio          0.243      0.247
      Agropecuária                                0.157      0.161
      Produção industrial                         0.161      0.165
      Operadores de máquinas                      0.213      0.217
      Manutenção e reparação                      0.143      0.187
      (!) = diferença > 0.1 entre 2d e 4d

### 5a. Definição de tratamento

Definir as variáveis de tratamento para a análise DiD. O tratamento é
baseado na **exposição ocupacional à IA generativa**: ocupações com alta
exposição (top 20%) vs. baixa exposição.

#### Variáveis criadas

| Variável | Definição | Uso |
|----|----|----|
| `alta_exp` | 1 se `exposure_score_2d >= percentil 80` | **Especificação principal** |
| `alta_exp_10` | 1 se `exposure_score_2d >= percentil 90` | Robustez (cutoff) |
| `alta_exp_25` | 1 se `exposure_score_2d >= percentil 75` | Robustez (cutoff) |
| `alta_exp_mediana` | 1 se `exposure_score_2d >= mediana` | Alternativa binária |
| `quintil_exp` | Quintil de exposição (Q1–Q5) | Análise por quantil |
| `alta_exp_4d` | 1 se `exposure_score_4d >= percentil 80` | Robustez (crosswalk 4d) |
| `did` | `post × alta_exp` | Interação DiD principal |
| `did_4d` | `post × alta_exp_4d` | Interação DiD robustez |

> **Nota:** Os thresholds são calculados sobre a distribuição de
> **ocupações** (uma obs por CBO), não ponderada por volume de
> movimentações. Cada ocupação tem peso igual na definição do
> tratamento.

> **Nota — Tratamento contínuo:** Além das dummies, `exposure_score_2d`
> e `exposure_score_4d` podem ser usados diretamente como tratamento
> contínuo em especificações alternativas, conforme Hui et al. (2024).

``` python
# Etapa 2a.5a — Definição de tratamento

# ── Thresholds sobre a distribuição de ocupações (2d) ──
ocup_scores_2d = painel.groupby('cbo_4d')['exposure_score_2d'].first().dropna()

thresholds_2d = {
    'alta_exp_10':      ocup_scores_2d.quantile(0.90),
    'alta_exp':         ocup_scores_2d.quantile(0.80),  # PRINCIPAL
    'alta_exp_25':      ocup_scores_2d.quantile(0.75),
    'alta_exp_mediana':  ocup_scores_2d.quantile(0.50),
}

print("Thresholds de exposição (2d, PRINCIPAL):")
for name, val in thresholds_2d.items():
    n_above = (ocup_scores_2d >= val).sum()
    pct = n_above / len(ocup_scores_2d) * 100
    print(f"  {name}: {val:.4f} ({n_above} ocupações, {pct:.0f}%)")

# ── Dummies de tratamento 2d ──
for name, threshold in thresholds_2d.items():
    painel[name] = (painel['exposure_score_2d'] >= threshold).astype(int)

# Quintis
painel['quintil_exp'] = pd.qcut(
    painel['exposure_score_2d'].rank(method='first'),
    q=5,
    labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
)

# ── Dummies 4d (ROBUSTEZ) ──
ocup_scores_4d = painel.groupby('cbo_4d')['exposure_score_4d'].first().dropna()
threshold_4d_80 = ocup_scores_4d.quantile(0.80)
painel['alta_exp_4d'] = (painel['exposure_score_4d'] >= threshold_4d_80).astype(int)
print(f"\nThreshold 4d (p80): {threshold_4d_80:.4f} ({(ocup_scores_4d >= threshold_4d_80).sum()} ocupações)")

# ── Interações DiD ──
painel['did'] = painel['post'] * painel['alta_exp']
painel['did_4d'] = painel['post'] * painel['alta_exp_4d']

# ── Resumo ──
print(f"\n--- Distribuição de tratamento ---")
print(f"  Alta exp 2d (top 20%): {painel['alta_exp'].mean():.1%} das obs")
print(f"  Alta exp 4d (top 20%): {painel['alta_exp_4d'].mean():.1%} das obs")
print(f"  Períodos pré:  {painel[painel['post']==0].shape[0]:,}")
print(f"  Períodos pós:  {painel[painel['post']==1].shape[0]:,}")

concordancia = (painel['alta_exp'] == painel['alta_exp_4d']).mean()
print(f"  Concordância 2d vs 4d: {concordancia:.1%}")

# Tabela de contingência
ct = pd.crosstab(
    painel['post'].map({0: 'Pré', 1: 'Pós'}),
    painel['alta_exp'].map({0: 'Controle', 1: 'Tratamento'}),
    margins=True
)
print(f"\nTabela de contingência (2d, principal):")
print(ct)
```

    Thresholds de exposição (2d, PRINCIPAL):
      alta_exp_10: 0.4433 (78 ocupações, 12%)
      alta_exp: 0.3854 (131 ocupações, 21%)
      alta_exp_25: 0.3725 (165 ocupações, 26%)
      alta_exp_mediana: 0.2459 (332 ocupações, 53%)

    Threshold 4d (p80): 0.3863 (137 ocupações)

    --- Distribuição de tratamento ---
      Alta exp 2d (top 20%): 20.3% das obs
      Alta exp 4d (top 20%): 21.3% das obs
      Períodos pré:  14,058
      Períodos pós:  18,930
      Concordância 2d vs 4d: 93.1%

    Tabela de contingência (2d, principal):
    alta_exp  Controle  Tratamento    All
    post                                 
    Pré          11195        2863  14058
    Pós          15092        3838  18930
    All          26287        6701  32988

### 5b. Verificar tratamento (CHECKPOINT)

Validar a definição de tratamento: top/bottom ocupações por exposição,
distribuição por quintil, e concordância entre especificações 2d e 4d.

``` python
# Etapa 2a.5b — CHECKPOINT: Verificar definição de tratamento

print("=" * 60)
print("CHECKPOINT — Definição de Tratamento")
print("=" * 60)

# 1. Top 10 ocupações mais expostas
print("\n--- Top 10 ocupações MAIS expostas ---")
top10 = painel.groupby('cbo_4d').agg(
    exposure=('exposure_score', 'first'),
    admissoes_total=('admissoes', 'sum'),
).nlargest(10, 'exposure')
for cbo, row in top10.iterrows():
    nome = GRANDES_GRUPOS_CBO.get(cbo[0], '')
    print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}  ({nome})")

# 2. Bottom 10 ocupações menos expostas
print(f"\n--- 10 ocupações MENOS expostas ---")
bot10 = painel.groupby('cbo_4d').agg(
    exposure=('exposure_score', 'first'),
    admissoes_total=('admissoes', 'sum'),
).nsmallest(10, 'exposure')
for cbo, row in bot10.iterrows():
    nome = GRANDES_GRUPOS_CBO.get(cbo[0], '')
    print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}  ({nome})")

# 3. Distribuição por quintil
print(f"\n--- Estatísticas por quintil de exposição ---")
for q in ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']:
    sub = painel[painel['quintil_exp'] == q]
    if len(sub) > 0:
        print(f"  {q}: n={len(sub):,}, "
              f"exposure={sub['exposure_score'].mean():.3f}, "
              f"adm_mean={sub['admissoes'].mean():.0f}, "
              f"sal_medio={sub['salario_medio_adm'].mean():,.0f}")

# 4. Concordância
concordancia = (painel['alta_exp'] == painel['alta_exp_4d']).mean()
print(f"\n--- Concordância 2d vs 4d: {concordancia:.1%} ---")

print(f"\n{'=' * 60}")
print(f"CHECKPOINT CONCLUÍDO")
print(f"{'=' * 60}")
```

    ============================================================
    CHECKPOINT — Definição de Tratamento
    ============================================================

    --- Top 10 ocupações MAIS expostas ---
      CBO 4101: score=0.632, admissões=343,660  (Trabalhadores de serv. admin.)
      CBO 4102: score=0.632, admissões=109,397  (Trabalhadores de serv. admin.)
      CBO 4110: score=0.632, admissões=7,169,112  (Trabalhadores de serv. admin.)
      CBO 4121: score=0.632, admissões=36,099  (Trabalhadores de serv. admin.)
      CBO 4122: score=0.632, admissões=217,727  (Trabalhadores de serv. admin.)
      CBO 4131: score=0.632, admissões=521,115  (Trabalhadores de serv. admin.)
      CBO 4132: score=0.632, admissões=178,605  (Trabalhadores de serv. admin.)
      CBO 4141: score=0.632, admissões=4,019,302  (Trabalhadores de serv. admin.)
      CBO 4142: score=0.632, admissões=406,552  (Trabalhadores de serv. admin.)
      CBO 4151: score=0.632, admissões=36,816  (Trabalhadores de serv. admin.)

    --- 10 ocupações MENOS expostas ---
      CBO 9101: score=0.117, admissões=44,866  (Manutenção e reparação)
      CBO 9102: score=0.117, admissões=13,108  (Manutenção e reparação)
      CBO 9109: score=0.117, admissões=1,394  (Manutenção e reparação)
      CBO 9111: score=0.117, admissões=38,881  (Manutenção e reparação)
      CBO 9112: score=0.117, admissões=83,226  (Manutenção e reparação)
      CBO 9113: score=0.117, admissões=489,020  (Manutenção e reparação)
      CBO 9131: score=0.117, admissões=85,145  (Manutenção e reparação)
      CBO 9141: score=0.117, admissões=9,542  (Manutenção e reparação)
      CBO 9142: score=0.117, admissões=1,889  (Manutenção e reparação)
      CBO 9143: score=0.117, admissões=7,158  (Manutenção e reparação)

    --- Estatísticas por quintil de exposição ---
      Q1 (Baixa): n=6,598, exposure=0.144, adm_mean=3200, sal_medio=4,469
      Q2: n=6,597, exposure=0.180, adm_mean=2207, sal_medio=2,599
      Q3: n=6,598, exposure=0.252, adm_mean=3676, sal_medio=7,018
      Q4: n=6,597, exposure=0.348, adm_mean=2735, sal_medio=8,072
      Q5 (Alta): n=6,598, exposure=0.466, adm_mean=3950, sal_medio=8,497

    --- Concordância 2d vs 4d: 93.1% ---

    ============================================================
    CHECKPOINT CONCLUÍDO
    ============================================================

### 6a. Enriquecimento do painel (variáveis adicionais)

Adicionar variáveis de controle e contexto temporal ao painel para a
análise DiD.

| Variável | Cálculo | Uso |
|----|----|----|
| `tempo_relativo_meses` | Meses desde Dez/2022 (t=0) | Event study |
| `trend` | Tendência linear (0, 1, 2, …) | Controle de tendência |
| `mes_do_ano` | Mês do ano (1-12) | Dummies de sazonalidade |
| `salario_sm` | `salario_medio_adm / SM do ano` | Normalização salarial |
| `grande_grupo_nome` | Nome do grande grupo CBO | Efeitos fixos |

``` python
# Etapa 2a.6a — Enriquecimento do painel

def periodo_num_to_months(pn):
    """Converter periodo_num (YYYYMM) para contagem absoluta de meses."""
    return (pn // 100) * 12 + (pn % 100)

# ── Tempo relativo ao tratamento ──
ref_periodo = ANO_TRATAMENTO * 100 + MES_TRATAMENTO
painel['meses_abs'] = painel['periodo_num'].apply(periodo_num_to_months)
ref_meses = periodo_num_to_months(ref_periodo)
painel['tempo_relativo_meses'] = painel['meses_abs'] - ref_meses

print(f"Tempo relativo: [{painel['tempo_relativo_meses'].min()}, "
      f"{painel['tempo_relativo_meses'].max()}] meses")
print(f"Referência (t=0): {MES_TRATAMENTO}/{ANO_TRATAMENTO}")

# ── Tendência temporal e sazonalidade ──
painel['trend'] = painel['meses_abs'] - painel['meses_abs'].min()
painel['mes_do_ano'] = painel['mes'].astype(int)

# ── Normalização salarial ──
painel['sm_ano'] = painel['ano'].astype(int).map(SALARIO_MINIMO)
painel['salario_sm'] = painel['salario_medio_adm'] / painel['sm_ano']
painel['ln_salario_sm'] = np.log(painel['salario_sm'].clip(lower=0.1))

# ── Salário real (deflacionado pelo IPCA, base Dez/2024 = 100) ──
painel = painel.merge(df_ipca[['ano', 'mes', 'indice']], on=['ano', 'mes'], how='left')
painel['salario_real_adm'] = painel['salario_medio_adm'] * (INDICE_BASE / painel['indice'])
painel['ln_salario_real_adm'] = np.log(painel['salario_real_adm'].clip(lower=1))

# ── Grande grupo ocupacional ──
painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]
painel['grande_grupo_nome'] = painel['grande_grupo_cbo'].map(GRANDES_GRUPOS_CBO)

print(f"\nVariáveis adicionadas: tempo_relativo_meses, trend, mes_do_ano, "
      f"salario_sm, ln_salario_sm, salario_real_adm, ln_salario_real_adm, grande_grupo_nome")
print(f"Colunas totais: {painel.shape[1]}")
```

    Tempo relativo: [-23, 30] meses
    Referência (t=0): 12/2022

    Variáveis adicionadas: tempo_relativo_meses, trend, mes_do_ano, salario_sm, ln_salario_sm, salario_real_adm, ln_salario_real_adm, grande_grupo_nome
    Colunas totais: 74

### Anexo 1: Integração Anthropic (Automation vs Augmentation)

Integração do **Anthropic Economic Index** (Brynjolfsson et al., 2025 —
“Canaries in the Coal Mine”) para diferenciar ocupações onde a IA atua
como **Automação** (substitui trabalho) vs **Augmentação**
(complementa). O índice é construído a partir dos modos de colaboração
(directive, feedback loop = automação; learning, task iteration,
validation = augmentação) e mapeado para CBO 4d via SOC → ISCO-08 → COD,
com imputação hierárquica para cobertura total.

**Arquivos necessários em `data/input` (copiar das pastas do repositório
se não existirem):**

| Arquivo | Origem no repositório |
|----|----|
| `aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv` | `EconomicIndex/release_2026_01_15/data/intermediate/` ou `etapa2_anthropic_index/` |
| `onet_task_statements.csv` | `EconomicIndex/release_2025_09_15/data/intermediate/` |
| `Crosswalk SOC 2010 a 2018.xlsx` | `etapa3_crosswalk_onet_isco08/data_input/` |
| `Crosswalk SOC 2010 ISCO-08.xls` | `etapa3_crosswalk_onet_isco08/data_input/` |
| `Estrutura Ocupação COD.xls` | `etapa1_ia_generativa/data/raw/` ou `etapa3_crosswalk_onet_isco08/data_input/` |

Se `anthropic_automation_augmentation_cbo.parquet` existir em
`data/processed` e `KEEP_ANTHROPIC_INDEX = True`, o processamento pesado
é pulado e o cache é carregado.

``` python
# Anexo 1 — Copiar inputs para data/input (se ainda não estiverem) para notebook autocontido
import shutil
# Raiz do projeto: se estamos em notebook/, sobe um nível
_cwd = Path(".").resolve()
REPO_ROOT = _cwd.parent if (_cwd / "etapa3_crosswalk_onet_isco08").exists() == False else _cwd
origins = [
    (REPO_ROOT / "EconomicIndex" / "release_2026_01_15" / "data" / "intermediate" / "aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv", DATA_INPUT / "aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv"),
    (REPO_ROOT / "EconomicIndex" / "release_2025_09_15" / "data" / "intermediate" / "onet_task_statements.csv", DATA_INPUT / "onet_task_statements.csv"),
    (REPO_ROOT / "etapa3_crosswalk_onet_isco08" / "data_input" / "Crosswalk SOC 2010 a 2018.xlsx", DATA_INPUT / "Crosswalk SOC 2010 a 2018.xlsx"),
    (REPO_ROOT / "etapa3_crosswalk_onet_isco08" / "data_input" / "Crosswalk SOC 2010 ISCO-08.xls", DATA_INPUT / "Crosswalk SOC 2010 ISCO-08.xls"),
    (REPO_ROOT / "etapa1_ia_generativa" / "data" / "raw" / "Estrutura Ocupação COD.xls", DATA_INPUT / "Estrutura Ocupação COD.xls"),
]
for src, dst in origins:
    if src.exists() and (not dst.exists() or dst.stat().st_size == 0):
        shutil.copy2(src, dst)
        print(f"Copiado: {dst.name}")
    elif not src.exists() and dst.exists():
        print(f"Já em data/input: {dst.name}")
    elif not src.exists():
        print(f"AVISO: não encontrado no repo: {src.relative_to(REPO_ROOT) if src.is_relative_to(REPO_ROOT) else src}")
print("Inputs em data/input conferidos.")
```

    Copiado: aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv
    Copiado: onet_task_statements.csv
    Copiado: Crosswalk SOC 2010 a 2018.xlsx
    Copiado: Crosswalk SOC 2010 ISCO-08.xls
    Inputs em data/input conferidos.

``` python
# Anexo 1 — Carregar cache ou rodar pipeline Anthropic (Automation vs Augmentation)
def _weighted_mean(values, weights):
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0: return np.nan
    v, w = values[mask], weights[mask]
    return np.average(v, weights=w) if w.sum() > 0 else v.mean()

def _calculate_indices(df_task):
    required_modes = ["directive", "feedback loop", "learning", "task iteration", "validation"]
    for m in required_modes:
        if m not in df_task.columns: df_task[m] = 0
    df_task["total_collab"] = df_task[required_modes].sum(axis=1)
    mask = df_task["total_collab"] > 0
    df_task.loc[mask, "automation_share"] = (df_task.loc[mask, "directive"] + df_task.loc[mask, "feedback loop"]) / df_task.loc[mask, "total_collab"]
    df_task.loc[mask, "augmentation_share"] = (df_task.loc[mask, "learning"] + df_task.loc[mask, "task iteration"] + df_task.loc[mask, "validation"]) / df_task.loc[mask, "total_collab"]
    df_task["automation_share"] = df_task["automation_share"].fillna(0)
    df_task["augmentation_share"] = df_task["augmentation_share"].fillna(0)
    df_task["automation_index"] = df_task["automation_share"] - df_task["augmentation_share"]
    df_task["dominant_mode"] = np.where(df_task["automation_index"] > 0, "automation", "augmentation")
    return df_task

df_anthropic_cbo = None
if KEEP_ANTHROPIC_INDEX and ANTHROPIC_INDEX_CACHE.exists():
    df_anthropic_cbo = pd.read_parquet(ANTHROPIC_INDEX_CACHE)
    print(f"Índice Anthropic carregado do cache: {ANTHROPIC_INDEX_CACHE.name} ({len(df_anthropic_cbo)} ocupações CBO 4d)")
else:
    # Pipeline completo
    AEI_RAW = DATA_INPUT / "aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv"
    ONET_TASKS = DATA_INPUT / "onet_task_statements.csv"
    CROSSWALK_10_18 = DATA_INPUT / "Crosswalk SOC 2010 a 2018.xlsx"
    CROSSWALK_ISCO = DATA_INPUT / "Crosswalk SOC 2010 ISCO-08.xls"
    ESTRUTURA_COD = DATA_INPUT / "Estrutura Ocupação COD.xls"
    if not AEI_RAW.exists() or not ONET_TASKS.exists():
        raise FileNotFoundError("Coloque aei_raw_claude_ai_*.csv e onet_task_statements.csv em data/input. Veja Anexo 1.")
    # 1) Carregar Anthropic + O*NET
    df_raw = pd.read_csv(AEI_RAW)
    mask = (df_raw["facet"] == "onet_task::collaboration") & (df_raw["geo_id"] == "GLOBAL")
    df_collab = df_raw[mask].copy()
    df_collab[["task_desc", "mode"]] = df_collab["cluster_name"].str.rsplit("::", n=1, expand=True)
    df_collab["task_desc_clean"] = df_collab["task_desc"].str.strip().str.lower().str.rstrip(".")
    df_pivot = df_collab.pivot_table(index="task_desc_clean", columns="mode", values="value", aggfunc="first").reset_index()
    df_onet = pd.read_csv(ONET_TASKS)
    df_onet["task_desc_clean"] = df_onet["Task"].str.strip().str.lower().str.rstrip(".")
    task_mapping = df_onet[["task_desc_clean", "O*NET-SOC Code"]].drop_duplicates()
    task_mapping.columns = ["task_desc_clean", "onet_soc_code"]
    df_pivot = df_pivot.merge(task_mapping, on="task_desc_clean", how="inner")
    mask_count = (df_raw["facet"] == "onet_task") & (df_raw["variable"] == "onet_task_count") & (df_raw["geo_id"] == "GLOBAL")
    df_counts = df_raw[mask_count][["cluster_name", "value"]].rename(columns={"cluster_name": "task_desc", "value": "usage_volume"})
    df_counts["task_desc_clean"] = df_counts["task_desc"].str.strip().str.lower().str.rstrip(".")
    df_counts = df_counts.groupby("task_desc_clean")["usage_volume"].sum().reset_index()
    df_task = df_pivot.merge(df_counts, on="task_desc_clean", how="inner")
    df_task = _calculate_indices(df_task)
    df_onet["soc_6d"] = df_onet["O*NET-SOC Code"].str.split(".").str[0]
    soc_mapping = df_onet[["O*NET-SOC Code", "soc_6d", "Title"]].drop_duplicates()
    soc_mapping.columns = ["onet_soc_code", "soc_6d", "occupation_title"]
    df_merged = df_task.merge(soc_mapping, on="onet_soc_code", how="inner")
    def agg_wm(x): return _weighted_mean(x, df_merged.loc[x.index, "usage_volume"])
    df_soc = df_merged.groupby(["soc_6d", "occupation_title"]).agg(
        automation_share=("automation_share", agg_wm), augmentation_share=("augmentation_share", agg_wm), usage_volume=("usage_volume", "sum")
    ).reset_index()
    df_soc["automation_index_cai"] = df_soc["automation_share"] - df_soc["augmentation_share"]
    df_soc["automation_share_cai"] = df_soc["automation_share"]
    df_soc["augmentation_share_cai"] = df_soc["augmentation_share"]
    df_soc.to_csv(DATA_PROCESSED / "onet_automation_augmentation_index.csv", index=False)
    # 2) Crosswalk SOC -> ISCO-08 (fallback SOC 2018 -> 2010 -> ISCO)
    df_10_18 = pd.read_excel(CROSSWALK_10_18, skiprows=7).iloc[:, :4]
    df_10_18.columns = ["soc_2010_code", "soc_2010_title", "soc_2018_code", "soc_2018_title"]
    df_10_18["soc_2018_code"] = df_10_18["soc_2018_code"].astype(str).str.replace(".00", "", regex=False).str.strip()
    df_10_18 = df_10_18.dropna(subset=["soc_2010_code", "soc_2018_code"])
    df_soc_isco = pd.read_excel(CROSSWALK_ISCO, sheet_name="2010 SOC to ISCO-08", skiprows=7)
    df_soc_isco.columns = ["soc_2010_code", "soc_2010_title", "part", "isco_08_code", "isco_08_title", "comment"]
    df_soc_isco = df_soc_isco.dropna(subset=["soc_2010_code", "isco_08_code"])
    df_soc_isco["isco_08_code"] = df_soc_isco["isco_08_code"].astype(str).str.replace(".0", "", regex=False).str.zfill(4)
    df_merged = df_soc.merge(df_10_18, left_on="soc_6d", right_on="soc_2018_code", how="inner").merge(df_soc_isco, on="soc_2010_code", how="inner")
    def agg_isco(x): return _weighted_mean(x, df_merged.loc[x.index, "usage_volume"])
    df_isco = df_merged.groupby("isco_08_code").agg(
        automation_share_cai=("automation_share_cai", agg_isco), augmentation_share_cai=("augmentation_share_cai", agg_isco),
        automation_index_cai=("automation_index_cai", agg_isco), usage_volume=("usage_volume", "sum")
    ).reset_index()
    df_isco["dominant_mode_cai"] = np.where(df_isco["automation_index_cai"] > 0, "automation", "augmentation")
    df_isco.to_csv(DATA_PROCESSED / "isco_automation_augmentation_index.csv", index=False)
```

``` python
# Anexo 1 — Continuação: ISCO -> COD, imputação hierárquica, salvar cache (só roda se pipeline foi executado)
if df_anthropic_cbo is None:
    try:
        df_esco = pd.read_csv(DATA_PROCESSED / "isco_automation_augmentation_index.csv")
    except Exception:
        raise RuntimeError("Execute a célula anterior do Anexo 1 primeiro.")
    ESTRUTURA_COD = DATA_INPUT / "Estrutura Ocupação COD.xls"
    if not ESTRUTURA_COD.exists():
        raise FileNotFoundError("Coloque Estrutura Ocupação COD.xls em data/input.")
    try:
        df_cod = pd.read_excel(ESTRUTURA_COD, sheet_name="Estrutura COD", engine="xlrd", header=1)
    except Exception:
        df_cod = pd.read_excel(ESTRUTURA_COD, sheet_name="Estrutura COD", engine="openpyxl", header=1)
    df_cod.columns = ["grande_grupo", "subgrupo_principal", "subgrupo", "grupo_base", "denominacao"]
    df_gb = df_cod.dropna(subset=["grupo_base"])[["grupo_base", "denominacao"]].copy()
    df_gb["cod_cod"] = df_gb["grupo_base"].astype(str).str.replace(".0", "", regex=False).str.zfill(4)
    df_esco["isco_08_code"] = df_esco["isco_08_code"].astype(str).str.zfill(4)
    df_cod_merge = df_gb[["cod_cod", "denominacao"]].merge(df_esco, left_on="cod_cod", right_on="isco_08_code", how="left")
    metrics_cols = ["automation_share_cai", "augmentation_share_cai", "automation_index_cai"]
    df_cod_merge["imputation_method"] = np.where(df_cod_merge["automation_index_cai"].notna(), "direct_match", "missing")
    df_isco = df_esco.copy()
    df_isco["isco_3d"] = df_isco["isco_08_code"].astype(str).str[:3]
    df_isco["isco_2d"] = df_isco["isco_08_code"].astype(str).str[:2]
    if "usage_volume" not in df_isco.columns: df_isco["usage_volume"] = 1.0
    avg_3d = df_isco.groupby("isco_3d").apply(lambda g: pd.Series({c: _weighted_mean(g[c], g["usage_volume"]) for c in metrics_cols if c in g.columns})).reset_index()
    avg_2d = df_isco.groupby("isco_2d").apply(lambda g: pd.Series({c: _weighted_mean(g[c], g["usage_volume"]) for c in metrics_cols if c in g.columns})).reset_index()
    df_cod_merge["cod_3d"] = df_cod_merge["cod_cod"].astype(str).str[:3]
    df_cod_merge["cod_2d"] = df_cod_merge["cod_cod"].astype(str).str[:2]
    mask_miss = df_cod_merge["automation_index_cai"].isna()
    for idx in df_cod_merge[mask_miss].index:
        c3 = df_cod_merge.loc[idx, "cod_3d"]
        row3 = avg_3d[avg_3d["isco_3d"] == c3]
        if len(row3) > 0:
            for c in metrics_cols:
                if c in row3.columns: df_cod_merge.loc[idx, c] = row3[c].iloc[0]
            df_cod_merge.loc[idx, "imputation_method"] = "hierarchical_3d_mean"
    mask_miss = df_cod_merge["automation_index_cai"].isna()
    for idx in df_cod_merge[mask_miss].index:
        c2 = df_cod_merge.loc[idx, "cod_2d"]
        row2 = avg_2d[avg_2d["isco_2d"] == c2]
        if len(row2) > 0:
            for c in metrics_cols:
                if c in row2.columns: df_cod_merge.loc[idx, c] = row2[c].iloc[0]
            df_cod_merge.loc[idx, "imputation_method"] = "hierarchical_2d_mean"
    mask_still = df_cod_merge["automation_index_cai"].isna()
    df_cod_merge.loc[mask_still, metrics_cols] = 0.0
    df_cod_merge.loc[mask_still, "imputation_method"] = "zero_imputation_no_data"
    df_cod_merge["dominant_mode_cai"] = np.where(df_cod_merge["automation_index_cai"] > 0, "automation", "augmentation")
    df_cod_merge.to_csv(DATA_PROCESSED / "cod_automation_augmentation_index_final.csv", index=False)
    df_anthropic_cbo = df_cod_merge[["cod_cod", "automation_share_cai", "augmentation_share_cai", "automation_index_cai", "dominant_mode_cai", "imputation_method"]].copy()
    df_anthropic_cbo = df_anthropic_cbo.rename(columns={"cod_cod": "cbo_4d", "automation_index_cai": "anthropic_automation_index"})
    df_anthropic_cbo["cbo_4d"] = df_anthropic_cbo["cbo_4d"].astype(str).str.zfill(4)
    df_anthropic_cbo.to_parquet(ANTHROPIC_INDEX_CACHE, index=False)
    print(f"Pipeline Anthropic concluído. Cache salvo: {ANTHROPIC_INDEX_CACHE}. Ocupações: {len(df_anthropic_cbo)}.")
```

    Pipeline Anthropic concluído. Cache salvo: data/processed/anthropic_automation_augmentation_cbo.parquet. Ocupações: 435.

``` python
# Anexo 1 — Merge do índice Anthropic ao painel e criação das dummies (automation vs augmentation)
# Garantir formato cbo_4d string 4 dígitos para o merge
_cbo = painel["cbo_4d"].astype(str).str.zfill(4)
df_anthropic_cbo["cbo_4d"] = df_anthropic_cbo["cbo_4d"].astype(str).str.zfill(4)
cols_merge = [c for c in ["anthropic_automation_index", "automation_share_cai", "augmentation_share_cai", "dominant_mode_cai"] if c in df_anthropic_cbo.columns]
idx_cbo = df_anthropic_cbo.set_index("cbo_4d")[cols_merge]
painel = painel.copy()
for c in cols_merge:
    painel[c] = _cbo.map(idx_cbo[c] if c in idx_cbo.columns else idx_cbo.squeeze()).values
# Score contínuo: preencher NaN com 0 (imputação hierárquica já cobriu todas as CBOs no índice)
painel["anthropic_automation_index"] = painel["anthropic_automation_index"].fillna(0.0)
# Dummies: Automação = 1 quando automation > augmentation (índice > 0); Augmentação = 1 quando augmentation > automation
painel["is_automation"] = (painel["anthropic_automation_index"] > 0).astype(int)
painel["is_augmentation"] = (painel["anthropic_automation_index"] <= 0).astype(int)
print(f"Anexo 1 — Merge concluído. anthropic_automation_index: cobertura {painel['anthropic_automation_index'].notna().mean():.1%}. "
      f"is_automation={painel['is_automation'].mean():.1%}, is_augmentation={painel['is_augmentation'].mean():.1%}")
```

    Anexo 1 — Merge concluído. anthropic_automation_index: cobertura 100.0%. is_automation=5.4%, is_augmentation=94.6%

### 7. Salvar dataset analítico final

Selecionar colunas finais, remover ocupações sem score de exposição e
salvar o dataset pronto para a análise DiD (Notebook 2b).

**Saída:** - `data/output/painel_caged_did_ready.parquet` — formato
eficiente para análise - `data/output/painel_caged_did_ready.csv` —
backup legível

``` python
# Etapa 2a.7 — Salvar dataset analítico final

if not KEEP_PANEL_FINAL:
    if PAINEL_FINAL_PARQUET.exists():
        PAINEL_FINAL_PARQUET.unlink()
        print(f"Cache removido: {PAINEL_FINAL_PARQUET.name}")
    if PAINEL_FINAL_CSV.exists():
        PAINEL_FINAL_CSV.unlink()
        print(f"Cache removido: {PAINEL_FINAL_CSV.name}")

# ── Selecionar colunas finais ──
cols_finais = [
    # Identificação
    'cbo_4d', 'cbo_2d', 'ano', 'mes', 'periodo', 'periodo_num',
    # Outcomes
    'admissoes', 'desligamentos', 'saldo', 'n_movimentacoes',
    'ln_admissoes', 'ln_desligamentos',
    'salario_medio_adm', 'salario_mediano_adm', 'salario_medio_desl',
    'ln_salario_adm', 'salario_sm', 'ln_salario_sm',
    'salario_real_adm', 'ln_salario_real_adm',
    # Demografia das admissões (proporções)
    'idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm', 'pct_branco_adm', 'pct_negro_adm', 'pct_jovem_adm',
    'pct_tecnologico_adm', 'setor_tecnologico',
    # Heterogeneidade: salários (log)
    'ln_salario_homem', 'ln_salario_mulher', 'ln_salario_jovem', 'ln_salario_naojovem',
    'ln_salario_branco', 'ln_salario_negro', 'ln_salario_superior', 'ln_salario_medio',
    # Heterogeneidade: volumes (log)
    'ln_admissoes_homem', 'ln_admissoes_mulher', 'ln_admissoes_jovem', 'ln_admissoes_negro',
    # Exposição IA — DUAL
    'exposure_score_2d',   # PRINCIPAL
    'exposure_score_4d',   # ROBUSTEZ
    # Tratamento — DUAL
    'alta_exp',            # Top 20% score 2d (PRINCIPAL)
    'alta_exp_10', 'alta_exp_25', 'alta_exp_mediana', 'quintil_exp',
    'alta_exp_4d',         # Top 20% score 4d (ROBUSTEZ)
    # Temporal
    'post', 'did', 'did_4d', 'tempo_relativo_meses', 'trend', 'mes_do_ano',
    # Classificação
    'grande_grupo_cbo', 'grande_grupo_nome',
    # Anthropic (Automation vs Augmentation) — Anexo 1
    'anthropic_automation_index', 'is_automation', 'is_augmentation',
]

cols_existentes = [c for c in cols_finais if c in painel.columns]
cols_faltantes = [c for c in cols_finais if c not in painel.columns]
if cols_faltantes:
    print(f"AVISO: Colunas não encontradas: {cols_faltantes}")

painel_final = painel[cols_existentes].copy()

# ── Remover ocupações sem score principal (2d) ──
n_antes = len(painel_final)
painel_final = painel_final[painel_final['exposure_score_2d'].notna()]
n_depois = len(painel_final)
if n_antes > n_depois:
    print(f"Removidas {n_antes - n_depois:,} linhas sem exposure_score_2d")

# ── Verificação para o Notebook 2b ──
cols_obrigatorias = ['exposure_score_2d', 'exposure_score_4d', 'alta_exp', 'did', 'tempo_relativo_meses', 'post']
for c in cols_obrigatorias:
    if c not in painel_final.columns:
        raise ValueError(f"Coluna obrigatória ausente para o DiD (Notebook 2b): {c}")
if painel_final[cols_obrigatorias].isna().any().any():
    raise ValueError("NA em coluna obrigatória para o DiD (Notebook 2b).")
print("  Verificação: colunas obrigatórias para o 2b presentes e sem NA.")

# ── Salvar ──
painel_final.to_parquet(PAINEL_FINAL_PARQUET, index=False)
painel_final.to_csv(PAINEL_FINAL_CSV, index=False)

# ══════════════════════════════════════════════════════════════════════
# RESUMO FINAL
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'=' * 60}")
print("DATASET ANALÍTICO FINAL — ETAPA 2a")
print(f"{'=' * 60}")
print(f"  Observações:        {len(painel_final):,}")
print(f"  Ocupações (CBO 4d): {painel_final['cbo_4d'].nunique()}")
print(f"  Períodos:           {painel_final['periodo'].nunique()} meses")
print(f"    Pré-tratamento:   {painel_final[painel_final['post']==0]['periodo'].nunique()}")
print(f"    Pós-tratamento:   {painel_final[painel_final['post']==1]['periodo'].nunique()}")
print(f"  Cobertura 2d:       {painel_final['exposure_score_2d'].notna().mean():.1%}")
print(f"  Cobertura 4d:       {painel_final['exposure_score_4d'].notna().mean():.1%}")
print(f"  Tratamento 2d:      {painel_final['alta_exp'].mean():.1%} das obs")
print(f"  Tratamento 4d:      {painel_final['alta_exp_4d'].mean():.1%} das obs")
print(f"  Colunas:            {painel_final.shape[1]}")
print(f"\n  Salvo em:")
print(f"    {PAINEL_FINAL_PARQUET}")
print(f"    {PAINEL_FINAL_CSV}")
pq_mb = PAINEL_FINAL_PARQUET.stat().st_size / 1e6
csv_mb = PAINEL_FINAL_CSV.stat().st_size / 1e6
print(f"    Tamanho: {pq_mb:.1f} MB (parquet), {csv_mb:.1f} MB (csv)")

print(f"\n  Info:")
painel_final.info()
```

    Cache removido: painel_caged_did_ready.parquet
    Cache removido: painel_caged_did_ready.csv
      Verificação: colunas obrigatórias para o 2b presentes e sem NA.

    ============================================================
    DATASET ANALÍTICO FINAL — ETAPA 2a
    ============================================================
      Observações:        32,988
      Ocupações (CBO 4d): 629
      Períodos:           54 meses
        Pré-tratamento:   23
        Pós-tratamento:   31
      Cobertura 2d:       100.0%
      Cobertura 4d:       100.0%
      Tratamento 2d:      20.3% das obs
      Tratamento 4d:      21.3% das obs
      Colunas:            59

      Salvo em:
        data/output/painel_caged_did_ready.parquet
        data/output/painel_caged_did_ready.csv
        Tamanho: 7.2 MB (parquet), 21.0 MB (csv)

      Info:
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 32988 entries, 0 to 32987
    Data columns (total 59 columns):
     #   Column                      Non-Null Count  Dtype   
    ---  ------                      --------------  -----   
     0   cbo_4d                      32988 non-null  object  
     1   cbo_2d                      32988 non-null  object  
     2   ano                         32988 non-null  Int64   
     3   mes                         32988 non-null  Int64   
     4   periodo                     32988 non-null  object  
     5   periodo_num                 32988 non-null  int64   
     6   admissoes                   32988 non-null  Int64   
     7   desligamentos               32988 non-null  Int64   
     8   saldo                       32988 non-null  Int64   
     9   n_movimentacoes             32988 non-null  Int64   
     10  ln_admissoes                32988 non-null  Float64 
     11  ln_desligamentos            32988 non-null  Float64 
     12  salario_medio_adm           32988 non-null  float64 
     13  salario_mediano_adm         32988 non-null  float64 
     14  salario_medio_desl          32988 non-null  float64 
     15  ln_salario_adm              32988 non-null  float64 
     16  salario_sm                  32988 non-null  float64 
     17  ln_salario_sm               32988 non-null  float64 
     18  salario_real_adm            32988 non-null  float64 
     19  ln_salario_real_adm         32988 non-null  float64 
     20  idade_media_adm             32988 non-null  Float64 
     21  pct_mulher_adm              32988 non-null  float64 
     22  pct_superior_adm            32988 non-null  float64 
     23  pct_branco_adm              32988 non-null  float64 
     24  pct_negro_adm               32988 non-null  float64 
     25  pct_jovem_adm               32988 non-null  float64 
     26  pct_tecnologico_adm         32988 non-null  float64 
     27  setor_tecnologico           32988 non-null  int64   
     28  ln_salario_homem            32988 non-null  float64 
     29  ln_salario_mulher           32988 non-null  float64 
     30  ln_salario_jovem            32988 non-null  float64 
     31  ln_salario_naojovem         32988 non-null  float64 
     32  ln_salario_branco           32988 non-null  float64 
     33  ln_salario_negro            32988 non-null  float64 
     34  ln_salario_superior         32988 non-null  float64 
     35  ln_salario_medio            32988 non-null  float64 
     36  ln_admissoes_homem          32988 non-null  float64 
     37  ln_admissoes_mulher         32988 non-null  float64 
     38  ln_admissoes_jovem          32988 non-null  float64 
     39  ln_admissoes_negro          32988 non-null  float64 
     40  exposure_score_2d           32988 non-null  float64 
     41  exposure_score_4d           32988 non-null  float64 
     42  alta_exp                    32988 non-null  int64   
     43  alta_exp_10                 32988 non-null  int64   
     44  alta_exp_25                 32988 non-null  int64   
     45  alta_exp_mediana            32988 non-null  int64   
     46  quintil_exp                 32988 non-null  category
     47  alta_exp_4d                 32988 non-null  int64   
     48  post                        32988 non-null  int64   
     49  did                         32988 non-null  int64   
     50  did_4d                      32988 non-null  int64   
     51  tempo_relativo_meses        32988 non-null  int64   
     52  trend                       32988 non-null  int64   
     53  mes_do_ano                  32988 non-null  int64   
     54  grande_grupo_cbo            32988 non-null  object  
     55  grande_grupo_nome           32988 non-null  object  
     56  anthropic_automation_index  32988 non-null  float64 
     57  is_automation               32988 non-null  int64   
     58  is_augmentation             32988 non-null  int64   
    dtypes: Float64(3), Int64(6), category(1), float64(29), int64(15), object(5)
    memory usage: 14.9+ MB

### Limitações desta etapa

1.  **Novo CAGED (descontinuidade 2020):** A transição para o
    eSocial (2020) pode afetar a comparabilidade. Mitigamos ao iniciar
    em 2021 (eSocial já estabilizado, sem efeitos COVID).

2.  **Fluxos vs. estoques:** O CAGED mede movimentações
    (admissões/desligamentos), não o estoque de empregados. Quedas em
    admissões não significam necessariamente queda no emprego total —
    podem refletir menor rotatividade. Esta é a mesma lógica usada por
    Hui et al. (2024) com dados do Upwork.

3.  **Crosswalk CBO → ISCO-08 (especificação principal, 2 dígitos):** Ao
    agregar por Sub-major Group com fallback a Major Group, perdemos
    variação intragrupo. Ocupações diferentes dentro do mesmo grupo
    recebem o mesmo score. A especificação de robustez a 4 dígitos (com
    fallback hierárquico em 6 níveis) ajuda a avaliar se essa agregação
    afeta os resultados.

4.  **Crosswalk CBO → ISCO-08 (robustez, 4 dígitos):** O match direto
    CBO 4d = ISCO-08 4d cobre apenas ~28% das ocupações. Para o
    restante, usamos fallback hierárquico (via correspondência
    ISCO-88→ISCO-08, médias a 3d, 2d e 1d). Quanto mais granular o
    match, mais preciso o score — mas mesmo com fallback, a correlação
    entre as especificações 2d e 4d é \>0.91, indicando consistência.
    Erro de medição no tratamento tipicamente atenua os coeficientes
    (viés em direção a zero).

5.  **Muendler: CBO 1994, não CBO 2002:** O arquivo de concordância
    Muendler & Poole (2004) mapeia a CBO *1994* (formato X-XX.XX), não a
    CBO 2002 (XXXX) usada no CAGED. A utilidade do Muendler para match
    4d direto é limitada. A estratégia adotada usa a similaridade
    estrutural entre CBO 2002 e ISCO-08/88 (ambas baseadas na ISCO),
    combinada com a tabela oficial de correspondência ISCO-08↔ISCO-88.

6.  **Emprego formal apenas:** O CAGED cobre apenas o mercado formal
    (CLT). A informalidade (~40% da força de trabalho brasileira) não é
    capturada. Efeitos da IA sobre o setor informal requerem fontes
    alternativas (PNAD).

7.  **Índice global aplicado ao Brasil:** Mesma limitação da Etapa 1 — o
    índice ILO foi desenvolvido com foco global e pode não capturar
    especificidades do mercado de trabalho brasileiro.

------------------------------------------------------------------------

### Checklist de entregáveis

- [x] `data/raw/caged_{ano}.parquet` — Microdados CAGED por ano
  (2021–2025)
- [x] `data/input/cbo-isco-conc.csv` — Concordância Muendler CBO
  1994→ISCO-88
- [x] `data/input/Correspondência ISCO 08 a 88.xlsx` — Tabela oficial
  ISCO-08↔ISCO-88
- [x] `data/processed/ilo_exposure_clean.csv` — Índice ILO processado
  (reusado da Etapa 1)
- [x] `data/output/painel_caged_did_ready.parquet` — Dataset analítico
  final (com scores 2d e 4d)
- [x] `data/output/painel_caged_did_ready.csv` — Backup CSV
- [x] Todos os CHECKPOINTs passando sem warnings críticos
- [x] Cobertura crosswalk 2d = 100%
- [x] Cobertura crosswalk 4d = 100% (com fallback hierárquico)
- [x] Correlação entre scores 2d e 4d: 0.9147
- [x] Sanity check por grande grupo coerente com a literatura

---

<!-- fonte: etapa_2b_analise_did_caged_ilo.ipynb -->

# ETAPA 2b — Análise Difference-in-Differences: IA Generativa e Emprego
Formal no Brasil


**Dissertação:** Inteligência Artificial Generativa e o Mercado de
Trabalho Brasileiro: Uma Análise de Exposição Ocupacional e seus Efeitos
Distributivos.

**Aluno:** Manoel Brasil Orlandi

**Objetivo deste notebook:** Estimar o efeito causal do lançamento da IA
generativa (ChatGPT, novembro/2022) sobre o mercado de trabalho formal
brasileiro, usando variação na exposição ocupacional à IA como fonte de
identificação. Implementa um design Difference-in-Differences (DiD) com
dados do CAGED (2021–2025) e o índice de exposição da OIT.

**Pergunta de pesquisa:** Após o lançamento do ChatGPT, ocupações mais
expostas à IA generativa tiveram mudanças diferenciais em contratações,
demissões ou salários de admissão, em comparação com ocupações menos
expostas?

**Input:** `data/output/painel_caged_did_ready.parquet` (produzido no
Notebook 2a).

**Estratégia de crosswalk:** Análise principal a 2 dígitos ISCO-08
(match por Sub-major Group com fallback a Major Group), com robustez a 4
dígitos via correspondência ISCO-88↔ISCO-08 e fallback hierárquico em 6
níveis.

**Referências metodológicas:** Hui, Reshef & Zhou (2024), *The
Short-Term Effects of Generative AI on Employment*; Cunningham (2021),
*Causal Inference: The Mixtape*, Cap. 9; Callaway & Sant’Anna (2021),
*DiD with multiple time periods*; Gmyrek, Berg & Cappelli (2025), ILO
Working Paper 140.

### Estratégia de identificação

| Elemento | Definição |
|----|----|
| **Unidade de análise** | Ocupação CBO × mês (2 dígitos na espec. principal; 4 dígitos na robustez) |
| **Tratamento** | Ocupações com alta exposição à IA (top 20% do índice ILO via `exposure_score_2d`) |
| **Controle** | Ocupações com baixa exposição (bottom 80%) |
| **Evento** | Lançamento do ChatGPT (30/nov/2022) |
| **Pré-tratamento** | Jan/2021 — Nov/2022 (23 meses) |
| **Pós-tratamento** | Dez/2022 — Jun/2025 (31 meses) |
| **Outcomes** | Admissões, desligamentos, saldo, salário médio de admissão |
| **Efeitos fixos** | Ocupação (CBO 4d) + período (ano-mês) |
| **Erros padrão** | Clusterizados por ocupação (CBO 4d) |

A hipótese central é que, **na ausência do lançamento do ChatGPT**,
ocupações de alta e baixa exposição teriam seguido tendências paralelas.
Com **tratamento sharp** (todos tratados no mesmo momento), o estimador
TWFE produz estimativas consistentes do ATT médio (Cunningham, Mixtape
Cap. 9).

### Outcomes

| Outcome | Variável | Transformação | Interpretação |
|----|----|----|----|
| Contratações | `admissoes` | `ln_admissoes = log(admissoes + 1)` | Fluxo de novas contratações |
| Demissões | `desligamentos` | `ln_desligamentos = log(desligamentos + 1)` | Fluxo de demissões |
| Saldo líquido | `saldo` | Em nível | Criação líquida de empregos |
| Salário de admissão (nominal) | `salario_medio_adm` | `ln_salario_adm = log(salario_medio_adm)` | Poder de barganha / demanda |
| Salário de admissão (**real**) | `salario_real_adm` (2a) | `ln_salario_real_adm` (deflacionado IPCA) | **Análise principal** — limpa inflação |

**Nota — Winsorização:** O Notebook 2a identificou outlier salarial em
Jun/2025. Aplicamos **winsorização nos percentis 1% e 99%** de
`salario_medio_adm` e `salario_sm` neste notebook antes da estimação,
preservando todas as observações.

### 1. Configuração do ambiente

Importar bibliotecas, definir caminhos e parâmetros de estimação.
Caminhos relativos ao diretório `notebook/`.

> **Sobre os avisos de colinearidade:** O pyfixest pode exibir
> *UserWarning* quando uma variável de controle (ex.: `pct_mulher_adm`)
> é omitida por **colinearidade** com os efeitos fixos (ocupação e
> período). Isso ocorre quando a variável tem pouca ou nenhuma variação
> dentro dos grupos. Não é erro: a estimação segue válida; o controle
> simplesmente não entra na regressão. Suprimimos esses avisos para
> deixar o notebook mais legível.

``` python
# Verificar dependências e instalar apenas o que faltar (rode esta célula primeiro)
import importlib.util
import subprocess
import sys

# (nome para import, nome para pip install)
PACOTES = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("pyfixest", "pyfixest"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("scipy", "scipy"),
    ("pyarrow", "pyarrow"),
]

def ja_instalado(nome_import):
    return importlib.util.find_spec(nome_import) is not None

faltando = [pip for imp, pip in PACOTES if not ja_instalado(imp)]
if faltando:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + faltando)
    print("Instalado:", ", ".join(faltando))
else:
    print("Todas as dependências já estão instaladas.")
```

    Todas as dependências já estão instaladas.

``` python
# Etapa 2b.1 — Configuração do ambiente

import warnings
import pandas as pd
import numpy as np
import pyfixest as pf
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)
# Suprimir aviso do pyfixest quando variável é omitida por colinearidade (ex.: pct_mulher_adm)
warnings.filterwarnings("ignore", message=".*dropped due to multicollinearity.*", category=UserWarning)

DATA_OUTPUT    = Path("../../data/output")
OUTPUTS_TABLES = Path("../../outputs/tables")
OUTPUTS_FIGURES = Path("../../outputs/figures")
OUTPUTS_LOGS   = Path("../../outputs/logs")
for d in [OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

TREATMENT_VAR    = 'alta_exp'
TREATMENT_VAR_4D  = 'alta_exp_4d'
CLUSTER_VAR      = 'cbo_4d'
VCOV_SPEC        = {'CRV1': 'cbo_4d'}
REFERENCE_PERIOD  = -1
ALPHA             = 0.05
ANO_TRATAMENTO   = 2022
MES_TRATAMENTO   = 12

OUTCOMES = {
    'ln_admissoes':       'Log(Admissões)',
    'ln_desligamentos':   'Log(Desligamentos)',
    'saldo':              'Saldo Líquido',
    'ln_salario_adm':     'Log(Salário Admissão Nominal)',
    'ln_salario_real_adm':'Log(Salário Real Admissão)',
    'pct_superior_adm':   '% Superior (Admissão)',
    # Heterogeneidade demográfica (salários por grupo)
    'ln_salario_mulher':  'Log(Salário Mulheres)',
    'ln_salario_homem':   'Log(Salário Homens)',
    'ln_salario_jovem':   'Log(Salário Jovens)',
    'ln_salario_naojovem':'Log(Salário Não-Jovens)',
    'ln_salario_branco':  'Log(Salário Brancos)',
    'ln_salario_negro':   'Log(Salário Negros)',
    'ln_salario_superior':'Log(Salário Superior)',
    'ln_salario_medio':   'Log(Salário Médio)',
    'ln_admissoes_mulher':'Log(Admissões Mulheres)',
    'ln_admissoes_homem': 'Log(Admissões Homens)',
    'ln_admissoes_jovem': 'Log(Admissões Jovens)',
    'ln_admissoes_negro': 'Log(Admissões Negros)',
}
OUTCOMES_SECONDARY = {'ln_salario_sm': 'Log(Salário em SM)'}

plt.style.use('seaborn-v0_8-paper')
sns.set_palette("Set2")
plt.rcParams.update({'font.size': 11, 'axes.titlesize': 13, 'axes.labelsize': 12, 'figure.dpi': 150})
COLORS = {'pre': '#1f77b4', 'post': '#d62728', 'ci': '#cccccc', 'treated': '#ff7f0e', 'control': '#2ca02c'}

print("Configuração carregada.")
```

    Configuração carregada.

### 2. Carregar e explorar dados

Carregar o painel produzido no Notebook 2a, aplicar winsorização P1/P99
nos salários e recalcular os logs. Em seguida, exibir estatísticas
descritivas dos outcomes.

``` python
# Etapa 2b.2 — Carregar e explorar dados

painel_path = DATA_OUTPUT / "painel_caged_did_ready.parquet"
df = pd.read_parquet(painel_path)

print(f"Painel carregado: {len(df):,} observações")
print(f"Ocupações: {df['cbo_4d'].nunique()}")
print(f"Períodos: {df['periodo'].nunique()} meses")
print(f"Tratamento ({TREATMENT_VAR}): Alta exposição: {df[TREATMENT_VAR].mean():.1%}")
print(f"  Pré: {df[df['post']==0].shape[0]:,} obs | Pós: {df[df['post']==1].shape[0]:,} obs")
# Colunas Anthropic (Anexo 1 — Automation vs Augmentation)
anth_cols = ['anthropic_automation_index', 'is_automation', 'is_augmentation']
for ac in anth_cols:
    if ac in df.columns:
        print(f"  {ac}: presente")
    else:
        print(f"  AVISO: {ac} ausente (rode o Anexo 1 no Notebook 2a)")

for col_sal in ['salario_medio_adm', 'salario_sm']:
    if col_sal in df.columns:
        p1, p99 = df[col_sal].quantile(0.01), df[col_sal].quantile(0.99)
        lower = max(float(p1), 0.01) if p1 <= 0 else float(p1)
        n_clip = ((df[col_sal] < lower) | (df[col_sal] > p99)).sum()
        df[col_sal] = df[col_sal].clip(lower=lower, upper=p99)
        print(f"Winsorização {col_sal}: [{lower:.2f}, {p99:.2f}], {n_clip} obs clipped")
df['ln_salario_adm'] = np.log(df['salario_medio_adm'])
df['ln_salario_sm'] = np.log(df['salario_sm'])

print("\nEstatísticas descritivas dos outcomes:")
for var, label in {**OUTCOMES, **OUTCOMES_SECONDARY}.items():
    if var in df.columns:
        print(f"  {label}: N={df[var].notna().sum():,}, média={df[var].mean():.3f}, std={df[var].std():.3f}")
```

    Painel carregado: 32,988 observações
    Ocupações: 629
    Períodos: 54 meses
    Tratamento (alta_exp): Alta exposição: 20.3%
      Pré: 14,058 obs | Pós: 18,930 obs
      anthropic_automation_index: presente
      is_automation: presente
      is_augmentation: presente
    Winsorização salario_medio_adm: [0.01, 25908.75], 678 obs clipped
    Winsorização salario_sm: [0.01, 20.37], 678 obs clipped

    Estatísticas descritivas dos outcomes:
      Log(Admissões): N=32,988, média=5.657, std=2.291
      Log(Desligamentos): N=32,988, média=5.629, std=2.257
      Saldo Líquido: N=32,988, média=279.879, std=2322.995
      Log(Salário Admissão Nominal): N=32,988, média=7.813, std=1.426
      Log(Salário Real Admissão): N=32,988, média=7.951, std=1.049
      % Superior (Admissão): N=32,988, média=0.215, std=0.264
      Log(Salário Mulheres): N=32,988, média=7.422, std=1.880
      Log(Salário Homens): N=32,988, média=7.809, std=1.302
      Log(Salário Jovens): N=32,988, média=7.511, std=1.435
      Log(Salário Não-Jovens): N=32,988, média=7.869, std=1.299
      Log(Salário Brancos): N=32,988, média=7.795, std=1.452
      Log(Salário Negros): N=32,988, média=7.005, std=2.536
      Log(Salário Superior): N=32,988, média=7.253, std=2.604
      Log(Salário Médio): N=32,988, média=7.709, std=1.213
      Log(Admissões Mulheres): N=32,988, média=4.116, std=2.397
      Log(Admissões Homens): N=32,988, média=5.179, std=2.261
      Log(Admissões Jovens): N=32,988, média=4.746, std=2.317
      Log(Admissões Negros): N=32,988, média=3.122, std=2.088
      Log(Salário em SM): N=32,988, média=0.732, std=0.830

### 3. Tabela de balanço (pré-tratamento)

Comparar características das ocupações tratadas vs. controle no período
pré-tratamento. Critério de balanço: \|diferença normalizada\| \< 0,25
(diferença em unidades de desvio-padrão pooled). Variáveis com ⚠️
indicam desbalance. *Ref. Mixtape Cap. 9:* uma tabela de balanço compara
as características pré-tratamento dos grupos; diferenças substanciais
tornam a hipótese de tendências paralelas menos plausível.

``` python
# Etapa 2b.3 — Tabela de balanço

df_pre = df[df['post'] == 0].copy()
ocup_pre = df_pre.groupby('cbo_4d').agg(
    alta_exp=('alta_exp', 'first'),
    admissoes_media=('admissoes', 'mean'),
    desligamentos_media=('desligamentos', 'mean'),
    saldo_media=('saldo', 'mean'),
    salario_media=('salario_medio_adm', 'mean'),
    idade_media=('idade_media_adm', 'mean'),
    pct_mulher=('pct_mulher_adm', 'mean'),
    pct_superior=('pct_superior_adm', 'mean'),
    n_meses=('periodo', 'nunique'),
).reset_index()

BALANCE_THRESHOLD = 0.25
covariates = {'admissoes_media': 'Admissões (média)', 'desligamentos_media': 'Desligamentos (média)',
              'saldo_media': 'Saldo (média)', 'salario_media': 'Salário médio (R$)',
              'idade_media': 'Idade média', 'pct_mulher': '% Mulheres', 'pct_superior': '% Superior', 'n_meses': 'Meses'}
results_balance = []
for var, label in covariates.items():
    treated = ocup_pre[ocup_pre['alta_exp']==1][var].dropna()
    control = ocup_pre[ocup_pre['alta_exp']==0][var].dropna()
    mean_t, mean_c = treated.mean(), control.mean()
    pooled_std = np.sqrt((treated.var() + control.var()) / 2)
    std_diff = (mean_t - mean_c) / pooled_std if pooled_std > 0 else np.nan
    results_balance.append({'Variável': label, 'Controle': mean_c, 'Tratamento': mean_t, 'Diff. Normalizada': std_diff,
                            'Balanceado': '✓' if abs(std_diff) < BALANCE_THRESHOLD else '⚠️'})
df_balance = pd.DataFrame(results_balance)
print(df_balance.to_string(index=False))
df_balance.to_csv(OUTPUTS_TABLES / 'balance_table_pre.csv', index=False)
```

                 Variável    Controle  Tratamento  Diff. Normalizada Balanceado
        Admissões (média) 2655.337806 3409.836736           0.060150          ✓
    Desligamentos (média) 2321.326358 2916.919394           0.055214          ✓
            Saldo (média)  334.011448  492.917342           0.086523          ✓
       Salário médio (R$) 2738.765085 5388.205892           0.684567         ⚠️
              Idade média   32.752803   31.799216          -0.172254          ✓
               % Mulheres    0.278944    0.441422           0.696466         ⚠️
               % Superior    0.155741    0.418939           1.150136         ⚠️
                    Meses   22.570565   21.854962          -0.218711          ✓

### 4. Tendências paralelas (inspeção visual)

Evolução temporal das métricas de emprego para tratamento vs. controle.
A hipótese de tendências paralelas exige que ambos os grupos sigam
trajetórias semelhantes **antes** do evento (Nov/2022). A linha vertical
marca o lançamento do ChatGPT; se as curvas já divergiam antes dela, a
interpretação causal do DiD fica comprometida.

``` python
# Etapa 2b.4 — Tendências paralelas (visual)

ts_grupo = df.groupby(['periodo_num', 'alta_exp']).agg(
    admissoes_total=('admissoes', 'sum'), desligamentos_total=('desligamentos', 'sum'),
    saldo_total=('saldo', 'sum'), salario_medio=('salario_medio_adm', 'mean'),
    n_ocupacoes=('cbo_4d', 'nunique')).reset_index()
for col in ['admissoes_total', 'desligamentos_total', 'saldo_total']:
    ts_grupo[f'{col}_per_ocup'] = ts_grupo[col] / ts_grupo['n_ocupacoes']
ts_grupo['grupo'] = ts_grupo['alta_exp'].map({0: 'Controle (Baixa Exp.)', 1: 'Tratamento (Alta Exp.)'})

outcomes_plot = {'admissoes_total_per_ocup': 'Admissões médias por ocupação',
                 'desligamentos_total_per_ocup': 'Desligamentos médios por ocupação',
                 'saldo_total_per_ocup': 'Saldo médio por ocupação', 'salario_medio': 'Salário médio (R$)'}
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
evento_periodo = ANO_TRATAMENTO * 100 + MES_TRATAMENTO
for i, (var, title) in enumerate(outcomes_plot.items()):
    ax = axes.flat[i]
    for grupo in ['Controle (Baixa Exp.)', 'Tratamento (Alta Exp.)']:
        data = ts_grupo[ts_grupo['grupo']==grupo]
        color = COLORS['control'] if 'Controle' in grupo else COLORS['treated']
        ax.plot(data['periodo_num'], data[var], label=grupo, color=color, linewidth=1.5)
    ax.axvline(x=evento_periodo, color='gray', linestyle='--', alpha=0.7)
    ax.set_title(title); ax.set_xlabel('Período'); ax.legend(fontsize=8)
plt.suptitle('Tendências Paralelas: Tratamento vs. Controle', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / 'parallel_trends_all_outcomes.png', dpi=150, bbox_inches='tight')
plt.show()
```

![](etapa_2b_analise_did_caged_ilo_files/figure-commonmark/cell-6-output-1.png)

### 5a. Estimação DiD principal

Seis modelos por outcome: (1) DiD básico, (2) com FE, (3) **PRINCIPAL**
FE + controles 2d, (4) tratamento contínuo 2d, (5) robustez FE+controles
4d, (6) contínuo 4d. Erros clusterizados por ocupação (CBO 4d).

``` python
# Etapa 2b.5a — Estimação DiD principal

df_reg = df.copy()
for col in ['admissoes','desligamentos','saldo','ln_admissoes','ln_desligamentos','ln_salario_adm','ln_salario_real_adm',
            'idade_media_adm','pct_mulher_adm','pct_superior_adm','post','alta_exp','exposure_score_2d','exposure_score_4d']:
    if col in df_reg.columns: df_reg[col] = pd.to_numeric(df_reg[col], errors='coerce')
df_reg['post_alta'] = df_reg['post'] * df_reg['alta_exp']
df_reg['post_exposure_2d'] = df_reg['post'] * df_reg['exposure_score_2d']
df_reg['post_alta_4d'] = df_reg['post'] * df_reg['alta_exp_4d']
df_reg['post_exposure_4d'] = df_reg['post'] * df_reg['exposure_score_4d']

def estimate_did(df_in, outcome, formula, label):
    try:
        model = pf.feols(formula, data=df_in, vcov=VCOV_SPEC)
        names = model.coef().index.tolist()
        did_name = [c for c in names if 'post' in c.lower() and ('alta' in c.lower() or 'exposure' in c.lower())]
        if not did_name: did_name = [names[0]]
        name = did_name[0]
        coef = float(model.coef().loc[name]); se = float(model.se().loc[name]); pval = float(model.pvalue().loc[name])
        stars = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''
        return {'model': label, 'outcome': outcome, 'coef': coef, 'se': se, 'p_value': pval, 'stars': stars, 'n_obs': len(df_in), 'n_clusters': None}
    except Exception as e: print(f"  ERRO {label}/{outcome}: {e}"); return None

all_results = []
controls_base = ['idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm']
for outcome, label in OUTCOMES.items():
    if outcome not in df_reg.columns: continue
    df_out = df_reg[df_reg[outcome].notna()].copy()
    controls = [c for c in controls_base if c != outcome]
    ctrl_str = ' + '.join(controls) if controls else ''
    formula_m3 = f"{outcome} ~ post_alta + {ctrl_str} | cbo_4d + periodo" if ctrl_str else f"{outcome} ~ post_alta | cbo_4d + periodo"
    formula_m4 = f"{outcome} ~ post_exposure_2d + {ctrl_str} | cbo_4d + periodo" if ctrl_str else f"{outcome} ~ post_exposure_2d | cbo_4d + periodo"
    for r in [estimate_did(df_out, outcome, f"{outcome} ~ post_alta + post + alta_exp", "Model 1: Basic"),
               estimate_did(df_out, outcome, f"{outcome} ~ post_alta | cbo_4d + periodo", "Model 2: FE"),
               estimate_did(df_out, outcome, formula_m3, "Model 3: FE + Controls (MAIN)"),
               estimate_did(df_out, outcome, formula_m4, "Model 4: Continuous (2d)")]:
        if r: all_results.append(r)
    df_4d = df_out[df_out['exposure_score_4d'].notna()].copy()
    formula_m5 = f"{outcome} ~ post_alta_4d + {ctrl_str} | cbo_4d + periodo" if ctrl_str else f"{outcome} ~ post_alta_4d | cbo_4d + periodo"
    formula_m6 = f"{outcome} ~ post_exposure_4d + {ctrl_str} | cbo_4d + periodo" if ctrl_str else f"{outcome} ~ post_exposure_4d | cbo_4d + periodo"
    for r in [estimate_did(df_4d, outcome, formula_m5, "Model 5: FE + Controls (4d)"),
              estimate_did(df_4d, outcome, formula_m6, "Model 6: Continuous (4d)")]:
        if r: all_results.append(r)

df_results = pd.DataFrame(all_results)
df_results.to_csv(OUTPUTS_TABLES / 'did_main_results.csv', index=False)
print("Model 3 (PRINCIPAL):")
print(df_results[df_results['model']=='Model 3: FE + Controls (MAIN)'][['outcome','coef','se','p_value','stars']].to_string(index=False))
```

    Model 3 (PRINCIPAL):
                outcome       coef        se  p_value stars
           ln_admissoes  -0.027130  0.026402 0.304556      
       ln_desligamentos   0.019000  0.026814 0.478853      
                  saldo -77.674731 69.625480 0.265017      
         ln_salario_adm  -0.065617  0.027789 0.018518    **
    ln_salario_real_adm  -0.034081  0.019308 0.078023     *
       pct_superior_adm   0.010283  0.004275 0.016447    **
      ln_salario_mulher  -0.044537  0.036202 0.219064      
       ln_salario_homem   0.003889  0.026967 0.885390      
       ln_salario_jovem  -0.133735  0.052203 0.010644    **
    ln_salario_naojovem   0.002496  0.027484 0.927677      
      ln_salario_branco  -0.028496  0.035817 0.426566      
       ln_salario_negro   0.110582  0.067872 0.103757      
    ln_salario_superior  -0.077509  0.040513 0.056178     *
       ln_salario_medio  -0.084545  0.031741 0.007930   ***
    ln_admissoes_mulher  -0.046679  0.026165 0.074905     *
     ln_admissoes_homem  -0.034969  0.026214 0.182701      
     ln_admissoes_jovem  -0.055804  0.028659 0.051962     *
     ln_admissoes_negro  -0.003190  0.027197 0.906666      

### 5b. Checkpoint — Resultados DiD

Resumo dos resultados principais (Model 3) e robustez (Model 5),
consistência 2d vs 4d.

``` python
# Etapa 2b.5b — Checkpoint

main_results = df_results[df_results['model'] == 'Model 3: FE + Controls (MAIN)']
rob_4d = df_results[df_results['model'] == 'Model 5: FE + Controls (4d)']
print("Model 3 (2d):"); [print(f"  {OUTCOMES.get(r['outcome'],r['outcome'])}: β={r['coef']:.4f}{r.get('stars','')} (p={r['p_value']:.3f})") for _,r in main_results.iterrows()]
print("Model 5 (4d):"); [print(f"  {OUTCOMES.get(r['outcome'],r['outcome'])}: β={r['coef']:.4f}{r.get('stars','')} (p={r['p_value']:.3f})") for _,r in rob_4d.iterrows()]
print("Consistência 2d vs 4d:")
for outcome in OUTCOMES:
    r2 = main_results[main_results['outcome']==outcome]; r4 = rob_4d[rob_4d['outcome']==outcome]
    if len(r2)>0 and len(r4)>0: print(f"  {outcome}: {'✓ mesma direção' if (r2.iloc[0]['coef']*r4.iloc[0]['coef'])>0 else '⚠ opostas'} (2d: {r2.iloc[0]['coef']:.4f}, 4d: {r4.iloc[0]['coef']:.4f})")
```

    Model 3 (2d):
      Log(Admissões): β=-0.0271 (p=0.305)
      Log(Desligamentos): β=0.0190 (p=0.479)
      Saldo Líquido: β=-77.6747 (p=0.265)
      Log(Salário Admissão Nominal): β=-0.0656** (p=0.019)
      Log(Salário Real Admissão): β=-0.0341* (p=0.078)
      % Superior (Admissão): β=0.0103** (p=0.016)
      Log(Salário Mulheres): β=-0.0445 (p=0.219)
      Log(Salário Homens): β=0.0039 (p=0.885)
      Log(Salário Jovens): β=-0.1337** (p=0.011)
      Log(Salário Não-Jovens): β=0.0025 (p=0.928)
      Log(Salário Brancos): β=-0.0285 (p=0.427)
      Log(Salário Negros): β=0.1106 (p=0.104)
      Log(Salário Superior): β=-0.0775* (p=0.056)
      Log(Salário Médio): β=-0.0845*** (p=0.008)
      Log(Admissões Mulheres): β=-0.0467* (p=0.075)
      Log(Admissões Homens): β=-0.0350 (p=0.183)
      Log(Admissões Jovens): β=-0.0558* (p=0.052)
      Log(Admissões Negros): β=-0.0032 (p=0.907)
    Model 5 (4d):
      Log(Admissões): β=-0.0247 (p=0.353)
      Log(Desligamentos): β=0.0196 (p=0.456)
      Saldo Líquido: β=-142.4436* (p=0.053)
      Log(Salário Admissão Nominal): β=-0.0679** (p=0.013)
      Log(Salário Real Admissão): β=-0.0449** (p=0.024)
      % Superior (Admissão): β=0.0061 (p=0.130)
      Log(Salário Mulheres): β=-0.0484 (p=0.227)
      Log(Salário Homens): β=-0.0157 (p=0.554)
      Log(Salário Jovens): β=-0.1803*** (p=0.000)
      Log(Salário Não-Jovens): β=-0.0179 (p=0.485)
      Log(Salário Brancos): β=-0.0342 (p=0.317)
      Log(Salário Negros): β=0.0361 (p=0.606)
      Log(Salário Superior): β=-0.0683* (p=0.090)
      Log(Salário Médio): β=-0.1147*** (p=0.000)
      Log(Admissões Mulheres): β=-0.0408 (p=0.129)
      Log(Admissões Homens): β=-0.0310 (p=0.240)
      Log(Admissões Jovens): β=-0.0520* (p=0.069)
      Log(Admissões Negros): β=-0.0132 (p=0.640)
    Consistência 2d vs 4d:
      ln_admissoes: ✓ mesma direção (2d: -0.0271, 4d: -0.0247)
      ln_desligamentos: ✓ mesma direção (2d: 0.0190, 4d: 0.0196)
      saldo: ✓ mesma direção (2d: -77.6747, 4d: -142.4436)
      ln_salario_adm: ✓ mesma direção (2d: -0.0656, 4d: -0.0679)
      ln_salario_real_adm: ✓ mesma direção (2d: -0.0341, 4d: -0.0449)
      pct_superior_adm: ✓ mesma direção (2d: 0.0103, 4d: 0.0061)
      ln_salario_mulher: ✓ mesma direção (2d: -0.0445, 4d: -0.0484)
      ln_salario_homem: ⚠ opostas (2d: 0.0039, 4d: -0.0157)
      ln_salario_jovem: ✓ mesma direção (2d: -0.1337, 4d: -0.1803)
      ln_salario_naojovem: ⚠ opostas (2d: 0.0025, 4d: -0.0179)
      ln_salario_branco: ✓ mesma direção (2d: -0.0285, 4d: -0.0342)
      ln_salario_negro: ✓ mesma direção (2d: 0.1106, 4d: 0.0361)
      ln_salario_superior: ✓ mesma direção (2d: -0.0775, 4d: -0.0683)
      ln_salario_medio: ✓ mesma direção (2d: -0.0845, 4d: -0.1147)
      ln_admissoes_mulher: ✓ mesma direção (2d: -0.0467, 4d: -0.0408)
      ln_admissoes_homem: ✓ mesma direção (2d: -0.0350, 4d: -0.0310)
      ln_admissoes_jovem: ✓ mesma direção (2d: -0.0558, 4d: -0.0520)
      ln_admissoes_negro: ✓ mesma direção (2d: -0.0032, 4d: -0.0132)

### 6. Event study

Estimação com dummies de interação período × tratamento. O **período de
referência é t = −1** (mês antes do ChatGPT, Nov/2022), de modo que
todos os demais coeficientes são interpretados em relação a esse mês.
**Binning dos extremos** (t ≤ −12 e t ≥ 24) reduz ruído nas pontas da
janela. Coeficientes pré-tratamento não significativos e próximos de
zero sustentam a hipótese de tendências paralelas.

``` python
# Etapa 2b.6 — Event study (dummies + estimação)

BIN_MIN, BIN_MAX, ref_t = -12, 24, -1
df_es = df_reg.copy()
df_es['t_binned'] = df_es['tempo_relativo_meses'].clip(lower=BIN_MIN, upper=BIN_MAX)

def _dname(t): return f"did_tm{-t}" if t < 0 else f"did_t{t}"
did_vars = []; t_to_name = {}
for t in sorted(df_es['t_binned'].unique()):
    if t == ref_t: continue
    dname = _dname(t); t_to_name[t] = dname
    df_es[dname] = ((df_es['t_binned']==t) & (df_es['alta_exp']==1)).astype(int)
    did_vars.append(dname)

event_study_results = {}
controls_es_base = ['idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm']
for outcome, label in OUTCOMES.items():
    if outcome not in df_es.columns: continue
    df_out = df_es[df_es[outcome].notna()].copy()
    controls_es = [c for c in controls_es_base if c != outcome]
    ctrl_es_str = ' + '.join(controls_es) if controls_es else ''
    formula = f"{outcome} ~ {' + '.join(did_vars)} + {ctrl_es_str} | cbo_4d + periodo" if ctrl_es_str else f"{outcome} ~ {' + '.join(did_vars)} | cbo_4d + periodo"
    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        idx = model.coef().index.tolist()
        coefs = []
        for t in sorted(df_es['t_binned'].unique()):
            if t == ref_t: coefs.append({'t':t,'coef':0,'se':0,'p_value':np.nan,'is_reference':True,'is_pre':t<0})
            else:
                dname = t_to_name.get(t, _dname(t))
                if dname in idx: coefs.append({'t':t,'coef':float(model.coef().loc[dname]),'se':float(model.se().loc[dname]),'p_value':float(model.pvalue().loc[dname]),'is_reference':False,'is_pre':t<0})
        df_c = pd.DataFrame(coefs); df_c['ci_low'] = df_c['coef'] - 1.96*df_c['se']; df_c['ci_high'] = df_c['coef'] + 1.96*df_c['se']
        event_study_results[outcome] = df_c
        df_c.to_csv(OUTPUTS_TABLES / f'event_study_{outcome}.csv', index=False)
    except Exception as e: print(f"  ERRO {outcome}: {e}")
print(f"Event study salvo para {len(event_study_results)} outcomes.")
```

    Event study salvo para 18 outcomes.

``` python
# Etapa 2b.6 (cont.) — Gráficos do event study

outcomes_with_results = [(o, OUTCOMES[o]) for o in OUTCOMES if o in event_study_results]
n_plot = len(outcomes_with_results)
n_cols = 4
n_rows = max(1, (n_plot + n_cols - 1) // n_cols)
fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 4 * n_rows))
axes = np.atleast_1d(axes).flat
for j in range(n_plot, len(axes)):
    axes[j].set_visible(False)
for i, (outcome, label) in enumerate(outcomes_with_results):
    ax = axes[i]
    df_c = event_study_results[outcome]
    ax.fill_between(df_c['t'], df_c['ci_low'], df_c['ci_high'], alpha=0.15, color='gray')
    pre = df_c[df_c['is_pre'] & ~df_c['is_reference']]; post = df_c[~df_c['is_pre'] & ~df_c['is_reference']]; ref = df_c[df_c['is_reference']]
    ax.scatter(pre['t'], pre['coef'], color=COLORS['pre'], s=30, label='Pré'); ax.scatter(post['t'], post['coef'], color=COLORS['post'], s=30, label='Pós')
    ax.scatter(ref['t'], ref['coef'], color='black', s=60, marker='D', label='Ref.')
    ax.plot(df_c['t'], df_c['coef'], color='gray', linewidth=0.8, alpha=0.5)
    ax.axhline(y=0, color='black', linewidth=0.5); ax.axvline(x=0, color='gray', linestyle='--', alpha=0.7)
    ax.set_title(label); ax.set_xlabel('Meses relativos ao ChatGPT'); ax.legend(fontsize=7)
plt.suptitle('Event Study: Efeito da IA Generativa sobre Emprego Formal', fontsize=14, fontweight='bold')
plt.tight_layout(); plt.savefig(OUTPUTS_FIGURES / 'event_study_all_outcomes.png', dpi=150, bbox_inches='tight'); plt.show()
```

![](etapa_2b_analise_did_caged_ilo_files/figure-commonmark/cell-10-output-1.png)

### 6b. Teste formal de tendências paralelas

H₀: todos os coeficientes pré-tratamento são conjuntamente zero. Se
rejeitarmos (ou se vários pré forem individualmente significativos), há
preocupação com a hipótese de tendências paralelas.

``` python
# Etapa 2b.6b — Teste formal tendências paralelas

results_pt = []
for outcome, label in OUTCOMES.items():
    if outcome not in event_study_results: continue
    df_c = event_study_results[outcome]
    pre_coefs = df_c[df_c['is_pre'] & ~df_c['is_reference']]
    if len(pre_coefs)==0: continue
    n_sig = (pre_coefs['p_value'] < 0.05).sum()
    se_nz = pre_coefs['se'].replace(0, np.nan); max_t = (pre_coefs['coef']/se_nz).abs().max() if se_nz.notna().any() else 0
    t_stats = (pre_coefs['coef']/pre_coefs['se'].replace(0,np.nan)).fillna(0).values; n_pre = len(t_stats)
    p_joint = 1 - stats.chi2.cdf(np.mean(t_stats**2)*n_pre, df=n_pre)
    status = 'PARALELAS' if n_sig==0 and p_joint>0.10 else 'PREOCUPAÇÃO'
    results_pt.append({'Outcome': label, 'N coefs pré': n_pre, 'Sig. (p<0.05)': int(n_sig), 'p-valor conjunto': f'{p_joint:.3f}', 'Status': status})
    print(f"{label}: {n_sig} pré sig., p_joint={p_joint:.3f} → {status}")
pd.DataFrame(results_pt).to_csv(OUTPUTS_TABLES / 'parallel_trends_test.csv', index=False)
```

    Log(Admissões): 0 pré sig., p_joint=0.639 → PARALELAS
    Log(Desligamentos): 5 pré sig., p_joint=0.000 → PREOCUPAÇÃO
    Saldo Líquido: 0 pré sig., p_joint=0.396 → PARALELAS
    Log(Salário Admissão Nominal): 0 pré sig., p_joint=0.985 → PARALELAS
    Log(Salário Real Admissão): 0 pré sig., p_joint=0.993 → PARALELAS
    % Superior (Admissão): 0 pré sig., p_joint=0.996 → PARALELAS
    Log(Salário Mulheres): 0 pré sig., p_joint=0.073 → PREOCUPAÇÃO
    Log(Salário Homens): 0 pré sig., p_joint=0.958 → PARALELAS
    Log(Salário Jovens): 0 pré sig., p_joint=0.265 → PARALELAS
    Log(Salário Não-Jovens): 0 pré sig., p_joint=0.696 → PARALELAS
    Log(Salário Brancos): 0 pré sig., p_joint=0.516 → PARALELAS
    Log(Salário Negros): 0 pré sig., p_joint=0.983 → PARALELAS
    Log(Salário Superior): 0 pré sig., p_joint=0.657 → PARALELAS
    Log(Salário Médio): 0 pré sig., p_joint=0.825 → PARALELAS
    Log(Admissões Mulheres): 0 pré sig., p_joint=0.853 → PARALELAS
    Log(Admissões Homens): 0 pré sig., p_joint=0.884 → PARALELAS
    Log(Admissões Jovens): 0 pré sig., p_joint=0.696 → PARALELAS
    Log(Admissões Negros): 0 pré sig., p_joint=0.894 → PARALELAS

### 7. Análise de heterogeneidade (Triple-DiD)

Testar se o efeito da IA é heterogêneo por composição das admissões:
idade (jovem ≤30), gênero (% mulher \> mediana), educação (% superior \>
mediana). O coeficiente da tripla interação (Post × AltaExp × Grupo)
captura o efeito diferencial para o subgrupo.

``` python
# Etapa 2b.7 — Heterogeneidade (Triple-DiD)

df_het = df_reg.copy()
pre_mask = df_het['post']==0
med_mulher = df_het.loc[pre_mask, 'pct_mulher_adm'].median(); med_educ = df_het.loc[pre_mask, 'pct_superior_adm'].median()
df_het['jovem_adm'] = (df_het['idade_media_adm'] <= 30).astype(int)
df_het['feminino_adm'] = (df_het['pct_mulher_adm'] > med_mulher).astype(int)
df_het['alta_educ_adm'] = (df_het['pct_superior_adm'] > med_educ).astype(int)

HET_GROUPS = {'jovem_adm': 'Idade (jovem ≤30)', 'feminino_adm': 'Gênero (feminino)', 'alta_educ_adm': 'Educação (superior)'}
results_het = []
for group_var, group_label in HET_GROUPS.items():
    df_het['post_alta'] = df_het['post']*df_het['alta_exp']; df_het['post_group'] = df_het['post']*df_het[group_var]
    df_het['alta_group'] = df_het['alta_exp']*df_het[group_var]; df_het['post_alta_group'] = df_het['post']*df_het['alta_exp']*df_het[group_var]
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_het.columns: continue
        ctrl_het = [c for c in ['idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm'] if c != outcome]
        ctrl_het_str = ' + '.join(ctrl_het) if ctrl_het else ''
        formula_het = f"{outcome} ~ post_alta_group + post_alta + post_group + alta_group + {ctrl_het_str} | cbo_4d + periodo" if ctrl_het_str else f"{outcome} ~ post_alta_group + post_alta + post_group + alta_group | cbo_4d + periodo"
        try:
            model = pf.feols(formula_het, data=df_het[df_het[outcome].notna()], vcov=VCOV_SPEC)
            if 'post_alta_group' not in model.coef().index: continue
            main_c = float(model.coef().loc['post_alta']); inter_c = float(model.coef().loc['post_alta_group']); inter_p = float(model.pvalue().loc['post_alta_group'])
            results_het.append({'outcome': outcome, 'outcome_label': out_label, 'group': group_label, 'main_effect': main_c, 'interaction': inter_c, 'interaction_pval': inter_p})
            if inter_p < 0.10: print(f"  {out_label} × {group_label}: β_inter = {inter_c:.4f} (p={inter_p:.3f})")
        except Exception as e: pass
df_het_results = pd.DataFrame(results_het)
df_het_results.to_csv(OUTPUTS_TABLES / 'heterogeneity_triple_did.csv', index=False)
print("Heterogeneidade salva.")
```

      Log(Salário Admissão Nominal) × Idade (jovem ≤30): β_inter = -0.3235 (p=0.001)
      Log(Salário Real Admissão) × Idade (jovem ≤30): β_inter = -0.1863 (p=0.002)
      % Superior (Admissão) × Idade (jovem ≤30): β_inter = -0.0205 (p=0.066)
      Log(Salário Homens) × Idade (jovem ≤30): β_inter = -0.2393 (p=0.012)
      Log(Salário Brancos) × Idade (jovem ≤30): β_inter = -0.1428 (p=0.097)
      Log(Salário Negros) × Idade (jovem ≤30): β_inter = -0.3994 (p=0.002)
      Log(Salário Superior) × Idade (jovem ≤30): β_inter = 0.1452 (p=0.090)
      Log(Salário Médio) × Idade (jovem ≤30): β_inter = -0.2012 (p=0.022)
      Log(Admissões Mulheres) × Idade (jovem ≤30): β_inter = 0.1158 (p=0.051)
      Log(Salário Homens) × Gênero (feminino): β_inter = -0.1008 (p=0.085)
      Log(Salário Jovens) × Gênero (feminino): β_inter = 0.2747 (p=0.035)
      Log(Admissões) × Educação (superior): β_inter = -0.1462 (p=0.050)
      % Superior (Admissão) × Educação (superior): β_inter = -0.0476 (p=0.001)
      Log(Salário Superior) × Educação (superior): β_inter = -0.6412 (p=0.000)
      Log(Admissões Homens) × Educação (superior): β_inter = -0.1295 (p=0.087)
      Log(Admissões Jovens) × Educação (superior): β_inter = -0.1484 (p=0.062)
      Log(Admissões Negros) × Educação (superior): β_inter = -0.1261 (p=0.074)
    Heterogeneidade salva.

### 8. Testes de robustez

Cinco testes: (1) **Cutoffs alternativos** (top 10%, 25%, mediana) —
espera-se mesma direção dos efeitos. (2) **Placebo temporal** (evento
fictício Dez/2021, só com dados pré-reais): o coeficiente deve ser não
significativo; significância indicaria efeitos espúrios. (3) **Exclusão
de TI** (CBO 21xx) — resultado principal deve permanecer estável. (4)
**Tendências diferenciais no pré** (trend × tratamento): coeficiente não
significativo apoia tendências paralelas. (5) **Crosswalk 2d vs 4d** —
mesma direção e magnitude similar reforçam robustez.

**O que foi feito:** A célula abaixo replica integralmente o script
`notebook/scripts/etapa_2b/10_robustness.py`, executando os cinco testes
no próprio notebook e gerando `outputs/tables/robustness_results.csv`.
Nenhum script externo é necessário; todo o código está documentado aqui.

``` python
# Etapa 2b.8 — Testes de robustez (código completo; replica 10_robustness.py no notebook)
# Gera outputs/tables/robustness_results.csv com os 5 testes abaixo.

PLACEBO_ANO, PLACEBO_MES = 2021, 12  # evento fictício Dez/2021 para placebo temporal
df_reg_rob = df_reg.copy()
results_robust = []

# Tendência linear para teste 4 (tendências diferenciais no pré)
if 'trend' not in df_reg_rob.columns and 'periodo_num' in df_reg_rob.columns:
    t_min = df_reg_rob['periodo_num'].min()
    df_reg_rob['trend'] = df_reg_rob['periodo_num'] - t_min

# TESTE 1: Cutoffs alternativos
print("TESTE 1: Cutoffs alternativos")
cutoff_vars = {
    "alta_exp": "Top 20% (MAIN)",
    "alta_exp_10": "Top 10%",
    "alta_exp_25": "Top 25%",
    "alta_exp_mediana": "Mediana",
}
for treat_var, treat_label in cutoff_vars.items():
    if treat_var not in df_reg_rob.columns:
        continue
    df_reg_rob[f"post_{treat_var}"] = df_reg_rob["post"] * df_reg_rob[treat_var]
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_reg_rob.columns:
            continue
        df_out = df_reg_rob[df_reg_rob[outcome].notna()].copy()
        formula = f"{outcome} ~ post_{treat_var} + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            cname = f"post_{treat_var}"
            coef = float(model.coef().loc[cname])
            se = float(model.se().loc[cname])
            pval = float(model.pvalue().loc[cname])
            stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
            results_robust.append({"outcome": outcome, "test_type": "Alternative Cutoff", "specification": treat_label, "coef": coef, "se": se, "p_value": pval, "stars": stars})
        except Exception as e:
            print(f"  Erro: {outcome}/{treat_label}: {e}")

# TESTE 2: Placebo temporal (evento fictício Dez/2021)
print("\nTESTE 2: Placebo temporal (evento fictício Dez/2021)")
df_placebo = df_reg_rob[df_reg_rob["post"] == 0].copy()
placebo_ref = PLACEBO_ANO * 100 + PLACEBO_MES
df_placebo["post_placebo"] = (df_placebo["periodo_num"] >= placebo_ref).astype(int)
df_placebo["did_placebo"] = df_placebo["post_placebo"] * df_placebo["alta_exp"]
for outcome, out_label in OUTCOMES.items():
    if outcome not in df_placebo.columns:
        continue
    df_out = df_placebo[df_placebo[outcome].notna()].copy()
    formula = f"{outcome} ~ did_placebo + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        coef = float(model.coef().loc["did_placebo"])
        se = float(model.se().loc["did_placebo"])
        pval = float(model.pvalue().loc["did_placebo"])
        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
        results_robust.append({"outcome": outcome, "test_type": "Placebo", "specification": f"Placebo ({PLACEBO_MES}/{PLACEBO_ANO})", "coef": coef, "se": se, "p_value": pval, "stars": stars})
        status = "PASS" if pval > 0.10 else "FAIL"
        print(f"  {out_label}: β={coef:.4f}{stars} (p={pval:.3f}) → {status}")
    except Exception as e:
        print(f"  Erro: {outcome}: {e}")

# TESTE 3: Exclusão de ocupações de TI (CBO 21xx)
print("\nTESTE 3: Exclusão de ocupações de TI")
df_no_it = df_reg_rob[~df_reg_rob["cbo_4d"].astype(str).str.startswith("21")].copy()
print(f"  Registros sem TI: {len(df_no_it):,} (removidos: {len(df_reg_rob)-len(df_no_it):,})")
for outcome, out_label in OUTCOMES.items():
    if outcome not in df_no_it.columns:
        continue
    df_out = df_no_it[df_no_it[outcome].notna()].copy()
    formula = f"{outcome} ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        coef = float(model.coef().loc["post_alta"])
        se = float(model.se().loc["post_alta"])
        pval = float(model.pvalue().loc["post_alta"])
        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
        results_robust.append({"outcome": outcome, "test_type": "Excl. TI", "specification": "Sem ocupações TI", "coef": coef, "se": se, "p_value": pval, "stars": stars})
    except Exception as e:
        print(f"  Erro: {outcome}: {e}")

# TESTE 4: Tendências diferenciais no pré-tratamento
print("\nTESTE 4: Tendências diferenciais pré-tratamento")
if 'trend' in df_reg_rob.columns:
    df_pre_trend = df_reg_rob[df_reg_rob["post"] == 0].copy()
    df_pre_trend["trend_alta"] = df_pre_trend["trend"] * df_pre_trend["alta_exp"]
    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_pre_trend.columns:
            continue
        df_out = df_pre_trend[df_pre_trend[outcome].notna()].copy()
        formula = f"{outcome} ~ trend_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef = float(model.coef().loc["trend_alta"])
            se = float(model.se().loc["trend_alta"])
            pval = float(model.pvalue().loc["trend_alta"])
            stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
            results_robust.append({"outcome": outcome, "test_type": "Differential Trends", "specification": "Trend × Tratamento (pré)", "coef": coef, "se": se, "p_value": pval, "stars": stars})
            status = "OK" if pval > 0.10 else "PREOCUPAÇÃO"
            print(f"  {out_label}: β_trend={coef:.6f}{stars} (p={pval:.3f}) → {status}")
        except Exception as e:
            print(f"  Erro: {outcome}: {e}")
else:
    print("  (trend não disponível; pulando teste 4)")

# TESTE 5: Crosswalk 4d (score 4d vs 2d)
print("\nTESTE 5: Crosswalk 2d vs 4d")
df_results_main = pd.read_csv(OUTPUTS_TABLES / "did_main_results.csv")
df_4d = df_reg_rob[df_reg_rob["exposure_score_4d"].notna()].copy()
for outcome, out_label in OUTCOMES.items():
    if outcome not in df_4d.columns:
        continue
    df_out = df_4d[df_4d[outcome].notna()].copy()
    formula = f"{outcome} ~ post_alta_4d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        coef = float(model.coef().loc["post_alta_4d"])
        se = float(model.se().loc["post_alta_4d"])
        pval = float(model.pvalue().loc["post_alta_4d"])
        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
        results_robust.append({"outcome": outcome, "test_type": "Crosswalk 4d", "specification": "Score 4d (fallback hierárquico 6 níveis)", "coef": coef, "se": se, "p_value": pval, "stars": stars})
        r_2d = df_results_main[(df_results_main["model"] == "Model 3: FE + Controls (MAIN)") & (df_results_main["outcome"] == outcome)]
        if len(r_2d) > 0:
            same_sign = (coef * r_2d.iloc[0]["coef"]) > 0
            status = "CONSISTENTE" if same_sign else "DIVERGE"
            print(f"  {out_label}: 4d β={coef:.4f}{stars} vs 2d β={r_2d.iloc[0]['coef']:.4f} → {status}")
    except Exception as e:
        print(f"  Erro: {outcome}: {e}")

df_robust = pd.DataFrame(results_robust)
df_robust.to_csv(OUTPUTS_TABLES / "robustness_results.csv", index=False)
print(f"\nResultados de robustez salvos: {OUTPUTS_TABLES / 'robustness_results.csv'}")

# Resumo por tipo de teste
for tt in df_robust["test_type"].unique():
    sub = df_robust[df_robust["test_type"] == tt]
    n_sig = (sub["p_value"] < 0.10).sum()
    print(f"  {tt}: {n_sig}/{len(sub)} significativos (p<0.10)")

# Robustez: cluster em cbo_2d (gerado por 04_did_main.py, se existir)
rob2_path = OUTPUTS_TABLES / "did_robustez_cbo2d.csv"
if rob2_path.exists():
    df_cbo2d = pd.read_csv(rob2_path)
    print("\nRobustez (cluster cbo_2d):")
    print(df_cbo2d[["outcome", "coef", "se", "p_value", "stars"]].to_string(index=False))
else:
    print("\nArquivo did_robustez_cbo2d.csv não encontrado (opcional).")
```

    TESTE 1: Cutoffs alternativos
      Erro: pct_superior_adm/Top 20% (MAIN): boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5
      Erro: pct_superior_adm/Top 10%: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5
      Erro: pct_superior_adm/Top 25%: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5
      Erro: pct_superior_adm/Mediana: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5

    TESTE 2: Placebo temporal (evento fictício Dez/2021)
      Log(Admissões): β=-0.0009 (p=0.967) → PASS

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Desligamentos): β=0.0153 (p=0.467) → PASS
      Saldo Líquido: β=-113.5738 (p=0.322) → PASS

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Admissão Nominal): β=0.0056 (p=0.859) → PASS
      Log(Salário Real Admissão): β=0.0206 (p=0.376) → PASS
      Erro: pct_superior_adm: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Mulheres): β=-0.0578 (p=0.216) → PASS
      Log(Salário Homens): β=0.0023 (p=0.952) → PASS

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Jovens): β=-0.0960* (p=0.079) → FAIL
      Log(Salário Não-Jovens): β=0.0327 (p=0.287) → PASS

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Brancos): β=-0.0041 (p=0.931) → PASS
      Log(Salário Negros): β=-0.0583 (p=0.565) → PASS

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Superior): β=0.0453 (p=0.346) → PASS
      Log(Salário Médio): β=0.0472 (p=0.308) → PASS

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Admissões Mulheres): β=-0.0009 (p=0.969) → PASS
      Log(Admissões Homens): β=-0.0059 (p=0.800) → PASS

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Admissões Jovens): β=-0.0244 (p=0.335) → PASS
      Log(Admissões Negros): β=0.0478** (p=0.049) → FAIL

    TESTE 3: Exclusão de ocupações de TI
      Registros sem TI: 31,761 (removidos: 1,227)

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Erro: pct_superior_adm: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5

    TESTE 4: Tendências diferenciais pré-tratamento
      Log(Admissões): β_trend=0.000595 (p=0.766) → OK

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Desligamentos): β_trend=0.000701 (p=0.664) → OK
      Saldo Líquido: β_trend=-0.124620 (p=0.988) → OK

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Admissão Nominal): β_trend=-0.000494 (p=0.836) → OK
      Log(Salário Real Admissão): β_trend=0.001202 (p=0.501) → OK
      Erro: pct_superior_adm: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Mulheres): β_trend=-0.005099 (p=0.153) → OK
      Log(Salário Homens): β_trend=0.001312 (p=0.669) → OK

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Jovens): β_trend=-0.006759 (p=0.113) → OK
      Log(Salário Não-Jovens): β_trend=0.001060 (p=0.640) → OK

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Brancos): β_trend=-0.001501 (p=0.686) → OK
      Log(Salário Negros): β_trend=-0.005099 (p=0.490) → OK

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Salário Superior): β_trend=0.003429 (p=0.372) → OK
      Log(Salário Médio): β_trend=0.002011 (p=0.586) → OK

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Admissões Mulheres): β_trend=0.000699 (p=0.713) → OK
      Log(Admissões Homens): β_trend=0.000227 (p=0.911) → OK

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Admissões Jovens): β_trend=-0.001469 (p=0.503) → OK
      Log(Admissões Negros): β_trend=0.004847** (p=0.015) → PREOCUPAÇÃO

    TESTE 5: Crosswalk 2d vs 4d

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

      Log(Admissões): 4d β=-0.0247 vs 2d β=-0.0271 → CONSISTENTE
      Log(Desligamentos): 4d β=0.0196 vs 2d β=0.0190 → CONSISTENTE
      Saldo Líquido: 4d β=-142.4436* vs 2d β=-77.6747 → CONSISTENTE
      Log(Salário Admissão Nominal): 4d β=-0.0679** vs 2d β=-0.0656 → CONSISTENTE
      Log(Salário Real Admissão): 4d β=-0.0449** vs 2d β=-0.0341 → CONSISTENTE
      Erro: pct_superior_adm: boolean index did not match indexed array along axis 0; size of axis is 4 but size of corresponding boolean axis is 5
      Log(Salário Mulheres): 4d β=-0.0484 vs 2d β=-0.0445 → CONSISTENTE
      Log(Salário Homens): 4d β=-0.0157 vs 2d β=0.0039 → DIVERGE
      Log(Salário Jovens): 4d β=-0.1803*** vs 2d β=-0.1337 → CONSISTENTE
      Log(Salário Não-Jovens): 4d β=-0.0179 vs 2d β=0.0025 → DIVERGE
      Log(Salário Brancos): 4d β=-0.0342 vs 2d β=-0.0285 → CONSISTENTE
      Log(Salário Negros): 4d β=0.0361 vs 2d β=0.1106 → CONSISTENTE
      Log(Salário Superior): 4d β=-0.0683* vs 2d β=-0.0775 → CONSISTENTE
      Log(Salário Médio): 4d β=-0.1147*** vs 2d β=-0.0845 → CONSISTENTE
      Log(Admissões Mulheres): 4d β=-0.0408 vs 2d β=-0.0467 → CONSISTENTE
      Log(Admissões Homens): 4d β=-0.0310 vs 2d β=-0.0350 → CONSISTENTE
      Log(Admissões Jovens): 4d β=-0.0520* vs 2d β=-0.0558 → CONSISTENTE
      Log(Admissões Negros): 4d β=-0.0132 vs 2d β=-0.0032 → CONSISTENTE

    Resultados de robustez salvos: outputs/tables/robustness_results.csv
      Alternative Cutoff: 24/68 significativos (p<0.10)
      Placebo: 2/17 significativos (p<0.10)
      Excl. TI: 6/17 significativos (p<0.10)
      Differential Trends: 1/17 significativos (p<0.10)
      Crosswalk 4d: 7/17 significativos (p<0.10)

    Robustez (cluster cbo_2d):
           outcome      coef       se  p_value stars
    ln_salario_adm -0.063085 0.036362 0.089601     *

### 10. Análise de Mecanismos e Heterogeneidade Adicional

Esta seção explora mecanismos (deskilling), robustez temporal (donut
hole), heterogeneidade por habilidade e uma tentativa de correção para o
outcome desligamentos.

#### 10.0 Mecanismos: Automação vs Augmentação (Brynjolfsson et al., 2025)

Usando o **Anthropic Economic Index** (Anexo 1 do Notebook 2a),
diferenciamos ocupações onde a IA atua como **Automação** (substitui
trabalho) vs **Augmentação** (complementa). Replicando a lógica de
“Canaries in the Coal Mine”: (1) Na amostra **Automação**
(`is_automation == 1`), estimamos DiD em admissões, desligamentos e
**salário real de admissão** — hipótese: substituição (fluxos) e queda
de salário concentrada nessas ocupações (ex.: efeito -18% em jovens).
(2) Na amostra **Augmentação** (`is_augmentation == 1`), analisamos
salário real e admissões (complementaridade; salário estável). (3)
Scatter: índice de automação (eixo X) vs coeficiente DiD estimado por
quartil (eixo Y).

``` python
# Etapa 2b.10.0 — Mecanismos: Automação vs Augmentação (Anthropic)
if not all(c in df_reg.columns for c in ['anthropic_automation_index', 'is_automation', 'is_augmentation']):
    print("AVISO: Colunas Anthropic ausentes. Rode o Anexo 1 no Notebook 2a e regenere o painel.")
else:
    # Amostra Automação: DiD em admissão/desligamento (substituição) e em salário real (hipótese: queda concentrada)
    df_auto = df_reg[df_reg['is_automation'] == 1].copy()
    df_aug  = df_reg[df_reg['is_augmentation'] == 1].copy()
    print("--- Amostra AUTOMAÇÃO (is_automation==1) ---")
    for out in ['ln_admissoes', 'ln_desligamentos', 'ln_salario_real_adm']:
        r = estimate_did(df_auto, out, f"{out} ~ post_alta | cbo_4d + periodo", f"DiD {out}")
        if r is not None: print(f"  {out}: coef={r['coef']:.4f} (se={r['se']:.4f}, p={r['p_value']:.3f}) {r.get('stars','')}")
    print("\n--- Amostra AUGMENTAÇÃO (is_augmentation==1) ---")
    for out in ['ln_salario_real_adm', 'ln_admissoes']:
        r = estimate_did(df_aug, out, f"{out} ~ post_alta | cbo_4d + periodo", f"DiD {out}")
        if r is not None: print(f"  {out}: coef={r['coef']:.4f} (se={r['se']:.4f}, p={r['p_value']:.3f}) {r.get('stars','')}")
    # Scatter: índice de automação (X) vs coeficiente DiD (Y) por quartil de ocupações
    idx_por_cbo = df_reg.groupby('cbo_4d')['anthropic_automation_index'].mean()
    df_reg['quartil_auto'] = pd.qcut(df_reg['anthropic_automation_index'].rank(method='first'), 4, labels=[1,2,3,4])
    coefs, med_idx = [], []
    for q in [1, 2, 3, 4]:
        dq = df_reg[df_reg['quartil_auto'] == q]
        if dq['post_alta'].var() < 1e-10: continue
        if dq['cbo_4d'].nunique() < 2: continue  # evita singleton FE
        try:
            mod = pf.feols('ln_admissoes ~ post_alta | cbo_4d + periodo', data=dq, vcov=VCOV_SPEC)
            if 'post_alta' in mod.coef().index:
                coefs.append(float(mod.coef().loc['post_alta']))
                med_idx.append(dq['anthropic_automation_index'].median())
        except (ValueError, Exception):
            continue  # colinearidade ou singleton FE: pula quartil
    if len(coefs) >= 2:
        fig, ax = plt.subplots()
        ax.scatter(med_idx, coefs, s=80)
        for i, (x, y) in enumerate(zip(med_idx, coefs)):
            ax.annotate(f'Q{i+1}', (x, y), xytext=(5,5), textcoords='offset points', fontsize=9)
        ax.axhline(0, color='gray', linestyle='--')
        ax.set_xlabel('Anthropic Automation Index (mediana do quartil)')
        ax.set_ylabel('Coeficiente DiD (ln_admissoes)')
        ax.set_title('Efeito DiD por quartil do índice de automação (Brynjolfsson et al., 2025)')
        plt.tight_layout()
        OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUTPUTS_FIGURES / 'scatter_automation_index_vs_did_coef.png', dpi=150, bbox_inches='tight')
        plt.show()
        print(f"Figura salva: {OUTPUTS_FIGURES / 'scatter_automation_index_vs_did_coef.png'}")
    else:
        print("Scatter não gerado: menos de 2 quartis com regressão válida (colinearidade/singleton FE).")
        print(f"  Quartis com coeficiente estimado: {len(coefs)}.")
```

    --- Amostra AUTOMAÇÃO (is_automation==1) ---
      ln_admissoes: coef=0.0333 (se=0.0671, p=0.623) 
      ln_desligamentos: coef=0.0716 (se=0.0703, p=0.316) 
      ln_salario_real_adm: coef=0.0768 (se=0.0557, p=0.177) 

    --- Amostra AUGMENTAÇÃO (is_augmentation==1) ---
      ln_salario_real_adm: coef=0.0145 (se=0.0317, p=0.647) 
      ln_admissoes: coef=-0.0303 (se=0.0291, p=0.298) 

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 2 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

![](etapa_2b_analise_did_caged_ilo_files/figure-commonmark/cell-14-output-3.png)

    Figura salva: outputs/figures/scatter_automation_index_vs_did_coef.png

#### 10.1 Mecanismo: Deskilling

Se o salário caiu após o choque da IA, interessa saber se (A) a empresa
paga menos para a mesma pessoa ou (B) contrata pessoas menos experientes
(mais jovens ou menos escolarizadas). Aqui tratamos **idade média** e
**% com ensino superior** na admissão como *outcomes*: coeficientes
**negativos** e significativos sugerem “rejuvenescimento” ou deskilling
da força de trabalho, coerente com a queda do salário médio.

``` python
# Etapa 2b.10.1 — Mecanismo: Deskilling
outcomes_mechanism = {
    'idade_media_adm': 'Idade Média (Admissão)',
    'pct_superior_adm': '% Superior (Admissão)'
}

print("--- Análise de Mecanismo (Deskilling) ---")
mec_results = []
for outcome, label in outcomes_mechanism.items():
    if outcome not in df_reg.columns:
        continue
    df_out = df_reg[df_reg[outcome].notna()].copy()
    res = estimate_did(df_out, outcome, f"{outcome} ~ post_alta | cbo_4d + periodo", label)
    if res:
        mec_results.append(res)

if mec_results:
    df_mec = pd.DataFrame(mec_results)
    print(df_mec[['outcome', 'coef', 'p_value', 'stars']].to_string(index=False))
    # Interpretação: se Idade Média cair (coef negativo sig.), a IA está "rejuvenescendo" a força de trabalho,
    # o que explica parte da queda do salário médio (jovens ganham menos em média).
else:
    print("Nenhum resultado (variáveis ausentes em df_reg).")
```

    --- Análise de Mecanismo (Deskilling) ---
             outcome     coef  p_value stars
     idade_media_adm 0.264103 0.059515     *
    pct_superior_adm 0.012041 0.008646   ***

#### 10.2 Robustez: Donut Hole

O ChatGPT foi lançado em 30/Nov/2022. Dezembro e Janeiro são meses
atípicos (férias, ajustes de fim de ano). Excluir **Dez/22 (202212)** e
**Jan/23 (202301)** testa se o resultado principal não depende apenas do
choque inicial; estimativa estável reforça robustez.

``` python
# Etapa 2b.10.2 — Robustez: Donut Hole (excluir Dez/22 e Jan/23)
donut_mask = ~df_reg['periodo_num'].isin([202212, 202301])
df_donut = df_reg[donut_mask].copy()

print("--- Robustez: Donut Hole (Sem Dez/22 e Jan/23) ---")
res_donut = estimate_did(
    df_donut,
    'ln_salario_real_adm',
    'ln_salario_real_adm ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo',
    'Robustez Donut'
)
if res_donut:
    print(f"Coef Salário Real Donut: {res_donut['coef']:.4f} (p={res_donut['p_value']:.3f})")
else:
    print("Erro na estimação donut.")
```

    --- Robustez: Donut Hole (Sem Dez/22 e Jan/23) ---
    Coef Salário Real Donut: -0.0376 (p=0.055)

#### 10.3 Heterogeneidade por nível de habilidade (High vs Low Skill)

A teoria sugere que a IA afeta sobretudo “trabalhadores do
conhecimento”. Usamos a mediana de **% com ensino superior na admissão**
(`pct_superior_adm`) como proxy de qualificação: ocupações acima da
mediana (high skill) vs. abaixo (low skill). Espera-se efeito mais forte
(mais negativo) no grupo high skill.

``` python
# Etapa 2b.10.3 — Heterogeneidade: Alta vs Baixa qualificação (proxy: pct_superior_adm)
mediana_sup = df_reg['pct_superior_adm'].median()
df_high_skill = df_reg[df_reg['pct_superior_adm'] > mediana_sup].copy()
df_low_skill = df_reg[df_reg['pct_superior_adm'] <= mediana_sup].copy()

print("--- Heterogeneidade por Nível de Escolaridade ---")
formula_m3 = "ln_salario_real_adm ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"
res_high = estimate_did(df_high_skill, 'ln_salario_real_adm', formula_m3, 'High Skill')
res_low = estimate_did(df_low_skill, 'ln_salario_real_adm', formula_m3, 'Low Skill')

if res_high:
    print(f"Efeito em High Skill: {res_high['coef']:.4f} (p={res_high['p_value']:.3f})")
if res_low:
    print(f"Efeito em Low Skill:  {res_low['coef']:.4f} (p={res_low['p_value']:.3f})")
# Esperado: efeito mais forte (negativo) no grupo High Skill.
```

    --- Heterogeneidade por Nível de Escolaridade ---

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 25 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 15 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

    Efeito em High Skill: 0.0023 (p=0.885)
    Efeito em Low Skill:  -0.1146 (p=0.051)

#### 10.4 Tentativa de correção para Desligamentos

O outcome *desligamentos* apresentou tendências paralelas questionáveis
no event study. Uma opção é controlar por uma **tendência linear
específica do grupo** (interação `alta_exp : trend`). Se o coeficiente
DiD de desligamentos deixar de ser significativo (p \> 0,10) ao incluir
essa tendência, isso sugere que o resultado anterior era espúrio (viés
por tendência pré-existente).

``` python
# Etapa 2b.10.4 — Tentativa de correção para Desligamentos (controle de tendência linear)
# Garantir que 'trend' exista no dataframe de regressão
if 'trend' not in df_reg.columns and 'periodo_num' in df_reg.columns:
    def periodo_num_to_months(pn):
        y, m = divmod(int(pn), 100)
        return (y - 2021) * 12 + (m - 1)
    df_reg['trend'] = df_reg['periodo_num'].apply(periodo_num_to_months)
    df_reg['trend'] = df_reg['trend'] - df_reg['trend'].min()

print("--- Tentativa de Correção Linear (Desligamentos) ---")
formula_trend = "ln_desligamentos ~ post_alta + alta_exp:trend | cbo_4d + periodo"
res_trend = estimate_did(df_reg, 'ln_desligamentos', formula_trend, 'Trend Control')
if res_trend:
    print(f"Coef Desligamentos (com trend): {res_trend['coef']:.4f} (p={res_trend['p_value']:.3f})")
    # Se p_value > 0.10, o efeito some ao controlar pela tendência; confirma que o resultado anterior pode ser espúrio.
else:
    print("Erro na estimação com trend.")
```

    --- Tentativa de Correção Linear (Desligamentos) ---
    Coef Desligamentos (com trend): -0.0361 (p=0.102)

### 11. Tabelas LaTeX

Tabela principal (Model 3) para inclusão na dissertação.

``` python
# Etapa 2b.9 - Tabela LaTeX

main = df_results[df_results['model'] == 'Model 3: FE + Controls (MAIN)']
outcomes_order = ['ln_admissoes', 'ln_desligamentos', 'saldo', 'ln_salario_real_adm', 'ln_admissoes_jovem', 'pct_superior_adm']
col_names = ['(1) Log(Adm.)', '(2) Log(Desl.)', '(3) Saldo', '(4) Log(Sal. Real)', '(5) Log(Adm. Jov.)', '(6) % Superior']

# Representação visual no notebook
coefs = []; ses = []
for o in outcomes_order:
    row = main[main['outcome']==o]
    if len(row) > 0:
        r = row.iloc[0]
        coefs.append(f"{r['coef']:.4f}{r.get('stars', '')}")
        ses.append(f"({r['se']:.4f})")
    else:
        coefs.append("—"); ses.append("—")
tab_vis = pd.DataFrame([coefs, ses], index=["Post × Alta Exp.", "Erro padrão"], columns=col_names)
print("Tabela principal (Model 3) — visualização:")
display(tab_vis)
print("\nFE Ocupação e FE Período: ✓ em todas as colunas. * p<0,10 ** p<0,05 *** p<0,01.")

coef_line = r"Post $\times$ Alta Exp."; se_line = ""
for o in outcomes_order:
    row = main[main['outcome']==o]
    if len(row)>0: r=row.iloc[0]; coef_line += f" & {r['coef']:.4f}{r.get('stars','')}"; se_line += f" & ({r['se']:.4f})"
    else: coef_line += " & —"; se_line += " & —"
lines = [r"\begin{table}[htbp]", r"\centering", r"\caption{Efeitos DiD sobre Emprego Formal: Resultados Principais}", r"\label{tab:did_main}", r"\begin{tabular}{lcccccc}", r"\toprule", r" & (1) Log(Adm.) & (2) Log(Desl.) & (3) Saldo & (4) Log(Sal. Real) & (5) Log(Adm. Jov.) & (6) % Superior \\", r"\midrule", coef_line + r" \\", se_line + r" \\", r"\midrule", r"FE Ocupação & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\", r"FE Período & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\", r"\bottomrule", r"\end{tabular}", r"\end{table}"]
latex_text = '\n'.join(lines)
with open(OUTPUTS_TABLES / 'table_did_main.tex', 'w') as f: f.write(latex_text)
print("Tabela LaTeX salva em outputs/tables/table_did_main.tex")

# Mostrar LaTeX no notebook (para copiar na dissertação)
from IPython.display import display, Markdown
display(Markdown("**Código LaTeX (para copiar na dissertação):**"))
display(Markdown("```latex\n" + latex_text + "\n```"))
```

    Tabela principal (Model 3) — visualização:

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | \(1\) Log(Adm.) | \(2\) Log(Desl.) | \(3\) Saldo | \(4\) Log(Sal. Real) | \(5\) Log(Adm. Jov.) | \(6\) % Superior |
|----|----|----|----|----|----|----|
| Post × Alta Exp. | -0.0271 | 0.0190 | -77.6747 | -0.0341\* | -0.0558\* | 0.0103\*\* |
| Erro padrão | (0.0264) | (0.0268) | (69.6255) | (0.0193) | (0.0287) | (0.0043) |

</div>


    FE Ocupação e FE Período: ✓ em todas as colunas. * p<0,10 ** p<0,05 *** p<0,01.
    Tabela LaTeX salva em outputs/tables/table_did_main.tex

**Código LaTeX (para copiar na dissertação):**

``` latex
\begin{table}[htbp]
\centering
\caption{Efeitos DiD sobre Emprego Formal: Resultados Principais}
\label{tab:did_main}
\begin{tabular}{lcccccc}
\toprule
 & (1) Log(Adm.) & (2) Log(Desl.) & (3) Saldo & (4) Log(Sal. Real) & (5) Log(Adm. Jov.) & (6) % Superior \\
\midrule
Post $\times$ Alta Exp. & -0.0271 & 0.0190 & -77.6747 & -0.0341* & -0.0558* & 0.0103** \\
 & (0.0264) & (0.0268) & (69.6255) & (0.0193) & (0.0287) & (0.0043) \\
\midrule
FE Ocupação & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
FE Período & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
\bottomrule
\end{tabular}
\end{table}
```

### 12. Síntese e conclusões

Resumo dos achados, comparação com a literatura e limitações.

``` python
# Etapa 2b.10 — Síntese

print("RESULTADOS DiD PRINCIPAIS (Model 3)")
for _, r in df_results[df_results['model']=='Model 3: FE + Controls (MAIN)'].iterrows():
    print(f"  {OUTCOMES.get(r['outcome'],r['outcome'])}: β = {r['coef']:.4f}{r.get('stars','')} (p = {r['p_value']:.3f})")
print("\nComparação PNAD: outcomes diferentes (CAGED = fluxos; PNAD = estoques). Ver texto da dissertação.")
```

    RESULTADOS DiD PRINCIPAIS (Model 3)
      Log(Admissões): β = -0.0271 (p = 0.305)
      Log(Desligamentos): β = 0.0190 (p = 0.479)
      Saldo Líquido: β = -77.6747 (p = 0.265)
      Log(Salário Admissão Nominal): β = -0.0656** (p = 0.019)
      Log(Salário Real Admissão): β = -0.0341* (p = 0.078)
      % Superior (Admissão): β = 0.0103** (p = 0.016)
      Log(Salário Mulheres): β = -0.0445 (p = 0.219)
      Log(Salário Homens): β = 0.0039 (p = 0.885)
      Log(Salário Jovens): β = -0.1337** (p = 0.011)
      Log(Salário Não-Jovens): β = 0.0025 (p = 0.928)
      Log(Salário Brancos): β = -0.0285 (p = 0.427)
      Log(Salário Negros): β = 0.1106 (p = 0.104)
      Log(Salário Superior): β = -0.0775* (p = 0.056)
      Log(Salário Médio): β = -0.0845*** (p = 0.008)
      Log(Admissões Mulheres): β = -0.0467* (p = 0.075)
      Log(Admissões Homens): β = -0.0350 (p = 0.183)
      Log(Admissões Jovens): β = -0.0558* (p = 0.052)
      Log(Admissões Negros): β = -0.0032 (p = 0.907)

    Comparação PNAD: outcomes diferentes (CAGED = fluxos; PNAD = estoques). Ver texto da dissertação.

### Limitações desta etapa

1.  **Emprego formal apenas:** CAGED cobre só CLT; informalidade não
    capturada.
2.  **Fluxos vs. estoques:** Redução em admissões pode refletir menor
    rotatividade ou menor demanda.
3.  **Difusão gradual da IA:** Tratamento assume impacto abrupto em
    Nov/2022; na prática a difusão é gradual.
4.  **Janela temporal:** Jan/2021–Jun/2025 (54 meses); 2025 limitado a 6
    meses.
5.  **Crosswalk 2d/4d:** Agregação perde variação; crosswalk 4d com
    fallback pode ter erro de medição.
6.  **Índice global:** ILO calibrado globalmente; pode não capturar
    especificidades brasileiras.
7.  **Outliers salariais:** Winsorização P1/P99 aplicada.

---

<!-- fonte: etapa_2c_resultados.ipynb -->

# ETAPA 2c — Resultados: Consolidação e Síntese da Análise DiD


**Dissertação:** Inteligência Artificial Generativa e o Mercado de
Trabalho Brasileiro: Uma Análise de Exposição Ocupacional e seus Efeitos
Distributivos.

**Aluno:** Manoel Brasil Orlandi

------------------------------------------------------------------------

### Objetivo deste notebook

Organizar as tabelas e figuras geradas no **Notebook 2b** (Análise DiD)
para leitura com a orientadora. Inclui: listagem e exibição de todos os
resultados e tabelas em `outputs/tables` e `outputs/figures`, gráficos
adicionais para ilustrar os achados, **resumo narrativo** e uma
**tabela-síntese de achados** com relevância estatística (***/**/*) e
destaque em cores para os achados mais relevantes.

**Input:** Arquivos gerados pelo notebook
`etapa_2b_analise_did_caged_ilo.ipynb` (pastas `outputs/tables` e
`outputs/figures`).

### 1. Configuração do ambiente

Importar bibliotecas, definir caminhos e estilo de gráficos. Caminhos
relativos ao diretório `notebook/`.

``` python
# Verificar dependências e instalar apenas o que faltar (rode esta célula primeiro)
import importlib.util
import subprocess
import sys

PACOTES = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
]

def ja_instalado(nome_import):
    return importlib.util.find_spec(nome_import) is not None

faltando = [pip for imp, pip in PACOTES if not ja_instalado(imp)]
if faltando:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + faltando)
    print("Instalado:", ", ".join(faltando))
else:
    print("Todas as dependências já estão instaladas.")
```

    Todas as dependências já estão instaladas.

``` python
# Etapa 2c — Configuração
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from IPython.display import display, Image

warnings.filterwarnings("ignore", category=FutureWarning)

OUTPUTS_TABLES = Path("../../outputs/tables")
OUTPUTS_FIGURES = Path("../../outputs/figures")
OUTPUTS_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUTS_FIGURES.mkdir(parents=True, exist_ok=True)

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)
pd.set_option("display.float_format", lambda x: f"{x:.4f}")

plt.style.use("seaborn-v0_8-paper")
sns.set_palette("Set2")
plt.rcParams.update({"font.size": 11, "axes.titlesize": 13, "axes.labelsize": 12, "figure.dpi": 150})

print("Configuração carregada.")
```

    Configuração carregada.

### 2. Tabelas geradas no etapa_2b

As tabelas abaixo foram salvas em `outputs/tables` pelo notebook
etapa_2b. Exibimos cada uma para leitura.

#### 2.1 Balanceamento pré-tratamento

Médias das variáveis no período pré-tratamento: grupo de controle (baixa
exposição) vs. grupo de tratamento (alta exposição). *Diff. Normalizada*
e indicador de balanceamento (✓ ou ⚠️).

``` python
path = OUTPUTS_TABLES / "balance_table_pre.csv"
if path.exists():
    df = pd.read_csv(path)
    display(df)
else:
    print("Arquivo não encontrado:", path, "- Execute o notebook etapa_2b para gerar as tabelas.")
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | Variável              | Controle  | Tratamento | Diff. Normalizada | Balanceado |
|-----|-----------------------|-----------|------------|-------------------|------------|
| 0   | Admissões (média)     | 2655.3378 | 3409.8367  | 0.0601            | ✓          |
| 1   | Desligamentos (média) | 2321.3264 | 2916.9194  | 0.0552            | ✓          |
| 2   | Saldo (média)         | 334.0114  | 492.9173   | 0.0865            | ✓          |
| 3   | Salário médio (R\$)   | 2738.7651 | 5388.2059  | 0.6846            | ⚠️         |
| 4   | Idade média           | 32.7528   | 31.7992    | -0.1723           | ✓          |
| 5   | % Mulheres            | 0.2789    | 0.4414     | 0.6965            | ⚠️         |
| 6   | % Superior            | 0.1557    | 0.4189     | 1.1501            | ⚠️         |
| 7   | Meses                 | 22.5706   | 21.8550    | -0.2187           | ✓          |

</div>

#### 2.2 Resultados principais DiD

Coeficiente do tratamento (alta exposição à IA) para cada modelo (1:
Basic, 2: FE, 3: FE + Controls — principal, 4–6: contínuo e 4d) e
outcome. Erros padrão clusterizados por ocupação (CBO 4d). Coluna
`stars`: \*\*\* p\<0.01, \*\* p\<0.05, \* p\<0.10.

``` python
path = OUTPUTS_TABLES / "did_main_results.csv"
if path.exists():
    df = pd.read_csv(path)
    display(df)
else:
    print("Arquivo não encontrado:", path)
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | model | outcome | coef | se | p_value | stars | n_obs | n_clusters |
|----|----|----|----|----|----|----|----|----|
| 0 | Model 1: Basic | ln_admissoes | 0.0056 | 0.0375 | 0.8807 | NaN | 32988 | NaN |
| 1 | Model 2: FE | ln_admissoes | -0.0215 | 0.0268 | 0.4235 | NaN | 32988 | NaN |
| 2 | Model 3: FE + Controls (MAIN) | ln_admissoes | -0.0271 | 0.0264 | 0.3046 | NaN | 32988 | NaN |
| 3 | Model 4: Continuous (2d) | ln_admissoes | 0.0090 | 0.0804 | 0.9112 | NaN | 32988 | NaN |
| 4 | Model 5: FE + Controls (4d) | ln_admissoes | -0.0247 | 0.0266 | 0.3528 | NaN | 32988 | NaN |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 103 | Model 2: FE | ln_admissoes_negro | -0.0032 | 0.0274 | 0.9076 | NaN | 32988 | NaN |
| 104 | Model 3: FE + Controls (MAIN) | ln_admissoes_negro | -0.0032 | 0.0272 | 0.9067 | NaN | 32988 | NaN |
| 105 | Model 4: Continuous (2d) | ln_admissoes_negro | 0.0880 | 0.0843 | 0.2970 | NaN | 32988 | NaN |
| 106 | Model 5: FE + Controls (4d) | ln_admissoes_negro | -0.0132 | 0.0282 | 0.6404 | NaN | 32988 | NaN |
| 107 | Model 6: Continuous (4d) | ln_admissoes_negro | 0.0439 | 0.0831 | 0.5978 | NaN | 32988 | NaN |

<p>108 rows × 8 columns</p>
</div>

#### 2.3 Testes de robustez

Efeito DiD sob: cutoff alternativo (top 10%, 25%, mediana), placebo
(tratamento em 12/2021), exclusão de ocupações de TI, tendências
diferenciais (pré) e crosswalk 4d.

``` python
path = OUTPUTS_TABLES / "robustness_results.csv"
if path.exists():
    df = pd.read_csv(path)
    display(df)
else:
    print("Arquivo não encontrado:", path)
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | outcome | test_type | specification | coef | se | p_value | stars |
|----|----|----|----|----|----|----|----|
| 0 | ln_admissoes | Alternative Cutoff | Top 20% (MAIN) | -0.0266 | 0.0265 | 0.3166 | NaN |
| 1 | ln_desligamentos | Alternative Cutoff | Top 20% (MAIN) | 0.0190 | 0.0268 | 0.4786 | NaN |
| 2 | saldo | Alternative Cutoff | Top 20% (MAIN) | -77.6159 | 69.6389 | 0.2655 | NaN |
| 3 | ln_salario_adm | Alternative Cutoff | Top 20% (MAIN) | -0.0631 | 0.0285 | 0.0274 | \*\* |
| 4 | ln_admissoes | Alternative Cutoff | Top 10% | 0.0547 | 0.0345 | 0.1133 | NaN |
| 5 | ln_desligamentos | Alternative Cutoff | Top 10% | 0.0633 | 0.0380 | 0.0958 | \* |
| 6 | saldo | Alternative Cutoff | Top 10% | -173.8931 | 102.5733 | 0.0905 | \* |
| 7 | ln_salario_adm | Alternative Cutoff | Top 10% | -0.0438 | 0.0372 | 0.2392 | NaN |
| 8 | ln_admissoes | Alternative Cutoff | Top 25% | -0.0369 | 0.0239 | 0.1241 | NaN |
| 9 | ln_desligamentos | Alternative Cutoff | Top 25% | 0.0297 | 0.0250 | 0.2351 | NaN |
| 10 | saldo | Alternative Cutoff | Top 25% | -112.5864 | 63.4546 | 0.0765 | \* |
| 11 | ln_salario_adm | Alternative Cutoff | Top 25% | -0.0630 | 0.0254 | 0.0135 | \*\* |
| 12 | ln_admissoes | Alternative Cutoff | Mediana | -0.0107 | 0.0196 | 0.5865 | NaN |
| 13 | ln_desligamentos | Alternative Cutoff | Mediana | -0.0112 | 0.0203 | 0.5811 | NaN |
| 14 | saldo | Alternative Cutoff | Mediana | -32.3607 | 48.2539 | 0.5027 | NaN |
| 15 | ln_salario_adm | Alternative Cutoff | Mediana | -0.0132 | 0.0211 | 0.5327 | NaN |
| 16 | ln_admissoes | Placebo | Placebo (12/2021) | 0.0000 | 0.0232 | 0.9986 | NaN |
| 17 | ln_desligamentos | Placebo | Placebo (12/2021) | 0.0151 | 0.0211 | 0.4739 | NaN |
| 18 | saldo | Placebo | Placebo (12/2021) | -113.1696 | 114.5243 | 0.3235 | NaN |
| 19 | ln_salario_adm | Placebo | Placebo (12/2021) | 0.0105 | 0.0321 | 0.7448 | NaN |
| 20 | ln_admissoes | Excl. TI | Sem ocupações TI | -0.0241 | 0.0306 | 0.4314 | NaN |
| 21 | ln_desligamentos | Excl. TI | Sem ocupações TI | 0.0317 | 0.0310 | 0.3065 | NaN |
| 22 | saldo | Excl. TI | Sem ocupações TI | -92.5477 | 79.3140 | 0.2437 | NaN |
| 23 | ln_salario_adm | Excl. TI | Sem ocupações TI | -0.0767 | 0.0324 | 0.0181 | \*\* |
| 24 | ln_admissoes | Differential Trends | Trend × Tratamento (pré) | 0.0007 | 0.0020 | 0.7343 | NaN |
| 25 | ln_desligamentos | Differential Trends | Trend × Tratamento (pré) | 0.0007 | 0.0016 | 0.6740 | NaN |
| 26 | saldo | Differential Trends | Trend × Tratamento (pré) | -0.0890 | 8.0470 | 0.9912 | NaN |
| 27 | ln_salario_adm | Differential Trends | Trend × Tratamento (pré) | -0.0001 | 0.0024 | 0.9805 | NaN |
| 28 | ln_admissoes | Crosswalk 4d | Score 4d (fallback hierárquico 6 níveis) | -0.0238 | 0.0268 | 0.3743 | NaN |
| 29 | ln_desligamentos | Crosswalk 4d | Score 4d (fallback hierárquico 6 níveis) | 0.0197 | 0.0264 | 0.4555 | NaN |
| 30 | saldo | Crosswalk 4d | Score 4d (fallback hierárquico 6 níveis) | -142.3377 | 73.4753 | 0.0532 | \* |
| 31 | ln_salario_adm | Crosswalk 4d | Score 4d (fallback hierárquico 6 níveis) | -0.0635 | 0.0283 | 0.0252 | \*\* |

</div>

#### 2.4 Robustez: cluster por CBO 2d

Resultado do modelo principal (FE + Controls) com erros padrão
clusterizados por CBO 2 dígitos em vez de 4d.

``` python
path = OUTPUTS_TABLES / "did_robustez_cbo2d.csv"
if path.exists():
    df = pd.read_csv(path)
    display(df)
else:
    print("Arquivo não encontrado:", path)
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | model | outcome | coef | se | p_value | stars | n_obs | n_clusters | vcov |
|----|----|----|----|----|----|----|----|----|----|
| 0 | FE+Controls (cluster cbo_2d) | ln_salario_adm | -0.0631 | 0.0364 | 0.0896 | \* | 32988 | NaN | cbo_2d |

</div>

#### 2.5 Teste de tendências paralelas

Para cada outcome: número de coeficientes pré-tratamento no event study,
quantos significativos (p\<0.05), p-valor do teste conjunto (pré = 0) e
status (PARALELAS ou PREOCUPAÇÃO).

``` python
path = OUTPUTS_TABLES / "parallel_trends_test.csv"
if path.exists():
    df = pd.read_csv(path)
    display(df)
else:
    print("Arquivo não encontrado:", path)
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | Outcome | N coefs pré | Sig. (p\<0.05) | p-valor conjunto | Status |
|----|----|----|----|----|----|
| 0 | Log(Admissões) | 11 | 0 | 0.6390 | PARALELAS |
| 1 | Log(Desligamentos) | 11 | 5 | 0.0000 | PREOCUPAÇÃO |
| 2 | Saldo Líquido | 11 | 0 | 0.3960 | PARALELAS |
| 3 | Log(Salário Admissão Nominal) | 11 | 0 | 0.9850 | PARALELAS |
| 4 | Log(Salário Real Admissão) | 11 | 0 | 0.9930 | PARALELAS |
| 5 | % Superior (Admissão) | 11 | 0 | 0.9960 | PARALELAS |
| 6 | Log(Salário Mulheres) | 11 | 0 | 0.0730 | PREOCUPAÇÃO |
| 7 | Log(Salário Homens) | 11 | 0 | 0.9580 | PARALELAS |
| 8 | Log(Salário Jovens) | 11 | 0 | 0.2650 | PARALELAS |
| 9 | Log(Salário Não-Jovens) | 11 | 0 | 0.6960 | PARALELAS |
| 10 | Log(Salário Brancos) | 11 | 0 | 0.5160 | PARALELAS |
| 11 | Log(Salário Negros) | 11 | 0 | 0.9830 | PARALELAS |
| 12 | Log(Salário Superior) | 11 | 0 | 0.6570 | PARALELAS |
| 13 | Log(Salário Médio) | 11 | 0 | 0.8250 | PARALELAS |
| 14 | Log(Admissões Mulheres) | 11 | 0 | 0.8530 | PARALELAS |
| 15 | Log(Admissões Homens) | 11 | 0 | 0.8840 | PARALELAS |
| 16 | Log(Admissões Jovens) | 11 | 0 | 0.6960 | PARALELAS |
| 17 | Log(Admissões Negros) | 11 | 0 | 0.8940 | PARALELAS |

</div>

#### 2.6 Heterogeneidade (Triple DiD)

Efeito principal e interação (tratamento × grupo: jovem, feminino,
superior, negro) para cada outcome. `interaction_pval` indica se o
efeito difere entre grupos.

``` python
path = OUTPUTS_TABLES / "heterogeneity_triple_did.csv"
if path.exists():
    df = pd.read_csv(path)
    display(df)
else:
    print("Arquivo não encontrado:", path)
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | outcome | outcome_label | group | main_effect | interaction | interaction_pval |
|----|----|----|----|----|----|----|
| 0 | ln_admissoes | Log(Admissões) | Idade (jovem ≤30) | -0.0444 | 0.0866 | 0.1545 |
| 1 | ln_desligamentos | Log(Desligamentos) | Idade (jovem ≤30) | 0.0075 | 0.0682 | 0.3731 |
| 2 | saldo | Saldo Líquido | Idade (jovem ≤30) | -7.9403 | -356.7984 | 0.2073 |
| 3 | ln_salario_adm | Log(Salário Admissão Nominal) | Idade (jovem ≤30) | -0.0055 | -0.3235 | 0.0007 |
| 4 | ln_salario_real_adm | Log(Salário Real Admissão) | Idade (jovem ≤30) | -0.0000 | -0.1863 | 0.0025 |
| 5 | pct_superior_adm | % Superior (Admissão) | Idade (jovem ≤30) | 0.0138 | -0.0205 | 0.0656 |
| 6 | ln_salario_mulher | Log(Salário Mulheres) | Idade (jovem ≤30) | -0.0455 | 0.0066 | 0.9369 |
| 7 | ln_salario_homem | Log(Salário Homens) | Idade (jovem ≤30) | 0.0478 | -0.2393 | 0.0125 |
| 8 | ln_salario_jovem | Log(Salário Jovens) | Idade (jovem ≤30) | -0.1268 | 0.0085 | 0.9368 |
| 9 | ln_salario_naojovem | Log(Salário Não-Jovens) | Idade (jovem ≤30) | -0.0350 | 0.1236 | 0.1860 |
| 10 | ln_salario_branco | Log(Salário Brancos) | Idade (jovem ≤30) | -0.0000 | -0.1428 | 0.0965 |
| 11 | ln_salario_negro | Log(Salário Negros) | Idade (jovem ≤30) | 0.1878 | -0.3994 | 0.0024 |
| 12 | ln_salario_superior | Log(Salário Superior) | Idade (jovem ≤30) | -0.1076 | 0.1452 | 0.0899 |
| 13 | ln_salario_medio | Log(Salário Médio) | Idade (jovem ≤30) | -0.0453 | -0.2012 | 0.0223 |
| 14 | ln_admissoes_mulher | Log(Admissões Mulheres) | Idade (jovem ≤30) | -0.0700 | 0.1158 | 0.0510 |
| 15 | ln_admissoes_homem | Log(Admissões Homens) | Idade (jovem ≤30) | -0.0519 | 0.0864 | 0.1436 |
| 16 | ln_admissoes_jovem | Log(Admissões Jovens) | Idade (jovem ≤30) | -0.0689 | 0.0633 | 0.3207 |
| 17 | ln_admissoes_negro | Log(Admissões Negros) | Idade (jovem ≤30) | -0.0039 | 0.0034 | 0.9608 |
| 18 | ln_admissoes | Log(Admissões) | Gênero (feminino) | -0.0371 | 0.0035 | 0.9446 |
| 19 | ln_desligamentos | Log(Desligamentos) | Gênero (feminino) | -0.0330 | 0.0631 | 0.1702 |
| 20 | saldo | Saldo Líquido | Gênero (feminino) | 32.6662 | -130.4921 | 0.3813 |
| 21 | ln_salario_adm | Log(Salário Admissão Nominal) | Gênero (feminino) | -0.1190 | 0.0848 | 0.1922 |
| 22 | ln_salario_real_adm | Log(Salário Real Admissão) | Gênero (feminino) | -0.0593 | 0.0442 | 0.3049 |
| 23 | pct_superior_adm | % Superior (Admissão) | Gênero (feminino) | 0.0224 | -0.0132 | 0.1287 |
| 24 | ln_salario_mulher | Log(Salário Mulheres) | Gênero (feminino) | -0.1170 | 0.1389 | 0.1594 |
| 25 | ln_salario_homem | Log(Salário Homens) | Gênero (feminino) | 0.0229 | -0.1008 | 0.0847 |
| 26 | ln_salario_jovem | Log(Salário Jovens) | Gênero (feminino) | -0.3424 | 0.2747 | 0.0352 |
| 27 | ln_salario_naojovem | Log(Salário Não-Jovens) | Gênero (feminino) | -0.0327 | 0.0277 | 0.7390 |
| 28 | ln_salario_branco | Log(Salário Brancos) | Gênero (feminino) | 0.0378 | -0.0998 | 0.1519 |
| 29 | ln_salario_negro | Log(Salário Negros) | Gênero (feminino) | 0.2306 | -0.1629 | 0.2725 |
| 30 | ln_salario_superior | Log(Salário Superior) | Gênero (feminino) | -0.1068 | 0.0323 | 0.6857 |
| 31 | ln_salario_medio | Log(Salário Médio) | Gênero (feminino) | -0.1471 | 0.0827 | 0.2584 |
| 32 | ln_admissoes_mulher | Log(Admissões Mulheres) | Gênero (feminino) | -0.0449 | -0.0135 | 0.8036 |
| 33 | ln_admissoes_homem | Log(Admissões Homens) | Gênero (feminino) | -0.0381 | -0.0066 | 0.8967 |
| 34 | ln_admissoes_jovem | Log(Admissões Jovens) | Gênero (feminino) | -0.0709 | 0.0173 | 0.7614 |
| 35 | ln_admissoes_negro | Log(Admissões Negros) | Gênero (feminino) | -0.0456 | 0.0456 | 0.3979 |
| 36 | ln_admissoes | Log(Admissões) | Educação (superior) | 0.0875 | -0.1462 | 0.0500 |
| 37 | ln_desligamentos | Log(Desligamentos) | Educação (superior) | -0.0037 | -0.0011 | 0.9875 |
| 38 | saldo | Saldo Líquido | Educação (superior) | 32.0870 | -148.4784 | 0.3556 |
| 39 | ln_salario_adm | Log(Salário Admissão Nominal) | Educação (superior) | -0.1050 | 0.0306 | 0.7787 |
| 40 | ln_salario_real_adm | Log(Salário Real Admissão) | Educação (superior) | -0.0546 | 0.0124 | 0.8555 |
| 41 | pct_superior_adm | % Superior (Admissão) | Educação (superior) | 0.0333 | -0.0476 | 0.0010 |
| 42 | ln_salario_mulher | Log(Salário Mulheres) | Educação (superior) | -0.0526 | -0.0763 | 0.4951 |
| 43 | ln_salario_homem | Log(Salário Homens) | Educação (superior) | 0.0542 | -0.1078 | 0.2799 |
| 44 | ln_salario_jovem | Log(Salário Jovens) | Educação (superior) | -0.0340 | -0.1732 | 0.2806 |
| 45 | ln_salario_naojovem | Log(Salário Não-Jovens) | Educação (superior) | 0.0811 | -0.1314 | 0.2486 |
| 46 | ln_salario_branco | Log(Salário Brancos) | Educação (superior) | -0.0689 | -0.0198 | 0.8924 |
| 47 | ln_salario_negro | Log(Salário Negros) | Educação (superior) | 0.0070 | 0.0523 | 0.6952 |
| 48 | ln_salario_superior | Log(Salário Superior) | Educação (superior) | 0.2279 | -0.6412 | 0.0000 |
| 49 | ln_salario_medio | Log(Salário Médio) | Educação (superior) | -0.0629 | -0.0900 | 0.2653 |
| 50 | ln_admissoes_mulher | Log(Admissões Mulheres) | Educação (superior) | 0.0389 | -0.1008 | 0.2335 |
| 51 | ln_admissoes_homem | Log(Admissões Homens) | Educação (superior) | 0.0684 | -0.1295 | 0.0865 |
| 52 | ln_admissoes_jovem | Log(Admissões Jovens) | Educação (superior) | 0.0740 | -0.1484 | 0.0624 |
| 53 | ln_admissoes_negro | Log(Admissões Negros) | Educação (superior) | 0.0955 | -0.1261 | 0.0745 |

</div>

#### 2.7 Event study (coeficientes por período relativo)

Coeficientes do evento (mês relativo ao lançamento do ChatGPT, t = -1 é
referência). Abaixo: outcomes principais. Arquivos completos em
`outputs/tables/event_study_*.csv`.

``` python
event_study_files = sorted(OUTPUTS_TABLES.glob("event_study_*.csv"))
print("Arquivos event study disponíveis:", [f.name for f in event_study_files])

# Exibir resumo para outcomes principais
principais = ["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_adm", "ln_salario_real_adm", "ln_salario_jovem"]
for out in principais:
    path = OUTPUTS_TABLES / f"event_study_{out}.csv"
    if path.exists():
        df_es = pd.read_csv(path)
        print(f"\n--- Event study: {out} ---")
        display(df_es.head(15))
```

    Arquivos event study disponíveis: ['event_study_ln_admissoes.csv', 'event_study_ln_admissoes_homem.csv', 'event_study_ln_admissoes_jovem.csv', 'event_study_ln_admissoes_mulher.csv', 'event_study_ln_admissoes_negro.csv', 'event_study_ln_desligamentos.csv', 'event_study_ln_salario_adm.csv', 'event_study_ln_salario_branco.csv', 'event_study_ln_salario_homem.csv', 'event_study_ln_salario_jovem.csv', 'event_study_ln_salario_medio.csv', 'event_study_ln_salario_mulher.csv', 'event_study_ln_salario_naojovem.csv', 'event_study_ln_salario_negro.csv', 'event_study_ln_salario_real_adm.csv', 'event_study_ln_salario_superior.csv', 'event_study_pct_superior_adm.csv', 'event_study_saldo.csv']

    --- Event study: ln_admissoes ---

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | t   | coef    | se     | p_value | is_reference | is_pre | ci_low  | ci_high |
|-----|-----|---------|--------|---------|--------------|--------|---------|---------|
| 0   | -12 | -0.0038 | 0.0379 | 0.9195  | False        | True   | -0.0782 | 0.0705  |
| 1   | -11 | -0.0087 | 0.0453 | 0.8481  | False        | True   | -0.0974 | 0.0801  |
| 2   | -10 | -0.0429 | 0.0572 | 0.4536  | False        | True   | -0.1550 | 0.0692  |
| 3   | -9  | -0.0502 | 0.0470 | 0.2860  | False        | True   | -0.1425 | 0.0420  |
| 4   | -8  | -0.0075 | 0.0413 | 0.8559  | False        | True   | -0.0885 | 0.0735  |
| 5   | -7  | -0.0445 | 0.0416 | 0.2854  | False        | True   | -0.1259 | 0.0370  |
| 6   | -6  | -0.0433 | 0.0366 | 0.2375  | False        | True   | -0.1150 | 0.0285  |
| 7   | -5  | -0.0527 | 0.0353 | 0.1352  | False        | True   | -0.1219 | 0.0164  |
| 8   | -4  | -0.0594 | 0.0488 | 0.2243  | False        | True   | -0.1550 | 0.0363  |
| 9   | -3  | -0.0269 | 0.0375 | 0.4739  | False        | True   | -0.1003 | 0.0466  |
| 10  | -2  | -0.0169 | 0.0332 | 0.6102  | False        | True   | -0.0821 | 0.0482  |
| 11  | -1  | 0.0000  | 0.0000 | NaN     | True         | True   | 0.0000  | 0.0000  |
| 12  | 0   | 0.0778  | 0.0359 | 0.0307  | False        | False  | 0.0074  | 0.1483  |
| 13  | 1   | 0.0089  | 0.0390 | 0.8189  | False        | False  | -0.0675 | 0.0854  |
| 14  | 2   | -0.0990 | 0.0558 | 0.0763  | False        | False  | -0.2083 | 0.0103  |

</div>


    --- Event study: ln_desligamentos ---

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | t   | coef    | se     | p_value | is_reference | is_pre | ci_low  | ci_high |
|-----|-----|---------|--------|---------|--------------|--------|---------|---------|
| 0   | -12 | 0.0392  | 0.0323 | 0.2254  | False        | True   | -0.0241 | 0.1024  |
| 1   | -11 | 0.0831  | 0.0349 | 0.0176  | False        | True   | 0.0147  | 0.1516  |
| 2   | -10 | 0.0369  | 0.0384 | 0.3367  | False        | True   | -0.0383 | 0.1122  |
| 3   | -9  | 0.0277  | 0.0336 | 0.4101  | False        | True   | -0.0382 | 0.0936  |
| 4   | -8  | 0.0756  | 0.0336 | 0.0250  | False        | True   | 0.0096  | 0.1415  |
| 5   | -7  | 0.1418  | 0.0337 | 0.0000  | False        | True   | 0.0756  | 0.2079  |
| 6   | -6  | 0.0813  | 0.0368 | 0.0276  | False        | True   | 0.0091  | 0.1535  |
| 7   | -5  | 0.0558  | 0.0378 | 0.1409  | False        | True   | -0.0184 | 0.1299  |
| 8   | -4  | 0.0301  | 0.0338 | 0.3732  | False        | True   | -0.0362 | 0.0964  |
| 9   | -3  | 0.0741  | 0.0326 | 0.0233  | False        | True   | 0.0102  | 0.1379  |
| 10  | -2  | 0.0546  | 0.0285 | 0.0557  | False        | True   | -0.0012 | 0.1104  |
| 11  | -1  | 0.0000  | 0.0000 | NaN     | True         | True   | 0.0000  | 0.0000  |
| 12  | 0   | -0.0199 | 0.0484 | 0.6814  | False        | False  | -0.1148 | 0.0750  |
| 13  | 1   | 0.0928  | 0.0354 | 0.0089  | False        | False  | 0.0235  | 0.1620  |
| 14  | 2   | 0.0618  | 0.0341 | 0.0705  | False        | False  | -0.0051 | 0.1287  |

</div>


    --- Event study: saldo ---

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | t   | coef      | se       | p_value | is_reference | is_pre | ci_low     | ci_high  |
|-----|-----|-----------|----------|---------|--------------|--------|------------|----------|
| 0   | -12 | -194.3597 | 266.2103 | 0.4656  | False        | True   | -716.1319  | 327.4125 |
| 1   | -11 | -349.4580 | 428.8335 | 0.4154  | False        | True   | -1189.9717 | 491.0557 |
| 2   | -10 | -193.2848 | 399.0517 | 0.6283  | False        | True   | -975.4261  | 588.8565 |
| 3   | -9  | -238.6669 | 337.6622 | 0.4799  | False        | True   | -900.4847  | 423.1510 |
| 4   | -8  | -269.3918 | 307.8041 | 0.3818  | False        | True   | -872.6878  | 333.9042 |
| 5   | -7  | -383.5216 | 260.0247 | 0.1407  | False        | True   | -893.1701  | 126.1268 |
| 6   | -6  | -301.7401 | 246.3585 | 0.2211  | False        | True   | -784.6027  | 181.1226 |
| 7   | -5  | -439.4320 | 273.1858 | 0.1082  | False        | True   | -974.8762  | 96.0121  |
| 8   | -4  | -321.2117 | 301.2095 | 0.2866  | False        | True   | -911.5823  | 269.1589 |
| 9   | -3  | -252.9877 | 258.9379 | 0.3289  | False        | True   | -760.5061  | 254.5306 |
| 10  | -2  | -126.9799 | 173.7076 | 0.4651  | False        | True   | -467.4468  | 213.4870 |
| 11  | -1  | 0.0000    | 0.0000   | NaN     | True         | True   | 0.0000     | 0.0000   |
| 12  | 0   | -587.3553 | 502.3584 | 0.2428  | False        | False  | -1571.9779 | 397.2673 |
| 13  | 1   | -442.1441 | 409.7918 | 0.2810  | False        | False  | -1245.3360 | 361.0479 |
| 14  | 2   | -291.8871 | 367.1464 | 0.4269  | False        | False  | -1011.4941 | 427.7198 |

</div>


    --- Event study: ln_salario_adm ---

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | t   | coef    | se     | p_value | is_reference | is_pre | ci_low  | ci_high |
|-----|-----|---------|--------|---------|--------------|--------|---------|---------|
| 0   | -12 | 0.0123  | 0.0761 | 0.8720  | False        | True   | -0.1369 | 0.1614  |
| 1   | -11 | 0.0106  | 0.0824 | 0.8979  | False        | True   | -0.1509 | 0.1721  |
| 2   | -10 | 0.0651  | 0.1076 | 0.5458  | False        | True   | -0.1459 | 0.2760  |
| 3   | -9  | -0.0083 | 0.0839 | 0.9211  | False        | True   | -0.1728 | 0.1562  |
| 4   | -8  | -0.0567 | 0.0968 | 0.5579  | False        | True   | -0.2464 | 0.1329  |
| 5   | -7  | -0.0418 | 0.0977 | 0.6687  | False        | True   | -0.2334 | 0.1497  |
| 6   | -6  | 0.0376  | 0.0975 | 0.6996  | False        | True   | -0.1535 | 0.2288  |
| 7   | -5  | -0.0402 | 0.1043 | 0.7003  | False        | True   | -0.2446 | 0.1643  |
| 8   | -4  | 0.1292  | 0.0980 | 0.1878  | False        | True   | -0.0629 | 0.3213  |
| 9   | -3  | -0.0194 | 0.0925 | 0.8337  | False        | True   | -0.2007 | 0.1619  |
| 10  | -2  | -0.0549 | 0.0956 | 0.5658  | False        | True   | -0.2424 | 0.1325  |
| 11  | -1  | 0.0000  | 0.0000 | NaN     | True         | True   | 0.0000  | 0.0000  |
| 12  | 0   | 0.0012  | 0.1054 | 0.9911  | False        | False  | -0.2053 | 0.2077  |
| 13  | 1   | 0.0809  | 0.0864 | 0.3492  | False        | False  | -0.0884 | 0.2503  |
| 14  | 2   | 0.0257  | 0.0984 | 0.7940  | False        | False  | -0.1671 | 0.2185  |

</div>


    --- Event study: ln_salario_real_adm ---

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | t   | coef    | se     | p_value | is_reference | is_pre | ci_low  | ci_high |
|-----|-----|---------|--------|---------|--------------|--------|---------|---------|
| 0   | -12 | -0.0156 | 0.0514 | 0.7614  | False        | True   | -0.1164 | 0.0852  |
| 1   | -11 | -0.0180 | 0.0580 | 0.7558  | False        | True   | -0.1316 | 0.0956  |
| 2   | -10 | 0.0157  | 0.0770 | 0.8382  | False        | True   | -0.1351 | 0.1666  |
| 3   | -9  | -0.0259 | 0.0578 | 0.6541  | False        | True   | -0.1393 | 0.0874  |
| 4   | -8  | -0.0285 | 0.0654 | 0.6633  | False        | True   | -0.1567 | 0.0997  |
| 5   | -7  | -0.0262 | 0.0663 | 0.6926  | False        | True   | -0.1562 | 0.1038  |
| 6   | -6  | -0.0001 | 0.0660 | 0.9982  | False        | True   | -0.1294 | 0.1291  |
| 7   | -5  | -0.0248 | 0.0710 | 0.7266  | False        | True   | -0.1640 | 0.1143  |
| 8   | -4  | 0.0878  | 0.0682 | 0.1981  | False        | True   | -0.0458 | 0.2214  |
| 9   | -3  | -0.0144 | 0.0651 | 0.8249  | False        | True   | -0.1421 | 0.1132  |
| 10  | -2  | -0.0289 | 0.0622 | 0.6429  | False        | True   | -0.1508 | 0.0931  |
| 11  | -1  | 0.0000  | 0.0000 | NaN     | True         | True   | 0.0000  | 0.0000  |
| 12  | 0   | -0.0330 | 0.0737 | 0.6548  | False        | False  | -0.1774 | 0.1114  |
| 13  | 1   | 0.0540  | 0.0647 | 0.4046  | False        | False  | -0.0729 | 0.1809  |
| 14  | 2   | 0.0201  | 0.0765 | 0.7929  | False        | False  | -0.1299 | 0.1701  |

</div>


    --- Event study: ln_salario_jovem ---

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | t   | coef    | se     | p_value | is_reference | is_pre | ci_low  | ci_high |
|-----|-----|---------|--------|---------|--------------|--------|---------|---------|
| 0   | -12 | 0.2473  | 0.1603 | 0.1235  | False        | True   | -0.0669 | 0.5616  |
| 1   | -11 | 0.1104  | 0.1531 | 0.4712  | False        | True   | -0.1896 | 0.4104  |
| 2   | -10 | 0.2639  | 0.1710 | 0.1233  | False        | True   | -0.0713 | 0.5990  |
| 3   | -9  | 0.0516  | 0.1552 | 0.7398  | False        | True   | -0.2526 | 0.3558  |
| 4   | -8  | 0.1100  | 0.1897 | 0.5622  | False        | True   | -0.2618 | 0.4818  |
| 5   | -7  | 0.0971  | 0.2055 | 0.6366  | False        | True   | -0.3056 | 0.4999  |
| 6   | -6  | 0.2559  | 0.1939 | 0.1873  | False        | True   | -0.1240 | 0.6359  |
| 7   | -5  | 0.2109  | 0.1664 | 0.2054  | False        | True   | -0.1152 | 0.5369  |
| 8   | -4  | 0.3670  | 0.1889 | 0.0526  | False        | True   | -0.0034 | 0.7373  |
| 9   | -3  | 0.0886  | 0.1847 | 0.6314  | False        | True   | -0.2734 | 0.4506  |
| 10  | -2  | 0.0725  | 0.1911 | 0.7047  | False        | True   | -0.3021 | 0.4470  |
| 11  | -1  | 0.0000  | 0.0000 | NaN     | True         | True   | 0.0000  | 0.0000  |
| 12  | 0   | -0.0847 | 0.2158 | 0.6947  | False        | False  | -0.5077 | 0.3382  |
| 13  | 1   | 0.1373  | 0.2224 | 0.5374  | False        | False  | -0.2987 | 0.5732  |
| 14  | 2   | 0.2700  | 0.2055 | 0.1894  | False        | False  | -0.1328 | 0.6728  |

</div>

### 3. Figuras geradas no etapa_2b

Figuras salvas em `outputs/figures` pelo notebook etapa_2b (tendências
paralelas, event study agregado, scatter exposição vs coeficiente). Se a
pasta estiver vazia, execute o notebook etapa_2b para gerá-las.

``` python
figuras = sorted(OUTPUTS_FIGURES.glob("*.png")) + sorted(OUTPUTS_FIGURES.glob("*.pdf"))
if not figuras:
    print("Nenhuma figura encontrada em", OUTPUTS_FIGURES)
    print("Execute o notebook etapa_2b_analise_did_caged_ilo.ipynb para gerar as figuras.")
else:
    for path in figuras:
        print("---", path.name, "---")
        if path.suffix.lower() == ".png":
            display(Image(filename=str(path)))
        else:
            print("(PDF: abra manualmente ou use outro viewer)")
```

    --- event_study_all_outcomes.png ---

![](etapa_2c_resultados_files/figure-commonmark/cell-11-output-2.png)

    --- parallel_trends_all_outcomes.png ---

![](etapa_2c_resultados_files/figure-commonmark/cell-11-output-4.png)

    --- scatter_automation_index_vs_did_coef.png ---

![](etapa_2c_resultados_files/figure-commonmark/cell-11-output-6.png)

### 4. Gráficos para ilustrar os achados

Gráficos construídos neste notebook a partir das tabelas do etapa_2b:
efeito DiD nos outcomes principais (Model 3) e dinâmica do event study
para um outcome emblemático.

#### 4.1 Efeito DiD (alta exposição à IA) nos outcomes principais

Coeficiente do tratamento para o modelo principal (Model 3: FE +
Controls). Barras: intervalo de confiança 95%. Cores: verde = p\<0.01,
laranja = p\<0.05, cinza = não significativo.

``` python
path = OUTPUTS_TABLES / "did_main_results.csv"
if not path.exists():
    print("Arquivo não encontrado. Execute o etapa_2b.")
else:
    df = pd.read_csv(path)
    main = df[df["model"] == "Model 3: FE + Controls (MAIN)"].copy()
    outcomes_principais = ["ln_admissoes", "ln_desligamentos", "saldo", "ln_salario_adm", "ln_salario_real_adm", "pct_superior_adm"]
    main = main[main["outcome"].isin(outcomes_principais)]
    labels = {
        "ln_admissoes": "Log(Admissões)", "ln_desligamentos": "Log(Desligamentos)", "saldo": "Saldo Líquido",
        "ln_salario_adm": "Log(Sal. Nominal)", "ln_salario_real_adm": "Log(Sal. Real)", "pct_superior_adm": "% Superior"
    }
    main["label"] = main["outcome"].map(labels)
    main["ci_lo"] = main["coef"] - 1.96 * main["se"]
    main["ci_hi"] = main["coef"] + 1.96 * main["se"]
    main["cor"] = main["p_value"].apply(lambda p: "#2e7d32" if p < 0.01 else "#ef6c00" if p < 0.05 else "#9e9e9e")
    main = main.sort_values("coef", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    y_pos = range(len(main))
    ax.barh(y_pos, main["coef"], color=main["cor"], alpha=0.85)
    ax.errorbar(main["coef"], y_pos, xerr=1.96 * main["se"], fmt="none", color="black", capsize=3)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(main["label"])
    ax.set_xlabel("Coeficiente DiD (alta exposição)")
    ax.set_title("Efeito DiD nos outcomes principais (Model 3: FE + Controls)")
    plt.tight_layout()
    plt.show()
```

![](etapa_2c_resultados_files/figure-commonmark/cell-12-output-1.png)

#### 4.2 Dinâmica do efeito: Event study (salário real de admissão)

Coeficientes por mês relativo ao lançamento do ChatGPT (t = -1 é
referência). Banda: IC 95%. Permite verificar tendências pré e evolução
pós-tratamento.

``` python
path = OUTPUTS_TABLES / "event_study_ln_salario_real_adm.csv"
if not path.exists():
    path = OUTPUTS_TABLES / "event_study_ln_salario_jovem.csv"
if path.exists():
    df_es = pd.read_csv(path)
    df_es = df_es.sort_values("t")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_es["t"], df_es["coef"], marker="o", markersize=5, color="#1f77b4")
    ax.fill_between(df_es["t"], df_es["ci_low"], df_es["ci_high"], alpha=0.3)
    ax.axhline(0, color="gray", linestyle="--")
    ax.axvline(-0.5, color="red", linestyle=":", alpha=0.7, label="Tratamento")
    ax.set_xlabel("Mês relativo ao ChatGPT (t = -1 referência)")
    ax.set_ylabel("Coeficiente")
    ax.set_title("Event study: " + ("Log(Salário Real Admissão)" if "real" in path.name else "Log(Salário Jovens)"))
    ax.legend()
    plt.tight_layout()
    plt.show()
else:
    print("Nenhum event_study_*.csv encontrado. Execute o etapa_2b.")
```

![](etapa_2c_resultados_files/figure-commonmark/cell-13-output-1.png)

#### 4.3 Tabela visual de significância (outcomes principais × modelo principal)

Heatmap: célula escura = significativo (***/**/*), clara = não
significativo. Facilita ver onde os efeitos são robustos.

``` python
path = OUTPUTS_TABLES / "did_main_results.csv"
if path.exists():
    df = pd.read_csv(path)
    main3 = df[df["model"] == "Model 3: FE + Controls (MAIN)"].copy()
    main3["sig"] = main3["p_value"].apply(lambda p: 3 if p < 0.01 else 2 if p < 0.05 else 1 if p < 0.10 else 0)
    pivot = main3.set_index("outcome")["sig"].to_frame("estrelas")
    pivot = pivot.sort_values("estrelas", ascending=False)
    fig, ax = plt.subplots(figsize=(4, max(5, len(pivot) * 0.35)))
    cmap = plt.cm.Greens
    im = ax.imshow(pivot.values, cmap=cmap, vmin=0, vmax=3, aspect="auto")
    ax.set_yticks(range(len(pivot)))
    ax.set_yticklabels(pivot.index)
    ax.set_xticks([0])
    ax.set_xticklabels(["Significância"])
    for i in range(len(pivot)):
        ax.text(0, i, "***" if pivot.iloc[i, 0] == 3 else "**" if pivot.iloc[i, 0] == 2 else "*" if pivot.iloc[i, 0] == 1 else "", ha="center", va="center")
    plt.colorbar(im, ax=ax, label="0=n.s. 1=* 2=** 3=***")
    ax.set_title("Model 3: FE + Controls (MAIN)")
    plt.tight_layout()
    plt.show()
else:
    print("Arquivo não encontrado.")
```

![](etapa_2c_resultados_files/figure-commonmark/cell-14-output-1.png)

### 5. Resumo dos achados

**Tendências paralelas:** O teste de tendências paralelas (coeficientes
pré-tratamento do event study) indica que a maioria dos outcomes
apresenta tendências paralelas entre grupos de alta e baixa exposição no
período pré-ChatGPT. Há sinal de preocupação em **Log(Desligamentos)** e
**Log(Salário Mulheres)** (p-valor conjunto pré baixo ou coeficientes
pré significativos), o que deve ser considerado na interpretação.

**Efeitos principais (Model 3: FE + Controls):** Após o lançamento do
ChatGPT, ocupações com **alta exposição à IA** apresentam, em média: (i)
**redução no salário de admissão nominal** (coef. negativo, **); (ii)
**redução no salário real de admissão\*\* (*); (iii) **aumento na
proporção de admissões com ensino superior** (**); (iv) **redução no
salário de admissão dos jovens** (**) e **redução no salário médio**
(***). Não há efeito estatisticamente significativo em admissões ou
desligamentos em nível; o saldo líquido é negativo em algumas
especificações (ex. contínuo 4d) com \* ou **.

**Robustez:** Os resultados de salário permanecem ao usar cutoff
alternativo (top 10%, 25%), placebo em 12/2021 (não significativo),
exclusão de ocupações de TI (efeito em salário nominal \*\*) e crosswalk
4d. O teste de tendências diferenciais (pré) não rejeita a hipótese de
paralelismo.

**Heterogeneidade:** A interação tratamento × **jovem** é forte para
salários (salário nominal, real, jovem, não-jovem, negro, salário médio)
e para % superior, sugerindo que **jovens em ocupações de alta
exposição** sofrem mais o efeito negativo nos salários. Há
heterogeneidade por gênero (salário jovem) e por raça (salário negro).

Em conjunto, os achados sugerem que a difusão da IA generativa está
associada a **piora nos salários de admissão** em ocupações mais
expostas, em especial para **jovens** e para cargos de **escolaridade
média**, com **aumento da share de admissões com ensino superior**
nessas ocupações — compatível com substituição de tarefas ou mudança na
composição da demanda.

### 6. Tabela-síntese de achados e relevância estatística

Tabela única com os principais achados: descrição, coeficiente, E.P.,
p-valor, significância (\*\*\* p\<0.01, \*\* p\<0.05, \* p\<0.10) e tipo
(Principal, Robustez, Heterogeneidade). **Cores:** verde = achados mais
relevantes (\*\*\* ou \*\*); âmbar = \* ou relevante; neutro = não
significativo.

``` python
# Construir tabela-síntese a partir dos CSVs
def stars(p):
    if p is None or pd.isna(p): return ""
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""

rows = []
# Model 3 principal
path_main = OUTPUTS_TABLES / "did_main_results.csv"
if path_main.exists():
    df_main = pd.read_csv(path_main)
    m3 = df_main[df_main["model"] == "Model 3: FE + Controls (MAIN)"]
    outcome_labels = {
        "ln_admissoes": "Log(Admissões)", "ln_desligamentos": "Log(Desligamentos)", "saldo": "Saldo Líquido",
        "ln_salario_adm": "Log(Sal. Nominal)", "ln_salario_real_adm": "Log(Sal. Real)", "pct_superior_adm": "% Superior",
        "ln_salario_jovem": "Log(Sal. Jovens)", "ln_salario_medio": "Log(Sal. Médio)", "ln_salario_superior": "Log(Sal. Superior)",
        "ln_salario_mulher": "Log(Sal. Mulheres)", "ln_salario_naojovem": "Log(Sal. Não-Jovens)", "ln_admissoes_mulher": "Log(Adm. Mulheres)",
        "ln_admissoes_jovem": "Log(Adm. Jovens)"
    }
    for _, r in m3.iterrows():
        out = r["outcome"]
        label = outcome_labels.get(out, out)
        s = stars(r["p_value"])
        rows.append({
            "Achado": f"Efeito DiD (alta exp.) em {label}",
            "Outcome": label,
            "Coeficiente": round(r["coef"], 4),
            "E.P.": round(r["se"], 4),
            "p-valor": round(r["p_value"], 4),
            "Sig.": s if s else "—",
            "Tipo": "Principal"
        })

# Robustez (linhas selecionadas: Top 20% e Placebo e Excl. TI)
path_rob = OUTPUTS_TABLES / "robustness_results.csv"
if path_rob.exists():
    df_rob = pd.read_csv(path_rob)
    for spec in ["Top 20% (MAIN)", "Placebo (12/2021)", "Sem ocupações TI", "Score 4d (fallback hierárquico 6 níveis)"]:
        sub = df_rob[df_rob["specification"] == spec]
        for _, r in sub.iterrows():
            s = stars(r["p_value"])
            rows.append({
                "Achado": f"Robustez: {spec} — {r['outcome']}",
                "Outcome": r["outcome"],
                "Coeficiente": round(r["coef"], 4),
                "E.P.": round(r["se"], 4),
                "p-valor": round(r["p_value"], 4),
                "Sig.": s if s else "—",
                "Tipo": "Robustez"
            })

sintese = pd.DataFrame(rows)
if sintese.empty:
    print("Nenhum dado encontrado. Execute o etapa_2b.")
else:
    # Relevância para cor: 2 = mais relevante (***/**), 1 = * ou robustez relevante, 0 = não sig.
    sintese.to_csv(OUTPUTS_TABLES / "sintese_achados_etapa2c.csv", index=False)
    # Estilo: verde para ***/**, âmbar para *, neutro para não sig.
    def highlight_relevancia(row):
        p = row["p-valor"]
        r = 2 if p < 0.05 else (1 if p < 0.10 else 0)
        if r == 2: return ["background-color: #c8e6c9"] * len(row)
        if r == 1: return ["background-color: #fff9c4"] * len(row)
        return [""] * len(row)
    styled = sintese.style.apply(highlight_relevancia, axis=1).set_caption("Síntese dos achados (verde = ***/**, âmbar = *)")
    display(styled)
```

<style type="text/css">
#T_22347_row3_col0, #T_22347_row3_col1, #T_22347_row3_col2, #T_22347_row3_col3, #T_22347_row3_col4, #T_22347_row3_col5, #T_22347_row3_col6, #T_22347_row5_col0, #T_22347_row5_col1, #T_22347_row5_col2, #T_22347_row5_col3, #T_22347_row5_col4, #T_22347_row5_col5, #T_22347_row5_col6, #T_22347_row8_col0, #T_22347_row8_col1, #T_22347_row8_col2, #T_22347_row8_col3, #T_22347_row8_col4, #T_22347_row8_col5, #T_22347_row8_col6, #T_22347_row13_col0, #T_22347_row13_col1, #T_22347_row13_col2, #T_22347_row13_col3, #T_22347_row13_col4, #T_22347_row13_col5, #T_22347_row13_col6, #T_22347_row21_col0, #T_22347_row21_col1, #T_22347_row21_col2, #T_22347_row21_col3, #T_22347_row21_col4, #T_22347_row21_col5, #T_22347_row21_col6, #T_22347_row29_col0, #T_22347_row29_col1, #T_22347_row29_col2, #T_22347_row29_col3, #T_22347_row29_col4, #T_22347_row29_col5, #T_22347_row29_col6, #T_22347_row33_col0, #T_22347_row33_col1, #T_22347_row33_col2, #T_22347_row33_col3, #T_22347_row33_col4, #T_22347_row33_col5, #T_22347_row33_col6 {
  background-color: #c8e6c9;
}
#T_22347_row4_col0, #T_22347_row4_col1, #T_22347_row4_col2, #T_22347_row4_col3, #T_22347_row4_col4, #T_22347_row4_col5, #T_22347_row4_col6, #T_22347_row12_col0, #T_22347_row12_col1, #T_22347_row12_col2, #T_22347_row12_col3, #T_22347_row12_col4, #T_22347_row12_col5, #T_22347_row12_col6, #T_22347_row14_col0, #T_22347_row14_col1, #T_22347_row14_col2, #T_22347_row14_col3, #T_22347_row14_col4, #T_22347_row14_col5, #T_22347_row14_col6, #T_22347_row16_col0, #T_22347_row16_col1, #T_22347_row16_col2, #T_22347_row16_col3, #T_22347_row16_col4, #T_22347_row16_col5, #T_22347_row16_col6, #T_22347_row32_col0, #T_22347_row32_col1, #T_22347_row32_col2, #T_22347_row32_col3, #T_22347_row32_col4, #T_22347_row32_col5, #T_22347_row32_col6 {
  background-color: #fff9c4;
}
</style>

<div id="T_22347">

Table 1: Síntese dos achados (verde = \*\*\*/\*\*, âmbar = \*)

|   | Achado | Outcome | Coeficiente | E.P. | p-valor | Sig. | Tipo |
|----|----|----|----|----|----|----|----|
| 0 | Efeito DiD (alta exp.) em Log(Admissões) | Log(Admissões) | -0.027100 | 0.026400 | 0.304600 | — | Principal |
| 1 | Efeito DiD (alta exp.) em Log(Desligamentos) | Log(Desligamentos) | 0.019000 | 0.026800 | 0.478900 | — | Principal |
| 2 | Efeito DiD (alta exp.) em Saldo Líquido | Saldo Líquido | -77.674700 | 69.625500 | 0.265000 | — | Principal |
| 3 | Efeito DiD (alta exp.) em Log(Sal. Nominal) | Log(Sal. Nominal) | -0.065600 | 0.027800 | 0.018500 | \*\* | Principal |
| 4 | Efeito DiD (alta exp.) em Log(Sal. Real) | Log(Sal. Real) | -0.034100 | 0.019300 | 0.078000 | \* | Principal |
| 5 | Efeito DiD (alta exp.) em % Superior | % Superior | 0.010300 | 0.004300 | 0.016400 | \*\* | Principal |
| 6 | Efeito DiD (alta exp.) em Log(Sal. Mulheres) | Log(Sal. Mulheres) | -0.044500 | 0.036200 | 0.219100 | — | Principal |
| 7 | Efeito DiD (alta exp.) em ln_salario_homem | ln_salario_homem | 0.003900 | 0.027000 | 0.885400 | — | Principal |
| 8 | Efeito DiD (alta exp.) em Log(Sal. Jovens) | Log(Sal. Jovens) | -0.133700 | 0.052200 | 0.010600 | \*\* | Principal |
| 9 | Efeito DiD (alta exp.) em Log(Sal. Não-Jovens) | Log(Sal. Não-Jovens) | 0.002500 | 0.027500 | 0.927700 | — | Principal |
| 10 | Efeito DiD (alta exp.) em ln_salario_branco | ln_salario_branco | -0.028500 | 0.035800 | 0.426600 | — | Principal |
| 11 | Efeito DiD (alta exp.) em ln_salario_negro | ln_salario_negro | 0.110600 | 0.067900 | 0.103800 | — | Principal |
| 12 | Efeito DiD (alta exp.) em Log(Sal. Superior) | Log(Sal. Superior) | -0.077500 | 0.040500 | 0.056200 | \* | Principal |
| 13 | Efeito DiD (alta exp.) em Log(Sal. Médio) | Log(Sal. Médio) | -0.084500 | 0.031700 | 0.007900 | \*\*\* | Principal |
| 14 | Efeito DiD (alta exp.) em Log(Adm. Mulheres) | Log(Adm. Mulheres) | -0.046700 | 0.026200 | 0.074900 | \* | Principal |
| 15 | Efeito DiD (alta exp.) em ln_admissoes_homem | ln_admissoes_homem | -0.035000 | 0.026200 | 0.182700 | — | Principal |
| 16 | Efeito DiD (alta exp.) em Log(Adm. Jovens) | Log(Adm. Jovens) | -0.055800 | 0.028700 | 0.052000 | \* | Principal |
| 17 | Efeito DiD (alta exp.) em ln_admissoes_negro | ln_admissoes_negro | -0.003200 | 0.027200 | 0.906700 | — | Principal |
| 18 | Robustez: Top 20% (MAIN) — ln_admissoes | ln_admissoes | -0.026600 | 0.026500 | 0.316600 | — | Robustez |
| 19 | Robustez: Top 20% (MAIN) — ln_desligamentos | ln_desligamentos | 0.019000 | 0.026800 | 0.478600 | — | Robustez |
| 20 | Robustez: Top 20% (MAIN) — saldo | saldo | -77.615900 | 69.638900 | 0.265500 | — | Robustez |
| 21 | Robustez: Top 20% (MAIN) — ln_salario_adm | ln_salario_adm | -0.063100 | 0.028500 | 0.027400 | \*\* | Robustez |
| 22 | Robustez: Placebo (12/2021) — ln_admissoes | ln_admissoes | 0.000000 | 0.023200 | 0.998600 | — | Robustez |
| 23 | Robustez: Placebo (12/2021) — ln_desligamentos | ln_desligamentos | 0.015100 | 0.021100 | 0.473900 | — | Robustez |
| 24 | Robustez: Placebo (12/2021) — saldo | saldo | -113.169600 | 114.524300 | 0.323500 | — | Robustez |
| 25 | Robustez: Placebo (12/2021) — ln_salario_adm | ln_salario_adm | 0.010500 | 0.032100 | 0.744800 | — | Robustez |
| 26 | Robustez: Sem ocupações TI — ln_admissoes | ln_admissoes | -0.024100 | 0.030600 | 0.431400 | — | Robustez |
| 27 | Robustez: Sem ocupações TI — ln_desligamentos | ln_desligamentos | 0.031700 | 0.031000 | 0.306500 | — | Robustez |
| 28 | Robustez: Sem ocupações TI — saldo | saldo | -92.547700 | 79.314000 | 0.243700 | — | Robustez |
| 29 | Robustez: Sem ocupações TI — ln_salario_adm | ln_salario_adm | -0.076700 | 0.032400 | 0.018100 | \*\* | Robustez |
| 30 | Robustez: Score 4d (fallback hierárquico 6 níveis) — ln_admissoes | ln_admissoes | -0.023800 | 0.026800 | 0.374300 | — | Robustez |
| 31 | Robustez: Score 4d (fallback hierárquico 6 níveis) — ln_desligamentos | ln_desligamentos | 0.019700 | 0.026400 | 0.455500 | — | Robustez |
| 32 | Robustez: Score 4d (fallback hierárquico 6 níveis) — saldo | saldo | -142.337700 | 73.475300 | 0.053200 | \* | Robustez |
| 33 | Robustez: Score 4d (fallback hierárquico 6 níveis) — ln_salario_adm | ln_salario_adm | -0.063500 | 0.028300 | 0.025200 | \*\* | Robustez |

</div>

### 7. Nota sobre reprodução

Todos os inputs deste notebook (tabelas em `outputs/tables` e figuras em
`outputs/figures`) são gerados pelo **notebook
etapa_2b_analise_did_caged_ilo.ipynb**. Para reproduzir os resultados do
zero, execute primeiro o
**etapa_2a_preparacao_dados_did_caged_ilo.ipynb** (preparação do painel)
e em seguida o **etapa_2b** (análise DiD). Depois, execute este notebook
(etapa_2c) para consolidar e visualizar os achados.

---

<!-- fonte: etapa_3a_preparacao_dados_did_municipio_conectividade.ipynb -->

# ETAPA 3a — Preparação do Painel CAGED × Município × Conectividade
(Anatel)


**Dissertação:** Inteligência Artificial Generativa e o Mercado de
Trabalho Brasileiro.

**Aluno:** Manoel Brasil Orlandi

------------------------------------------------------------------------

### Contextualização

A Etapa 2 estimou o efeito médio nacional da IA generativa sobre o
emprego formal. O efeito médio mascara **heterogeneidade espacial**: a
penetração de banda larga varia fortemente entre municípios. A Etapa 3
explora isso via **Triple-DiD**, adicionando a dimensão municipal de
conectividade (Anatel). Hipótese: o efeito da IA é **amplificado** em
municípios com alta conectividade.

### Objetivo

Construir painel **ocupação (CBO 4d) × município × mês** com CAGED,
exposição à IA (Etapa 2a) e índice de conectividade municipal.
**Saída:** `data/output/painel_caged_municipio_anatel.parquet`.

### Ficha Técnica dos Dados

| Campo | CAGED | Anatel BLF | IBGE |
|----|----|----|----|
| Fonte | MTE / CAGED | Anatel / SCM | IBGE / Censo |
| Período | Jan/2021 – Jun/2025 | 2021–Out/2022 (pré-trat.) | 2022 |
| Unidade | Movimentação | Acesso banda larga | Município |
| Granularidade | Ocupação × Município × Mês | Município × mês | Município |

### Referências

- Autor & Dorn (2013); Hjort & Poulsen (2019); Goldfarb & Tucker (2019);
  Webb (2020); Felten et al. (2021).

### 1. Configuração do ambiente

Paths, parâmetros e dependências. Conectividade medida em período
**pré-tratamento** (Jan–Out/2022) para evitar endogeneidade.

``` python
# Etapa 3a.1 — Configuração
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# Sempre usar a pasta notebook/data (raiz = pasta que contém 'notebook')
def _find_project_root():
    p = Path.cwd().resolve()
    for _ in range(5):
        if (p / "notebook").is_dir():
            return p
        p = p.parent if p.parent != p else p
    return Path.cwd().resolve()
PROJECT_ROOT = _find_project_root()
DATA_ROOT = PROJECT_ROOT / "notebook" / "data"

DATA_INPUT     = DATA_ROOT / "input"
DATA_RAW       = DATA_ROOT / "raw"
DATA_PROCESSED = DATA_ROOT / "processed"
DATA_OUTPUT    = DATA_ROOT / "output"
OUTPUTS_TABLES = PROJECT_ROOT / "notebook" / "outputs" / "tables"
for d in [DATA_INPUT, DATA_RAW, DATA_PROCESSED, DATA_OUTPUT, OUTPUTS_TABLES]:
    d.mkdir(parents=True, exist_ok=True)

# Cache CAGED municipal: para forçar nova agregação (ex.: faixa etária), use USE_CAGED_CACHE = False ou apague o arquivo
USE_CAGED_CACHE = False
CAGED_CACHE_FILE = DATA_PROCESSED / "painel_caged_municipio.parquet"
PAINEL_CAGED_MUN = CAGED_CACHE_FILE

GCP_PROJECT_ID = "mestrado-pnad-2026"
ANO_INICIO, ANO_FIM = 2021, 2025
ANO_TRATAMENTO, MES_TRATAMENTO = 2022, 12
ANO_PRE_CONECT, MES_FIM_PRE_CONECT = 2022, 10
MIN_POPULACAO = 50_000
MIN_MOVIMENTACOES_PRE = 5

PAINEL_ETAPA2 = DATA_OUTPUT / "painel_caged_did_ready.parquet"
IPCA_FILE = DATA_PROCESSED / "ipca_mensal.parquet"
ANATEL_PRE_FILE = DATA_PROCESSED / "anatel_pre_tratamento.parquet"
IBGE_FILE = DATA_PROCESSED / "ibge_municipios.parquet"
CONECTIVIDADE_FILE = DATA_PROCESSED / "conectividade_municipal.parquet"
PAINEL_FINAL = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
PAINEL_FINAL_V2 = DATA_OUTPUT / "painel_caged_municipio_anatel_v2.parquet"

print("Data root:", DATA_ROOT.resolve())
print("Cache CAGED:", CAGED_CACHE_FILE.resolve(), "(existe:", CAGED_CACHE_FILE.exists(), ", use_cache:", USE_CAGED_CACHE, ")")
print("Configuração carregada. Período pré conectividade: até", f"{MES_FIM_PRE_CONECT}/{ANO_PRE_CONECT}")
```

    Data root: /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/data
    Cache CAGED: /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/data/processed/painel_caged_municipio.parquet (existe: True , use_cache: False )
    Configuração carregada. Período pré conectividade: até 10/2022

### 2. Anatel — Banda Larga Fixa

Download via BigQuery (Base dos Dados). Período pré-tratamento: 2021 e
Jan–Out/2022. Agregado por município: média de acessos e % fibra.

``` python
# Etapa 3a.2 — Anatel (ou carregar do cache)
if ANATEL_PRE_FILE.exists():
    df_anatel = pd.read_parquet(ANATEL_PRE_FILE)
    print(f"Anatel carregado do cache: {len(df_anatel):,} municípios")
else:
    query_anatel = f'''
    SELECT ano, mes, id_municipio,
           SUM(acessos) AS total_acessos,
           SUM(CASE WHEN LOWER(SAFE_CAST(tecnologia AS STRING)) LIKE '%fibra%' THEN acessos ELSE 0 END) AS acessos_fibra
    FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
    WHERE ano IN (2021, {ANO_PRE_CONECT}) AND (ano < {ANO_PRE_CONECT} OR mes <= {MES_FIM_PRE_CONECT})
    GROUP BY ano, mes, id_municipio
    '''
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT_ID)
        df = client.query(query_anatel).to_dataframe(create_bqstorage_client=True)
    except Exception as e:
        import basedosdados as bd
        df = bd.read_sql(query_anatel, billing_project_id=GCP_PROJECT_ID)
    out = df.groupby("id_municipio").agg(
        media_acessos_pre=("total_acessos", "mean"),
        soma_acessos=("total_acessos", "sum"),
        soma_fibra=("acessos_fibra", "sum"),
    ).reset_index()
    out["pct_fibra_pre"] = out["soma_fibra"] / out["soma_acessos"].clip(lower=1)
    df_anatel = out[["id_municipio", "media_acessos_pre", "pct_fibra_pre"]]
    df_anatel.to_parquet(ANATEL_PRE_FILE, index=False)
    print(f"Anatel salvo: {len(df_anatel):,} municípios")
df_anatel.head()
```

    Anatel carregado do cache: 5,570 municípios

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | id_municipio | media_acessos_pre | pct_fibra_pre |
|-----|--------------|-------------------|---------------|
| 0   | 1100015      | 1771.0            | 0.0           |
| 1   | 1100023      | 19923.5           | 0.0           |
| 2   | 1100031      | 169.636364        | 0.0           |
| 3   | 1100049      | 14243.272727      | 0.0           |
| 4   | 1100056      | 1107.636364       | 0.0           |

</div>

### 3. IBGE — Domicílios, PIB, População

População (2022), PIB municipal (2021), domicílios (Censo 2022 ou proxy)
para denominador da penetração e filtro de porte.

``` python
# Etapa 3a.3 — IBGE
# Nota: tabela br_ibge_pib.municipio tem apenas id_municipio e pib; população vem de br_ibge_populacao.municipio.
if IBGE_FILE.exists():
    df_ibge = pd.read_parquet(IBGE_FILE)
    print(f"IBGE carregado do cache: {len(df_ibge):,} municípios")
else:
    q_pop = "SELECT id_municipio, populacao FROM `basedosdados.br_ibge_populacao.municipio` WHERE ano = 2022"
    q_pib = "SELECT id_municipio, pib FROM `basedosdados.br_ibge_pib.municipio` WHERE ano = 2021"
    use_bq = False
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT_ID)
        df_pop = client.query(q_pop).to_dataframe(create_bqstorage_client=True)
        df_pib = client.query(q_pib).to_dataframe(create_bqstorage_client=True)
        use_bq = True
    except Exception:
        import basedosdados as bd
        df_pop = bd.read_sql(q_pop, billing_project_id=GCP_PROJECT_ID)
        df_pib = bd.read_sql(q_pib, billing_project_id=GCP_PROJECT_ID)
    df_ibge = df_pop.merge(df_pib[["id_municipio", "pib"]], on="id_municipio", how="outer")
    df_ibge["pib_per_capita"] = df_ibge["pib"] / df_ibge["populacao"].clip(lower=1)
    try:
        q_dom = "SELECT id_municipio, SUM(domicilios_particulares_ocupados) AS domicilios FROM `basedosdados.br_ibge_censo_2022.setor_censitario` GROUP BY id_municipio"
        if use_bq:
            df_dom = client.query(q_dom).to_dataframe(create_bqstorage_client=True)
        else:
            import basedosdados as bd
            df_dom = bd.read_sql(q_dom, billing_project_id=GCP_PROJECT_ID)
        df_ibge = df_ibge.merge(df_dom, on="id_municipio", how="left")
    except Exception:
        df_ibge["domicilios"] = (df_ibge["populacao"] / 3).round().clip(lower=1)
    if "domicilios" not in df_ibge.columns:
        df_ibge["domicilios"] = (df_ibge["populacao"] / 3).round().clip(lower=1)
    df_ibge = df_ibge[["id_municipio", "populacao", "domicilios", "pib", "pib_per_capita"]]
    df_ibge.to_parquet(IBGE_FILE, index=False)
    print(f"IBGE salvo: {len(df_ibge):,} municípios")
df_ibge.head()
```

    IBGE carregado do cache: 5,570 municípios

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|     | id_municipio | populacao | domicilios | pib        | pib_per_capita |
|-----|--------------|-----------|------------|------------|----------------|
| 0   | 1100015      | 21494     | 7699       | 734469000  | 34170.884898   |
| 1   | 1100023      | 96833     | 34784      | 3209761000 | 33147.387771   |
| 2   | 1100031      | 5351      | 1967       | 238412000  | 44554.66268    |
| 3   | 1100049      | 86887     | 31931      | 2792383000 | 32138.09891    |
| 4   | 1100056      | 15890     | 5876       | 743037000  | 46761.296413   |

</div>

### 4. Índice de Conectividade Municipal

Merge Anatel + IBGE. **penetracao_bl** = media_acessos_pre / domicilios.
**alta_conectividade** = 1 se penetração \> mediana. Filtrar municípios
com população ≥ MIN_POPULACAO.

``` python
# Etapa 3a.4 — Conectividade
df_anatel = pd.read_parquet(ANATEL_PRE_FILE)
df_ibge = pd.read_parquet(IBGE_FILE)
for d in [df_anatel, df_ibge]:
    d["id_municipio"] = d["id_municipio"].astype(str).str.zfill(7)
df_conect = df_anatel.merge(df_ibge, on="id_municipio", how="inner")
df_conect["penetracao_bl"] = df_conect["media_acessos_pre"] / df_conect["domicilios"].clip(lower=1)
med = df_conect["penetracao_bl"].median()
df_conect["alta_conectividade"] = (df_conect["penetracao_bl"] > med).astype(int)
df_conect["conectividade_q75"] = (df_conect["penetracao_bl"] > df_conect["penetracao_bl"].quantile(0.75)).astype(int)
df_conect["conectividade_q25"] = (df_conect["penetracao_bl"] > df_conect["penetracao_bl"].quantile(0.25)).astype(int)
# % fibra óptica como proxy alternativo de qualidade (cutoff por mediana)
mediana_fibra = df_conect["pct_fibra_pre"].median()
df_conect["alta_fibra"] = (df_conect["pct_fibra_pre"] > mediana_fibra).astype(int)
df_conect = df_conect[df_conect["populacao"] >= MIN_POPULACAO].copy()
df_conect.to_parquet(CONECTIVIDADE_FILE, index=False)
print(f"Mediana penetração: {med:.4f}. Alta conect.: {df_conect['alta_conectividade'].sum():,} municípios. Total: {len(df_conect):,}")
```

    Mediana penetração: 0.2681. Alta conect.: 529 municípios. Total: 657

### 5. CAGED — Agregação por Ocupação × Município × Período

Reagregar microdados CAGED (data/raw/caged\_{ano}.parquet) por
**(cbo_4d, id_municipio, ano, mes)** com as mesmas métricas da Etapa 2a.
Inclui sigla_uf e **decomposição por faixa etária** (jovem \<30,
intermediário 30–49, senior 50+): adm_jovem, adm_intermediario,
adm_senior e salário médio por faixa. Processamento ano a ano para
evitar OOM.

**Nota:** Se o cache foi gerado antes da inclusão da faixa etária, use
na seção 1 `USE_CAGED_CACHE = False` e execute de novo, ou apague o
arquivo em `notebook/data/processed/painel_caged_municipio.parquet`.

``` python
# Etapa 3a.5 — CAGED municipal (ou carregar do cache)
# Agregação por (cbo_4d, id_municipio, ano, mes) — mesmas métricas da Etapa 2a. Sexo: 1=Masculino, 3=Feminino.
import time
CODIGO_SEXO_MULHER = 3
CODIGOS_RACA_BRANCA, CODIGOS_RACA_NEGRA = [1], [2, 4]
IDADE_CORTE_JOVEM = 29
CODIGOS_ESCOLARIDADE_SUPERIOR = ["9", "10", "11", "12", "13"]
CNAE_SECOES_TECNOLOGICO = ["J"]
SETOR_TECNOLOGICO_LIMIAR = 0.5

def processar_ano_caged_mun(ano):
    """Agrega um ano de CAGED por (cbo_4d, id_municipio, ano, mes)."""
    t0 = time.time()
    df = pd.read_parquet(DATA_RAW / f"caged_{ano}.parquet")
    print(f"  [{ano}] Carregado: {len(df):,} registros ({time.time()-t0:.0f}s)")
    df["cbo_2002"] = df["cbo_2002"].astype(str).str.strip()
    df["cbo_4d"] = df["cbo_2002"].str[:4]
    df = df[df["cbo_4d"].str.len() == 4]
    df = df[df["cbo_4d"].str.isdigit()]
    df = df[~df["cbo_4d"].isin(["0000", "nan", ""])]
    df["is_mulher"] = (df["sexo"].astype(str) == str(CODIGO_SEXO_MULHER)).astype(float)
    raca_str = df["raca_cor"].astype(str)
    df["is_branco"] = raca_str.isin([str(c) for c in CODIGOS_RACA_BRANCA]).astype(float)
    df["is_negro"] = raca_str.isin([str(c) for c in CODIGOS_RACA_NEGRA]).astype(float)
    df["is_jovem"] = (df["idade"] <= IDADE_CORTE_JOVEM).astype(float)
    df["is_intermediario"] = ((df["idade"] >= 30) & (df["idade"] < 50)).astype(float)
    df["is_senior"] = (df["idade"] >= 50).astype(float)
    df["is_superior"] = df["grau_instrucao"].astype(str).isin(CODIGOS_ESCOLARIDADE_SUPERIOR).astype(float)
    df["is_setor_tech"] = df["cnae_2_secao"].astype(str).str.strip().isin(CNAE_SECOES_TECNOLOGICO).astype(float)
    df_adm = df[df["saldo_movimentacao"] == 1].copy()
    df_desl = df[df["saldo_movimentacao"] == -1]
    print(f"  [{ano}] Admissões: {len(df_adm):,} | Desligamentos: {len(df_desl):,}")
    df_adm["sal_mulher"] = np.where(df_adm["is_mulher"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_homem"] = np.where(df_adm["is_mulher"] == 0, df_adm["salario_mensal"], np.nan)
    df_adm["sal_branco"] = np.where(df_adm["is_branco"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_negro"] = np.where(df_adm["is_negro"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_jovem"] = np.where(df_adm["is_jovem"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_naojovem"] = np.where(df_adm["is_jovem"] == 0, df_adm["salario_mensal"], np.nan)
    df_adm["sal_intermediario"] = np.where(df_adm["is_intermediario"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_senior"] = np.where(df_adm["is_senior"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_sup"] = np.where(df_adm["is_superior"] == 1, df_adm["salario_mensal"], np.nan)
    df_adm["sal_med"] = np.where(df_adm["is_superior"] == 0, df_adm["salario_mensal"], np.nan)
    df_adm["is_homem"] = 1 - df_adm["is_mulher"]
    grp = ["cbo_4d", "id_municipio", "ano", "mes"]
    painel_adm = df_adm.groupby(grp).agg(
        sigla_uf=("sigla_uf", "first"),
        admissoes=("saldo_movimentacao", "count"),
        salario_medio_adm=("salario_mensal", "mean"),
        idade_media_adm=("idade", "mean"),
        pct_mulher_adm=("is_mulher", "mean"),
        pct_superior_adm=("is_superior", "mean"),
        pct_branco_adm=("is_branco", "mean"),
        pct_negro_adm=("is_negro", "mean"),
        pct_jovem_adm=("is_jovem", "mean"),
        pct_tecnologico_adm=("is_setor_tech", "mean"),
        salario_medio_mulher=("sal_mulher", "mean"),
        salario_medio_homem=("sal_homem", "mean"),
        salario_medio_branco=("sal_branco", "mean"),
        salario_medio_negro=("sal_negro", "mean"),
        salario_medio_jovem=("sal_jovem", "mean"),
        salario_medio_naojovem=("sal_naojovem", "mean"),
        salario_medio_intermediario=("sal_intermediario", "mean"),
        salario_medio_senior=("sal_senior", "mean"),
        salario_medio_superior=("sal_sup", "mean"),
        salario_medio_medio=("sal_med", "mean"),
        admissoes_mulher=("is_mulher", "sum"),
        admissoes_homem=("is_homem", "sum"),
        admissoes_jovem=("is_jovem", "sum"),
        adm_jovem=("is_jovem", "sum"),
        adm_intermediario=("is_intermediario", "sum"),
        adm_senior=("is_senior", "sum"),
        admissoes_negro=("is_negro", "sum"),
    ).reset_index()
    mediana = df_adm.groupby(grp)["salario_mensal"].median().reset_index().rename(columns={"salario_mensal": "salario_mediano_adm"})
    painel_adm = painel_adm.merge(mediana, on=grp, how="left")
    painel_desl = df_desl.groupby(grp).agg(
        desligamentos=("saldo_movimentacao", "count"),
        salario_medio_desl=("salario_mensal", "mean"),
    ).reset_index()
    p = painel_adm.merge(painel_desl, on=grp, how="outer").fillna(0)
    p["saldo"] = p["admissoes"] - p["desligamentos"]
    p["n_movimentacoes"] = p["admissoes"] + p["desligamentos"]
    p["setor_tecnologico"] = (p["pct_tecnologico_adm"] >= SETOR_TECNOLOGICO_LIMIAR).astype(int)
    p["periodo"] = p["ano"].astype(int).astype(str) + "-" + p["mes"].astype(int).astype(str).str.zfill(2)
    p["periodo_num"] = p["ano"].astype(int) * 100 + p["mes"].astype(int)
    p["post"] = (p["periodo_num"] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)
    p["ln_admissoes"] = np.log(p["admissoes"] + 1)
    p["ln_desligamentos"] = np.log(p["desligamentos"] + 1)
    p["ln_salario_adm"] = np.log(p["salario_medio_adm"].clip(lower=1))
    p["cbo_2d"] = p["cbo_4d"].str[:2]
    for grp_name in ["mulher", "homem", "branco", "negro", "jovem", "naojovem", "superior", "medio"]:
        col = f"salario_medio_{grp_name}"
        if col in p.columns:
            p[f"ln_salario_{grp_name}"] = np.log(p[col].clip(lower=1))
    for grp_name in ["mulher", "homem", "jovem", "negro"]:
        col = f"admissoes_{grp_name}"
        if col in p.columns:
            p[f"ln_admissoes_{grp_name}"] = np.log(p[col].astype(float) + 1)
    print(f"  [{ano}] Painel: {len(p):,} linhas ({time.time()-t0:.0f}s)")
    del df, df_adm, df_desl
    return p

if USE_CAGED_CACHE and CAGED_CACHE_FILE.exists():
    df_caged = pd.read_parquet(CAGED_CACHE_FILE)
    print(f"CAGED municipal carregado do cache: {CAGED_CACHE_FILE.resolve()}")
    print(f"  {len(df_caged):,} linhas, {df_caged['id_municipio'].nunique():,} municípios")
else:
    print("ETAPA 3a — Agregação CAGED por ocupação × município × período")
    t0 = time.time()
    paineis = [processar_ano_caged_mun(ano) for ano in range(ANO_INICIO, ANO_FIM + 1)]
    painel = pd.concat(paineis, ignore_index=True)
    painel["id_municipio"] = painel["id_municipio"].astype(str).str.zfill(7)
    # Garantir colunas texto como string para o PyArrow (evitar ArrowTypeError por tipo object misto)
    for col in ["sigla_uf", "cbo_4d", "cbo_2d", "periodo"]:
        if col in painel.columns:
            painel[col] = painel[col].astype(str)
    painel.to_parquet(CAGED_CACHE_FILE, index=False)
    print(f"Total: {len(painel):,} linhas | {painel['cbo_4d'].nunique()} ocupações | {painel['id_municipio'].nunique()} municípios | {painel['periodo'].nunique()} períodos | salvo em {time.time()-t0:.0f}s")
    df_caged = painel
df_caged["id_municipio"] = df_caged["id_municipio"].astype(str).str.zfill(7)
df_caged.head()
```

    ETAPA 3a — Agregação CAGED por ocupação × município × período
      [2021] Carregado: 36,554,795 registros (7s)
      [2021] Admissões: 19,703,604 | Desligamentos: 16,851,191
      [2021] Painel: 2,627,059 linhas (115s)
      [2022] Carregado: 42,475,516 registros (7s)
      [2022] Admissões: 22,243,441 | Desligamentos: 20,232,075
      [2022] Painel: 2,868,327 linhas (137s)
      [2023] Carregado: 44,485,982 registros (9s)
      [2023] Admissões: 22,982,161 | Desligamentos: 21,503,821
      [2023] Painel: 2,945,596 linhas (145s)
      [2024] Carregado: 48,996,040 registros (10s)
      [2024] Admissões: 25,336,277 | Desligamentos: 23,659,763
      [2024] Painel: 3,056,122 linhas (156s)
      [2025] Carregado: 26,312,103 registros (4s)
      [2025] Admissões: 13,763,059 | Desligamentos: 12,549,044
      [2025] Painel: 1,597,780 linhas (76s)
    Total: 13,094,884 linhas | 629 ocupações | 5570 municípios | 54 períodos | salvo em 689s

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | cbo_4d | id_municipio | ano | mes | sigla_uf | admissoes | salario_medio_adm | idade_media_adm | pct_mulher_adm | pct_superior_adm | ... | ln_salario_branco | ln_salario_negro | ln_salario_jovem | ln_salario_naojovem | ln_salario_superior | ln_salario_medio | ln_admissoes_mulher | ln_admissoes_homem | ln_admissoes_jovem | ln_admissoes_negro |
|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
| 0 | 1010 | 1100015 | 2021 | 2 | RO | 1 | 1178.0 | 21.0 | 0.0 | 0.0 | ... | 0.0 | 0.0 | 7.071573 | 0.000000 | 0.0 | 7.071573 | 0.000000 | 0.693147 | 0.693147 | 0.0 |
| 1 | 1010 | 1100023 | 2021 | 5 | RO | 1 | 1243.0 | 40.0 | 1.0 | 0.0 | ... | 0.0 | 0.0 | 0.000000 | 7.125283 | 0.0 | 7.125283 | 0.693147 | 0.000000 | 0.000000 | 0.0 |
| 2 | 1010 | 1100056 | 2021 | 10 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | ... | 0.0 | 0.0 | 0.000000 | 0.000000 | 0.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.0 |
| 3 | 1010 | 1100205 | 2021 | 1 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | ... | 0.0 | 0.0 | 0.000000 | 0.000000 | 0.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.0 |
| 4 | 1010 | 1100205 | 2021 | 5 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | ... | 0.0 | 0.0 | 0.000000 | 0.000000 | 0.0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.0 |

<p>5 rows × 56 columns</p>
</div>

### 6. Merge — Painel Tridimensional

Merge CAGED municipal + exposição (Etapa 2, uma linha por cbo_4d) +
conectividade. Variáveis temporais (post, tempo_relativo_meses) e
interações DDD (triple_did, post_alta_exp, post_alta_conect). Salário
real com IPCA.

``` python
# Etapa 3a.6 — Merge
painel2 = pd.read_parquet(PAINEL_ETAPA2)
cols_exp = ["cbo_4d", "exposure_score_2d", "exposure_score_4d", "alta_exp", "alta_exp_4d",
            "alta_exp_10", "alta_exp_25", "alta_exp_mediana", "quintil_exp",
            "grande_grupo_cbo", "grande_grupo_nome", "anthropic_automation_index", "is_automation", "is_augmentation"]
cols_exp = [c for c in cols_exp if c in painel2.columns]
df_exposure = painel2[cols_exp].drop_duplicates("cbo_4d")

df = df_caged.merge(df_exposure, on="cbo_4d", how="inner")
df = df.merge(
    df_conect[["id_municipio", "penetracao_bl", "pct_fibra_pre", "alta_conectividade", "alta_fibra", "conectividade_q75", "conectividade_q25", "pib_per_capita", "populacao"]],
    on="id_municipio", how="inner"
)
df["periodo_dt"] = pd.to_datetime(df["periodo"] + "-01", errors="coerce")
df["post"] = (df["periodo_dt"] >= f"{ANO_TRATAMENTO}-{MES_TRATAMENTO:02d}-01").astype(int)
df["tempo_relativo_meses"] = (df["periodo_dt"].dt.year - ANO_TRATAMENTO) * 12 + (df["periodo_dt"].dt.month - MES_TRATAMENTO)
df["uf_periodo"] = df["sigla_uf"].astype(str) + "_" + df["periodo"].astype(str)
df["post_alta_exp"] = df["post"] * df["alta_exp"]
df["post_alta_conect"] = df["post"] * df["alta_conectividade"]
df["alta_exp_alta_conect"] = df["alta_exp"] * df["alta_conectividade"]
df["triple_did"] = df["post"] * df["alta_exp"] * df["alta_conectividade"]
# Interações para Triple-DiD com proxy fibra
df["post_alta_fibra"] = df["post"] * df["alta_fibra"]
df["alta_exp_alta_fibra"] = df["alta_exp"] * df["alta_fibra"]
df["triple_did_fibra"] = df["post"] * df["alta_exp"] * df["alta_fibra"]
# Dummy capital estadual (proxy extrema de conectividade para robustez no 3b)
capitais_ibge = ["1100205", "1200401", "1302603", "1400100", "1501402", "1600303", "1721000", "2111300", "2211001", "2304400", "2408102", "2507507", "2611606", "2704302", "2800308", "2927408", "3106200", "3205309", "3304557", "3550308", "4106902", "4205407", "4314902", "5002704", "5103403", "5208707", "5300108"]
df["capital"] = df["id_municipio"].astype(str).str.zfill(7).isin(capitais_ibge).astype(int)

if IPCA_FILE.exists():
    df_ipca = pd.read_parquet(IPCA_FILE)
    df = df.merge(df_ipca[["ano", "mes", "indice"]], on=["ano", "mes"], how="left")
    df["salario_real_adm"] = df["salario_medio_adm"] * (100.0 / df["indice"].clip(lower=0.01))
else:
    df["salario_real_adm"] = df["salario_medio_adm"]
df["ln_salario_real_adm"] = np.log(df["salario_real_adm"].clip(lower=1))
df["ln_pib_pc"] = np.log(df["pib_per_capita"].clip(lower=1))

if MIN_MOVIMENTACOES_PRE > 0:
    pre = df["post"] == 0
    mov = df.loc[pre].groupby(["cbo_4d", "id_municipio"])["n_movimentacoes"].sum().reset_index()
    mov.columns = ["cbo_4d", "id_municipio", "mov_pre"]
    df = df.merge(mov, on=["cbo_4d", "id_municipio"], how="left")
    df = df[df["mov_pre"] >= MIN_MOVIMENTACOES_PRE].drop(columns=["mov_pre"])
print(f"Painel final: {len(df):,} linhas | {df['cbo_4d'].nunique()} ocupações | {df['id_municipio'].nunique()} municípios | {df['periodo'].nunique()} períodos")
```

    Painel final: 5,534,808 linhas | 614 ocupações | 657 municípios | 54 períodos

### 7. Validação e Estatísticas Descritivas

Balanço pré por grupo de conectividade; distribuição de penetração;
correlação penetração × PIB per capita.

``` python
# Etapa 3a.7 — Validação
pre = df[df["post"] == 0]
print("Balanço pré-tratamento por conectividade:")
print(pre.groupby("alta_conectividade").agg(
    n_obs=("cbo_4d", "count"),
    admissoes_media=("admissoes", "mean"),
    salario_medio=("salario_medio_adm", "mean"),
    penetracao_media=("penetracao_bl", "mean"),
).round(2))
print("\nCorrelação penetração × PIB per capita:", df_conect["penetracao_bl"].corr(df_conect["pib_per_capita"]).round(3))
```

    Balanço pré-tratamento por conectividade:
                          n_obs  admissoes_media  salario_medio  penetracao_media
    alta_conectividade                                                           
    0                    205077             5.02        8230.56              0.18
    1                   2126257            15.02        3991.63              0.69

    Correlação penetração × PIB per capita: 0.304

### 8. Exportação

Salvar painel final em parquet e tabela de conectividade em CSV.

``` python
# Etapa 3a.8 — Exportação
df.to_parquet(PAINEL_FINAL, index=False)
df_conect.to_csv(OUTPUTS_TABLES / "conectividade_municipal.csv", index=False)
print(f"Painel salvo: {PAINEL_FINAL} ({PAINEL_FINAL.stat().st_size/1e6:.1f} MB)")
print(f"Conectividade: {OUTPUTS_TABLES / 'conectividade_municipal.csv'}")
```

    Painel salvo: /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/data/output/painel_caged_municipio_anatel.parquet (635.3 MB)
    Conectividade: /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/outputs/tables/conectividade_municipal.csv

### 9. Decomposição por Faixa Etária e Exportação v2

Construir outcomes desagregados por faixa etária (jovem \<30,
intermediário 30–49, senior 50+) para o Triple-DiD etário no Notebook
3b: share de jovens/seniores nas admissões, log-admissões e log-salário
real por faixa, razão salarial jovem/senior.

**Nota:** Células ocupação×município×mês sem admissões em alguma faixa
terão NaN; regressões com outcomes por faixa no 3b terão menos
observações (perda amostral esperada).

``` python
# Etapa 3a.9 — Decomposição por Faixa Etária e Re-exportação v2
colunas_faixa = ["adm_jovem", "adm_intermediario", "adm_senior", "salario_medio_jovem", "salario_medio_intermediario", "salario_medio_senior"]
if not all(c in df.columns for c in colunas_faixa):
    print("AVISO: Painel sem colunas de faixa etária (adm_jovem, adm_intermediario, adm_senior, etc.).")
    print("Rode a seção 5 com USE_CAGED_CACHE = False na seção 1, ou apague o cache:", CAGED_CACHE_FILE.resolve())
else:
    # adm_total = soma das três faixas (pode diferir de admissoes se houver missings de idade)
    df["adm_total"] = df["adm_jovem"].fillna(0) + df["adm_intermediario"].fillna(0) + df["adm_senior"].fillna(0)
    df["adm_total"] = df["adm_total"].replace(0, np.nan)
    df["share_jovem"] = df["adm_jovem"] / df["adm_total"]
    df["share_senior"] = df["adm_senior"] / df["adm_total"]
    df["ln_adm_jovem"] = np.log1p(df["adm_jovem"].fillna(0))
    df["ln_adm_intermediario"] = np.log1p(df["adm_intermediario"].fillna(0))
    df["ln_adm_senior"] = np.log1p(df["adm_senior"].fillna(0))
    # Salário real por faixa (deflator = indice IPCA, mesmo que ln_salario_real_adm)
    if "indice" in df.columns:
        deflator = df["indice"] / 100.0
    else:
        deflator = 1.0
    for faixa in ["jovem", "intermediario", "senior"]:
        col_sal = f"salario_medio_{faixa}"
        df[f"sal_real_{faixa}"] = df[col_sal] / deflator
        df[f"ln_sal_real_{faixa}"] = np.log(df[f"sal_real_{faixa}"].clip(lower=1))
    df["razao_sal_jovem_senior"] = df["sal_real_jovem"] / df["sal_real_senior"].replace(0, np.nan)
    # Re-exportar painel v2 com todas as variáveis (faixa etária, fibra, capital)
    df.to_parquet(PAINEL_FINAL_V2, index=False)
    print(f"Painel v2 salvo: {PAINEL_FINAL_V2} ({PAINEL_FINAL_V2.stat().st_size/1e6:.1f} MB)")
    print(f"Variáveis: share_jovem, share_senior, ln_adm_* por faixa, ln_sal_real_* por faixa, razao_sal_jovem_senior, alta_fibra, triple_did_fibra, capital")
```

    Painel v2 salvo: /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/data/output/painel_caged_municipio_anatel_v2.parquet (803.2 MB)
    Variáveis: share_jovem, share_senior, ln_adm_* por faixa, ln_sal_real_* por faixa, razao_sal_jovem_senior, alta_fibra, triple_did_fibra, capital

---

<!-- fonte: etapa_3b_analise_did_municipio_conectividade.ipynb -->

# ETAPA 3b — Análise Triple-DiD: IA Generativa, Conectividade e Emprego
Formal


**Dissertação:** Inteligência Artificial Generativa e o Mercado de
Trabalho Brasileiro.

**Objetivo:** Estimar o efeito diferencial da IA generativa entre
municípios de alta e baixa conectividade (Triple-DiD). Unidade: ocupação
× município × mês. Coeficiente de interesse: **β₇** (triple_did = post ×
alta_exp × alta_conectividade).

**Input:** `data/output/painel_caged_municipio_anatel.parquet` (Notebook
3a).

### 0. Dependências

Conferir pacotes instalados e instalar o necessário para o notebook
(pandas, numpy, pyfixest e dependências como platformdirs).

``` python
# Etapa 3b.0 — Conferir e instalar dependências
!pip install pandas numpy pyfixest platformdirs pyarrow -q
print("Pacotes principais (após install):")
!pip list
```

    Pacotes principais (após install):
    Package                            Version
    ---------------------------------- --------------
    aiohappyeyeballs                   2.6.1
    aiohttp                            3.13.2
    aiosignal                          1.4.0
    altair                             5.4.1
    annotated-types                    0.6.0
    anyio                              4.12.0
    appnope                            0.1.3
    argon2-cffi                        25.1.0
    argon2-cffi-bindings               25.1.0
    arrow                              1.3.0
    asttokens                          2.4.1
    async-lru                          2.0.5
    attrs                              23.2.0
    Authlib                            1.6.6
    babel                              2.17.0
    backports.tarfile                  1.2.0
    basedosdados                       2.0.2
    beartype                           0.22.8
    beautifulsoup4                     4.12.2
    bleach                             6.2.0
    blinker                            1.8.2
    brotli                             1.2.0
    cachetools                         5.5.0
    catboost                           1.2.8
    certifi                            2023.5.7
    cffi                               1.17.1
    charset-normalizer                 2.1.1
    click                              8.1.7
    cloudpickle                        3.1.2
    cobble                             0.1.4
    coloredlogs                        15.0.1
    comm                               0.2.0
    commonmark                         0.9.1
    contourpy                          1.3.3
    coverage                           7.13.0
    cryptography                       44.0.0
    cssselect2                         0.8.0
    cycler                             0.12.1
    cyclopts                           4.3.0
    dataclasses-json                   0.6.7
    db-dtypes                          1.5.0
    debugpy                            1.8.0
    decorator                          5.1.1
    defusedxml                         0.7.1
    diskcache                          5.6.3
    distlib                            0.3.6
    distro                             1.8.0
    dnspython                          2.8.0
    docstring_parser                   0.17.0
    docutils                           0.22.3
    einops                             0.7.0
    email-validator                    2.3.0
    et_xmlfile                         2.0.0
    exceptiongroup                     1.3.1
    executing                          2.0.1
    faicons                            0.2.2
    fakeredis                          2.32.1
    fastjsonschema                     2.21.1
    fastmcp                            2.14.0
    fastuuid                           0.14.0
    filelock                           3.12.2
    filetype                           1.2.0
    flatbuffers                        24.3.25
    fonttools                          4.61.1
    formulaic                          1.2.1
    fqdn                               1.5.1
    frozenlist                         1.4.1
    fsspec                             2023.12.2
    ftfy                               6.3.1
    geobr                              0.2.2
    geopandas                          1.1.0
    gitdb                              4.0.11
    GitPython                          3.1.43
    google-ai-generativelanguage       0.6.15
    google-api-core                    2.25.1
    google-api-python-client           2.178.0
    google-auth                        2.40.3
    google-auth-httplib2               0.2.0
    google-auth-oauthlib               1.2.3
    google-cloud-bigquery              3.40.0
    google-cloud-bigquery-connection   1.20.0
    google-cloud-bigquery-storage      2.36.0
    google-cloud-core                  2.5.0
    google-cloud-storage               2.19.0
    google-crc32c                      1.8.0
    google-generativeai                0.8.5
    google-resumable-media             2.8.0
    googleapis-common-protos           1.70.0
    graphviz                           0.21
    great-tables                       0.20.0
    greenlet                           3.2.4
    grpc-google-iam-v1                 0.14.3
    grpcio                             1.76.0
    grpcio-status                      1.71.2
    h11                                0.14.0
    html5lib                           1.1
    htmltools                          0.6.0
    httpcore                           1.0.2
    httplib2                           0.22.0
    httpx                              0.28.1
    httpx-sse                          0.4.3
    huggingface-hub                    0.26.2
    humanfriendly                      10.0
    idna                               3.4
    imbalanced-learn                   0.14.0
    importlib_metadata                 8.7.0
    importlib_resources                6.5.2
    iniconfig                          2.3.0
    interface-meta                     1.3.0
    ipykernel                          6.26.0
    ipython                            8.17.2
    ipywidgets                         8.1.7
    isoduration                        20.11.0
    jaraco.classes                     3.4.0
    jaraco.context                     6.0.1
    jaraco.functools                   4.3.0
    jedi                               0.19.1
    Jinja2                             3.1.2
    jiter                              0.12.0
    joblib                             1.4.2
    json5                              0.12.1
    jsonpatch                          1.33
    jsonpointer                        3.0.0
    jsonschema                         4.23.0
    jsonschema-path                    0.3.4
    jsonschema-specifications          2023.12.1
    jupyter                            1.1.1
    jupyter-book                       2.1.2
    jupyter_client                     8.6.0
    jupyter-console                    6.6.3
    jupyter_core                       5.5.0
    jupyter-events                     0.12.0
    jupyter-lsp                        2.2.6
    jupyter_server                     2.16.0
    jupyter_server_terminals           0.5.3
    jupyterlab                         4.4.5
    jupyterlab_pygments                0.3.0
    jupyterlab_server                  2.27.3
    jupyterlab_widgets                 3.0.15
    kaggle                             1.7.4.5
    keyring                            25.7.0
    kiwisolver                         1.4.9
    langchain                          0.3.8
    langchain-core                     0.3.21
    langchain-text-splitters           0.3.0
    langsmith                          0.1.145
    lightgbm                           4.6.0
    litellm                            1.80.10
    llvmlite                           0.46.0
    loguru                             0.7.3
    lupa                               2.6
    lxml                               5.3.0
    mammoth                            1.9.0
    mapclassify                        2.10.0
    markdown-it-py                     3.0.0
    markdownify                        0.14.1
    marker-pdf                         0.3.10
    markitdown                         0.0.1a3
    MarkupSafe                         2.1.3
    marshmallow                        3.22.0
    matplotlib                         3.10.5
    matplotlib-inline                  0.1.6
    mcp                                1.24.0
    mdurl                              0.1.2
    mistune                            3.1.3
    mock-open                          1.4.0
    more-itertools                     10.8.0
    mpmath                             1.2.1
    multidict                          6.0.4
    mypy-extensions                    1.0.0
    mysql-connector-python             9.5.0
    narwhals                           2.1.1
    nbclient                           0.10.2
    nbconvert                          7.16.6
    nbformat                           5.10.4
    nest-asyncio                       1.5.8
    networkx                           3.6.1
    nodeenv                            1.10.0
    notebook                           7.4.5
    notebook_shim                      0.2.4
    numba                              0.63.1
    numpy                              1.26.4
    oauthlib                           3.3.1
    onnxruntime                        1.20.1
    openai                             2.13.0
    openapi-pydantic                   0.5.1
    opencv-python                      4.10.0.84
    openpyxl                           3.1.5
    opentelemetry-api                  1.39.1
    opentelemetry-exporter-prometheus  0.60b1
    opentelemetry-sdk                  1.39.1
    opentelemetry-semantic-conventions 0.60b1
    orjson                             3.10.7
    overrides                          7.7.0
    packaging                          25.0
    pandas                             2.2.2
    pandas-gbq                         0.33.0
    pandocfilters                      1.5.1
    parso                              0.8.3
    pathable                           0.4.4
    pathvalidate                       3.3.1
    patsy                              1.0.1
    pdf2image                          1.17.0
    pdfminer.six                       20250506
    pdfplumber                         0.11.7
    pdftext                            0.3.19
    pexpect                            4.8.0
    pillow                             10.4.0
    pip                                26.0.1
    pipenv                             2023.6.26
    platformdirs                       4.5.1
    playwright                         1.54.0
    plotly                             6.3.0
    pluggy                             1.6.0
    prometheus_client                  0.22.1
    prompt-toolkit                     3.0.41
    propcache                          0.4.1
    proto-plus                         1.26.1
    protobuf                           5.29.5
    psutil                             7.2.1
    ptyprocess                         0.7.0
    pure-eval                          0.2.2
    puremagic                          1.28
    py-key-value-aio                   0.3.0
    py-key-value-shared                0.3.0
    pyarrow                            17.0.0
    pyasn1                             0.6.1
    pyasn1_modules                     0.4.2
    pycparser                          2.22
    pydantic                           2.12.5
    pydantic_core                      2.41.5
    pydantic-settings                  2.6.1
    pydata-google-auth                 1.9.1
    pydeck                             0.9.1
    pydocket                           0.15.4
    pydub                              0.25.1
    pydyf                              0.12.1
    pyee                               13.0.0
    pyfixest                           0.40.1
    Pygments                           2.16.1
    PyJWT                              2.10.1
    pyogrio                            0.12.1
    pyparsing                          3.2.3
    PyPDF2                             3.0.1
    pypdfium2                          4.30.0
    pyperclip                          1.11.0
    pyphen                             0.17.2
    pyproj                             3.7.2
    pytest                             9.0.2
    pytest-cov                         7.0.0
    python-bcb                         0.3.3
    python-dateutil                    2.8.2
    python-dotenv                      1.1.0
    python-json-logger                 3.3.0
    python-multipart                   0.0.20
    python-pptx                        1.0.2
    python-slugify                     8.0.4
    pytz                               2024.2
    PyYAML                             6.0.1
    pyzmq                              25.1.1
    RapidFuzz                          3.10.1
    redis                              7.1.0
    referencing                        0.35.1
    regex                              2024.11.6
    requests                           2.31.0
    requests-oauthlib                  2.0.0
    requests-toolbelt                  1.0.0
    rfc3339-validator                  0.1.4
    rfc3986-validator                  0.1.1
    rich                               14.2.0
    rich-rst                           1.3.2
    rpds-py                            0.20.0
    rsa                                4.9.1
    safetensors                        0.4.2
    scikit-learn                       1.5.2
    scipy                              1.12.0
    seaborn                            0.13.2
    Send2Trash                         1.8.3
    sentence-transformers              5.2.0
    setuptools                         68.0.0
    shapely                            2.1.0
    shellingham                        1.5.4
    six                                1.16.0
    smmap                              5.0.1
    sniffio                            1.3.0
    sortedcontainers                   2.4.0
    soupsieve                          2.6
    SpeechRecognition                  3.14.0
    SQLAlchemy                         2.0.35
    sse-starlette                      3.0.3
    stack-data                         0.6.3
    starlette                          0.50.0
    statsmodels                        0.14.5
    streamlit                          1.40.1
    surya-ocr                          0.6.13
    sympy                              1.13.1
    tabled-pdf                         0.1.4
    tabulate                           0.9.0
    tenacity                           8.5.0
    terminado                          0.18.1
    texify                             0.2.1
    text-unidecode                     1.3
    threadpoolctl                      3.5.0
    tiktoken                           0.12.0
    tinycss2                           1.4.0
    tinyhtml5                          2.0.0
    tokenizers                         0.20.3
    toml                               0.10.2
    tomlkit                            0.11.8
    torch                              2.5.1
    torchaudio                         2.5.1
    torchsde                           0.2.6
    torchvision                        0.20.1
    tornado                            6.3.3
    tqdm                               4.66.1
    traitlets                          5.13.0
    trampoline                         0.1.2
    transformers                       4.46.3
    typer                              0.20.0
    types-python-dateutil              2.9.0.20250809
    typing_extensions                  4.15.0
    typing-inspect                     0.9.0
    typing-inspection                  0.4.2
    tzdata                             2024.1
    uri-template                       1.3.0
    uritemplate                        4.2.0
    urllib3                            1.26.13
    uvicorn                            0.38.0
    virtualenv                         20.23.1
    virtualenv-clone                   0.5.7
    wcwidth                            0.2.10
    weasyprint                         68.1
    webcolors                          24.11.1
    webencodings                       0.5.1
    websocket-client                   1.8.0
    websockets                         15.0.1
    wheel                              0.40.0
    widgetsnbextension                 4.0.14
    wordcloud                          1.9.4
    wrapt                              2.1.1
    xgboost                            3.1.2
    xlrd                               2.0.2
    XlsxWriter                         3.2.0
    yarl                               1.22.0
    youtube-transcript-api             0.6.3
    zipp                               3.23.0
    zopfli                             0.4.0

### Estratégia de identificação

| Elemento        | Especificação                                 |
|-----------------|-----------------------------------------------|
| Unidade         | Ocupação (CBO 4d) × Município × Mês           |
| Tratamento (1)  | Alta exposição à IA (ILO score \> mediana)    |
| Tratamento (2)  | Alta conectividade (penetração BL \> mediana) |
| Evento          | Lançamento ChatGPT (Nov/2022)                 |
| FE              | cbo_4d + uf_periodo                           |
| Clustering      | id_municipio                                  |
| Coef. interesse | β₇ (triple_did)                               |

### 1. Configuração e carga de dados

Carregar painel 3a, winsorizar salários (P1/P99).

``` python
# Etapa 3b.1 — Configuração e carga
import warnings
import pandas as pd
import numpy as np
import pyfixest as pf
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*multicollinearity.*", category=UserWarning)

# Sempre usar a pasta notebook/data
def _find_project_root():
    p = Path.cwd().resolve()
    for _ in range(5):
        if (p / "notebook").is_dir():
            return p
        p = p.parent if p.parent != p else p
    return Path.cwd().resolve()
PROJECT_ROOT = _find_project_root()
DATA_ROOT = PROJECT_ROOT / "notebook" / "data"
DATA_OUTPUT = DATA_ROOT / "output"
CACHE_DIR = DATA_ROOT / "cache"
OUTPUTS_TABLES = PROJECT_ROOT / "notebook" / "outputs" / "tables"
OUTPUTS_FIGURES = PROJECT_ROOT / "notebook" / "outputs" / "figures"
USE_CACHE_3B = True  # Se True, seção 8 usa cache e checkpoints; se False, tudo em memória
for d in [OUTPUTS_TABLES, OUTPUTS_FIGURES, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PAINEL_FILE = DATA_OUTPUT / "painel_caged_municipio_anatel.parquet"
PAINEL_FILE_V2 = DATA_OUTPUT / "painel_caged_municipio_anatel_v2.parquet"
VCOV_SPEC = {"CRV1": "id_municipio"}
OUTCOMES = {"ln_salario_real_adm": "Log(Sal. Real Adm.)", "ln_admissoes": "Log(Admissões)", "pct_superior_adm": "% Superior", "idade_media_adm": "Idade Média"}

print("Data output:", DATA_OUTPUT.resolve())
if PAINEL_FILE_V2.exists():
    df = pd.read_parquet(PAINEL_FILE_V2)
    print("Painel v2 (faixa etária, fibra, capital) carregado:", PAINEL_FILE_V2.resolve())
else:
    df = pd.read_parquet(PAINEL_FILE)
    print("Painel (sem v2) carregado:", PAINEL_FILE.resolve())
for c in ["salario_medio_adm", "salario_real_adm"]:
    if c in df.columns:
        lo, hi = df[c].quantile(0.01), df[c].quantile(0.99)
        df[c] = df[c].clip(lo, hi)
if "ln_salario_real_adm" in df.columns:
    df["ln_salario_real_adm"] = np.log(df["salario_real_adm"].clip(lower=1))
print(f"Painel: {len(df):,} obs | {df['id_municipio'].nunique():,} municípios | {df['cbo_4d'].nunique()} ocupações")
```

    Data output: /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/data/output
    Painel v2 (faixa etária, fibra, capital) carregado: /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/data/output/painel_caged_municipio_anatel_v2.parquet
    Painel: 5,534,808 obs | 657 municípios | 614 ocupações

### 2. Tabela de balanço por conectividade (pré-tratamento)

``` python
# Etapa 3b.2 — Balanço
pre = df[df["post"] == 0]
print(pre.groupby("alta_conectividade").agg(
    n_obs=("cbo_4d", "count"),
    admissoes_media=("admissoes", "mean"),
    salario_medio=("salario_medio_adm", "mean"),
    penetracao_media=("penetracao_bl", "mean"),
).round(2))
```

                          n_obs  admissoes_media  salario_medio  penetracao_media
    alta_conectividade                                                           
    0                    205077             5.02        1330.58              0.18
    1                   2126257            15.02        1742.66              0.69

### 3. DiD por subgrupo de conectividade (motivação)

Estimar DiD (post × alta_exp) separadamente para municípios de alta e
baixa conectividade.

``` python
# Etapa 3b.3 — DiD por subgrupo
df["post_alta_exp"] = df["post"] * df["alta_exp"]
for conn_label, mask in [("Alta conect.", df["alta_conectividade"] == 1), ("Baixa conect.", df["alta_conectividade"] == 0)]:
    d = df.loc[mask].dropna(subset=["ln_salario_real_adm"])
    m = pf.feols("ln_salario_real_adm ~ post_alta_exp | cbo_4d + uf_periodo", data=d, vcov=VCOV_SPEC)
    c = m.coef().get("post_alta_exp", m.coef().iloc[0])
    print(f"{conn_label}: coef = {float(c):.4f}, se = {float(m.se().loc['post_alta_exp']):.4f}")
```

    Alta conect.: coef = -0.0058, se = 0.0018
    Baixa conect.: coef = -0.0089, se = 0.0046

### 4. Triple-DiD — Modelo principal

outcome ~ triple_did + post_alta_exp + post_alta_conect +
alta_exp_alta_conect \| cbo_4d + uf_periodo

``` python
# Etapa 3b.4 — Triple-DiD principal
formula = "ln_salario_real_adm ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo"
m = pf.feols(formula, data=df.dropna(subset=["ln_salario_real_adm"]), vcov=VCOV_SPEC)
print(m.summary())
results_triple = pd.DataFrame({"coef": m.coef(), "se": m.se(), "p_value": m.pvalue()})
results_triple.to_csv(OUTPUTS_TABLES / "triple_did_main_etapa3b.csv")
```

    ###

    Estimation:  OLS
    Dep. var.: ln_salario_real_adm, Fixed effects: cbo_4d+uf_periodo
    Inference:  CRV1
    Observations:  5534808

    | Coefficient          |   Estimate |   Std. Error |   t value |   Pr(>|t|) |   2.5% |   97.5% |
    |:---------------------|-----------:|-------------:|----------:|-----------:|-------:|--------:|
    | triple_did           |     -0.016 |        0.008 |    -1.888 |      0.059 | -0.032 |   0.001 |
    | post_alta_exp        |      0.008 |        0.008 |     1.069 |      0.285 | -0.007 |   0.024 |
    | post_alta_conect     |      0.017 |        0.008 |     2.239 |      0.025 |  0.002 |   0.032 |
    | alta_exp_alta_conect |      0.037 |        0.010 |     3.743 |      0.000 |  0.017 |   0.056 |
    ---
    RMSE: 0.555 R2: 0.969 R2 Within: 0.0 
    None

### 5. Event study por grupo de conectividade

Dummies (tempo_relativo × alta_exp) para alta e baixa conectividade;
referência t = -1.

``` python
# Etapa 3b.5 — Event study por conectividade
# Dummies (tempo_relativo × alta_exp) para alta e baixa conectividade; referência t = -1.
# Nomes das variáveis: sem "-" na fórmula (formulaic interpreta "did_t-12" como did_t menos 12).
def _nome_did(t):
    return f"did_m{-t}" if t < 0 else f"did_{t}"

BIN_MIN, BIN_MAX, REF = -12, 24, -1
df["t_bin"] = df["tempo_relativo_meses"].clip(lower=BIN_MIN, upper=BIN_MAX)
for conn_val, label in [(1, "Alta"), (0, "Baixa")]:
    d = df[(df["alta_conectividade"] == conn_val) & df["ln_salario_real_adm"].notna()].copy()
    ts = [t for t in sorted(d["t_bin"].unique()) if t != REF]
    did_vars = [_nome_did(t) for t in ts]
    for t, v in zip(ts, did_vars):
        d[v] = ((d["t_bin"] == t) & (d["alta_exp"] == 1)).astype(int)
    if did_vars:
        m = pf.feols(f"ln_salario_real_adm ~ {' + '.join(did_vars)} | cbo_4d + uf_periodo", data=d, vcov=VCOV_SPEC)
        print(f"{label} conect.: {len(ts)} coeficientes estimados")
```

    Alta conect.: 36 coeficientes estimados
    Baixa conect.: 36 coeficientes estimados

### 6. Testes de robustez e síntese

Placebo temporal (Dez/2021); cutoff Q75. Correção FDR para múltiplos
outcomes (opcional). Síntese: comparar com Etapa 2 — efeito concentrado
onde a adoção de IA é viável.

``` python
# Etapa 3b.6 — Robustez (placebo) e múltiplos outcomes
# Placebo: post = 1 a partir de Dez/2021
df["post_placebo"] = ((df["ano"] == 2021) & (df["mes"] >= 12)) | (df["ano"] > 2021)
df["triple_did_placebo"] = df["post_placebo"].astype(int) * df["alta_exp"] * df["alta_conectividade"]
df["post_alta_exp_placebo"] = df["post_placebo"].astype(int) * df["alta_exp"]
m_placebo = pf.feols("ln_salario_real_adm ~ triple_did_placebo + post_alta_exp_placebo | cbo_4d + uf_periodo",
                     data=df.dropna(subset=["ln_salario_real_adm"]), vcov=VCOV_SPEC)
print("Placebo Dez/2021 (triple_did_placebo):", m_placebo.coef().get("triple_did_placebo"), "p =", m_placebo.pvalue().get("triple_did_placebo"))
print("Esperado: não significativo.")
if USE_CACHE_3B:
    import json
    with open(CACHE_DIR / "placebo_secao6.json", "w") as f:
        json.dump({"triple_did_placebo": {"coef": float(m_placebo.coef().get("triple_did_placebo")), "se": float(m_placebo.se().get("triple_did_placebo")), "pval": float(m_placebo.pvalue().get("triple_did_placebo"))}}, f, indent=2)
```

    Placebo Dez/2021 (triple_did_placebo): 0.03653039627709792 p = 5.672064404560473e-05
    Esperado: não significativo.

### 7. Correção de tendência diferencial pré (Caminho 1)

Se o placebo falha por tendência pré-existente no grupo alta_exp ×
alta_conectividade, controlar por **alta_exp × alta_conectividade ×
trend** (trend = 1, 2, …, T). Se β₇ (triple_did) permanece significativo
após incluir a tendência, o efeito é robusto; se não, o efeito era
explicado pela tendência pré.

``` python
# Etapa 3b.7 — Tendência diferencial pré (Caminho 1)
periodos_ordenados = sorted(df["periodo"].unique())
trend_map = {p: i + 1 for i, p in enumerate(periodos_ordenados)}
df["trend"] = df["periodo"].map(trend_map)
df["trend_exp_conect"] = df["alta_exp"] * df["alta_conectividade"] * df["trend"]
df["trend_exp"] = df["alta_exp"] * df["trend"]
df["trend_conect"] = df["alta_conectividade"] * df["trend"]

outcome = "ln_salario_real_adm"
formula_trend = (
    f"{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect"
    " + trend_exp_conect + trend_exp + trend_conect | cbo_4d + uf_periodo"
)
model_trend = pf.feols(formula_trend, data=df.dropna(subset=[outcome]), vcov=VCOV_SPEC)
print("Modelo com tendência diferencial pré:")
print(model_trend.summary())

# Comparar com modelo original (seção 4)
formula_orig = "ln_salario_real_adm ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo"
model_orig = pf.feols(formula_orig, data=df.dropna(subset=["ln_salario_real_adm"]), vcov=VCOV_SPEC)
print("\nComparação: Original vs. com tendência")
pf.etable([model_orig, model_trend])
```

    Modelo com tendência diferencial pré:
    ###

    Estimation:  OLS
    Dep. var.: ln_salario_real_adm, Fixed effects: cbo_4d+uf_periodo
    Inference:  CRV1
    Observations:  5534808

    | Coefficient          |   Estimate |   Std. Error |   t value |   Pr(>|t|) |   2.5% |   97.5% |
    |:---------------------|-----------:|-------------:|----------:|-----------:|-------:|--------:|
    | triple_did           |      0.006 |        0.010 |     0.668 |      0.504 | -0.012 |   0.025 |
    | post_alta_exp        |     -0.005 |        0.009 |    -0.596 |      0.552 | -0.023 |   0.012 |
    | post_alta_conect     |     -0.015 |        0.007 |    -2.070 |      0.039 | -0.030 |  -0.001 |
    | alta_exp_alta_conect |      0.034 |        0.010 |     3.375 |      0.001 |  0.014 |   0.054 |
    | trend_exp_conect     |     -0.001 |        0.000 |    -1.321 |      0.187 | -0.001 |   0.000 |
    | trend_exp            |      0.000 |        0.000 |     0.616 |      0.538 | -0.000 |   0.001 |
    | trend_conect         |      0.001 |        0.000 |     2.463 |      0.014 |  0.000 |   0.002 |
    ---
    RMSE: 0.555 R2: 0.969 R2 Within: 0.0 
    None

    Comparação: Original vs. com tendência

<div id="wlxoxwixkf" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>
#wlxoxwixkf table {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', 'Fira Sans', 'Droid Sans', Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
&#10;#wlxoxwixkf thead, tbody, tfoot, tr, td, th { border-style: none !important; }
 tr { background-color: transparent !important; }
#wlxoxwixkf p { margin: 0 !important; padding: 0 !important; }
 #wlxoxwixkf .gt_table { display: table !important; border-collapse: collapse !important; line-height: normal !important; margin-left: auto !important; margin-right: auto !important; color: #333333 !important; font-size: 16px !important; font-weight: normal !important; font-style: normal !important; background-color: #FFFFFF !important; width: auto !important; border-top-style: solid !important; border-top-width: 2px !important; border-top-color: #A8A8A8 !important; border-right-style: none !important; border-right-width: 2px !important; border-right-color: #D3D3D3 !important; border-bottom-style: hidden !important; border-bottom-width: 2px !important; border-bottom-color: #A8A8A8 !important; border-left-style: none !important; border-left-width: 2px !important; border-left-color: #D3D3D3 !important; }
 #wlxoxwixkf .gt_caption { padding-top: 4px !important; padding-bottom: 4px !important; }
 #wlxoxwixkf .gt_title { color: #333333 !important; font-size: 125% !important; font-weight: initial !important; padding-top: 4px !important; padding-bottom: 4px !important; padding-left: 5px !important; padding-right: 5px !important; border-bottom-color: #FFFFFF !important; border-bottom-width: 0 !important; }
 #wlxoxwixkf .gt_subtitle { color: #333333 !important; font-size: 85% !important; font-weight: initial !important; padding-top: 3px !important; padding-bottom: 5px !important; padding-left: 5px !important; padding-right: 5px !important; border-top-color: #FFFFFF !important; border-top-width: 0 !important; }
 #wlxoxwixkf .gt_heading { background-color: #FFFFFF !important; text-align: center !important; border-bottom-color: #FFFFFF !important; border-left-style: none !important; border-left-width: 1px !important; border-left-color: #D3D3D3 !important; border-right-style: none !important; border-right-width: 1px !important; border-right-color: #D3D3D3 !important; }
 #wlxoxwixkf .gt_bottom_border { border-bottom-style: solid !important; border-bottom-width: 2px !important; border-bottom-color: #D3D3D3 !important; }
 #wlxoxwixkf .gt_col_headings { border-top-style: solid !important; border-top-width: 2px !important; border-top-color: black !important; border-bottom-style: solid !important; border-bottom-width: 0.5px !important; border-bottom-color: black !important; border-left-style: none !important; border-left-width: 1px !important; border-left-color: #D3D3D3 !important; border-right-style: none !important; border-right-width: 1px !important; border-right-color: #D3D3D3 !important; }
 #wlxoxwixkf .gt_col_heading { color: #333333 !important; background-color: #FFFFFF !important; font-size: 100% !important; font-weight: normal !important; text-transform: inherit !important; border-left-style: none !important; border-left-width: 0px !important; border-left-color: white !important; border-right-style: none !important; border-right-width: 0px !important; border-right-color: white !important; vertical-align: bottom !important; padding-top: 4px !important; padding-bottom: 5px !important; padding-left: 5px !important; padding-right: 5px !important; overflow-x: hidden !important; }
 #wlxoxwixkf .gt_column_spanner_outer { color: #333333 !important; background-color: #FFFFFF !important; font-size: 100% !important; font-weight: normal !important; text-transform: inherit !important; padding-top: 0 !important; padding-bottom: 0 !important; padding-left: 4px !important; padding-right: 4px !important; }
 #wlxoxwixkf .gt_column_spanner_outer:first-child { padding-left: 0 !important; }
 #wlxoxwixkf .gt_column_spanner_outer:last-child { padding-right: 0 !important; }
 #wlxoxwixkf .gt_column_spanner { border-bottom-style: solid !important; border-bottom-width: 0.5px !important; border-bottom-color: black !important; vertical-align: bottom !important; padding-top: 4px !important; padding-bottom: 4px !important; overflow-x: hidden !important; display: inline-block !important; width: 100% !important; }
 #wlxoxwixkf .gt_spanner_row { border-bottom-style: hidden !important; }
 #wlxoxwixkf .gt_group_heading { padding-top: 0px !important; padding-bottom: 0px !important; padding-left: 5px !important; padding-right: 5px !important; color: #333333 !important; background-color: #FFFFFF !important; font-size: 0px !important; font-weight: initial !important; text-transform: inherit !important; border-top-style: solid !important; border-top-width: 0.5px !important; border-top-color: black !important; border-bottom-style: solid !important; border-bottom-width: 0.5px !important; border-bottom-color: black !important; border-left-style: none !important; border-left-width: 1px !important; border-left-color: white !important; border-right-style: none !important; border-right-width: 1px !important; border-right-color: white !important; vertical-align: middle !important; text-align: left !important; }
 #wlxoxwixkf .gt_empty_group_heading { padding: 0.5px !important; color: #333333 !important; background-color: #FFFFFF !important; font-size: 0px !important; font-weight: initial !important; border-top-style: solid !important; border-top-width: 0.5px !important; border-top-color: black !important; border-bottom-style: solid !important; border-bottom-width: 0.5px !important; border-bottom-color: black !important; vertical-align: middle !important; }
 #wlxoxwixkf .gt_from_md> :first-child { margin-top: 0 !important; }
 #wlxoxwixkf .gt_from_md> :last-child { margin-bottom: 0 !important; }
 #wlxoxwixkf .gt_row { padding-top: 4px !important; padding-bottom: 4px !important; padding-left: 5px !important; padding-right: 5px !important; margin: 10px !important; border-top-style: none !important; border-top-width: 1px !important; border-top-color: #D3D3D3 !important; border-left-style: none !important; border-left-width: 0px !important; border-left-color: white !important; border-right-style: none !important; border-right-width: 0px !important; border-right-color: white !important; vertical-align: middle !important; overflow-x: hidden !important; }
 #wlxoxwixkf .gt_stub { color: #333333 !important; background-color: #FFFFFF !important; font-size: 100% !important; font-weight: initial !important; text-transform: inherit !important; border-right-style: hidden !important; border-right-width: 2px !important; border-right-color: #D3D3D3 !important; padding-left: 5px !important; padding-right: 5px !important; }
 #wlxoxwixkf .gt_stub_row_group { color: #333333 !important; background-color: #FFFFFF !important; font-size: 100% !important; font-weight: initial !important; text-transform: inherit !important; border-right-style: solid !important; border-right-width: 2px !important; border-right-color: #D3D3D3 !important; padding-left: 5px !important; padding-right: 5px !important; vertical-align: top !important; }
 #wlxoxwixkf .gt_row_group_first td { border-top-width: 0.5px !important; }
 #wlxoxwixkf .gt_row_group_first th { border-top-width: 0.5px !important; }
 #wlxoxwixkf .gt_striped { color: #333333 !important; background-color: #F4F4F4 !important; }
 #wlxoxwixkf .gt_table_body { border-top-style: solid !important; border-top-width: 0.5px !important; border-top-color: black !important; border-bottom-style: solid !important; border-bottom-width: 2px !important; border-bottom-color: black !important; }
 #wlxoxwixkf .gt_grand_summary_row { color: #333333 !important; background-color: #FFFFFF !important; text-transform: inherit !important; padding-top: 8px !important; padding-bottom: 8px !important; padding-left: 5px !important; padding-right: 5px !important; }
 #wlxoxwixkf .gt_first_grand_summary_row_bottom { border-top-style: double !important; border-top-width: 6px !important; border-top-color: #D3D3D3 !important; }
 #wlxoxwixkf .gt_last_grand_summary_row_top { border-bottom-style: double !important; border-bottom-width: 6px !important; border-bottom-color: #D3D3D3 !important; }
 #wlxoxwixkf .gt_sourcenotes { color: #333333 !important; background-color: #FFFFFF !important; border-bottom-style: none !important; border-bottom-width: 2px !important; border-bottom-color: #D3D3D3 !important; border-left-style: none !important; border-left-width: 2px !important; border-left-color: #D3D3D3 !important; border-right-style: none !important; border-right-width: 2px !important; border-right-color: #D3D3D3 !important; }
 #wlxoxwixkf .gt_sourcenote { font-size: 90% !important; padding-top: 4px !important; padding-bottom: 4px !important; padding-left: 5px !important; padding-right: 5px !important; text-align: left !important; }
 #wlxoxwixkf .gt_left { text-align: left !important; }
 #wlxoxwixkf .gt_center { text-align: center !important; }
 #wlxoxwixkf .gt_right { text-align: right !important; font-variant-numeric: tabular-nums !important; }
 #wlxoxwixkf .gt_font_normal { font-weight: normal !important; }
 #wlxoxwixkf .gt_font_bold { font-weight: bold !important; }
 #wlxoxwixkf .gt_font_italic { font-style: italic !important; }
 #wlxoxwixkf .gt_super { font-size: 65% !important; }
 #wlxoxwixkf .gt_footnote_marks { font-size: 75% !important; vertical-align: 0.4em !important; position: initial !important; }
 #wlxoxwixkf .gt_asterisk { font-size: 100% !important; vertical-align: 0 !important; }
 &#10;</style>

<table class="gt_table" data-quarto-postprocess="true"
data-quarto-disable-processing="false" data-quarto-bootstrap="false">
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="gt_col_headings gt_spanner_row">
<th rowspan="2" class="gt_col_heading gt_columns_bottom_border gt_left"
data-quarto-table-cell-role="th" scope="col"></th>
<th colspan="2" id="ln_salario_real_adm"
class="gt_center gt_columns_top_border gt_column_spanner_outer"
data-quarto-table-cell-role="th" scope="colgroup"><span
class="gt_column_spanner">ln_salario_real_adm</span></th>
</tr>
<tr class="gt_col_headings">
<th id="0" class="gt_col_heading gt_columns_bottom_border gt_center"
data-quarto-table-cell-role="th" scope="col">(1)</th>
<th id="1" class="gt_col_heading gt_columns_bottom_border gt_center"
data-quarto-table-cell-role="th" scope="col">(2)</th>
</tr>
</thead>
<tbody class="gt_table_body">
<tr class="gt_group_heading_row">
<td colspan="3" class="gt_group_heading"
data-quarto-table-cell-role="th">coef</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">triple_did</td>
<td class="gt_row gt_center">-0.016<br />
(0.008)</td>
<td class="gt_row gt_center">0.006<br />
(0.010)</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">post_alta_exp</td>
<td class="gt_row gt_center">0.008<br />
(0.008)</td>
<td class="gt_row gt_center">-0.005<br />
(0.009)</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">post_alta_conect</td>
<td class="gt_row gt_center">0.017*<br />
(0.008)</td>
<td class="gt_row gt_center">-0.015*<br />
(0.007)</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">alta_exp_alta_conect</td>
<td class="gt_row gt_center">0.037***<br />
(0.010)</td>
<td class="gt_row gt_center">0.034***<br />
(0.010)</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">trend_exp_conect</td>
<td class="gt_row gt_center"></td>
<td class="gt_row gt_center">-0.001<br />
(0.000)</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">trend_exp</td>
<td class="gt_row gt_center"></td>
<td class="gt_row gt_center">0.000<br />
(0.000)</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">trend_conect</td>
<td class="gt_row gt_center"></td>
<td class="gt_row gt_center">0.001*<br />
(0.000)</td>
</tr>
<tr class="gt_group_heading_row">
<td colspan="3" class="gt_group_heading"
data-quarto-table-cell-role="th">fe</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">uf_periodo</td>
<td class="gt_row gt_center">x</td>
<td class="gt_row gt_center">x</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">cbo_4d</td>
<td class="gt_row gt_center">x</td>
<td class="gt_row gt_center">x</td>
</tr>
<tr class="gt_group_heading_row">
<td colspan="3" class="gt_group_heading"
data-quarto-table-cell-role="th">stats</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">Observations</td>
<td class="gt_row gt_center">5534808</td>
<td class="gt_row gt_center">5534808</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub" data-quarto-table-cell-role="th">S.E.
type</td>
<td class="gt_row gt_center">by: id_municipio</td>
<td class="gt_row gt_center">by: id_municipio</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">R<sup>2</sup></td>
<td class="gt_row gt_center">0.969</td>
<td class="gt_row gt_center">0.969</td>
</tr>
<tr>
<td class="gt_row gt_left gt_stub"
data-quarto-table-cell-role="th">R<sup>2</sup> Within</td>
<td class="gt_row gt_center">0.000</td>
<td class="gt_row gt_center">0.000</td>
</tr>
</tbody><tfoot class="gt_sourcenotes">
<tr>
<td colspan="3" class="gt_sourcenote">Significance levels: * p &lt;
0.05, ** p &lt; 0.01, *** p &lt; 0.001. Format of coefficient cell:
Coefficient (Std. Error)</td>
</tr>
</tfoot>
&#10;</table>

&#10;</div>

### 8. Proxies alternativos de conectividade (Caminho 2)

Testar quatro proxies além da mediana de penetração: (1) extremos Q75 vs
Q25, (2) % fibra óptica, (3) tratamento contínuo (dose-resposta), (4)
apenas capitais. Para cada um, rodar Triple-DiD e placebo temporal
(Dez/2021). Se algum proxy passar no placebo, sugere que o problema está
na definição de conectividade.

**Nota:** Rode as células 8a a 8g em sequência. Com
`USE_CACHE_3B = True`, cada célula carrega só a amostra necessária do
cache e libera memória ao final.

``` python
# Etapa 3b.8a — Preparação e gravação do cache (Proxies)
outcome = "ln_salario_real_adm"

# Garantir placebo da seção 6; se não rodou, calcula aqui
try:
    _ = m_placebo.pvalue()
except NameError:
    df["post_placebo"] = ((df["ano"] == 2021) & (df["mes"] >= 12)) | (df["ano"] > 2021)
    df["triple_did_placebo"] = df["post_placebo"].astype(int) * df["alta_exp"] * df["alta_conectividade"]
    df["post_alta_exp_placebo"] = df["post_placebo"].astype(int) * df["alta_exp"]
    m_placebo = pf.feols("ln_salario_real_adm ~ triple_did_placebo + post_alta_exp_placebo | cbo_4d + uf_periodo", data=df.loc[df[outcome].notna()], vcov=VCOV_SPEC)

# Variáveis de dose e capital
exp_col = "ilo_exposure_score" if "ilo_exposure_score" in df.columns else "alta_exp"
df["dose_triple"] = df["penetracao_bl"] * (df[exp_col] if exp_col == "ilo_exposure_score" else df[exp_col].astype(float)) * df["post"]
df["dose_exp_post"] = (df[exp_col].astype(float) if exp_col == "alta_exp" else df[exp_col]) * df["post"]
df["dose_conect_post"] = df["penetracao_bl"] * df["post"]
df["dose_exp_conect"] = (df[exp_col].astype(float) if exp_col == "alta_exp" else df[exp_col]) * df["penetracao_bl"]
if "capital" in df.columns:
    df["triple_did_capital"] = df["post"] * df["alta_exp"] * df["capital"]
    df["post_capital"] = df["post"] * df["capital"]
    df["alta_exp_capital"] = df["alta_exp"] * df["capital"]

# Amostra de regressão
print("8a: Preparando amostra de regressão…")
df_reg = df.loc[df[outcome].notna()].copy()

# Amostra extremos Q25/Q75
q25, q75 = df["penetracao_bl"].quantile(0.25), df["penetracao_bl"].quantile(0.75)
df_extremos = df[(df["penetracao_bl"] <= q25) | (df["penetracao_bl"] >= q75)].copy()
df_extremos["alta_conect_extremo"] = (df_extremos["penetracao_bl"] >= q75).astype(int)
df_extremos["triple_did_extremo"] = df_extremos["post"] * df_extremos["alta_exp"] * df_extremos["alta_conect_extremo"]
df_extremos["post_alta_conect_ext"] = df_extremos["post"] * df_extremos["alta_conect_extremo"]
df_extremos["alta_exp_alta_conect_ext"] = df_extremos["alta_exp"] * df_extremos["alta_conect_extremo"]
df_extremos["post_placebo"] = ((df_extremos["ano"] == 2021) & (df_extremos["mes"] >= 12)) | (df_extremos["ano"] > 2021)
df_extremos["triple_placebo_ext"] = df_extremos["post_placebo"].astype(int) * df_extremos["alta_exp"] * df_extremos["alta_conect_extremo"]
df_extremos["post_placebo_alta_exp"] = df_extremos["post_placebo"].astype(int) * df_extremos["alta_exp"]
df_extremos["post_placebo_alta_conect_ext"] = df_extremos["post_placebo"].astype(int) * df_extremos["alta_conect_extremo"]
df_ext = df_extremos.loc[df_extremos[outcome].notna()].copy()

if USE_CACHE_3B:
    df_reg.to_parquet(CACHE_DIR / "painel_3b_df_reg.parquet", index=False)
    df_ext.to_parquet(CACHE_DIR / "painel_3b_df_ext.parquet", index=False)
    if (CACHE_DIR / "resultados_proxy.csv").exists():
        (CACHE_DIR / "resultados_proxy.csv").unlink()
    print("Cache salvo em", CACHE_DIR.resolve())
    del df_reg, df_extremos, df_ext
    print("8a concluído. Memória liberada.")
else:
    print("8a concluído (sem cache). df_reg e df_ext em memória para 8b–8f.")
```

    8a: Preparando amostra de regressão…
    Cache salvo em /Users/manebrasil/Documents/Projects/Dissetação Mestrado/notebook/data/cache
    8a concluído. Memória liberada.

``` python
# Etapa 3b.8b — Proxy Original (mediana)
outcome = "ln_salario_real_adm"
RESULTADOS_PROXY_CSV = CACHE_DIR / "resultados_proxy.csv"

if USE_CACHE_3B and (CACHE_DIR / "painel_3b_df_reg.parquet").exists():
    df_reg = pd.read_parquet(CACHE_DIR / "painel_3b_df_reg.parquet")
else:
    if "df_reg" not in dir():
        raise RuntimeError("Rode a célula 8a antes.")

# m_placebo: do escopo (seção 6) ou do cache
try:
    pval_placebo = m_placebo.pvalue().get("triple_did_placebo")
except NameError:
    import json
    with open(CACHE_DIR / "placebo_secao6.json") as f:
        pval_placebo = json.load(f)["triple_did_placebo"]["pval"]

formula_orig = "ln_salario_real_adm ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo"
m_orig = pf.feols(formula_orig, data=df_reg, vcov=VCOV_SPEC)
row = {"proxy": "Original (mediana)", "coef": m_orig.coef().get("triple_did"), "se": m_orig.se().get("triple_did"), "pval": m_orig.pvalue().get("triple_did"), "placebo_pval": pval_placebo}
pd.DataFrame([row]).to_csv(RESULTADOS_PROXY_CSV, index=False)
if USE_CACHE_3B:
    del df_reg
print("8b concluído.")
```

    8b concluído.

``` python
# Etapa 3b.8c — Proxy Extremos (Q75/Q25)
outcome = "ln_salario_real_adm"

if USE_CACHE_3B and (CACHE_DIR / "painel_3b_df_ext.parquet").exists():
    df_ext = pd.read_parquet(CACHE_DIR / "painel_3b_df_ext.parquet")
else:
    if "df_ext" not in dir():
        raise RuntimeError("Rode a célula 8a antes.")

formula_ext = f"{outcome} ~ triple_did_extremo + post_alta_exp + post_alta_conect_ext + alta_exp_alta_conect_ext | cbo_4d + uf_periodo"
m_ext = pf.feols(formula_ext, data=df_ext, vcov=VCOV_SPEC)
m_placebo_ext = pf.feols(f"{outcome} ~ triple_placebo_ext + post_placebo_alta_exp + post_placebo_alta_conect_ext + alta_exp_alta_conect_ext | cbo_4d + uf_periodo", data=df_ext, vcov=VCOV_SPEC)
pval_placebo_ext = m_placebo_ext.pvalue().get("triple_placebo_ext", np.nan)
row = {"proxy": "Extremos Q75/Q25", "coef": m_ext.coef().get("triple_did_extremo"), "se": m_ext.se().get("triple_did_extremo"), "pval": m_ext.pvalue().get("triple_did_extremo"), "placebo_pval": pval_placebo_ext}
pd.DataFrame([row]).to_csv(RESULTADOS_PROXY_CSV, mode="a", header=False, index=False)
if USE_CACHE_3B:
    del df_ext
print("8c concluído.")
```

    8c concluído.

``` python
# Etapa 3b.8d — Proxy % Fibra (requer painel v2)
outcome = "ln_salario_real_adm"

if USE_CACHE_3B and (CACHE_DIR / "painel_3b_df_reg.parquet").exists():
    df_reg = pd.read_parquet(CACHE_DIR / "painel_3b_df_reg.parquet")
else:
    if "df_reg" not in dir():
        raise RuntimeError("Rode a célula 8a antes.")

if "triple_did_fibra" in df_reg.columns:
    df_reg["triple_placebo_fibra"] = df_reg["post_placebo"].astype(int) * df_reg["alta_exp"] * df_reg["alta_fibra"]
    df_reg["post_placebo_alta_fibra"] = df_reg["post_placebo"].astype(int) * df_reg["alta_fibra"]
    formula_fibra = f"{outcome} ~ triple_did_fibra + post_alta_exp + post_alta_fibra + alta_exp_alta_fibra | cbo_4d + uf_periodo"
    m_fibra = pf.feols(formula_fibra, data=df_reg, vcov=VCOV_SPEC)
    m_pl_fibra = pf.feols(f"{outcome} ~ triple_placebo_fibra + post_alta_exp_placebo + post_placebo_alta_fibra + alta_exp_alta_fibra | cbo_4d + uf_periodo", data=df_reg, vcov=VCOV_SPEC)
    row = {"proxy": "% Fibra", "coef": m_fibra.coef().get("triple_did_fibra"), "se": m_fibra.se().get("triple_did_fibra"), "pval": m_fibra.pvalue().get("triple_did_fibra"), "placebo_pval": m_pl_fibra.pvalue().get("triple_placebo_fibra")}
else:
    row = {"proxy": "% Fibra", "coef": np.nan, "se": np.nan, "pval": np.nan, "placebo_pval": np.nan}
pd.DataFrame([row]).to_csv(RESULTADOS_PROXY_CSV, mode="a", header=False, index=False)
if USE_CACHE_3B:
    del df_reg
print("8d concluído.")
```

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/feols_.py:2847: UserWarning: 
                3 variables dropped due to multicollinearity.
                The following variables are dropped: ['triple_did_fibra', 'post_alta_fibra', 'alta_exp_alta_fibra'].
                
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/feols_.py:2847: UserWarning: 
                3 variables dropped due to multicollinearity.
                The following variables are dropped: ['triple_placebo_fibra', 'post_placebo_alta_fibra', 'alta_exp_alta_fibra'].
                
      warnings.warn(

    8d concluído.

``` python
# Etapa 3b.8e — Proxy Contínuo (dose-resposta)
outcome = "ln_salario_real_adm"

if USE_CACHE_3B and (CACHE_DIR / "painel_3b_df_reg.parquet").exists():
    df_reg = pd.read_parquet(CACHE_DIR / "painel_3b_df_reg.parquet")
else:
    if "df_reg" not in dir():
        raise RuntimeError("Rode a célula 8a antes.")

formula_cont = f"{outcome} ~ dose_triple + dose_exp_post + dose_conect_post + dose_exp_conect | cbo_4d + uf_periodo"
m_cont = pf.feols(formula_cont, data=df_reg, vcov=VCOV_SPEC)
row = {"proxy": "Contínuo", "coef": m_cont.coef().get("dose_triple"), "se": m_cont.se().get("dose_triple"), "pval": m_cont.pvalue().get("dose_triple"), "placebo_pval": np.nan}
pd.DataFrame([row]).to_csv(RESULTADOS_PROXY_CSV, mode="a", header=False, index=False)
if USE_CACHE_3B:
    del df_reg
print("8e concluído.")
```

    8e concluído.

``` python
# Etapa 3b.8f — Proxy Capitais (requer painel v2)
outcome = "ln_salario_real_adm"

if USE_CACHE_3B and (CACHE_DIR / "painel_3b_df_reg.parquet").exists():
    df_reg = pd.read_parquet(CACHE_DIR / "painel_3b_df_reg.parquet")
else:
    if "df_reg" not in dir():
        raise RuntimeError("Rode a célula 8a antes.")

if "capital" in df_reg.columns:
    try:
        formula_cap = f"{outcome} ~ triple_did_capital + post_alta_exp + post_capital + alta_exp_capital | cbo_4d + uf_periodo"
        m_cap = pf.feols(formula_cap, data=df_reg, vcov=VCOV_SPEC)
        row = {"proxy": "Capitais", "coef": m_cap.coef().get("triple_did_capital"), "se": m_cap.se().get("triple_did_capital"), "pval": m_cap.pvalue().get("triple_did_capital"), "placebo_pval": np.nan}
    except Exception:
        row = {"proxy": "Capitais", "coef": np.nan, "se": np.nan, "pval": np.nan, "placebo_pval": np.nan}
else:
    row = {"proxy": "Capitais", "coef": np.nan, "se": np.nan, "pval": np.nan, "placebo_pval": np.nan}
pd.DataFrame([row]).to_csv(RESULTADOS_PROXY_CSV, mode="a", header=False, index=False)
if USE_CACHE_3B:
    del df_reg
print("8f concluído.")
```

    8f concluído.

``` python
# Etapa 3b.8g — Montagem da tabela
RESULTADOS_PROXY_CSV = CACHE_DIR / "resultados_proxy.csv"
if not RESULTADOS_PROXY_CSV.exists():
    print("Rode as células 8b–8f antes para gerar resultados_proxy.csv")
else:
    tab_proxy = pd.read_csv(RESULTADOS_PROXY_CSV)
    tab_proxy["sig"] = tab_proxy["pval"].apply(lambda p: "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.1 else "")))
    print("Tabela comparativa — Triple-DiD por proxy de conectividade")
    print(tab_proxy.to_string())
```

    Tabela comparativa — Triple-DiD por proxy de conectividade
                    proxy      coef        se          pval  placebo_pval  sig
    0  Original (mediana) -0.015759  0.008346  5.944694e-02      0.000057    *
    1    Extremos Q75/Q25 -0.021561  0.007295  3.322350e-03      0.017556  ***
    2             % Fibra       NaN       NaN           NaN           NaN     
    3            Contínuo -0.058241  0.011591  6.506810e-07           NaN  ***
    4            Capitais -0.113379  0.016465  1.345479e-11           NaN  ***

### 9. Decomposição etária do Triple-DiD

Rodar Triple-DiD para cada outcome por faixa etária (admissões e salário
por jovem/intermediário/senior, share de jovens/seniores, razão salarial
jovem/senior). Se a hipótese de compensação etária estiver correta:
share_jovem ↓, share_senior ↑, ln_sal_real_jovem ↓,
razao_sal_jovem_senior ↓.

**Cache:** Com `USE_CACHE_3B = True`, os resultados são salvos em
`resultados_idade.csv`. Se o kernel cair ou você reexecutar a célula, os
outcomes já calculados são carregados do cache e só os faltantes são
estimados (um por vez, com menos memória).

``` python
# Etapa 3b.9 — Decomposição etária do Triple-DiD (com cache; reaproveita resultados anteriores)
outcomes_idade = {
    "Admissões jovens (log)": "ln_adm_jovem",
    "Admissões intermediários (log)": "ln_adm_intermediario",
    "Admissões seniores (log)": "ln_adm_senior",
    "Share jovens nas admissões": "share_jovem",
    "Share seniores nas admissões": "share_senior",
    "Salário real jovens (log)": "ln_sal_real_jovem",
    "Salário real intermediários (log)": "ln_sal_real_intermediario",
    "Salário real seniores (log)": "ln_sal_real_senior",
    "Razão salarial jovem/senior": "razao_sal_jovem_senior",
}

CACHE_IDADE_CSV = CACHE_DIR / "resultados_idade.csv"
COLS_REGR = ["triple_did", "post_alta_exp", "post_alta_conect", "alta_exp_alta_conect", "cbo_4d", "uf_periodo", "id_municipio"]
resultados_idade = {}
if CACHE_IDADE_CSV.exists() and USE_CACHE_3B:
    cache_df = pd.read_csv(CACHE_IDADE_CSV)
    for _, r in cache_df.iterrows():
        resultados_idade[r["outcome_name"]] = {"coef": r["coef"], "se": r["se"], "pval": r["pval"], "n": int(r["n"])}
    print(f"Carregados {len(resultados_idade)} resultados do cache.")

formula_base = "{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo"
for nome, outcome_var in outcomes_idade.items():
    if nome in resultados_idade:
        continue
    if outcome_var not in df.columns:
        print(f"SKIP {nome}: coluna {outcome_var} não encontrada (rode 3a com painel v2).")
        continue
    # Só as colunas necessárias para a regressão (reduz memória)
    use_cols = [outcome_var] + [c for c in COLS_REGR if c in df.columns]
    mask = df[outcome_var].notna()
    df_valid = df.loc[mask, use_cols].copy()
    if len(df_valid) < 1000:
        print(f"SKIP {nome}: apenas {len(df_valid)} obs válidas")
        del df_valid
        continue
    formula = formula_base.format(outcome=outcome_var)
    try:
        model = pf.feols(formula, data=df_valid, vcov=VCOV_SPEC)
        coef = float(model.coef().get("triple_did"))
        se = float(model.se().get("triple_did"))
        pval = float(model.pvalue().get("triple_did"))
        n = len(df_valid)
        resultados_idade[nome] = {"coef": coef, "se": se, "pval": pval, "n": n}
        if USE_CACHE_3B:
            pd.DataFrame([{"outcome_name": nome, "outcome_var": outcome_var, "coef": coef, "se": se, "pval": pval, "n": n}]).to_csv(CACHE_IDADE_CSV, mode="a", header=not CACHE_IDADE_CSV.exists(), index=False)
        print(f"OK {nome}")
    except Exception as e:
        print(f"ERRO {nome}: {e}")
    del df_valid

if resultados_idade:
    df_resultados_idade = pd.DataFrame(resultados_idade).T
    df_resultados_idade["sig"] = df_resultados_idade["pval"].apply(
        lambda p: "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.1 else ""))
    )
    print("Triple-DiD por outcome etário (coef = triple_did):")
    print(df_resultados_idade.to_string())
else:
    print("Nenhum outcome etário disponível. Execute o Notebook 3a e exporte o painel v2.")
```

    Carregados 9 resultados do cache.
    Triple-DiD por outcome etário (coef = triple_did):
                                           coef        se          pval          n  sig
    Admissões jovens (log)            -0.330124  0.043301  8.659740e-14  5534808.0  ***
    Admissões intermediários (log)    -0.351799  0.050120  5.585532e-12  5534808.0  ***
    Admissões seniores (log)          -0.182257  0.027490  7.022161e-11  5534808.0  ***
    Share jovens nas admissões        -0.001168  0.005800  8.405146e-01  4404189.0     
    Share seniores nas admissões      -0.001866  0.002645  4.805814e-01  4404189.0     
    Salário real jovens (log)         -0.631805  0.076151  6.661338e-16  5534808.0  ***
    Salário real intermediários (log) -0.534896  0.076899  8.498313e-12  5534808.0  ***
    Salário real seniores (log)       -0.723624  0.116553  9.486867e-10  5534808.0  ***
    Razão salarial jovem/senior       -7.271724  8.598501  3.980303e-01  1391959.0     

### 10. Modelo reformulado: impacto sobre jovens

Hipótese: após o ChatGPT, a **participação de jovens nas contratações**
(share_jovem) caiu mais em ocupações expostas à IA e em municípios
conectados. Outcome principal: **share_jovem** = admissões de jovens
(\<30) / total de admissões. Três especificações (pura, com tendência,
com controles demográficos), placebo temporal e event study por
conectividade.

**Memória:** A célula usa apenas as colunas necessárias em cada bloco e
libera os DataFrames entre as etapas para evitar travamento.

``` python
# Etapa 3b.10 — Modelo reformulado: share_jovem (DataFrames mínimos para reduzir memória)
if "share_jovem" not in df.columns:
    print("share_jovem não disponível. Execute o Notebook 3a e exporte o painel v2.")
else:
    # Colunas necessárias para as 3 especificações (evita cópia do painel inteiro)
    cols_j = ["share_jovem", "triple_did", "post_alta_exp", "post_alta_conect", "alta_exp_alta_conect", "alta_exp", "alta_conectividade", "cbo_4d", "uf_periodo", "id_municipio"]
    if "periodo" in df.columns:
        cols_j.append("periodo")
    for c in ["pct_superior_adm", "pct_mulher_adm", "ln_pib_pc"]:
        if c in df.columns:
            cols_j.append(c)
    cols_j = [c for c in cols_j if c in df.columns]
    df_j = df.loc[df["share_jovem"].notna(), cols_j].copy()
    if "periodo" in df_j.columns and "trend_exp_conect" not in df_j.columns:
        periodos_ordenados = sorted(df_j["periodo"].unique())
        trend_map = {p: i + 1 for i, p in enumerate(periodos_ordenados)}
        df_j["trend"] = df_j["periodo"].map(trend_map)
        df_j["trend_exp_conect"] = df_j["alta_exp"] * df_j["alta_conectividade"] * df_j["trend"]
        df_j["trend_exp"] = df_j["alta_exp"] * df_j["trend"]
        df_j["trend_conect"] = df_j["alta_conectividade"] * df_j["trend"]

    formula_j1 = "share_jovem ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo"
    m_jovem_1 = pf.feols(formula_j1, data=df_j, vcov=VCOV_SPEC)
    formula_j2 = "share_jovem ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect + trend_exp_conect + trend_exp + trend_conect | cbo_4d + uf_periodo"
    m_jovem_2 = pf.feols(formula_j2, data=df_j, vcov=VCOV_SPEC)
    controles = [c for c in ["pct_superior_adm", "pct_mulher_adm", "ln_pib_pc"] if c in df_j.columns]
    formula_j3 = "share_jovem ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect + trend_exp_conect + trend_exp + trend_conect + " + " + ".join(controles) + " | cbo_4d + uf_periodo" if controles else formula_j2
    m_jovem_3 = pf.feols(formula_j3, data=df_j.dropna(subset=controles) if controles else df_j, vcov=VCOV_SPEC)
    print("Três especificações — outcome: share_jovem")
    pf.etable([m_jovem_1, m_jovem_2, m_jovem_3])
    del df_j

    # Placebo: só colunas necessárias
    mask_pre = (df["ano"] < 2022) | ((df["ano"] == 2022) & (df["mes"] < 11)) if "ano" in df.columns else (df["periodo_dt"] < pd.Timestamp("2022-11-01")) if "periodo_dt" in df.columns else pd.Series(False, index=df.index)
    cols_pre = ["share_jovem", "alta_exp", "alta_conectividade", "alta_exp_alta_conect", "cbo_4d", "uf_periodo", "id_municipio"]
    if "ano" in df.columns:
        cols_pre.extend(["ano", "mes"])
    if "periodo_dt" in df.columns:
        cols_pre.append("periodo_dt")
    cols_pre = [c for c in cols_pre if c in df.columns]
    df_pre = df.loc[mask_pre, cols_pre].copy()
    df_pre = df_pre.dropna(subset=["share_jovem"])
    if "periodo_dt" not in df_pre.columns and "ano" in df_pre.columns:
        df_pre["periodo_dt"] = pd.to_datetime(df_pre["ano"].astype(str) + "-" + df_pre["mes"].astype(str).str.zfill(2) + "-01", errors="coerce")
    df_pre["post_placebo"] = (df_pre["periodo_dt"] >= pd.Timestamp("2021-12-01")).astype(int) if "periodo_dt" in df_pre.columns else ((df_pre["ano"] == 2021) & (df_pre["mes"] >= 12)) | (df_pre["ano"] > 2021)
    df_pre["triple_placebo"] = df_pre["post_placebo"].astype(int) * df_pre["alta_exp"] * df_pre["alta_conectividade"]
    df_pre["post_placebo_alta_exp"] = df_pre["post_placebo"].astype(int) * df_pre["alta_exp"]
    df_pre["post_placebo_alta_conect"] = df_pre["post_placebo"].astype(int) * df_pre["alta_conectividade"]
    if "alta_exp_alta_conect" not in df_pre.columns:
        df_pre["alta_exp_alta_conect"] = df_pre["alta_exp"] * df_pre["alta_conectividade"]
    m_placebo_j = pf.feols("share_jovem ~ triple_placebo + post_placebo_alta_exp + post_placebo_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo", data=df_pre, vcov=VCOV_SPEC)
    print(f"Placebo share_jovem (Dez/2021): coef = {m_placebo_j.coef().get('triple_placebo', np.nan):.4f}, p = {m_placebo_j.pvalue().get('triple_placebo', np.nan):.4f}")
    del df_pre

    # Event study: só colunas necessárias; um grupo de conectividade por vez
    if "tempo_relativo_meses" in df.columns:
        BIN_MIN, BIN_MAX, REF = -12, 24, -1
        cols_es = ["share_jovem", "tempo_relativo_meses", "alta_conectividade", "alta_exp", "cbo_4d", "uf_periodo", "id_municipio"]
        cols_es = [c for c in cols_es if c in df.columns]
        df_es = df.loc[df["share_jovem"].notna(), cols_es].copy()
        df_es["t_bin"] = df_es["tempo_relativo_meses"].clip(lower=BIN_MIN, upper=BIN_MAX)
        for conn_val, label in [(1, "Alta"), (0, "Baixa")]:
            d = df_es[df_es["alta_conectividade"] == conn_val].copy()
            ts = [t for t in sorted(d["t_bin"].unique()) if t != REF]
            did_vars = [f"did_m{-t}" if t < 0 else f"did_{t}" for t in ts]
            for t, v in zip(ts, did_vars):
                d[v] = ((d["t_bin"] == t) & (d["alta_exp"] == 1)).astype(int)
            if did_vars:
                m_es = pf.feols(f"share_jovem ~ {' + '.join(did_vars)} | cbo_4d + uf_periodo", data=d, vcov=VCOV_SPEC)
                print(f"Event study share_jovem — {label} conect.: {len(ts)} coeficientes")
            del d
        del df_es
    print("3b.10 concluído.")
```

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(
    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

    Três especificações — outcome: share_jovem

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 3 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

    Placebo share_jovem (Dez/2021): coef = -0.0064, p = 0.3391

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 1 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

    Event study share_jovem — Alta conect.: 36 coeficientes

    /opt/homebrew/lib/python3.10/site-packages/pyfixest/estimation/model_matrix_fixest_.py:215: UserWarning: 6 singleton fixed effect(s) detected. These observations are dropped from the model.
      warnings.warn(

    Event study share_jovem — Baixa conect.: 36 coeficientes
    3b.10 concluído.

    : 
    [1;31mThe Kernel crashed while executing code in the current cell or a previous cell. 

    [1;31mPlease review the code in the cell(s) to identify a possible cause of the failure. 

    [1;31mClick <a href='https://aka.ms/vscodeJupyterKernelCrash'>here</a> for more info. 

    [1;31mView Jupyter <a href='command:jupyter.viewOutput'>log</a> for further details.

### Verificação metodológica (conferência com o plano Etapa 3)

- **β₇ (triple_did):** Interpretar como a diferença do efeito da IA
  entre municípios de alta e baixa conectividade. β₇ \< 0 em salário
  real = efeito mais negativo onde a adoção de IA é viável.
- **Conectividade pré-tratamento:** Medida Jan–Out/2022 para evitar
  endogeneidade.
- **FE:** cbo_4d + uf_periodo absorvem choques estaduais; robustez com
  id_municipio + periodo.
- **Clustering:** Por id_municipio; robustez multiway (ocupação +
  município).
- **Comparação com Etapa 2:** Apresentar 3 como extensão — efeito médio
  concentrado nos municípios conectados.
