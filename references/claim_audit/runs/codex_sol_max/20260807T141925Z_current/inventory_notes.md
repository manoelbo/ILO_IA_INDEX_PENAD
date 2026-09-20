# Current Claim Inventory Notes

## Scope

This inventory was rebuilt from the frozen current dissertation snapshot at `source_snapshot/notion_page.md`. It covers formal author-year citations in the dissertation body, prose, tables, captions, and table notes through Appendix D, stopping before the `REFERÊNCIAS` section. The Notion page properties and AI-generated page summary were treated as metadata rather than dissertation body text.

No source PDF was opened, no claim was fact-checked, and the `fact_checked` and `pages` fields remain blank by design. Historical artifacts were used only to understand the schema and atomization convention.

Mentions of the Benjamini-Hochberg procedure were excluded as purely instrumental descriptions of the multiple-testing workflow, as instructed.

## Counts

| Measure | Count |
|---|---:|
| Formal citation occurrences | 59 |
| Unique atomic claims | 175 |
| Claim-source-occurrence rows | 213 |
| Unique citation keys | 22 |

| Claim type | Unique claims | Rows |
|---|---:|---:|
| `DIRECT` | 111 | 126 |
| `AUTHOR_INFERENCE` | 64 | 87 |

## Occurrence Coverage

Every formal occurrence has at least one atomic claim row. In grouped citations, shared claims retain one `claim_id` and expand to one row per `citation_key`.

