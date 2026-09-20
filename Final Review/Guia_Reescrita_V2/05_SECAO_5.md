# Seção 5 — números e interpretações que mudam

**Rodada 4 do guia.** Todo número conferido contra o artefato que o produz.

---

## §5.1 — resultados nacionais

### Os números

| Outcome | V1 | V2 | Situação |
|---|---:|---:|---|
| Admissões | −0,0309 (0,0263) | **−0,0538** (0,0386) | mais negativo, segue não significativo |
| Desligamentos | −0,0417 (0,0254) | −0,0420 (0,0347) | praticamente igual |
| Salário real de admissão | −0,0207 (0,0140) | **−0,0507** (0,0103) | **de p = 0,140 para p < 0,000001** |
| Saldo (asinh) | −0,6597 (0,3773) | −0,5513 (0,3783) | menor em módulo |
| Fluxo bruto | — | −0,0481 (0,0353) | outcome novo |

### Quatro frases que caem

**1. Linha 440 — *"nenhum é estatisticamente significativo"*.** Falso: o salário rejeita a 5% com
folga. E *"reduções aproximadas de 3,0%, 4,1% e 2,0%"* → **5,4%, 4,2% e 5,1%**.

**2. Linhas 5 e 23 — *"tendências paralelas são rejeitadas para os fluxos"*.** A qualificação "para
os fluxos" implica que o salário estava bem. Agora **os cinco** falham, e a Fase 8A testou mais
cinco especificações — amostra a partir de 2022, nível setorial, exposição contínua, `Minimal
Exposure` como controle, cobertura salarial completa — e **nenhuma passa**. São 51 células.

**3. Linha 442 — *"Para admissões e desligamentos, a interpretação causal é ainda mais limitada"*.**
A restrição vale para todos. Reescreva sem hierarquia.

**4. Linha 456 — *"a evidência mais coerente, no salário de admissão, aponta no máximo para uma
redução modesta"*.** Não é modesta: é 5,1%, precisa, e estável nos quatro horizontes longos
(−0,0514 / −0,0507 / −0,0481 / −0,0548, todos rejeitando a 5%).

### O que explica a falha de tendências paralelas — e isto fortalece o texto

Hoje o texto **admite** a falha. Com a Fase 9 é possível **explicá-la**, o que é muito melhor de
defender. No pré-período, os dois grupos são estruturalmente diferentes:

| | Tratado | Controle |
|---|---:|---:|
| Ocupações | 75 | 265 |
| Salário real médio de admissão | R$ 2.301 | R$ 1.963 |
| Admitidos com superior | **19,7%** | **4,0%** |
| Idade média | 28,9 | 33,8 |
| **Desvio-padrão do crescimento mensal** | **8,3%** | **14,0%** |
| **Amplitude sazonal** | **27,3%** | **44,7%** |

O controle é **68% mais volátil** e **64% mais sazonal**. As maiores ocupações de controle são
manuais e de serviços — manutenção de edificações, alimentadores de linha de produção — contra
administrativas e profissionais no tratado.

**Formulação sugerida:**

> A rejeição das tendências paralelas não é um resultado anômalo: é o que se espera de dois blocos
> ocupacionais com perfis cíclicos tão distintos. No período anterior ao evento, o grupo de controle
> apresenta desvio-padrão de crescimento mensal de 14,0% contra 8,3% do grupo tratado, e amplitude
> sazonal de 44,7% contra 27,3%. Ocupações manuais e de serviços respondem ao ciclo e à
> sazonalidade de forma sistematicamente diferente das ocupações administrativas e profissionais.
> O desenho de exposição ocupacional herda essa diferença estrutural, e nenhuma das especificações
> testadas — incluindo efeitos fixos de setor por mês — a elimina.

Isso converte uma admissão defensiva num argumento com número.

### A qualificação obrigatória do salário

A auditoria da Fase 9 mediu, por dois métodos independentes, que **23% a 29% do diferencial é
composição educacional**, não preço. O share de admitidos com superior cai 2,69 p.p. a mais no
grupo tratado.

Sobra um componente de preço de **−3,6% a −3,9%** — ainda grande, ainda significativo. **Formulação
sugerida:**

> O salário médio de admissão nas ocupações expostas é 5,1% menor que nas não expostas no período
> posterior ao ChatGPT. Cerca de um quarto dessa diferença decorre da mudança na composição
> educacional dos contratados: a participação de admitidos com ensino superior cai 2,7 pontos
> percentuais a mais no grupo exposto. Dentro de faixas de escolaridade comparáveis, o diferencial
> permanece entre 3,6% e 3,9%. O efeito não é composição de idade, sexo ou raça: dentro de cada uma
> dessas dimensões o diferencial é praticamente idêntico ao agregado. Tampouco é jornada — o
> diferencial de salário-hora, de 6,95%, é maior que o mensal.

