# 06 — Conclusão e Recomendação

Você perguntou: vale refazer o estudo na V2, ou basta corrigir e melhorar a V1?

---

## A resposta

**Faça a V2, com escopo fechado.**

Não porque a V1 seja ruim — não é. Porque um dos achados desta auditoria não tem correção
editorial: só se resolve reconstruindo o painel. E, uma vez que você vai reconstruir o painel,
quase tudo o mais entra de carona.

---

## Por que deixou de ser opcional

O pipeline consulta apenas `basedosdados.br_me_caged.microdados_movimentacao`. As declarações
**fora do prazo** (8.609.944 registros) e as **exclusões** (607.497) nunca entram. A estatística
oficial do PDET é MOV + FOR − EXC; o painel é só MOV.

A fração omitida não é constante. Ela cai de **8,61% em 2021 para 1,29% em 2024** — e a janela
2021→2024 é exatamente o eixo da identificação. Pior: a queda difere entre grupos ocupacionais.
Os grupos que compõem majoritariamente o controle perdiam cerca de **2 pontos percentuais a mais**
de cobertura em 2021 do que os grupos tratados, e essa diferença desaparece no pós-tratamento.

Mecanicamente, isso deprime os fluxos do controle no período pré e os "recupera" no pós. O
resultado é (i) um coeficiente DiD negativo para o grupo tratado e (ii) uma falha de tendência
paralela. Os dois são exatamente o que a Seção 5.1 reporta: −3,1% em admissões com pretrend
falhando a p=0,001, e −4,2% em desligamentos com pretrend falhando a p=0,031.

Sejamos precisos sobre o que isso significa e o que não significa. **Não está provado que os
resultados são artefato** — a composição de cada grande grupo não é idêntica à do grupo tratado
formal, e o efeito líquido pode ser menor que a diferença bruta de cobertura. O que está provado é
que a construção atual **não permite distinguir**, e que a magnitude potencial do artefato é da
mesma ordem do efeito estimado.

É por isso que não há saída editorial. Você não pode adicionar uma ressalva e seguir em frente,
porque a ressalva seria "os coeficientes principais podem ser inteiramente devidos a uma variação
de cobertura administrativa que eu não corrigi". E se um membro da banca perguntar "você usou as
declarações fora do prazo?", a única resposta hoje é não.

---

## Por que o escopo é fechado, e não "refazer tudo"

Três razões concretas.

**A infraestrutura de reprodução já existe e é boa.** Contratos declarativos, hashes SHA-256 de
todos os insumos e artefatos, 138 testes, um teste que re-estima os quatro modelos principais do
zero exigindo concordância a 1e-12, e replicação cruzada Python↔R batendo a 5,4e-12. Isso é
infraestrutura de qualidade de periódico. Você não vai reconstruir a máquina — vai trocar o
insumo e apertar o botão. É a diferença entre semanas e meses.

**Metade da dissertação não está em risco.** A Seção 3 é uma análise descritiva transversal com a
PNADc, com crosswalk COD→ISCO de 99,2% de cobertura, validada por testes com números fixados. Nada
nesta auditoria a afeta. Ela responde sozinha à primeira pergunta de pesquisa. Se a Seção 5 mudar
inteira, a Seção 3 continua de pé.

**A estrutura do texto não muda.** As seções 1 a 5 permanecem. Mudam números, tabelas, figuras e os
parágrafos de leitura. A única adição estrutural é a Conclusão — que hoje simplesmente não existe,
e cuja ausência é o primeiro comentário que uma banca faz.

---

## O que você ganha, além de tirar o risco

Uma vez reconstruindo o painel, estes vêm quase de graça:

**Onze meses a mais de pós-tratamento.** De 2025-06 para 2026-05: o pós vai de 31 para 42 meses.
E 2025–2026 é justamente quando a adoção de IA no Brasil escalou — é onde o efeito, se existir,
tem mais chance de aparecer. Verificado: o FTP do MTE tem até `202605`.

**A resposta à pergunta que o texto declara não conseguir responder.** `tipo_movimentacao` está no
parquet e nunca foi usado. Todo desligamento é tratado como um evento só. Decompondo em demissão
sem justa causa, pedido de demissão e término de contrato, a §5.1 deixa de dizer "é compatível com
menor movimentação dos fluxos, mas não posso distinguir de destruição de vínculos" e passa a dizer
qual margem se moveu. Se caem as demissões, a decisão é da firma; se caem os pedidos, a decisão é
do trabalhador e a alternativa externa piorou. Qualquer um dos dois é um achado.

**A porta de entrada medida diretamente.** O enquadramento do trabalho é o ajuste na entrada do
mercado, hoje aproximado por faixa etária. `tipo_movimentacao` tem "admissão por primeiro emprego",
que é a medida direta — e que os autores americanos de referência não têm. É a tradução mais fiel
possível do exercício deles para o contexto brasileiro.

