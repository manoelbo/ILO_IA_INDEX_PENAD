# PLANO — Etapa 3: Triple-DiD com Heterogeneidade Espacial

**Dissertação:** Impacto da IA Generativa sobre o Emprego Formal no Brasil
**Aluno:** Mané — Mestrado em Economia, FGV
**Data:** Fevereiro 2026

---

## Motivação

A Etapa 2 estimou o efeito médio nacional da IA generativa sobre o emprego formal, usando variação cross-sectional na exposição ocupacional (ILO AI Exposure Index). O resultado principal mostra que ocupações de alta exposição à IA sofreram queda de salário real de admissão (~3-4%) após o lançamento do ChatGPT (Nov/2022), com evidência de deskilling (aumento de idade média e % com ensino superior nas admissões).

Porém, o efeito médio nacional mascara heterogeneidade espacial importante. O Brasil é um dos países mais desiguais do mundo em termos de infraestrutura digital. A penetração de banda larga fixa varia de >90 acessos/100 domicílios em municípios como São Paulo e Florianópolis a <5 acessos/100 domicílios em municípios rurais do Norte e Nordeste. Essa desigualdade digital implica que a exposição **efetiva** à IA generativa é mediada pela infraestrutura de conectividade local — mesmo ocupações teoricamente expostas (advogados, contadores, analistas) só adotam ferramentas de IA onde há internet de qualidade.

A Etapa 3 explora essa heterogeneidade espacial via **Triple Difference-in-Differences (DDD)**, adicionando a dimensão municipal de conectividade ao design da Etapa 2. A hipótese central é que o efeito da IA generativa sobre o emprego formal é **amplificado** em municípios com alta conectividade, onde a adoção efetiva de ferramentas como ChatGPT, Copilot e similares é viável.

**Conexão com a literatura:**
- Autor & Dorn (2013): automação afeta mercados de trabalho locais de forma heterogênea
- Hjort & Poulsen (2019): internet de alta velocidade afeta emprego em países africanos
- Goldfarb & Tucker (2019): custos de adoção de tecnologia digital variam com infraestrutura
- Brynjolfsson et al. (2025): canários na mina — efeitos precoces de IA em ocupações expostas

---

## Fonte de Dados: Anatel — Banda Larga Fixa

### O que é

A Anatel (Agência Nacional de Telecomunicações) publica dados de acessos de banda larga fixa (SCM — Serviço de Comunicação Multimídia) por município, com frequência mensal. O dataset `br_anatel_banda_larga_fixa` contém o número de acessos, tecnologia (fibra, DSL, cabo, rádio), velocidade contratada, e operadora, desagregado por município (código IBGE de 7 dígitos).

### Onde baixar

Existem três caminhos para acessar os dados:

**Opção 1 — Base dos Dados (RECOMENDADA)**
- URL: https://basedosdados.org/dataset/br-anatel-banda-larga-fixa
- Pacote Python: `pip install basedosdados`
- Acesso via BigQuery (1 TB grátis/mês por usuário Google Cloud)
- Vantagem: dados já tratados, padronizados, com código IBGE normalizado
- Permite query SQL direta, filtrando período e variáveis desejadas

```python
import basedosdados as bd

# Exemplo de query
query = """
SELECT
    ano, mes, id_municipio,
    SUM(acessos) as total_acessos
FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
WHERE ano BETWEEN 2021 AND 2022
GROUP BY ano, mes, id_municipio
"""
df_anatel = bd.read_sql(query, billing_project_id="seu-projeto-gcp")
```

**Opção 2 — Portal de Dados Abertos (dados.gov.br)**
- URL: https://dados.gov.br/dados/conjuntos-dados/acessos---banda-larga-fixa
- Download direto de CSVs
- Requer mais limpeza manual
- Também disponível: densidade por 100 habitantes

**Opção 3 — Anatel Open Data Portal**
- URL: https://www.gov.br/anatel/pt-br/dados/dados-abertos
- Inclui painéis interativos e dados brutos
- Dataset "Meu Município" com dados consolidados de telecomunicações

### Variáveis relevantes

| Variável | Descrição | Uso no estudo |
|----------|-----------|---------------|
| `id_municipio` | Código IBGE 7 dígitos | Chave de merge com CAGED |
| `ano`, `mes` | Período | Alinhamento temporal |
| `acessos` | Número de acessos de banda larga fixa | Numerador da penetração |
| `velocidade` | Faixa de velocidade contratada | Proxy de qualidade |
| `tecnologia` | Fibra, DSL, cabo, rádio, satélite | Proxy de qualidade |

