# Fase 8B — Geração de tabelas e figuras

**Data:** 27 de julho de 2026
**Pré-requisito:** Gate 8A fechado. Ver `tasks/fase8a_todo.md` e
`Replication Package/V2/results/diagnostics/DIAGNOSTICO_PRETRENDS.md`.
**Insumo obrigatório:** `tasks/inventario_tabelas_figuras.md` — os 49 itens, com veredito por item.
**Escopo:** dados e artefatos. **Nenhuma alteração no texto da dissertação.**

---

## LEIA ISTO PRIMEIRO

1. **Não improvise.** Se um fato não estiver aqui, no inventário, ou não for verificável por
   comando, pare e pergunte.
2. **Não escolha especificação por p-valor.** A especificação principal congelada é
   `01_no_controls` na amostra completa, referência novembro de 2022. O Gate 8A não a mudou porque
   nenhuma alternativa passou no diagnóstico.
3. **Não edite `Replication Package/V1/`.**
4. Registre toda decisão em `Replication Package/V2/DECISIONS.md` **antes** de rodar.
5. **Nenhum artefato desta fase pode omitir o diagnóstico de tendência prévia.** As 51 células
   diagnosticadas na Fase 8A falham. Toda tabela e toda figura desta fase carrega essa informação
   ou o rótulo que a torna localizável.

### Decisões do autor, fechadas em 27 de julho de 2026

| # | Decisão |
|---|---|
| 1 | **Seção 5.3 parcial:** Tabela 5.3.1 e Figuras 5.3.1/5.3.2. O Apêndice B (3 figuras, 5 tabelas externas) fica adiado. |
| 2 | **Construir as faixas etárias PNAD/IBGE** (18–24, 25–34, 35–44, 45–54, 55–65) e manter as duas partições, como a V1. |
| 3 | **Não atualizar a Seção 3.** Permanece PNADc 2025 T3. |
| 4 | **Estrelas no p ajustado por BH** nas tabelas principais; nominal e BH lado a lado no Apêndice A. |
| 5 | **Raça:** agregado `Negra` = preta + parda na tabela principal; seis categorias no Apêndice A.3. |
| 6 | **Painel B.2 da Tabela A.1:** trocar as duas construções da V1 pelo proxy cumulativo da V2. |
| 7 | **Janela das figuras de event study: `−23 … +41`**, com a fronteira de +23 marcada. |
| 8 | **Toda figura de event study leva uma linha horizontal na média dos coeficientes pré.** |
| 9 | **Painel B.2 cortado das tabelas de heterogeneidade** (A.2 a A.6). Só a A.1 mantém um Painel B.2, com o proxy cumulativo. |
| 10 | **Tabelas 5.2.x ganham uma coluna compacta de pretrend**, além das estrelas no BH. |
| 11 | **Figura 5.2.6 nova:** forest plot dos 100 contrastes com intervalos ajustados por BH, fechando a subseção de síntese. |

### Regra de multiplicidade — registrar antes de rodar

Adicionar as faixas PNAD (25 testes) e o agregado `Negra` (5 testes) **não** infla a família
congelada de 100. Elas são partições alternativas de dimensões que já estão na família — testar
18–24 e testar 22–25 não são hipóteses independentes sobre coisas diferentes, e `Negra` é a soma de
dois grupos já contados. Incluí-las seria dupla contagem e pioraria todos os p-valores já
publicados sem ganho informacional.

- **Família A (congelada, 100 testes):** os 20 grupos originais × 5 outcomes, no estimador **DDD**.
  `PLANNED_FAMILY_SIZE` permanece 100. Nenhum número muda.
- **Família B (nova, 30 testes):** as partições alternativas — 5 faixas PNAD + 1 agregado `Negra` —
  × 5 outcomes, também no estimador **DDD**. BH próprio.
- **Família C (nova, 130 testes):** **todo** o DiD por grupo estimado, isto é, os 20 grupos
  originais **mais** os 6 das partições alternativas, × 5 outcomes. BH próprio, sobre os 130.

### Por que A e B se separam mas C não se divide

A assimetria é deliberada e tem um motivo só:

