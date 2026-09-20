# Dissertação V4: observações da professora e plano de revisão

Data: 19/09/2026

## Avaliação geral

**As observações pedem principalmente reorganização, explicações mais claras, cortes seletivos e uma separação melhor entre resultados, interpretação e conclusão. Não há pedido de novos dados, novos estimadores, novas regressões ou mudança da pergunta de pesquisa.**

Mas dizer que tudo é uma mudança puramente mecânica seria ir longe demais. Alguns trechos precisam de esclarecimento substantivo: o que significa significância estatística, o que o DDD compara, por que a identificação falha e como os resultados brasileiros dialogam com a literatura internacional. Posso preparar esses trechos; você revisa a interpretação e o tom. As figuras propostas e as estrelas de significância também exigem ajustes no código de apresentação, caso o pacote de replicação deva reproduzir a dissertação revisada.

O trabalho empírico existente continua sendo a base. Os comentários, por si só, não justificam mudar a estimação ou a construção dos dados. Isso não equivale a certificar que todo o código está correto: esta revisão leu o texto, partes da implementação e resultados salvos, sem executar novamente o pipeline nem realizar uma auditoria completa de replicação.

**Seu trabalho:** você não precisa reescrever essas seções do zero. Posso fazer a parte estrutural e preparar a primeira versão de todos os trechos delicados. Sua participação fica concentrada em revisar interpretações, escolher a ênfase e conferir se o texto continua com a sua voz.

## Escopo e fontes

A entrega desta etapa é apenas este levantamento. Não alterei a dissertação, a página do Notion, o código da análise, figuras, tabelas ou resultados de referência congelados.

O documento para a edição futura é a cópia [Dissertação de Mestrado V4 - Revisão](https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e). Li seu conteúdo em 19/09/2026, com foco nas Seções 4–6 e nas conexões com a introdução e os apêndices. Essa página é a referência para preservar sua redação. Este plano e a futura revisão do texto ficam em português, conforme seu pedido.

Fontes da professora, também fornecidas na conversa:

- **S-E:** [Observações seção estratégia empírica_Mané.docx](../../../Observações%20seção%20estratégia%20empírica_Mané.docx).
- **S-R:** [Observações sobre seção de resultados_Mané.docx](../../../Observações%20sobre%20seção%20de%20resultados_Mané.docx).
- **S-C:** [Observações sobre conclusão.docx](../../../Observações%20sobre%20conclusão.docx).

Extraí o texto dos três DOCX e conferi as observações. Não encontrei partes adicionais `comments.xml` nem inserções/exclusões registradas como controle de alterações. Foi uma leitura do conteúdo, sem revisão visual da diagramação desses arquivos.

As evidências técnicas consultadas estão vinculadas nas partes de consistência e código. Separei os achados dessa checagem dos pedidos da professora.

## Como ler as marcações

| Marcação | Quem executa | O que você precisa fazer |
|---|---|---|
| **SOZINHO** | Eu movo, resumo, organizo, ajusto títulos e confiro o material existente. | Nenhuma redação nova; apenas a leitura final habitual. |
| **RASCUNHO** | Eu preparo a primeira versão com base no seu texto e nas evidências existentes. | Revisar interpretação, ênfase e voz antes de finalizar o trecho. |
| **CONFERIR** | Eu verifico a consistência com resultados, equações e fontes existentes. | Decidir apenas se houver conflito entre as evidências ou dúvida real sobre a especificação pretendida. |
| **CÓDIGO-P** | Eu ajusto a geração de tabelas/figuras ou os registros de publicação. | Revisar a apresentação; isso não implica um novo desenho empírico. |

As marcações podem aparecer juntas. **RASCUNHO nunca significa que você recebe uma página em branco e precisa fazer a reescrita.** CONFERIR indica uma verificação, não um pedido automático de nova pesquisa ou novos cálculos.

Todos os itens desmarcados abaixo representam trabalho futuro. Esta etapa conclui o levantamento, não a implementação das mudanças.

## Como preservar seu jeito de escrever

- Mover os parágrafos existentes antes de reescrevê-los. Cortar repetições depois de definir os destinos.
- Manter seu vocabulário, exemplos concretos, explicações diretas e transições características. Encurtar retirando duplicações e detalhes dispensáveis, sem substituir seções inteiras por uma redação acadêmica genérica.
- Preservar a primeira pessoa nas escolhas de pesquisa quando ela combina com o texto. O pedido para retirar expressões avaliativas como “considero mais sério” é localizado; não exige tornar a dissertação inteira impessoal.
- Preservar a ideia central sobre a sobreposição entre ocupações expostas e trabalho de escritório/atendimento. Apresentar as explicações propostas como hipóteses, mantendo suas ressalvas.
- Manter números, sinais, unidades, grupos de comparação, fontes e incerteza junto das afirmações que qualificam. Registrar separadamente qualquer correção factual.
- Preservar a evidência completa nos apêndices ou no pacote ao encurtar o corpo. Não escolher o que mostrar porque o p-valor é mais favorável.
- Na entrega futura, distinguir texto movido, resumido, recém-redigido e corrigido. Concentrar sua revisão nas novas interpretações, não em cada parágrafo deslocado.

## Estrutura proposta para a dissertação

```text
4 Estratégia empírica
  4.1 Dados e construção do painel CAGED
  4.2 Correspondência CBO–OIT e definição dos grupos de exposição
  4.3 Desenho de identificação por diferenças em diferenças
  4.4 Especificações econométricas e desfechos
    4.4.1 Especificação principal
    4.4.2 Estudo de eventos
    4.4.3 Desfechos e transformações
    4.4.4 Inferência e especificações adicionais
  4.5 Heterogeneidades
  4.6 Diagnósticos, placebos e robustez

5 Resultados
  5.1 Resultados médios nacionais
  5.2 Diagnósticos e especificações complementares
    Especificação setorial co-principal
    Sensibilidade a tendências prévias
    Decomposição do diferencial salarial
    Robustez e placebos selecionados
  5.3 Heterogeneidades demográficas
    Sexo; raça/cor; idade; escolaridade; faixa salarial ocupacional; síntese

6 Discussão dos resultados
  6.1 Por que a estratégia empírica não entrega identificação causal?
  6.2 Como os resultados dialogam com a literatura internacional?
  6.3 O que os resultados médios podem esconder?
  6.4 O que aprendemos sobre as escolhas de mensuração?

7 Conclusão
  Texto corrido, sem subseções
```

