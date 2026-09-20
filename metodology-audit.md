# Auditoria de Decisões Metodológicas

**Objeto:** Dissertação de Mestrado V2.5 + Replication Package V2
**Data do levantamento:** 2026-08-08
**Fase atual:** inventário (Fase 1). A avaliação de cada decisão vem depois.

---

## 1. Propósito e escopo

Este documento inventaria **todas as decisões metodológicas** identificáveis no trabalho — as que estão escritas no texto, as que estão declaradas apenas no contrato de replicação e as que existem somente como parâmetro no código. O objetivo é ter uma lista fechada e nomeada para, na fase seguinte, avaliar cada decisão uma a uma.

**Fontes consultadas:**

| Fonte | Papel |
| --- | --- |
| `Dissertação/V2.5/Dissertação de Mestrado V2 325cc8ca...md` | Texto autoritativo (Seções 1–6, Apêndices A–D) |
| `Replication Package/V2/RESEARCH_DESIGN.md` | Contrato de replicação; estimandos, famílias, gates |
| `Replication Package/V2/config/*.csv` | Registros de análises, fontes de dados, artefatos |
| `Replication Package/V2/code/**` | Decisões que só existem como parâmetro de código |
| `Replication Package/V2/R/**` | HonestDiD e replicação cruzada |

**Convenções deste inventário:**

- **Slug** — identificador estável em kebab-case. É a chave para referenciar a decisão na fase de avaliação.
- **Tipo** — `S` = substantiva (afeta o estimando ou a estimativa); `P` = procedimental (afeta credibilidade, transparência ou reprodutibilidade, não o número).
- **Onde consta** — localização primária. `§` = seção da dissertação; `RD` = `RESEARCH_DESIGN.md`; caminho = arquivo do pacote.
- Uma decisão de **não fazer** algo (não executar, não estimar, não corrigir) conta como decisão metodológica e está inventariada.

---

## 2. Bloco A — Mensuração da exposição

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| A1 | Definir exposição como potencial técnico ex-ante | `exposicao-como-potencial` | S | Exposição é definida como o potencial de a IA afetar as tarefas de uma ocupação, explicitamente distinta de adoção efetiva e de impacto causal. A definição é fixada antes de qualquer medida e governa toda a leitura dos resultados. | §2.1, §2.5 |
| A2 | Adotar o arcabouço baseado em tarefas | `abordagem-por-tarefas` | S | A mensuração se apoia na abordagem de tarefas (Autor, Levy e Murnane, 2003): a tecnologia atinge tarefas, não ocupações inteiras. Daí decorre a distinção entre automação e complementaridade, que é mantida como não-decidível pelo índice. | §2.2 |
| A3 | Comparar quatro índices antes de escolher | `comparacao-indices` | P | GPT Exposure, GENOE, Anthropic Economic Index e ILO Global Index são comparados em três critérios declarados (base ocupacional, forma de classificar, adaptabilidade ao Brasil) antes da escolha, com o papel de cada um na dissertação fixado na Tabela 2.1. | §2.3 |
| A4 | Adotar o ILO Global Index como medida principal | `indice-oit-principal` | S | O índice da OIT (Gmyrek *et al.*, 2025) é a medida principal, por dois critérios declarados: ser o único estruturado em ISCO-08 (compatível com COD e, via ISCO-88, com a CBO) e combinar validação humana em três camadas com escalonamento por LLM. | §2.4, §6.5 |
| A5 | Preferir ISCO-08 a uma medida derivada da O*NET | `preferir-isco-a-onet` | S | Rejeita-se explicitamente uma medida baseada em O*NET, apesar da maior comparabilidade com a literatura, porque a distância entre O*NET e CBO é maior que a distância entre CBO e ISCO-08, para a qual existe correspondência oficial brasileira. | §6.5 |
| A6 | Usar a regra de gradiente (μ, σ) e não a média | `regra-gradiente-mu-sigma` | S | A classificação usa a regra da OIT que cruza média (μ) e desvio-padrão (σ) das pontuações de tarefa, e não a média isolada. Consequência aceita: a classificação não cresce monotonicamente com a média. | §3.2 (nota), §4.2 |
| A7 | Definir alta exposição como Gradientes 3 e 4 | `alta-exposicao-g3-g4` | S | Na etapa descritiva, "alta exposição" é operacionalizada como G3 + G4, o que gera o número de 10,1% da força de trabalho. G1 e G2 são tratados como complementação provável. | §3.2, §3.4 |
| A8 | Declarar cinco limites do que o índice não mede | `limites-do-indice` | P | Registram-se explicitamente cinco limitações: não mede uso efetivo, não mede impacto causal, não mede substituição automática, depende de crosswalk e é um índice global. Funciona como restrição declarada de interpretação. | §2.5 |
| A9 | Reservar medidas alternativas de exposição para robustez | `medidas-alternativas-exposicao` | S | Três medidas alternativas entram apenas como sensibilidade: a safra 2023 do índice da OIT, um consenso GPT-4o + Gemini e o índice da Anthropic. Nenhuma pode substituir a medida principal. | §4.5, `code/caged/models/exposure_sensitivity.py` |

---

