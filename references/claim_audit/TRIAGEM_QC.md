# Triagem da fila de QC cego

**Data:** 3 de agosto de 2026
**Base:** 227 resultados primários, 42 revisões cegas concluídas, 129 pendentes.
**Motivo:** a fila restante custa ~15h de revisor serial a 7 min/linha. Metade dela não responde a pergunta que o revisor cego sabe responder.

> Este documento não altera nenhum arquivo do run em execução. `queue.tsv`, `results/`, `qc_log.jsonl` e
> `run_manifest.json` continuam sob controle do processo do Codex, que escreveu pela última vez às 21:04:57Z.

---

## Correção da recomendação anterior

Eu havia dito que as 62 linhas "só-versão" podiam sair da fila semântica como tarefa mecânica de bibliografia.
**Isso vale para 16 delas, não para 62.** A separação correta é por tipo de obra:

| | Linhas | Por que |
|---|---:|---|
| **A — metodológicas** (Goodman-Bacon, Callaway–Sant'Anna, Sun–Abraham, de Chaisemartin–D'Haultfœuille, Santos Silva–Tenreyro, Chen–Roth) | 16 | o PDF em disco é o preprint, o `.bib` cita o publicado. O conteúdo metodológico não muda entre versões. Higiene de bibliografia. |
| **B — empíricas** (Brynjolfsson 30, Klein-Teeselink 11, Humlum 5) | 46 | **os números mudam entre revisões.** Reauditar contra o PDF errado é trabalho perdido em qualquer direção. |

O caso B não é hipotético. A ROW-0123 já mostra o mecanismo concreto: a dissertação cita "queda relativa de cerca de
16%" atribuída à **versão de 13 de novembro de 2025**; o PDF em disco é o manuscrito de **26 de agosto de 2025**, que
registra 13% no resumo e 12 pontos logarítmicos na especificação Poisson com efeitos fixos firma-tempo e firma-quintil.
Não dá para saber se 16% está errado ou se está na versão que não temos.

---

## Fila reordenada

| Balde | Linhas | Ação | Custo |
|---|---:|---|---|
| 1. Erro factual duro | **12** | revisor cego, esforço máximo, agora | ~1,5h |
| 2. Versão de PDF, obra empírica | **46** | **bloqueado** — baixar a versão citada antes de qualquer releitura | 1 tarefa de aquisição |
| 3. Versão de PDF, obra metodológica | **16** | sai da fila semântica; vira nota de bibliografia | ~0 |
| 4. Calibração pura | **55** | não precisa de terceiro leitor; precisa da régua (`REGUA_CALIBRACAO.md`) | 1 decisão sua |

De ~15h de revisor para ~1,5h, uma aquisição e uma decisão.

---

## Balde 1 — as 12 linhas que podem mudar o texto

Ordenadas por risco. Todas ainda não passaram pelo teste cego.

| Linha | Veredito primário | Obra | Onde | Código |
|---|---|---|---|---|
| ROW-0186 | OVERSTATED | brynjolfsson_canaries_2025 | 5.1 §13 | CAUSAL_OVERCLAIM |
| ROW-0187 | OVERSTATED | brynjolfsson_canaries_2025 | 5.1 §13 | CAUSAL_OVERCLAIM |
| ROW-0123 | OVERSTATED | brynjolfsson_canaries_2025 | 4.1 §1 | WRONG_MAGNITUDE |
| ROW-0178 | PARTIALLY_SUPPORTED | teutloff_winners_2025 | 4.5 §3 | WRONG_PERIOD |
| ROW-0170 | PARTIALLY_SUPPORTED | brynjolfsson_canaries_2025 | 4.3 §18 | MISATTRIBUTED_METHOD |
| ROW-0147 | PARTIALLY_SUPPORTED | callaway_difference_2021 | 4.1 §6 | MISATTRIBUTED_METHOD |
| ROW-0110 | PARTIALLY_SUPPORTED | brynjolfsson_canaries_2025 | 4.1 §1 | MISATTRIBUTED_METHOD |
| ROW-0125 | PARTIALLY_SUPPORTED | brynjolfsson_canaries_2025 | 4.1 §5 | MISATTRIBUTED_METHOD |
| ROW-0074 | OVERSTATED | eloundou_gpts_2023 | 2.3 §6 | MISATTRIBUTED_METHOD |
| ROW-0075 | OVERSTATED | eloundou_gpts_2023 | 2.3 §6 | MISATTRIBUTED_METHOD |
| ROW-0083 | OVERSTATED | benitez_mirror_2024 | 2.3 §6 | MISATTRIBUTED_METHOD |
| ROW-0077 | PARTIALLY_SUPPORTED | eloundou_gpts_2023 | 2.3 §6 | MISSING_EVIDENCE |

**Observação que revisa o diagnóstico geral.** O padrão de brandura do revisor cego (9 de 13 mudanças de veredito para
o lado mais leniente) concentra-se nos códigos de calibração. Nos códigos duros, o auditor primário parece **acurado**,
não severo — conferi ROW-0186, ROW-0187 e ROW-0123 contra o resumo de evidência e a fonte, e os três se sustentam.
É mais uma razão para o balde 1 vir primeiro: é onde a primeira rodada acerta e onde o erro custa caro.

---