### Variável de conectividade a construir

A variável principal será a **penetração de banda larga fixa** = (total de acessos no município) / (número de domicílios no município, do Censo IBGE). Variantes para robustez:

1. `penetracao_bl`: acessos / domicílios (variável principal)
2. `pct_fibra`: % de acessos via fibra óptica (proxy de qualidade)
3. `velocidade_media`: velocidade média ponderada contratada
4. `ibc`: Índice Brasileiro de Conectividade (índice composto da Anatel, disponível em basedosdados.org)

**IMPORTANTE:** Usar dados de conectividade do período **pré-tratamento** (média de Jan-Out/2022 ou ano de 2021) para evitar endogeneidade. A expansão de banda larga pós-2022 pode ser correlacionada com adoção de IA — conectividade pré-tratamento é predeterminada.

### Dados complementares necessários

- **Domicílios por município (IBGE):** Para calcular penetração. Fonte: Censo 2022 ou estimativas populacionais IBGE. Também disponível no `basedosdados` (`br_ibge_censo2022` ou `br_ibge_populacao`).
- **PIB per capita municipal (IBGE):** Controle importante para evitar que conectividade seja apenas proxy de riqueza.
- **Porte do município:** População, para filtrar municípios com volume mínimo de emprego no CAGED.

---

## Notebook 3a — Preparação do Painel CAGED × Município × Conectividade Anatel

### Estrutura (seguindo o padrão da Etapa 2a)

```
0.1  Contextualização
0.2  Objetivo
0.3  Ficha Técnica dos Dados
0.4  Referências principais
0.5  1. Configuração do ambiente
0.6  2. Dados Anatel — Banda Larga Fixa
0.7  3. Dados IBGE — Domicílios e PIB municipal
0.8  4. Construção do Índice de Conectividade Municipal
0.9  5. Dados CAGED — Agregação por Ocupação × Município × Período
0.10 6. Merge: Painel Tridimensional
0.11 7. Definição de Tratamento (Exposição IA × Conectividade)
0.12 8. Validação e Estatísticas Descritivas
0.13 9. Exportação do Painel Final
```

### Detalhamento de cada seção

#### 0.1 Contextualização

Texto narrativo explicando a motivação da Etapa 3: a heterogeneidade espacial da adoção de IA no Brasil, a desigualdade digital como moderador do efeito, e a contribuição original do estudo (nenhum trabalho anterior combinou exposição ocupacional à IA com infraestrutura digital municipal no Brasil).

#### 0.2 Objetivo

Construir um painel balanceado no nível **ocupação (CBO 4d) × município × mês** que combine:
- Variáveis de emprego formal do CAGED (admissões, desligamentos, saldo, salários)
- Exposição ocupacional à IA (ILO AI Exposure Index, já construído na Etapa 2a)
- Índice de conectividade municipal (Anatel + IBGE)

Saída: arquivo `painel_caged_municipio_anatel.parquet` pronto para estimação na Etapa 3b.

#### 0.3 Ficha Técnica dos Dados

| Campo | CAGED | Anatel BLF | IBGE |
|-------|-------|------------|------|
| Fonte | MTE / CAGED | Anatel / SCM | IBGE / Censo |
| Dataset | Movimentações | Acessos BLF | Domicílios / PIB |
| Período | Jan/2021 – Jun/2025 | 2021 – 2022 (pré-trat.) | 2022 |
| Unidade | Movimentação trabalhista | Acesso de banda larga | Município |
| Cobertura | Brasil (emprego formal) | Brasil (5.570 municípios) | Brasil |
| Granularidade | Indivíduo → agregar | Município × mês | Município |
| Classificação | CBO 2002 (4 dígitos) | — | Código IBGE |

#### 0.4 Referências principais

- Autor, D. & Dorn, D. (2013). The Growth of Low-Skill Service Jobs. AER.
- Hjort, J. & Poulsen, J. (2019). The Arrival of Fast Internet and Employment in Africa. AER.
- Goldfarb, A. & Tucker, C. (2019). Digital Economics. JEL.
- Webb, M. (2020). The Impact of AI on the Labor Market. Stanford WP.
- Felten, E., Raj, M. & Seamans, R. (2021). Occupational, industry, and geographic exposure to AI. SSRN.

#### 0.5 1. Configuração do ambiente

