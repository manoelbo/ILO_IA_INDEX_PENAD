# Primary Claim Audit Report

> **PRIMARY / PROVISIONAL — NOT FINAL.** This report summarizes the completed primary judgments. Blind quality control is paused and the findings must not be represented as a final source audit.

## Executive summary

The primary audit contains **213 source–claim–occurrence rows**, representing **175 atomic claims** and **59 formal citation occurrences** across 22 works. A final Notion refetch found one changed cited paragraph: **211 primary rows remain exact reuses and 2 rows in CIT-CUR-002 are DEFERRED_DEEP_AUDIT**. No substantive recommendation from the older wording is proposed for that occurrence.

| Primary verdict | Rows |
| --- | --- |
| SUPPORTED | 164 |
| OVERSTATED | 14 |
| PARTIALLY_SUPPORTED | 32 |
| CONTRADICTED | 1 |
| NOT_VERIFIABLE | 2 |

There are **49 rows** that are not fully supported, affecting **45 claims** and **32 citation occurrences**. The primary files mark **22 claims** as potentially requiring another source. This flag is source-specific: where a grouped citation already contains an independently supporting work, the change queue prefers removing or repositioning the unsuitable source instead of adding a redundant reference.

Separately, **19 SUPPORTED rows** have a PDF/version mismatch. Their substantive judgment is retained provisionally, but pagination and canonical reference metadata cannot be finalized until the source artifacts are aligned.

## Frozen dissertation and source inputs

| Field | Value |
| --- | --- |
| Notion page | Dissertação de Mestrado V2 |
| Page ID | 325cc8ca-4610-82d7-94db-01323b295bb5 |
| Last edited | 2026-08-05T23:58:00.000Z |
| Current fetch | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/notion_changes/notion_current_fetch.md |
| Current raw SHA-256 | 86594a43166b05a1ae2050d94650785b3926f05f52e0ac6ccfb493bbd205e6ef |
| Audited snapshot | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_snapshot/notion_page.md |
| Audited raw SHA-256 | bee994ca7796c33e67ef5de91156fdb6b55c3d4b110b3161a9c7ad938bc818f6 |
| Canonical semantic SHA-256 | 7eac685f97e2c1310e9da1b20fd4bac82307f4f2ab9a4cd7bafc560c8a4a2b49 |
| Semantic comparison | CHANGED: CIT-CUR-002 plus three changes outside audited citation excerpts |
| Primary TSV SHA-256 | 5286b14d7a9f7b6a49bd6f65aeebfe9e994be14392b4e5102ce3afdaefc85052 |

The canonical comparison isolates the `<content>` body, removes only expiring image-query strings, and normalizes whitespace; it does not remove dissertation text, citation labels, stable URLs, tables, or equations. It identified four current-body edits: ‘consolidou-se’ changed to ‘se consolidou’ in CIT-CUR-002, and ‘concentra-se’ changed to ‘elas e concentra’ in an uncited descriptive paragraph. A third edit restated the significance sentence in the introductory empirical summary; it falls outside the source excerpt assigned to CIT-CUR-007 and does not change that citation claim. A fourth edit shortened the uncited paragraph that describes the dissertation structure. The apparent typing error is reported but not added to the citation changeset.

## Method and limitations

Each primary row was evaluated independently against an immutable source snapshot and a page-level evidence artifact. The primary taxonomy is SUPPORTED, PARTIALLY_SUPPORTED, OVERSTATED, CONTRADICTED, NOT_FOUND, and NOT_VERIFIABLE. Page numbers below are printed pages; PDF indices remain available in the TSV and evidence files.

This report distinguishes: (1) substantive claim problems, (2) bibliographic/source-version problems, and (3) editorial or ABNT/link improvements. A primary judgment can be substantively SUPPORTED while still requiring source-version alignment. The paused blind QC may later confirm or revise individual judgments.

## Counts by section

| Value | Count |
| --- | --- |
| 2.3 Índices de exposição à IA na literatura | 67 |
| 4.1 Abordagem de diferenças em diferenças | 37 |
| 1 Introdução | 27 |
| 5.1 Resultados médios nacionais | 20 |
| 5.2.3 Resultados por faixa etária | 7 |
| 2.2 Fundamentos conceituais: tarefas, automação e complementaridade | 6 |
| 4.3 Especificação econométrica e desfechos | 6 |
| 4.4 Heterogeneidades e estudos de caso | 5 |
| Apêndice C — Casos ocupacionais e trajetórias por idade | 5 |
| 4.5 Testes de robustez e diagnósticos | 4 |
| 5.2.4 Resultados por nível de escolaridade | 4 |
| 5.2.5 Resultados por faixa salarial ocupacional | 4 |
| 6.3 Interpretação | 4 |
| 2.4 Escolha do índice da OIT e adaptação às bases brasileiras | 3 |
| 3.1 Base analítica e amostra | 3 |
| 4.2 Construção do painel ocupação-mês com CAGED e correspondência CBO → OIT | 3 |
| 5.2.1 Resultados por sexo | 3 |
| 5.2.2 Resultados por raça/cor | 3 |
| 3.5.2 Análise por raça | 1 |
| 3.5.3 Análise por faixa etária | 1 |

## Counts by work

| Value | Count |
| --- | --- |
| brynjolfsson_canaries_2025 | 51 |
| gmyrek_generative_2025 | 33 |
| eloundou_gpts_2023 | 20 |
| klein_teeselink_generative_2025 | 18 |
| benitez_mirror_2024 | 16 |
| hosseini_maasoum_generative_2025 | 11 |
| appel_anthropic_2026 | 11 |
| humlum_still_2025 | 6 |
| goodman_bacon_difference_2021 | 6 |
| callaway_difference_2021 | 6 |
| sun_estimating_2021 | 6 |
| de_chaisemartin_two-way_2020 | 6 |
| bick_rapid_2024 | 4 |
| autor_skill_2003 | 3 |
| agarwal_combining_2023 | 3 |
| chandar_tracking_2025 | 3 |
| santos_silva_log_2006 | 2 |
| chen_logs_2024 | 2 |
| teutloff_winners_2025 | 2 |
| rambachan_more_2023 | 2 |
| brasil_decreto_12342_2024 | 1 |
| osorio_o_2003 | 1 |

## Counts by claim type

| Value | Count |
| --- | --- |
| DIRECT | 126 |
| AUTHOR_INFERENCE | 87 |

## Problem codes

| Value | Count |
| --- | --- |
| PDF_VERSION_MISMATCH | 31 |
| PARTIAL_SCOPE | 14 |
| GENERALIZATION_OVERCLAIM | 8 |
| MISATTRIBUTED_METHOD | 6 |
| MISSING_EVIDENCE | 5 |
| WRONG_POPULATION | 4 |
| AUTHOR_INFERENCE_UNSUPPORTED | 3 |
| CAUSAL_OVERCLAIM | 1 |
| WRONG_MAGNITUDE | 1 |

## Affected claims

### CLM-CUR-005 — 1 Introdução, paragraph 2

**Claim (PT-BR):** A metodologia de construção de índices de exposição baseados em tarefas consolidou-se a partir do GPT Exposure.

**Current reconciliation:** `DEFERRED_DEEP_AUDIT`. The evidence below belongs to the prior wording and must not be used to apply a substantive edit before re-audit.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| eloundou_gpts_2023 | OVERSTATED | GENERALIZATION_OVERCLAIM | N/A — o PDF não exibe numeração impressa; evidência nas páginas físicas 5–8 | Nas páginas físicas 5–8, o artigo situa sua proposta entre métodos anteriores de exposição e automação baseados em tarefas, declara uma abordagem nova que usa o GPT-4 para avaliar tarefas, define uma rubrica de exposição e agrega os rótulos em três medidas ocupacionais (α, β e ζ). Essas páginas não documentam adoção posterior nem consolidação da metodologia na literatura. (evidence_pages/ROW-CUR-0005.pdf) | Substituir por: ‘Eloundou et al. (2023) propõem uma rubrica de exposição baseada em tarefas e demonstram o uso do GPT-4 para classificá-las e agregar as avaliações em medidas ocupacionais de exposição.’ Para manter ‘consolidou-se’, acrescentar fontes posteriores que demonstrem adoção recorrente da abordagem. | true |

### CLM-CUR-007 — 1 Introdução, paragraph 2

**Claim (PT-BR):** Estudos recentes nos Estados Unidos e no Reino Unido convergem para a conclusão de que o impacto da IA está se manifestando principalmente pela porta de entrada do mercado de trabalho.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | OVERSTATED | CAUSAL_OVERCLAIM | 3-7 | O artigo documenta queda relativa do emprego de trabalhadores de 22 a 25 anos em ocupações mais expostas à IA, em contraste com grupos mais experientes, e informa que estudos posteriores encontraram de modo semelhante quedas no emprego de entrada exposto à IA em dados dos Estados Unidos e do Reino Unido. Contudo, atribuição causal à IA e redução prioritária dos fluxos de trabalhadores juniores são apresentadas como hipóteses ou explicações possíveis ainda a testar. (evidence_pages/ROW-CUR-0007.pdf) | Estudos recentes nos Estados Unidos e no Reino Unido apresentam evidências convergentes de quedas relativas no emprego de trabalhadores em início de carreira em ocupações expostas à IA, padrão consistente, mas não causalmente conclusivo, com efeitos iniciais concentrados na entrada do mercado de trabalho. | false |
| hosseini_maasoum_generative_2025 | SUPPORTED | None | 3, 5, 41-42, 44 | Na p. 3, os autores sintetizam a evidência emergente de mercado de trabalho — incluindo seus próprios resultados e Klein Teeselink (2025) — como associando adoção ou exposição à GenAI a quedas do emprego júnior; a referência da p. 44 identifica Klein Teeselink como evidência do Reino Unido. Nos próprios dados de empresas dos EUA, a p. 5 mostra queda relativa de cerca de 9% no emprego júnior e de cerca de 7% em ocupações altamente expostas. A p. 41 resume que a contração se concentra nessas ocupações e decorre sobretudo de contratação mais lenta, e a p. 42 descreve deslocamento da demanda para longe das tarefas de entrada e estreitamento dos degraus inferiores das carreiras. (evidence_pages/ROW-CUR-0008.pdf) | Manter a afirmação e o conjunto de citações; a formulação é compatível com a síntese bibliográfica e com os resultados apresentados pela fonte. | false |
| klein_teeselink_generative_2025 | SUPPORTED | None | 4, 27-28 | Na introdução, o artigo situa seus resultados do Reino Unido junto a estudos dos Estados Unidos que documentam quedas de emprego concentradas em posições de início de carreira e afirma que, no Reino Unido, a contratação reage mais rápida e fortemente que os estoques de emprego. Na conclusão, a redução britânica de emprego é descrita como predominantemente concentrada em posições juniores, e as perdas em posições de entrada atingem novos entrantes. (evidence_pages/ROW-CUR-0009.pdf) | Manter a afirmação e esta citação como estão. | false |