Na 5.2, proponho começar com quatro aberturas de parágrafo em negrito. A professora aceita explicitamente essa alternativa aos subtópicos numerados. Numerar só se o tamanho final justificar. Na 5.3, proponho seguir a recomendação de priorizar os DDDs existentes, mantendo os DiDs dentro dos grupos como evidência complementar no apêndice.

### Mapa de deslocamentos

| Material atual | Destino | Operação principal |
|---|---|---|
| Justificativa do CAGED na 4.1; construção do painel, amostra e janela na 4.2 | 4.1 | Reunir a descrição dos dados e retirar repetição. |
| Crosswalk, classificação, exclusões e cobertura na 4.2 | 4.2 | Dar à correspondência uma subseção própria e coesa. |
| Comparação, evento, identificação e discussão de DiD escalonado na 4.1/4.3 | 4.3 | Separar o desenho conceitual da construção dos dados. |
| Equações nacionais, estudo de eventos, desfechos e inferência na 4.3 | 4.4.1–4.4.4 | Separar e explicar as especificações existentes. |
| Equação DDD ao fim da 4.3; atual 4.4 | 4.5 | Reunir motivação, estimandos, equação, multiplicidade e casos. |
| Atual 4.5 | 4.6; modelo setorial apresentado na 4.4.4 | Preservar os diagnósticos e remeter à especificação co-principal. |
| Tabela nacional e diagnóstico imediato de pré-tendências na 5.1 | 5.1 | Explicar o resultado central antes dos complementos. |
| Modelo setorial, HonestDiD, decomposição salarial e robustez na 5.1 | 5.2 | Organizar a evidência complementar em quatro blocos. |
| Comparações com a literatura na 5.1 e nas subseções demográficas | 6.2 | Organizar o diálogo por achado. |
| Atual 5.2 e tabelas DDD pertinentes do Apêndice A | 5.3 e Apêndice A reorganizado | Priorizar DDD; tornar os DiDs evidência de apoio. |
| Atual Figura 5.2.6 | Três figuras mais simples no apêndice | Separar admissões, desligamentos e salário de admissão. |
| Atuais 6.2–6.3, especialmente pandemia e interpretação macroeconômica | 6.1 | Preservar as explicações analíticas e qualificar seu alcance. |
| Atual 6.4 e interpretação das trajetórias/idade na 6.3 | 6.3, com comparações etárias selecionadas na 6.2 | Explicar limites da média e preservar contrapontos. |
| Atual 6.5 | 6.4 | Resumir o balanço das escolhas de mensuração. |
| Atual 6.1, limitações selecionadas da 6.2, agenda da 6.6 e fechamento | 7 | Construir uma conclusão curta em sete parágrafos. |

## Seção 4: pontos acionáveis

### E01 — Reunir dados e construção do painel

**Fonte:** S-E, proposta de 4.1. **Responsável:** SOZINHO. **Código:** nenhum.

- [ ] Mover para a 4.1 a justificativa do CAGED e sua comparação com a PNADc: frequência mensal, cobertura administrativa, detalhe ocupacional e fluxos versus estoque.
- [ ] Ordenar unidade CBO4 × mês, janela janeiro de 2021–maio de 2026, exclusão de 2020, `MOV + FOR − EXC`, atribuição ao mês de competência do fato, filtros, valores ausentes e winsorização no registro.
- [ ] Descrever os desfechos brutos construídos dos microdados e trazer a tabela de escopo do painel. Deixar transformações para a 4.4.3 e grupos de exposição para a 4.2.

**Concluído quando:** o leitor entende o que representa uma observação e como o painel foi construído antes de encontrar a identificação. Contagens e datas são preservadas ou explicitamente reconciliadas nos itens CONFERIR.

### E02 — Dar uma subseção própria ao crosswalk e aos grupos

**Fonte:** S-E, proposta de 4.2. **Responsável:** SOZINHO + CONFERIR. **Código:** nenhum previsto.

- [ ] Ordenar a explicação: correspondência institucional → agregação muitos-para-muitos → falta de pontuação e cobertura → categorias de exposição → tratamento e controle.
- [ ] Preservar CBO 2002 → CBO94/CIUO88 → ISCO-08 → índice OIT; exclusão das ocupações sem pontuação; diluição; ausência do Gradiente 4; e tabelas de classificação/cobertura.
- [ ] Explicar por que `Not Exposed` é o controle principal e `Minimal Exposure` fica de fora. Separar a regra que inclui Gradientes 1–4 da amostra observada, com Gradientes 1–3.
- [ ] Reconciliar os universos ocupacionais e revisar a força das afirmações sobre atenuação; ver F04 e F05.

**Concluído quando:** o leitor consegue reconstruir os grupos sem confundir ausência de pontuação com baixa exposição e sem alterar a regra de tratamento implementada.

### E03 — Explicitar o argumento de identificação

**Fonte:** S-E, proposta de 4.3. **Responsável:** SOZINHO para mover; RASCUNHO para esclarecer o argumento. **Código:** nenhum.

- [ ] Apresentar comparação expostas/não expostas, lançamento do ChatGPT em novembro de 2022, codificação efetiva do pré/pós, coeficiente de interesse e papel conceitual dos efeitos fixos de ocupação e mês.
- [ ] Explicitar a hipótese contrafactual de tendências paralelas: sem a difusão da IA generativa, ocupações expostas e não expostas teriam seguido trajetórias paralelas nos desfechos.
- [ ] Explicar que o coeficiente descreve um diferencial pós-evento associado à exposição ocupacional; os dados não medem adoção diretamente.
- [ ] Encurtar a discussão de DiD escalonado. A data comum elimina aquele problema específico de timing, mas tendências prévias e diferenças estruturais continuam centrais.

**Concluído quando:** comparação, hipótese de identificação, diagnósticos e limites da inferência ficam distintos. Você revisa apenas o novo trecho conceitual.

### E04 — Separar as equações principais e explicar seus termos