## 3. Bloco B — Base descritiva (PNADc, Seção 3)

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| B1 | Usar um único corte transversal (3T/2025) | `pnadc-3t2025-corte-unico` | S | A análise descritiva usa apenas o 3º trimestre de 2025, escolhido por ser o mais recente com microdados completos. Aceita-se explicitamente que o resultado é um retrato transversal, não uma trajetória. | §3.1 |
| B2 | Restringir a amostra a 18–65 anos | `restricao-etaria-18-65` | S | A população analisada é a ocupada de 18 a 65 anos, deixando de fora as pontas da distribuição de idade. A limitação é declarada. | §3.1 |
| B3 | Ponderar por V1028 | `peso-v1028` | S | O peso amostral V1028 (projeção populacional trimestral) é usado em todas as estatísticas descritivas, gerando o universo de 97,8 milhões. | §3.1 (Tabela 3.1) |
| B4 | Aplicar filtros conservadores de amostra | `filtros-amostra-pnadc` | S | Seleção de 15 variáveis e remoção de faltantes críticos e de códigos de ocupação inválidos, resultando em 207.901 observações. | §3.1 |
| B5 | Crosswalk COD→ISCO-08 com fallback hierárquico | `crosswalk-cod-isco-fallback` | S | Correspondência direta a 4 dígitos (97,9%) e, na ausência de match, fallback para 3 e depois 2 dígitos com atribuição da pontuação média do subgrupo. Cobertura final de 99,2%; 0,8% fica sem classificação. | §3.1 |
| B6 | Agregar pretos e pardos como "negra" | `agregacao-racial-osorio` | S | O recorte racial usa a agregação preta + parda, seguindo Osorio (2003). A desagregação em seis categorias do IBGE é preservada nos DDD do Apêndice A. | §3.5.2, §A.4 |
| B7 | Medir renda em salários mínimos com referência fixa | `faixas-renda-sm` | S | As faixas de renda descritivas usam o salário mínimo de R$ 1.518 como referência. | §3.1 (Tabela 3.1), §3.5.5 |
| B8 | Setorizar pela CNAE-Domiciliar 2.0 | `setores-cnae-domiciliar` | S | A distribuição setorial usa as 19 seções (A–T) da CNAE-Domiciliar 2.0, derivadas da variável V4013. | §3.4 |
| B9 | Tratar a exposição como ocupacional, não setorial | `exposicao-ocupacional-nao-setorial` | P | Decisão interpretativa declarada: a distribuição setorial não é lida como se apenas alguns ramos fossem alcançados, porque o trabalho *white collar* existe em todos os setores. | §3.3, §3.4 |
| B10 | Usar a PNADc para caracterizar, não para estimar efeito | `pnadc-papel-descritivo` | P | Divisão de trabalho declarada entre bases: a PNADc responde *quem está exposto*; o CAGED responde *o que aconteceu*. A PNADc não sustenta identificação na Seção 3. | §1, §4.1, §3.6 |

---

## 4. Bloco C — Fonte e construção do painel CAGED

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| C1 | Escolher o CAGED em vez da PNADc para a etapa empírica | `caged-como-fonte-principal` | S | Três razões declaradas: frequência mensal (um evento em novembro exige resolução mensal), natureza de registro administrativo censitário do mercado formal, e o objeto observado ser fluxo de admissões, não estoque. | §4.1, §6.5 |
| C2 | Aceitar que o desenho não observa adoção de IA | `sem-medida-de-adocao` | S | Decisão declarada de que o CAGED não informa uso de IA pela firma; o que se estima é evolução diferencial de ocupações mais expostas, com o choque temporal vindo da difusão pública e a intensidade vindo do índice. | §4.1, §6.2, §6.3 |
| C3 | Fixar a unidade de análise em CBO 4 dígitos × mês | `unidade-cbo4-mes` | S | Toda a análise CAGED opera sobre a célula ocupação-mês (CBO4 × mês), não sobre o vínculo individual nem sobre a firma. | §4.2 |
| C4 | Usar uma única safra oficial e a identidade MOV + FOR − EXC | `identidade-mov-for-exc` | S | O painel vem de uma única safra do Novo CAGED e cada mês obedece à identidade movimentações no prazo + fora do prazo − exclusões. | §4.2, RD |
| C5 | Reatribuir movimentações ao mês de competência do fato | `mes-de-competencia` | S | Toda movimentação é atribuída ao mês do fato, não ao mês de declaração, porque a incidência de declaração fora do prazo é decrescente no tempo (8,6% em 2021 vs. 1,3% em 2024) e se confundiria com tendência prévia. | §4.2 |
| C6 | Reconciliar a série reconstruída com o PDET | `reconciliacao-pdet` | P | A série mensal reconstruída é validada contra a série ajustada divulgada pelo PDET nos 65 meses, em admissões, desligamentos e saldo, antes de qualquer estimação. | §4.2, `config/analysis_registry.csv` |
| C7 | Rejeitar registros inválidos antes da agregação | `filtros-registro-caged` | S | São rejeitados registros com salário fora de (0; R$ 1 milhão), idade fora de 14–90, CBO inválida ou código de movimentação impossível: 3.574.530 de 252.838.929 linhas (1,4%). | §4.2 |
| C8 | Tratar salário e composição como ausentes, não zero | `ausente-nao-zero` | S | Quando o fluxo correspondente é nulo (403 células sem admissão, 355 sem desligamento), salário e composição ficam ausentes em vez de zero, para que a winsorização não produza salários plausíveis onde não houve contratação. | §4.2 |
| C9 | Winsorizar no nível do registro, p1/p99, por CBO4 × ano | `winsorizacao-p1-p99` | S | A winsorização é aplicada no registro, nos percentis 1 e 99, dentro de cada célula CBO4-ano, igualmente ao salário de admissão e de desligamento. | §4.2, `code/caged/panel/build_panel.py` |
| C10 | Deflacionar salários pelo IPCA congelado | `deflacionamento-ipca` | S | O salário de admissão é deflacionado pelo IPCA (série SGS 433 do BCB), congelada com hash no pacote. | §4.3, `config/data_sources.csv` |
| C11 | Iniciar a janela em janeiro de 2021 e excluir 2020 | `janela-2021-2026` | S | Dupla justificativa: o Novo CAGED começa em 2020 e 2020 coincide com a fase aguda da pandemia, cujos efeitos excepcionais se confundiriam com tendência prévia. Consequência aceita e declarada: nenhum mês pré-pandemia na janela. | §4.2, §6.2, §6.3 |
| C12 | Aceitar janela assimétrica (23 pré / 42 pós) | `janela-assimetrica` | S | A janela tem mais tempo depois do evento do que antes, justificada como prática corrente na literatura (Klein Teeselink, 2025: 15 pré / 30 pós). | §4.2 |
| C13 | Reter a cauda incompleta até maio de 2026 | `cauda-incompleta-retida` | S | A janela completa é mantida porque o gap de declaração tardia entre tratados e controle fica abaixo de 1 ponto percentual; direção e magnitude da cauda incompleta são reportadas em vez de a cauda ser truncada. | RD, §4.5 (degrau 7) |
| C14 | Construir o painel de forma determinística | `determinismo-do-painel` | P | O painel setorial é agregado pelo DuckDB com um único worker e ordenado pela chave analítica completa antes da serialização em Parquet, para que o hash não dependa da ordem de agregação paralela. | RD |

---

