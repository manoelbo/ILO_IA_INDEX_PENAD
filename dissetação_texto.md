# 1 Introdução

## 1.1 Sumário

Essa dissertação tem como objetivo investigar a exposição do mercado de trabalho brasileiro à inteligência artificial e seus efeitos iniciais sobre o emprego formal. Para isso, dividi a análise de dados em duas etapas.

Na primeira etapa, cruzei os microdados da Pesquisa Nacional por Amostra de Domicílios Contínua (PNADc, 3º trimestre de 2025) ao índice de exposição ocupacional da Organização Internacional do Trabalho (Gmyrek et al., 2025). A combinação desses dois dados permitiu analisar o grau de exposição de 97,8 milhões de trabalhadores e identificar que 10,1% da força de trabalho está em ocupações altamente expostas, com concentração entre trabalhadores administrativos, mulheres, brancos e indivíduos com maior escolaridade, padrões consistentes com países de renda média-alta na avaliação global da OIT.

Na segunda etapa, segui a abordagem empírica de Brynjolfsson, Chandar e Chen (2025), que explora a variação do índice de exposição ocupacional para identificar efeitos sobre o emprego formal nos EUA. Adotei um design de diferenças em diferenças aplicado a dados administrativos brasileiros (CAGED), usando o lançamento do ChatGPT como evento e o índice de exposição da OIT como fonte de variação no tratamento. Os resultados indicam que ocupações altamente expostas apresentaram queda estatisticamente significativa nos salários reais de admissão de aproximadamente 3,4%, impulsionada quase inteiramente por trabalhadores jovens (queda de 13,4%), sem efeito significativo sobre os volumes de admissões ou desligamentos. Esses efeitos salariais são robustos a cutoffs alternativos de exposição e testes de placebo, e são amplificados em municípios com maior conectividade de banda larga.

Os resultados sugerem que a inteligência artificial já está remodelando o mercado de trabalho brasileiro, com consequências distributivas que recaem desproporcionalmente sobre os entrantes mais jovens no mercado de trabalho formal.

## 1.2 Panorama

O alto volume de dados produzidos na era digital, combinado à evolução da capacidade computacional, abriu espaço para que uma nova geração de cientistas da computação desenvolvesse algoritmos e modelos de inteligência artificial capazes de realizar tarefas até então exclusivas da cognição humana. Entre esses modelos,  o ChatGPT 3.5, lançando em novembro de 2022,  se destacou por representar um salto qualitativo na capacidade dos LLMs (Modelos de Linguagem de Grande Escala). Pela primeira vez, um modelo de uso geral conseguiu realizar tarefas de classificação e interpretação de texto, tradução e escrita de forma fluída e adaptativa. Esse resultado foi possível graças a uma combinação de avanços acumulados ao longo de anos: a arquitetura Transformer (Vaswani et al., 2017), que substituiu as redes recorrentes e viabilizou o processamento paralelo de linguagem em escala, e o RLHF (Reinforcement Learning from Human Feedback), técnica que usa avaliações humanas para alinhar as respostas do modelo às expectativas dos usuários, extendendo a funcionalidade da tecnologia para uso geral . Sua repercussão impulsionou uma nova corrida de desenvolvimento, alimentada também pela consolidação das *scaling laws* (Kaplan et al., 2020): a descoberta empírica de que mais dados e mais investimento em capacidade computacional produzem modelos sistematicamente melhores, criando um incentivo estrutural para que empresas e países competissem para escalar essa tecnologia o mais rápido possível. Ao longo desta dissertação, o termo *inteligência artificial* se refere especificamente a essa geração de modelos que ganhou escala e visibilidade pública a partir do lançamento do ChatGPT 3.5. 

Essa corrida encontrou terreno fértil. A difusão da inteligência artificial entre a população geral foi rápida e sem precedentes históricos comparáveis: nos Estados Unidos, estima-se que 32,1% dos trabalhadores já integravam ferramentas de IA em suas rotinas até o final de 2024, num ritmo de adoção comparável ao do computador pessoal na década de 1980 e superior, em termos populacionais, ao da própria internet (Bick, Blandin e Deming, 2025). Os anos seguintes ao lançamento do ChatGPT foram marcados pelo surgimento de modelos progressivamente mais capazes, com impacto transversal sobre setores e ocupações, o que ampliou o debate acadêmico e público sobre os desdobramentos da tecnologia. No âmbito da literatura econômica, dois temas se consolidaram como objetos centrais de investigação empírica: o impacto sobre a produtividade e os efeitos sobre o mercado de trabalho.

Alguns estudos que investigam o efeito da inteligência artificial em áreas específicas, como desenvolvimento de software e atendimento ao consumidor, encontraram ganhos de produtividade entre 14% e 26% (Stanford Institute for Human-Centered AI, Artificial Intelligence Index Report 2026). No entanto, até a data de conclusão desta dissertação, a evidência empírica disponível não identifica efeitos estatisticamente significativos da inteligência artificial sobre a produtividade agregada ou o crescimento do PIB. Acemoglu (2025) estima que o impacto da IA sobre a produtividade total dos fatores será de, no máximo, 0,53% a 0,66% ao longo de uma década, o equivalente a cerca de 0,06 ponto percentual ao ano. Esse padrão configura o que pode ser descrito como um novo paradoxo de Solow: apesar da rápida difusão da tecnologia, seus efeitos sobre a produtividade agregada ainda não aparecem nos dados macroeconômicos.

O quadro é distinto quando se observa o mercado de trabalho. Nesse caso, a evidência empírica de efeitos já detectáveis é mais robusta: estudos recentes nos Estados Unidos e no Reino Unido convergem para a conclusão de que o impacto da IA está se manifestando principalmente pela porta de entrada do mercado de trabalho, com recém-formados e trabalhadores jovens em ocupações com alta exposição à IA recebendo salários menores e enfrentando menor oferta de postos de trabalho (Brynjolfsson, Chandar e Chen, 2025; Lichtinger e Hosseini Maasoum, 2025; Klein Teeselink, 2025). Esta dissertação documenta o mesmo padrão no mercado brasileiro, contribuindo para essa literatura.

# 2 Contexto Metodológico

## 2.1 Índices de exposição à IA

Para identificar quais ocupações são afetadas por essa nova onda de inteligência artificial e em que grau, grupos acadêmicos e centros de pesquisa começaram a desenvolver **índices de exposição à IA**, uma medida que agrega diferentes informações em uma análise do quanto cada tarefa de trabalho está exposta à IA, para ao final atribuir uma pontuação que dimensiona o potencial de impacto da tecnologia sobre cada posto de trabalho.

Esses índices são construídos por metodologias distintas, mas compartilham uma estrutura comum: produzem um valor contínuo, tipicamente entre 0 e 1, onde 0 indica ausência de exposição e 1 indica exposição máxima, e são associados a classificações ocupacionais padronizadas já existentes, o que permite que os índices sejam integrados a microdados de pesquisas domiciliares e registros administrativos para análises populacionais.

O índice mais influente da literatura é o **GPT Exposure**, desenvolvido por Eloundou et al. (2023) em parceria entre a OpenAI, criadora do ChatGPT, e a Universidade da Pensilvânia. Esse trabalho aproveitou a própria capacidade de análise do LLM para avaliar milhares de tarefas e estabeleceu a metodologia de referência do campo. A partir desse trabalho, outros grupos produziram índices alternativos, refinando a metodologia ou se adaptando a classificações ocupacionais específicas. A análise comparativa desenvolvida nesta dissertação é fundamentada nesses quatro índices: o **GPT Exposure** (Eloundou et al., 2023), o **ILO Global Index** (Gmyrek et al., 2025), adotado como índice principal, o **GENOE** (Benítez-Rueda & Parrado, 2024) e o **Anthropic Economic Index** (Massenkoff & McCrory, 2026). Embora as escolhas metodológicas variem entre eles, todos compartilham a mesma base teórica, que exploramos na seção a seguir.

### 2.1.1 Pilares Teoricos

**Abordagem Baseada em Tarefas**

Os quatro índices usam como ponto de partida o trabalho seminal de David Autor (The Skill Content of Recent Technological Change: An Empirical Exploration, 2003), que estabelece que um emprego é baseado em um conjunto de tarefas. Novas tecnologias não impactam profissões diretamente, elas impactam as tarefas que constituem essas profissões. Esse conceito é fundamental tanto na hora de construir o índice, que começa avaliando o impacto no nível da tarefa, quanto para a discussão acadêmica mais ampla.

Um experimento com radiologistas ilustra bem esse ponto: os diagnósticos feitos por IA foram iguais ou tão precisos quanto os de dois terços dos médicos americanos (Agarwal et al., 2023). Mas quando destrinchamos o trabalho do radiologista, vemos que fazer o diagnóstico é apenas uma de muitas tarefas da profissão, que também exige coordenação de equipe, comunicação com médicos e interação com pacientes. Os avanços da tecnologia nessa área não tornam os radiologistas substituíveis justamente porque o diagnóstico é apenas uma parte do que eles fazem. Ao enxergar ocupações como um conjunto de tarefas que mudam e se adaptam, conseguimos ter uma visão mais complexa e realista do que pode acontecer com cada profissão e com o mercado de trabalho.

**Automação vs. Complementaridade** 

Outro conceito amplamente citado, também introduzido por David Autor, é o de **Automação vs. Complementaridade**, que nos ajuda a sair de uma visão binária em que tecnologias como robôs e IA simplesmente substituem trabalhadores. Na prática, há dois cenários possíveis:

**Automação:** a IA executa a tarefa sozinha, com a mesma qualidade e em menos tempo.

**Complementaridade:** o humano usa a IA para executar a tarefa com mais qualidade ou eficiência.

Um tradutor com foco em documentos empresariais pode ser substituído por uma automação com uso de inteligência artificial. Já um atendente ao cliente por telefone pode usar a IA para buscar e formular respostas melhores em tempo real, tornando o seu trabalho mais eficaz sem ser substituído por ela.

Quando falamos grau de exposição, não necessariamente estamos falando em automação.

**Tecnologia de Propósito Geral**

Para uma tecnologia ser considerada um Tecnologia de Propósito Geral (do inglês General-Purpose Technology) ela precisa reunir essas três características: Ela se espalha por diversos setores da economia, melhora continuamente ao longo do tempo e cria um ecossistema de inovações complementares ao seu redor. 

A máquina a vapor, a eletricidade e a internet são os exemplos mais citados. O que elas têm em comum é que seus efeitos não foram imediatos: levaram décadas para se consolidar, porque exigiram que empresas e trabalhadores reinventassem seus processos para aproveitar todo o potencial da tecnologia.

Uma das hipóteses que os índices de exposição buscam testar é justamente essa: a IA generativa e os LLMs estão agindo como a Tecnologia de Propósito Geral da nossa era. 

A visão da inteligência artificial como uma Tecnologia de Propósito Geral foi debatida principalmente no **GPT Exposure** e também é mencionada nos outros índices, servindo como um argumento importante para destacar sua relevância diante de uma mudança estrutural no mercado e na economia.

### 2.1.2 Pilares Metodológicos

Como esses índices são construídos na prática? Apesar das diferenças entre eles, há três pilares metodológicos que convergem e representam o que há de mais avançado em economia do trabalho e tecnologia.

**Taxonomias Ocupacionais Estruturadas**

Os índices de exposição dependem de um trabalho prévio de catalogação de profissões e tarefas que já existe em escala nacional e internacional. O **GPT Exposure**, o **GENOE** e o **Anthropic Economic Index** se apoiam na base de dados **O*NET**, mantida pelo governo americano, que reúne mais de 900 ocupações e 18.000 descrições de tarefas. A OIT segue um caminho diferente: utiliza a **ISCO-08**, a classificação ocupacional internacional da ONU, que contempla 436 ocupações, complementada pela taxonomia polonesa de 6 dígitos, que expande o dicionário para quase 30.000 tarefas. Como veremos mais para frente, o Brasil adota a sua própria classificação ocupacional, a CBO, que guarda maior afinidade estrutural com a ISCO-08 do que com a O*NET. 

**Avaliação Baseada em LLMs**

