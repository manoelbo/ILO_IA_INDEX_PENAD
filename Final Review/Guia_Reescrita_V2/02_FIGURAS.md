# Figuras a substituir

**Rodada 2 do guia.** Caminhos conferidos por comando em 28 de julho de 2026.

Raiz: `Replication Package/V2/results/figures/`. Todas a **300 dpi**.

**São 15 figuras: 13 substituem as existentes e 2 são novas.** As três do Apêndice B são
removidas do texto, por decisão do autor em 28/07.

---

## Três mudanças que valem para toda figura de event study

Antes da lista, o que muda em **todas** de uma vez:

**1. A janela vai a `+41`, não `+23`.** Passa a mostrar os 42 meses de pós, com a fronteira de +23
marcada. Klein Teeselink (2025, p. 11) usa 15 pré e 30 pós — janela assimétrica é prática corrente,
não precisa de defesa.

**2. Toda figura leva uma linha horizontal na média dos coeficientes pré.** Sem ela a figura
contradiz a tabela: o event study mede cada mês contra novembro de 2022, e a tabela mede o pós
contra a média do pré-período. No salário isso é a diferença entre **−0,0154 e −0,0507** — um
leitor que compare figura e tabela sem essa linha conclui que uma das duas está errada.

A distância vertical da linha tracejada até a trajetória pós é que lê como o DiD. A legenda de cada
figura já explica isso; mantenha.

**3. A referência é novembro de 2022**, marcada e rotulada. Humlum e Vestergaard (p. 12, nota 8)
registram que event studies centrados em novembro de 2022 viraram convenção na literatura, citando
cinco trabalhos. Não é escolha idiossincrática sua.

---

## Seção 5.1

| ID | Linha | Artefato novo |
|---|---:|---|
| **5.1** Event studies e trajetórias nacionais | 446 | `figure_5_1_national_event_studies.png` |

Quatro painéis, um por outcome, coerentes com os quatro da Tabela 5.1. O painel do salário é o que
mais muda visualmente: o pré-período fica visivelmente acima do pós, e a linha tracejada em +0,037
torna a queda legível como distância.

---

## Seção 5.2 — dez figuras

| ID | Linha | Artefato novo |
|---|---:|---|
| **5.2.1.1** Admissões por sexo | 488 | `figure_5_2_1_1_sex_admissions.png` |
| **5.2.1.2** Salário por sexo | 494 | `figure_5_2_1_2_sex_wage.png` |
| **5.2.2.1** Admissões por raça/cor | 534 | `figure_5_2_2_1_race_admissions.png` |
| **5.2.2.2** Salário por raça/cor | 540 | `figure_5_2_2_2_race_wage.png` |
| **5.2.3.1** Admissões por idade | 597 | `figure_5_2_3_1_age_admissions.png` |
| **5.2.3.2** Salário por idade | 603 | `figure_5_2_3_2_age_wage.png` |
| **5.2.4.1** Admissões por escolaridade | 651 | `figure_5_2_4_1_education_admissions.png` |
| **5.2.4.2** Salário por escolaridade | 657 | `figure_5_2_4_2_education_wage.png` |
| **5.2.5.1** Admissões por renda | 700 | `figure_5_2_5_1_income_admissions.png` |
| **5.2.5.2** Salário por renda | 710 | `figure_5_2_5_2_income_wage.png` |

**Partições usadas:** as figuras acompanham as tabelas principais, então usam `Branca`/`Negra` para
raça e as faixas **PNAD/IBGE** para idade. As seis categorias raciais e as coortes Canaries ficam
só em tabela, no Apêndice A.

**Decidido em 28/07: entra uma figura extra para a coorte 22–25.** É o único contraste da
dissertação inteira cujo pretrend sobrevive — p conjunto 0,585, coeficiente −0,0517, p = 1e-06 — e
hoje ele só aparece em tabela, porque as figuras usam as faixas PNAD e ele está nas coortes
Canaries. Ver a seção nova abaixo.

---