### CLM-CUR-008 — 1 Introdução, paragraph 2

**Claim (PT-BR):** Posições de entrada em ocupações expostas à IA enfrentam menor oferta de trabalho.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | SUPPORTED | None | 3–4 | Na p. 3, os autores relatam quedas substanciais no emprego de trabalhadores em início de carreira, definidos como pessoas de 22 a 25 anos, nas ocupações mais expostas à IA. Informam ainda queda de 6% entre o fim de 2022 e setembro de 2025 nesse grupo e descrevem redução do emprego de entrada nas aplicações de IA que automatizam o trabalho. Na p. 4, registram queda relativa de 15 pontos log nos quintis mais expostos após controles por efeitos firma-tempo. O recorte e a direção sustentam diretamente a afirmação auditada. (evidence_pages/ROW-CUR-0010.pdf) | Manter a afirmação. Como refinamento opcional, explicitar que o resultado se refere ao emprego de trabalhadores de 22 a 25 anos nas ocupações mais expostas à IA. | false |
| hosseini_maasoum_generative_2025 | SUPPORTED | None | 5-7 | Nas firmas adotantes, o emprego júnior em ocupações de alta exposição à GenAI cai cerca de 7% em relação ao emprego júnior em ocupações de baixa exposição ao longo dos dois anos seguintes. O artigo também mostra queda acentuada das vagas anunciadas e atribui a redução do emprego júnior principalmente à menor contratação, caracterizando-a como demanda por trabalho mais fraca, e não como restrição de oferta de trabalho. (evidence_pages/ROW-CUR-0011.pdf) | Manter. Para maior precisão econômica, pode-se escrever: “Em firmas adotantes dos Estados Unidos, o emprego júnior em ocupações mais expostas à IA generativa caiu relativamente, sobretudo por menor contratação, refletindo menor demanda por trabalho.” | false |
| klein_teeselink_generative_2025 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 15, 20 | No painel de empresas, um aumento de um desvio-padrão na exposição a LLMs está associado a redução de 0,4% no emprego júnior. Separadamente, no painel de ocupações, o mesmo aumento de exposição está associado a redução de 3,9% no volume de anúncios. O artigo não estima se a queda nas ocupações expostas se concentra especificamente em posições de entrada. (evidence_pages/ROW-CUR-0012.pdf) | No Reino Unido, empresas mais expostas a LLMs reduziram o emprego em cargos de baixa senioridade; em análise separada, ocupações mais expostas registraram menos anúncios de vagas. | false |

### CLM-CUR-009 — 1 Introdução, paragraph 2

**Claim (PT-BR):** Trabalhadores em início de carreira em ocupações expostas à IA enfrentam menor oferta de trabalho.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | SUPPORTED | None | 3 | Na amostra de folhas de pagamento da ADP nos Estados Unidos, o artigo relata queda substancial do emprego entre trabalhadores de 22–25 anos nas ocupações mais expostas à IA. Entre o fim de 2022 e setembro de 2025, o emprego desse grupo caiu 6%, enquanto aumentou 6%–9% entre trabalhadores mais velhos. (evidence_pages/ROW-CUR-0013.pdf) | Manter a afirmação como está. | false |
| hosseini_maasoum_generative_2025 | SUPPORTED | PDF_VERSION_MISMATCH | 1, 33 | Na amostra de firmas dos Estados Unidos, a contração pós-2022 do emprego júnior nas firmas adotantes concentra-se em ocupações de alta exposição à GenAI. Na página 33, os autores registram queda relativa de cerca de 7 pontos logarítmicos e interpretam o resultado como deslocamento da demanda para longe de trabalhadores juniores justamente nas ocupações em que a tecnologia é mais aplicável. (evidence_pages/ROW-CUR-0014.pdf) | Manter a afirmação; atualizar ou anotar a entrada bibliográfica para refletir que o PDF auditado é a versão de 6 de junho de 2026. | false |
| klein_teeselink_generative_2025 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 15, 20, 27-28 | Na p. 15, o artigo estima que um desvio-padrão adicional de exposição da firma a LLMs está associado a redução de 0,4% no emprego de baixa senioridade, enquanto a queda entre empregados seniores não é estatisticamente significativa. Na p. 20, em análise distinta, um desvio-padrão adicional de exposição da própria ocupação está associado a redução de 3,9% no volume de vagas. As pp. 27-28 recapitulam separadamente esses dois níveis de análise. A fonte, portanto, sustenta menor emprego de baixa senioridade em firmas expostas e menor demanda por vagas em ocupações expostas, mas não estima diretamente a interseção entre início de carreira e exposição da própria ocupação. (evidence_pages/ROW-CUR-0015.pdf) | No Reino Unido, após novembro de 2022, firmas mais expostas a LLMs apresentaram redução concentrada no emprego de baixa senioridade; separadamente, ocupações mais expostas registraram queda no volume de vagas. | false |

### CLM-CUR-010 — 1 Introdução, paragraph 2

**Claim (PT-BR):** O ajuste documentado por esses estudos concentra-se no emprego, e não na remuneração.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | SUPPORTED | None | 13 | Na seção 4.5, os autores comparam emprego à remuneração-base anual e observam menor divergência na remuneração do que no emprego, além de pouca diferença nas tendências de remuneração por idade ou quintil de exposição. O próprio título do Fact 5 formula diretamente que os ajustes do mercado de trabalho são mais visíveis no emprego do que na remuneração. (evidence_pages/ROW-CUR-0016.pdf) | Manter a afirmação. Opcionalmente, para máxima literalidade, usar ‘o ajuste é mais visível no emprego do que na remuneração-base anual’. | false |
| hosseini_maasoum_generative_2025 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 41-42, A.13-A.14 | A conclusão documenta queda do emprego júnior em relação ao emprego sênior nas firmas adotantes, concentrada em ocupações mais expostas e impulsionada principalmente por menor contratação. Porém, o apêndice informa que salários efetivos por posição não estão disponíveis; os salários preditos são usados apenas para interpretar heterogeneidade por formação educacional. Assim, o componente relativo ao emprego é sustentado, mas a oposição entre emprego e remuneração não é demonstrada. (evidence_pages/ROW-CUR-0017.pdf) | Hosseini Maasoum e Lichtinger documentam que, nas firmas adotantes, o emprego júnior caiu em relação ao emprego sênior, sobretudo pela desaceleração da contratação; o estudo não estima efeitos sobre salários. Para manter a oposição à remuneração, acrescente uma fonte que estime diretamente efeitos salariais. | true |
| klein_teeselink_generative_2025 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 20-21 | Na análise ocupacional, um desvio-padrão adicional de exposição a LLMs associa-se a uma redução de 3,9% nas vagas e também a uma queda de £495, ou 1,1%, nos salários anunciados. O texto caracteriza a pressão salarial como imediata e persistente e afirma haver depressão salarial ampla nas ocupações expostas, distinguindo-a do pequeno aumento composicional da remuneração média no nível da firma. (evidence_pages/ROW-CUR-0018.pdf) | No estudo do Reino Unido, o ajuste aparece tanto no emprego e nas vagas quanto na remuneração: ocupações mais expostas apresentam menos vagas e salários anunciados menores, enquanto a remuneração média intrafirma aumenta levemente por composição. | false |

### CLM-CUR-012 — 1 Introdução, paragraph 5

**Claim (PT-BR):** O ILO Global Index é o único entre os principais índices de exposição estruturado em torno da ISCO-08.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | OVERSTATED | GENERALIZATION_OVERCLAIM | 10-11, 46 | O artigo descreve seu índice como baseado na ISCO-08 e apresenta essa classificação como um denominador comum global, em contraste com o predomínio de estudos orientados ao contexto dos EUA e à O*NET. Contudo, não define nem compara exaustivamente os ‘principais índices’ e não declara que o ILO Global Index seja o único estruturado em torno da ISCO-08. (evidence_pages/ROW-CUR-0022.pdf) | O ILO Global Index é estruturado em torno da ISCO-08, que oferece um denominador comum para projeções entre países. Para manter a alegação de exclusividade, é necessária uma fonte comparativa abrangente que defina e examine os principais índices. | true |

### CLM-CUR-013 — 1 Introdução, paragraph 5

**Claim (PT-BR):** A ISCO-08 é a classificação internacional com maior compatibilidade com as taxonomias ocupacionais brasileiras.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | OVERSTATED | GENERALIZATION_OVERCLAIM | 12, 39, 46 | A fonte afirma que a classificação polonesa é compatível com a estrutura hierárquica da ISCO-08 (p. 12), reconhece que o índice global carece de nuance por país (p. 39) e caracteriza a ISCO-08 como denominador global comum, com mapeamentos de sistemas nacionais disponíveis (p. 46). Ela não menciona Brasil, CBO, COD, PNAD ou CAGED, não avalia a compatibilidade das taxonomias brasileiras e não compara classificações internacionais para demonstrar que a ISCO-08 tenha a maior compatibilidade. (evidence_pages/ROW-CUR-0023.pdf) | Com esta fonte, escrever: ‘A ISCO-08 oferece um denominador comum para comparações internacionais e dispõe de mapeamentos de sistemas ocupacionais nacionais.’ Para manter a afirmação de maior compatibilidade com COD e CBO, acrescentar uma fonte brasileira que documente esses mapeamentos e compare alternativas internacionais. | true |

### CLM-CUR-018 — 2.2 Fundamentos conceituais: tarefas, automação e complementaridade, paragraph 1

**Claim (PT-BR):** O trabalho de Autor, Levy e Murnane (2003) é seminal para a abordagem baseada em tarefas.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| autor_skill_2003 | PARTIALLY_SUPPORTED | MISSING_EVIDENCE | 1280-1282 | Nas páginas 1280-1282, o artigo declara que formaliza e testa uma teoria sobre como a informatização altera as tarefas realizadas nos empregos, afirma preencher um elo conceitual e empírico e apresenta um ‘task model’ que conceitua o trabalho como uma série de tarefas. Isso sustenta a associação do artigo à abordagem baseada em tarefas, mas a própria publicação não demonstra que o trabalho se tornou ‘seminal’, qualificativo referente à recepção e à influência posteriores. (evidence_pages/ROW-CUR-0028.pdf) | Se esta fonte permanecer sozinha, substituir por: ‘Autor, Levy e Murnane (2003) formalizam e testam um modelo baseado em tarefas para analisar como a informatização altera a composição das tarefas dos empregos.’ Para manter ‘seminal’, acrescentar uma fonte posterior de revisão ou história da literatura que documente sua influência. | true |