**Fonte:** S-E, proposta de 4.4.1. **Responsável:** SOZINHO + CONFERIR; RASCUNHO se houver correção conceitual de equação. **Código:** nenhum previsto.

- [ ] Apresentar especificações PPML e linear, com índices consistentes e definições logo abaixo.
- [ ] Explicar que o parâmetro de interesse é o coeficiente de exposição × pós nos dois casos; mudam estimador e transformação do desfecho.
- [ ] Manter PPML nas contagens, MQO no log do salário e no asinh do saldo; distinguir conversão exata `100 × (exp(beta) − 1)`, aproximação logarítmica e ausência de interpretação percentual direta do saldo em asinh.

**Concluído quando:** equações, definições, notas e contratos implementados descrevem os mesmos objetos.

### E05 — Separar o estudo de eventos e reconciliar sua janela

**Fonte:** S-E, proposta de 4.4.2. **Responsável:** SOZINHO + CONFERIR. **Código:** nenhum previsto para a divergência identificada.

- [ ] Apresentar a equação e explicar três funções: avaliar pré-tendências, possível antecipação e dinâmica pós-evento.
- [ ] Identificar dezembro de 2022 como tempo zero e novembro de 2022 como referência omitida.
- [ ] Distinguir amostra completa do modelo estático, janela balanceada do estudo de eventos e exercícios de horizontes longos. Resolver a divergência entre `+41` no texto e `+23` na implementação, descrita em F01.

**Concluído quando:** equação e amostra descritas correspondem ao resultado apresentado; o texto não sugere que todas as análises usam a mesma janela.

### E06 — Organizar desfechos, inferência e especificação setorial

**Fonte:** S-E, proposta de 4.4.3–4.4.4. **Responsável:** SOZINHO + CONFERIR; RASCUNHO para explicações ausentes. **Código:** nenhum previsto.

- [ ] Mover a tabela de desfechos para a 4.4.3 e distinguir admissões, desligamentos, fluxo bruto, salário real de admissão e saldo. Explicar por que a tabela nacional de destaque traz quatro desfechos e outros exercícios incluem fluxo bruto.
- [ ] Reunir efeitos fixos e agrupamento de erros por CBO na 4.4.4; conferir qualquer afirmação sobre pesos na implementação, sem acrescentá-los por suposição.
- [ ] Introduzir aqui a especificação existente de setor × mês como co-principal. Explicar a comparação dentro do mesmo setor e mês, mantendo seus limites de identificação.

**Concluído quando:** o status do modelo setorial é consistente entre método e resultados; nenhum peso, desfecho ou modelo novo foi introduzido silenciosamente.

### E07 — Reorganizar o método das heterogeneidades

**Fonte:** S-E, proposta de 4.5. **Responsável:** SOZINHO + RASCUNHO + CONFERIR. **Código:** nenhum previsto.

- [ ] Usar a sequência: motivação; grupos de sexo/raça/idade/escolaridade/faixa salarial ocupacional; DiD dentro do grupo versus DDD; equação DDD e índices; Benjamini–Hochberg; casos ocupacionais e localização no apêndice.
- [ ] Mover a equação DDD da atual 4.3. Conferir sua forma para cada estimador e a interpretação de grupo/complemento nos modelos existentes.
- [ ] Preservar famílias A, B e C e os ajustes existentes. Explicar partições alternativas de idade/raça sem confundi-las com a família principal.
- [ ] Manter os seis estudos de caso, sua seleção e seu caráter descritivo; remeter ao Apêndice C.

**Concluído quando:** o leitor entende qual comparação testa formalmente heterogeneidade e consegue ligá-la à nova seção de resultados.

### E08 — Preservar e enxugar os diagnósticos

**Fonte:** S-E, proposta de 4.6. **Responsável:** SOZINHO. **Código:** nenhum.

- [ ] Preservar os oito exercícios: escada de especificações, placebo temporal, placebo de grupo, variantes de tratamento, medidas alternativas de exposição, sensibilidade a tendências prévias, comparação setorial e influência ocupacional/jackknife.
- [ ] Para cada um, indicar a pergunta e onde o resultado aparece. Definir o modelo setorial na 4.4.4 e fazer uma remissão aqui, sem tratá-lo como robustez subordinada.
- [ ] Retirar a explicação repetida da exclusão de exposição mínima; manter sua versão definitiva na 4.2.

**Concluído quando:** as oito ideias continuam rastreáveis, sem duplicar definições nem antecipar toda a discussão dos resultados. As duas orientações da professora sobre o modelo setorial se conciliam por localização e remissão, sem inventar um oitavo teste substituto.

## Seção 5: pontos acionáveis

### R01 — Tornar o resultado nacional compreensível antes dos complementos

**Fonte:** S-R, 5.1. **Responsável:** SOZINHO + RASCUNHO. **Código:** nenhum além de R02.

- [ ] Manter a sequência: apresentar a Tabela 5.1 → explicar cada resultado e sua incerteza → apresentar o diagnóstico nacional de pré-tendências → delimitar a inferência.
- [ ] Explicar admissões e desligamentos como negativos e imprecisos, salário real de admissão como negativo e estatisticamente preciso, e saldo como negativo e impreciso. Explicar os intervalos de confiança e a comparação, em vez de apenas enumerar valores.
- [ ] Aproximar a figura nacional de estudo de eventos da discussão das pré-tendências. Mover diagnósticos alternativos detalhados para a 5.2 e interpretação econômica/literatura para a Seção 6.
- [ ] Encerrar dizendo que há diferenciais negativos, especialmente no salário, sem identificação causal. Não transformar imprecisão em evidência de ausência de efeito.

**Concluído quando:** a 5.1 responde às três perguntas da professora: resultado médio, precisão estatística e interpretação causal. Sua explicação original fornece a maior parte da redação.

### R02 — Recolocar estrelas e separar significância de identificação

**Fonte:** S-R, recomendação sobre estrelas. **Responsável:** SOZINHO + CÓDIGO-P. **Código:** formatação e notas das tabelas.