Como classificar a impacto de IA em dezenas de milhares de tarefas? Os primeiros índices, anteriores ao **GPT Exposure,** dependiam inteiramente de avaliações humanas: Felten et al. (2018, 2021) contrataram 2.000 trabalhadores pelo Amazon Mechanical Turk para julgar, tarefa por tarefa, se a IA conseguiria realizar habilidades específicas. A ruptura metodológica veio com o **GPT Exposure** (Eloundou et al., 2023), que passou a usar a própria IA para fazer essa avaliação. Para validar essa abordagem, os pesquisadores coletaram classificações em paralelo, tanto de anotadores humanos quanto do GPT-4, e observaram uma concordância de mais de 80% entre as duas fontes. Esse resultado estabelece que LLMs são avaliadores confiáveis para essa tarefa, abrindo caminho para que os índices seguintes a mesma abordagem.

O **GENOE** (2024) alterou o prompt fornecido ao modelo: em vez de avaliar tarefas isoladas, passou a oferecer ao LLM o contexto completo da ocupação, como nome, conjunto de tarefas e implicações sociais, permitindo que a IA fizesse uma avaliação holística. É essa abordagem que captura, por exemplo, a diferença entre um juiz e um analista de crédito: embora ambos analisem grandes volumes de informação, o peso ético e o impacto social do papel do juiz reduzem sua exposição à IA de forma que uma análise tarefa a tarefa jamais revelaria. 

Já o **ILO Global Index** (Gmyrek et al., 2025) desenvolveu a metodologia mais sofisticada entre os quatro índices. A lógica foi construir primeiro um gabarito de alta qualidade, validado por humanos, para depois escalar a classificação com uso de  modelos de linguagem.

O processo funcionou da seguinte maneira: os pesquisadores extraíram uma amostra representativa de tarefas e submeteram essa amostra a três camadas de validação. Na primeira, 1.640 trabalhadores reais avaliaram o potencial de automação das tarefas da sua própria área de atuação. Na segunda, um painel de especialistas revisou um subconjunto de 608 tarefas para corrigir vieses e avaliar a viabilidade prática da automação no mundo real. Na terceira, nos casos em que trabalhadores e especialistas discordavam, os modelos GPT-4o e Gemini Flash 1.5 foram usados como um mecanismo de desempate.

O objetivo dessa validação não era classificar todas as tarefas, era criar uma base de referência confiável. Com esse gabarito pronto, os pesquisadores usaram os LLMs para predizer a exposição das tarefas restantes da amostra e, em seguida, das 3.265 tarefas da ISCO-08 global. É esse processo, de alimentar a IA com julgamento humano antes de deixá-la escalar, que torna o ILO Global Index o mais robusto entre os quatro avaliados nesta dissertação.

**A Definição Métrica de Exposição**

A forma de pontuar a exposição também evoluiu ao longo do tempo. No **GPT Exposure** (Eloundou et al., 2023), a avaliação era essencialmente categórica: a pergunta central era se a IA conseguia reduzir o tempo necessário para um humano concluir uma tarefa em pelo menos 50%, mantendo uma qualidade consistente. Com base nisso, cada tarefa era classificada em uma de três categorias: sem exposição, com exposição direta ou com exposição via software complementar.

O **Anthropic Economic Index** (Massenkoff & McCrory, 2026) avança ao substituir essa lógica binária por cinco "primitivas econômicas" que buscam entender não apenas *se* a IA é usada, mas como ela atua no mercado de trabalho. Duas dimensões são centrais: a **autonomia**, que mede o grau em que os usuários efetivamente delegam a tomada de decisão para a máquina, de uma colaboração ativa até a delegação total, e a **taxa de sucesso da tarefa**, que avalia se a IA consegue completar o trabalho de forma eficaz. Esse índice é elaborado pela Anthropic, que é proprietária de um dos modelos de LLM mais usados no mercado, e se baseia em dados reais de uso dos usuários.

O **ILO Global Index** (Gmyrek et al., 2025) vai em outra direção: em vez de trabalhar apenas com a média das pontuações das tarefas de uma ocupação, incorpora também o desvio padrão como medida de variância. O argumento é que olhar apenas para a média deforma a realidade. Se um advogado tem tarefas com pontuação 0,9 e outras com 0,1, a média pode ser moderada, mas a variância revela que a profissão será profundamente *transformada*, com parte das suas tarefas automatizadas e outra parte inalterada, em vez de ser extinta ou totalmente preservada. É essa combinação de média e desvio padrão que gera os quatro gradientes de exposição da OIT (1 a 4): profissões com média moderada, mas alta variabilidade entre tarefas, são classificadas nos gradientes intermediários e tendem a exigir adaptação profunda dos trabalhadores, sem desaparecer do mercado.

### 2.1.3 Escolha de índice e adaptação para t**axonomia brasileira.**

A análise dos índices foi importante não só para entender a base teórica e como eles funcionam, mas também para avaliar qual deles se aplica melhor ao mercado de trabalho brasileiro e aos objetivos desta dissertação. O índice escolhido foi o ILO Global Index, por dois motivos principais: compatibilidade taxonômica e robustez metodológica.

O primeiro motivo é que o ILO Global Index é o único dos quatro estruturado em torno da ISCO-08, a Classificação Internacional Padrão de Ocupações. Isso é relevante porque o sistema ocupacional brasileiro é compatível com a ISCO. A PNAD Contínua, principal pesquisa domiciliar do IBGE, utiliza a COD (Classificação de Ocupações para Pesquisas Domiciliares), que é derivada da ISCO-08. Já os registros administrativos, como o CAGED e a Carteira de Trabalho, utilizam a CBO (Classificação Brasileira de Ocupações), cuja revisão de 2002 foi estruturada com base na ISCO-88, a versão anterior da classificação internacional. A ISCO-88 e a ISCO-08 compartilham a mesma lógica hierárquica e possuem tabelas de correspondência oficiais, o que viabiliza o mapeamento entre a CBO e o índice da OIT. Os três outros índices, por sua vez, são baseados na O*NET americana, o que exigiria uma etapa adicional de conversão para a taxonomia brasileira, com maior risco de perda de precisão.

O segundo motivo é a robustez do processo de construção do índice. O GPT Exposure, apesar de ser um trabalho pioneiro, teve sua metodologia rapidamente superada por trabalhos subsequentes que aprofundaram a abordagem. O GENOE, desenvolvido por pesquisadores do Banco Interamericano de Desenvolvimento (BID), adota uma classificação mais holística ao pedir que o modelo reflita sobre barreiras sociais e institucionais, o que pode ser relevante para o contexto brasileiro. No entanto, o GENOE é baseado essencialmente na geração de dados sintéticos, sem a participação de profissionais e especialistas que caracteriza o ILO Global Index. O Anthropic Economic Index traz uma contribuição relevante ao usar dados reais de uso dos seus modelos e mensurar dimensões como autonomia e taxa de sucesso, mas carrega um viés de amostragem: representa apenas os usuários dos modelos da Anthropic, o que limita a generalização dos seus resultados para o conjunto mais amplo do mercado de trabalho.

# 3 Análise Descritiva

Este capítulo apresenta a análise descritiva da exposição do mercado de trabalho brasileiro à inteligência artificial generativa. A base analítica e os principais resultados foram obtidos ao integrar os microdados da PNAD Contínua ao índice de exposição da OIT, o que permitiu produzir o conjunto de análises descritivas, decomposições, regressões multivariadas e testes de robustez aqui reportados. 

## **3.1 Construção da base analítica**

A base analítica desta etapa combina os microdados da PNADc do 3º trimestre de 2025, produzida pelo IBGE, ao **ILO Global Index** (Gmyrek et al., 2025). Da pesquisa, selecionei 14 variáveis cobrindo características demográficas, ocupacionais, salariais e de jornada. As observações passaram por filtros conservadores: remoção de dados faltantes críticos, restrição à faixa etária de 18 a 65 anos e exclusão de códigos de ocupação inválidos. O resultado final representa 97,8 milhões de trabalhadores ocupados, ponderados pelo peso amostral V1028. Para o índice, utilizei a planilha publicada pela OIT no site do Working Paper 140, que contém scores de exposição mapeados para 427 ocupações ISCO-08, com a classificação oficial em seis gradientes construída a partir da combinação de média e desvio padrão dos scores por tarefa.

A ponte entre os dois conjuntos de dados é o *crosswalk* entre a COD (classificação da PNADc) e a ISCO-08, e este é um dos momentos metodologicamente mais frágeis do trabalho. Não existe uma tabela oficial de correspondência entre as duas classificações, nem uma convenção estabelecida ou um padrão consagrado para esse tipo de conversão. Cruzamentos entre taxonomias construídas de forma independente nunca são perfeitos e exigem que cada pesquisa analise as estruturas disponíveis, busque alternativas e construa sua própria estratégia de mapeamento. No caso da COD, o ponto de partida é favorável: como ela é derivada da ISCO-08 e compartilha a mesma estrutura hierárquica de quatro dígitos, a correspondência direta funciona para a grande maioria dos casos. Nos casos sem match exato, adotei uma estratégia hierárquica de fallback, buscando correspondência a 3 e depois a 2 dígitos e atribuindo o score médio do subgrupo. Na prática, 97,9% das observações encontraram correspondência exata, e a cobertura final ficou em 99,2%. As falhas residuais foram mitigadas e os testes de robustez confirmaram que não afetam os resultados.

**Tabela 3.1 — Ficha técnica da base analítica final**

| **Item** | **Valor** |
| --- | --- |
| Fonte | PNADc 3T/2025 (IBGE) + ILO WP140 (Gmyrek et al., 2025) |
| Universo | População ocupada de 18–65 anos com código de ocupação válido |
| Observações na amostra | 207.901 |
| População representada | 97,8 milhões |
| Unidades federativas | 27 |
| Ocupações ISCO-08 | 427 |
| Ocupações COD com match | 422 (de 428 presentes na PNAD) |
| Cobertura de score (% pop.) | 99,2% |
| Match a 4 dígitos | 97,9% |
| Match a 3 dígitos | 1,3% |
| Sem classificação | 0,8% |
| Setores agregados (CNAE Dom. 2.0 → seções A–T) | 17 |
| Salário mínimo de referência | R 1.518 (Decreto 12.342/2025) |
| Peso amostral | V1028 (projeção populacional trimestral) |

## **3.2 Panorama da exposição no mercado brasileiro.**

A exposição média do mercado de trabalho brasileiro à Inteligência Artifical, ponderada pelos pesos amostrais da PNADc, é de 0,278 [IC 95%: 0,278 — 0,278]. Mas a metodologia sugerida pelo ILO Global Index vai além da média simples: ela organiza as ocupações em gradientes de exposição. A formulação do gradiente cruza a nota média de exposição da profissão (*μ*) com a variabilidade das suas tarefas (*σ*). A lógica é direta: o impacto da IA tende a ser maior quando uma profissão concentra tarefas de alta exposição e apresenta baixa variabilidade. Quando a média é alta, mas existe uma variedade de tarefas pouco impactadas pela IA, a tendência é que a profissão seja mais resiliente. Essa formulação também ajuda a distinguir os casos de complementaridade dos de automação.

**Tabela 3.2 — População ocupada por gradiente de exposição à IA e critério de agrupamento do ILO**

| **Gradiente** | **População (milhões)** | **%** | **Critério**  |
| --- | --- | --- | --- |
| Não exposto | 52,2 | 53,9 | Não cumprem nenhuma das condições dos Gradientes 1–4 ou de Exposição mínima. |
| Exposição mínima | 15,2 | 15,7 | μ **<** 0,5 **e** μ+σ **>** 0,4 |
| Gradiente 1 | 8,7 | 9,0 | μ **<** 0,4 **e** μ+σ ≥ 0,5 |
| Gradiente 2 | 10,0 | 10,3 | 0,4 ≤ μ **<** 0,5 **e** μ+σ ≥ 0,5 |
| Gradiente 3 | 4,8 | 4,9 | 0,5 ≤ μ **<** 0,6 **e** μ+σ ≥ 0,5 |
| Gradiente 4 | 5,0 | 5,1 | μ ≥ 0,6 **e** μ−σ ≥ 0,5 |
| Sem classificação | 1,0 | 1,1 | Amostra com score atribuído por agregação ISCO; gradiente não reportado pelo WP140 nesse nível de match (~1,1% da população com score). |

**Figura 3.1 — Distribuição da exposição à IA generativa no Brasil.**

![image.png](attachment:e293fd6c-05a8-47c8-8aca-b0ee093f3113:image.png)

> A Figura 3.1: histograma ponderado de scores com a curva KDE sobreposta. Como podemos ver, há cenários em que diferentes gradientes aparecem para a mesma média de exposição. Entre 0,2 e 0,4, o impacto da IA pode variar nessa população.
> 