| Occurrence | Citation key | Section / paragraph | Atomic claims | Rows |
|---|---|---|---:|---:|
| `CIT-CUR-001` | `bick_rapid_2024` | 1 Introdução / 1 | 4 | 4 |
| `CIT-CUR-002` | `eloundou_gpts_2023` | 1 Introdução / 2 | 2 | 2 |
| `CIT-CUR-003` | `brynjolfsson_canaries_2025` | 1 Introdução / 2 | 5 | 5 |
| `CIT-CUR-004` | `hosseini_maasoum_generative_2025` | 1 Introdução / 2 | 5 | 5 |
| `CIT-CUR-005` | `klein_teeselink_generative_2025` | 1 Introdução / 2 | 5 | 5 |
| `CIT-CUR-006` | `gmyrek_generative_2025` | 1 Introdução / 5 | 4 | 4 |
| `CIT-CUR-007` | `brynjolfsson_canaries_2025` | 1 Introdução / 8 | 2 | 2 |
| `CIT-CUR-008` | `autor_skill_2003` | 2.2 Fundamentos conceituais: tarefas, automação e complementaridade / 1 | 3 | 3 |
| `CIT-CUR-009` | `agarwal_combining_2023` | 2.2 Fundamentos conceituais: tarefas, automação e complementaridade / 2 | 3 | 3 |
| `CIT-CUR-010` | `eloundou_gpts_2023` | 2.3 Índices de exposição à IA na literatura / 3 | 9 | 9 |
| `CIT-CUR-011` | `benitez_mirror_2024` | 2.3 Índices de exposição à IA na literatura / 4 | 7 | 7 |
| `CIT-CUR-012` | `appel_anthropic_2026` | 2.3 Índices de exposição à IA na literatura / 5 | 4 | 4 |
| `CIT-CUR-013` | `gmyrek_generative_2025` | 2.3 Índices de exposição à IA na literatura / 6 | 12 | 12 |
| `CIT-CUR-014` | `gmyrek_generative_2025` | 2.3 Índices de exposição à IA na literatura / 6 | 1 | 1 |
| `CIT-CUR-015` | `eloundou_gpts_2023` | 2.3 Índices de exposição à IA na literatura / 6 | 9 | 9 |
| `CIT-CUR-016` | `benitez_mirror_2024` | 2.3 Índices de exposição à IA na literatura / 6 | 9 | 9 |
| `CIT-CUR-017` | `appel_anthropic_2026` | 2.3 Índices de exposição à IA na literatura / 6 | 7 | 7 |
| `CIT-CUR-018` | `gmyrek_generative_2025` | 2.3 Índices de exposição à IA na literatura / 6 | 9 | 9 |
| `CIT-CUR-019` | `gmyrek_generative_2025` | 2.4 Escolha do índice da OIT e adaptação às bases brasileiras / 1 | 3 | 3 |
| `CIT-CUR-020` | `gmyrek_generative_2025` | 3.1 Base analítica e amostra / 1 | 1 | 1 |
| `CIT-CUR-021` | `gmyrek_generative_2025` | 3.1 Base analítica e amostra / 4 | 1 | 1 |
| `CIT-CUR-022` | `brasil_decreto_12342_2024` | 3.1 Base analítica e amostra / 4 | 1 | 1 |
| `CIT-CUR-023` | `osorio_o_2003` | 3.5.2 Análise por raça / 2 | 1 | 1 |
| `CIT-CUR-024` | `brynjolfsson_canaries_2025` | 3.5.3 Análise por faixa etária / 2 | 1 | 1 |
| `CIT-CUR-025` | `brynjolfsson_canaries_2025` | 4.1 Abordagem de diferenças em diferenças / 1 | 3 | 3 |
| `CIT-CUR-026` | `brynjolfsson_canaries_2025` | 4.1 Abordagem de diferenças em diferenças / 1 | 7 | 7 |
| `CIT-CUR-027` | `brynjolfsson_canaries_2025` | 4.1 Abordagem de diferenças em diferenças / 5 | 1 | 1 |
| `CIT-CUR-028` | `humlum_still_2025` | 4.1 Abordagem de diferenças em diferenças / 5 | 2 | 2 |
| `CIT-CUR-029` | `goodman_bacon_difference_2021` | 4.1 Abordagem de diferenças em diferenças / 6 | 6 | 6 |
| `CIT-CUR-030` | `callaway_difference_2021` | 4.1 Abordagem de diferenças em diferenças / 6 | 6 | 6 |
| `CIT-CUR-031` | `sun_estimating_2021` | 4.1 Abordagem de diferenças em diferenças / 6 | 6 | 6 |
| `CIT-CUR-032` | `de_chaisemartin_two-way_2020` | 4.1 Abordagem de diferenças em diferenças / 6 | 6 | 6 |
| `CIT-CUR-033` | `klein_teeselink_generative_2025` | 4.2 Construção do painel ocupação-mês com CAGED e correspondência CBO → OIT / 5 | 3 | 3 |
| `CIT-CUR-034` | `brynjolfsson_canaries_2025` | 4.3 Especificação econométrica e desfechos / 1 | 1 | 1 |
| `CIT-CUR-035` | `santos_silva_log_2006` | 4.3 Especificação econométrica e desfechos / 18 | 2 | 2 |
| `CIT-CUR-036` | `chen_logs_2024` | 4.3 Especificação econométrica e desfechos / 18 | 2 | 2 |
| `CIT-CUR-037` | `brynjolfsson_canaries_2025` | 4.3 Especificação econométrica e desfechos / 18 | 1 | 1 |
| `CIT-CUR-038` | `brynjolfsson_canaries_2025` | 4.4 Heterogeneidades e estudos de caso / 1 | 5 | 5 |
| `CIT-CUR-039` | `teutloff_winners_2025` | 4.5 Testes de robustez e diagnósticos / 3 | 2 | 2 |
| `CIT-CUR-040` | `rambachan_more_2023` | 4.5 Testes de robustez e diagnósticos / 7 | 2 | 2 |
| `CIT-CUR-041` | `brynjolfsson_canaries_2025` | 5.1 Resultados médios nacionais / 13 | 5 | 5 |
| `CIT-CUR-042` | `humlum_still_2025` | 5.1 Resultados médios nacionais / 13 | 4 | 4 |
| `CIT-CUR-043` | `chandar_tracking_2025` | 5.1 Resultados médios nacionais / 13 | 3 | 3 |
| `CIT-CUR-044` | `hosseini_maasoum_generative_2025` | 5.1 Resultados médios nacionais / 13 | 4 | 4 |
| `CIT-CUR-045` | `klein_teeselink_generative_2025` | 5.1 Resultados médios nacionais / 13 | 4 | 4 |
| `CIT-CUR-046` | `brynjolfsson_canaries_2025` | 5.2.1 Resultados por sexo / 9 | 1 | 1 |
| `CIT-CUR-047` | `gmyrek_generative_2025` | 5.2.1 Resultados por sexo / 9 | 2 | 2 |
| `CIT-CUR-048` | `brynjolfsson_canaries_2025` | 5.2.2 Resultados por raça/cor / 10 | 1 | 1 |
| `CIT-CUR-049` | `hosseini_maasoum_generative_2025` | 5.2.2 Resultados por raça/cor / 10 | 1 | 1 |
| `CIT-CUR-050` | `klein_teeselink_generative_2025` | 5.2.2 Resultados por raça/cor / 10 | 1 | 1 |
| `CIT-CUR-051` | `brynjolfsson_canaries_2025` | 5.2.3 Resultados por faixa etária / 1 | 1 | 1 |
| `CIT-CUR-052` | `brynjolfsson_canaries_2025` | 5.2.3 Resultados por faixa etária / 9 | 6 | 6 |
| `CIT-CUR-053` | `klein_teeselink_generative_2025` | 5.2.4 Resultados por nível de escolaridade / 8 | 2 | 2 |
| `CIT-CUR-054` | `brynjolfsson_canaries_2025` | 5.2.4 Resultados por nível de escolaridade / 8 | 1 | 1 |
| `CIT-CUR-055` | `hosseini_maasoum_generative_2025` | 5.2.4 Resultados por nível de escolaridade / 8 | 1 | 1 |
| `CIT-CUR-056` | `klein_teeselink_generative_2025` | 5.2.5 Resultados por faixa salarial ocupacional / 9 | 3 | 3 |
| `CIT-CUR-057` | `brynjolfsson_canaries_2025` | 5.2.5 Resultados por faixa salarial ocupacional / 9 | 1 | 1 |
| `CIT-CUR-058` | `brynjolfsson_canaries_2025` | 6.3 Interpretação / 3 | 4 | 4 |
| `CIT-CUR-059` | `brynjolfsson_canaries_2025` | Apêndice C — Casos ocupacionais e trajetórias por idade / 8 | 5 | 5 |

