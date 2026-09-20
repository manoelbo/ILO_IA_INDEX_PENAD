# Plano de reescrita V3 — o que muda no texto depois das três frentes

**Data:** 1 de agosto de 2026
**Insumo:** `Replication Package/V2/experiment/VEREDITO_V3.md` e os relatórios das três frentes.
**Escopo:** apenas o que as frentes RAIS, PNADc e Anatel autorizam mudar. Nada mais.

**Regra que vale para o documento inteiro:** cada item traz a frase atual **verbatim**, o artefato que
justifica a mudança, e se ela é estrutural ou não. Item sem artefato de origem não entra.

**Localização:** as linhas citadas são do snapshot `tasks/notion_snapshot.txt`, de 28/07. O texto foi
editado depois. **Localize por frase, nunca por número de linha.**

---

## 0. A decisão que trava parte do plano

O documento atual não tem Seção 6. A estrutura é:

```
Introdução · 2 Mensuração · 3 Análise Descritiva · 4 Estratégia Empírica
· 5 Resultados · Apêndice A · REFERÊNCIAS
```

Não há conclusão, não há considerações finais, e **não há §6.4**. Isso importa porque o pré-registro
das três frentes fixou o destino do Anatel como "agenda §6.4" e o teto de RAIS e PNADc como "Seção 5
ou 6". Duas dessas três casas não existem.

Três saídas, na minha ordem de preferência:

| | Saída | Custo | O que se perde |
|---|---|---|---|
| **A** | **Escrever a conclusão** (Seção 6), com a agenda de pesquisa como última subseção | Alto — é uma rodada própria, fora deste plano | Nada. É o que a dissertação precisa de qualquer forma |
| **B** | Sem Seção 6: o negativo do Anatel vira parágrafo final da **§4.5**, e os diagnósticos vão para um Apêndice B novo | Baixo | A agenda de pesquisa não é escrita; o Anatel aparece como validação, não como programa futuro |
| **C** | Anatel fica só no pacote de replicação, sem entrar no texto | Nenhum | Perde-se a melhor demonstração de disciplina metodológica do trabalho |

**Minha recomendação: B agora, A depois.** A defesa vai perguntar pela conclusão de qualquer jeito, e
uma dissertação sem seção de fechamento é uma fragilidade maior do que qualquer coisa neste plano. Mas
a conclusão é rodada própria e não deve atrasar a incorporação das frentes.

**Tudo na Parte 1 abaixo independe dessa decisão.** Só a Parte 2 depende.

---

# Parte 1 — Reescritas, sem mudança de estrutura

Sete frases. Nenhuma cria seção, subseção, tabela ou figura.

---

## T1 — §5.1, síntese · a mudança mais consequente

**Onde:** §5.1, parágrafo de fechamento da leitura causal (L861).

**Está escrito:**

> Como admissões e desligamentos caem simultaneamente, o padrão é compatível com menor movimentação
> dos fluxos; entretanto, como o modelo não observa o estoque de emprego, ele não permite concluir se
> houve ou não destruição líquida de vínculos.

**O problema:** a segunda metade deixou de ser verdade. Existe agora uma medição de estoque — e ela
aponta na direção **contrária** à leitura que a primeira metade sugere. A hipótese de menor
movimentação prevê fluxos caindo com estoque estável. A RAIS mostra estoque caindo com rotatividade
não detectável.

**Fonte:** `1_rais/results/rais_static_results.csv` — estoque PPML −0,042925 (EP 0,015574; p 0,006;
BH **0,018**; pretrend `fail`); rotatividade MQO −0,017839 (p 0,496; BH 0,496).

**Texto sugerido:**