- [ ] Recolocar estrelas na Tabela 5.1 com os p-valores existentes. Aplicar a mesma distinção à tabela setorial co-principal, que também justifica a omissão de estrelas pela falha de pré-tendências.
- [ ] Manter erros-padrão, intervalos/p-valores e diagnósticos. Acrescentar uma nota curta dizendo que as estrelas indicam significância estatística segundo a inferência reportada, não validade causal.
- [ ] Nas tabelas de grupos, preservar estrelas calculadas pelos p-valores já ajustados por BH. Não trocar por estrelas nominais nem recalcular BH apenas sobre as linhas exibidas.

**Concluído quando:** o salário pode aparecer como estatisticamente significativo enquanto a falha de identificação continua visível; as estrelas reproduzem os limites declarados. Recolocar estrelas é uma recomendação da professora, não um pedido para mudar estimação ou suprimir diagnósticos.

### R03 — Criar a subseção de resultados complementares

**Fonte:** S-R, proposta de 5.2. **Responsável:** SOZINHO. **Código:** títulos e remissões, quando gerados.

- [ ] Criar quatro blocos: especificação setorial co-principal; sensibilidade a tendências prévias; decomposição salarial; principais exercícios de robustez e placebos.
- [ ] Transferir o material existente na 5.1, preservando fontes e remissões aos apêndices.
- [ ] Abrir cada bloco com sua pergunta e encerrar com o que o resultado muda em magnitude, precisão ou identificação.

**Concluído quando:** a 5.1 fica menor sem perda de evidência, e a 5.2 é compreensível sem consultar o pacote inteiro.

### R04 — Explicar o que a comparação setorial acrescenta

**Fonte:** S-R, proposta de 5.2.1 e parágrafo de exemplo. **Responsável:** SOZINHO + RASCUNHO. **Código:** apresentação por R02/P03.

- [ ] Explicar por que diferenças nacionais podem refletir composição setorial e o que os efeitos de setor × mês absorvem.
- [ ] Trazer a tabela nacional/setorial, explicar as mudanças em fluxos, salário e saldo, e preservar as falhas de pré-tendências.
- [ ] Adaptar o exemplo da professora usando sua redação existente. Não sugerir que acrescentar efeitos setoriais resolve a identificação ou identifica mecanicamente uma parcela causal de composição setorial.

**Concluído quando:** o modelo co-principal informa a comparação e seus limites aparecem junto dos resultados.

### R05 — Explicar a sensibilidade sem misturar estimandos

**Fonte:** S-R, proposta de 5.2.2. **Responsável:** SOZINHO + RASCUNHO + CONFERIR. **Código:** nenhum previsto.

- [ ] Mover a interpretação de Rambachan–Roth/HonestDiD e explicar sua pergunta em linguagem acessível.
- [ ] Distinguir o coeficiente salarial estático da média pós-evento do estudo de eventos. Preservar o significado de `M = 0` e da sensibilidade à curvatura para o estimando efetivamente analisado.
- [ ] Deixar as saídas técnicas e grades completas no apêndice, com informação suficiente no corpo para entender o resultado.

**Concluído quando:** um intervalo de sensibilidade referente a um estimando não é apresentado como intervalo de outro.

### R06 — Mover e esclarecer a decomposição salarial

**Fonte:** S-R, proposta de 5.2.3. **Responsável:** SOZINHO + RASCUNHO. **Código:** nenhum previsto.

- [ ] Trazer a decomposição por escolaridade/composição, distinguindo salários dentro das categorias e perfil dos novos contratados.
- [ ] Explicar os 23% e aproximadamente 29% existentes com suas respectivas especificações e denominadores. Manter o salário-hora se ele ajudar a interpretar esse bloco.
- [ ] Preservar a ressalva não causal e as tabelas detalhadas do Apêndice A; não transformar a parcela de decomposição em mecanismo comprovado de ajuste à IA.

**Concluído quando:** fica claro o que foi decomposto e o que essa decomposição não permite afirmar.

### R07 — Selecionar a robustez principal e preservar os detalhes

**Fonte:** S-R, proposta de 5.2.4. **Responsável:** SOZINHO para propor a seleção; RASCUNHO para a ênfase interpretativa. **Código:** nenhum teste novo solicitado.

- [ ] Propor uma seleção curta a partir das perguntas da 4.6: janela amostral, definição do controle, placebo temporal e concentração/influência quando informativas. Isso é uma proposta editorial minha, não uma instrução adicional da professora.
- [ ] Incluir evidência que qualifique a narrativa, não apenas resultados favoráveis. Explicar por que um placebo ou p-valor menor não estabelece identificação.
- [ ] Mapear detalhes retirados para o apêndice adequado e manter as saídas completas no pacote. Evitar repetir as discussões setorial e de HonestDiD.

**Concluído quando:** as sensibilidades mais importantes ficam visíveis e cada diagnóstico existente tem um destino identificável.

### R08 — Tornar o DDD a evidência principal das heterogeneidades

**Fonte:** S-R, proposta de 5.3. **Responsável:** SOZINHO + RASCUNHO + CONFERIR; CÓDIGO-P se as tabelas forem reformatadas.

- [ ] Preservar e adaptar o guia inicial: DiD dentro do grupo compara ocupações expostas/não expostas naquele grupo; DDD pergunta se esse diferencial difere daquele do grupo de comparação especificado.
- [ ] Trazer do Apêndice A os DDDs pertinentes. Mover as tabelas atuais de DiD dentro dos grupos para o apêndice, mantendo referências seletivas quando ajudam a explicar o sinal do DDD.
- [ ] Organizar os cinco recortes por DDD, p-valores ajustados, suporte e pré-tendências. Distinguir partições principais e alternativas de idade/raça e dizer se a comparação é com um grupo específico ou com todo o complemento.
- [ ] Preservar resultados nulos/imprecisos e exceções. Distinguir significância de suporte adequado e identificação; ver F03.
- [ ] Rever as figuras por sua função. Mover exibições redundantes de DiD para posições de apoio, preservando diagnósticos úteis e explicações das exceções.

**Concluído quando:** tabelas e texto principais respondem à heterogeneidade entre grupos, sem renomear DiD como DDD nem sugerir que basta subtrair DiDs estimados separadamente para recriar o DDD ajustado. A professora permite manter a organização anterior; priorizar DDD é a opção recomendada para esta revisão.

### R09 — Substituir a figura muito densa de heterogeneidades

