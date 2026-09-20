# Ledger de Avaliação — 143 Decisões Metodológicas

**Visão de triagem.** Uma linha por decisão. O argumento completo está nos arquivos de fase em `evaluations/`.
**Última atualização:** Fase 2 concluída (Blocos I, D)
**Progresso:** 25 / 143 avaliadas

## Estado por fase

| Fase | Bloco(s) | Decisões | Status |
| --- | --- | --- | --- |
| 1 | I — Identificação | 11 | ✅ concluída |
| 2 | D — Crosswalk e tratamento | 14 | ✅ concluída |
| 3 | C — Painel e janela | 14 | ⬜ pendente |
| 4 | F + E — Especificação e evento | 16 | ⬜ pendente |
| 5 | G + H — Heterogeneidade e multiplicidade | 18 | ⬜ pendente |
| 6 | A + B — Mensuração e PNADc | 19 | ⬜ pendente |
| 7 | J + K + L — Robustez, decomposição, casos | 20 | ⬜ pendente |
| 8 | M + N + O — Complementares, espacial, processo | 31 | ⬜ pendente |

## Contagem de vereditos (parcial)

| Veredito | n | % do avaliado |
| --- | --- | --- |
| `sólida` | 13 | 52% |
| `sólida, subdocumentada` | 8 | 32% |
| `frágil, reportada` | 1 | 4% |
| `frágil, não reportada` | 3 | 12% |
| `insustentável` | 0 | 0% |
| `pendente` | 0 | 0% |

**Padrão que já se firmou em 25 decisões:** nenhuma decisão de desenho precisou ser revertida. Das 12 ações abertas, **11 consistem em publicar número que já existe no pacote de replicação**. O gargalo é reporte, não método — e em quatro casos (I8, D8, D10, D7) a publicação do número torna o trabalho mais forte.

## Correção da distribuição de tier

A tabela da Seção 5 de `metodology-audit-plan.md` registra 51 / 77 / 15 e atribui 7 decisões T1 ao Bloco D. A contagem correta, conferida contra a lista nominal de slugs do próprio plano, é **52 / 76 / 15**, com **8** T1 no Bloco D — `gradiente-4-vazio` foi demovido a T2 no texto do plano, mas a soma da coluna não foi refeita. Este ledger usa 52 / 76 / 15.

---

## Ledger

Legenda de tier: **1** análise completa · **2** análise média · **3** veredito curto.
Legenda de prioridade: **A** alta · **M** média · **B** baixa · **—** sem ação.

