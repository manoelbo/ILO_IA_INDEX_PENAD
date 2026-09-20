Here is the result of "fetch" for the Page with URL https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e as of 2026-09-19T17:31:56.682Z:
<page url="https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e" icon="icons/iterate_blue">
<ancestor-path>
<parent-data-source url="collection://2c0cc8ca-4610-8023-a801-000bd2bfea2d" name="Projetos"/>
<ancestor-2-database url="https://app.notion.com/p/2c0cc8ca46108006bc9bc543ca92b8a5" title=""/>
</ancestor-path>
<properties>
{"Documentos":["https://app.notion.com/p/33fcc8ca461080d0b1a0ea6a4274e320","https://app.notion.com/p/33fcc8ca461080edacbce8725fbc6df0","https://app.notion.com/p/33fcc8ca4610805696d5dd4dda048926"],"Nome do projeto":"Dissertação de Mestrado V4 - Revisão","Progresso":"formulaResult://2c0cc8ca-4610-8023-a801-000bd2bfea2d/3e0cc8ca-4610-80c0-8ca1-fe386472b72e/a0tqPA","Resumo por IA":"A dissertação analisa a exposição ocupacional à inteligência artificial no Brasil usando o ILO Global Index, identificando que 10 % da força de trabalho (principalmente em funções administrativas) está altamente exposta, concentrada entre mulheres, brancos, jovens e trabalhadores formais; ao aplicar diferença‑em‑diferenças ao CAGED, não há evidência causal robusta de impacto da difusão do ChatGPT – os fluxos de admissões e desligamentos apresentam estimativas negativas porém imprecisas, enquanto o salário real de admissão registra queda de cerca de 5 % sem cumprir o pré‑teste de tendências paralelas; análises de heterogeneidade revelam padrões setoriais e sociodemográficos, mas nenhum efeito significativo persiste após correções de múltiplas comparações, levando à conclusão de que, até o momento, não há confirmação de efeitos concretos da IA no emprego formal brasileiro.","Status":"Em andamento","date:Data de início:is_datetime":0,"date:Data de término:is_datetime":0,"url":"https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e"}
</properties>
<iconMetadata>{"type":"icon","icon":{"name":"iterate","color":"blue"}}</iconMetadata>
<content>
<details>
<summary>Controle da revisão V4</summary>
	**Revisar texto**
	- Revisão em andamento: os rascunhos serão identificados por “REVISAR COM MANÉ” e vinculados aqui por seção.
	**Pendências manuais**
	- Inventário inicial: 36 tabelas e 26 blocos de imagem, dos quais um já estava vazio na Seção 3.2. As 25 imagens com arquivo foram preservadas na cópia local.