**Fonte:** S-R, Figura 5.2.6. **Responsável:** SOZINHO + CÓDIGO-P. **Código:** geração e registro das figuras.

- [ ] Criar três figuras mais simples no apêndice com as estimativas existentes: admissões, desligamentos e salário real de admissão.
- [ ] Manter grupos legíveis, distinguir recortes demográficos, identificar estimador e convenção dos intervalos, e preservar marcadores de suporte e ressalva causal.
- [ ] Preservar o ajuste BH original da família C com 130 testes, mesmo exibindo um desfecho por figura. Manter fluxo bruto e saldo disponíveis nas tabelas completas/pacote.
- [ ] Descrever as figuras como sínteses complementares dos DiDs dentro dos grupos, úteis para interpretar os DDDs, e não como teste principal de heterogeneidade.

**Concluído quando:** cada figura é legível no tamanho da dissertação e reproduz os dados de origem. Separar a exibição não cria estimativas nem famílias de multiplicidade novas.

## Nova Seção 6: pontos acionáveis

### D01 — Discutir os limites de identificação

**Fonte:** S-C, proposta de 6.1. **Responsável:** SOZINHO para mover; RASCUNHO para revisar o argumento. **Código:** nenhum.

- [ ] Reaproveitar a atual 6.3 e partes da 6.2 sobre início em janeiro de 2021, ausência de pré-pandemia comparável, recuperação do mercado e diferenças estruturais entre grupos.
- [ ] Manter a concentração do grupo exposto em escritório, atendimento, recepção, telemarketing e vendas. Preservar a ideia da sobreposição entre exposição e a fronteira escritório/atendimento versus trabalho manual/presencial.
- [ ] Explicar pandemia, ciclo macroeconômico e composição ocupacional como explicações concorrentes plausíveis. Não afirmar que o desenho identifica qual delas causou o diferencial.
- [ ] Retirar expressões avaliativas pontuais como “considero mais sério”, mantendo seu raciocínio concreto. Preservar contrapontos, inclusive que controlar uma tendência linear prévia não elimina mecanicamente as estimativas.

**Concluído quando:** a discussão explica por que a identificação importa, sem converter hipóteses em achados estabelecidos nem repetir apenas uma lista de limitações.

### D02 — Organizar o diálogo internacional por achado

**Fonte:** S-C, proposta de 6.2; S-R, deslocamento das comparações. **Responsável:** RASCUNHO + CONFERIR. **Código:** nenhum.

- [ ] Reunir comparações existentes nos resultados nacionais, recortes demográficos e conclusão.
- [ ] Preparar quatro blocos conectados, seguindo as perguntas abaixo. Fazer uma síntese, sem reabrir uma revisão artigo por artigo.
- [ ] Conferir afirmações e versões dos artigos já citados antes de finalizar os novos trechos. Não foi feita uma nova busca bibliográfica nesta etapa de levantamento.
- [ ] Preservar diferenças de país, amostra, medida de exposição/adoção, desfecho, período e diagnóstico. Não chamar comparações entre estimandos distintos de replicação, confirmação ou contradição apenas pelo sinal.

| Bloco | O que o texto deve estabelecer | Cuidado principal |
|---|---|---|
| Efeito médio no emprego | Situar a ausência de evidência causal robusta nos fluxos nacionais diante dos resultados mistos das referências já utilizadas. | Falta de identificação não prova ausência de efeito tecnológico; fluxos, estoque e vagas são diferentes. |
| Jovens e início de carreira | Comparar os contrastes brasileiros com a ênfase em jovens/juniores de Brynjolfsson, Chandar e Chen e Hosseini Maasoum e Lichtinger. Ligar maior exposição dos jovens na Seção 3 à ausência de queda adicional clara de admissões na Seção 5 e aos contrastes positivos de 41–49 anos. | Exposição, idade e senioridade não são equivalentes; DDD positivo não demonstra proteção ou aumento do emprego. |
| Salários | Explicar por que salário de admissão é a margem nacional mais precisa e comparar com as margens efetivamente medidas nos outros estudos. | Salário de admissão, remuneração de empregados, salário anunciado e rendimentos não são intercambiáveis; precisão não estabelece causalidade. |
| Pré-tendências e identificação | Discutir o ponto da professora sobre o diagnóstico do estudo de referência depender da medida de exposição e relacioná-lo à falha mais abrangente no Brasil. | Conferir versão e afirmação específica sobre cada medida; não sugerir que toda a literatura tem o mesmo problema. |

**Concluído quando:** a seção mostra aproximações, diferenças e limites de comparação, e você revisou o primeiro rascunho quanto à ênfase e à voz.

### D03 — Explicar o que médias e trajetórias estáveis podem esconder

**Fonte:** S-C, proposta de 6.3 e deslocamento de interpretação. **Responsável:** SOZINHO + RASCUNHO + CONFERIR. **Código:** nenhum previsto.

- [ ] Reaproveitar a atual 6.4 sobre ocupações pequenas e o exemplo de tradutores/intérpretes. Conferir o alcance das afirmações sobre ponderação e contribuição aproximada no estimador correspondente.
- [ ] Reaproveitar a discussão das trajetórias pós-evento estáveis, dos casos ocupacionais e da diferença entre mudanças agregadas e específicas.
- [ ] Preservar que estabilidade não demonstra ausência de substituição e que uma estimativa agregada imprecisa não refuta mudanças em ocupações particulares.
- [ ] Manter recomposição de tarefas, complementaridade e experiência como hipóteses. Deixar trajetórias detalhadas no Apêndice C; preservar as ressalvas de RAIS/PNADc quando limitam a interpretação dos fluxos.

**Concluído quando:** a seção explica o alcance da pergunta agregada sem apresentar exemplos ou estabilidade como mecanismo identificado.

### D04 — Resumir o balanço das escolhas de mensuração

**Fonte:** S-C, proposta de 6.4. **Responsável:** SOZINHO + RASCUNHO + CONFERIR. **Código:** nenhum previsto.