```python
# Etapa 3a.1 — Configuração do ambiente
# Mesma estrutura da Etapa 2a: imports, paths, parâmetros

import pandas as pd
import numpy as np
import basedosdados as bd  # para dados Anatel e IBGE
from pathlib import Path

# Parâmetros
EVENTO = '2022-11'           # Lançamento ChatGPT
PERIODO_INICIO = '2021-01'
PERIODO_FIM = '2025-06'
GCP_PROJECT = 'seu-projeto'  # Para BigQuery/basedosdados

# Paths (mesma estrutura da Etapa 2)
BASE_DIR = Path('.')
OUTPUTS = BASE_DIR / 'outputs'
OUTPUTS_TABLES = OUTPUTS / 'tables'
OUTPUTS_FIGURES = OUTPUTS / 'figures'
DATA_DIR = BASE_DIR / 'data'

# Reaproveitar dados da Etapa 2a
PAINEL_ETAPA2 = DATA_DIR / 'painel_caged_ilo.parquet'  # painel ocupação×mês da Etapa 2a

# Parâmetros de filtragem
MIN_POPULACAO = 50_000      # municípios com pelo menos 50k habitantes
MIN_MOVIMENTACOES = 100     # mínimo de movimentações no CAGED no período pré
```

**Nota sobre filtragem de municípios:** O CAGED mensal por ocupação×município terá muitas células com zero ou poucas movimentações. Municípios pequenos (<50 mil hab.) terão poucas observações por ocupação, gerando ruído extremo. Recomenda-se filtrar por porte mínimo. Como robustez, testar com threshold de 100 mil e 20 mil.

#### 0.6 2. Dados Anatel — Banda Larga Fixa

```python
# Etapa 3a.2 — Download e processamento dos dados Anatel

# Opção A: via basedosdados (recomendada)
query_anatel = """
SELECT
    ano,
    mes,
    id_municipio,
    SUM(acessos) as total_acessos,
    SUM(CASE WHEN tecnologia = 'Fibra Óptica' THEN acessos ELSE 0 END) as acessos_fibra
FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
WHERE ano IN (2021, 2022)
  AND mes <= CASE WHEN ano = 2022 THEN 10 ELSE 12 END  -- Pré-tratamento
GROUP BY ano, mes, id_municipio
"""
df_anatel_raw = bd.read_sql(query_anatel, billing_project_id=GCP_PROJECT)

# Opção B: via CSV direto (fallback)
# df_anatel_raw = pd.read_csv('data/anatel_banda_larga_fixa.csv', sep=';')
```

Processamento:
1. Agregar por município: média mensal de acessos no período pré-tratamento
2. Calcular % fibra óptica sobre total de acessos
3. Resultado: DataFrame `df_anatel` com uma linha por município, colunas: `id_municipio`, `media_acessos_pre`, `pct_fibra_pre`

#### 0.7 3. Dados IBGE — Domicílios e PIB municipal

```python
# Etapa 3a.3 — Dados IBGE (domicílios e PIB)

# Domicílios (Censo 2022 ou estimativa)
query_domicilios = """
SELECT
    id_municipio,
    domicilios_particulares_permanentes_ocupados as domicilios
FROM `basedosdados.br_ibge_censo_2022.domicilio_municipio`
"""

# PIB municipal (último disponível)
query_pib = """
SELECT
    id_municipio,
    pib / populacao as pib_per_capita
FROM `basedosdados.br_ibge_pib.municipio`
WHERE ano = 2021
"""

# População
query_pop = """
SELECT
    id_municipio,
    populacao
FROM `basedosdados.br_ibge_populacao.municipio`
WHERE ano = 2022
"""
```

**Nota:** Verificar disponibilidade exata das tabelas no basedosdados. Os nomes de tabela acima são aproximados — rodar `bd.list_datasets()` e `bd.list_tables()` para confirmar. Como fallback, baixar do SIDRA/IBGE.

#### 0.8 4. Construção do Índice de Conectividade Municipal

