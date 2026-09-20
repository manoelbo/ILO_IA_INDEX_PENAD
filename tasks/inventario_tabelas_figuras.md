# Inventário de tabelas e figuras — o que a Fase 8B precisa gerar

**Data:** 27 de julho de 2026
**Fonte do texto:** `Dissertação/Dissertação de Mestrado 33fcc8ca461080cb8412e25e5b5b6ba3.md` (1.043 linhas)
**Fonte dos números novos:** `Replication Package/V2/results/`

**Decisões do autor fechadas em 27/07/2026** — ver o rodapé.

Este documento **não altera o texto**. Ele lista cada tabela e figura, diz de onde vem o número
novo, se a afirmação que ela sustenta ainda se sustenta, e o que fazer com ela.

**Total: 51 itens** — 24 tabelas e 27 figuras, incluindo a Figura 5.2.6 e a Tabela 5.1.1,
acrescentadas em 27/07.

Vereditos usados:

| Código | Significa |
|---|---|
| `MANTER` | Não depende do CAGED/V2. Regerar igual ou nem isso. |
| `NÚMERO NOVO` | Mesma tabela, número diferente. Gerar. |
| `CONSTRUIR` | O corte não existe na V2. Precisa ser estimado do zero. |
| `AFIRMAÇÃO CAIU` | O número existe, mas a frase que ele sustentava não se sustenta mais. |
| `DECIDIR` | Depende de uma escolha sua antes de gerar. |

---

## Bloco A — Seção 2 e 3: não tocados pela V2 (14 itens)

A Seção 3 é descritiva sobre a **PNAD Contínua 2025 T3**, não sobre o CAGED. A V2 não mexeu nessa
base. Nada aqui muda.

| Item | O que é | Veredito |
|---|---|---|
| Tabela 2.1 | Comparação dos índices de exposição | `MANTER` — conceitual, sem dado |
| Tabela 3.1 | Ficha técnica da base PNADc | `MANTER` |
| Tabela 3.2 | População ocupada por gradiente | `MANTER` |
| Tabela 3.3 | Top 5 ocupações em alta exposição | `MANTER` |
| Tabela 3.4 | Exposição por setor CNAE-Domiciliar | `MANTER` |
| Figuras 3.1 a 3.10 | Distribuição da exposição; por estado, sexo, raça, idade, escolaridade, renda, formalidade | `MANTER` — 10 figuras |

**Nota, não é ação:** a PNADc já tem 2026 T1 disponível. Atualizar a Seção 3 mudaria 14 itens e não
está no escopo que você definiu. Fica registrado como opção, não como pendência.

---

## Bloco B — Seção 4: definições do painel (4 itens)

| Item | O que é | Fonte V2 | Veredito |
|---|---|---|---|
| Tabela 4.2.1 | Escopo do painel ocupação-mês | `reconciliation/painel_nacional_support.json` | `NÚMERO NOVO` — janela vai a mai/2026, 65 meses, 22.049 células principais |
| Tabela 4.2.2 | Classificação das CBOs e grupos | `treatment/treatment_variant_comparison.csv` | `NÚMERO NOVO` — V-A idêntica à V1 (75 tratadas / 266 controle), mas agora há 3 variantes pré-registradas para reportar |
| Tabela 4.2.3 | Cobertura do painel por grupo | `reconciliation/completude_por_tratamento.csv` | `NÚMERO NOVO` |
| Tabela 4.3.1 | Definição dos outcomes | contrato da V2 | `NÚMERO NOVO` — **passa de 4 para 5 outcomes** (entra fluxo bruto `n_movimentacoes`) e o estimador principal de contagens passa a PPML |

---

## Bloco C — Seção 5.1 e Apêndice A.1: o resultado nacional (3 itens)

| Item | O que é | Fonte V2 | Mudou? | Veredito |
|---|---|---|---|---|
| Tabela 5.1 | Resultados médios nacionais | `models/specification_ladder.csv` passo `01_no_controls` | **Sim, muito** | `NÚMERO NOVO` + `AFIRMAÇÃO CAIU` |
| Tabela A.1 Painel B.1 | Diagnósticos do modelo nacional | `diagnostics/pretrend_diagnostics.csv` | **Sim** | `NÚMERO NOVO` + `AFIRMAÇÃO CAIU` |
| Tabela A.1 Painel B.2 | Robustez da construção do saldo | **não existe na V2** | — | `DECIDIR` |
| Figura 5.1 | Event studies e trajetórias nacionais | `models/event_study_coefficients.csv` | **Sim** | `NÚMERO NOVO` |
| **Tabela 5.1.1 (nova)** | Nível 1 vs nível 2 — controle setorial | `models/sector_level1_vs_level2.csv`, `models/sector_fixed_effect_ladder.csv`, `diagnostics/pretrend_level2.csv` | — | `CONSTRUIR` |