**Figura 3.2 — Composição da população ocupada por faixa de score de exposição à IA generativa, segundo o grande grupo ocupacional**

![image.png](attachment:de6695ff-4024-40a3-aea8-e9e92f611c5d:image.png)

> A Figura 3.2:  Há uma moda clara em torno de 0,12–0,18, que corresponde a ocupações elementares, na industria ou na agropecuária, e uma cauda secundária por volta de 0,55–0,65, formada principalmente pelo apoio administrativo.
> 

**Figura 3.3 — População ocupada por gradiente de exposição à IA generativa** 

![image.png](attachment:e93045d7-4c12-4607-a627-7af181fbbc5c:image.png)

A leitura por gradiente é o resultado central desta seção. Mais da metade da força de trabalho brasileira (53,9%, ou 52,2 milhões) está em ocupações classificadas como "Não Expostas", predominantemente ocupações elementares, da agropecuária, da construção e da indústria de transformação tradicional. Outros 15,7% (15,2 milhões) estão em "Exposição Mínima". Os Gradientes 1 e 2, onde a OIT considera mais provável que a IA generativa complemente o trabalho humano (*augmentation*), reúnem 9,0% e 10,3% da população, respectivamente. Já os Gradientes 3 e 4, onde a IA tende a transformar profundamente as tarefas ou substituí-las, somam 9,8 milhões de trabalhadores, ou 10,1% da força de trabalho ocupada.

A OIT estimou a proporção de trabalhadores com alta exposição à Inteligência Artificial  (Gradientes 3 e 4) para diferentes grupos de países, o que permite uma comparação informativa com os dados encontrados neste estudo. A taxa de trabalhadores altamente expostos no Brasil (10,1%) fica ligeiramente acima da estimativa global da OIT (7,5%) e do padrão projetado para países de renda média-alta (7,0%). No entanto, a distância é expressiva quando comparamos o mercado brasileiro às economias de alta renda, onde a alta exposição atinge 17,3% da força de trabalho. Essa diferença reflete a estrutura ocupacional do país, caracterizada por um peso ainda expressivo de ocupações em setores de baixa exposição tecnológica, como a indústria de transformação tradicional e a agropecuária

**Tabela 3.3 — Comparação Brasil × WP140 (por grupo de renda)**

| **Indicador** | **Brasil (este estudo)** | **High-Income (WP140)** | **Upper-Middle (WP140)** | **Lower-Middle (WP140)** | **Low Income (WP140)** | **Global (WP140)** |
| --- | --- | --- | --- | --- | --- | --- |
| **Exposição média** | 0,278 | N/D* | N/D* | N/D* | N/D* | 0,29* |
| **% Fora dos Gradientes 1 a 4 (Não Exposto + Mínima)** | 69,6%** | 66% | 75% | 80% | 89% | 76% |
| **% Alta Exposição (G3–G4)** | 10,1% | 17,3% | 7,0% | 3,8% | 1,2% | 7,5% |

> 
> 
> 
> *\* O relatório da OIT (WP140) não informa a média de exposição subdividida por faixa de renda dos países; o valor de 0,29 refere-se à média ocupacional geral das avaliações em 2025.*
> 
> *\**  Para fins de comparação com os dados globais que não segregam os níveis de base, o valor do Brasil (69,6%) representa a soma das categorias "Não Exposto" (53,9%) e "Exposição Mínima" (15,7%).*
> 
> *Os dados de porcentagem de emprego do WP140 foram extraídos do "Figure 20: Global estimates of occupations potentially exposed to GenAI" (Total).*
> 

## **3.3 Distribuição Setorial e Regional de trabalhadores em Alta Exposição.**

No Anexo 1.1 tem uma tabela com a média e o gradiente para cada profissão com base no CBO, mas para deixar mais ilustrativo, abaixo estão as 5 ocupações com a maior média de exposição.

Isso ajuda a entender um ponto comum entre as analises feias através de indices de exposição: as ocupações mais impactadas pela inteligência artificial tendem a ser as chamadas *white collar* (em português, “trabalhos de colarinho branco”). O termo é amplamente usado na literatura internacional e acredita-se que tenha surgido no começo do século XX. “Colarinho branco” remete ao status de quem não precisa “sujar as mãos” e pode usar uma camisa branca no trabalho, associado a funções administrativas de escritório, ligadas a tarefas rotineiras e repetitivas e, em geral, a maior renda e maior escolaridade. 

**Tabela 3.4 — Top 5 ocupações COD em alta exposição (Gradientes 3 e 4)**

| **COD** | **Ocupação (descrição ISCO-08)** | Exposição Média | **Pop. (milhões)** | **Grande grupo** |
| --- | --- | --- | --- | --- |
| 4110 | Auxiliares de escritório em geral | 0,60 | 3,75 | Apoio administrativo |
| 4226 | Caixas, bilheteiros e atendentes em estabelecimentos | 0,57 | 1,04 | Apoio administrativo |
| 2411 | Contabilistas | 0,51 | 0,59 | Profissionais das ciências |
| 4120 | Secretários administrativos e executivos | 0,58 | 0,50 | Apoio administrativo |
| 2431 | Profissionais de marketing, propaganda e relações públicas | 0,55 | 0,43 | Profissionais das ciências |

O trabalho *white collar* descrito acima existe em todos os setores da economia, sem exceção. Uma indústria tem contabilidade e um hospital tem equipe administrativa. Por isso, é importante não olhar para a distribuição setorial como se apenas alguns setores fossem afetados pela IA: todos estão sendo impactados, em maior ou menor grau. 

Para a leitura setorial, proponho olhar os números com duas perceptivas: primeiro, a intensidade da exposição, qual proporção dos trabalhadores de um setor está em alta exposição; depois, o volume de trabalhadores, quantas trabalhadores desse setor estão em alta exposição.

Em intensidade, Finanças e Seguros lidera: 54,9% dos seus trabalhadores estão no gradiente 3  e 4. Quando mais da metade de um setor está no nível de maior exposição, isso é representativo de uma transformação em curso. Ainda é cedo para saber todos os efeitos, mas sem dúvida é um sinal que revela que alguns setores precisam de uma atenção melhor quando pensamos em políticas públicas.

Em volume, o destaque vai para Serviços Profissionais e Administração Pública, que juntos somam aproximadamente 2,39 milhões de trabalhadores em alta exposição. A relevância aqui não está tanto na proporção interna de cada setor, mas no número de pessoas em profissões com exposição alta, o que amplifica o potencial de impacto agregado sobre o mercado de trabalho.

**Tabela 3.5 — Exposição a IA  por setor CNAE-Domiciliar 2.0** (IBGE)**.**

Universo: ocupados classificaveis (~96M, excluindo 'Sem classificacao' do gradiente).

Setores: 19 categorias derivadas das **Secoes A-T da CNAE-Domiciliar 2.0** (IBGE),
agrupadas a partir da variavel V4013 da PNADC com zero-padding de 5 digitos.

| Setor | Total (M) | % BR | Exposição Média | Alta (M) | Alta (%) |
| --- | --- | --- | --- | --- | --- |
| Finanças e Seguros | 1.53 | 1.6 | 0.512 | 0.84 | 54.9 |
| Informação e Comunicação | 1.73 | 1.8 | 0.456 | 0.55 | 31.9 |
| Serviços Profissionais | 4.07 | 4.2 | 0.420 | 1.27 | 31.2 |
| Atividades Imobiliárias | 0.70 | 0.7 | 0.386 | 0.12 | 17.8 |
| Administração Pública | 4.27 | 4.5 | 0.352 | 1.12 | 26.3 |
| Comércio | 17.83 | 18.6 | 0.342 | 1.36 | 7.7 |
| Artes e Cultura | 1.10 | 1.1 | 0.316 | 0.10 | 9.4 |
| Saúde | 6.19 | 6.5 | 0.300 | 0.85 | 13.7 |
| Serviços Administrativos | 4.37 | 4.6 | 0.294 | 0.82 | 18.8 |
| Utilidades | 0.72 | 0.8 | 0.293 | 0.11 | 15.2 |
| Educação | 7.18 | 7.5 | 0.290 | 0.65 | 9.0 |
| Transporte | 5.72 | 6.0 | 0.280 | 0.46 | 8.0 |
| Alojamento e Alimentação | 5.09 | 5.3 | 0.266 | 0.23 | 4.4 |
| Ind. Extrativa | 0.59 | 0.6 | 0.262 | 0.04 | 6.4 |
| Ind. Transformação | 11.31 | 11.8 | 0.245 | 0.76 | 6.7 |
| Outros Serviços | 4.04 | 4.2 | 0.219 | 0.25 | 6.3 |
| Serviços Domésticos | 5.30 | 5.5 | 0.160 | 0.00 | 0.0 |
| Agropecuária | 6.97 | 7.3 | 0.155 | 0.06 | 0.8 |
| Construção | 7.23 | 7.5 | 0.146 | 0.18 | 2.5 |

## Glossario das colunas

- `Total (M)`: trabalhadores ocupados no setor, em milhoes.
- `% BR`: participacao do setor no total de ocupados classificaveis do Brasil.
- `Score medio`: media ponderada (pelo peso amostral) do score continuo de exposicao OIT (0 a 1).
- `Baixa`: Not Exposed + Minimal Exposure (ocupacoes pouco/nada expostas).
- `Moderada`: Gradients 1 + 2 (exposicao parcial; tarefas potencialmente complementadas pela IA).
- `Alta`: Gradients 3 + 4 (exposicao alta e consistente; tarefas potencialmente automatizadas).
- `Expostos`: soma de todos os trabalhadores em algum gradiente 1-4 (excluindo nao-expostos e exposicao minima).

Da mesma maneira que os 9,8 milhões de trabalhadores em alta exposição (Gradientes 3 e 4) não são “exlusivos” de um setor, esse grupo de espalha por todos os estados do país. O mapa abaixo ilustra essa distribuição, divulgando simultaneamente o volume absoluto e a proporção de trabalhadores em alta exposição em relação à força de trabalho de cada unidade federativa.

São Paulo concentra o maior contingente em termos absolutos: 2,8 milhões de trabalhadores, o que representa cerca de 12% da força de trabalho paulista. Esse resultado é esperado, o estado abriga a maior economia do país, com a maior concentração de sedes corporativas e serviços financeiros. Outros estados, como a Bahia, apresentam proporções consideravelmente menores, reflexo de uma estrutura ocupacional com maior peso de setores agrícolas, industriais e de serviços de baixa exposição.

O caso mais ilustrativo é o Distrito Federal. Apesar de ter uma força de trabalho relativamente pequena em termos absolutos, o DF apresenta a maior proporção de trabalhadores em alta exposição entre todas as UFs, consequência direta do seu perfil ocupacional: capital do país, com altíssima concentração de servidores públicos, analistas, profissionais técnicos e funções administrativas ligadas à máquina pública federal. É o caso em que a proporção diz mais do que o número absoluto.

A leitura combinada dos dois indicadores, volume e proporção, revela um fenômeno relevante para a agenda de políticas públicas. Embora a alta exposição à IA generativa não represente a maioria da força de trabalho em nenhum estado, sua distribuição capilar por todo o território nacional implica que os efeitos potenciais da tecnologia sobre o mercado de trabalho não se restringem a um polo econômico específico. Em estados onde a proporção de trabalhadores altamente expostos é maior,como o DF, Rio de Janeiro e São Paulo, políticas de requalificação, proteção salarial e monitoramento do emprego formal podem ter impacto proporcionalmente mais significativo sobre a satisfação ocupacional e a estabilidade do mercado de trabalho local.

**Figura 3.4 — Mapa com Alta Exposição a IA por estado.**

![image.png](attachment:3410ae5e-553a-4577-aed6-463d148d54c9:image.png)

## **3.4 Perfil sociodemográfico**

O perfil demográfica geral é claro e consistente com o WP140: mulheres, brancos, jovens e trabalhadores com mais escolaridade estão sistematicamente mais expostos.

### **3.4.1 Análise por Sexo**

![image.png](attachment:be72584a-ec5f-4be2-9fdd-3ddc197b68d4:7c9d0510-dd42-485a-99f5-5c38939958ad.png)