## Ambiguous or Non-Propositional Cases

- `CIT-CUR-013` and `CIT-CUR-014` refer to Gmyrek et al. in the same paragraph. They remain separate occurrences because the paragraph first names the index and later supplies a second explicit page-located citation; anaphoric claims stop at the later citation.
- `CIT-CUR-025` and `CIT-CUR-026` refer to Brynjolfsson, Chandar, and Chen in the same paragraph. They remain separate because the first is a narrative citation and the second is a page-located parenthetical citation attached to the estimation design.
- The Teutloff citation is split across Notion span markup in the snapshot, but author, year, and page form one formal occurrence (`CIT-CUR-039`).
- The title-only mention of *Canaries in the Coal Mine* at the start of Appendix C has no author-year citation and was not counted as a separate formal occurrence. The later author-year citation in the appendix is `CIT-CUR-059`.
- The sentence naming Hosseini Maasoum and Lichtinger without a year in Section 5.2.3 was not counted as a new formal occurrence. Their formally cited propositions elsewhere remain inventoried.
- Formal citations with no proposition: 0. All 59 retained occurrences have at least one claim row.

## Validation

- Header matches the required 12-column order exactly.
- Tab-delimited CSV parsing returns width 12 for every row.
- `CLM-CUR`, `CIT-CUR`, and `ROW-CUR` identifiers are continuous in their respective sequences.
- Duplicate `(claim_id, citation_key, occurrence_id)` triples: 0.
- Uncovered occurrence IDs: 0.
- Every citation key exists in `references/library.bib`, and every `work` value matches the normalized current BibTeX title.
- `fact_checked` and `pages` are blank in all 213 rows.
- `benjamini_controlling_1995` rows: 0, consistent with the instructed procedural exclusion.
