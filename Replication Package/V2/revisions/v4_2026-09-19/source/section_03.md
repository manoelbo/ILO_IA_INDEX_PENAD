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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/e293fd6c-05a8-47c8-8aca-b0ee093f3113/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=94a4567bfadfcb89e2dd692a462b01e51c1c00c995f4583efaf24ddbe6f8d8a4&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A figura evidencia que, para uma mesma faixa de pontuação média, podem coexistir diferentes gradientes; entre 0,2 e 0,4, em particular, a exposição da população é mais heterogênea.
A Figura 3.2 resume a mesma informação em termos de contingente populacional por gradiente.
**Figura 3.2: População ocupada por gradiente de exposição à IA**
![]()
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/04f3793a-74c8-4d47-82d0-6a5085acbc8c/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=5f7faec14d4b99ade5a448b1751fb7a701feb1b19f6f7113d40892f6c43d017f&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<empty-block/>
A OIT estimou a proporção de trabalhadores com alta exposição à inteligência artificial (Gradientes 3 e 4) para diferentes grupos de países, o que permite uma comparação informativa com os dados encontrados neste estudo. A taxa de trabalhadores altamente expostos no Brasil (10,1%) fica ligeiramente acima da estimativa global da OIT (7,5%) e do padrão projetado para países de renda média-alta (7,0%). No entanto, a distância é expressiva quando comparamos o mercado brasileiro às economias de alta renda, em que a alta exposição atinge 17,3% da força de trabalho. Essa diferença reflete a estrutura ocupacional do país, caracterizada por um peso ainda expressivo de ocupações em setores de baixa exposição tecnológica, como a indústria de transformação tradicional e a agropecuária.
## **3.3 Ocupações mais expostas à IA**
Como o índice de exposição é construído no nível ocupacional, o ponto de partida natural é identificar quais ocupações estão no topo da distribuição. A Figura 3.3 mostra a composição da população ocupada por faixa de pontuação, segundo o grande grupo ocupacional.
**Figura 3.3: Composição da população ocupada por faixa de pontuação de exposição à IA, segundo o grande grupo ocupacional**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/de6695ff-4024-40a3-aea8-e9e92f611c5d/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=7dbb9b4d3c938a8df06843193959dd496c8e4ff0b0d657893c9bf8967e485fda&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
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
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/1373c5b8-11db-48c3-9b4e-2f5137efbaa0/image.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=58a86376f8fa8ea11b254a0c7636dd11de7ac7e3609c11fbb2390cb4fbc10a38&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
São Paulo concentra o maior contingente em termos absolutos: 2,8 milhões de trabalhadores, o que representa cerca de 12% da força de trabalho paulista. Esse resultado é esperado, pois o estado abriga a maior economia do país, com a maior concentração de sedes corporativas e serviços financeiros. Outros estados, como a Bahia, apresentam proporções consideravelmente menores, reflexo de uma estrutura ocupacional com maior peso de setores agrícolas, industriais e de serviços de baixa exposição.
O caso mais ilustrativo é o Distrito Federal. Apesar de ter uma força de trabalho relativamente pequena em termos absolutos, o DF apresenta a maior proporção de trabalhadores em alta exposição entre todas as UFs, consequência direta do seu perfil ocupacional: capital do país, com altíssima concentração de servidores públicos, analistas, profissionais técnicos e funções administrativas ligadas à máquina pública federal. É o caso em que a proporção diz mais do que o número absoluto.
A leitura conjunta do volume e da proporção mostra que a alta exposição à IA está distribuída por todo o território nacional, embora tenha maior peso relativo no Distrito Federal, no Rio de Janeiro e em São Paulo. Essas diferenças refletem, sobretudo, a composição ocupacional de cada estado e ajudam a localizar onde o potencial de exposição é maior. Elas não demonstram que a IA já tenha alterado o emprego ou os salários nessas regiões.
## **3.5 Perfil sociodemográfico**
Esta subseção caracteriza o perfil dos trabalhadores brasileiros mais expostos à IA . Como a exposição está concentrada em ocupações administrativas, técnicas e profissionais, ela não se distribui aleatoriamente entre os grupos sociais: decorre da posição dos trabalhadores na estrutura ocupacional. Os resultados mostram maior exposição entre trabalhadores mais escolarizados, mulheres, brancos, jovens e formais, além de concentração relevante nas faixas intermediárias de renda. Os recortes a seguir detalham esse padrão.
### **3.5.1 Análise por sexo**
A Figura 3.5 compara a exposição de mulheres e homens.
**Figura 3.5: Exposição à IA por sexo**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/be72584a-ec5f-4be2-9fdd-3ddc197b68d4/7c9d0510-dd42-485a-99f5-5c38939958ad.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=b80befdac010e662b51d4705b5178f0c5db3312a300ee16d5d0ccfb1c9565034&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A exposição média das mulheres (0,303) é 0,044 ponto maior do que a dos homens (0,259), uma diferença relativa de +17% sobre a média masculina. A leitura mais informativa, porém, não está na média, mas em como a população se distribui entre os níveis de exposição: 14,5% das mulheres ocupadas (6,1 milhões) estão em alta exposição (G3 e G4), contra 6,8% dos homens (3,6 milhões). Proporcionalmente, as mulheres são 2,2 vezes mais presentes na alta exposição do que os homens. A diferença por sexo é compatível com o padrão internacional documentado por [Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[ (2025, p. 43, Figura 20)](https://doi.org/10.54394/HETP0387): nos países de alta renda, 24,0% do emprego feminino e 11,6% do masculino situam-se nos Gradientes 3 e 4.
### **3.5.2 Análise por raça**
A Figura 3.6 apresenta o recorte racial.
**Figura 3.6: Exposição à IA por raça**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/ef4545d0-02af-4968-9a16-52ee00fffd7c/63487b0c-af82-47cd-a41b-47c4a7a09f4b.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=60e584e08b6602bb667e7c921590f72436f831e3a7f7e2e627939fbce9bc185f&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
O padrão racial é semelhante em magnitude, mas oposto à direção que se costuma esperar em análises de desigualdade: trabalhadores brancos têm exposição média de 0,305, contra 0,257 entre trabalhadores negros, definidos pela agregação de pretos e pardos conforme [Osorio (2003)](https://repositorio.ipea.gov.br/bitstreams/e09cc868-669f-4064-b396-693e22e0ce07/download), uma diferença relativa de +19% sobre a média negra. Em alta exposição, 12,5% dos brancos (5,2 milhões) estão expostos, contra 8,4% dos negros (4,5 milhões): os brancos são 1,5 vez mais presentes na alta exposição, mesmo sendo um contingente 11,9 milhões menor na força de trabalho ocupada (41,5 ante 53,4 milhões). A interpretação econômica se conecta diretamente ao que foi visto: as ocupações de alta exposição são, em sua maioria, *white collar* e, no Brasil, esse tipo de trabalho está historicamente associado a maior renda e escolaridade. O país carrega um legado de desigualdade racial, com uma estrutura de mercado de trabalho forjada em séculos de escravidão, que concentrou e ainda concentra grande parte da população negra em ocupações elementares, da construção, dos serviços domésticos e da indústria de transformação, setores de alto volume, baixa remuneração e baixa exposição à IA. 
### **3.5.3 Análise por faixa etária**
A Figura 3.7 descreve a exposição ao longo da idade.
**Figura 3.7: Exposição à IA por faixa etária**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/18134332-88f2-4a27-a749-36cc9eb9f465/305f57f1-ea80-4489-b48f-1458e3b2b0e6.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=624a62fc08846e44ffa6723d85c70a62e2a7186d1eadda182f9054e74c8c0ebf&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A exposição decresce de forma monotônica com a idade, partindo de 0,304 na faixa de 18 a 24 anos e caindo até 0,252 na faixa de 55 a 59 anos, uma diferença de 0,056 ponto, equivalente a +22% para os mais jovens em relação aos mais velhos. O contraste é ainda mais expressivo no segmento de alta exposição: a faixa de 18 a 24 anos tem 3,2 vezes mais trabalhadores em alta exposição (16,2%) do que a de 55+ (5,9%). Os jovens estão mais expostos por uma razão estrutural: ingressam preferencialmente em ocupações de apoio administrativo, vendas e serviços qualificados, justamente as mais expostas. Esse achado tem peso analítico relevante na segunda etapa desta dissertação, em que avalio se essa coorte mais exposta sofreu efeitos diferenciados após o lançamento do ChatGPT, padrão já documentado por [Brynjolfsson, Chandar e Chen (2025)](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/) nos Estados Unidos.
### **3.5.4 Análise por nível de escolaridade**
O gradiente educacional é o mais forte de todos os recortes individuais. A Figura 3.8 mostra esse padrão.
**Figura 3.8: Exposição à IA por nível de escolaridade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/bc60ec35-aa67-4e8f-ad52-3b662d104bac/7a88f2d4-6599-4c85-872e-1e9a7690de45.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=7b60436e3df42dbc94071f78035f81ea3c864575e09d6e1b9907d329bd75c2c4&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
A exposição média sobe de 0,179 entre trabalhadores sem instrução ou com fundamental incompleto para 0,275 entre os com médio completo (+54% em relação ao piso), 0,359 entre os com superior incompleto (+102%) e 0,364 entre os com superior completo (+105%), uma variação que mais que dobra a exposição ao longo da distribuição educacional. A interpretação é direta: a escolaridade abre acesso a ocupações de escritório, profissionais e técnicas, e essas são as mais expostas à IA.
### **3.5.5 Análise por renda**
A Figura 3.9 relaciona a exposição e a faixa de renda.
**Figura 3.9: Exposição à IA por faixa de renda**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/a18842f5-17d1-482b-9503-18ecfefc5819/acc6a675-2b6b-40d9-9c66-f87bd6614375.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=88c7b1b87dfc07d41b1d4aa1422bc10259241f4e466368fb77e7a47ac91c847b&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
O padrão central é que, embora a exposição média à IA aumente com a renda (de 0,237 na faixa até 1 salário mínimo para 0,365 em 5 ou mais), a **alta exposição** (Gradientes 3 e 4) não cresce indefinidamente: ela sobe de 7,6% na faixa mais baixa para cerca de 12,3% nas faixas intermediárias (1 a 3 salários mínimos) e depois **satura**, ficando praticamente estável mesmo entre os mais ricos. Esse resultado pede cautela na interpretação. Há uma leitura intuitiva, mas equivocada, de que seria a elite intelectual e financeira o grupo mais exposto à IA, afinal é ela que lida com as tarefas mais sofisticadas, digitais e baseadas em conhecimento. Os dados mostram outra direção. No *ILO Global Index*, a maior parte das ocupações do Gradiente 4 pertence a funções administrativas, como digitadores, operadores de processamento de texto, escriturários de contabilidade e escriturários de escritório geral ([Gmyrek ](https://doi.org/10.54394/HETP0387)[*et al.*](https://doi.org/10.54394/HETP0387)[, 2025, p. 40](https://doi.org/10.54394/HETP0387)). Acima desse patamar, a renda passa a refletir mais cargos de gestão e profissões liberais especializadas, que tendem a cair em exposição **moderada** (G1 e G2), não alta. O resultado é que a maior massa de trabalhadores em alta exposição está em salários de até 2 salários mínimos, cerca de dois terços do total, um segmento com menor capacidade de absorver choques. 
### **3.5.6 Análise por situação de formalidade**
A Figura 3.10 fecha os recortes com a situação de formalidade, que serve de ponte para a etapa empírica.
**Figura 3.10: Exposição à IA por situação de formalidade**
![](https://prod-files-secure.s3.us-west-2.amazonaws.com/07ecc8ca-4610-810a-aaa1-0003f557fbe1/f202a434-d610-4db8-b019-d5610ce848e6/09bebfba-37e6-4804-a4b0-4d8d0595c2ed.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAZI2LB466UWV2OSJD%2F20260919%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20260919T171107Z&X-Amz-Expires=300&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEJX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJHMEUCIQD0t4iHKPYEOHL3i8EXU0U3w9enmA%2FzuxmXmPkJIAbR3QIgVDai0OFXgYC1MXtQU5uUxp%2BIC8mMn1PeUGThTMQHH10q%2FwMIXhAAGgw2Mzc0MjMxODM4MDUiDEJ%2FQy%2F%2BcLG1PAF3LircA5Y2hamnl5hflZWo1VNe55KH0iyL18VVSPX9Ep4pKHvjf1UijhzBx8Ntx9FDPiHGq2oTeZI6KK9FAcfdSgagXaAk0y3R95016CvgH3EuKaPL7fknV%2BgipojTp83gzRJjmaeG4lrjk3a8xLwPaxIIZ6oyhKNPm2NXKeIkf2iLHRVGQLjpz%2BY6Gk2KCO0xgaJhIWNR1b1ZnW4FNPi2uwpNoNqxgXEuqSH8OrUraWQGk7vLGhOwg5EkoVG2YtUzZ%2B2kEePeZONWLB7ljuzlotwW15Niv9wDGoxo05gz7bG1BnJQlvMfWrV%2FMia6QS0cYXudMXzUzGwd8hso0u2iuo3edoZM%2Ftj4jrZRtdNMFoHcZ721gG9GByRFzO6BbIKGL2DiToUweZrOrYmLLsiDOogo1fQM6JESBU179QxX5QMJe3J2XoBem3nHyNWBa4nFKvNMcefjr2WAyymFpLgxSOnUGWf0O787jiTGPFFoHqQRSB7NdeZc8GuH9cUXLU7EeH62OoLBFL%2BBdi3OHE6tnOeE1rT84dyFM%2FzYMGVKYOBzfwSjXrayP8cBYo0nUb6uTNi5YBlXt3IY956P%2FAEUEmTtdzMrCkMKASvtTkRIkFpnFfDHb001J4iUeMRr6cszMLCKutUGOqUB7l%2BEl9H6VJEJOXjf1X0Stmi9ELPjOPcDio64H79M3U2iuM%2Bx2848eRhf%2FpOYCRlK3H89BLXypvbID2OrUI93b7dibQhTA20Gd0Ni2ybEGdEcfqioUMsWRCEIEIL3IVW0OWjoWYSAVNfNjY8PFt2D9TlHV7QJ0XF1JU88Gz6K4jWCy%2FFCULNN4zzemafcu62c6vVd3gOHGzF7frruEq%2BzFtYoZ1d1&X-Amz-Signature=1c4424ff52357983031248b3652cdc8c9c112b8291b3bd330ddefb9ce087c07e&X-Amz-SignedHeaders=host&x-amz-checksum-mode=ENABLED&x-id=GetObject)
<synced_block url="https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e#e90cc8ca4610828ca4550122ebb70126">
	A exposição média dos trabalhadores formais (0,305) é 0,046 ponto maior do que a dos informais (0,258), uma diferença relativa de +18% em relação à média informal. Novamente, o contraste é mais nítido na alta exposição: 14,8% dos formais (6,1 milhões) estão em ocupações de alta exposição (G3 e G4), contra apenas 6,7% dos informais (3,6 milhões). Em termos proporcionais, os trabalhadores com vínculo formal são 2,2 vezes mais presentes na alta exposição do que os informais. Apesar de a força de trabalho informal ser 32% maior do que a formal (54,6 ante 41,3 milhões de ocupados), os formais respondem por 63% dos 9,8 milhões em alta exposição (6,1 milhões) e os informais por apenas 37% (3,6 milhões).
</synced_block>
A interpretação é estrutural. Os trabalhadores formais, predominantemente empregados CLT em escritórios e na administração pública, se concentram justamente nas ocupações de alta exposição. 
## **3.6 Síntese e implicações para a análise com CAGED**
Esta análise descritiva permitiu três conjuntos de achados. Primeiro, a alta exposição à IA alcança cerca de 10,1% da força de trabalho ocupada (9,8 milhões de trabalhadores), patamar acima da média global estimada pela OIT, mas ainda distante das economias de alta renda. Segundo, essa exposição é ocupacional: se concentra em ocupações administrativas, de apoio, contábeis e de atendimento, e se distribui por praticamente todos os setores e estados, com destaque de intensidade para Finanças e Seguros e de volume para Serviços Profissionais e Administração Pública. Terceiro, porque decorre da posição na estrutura ocupacional, a exposição aparece de forma desigual entre os grupos sociais, sendo maior entre trabalhadores mais escolarizados, mulheres, brancos, jovens, formais e das faixas intermediárias de renda.
Esses achados motivam diretamente a próxima etapa. A PNAD oferece um retrato transversal: mede a exposição e caracteriza o perfil dos trabalhadores, mas não acompanha a dinâmica do emprego ao longo do tempo. Para investigar se a exposição à IA se traduz em mudanças efetivas no mercado de trabalho, é preciso uma base longitudinal do emprego formal. Isso é o que vamos fazer na próxima seção.