A exposição média das mulheres (0,303) é 0,044 ponto maior do que a dos homens (0,259), uma diferença relativa de +17% sobre a média masculina.Essa diferença é estatisticamente significativa (t = -1.473,7; p < 0,001). A leitura mais informativa não está na média, mas em como a população é destribuida entre os níveis de exposição: 14,5% das mulheres do mercado de trabalho (6,1 milhões) estão em alta exposição (G3-G4), contra 6,8% dos homens (3,6 milhões). Proporcionalmente, mulheres são 2,1 vezes mais expostas em alta exposição que homens. O trabalho analítico realizado pela OIT no desenvolvimento do índice WP140 (Seção 3.2) também indica que as mulheres estão significativamente mais expostas do que os homens. Em países de alta renda, 41% do emprego feminino está exposto.

### **3.4.2 Análise por Raça**

![image.png](attachment:ef4545d0-02af-4968-9a16-52ee00fffd7c:63487b0c-af82-47cd-a41b-47c4a7a09f4b.png)

O padrão racial é semelhante em magnitude, mas oposto em direção ao que se costuma esperar em análises de desigualdade: trabalhadores brancos têm exposição média de 0,305, contra 0,257 entre trabalhadores negros (pretos e pardos agregados, conforme Osorio, 2003), com gap de +0,048, uma diferença relativa de +19% sobre a média negra (t = 1.601,2; p < 0,001; d = 0,33). 

Em alta exposição, 12,5% dos brancos (5,2 milhões) estão expostos, contra 8,4% dos negros (4,5 milhões): brancos são 1,5 vez mais expostos em alta exposição que negros, mesmo sendo um contingente 11,9 milhões menor na força de trabalho ocupada (41,5 vs 53,4 milhões). 

A interpretação econômica conecta-se diretamente ao que foi visto anteriormente: as ocupações de alta exposição à IA são, em sua maioria, *white collar,* e no Brasil, esse tipo de trabalho está historicamente associado a maior renda e maior escolaridade. O país carrega um legado de desigualdade racial e a estrutura do mercado de trabalho forjada em séculos de escravidão, que concentrou e ainda concentra grande parte da população negra em ocupações elementares, da construção, dos serviços domésticos e da indústria de transformação, setores com alto volume de trabalhadores, baixa remuneração e baixa exposição à IA. O gap de exposição é o reflexo de uma segmentação ocupacional com raízes históricas profundas. 

### **3.4.3 Análise por Faixa Etária**

![image.png](attachment:18134332-88f2-4a27-a749-36cc9eb9f465:305f57f1-ea80-4489-b48f-1458e3b2b0e6.png)

A exposição decresce monotonicamente com a idade, partindo de 0,307 entre os 15-19 anos e caindo até 0,251 na faixa 55-59, uma diferença de 0,056 ponto, equivalente a +22% na faixa mais jovem em relação à mais velha. A diferença é ainda mais expressiva no segmento de alta exposição: a faixa 15-19 tem 3,2 vezes mais trabalhadores em alta exposição (19,0%) que a faixa 55-59 (5,8%). 

Trabalhadores jovens estão mais expostos por uma razão estrutural: eles ingressam preferencialmente em ocupações de apoio administrativo, vendas e serviços qualificados, justamente as mais expostas. Esse achado tem peso analítico relevante para a Etapa 2 desta dissertação, em que avalio se essa coorte mais exposta sofreu efeitos diferenciados após o lançamento do ChatGPT , um padrão já documentado por Brynjolfsson, Chandar e Chen (2025) nos EUA. 

### **3.4.4 Análise por Nível de Escolaridade**

O gradiente educacional é o mais forte de todos os recortes individuais. A exposição média sobe de 0,178 entre trabalhadores sem instrução ou com fundamental incompleto, para 0,274 entre os com médio completo (+54% em relação ao piso), 0,359 entre os com superior incompleto (+102%) e 0,364 entre os com superior completo (+105%), uma variação que mais que dobra a exposição ao longo da distribuição educacional. A interpretação é direta: escolaridade abre acesso a ocupações de escritório, profissionais e técnicas, e essas são as mais expostas à IA.

![image.png](attachment:bc60ec35-aa67-4e8f-ad52-3b662d104bac:7a88f2d4-6599-4c85-872e-1e9a7690de45.png)

### **3.4.5 Análise por Renda**

![image.png](attachment:a18842f5-17d1-482b-9503-18ecfefc5819:acc6a675-2b6b-40d9-9c66-f87bd6614375.png)

O padrão central é que, embora a exposição média à IA aumente com a renda (de 0,237 na faixa até 1 SM para 0,365 em 5+ SM), a **alta exposição** (Gradientes 3–4) não cresce indefinidamente: ela sobe de 7,6% na faixa mais baixa para cerca de 11–12% nas faixas intermediárias (1–3 SM) e depois **satura**, ficando praticamente estável mesmo entre os mais ricos.

Esse resultado pede cautela na interpretação. Há uma leitura intuitiva, mas equivocada, de que seria a elite intelectual e financeira o grupo mais exposto à IA, afinal, são eles que lidam com as tarefas mais sofisticadas, digitais e baseadas em conhecimento. Os dados mostram o contrário.

A OIT chega à mesma conclusão no WP140: o Gradiente 4, o de maior exposição, concentra-se sobretudo entre os **trabalhadores de apoio administrativo,** digitadores de dados, escriturários de contabilidade, secretários e caixas. São profissões com tarefas altamente estruturadas, centradas em dados e linguagem rotineira, exatamente o que os modelos de linguagem fazem com facilidade. Acima desse patamar, a renda passa a refletir mais cargos de gestão e profissões liberais especializadas, que tendem a cair em exposição **moderada** (G1–G2), não alta.

O resultado é que a maior "massa" de trabalhadores em alta exposição está em salários de até 2 SM, cerca de dois terços do total, um segmento com menor capacidade de absorver choques. Para o Brasil, isso tem uma implicação direta: os eventuais efeitos distributivos da IA devem aparecer primeiro na classe média de escritório, e não no topo da pirâmide.

### **3.4.6 Análise por situação de formalidade**

![image.png](attachment:f202a434-d610-4db8-b019-d5610ce848e6:09bebfba-37e6-4804-a4b0-4d8d0595c2ed.png)

A exposição média dos trabalhadores formais (0,305) é 0,047 ponto maior do que a dos informais (0,258), uma diferença relativa de +18% em relação à média informal. Novamente, o contraste é mais nítido na alta exposição: 14,8% dos formais (6,1 milhões) estão em ocupações de alta exposição (G3-G4), contra apenas 6,7% dos informais (3,6 milhões). Em termos proporcionais, trabalhadores com vínculo formal são 2,2 vezes mais presentes na alta exposição do que trabalhadores informais.

Apesar de a força de trabalho informal ser 32% maior do que a formal (54,6 vs. 41,3 milhões de ocupados), os formais respondem por 63% dos 9,8 milhões em alta exposição (6,1 milhões), e os informais por apenas 37% (3,6 milhões).

A interpretação é estrutural. Trabalhadores formais, predominantemente empregados CLT em escritórios e na administração pública, estão concentrados justamente nas ocupações classificadas com alta exposição. Mesmo que a maioria dos trabalhadores brasileiros esteja no mercado informal, a coorte mais sujeita a choques associados à IA generativa está no mercado formal, justamente onde o CAGED tem cobertura plena. Isso reforça a validade do desenho de diferenças em diferenças: ao focar no mercado formal, não estamos deixando de fora o grupo mais relevante. Estamos focando nele.

## **3.10 Augmentation vs. automação, robustez e síntese**

Para fechar o capítulo, junto três blocos: a comparação entre os trabalhadores em gradientes de complementaridade (G1-G2) e os em gradientes de transformação radical (G3-G4); os testes de robustez; e a síntese dos achados, com as limitações relevantes e a transição para o Capítulo 4.

### **3.10.3 Síntese e limitações**

A análise descritiva da Etapa 1 entrega sete achados centrais sobre a exposição do mercado de trabalho brasileiro à IA generativa.

1. **Dimensão.** 10,1% da força de trabalho ocupada (9,8 milhões de trabalhadores) está em ocupações de alta exposição (Gradientes 3-4 da OIT). Outros 19,3% estão em gradientes de complementaridade (G1-G2). A média (0,278) coloca o Brasil dentro do esperado para países de renda média-alta.
2. **Concentração ocupacional.** O grupo Apoio Administrativo (8,2 milhões) concentra a maior parte da alta exposição. Os setores críticos são Finanças e Seguros, Informação e Comunicação e Serviços Profissionais.
3. **Heterogeneidade demográfica.** Mulheres, brancos, jovens e mais escolarizados estão sistematicamente mais expostos. A decomposição Oaxaca-Blinder mostra que esses gaps são majoritariamente explicados por sorting ocupacional, com componente de segregação reversa no caso feminino.
4. **Formalidade.** O retorno da exposição sobre a renda é menor para formais que para informais — efeito que parece refletir profissionais liberais autônomos que capturam ganhos de produtividade da IA. Essa é uma dimensão ausente do WP140 e relevante para a agenda OIT sobre informalidade.
5. **Geografia.** A heterogeneidade regional é modesta em média, mas significativa em UFs específicas (DF lidera, Pará na base). A decomposição shift-share sugere que cerca de 60% das diferenças regionais vêm do efeito *within* setorial, não da composição setorial em si.
6. **Renda.** A relação descritiva exposição-renda é positiva no agregado (Q5/Q1 = 2,23x) mas não-monotônica e côncava em forma. A regressão quantílica indica que o prêmio da exposição é até 4x maior na cauda superior da renda.
7. **Augmentation × automação.** A maioria dos trabalhadores expostos está em gradientes de complementaridade, mas o subconjunto em alta transformação é majoritariamente feminino, formalizado e escolarizado.

Essas conclusões carregam limitações importantes que organizei em nove itens.

1. **Análise cross-sectional.** Os dados referem-se a um único trimestre (Q3/2025) e não permitem inferência causal. Padrões observados refletem o estado atual do mercado de trabalho, não o efeito da IA sobre ele.
2. **Índice global aplicado ao Brasil.** O WP140 foi construído com foco global e pode não capturar especificidades brasileiras como alta informalidade, terceirização extensiva e heterogeneidade na adoção tecnológica entre formal e informal.
3. **Exposição ≠ impacto.** O índice mede potencial técnico, não impacto realizado. A materialização depende de adoção, regulação, custos e respostas institucionais.
4. **Erros-padrão subestimados.** O desenho amostral complexo da PNADc não foi totalmente respeitado — erros-padrão tratam a amostra como aleatória simples reponderada.
5. **Crosswalk introduz erro de medida.** Apesar da cobertura de 99,2%, 1,3% das observações dependem de fallback a 3 dígitos. Os testes de robustez sugerem efeito desprezível, mas o erro existe.
6. **Variável de renda ausente.** 1,1 milhão de trabalhadores não declararam renda, sendo excluídos das análises de rendimento.
7. **Capacidade tecnológica datada.** O índice reflete o estado da arte da IA generativa em 2024-2025; a evolução rápida da tecnologia pode tornar parte das classificações defasada.
8. **Regressão quantílica não ponderada.** A implementação `QuantReg` do `statsmodels` não suporta pesos amostrais.
9. **Variável UPA indisponível.** Não foi possível clusterizar erros-padrão por UPA, o que poderia ampliar os intervalos de confiança reportados.

### **3.10.4 Transição para o Capítulo 4**

Os padrões descritos neste capítulo são correlativos. A pergunta natural que se segue é causal: o lançamento do ChatGPT, em novembro de 2022, alterou os resultados de mercado de trabalho das ocupações altamente expostas em comparação com as não-expostas? O Capítulo 4 responde a essa pergunta com um desenho de diferenças em diferenças aplicado aos registros administrativos do CAGED, usando o índice da OIT como variável de tratamento contínua e o evento ChatGPT como choque temporal exógeno. Os resultados causais que apresento lá ganham sentido econômico apenas quando lidos contra o pano de fundo descritivo deste capítulo: quem é exposto, em que ocupação, em que setor, e em que parte do mercado de trabalho.

# 4 Abordagem Empírica

Este capítulo apresenta o estudo empírico que dá nome à dissertação. A pergunta é causal: o lançamento do ChatGPT, em novembro de 2022, alterou os resultados do mercado de trabalho formal brasileiro nas ocupações mais expostas à IA generativa em comparação com as menos expostas? Para respondê-la, transito da PNADc para os microdados administrativos do Novo CAGED, monto um painel ocupação × mês com cinco anos de movimentações e estimo um desenho de diferenças em diferenças (DiD) inspirado em Brynjolfsson, Chandar e Chen (2025), *Canaries in the Coal Mine*. A escolha do desenho, da base e da medida de tratamento é o objeto da seção 4.1; a construção do painel e a especificação econométrica estão na 4.2; os resultados principais, em três blocos analíticos, na 4.3; a heterogeneidade por idade, escolaridade, mecanismo (automação × augmentação) e geografia, na 4.4; a robustez, na 4.5; e a síntese, com a comparação direta com o paper-âncora e as limitações, na 4.6.

