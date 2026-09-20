# Metodologia e referências — o que citar, onde, e por quê

**Rodada 1 do guia de reescrita.** Data: 28 de julho de 2026.

Este é o eixo mais importante do guia, porque é o único onde hoje **não existe nada**: a Seção 4
monta DiD com efeitos fixos de duas vias, event study, testes de tendências prévias e DDD, e não
cita um único trabalho de metodologia.

Duas verificações que definem o problema:

| Verificação | Resultado |
|---|---|
| Referências metodológicas em `references/library.bib` | **zero**, em 36 entradas |
| Artigos empíricos pedidos que o texto cita zero vezes | **3 de 8**: `adamczyk_skills_2024`, `teutloff_winners_2025`, `hui_short-term_2024` |
| Citações de `brynjolfsson_canaries_2025` no texto | **16** — o texto se apoia quase inteiramente num artigo |

---

## Parte 1 — O que os artigos de referência realmente fazem

Lidos nos PDFs de `references/pdfs/`. Cada afirmação traz a página.

### A grade comparativa

| | **Canaries** (Brynjolfsson et al. 2025) | **Humlum e Vestergaard 2025** | **Klein Teeselink 2025** |
|---|---|---|---|
| Unidade | firma × quintil de exposição × mês | trabalhador × mês | firma × mês e ocupação × mês |
| Tratamento | quintis de exposição (Eloundou) | adoção autodeclarada de chatbot | **exposição contínua padronizada** |
| Evento | ChatGPT | ChatGPT | ChatGPT |
| **Referência** | **out/2022 (τ = −1)**, p. 19 | **nov/2022**, p. 13 | **out/2022 (τ = −1)**, p. 11 |
| **Estimador** | **Poisson (PPML)**, p. 15 eq. 4.1 | OLS, p. 13 eq. 1 | OLS, p. 11 eq. 3 |
| Efeitos fixos | firma×quintil + **firma×tempo**, p. 19 | mês + controles predeterminados | firma + **indústria×período**, p. 11 |
| Agrupamento | **firma**, p. 19 | local×ocupação, p. 13 | **firma**, p. 11 |
| Janela | jan/2021–jul/2025 | mensal em torno de nov/2022 | **15 pré, 30 pós** (assimétrica), p. 11 |
| Tendências prévias | inspeção do event study | **controla por tendência do grupo**, eq. 2 | testa no event study |
| Robustez | excluir ocupações de TI; excluir setor de informação; condicionar em trabalho remoto, p. 21 | intensidade do tratamento; heterogeneidade ocupacional | — |
| Multiplicidade | não corrige | não corrige | não corrige |

### As cinco frases que você pode usar diretamente

**1. Novembro de 2022 como referência é convenção da literatura — não é escolha sua.**

Humlum e Vestergaard, p. 12, nota 8, textualmente:

> *"event studies centered on its launch in November 2022 have become common in the literature (e.g.,
> Brynjolfsson, Chandar and Chen (2025); Eisfeldt et al. (2024); Lichtinger and Hosseini Maasoum
> (2025); Schubert (2025); Teutloff et al. (2025)), facilitating comparison across studies."*

Cinco artigos listados como usando a mesma convenção. Isso resolve de uma vez a justificativa da
referência temporal da V2.

**2. PPML para contagem tem precedente direto no artigo de referência.**

Canaries, p. 19, nota 17, textualmente:

> *"Because of zero counts in the outcome variable, we estimate a Poisson regression instead of an
> OLS regression in logs following guidance from **Chen and Roth (2024)**."*

Isso é decisivo. O seu artigo de referência principal usa **exatamente o estimador da V2**, pelo
**mesmo motivo**, e cita a fonte metodológica. A V1 usava `log(1+y)`; a V2 corrigiu para PPML; e
agora há como dizer que a correção alinha o trabalho com a fronteira.

**3. Efeitos fixos de setor × período são especificação principal, não robustez.**

Klein Teeselink, p. 11, inclui `δ_jt`, efeitos fixos de indústria por período, *"to account for
sector-specific shocks that might correlate with technology adoption patterns"* — na equação
principal. É exatamente o **nível 2** da V2, que o contrato declara `co_principal_sector`.

Canaries vai além, com efeitos fixos de **firma × tempo** (p. 19), que são mais saturados ainda.

Ou seja: a V2 está alinhada com os dois, e o texto atual não reporta esse exercício em lugar nenhum.