**Lacuna encontrada em 27/07, depois do Gate B3.** O nível 2 — efeitos fixos de `CBO4 × seção CNAE`
e `seção CNAE × mês` — está declarado `co_principal_sector` no contrato congelado da V2 e foi
diagnosticado na Fase 8A, mas **não aparece em nenhuma das 18 tabelas renderizadas**. O inventário
original percorreu as tabelas que o texto atual tem, e o texto não tem tabela setorial porque esse
exercício não existia na V1.

É lacuna material: controlando por setor, as admissões passam de −0,0538 (p = 0,164) para
−0,0751 (p = 0,036) e rejeitam a 5%; o salário encolhe de −0,0507 para −0,0356, ou seja, cerca de
30% do diferencial salarial é entre setores e não entre ocupações dentro do setor.

### O que exatamente mudou

| Outcome | V1 (Tabela 5.1) | V2 principal | Comentário |
|---|---:|---:|---|
| Admissões | −0,0309 (0,0263) | **−0,0538** (0,0386) | mais negativo, continua não significativo |
| Desligamentos | −0,0417 (0,0254) | **−0,0420** (0,0347) | praticamente igual |
| Salário real de admissão | −0,0207 (0,0140) | **−0,0507** (0,0103) | **de p=0,140 para p=0,000001** |
| Saldo (asinh) | −0,6597 (0,3773) | **−0,5513** (0,3783) | menor em módulo |
| Fluxo bruto | — | **−0,0481** (0,0353) | outcome novo |

### As afirmações que caíram

1. **Tabela A.1 certifica que o pretrend do salário passa: `pass (p=0,932)`.** Na V2 ele falha:
   teste conjunto p = 1,6e-04, com 11 dos 22 leads individualmente significativos. Isso derruba a
   frase da introdução (*"O sinal mais consistente está no salário de entrada"*) enquanto apoio de
   credibilidade — o salário deixa de ser o outcome bem-comportado.
2. **"nenhum é estatisticamente significativo"** (linha 440) fica falso: o salário rejeita a 5%
   com folga.
3. **"os testes de tendências paralelas são rejeitados"** aparece qualificado como *"para os
   fluxos"* (linhas 5 e 23). Passa a valer para os cinco outcomes.
4. **"As reduções aproximadas são de 3,0% nas admissões, 4,1% nos desligamentos e 2,0% no salário"**
   → 5,4%, 4,2% e 5,1%.

### Decisão pendente no Painel B.2

A V1 reportava duas construções alternativas do saldo — `saldo/admissões pré` e
`saldo/fluxo total`. **Nenhuma das duas existe na V2.** A V2 tem um proxy diferente:
`mechanisms/stock_proxy_result.csv`, o índice cumulativo `100 + 100 × Δ saldo acumulado / fluxo
bruto pré`, que dá +1,429 pontos (EP 1,309, p = 0,276).

Opções: (a) reestimar as duas construções da V1 na V2; (b) trocar o Painel B.2 pelo proxy da V2;
(c) cortar o painel. Recomendo **(b)** — o proxy da V2 tem normalização declarada e evita a
divisão pelo saldo de janeiro, que era o problema das construções antigas.

---

## Bloco D — Seção 5.2 e Apêndice A.2–A.6: as heterogeneidades (17 itens)

Aqui está a maior parte do trabalho e a maior parte do risco. **Boa notícia:** a Fase 8A já
estimou quase tudo. Os 100 contrastes DDD com ajuste BH estão em
`diagnostics/ddd_multiplicity_results.csv`, e as três colunas de diagnóstico que a V1 tinha e a V2
tinha perdido — `Pretrend grupo`, `Pretrend DDD`, `Poder grupo` — estão em
`diagnostics/ddd_pretrends.csv`, junto com o DiD por grupo.