**A Família A está congelada porque já foi estimada e publicada na entrega da V2.** Acrescentar
testes a ela mudaria retroativamente p-valores que já existem em `ddd_multiplicity_results.csv`,
e o faria por conta de hipóteses que são reexpressões das que já estão lá. Por isso as partições
alternativas ganham a Família B, separada.

**A Família C não tem esse problema: ela está sendo criada agora.** Não há p-valor prévio a
proteger, então a pergunta é só qual é a família correta — e a resposta é o conjunto inteiro de
diferenças por grupo que o executor calculou e a partir do qual poderia selecionar o que destacar.
São 130.

Isso tem uma consequência prática que decide a questão: as Tabelas 5.2.1 a 5.2.5 são todas Família
C. Se raça e idade tivessem família própria, uma estrela na Tabela 5.2.2 significaria uma coisa e
na 5.2.1 outra, em tabelas visualmente idênticas e adjacentes. Uma família única faz as estrelas
das cinco tabelas quererem dizer o mesmo.

Incluir as partições redundantes torna o BH **mais conservador**, nunca menos válido. Num desenho
em que as 51 células de diagnóstico falham, errar para o lado conservador é a direção certa.

Cada tabela declara a qual família pertence e o tamanho dela.

### Convenção de saída — vale para todos os artefatos desta fase

- **Toda tabela sai em par `.csv` + `.md`.** O CSV é o artefato de auditoria; o MD é o que vai para
  a dissertação. É a convenção que a V1 já usava (69 arquivos, 39 tabelas).
- Destino: `Replication Package/V2/results/tables/` e `.../results/figures/`. Os dois diretórios
  são **novos**.
- **Nada em `outputs/` na raiz do repositório é tocado**, e nada em `Replication Package/V1/`.
  Aquelas são as árvores da V1 e permanecem congeladas. Esta fase só cria arquivos novos.
- Nomes seguem a convenção da V1: `table_5_2_1_sex.csv`, `figure_5_1_national_event_studies.png`.
- Toda tabela declara, em nota de rodapé: a fonte do número, a família de multiplicidade e o seu
  tamanho.

### Por que as figuras ficam em dois outcomes

As figuras por grupo cobrem **admissões e salário real de admissão** — não desligamentos, não
fluxo bruto, não saldo. Isso é deliberado e não deve ser "melhorado" pelo executor.

O motivo é narrativo e a V2 o reforçou. Há duas histórias possíveis no texto: a **porta de
entrada** (admissões e salário de entrada, o enquadramento do *Canaries*) e a **acomodação
silenciosa** (admissões e desligamentos caindo juntos). A decomposição de desligamentos da V2 não
apoia a segunda — demissão sem justa causa dá −0,00002 com BH p = 0,9995 — enquanto a primeira é
onde estão os dois resultados que sobrevivem: o salário nacional, estável nos quatro horizontes, e
a coorte 22–25 no salário, o único contraste da dissertação inteira cujo pretrend passa.

Desligamentos, fluxo bruto e saldo continuam nas tabelas. Só não ganham figura.

---

## Contexto: o que já existe e o que falta

A Fase 8A estimou mais do que parecia. Dos 50 itens do inventário:

| Situação | Itens |
|---|---:|
| `MANTER` — Seção 2 e 3, não dependem do CAGED | 15 |
| `NÚMERO NOVO` — dado já existe na V2, só renderizar | 19 |
| `CONSTRUIR` — precisa ser estimado | 13 |
| Adiado por decisão 1 (Apêndice B) | 3 |

**Quatro coisas precisam ser construídas do zero:** as faixas etárias PNAD, a agregação racial
`Negra`, os casos ocupacionais da Seção 5.3, e a Figura 5.2.6.

---

## Parte 1 — Construção

### T8B.1 — Faixas etárias PNAD/IBGE e agregado racial no painel DDD

**Descrição.** Acrescentar duas dimensões a `code/models/heterogeneity.py`: `age_pnad` com as
faixas 18–24, 25–34, 35–44, 45–54 e 55–65; e `race_aggregate` com o grupo `negra` = `preta` +
`parda`. As duas entram na **Família B**, não na família congelada.