```python
# Etapa 3a.4 — Índice de Conectividade Municipal

# Merge Anatel + IBGE
df_conectividade = df_anatel.merge(df_ibge, on='id_municipio', how='inner')

# Variável principal: penetração de banda larga
df_conectividade['penetracao_bl'] = (
    df_conectividade['media_acessos_pre'] / df_conectividade['domicilios']
)

# Variável secundária: % fibra
df_conectividade['pct_fibra'] = df_conectividade['pct_fibra_pre']

# Definição de grupos (pré-tratamento, fixo no tempo)
mediana_penetracao = df_conectividade['penetracao_bl'].median()
df_conectividade['alta_conectividade'] = (
    df_conectividade['penetracao_bl'] > mediana_penetracao
).astype(int)

# Variantes para robustez
q25 = df_conectividade['penetracao_bl'].quantile(0.25)
q75 = df_conectividade['penetracao_bl'].quantile(0.75)
df_conectividade['conectividade_q75'] = (df_conectividade['penetracao_bl'] > q75).astype(int)
df_conectividade['conectividade_q25'] = (df_conectividade['penetracao_bl'] > q25).astype(int)

# Diagnóstico
print(f"Mediana penetração: {mediana_penetracao:.3f}")
print(f"Municípios alta conectividade: {df_conectividade['alta_conectividade'].sum()}")
print(f"Municípios baixa conectividade: {(~df_conectividade['alta_conectividade'].astype(bool)).sum()}")
```

**Decisão metodológica — cutoff:**
- Especificação principal: mediana da penetração (consistente com a Etapa 2, que usa mediana do exposure score)
- Robustez: top quartil vs. bottom quartil (exclui municípios intermediários, efeito mais limpo)
- Robustez: tratamento contínuo (penetração × HighExp × Post, sem cutoff)

#### 0.9 5. Dados CAGED — Agregação por Ocupação × Município × Período

Esta é a seção mais crítica. Na Etapa 2a, o CAGED foi agregado no nível **ocupação × período** (nacional). Agora, precisamos agregar no nível **ocupação × município × período**.

```python
# Etapa 3a.5 — CAGED municipal

# OPÇÃO A: Reagregar a partir dos microdados CAGED originais
# (preferível se os microdados estão acessíveis)
# O CAGED no basedosdados: br_me_caged.microdados_movimentacao

query_caged_mun = """
SELECT
    SUBSTR(cbo_2002, 1, 4) as cbo_4d,
    id_municipio,
    CONCAT(CAST(ano AS STRING), '-', LPAD(CAST(mes AS STRING), 2, '0')) as periodo,
    SUM(CASE WHEN tipo_movimentacao IN ('admissao') THEN 1 ELSE 0 END) as admissoes,
    SUM(CASE WHEN tipo_movimentacao IN ('desligamento') THEN 1 ELSE 0 END) as desligamentos,
    AVG(salario) as salario_medio,
    AVG(idade) as idade_media,
    AVG(CASE WHEN grau_instrucao >= 9 THEN 1.0 ELSE 0.0 END) as pct_superior,
    AVG(CASE WHEN sexo = 'Feminino' THEN 1.0 ELSE 0.0 END) as pct_mulher
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano BETWEEN 2021 AND 2025
GROUP BY cbo_4d, id_municipio, periodo
"""

# OPÇÃO B: Usar os microdados locais já baixados na Etapa 2
# e reagregar incluindo a dimensão município
# Isso depende de como os dados foram baixados originalmente
```

**Nota sobre dimensionalidade:**
- Etapa 2: ~629 ocupações × 54 meses = ~34 mil observações
- Etapa 3: ~629 ocupações × ~500 municípios (filtrados) × 54 meses = ~17 milhões de observações potenciais
- Muitas células estarão vazias (nem toda ocupação existe em todo município)
- Filtrar: manter apenas células ocupação×município com ≥ 5 movimentações no período pré para garantir variação estatística

**Reaproveitar da Etapa 2a:**
- O crosswalk CBO → ISCO → ILO AI Exposure Index (já validado)
- O deflator IPCA (já calculado)
- As definições de outcomes (log admissões, log salário real, etc.)

#### 0.10 6. Merge — Painel Tridimensional

