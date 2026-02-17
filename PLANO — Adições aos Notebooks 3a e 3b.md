# PLANO — Adições aos Notebooks 3a e 3b

**Objetivo:** Adicionar correções, proxies alternativos, decomposição etária e um modelo reformulado aos notebooks existentes. Não refazer o que já foi feito — apenas estender.

---

## Decisões tomadas

**Sobre os Caminhos 1 e 2:** Sim, os dois se complementam. O Caminho 1 (tendência diferencial pré) tenta salvar a especificação atual. O Caminho 2 (proxies alternativos) testa se o problema está no cutoff de conectividade. Se ambos falharem, temos evidência robusta de que a heterogeneidade espacial não é o canal — o que é um resultado informativo.

**Sobre a decomposição etária:** A intuição está correta. Se a IA substitui jovens por seniores (ou reduz salários de jovens enquanto mantém/aumenta de seniores), o efeito médio sobre salário geral pode ser atenuado ou anulado. Precisamos decompor. A abordagem é rodar o Triple-DiD separadamente por faixa etária, usando outcomes específicos (admissões e salário de jovens, de intermediários, de seniores).

**Sobre o modelo reformulado:** A ideia de focar nos jovens como grupo mais afetado faz sentido teórico (menor experiência, mais substituíveis por IA, menor poder de barganha). O modelo reformulado não substitui o Triple-DiD — é um experimento adicional que testa uma hipótese mais precisa: "A IA generativa reduziu a participação de jovens nas contratações, especialmente em ocupações expostas e municípios conectados."

---

## Resumo das adições

| O que | Onde | Tipo |
|-------|------|------|
| Agregação por faixa etária | **Notebook 3a** — nova seção após 0.9 | Dados |
| Variável de % fibra óptica | **Notebook 3a** — ajuste na seção 0.4 | Dados |
| Tendência diferencial pré (Caminho 1) | **Notebook 3b** — nova seção após 0.7 | Estimação |
| Proxies alternativos de conectividade (Caminho 2) | **Notebook 3b** — nova seção de robustez | Estimação |
| Decomposição etária do Triple-DiD | **Notebook 3b** — nova seção após robustez | Estimação |
| Modelo reformulado: jovens × IA × conectividade | **Notebook 3b** — nova seção final | Estimação |

---

## Adições ao Notebook 3a

### A1. Agregação por faixa etária (nova seção 0.10)

Adicionar após a seção 0.9 (Exportação). Criar outcomes desagregados por faixa etária dentro de cada célula ocupação × município × mês.

**Faixas etárias:**
- Jovens: 18–29 anos
- Intermediários: 30–49 anos
- Seniores: 50+ anos

```python
# ============================================================
# Etapa 3a.10 — Decomposição por Faixa Etária
# ============================================================

# Definir faixas
def faixa_etaria(idade):
    if idade < 30:
        return 'jovem'
    elif idade < 50:
        return 'intermediario'
    else:
        return 'senior'

# Reagregar CAGED municipal por ocupação × município × período × faixa etária
# (a partir dos microdados, antes da agregação final)
# Se os microdados já foram descartados, usar a coluna 'idade' para criar
# os outcomes diretamente na agregação BigQuery.

# OPÇÃO A: Query BigQuery adicional
query_caged_idade = """
SELECT
    SUBSTR(cbo_2002, 1, 4) as cbo_4d,
    id_municipio,
    CONCAT(CAST(ano AS STRING), '-', LPAD(CAST(mes AS STRING), 2, '0')) as periodo,

    -- Admissões por faixa
    SUM(CASE WHEN idade < 30 AND tipo_movimentacao = 'admissao' THEN 1 ELSE 0 END) as adm_jovem,
    SUM(CASE WHEN idade BETWEEN 30 AND 49 AND tipo_movimentacao = 'admissao' THEN 1 ELSE 0 END) as adm_intermediario,
    SUM(CASE WHEN idade >= 50 AND tipo_movimentacao = 'admissao' THEN 1 ELSE 0 END) as adm_senior,

    -- Salário médio por faixa (admissões)
    AVG(CASE WHEN idade < 30 AND tipo_movimentacao = 'admissao' THEN salario END) as sal_jovem,
    AVG(CASE WHEN idade BETWEEN 30 AND 49 AND tipo_movimentacao = 'admissao' THEN salario END) as sal_intermediario,
    AVG(CASE WHEN idade >= 50 AND tipo_movimentacao = 'admissao' THEN salario END) as sal_senior,

    -- Total de admissões (para calcular shares)
    SUM(CASE WHEN tipo_movimentacao = 'admissao' THEN 1 ELSE 0 END) as adm_total

FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano BETWEEN 2021 AND 2025
GROUP BY cbo_4d, id_municipio, periodo
"""

# OPÇÃO B: Se já tem os microdados locais com coluna 'idade',
# reagregar localmente com pandas groupby
```