- [ ] Reaproveitar a atual 6.5 sobre índice OIT, CAGED, cobertura do crosswalk, agregação muitos-para-muitos e limites de mensuração.
- [ ] Manter o que cada escolha permite e o que custa; cortar defesas metodológicas já apresentadas na Seção 4.
- [ ] Preservar as distinções entre coeficientes de exposição contínua/binária, amostras diferentes e controles alternativos quando necessárias à comparação.
- [ ] Deixar os aprendizados na Seção 6, os números detalhados de sensibilidade na 5.2/apêndice e a construção na Seção 4. Rever a direção atribuída ao erro de mensuração em F05.

**Concluído quando:** o leitor avalia contribuição e limitações da adaptação brasileira sem reler todo o método.

## Nova Seção 7: pontos acionáveis

### C01 — Montar uma conclusão curta em texto corrido

**Fonte:** S-C, instruções sobre a conclusão. **Responsável:** SOZINHO para cortar/mover; RASCUNHO para a versão completa. **Código:** nenhum.

- [ ] Retirar as subseções atuais e usar a sequência de sete parágrafos abaixo.
- [ ] Reaproveitar sua redação, especialmente a síntese descritiva/empírica e o fechamento. Escrever apenas as conexões e a síntese que faltarem.
- [ ] Deixar interpretação detalhada de pandemia/macroeconomia, defesa metodológica, trajetórias e comparações na Seção 6.

| Parágrafo | Conteúdo | Material existente para reaproveitar |
|---|---|---|
| 1 | Objetivo e duas perguntas da pesquisa. | Introdução; síntese final atual. |
| 2 | Principal achado descritivo sobre exposição e sua distribuição. | Primeiro parágrafo da atual 6.1. |
| 3 | Resultado nacional: fluxos negativos e imprecisos, diferencial salarial mais preciso, falha de identificação. | Atual 6.1 e fechamento da 6.6. |
| 4 | Síntese breve das heterogeneidades, com ressalvas de suporte e inferência. | Atuais 6.1 e 5.2.6, corrigidas conforme F02/F03. |
| 5 | Limitações de forma compacta. | Trechos selecionados da atual 6.2. |
| 6 | Quatro direções principais de pesquisa. | Trechos selecionados da atual 6.6. |
| 7 | Contribuição: mensuração adaptada, evidência distributiva e limites documentados da inferência causal com os dados disponíveis. | Fechamento atual, orientado pelo exemplo da professora. |

- [ ] Preservar todos os temas de limitação citados: exposição não é adoção; identificação causal não foi alcançada; CAGED cobre fluxos formais; crosswalk introduz perda/erro de mensuração; e janela iniciada em 2021 sem pré-pandemia comparável.
- [ ] Resolver a pequena ambiguidade de contagem: a professora diz “quatro” limitações, mas cita cinco temas. Organizar em quatro blocos compactos, agrupando crosswalk e janela, sem omitir nenhum. Aplicar a limitação do CAGED à análise principal, reconhecendo os complementos de RAIS/PNADc quando necessário.
- [ ] Manter quatro prioridades na agenda final: medir adoção efetiva, acompanhar trabalhadores, estender o horizonte e melhorar a mensuração ocupacional.
- [ ] Mover detalhes da agenda espacial e de ocupações específicas para discussão/apêndice quando úteis. Eles podem sair da conclusão sem desaparecer do projeto.

**Concluído quando:** a Seção 7 responde a objetivo, achados, limites e agenda em texto corrido, sem resultado novo nem repetição de tabelas. Você revisa a conclusão completa que eu preparar, com os trechos originais identificáveis.

## Pontos de consistência encontrados nesta revisão

Estes itens **não são pedidos adicionais da professora**. Surgiram ao conferir se a reorganização poderia reaproveitar o conteúdo atual com segurança. São correções ou verificações delimitadas, não uma proposta para reabrir o trabalho empírico.

### F01 — O limite do estudo de eventos no texto difere da implementação

**Situação:** divergência confirmada. **Responsável:** CONFERIR, depois SOZINHO para corrigir com base na fonte. **Impacto no código:** nenhum indicado por enquanto.

A atual 4.3 do Notion apresenta uma soma até `+41`. A [implementação](../code/caged/models/event_study.py) define `EVENT_TIME_MAX = 23`, e o [registro do estudo de eventos salvo](../results/reference/artifacts/caged/models/event_study_support.json) informa `-23...+23`, com novembro de 2022 omitido. O [contrato de pesquisa](../RESEARCH_DESIGN.md) distingue essa janela balanceada do modelo estático e dos exercícios de horizontes longos.

- [ ] Associar cada equação/figura à sua saída efetiva e corrigir a descrição. A solução provável é explicar corretamente as janelas existentes, em vez de mudar a estimação para corresponder a uma equação descrita incorretamente.

### F02 — Uma nota gerada usa o denominador errado para os DDDs salariais

**Situação:** erro confirmado no texto de apresentação. **Responsável:** SOZINHO + CÓDIGO-P. **Impacto no código:** nota explicativa gerada, não resultados estimados.

O texto repete “2 dos 100 contrastes salariais”. Os [resultados salvos da família A](../results/reference/artifacts/caged/diagnostics/ddd_multiplicity_results.csv) contêm 100 testes em cinco desfechos, **20 testes salariais** e **2 rejeições salariais** após o ajuste BH da família original. Em [phase8b_common.py](../code/render/phase8b_common.py), `mandatory_interpretation_note` multiplica `family_a_wage_tests` por cinco e chama o total de contrastes salariais.

- [ ] Corrigir texto e gerador para distinguir “2 de 20 contrastes salariais” de “100 testes na família A”. Preservar o ajuste BH sobre os 100 testes. Revisar verificações associadas e outras notas que repetem a redação.

### F03 — Algumas sínteses amplas de heterogeneidade apagam exceções

**Situação:** confirmada no texto e nas saídas salvas da família A. **Responsável:** RASCUNHO + CONFERIR. **Impacto no código:** nenhum na estimação; eventualmente em sínteses geradas.

A síntese/conclusão às vezes afirma que sexo e renda não têm diferenças ajustadas e que escolaridade fica apenas perto do limiar. Essas frases são mais amplas do que os resultados detalhados:

- O contraste de sexo no saldo sobrevive a BH, com sinais opostos nas duas orientações de comparação; a limitação de pré-tendências permanece.
- O DDD salarial da faixa ocupacional de renda mais alta sobrevive a BH, mas tem suporte baixo e não sustenta uma afirmação substantiva ampla.
- Ensino superior apresenta rejeições ajustadas em fluxo bruto e saldo, enquanto admissões/desligamentos ficam pouco acima de 5%.

