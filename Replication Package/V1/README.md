# Pacote de replicação da dissertação

Este diretório contém o código, os insumos analíticos congelados e os
resultados de referência necessários para reproduzir as Seções 3, 4 e 5 da
dissertação. O pacote é autônomo: a execução pública não depende de arquivos
em `src/`, `data/` ou `outputs/` fora desta pasta, nem de uma exportação HTML
da dissertação.

Há dois usos:

- `reproduce` (padrão): reproduz os resultados a partir dos insumos analíticos
  compactos em `data/derived/`;
- `full`: reconstrói os dados derivados a partir dos arquivos externos em
  `data/raw/` ou, quando indicado, por consulta ao BigQuery.

Nos dois modos, os 23 quadros e as 13 figuras das Seções 4–5 são renderizados
por código a partir do backing data numérico. O pacote não contém snapshots
duplicados de tabelas ou figuras em `data/derived/`.

Toda execução é estrita. Um input ausente, um período incorreto, uma quebra de
contrato econométrico ou uma divergência em relação aos resultados de
referência encerra o processo com código de saída diferente de zero.

> **Importante sobre a Seção 3:** a base PNAD–ILO é um **corte transversal**
> da PNAD Contínua de 2025, terceiro trimestre. Ela não é um painel
> longitudinal. O painel mensal aparece somente nas Seções 4–5 e tem como
> unidade CBO de quatro dígitos × mês.

## Execução rápida

Requisitos: Python 3.11, aproximadamente 200 MB livres para a execução padrão
e um sistema operacional capaz de instalar as dependências geoespaciais
listadas em `requirements.txt`.

```bash
cd "Replication Package"
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run_replication.py
```

No Windows PowerShell, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

O comando padrão executa todas as seções no modo `reproduce` e grava os
resultados em:

```text
results/reproduced/
├── section3/
└── sections4_5/
```

Para uma verificação mais rápida, sem materializar os PNG:

```bash
python run_replication.py --skip-figures
```

## Interface pública

Existe um único ponto de entrada:

```bash
python run_replication.py [opções]
```

Opções:

| Opção | Valores | Padrão | Função |
|---|---|---|---|
| `--section` | `all`, `3`, `4-5` | `all` | Seleciona a parte da dissertação. |
| `--mode` | `reproduce`, `full` | `reproduce` | Usa insumos congelados ou reconstrói a cadeia. |
| `--raw-dir` | caminho | `data/raw` | Raiz dos arquivos externos fornecidos pelo replicador. |
| `--output-dir` | caminho | `results/reproduced` | Raiz dos resultados regenerados. |
| `--billing-project` | ID GCP | vazio | Projeto de cobrança para downloads PNAD/CAGED no BigQuery. |
| `--skip-figures` | flag | falso | Executa tabelas e validações sem renderizar PNG. |
| `--dry-run` | flag | falso | Exibe DAG e inputs, sem executar ou alterar outputs. |

Exemplos:

```bash
# Reproduzir somente a Seção 3 com os dados congelados
python run_replication.py --section 3

# Reconstruir a Seção 3 usando PNAD local
python run_replication.py --section 3 --mode full --raw-dir data/raw

# Baixar a PNAD exata via BigQuery e reconstruir a Seção 3
python run_replication.py \
  --section 3 \
  --mode full \
  --billing-project MEU_PROJECT_ID

# Reconstruir as Seções 4–5 com arquivos CAGED locais
python run_replication.py \
  --section 4-5 \
  --mode full \
  --raw-dir data/raw

# Baixar os Parquets CAGED ausentes via BigQuery
python run_replication.py \
  --section 4-5 \
  --mode full \
  --billing-project MEU_PROJECT_ID

# Conferir o DAG e o estado dos inputs sem executar
python run_replication.py --mode full --dry-run
```

O caminho informado em `--raw-dir` é uma raiz. O programa procura os arquivos
da Seção 3 em `<raw-dir>/section3/` e os das Seções 4–5 em
`<raw-dir>/sections4_5/`.

O programa pode ser chamado a partir de qualquer diretório. Todos os caminhos
internos são resolvidos a partir da localização de `run_replication.py`, não do
diretório corrente.

## Estrutura do pacote