**Contexto para ler tudo abaixo:** dos 100 contrastes, 34 são nominalmente significativos e **21
sobrevivem ao ajuste BH**. A V1 não tinha ajuste nenhum.

### 5.2.1 Sexo — Tabela 5.2.1, Tabela A.2, Figuras 5.2.1.1 e 5.2.1.2

| | |
|---|---|
| Fonte | `ddd_multiplicity_results.csv` + `ddd_pretrends.csv`, dimensão `sex` |
| Veredito | `NÚMERO NOVO` + **`AFIRMAÇÃO CAIU`** |

**Esta é a maior baixa do inventário.** A afirmação central da subseção — e do resumo — é que as
admissões femininas caem mais.

| | V1 | V2 |
|---|---:|---:|
| DDD admissões (homens−mulheres) | **+0,0446** (p = 0,018) | **+0,0116** (p = 0,803, BH 0,907) |
| DDD salário | −0,0209 (p = 0,205) | −0,0022 (p = 0,824, BH 0,907) |

O diferencial de gênero nas admissões **desaparece**. O DiD dentro de cada grupo continua negativo
e parecido nos dois: homens −0,0779 (p = 0,0045), mulheres −0,0724 (p = 0,119). Ou seja: ambos
caem, mas não há assimetria detectável entre eles.

O único contraste de sexo que sobrevive ao BH é o saldo (asinh): +0,799, BH p = 0,0026 — e o saldo
é outcome complementar com pretrend falho.

Frases afetadas: resumo (linha 5), introdução (linha 23), toda a síntese da 5.2.1 (linha 506) e a
implicação de política sobre convergência entre os sexos.

### 5.2.2 Raça/cor — Tabela 5.2.2, Tabela A.3, Figuras 5.2.2.1 e 5.2.2.2

| | |
|---|---|
| Fonte | dimensão `race_color` |
| Veredito | `CONSTRUIR` (agregação) + `NÚMERO NOVO` |

**Problema de compatibilidade:** a dissertação compara **Branca vs. Negra**, onde `Negra` agrega
pretos e pardos. A V2 tem seis categorias separadas — `white`, `black`, `pardo`, `yellow`,
`indigenous`, `unknown` — e **não tem o agregado**. Precisa ser construído.

A direção da V1 se sustenta e agora fica mais forte:

| Grupo | DDD desligamentos | BH p |
|---|---:|---:|
| Branca | +0,0651 | 0,000049 |
| Parda | −0,0886 | 0,018 |
| Preta | +0,0445 | 0,341 |

Brancos se desligam relativamente mais, pardos relativamente menos — consistente com a leitura da
V1 (*"redução dos desligamentos cerca de 3,2% maior entre trabalhadores negros"*), e agora
sobrevive ao ajuste de multiplicidade. Mas o efeito está concentrado em **pardos**, não em pretos.
Ao agregar, isso fica escondido; vale reportar os dois.

**Resultado novo que a V1 não tinha:** `race_yellow` tem os maiores coeficientes de toda a família
— admissões −0,277 e desligamentos −0,218, ambos BH p < 1e-4, com suporte adequado. A V1 não
reportava essa categoria.

### 5.2.3 Idade — Tabela 5.2.3, Tabela A.4 (dois painéis), Figuras 5.2.3.1 e 5.2.3.2

| | |
|---|---|
| Veredito | **`CONSTRUIR`** para a tabela principal, `NÚMERO NOVO` para o painel Canaries |

**A Tabela 5.2.3 usa faixas PNAD/IBGE — 18–24, 25–34, 35–44, 45–54, 55–65 — e a V2 não tem
nenhuma delas.** A V2 só tem as coortes Canaries (22–25, 26–30, 31–34, 35–40, 41–49, 50+), que
cobrem o segundo painel da A.4. As faixas PNAD precisam ser construídas do zero no painel DDD.

Nas coortes que existem, o resultado é forte mas não é o que se esperaria:

| Coorte | DDD admissões | BH p |
|---|---:|---:|
| 22–25 | −0,0189 | 0,652 |
| 41–49 | **+0,0841** | **0,0043** |

Ou seja: **não é que os jovens sejam atingidos de forma diferencial — é que os de 41 a 49 são
poupados.** A frase do resumo sobre "jovens" precisa ser reescrita nesses termos.

