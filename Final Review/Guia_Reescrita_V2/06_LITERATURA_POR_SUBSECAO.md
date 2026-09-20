# Literatura, subseção por subseção

**Rodada 4 do guia.** Toda afirmação sobre um artigo vem do PDF, com página.

Problema de fundo, medido: **`brynjolfsson_canaries_2025` é citado 16 vezes** no texto, contra 6 de
Klein Teeselink, 6 de Hosseini Maasoum, 2 de Humlum e 2 de Aldasoro. Três artigos da pasta são
citados **zero** vezes — `adamczyk_skills_2024`, `teutloff_winners_2025`, `hui_short-term_2024`.

O trabalho se apoia quase inteiramente num artigo. Com os números novos, isso ficou pior: em dois
pontos centrais a V2 **diverge** do Canaries, e o texto não tem outra literatura para se apoiar.

---

## §4.1 — o desenho

**O que está lá:** Canaries como referência única, com descrição imprecisa do painel ADP.

**Corrigir:** o desenho deles é firma × quintil de exposição × mês, com **regressão de Poisson**
(p. 15, eq. 4.1), efeitos fixos de firma×quintil e **firma×tempo**, agrupamento por firma (p. 19).

**Acrescentar:** o parágrafo de convenção temporal. Humlum e Vestergaard (p. 12, nota 8) registram
que estudos de evento centrados em novembro de 2022 *"have become common in the literature"*,
citando cinco trabalhos — o que justifica a referência da V2 sem que seja escolha sua.

---

## §4.3 — o estimador

**Acrescentar, e é a citação mais valiosa do guia:** Canaries, p. 19, nota 17 —

> *"Because of zero counts in the outcome variable, we estimate a Poisson regression instead of an
> OLS regression in logs following guidance from Chen and Roth (2024)."*

Seu artigo de referência usa **o mesmo estimador da V2, pelo mesmo motivo, citando a fonte**. A V1
usava `log(1+y)`; a mudança para PPML alinha o trabalho com a fronteira, e agora há como dizer isso.

---

## §5.1 — o resultado nacional

### O contraste que não pode ser evitado

**Canaries não encontra efeito salarial** (Fact 5, p. 21): *"a less marked divergence in
compensation compared to employment"* e *"little difference in compensation trends by age or
exposure quintile"*. A V2 encontra −5,1%, significativo.

O texto atual (linha 454) usa Canaries para apoiar a leitura de nulidade agregada. **Isso deixou de
funcionar para o salário.** Reescreva como contraste explicado, não como concordância:

- ele mede remuneração de **estoque**; você mede salário de **admissão**;
- os efeitos fixos de firma × tempo dele absorvem política salarial da firma;
- **Autor e Thompson (2025)**, citados por ele na p. 21, mostram que o sinal do efeito salarial
  depende de a tecnologia substituir tarefas experientes ou inexperientes — sinais opostos entre
  desenhos são teoricamente possíveis;
- **Davis e Krolikowski (2025)**, também citados ali, dão a alternativa da rigidez de curto prazo.

### Humlum inverte de aliado a contraste

O texto (linha 454) cita Humlum para "efeitos nulos e precisos". Isso continua verdadeiro **no
resultado dele**. Mas a V2 rodou a especificação dele e obteve o oposto.

Humlum, p. 15, nota 11: *"because these trends entirely predate AI chatbots, the pooled
difference-in-differences (which control for pre-trends) are precise zeros"*. A Equação 2 dele
(p. 13) acrescenta tendência linear específica do grupo tratado — que é exatamente a especificação
`02_differential_linear_trend` da Fase 8A.

**Na V2, controlar pela tendência prévia não zera nada:** os coeficientes ficam praticamente iguais
e mais precisos — admissões vão de p = 0,164 para p = 0,0004. Isso merece um parágrafo, e é a favor
do seu resultado.

### Klein Teeselink: a descrição atual está correta, mas subutilizada

A auditoria da V1 já corrigiu a descrição (item 15). O que falta é usar o desenho dele: efeitos
fixos de **indústria × período** na equação principal (p. 11), exposição **contínua padronizada**, e
janela assimétrica de 15 pré e 30 pós.

São três precedentes diretos para escolhas da V2 que hoje aparecem sem apoio: o nível 2 setorial, o
degrau de exposição contínua, e a janela `−23…+41`.