> Como admissões e desligamentos caem simultaneamente, o padrão é compatível com menor movimentação
> dos fluxos. Essa leitura, porém, prevê fluxos mais lentos com estoque estável, e o exercício
> complementar com a RAIS não a sustenta: entre 2019 e 2024, o estoque de vínculos ativos em 31 de
> dezembro das ocupações expostas é menor, com coeficiente PPML de −0,043 — cerca de −4,2% —, enquanto
> o diferencial de rotatividade não é distinguível de zero. O sentido descritivo é, portanto, mais
> compatível com menos vínculos ativos do que com menos rotatividade. Nenhuma das duas medições é
> causal: a tendência prévia do estoque falha e a rotatividade dispõe de um único período anterior à
> referência. O que se pode afirmar é que a ausência de observação do estoque deixou de ser uma
> limitação do trabalho e passou a ser uma medição com resultado, e que esse resultado não favorece a
> hipótese de acomodação silenciosa.

**Cuidado:** não escrever estrela, não escrever "significativo", não usar o p BH de 0,018 como
manchete. O pretrend falha.

---

## T2 — §4.1, a contrapartida declarada

**Onde:** §4.1, o parágrafo que declara as limitações do CAGED (L517).

**Está escrito:**

> A contrapartida é declarada e é séria: o CAGED observa apenas o mercado formal e não observa o
> estoque. Se a difusão da IA empurrar trabalhadores para a informalidade, esse deslocamento é
> invisível aqui. A Seção 3, baseada na PNADc, cumpre o papel complementar de caracterizar a estrutura
> ocupacional e a informalidade; as duas seções respondem a perguntas diferentes com a base adequada a
> cada uma.

**O problema:** as duas limitações da mesma frase deixaram de ser cegueira. **O CAGED continua não
observando** nenhuma das duas — isso não muda. O que muda é que a dissertação passa a observar, em
bases complementares.

**Fonte:** as duas frentes inteiras.

**Texto sugerido:**

> A contrapartida é declarada e é séria: o CAGED observa apenas o mercado formal e observa fluxo, não
> estoque. Nenhuma dessas duas restrições é removível dentro da própria base. Por isso o trabalho as
> trata em bases complementares, com desenho declarado antes da estimação: a RAIS fornece o estoque de
> vínculos ativos por ocupação e ano, e a PNAD Contínua permite examinar se houve deslocamento em
> direção à informalidade. Nenhum dos dois exercícios alcança identificação causal, e ambos são
> reportados como medição. A Seção 3, também baseada na PNADc, cumpre o papel distinto de caracterizar
> a estrutura ocupacional; as seções respondem a perguntas diferentes com a base adequada a cada uma.

---

## T3 — Resumo

**Onde:** resumo (L19).

**Está escrito:**

> …mas o desenho não observa a adoção efetiva da IA nem o estoque de emprego, e boa parte das
> estimativas permanece exploratória.

**O que muda:** cai a metade do estoque. **A metade da adoção de IA fica intacta** — nenhuma das três
frentes observa adoção, e essa limitação permanece inteira em todos os lugares onde aparece.

**Sugestão:** *"…mas o desenho não observa a adoção efetiva da IA, e boa parte das estimativas
permanece exploratória."* — mais uma oração indicando que estoque e informalidade foram examinados em
bases complementares, sem identificação causal.

**Também no resumo, com cuidado:** a frase *"o padrão é compatível com menor movimentação dos fluxos, e
não com destruição de vínculos"* recebe o mesmo problema de T1. Como o resumo não comporta a
qualificação inteira, a saída é enfraquecer a afirmação — trocar *"e não com destruição de vínculos"*
por algo como *"embora o exercício complementar com a RAIS não corrobore essa leitura"*.

---

## T4 — §5.2.3 e §5.2.6, comparações com Brynjolfsson

**Onde:** dois parágrafos (L1350 e L1706).

**Está escrito, em §5.2.3:**

> A diferença pode decorrer dos desenhos: os autores analisam o estoque de emprego e comparam quintis
> de exposição, com efeitos concentrados nos níveis mais elevados, enquanto esta dissertação examina
> fluxos de admissões e desligamentos e utiliza uma classificação binária mais ampla de ocupações
> expostas.