Ao mesmo tempo, é na coorte 22–25 que o **DiD por grupo passa no pretrend** (p conjunto = 0,585)
com salário −0,0517 (p = 1e-06). É o único lugar da dissertação inteira onde a identificação
sobrevive. Vale um tratamento à parte.

### 5.2.4 Escolaridade — Tabela 5.2.4, Tabela A.5, Figuras 5.2.4.1 e 5.2.4.2

| | |
|---|---|
| Fonte | dimensão `education` — grupos batem com a V1 |
| Veredito | `NÚMERO NOVO` + `AFIRMAÇÃO ENFRAQUECIDA` |

A direção se mantém: superior tem DDD de admissões −0,111 contra +0,123 do fundamental. Mas o
nominal p = 0,0145 vira **BH p = 0,055** — passa raspando do outro lado da linha. O fluxo bruto do
superior sobrevive (BH p = 0,048) e o saldo também (BH p = 0,015).

A frase *"a retração das admissões é mais forte entre... trabalhadores com ensino superior"*
continua verdadeira em direção e magnitude, mas não em significância ajustada. Precisa da
qualificação.

### 5.2.5 Faixa salarial ocupacional — Tabela 5.2.5, Tabela A.6, Figuras 5.2.5.1 e 5.2.5.2

| | |
|---|---|
| Fonte | dimensão `income` — grupos batem com a V1 |
| Veredito | `NÚMERO NOVO` + **alerta de suporte** |

| Grupo | CBOs tratadas / controle | Suporte |
|---|---:|---|
| Até 2 SM | 46 / 227 | adequado |
| 2 a 5 SM | 26 / 32 | **limitado** |
| Mais de 5 SM | **3 / 6** | **fino** |

A V1 afirmava redução dos desligamentos concentrada na renda intermediária. Na V2, o DDD de
desligamentos da faixa média é −0,054 com p = 0,55 — **não se sustenta**.

Aparece um resultado novo: salário da faixa alta, DDD +0,064, **BH p = 0,043** — ocupações de
renda alta têm queda salarial menor. Mas isso repousa em **3 CBOs tratadas**. Não deve virar
achado de texto; se entrar, entra com o suporte declarado ao lado.

### Subseção 5.2.6 — síntese das heterogeneidades

Não é tabela numerada no texto. Depende inteiramente do acima. `AFIRMAÇÃO CAIU` em pelo menos dois
dos cinco eixos.

**Item novo — Figura 5.2.6 (forest plot).** A subseção não tem figura nenhuma hoje: o leitor sai de
cinco subseções com 100 números e nenhum fecho visual. A V1 chegou a construir a figura certa e
nunca a usou — `outputs/section4_5_final/figures/figure_5_4_group_outcome_forest.png`, gerada em
19/07/2026, zero menções no texto.

Veredito: `CONSTRUIR`. Um forest plot dos 100 contrastes com **intervalos ajustados por BH** torna
a multiplicidade visível — 100 contrastes, 21 sobreviventes — e dá à 5.2.6 o fecho que falta.

---

## Bloco E — Seção 5.3 e Apêndice B: casos ocupacionais (11 itens)

| Item | O que é | Veredito |
|---|---|---|
| Tabela 5.3.1 | Seleção e composição dos 6 casos | `CONSTRUIR` |
| Figura 5.3.1 | Trajetórias de admissões por caso e idade | `CONSTRUIR` |
| Figura 5.3.2 | Trajetórias de salário por caso e idade | `CONSTRUIR` |
| Figuras B.1, B.2, B.3 | Casos por sexo, raça, escolaridade | `CONSTRUIR` |
| Tabelas B.1 a B.5 | Dicionário, matriz idade, diagnósticos pré, sensibilidades, grupos legados | `CONSTRUIR` — são links externos, não renderizadas no texto |

**Nada disto existe na V2.** É o bloco mais caro da Fase 8B: 76 códigos CBO de seis dígitos, seis
casos, seis faixas etárias, dois outcomes, mais as sensibilidades.

Duas correções obrigatórias ao reconstruir:

1. **Base temporal.** A 5.3 normaliza **outubro de 2022** em 1, enquanto todo o resto da
   dissertação usa novembro de 2022 como referência. Harmonizar.
