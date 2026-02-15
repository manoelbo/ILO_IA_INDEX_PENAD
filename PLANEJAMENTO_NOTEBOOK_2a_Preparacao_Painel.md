# ETAPA 2a — Preparação do Painel CAGED + ILO Exposure Index

## Planejamento Detalhado do Notebook

**Dissertação:** Inteligência Artificial Generativa e o Mercado de Trabalho Brasileiro: Uma Análise de Exposição Ocupacional e seus Efeitos Distributivos.

**Aluno:** Manoel Brasil Orlandi

**Objetivo deste notebook:** Construir o painel mensal de ocupações formais brasileiras (2021–2025) a partir do Novo CAGED, realizar o crosswalk CBO → ISCO-08 (ver documento `abordagens_crosswalk.md` para análise detalhada), e fazer o merge com o índice de exposição à IA generativa da OIT (Gmyrek, Berg & Cappelli, 2025). O output final é um dataset analítico pronto para a estimação DiD no Notebook 2b.

**Estratégia de crosswalk:** Análise principal a **2 dígitos** ISCO-08 (match perfeito CBO↔ISCO), com robustez a **4 dígitos** via dois passos (CBO→ISCO-88→ISCO-08). Ver `abordagens_crosswalk.md` para justificativa completa.

**Inspiração metodológica:** Hui, Reshef & Zhou (2024), "The Short-Term Effects of Generative Artificial Intelligence on Employment: Evidence from an Online Labor Market" — adaptado para dados administrativos brasileiros (CAGED) com o índice ILO de exposição ocupacional.

---

## Referências Principais

- Gmyrek, P., Berg, J. & Cappelli, D. (2025). *Generative AI and Jobs: An updated global assessment*. ILO Working Paper 140.
- Hui, X., Reshef, O. & Zhou, L. (2024). *The Short-Term Effects of Generative AI on Employment*. Organization Science, 35(6).
- Cunningham, S. (2021). *Causal Inference: The Mixtape*. Yale University Press. Capítulo 9.
- Callaway, B. & Sant'Anna, P. (2021). *Difference-in-differences with multiple time periods*. Journal of Econometrics, 225(2).
- IBGE/CONCLA. *Classificação Brasileira de Ocupações (CBO)*.
- Muendler, M.-A., Poole, J. et al. (2004). *Job Concordances for Brazil: Mapping CBO to ISCO-88*.

---

## Ficha Técnica dos Dados

### Novo CAGED (Cadastro Geral de Empregados e Desempregados)

| Item | Descrição |
|------|-----------|
| **Fonte** | Ministério do Trabalho e Emprego (MTE), via Base dos Dados (BigQuery) |
| **Dataset BigQuery** | `basedosdados.br_me_caged.microdados_movimentacao` |
| **Período** | Janeiro/2021 — Dezembro/2025 (60 meses) |
| **Unidade** | Movimentação individual (admissão ou desligamento) |
| **Cobertura** | Emprego formal (CLT) em todo o Brasil |
| **Acesso** | `basedosdados` Python package + Google Cloud Project |

> **Nota sobre a janela temporal:** Excluímos 2020 para evitar os efeitos distorcivos da pandemia de COVID-19 sobre o mercado de trabalho formal. O ano de 2020 apresentou quedas e recuperações atípicas em contratações e demissões que contaminariam o período pré-tratamento do DiD. A janela Jan/2021–Dez/2025 oferece 23 meses pré-ChatGPT (Jan/2021–Nov/2022) e 37 meses pós (Dez/2022–Dez/2025).

> **Nota sobre o Novo CAGED:** A partir de janeiro/2020, o CAGED foi substituído pelo sistema eSocial (Portaria SEPRT 1.127/2019). Usamos dados de 2021+ para consistência metodológica (eSocial já estabilizado) e para evitar efeitos COVID.