### CLM-CUR-021 — 2.2 Fundamentos conceituais: tarefas, automação e complementaridade, paragraph 2

**Claim (PT-BR):** Diagnósticos produzidos por IA foram iguais ou tão precisos quanto os de dois terços dos médicos dos Estados Unidos.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| agarwal_combining_2023 | OVERSTATED | WRONG_POPULATION | 14, 20 | Na p. 20, os autores afirmam que a IA é mais preditiva do que aproximadamente dois terços dos radiologistas, com base em AUROC e RMSE. A p. 14 esclarece que os 180 participantes incluíam radiologistas baseados e não baseados nos Estados Unidos e que somente cerca de 17% eram baseados no país. (evidence_pages/ROW-CUR-0031.pdf) | No experimento de Agarwal et al. (2023), as previsões da IA foram mais precisas do que as de aproximadamente dois terços dos 180 radiologistas participantes. | false |

### CLM-CUR-022 — 2.2 Fundamentos conceituais: tarefas, automação e complementaridade, paragraph 2

**Claim (PT-BR):** O diagnóstico é apenas uma das tarefas do radiologista, cuja profissão também envolve coordenação de equipe, comunicação com outros médicos e interação com pacientes.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| agarwal_combining_2023 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 2, 4, 10–11 | A fonte caracteriza a classificação de imagens como tarefa central do radiologista, descreve o diagnóstico a pedido do médico assistente, a troca formal de informações e o relato de achados, além de discutir automação parcial. Contudo, não menciona coordenação de equipe e afirma que radiologistas raramente têm contato direto com pacientes ou com o médico assistente. (evidence_pages/ROW-CUR-0032.pdf) | A classificação de imagens é uma tarefa central do radiologista, mas o fluxo diagnóstico também incorpora histórico clínico, solicitações do médico assistente, relato de achados e recomendações de acompanhamento; por isso, a IA tende a automatizar apenas parte desse fluxo. Para manter coordenação de equipe ou interação com pacientes, acrescente uma fonte específica sobre o escopo ocupacional da radiologia. | true |

### CLM-CUR-025 — 2.3 Índices de exposição à IA na literatura, paragraph 3

**Claim (PT-BR):** O GPT Exposure é apresentado como o trabalho de referência do campo de índices de exposição à IA.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| eloundou_gpts_2023 | OVERSTATED | GENERALIZATION_OVERCLAIM | N/A — documento sem folios impressos; evidência nas páginas físicas 2–3 | Nas páginas físicas 2–3, Eloundou et al. afirmam que propõem uma nova rubrica, seguindo trabalhos anteriores, e descrevem suas contribuições como medidas do impacto potencial de LLMs e como demonstração do uso de LLMs para produzi-las. O artigo não se caracteriza como “o trabalho de referência” do campo, e a busca integral por termos de status ou recepção não encontrou essa afirmação. (evidence_pages/ROW-CUR-0035.pdf) | Substituir por: “Eloundou et al. (2023) propõem uma nova rubrica para medir a exposição de tarefas a LLMs, aplicando-a com anotações humanas e classificações do GPT-4.” Se for indispensável manter a caracterização como trabalho de referência, acrescentar uma revisão independente ou evidência bibliométrica que a sustente. | true |

### CLM-CUR-027 — 2.3 Índices de exposição à IA na literatura, paragraph 3

**Claim (PT-BR):** O GPT Exposure foi o primeiro índice a usar a própria IA para avaliar tarefas.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| eloundou_gpts_2023 | PARTIALLY_SUPPORTED | AUTHOR_INFERENCE_UNSUPPORTED | N/A | Na página física 2, os autores propõem uma nova rubrica e afirmam empregar o próprio GPT-4 como classificador para aplicá-la aos dados ocupacionais. Na página física 6, qualificam como novo o método que emprega GPT-4 para avaliar exposição no nível das tarefas. Isso sustenta o uso da própria IA, mas a fonte não declara que este tenha sido o primeiro índice a fazê-lo. (evidence_pages/ROW-CUR-0037.pdf) | Sem uma fonte comparativa que demonstre a primazia, revise para: ‘O GPT Exposure empregou o próprio GPT-4 como classificador para aplicar uma nova rubrica a tarefas ocupacionais.’ | true |

### CLM-CUR-036 — 2.3 Índices de exposição à IA na literatura, paragraph 4

**Claim (PT-BR):** O GENOE fornece ao modelo o nome, o conjunto de tarefas e as implicações sociais da ocupação.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| benitez_mirror_2024 | PARTIALLY_SUPPORTED | MISATTRIBUTED_METHOD | 3, 14–15 | A fonte afirma diretamente que a especificação basal fornece ao modelo o nome da ocupação e seu vetor de tarefas. Ela também afirma que o modelo considera o contexto ético e social organicamente e, na seção de alternativas, esclarece que a inclusão explícita de repercussões éticas e resistência social pertence ao Ethical Emphasis Index, não aos dados ocupacionais fornecidos na especificação basal. Assim, nome e tarefas estão sustentados, mas ‘implicações sociais’ não constitui um terceiro insumo fornecido ao modelo. (evidence_pages/ROW-CUR-0046.pdf) | O GENOE fornece ao modelo o nome da ocupação e seu vetor de tarefas, permitindo que o LLM considere implicitamente o contexto ético e social da ocupação. | false |

### CLM-CUR-041 — 2.3 Índices de exposição à IA na literatura, paragraph 5

**Claim (PT-BR):** O Anthropic Economic Index substitui uma classificação binária por dimensões econômicas.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| appel_anthropic_2026 | CONTRADICTED | AUTHOR_INFERENCE_UNSUPPORTED | pp. 19–21 | O relatório confirma que esta edição acrescenta cinco primitivas econômicas à medida preexistente de padrões de colaboração (automação/augmentação), entre elas autonomia da IA e sucesso da tarefa. A fonte caracteriza as novas dimensões como uma expansão para além da distinção já medida, não como sua substituição. (evidence_pages/ROW-CUR-0051.pdf) | O Anthropic Economic Index amplia suas métricas de uso: além dos padrões de colaboração (automação/augmentação), acrescenta cinco primitivas econômicas, entre elas autonomia da IA e sucesso da tarefa. | false |

### CLM-CUR-045 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** O ILO Global Index é apresentado como o único índice estruturado na ISCO-08.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | OVERSTATED | GENERALIZATION_OVERCLAIM | 11, 37, 46 | A fonte afirma que trabalhar com tarefas da ISCO-08 oferece um denominador comum internacional, classifica ocupações ISCO-08 no índice ajustado e denomina o produto como um índice baseado na ISCO-08. A discussão comparativa diz apenas que a maioria dos estudos orientados por tarefas se concentra nos Estados Unidos e usa a O*NET; ela não afirma que o ILO Global Index seja o único índice estruturado na ISCO-08. (evidence_pages/ROW-CUR-0055.pdf) | O ILO Global Index é estruturado na ISCO-08. Para manter o qualificativo “único”, acrescente uma fonte comparativa que examine explicitamente o universo pertinente de índices. | true |

### CLM-CUR-046 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** A ISCO-08 é apresentada como a classificação ocupacional internacional da ONU.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | PARTIALLY_SUPPORTED | MISSING_EVIDENCE | 7; 9; contracapa sem numeração | A p. 7 expande ISCO-08 como ‘International Standard Classification of Occupations (2008 version)’. A p. 9 informa que um método desenvolvido pela OIT usou descrições de tarefas da ISCO-08. A contracapa afirma que a OIT é a agência das Nações Unidas para o mundo do trabalho. A fonte, porém, não declara que a ISCO-08 seja a classificação ‘da ONU’ nem explicita uma relação de pertencimento entre a classificação e a OIT. (evidence_pages/ROW-CUR-0056.pdf) | A ISCO-08 é a Classificação Internacional Uniforme de Ocupações, na versão de 2008. | false |

### CLM-CUR-047 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** A ISCO-08 usada no ILO Global Index é complementada por uma taxonomia polonesa de seis dígitos.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | PARTIALLY_SUPPORTED | MISATTRIBUTED_METHOD | 36-37 | Na p. 36, o relatório afirma que o sistema prevê escores para 3.265 tarefas da ISCO-08, gera separadamente previsões para 29.753 tarefas da classificação polonesa e compara as previsões de seis dígitos com classificações ISCO-08 de quatro dígitos. A mesma página informa que o restante do artigo se concentra nos escores ISCO-08 e reserva a análise detalhada das ocupações polonesas a outro estudo; na p. 37, o Índice Global Ajustado é explicitamente definido pela classificação de ocupações ISCO-08. Assim, ambas as classificações aparecem na metodologia, mas a fonte não apresenta a taxonomia polonesa como complemento estrutural da ISCO-08 no índice. (evidence_pages/ROW-CUR-0057.pdf) | O ILO Global Index é estruturado na ISCO-08. O estudo também gera e compara previsões para a classificação ocupacional polonesa de seis dígitos, cuja análise detalhada é deixada para um estudo separado. | false |

### CLM-CUR-062 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** A validação humana inicial é apresentada como uma vantagem do GPT Exposure.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| eloundou_gpts_2023 | PARTIALLY_SUPPORTED | MISATTRIBUTED_METHOD | N/A | A página física 8 documenta anotações humanas, a comparação de concordância entre humanos e GPT-4 e o ajuste do rubric apresentado ao modelo para elevar a concordância com rótulos humanos. A página física 9, porém, trata a subjetividade dos julgamentos humanos como limitação fundamental, afirma que validar os resultados exige trabalho futuro e esclarece que nenhuma fonte de anotação é verdade de referência definitiva. Há suporte para uma comparação humana inicial, mas não para afirmar que o artigo a apresenta como vantagem. (evidence_pages/ROW-CUR-0072.pdf) | O GPT Exposure combina anotações humanas e classificações do GPT-4, com ajuste do rubric do modelo para elevar a concordância com rótulos humanos; os autores, contudo, não tratam nenhuma fonte de anotação como verdade de referência definitiva e apontam limitações de validação. | false |