- [ ] Reescrever as sínteses nomeando desfecho e limitação. Uma síntese curta pode destacar admissões, desligamentos e salário e indicar onde estão os demais desfechos; não deve declarar ausência de todas as rejeições ajustadas. Não contar orientações opostas de um contraste binário como achados substantivos diferentes.

**Evidência:** atuais 5.2.1, 5.2.4–5.2.6 e 6.1 do Notion; [resultados salvos da família A](../results/reference/artifacts/caged/diagnostics/ddd_multiplicity_results.csv).

### F04 — Regras de tratamento e universos ocupacionais precisam de redação consistente

**Situação:** diferenças observadas que precisam ser identificadas e reconciliadas. **Responsável:** CONFERIR + SOZINHO. **Impacto no código:** nenhum indicado por enquanto.

O texto usa 629 ocupações/193 sem pontuação no crosswalk e 630 ocupações/194 sem pontuação no painel observado. A [cobertura salva do crosswalk](../results/reference/artifacts/caged/reconciliation/crosswalk_coverage.json) confirma o universo 629/193. O texto também alterna entre Gradientes 1–3 e 1–4; o [contrato](../RESEARCH_DESIGN.md) define 1–4, enquanto o Gradiente 4 observado está vazio.

- [ ] Nomear os universos e explicar cada denominador. Confirmar a ocupação adicional do painel nos dados de origem antes de mudar qualquer número. Separar regra de classificação e amostra observada. Isso não pede excluir/incluir ocupações ou alterar o tratamento.

### F05 — Afirmações interpretativas fortes precisam de ressalva ou justificativa

**Situação:** trechos que exigem revisão, não um novo defeito demonstrado do modelo. **Responsável:** RASCUNHO + CONFERIR. **Impacto no código:** nenhum previsto.

A atual 4.2 afirma que a diluição do crosswalk torna os coeficientes limites inferiores em magnitude. A 6.3 contém afirmações categóricas sobre explicações pandêmicas/macroeconômicas; a 6.6 sugere que medir adoção permitiria finalmente separar tecnologia e ciclo.

- [ ] Revisar essas afirmações antes de movê-las. Distinguir compressão das pontuações de exposição de um limite demonstrado para o coeficiente da regressão; explicitar as hipóteses necessárias para sustentar esse limite.
- [ ] Manter explicações pandêmicas/macroeconômicas condicionadas à evidência disponível e preservar os contrapontos existentes.
- [ ] Apresentar mensuração de adoção como aprimoramento de um desenho futuro, sem sugerir que observar adoção, por si só, garante identificação causal.

Esses são exemplos de trechos em que eu preparo uma primeira versão cuidadosa e você revisa o significado. Eles não exigem, por si só, uma regressão nova.

### F06 — Alguns rótulos de diagnóstico podem se referir a versões ou amostras diferentes

**Situação:** reconciliação necessária. **Responsável:** CONFERIR. **Impacto no código:** apenas se a conferência revelar um defeito adicional no gerador.

A subseção de renda mistura contagens de suporte e descreve um p-valor conjunto de pré-tendência salarial de 0,057/“alerta” para renda alta. O [contrato de pesquisa atual](../RESEARCH_DESIGN.md) registra os diagnósticos de pré-tendência do grupo-alvo de renda alta como indefinidos por deficiência de posto, preservando os coeficientes do estudo de eventos. Podem ser especificações ou versões diferentes; não devem ser tratadas silenciosamente como o mesmo resultado.

- [ ] Associar cada afirmação ao modelo, amostra e diagnóstico salvo exatos antes de resumir. Preservar o status indefinido/deficiência de posto quando aplicável, sem descrevê-lo como aprovação ou rejeição de um teste conjunto calculado.

## Código: o que precisa mudar e o que não precisa

**O feedback da professora não pede mudanças na construção dos dados, no algoritmo do crosswalk, na seleção da amostra, nos estimadores, nos coeficientes ou nas famílias de multiplicidade.** As saídas de DDD, DiD dentro dos grupos, especificação setorial, decomposição, placebos e sensibilidade já existem para a reorganização. Esta checagem encontrou trabalho de apresentação e divergências textuais; não estabeleceu necessidade de nova estimação.

| ID | Ação técnica prevista | Classificação | Arquivos/saídas prováveis | Verificação |
|---|---|---|---|---|
| P01 | Recolocar estrelas nas tabelas nacional e setorial; corrigir notas que ligam sua ausência à falha de pré-tendências. | CÓDIGO-P; necessário se adotarmos a recomendação e mantivermos a reprodução pelo pacote. | [phase8b_tables.py](../code/render/phase8b_tables.py), função existente [significance_stars](../code/render/phase8b_common.py). | Coeficientes, erros-padrão, p-valores e diagnósticos preservados; estrelas coerentes com a fonte nominal/BH declarada. |
| P02 | Gerar três figuras separadas a partir dos dados existentes de DiD dentro dos grupos. | CÓDIGO-P; necessário para o redesenho solicitado. | [phase8b_figures.py](../code/render/phase8b_figures.py), exportação pertinente em [phase8b_tables.py](../code/render/phase8b_tables.py). | Valores e ajuste original da família C preservados; inspeção visual no tamanho da dissertação. |
| P03 | Alinhar títulos, posição no corpo/apêndice e referências à nova estrutura. | CÓDIGO-P quando gerado; editorial no restante. | [phase8b_render.py](../code/render/phase8b_render.py), [manuscript_artifacts.csv](../config/manuscript_artifacts.csv), localizadores afetados em [numeric_claims.csv](../config/numeric_claims.csv), legendas/notas geradas. | Cada referência aponta ao conteúdo correto; sem conflito entre a nova 5.2 e a numeração antiga das heterogeneidades. |
| P04 | Apresentar os DDDs existentes em tabelas legíveis no corpo, se o formato do apêndice for amplo/técnico demais. | CÓDIGO-P, condicionado ao formato final. | Geradores do apêndice em [phase8b_tables.py](../code/render/phase8b_tables.py) e resultados das famílias [A](../results/reference/artifacts/caged/diagnostics/ddd_multiplicity_results.csv)/[B](../results/reference/artifacts/caged/diagnostics/ddd_alternative_partitions.csv). | Modelo/complemento, coeficiente, p ajustado e diagnóstico preservados; sem reestimar ou substituir DDD por DiDs. |
| P05 | Corrigir o denominador dos DDDs salariais na nota automática. | CÓDIGO-P; erro confirmado nesta checagem, separado do feedback. | `mandatory_interpretation_note` em [phase8b_common.py](../code/render/phase8b_common.py), verificações afetadas. | Nota informa 2 de 20 testes salariais na família de 100; valores BH originais preservados. |
| P06 | Reconciliar inventário de publicações e validações ao substituir uma figura registrada por três. | Registro/validação de publicação, condicionado ao esquema final de exportação. | [manuscript_artifacts.csv](../config/manuscript_artifacts.csv), [reference_validation.py](../code/replication/reference_validation.py), [test_phase8b_rendering.py](../tests/test_phase8b_rendering.py), testes de registro e documentação afetados. | Inventário corresponde ao esquema escolhido; referência analítica antiga rastreável e equivalência numérica documentada. |

