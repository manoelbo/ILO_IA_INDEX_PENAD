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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/bc7a2b7c-918b-48cc-b18d-814e554e23a6/figure_5_1_national_event_studies.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=b7500350a786ca9d5d3a516f0e8816e8a8648db4087603fcfdf010b30f7f17d3&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/9dba5094-eeaa-4447-8e53-56041b378fa0/figure_5_2_1_1_sex_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=46f74b2be29b0d3e41b2591dd7fd247b2264e1d6533f5a1723ab3bebc5c48406&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura 5.2.1.2: Salário real de admissão — event study e trajetórias por sexo**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/f0048003-e495-4148-994f-63f869144d68/figure_5_2_1_2_sex_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=6bf9a27d8ed6fb82f8c590c78bd8fcb51429f830bd7b0666e5063c2d48df24c6&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/43569aa6-4fda-4f26-8bec-dda7e914784d/figure_5_2_2_1_race_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=421b93465d10e9dd5ea0fbb8315394a74de9251cee0eac8dd4aa7ed94ca6bc47&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura 5.2.2.2: Salário real de admissão — event study e trajetórias por raça/cor**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/a085e669-69fb-46ff-b89d-b5c38af8715b/figure_5_2_2_2_race_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=9de372cdf71bcaab69dc4cdf9172012b1619c6ba6a51203641ce6fb87e13bb3f&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/83d038a4-ea95-4dca-9499-6e98ef3e4670/figure_5_2_3_1_age_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=0440e3f42c4ceeddfaa38f96281fee9e06026d5865cdf9f83d1ee2e43ebecb23&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
**Figura 5.2.3.2: Heterogeneidade por idade — Salário real de admissão**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/f2ed0e44-a833-4aa6-a352-2a2b6a05f7f0/figure_5_2_3_2_age_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=c193c3914f135b1bcd39fb7bb4c57d2ecd4602389297dc7d81218ed89a29e7ce&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
<br>As figuras evidenciam comportamentos distintos entre as faixas, mas não estabelecem hierarquia etária causal.
Há uma exceção diagnóstica que merece ser mostrada. No DiD estimado **dentro** da coorte de 22 a 25 anos, o salário real de admissão apresenta diferencial de −0,0517, com p nominal de 1×10⁻⁶ e p ajustado de 4×10⁻⁵, e o teste conjunto de tendências prévias não é rejeitado, com p = 0,585. 
Essa é uma das duas únicas células, entre os cem contrastes estimados dentro dos grupos, cujo teste conjunto de tendências prévias não é rejeitado; a outra é o salário na categoria indígena, reportada no Apêndice A. Somados os três casos classificados como alerta, cinco dos cem contrastes escapam da classificação de falha, e outros cinco têm diagnóstico indefinido por deficiência de rank. Como não houve ajuste de multiplicidade para essa família de diagnósticos, um punhado de exceções é exatamente o que se espera por acaso quando cem testes são realizados. Por isso, trato o resultado como uma exceção que merece ser mostrada, não como uma validação do desenho. A Figura 5.2.3.3 mostra esse contraste isoladamente: os coeficientes pré-tratamento oscilam em torno de +0,0064, sem tendência e sem nenhum lead individualmente significativo a 5%, e a trajetória posterior se estabelece de forma persistente abaixo dessa média. A distância entre a linha tracejada e o pós-evento é de −0,0507, praticamente idêntica ao DiD de −0,0517 estimado dentro do grupo.
**Figura 5.2.3.3: Coorte de 22 a 25 anos — salário real de admissão**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/d38fc5a1-b553-4453-bdb4-cd486a06860c/2cd4f183-47b1-4136-8fed-c2e403155a78.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=f22ff1d691df6cdf29e1fcbeb1cee107569f2ea373b17a86dcfc5f48b1cc948f&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/60273f1e-707d-4f3a-a4b6-a57229a20808/figure_5_2_4_1_education_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=b709dbd44df52093858a48981be2cec18dea3594a3640a83d1b19648c54787e0&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
**Figura 5.2.4.2: Salário real de admissão — event study e trajetórias por escolaridade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/4fc552e5-f436-4e79-b799-ee9749a4e119/figure_5_2_4_2_education_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=b74e65a4b1dada4bd3729863aafc7fc4a268c4b43207db779e831905819c8683&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/230c0c5e-7145-4568-bd88-6a94acbd37cf/figure_5_2_5_1_income_admissions.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=96512b6e048ff28bb60cd14bf8da6d5fc30a9ea39aaf14e00120fb89691b65db&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A maior volatilidade da faixa superior decorre do pequeno número de ocupações: os coeficientes dependem de apenas 3 CBOs expostas e 7 não expostas, o que amplia a incerteza das estimativas.
A Figura 5.2.5.2 faz o mesmo para o salário real de admissão.
**Figura 5.2.5.2: Salário real de admissão — event studies e trajetórias por renda pré-tratamento**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/de949134-0684-4087-9a5f-7526bb134454/figure_5_2_5_2_income_wage.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=7319920698c910d9cb1eb88a16ed3da8befd57e69607e4c48ca59d15071d0fb4&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
Os coeficientes salariais oscilam em torno de zero e seus intervalos de confiança são amplos. Os testes conjuntos não rejeitam os pretrends nas duas primeiras faixas (p=0,417 e p=0,277), mas ambas são classificadas como falha porque apresentam três coeficientes pré-tratamento individualmente significativos. No topo, o teste conjunto é limítrofe (p=0,057) e gera alerta. Não há, portanto, evidência de heterogeneidade salarial robusta.
O resultado dialoga com a Subseção 3.5.5, que mostrou a alta exposição crescendo até as faixas intermediárias e depois se estabilizando. A comparação é indicativa, porque lá os trabalhadores são classificados por renda e aqui uso a mediana salarial da CBO. O padrão também converge em parte com [Klein Teeselink (2025)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5516798), que encontra maior ajuste nos segmentos de alta remuneração do Reino Unido e pouca alteração nos de baixa remuneração. A correspondência não é exata: aqui o sinal está na faixa intermediária e o topo não tem suporte. Já a ausência de contrastes salariais é compatível com [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/), que encontram ajustes mais visíveis no emprego do que na remuneração.
Não aparece uma heterogeneidade por renda sustentada pelo conjunto dos diagnósticos. Nenhum contraste DDD com suporte adequado permanece abaixo de 5% após o ajuste de multiplicidade. O único que cruza esse limiar é o salário na faixa acima de 5 salários mínimos, com coeficiente de +0,0643 e p BH de 0,043, mas o suporte é baixo: apenas 3 CBOs tratadas e 6 de controle, além de pré-tendência falha. A queda salarial de −0,0493 na faixa de até 2 salários mínimos é um DiD dentro do grupo e apenas reproduz o diferencial nacional; ela não demonstra que as faixas de renda respondem de modo diferente. Portanto, não há base para afirmar proteção do topo, compressão salarial ou redução diferencial do emprego líquido por faixa de renda.
### 5.2.6 Síntese das heterogeneidades demográficas
Dos **100 contrastes de diferença tripla, 34 são nominalmente significativos a 5% e 21 sobrevivem ao ajuste de Benjamini-Hochberg**. Os contrastes que permanecem se concentram em **raça/cor** e **faixa etária**; sexo e renda não apresentam diferenças ajustadas, e escolaridade fica próxima do limiar. Esses resultados são exploratórios porque as tendências prévias falham e o suporte varia entre células.
Os cinco eixos podem ser resumidos assim. **Sexo:** nenhum contraste de fluxo ou salário sobrevive ao ajuste. **Raça/cor:** os contrastes de fluxo mais negativos aparecem entre trabalhadores negros, sobretudo pardos, mas não identificam um efeito da tecnologia sobre esses grupos. **Idade:** os contrastes que sobrevivem são positivos e se concentram entre 41 e 49 anos, indicando uma diferença relativa, não proteção. **Escolaridade:** os contrastes do ensino superior ficam próximos do limiar, com p ajustado de 0,055 em admissões e desligamentos. **Renda:** nenhum resultado se sustenta com suporte adequado.
No salário de admissão, o diferencial negativo aparece em quase todos os grupos, mas apenas 2 dos 100 contrastes salariais de diferença tripla sobrevivem ao ajuste. As duas informações são compatíveis: há um padrão salarial disseminado entre grupos e pouca evidência de que sua magnitude difira entre eles. Como as tendências prévias também falham, esse padrão não recebe interpretação causal.
A **Figura 5.2.6** reúne os 130 contrastes de DiD estimados dentro dos grupos, organizados por desfecho, com intervalos ajustados por Benjamini-Hochberg e marcação das células de suporte `limited` e `thin`. Ela sintetiza a multiplicidade dos testes, a maior precisão do salário em relação aos fluxos e a raridade dos contrastes que permanecem após o ajuste.
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/d5337407-9dba-4b46-9b01-9d58fe1a48d3/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=e0bb57c29a853072589f5c79df4a6f20785dac9d01d8bab7d9555be8f0f70053&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
