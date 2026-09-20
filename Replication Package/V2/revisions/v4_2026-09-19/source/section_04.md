# 4 Estratégia empírica
## 4.1 Abordagem de diferenças em diferenças
Uma referência para a estratégia empírica é o estudo de [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/). Os autores usam registros mensais da ADP, que processa a folha de mais de 25 milhões de trabalhadores nos Estados Unidos. Em vez de estimar cada vínculo separadamente, eles agregam o emprego em células de firma, quintil de exposição e mês e aplicam uma regressão de Poisson com efeitos fixos de firma por quintil e de firma por tempo ([Brynjolfsson; Chandar; Chen, 2025, p. 12](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/)). O principal resultado é uma queda relativa de 16% no emprego de trabalhadores de 22 a 25 anos nas ocupações mais expostas, enquanto os trabalhadores mais experientes nas mesmas ocupações permaneceram estáveis ou cresceram.
No Brasil, o equivalente mais próximo dessa base é o CAGED (Cadastro Geral de Empregados e Desempregados), estatística administrativa do Ministério do Trabalho e Emprego construída a partir de informações do eSocial, do CAGED e do Empregador Web. Desde janeiro de 2020, a maior parte das empresas cumpre a obrigação de informar admissões e desligamentos pelo eSocial, e os registros são consolidados mensalmente. Essa obrigatoriedade dá ao CAGED cobertura praticamente completa do mercado formal em frequência mensal, o que o torna adequado para acompanhar a porta de entrada e de saída do emprego, justamente a margem em que a literatura internacional tem encontrado os primeiros sinais de ajuste à IA. A adaptação ao Brasil, porém, exige duas ressalvas em relação ao artigo de referência. Primeiro, o CAGED observa fluxos formais de admissões e desligamentos, e não o estoque mensal de trabalhadores por firma. Segundo, a variação de exposição vem do índice da OIT aplicado à CBO, e não de quintis construídos sobre a classificação ocupacional americana. Por isso, o que se faz aqui é uma análise da dinâmica do emprego formal brasileiro em ocupações mais expostas, e não uma reprodução direta do painel firma-trabalhador do artigo de referência. 
A escolha do CAGED, em vez da PNAD Contínua (usada na Seção 3), decorre do que se quer medir. Aqui estão três justificativas para essa escolha.
Primeiro, a **frequência**: o CAGED é mensal e a PNADc é trimestral, e um estudo de eventos centrado em novembro de 2022 precisa de resolução mensal para separar o antes do depois, ao passo que, com dados trimestrais, o trimestre do evento é simultaneamente pré e pós. Segundo, a **natureza do registro**: o CAGED é registro administrativo de declaração obrigatória, com cobertura praticamente completa do mercado formal, enquanto a PNADc é amostra domiciliar complexa, cuja precisão não se sustenta em recortes por ocupação de quatro dígitos, em que muitas células teriam poucas observações por trimestre. Terceiro, e mais importante, **o objeto observado**: a PNADc mede o estoque de ocupados e o CAGED mede o fluxo de admissões e desligamentos, e a hipótese testada aqui é sobre contratação. O estoque só se move depois que o fluxo se move.
Essa escolha também tem limitações. O CAGED cobre apenas o mercado formal e registra fluxos, não o estoque de trabalhadores. Para observar dimensões que a base não alcança, uso a RAIS para medir o estoque anual de vínculos formais e a PNAD Contínua para examinar a informalidade. Esses dois exercícios são complementares e descritivos, sem identificação causal, e aparecem na Apêndice D. 
O desenho não capta a adoção direta de IA dentro das firmas, pois o CAGED não informa se uma empresa usa ChatGPT ou ferramentas semelhantes. O que se estima é se ocupações mais expostas passaram a apresentar evolução diferencial após a difusão da tecnologia. O choque temporal vem da difusão pública da IA, e a intensidade do tratamento vem da exposição ocupacional medida pela OIT. O evento escolhido nesta dissertação é o lançamento público do ChatGPT, em 30 de novembro de 2022, tratado como marco inicial da difusão dos LLMs (*Large Language Models*). Essa escolha dialoga com a literatura recente, mas não reproduz exatamente a datação de todos os estudos. [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) observam que a OpenAI introduziu o ChatGPT em novembro de 2022 e estimam um estudo de evento cujo período de referência é outubro de 2022. [Humlum e Vestergaard (2026, p. 12, nota 8)](https://doi.org/10.3386/w33777) identificam cinco estudos de evento centrados em novembro de 2022.
A literatura recente alerta que estimadores convencionais de diferenças em diferenças podem produzir comparações problemáticas quando a adoção é escalonada no tempo e os efeitos são heterogêneos ([Callaway; Sant'Anna, 2021](https://doi.org/10.1016/j.jeconom.2020.12.001); [de Chaisemartin; D'Haultfœuille, 2020](https://doi.org/10.1257/aer.20181169); [Sun; Abraham, 2021](https://doi.org/10.1016/j.jeconom.2020.09.006)). Esse problema específico não caracteriza o desenho usado aqui: todas as ocupações expostas passam a ser consideradas tratadas na mesma data, o lançamento do ChatGPT, e as ocupações não expostas permanecem como controle. Portanto, não há comparação entre grupos tratados mais cedo e mais tarde. A principal condição do desenho continua sendo outra: antes do evento, os grupos deveriam apresentar trajetórias paralelas. Os diagnósticos da Seção 5 mostram que essa condição não se sustenta, o que limita a interpretação causal.
## **4.2 Construção do painel ocupação-mês com CAGED e correspondência CBO → OIT**
Enquanto a PNAD Contínua utiliza a Classificação de Ocupações para Pesquisas Domiciliares (COD), o CAGED utiliza a Classificação Brasileira de Ocupações (CBO). Por isso, a unidade de análise desta etapa é a ocupação CBO de quatro dígitos observada mês a mês. A partir dos microdados do CAGED, construo para cada ocupação e mês medidas de admissões, desligamentos, saldo líquido e salários médios de admissão e desligamento.
O painel é construído a partir de uma única safra oficial do Novo CAGED, e a série de cada mês obedece à identidade `MOV + FOR − EXC`: as movimentações declaradas no prazo, mais as declarações fora do prazo, menos as exclusões. Todas as movimentações são reatribuídas ao **mês de competência do fato**, e não ao mês em que foram declaradas. O procedimento importa porque a incidência de declaração fora do prazo não é constante no tempo: usar apenas o arquivo de movimentações omitiria 8,6% dos registros de 2021 contra 1,3% dos de 2024, uma perda que cresce para trás e que se confundiria com tendência prévia. A série mensal assim reconstruída reproduz exatamente a série ajustada divulgada pelo Programa de Disseminação das Estatísticas do Trabalho (PDET) nos 65 meses, em admissões, desligamentos e saldo.
Três regras de tratamento completam a construção. Primeira, registros com salário fora do intervalo aberto entre zero e R\$ 1 milhão, idade fora da faixa de 14 a 90 anos, CBO inválida ou código de movimentação impossível são rejeitados antes da agregação. Ao todo, 3.574.530 de 252.838.929 linhas, ou 1,4%. Segunda, salário e composição são tratados como **ausentes**, e não como zero, quando o fluxo correspondente é nulo: há 403 células sem nenhuma admissão e 355 sem nenhum desligamento, e preenchê-las com zero faria a winsorização produzir salários plausíveis onde não houve contratação alguma. Terceira, a winsorização é aplicada no nível do registro, nos percentis 1 e 99, dentro de cada célula de CBO de quatro dígitos por ano, igualmente ao salário de admissão e ao de desligamento.
**Tabela 4.2.1 — Escopo do painel ocupação-mês**
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
> *Notas: o painel observado reúne todas as 630 famílias de CBO de quatro dígitos presentes na safra; a amostra principal retém apenas as 341 que entram no contraste entre expostas e não expostas. Os dois números são distintos e nomeados separadamente de propósito. \\*
A janela de análise começa em janeiro de 2021 por duas razões. Primeiro, o Novo CAGED teve início em janeiro de 2020, não havendo dados diretamente comparáveis para períodos anteriores. Segundo, optei por excluir o ano de 2020 porque ele coincide com a fase mais aguda da pandemia de Covid-19, marcada por fortes alterações nas admissões, nos desligamentos e nos salários. A inclusão desse período poderia fazer com que os efeitos excepcionais da pandemia fossem confundidos com as tendências anteriores à difusão do ChatGPT. Assim, o painel compreende o período entre janeiro de 2021 e maio de 2026, preservando 23 meses anteriores ao evento e 42 posteriores. A janela é assimétrica, com mais tempo depois do evento do que antes. [Klein Teeselink (2025, p. 11)](https://doi.org/10.2139/ssrn.5516798), por exemplo, adota uma janela de 15 meses de pré-tratamento e 30 meses de pós-tratamento.
O principal desafio metodológico é fazer a correspondência do CBO, usada nos registros administrativos brasileiros, com o índice da OIT, construído em ISCO-08. Para evitar uma correspondência ad hoc entre códigos numericamente parecidos, adotei uma ponte institucional em duas etapas. Primeiro, usei a tábua oficial do Ministério do Trabalho e Emprego que relaciona CBO 2002, CBO 94 e CIUO/ISCO-88. Em seguida, converti os códigos ISCO-88 para ISCO-08 por meio da tabela de correspondência da OIT. O caminho completo é, portanto: CBO 2002 → CBO94/CIUO88 via MTE → ISCO-08 via OIT → índice de exposição da OIT. A correspondência é mantida apenas quando existe uma ponte institucional identificável entre a família ocupacional brasileira e a classificação internacional. 
Das 629 CBOs avaliadas no crosswalk, 193 não tiveram uma correspondência oficial válida com a ISCO-08. Elas recebem o rótulo “sem pontuação disponível” (*No score*) e ficam fora da amostra principal. Isso não significa que tenham baixa ou nenhuma exposição, mas apenas que não foi possível atribuir uma pontuação confiável. A perda também não é uniforme, e não é unilateral: dirigentes e gerentes representam 19,2% das CBOs sem correspondência contra 2,8% das classificadas, uma sobre-representação de sete vezes, mas as ocupações elementares também são perdidas em excesso, com 9,3% contra 3,7%, enquanto trabalhadores da produção e operadores de instalações são retidos em excesso. Como a perda atinge tanto o topo quanto a base da estrutura ocupacional, de onde viriam respectivamente ocupações expostas e ocupações de controle, a direção do viés que ela introduz no contraste é indeterminada, e não sistematicamente adversa. 
Para as 436 CBOs com correspondência, uma mesma ocupação brasileira pode apontar para mais de um código ISCO-08. Nesses casos, agrego as pontuações disponíveis e aplico a regra da OIT, que considera tanto o nível médio quanto a dispersão da exposição. A diluição resultante não é simétrica entre os grupos: as famílias tratadas apontam, em média, para 2,89 destinos ISCO cada, contra 1,65 no grupo de controle. A agregação comprime, portanto, justamente as pontuações mais altas, o que atenua o contraste estimado e torna os coeficientes reportados adiante limites inferiores em magnitude, e não superiores. A Tabela 4.2.2 apresenta os grupos resultantes.
**Tabela 4.2.2 — Classificação das CBOs segundo o índice da OIT e definição de grupos de tratamento e controle.**
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
Nenhuma CBO de quatro dígitos ficou no Gradiente 4. Isso ocorre porque uma CBO pode reunir vários códigos ISCO-08 e a agregação reduz os valores mais extremos. A maior pontuação entre as 436 CBOs classificadas foi 0,5933, pouco abaixo do limite de 0,60 exigido para o Gradiente 4. Por isso, a análise principal reúne os Gradientes 1 a 3 como grupo exposto. O grupo vazio é consequência da regra de agregação, e não do mercado de trabalho brasileiro. Quando a pontuação de uma família é a média das pontuações de seus destinos ISCO, ela não pode exceder o máximo desses destinos, e o máximo observado é 0,5933. A demonstração está nas variantes pré-registradas: a variante que agrega pelo modo ponderado do rótulo nativo da OIT, em vez de pela média das pontuações, recupera três famílias no Gradiente 4. Não há, portanto, evidência de ausência de ocupações altamente expostas no Brasil; há uma regra de agregação que as dilui.
Essa diluição é atenuada pela forma como o grupo de tratamento foi definido. Reuni os Gradientes 1, 2, 3 e 4 em um único grupo de ocupações expostas. Assim, uma ocupação cuja pontuação foi diluída continua classificada como exposta, ainda que em um gradiente mais baixo do que teria sob uma correspondência perfeita. A contrapartida é que o crosswalk perde precisão dentro de cada gradiente: ele não sustenta, com segurança, análises que tratem os gradientes de forma isolada, comparando, por exemplo, o Gradiente 3 diretamente com o Gradiente 1. Por isso, a exposição é usada principalmente de forma binária, entre expostos e não expostos, e as análises por gradiente específico ficam em segundo plano.
Definido o grupo tratado, resta delimitar o controle. O modelo principal compara esse grupo tratado com as ocupações Not Exposed, que formam o controle estrito. O grupo Minimal Exposure fica fora do controle principal porque representa uma categoria intermediária: são ocupações com exposição média baixa, mas com alguma dispersão de tarefas potencialmente expostas. Incluí-las no controle poderia enfraquecer o contraste entre ocupações efetivamente não expostas e ocupações expostas. Por isso, Minimal Exposure entra apenas como especificação de robustez com controle ampliado.
O painel contém 630 famílias de CBO de quatro dígitos. Destas, 436 receberam uma correspondência oficial e uma pontuação de exposição, o que representa 69,2% das famílias e 70,7% das células de ocupação por mês. Embora a cobertura do número de ocupações seja parcial, essas CBOs concentram 92,3% dos fluxos de admissões e desligamentos observados. A Tabela 4.2.3 resume a distribuição por grupo de exposição.
**Tabela 4.2.3: Cobertura do painel por grupo de exposição**
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
## **4.3 Especificação econométrica e desfechos**
A especificação foi construída em etapas. Parti do desenho usado por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/), adaptei a comparação às características do CAGED e confrontei as escolhas de estimador, controles e inferência com a literatura metodológica. O objetivo foi escolher um modelo coerente com a pergunta e com os limites da base, e não procurar a especificação que produzisse o resultado mais favorável. As equações abaixo registram a versão adotada e permitem que essas decisões sejam avaliadas.
### Especificação comum às duas alternativas
Como os resultados têm formatos diferentes, a mesma comparação é estimada de duas formas. Admissões e desligamentos são contagens e podem ser zero; por isso, uso PPML. A primeira equação apresenta esse caso:
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
Esses controles tornam a comparação mais adequada, mas não garantem causalidade. Para interpretar $`\beta`$ como efeito, as trajetórias dos grupos precisariam ser paralelas antes do evento. Os diagnósticos apresentados na Seção 5 mostram que essa condição falha.
Além do modelo estático, estimo estudos de eventos que substituem a interação única $`\text{Exposta} \times \text{Pós}`$ por interações entre o tratamento e cada mês relativo ao evento:
$$
E\left[Y_{c,t} \mid \cdot\right] = \exp\left(\sum_{k=-23,\, k \neq -1}^{+41} \beta_k \, \mathbf{1}[t - t^{*} = k] \times \text{Exposta}_c + \alpha_c + \delta_t\right)
$$
No estudo de eventos, $`t^{*}`$ corresponde a dezembro de 2022 e $`k = -1`$ corresponde a novembro de 2022, o mês de referência. Cada coeficiente representa um mês, sem agrupar os extremos da série. Os meses anteriores mostram se os grupos já seguiam caminhos diferentes antes do evento; os meses posteriores descrevem como essa diferença evoluiu. Essa trajetória ajuda no diagnóstico, mas não prova causalidade por si só.
Idade média, participação feminina, escolaridade e composição racial dos admitidos não entram no modelo principal. Essas características podem mudar depois do evento e fazer parte do próprio resultado que se pretende observar. Controlá-las nesse momento poderia retirar parte dessa mudança. Por isso, elas aparecem separadamente na descrição da composição e em testes de robustez que usam medidas calculadas antes do evento.
O PPML é usado nas admissões e nos desligamentos porque essas contagens incluem zeros. Transformações do tipo $`\log(1+y)`$ alteram o estimando e podem ser arbitrariamente sensíveis à unidade de medida quando há efeito na margem extensiva ([Chen; Roth, 2024](https://doi.org/10.1093/qje/qjad054)). Separadamente, modelos log-lineares podem ser inconsistentes sob heterocedasticidade, o que motiva o uso de PPML ([Santos Silva; Tenreyro, 2006](https://doi.org/10.1162/rest.88.4.641)). O PPML trabalha diretamente com a contagem em nível e também é usado por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/). A estimação linear com $`\log(1+y)`$ permanece apenas como resultado secundário.
A mesma comparação é aplicada a quatro resultados principais: admissões, desligamentos, salário real de admissão e saldo líquido. A Tabela 4.3.1 apresenta a definição e a transformação usada em cada caso.
**Tabela 4.3.1: Desfechos da análise**
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
Por fim, a análise de heterogeneidade emprega uma diferença tripla, em que o painel passa a ser indexado também por subgrupo sociodemográfico $`g`$:
$$
Y_{c,g,t} = \beta_{\text{DDD}}\,(\text{Pós}_t \times \text{Exposta}_c \times \text{Grupo}_g) + \gamma_1 (\text{Pós} \times \text{Exposta}) + \gamma_2 (\text{Pós} \times \text{Grupo}) + \gamma_3 (\text{Exposta} \times \text{Grupo}) + \alpha_c + \delta_t + \theta_g + \varepsilon_{c,g,t}
$$
É importante separar os dois estimadores usados na Seção 5. O **DiD dentro do grupo** pergunta, por exemplo, se entre as mulheres as ocupações expostas mudaram de forma diferente das não expostas. O **DDD** pergunta se esse diferencial entre as mulheres é diferente do diferencial entre os homens. As tabelas do corpo apresentam o primeiro; o Apêndice A apresenta o segundo. Portanto, apenas o DDD testa uma diferença entre subgrupos. Como os diagnósticos de tendências prévias falham, os dois resultados permanecem exploratórios.
## **4.4 Heterogeneidades e estudos de caso**
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
As famílias A e B ficam separadas porque a família B apenas usa definições alternativas de grupos já testados na família A. Por exemplo, as faixas de 18 a 24 e de 22 a 25 anos são duas formas próximas de examinar trabalhadores jovens, não hipóteses independentes. Juntá-las trataria essas repetições como novos testes e distorceria a correção. A família C é separada por outro motivo: ela reúne os DiD estimados dentro de cada grupo, enquanto A e B reúnem contrastes DDD. O ajuste de Benjamini-Hochberg reduz os resultados que cruzam o limiar de 5% de 34 para 21 na família A, de 6 para 4 na B e de 54 para 40 na C.
Também defini seis estudos de caso ocupacionais: desenvolvedores de software, atendimento ao cliente, gerentes de marketing e vendas, supervisores de produção, estoquistas e repositores e auxiliares de saúde e cuidado. Os dois primeiros permitem uma comparação direta com o estudo de referência; os demais ampliam a análise para ocupações com perfis distintos. Esses casos são descritivos e não identificam mecanismos causais. Eles foram definidos antes da inspeção dos resultados, a partir das descrições oficiais das CBOs de seis dígitos, e reúnem 76 códigos sem sobreposição. A composição segundo a OIT é usada apenas na interpretação posterior.
## **4.5 Testes de robustez e diagnósticos**
Os testes a seguir foram definidos antes da estimação para mostrar quanto os resultados dependem das escolhas do desenho. Eles não validam automaticamente as estimativas: revelam sua sensibilidade e suas limitações. Esta subseção apresenta cada exercício; os resultados aparecem na Seção 5 e, de forma completa, no pacote de replicação.
1. **Escada de especificações.** Sete degraus pré-registrados: sem controles, composição pré-tratamento interagida com o pós, composição contemporânea, *Minimal Exposure* incorporada ao controle, exposição contínua padronizada, amostra restrita ao período a partir de 2022 e amostra truncada em dezembro de 2025.
2. **Placebo temporal.** Um evento falso é datado em dezembro de 2021 e estimado apenas dentro do pré-período verdadeiro, descartando-se todo o período posterior ao ChatGPT. O procedimento, ainda que com data distinta, pois aquele estudo situa seu evento falso em 30 de maio de 2022, é o mesmo de [Teutloff ](https://doi.org/10.1016/j.jebo.2024.106845)[*et al.*](https://doi.org/10.1016/j.jebo.2024.106845)[ (2025, p. 12)](https://doi.org/10.1016/j.jebo.2024.106845).
3. **Placebo de grupo.** Quinhentas reatribuições aleatórias do rótulo de tratamento, preservando o desenho de 75 ocupações tratadas entre 341, para situar o coeficiente observado na distribuição do que se obteria por acaso.
4. **Variantes de tratamento.** Quatro regras definidas previamente alteram a forma de combinar a pontuação média de exposição e sua dispersão entre os destinos ISCO.
5. **Medidas alternativas de exposição.** A safra de 2023 do índice da OIT, um consenso construído com GPT-4o e Gemini, e o índice de exposição da Anthropic.
6. **Sensibilidade a tendências prévias.** O procedimento de [Rambachan e Roth (2023)](https://doi.org/10.1093/restud/rdad018) avalia quão diferentes as violações pós-tratamento das tendências paralelas podem ser das pré-tendências antes que uma conclusão causal deixe de ser sustentada. Assim, o diagnóstico não se resume a aprovar ou reprovar o teste de tendências paralelas.
7. **Nível setorial.** Efeitos fixos de seção da CNAE por mês, tratados como especificação co-principal e não como robustez subordinada, conforme a Tabela 5.1.1.
8. **Influência ocupacional.** Um jackknife que remove cada uma das 75 ocupações tratadas, uma de cada vez, para verificar se o resultado depende de poucas ocupações grandes.
**Por que a exposição mínima fica fora do controle.** Excluí do grupo de controle as 95 CBOs de exposição mínima porque elas ocupam uma posição intermediária na escala. Incluí-las produziria um controle parcialmente exposto e reduziria o contraste por construção. A escada de especificações mostra quanto os resultados mudam quando essa escolha é invertida.
