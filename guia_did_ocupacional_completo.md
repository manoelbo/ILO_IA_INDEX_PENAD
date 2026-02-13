# Guia Completo: DiD Ocupacional para Análise do Impacto da IA Generativa no Brasil

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Fundamentação Teórica](#2-fundamentação-teórica)
3. [Dados Necessários](#3-dados-necessários)
4. [Passo a Passo Detalhado](#4-passo-a-passo-detalhado)
5. [Especificação Econométrica](#5-especificação-econométrica)
6. [Implementação em Código](#6-implementação-em-código)
7. [Análise de Resultados](#7-análise-de-resultados)
8. [Testes de Robustez](#8-testes-de-robustez)
9. [Limitações e Caveats](#9-limitações-e-caveats)
10. [Checklist Final](#10-checklist-final)

---

# 1. Visão Geral

## 1.1 O Que Estamos Fazendo

Este guia detalha a implementação de uma estratégia de **Difference-in-Differences (DiD)** para estimar o efeito causal da IA Generativa sobre o mercado de trabalho brasileiro, usando variação na **intensidade de exposição ocupacional**.

## 1.2 Pergunta de Pesquisa

> "Após o lançamento do ChatGPT (novembro 2022), trabalhadores em ocupações mais expostas à IA Generativa experimentaram mudanças diferenciais em emprego, horas trabalhadas ou rendimentos, comparados a trabalhadores em ocupações menos expostas?"

## 1.3 Estratégia de Identificação

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     INTUIÇÃO DO DiD OCUPACIONAL                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   PROBLEMA: O ChatGPT afetou TODAS as ocupações ao mesmo tempo.        │
│             Não existe um "grupo de controle puro".                     │
│                                                                         │
│   SOLUÇÃO:  Usar a INTENSIDADE de exposição como tratamento.           │
│             Ocupações mais expostas = "mais tratadas"                   │
│             Ocupações menos expostas = "menos tratadas" (controle)      │
│                                                                         │
│   HIPÓTESE: Se a IA afeta o mercado de trabalho, o efeito deve ser    │
│             MAIOR em ocupações com MAIOR exposição.                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 1.4 Timeline do Projeto

```
DADOS NECESSÁRIOS:
─────────────────────────────────────────────────────────────────────────►
2021T1    2021T4    2022T1    2022T4    2023T1    2023T4    2024T1    2024T4
   │         │         │         │         │         │         │         │
   └─────────┴─────────┴─────────┘         └─────────┴─────────┴─────────┘
        PERÍODO PRÉ-TRATAMENTO                  PERÍODO PÓS-TRATAMENTO
           (8 trimestres)                          (8+ trimestres)
                                    ▲
                                    │
                            Novembro 2022
                          Lançamento ChatGPT
```

---

# 2. Fundamentação Teórica

## 2.1 O Que é Difference-in-Differences?

O DiD é uma técnica de inferência causal que estima o efeito de um tratamento comparando:
- A **mudança ao longo do tempo** no grupo tratado
- Com a **mudança ao longo do tempo** no grupo controle

### Fórmula Básica

```
Efeito Causal (β) = [E(Y|Tratado, Pós) - E(Y|Tratado, Pré)]
                  - [E(Y|Controle, Pós) - E(Y|Controle, Pré)]
```

### Representação Visual

```
                    Outcome (Y)
                         │
    Tratados (observado) │                    ●────── Observado
                         │                   /
                         │                  /
    Controles            │    ●────────────●
                         │   /            /
                         │  /            /
    Tratados             │ ●            ○────── Contrafactual
    (contrafactual)      │             (não observado)
                         │
                         └──────────────┬──────────────►
                                    Tratamento         Tempo
                                    
    β = Distância entre ● observado e ○ contrafactual no período pós
```

## 2.2 Hipótese de Identificação: Tendências Paralelas

A validade do DiD depende da **hipótese de tendências paralelas**:

> "Na ausência do tratamento, o grupo tratado teria evoluído de forma paralela ao grupo controle."

### O Que Isso Significa na Prática

- **Antes do ChatGPT:** Ocupações de alta e baixa exposição podem ter níveis diferentes de emprego, mas devem estar **mudando na mesma direção e velocidade**.
- **Não é necessário:** Que os grupos sejam idênticos em nível.
- **É necessário:** Que não haja tendências pré-existentes diferentes.

### Como Testar

Usamos um **Event Study** que estima coeficientes separados para cada período. Se os coeficientes pré-tratamento forem estatisticamente iguais a zero, há evidência de tendências paralelas.

## 2.3 Por Que Essa Estratégia Funciona (ou Pode Funcionar)

### Argumentos a Favor

1. **Choque Exógeno:** O lançamento do ChatGPT foi um evento tecnológico, não uma resposta a condições do mercado de trabalho brasileiro.

2. **Variação Pré-Determinada:** O índice de exposição ILO foi construído com base em características das tarefas, não em resultados do mercado de trabalho.

3. **Timing Preciso:** Sabemos exatamente quando o tratamento ocorreu (novembro 2022).

### Potenciais Problemas

1. **Tendências Pré-Existentes:** Ocupações cognitivas já estavam em trajetória diferente (ex: crescimento de TI).

2. **Choques Correlacionados:** Outros eventos (juros, pandemia) podem ter afetado ocupações expostas de forma diferente.

3. **Erro de Medida:** Classificação ocupacional na PNAD pode ser imprecisa.

---

# 3. Dados Necessários

## 3.1 Fonte Principal: PNAD Contínua

### Características

| Aspecto | Detalhe |
|---------|---------|
| **Fonte** | IBGE - Instituto Brasileiro de Geografia e Estatística |
| **Periodicidade** | Trimestral |
| **Cobertura** | Brasil inteiro (urbano e rural) |
| **Amostra** | ~211.000 domicílios/trimestre, ~500.000 pessoas |
| **Período Necessário** | 2021T1 a 2024T4 (mínimo) |

### Variáveis Necessárias da PNAD

| Variável | Código PNAD | Descrição | Uso |
|----------|-------------|-----------|-----|
| **Identificação** | | | |
| UF | UF | Unidade da Federação | Controle regional |
| Ano | Ano | Ano de referência | Construir período |
| Trimestre | Trimestre | Trimestre de referência | Construir período |
| **Demográficas** | | | |
| Idade | V2009 | Idade em anos | Controle + heterogeneidade |
| Sexo | V2007 | Masculino/Feminino | Controle + heterogeneidade |
| Raça/Cor | V2010 | Branca, Preta, Parda, etc. | Controle + análise distributiva |
| **Educação** | | | |
| Anos de estudo | VD3005 | Anos de estudo completos | Controle |
| Nível de instrução | VD3004 | Nível mais alto concluído | Controle |
| **Trabalho** | | | |
| Ocupação | V4010 | Código COD (4 dígitos) | **Variável-chave para merge** |
| Condição de ocupação | VD4002 | Ocupado/Desocupado | **Outcome principal** |
| Horas trabalhadas | VD4035 | Horas na semana de referência | Outcome secundário |
| Rendimento habitual | VD4016 | Rendimento mensal habitual | Outcome secundário |
| Posição na ocupação | VD4008 | Empregado, conta própria, etc. | Identificar formalidade |
| Tipo de vínculo | VD4009 | Com/sem carteira, estatutário | Identificar formalidade |
| **Peso Amostral** | | | |
| Peso | V1028 | Peso da pessoa | **Obrigatório para inferência** |

## 3.2 Índice de Exposição: ILO GenAI Exposure Index

### Características

| Aspecto | Detalhe |
|---------|---------|
| **Fonte** | Gmyrek, Berg et al. (2025) - ILO Working Paper |
| **Classificação** | ISCO-08 (4 dígitos) |
| **Metodologia** | LLM classifica tarefas + validação humana |
| **Escala** | 0 (nenhuma exposição) a 1 (exposição total) |
| **Cobertura** | ~430 ocupações ISCO-08 |

### Variáveis do Índice ILO

| Variável | Descrição | Uso |
|----------|-----------|-----|
| `isco08_code` | Código ISCO-08 (4 dígitos) | Chave para merge |
| `exposure_score` | Índice de exposição geral | **Tratamento principal** |
| `automation_score` | Potencial de automação | Análise complementar |
| `augmentation_score` | Potencial de aumentação | Análise complementar |

## 3.3 Compatibilidade COD-ISCO

### Boa Notícia

A variável V4010 da PNAD Contínua usa a **Classificação de Ocupações para Pesquisas Domiciliares (COD)**, que é baseada diretamente na **ISCO-08**. Os primeiros 4 dígitos são compatíveis.

```
V4010 (PNAD) = XXXX = ISCO-08 (4 dígitos)

Exemplo:
V4010 = 2512 → ISCO-08 2512 → "Desenvolvedores de software"
```

### Procedimento de Merge

```python
# O merge é direto!
pnad['isco08'] = pnad['V4010'].astype(str).str.zfill(4)
pnad = pnad.merge(ilo_index, left_on='isco08', right_on='isco08_code', how='left')
```

## 3.4 Estrutura Final dos Dados

Após preparação, sua base deve ter esta estrutura:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ESTRUTURA DA BASE FINAL                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Unidade de observação: Indivíduo i, na ocupação o, no período t           │
│                                                                             │
│  Dimensões:                                                                 │
│  - N indivíduos: ~4-5 milhões por trimestre × 16 trimestres ≈ 70-80M obs   │
│  - N ocupações: ~400 códigos ISCO-08                                        │
│  - N períodos: 16 trimestres (2021T1 a 2024T4)                             │
│                                                                             │
│  Variáveis principais:                                                      │
│  - Y (outcomes): ocupado, horas_trabalhadas, ln_renda, formal              │
│  - Tratamento: exposure_score, alta_exposicao (dummy)                       │
│  - Tempo: periodo, post (dummy ≥2023T1)                                    │
│  - Controles: idade, sexo, raca, escolaridade, UF                          │
│  - Peso: peso_amostral                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 4. Passo a Passo Detalhado

## Fase 1: Aquisição de Dados

### Passo 1.1: Baixar PNAD Contínua

**Opção A: Via Base dos Dados (Recomendado)**

Vantagens: Dados já limpos, BigQuery permite queries eficientes, gratuito até certo limite.

```python
# Instalar pacote
# pip install basedosdados

from basedosdados import read_sql

query = """
SELECT 
    -- Identificação
    ano,
    trimestre,
    sigla_uf AS uf,
    id_domicilio,
    
    -- Demográficas
    V2007 AS sexo,
    V2009 AS idade,
    V2010 AS raca,
    
    -- Educação
    VD3004 AS nivel_instrucao,
    VD3005 AS anos_estudo,
    
    -- Trabalho
    V4010 AS cod_ocupacao,
    VD4002 AS condicao_ocupacao,
    VD4008 AS posicao_ocupacao,
    VD4009 AS tipo_vinculo,
    VD4016 AS rendimento_habitual,
    VD4035 AS horas_trabalhadas,
    
    -- Peso
    V1028 AS peso

FROM `basedosdados.br_ibge_pnadc.microdados`

WHERE ano >= 2021
  AND ano <= 2024
  AND V2009 >= 18  -- Idade mínima
  AND V2009 <= 65  -- Idade máxima
"""

print("Iniciando download... (pode levar alguns minutos)")
pnad = read_sql(query, billing_project_id="seu-projeto-gcp")
print(f"Download concluído: {len(pnad):,} observações")
```

**Opção B: Via FTP do IBGE**

Para quem prefere trabalhar com arquivos locais.

```python
import requests
import zipfile
import os

def baixar_pnad_trimestre(ano, trimestre, pasta_destino='./dados_pnad'):
    """Baixa microdados de um trimestre específico do FTP do IBGE"""
    
    os.makedirs(pasta_destino, exist_ok=True)
    
    # URL do FTP do IBGE
    url = f"https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/{ano}/PNADC_{ano}{trimestre:02d}.zip"
    
    arquivo_zip = f"{pasta_destino}/PNADC_{ano}{trimestre:02d}.zip"
    
    print(f"Baixando {ano}T{trimestre}...")
    response = requests.get(url, stream=True)
    
    with open(arquivo_zip, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Extrair
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        zip_ref.extractall(pasta_destino)
    
    print(f"Concluído: {ano}T{trimestre}")

# Baixar todos os trimestres necessários
for ano in range(2021, 2025):
    for tri in range(1, 5):
        try:
            baixar_pnad_trimestre(ano, tri)
        except Exception as e:
            print(f"Erro em {ano}T{tri}: {e}")
```

### Passo 1.2: Baixar Índice ILO

```python
import pandas as pd

# O índice ILO está disponível no material suplementar do Working Paper
# URL aproximada (verificar versão mais recente)
url_ilo = "https://www.ilo.org/sites/default/files/2024-08/genai_exposure_by_isco08.csv"

ilo_index = pd.read_csv(url_ilo)

# Verificar estrutura
print("Estrutura do índice ILO:")
print(ilo_index.head())
print(f"\nTotal de ocupações: {len(ilo_index)}")
print(f"\nEstatísticas do exposure_score:")
print(ilo_index['exposure_score'].describe())
```

**Alternativa: Usar seu arquivo já construído**

Se você já fez o crosswalk ILO → COD na Etapa 1 do projeto:

```python
ilo_index = pd.read_csv('dados/ilo_exposure_by_cod.csv')
```

---

## Fase 2: Limpeza e Preparação

### Passo 2.1: Limpeza Básica

```python
def limpar_pnad(df):
    """
    Realiza limpeza básica dos dados da PNAD Contínua.
    
    Parâmetros:
    -----------
    df : DataFrame
        Dados brutos da PNAD
        
    Retorna:
    --------
    DataFrame limpo
    """
    
    # Criar cópia
    df = df.copy()
    
    # =========================================
    # 1. CONVERSÃO DE TIPOS
    # =========================================
    
    # Numéricas
    vars_numericas = ['idade', 'anos_estudo', 'rendimento_habitual', 
                      'horas_trabalhadas', 'peso']
    for var in vars_numericas:
        if var in df.columns:
            df[var] = pd.to_numeric(df[var], errors='coerce')
    
    # Strings (para códigos)
    df['cod_ocupacao'] = df['cod_ocupacao'].astype(str).str.strip()
    df['uf'] = df['uf'].astype(str).str.strip()
    
    # =========================================
    # 2. FILTROS DE QUALIDADE
    # =========================================
    
    n_inicial = len(df)
    
    # Idade válida (18-65)
    df = df[(df['idade'] >= 18) & (df['idade'] <= 65)]
    
    # Peso válido
    df = df[df['peso'] > 0]
    
    # Ocupação válida (não missing, não "0000")
    df = df[df['cod_ocupacao'].notna()]
    df = df[df['cod_ocupacao'] != '']
    df = df[df['cod_ocupacao'] != '0000']
    
    n_final = len(df)
    print(f"Filtros aplicados: {n_inicial:,} → {n_final:,} ({n_final/n_inicial:.1%} mantido)")
    
    # =========================================
    # 3. PADRONIZAÇÃO DE CÓDIGOS
    # =========================================
    
    # COD ocupação: garantir 4 dígitos
    df['cod_ocupacao'] = df['cod_ocupacao'].str[:4].str.zfill(4)
    
    return df

# Aplicar limpeza
pnad = limpar_pnad(pnad)
```

### Passo 2.2: Criação de Variáveis

```python
def criar_variaveis(df):
    """
    Cria todas as variáveis necessárias para a análise.
    
    Variáveis criadas:
    - Temporais: periodo, periodo_num, post, tempo_relativo
    - Outcomes: ocupado, formal, ln_renda
    - Demográficas: mulher, negro_pardo, jovem, faixa_etaria
    - Educação: superior
    """
    
    df = df.copy()
    
    # =========================================
    # 1. VARIÁVEIS TEMPORAIS
    # =========================================
    
    # Período como string (para gráficos)
    df['periodo'] = df['ano'].astype(str) + 'T' + df['trimestre'].astype(str)
    
    # Período numérico (para ordenação e cálculos)
    df['periodo_num'] = df['ano'] * 10 + df['trimestre']
    
    # Período de referência: 2022T4 (último antes do ChatGPT)
    PERIODO_REF = 20224
    
    # Tempo relativo ao período de referência
    # -1 = 2022T3, 0 = 2022T4 (referência), 1 = 2023T1, etc.
    df['tempo_relativo'] = df['periodo_num'] - PERIODO_REF
    
    # Dummy pós-tratamento (ChatGPT lançado nov/2022, efeitos a partir de 2023T1)
    df['post'] = (df['periodo_num'] >= 20231).astype(int)
    
    print(f"Períodos pré-tratamento: {df[df['post']==0]['periodo'].nunique()}")
    print(f"Períodos pós-tratamento: {df[df['post']==1]['periodo'].nunique()}")
    
    # =========================================
    # 2. VARIÁVEIS DE OUTCOME
    # =========================================
    
    # Ocupado (VD4002: 1 = ocupado)
    df['ocupado'] = (df['condicao_ocupacao'] == '1').astype(int)
    
    # Formal (simplificado: com carteira, estatutário, ou militar)
    # VD4009: 01-04 = formal, 05-10 = informal
    condicoes_formal = ['01', '02', '03', '04']
    df['formal'] = df['tipo_vinculo'].isin(condicoes_formal).astype(int)
    
    # Informal (complemento)
    df['informal'] = 1 - df['formal']
    
    # Log do rendimento (apenas para quem tem rendimento positivo)
    df['ln_renda'] = np.where(
        df['rendimento_habitual'] > 0,
        np.log(df['rendimento_habitual']),
        np.nan
    )
    
    # =========================================
    # 3. VARIÁVEIS DEMOGRÁFICAS
    # =========================================
    
    # Sexo: mulher
    df['mulher'] = (df['sexo'] == '2').astype(int)
    
    # Raça: negro ou pardo
    # V2010: 1=Branca, 2=Preta, 3=Amarela, 4=Parda, 5=Indígena
    df['negro_pardo'] = df['raca'].isin(['2', '4']).astype(int)
    
    # Faixas etárias
    df['faixa_etaria'] = pd.cut(
        df['idade'],
        bins=[18, 25, 30, 40, 50, 65],
        labels=['18-25', '26-30', '31-40', '41-50', '51-65'],
        include_lowest=True
    )
    
    # Jovem (para heterogeneidade - comparável com Brynjolfsson)
    df['jovem'] = (df['idade'] <= 30).astype(int)
    
    # Jovem estrito (22-25, exatamente como Brynjolfsson)
    df['jovem_estrito'] = ((df['idade'] >= 22) & (df['idade'] <= 25)).astype(int)
    
    # =========================================
    # 4. VARIÁVEIS DE EDUCAÇÃO
    # =========================================
    
    # Superior completo (VD3004 >= 7 ou anos_estudo >= 15)
    df['superior'] = (df['anos_estudo'] >= 15).astype(int)
    
    # Médio completo
    df['medio'] = (df['anos_estudo'] >= 11).astype(int)
    
    return df

# Aplicar criação de variáveis
pnad = criar_variaveis(pnad)
```

### Passo 2.3: Merge com Índice ILO

```python
def merge_exposicao(df, ilo_index):
    """
    Faz merge dos dados da PNAD com o índice de exposição ILO.
    
    Parâmetros:
    -----------
    df : DataFrame
        PNAD preparada
    ilo_index : DataFrame
        Índice ILO com colunas: isco08_code, exposure_score, etc.
        
    Retorna:
    --------
    DataFrame com exposição anexada
    """
    
    # Garantir que códigos estão no mesmo formato
    df['cod_ocupacao'] = df['cod_ocupacao'].str.zfill(4)
    ilo_index['isco08_code'] = ilo_index['isco08_code'].astype(str).str.zfill(4)
    
    # Merge
    n_antes = len(df)
    df = df.merge(
        ilo_index[['isco08_code', 'exposure_score', 'automation_score', 'augmentation_score']],
        left_on='cod_ocupacao',
        right_on='isco08_code',
        how='left'
    )
    
    # Verificar cobertura
    cobertura = df['exposure_score'].notna().mean()
    print(f"Cobertura do merge: {cobertura:.1%}")
    
    # Listar ocupações sem match (para diagnóstico)
    sem_match = df[df['exposure_score'].isna()]['cod_ocupacao'].unique()
    if len(sem_match) > 0:
        print(f"\nOcupações sem match ({len(sem_match)}):")
        for cod in sem_match[:10]:  # Mostrar apenas 10 primeiras
            print(f"  - {cod}")
        if len(sem_match) > 10:
            print(f"  ... e mais {len(sem_match)-10}")
    
    return df

# Aplicar merge
pnad = merge_exposicao(pnad, ilo_index)
```

### Passo 2.4: Criar Variáveis de Tratamento

```python
def criar_tratamento(df, percentil_corte=80):
    """
    Cria variáveis de tratamento (alta exposição).
    
    Parâmetros:
    -----------
    df : DataFrame
        PNAD com exposição
    percentil_corte : int
        Percentil para definir "alta exposição" (default: 80 = top 20%)
        
    Retorna:
    --------
    DataFrame com variáveis de tratamento
    """
    
    df = df.copy()
    
    # Calcular thresholds
    threshold_20 = df['exposure_score'].quantile(0.80)  # Top 20%
    threshold_10 = df['exposure_score'].quantile(0.90)  # Top 10%
    threshold_25 = df['exposure_score'].quantile(0.75)  # Top 25%
    
    print("Thresholds de exposição:")
    print(f"  Top 25% (p75): {threshold_25:.4f}")
    print(f"  Top 20% (p80): {threshold_20:.4f}")
    print(f"  Top 10% (p90): {threshold_10:.4f}")
    
    # Criar dummies de alta exposição
    df['alta_exp'] = (df['exposure_score'] >= threshold_20).astype(int)
    df['alta_exp_10'] = (df['exposure_score'] >= threshold_10).astype(int)
    df['alta_exp_25'] = (df['exposure_score'] >= threshold_25).astype(int)
    
    # Criar quintis de exposição
    df['quintil_exp'] = pd.qcut(
        df['exposure_score'],
        q=5,
        labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
    )
    
    # Criar interação DiD principal
    df['did'] = df['post'] * df['alta_exp']
    
    # Verificar distribuição
    print("\nDistribuição do tratamento:")
    print(df.groupby(['post', 'alta_exp']).agg({
        'peso': 'sum'
    }).unstack().round(0))
    
    return df, {
        'threshold_20': threshold_20,
        'threshold_10': threshold_10,
        'threshold_25': threshold_25
    }

# Aplicar
pnad, thresholds = criar_tratamento(pnad)
```

---

## Fase 3: Análise Descritiva Pré-Regressão

### Passo 3.1: Tabela de Balanço

```python
def tabela_balanco(df, tratamento='alta_exp', peso='peso', periodo='pre'):
    """
    Cria tabela de balanço comparando grupos tratado e controle.
    
    Esta tabela é ESSENCIAL para verificar comparabilidade dos grupos.
    """
    
    # Filtrar período
    if periodo == 'pre':
        df = df[df['post'] == 0]
        titulo = "PERÍODO PRÉ-TRATAMENTO"
    else:
        titulo = "TODOS OS PERÍODOS"
    
    # Variáveis para comparar
    variaveis = {
        'idade': 'Idade (anos)',
        'mulher': 'Mulher (%)',
        'negro_pardo': 'Negro/Pardo (%)',
        'superior': 'Superior completo (%)',
        'medio': 'Médio completo (%)',
        'rendimento_habitual': 'Rendimento (R$)',
        'horas_trabalhadas': 'Horas trabalhadas',
        'formal': 'Formal (%)',
        'ocupado': 'Taxa de ocupação (%)'
    }
    
    resultados = []
    
    for var, nome in variaveis.items():
        if var not in df.columns:
            continue
            
        # Remover missing
        df_var = df[df[var].notna()]
        
        # Médias ponderadas
        controle = df_var[df_var[tratamento] == 0]
        tratado = df_var[df_var[tratamento] == 1]
        
        media_c = np.average(controle[var], weights=controle[peso])
        media_t = np.average(tratado[var], weights=tratado[peso])
        
        # Desvios padrão
        std_c = np.sqrt(np.average((controle[var] - media_c)**2, weights=controle[peso]))
        std_t = np.sqrt(np.average((tratado[var] - media_t)**2, weights=tratado[peso]))
        
        # Diferença normalizada (para avaliar magnitude)
        diff_norm = (media_t - media_c) / np.sqrt((std_c**2 + std_t**2) / 2)
        
        resultados.append({
            'Variável': nome,
            'Controle': f"{media_c:.2f}",
            'Tratamento': f"{media_t:.2f}",
            'Diferença': f"{media_t - media_c:.2f}",
            'Diff. Normalizada': f"{diff_norm:.3f}"
        })
    
    tabela = pd.DataFrame(resultados)
    
    print(f"\n{'='*70}")
    print(f"TABELA DE BALANÇO - {titulo}")
    print(f"{'='*70}")
    print(f"Controle = Baixa Exposição | Tratamento = Alta Exposição (top 20%)")
    print(f"{'='*70}")
    print(tabela.to_string(index=False))
    print(f"{'='*70}")
    print("Nota: Diff. Normalizada > |0.25| indica desequilíbrio substancial")
    
    return tabela

# Gerar tabela
tabela_bal = tabela_balanco(pnad)
```

### Passo 3.2: Gráfico de Tendências Paralelas

```python
def plot_tendencias_paralelas(df, outcome='ocupado', tratamento='alta_exp', 
                               peso='peso', titulo=None):
    """
    Plota tendências do outcome por grupo de tratamento.
    
    Este gráfico é CRUCIAL para avaliar visualmente a hipótese de 
    tendências paralelas.
    """
    
    # Calcular médias ponderadas por período e grupo
    tendencias = (
        df.groupby(['periodo', 'periodo_num', tratamento])
        .apply(lambda x: np.average(x[outcome].dropna(), 
                                   weights=x.loc[x[outcome].notna(), peso]))
        .reset_index(name=outcome)
    )
    
    # Separar grupos
    controle = tendencias[tendencias[tratamento] == 0].sort_values('periodo_num')
    tratado = tendencias[tendencias[tratamento] == 1].sort_values('periodo_num')
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plotar linhas
    ax.plot(controle['periodo'], controle[outcome], 
            'o-', color='#2ecc71', linewidth=2.5, markersize=10,
            label='Baixa Exposição (controle)', markeredgecolor='white', markeredgewidth=2)
    
    ax.plot(tratado['periodo'], tratado[outcome], 
            's-', color='#e74c3c', linewidth=2.5, markersize=10,
            label='Alta Exposição (tratamento)', markeredgecolor='white', markeredgewidth=2)
    
    # Linha vertical no tratamento
    ax.axvline(x='2022T4', color='#34495e', linestyle='--', linewidth=2,
               label='Lançamento ChatGPT (Nov/2022)', alpha=0.7)
    
    # Sombrear região pré e pós
    periodos = list(controle['periodo'])
    idx_chatgpt = periodos.index('2022T4') if '2022T4' in periodos else len(periodos)//2
    
    ax.axvspan(-0.5, idx_chatgpt + 0.5, alpha=0.1, color='blue', label='Período Pré')
    ax.axvspan(idx_chatgpt + 0.5, len(periodos) - 0.5, alpha=0.1, color='red', label='Período Pós')
    
    # Formatação
    ax.set_xlabel('Período', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'{outcome.replace("_", " ").title()}', fontsize=12, fontweight='bold')
    
    if titulo:
        ax.set_title(titulo, fontsize=14, fontweight='bold')
    else:
        ax.set_title(f'Tendências de {outcome.replace("_", " ").title()} por Grupo de Exposição', 
                    fontsize=14, fontweight='bold')
    
    ax.legend(loc='best', fontsize=10)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    
    # Adicionar anotação
    ax.annotate('Verificar paralelismo\nantes da linha vertical',
                xy=(periodos[2], tratado[outcome].iloc[2]),
                xytext=(periodos[0], tratado[outcome].iloc[2] + 0.02),
                fontsize=9, style='italic',
                arrowprops=dict(arrowstyle='->', color='gray'))
    
    plt.tight_layout()
    plt.savefig(f'tendencias_paralelas_{outcome}.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    return fig

# Gerar gráficos para diferentes outcomes
for outcome in ['ocupado', 'horas_trabalhadas', 'ln_renda', 'formal']:
    try:
        plot_tendencias_paralelas(pnad, outcome=outcome)
    except Exception as e:
        print(f"Erro ao plotar {outcome}: {e}")
```

### Passo 3.3: Estatísticas por Quintil de Exposição

```python
def estatisticas_por_quintil(df, peso='peso'):
    """
    Calcula estatísticas descritivas por quintil de exposição.
    """
    
    # Usar apenas período pré para caracterização
    df_pre = df[df['post'] == 0]
    
    stats = []
    
    for quintil in df_pre['quintil_exp'].unique():
        if pd.isna(quintil):
            continue
            
        subset = df_pre[df_pre['quintil_exp'] == quintil]
        
        # Exposição média do quintil
        exp_media = np.average(subset['exposure_score'], weights=subset[peso])
        
        # Características
        stats.append({
            'Quintil': quintil,
            'Exposição Média': f"{exp_media:.3f}",
            'N (milhões)': f"{subset[peso].sum()/1e6:.1f}",
            'Idade Média': f"{np.average(subset['idade'], weights=subset[peso]):.1f}",
            '% Mulher': f"{np.average(subset['mulher'], weights=subset[peso])*100:.1f}",
            '% Negro/Pardo': f"{np.average(subset['negro_pardo'], weights=subset[peso])*100:.1f}",
            '% Superior': f"{np.average(subset['superior'], weights=subset[peso])*100:.1f}",
            'Renda Média': f"{np.average(subset['rendimento_habitual'].dropna(), weights=subset.loc[subset['rendimento_habitual'].notna(), peso]):.0f}",
            '% Formal': f"{np.average(subset['formal'], weights=subset[peso])*100:.1f}"
        })
    
    tabela = pd.DataFrame(stats)
    
    print("\n" + "="*90)
    print("CARACTERÍSTICAS POR QUINTIL DE EXPOSIÇÃO À IA (Período Pré-Tratamento)")
    print("="*90)
    print(tabela.to_string(index=False))
    print("="*90)
    
    return tabela

# Gerar tabela
stats_quintil = estatisticas_por_quintil(pnad)
```

---

## Fase 4: Estimação

### Passo 4.1: DiD Médio (Modelo Principal)

```python
import pyfixest as pf

def estimar_did_medio(df, outcome='ocupado', tratamento='alta_exp', 
                       controles=True, fe_ocupacao=True, fe_periodo=True):
    """
    Estima o modelo DiD médio.
    
    Parâmetros:
    -----------
    outcome : str
        Variável dependente
    tratamento : str
        Variável de tratamento (dummy)
    controles : bool
        Incluir controles individuais
    fe_ocupacao : bool
        Incluir efeito fixo de ocupação
    fe_periodo : bool
        Incluir efeito fixo de período
    """
    
    # Construir fórmula
    # Termo DiD
    did_term = f"post:{tratamento}"
    
    # Controles
    if controles:
        controls = "+ idade + I(idade**2) + mulher + negro_pardo + superior"
    else:
        controls = ""
    
    # Efeitos fixos
    fe_terms = []
    if fe_ocupacao:
        fe_terms.append("cod_ocupacao")
    if fe_periodo:
        fe_terms.append("periodo")
    
    if fe_terms:
        fe = " | " + " + ".join(fe_terms)
    else:
        fe = ""
    
    # Fórmula completa
    formula = f"{outcome} ~ {did_term} {controls} {fe}"
    
    print(f"\nEstimando: {formula}\n")
    
    # Filtrar dados
    df_reg = df[df[outcome].notna()].copy()
    
    # Estimar
    modelo = pf.feols(
        formula,
        data=df_reg,
        weights="peso",
        vcov={"CRV1": "cod_ocupacao"}  # Cluster por ocupação
    )
    
    return modelo

# ===============================================
# ESTIMAR DIFERENTES ESPECIFICAÇÕES
# ===============================================

print("="*70)
print("RESULTADOS DiD - VARIÁVEL DEPENDENTE: OCUPAÇÃO")
print("="*70)

# Modelo 1: Apenas DiD, sem controles, sem FE
modelo1 = estimar_did_medio(pnad, controles=False, fe_ocupacao=False, fe_periodo=False)
print("\nMODELO 1: DiD Simples (sem controles, sem FE)")
print(modelo1.summary())

# Modelo 2: Com FE, sem controles individuais
modelo2 = estimar_did_medio(pnad, controles=False, fe_ocupacao=True, fe_periodo=True)
print("\nMODELO 2: DiD com Efeitos Fixos")
print(modelo2.summary())

# Modelo 3: Completo (com controles e FE)
modelo3 = estimar_did_medio(pnad, controles=True, fe_ocupacao=True, fe_periodo=True)
print("\nMODELO 3: DiD Completo (controles + FE)")
print(modelo3.summary())

# Modelo 4: Tratamento contínuo
modelo4 = pf.feols(
    "ocupado ~ post:exposure_score + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo",
    data=pnad[pnad['ocupado'].notna()],
    weights="peso",
    vcov={"CRV1": "cod_ocupacao"}
)
print("\nMODELO 4: Exposição Contínua")
print(modelo4.summary())
```

### Passo 4.2: Event Study

```python
def estimar_event_study(df, outcome='ocupado', tratamento='alta_exp',
                         periodo_ref='2022T4'):
    """
    Estima modelo de Event Study.
    
    O Event Study estima um coeficiente para cada período, permitindo:
    1. Testar tendências paralelas (coefs pré devem ser ~0)
    2. Ver a dinâmica do efeito ao longo do tempo
    """
    
    df = df.copy()
    
    # Obter lista de períodos ordenada
    periodos = sorted(df['periodo'].unique())
    
    # Criar dummies de interação período × tratamento
    # (exceto período de referência)
    for p in periodos:
        if p != periodo_ref:
            df[f'did_{p}'] = ((df['periodo'] == p) & (df[tratamento] == 1)).astype(int)
    
    # Lista de variáveis DiD
    vars_did = [f'did_{p}' for p in periodos if p != periodo_ref]
    
    # Fórmula
    formula = f"{outcome} ~ {' + '.join(vars_did)} + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo"
    
    print(f"Estimando Event Study com {len(vars_did)} coeficientes...")
    
    # Estimar
    modelo = pf.feols(
        formula,
        data=df[df[outcome].notna()],
        weights="peso",
        vcov={"CRV1": "cod_ocupacao"}
    )
    
    # Extrair coeficientes
    coefs = []
    for p in periodos:
        if p == periodo_ref:
            coefs.append({
                'periodo': p,
                'coef': 0,
                'se': 0,
                'ci_low': 0,
                'ci_high': 0,
                'pvalue': np.nan
            })
        else:
            var = f'did_{p}'
            coef = modelo.coef()[var]
            se = modelo.se()[var]
            pval = modelo.pvalue()[var]
            coefs.append({
                'periodo': p,
                'coef': coef,
                'se': se,
                'ci_low': coef - 1.96 * se,
                'ci_high': coef + 1.96 * se,
                'pvalue': pval
            })
    
    coefs_df = pd.DataFrame(coefs)
    
    return modelo, coefs_df

# Estimar
modelo_es, coefs_es = estimar_event_study(pnad)

# Mostrar coeficientes
print("\nCOEFICIENTES DO EVENT STUDY")
print("="*70)
print(coefs_es.to_string(index=False))
```

### Passo 4.3: Gráfico do Event Study

```python
def plot_event_study(coefs_df, periodo_ref='2022T4', titulo=None):
    """
    Plota os coeficientes do Event Study com intervalos de confiança.
    """
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Encontrar índice do período de referência
    periodos = list(coefs_df['periodo'])
    idx_ref = periodos.index(periodo_ref)
    
    # Cores diferentes para pré e pós
    cores = ['#3498db' if i <= idx_ref else '#e74c3c' for i in range(len(periodos))]
    
    # Plotar pontos e intervalos de confiança
    x = range(len(coefs_df))
    
    for i, (xi, row) in enumerate(zip(x, coefs_df.itertuples())):
        cor = cores[i]
        
        # Intervalo de confiança
        ax.plot([xi, xi], [row.ci_low, row.ci_high], 
                color=cor, linewidth=2, alpha=0.6)
        
        # Ponto
        marker = 'o' if i <= idx_ref else 's'
        ax.scatter(xi, row.coef, color=cor, s=100, marker=marker, 
                   zorder=5, edgecolors='white', linewidth=2)
    
    # Linha horizontal em zero
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    # Linha vertical no tratamento
    ax.axvline(x=idx_ref + 0.5, color='#e74c3c', linestyle='--', 
               linewidth=2, alpha=0.7)
    
    # Sombrear regiões
    ax.axvspan(-0.5, idx_ref + 0.5, alpha=0.1, color='blue')
    ax.axvspan(idx_ref + 0.5, len(periodos) - 0.5, alpha=0.1, color='red')
    
    # Anotações
    ax.annotate('PRÉ-TRATAMENTO\n(testar ≈ 0)', 
                xy=(idx_ref/2, ax.get_ylim()[1]*0.8),
                fontsize=10, ha='center', color='#3498db', fontweight='bold')
    
    ax.annotate('PÓS-TRATAMENTO\n(efeito causal)', 
                xy=(idx_ref + (len(periodos)-idx_ref)/2, ax.get_ylim()[1]*0.8),
                fontsize=10, ha='center', color='#e74c3c', fontweight='bold')
    
    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels(periodos, rotation=45, ha='right')
    ax.set_xlabel('Período', fontsize=12, fontweight='bold')
    ax.set_ylabel('Coeficiente DiD (efeito sobre probabilidade de ocupação)', 
                  fontsize=12, fontweight='bold')
    
    if titulo:
        ax.set_title(titulo, fontsize=14, fontweight='bold')
    else:
        ax.set_title('Event Study: Efeito da Exposição à IA sobre Emprego\n' + 
                    '(período de referência: 2022T4)', fontsize=14, fontweight='bold')
    
    # Grid
    ax.grid(True, alpha=0.3, axis='y')
    
    # Legenda
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='#3498db', label='Pré-tratamento', 
               markersize=10, linestyle='None'),
        Line2D([0], [0], marker='s', color='#e74c3c', label='Pós-tratamento', 
               markersize=10, linestyle='None'),
        Line2D([0], [0], color='#e74c3c', linestyle='--', label='ChatGPT', linewidth=2)
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('event_study.png', dpi=200, bbox_inches='tight')
    plt.show()
    
    return fig

# Plotar
plot_event_study(coefs_es)
```

### Passo 4.4: Heterogeneidade por Idade

```python
def estimar_heterogeneidade_idade(df, outcome='ocupado'):
    """
    Estima heterogeneidade do efeito por idade usando triple-DiD.
    
    Pergunta: O efeito da IA é MAIOR para jovens do que para experientes?
    """
    
    # Modelo com interação tripla
    formula = """
    {outcome} ~ post:alta_exp:jovem + post:alta_exp + post:jovem + alta_exp:jovem
              + idade + I(idade**2) + mulher + negro_pardo + superior 
              | cod_ocupacao + periodo
    """.format(outcome=outcome)
    
    modelo = pf.feols(
        formula,
        data=df[df[outcome].notna()],
        weights="peso",
        vcov={"CRV1": "cod_ocupacao"}
    )
    
    print("\n" + "="*70)
    print("HETEROGENEIDADE POR IDADE (Triple-DiD)")
    print("="*70)
    print(modelo.summary())
    
    # Interpretação
    print("\nINTERPRETAÇÃO:")
    print("-" * 50)
    print("post:alta_exp       = Efeito para NÃO-jovens (>30 anos)")
    print("post:alta_exp:jovem = Efeito ADICIONAL para jovens (≤30 anos)")
    print("                      (se negativo, jovens são mais afetados)")
    print("-" * 50)
    
    # Calcular efeito total para jovens
    coef_base = modelo.coef()['post:alta_exp']
    coef_jovem = modelo.coef()['post:alta_exp:jovem']
    efeito_jovens = coef_base + coef_jovem
    
    print(f"\nEfeito para não-jovens:  {coef_base:.4f}")
    print(f"Efeito adicional jovens: {coef_jovem:.4f}")
    print(f"Efeito total para jovens: {efeito_jovens:.4f}")
    
    return modelo

# Estimar
modelo_idade = estimar_heterogeneidade_idade(pnad)
```

### Passo 4.5: Event Study por Faixa Etária

```python
def event_study_por_grupo(df, grupo_var, grupo_valores, outcome='ocupado'):
    """
    Estima event studies separados para diferentes grupos.
    
    Útil para comparar visualmente a dinâmica do efeito entre grupos.
    """
    
    resultados = {}
    
    for valor, nome in grupo_valores.items():
        print(f"\nEstimando para: {nome}")
        
        # Filtrar
        df_grupo = df[df[grupo_var] == valor].copy()
        
        if len(df_grupo) < 1000:
            print(f"  Atenção: apenas {len(df_grupo)} observações")
            continue
        
        # Estimar
        try:
            _, coefs = estimar_event_study(df_grupo, outcome=outcome)
            coefs['grupo'] = nome
            resultados[nome] = coefs
        except Exception as e:
            print(f"  Erro: {e}")
    
    return resultados

# Estimar para jovens vs. experientes
grupos_idade = {1: 'Jovens (≤30)', 0: 'Experientes (>30)'}
resultados_idade = event_study_por_grupo(pnad, 'jovem', grupos_idade)

# Plotar comparação
def plot_event_study_comparativo(resultados, titulo=None):
    """
    Plota event studies de múltiplos grupos no mesmo gráfico.
    """
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    cores = {'Jovens (≤30)': '#e74c3c', 'Experientes (>30)': '#3498db'}
    marcadores = {'Jovens (≤30)': 's', 'Experientes (>30)': 'o'}
    
    for nome, coefs in resultados.items():
        cor = cores.get(nome, 'gray')
        marker = marcadores.get(nome, 'o')
        
        x = range(len(coefs))
        
        ax.errorbar(x, coefs['coef'], yerr=1.96*coefs['se'],
                    fmt=f'{marker}-', capsize=3, capthick=1.5,
                    label=nome, color=cor, linewidth=2, markersize=8,
                    alpha=0.8)
    
    # Linha zero e vertical
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    # Encontrar índice do ChatGPT
    periodos = list(list(resultados.values())[0]['periodo'])
    idx_chatgpt = periodos.index('2022T4') if '2022T4' in periodos else 7
    ax.axvline(x=idx_chatgpt + 0.5, color='gray', linestyle='--', linewidth=2)
    
    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels(periodos, rotation=45, ha='right')
    ax.set_xlabel('Período', fontsize=12)
    ax.set_ylabel('Coeficiente DiD', fontsize=12)
    ax.set_title(titulo or 'Event Study Comparativo por Faixa Etária', fontsize=14)
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('event_study_por_idade.png', dpi=200, bbox_inches='tight')
    plt.show()
    
    return fig

plot_event_study_comparativo(resultados_idade)
```

---

# 5. Especificação Econométrica

## 5.1 Modelo Principal (DiD Médio)

### Equação

$$Y_{iot} = \alpha + \beta \cdot (Post_t \times AltaExp_o) + \theta X_{it} + \delta_o + \mu_t + \varepsilon_{iot}$$

### Tabela de Variáveis

| Símbolo | Nome | Tipo | Descrição |
|---------|------|------|-----------|
| $Y_{iot}$ | Outcome | Dependente | Ocupado (0/1), horas, ln(renda) |
| $Post_t$ | Pós-tratamento | Dummy | 1 se $t \geq 2023T1$ |
| $AltaExp_o$ | Alta exposição | Dummy | 1 se ocupação no top 20% de exposição |
| $Post \times AltaExp$ | **Interação DiD** | Dummy | **Coeficiente de interesse ($\beta$)** |
| $X_{it}$ | Controles | Vetor | Idade, idade², mulher, negro_pardo, superior |
| $\delta_o$ | EF Ocupação | Fixo | Absorve diferenças permanentes entre ocupações |
| $\mu_t$ | EF Período | Fixo | Absorve choques comuns a todos |
| $\varepsilon_{iot}$ | Erro | Resíduo | Clusterizado por ocupação |

### Interpretação de $\beta$

> "$\beta$ representa a mudança diferencial na probabilidade de estar ocupado para trabalhadores em ocupações de alta exposição (comparados aos de baixa exposição), após o lançamento do ChatGPT (comparado ao período anterior)."

**Exemplo:** Se $\beta = -0.03$, então:
- "Trabalhadores em ocupações de alta exposição tiveram probabilidade de ocupação 3 pontos percentuais menor após o ChatGPT, relativo à diferença pré-existente com ocupações de baixa exposição."

## 5.2 Modelo de Event Study

### Equação

$$Y_{iot} = \alpha + \sum_{j \neq ref} \beta_j \cdot (1\{t=j\} \times AltaExp_o) + \theta X_{it} + \delta_o + \mu_t + \varepsilon_{iot}$$

### Interpretação

- Estimamos um $\beta_j$ para **cada período** (exceto o de referência, 2022T4)
- $\beta_j$ para $j < 2023T1$: Devem ser ≈ 0 (tendências paralelas)
- $\beta_j$ para $j \geq 2023T1$: Efeito causal período a período

## 5.3 Modelo de Heterogeneidade (Triple-DiD)

### Equação (por idade)

$$Y_{iot} = \alpha + \beta_1 (Post \times AltaExp) + \beta_2 (Post \times Jovem) + \beta_3 (AltaExp \times Jovem)$$
$$+ \beta_4 (Post \times AltaExp \times Jovem) + \theta X_{it} + \delta_o + \mu_t + \varepsilon_{iot}$$

### Interpretação

| Coeficiente | Pergunta que Responde |
|-------------|----------------------|
| $\beta_1$ | Efeito para não-jovens em ocupações expostas |
| $\beta_4$ | Efeito **adicional** para jovens em ocupações expostas |
| $\beta_1 + \beta_4$ | Efeito **total** para jovens em ocupações expostas |

**Se $\beta_4 < 0$:** Jovens são mais afetados que experientes

---

# 6. Implementação em Código

## 6.1 Script Completo

```python
"""
SCRIPT COMPLETO: DiD Ocupacional para Análise do Impacto da IA no Brasil
=========================================================================

Autor: [Seu nome]
Data: [Data]
Versão: 1.0

Descrição:
Este script implementa a estratégia de Difference-in-Differences para
estimar o efeito causal da IA Generativa sobre o mercado de trabalho
brasileiro, usando variação na intensidade de exposição ocupacional.

Requisitos:
- Python 3.8+
- pandas, numpy, matplotlib, seaborn
- pyfixest (para regressões com FE)
- basedosdados (opcional, para download)

Uso:
    python did_ocupacional.py
"""

# ============================================
# 1. CONFIGURAÇÃO
# ============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pyfixest as pf
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Configurações
SEED = 42
np.random.seed(SEED)

# Diretórios
DIR_DADOS = Path('./dados')
DIR_RESULTADOS = Path('./resultados')
DIR_FIGURAS = Path('./figuras')

for d in [DIR_DADOS, DIR_RESULTADOS, DIR_FIGURAS]:
    d.mkdir(exist_ok=True)

# Parâmetros
PERIODO_REF = '2022T4'  # Último período pré-tratamento
PERCENTIL_TRATAMENTO = 80  # Top 20% = alta exposição

print("="*70)
print("DiD OCUPACIONAL - IMPACTO DA IA NO MERCADO DE TRABALHO BRASILEIRO")
print("="*70)

# ============================================
# 2. CARREGAR DADOS
# ============================================

# [Inserir código de carregamento aqui - ver seções anteriores]

# ============================================
# 3. PREPARAÇÃO
# ============================================

# [Inserir código de preparação aqui - ver seções anteriores]

# ============================================
# 4. ANÁLISE DESCRITIVA
# ============================================

# [Inserir código de análise descritiva aqui]

# ============================================
# 5. ESTIMAÇÃO
# ============================================

# [Inserir código de estimação aqui]

# ============================================
# 6. EXPORTAR RESULTADOS
# ============================================

# Salvar tabelas
tabela_bal.to_csv(DIR_RESULTADOS / 'tabela_balanco.csv', index=False)
coefs_es.to_csv(DIR_RESULTADOS / 'event_study_coefs.csv', index=False)

# Salvar coeficientes principais
resultados_principais = pd.DataFrame({
    'Modelo': ['Básico', 'Com FE', 'Completo', 'Contínuo'],
    'Coeficiente': [modelo1.coef()['post:alta_exp'], 
                    modelo2.coef()['post:alta_exp'],
                    modelo3.coef()['post:alta_exp'],
                    modelo4.coef()['post:exposure_score']],
    'Erro Padrão': [modelo1.se()['post:alta_exp'],
                    modelo2.se()['post:alta_exp'],
                    modelo3.se()['post:alta_exp'],
                    modelo4.se()['post:exposure_score']],
    'p-valor': [modelo1.pvalue()['post:alta_exp'],
                modelo2.pvalue()['post:alta_exp'],
                modelo3.pvalue()['post:alta_exp'],
                modelo4.pvalue()['post:exposure_score']]
})
resultados_principais.to_csv(DIR_RESULTADOS / 'resultados_principais.csv', index=False)

print("\n" + "="*70)
print("ANÁLISE CONCLUÍDA")
print("="*70)
print(f"Resultados salvos em: {DIR_RESULTADOS}")
print(f"Figuras salvas em: {DIR_FIGURAS}")
```

---

# 7. Análise de Resultados

## 7.1 Tabelas para a Dissertação

### Tabela 1: Estatísticas Descritivas

```
┌────────────────────────────────────────────────────────────────────────┐
│           TABELA 1: Estatísticas Descritivas por Grupo de Exposição   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ Painel A: Características dos Trabalhadores (Período Pré-Tratamento)  │
│                                                                        │
│                          Baixa Exposição   Alta Exposição  Diferença  │
│                          ────────────────  ──────────────  ─────────  │
│ Idade (anos)                   XX.X            XX.X          X.X      │
│ Mulher (%)                     XX.X            XX.X          X.X      │
│ Negro/Pardo (%)                XX.X            XX.X          X.X      │
│ Superior completo (%)          XX.X            XX.X          X.X      │
│ Rendimento médio (R$)        X,XXX           X,XXX          XXX      │
│ Horas trabalhadas              XX.X            XX.X          X.X      │
│ Formal (%)                     XX.X            XX.X          X.X      │
│                                                                        │
│ Observações (milhões)          XX.X            XX.X                    │
│                                                                        │
│ Painel B: Exposição à IA                                              │
│                                                                        │
│ Exposure score (média)        0.XXX           0.XXX                   │
│ Exposure score (mediana)      0.XXX           0.XXX                   │
│ N ocupações                     XXX             XXX                    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Tabela 2: Resultados DiD Principais

```
┌────────────────────────────────────────────────────────────────────────┐
│                 TABELA 2: Efeitos DiD sobre Emprego                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ Variável Dependente: Probabilidade de Estar Ocupado                   │
│                                                                        │
│                              (1)        (2)        (3)        (4)     │
│                           ───────    ───────    ───────    ───────    │
│ Post × AltaExposição       X.XXX      X.XXX      X.XXX        -       │
│                           (X.XXX)    (X.XXX)    (X.XXX)               │
│                                                                        │
│ Post × Exposição (cont.)     -          -          -        X.XXX     │
│                                                             (X.XXX)   │
│                                                                        │
│ Controles individuais        Não        Não        Sim        Sim     │
│ EF Ocupação                  Não        Sim        Sim        Sim     │
│ EF Período                   Não        Sim        Sim        Sim     │
│                                                                        │
│ Observações               X,XXX,XXX  X,XXX,XXX  X,XXX,XXX  X,XXX,XXX  │
│ R²                          0.XXX      0.XXX      0.XXX      0.XXX    │
│ N clusters (ocupações)        -         XXX        XXX        XXX     │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ Notas: Erros padrão clusterizados por ocupação em parênteses.         │
│ * p<0.10, ** p<0.05, *** p<0.01                                       │
│ Alta exposição = ocupações no percentil 80+ do índice ILO.            │
└────────────────────────────────────────────────────────────────────────┘
```

### Tabela 3: Heterogeneidade por Idade

```
┌────────────────────────────────────────────────────────────────────────┐
│              TABELA 3: Heterogeneidade por Faixa Etária               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ Variável Dependente: Probabilidade de Estar Ocupado                   │
│                                                                        │
│                                         (1)            (2)            │
│                                      ─────────      ─────────         │
│ Post × AltaExp                         X.XXX            -             │
│                                       (X.XXX)                         │
│                                                                        │
│ Post × AltaExp × Jovem                   -           X.XXX            │
│                                                     (X.XXX)           │
│                                                                        │
│ Post × AltaExp (base: >30 anos)          -           X.XXX            │
│                                                     (X.XXX)           │
│                                                                        │
│ Efeito total para jovens (≤30)           -           X.XXX            │
│                                                     [X.XXX]           │
│                                                                        │
│ Controles                               Sim            Sim            │
│ EF Ocupação + Período                   Sim            Sim            │
│                                                                        │
│ p-valor (H0: efeito igual)               -           X.XXX            │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ Notas: Jovem = idade ≤ 30 anos. Erros padrão em parênteses.          │
│ Efeito total = soma dos coeficientes [erro padrão do efeito total].  │
└────────────────────────────────────────────────────────────────────────┘
```

## 7.2 Interpretação dos Resultados

### Cenário A: Efeito Negativo Significativo

**Se $\beta < 0$ e p < 0.05:**

> "Os resultados indicam que trabalhadores em ocupações de alta exposição à IA Generativa experimentaram uma redução estatisticamente significativa de X pontos percentuais na probabilidade de estar ocupado após o lançamento do ChatGPT, comparados a trabalhadores em ocupações de baixa exposição. Este resultado é consistente com a hipótese de que a IA está começando a afetar o emprego em ocupações cognitivas no Brasil, de forma semelhante aos achados de Brynjolfsson et al. (2025) para os Estados Unidos."

### Cenário B: Sem Efeito Significativo

**Se $\beta \approx 0$ ou p > 0.10:**

> "Não encontramos evidência estatisticamente significativa de efeitos diferenciais sobre emprego entre ocupações mais e menos expostas à IA Generativa no período analisado. Este resultado pode indicar que: (i) os efeitos da IA ainda não se materializaram de forma detectável no Brasil; (ii) o ajuste está ocorrendo por outras margens não captadas (como informalidade ou horas); (iii) há erro de medida atenuando os coeficientes; ou (iv) a economia brasileira responde de forma diferente à tecnologia devido a características estruturais específicas."

### Cenário C: Tendências Paralelas Violadas

**Se coeficientes pré-tratamento ≠ 0:**

> "Os coeficientes do event study para períodos anteriores ao tratamento são estatisticamente diferentes de zero, sugerindo que ocupações de alta e baixa exposição já apresentavam tendências divergentes antes do lançamento do ChatGPT. Esta violação da hipótese de tendências paralelas compromete a interpretação causal dos resultados, e os coeficientes pós-tratamento devem ser interpretados com cautela."

---

# 8. Testes de Robustez

## 8.1 Cortes Alternativos de Tratamento

```python
def robustez_cortes(df, outcome='ocupado'):
    """
    Testa sensibilidade a diferentes definições de tratamento.
    """
    
    cortes = {
        'Top 10%': 'alta_exp_10',
        'Top 20%': 'alta_exp',
        'Top 25%': 'alta_exp_25',
        'Contínuo': 'exposure_score'
    }
    
    resultados = []
    
    for nome, var in cortes.items():
        if var == 'exposure_score':
            formula = f"{outcome} ~ post:{var} + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo"
            var_coef = f'post:{var}'
        else:
            df['did_temp'] = df['post'] * df[var]
            formula = f"{outcome} ~ did_temp + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo"
            var_coef = 'did_temp'
        
        modelo = pf.feols(formula, data=df[df[outcome].notna()], 
                          weights="peso", vcov={"CRV1": "cod_ocupacao"})
        
        resultados.append({
            'Definição': nome,
            'Coeficiente': modelo.coef()[var_coef],
            'Erro Padrão': modelo.se()[var_coef],
            'p-valor': modelo.pvalue()[var_coef],
            'IC 95% Inferior': modelo.coef()[var_coef] - 1.96*modelo.se()[var_coef],
            'IC 95% Superior': modelo.coef()[var_coef] + 1.96*modelo.se()[var_coef]
        })
    
    return pd.DataFrame(resultados)

# Executar
robustez = robustez_cortes(pnad)
print("\nTABELA DE ROBUSTEZ: Cortes Alternativos")
print(robustez.to_string(index=False))
```

## 8.2 Placebo Temporal

```python
def teste_placebo(df, outcome='ocupado', periodo_placebo='2021T4'):
    """
    Testa se havia "efeito" antes do tratamento real (placebo).
    
    Se encontrar efeito no período placebo, sugere que há tendências
    pré-existentes diferentes.
    """
    
    # Usar apenas dados pré-ChatGPT
    df_pre = df[df['periodo_num'] < 20231].copy()
    
    # Criar "post" placebo
    periodo_num_placebo = int(periodo_placebo.replace('T', ''))
    df_pre['post_placebo'] = (df_pre['periodo_num'] >= periodo_num_placebo).astype(int)
    df_pre['did_placebo'] = df_pre['post_placebo'] * df_pre['alta_exp']
    
    # Estimar
    modelo = pf.feols(
        f"{outcome} ~ did_placebo + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo",
        data=df_pre[df_pre[outcome].notna()],
        weights="peso",
        vcov={"CRV1": "cod_ocupacao"}
    )
    
    print(f"\nTESTE PLACEBO (tratamento fictício em {periodo_placebo})")
    print("="*50)
    print(f"Coeficiente: {modelo.coef()['did_placebo']:.4f}")
    print(f"Erro padrão: {modelo.se()['did_placebo']:.4f}")
    print(f"p-valor: {modelo.pvalue()['did_placebo']:.4f}")
    print("="*50)
    print("Esperado: coeficiente ≈ 0 e não significativo")
    
    return modelo

# Executar
modelo_placebo = teste_placebo(pnad)
```

## 8.3 Exclusão de Ocupações de TI

```python
def robustez_sem_ti(df, outcome='ocupado'):
    """
    Verifica se resultados são robustos à exclusão de ocupações de TI.
    
    Motivação: Ocupações de TI podem ter tendências específicas
    (boom pós-pandemia, depois correção) não relacionadas à IA.
    """
    
    # Códigos ISCO de ocupações de TI (grupo 25)
    codigos_ti = [cod for cod in df['cod_ocupacao'].unique() 
                  if cod.startswith('25')]
    
    print(f"Excluindo {len(codigos_ti)} ocupações de TI")
    
    # Filtrar
    df_sem_ti = df[~df['cod_ocupacao'].isin(codigos_ti)].copy()
    
    # Estimar
    modelo = pf.feols(
        f"{outcome} ~ post:alta_exp + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo",
        data=df_sem_ti[df_sem_ti[outcome].notna()],
        weights="peso",
        vcov={"CRV1": "cod_ocupacao"}
    )
    
    print("\nRESULTADO SEM OCUPAÇÕES DE TI")
    print(modelo.summary())
    
    return modelo

# Executar
modelo_sem_ti = robustez_sem_ti(pnad)
```

## 8.4 Diferentes Outcomes

```python
def robustez_outcomes(df):
    """
    Testa o efeito sobre diferentes outcomes.
    """
    
    outcomes = {
        'ocupado': 'Probabilidade de ocupação',
        'horas_trabalhadas': 'Horas trabalhadas',
        'ln_renda': 'Log do rendimento',
        'formal': 'Probabilidade de emprego formal',
        'informal': 'Probabilidade de informalidade'
    }
    
    resultados = []
    
    for var, nome in outcomes.items():
        if var not in df.columns:
            continue
            
        try:
            modelo = pf.feols(
                f"{var} ~ post:alta_exp + idade + I(idade**2) + mulher + negro_pardo + superior | cod_ocupacao + periodo",
                data=df[df[var].notna()],
                weights="peso",
                vcov={"CRV1": "cod_ocupacao"}
            )
            
            resultados.append({
                'Outcome': nome,
                'Coeficiente': modelo.coef()['post:alta_exp'],
                'Erro Padrão': modelo.se()['post:alta_exp'],
                'p-valor': modelo.pvalue()['post:alta_exp'],
                'N': len(df[df[var].notna()])
            })
        except Exception as e:
            print(f"Erro em {var}: {e}")
    
    return pd.DataFrame(resultados)

# Executar
robustez_out = robustez_outcomes(pnad)
print("\nROBUSTEZ: Diferentes Outcomes")
print(robustez_out.to_string(index=False))
```

---

# 9. Limitações e Caveats

## 9.1 Limitações da Estratégia de Identificação

| Limitação | Descrição | Mitigação |
|-----------|-----------|-----------|
| **Tendências paralelas** | Não é possível testar definitivamente; apenas verificar no período pré | Event study, placebos |
| **Choques correlacionados** | Outros eventos (juros, pandemia) podem confundir | Controles, exclusão de TI |
| **SUTVA** | Spillovers entre ocupações não são captados | Reconhecer na interpretação |
| **Erro de medida** | Classificação ocupacional imprecisa na PNAD | Agregação, robustez |

## 9.2 Limitações dos Dados

| Limitação | Descrição | Implicação |
|-----------|-----------|------------|
| **Frequência** | Apenas trimestral (não mensal como ADP) | Menos precisão temporal |
| **Amostra** | ~300k ocupados/trimestre (vs. 25M no ADP) | Menos poder para subgrupos |
| **Survey** | Auto-declaração (não administrativo) | Mais erro de medida |
| **Sem painel individual** | Não acompanhamos mesma pessoa | Não podemos ver transições |

## 9.3 Limitações de Interpretação

- **Exposição ≠ Adoção:** Alto índice de exposição não significa que empresas brasileiras adotaram IA
- **Efeito local:** Resultados são para o Brasil e podem não generalizar
- **Timing:** Efeitos podem ser defasados e não captados ainda

---

# 10. Checklist Final

## Antes de Começar
- [ ] Python 3.8+ instalado
- [ ] Pacotes: pandas, numpy, matplotlib, seaborn, pyfixest
- [ ] Acesso ao BigQuery (ou arquivos PNAD locais)
- [ ] Índice ILO disponível

## Fase 1: Dados
- [ ] Baixar PNAD 2021T1 a 2024T4
- [ ] Baixar/carregar índice ILO
- [ ] Verificar estrutura dos dados

## Fase 2: Preparação
- [ ] Limpar PNAD (filtros, tipos)
- [ ] Criar variáveis temporais (periodo, post)
- [ ] Criar variáveis de outcome (ocupado, formal, ln_renda)
- [ ] Criar variáveis demográficas (mulher, negro_pardo, jovem)
- [ ] Merge com índice ILO
- [ ] Criar variáveis de tratamento (alta_exp, did)
- [ ] Verificar cobertura do merge (>95%)

## Fase 3: Descritiva
- [ ] Tabela de balanço
- [ ] Gráfico de tendências paralelas
- [ ] Estatísticas por quintil de exposição

## Fase 4: Estimação
- [ ] DiD médio (3+ especificações)
- [ ] Event study
- [ ] Gráfico do event study
- [ ] Heterogeneidade por idade
- [ ] Event study por subgrupo

## Fase 5: Robustez
- [ ] Cortes alternativos (10%, 25%, contínuo)
- [ ] Placebo temporal
- [ ] Exclusão de TI
- [ ] Diferentes outcomes

## Fase 6: Documentação
- [ ] Salvar tabelas em CSV
- [ ] Salvar figuras em PNG (alta resolução)
- [ ] Documentar código
- [ ] Escrever seção de resultados

---

# Referências

## Metodológicas
- Angrist, J. D., & Pischke, J. S. (2009). *Mostly Harmless Econometrics*. Princeton University Press.
- Cunningham, S. (2021). *Causal Inference: The Mixtape*. Yale University Press.
- Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. *Journal of Econometrics*, 225(2), 254-277.

## Substantivas
- Brynjolfsson, E., Chandar, B., & Chen, R. (2025). Canaries in the Coal Mine? Six Facts about the Recent Employment Effects of Artificial Intelligence. *Stanford Digital Economy Lab*.
- Gmyrek, P., Berg, J., et al. (2025). Generative AI and Jobs: A Refined Global Index of Occupational Exposure. *ILO Working Paper*.
- Eloundou, T., Manning, S., et al. (2023). GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models. *OpenAI*.

## Dados
- IBGE. Pesquisa Nacional por Amostra de Domicílios Contínua - PNAD Contínua. Disponível em: https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html
- Base dos Dados. Disponível em: https://basedosdados.org/

---

*Documento gerado em Fevereiro de 2026*
*Versão 1.0*
