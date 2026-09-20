# Auditoria metodológica da V2 — relatório

**Data:** 27 de julho de 2026
**Escopo:** desenho, não código. Consistência interna já foi auditada duas vezes.
**Regra:** nenhum achado entra sem evidência numérica. Comandos e arquivos em `evidencia/`.

---

## Resumo

| Nível | O que significa | Achados |
|---|---|---:|
| **1** | Invalida uma afirmação central | **0** |
| **2** | A afirmação sobrevive, mas exige qualificação | **6** |
| **3** | Apresentação ou limitação a declarar | **3** |

**Nenhum achado de Nível 1.** Uma das suspeitas com que entrei — transferências entre
estabelecimentos inflando os fluxos — foi **refutada com número**, e a explicação que o texto já dá
para o Gradiente 4 vazio foi **confirmada**.

O resultado mais importante é positivo: o diferencial salarial, que é o único achado nacional
significativo, **sobrevive a todos os testes de robustez desta auditoria**. O que ele exige é uma
qualificação de magnitude, não de existência.

---

## Tabela de achados

| # | Bloco | Achado | Evidência | Nível |
|---|---|---|---|---|
| 1 | A | 23% a 29% do diferencial salarial é composição educacional, não preço | dois métodos independentes: 22,7% e 29,1% | **2** |
| 2 | C | O tratamento binário **não é monótono** no score de exposição: 3 CBOs tratadas e 30 de controle ocupam a mesma faixa `[0,28; 0,32]` | 64 CBOs na faixa de sobreposição | **2** |
| 3 | C | As 193 CBOs sem score (30,7%) não são aleatórias: gerentes são 19,2% delas contra 2,8% das classificadas | sobre-representação de 7× | **2** |
| 4 | D | O grupo de controle é **68% mais volátil** e **64% mais sazonal** que o tratado no pré-período | SD de crescimento 14,0% vs 8,3% | **2** |
| 5 | D | Excluir `Minimal Exposure` muda a conclusão das admissões de não significativa para significativa | −0,0538 (p=0,164) vs −0,0887 (p=0,022) | **2** |
| 6 | B | Retirar as três maiores ocupações tratadas **fortalece** os fluxos, em vez de enfraquecê-los | admissões −0,0538 → −0,1232 (p=0,002) | **2** |
| 7 | E | `tipomovimentacao` é 93,2% "tipo ignorado" nas admissões; nos desligamentos, só 0,08% | inviabiliza decomposição da porta de entrada | **3** |
| 8 | C | O Gradiente 4 está vazio por aritmética: o maior score observado é 0,5933 e o limiar é 0,60 | distância de 0,0067 | **3** |
| 9 | F | Quatro perguntas prováveis de banca não têm resposta escrita no pacote | — | **3** |

**Refutado:** transferências entre estabelecimentos. Códigos 70 e 80 têm **zero ocorrências** no
vintage congelado — o Novo CAGED, baseado no eSocial, não os reporta. A preocupação vinha do CAGED
antigo e não se aplica.

---

## Bloco A — O salário é preço ou composição?

Era a pergunta mais perigosa, porque o salário de admissão é o único resultado nacional
significativo e o outcome é a **média salarial de quem foi contratado**. Se ocupações expostas
passaram a contratar gente menos escolarizada, a média cai sem que o preço do trabalho mude.

O deslocamento existe e está medido. Entre pré e pós, no tratado contra o controle:

| Escolaridade dos admitidos | DiD |
|---|---:|
| Superior | **−2,69 p.p.** |
| Médio | −0,07 p.p. |
| Fundamental ou menos | **+2,76 p.p.** |

**Dois métodos independentes concordam sobre o tamanho.** A decomposição tipo Oaxaca, ponderando os
efeitos dentro de cada faixa de escolaridade pelas participações pré-tratamento, atribui **22,7%** à
composição. O degrau `02_pre_treatment_controls_x_post`, que já existia no pacote, atribui **29,1%**.

Isso deixa o componente de preço entre **−0,036 e −0,039** — ainda grande e ainda significativo.

**E é especificamente escolaridade.** Nas outras dimensões o efeito é praticamente idêntico dentro
de cada grupo, o que significa que elas não carregam composição:

| Dimensão | Efeitos dentro dos grupos | Média |
|---|---|---:|
| Idade (Canaries) | −0,058 a −0,037 | −0,047 |
| Idade (PNAD) | −0,055 a −0,042 | −0,048 |
| Sexo | −0,050 e −0,049 | −0,050 |
| Raça/cor | −0,071 a −0,026 | −0,051 |
| **Escolaridade** | **−0,043 a −0,008** | **−0,029** |

Só escolaridade fica sistematicamente abaixo do agregado de −0,051.

**A jornada aponta na direção contrária.** O salário-hora é **−0,0695**, maior em módulo que o
mensal de −0,0507, e as horas semanais são +0,0016. Não há diluição por jornada; se algo, o efeito
por hora é mais forte.

### O que isso exige do texto

A frase *"o salário de entrada é 5% menor"* precisa virar algo como: *o salário médio de admissão é
5,1% menor, dos quais cerca de um quarto se deve à mudança da composição educacional dos
contratados; dentro de faixas de escolaridade comparáveis, o diferencial é de 3,6% a 3,9%.*

Isso é mais forte, não mais fraco: você antecipa a objeção e mostra que o resultado sobrevive a ela.

**Evidência:** `evidencia/a1_education_composition_shift.csv`,
`a2_wage_price_composition_split.csv`, `a3_wage_within_dimension_range.csv`,
`a_wage_composition_summary.json`.
**Comando:** `.venv/bin/python code/audit/wage_composition.py`

---

## Bloco B — O resultado é de 75 ocupações ou de três?

54,1% das admissões tratadas estão em três CBOs — 4110, 4211 e 4221, todas administrativas. O
controle é mais disperso (33,9%). Como o PPML pondera pelo tamanho, o coeficiente "nacional"
poderia ser, na prática, o de escriturários.

**Jackknife com 375 modelos: 75 remoções × 5 outcomes.**

| Outcome | Base | Faixa nas 75 remoções | Troca de sinal | Fração significativa |
|---|---:|---|---:|---:|
| **Salário real** | −0,0507 | **[−0,0524; −0,0449]** | 0 | **100%** |
| Admissões | −0,0538 | [−0,0818; −0,0400] | 0 | 1% |
| Desligamentos | −0,0420 | [−0,0638; −0,0207] | 0 | 1% |
| Fluxo bruto | −0,0481 | [−0,0733; −0,0309] | 0 | 1% |
| Saldo | −0,5513 | [−0,6300; −0,3750] | 0 | 0% |

**O salário é notavelmente robusto:** desvio máximo de 0,0059 e significância em todas as 75
remoções. A ocupação mais influente é a 7686, e mesmo ela move o coeficiente em menos de seis
milésimos. O resultado não é de nenhuma ocupação em particular.

**Os fluxos nunca trocam de sinal e nunca ficam significativos.** Consistentemente negativos,
consistentemente imprecisos.

**Mas há um resultado que muda a interpretação.** Retirando as três maiores simultaneamente:

| Outcome | Com as três | Sem as três |
|---|---:|---:|
| Admissões | −0,0538 (p=0,164) | **−0,1232 (p=0,002)** |
| Fluxo bruto | −0,0481 (p=0,174) | **−0,1034 (p=0,011)** |
| Salário | −0,0507 | −0,0520 |

As grandes ocupações administrativas estavam **atenuando** o efeito de fluxo, não produzindo-o. Nas
ocupações expostas de porte médio, a queda de admissões é mais que o dobro e é significativa.

Isso é material e não está no texto. Não é razão para trocar a especificação principal — seria
seleção sobre o resultado —, mas é uma robustez que vale reportar.

**Evidência:** `evidencia/b1_concentration.csv`, `b2_leave_one_out.csv`,
`b3_drop_three_largest.csv`, `b4_unweighted_comparison.csv`, `b_jackknife_summary.json`.
**Comando:** `.venv/bin/python code/audit/jackknife_occupations.py`

---

## Bloco C — A medida de exposição

É a contribuição declarada número um da dissertação, e é onde estão os dois achados mais
desconfortáveis.

### O tratamento não é monótono no score