**4. Janela assimétrica é normal.**

Klein Teeselink usa 15 meses pré e 30 pós (p. 11). A V2 usa 23 e 42. Não é preciso justificar
simetria que a literatura não pratica.

**5. Controlar por tendência prévia é o que Humlum faz — e a forma importa.**

Humlum, p. 15, nota 11:

> *"the pooled difference-in-differences in Figure 5(a) (which control for pre-trends; see Equation
> (2)) are precise zeros"*

A Equação 2 dele (p. 13) acrescenta `λ_3 t + λ_4 A_i t` — **tendência linear específica do grupo
tratado**. Isso é exatamente a especificação `02_differential_linear_trend` da Fase 8A da V2, não a
de inclinação por CBO. Vale dizer isso explicitamente: a forma que você reporta é a mesma dele.

**Resultado que precisa ser dito:** em Humlum a tendência prévia zera o efeito; na V2 ela **não**
zera — os coeficientes ficam praticamente iguais e mais precisos. Isso é uma diferença substantiva
entre os dois trabalhos e merece um parágrafo, não uma nota.

### O contraste que o texto precisa enfrentar: salário

**Canaries não encontra efeito salarial.** Fact 5, p. 21: *"a less marked divergence in
compensation compared to employment"*, e *"little difference in compensation trends by age or
exposure quintile"*.

A V2 encontra −5,1% no salário de admissão, significativo. **É o oposto do artigo de referência.**

Canaries dá o arcabouço teórico para explicar por que o sinal pode ir para qualquer lado, citando
**Autor e Thompson (2025)** (p. 21): tecnologia que substitui tarefas *inexperientes* pode reduzir
emprego e **aumentar** salário ocupacional; tecnologia que substitui tarefas *experientes* faz o
contrário. E cita **Davis e Krolikowski (2025)** para rigidez salarial de curto prazo.

Três diferenças de desenho ajudam a explicar por que você acha e ele não:

1. ele mede **remuneração de estoque**, você mede **salário de admissão** — margens diferentes;
2. ele tem efeitos fixos de firma × tempo, que absorvem política salarial da firma;
3. a Fase 9 mostrou que 23% a 29% do seu diferencial é **composição educacional**, e ele controla
   composição via firma × tempo.

Isso não invalida seu achado. Torna-o explicável.

### O quarto artigo: a lacuna brasileira

`adamczyk_skills_2024` — Adamczyk, Ehrl e Monasterio, *Skills and employment transitions in Brazil*
— é o único artigo brasileiro da pasta e é **citado zero vezes**.

Ele não é sobre IA. É sobre habilidades, mudança tecnológica enviesada à rotina e polarização no
Brasil, usando a **RAIS** de 2003 a 2018 (p. 3). Serve para duas coisas:

1. **ancorar o trabalho numa tradição brasileira**, que é a lacuna nº 13 da auditoria da V1;
2. **fornecer a bibliografia brasileira que falta**. As referências dele que você deve buscar:

| Referência | Para quê |
|---|---|
| **Maciente (2013)** | mapeamento O*NET ↔ CBO já existente no Brasil — **é o precedente direto do seu crosswalk** e você precisa dizer por que construiu outro |
| Firpo e Portella (2019) | mudança técnica enviesada por idade e obsolescência de habilidades no Brasil |
| Almeida, Corseuil e Poole (2017) | polarização no Brasil, com RAIS completa |
| Maloney e Molina (2019); Ariza e Bara (2020) | evidência divergente sobre polarização |
| Albuquerque et al. (2019) | previsão de impacto da automação no mercado brasileiro |
| Ehrl e Monasterio (2019, 2021) | concentração de habilidades em mercados locais |

O ponto mais importante é **Maciente (2013)**: existe um mapeamento O*NET→CBO consolidado no
Brasil. Você construiu o seu a partir da ponte MTE CBO94→CIUO-88. Uma banca brasileira vai
perguntar por que, e a resposta — que o índice da OIT é nativo em ISCO-08 e não em O*NET — é boa,
mas precisa estar escrita.

### Os outros quatro artigos