**Outcomes a construir a partir dessa agregação:**

```python
# Share de jovens nas admissões (outcome principal do modelo reformulado)
df_panel['share_jovem'] = df_panel['adm_jovem'] / df_panel['adm_total']
df_panel['share_senior'] = df_panel['adm_senior'] / df_panel['adm_total']

# Log de admissões por faixa
df_panel['ln_adm_jovem'] = np.log1p(df_panel['adm_jovem'])
df_panel['ln_adm_intermediario'] = np.log1p(df_panel['adm_intermediario'])
df_panel['ln_adm_senior'] = np.log1p(df_panel['adm_senior'])

# Log de salário real por faixa (deflacionar pelo IPCA, mesmo procedimento)
for faixa in ['jovem', 'intermediario', 'senior']:
    col_sal = f'sal_{faixa}'
    col_real = f'sal_real_{faixa}'
    df_panel[col_real] = df_panel[col_sal] / df_panel['deflator_ipca']
    df_panel[f'ln_sal_real_{faixa}'] = np.log(df_panel[col_real])

# Razão salarial jovem/senior (mede compressão salarial)
df_panel['razao_sal_jovem_senior'] = df_panel['sal_real_jovem'] / df_panel['sal_real_senior']
```

**Nota:** Haverá muitos NaN — nem toda célula ocupação×município×mês terá admissões em todas as faixas. As regressões com outcomes por faixa terão menos observações. Isso é esperado. Documentar a perda amostral.

### A2. Variável de % fibra óptica (ajuste na seção 0.4)

Se a % fibra não foi calculada no 3a original, adicionar:

```python
# Na seção 0.4 (Construção do Índice de Conectividade), adicionar:

# % fibra óptica como proxy alternativo de qualidade
# (já deveria existir do query Anatel; se não, reprocessar)
df_conectividade['pct_fibra_pre'] = (
    df_conectividade['acessos_fibra_pre'] / df_conectividade['total_acessos_pre']
)

# Cutoff por mediana de % fibra
mediana_fibra = df_conectividade['pct_fibra_pre'].median()
df_conectividade['alta_fibra'] = (df_conectividade['pct_fibra_pre'] > mediana_fibra).astype(int)

# Merge com o painel (adicionar coluna)
df_panel = df_panel.merge(
    df_conectividade[['id_municipio', 'pct_fibra_pre', 'alta_fibra']],
    on='id_municipio', how='left'
)

# Interações para o Triple-DiD com fibra
df_panel['post_alta_fibra'] = df_panel['post'] * df_panel['alta_fibra']
df_panel['alta_exp_alta_fibra'] = df_panel['alta_exp'] * df_panel['alta_fibra']
df_panel['triple_did_fibra'] = df_panel['post'] * df_panel['alta_exp'] * df_panel['alta_fibra']
```

### A3. Re-exportar painel com as novas variáveis

```python
# Etapa 3a — Re-exportação (sobrescreve o parquet anterior)
df_panel.to_parquet(DATA_DIR / 'painel_caged_municipio_anatel_v2.parquet', index=False)
print(f"Painel atualizado: {df_panel.shape[0]:,} obs, {df_panel.shape[1]} variáveis")
print(f"Novos outcomes etários: share_jovem, share_senior, ln_adm_jovem, ...")
print(f"Novas proxies: alta_fibra, triple_did_fibra")
```