A regra V-A combina o score médio com o desvio-padrão agrupado entre os destinos ISCO de cada CBO.
A consequência é que o tratamento binário **não é função monótona da exposição**:

| Lado | CBOs | Faixa de score |
|---|---:|---|
| Tratado | 75 | 0,280 a 0,593 |
| `Minimal Exposure` (excluído) | 95 | 0,220 a 0,410 |
| Controle | 266 | 0,090 a 0,320 |

Na faixa **[0,280; 0,320]** convivem **64 CBOs**: 30 no controle, 31 excluídas e 3 tratadas. Duas
ocupações com o mesmo score de exposição podem acabar em lados opostos do tratamento.

A atenuante é quantitativa: 72 das 75 tratadas (96%) estão acima do máximo do controle. A faixa de
ambiguidade é estreita. Mas ela existe e deve ser declarada.

### As 193 sem score não são aleatórias

30,7% das famílias CBO não recebem score. Sua distribuição por grande grupo é bem diferente da das
classificadas:

| Grande grupo CBO | % das sem score | % das classificadas |
|---|---:|---:|
| 1 — Dirigentes e gerentes | **19,2%** | **2,8%** |
| 9 — Manutenção e reparação | 9,3% | 3,7% |
| 7 — Bens e serviços industriais | 10,4% | 25,9% |
| 8 — Processos contínuos | 2,6% | 11,7% |

Gerentes estão **sete vezes** mais representados entre as ocupações perdidas do que entre as
mantidas — e gerência é um dos grupos mais expostos à IA generativa na literatura. A perda é
sistemática e vai contra o achado.

### O Gradiente 4 vazio está explicado corretamente

O maior score observado entre as 436 CBOs pontuadas é **0,5933**; o limiar do Gradiente 4 é
**0,60**. Ele está vazio por **0,0067** — por aritmética, não por escolha. A média sobre os destinos
ISCO (1,96 por família, com desvio agrupado de 0,097) não consegue ultrapassar o limiar.

**A explicação de diluição que o texto já dá está correta.** Vale citar o número do teto, porque um
argumento com 0,5933 nele é muito mais forte que um argumento qualitativo.

**Evidência:** `evidencia/c1_score_landscape.csv`, `c2_unscored_profile.csv`,
`cd_exposure_and_control_summary.json`.
**Comando:** `.venv/bin/python code/audit/exposure_and_control.py`

---

## Bloco D — O grupo de controle é comparável?

No pré-período, os dois grupos são estruturalmente diferentes:

| | Tratado | Controle |
|---|---:|---:|
| Ocupações | 75 | 265 |
| Salário real médio de admissão | R$ 2.301 | R$ 1.963 |
| Admitidos com superior | **19,7%** | **4,0%** |
| Idade média | 28,9 | 33,8 |
| **Desvio-padrão do crescimento mensal** | **8,3%** | **14,0%** |
| **Amplitude sazonal** | **27,3%** | **44,7%** |

O controle é **68% mais volátil** e **64% mais sazonal**. Dois blocos com perfis cíclicos tão
distintos dificilmente teriam trajetórias paralelas na ausência do tratamento — e é a explicação
mais econômica para as 51 células de pretrend falharem.

Isto não é achado novo no sentido de mudar um número. É o que transforma *"as tendências paralelas
falham"* de constatação em **explicação**, e uma explicação com números é muito melhor de defender
do que uma admissão sem eles.

### A exclusão de `Minimal Exposure` não é neutra

| Outcome | Excluindo (principal) | Como controle (degrau 04) |
|---|---:|---:|
| Admissões | −0,0538 (p=0,164) | **−0,0887 (p=0,022)** |
| Fluxo bruto | −0,0481 (p=0,174) | **−0,0801 (p=0,030)** |
| Salário | −0,0507 (p<0,001) | −0,0456 (p<0,001) |

Incluir as 95 ocupações de exposição mínima no controle torna o resultado de admissões
significativo. A decisão de excluí-las foi herdada da V1 e nunca justificada por escrito. Ela
precisa de justificativa — e a justificativa não pode ser o p-valor.

**Evidência:** `evidencia/d1_pre_period_comparability.csv`,
`cd_exposure_and_control_summary.json`.