```python
# Etapa 3a.6 — Construção do painel final

# 1. Merge CAGED municipal com exposure score (via CBO)
df_panel = df_caged_mun.merge(
    df_exposure[['cbo_4d', 'ilo_exposure_score', 'alta_exp']],
    on='cbo_4d',
    how='inner'
)

# 2. Merge com conectividade municipal
df_panel = df_panel.merge(
    df_conectividade[['id_municipio', 'penetracao_bl', 'alta_conectividade',
                       'conectividade_q75', 'pib_per_capita', 'populacao', 'uf']],
    on='id_municipio',
    how='inner'
)

# 3. Variáveis temporais (reaproveitar lógica da Etapa 2a)
df_panel['periodo_dt'] = pd.to_datetime(df_panel['periodo'] + '-01')
df_panel['post'] = (df_panel['periodo_dt'] >= '2022-11-01').astype(int)
df_panel['tempo_relativo_meses'] = (
    (df_panel['periodo_dt'].dt.year - 2022) * 12 +
    (df_panel['periodo_dt'].dt.month - 11)
)

# 4. Variáveis de interação para DDD
df_panel['post_alta_exp'] = df_panel['post'] * df_panel['alta_exp']
df_panel['post_alta_conect'] = df_panel['post'] * df_panel['alta_conectividade']
df_panel['alta_exp_alta_conect'] = df_panel['alta_exp'] * df_panel['alta_conectividade']
df_panel['triple_did'] = (
    df_panel['post'] * df_panel['alta_exp'] * df_panel['alta_conectividade']
)

# 5. Construir outcomes (mesma lógica da Etapa 2a)
df_panel['saldo'] = df_panel['admissoes'] - df_panel['desligamentos']
df_panel['ln_admissoes'] = np.log1p(df_panel['admissoes'])
df_panel['ln_desligamentos'] = np.log1p(df_panel['desligamentos'])
# ... deflacionar salários pelo IPCA (mesmo procedimento da Etapa 2a)
```

#### 0.11 7. Definição de Tratamento

Quadro resumo das dimensões de tratamento:

| Dimensão | Variável | Cutoff principal | Robustez |
|----------|----------|-----------------|----------|
| Exposição IA | `alta_exp` (ILO score) | Mediana | Top 10%, 25% |
| Temporal | `post` | Nov/2022 | Placebo Dez/2021 |
| Conectividade | `alta_conectividade` | Mediana penetração BL | Q75, contínuo |

O **grupo "tratado"** no Triple-DiD são as observações que satisfazem simultaneamente: ocupação de alta exposição à IA, período pós-ChatGPT, e município de alta conectividade. O coeficiente β₇ (interação tripla) captura o efeito diferencial.

#### 0.12 8. Validação e Estatísticas Descritivas

Seguindo o padrão da Etapa 2b:
1. **Tabela de balanço pré-tratamento** por grupo de conectividade (alta vs. baixa): comparar composição de admissões, salários, demografia
2. **Distribuição de penetração de BL** por UF e por porte de município (histograma e mapa)
3. **Correlação** entre penetração BL e PIB per capita (documentar que são correlacionados, mas não colineares)
4. **Tabela de cobertura do painel:** quantas ocupações × municípios × períodos, % de células preenchidas
5. **Mapa de calor:** penetração BL por município (usando geopandas, se desejável)

#### 0.13 9. Exportação

```python
# Etapa 3a.9 — Exportação
df_panel.to_parquet(DATA_DIR / 'painel_caged_municipio_anatel.parquet', index=False)
df_conectividade.to_csv(OUTPUTS_TABLES / 'conectividade_municipal.csv', index=False)
print(f"Painel final: {df_panel.shape[0]:,} observações, {df_panel.shape[1]} variáveis")
print(f"Ocupações: {df_panel['cbo_4d'].nunique()}")
print(f"Municípios: {df_panel['id_municipio'].nunique()}")
print(f"Períodos: {df_panel['periodo'].nunique()}")
```

---

## Notebook 3b — Estimação Triple-DiD: IA Generativa, Conectividade e Emprego Formal

### Estrutura (seguindo o padrão da Etapa 2b)

```
0.1  Estratégia de Identificação
0.2  Outcomes
0.3  1. Configuração do ambiente
0.4  2. Carregar e explorar dados
0.5  3. Tabela de balanço (por grupo de conectividade)
0.6  4. DiD por subgrupo de conectividade (motivação)
0.7  5. Triple-DiD — Modelo Principal
0.8  6. Event Study por grupo de conectividade
0.9  6b. Teste formal de tendências paralelas
0.10 7. Análise de heterogeneidade adicional
0.11 8. Testes de robustez
0.12 9. Mecanismos
0.13 10. Tabelas LaTeX e figuras finais
0.14 11. Síntese dos resultados
```

### Detalhamento de cada seção

#### 0.1 Estratégia de Identificação