| | **Hosseini Maasoum e Lichtinger 2025** | **Teutloff et al. 2025** | **Hui et al. 2024** | **Aldasoro et al. 2026** |
|---|---|---|---|---|
| Unidade | firma × mês; tarefa × firma × ocupação × senioridade | semana × cluster de habilidade | freelancer × mês | firma (survey anual) |
| Tratamento | **adoção** de GenAI pela firma | cluster substituível vs. complementar | ocupação de escrita | adoção de IA declarada |
| Adoção | **escalonada**, 2023–2025 | data única | data única | — |
| Estimador | DiD e **diferença tripla** | OLS DiD | DiD | **variável instrumental** |
| Efeitos fixos | tarefa; firma × ocupação | semana; cluster | freelancer | — |
| Agrupamento | **firma** | cluster | — | — |
| Multiplicidade | não corrige | **reconhece e declina**, p. 12 | não corrige | — |

**Hosseini Maasoum** é o mais próximo do seu DDD. A equação 9 (p. 25) é
`β^A Exp×Adopt + β^AS Exp×Adopt×Senior + Γ'Z + α_j + α_ic`, onde **`Z` reúne explicitamente as
interações de ordem inferior** — validando a exigência da V2 de que todos os termos de ordem
inferior entrem na especificação DDD.

Dois pontos de contraste com o seu desenho, ambos úteis:

- a adoção deles é **escalonada** (Figura 2, p. 21: adotantes entram entre 2023 e 2025), então é
  exatamente o caso em que Goodman-Bacon e Callaway–Sant'Anna importam. O seu não é. Isso reforça o
  parágrafo do §4.1;
- o arcabouço teórico deles (§3, p. 12–16) dá o **mecanismo** para efeitos enviesados por
  senioridade: deslocamento, produtividade e realocação, sobre a estrutura de tarefas de
  Acemoglu–Autor. É a base teórica que falta à sua §5.2.3, hoje puramente empírica.

### Teutloff traz dois presentes

**1. O placebo temporal da V2 tem precedente idêntico** (p. 12):

> *"We first provide a standard 'placebo treatment time' test to show that our results do not
> capture underlying trends that are unrelated to ChatGPT. We do this by **entirely dropping the
> post-ChatGPT period** from our data. Thereafter, we introduce a placebo treatment set to 30th May
> 2022."*

É exatamente o desenho da V2 — descartar o pós e datar um evento falso dentro do pré verdadeiro. A
V2 usa dezembro de 2021; eles usam maio de 2022. Cite.

**2. Eles reconhecem o problema de multiplicidade e escolhem não corrigir** (p. 12):

> *"Given the large number of comparisons, some statistically significant pre-trends will occur by
> chance... comparing estimates requires adjusting for multiple hypothesis testing. However,
> adjusting for every pairwise comparison is impractical, as it would inflate standard errors and
> make Fig. 5 uninformative. We therefore recommend focusing on the top and bottom of the
> distribution."*

**Isto é um ponto onde o seu trabalho é mais rigoroso que o publicado.** Um artigo do *Journal of
Economic Behavior and Organization* declara o problema e declina de tratá-lo; a V2 aplica
Benjamini-Hochberg sobre famílias declaradas antes da estimação. Vale uma frase na §4.4 — não como
crítica a eles, mas para posicionar a escolha.

Teutloff também roda robustez removendo do controle os clusters de design gráfico, porque geradores
de imagem poderiam contaminá-los (p. 12) — o análogo do seu jackknife.

### Aldasoro não é comparável, e o texto trata como se fosse

`aldasoro_ai_2026` **não usa diferenças em diferenças**. É uma estratégia de **variável
instrumental** sobre o EIBIS, survey anual de ~12 mil firmas da UE, estendendo a abordagem de
dependência financeira de Rajan e Zingales à difusão tecnológica (p. 5). Encontra ganho causal de
4% em produtividade do trabalho, com aprofundamento de capital em vez de substituição de trabalho.

O texto atual (linha 454) o cita ao lado de estudos de DiD como evidência do mesmo tipo. São
identificações diferentes, com dados de natureza diferente — survey anual contra registro mensal.
Vale ajustar a frase para não sugerir comparabilidade que não existe.

### Hui: a winsorização tem precedente

Upwork, painel freelancer-mês de janeiro de 2022 a abril de 2023, 92.547 freelancers. Tratamento:
ocupações de escrita. **Winsorizam os outcomes a 1% e 99%** (p. 6) — a mesma regra da V2, o que
dispensa justificar do zero.

Limitação declarada por eles e que vale para você: não observam emprego fora da plataforma, então
não sabem se a queda é redução de emprego ou substituição por outra forma. É o análogo exato da sua
limitação de informalidade.