**E em §5.2.6:**

> A comparação, entretanto, não é equivalente: o artigo acompanha estoque de emprego em firmas,
> enquanto o CAGED registra fluxo de admissões formais, e a classificação de exposição da OIT também
> difere dos quintis utilizados pelos autores.

**O problema:** os dois contrastes usam "eles têm estoque, nós temos fluxo" como eixo. Esse eixo ficou
impreciso — a dissertação passa a ter estoque também, só que anual, por CBO4 e não identificado.

**O que fazer:** estreitar o contraste para o que ele de fato é. Não é estoque contra fluxo; é
**estoque de firma por quintis de exposição** contra **estoque ocupacional anual mais fluxos mensais,
com classificação binária**. A distinção continua válida e fica mais defensável.

---

## T5 — Nota da Tabela A.1, proxy cumulativo de fluxo

**Onde:** nota de rodapé da Tabela A.1 (L1787).

**Está escrito:**

> O Painel B.2 substitui as duas construções alternativas do saldo por um índice cumulativo de fluxo
> líquido, normalizado pelo fluxo bruto pré-tratamento; **ele não observa o estoque de emprego** e não
> deve ser lido como tal.

**O que muda:** a nota **fica**, e ganha evidência. O proxy foi validado contra o estoque observado.

**Fonte:** `1_rais/results/rais_proxy_validation.csv` — classificação
`accompanies_stock_directionally`; correlação mediana de nível **0,0311**; de variação **0,1121**; erro
assinado de direção mista.

**Acréscimo sugerido à nota:** *"A validação contra o estoque observado na RAIS classifica o índice
como concordante apenas em direção: todas as correlações estimáveis são positivas, mas a mediana de
nível é 0,03 e a de variação é 0,11."*

---

## T6 — §5.2.2 e demais heterogeneidades: **não mexer**

**Onde:** §5.2.2, raça (L1137), e qualquer outra subseção de heterogeneidade que invoque a ausência de
estoque.

**Está escrito:**

> Como admissões e desligamentos recuam juntos, o padrão é compatível com menor movimentação dos
> fluxos entre trabalhadores negros; sem observar o estoque, ele não permite distinguir menor
> rotatividade de perda líquida de vínculos.

**Por que fica:** a frente RAIS mede estoque por **CBO4-ano, sem recorte demográfico**. Não existe
estoque por raça, por sexo, por idade ou por escolaridade. A limitação continua inteira em todas as
subseções de heterogeneidade, e transportar o achado nacional para elas seria erro.

**Este item existe para impedir uma mudança, não para fazer uma.**

---

## T7 — §5.1, diálogo com a literatura

**Onde:** o parágrafo que compara com Humlum e Vestergaard, Chandar e Aldasoro (L935).

**O que muda:** hoje a comparação é sobre nulos em ganhos, horas e emprego agregado. A RAIS acrescenta
uma comparação direta que não existia: um diferencial **negativo** de estoque formal, não identificado.
Vale uma oração situando o resultado brasileiro entre os nulos precisos dinamarqueses e os negativos de
subgrupo, declarando que o brasileiro não é identificado e portanto não arbitra entre eles.

**Opcional.** Só entra se não inchar o parágrafo.

---

# Parte 2 — Adições, com custo estrutural

Depende da decisão do §0.

---

## T8 — Nova §5.4 · evidência complementar

**Estrutural: sim.** Cria subseção dentro da Seção 5, que já tem 5.1, 5.2 e 5.3. Não cria seção nova —
o custo estrutural declarado no pré-registro é exatamente "subseção".

**Título sugerido:** *5.4 Evidência complementar: estoque formal e informalidade*

**Conteúdo mínimo, com os números verificados:**

**Bloco RAIS.** Estoque de vínculos ativos em 31/12, rotatividade de fluxo bruto e tempo médio de
emprego, com o mesmo tratamento da dissertação — 75 CBO4 expostas contra 266 `Not Exposed`. Janela
2019–2024, imposta pela quebra do eSocial, que é diferencial e dominante na janela longa.