| Elemento | Especificação |
|----------|---------------|
| **Unidade analítica** | Ocupação (CBO 4d) × Município × Mês |
| **Tratamento (Dim. 1)** | Alta exposição à IA (ILO score > mediana) |
| **Tratamento (Dim. 2)** | Alta conectividade (penetração BL > mediana) |
| **Controle** | Ocupações de baixa exposição e/ou municípios de baixa conectividade |
| **Evento** | Lançamento do ChatGPT (30/Nov/2022) |
| **Período pré** | Jan/2021 – Out/2022 (22 meses) |
| **Período pós** | Nov/2022 – Jun/2025 (32 meses) |
| **Efeitos fixos** | Ocupação, UF×Período (ou Município, Período) |
| **Clustering** | Município (ou multiway: ocupação + município) |
| **Coeficiente de interesse** | β₇ (HighExp × Post × HighConnect) |

**Interpretação de β₇:** Diferença no efeito da IA entre municípios de alta e baixa conectividade, para ocupações expostas vs. não-expostas, pós vs. pré-ChatGPT. Um β₇ < 0 para salários significaria que a IA reduz salários **mais** em municípios conectados — consistente com adoção efetiva mediada por infraestrutura.

#### 0.2 Outcomes

Reaproveitar os mesmos outcomes da Etapa 2b, focando nos que apresentaram resultados significativos:

**Outcomes prioritários (resultados significativos na Etapa 2):**
- `ln_salario_real_adm`: Log do salário real de admissão
- `ln_admissoes`: Log das admissões
- `pct_superior_adm`: % com ensino superior nas admissões
- `idade_media_adm`: Idade média das admissões

**Outcomes secundários:**
- `ln_desligamentos`: Log dos desligamentos (com cautela — tendências paralelas violadas na Etapa 2)
- `saldo`: Saldo líquido
- Subgrupos demográficos: `ln_salario_jovem`, `ln_salario_mulher`, etc.

#### 0.3–0.4 Configuração e Carga de Dados

Mesma estrutura da Etapa 2b. Carregar o painel exportado na Etapa 3a.

#### 0.5 Tabela de Balanço

Duas tabelas:
1. **Balanço por exposição IA** (como na Etapa 2b, mas agora no painel municipal)
2. **Balanço por conectividade** (nova): comparar municípios de alta vs. baixa conectividade em termos de salário médio, composição ocupacional, demografia das admissões

#### 0.6 DiD por Subgrupo de Conectividade (Motivação)

Antes do Triple-DiD, estimar o DiD simples (Etapa 2) **separadamente** para municípios de alta e baixa conectividade. Isso motiva o Triple-DiD visualmente e intuitivamente.

```python
# Etapa 3b.6 — DiD separado por grupo de conectividade

# Municípios de ALTA conectividade
df_high_c = df_panel[df_panel['alta_conectividade'] == 1]
# Estimar: outcome ~ post_alta_exp | cbo_4d + periodo, cluster = id_municipio

# Municípios de BAIXA conectividade
df_low_c = df_panel[df_panel['alta_conectividade'] == 0]
# Estimar: outcome ~ post_alta_exp | cbo_4d + periodo, cluster = id_municipio

# Comparar coeficientes: se o efeito é maior (mais negativo) em alta conectividade,
# isso justifica o Triple-DiD
```

**Expectativa:** O coeficiente DiD para salário real deve ser mais negativo nos municípios de alta conectividade (onde a IA é efetivamente adotada).

#### 0.7 Triple-DiD — Modelo Principal

```python
# Etapa 3b.7 — Triple-DiD

# Especificação completa
# Y_omt = β₁·HighExp + β₂·Post + β₃·HighConnect
#        + β₄·(HighExp×Post) + β₅·(HighExp×HighConnect) + β₆·(Post×HighConnect)
#        + β₇·(HighExp×Post×HighConnect)
#        + γ·Controls + FE_ocupacao + FE_uf×periodo + ε

# Com pyFixest:
import pyfixest as pf

# Modelo 1: Sem controles
formula_m1 = f"{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + periodo"

# Modelo 2: Com FE de UF×período (absorve choques estaduais)
formula_m2 = f"{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect | cbo_4d + uf_periodo"

# Modelo 3: Com FE + controles demográficos
formula_m3 = f"{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect + idade_media_adm + pct_mulher_adm + pct_superior_adm + ln_pib_pc | cbo_4d + uf_periodo"

# Clustering: município (captura correlação serial e entre ocupações dentro do município)
VCOV_SPEC = {'CRV1': 'id_municipio'}

# Reportar os 3 modelos lado a lado, como na Etapa 2b
```