---

## Bloco E — Transferências: refutado

`build_panel.py` não lê `tipomovimentacao`, então admissões e desligamentos são definidos só pelo
saldo. No CAGED antigo isso incluiria transferências entre estabelecimentos, que não são entrada
nem saída do emprego formal.

**No Novo CAGED os códigos 70 e 80 têm zero ocorrências em 253.883.019 registros.** O regime do
eSocial não os reporta. A preocupação não se aplica.

O mesmo scan trouxe outra coisa. A usabilidade do campo é radicalmente assimétrica:

| Fluxo | Código mais frequente | Participação |
|---|---|---:|
| Admissões | 97 — "tipo ignorado" | **93,2%** |
| Desligamentos | 98 — "tipo ignorado" | **0,08%** |

Os desligamentos são bem codificados — 45,6% sem justa causa, 34,5% a pedido, 16,3% término de
contrato —, o que valida a decomposição de mecanismos da V2. As admissões não são: **93% não têm
tipo**. Qualquer análise de porta de entrada por tipo de admissão — primeiro emprego, reemprego —
está inviabilizada pelo dado, e isso deve ser declarado como limitação em vez de descoberto por um
arguidor.

**Evidência:** `evidencia/e1_transfer_share_by_year.csv`,
`e2_movement_type_distribution.csv`, `e_transfer_summary.json`.
**Comando:** `.venv/bin/python code/audit/transfer_share.py`

---

## Bloco F — Quatro respostas que faltam por escrito

Nenhuma muda um número. A ausência delas custa caro numa arguição.

**1. Por que TWFE e não Callaway–Sant'Anna ou Sun–Abraham?** Porque não há escalonamento: a data de
tratamento é única (dezembro de 2022) e existe um grupo nunca tratado. O problema de pesos
negativos de Goodman-Bacon surge da comparação entre coortes tratadas em momentos diferentes, que
aqui não existe. Com adoção simultânea e controle nunca tratado, o estimador de dois períodos e
dois grupos é não viesado sob tendências paralelas. **A ausência dessa frase é o que faz parecer
que o autor desconhece a literatura recente.**

**2. Por que PPML e não OLS em log?** Porque o outcome é contagem com zeros, porque `log(1+y)` não
identifica a elasticidade em nível na presença de heterocedasticidade, e porque o coeficiente PPML
é semi-elasticidade da média condicional em nível. A V2 reporta os dois: −0,0538 no PPML e −0,0107
no OLS secundário. A diferença é real e deve ser explicada, não escondida.

**3. O que `asinh(saldo)` não é.** Não é percentual, não é elasticidade e não é estoque de emprego.
É transformação de uma variável que aceita zero e negativo.

**4. Sobre a inferência.** 341 clusters de CBO4 são folgados para inferência assintótica; não é
preciso wild bootstrap. E o agrupamento bidirecional com divisão CNAE produziu matriz de
covariância **não positiva semidefinida em três das dez células** do nível 2 — medido na Fase 8A.
Os p-valores de pretrend de 0,269 e 0,555 daquelas células não são interpretáveis, e o pacote já os
marca.

---

## O que fazer com isto

**Nada precisa ser reestimado.** Não há Nível 1, e a especificação principal não muda.

Três coisas entram no texto quando você escrever:

1. **A qualificação do salário** (achado 1) — a mais importante, e a que mais fortalece;
2. **A comparabilidade do controle** (achado 4) — transforma a falha de pretrend de admissão em
   explicação;
3. **As duas limitações da medida** (achados 2 e 3) — declaradas com número, na seção de limitações.

Três coisas viram robustez reportada: o jackknife, a queda das três maiores, e a inclusão de
`Minimal Exposure`.

E as quatro respostas do Bloco F entram na Seção 4, onde a estratégia empírica é apresentada.

---

## Verificação

- Família A permanece **byte-idêntica** ao commit.
- Os scripts vivem em `Replication Package/V2/code/audit/` e escrevem apenas em `results/audit/`.
  Nenhum artefato existente foi alterado.
- Toda evidência está copiada em `evidencia/`, com o comando que a reproduz ao lado de cada bloco.
