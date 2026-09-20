# Robustez — o que entra na Seção 4 e o que entra na Seção 5

**Rodada 5 do guia.**

A auditoria da V1 registrou robustez **prometida e não reportada** (item 6). Era uma fragilidade
real: o texto anunciava validações que o leitor não encontrava. Agora há material de sobra, e o
risco inverteu — despejar tudo cansa e dilui.

**Divisão sugerida:** a §4.5 diz *o que foi feito e por quê*, em uma frase por exercício. A §5
reporta *o que deu*, só onde o resultado muda a leitura.

---

## Na §4.5 — o catálogo, uma frase cada

Ver `04_SECAO_4.md` para a lista completa dos oito exercícios. O que importa aqui é o critério: a
§4.5 **não traz números**. Ela declara o desenho de cada validação antes de o leitor ver
resultados, que é o que torna a validação crível.

Uma frase que a §4.5 precisa carregar:

> Os exercícios de falsificação foram definidos como regras de parada antes da estimação: um
> resultado que falhasse no placebo temporal seria reportado como falha, não reinterpretado.

---

## Na §5 — quatro resultados que mudam a leitura

### 1. Placebo temporal — reportar o número, não só o veredito

Evento falso em dezembro de 2021, estimado apenas no pré-período verdadeiro. Os cinco outcomes têm
p ≥ 0,05, e o gate passa.

**Mas o salário dá −0,0198 com p = 0,081** — 39% do coeficiente principal, num período em que o
ChatGPT não existia.

Passa no critério. Reportar apenas "passou" seria seletivo, e é o tipo de omissão que uma banca
encontra. **Declare o número e discuta**: é a evidência mais concreta de que parte do diferencial
salarial antecede o evento, e conversa diretamente com a falha de tendências prévias.

**Onde:** §5.1, junto da qualificação do salário.

---

### 2. Placebo de grupo — o resultado mais favorável ao trabalho

500 reatribuições aleatórias preservando o desenho de 75 tratadas em 341 CBOs:

| Outcome | p empírico bilateral | Percentil observado |
|---|---:|---:|
| **Salário real** | **0,002** | **0,0** |
| Saldo | 0,090 | 5,8 |
| Fluxo bruto | 0,271 | 14,0 |
| Desligamentos | 0,295 | 13,8 |
| Admissões | 0,299 | 16,6 |

O coeficiente salarial observado é **mais negativo que todas as 500 reatribuições aleatórias**.

**Por que importa:** é um teste de base no desenho, que não depende da hipótese de tendências
paralelas da mesma forma que o DiD. Com os cinco pretrends falhando, é a evidência mais forte que
resta de que o agrupamento ocupacional não é arbitrário.

Ressalva a manter: reatribuição aleatória não preserva a estrutura de tendências prévias, então o
teste diz *"este agrupamento é especial"*, não *"o timing é causal"*.

**Onde:** §5.1.

---

### 3. Jackknife por ocupação — responde à objeção da concentração

54,1% das admissões tratadas estão em três CBOs — auxiliares administrativos, caixas e
recepcionistas. A objeção óbvia é que o resultado "nacional" seja o dessas três.

Removendo cada uma das 75 ocupações tratadas, uma de cada vez:

| Outcome | Faixa nas 75 remoções | Significativo em |
|---|---|---:|
| **Salário real** | **[−0,0524; −0,0449]** | **100% das remoções** |
| Admissões | [−0,0818; −0,0400] | 1% |
| Desligamentos | [−0,0638; −0,0207] | 1% |

Nenhum outcome troca de sinal. O salário desvia no máximo 0,0059.

**E um resultado que muda a interpretação:** removendo as três maiores **simultaneamente**, as
admissões vão de −0,0538 (p = 0,164) para **−0,1232 (p = 0,002)**. As grandes ocupações
administrativas estavam **atenuando** o efeito de fluxo, não produzindo-o.

Isso não é motivo para trocar a especificação principal — seria seleção sobre o resultado. É
robustez a reportar, com a leitura correta.

**Onde:** §5.1 ou §5.2.6.

---

### 4. Rambachan e Roth — reportar com cuidado

`DeltaRM` e `DeltaSD` sobre o estimando do **event study**,
`average_post_event_time_0_to_23` = −0,0154 (EP 0,0122).

**A armadilha:** justapor "o salário é −0,0507 e significativo" com "o intervalo HonestDiD não
exclui zero nem em M = 0" faz parecer que a manchete é frágil. **São estimandos diferentes**, em
janelas diferentes, com normalizações diferentes. O intervalo convencional do alvo do HonestDiD já
inclui zero antes de qualquer ajuste.

Se for reportar, declare janela e estimando em cada afirmação. Se não houver espaço para fazer isso
direito, **é melhor não reportar** do que reportar de forma que induza ao erro.

Nota adicional: o `DeltaSD` é não informativo neste desenho mesmo em M = 0 — com 24 períodos pós, o
desvio admissível cresce com o quadrado do horizonte.

---

## O que não reportar em §5

- **Porte do estabelecimento** — 50 modelos, zero rejeições após BH. Uma linha na §4.5.
- **Público versus privado** — não executada, porque os campos oficiais codificam forma de registro
  e não propriedade. Uma frase na §4.5, e ela é a favor: declarar não execução é melhor que
  fabricar um contraste que os dados não identificam.
- **Escada completa dos sete degraus** — a tabela inteira cansa. Reporte no texto os dois degraus
  que mudam a leitura: `04_include_minimal_as_control`, que torna as admissões significativas
  (−0,0887, p = 0,022), e `02_pre_treatment_controls_x_post`, que sustenta a decomposição do
  salário. O resto vai para o apêndice ou para o pacote.

---

## Uma decisão que precisa de justificativa escrita

Excluir `Minimal Exposure` — 95 CBOs — **não é neutro**:

| Outcome | Excluindo (principal) | Como controle |
|---|---:|---:|
| Admissões | −0,0538 (p = 0,164) | **−0,0887 (p = 0,022)** |
| Fluxo bruto | −0,0481 (p = 0,174) | **−0,0801 (p = 0,030)** |

A decisão foi herdada da V1 e nunca justificada por escrito. Ela precisa de justificativa — e a
justificativa **não pode ser o p-valor**. O argumento defensável é de desenho: `Minimal Exposure`
está na escala de exposição entre tratados e controles, então incluí-la no controle contamina o
contrafactual com ocupações parcialmente expostas.

Escreva isso, e reporte o degrau 04 como sensibilidade.
