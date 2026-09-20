# 06 — Conclusão e Recomendação (combinada)

Duas auditorias independentes, dois vereditos. Este documento reconcilia.

---

## Os dois vereditos originais

**Codex:** `DO NOT CIRCULATE`. Alvo recomendado: `USE V2`, depois que os gates de armazenamento e de
dados oficiais abrirem. V2 **NO-GO hoje**.

**Claude:** fazer a V2 com escopo fechado. Congelar a V1 hoje, reconstruir o painel, deixar o
resultado da reconciliação decidir o resto.

## Veredito combinado

**Não circular o PDF atual. Fazer a V2. E a V2 pode começar agora.**

Os dois conjuntos concordam no diagnóstico e na direção. Divergiam em um ponto operacional — se os
gates estavam abertos — e essa divergência se resolve com um fato que só uma das auditorias
levantou.

---

## Por que não circular

Não é uma questão de rigor excessivo. São defeitos que um leitor vê na primeira passada:

1. **A primeira página tem um erro factual.** O resumo diz "cerca de 10% da força de trabalho
   **formal**". Os números do próprio trabalho são 10,1% de todos os ocupados e **14,8%** dos
   formais. Ironicamente, a correção fortalece o argumento.
2. **O Apêndice A.6 do texto e o do pacote são objetos diferentes.** Os artefatos chamados
   `table_a_6_income_*` são gerados da tabela de escolaridade. Os testes passam porque o diretório de
   referência contém a mesma saída errada — a identidade byte-a-byte validou um erro semântico.
3. **O Apêndice A.5 não entrega o que o corpo promete**, e escolaridade é um dos resultados mais
   enfatizados.
4. **Quatro especificações de robustez são prometidas e nenhuma é reportada.**
5. **O PDF corta a coluna de suporte** das tabelas A.2–A.6 — justamente o diagnóstico usado para
   qualificar heterogeneidade — e imprime `<br>` e `&lt;0,001` literais.
6. **A lista de referências tem 15 de 36 entradas**; 21 registros citados estão ausentes.
7. **Os seis links do Apêndice B retornam 404.**
8. **Não existe seção de Conclusão.**

Nada disso exige pesquisa nova. Exige uma rodada de correção — `04` §P0 — que é independente da V2 e
deve ser feita mesmo que tudo o mais pare.

---

## Por que a V2, e não apenas correção da V1

Os dois conjuntos chegaram aqui por caminhos diferentes. Ambos são suficientes sozinhos.

### O caminho do Codex: reprodutibilidade e semântica

Quatro problemas materiais exigem uma nova geração empírica:

1. Células de fluxo zero recebem salários positivos artificiais (R$ 1.104,7868, o piso da
   winsorização) e controles de composição zerados; **31 entram na amostra principal**. E salários de
   desligamento chegam a **R$ 203,3 milhões**, com sete células acima de R$ 1 milhão dentro da
   amostra principal.
2. O modelo preferido condiciona em composição das admissões que pode ser pós-tratamento.
3. **A maior parte das saídas inferenciais é estimativa congelada, não re-estimada** pelo caminho
   público. Só quatro modelos nacionais são re-estimados; event studies, DDD, heterogeneidades,
   Poisson, salário real e casos ocupacionais são renderizados de CSVs.
4. As caudas do event study são recortadas e os modelos de fluxo principais falham seus pretrends.

Corrigir isso dentro da V1 destruiria o sentido da linha de base congelada.

### O caminho do Claude: integridade dos dados de origem

O pipeline consulta só `microdados_movimentacao`. As declarações **fora do prazo** (8.609.944
registros) e as **exclusões** (607.497) nunca entram. A estatística oficial do PDET é MOV + FOR − EXC.

A fração omitida cai de **8,61% em 2021 para 1,29% em 2024** — e a janela 2021→2024 é o eixo da
identificação. Pior, a queda difere entre grupos ocupacionais: os grupos que compõem majoritariamente
o controle perdiam cerca de **2 pontos percentuais a mais** de cobertura em 2021 do que os tratados,
e a diferença desaparece no pós.

Mecanicamente, isso deprime os fluxos do controle no pré e os recupera no pós — produzindo um DiD
negativo para o tratado e uma falha de tendência paralela. Que é exatamente o que a Seção 5.1
reporta: −3,1% em admissões com pretrend falhando a p=0,001, e −4,2% em desligamentos a p=0,031.