## **4.1 Da descrição à inferência causal: por que CAGED, por que DiD**

A Etapa 1 mostrou que jovens, mulheres, brancos e mais escolarizados estão sistematicamente mais expostos à IA generativa no Brasil. Esses padrões, porém, são correlativos: descrevem quem ocupa as posições mais expostas em um corte transversal de 2025, mas não informam se a exposição já produziu efeitos diferenciais sobre o emprego ou os salários. A pergunta que se impõe aqui é diferente — é uma pergunta sobre causalidade, sobre o que mudou depois de um choque tecnológico observável.

A inspiração metodológica explícita é Brynjolfsson, Chandar e Chen (2025). Os autores usam folhas de pagamento da ADP, a maior administradora de RH dos Estados Unidos, para estimar diferenças em diferenças entre ocupações mais e menos expostas à IA, antes e depois do ChatGPT. O resultado central deles é que jovens entre 22 e 25 anos em ocupações altamente expostas tiveram queda relativa de cerca de 13% no emprego, enquanto trabalhadores mais velhos não foram afetados — o ajuste, no caso americano, aparece quase inteiramente do lado do volume, com salários "rígidos". O paper organiza os achados em seis fatos, mas o primeiro é o âncora: jovens em ocupações expostas perderam empregos.

A adaptação ao Brasil exige um equivalente da ADP. O candidato natural é o **Novo CAGED**, integrado ao eSocial, com cobertura mensal e censitária do mercado de trabalho formal celetista. Defendo o CAGED em vez do painel longitudinal da PNADc por três razões. Primeira, granularidade temporal: a frequência mensal do CAGED permite construir um event study denso, com 23 meses pré-ChatGPT e 31 meses pós, suficiente para testar tendências paralelas e identificar a dinâmica do efeito. Segunda, qualidade salarial: o CAGED registra o salário no momento da contratação, sem o ruído de imputação que afeta a renda do trabalho na PNAD. Terceira, cobertura: ao restringir a análise ao mercado formal, foco justamente no segmento que a Etapa 1 mostrou ser o mais relevante para o estudo da IA generativa — 63% dos trabalhadores em alta exposição (G3-G4) estão na formalidade, contra apenas 37% na informalidade. A aparente desvantagem de "deixar a informalidade de fora" se converte em vantagem analítica: estou olhando para o grupo onde o choque é mais provável de aparecer.

A pergunta de pesquisa é, então, direta: *após o lançamento do ChatGPT, ocupações altamente expostas à IA (top 20% do índice OIT) tiveram mudanças diferenciais em volume e/ou salário de admissão em comparação com ocupações menos expostas?*

Antecipo, ainda nesta abertura, uma diferença substantiva esperada em relação ao paper original. O mercado de trabalho brasileiro tem instituições que tornam o ajuste via emprego mais custoso do que o americano. A CLT impõe custos de demissão (multas rescisórias, aviso prévio, FGTS), o salário mínimo amarra o piso da distribuição e a estrutura sindical influencia parte da formação salarial. A hipótese que carrego para os dados é que, no Brasil, o ajuste talvez apareça mais via *preço* (salário) do que via *quantidade* (emprego). Essa não é uma previsão livre — é uma tese a ser testada, e os resultados da seção 4.3 indicam que a leitura tem suporte empírico.

## **4.2 Construção da base e estratégia empírica**

### **4.2.1 Microdados CAGED e painel ocupação × mês**

A janela analítica vai de janeiro de 2021 a junho de 2025, totalizando 54 meses. Excluí o ano de 2020 para evitar contaminação direta da pandemia de COVID-19, que produziu choques de magnitude muito superior ao do evento de interesse e geraria tendências pré-tratamento erráticas. O ponto inicial em 2021 garante 23 meses de pré-tratamento, suficientes para o teste formal de tendências paralelas, e o limite em junho de 2025 reflete o último mês com microdados consolidados disponíveis no momento desta escrita.

O volume bruto manipulado é grande: 198,8 milhões de movimentações registradas no CAGED no período. A unidade de análise, porém, não é a movimentação individual — é o painel agregado por ocupação × mês. Agreguei os microdados em CBO 2002 a 4 dígitos, gerando um painel com **32.988 observações, 629 ocupações e 54 períodos**, com balanceamento de aproximadamente 97% (ocupações que aparecem em pelo menos 50 dos 54 meses). A construção sequencial está documentada no notebook [`etapa_2a_preparacao_dados_did_caged_ilo.ipynb`](src/notebooks/etapa_2a_preparacao_dados_did_caged_ilo.ipynb).

Os outcomes derivam todos das **admissões**, seguindo a convenção de Hui, Reshef e Zhou (2024). A justificativa é metodológica: o salário no momento da contratação é a margem de ajuste mais limpa para o pesquisador interessado em mudanças de demanda por trabalho, porque incorpora a decisão de mercado mais recente do empregador. Os principais outcomes são (i) admissões, desligamentos e saldo líquido; (ii) salário médio nominal de admissão; (iii) **salário real de admissão**, deflacionado pelo IPCA do IBGE com base em dezembro de 2024; (iv) percentual de admissões com escolaridade superior; (v) idade média na admissão; e (vi) recortes por subgrupo demográfico — log de salário e log de admissões para mulheres, homens, jovens (≤29 anos), não-jovens, brancos, negros, ocupados com superior e ocupados com médio.

O salário real é o outcome principal. Em uma janela com inflação acumulada relevante (cerca de 22% entre 2021 e 2025 pelo IPCA), o salário nominal incorpora variação puramente monetária que não tem relação com o choque de IA. Aplico winsorização P1/P99 sobre as variáveis de salário e admissão para conter outliers — o procedimento clipou 678 observações, ou 2,1% do painel, com concentração em junho de 2025 (mês com volume atípico em ocupações específicas).

### **4.2.2 Crosswalk CBO 2002 → ISCO-08**

A ponte entre o CAGED, classificado em CBO 2002, e o índice OIT, classificado em ISCO-08, é o passo metodologicamente mais delicado da Etapa 2 e merece um detalhamento próprio. Diferentemente do que ocorre na Etapa 1, em que a PNADc usa a COD (derivada da ISCO-08 e estruturalmente compatível), o CAGED usa a CBO 2002, que é uma classificação de origem brasileira com lógica de agregação distinta. A correspondência exigiu construir uma estratégia *dual*.

A **especificação principal (2 dígitos)** parte do CBO 2d e mapeia para o subgrupo principal (sub-major group) do ISCO-08. Quando não há correspondência direta, faço *fallback* para o grande grupo (major group, 1d). A cobertura é de **100%** das movimentações do CAGED, e o score de exposição é o score médio do subgrupo no índice OIT. Essa é a especificação que sustenta os resultados principais.

A **especificação de robustez (4 dígitos)** usa um *fallback hierárquico em seis níveis*, espelhando o procedimento adotado em pesquisa internacional sobre crosswalks ocupacionais. O nível 1 (N1) busca correspondência direta entre CBO 4d e ISCO-08 4d (cobertura de aproximadamente 28%); N2 usa a ponte ISCO-88 → ISCO-08 4d; N3 cai para 3 dígitos (CBO 3d = ISCO-08 3d); N4 usa ISCO-88 a 3 dígitos; N5 cai para 2 dígitos; e N6, no limite, retorna o grande grupo a 1 dígito. A cobertura final, com fallback, é também de **100%**.

O critério mais informativo para julgar a qualidade do crosswalk é a correlação entre os scores produzidos pelas duas especificações. A **correlação 2d × 4d é de 0,915**, e os principais achados (seção 4.5) sobrevivem com mesma direção e magnitude semelhante quando reestimados com o crosswalk a 4 dígitos. As cinco ocupações com maior score de exposição na especificação principal são todas do grande grupo de Apoio Administrativo (CBO 41xx, score 0,632): auxiliares de escritório, secretários, escriturários e caixas. As cinco com menor score são do grande grupo de Manutenção e Reparação (CBO 91xx, score 0,117). Esse padrão — concentração da alta exposição em apoio administrativo — é o mesmo que a Etapa 1 documentou para a PNADc, reforçando a consistência do mapeamento.

A definição do tratamento usa o critério do **top 20% do score**, gerando um grupo de tratamento com 131 ocupações (cerca de 6,7 milhões de movimentações no CAGED) e um grupo de controle com 498 ocupações (bottom 80%). Cutoffs alternativos — top 10%, top 25% e mediana — e uma especificação com tratamento contínuo são reportados na seção 4.5 como testes de robustez. O ponto de corte de 20% concilia duas exigências: separar com clareza ocupações de alta exposição (acima do score 0,40) das demais e preservar amostra suficiente no grupo tratado para identificação dos efeitos por subgrupo demográfico.

**Tabela 4.1 — Ficha técnica do painel CAGED+ILO**

| **Item** | **Valor** |
| --- | --- |
| Fonte | Novo CAGED (eSocial/MTE) + ILO WP140 (Gmyrek et al., 2025) |
| Janela analítica | Jan/2021 – Jun/2025 (54 meses) |
| Movimentações brutas | 198,8 milhões |
| Unidade do painel | CBO 2002 a 4 dígitos × mês |
| Observações no painel | 32.988 |
| Ocupações distintas | 629 |
| Períodos | 54 |
| Balanceamento | ~97% |
| Crosswalk principal | CBO 2d → ISCO-08 sub-major (cobertura 100%) |
| Crosswalk robustez | CBO 4d → ISCO-08 4d, fallback hierárquico em 6 níveis (cobertura 100%) |
| Correlação 2d × 4d | 0,915 |
| Tratamento | Top 20% do score OIT (131 ocupações) vs. bottom 80% (498) |
| Evento | 30/Nov/2022 (lançamento do ChatGPT) |
| Pré-tratamento | 23 meses (Jan/2021 – Nov/2022) |
| Pós-tratamento | 31 meses (Dez/2022 – Jun/2025) |
| Deflator | IPCA/IBGE, base Dez/2024 |
| Winsorização | P1/P99 (678 obs clipadas, 2,1%) |

### **4.2.3 Especificação econométrica**

O modelo principal é um TWFE (two-way fixed effects) clássico. Para cada outcome $y_{ot}$ na ocupação $o$ no mês $t$, estimo:

$$y_{ot} = \beta \cdot (\text{Pós}_t \times \text{Alta\_Exp}_o) + \gamma \cdot X_{ot} + \alpha_o + \delta_t + \varepsilon_{ot}$$

onde $\text{Alta\_Exp}_o = 1$ se a ocupação $o$ está no top 20% do score OIT, $\text{Pós}_t = 1$ se $t \geq$ Dez/2022, $X_{ot}$ é um vetor de controles que varia por outcome (idade média, % mulheres, % superior nas admissões, omitindo o controle quando ele é o próprio outcome para evitar simultaneidade), $\alpha_o$ é o efeito fixo de ocupação a 4 dígitos, $\delta_t$ é o efeito fixo de período (mês-ano) e $\varepsilon_{ot}$ é o erro idiossincrático. Os erros-padrão são clusterizados por CBO 4d, que é a unidade de variação do tratamento.

O coeficiente de interesse é $\beta$. Sob a hipótese de **tendências paralelas** — ou seja, sob a hipótese contrafactual de que, na ausência do ChatGPT, ocupações de alta e baixa exposição teriam seguido a mesma trajetória —, $\beta$ identifica o efeito médio do tratamento sobre os tratados. A hipótese é testada formalmente com um event study saturado em *leads* e *lags* relativos ao mês do tratamento, com $t = -1$ como referência e binning em $-12$ e $+24$ para evitar multicolinearidade nas pontas.

Para complementar o TWFE de 2×2, estimo também um event study com a especificação:

$$y_{ot} = \sum_{k \neq -1} \tau_k \cdot \mathbb{1}[t = t^* + k] \cdot \text{Alta\_Exp}_o + \gamma \cdot X_{ot} + \alpha_o + \delta_t + \varepsilon_{ot}$$

