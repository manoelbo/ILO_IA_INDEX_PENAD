# Fase 2 — Bloco D: Crosswalk CBO→ISCO e definição do tratamento

Status: **concluída**
Avaliadas: 14/14 · Próxima: Fase 3 (Bloco C — painel e janela)
Promoções de tier nesta fase: nenhuma
Vereditos: sólida 6 · subdocumentada 6 · frágil-reportada 0 · frágil-não-reportada 2 · insustentável 0 · pendente 0

Itens de verificação abertos gerados nesta fase: 2 (V3, V4)

---

## Resumo da fase

O crosswalk está construído corretamente e validado com exatidão: 629 famílias, **0 atribuições divergentes** contra a referência. Nenhuma decisão do Bloco D precisa ser revertida.

O padrão da fase é outro: **o texto subutiliza sistematicamente a evidência que o próprio pacote produziu**, e em duas direções opostas. Duas sensibilidades favoráveis ao trabalho ficaram sem reporte completo (D10, D8) e duas declarações são mais amplas do que a evidência sustenta (D7, D4). O caso mais importante é o **D8**: a forma como a medida contínua é apresentada faz o resultado principal parecer 63% mais fraco do que ele é.

---

## D8 · Usar a exposição de forma binária
`exposicao-binaria` · Tipo S · **Veredito: sólida, subdocumentada** — com erro de apresentação que prejudica o autor

**A decisão.** A exposição entra binária na especificação principal; a medida contínua padronizada aparece como degrau 05 da escada.

**Justificação declarada.** §4.2: o crosswalk perde precisão dentro de cada gradiente e não sustenta com segurança comparações entre gradientes isolados. A justificativa é boa e é a razão certa.

**Alternativa.** A medida contínua, que foi estimada. §6.5 a resume assim: *"a medida contínua reduz o diferencial salarial a −0,0188 por desvio-padrão e deixa os fluxos imprecisos."*

**Momento.** Ex-ante (degrau pré-registrado).

**Sensibilidade.** Aqui está o problema. A frase da §6.5 convida o leitor a comparar **−0,0188 com −0,0507** e concluir que o resultado principal encolhe cerca de 63% sob a medida contínua. A comparação é inválida por duas razões simultâneas, ambas verificáveis nos artefatos:

**Primeira: amostras diferentes.** De `caged/models/specification_ladder.csv`, o degrau 01 roda em 341 clusters e 22.012 observações; o degrau 05 roda em **436 clusters e 28.004 observações**, porque a medida contínua não precisa de corte binário e portanto reincorpora as 95 famílias de exposição mínima. O comparável na mesma amostra é o degrau 04, com −0,0456.

**Segunda: unidades incomensuráveis.** −0,0507 é um contraste binário entre tratados e controle; −0,0188 é o efeito de **um desvio-padrão** de pontuação. De `caged/audit/c1_score_landscape.csv`:

| Lado | Famílias | Pontuação média | Mín. | Máx. | Destinos ISCO médios |
| --- | --- | --- | --- | --- | --- |
| Tratado | 75 | **0,4712** | 0,28 | 0,5933 | 2,89 |
| Exposição mínima | 95 | 0,3292 | 0,22 | 0,41 | 2,08 |
| Controle | 266 | **0,2021** | 0,09 | 0,32 | 1,65 |

O intervalo tratado−controle é de **0,269 ponto de pontuação**. O desvio-padrão da pontuação entre as 436 famílias da amostra do degrau 05 é de aproximadamente **0,119**, de modo que o contraste tratado−controle vale cerca de **2,3 desvios-padrão**. Reescalando: 2,3 × (−0,0188) ≈ **−0,043**, contra os **−0,0456** do degrau 04 na mesma amostra.

Ou seja: a especificação contínua **reproduz** a binária, não a enfraquece. Mesmo tomando o desvio-padrão em qualquer valor entre 0,10 e 0,14, o contraste equivale a 1,9–2,7 desvios e o reescalamento devolve algo entre −0,036 e −0,051 — sempre compatível com −0,0456.

**Direção do viés.** Contra o autor. A apresentação atual concede fragilidade que os dados não impõem, e concede exatamente no resultado mais forte do trabalho.