---

## Adições ao Notebook 3b

### B1. Correção de tendência diferencial pré — Caminho 1 (nova seção 0.7b)

Inserir imediatamente após a seção 0.7 (Placebo). O objetivo é verificar se o β₇ sobrevive quando controlamos por uma tendência linear específica do grupo alta_exp × alta_conectividade.

```python
# ============================================================
# Etapa 3b — 0.7b Correção de Tendência Diferencial Pré (Caminho 1)
# ============================================================

# Lógica: se o placebo falha porque existe uma tendência pré-existente
# na interação tripla, podemos controlar por isso adicionando:
#   alta_exp × alta_conectividade × trend
# onde 'trend' é uma variável de tendência linear (1, 2, 3, ..., T)

# Construir variável de tendência
periodos_ordenados = sorted(df_panel['periodo'].unique())
trend_map = {p: i+1 for i, p in enumerate(periodos_ordenados)}
df_panel['trend'] = df_panel['periodo'].map(trend_map)

# Interação de tendência diferencial
df_panel['trend_exp_conect'] = (
    df_panel['alta_exp'] * df_panel['alta_conectividade'] * df_panel['trend']
)

# Também incluir tendências de cada interação dupla (para completude)
df_panel['trend_exp'] = df_panel['alta_exp'] * df_panel['trend']
df_panel['trend_conect'] = df_panel['alta_conectividade'] * df_panel['trend']

# --- Modelo com tendência diferencial pré ---
# Especificação: adicionar trend_exp_conect + trend_exp + trend_conect como controles

import pyfixest as pf

outcome = 'ln_salario_real_adm'  # ou iterar sobre outcomes

formula_trend = (
    f"{outcome} ~ triple_did + post_alta_exp + post_alta_conect + alta_exp_alta_conect"
    f" + trend_exp_conect + trend_exp + trend_conect"
    f" | cbo_4d + uf_periodo"
)

model_trend = pf.feols(formula_trend, data=df_panel, vcov={'CRV1': 'id_municipio'})
model_trend.summary()

# --- Interpretar ---
# Se triple_did continua significativo (e o sinal se mantém negativo):
#   → O efeito é robusto à tendência pré. A tendência linear diferencial
#     foi controlada, e o efeito pós-ChatGPT vai ALÉM da tendência.
#   → RESULTADO BOM. Reportar como especificação principal corrigida.
#
# Se triple_did perde significância:
#   → O efeito era explicado pela tendência pré-existente, não pelo ChatGPT.
#   → Documentar honestamente. O Caminho 2 e a decomposição etária
#     podem ainda revelar efeitos reais.

# --- Comparar com o modelo original (sem tendência) ---
# Apresentar lado a lado: modelo original vs. modelo com tendência
```

**Nota importante:** A tendência linear é a correção mais simples. Se o placebo ainda falhar (o que seria raro após controlar tendência linear), considerar tendência quadrática. Mas linear é o padrão na literatura.

### B2. Proxies alternativos de conectividade — Caminho 2 (nova seção 0.8b)

Inserir como nova seção de robustez. Testar 4 proxies diferentes.