---

## §5.2.1 — Sexo

O texto (linha 504) diz que o resultado *"contrasta parcialmente"* com Canaries, que encontra
efeitos semelhantes para homens e mulheres.

**Com os números novos, deixou de contrastar: passou a concordar.** O DDD de gênero na V2 é +0,0116
com BH p = 0,907 — não há assimetria detectável, exatamente como neles.

Reescreva como convergência. E use o espaço para a afirmação que a Seção 3 sustenta: exposição
desigual entre sexos, ajuste pós-ChatGPT que não é diferencial.

---

## §5.2.2 — Raça

O texto (linha 548) registra que os principais estudos **não apresentam estimativas causais
desagregadas por raça**. Isso continua verdadeiro e é uma boa observação — mantenha.

**O que muda:** o resultado agora sobrevive ao ajuste de multiplicidade em três outcomes, e o efeito
está concentrado em pardos, não em pretos. É contribuição própria, sem paralelo na literatura
citada. Vale dizer que é contribuição.

---

## §5.2.3 — Idade

**A subseção mais afetada.**

Canaries encontra queda de 12 pontos log para 22–25 nas ocupações mais expostas (p. 19), e o texto
constrói a comparação em cima disso.

Na V2, o DDD de 22–25 é **−0,0189 com BH p = 0,652** — nada. O que sobrevive é **41–49 com +0,0841
(BH p = 0,0043)**: os de meia-idade são poupados.

A direção é compatível — jovens relativamente pior que os de 41–49 —, mas o mecanismo estatístico é
outro, e a magnitude não se compara. Reescreva com precisão em vez de analogia.

**E há um ponto de convergência forte que o texto não tem:** no DiD dentro da coorte 22–25, o
salário cai 5,17% **e o pretrend passa** (p conjunto 0,585). É o único contraste do trabalho cuja
identificação sobrevive, e alinha com o enquadramento de porta de entrada do artigo de referência.

Aqui cabe também `hosseini_maasoum_generative_2025`, hoje citado 6 vezes mas nunca na §5.2.3: o
título dele é literalmente *"Generative AI as seniority-biased technological change"*.

---

## §5.2.4 e §5.2.5 — Escolaridade e renda

Sem literatura citada hoje. **Duas oportunidades:**

- **Klein Teeselink** documenta deslocamento da composição para posições sêniores em firmas mais
  expostas (p. 8): a participação de alta senioridade sobe 0,5 p.p. contra 0,2 p.p. nas menos
  expostas. É o análogo firma-nível do que você vê em escolaridade.
- **Adamczyk, Ehrl e Monasterio (2024)** dão o contexto brasileiro de polarização e mudança
  enviesada à rotina, com RAIS 2003–2018. É a âncora nacional que falta ao trabalho inteiro.

---

## Onde a literatura brasileira entra

`adamczyk_skills_2024` é o único artigo brasileiro da pasta e é citado **zero vezes**. Ele não é
sobre IA — é sobre habilidades, RBTC e polarização no Brasil — e serve para duas coisas:

1. ancorar o trabalho numa tradição nacional, lacuna nº 13 da auditoria da V1;
2. fornecer a bibliografia brasileira que falta. A referência mais importante que ele traz é
   **Maciente (2013)**, o mapeamento O*NET ↔ CBO já consolidado no Brasil.

**Maciente merece parágrafo na §4.2**, não nota de rodapé: existe um crosswalk brasileiro
estabelecido, e você construiu outro. A razão é boa — o índice da OIT é nativo em ISCO-08, não em
O*NET — mas precisa estar escrita, porque uma banca brasileira pergunta.

---

## Três artigos que você tem e não usa

| Artigo | Onde caberia |
|---|---|
| `hui_short-term_2024` | mercado de trabalho online, efeitos de curtíssimo prazo — §5.1, como contraste de contexto |
| `teutloff_winners_2025` | citado por Humlum como parte da convenção de nov/2022 — §4.1 |
| `aldasoro_ai_2026` | citado 2 vezes; poderia sustentar a discussão de produtividade sem efeito de emprego — §5.1 |

Não é obrigatório usar os três. Mas citar 16 vezes um único artigo, num trabalho que agora diverge
dele em dois pontos, é fragilidade que uma banca nota.