**Pergunta de banca.** *"Sua própria medida contínua devolve um terço do efeito. Isso não indica que a classificação binária está inflando o resultado?"* — Com a apresentação atual, essa pergunta não tem resposta. Com o reescalamento, ela tem resposta completa e favorável.

**AÇÃO.** Reescrever a passagem da §6.5. Em vez de comparar −0,0188 com −0,0507, dizer: (i) que a especificação contínua roda em 436 famílias e não em 341, sendo comparável ao degrau 04 (−0,0456); (ii) que o coeficiente é por desvio-padrão e o contraste tratado−controle vale cerca de 2,3 desvios; (iii) que o reescalamento devolve ≈ −0,043, consistente com a estimativa binária. Calcular o desvio-padrão exato a partir da tabela de tratamento congelada antes de publicar o número (item V3).
**Prioridade.** **Alta** — é a única ação da fase que muda como o resultado central é lido.

---

## D10 · Reverter a exclusão de `Minimal Exposure` apenas como sensibilidade
`minimal-como-sensibilidade` · Tipo S · **Veredito: frágil, não reportada**

**A decisão.** Estimar e reportar a inversão de D9, sem promovê-la a principal.

**Justificação declarada.** §4.5 e §6.5, que registram: *"Há uma exceção, a configuração que incorpora as ocupações de exposição mínima ao controle, na qual o coeficiente de admissões passa a −0,0887 e se torna significativo. Ela permanece reportada como sensibilidade, não como especificação principal."*

**Sensibilidade.** O texto reporta **um** dos cinco desfechos. O quadro completo, de `caged/models/specification_ladder.csv` e `caged/audit/cd_exposure_and_control_summary.json`:

| Desfecho | Principal (341 CBOs) | p | `Minimal` no controle (436 CBOs) | p | Δ |
| --- | --- | --- | --- | --- | --- |
| Admissões | −0,0538 | 0,164 | **−0,0887** | **0,022** | −0,035 |
| Desligamentos | −0,0420 | 0,227 | **−0,0707** | **0,056** | −0,029 |
| Fluxo bruto | −0,0481 | 0,174 | **−0,0801** | **0,030** | −0,032 |
| Salário (log) | −0,0507 | <0,001 | −0,0456 | <0,001 | +0,005 |
| Saldo (asinh) | −0,5513 | 0,146 | −0,5898 | 0,117 | −0,039 |

Não é só admissões: **o fluxo bruto também cruza 5% (p = 0,030) e os desligamentos ficam na borda (p = 0,056)**. Três dos cinco desfechos mudam de status inferencial quando a exclusão de D9 é invertida, e o texto menciona um.

**Direção do viés.** A omissão trabalha contra o autor — reportar tudo tornaria a história dos fluxos mais forte, não mais fraca. Mas ela cria simultaneamente a vulnerabilidade oposta, que é a que importa numa banca: a aparência de que a especificação principal foi a que produziu fluxos nulos.

**Pergunta de banca.** *"Quando o senhor amplia o controle, três dos cinco desfechos passam a rejeitar. Por que a especificação escolhida é justamente a que não rejeita?"* — A resposta existe e é boa: a escolha é ex-ante, declarada antes da estimação, e justificada por construção (um controle parcialmente exposto reduz o contraste). Mas a resposta só é convincente se o quadro completo estiver publicado; se o leitor descobrir os outros dois desfechos por conta própria, a defesa ex-ante soa reconstruída.

**AÇÃO.** Publicar a tabela de cinco linhas acima, em §4.5 ou no Apêndice A, com a justificativa ex-ante ao lado. É a forma de transformar a maior vulnerabilidade aparente do desenho em demonstração de disciplina.
**Prioridade.** **Alta.**

---

## D7 · Declarar o Gradiente 4 vazio como artefato do crosswalk
`gradiente-4-vazio` · Tipo P · **Veredito: frágil, não reportada**

**A decisão.** §4.2 afirma: *"O grupo vazio é uma consequência do crosswalk, não uma evidência de que não existam ocupações altamente expostas no Brasil."*