**Nota sobre efeitos fixos:**
- `cbo_4d`: absorve diferenças fixas entre ocupações (nível de salário, tamanho)
- `uf_periodo` (UF × mês-ano): absorve qualquer choque estadual variante no tempo (política econômica, sazonalidade regional, ciclo local). Esta é a especificação mais conservadora e recomendada.
- Alternativa para robustez: `id_municipio + periodo` (FE de município + FE de período separados)
- Não incluir `id_municipio` e `uf_periodo` simultaneamente (município já implica UF)

#### 0.8 Event Study por Grupo de Conectividade

Estimar event studies **separados** para municípios de alta e baixa conectividade, plotando os coeficientes no mesmo gráfico. Isso permite visualizar:
- Se tendências paralelas se sustentam em ambos os subgrupos
- Se a divergência pós-tratamento é mais forte nos municípios conectados
- O timing do efeito em cada grupo

```python
# Etapa 3b.8 — Event study por grupo de conectividade

# Para cada grupo (alta/baixa conectividade):
#   Criar dummies did_t{t} = 1(tempo_relativo == t & alta_exp == 1)
#   Estimar: outcome ~ sum(did_t{t}) | cbo_4d + periodo
#   Binning: t <= -12 e t >= 24
#   Referência: t = -1

# Plotar ambas as séries de coeficientes no mesmo gráfico
# (azul = alta conectividade, vermelho = baixa conectividade)
```

#### 0.9 Teste Formal de Tendências Paralelas

Mesma metodologia da Etapa 2b: teste conjunto (Wald/F) de que todos os coeficientes pré-tratamento são zero, **separadamente** para cada subgrupo de conectividade e para o modelo Triple-DiD completo.

#### 0.10 Análise de Heterogeneidade Adicional

Extensões do Triple-DiD que exploram outras dimensões:

1. **Capitais vs. Interior:** Dummy de capital estadual em vez de penetração BL como proxy
2. **Porte do município:** Interação com faixas populacionais (100k+, 500k+, 1M+)
3. **Setor tecnológico:** Interação com a dummy de setor de TI (CBO 21xx) — expect: efeito ainda mais forte em TI + alta conectividade
4. **Automação vs. Augmentação × Conectividade:** Cruzar o Anthropic Economic Index (da Etapa 2b) com conectividade

#### 0.11 Testes de Robustez

Manter os 5 testes da Etapa 2b e adicionar robustez específica da Etapa 3:

| Teste | Descrição | Expectativa |
|-------|-----------|-------------|
| **R1. Cutoffs alternativos de exposição IA** | Top 10%, 25%, mediana | Mesma direção |
| **R2. Cutoffs alternativos de conectividade** | Q75, Q25, contínuo | Efeito mais forte com cutoff mais restritivo |
| **R3. Placebo temporal** | Evento fictício Dez/2021 | Não significativo |
| **R4. Exclusão de TI** | Remover CBO 21xx | Resultado estável |
| **R5. Apenas capitais** | Capital=1 em vez de penetração BL | Mesma direção, magnitude similar |
| **R6. FE de município** | `id_municipio + periodo` em vez de `cbo_4d + uf_periodo` | Resultado robusto |
| **R7. Clustering alternativo** | Multiway (ocupação + município) | SE maiores mas significância mantida |
| **R8. Tratamento contínuo** | `penetracao_bl × exposure_score × post` | Dose-resposta monotônica |
| **R9. Threshold de população** | Filtrar >100k, >20k | Resultado estável |
| **R10. PIB per capita como controle** | Incluir ln(PIB pc) | Resultado estável (conectividade ≠ riqueza) |
| **R11. Crosswalk 2d vs. 4d** | Como na Etapa 2b | Mesma direção |

#### 0.12 Mecanismos

1. **Deskilling espacial:** A composição de admissões (idade, escolaridade) muda mais em municípios conectados? Usar idade média e % superior como outcomes no Triple-DiD.
2. **Migração ocupacional:** Em municípios conectados, trabalhadores de ocupações de alta exposição migram para ocupações de baixa exposição? (Medir via aumento de admissões em ocupações de baixa exposição em municípios de alta conectividade.)
3. **Efeito spillover entre municípios vizinhos:** Se houver dados de contiguidade municipal (IBGE), testar se municípios vizinhos a municípios conectados também sofrem efeito.

#### 0.13–0.14 Tabelas, Figuras e Síntese

Seguir o padrão da Etapa 2b/2c:
- Tabela principal do Triple-DiD (3 modelos lado a lado)
- Event study com dois grupos sobrepostos
- Heatmap de significância por outcome × teste de robustez
- Tabela-síntese narrativa

---