### CLM-CUR-063 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** O critério categórico e binário do GPT Exposure não gradua a exposição.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| eloundou_gpts_2023 | PARTIALLY_SUPPORTED | MISATTRIBUTED_METHOD | N/A — o PDF não exibe numeração impressa nas páginas relevantes | A seção 3.3 classifica tarefas em categorias discretas E0, E1 e E2, com E3 separado apenas na anotação, usando um limiar de 50% de redução do tempo. Isso sustenta a caracterização do critério por tarefa como categórico e baseado em limiar. Contudo, o método não é simplesmente binário nem deixa de graduar toda exposição: o artigo constrói α = E1, β = E1 + 0,5×E2 e ζ = E1 + E2, agregadas como proporções de tarefas no nível ocupacional. O que a rubrica não estima é a economia contínua de tempo dentro de cada categoria. (evidence_pages/ROW-CUR-0073.pdf) | O GPT Exposure aplica, no nível da tarefa, uma taxonomia discreta baseada no limiar de 50% de redução do tempo; ela não mede continuamente a economia de tempo dentro de cada categoria, mas gera medidas ocupacionais graduadas ao agregar E1 e E2, inclusive atribuindo peso 0,5 a E2 em β. | false |

### CLM-CUR-064 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** A taxonomia americana do GPT Exposure exige um crosswalk adicional para aplicação no Brasil.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| eloundou_gpts_2023 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | N/A | Na página física 6, o artigo afirma que sua análise cobre o mercado de trabalho contemporâneo dos EUA, usa a base O*NET 27.2 e combina dados do BLS com o O*NET por meio de um crosswalk recomendado pelo BLS. Isso sustenta a base ocupacional norte-americana, mas não a exigência específica de um crosswalk para aplicação no Brasil. (evidence_pages/ROW-CUR-0074.pdf) | Separar o dado documentado da inferência: 'O índice de Eloundou et al. (2023) usa O*NET 27.2 e dados do BLS para o mercado de trabalho dos EUA. Sua aplicação ao Brasil demandaria uma etapa própria de compatibilização ocupacional.' A segunda frase requer uma fonte adicional sobre a classificação brasileira e sua compatibilização com a base norte-americana. | true |

### CLM-CUR-067 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** O GENOE fornece ao modelo de linguagem o contexto completo da ocupação.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| benitez_mirror_2024 | OVERSTATED | PARTIAL_SCOPE | 3-5 | A fonte afirma que o GENOE fornece ao modelo o nome da ocupação e seu vetor integral de tarefas, o que permite uma avaliação holística e a consideração orgânica de contextos éticos e sociais. Contudo, o artigo também informa que o O*NET contém outros atributos ocupacionais e que a metodologia se concentra nas tarefas, em vez de habilidades ou aptidões; assim, não demonstra que todo o contexto ocupacional seja fornecido ao modelo. (evidence_pages/ROW-CUR-0077.pdf) | O GENOE fornece ao modelo o nome da ocupação e seu vetor completo de tarefas, possibilitando uma avaliação holística. | false |

### CLM-CUR-079 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** O Anthropic Economic Index apresenta viés de amostragem por observar apenas usuários de modelos específicos.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| appel_anthropic_2026 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 2, 22 | Na p. 2, o relatório delimita os dados a interações com Claude em novembro de 2025, obtidas de transcrições anonimizadas do Claude.ai e da API própria. Na p. 22, a ressalva explícita de representatividade refere-se aos conjuntos usados para validar classificadores, não à amostra principal de uso. A fonte sustenta, portanto, a restrição de escopo, mas não afirma nem demonstra o ‘viés de amostragem’ atribuído. (evidence_pages/ROW-CUR-0089.pdf) | O Anthropic Economic Index analisa um universo restrito de interações com Claude, com base em transcrições anonimizadas do Claude.ai e da API própria. | false |

### CLM-CUR-080 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** A base do Anthropic Economic Index é americana.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| appel_anthropic_2026 | OVERSTATED | GENERALIZATION_OVERCLAIM | 2, 21, 24, 36 | A p. 21 mostra que a análise de tarefas é ancorada no O*NET, e a p. 24 valida a medida educacional com dados do BLS e microdados da American Community Survey de 2022–2023. Porém, as pp. 2 e 36 deixam claro que a base de uso inclui conversas do Claude.ai e recortes por país e por estados dos EUA, inclusive localizações internacionais. Assim, apenas parte da estrutura e da validação é americana, não a base do índice de modo geral. (evidence_pages/ROW-CUR-0090.pdf) | O Anthropic Economic Index ancora parte da análise ocupacional no O*NET e valida a medida de escolaridade com dados BLS/ACS dos EUA, mas sua base de uso inclui conversas globais do Claude.ai. | false |

### CLM-CUR-089 — 2.3 Índices de exposição à IA na literatura, paragraph 6

**Claim (PT-BR):** Aplicar o ILO Global Index ao Brasil exige um crosswalk com COD e CBO.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 39, 46 | Nas páginas 39 e 46, os autores descrevem o índice como genérico e baseado na ISCO-08, reconhecem a ausência de parte da nuance nacional e afirmam que existem mapeamentos dos sistemas nacionais para esse padrão internacional. A fonte não menciona o Brasil, COD ou CBO, nem estabelece que a aplicação brasileira exija um crosswalk envolvendo ambas as classificações; ela também apresenta um preditor para tarefas de classificações nacionais. (evidence_pages/ROW-CUR-0099.pdf) | Reescrever como: ‘O ILO Global Index usa a ISCO-08 como denominador comum e informa que existem mapeamentos dos sistemas ocupacionais nacionais para esse padrão.’ Para manter a menção ao Brasil, COD e CBO, adicionar uma fonte brasileira que documente o crosswalk e justifique a necessidade das duas classificações. | true |

### CLM-CUR-092 — 2.4 Escolha do índice da OIT e adaptação às bases brasileiras, paragraph 1

**Claim (PT-BR):** A escolha do ILO Global Index apoia-se em sua compatibilidade com as classificações ocupacionais brasileiras.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | PARTIALLY_SUPPORTED | MISSING_EVIDENCE | 9, 46 | A introdução mostra que uma classificação nacional alinhada à ISCO-08 permite compilar escores comparáveis e preservar um vínculo hierárquico para uso internacional. A conclusão caracteriza o índice como denominador global e afirma que existem mapeamentos dos sistemas nacionais para a ISCO-08. Contudo, o artigo não identifica nem demonstra um mapeamento específico das classificações ocupacionais brasileiras; a única ocorrência de ‘Brazil’ está nos agradecimentos, em uma afiliação institucional. (evidence_pages/ROW-CUR-0102.pdf) | A escolha apoia-se na arquitetura ISCO-08 do índice, que permite mapeamentos com sistemas ocupacionais nacionais; para afirmar compatibilidade específica com as classificações brasileiras utilizadas, acrescentar uma fonte que documente sua correspondência com a ISCO-08. | true |

### CLM-CUR-094 — 3.1 Base analítica e amostra, paragraph 1

**Claim (PT-BR):** A base analítica combina os microdados da PNAD Contínua do terceiro trimestre de 2025 com o ILO Global Index.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | PARTIALLY_SUPPORTED | MISSING_EVIDENCE | 43, 46 | A p. 43 mostra que o estudo combina os escores de exposição com a coleção harmonizada de microdados da OIT para produzir estimativas globais, regionais e por nível de renda. A p. 46 caracteriza o índice como um denominador global com ligação direta a pesquisas nacionais de força de trabalho. O artigo, porém, não identifica a PNAD Contínua, o 3º trimestre de 2025 nem a combinação executada nesta dissertação. (evidence_pages/ROW-CUR-0104.pdf) | A base analítica combina os microdados da PNAD Contínua do 3º trimestre de 2025 com os escores ocupacionais do ILO Global Index de Gmyrek et al. (2025); a escolha da PNAD, o período e o procedimento de vinculação devem ser documentados por uma fonte ou nota metodológica específica. | true |

### CLM-CUR-095 — 3.1 Base analítica e amostra, paragraph 4

**Claim (PT-BR):** A fonte declarada para a base é a combinação da PNAD Contínua do terceiro trimestre de 2025 com o ILO Working Paper 140.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| gmyrek_generative_2025 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 1 | A página identifica o documento como ILO Working Paper 140 e afirma que seu índice refinado pode ser ligado a microdados nacionais. Ela não identifica a PNAD Contínua, o IBGE nem o terceiro trimestre de 2025. (evidence_pages/ROW-CUR-0105.pdf) | Separar as atribuições: ‘A base combina os microdados da PNAD Contínua do terceiro trimestre de 2025 [citar a documentação específica do IBGE] com o índice refinado de exposição do ILO Working Paper 140 (Gmyrek et al., 2025).’ | true |

### CLM-CUR-099 — 4.1 Abordagem de diferenças em diferenças, paragraph 1

**Claim (PT-BR):** Brynjolfsson, Chandar e Chen (2025) são a principal referência para a estratégia empírica.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE | 1, 11-12 | A página 1 confirma título, autores e data da versão. As páginas 11-12 apresentam uma regressão Poisson em formato de event study, com efeitos firma-quintil e firma-tempo. Isso demonstra a pertinência metodológica da citação, mas a própria fonte não pode estabelecer que seja a principal referência da estratégia empírica da dissertação, qualificação que depende de comparação com as demais bases metodológicas do trabalho. (evidence_pages/ROW-CUR-0109.pdf) | Uma referência para a estratégia empírica é Brynjolfsson, Chandar e Chen (2025), que estimam uma regressão Poisson em formato de event study com efeitos firma-quintil e firma-tempo. | false |

### CLM-CUR-109 — 4.1 Abordagem de diferenças em diferenças, paragraph 5

**Claim (PT-BR):** Brynjolfsson, Chandar e Chen (2025) usam o lançamento público do ChatGPT, em 30 de novembro de 2022, como evento do estudo.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | PARTIALLY_SUPPORTED | MISATTRIBUTED_METHOD;MISSING_EVIDENCE | 4, 12 | Na p. 4, os autores situam os padrões no fim de 2022 e início de 2023, em torno da rápida proliferação de ferramentas de IA generativa, e a nota 3 afirma que a OpenAI introduziu o ChatGPT em novembro de 2022. Na p. 12, a regressão é denominada estudo de evento e outubro de 2022 é definido como período de referência. A fonte não informa o dia 30 nem declara que o lançamento público foi o evento escolhido para o desenho do estudo. (evidence_pages/ROW-CUR-0119.pdf) | Brynjolfsson, Chandar e Chen (2025) observam que a OpenAI introduziu o ChatGPT em novembro de 2022 e estimam um estudo de evento cujo período de referência é outubro de 2022. | true |