**Sensibilidade.** A afirmação é verdadeira para a regra de agregação adotada e **falsa como enunciado geral**. De `caged/treatment/treatment_variant_comparison.csv`, a variante **V-D recupera 3 famílias no Gradiente 4**:

| Variante | G4 | G3 | G2 | G1 | Tratadas | Mínima | Não expostas | Famílias alteradas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V-A (principal) | **0** | 31 | 31 | 13 | 75 | 95 | 266 | — |
| V-B | 0 | 30 | 32 | 11 | 73 | 96 | 267 | 8 |
| V-C | 0 | 31 | 27 | 8 | 66 | 97 | 273 | 16 |
| V-D | **3** | 20 | 37 | 7 | 67 | 79 | 290 | 53 |

O mecanismo explica a diferença e o texto não o distingue. Em V-A a pontuação da família é a **média** das pontuações dos destinos ISCO, e `caged/audit/cd_exposure_and_control_summary.json` registra corretamente que *"Gradient 4 is empty by arithmetic"*: uma média não pode exceder o máximo dos seus componentes, e o máximo observado é 0,5933 contra o limiar de 0,60 — faltam 0,0067. Já V-D agrega pelo **modo ponderado do rótulo nativo da OIT**, sem calcular média, então uma família herda o rótulo G4 diretamente. As duas coisas são verdadeiras ao mesmo tempo.

Portanto o vazio não é consequência "do crosswalk", e sim da decisão de agregar por média de pontuação — que é uma escolha, declarada e defensável, mas escolha.

**Direção do viés.** A formulação atual atribui a natureza o que é atribuível a uma decisão do autor, o que enfraquece a credibilidade do resto da seção justamente onde ela mais precisa ser firme.

**Pergunta de banca.** *"O senhor diz que o Gradiente 4 vazio é consequência do crosswalk, mas uma das suas próprias variantes pré-registradas produz três famílias no Gradiente 4. Não é consequência da sua regra de agregação?"* — Hoje, sem resposta.

**AÇÃO.** Corrigir a frase da §4.2 para atribuir o vazio à agregação por média de pontuação, e acrescentar que a variante de modo de rótulo nativo (V-D) recupera 3 famílias em G4 — o que **reforça** o argumento de que o vazio é artefato de método e não fato do mercado de trabalho brasileiro. A correção torna a afirmação mais forte, não mais fraca.
**Prioridade.** Média-alta.

---

## D4 · Declarar a seletividade da perda de correspondência
`seletividade-do-no-score` · Tipo P · **Veredito: sólida, subdocumentada**

**A decisão.** Registrar que a perda de 193 famílias não é uniforme entre grandes grupos ocupacionais.

**Justificação declarada.** §4.2: *"dirigentes e gerentes representam 19,2% das CBOs sem correspondência, contra 2,8% das classificadas."* Confere exatamente com `caged/audit/c2_unscored_profile.csv` (19,17% e 2,75%).

**Sensibilidade.** O texto reporta **um** dos nove grandes grupos, e é o que soa pior. O perfil completo:

| Grande grupo | Classificadas | % class. | Sem pontuação | % s/pont. | Razão |
| --- | --- | --- | --- | --- | --- |
| 1 Dirigentes e gerentes | 12 | 2,8% | 37 | **19,2%** | 7,0× |
| 2 Profissionais das ciências | 82 | 18,8% | 39 | 20,2% | 1,1× |
| 3 Técnicos de nível médio | 80 | 18,3% | 43 | 22,3% | 1,2× |
| 4 Apoio administrativo | 16 | 3,7% | 6 | 3,1% | 0,8× |
| 5 Serviços e vendas | 31 | 7,1% | 13 | 6,7% | 0,9× |
| 6 Agropecuária | 35 | 8,0% | 12 | 6,2% | 0,8× |
| 7 Produção e reparação | 113 | 25,9% | 20 | 10,4% | 0,4× |
| 8 Operadores de instalações | 51 | 11,7% | 5 | 2,6% | 0,2× |
| 9 Ocupações elementares | 16 | 3,7% | 18 | **9,3%** | 2,5× |