O pacote documenta hoje exatamente 53 publicações registradas. Se uma figura registrada for substituída por três publicações independentes, sem outra mudança, o total passa a 55. Não atualizar a contagem automaticamente: primeiro definir o mapa final, incluindo tabelas movidas ou consolidadas. Preservar identificadores computacionais estáveis quando possível e associá-los aos novos rótulos da dissertação. Manter a referência congelada anterior e documentar separadamente uma nova referência de apresentação, sem substituir valores empíricos aceitos.

O gerador já lê uma base completa de 26 grupos × 5 desfechos para a Figura 5.2.6. Separá-la exige outro layout, não regressões novas. As estrelas também usam p-valores já disponíveis.

Na implementação futura, verificar os geradores e registros afetados e comparar figuras/tabelas com as entradas numéricas salvas. Não é necessário reestimar tudo apenas para planejar ou demonstrar mudanças de apresentação. Se a implementação revelar um defeito numérico, documentá-lo separadamente antes de ampliar o escopo empírico.

## Ordem sugerida para executar depois deste levantamento

1. **Resolver as referências factuais.** Concluir F01–F04 e F06; identificar as saídas exatas de cada tabela/figura. Preparar a redação proposta para F05. Isso evita propagar erros ao mover o texto.
2. **Reestruturar a Seção 4.** Executar E01–E08 com o mínimo de reescrita. Reunir os poucos parágrafos conceituais novos para sua revisão.
3. **Reestruturar a Seção 5 e seus apêndices.** Executar R01–R09, definir o mapa de apresentação e implementar P01–P06 conforme necessário. Escolher DDDs e robustez por sua função, não pela significância.
4. **Montar a discussão.** Executar D01–D04 movendo argumentos existentes e preparando o diálogo internacional. Revisar com você as interpretações novas.
5. **Preparar a conclusão curta.** Executar C01 quando resultados/discussão estiverem estáveis. Eu entrego a primeira versão completa.
6. **Conferir a dissertação inteira.** Atualizar o parágrafo de organização da introdução, referências a seções/tabelas/figuras, apêndices, legendas, equações e sínteses afetadas. Verificar se nenhuma ressalva importante desapareceu nos cortes.

Posso avançar nas tarefas independentes de organização, conferência e apresentação enquanto você revisa os rascunhos. Nesta etapa, o trabalho se limita ao plano porque você pediu apenas o levantamento e a organização.

## O que concentrar na sua revisão

| Item | O que eu vou entregar | O que você avalia |
|---|---|---|
| Identificação e crosswalk | Parágrafos conceituais revisados, com os trechos originais e o motivo das correções. | Se as afirmações correspondem ao argumento pretendido e mantêm seu tom. |
| Explicação nacional e das heterogeneidades | Narrativa por tabela e lista curta das exceções preservadas. | Se a ênfase representa a mensagem do trabalho sem esconder resultados inconvenientes. |
| Pandemia, ciclo macroeconômico e ocupações pequenas | Texto condensado, preservando hipóteses e contrapontos. | Se as hipóteses estão bem representadas e qualificadas. |
| Comparação internacional | Primeiro rascunho organizado pelos quatro grupos de achados, com referências conferidas. | Se as comparações são justas e a ênfase faz sentido. |
| Conclusão | Rascunho completo de sete parágrafos, principalmente com sua redação existente. | Se soa como você e apresenta a contribuição pretendida. |

Nenhum item identificado exige que você invente um resultado, colete novos dados ou escreva uma seção sozinho. Se uma justificativa estiver ausente tanto no texto quanto no registro do desenho, eu identifico a lacuna e proponho uma explicação para você confirmar, sem inventar uma decisão de pesquisa.

## Checklist de conclusão da revisão futura

- [ ] Toda observação da professora foi atendida ou tem justificativa para uma alternativa que ela permitiu.
- [ ] A Seção 4 segue dados → exposição → identificação → modelos → heterogeneidades → diagnósticos.
- [ ] A 5.1 distingue magnitude, incerteza estatística e interpretação causal.
- [ ] A 5.2 apresenta complementos selecionados; os diagnósticos completos continuam rastreáveis.
- [ ] A 5.3 prioriza DDD e o distingue de DiD dentro do grupo em todo o texto.
- [ ] As três figuras novas do apêndice são legíveis, identificadas corretamente e fiéis aos números.
- [ ] A Seção 6 reúne interpretação e diálogo com a literatura; a 7 é curta e em texto corrido.
- [ ] Os cinco temas de limitação e as quatro prioridades de agenda continuam presentes na conclusão.
- [ ] Sua voz e os trechos úteis da redação original continuam reconhecíveis; correções substantivas estão registradas.
- [ ] Datas, janelas, denominadores, sinais, famílias de p-valores, complementos, suporte e diagnósticos indefinidos correspondem às fontes.
- [ ] Tabelas, legendas, remissões, apêndices e registros de publicação estão sincronizados.
- [ ] Nenhuma escolha empírica ou estimativa foi alterada sob o rótulo de reorganização editorial.