Isso é **mais forte** que o texto atual, não mais fraco: você antecipa a objeção óbvia e mostra que
o resultado sobrevive a ela.

### O contraste com Canaries precisa ser enfrentado

Canaries **não encontra efeito salarial** (Fact 5, p. 21). Você encontra. Não escondа — explique:

> A ausência de efeito salarial em Brynjolfsson, Chandar e Chen (2025) e a presença de um
> diferencial aqui não são necessariamente contraditórias. Eles medem remuneração do **estoque** de
> empregados; esta seção mede o salário de **admissão**, que é a margem de preço mais flexível.
> Além disso, seus efeitos fixos de firma × tempo absorvem a política salarial da firma, ao passo
> que o desenho ocupacional aqui não a observa. Autor e Thompson (2025), citados pelos próprios
> autores, mostram que o sinal do efeito salarial depende de a tecnologia substituir tarefas
> experientes ou inexperientes, de modo que sinais opostos entre desenhos são teoricamente
> possíveis.

### E o placebo temporal

O placebo de dezembro de 2021 dá **−0,0198 no salário (p = 0,081)** — 39% do coeficiente principal,
num período em que o ChatGPT não existia. Passa no critério de 5%, mas reportar apenas "passou"
seria seletivo. Declare o número.

---

## §5.2.1 — Sexo: a maior baixa

**A afirmação central da subseção não sobrevive.**

| | V1 | V2 |
|---|---:|---:|
| DDD admissões (homens − mulheres) | **+0,0446** (p = 0,018) | **+0,0116** (p = 0,803, BH 0,907) |
| DDD salário | −0,0209 (p = 0,205) | −0,0022 (BH 0,907) |

O diferencial de gênero nas admissões **desaparece**. O DiD dentro de cada grupo é negativo e
parecido nos dois — homens −0,0779 (BH p = 0,019), mulheres −0,0724 (BH p = 0,228).

O único contraste de sexo que sobrevive ao BH é o saldo, +0,799 — e o saldo tem o pior histórico de
pretrend de todos os outcomes, com 21 dos 22 leads individualmente significativos.

**Frases a reescrever:** toda a síntese da linha 506, e a implicação de política sobre convergência
entre os sexos.

**Mas o nulo é informativo, e vale dizer isso:** a Seção 3 mostra que mulheres estão mais expostas;
a Seção 5 mostra que o ajuste pós-ChatGPT **não** foi diferencial por sexo. Exposição desigual sem
ajuste diferencial é uma afirmação forte e defensável.

---

## §5.2.2 — Raça: sobrevive e fica mais forte, mas muda de lugar

O DDD do agregado `Negra` sobrevive ao BH em três outcomes:

| Outcome | DDD | BH p |
|---|---:|---:|
| Admissões | −0,1144 | 0,015 |
| Desligamentos | −0,0990 | 0,015 |
| Fluxo bruto | −0,1068 | 0,015 |

**Duas coisas que o texto precisa dizer e hoje não diz:**

1. **O efeito está concentrado em pardos.** No desagregado, pardos dão −0,089 nos desligamentos
   (BH p = 0,018) e pretos +0,045 não significativo (BH p = 0,341). Agregar esconde isso.
2. **O agregado é mais forte que qualquer componente**, e isso parece contradição sem explicação.
   Não é: são contrastes diferentes. `Negra` compara com branca, amarela, indígena e não
   identificada; `parda` compara com um complemento que **inclui pretos**. Escreva essa frase, ou o
   leitor que comparar a Tabela 5.2.2 com a A.3 vai achar que uma está errada.

**Resultado novo:** a categoria **amarela** tem os maiores coeficientes de toda a família —
admissões −0,277, desligamentos −0,218, ambos BH p < 1e-4, com suporte adequado. A V1 não a
reportava.

---

## §5.2.3 — Idade: a leitura inverte

A V1 e o resumo falam em jovens atingidos. **Os dados dizem outra coisa.**

| Coorte | DDD admissões | BH p |
|---|---:|---:|
| 22–25 | −0,0189 | 0,652 |
| 41–49 | **+0,0841** | **0,0043** |

Não é que os jovens sejam atingidos de forma diferencial — é que **os de 41 a 49 são poupados**. O
DDD de 22–25 é pequeno e não significativo.