A perda é **bilateral**. Dirigentes e gerentes — candidatos naturais ao grupo exposto — são perdidos a 7,0×, mas **ocupações elementares — candidatas naturais ao controle — são perdidas a 2,5×**, enquanto produção e operadores de instalações, também controle, são retidos em excesso (0,4× e 0,2×).

Isso muda a leitura. Uma perda concentrada só no topo enviesaria o contraste numa direção conhecida; uma perda que atinge topo **e** base deixa a direção indeterminada, o que é mais honesto e menos condenatório do que o texto sugere.

**Direção do viés.** Indeterminada, e o texto atualmente implica que é adversa de um lado só.

**AÇÃO.** Publicar a tabela de nove linhas no Apêndice A e substituir a frase da §4.2 por uma que registre a bilateralidade da perda.
**Prioridade.** Média.

---

## D1 · Usar ponte institucional em duas etapas
`ponte-institucional-cbo-isco` · Tipo S · **Veredito: sólida, subdocumentada**

**A decisão.** CBO 2002 → CBO94/CIUO88 (tábua oficial do MTE) → ISCO-08 (tabela da OIT) → índice.

**Justificação declarada.** §2.4 e §4.2, com o argumento correto: nenhuma etapa é construída pelo autor, e a alternativa de pareamento por semelhança numérica é rejeitada explicitamente.

**Alternativa.** Correspondência semântica por descrição de tarefa, registrada como agenda em §6.6 e não tentada. A recusa é bem argumentada — exigiria validar contra a oficial e demonstrar que remove mais erro do que introduz.

**Momento.** Ex-ante.

**Sensibilidade.** `caged/reconciliation/treatment_classification_validation.json` registra `different_assignments: 0`, `missing_from_reference: 0`, `missing_from_v2: 0`, com 629 famílias nos dois lados. É uma validação **exata** — e é preciso ser claro sobre o que ela valida: **fidelidade de implementação**, ou seja, que o código reproduz a classificação de referência. Ela não valida a **acurácia semântica da ponte**. Nenhum artefato do pacote mede o erro introduzido pela cadeia de duas etapas, e a etapa ISCO-88 → ISCO-08 é ela própria de muitos para muitos.

**Direção do viés.** Erro de medida clássico no tratamento, que atenua estimativas em direção a zero. Isso favorece a leitura conservadora do trabalho: os coeficientes reportados são, se algo, limites inferiores em magnitude. O texto declara o erro de medida em §2.5 e §6.2 mas **não usa esse argumento**, que é favorável.

**Pergunta de banca.** *"Como o senhor sabe que a ponte de duas etapas não introduz mais erro do que resolve?"* — Não sabe, e não pode saber com os dados disponíveis. A resposta defensável é a de atenuação: o erro de medida no tratamento binário empurra os coeficientes para zero, então as estimativas são conservadoras.

**AÇÃO.** Duas frases: uma distinguindo que a validação de 0 divergências é de implementação e não de acurácia semântica; outra invocando a atenuação clássica, para converter a limitação em argumento de conservadorismo.
**Prioridade.** Média.

---

## D3 · Excluir as CBOs sem correspondência como "No score"
`no-score-excluido` · Tipo S · **Veredito: sólida, subdocumentada**

**A decisão.** As 193 famílias sem correspondência oficial recebem rótulo próprio e ficam fora da amostra principal, com declaração explícita de que isso não é exposição nula.

**Justificação declarada.** §4.2 e §6.5, que quantificam o custo: 288 famílias fora, ou 45,8% do total.

**Alternativa.** Imputar pontuação por agregação hierárquica, como se faz na PNAD (`crosswalk-cod-isco-fallback`, B5). A assimetria é notável e não é justificada: **na PNAD o autor imputa por fallback a 3 e 2 dígitos; no CAGED ele exclui**. As duas escolhas são defensáveis isoladamente, mas a diferença entre elas pede uma frase e não recebe nenhuma.

**Momento.** Ex-ante.