Ponto de atenção: a V1 registra que a faixa 55+ na alternativa PNAD é na verdade 55–65, porque a
amostra é restrita a 18–65 anos. Preservar essa restrição e o rótulo.

**Critérios de aceitação:**
- [ ] `DECISIONS.md` registra a regra de família **antes** da primeira estimação.
- [ ] `PLANNED_FAMILY_SIZE` da família congelada permanece 100 e nenhum número de
      `ddd_multiplicity_results.csv` muda. Verificar por comparação byte a byte das colunas
      `coefficient` e `bh_adjusted_p_value` dos 100 contrastes originais.
- [ ] Novo artefato `results/diagnostics/ddd_alternative_partitions.csv` com os 30 contrastes da
      Família B, BH próprio declarado na coluna `family_id`.
- [ ] Tabela de suporte por grupo antes dos coeficientes, no mesmo formato de
      `ddd_family_support.csv`.
- [ ] A soma de admissões de `preta` e `parda` reconcilia exatamente com `negra` em todas as
      células. Falhar se não.

**Dependências:** nenhuma. **Tamanho:** M.

---

### T8B.2 — Painel dos casos ocupacionais

**Descrição.** Congelar o dicionário dos 76 códigos CBO de seis dígitos que definem os seis casos
da Seção 5.3, e construir o painel caso × faixa etária × mês com admissões e salário real médio dos
admitidos.

A V1 congelou essa seleção antes de olhar os resultados e ela não deve ser revista aqui.
**O dicionário foi localizado e verificado em 27 de julho de 2026:**

```
outputs/section5_3_occupation_cases/tables/occupation_case_dictionary.csv
SHA-256  b8d0310606c37ed32decf4cb46a9088632f9c1409c837d869a2c33d4ac8aa4b2
```

80 linhas, das quais **76 com `primary_included = True`**, sem CBO duplicado. Composição por caso:
supervisores de produção 53, desenvolvedores de software 7, auxiliares de saúde 7, estoquistas 5,
atendimento ao cliente 2, gerentes de marketing e vendas 2. O arquivo traz ainda
`variant_membership`, `mapping_confidence` e `semantic_rationale` por código.

**Reutilizar exatamente este arquivo.** Não reconstruir a seleção por conta própria: isso quebraria
o pré-registro, que é o que dá defensabilidade à Seção 5.3. Se o hash não bater, parar e perguntar.

Faixas etárias: 22–25, 26–30, 31–34, 35–40, 41–49, 50+ — as mesmas coortes Canaries.

**Duas correções obrigatórias em relação à V1:**
1. Base de normalização passa de **outubro de 2022 para novembro de 2022**, harmonizando com o
   resto da dissertação.
2. Janela-resumo passa de "janeiro a junho de 2025" para os **12 meses terminais**, jun/2025 a
   mai/2026.

Winsorização: manter a regra da V1 — P1/P99 dentro de CBO de seis dígitos e ano.

**Critérios de aceitação:**
- [ ] `data/derived/painel_casos_ocupacionais.parquet` com chave `caso × faixa × periodo_num`, sem
      duplicatas.
- [ ] Os 76 códigos reconciliam com o dicionário congelado; nenhum código em dois casos.
- [ ] Cobertura mensal reportada por caso e faixa **antes** de qualquer trajetória.
- [ ] `DECISIONS.md` registra as duas correções e o motivo.

**Dependências:** nenhuma. **Tamanho:** M.

---

### T8B.3 — Diagnósticos descritivos do período pré dos casos

**Descrição.** Para cada caso e faixa, medir cobertura, inclinação e volatilidade no período
anterior a dezembro de 2022.

**Isto não é teste de tendências paralelas** e não pode ser rotulado como tal. Os casos não têm
grupo de controle próprio; as trajetórias são descritivas. A V1 já dizia isso e o rótulo deve
sobreviver.

**Critérios de aceitação:**
- [ ] `results/mechanisms/occupation_case_preperiod_diagnostics.csv`.
- [ ] Cada linha carrega `is_causal_test = false`.
- [ ] O `.md` que acompanha afirma explicitamente a ausência de contrafactual.

**Dependências:** T8B.2. **Tamanho:** S.

---