onde $t^* = $ Nov/2022 e os coeficientes $\tau_k$ traçam a dinâmica do efeito. A leitura é direta: $\tau_k$ para $k < 0$ não deve ser estatisticamente diferente de zero (pré-tratamento paralelo) e $\tau_k$ para $k \geq 0$ traça a trajetória do impacto pós-evento.

Antes de apresentar resultados, é necessário verificar o balanço pré-tratamento entre os grupos. A Tabela 4.2 reporta as médias do grupo de controle e do grupo de tratamento na janela pré-ChatGPT (Jan/2021 – Nov/2022) e a diferença normalizada (Imbens & Rubin, 2015), com o critério convencional de balanceamento de |diferença| < 0,25.

**Tabela 4.2 — Balanço pré-tratamento (Jan/2021 – Nov/2022)**

| **Variável** | **Controle (média)** | **Tratamento (média)** | **Dif. normalizada** | **Balanceado** |
| --- | --- | --- | --- | --- |
| Admissões (média mensal) | 2.655 | 3.410 | 0,06 | ✓ |
| Desligamentos (média mensal) | 2.321 | 2.917 | 0,06 | ✓ |
| Saldo líquido (média mensal) | 334 | 493 | 0,09 | ✓ |
| Salário médio (R$) | 2.739 | 5.388 | **0,68** | ⚠️ |
| Idade média | 32,8 | 31,8 | -0,17 | ✓ |
| % Mulheres | 27,9% | 44,1% | **0,70** | ⚠️ |
| % Superior | 15,6% | 41,9% | **1,15** | ⚠️ |

*Fonte: elaboração própria a partir do CAGED. Cf. [`outputs/tables/balance_table_pre.csv`](outputs/tables/balance_table_pre.csv).*

A leitura é exatamente a esperada. As variáveis de fluxo (admissões, desligamentos, saldo) e a idade média estão balanceadas: ocupações de alta e baixa exposição admitem volumes parecidos. Mas três variáveis estão claramente desbalanceadas: salário (diferença normalizada de 0,68), proporção de mulheres (0,70) e proporção de admitidos com superior (1,15). Esse padrão é exatamente o documentado na Etapa 1: as ocupações altamente expostas são predominantemente *white collar*, com remuneração mais alta, maior participação feminina e escolaridade superior — não é defeito, é o próprio retrato sociodemográfico da exposição que vem da Etapa 1. Os efeitos fixos de ocupação absorvem essas diferenças *time-invariant*, e os controles de composição entram para tratar variação ao longo do tempo. Os testes de robustez (seção 4.5) com cutoffs alternativos e crosswalk a 4 dígitos confirmam que o desbalance estrutural não dirige os resultados.

## **4.3 Resultados principais**

A Tabela 4.3 consolida os coeficientes de $\beta$ estimados com o Modelo 3 (FE de ocupação + FE de período + controles, especificação principal) para os seis outcomes de cabeça do painel. Os números completos para todos os 18 outcomes e todas as seis variantes do modelo estão no notebook [`etapa_2b_analise_did_caged_ilo.ipynb`](src/notebooks/etapa_2b_analise_did_caged_ilo.ipynb) e em [`outputs/tables/did_main_results.csv`](outputs/tables/did_main_results.csv).

**Tabela 4.3 — Resultados DiD principais (Modelo 3: FE + Controles)**

| **Outcome** | **β** | **E.P.** | **p-valor** | **Sig.** |
| --- | --- | --- | --- | --- |
| Log(Admissões) | -0,027 | 0,026 | 0,305 | — |
| Log(Desligamentos) | +0,019 | 0,027 | 0,479 | — |
| Saldo líquido (vagas/mês) | -77,7 | 69,6 | 0,265 | — |
| Log(Salário nominal de admissão) | -0,066 | 0,028 | 0,019 | ** |
| Log(Salário real de admissão) | -0,034 | 0,019 | 0,078 | * |
| % Superior nas admissões (pp) | +0,010 | 0,004 | 0,016 | ** |
| Log(Salário jovens ≤29) | -0,134 | 0,052 | 0,011 | ** |
| Log(Salário não-jovens) | +0,003 | 0,027 | 0,928 | — |
| Log(Salário escolaridade média) | -0,085 | 0,032 | 0,008 | *** |
| Log(Salário escolaridade superior) | -0,078 | 0,041 | 0,056 | * |
| Log(Admissões jovens ≤29) | -0,056 | 0,029 | 0,052 | * |

*\* p<0,10; ** p<0,05; *** p<0,01. Erros-padrão clusterizados por CBO 4d. n=32.988. Fonte: [`outputs/tables/did_main_results.csv`](outputs/tables/did_main_results.csv).*

A leitura agregada produz três blocos analíticos.

### **4.3.1 Bloco 1 — O ajuste é via salário, não via volume**

O primeiro achado é também o mais surpreendente quando contrastado com o paper-âncora. As variáveis de quantidade — admissões, desligamentos e saldo líquido — não respondem ao tratamento. O coeficiente sobre admissões é -0,027 (p=0,305), sobre desligamentos é +0,019 (p=0,479) e sobre saldo é -77,7 vagas/mês (p=0,265). Nenhum desses estimadores é estatisticamente significativo, e os intervalos de confiança incluem o zero com folga.

Já as variáveis de preço respondem com clareza. O **salário nominal de admissão** cai 6,6% nas ocupações tratadas em comparação com o contrafactual (β = -0,066, p=0,019), e o **salário real de admissão**, deflacionado pelo IPCA, cai 3,4% (β = -0,034, p=0,078). Em economia, esses são efeitos econômica e estatisticamente relevantes.

A interpretação é o ponto central deste capítulo. Brynjolfsson, Chandar e Chen (2025) encontram nos Estados Unidos um padrão oposto: o ajuste lá aparece via *quantidade* — o emprego cai entre os jovens em ocupações expostas — com salários "rígidos". Aqui, o ajuste aparece via *preço* — o salário de admissão cai — com volumes estáveis. A hipótese institucional já delineada na seção 4.1 ganha suporte empírico. Três mecanismos plausíveis explicam o contraste:

1. **CLT torna a demissão custosa.** Multas rescisórias, aviso prévio e FGTS empurram o empregador a ajustar via margem nova (salário de entrada) em vez de demitir. O efeito sobre admissões e desligamentos é, por construção, atenuado pela rigidez à demissão.
2. **Salário mínimo amarra o piso.** O efeito não pode aparecer no fundo da distribuição — o piso está protegido. Mas aparece com força nas ocupações *white collar* de classe média (apoio administrativo, profissionais técnicos), que estão acima do piso e onde existe espaço para ajuste para baixo.
3. **Difusão gradual da IA.** A penetração efetiva de ferramentas como ChatGPT, Copilot e similares no mercado brasileiro é mais lenta do que nos EUA, especialmente em 2023 e 2024. O canal volume pode aparecer em janelas mais longas; o canal preço, no entanto, já é mensurável.

### **4.3.2 Bloco 2 — Quem está sendo afetado: jovens carregam o efeito**

Quando desagrego o efeito por idade, a história ganha contorno. O coeficiente sobre o **log do salário dos jovens (≤29 anos)** nas ocupações tratadas é -0,134 (p=0,011): uma queda relativa de **13,4%** no salário de admissão dos jovens em ocupações expostas, contra um efeito nulo (-0,003, p=0,928) sobre os não-jovens. A magnitude é virtualmente a mesma encontrada por Brynjolfsson, Chandar e Chen (2025) nos Estados Unidos para a faixa 22–25 anos (-13%) — só que aqui o efeito aparece via *salário*, não via *emprego*.

A volta do efeito-jovem nesta dissertação fecha um arco com a Etapa 1. No Capítulo 3, mostrei que a faixa 15–19 tem 3,2 vezes mais trabalhadores em alta exposição do que a faixa 55–59. Os jovens estão mais expostos por uma razão estrutural — ingressam em apoio administrativo, vendas qualificadas e funções técnicas iniciais. A Etapa 2 mostra que essa cohort mais exposta sofreu o ajuste de preço quando o choque tecnológico chegou. O Brasil produz, com dados próprios, o mesmo "fato âncora" do *Canaries in the Coal Mine* — só que adaptado à sua estrutura institucional.

A confirmação formal vem do Triple-DiD. Quando estimo:

$$y_{ot} = \beta_1 \cdot (\text{Pós} \times \text{Alta\_Exp}) + \beta_2 \cdot (\text{Pós} \times \text{Jovem}) + \beta_3 \cdot (\text{Alta\_Exp} \times \text{Jovem}) + \beta_4 \cdot (\text{Pós} \times \text{Alta\_Exp} \times \text{Jovem}) + \cdots$$

a interação tripla $\beta_4$ para o salário real é -0,186 (p=0,003), e para o salário nominal é -0,324 (p=0,001). O efeito não é apenas concentrado em jovens — é estatisticamente concentrado em jovens, com diferença significativa em relação aos não-jovens. Os números completos do Triple-DiD estão em [`outputs/tables/heterogeneity_triple_did.csv`](outputs/tables/heterogeneity_triple_did.csv).

A magnitude do efeito sobre jovens também aparece, em direção e significância, nas admissões: o log de admissões de jovens em ocupações tratadas cai 5,6% (β = -0,056, p=0,052). É o único subgrupo em que o canal volume acompanha o canal preço. Os jovens, no Brasil, foram afetados nas duas margens — só que o canal salarial foi mais forte e mais nítido estatisticamente.

### **4.3.3 Bloco 3 — Há recomposição da força de trabalho**

O terceiro bloco analítico vem da composição das contratações. O coeficiente sobre o **percentual de superior nas admissões** em ocupações tratadas é +0,010 (p=0,016): empresas em ocupações altamente expostas estão admitindo, depois do ChatGPT, 1 ponto percentual a mais de profissionais com superior do que admitiriam no contrafactual. A idade média na admissão também sobe (β = +0,26 ano, p=0,060), reforçando a leitura.

O que isso significa? Empresas em ocupações expostas estão recompondo o perfil das contratações — selecionando trabalhadores mais qualificados e mais experientes. A leitura econômica é consistente com a hipótese de que a IA generativa absorve as **tarefas de entrada** dessas ocupações: redação simples, planilhas rotineiras, atendimento de primeiro nível, sumários e classificações. O que sobra para ser contratado é trabalho remanescente que exige julgamento, contexto institucional e expertise — tipicamente, perfis sênior ou com formação superior.

Esse achado é a outra face do que Brynjolfsson, Chandar e Chen (2025) descrevem como "vagas de entrada quebradas". No caso americano, as vagas de entrada *desaparecem* (jovens deixam de ser contratados em ocupações expostas). No Brasil, as vagas de entrada *migram*: continuam sendo abertas, mas para perfis de maior senioridade e escolaridade, com salário menor para os jovens que ainda entram. É um ajuste qualitativo da estrutura ocupacional, não uma simples redução do tamanho dela.

### **4.3.4 Tendências paralelas e dinâmica do efeito**

A validade da identificação do DiD repousa sobre a hipótese de tendências paralelas. Estimei o teste formal por outcome, contando o número de coeficientes de leads (pré-tratamento) estatisticamente significativos a 5% e calculando o p-valor conjunto da hipótese de não-significância de todos os leads. Os resultados estão em [`outputs/tables/parallel_trends_test.csv`](outputs/tables/parallel_trends_test.csv).

Dos 18 outcomes testados, **16 passam no teste formal** (p_conjunto > 0,10): admissões, saldo, salário nominal, salário real, % superior, salário homens, salário jovens, salário não-jovens, salário brancos, salário negros, salário superior, salário médio, admissões mulheres, admissões homens, admissões jovens e admissões negros. Apenas dois levantam preocupação: desligamentos (p_conjunto = 0,000) e salário das mulheres (p_conjunto = 0,073).

O outcome de desligamentos é discutido como limitação do desenho, mas há uma evidência mitigadora. Quando reestimei a especificação principal incluindo tendências grupo-específicas de pré-tratamento (notebook 2b, seção 10.4), o coeficiente sobre desligamentos perde significância (p=0,102), o que sugere que o resultado original — coeficiente positivo e *não significativo* a 5% mesmo no Modelo 3 (β=+0,019, p=0,479) — pode refletir um padrão de tendência divergente que não tem relação com o evento de interesse. Os outcomes principais (salário real, salário jovens, % superior) passam tanto no teste formal de tendências paralelas quanto no teste de tendências diferenciais incluído na seção 4.5.