---

## Parte 2 — Referências metodológicas a adquirir

**Nenhuma está em `references/pdfs/`.** Todas precisam ser baixadas e adicionadas ao `library.bib`.

### Bloco 1 — Por que o TWFE é válido aqui (§4.1)

| Referência | O que você diz com ela |
|---|---|
| Goodman-Bacon (2021), *JoE* | Decomposição do TWFE com adoção escalonada. **Cite para dizer que não se aplica**: sua data de tratamento é única. |
| Callaway e Sant'Anna (2021), *JoE* | Estimador robusto a escalonamento. Idem — não é necessário aqui. |
| Sun e Abraham (2021), *JoE* | Contaminação entre coortes no event study. Idem. |
| de Chaisemartin e D'Haultfœuille (2020), *AER* | Pesos negativos. Idem. |

**Este é o parágrafo mais barato e de maior retorno do trabalho inteiro.** Sem ele, parece que você
desconhece a literatura de 2020–2021. Com ele, a ausência de escalonamento vira força declarada.

### Bloco 2 — Tendências prévias (§4.3 e §5.1)

| Referência | O que você diz com ela |
|---|---|
| **Roth (2022)**, *AER: Insights* | Condicionar a interpretação no resultado de um pré-teste distorce a inferência. É o problema central do seu trabalho e você deve levantá-lo antes que levantem. |
| **Rambachan e Roth (2023)**, *ReStud* | A alternativa construtiva — a V2 já roda `DeltaRM` e `DeltaSD`. |
| Borusyak, Jaravel e Spiess (2024), *ReStud* | Estimação eficiente e diagnóstico de pré-tendência. Opcional. |

### Bloco 3 — Estimador (§4.3)

| Referência | O que você diz com ela |
|---|---|
| **Silva e Tenreyro (2006)**, *ReStat* | O clássico do PPML: log-linearização é viesada sob heterocedasticidade. |
| **Chen e Roth (2024)**, *QJE* | **Citado pelo Canaries, p. 19, nota 17.** Zeros e transformações logarítmicas; justifica a escolha de Poisson em vez de `log(1+y)`. |
| Correia, Guimarães e Zylkin (2020), *Stata Journal* | Implementação de PPML com muitos efeitos fixos e detecção de separação. |
| Bellemare e Wichman (2020), *OBES* | Interpretação do `asinh` — e por que não é percentual. |

### Bloco 4 — Inferência (§4.3)

| Referência | O que você diz com ela |
|---|---|
| **Cameron e Miller (2015)**, *JHR* | Agrupamento, graus de liberdade e por que 341 clusters bastam. |
| Abadie, Athey, Imbens e Wooldridge (2023), *QJE* | Quando agrupar — útil se perguntarem por que CBO4 e não algo mais agregado. |

### Bloco 5 — Multiplicidade (§4.4)

| Referência | O que você diz com ela |
|---|---|
| **Benjamini e Hochberg (1995)**, *JRSS-B* | O procedimento que a V2 usa. Obrigatória. |
| Romano e Wolf (2005), *Econometrica* | Alternativa por reamostragem; cite como caminho não seguido e por quê. |
| List, Shaikh e Xu (2019), *Exp. Econ.* | Multiplicidade em economia experimental e aplicada. Opcional. |

### Bloco 6 — Falsificação (§4.5 nova)

| Referência | O que você diz com ela |
|---|---|
| Bertrand, Duflo e Mullainathan (2004), *QJE* | O clássico do placebo e da inferência em DiD com séries longas. |
| Abadie, Diamond e Hainmueller (2010), *JASA* | Placebo de grupo por reatribuição — a V2 roda 500. |

---

## Parte 3 — Ordem de trabalho sugerida

1. **Baixe primeiro o Bloco 1 e o Bloco 2.** São seis referências e resolvem as duas lacunas mais
   visíveis: o silêncio sobre o TWFE e o silêncio sobre pré-testes.
2. **Chen e Roth (2024)** vem em seguida, porque é a citação que o seu próprio artigo de referência
   usa para justificar o estimador que você adotou.
3. **Adamczyk (2024) e Maciente (2013)** fecham a lacuna brasileira, que é a que uma banca daqui
   pergunta primeiro.
4. O restante pode entrar conforme você escreve.

Nenhuma dessas referências muda um número. Todas mudam o quanto o trabalho parece saber o que está
fazendo.