**Reescreva nesses termos.** A diferença importa para a comparação com Canaries, que encontra queda
de 12 pontos log para 22–25 (p. 19). Lá o efeito é dos jovens; aqui é a ausência de efeito nos de
meia-idade que gera o contraste.

**E há o achado mais defensável do trabalho inteiro, que hoje não é destacado:** no DiD **dentro**
da coorte 22–25, o salário cai −0,0517 com p = 1e-06 **e o pretrend passa** — teste conjunto
p = 0,585. É o único contraste da dissertação cuja identificação sobrevive ao diagnóstico.

Ressalva obrigatória: é 1 entre 100 contrastes de diagnóstico, sem ajuste de multiplicidade sobre a
família de pretrends. Mas merece parágrafo próprio, porque alinha com o enquadramento de porta de
entrada e com o artigo de referência.

---

## §5.2.4 — Escolaridade: direção se mantém, significância não

Superior: DDD de admissões **−0,1108**, nominal p = 0,0145, **BH p = 0,055**. Passa raspando do
lado errado da linha. O fluxo bruto sobrevive (BH p = 0,048) e o saldo também (BH p = 0,015).

No DiD dentro do grupo, superior dá −0,1075 (BH p = 0,017) e fundamental +0,0018 (BH p = 0,974).

A frase *"a retração das admissões é mais forte entre trabalhadores com ensino superior"* continua
verdadeira em direção e magnitude, **mas precisa da qualificação de significância ajustada**.

---

## §5.2.5 — Renda: não se sustenta, e aparece outra coisa

A V1 afirmava redução dos desligamentos concentrada na renda intermediária. Na V2 o DDD de
desligamentos da faixa média é −0,054 com p = 0,55. **Não se sustenta.**

O que aparece: DiD de admissões da faixa média em **−0,1914 (BH p = 0,021)** — mas com suporte
`limited` (26 CBOs tratadas, 32 de controle). E o DDD de salário da faixa alta em +0,064
(BH p = 0,043) com suporte **`thin`: 3 CBOs tratadas e 6 de controle**.

**O resultado de renda alta não deve entrar na prosa.** Três ocupações não sustentam afirmação. Ele
fica na tabela com o rótulo de suporte ao lado, e só.

---

## §5.2.6 — Síntese

Precisa ser reescrita a partir dos cinco eixos acima, e ganha a **Figura 5.2.6** (forest plot).

**Frase-chave que a subseção precisa carregar:**

> Dos 100 contrastes de diferença tripla, 34 são nominalmente significativos e 21 sobrevivem ao
> ajuste de Benjamini-Hochberg. A heterogeneidade detectável concentra-se em raça/cor e em faixa
> etária; sexo e renda não apresentam diferencial robusto, e escolaridade fica no limite da
> significância ajustada.

---

## §5.3 — Casos ocupacionais

Duas correções, já implementadas nos artefatos: base de normalização em **novembro de 2022** (era
outubro), e medida-resumo nos **12 meses terminais**, junho de 2025 a maio de 2026 (era janeiro a
junho de 2025).

**Composição a declarar:** 53 dos 76 códigos estão em um único caso, supervisores de produção, e 60
dos 80 mapeamentos têm confiança `medium`. Reportar a composição, não só o total.

O caráter descritivo se mantém: sem estrela, sem p-valor, sem linguagem causal.

**Se o Apêndice B ficar adiado**, remova as duas promessas a ele nas linhas 730 e 764.

---

## A acomodação silenciosa

Esta é a mudança narrativa mais delicada e vale para a §5.1 e para a §5.2.6.

A hipótese é que admissões e desligamentos caem juntos porque há **menor rotatividade**, não
destruição de vínculos. Na V1 era hipótese porque não havia como testar.

**A V2 testou e não confirma.** A decomposição em seis famílias de desligamento dá:

| Família | Coeficiente | BH p |
|---|---:|---:|
| Demissão sem justa causa | −0,00002 | 0,9995 |
| Pedido de demissão | −0,1166 | 0,3299 |

Se fosse menor rotatividade, a queda estaria concentrada em pedido de demissão e demissão sem justa
causa. Não está.

Isso **não refuta** a hipótese — tira dela o apoio que o texto sugere existir. Rebaixe de "hipótese
com indícios" para "hipótese que a decomposição disponível não sustenta", e diga qual evidência a
confirmaria.

---

## Uma limitação de dado a declarar

`tipomovimentacao` é **93,2% "tipo ignorado" nas admissões** e apenas 0,08% nos desligamentos. Isso
valida a decomposição de desligamentos e **inviabiliza** qualquer decomposição da porta de entrada
por tipo de admissão — primeiro emprego, reemprego. Declare como limitação em vez de deixar um
arguidor descobrir.
