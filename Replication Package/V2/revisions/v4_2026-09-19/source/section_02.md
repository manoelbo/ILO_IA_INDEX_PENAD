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