### CLM-CUR-112 — 4.1 Abordagem de diferenças em diferenças, paragraph 6

**Claim (PT-BR):** A literatura recente alerta para problemas em modelos de diferenças em diferenças quando as unidades começam a ser tratadas em datas diferentes.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| goodman_bacon_difference_2021 | NOT_VERIFIABLE | PDF_VERSION_MISMATCH | capa sem numeração; 2 | Na versão de trabalho disponível, o autor afirma que há conhecimento limitado sobre o modelo DD com efeitos fixos bidirecionais quando o momento do tratamento varia, mostra que o estimador compara grupos tratados em momentos distintos e apresenta ferramentas para analisar problemas práticos. O conteúdo sustenta diretamente a afirmação, mas o arquivo fornecido é o NBER Working Paper No. 25018, de setembro de 2018, e não o artigo do Journal of Econometrics de 2021 indicado na entrada bibliográfica. (evidence_pages/ROW-CUR-0122.pdf) | Substituir o PDF local pela versão publicada em 2021 e confirmar nela a mesma sustentação. Se a versão de trabalho for a fonte pretendida, corrigir a referência para NBER Working Paper No. 25018 (2018). A redação da afirmação pode ser mantida após essa correção documental. | true |
| callaway_difference_2021 | SUPPORTED | PDF_VERSION_MISMATCH | 1, 4 | Na página 4, os autores enquadram explicitamente uma literatura recente sobre efeitos heterogêneos em DiD e estudos de evento com variação no momento do tratamento e afirmam que esses trabalhos apresentam resultados negativos sobre a interpretação de especificações TWFE, além de mencionar suas armadilhas. Isso sustenta diretamente o alerta descrito na afirmação. A página 1 foi usada somente para identificar a versão do arquivo, não como evidência substantiva. (evidence_pages/ROW-CUR-0123.pdf) | Manter a afirmação. Para alinhar o artefato de evidência à entrada bibliográfica, substituir o PDF arXiv v4 pelo PDF da versão publicada de 2021 associada ao DOI; alternativamente, citar explicitamente a versão arXiv. | true |
| sun_estimating_2021 | SUPPORTED | PDF_VERSION_MISMATCH | unnumbered title page; 2 | Na introdução, Sun e Abraham situam a discussão em regressões de efeitos fixos em duas vias com heterogeneidade dos efeitos e variação no momento do tratamento. Em seguida, afirmam que o objetivo é revelar armadilhas potenciais: coeficientes de períodos relativos podem ser contaminados por efeitos de outros períodos, e o uso de leads para testar pré-tendências pode ser problemático. Isso sustenta diretamente o alerta expresso na afirmação. (evidence_pages/ROW-CUR-0124.pdf) | Manter a afirmação tal como está. Para eliminar a inconsistência de versão, substituir o PDF local pela versão publicada de 2021 ou alinhar a entrada bibliográfica ao manuscrito arXiv efetivamente arquivado. | true |
| de_chaisemartin_two-way_2020 | SUPPORTED | None | 9-10 | A página 9 define desenhos de adoção escalonada como aplicações em que grupos adotam o tratamento em datas heterogêneas e explica o problema de pesos negativos no estimador de efeitos fixos em duas vias. A página 10 acrescenta que grupos tratados mais cedo têm maior probabilidade de receber pesos negativos e que o estimador pode ser enganoso sob efeitos heterogêneos. Isso sustenta diretamente o alerta geral da afirmação. (evidence_pages/ROW-CUR-0125.pdf) | Manter a afirmação. Como refinamento opcional, explicitar que o problema destacado envolve estimadores de efeitos fixos em duas vias sob heterogeneidade dos efeitos em desenhos de adoção escalonada. Para consistência bibliográfica, alinhar o PDF arquivado à versão publicada indicada pelo DOI. | false |

### CLM-CUR-113 — 4.1 Abordagem de diferenças em diferenças, paragraph 6

**Claim (PT-BR):** O problema associado a datas de tratamento diferentes não se aplica ao desenho desta dissertação.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| goodman_bacon_difference_2021 | PARTIALLY_SUPPORTED | PDF_VERSION_MISMATCH | capa sem numeração; 1-2 | A capa identifica o arquivo como NBER Working Paper 25018, de setembro de 2018, e não como o artigo do Journal of Econometrics de 2021 registrado na bibliografia. Na introdução, a fonte contrasta o DD canônico de dois grupos e dois períodos com o modelo de efeitos fixos quando o momento do tratamento varia; neste último, o estimador combina comparações entre grupos de timing, inclusive entre unidades tratadas em duas datas diferentes. Assim, dado o desenho declarado na dissertação — uma única data de tratamento para todas as ocupações expostas e controles nunca tratados — é razoável inferir que a comparação cedo-versus-tarde discutida pela fonte não ocorre, embora a versão exata citada não tenha sido verificada. (evidence_pages/ROW-CUR-0126.pdf) | Manter a formulação da afirmação, mas alinhar o PDF à referência bibliográfica: obter a versão publicada de 2021 e reconferir nela a passagem metodológica, ou citar explicitamente o working paper NBER de 2018. | true |
| callaway_difference_2021 | SUPPORTED | PDF_VERSION_MISMATCH | 1-2 | Na p. 2, os autores distinguem o DiD canônico, com dois períodos e dois grupos, das aplicações com variação no momento do tratamento; concentram o artigo em adoção escalonada, associam a esse contexto problemas de interpretação causal de regressões TWFE e definem os grupos pelo período do primeiro tratamento. Isso sustenta diretamente a premissa metodológica. Dada a descrição, no próprio texto da dissertação, de uma data comum para todas as ocupações expostas e de controles nunca tratados, é razoável inferir que não surgem comparações entre coortes tratadas mais cedo e mais tarde. A p. 1 foi usada somente para identidade e versão; seu resumo não foi usado como evidência substantiva. (evidence_pages/ROW-CUR-0127.pdf) | Manter a afirmação, que delimita corretamente o problema às diferenças nas datas de tratamento; substituir o PDF arquivado pela versão publicada de 2021 para alinhar a evidência à entrada bibliográfica. | true |
| sun_estimating_2021 | SUPPORTED | PDF_VERSION_MISMATCH | folha de rosto sem numeração; 2; 5; 9-10 | A fonte define o desenho de estudo de evento que analisa como adoção escalonada, distingue-o do DiD em que as unidades tratadas iniciam em uma única data e os controles nunca são tratados e afirma que seu foco são as propriedades dos coeficientes quando há variação no momento inicial do tratamento. Na p. 9, separa explicitamente o caso simples de tratamento simultâneo do caso mais complexo de tratamentos em momentos variados. Condicional à descrição do desenho da dissertação, a inferência de que não há comparação entre coortes tratadas cedo e tarde é razoável. A folha de rosto identifica, porém, uma versão arXiv de 2020. (evidence_pages/ROW-CUR-0128.pdf) | Manter a formulação da inferência. Para sanar a divergência documental, substituir o PDF arXiv pela versão publicada de 2021 ou alinhar a entrada bibliográfica à versão efetivamente auditada. | false |
| de_chaisemartin_two-way_2020 | SUPPORTED | PDF_VERSION_MISMATCH | 1, 4, 8-10 | A página 9 define o desenho de adoção escalonada como aquele em que grupos adotam o tratamento em datas heterogêneas e explica que o peso negativo surge quando observações já tratadas funcionam como controle; as páginas 8-10 mostram o exemplo com adoção em períodos distintos e registram que grupos tratados mais cedo têm maior probabilidade de receber pesos negativos. Isso sustenta a premissa conceitual e torna razoável a inferência restrita de que, sem coortes tratadas antes e depois, esse mecanismo específico não ocorre. A página 4 ressalva que os resultados gerais do artigo sobre efeitos fixos bidirecionais não se limitam à adoção escalonada. A página 1 identifica a cópia examinada como arXiv v7, e não como a versão AER registrada na bibliografia. (evidence_pages/ROW-CUR-0129.pdf) | Manter a afirmação com seu escopo atual ou explicitar que se trata do viés específico de usar coortes já tratadas como controle para coortes tratadas depois; não generalizar a conclusão para todos os problemas de efeitos fixos bidirecionais. Para consistência bibliográfica, substituir a cópia arXiv pela versão AER citada. | false |

### CLM-CUR-114 — 4.1 Abordagem de diferenças em diferenças, paragraph 6