## ✅ GATE B1 — painéis antes de qualquer coeficiente

- [ ] Os 100 contrastes da família congelada estão **numericamente intactos**.
- [ ] Família B tem 30 contrastes com suporte reportado.
- [ ] Painel de casos reconcilia com o dicionário congelado.
- [ ] Nenhuma estimativa da Parte 2 rodou antes deste gate.

---

## Parte 2 — Estimação

### T8B.4 — DiD por grupo promovido a resultado reportável

**Descrição.** A Fase 8A estimou o DiD por grupo com `interpretation = diagnostic_only`, apenas
para obter o erro padrão do efeito mínimo detectável. A decisão 4 o promove: **as Tabelas
5.2.1 a 5.2.5 são exatamente esse estimador.**

Promover significa: aplicar BH sobre a Família C (100 testes), anexar as colunas de diagnóstico já
produzidas na Fase 8A, e trocar `diagnostic_only` por `reportable`.

**Não reestimar os 100 originais.** Eles já existem em `results/diagnostics/ddd_pretrends.csv`
nas colunas `group_did_*`; reestimar arriscaria divergência sem ganho.

**Os 30 restantes são novos e precisam ser estimados aqui:** o DiD por grupo das 5 faixas PNAD e do
agregado `Negra`, que a T8B.1 acabou de construir. Mesmo estimador, mesmos efeitos fixos, mesma
inferência dos 100 originais.

O BH da Família C é calculado sobre os **130 juntos**, de uma vez, depois que todos existirem.
Nunca sobre 100 e depois sobre 30.

**Critérios de aceitação:**
- [ ] `results/models/group_did_results.csv` com **130 linhas** e as colunas coeficiente, EP, IC,
      p nominal, **p BH**, `Pretrend grupo`, `Poder grupo` (MDE a 80%), N e CBOs tratadas/controle.
- [ ] Os 100 coeficientes originais são **idênticos** aos de `ddd_pretrends.csv`. Verificar por
      igualdade exata; qualquer divergência é falha, não arredondamento.
- [ ] `family_id = C`, `family_size = 130` declarados em toda linha.
- [ ] O BH foi aplicado uma vez, sobre os 130.
- [ ] Um contador: quantos dos 130 são nominalmente significativos e quantos sobrevivem ao BH.
- [ ] Um aviso explícito no `.md` que acompanha: os p-valores BH dos 100 originais **não** são
      comparáveis aos de `ddd_multiplicity_results.csv`, porque aquele é o estimador DDD na Família
      A de 100 e este é o DiD por grupo na Família C de 130.

**Dependências:** Gate B1. **Tamanho:** M.

---

### T8B.5 — DDD e diagnósticos das partições alternativas

**Descrição.** Rodar sobre a Família B o mesmo tratamento da Fase 8A: DDD dinâmico saturado,
pretrend por grupo, pretrend do DDD, e MDE.

Usar a forma saturada já registrada: `cbo_4d^subgroup + periodo^subgroup + periodo^treatment`.

**Critérios de aceitação:**
- [ ] `results/diagnostics/ddd_alternative_partitions_pretrends.csv` com as três colunas de
      diagnóstico para os 30 contrastes.
- [ ] Comparação explícita entre a faixa PNAD 18–24 e a coorte Canaries 22–25 no mesmo quadro: são
      partições diferentes do mesmo fenômeno e o leitor precisa ver as duas.

**Dependências:** T8B.1, Gate B1. **Tamanho:** M.

---

### T8B.6 — Event studies por grupo, janela `−23 … +41`

**Descrição.** As dez figuras 5.2.x.x são event studies por grupo em dois outcomes — admissões e
salário real de admissão — para sexo, raça, idade, escolaridade e renda.

São 5 dimensões × 2 outcomes × os grupos de cada dimensão. Estimar na janela `−23 … +41`
(decisão 7), não na janela congelada de `+23`.

**Ponto crítico de execução.** A janela estendida **não** substitui a grade congelada `−23…+23` nos
artefatos existentes. Ela é a grade das figuras desta fase. Os dois convivem, e a fronteira de +23
é marcada nas figuras.