## 5. Bloco D — Crosswalk CBO→ISCO e definição do tratamento

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| D1 | Usar ponte institucional em duas etapas | `ponte-institucional-cbo-isco` | S | O caminho é CBO 2002 → CBO94/CIUO88 (tábua oficial do MTE) → ISCO-08 (tabela da OIT) → índice. Nenhuma etapa é construída ad hoc pelo autor. | §4.2 |
| D2 | Rejeitar correspondência por semelhança numérica | `sem-correspondencia-adhoc` | S | A correspondência é mantida apenas quando existe ponte institucional identificável; códigos numericamente parecidos não são pareados. | §4.2 |
| D3 | Excluir as CBOs sem correspondência como "No score" | `no-score-excluido` | S | As 193 CBOs sem correspondência oficial recebem rótulo "sem pontuação disponível" e ficam fora da amostra principal, com a declaração explícita de que isso não é exposição baixa ou nula. | §4.2 |
| D4 | Declarar a seletividade da perda de correspondência | `seletividade-do-no-score` | P | Registra-se que a perda não é uniforme: dirigentes e gerentes são 19,2% das CBOs sem correspondência contra 2,8% das classificadas, o que recomenda cautela na leitura da amostra. | §4.2 |
| D5 | Agregar correspondências de muitos para muitos | `agregacao-muitos-para-muitos` | S | Quando uma CBO aponta para vários ISCO-08, as pontuações são agregadas e a regra da OIT é reaplicada. O emprego CBO6 é dividido igualmente entre destinos antes da aplicação dos pesos de destino. | §4.2, RD |
| D6 | Reunir Gradientes 1–4 num único grupo tratado | `tratamento-gradientes-1-4` | S | O grupo exposto pool os Gradientes 1 a 4, escolha justificada como atenuação da diluição do crosswalk. Contrapartida aceita: o desenho não sustenta comparações entre gradientes isolados. | §4.2, RD |
| D7 | Declarar o Gradiente 4 vazio como artefato do crosswalk | `gradiente-4-vazio` | P | Nenhuma CBO4 atinge G4 (máximo de 0,5933 contra o limiar de 0,60) porque a agregação reduz extremos. Declara-se explicitamente que isso é consequência do crosswalk, não evidência de ausência de ocupações altamente expostas no Brasil. | §4.2 |
| D8 | Usar a exposição de forma binária | `exposicao-binaria` | S | A exposição entra como binária (exposta vs. não exposta) na especificação principal; análises por gradiente específico ficam em segundo plano. A medida contínua padronizada aparece só na escada de especificações. | §4.2, §4.5 |
| D9 | Definir o controle como `Not Exposed` estrito | `controle-estrito-not-exposed` | S | O controle são as 266 CBOs `Not Exposed`. As 95 de `Minimal Exposure` ficam fora porque produziriam um controle parcialmente exposto e reduziriam o contraste por construção. | §4.2, §4.5 |
| D10 | Reverter a exclusão de `Minimal Exposure` apenas como sensibilidade | `minimal-como-sensibilidade` | S | A inversão da escolha D9 é estimada e reportada como degrau da escada, inclusive quando fortalece o sinal (admissões passam a −0,0887 e ficam significativas), sem ser promovida a principal. | §4.5, §6.5 |
| D11 | Congelar a atribuição de tratamento antes da estimação | `tratamento-congelado` | P | A classificação é congelada antes de estimar. Variantes ponderadas por emprego, por dispersão de tarefas e por rótulo nativo permanecem sensibilidades e não podem substituir a principal por causa de coeficiente ou significância. | RD, §4.5 |
| D12 | Pré-registrar quatro variantes de tratamento | `variantes-de-tratamento` | S | Quatro regras alternativas de combinar média e dispersão entre destinos ISCO, alterando 8, 16 e 53 das 629 famílias sem reverter a leitura geral. Empates no modo ponderado de rótulo nativo são resolvidos para a categoria menos exposta. | §4.5, §6.5, RD |
| D13 | Auditar o caso CBO 4121 sob quatro agregações | `auditoria-cbo-4121` | P | O caso mais diluído (três destinos com 0,43, 0,65 e 0,70) é verificado sob quatro formas de agregação, das quais três devolvem a mesma classificação, e o resultado é reportado. | §6.5, `code/caged/panel/treatment_variants.py` |
| D14 | Reportar a sobreposição residual entre grupos | `sobreposicao-de-pontuacao` | P | Declara-se que 72 das 75 tratadas têm pontuação acima do máximo do controle, mas que existe uma faixa de sobreposição que deve entrar na interpretação. | §4.2 |

---

## 6. Bloco E — Evento e estrutura temporal

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| E1 | Datar o evento no lançamento do ChatGPT | `evento-chatgpt-nov-2022` | S | O evento é 30 de novembro de 2022, com dezembro de 2022 como tempo zero e novembro de 2022 como período omitido (k = −1). Justificado por alinhamento com a literatura (cinco estudos de evento na mesma data, por Humlum e Vestergaard, 2025). | §4.1, §4.3, RD |
| E2 | Tratar todas as expostas como tratadas na mesma data | `data-unica-sem-staggered` | S | Não há adoção escalonada: todas as ocupações expostas passam a tratadas simultaneamente. Por isso os estimadores de DiD escalonado (Goodman-Bacon; Callaway e Sant'Anna; Sun e Abraham; de Chaisemartin e D'Haultfœuille) são declarados inaplicáveis, e a condição crítica passa a ser tendências paralelas. | §4.1 |
| E3 | Aceitar que o evento é difuso | `evento-difuso` | P | Declara-se que a data é conveniente mas que a difusão de uma tecnologia de propósito geral não ocorre num instante, e que parte dos ajustes pode exceder o período observado. | §6.2 |
| E4 | Fixar a janela balanceada do event study em −23…+23 | `janela-event-study` | S | O event study balanceado usa −23 a +23 com novembro de 2022 omitido; o estático estende-se ao tempo de evento +41. Cada mês recebe seu coeficiente, sem agrupar extremos (*binning*). | §4.3, RD |

---