2. **Janela.** A medida-resumo do texto é *"a média de janeiro a junho de 2025"*. Com dados até
   maio de 2026 isso é arbitrário; estender.

---

## Resumo executivo

| Veredito | Itens |
|---|---:|
| `MANTER` — não tocar | **15** (Seção 2 e 3) |
| `NÚMERO NOVO` — gerar com dado V2 já existente | **19** |
| `CONSTRUIR` — não existe na V2, estimar do zero | **14** (com a Figura 5.2.6) |
| `DECIDIR` — depende de escolha sua | **2** |
| **Total** | **50** |

### O que precisa ser estimado do zero na Fase 8B

1. **Faixas etárias PNAD/IBGE** no painel DDD (18–24, 25–34, 35–44, 45–54, 55–65) — Tabela 5.2.3 e
   painel 1 da A.4.
2. **Agregação racial `Negra` = preta + parda** — Tabela 5.2.2 e A.3.
3. **Os seis casos ocupacionais da Seção 5.3** — Tabela 5.3.1 e Figuras 5.3.1/5.3.2. O Apêndice B
   fica adiado pela decisão 1.
4. **Figura 5.2.6**, o forest plot de síntese.

Tudo o mais já está calculado. Isso reduz bastante o tamanho da 8B em relação ao que eu havia
estimado.

### O que provavelmente sai do texto

Nada sai por falta de número. O que sai são **afirmações**, não tabelas:

- a assimetria de gênero nas admissões (5.2.1 e resumo) — não sobrevive;
- a concentração da queda de desligamentos na renda intermediária (5.2.5) — não sobrevive;
- a leitura de "jovens atingidos" (resumo) — inverte para "41–49 poupados";
- a acomodação silenciosa como hipótese com indícios — a decomposição de desligamentos da V2 não
  a apoia (demissão sem justa causa −0,00002, BH p = 0,9995).

### Duas decisões já fechadas por você

- **Janela das figuras de event study: `−23 … +41`**, com a fronteira de +23 marcada.
- **Toda figura de event study leva uma linha horizontal na média dos coeficientes pré**, para que
  a distância vertical até a trajetória pós leia como o DiD e a figura não contradiga a tabela.

### Uma decisão ainda aberta

Painel B.2 da Tabela A.1 — as duas construções alternativas do saldo. Recomendo trocar pelo proxy
cumulativo da V2. Precisa do seu aval antes de eu escrever o plano da 8B.


---

## Decisões do autor — fechadas em 27 de julho de 2026

| # | Questão | Decisão |
|---|---|---|
| 1 | Escopo da Seção 5.3 | **(b)** Tabela 5.3.1 e as duas figuras principais. Apêndice B adiado. |
| 2 | Faixas etárias PNAD/IBGE | **(a)** Construir. Mantém as duas partições, como a V1. |
| 3 | Atualizar a Seção 3 para a PNADc 2026 T1 | **Não.** Fica em 2025 T3. |
| 4 | Onde ficam as estrelas | **(a)** BH nas tabelas principais; nominal e BH lado a lado no Apêndice A. |
| 5 | Raça | **(a)** Agregado `Negra` na tabela principal, seis categorias no Apêndice A.3 — a categoria amarela entra por consequência. |
| 6 | Painel B.2 da Tabela A.1 | **(a)** Trocar pelo proxy cumulativo da V2. |
| 9 | Painel B.2 nas tabelas de heterogeneidade | **Cortado.** O proxy é nacional e não existe por grupo; `asinh(saldo)` segue no Painel B.1. |
| 10 | Coluna de pretrend nas Tabelas 5.2.x | **Sim.** Com as 51 células falhando, o coeficiente não viaja sozinho na tabela principal. |
| 11 | Figura 5.2.6 | **Criar.** Forest plot dos 100 contrastes com IC ajustados por BH. |
| 12 | Outcomes nas figuras por grupo | **Ficam dois** — admissões e salário. A V2 reforçou a narrativa de porta de entrada e enfraqueceu a de acomodação silenciosa. |

Consequência resolvida pelo executor, registrada em `DECISIONS.md` antes de rodar: as faixas PNAD e
o agregado `Negra` **não** entram na família de multiplicidade congelada de 100 testes. São
partições alternativas de dimensões que já estão na família, não hipóteses novas, e contá-las de
novo seria dupla contagem. Elas formam família própria de 30 testes com BH independente.