**Partições das figuras.** As figuras acompanham as **tabelas principais**, então usam as
partições principais: `Branca` e `Negra` para raça, faixas **PNAD/IBGE** para idade. As partições do
apêndice — as seis categorias raciais e as coortes Canaries — ficam só em tabela.

**Critérios de aceitação:**
- [ ] `results/models/group_event_study_coefficients.csv` com `event_time` de −23 a +41, referência
      única em −1, sem agrupamento de caudas.
- [ ] Coluna `beyond_frozen_window` marcando `event_time > 23`.
- [ ] Média dos coeficientes pré por grupo e outcome, exportada — é a linha horizontal da decisão 8.
- [ ] Todo modelo converge, ou a falha é registrada com o motivo e não silenciada.

**Dependências:** Gate B1. **Tamanho:** L — se passar de 5 arquivos ou de uma sessão, quebrar por
dimensão.

---

### T8B.7 — Trajetórias dos casos ocupacionais

**Descrição.** Trajetórias mensais normalizadas de admissões e salário real por caso e faixa
etária, base novembro de 2022 = 1.

**Critérios de aceitação:**
- [ ] `results/mechanisms/occupation_case_trajectories.csv`.
- [ ] Medida-resumo dos 12 meses terminais por caso e faixa.
- [ ] Nenhuma estrela, nenhum p-valor, nenhuma linguagem causal em qualquer artefato deste task.

**Dependências:** T8B.2, T8B.3. **Tamanho:** M.

---

## ✅ GATE B2 — estimativas antes de qualquer renderização

- [ ] Famílias A, B e C com BH declarado e tamanho declarado.
- [ ] Event studies por grupo completos na janela estendida.
- [ ] Trajetórias dos casos sem linguagem causal.
- [ ] Um contador único: quantos contrastes sobrevivem ao BH em cada família.

---

## Parte 3 — Renderização

São **32 artefatos**: 18 tabelas e 14 figuras.

### T8B.8 — Tabelas da Seção 4

`4.2.1`, `4.2.2`, `4.2.3`, `4.3.1`.

A `4.3.1` passa de 4 para 5 outcomes e o estimador principal de contagens passa a PPML. O rótulo
"Admissões (log)" deve virar algo que não engane: o coeficiente PPML é semi-elasticidade em nível,
não log-log.

**Critérios:** as quatro tabelas em `results/tables/`, com fonte declarada por célula. **Tamanho:** S.

---

### T8B.9 — Tabela 5.1 e Tabela A.1

A `5.1` traz os quatro outcomes da V1 com os números da V2. A `A.1` Painel B.1 traz os
diagnósticos — **e agora o pretrend do salário é `fail`, não `pass`**. Isso não é opcional: a
célula que a V1 reportava como `pass (p=0,932)` é `fail (p=1,6e-04)`.

Painel B.2 troca as duas construções antigas pelo proxy cumulativo (decisão 6):
`mechanisms/stock_proxy_result.csv`, +1,429 pontos, EP 1,309, p = 0,276, com a nota de que o proxy
não é estoque de emprego.

**A Tabela A.1 é a única a manter um Painel B.2** (decisão 9). Nas tabelas de heterogeneidade o
painel é cortado: o proxy cumulativo é uma estimativa nacional e não existe por grupo demográfico,
e reconstruí-lo por grupo criaria uma quarta família de multiplicidade para robustecer um outcome
que já é declaradamente complementar. O `asinh(saldo)` continua no Painel B.1 como um dos cinco
outcomes, então a medida de saldo segue representada.

**Critérios:**
- [ ] Nenhuma célula de pretrend reporta `pass` para o salário.
- [ ] O Painel B.2 declara que o proxy não observa estoque.
- [ ] Um teste em `tests/` falha se a Tabela A.1 voltar a reportar `pass` no salário.

**Tamanho:** S.

---

### T8B.10 — Tabelas 5.2.1 a 5.2.5

DiD por grupo, Família C, **estrelas no p BH** (decisão 4). Raça usa o agregado `Negra`
(decisão 5). Idade usa as faixas PNAD (decisão 2).