## 7. Bloco F — Especificação econométrica

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| F1 | Estimar contagens por PPML em nível | `ppml-para-contagens` | S | Admissões, desligamentos e fluxo bruto são estimados por PPML sobre a contagem em nível, justificado pelos zeros e pelos problemas de `log(1+y)` sob heterocedasticidade (Silva e Tenreyro, 2006; Chen e Roth, 2024), além do alinhamento com o artigo de referência. | §4.3 |
| F2 | Estimar o salário real de admissão por MQO em log | `ols-log-salario` | S | O salário deflacionado entra em logaritmo, estimado por MQO, com leitura percentual aproximada. | §4.3 |
| F3 | Estimar o saldo líquido por MQO sobre asinh | `asinh-saldo` | S | O saldo pode ser positivo, negativo ou zero, então usa-se `asinh`, com a restrição declarada de que o coeficiente não tem leitura percentual. | §4.3 |
| F4 | Manter `log(1+y)` apenas como estimador secundário | `log1p-secundario` | S | A estimação linear em `log(1+y)` é calculada e publicada, mas apenas como resultado secundário, nunca como principal. | §4.3, `config/analysis_registry.csv` |
| F5 | Usar efeitos fixos de CBO4 e de mês | `efeitos-fixos-cbo4-mes` | S | A especificação nacional absorve efeitos fixos de ocupação (nível médio de cada CBO) e de mês (sazonalidade, inflação, ciclo). | §4.3, RD |
| F6 | Agrupar os erros-padrão por CBO4 | `cluster-cbo4` | S | A inferência usa erros-padrão agrupados nas 341 CBOs, permitindo correlação temporal dentro da ocupação. Mantida também no nível setorial. | §4.3, §5.1 |
| F7 | Usar distribuição t de cluster com G−1 graus de liberdade | `inferencia-cluster-t` | S | A inferência reportada usa distribuição de referência t com graus de liberdade iguais à menor contagem de clusters menos um, e não a normal. | RD, §A.1 |
| F8 | Excluir controles de composição contemporânea da especificação principal | `sem-controles-contemporaneos` | S | Idade média, participação feminina, escolaridade e composição racial dos admitidos ficam fora do modelo principal porque podem mudar depois do evento e integrar o próprio resultado. Entram só como degrau da escada e como medidas pré-evento. | §4.3, §4.5 |
| F9 | Declarar o nível setorial como co-principal | `nivel-2-co-principal` | S | Efeitos fixos de seção da CNAE por mês são declarados especificação co-principal, e não robustez subordinada, com as duas colunas apresentadas lado a lado na Tabela 5.1.1. | §4.5, §5.1 |
| F10 | Separar dois estimandos salariais que não se equivalem | `dois-estimandos-distintos` | S | O coeficiente estático (−0,050740, pós contra todo o pré, até +41) e a média pós do event study (−0,015363, normalizada a novembro de 2022) são estimandos diferentes e nunca são justapostos como se fossem a mesma estimativa. | RD, §5.1 |
| F11 | Suprimir estrelas de significância na tabela nacional | `sem-estrelas-nacional` | P | A Tabela 5.1 não recebe marcação de significância porque os quatro pretrends falham e a tabela não sustenta leitura causal. | §5.1 |
| F12 | Não definir limiar de relevância econômica | `sem-limiar-de-relevancia` | P | Declara-se que nenhum valor foi fixado ex-ante para classificar magnitudes como economicamente relevantes, e por isso reporta-se tamanho e incerteza sem rotular. | §5.1 |

---

## 8. Bloco G — Heterogeneidade

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| G1 | Reservar o nome DDD para o modelo de tripla interação | `ddd-versus-did-no-grupo` | S | DDD exige `pós × exposta × subgrupo` e todos os termos de ordem inferior identificados. DiD dentro do grupo é insumo descritivo e não se torna tripla diferença por renomeação. Só o DDD testa heterogeneidade. | §4.3, §5.2, RD |
| G2 | Apresentar DiD no corpo e DDD no apêndice | `did-no-corpo-ddd-no-apendice` | P | As tabelas do corpo do texto reportam o DiD dentro do grupo, com nota explícita de que "estas células não medem heterogeneidade"; o teste entre grupos fica no Apêndice A. | §5.2, §A.3–A.7 |
| G3 | Examinar cinco eixos sociodemográficos | `cinco-eixos-heterogeneidade` | S | Sexo, raça/cor, faixa etária, escolaridade e faixa salarial ocupacional, escolhidos porque a Seção 3 mostrou que a exposição varia entre esses perfis. | §4.4 |
| G4 | Usar duas grades de faixa etária | `faixas-etarias-duplas` | S | Faixas da PNAD/IBGE para dialogar com a Seção 3, e as faixas do artigo de referência (22–25, 26–30, 31–34, 35–40, 41–49, 50+) para testar a hipótese de início de carreira. As duas grades são separadas em famílias distintas. | §4.4 |
| G5 | Medir renda pela mediana pré-tratamento da CBO | `renda-mediana-pre-cbo` | S | A faixa salarial usa a mediana pré-tratamento da ocupação, expressa em salários mínimos, e não a renda individual corrente — o que torna o recorte não comparável ponto a ponto com a Seção 3.5.5. | §5.2.5 |
| G6 | Classificar suporte amostral em três níveis declarados | `classificacao-de-suporte` | S | `adequate` a partir de 20 CBOs tratadas e 50 de controle; `limited` a partir de 10/25; `thin` abaixo disso. O rótulo é publicado como parte do resultado, e células `thin` não são usadas como base de afirmação. | §5.2, §5.2.5, `code/caged/models/heterogeneity.py` |
| G7 | Reportar o efeito mínimo detectável a 80% de poder | `mde-80-poder` | P | Cada contraste DDD publica o MDE a 80% de poder, para separar ausência de efeito de ausência de precisão. | §A.3–A.7 |
| G8 | Declarar que DDDs binários são espelhados | `ddd-espelhado-binario` | P | Em dimensões binárias, os DDD dos dois grupos são espelhados por construção e a nota declara que não constituem testes independentes. | §A.3 |
| G9 | Declarar a não aditividade dos contrastes raciais | `nao-aditividade-racial` | P | Registra-se que o contraste do agregado *Negra* é maior que o de qualquer componente porque os complementos diferem, e que a desagregação mostra o efeito conduzido por pardos, não por pretos. | §5.2.2, §A.4 |
| G10 | Definir os subgrupos por composição dos admitidos | `subgrupos-por-composicao` | S | Os recortes demográficos são construídos sobre a composição dos fluxos declarados no CAGED (admitidos por sexo, raça, idade, escolaridade), não sobre painel de trabalhadores. | §4.3, §4.4 |

---