## Cuidados Metodológicos

### 1. SUTVA e Spillovers
O Triple-DiD assume que o tratamento em um município não afeta outros. Possíveis violações: migração de trabalhadores entre municípios, competição interurbana por emprego. Mitigação: o CAGED registra movimentações no município do empregador, e a mobilidade intermunicipal mensal é relativamente baixa no curto prazo. Discutir na dissertação.

### 2. Endogeneidade da Conectividade
Se municípios mais conectados são sistematicamente diferentes (mais ricos, mais urbanos, mais educados), o efeito pode refletir riqueza e não conectividade. Mitigação: incluir PIB per capita como controle, e os FE de UF×período absorvem diferenças temporais entre estados. Robustez: usar variação de conectividade **dentro do mesmo estado** (que é o que os FE de UF×período garantem).

### 3. Múltiplas Hipóteses
Aplicar correção FDR (Benjamini-Hochberg) sobre os p-values dos múltiplos outcomes, como recomendado na revisão da Etapa 2. Reportar q-values.

### 4. Poder Estatístico
O Triple-DiD é mais exigente em poder que o DiD simples. Monitorar:
- Número efetivo de clusters no grupo tratado (HighExp × HighConnect)
- Variância residual após absorver FE
- Se necessário, restringir outcomes aos 4-5 prioritários

### 5. Dimensionalidade
O painel tridimensional pode ter >10 milhões de linhas. Usar `parquet` para armazenamento, e `pyFixest` lida bem com datasets grandes via absorção de FE. Se necessário, agregar por CBO 2 dígitos (como robustez).

### 6. Comparação com Etapa 2
Apresentar os resultados da Etapa 3 como **extensão** da Etapa 2, não como substituição. A narrativa ideal: "A Etapa 2 mostra o efeito médio; a Etapa 3 mostra que esse efeito é concentrado nos municípios onde a adoção de IA é viável."

---

## Checklist de Implementação

### Notebook 3a
- [ ] Configuração do ambiente (imports, paths, parâmetros)
- [ ] Download dos dados Anatel via `basedosdados` (ou CSV)
- [ ] Download dos dados IBGE (domicílios, PIB, população)
- [ ] Construção do índice de conectividade municipal (penetração BL pré-tratamento)
- [ ] Reagregação do CAGED por ocupação × município × período
- [ ] Merge do painel tridimensional
- [ ] Criação de variáveis de tratamento e interação
- [ ] Validação: estatísticas descritivas, cobertura, diagnósticos
- [ ] Exportação do painel final (.parquet)

### Notebook 3b
- [ ] Carregamento do painel e configuração
- [ ] Tabela de balanço por conectividade
- [ ] DiD separado por subgrupo de conectividade (motivação)
- [ ] Triple-DiD — 3 especificações (sem FE, FE, FE + controles)
- [ ] Event study por grupo de conectividade
- [ ] Teste formal de tendências paralelas
- [ ] Heterogeneidade adicional (capitais, porte, setor)
- [ ] Testes de robustez (R1–R11)
- [ ] Análise de mecanismos (deskilling espacial, migração)
- [ ] Tabelas LaTeX e figuras finais
- [ ] Síntese narrativa dos resultados
- [ ] Correção FDR para múltiplas hipóteses

---

## Referências Completas

- Autor, D. & Dorn, D. (2013). The Growth of Low-Skill Service Jobs and the Polarization of the US Labor Market. *American Economic Review*, 103(5), 1553-1597.
- Brynjolfsson, E., Li, D. & Raymond, L. (2025). Canaries in the AI Coal Mine: Generative AI and the Labor Market. *NBER Working Paper*.
- Cameron, A.C., Gelbach, J.B. & Miller, D.L. (2011). Robust Inference with Multiway Clustering. *Journal of Business & Economic Statistics*, 29(2), 238-249.
- Felten, E., Raj, M. & Seamans, R. (2021). Occupational, Industry, and Geographic Exposure to Artificial Intelligence: A Novel Dataset and Its Potential Uses. *Strategic Management Journal*, 42(12), 2195-2217.
- Goldfarb, A. & Tucker, C. (2019). Digital Economics. *Journal of Economic Literature*, 57(1), 3-43.
- Hjort, J. & Poulsen, J. (2019). The Arrival of Fast Internet and Employment in Africa. *American Economic Review*, 109(3), 1032-1079.
- Webb, M. (2020). The Impact of Artificial Intelligence on the Labor Market. *Stanford University Working Paper*.
