# Guia Completo: Implementação das Abordagens 1 e 2

## Sumário
1. [Abordagem 1: DiD Ocupacional](#abordagem-1-did-ocupacional)
2. [Abordagem 2: DiD Regional](#abordagem-2-did-regional)

---

# ABORDAGEM 1: DiD Ocupacional (Sugestão da Professora)

## 1. Passo a Passo

### Fase 1: Preparação dos Dados

| Passo | Descrição | Output |
|-------|-----------|--------|
| 1.1 | Baixar PNAD Contínua trimestral (2021T1 até 2024T4) | Arquivos .txt ou via BigQuery |
| 1.2 | Empilhar todos os trimestres em uma base única | Base com ~16 trimestres |
| 1.3 | Filtrar população de interesse (18-65 anos, ocupados) | Base de análise |
| 1.4 | Fazer merge com índice ILO via COD (V4010) | Base com exposição |
| 1.5 | Criar variáveis de tratamento e controle | Base final |

### Fase 2: Análise Descritiva Pré-Regressão

| Passo | Descrição | Output |
|-------|-----------|--------|
| 2.1 | Verificar distribuição de exposição por trimestre | Gráfico de linhas |
| 2.2 | Calcular estatísticas descritivas por grupo de tratamento | Tabela de balanço |
| 2.3 | Plotar tendências pré-tratamento por grupo | Gráfico de tendências paralelas |

### Fase 3: Estimação

| Passo | Descrição | Output |
|-------|-----------|--------|
| 3.1 | Estimar DiD médio (modelo básico) | Coeficiente β |
| 3.2 | Estimar Event Study (coeficientes por período) | Gráfico de coeficientes |
| 3.3 | Estimar heterogeneidades (idade, gênero) | Coeficientes das interações |

### Fase 4: Robustez

| Passo | Descrição | Output |
|-------|-----------|--------|
| 4.1 | Testar cortes alternativos (top 10%, 25%, contínuo) | Tabela de sensibilidade |
| 4.2 | Placebo temporal (usar 2019-2022) | Coeficiente placebo ≈ 0 |
| 4.3 | Diferentes especificações de erro padrão | Comparação de SEs |

---

## 2. Descrição do Modelo

### 2.1 O Que é Difference-in-Differences (DiD)?

O DiD é uma técnica para estimar efeitos causais quando temos:
- Um **tratamento** que afeta alguns grupos mas não outros
- Dados de **antes e depois** do tratamento

A ideia central é comparar a **mudança** no grupo tratado com a **mudança** no grupo controle.

```
Efeito Causal = (Tratados_depois - Tratados_antes) - (Controle_depois - Controle_antes)
```

### 2.2 Aplicação ao Nosso Problema

**Nosso "tratamento":** Lançamento do ChatGPT (novembro 2022)

**Problema:** O ChatGPT afetou TODAS as ocupações simultaneamente. Não temos um grupo que "não recebeu" IA.

**Solução:** Usar a **intensidade de exposição** como proxy para tratamento. Ocupações mais expostas são "mais tratadas".

### 2.3 O Modelo Econométrico

#### Modelo Básico (DiD Médio)

```
Y_iot = α + β(Post_t × AltExp_o) + θX_it + δ_o + μ_t + ε_iot
```

**Vamos decompor cada elemento:**

| Símbolo | Nome | Descrição | Exemplo |
|---------|------|-----------|---------|
| Y_iot | Variável dependente | Outcome de interesse para indivíduo i, ocupação o, período t | 1 se ocupado, 0 se não |
| α | Intercepto | Constante | - |
| Post_t | Dummy pós-tratamento | = 1 se t ≥ 2023T1, = 0 caso contrário | Post = 1 para 2023T2 |
| AltExp_o | Dummy alta exposição | = 1 se ocupação o está no top 20% de exposição | AltExp = 1 para "Desenvolvedores" |
| Post × AltExp | **Interação (DiD)** | = 1 apenas se pós-tratamento E alta exposição | **Este é o coeficiente de interesse!** |
| X_it | Controles individuais | Características observáveis do indivíduo | Idade, gênero, raça, escolaridade |
| δ_o | Efeito fixo de ocupação | Controla tudo que é fixo na ocupação | Absorve diferenças de nível entre ocupações |
| μ_t | Efeito fixo de tempo | Controla choques comuns a todos | Absorve efeitos de ciclo econômico |
| ε_iot | Erro | Componente não explicado | Clusterizado por ocupação |

#### O Que Cada Efeito Fixo Controla?

**Efeito fixo de ocupação (δ_o):**
- Diferenças permanentes entre ocupações
- Ex: Desenvolvedores sempre ganham mais que auxiliares administrativos
- Remove viés de "ocupações expostas são diferentes de ocupações não expostas"

**Efeito fixo de tempo (μ_t):**
- Choques que afetam todos igualmente em cada período
- Ex: Crise econômica em 2023T2 que afeta todo mundo
- Remove viés de "o período pós-ChatGPT era diferente por outras razões"

#### Interpretação do Coeficiente β

**β é o efeito DiD:** A mudança diferencial no outcome para ocupações de alta exposição (relativo às de baixa exposição) após o lançamento do ChatGPT (relativo ao período anterior).

**Se β = -0.05 e Y = probabilidade de estar ocupado:**
"Após o ChatGPT, trabalhadores em ocupações de alta exposição tiveram probabilidade de ocupação 5 pontos percentuais menor do que trabalhadores em ocupações de baixa exposição, comparado à diferença pré-existente."

### 2.4 Event Study

O Event Study é uma extensão que estima **um coeficiente para cada período** em vez de um único β.

```
Y_iot = α + Σ_j β_j(1{t=j} × AltExp_o) + θX_it + δ_o + μ_t + ε_iot
```

**Para que serve:**
1. **Testar tendências paralelas:** Se β_j ≈ 0 para j < 2023T1, as tendências eram paralelas antes do tratamento
2. **Ver dinâmica do efeito:** O efeito aparece imediatamente? Cresce ao longo do tempo?

**Período de referência:** Omitimos j = 2022T4 (último período pré-tratamento). Todos os coeficientes são relativos a este período.

### 2.5 Hipótese de Identificação

**Tendências Paralelas:** Na ausência do ChatGPT, ocupações de alta e baixa exposição teriam evoluído de forma semelhante.

**Como testar:** Os coeficientes β_j para j < 2023T1 devem ser estatisticamente iguais a zero.

**Ameaças à identificação:**
- Tendências pré-existentes diferentes entre ocupações
- Choques correlacionados com exposição (ex: pandemia afetou mais ocupações cognitivas)
- Composição da força de trabalho mudando diferentemente entre grupos

---

## 3. Exemplos de Código

### 3.1 Configuração Inicial (Python)

```python
# ============================================
# CONFIGURAÇÃO E IMPORTS
# ============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Para regressões
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
import pyfixest as pf  # Pacote moderno para fixed effects

# Configurações
pd.set_option('display.max_columns', 50)
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("colorblind")

# Seed para reprodutibilidade
np.random.seed(42)
```

### 3.2 Download e Preparação dos Dados

```python
# ============================================
# OPÇÃO A: VIA BASE DOS DADOS (BigQuery)
# ============================================

from basedosdados import read_sql

# Query para baixar PNAD Contínua trimestral
query = """
SELECT 
    ano,
    trimestre,
    -- Identificação
    id_domicilio,
    id_pessoa,
    -- Demográficas
    idade,
    sexo,
    raca_cor AS raca,
    -- Educação
    anos_estudo,
    -- Trabalho
    ocupacao_cod AS cod_ocupacao,  -- Código COD (compatível com ISCO)
    condicao_ocupacao,
    horas_trabalhadas,
    renda_trabalho,
    tipo_vinculo,  -- Para identificar formalidade
    -- Peso amostral
    peso_pessoa AS peso
FROM `basedosdados.br_ibge_pnadc.microdados`
WHERE ano >= 2021 
    AND idade BETWEEN 18 AND 65
    AND condicao_ocupacao IS NOT NULL
"""

# Executar query
print("Baixando dados da PNAD Contínua...")
pnad = read_sql(query, billing_project_id="seu-projeto-gcp")
print(f"Dados carregados: {len(pnad):,} observações")
```

```python
# ============================================
# OPÇÃO B: VIA ARQUIVOS LOCAIS DO IBGE
# ============================================

import os
import zipfile

def carregar_pnad_trimestre(ano, trimestre, caminho_base):
    """Carrega microdados de um trimestre específico"""
    
    arquivo = f"{caminho_base}/PNADC_{ano}{trimestre:02d}.txt"
    
    # Dicionário de variáveis (posições no arquivo de largura fixa)
    # Consultar dicionário oficial do IBGE
    colunas = {
        'UF': (1, 2),
        'V1008': (3, 6),      # Número de seleção do domicílio
        'V2007': (61, 61),    # Sexo
        'V2009': (63, 65),    # Idade
        'V2010': (66, 66),    # Cor ou raça
        'V4010': (145, 149),  # COD ocupação (5 dígitos, usar 4 primeiros)
        'VD4002': (193, 193), # Condição de ocupação
        'VD4016': (212, 221), # Rendimento habitual
        'VD4035': (250, 252), # Horas trabalhadas
        'V1028': (277, 291),  # Peso da pessoa
    }
    
    # Ler arquivo de largura fixa
    df = pd.read_fwf(
        arquivo,
        colspecs=[(v[0]-1, v[1]) for v in colunas.values()],
        names=list(colunas.keys()),
        dtype=str
    )
    
    df['ano'] = ano
    df['trimestre'] = trimestre
    
    return df

# Carregar todos os trimestres
trimestres = []
for ano in range(2021, 2025):
    for tri in range(1, 5):
        try:
            df = carregar_pnad_trimestre(ano, tri, "./dados_pnad")
            trimestres.append(df)
            print(f"Carregado: {ano}T{tri}")
        except FileNotFoundError:
            print(f"Não encontrado: {ano}T{tri}")

pnad = pd.concat(trimestres, ignore_index=True)
```

### 3.3 Limpeza e Criação de Variáveis

```python
# ============================================
# LIMPEZA E PREPARAÇÃO
# ============================================

def preparar_pnad(df):
    """Limpa e prepara a base da PNAD"""
    
    # Cópia para não modificar original
    df = df.copy()
    
    # Converter tipos
    df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
    df['peso'] = pd.to_numeric(df['peso'], errors='coerce')
    df['horas_trabalhadas'] = pd.to_numeric(df['horas_trabalhadas'], errors='coerce')
    df['renda_trabalho'] = pd.to_numeric(df['renda_trabalho'], errors='coerce')
    
    # Criar período (ano-trimestre)
    df['periodo'] = df['ano'].astype(str) + 'T' + df['trimestre'].astype(str)
    df['periodo_num'] = df['ano'] * 10 + df['trimestre']  # Para ordenação
    
    # Criar variável de tempo relativo (2022T4 = 0)
    periodo_ref = 2022 * 10 + 4  # 2022T4
    df['tempo_relativo'] = df['periodo_num'] - periodo_ref
    
    # COD ocupação (4 dígitos)
    df['cod_ocupacao'] = df['cod_ocupacao'].astype(str).str[:4].str.zfill(4)
    
    # Dummy de ocupado
    df['ocupado'] = (df['condicao_ocupacao'] == '1').astype(int)
    
    # Dummy de formal (simplificado)
    df['formal'] = df['tipo_vinculo'].isin(['01', '02', '03']).astype(int)
    
    # Dummies demográficas
    df['mulher'] = (df['sexo'] == '2').astype(int)
    df['negro_pardo'] = df['raca'].isin(['2', '4']).astype(int)  # Preto ou Pardo
    
    # Faixas etárias
    df['faixa_etaria'] = pd.cut(
        df['idade'],
        bins=[18, 25, 30, 40, 50, 65],
        labels=['18-25', '26-30', '31-40', '41-50', '51-65']
    )
    df['jovem'] = (df['idade'] <= 30).astype(int)
    
    # Escolaridade (simplificada)
    df['superior'] = (df['anos_estudo'] >= 15).astype(int)
    
    # Log do rendimento
    df['ln_renda'] = np.log(df['renda_trabalho'].replace(0, np.nan))
    
    return df

pnad = preparar_pnad(pnad)
print(f"Base preparada: {len(pnad):,} observações")
```

### 3.4 Merge com Índice ILO

```python
# ============================================
# CARREGAR E FAZER MERGE COM ÍNDICE ILO
# ============================================

# Carregar índice ILO (que você já construiu)
ilo_index = pd.read_csv('ilo_exposure_by_isco08.csv')

# Verificar estrutura
print("Estrutura do índice ILO:")
print(ilo_index.head())
print(f"\nOcupações no índice: {len(ilo_index)}")

# O COD da PNAD (V4010) é baseado em ISCO-08
# Fazer merge direto
pnad = pnad.merge(
    ilo_index[['isco08_code', 'exposure_score', 'automation_score', 'augmentation_score']],
    left_on='cod_ocupacao',
    right_on='isco08_code',
    how='left'
)

# Verificar cobertura
cobertura = pnad['exposure_score'].notna().mean()
print(f"\nCobertura do merge: {cobertura:.1%}")

# Criar variável de tratamento: Alta Exposição (top 20%)
threshold_20 = pnad['exposure_score'].quantile(0.80)
pnad['alta_exposicao'] = (pnad['exposure_score'] >= threshold_20).astype(int)

# Também criar versões alternativas para robustez
threshold_10 = pnad['exposure_score'].quantile(0.90)
threshold_25 = pnad['exposure_score'].quantile(0.75)
pnad['alta_exp_10'] = (pnad['exposure_score'] >= threshold_10).astype(int)
pnad['alta_exp_25'] = (pnad['exposure_score'] >= threshold_25).astype(int)

print(f"\nThreshold 20%: {threshold_20:.3f}")
print(f"Threshold 10%: {threshold_10:.3f}")
print(f"Threshold 25%: {threshold_25:.3f}")
```

### 3.5 Criar Variável de Tratamento (Post)

```python
# ============================================
# CRIAR VARIÁVEL POST (PÓS-CHATGPT)
# ============================================

# ChatGPT lançado em novembro 2022
# Usamos 2023T1 como primeiro período pós-tratamento
pnad['post'] = (pnad['periodo_num'] >= 20231).astype(int)

# Interação DiD
pnad['did'] = pnad['post'] * pnad['alta_exposicao']

# Verificar distribuição
print("Distribuição de observações:")
print(pnad.groupby(['post', 'alta_exposicao']).size().unstack())

print("\n\nDistribuição por período:")
print(pnad.groupby('periodo')['alta_exposicao'].mean().round(3))
```

### 3.6 Análise Descritiva Pré-Regressão

```python
# ============================================
# TABELA DE BALANÇO (BALANCE TABLE)
# ============================================

def tabela_balanco(df, tratamento='alta_exposicao', peso='peso'):
    """Cria tabela comparando grupos tratado e controle"""
    
    variaveis = ['idade', 'mulher', 'negro_pardo', 'superior', 
                 'renda_trabalho', 'horas_trabalhadas', 'formal']
    
    resultado = []
    
    for var in variaveis:
        # Médias ponderadas por grupo
        media_controle = np.average(
            df.loc[df[tratamento]==0, var].dropna(),
            weights=df.loc[df[tratamento]==0, peso].loc[df[var].notna()]
        )
        media_tratado = np.average(
            df.loc[df[tratamento]==1, var].dropna(),
            weights=df.loc[df[tratamento]==1, peso].loc[df[var].notna()]
        )
        
        # Diferença
        diff = media_tratado - media_controle
        
        resultado.append({
            'Variável': var,
            'Controle (Baixa Exp.)': f"{media_controle:.3f}",
            'Tratamento (Alta Exp.)': f"{media_tratado:.3f}",
            'Diferença': f"{diff:.3f}"
        })
    
    return pd.DataFrame(resultado)

# Usar apenas período pré-tratamento para balanço
pnad_pre = pnad[pnad['post'] == 0]
tabela = tabela_balanco(pnad_pre)
print("TABELA DE BALANÇO (Período Pré-Tratamento)")
print("=" * 60)
print(tabela.to_string(index=False))
```

```python
# ============================================
# GRÁFICO DE TENDÊNCIAS PARALELAS
# ============================================

def plot_tendencias(df, outcome, tratamento='alta_exposicao', peso='peso'):
    """Plota tendências do outcome por grupo de tratamento"""
    
    # Calcular médias ponderadas por período e grupo
    tendencias = df.groupby(['periodo', 'periodo_num', tratamento]).apply(
        lambda x: np.average(x[outcome].dropna(), 
                           weights=x.loc[x[outcome].notna(), peso])
    ).reset_index(name=outcome)
    
    # Separar grupos
    controle = tendencias[tendencias[tratamento] == 0]
    tratado = tendencias[tendencias[tratamento] == 1]
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(controle['periodo'], controle[outcome], 
            'o-', label='Baixa Exposição', linewidth=2, markersize=8)
    ax.plot(tratado['periodo'], tratado[outcome], 
            's-', label='Alta Exposição', linewidth=2, markersize=8)
    
    # Linha vertical no tratamento
    ax.axvline(x='2022T4', color='red', linestyle='--', 
               label='Lançamento ChatGPT', alpha=0.7)
    
    ax.set_xlabel('Período', fontsize=12)
    ax.set_ylabel(outcome, fontsize=12)
    ax.set_title(f'Tendências de {outcome} por Grupo de Exposição', fontsize=14)
    ax.legend(loc='best')
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'tendencias_{outcome}.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    return fig

# Plotar para diferentes outcomes
for outcome in ['ocupado', 'horas_trabalhadas', 'ln_renda']:
    plot_tendencias(pnad, outcome)
```

### 3.7 Estimação do DiD

```python
# ============================================
# DiD BÁSICO COM PYFIXEST (Recomendado)
# ============================================

import pyfixest as pf

# Modelo 1: DiD simples sem controles
modelo1 = pf.feols(
    "ocupado ~ post:alta_exposicao | cod_ocupacao + periodo",
    data=pnad,
    weights="peso",
    vcov={"CRV1": "cod_ocupacao"}  # Cluster por ocupação
)

print("MODELO 1: DiD Básico")
print("=" * 50)
print(modelo1.summary())

# Modelo 2: Com controles individuais
modelo2 = pf.feols(
    "ocupado ~ post:alta_exposicao + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo",
    data=pnad,
    weights="peso",
    vcov={"CRV1": "cod_ocupacao"}
)

print("\n\nMODELO 2: DiD com Controles")
print("=" * 50)
print(modelo2.summary())

# Modelo 3: Com tratamento contínuo
modelo3 = pf.feols(
    "ocupado ~ post:exposure_score + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo",
    data=pnad,
    weights="peso",
    vcov={"CRV1": "cod_ocupacao"}
)

print("\n\nMODELO 3: DiD com Exposição Contínua")
print("=" * 50)
print(modelo3.summary())
```

```python
# ============================================
# ALTERNATIVA: STATSMODELS (mais detalhado)
# ============================================

import statsmodels.formula.api as smf

# Criar dummies de ocupação e período (para modelos sem absorção)
# ATENÇÃO: Isso pode ser muito pesado com muitas ocupações

# Modelo com formula
formula = """
ocupado ~ post:alta_exposicao + idade + I(idade**2) + mulher + negro_pardo + superior 
          + C(cod_ocupacao) + C(periodo)
"""

modelo_sm = smf.wls(
    formula=formula,
    data=pnad.dropna(subset=['ocupado', 'alta_exposicao', 'idade']),
    weights=pnad.dropna(subset=['ocupado', 'alta_exposicao', 'idade'])['peso']
).fit(cov_type='cluster', cov_kwds={'groups': pnad['cod_ocupacao']})

# Extrair apenas coeficiente de interesse
print("Coeficiente DiD (post:alta_exposicao):")
print(modelo_sm.params['post:alta_exposicao'])
print(f"Erro padrão: {modelo_sm.bse['post:alta_exposicao']:.4f}")
print(f"p-valor: {modelo_sm.pvalues['post:alta_exposicao']:.4f}")
```

### 3.8 Event Study

```python
# ============================================
# EVENT STUDY
# ============================================

# Criar dummies de período × tratamento
# Omitir 2022T4 como referência
periodos = sorted(pnad['periodo'].unique())
periodo_ref = '2022T4'

for p in periodos:
    if p != periodo_ref:
        pnad[f'did_{p}'] = ((pnad['periodo'] == p) & (pnad['alta_exposicao'] == 1)).astype(int)

# Lista de variáveis de interação
vars_did = [f'did_{p}' for p in periodos if p != periodo_ref]

# Modelo Event Study
formula_es = f"ocupado ~ {' + '.join(vars_did)} + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo"

modelo_es = pf.feols(
    formula_es,
    data=pnad,
    weights="peso",
    vcov={"CRV1": "cod_ocupacao"}
)

print("EVENT STUDY")
print("=" * 50)
print(modelo_es.summary())

# Extrair coeficientes para gráfico
coefs = []
for p in periodos:
    if p == periodo_ref:
        coefs.append({'periodo': p, 'coef': 0, 'se': 0, 'ci_low': 0, 'ci_high': 0})
    else:
        var = f'did_{p}'
        coef = modelo_es.coef()[var]
        se = modelo_es.se()[var]
        coefs.append({
            'periodo': p,
            'coef': coef,
            'se': se,
            'ci_low': coef - 1.96 * se,
            'ci_high': coef + 1.96 * se
        })

coefs_df = pd.DataFrame(coefs)
```

```python
# ============================================
# GRÁFICO DO EVENT STUDY
# ============================================

def plot_event_study(coefs_df, periodo_ref='2022T4'):
    """Plota coeficientes do event study"""
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Pontos e intervalos de confiança
    x = range(len(coefs_df))
    ax.errorbar(x, coefs_df['coef'], 
                yerr=[coefs_df['coef'] - coefs_df['ci_low'], 
                      coefs_df['ci_high'] - coefs_df['coef']],
                fmt='o', capsize=5, capthick=2, markersize=10, 
                color='navy', ecolor='gray')
    
    # Linha horizontal em zero
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    # Linha vertical no tratamento
    idx_ref = coefs_df[coefs_df['periodo'] == periodo_ref].index[0]
    ax.axvline(x=idx_ref + 0.5, color='red', linestyle='--', 
               linewidth=2, label='Lançamento ChatGPT')
    
    # Sombrear região pré-tratamento
    ax.axvspan(-0.5, idx_ref + 0.5, alpha=0.1, color='gray', label='Pré-tratamento')
    
    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels(coefs_df['periodo'], rotation=45, ha='right')
    ax.set_xlabel('Período', fontsize=12)
    ax.set_ylabel('Coeficiente (efeito sobre probabilidade de ocupação)', fontsize=12)
    ax.set_title('Event Study: Efeito da Exposição à IA sobre Emprego', fontsize=14)
    ax.legend(loc='upper left')
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('event_study_ocupacao.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    return fig

plot_event_study(coefs_df)
```

### 3.9 Heterogeneidade por Idade

```python
# ============================================
# HETEROGENEIDADE POR IDADE (Triple DiD)
# ============================================

# Modelo com interação tripla
modelo_idade = pf.feols(
    """ocupado ~ post:alta_exposicao:jovem + post:alta_exposicao + post:jovem + alta_exposicao:jovem
       + idade + I(idade**2) + mulher + negro_pardo + superior 
       | cod_ocupacao + periodo""",
    data=pnad,
    weights="peso",
    vcov={"CRV1": "cod_ocupacao"}
)

print("HETEROGENEIDADE POR IDADE")
print("=" * 50)
print(modelo_idade.summary())

# Interpretação:
# post:alta_exposicao = efeito para NÃO-jovens (base)
# post:alta_exposicao:jovem = efeito ADICIONAL para jovens
```

```python
# ============================================
# EVENT STUDY SEPARADO POR FAIXA ETÁRIA
# ============================================

def event_study_por_grupo(df, grupo_var, grupo_valor, nome_grupo):
    """Estima event study para um subgrupo"""
    
    df_grupo = df[df[grupo_var] == grupo_valor].copy()
    
    # Criar variáveis de interação
    periodos = sorted(df_grupo['periodo'].unique())
    periodo_ref = '2022T4'
    
    for p in periodos:
        if p != periodo_ref:
            df_grupo[f'did_{p}'] = ((df_grupo['periodo'] == p) & 
                                    (df_grupo['alta_exposicao'] == 1)).astype(int)
    
    vars_did = [f'did_{p}' for p in periodos if p != periodo_ref]
    formula_es = f"ocupado ~ {' + '.join(vars_did)} | cod_ocupacao + periodo"
    
    modelo = pf.feols(formula_es, data=df_grupo, weights="peso", 
                      vcov={"CRV1": "cod_ocupacao"})
    
    # Extrair coeficientes
    coefs = []
    for p in periodos:
        if p == periodo_ref:
            coefs.append({'periodo': p, 'coef': 0, 'se': 0, 'grupo': nome_grupo})
        else:
            var = f'did_{p}'
            coefs.append({
                'periodo': p,
                'coef': modelo.coef()[var],
                'se': modelo.se()[var],
                'grupo': nome_grupo
            })
    
    return pd.DataFrame(coefs)

# Estimar para jovens e não-jovens
coefs_jovens = event_study_por_grupo(pnad, 'jovem', 1, 'Jovens (≤30)')
coefs_experientes = event_study_por_grupo(pnad, 'jovem', 0, 'Experientes (>30)')

# Combinar
coefs_idade = pd.concat([coefs_jovens, coefs_experientes])

# Plotar comparação
fig, ax = plt.subplots(figsize=(14, 7))

for grupo, cor in [('Jovens (≤30)', 'red'), ('Experientes (>30)', 'blue')]:
    dados = coefs_idade[coefs_idade['grupo'] == grupo]
    x = range(len(dados))
    ax.errorbar(x, dados['coef'], yerr=1.96*dados['se'],
                fmt='o-', capsize=3, label=grupo, color=cor, alpha=0.8)

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.axvline(x=7.5, color='gray', linestyle='--', label='ChatGPT')  # Ajustar índice
ax.set_xticks(range(len(coefs_jovens)))
ax.set_xticklabels(coefs_jovens['periodo'], rotation=45)
ax.set_xlabel('Período')
ax.set_ylabel('Coeficiente DiD')
ax.set_title('Event Study por Faixa Etária')
ax.legend()
plt.tight_layout()
plt.savefig('event_study_por_idade.png', dpi=150)
plt.show()
```

---

## 4. Resultados e Análises Esperados

### 4.1 Tabelas de Resultado

**Tabela Principal: Efeitos DiD sobre Emprego**

| Variável | (1) Básico | (2) Controles | (3) Contínuo |
|----------|------------|---------------|--------------|
| Post × AltaExp | -0.XXX | -0.XXX | - |
|  | (0.XXX) | (0.XXX) | - |
| Post × Exposição | - | - | -0.XXX |
|  | - | - | (0.XXX) |
| Controles Individuais | Não | Sim | Sim |
| EF Ocupação | Sim | Sim | Sim |
| EF Período | Sim | Sim | Sim |
| N | X,XXX,XXX | X,XXX,XXX | X,XXX,XXX |
| R² | 0.XXX | 0.XXX | 0.XXX |

*Notas: Erros padrão clusterizados por ocupação em parênteses. * p<0.10, ** p<0.05, *** p<0.01*

### 4.2 Gráficos Esperados

1. **Tendências Paralelas:** Gráfico de linhas mostrando evolução do outcome para tratados e controles
   - *Esperado:* Linhas paralelas antes de 2022T4, divergência depois

2. **Event Study:** Gráfico de coeficientes com intervalos de confiança
   - *Esperado:* Coeficientes ≈ 0 antes do tratamento, negativos (ou positivos) depois

3. **Heterogeneidade por Idade:** Event study separado para jovens vs. experientes
   - *Esperado (se replicar Brynjolfsson):* Efeito maior para jovens

### 4.3 Interpretação dos Resultados

**Se β < 0 e significativo:**
"Trabalhadores em ocupações de alta exposição à IA tiveram redução de X pontos percentuais na probabilidade de estar ocupado após o lançamento do ChatGPT, comparado a trabalhadores em ocupações de baixa exposição."

**Se β ≈ 0:**
"Não encontramos evidência de efeitos diferenciais sobre emprego entre ocupações mais e menos expostas à IA no período analisado. Isso pode indicar que: (a) os efeitos ainda não se materializaram no Brasil, (b) há erro de medida atenuando os coeficientes, ou (c) ajustes ocorrem por outras margens (informalidade, horas)."

**Se tendências paralelas violadas:**
"Os coeficientes pré-tratamento são estatisticamente diferentes de zero, sugerindo que ocupações de alta e baixa exposição já tinham tendências diferentes antes do ChatGPT. Isso compromete a identificação causal e os resultados devem ser interpretados com cautela."

### 4.4 Testes de Robustez

```python
# ============================================
# TABELA DE ROBUSTEZ
# ============================================

resultados_robustez = []

# Diferentes definições de tratamento
for nome, var in [('Top 10%', 'alta_exp_10'), 
                   ('Top 20%', 'alta_exposicao'), 
                   ('Top 25%', 'alta_exp_25')]:
    
    pnad['did_temp'] = pnad['post'] * pnad[var]
    
    modelo = pf.feols(
        "ocupado ~ did_temp + idade + mulher + negro_pardo + superior | cod_ocupacao + periodo",
        data=pnad, weights="peso", vcov={"CRV1": "cod_ocupacao"}
    )
    
    resultados_robustez.append({
        'Definição': nome,
        'Coeficiente': modelo.coef()['did_temp'],
        'Erro Padrão': modelo.se()['did_temp'],
        'p-valor': modelo.pvalue()['did_temp']
    })

# Tratamento contínuo
modelo_cont = pf.feols(
    "ocupado ~ post:exposure_score + idade + mulher + negro_pardo + superior | cod_ocupacao + periodo",
    data=pnad, weights="peso", vcov={"CRV1": "cod_ocupacao"}
)

resultados_robustez.append({
    'Definição': 'Contínuo',
    'Coeficiente': modelo_cont.coef()['post:exposure_score'],
    'Erro Padrão': modelo_cont.se()['post:exposure_score'],
    'p-valor': modelo_cont.pvalue()['post:exposure_score']
})

robustez_df = pd.DataFrame(resultados_robustez)
print("\nTABELA DE ROBUSTEZ")
print("=" * 60)
print(robustez_df.to_string(index=False))
```

---

# ABORDAGEM 2: DiD Regional (Explorando Desigualdade Brasileira)

## 1. Passo a Passo

### Fase 1: Calcular Exposição Regional

| Passo | Descrição | Output |
|-------|-----------|--------|
| 1.1 | Usar PNAD de período pré-tratamento (2021) | Base de referência |
| 1.2 | Calcular composição ocupacional por UF | % de cada ocupação por UF |
| 1.3 | Ponderar exposição ILO pela composição | Exposição agregada por UF |
| 1.4 | Classificar UFs em alta/baixa exposição | Variável de tratamento regional |

### Fase 2: Preparar Base para DiD Regional

| Passo | Descrição | Output |
|-------|-----------|--------|
| 2.1 | Fazer merge da exposição regional na PNAD completa | Base com exposição por UF |
| 2.2 | Criar variáveis de tratamento regional | RegionalExp, AltaExpRegiao |
| 2.3 | Agregar outcomes por UF-período (opcional) | Painel UF-período |

### Fase 3: Estimação

| Passo | Descrição | Output |
|-------|-----------|--------|
| 3.1 | DiD regional no nível individual | Coeficiente β |
| 3.2 | DiD regional no nível agregado (UF-período) | Coeficiente β |
| 3.3 | Event study regional | Gráfico de coeficientes |

### Fase 4: Validação

| Passo | Descrição | Output |
|-------|-----------|--------|
| 4.1 | Verificar variação de exposição entre UFs | Mapa e estatísticas |
| 4.2 | Testar tendências paralelas regionais | Gráfico |
| 4.3 | Placebo temporal | Coeficiente ≈ 0 |

---

## 2. Descrição do Modelo

### 2.1 Por Que Variação Regional?

A ideia é que diferentes regiões do Brasil têm **estruturas ocupacionais muito diferentes**:

- **São Paulo:** Muitos trabalhadores em finanças, TI, serviços cognitivos → Alta exposição agregada
- **Maranhão:** Mais trabalhadores em agricultura, comércio informal, ocupações manuais → Baixa exposição agregada

Se a IA afeta o mercado de trabalho, regiões com mais trabalhadores em ocupações expostas devem sentir mais os efeitos.

### 2.2 Construindo a Exposição Regional

**Fórmula:**

```
RegionalExp_r = Σ_o (Emp_ro / Emp_r) × ILOExposure_o
```

Onde:
- **Emp_ro** = número de trabalhadores na ocupação o na região r (período pré-tratamento)
- **Emp_r** = número total de trabalhadores na região r
- **ILOExposure_o** = índice de exposição da ocupação o

**Exemplo numérico:**

| UF | % Desenvolvedores | Exposição Dev. | % Agricultores | Exposição Agric. | ... | RegionalExp |
|----|-------------------|----------------|----------------|------------------|-----|-------------|
| SP | 3% | 0.65 | 2% | 0.05 | ... | 0.35 |
| MA | 0.5% | 0.65 | 15% | 0.05 | ... | 0.15 |

### 2.3 Por Que Usar Pesos Pré-Tratamento?

**Problema de endogeneidade:** Se a IA muda a composição ocupacional, usar pesos contemporâneos criaria viés.

**Solução:** Usar composição ocupacional de **antes** do tratamento (2021 ou 2019). Isso é chamado de **"shift-share" ou "Bartik instrument"**.

A lógica: A exposição regional é determinada pela estrutura ocupacional **histórica**, não pela resposta ao tratamento.

### 2.4 O Modelo Econométrico

#### Modelo no Nível Individual

```
Y_irt = α + β(Post_t × RegionalExp_r) + θX_it + δ_r + μ_t + ε_irt
```

| Símbolo | Nome | Descrição |
|---------|------|-----------|
| Y_irt | Outcome | Variável de interesse para indivíduo i, região r, período t |
| RegionalExp_r | Exposição regional | Índice agregado calculado com pesos pré-tratamento |
| Post_t | Dummy pós | = 1 se t ≥ 2023T1 |
| X_it | Controles | Características individuais |
| δ_r | EF região | Controla diferenças permanentes entre UFs |
| μ_t | EF tempo | Controla choques comuns |

#### Modelo no Nível Agregado (UF-Período)

```
Y_rt = α + β(Post_t × RegionalExp_r) + δ_r + μ_t + ε_rt
```

Onde Y_rt é a média (ou total) do outcome na região r no período t.

### 2.5 Vantagens sobre Abordagem Ocupacional

1. **Menos erro de medida:** Agregação reduz ruído da classificação ocupacional
2. **Variação mais limpa:** Diferenças entre UFs são mais persistentes e observáveis
3. **Narrativa mais clara:** "Estados mais digitalizados foram mais afetados"
4. **Potencial para contribuição original:** Poucos estudos usam variação regional para IA

### 2.6 Hipótese de Identificação

**Tendências paralelas regionais:** Na ausência do ChatGPT, UFs de alta e baixa exposição teriam evoluído de forma semelhante.

**Ameaças:**
- Choques regionais correlacionados com exposição (ex: boom de TI no Sudeste)
- Tendências pré-existentes diferentes (ex: Sudeste já estava crescendo mais)

---

## 3. Exemplos de Código

### 3.1 Calcular Exposição Regional

```python
# ============================================
# CALCULAR EXPOSIÇÃO REGIONAL AGREGADA
# ============================================

# Usar apenas período pré-tratamento (2021)
pnad_pre = pnad[pnad['ano'] == 2021].copy()

# Verificar que temos exposição para as ocupações
print(f"Cobertura de exposição: {pnad_pre['exposure_score'].notna().mean():.1%}")

# Calcular composição ocupacional por UF (ponderada)
composicao_uf = (
    pnad_pre
    .groupby(['UF', 'cod_ocupacao'])
    .apply(lambda x: x['peso'].sum())
    .reset_index(name='emprego')
)

# Total por UF
total_uf = composicao_uf.groupby('UF')['emprego'].sum().reset_index(name='total_uf')
composicao_uf = composicao_uf.merge(total_uf, on='UF')
composicao_uf['share'] = composicao_uf['emprego'] / composicao_uf['total_uf']

# Merge com exposição ILO
composicao_uf = composicao_uf.merge(
    ilo_index[['isco08_code', 'exposure_score']],
    left_on='cod_ocupacao',
    right_on='isco08_code',
    how='left'
)

# Calcular exposição regional agregada
exposicao_regional = (
    composicao_uf
    .groupby('UF')
    .apply(lambda x: np.average(x['exposure_score'].fillna(0), weights=x['share']))
    .reset_index(name='regional_exposure')
)

# Ordenar e visualizar
exposicao_regional = exposicao_regional.sort_values('regional_exposure', ascending=False)
print("\nEXPOSIÇÃO REGIONAL À IA GENERATIVA")
print("=" * 50)
print(exposicao_regional.to_string(index=False))

# Estatísticas
print(f"\nMédia: {exposicao_regional['regional_exposure'].mean():.3f}")
print(f"Desvio Padrão: {exposicao_regional['regional_exposure'].std():.3f}")
print(f"Mínimo: {exposicao_regional['regional_exposure'].min():.3f} ({exposicao_regional.iloc[-1]['UF']})")
print(f"Máximo: {exposicao_regional['regional_exposure'].max():.3f} ({exposicao_regional.iloc[0]['UF']})")
```

### 3.2 Visualizar Variação Regional

```python
# ============================================
# MAPA DE EXPOSIÇÃO REGIONAL
# ============================================

import geopandas as gpd

# Carregar shapefile do Brasil (disponível em várias fontes)
# Exemplo: https://github.com/codeforamerica/click_that_hood/tree/master/public/data
brasil = gpd.read_file('brasil_ufs.geojson')

# Merge com exposição
brasil = brasil.merge(exposicao_regional, left_on='sigla', right_on='UF')

# Plot
fig, ax = plt.subplots(1, 1, figsize=(12, 12))

brasil.plot(
    column='regional_exposure',
    ax=ax,
    legend=True,
    legend_kwds={'label': 'Exposição à IA Generativa', 'orientation': 'horizontal'},
    cmap='RdYlGn_r',  # Vermelho = alta exposição
    edgecolor='black',
    linewidth=0.5
)

# Adicionar labels das UFs
for idx, row in brasil.iterrows():
    ax.annotate(
        text=row['sigla'],
        xy=(row.geometry.centroid.x, row.geometry.centroid.y),
        ha='center',
        fontsize=8
    )

ax.set_title('Exposição Regional à IA Generativa no Brasil\n(baseado na composição ocupacional de 2021)', 
             fontsize=14)
ax.axis('off')

plt.tight_layout()
plt.savefig('mapa_exposicao_regional.png', dpi=200, bbox_inches='tight')
plt.show()
```

```python
# ============================================
# GRÁFICO DE BARRAS DA EXPOSIÇÃO POR UF
# ============================================

fig, ax = plt.subplots(figsize=(14, 8))

cores = ['red' if x > exposicao_regional['regional_exposure'].median() else 'blue' 
         for x in exposicao_regional['regional_exposure']]

bars = ax.barh(exposicao_regional['UF'], exposicao_regional['regional_exposure'], color=cores)

# Linha da mediana
mediana = exposicao_regional['regional_exposure'].median()
ax.axvline(x=mediana, color='black', linestyle='--', label=f'Mediana: {mediana:.3f}')

ax.set_xlabel('Exposição Agregada à IA Generativa', fontsize=12)
ax.set_ylabel('Unidade da Federação', fontsize=12)
ax.set_title('Exposição Regional à IA por UF\n(vermelho = acima da mediana)', fontsize=14)
ax.legend()

plt.tight_layout()
plt.savefig('barras_exposicao_uf.png', dpi=150, bbox_inches='tight')
plt.show()
```

### 3.3 Preparar Base para DiD Regional

```python
# ============================================
# MERGE EXPOSIÇÃO REGIONAL NA PNAD COMPLETA
# ============================================

# Merge
pnad = pnad.merge(exposicao_regional, on='UF', how='left')

# Criar variável de tratamento regional
mediana_regional = exposicao_regional['regional_exposure'].median()
pnad['alta_exp_regiao'] = (pnad['regional_exposure'] >= mediana_regional).astype(int)

# Também criar quartis
pnad['quartil_regional'] = pd.qcut(
    pnad['regional_exposure'], 
    q=4, 
    labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4 (Alta)']
)

# Interação DiD regional
pnad['did_regional'] = pnad['post'] * pnad['alta_exp_regiao']

# Verificar
print("Distribuição por UF e tratamento regional:")
print(pnad.groupby(['UF', 'alta_exp_regiao']).size().unstack())
```

### 3.4 DiD Regional no Nível Individual

```python
# ============================================
# DiD REGIONAL - NÍVEL INDIVIDUAL
# ============================================

# Modelo 1: DiD regional básico
modelo_reg1 = pf.feols(
    "ocupado ~ post:alta_exp_regiao | UF + periodo",
    data=pnad,
    weights="peso",
    vcov={"CRV1": "UF"}  # Cluster por UF
)

print("MODELO REGIONAL 1: DiD Básico")
print("=" * 50)
print(modelo_reg1.summary())

# Modelo 2: Com controles individuais
modelo_reg2 = pf.feols(
    "ocupado ~ post:alta_exp_regiao + idade + I(idade**2) + mulher + negro_pardo + superior | UF + periodo",
    data=pnad,
    weights="peso",
    vcov={"CRV1": "UF"}
)

print("\n\nMODELO REGIONAL 2: Com Controles")
print("=" * 50)
print(modelo_reg2.summary())

# Modelo 3: Com exposição contínua
modelo_reg3 = pf.feols(
    "ocupado ~ post:regional_exposure + idade + I(idade**2) + mulher + negro_pardo + superior | UF + periodo",
    data=pnad,
    weights="peso",
    vcov={"CRV1": "UF"}
)

print("\n\nMODELO REGIONAL 3: Exposição Contínua")
print("=" * 50)
print(modelo_reg3.summary())
```

### 3.5 DiD Regional no Nível Agregado

```python
# ============================================
# AGREGAR DADOS POR UF-PERÍODO
# ============================================

# Calcular médias ponderadas por UF-período
painel_uf = (
    pnad
    .groupby(['UF', 'periodo', 'periodo_num', 'post', 'regional_exposure', 'alta_exp_regiao'])
    .apply(lambda x: pd.Series({
        'ocupados': np.average(x['ocupado'], weights=x['peso']),
        'horas': np.average(x['horas_trabalhadas'].dropna(), 
                          weights=x.loc[x['horas_trabalhadas'].notna(), 'peso']),
        'ln_renda': np.average(x['ln_renda'].dropna(), 
                              weights=x.loc[x['ln_renda'].notna(), 'peso']),
        'informal': 1 - np.average(x['formal'], weights=x['peso']),
        'n_obs': len(x),
        'peso_total': x['peso'].sum()
    }))
    .reset_index()
)

print(f"Painel UF-período: {len(painel_uf)} observações")
print(f"UFs: {painel_uf['UF'].nunique()}, Períodos: {painel_uf['periodo'].nunique()}")

# DiD no nível agregado
modelo_agregado = pf.feols(
    "ocupados ~ post:alta_exp_regiao | UF + periodo",
    data=painel_uf,
    weights="peso_total",
    vcov={"CRV1": "UF"}
)

print("\n\nMODELO AGREGADO (UF-PERÍODO)")
print("=" * 50)
print(modelo_agregado.summary())
```

### 3.6 Event Study Regional

```python
# ============================================
# EVENT STUDY REGIONAL
# ============================================

# Criar variáveis de interação período × região
periodos = sorted(painel_uf['periodo'].unique())
periodo_ref = '2022T4'

for p in periodos:
    if p != periodo_ref:
        painel_uf[f'did_reg_{p}'] = ((painel_uf['periodo'] == p) & 
                                      (painel_uf['alta_exp_regiao'] == 1)).astype(int)

vars_did_reg = [f'did_reg_{p}' for p in periodos if p != periodo_ref]

# Modelo
formula_es_reg = f"ocupados ~ {' + '.join(vars_did_reg)} | UF + periodo"

modelo_es_reg = pf.feols(
    formula_es_reg,
    data=painel_uf,
    weights="peso_total",
    vcov={"CRV1": "UF"}
)

print("EVENT STUDY REGIONAL")
print("=" * 50)
print(modelo_es_reg.summary())

# Extrair coeficientes
coefs_reg = []
for p in periodos:
    if p == periodo_ref:
        coefs_reg.append({'periodo': p, 'coef': 0, 'se': 0})
    else:
        var = f'did_reg_{p}'
        coefs_reg.append({
            'periodo': p,
            'coef': modelo_es_reg.coef()[var],
            'se': modelo_es_reg.se()[var]
        })

coefs_reg_df = pd.DataFrame(coefs_reg)

# Plot
plot_event_study(coefs_reg_df)
plt.savefig('event_study_regional.png', dpi=150)
```

### 3.7 Gráfico de Tendências Regionais

```python
# ============================================
# TENDÊNCIAS POR GRUPO REGIONAL
# ============================================

fig, ax = plt.subplots(figsize=(14, 7))

for grupo, cor, label in [(0, 'blue', 'Baixa Exposição Regional'), 
                           (1, 'red', 'Alta Exposição Regional')]:
    dados = painel_uf[painel_uf['alta_exp_regiao'] == grupo]
    media_periodo = dados.groupby('periodo')['ocupados'].mean()
    ax.plot(media_periodo.index, media_periodo.values, 'o-', 
            color=cor, label=label, linewidth=2, markersize=8)

ax.axvline(x='2022T4', color='gray', linestyle='--', label='ChatGPT')
ax.set_xlabel('Período', fontsize=12)
ax.set_ylabel('Taxa de Ocupação', fontsize=12)
ax.set_title('Tendências de Ocupação por Exposição Regional', fontsize=14)
ax.legend()
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig('tendencias_regionais.png', dpi=150)
plt.show()
```

### 3.8 Comparação UFs Específicas

```python
# ============================================
# COMPARAR UFs ESPECÍFICAS (CASE STUDIES)
# ============================================

# Selecionar UFs extremas
ufs_alta = exposicao_regional.head(3)['UF'].tolist()  # Top 3
ufs_baixa = exposicao_regional.tail(3)['UF'].tolist()  # Bottom 3

print(f"UFs alta exposição: {ufs_alta}")
print(f"UFs baixa exposição: {ufs_baixa}")

# Filtrar dados
case_studies = painel_uf[painel_uf['UF'].isin(ufs_alta + ufs_baixa)]

# Plot
fig, ax = plt.subplots(figsize=(14, 7))

for uf in ufs_alta + ufs_baixa:
    dados = case_studies[case_studies['UF'] == uf]
    cor = 'red' if uf in ufs_alta else 'blue'
    estilo = '-' if uf in ufs_alta else '--'
    ax.plot(dados['periodo'], dados['ocupados'], estilo, 
            color=cor, label=uf, linewidth=2, alpha=0.7)

ax.axvline(x='2022T4', color='gray', linestyle=':', linewidth=2)
ax.set_xlabel('Período')
ax.set_ylabel('Taxa de Ocupação')
ax.set_title('Comparação de UFs Extremas')
ax.legend(loc='best')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig('case_studies_ufs.png', dpi=150)
plt.show()
```

---

## 4. Resultados e Análises Esperados

### 4.1 Tabela de Variação Regional

**Tabela: Exposição Regional à IA Generativa por UF**

| Rank | UF | Exposição | Classificação |
|------|-----|-----------|---------------|
| 1 | DF | 0.XXX | Alta |
| 2 | SP | 0.XXX | Alta |
| 3 | RJ | 0.XXX | Alta |
| ... | ... | ... | ... |
| 25 | PI | 0.XXX | Baixa |
| 26 | MA | 0.XXX | Baixa |
| 27 | AC | 0.XXX | Baixa |

**Estatísticas:**
- Média: 0.XXX
- Desvio Padrão: 0.XXX
- Coeficiente de Variação: XX%
- Spread (Max - Min): 0.XXX

### 4.2 Tabela de Resultados DiD Regional

**Tabela: Efeitos DiD Regionais sobre Emprego**

| Variável | (1) Individual | (2) Agregado | (3) Contínuo |
|----------|---------------|--------------|--------------|
| Post × AltaExpRegião | -0.XXX | -0.XXX | - |
|  | (0.XXX) | (0.XXX) | - |
| Post × RegionalExp | - | - | -0.XXX |
|  | - | - | (0.XXX) |
| EF UF | Sim | Sim | Sim |
| EF Período | Sim | Sim | Sim |
| Nível | Individual | UF-Período | Individual |
| N | X,XXX,XXX | XXX | X,XXX,XXX |

### 4.3 Interpretação

**Se β < 0 e significativo:**
"Estados com maior concentração de ocupações expostas à IA (como DF, SP, RJ) experimentaram uma redução de X pontos percentuais na taxa de ocupação após o lançamento do ChatGPT, comparados a estados com menor exposição (como MA, PI, AC)."

**Se β ≈ 0:**
"Não encontramos evidência de efeitos diferenciais entre regiões mais e menos expostas. Isso pode indicar que: (a) efeitos são absorvidos localmente, (b) mobilidade entre regiões equaliza os efeitos, ou (c) o período analisado é curto demais."

### 4.4 Vantagens da Abordagem Regional para sua Dissertação

1. **Narrativa poderosa:** "A desigualdade regional brasileira criou um experimento natural"

2. **Contribuição original:** Primeiro estudo a usar variação regional brasileira para IA generativa

3. **Robustez adicional:** Se encontrar efeitos tanto ocupacionais quanto regionais, reforça a conclusão

4. **Discussão de política:** Implicações para políticas regionais de desenvolvimento

### 4.5 Limitações a Documentar

1. **Número pequeno de clusters:** Com apenas 27 UFs, inferência estatística pode ser frágil

2. **Exposição é composição, não adoção:** Alta exposição não significa que empresas locais adotaram IA

3. **Mobilidade regional:** Trabalhadores podem se mover entre UFs em resposta ao choque

4. **Choques correlacionados:** Sudeste pode ter tendências diferentes por outras razões

---

## Resumo: Checklist de Implementação

### Abordagem 1 (Ocupacional)
- [ ] Baixar PNAD 2021T1-2024T4
- [ ] Merge com índice ILO
- [ ] Criar AltExp (top 20%)
- [ ] Criar Post (≥2023T1)
- [ ] Tabela de balanço
- [ ] Gráfico tendências paralelas
- [ ] DiD básico
- [ ] Event study
- [ ] Heterogeneidade idade/gênero
- [ ] Robustez (10%, 25%, contínuo)

### Abordagem 2 (Regional)
- [ ] Calcular exposição regional com pesos 2021
- [ ] Verificar variação entre UFs
- [ ] Criar mapa de exposição
- [ ] Merge na PNAD completa
- [ ] DiD regional (individual e agregado)
- [ ] Event study regional
- [ ] Case studies de UFs extremas
- [ ] Comparar resultados com Abordagem 1