| Outcome | Estimador | Coeficiente | EP | p nominal | p BH | Pretrend |
|---|---|---:|---:|---:|---:|---|
| Estoque em 31/12 | PPML | −0,0429 | 0,0156 | 0,006 | 0,018 | `fail` |
| Rotatividade | MQO | −0,0178 | 0,0262 | 0,496 | 0,496 | `pass`, 1 lead |
| Tempo de emprego | MQO | −0,0264 | 0,0185 | 0,156 | 0,234 | `fail` |

**Bloco PNADc.** 57 trimestres de 2012T1 a 2026T1, 2022T4 excluído como transição, ocupados de 18 a 65
anos ponderados por `V1028`. **Zero rejeições nominais e zero após BH** nos seis desfechos. Os
diferenciais de estoque são positivos ao mesmo tempo para informal (+8,5%), formal (+4,3%) e total
(+6,4%) — o que **não** é o padrão de substituição que a hipótese de deslocamento prevê. Os 12
pretrends do modelo exato falham.

**Bloco obrigatório — a discordância.** As duas medições de estoque formal têm sinais opostos e
magnitudes quase simétricas: RAIS −0,0429 (p 0,006) e PNADc +0,0420 (p 0,386). Registro e amostra
domiciliar, pareamento exato de quatro dígitos e regra de 0,50 no COD3, seis anos e quatorze, data fixa
e média ponderada. Nenhuma identificada. **Escreva isso antes que a banca escreva.** A leitura
defensável é que não são o mesmo estimando e que a divergência delimita a precisão do que se pode
dizer; a indefensável é escolher a que rejeita.

**Regras de linguagem para a subseção inteira:** nenhuma estrela, nenhum "significativo", janela e
estimando declarados em toda afirmação, e a palavra "medição" no lugar de "efeito".

---

## T9 — §4.5, parágrafo final sobre o Anatel

**Estrutural: não.** Acrescenta parágrafo a subseção existente. **Depende da saída B do §0.**

A §4.5 já declara dois exercícios encerrados sem resultado — porte do estabelecimento e público versus
privado. O Anatel é o terceiro, e o mais instrutivo, porque parou por diagnóstico e não por dado
ausente.

**O parágrafo já está escrito**, em português e na voz do texto, ao fim de
`3_anatel/results/ANATEL_RELATORIO.md`, sob "Texto final para a §6.4". Ele cobre o corte 80/20
mecanicamente errado, o campo de fibra corrigido, a melhora demonstrável dos placebos, a contribuição
não isolada do vintage, e a concentração excessiva entre UFs. Termina afirmando que a interrupção não é
evidência de efeito nulo.

**Se a saída for A**, esse mesmo parágrafo vai para a agenda da Seção 6 e a §4.5 recebe apenas uma
remissão de uma linha.

---

## T10 — Apêndice B novo · diagnósticos das três frentes

**Estrutural: sim.** Cria apêndice. O Apêndice B anterior foi removido na rodada da V2, então o rótulo
está livre.

**Conteúdo:** pretrends das três frentes com p conjunto e classificação; suporte publicado; escada de
sensibilidades da RAIS e da PNADc; os oito diagnósticos de suporte do Anatel; e as duas replicações
cruzadas em R.

**Três coisas que este apêndice tem de declarar, e que não podem ficar só no pacote de replicação:**

1. Os erros-padrão da PNADc **não implementam o desenho amostral complexo completo** — estratos e UPAs
   não entram na inferência registrada.
2. A sensibilidade de estoque médio anual da RAIS é **não executável**: 2.749.713 meses de início e
   316.377 meses de fim inativos não se resolvem pelos campos da fonte sem um proxy não assinado.
3. O gate de suporte que interrompeu o Anatel **não era pré-registrado** — é emenda posterior à
   abertura do gate original, com a ordem declaração-antes-observação preservada. Omitir isso é o único
   erro que transformaria um negativo honesto em algo indefensável.