```text
Replication Package/
├── README.md
├── run_replication.py
├── requirements.txt
├── requirements-full.txt
├── code/
│   ├── common/                    # manifests, hashes e validação compartilhada
│   ├── section3/                  # dados, tabelas, figuras e checks da Seção 3
│   └── sections4_5/
│       ├── author_pipeline/       # código autoritativo do DAG completo
│       └── *.py                   # reprodução, modelos e contratos públicos
├── data/
│   ├── raw/
│   │   ├── section3/              # preenchido pelo replicador; não distribuído
│   │   └── sections4_5/           # preenchido pelo replicador; não distribuído
│   └── derived/
│       ├── section3/              # corte analítico PNAD–ILO congelado
│       └── sections4_5/           # painel e backing data congelados
├── results/
│   └── reference/
│       ├── section3/              # artefatos canônicos publicados
│       └── sections4_5/
├── tests/
└── .gitignore
```

Durante a execução:

- `results/reproduced/` recebe os artefatos regenerados;
- `work/section3/` recebe a base reconstruída da Seção 3;
- `work/sections4_5/` recebe uma cópia isolada do DAG completo;
- os inputs em `data/derived/` permanecem somente leitura;
- `results/reproduced/` e `work/` não fazem parte do pacote distribuído.

## Instalação completa

O modo padrão não precisa acessar a internet nem o BigQuery. Para o modo
`full`, instale as dependências adicionais:

```bash
python -m pip install -r requirements-full.txt
```

As versões estão fixadas para tornar a execução auditável. Se uma plataforma
não oferecer wheel para uma dependência geoespacial, use Python 3.11 em um
ambiente conda ou instale previamente GDAL/GEOS conforme a documentação do
sistema operacional.

## Dados externos da Seção 3

### Arquivos esperados

Coloque em `data/raw/section3/`:

| Arquivo | Obrigatório | Origem e observação |
|---|---:|---|
| `pnad_2025q3.parquet` | não, se houver BigQuery | Extração exata da PNAD Contínua 2025 T3 com as 15 colunas descritas abaixo. |
| `Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx` | sim | Workbook do índice ILO 2025. |

