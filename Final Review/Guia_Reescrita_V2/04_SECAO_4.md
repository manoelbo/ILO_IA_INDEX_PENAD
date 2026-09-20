# Seção 4 — o que muda

**Rodada 3 do guia.** Todas as equações conferidas contra a fórmula que o código executa de fato
(`specification_ladder.csv`, `event_study_support.json`, `ddd_multiplicity_results.csv`).

---

## §4.1 — três acréscimos e uma correção

### Acréscimo 1: por que CAGED e não PNADc

Hoje o texto não justifica. A §4.2 apenas menciona, de passagem, que a PNAD usa COD e o CAGED usa
CBO. Isso é diferença de taxonomia, não argumento de desenho. **Texto pronto:**

> A escolha do CAGED sobre a PNAD Contínua decorre do que se quer medir. O objeto desta seção é a
> **porta de entrada** do emprego formal — admissões e o salário de contratação —, e é nessa margem
> que a literatura internacional tem encontrado os primeiros ajustes à IA generativa. Três
> propriedades tornam o CAGED mais adequado.
>
> Primeiro, **frequência**. O CAGED é mensal e a PNADc é trimestral. Um desenho de estudo de eventos
> centrado em novembro de 2022 precisa de resolução mensal para distinguir o que acontece antes e
> depois do choque; com dados trimestrais, o trimestre do evento é simultaneamente pré e pós.
>
> Segundo, **natureza do registro**. O CAGED é registro administrativo de declaração obrigatória,
> com cobertura praticamente completa do mercado formal, enquanto a PNADc é amostra domiciliar
> complexa. Para recortes finos por ocupação de quatro dígitos, a amostra da PNADc não sustenta
> precisão: muitas ocupações teriam poucas observações por trimestre.
>
> Terceiro, e mais importante, **o objeto observado**. A PNADc mede **estoque** de ocupados; o CAGED
> mede **fluxo** de admissões e desligamentos. A hipótese testada aqui é sobre contratação, e o
> estoque só se move depois que o fluxo se move.
>
> A contrapartida é declarada e é séria: o CAGED observa apenas o mercado formal, e não observa o
> estoque. Se a difusão da IA empurrar trabalhadores para a informalidade, esse deslocamento é
> invisível aqui. A Seção 3, baseada na PNADc, cumpre o papel complementar de caracterizar a
> estrutura ocupacional e a informalidade; as duas seções respondem a perguntas diferentes com a
> base adequada a cada uma.

### Acréscimo 2: por que o TWFE é válido aqui

**É o parágrafo de maior retorno do trabalho inteiro.** Sem ele, parece desconhecimento da
literatura de 2020–2021. **Texto pronto:**