## 9. Bloco H — Multiplicidade

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| H1 | Controlar FDR por Benjamini–Hochberg | `bh-por-familia` | S | BH (1995) é aplicado **uma única vez** dentro de cada família estimada, para controlar a taxa de falsas descobertas em vez do erro familiar. | §4.4, RD |
| H2 | Declarar seis famílias antes da estimação | `familias-a-f` | S | A: 100 DDD primários; B: 30 DDD de partições alternativas; C: 130 DiD dentro do grupo; D: 3 desfechos RAIS; E: 6 desfechos PNADc; F: 12 posições espaciais declaradas. Tamanhos fixados por escrito antes de estimar. | §4.4, RD, §B.3 |
| H3 | Separar as famílias A e B | `separacao-familias-a-b` | S | B fica separada porque apenas redefine grupos já testados em A (18–24 vs. 22–25, p.ex.); juntá-las trataria repetições como testes novos e distorceria a correção. | §4.4 |
| H4 | Separar a família C das famílias de DDD | `separacao-familia-c` | S | C reúne os DiD dentro dos grupos, estimandos distintos dos contrastes DDD de A e B, e por isso recebe ajuste próprio sobre a família completa. | §4.4, RD |
| H5 | Calcular estrelas exclusivamente sobre o p ajustado | `estrelas-sobre-p-bh` | P | Nas tabelas de heterogeneidade, `*`, `**` e `***` são calculados sobre o p de BH, não sobre o nominal, e os dois p aparecem lado a lado no apêndice. | §5.2, §A.3 |
| H6 | Manter a família F declarada e vazia | `familia-f-vazia` | P | As 12 posições espaciais permanecem declaradas sem nenhum coeficiente, p nominal ou p ajustado, registradas como limitação de identificação e não como efeito nulo. | §4.5, §B.3, RD |
| H7 | Não ajustar a família de diagnósticos de pretendência | `diagnosticos-sem-ajuste` | P | Declara-se que os diagnósticos de tendência prévia não recebem correção por multiplicidade, e por isso a única célula que passa entre 100 pode ser acaso — o que impede tratá-la como validação. | §5.2.3, §A.1 |
| H8 | Não fundir famílias nem reajustar após conhecer resultados | `sem-refusao-de-familias` | P | As famílias D, E e F são declaradas independentes das do Apêndice A, e nenhuma é fundida ou reajustada depois da estimação. | §B.4 |

---

## 10. Bloco I — Portões de identificação e diagnósticos

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| I1 | Avaliar suporte antes de coeficientes | `suporte-antes-de-coeficientes` | P | Regra estrutural: o suporte é calculado e publicado antes de qualquer coeficiente, e nenhum critério de continuidade depende do coeficiente de tratamento. | RD, §B.2, §B.3 |
| I2 | Classificar tendências prévias por três critérios combinados | `classificacao-pretendencias` | S | A classificação `pass`/`warning`/`fail` combina o teste conjunto de Wald sobre os leads, a inclinação linear por GLS e a inspeção de leads individuais — de modo que um teste conjunto não rejeitado ainda pode falhar por leads individuais significativos. | RD, §5.2.5, `code/caged/models/pretrend_engine.py` |
| I3 | Estimar pretendência sobre o modelo e a amostra exatos | `pretendencia-modelo-exato` | S | Cada teste de tendência prévia é estimado sobre o modelo, a amostra e a estrutura de agrupamento exatos do resultado reportado, e não sobre uma especificação simplificada. | §A.1, §B.1, §B.2 |
| I4 | Registrar rank e PSD separadamente | `diagnostico-rank-psd` | S | Semidefinição positiva e rank numérico são registrados como diagnósticos distintos, com limiar declarado `max(nrow, ncol) × ε × maior valor singular` nas duas linguagens. Bloco PSD mas deficiente em rank não identifica Wald por inversa nem inclinação GLS. | RD |
| I5 | Publicar coeficientes com diagnósticos indefinidos por construção | `rank-deficiente-visivel` | P | Em blocos deficientes em rank, coeficientes e erros-padrão permanecem publicados enquanto os testes derivados ficam ausentes por construção, com classificação `not_interpretable_rank_deficient` (caso da faixa de renda alta, rank 7 em bloco de 22 leads). | RD |
| I6 | Declarar que a identificação causal não foi alcançada | `identificacao-nao-alcancada` | S | Decisão central: os testes de tendências paralelas são rejeitados em praticamente todas as células, inclusive nas 51 do bloco nacional, e o trabalho declara que os coeficientes descrevem diferenças pós-evento, não efeitos. | §5.1, §6.2, RD |
| I7 | Manter resultados falhos visíveis como exploratórios | `resultados-exploratorios-declarados` | P | Pretendências falhas, blocos não-PSD, rótulos de suporte fino e falhas de estimação permanecem visíveis nos outputs e no status cruzado Python–R, em vez de serem descartados ou omitidos. | RD |
| I8 | Usar HonestDiD para sensibilidade a tendências prévias | `honestdid-rambachan-roth` | S | O procedimento de Rambachan e Roth (2023) substitui o binário aprova/reprova por quanto as tendências poderiam divergir sem alterar a conclusão. Grade M de 0 a 2 em passos de 0,05, `Delta^RM` como principal e `Delta^SD` como complemento de curvatura, mirando o estimando do event study. | §4.5, `R/honest_did.R`, `R/honest_did_sd.R`, RD |
| I9 | Manter HonestDiD nativo em R com insumos independentes | `honestdid-nativo-em-r` | P | HonestDiD roda em R e recebe coeficientes e covariâncias exportados dos modelos de event study ajustados independentemente em R, nunca de um arquivo de resultado do Python. | RD |
| I10 | Documentar a diferença de diagnóstico em relação ao artigo de referência | `diferenca-com-canaries` | P | Registra-se explicitamente que Brynjolfsson, Chandar e Chen (2025) testaram e não encontraram poder preditivo pré-difusão, de modo que a falha de pretendência aqui é uma diferença em relação ao caso americano, e não um problema compartilhado. | §5.1, §6.3 |
| I11 | Nomear a confusão entre exposição e trabalho de escritório | `confusao-escritorio-vs-ia` | S | Declara-se como problema de identificação mais sério que o erro de medida do crosswalk: a fronteira do índice e a fronteira escritório/não-escritório são quase a mesma, e um choque tecnológico e um choque de demanda sobre trabalho administrativo produzem o mesmo coeficiente. | §6.3 |

---