```python
# ============================================================
# Etapa 3b — 0.8b Proxies Alternativos de Conectividade (Caminho 2)
# ============================================================

# --- Proxy 1: Extremos Q75 vs Q25 (exclui municípios intermediários) ---
df_extremos = df_panel[
    (df_panel['penetracao_bl'] >= df_panel['penetracao_bl'].quantile(0.75)) |
    (df_panel['penetracao_bl'] <= df_panel['penetracao_bl'].quantile(0.25))
].copy()
df_extremos['alta_conect_extremo'] = (
    df_extremos['penetracao_bl'] >= df_extremos['penetracao_bl'].quantile(0.75)
).astype(int)
df_extremos['triple_did_extremo'] = (
    df_extremos['post'] * df_extremos['alta_exp'] * df_extremos['alta_conect_extremo']
)

formula_extremo = (
    f"{outcome} ~ triple_did_extremo + post:alta_exp + post:alta_conect_extremo"
    f" + alta_exp:alta_conect_extremo | cbo_4d + uf_periodo"
)
model_extremo = pf.feols(formula_extremo, data=df_extremos, vcov={'CRV1': 'id_municipio'})

# Expectativa: efeito mais forte (contraste mais limpo entre extremos)

# --- Proxy 2: % Fibra Óptica (qualidade, não quantidade) ---
# Usar alta_fibra já construída no 3a

df_panel['post_alta_fibra'] = df_panel['post'] * df_panel['alta_fibra']
df_panel['alta_exp_alta_fibra'] = df_panel['alta_exp'] * df_panel['alta_fibra']
df_panel['triple_did_fibra'] = df_panel['post'] * df_panel['alta_exp'] * df_panel['alta_fibra']

formula_fibra = (
    f"{outcome} ~ triple_did_fibra + post:alta_exp + post:alta_fibra"
    f" + alta_exp:alta_fibra | cbo_4d + uf_periodo"
)
model_fibra = pf.feols(formula_fibra, data=df_panel, vcov={'CRV1': 'id_municipio'})

# Expectativa: fibra captura qualidade de conexão (velocidade para usar LLMs),
# pode ser proxy mais preciso que penetração bruta

# --- Proxy 3: Tratamento Contínuo (sem cutoff) ---
# Dose-resposta: penetração × exposure_score × post

df_panel['dose_triple'] = (
    df_panel['penetracao_bl'] * df_panel['ilo_exposure_score'] * df_panel['post']
)
df_panel['dose_exp_post'] = df_panel['ilo_exposure_score'] * df_panel['post']
df_panel['dose_conect_post'] = df_panel['penetracao_bl'] * df_panel['post']
df_panel['dose_exp_conect'] = df_panel['ilo_exposure_score'] * df_panel['penetracao_bl']

formula_continuo = (
    f"{outcome} ~ dose_triple + dose_exp_post + dose_conect_post + dose_exp_conect"
    f" | cbo_4d + uf_periodo"
)
model_continuo = pf.feols(formula_continuo, data=df_panel, vcov={'CRV1': 'id_municipio'})

# Expectativa: evita arbitrariedade do cutoff.
# Coeficiente negativo em dose_triple = quanto mais exposição E conectividade,
# maior a queda salarial pós-ChatGPT

# --- Proxy 4: Apenas Capitais ---
# Capital = 1 como proxy extrema de conectividade

# Criar dummy de capital (se não existe ainda)
capitais_ibge = [
    '1100205','1200401','1302603','1400100','1501402','1600303','1721000',
    '2111300','2211001','2304400','2408102','2507507','2611606','2704302',
    '2800308','2927408','3106200','3205309','3304557','3550308',
    '4106902','4205407','4314902','5002704','5103403','5208707','5300108'
]
df_panel['capital'] = df_panel['id_municipio'].astype(str).isin(capitais_ibge).astype(int)
df_panel['triple_did_capital'] = df_panel['post'] * df_panel['alta_exp'] * df_panel['capital']

formula_capital = (
    f"{outcome} ~ triple_did_capital + post:alta_exp + post:capital"
    f" + alta_exp:capital | cbo_4d + uf_periodo"
)
model_capital = pf.feols(formula_capital, data=df_panel, vcov={'CRV1': 'id_municipio'})

# --- Tabela comparativa ---
# Apresentar os 5 modelos lado a lado:
# (1) Original (mediana penetração)
# (2) Extremos Q75/Q25
# (3) % Fibra
# (4) Contínuo
# (5) Capitais
# Para cada um: coef triple_did, SE, p-valor

# Para cada proxy, rodar também o placebo temporal (Dez/2021).
# Se algum proxy resolve o problema do placebo, esse é o proxy correto.
```

**Decisão metodológica:** Rodar o placebo para CADA proxy. Se o proxy de fibra ou o contínuo passarem no placebo enquanto a penetração bruta não passa, isso sugere que o problema está na definição de conectividade, não no design como um todo.