| ID | Slug | T | Veredito | Ação | Pr. |
| --- | --- | --- | --- | --- | --- |
| **I1** | `suporte-antes-de-coeficientes` | 2 | sólida | nenhuma | — |
| **I2** | `classificacao-pretendencias` | 1 | sólida, subdocumentada | declarar que a regra é conjuntiva e por isso conservadora; nomear que o Wald conjunto rejeita sozinho | M |
| **I3** | `pretendencia-modelo-exato` | 2 | sólida | opcional: frase em §A.1 registrando o uso do modelo exato | B |
| **I4** | `diagnostico-rank-psd` | 1 | sólida | opcional: número de condição na Tabela A.1 | B |
| **I5** | `rank-deficiente-visivel` | 2 | sólida | nenhuma | — |
| **I6** | `identificacao-nao-alcancada` | 1 | **sólida** | nenhuma — apresentar como escolha deliberada | — |
| **I7** | `resultados-exploratorios-declarados` | 2 | sólida, subdocumentada | corrigir "único diagnóstico que não falha" na §5.2.3: há 2 `pass` por família | M |
| **I8** | `honestdid-rambachan-roth` | 1 | **frágil, não reportada** | publicar o resultado (quadro no Apêndice A + frase em §5.1 + justificar cobertura de 2/5 desfechos) | **A** |
| **I9** | `honestdid-nativo-em-r` | 3 | sólida | nenhuma | — |
| **I10** | `diferenca-com-canaries` | 2 | sólida | nenhuma | — |
| **I11** | `confusao-escritorio-vs-ia` | 1 | **frágil, reportada** | promover `d1_pre_period_comparability` a tabela de balanceamento no Apêndice A; citar 19,7% vs 4,0% em §6.3 | **A** |
| **D1** | `ponte-institucional-cbo-isco` | 1 | sólida, subdocumentada | distinguir validação de implementação vs. acurácia semântica; invocar atenuação por erro de medida | M |
| **D2** | `sem-correspondencia-adhoc` | 2 | sólida | nenhuma | — |
| **D3** | `no-score-excluido` | 1 | sólida, subdocumentada | reconciliar 629/630 e 193/194 entre Tabelas 4.2.2 e 4.2.3; justificar exclusão no CAGED vs. imputação na PNAD | M |
| **D4** | `seletividade-do-no-score` | 1 | sólida, subdocumentada | publicar `c2_unscored_profile` completo: a perda é **bilateral** (grupo 1 a 7,0×, grupo 9 a 2,5×) | M |
| **D5** | `agregacao-muitos-para-muitos` | 1 | sólida, subdocumentada | reportar 2,89 vs 1,65 destinos ISCO (tratado vs controle) e cobertura de 78,9% | M |
| **D6** | `tratamento-gradientes-1-4` | 1 | sólida | nenhuma | — |
| **D7** | `gradiente-4-vazio` | 2 | **frágil, não reportada** | corrigir "consequência do crosswalk" → consequência da agregação por média; V-D recupera 3 famílias em G4 | M-A |
| **D8** | `exposicao-binaria` | 1 | sólida, subdocumentada | **corrigir a comparação da §6.5**: −0,0188 é por DP e em amostra de 436; reescalado ≈ −0,043 vs −0,0456 → consistente, não fraco | **A** |
| **D9** | `controle-estrito-not-exposed` | 1 | sólida | nenhuma (ação em D10) | — |
| **D10** | `minimal-como-sensibilidade` | 1 | **frágil, não reportada** | publicar os 5 desfechos: fluxo bruto também cruza 5% (p=0,030) e desligamentos ficam em 0,056 | **A** |
| **D11** | `tratamento-congelado` | 2 | sólida | nenhuma | — |
| **D12** | `variantes-de-tratamento` | 2 | sólida, subdocumentada | reportar a composição resultante de V-D (tratadas 75→67), não só famílias alteradas | M |
| **D13** | `auditoria-cbo-4121` | 2 | sólida | nenhuma | — |
| **D14** | `sobreposicao-de-pontuacao` | 2 | sólida | opcional: nomear a não monotonicidade em §4.2 | B |
| **C1** | `caged-como-fonte-principal` | 1 | — | fase 3 | |
| **C2** | `sem-medida-de-adocao` | 1 | — | fase 3 | |
| **C3** | `unidade-cbo4-mes` | 2 | — | fase 3 | |
| **C4** | `identidade-mov-for-exc` | 2 | — | fase 3 | |
| **C5** | `mes-de-competencia` | 2 | — | fase 3 | |
| **C6** | `reconciliacao-pdet` | 2 | — | fase 3 | |
| **C7** | `filtros-registro-caged` | 2 | — | fase 3 | |
| **C8** | `ausente-nao-zero` | 2 | — | fase 3 | |
| **C9** | `winsorizacao-p1-p99` | 1 | — | fase 3 | |
| **C10** | `deflacionamento-ipca` | 2 | — | fase 3 | |
| **C11** | `janela-2021-2026` | 1 | — | fase 3 | |
| **C12** | `janela-assimetrica` | 2 | — | fase 3 | |
| **C13** | `cauda-incompleta-retida` | 2 | — | fase 3 | |
| **C14** | `determinismo-do-painel` | 3 | — | fase 3 | |
| **F1** | `ppml-para-contagens` | 1 | — | fase 4 | |
| **F2** | `ols-log-salario` | 2 | — | fase 4 | |
| **F3** | `asinh-saldo` | 1 | — | fase 4 | |
| **F4** | `log1p-secundario` | 2 | — | fase 4 | |
| **F5** | `efeitos-fixos-cbo4-mes` | 2 | — | fase 4 | |
| **F6** | `cluster-cbo4` | 1 | — | fase 4 · hipótese de lacuna 2 | |
| **F7** | `inferencia-cluster-t` | 1 | — | fase 4 | |
| **F8** | `sem-controles-contemporaneos` | 1 | — | fase 4 | |
| **F9** | `nivel-2-co-principal` | 1 | — | fase 4 | |
| **F10** | `dois-estimandos-distintos` | 1 | — | fase 4 | |
| **F11** | `sem-estrelas-nacional` | 2 | — | fase 4 | |
| **F12** | `sem-limiar-de-relevancia` | 2 | — | fase 4 | |
| **E1** | `evento-chatgpt-nov-2022` | 1 | — | fase 4 | |
| **E2** | `data-unica-sem-staggered` | 1 | — | fase 4 | |
| **E3** | `evento-difuso` | 2 | — | fase 4 | |
| **E4** | `janela-event-study` | 2 | — | fase 4 | |
| **G1** | `ddd-versus-did-no-grupo` | 1 | — | fase 5 | |
| **G2** | `did-no-corpo-ddd-no-apendice` | 2 | — | fase 5 | |
| **G3** | `cinco-eixos-heterogeneidade` | 2 | — | fase 5 | |
| **G4** | `faixas-etarias-duplas` | 2 | — | fase 5 | |
| **G5** | `renda-mediana-pre-cbo` | 1 | — | fase 5 | |
| **G6** | `classificacao-de-suporte` | 1 | — | fase 5 | |
| **G7** | `mde-80-poder` | 2 | — | fase 5 | |
| **G8** | `ddd-espelhado-binario` | 2 | — | fase 5 | |
| **G9** | `nao-aditividade-racial` | 2 | — | fase 5 | |
| **G10** | `subgrupos-por-composicao` | 1 | — | fase 5 | |
| **H1** | `bh-por-familia` | 1 | — | fase 5 | |
| **H2** | `familias-a-f` | 1 | — | fase 5 | |
| **H3** | `separacao-familias-a-b` | 1 | — | fase 5 | |
| **H4** | `separacao-familia-c` | 2 | — | fase 5 | |
| **H5** | `estrelas-sobre-p-bh` | 2 | — | fase 5 | |
| **H6** | `familia-f-vazia` | 2 | — | fase 5 | |
| **H7** | `diagnosticos-sem-ajuste` | 1 | — | fase 5 · ver I7 | |
| **H8** | `sem-refusao-de-familias` | 3 | — | fase 5 | |
| **A1** | `exposicao-como-potencial` | 2 | — | fase 6 | |
| **A2** | `abordagem-por-tarefas` | 3 | — | fase 6 | |
| **A3** | `comparacao-indices` | 2 | — | fase 6 | |
| **A4** | `indice-oit-principal` | 1 | — | fase 6 | |
| **A5** | `preferir-isco-a-onet` | 2 | — | fase 6 | |
| **A6** | `regra-gradiente-mu-sigma` | 1 | — | fase 6 | |
| **A7** | `alta-exposicao-g3-g4` | 1 | — | fase 6 | |
| **A8** | `limites-do-indice` | 3 | — | fase 6 | |
| **A9** | `medidas-alternativas-exposicao` | 2 | — | fase 6 | |
| **B1** | `pnadc-3t2025-corte-unico` | 2 | — | fase 6 | |
| **B2** | `restricao-etaria-18-65` | 2 | — | fase 6 | |
| **B3** | `peso-v1028` | 3 | — | fase 6 | |
| **B4** | `filtros-amostra-pnadc` | 2 | — | fase 6 | |
| **B5** | `crosswalk-cod-isco-fallback` | 1 | — | fase 6 | |
| **B6** | `agregacao-racial-osorio` | 2 | — | fase 6 | |
| **B7** | `faixas-renda-sm` | 3 | — | fase 6 | |
| **B8** | `setores-cnae-domiciliar` | 3 | — | fase 6 | |
| **B9** | `exposicao-ocupacional-nao-setorial` | 3 | — | fase 6 | |
| **B10** | `pnadc-papel-descritivo` | 2 | — | fase 6 | |
| **J1** | `escada-de-especificacoes` | 1 | — | fase 7 | |
| **J2** | `placebo-temporal` | 1 | — | fase 7 | |
| **J3** | `placebo-de-grupo` | 2 | — | fase 7 | |
| **J4** | `jackknife-ocupacional` | 2 | — | fase 7 | |
| **J5** | `horizontes-longos` | 2 | — | fase 7 | |
| **J6** | `mecanismos-de-desligamento` | 2 | — | fase 7 | |
| **J7** | `proxy-fluxo-cumulativo` | 1 | — | fase 7 | |
| **J8** | `salario-hora-e-jornada` | 2 | — | fase 7 | |
| **J9** | `porte-do-estabelecimento` | 2 | — | fase 7 | |
| **J10** | `publico-privado-nao-executado` | 2 | — | fase 7 | |
| **J11** | `sensibilidade-winsorizacao` | 1 | — | fase 7 · hipótese de lacuna 1 | |
| **J12** | `auditoria-concentracao` | 1 | — | fase 7 · ver I11 | |
| **K1** | `decomposicao-salarial` | 1 | — | fase 7 | |
| **K2** | `decomposicao-nao-oaxaca` | 2 | — | fase 7 | |
| **K3** | `composicao-sem-atribuicao` | 2 | — | fase 7 | |
| **L1** | `casos-ocupacionais` | 2 | — | fase 7 | |
| **L2** | `selecao-independente-do-indice` | 2 | — | fase 7 | |
| **L3** | `casos-descritivos` | 2 | — | fase 7 | |
| **L4** | `desequilibrio-dos-casos` | 1 | — | fase 7 | |
| **L5** | `tipo-movimentacao-inviavel` | 2 | — | fase 7 | |
| **M1** | `complementares-sem-causalidade` | 2 | — | fase 8 | |
| **M2** | `rais-mesmo-tratamento` | 2 | — | fase 8 | |
| **M3** | `rais-janela-2019-2024` | 1 | — | fase 8 | |
| **M4** | `rais-estoque-31-12` | 2 | — | fase 8 | |
| **M5** | `sensibilidade-inexequivel` | 2 | — | fase 8 | |
| **M6** | `rotatividade-um-periodo` | 2 | — | fase 8 | |
| **M7** | `pnadc-exclui-2022t4` | 2 | — | fase 8 | |
| **M8** | `pnadc-regra-de-maioria` | 1 | — | fase 8 | |
| **M9** | `pnadc-pareamento-exato` | 2 | — | fase 8 | |
| **M10** | `pnadc-dois-bracos` | 2 | — | fase 8 | |
| **M11** | `sem-desenho-amostral-completo` | 1 | — | fase 8 · hipótese de lacuna 4 | |
| **M12** | `quebra-2020-diferencial` | 2 | — | fase 8 | |
| **M13** | `discordancia-declarada` | 1 | — | fase 8 | |
| **M14** | `estoque-afasta-substituicao` | 2 | — | fase 8 | |
| **N1** | `extensao-espacial-interrompida` | 2 | — | fase 8 | |
| **N2** | `emenda-de-suporte` | 1 | — | fase 8 | |
| **N3** | `conflito-da-emenda` | 2 | — | fase 8 | |
| **N4** | `piso-de-ufs-efetivas` | 1 | — | fase 8 | |
| **N5** | `criterio-de-continuidade-estreito` | 2 | — | fase 8 | |
| **N6** | `correcao-de-erros-espaciais` | 2 | — | fase 8 | |
| **N7** | `benchmark-incompativel` | 2 | — | fase 8 | |
| **O1** | `pre-registro-do-desenho` | 1 | — | fase 8 · hipótese de lacuna 3 | |
| **O2** | `regra-anti-garimpo` | 2 | — | fase 8 | |
| **O3** | `insumos-congelados` | 3 | — | fase 8 | |
| **O4** | `replicacao-independente-r` | 2 | — | fase 8 | |
| **O5** | `tolerancias-declaradas` | 3 | — | fase 8 | |
| **O6** | `sem-importacao-de-p` | 3 | — | fase 8 | |
| **O7** | `registro-de-artefatos` | 3 | — | fase 8 | |
| **O8** | `nove-gates-de-release` | 3 | — | fase 8 | |
| **O9** | `preservacao-v1` | 3 | — | fase 8 | |
| **O10** | `auditoria-referee2` | 2 | — | fase 8 | |