## 11. Bloco J — Robustez, placebos e falsificação

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| J1 | Pré-registrar a escada de sete degraus | `escada-de-especificacoes` | S | Sete degraus declarados antes da estimação: sem controles; composição pré × pós; composição contemporânea; `Minimal` no controle; exposição contínua padronizada; amostra a partir de 2022-01; amostra truncada em 2025-12. | §4.5, `code/caged/models/specification_ladder.py` |
| J2 | Estimar placebo temporal dentro do pré-período | `placebo-temporal` | S | Evento falso em dezembro de 2021, estimado apenas dentro do pré-período verdadeiro, descartando todo o pós-ChatGPT — procedimento igual ao de Teutloff *et al.* (2025), com data distinta. Resultado (−0,0198, p = 0,081, 39% do coeficiente principal) é reportado como reforço de cautela. | §4.5, §5.1 |
| J3 | Fazer placebo de grupo com 500 reatribuições | `placebo-de-grupo` | S | 500 reatribuições aleatórias do rótulo de tratamento, preservando o desenho de 75 tratadas entre 341, com semente fixa e checkpoint verificado, para situar o coeficiente na distribuição do acaso. | §4.5, `code/caged/models/placebos.py` |
| J4 | Fazer jackknife sobre as 75 ocupações tratadas | `jackknife-ocupacional` | S | Remoção de cada ocupação tratada, uma por vez, para verificar se o resultado depende de poucas ocupações grandes. | §4.5, `code/caged/audit/jackknife_occupations.py` |
| J5 | Estimar quatro horizontes longos | `horizontes-longos` | S | O coeficiente estático é reestimado em quatro horizontes anuais do pós, e a estabilidade é declarada como diagnóstico, explicitamente não como teste de substituição. | §5.1, §6.3 |
| J6 | Decompor desligamentos por motivo | `mecanismos-de-desligamento` | S | Os desligamentos são decompostos por motivo como módulo de mecanismo, viabilizado porque `tipomovimentacao` é preenchido em 99,92% dos desligamentos. | §4.5, §C.2, `code/caged/models/separation_mechanisms.py` |
| J7 | Construir proxy cumulativo de fluxo líquido e validá-lo contra a RAIS | `proxy-fluxo-cumulativo` | S | Índice cumulativo de fluxo líquido normalizado pelo fluxo bruto pré-tratamento, com declaração explícita de que **não observa estoque**, e validação contra a RAIS que o classifica como concordante apenas em direção (mediana de nível 0,03; de variação 0,11). | §A.1 (Painel B.2), §D.1 |
| J8 | Testar salário-hora e jornada | `salario-hora-e-jornada` | S | Salário-hora (−0,0695) e horas semanais (+0,0016) são estimados para verificar se redução de jornada explicaria a queda do salário mensal — e o resultado é usado para descartar essa explicação mecânica. | §5.1, §A.2 |
| J9 | Reportar o porte do estabelecimento como nulo | `porte-do-estabelecimento` | P | Cinquenta modelos estimados, nenhum rejeitando após o ajuste de multiplicidade; o exercício é reportado como resultado nulo, não omitido. | §4.5 |
| J10 | Não executar o contraste público/privado | `publico-privado-nao-executado` | S | Decisão de não executar: os campos oficiais do CAGED codificam a forma de registro do vínculo, não a propriedade do empregador, então a distinção não é identificável na base. | §4.5 |
| J11 | Verificar sensibilidade a ausência e winsorização de salário | `sensibilidade-winsorizacao` | S | Módulos registrados de robustez cobrem missingness de salário e a escolha de winsorização, sem que nenhum possa sobrepor os portões de identificação. | RD, `config/analysis_registry.csv` |
| J12 | Auditar concentração e transferências | `auditoria-concentracao` | P | Auditorias declaradas de concentração ocupacional (uma família com 31,8% das admissões do grupo tratado; cinco maiores com 65,4%) e de participação de transferências, usadas para qualificar o que o coeficiente médio pode captar. | §6.3, §6.4, `code/caged/audit/` |

---

## 12. Bloco K — Decomposição salarial

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| K1 | Decompor o diferencial salarial por dois métodos | `decomposicao-salarial` | S | Método 1: ponderar os diferenciais dentro de faixas de escolaridade pelas participações pré-evento nas expostas (−0,03924; composição = 22,66%). Método 2: interagir o pós com quatro características pré-evento (−0,035998; 29,06%). | §5.1, §A.2 |
| K2 | Declarar que a decomposição não é identidade de Oaxaca | `decomposicao-nao-oaxaca` | P | Registra-se que o cálculo é aproximação e não identidade de Oaxaca, porque os modelos de cada faixa educacional têm seus próprios efeitos fixos. | §A.2 |
| K3 | Não atribuir a mudança de composição à IA | `composicao-sem-atribuicao` | P | O padrão é declarado compatível com redução relativa de oportunidades de entrada para trabalhadores com superior, mas explicitamente não atribuível à IA nem tratado como perda de poder de barganha. | §A.2 |

---

## 13. Bloco L — Casos ocupacionais

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| L1 | Definir seis casos semanticamente e congelá-los | `casos-ocupacionais` | S | Seis casos definidos a partir das descrições oficiais da CBO de seis dígitos, congelados antes da inspeção de resultados, reunindo 76 códigos sem sobreposição, com dicionário selado por SHA-256. | §4.4, §C.1 |
| L2 | Selecionar os casos independentemente da classificação da OIT | `selecao-independente-do-indice` | S | A seleção usa títulos e tarefas oficiais da CBO; a composição segundo a OIT é usada apenas na interpretação posterior, e nunca para reclassificar os casos. | §4.4, §C.1 |
| L3 | Tratar os casos como puramente descritivos | `casos-descritivos` | S | Não há grupo de controle por caso. Novembro de 2022 é normalizado em 1 e a medida citada é a média dos doze meses terminais (jun/2025–mai/2026) contra essa base; as figuras mostram trajetórias, não efeitos. | §C.1, §C.2 |
| L4 | Declarar o desequilíbrio do dicionário de casos | `desequilibrio-dos-casos` | P | Registra-se que 53 dos 76 códigos pertencem a um único caso (supervisores de produção), que 60 dos 80 mapeamentos têm confiança `medium` e que a cobertura da pontuação varia de 63,8% a 100% — e que por isso esse caso é o que menos suporta leitura substantiva. | §C.1 |
| L5 | Abandonar a decomposição da porta de entrada | `tipo-movimentacao-inviavel` | S | A decomposição das admissões entre primeiro emprego e recolocação é declarada inviável porque `tipomovimentacao` vem como "tipo ignorado" em 93,2% das admissões. Limitação da base, não do desenho. | §C.2 |

---