A Figura 4.1 traça a dinâmica do efeito para os quatro outcomes principais (admissões, salário real de admissão, salário dos jovens, % superior nas admissões), com os 23 leads e 31 lags relativos a Nov/2022.

**Figura 4.1 — Event study agregado (4 outcomes principais)**

![image.png](attachment:event-study-agregado:event_study_all_outcomes.png)

*Os coeficientes pré-tratamento (à esquerda da linha tracejada) ficam estatisticamente nulos em todos os outcomes principais, sustentando a hipótese de tendências paralelas. Os coeficientes pós-tratamento começam a divergir a partir de t=0 e ficam consistentemente negativos para os outcomes salariais entre t=+6 e t=+24, com aprofundamento gradual. Para % superior, a divergência é positiva e cresce. Cf. [`outputs/figures/event_study_all_outcomes.png`](outputs/figures/event_study_all_outcomes.png).*

A leitura visual é nítida: não há tendência divergente antes de Nov/2022, e o efeito aparece com gradualidade entre 6 e 12 meses depois do tratamento, consistente com a difusão progressiva da IA generativa no mercado. O salário dos jovens é o caso mais dramático — a queda começa ainda no primeiro semestre de 2023 e aprofunda-se em 2024 e 2025.

## **4.4 Heterogeneidade**

Os achados da seção 4.3 são médios — refletem o comportamento agregado das ocupações tratadas. A heterogeneidade analítica organiza-se em quatro dimensões: idade, escolaridade, mecanismo (automação × augmentação) e geografia. Os resultados desta seção vêm do Triple-DiD reportado em [`outputs/tables/heterogeneity_triple_did.csv`](outputs/tables/heterogeneity_triple_did.csv) e da subamostra municipal da Etapa 3.

### **4.4.1 Por idade**

A dimensão da idade já apareceu como bloco principal na seção 4.3.2 e aprofundo aqui. A interação tripla `Pós × Alta_Exp × Jovem` é negativa e significativa para os dois principais outcomes salariais — salário nominal (β = -0,324, p=0,001) e salário real (β = -0,186, p=0,003) — confirmando que o ajuste salarial documentado na seção 4.3 é estatisticamente concentrado nos jovens, e não apenas mais visível neles.

A interação para % superior também é informativa: -0,021 (p=0,066). O sinal negativo significa que a recomposição para perfis mais qualificados é *menor* nas ocupações onde os jovens são mais presentes. Em outras palavras, a "migração para sênior" descrita no Bloco 3 acontece no agregado, mas é mais limitada exatamente nas ocupações com mais juventude — o que faz sentido empírico, porque essas são as ocupações onde a oferta de trabalho jovem é mais elástica e onde a maior parte do ajuste cai sobre o salário de entrada da própria coorte jovem.

### **4.4.2 Por escolaridade**

A divisão entre ocupações de "alta qualificação" (acima da mediana de % superior nas admissões pré-tratamento) e "baixa qualificação" (abaixo da mediana) revela uma assimetria importante. Em ocupações de **alta qualificação**, o coeficiente sobre o salário real é +0,002 (p=0,885) — efeito *nulo*. Em ocupações de **baixa qualificação**, o coeficiente é -0,115 (p=0,051) — efeito *forte e estatisticamente significativo a 10%*.

A leitura conversa diretamente com a Etapa 1. No Capítulo 3, mostrei que a maior massa de trabalhadores em alta exposição (Gradientes 3 e 4) está concentrada em salários de até 2 SM, segmento de menor capacidade de absorver choques. A Etapa 2 confirma a previsão correlacional com inferência causal: a IA está pressionando o salário nas ocupações de média e baixa qualificação dentro do grupo de alta exposição (apoio administrativo, escriturários, caixas), não no topo da pirâmide. O coeficiente do log de salário em ocupações com escolaridade *média* (-0,085, p=0,008) é o mais forte da Tabela 4.3 entre os controles de composição educacional.

### **4.4.3 Mecanismo: automação vs. augmentação**

Para distinguir entre os mecanismos teóricos de automação (a IA substitui o trabalho humano) e augmentação (a IA complementa o trabalho humano), incorporei o Anthropic Economic Index (AEI) ao painel CAGED+ILO. O AEI classifica ocupações conforme o uso predominante das ferramentas de IA observado em logs reais de Claude — quando o uso é majoritariamente para substituir tarefas (executar uma tarefa por completo no lugar do humano), a ocupação tem índice positivo de automação; quando é majoritariamente para complementar (auxiliar o humano), o índice é negativo (mode dominante de augmentação).

No painel brasileiro com correspondência ao AEI, **5,4% das ocupações** se classificam como Automação, e os outros **94,6%** como Augmentação. A grande maioria das ocupações brasileiras, portanto, tem perfil de uso da IA voltado para complementação, não substituição.

Quando estimo o DiD separadamente para os dois subgrupos, o resultado é menos nítido do que esperaríamos teoricamente. Em Automação, β = +0,077 (p=0,177) sobre o salário real; em Augmentação, β = +0,015 (p=0,647). O efeito não é estatisticamente diferente entre os dois grupos no Brasil, e nenhum dos dois subgrupos alcança significância estatística isoladamente. A leitura honesta é dupla: (i) há uma limitação de poder estatístico, porque a subamostra de Automação tem poucas ocupações; (ii) há, possivelmente, uma diferença substantiva com o achado de Brynjolfsson, Chandar e Chen (2025), que veem nitidez maior em Automação no caso americano.

A Figura 4.2 ilustra a relação entre o índice de automação do AEI e o coeficiente DiD por ocupação, com o subconjunto de ocupações de Automação destacado.

**Figura 4.2 — Coeficiente DiD por ocupação contra índice de automação (Anthropic)**

![image.png](attachment:scatter-automacao-coef:scatter_automation_index_vs_did_coef.png)

*Cada ponto é uma ocupação CBO 4d. O eixo horizontal traz o índice de automação Anthropic (positivo = Automação); o eixo vertical, o coeficiente DiD do log do salário real para aquela ocupação. A inclinação da reta de regressão não é estatisticamente significativa. Cf. [`outputs/figures/scatter_automation_index_vs_did_coef.png`](outputs/figures/scatter_automation_index_vs_did_coef.png).*

### **4.4.4 Geografia: a dimensão da conectividade municipal**

A dimensão geográfica entra como uma extensão natural do desenho. A IA é uma tecnologia que se difunde pela infraestrutura digital — em particular, pela penetração de banda larga. Esperaríamos, portanto, que o efeito ocupacional documentado na seção 4.3 fosse *amplificado* em municípios com maior conectividade. Para testar essa hipótese, construí na Etapa 3 um painel mais granular em município × ocupação × mês, integrando o CAGED com indicadores de conectividade municipal da Anatel (densidade de acessos de banda larga fixa, fração de fibra) e indicadores de IBGE (população, PIB per capita). Os scripts estão em [`notebook/scripts/etapa_3a/`](notebook/scripts/etapa_3a/) e [`notebook/scripts/etapa_3b/`](notebook/scripts/etapa_3b/).

A especificação Triple-DiD é:

$$y_{m o t} = \beta_1 \cdot (\text{Pós} \times \text{Alta\_Exp}) + \beta_2 \cdot (\text{Pós} \times \text{Alta\_Conect}) + \beta_3 \cdot (\text{Alta\_Exp} \times \text{Alta\_Conect}) + \beta_4 \cdot (\text{Pós} \times \text{Alta\_Exp} \times \text{Alta\_Conect}) + \gamma X + \alpha_{mo} + \delta_t + \varepsilon$$

onde $\alpha_{mo}$ é o efeito fixo de município × ocupação (controle estrutural mais exigente do que o uso só de FE de ocupação, porque absorve heterogeneidade municipal permanente em cada ocupação). O coeficiente de interesse é $\beta_4$, que captura o efeito *adicional* do tratamento nas ocupações expostas em municípios mais conectados.

O resultado central, em [`outputs/tables/triple_did_main_etapa3b.csv`](outputs/tables/triple_did_main_etapa3b.csv), é:

| **Coeficiente** | **β** | **E.P.** | **p-valor** | **Sig.** |
| --- | --- | --- | --- | --- |
| Pós × Alta_Exp | +0,008 | 0,008 | 0,285 | — |
| Pós × Alta_Conect | +0,017 | 0,008 | 0,025 | ** |
| Alta_Exp × Alta_Conect | +0,037 | 0,010 | 0,000 | *** |
| **Pós × Alta_Exp × Alta_Conect** | **-0,016** | **0,008** | **0,059** | * |

A interação tripla é negativa e marginalmente significativa: -0,016 (p=0,059). A leitura é que, em municípios de alta conectividade, o efeito do tratamento sobre o salário das ocupações expostas é *adicionalmente negativo* em cerca de 1,6 pontos percentuais em relação ao efeito médio observado nos municípios menos conectados — uma amplificação do canal salarial documentado na seção 4.3.2. Os efeitos cruzados auxiliares são consistentes com a interpretação: ocupações altamente expostas e municípios de alta conectividade têm, no conjunto da janela, salários estruturalmente mais altos (β = +0,037, p<0,001), e a conectividade pós-2022 traz um efeito médio positivo sobre todas as ocupações (β = +0,017, p=0,025), provavelmente refletindo digitalização agregada da economia. Mas, *dentro* das ocupações expostas, a conectividade adiciona uma camada negativa pós-ChatGPT — exatamente onde a teoria prevê que o canal de difusão da IA seria mais ativo.

A leitura não é trivial. O sinal positivo geral da conectividade pós-tratamento (+0,017 sobre todas as ocupações) significa que o digital, no agregado, valorizou trabalho. Mas o sinal negativo da interação tripla (-0,016) significa que essa valorização *não* alcançou as ocupações altamente expostas à IA — pelo contrário, a conectividade comprimiu essas remunerações relativamente. É consistente com a leitura de que a IA generativa, ao se difundir mais rapidamente em municípios conectados, exerce uma pressão competitiva específica sobre os trabalhadores cujas tarefas são mais substituíveis.

## **4.5 Testes de robustez**

A Tabela 4.4 reúne os principais resultados dos cinco testes de robustez aplicados ao desenho. O foco é o **salário real de admissão**, que é o outcome principal, mas reporto também o salário dos jovens, que é o segundo achado mais saliente. Os números completos para todos os outcomes estão em [`outputs/tables/robustness_results.csv`](outputs/tables/robustness_results.csv).

**Tabela 4.4 — Testes de robustez (especificação principal e variantes)**

| **Teste** | **Especificação** | **β salário real** | **E.P.** | **p** | **β salário jovens** | **E.P.** | **p** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Principal | Top 20% | -0,034 | 0,019 | 0,078\* | -0,134 | 0,052 | 0,011\*\* |
| Cutoff alternativo | Top 10% | -0,035 | 0,025 | 0,150 | -0,079 | 0,052 | 0,127 |
| Cutoff alternativo | Top 25% | -0,047 | 0,018 | 0,009\*\*\* | -0,117 | 0,044 | 0,008\*\*\* |
| Cutoff alternativo | Mediana | -0,012 | 0,016 | 0,471 | -0,041 | 0,032 | 0,200 |
| Placebo temporal | Choque em Dez/2021 | +0,021 | 0,023 | 0,376 | -0,096 | 0,055 | 0,079\* |
| Exclusão de TI | Sem CBO 21xx | -0,046 | 0,021 | 0,033\*\* | -0,171 | 0,060 | 0,004\*\*\* |
| Crosswalk 4d | Hierárquico 6 níveis | -0,045 | 0,020 | 0,024\*\* | -0,180 | 0,048 | 0,000\*\*\* |
| Tendências dif. | Trend × Tratamento (pré) | +0,001 | 0,002 | 0,501 | -0,007 | 0,004 | 0,113 |

*\* p<0,10; ** p<0,05; *** p<0,01. Fonte: [`outputs/tables/robustness_results.csv`](outputs/tables/robustness_results.csv).*

A leitura do conjunto é favorável ao achado principal.

**Cutoffs alternativos.** Movendo o ponto de corte para top 25%, o efeito sobre o salário real fica mais forte (-0,047, p=0,009). Para top 10%, a magnitude se mantém (-0,035) mas perde significância, com IC mais largo por menor amostra tratada. Na mediana, o efeito desaparece, o que faz sentido: ao incluir metade das ocupações no grupo "tratado", a definição perde o foco analítico nas ocupações de fato altamente expostas. O top 20% é o ponto que combina clareza conceitual (acima do score 0,40, faixa em que a OIT classifica os Gradientes 3 e 4) com poder estatístico.