> **Nota sobre disponibilidade:** O CAGED tem dados publicados até dezembro/2025. Verificar disponibilidade no basedosdados (que pode ter defasagem de alguns meses). Se 2025 não estiver completo no basedosdados, baixar os meses faltantes diretamente do [PDET/MTE](http://pdet.mte.gov.br/novo-caged) ou ajustar a janela para o último mês disponível.

### Variáveis-chave do CAGED

| Variável BigQuery | Nome no dataset | Descrição |
|-------------------|-----------------|-----------|
| `ano` | `ano` | Ano da movimentação |
| `mes` | `mes` | Mês da movimentação |
| `sigla_uf` | `sigla_uf` | UF do estabelecimento |
| `id_municipio` | `id_municipio` | Código IBGE do município (7 dígitos) |
| `cbo_2002` | `cbo_2002` | Código CBO 2002 (6 dígitos: XXXX-XX) |
| `categoria` | `categoria` | Tipo de movimentação (admissão/desligamento) |
| `tipo_movimentacao` | `tipo_movimentacao` | Subtipo (primeiro emprego, reemprego, transferência, etc.) |
| `salario_mensal` | `salario_mensal` | Salário mensal contratual (R$) |
| `saldo_movimentacao` | `saldo_movimentacao` | +1 (admissão) ou -1 (desligamento) |
| `grau_instrucao` | `grau_instrucao` | Escolaridade do trabalhador |
| `idade` | `idade` | Idade do trabalhador |
| `sexo` | `sexo` | Sexo do trabalhador |
| `raca_cor` | `raca_cor` | Raça/cor do trabalhador |
| `cnae_2_secao` | `cnae_2_secao` | Seção CNAE 2.0 |
| `cnae_2_subclasse` | `cnae_2_subclasse` | Subclasse CNAE 2.0 |
| `tamanho_estabelecimento` | `tamanho_estabelecimento` | Faixa de tamanho do estabelecimento |

### Índice ILO de Exposição à IA Generativa

| Item | Descrição |
|------|-----------|
| **Fonte** | Gmyrek, Berg & Cappelli (2025), ILO Working Paper 140 |
| **Arquivo** | `data/input/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx` |
| **Classificação** | ISCO-08, 4 dígitos (427 ocupações) |
| **Score** | `mean_score_2025` — média do score de exposição por ocupação [0, 1] |
| **Gradiente** | `potential25` — classificação em 6 categorias (Not Exposed → Gradient 4) |
| **Disponível da Etapa 1** | `data/processed/ilo_exposure_clean.csv` (já processado) |

---

## Estrutura do Notebook

O notebook segue o mesmo padrão dos Notebooks 1a e 1b: blocos markdown explicativos alternados com blocos de código, passos numerados, e checkpoints de validação após cada etapa.

---

### 1. Configuração do ambiente

**Markdown:** Definir caminhos, importar bibliotecas e configurar parâmetros.

```python
# Etapa 2a.1 — Configuração do ambiente

import warnings
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATA_INPUT     = Path("data/input")
DATA_RAW       = Path("data/raw")
DATA_PROCESSED = Path("data/processed")
DATA_OUTPUT    = Path("data/output")

for d in [DATA_RAW, DATA_PROCESSED, DATA_OUTPUT]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parâmetros do Painel CAGED
# ---------------------------------------------------------------------------
GCP_PROJECT_ID  = "mestrado-pnad-2026"   # Mesmo projeto da Etapa 1

# Período do painel: Jan/2021 — Dez/2025 (60 meses)
# Exclui 2020 para evitar efeitos COVID-19
ANO_INICIO      = 2021
ANO_FIM         = 2025

# Evento: lançamento do ChatGPT (30 de novembro de 2022)
# Pós-tratamento: a partir de dezembro/2022 (mês imediatamente após)
ANO_TRATAMENTO  = 2022
MES_TRATAMENTO  = 12   # Dezembro/2022 como primeiro mês "pós"

# Salário mínimo por ano (para normalização)
SALARIO_MINIMO = {
    2021: 1100, 2022: 1212, 2023: 1320, 2024: 1412, 2025: 1518
}

# ---------------------------------------------------------------------------
# Arquivo ILO (mesmo da Etapa 1)
# ---------------------------------------------------------------------------
ILO_FILE = DATA_PROCESSED / "ilo_exposure_clean.csv"
# Alternativa se rodar standalone:
# ILO_FILE = DATA_INPUT / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"

# ---------------------------------------------------------------------------
# Crosswalk CBO → ISCO-08
# Ver: abordagens_crosswalk.md para análise completa
# ---------------------------------------------------------------------------
# ESTRATÉGIA PRINCIPAL: 2 dígitos (match perfeito CBO ↔ ISCO-08)
# ROBUSTEZ: 4 dígitos via dois passos (CBO→ISCO-88→ISCO-08)
#
# A CBO 2002 foi construída com base na ISCO-88 (NÃO ISCO-08).
# A 2 dígitos, CBO, ISCO-88 e ISCO-08 são idênticas (43 sub-major groups).
# A 4 dígitos, há diferenças reais — por isso usamos Muendler + ILO tables.
# ---------------------------------------------------------------------------

# Muendler & Poole (2004): CBO → ISCO-88
MUENDLER_URL = "https://econweb.ucsd.edu/~muendler/download/brazil/cbo/cbo-isco-conc.csv"
MUENDLER_FILE = DATA_INPUT / "cbo-isco-conc.csv"

# ILO: ISCO-88 → ISCO-08 correspondence
ILO_CORRTAB_URL = "http://www.ilo.org/public/english/bureau/stat/isco/docs/corrtab88-08.xls"
ILO_CORRTAB_FILE = DATA_INPUT / "corrtab88-08.xls"

# Tabela oficial MTE/CONCLA (se obtida via LAI — opcional, gold standard)
MTE_CROSSWALK_FILE = DATA_INPUT / "crosswalk_cbo_isco08_mte.csv"

print("Configuração carregada.")
print(f"  Período: {ANO_INICIO}–{ANO_FIM} ({(ANO_FIM - ANO_INICIO + 1) * 12} meses)")
print(f"  Evento: ChatGPT — Nov/2022 (pós a partir de {MES_TRATAMENTO}/{ANO_TRATAMENTO})")
print(f"  Projeto GCP: {GCP_PROJECT_ID}")
print(f"  ILO file: {ILO_FILE}")
```

---

### 2a. Download dos microdados CAGED

**Markdown:**

Extrair do Novo CAGED (BigQuery/Base dos Dados) todas as movimentações de emprego formal no período 2021–2025.

#### Ficha técnica

| Item | Descrição |
|------|-----------|
| **Tabela BigQuery** | `basedosdados.br_me_caged.microdados_movimentacao` |
| **Período** | 2021-01 a 2025-12 (ou último mês disponível) |
| **Filtros** | `ano BETWEEN 2021 AND 2025` |
| **Volume estimado** | ~100-150 milhões de registros (movimentações) |

> **Nota metodológica — Exclusão de 2020:** O ano de 2020 foi excluído para evitar contaminação pelo COVID-19, que causou distorções severas no mercado de trabalho formal (lockdowns, layoffs em massa, programas emergenciais como BEm). Iniciar em 2021 garante um período pré-tratamento mais limpo.

> **Nota metodológica — Volume de dados:** O CAGED registra ~20-25 milhões de movimentações/ano. Para 5 anos, esperamos ~100-125M de registros. Recomenda-se download por ano para evitar timeout do BigQuery.

> **Nota sobre 2025:** Os dados do CAGED até dezembro/2025 foram publicados pelo MTE em janeiro/2026. Verificar se o basedosdados já incorporou 2025. Se não, alternativas: (a) baixar de [pdet.mte.gov.br](http://pdet.mte.gov.br/novo-caged) em CSV; (b) usar até o último mês disponível no basedosdados.

> **Nota sobre tabelas alternativas:** O basedosdados pode ter a tabela como `microdados_movimentacao` ou `microdados`. Verificar nomes exatos antes de executar.

```python
# Etapa 2a.2a — Download dos microdados CAGED
# Estratégia: baixar ano a ano e concatenar, salvando parquets individuais.

import basedosdados as bd

# ---------------------------------------------------------------------------
# PASSO 1: Verificar tabelas disponíveis no dataset CAGED
# ---------------------------------------------------------------------------
# Listar tabelas disponíveis (executar uma vez para verificar nomes)
query_tables = """
SELECT table_name
FROM `basedosdados.br_me_caged.INFORMATION_SCHEMA.TABLES`
"""
try:
    df_tables = bd.read_sql(query_tables, billing_project_id=GCP_PROJECT_ID)
    print("Tabelas disponíveis no dataset br_me_caged:")
    for t in df_tables['table_name'].tolist():
        print(f"  - {t}")
except Exception as e:
    print(f"Erro ao listar tabelas: {e}")
    print("Tentando nomes conhecidos: microdados_movimentacao, microdados_movimentacao_fora_prazo")

# ---------------------------------------------------------------------------
# PASSO 2: Verificar colunas disponíveis
# ---------------------------------------------------------------------------
query_cols = """
SELECT column_name, data_type
FROM `basedosdados.br_me_caged.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'microdados_movimentacao'
ORDER BY ordinal_position
"""
try:
    df_cols = bd.read_sql(query_cols, billing_project_id=GCP_PROJECT_ID)
    print(f"\nColunas em microdados_movimentacao ({len(df_cols)}):")
    for _, row in df_cols.iterrows():
        print(f"  {row['column_name']}: {row['data_type']}")
except Exception as e:
    print(f"Erro: {e}")
```

```python
# Etapa 2a.2a (cont.) — Download ano a ano

# ---------------------------------------------------------------------------
# PASSO 3: Download ano a ano
# ---------------------------------------------------------------------------
# NOTA PARA IMPLEMENTAÇÃO: ajustar nomes de colunas conforme output do PASSO 2.
# Os nomes abaixo são os mais prováveis baseados na documentação do basedosdados.

COLUNAS_CAGED = """
    ano,
    mes,
    sigla_uf,
    id_municipio,
    cbo_2002,
    categoria,
    tipo_movimentacao,
    saldo_movimentacao,
    salario_mensal,
    grau_instrucao,
    idade,
    sexo,
    raca_cor,
    cnae_2_secao,
    cnae_2_subclasse,
    tamanho_estabelecimento
"""

dfs_anuais = []
for ano in range(ANO_INICIO, ANO_FIM + 1):
    parquet_path = DATA_RAW / f"caged_{ano}.parquet"

    if parquet_path.exists():
        print(f"Arquivo {parquet_path.name} já existe. Carregando...")
        df_ano = pd.read_parquet(parquet_path)
    else:
        print(f"Baixando CAGED {ano} do BigQuery...")
        query = f"""
        SELECT {COLUNAS_CAGED}
        FROM `basedosdados.br_me_caged.microdados_movimentacao`
        WHERE ano = {ano}
        """
        df_ano = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID)
        df_ano.to_parquet(parquet_path, index=False)
        print(f"  Salvo: {parquet_path.name} ({len(df_ano):,} registros)")

    dfs_anuais.append(df_ano)
    print(f"  {ano}: {len(df_ano):,} movimentações")

# Concatenar
df_caged_raw = pd.concat(dfs_anuais, ignore_index=True)
print(f"\nTotal: {len(df_caged_raw):,} movimentações ({ANO_INICIO}–{ANO_FIM})")
print(f"Colunas: {list(df_caged_raw.columns)}")
```

---

### 2b. Verificar dados CAGED (CHECKPOINT)

**Markdown:** Verificar integridade dos dados baixados: cobertura temporal, volume por ano/mês, preenchimento de variáveis-chave.

```python
# Etapa 2a.2b — CHECKPOINT: Verificar dados CAGED

print("=" * 60)
print("CHECKPOINT — Microdados CAGED")
print("=" * 60)

# 1. Volume por ano
print("\nVolume por ano:")
for ano, count in df_caged_raw.groupby('ano').size().items():
    print(f"  {ano}: {count:,} movimentações")

# 2. Meses cobertos por ano
print("\nMeses por ano:")
for ano in range(ANO_INICIO, ANO_FIM + 1):
    meses = sorted(df_caged_raw[df_caged_raw['ano'] == ano]['mes'].unique())
    print(f"  {ano}: {len(meses)} meses — {meses}")
    if len(meses) != 12:
        print(f"    WARNING: Esperado 12 meses, encontrado {len(meses)}")

# 3. Preenchimento de variáveis-chave
print("\nPreenchimento de variáveis:")
for col in df_caged_raw.columns:
    n_valid = df_caged_raw[col].notna().sum()
    pct = n_valid / len(df_caged_raw) * 100
    flag = "  " if pct > 90 else "  WARNING —" if pct > 50 else "  CRÍTICO —"
    print(f"{flag} {col}: {n_valid:,} ({pct:.1f}%)")

# 4. Distribuição admissões vs desligamentos
print("\nSaldo de movimentações:")
saldo = df_caged_raw['saldo_movimentacao'].value_counts()
print(saldo)
# Ou se for texto:
# print(df_caged_raw['categoria'].value_counts())

# 5. CBO: verificar formato
cbo_sample = df_caged_raw['cbo_2002'].dropna().astype(str).head(20)
print(f"\nAmostra de códigos CBO: {cbo_sample.tolist()}")
print(f"CBO únicos: {df_caged_raw['cbo_2002'].nunique():,}")
```

---

### 3a. Agregação: Microdados → Painel Mensal por Ocupação

**Markdown:**

Agregar os microdados de movimentação (nível individual) em um painel mensal por ocupação CBO (4 dígitos). Cada linha do painel representará uma ocupação-mês com métricas agregadas.

#### Estratégia de agregação

Seguindo a abordagem de Hui, Reshef & Zhou (2024), construímos um painel ao nível de **ocupação × mês** com as seguintes métricas:

| Métrica | Cálculo | Inspiração |
|---------|---------|------------|
| `admissoes` | Soma de `saldo_movimentacao == 1` | Fluxo de contratação |
| `desligamentos` | Soma de `saldo_movimentacao == -1` | Fluxo de demissão |
| `saldo` | `admissoes - desligamentos` | Criação líquida de empregos |
| `salario_medio` | Média do `salario_mensal` das admissões | Nível salarial |
| `salario_mediano` | Mediana do `salario_mensal` das admissões | Robustez a outliers |
| `n_movimentacoes` | Total de registros | Volume total |

> **Nota metodológica — Nível de agregação:** O CAGED registra **fluxos** (contratações e demissões), não **estoques**. Diferente da PNAD (que fotografa o estoque de ocupados), o CAGED captura a dinâmica do mercado formal. Esta é a mesma lógica usada por Hui et al. (2024) com dados do Upwork.

> **Nota — CBO 4 dígitos vs 6 dígitos:** A CBO tem 6 dígitos (XXXX-XX), onde os 4 primeiros definem a "família" ocupacional e os 2 últimos a especialização. Para o crosswalk com ISCO-08, usaremos os **4 primeiros dígitos** (família CBO ≈ unit group ISCO-08). Isso alinha com o nível de granularidade do índice ILO.

```python
# Etapa 2a.3a — Agregação: Microdados → Painel Mensal por Ocupação

# ---------------------------------------------------------------------------
# PASSO 1: Preparar CBO 4 dígitos
# ---------------------------------------------------------------------------
df_caged = df_caged_raw.copy()

# Garantir CBO como string e extrair 4 primeiros dígitos
df_caged['cbo_2002'] = df_caged['cbo_2002'].astype(str).str.strip()
df_caged['cbo_4d'] = df_caged['cbo_2002'].str[:4]

# Remover CBO inválidos
cbo_invalidos = ['0000', 'nan', '', 'None']
n_antes = len(df_caged)
df_caged = df_caged[~df_caged['cbo_4d'].isin(cbo_invalidos)]
df_caged = df_caged[df_caged['cbo_4d'].str.len() == 4]
df_caged = df_caged[df_caged['cbo_4d'].str.isdigit()]
n_depois = len(df_caged)
print(f"CBO válidos: {n_depois:,} / {n_antes:,} ({n_depois/n_antes:.1%})")
print(f"Famílias CBO (4d) únicas: {df_caged['cbo_4d'].nunique()}")

# ---------------------------------------------------------------------------
# PASSO 2: Criar variável temporal
# ---------------------------------------------------------------------------
df_caged['periodo'] = df_caged['ano'].astype(str) + '-' + df_caged['mes'].astype(str).str.zfill(2)
df_caged['periodo_num'] = df_caged['ano'] * 100 + df_caged['mes']

# Flag pós-tratamento
df_caged['post'] = (df_caged['periodo_num'] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)
print(f"\nPeríodos pré: {df_caged[df_caged['post']==0]['periodo'].nunique()} meses")
print(f"Períodos pós: {df_caged[df_caged['post']==1]['periodo'].nunique()} meses")

# ---------------------------------------------------------------------------
# PASSO 3: Separar admissões e desligamentos
# ---------------------------------------------------------------------------
# Verificar como saldo_movimentacao está codificado
print(f"\nValores únicos de saldo_movimentacao: {df_caged['saldo_movimentacao'].unique()}")

df_admissoes = df_caged[df_caged['saldo_movimentacao'] == 1]
df_desligamentos = df_caged[df_caged['saldo_movimentacao'] == -1]

print(f"Admissões: {len(df_admissoes):,}")
print(f"Desligamentos: {len(df_desligamentos):,}")
```

```python
# Etapa 2a.3a (cont.) — Agregar por ocupação × mês

# ---------------------------------------------------------------------------
# PASSO 4: Painel de admissões por ocupação × mês
# ---------------------------------------------------------------------------
painel_admissoes = df_admissoes.groupby(['cbo_4d', 'ano', 'mes']).agg(
    admissoes=('saldo_movimentacao', 'count'),
    salario_medio_adm=('salario_mensal', 'mean'),
    salario_mediano_adm=('salario_mensal', 'median'),
    idade_media_adm=('idade', 'mean'),
    pct_mulher_adm=('sexo', lambda x: (x == 2).mean() if len(x) > 0 else np.nan),  # Ajustar codificação
    pct_superior_adm=('grau_instrucao', lambda x: (x.astype(str).isin(['9', '10', '11', '12', '13'])).mean()),
).reset_index()

# ---------------------------------------------------------------------------
# PASSO 5: Painel de desligamentos por ocupação × mês
# ---------------------------------------------------------------------------
painel_deslig = df_desligamentos.groupby(['cbo_4d', 'ano', 'mes']).agg(
    desligamentos=('saldo_movimentacao', 'count'),
    salario_medio_desl=('salario_mensal', 'mean'),
).reset_index()

# ---------------------------------------------------------------------------
# PASSO 6: Merge admissões + desligamentos → painel completo
# ---------------------------------------------------------------------------
painel = painel_admissoes.merge(
    painel_deslig,
    on=['cbo_4d', 'ano', 'mes'],
    how='outer'
).fillna(0)

# Saldo líquido
painel['saldo'] = painel['admissoes'] - painel['desligamentos']
painel['n_movimentacoes'] = painel['admissoes'] + painel['desligamentos']

# Variáveis temporais
painel['periodo'] = painel['ano'].astype(int).astype(str) + '-' + painel['mes'].astype(int).astype(str).str.zfill(2)
painel['periodo_num'] = painel['ano'].astype(int) * 100 + painel['mes'].astype(int)
painel['post'] = (painel['periodo_num'] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)

# Log de variáveis
painel['ln_admissoes'] = np.log(painel['admissoes'] + 1)
painel['ln_desligamentos'] = np.log(painel['desligamentos'] + 1)
painel['ln_salario_adm'] = np.log(painel['salario_medio_adm'].clip(lower=1))

print(f"\nPainel construído: {len(painel):,} linhas (ocupação × mês)")
print(f"Ocupações: {painel['cbo_4d'].nunique()}")
print(f"Períodos: {painel['periodo'].nunique()}")
print(f"Shape: {painel.shape}")
```

---

### 3b. Verificar painel agregado (CHECKPOINT)

**Markdown:** Verificar integridade do painel: balanceamento, cobertura temporal, distribuição de variáveis.

```python
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

# 2. Verificar se há ocupações com poucos meses
ocup_meses = painel.groupby('cbo_4d')['periodo'].nunique()
print(f"\nMeses por ocupação:")
print(f"  Min: {ocup_meses.min()}, Max: {ocup_meses.max()}, Média: {ocup_meses.mean():.1f}")
print(f"  Ocupações com < 12 meses: {(ocup_meses < 12).sum()}")
print(f"  Ocupações com todos os {n_periodos} meses: {(ocup_meses == n_periodos).sum()}")

# 3. Estatísticas descritivas
print("\nEstatísticas descritivas do painel:")
print(painel[['admissoes', 'desligamentos', 'saldo', 'salario_medio_adm']].describe())

# 4. Série temporal agregada (sanity check visual)
ts_mensal = painel.groupby('periodo_num').agg(
    total_admissoes=('admissoes', 'sum'),
    total_desligamentos=('desligamentos', 'sum'),
    salario_medio=('salario_medio_adm', 'mean'),
).reset_index()
print("\nSérie temporal (primeiros e últimos 3 meses):")
print(ts_mensal.head(3))
print("...")
print(ts_mensal.tail(3))
```

---

### 4a. Crosswalk CBO → ISCO-08

**Markdown:**

Mapear os códigos CBO 2002 (usados no CAGED) para ISCO-08 (usados no índice ILO). **Esta é a etapa metodologicamente mais delicada do pipeline** — ver `abordagens_crosswalk.md` para análise completa de 9 abordagens avaliadas.

#### Problema central

A CBO 2002 foi construída com base na **ISCO-88** (não na ISCO-08). Diferente da COD (usada na PNAD), que foi desenhada diretamente a partir da ISCO-08 e permitiu 97,9% de match na Etapa 1a, **não existe tabela oficial publicada de CBO → ISCO-08**. Um match direto naive (CBO 4d = ISCO-08 4d) é arriscado porque as versões ISCO-88 e ISCO-08 têm diferenças reais a 4 dígitos.

#### Estratégia adotada: Dual (2d principal + 4d robustez)

**Especificação PRINCIPAL — 2 dígitos (43 sub-major groups):**
- Os sub-major groups (2 dígitos) são **idênticos** entre CBO, ISCO-88 e ISCO-08
- Match perfeito, sem nenhum risco de erro
- Agrega o índice ILO a 2 dígitos (média das 427 ocupações por sub-major group)
- 43 categorias preservam variação suficiente para o DiD

**Especificação de ROBUSTEZ — 4 dígitos (via dois passos):**
- Passo 1: CBO → ISCO-88 usando Muendler & Poole (2004) — [cbo-isco-conc.csv](https://econweb.ucsd.edu/~muendler/download/brazil/cbo/cbo-isco-conc.csv)
- Passo 2: ISCO-88 → ISCO-08 usando tabela oficial ILO — [corrtab88-08.xls](http://www.ilo.org/public/english/bureau/stat/isco/docs/corrtab88-08.xls)
- Fallback hierárquico: 4d → 3d → 2d → 1d para ocupações sem match

> **Nota metodológica — Por que 2 dígitos como principal:** A escolha de 2 dígitos como especificação principal é conservadora mas metodologicamente incontestável. O match é perfeito. Se o DiD encontrar resultados significativos a 2 dígitos, e esses resultados forem consistentes com a análise a 4 dígitos (robustez), a conclusão é robusta. Se divergirem, a divergência é informativa sobre a sensibilidade à classificação.

> **Nota sobre atenuação:** Se o crosswalk a 4 dígitos introduz erro de medição no `exposure_score`, o efeito típico é **atenuação** (viés em direção a zero). Encontrar efeito significativo mesmo com erro de medição sugere que o efeito real é provavelmente maior.

> **Referências:**
> - Muendler, M.-A. & Poole, J.P. (2004). *Job Concordances for Brazil: Mapping the CBO to ISCO-88*. UC San Diego.
> - ILO (2012). *ISCO-08 Structure, definitions and correspondence tables*. Geneva.

```python
# Etapa 2a.4a — Crosswalk CBO → ISCO-08

# ===========================================================================
# PARTE A: ESPECIFICAÇÃO PRINCIPAL — 2 DÍGITOS (match perfeito)
# ===========================================================================

# ---------------------------------------------------------------------------
# PASSO 1: Carregar índice ILO
# ---------------------------------------------------------------------------
if ILO_FILE.exists():
    df_ilo = pd.read_csv(ILO_FILE)
    print(f"Índice ILO carregado: {len(df_ilo)} ocupações ISCO-08")
else:
    ilo_raw = pd.read_excel(DATA_INPUT / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx")
    df_ilo = ilo_raw.groupby('ISCO_08').agg({
        'Title': 'first',
        'mean_score_2025': 'mean',
        'SD_2025': 'mean',
        'potential25': 'first',
    }).reset_index()
    df_ilo.columns = ['isco_08', 'occupation_title', 'exposure_score', 'exposure_sd', 'exposure_gradient']
    print(f"Índice ILO processado do arquivo original: {len(df_ilo)} ocupações")

# Garantir formato string 4 dígitos
if 'isco_08' in df_ilo.columns:
    df_ilo['isco_08_str'] = df_ilo['isco_08'].astype(str).str.zfill(4)
else:
    df_ilo['isco_08_str'] = df_ilo['isco_08_str'].astype(str).str.zfill(4)

print(f"Score range: [{df_ilo['exposure_score'].min():.3f}, {df_ilo['exposure_score'].max():.3f}]")

# ---------------------------------------------------------------------------
# PASSO 2: Agregar ILO a 2 dígitos (sub-major groups)
# Cada sub-major group recebe a MÉDIA dos scores das ocupações 4d que contém
# ---------------------------------------------------------------------------
df_ilo['isco_2d'] = df_ilo['isco_08_str'].str[:2]

ilo_2d = df_ilo.groupby('isco_2d').agg(
    exposure_score_2d=('exposure_score', 'mean'),
    exposure_sd_2d=('exposure_sd', 'mean'),
    n_ocupacoes_4d=('isco_08_str', 'nunique'),
).reset_index()

print(f"\nÍndice ILO agregado a 2 dígitos: {len(ilo_2d)} sub-major groups")
print(f"\nDistribuição de exposure por sub-major group:")
print(ilo_2d.sort_values('exposure_score_2d', ascending=False).head(10).to_string(index=False))
print("...")
print(ilo_2d.sort_values('exposure_score_2d', ascending=True).head(5).to_string(index=False))

# ---------------------------------------------------------------------------
# PASSO 3: Aplicar match 2d ao painel (PRINCIPAL)
# CBO 2d = ISCO-08 2d = ISCO-88 2d (match PERFEITO)
# ---------------------------------------------------------------------------
painel['cbo_2d'] = painel['cbo_4d'].str[:2]

ilo_2d_dict = ilo_2d.set_index('isco_2d')['exposure_score_2d'].to_dict()
painel['exposure_score_2d'] = painel['cbo_2d'].map(ilo_2d_dict)

coverage_2d = painel['exposure_score_2d'].notna().mean()
print(f"\nCOBERTURA 2 DÍGITOS: {coverage_2d:.1%}")
print(f"Sub-major groups no painel: {painel['cbo_2d'].nunique()}")
print(f"Sub-major groups com score: {painel[painel['exposure_score_2d'].notna()]['cbo_2d'].nunique()}")

# Este é o exposure_score PRINCIPAL para o DiD
painel['exposure_score'] = painel['exposure_score_2d']
painel['match_level'] = '2-digit (principal)'
```

```python
# Etapa 2a.4a (cont.) — Crosswalk 4 dígitos para robustez

# ===========================================================================
# PARTE B: ROBUSTEZ — 4 DÍGITOS via CBO → ISCO-88 → ISCO-08
# ===========================================================================

import urllib.request

# ---------------------------------------------------------------------------
# PASSO 4: Baixar concordância Muendler (CBO → ISCO-88)
# ---------------------------------------------------------------------------
if not MUENDLER_FILE.exists():
    print(f"Baixando concordância Muendler de {MUENDLER_URL}...")
    urllib.request.urlretrieve(MUENDLER_URL, MUENDLER_FILE)
    print(f"Salvo em: {MUENDLER_FILE}")
else:
    print(f"Concordância Muendler já existe: {MUENDLER_FILE}")

df_muendler = pd.read_csv(MUENDLER_FILE)
print(f"Muendler: {len(df_muendler)} mapeamentos CBO → ISCO-88")
print(f"Colunas: {list(df_muendler.columns)}")

# NOTA: Ajustar nomes de colunas conforme o CSV real.
# Colunas prováveis: cboid, iscoid (ou variantes)
# Verificar e renomear se necessário:
# df_muendler.rename(columns={'cboid': 'cbo_6d', 'iscoid': 'isco88_4d'}, inplace=True)

# Extrair CBO 4d (família) e ISCO-88 4d
df_muendler['cbo_4d'] = df_muendler['cbo_6d'].astype(str).str[:4]  # Ajustar nome da coluna
df_muendler['isco88_4d'] = df_muendler['isco88_4d'].astype(str).str.zfill(4)  # Ajustar nome

# Agregar: para cada família CBO 4d, qual ISCO-88 4d mais frequente?
cbo4d_to_isco88 = df_muendler.groupby('cbo_4d')['isco88_4d'].agg(
    lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]
).reset_index()
cbo4d_to_isco88.columns = ['cbo_4d', 'isco88_4d']

print(f"\nFamílias CBO 4d mapeadas para ISCO-88: {len(cbo4d_to_isco88)}")

# ---------------------------------------------------------------------------
# PASSO 5: Baixar tabela ILO ISCO-88 → ISCO-08
# ---------------------------------------------------------------------------
if not ILO_CORRTAB_FILE.exists():
    print(f"\nBaixando tabela ILO de {ILO_CORRTAB_URL}...")
    urllib.request.urlretrieve(ILO_CORRTAB_URL, ILO_CORRTAB_FILE)
    print(f"Salvo em: {ILO_CORRTAB_FILE}")
else:
    print(f"\nTabela ILO já existe: {ILO_CORRTAB_FILE}")

df_ilo_corr = pd.read_excel(ILO_CORRTAB_FILE)
print(f"ILO corrtab: {len(df_ilo_corr)} mapeamentos ISCO-88 → ISCO-08")
print(f"Colunas: {list(df_ilo_corr.columns)}")

# NOTA: Ajustar nomes de colunas conforme o Excel real.
# Colunas prováveis: ISCO-88, ISCO-08, Title (ou variantes)
# df_ilo_corr.rename(columns={...}, inplace=True)

# ---------------------------------------------------------------------------
# PASSO 6: Merge dois passos: CBO 4d → ISCO-88 → ISCO-08
# ---------------------------------------------------------------------------
cbo_to_isco08 = cbo4d_to_isco88.merge(
    df_ilo_corr[['isco88_4d', 'isco08_4d']],  # Ajustar nomes
    on='isco88_4d',
    how='left'
)

# Para muitos-para-muitos no passo 2, pegar primeiro match
cbo_to_isco08 = cbo_to_isco08.drop_duplicates(subset='cbo_4d', keep='first')

n_matched = cbo_to_isco08['isco08_4d'].notna().sum()
print(f"\nCBO 4d com match completo CBO→ISCO-88→ISCO-08: {n_matched} / {len(cbo_to_isco08)}")

# ---------------------------------------------------------------------------
# PASSO 7: Aplicar ao painel (robustez)
# ---------------------------------------------------------------------------
# Merge com ILO exposure a 4 dígitos
ilo_4d_dict = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()

cbo_to_isco08['exposure_score_4d'] = cbo_to_isco08['isco08_4d'].map(ilo_4d_dict)

# Fallback hierárquico para scores faltantes
ilo_3d_dict = df_ilo.groupby(df_ilo['isco_08_str'].str[:3])['exposure_score'].mean().to_dict()
ilo_2d_dict_fb = df_ilo.groupby(df_ilo['isco_08_str'].str[:2])['exposure_score'].mean().to_dict()

mask_na = cbo_to_isco08['exposure_score_4d'].isna()
if mask_na.any():
    # Fallback a 3 dígitos do ISCO-08 mapeado
    cbo_to_isco08.loc[mask_na, 'exposure_score_4d'] = (
        cbo_to_isco08.loc[mask_na, 'isco08_4d'].str[:3].map(ilo_3d_dict)
    )

mask_na = cbo_to_isco08['exposure_score_4d'].isna()
if mask_na.any():
    # Fallback a 2 dígitos (= CBO 2d, que é certo)
    cbo_to_isco08.loc[mask_na, 'exposure_score_4d'] = (
        cbo_to_isco08.loc[mask_na, 'cbo_4d'].str[:2].map(ilo_2d_dict_fb)
    )

# Aplicar ao painel
cbo_score_4d = cbo_to_isco08.set_index('cbo_4d')['exposure_score_4d'].to_dict()
painel['exposure_score_4d'] = painel['cbo_4d'].map(cbo_score_4d)

coverage_4d = painel['exposure_score_4d'].notna().mean()
print(f"\nCOBERTURA 4 DÍGITOS (robustez): {coverage_4d:.1%}")
```

---

### 4b. Verificar crosswalk (CHECKPOINT)

**Markdown:** Validar qualidade do crosswalk nas DUAS especificações: principal (2 dígitos) e robustez (4 dígitos). Verificar cobertura, distribuição de scores, consistência entre especificações e sanity check por grande grupo.

```python
# Etapa 2a.4b — CHECKPOINT: Verificar crosswalk CBO → ISCO-08

print("=" * 60)
print("CHECKPOINT — Crosswalk CBO → ISCO-08 (Dual)")
print("=" * 60)

# -----------------------------------------------------------------------
# 1. Cobertura das DUAS especificações
# -----------------------------------------------------------------------
coverage_2d = painel['exposure_score_2d'].notna().mean()
coverage_4d = painel['exposure_score_4d'].notna().mean()

print(f"\n--- Cobertura ---")
print(f"  2 dígitos (PRINCIPAL): {coverage_2d:.1%}")
print(f"  4 dígitos (ROBUSTEZ):  {coverage_4d:.1%}")

if coverage_2d < 0.95:
    print(f"  ALERTA: Cobertura 2d {coverage_2d:.1%} abaixo de 95% — investigar!")
if coverage_4d < 0.80:
    print(f"  AVISO: Cobertura 4d {coverage_4d:.1%} abaixo de 80% — considerar fallback.")

# -----------------------------------------------------------------------
# 2. Ocupações sem match em cada especificação
# -----------------------------------------------------------------------
sem_match_2d = painel[painel['exposure_score_2d'].isna()]['cbo_4d'].unique()
sem_match_4d = painel[painel['exposure_score_4d'].isna()]['cbo_4d'].unique()

print(f"\n--- Ocupações sem match ---")
print(f"  Sem match 2d: {len(sem_match_2d)} CBOs 4d")
print(f"  Sem match 4d: {len(sem_match_4d)} CBOs 4d")

if len(sem_match_2d) > 0:
    print(f"\n  CBOs sem match 2d (primeiros 10):")
    for cbo in sem_match_2d[:10]:
        n = (painel['cbo_4d'] == cbo).sum()
        print(f"    CBO {cbo}: {n} linhas")

if len(sem_match_4d) > 0:
    print(f"\n  CBOs sem match 4d (primeiros 10):")
    for cbo in sem_match_4d[:10]:
        n = (painel['cbo_4d'] == cbo).sum()
        print(f"    CBO {cbo}: {n} linhas")

# -----------------------------------------------------------------------
# 3. Estatísticas dos scores (ambas especificações)
# -----------------------------------------------------------------------
print(f"\n--- Estatísticas dos scores ---")
print(f"\nexposure_score_2d (PRINCIPAL):")
print(painel['exposure_score_2d'].describe())
print(f"\nexposure_score_4d (ROBUSTEZ):")
print(painel['exposure_score_4d'].describe())

# -----------------------------------------------------------------------
# 4. Correlação entre as duas especificações
# -----------------------------------------------------------------------
mask_both = painel['exposure_score_2d'].notna() & painel['exposure_score_4d'].notna()
if mask_both.any():
    corr = painel.loc[mask_both, 'exposure_score_2d'].corr(
        painel.loc[mask_both, 'exposure_score_4d']
    )
    print(f"\n--- Correlação 2d vs 4d ---")
    print(f"  Pearson: {corr:.4f}")
    print(f"  {'Alta correlação — bom sinal de consistência.' if corr > 0.8 else 'Correlação moderada — as especificações podem dar resultados diferentes.'}")

# -----------------------------------------------------------------------
# 5. Sanity check: grande grupo CBO
# -----------------------------------------------------------------------
painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]
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
painel['grande_grupo_nome'] = painel['grande_grupo_cbo'].map(GRANDES_GRUPOS_CBO)

print("\n--- Exposição por grande grupo CBO (sanity check) ---")
print(f"{'Grande Grupo':<40} {'Score 2d':>10} {'Score 4d':>10}")
print("-" * 62)
for gg, nome in sorted(GRANDES_GRUPOS_CBO.items()):
    mask_gg = painel['grande_grupo_cbo'] == gg
    s2d = painel.loc[mask_gg, 'exposure_score_2d'].mean()
    s4d = painel.loc[mask_gg, 'exposure_score_4d'].mean()
    flag = " ⚠" if abs(s2d - s4d) > 0.1 else ""
    print(f"  {nome:<38} {s2d:>10.3f} {s4d:>10.3f}{flag}")

print("\n  ⚠ = diferença > 0.1 entre 2d e 4d (esperado em alguns grupos)")
```

---

### 5a. Definição de tratamento

**Markdown:**

Definir as variáveis de tratamento para a análise DiD. O tratamento é baseado na **exposição ocupacional à IA generativa**: ocupações com alta exposição (top 20%) vs. baixa exposição.

As variáveis de tratamento são criadas com base no `exposure_score_2d` (especificação principal, match perfeito). Variáveis equivalentes com `exposure_score_4d` são criadas para robustez.

#### Definições

| Variável | Definição | Referência |
|----------|-----------|------------|
| `alta_exp` | 1 se `exposure_score_2d >= percentil 80` | Especificação principal |
| `alta_exp_10` | 1 se `exposure_score_2d >= percentil 90` | Robustez (cutoff) |
| `alta_exp_25` | 1 se `exposure_score_2d >= percentil 75` | Robustez (cutoff) |
| `alta_exp_mediana` | 1 se `exposure_score_2d >= mediana` | Alternativa binária |
| `quintil_exp` | Quintil de exposição (Q1–Q5) | Análise por quantil |
| `alta_exp_4d` | 1 se `exposure_score_4d >= percentil 80` | Robustez (crosswalk 4d) |

> **Nota:** Os thresholds são calculados sobre a distribuição de ocupações (uma obs por CBO), não ponderada por volume de movimentações. Cada ocupação tem peso igual na definição do tratamento.

> **Alternativa — Tratamento contínuo:** Além das dummies, usaremos `exposure_score_2d` e `exposure_score_4d` diretamente como tratamento contínuo em especificações alternativas, conforme Hui et al. (2024).

> **Nota — Consistência entre especificações:** Se os resultados DiD com `alta_exp` (2d) e `alta_exp_4d` (4d) forem na mesma direção, isso reforça a robustez. Se divergirem, a especificação principal (2d) prevalece por ter match perfeito.

```python
# Etapa 2a.5a — Definição de tratamento

# ---------------------------------------------------------------------------
# PASSO 1: Calcular thresholds sobre a distribuição de ocupações (2d)
# ---------------------------------------------------------------------------
# PRINCIPAL: baseado no exposure_score_2d (match perfeito)
ocup_scores_2d = painel.groupby('cbo_4d')['exposure_score_2d'].first().dropna()

thresholds_2d = {
    'alta_exp_10': ocup_scores_2d.quantile(0.90),
    'alta_exp': ocup_scores_2d.quantile(0.80),       # PRINCIPAL
    'alta_exp_25': ocup_scores_2d.quantile(0.75),
    'alta_exp_mediana': ocup_scores_2d.quantile(0.50),
}

print("Thresholds de exposição (2d, PRINCIPAL):")
for name, val in thresholds_2d.items():
    n_above = (ocup_scores_2d >= val).sum()
    print(f"  {name}: {val:.4f} ({n_above} ocupações acima)")

# ---------------------------------------------------------------------------
# PASSO 2: Criar dummies de tratamento 2d no painel
# ---------------------------------------------------------------------------
for name, threshold in thresholds_2d.items():
    painel[name] = (painel['exposure_score_2d'] >= threshold).astype(int)

# Quintis (2d)
painel['quintil_exp'] = pd.qcut(
    painel['exposure_score_2d'].rank(method='first'),
    q=5,
    labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']
)

# ---------------------------------------------------------------------------
# PASSO 3: Criar dummies de tratamento 4d (ROBUSTEZ)
# ---------------------------------------------------------------------------
ocup_scores_4d = painel.groupby('cbo_4d')['exposure_score_4d'].first().dropna()
threshold_4d_80 = ocup_scores_4d.quantile(0.80)
painel['alta_exp_4d'] = (painel['exposure_score_4d'] >= threshold_4d_80).astype(int)

print(f"\nThreshold 4d (p80): {threshold_4d_80:.4f} ({(ocup_scores_4d >= threshold_4d_80).sum()} ocupações)")

# ---------------------------------------------------------------------------
# PASSO 4: Interação DiD
# ---------------------------------------------------------------------------
painel['did'] = painel['post'] * painel['alta_exp']
painel['did_4d'] = painel['post'] * painel['alta_exp_4d']

# Verificar distribuição
print("\nDistribuição de tratamento:")
print(f"  Alta exp 2d (top 20%): {painel['alta_exp'].mean():.1%}")
print(f"  Alta exp 4d (top 20%): {painel['alta_exp_4d'].mean():.1%}")
print(f"  Períodos pré:  {painel[painel['post']==0].shape[0]:,}")
print(f"  Períodos pós:  {painel[painel['post']==1].shape[0]:,}")

# Concordância entre 2d e 4d
if painel['alta_exp_4d'].notna().any():
    concordancia = (painel['alta_exp'] == painel['alta_exp_4d']).mean()
    print(f"\n  Concordância 2d vs 4d: {concordancia:.1%}")
    print(f"  (Alta concordância = crosswalk 4d consistente com 2d)")

# Tabela de contingência (principal)
ct = pd.crosstab(
    painel['post'].map({0: 'Pré', 1: 'Pós'}),
    painel['alta_exp'].map({0: 'Controle', 1: 'Tratamento'}),
    margins=True
)
print("\nTabela de contingência (2d, principal):")
print(ct)
```

---

### 5b. Verificar tratamento (CHECKPOINT)

```python
# Etapa 2a.5b — CHECKPOINT: Verificar definição de tratamento

print("=" * 60)
print("CHECKPOINT — Definição de Tratamento")
print("=" * 60)

# 1. Top 10 ocupações mais expostas
print("\nTop 10 ocupações mais expostas:")
top10 = painel.groupby('cbo_4d').agg(
    exposure=('exposure_score', 'first'),
    admissoes_total=('admissoes', 'sum'),
).nlargest(10, 'exposure')
for cbo, row in top10.iterrows():
    print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}")

# 2. Top 10 ocupações menos expostas
print("\n10 ocupações menos expostas:")
bot10 = painel.groupby('cbo_4d').agg(
    exposure=('exposure_score', 'first'),
    admissoes_total=('admissoes', 'sum'),
).nsmallest(10, 'exposure')
for cbo, row in bot10.iterrows():
    print(f"  CBO {cbo}: score={row['exposure']:.3f}, admissões={row['admissoes_total']:,.0f}")

# 3. Distribuição por quintil
print("\nEstatísticas por quintil de exposição:")
for q, sub in painel.groupby('quintil_exp'):
    print(f"  {q}: n={len(sub):,}, exposure_mean={sub['exposure_score'].mean():.3f}, "
          f"adm_mean={sub['admissoes'].mean():.0f}")
```

---

### 6a. Enriquecimento do painel (variáveis adicionais)

**Markdown:**

Adicionar variáveis de controle e contexto ao painel para a análise DiD.

```python
# Etapa 2a.6a — Enriquecimento do painel

# ---------------------------------------------------------------------------
# PASSO 1: Variáveis temporais para event study
# ---------------------------------------------------------------------------
# Tempo relativo ao tratamento (em meses)
ref_periodo = ANO_TRATAMENTO * 100 + MES_TRATAMENTO  # 202212
painel['tempo_relativo'] = painel['periodo_num'] - ref_periodo

# Ajuste: converter para contagem de meses (não diferença numérica simples)
# Ex: 202301 - 202212 = 89 numericamente, mas é 1 mês
def periodo_num_to_months(pn):
    return (pn // 100) * 12 + (pn % 100)

painel['meses_abs'] = painel['periodo_num'].apply(periodo_num_to_months)
ref_meses = periodo_num_to_months(ref_periodo)
painel['tempo_relativo_meses'] = painel['meses_abs'] - ref_meses

print(f"Tempo relativo: [{painel['tempo_relativo_meses'].min()}, {painel['tempo_relativo_meses'].max()}] meses")
print(f"Referência (t=0): {MES_TRATAMENTO}/{ANO_TRATAMENTO}")

# ---------------------------------------------------------------------------
# PASSO 2: Tendência temporal e sazonalidade
# ---------------------------------------------------------------------------
painel['trend'] = painel['meses_abs'] - painel['meses_abs'].min()  # Tendência linear
painel['mes_do_ano'] = painel['mes'].astype(int)  # Para dummies de mês (sazonalidade)

# ---------------------------------------------------------------------------
# PASSO 3: Normalização salarial (salário em SM do ano)
# ---------------------------------------------------------------------------
painel['sm_ano'] = painel['ano'].astype(int).map(SALARIO_MINIMO)
painel['salario_sm'] = painel['salario_medio_adm'] / painel['sm_ano']
painel['ln_salario_sm'] = np.log(painel['salario_sm'].clip(lower=0.1))

# ---------------------------------------------------------------------------
# PASSO 4: Grande grupo ocupacional
# ---------------------------------------------------------------------------
painel['grande_grupo_cbo'] = painel['cbo_4d'].str[0]

print("\nVariáveis adicionadas ao painel:")
print(f"  tempo_relativo_meses, trend, mes_do_ano, salario_sm, ln_salario_sm, grande_grupo_cbo")
print(f"  Colunas totais: {painel.shape[1]}")
```

---

### 7. Salvar dataset analítico final

**Markdown:**

Selecionar colunas finais e salvar o dataset pronto para a análise DiD (Notebook 2b).

**Saída:** `data/output/painel_caged_did_ready.parquet`

```python
# Etapa 2a.7 — Salvar dataset analítico final

# ---------------------------------------------------------------------------
# Selecionar colunas finais
# ---------------------------------------------------------------------------
cols_finais = [
    # Identificação
    'cbo_4d', 'cbo_2d', 'ano', 'mes', 'periodo', 'periodo_num',
    # Outcomes
    'admissoes', 'desligamentos', 'saldo', 'n_movimentacoes',
    'ln_admissoes', 'ln_desligamentos',
    'salario_medio_adm', 'salario_mediano_adm', 'salario_medio_desl',
    'ln_salario_adm', 'salario_sm', 'ln_salario_sm',
    # Demografia das admissões
    'idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm',
    # Exposição IA — DUAL
    'exposure_score_2d',   # PRINCIPAL (match perfeito)
    'exposure_score_4d',   # ROBUSTEZ (via Muendler + ILO)
    # Tratamento — DUAL
    'alta_exp',            # Top 20% do score 2d (PRINCIPAL)
    'alta_exp_10', 'alta_exp_25', 'alta_exp_mediana', 'quintil_exp',
    'alta_exp_4d',         # Top 20% do score 4d (ROBUSTEZ)
    # Temporal
    'post', 'did', 'did_4d', 'tempo_relativo_meses', 'trend', 'mes_do_ano',
    # Classificação
    'grande_grupo_cbo', 'grande_grupo_nome',
]

# Filtrar colunas que existem
cols_existentes = [c for c in cols_finais if c in painel.columns]
cols_faltantes = [c for c in cols_finais if c not in painel.columns]
if cols_faltantes:
    print(f"AVISO: Colunas não encontradas: {cols_faltantes}")

painel_final = painel[cols_existentes].copy()

# ---------------------------------------------------------------------------
# Remover ocupações sem score de exposição
# ---------------------------------------------------------------------------
n_antes = len(painel_final)
# Remover apenas se não tem score PRINCIPAL (2d) — o 4d pode faltar
painel_final = painel_final[painel_final['exposure_score_2d'].notna()]
n_depois = len(painel_final)
print(f"Removidas {n_antes - n_depois:,} linhas sem exposure_score_2d ({(n_antes-n_depois)/n_antes:.1%})")
n_com_4d = painel_final['exposure_score_4d'].notna().sum()
print(f"Linhas com exposure_score_4d: {n_com_4d:,} ({n_com_4d/len(painel_final):.1%})")

# ---------------------------------------------------------------------------
# Salvar
# ---------------------------------------------------------------------------
output_parquet = DATA_OUTPUT / "painel_caged_did_ready.parquet"
output_csv = DATA_OUTPUT / "painel_caged_did_ready.csv"

painel_final.to_parquet(output_parquet, index=False)
painel_final.to_csv(output_csv, index=False)

# ---------------------------------------------------------------------------
# Resumo final
# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
print("DATASET ANALÍTICO FINAL — ETAPA 2a")
print(f"{'=' * 60}")
print(f"Observações:       {len(painel_final):,}")
print(f"Ocupações (CBO 4d):{painel_final['cbo_4d'].nunique()}")
print(f"Períodos:          {painel_final['periodo'].nunique()} meses")
print(f"  Pré-tratamento:  {painel_final[painel_final['post']==0]['periodo'].nunique()}")
print(f"  Pós-tratamento:  {painel_final[painel_final['post']==1]['periodo'].nunique()}")
print(f"Cobertura 2d:      {painel_final['exposure_score_2d'].notna().mean():.1%}")
print(f"Cobertura 4d:      {painel_final['exposure_score_4d'].notna().mean():.1%}")
print(f"Tratamento 2d (20%):{painel_final['alta_exp'].mean():.1%} das obs")
print(f"Tratamento 4d (20%):{painel_final['alta_exp_4d'].mean():.1%} das obs")
print(f"Colunas:           {painel_final.shape[1]}")
print(f"\nSalvo em:")
print(f"  {output_parquet}")
print(f"  {output_csv}")
print(f"  Tamanho: {output_parquet.stat().st_size / 1e6:.1f} MB (parquet)")

painel_final.info()
```

---

## Limitações desta etapa

1. **Novo CAGED (descontinuidade 2020):** A transição para o eSocial (2020) pode afetar a comparabilidade. Mitigamos ao iniciar em 2021 (eSocial já estabilizado, sem efeitos COVID).

2. **Fluxos vs. estoques:** O CAGED mede movimentações (admissões/desligamentos), não o estoque de empregados. Quedas em admissões não significam necessariamente queda no emprego total — podem refletir menor rotatividade.

3. **Crosswalk CBO → ISCO-08 (especificação principal, 2 dígitos):** Ao agregar a 2 dígitos (43 sub-major groups), perdemos variação intragrupo. Ocupações muito diferentes dentro do mesmo sub-major group recebem o mesmo score de exposição. A especificação de robustez a 4 dígitos ajuda a avaliar se essa agregação afeta os resultados.

4. **Crosswalk CBO → ISCO-08 (robustez, 4 dígitos):** O mapeamento via dois passos (Muendler CBO→ISCO-88 + ILO ISCO-88→ISCO-08) pode introduzir erro de medição. A concordância Muendler data de 2004 e pode não cobrir CBOs criados após essa data. Erro de medição no tratamento tipicamente atenua os coeficientes (viés em direção a zero).

5. **Emprego formal apenas:** O CAGED cobre apenas o mercado formal (CLT). A informalidade (~40% da força de trabalho brasileira) não é capturada. Efeitos da IA sobre o setor informal requerem fontes alternativas (PNAD).

6. **Índice global aplicado ao Brasil:** Mesma limitação da Etapa 1 — o índice ILO foi desenvolvido com foco global.

---

## Checklist de entregáveis

- [ ] `data/raw/caged_{ano}.parquet` — Microdados CAGED por ano (2021–2025)
- [ ] `data/input/cbo-isco-conc.csv` — Concordância Muendler CBO→ISCO-88
- [ ] `data/input/corrtab88-08.xls` — Tabela ILO ISCO-88→ISCO-08
- [ ] `data/processed/ilo_exposure_clean.csv` — Índice ILO processado (reusado da Etapa 1)
- [ ] `data/output/painel_caged_did_ready.parquet` — Dataset analítico final (com scores 2d e 4d)
- [ ] `data/output/painel_caged_did_ready.csv` — Backup CSV
- [ ] Todos os CHECKPOINTs passando sem CRITICAL warnings
- [ ] Cobertura crosswalk 2d > 95% (esperado ~100%)
- [ ] Cobertura crosswalk 4d > 80%
- [ ] Correlação entre scores 2d e 4d reportada
- [ ] Sanity check por grande grupo coerente com a literatura (ambas especificações)