**Coluna de pretrend obrigatória** (decisão 10). A V1 deixava o diagnóstico só no Apêndice A. Com
as 51 células da Fase 8A falhando, um coeficiente sozinho na tabela principal convida o leitor a
ler mais do que o desenho sustenta. Cada linha leva um rótulo compacto — `pass` / `warning` /
`fail` — vindo de `ddd_pretrends.csv`, coluna `group_pretrend_pretrend_status`.

**Critérios:**
- [ ] Cinco tabelas, cada uma declarando `família C, 100 testes, BH`.
- [ ] Coluna de pretrend presente em todas as linhas, sem célula vazia. O único contraste que a
      Fase 8A não estimou — `income / high_income / desligamentos` — aparece como `not_estimated`
      com o motivo, nunca em branco.
- [ ] A faixa de renda alta carrega o rótulo de suporte `thin` (3 CBOs tratadas) na própria célula.
- [ ] Nenhuma estrela vem de p nominal.
- [ ] Par `.csv` + `.md` para cada uma.

**Tamanho:** M.

---

### T8B.11 — Tabelas A.2 a A.6

DDD com **nominal e BH lado a lado** (decisão 4), mais `Pretrend grupo`, `Pretrend DDD`,
`Poder grupo`, `N` e `CBOs trat./controle` — as colunas que a V1 tinha e a V2 tinha perdido.

`A.3` traz as seis categorias raciais, incluindo amarela e indígena, que a V1 não reportava.
`A.4` traz os dois painéis: faixas PNAD (Família B) e coortes Canaries (Família A), com o
identificador de família visível em cada um.

**Sem Painel B.2** (decisão 9). Estas tabelas têm apenas o painel de contrastes DDD.

**Critérios:**
- [ ] Cinco tabelas com as nove colunas.
- [ ] Cada painel declara sua família e o tamanho dela.
- [ ] Nenhuma delas tem Painel B.2.
- [ ] A nota de rodapé diz que resultados com pretrend falho ou poder `thin` exigem cautela — e
      **quantos dos contrastes daquela tabela estão nessa situação.**
- [ ] Par `.csv` + `.md` para cada uma.

**Tamanho:** M.

---

### T8B.12 — Tabela 5.3.1

Seleção e composição dos seis casos: 76 códigos, contagem por caso, composição de exposição.

**Critérios:**
- [ ] Tabela renderizada, com o dicionário congelado citado por caminho e hash.
- [ ] A composição por caso é reportada, não só o total: **53 dos 76 códigos estão em um único
      caso** (supervisores de produção), e 60 dos 80 mapeamentos têm confiança `medium`. Isso é
      previsível de ser questionado; reportar é mais defensável que agregar.

**Tamanho:** S.

---

### T8B.13 — Figura 5.1

Event studies nacionais e trajetórias, janela `−23 … +41`, fronteira de +23 marcada, **linha
horizontal na média dos coeficientes pré**.

Esta figura é a que mais depende da decisão 8. Sem a linha, o leitor vê a trajetória do salário
oscilando perto de zero enquanto a Tabela 5.1 diz −5%, e conclui que uma das duas está errada. A
distância vertical da linha até a trajetória pós é que lê como o DiD.

**Critérios:**
- [ ] A linha da média pré aparece e está rotulada na legenda.
- [ ] A fronteira de +23 aparece e está rotulada.
- [ ] A legenda ou a nota diz que o estimando da figura é relativo a novembro de 2022, e que a
      tabela é relativa à média do pré-período.

**Tamanho:** M.

---

### T8B.14 — Dez figuras de event study por grupo

`5.2.1.1`, `5.2.1.2`, `5.2.2.1`, `5.2.2.2`, `5.2.3.1`, `5.2.3.2`, `5.2.4.1`, `5.2.4.2`,
`5.2.5.1`, `5.2.5.2`.

Mesmas regras da Figura 5.1: janela estendida, fronteira marcada, linha da média pré.

**Critérios:** dez PNG, cada um com as três marcações. **Tamanho:** M.

---

### T8B.15 — Figuras 5.3.1 e 5.3.2

Trajetórias por caso ocupacional e idade, base novembro de 2022.

**Critérios:** duas figuras, nenhum intervalo de confiança, nota explicitando a ausência de grupo
de controle. **Tamanho:** M.