## ⚠ Dependência com a Seção 6.4, escrita em 1º de agosto

ROW-0186 e ROW-0187 atacam esta frase da §5.1:

> "Brynjolfsson, Chandar e Chen (2025) […] enfrentam o mesmo problema de tendências paralelas: ocupações altamente
> expostas foram atingidas de forma distinta pela pandemia de Covid-19, o que contamina a linha de base anterior ao ChatGPT."

O que a fonte diz, segundo a auditoria:

- **p. 4** — a taxonomia de exposição **não** previu de modo relevante os resultados de emprego antes do uso difundido de
  LLMs, **inclusive durante o pico de desemprego da Covid-19**;
- **p. 24** — há uma preocupação **específica da medida de Eloundou et al. (2024)**: o quintil mais exposto crescia mais
  devagar desde cerca de 2020. Esse padrão **não** aparece nas medidas da Anthropic (Figuras A8–A9).

Ou seja: a dissertação generaliza uma observação específica de uma medida, e atribui à pandemia uma causalidade que a
fonte não estabelece — em tensão com o que a fonte afirma na p. 4.

**Por que isso me afeta.** Na §6.4 que escrevi, a hipótese da Covid termina com:

> "A hipótese não é minha: ela aparece na literatura internacional que examina o mesmo período."

Se o único apoio dessa frase for a passagem da §5.1, ela herda o erro e o amplifica, porque usa a atribuição para dar
autoridade externa à sua hipótese. **Não mexi na §6.4 ainda** — depende de ROW-0186/0187 passarem pelo teste cego.

Três saídas, na ordem em que eu as prefiro:

1. **Trocar a fonte.** Se existir artigo que estabeleça o efeito diferencial da Covid sobre ocupações expostas, a frase
   fica e a citação muda. É a saída que preserva o argumento.
2. **Rebaixar a frase** para "é uma hipótese levantada no debate sobre o período", sem atribuir a Brynjolfsson.
3. **Cortar a frase.** O argumento da §6.4 não depende dela — as três reduções quantitativas (corte para 2022, composição
   pré, decomposição educacional) sustentam a hipótese sozinhas. Ela só perde o reforço de autoridade.

---

## Balde 2 — versões (verificado em 04/08/2026 contra `library.bib` e `pdf_manifest.tsv`)

Conferi as quatro obras empíricas campo a campo. **Só uma precisa de download.** Nas outras três o PDF em disco é igual
ou mais recente do que o `.bib` declara — o defeito está na citação, não no arquivo.

| Obra | `.bib` declara | PDF em disco | Diagnóstico | Linhas |
|---|---|---|---|---:|
| `brynjolfsson_canaries_2025` | `date = 2025-11-13`, Stanford Digital Economy Lab | manuscrito de **26/08/2025** | **falta o PDF** — o `.bib` aponta uma versão que não temos | 52 |
| `klein_teeselink_generative_2025` | `date = 2025-09-22`, SSRN | SSRN, 46 pp., **21/12/2025** | PDF **mais novo** que o `.bib`; corrigir a data | 20 |
| `bick_rapid_2024` | `date = 2024`, FRB St. Louis WP **2024-027** | WP **2024-027F**, revisão de **27/10/2025** | PDF **mais novo**; o número citado só existe na revisão F | 4 |
| `humlum_still_2025` | `date = 2025-05`, **NBER WP 33777** | **BFI WP 2025-56**, atualização de set/2025 | **série diferente**; decidir qual citar | 5 |

**Brynjolfsson é o único download.** O `.bib` já declara `2025-11-13` e o arquivo é de agosto: baixar a revisão de 13 de
novembro alinha os dois, desbloqueia 30 linhas da fila e é pré-requisito de ROW-0123 (o "cerca de 16%" não existe no
manuscrito de agosto, que traz 13% no resumo e 12 pontos logarítmicos na especificação com efeitos fixos).

**Bick é o caso mais sutil e não se resolve baixando nada.** O texto cita "(Bick; Blandin; Deming, 2024)" e usa 32,1%,
mas o resumo da versão 2024-027 registra 27%; os 32,1% só aparecem na revisão F de outubro de 2025, que é a que está em
disco. A citação aponta para uma versão que diz outro número. Corrigir o `.bib` para a revisão F.

**Humlum exige uma escolha, não uma verificação.** O `.bib` cita NBER WP 33777 (maio/2025) e o disco tem BFI WP 2025-56
(setembro/2025). Alinhar o `.bib` ao arquivo é mais barato do que baixar o NBER, e o BFI é a versão mais recente.

---

## Balde 3 — nota de bibliografia (16 linhas, sem releitura)

Goodman-Bacon (5), Callaway–Sant'Anna (4), de Chaisemartin–D'Haultfœuille (3), Sun–Abraham (2), Santos Silva–Tenreyro (1),
Chen–Roth (1). Em todas, o `.bib` cita a versão publicada e o PDF consultado é o preprint. É a prática normal da área e
não afeta nenhuma afirmação. Basta uma linha declarando que os PDFs consultados são as versões de working paper, com a
data de cada uma.

---

## Balde 4 — 55 linhas de calibração

Ver `REGUA_CALIBRACAO.md`. São três decisões suas; elas reclassificam as 55 em lote, sem revisor.