**Não está provado que os resultados sejam artefato.** A composição de cada grande grupo não é
idêntica à do grupo tratado formal, e o efeito líquido pode ser menor que a diferença bruta de
cobertura. **Está provado que a construção atual não permite distinguir**, e que a magnitude
potencial do artefato é da mesma ordem do efeito estimado.

Não há saída editorial para isso. Você não pode adicionar uma ressalva dizendo "os coeficientes
principais podem ser inteiramente devidos a uma variação de cobertura administrativa que eu não
corrigi". E se alguém na banca perguntar "você usou as declarações fora do prazo?", a única resposta
hoje é não.

---

## Por que a V2 pode começar agora

Este é o ponto onde os dois conjuntos divergiam.

O Codex registrou NO-GO porque o contrato exige 15–20 GiB livres e há 8,45 GiB, com a restrição
autoimposta de que "nenhum dado do autor pode ser apagado".

**Existem 4,2 GB em painéis municipais derivados que pertencem à extensão Anatel — documentada como
excluída da dissertação.** São reconstruíveis a partir de `data/raw/` e dos scripts, que permanecem
no repositório. Painel derivado é cache, não dado do autor. Removê-los leva o espaço de 8,5 para
~12,7 GiB. A lista completa está em `05` §2.1.

E a arquitetura de ingestão proposta é mais leve que o contrato supõe: processando competência a
competência com descarte, o pico fica em 1–2 GB, não 15–20. Corrigir a arquitetura — que já era um
gate NO-GO independente — resolve o de armazenamento junto.

Sobre o corte de dados: o FTP tem até maio/2026, verificado. Junho sai em 30/07/2026, cinco dias
depois do freeze. Junho acrescenta um mês a um pós-tratamento que já terá 42 — o ganho estatístico é
desprezível. Se a entrega for depois de 30/07, use junho; se for antes, use maio e não perca nada.

**Os gates estão abertos.**

---

## O que você ganha, além de tirar o risco

Uma vez reconstruindo o painel, estes vêm quase de graça:

**Onze meses a mais de pós-tratamento.** De jun/2025 para mai/2026: o pós vai de 31 para 42 meses. E
2025–2026 é quando a adoção de IA no Brasil escalou.

**A resposta à pergunta que o texto declara não conseguir responder.** `tipo_movimentacao` está no
parquet e nunca foi usado — todo desligamento é um evento só. Decompondo em demissão sem justa causa,
pedido de demissão e término de contrato, a §5.1 deixa de dizer "compatível com menor movimentação
dos fluxos, mas não posso distinguir de destruição de vínculos" e passa a dizer qual margem se moveu.
Se caem as demissões, a decisão é da firma; se caem os pedidos, é o trabalhador, e a alternativa
externa piorou. Qualquer um dos dois é um achado.

**A porta de entrada medida diretamente.** O enquadramento do trabalho é o ajuste na entrada, hoje
aproximado por faixa etária — que o seu próprio plano proíbe de traduzir como senioridade.
`tipo_movimentacao` tem "admissão por primeiro emprego", a medida direta, que os autores americanos
de referência não têm.

**O Gradiente 4 deixa de estar vazio, ou passa a estar vazio por uma razão defensável.** A ponte
alcança 11 das 13 ocupações ISCO-08 de G4, e 16 CBOs tocam pelo menos uma. Nenhuma é classificada
como G4 porque a regra é assimétrica — G4 exige `média − desvio ≥ 0,50` enquanto G1–G3 exigem
`média + desvio ≥ 0,50` — e o desvio soma dispersão entre destinos à dispersão entre tarefas. A CBO
4121 corresponde à ocupação mais exposta do índice inteiro (0,70) e sai como G3, falhando o corte por
0,007. A explicação atual da §4.2 atribui isso à diluição da média; 207 das 436 CBOs mapeiam para um
único destino, então para quase metade não há diluição alguma.

**A maior fraqueza vira uma seção de método.** Hoje, quando o pretrend falha, a resposta é rebaixar a
linguagem para "exploratório". Rambachan–Roth permite reportar os limites do efeito sob a hipótese de
que a violação pós é no máximo M vezes a observada no pré. Você sai de "não posso concluir nada" para
"o efeito é negativo desde que a violação não exceda 1,5 vez a observada no pré".

---

## Onde as duas auditorias discordaram, e como fica