## Seção 5.2.6 — figura nova

| ID | Linha | Artefato novo |
|---|---:|---|
| **5.2.6** Forest plot de síntese | **nova**, subseção na linha 722 | `figure_5_2_6_group_outcome_forest.png` |

A subseção de síntese das heterogeneidades **não tem figura nenhuma**: o leitor sai de cinco
subseções com 100 números e nenhum fecho visual.

O forest plot mostra os 130 contrastes da Família C, facetado por outcome, com intervalos ajustados
por BH e marcação de suporte `limited` e `thin`. Ele torna a multiplicidade visível — o leitor vê
130 contrastes e 40 sobreviventes — e mostra de relance que o salário domina.

O dado que gera a figura sai em `table_5_2_6...` no mesmo diretório de tabelas, caso queira
reportar os valores.

---

## Seção 5.3 — duas figuras

| ID | Linha | Artefato novo |
|---|---:|---|
| **5.3.1** Trajetórias de admissões por caso e idade | 748 | `figure_5_3_1_occupation_cases_admissions_by_age.png` |
| **5.3.2** Trajetórias de salário por caso e idade | 756 | `figure_5_3_2_occupation_cases_wage_by_age.png` |

**Duas correções em relação à V1**, ambas já implementadas nos artefatos:

1. a base de normalização passa de **outubro para novembro de 2022**, alinhando com o resto do
   trabalho;
2. a medida-resumo deixa de ser "janeiro a junho de 2025" e passa a ser os **12 meses terminais**,
   junho de 2025 a maio de 2026 — o recorte antigo virou arbitrário com o vintage novo.

Estas figuras continuam **descritivas**: sem estrela, sem p-valor, sem linguagem causal. Os casos
não têm grupo de controle próprio. O texto da §5.3 já diz isso; mantenha.

---

## Figura 5.2.3.3 — nova, a coorte 22–25 no salário

| ID | Onde | Artefato |
|---|---|---|
| **5.2.3.3** | §5.2.3, depois da 5.2.3.2 | `figure_5_2_3_3_canaries_22_25_wage.png` — **a gerar** |

**Por que existe.** É o único contraste do trabalho cujo pretrend passa: teste conjunto p = 0,585,
DiD dentro do grupo −0,0517 com p = 1e-06. Alinha com o enquadramento de porta de entrada e com o
artigo de referência, e hoje está invisível.

**Precisa ser estimada.** O `group_event_study_coefficients.csv` cobre as 15 partições principais e
**não** inclui as coortes Canaries. É preciso rodar o event study de `age_22_25` no salário, na
janela `−23…+41`, com a mesma linha da média pré e a mesma fronteira de +23 das demais.

**Ressalva obrigatória na legenda:** é 1 entre 100 contrastes de diagnóstico, sem ajuste de
multiplicidade sobre a família de pretrends. A figura mostra o caso, não prova a exceção.

---

## Apêndice B — removido do texto

| ID | Situação |
|---|---|
| **B.1** Casos por sexo | **removido** |
| **B.2** Casos por raça/cor | **removido** |
| **B.3** Casos por escolaridade | **removido** |

Decisão do autor em 28/07: em vez de manter um apêndice prometido e não entregue, o texto deixa de
prometê-lo. Prometer e não entregar foi o achado nº 6 da auditoria da V1.

**O que precisa sair do texto:**

1. as duas remissões ao Apêndice B na §5.3, linhas 730 e 764;
2. a seção `## Apêndice B` inteira, com as três subseções B.1, B.2 e B.3 e os cinco links para
   tabelas externas.

O material continua existindo no repositório — `outputs/section5_3_occupation_cases/` — e pode ser
retomado numa versão futura. O que sai é a promessa, não o dado.

---

## Seção 3 — não tocar

As dez figuras da Seção 3 (3.1 a 3.10) descrevem a **PNAD Contínua**, não o CAGED. A V2 não mexeu
nessa base e você decidiu não atualizar para 2026 T1. Nenhuma delas muda.