### B3. Decomposição etária do Triple-DiD (nova seção 0.9b)

Inserir após os testes de robustez. Esta seção responde diretamente à pergunta: "O efeito sobre jovens está sendo anulado pelo efeito sobre seniores?"

```python
# ============================================================
# Etapa 3b — 0.9b Decomposição Etária do Triple-DiD
# ============================================================

# --- Hipótese ---
# A IA generativa não afeta todos os trabalhadores igualmente.
# Jovens (<30): mais substituíveis, menor experiência, mais afetados negativamente
# Seniores (50+): experiência complementa IA, podem se beneficiar
# O efeito médio pode mascarar essa heterogeneidade

# --- Outcomes por faixa etária ---
outcomes_idade = {
    'Admissões jovens (log)': 'ln_adm_jovem',
    'Admissões intermediários (log)': 'ln_adm_intermediario',
    'Admissões seniores (log)': 'ln_adm_senior',
    'Share jovens nas admissões': 'share_jovem',
    'Share seniores nas admissões': 'share_senior',
    'Salário real jovens (log)': 'ln_sal_real_jovem',
    'Salário real intermediários (log)': 'ln_sal_real_intermediario',
    'Salário real seniores (log)': 'ln_sal_real_senior',
    'Razão salarial jovem/senior': 'razao_sal_jovem_senior',
}

# --- Rodar Triple-DiD para cada outcome ---
# Usar a melhor especificação do Caminho 1/2
# (a que passou no placebo, ou se nenhuma passou, usar a com tendência)

resultados_idade = {}
for nome, outcome_var in outcomes_idade.items():
    df_valid = df_panel.dropna(subset=[outcome_var])
    if len(df_valid) < 1000:
        print(f"SKIP {nome}: apenas {len(df_valid)} obs válidas")
        continue

    formula = (
        f"{outcome_var} ~ triple_did + post_alta_exp + post_alta_conect"
        f" + alta_exp_alta_conect | cbo_4d + uf_periodo"
    )
    try:
        model = pf.feols(formula, data=df_valid, vcov={'CRV1': 'id_municipio'})
        coef = model.coef()['triple_did']
        se = model.se()['triple_did']
        pval = model.pvalue()['triple_did']
        resultados_idade[nome] = {'coef': coef, 'se': se, 'pval': pval, 'n': len(df_valid)}
    except Exception as e:
        print(f"ERRO {nome}: {e}")

# --- Apresentar resultados ---
df_resultados_idade = pd.DataFrame(resultados_idade).T
df_resultados_idade['sig'] = df_resultados_idade['pval'].apply(
    lambda p: '***' if p < 0.01 else ('**' if p < 0.05 else ('*' if p < 0.1 else ''))
)
print(df_resultados_idade.to_string())

# --- Expectativas ---
# Se a hipótese de "compensação etária" estiver correta:
#   - share_jovem: β₇ NEGATIVO (menos jovens contratados pós-IA em municípios conectados)
#   - share_senior: β₇ POSITIVO (mais seniores contratados)
#   - ln_sal_real_jovem: β₇ NEGATIVO (salário de jovens cai mais)
#   - ln_sal_real_senior: β₇ ZERO ou POSITIVO (salário de seniores não cai, ou sobe)
#   - razao_sal_jovem_senior: β₇ NEGATIVO (compressão salarial contra jovens)
#
# Esse padrão explicaria por que o Triple-DiD sobre salário GERAL
# mostra efeito fraco (-0.016, p=0.059): o efeito negativo nos jovens
# é parcialmente compensado pelo efeito neutro/positivo nos seniores.
```

### B4. Modelo Reformulado: Jovens × IA × Conectividade (nova seção 0.10)

Esta é a seção final e conceitualmente a mais ambiciosa. O foco muda de "salário geral" para "participação dos jovens no mercado de trabalho".