| # | Divergência | Resolução |
|---|---|---|
| D1 | V2 pode começar hoje? | **Sim.** O gate de armazenamento abre com os 4,2 GB de painéis derivados da extensão excluída. |
| D2 | G4 vazio é força ou defeito? | **Os dois.** É força o código expor o fato; é defeito a §4.2 explicá-lo pela razão errada. Manter o contrato do Codex, acrescentar o diagnóstico. |
| D3 | Entram novos outcomes? | **Sim, com a disciplina do Codex.** Não são novos subgrupos — são decomposições de outcomes que já estão no texto. Pré-registrar, limitar a família, corrigir multiplicidade, reportar suporte. |
| D4 | Gravidade do bug de fluxo zero | **Alta**, não baixa. O Claude mediu o estágio errado do pipeline; o Codex mediu o painel de estimação, onde o piso da winsorização transformou o zero num salário plausível que passa despercebido. |

---

## O custo honesto e a regra de parada

O caminho completo tem dez pacotes de trabalho e envolve escrever um ingestor novo, reconstruir o
painel, re-estimar tudo (inclusive o que hoje é só renderizado), regerar tabelas e figuras, e
reescrever os parágrafos de leitura da Seção 5.

A janela de duas a três semanas continua realista **se o escopo for mantido na dissertação
existente**. A maior incerteza é engenharia de dados, não escrita.

Mas o plano tem gates justamente para você poder parar. O **gate do WP3** é o que importa: rodar o
modelo antigo, sem nenhuma outra mudança, sobre o painel corrigido, e ver quanto o coeficiente se
move.

- **Se mover pouco**, a Seção 5 sobrevive quase intacta, você ganhou um apêndice de robustez que
  nenhum trabalho comparável tem, e o resto vira melhoria incremental.
- **Se mover muito**, você descobriu antes de investir nos outros pacotes — e descobriu algo que
  precisava ser descoberto.

De qualquer forma, você sabe cedo. A ordem de valor decrescente, para parar em qualquer ponto, está
em `05` §10.

**Condição de parada:** registre `NOT EXECUTED` em vez de resultado parcial se o vintage não puder
ser reconciliado, se os modelos preferidos falharem suporte de um jeito que mude o estimando, ou se a
V2 exigir mudar a estrutura da dissertação.

---

## Se a professora precisar de um rascunho antes

Use a V1 explicitamente como linha de base preliminar, e complete antes **todo** o `04` §P0:

1. corrigir o universo dos 10,1% versus 14,8%;
2. completar a A.5 e reconciliar a A.6 com sua fonte real;
3. reportar ou retirar as promessas de robustez;
4. substituir os links quebrados do Apêndice B;
5. regerar as 36 referências a partir da bibliografia corrigida;
6. estreitar a linguagem causal, de adoção, de estoque e de mecanismo;
7. reconstruir e inspecionar o PDF;
8. escrever a Conclusão;
9. **divulgar que só quatro modelos centrais são re-estimados publicamente e que os pretrends
   nacionais de fluxo falham.**

Esse documento pode ser compartilhado para feedback metodológico. Não deve ser descrito como o
pacote empírico final.

---

## Uma observação sobre o que você já tem

Vale dizer, porque não é óbvio de dentro do trabalho, e porque as duas auditorias registraram isso
de forma independente.

A honestidade metodológica desta dissertação está acima da média do que se publica. O texto reporta
tendências paralelas que falham em vez de esconder. Diz quando o suporte é fino. Avisa que não há
correção por testes múltiplos. Apresenta "acomodação silenciosa" explicitamente como hipótese.
Congelou 76 códigos ocupacionais antes de olhar os resultados. Rodou duas rodadas de referee
adversarial contra o próprio trabalho e fechou 39 de 44 achados. E o replication package tem
contratos declarativos, hashes SHA-256, replicação cruzada Python↔R a 1e-12, e testes de segurança
destrutiva.

Isso não é comum. É exatamente por isso que a recomendação é fazer a V2: um trabalho com esse nível
de disciplina merece não ter um problema de cobertura de dados não endereçado no meio dele. A
distância entre onde a dissertação está e onde ela pode estar é menor do que parece — o que falta é
insumo correto e cobertura de re-estimação, não método.

A separação conceitual da §2.1 — exposição não é adoção, não é impacto causal, não é substituição —
continua sendo a melhor página do trabalho, e continuará sendo depois da V2. E a Seção 3 se sustenta
sozinha: metade da dissertação não está em risco.

---

## Recomendação em uma frase

Libere os 4,2 GB, feche o congelamento da V1, reconstrua o painel com as declarações fora do prazo,
rode o modelo antigo nele — e deixe esse número decidir quanto do resto do plano você vai executar.