---

### T8B.16 — Figura 5.2.6: forest plot de síntese

**Descrição.** A subseção 5.2.6 é a síntese das heterogeneidades e hoje **não tem figura nenhuma**:
o leitor sai de cinco subseções com 100 números e nenhum fecho visual.

A V1 chegou a construir a figura certa e nunca a usou:
`outputs/section4_5_final/figures/figure_5_4_group_outcome_forest.png`. Esta tarefa a regera com os
números da V2.

Um forest plot com todos os contrastes e os intervalos ajustados por BH resolve três coisas ao
mesmo tempo: mostra a paisagem inteira num olhar, torna a multiplicidade visível — o leitor vê
100 contrastes e 21 sobreviventes — e dá à 5.2.6 o fecho que falta.

**Critérios de aceitação:**
- [ ] `results/figures/figure_5_2_6_group_outcome_forest.png`.
- [ ] Os **130 contrastes da Família C** — o DiD por grupo, que é o que as Tabelas 5.2.x mostram —
      agrupados por dimensão, com **intervalo ajustado por BH**, não o nominal.
- [ ] Marcação visual distinguindo os que sobrevivem ao BH dos que não.
- [ ] Suporte `limited` e `thin` marcados no próprio ponto, para que a faixa de renda alta não seja
      lida como um achado de mesma qualidade que os demais.
- [ ] Linha vertical em zero.
- [ ] O CSV que gera a figura sai junto, como em toda tabela.

**Dependências:** T8B.4, T8B.5. **Tamanho:** M.

---

---

## ✅ GATE B3 — checagem contra o inventário

- [ ] Os 32 artefatos existem.
- [ ] Cada um bate com a linha correspondente de `tasks/inventario_tabelas_figuras.md`.
- [ ] Nenhum dos 15 itens `MANTER` foi tocado.
- [ ] Os 3 itens do Apêndice B continuam adiados e estão declarados como tal.
- [ ] **Um relatório único** — `results/RENDERIZACAO_8B.md` — com uma linha por artefato: ID, fonte,
      família de multiplicidade, e se a afirmação que ele sustentava mudou.

---

## Parte 4 — Fechamento

### T8B.17 — DAG, referência assinada e testes

**Descrição.** Acrescentar os nós novos a `run_replication.py`, re-assinar a referência semântica
— que hoje **não** inclui os artefatos da Fase 8A — e cobrir os artefatos novos com testes.

**Critérios de aceitação:**
- [ ] `--section 4-5 --mode reproduce --dry-run` lista todos os nós novos.
- [ ] `results/reference/manifest.json` re-assinado, incluindo Fase 8A e Fase 8B.
- [ ] Suíte completa passa.
- [ ] `CHECKPOINTS.md` recebe o veredito do Gate B3 com evidência.

**Tamanho:** M.

---

## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| ~~O dicionário dos 76 códigos não é localizável~~ | — | **Eliminado em 27/07/2026:** arquivo localizado, 76 códigos primários confirmados, hash fixado na T8B.2 |
| Concentração: 53 dos 76 códigos em um único caso | Médio — a banca pode questionar o peso dos supervisores | Reportar a composição na Tabela 5.3.1 em vez de só o total |
| Reconstruir o painel DDD altera os 100 contrastes congelados | Alto — invalida a Fase 8A | Gate B1 verifica igualdade exata antes de seguir |
| Event study por grupo não converge em grupos pequenos | Médio | Registrar a falha com motivo; nunca substituir por OLS em silêncio |
| A janela estendida ser confundida com a grade congelada | Médio | Coluna `beyond_frozen_window` e fronteira marcada em toda figura |
| As figuras contradizerem as tabelas | Alto — foi o que motivou a decisão 8 | Critério de aceitação explícito em T8B.13 e T8B.14 |

---

## Fora de escopo

- Texto da dissertação — rodada separada.
- Apêndice B: 3 figuras e 5 tabelas externas (decisão 1).
- Seção 3 e a PNADc 2026 T1 (decisão 3).
- Qualquer mudança na especificação principal.
- Synthetic DiD, `Minimal Exposure` como controle exclusivo, extensão Anatel.