> A literatura recente documentou que estimadores de diferenças em diferenças com efeitos fixos de
> duas vias podem produzir ponderações negativas e estimativas viesadas quando as unidades são
> tratadas em **momentos diferentes** (Goodman-Bacon, 2021; Callaway e Sant'Anna, 2021; Sun e
> Abraham, 2021; de Chaisemartin e D'Haultfœuille, 2020). Esse problema **não se aplica a este
> desenho**. Aqui a data de tratamento é única e comum a todas as ocupações expostas — o lançamento
> público do ChatGPT —, e existe um grupo que nunca é tratado, as ocupações não expostas. Sem adoção
> escalonada não há comparações entre coortes tratadas em momentos distintos, que é a fonte das
> ponderações negativas. Nesse caso, o estimador de dois grupos e dois períodos com efeitos fixos é
> o estimador correto sob a hipótese de tendências paralelas, e os estimadores robustos a
> escalonamento seriam equivalentes.

### Acréscimo 3: alinhar o desenho com a literatura

Vale um parágrafo curto dizendo que a referência em novembro de 2022 é convenção. Humlum e
Vestergaard (2025, p. 12, nota 8) registram textualmente que estudos de evento centrados nessa data
*"have become common in the literature"*, citando cinco trabalhos. É defesa barata.

### Correção: a descrição do estudo ADP

O texto atual descreve o Canaries como painel de vínculos por firma com foco em tecnologia. A
descrição precisa ser corrigida — o desenho deles é firma × quintil de exposição × mês, com
**regressão de Poisson** e efeitos fixos de firma×quintil e firma×tempo (p. 15, eq. 4.1; p. 19).

---

## §4.2 — reescrever a construção do painel

O texto atual descreve uma extração simples de microdados. A V2 fez muito mais, e nada disso está
escrito. **Acrescentar:**

1. **Vintage único e assinado.** Os dados vêm de uma única safra oficial do MTE, com identidade
   `MOV + FOR − EXC`: movimentações no prazo, mais declarações fora do prazo, menos exclusões,
   todas reatribuídas ao **mês do fato** e não ao mês da declaração. A V1 usava apenas MOV, o que
   omitia 8,6% das movimentações de 2021 contra 1,3% de 2024 — perda diferencial no tempo.
2. **Validação externa.** A série mensal reconstruída bate **exatamente** com a série ajustada do
   PDET nos 65 meses, em admissões, desligamentos e saldo.
3. **Regra de ausência.** Salário e composição são **ausentes** quando o fluxo correspondente é
   zero. A V1 preenchia com zero, o que fazia a winsorização inventar salários plausíveis em
   células sem nenhuma admissão.
4. **Domínios inválidos.** Registros com salário fora de (0, R$ 1 milhão), idade fora de 14–90, CBO
   inválida ou código de fluxo impossível são rejeitados **antes** da agregação.
5. **Winsorização.** P1/P99 no nível do registro, dentro de CBO4 × ano, aplicada igualmente a
   salário de admissão e de desligamento.

E os quatro números da Tabela 4.2.1 — ver `01_TABELAS.md`.

### Duas limitações da medida que precisam ser declaradas aqui

A auditoria da Fase 9 mediu duas propriedades da classificação de tratamento que o texto não
declara. Nenhuma invalida o desenho; ambas são o tipo de coisa que fica muito ruim se um arguidor
descobrir antes de você.

**1. O tratamento não é função monótona do score.** A regra V-A combina o score médio com o
desvio-padrão agrupado entre os destinos ISCO de cada CBO. A consequência é que ocupações com o
mesmo score podem cair em lados opostos:

| Lado | CBOs | Faixa de score |
|---|---:|---|
| Tratado | 75 | 0,280 a 0,593 |
| `Minimal Exposure` (excluído) | 95 | 0,220 a 0,410 |
| Controle | 266 | 0,090 a 0,320 |

Na faixa **[0,280; 0,320]** convivem 64 CBOs: 30 no controle, 31 excluídas e 3 tratadas.

A atenuante é quantitativa e vale declarar junto: **72 das 75 tratadas (96%) estão acima do máximo
do controle**. A faixa de ambiguidade é estreita, mas existe.

**2. As 193 CBOs sem score não são aleatórias.** São 30,7% do universo, e sua distribuição por
grande grupo difere sistematicamente das classificadas:

| Grande grupo CBO | % das sem score | % das classificadas |
|---|---:|---:|
| 1 — Dirigentes e gerentes | **19,2%** | **2,8%** |
| 7 — Bens e serviços industriais | 10,4% | 25,9% |
| 8 — Processos contínuos | 2,6% | 11,7% |

Gerentes estão **sete vezes** mais representados entre as ocupações perdidas — e gerência é um dos
grupos mais expostos na literatura. A perda é sistemática e vai **contra** o achado, o que é a
direção conservadora, mas precisa estar escrito.

**3. O Gradiente 4 vazio, com número.** O maior score observado entre as 436 CBOs pontuadas é
**0,5933**; o limiar do Gradiente 4 é **0,60**. Ele está vazio por **0,0067** — por aritmética, não
por escolha. A explicação de diluição que o texto já dá está **correta**; o que falta é o número.
Um argumento com 0,5933 dentro é muito mais forte que um argumento qualitativo.

---

## §4.3 — as equações

**Texto pronto.** Substitui a equação única atual, que traz `X'γ` no modelo principal e é linear.

### Modelo estático

Para os fluxos, que são contagens com zeros, a especificação principal é PPML:

```latex
E\!\left[Y_{c,t} \mid \cdot\right] = \exp\!\Big(\beta\,\big(\text{Exposta}_c \times \text{Pós}_t\big) + \alpha_c + \delta_t\Big)
```

Para o salário real de admissão e o saldo líquido, a especificação é linear:

```latex
Y_{c,t} = \beta\,\big(\text{Exposta}_c \times \text{Pós}_t\big) + \alpha_c + \delta_t + \varepsilon_{c,t}
```

onde $c$ indexa a CBO de quatro dígitos, $t$ o mês, $\alpha_c$ e $\delta_t$ são efeitos fixos de
ocupação e de mês, $\text{Exposta}_c$ vale 1 para os gradientes 1 a 4 da OIT e 0 para `Not
Exposed`, e $\text{Pós}_t$ vale 1 a partir de dezembro de 2022. Erros-padrão agrupados por CBO de
quatro dígitos, com inferência baseada na distribuição $t$ com $G-1$ graus de liberdade.

**O que mudou e precisa ser dito:**

- **Não há mais $X_{c,t}'\gamma$ no modelo principal.** Os controles de composição — idade média,
  participação feminina, escolaridade, raça dos admitidos — são **pós-tratamento**: se a IA muda
  quem é contratado, controlá-los remove parte do efeito. Passam a ser reportados como
  especificação descritiva, e a composição pré-tratamento interagida com o pós entra como robustez.
- **O coeficiente PPML é semi-elasticidade em nível**, não log-log. Uma queda de 5% em admissões é
  $100 \times (e^{\beta} - 1)$.

### Justificativa do PPML

> As contagens de admissões e desligamentos contêm zeros, e a log-linearização de variáveis com
> zeros exige transformações cujo coeficiente não recupera a elasticidade de interesse. Silva e
> Tenreyro (2006) mostram que a estimação log-linear é viesada sob heterocedasticidade, e Chen e
> Roth (2024) documentam os problemas de $\log(1+y)$ na presença de zeros. Adota-se por isso a
> pseudo-máxima verossimilhança de Poisson, que estima a média condicional em nível e acomoda zeros
> diretamente. **Esta é também a escolha de Brynjolfsson, Chandar e Chen (2025)**, que estimam
> regressão de Poisson pelo mesmo motivo e citando a mesma fonte. Os modelos OLS em $\log(1+y)$
> permanecem reportados como estimador secundário.

### Estudo de eventos

```latex
E\!\left[Y_{c,t} \mid \cdot\right] = \exp\!\Big(\textstyle\sum_{k=-23,\,k\neq-1}^{+41} \beta_k\,\mathbf{1}[t - t^{*} = k]\times\text{Exposta}_c + \alpha_c + \delta_t\Big)
```

com $t^{*}$ = dezembro de 2022 e **novembro de 2022 ($k=-1$) omitido**. Sem agrupamento de caudas:
cada coeficiente corresponde a um mês.

> A janela é assimétrica — 23 meses antes e 42 depois — porque a safra congelada permite acompanhar
> o período pós até maio de 2026. Janelas assimétricas são prática corrente nesta literatura: Klein
> Teeselink (2025) usa 15 meses antes e 30 depois.

### Diferença tripla

```latex
Y_{c,g,t} = \beta_{\text{DDD}}\,\big(\text{Pós}_t \times \text{Exposta}_c \times \text{Grupo}_g\big) + \gamma_1 (\text{Pós}\times\text{Exposta}) + \gamma_2 (\text{Pós}\times\text{Grupo}) + \gamma_3 (\text{Exposta}\times\text{Grupo}) + \alpha_c + \delta_t + \theta_g + \varepsilon_{c,g,t}
```

Todos os termos de ordem inferior entram explicitamente.

**Distinção que precisa estar escrita**, porque a Fase 8B mostrou que é fácil de confundir:

| Estimador | Pergunta | Onde aparece |
|---|---|---|
| **DiD dentro do grupo** | Entre mulheres, ocupações expostas divergiram das não expostas? | Tabelas 5.2.x |
| **DDD** | Essa divergência é **diferente** da dos homens? | Tabelas A.2 a A.6 |

O primeiro capta o efeito nacional inteiro e reaparece em quase todo grupo. Só o segundo testa
heterogeneidade.

---

## §4.4 — pré-especificar a multiplicidade

Hoje a §4.4 descreve as dimensões de heterogeneidade e o DDD, mas não diz nada sobre testes
múltiplos. **Acrescentar:**

> Os exercícios de heterogeneidade envolvem um número grande de contrastes, e a 5% nominais alguns
> resultados significativos são esperados por acaso. Adota-se o procedimento de Benjamini e Hochberg
> (1995), que controla a taxa de falsas descobertas, sobre famílias declaradas **antes** da
> estimação:
>
> | Família | Conteúdo | Testes |
> |---|---|---:|
> | A | DDD sobre as 20 partições originais × 5 outcomes | 100 |
> | B | DDD sobre as partições alternativas — faixas PNAD e agregado `Negra` | 30 |
> | C | DiD dentro do grupo, todas as 26 partições × 5 outcomes | 130 |
>
> As famílias A e B são mantidas separadas porque as partições alternativas são reexpressões de
> dimensões já contidas em A — testar 18–24 e testar 22–25 não são hipóteses independentes — e
> contá-las duas vezes inflaria a família sem ganho informacional. Cada tabela declara a que família
> pertence e o tamanho dela.

E o resultado: **34 contrastes nominalmente significativos, 21 sobreviventes ao ajuste** na Família
A.

---

## §4.5 — subseção nova de robustez

A auditoria da V1 registrou robustez prometida e não reportada (item 6). Agora há material.
**Sugestão de estrutura, uma frase por item:**

1. **Escada de especificações** — sete degraus pré-registrados: sem controles, composição pré × pós,
   composição contemporânea, `Minimal Exposure` como controle, exposição contínua padronizada,
   amostra a partir de 2022, amostra até dez/2025.
2. **Placebo temporal** — evento falso em dezembro de 2021, estimado apenas no pré-período
   verdadeiro. Passa nos cinco outcomes.
3. **Placebo de grupo** — 500 reatribuições aleatórias preservando 75 tratadas e 341 CBOs. O
   salário fica no percentil 0,0.
4. **Variantes de tratamento** — quatro regras de classificação pré-registradas.
5. **Medidas alternativas de exposição** — safra 2023 da OIT, consenso GPT-4o/Gemini, e o índice da
   Anthropic.
6. **Sensibilidade a tendências prévias** — Rambachan e Roth (2023), com `DeltaRM` e `DeltaSD`.
7. **Nível setorial** — efeitos fixos de CNAE × mês, co-principal.
8. **Influência ocupacional** — jackknife removendo cada uma das 75 ocupações tratadas.

O item 2 e o item 3 merecem cuidado na redação: o placebo temporal do salário dá **−0,0198 com
p = 0,081**, que é 39% do coeficiente principal num período sem ChatGPT. Passa no critério, mas
reportar só "passou" seria seletivo.