**Claim (PT-BR):** No desenho da dissertação, todas as ocupações expostas são consideradas tratadas na mesma data: o lançamento do ChatGPT.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| goodman_bacon_difference_2021 | PARTIALLY_SUPPORTED | PDF_VERSION_MISMATCH | capa sem paginação; 1-2 | A capa identifica o arquivo como NBER Working Paper No. 25018, de setembro de 2018, enquanto a entrada bibliográfica corresponde ao artigo publicado no Journal of Econometrics em 2021. Nas páginas impressas 1-2, o working paper explica que tratamentos em momentos diferentes geram variação de timing e que o estimador TWFE combina comparações entre grupos tratados em datas distintas. Condicionalmente à descrição interna de que todas as ocupações expostas recebem a mesma data de tratamento, é razoável inferir que não há comparação entre grupos tratados mais cedo e mais tarde; essa aplicação ao desenho da dissertação não é afirmada explicitamente pela fonte. O conteúdo metodológico está sustentado pela versão disponível, mas a edição citada de 2021 não foi verificada. (evidence_pages/ROW-CUR-0130.pdf) | Manter a inferência de desenho em formulação condicional, mas substituir o arquivo de 2018 pela versão publicada de 2021 correspondente ao DOI citado e repetir a conferência da passagem e da paginação. | false |
| callaway_difference_2021 | SUPPORTED | PDF_VERSION_MISMATCH | 1-2 | A página 2 descreve o DiD canônico como um desenho com dois períodos e dois grupos, contrasta-o com aplicações que apresentam variação no momento do tratamento e define cada grupo pelo período em que as unidades são tratadas pela primeira vez. Portanto, uma codificação em que todas as ocupações expostas recebem a mesma data de primeiro tratamento implica uma única coorte temporal, de modo consistente com a afirmação do autor. O artigo não menciona o ChatGPT nem verifica a codificação específica da dissertação; esses elementos são apresentados claramente como parte do desenho próprio. A página 1 foi usada somente para confirmar título, autores e versão, não como evidência substantiva. (evidence_pages/ROW-CUR-0131.pdf) | Manter a afirmação como formulação explícita do desenho próprio. Para alinhamento bibliográfico, substituir o PDF local pela versão final publicada ou registrar que os localizadores se referem ao manuscrito arXiv v4. | false |
| sun_estimating_2021 | SUPPORTED | PDF_VERSION_MISMATCH | folha de rosto sem numeração; 2 | Na p. 2, Sun e Abraham definem E_i como o momento em que cada unidade recebe inicialmente o tratamento e afirmam que as unidades são agrupadas em coortes conforme esse momento. Isso sustenta a premissa de que o problema analisado envolve variação temporal entre unidades. Se todas as ocupações expostas recebem uma data comum por construção, a conclusão de que não existem grupos tratados mais cedo e mais tarde decorre razoavelmente do desenho, embora a fonte não descreva a dissertação nem o lançamento do ChatGPT. A folha de rosto foi usada somente para identificar a versão do arquivo, não como evidência substantiva. (evidence_pages/ROW-CUR-0132.pdf) | Manter a formulação da afirmação; corrigir o acervo substituindo o manuscrito arXiv de 2020 pela versão publicada de 2021 indicada na bibliografia e reconfirmar o localizador. | true |
| de_chaisemartin_two-way_2020 | SUPPORTED | None | 2, 4 | Na página 2, os autores explicam que o estimador TWFE combina comparações DID entre pares de grupos e que, em algumas delas, o grupo de controle pode estar tratado nos dois períodos. Na página 4, caracterizam a adoção escalonada pela evolução temporal do tratamento de cada grupo. Isso sustenta a premissa metodológica; aplicar uma única data de tratamento às ocupações expostas é uma regra do desenho da dissertação, da qual decorre que não existem coortes tratadas mais cedo e mais tarde. (evidence_pages/ROW-CUR-0133.pdf) | Manter a redação; opcionalmente, explicitar que a data comum é uma convenção de codificação do desenho empírico. | false |

### CLM-CUR-115 — 4.1 Abordagem de diferenças em diferenças, paragraph 6

**Claim (PT-BR):** No desenho da dissertação, as ocupações não expostas permanecem como grupo de controle.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| goodman_bacon_difference_2021 | NOT_VERIFIABLE | PDF_VERSION_MISMATCH | N/A (capa sem paginação impressa); 2 | Na p. impressa 2, a versão disponível afirma que algumas especificações usam unidades não tratadas como grupo de controle e distingue esse caso das comparações entre unidades tratadas em datas diferentes. A capa, sem paginação impressa, identifica o arquivo como NBER Working Paper 25018, de setembro de 2018, enquanto a referência declara um artigo de 2021 no Journal of Econometrics. (evidence_pages/ROW-CUR-0134.pdf) | Substituir o PDF pela versão publicada de 2021 e confirmar nela a passagem correspondente antes de manter esta ocorrência; se a intenção for usar o texto examinado, corrigir a referência para o working paper NBER de 2018. | true |
| callaway_difference_2021 | PARTIALLY_SUPPORTED | PDF_VERSION_MISMATCH | 1, 11 | Na p. 11, a fonte afirma que, sob a Assumption 4, unidades nunca tratadas podem ser usadas como grupo de comparação fixo para todas as unidades eventualmente tratadas. Isso sustenta a premissa metodológica para manter as ocupações não expostas como controle, desde que elas correspondam às unidades nunca tratadas na codificação da dissertação e que se assumam as condições de identificação pertinentes. A p. 1 identifica o arquivo como arXiv v4 de 2020, e não como a versão editorial citada de 2021. (evidence_pages/ROW-CUR-0135.pdf) | Manter a redação da afirmação, mas substituir o PDF arXiv pela versão publicada de 2021 e confirmar que a passagem metodológica permanece equivalente. | true |
| sun_estimating_2021 | SUPPORTED | PDF_VERSION_MISMATCH | 5, 24 | Na página 5, os autores distinguem o desenho escalonado do desenho de diferenças em diferenças em que as unidades são tratadas em uma única data ou nunca tratadas. Na página 24, definem explicitamente as unidades nunca tratadas como a coorte de controle quando ela existe. Isso sustenta a aplicação metodológica feita pela dissertação às ocupações declaradas como não expostas. (evidence_pages/ROW-CUR-0136.pdf) | Manter a afirmação como está; para consistência bibliográfica, substituir o PDF arquivado do arXiv pela versão publicada de 2021. | false |
| de_chaisemartin_two-way_2020 | SUPPORTED | PDF_VERSION_MISMATCH | 1-3 | A introdução explica que o estimador de efeitos fixos em duas vias combina comparações de diferenças em diferenças e que, em algumas delas, o grupo usado como controle pode já estar tratado nos dois períodos; também afirma que o estimador alternativo pode ser aplicado quando há grupos cujo tratamento não muda entre datas consecutivas. Dado o desenho descrito pela autora — início comum para todas as ocupações expostas e ausência de tratamento para as não expostas —, é razoável inferir que as ocupações não expostas permanecem como controle. A fonte não descreve as ocupações nem enuncia essa conclusão específica. O arquivo auditado é a versão arXiv v7, enquanto a entrada bibliográfica identifica a versão publicada na AER. (evidence_pages/ROW-CUR-0137.pdf) | Manter a formulação da afirmação; antes da consolidação, alinhar o PDF e a entrada bibliográfica à mesma versão da obra. | true |

### CLM-CUR-117 — 4.1 Abordagem de diferenças em diferenças, paragraph 6

**Claim (PT-BR):** A condição principal do desenho é que os grupos apresentem trajetórias paralelas antes do evento; os diagnósticos não sustentam essa condição, o que limita a interpretação causal.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| goodman_bacon_difference_2021 | PARTIALLY_SUPPORTED | PDF_VERSION_MISMATCH | capa sem numeração; 1-2; 19 | Na p. impressa 1, o texto afirma que um DD 2×2 identifica o efeito médio sobre os tratados sob a hipótese de tendências comuns e distingue esse caso daquele em que tratamentos ocorrem em datas diferentes. Na p. 2, explica que a variação de timing cria comparações entre grupos tratados em momentos distintos. Na p. 19, apresenta testes de tendências pré-tratamento como diagnósticos da hipótese de identificação e ressalva os limites do teste por estudo de evento. Isso sustenta a premissa metodológica e torna razoável a inferência autoral de que diagnósticos desfavoráveis limitam a leitura causal. Contudo, o arquivo auditado é o working paper NBER de 2018, e não o artigo de 2021 identificado na entrada bibliográfica. (evidence_pages/ROW-CUR-0142.pdf) | Manter a inferência autoral e a remissão explícita aos diagnósticos da Seção 5, mas substituir o arquivo de trabalho de 2018 pela versão publicada de 2021 e reconferir nela o suporte metodológico. | true |
| callaway_difference_2021 | SUPPORTED | None | 2, 8-9, 25, 29, 32 | A fonte explica que, no DiD canônico, trajetórias paralelas dos resultados potenciais não tratados permitem identificar o efeito causal (p. 2) e formaliza versões condicionais dessa hipótese (p. 8). Ela distingue a hipótese contrafactual dos padrões pré-tratamento observados (p. 9), mas recomenda estimar parâmetros pré-tratamento para avaliar a credibilidade das hipóteses de identificação (p. 25). Na aplicação da própria fonte, pseudoefeitos pré-tratamento significativamente diferentes de zero são tratados como evidência sugestiva contra tendências paralelas e como motivo para interpretar resultados com cautela (pp. 29 e 32). Isso sustenta a lógica da inferência autoral; o resultado empírico específico dos diagnósticos da dissertação é corretamente atribuído à Seção 5, não à fonte. (evidence_pages/ROW-CUR-0143.pdf) | Manter a afirmação. Para máxima precisão técnica, pode-se chamar as trajetórias pré-evento de diagnóstico da plausibilidade da hipótese contrafactual de tendências paralelas. | false |
| sun_estimating_2021 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE;PDF_VERSION_MISMATCH | unnumbered title page; 5; 7; 29-30 | O preprint define o estudo de evento como um desenho de adoção escalonada e reconhece que ele inclui o DiD em que as unidades são tratadas em uma data comum ou nunca tratadas (p. 5). Em seguida, apresenta tendências paralelas dos resultados de base como a Assunção 1, mas também requer ausência de antecipação (p. 7); na conclusão, restringe o problema de contaminação a contextos com variação no timing e heterogeneidade dos efeitos e afirma que o estimador IW é identificado sob tendências paralelas e ausência de antecipação (pp. 29-30). A fonte não contém ChatGPT, ocupações ou os diagnósticos da Seção 5 da dissertação, portanto não verifica a premissa empírica de que esses diagnósticos não sustentam trajetórias paralelas nem declara a limitação causal específica da aplicação. (evidence_pages/ROW-CUR-0144.pdf) | Preservar a conclusão como inferência autoral, separando claramente o apoio metodológico de Sun e Abraham da evidência empírica interna da Seção 5. Substituir também o preprint arXiv pelo PDF da versão publicada citada, ou alinhar a referência bibliográfica à versão efetivamente usada. | true |
| de_chaisemartin_two-way_2020 | PARTIALLY_SUPPORTED | PDF_VERSION_MISMATCH | 1-3 | Na p. 2, o manuscrito afirma que regressões com efeitos fixos de grupo e tempo estimam o efeito sob a condição padrão de tendências comuns. Na p. 3, afirma que o estimador proposto depende de tendências comuns nos dois resultados potenciais e que essas condições são parcialmente testáveis por um teste de pré-tendências. Isso sustenta diretamente a premissa metodológica e torna razoável inferir que diagnósticos contrários às tendências paralelas limitam a interpretação causal. A constatação empírica sobre os diagnósticos é análise própria, explicitamente atribuída à Seção 5, e não aparece nesta fonte. A p. 1 identifica o arquivo como manuscrito arXiv v7 de 5 de março de 2020, não como a edição final da American Economic Review descrita na entrada bibliográfica. (evidence_pages/ROW-CUR-0145.pdf) | Manter a formulação da alegação, mas substituir o PDF de pré-publicação pela edição final da American Economic Review correspondente ao DOI da entrada bibliográfica e atualizar os localizadores de página. | true |

### CLM-CUR-118 — 4.2 Construção do painel ocupação-mês com CAGED e correspondência CBO → OIT, paragraph 5