---

## Ações de prioridade alta acumuladas

**Todas aplicadas na V3 em 2026-08-08** (página Notion `33dcc8ca461082bda8880151f42ba19b`), verificadas por releitura da página.

| Origem | Ação | Status | Efeito na tese |
| --- | --- | --- | --- |
| **I8** | Resultado do HonestDiD publicado: **Tabela A.1b** no Apêndice A + parágrafo na §5.1. | ✅ aplicada | Reforça a conclusão de não identificação |
| **I11** | `d1_pre_period_comparability` promovida a **Tabela A.1c**; razão 19,7% vs 4,0% de ensino superior inserida na §6.3. | ✅ aplicada | Converte admissão retórica em evidência |
| **D8** | Comparação da medida contínua reescrita na §6.5: amostra de 436 vs 341 e unidade por desvio-padrão agora declaradas. | ✅ aplicada (ver nota V3) | **Fortalece o resultado central** |
| **D10** | Cinco desfechos sob controle ampliado publicados na §6.5, com a justificativa ex-ante ao lado. | ✅ aplicada | Neutraliza a acusação de escolha de especificação |
| **D7** | §4.2 corrigida: o Gradiente 4 vazio é consequência da agregação por média; V-D recupera 3 famílias. | ✅ aplicada | Torna a afirmação mais forte |
| **I7** | §5.2.3 corrigida: "único diagnóstico" → duas células `pass`, três alertas, cinco deficientes em rank. | ✅ aplicada | Remove contradição com o Apêndice A |
| **D4** | §4.2: perda de correspondência agora declarada como **bilateral** (topo a 7,0×, base a 2,5×). | ✅ aplicada | Direção do viés passa a indeterminada, não adversa |
| **D5** | §4.2: assimetria de destinos ISCO (2,89 vs 1,65) e argumento de atenuação inseridos. | ✅ aplicada | Coeficientes passam a limites inferiores |

**Nota sobre D8.** O texto publicado afirma que o contraste vale "bem mais de um desvio-padrão" e que o coeficiente reescalado fica "na mesma ordem de magnitude" do binário — formulação rigorosa com os dados disponíveis. O ponto pode ser afiado para estimativa pontual (≈ −0,043) depois de resolver **V3**.

## Itens de verificação abertos

| ID | Item | Fase |
| --- | --- | --- |
| **V1** | Confirmar qual artefato sustenta o "65,4%" das cinco maiores famílias na §6.3 — `b1_concentration.csv` registra 66,83% sobre base de período completo, e a base pré-tratamento é outra. Provável diferença de base, não erro. | 1 |
| **V2** | Verificar se a cobertura do HonestDiD em 2 dos 5 desfechos é restrição técnica ou escolha declarada. Muda a redação da ação de I8. | 1 |
| **V3** | Computar o desvio-padrão exato da pontuação nas 436 famílias do degrau 05, para publicar o reescalamento de D8 com número exato. Minha estimativa é 0,119; a conclusão é robusta em [0,10; 0,14]. | 2 |
| **V4** | Reconciliar 629/630 famílias e 193/194 sem pontuação entre as Tabelas 4.2.2 e 4.2.3. | 2 |