```python
# ============================================================
# Etapa 3b — 0.10 Modelo Reformulado: Impacto sobre Jovens
# ============================================================

# --- Narrativa ---
# Hipótese reformulada:
# "Após o lançamento do ChatGPT, houve uma redução da participação de
# jovens nas contratações de ocupações expostas à IA, especialmente em
# municípios com alta conectividade. A IA generativa reduziu a demanda
# relativa por trabalhadores jovens e menos experientes nessas ocupações,
# mas esse efeito só se materializa onde há infraestrutura para adoção."
#
# A alta exposição à IA explica PARTE desse efeito, mas não todo.
# Outros fatores (automação geral, mudanças na composição educacional,
# tendências demográficas) também contribuem.

# --- Outcome principal ---
# share_jovem = admissões de jovens (<30) / total de admissões
# Interpretação: se β₇ < 0, a participação de jovens nas contratações
# caiu mais em ocupações expostas à IA em municípios conectados.

# --- Modelo 1: Triple-DiD puro ---
formula_jovem_1 = (
    "share_jovem ~ triple_did + post_alta_exp + post_alta_conect"
    " + alta_exp_alta_conect | cbo_4d + uf_periodo"
)
m_jovem_1 = pf.feols(formula_jovem_1, data=df_panel.dropna(subset=['share_jovem']),
                       vcov={'CRV1': 'id_municipio'})

# --- Modelo 2: Com tendência diferencial pré ---
formula_jovem_2 = (
    "share_jovem ~ triple_did + post_alta_exp + post_alta_conect"
    " + alta_exp_alta_conect + trend_exp_conect + trend_exp + trend_conect"
    " | cbo_4d + uf_periodo"
)
m_jovem_2 = pf.feols(formula_jovem_2, data=df_panel.dropna(subset=['share_jovem']),
                       vcov={'CRV1': 'id_municipio'})

# --- Modelo 3: Com controles demográficos ---
formula_jovem_3 = (
    "share_jovem ~ triple_did + post_alta_exp + post_alta_conect"
    " + alta_exp_alta_conect + trend_exp_conect + trend_exp + trend_conect"
    " + pct_superior_adm + pct_mulher_adm + ln_pib_pc"
    " | cbo_4d + uf_periodo"
)
m_jovem_3 = pf.feols(formula_jovem_3, data=df_panel.dropna(subset=['share_jovem']),
                       vcov={'CRV1': 'id_municipio'})

# --- Tabela: 3 modelos lado a lado ---
pf.etable([m_jovem_1, m_jovem_2, m_jovem_3])

# --- Placebo temporal (Dez/2021) para share_jovem ---
df_pre = df_panel[df_panel['periodo_dt'] < '2022-11-01'].copy()
df_pre['post_placebo'] = (df_pre['periodo_dt'] >= '2021-12-01').astype(int)
df_pre['triple_placebo'] = (
    df_pre['post_placebo'] * df_pre['alta_exp'] * df_pre['alta_conectividade']
)
formula_placebo_jovem = (
    "share_jovem ~ triple_placebo + post_placebo:alta_exp"
    " + post_placebo:alta_conectividade + alta_exp:alta_conectividade"
    " | cbo_4d + uf_periodo"
)
m_placebo_jovem = pf.feols(formula_placebo_jovem,
                            data=df_pre.dropna(subset=['share_jovem']),
                            vcov={'CRV1': 'id_municipio'})
print(f"Placebo share_jovem: coef={m_placebo_jovem.coef()['triple_placebo']:.4f}, "
      f"p={m_placebo_jovem.pvalue()['triple_placebo']:.4f}")

# --- Event study para share_jovem (por grupo de conectividade) ---
# Mesma lógica do event study da seção 0.6, mas com share_jovem como outcome
# Plotar as duas séries (alta e baixa conectividade) no mesmo gráfico
# Isso permite VER se há divergência pós-ChatGPT na composição etária

# --- Análise adicional: decomposição do efeito ---
# Quão grande é o efeito da IA vs. outros fatores?
# Estratégia: comparar o β₇ do Triple-DiD (efeito IA × conectividade)
# com o efeito simples post × alta_conectividade (efeito geral de
# conectividade, independente de IA).
#
# Se β₇ ≈ β₆ (post × alta_conect), então o efeito sobre jovens
# é generalizado e não específico da IA.
# Se β₇ >> β₆, então a IA amplifica o efeito sobre jovens
# ALÉM do efeito geral de conectividade.
```