**Sensibilidade.** `caged/reconciliation/crosswalk_coverage.json` confirma 629 famílias e 193 sem pontuação. Mas há uma **inconsistência interna no texto**: a Tabela 4.2.2 soma 629 famílias com 193 sem pontuação (batendo com o artefato), enquanto a Tabela 4.2.3, na mesma subseção, registra **194** sem pontuação e soma **630**. A §4.2 também alterna entre "o painel contém 630 famílias" e "das 629 CBOs avaliadas no crosswalk". A diferença de uma família provavelmente separa o painel observado da avaliação do crosswalk, mas o texto não a explica e as duas tabelas vizinhas se contradizem (item V4).

**Direção do viés.** A exclusão preserva a interpretabilidade e é preferível à imputação, que criaria tratamento medido com erro de forma não aleatória.

**AÇÃO.** Reconciliar 629/630 e 193/194 entre as Tabelas 4.2.2 e 4.2.3 com uma nota explicando a diferença de base, e acrescentar uma frase justificando por que a estratégia é exclusão no CAGED e imputação na PNAD.
**Prioridade.** Média (a reconciliação), baixa (a assimetria).

---

## D5 · Agregar correspondências de muitos para muitos
`agregacao-muitos-para-muitos` · Tipo S · **Veredito: sólida, subdocumentada**

**A decisão.** Pontuações dos múltiplos destinos ISCO são agregadas e a regra da OIT é reaplicada; o emprego CBO6 é dividido igualmente entre destinos antes dos pesos de destino.

**Justificação declarada.** §4.2, com o caso 4121 auditado em §6.5.

**Sensibilidade.** `caged/audit/c1_score_landscape.csv` traz um número que o texto não usa: os destinos ISCO médios por família são **2,89 no grupo tratado contra 1,65 no controle**. A diluição por agregação é, portanto, **concentrada no grupo tratado** — quase o dobro de destinos por família. É exatamente a assimetria que produz o Gradiente 4 vazio e que atenua o contraste, e é evidência direta a favor da explicação de diluição que o texto oferece em §4.2 sem sustentar com número.

Também não reportado: `caged/treatment/treatment_variant_support.json` registra `matched_pre_admission_share = 0,789`, isto é, a ponderação por emprego das variantes cobre **78,9%** das admissões pré-tratamento no nível CBO6, com fallback em 2 famílias.

**AÇÃO.** Acrescentar a assimetria de destinos ISCO (2,89 contra 1,65) à §4.2 como sustentação numérica do argumento de diluição, e declarar a cobertura de 78,9% na descrição das variantes.
**Prioridade.** Média.

---

## D12 · Pré-registrar quatro variantes de tratamento
`variantes-de-tratamento` · Tipo S · **Veredito: sólida, subdocumentada**

Quatro regras alternativas, alterando 8, 16 e 53 famílias — confere exatamente com `treatment_variant_support.json` (`V-B: 8, V-C: 16, V-D: 53`). A decisão é sólida: as variantes existem, são pré-registradas, e nenhuma substituiu a principal. Duas lacunas de reporte: a cobertura de 78,9% da ponderação por emprego (ver D5) e o fato de V-D alterar a composição do grupo tratado de forma substantiva, não marginal — tratadas caem de 75 para 67 e não expostas sobem de 266 para 290, além de reabrir o G4 (ver D7). O texto trata as variantes como perturbações pequenas; V-D não é pequena.
**AÇÃO.** Reportar a composição resultante de V-D, não apenas a contagem de famílias alteradas. · Prioridade: média

---

## Demais decisões Tier 2

### D2 · Rejeitar correspondência por semelhança numérica
`sem-correspondencia-adhoc` · **Veredito: sólida**

A correspondência é mantida só quando há ponte institucional identificável. É a decisão que separa este crosswalk de um pareamento ad hoc, e é a razão pela qual as 193 famílias sem match não foram simplesmente encaixadas em códigos parecidos. Custa cobertura e compra interpretabilidade; a troca é a correta e está declarada.
**AÇÃO.** Nenhuma. · Prioridade: —

### D6 · Reunir Gradientes 1–4 num único grupo tratado
`tratamento-gradientes-1-4` · **Veredito: sólida**

O pool atenua a diluição documentada em D5 (2,89 destinos por família tratada): uma ocupação cuja pontuação foi diluída permanece classificada como exposta, ainda que em gradiente mais baixo. A contrapartida — o desenho não sustenta comparações entre gradientes isolados — está declarada em §4.2 e é respeitada na prática, já que as análises por gradiente ficam efetivamente fora do trabalho. Coerente de ponta a ponta.
**AÇÃO.** Nenhuma. · Prioridade: —