**Placebo temporal.** Defini um "choque falso" em dezembro de 2021 — exatamente um ano antes do ChatGPT, com toda a janela pós-evento ainda dentro do pré-ChatGPT real — e reestimei. Sobre o salário real, o coeficiente é +0,021 (p=0,376), positivo e não significativo. Para os 18 outcomes do painel, apenas 2 ficam significativos a 10% no placebo (salário jovens e admissões negros), o que está dentro do esperado por ruído estatístico (1,8 falsos positivos esperados a 10% × 18 testes). O placebo *não* reproduz os achados da seção 4.3, o que é uma evidência forte a favor da interpretação causal.

**Exclusão das ocupações de TI.** Uma preocupação razoável é que o efeito esteja capturando o ajuste pós-COVID em ocupações de tecnologia da informação, que é um choque diferente do ChatGPT (booms de contratação em 2021, demissões em 2023). Excluí o grande grupo CBO 21xx (Profissionais das Ciências Exatas, Físicas e da Engenharia, com peso de aproximadamente 4% do painel) e reestimei. O efeito sobre salário real *fortalece*: -0,046 (p=0,033), a magnitude maior. O efeito não vem da TI — sobrevive à sua exclusão.

**Crosswalk 4d.** A especificação de robustez do crosswalk (CBO 4d → ISCO-08 4d com fallback em 6 níveis), com correlação 0,915 com a especificação principal, produz coeficiente de -0,045 (p=0,024) sobre o salário real e -0,180 (p<0,001) sobre o salário dos jovens. As duas especificações entregam direção, magnitude e significância semelhantes, com 13 dos 15 outcomes principais com mesmo sinal e robustez salarial preservada. O risco de erro de medida no crosswalk não compromete os achados.

**Tendências diferenciais no pré.** Inclui uma tendência linear interagida com o tratamento, restrita ao período pré-ChatGPT. O coeficiente da tendência diferencial é +0,001 (p=0,501) sobre salário real e -0,007 (p=0,113) sobre salário dos jovens — em nenhum caso significativo. Para os 18 outcomes do painel, apenas 1 (admissões de negros) tem trend × tratamento significativo a 5%, o que está dentro do esperado por ruído. Os outcomes principais sustentam a hipótese de tendências paralelas mesmo sob esse teste mais exigente.

**Testes adicionais.** Mantive ainda dois exercícios complementares, reportados no notebook 2b. (i) **Donut hole**: excluindo dezembro de 2022 e janeiro de 2023 — meses que poderiam concentrar o "burst" inicial pós-ChatGPT —, o coeficiente sobre salário real fica em -0,038 (p=0,055), virtualmente idêntico ao principal. O efeito persiste sem o pico inicial. (ii) **Cluster CBO 2d** (em vez do CBO 4d principal): salário nominal β=-0,063 (p=0,090), atenuação esperada quando o cluster é mais agregado, mas direção e magnitude preservadas.

## **4.6 Síntese, comparação com a literatura e limitações**

### **4.6.1 Sete achados centrais**

A análise causal da Etapa 2 entrega sete achados centrais sobre o impacto do ChatGPT no mercado de trabalho formal brasileiro.

1. **Salário cai, volume não.** Ocupações altamente expostas tiveram queda de 3,4% no salário real de admissão pós-ChatGPT (β = -0,034, p=0,078) e de 6,6% no salário nominal (β = -0,066, p=0,019), sem efeito estatisticamente significativo sobre admissões, desligamentos ou saldo líquido. O ajuste, no Brasil, aparece via *preço*, não via *quantidade*.
2. **Jovens carregam o efeito.** O salário de admissão dos jovens (≤29) em ocupações expostas caiu 13,4% (β = -0,134, p=0,011), magnitude que espelha quase exatamente o achado central de Brynjolfsson, Chandar e Chen (2025) para os Estados Unidos. A interação tripla `Pós × Alta_Exp × Jovem` é -0,186 (p=0,003), confirmando que o efeito é *estatisticamente* concentrado em jovens.
3. **Recomposição da força de trabalho.** O percentual de superior nas admissões em ocupações tratadas subiu 1 ponto percentual (β = +0,010, p=0,016) e a idade média na admissão subiu 0,26 ano (β = +0,26, p=0,060). Empresas em ocupações expostas estão admitindo perfis mais qualificados e mais experientes — uma migração estrutural das vagas de entrada.
4. **Escolaridade média é o epicentro.** Ocupações de baixa qualificação (abaixo da mediana de % superior) têm queda de 11,5% no salário real (p=0,051), enquanto ocupações de alta qualificação têm efeito *nulo* (β = +0,002, p=0,885). O efeito, dentro do grupo tratado, concentra-se no apoio administrativo e nas ocupações *white collar* de média qualificação.
5. **Geografia importa.** A conectividade municipal de banda larga *amplifica* o efeito salarial: a interação tripla `Pós × Alta_Exp × Alta_Conect` é -0,016 (p=0,059). O canal digital de difusão da IA deixa pegada mensurável no salário das ocupações expostas dos municípios mais conectados.
6. **Achado robusto.** Os resultados sobrevivem a cutoffs alternativos (top 25% reforça, top 10% e mediana mantêm direção), placebo temporal (não reproduz), exclusão das ocupações de TI (efeito fortalece), crosswalk a 4 dígitos (β = -0,045, p=0,024), donut hole (β = -0,038, p=0,055) e cluster CBO 2d.
7. **Diferente dos EUA na margem.** Onde Brynjolfsson, Chandar e Chen (2025) encontraram nos EUA ajuste via *quantidade* com salários "rígidos", encontro no Brasil o oposto — ajuste via *preço* com volumes estáveis. A hipótese institucional (CLT, custos de demissão, salário mínimo) tem suporte empírico nos dados.

### **4.6.2 Comparação com Brynjolfsson, Chandar e Chen (2025)**

A comparação direta com o paper-âncora é o exercício analítico mais informativo desta seção. Os autores organizam seus achados em seis fatos. Reorganizo a comparação aqui:

| **Fato Brynjolfsson et al. (2025) — EUA** | **Equivalente brasileiro — esta dissertação** |
| --- | --- |
| Jovens (22–25) em ocupações expostas: -13% no emprego | Jovens (≤29) em ocupações expostas: **-13,4% no salário** |
| Ajuste via volume; salários "rígidos" | Ajuste via salário; **volumes estáveis** |
| Trabalhadores mais velhos não afetados | Não-jovens não afetados (β = +0,003, p=0,928) ✓ |
| Efeito mais forte em Automação que Augmentação | Diferença não significativa entre os dois grupos no Brasil |
| Vagas de entrada quebradas | Vagas de entrada **migradas para perfis mais sênior** |
| Persistência: efeito não desaparece com o tempo | Efeito persiste em event study e donut hole ✓ |

A leitura conjunta produz uma narrativa coerente. Em ambos os países, jovens em ocupações expostas à IA são os mais afetados — em magnitudes muito próximas (-13% nos EUA, -13,4% no Brasil). Em ambos os países, há recomposição das contratações para perfis mais sênior. Em ambos os países, o efeito persiste e não é explicado por placebos. A diferença é a margem de ajuste: o mercado americano transmite o choque para emprego; o brasileiro, para salário. A interpretação institucional é direta: instituições importam para a alocação do choque entre preço e quantidade, mas não impedem que o choque chegue. Os jovens, em qualquer dos dois mercados, são os que pagam a maior parte do custo de ajuste.

### **4.6.3 Limitações**

Os achados desta etapa carregam oito limitações relevantes que organizo a seguir.

1. **CAGED apenas formal.** A análise restringe-se ao mercado formal celetista, excluindo a informalidade (cerca de 40% da força de trabalho ocupada brasileira). Como mostrado na Etapa 1, a alta exposição é majoritariamente formal (63%), mas o lado informal não é capturado. Trabalhadores autônomos e MEIs em ocupações expostas podem estar tendo trajetórias diferentes que não chegam a este desenho.
2. **Fluxos, não estoques.** O CAGED mede admissões e desligamentos (fluxos), não estoque de empregos. Um efeito sobre admissões pode refletir, entre outras coisas, redução de rotatividade — empresas mantendo trabalhadores existentes em vez de contratar novos. A leitura do canal volume está condicionada a essa especificidade.
3. **Tratamento sharp.** A definição binária do tratamento em Nov/2022 simplifica a difusão gradual da IA generativa. O event study sugere efeitos crescentes ao longo de 2023 e 2024, mas o desenho não modela explicitamente o roll-out tecnológico.
4. **Janela curta para 2025.** Apenas 6 meses de dados de 2025 estão disponíveis no painel, o que limita a análise de efeitos de médio e longo prazo. A persistência observada até Jun/2025 é encorajadora, mas o quadro completo de ajuste pode ainda estar se desenrolando.
5. **Erro de medida no crosswalk.** Apesar da cobertura de 100% e da correlação 0,915 entre as duas especificações, o crosswalk CBO → ISCO-08 introduz erro de medida que não é observável diretamente. Os testes de robustez sustentam os achados, mas o erro existe.
6. **Singletons em fixed effects.** Para alguns subgrupos demográficos pequenos (ocupações com poucas observações de raça ou subgrupo etário em meses específicos), o `pyfixest` reporta avisos de singletons. O efeito sobre os erros-padrão é mitigado por cluster, mas a precisão local é menor do que o ideal.
7. **Variável de raça com missing parcial.** O CAGED tem cobertura incompleta da variável de raça/cor, especialmente em registros mais antigos. Os efeitos por raça são reportados como exploratórios, e a interpretação é mais cautelosa do que para os recortes de idade e escolaridade.
8. **Índice OIT calibrado globalmente.** O ILO Global Index é construído com referência ao mercado de trabalho global e pode não capturar especificidades brasileiras de uso da IA por ocupação. A correlação entre a estrutura ocupacional brasileira (Etapa 1) e os achados causais (Etapa 2) é encorajadora, mas a calibração do índice é uma escolha externa do desenho.

### **4.6.4 Encerramento**

Os efeitos documentados aqui são iniciais, em uma janela curta, mas estatisticamente robustos e consistentes com a hipótese de que a IA generativa começou a deslocar o preço do trabalho em ocupações altamente expostas no Brasil — com a porta de entrada do mercado formal, os jovens, pagando a maior parte do custo de ajuste. O Capítulo 5 sintetiza os achados das duas etapas, discute implicações para política pública, e organiza uma agenda de pesquisa para os próximos passos.

# 5 Apêncice

### **5.1 Testes de robustez**

Submeti os principais resultados da seção 3.9 (Mincer 2) a três testes de sensibilidade. A Tabela 3.12 sintetiza.

**Tabela 3.12 — Testes de robustez do coeficiente de exposição na equação de Mincer**

| **Especificação** | **Média de exposição** | **Coef. exposição (Mincer)** | **Diferença vs. base** |
| --- | --- | --- | --- |
| Amostra completa (base) | 0,2783 | +0,3927 (*) | — |
| Apenas matches a 4 dígitos (exclui fallback 3-d) | 0,2781 | +0,3970 (*) | +0,0043 |
| Renda winsorizada P1-P99 | 0,2783 | +0,3842 (*) | -0,0085 |
| SE clusterizados por UPA | — | — | (UPA não disponível) |

*Fonte: elaboração própria. Notebook `etapa_1b_analise_dados_ilo_pnadc.ipynb`, seções 8.3 a 8.5.*

Os dois primeiros testes confirmam que os resultados são robustos. Excluir os 1,3% de observações que dependeram do fallback de 3 dígitos no *crosswalk* desloca o coeficiente em apenas +0,004; a winsorização da renda nos percentis 1 e 99 desloca em -0,009. Em ambos os casos, a magnitude da mudança é uma ordem de grandeza inferior aos próprios coeficientes — os achados não são artefatos do crosswalk hierárquico nem de outliers de renda. O terceiro teste (erros-padrão clusterizados pela Unidade Primária de Amostragem, UPA, do desenho da PNADc) não pôde ser executado: a variável `UPA` não está disponível na fonte utilizada (Base dos Dados/BigQuery) para o trimestre analisado. Isso significa que os erros-padrão reportados tratam a amostra como aleatória simples reponderada, e devem ser interpretados como **limites inferiores** da incerteza estatística real — limitação que declaro abaixo.