---

## Ordem de execução recomendada

### No Notebook 3a:
1. Rodar a query BigQuery com agregação por faixa etária (seção A1)
2. Construir os outcomes etários (share_jovem, ln_adm_jovem, etc.)
3. Adicionar % fibra e dummy de capital (seção A2)
4. Re-exportar painel com as novas colunas (seção A3)

### No Notebook 3b:
1. **Primeiro:** Caminho 1 — tendência diferencial pré (seção B1)
   - Se β₇ sobrevive → reportar como especificação principal corrigida
   - Se β₇ morre → documentar, prosseguir com Caminho 2
2. **Segundo:** Caminho 2 — proxies alternativos (seção B2)
   - Para CADA proxy, rodar modelo + placebo
   - Montar tabela comparativa dos 5 proxies
   - Se algum proxy passa no placebo → usar como especificação alternativa
3. **Terceiro:** Decomposição etária (seção B3)
   - Rodar Triple-DiD para 9 outcomes etários
   - Verificar se o padrão jovens↓ / seniores↑ se confirma
4. **Quarto:** Modelo reformulado (seção B4)
   - share_jovem como outcome principal
   - 3 especificações + placebo + event study
   - Esta seção pode produzir os resultados mais originais da dissertação

---

## O que esperar dos resultados

**Cenário otimista:** A tendência diferencial pré (Caminho 1) controla o placebo e o β₇ se torna mais significativo. A decomposição etária revela que o efeito é concentrado nos jovens. O modelo reformulado com share_jovem mostra efeito forte e passa no placebo. Narrativa: "A IA generativa reduziu a participação de jovens no mercado de trabalho formal, especialmente em ocupações expostas e municípios conectados."

**Cenário intermediário:** O Triple-DiD sobre salário geral continua frágil, mas a decomposição etária revela efeitos heterogêneos claros (jovens↓, seniores→). O modelo reformulado com share_jovem funciona melhor que o modelo geral. Narrativa: "O efeito médio da IA sobre salários é atenuado pela heterogeneidade etária. Jovens são os mais afetados, mas o efeito é compensado por mudanças na composição."

**Cenário pessimista:** Nenhuma especificação resolve o placebo. A decomposição etária não mostra padrão claro. Narrativa: "A heterogeneidade espacial na adoção de IA não é detectável no período analisado, possivelmente porque a adoção de IA generativa no Brasil é mediada por empresas de atuação nacional, não pela infraestrutura municipal local."

**Mesmo o cenário pessimista é publicável.** Um resultado nulo bem documentado é valioso — mostra que a infraestrutura digital municipal não é o canal de transmissão relevante no curto prazo.

---

## Checklist

### Notebook 3a — Adições
- [ ] Query BigQuery para admissões/salário por faixa etária
- [ ] Construir: share_jovem, share_senior, ln_adm por faixa, ln_sal por faixa, razão salarial
- [ ] Adicionar % fibra óptica como variável de conectividade
- [ ] Adicionar dummy de capital estadual
- [ ] Re-exportar painel v2

### Notebook 3b — Adições
- [ ] B1: Tendência diferencial pré (trend × alta_exp × alta_conect)
- [ ] B1: Comparar modelo original vs. modelo com tendência
- [ ] B2: Triple-DiD com 4 proxies alternativos (extremos, fibra, contínuo, capitais)
- [ ] B2: Placebo temporal para CADA proxy
- [ ] B2: Tabela comparativa dos 5 proxies
- [ ] B3: Triple-DiD para 9 outcomes etários
- [ ] B3: Identificar padrão jovens↓ / seniores↑ (ou não)
- [ ] B4: Modelo reformulado — share_jovem como outcome
- [ ] B4: 3 especificações + placebo + event study
- [ ] B4: Comparação β₇ vs β₆ (efeito IA vs. efeito geral de conectividade)
- [ ] Tabela-síntese final com todos os resultados