## 14. Bloco M — Exercícios complementares (RAIS e PNADc)

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| M1 | Enquadrar os complementares como medição, não identificação | `complementares-sem-causalidade` | P | Os exercícios de RAIS e PNADc são declarados medição complementar: nenhum coeficiente autoriza leitura causal e nenhum recebe marcação de significância. Composição não é transição de trabalhador. | §D (abertura), RD |
| M2 | Replicar o tratamento do CAGED na RAIS | `rais-mesmo-tratamento` | S | O painel anual da RAIS usa exatamente as 75 CBO4 expostas contra as 266 `Not Exposed`, com efeitos fixos de ocupação e ano e cluster por ocupação. | §D.1 |
| M3 | Escolher a janela 2019–2024 por diagnóstico de quebra | `rais-janela-2019-2024` | S | A janela é escolhida porque, na janela longa iniciada em 2016, a quebra de série da migração ao eSocial é **diferencial** entre tratados e controle e domina o painel; entre 2019 e 2024 deixa de ser. | §D.1 |
| M4 | Medir estoque em data fixa (31 de dezembro) | `rais-estoque-31-12` | S | O estoque é o de vínculos ativos em 31 de dezembro, com três desfechos declarados (estoque, rotatividade relativa, tempo médio de emprego). | §D.1 |
| M5 | Declarar uma sensibilidade como inexequível | `sensibilidade-inexequivel` | P | O estoque médio anual, alternativa declarada, exigiria resolver 2.749.713 meses de início e 316.377 de fim inativos que a fonte não determina; consta como **inexequível**, não como omitido, para não introduzir proxy não declarado. | §B.1 |
| M6 | Declarar a fragilidade do pretrend de rotatividade | `rotatividade-um-periodo` | P | Registra-se que a rotatividade dispõe de um único período anterior à referência, de modo que sua não rejeição **não é prova** de tendências paralelas. | §D.1, §B.1 |
| M7 | Excluir 2022T4 da análise PNADc | `pnadc-exclui-2022t4` | S | O trimestre do evento é excluído porque seria simultaneamente pré e pós; o pós vai de 2023T1 a 2026T1 sobre janela de 2012T1 a 2026T1. | §D.2 |
| M8 | Atribuir tratamento por regra de maioria a 3 dígitos | `pnadc-regra-de-maioria` | S | No braço de estoque, o rótulo de exposição é atribuído a grupo ocupacional de 3 dígitos por regra de maioria de 0,50 (32 tratados, 77 controle, 14 intermediários excluídos), com limiar alternativo de 0,75 como sensibilidade. | §D.2, §B.2 |
| M9 | Herdar exposição só por pareamento exato de 4 dígitos | `pnadc-pareamento-exato` | S | Apenas o pareamento exato de 4 dígitos com a ISCO-08 herda o rótulo (97,9% das observações); o restante recebe `Sem classificação` e fica fora da estimação. | §D.2 |
| M10 | Estimar dois braços independentes | `pnadc-dois-bracos` | S | Um braço individual no nível da observação (MQO ponderado) e um de estoque por grupo ocupacional e trimestre (PPML), com seis desfechos na família E. | §D.2 |
| M11 | Declarar que a inferência não implementa o plano amostral completo | `sem-desenho-amostral-completo` | S | Os erros-padrão são agrupados por grupo ocupacional e **não** implementam estratos e UPAs da PNAD Contínua. As estimativas pontuais usam o peso; a variância, não o plano inteiro. | §B.2 |
| M12 | Diagnosticar a quebra de coleta de 2020 como diferencial | `quebra-2020-diferencial` | S | A quebra de coleta de 2020 é diagnosticada como diferencial (até 3,39 pontos de distância entre expostos e controle), o que torna a especificação sem 2020 obrigatória por desenho, e ela é reportada. | §B.2 |
| M13 | Declarar a discordância RAIS × PNADc em vez de arbitrá-la | `discordancia-declarada` | P | Os dois estoques têm sinais opostos (−0,0429 na RAIS; +0,0420 na PNADc). A divergência é declarada, com a justificativa de que não medem o mesmo estimando e que escolher a que rejeita seria decidir pelo resultado. | §D.3, §6.1 |
| M14 | Usar o braço de estoque para afastar substituição por estrutura | `estoque-afasta-substituicao` | P | Como os diferenciais são positivos ao mesmo tempo para estoque informal, formal e total, a leitura de migração formal→informal é afastada por estrutura do resultado, e não por falta de precisão. | §D.2 |

---

## 15. Bloco N — Extensão espacial (negativo documentado)

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| N1 | Interromper o exercício espacial no portão de suporte | `extensao-espacial-interrompida` | S | O módulo municipal para antes de estimar qualquer coeficiente de tratamento, deixando as 12 posições da família F vazias, e é declarado como limitação de identificação, não evidência de efeito nulo. | §4.5, §B.3, RD |
| N2 | Declarar o diagnóstico de suporte como emenda | `emenda-de-suporte` | P | Declara-se que o diagnóstico que interrompeu o exercício **não integrava o desenho original**: foi adotado depois de o critério de continuidade original ser satisfeito, embora antes de qualquer número de suporte ser calculado. Consta como emenda, não como regra pré-registrada. | §B.3 |
| N3 | Manter a regra conservadora do conflito interno da emenda | `conflito-da-emenda` | P | A emenda previa tanto rebaixar um resultado frágil quanto interromper o exercício; a regra conservadora foi mantida precisamente para não escolher a alternativa mais permissiva depois de saber qual delas prendia. | §B.3 |
| N4 | Respeitar o piso de 10 UFs efetivas sem arredondar | `piso-de-ufs-efetivas` | S | O piso declarado era de 10 UFs efetivas; o segundo proxy ficou em 9,19 (SP com 25,7%) e o valor não foi arredondado, recalibrado nem substituído. | §B.3 (Tabela B.4) |
| N5 | Aceitar continuidade por margem estreita de um desfecho | `criterio-de-continuidade-estreito` | P | O critério de continuidade exigia que **um** desfecho não falhasse na pretendência; só o salário passou (p = 0,347) e o exercício prosseguiu por essa margem — declarada como estreita. | §B.3 |
| N6 | Corrigir e documentar erros da implementação anterior | `correcao-de-erros-espaciais` | P | Documenta-se que o corte de conectividade era calculado antes dos filtros da amostra (divisão ~80/20) e que a participação de fibra era lida na coluna errada; após a correção (328/329 municípios), as rejeições de placebo desapareceram. | §4.5 |
| N7 | Manter o benchmark de 8,61% como incompatível | `benchmark-incompativel` | P | O benchmark legado de 8,61% de declaração tardia é retido como **incompatível**, porque mistura eixo de ano-declaração com eixo de mês-fato, enquanto o construto registrado usa consistentemente o mês do fato assinado. A discrepância não é reparada redefinindo o denominador congelado. | RD |

---

## 16. Bloco O — Pré-registro, replicação e governança do processo