### D9 · Definir o controle como `Not Exposed` estrito
`controle-estrito-not-exposed` · **Veredito: sólida**

Excluir as 95 famílias de exposição mínima do controle é justificado por construção: `c1_score_landscape.csv` mostra que elas têm pontuação média de 0,3292, **acima** do máximo do controle (0,32) e sobrepondo-se à faixa inferior dos tratados (mín. 0,28). Um controle que as incluísse seria parcialmente exposto, e o contraste ficaria mecanicamente comprimido. A decisão é ex-ante, declarada e sustentada pelos dados. Toda a vulnerabilidade está no reporte da inversão, não na escolha — ver D10.
**AÇÃO.** Nenhuma (a ação está em D10). · Prioridade: —

### D11 · Congelar a atribuição de tratamento antes da estimação
`tratamento-congelado` · **Veredito: sólida**

A classificação é congelada e as variantes não podem substituí-la por coeficiente ou significância. A verificação é comportamental e passa: V-D produz um grupo tratado bem diferente e não foi promovida; D10 mostra uma configuração que torna três desfechos significativos e ela permanece sensibilidade. O congelamento é observável no comportamento, não só declarado.
**AÇÃO.** Nenhuma. · Prioridade: —

### D13 · Auditar o caso CBO 4121 sob quatro agregações
`auditoria-cbo-4121` · **Veredito: sólida**

O caso mais diluído (destinos com 0,43, 0,65 e 0,70) é verificado sob quatro agregações, três das quais devolvem a mesma classificação, e o resultado é reportado em §6.5 com o relatório dedicado no pacote. Escolher justamente o pior caso para auditar e publicar que uma das quatro discorda é o oposto de seleção favorável.
**AÇÃO.** Nenhuma. · Prioridade: —

### D14 · Reportar a sobreposição residual entre grupos
`sobreposicao-de-pontuacao` · **Veredito: sólida**

§4.2 declara que 72 das 75 tratadas têm pontuação acima do máximo do controle — consistente com `cd_exposure_and_control_summary.json`, que registra faixa de sobreposição [0,28; 0,32] com 64 famílias, das quais 3 tratadas. O artefato vai além e grava `binary_treatment_is_monotone_in_score: false`, isto é, o tratamento binário **não** é monótono na pontuação. Registrar isso em campo próprio, em vez de deixá-lo implícito, é prática de auditoria acima da média.
**AÇÃO.** Opcional: mencionar a não monotonicidade explicitamente em §4.2, já que o artefato a nomeia. · Prioridade: baixa

---

## Itens de verificação abertos

**V3 — Desvio-padrão exato da pontuação na amostra do degrau 05.** Minha estimativa de 0,119 usa as médias e amplitudes por lado de `c1_score_landscape.csv` com heurística de amplitude/4 para a variância intragrupo. O reescalamento de D8 deve usar o desvio-padrão exato, computado sobre as 436 famílias da tabela de tratamento congelada. A conclusão qualitativa é robusta a qualquer valor entre 0,10 e 0,14, mas o número publicado precisa ser exato.

**V4 — Reconciliar 629/630 e 193/194.** A Tabela 4.2.2 soma 629 famílias com 193 sem pontuação; a Tabela 4.2.3 registra 194 e soma 630. Determinar qual base cada tabela usa (avaliação do crosswalk contra painel observado) e alinhar as duas com nota explicativa.

---

## Balanço da fase

Nenhuma decisão de desenho do Bloco D precisa mudar — o crosswalk se defende, o tratamento se defende, o controle estrito se defende, e o congelamento é observável no comportamento e não apenas declarado.

O que precisa mudar é **o que o texto conta sobre o que já foi calculado**. Das seis ações desta fase, cinco consistem em publicar número que já existe no pacote, e duas delas (**D8** e **D10**) tornam o trabalho mais forte, não mais fraco. Isso reforça o padrão da Fase 1: o gargalo deste trabalho é reporte, não método.