</details>
# 1 Introdução
A última geração de modelos de inteligência artificial, que ganhou visibilidade pública a partir do lançamento do ChatGPT 3.5, em novembro de 2022, ampliou, de forma inédita, a capacidade de automatizar ou complementar tarefas cognitivas. Diferentemente de ondas anteriores de automação, em que o alcance se concentrava em atividades manuais e rotineiras, os modelos de linguagem de grande escala (*Large Language Models*, LLMs) atingem ocupações de escritório, finanças, educação, tecnologia e gestão. Nos Estados Unidos, estima-se que 32,1% dos trabalhadores já integravam ferramentas de IA em suas rotinas até o final de 2024, num ritmo de adoção comparável ao do computador pessoal na década de 1980 e superior, em termos populacionais, ao da própria internet ([Bick; Blandin; Deming, 2025](https://doi.org/10.20955/wp.2024.027)). Essa combinação de alcance ocupacional e velocidade de difusão justifica tratar essa nova geração de modelos de inteligência artificial como um problema econômico, e não apenas tecnológico. A maneira como essa tecnologia se espalha pelas ocupações, seus efeitos potenciais sobre emprego, salários e desigualdade passam a ser uma questão central para a economia do trabalho.
A literatura internacional avançou em duas frentes. De um lado, se consolidou uma metodologia de construção de índices de exposição baseados em tarefas, a partir do *GPT Exposure* de [Eloundou ](https://doi.org/10.48550/arXiv.2303.10130)[*et al.*](https://doi.org/10.48550/arXiv.2303.10130)[ (2023)](https://doi.org/10.48550/arXiv.2303.10130), que passou a usar os próprios LLMs como avaliadores das tarefas. De outro, começou a se acumular evidência empírica sobre emprego e salários. Estudos recentes nos Estados Unidos e no Reino Unido documentam quedas relativas no emprego de trabalhadores em início de carreira em firmas ou ocupações mais expostas à IA, padrão concentrado na entrada do mercado de trabalho, mas que não permite uma atribuição causal conclusiva à tecnologia. [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) encontram um diferencial mais visível no emprego do que na remuneração-base; [Hosseini Maasoum e Lichtinger (2026)](https://doi.org/10.2139/ssrn.5425555) documentam menor contratação de trabalhadores juniores em firmas adotantes; e [Klein Teeselink (2025)](https://doi.org/10.2139/ssrn.5516798) encontra reduções no emprego, nas vagas e nos salários anunciados. Essa evidência, no entanto, foi produzida quase inteiramente em economias de alta renda. Permanece uma lacuna importante quando o objeto é um país de renda média, com elevada informalidade, desigualdade racial e regional acentuada e uma estrutura ocupacional distinta da dos países desenvolvidos. É nessa lacuna que o Brasil se encaixa, e é ela que esta dissertação procura ajudar a preencher.
O objetivo desta dissertação é construir e aplicar uma medida de exposição ocupacional à inteligência artificial para o Brasil e investigar se ocupações mais expostas apresentaram mudanças diferenciais nos fluxos e nos salários do emprego formal após a difusão do ChatGPT. Para isso, o trabalho responde a duas perguntas: (i) quais trabalhadores e ocupações estão mais expostos à IA no Brasil? e (ii) ocupações formais mais expostas apresentaram mudanças diferenciais em admissões, desligamentos e salários após a difusão do ChatGPT? A primeira pergunta tem caráter descritivo e distributivo; a segunda, caráter empírico e exploratório sobre a dinâmica do emprego formal.
Para responder a essas perguntas, recorro a duas bases de dados com papéis distintos. A Pesquisa Nacional por Amostra de Domicílios Contínua (PNADc) sustenta a etapa descritiva: por sua representatividade e riqueza de variáveis sociodemográficas, ela permite traçar um retrato de quem está exposto à IA no Brasil. O Cadastro Geral de Empregados e Desempregados (CAGED), por sua vez, sustenta a etapa empírica: como registro administrativo de cobertura plena do mercado formal, ele permite observar admissões, desligamentos e salários no tempo, viabilizando um desenho de diferenças em diferenças em torno do lançamento do ChatGPT. A PNAD responde quem está exposto; o CAGED, o que aconteceu com o emprego formal mais exposto.
A peça que conecta as duas etapas é o índice de exposição. Adotei o *ILO Global Index* de [Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[ (2025)](https://doi.org/10.54394/HETP0387) porque ele é estruturado em torno da ISCO-08, denominador comum para comparações internacionais, e combina avaliação humana de tarefas com classificação assistida por LLMs. Aplicá-lo ao Brasil, no entanto, exigiu uma etapa de tradução: construí um *crosswalk* entre as classificações ocupacionais brasileiras (a COD, usada na PNAD, e a CBO, usada no CAGED) e a ISCO-08. 
Antes de apresentar os primeiros achados do estudo, é importante deixar claro o que significa exposição ocupacional, que mede o potencial de a IA afetar as tarefas de uma ocupação. Uma ocupação está mais exposta quando uma parcela relevante de suas tarefas pode ser automatizada ou complementada por modelos de IA. Exposição não é impacto e não é um indicador de substituição. Vamos explorar essa distinção com mais profundidade na seção 2.
Os resultados descritivos, obtidos ao cruzar a PNADc do 3º trimestre de 2025 com o índice da OIT, cobrem 97,8 milhões de trabalhadores e mostram que 10,1% da força de trabalho está em ocupações altamente expostas. Essa exposição não se distribui de forma neutra: ela se concentra entre trabalhadores de apoio administrativo, mulheres, brancos, jovens e indivíduos com maior escolaridade, padrões consistentes com o que a OIT observa em países de renda média-alta. A formalidade reforça esse recorte: embora a força de trabalho informal seja maior do que a formal, são os trabalhadores com vínculo formal que se concentram nas ocupações de alta exposição (14,8%, contra 6,7% dos informais). Esse ponto é central para a estratégia empírica da dissertação, pois indica que a parcela mais exposta à IA está justamente no mercado formal, onde o CAGED tem cobertura plena. 
Na etapa empírica, segui a abordagem de [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/), com um desenho de diferenças em diferenças aplicado ao CAGED, tomando o lançamento do ChatGPT como marco temporal e o índice da OIT como base para separar os grupos ocupacionais. No agregado nacional, as ocupações expostas apresentam, após o evento, diferenciais de aproximadamente 5,4% a menos nas admissões, 4,2% a menos nos desligamentos e 5,1% a menos no salário real de admissão, em comparação com as ocupações não expostas. O salário é a única estimativa estatisticamente significativa na especificação principal, mas todos os testes nacionais de tendências paralelas falham. Por isso, esses números descrevem diferenças entre os grupos depois do evento, mas não podem ser interpretados como efeitos causados pelo ChatGPT. As análises de heterogeneidade também permanecem exploratórias por causa das tendências prévias, da multiplicidade de testes e das diferenças de suporte amostral. Os exercícios complementares com a RAIS e a PNAD Contínua ampliam a análise para o estoque formal e a informalidade, mas também não têm identificação causal. Em conjunto, os resultados são compatíveis com menores fluxos e menor salário de entrada nas ocupações expostas, sem demonstrar que a difusão da IA causou essas mudanças.
Esta dissertação contribui para a literatura em três dimensões. A primeira é metodológica e de mensuração: comparo as medidas disponíveis, justifico a escolha do índice da OIT, construo as correspondências entre as classificações ocupacionais e integro essa medida às bases brasileiras, deixando explícitos os limites de cada decisão. A segunda é distributiva: mostro quem está mais exposto à IA no mercado de trabalho brasileiro, considerando ocupações, setores, regiões e características sociodemográficas. A terceira é empírica: documento como admissões, desligamentos e salários de entrada variaram nas ocupações formais mais expostas após novembro de 2022, com atenção às heterogeneidades e aos limites de identificação do desenho.
O restante do trabalho está organizado da seguinte forma. A Seção 2 introduz a teoria e a metodologia dos índices de exposição à IA e justifica a escolha do *ILO Global Index*. A Seção 3 descreve a construção da base analítica com a PNADc e apresenta os resultados descritivos sobre a distribuição da exposição no Brasil. A Seção 4 apresenta a estratégia empírica com o CAGED, detalhando a construção do painel ocupação-mês, a correspondência entre a CBO e o índice da OIT, a especificação de diferenças em diferenças e o desenho das heterogeneidades. A Seção 5 reúne os resultados nacionais e as heterogeneidades por sexo, raça, idade, escolaridade e renda. A Seção 6 conclui, recolhendo o que os dados mostram, o que o desenho não permite afirmar e a agenda de pesquisa que decorre de ambos.
# 2 Mensuração da exposição ocupacional à IA
## 2.1 Definição e interpretação da exposição ocupacional
Antes de discutir como medir, é preciso definir o que está sendo medido. O debate público sobre mercado de trabalho mistura com frequência três coisas distintas, e tratá-las como sinônimos leva a interpretações equivocadas. Por isso, começo separando os conceitos e fixando uma definição explícita de exposição que será usada ao longo de todo o trabalho.
Nesta dissertação, defino *exposição ocupacional* como o potencial de uma ocupação ser afetada pela IA, dado o conjunto de tarefas que a compõem. Uma ocupação é mais exposta quando uma parcela relevante de suas tarefas pode ser automatizada ou complementada por modelos de IA. A exposição é, portanto, uma medida de potencial técnico, e não um diagnóstico do que já aconteceu no mercado.
É importante separar a exposição de outros dois conceitos com os quais ela costuma ser confundida. A *adoção efetiva* da tecnologia depende de empresas, trabalhadores, custos, infraestrutura digital, regulação, incentivos e da capacidade de reorganizar processos produtivos; uma ocupação pode ser altamente exposta e mesmo assim ter adoção baixa. Os *efeitos sobre emprego e salários*, por sua vez, só podem ser identificados empiricamente depois que a tecnologia começa a se difundir. Em resumo: exposição não é adoção, não é impacto causal e não é um indicador de substituição automática. Ela mede apenas o quanto as tarefas de uma ocupação são, em princípio, alcançáveis pela IA.
Feita essa delimitação, podemos explorar como índices de exposição ocupacional à IA são construídos.
## 2.2 Fundamentos conceituais: tarefas, automação e complementaridade
A mensuração da exposição se apoia em uma escolha conceitual bem estabelecida na economia do trabalho: a abordagem baseada em tarefas. [Autor, Levy e Murnane (2003)](https://doi.org/10.1162/003355303322552801) formalizam e testam um modelo no qual um emprego é entendido como um conjunto de tarefas. Essa abordagem muda nossa perspectiva de maneira objetiva: novas tecnologias não impactam ocupações inteiras de forma homogênea; elas impactam as tarefas que constituem essas ocupações.
Um experimento com radiologistas ilustra bem esse ponto. No estudo de [Agarwal ](https://doi.org/10.3386/w31422)[*et al.*](https://doi.org/10.3386/w31422)[ (2023)](https://doi.org/10.3386/w31422), as previsões da IA foram mais precisas do que as de aproximadamente dois terços dos 180 radiologistas participantes. A classificação de imagens é uma tarefa central, mas o fluxo diagnóstico também incorpora o histórico clínico, a solicitação do exame, o relato dos achados e recomendações. Os avanços da tecnologia podem, portanto, automatizar parte do trabalho sem tornar automaticamente substituível a profissão inteira. Enxergar ocupações como conjuntos de tarefas permite uma leitura mais realista do que pode acontecer com cada profissão e com o mercado de trabalho.
Desse mesmo arcabouço vem uma segunda distinção essencial, também associada a Autor, que ajuda a sair de uma visão binária em que a IA simplesmente substitui trabalhadores. Para uma dada tarefa, há dois cenários possíveis:
- **Automação**: a IA executa a tarefa sozinha, com a mesma qualidade e em menos tempo. Um tradutor focado em documentos empresariais, por exemplo, pode ter parte relevante de seu trabalho automatizada.
- **Complementaridade**: um profissional usa a IA para executar a tarefa com mais qualidade ou eficiência. Um atendente de telefone pode usar a IA para buscar e formular respostas melhores em tempo real, tornando seu trabalho mais eficaz sem ser substituído.
Essa distinção é central para interpretar corretamente os índices: um grau alto de exposição não significa, necessariamente, automação. Uma ocupação muito exposta pode estar caminhando para a complementaridade, não para a extinção. É por isso que medir exposição é diferente de prever desemprego, e é também por isso que a forma como cada índice trata automação e complementaridade importa para o que a pontuação de exposição (score) efetivamente mede.
## 2.3 Índices de exposição à IA na literatura
A partir desse base teórica, grupos acadêmicos e centros de pesquisa passaram a construir *índices de exposição à IA*: medidas que avaliam o quanto cada tarefa de uma ocupação está exposta à IA e agregam essas avaliações em uma pontuação por ocupação. Apesar de metodologias distintas, esses índices compartilham uma estrutura comum: produzem um valor contínuo, tipicamente entre 0 e 1, e o associam a classificações ocupacionais padronizadas, o que permite integrá-los a pesquisas domiciliares e registros administrativos.
Analisar e comparar os índices de exposição já existentes foi uma parte fundamental deste trabalho: a comparação permitiu identificar qual deles tinha maior correspondência com os dados e o cenário brasileiro e explicitar as diferenças entre suas estratégias de construção. Para isso, comparei quatro índices olhando para três pontos principais: em que base ocupacional cada um se apoia, como mede a exposição e o quanto se adapta ao contexto brasileiro.
O **GPT Exposure**, de [Eloundou ](https://doi.org/10.48550/arXiv.2303.10130)[*et al.*](https://doi.org/10.48550/arXiv.2303.10130)[ (2023)](https://doi.org/10.48550/arXiv.2303.10130), foi desenvolvido por pesquisadores da OpenAI e da Universidade da Pensilvânia com base na O\*NET/SOC dos Estados Unidos. O estudo compara anotações humanas e classificações produzidas pelo GPT-4, com concordância de 80,8% e 82,1% em duas das três medidas e de 65,6% na terceira. No nível da tarefa, aplica uma taxonomia discreta baseada na possibilidade de reduzir em pelo menos 50% o tempo necessário, mantendo a qualidade; na agregação ocupacional, combina essas categorias em medidas graduadas de exposição. 
O **GENOE**, de [Benítez e Parrado (2024)](https://doi.org/10.18235/0013125), também se apoia na O\*NET, mas altera o prompt fornecido ao modelo: em vez de avaliar tarefas isoladas, informa o nome da ocupação e o vetor completo de tarefas. Essa avaliação holística permite que o modelo considere implicitamente diferenças de contexto, inclusive aspectos éticos e sociais, ao comparar ocupações. 
O **Anthropic Economic Index**, de [Appel ](https://www.anthropic.com/research/economic-index-primitives)[*et al.*](https://www.anthropic.com/research/economic-index-primitives)[ (2026)](https://www.anthropic.com/research/economic-index-primitives), parte de conversas reais de usuários com os modelos Claude. Além dos padrões de colaboração classificados como automação ou ampliação das capacidades humanas, o relatório introduz cinco dimensões econômicas, entre elas a *autonomia, *o grau em que o usuário delega decisões à máquina, e a *taxa de sucesso* da tarefa. 
O **ILO Global Index**, de [Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[ (2025)](https://doi.org/10.54394/HETP0387), é estruturado na **ISCO-08**, a Classificação Internacional Uniforme de Ocupações. Sua classificação combina validação humana e LLMs em três camadas: 1.640 trabalhadores avaliaram tarefas de sua própria área, um painel de especialistas revisou um subconjunto para avaliar a viabilidade prática da automação, e os modelos GPT-4o e Gemini Flash 1.5 atuaram como desempate nos casos de divergência. Esse gabarito validado por humanos foi então usado para escalar a classificação às 3.265 tarefas da ISCO-08. Além disso, o índice combina a média das pontuações atribuídas às tarefas de cada ocupação com seu desvio-padrão, que mede a dispersão entre essas tarefas. Essa combinação classifica as ocupações pelo nível e pela variabilidade da exposição potencial. Ela não prevê quais profissões serão preservadas ou extintas ([Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[, 2025, p. 37–38, 44](https://doi.org/10.54394/HETP0387)).
**Tabela 2.1 — Comparação dos índices de exposição à IA**
<table fit-page-width="true" header-row="true" header-column="true">
<tr>
<td>**Índice**</td>
<td>**Base ocupacional**</td>
<td>**Como classifica a exposição**</td>
<td>**Principal vantagem**</td>
<td>**Principal limitação para o Brasil**</td>
<td>**Papel na dissertação**</td>
</tr>
<tr>
<td>GPT Exposure ([Eloundou ](https://doi.org/10.48550/arXiv.2303.10130)[*et al.*](https://doi.org/10.48550/arXiv.2303.10130)[, 2023](https://doi.org/10.48550/arXiv.2303.10130))</td>
<td>O\*NET / SOC (EUA)</td>
<td>LLM avaliando tarefa a tarefa, validado contra humanos; critério categórico (redução de 50% do tempo)</td>
<td>Taxonomia explícita por tarefa e comparação entre anotações humanas e do GPT-4</td>
<td>A classificação por tarefa é discreta; a taxonomia americana exige *crosswalk* adicional</td>
<td>Referência conceitual</td>
</tr>
<tr>
<td>GENOE ([Benítez; Parrado, 2024](https://publications.iadb.org/en/mirror-mirror-wall-which-jobs-will-ai-replace-after-all-new-index-occupational-exposure))</td>
<td>O\*NET / SOC (EUA)</td>
<td>LLM recebe o nome da ocupação e o vetor completo de tarefas</td>
<td>Sensível a barreiras sociais e institucionais</td>
<td>Avaliações inteiramente sintéticas, sem validação direta por especialistas — a aferição é indireta, pela replicação do AIOE; base americana</td>
<td>Comparação</td>
</tr>
<tr>
<td>Anthropic Economic Index ([Appel ](https://www.anthropic.com/research/economic-index-primitives)[*et al.*](https://www.anthropic.com/research/economic-index-primitives)[, 2026](https://www.anthropic.com/research/economic-index-primitives))</td>
<td>Conversas globais com Claude; O\*NET/SOC e BLS na análise ocupacional</td>
<td>Uso efetivo dos modelos; dimensões de autonomia e taxa de sucesso</td>
<td>Mede uso real; distingue automação de complementaridade</td>
<td>Viés de amostragem (apenas usuários de modelos específicos); base americana</td>
<td>Comparação</td>
</tr>
<tr>
<td>ILO Global Index ([Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[, 2025](https://doi.org/10.54394/HETP0387))</td>
<td>ISCO-08 (internacional)</td>
<td>Validação em três camadas (trabalhadores, especialistas e LLMs) escalada por LLM; média e desvio padrão das tarefas</td>
<td>Validação em múltiplas etapas e comparabilidade internacional via ISCO-08</td>
<td>Índice global; pode não captar especificidades brasileiras; sua aplicação exige *crosswalk* COD/CBO–ISCO</td>
<td>Índice principal</td>
</tr>
</table>
## 2.4 Escolha do índice da OIT e adaptação às bases brasileiras
Esta dissertação adota o **ILO Global Index** de [Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[ (2025)](https://doi.org/10.54394/HETP0387) como medida principal de exposição ocupacional à inteligência artificial. A escolha se apoia na arquitetura do índice em torno da ISCO-08, que funciona como denominador comum para os mapeamentos entre classificações nacionais, e em sua combinação de avaliação humana com classificação assistida por modelos de linguagem.
O índice da OIT é construído com base na **ISCO-08**, a classificação internacional de ocupações. Isso facilita sua aplicação ao Brasil porque as duas classificações ocupacionais usadas nesta dissertação se relacionam com a família ISCO. A PNAD Contínua utiliza a **COD**, classificação do IBGE derivada da ISCO-08. Já o CAGED utiliza a **CBO 2002**, que não é idêntica à ISCO-08, mas foi construída tomando a **ISCO-88** como referência. Como existe uma tabela oficial de correspondência entre **ISCO-88** e **ISCO-08**, é possível construir uma ponte entre as famílias ocupacionais da CBO e o índice da OIT, ainda que com mais cautela do que no caso da PNAD. A forma como esse *crosswalk* foi construído será detalhada nas Seções 3 e 4.
O segundo critério é metodológico. O índice da OIT combina avaliação humana das tarefas com predição de pontuações assistida por modelos de linguagem. Na classificação das ocupações, ele considera tanto a média das pontuações de exposição quanto sua dispersão entre tarefas, medida pelo desvio-padrão. Isso permite diferenciar as ocupações pelo nível e pela distribuição da exposição potencial, sem tratar a classificação como uma previsão de complementação, substituição ou impacto sobre o emprego.
## 2.5 Limitações da medida de exposição
Fechando a seção, vale delimitar com clareza o que o índice de exposição não mede. Essa delimitação protege o trabalho de interpretações exageradas e ajuda a ler corretamente os resultados das seções seguintes.
- **Não mede uso efetivo de IA nas firmas.** O índice capta o potencial técnico das tarefas, não a adoção real da tecnologia por empresas e trabalhadores, que depende de custos, infraestrutura, regulação e incentivos.
- **Não mede impacto causal.** Exposição é uma medida ex-ante de potencial; por si só, ela não indica o que de fato acontece com emprego e salários. Qualquer afirmação sobre efeitos exige um desenho empírico próprio, apresentado na Seção 4.
- **Não mede substituição automática.** Um grau alto de exposição é compatível tanto com automação quanto com complementaridade. O índice não distingue, no nível da ocupação, se a IA substituirá ou apenas auxiliará o trabalhador.
- **Depende de um crosswalk ocupacional.** A aplicação às bases brasileiras passa por uma correspondência entre a ISCO-08 e as classificações nacionais (COD e CBO), que não é perfeita e introduz erro de medida, mais relevante no CAGED.
- **É um índice global.** Por ser construído a partir de uma taxonomia internacional, o índice pode não capturar particularidades do conteúdo das tarefas no contexto brasileiro, como diferenças de organização do trabalho, informalidade e composição setorial.
Em resumo: a exposição é um ponto de partida para descrever quem está mais sujeito a ter seu trabalho afetado pela inteligência artificial no Brasil.
# 3 Análise descritiva
Esta seção apresenta a análise descritiva da exposição do mercado de trabalho brasileiro à inteligência artificial. A base analítica e os principais resultados foram obtidos ao integrar os microdados da PNAD Contínua ao índice de exposição da OIT, o que permitiu produzir o conjunto de análises descritivas aqui reportados.
## **3.1 Base analítica e amostra**
A base analítica desta etapa combina os microdados da PNAD Contínua do 3º trimestre de 2025, produzida pelo IBGE, com os escores ocupacionais do **ILO Global Index** de [Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[ (2025)](https://doi.org/10.54394/HETP0387). Optei pelo 3º trimestre de 2025 por ser o período mais recente com microdados completos disponíveis no momento da análise, o que permite retratar a estrutura ocupacional brasileira já sob ampla difusão da inteligência artificial. Da pesquisa, selecionei 15 variáveis que cobrem características demográficas, ocupacionais, salariais e de jornada. As observações passaram por filtros conservadores: remoção de dados faltantes críticos, restrição à faixa etária de 18 a 65 anos e exclusão de códigos de ocupação inválidos. Ponderado pelo peso amostral V1028, o universo final representa 97,8 milhões de trabalhadores ocupados.
A ponte entre os dois conjuntos de dados é o *crosswalk* entre a COD, classificação da PNADc, e a ISCO-08, na qual o índice da OIT é construído. Como a COD deriva da ISCO-08 e compartilha a mesma estrutura hierárquica de quatro dígitos, a correspondência direta funciona para a grande maioria dos casos; nos casos sem match exato, adotei uma estratégia hierárquica de *fallback*, buscando correspondência a 3 e depois a 2 dígitos e atribuindo a pontuação média do subgrupo. Na prática, 97,9% das observações encontraram correspondência exata e a cobertura final ficou em 99,2%. 
Três limitações devem ser registradas. Primeiro, a análise se apoia em um trimestre específico (3T/2025), o que oferece um retrato transversal, e não uma trajetória temporal. Segundo, a restrição etária de 18 a 65 anos deixa de fora trabalhadores nas pontas da distribuição de idade. Terceiro, apesar da cobertura elevada, o crosswalk COD-ISCO ainda comporta erros residuais de mapeamento. 
A Tabela 3.1 sintetiza a ficha técnica da base analítica final, organizada em três blocos: as características da PNAD (fonte, universo e amostra), a qualidade do cruzamento COD-ISCO e as dimensões analíticas usadas adiante.
**Tabela 3.1: Ficha técnica da base analítica final**
<table header-row="true">
<tr>
<td>**Item**</td>
<td>**Valor**</td>
</tr>
<tr>
<td>**Fonte, universo e amostra**</td>
<td></td>
</tr>
<tr>
<td>Fonte</td>
<td>PNADc 3T/2025 (IBGE) + ILO Working Paper 140 ([Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[, 2025](https://doi.org/10.54394/HETP0387))</td>
</tr>
<tr>
<td>Universo</td>
<td>População ocupada de 18 a 65 anos com código de ocupação válido</td>
</tr>
<tr>
<td>Observações na amostra</td>
<td>207.901</td>
</tr>
<tr>
<td>População representada</td>
<td>97,8 milhões</td>
</tr>
<tr>
<td>Peso amostral</td>
<td>V1028 (projeção populacional trimestral)</td>
</tr>
<tr>
<td>**Cobertura ocupacional e qualidade do merge**</td>
<td></td>
</tr>
<tr>
<td>Ocupações ISCO-08</td>
<td>427</td>
</tr>
<tr>
<td>Ocupações COD com match</td>
<td>422 (de 428 presentes na PNAD)</td>
</tr>
<tr>
<td>Cobertura da pontuação (% da população)</td>
<td>99,2%</td>
</tr>
<tr>
<td>Match a 4 dígitos</td>
<td>97,9%</td>
</tr>
<tr>
<td>Match a 3 dígitos</td>
<td>1,3%</td>
</tr>
<tr>
<td>Sem classificação</td>
<td>0,8%</td>
</tr>
<tr>
<td>**Dimensões analíticas**</td>
<td></td>
</tr>
<tr>
<td>Unidades federativas</td>
<td>27</td>
</tr>
<tr>
<td>Setores agregados (CNAE Dom. 2.0, seções A a T)</td>
<td>19</td>
</tr>
<tr>
<td>Salário mínimo de referência</td>
<td>R\$ 1.518 ([Brasil, 2024](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12342.htm))</td>
</tr>
</table>
## **3.2 Distribuição agregada da exposição à IA no Brasil**
A exposição média ponderada do mercado de trabalho brasileiro à inteligência artificial é de 0,278. Mas a metodologia do ILO Global Index vai além da média simples: ela organiza as ocupações em gradientes de exposição. A formulação do gradiente cruza a nota média de exposição da ocupação (*μ*) com a dispersão das pontuações de suas tarefas, medida pelo desvio-padrão (*σ*). Em termos intuitivos, uma média alta acompanhada de baixo desvio-padrão indica que a exposição está distribuída de modo mais homogêneo entre as tarefas; uma média alta com maior dispersão indica uma composição mais heterogênea, com tarefas de exposição distinta.
Antes de ler a Tabela 3.2, vale relacionar a tradução aos termos usados no artigo da OIT. O estudo chama as categorias de *Not Exposed*, *Minimal Exposure* e *Exposure Gradients 1 a 4*. Neste trabalho, elas aparecem como “Não expostas”, “Exposição mínima” e “Gradientes 1 a 4”. Os Gradientes 1 e 2 reúnem ocupações com exposição baixa ou moderada à IA generativa e alta variabilidade entre suas tarefas. O Gradiente 3 corresponde a exposição significativa, mas ainda heterogênea entre tarefas. Já o Gradiente 4 reúne ocupações com a maior exposição e baixa variabilidade: a maior parte de suas tarefas apresenta alto potencial de automação por IA generativa.
A Tabela 3.2 apresenta a distribuição da população ocupada por gradiente de exposição.
**Tabela 3.2: População ocupada por gradiente de exposição à IA**
<table header-row="true">
<tr>
<td>**Categoria**</td>
<td>**Interpretação**</td>
<td>**População (milhões)**</td>
<td>**%**</td>
</tr>
<tr>
<td>Não exposto</td>
<td>Ocupações sem exposição relevante</td>
<td>52,2</td>
<td>53,9</td>
</tr>
<tr>
<td>Exposição mínima</td>
<td>Exposição residual ou pontual</td>
<td>15,2</td>
<td>15,7</td>
</tr>
<tr>
<td>Gradiente 1</td>
<td>Exposição parcial; tarefas potencialmente complementadas pela IA</td>
<td>8,7</td>
<td>9,0</td>
</tr>
<tr>
<td>Gradiente 2</td>
<td>Exposição parcial mais intensa; complementação provável</td>
<td>10,0</td>
<td>10,3</td>
</tr>
<tr>
<td>Gradiente 3</td>
<td>Alta exposição; transformação profunda das tarefas</td>
<td>4,8</td>
<td>4,9</td>
</tr>
<tr>
<td>Gradiente 4</td>
<td>Exposição máxima; tarefas potencialmente substituíveis</td>
<td>5,0</td>
<td>5,1</td>
</tr>
<tr>
<td>Sem classificação</td>
<td>Pontuação atribuída por agregação ISCO; gradiente não reportado pelo WP140</td>
<td>1,0</td>
<td>1,1</td>
</tr>
</table>
*Nota: o agrupamento do ILO combina a média (μ) e o desvio padrão (σ) das pontuações de tarefa. Exposição mínima: μ \< 0,5 e μ+σ \> 0,4. Gradiente 1: μ \< 0,4 e μ+σ ≥ 0,5. Gradiente 2: 0,4 ≤ μ \< 0,5 e μ+σ ≥ 0,5. Gradiente 3: 0,5 ≤ μ \< 0,6 e μ+σ ≥ 0,5. Gradiente 4: μ ≥ 0,6 e μ−σ ≥ 0,5. "Sem classificação" reúne cerca de 1,1% da população, com pontuação atribuída por agregação ISCO, nível em que o *[Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[, 2025](https://doi.org/10.54394/HETP0387)* não reporta gradiente.*
A leitura por gradiente é o resultado central desta seção. Mais da metade da força de trabalho brasileira, 53,9% ou 52,2 milhões de pessoas, está em ocupações classificadas como “Não Expostas”, predominantemente ocupações elementares, da agropecuária, da construção e da indústria de transformação tradicional. Outros 15,7%, ou 15,2 milhões de pessoas, estão na categoria de “Exposição Mínima”.<br><br>Os Gradientes 1 e 2, caracterizados por exposição baixa ou moderada à IA e alta variabilidade entre tarefas, reúnem 9,0% e 10,3% da população ocupada, respectivamente. Os Gradientes 3 e 4 somam 9,8 milhões de trabalhadores, ou 10,1% da força de trabalho ocupada. O Gradiente 3 indica exposição significativa, mas heterogênea entre tarefas; o Gradiente 4 combina a maior exposição com baixa variabilidade, de modo que a maior parte das tarefas apresenta alto potencial de automação por IA generativa.
A Figura 3.1 detalha o formato dessa distribuição por meio do histograma ponderado de pontuações, com a curva de densidade (KDE) sobreposta.
**Figura 3.1: Distribuição da exposição à IA no Brasil**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/e293fd6c-05a8-47c8-8aca-b0ee093f3113/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173158Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=f3d95ce2fe50f7980039d1c6ebadd4af010225c490b635c0b4ad030a5b072a76&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A figura evidencia que, para uma mesma faixa de pontuação média, podem coexistir diferentes gradientes; entre 0,2 e 0,4, em particular, a exposição da população é mais heterogênea.
A Figura 3.2 resume a mesma informação em termos de contingente populacional por gradiente.
**Figura 3.2: População ocupada por gradiente de exposição à IA**
![]()
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/04f3793a-74c8-4d47-82d0-6a5085acbc8c/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173158Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=cf32e81919768b942700240080e34316d7cbc8f8212af1ede0750d51e5346e12&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
A OIT estimou a proporção de trabalhadores com alta exposição à inteligência artificial (Gradientes 3 e 4) para diferentes grupos de países, o que permite uma comparação informativa com os dados encontrados neste estudo. A taxa de trabalhadores altamente expostos no Brasil (10,1%) fica ligeiramente acima da estimativa global da OIT (7,5%) e do padrão projetado para países de renda média-alta (7,0%). No entanto, a distância é expressiva quando comparamos o mercado brasileiro às economias de alta renda, em que a alta exposição atinge 17,3% da força de trabalho. Essa diferença reflete a estrutura ocupacional do país, caracterizada por um peso ainda expressivo de ocupações em setores de baixa exposição tecnológica, como a indústria de transformação tradicional e a agropecuária.
## **3.3 Ocupações mais expostas à IA**
Como o índice de exposição é construído no nível ocupacional, o ponto de partida natural é identificar quais ocupações estão no topo da distribuição. A Figura 3.3 mostra a composição da população ocupada por faixa de pontuação, segundo o grande grupo ocupacional.
**Figura 3.3: Composição da população ocupada por faixa de pontuação de exposição à IA, segundo o grande grupo ocupacional**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/de6695ff-4024-40a3-aea8-e9e92f611c5d/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173158Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=8c31233f6afaee2fce234980721e3e70c34ee079812e35f67df8a6026a209a52&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A figura evidencia uma moda em torno de 0,12 a 0,18, formada por ocupações elementares, da indústria e da agropecuária, e uma cauda secundária por volta de 0,55 a 0,65, composta sobretudo por trabalhadores do apoio administrativo.
A Tabela 3.3 detalha as cinco ocupações em alta exposição com maior contingente de trabalhadores na PNADc. A seleção, portanto, não corresponde às maiores pontuações médias absolutas, mas às ocupações dos Gradientes 3 e 4 que concentram mais trabalhadores. No Anexo 1.1 consta a tabela completa, com a média de exposição, o gradiente e o contingente estimado de cada ocupação segundo a COD.
**Tabela 3.3: Top 5 ocupações em alta exposição com maior contingente de trabalhadores**
<table header-row="true">
<tr>
<td>**COD**</td>
<td>**Ocupação (descrição ISCO-08)**</td>
<td>**Exposição média**</td>
<td>**Pop. (milhões)**</td>
<td>**Grande grupo**</td>
</tr>
<tr>
<td>4110</td>
<td>Auxiliares de escritório em geral</td>
<td>0,60</td>
<td>3,75</td>
<td>Apoio administrativo</td>
</tr>
<tr>
<td>4226</td>
<td>Caixas, bilheteiros e atendentes em estabelecimentos</td>
<td>0,57</td>
<td>1,04</td>
<td>Apoio administrativo</td>
</tr>
<tr>
<td>2411</td>
<td>Contabilistas</td>
<td>0,51</td>
<td>0,59</td>
<td>Profissionais das ciências</td>
</tr>
<tr>
<td>4120</td>
<td>Secretários administrativos e executivos</td>
<td>0,58</td>
<td>0,50</td>
<td>Apoio administrativo</td>
</tr>
<tr>
<td>2431</td>
<td>Profissionais de marketing, propaganda e relações públicas</td>
<td>0,55</td>
<td>0,43</td>
<td>Profissionais das ciências</td>
</tr>
</table>
A leitura confirma um padrão comum às análises baseadas em índices de exposição: as ocupações mais expostas à IA são as chamadas *white collar*. Em termos econômicos, estamos nos referindo a funções administrativas e de escritório, centradas em tarefas rotineiras, textuais, contábeis e de atendimento, e em geral associadas a maior escolaridade. O ponto central é que a exposição é ocupacional, não setorial: ela acompanha o tipo de tarefa executada, e não o ramo de atividade da empresa. Por isso, a próxima subseção mostra onde esses trabalhadores estão distribuídos.
## **3.4 Distribuição setorial e regional dos trabalhadores em alta exposição**
Identificadas as ocupações que puxam a exposição, resta mapear onde se encontram os trabalhadores em alta exposição. Convém lembrar, antes, que o trabalho *white collar* existe em praticamente todos os setores da economia: uma indústria tem contabilidade e um hospital tem equipe administrativa. Por isso, não se deve ler a distribuição setorial como se apenas alguns ramos fossem alcançados pela IA; todos os setores têm trabalhadores em ocupações potencialmente expostas, em maior ou menor grau.
A Tabela 3.4 apresenta a distribuição dos trabalhadores em alta exposição por setor, distinguindo duas dimensões: a intensidade da exposição, isto é, a proporção de trabalhadores em alta exposição dentro de cada setor, e o volume, ou seja, o número absoluto de trabalhadores nessa condição. Essa distinção é importante porque setores pequenos podem ter alta intensidade de exposição, enquanto setores grandes podem concentrar maior número de trabalhadores expostos.
**Tabela 3.4: Exposição à IA por setor (CNAE-Domiciliar 2.0, IBGE)**
<table header-row="true">
<tr>
<td>Setor</td>
<td>Total (M)</td>
<td>% BR</td>
<td>Exposição Média</td>
<td>Alta (M)</td>
<td>Alta (%)</td>
</tr>
<tr>
<td>Finanças e Seguros</td>
<td>1.53</td>
<td>1.6</td>
<td>0.512</td>
<td>0.84</td>
<td>54.9</td>
</tr>
<tr>
<td>Informação e Comunicação</td>
<td>1.73</td>
<td>1.8</td>
<td>0.456</td>
<td>0.55</td>
<td>31.9</td>
</tr>
<tr>
<td>Serviços Profissionais</td>
<td>4.07</td>
<td>4.2</td>
<td>0.420</td>
<td>1.27</td>
<td>31.2</td>
</tr>
<tr>
<td>Atividades Imobiliárias</td>
<td>0.70</td>
<td>0.7</td>
<td>0.386</td>
<td>0.12</td>
<td>17.8</td>
</tr>
<tr>
<td>Administração Pública</td>
<td>4.27</td>
<td>4.5</td>
<td>0.352</td>
<td>1.12</td>
<td>26.3</td>
</tr>
<tr>
<td>Comércio</td>
<td>17.83</td>
<td>18.6</td>
<td>0.342</td>
<td>1.36</td>
<td>7.7</td>
</tr>
<tr>
<td>Artes e Cultura</td>
<td>1.10</td>
<td>1.1</td>
<td>0.316</td>
<td>0.10</td>
<td>9.4</td>
</tr>
<tr>
<td>Saúde</td>
<td>6.19</td>
<td>6.5</td>
<td>0.300</td>
<td>0.85</td>
<td>13.7</td>
</tr>
<tr>
<td>Serviços Administrativos</td>
<td>4.37</td>
<td>4.6</td>
<td>0.294</td>
<td>0.82</td>
<td>18.8</td>
</tr>
<tr>
<td>Utilidades</td>
<td>0.72</td>
<td>0.8</td>
<td>0.293</td>
<td>0.11</td>
<td>15.2</td>
</tr>
<tr>
<td>Educação</td>
<td>7.18</td>
<td>7.5</td>
<td>0.290</td>
<td>0.65</td>
<td>9.0</td>
</tr>
<tr>
<td>Transporte</td>
<td>5.72</td>
<td>6.0</td>
<td>0.280</td>
<td>0.46</td>
<td>8.0</td>
</tr>
<tr>
<td>Alojamento e Alimentação</td>
<td>5.09</td>
<td>5.3</td>
<td>0.266</td>
<td>0.23</td>
<td>4.4</td>
</tr>
<tr>
<td>Ind. Extrativa</td>
<td>0.59</td>
<td>0.6</td>
<td>0.262</td>
<td>0.04</td>
<td>6.4</td>
</tr>
<tr>
<td>Ind. Transformação</td>
<td>11.31</td>
<td>11.8</td>
<td>0.245</td>
<td>0.76</td>
<td>6.7</td>
</tr>
<tr>
<td>Outros Serviços</td>
<td>4.04</td>
<td>4.2</td>
<td>0.219</td>
<td>0.25</td>
<td>6.3</td>
</tr>
<tr>
<td>Serviços Domésticos</td>
<td>5.30</td>
<td>5.5</td>
<td>0.160</td>
<td>0.00</td>
<td>0.0</td>
</tr>
<tr>
<td>Agropecuária</td>
<td>6.97</td>
<td>7.3</td>
<td>0.155</td>
<td>0.06</td>
<td>0.8</td>
</tr>
<tr>
<td>Construção</td>
<td>7.23</td>
<td>7.5</td>
<td>0.146</td>
<td>0.18</td>
<td>2.5</td>
</tr>
</table>
*Nota: universo de ocupados classificáveis (cerca de 96 milhões, excluindo "Sem classificação"). Setores derivados das seções A a T da CNAE-Domiciliar 2.0 (IBGE), a partir da variável V4013. "Exposição Média" é a média ponderada da pontuação contínua de exposição (0 a 1); "Alta (M)" e "Alta (%)" referem-se aos trabalhadores em Gradientes 3 e 4.*
A Tabela 3.4 mostra que Finanças e Seguros lidera em intensidade de exposição, com 54,9% de seus trabalhadores em ocupações de alta exposição (Gradientes 3 e 4). Essa participação indica amplo alcance técnico potencial, não adoção da tecnologia ou transformação já realizada. Em termos absolutos, o Comércio concentra o maior contingente, com aproximadamente 1,36 milhão de trabalhadores em ocupações de alta exposição. A relevância descritiva, nesse caso, está menos na proporção interna do setor e mais no número de pessoas potencialmente alcançadas. Assim, a exposição à IA não se restringe aos setores de tecnologia: ela aparece em ocupações administrativas e profissionais distribuídas por diferentes atividades econômicas.
A mesma capilaridade aparece na dimensão regional. Os 9,8 milhões de trabalhadores em alta exposição não são exclusivos de um setor, e tampouco se concentram em um único polo: eles se espalham por todos os estados do país. A Figura 3.4 mapeia simultaneamente o volume absoluto e a proporção de trabalhadores em alta exposição em relação à força de trabalho de cada estado.
**Figura 3.4: Alta exposição à IA por estado**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/1373c5b8-11db-48c3-9b4e-2f5137efbaa0/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173158Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=cc179575e25f458eb59edee2a9d4ab57290c8639d2061a9ea8e209270d06ddf0&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
São Paulo concentra o maior contingente em termos absolutos: 2,8 milhões de trabalhadores, o que representa cerca de 12% da força de trabalho paulista. Esse resultado é esperado, pois o estado abriga a maior economia do país, com a maior concentração de sedes corporativas e serviços financeiros. Outros estados, como a Bahia, apresentam proporções consideravelmente menores, reflexo de uma estrutura ocupacional com maior peso de setores agrícolas, industriais e de serviços de baixa exposição.
O caso mais ilustrativo é o Distrito Federal. Apesar de ter uma força de trabalho relativamente pequena em termos absolutos, o DF apresenta a maior proporção de trabalhadores em alta exposição entre todas as UFs, consequência direta do seu perfil ocupacional: capital do país, com altíssima concentração de servidores públicos, analistas, profissionais técnicos e funções administrativas ligadas à máquina pública federal. É o caso em que a proporção diz mais do que o número absoluto.
A leitura conjunta do volume e da proporção mostra que a alta exposição à IA está distribuída por todo o território nacional, embora tenha maior peso relativo no Distrito Federal, no Rio de Janeiro e em São Paulo. Essas diferenças refletem, sobretudo, a composição ocupacional de cada estado e ajudam a localizar onde o potencial de exposição é maior. Elas não demonstram que a IA já tenha alterado o emprego ou os salários nessas regiões.
## **3.5 Perfil sociodemográfico**
Esta subseção caracteriza o perfil dos trabalhadores brasileiros mais expostos à IA . Como a exposição está concentrada em ocupações administrativas, técnicas e profissionais, ela não se distribui aleatoriamente entre os grupos sociais: decorre da posição dos trabalhadores na estrutura ocupacional. Os resultados mostram maior exposição entre trabalhadores mais escolarizados, mulheres, brancos, jovens e formais, além de concentração relevante nas faixas intermediárias de renda. Os recortes a seguir detalham esse padrão.
### **3.5.1 Análise por sexo**
A Figura 3.5 compara a exposição de mulheres e homens.
**Figura 3.5: Exposição à IA por sexo**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/be72584a-ec5f-4be2-9fdd-3ddc197b68d4/7c9d0510-dd42-485a-99f5-5c38939958ad.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173158Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=64bc140bfde0ae907ffb864622c7bc3afc77c2b1a9dd0d9cbce9f7306ce6a405&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A exposição média das mulheres (0,303) é 0,044 ponto maior do que a dos homens (0,259), uma diferença relativa de +17% sobre a média masculina. A leitura mais informativa, porém, não está na média, mas em como a população se distribui entre os níveis de exposição: 14,5% das mulheres ocupadas (6,1 milhões) estão em alta exposição (G3 e G4), contra 6,8% dos homens (3,6 milhões). Proporcionalmente, as mulheres são 2,2 vezes mais presentes na alta exposição do que os homens. A diferença por sexo é compatível com o padrão internacional documentado por [Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[ (2025, p. 43, Figura 20)](https://doi.org/10.54394/HETP0387): nos países de alta renda, 24,0% do emprego feminino e 11,6% do masculino situam-se nos Gradientes 3 e 4.
### **3.5.2 Análise por raça**
A Figura 3.6 apresenta o recorte racial.
**Figura 3.6: Exposição à IA por raça**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/ef4545d0-02af-4968-9a16-52ee00fffd7c/63487b0c-af82-47cd-a41b-47c4a7a09f4b.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173158Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=ab8a59a721bc0dbb7b8ccf5faf3ae06c18bb46d53905e245d864478855dc23c6&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
O padrão racial é semelhante em magnitude, mas oposto à direção que se costuma esperar em análises de desigualdade: trabalhadores brancos têm exposição média de 0,305, contra 0,257 entre trabalhadores negros, definidos pela agregação de pretos e pardos conforme [Osorio (2003)](https://repositorio.ipea.gov.br/bitstreams/e09cc868-669f-4064-b396-693e22e0ce07/download), uma diferença relativa de +19% sobre a média negra. Em alta exposição, 12,5% dos brancos (5,2 milhões) estão expostos, contra 8,4% dos negros (4,5 milhões): os brancos são 1,5 vez mais presentes na alta exposição, mesmo sendo um contingente 11,9 milhões menor na força de trabalho ocupada (41,5 ante 53,4 milhões). A interpretação econômica se conecta diretamente ao que foi visto: as ocupações de alta exposição são, em sua maioria, *white collar* e, no Brasil, esse tipo de trabalho está historicamente associado a maior renda e escolaridade. O país carrega um legado de desigualdade racial, com uma estrutura de mercado de trabalho forjada em séculos de escravidão, que concentrou e ainda concentra grande parte da população negra em ocupações elementares, da construção, dos serviços domésticos e da indústria de transformação, setores de alto volume, baixa remuneração e baixa exposição à IA. 
### **3.5.3 Análise por faixa etária**
A Figura 3.7 descreve a exposição ao longo da idade.
**Figura 3.7: Exposição à IA por faixa etária**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/18134332-88f2-4a27-a749-36cc9eb9f465/305f57f1-ea80-4489-b48f-1458e3b2b0e6.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173158Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=4c3f602969954d0ba056a5e5f48839bce1470cfb0b8340af1d529a9169927437&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A exposição decresce de forma monotônica com a idade, partindo de 0,304 na faixa de 18 a 24 anos e caindo até 0,252 na faixa de 55 a 59 anos, uma diferença de 0,056 ponto, equivalente a +22% para os mais jovens em relação aos mais velhos. O contraste é ainda mais expressivo no segmento de alta exposição: a faixa de 18 a 24 anos tem 3,2 vezes mais trabalhadores em alta exposição (16,2%) do que a de 55+ (5,9%). Os jovens estão mais expostos por uma razão estrutural: ingressam preferencialmente em ocupações de apoio administrativo, vendas e serviços qualificados, justamente as mais expostas. Esse achado tem peso analítico relevante na segunda etapa desta dissertação, em que avalio se essa coorte mais exposta sofreu efeitos diferenciados após o lançamento do ChatGPT, padrão já documentado por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) nos Estados Unidos.
### **3.5.4 Análise por nível de escolaridade**
O gradiente educacional é o mais forte de todos os recortes individuais. A Figura 3.8 mostra esse padrão.
**Figura 3.8: Exposição à IA por nível de escolaridade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/bc60ec35-aa67-4e8f-ad52-3b662d104bac/7a88f2d4-6599-4c85-872e-1e9a7690de45.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=db6775fb9698f8ffe9cf766944b0c30b66492f68cf7678bf329f1659aed4f3b2&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A exposição média sobe de 0,179 entre trabalhadores sem instrução ou com fundamental incompleto para 0,275 entre os com médio completo (+54% em relação ao piso), 0,359 entre os com superior incompleto (+102%) e 0,364 entre os com superior completo (+105%), uma variação que mais que dobra a exposição ao longo da distribuição educacional. A interpretação é direta: a escolaridade abre acesso a ocupações de escritório, profissionais e técnicas, e essas são as mais expostas à IA.
### **3.5.5 Análise por renda**
A Figura 3.9 relaciona a exposição e a faixa de renda.
**Figura 3.9: Exposição à IA por faixa de renda**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/a18842f5-17d1-482b-9503-18ecfefc5819/acc6a675-2b6b-40d9-9c66-f87bd6614375.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=476aa8ba47df62d3a7b8c3140b28b7e4f8afbd1e2563a016bcf9a94c7835aba1&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
O padrão central é que, embora a exposição média à IA aumente com a renda (de 0,237 na faixa até 1 salário mínimo para 0,365 em 5 ou mais), a **alta exposição** (Gradientes 3 e 4) não cresce indefinidamente: ela sobe de 7,6% na faixa mais baixa para cerca de 12,3% nas faixas intermediárias (1 a 3 salários mínimos) e depois **satura**, ficando praticamente estável mesmo entre os mais ricos. Esse resultado pede cautela na interpretação. Há uma leitura intuitiva, mas equivocada, de que seria a elite intelectual e financeira o grupo mais exposto à IA, afinal é ela que lida com as tarefas mais sofisticadas, digitais e baseadas em conhecimento. Os dados mostram outra direção. No *ILO Global Index*, a maior parte das ocupações do Gradiente 4 pertence a funções administrativas, como digitadores, operadores de processamento de texto, escriturários de contabilidade e escriturários de escritório geral ([Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[, 2025, p. 40](https://doi.org/10.54394/HETP0387)). Acima desse patamar, a renda passa a refletir mais cargos de gestão e profissões liberais especializadas, que tendem a cair em exposição **moderada** (G1 e G2), não alta. O resultado é que a maior massa de trabalhadores em alta exposição está em salários de até 2 salários mínimos, cerca de dois terços do total, um segmento com menor capacidade de absorver choques. 
### **3.5.6 Análise por situação de formalidade**
A Figura 3.10 fecha os recortes com a situação de formalidade, que serve de ponte para a etapa empírica.
**Figura 3.10: Exposição à IA por situação de formalidade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/f202a434-d610-4db8-b019-d5610ce848e6/09bebfba-37e6-4804-a4b0-4d8d0595c2ed.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=94ba1b3c5b3de3668266a066945baea46fcde702a33c2b801778c98ceeacf11e&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<synced_block url="https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e#e90cc8ca4610828ca4550122ebb70126">
	A exposição média dos trabalhadores formais (0,305) é 0,046 ponto maior do que a dos informais (0,258), uma diferença relativa de +18% em relação à média informal. Novamente, o contraste é mais nítido na alta exposição: 14,8% dos formais (6,1 milhões) estão em ocupações de alta exposição (G3 e G4), contra apenas 6,7% dos informais (3,6 milhões). Em termos proporcionais, os trabalhadores com vínculo formal são 2,2 vezes mais presentes na alta exposição do que os informais. Apesar de a força de trabalho informal ser 32% maior do que a formal (54,6 ante 41,3 milhões de ocupados), os formais respondem por 63% dos 9,8 milhões em alta exposição (6,1 milhões) e os informais por apenas 37% (3,6 milhões).
</synced_block>
A interpretação é estrutural. Os trabalhadores formais, predominantemente empregados CLT em escritórios e na administração pública, se concentram justamente nas ocupações de alta exposição. 
## **3.6 Síntese e implicações para a análise com CAGED**
Esta análise descritiva permitiu três conjuntos de achados. Primeiro, a alta exposição à IA alcança cerca de 10,1% da força de trabalho ocupada (9,8 milhões de trabalhadores), patamar acima da média global estimada pela OIT, mas ainda distante das economias de alta renda. Segundo, essa exposição é ocupacional: se concentra em ocupações administrativas, de apoio, contábeis e de atendimento, e se distribui por praticamente todos os setores e estados, com destaque de intensidade para Finanças e Seguros e de volume para Serviços Profissionais e Administração Pública. Terceiro, porque decorre da posição na estrutura ocupacional, a exposição aparece de forma desigual entre os grupos sociais, sendo maior entre trabalhadores mais escolarizados, mulheres, brancos, jovens, formais e das faixas intermediárias de renda.
Esses achados motivam diretamente a próxima etapa. A PNAD oferece um retrato transversal: mede a exposição e caracteriza o perfil dos trabalhadores, mas não acompanha a dinâmica do emprego ao longo do tempo. Para investigar se a exposição à IA se traduz em mudanças efetivas no mercado de trabalho, é preciso uma base longitudinal do emprego formal. Isso é o que vamos fazer na próxima seção.
# 4 Estratégia empírica
## 4.1 Dados e construção do painel CAGED
No Brasil, o equivalente mais próximo dessa base é o CAGED (Cadastro Geral de Empregados e Desempregados), estatística administrativa do Ministério do Trabalho e Emprego construída a partir de informações do eSocial, do CAGED e do Empregador Web. Desde janeiro de 2020, a maior parte das empresas cumpre a obrigação de informar admissões e desligamentos pelo eSocial, e os registros são consolidados mensalmente. Essa obrigatoriedade dá ao CAGED cobertura praticamente completa do mercado formal em frequência mensal, o que o torna adequado para acompanhar a porta de entrada e de saída do emprego, justamente a margem em que a literatura internacional tem encontrado os primeiros sinais de ajuste à IA. A adaptação ao Brasil, porém, exige duas ressalvas em relação ao artigo de referência. Primeiro, o CAGED observa fluxos formais de admissões e desligamentos, e não o estoque mensal de trabalhadores por firma. Segundo, a variação de exposição vem do índice da OIT aplicado à CBO, e não de quintis construídos sobre a classificação ocupacional americana. Por isso, o que se faz aqui é uma análise da dinâmica do emprego formal brasileiro em ocupações mais expostas, e não uma reprodução direta do painel firma-trabalhador do artigo de referência. 
A escolha do CAGED, em vez da PNAD Contínua (usada na Seção 3), decorre do que se quer medir. Aqui estão três justificativas para essa escolha.
Primeiro, a **frequência**: o CAGED é mensal e a PNADc é trimestral, e um estudo de eventos centrado em novembro de 2022 precisa de resolução mensal para separar o antes do depois, ao passo que, com dados trimestrais, o trimestre do evento é simultaneamente pré e pós. Segundo, a **natureza do registro**: o CAGED é registro administrativo de declaração obrigatória, com cobertura praticamente completa do mercado formal, enquanto a PNADc é amostra domiciliar complexa, cuja precisão não se sustenta em recortes por ocupação de quatro dígitos, em que muitas células teriam poucas observações por trimestre. Terceiro, e mais importante, **o objeto observado**: a PNADc mede o estoque de ocupados e o CAGED mede o fluxo de admissões e desligamentos, e a hipótese testada aqui é sobre contratação. O estoque só se move depois que o fluxo se move.
Essa escolha também tem limitações. O CAGED cobre apenas o mercado formal e registra fluxos, não o estoque de trabalhadores. Para observar dimensões que a base não alcança, uso a RAIS para medir o estoque anual de vínculos formais e a PNAD Contínua para examinar a informalidade. Esses dois exercícios são complementares e descritivos, sem identificação causal, e aparecem no Apêndice D. 
Enquanto a PNAD Contínua utiliza a Classificação de Ocupações para Pesquisas Domiciliares (COD), o CAGED utiliza a Classificação Brasileira de Ocupações (CBO). Por isso, a unidade de análise desta etapa é a ocupação CBO de quatro dígitos observada mês a mês. A partir dos microdados do CAGED, construo para cada ocupação e mês medidas de admissões, desligamentos, saldo líquido e salários médios de admissão e desligamento.
O painel é construído a partir de uma única safra oficial do Novo CAGED, e a série de cada mês obedece à identidade `MOV + FOR − EXC`: as movimentações declaradas no prazo, mais as declarações fora do prazo, menos as exclusões. Todas as movimentações são reatribuídas ao **mês de competência do fato**, e não ao mês em que foram declaradas. O procedimento importa porque a incidência de declaração fora do prazo não é constante no tempo: usar apenas o arquivo de movimentações omitiria 8,6% dos registros de 2021 contra 1,3% dos de 2024, uma perda que cresce para trás e que se confundiria com tendência prévia. A série mensal assim reconstruída reproduz exatamente a série ajustada divulgada pelo Programa de Disseminação das Estatísticas do Trabalho (PDET) nos 65 meses, em admissões, desligamentos e saldo.
Três regras de tratamento completam a construção. Primeira, registros com salário fora do intervalo aberto entre zero e R\$ 1 milhão, idade fora da faixa de 14 a 90 anos, CBO inválida ou código de movimentação impossível são rejeitados antes da agregação. Ao todo, 3.574.530 de 252.838.929 linhas, ou 1,4%. Segunda, salário e composição são tratados como **ausentes**, e não como zero, quando o fluxo correspondente é nulo: há 403 células sem nenhuma admissão e 355 sem nenhum desligamento, e preenchê-las com zero faria a winsorização produzir salários plausíveis onde não houve contratação alguma. Terceira, a winsorização é aplicada no nível do registro, nos percentis 1 e 99, dentro de cada célula de CBO de quatro dígitos por ano, igualmente ao salário de admissão e ao de desligamento.
**Tabela 4.1.1 — Escopo do painel ocupação-mês**
<table header-row="true">
<tr>
<td>Indicador</td>
<td>Valor</td>
</tr>
<tr>
<td>Células CBO-mês no painel observado</td>
<td>39.742</td>
</tr>
<tr>
<td>Células CBO-mês na amostra principal</td>
<td>22.049</td>
</tr>
<tr>
<td>CBOs na amostra principal</td>
<td>341</td>
</tr>
<tr>
<td>CBOs tratadas / controle</td>
<td>75 / 266</td>
</tr>
<tr>
<td>Meses</td>
<td>65</td>
</tr>
<tr>
<td>Janela</td>
<td>2021-01 a 2026-05</td>
</tr>
</table>
> *Notas: o painel observado reúne todas as 630 famílias de CBO de quatro dígitos presentes na safra; a amostra principal retém apenas as 341 que entram no contraste entre expostas e não expostas. Os dois números são distintos e nomeados separadamente de propósito.*
A janela de análise começa em janeiro de 2021 por duas razões. Primeiro, o Novo CAGED teve início em janeiro de 2020, não havendo dados diretamente comparáveis para períodos anteriores. Segundo, optei por excluir o ano de 2020 porque ele coincide com a fase mais aguda da pandemia de Covid-19, marcada por fortes alterações nas admissões, nos desligamentos e nos salários. A inclusão desse período poderia fazer com que os efeitos excepcionais da pandemia fossem confundidos com as tendências anteriores à difusão do ChatGPT. Assim, o painel compreende o período entre janeiro de 2021 e maio de 2026, preservando 23 meses anteriores ao evento e 42 posteriores. A janela é assimétrica, com mais tempo depois do evento do que antes. [Klein Teeselink (2025, p. 11)](https://doi.org/10.2139/ssrn.5516798), por exemplo, adota uma janela de 15 meses de pré-tratamento e 30 meses de pós-tratamento.
## 4.2 Correspondência CBO–OIT e definição dos grupos
O principal desafio metodológico é fazer a correspondência do CBO, usada nos registros administrativos brasileiros, com o índice da OIT, construído em ISCO-08. Para evitar uma correspondência ad hoc entre códigos numericamente parecidos, adotei uma ponte institucional em duas etapas. Primeiro, usei a tábua oficial do Ministério do Trabalho e Emprego que relaciona CBO 2002, CBO 94 e CIUO/ISCO-88. Em seguida, converti os códigos ISCO-88 para ISCO-08 por meio da tabela de correspondência da OIT. O caminho completo é, portanto: CBO 2002 → CBO94/CIUO88 via MTE → ISCO-08 via OIT → índice de exposição da OIT. A correspondência é mantida apenas quando existe uma ponte institucional identificável entre a família ocupacional brasileira e a classificação internacional. 
Das 629 CBOs avaliadas no crosswalk, 193 não tiveram uma correspondência oficial válida com a ISCO-08. Elas recebem o rótulo “sem pontuação disponível” (*No score*) e ficam fora da amostra principal. Isso não significa que tenham baixa ou nenhuma exposição, mas apenas que não foi possível atribuir uma pontuação confiável. A perda também não é uniforme, e não é unilateral: dirigentes e gerentes representam 19,2% das CBOs sem correspondência contra 2,8% das classificadas, uma sobre-representação de sete vezes, mas as ocupações elementares também são perdidas em excesso, com 9,3% contra 3,7%, enquanto trabalhadores da produção e operadores de instalações são retidos em excesso. Como a perda atinge tanto o topo quanto a base da estrutura ocupacional, de onde viriam respectivamente ocupações expostas e ocupações de controle, a direção do viés que ela introduz no contraste é indeterminada, e não sistematicamente adversa. 
Para as 436 CBOs com correspondência, uma mesma ocupação brasileira pode apontar para mais de um código ISCO-08. Nesses casos, agrego as pontuações disponíveis e aplico a regra da OIT, que considera tanto o nível médio quanto a dispersão da exposição. As famílias tratadas apontam, em média, para 2,89 destinos ISCO cada, contra 1,65 no grupo de controle. A Tabela 4.2.1 apresenta os grupos resultantes.
**REVISAR COM MANÉ — R01: compressão das pontuações e direção do erro de mensuração**
A agregação pode comprimir as pontuações mais altas e reduzir a separação entre grupos. Isso não demonstra, porém, que o coeficiente da regressão seja um limite inferior em magnitude. Essa leitura exigiria hipóteses adicionais sobre o erro de mensuração, sua relação com os desfechos e a seleção das ocupações que recebem pontuação. Como o crosswalk perde ocupações tanto no topo quanto na base da estrutura ocupacional e pode mudar a classificação binária, a direção do viés no contraste estimado permanece indeterminada.
**Tabela 4.2.1 — Classificação das CBOs segundo o índice da OIT e definição de grupos de tratamento e controle.**
<table header-row="true">
<tr>
<td>Categoria OIT</td>
<td>CBOs</td>
<td>Match MTE</td>
<td>Tratamento</td>
<td>Controle</td>
<td>Excluído</td>
<td>Pontuação média</td>
<td>SD pooled</td>
</tr>
<tr>
<td>Exposed: Gradient 4</td>
<td>0</td>
<td>0</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Exposed: Gradient 3</td>
<td>31</td>
<td>31</td>
<td>✓</td>
<td></td>
<td></td>
<td>0,539</td>
<td>0,114</td>
</tr>
<tr>
<td>Exposed: Gradient 2</td>
<td>31</td>
<td>31</td>
<td>✓</td>
<td></td>
<td></td>
<td>0,452</td>
<td>0,121</td>
</tr>
<tr>
<td>Exposed: Gradient 1</td>
<td>13</td>
<td>13</td>
<td>✓</td>
<td></td>
<td></td>
<td>0,356</td>
<td>0,167</td>
</tr>
<tr>
<td>Minimal Exposure</td>
<td>95</td>
<td>95</td>
<td></td>
<td></td>
<td>✓</td>
<td>0,329</td>
<td>0,123</td>
</tr>
<tr>
<td>Not Exposed</td>
<td>266</td>
<td>266</td>
<td></td>
<td>✓</td>
<td></td>
<td>0,202</td>
<td>0,080</td>
</tr>
<tr>
<td>Sem pontuação disponível</td>
<td>193</td>
<td>0</td>
<td></td>
<td></td>
<td>✓</td>
<td></td>
<td></td>
</tr>
</table>
A classificação combina a pontuação média com a dispersão entre os códigos ISCO associados. Por isso, ela não cresce mecanicamente com a média: duas ocupações com pontuações parecidas podem ficar em grupos diferentes. Na maior parte da amostra, a separação é clara, pois 72 das 75 ocupações tratadas têm pontuação acima do máximo observado no grupo de controle. Ainda assim, existe uma pequena faixa de sobreposição, que deve ser considerada na interpretação dos resultados.
Nenhuma CBO de quatro dígitos ficou no Gradiente 4. Isso ocorre porque uma CBO pode reunir vários códigos ISCO-08 e a agregação reduz os valores mais extremos. A maior pontuação entre as 436 CBOs classificadas foi 0,5933, pouco abaixo do limite de 0,60 exigido para o Gradiente 4. A regra de tratamento reúne os Gradientes 1 a 4; na amostra efetiva, somente os Gradientes 1 a 3 estão presentes. O grupo vazio é consequência da regra de agregação, e não do mercado de trabalho brasileiro. Quando a pontuação de uma família é a média das pontuações de seus destinos ISCO, ela não pode exceder o máximo desses destinos, e o máximo observado é 0,5933. A demonstração está nas variantes pré-registradas: a variante que agrega pelo modo ponderado do rótulo nativo da OIT, em vez de pela média das pontuações, recupera três famílias no Gradiente 4. Não há, portanto, evidência de ausência de ocupações altamente expostas no Brasil; há uma regra de agregação que as dilui.
A definição binária reduz parte da sensibilidade a mudanças entre gradientes, embora não elimine o erro de mensuração. Reuni os Gradientes 1, 2, 3 e 4 em um único grupo de ocupações expostas. Assim, uma ocupação que muda entre esses quatro gradientes continua classificada como exposta; a regra não evita mudanças que atravessem a fronteira entre exposição, exposição mínima e não exposição. A contrapartida é que o crosswalk perde precisão dentro de cada gradiente: ele não sustenta, com segurança, análises que tratem os gradientes de forma isolada, comparando, por exemplo, o Gradiente 3 diretamente com o Gradiente 1. Por isso, a exposição é usada principalmente de forma binária, entre expostos e não expostos, e as análises por gradiente específico ficam em segundo plano.
Definido o grupo tratado, resta delimitar o controle. O modelo principal compara esse grupo tratado com as ocupações Not Exposed, que formam o controle estrito. O grupo Minimal Exposure fica fora do controle principal porque representa uma categoria intermediária: são ocupações com exposição média baixa, mas com alguma dispersão de tarefas potencialmente expostas. Incluí-las no controle poderia enfraquecer o contraste entre ocupações efetivamente não expostas e ocupações expostas. Por isso, Minimal Exposure entra apenas como especificação de robustez com controle ampliado.
Os dois universos têm denominadores distintos. O crosswalk contém 629 famílias, das quais 193 não recebem pontuação. O painel observado contém essas famílias e a CBO 2414, ausente da tabela de correspondência e presente em cinco células entre julho de 2025 e maio de 2026. Ela permanece sem pontuação e fora da amostra principal. O painel contém, portanto, 630 famílias de CBO de quatro dígitos, das quais 194 não recebem pontuação. Destas, 436 receberam uma correspondência oficial e uma pontuação de exposição, o que representa 69,2% das famílias e 70,7% das células de ocupação por mês. Embora a cobertura do número de ocupações seja parcial, essas CBOs concentram 92,3% dos fluxos de admissões e desligamentos observados. A Tabela 4.2.2 resume a distribuição por grupo de exposição.
**Tabela 4.2.2: Cobertura do painel por grupo de exposição**
<table header-row="true">
<tr>
<td>Categoria</td>
<td>CBOs</td>
<td>% do total</td>
<td>Células CBO-mês</td>
<td>% das células</td>
<td>% dos fluxos</td>
</tr>
<tr>
<td>Exposed</td>
<td>75</td>
<td>11,9%</td>
<td>4.875</td>
<td>12,3%</td>
<td>21,7%</td>
</tr>
<tr>
<td>Not Exposed</td>
<td>266</td>
<td>42,2%</td>
<td>17.174</td>
<td>43,2%</td>
<td>41,2%</td>
</tr>
<tr>
<td>Minimal Exposure</td>
<td>95</td>
<td>15,1%</td>
<td>6.033</td>
<td>15,2%</td>
<td>29,5%</td>
</tr>
<tr>
<td>Sem pontuação disponível</td>
<td>194</td>
<td>30,8%</td>
<td>11.660</td>
<td>29,3%</td>
<td>7,7%</td>
</tr>
</table>
> *Notas: as células são contadas sobre os 65 meses do painel observado. A amostra principal é a soma das linhas *Exposed* e *Not Exposed*, ou seja, 4.875 mais 17.174, igual a 22.049 células. A coluna de fluxos usa a soma de admissões e desligamentos. Fonte: **`data/derived/painel_nacional.parquet`**.*
## 4.3 Desenho de identificação por diferenças em diferenças
O desenho não capta a adoção direta de IA dentro das firmas, pois o CAGED não informa se uma empresa usa ChatGPT ou ferramentas semelhantes. O que se estima é se ocupações mais expostas passaram a apresentar evolução diferencial após a difusão da tecnologia. O choque temporal vem da difusão pública da IA, e a intensidade do tratamento vem da exposição ocupacional medida pela OIT. O evento escolhido nesta dissertação é o lançamento público do ChatGPT, em 30 de novembro de 2022, tratado como marco inicial da difusão dos LLMs (*Large Language Models*). Essa escolha dialoga com a literatura recente, mas não reproduz exatamente a datação de todos os estudos. [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) observam que a OpenAI introduziu o ChatGPT em novembro de 2022 e estimam um estudo de evento cujo período de referência é outubro de 2022. [Humlum e Vestergaard (2026, p. 12, nota 8)](https://doi.org/10.3386/w33777) identificam cinco estudos de evento centrados em novembro de 2022.
O lançamento ocorreu no fim de novembro; na codificação do painel, janeiro de 2021 a novembro de 2022 é o pré-período e dezembro de 2022 a maio de 2026 é o pós-período. Todas as ocupações expostas recebem a mesma data de início. O contraste compara a mudança das ocupações expostas com a mudança das não expostas, mantendo os grupos definidos antes da estimação.
**REVISAR COM MANÉ — R02: hipótese de identificação e alcance dos efeitos fixos**
A hipótese contrafactual é que, sem a difusão da IA generativa, os dois grupos teriam seguido trajetórias paralelas nos desfechos. Os efeitos fixos de ocupação retiram diferenças permanentes entre CBOs; os de mês retiram choques comuns a todas elas. Eles não retiram automaticamente choques que atingem de modo diferente o trabalho administrativo e o trabalho manual, nem tendências próprias de cada grupo. Os coeficientes descrevem diferenciais pós-evento associados à exposição potencial. Para atribuí-los à tecnologia seriam necessárias, além dessa comparação, condições de identificação que os diagnósticos não sustentam.
A literatura recente alerta que estimadores convencionais de diferenças em diferenças podem produzir comparações problemáticas quando a adoção é escalonada no tempo e os efeitos são heterogêneos ([Callaway; Sant'Anna, 2021](https://doi.org/10.1016/j.jeconom.2020.12.001); [de Chaisemartin; D'Haultfœuille, 2020](https://doi.org/10.1257/aer.20181169); [Sun; Abraham, 2021](https://doi.org/10.1016/j.jeconom.2020.09.006)). Esse problema específico não caracteriza o desenho usado aqui: todas as ocupações expostas passam a ser consideradas tratadas na mesma data, o lançamento do ChatGPT, e as ocupações não expostas permanecem como controle. Portanto, não há comparação entre grupos tratados mais cedo e mais tarde. A principal condição do desenho continua sendo outra: antes do evento, os grupos deveriam apresentar trajetórias paralelas. Os diagnósticos da Seção 5 mostram que essa condição não se sustenta, o que limita a interpretação causal.
## 4.4 Especificações econométricas e desfechos
### 4.4.1 Especificação principal
A especificação foi construída em etapas. Parti do desenho usado por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/), adaptei a comparação às características do CAGED e confrontei as escolhas de estimador, controles e inferência com a literatura metodológica. O objetivo foi escolher um modelo coerente com a pergunta e com os limites da base, e não procurar a especificação que produzisse o resultado mais favorável. As equações abaixo registram a versão adotada e permitem que essas decisões sejam avaliadas.
Como os resultados têm formatos diferentes, a mesma comparação é estimada de duas formas. Admissões, desligamentos e fluxo bruto são contagens e podem ser zero; por isso, uso PPML. A primeira equação apresenta esse caso:
$$
E\left[Y_{c,t} \mid \cdot\right] = \exp\left(\beta\,(\text{Exposta}_c \times \text{Pós}_t) + \alpha_c + \delta_t\right)
$$
Para o salário real de admissão e o saldo líquido, uso a forma linear da mesma comparação:
$$
Y_{c,t} = \beta\,(\text{Exposta}_c \times \text{Pós}_t) + \alpha_c + \delta_t + \varepsilon_{c,t}
$$
A leitura dos termos é a seguinte:
- $`Y_{c,t}`$ é o resultado observado para a ocupação CBO de quatro dígitos $`c`$ no mês $`t`$.
- $`\text{Exposta}_c \times \text{Pós}_t`$ marca as ocupações expostas depois do evento. Na amostra efetiva, o grupo exposto reúne os Gradientes 1 a 3 e o controle reúne as ocupações classificadas como não expostas.
- $`\beta`$ mede o diferencial pós-evento entre esses dois grupos. No PPML, a variação percentual correspondente é calculada por $`100 \times (e^{\beta} - 1)`$. No modelo linear em logaritmo, o coeficiente tem leitura percentual aproximada.
- $`\alpha_c`$ são os efeitos fixos de ocupação. Eles retiram diferenças que permanecem estáveis em cada CBO, como seu nível médio de salário ou contratação.
- $`\delta_t`$ são os efeitos fixos de mês. Eles retiram fatores comuns às ocupações em cada período, como sazonalidade, inflação e ciclo econômico.
- $`\varepsilon_{c,t}`$ reúne as variações não explicadas pelo modelo. Os erros-padrão são agrupados nas 341 CBOs, permitindo que observações da mesma ocupação estejam relacionadas ao longo do tempo.
Esses controles tornam a comparação mais adequada, mas não garantem causalidade. Para interpretar $`\beta`$ como efeito, seria necessária a hipótese contrafactual de tendências paralelas na ausência do evento, apoiada por trajetórias prévias compatíveis. Os diagnósticos apresentados na Seção 5 mostram que essa condição falha.
### 4.4.2 Estudo de eventos
Além do modelo estático, estimo estudos de eventos que substituem a interação única $`\text{Exposta} \times \text{Pós}`$ por interações entre o tratamento e cada mês relativo ao evento:
$$
E\left[Y_{c,t} \mid \cdot\right] = \exp\left(\sum_{k=-23,\, k \neq -1}^{+23} \beta_k \, \mathbf{1}[t - t^{*} = k] \times \text{Exposta}_c + \alpha_c + \delta_t\right)
$$
No estudo de eventos, $`t^{*}`$ corresponde a dezembro de 2022 e $`k = -1`$ corresponde a novembro de 2022, o mês de referência. Cada coeficiente representa um mês, sem agrupar os extremos da série. Os meses anteriores mostram se os grupos já seguiam caminhos diferentes antes do evento; os meses posteriores descrevem como essa diferença evoluiu. Essa trajetória ajuda no diagnóstico, mas não prova causalidade por si só.
A janela balanceada do estudo de eventos vai de janeiro de 2021 a novembro de 2024 (−23 a +23), com novembro de 2022 omitido. Ela é distinta da janela completa do modelo estático, que chega a maio de 2026 (+41). A equação acima se aplica ao PPML; para salário em log e saldo em asinh, uso a mesma soma de interações na forma linear. Os coeficientes anteriores ao evento são diagnósticos da comparação, os posteriores descrevem sua dinâmica e a média de k = 0 a +23 é o estimando usado no exercício de sensibilidade. Essa média normalizada não é o coeficiente pós da regressão estática.
### 4.4.3 Desfechos e transformações
O PPML é usado nas admissões e nos desligamentos porque essas contagens incluem zeros. Transformações do tipo $`\log(1+y)`$ alteram o estimando e podem ser arbitrariamente sensíveis à unidade de medida quando há efeito na margem extensiva ([Chen; Roth, 2024](https://doi.org/10.1093/qje/qjad054)). Separadamente, modelos log-lineares podem ser inconsistentes sob heterocedasticidade, o que motiva o uso de PPML ([Santos Silva; Tenreyro, 2006](https://doi.org/10.1162/rest.88.4.641)). O PPML trabalha diretamente com a contagem em nível e também é usado por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/). A estimação linear com $`\log(1+y)`$ permanece apenas como resultado secundário.
A análise acompanha cinco desfechos: admissões, desligamentos, fluxo bruto, salário real de admissão e saldo líquido. A tabela nacional destaca quatro deles; o fluxo bruto, soma das entradas e saídas, permanece nas tabelas setoriais, nas heterogeneidades completas e no apêndice. A Tabela 4.4.1 apresenta a definição e a transformação usada em cada caso.
**Tabela 4.4.1: Desfechos da análise**
<table header-row="true">
<tr>
<td>**Grupo**</td>
<td>**Desfecho**</td>
<td>**Definição**</td>
<td>**Transformação**</td>
</tr>
<tr>
<td>Fluxos</td>
<td>Admissões (PPML, nível)</td>
<td>Número de admissões formais na ocupação-mês</td>
<td>PPML sobre a contagem em nível; semi-elasticidade</td>
</tr>
<tr>
<td>Fluxos</td>
<td>Desligamentos (PPML, nível)</td>
<td>Número de desligamentos formais na ocupação-mês</td>
<td>PPML sobre a contagem em nível; semi-elasticidade</td>
</tr>
<tr>
<td>Fluxos</td>
<td>Fluxo bruto (PPML, nível)</td>
<td>Admissões mais desligamentos na ocupação-mês</td>
<td>PPML sobre a contagem em nível; semi-elasticidade</td>
</tr>
<tr>
<td>Salários</td>
<td>Salário real de admissão (log)</td>
<td>Salário médio de admissão deflacionado pelo IPCA</td>
<td>$`\log`$; MQO. Diferença aproximada em proporção</td>
</tr>
<tr>
<td>Saldo</td>
<td>Saldo líquido (asinh)</td>
<td>Admissões menos desligamentos na ocupação-mês</td>
<td>$`\text{asinh}`$; MQO. Não interpretar como percentual</td>
</tr>
</table>
As transformações acompanham o formato de cada resultado. Admissões e desligamentos são contagens com zeros e entram no PPML em nível. O salário de admissão é corrigido pelo IPCA e entra em logaritmo. O saldo líquido pode ser positivo, negativo ou zero; por isso, uso $`\text{asinh}`$, que preserva o sinal, mas não permite uma leitura percentual direta do coeficiente.
### 4.4.4 Inferência e especificações adicionais
Idade média, participação feminina, escolaridade e composição racial dos admitidos não entram no modelo principal. Essas características podem mudar depois do evento e fazer parte do próprio resultado que se pretende observar. Controlá-las nesse momento poderia retirar parte dessa mudança. Por isso, elas aparecem separadamente na descrição da composição e em especificações separadas: uma interage características prévias com o pós e outra inclui composição contemporânea, sem substituir o modelo principal.
A inferência usa erros-padrão agrupados por CBO de quatro dígitos e distribuição t com graus de liberdade iguais ao menor número de clusters menos um. No modelo nacional, são 341 clusters e 340 graus de liberdade. Estrelas indicam o p-valor declarado em cada tabela e não validam a interpretação causal. Nas heterogeneidades, elas usam os p-valores BH das famílias originais.
A especificação setorial é co-principal. No painel por ocupação, setor e mês, ela absorve efeitos fixos de CBO × seção da CNAE e de seção da CNAE × mês. A comparação passa a ocorrer entre ocupações do mesmo setor e mês, com agrupamento dos erros por CBO. Esse desenho controla choques mensais comuns ao setor, mas não garante trajetórias paralelas entre as ocupações que nele trabalham. A comparação com o nível nacional está na Tabela 5.2.1; a inferência alternativa com agrupamento em duas dimensões permanece como diagnóstico na Seção 4.6 e no pacote.
## 4.5 Heterogeneidades
A análise de heterogeneidade emprega uma diferença tripla, em que o painel passa a ser indexado também por subgrupo sociodemográfico $`g`$:
$$
Y_{c,g,t} = \beta_{\text{DDD}}\,(\text{Pós}_t \times \text{Exposta}_c \times \text{Grupo}_g) + \gamma_1 (\text{Pós} \times \text{Exposta}) + \gamma_2 (\text{Pós} \times \text{Grupo}) + \gamma_3 (\text{Exposta} \times \text{Grupo}) + \alpha_c + \delta_t + \theta_g + \varepsilon_{c,g,t}
$$
É importante separar os dois estimadores usados na Seção 5. O **DiD dentro do grupo** pergunta, por exemplo, se entre as mulheres as ocupações expostas mudaram de forma diferente das não expostas. O **DDD** pergunta se esse diferencial entre as mulheres é diferente do diferencial entre os homens. As tabelas da Seção 5.3 priorizam o DDD; o Apêndice A reúne os DDDs completos, os DiDs dentro dos grupos e suas figuras de apoio. Portanto, apenas o DDD testa uma diferença entre subgrupos. Como os diagnósticos de tendências prévias falham, os dois resultados permanecem exploratórios.
Na equação linear, o parâmetro de interesse é a interação tripla e os termos de ordem inferior identificados são mantidos. Para os desfechos de contagem, o mesmo preditor entra na média condicional exponencial do PPML. Os termos invariantes que são absorvidos pelos efeitos fixos não são identificados separadamente. O DDD é estimado em seu próprio modelo; não é obtido subtraindo mecanicamente DiDs estimados em amostras separadas. Cada perfil é comparado com seu complemento na partição informada. Em sexo, as duas orientações expressam o mesmo contraste com sinais opostos; nas demais partições, os complementos podem mudar.
A literatura internacional sugere que os efeitos da IA generativa podem aparecer primeiro em trabalhadores no início da carreira. [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) mostram que, nos Estados Unidos, a queda relativa de emprego em ocupações expostas é mais intensa entre trabalhadores de 22 a 25 anos. A interpretação é que trabalhadores jovens dependem mais de conhecimento codificado, adquirido na educação formal, enquanto trabalhadores mais experientes acumulam conhecimento tácito e específico da firma. Se a IA substitui parte desse conhecimento codificado, os jovens podem ser mais vulneráveis. Agrupei idade conforme aplicado na PNAD, para ajudar na interpretação e comparação dos resultados da seção 3, mas também adotei as faixas etárias inspiradas no artigo de referência: 22-25, 26-30, 31-34, 35-40, 41-49 e 50 anos ou mais. Para dialogar com essa hipótese, essas faixas ajudam a separar o início da carreira de estágios mais avançados da trajetória profissional.
A Seção 3 mostra que a exposição varia entre perfis sociodemográficos. Por isso, examino idade, sexo, raça/cor, escolaridade e renda. Para testar se o diferencial entre ocupações expostas e não expostas muda entre esses perfis, uso uma diferença tripla (DDD), formada pela interação entre período posterior, grupo ocupacional e perfil analisado. Em termos simples, o DDD verifica se o diferencial pós-evento de um perfil é diferente do observado em seu grupo de comparação.
Esses exercícios envolvem um número grande de contrastes, e a 5% nominais alguns resultados significativos são esperados por acaso. Por isso adoto o procedimento de [Benjamini e Hochberg (1995)](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x), que controla a taxa de falsas descobertas, aplicado sobre famílias declaradas **antes** da estimação:
<table header-row="true">
<tr>
<td>Família</td>
<td>Conteúdo</td>
<td>Testes</td>
</tr>
<tr>
<td>A</td>
<td>DDD sobre as 20 partições originais, em 5 desfechos</td>
<td>100</td>
</tr>
<tr>
<td>B</td>
<td>DDD sobre as partições alternativas: faixas etárias da PNAD e agregado Negra</td>
<td>30</td>
</tr>
<tr>
<td>C</td>
<td>DiD dentro do grupo, nas 26 partições, em 5 desfechos</td>
<td>130</td>
</tr>
</table>
As famílias A e B foram declaradas separadamente para distinguir partições principais e alternativas. Por exemplo, as faixas de 18 a 24 e de 22 a 25 anos examinam populações que se sobrepõem. A revisão preserva esse desenho de multiplicidade e seus p-valores, sem refazer o ajuste ao selecionar linhas para as tabelas do corpo. A família C é separada por outro motivo: ela reúne os DiD estimados dentro de cada grupo, enquanto A e B reúnem contrastes DDD. O ajuste de Benjamini-Hochberg reduz os resultados que cruzam o limiar de 5% de 34 para 21 na família A, de 6 para 4 na B e de 54 para 40 na C.
Também defini seis estudos de caso ocupacionais: desenvolvedores de software, atendimento ao cliente, gerentes de marketing e vendas, supervisores de produção, estoquistas e repositores e auxiliares de saúde e cuidado. Os dois primeiros permitem uma comparação direta com o estudo de referência; os demais ampliam a análise para ocupações com perfis distintos. Esses casos são descritivos e não identificam mecanismos causais. Eles foram definidos antes da inspeção dos resultados, a partir das descrições oficiais das CBOs de seis dígitos, e reúnem 76 códigos sem sobreposição. A composição segundo a OIT é usada apenas na interpretação posterior.
Os DiDs dentro dos grupos e seus estudos de eventos usam a janela balanceada −23 a +23. Os DDDs estáticos usam a amostra própria registrada de cada modelo, e os diagnósticos DDD usam estudos de eventos com efeitos fixos mais saturados: CBO × subgrupo, mês × subgrupo e mês × tratamento. Por isso, os tamanhos amostrais e os diagnósticos de um DiD não devem ser atribuídos ao DDD correspondente.
## 4.6 Diagnósticos, placebos e robustez
Os testes a seguir foram definidos antes da estimação para mostrar quanto os resultados dependem das escolhas do desenho. Eles não validam automaticamente as estimativas: revelam sua sensibilidade e suas limitações. Esta subseção apresenta cada exercício; os resultados aparecem na Seção 5 e, de forma completa, no pacote de replicação.
1. **Escada de especificações.** Sete degraus pré-registrados: sem controles, composição pré-tratamento interagida com o pós, composição contemporânea, *Minimal Exposure* incorporada ao controle, exposição contínua padronizada, amostra restrita ao período a partir de 2022 e amostra truncada em dezembro de 2025.
2. **Placebo temporal.** Um evento falso é datado em dezembro de 2021 e estimado apenas dentro do pré-período verdadeiro, descartando-se todo o período posterior ao ChatGPT. O procedimento, ainda que com data distinta, pois aquele estudo situa seu evento falso em 30 de maio de 2022, é o mesmo de [Teutloff ](https://doi.org/10.1016/j.jebo.2024.106845)[*et al.*](https://doi.org/10.1016/j.jebo.2024.106845)[ (2025, p. 12)](https://doi.org/10.1016/j.jebo.2024.106845).
3. **Placebo de grupo.** Quinhentas reatribuições aleatórias do rótulo de tratamento, preservando o desenho de 75 ocupações tratadas entre 341, para situar o coeficiente observado na distribuição do que se obteria por acaso.
4. **Variantes de tratamento.** Quatro regras definidas previamente alteram a forma de combinar a pontuação média de exposição e sua dispersão entre os destinos ISCO.
5. **Medidas alternativas de exposição.** A safra de 2023 do índice da OIT, um consenso construído com GPT-4o e Gemini, e o índice de exposição da Anthropic.
6. **Sensibilidade a tendências prévias.** O procedimento de [Rambachan e Roth (2023)](https://doi.org/10.1093/restud/rdad018) avalia quão diferentes as violações pós-tratamento das tendências paralelas podem ser das pré-tendências antes que uma conclusão causal deixe de ser sustentada. Assim, o diagnóstico não se resume a aprovar ou reprovar o teste de tendências paralelas.
7. **Nível setorial.** Efeitos fixos de seção da CNAE por mês, tratados como especificação co-principal e não como robustez subordinada, conforme a Seção 4.4.4 e a Tabela 5.2.1.
8. **Influência ocupacional.** Um jackknife que remove cada uma das 75 ocupações tratadas, uma de cada vez, para verificar se o resultado depende de poucas ocupações grandes.
Os diagnósticos de pré-tendências combinam teste conjunto dos coeficientes anteriores, inclinação linear GLS e inspeção dos coeficientes individuais. Suporte ocupacional, posto e positividade da matriz de covariância são verificados antes de interpretar os testes. Uma matriz com posto insuficiente não produz um teste conjunto válido: os coeficientes mensais permanecem publicados, mas o teste e a inclinação GLS ficam indefinidos. “Não rejeitada” e “alerta” também não equivalem a identificação causal assegurada.
A extensão espacial foi interrompida antes da estimação do contraste de tratamento porque a variação identificadora se concentrava em poucas Unidades da Federação. O Apêndice B.3 preserva o diagnóstico de suporte e os placebos; não há coeficientes espaciais a interpretar. Os exercícios de estoque formal e informalidade são apresentados no Apêndice D, com diagnósticos próprios no Apêndice B.
# 5 Resultados
## 5.1 Resultados médios nacionais
Começo pelo resultado médio nacional. A Tabela 5.1 traz as estimativas do modelo de diferenças em diferenças, comparando as ocupações expostas à IA (gradientes da OIT) com as não expostas depois do lançamento do ChatGPT. Os coeficientes medem a variação relativa das ocupações expostas.
**Tabela 5.1: Resultados médios nacionais**
<table header-row="true">
<tr>
<td>Resultado</td>
<td>Estimador</td>
<td>Coeficiente</td>
<td>EP</td>
<td>IC 95%</td>
<td>p</td>
<td>Pretrend</td>
<td>N</td>
</tr>
<tr>
<td>Admissões (nível)</td>
<td>PPML</td>
<td>−0,0538</td>
<td>0,0386</td>
<td>\[−0,1296; 0,0221\]</td>
<td>0,164</td>
<td>fail</td>
<td>22.049</td>
</tr>
<tr>
<td>Desligamentos (nível)</td>
<td>PPML</td>
<td>−0,0420</td>
<td>0,0347</td>
<td>\[−0,1103; 0,0262\]</td>
<td>0,227</td>
<td>fail</td>
<td>22.049</td>
</tr>
<tr>
<td>Salário real de admissão (log)</td>
<td>OLS</td>
<td>−0,0507</td>
<td>0,0103</td>
<td>\[−0,0711; −0,0304\]</td>
<td>\< 0,001</td>
<td>fail</td>
<td>22.012</td>
</tr>
<tr>
<td>Saldo líquido (asinh)</td>
<td>OLS</td>
<td>−0,5513</td>
<td>0,3783</td>
<td>\[−1,2954; 0,1929\]</td>
<td>0,146</td>
<td>fail</td>
<td>22.049</td>
</tr>
</table>
> *Notas: especificação principal **`01_no_controls`**, com efeitos fixos de CBO de quatro dígitos e de mês. Erros-padrão clusterizados por CBO de quatro dígitos, 341 clusters. Admissões e desligamentos são estimados por PPML em nível, e o coeficiente lê-se como semi-elasticidade: para coeficientes próximos de zero, multiplicá-lo por 100 aproxima a diferença percentual; a conversão exata é 100 × (e\^β − 1); salário e saldo são estimados por MQO sobre o logaritmo e sobre o arco-seno hiperbólico, respectivamente. Não há estrelas de significância: os quatro pretrends falham e a tabela não sustenta leitura causal. O tratamento compara as CBOs expostas segundo os gradientes da OIT às CBOs classificadas como **`Not Exposed`**. Fonte: **`results/models/specification_ladder.csv`**.*
Os quatro coeficientes têm sinal negativo: cerca de 5,4% nas admissões, 4,2% nos desligamentos e 5,1% no salário real de admissão, além de um saldo líquido negativo. O salário é a única estimativa cujo intervalo de 95% não inclui zero, entre −7,1% e −3,0%. Nos demais resultados, os intervalos são largos e incluem tanto diferenças negativas quanto valores próximos de zero. Essas magnitudes podem ser importantes na prática, mas eu não defini antecipadamente um valor a partir do qual as classificaria como relevantes. Por isso apresento o tamanho estimado e sua incerteza, sem rotulá-las como economicamente relevantes ou irrelevantes.
Nenhum dos quatro sustenta leitura causal, e aqui não há hierarquia: o teste de tendências paralelas é rejeitado em todos. Estendi o diagnóstico a cinco especificações alternativas (amostra a partir de 2022, agregação em nível setorial, exposição contínua, `Minimal Exposure` como grupo de controle e cobertura salarial completa), e nenhuma das 51 células examinadas passa no teste. Nenhum resultado deste bloco, portanto, tem identificação assegurada pelo diagnóstico padrão. O diagnóstico, porém, não precisa parar na rejeição. O procedimento de Rambachan e Roth (2023), anunciado na subseção 4.5, pergunta quanto a tendência prévia poderia divergir sem que a conclusão mudasse, e sua resposta aqui é dura: aplicado ao estimando do estudo de eventos, que é a média pós-tratamento normalizada a novembro de 2022, de −0,0154, o salário real de admissão não é robusto nem em M = 0, ou seja, o intervalo já contém zero antes de se admitir qualquer violação de tendências paralelas. Sob a restrição de curvatura, o ponto de quebra fica abaixo da curvatura pré-tratamento efetivamente observada. 
Esse resultado não contraria o que esta seção afirma: ele o confirma por outra via, e as duas leituras convergem na conclusão de que não há efeito causal estabelecido. Os resultados completos estão no Apêndice A. A queda simultânea de admissões e desligamentos é compatível com a hipótese de “acomodação silenciosa”: uma redução da rotatividade poderia diminuir entradas e saídas sem grande mudança no estoque de empregos. Os fluxos do CAGED não identificam esse mecanismo, porém, e o exercício complementar com a RAIS, apresentado na Apêndice D, não confirma a estabilidade do estoque. 
A falha das pré-tendências aparece junto com uma diferença clara entre os grupos antes do evento. O crescimento mensal do controle tinha desvio-padrão de 14,0%, contra 8,3% no grupo exposto, e amplitude sazonal de 44,7%, contra 27,3%. O controle reúne mais ocupações manuais e de serviços, enquanto o grupo exposto concentra ocupações administrativas e profissionais. Esses perfis já seguiam trajetórias distintas, como também mostram os gráficos dos casos que serão organizados no Apêndice C. 
Para entender esse resultado, eu decompus o diferencial salarial entre a parcela observada dentro das faixas de escolaridade e a parcela associada à mudança no perfil dos novos contratados. Nas ocupações expostas, a participação de admitidos com ensino superior caiu 2,7 pontos percentuais a mais do que nas não expostas. A decomposição por escolaridade indica que cerca de 23% do diferencial salarial agregado está associado a essa mudança de composição. Em uma especificação mais ampla, que também considera características anteriores das ocupações relacionadas à escolaridade, idade, sexo e raça, essa parcela chega a aproximadamente 29%. O padrão é compatível com a hipótese de uma redução relativa das oportunidades de entrada para trabalhadores com ensino superior nas ocupações expostas, mas não permite atribuir essa mudança à IA, sobretudo porque as pré-tendências falham. O diferencial do salário-hora, de 6,95%, também não sugere que uma redução da jornada explique a queda do salário mensal. Os cálculos e as tabelas completas são apresentados no Apêndice A.
A Figura 5.1 apresenta os coeficientes mensais dos event studies (painéis superiores, com intervalos de confiança de 95%) e as trajetórias normalizadas pela média pré-tratamento (painéis inferiores, descritivos).
**Figura 5.1: Resultados nacionais: event studies e trajetórias**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/bc7a2b7c-918b-48cc-b18d-814e554e23a6/figure_5_1_national_event_studies.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=931341067c07e13fb8109258b6765ef4ce101bc277b22f06507078c3e7294ae8&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
O padrão mais consistente está no salário real de admissão: no pós-tratamento os coeficientes são sistematicamente negativos e a estimativa média é precisa, ainda que o teste de tendências paralelas também seja rejeitado aqui. Vale notar que o event study normaliza cada mês contra novembro de 2022, enquanto a tabela compara o pós-tratamento à média de todo o pré-período; como os coeficientes pré do salário se situam em média em +0,037, a queda de 5,1% da tabela corresponde a uma distância maior do que sugere a leitura dos painéis contra o zero.
Declarei duas especificações co-principais no contrato congelado. O nível 1 compara ocupações expostas e não expostas em toda a economia. O nível 2 acrescenta efeitos fixos de seção da CNAE por mês, ou seja, compara ocupações dentro do mesmo setor e do mesmo mês. A diferença entre as duas diz bastante.
**Tabela 5.1.1: Controle setorial — especificações co-principais**
<table header-row="true">
<tr>
<td>Resultado</td>
<td>Nível 1 coef.</td>
<td>EP</td>
<td>p</td>
<td>Nível 2 coef.</td>
<td>EP</td>
<td>p</td>
<td>Diferença N2 − N1</td>
</tr>
<tr>
<td>Admissões (nível)</td>
<td>−0,0538</td>
<td>0,0386</td>
<td>0,164</td>
<td>−0,0751</td>
<td>0,0356</td>
<td>0,036</td>
<td>−0,0213</td>
</tr>
<tr>
<td>Desligamentos (nível)</td>
<td>−0,0420</td>
<td>0,0347</td>
<td>0,227</td>
<td>−0,0664</td>
<td>0,0348</td>
<td>0,057</td>
<td>−0,0244</td>
</tr>
<tr>
<td>Fluxo bruto (nível)</td>
<td>−0,0481</td>
<td>0,0353</td>
<td>0,174</td>
<td>−0,0707</td>
<td>0,0343</td>
<td>0,040</td>
<td>−0,0226</td>
</tr>
<tr>
<td>Salário real de admissão (log)</td>
<td>−0,0507</td>
<td>0,0103</td>
<td>\< 0,001</td>
<td>−0,0356</td>
<td>0,0064</td>
<td>\< 0,001</td>
<td>0,0151</td>
</tr>
<tr>
<td>Saldo líquido (asinh)</td>
<td>−0,5513</td>
<td>0,3783</td>
<td>0,146</td>
<td>−0,1395</td>
<td>0,0734</td>
<td>0,058</td>
<td>0,4118</td>
</tr>
</table>
> *Notas: fluxo bruto é a soma de admissões e desligamentos. Nível 1: 22.049 células, 22.012 no salário, 341 clusters. Nível 2: de 804.574 a 804.735 células, 682.889 no salário, 341 clusters. Erros-padrão clusterizados por CBO de quatro dígitos nas duas especificações. Os dez pretrends falham, com p \< 0,001 em todos, e por isso não há estrelas de significância. O nível 3 fica fora das colunas principais por ser diagnóstico de suporte. Fonte: **`results/tables/table_5_1_1_sector_control.md`**.*
Ao incluir efeitos fixos de setor por mês, os diferenciais estimados para os fluxos ficam mais negativos: as admissões passam de −0,0538 para −0,0751 e o fluxo bruto, de −0,0481 para −0,0707. No salário, o diferencial diminui de −0,0507 para −0,0356, o que sugere que parte da diferença agregada acompanha a composição entre setores. O saldo líquido também se aproxima de zero, de −0,5513 para −0,1395. Essas mudanças mostram que a especificação setorial altera a magnitude e a precisão das estimativas, mas não resolve o problema de identificação: os cinco pré-testes também falham nesse nível. Portanto, os p-valores menores dos fluxos não transformam os coeficientes em efeitos causais; o nível 2 serve para comparar ocupações dentro do mesmo setor e mês.
Esse quadro conversa bem com a fronteira recente da literatura empírica sobre IA e emprego. [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) não encontram quedas relativas semelhantes fora da faixa de 22 a 25 anos. Seus diagnósticos de pré-tendências, porém, dependem da medida de exposição: com a taxonomia da Anthropic, não há divergência anterior; com a medida de Eloundou *et al.*, o quintil mais exposto já apresentava crescimento mais lento do emprego desde cerca de 2020. Os autores situam o aparecimento mais agudo dos padrões no fim de 2022 e no início de 2023. A evidência posterior é mista: efeitos nulos e precisos sobre ganhos e horas na Dinamarca ([Humlum e Vestergaard, 2026](https://doi.org/10.3386/w33777)) e ausência de diferenças sistemáticas na *Current Population Survey* ([Chandar, 2025](https://doi.org/10.2139/ssrn.5384519)) convivem com resultados negativos em subgrupos e firmas. 
Em relação às não adotantes após o primeiro trimestre de 2023, firmas adotantes reduziram as contratações de trabalhadores juniores e também seus desligamentos, embora a queda nas contratações tenha sido cerca de quatro vezes maior ([Hosseini Maasoum; Lichtinger, 2026](https://doi.org/10.2139/ssrn.5425555)). No Reino Unido, [Klein Teeselink (2025)](https://doi.org/10.2139/ssrn.5516798) encontra reduções no emprego e nas novas vagas. O padrão, portanto, ainda não deve ser tratado como consolidado, e o exercício com a RAIS do Apêndice D não arbitra entre esses grupos de achados, porque seu diferencial de estoque é negativo, mas sua tendência prévia falha. 
Em resumo: não há efeito médio nacional robusto nos fluxos. Admissões, desligamentos e saldo são imprecisos e violam as tendências paralelas. O salário real de admissão é a exceção quanto à precisão, com redução de 5,1% estável nos quatro horizontes longos examinados (−0,0514, −0,0507, −0,0481 e −0,0548, todos rejeitando a 5%), mas partilha da mesma violação e não pode ser lido como efeito causal estabelecido; um placebo temporal em dezembro de 2021 passa no critério de 5% (−0,0198, com p = 0,081), embora recupere 39% do coeficiente principal, o que reforça a cautela. Nada disso demonstra ausência de efeitos futuros ou de mudanças concentradas em subgrupos. 
A próxima pergunta é, portanto, se os diferenciais estimados variam entre grupos sociodemográficos. A subseção seguinte examina essa possibilidade de forma exploratória, com ajuste de multiplicidade, diagnóstico de suporte e as mesmas ressalvas sobre tendências prévias.
## **5.2 Heterogeneidades demográficas**
Antes dos cinco recortes, apresento três observações sobre como esta subseção foi organizada.
A primeira é a distinção entre os dois estimadores. As tabelas do corpo do texto reportam o **DiD estimado dentro da amostra de cada grupo**, que podemos ler como, naquele grupo, as ocupações expostas divergiram das não expostas. Como o diferencial salarial nacional é de −0,0507 e rejeita a 5%, ele reaparece dentro de praticamente todo grupo: 22 dos 26 grupos da família de 130 testes apresentam queda salarial significativa depois do ajuste. Isso não é heterogeneidade, é o efeito médio visto de perto. Quem testa heterogeneidade é o **DDD**, no Apêndice A, que pergunta se a divergência de um grupo difere da do seu complemento.
A segunda observação é a multiplicidade. A família A reúne 100 contrastes DDD e a família C reúne 130 DiD estimados dentro dos grupos. Como muitos testes são feitos ao mesmo tempo, o procedimento de Benjamini-Hochberg ajusta cada valor p para limitar a proporção esperada de falsos positivos entre os resultados selecionados. Nas tabelas, “p BH” é esse valor p ajustado. Os asteriscos também usam o valor ajustado: \* para p BH abaixo de 0,10, \*\* abaixo de 0,05 e \*\*\* abaixo de 0,01. Dizer que um resultado sobrevive ao ajuste significa que seu p BH permanece abaixo de 0,05.
A terceira observação é o diagnóstico. Os testes de tendências paralelas falham em praticamente todas as células, com uma exceção discutida na subseção 5.2.3, e por isso os resultados são exploratórios. O suporte informa quantas ocupações tratadas e de controle, com fluxos observados, sustentam cada estimativa. Ele é adequado (`adequate`) quando há pelo menos 20 CBOs tratadas e 50 de controle; limitado (`limited`) quando há pelo menos 10 tratadas e 25 de controle, mas não se alcança o nível adequado; e baixo (`thin`) quando um desses limites mínimos não é atingido. Esses rótulos ajudam a avaliar a estabilidade da comparação, mas não corrigem a falha das pré-tendências.
### 5.2.1 Resultados por sexo
A Tabela 5.2.1 traz as estimativas por sexo, com o DiD calculado dentro da amostra de cada grupo. O contraste formal entre homens e mulheres está no Apêndice A.
**Tabela 5.2.1: Resultados por sexo**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD no grupo</td>
<td>EP</td>
<td>p BH</td>
<td>Pretrend</td>
<td>Suporte</td>
</tr>
<tr>
<td>Homens</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0779\*\*</td>
<td>0,0272</td>
<td>0,019</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Homens</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0635\*\*</td>
<td>0,0244</td>
<td>0,034</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Homens</td>
<td>Salário real de admissão (log)</td>
<td>−0,0501\*\*\*</td>
<td>0,0122</td>
<td>\< 0,001</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Homens</td>
<td>Saldo líquido (asinh)</td>
<td>−0,2451</td>
<td>0,3434</td>
<td>0,582</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0724</td>
<td>0,0464</td>
<td>0,228</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0776\*</td>
<td>0,0371</td>
<td>0,095</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Salário real de admissão (log)</td>
<td>−0,0491\*\*\*</td>
<td>0,0117</td>
<td>\< 0,001</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Saldo líquido (asinh)</td>
<td>−1,0188\*\*\*</td>
<td>0,3015</td>
<td>0,004</td>
<td>fail</td>
<td>adequate</td>
</tr>
</table>
> *Notas: cada linha traz o DiD estimado dentro da amostra do próprio grupo, com erro-padrão clusterizado por CBO de quatro dígitos. Família C, de 130 testes; as estrelas são calculadas exclusivamente sobre o p ajustado de Benjamini-Hochberg: \\* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. **Estas células não medem heterogeneidade.** O teste entre grupos é o contraste DDD do Apêndice A, no qual apenas 2 dos 100 contrastes salariais sobrevivem ao mesmo ajuste. O saldo em transformação asinh não deve ser interpretado como percentual. Fonte: `results/models/group_did_results.csv`.\*
Dentro de cada grupo, as estimativas repetem o padrão nacional: os diferenciais de admissões são de cerca de −7,5% entre homens e −7,0% entre mulheres, e os diferenciais do salário real de admissão são de −4,9% e −4,8%, ambos abaixo de 5% após o ajuste de multiplicidade. Em admissões, desligamentos e salário, homens e mulheres apresentam estimativas próximas, e os contrastes DDD não indicam uma diferença relevante entre os sexos. O saldo é uma exceção separada, discutida no parágrafo seguinte, mas sua pré-tendência falha.
O teste de heterogeneidade não encontra assimetria. O DDD de admissões é de **+0,0116**, com p ajustado de 0,907; o de desligamentos, +0,0332, com BH p = 0,581; o de salário, +0,0022, com BH p = 0,907. O único contraste de sexo que sobrevive ao ajuste é o saldo líquido, +0,7989 com BH p = 0,0026, e o saldo é o desfecho com o pior diagnóstico de tendências prévias de todo o trabalho, com 21 dos 22 leads individualmente significativos a 5%. Ele não sustenta leitura causal.
As Figuras 5.2.1.1 e 5.2.1.2 trazem os event studies e as trajetórias de admissões e salário de admissão por sexo.
**Figura 5.2.1.1: Admissões — event study e trajetórias por sexo**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/9dba5094-eeaa-4447-8e53-56041b378fa0/figure_5_2_1_1_sex_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=eda46eb23fd4824b94cf4ad76edf17cf88de82bfbccc0fcc2a96a82327580d4c&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura 5.2.1.2: Salário real de admissão — event study e trajetórias por sexo**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/f0048003-e495-4148-994f-63f869144d68/figure_5_2_1_2_sex_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=87c888bcf0a2cdb1786cc23366571d9b84bb7d99339bffdddf96c02f06d6b124&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
Nas admissões, as trajetórias de homens e mulheres em ocupações expostas correm próximas ao longo de todo o período, antes e depois do evento. No salário, os dois grupos ficam abaixo da média do próprio pré-período, com magnitudes muito parecidas: é a versão visual do que a tabela mostra.
A ausência de contrastes ajustados converge com [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/), que também não encontram efeitos diferenciais por sexo nos Estados Unidos. Continua valendo a leitura da Subseção 3.5.1 e de [Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[ (2025)](https://doi.org/10.54394/HETP0387) sobre a maior exposição ocupacional das mulheres, que é uma afirmação sobre exposição potencial, e não sobre ajuste realizado. O desenho não observa adoção de IA; as estimativas não revelam diferença entre os sexos no período observado, sem permitir concluir se houve ou não adoção ou impacto da IA.
Em resumo: nenhum contraste DDD de admissões, desligamentos ou salário por sexo sobrevive ao ajuste de multiplicidade. A maior exposição ocupacional das mulheres, documentada na Seção 3, não coincide com diferenças detectáveis nas estimativas da porta de entrada, mas isso não demonstra ausência de impacto.
### 5.2.2 Resultados por raça/cor
A Tabela 5.2.2 traz as estimativas por raça/cor, comparando trabalhadores brancos e negros, categoria que agrega pretos e pardos. Os contrastes DDD e a desagregação nas seis categorias do IBGE estão no Apêndice A.
**Tabela 5.2.2: Heterogeneidade por raça/cor — Branca e Negra**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD no grupo</td>
<td>EP</td>
<td>p BH</td>
<td>Pretrend</td>
<td>Suporte</td>
</tr>
<tr>
<td>Branca</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0241</td>
<td>0,0350</td>
<td>0,592</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Branca</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0182</td>
<td>0,0250</td>
<td>0,579</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Branca</td>
<td>Salário real de admissão (log)</td>
<td>−0,0544\*\*\*</td>
<td>0,0114</td>
<td>\< 0,001</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Branca</td>
<td>Saldo líquido (asinh)</td>
<td>−0,2246</td>
<td>0,3002</td>
<td>0,569</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0621</td>
<td>0,0446</td>
<td>0,261</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0584</td>
<td>0,0396</td>
<td>0,244</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Salário real de admissão (log)</td>
<td>−0,0513\*\*\*</td>
<td>0,0103</td>
<td>\< 0,001</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Saldo líquido (asinh)</td>
<td>−0,3264</td>
<td>0,2625</td>
<td>0,308</td>
<td>fail</td>
<td>adequate</td>
</tr>
</table>
> *Notas: cada linha traz o DiD estimado dentro da amostra do próprio grupo, com erro-padrão clusterizado por CBO de quatro dígitos. Família C, de 130 testes; estrelas calculadas exclusivamente sobre o p ajustado de Benjamini-Hochberg: \\* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Estas células não medem heterogeneidade; o teste entre grupos é o DDD do Apêndice A. O saldo em transformação asinh não deve ser interpretado como percentual. Fonte: `results/models/group_did_results.csv`.\*
Dentro de cada grupo, os coeficientes de fluxo são negativos e imprecisos nos dois casos, e o salário cai de forma significativa em ambos: 5,3% entre brancos e 5,0% entre negros. Essa semelhança é o eco do diferencial nacional.
Os contrastes DDD mais precisos aparecem em raça/cor. Para trabalhadores negros, são **−0,1144 nas admissões**, **−0,0990 nos desligamentos** e **−0,1068 no fluxo bruto**, os três com p ajustado de 0,015. Em termos aproximados, os diferenciais são de 10,8% nas admissões e 9,4% nos desligamentos. No salário, o DDD é de −0,0121, com p ajustado de 0,399. Assim, o padrão salarial aparece nos dois grupos, sem diferença racial detectável. Como as pré-tendências falham, os contrastes de fluxo permanecem exploratórios.
Duas qualificações são obrigatórias aqui. A primeira é que **os contrastes do agregado negro são conduzidos principalmente pela categoria parda**. Na desagregação em seis categorias, o contraste de pardos é de −0,0817 nas admissões (p ajustado de 0,042) e −0,0886 nos desligamentos (p ajustado de 0,018), enquanto o de pretos não se distingue de zero em nenhum desfecho: −0,0088 nas admissões (p ajustado de 0,907) e +0,0445 nos desligamentos (p ajustado de 0,341). Agregar as duas categorias produz um contraste maior, mas não autoriza interpretação causal sobre nenhuma delas.
A segunda: **o agregado é mais forte que qualquer um de seus componentes**. Parece contradição, mas não é, porque os complementos são diferentes. O contraste da categoria *Negra* compara pretos e pardos com brancos, amarelos, indígenas e não identificados; o de *parda*, isoladamente, compara pardos com um complemento que **inclui os pretos**. Como as estimativas de pretos e pardos apontam na mesma direção, separá-los reduz o contraste de cada um.
A categoria amarela precisa de uma distinção clara entre os dois estimadores. O DiD dentro do grupo é de −0,3479 nas admissões e −0,2722 nos desligamentos. Já o DDD, que compara esse grupo com seu complemento, é de −0,2770 e −0,2179, respectivamente. Nos quatro casos, o p ajustado fica abaixo de 0,001 e o suporte ocupacional é adequado, mas as pré-tendências falham. 
As Figuras 5.2.2.1 e 5.2.2.2 trazem os event studies e as trajetórias normalizadas de admissões e salário real de admissão.
**Figura 5.2.2.1 Admissões — event study e trajetórias por raça/cor**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/43569aa6-4fda-4f26-8bec-dda7e914784d/figure_5_2_2_1_race_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=2338a85c6375b5d31b2788d9d6dc17cd57dd421928bec823a7500fdc8bd4eefb&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura 5.2.2.2: Salário real de admissão — event study e trajetórias por raça/cor**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/a085e669-69fb-46ff-b89d-b5c38af8715b/figure_5_2_2_2_race_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=86e7acfc9de737786b2a8508a34d8cd3a4b3d25a628d935640b4f736376eecc3&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
Nas admissões, a trajetória dos trabalhadores negros em ocupações expostas se afasta da observada entre brancos no período posterior, contrapartida visual do contraste DDD. No salário, as duas trajetórias caem e permanecem próximas. As figuras são descritivas e não superam as falhas de pré-tendências.
Esse padrão qualifica a Subseção 3.5.2. Os trabalhadores brancos estão mais presentes em ocupações altamente expostas, enquanto os contrastes de fluxo mais negativos aparecem entre trabalhadores negros. Exposição e heterogeneidade estimada, portanto, apontam em direções diferentes, mas o desenho não permite chamar essa diferença de ajuste causado pelo ChatGPT. A comparação internacional permanece limitada, pois os principais estudos empíricos lidos para essa dissertação não apresentam estimativas causais desagregadas por raça ([Brynjolfsson; Chandar; Chen, 2025](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/); [Hosseini Maasoum; Lichtinger, 2026](https://doi.org/10.2139/ssrn.5425555); [Klein Teeselink, 2025](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5516798)).
Em resumo: raça/cor é a dimensão com os contrastes ajustados mais precisos nos três desfechos de fluxo, mas não no salário. Como admissões e desligamentos apresentam diferenciais negativos, o padrão é compatível com menor movimentação relativa; sem observar o estoque e com pré-tendências falhas, não é possível distinguir rotatividade, perda líquida de vínculos ou outros mecanismos. Na desagregação, os contrastes negativos aparecem sobretudo entre pardos, não de forma homogênea em toda a população negra.
### 5.2.3 Resultados por faixa etária
A Tabela 5.2.3 traz as estimativas por faixa etária, nas faixas da PNAD/IBGE. Os contrastes DDD e os painéis da classificação etária adotada por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) são apresentados no Apêndice A.
**Tabela 5.2.3: Heterogeneidade por faixa etária — faixas PNAD/IBGE**
<table header-row="true">
<tr>
<td>Faixa etária</td>
<td>Resultado</td>
<td>DiD no grupo</td>
<td>EP</td>
<td>p BH</td>
<td>Pretrend</td>
<td>Suporte</td>
</tr>
<tr>
<td>18–24</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0380</td>
<td>0,0360</td>
<td>0,399</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0170</td>
<td>0,0443</td>
<td>0,753</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Salário real de admissão (log)</td>
<td>−0,0512\*\*\*</td>
<td>0,0111</td>
<td>\< 0,001</td>
<td>warning</td>
<td>adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Saldo líquido (asinh)</td>
<td>−0,0344</td>
<td>0,1930</td>
<td>0,872</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0693\*</td>
<td>0,0314</td>
<td>0,079</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0608\*</td>
<td>0,0258</td>
<td>0,059</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Salário real de admissão (log)</td>
<td>−0,0460\*\*\*</td>
<td>0,0110</td>
<td>\< 0,001</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Saldo líquido (asinh)</td>
<td>−0,5069</td>
<td>0,3529</td>
<td>0,250</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0454</td>
<td>0,0343</td>
<td>0,286</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0398</td>
<td>0,0270</td>
<td>0,244</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Salário real de admissão (log)</td>
<td>−0,0549\*\*\*</td>
<td>0,0129</td>
<td>\< 0,001</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Saldo líquido (asinh)</td>
<td>−0,5498</td>
<td>0,3050</td>
<td>0,162</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0125</td>
<td>0,0469</td>
<td>0,822</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0221</td>
<td>0,0325</td>
<td>0,593</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Salário real de admissão (log)</td>
<td>−0,0417\*\*\*</td>
<td>0,0114</td>
<td>0,002</td>
<td>warning</td>
<td>adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Saldo líquido (asinh)</td>
<td>−0,2274</td>
<td>0,2270</td>
<td>0,425</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0399</td>
<td>0,0678</td>
<td>0,646</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0860\*</td>
<td>0,0394</td>
<td>0,082</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Salário real de admissão (log)</td>
<td>−0,0448\*\*\*</td>
<td>0,0129</td>
<td>0,003</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Saldo líquido (asinh)</td>
<td>0,3794\*\*</td>
<td>0,1345</td>
<td>0,020</td>
<td>fail</td>
<td>adequate</td>
</tr>
</table>
> *Notas: cada linha traz o DiD estimado dentro da amostra da própria faixa, com erro-padrão clusterizado por CBO de quatro dígitos. Família C, de 130 testes; estrelas calculadas exclusivamente sobre o p ajustado de Benjamini-Hochberg: \\* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Estas células não medem heterogeneidade; o teste entre faixas é o DDD do Apêndice A. A amostra é restrita a trabalhadores de 18 a 65 anos. Fonte: `results/models/group_did_results.csv`.\*
Dentro de cada faixa, os coeficientes de admissão são negativos e majoritariamente imprecisos, e o salário de entrada cai de forma significativa em **todas** as cinco faixas, entre 4,2% e 5,5%. A queda salarial não é um fenômeno de jovens: ela atravessa a distribuição etária inteira.
Nas faixas etárias do artigo de referência, o DDD das admissões entre trabalhadores de 22 a 25 anos é de −0,0189, com p ajustado de 0,652. Portanto, não aparece uma queda adicional dos mais jovens em relação ao restante da amostra. O contraste que permanece abaixo de 5% após o ajuste é o da faixa de 41 a 49 anos, e tem sinal positivo: +0,0841 nas admissões, +0,0699 nos desligamentos e +0,0776 no fluxo bruto.
Em termos simples, o DDD positivo da faixa de 41 a 49 anos indica que a diferença entre ocupações expostas e não expostas foi menos negativa, ou mais positiva, nesse grupo do que em seu complemento. Os contrastes intermediários mudam gradualmente de sinal, mas nenhum permanece abaixo de 5% após o ajuste. Como as pré-tendências falham, o conjunto deve ser lido apenas como um padrão relativo entre faixas etárias, sem atribuição de mecanismo.
No salário, nenhum contraste etário sobrevive ao ajuste: o DDD da faixa de 22 a 25 anos é de −0,0004, com p ajustado de 0,974. O diferencial salarial é generalizado e não etário.
As Figuras 5.2.3.1 e 5.2.3.2 trazem os event studies e as trajetórias de admissões e salário real de admissão em todas as faixas da PNAD/IBGE.
**Figura 5.2.3.1: Heterogeneidade por idade — admissões**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/83d038a4-ea95-4dca-9499-6e98ef3e4670/figure_5_2_3_1_age_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=0d49aca2bd6cad4ddbbaed0821f3e237b41720202b2081c1db52804a2867bb49&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
**Figura 5.2.3.2: Heterogeneidade por idade — Salário real de admissão**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/f2ed0e44-a833-4aa6-a352-2a2b6a05f7f0/figure_5_2_3_2_age_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=03066aa6bc3326585331d6f6e58c76e5c29602864f1eff1118b66fd77e3badfe&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
<br>As figuras evidenciam comportamentos distintos entre as faixas, mas não estabelecem hierarquia etária causal.
Há uma exceção diagnóstica que merece ser mostrada. No DiD estimado **dentro** da coorte de 22 a 25 anos, o salário real de admissão apresenta diferencial de −0,0517, com p nominal de 1×10⁻⁶ e p ajustado de 4×10⁻⁵, e o teste conjunto de tendências prévias não é rejeitado, com p = 0,585. 
Essa é uma das duas únicas células, entre os cem contrastes estimados dentro dos grupos, cujo teste conjunto de tendências prévias não é rejeitado; a outra é o salário na categoria indígena, reportada no Apêndice A. Somados os três casos classificados como alerta, cinco dos cem contrastes escapam da classificação de falha, e outros cinco têm diagnóstico indefinido por deficiência de rank. Como não houve ajuste de multiplicidade para essa família de diagnósticos, um punhado de exceções é exatamente o que se espera por acaso quando cem testes são realizados. Por isso, trato o resultado como uma exceção que merece ser mostrada, não como uma validação do desenho. A Figura 5.2.3.3 mostra esse contraste isoladamente: os coeficientes pré-tratamento oscilam em torno de +0,0064, sem tendência e sem nenhum lead individualmente significativo a 5%, e a trajetória posterior se estabelece de forma persistente abaixo dessa média. A distância entre a linha tracejada e o pós-evento é de −0,0507, praticamente idêntica ao DiD de −0,0517 estimado dentro do grupo.
**Figura 5.2.3.3: Coorte de 22 a 25 anos — salário real de admissão**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/d38fc5a1-b553-4453-bdb4-cd486a06860c/2cd4f183-47b1-4136-8fed-c2e403155a78.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=37a63e39116eacdda0ca077f78b555d23d79a1c485f8b3f7973f16c9307b0bd9&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<br>Nas admissões, as estimativas brasileiras não reproduzem o padrão concentrado entre 22 e 25 anos reportado por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/), de queda de 15 pontos log no emprego relativo dos trabalhadores de 22 a 25 anos nos quintis mais expostos à IA, em comparação com o quintil menos exposto. A comparação pede cuidado. Os autores analisam estoque de emprego em firmas e comparam quintis de exposição, enquanto esta dissertação observa fluxos mensais por ocupação e usa uma classificação binária mais ampla. Aqui, o contraste ajustado aparece na faixa de 41 a 49 anos e tem sinal positivo. O estoque ocupacional anual do Apêndice D não permite aproximar a comparação porque não é desagregado por idade. [Hosseini Maasoum e Lichtinger (2026)](https://doi.org/10.2139/ssrn.5425555) também encontram redução do emprego júnior sobretudo pela desaceleração das contratações, enquanto, nesta análise, o contraste etário mais preciso aparece nos desligamentos.
<br>Em resumo: a maior exposição dos jovens documentada na Seção 3.5.3 não coincide com uma retração diferencial de suas admissões. Os contrastes etários que sobrevivem ao ajuste de multiplicidade são positivos e se concentram na faixa de 41 a 49 anos. Eles registram uma diferença relativa entre faixas, não proteção dos trabalhadores de meia-idade nem punição dos jovens. Como as tendências prévias falham, a leitura permanece exploratória. 
Na margem salarial, a queda é generalizada e atinge todas as faixas com magnitude semelhante, sem heterogeneidade etária detectável. Nessa margem e nessa coorte está a única célula cujo teste conjunto de tendências prévias não é rejeitado: dentro do grupo de 22 a 25 anos, o diferencial do salário de entrada é preciso. Como se trata de uma exceção entre cem diagnósticos, o resultado é reportado sem ser tratado como validação causal.
### 5.2.4 Resultados por nível de escolaridade
A Tabela 5.2.4 traz as estimativas por nível de escolaridade. Os contrastes DDD e os diagnósticos estão no apêndice.
**Tabela 5.2.4: Heterogeneidade por nível de escolaridade**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD no grupo</td>
<td>EP</td>
<td>p BH</td>
<td>Pretrend</td>
<td>Suporte</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Admissões (PPML, nível)</td>
<td>0,0018</td>
<td>0,0531</td>
<td>0,974</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Desligamentos (PPML, nível)</td>
<td>0,0141</td>
<td>0,0469</td>
<td>0,800</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Salário real de admissão (log)</td>
<td>−0,0080</td>
<td>0,0144</td>
<td>0,661</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Saldo líquido (asinh)</td>
<td>0,3330</td>
<td>0,1668</td>
<td>0,112</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0438</td>
<td>0,0314</td>
<td>0,261</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0455</td>
<td>0,0307</td>
<td>0,244</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Salário real de admissão (log)</td>
<td>−0,0427\*\*\*</td>
<td>0,0122</td>
<td>0,003</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Saldo líquido (asinh)</td>
<td>−0,2973</td>
<td>0,3251</td>
<td>0,470</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Admissões (PPML, nível)</td>
<td>−0,1075\*\*</td>
<td>0,0371</td>
<td>0,017</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0939\*\*</td>
<td>0,0363</td>
<td>0,035</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Salário real de admissão (log)</td>
<td>−0,0352\*\*\*</td>
<td>0,0093</td>
<td>0,001</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Saldo líquido (asinh)</td>
<td>−1,1562\*\*\*</td>
<td>0,3173</td>
<td>0,002</td>
<td>fail</td>
<td>adequate</td>
</tr>
</table>
> *Notas: cada linha traz o DiD estimado dentro da amostra do próprio grupo, com erro-padrão clusterizado por CBO de quatro dígitos. Família C, de 130 testes; estrelas calculadas exclusivamente sobre o p ajustado de Benjamini-Hochberg: \\* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Estas células não medem heterogeneidade; o teste entre grupos é o DDD do Apêndice A. Fonte: `results/models/group_did_results.csv`.\*
Os diferenciais negativos de fluxo são mais pronunciados entre trabalhadores com ensino superior. Dentro desse grupo, as estimativas são de −0,1075 nas admissões (p ajustado de 0,017) e −0,0939 nos desligamentos (p ajustado de 0,035), enquanto os níveis médio e fundamental não apresentam estimativas de fluxo abaixo de 5% após o ajuste. No salário, os diferenciais são negativos nos níveis médio e superior, mas não no fundamental.
No contraste DDD, a direção se mantém e a magnitude é grande, **mas a significância fica no limite depois do ajuste de multiplicidade**. O contraste do ensino superior nas admissões é de −0,1108, com p nominal de 0,0145 e **p ajustado de 0,055**: fora do limiar de 5%, ainda que por pouco. Nos desligamentos ocorre o mesmo, com −0,1064 e p ajustado de 0,055. Dois contrastes do grupo sobrevivem ao ajuste: o fluxo bruto, com −0,1083 e p ajustado de 0,048, e o saldo líquido, com −0,8421 e p ajustado de 0,015. O sentido oposto também aparece: o contraste do ensino fundamental é positivo, com +0,1231 nas admissões, também no limite, e saldo de +0,9560 com p ajustado de 0,043.
Os contrastes de fluxo do ensino superior apontam na direção negativa, mas, nas duas margens mais diretas, admissões e desligamentos, não cruzam o limiar ajustado. Apenas as medidas agregadas de fluxo bruto e saldo ficam abaixo de 5%. No salário, o DDD do ensino superior é de +0,0076, com p ajustado de 0,707, sem diferença detectável entre níveis. As falhas de pré-tendências impedem interpretação causal desses padrões.
As Figuras 5.2.4.1 e 5.2.4.2 trazem os event studies e as trajetórias de admissões e salário real de admissão por escolaridade.
**Figura 5.2.4.1: Admissões — event study e trajetórias por escolaridade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/60273f1e-707d-4f3a-a4b6-a57229a20808/figure_5_2_4_1_education_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=30eb549e8015564f772675dba78860087f858c69cdf864540751816d9e8849e6&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura 5.2.4.2: Salário real de admissão — event study e trajetórias por escolaridade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/4fc552e5-f436-4e79-b799-ee9749a4e119/figure_5_2_4_2_education_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=34ce769122d529a4d01de639718597ac4623c3f22dac7998a2edaaf1fc3b8483&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
Nas admissões, as trajetórias do ensino superior mantêm as ocupações expostas abaixo das não expostas ao longo do pós-evento, e a separação entre níveis educacionais é visível. Nos salários, as trajetórias dos três níveis permanecem próximas. As figuras são descritivas e não corrigem as falhas de pré-tendências.
A direção das estimativas dialoga com a Subseção 3.5.4, que mostrou aumento expressivo da exposição à IA com a escolaridade, mas exposição e ajuste não são equivalentes. Também é compatível com [Klein Teeselink (2025)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5516798), que encontra efeitos concentrados em firmas e ocupações de alta remuneração no Reino Unido. A comparação não é direta, pois remuneração não equivale a escolaridade. [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) mostram ainda que ocupações com menor proporção de graduados também podem ser afetadas, enquanto [Hosseini Maasoum e Lichtinger (2026)](https://doi.org/10.2139/ssrn.5425555) identificam diferenças importantes dentro do próprio ensino superior.
Em resumo: os contrastes educacionais ficam próximos do limiar nas margens principais. Entre trabalhadores com ensino superior, admissões e desligamentos têm p ajustado de 0,055, e apenas fluxo bruto e saldo ficam abaixo de 5%. Não há diferença salarial detectável por escolaridade nem base para afirmar contração líquida do emprego ou efeito causado pela IA.
### 5.2.5 Resultados por faixa salarial ocupacional
A Tabela 5.2.5 traz as estimativas por faixa salarial ocupacional, definida pela mediana pré-tratamento da CBO e não pela renda individual. Aqui a coluna de suporte pesa mais do que em qualquer outro recorte.
**Tabela 5.2.5: Estimativas dentro dos grupos por faixa salarial ocupacional**
<table header-row="true">
<tr>
<td>Faixa de renda</td>
<td>Resultado</td>
<td>DiD no grupo</td>
<td>EP</td>
<td>p BH</td>
<td>Pretrend</td>
<td>Suporte</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0304</td>
<td>0,0321</td>
<td>0,453</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0409</td>
<td>0,0299</td>
<td>0,271</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Salário real de admissão (log)</td>
<td>−0,0493\*\*\*</td>
<td>0,0140</td>
<td>0,003</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Saldo líquido (asinh)</td>
<td>0,2144</td>
<td>0,3569</td>
<td>0,642</td>
<td>fail</td>
<td>adequate</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Admissões (PPML, nível)</td>
<td>−0,1914\*\*</td>
<td>0,0664</td>
<td>0,021</td>
<td>fail</td>
<td>limited</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Desligamentos (PPML, nível)</td>
<td>−0,1028</td>
<td>0,0800</td>
<td>0,298</td>
<td>fail</td>
<td>limited</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Salário real de admissão (log)</td>
<td>−0,0434</td>
<td>0,0258</td>
<td>0,198</td>
<td>fail</td>
<td>limited</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Saldo líquido (asinh)</td>
<td>−1,2484</td>
<td>0,8350</td>
<td>0,244</td>
<td>warning</td>
<td>limited</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Admissões (PPML, nível)</td>
<td>−0,0068</td>
<td>0,0954</td>
<td>0,952</td>
<td>fail</td>
<td>thin</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Desligamentos (PPML, nível)</td>
<td>0,1564</td>
<td>0,1053</td>
<td>0,272</td>
<td>not_estimated</td>
<td>thin</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Salário real de admissão (log)</td>
<td>0,0117</td>
<td>0,0345</td>
<td>0,785</td>
<td>fail</td>
<td>thin</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Saldo líquido (asinh)</td>
<td>−3,4227</td>
<td>2,1171</td>
<td>0,244</td>
<td>fail</td>
<td>thin</td>
</tr>
</table>
> *Notas: cada linha traz o DiD estimado dentro da amostra da própria faixa, com erro-padrão clusterizado por CBO de quatro dígitos. Família C, de 130 testes; estrelas calculadas exclusivamente sobre o p ajustado de Benjamini-Hochberg: \\* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. As faixas utilizam a mediana salarial pré-tratamento da CBO, expressa em salários mínimos, e não a renda individual corrente. **A coluna de suporte é parte do resultado:** `limited` indica 26 CBOs tratadas e 32 de controle; `thin` indica 3 tratadas e 6 de controle, base insuficiente para inferência substantiva. `not_estimated` no pretrend registra que a inclinação GLS não é identificada naquela célula. Fonte: `results/models/group_did_results.csv`.\*
O único movimento nominalmente forte está nas admissões da faixa de 2 a 5 salários mínimos, com −0,1914 e p ajustado de 0,021 no DiD dentro do grupo. Ele precisa ser lido com a coluna de suporte ao lado: a faixa reúne 26 CBOs tratadas e 32 de controle, o que a classifica como suporte `limited`.
O contraste DDD, porém, **não sustenta** a leitura de que a redução dos desligamentos se concentraria na renda intermediária. O DDD de desligamentos dessa faixa é de −0,0543 (p ajustado de 0,707) e o de admissões, de −0,1474 (p ajustado de 0,164). Nenhum dos quinze contrastes de renda sobrevive ao ajuste de multiplicidade com suporte adequado.<br><br>Na faixa de até 2 salários mínimos, nem as estimativas dentro do grupo nem os contrastes DDD ficam abaixo de 5% depois do ajuste: as admissões dão +0,1183, com p ajustado de 0,325. Esse resultado não sustenta diferença entre faixas de renda.
Acima de 5 salários mínimos, a limitação é severa: a comparação depende de 3 CBOs tratadas e 6 de controle. Existe nessa faixa um contraste DDD de salário positivo que sobrevive nominalmente ao ajuste, mas ele repousa sobre três ocupações tratadas e, por isso, **fica registrado na tabela com o rótulo de suporte ****`thin`**** e não é usado como base de afirmação**.
A Figura 5.2.5.1 traz os event studies e as trajetórias das admissões por renda pré-tratamento.
**Figura 5.2.5.1: Admissões — event studies e trajetórias por renda pré-tratamento**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/230c0c5e-7145-4568-bd88-6a94acbd37cf/figure_5_2_5_1_income_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=07311ddbc7618a0bc5ab178843a2509907b3363e620f2dc74bc9e40b995159e2&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A maior volatilidade da faixa superior decorre do pequeno número de ocupações: os coeficientes dependem de apenas 3 CBOs expostas e 7 não expostas, o que amplia a incerteza das estimativas.
A Figura 5.2.5.2 faz o mesmo para o salário real de admissão.
**Figura 5.2.5.2: Salário real de admissão — event studies e trajetórias por renda pré-tratamento**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/de949134-0684-4087-9a5f-7526bb134454/figure_5_2_5_2_income_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=57bea524bf3e38cbf8a53d2aadbcb086f29c58b8ccde1aeffa713a3366d93295&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
Os coeficientes salariais oscilam em torno de zero e seus intervalos de confiança são amplos. Os testes conjuntos não rejeitam os pretrends nas duas primeiras faixas (p=0,417 e p=0,277), mas ambas são classificadas como falha porque apresentam três coeficientes pré-tratamento individualmente significativos. No topo, o teste conjunto é limítrofe (p=0,057) e gera alerta. Não há, portanto, evidência de heterogeneidade salarial robusta.
O resultado dialoga com a Subseção 3.5.5, que mostrou a alta exposição crescendo até as faixas intermediárias e depois se estabilizando. A comparação é indicativa, porque lá os trabalhadores são classificados por renda e aqui uso a mediana salarial da CBO. O padrão também converge em parte com [Klein Teeselink (2025)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5516798), que encontra maior ajuste nos segmentos de alta remuneração do Reino Unido e pouca alteração nos de baixa remuneração. A correspondência não é exata: aqui o sinal está na faixa intermediária e o topo não tem suporte. Já a ausência de contrastes salariais é compatível com [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/), que encontram ajustes mais visíveis no emprego do que na remuneração.
Não aparece uma heterogeneidade por renda sustentada pelo conjunto dos diagnósticos. Nenhum contraste DDD com suporte adequado permanece abaixo de 5% após o ajuste de multiplicidade. O único que cruza esse limiar é o salário na faixa acima de 5 salários mínimos, com coeficiente de +0,0643 e p BH de 0,043, mas o suporte é baixo: apenas 3 CBOs tratadas e 6 de controle, além de pré-tendência falha. A queda salarial de −0,0493 na faixa de até 2 salários mínimos é um DiD dentro do grupo e apenas reproduz o diferencial nacional; ela não demonstra que as faixas de renda respondem de modo diferente. Portanto, não há base para afirmar proteção do topo, compressão salarial ou redução diferencial do emprego líquido por faixa de renda.
### 5.2.6 Síntese das heterogeneidades demográficas
Dos **100 contrastes de diferença tripla, 34 são nominalmente significativos a 5% e 21 sobrevivem ao ajuste de Benjamini-Hochberg**. Os contrastes que permanecem se concentram em **raça/cor** e **faixa etária**; sexo e renda não apresentam diferenças ajustadas, e escolaridade fica próxima do limiar. Esses resultados são exploratórios porque as tendências prévias falham e o suporte varia entre células.
Os cinco eixos podem ser resumidos assim. **Sexo:** nenhum contraste de fluxo ou salário sobrevive ao ajuste. **Raça/cor:** os contrastes de fluxo mais negativos aparecem entre trabalhadores negros, sobretudo pardos, mas não identificam um efeito da tecnologia sobre esses grupos. **Idade:** os contrastes que sobrevivem são positivos e se concentram entre 41 e 49 anos, indicando uma diferença relativa, não proteção. **Escolaridade:** os contrastes do ensino superior ficam próximos do limiar, com p ajustado de 0,055 em admissões e desligamentos. **Renda:** nenhum resultado se sustenta com suporte adequado.
No salário de admissão, o diferencial negativo aparece em quase todos os grupos, mas apenas 2 dos 100 contrastes salariais de diferença tripla sobrevivem ao ajuste. As duas informações são compatíveis: há um padrão salarial disseminado entre grupos e pouca evidência de que sua magnitude difira entre eles. Como as tendências prévias também falham, esse padrão não recebe interpretação causal.
A **Figura 5.2.6** reúne os 130 contrastes de DiD estimados dentro dos grupos, organizados por desfecho, com intervalos ajustados por Benjamini-Hochberg e marcação das células de suporte `limited` e `thin`. Ela sintetiza a multiplicidade dos testes, a maior precisão do salário em relação aos fluxos e a raridade dos contrastes que permanecem após o ajuste.
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/d5337407-9dba-4b46-9b01-9d58fe1a48d3/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=64d5e1268a3d032123c996e414635dca66cf8bb55ada582065cafc89ce641517&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
# 6 Conclusão
## 6.1 O que os dados mostram
A resposta à primeira pergunta é nítida. Entre os 97,8 milhões de trabalhadores retratados no terceiro trimestre de 2025, 10,1% estão em ocupações de alta exposição, e essa exposição não se distribui de maneira neutra: elas se concentram no apoio administrativo, entre mulheres, brancos, jovens e trabalhadores de maior escolaridade. A formalidade reforça o recorte, com 14,8% dos formais em alta exposição contra 6,7% dos informais, e foi isso que fez do CAGED a base adequada para a etapa empírica.
A resposta à segunda é mais qualificada. No agregado nacional, os coeficientes dos fluxos são negativos e imprecisos. O padrão mais consistente está no salário real de admissão, com diferencial de −0,0507, que fica mais preciso quando entra o controle setorial e reaparece em quase todos os grupos demográficos examinados: 22 dos 26 grupos exibem queda salarial significativa depois do ajuste de multiplicidade. Mas **a tendência prévia do salário também é rejeitada**. Por isso, a estimativa descreve o padrão mais estável dos dados, mas não identifica um efeito causal.
As heterogeneidades acrescentam padrões exploratórios. Dos 100 contrastes de diferença tripla, 34 são nominalmente significativos e 21 sobrevivem ao ajuste de Benjamini-Hochberg, concentrados em raça/cor e faixa etária. Os contrastes raciais são mais negativos para trabalhadores negros, sobretudo pardos. No eixo etário, os contrastes que sobrevivem são positivos e se concentram entre 41 e 49 anos, o que indica uma diferença relativa em relação às demais faixas, não proteção desse grupo. Sexo e renda não apresentam contrastes sustentados pelo ajuste, e escolaridade fica no limiar. Como as tendências prévias falham, esses padrões não estabelecem quem foi afetado pela tecnologia.
**O mapa da exposição potencial não coincide com o mapa das heterogeneidades estimadas.** Mulheres e trabalhadores de maior escolaridade estão entre os mais expostos, mas não concentram os contrastes ajustados, enquanto os contrastes raciais mais negativos aparecem entre trabalhadores negros, que não estão entre os grupos mais expostos. Essa diferença entre os mapas é descritiva. O desenho não permite concluir quem absorveu um ajuste nem por qual mecanismo ele teria ocorrido.
Os dois exercícios complementares do Apêndice D atacaram limitações que o próprio desenho declarava. Na RAIS, o estoque de vínculos das ocupações expostas aparece menor no pós e o diferencial de rotatividade não se distingue de zero, combinação que **não favorece a hipótese de acomodação silenciosa**. Na PNAD Contínua, procurei deslocamento em direção à informalidade e não encontrei: nenhum dos seis testes rejeita, e os estoques formal e informal se movem no mesmo sentido. As duas medições de estoque discordam de sinal entre si, e deixei a discordância declarada em vez de arbitrada, porque elas não medem o mesmo objeto e escolher a que rejeita seria decidir pelo resultado.
## 6.2 O que o desenho não permite afirmar
As ressalvas abaixo não são formalidade de encerramento; elas delimitam o que se pode levar deste trabalho.
**Exposição não é adoção, e adoção não é impacto.** O índice mede o potencial técnico das tarefas, e nenhuma das bases utilizadas observa se firmas e trabalhadores de fato passaram a usar a tecnologia. Toda a evidência empírica desta dissertação é, nesse sentido, sobre ocupações potencialmente afetadas, e não sobre ocupações comprovadamente atingidas.
**A identificação causal não foi alcançada.** Os testes de tendências paralelas são rejeitados em praticamente todas as células examinadas, inclusive na do salário de admissão, e a rejeição persiste sob especificações alternativas de amostra, agregação e definição de tratamento. Os coeficientes reportados descrevem diferenças entre grupos após um evento; não são efeitos do evento.
**A janela é curta e o evento é difuso.** O lançamento do ChatGPT é uma data conveniente, mas a difusão de uma tecnologia de propósito geral não ocorre num instante, e parte dos ajustes de emprego pode levar mais tempo do que o período observado.
**A tradução entre classificações introduz erro de medida**, mais relevante no CAGED do que na PNAD, e o índice é global, podendo não captar particularidades do conteúdo das tarefas no Brasil.
**O desenho não observa trajetória individual.** Os dados são de fluxo ocupacional e de cortes transversais repetidos; eles não acompanham o mesmo trabalhador ao longo do tempo e, portanto, não permitem afirmar para onde foi quem deixou uma ocupação exposta.
**A janela não contém um período pré-pandemia.** O CAGED foi reformulado em 2020 e a série comparável começa em janeiro de 2021, de modo que o pré-tratamento inteiro é um mercado de trabalho em recuperação. Dá para encurtar a amostra e comparar, como faço na escada de especificações, mas não dá para construir com esta fonte um pré-período anterior à pandemia. É limitação estrutural do desenho, e não escolha de amostra.
**O exercício de estoque cobre apenas dois anos posteriores.** A safra da RAIS vai até 2024, o que deixa 2023 e 2024 como os únicos anos pós-tratamento completos do Apêndice D.1, margem estreita para uma série anual.
## 6.3 Interpretação
O que vem a seguir são leituras minhas sobre por que os resultados têm a forma que têm. Nenhuma é identificada pelo desenho, e nenhuma deve ser lida como conclusão do trabalho. Em cada uma procuro dizer o que a distinguiria de suas alternativas, para que a especulação venha acompanhada do seu próprio teste.
**Por que as tendências prévias falham.** A rejeição sistemática das tendências paralelas é o fato metodológico central deste trabalho. Tenho duas hipóteses, e elas não se excluem.
A primeira é a pandemia. O painel começa em janeiro de 2021 e o pré-tratamento vai até novembro de 2022, então **não há um único mês pré-pandemia na janela de comparação**, e janeiro de 2021 é o auge da segunda onda no Brasil. O teste não examina um mercado de trabalho em regime, e sim um mercado em recuperação de um choque que atingiu de forma muito desigual justamente o eixo que o índice separa. Por mais de dois anos, o trabalho de escritório e o atendimento remoto operaram sob uma demanda que a distância física inflou, enquanto o trabalho presencial foi suspenso ou reduzido. Se essa demanda estava se corrigindo ao longo de 2022 e 2023, expostas e não expostas já vinham em trajetórias distintas por razões que nada têm a ver com o ChatGPT. Registro, porém, que os resultados da principal referência desta dissertação dependem da medida de exposição. [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) não encontram divergência prévia com a taxonomia da Anthropic, mas reconhecem que, com a medida de Eloundou *et al.*, o quintil mais exposto já apresentava crescimento mais lento do emprego desde cerca de 2020. A falha de tendências prévias encontrada aqui é mais generalizada, mas não inteiramente ausente do caso americano. Essa diferença pode refletir a janela, o painel brasileiro não contém um único mês pré-pandemia, enquanto o deles recua bem antes de 2020, ou a composição do grupo tratado.
Os dados dão apoio. Começando a amostra em janeiro de 2022, o diferencial salarial cai de −0,0507 para −0,0363, cerca de 28% menor. Interagindo a composição pré-tratamento com o indicador de pós, cai para −0,0360. E a decomposição da subseção 5.1 atribui de 23% a 29% do diferencial a composição educacional. As três reduções apontam na mesma direção: parte apreciável do resultado mais forte do trabalho é herança da janela, e não do evento.
O contra-argumento é forte e desfavorece a minha leitura: controlar a tendência prévia não elimina o resultado. Com uma inclinação linear ajustada apenas no pré-período como regressor, o diferencial salarial fica em −0,0464, e o de admissões passa de −0,0538, sem significância, para −0,0662 com p de 0,004. A falha desqualifica a leitura causal, mas não explica mecanicamente os resultados.
A segunda hipótese é macroeconômica. O pós-pandemia trouxe inflação alta e um ciclo de aperto monetário que estreitou crédito e investimento justamente onde estão os projetos de expansão comercial e administrativa. Vale olhar o que o grupo tratado é em volume, e não em rótulo. Das 75 famílias classificadas como expostas, uma sozinha, a de auxiliares de escritório e assistentes administrativos, responde por 31,8% das admissões pré-tratamento do grupo, e as cinco maiores somam 65,4%: escritório, atendimento comercial, recepção, telemarketing e vendas. A diferença entre os grupos não para no volume. Antes do evento, 19,7% dos admitidos nas ocupações tratadas tinham ensino superior, contra 4,0% no controle, quase cinco vezes mais; a idade média era de 28,9 anos contra 33,8, e o desvio-padrão do crescimento mensal das admissões era de 8,3% contra 14,0%. Tratados e controle não são o mesmo tipo de trabalho medido com exposições diferentes: são populações ocupacionais estruturalmente distintas. O grupo exposto é, em massa, o trabalho administrativo e de atendimento brasileiro, cuja contratação responde ao ciclo de comércio e serviços. Um aperto monetário produziria exatamente o que se observa, contratação mais fraca e salário de entrada mais baixo.
Daí vem um problema de identificação que considero mais sério do que o erro de medida do crosswalk: **a fronteira que o índice de exposição desenha e a fronteira entre trabalho de escritório e trabalho não-escritório são quase a mesma fronteira.** Um choque tecnológico sobre o trabalho administrativo e um choque de demanda sobre o trabalho administrativo produzem o mesmo coeficiente. Nenhuma sofisticação econométrica separa os dois quando a variável de tratamento não os distingue. O que separaria é uma medida de adoção, que é precisamente o que não existe.
**A estabilidade da trajetória é um diagnóstico, não um teste de substituição.** Se a substituição avançasse na mesma direção e no mesmo ritmo da difusão tecnológica, seria razoável esperar diferenciais progressivamente mais negativos. Essa previsão, porém, depende de algo que o desenho não observa: a adoção efetiva da tecnologia. Por isso, a forma da trajetória ajuda a organizar hipóteses, mas não permite aceitar ou rejeitar um mecanismo.
Nos quatro horizontes anuais do pós, os coeficientes permanecem próximos entre si. Em admissões, são −0,0523, −0,0522, −0,0535 e −0,0600. No salário real de admissão, são −0,0514, −0,0507, −0,0481 e −0,0548. Nos desligamentos, a diferença passa de −0,0382 para −0,0303. O padrão é compatível com uma diferença de nível persistente, que pode refletir a recuperação da pandemia, o ciclo macroeconômico, a difusão da IA ou uma combinação desses processos.
A estabilidade não prova ausência de substituição, assim como uma trajetória descendente não provaria causalidade com tendências prévias rejeitadas. Ela apenas não apresenta a aceleração que uma narrativa simples de substituição crescente faria esperar.
Os casos ocupacionais do Apêndice C também não exibem uma trajetória comum de piora. Entre desenvolvedores de software, as admissões dos doze meses terminais estão de 2% a 3% acima do patamar de novembro de 2022 nas faixas mais jovens e cerca de 14% e 21% acima entre 41 e 49 anos e acima de 50, com salário praticamente estável. No atendimento ao cliente, as admissões de trabalhadores de 22 a 25 anos ficam 23,5% abaixo da referência. Essas trajetórias são descritivas, não têm contrafactual e não identificam substituição, complementação ou qualquer outro mecanismo.
**O gradiente etário é relativo e não demonstra proteção.** O contraste entre grupos se torna mais positivo com a idade: em admissões, −0,019 entre 22 e 25 anos, −0,011 entre 26 e 30, +0,025 entre 31 e 34, +0,035 entre 35 e 40, +0,084 entre 41 e 49 e +0,066 acima de 50. Depois do ajuste de multiplicidade, apenas a faixa de 41 a 49 anos permanece significativa nos três desfechos de fluxo. Os contrastes da faixa de 22 a 25 anos não se distinguem de zero, com p ajustado entre 0,51 e 0,99.
Uma hipótese é que experiência, conhecimento tácito e julgamento acumulado favoreçam a complementação entre trabalhadores e tecnologia. Os dados, contudo, não identificam esse mecanismo. O contraste de 41 a 49 anos é positivo tanto em admissões quanto em desligamentos, e o saldo líquido não se distingue de zero. Além disso, as tendências prévias falham, e o mesmo gradiente é compatível com uma explicação cíclica, na qual a contratação de entrada se ajusta antes da retenção de quadros experientes. Portanto, o resultado registra uma diferença relativa entre faixas, não proteção, aumento do emprego ou benefício causado pela IA.
## 6.4 O que um efeito médio silencia
Os resultados agregados não estabelecem que haja substituição em curso no mercado formal brasileiro, mas também não demonstram sua ausência. Há uma limitação adicional: coeficientes médios ponderados por volume têm pouca sensibilidade a mudanças concentradas em ocupações pequenas.
Tradutores e intérpretes ilustram essa limitação. A família está classificada como exposta, com pontuação de 0,59, mas responde por **3.846 admissões formais nos vinte e três meses pré-tratamento, ou 0,041% da massa do grupo tratado**, na 57ª posição entre as 75 famílias tratadas. Sessenta das setenta e cinco famílias estão abaixo de 1% da massa e, juntas, somam 14,1% dela.
A consequência é aritmética: mesmo uma redução integral das admissões de tradutores e intérpretes moveria o coeficiente agregado em cerca de quatro centésimos de ponto percentual, diante de uma estimativa da ordem de −5%. Uma transformação intensa em uma ocupação pequena pode, portanto, permanecer quase invisível no resultado médio.
Isso não é defeito da estimação, mas uma propriedade do estimando. Relatos de transformação em ocupações específicas não são contraditos por esta análise. A dissertação responde a uma pergunta agregada e não resolve o que ocorreu em cada ocupação. Investigações sobre ocupações particulares exigem desenhos dedicados.
Uma interpretação possível é que ocupações sejam mais resistentes à substituição integral porque combinam tarefas cognitivas com coordenação social, negociação, autonomia, decisão sob responsabilidade e habilidades motoras ou espaciais. Nesse caso, uma tecnologia que executa parte das tarefas pode recompor o trabalho sem eliminar a ocupação. Os resultados são compatíveis com essa hipótese, mas não a distinguem de explicações cíclicas, mudanças de composição ou ausência de adoção relevante.
## 6.5 Balanço das escolhas de desenho
As duas escolhas estruturais, o índice da OIT como medida de exposição e o CAGED como fonte, se sustentam. Registro o que elas custam.
**Falta um índice brasileiro.** A lacuna mais séria é anterior a qualquer escolha minha: **o Brasil não tem um índice de exposição à inteligência artificial construído sobre suas próprias ocupações.** Um índice assim exigiria um catálogo estruturado das tarefas de cada ocupação brasileira, e a CBO traz um esboço disso em suas descrições, mas não em forma catalogada, granular e comparável. É essa ausência que obriga qualquer estudo brasileiro a importar uma medida estrangeira e a perder no caminho a granularidade que permitiria enxergar particularidades locais, inclusive as regionais.
**A correspondência entre classificações cobra um preço, e ele está reportado.** Das 629 famílias da CBO, 193 não recebem pontuação e 95 são de exposição mínima. Assim, **o contraste principal opera sobre 341 famílias, enquanto 288, ou 45,8% do total, ficam de fora**. Há também diluição nas correspondências de muitos para muitos, como na CBO 4121, cujos três destinos na ISCO-08 têm pontuações de 0,43, 0,65 e 0,70.
Ainda assim, o procedimento é defensável: a correspondência veio da tabela oficial do ministério, as regras foram declaradas antes da estimação e o caso 4121 foi verificado sob quatro formas de agregação, das quais três devolvem a mesma classificação. As três variantes pré-registradas alteram 8, 16 e 53 das 629 famílias sem reverter a leitura geral. Duas configurações alternativas pedem leitura cuidadosa, porque as duas são frequentemente lidas como enfraquecimento do resultado e nenhuma das duas o é. A medida contínua padronizada devolve −0,0188 por desvio-padrão de pontuação, e comparar esse número diretamente com os −0,0507 da especificação principal seria erro duplo. Primeiro, a especificação contínua dispensa o corte binário e por isso roda sobre 436 famílias, e não 341: seu comparável é o degrau que incorpora a exposição mínima ao controle, de −0,0456. Segundo, o coeficiente é por desvio-padrão, enquanto o contraste entre tratados e controle vale bem mais de um desvio: a pontuação média é de 0,471 no grupo tratado e 0,202 no controle, uma distância de 0,269 ponto. Reescalado à distância efetivamente estimada, o coeficiente contínuo fica na mesma ordem de magnitude do binário. A medida contínua, portanto, reproduz a especificação principal em vez de reduzi-la a um terço. A segunda configuração incorpora as 95 ocupações de exposição mínima ao controle, invertendo a escolha da subseção 4.2, e move três dos cinco desfechos: as admissões passam de −0,0538 (p = 0,164) para −0,0887 (p = 0,022), o fluxo bruto de −0,0481 (p = 0,174) para −0,0801 (p = 0,030) e os desligamentos de −0,0420 (p = 0,227) para −0,0707 (p = 0,056), enquanto salário e saldo praticamente não se movem. Registro o quadro completo porque a leitura importa: a especificação principal é a que não rejeita nos fluxos, e a razão para mantê-la é anterior ao resultado, pois um controle que inclui ocupações de pontuação média 0,329, acima do máximo de 0,32 do controle estrito, é um controle parcialmente exposto e comprime o contraste por construção. A escolha foi declarada antes da estimação e não é revista por causa do que produz.
**O CAGED foi a fonte certa.** É registro administrativo mensal, censitário sobre o mercado formal, com ocupação a quatro dígitos e acesso público, combinação que poucos países mantêm. Houve a tentação de privilegiar a PNAD Contínua, que se corresponde ao índice de forma mais direta, mas ela é trimestral e amostral e não observa a porta de entrada do emprego formal, que é onde procuro o ajuste. Usei-a onde é superior, no retrato distributivo da Seção 3 e no exercício de informalidade do Apêndice D. Pela mesma lógica preferi o índice da OIT a uma medida derivada da O\*NET: a O\*NET facilitaria a comparação com a literatura, mas está construída sobre a estrutura ocupacional americana, e a distância entre ela e a CBO é maior do que a distância entre a CBO e a ISCO-08, para a qual existe correspondência oficial brasileira.
## 6.6 Agenda de pesquisa
Seis caminhos me parecem os mais promissores, e quase todos decorrem das limitações e das interpretações acima.
**Medir adoção, e não apenas exposição.** Enquanto o uso efetivo de IA por firmas e trabalhadores brasileiros não for observado, a distinção entre potencial e realizado seguirá sendo a maior fragilidade desta literatura no país. Suplementos de pesquisas domiciliares, pesquisas de inovação e dados de firmas são rotas plausíveis. Não é só fechar uma lacuna descritiva: uma medida de intensidade de adoção mudaria o desenho, porque permitiria comparar quem adotou intensamente com quem não adotou e separar enfim o efeito da tecnologia do efeito do ciclo. É uma agenda inteira por si só.
**Acompanhar trabalhadores, e não ocupações.** Um painel de pessoa por período, com identificador estável e pesos longitudinais, permitiria estimar transições entre estados, de formal para informal e de ocupação exposta para não exposta, e responder à pergunta que esta dissertação só pode formular.
**Retomar a dimensão espacial com o obstáculo nomeado.** Investiguei se a capacidade digital local alterava a evolução das ocupações expostas e, conforme a subseção 4.5, interrompi o exercício depois que o diagnóstico mostrou variabilidade identificadora concentrada demais entre Unidades da Federação. Uma investigação futura precisa de uma fonte de variação em intensidade digital mais dispersa entre estados, ou de um desenho que não dependa de agrupamento estadual para a inferência.
**Estender o horizonte.** Se os ajustes de uma tecnologia de propósito geral se acumulam lentamente, a leitura correta destes resultados pode depender de dados que ainda não existem. Replicar este desenho com dois ou três anos a mais é barato e informativo, e o pacote de replicação foi construído para tornar isso direto. Parte desses dados já está a caminho: cada nova safra anual da RAIS acrescenta um ano inteiro a uma série que hoje tem apenas dois.
**Investigar ocupações particulares.** Pela aritmética da subseção 6.4, ocupações pequenas e intensamente expostas podem ser transformadas ou extintas sem deixar traço num coeficiente médio ponderado por volume. Estudos de caso com desenho próprio e amostra dimensionada ao tamanho da ocupação são o instrumento correto, e são complementares a este trabalho.
**Atacar o crosswalk com as ferramentas que esta dissertação estuda.** A correspondência entre classificações é feita hoje de código a código, e é aí que a informação se perde. Modelos de linguagem permitiriam, em princípio, uma correspondência semântica construída sobre as descrições de tarefa. A ideia é atraente e não é gratuita: exigiria validar a correspondência contra a oficial, medir sua estabilidade e demonstrar que ela remove mais erro do que introduz. Registro como agenda, e não como recomendação.
Encerro com a leitura que me parece mais defensável. Nos primeiros três anos após o ChatGPT, as estimativas não estabelecem um choque nacional no emprego formal das ocupações mais expostas à inteligência artificial. Elas registram diferenciais negativos e imprecisos nos fluxos e um diferencial mais preciso no salário de admissão, mas as tendências prévias falham e nenhum desses padrões está causalmente identificado. Este trabalho, portanto, não afirma que a inteligência artificial os produziu nem que sua ausência tenha sido demonstrada. Sua contribuição é oferecer uma medida de exposição adaptada ao país, um retrato de quem está sob ela, diagnósticos que delimitam o que os dados disponíveis podem e não podem responder e um ponto de partida documentado para quando houver mais tempo de observação e medidas de adoção.
## Apêndice A: Decomposição salarial, contrastes DDD e diagnósticos
Este apêndice reúne os diagnósticos do modelo nacional, a decomposição do diferencial salarial e os contrastes entre cada grupo e seu complemento, estimados por diferenças em diferenças triplas (DDD). Também apresenta os diagnósticos de tendências prévias, suporte amostral e tamanho das amostras. Os diagnósticos nacionais reportam p-valores convencionais. Nas tabelas de DDD, o p-valor nominal e o p-valor ajustado pelo procedimento de Benjamini–Hochberg aparecem lado a lado. Os diagnósticos de pretrend das heterogeneidades testam uma tendência linear no período anterior ao tratamento e, portanto, não correspondem ao teste conjunto do estudo de eventos nacional. As análises devem ser consideradas exploratórias, sobretudo quando o pretrend falha ou o suporte é classificado como insuficiente.
### A.1 Diagnósticos do modelo nacional
**Tabela A.1: Diagnósticos dos resultados médios nacionais**
Painel B.1: Estimativas DiD e diagnósticos dos desfechos principais
<table header-row="true">
<tr>
<td>Resultado</td>
<td>DiD nacional</td>
<td>p DiD</td>
<td>Pretrend</td>
<td>p pretrend</td>
<td>N</td>
<td>CBOs</td>
</tr>
<tr>
<td>Admissões (PPML, nível)</td>
<td>−0,0538\<br\>(0,0386)</td>
<td>0,164</td>
<td>fail</td>
<td>p\<0,001</td>
<td>22.049</td>
<td>341</td>
</tr>
<tr>
<td>Desligamentos (PPML, nível)</td>
<td>−0,0420\<br\>(0,0347)</td>
<td>0,227</td>
<td>fail</td>
<td>p\<0,001</td>
<td>22.049</td>
<td>341</td>
</tr>
<tr>
<td>Fluxo bruto (PPML, nível)</td>
<td>−0,0481\<br\>(0,0353)</td>
<td>0,174</td>
<td>fail</td>
<td>p\<0,001</td>
<td>22.049</td>
<td>341</td>
</tr>
<tr>
<td>Salário real de admissão (log)</td>
<td>−0,0507\*\*\*\<br\>(0,0103)</td>
<td>p\<0,001</td>
<td>fail</td>
<td>p=1,6e-04</td>
<td>22.012</td>
<td>341</td>
</tr>
<tr>
<td>Saldo líquido (asinh)</td>
<td>−0,5513\<br\>(0,3783)</td>
<td>0,146</td>
<td>fail</td>
<td>p\<0,001</td>
<td>22.049</td>
<td>341</td>
</tr>
</table>
Painel B.2: Proxy cumulativo de fluxo líquido
<table header-row="true">
<tr>
<td>Resultado</td>
<td>DiD nacional</td>
<td>p DiD</td>
<td>Pretrend</td>
<td>N</td>
<td>CBOs</td>
</tr>
<tr>
<td>Proxy cumulativo de fluxo líquido</td>
<td>1,4292\<br\>(1,3093)</td>
<td>0,276</td>
<td>not_available</td>
<td>22.100</td>
<td>340</td>
</tr>
</table>
Notas: as células do Painel B.1 apresentam o coeficiente e, entre parênteses, o erro-padrão clusterizado por CBO de quatro dígitos, com inferência baseada na distribuição t com G−1 graus de liberdade. \* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Admissões, desligamentos e fluxo bruto são estimados por PPML, e o coeficiente é semi-elasticidade da média condicional em nível, não log-log. O tratamento compara CBOs expostas nos gradientes da OIT a CBOs `Not Exposed`; `Minimal Exposure` não integra o controle principal. **Os cinco pretrends falham**, incluindo o do salário real de admissão, cujo teste conjunto tem p=1,6e-04 e 11 dos 22 leads individualmente significativos. O pretrend é o teste conjunto dos coeficientes mensais anteriores ao tratamento, estimado sobre o modelo exato do event study. `asinh(saldo)` aceita valores negativos e zero e não deve ser interpretado como percentual. O Painel B.2 substitui as duas construções alternativas do saldo por um índice cumulativo de fluxo líquido, normalizado pelo fluxo bruto pré-tratamento; **ele não observa o estoque de emprego** e não deve ser lido como tal. A validação contra o estoque observado na RAIS, descrita na Apêndice D, classifica o índice como concordante apenas em direção: todas as correlações estimáveis são positivas, mas a mediana de nível é 0,03 e a de variação é 0,11. Uma CBO é excluída do proxy por ter fluxo bruto pré-tratamento igual a zero. Os p-valores desta tabela são convencionais e não recebem correção por testes múltiplos, que se aplica às famílias de heterogeneidade do Apêndice A. N denota observações CBO-mês, não trabalhadores. Esta é a única tabela do trabalho que mantém um Painel B.2.
**Tabela A.1b — Sensibilidade a tendências prévias (Rambachan e Roth, 2023)**
<table header-row="true">
<tr>
<td>Desfecho</td>
<td>Estimativa (EP)</td>
<td>IC 95% original</td>
<td>Maior M com IC excluindo zero</td>
<td>Status em M = 0</td>
<td>Curvatura pré observada</td>
<td>Quebra abaixo da curvatura observada</td>
</tr>
<tr>
<td>Salário real de admissão (log)</td>
<td>−0,0154 (0,0122)</td>
<td>\[−0,0392; +0,0085\]</td>
<td>—</td>
<td>não robusto</td>
<td>0,0818</td>
<td>sim</td>
</tr>
<tr>
<td>Saldo líquido (asinh)</td>
<td>−3,3079 (0,7068)</td>
<td>\[−4,6931; −1,9227\]</td>
<td>0,05</td>
<td>robusto</td>
<td>2,9233</td>
<td>sim</td>
</tr>
</table>
> *Notas: método C-LF sobre 22 períodos pré e 24 pós, com grade de M de 0 a 2 em passos de 0,05. O estimando alvo é a média pós-tratamento do estudo de eventos normalizada a novembro de 2022, distinta do coeficiente estático da Tabela 5.1, que compara o pós à média de todo o pré-período. As duas primeiras colunas de M referem-se à restrição de variação relativa, que limita quanto o desvio de tendência pode mudar entre períodos consecutivos; as duas últimas, à restrição de suavidade, que limita sua curvatura. No salário, o intervalo já contém zero em M = 0, isto é, antes de se admitir qualquer violação de tendências paralelas, e os 12 pontos da grade de suavidade produzem intervalos não informativos. Nos dois desfechos, o ponto de quebra fica abaixo da curvatura pré-tratamento efetivamente observada. O procedimento cobre os dois desfechos estimados por MQO; os desfechos de contagem estimados por PPML não integram este quadro. Fonte: **`results/diagnostics/honest_did_summary.csv`**.*
**Tabela A.1c — Comparabilidade pré-tratamento entre tratados e controle**
<table header-row="true">
<tr>
<td>Indicador (jan/2021 a nov/2022)</td>
<td>Tratados (75 CBOs)</td>
<td>Controle (265 CBOs)</td>
</tr>
<tr>
<td>Admissões no período</td>
<td>9.443.185</td>
<td>17.351.605</td>
</tr>
<tr>
<td>Admissões médias mensais</td>
<td>410.573</td>
<td>754.418</td>
</tr>
<tr>
<td>Participação com ensino superior</td>
<td>19,7%</td>
<td>4,0%</td>
</tr>
<tr>
<td>Salário real médio de admissão</td>
<td>R\$ 2.300,58</td>
<td>R\$ 1.962,51</td>
</tr>
<tr>
<td>Idade média dos admitidos</td>
<td>28,9</td>
<td>33,8</td>
</tr>
<tr>
<td>Crescimento mensal médio</td>
<td>0,38%</td>
<td>0,44%</td>
</tr>
<tr>
<td>Desvio-padrão do crescimento mensal</td>
<td>8,3%</td>
<td>14,0%</td>
</tr>
<tr>
<td>Amplitude sazonal</td>
<td>27,3%</td>
<td>44,7%</td>
</tr>
</table>
> *Notas: a tabela não é um teste de balanceamento no sentido experimental, porque o desenho não randomiza; ela documenta quanto os dois grupos já diferiam antes do evento. A razão de quase cinco para um na participação de ensino superior, somada às diferenças de idade, salário e sazonalidade, indica que o contraste opera entre estruturas ocupacionais distintas, e não entre o mesmo tipo de trabalho sob exposições diferentes. É esse fato que sustenta a discussão da subseção 6.3 sobre a coincidência entre a fronteira do índice e a fronteira entre trabalho de escritório e trabalho não-escritório, e ajuda a explicar a rejeição sistemática das tendências paralelas. Fonte: **`results/audit/d1_pre_period_comparability.csv`**.*
### A.2 Decomposição do diferencial salarial e composição dos admitidos
Esta seção apresenta os cálculos usados para avaliar quanto do diferencial do salário real de admissão está associado à mudança no perfil dos novos contratados. O exercício não identifica um mecanismo causal. Ele organiza o diferencial observado em uma parcela estimada dentro dos grupos e outra associada à composição dos admitidos.
Primeiro, calculamos a participação de cada faixa de escolaridade no total de admissões antes e depois de dezembro de 2022, separadamente para ocupações expostas e não expostas.
**Tabela A.2.1: Mudança na composição educacional dos admitidos**
<table fit-page-width="true" header-row="true">
<tr>
<td>Faixa de escolaridade</td>
<td>Expostas: pré</td>
<td>Expostas: pós</td>
<td>Mudança expostas</td>
<td>Não expostas: pré</td>
<td>Não expostas: pós</td>
<td>Mudança não expostas</td>
<td>Diferença das mudanças</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>3,47%</td>
<td>3,39%</td>
<td>−0,09 p.p.</td>
<td>27,06%</td>
<td>24,21%</td>
<td>−2,85 p.p.</td>
<td>+2,76 p.p.</td>
</tr>
<tr>
<td>Ensino médio</td>
<td>66,63%</td>
<td>69,54%</td>
<td>+2,91 p.p.</td>
<td>67,56%</td>
<td>70,55%</td>
<td>+2,99 p.p.</td>
<td>−0,07 p.p.</td>
</tr>
<tr>
<td>Ensino superior</td>
<td>29,90%</td>
<td>27,07%</td>
<td>−2,83 p.p.</td>
<td>5,38%</td>
<td>5,24%</td>
<td>−0,14 p.p.</td>
<td>−2,69 p.p.</td>
</tr>
</table>
> *Notas: as participações são ponderadas pelo número de admissões. O pré-período vai de janeiro de 2021 a novembro de 2022, e o pós-período vai de dezembro de 2022 a maio de 2026. A diferença das mudanças corresponde à variação nas ocupações expostas menos a variação nas não expostas. Fonte: \`results/audit/a1_education_composition_shift.csv\`.*
No primeiro método, ponderamos o diferencial salarial estimado dentro de cada faixa de escolaridade pela participação dessa faixa nas admissões das ocupações expostas antes do evento:
$$
\widehat{\beta}_{\text{dentro}}=\sum_g s_{g,\text{expostas},\text{pré}}\widehat{\beta}_g=-0,03924
$$
O diferencial agregado é −0,05074. A diferença entre o resultado agregado e o componente ponderado dentro das faixas é −0,01150. Em valor absoluto, essa diferença corresponde a 22,66% do resultado agregado. Esse cálculo é uma aproximação, e não uma identidade de Oaxaca, porque os modelos de cada faixa educacional possuem seus próprios efeitos fixos.
O segundo método compara o resultado agregado com uma especificação que interage o período posterior com quatro características das ocupações medidas antes do evento: idade média dos admitidos, participação feminina, participação com ensino superior e participação negra. Nessa especificação, o diferencial salarial é −0,035998. A diferença em relação ao resultado agregado é −0,014743, equivalente a 29,06%. Esse segundo número captura a composição demográfica conjunta e não pode ser atribuído exclusivamente à escolaridade.
**Tabela A.2.2: Decomposição do diferencial salarial**
<table fit-page-width="true" header-row="true">
<tr>
<td>Método</td>
<td>Diferencial agregado</td>
<td>Resultado após decomposição ou ajuste</td>
<td>Parcela associada à composição</td>
<td>Participação do agregado</td>
<td>Escopo</td>
</tr>
<tr>
<td>Ponderação por escolaridade</td>
<td>−0,05074</td>
<td>−0,03924</td>
<td>−0,01150</td>
<td>22,66%</td>
<td>Composição educacional</td>
</tr>
<tr>
<td>Características anteriores ao evento</td>
<td>−0,05074</td>
<td>−0,035998</td>
<td>−0,014743</td>
<td>29,06%</td>
<td>Escolaridade, idade, sexo e raça em conjunto</td>
</tr>
</table>
> *Notas: os coeficientes salariais estão em pontos log e são interpretados como variações percentuais aproximadas. No primeiro método, a parcela associada à composição é a diferença entre o diferencial agregado e a média ponderada dos diferenciais dentro das faixas educacionais. No segundo, é a diferença entre a especificação agregada e aquela que inclui as interações com características anteriores ao evento. Fonte: \`results/audit/a_wage_composition_summary.json\` e \`results/audit/a2_wage_price_composition_split.csv\`.*
Como checagem complementar, o diferencial estimado para o salário mensal é −0,05074, para o salário-hora é −0,06951 e para as horas semanais é +0,00155. O resultado das horas não sugere que uma redução da jornada explique a queda do salário mensal.
O conjunto dos resultados é compatível com a hipótese de uma redução relativa das oportunidades de entrada para trabalhadores com ensino superior nas ocupações expostas. Essa leitura permanece exploratória: as pré-tendências falham e a medida de exposição não observa diretamente a adoção de IA pelas empresas. Portanto, os cálculos não permitem atribuir a mudança à IA nem demonstrar uma perda de poder de barganha.
### A.3 Sexo
**Tabela A.3.1 — Contrastes DDD completos: sexo**
<table header-row="true">
<tr>
<td>Grupo (família)</td>
<td>Resultado</td>
<td>DDD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo / DDD</td>
<td>N estático DDD</td>
<td>N evento grupo / DDD</td>
<td>CBOs alvo T/C · suporte</td>
<td>MDE 80% grupo / DDD</td>
</tr>
<tr>
<td>Homens (A)</td>
<td>Admissões</td>
<td>0,0116 (0,0466)</td>
<td>0,803 / 0,907</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31861</td>
<td>75/266 · adequate</td>
<td>0,0765 / 0,1309</td>
</tr>
<tr>
<td>Homens (A)</td>
<td>Desligamentos</td>
<td>0,0332 (0,0390)</td>
<td>0,395 / 0,581</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0685 / 0,1096</td>
</tr>
<tr>
<td>Homens (A)</td>
<td>Fluxo bruto</td>
<td>0,0216 (0,0420)</td>
<td>0,607 / 0,742</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0655 / 0,1179</td>
</tr>
<tr>
<td>Homens (A)</td>
<td>Salário real (log)</td>
<td>0,0022 (0,0100)</td>
<td>0,824 / 0,907</td>
<td>falha / falha</td>
<td>43292</td>
<td>15867 / 31285</td>
<td>75/266 · adequate</td>
<td>0,0342 / 0,0281</td>
</tr>
<tr>
<td>Homens (A)</td>
<td>Saldo (asinh)</td>
<td>0,7989\*\*\* (0,2145)</td>
<td>\<0,001 / 0,003</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,9649 / 0,6027</td>
</tr>
<tr>
<td>Mulheres (A)</td>
<td>Admissões</td>
<td>−0,0116 (0,0466)</td>
<td>0,803 / 0,907</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/266 · adequate</td>
<td>0,1302 / 0,1309</td>
</tr>
<tr>
<td>Mulheres (A)</td>
<td>Desligamentos</td>
<td>−0,0332 (0,0390)</td>
<td>0,395 / 0,581</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1043 / 0,1096</td>
</tr>
<tr>
<td>Mulheres (A)</td>
<td>Fluxo bruto</td>
<td>−0,0216 (0,0420)</td>
<td>0,607 / 0,742</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1142 / 0,1179</td>
</tr>
<tr>
<td>Mulheres (A)</td>
<td>Salário real (log)</td>
<td>−0,0022 (0,0100)</td>
<td>0,824 / 0,907</td>
<td>falha / falha</td>
<td>43292</td>
<td>15418 / 31285</td>
<td>75/266 · adequate</td>
<td>0,0329 / 0,0281</td>
</tr>
<tr>
<td>Mulheres (A)</td>
<td>Saldo (asinh)</td>
<td>−0,7989\*\*\* (0,2145)</td>
<td>\<0,001 / 0,003</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,8472 / 0,6027</td>
</tr>
</table>
> Notas: cada DDD compara o grupo-alvo com seu complemento, preservando p nominal, p BH e famílias A (100 testes) e B (30). N estático DDD vem do modelo estático; N evento discrimina a amostra do diagnóstico dentro do grupo e a do diagnóstico DDD. CBOs T/C referem-se ao suporte do grupo-alvo, não ao número total de clusters do DDD. MDE informa separadamente o mínimo detectável a 80% de poder no grupo e no DDD. Estrelas usam p BH: \* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Falha, alerta e diagnóstico indefinido não autorizam interpretação causal. Saldo em asinh não tem leitura percentual. Fonte: ddd_multiplicity_results.csv, ddd_alternative_partitions.csv e seus diagnósticos.
**Tabela A.3.2 — DiDs dentro dos grupos: sexo**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo</td>
<td>N</td>
<td>CBOs T/C · suporte</td>
</tr>
<tr>
<td>Homens</td>
<td>Admissões</td>
<td>−0,0779\*\* (0,0272)</td>
<td>0,004 / 0,019</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Homens</td>
<td>Desligamentos</td>
<td>−0,0635\*\* (0,0244)</td>
<td>0,010 / 0,034</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Homens</td>
<td>Fluxo bruto</td>
<td>−0,0710\*\* (0,0233)</td>
<td>0,003 / 0,011</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Homens</td>
<td>Salário real (log)</td>
<td>−0,0501\*\*\* (0,0122)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15867</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Homens</td>
<td>Saldo (asinh)</td>
<td>−0,2451 (0,3434)</td>
<td>0,476 / 0,582</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Admissões</td>
<td>−0,0724 (0,0464)</td>
<td>0,119 / 0,228</td>
<td>falha</td>
<td>15926</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Desligamentos</td>
<td>−0,0776\* (0,0371)</td>
<td>0,037 / 0,095</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Fluxo bruto</td>
<td>−0,0744 (0,0407)</td>
<td>0,068 / 0,158</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Salário real (log)</td>
<td>−0,0491\*\*\* (0,0117)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15418</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Mulheres</td>
<td>Saldo (asinh)</td>
<td>−1,0188\*\*\* (0,3015)</td>
<td>\<0,001 / 0,004</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
</table>
> Notas: DiD dentro do próprio grupo, janela balanceada −23 a +23, com referência em novembro de 2022 e erros agrupados por CBO. A família C contém 130 testes e seu ajuste BH foi preservado integralmente. Estas linhas não testam diferenças entre subgrupos. Os DDDs respondem a essa outra pergunta. Fonte: group_did_results.csv. O suporte e o diagnóstico de pré-tendências são parte do resultado.
Homens e mulheres apresentam orientações opostas do mesmo contraste. A rejeição ajustada no saldo é preservada e não deve ser contada como dois achados substantivos. As pré-tendências DDD falham.
**Figura A.3.1 — Admissões: perfis mensais por sexo**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/9c505293-ca21-4df3-bf2f-2b7376ee6068/figure_A_3_1_sex_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=da020ff308ac0a084ed82dd38414a23d60699588856e1f88c354f221ea019cf6&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.3.2 — Salário real de admissão: perfis mensais por sexo**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/dcc5a720-cd92-414d-9946-0a8b3f2376e6/figure_A_3_2_sex_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=7b9bf383053450b03dde52d8a30dc5ffcf802c8f8606289bce5924c09aa2302f&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
> Figuras: séries estendidas de −23 a +41, relativas a novembro de 2022; bandas de 95%, linhas horizontais na média dos coeficientes pré e linha vertical pontilhada em +23. Os testes das tabelas usam −23 a +23. A numeração foi atualizada com os mesmos coeficientes, intervalos e convenções; as imagens anteriores estão preservadas na cópia local da V4.
### A.4 Raça/cor
**Tabela A.4.1 — Contrastes DDD completos: raça/cor**
<table header-row="true">
<tr>
<td>Grupo (família)</td>
<td>Resultado</td>
<td>DDD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo / DDD</td>
<td>N estático DDD</td>
<td>N evento grupo / DDD</td>
<td>CBOs alvo T/C · suporte</td>
<td>MDE 80% grupo / DDD</td>
</tr>
<tr>
<td>Branca (A)</td>
<td>Admissões</td>
<td>0,0827\*\*\* (0,0188)</td>
<td>\<0,001 / \<0,001</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0982 / 0,0529</td>
</tr>
<tr>
<td>Branca (A)</td>
<td>Desligamentos</td>
<td>0,0651\*\*\* (0,0136)</td>
<td>\<0,001 / \<0,001</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0703 / 0,0382</td>
</tr>
<tr>
<td>Branca (A)</td>
<td>Fluxo bruto</td>
<td>0,0743\*\*\* (0,0144)</td>
<td>\<0,001 / \<0,001</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0794 / 0,0405</td>
</tr>
<tr>
<td>Branca (A)</td>
<td>Salário real (log)</td>
<td>−0,0080 (0,0088)</td>
<td>0,361 / 0,556</td>
<td>falha / falha</td>
<td>43858</td>
<td>15802 / 31687</td>
<td>75/266 · adequate</td>
<td>0,0320 / 0,0246</td>
</tr>
<tr>
<td>Branca (A)</td>
<td>Saldo (asinh)</td>
<td>0,7390\*\* (0,2544)</td>
<td>0,004 / 0,026</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,8436 / 0,7149</td>
</tr>
<tr>
<td>Preta (A)</td>
<td>Admissões</td>
<td>−0,0088 (0,0399)</td>
<td>0,825 / 0,907</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,1517 / 0,1122</td>
</tr>
<tr>
<td>Preta (A)</td>
<td>Desligamentos</td>
<td>0,0445 (0,0309)</td>
<td>0,150 / 0,341</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,1222 / 0,0867</td>
</tr>
<tr>
<td>Preta (A)</td>
<td>Fluxo bruto</td>
<td>0,0160 (0,0356)</td>
<td>0,653 / 0,787</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,1346 / 0,1000</td>
</tr>
<tr>
<td>Preta (A)</td>
<td>Salário real (log)</td>
<td>−0,0052 (0,0101)</td>
<td>0,608 / 0,742</td>
<td>falha / falha</td>
<td>42779</td>
<td>14922 / 30827</td>
<td>75/265 · adequate</td>
<td>0,0343 / 0,0283</td>
</tr>
<tr>
<td>Preta (A)</td>
<td>Saldo (asinh)</td>
<td>0,2580 (0,2821)</td>
<td>0,361 / 0,556</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/265 · adequate</td>
<td>0,4386 / 0,7925</td>
</tr>
<tr>
<td>Parda (A)</td>
<td>Admissões</td>
<td>−0,0817\*\* (0,0304)</td>
<td>0,008 / 0,042</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1233 / 0,0853</td>
</tr>
<tr>
<td>Parda (A)</td>
<td>Desligamentos</td>
<td>−0,0886\*\* (0,0292)</td>
<td>0,003 / 0,018</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1120 / 0,0820</td>
</tr>
<tr>
<td>Parda (A)</td>
<td>Fluxo bruto</td>
<td>−0,0848\*\* (0,0293)</td>
<td>0,004 / 0,026</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1151 / 0,0824</td>
</tr>
<tr>
<td>Parda (A)</td>
<td>Salário real (log)</td>
<td>−0,0102 (0,0092)</td>
<td>0,270 / 0,465</td>
<td>falha / não rejeitada</td>
<td>43856</td>
<td>15804 / 31679</td>
<td>75/266 · adequate</td>
<td>0,0276 / 0,0258</td>
</tr>
<tr>
<td>Parda (A)</td>
<td>Saldo (asinh)</td>
<td>0,1655 (0,2834)</td>
<td>0,560 / 0,708</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,7276 / 0,7964</td>
</tr>
<tr>
<td>Amarela (A)</td>
<td>Admissões</td>
<td>−0,2770\*\*\* (0,0576)</td>
<td>\<0,001 / \<0,001</td>
<td>falha / falha</td>
<td>44098</td>
<td>15832 / 31767</td>
<td>75/264 · adequate</td>
<td>0,2262 / 0,1619</td>
</tr>
<tr>
<td>Amarela (A)</td>
<td>Desligamentos</td>
<td>−0,2179\*\*\* (0,0365)</td>
<td>\<0,001 / \<0,001</td>
<td>falha / falha</td>
<td>44098</td>
<td>15832 / 31767</td>
<td>75/264 · adequate</td>
<td>0,1564 / 0,1025</td>
</tr>
<tr>
<td>Amarela (A)</td>
<td>Fluxo bruto</td>
<td>−0,2487\*\*\* (0,0466)</td>
<td>\<0,001 / \<0,001</td>
<td>falha / falha</td>
<td>44098</td>
<td>15879 / 31814</td>
<td>75/264 · adequate</td>
<td>0,1901 / 0,1310</td>
</tr>
<tr>
<td>Amarela (A)</td>
<td>Salário real (log)</td>
<td>−0,0171 (0,0150)</td>
<td>0,254 / 0,454</td>
<td>falha / alerta</td>
<td>37931</td>
<td>11300 / 27207</td>
<td>75/264 · adequate</td>
<td>0,0486 / 0,0421</td>
</tr>
<tr>
<td>Amarela (A)</td>
<td>Saldo (asinh)</td>
<td>0,3108 (0,3305)</td>
<td>0,348 / 0,552</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/264 · adequate</td>
<td>0,2746 / 0,9286</td>
</tr>
<tr>
<td>Indígena (A)</td>
<td>Admissões</td>
<td>−0,1744 (0,1003)</td>
<td>0,083 / 0,218</td>
<td>falha / falha</td>
<td>44098</td>
<td>15040 / 30975</td>
<td>73/259 · adequate</td>
<td>0,2502 / 0,2817</td>
</tr>
<tr>
<td>Indígena (A)</td>
<td>Desligamentos</td>
<td>−0,1172 (0,1140)</td>
<td>0,305 / 0,507</td>
<td>falha / falha</td>
<td>44098</td>
<td>15185 / 31120</td>
<td>73/259 · adequate</td>
<td>0,1926 / 0,3204</td>
</tr>
<tr>
<td>Indígena (A)</td>
<td>Fluxo bruto</td>
<td>−0,1455 (0,1049)</td>
<td>0,166 / 0,370</td>
<td>falha / falha</td>
<td>44098</td>
<td>15420 / 31355</td>
<td>73/259 · adequate</td>
<td>0,2178 / 0,2948</td>
</tr>
<tr>
<td>Indígena (A)</td>
<td>Salário real (log)</td>
<td>−0,0036 (0,0178)</td>
<td>0,838 / 0,910</td>
<td>não rejeitada / não rejeitada</td>
<td>33908</td>
<td>8228 / 24135</td>
<td>73/259 · adequate</td>
<td>0,0473 / 0,0499</td>
</tr>
<tr>
<td>Indígena (A)</td>
<td>Saldo (asinh)</td>
<td>0,3605 (0,3540)</td>
<td>0,309 / 0,507</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>73/259 · adequate</td>
<td>0,1849 / 0,9945</td>
</tr>
<tr>
<td>Não identificada (A)</td>
<td>Admissões</td>
<td>0,0197 (0,0300)</td>
<td>0,510 / 0,681</td>
<td>falha / falha</td>
<td>44098</td>
<td>15931 / 31866</td>
<td>75/266 · adequate</td>
<td>0,0675 / 0,0842</td>
</tr>
<tr>
<td>Não identificada (A)</td>
<td>Desligamentos</td>
<td>0,0541 (0,0263)</td>
<td>0,040 / 0,126</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/266 · adequate</td>
<td>0,0790 / 0,0739</td>
</tr>
<tr>
<td>Não identificada (A)</td>
<td>Fluxo bruto</td>
<td>0,0376 (0,0278)</td>
<td>0,176 / 0,375</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0666 / 0,0781</td>
</tr>
<tr>
<td>Não identificada (A)</td>
<td>Salário real (log)</td>
<td>0,0415\*\*\* (0,0107)</td>
<td>\<0,001 / 0,002</td>
<td>alerta / falha</td>
<td>37155</td>
<td>14437 / 30327</td>
<td>75/266 · adequate</td>
<td>0,0320 / 0,0301</td>
</tr>
<tr>
<td>Não identificada (A)</td>
<td>Saldo (asinh)</td>
<td>−0,9754 (0,4922)</td>
<td>0,048 / 0,142</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>1,0994 / 1,3828</td>
</tr>
<tr>
<td>Negra (preta e parda) (B)</td>
<td>Admissões</td>
<td>−0,1144\*\* (0,0346)</td>
<td>0,001 / 0,015</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1253 / 0,0972</td>
</tr>
<tr>
<td>Negra (preta e parda) (B)</td>
<td>Desligamentos</td>
<td>−0,0990\*\* (0,0310)</td>
<td>0,002 / 0,015</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1112 / 0,0870</td>
</tr>
<tr>
<td>Negra (preta e parda) (B)</td>
<td>Fluxo bruto</td>
<td>−0,1068\*\* (0,0325)</td>
<td>0,001 / 0,015</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1158 / 0,0914</td>
</tr>
<tr>
<td>Negra (preta e parda) (B)</td>
<td>Salário real (log)</td>
<td>−0,0121 (0,0084)</td>
<td>0,148 / 0,399</td>
<td>falha / não rejeitada</td>
<td>43865</td>
<td>15825 / 31691</td>
<td>75/266 · adequate</td>
<td>0,0289 / 0,0235</td>
</tr>
<tr>
<td>Negra (preta e parda) (B)</td>
<td>Saldo (asinh)</td>
<td>0,0101 (0,2980)</td>
<td>0,973 / 0,973</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,7376 / 0,8373</td>
</tr>
</table>
> Notas: cada DDD compara o grupo-alvo com seu complemento, preservando p nominal, p BH e famílias A (100 testes) e B (30). N estático DDD vem do modelo estático; N evento discrimina a amostra do diagnóstico dentro do grupo e a do diagnóstico DDD. CBOs T/C referem-se ao suporte do grupo-alvo, não ao número total de clusters do DDD. MDE informa separadamente o mínimo detectável a 80% de poder no grupo e no DDD. Estrelas usam p BH: \* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Falha, alerta e diagnóstico indefinido não autorizam interpretação causal. Saldo em asinh não tem leitura percentual. Fonte: ddd_multiplicity_results.csv, ddd_alternative_partitions.csv e seus diagnósticos.
**Tabela A.4.2 — DiDs dentro dos grupos: raça/cor**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo</td>
<td>N</td>
<td>CBOs T/C · suporte</td>
</tr>
<tr>
<td>Branca</td>
<td>Admissões</td>
<td>−0,0241 (0,0350)</td>
<td>0,491 / 0,592</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Branca</td>
<td>Desligamentos</td>
<td>−0,0182 (0,0250)</td>
<td>0,468 / 0,579</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Branca</td>
<td>Fluxo bruto</td>
<td>−0,0212 (0,0283)</td>
<td>0,453 / 0,569</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Branca</td>
<td>Salário real (log)</td>
<td>−0,0544\*\*\* (0,0114)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15802</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Branca</td>
<td>Saldo (asinh)</td>
<td>−0,2246 (0,3002)</td>
<td>0,455 / 0,569</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Preta</td>
<td>Admissões</td>
<td>−0,0383 (0,0540)</td>
<td>0,479 / 0,582</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>Preta</td>
<td>Desligamentos</td>
<td>0,0092 (0,0435)</td>
<td>0,832 / 0,859</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>Preta</td>
<td>Fluxo bruto</td>
<td>−0,0160 (0,0479)</td>
<td>0,739 / 0,785</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>Preta</td>
<td>Salário real (log)</td>
<td>−0,0492\*\*\* (0,0122)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>14922</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>Preta</td>
<td>Saldo (asinh)</td>
<td>−0,2001 (0,1561)</td>
<td>0,201 / 0,297</td>
<td>falha</td>
<td>15935</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>Parda</td>
<td>Admissões</td>
<td>−0,0663 (0,0439)</td>
<td>0,132 / 0,244</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Parda</td>
<td>Desligamentos</td>
<td>−0,0700 (0,0399)</td>
<td>0,080 / 0,171</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Parda</td>
<td>Fluxo bruto</td>
<td>−0,0680 (0,0410)</td>
<td>0,098 / 0,198</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Parda</td>
<td>Salário real (log)</td>
<td>−0,0502\*\*\* (0,0098)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15804</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Parda</td>
<td>Saldo (asinh)</td>
<td>−0,2841 (0,2590)</td>
<td>0,273 / 0,382</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Amarela</td>
<td>Admissões</td>
<td>−0,3479\*\*\* (0,0805)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15832</td>
<td>75/264 · adequate</td>
</tr>
<tr>
<td>Amarela</td>
<td>Desligamentos</td>
<td>−0,2722\*\*\* (0,0556)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15832</td>
<td>75/264 · adequate</td>
</tr>
<tr>
<td>Amarela</td>
<td>Fluxo bruto</td>
<td>−0,3120\*\*\* (0,0676)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15879</td>
<td>75/264 · adequate</td>
</tr>
<tr>
<td>Amarela</td>
<td>Salário real (log)</td>
<td>−0,0706\*\*\* (0,0173)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>11300</td>
<td>75/264 · adequate</td>
</tr>
<tr>
<td>Amarela</td>
<td>Saldo (asinh)</td>
<td>−0,1612 (0,0977)</td>
<td>0,100 / 0,200</td>
<td>falha</td>
<td>15935</td>
<td>75/264 · adequate</td>
</tr>
<tr>
<td>Indígena</td>
<td>Admissões</td>
<td>−0,1105 (0,0890)</td>
<td>0,215 / 0,308</td>
<td>falha</td>
<td>15040</td>
<td>73/259 · adequate</td>
</tr>
<tr>
<td>Indígena</td>
<td>Desligamentos</td>
<td>−0,0387 (0,0685)</td>
<td>0,573 / 0,659</td>
<td>falha</td>
<td>15185</td>
<td>73/259 · adequate</td>
</tr>
<tr>
<td>Indígena</td>
<td>Fluxo bruto</td>
<td>−0,0759 (0,0775)</td>
<td>0,328 / 0,435</td>
<td>falha</td>
<td>15420</td>
<td>73/259 · adequate</td>
</tr>
<tr>
<td>Indígena</td>
<td>Salário real (log)</td>
<td>−0,0549\*\*\* (0,0168)</td>
<td>0,001 / 0,006</td>
<td>não rejeitada</td>
<td>8228</td>
<td>73/259 · adequate</td>
</tr>
<tr>
<td>Indígena</td>
<td>Saldo (asinh)</td>
<td>−0,1829\*\* (0,0658)</td>
<td>0,006 / 0,021</td>
<td>falha</td>
<td>15935</td>
<td>73/259 · adequate</td>
</tr>
<tr>
<td>Não identificada</td>
<td>Admissões</td>
<td>−0,0506\* (0,0240)</td>
<td>0,036 / 0,095</td>
<td>falha</td>
<td>15931</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Não identificada</td>
<td>Desligamentos</td>
<td>−0,0175 (0,0281)</td>
<td>0,535 / 0,632</td>
<td>falha</td>
<td>15926</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Não identificada</td>
<td>Fluxo bruto</td>
<td>−0,0344 (0,0237)</td>
<td>0,148 / 0,246</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Não identificada</td>
<td>Salário real (log)</td>
<td>−0,0264\* (0,0114)</td>
<td>0,021 / 0,063</td>
<td>alerta</td>
<td>14437</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Não identificada</td>
<td>Saldo (asinh)</td>
<td>−1,1142\*\* (0,3913)</td>
<td>0,005 / 0,019</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Admissões</td>
<td>−0,0621 (0,0446)</td>
<td>0,164 / 0,261</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Desligamentos</td>
<td>−0,0584 (0,0396)</td>
<td>0,141 / 0,244</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Fluxo bruto</td>
<td>−0,0604 (0,0412)</td>
<td>0,144 / 0,244</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Salário real (log)</td>
<td>−0,0513\*\*\* (0,0103)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15825</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Negra (preta e parda)</td>
<td>Saldo (asinh)</td>
<td>−0,3264 (0,2625)</td>
<td>0,215 / 0,308</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
</table>
> Notas: DiD dentro do próprio grupo, janela balanceada −23 a +23, com referência em novembro de 2022 e erros agrupados por CBO. A família C contém 130 testes e seu ajuste BH foi preservado integralmente. Estas linhas não testam diferenças entre subgrupos. Os DDDs respondem a essa outra pergunta. Fonte: group_did_results.csv. O suporte e o diagnóstico de pré-tendências são parte do resultado.
O agregado Negra pertence à família B; as seis categorias separadas pertencem à família A. Os complementos mudam entre as comparações. O DDD salarial da categoria não identificada é uma das duas rejeições salariais ajustadas da família A, mas não representa uma categoria racial substantiva.
**Figura A.4.1 — Admissões: perfis mensais por raça/cor**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/45c88744-6e64-4fa3-a01d-0c8f8c82d9c6/figure_A_4_1_race_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=a1e0ad184390c8b2933beb35ef75290c4af8ce6fbfd96fb434c00599163a5c0c&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.4.2 — Salário real de admissão: perfis mensais por raça/cor**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/7b85f792-a0f8-40cc-9b72-6e529342c14e/figure_A_4_2_race_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=eb4ecee9247dfb0f571ad0eb4d868164b6fd5b32ac6280ba6f66108adeedc3b4&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
> Figuras: séries estendidas de −23 a +41, relativas a novembro de 2022; bandas de 95%, linhas horizontais na média dos coeficientes pré e linha vertical pontilhada em +23. Os testes das tabelas usam −23 a +23. A numeração foi atualizada com os mesmos coeficientes, intervalos e convenções; as imagens anteriores estão preservadas na cópia local da V4.
### A.5 Idade
**Tabela A.5.1 — Contrastes DDD completos: idade**
<table header-row="true">
<tr>
<td>Grupo (família)</td>
<td>Resultado</td>
<td>DDD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo / DDD</td>
<td>N estático DDD</td>
<td>N evento grupo / DDD</td>
<td>CBOs alvo T/C · suporte</td>
<td>MDE 80% grupo / DDD</td>
</tr>
<tr>
<td>22–25 (A)</td>
<td>Admissões</td>
<td>−0,0189 (0,0269)</td>
<td>0,482 / 0,652</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,0905 / 0,0756</td>
</tr>
<tr>
<td>22–25 (A)</td>
<td>Desligamentos</td>
<td>0,0002 (0,0367)</td>
<td>0,995 / 0,995</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,1010 / 0,1030</td>
</tr>
<tr>
<td>22–25 (A)</td>
<td>Fluxo bruto</td>
<td>−0,0107 (0,0302)</td>
<td>0,723 / 0,850</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,0872 / 0,0849</td>
</tr>
<tr>
<td>22–25 (A)</td>
<td>Salário real (log)</td>
<td>−0,0004 (0,0083)</td>
<td>0,964 / 0,974</td>
<td>não rejeitada / falha</td>
<td>43508</td>
<td>15554 / 31453</td>
<td>75/265 · adequate</td>
<td>0,0294 / 0,0234</td>
</tr>
<tr>
<td>22–25 (A)</td>
<td>Saldo (asinh)</td>
<td>0,4145 (0,4033)</td>
<td>0,305 / 0,507</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/265 · adequate</td>
<td>0,6972 / 1,1332</td>
</tr>
<tr>
<td>26–30 (A)</td>
<td>Admissões</td>
<td>−0,0105 (0,0139)</td>
<td>0,450 / 0,616</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0877 / 0,0390</td>
</tr>
<tr>
<td>26–30 (A)</td>
<td>Desligamentos</td>
<td>−0,0125 (0,0113)</td>
<td>0,266 / 0,465</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0751 / 0,0317</td>
</tr>
<tr>
<td>26–30 (A)</td>
<td>Fluxo bruto</td>
<td>−0,0115 (0,0116)</td>
<td>0,323 / 0,522</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0739 / 0,0327</td>
</tr>
<tr>
<td>26–30 (A)</td>
<td>Salário real (log)</td>
<td>0,0070 (0,0081)</td>
<td>0,388 / 0,581</td>
<td>falha / falha</td>
<td>43707</td>
<td>15708 / 31597</td>
<td>75/266 · adequate</td>
<td>0,0295 / 0,0227</td>
</tr>
<tr>
<td>26–30 (A)</td>
<td>Saldo (asinh)</td>
<td>0,2284 (0,1840)</td>
<td>0,215 / 0,418</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,8193 / 0,5168</td>
</tr>
<tr>
<td>31–34 (A)</td>
<td>Admissões</td>
<td>0,0253 (0,0122)</td>
<td>0,038 / 0,125</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0888 / 0,0342</td>
</tr>
<tr>
<td>31–34 (A)</td>
<td>Desligamentos</td>
<td>0,0202 (0,0121)</td>
<td>0,097 / 0,245</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0706 / 0,0341</td>
</tr>
<tr>
<td>31–34 (A)</td>
<td>Fluxo bruto</td>
<td>0,0231 (0,0115)</td>
<td>0,046 / 0,139</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0734 / 0,0324</td>
</tr>
<tr>
<td>31–34 (A)</td>
<td>Salário real (log)</td>
<td>−0,0105 (0,0070)</td>
<td>0,135 / 0,325</td>
<td>falha / falha</td>
<td>43505</td>
<td>15561 / 31460</td>
<td>75/266 · adequate</td>
<td>0,0329 / 0,0196</td>
</tr>
<tr>
<td>31–34 (A)</td>
<td>Saldo (asinh)</td>
<td>0,4299\* (0,1942)</td>
<td>0,028 / 0,095</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,8533 / 0,5457</td>
</tr>
<tr>
<td>35–40 (A)</td>
<td>Admissões</td>
<td>0,0353\* (0,0148)</td>
<td>0,017 / 0,062</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,0930 / 0,0415</td>
</tr>
<tr>
<td>35–40 (A)</td>
<td>Desligamentos</td>
<td>0,0275 (0,0166)</td>
<td>0,098 / 0,245</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,0745 / 0,0466</td>
</tr>
<tr>
<td>35–40 (A)</td>
<td>Fluxo bruto</td>
<td>0,0319 (0,0154)</td>
<td>0,039 / 0,125</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/265 · adequate</td>
<td>0,0790 / 0,0433</td>
</tr>
<tr>
<td>35–40 (A)</td>
<td>Salário real (log)</td>
<td>0,0026 (0,0068)</td>
<td>0,699 / 0,832</td>
<td>falha / alerta</td>
<td>43655</td>
<td>15663 / 31561</td>
<td>75/265 · adequate</td>
<td>0,0310 / 0,0192</td>
</tr>
<tr>
<td>35–40 (A)</td>
<td>Saldo (asinh)</td>
<td>0,2605 (0,2006)</td>
<td>0,195 / 0,398</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/265 · adequate</td>
<td>0,8033 / 0,5636</td>
</tr>
<tr>
<td>41–49 (A)</td>
<td>Admissões</td>
<td>0,0841\*\*\* (0,0236)</td>
<td>\<0,001 / 0,004</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1125 / 0,0664</td>
</tr>
<tr>
<td>41–49 (A)</td>
<td>Desligamentos</td>
<td>0,0699\*\* (0,0245)</td>
<td>0,005 / 0,027</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0829 / 0,0689</td>
</tr>
<tr>
<td>41–49 (A)</td>
<td>Fluxo bruto</td>
<td>0,0776\*\*\* (0,0235)</td>
<td>0,001 / 0,009</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0942 / 0,0660</td>
</tr>
<tr>
<td>41–49 (A)</td>
<td>Salário real (log)</td>
<td>0,0010 (0,0076)</td>
<td>0,892 / 0,925</td>
<td>alerta / alerta</td>
<td>43624</td>
<td>15646 / 31536</td>
<td>75/266 · adequate</td>
<td>0,0383 / 0,0214</td>
</tr>
<tr>
<td>41–49 (A)</td>
<td>Saldo (asinh)</td>
<td>0,3007 (0,2457)</td>
<td>0,222 / 0,418</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,7140 / 0,6903</td>
</tr>
<tr>
<td>50+ (A)</td>
<td>Admissões</td>
<td>0,0663 (0,0533)</td>
<td>0,214 / 0,418</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1664 / 0,1497</td>
</tr>
<tr>
<td>50+ (A)</td>
<td>Desligamentos</td>
<td>0,0069 (0,0377)</td>
<td>0,855 / 0,919</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0994 / 0,1058</td>
</tr>
<tr>
<td>50+ (A)</td>
<td>Fluxo bruto</td>
<td>0,0357 (0,0430)</td>
<td>0,407 / 0,581</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1265 / 0,1208</td>
</tr>
<tr>
<td>50+ (A)</td>
<td>Salário real (log)</td>
<td>0,0136 (0,0103)</td>
<td>0,189 / 0,394</td>
<td>falha / falha</td>
<td>43199</td>
<td>15318 / 31210</td>
<td>75/266 · adequate</td>
<td>0,0305 / 0,0290</td>
</tr>
<tr>
<td>50+ (A)</td>
<td>Saldo (asinh)</td>
<td>1,2056\*\*\* (0,3571)</td>
<td>\<0,001 / 0,007</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,4846 / 1,0033</td>
</tr>
<tr>
<td>18–24 (B)</td>
<td>Admissões</td>
<td>0,0326 (0,0339)</td>
<td>0,336 / 0,505</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1011 / 0,0952</td>
</tr>
<tr>
<td>18–24 (B)</td>
<td>Desligamentos</td>
<td>0,0508 (0,0448)</td>
<td>0,258 / 0,440</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/266 · adequate</td>
<td>0,1246 / 0,1260</td>
</tr>
<tr>
<td>18–24 (B)</td>
<td>Fluxo bruto</td>
<td>0,0397 (0,0377)</td>
<td>0,294 / 0,464</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1064 / 0,1059</td>
</tr>
<tr>
<td>18–24 (B)</td>
<td>Salário real (log)</td>
<td>−0,0034 (0,0104)</td>
<td>0,746 / 0,861</td>
<td>alerta / falha</td>
<td>43615</td>
<td>15616 / 31516</td>
<td>75/266 · adequate</td>
<td>0,0311 / 0,0292</td>
</tr>
<tr>
<td>18–24 (B)</td>
<td>Saldo (asinh)</td>
<td>0,7097 (0,4037)</td>
<td>0,080 / 0,299</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,5424 / 1,1343</td>
</tr>
<tr>
<td>25–34 (B)</td>
<td>Admissões</td>
<td>−0,0207 (0,0158)</td>
<td>0,189 / 0,399</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0881 / 0,0443</td>
</tr>
<tr>
<td>25–34 (B)</td>
<td>Desligamentos</td>
<td>−0,0275 (0,0180)</td>
<td>0,128 / 0,399</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0725 / 0,0507</td>
</tr>
<tr>
<td>25–34 (B)</td>
<td>Fluxo bruto</td>
<td>−0,0229 (0,0158)</td>
<td>0,148 / 0,399</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0734 / 0,0444</td>
</tr>
<tr>
<td>25–34 (B)</td>
<td>Salário real (log)</td>
<td>−0,0006 (0,0061)</td>
<td>0,921 / 0,952</td>
<td>falha / alerta</td>
<td>43878</td>
<td>15828 / 31716</td>
<td>75/266 · adequate</td>
<td>0,0308 / 0,0170</td>
</tr>
<tr>
<td>25–34 (B)</td>
<td>Saldo (asinh)</td>
<td>−0,1245 (0,2233)</td>
<td>0,577 / 0,722</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,9915 / 0,6275</td>
</tr>
<tr>
<td>35–44 (B)</td>
<td>Admissões</td>
<td>0,0297 (0,0216)</td>
<td>0,170 / 0,399</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0965 / 0,0607</td>
</tr>
<tr>
<td>35–44 (B)</td>
<td>Desligamentos</td>
<td>0,0191 (0,0253)</td>
<td>0,451 / 0,606</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0757 / 0,0710</td>
</tr>
<tr>
<td>35–44 (B)</td>
<td>Fluxo bruto</td>
<td>0,0257 (0,0230)</td>
<td>0,264 / 0,440</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0816 / 0,0645</td>
</tr>
<tr>
<td>35–44 (B)</td>
<td>Salário real (log)</td>
<td>−0,0083 (0,0065)</td>
<td>0,199 / 0,399</td>
<td>falha / falha</td>
<td>43802</td>
<td>15775 / 31664</td>
<td>75/266 · adequate</td>
<td>0,0361 / 0,0181</td>
</tr>
<tr>
<td>35–44 (B)</td>
<td>Saldo (asinh)</td>
<td>−0,0695 (0,2572)</td>
<td>0,787 / 0,875</td>
<td>falha / não rejeitada</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,8570 / 0,7225</td>
</tr>
<tr>
<td>45–54 (B)</td>
<td>Admissões</td>
<td>0,0751 (0,0373)</td>
<td>0,045 / 0,224</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1317 / 0,1048</td>
</tr>
<tr>
<td>45–54 (B)</td>
<td>Desligamentos</td>
<td>0,0455 (0,0339)</td>
<td>0,181 / 0,399</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0914 / 0,0952</td>
</tr>
<tr>
<td>45–54 (B)</td>
<td>Fluxo bruto</td>
<td>0,0615 (0,0345)</td>
<td>0,076 / 0,299</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1086 / 0,0970</td>
</tr>
<tr>
<td>45–54 (B)</td>
<td>Salário real (log)</td>
<td>0,0151 (0,0074)</td>
<td>0,043 / 0,224</td>
<td>alerta / falha</td>
<td>43440</td>
<td>15478 / 31377</td>
<td>75/266 · adequate</td>
<td>0,0319 / 0,0209</td>
</tr>
<tr>
<td>45–54 (B)</td>
<td>Saldo (asinh)</td>
<td>0,3714 (0,3082)</td>
<td>0,229 / 0,429</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,6379 / 0,8659</td>
</tr>
<tr>
<td>55–65 (B)</td>
<td>Admissões</td>
<td>0,0332 (0,0686)</td>
<td>0,628 / 0,754</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/266 · adequate</td>
<td>0,1904 / 0,1926</td>
</tr>
<tr>
<td>55–65 (B)</td>
<td>Desligamentos</td>
<td>−0,0418 (0,0460)</td>
<td>0,365 / 0,521</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1106 / 0,1294</td>
</tr>
<tr>
<td>55–65 (B)</td>
<td>Fluxo bruto</td>
<td>−0,0067 (0,0535)</td>
<td>0,900 / 0,952</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1398 / 0,1502</td>
</tr>
<tr>
<td>55–65 (B)</td>
<td>Salário real (log)</td>
<td>0,0090 (0,0123)</td>
<td>0,465 / 0,606</td>
<td>falha / alerta</td>
<td>42131</td>
<td>14512 / 30416</td>
<td>75/266 · adequate</td>
<td>0,0361 / 0,0346</td>
</tr>
<tr>
<td>55–65 (B)</td>
<td>Saldo (asinh)</td>
<td>1,0083\*\* (0,3546)</td>
<td>0,005 / 0,035</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,3780 / 0,9963</td>
</tr>
</table>
> Notas: cada DDD compara o grupo-alvo com seu complemento, preservando p nominal, p BH e famílias A (100 testes) e B (30). N estático DDD vem do modelo estático; N evento discrimina a amostra do diagnóstico dentro do grupo e a do diagnóstico DDD. CBOs T/C referem-se ao suporte do grupo-alvo, não ao número total de clusters do DDD. MDE informa separadamente o mínimo detectável a 80% de poder no grupo e no DDD. Estrelas usam p BH: \* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Falha, alerta e diagnóstico indefinido não autorizam interpretação causal. Saldo em asinh não tem leitura percentual. Fonte: ddd_multiplicity_results.csv, ddd_alternative_partitions.csv e seus diagnósticos.
**Tabela A.5.2 — DiDs dentro dos grupos: idade**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo</td>
<td>N</td>
<td>CBOs T/C · suporte</td>
</tr>
<tr>
<td>22–25</td>
<td>Admissões</td>
<td>−0,0741\* (0,0322)</td>
<td>0,022 / 0,065</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>22–25</td>
<td>Desligamentos</td>
<td>−0,0530 (0,0359)</td>
<td>0,141 / 0,244</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>22–25</td>
<td>Fluxo bruto</td>
<td>−0,0639 (0,0310)</td>
<td>0,040 / 0,101</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>22–25</td>
<td>Salário real (log)</td>
<td>−0,0517\*\*\* (0,0105)</td>
<td>\<0,001 / \<0,001</td>
<td>não rejeitada</td>
<td>15554</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>22–25</td>
<td>Saldo (asinh)</td>
<td>−0,1280 (0,2482)</td>
<td>0,606 / 0,685</td>
<td>falha</td>
<td>15935</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>26–30</td>
<td>Admissões</td>
<td>−0,0753\* (0,0312)</td>
<td>0,016 / 0,052</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>26–30</td>
<td>Desligamentos</td>
<td>−0,0680\*\* (0,0267)</td>
<td>0,011 / 0,038</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>26–30</td>
<td>Fluxo bruto</td>
<td>−0,0710\*\* (0,0263)</td>
<td>0,007 / 0,027</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>26–30</td>
<td>Salário real (log)</td>
<td>−0,0403\*\*\* (0,0105)</td>
<td>\<0,001 / 0,001</td>
<td>falha</td>
<td>15708</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>26–30</td>
<td>Saldo (asinh)</td>
<td>−0,3820 (0,2916)</td>
<td>0,191 / 0,289</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>31–34</td>
<td>Admissões</td>
<td>−0,0597 (0,0316)</td>
<td>0,060 / 0,141</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>31–34</td>
<td>Desligamentos</td>
<td>−0,0526\* (0,0251)</td>
<td>0,037 / 0,095</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>31–34</td>
<td>Fluxo bruto</td>
<td>−0,0551\* (0,0261)</td>
<td>0,036 / 0,095</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>31–34</td>
<td>Salário real (log)</td>
<td>−0,0582\*\*\* (0,0117)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15561</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>31–34</td>
<td>Saldo (asinh)</td>
<td>−0,3207 (0,3037)</td>
<td>0,292 / 0,399</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>35–40</td>
<td>Admissões</td>
<td>−0,0530 (0,0331)</td>
<td>0,110 / 0,217</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>35–40</td>
<td>Desligamentos</td>
<td>−0,0476 (0,0265)</td>
<td>0,074 / 0,162</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>35–40</td>
<td>Fluxo bruto</td>
<td>−0,0491 (0,0281)</td>
<td>0,081 / 0,171</td>
<td>falha</td>
<td>15926</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>35–40</td>
<td>Salário real (log)</td>
<td>−0,0500\*\*\* (0,0110)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15663</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>35–40</td>
<td>Saldo (asinh)</td>
<td>−0,4532 (0,2859)</td>
<td>0,114 / 0,221</td>
<td>falha</td>
<td>15935</td>
<td>75/265 · adequate</td>
</tr>
<tr>
<td>41–49</td>
<td>Admissões</td>
<td>−0,0161 (0,0400)</td>
<td>0,688 / 0,746</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>41–49</td>
<td>Desligamentos</td>
<td>−0,0145 (0,0295)</td>
<td>0,624 / 0,693</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>41–49</td>
<td>Fluxo bruto</td>
<td>−0,0141 (0,0335)</td>
<td>0,675 / 0,741</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>41–49</td>
<td>Salário real (log)</td>
<td>−0,0455\*\*\* (0,0136)</td>
<td>\<0,001 / 0,005</td>
<td>alerta</td>
<td>15646</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>41–49</td>
<td>Saldo (asinh)</td>
<td>−0,4563 (0,2541)</td>
<td>0,073 / 0,162</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>50+</td>
<td>Admissões</td>
<td>−0,0296 (0,0592)</td>
<td>0,617 / 0,692</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>50+</td>
<td>Desligamentos</td>
<td>−0,0631 (0,0354)</td>
<td>0,075 / 0,163</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>50+</td>
<td>Fluxo bruto</td>
<td>−0,0461 (0,0450)</td>
<td>0,307 / 0,416</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>50+</td>
<td>Salário real (log)</td>
<td>−0,0370\*\*\* (0,0109)</td>
<td>\<0,001 / 0,004</td>
<td>falha</td>
<td>15318</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>50+</td>
<td>Saldo (asinh)</td>
<td>0,3817\* (0,1725)</td>
<td>0,028 / 0,079</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Admissões</td>
<td>−0,0380 (0,0360)</td>
<td>0,292 / 0,399</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Desligamentos</td>
<td>−0,0170 (0,0443)</td>
<td>0,701 / 0,753</td>
<td>falha</td>
<td>15926</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Fluxo bruto</td>
<td>−0,0284 (0,0379)</td>
<td>0,454 / 0,569</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Salário real (log)</td>
<td>−0,0512\*\*\* (0,0111)</td>
<td>\<0,001 / \<0,001</td>
<td>alerta</td>
<td>15616</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>18–24</td>
<td>Saldo (asinh)</td>
<td>−0,0344 (0,1930)</td>
<td>0,859 / 0,872</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Admissões</td>
<td>−0,0693\* (0,0314)</td>
<td>0,028 / 0,079</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Desligamentos</td>
<td>−0,0608\* (0,0258)</td>
<td>0,019 / 0,059</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Fluxo bruto</td>
<td>−0,0643\*\* (0,0261)</td>
<td>0,014 / 0,047</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Salário real (log)</td>
<td>−0,0460\*\*\* (0,0110)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15828</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>25–34</td>
<td>Saldo (asinh)</td>
<td>−0,5069 (0,3529)</td>
<td>0,152 / 0,250</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Admissões</td>
<td>−0,0454 (0,0343)</td>
<td>0,187 / 0,286</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Desligamentos</td>
<td>−0,0398 (0,0270)</td>
<td>0,141 / 0,244</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Fluxo bruto</td>
<td>−0,0415 (0,0290)</td>
<td>0,154 / 0,251</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Salário real (log)</td>
<td>−0,0549\*\*\* (0,0129)</td>
<td>\<0,001 / \<0,001</td>
<td>falha</td>
<td>15775</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>35–44</td>
<td>Saldo (asinh)</td>
<td>−0,5498 (0,3050)</td>
<td>0,072 / 0,162</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Admissões</td>
<td>−0,0125 (0,0469)</td>
<td>0,790 / 0,822</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Desligamentos</td>
<td>−0,0221 (0,0325)</td>
<td>0,497 / 0,593</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Fluxo bruto</td>
<td>−0,0160 (0,0386)</td>
<td>0,678 / 0,741</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Salário real (log)</td>
<td>−0,0417\*\*\* (0,0114)</td>
<td>\<0,001 / 0,002</td>
<td>alerta</td>
<td>15478</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>45–54</td>
<td>Saldo (asinh)</td>
<td>−0,2274 (0,2270)</td>
<td>0,317 / 0,425</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Admissões</td>
<td>−0,0399 (0,0678)</td>
<td>0,557 / 0,646</td>
<td>falha</td>
<td>15926</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Desligamentos</td>
<td>−0,0860\* (0,0394)</td>
<td>0,030 / 0,082</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Fluxo bruto</td>
<td>−0,0643 (0,0498)</td>
<td>0,198 / 0,295</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Salário real (log)</td>
<td>−0,0448\*\*\* (0,0129)</td>
<td>\<0,001 / 0,003</td>
<td>falha</td>
<td>14512</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>55–65</td>
<td>Saldo (asinh)</td>
<td>0,3794\*\* (0,1345)</td>
<td>0,005 / 0,020</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
</table>
> Notas: DiD dentro do próprio grupo, janela balanceada −23 a +23, com referência em novembro de 2022 e erros agrupados por CBO. A família C contém 130 testes e seu ajuste BH foi preservado integralmente. Estas linhas não testam diferenças entre subgrupos. Os DDDs respondem a essa outra pergunta. Fonte: group_did_results.csv. O suporte e o diagnóstico de pré-tendências são parte do resultado.
As duas partições etárias são preservadas: coortes do artigo de referência na família A e faixas PNAD/IBGE na família B. A ausência de rejeição do teste salarial dentro de 22–25 anos é uma das duas exceções pass entre 100 diagnósticos das partições principais, junto do salário na categoria indígena. Não há ajuste de multiplicidade desses diagnósticos; o DDD salarial dessa coorte tem pré-tendência falha. O saldo de 50+ (família A) e o de 55–65 (família B) rejeitam após BH, mas seus diagnósticos DDD falham.
**Figura A.5.1 — Admissões: perfis mensais por idade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/728afdc7-9aaa-4864-b01b-48f275e90409/figure_A_5_1_age_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=7f424cd4fc63a01bb7f1b12913373fc0bbcacd6fadec52502f1464d395ad45ce&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.5.2 — Salário real de admissão: perfis mensais por idade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/2ad14e40-7112-43af-b109-6051babb4ae8/figure_A_5_2_age_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=61e950c079ec7b2f82914e32b55e9dbd98a1a4d6eef37760840cc5b408ed75df&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.5.3 — Coorte de 22–25 anos: salário real de admissão**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/e25b5523-562d-42b4-b64b-8013f419d439/figure_A_5_3_canaries_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=ef504387dfd18f691e5c771653cf7f490a1d7651fb7daa15a8ad67f78e01cc28&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
> Figuras: séries estendidas de −23 a +41, relativas a novembro de 2022; bandas de 95%, linhas horizontais na média dos coeficientes pré e linha vertical pontilhada em +23. Os testes das tabelas usam −23 a +23. A numeração foi atualizada com os mesmos coeficientes, intervalos e convenções; as imagens anteriores estão preservadas na cópia local da V4.
### A.6 Escolaridade
**Tabela A.6.1 — Contrastes DDD completos: escolaridade**
<table header-row="true">
<tr>
<td>Grupo (família)</td>
<td>Resultado</td>
<td>DDD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo / DDD</td>
<td>N estático DDD</td>
<td>N evento grupo / DDD</td>
<td>CBOs alvo T/C · suporte</td>
<td>MDE 80% grupo / DDD</td>
</tr>
<tr>
<td>Fundamental ou menos (A)</td>
<td>Admissões</td>
<td>0,1231\* (0,0502)</td>
<td>0,015 / 0,055</td>
<td>falha / falha</td>
<td>44098</td>
<td>15879 / 31814</td>
<td>75/266 · adequate</td>
<td>0,1492 / 0,1411</td>
</tr>
<tr>
<td>Fundamental ou menos (A)</td>
<td>Desligamentos</td>
<td>0,1321\* (0,0531)</td>
<td>0,013 / 0,055</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1316 / 0,1493</td>
</tr>
<tr>
<td>Fundamental ou menos (A)</td>
<td>Fluxo bruto</td>
<td>0,1284\* (0,0504)</td>
<td>0,011 / 0,051</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1370 / 0,1416</td>
</tr>
<tr>
<td>Fundamental ou menos (A)</td>
<td>Salário real (log)</td>
<td>0,0349\* (0,0142)</td>
<td>0,014 / 0,055</td>
<td>falha / falha</td>
<td>42233</td>
<td>14641 / 30543</td>
<td>75/266 · adequate</td>
<td>0,0405 / 0,0398</td>
</tr>
<tr>
<td>Fundamental ou menos (A)</td>
<td>Saldo (asinh)</td>
<td>0,9560\*\* (0,3619)</td>
<td>0,009 / 0,043</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,4687 / 1,0168</td>
</tr>
<tr>
<td>Médio (A)</td>
<td>Admissões</td>
<td>−0,0057 (0,0344)</td>
<td>0,868 / 0,923</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31861</td>
<td>75/266 · adequate</td>
<td>0,0882 / 0,0967</td>
</tr>
<tr>
<td>Médio (A)</td>
<td>Desligamentos</td>
<td>−0,0333 (0,0288)</td>
<td>0,248 / 0,451</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0862 / 0,0809</td>
</tr>
<tr>
<td>Médio (A)</td>
<td>Fluxo bruto</td>
<td>−0,0187 (0,0294)</td>
<td>0,525 / 0,691</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0827 / 0,0826</td>
</tr>
<tr>
<td>Médio (A)</td>
<td>Salário real (log)</td>
<td>−0,0014 (0,0112)</td>
<td>0,902 / 0,925</td>
<td>falha / falha</td>
<td>43729</td>
<td>15801 / 31595</td>
<td>75/266 · adequate</td>
<td>0,0342 / 0,0316</td>
</tr>
<tr>
<td>Médio (A)</td>
<td>Saldo (asinh)</td>
<td>0,1938 (0,2481)</td>
<td>0,435 / 0,605</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,9134 / 0,6971</td>
</tr>
<tr>
<td>Superior (A)</td>
<td>Admissões</td>
<td>−0,1108\* (0,0451)</td>
<td>0,015 / 0,055</td>
<td>falha / falha</td>
<td>44098</td>
<td>15926 / 31861</td>
<td>75/266 · adequate</td>
<td>0,1041 / 0,1267</td>
</tr>
<tr>
<td>Superior (A)</td>
<td>Desligamentos</td>
<td>−0,1064\* (0,0435)</td>
<td>0,015 / 0,055</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,1021 / 0,1222</td>
</tr>
<tr>
<td>Superior (A)</td>
<td>Fluxo bruto</td>
<td>−0,1083\*\* (0,0418)</td>
<td>0,010 / 0,048</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,0929 / 0,1175</td>
</tr>
<tr>
<td>Superior (A)</td>
<td>Salário real (log)</td>
<td>0,0076 (0,0128)</td>
<td>0,551 / 0,707</td>
<td>falha / alerta</td>
<td>42494</td>
<td>14892 / 30703</td>
<td>75/266 · adequate</td>
<td>0,0262 / 0,0359</td>
</tr>
<tr>
<td>Superior (A)</td>
<td>Saldo (asinh)</td>
<td>−0,8421\*\* (0,2689)</td>
<td>0,002 / 0,015</td>
<td>falha / falha</td>
<td>44098</td>
<td>15935 / 31870</td>
<td>75/266 · adequate</td>
<td>0,8915 / 0,7555</td>
</tr>
</table>
> Notas: cada DDD compara o grupo-alvo com seu complemento, preservando p nominal, p BH e famílias A (100 testes) e B (30). N estático DDD vem do modelo estático; N evento discrimina a amostra do diagnóstico dentro do grupo e a do diagnóstico DDD. CBOs T/C referem-se ao suporte do grupo-alvo, não ao número total de clusters do DDD. MDE informa separadamente o mínimo detectável a 80% de poder no grupo e no DDD. Estrelas usam p BH: \* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Falha, alerta e diagnóstico indefinido não autorizam interpretação causal. Saldo em asinh não tem leitura percentual. Fonte: ddd_multiplicity_results.csv, ddd_alternative_partitions.csv e seus diagnósticos.
**Tabela A.6.2 — DiDs dentro dos grupos: escolaridade**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo</td>
<td>N</td>
<td>CBOs T/C · suporte</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Admissões</td>
<td>0,0018 (0,0531)</td>
<td>0,974 / 0,974</td>
<td>falha</td>
<td>15879</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Desligamentos</td>
<td>0,0141 (0,0469)</td>
<td>0,763 / 0,800</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Fluxo bruto</td>
<td>0,0089 (0,0488)</td>
<td>0,855 / 0,872</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Salário real (log)</td>
<td>−0,0080 (0,0144)</td>
<td>0,580 / 0,661</td>
<td>falha</td>
<td>14641</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Fundamental ou menos</td>
<td>Saldo (asinh)</td>
<td>0,3330 (0,1668)</td>
<td>0,047 / 0,112</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Admissões</td>
<td>−0,0438 (0,0314)</td>
<td>0,164 / 0,261</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Desligamentos</td>
<td>−0,0455 (0,0307)</td>
<td>0,139 / 0,244</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Fluxo bruto</td>
<td>−0,0444 (0,0294)</td>
<td>0,132 / 0,244</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Salário real (log)</td>
<td>−0,0427\*\*\* (0,0122)</td>
<td>\<0,001 / 0,003</td>
<td>falha</td>
<td>15801</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Médio</td>
<td>Saldo (asinh)</td>
<td>−0,2973 (0,3251)</td>
<td>0,361 / 0,470</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Admissões</td>
<td>−0,1075\*\* (0,0371)</td>
<td>0,004 / 0,017</td>
<td>falha</td>
<td>15926</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Desligamentos</td>
<td>−0,0939\*\* (0,0363)</td>
<td>0,010 / 0,035</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Fluxo bruto</td>
<td>−0,1008\*\* (0,0331)</td>
<td>0,002 / 0,011</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Salário real (log)</td>
<td>−0,0352\*\*\* (0,0093)</td>
<td>\<0,001 / 0,001</td>
<td>falha</td>
<td>14892</td>
<td>75/266 · adequate</td>
</tr>
<tr>
<td>Superior</td>
<td>Saldo (asinh)</td>
<td>−1,1562\*\*\* (0,3173)</td>
<td>\<0,001 / 0,002</td>
<td>falha</td>
<td>15935</td>
<td>75/266 · adequate</td>
</tr>
</table>
> Notas: DiD dentro do próprio grupo, janela balanceada −23 a +23, com referência em novembro de 2022 e erros agrupados por CBO. A família C contém 130 testes e seu ajuste BH foi preservado integralmente. Estas linhas não testam diferenças entre subgrupos. Os DDDs respondem a essa outra pergunta. Fonte: group_did_results.csv. O suporte e o diagnóstico de pré-tendências são parte do resultado.
Ensino superior: admissões e desligamentos ficam em p BH = 0,055; fluxo bruto e saldo rejeitam a 5% após BH. O saldo do ensino fundamental também rejeita, com sinal positivo. Esses resultados não superam os diagnósticos de pré-tendências.
**Figura A.6.1 — Admissões: perfis mensais por escolaridade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/fee7df88-0e47-4459-974c-28784918f6ce/figure_A_6_1_education_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=124938a61ce70b4e2fc4cc0c5ff9eed802157570299d42292c0e06f29b7f8587&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.6.2 — Salário real de admissão: perfis mensais por escolaridade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/99f5524a-6371-4bb2-99b2-1dca14c683f0/figure_A_6_2_education_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=cae9d914657c236c24cc156bbf1d1daeba60ed3de28a13e3691fbc2d87116ac6&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
> Figuras: séries estendidas de −23 a +41, relativas a novembro de 2022; bandas de 95%, linhas horizontais na média dos coeficientes pré e linha vertical pontilhada em +23. Os testes das tabelas usam −23 a +23. A numeração foi atualizada com os mesmos coeficientes, intervalos e convenções; as imagens anteriores estão preservadas na cópia local da V4.
### A.7 Renda ocupacional pré-tratamento
**Tabela A.7.1 — Contrastes DDD completos: renda ocupacional pré-tratamento**
<table header-row="true">
<tr>
<td>Grupo (família)</td>
<td>Resultado</td>
<td>DDD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo / DDD</td>
<td>N estático DDD</td>
<td>N evento grupo / DDD</td>
<td>CBOs alvo T/C · suporte</td>
<td>MDE 80% grupo / DDD</td>
</tr>
<tr>
<td>Até 2 SM (A)</td>
<td>Admissões</td>
<td>0,1183 (0,0793)</td>
<td>0,136 / 0,325</td>
<td>falha / falha</td>
<td>22049</td>
<td>12782 / 15935</td>
<td>46/227 · adequate</td>
<td>0,0902 / 0,2227</td>
</tr>
<tr>
<td>Até 2 SM (A)</td>
<td>Desligamentos</td>
<td>0,0112 (0,0952)</td>
<td>0,906 / 0,925</td>
<td>falha / falha</td>
<td>22049</td>
<td>12782 / 15935</td>
<td>46/227 · adequate</td>
<td>0,0842 / 0,2675</td>
</tr>
<tr>
<td>Até 2 SM (A)</td>
<td>Fluxo bruto</td>
<td>0,0676 (0,0863)</td>
<td>0,434 / 0,605</td>
<td>falha / falha</td>
<td>22049</td>
<td>12782 / 15935</td>
<td>46/227 · adequate</td>
<td>0,0839 / 0,2424</td>
</tr>
<tr>
<td>Até 2 SM (A)</td>
<td>Salário real (log)</td>
<td>−0,0062 (0,0236)</td>
<td>0,792 / 0,907</td>
<td>falha / alerta</td>
<td>22012</td>
<td>12755 / 15907</td>
<td>46/227 · adequate</td>
<td>0,0393 / 0,0664</td>
</tr>
<tr>
<td>Até 2 SM (A)</td>
<td>Saldo (asinh)</td>
<td>1,6638 (0,8627)</td>
<td>0,055 / 0,156</td>
<td>falha / falha</td>
<td>22049</td>
<td>12782 / 15935</td>
<td>46/227 · adequate</td>
<td>1,0034 / 2,4238</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM (A)</td>
<td>Admissões</td>
<td>−0,1474 (0,0779)</td>
<td>0,059 / 0,164</td>
<td>falha / falha</td>
<td>22049</td>
<td>2726 / 15935</td>
<td>26/32 · limited</td>
<td>0,1893 / 0,2188</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM (A)</td>
<td>Desligamentos</td>
<td>−0,0543 (0,0911)</td>
<td>0,552 / 0,707</td>
<td>falha / falha</td>
<td>22049</td>
<td>2726 / 15935</td>
<td>26/32 · limited</td>
<td>0,2280 / 0,2561</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM (A)</td>
<td>Fluxo bruto</td>
<td>−0,1033 (0,0836)</td>
<td>0,217 / 0,418</td>
<td>falha / falha</td>
<td>22049</td>
<td>2726 / 15935</td>
<td>26/32 · limited</td>
<td>0,2069 / 0,2349</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM (A)</td>
<td>Salário real (log)</td>
<td>−0,0031 (0,0256)</td>
<td>0,904 / 0,925</td>
<td>falha / falha</td>
<td>22012</td>
<td>2725 / 15907</td>
<td>26/32 · limited</td>
<td>0,0734 / 0,0718</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM (A)</td>
<td>Saldo (asinh)</td>
<td>−1,2692 (0,9244)</td>
<td>0,171 / 0,371</td>
<td>alerta / falha</td>
<td>22049</td>
<td>2726 / 15935</td>
<td>26/32 · limited</td>
<td>2,3802 / 2,5971</td>
</tr>
<tr>
<td>Mais de 5 SM (A)</td>
<td>Admissões</td>
<td>0,0947 (0,1133)</td>
<td>0,404 / 0,581</td>
<td>indefinido: posto / falha</td>
<td>22049</td>
<td>423 / 15935</td>
<td>3/6 · thin</td>
<td>0,3048 / 0,3183</td>
</tr>
<tr>
<td>Mais de 5 SM (A)</td>
<td>Desligamentos</td>
<td>0,2486 (0,1375)</td>
<td>0,071 / 0,193</td>
<td>indefinido: posto / falha</td>
<td>22049</td>
<td>423 / 15935</td>
<td>3/6 · thin</td>
<td>0,3364 / 0,3862</td>
</tr>
<tr>
<td>Mais de 5 SM (A)</td>
<td>Fluxo bruto</td>
<td>0,1699 (0,1153)</td>
<td>0,142 / 0,329</td>
<td>indefinido: posto / falha</td>
<td>22049</td>
<td>423 / 15935</td>
<td>3/6 · thin</td>
<td>0,2702 / 0,3240</td>
</tr>
<tr>
<td>Mais de 5 SM (A)</td>
<td>Salário real (log)</td>
<td>0,0643\*\* (0,0242)</td>
<td>0,008 / 0,043</td>
<td>indefinido: posto / falha</td>
<td>22012</td>
<td>423 / 15907</td>
<td>3/6 · thin</td>
<td>0,1102 / 0,0680</td>
</tr>
<tr>
<td>Mais de 5 SM (A)</td>
<td>Saldo (asinh)</td>
<td>−2,4186 (2,0104)</td>
<td>0,230 / 0,426</td>
<td>indefinido: posto / falha</td>
<td>22049</td>
<td>423 / 15935</td>
<td>3/6 · thin</td>
<td>6,7640 / 5,6484</td>
</tr>
</table>
> Notas: cada DDD compara o grupo-alvo com seu complemento, preservando p nominal, p BH e famílias A (100 testes) e B (30). N estático DDD vem do modelo estático; N evento discrimina a amostra do diagnóstico dentro do grupo e a do diagnóstico DDD. CBOs T/C referem-se ao suporte do grupo-alvo, não ao número total de clusters do DDD. MDE informa separadamente o mínimo detectável a 80% de poder no grupo e no DDD. Estrelas usam p BH: \* p\<0,10; \*\* p\<0,05; \*\*\* p\<0,01. Falha, alerta e diagnóstico indefinido não autorizam interpretação causal. Saldo em asinh não tem leitura percentual. Fonte: ddd_multiplicity_results.csv, ddd_alternative_partitions.csv e seus diagnósticos.
**Tabela A.7.2 — DiDs dentro dos grupos: renda ocupacional pré-tratamento**
<table header-row="true">
<tr>
<td>Grupo</td>
<td>Resultado</td>
<td>DiD (EP)</td>
<td>p nominal / BH</td>
<td>Pré-tendência grupo</td>
<td>N</td>
<td>CBOs T/C · suporte</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Admissões</td>
<td>−0,0304 (0,0321)</td>
<td>0,345 / 0,453</td>
<td>falha</td>
<td>12782</td>
<td>46/227 · adequate</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Desligamentos</td>
<td>−0,0409 (0,0299)</td>
<td>0,173 / 0,271</td>
<td>falha</td>
<td>12782</td>
<td>46/227 · adequate</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Fluxo bruto</td>
<td>−0,0353 (0,0298)</td>
<td>0,237 / 0,335</td>
<td>falha</td>
<td>12782</td>
<td>46/227 · adequate</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Salário real (log)</td>
<td>−0,0493\*\*\* (0,0140)</td>
<td>\<0,001 / 0,003</td>
<td>falha</td>
<td>12755</td>
<td>46/227 · adequate</td>
</tr>
<tr>
<td>Até 2 SM</td>
<td>Saldo (asinh)</td>
<td>0,2144 (0,3569)</td>
<td>0,548 / 0,642</td>
<td>falha</td>
<td>12782</td>
<td>46/227 · adequate</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Admissões</td>
<td>−0,1914\*\* (0,0664)</td>
<td>0,006 / 0,021</td>
<td>falha</td>
<td>2726</td>
<td>26/32 · limited</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Desligamentos</td>
<td>−0,1028 (0,0800)</td>
<td>0,204 / 0,298</td>
<td>falha</td>
<td>2726</td>
<td>26/32 · limited</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Fluxo bruto</td>
<td>−0,1494 (0,0726)</td>
<td>0,044 / 0,108</td>
<td>falha</td>
<td>2726</td>
<td>26/32 · limited</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Salário real (log)</td>
<td>−0,0434 (0,0258)</td>
<td>0,097 / 0,198</td>
<td>falha</td>
<td>2725</td>
<td>26/32 · limited</td>
</tr>
<tr>
<td>Mais de 2 a 5 SM</td>
<td>Saldo (asinh)</td>
<td>−1,2484 (0,8350)</td>
<td>0,140 / 0,244</td>
<td>alerta</td>
<td>2726</td>
<td>26/32 · limited</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Admissões</td>
<td>−0,0068 (0,0954)</td>
<td>0,945 / 0,952</td>
<td>indefinido: posto</td>
<td>423</td>
<td>3/6 · thin</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Desligamentos</td>
<td>0,1564 (0,1053)</td>
<td>0,176 / 0,272</td>
<td>indefinido: posto</td>
<td>423</td>
<td>3/6 · thin</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Fluxo bruto</td>
<td>0,0723 (0,0846)</td>
<td>0,417 / 0,537</td>
<td>indefinido: posto</td>
<td>423</td>
<td>3/6 · thin</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Salário real (log)</td>
<td>0,0117 (0,0345)</td>
<td>0,743 / 0,785</td>
<td>indefinido: posto</td>
<td>423</td>
<td>3/6 · thin</td>
</tr>
<tr>
<td>Mais de 5 SM</td>
<td>Saldo (asinh)</td>
<td>−3,4227 (2,1171)</td>
<td>0,145 / 0,244</td>
<td>indefinido: posto</td>
<td>423</td>
<td>3/6 · thin</td>
</tr>
</table>
> Notas: DiD dentro do próprio grupo, janela balanceada −23 a +23, com referência em novembro de 2022 e erros agrupados por CBO. A família C contém 130 testes e seu ajuste BH foi preservado integralmente. Estas linhas não testam diferenças entre subgrupos. Os DDDs respondem a essa outra pergunta. Fonte: group_did_results.csv. O suporte e o diagnóstico de pré-tendências são parte do resultado.
Na renda alta, os cinco modelos dentro do grupo foram estimados em 423 observações na janela balanceada. A matriz dos 22 leads tem posto 7, de modo que Wald conjunto e inclinação GLS ficam indefinidos. As contagens de 3 CBOs tratadas e 6 controles descrevem o suporte efetivo com fluxos nessa janela. Os estudos de eventos estendidos das figuras são outra amostra e não transferem seus p-valores para essas tabelas. O DDD inclui também o complemento: sua amostra é maior e seu diagnóstico falha. O DDD salarial positivo (+0,0643; p BH = 0,043) não elimina a limitação de suporte do grupo-alvo.
**Figura A.7.1 — Admissões: perfis mensais por renda ocupacional pré-tratamento**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/6ddae0ce-7149-4f62-acfb-bfdac18db8b8/figure_A_7_1_income_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=277ff96a5147d9968fb5cc8a1b45c724f2482032668ff46d2e0c6a156603c6ed&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.7.2 — Salário real de admissão: perfis mensais por renda ocupacional pré-tratamento**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/79176617-518a-4669-b358-d0059503d981/figure_A_7_2_income_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=3cac8d1f3e301a1772f59b45d1cc5bc97987b45f9a654532450c25b076a57be3&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
> Figuras: séries estendidas de −23 a +41, relativas a novembro de 2022; bandas de 95%, linhas horizontais na média dos coeficientes pré e linha vertical pontilhada em +23. Os testes das tabelas usam −23 a +23. A numeração foi atualizada com os mesmos coeficientes, intervalos e convenções; as imagens anteriores estão preservadas na cópia local da V4.
### A.8 Síntese dos DiDs dentro dos grupos
As três figuras separam os desfechos da antiga síntese única e preservam os 26 grupos em cada painel. São DiDs dentro dos grupos, não DDDs. As estimativas vêm das mesmas saídas salvas; nenhum modelo foi reestimado. Fluxo bruto e saldo permanecem nas Tabelas A.3.2–A.7.2.
Os intervalos são os intervalos cluster-t no limiar de descoberta BH da família C: q × k / m = 0,05 × 40 / 130 = 0,0153846. Eles não são intervalos simultâneos de 95%. Separar os desfechos visualmente não altera os 130 testes da família nem os p-valores ajustados. Marcadores preenchidos indicam p BH abaixo de 0,05; triângulo indica suporte limitado e X, suporte baixo.
**Figura A.8.1 — Admissões: DiDs dentro dos grupos**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/e819e4be-4124-4767-b96f-994a5fb88743/figure_a_8_1_admissoes.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=e2a5be4a9294af36cf2b91ef1bcbf53bd44dd52c09d089a9f04dcb1ac3b47208&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.8.2 — Desligamentos: DiDs dentro dos grupos**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/7bd0155e-5faa-4308-b5ac-48019545b68f/figure_a_8_2_desligamentos.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=fde6448122e87aaee6ba4af12ec726e2d63252057779b87ca70c85a5bf268265&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura A.8.3 — Salário real de admissão: DiDs dentro dos grupos**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/805b69e9-0ca8-49b3-9dd9-03808d24cc07/figure_a_8_3_ln_salario_real_adm.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=ff272835fa68f044ff8b0d47d2d29c14ac8a316dc7073269bf01649fdd1a069d&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
O salário é negativo e rejeita após BH em 22 dos 26 grupos. Isso é compatível com apenas 2 rejeições entre os 20 testes salariais DDD da família A, cujo ajuste abrange os 100 testes: um estimador descreve o diferencial em cada grupo; o outro testa diferenças entre grupos. Suporte e pré-tendências impedem uma leitura causal do conjunto.
## Apêndice B: Diagnósticos dos exercícios complementares
Este apêndice reúne os diagnósticos dos exercícios do Apêndice D e da extensão espacial declarada na subseção 4.5. Em todos eles, o suporte foi publicado antes dos coeficientes, o tamanho de cada família foi fixado por escrito antes da estimação, e nenhum critério de continuidade dependeu do coeficiente de tratamento.
### B.1 Tendências prévias da RAIS
**Tabela B.1: Tendências prévias no modelo e na amostra exatos — RAIS**
<table header-row="true">
<tr>
<td>Desfecho</td>
<td>Janela</td>
<td>Períodos pré</td>
<td>p conjunto</td>
<td>p linear</td>
<td>Períodos com p \< 0,05</td>
<td>Classificação</td>
</tr>
<tr>
<td>Estoque em 31 de dezembro</td>
<td>2019–2024</td>
<td>3</td>
<td>0,082</td>
<td>0,145</td>
<td>2</td>
<td>falha</td>
</tr>
<tr>
<td>Rotatividade (log)</td>
<td>2021–2024</td>
<td>1</td>
<td>0,469</td>
<td>0,469</td>
<td>0</td>
<td>passa</td>
</tr>
<tr>
<td>Tempo médio de emprego (log)</td>
<td>2019–2024</td>
<td>3</td>
<td>0,047</td>
<td>0,800</td>
<td>0</td>
<td>falha</td>
</tr>
</table>
> *Notas: cada teste é estimado sobre o modelo, a amostra e a estrutura de agrupamento exatos do resultado reportado na Tabela D.1. A agregação anual, portanto, não remove todas as diferenças de tendência detectáveis entre tratados e controle. A rotatividade dispõe de um único período anterior à referência, e sua não rejeição não é prova de tendências paralelas.*
As sensibilidades declaradas da família D, que incluem a janela de 2019 a 2024, a exclusão de 2020 e a exclusão de 2022, preservam o sinal e a ordem de magnitude dos três coeficientes. A exclusão de 2022 deixa a rotatividade sem período pré-referência anterior, de modo que sua tendência prévia passa a ser explicitamente **não estimável**. Nenhuma sensibilidade substitui a especificação principal, e todas estão fora da família D.
**Uma sensibilidade declarada não pôde ser executada.** O estoque médio anual, alternativa ao estoque em data fixa, exigiria resolver 2.749.713 meses de início e 316.377 meses de fim inativos que os campos da fonte não determinam. Construí-la exigiria um proxy não declarado, e por isso o item consta como inexequível, e não como omitido.
### B.2 Tendências prévias da PNAD Contínua
**Tabela B.2: Tendências prévias no modelo e na amostra exatos — PNAD Contínua**
<table header-row="true">
<tr>
<td>Desfecho</td>
<td>Amostra</td>
<td>Períodos pré</td>
<td>p conjunto</td>
<td>p linear</td>
<td>Períodos com p \< 0,05</td>
<td>Classificação</td>
</tr>
<tr>
<td>Informalidade</td>
<td>completa</td>
<td>42</td>
<td>\< 0,001</td>
<td>0,523</td>
<td>0</td>
<td>falha</td>
</tr>
<tr>
<td>Informalidade</td>
<td>sem 2020</td>
<td>38</td>
<td>\< 0,001</td>
<td>0,061</td>
<td>0</td>
<td>falha</td>
</tr>
<tr>
<td>Conta própria</td>
<td>completa</td>
<td>42</td>
<td>0,002</td>
<td>0,928</td>
<td>0</td>
<td>falha</td>
</tr>
<tr>
<td>Conta própria</td>
<td>sem 2020</td>
<td>38</td>
<td>\< 0,001</td>
<td>0,921</td>
<td>0</td>
<td>falha</td>
</tr>
<tr>
<td>Ocupados, total</td>
<td>completa</td>
<td>42</td>
<td>\< 0,001</td>
<td>\< 0,001</td>
<td>2</td>
<td>falha</td>
</tr>
<tr>
<td>Ocupados, total</td>
<td>sem 2020</td>
<td>38</td>
<td>\< 0,001</td>
<td>\< 0,001</td>
<td>2</td>
<td>falha</td>
</tr>
<tr>
<td>Ocupados formais</td>
<td>completa</td>
<td>42</td>
<td>\< 0,001</td>
<td>0,003</td>
<td>3</td>
<td>falha</td>
</tr>
<tr>
<td>Ocupados formais</td>
<td>sem 2020</td>
<td>38</td>
<td>\< 0,001</td>
<td>0,003</td>
<td>2</td>
<td>falha</td>
</tr>
<tr>
<td>Ocupados informais</td>
<td>completa</td>
<td>42</td>
<td>\< 0,001</td>
<td>0,190</td>
<td>3</td>
<td>falha</td>
</tr>
<tr>
<td>Ocupados informais</td>
<td>sem 2020</td>
<td>38</td>
<td>\< 0,001</td>
<td>0,647</td>
<td>3</td>
<td>falha</td>
</tr>
<tr>
<td>Rendimento (log)</td>
<td>completa</td>
<td>42</td>
<td>\< 0,001</td>
<td>\< 0,001</td>
<td>0</td>
<td>falha</td>
</tr>
<tr>
<td>Rendimento (log)</td>
<td>sem 2020</td>
<td>38</td>
<td>\< 0,001</td>
<td>\< 0,001</td>
<td>1</td>
<td>falha</td>
</tr>
</table>
> *Notas: as doze classificações falham, inclusive todas as que excluem 2020. O diferencial de tendência antecede o período pós-tratamento e não é explicado pela mudança de coleta de 2020. As matrizes de covariância dos períodos pré são positivas semidefinidas em todos os casos. A quebra de coleta de 2020 foi diagnosticada como diferencial, com a maior mudança de distância entre expostos e controle chegando a 3,39 pontos no índice de população ponderada; a especificação sem 2020 é obrigatória por desenho e está reportada acima.*
O suporte foi publicado antes de qualquer coeficiente. Sob a regra de maioria de 0,50, a tabela de tratamento contém 32 grupos ocupacionais tratados, 77 de controle e 14 intermediários excluídos. O painel de estoque reúne 32 tratados e 69 de controle observados; o braço individual reúne 46 grupos com observações expostas e 84 com controle. As dezoito sensibilidades declaradas, que incluem o tratamento do trimestre de transição, a exclusão de 2020, o limiar alternativo de 0,75 e o tratamento por grupo ocupacional no braço individual, preservam os sinais principais e permanecem fora da família E, sem ajuste de multiplicidade e sem promoção.
**Uma restrição de inferência precisa ficar declarada.** Os erros-padrão são agrupados por grupo ocupacional e **não implementam o desenho amostral complexo completo da PNAD Contínua**: estratos e unidades primárias de amostragem não integram a inferência registrada. As estimativas pontuais usam o peso amostral; a variância, não o plano amostral inteiro.
### B.3 Falsificação e suporte da extensão espacial
A extensão espacial descrita ao fim da subseção 4.5 executou falsificação e diagnóstico de suporte, e parou antes de estimar qualquer coeficiente de tratamento.
**Tabela B.3: Placebo temporal de dezembro de 2021 na interação tripla**
<table header-row="true">
<tr>
<td>Desfecho</td>
<td>Coeficiente</td>
<td>EP</td>
<td>p</td>
</tr>
<tr>
<td>Admissões</td>
<td>+0,0096</td>
<td>0,0056</td>
<td>0,085</td>
</tr>
<tr>
<td>Desligamentos</td>
<td>+0,0077</td>
<td>0,0050</td>
<td>0,126</td>
</tr>
<tr>
<td>Salário real de admissão</td>
<td>+0,0012</td>
<td>0,0025</td>
<td>0,641</td>
</tr>
<tr>
<td>Saldo líquido (asinh)</td>
<td>−0,0139</td>
<td>0,0158</td>
<td>0,382</td>
</tr>
</table>
> *Notas: evento falso datado em dezembro de 2021 e estimado apenas dentro do pré-período verdadeiro, descartando-se todo o período posterior ao ChatGPT. Os quatro placebos passam o critério de p ≥ 0,05.*
As tendências prévias da interação tripla, por sua vez, falham em três dos quatro desfechos: admissões com p conjunto de 0,0001, desligamentos com 0,033 e saldo líquido com 1,1 × 10⁻⁹. O salário real de admissão é o único que não falha, com p conjunto de 0,347. O critério de continuidade exigia apenas que **um** desfecho não falhasse, e foi por essa margem que o exercício prosseguiu ao diagnóstico de suporte. O critério foi satisfeito por margem estreita, assim como foi estreita a margem que depois interrompeu o exercício.
O diagnóstico de suporte cobriu oito itens, todos calculados sem usar desfecho e sem estimar modelo. A variação identificadora residual é adequada para os três proxies, retendo entre 12,6% e 16,6% da variância bruta após a absorção dos efeitos fixos. A coexistência de ocupações expostas e não expostas dentro da mesma célula de município e mês alcança 99,93% antes e 99,95% depois do evento. Todas as células do desenho dois por dois são não vazias. A remoção iterativa de singletons descarta 137 de 4.343.581 linhas, ou 0,003%, e 99,21% das células sobreviventes têm observações antes e depois.
O item que interrompeu o exercício foi a **estrutura efetiva de agrupamento**:
**Tabela B.4: Clusters efetivos do regressor de interesse, por proxy**
<table header-row="true">
<tr>
<td>Proxy de intensidade digital</td>
<td>Municípios efetivos</td>
<td>UFs efetivas</td>
<td>Maior alavancagem estadual</td>
<td>Classificação</td>
</tr>
<tr>
<td>Penetração de banda larga fixa</td>
<td>445,5</td>
<td>11,7</td>
<td>SP, 20,1%</td>
<td>limitado</td>
</tr>
<tr>
<td>Admissões em atividades digitais</td>
<td>532,5</td>
<td>9,2</td>
<td>SP, 25,7%</td>
<td>insuficiente</td>
</tr>
<tr>
<td>Uso de internet, PNAD TIC 2021</td>
<td>516,8</td>
<td>10,1</td>
<td>SP, 23,0%</td>
<td>limitado</td>
</tr>
</table>
> *Notas: há 657 municípios e 27 Unidades da Federação nominais. A contagem efetiva pondera cada unidade por sua participação na massa do regressor de interesse residualizado, de modo que ela cai abaixo da contagem nominal quando poucas unidades concentram a variação identificadora. O piso declarado para suporte estadual limitado era de 10 UFs efetivas. O segundo proxy ficou em 9,19; o valor não foi arredondado, recalibrado nem substituído. A inferência principal, agrupada por município, tinha suporte adequado nos três casos.*
**Três declarações de procedência acompanham este exercício e não devem ser omitidas.** A primeira: o diagnóstico de suporte que o interrompeu **não integrava o desenho original**; ele foi adotado depois que o critério de continuidade original já havia sido satisfeito, embora antes de qualquer número de suporte ser calculado, e por isso consta como emenda, e não como regra pré-registrada. A segunda: a emenda contém um conflito interno conhecido, porque previa tanto rebaixar um resultado frágil quanto interromper o exercício, e a regra conservadora foi mantida precisamente para não escolher a alternativa mais permissiva depois de saber qual delas prendia. A terceira: a família de 12 hipóteses permanece declarada com todas as vagas vazias, sem nenhum coeficiente, p-valor nominal ou p-valor ajustado.
### B.4 Reprodutibilidade
Os dois exercícios do Apêndice D foram replicados de forma independente em R, com a implementação do pacote `fixest`, sobre as mesmas amostras e estruturas de agrupamento. Os três coeficientes principais da RAIS e os seis da PNAD Contínua coincidem com a implementação em Python até a sexta casa decimal, com diferença máxima de coeficiente da ordem de 10⁻¹⁶ e de erro-padrão da ordem de 10⁻¹¹ e 10⁻⁸, respectivamente. Nenhum p-valor foi importado da replicação, e nenhuma família foi reajustada.
Os insumos brutos das três frentes estão congelados com verificação criptográfica, e nenhuma consulta ao vivo ocorreu durante a estimação. As famílias de multiplicidade D, E e F são independentes das famílias empregadas no Apêndice A, e nenhuma foi fundida a outra. O material completo, incluindo código, artefatos assinados, registro cronológico de decisões e diagnósticos integrais, acompanha o pacote de replicação.
## Apêndice C — Casos ocupacionais e trajetórias por idade
Este apêndice refaz o exercício de casos ocupacionais de *Canaries in the Coal Mine*. A pergunta é direta: as ocupações que o artigo destaca, sobretudo desenvolvimento de software e atendimento, mostram por aqui a retração de entrada que ele encontra?
Defini seis casos semanticamente, a partir das descrições oficiais da CBO de seis dígitos, congelei a seleção antes de olhar os resultados e reuni 76 códigos sem sobreposição. Para cada caso, acompanho mensalmente as admissões e o salário real de admissão nas faixas de 22–25, 26–30, 31–34, 35–40, 41–49 e 50 anos ou mais, com **novembro de 2022** normalizado em 1. A medida citada no texto é a média dos **doze meses terminais**, de junho de 2025 a maio de 2026, contra essa base. Os salários foram winsorizados nos percentis 1 e 99 dentro de cada CBO e ano, porque os registros brutos traziam valores implausíveis. Não há grupo de controle por caso, então tudo aqui é descritivo: as figuras mostram trajetórias, e não efeitos.
### C.1 Seleção e composição dos casos ocupacionais
O primeiro achado é sobre as próprias ocupações, e está na Tabela C.1: a correspondência semântica não reproduz a ordenação do artigo. Desenvolvedores e atendimento caem no topo da escala da OIT, como lá, mas supervisores de produção são majoritariamente não expostos ou sem pontuação disponível, estoquistas ficam inteiros em exposição mínima e auxiliares de saúde se dividem entre não expostos e minimamente expostos. Uso essa composição para interpretar os casos, e não para reclassificá-los; ausência de pontuação não é exposição zero.
**Tabela C.1: Seleção e composição da exposição dos casos ocupacionais**
<table header-row="true">
<tr>
<td>Caso ocupacional</td>
<td>CBOs (n)</td>
<td>Confiança semântica</td>
<td>Referência em *Canaries*</td>
<td>Composição OIT no Brasil</td>
<td>Admissões pré-tratamento</td>
</tr>
<tr>
<td>Desenvolvedores de software</td>
<td>7</td>
<td>Alta</td>
<td>Alta exposição</td>
<td>G3 64,6%; G2 29,9%; sem pontuação 5,5%</td>
<td>293.893</td>
</tr>
<tr>
<td>Atendimento ao cliente</td>
<td>2</td>
<td>Alta</td>
<td>Alta exposição</td>
<td>G3 100,0%</td>
<td>160.341</td>
</tr>
<tr>
<td>Gerentes de marketing e vendas</td>
<td>2</td>
<td>Alta</td>
<td>Quintil 4</td>
<td>G2 100,0%</td>
<td>68.132</td>
</tr>
<tr>
<td>Supervisores de produção</td>
<td>53</td>
<td>Moderada</td>
<td>Quintil 3</td>
<td>não exposto 58,3%; exposição mínima 5,5%; sem pontuação 36,2%</td>
<td>62.953</td>
</tr>
<tr>
<td>Estoquistas e repositores</td>
<td>5</td>
<td>Alta</td>
<td>Quintil 2</td>
<td>exposição mínima 100,0%</td>
<td>1.593.069</td>
</tr>
<tr>
<td>Auxiliares de saúde e cuidado</td>
<td>7</td>
<td>Moderada</td>
<td>Quintil 1</td>
<td>não exposto 62,4%; exposição mínima 37,6%</td>
<td>147.801</td>
</tr>
</table>
> *Nota: a composição da OIT é ponderada pelas admissões entre janeiro de 2021 e outubro de 2022. A seleção dos casos usa títulos e tarefas oficiais da CBO de seis dígitos e é independente dessa classificação. A composição do dicionário precisa ser declarada, porque ela não é equilibrada: dos 76 códigos principais, 53 pertencem a um único caso, o de supervisores de produção, e dos 80 mapeamentos registrados 60 têm confiança **`medium`**, não **`high`**. A cobertura da pontuação da OIT também varia entre os casos, de 63,8% em supervisores a 100% em quatro deles. Por isso o caso de supervisores é o menos homogêneo do conjunto e o que menos suporta leitura substantiva. Dicionário congelado com SHA-256 **`b8d0310606c37ed3…`**; fonte: **`results/tables/table_5_3_1_occupation_cases.md`**.*
### C.2 Trajetórias por idade
**Figura C.1: Trajetórias mensais de admissões por caso ocupacional e idade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/3405eba2-a1e6-434f-9b13-ef4515319074/figure_5_3_1_occupation_cases_admissions_by_age.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=c62d8e00925d8214e499f748223098e81ae414b397477d44d06be976c211a956&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
Nas admissões, o padrão comum aos seis casos não é de nível, e sim de **inclinação etária**: em todos eles as faixas mais velhas variam mais que as jovens. Só em **atendimento ao cliente** essa inclinação vira mudança de sinal, com −23,5% entre 22 e 25 anos contra **+12,2% entre 41 e 49 e +20,7% acima de 50**. **Desenvolvedores de software**, o caso mais citado no debate público, não mostram contratação mais fraca entre os jovens: as três faixas abaixo de 35 anos ficam praticamente na base, e as duas mais velhas crescem 13,8% e 20,7%. Nos outros quatro casos as admissões crescem em todas as idades. Supervisores de produção pedem cautela extra: são 53 dos 76 códigos do dicionário, todos de confiança `medium`, e o caso com a menor cobertura da pontuação.
**Figura C.2: Trajetórias mensais do salário real de admissão por caso ocupacional e idade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/6ef46caa-d351-41ca-af17-3b8088b82e8a/figure_5_3_2_occupation_cases_wage_by_age.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB4662A3SA33V%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T173159Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQDCQeRWu6jN0mU71VnSRlYSrAJujRPj2YaMropUnpv%2BqQIhALefDm1BXC8Rw%2BBtYO6qPNqEMmVMkDBZ3AMI8CvRYVoxKv8DCF4QABoMNjM3NDIzMTgzODA1IgyN0tIrY79zQKU%2FdEsq3AMzPXtbsZzMP1oEo2oIErY8lE4u4dIbBE4tSEq9alnDor%2FVByXuoI0nkHTyiEBCgtXYUZ9nOiCij1g4DpfHg6pphP%2BXse7qa6SrMp1qyZUsDzQG6HpPR%2F5cbFHMn9weXKCcFmdiiDPAHsTcB3pSSFE4KOC%2F4ofmP2Eu9nZYWbCU%2B2C%2B4nH9TQTjmhhE3Vfnp8zVWMKXu1l4CJrlC%2FtgFWCqUGa3IGQ43dHnzk8LGMtSUQOfda45XvabNPeyyiAAxsCWIS3G9MxsQ8rJn7ZxGcH5AWOKZt1krkcscSv3%2BbC%2FG66LSQU1lVbOBXTe5oFbNd5JYjwTi0VkWooaMWnlIjGvkoYKUhzVwnCO6TIOEqJgC9hy8yGx4d3gHUXQlphP1D0ByKjrpGnvSTqGKiUBtc9Ed2un7%2BlkHLexcDRGAZ8VsieujfkuOnEGHUnl%2BZTEeBk3hbiN2RBwHpBlbwqb6Czs8gao6h0zft%2BSj39T3MN9HUUB6O9J7KG23K0k97rLoTD24zeqRNnbN%2Fh7YqzyoIm9r24oaWk9UdJszYULw4HPNnPd6OZZZTeVMWxcHKdhGVKZKyPRKYuX%2Bgj2DykZU3ZAhmaCf76t8%2BmO6vTi7bAgwBmSL5sRu%2FULUN5K8zDZjLrVBjqkAQkRWJamWbf66u5Ki2t%2BtMblAsJ0maCCAdy%2BJafXkfSpMATGIpSBZjNLXfoVtqVdWX5qOepOxMTcgFiGQ3KO9yi2LejBxlY0VgFOKQlKR72%2BUC0Rn1C6EY3aU7zVp3AnbGrv4eKB%2BU1wlyfxUwkC0Db7sapdHNFDK2pK9PuPwDLXQesEy7R21KulKirJeqT6zdEmx5wG9WTHWxVHJViaV6pWaFTW&X-Amz-Signature=db2533a967347126fb90144dd446a52c6d38d0d61cee02c6d9161cee24e47979&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
No salário real de admissão não há inclinação etária nítida. **Atendimento** e **estoquistas** são positivos nas seis faixas, de +7,8% a +12,8% e de +5,7% a +7,5%. **Auxiliares de saúde e cuidado** é o único caso com quedas expressivas, de −11,3% a −25,1% acima dos 26 anos, e a volatilidade prévia alta pede cautela. Software, marketing e supervisores oscilam perto de zero. Como essas oscilações são pequenas diante da variação mensal das próprias séries, a leitura substantiva se restringe aos três primeiros casos.
O recorte etário sugere uma assimetria na porta de entrada, mas ela aparece de forma localizada: **a contratação mais fraca entre jovens é visível em um dos casos**. A inclinação das trajetórias é compatível com mudanças nas oportunidades de entrada, mas também com envelhecimento da população ocupada, sazonalidade e composição. Some-se a isso que o início das séries retrata um mercado de trabalho em recuperação da pandemia, a mesma limitação declarada na subseção 5.1 e visível nas figuras.
Uma limitação de dado fecha aqui uma porta analítica. O campo `tipomovimentacao` do CAGED vem como “tipo ignorado” em **93,2% das admissões**, contra 0,08% dos desligamentos. Isso viabiliza a decomposição dos desligamentos por motivo, usada na seção de robustez, e **inviabiliza** a decomposição simétrica da entrada, entre primeiro emprego e recolocação, que seria o exercício natural para separar entrada de recolocação. A limitação é da base, não do desenho.
Em resumo: procurei nas ocupações destacadas por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) o padrão de entrada que eles encontram. Há uma trajetória compatível em atendimento ao cliente, mas não em software. A comparação não é equivalente, porque o artigo acompanha estoque de emprego em firmas, o CAGED registra fluxo de admissões e a classificação da OIT difere dos quintis usados pelos autores. Este apêndice, portanto, não altera as conclusões das Seções 5.1 e 5.2. O que ele acrescenta é textura: a média nacional encobre trajetórias ocupacionais e etárias bem distintas, e ocupações de gradientes diferentes diferem também em ciclo, sazonalidade e volatilidade, o que ajuda a entender por que o contraste agregado é tão ruidoso.
## Apêndice D — Evidências complementares sobre estoque formal e informalidade
O CAGED observa fluxo, não estoque, e só enxerga o mercado formal. As duas limitações estão declaradas na subseção 4.1 e não têm solução dentro da própria base, então recorro a bases complementares. Desenho, tamanho de família e regra de parada foram declarados antes da estimação, aqui e nos dois exercícios seguintes. Os dois são medição, não identificação: nenhum coeficiente abaixo autoriza leitura causal, e por isso nenhum recebe marcação de significância.
### D.1 Estoque de vínculos formais na RAIS
O exercício replica o tratamento da dissertação, 75 CBO de quatro dígitos expostas contra 266 `Not Exposed`, em painel anual com efeitos fixos de ocupação e de ano e erro-padrão agrupado por ocupação. São três desfechos: o estoque de vínculos ativos em 31 de dezembro, a rotatividade de fluxo bruto anual relativa a esse estoque e o tempo médio de emprego.
A janela principal é **2019–2024**, e a escolha vem do diagnóstico: na janela longa iniciada em 2016, a quebra de série da migração ao eSocial é diferencial entre expostas e controle e domina o painel, e entre 2019 e 2024 ela deixa de ser. A rotatividade só é observável de 2021 a 2024, e o pós começa em 2023. O painel reúne 2.041 células de ocupação por ano, 1.360 no caso da rotatividade, com suporte adequado nas 16 linhas e mínimo de 75 ocupações tratadas e 265 de controle.
**Tabela D.1: Estoque, rotatividade e tempo de emprego (família D)**
<table header-row="true">
<tr>
<td>Desfecho</td>
<td>Janela</td>
<td>Estimador</td>
<td>Coeficiente</td>
<td>EP</td>
<td>p nominal</td>
<td>p ajustado</td>
<td>Tendência prévia</td>
</tr>
<tr>
<td>Estoque em 31 de dezembro</td>
<td>2019–2024</td>
<td>PPML</td>
<td>−0,0429</td>
<td>0,0156</td>
<td>0,006</td>
<td>0,018</td>
<td>falha</td>
</tr>
<tr>
<td>Rotatividade (log)</td>
<td>2021–2024</td>
<td>MQO</td>
<td>−0,0178</td>
<td>0,0262</td>
<td>0,496</td>
<td>0,496</td>
<td>passa, 1 período</td>
</tr>
<tr>
<td>Tempo médio de emprego (log)</td>
<td>2019–2024</td>
<td>MQO</td>
<td>−0,0264</td>
<td>0,0185</td>
<td>0,156</td>
<td>0,234</td>
<td>falha</td>
</tr>
</table>
> *Notas: família D, de três testes, com ajuste de Benjamini-Hochberg aplicado uma única vez sobre o conjunto declarado antes da estimação. O coeficiente do estoque é semi-elasticidade PPML da média condicional em nível e implica cerca de −4,2%; os dois demais são diferenciais em pontos logarítmicos. A tendência prévia da rotatividade dispõe de um único período anterior à referência, de modo que sua não rejeição não constitui prova de tendências paralelas. A replicação em R, a sensibilidade de estoque médio anual declarada e inexequível e os testes completos de tendência prévia estão no Apêndice B.1.*
O estoque de vínculos ativos das ocupações expostas é menor no pós, e é o único dos nove testes desta subseção que rejeita após o ajuste. Mas a tendência prévia desse mesmo desfecho falha, o que impede leitura causal e desaconselha tratá-lo como resultado principal. O diferencial de rotatividade não é distinguível de zero.
A leitura descritiva é estreita, e ainda assim importa para a subseção 5.1: estoque menor com rotatividade estável combina mais com menos vínculos ativos do que com menos movimentação. A hipótese de acomodação silenciosa prevê o contrário, fluxos mais lentos com estoque preservado, e não encontra apoio aqui. Aproveito também o estoque observado para validar o índice cumulativo de fluxo líquido usado no Apêndice A: ele acompanha o estoque em direção, mas não em magnitude, com mediana de correlação de nível de 0,03 e de variação de 0,11.
### D.2 Deslocamento para a informalidade na PNAD Contínua
O segundo exercício pergunta se houve deslocamento para a informalidade, com 57 cortes trimestrais de 2012T1 a 2026T1, entre ocupados de 18 a 65 anos e ponderados pelo peso amostral. Excluí 2022T4, que contém o evento e seria pré e pós ao mesmo tempo, de modo que o pós vai de 2023T1 a 2026T1. São dois braços: um individual, no nível da observação, e um de estoque por grupo ocupacional e trimestre, por PPML. Só o pareamento exato de quatro dígitos com a ISCO-08 herda o rótulo de exposição, o que cobre 97,9% das observações; o restante recebe `Sem classificação` e fica fora da estimação.
**Tabela D.2: Composição e estoque ocupacional (família E)**
<table header-row="true">
<tr>
<td>Braço</td>
<td>Desfecho</td>
<td>Estimador</td>
<td>Coeficiente</td>
<td>EP</td>
<td>p nominal</td>
<td>p ajustado</td>
</tr>
<tr>
<td>Individual</td>
<td>Informalidade</td>
<td>MQO ponderado</td>
<td>+0,0085</td>
<td>0,0113</td>
<td>0,452</td>
<td>0,543</td>
</tr>
<tr>
<td>Individual</td>
<td>Conta própria</td>
<td>MQO ponderado</td>
<td>+0,0213</td>
<td>0,0209</td>
<td>0,312</td>
<td>0,543</td>
</tr>
<tr>
<td>Estoque</td>
<td>Ocupados, total</td>
<td>PPML</td>
<td>+0,0616</td>
<td>0,0430</td>
<td>0,155</td>
<td>0,477</td>
</tr>
<tr>
<td>Estoque</td>
<td>Ocupados formais</td>
<td>PPML</td>
<td>+0,0420</td>
<td>0,0482</td>
<td>0,386</td>
<td>0,543</td>
</tr>
<tr>
<td>Estoque</td>
<td>Ocupados informais</td>
<td>PPML</td>
<td>+0,0817</td>
<td>0,0576</td>
<td>0,159</td>
<td>0,477</td>
</tr>
<tr>
<td>Individual</td>
<td>Rendimento (log)</td>
<td>MQO ponderado</td>
<td>−0,0093</td>
<td>0,0218</td>
<td>0,670</td>
<td>0,670</td>
</tr>
</table>
> *Notas: família E, de seis testes, com ajuste de Benjamini-Hochberg aplicado uma única vez sobre o conjunto declarado antes da estimação. O estimando é o diferencial médio entre expostos e controle no período de 2023T1 a 2026T1, condicional a efeitos fixos de grupo ocupacional e de trimestre sobre a janela de 2012T1 a 2026T1, excluído 2022T4. Não há nenhuma rejeição a 5%, nem nominal nem ajustada, e as 12 classificações de tendência prévia do modelo exato falham, inclusive nas especificações que excluem 2020. O rendimento entra como reconciliação com a Seção 3 e nunca como desfecho principal. A restrição de inferência, já que os erros-padrão agrupados por grupo ocupacional não implementam o desenho amostral complexo da PNAD Contínua, a replicação em R e os testes de tendência prévia estão no Apêndice B.2.*
Procurei o deslocamento e não o encontrei. Os sinais até apontam para composição mais informal entre os expostos, 0,85 ponto percentual na informalidade e 2,1 pontos no trabalho por conta própria, mas nenhum dos seis testes rejeita, nem antes nem depois do ajuste.
O braço de estoque afasta a leitura de substituição por estrutura, e não por falta de precisão: os diferenciais são positivos ao mesmo tempo para o estoque informal, cerca de 8,5%, para o formal, 4,3%, e para o total, 6,4%. Se houvesse migração do emprego formal para o informal, as duas primeiras séries teriam sinais opostos, e não é o que aparece.
Uma fronteira fica de pé: o desenho mede composição de cortes transversais repetidos, não trajetória individual, e por isso não observa transição entre estados. Responder sobre transição exigiria um painel de pessoa por trimestre com identificador estável e pesos longitudinais, que os arquivos públicos não oferecem.
### D.3 Uma discordância que precisa ser declarada
As duas medições de estoque formal desta subseção têm sinais opostos e magnitudes quase simétricas: −0,0429 na RAIS, com p nominal de 0,006, e +0,0420 no braço de estoque da PNAD Contínua, com p nominal de 0,386. A simetria numérica é coincidência, mas a divergência de sinal não pode ser omitida.
# **REFERÊNCIAS**
AGARWAL, Nikhil; MOEHRING, Alex; RAJPURKAR, Pranav; SALZ, Tobias. **Combining human expertise with artificial intelligence: Experimental evidence from radiology**. Cambridge, MA: National Bureau of Economic Research, jul. 2023. DOI: [https://doi.org/10.3386/w31422](https://doi.org/10.3386/w31422). Disponível em: [https://www.nber.org/papers/w31422](https://www.nber.org/papers/w31422). Acesso em: 8 ago. 2026.
APPEL, Ruth; MASSENKOFF, Maxim; MCCRORY, Peter; MCCAIN, Miles; HELLER, Ryan; NEYLON, Tyler; TAMKIN, Alex. **Anthropic Economic Index report: Economic primitives**. \[*S. l.*\]: Anthropic, 15 jan. 2026. Disponível em: [https://www.anthropic.com/research/anthropic-economic-index-january-2026-report](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report). Acesso em: 8 ago. 2026.
AUTOR, David H.; LEVY, Frank; MURNANE, Richard J. The skill content of recent technological change: An empirical exploration. **The Quarterly Journal of Economics**, \[*s. l.*\], v. 118, n. 4, p. 1279–1333, nov. 2003. DOI: [https://doi.org/10.1162/003355303322552801](https://doi.org/10.1162/003355303322552801). Disponível em: [https://academic.oup.com/qje/article/118/4/1279/1925105](https://academic.oup.com/qje/article/118/4/1279/1925105). Acesso em: 8 ago. 2026.
BENÍTEZ, Miguel; PARRADO, Eric. **Mirror, Mirror on the Wall: Which Jobs Will AI Replace After All?: A New Index of Occupational Exposure**. \[*S. l.*\]: Inter-American Development Bank, 27 ago. 2024. DOI: [https://doi.org/10.18235/0013125](https://doi.org/10.18235/0013125). Disponível em: [https://publications.iadb.org/en/mirror-mirror-wall-which-jobs-will-ai-replace-after-all-new-index-occupational-exposure](https://publications.iadb.org/en/mirror-mirror-wall-which-jobs-will-ai-replace-after-all-new-index-occupational-exposure). Acesso em: 8 ago. 2026.
BENJAMINI, Yoav; HOCHBERG, Yosef. Controlling the false discovery rate: A practical and powerful approach to multiple testing. **Journal of the Royal Statistical Society: Series B (Methodological)**, \[*s. l.*\], v. 57, n. 1, p. 289–300, 1995. DOI: [https://doi.org/10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x). Disponível em: [https://doi.org/10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x). Acesso em: 8 ago. 2026.
BICK, Alexander; BLANDIN, Adam; DEMING, David J. **The rapid adoption of generative AI**. St. Louis: Federal Reserve Bank of St. Louis, 27 out. 2025. Working Paper n. 2024-027F. DOI: [https://doi.org/10.20955/wp.2024.027](https://doi.org/10.20955/wp.2024.027). Disponível em: [https://doi.org/10.20955/wp.2024.027](https://doi.org/10.20955/wp.2024.027). Acesso em: 8 ago. 2026.
BRASIL. **Decreto nº 12.342, de 30 de dezembro de 2024**. Dispõe sobre o valor do salário mínimo a vigorar a partir de 1º de janeiro de 2025. Brasília, DF: Presidência da República, 2024. Disponível em: [https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12342.htm](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12342.htm). Acesso em: 8 ago. 2026.
BRYNJOLFSSON, Erik; CHANDAR, Bharat; CHEN, Ruyu. **Canaries in the coal mine? Six facts about the recent employment effects of artificial intelligence**. Stanford: Stanford Digital Economy Lab, 13 nov. 2025. Disponível em: [https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/](https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/). Acesso em: 8 ago. 2026.
CALLAWAY, Brantly; SANT’ANNA, Pedro H. C. Difference-in-differences with multiple time periods. **Journal of Econometrics**, \[*s. l.*\], v. 225, n. 2, p. 200–230, 2021. DOI: [https://doi.org/10.1016/j.jeconom.2020.12.001](https://doi.org/10.1016/j.jeconom.2020.12.001). Disponível em: [https://doi.org/10.1016/j.jeconom.2020.12.001](https://doi.org/10.1016/j.jeconom.2020.12.001). Acesso em: 8 ago. 2026.
CHAISEMARTIN, Clément de; D’HAULTFŒUILLE, Xavier. Two-way fixed effects estimators with heterogeneous treatment effects. **American Economic Review**, \[*s. l.*\], v. 110, n. 9, p. 2964–2996, 2020. DOI: [https://doi.org/10.1257/aer.20181169](https://doi.org/10.1257/aer.20181169). Disponível em: [https://doi.org/10.1257/aer.20181169](https://doi.org/10.1257/aer.20181169). Acesso em: 8 ago. 2026.
CHANDAR, Bharat. **Tracking employment changes in AI-exposed jobs**. Stanford: Stanford Digital Economy Laboratory, 1 ago. 2025. DOI: [https://doi.org/10.2139/ssrn.5384519](https://doi.org/10.2139/ssrn.5384519). Disponível em: [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5384519](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5384519). Acesso em: 8 ago. 2026.
CHEN, Jiafeng; ROTH, Jonathan. Logs with zeros? Some problems and solutions. **The Quarterly Journal of Economics**, \[*s. l.*\], v. 139, n. 2, p. 891–936, 2024. DOI: [https://doi.org/10.1093/qje/qjad054](https://doi.org/10.1093/qje/qjad054). Disponível em: [https://doi.org/10.1093/qje/qjad054](https://doi.org/10.1093/qje/qjad054). Acesso em: 8 ago. 2026.
ELOUNDOU, Tyna; MANNING, Sam; MISHKIN, Pamela; ROCK, Daniel. **GPTs are GPTs: An Early Look at the Labor Market Impact Potential of Large Language Models**. arXiv:2303.10130. \[*S. l.*\]: arXiv, 21 ago. 2023. DOI: [https://doi.org/10.48550/arXiv.2303.10130](https://doi.org/10.48550/arXiv.2303.10130). Disponível em: [http://arxiv.org/abs/2303.10130](http://arxiv.org/abs/2303.10130). Acesso em: 8 ago. 2026.
GMYREK, Pawel; BERG, Janine; KAMIŃSKI, Karol; KONOPCZYŃSKI, Filip; ŁADNA, Agnieszka; NAFRADI, Balint; ROSŁANIEC, Konrad; TROSZYŃSKI, Marek. **Generative AI and jobs: A refined global index of occupational exposure**. Geneva: International Labour Organization, 20 maio 2025. ILO Working Paper, n. 140. DOI: [https://doi.org/10.54394/HETP0387](https://doi.org/10.54394/HETP0387). Disponível em: [https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure](https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure). Acesso em: 8 ago. 2026.
HOSSEINI MAASOUM, Seyed Mahdi; LICHTINGER, Guy. **Generative AI as seniority-biased technological change: Evidence from U.S. résumé and job posting data**. \[*S. l.*\]: SSRN, 6 jun. 2026. DOI: [https://doi.org/10.2139/ssrn.5425555](https://doi.org/10.2139/ssrn.5425555). Disponível em: [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5425555](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5425555). Acesso em: 8 ago. 2026.
HUMLUM, Anders; VESTERGAARD, Emilie. **Large language models, small labor market effects**. Cambridge, MA: National Bureau of Economic Research, 2026. NBER Working Paper n. 33777, rev. mar. 2026. DOI: [https://doi.org/10.3386/w33777](https://doi.org/10.3386/w33777). Disponível em: [https://www.nber.org/papers/w33777](https://www.nber.org/papers/w33777). Acesso em: 8 ago. 2026.
KLEIN TEESELINK, Bouke. **Generative AI and labor market outcomes: Evidence from the United Kingdom**. \[*S. l.*\]: SSRN, 21 dez. 2025. DOI: [https://doi.org/10.2139/ssrn.5516798](https://doi.org/10.2139/ssrn.5516798). Disponível em: [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5516798](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5516798). Acesso em: 8 ago. 2026.
OSORIO, Rafael Guerreiro. **O sistema classificatório de “cor ou raça” do IBGE**. Brasília, DF: Instituto de Pesquisa Econômica Aplicada, nov. 2003. Disponível em: [https://repositorio.ipea.gov.br/bitstreams/e09cc868-669f-4064-b396-693e22e0ce07/download](https://repositorio.ipea.gov.br/bitstreams/e09cc868-669f-4064-b396-693e22e0ce07/download). Acesso em: 8 ago. 2026.
RAMBACHAN, Ashesh; ROTH, Jonathan. A more credible approach to parallel trends. **The Review of Economic Studies**, \[*s. l.*\], v. 90, n. 5, p. 2555–2591, 2023. DOI: [https://doi.org/10.1093/restud/rdad018](https://doi.org/10.1093/restud/rdad018). Disponível em: [https://doi.org/10.1093/restud/rdad018](https://doi.org/10.1093/restud/rdad018). Acesso em: 8 ago. 2026.
SANTOS SILVA, J. M. C.; TENREYRO, Silvana. The log of gravity. **The Review of Economics and Statistics**, \[*s. l.*\], v. 88, n. 4, p. 641–658, 2006. DOI: [https://doi.org/10.1162/rest.88.4.641](https://doi.org/10.1162/rest.88.4.641). Disponível em: [https://doi.org/10.1162/rest.88.4.641](https://doi.org/10.1162/rest.88.4.641). Acesso em: 8 ago. 2026.
SUN, Liyang; ABRAHAM, Sarah. Estimating dynamic treatment effects in event studies with heterogeneous treatment effects. **Journal of Econometrics**, \[*s. l.*\], v. 225, n. 2, p. 175–199, 2021. DOI: [https://doi.org/10.1016/j.jeconom.2020.09.006](https://doi.org/10.1016/j.jeconom.2020.09.006). Disponível em: [https://doi.org/10.1016/j.jeconom.2020.09.006](https://doi.org/10.1016/j.jeconom.2020.09.006). Acesso em: 8 ago. 2026.
TEUTLOFF, Ole; EINSIEDLER, Johanna; KÄSSI, Otto; BRAESEMANN, Fabian; MISHKIN, Pamela; DEL RIO-CHANONA, R. Maria. Winners and losers of generative AI: Early evidence of shifts in freelancer demand. **Journal of Economic Behavior & Organization**, \[*s. l.*\], v. 235, p. 106845, jul. 2025. DOI: [https://doi.org/10.1016/j.jebo.2024.106845](https://doi.org/10.1016/j.jebo.2024.106845). Disponível em: [https://linkinghub.elsevier.com/retrieve/pii/S0167268124004591](https://linkinghub.elsevier.com/retrieve/pii/S0167268124004591). Acesso em: 8 ago. 2026.
</content>
</page>