**O Gradiente 4 deixa de estar vazio, ou passa a estar vazio por uma razão que você consegue
defender.** Verifiquei: a ponte alcança 11 das 13 ocupações ISCO-08 que a OIT classifica como
Gradiente 4, e 16 CBOs tocam pelo menos uma delas. Nenhuma é classificada como G4, e a causa é a
assimetria da regra — o G4 exige `média − desvio ≥ 0,50` enquanto os gradientes inferiores exigem
`média + desvio ≥ 0,50`, e o desvio usado soma dispersão entre destinos à dispersão entre tarefas.
A CBO 4121, operadores de entrada de dados, corresponde à ocupação mais exposta de todo o índice
(score 0,70) e sai classificada como Gradiente 3, falhando o corte por 0,007. A explicação que está
hoje na §4.2 atribui isso à diluição da média, o que é parte da história mas não é o que decide.

**A maior fraqueza vira uma seção de método.** Hoje, quando o teste de tendências paralelas falha,
a resposta é rebaixar a linguagem para "exploratório". Rambachan e Roth dão a alternativa: reportar
os limites do efeito sob a hipótese de que a violação pós-tratamento é no máximo M vezes a violação
pré observada. Você sai de "não posso concluir nada" para "o efeito é negativo desde que a violação
não exceda 1,5 vez a observada no pré". É o item de maior retorno por esforço de todo o plano.

---

## O que eu conferi e concluí que é menor do que parece

Registro para você não gastar energia à toa. Três coisas que soavam graves e não são:

- **O bug do `.fillna(0)`**, que injeta `ln_salario_adm = 0` em células sem admissão, atinge **63
  de 23.319 células (0,27%)**. Corrija por correção, não por urgência.
- **A afirmação de "muitos zeros"** que justifica `log(y+1)` é falsa — 0,27% de zeros, mediana de
  479 admissões por célula. Mas isso muda uma frase do texto, não a substância. O argumento para
  PPML tem que ser outro, e existe.
- **A extensão Anatel** foi corretamente deixada de fora. O placebo temporal de dez/2021 é
  significativo, o que é uma falha de falsificação. Não reabra.

---

## O custo honesto

Não vou fingir que é pouco. O caminho completo tem nove pacotes de trabalho e envolve escrever um
ingestor de FTP novo, reconstruir o painel, re-estimar tudo, regerar 23 tabelas e 13 figuras, e
reescrever os parágrafos de leitura da Seção 5 inteira.

Mas o plano tem gates justamente para você poder parar. O **gate do WP3** é o que importa: rodar o
modelo antigo, sem nenhuma outra mudança, sobre o painel corrigido, e ver quanto o coeficiente se
move.

- **Se mover pouco**, a Seção 5 sobrevive quase intacta, você ganhou um apêndice de robustez que
  nenhum trabalho comparável tem, e o resto do plano vira melhoria incremental que você faz até
  onde quiser.
- **Se mover muito**, você descobriu isso antes de investir nos outros seis pacotes — e descobriu
  algo que precisava ser descoberto.

De qualquer forma, você sabe cedo. Esse é o desenho do plano.

E se o tempo apertar, a ordem de valor decrescente está em `05_PLANO_V2.md` §7. O mínimo que já
justifica a rodada é WP1 a WP3: congelar a V1, ingerir o vintage correto, reconstruir o painel.

---

## Uma observação sobre o que você já tem

Vale dizer, porque não é óbvio de dentro do trabalho.

A honestidade metodológica desta dissertação está acima da média do que se publica. O texto reporta
tendências paralelas que falham em vez de esconder. Diz quando o suporte amostral é fino. Avisa que
não há correção por testes múltiplos. Apresenta "acomodação silenciosa" explicitamente como hipótese
de discussão, não como achado. Congelou 76 códigos ocupacionais antes de olhar os resultados. Rodou
duas rodadas de referee adversarial contra o próprio trabalho e fechou 39 de 44 achados.

Isso não é comum. E é exatamente por isso que a recomendação é fazer a V2: um trabalho que já tem
esse nível de disciplina merece não ter um problema de cobertura de dados não endereçado no meio
dele. A distância entre onde a dissertação está e onde ela pode estar é menor do que parece — o que
falta é insumo correto, não método.

A separação conceitual da §2.1 — exposição não é adoção, não é impacto causal, não é substituição —
é a melhor página do trabalho e continuará sendo depois da V2.

---

## Recomendação em uma frase

Congele a V1 hoje, reconstrua o painel com as declarações fora do prazo, rode o modelo antigo nele,
e deixe esse número decidir quanto do resto do plano você vai executar.