**Claim (PT-BR):** Janelas de análise com mais tempo após o evento do que antes dele são apresentadas como prática corrente nessa literatura.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| klein_teeselink_generative_2025 | OVERSTATED | GENERALIZATION_OVERCLAIM | 11 | Na p. 11, o artigo informa que o estudo de evento usa 15 meses de dados pré-tratamento e 30 meses de dados pós-tratamento, confirmando uma janela assimétrica. A fonte, porém, não afirma que essa assimetria seja prática corrente na literatura; ela apenas descreve a própria especificação. (evidence_pages/ROW-CUR-0146.pdf) | Reformular para: “Klein Teeselink (2025, p. 11) adota uma janela assimétrica, com 15 meses de pré-tratamento e 30 meses de pós-tratamento.” Se a intenção for sustentar que essa é prática corrente, adicionar evidência de revisão ou múltiplos estudos representativos. | true |

### CLM-CUR-122 — 4.3 Especificação econométrica e desfechos, paragraph 18

**Claim (PT-BR):** Transformações como log(1+y) mudam a interpretação do coeficiente.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| santos_silva_log_2006 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE;PDF_VERSION_MISMATCH | capa sem numeração; 2-3; 10 | A versão disponível afirma que interpretar parâmetros de modelos log-linearizados estimados por MQO como elasticidades pode ser enganoso sob heterocedasticidade, relata que isso distorce a interpretação e estende a crítica a transformações não lineares. Contudo, ela não menciona nem analisa especificamente log(1+y). A capa identifica o arquivo como CEP Discussion Paper No. 701, de julho de 2005, e não como o artigo de periódico de 2006 descrito na entrada bibliográfica. (evidence_pages/ROW-CUR-0150.pdf) | Restringir a atribuição a Silva e Tenreyro à afirmação diretamente sustentada sobre log-linearização, interpretação como elasticidade e heterocedasticidade; manter log(1+y) apenas com fonte que trate explicitamente dessa transformação. Corrigir também a divergência entre o PDF de 2005 e a referência do artigo de 2006. | true |
| chen_logs_2024 | SUPPORTED | PDF_VERSION_MISMATCH | 1-2, 6 | Na p. 2, os autores apresentam log(1+Y) como transformação alternativa para desfechos com zero e afirmam que os efeitos assim transformados não devem ser interpretados como efeitos percentuais, pois dependem das unidades do desfecho. Na p. 6, aplicam explicitamente esse argumento a log(1+Y) e concluem que a interpretação como efeito percentual é comprometida pela dependência arbitrária das unidades. Isso sustenta diretamente que a transformação altera a interpretação do coeficiente ou efeito estimado. (evidence_pages/ROW-CUR-0151.pdf) | Manter a afirmação. Para rastreabilidade bibliográfica, substituir o arquivo local da versão arXiv pela versão publicada do mesmo artigo no Quarterly Journal of Economics. | false |

### CLM-CUR-123 — 4.3 Especificação econométrica e desfechos, paragraph 18

**Claim (PT-BR):** Transformações como log(1+y) podem gerar problemas sob heterocedasticidade.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| santos_silva_log_2006 | SUPPORTED | PDF_VERSION_MISMATCH | 28, 31 | Na p. 28, os autores afirmam que o resultado de inadequação também ocorre quando OLS usa ln(1+Tij) como variável dependente, em uma análise de especificação e heterocedasticidade. Na p. 31, concluem que a log-linearização — ou qualquer transformação não linear — na presença de heterocedasticidade leva a estimativas inconsistentes. (evidence_pages/ROW-CUR-0152.pdf) | Manter a afirmação; para alinhar a prova à entrada bibliográfica, substituir o PDF arquivado pela versão publicada de 2006 vinculada ao DOI. | false |
| chen_logs_2024 | PARTIALLY_SUPPORTED | PARTIAL_SCOPE;PDF_VERSION_MISMATCH | Main text pp. 1-2; Appendix pp. 7-8, 11 | Na Introdução, Chen e Roth incluem log(1+Y) entre as transformações log-like e mostram que seu ATE pode ser arbitrariamente sensível à unidade quando o tratamento afeta a margem extensiva; esse é um problema de escala e interpretação, não uma afirmação sobre heterocedasticidade. No Apêndice B.3, todas as ocorrências de heteroskedasticity qualificam erros-padrão robustos em um resultado sobre a convergência do t-estatístico após reescala. No Apêndice C.2, o artigo relata que regressões com log(1+Y) podem ser inconsistentes para beta em um modelo estrutural específico, mas não atribui essa inconsistência à heterocedasticidade; a nota 52 acrescenta que Santos Silva e Tenreyro não apresentam resultado formal para transformações log-like. A página de rosto identifica o arquivo como arXiv v7, de 15 de novembro de 2023, e não como a versão QJE 2024 da bibliografia. (evidence_pages/ROW-CUR-0153.pdf) | Reformular a atribuição a Chen e Roth para: “Transformações log-like como log(1+y) podem ser arbitrariamente sensíveis à unidade de medida quando há efeito na margem extensiva e não devem ser interpretadas automaticamente como efeitos percentuais.” Se a oração sobre heterocedasticidade for mantida, sustentá-la com uma fonte que trate diretamente de log(1+y) nessa condição. Substituir também o preprint pela versão QJE 2024 citada e conferir novamente as páginas. | true |

### CLM-CUR-132 — 4.5 Testes de robustez e diagnósticos, paragraph 7

**Claim (PT-BR):** O procedimento de Rambachan e Roth (2023) estima quanto as tendências anteriores ao evento poderiam divergir sem alterar a conclusão.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| rambachan_more_2023 | PARTIALLY_SUPPORTED | MISATTRIBUTED_METHOD | 2583-2584 | A seção 6.1.3 recomenda variar um parâmetro que governa quão diferentes as violações pós-tratamento das tendências paralelas podem ser das pré-tendências e relatar o valor de ruptura no qual hipóteses deixam de ser rejeitadas. No exemplo da seção 6.2, o valor de ruptura para efeito nulo é aproximadamente M̄ = 2. Isso sustenta a ideia de medir a sensibilidade da conclusão, mas não a afirmação de que o procedimento estima quanto as próprias tendências anteriores ao evento poderiam divergir. (evidence_pages/ROW-CUR-0162.pdf) | O procedimento de Rambachan e Roth (2023) avalia quão diferentes as violações pós-tratamento das tendências paralelas podem ser das pré-tendências antes que uma conclusão causal deixe de ser sustentada. | false |

### CLM-CUR-135 — 5.1 Resultados médios nacionais, paragraph 13

**Claim (PT-BR):** Brynjolfsson, Chandar e Chen (2025) não enfrentam o problema de tendências prévias observado nesta dissertação.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | OVERSTATED | GENERALIZATION_OVERCLAIM | 4, 14, 45-48 | Na p. 4, os autores resumem que a taxonomia de exposição não previa de modo relevante os resultados de emprego de jovens antes do uso disseminado de LLMs, inclusive no pico de desemprego da Covid-19, e situam a divergência no fim de 2022 e início de 2023. Contudo, na p. 14 reconhecem que, para as medidas de Eloundou et al. (2024), o quintil mais exposto já apresentava crescimento mais lento desde cerca de 2020; a Figura A16 (p. 45) mostra essa ressalva. A ausência de separação prévia é sustentada para as medidas Anthropic nas Figuras A17–A19 (pp. 46–48), não de forma irrestrita para todas as taxonomias. (evidence_pages/ROW-CUR-0165.pdf) | Brynjolfsson, Chandar e Chen (2025) não encontram divergências prévias nas medidas de exposição da Anthropic, mas reconhecem que, na medida de Eloundou et al. (2024), o quintil mais exposto já apresentava crescimento de emprego mais lento desde cerca de 2020. | false |

### CLM-CUR-138 — 5.1 Resultados médios nacionais, paragraph 13

**Claim (PT-BR):** A ausência de previsão prévia leva os autores a datar os padrões observados no fim de 2022 e no início de 2023.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | PARTIALLY_SUPPORTED | AUTHOR_INFERENCE_UNSUPPORTED | 4 | Na p. 4, os autores afirmam que a taxonomia de exposição à IA não previa de modo significativo os resultados de emprego dos jovens antes do uso disseminado de LLMs, inclusive durante o pico de desemprego da Covid-19. Na frase seguinte, situam o aparecimento mais agudo dos padrões no fim de 2022 e no início de 2023, em torno da rápida difusão das ferramentas de IA generativa. As premissas são sustentadas e o nexo inferencial é razoável, mas a fonte não declara explicitamente que a ausência de previsão prévia é o motivo que leva os autores a essa datação. (evidence_pages/ROW-CUR-0168.pdf) | Reescrever como: ‘A taxonomia de exposição não previa significativamente os resultados de emprego antes da difusão dos LLMs, inclusive durante o pico de desemprego da Covid-19; os autores situam o aparecimento mais agudo dos padrões no fim de 2022 e no início de 2023.’ | false |

### CLM-CUR-142 — 5.1 Resultados médios nacionais, paragraph 13

**Claim (PT-BR):** Em firmas adotantes, Hosseini Maasoum e Lichtinger (2025) documentam desaceleração das contratações.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| hosseini_maasoum_generative_2025 | OVERSTATED | WRONG_POPULATION;PDF_VERSION_MISMATCH | 1, 40–41 | Na seção 5.5, os autores estimam regressões DiD para fluxos de trabalhadores juniores. Em relação às firmas não adotantes, as adotantes contrataram em média 4,0 trabalhadores juniores a menos por trimestre após 2023T1, cerca de 80% abaixo da média pré-período; a Tabela 4 reporta β = -4,006 (EP 0,221). Isso sustenta uma desaceleração das contratações juniores, não das contratações em geral. A folha de rosto identifica o arquivo como versão de 6 de junho de 2026. (evidence_pages/ROW-CUR-0172.pdf) | Reescrever como: 'Em relação às não adotantes, firmas adotantes reduziram as contratações de trabalhadores juniores após 2023T1.' Atualizar também a entrada bibliográfica para refletir a versão do PDF de 2026-06-06, ou substituir o arquivo pela versão de 2025 citada. | false |

### CLM-CUR-143 — 5.1 Resultados médios nacionais, paragraph 13