O workbook está no [repositório dos autores do índice
ILO](https://github.com/pgmyrek/2025_GenAI_scores_ISCO08/blob/main/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx).
O pacote aceita somente a versão usada na dissertação:

```text
SHA-256:
c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a
```

O arquivo precisa conter:

```text
ISCO_08
Title
mean_score_2025
SD_2025
potential25
```

O Parquet local da PNAD precisa conter exclusivamente o período 2025 T3 e as
seguintes colunas:

```text
ano, trimestre, sigla_uf, sexo, idade, raca_cor, nivel_instrucao,
cod_ocupacao, grupamento_atividade, posicao_ocupacao,
rendimento_habitual, rendimento_efetivo, horas_habituais,
horas_efetivas, peso
```

Os nomes correspondem às aliases produzidas pela consulta documentada em
`code/section3/build_data.py`. A fonte primária é a [PNAD Contínua
Trimestral do IBGE](https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/17270-pnad-continua.html);
o pacote consulta a cópia tratada
`basedosdados.br_ibge_pnadc.microdados` quando `--billing-project` é
informado. A consulta fixa `ano = 2025` e `trimestre = 3`; não existe fallback
para outro trimestre.

### Autenticação no BigQuery

Instale o Google Cloud CLI e crie credenciais de aplicação:

```bash
gcloud auth application-default login
gcloud config set project MEU_PROJECT_ID
```

Em seguida:

```bash
python run_replication.py \
  --section 3 \
  --mode full \
  --billing-project MEU_PROJECT_ID
```

O usuário é responsável por habilitar faturamento e as APIs necessárias. A
consulta pode gerar cobrança no projeto informado. O download é salvo como
`data/raw/section3/pnad_2025q3.parquet` para reutilização.

## Construção da base da Seção 3

O código relevante está separado por responsabilidade:

- `code/section3/build_data.py`: leitura, filtros, crosswalk e Parquet;
- `code/section3/data.py`: seleções e estatísticas ponderadas;
- `code/section3/tables.py`: cinco quadros;
- `code/section3/figures.py`: dez figuras;
- `code/section3/validation.py`: invariantes da amostra;
- `code/section3/pipeline.py`: orquestração e comparação.

A construção segue esta ordem:

1. valida que toda observação pertence a 2025 T3;
2. valida as colunas PNAD e a versão do workbook ILO;
3. normaliza COD e CNAE, converte variáveis numéricas e remove chaves críticas
   ausentes;
4. restringe a amostra a pessoas ocupadas de 18 a 65 anos e exclui códigos
   ocupacionais inválidos;
5. cria sexo, raça/cor agregada, faixa etária, formalidade, renda, região e
   setor;
6. winsoriza rendimento habitual nos percentis ponderados P1 e P99;
7. aplica o crosswalk COD–ISCO-08 hierárquico em 4, 3, 2 e 1 dígito;
8. registra cobertura por observações e população ponderada em cada nível;
9. normaliza o código setorial antes da classificação e preserva a coluna
   legada em `setor_agregado_original` somente para auditoria;
10. grava `pnad_ilo_merged.parquet` com compressão Zstandard e
    `data_build_diagnostics.csv`.

O score em um fallback hierárquico é a média dos scores disponíveis no nível
correspondente. Somente a correspondência exata de quatro dígitos recebe a
categoria ILO original; os fallbacks permanecem identificados como
`Sem classificação`. Os pesos da PNAD são usados nas estatísticas de
população e distribuição.

## Dados externos das Seções 4–5

### Arquivos obrigatórios

Coloque em `data/raw/sections4_5/`:

| Arquivo | Origem/função |
|---|---|
| `caged_2021.parquet` | Movimentações do Novo CAGED em 2021. |
| `caged_2022.parquet` | Movimentações do Novo CAGED em 2022. |
| `caged_2023.parquet` | Movimentações do Novo CAGED em 2023. |
| `caged_2024.parquet` | Movimentações do Novo CAGED em 2024. |
| `caged_2025.parquet` | Movimentações de janeiro a junho de 2025; meses posteriores são descartados. |
| `cbo-isco-conc.csv` | Concordância CBO 1994–ISCO-88 de Muendler e Poole. |
| `isco_08_to_88.xlsx` | Tabela oficial ISCO-08–ISCO-88. |
| `isco_08_structure.xlsx` | Estrutura e definições ISCO-08. |

Os cinco Parquets CAGED não precisam estar presentes quando
`--billing-project` é informado: o DAG consulta
`basedosdados.br_me_caged.microdados_movimentacao` e baixa somente as colunas
usadas. Os arquivos locais são preferidos e evitam nova cobrança. A fonte
primária também pode ser obtida na página de [microdados RAIS e CAGED do
MTE](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged).

Cada Parquet CAGED deve conter:

```text
ano, mes, sigla_uf, id_municipio, cbo_2002, categoria,
tipo_movimentacao, saldo_movimentacao, salario_mensal,
grau_instrucao, idade, sexo, raca_cor, cnae_2_secao,
cnae_2_subclasse, tamanho_estabelecimento_janeiro
```

As correspondências são obtidas em:

- [Muendler e Poole — `cbo-isco-conc.csv`](https://econweb.ucsd.edu/~muendler/download/brazil/cbo/cbo-isco-conc.csv);
- [portal oficial ISCO-08 da ILO](https://isco.ilo.org/en/isco-08/), para a
  estrutura e a correspondência ISCO-08–ISCO-88;
- [tábua oficial CBO 2002–CBO 1994–CIUO-88 do
  MTE](https://cbo.mte.gov.br/cbosite/pages/tabua/FiltroConversao_CBO2002_CBO94_CIUO88.jsf).

### Caches opcionais do crosswalk

O DAG consulta a tábua online do MTE e reconstrói os dois arquivos abaixo.
Para fixar uma versão anterior ou evitar centenas de requisições, eles podem
ser colocados em `data/raw/sections4_5/`:

```text
mte_cbo2002_cbo94_ciuo88_by_family.csv
caged_mte_bridge_full.csv
```

Esses arquivos são caches derivados, não inputs brutos obrigatórios. O
`--dry-run` os mostra como `FOUND` ou `REBUILD`.

## DAG completo das Seções 4–5

O modo `full` executa o código em
`code/sections4_5/author_pipeline/` dentro de uma cópia isolada em
`work/sections4_5/`. Nenhuma etapa escreve em `data/derived/`.

```text
01_panel
  CAGED individual → agregação CBO4 × mês
      ↓
02_crosswalk_treatment
  CBO 2002 → CBO 1994 → ISCO-88 → ISCO-08 → ILO
      ↓
03_analysis_panel
  painel analítico, controles e salários reais
      ↓
04_models
  DiD, DDD, event studies e robustez
      ↓
05_extensions
  sexo, raça/cor, renda, idade e casos ocupacionais
      ↓
06_artifacts
  backing data → quadros e figuras → validação final
```

Contratos centrais:

- janela fixa de janeiro de 2021 a junho de 2025;
- primeiro mês pós-tratamento: dezembro de 2022;
- crosswalk `mte_official_no_numeric_fallback`;
- tratamento principal: Gradientes ILO 1–4;
- controle principal: `Not Exposed`;
- `Minimal Exposure` e CBOs sem score são excluídos da estimação principal;
- efeitos fixos de CBO4 e mês;
- erros-padrão CRV1 agrupados por CBO4;
- DDD exige a interação tripla e todas as interações de ordem inferior;
- cada extensão escreve apenas em seu diretório de trabalho.

O modo completo é custoso. Antes de iniciá-lo:

```bash
python run_replication.py --section 4-5 --mode full --dry-run
```

## Outputs e navegação

Cada seção em `results/reference/` e `results/reproduced/` segue:

```text
section*/
├── INDEX.md
├── artifact_manifest.csv
├── run_manifest.json             # apenas em reproduced
├── reference_manifest.json       # apenas em reference
├── tables/
├── figures/
├── backing_data/
└── validation/
```

- `INDEX.md`: índice humano com links para cada quadro e figura;
- `artifact_manifest.csv`: seção, artefato, função produtora, input,
  referência, reprodução, hashes e status;
- `tables/*.csv`: versão para conferência computacional;
- `tables/*.md`: versão legível da mesma tabela;
- `figures/*.png`: figura canônica ou regenerada;
- `backing_data/`: diagnósticos e resultados em precisão completa usados por
  artefatos ou checks;
- `validation/validation_checks.csv`: relatório legível por máquina;
- `validation/validation_checks.md`: o mesmo relatório para inspeção humana;
- `run_manifest.json`: versões de software e SHA-256 de código, inputs e
  outputs, sempre com caminhos relativos.
- `reference_manifest.json`: snapshot equivalente da árvore canônica, com
  hashes calculados sobre os arquivos de referência.

Comece por:

```text
results/reproduced/section3/INDEX.md
results/reproduced/sections4_5/INDEX.md
```

## Como a comparação funciona

Os resultados publicados permanecem imutáveis em `results/reference/`. Cada
execução grava uma nova árvore em `results/reproduced/` ou no caminho escolhido
com `--output-dir`.

Critérios:

- CSV e Markdown: bytes exatamente iguais;
- categorias, textos, estruturas e N: igualdade exata;
- quatro modelos nacionais: mesma amostra e diferença máxima de `1e-12` para
  coeficiente, erro-padrão e valor-p;
- PNG: dimensões idênticas e RMS perceptual em miniatura de no máximo `5.0`;
- inputs, código e artefatos: SHA-256 no manifest.

Status:

- `PASS`: o critério foi satisfeito;
- `WARN`: aviso informativo que não invalida a replicação; reservado para
  condições não numéricas explicitamente não bloqueantes;
- `FAIL`: divergência ou contrato quebrado; a execução termina com erro.

Não interprete `PASS` como nova evidência substantiva. Ele significa que o
artefato foi reproduzido sob o contrato registrado.

## Resultados esperados

### Seção 3

| Métrica | Valor esperado |
|---|---:|
| Período | PNAD 2025 T3 |
| Observações | 207.901 |
| Unidades da Federação | 27 |
| População ponderada | 97.783.776,1804 |
| Colunas analíticas | 32 |
| Match exato de 4 dígitos | 203.617 observações |
| Fallback de 3 dígitos | 2.613 observações |
| Sem score | 1.671 observações |
| Quadros | 5 |
| Figuras | 10 |

### Seções 4–5

| Métrica | Valor esperado |
|---|---:|
| Observações CBO4–mês | 23.319 |
| CBOs no painel | 436 |
| Meses | 54 |
| Janela | 2021-01 a 2025-06 |
| Universo classificado | 629 CBO4 |
| Tratados | 75 CBO4 |
| Controles | 266 CBO4 |
| Excluídos | 288 CBO4 |
| Amostra dos quatro modelos principais | 18.307 observações, 341 CBO4 |
| Quadros | 23 |
| Figuras | 13 |

## Testes

Da raiz deste pacote:

```bash
PYTHONDONTWRITEBYTECODE=1 \
python -m unittest discover -s tests -v
```

A suíte verifica:

- layout autônomo e defaults da CLI;
- DAG completo e preflight dos inputs;
- rejeição de qualquer PNAD diferente de 2025 T3;
- crosswalk hierárquico e normalização setorial;
- dimensões do painel e classificação de tratamento;
- reprodução das tabelas;
- reestimação independente dos quatro modelos principais;
- ausência de caminhos absolutos nos manifests.

Para testar a independência em uma cópia:

```bash
tmpdir="$(mktemp -d)"
cp -R . "$tmpdir/Replication Package"
cd /tmp
PYTHONDONTWRITEBYTECODE=1 \
python "$tmpdir/Replication Package/run_replication.py" --skip-figures
```

## Tempo e espaço aproximados

Os números variam conforme CPU, disco, rede e cache:

| Execução | Tempo típico | Espaço adicional |
|---|---:|---:|
| `reproduce`, todas as seções | 60–90 segundos | 100–200 MB |
| `reproduce --skip-figures` | 20–40 segundos | 50–100 MB |
| Seção 3 `full` com Parquet local | 15–45 segundos | 10–50 MB |
| Seção 3 `full` via BigQuery | minutos, conforme rede | 0,5–1 GB |
| Seções 4–5 `full` | dezenas de minutos a algumas horas | 5–10 GB livres |

Os Parquets CAGED usados na dissertação ocupam aproximadamente 1,9 GB. Eles
não são distribuídos.

## Erros comuns

### `Missing ... See README.md`

Execute:

```bash
python run_replication.py --mode full --dry-run
```

Arquivos `MISSING` são obrigatórios. CAGED marcado como `BIGQUERY` será
baixado. Cache marcado como `REBUILD` será reconstruído.

### `PNAD input must contain exactly 2025 Q3`

O Parquet contém outro período ou mistura trimestres. Refaça a extração com
`ano = 2025 AND trimestre = 3`. O programa não seleciona silenciosamente outro
trimestre.

### `ILO workbook SHA-256 differs`

O workbook foi atualizado, renomeado internamente ou corrompido. Use a versão
indicada neste README. Uma nova versão exige uma decisão metodológica e não é
uma replicação exata.

### Erro de autenticação ou cobrança no BigQuery

Confirme:

```bash
gcloud auth application-default login
gcloud auth application-default print-access-token
```

Verifique também faturamento, permissões de consulta e
`--billing-project`.

### Erro na consulta da tábua MTE

A página oficial é uma aplicação JSF e pode ficar temporariamente indisponível.
Tente novamente ou forneça os dois caches opcionais do crosswalk.

### `Refusing to replace ... without a valid package run manifest`

O caminho de output ou de trabalho contém arquivos que não foram criados pelo
pacote. Escolha outro `--output-dir` ou mova esses arquivos manualmente. Essa
proteção valida o schema de `run_manifest.json` antes de substituir qualquer
execução anterior e evita apagar dados do usuário.

### Figuras diferentes, mas tabelas iguais

Confira a versão de Python e as versões fixadas em `requirements.txt`.
Diferenças de fonte, backend gráfico ou biblioteca geoespacial podem afetar
antialiasing. O manifest registra o ambiente e o relatório informa dimensões e
RMS observados.

## Escopo e limitações

- A Seção 3 é descritiva e transversal; não identifica efeitos causais.
- O CAGED registra fluxos do mercado formal, não todo o emprego brasileiro.
- O índice ILO mede exposição ocupacional potencial, não adoção observada de
  IA por trabalhador ou empresa.
- A janela CAGED é congelada em junho de 2025. Revisões posteriores da fonte
  podem alterar uma reconstrução completa.
- O crosswalk online do MTE pode mudar; use os caches opcionais para auditar
  uma versão específica.
- Os microdados brutos não são redistribuídos. O replicador deve observar os
  termos de uso e citação de IBGE, MTE, ILO, Base dos Dados e autores das
  concordâncias.
- Relatórios editoriais e recomendações de alteração da dissertação não fazem
  parte deste pacote. Somente verificações numéricas de replicação são
  preservadas.

## Referências de dados

- Gmyrek et al. (2025), *Generative AI and Jobs: A Refined Global Index of
  Occupational Exposure*, ILO Working Paper 140, e
  [dados dos autores](https://github.com/pgmyrek/2025_GenAI_scores_ISCO08).
- [IBGE — PNAD Contínua](https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/17270-pnad-continua.html).
- [Base dos Dados — documentação](https://basedosdados.org/docs/home).
- [MTE — microdados RAIS e CAGED](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/acoes-e-programas/programas-projetos-acoes-obras-e-atividades/estatisticas-trabalho/microdados-rais-e-caged).
- [ILO — classificação ISCO-08](https://isco.ilo.org/en/isco-08/).
- Muendler, M.-A. e Poole, J. (2004), concordância ocupacional
  CBO–ISCO-88.