---

# Parte 3 — O que não muda

Lista curta e deliberada. Serve para conter a rodada.

- **Nenhuma alegação causal é removida.** Os pretrends falham em 2 de 3 outcomes da RAIS e em 12 de 12
  da PNADc. Nenhuma frente autoriza suavizar uma qualificação existente.
- **Toda menção à não observação da adoção de IA fica.** Exposição não é uso, e nenhuma frente move
  isso.
- **As Seções 2 e 3 não são tocadas.**
- **Os resultados da Seção 5.1 a 5.3 não mudam de número.** As três frentes não reestimam nada da V2.
- **Famílias A, B e C intactas.** As famílias novas são D, E e F, e nunca se fundem com as antigas.
- **Tabela A.1 permanece válida e inalterada** — T5 acrescenta uma linha de validação à nota, não
  corrige a tabela.

---

# Parte 4 — O que a banca vai atacar

| Ataque | Resposta preparada |
|---|---|
| "A única rejeição tem pretrend falhando" | Está escrito no texto, não escondido. Das 21 vagas declaradas, nove foram estimadas e uma rejeita após BH — e a subseção diz isso |
| "As duas medições de estoque se contradizem" | Antecipado em T8, com as quatro diferenças de desenho nomeadas |
| "Vocês pararam o Anatel porque não deu certo" | O gate fechou sobre diagnóstico de suporte, sem nenhum coeficiente estimado; as 12 vagas estão declaradas e vazias; e A-G1 abriu com margens igualmente apertadas, o que impede invocar marginalidade seletivamente |
| "O gate do Anatel foi inventado no meio" | Sim, e está declarado como emenda, com carimbo de data anterior a qualquer número de A6 |
| "A PNADc não usa o desenho amostral completo" | Declarado em T10, item 1 |
| "Cadê a conclusão?" | É a decisão do §0, e não tem resposta boa exceto escrevê-la |

---

# Parte 5 — Ordem de execução

1. **Decidir o §0.** Trava T9 e parte de T10.
2. **T1** — §5.1. É a mais consequente e a que muda o argumento.
3. **T2, T3** — §4.1 e resumo. Dependem de T1 estar decidida, para não se contradizerem.
4. **T8** — a nova §5.4, se aprovada.
5. **T4, T5, T7** — ajustes de comparação e nota.
6. **T9, T10** — Anatel e apêndice.
7. **T6** — verificação final de que nada foi mexido onde não devia.

**Verificação, no padrão das rodadas anteriores:** toda substituição conferida por comando, com
checagem byte-a-byte fora da região editada; todo número conferido contra o artefato de origem antes de
entrar no texto; e nenhum valor preenchido de memória.

---

# Anexo — de onde vem cada número

| Número | Artefato |
|---|---|
| Coeficientes e p BH da RAIS | `experiment/1_rais/results/rais_static_results.csv` |
| Pretrends da RAIS | `experiment/1_rais/results/rais_pretrends.csv` |
| Validação do proxy | `experiment/1_rais/results/rais_proxy_validation.csv` |
| Coeficientes e p BH da PNADc | `experiment/2_pnadc/results/pnadc_results.csv` |
| Pretrends da PNADc | `experiment/2_pnadc/results/pnadc_pretrends.csv` |
| Diagnósticos de suporte do Anatel | `experiment/3_anatel/results/anatel_a6_*.csv` |
| Placebos e pretrends do Anatel | `experiment/3_anatel/results/anatel_placebo_dec2021.csv`, `anatel_pretrends_interaction.csv` |
| Parágrafo pronto do Anatel | `experiment/3_anatel/results/ANATEL_RELATORIO.md` |
| Consolidado das três frentes | `experiment/VEREDITO_V3.md` |
| Scorecard de seis linhas | `experiment/results/scorecard_v3.csv` |