**Claim (PT-BR):** Em firmas adotantes, a desaceleração das contratações é acompanhada por queda nos desligamentos.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| hosseini_maasoum_generative_2025 | OVERSTATED | WRONG_POPULATION | 40-41 | A Seção 5.5 estima regressões DiD para fluxos de trabalhadores juniores. Após 2023Q1, firmas adotantes contrataram em média 4,0 juniores a menos por trimestre e tiveram cerca de 1,1 separações de juniores a menos, relativamente às firmas não adotantes; a queda nos desligamentos compensou parcialmente a contração das contratações. As direções descritas na afirmação constam da fonte, mas o resultado é específico a juniores e relativo às não adotantes. (evidence_pages/ROW-CUR-0173.pdf) | Em relação às firmas não adotantes após 2023Q1, firmas adotantes reduziram as contratações de trabalhadores juniores e também seus desligamentos, embora a queda nas contratações tenha sido cerca de quatro vezes maior. | false |

### CLM-CUR-147 — 5.1 Resultados médios nacionais, paragraph 13

**Claim (PT-BR):** O padrão da evidência posterior ainda não deve ser tratado como consolidado.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| humlum_still_2025 | SUPPORTED | None | 3 | Na página impressa 3, o artigo informa que os registros administrativos cobrem ganhos e horas mensais até dezembro de 2024 e que, em diferenças-em-diferenças, os efeitos do uso de chatbots de IA sobre ganhos e horas são precisamente nulos. As estimativas se concentram em zero e os intervalos de confiança excluem efeitos médios superiores a 2%. Isso sustenta diretamente o componente factual atribuído a Humlum e Vestergaard. A conclusão de que a evidência posterior ainda não está consolidada é uma síntese autoral entre vários estudos, não uma afirmação explícita deste artigo isoladamente. (evidence_pages/ROW-CUR-0180.pdf) | Manter a formulação e a citação como estão; nenhuma revisão é necessária para esta ocorrência. | false |
| chandar_tracking_2025 | SUPPORTED | PDF_VERSION_MISMATCH | 1, 6-7 | Nas pp. 6-7, a seção 4.1 informa que, entre os quartis de exposição à IA, há pouca evidência de perda de emprego ou crescimento salarial mais lento; na p. 7, registra pouca ou nenhuma evidência de declínio relativo do emprego nas ocupações mais expostas e crescimento semelhante dos ganhos reais. Isso sustenta a premissa agregada atribuída a Chandar e torna razoável sua contribuição à síntese de que a evidência não está consolidada. A p. 1 foi usada somente para identificar a revisão do PDF, não como evidência substantiva baseada no resumo. (evidence_pages/ROW-CUR-0181.pdf) | Manter a inferência substantiva; para tornar a premissa de Chandar ainda mais precisa, pode-se explicitar ‘no agregado da CPS’. Separadamente, alinhar a data bibliográfica à revisão auditada de 2025-08-01 ou recuperar a versão de 2025-06-03. | false |
| hosseini_maasoum_generative_2025 | OVERSTATED | WRONG_POPULATION | 40-42 | Na seção 5.5, regressões DiD mostram que, após 2023T1 e relativamente às não adotantes, firmas adotantes contrataram em média 4,0 trabalhadores juniores a menos por trimestre e tiveram 1,1 separação júnior a menos. A contração da contratação é cerca de quatro vezes maior e domina o efeito líquido. A conclusão caracteriza o estudo como evidência inicial, recomenda cautela e deixa em aberto a persistência do padrão. (evidence_pages/ROW-CUR-0182.pdf) | Manter a inferência final, mas qualificar a premissa como ‘a desaceleração das contratações de trabalhadores juniores, acompanhada de queda nos desligamentos desse grupo, em firmas adotantes’. | false |
| klein_teeselink_generative_2025 | SUPPORTED | None | 4, 14, 20 | Na p. 4, o artigo contrapõe estudos internacionais com quedas de emprego a resultados nulos na CPS e em dados administrativos dinamarqueses, qualificando-os como disparidades. Na p. 14, relata que um desvio-padrão adicional de exposição a LLMs está associado a redução de 0,3% no emprego total de firmas britânicas no período pós-tratamento, com significância apenas marginal no agregado. Na p. 20, define job postings como o número de novas vagas e estima redução média de 3,9% no volume de postings em ocupações mais expostas (p = 0,029). Isso sustenta a premissa negativa atribuída à fonte e torna razoável a inferência cautelosa da dissertação quando combinada aos resultados nulos citados no excerto. (evidence_pages/ROW-CUR-0183.pdf) | Manter a redação; nenhuma correção é necessária. Em eventual ajuste de precisão, pode-se explicitar que esta fonte fornece o resultado negativo britânico e que a conclusão sobre consolidação é uma síntese autoral. | false |

### CLM-CUR-154 — 5.2.3 Resultados por faixa etária, paragraph 9

**Claim (PT-BR):** Brynjolfsson, Chandar e Chen (2025) reportam queda de aproximadamente 12 pontos log para a coorte de 22 a 25 anos.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| brynjolfsson_canaries_2025 | PARTIALLY_SUPPORTED | WRONG_MAGNITUDE | 4 | Na p. 4, os autores informam que, para trabalhadores de 22 a 25 anos, o emprego relativo nos quintis mais expostos à IA caiu 15 pontos log em comparação com o quintil menos exposto. A faixa etária, a direção e o contraste entre quintis estão corretos, mas a magnitude de cerca de 12 pontos log não corresponde à versão auditada. (evidence_pages/ROW-CUR-0192.pdf) | Substituir “queda de cerca de 12 pontos log” por “queda de 15 pontos log no emprego relativo dos trabalhadores de 22 a 25 anos nos quintis mais expostos à IA, em comparação com o quintil menos exposto”. | false |

### CLM-CUR-162 — 5.2.4 Resultados por nível de escolaridade, paragraph 8

**Claim (PT-BR):** Hosseini Maasoum e Lichtinger (2025) identificam diferenças importantes dentro do próprio ensino superior.

**Current reconciliation:** `REUSED_EXACT`.

| Source | Verdict | Problem | Printed pages | Evidence | Recommended revision (PT-BR) | New source? |
| --- | --- | --- | --- | --- | --- | --- |
| hosseini_maasoum_generative_2025 | PARTIALLY_SUPPORTED | PDF_VERSION_MISMATCH | 1; A.13–A.14 | O Apêndice A.3 da versão de 6 de junho de 2026 divide os trabalhadores juniores em cinco estratos de qualidade ou prestígio da instituição de ensino e encontra um padrão em U: a maior queda relativa ocorre no estrato 3, os estratos 2 e 4 também apresentam reduções significativas e os estratos 1 e 5 têm as menores quedas. Isso sustenta a existência de diferenças internas ao ensino superior. A folha de rosto, contudo, identifica o PDF auditado como versão de 2026, enquanto a entrada bibliográfica data o trabalho em 2025. (evidence_pages/ROW-CUR-0200.pdf) | Manter a afirmação substantiva, mas atualizar a chamada para Hosseini Maasoum e Lichtinger (2026) e a data da entrada bibliográfica para 2026-06-06. Alternativamente, localizar e verificar a versão arquivada de 31 de agosto de 2025 antes de conservar o ano 2025. | false |

## Claims currently flagged as needing another source

`CLM-CUR-005`, `CLM-CUR-010`, `CLM-CUR-012`, `CLM-CUR-013`, `CLM-CUR-018`, `CLM-CUR-022`, `CLM-CUR-025`, `CLM-CUR-027`, `CLM-CUR-045`, `CLM-CUR-064`, `CLM-CUR-089`, `CLM-CUR-092`, `CLM-CUR-094`, `CLM-CUR-095`, `CLM-CUR-109`, `CLM-CUR-112`, `CLM-CUR-113`, `CLM-CUR-115`, `CLM-CUR-117`, `CLM-CUR-118`, `CLM-CUR-122`, `CLM-CUR-123`

## Source-version incompatibilities

| Citation key | Required decision |
| --- | --- |
| bick_rapid_2024 | Align Zotero, library.bib, the reference entry, and the in-text year to Federal Reserve Bank of St. Louis Working Paper 2024-027F, revision dated 27 October 2025. |
| hosseini_maasoum_generative_2025 | The audited PDF is dated 6 June 2026, while library.bib and the Notion reference identify the 31 August 2025 version. Either update the record and citation year or restore and audit the cited version. |
| klein_teeselink_generative_2025 | Align the Notion reference dated 22 September 2025 with the 21 December 2025 version recorded in library.bib and the stored PDF. |
| humlum_still_2025 | Align the May 2025 title/date in the Notion reference with the official NBER revision stored and audited (revised March 2026), including its current title and version note. |
| chandar_tracking_2025 | Align the 3 June 2025 Notion/library metadata with the audited PDF revision dated 1 August 2025, or restore the cited June file. |
| goodman_bacon_difference_2021 | Replace the 2018 working-paper PDF with the published 2021 article, or explicitly cite the working paper and recheck its pagination. |
| callaway_difference_2021 | Replace the archived arXiv manuscript with the published 2021 article associated with the DOI, then recheck page locators. |
| sun_estimating_2021 | Replace the 2020 arXiv manuscript with the published 2021 article, or identify the preprint explicitly in the bibliography. |
| de_chaisemartin_two-way_2020 | Align the stored pre-publication PDF with the final American Economic Review article and refresh page locators. |
| santos_silva_log_2006 | Replace the archived earlier manuscript with the published 2006 Review of Economics and Statistics article. |
| chen_logs_2024 | Replace the arXiv manuscript with the published Quarterly Journal of Economics article and refresh page locators. |

These alignment items include all 31 rows carrying the explicit PDF_VERSION_MISMATCH code, including all 19 SUPPORTED rows with that code, plus the Bick, Humlum, and Klein Teeselink metadata/version dependencies identified during current-reference reconciliation.

## Paused blind quality control

| Field | Value |
| --- | --- |
| Checkpoint | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/quality_control/PAUSE_CHECKPOINT.json |
| Queue rows | 208 |
| Completed | 11 |
| Prompt ready | 3 |
| Pending | 194 |
| Agrees | 8 |
| Needs adjudication | 3 |
| Interrupted row | ROW-CUR-0012 |
| Remaining QC processes | 0 |

No partial output from the interrupted row was promoted. The primary TSV retained its pre-pause SHA-256 and the completed QC artifacts remain resumable. This is why the present report is provisional.

## Editorial handoff

The proposed Notion edits are listed in `references/notion_changes/PRIMARY_NOTION_CHANGESET.md` and `references/notion_changes/notion_change_queue.tsv`. No Notion, Zotero, PDF, or library.bib content was changed while producing this report.