| # | Título | Slug | Tipo | Descrição da decisão | Onde consta |
| --- | --- | --- | --- | --- | --- |
| O1 | Pré-registrar desenho, famílias e regras de parada | `pre-registro-do-desenho` | P | Especificação principal, robustezes, tamanhos de família, rótulos de suporte e regras de parada são declarados por escrito antes da estimação, em todas as três frentes. | §4.5, §B.2, §D, RD |
| O2 | Proibir que uma estimativa nova substitua a referência assinada | `regra-anti-garimpo` | P | Regra explícita: uma estimativa nova não pode substituir a referência assinada apenas por parecer mais favorável. Vale para variantes de tratamento, especificações e medidas de exposição. | RD |
| O3 | Congelar insumos com verificação criptográfica | `insumos-congelados` | P | Todos os insumos brutos são congelados com hash SHA-256 registrado em `config/data_sources.csv` e manifests, e nenhuma consulta ao vivo ocorre durante a estimação. | §B.4, `config/data_sources.csv` |
| O4 | Replicar de forma independente em R | `replicacao-independente-r` | P | Python constrói insumos analíticos sem coeficientes e contratos de modelo; R 4.4.1 (`fixest`) recalcula independentemente agregados da Seção 3, estimativas nacionais e setoriais, famílias A–E, coeficientes de event time, pretendências e placebos espaciais. | RD, §B.4, `R/complete_replication.R` |
| O5 | Declarar tolerâncias numéricas de equivalência | `tolerancias-declaradas` | P | Coeficientes e erros-padrão devem diferir em no máximo 1e-6; p-valores derivados usam 2e-5 absoluto; Wald conjunto usa 1e-6 absoluto + 1e-3 relativo; contagens, amostras, status, rank e flags PSD devem coincidir exatamente. | RD |
| O6 | Não importar p-valores da replicação | `sem-importacao-de-p` | P | Nenhum p-valor é importado da replicação em R e nenhuma família é reajustada a partir dela. | §B.4 |
| O7 | Manter registro de artefatos como autoridade computacional | `registro-de-artefatos` | P | A autoridade é o registro de 53 publicações em `config/manuscript_artifacts.csv`, com as quantidades narrativas enumeradas separadamente em `config/numeric_claims.csv` e reconciliadas com os dados. | RD, `config/` |
| O8 | Exigir nove portões antes de liberar a versão | `nove-gates-de-release` | P | Release exige: 53 publicações exatas; reconciliação de todas as quantidades narrativas; `reproduce` offline; rebuild `full` das fontes oficiais; duas execuções determinísticas; validação Python–R completa sem linha silenciosamente pulada; ausência de caminho absoluto ou dependência externa; preservação byte a byte da V1; e auditoria Referee 2 independente. | RD |
| O9 | Preservar a V1 byte a byte | `preservacao-v1` | P | A V1 do pacote é preservada sem alteração, de modo que o refactor mude empacotamento e validação, não especificações, amostras, famílias ou estimativas aceitas. | RD |
| O10 | Submeter o trabalho a auditoria externa antes da liberação | `auditoria-referee2` | P | Uma auditoria Referee 2 independente é requisito de liberação, com a correspondência mantida no repositório. | RD, `correspondence/referee2/` |

---

## 17. Sumário quantitativo

| Bloco | Tema | Decisões |
| --- | --- | --- |
| A | Mensuração da exposição | 9 |
| B | Base descritiva (PNADc) | 10 |
| C | Fonte e construção do painel CAGED | 14 |
| D | Crosswalk e tratamento | 14 |
| E | Evento e estrutura temporal | 4 |
| F | Especificação econométrica | 12 |
| G | Heterogeneidade | 10 |
| H | Multiplicidade | 8 |
| I | Portões de identificação | 11 |
| J | Robustez e placebos | 12 |
| K | Decomposição salarial | 3 |
| L | Casos ocupacionais | 5 |
| M | Exercícios complementares | 14 |
| N | Extensão espacial | 7 |
| O | Pré-registro e replicação | 10 |
| **Total** | | **143** |

Distribuição por tipo: **77 substantivas** (afetam o estimando ou a estimativa) e **66 procedimentais** (afetam credibilidade, transparência ou reprodutibilidade).

---

## 18. Observações do levantamento

Quatro coisas que apareceram ao montar o inventário e que valem registro antes da fase de avaliação.

**1. Há decisões que só existem no código ou no contrato, não no texto.** A distribuição t de cluster com G−1 graus de liberdade (`inferencia-cluster-t`), o limiar de rank (`diagnostico-rank-psd`), a grade M do HonestDiD (`honestdid-rambachan-roth`), a semente do placebo de grupo (`placebo-de-grupo`) e o determinismo do painel (`determinismo-do-painel`) estão em `RESEARCH_DESIGN.md` ou nos módulos, mas não na dissertação. Na avaliação vale decidir quais precisam subir para o texto.

**2. A proporção de decisões procedimentais é alta (46%).** Isso é consequência do desenho ter falhado nas tendências paralelas: boa parte do trabalho metodológico se deslocou de identificar um efeito para delimitar e documentar o que não se pode afirmar. Não é defeito do inventário — é o perfil do trabalho.

**3. Três decisões são de *não fazer*, e estão declaradas como tal.** `publico-privado-nao-executado`, `sensibilidade-inexequivel` e `familia-f-vazia`. Somam-se a `tipo-movimentacao-inviavel` e `extensao-espacial-interrompida`. Esse conjunto é atipicamente bem documentado e provavelmente é um ponto forte a defender, não a esconder.

**4. Duas decisões concentram o risco de crítica externa.** `confusao-escritorio-vs-ia` (a fronteira do índice coincide com a fronteira escritório/não-escritório) e `janela-2021-2026` (nenhum mês pré-pandemia no pré-período) são as duas que o próprio texto identifica como estruturais e insolúveis dentro do desenho. Elas devem entrar na avaliação com prioridade, porque são as que uma banca atacaria primeiro.

---

## 19. Como será a fase de avaliação

Proposta de critérios para a próxima etapa, a aplicar decisão por decisão via slug:

| Critério | Pergunta |
| --- | --- |
| **Justificação** | A decisão está justificada no texto, ou apenas implementada? |
| **Alternativa** | A alternativa foi considerada, e o custo de tê-la rejeitado está reportado? |
| **Momento** | Foi tomada antes ou depois de ver resultados? Está declarada como tal? |
| **Sensibilidade** | Existe teste que mostre quanto o resultado depende dela? |
| **Direção do viés** | Se a decisão estiver errada, para que lado o resultado se move? |
| **Defensabilidade** | Sobrevive à pergunta mais dura que uma banca faria? |

Veredito sugerido por decisão: `sólida` · `justificada mas subdocumentada` · `frágil e reportada` · `frágil e não reportada` · `revisar`.

Sugestão de ordem de ataque: **Bloco I** (portões de identificação) → **Bloco D** (crosswalk e tratamento) → **Bloco C** (janela e construção) → **Bloco F** (especificação) → **Bloco H** (multiplicidade) → o resto.
