# Régua de calibração — três decisões que resolvem 55 linhas

**Data:** 3 de agosto de 2026
**Problema:** em 13 das 42 comparações cegas, os dois leitores discordam do veredito. A discordância **não é sobre o que
a fonte diz** — é sobre onde fica a linha entre "folga retórica aceitável" e "exagero". Um terceiro leitor produz um
terceiro ponto na mesma nuvem. O que converge é um critério escrito.

O padrão das divergências mostra que são três perguntas, sempre as mesmas:

| Só o primário acusou | n | | Só o QC acusou | n |
|---|---:|---|---|---:|
| `GENERALIZATION_OVERCLAIM` | 5 | | `PARTIAL_SCOPE` | 6 |
| `WRONG_POPULATION` | 2 | | | |
| `AUTHOR_INFERENCE_UNSUPPORTED` | 2 | | | |

---

## Decisão 1 — População: quando trocar o universo conta como erro?

**Caso concreto (ROW-0001).** A dissertação escreve *"32,1% dos trabalhadores dos Estados Unidos"*. A fonte mede
*employed respondents de 18 a 64 anos, N = 6.935*, em pesquisa nacionalmente representativa. O primário marcou
`WRONG_POPULATION` + `GENERALIZATION_OVERCLAIM` → OVERSTATED. O cego leu a mesma página e disse SUPPORTED.

**Regra proposta.** Marcar `WRONG_POPULATION` somente quando a troca **muda a ordem de grandeza ou o sinal** do que se
afirma. Restrições de faixa etária, de condição de ocupação ou de desenho amostral em pesquisa representativa não contam,
desde que o texto não atribua o número a um universo mais amplo do que o país da fonte.

*Efeito:* ROW-0001 vira SUPPORTED. Recomendo esta. Um leitor de dissertação entende "trabalhadores dos Estados Unidos"
como a população da pesquisa; exigir a glosa completa em cada menção tornaria o texto ilegível.

*Alternativa mais dura:* exigir a restrição explícita na primeira menção de cada fonte, e liberar as menções seguintes.
Custa uma frase por obra e é defensável diante de banca exigente.

---

## Decisão 2 — Generalização: `GENERALIZATION_OVERCLAIM` ou `PARTIAL_SCOPE`?

É a divergência mais frequente: o primário vê exagero, o cego vê escopo parcial — mesmo fato, gravidade diferente.

**Regra proposta.** A distinção é **direcional**, não de grau:

- `PARTIAL_SCOPE` — a afirmação é verdadeira para parte do que a fonte cobre e o texto **não nega** o resto. Falta
  qualificação. **Não rebaixa o veredito abaixo de PARTIALLY_SUPPORTED.**
- `GENERALIZATION_OVERCLAIM` — a afirmação seria **falsa** se aplicada ao escopo completo, ou a fonte afirma
  explicitamente o contrário em outro ponto. **Rebaixa para OVERSTATED.**

*Teste operacional:* a fonte contradiz em algum lugar? Se sim, é exagero. Se apenas não cobre, é escopo parcial.

*Efeito:* ROW-0186 e ROW-0187 **permanecem** OVERSTATED sob esta régua — a fonte afirma na p. 4 o contrário do que a
dissertação lhe atribui. Isso é bom sinal: a régua não é uma anistia, ela separa o que é lapso de redação do que é
leitura errada da fonte.

---

## Decisão 3 — Inferência do autor: quando ela é "não sustentada"?

88 das 227 linhas são `AUTHOR_INFERENCE` — interpretação, comparação ou consequência metodológica que o autor deriva da
fonte, não algo que a fonte afirme. `AUTHOR_INFERENCE_UNSUPPORTED` aplicado com rigor máximo condenaria quase toda
discussão de literatura já escrita.

**Regra proposta.** Marcar `AUTHOR_INFERENCE_UNSUPPORTED` somente se **uma** das duas condições valer:

1. alguma premissa factual da inferência é falsa segundo a fonte; **ou**
2. a inferência é apresentada como achado da fonte, e não como leitura do autor.

Divergir da fonte, ou ir além dela, com premissas corretas e atribuição correta, **não** é defeito — é o que uma revisão
de literatura faz.

*Efeito:* ROW-0004 vira SUPPORTED. Recomendo esta.

---

## O que decidir

Três respostas, uma vez. Sugiro **1-branda, 2-direcional, 3-branda** — é o conjunto que mantém severidade onde a fonte é
contradita e a retira onde o problema é só falta de glosa.

Depois de fixadas, as 55 linhas de calibração são reclassificadas em lote, sem revisor cego, e o teste cego fica
reservado às 12 do balde 1.

**Ordem obrigatória:** a régua entra em vigor por escrito **antes** da reclassificação, e a reclassificação não pode
reabrir linha alguma olhando para o veredito que se prefere. É a mesma disciplina do `PRE_REGISTRO_V3.md`: o critério
é declarado antes de ser aplicado ao caso.
