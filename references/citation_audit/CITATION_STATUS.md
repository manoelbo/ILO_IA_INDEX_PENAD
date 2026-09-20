# Citation Status Audit

## Verdict

This read-only audit reconciles the current Notion dissertation with the canonical portable bibliography, [`references/library.bib`](../library.bib).

- **58 formal citation occurrences** were found, covering **24 unique works**.
- **All 58 occurrences map unambiguously** to one `.bib` key; no cited work is absent from `library.bib`.
- **52 occurrence rows have correct in-text formatting**. Six rows require correction, but they represent only **three visible citation constructs** because one grouped citation maps to four works.
- **31 occurrences have a valid hyperlink** and **27 have no hyperlink**. No existing link was classified as broken or inappropriate. Hyperlinks are informative and are not required for ABNT compliance.
- The Notion reference list contains **15 works**. All 15 are cited, but **nine cited works are missing** from that list.
- Of the 15 rendered references, **3 are currently OK** and **12 require normalization**. The nine missing references are marked `AUSENTE`.
- The canonical `.bib` contains **44 records**: 24 cited in the current dissertation and 20 currently uncited.
- Portable PDF coverage is **23 of 24 cited works**. The sole cited work without a PDF is the Brazilian decree, for which the official legal URL is the appropriate source.
- This step checks citation/reference correspondence and formatting. It **does not verify whether each source substantively supports the surrounding claim**.

The occurrence-level machine-readable evidence is in [`citation_occurrences.tsv`](citation_occurrences.tsv). The incremental audit of the eight methodological records is in [`bibcheck_20260801T140054Z/bibcheck_report.md`](bibcheck_20260801T140054Z/bibcheck_report.md).

## Frozen source snapshot

| Field | Value |
|---|---|
| Notion page | [Dissertação de Mestrado V2](https://app.notion.com/p/325cc8ca461082d794db01323b295bb5) |
| Page ID | `325cc8ca-4610-82d7-94db-01323b295bb5` |
| Notion last-edited timestamp | `2026-08-01T13:35:00.000Z` |
| Semantic SHA-256 | `d04060553ccad2aa746e261b72d85f08fe48ee13130aea4d444891d238c74d0f` |
| Canonical bibliography | `references/library.bib` (44 records) |
| Excluded bibliography | Root-level `.bib` export (not used) |
| Audit date | 2026-08-01 |

The page was fetched again after the audit. Its normalized content and semantic SHA-256 were unchanged. Raw fetch hashes differed only because Notion rotated expiring query parameters on signed image URLs.

## Standards and status rules

The audit follows the [FGV Manual de Formatação de Trabalhos Acadêmicos (2025)](https://biblioteca.fgv.br/sites/default/files/2025-08/formatacao-de-trabalhos-academicos-manual-fgv-visualizacao-2025.pdf), ABNT NBR 10520:2023 for in-text citations, and the NBR 6023:2025 reference update [reported by FGV](https://portal.fgv.br/noticias/webinar-debate-atualizacoes-das-normas-abnt-para-trabalhos-academicos).

- **Formatação no Texto:** `OK`, `CORRIGIR`, or `REVISÃO MANUAL`.
- **Link no Texto:** `VÁLIDO`, `AUSENTE`, `QUEBRADO`, or `DESTINO INADEQUADO`.
- **Citação em Referência:** `SIM`, `NÃO`, or `AMBÍGUA`.
- **Formatação em Referência:** `OK`, `CORRIGIR`, `AUSENTE`, or `N/A`.

For consolidated rows, the link column reports valid and absent occurrence counts. An absent hyperlink is not itself a formatting error.

## Consolidated status by work

| Citation key | Work | Occurrences | Formatação no Texto | Link no Texto | Citação em Referência | Formatação em Referência | Main action |
|---|---|---:|---|---|---|---|---|
| `bick_rapid_2024` | The rapid adoption of generative AI (2024) | 1 | OK | 1 VÁLIDO; 0 AUSENTE | SIM | CORRIGIR | Update to the canonical 2026 article, or explicitly retain the preliminary working-paper version and add no. 2024-027. |
| `eloundou_gpts_2023` | GPTs are GPTs: An early look at the labor market impact potential of large language models (2023) | 3 | OK | 0 VÁLIDO; 3 AUSENTE | SIM | CORRIGIR | Bold the main title only; leave the subtitle unbolded. |
| `brynjolfsson_canaries_2025` | Canaries in the coal mine? Six facts about the recent employment effects of artificial intelligence (2025) | 16 | CORRIGIR (1) | 14 VÁLIDO; 2 AUSENTE | SIM | CORRIGIR | Fix CIT-025 coauthor separators; bold the main title only. |
| `hosseini_maasoum_generative_2025` | Generative AI as seniority-biased technological change: Evidence from u.s. Résumé and job posting data (2025) | 4 | OK | 4 VÁLIDO; 0 AUSENTE | SIM | CORRIGIR | Bold the main title only. |
| `klein_teeselink_generative_2025` | Generative AI and labor market outcomes: Evidence from the united kingdom (2025) | 6 | OK | 5 VÁLIDO; 1 AUSENTE | SIM | CORRIGIR | Bold the main title only. |
| `gmyrek_generative_2025` | Generative AI and jobs: A refined global index of occupational exposure (2025) | 7 | OK | 0 VÁLIDO; 7 AUSENTE | SIM | CORRIGIR | Bold the main title only and add ILO Working Paper no. 140. |
| `autor_skill_2003` | The skill content of recent technological change: An empirical exploration (2003) | 1 | OK | 1 VÁLIDO; 0 AUSENTE | SIM | OK | No correction identified. |
| `agarwal_combining_2023` | Combining human expertise with artificial intelligence: Experimental evidence from radiology (2023) | 1 | OK | 0 VÁLIDO; 1 AUSENTE | SIM | CORRIGIR | Bold the main title only and add NBER Working Paper no. 31422. |
| `benitez_mirror_2024` | Mirror, mirror on the wall: Which jobs will AI replace after all?: A new index of occupational exposure (2024) | 2 | OK | 2 VÁLIDO; 0 AUSENTE | SIM | CORRIGIR | Bold the main title only and add IDB-WP-1624. |
| `appel_anthropic_2026` | Anthropic economic index report: Economic primitives (2026) | 2 | OK | 0 VÁLIDO; 2 AUSENTE | SIM | CORRIGIR | Bold the main title only; leave “Economic primitives” unbolded. |
| `brasil_decreto_12342_2024` | Decreto nº 12.342, de 30 de dezembro de 2024 (2024) | 1 | OK | 1 VÁLIDO; 0 AUSENTE | SIM | OK | No correction identified. |
| `osorio_o_2003` | O sistema classificatório de “cor ou raça” do IBGE (2003) | 1 | OK | 1 VÁLIDO; 0 AUSENTE | SIM | CORRIGIR | Add Texto para Discussão no. 996. |
| `goodman_bacon_difference_2021` | Difference-in-differences with variation in treatment timing (2021) | 1 | CORRIGIR (1) | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Correct the grouped citation and add the full reference. |
| `callaway_difference_2021` | Difference-in-differences with multiple time periods (2021) | 1 | CORRIGIR (1) | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Correct the grouped citation and add the full reference. |
| `sun_estimating_2021` | Estimating dynamic treatment effects in event studies with heterogeneous treatment effects (2021) | 1 | CORRIGIR (1) | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Correct the grouped citation and add the full reference. |
| `de_chaisemartin_two-way_2020` | Two-way fixed effects estimators with heterogeneous treatment effects (2020) | 1 | CORRIGIR (1) | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Correct the grouped citation and add the full reference. |
| `humlum_still_2025` | Still waters, rapid currents: Early labor market transformation under generative AI (2025) | 2 | OK | 1 VÁLIDO; 1 AUSENTE | SIM | CORRIGIR | Bold the main title only and add NBER Working Paper no. 33777. |
| `santos_silva_log_2006` | The log of gravity (2006) | 1 | CORRIGIR (1) | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Use the compound surname “Santos Silva” in text and add the full reference. |
| `chen_logs_2024` | Logs with zeros? Some problems and solutions (2024) | 1 | OK | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Add the full reference. |
| `benjamini_controlling_1995` | Controlling the false discovery rate: A practical and powerful approach to multiple testing (1995) | 1 | OK | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Add the full reference. |
| `teutloff_winners_2025` | Winners and losers of generative AI: Early evidence of shifts in freelancer demand (2025) | 1 | OK | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Add the full reference. |
| `rambachan_more_2023` | A more credible approach to parallel trends (2023) | 1 | OK | 0 VÁLIDO; 1 AUSENTE | NÃO | AUSENTE | Add the full reference. |
| `chandar_tracking_2025` | Tracking employment changes in AI-exposed jobs (2025) | 1 | OK | 1 VÁLIDO; 0 AUSENTE | SIM | OK | No correction identified. |
| `aldasoro_ai_2026` | AI adoption, productivity and employment: Evidence from european firms (2026) | 1 | OK | 0 VÁLIDO; 1 AUSENTE | SIM | CORRIGIR | Bold the main title only and add EIB Working Paper no. 2026/02. |

## Priority correction queue

### 1. Correct three visible in-text citation constructs

1. **CIT-025 — §4.1:** replace `(Brynjolfsson, Chandar e Chen, 2025, p. 15)` with `(Brynjolfsson; Chandar; Chen, 2025, p. 15)`.
2. **CIT-027 to CIT-030 — §4.1:** replace `(Goodman-Bacon, 2021; Callaway e Sant'Anna, 2021; Sun e Abraham, 2021; de Chaisemartin e D'Haultfœuille, 2020)` with `(Callaway; Sant’Anna, 2021; de Chaisemartin; D’Haultfœuille, 2020; Goodman-Bacon, 2021; Sun; Abraham, 2021)`.
3. **CIT-033 — §4.3:** replace `Silva e Tenreyro (2006)` with `Santos Silva e Tenreyro (2006)`.

The second correction uses semicolons between coauthors and places the four works in alphabetical order. Apostrophes were typographically normalized in the recommended rendering.

### 2. Add nine cited works to the Notion reference list

| Citation key | Work | Required action |
|---|---|---|
| `goodman_bacon_difference_2021` | Difference-in-differences with variation in treatment timing (2021) | Add the ABNT entry; supply/confirm an access date if the online version is cited. |
| `callaway_difference_2021` | Difference-in-differences with multiple time periods (2021) | Add the ABNT entry generated from the canonical `.bib` record. |
| `sun_estimating_2021` | Estimating dynamic treatment effects in event studies with heterogeneous treatment effects (2021) | Add the ABNT entry generated from the canonical `.bib` record. |
| `de_chaisemartin_two-way_2020` | Two-way fixed effects estimators with heterogeneous treatment effects (2020) | Add the ABNT entry generated from the canonical `.bib` record. |
| `santos_silva_log_2006` | The log of gravity (2006) | Add the ABNT entry; supply/confirm an access date if the online version is cited. |
| `chen_logs_2024` | Logs with zeros? Some problems and solutions (2024) | Add the ABNT entry generated from the canonical `.bib` record. |
| `benjamini_controlling_1995` | Controlling the false discovery rate: A practical and powerful approach to multiple testing (1995) | Add the ABNT entry generated from the canonical `.bib` record. |
| `teutloff_winners_2025` | Winners and losers of generative AI: Early evidence of shifts in freelancer demand (2025) | Add the ABNT entry generated from the canonical `.bib` record. |
| `rambachan_more_2023` | A more credible approach to parallel trends (2023) | Add the ABNT entry generated from the canonical `.bib` record. |

The first eight entries above are the newly added methodological sources. `teutloff_winners_2025` was already present in `library.bib` but is also missing from the rendered Notion reference list.

### 3. Normalize twelve existing rendered references

FGV's manual requires consistent typographic emphasis and states that bold applies to the main title, not the subtitle. The current list frequently bolds the complete title and subtitle.

| Citation key | Required reference correction |
|---|---|
| `bick_rapid_2024` | Update to the canonical 2026 journal publication, or explicitly label the retained 2024 preliminary working paper and include no. 2024-027. |
| `eloundou_gpts_2023` | Bold only “GPTs are GPTs”; leave the subtitle unbolded. |
| `brynjolfsson_canaries_2025` | Bold only “Canaries in the coal mine?”; leave the subtitle unbolded. |
| `hosseini_maasoum_generative_2025` | Bold only the main title; leave the subtitle unbolded. |
| `klein_teeselink_generative_2025` | Bold only the main title; leave the subtitle unbolded. |
| `gmyrek_generative_2025` | Bold only the main title; add ILO Working Paper no. 140. |
| `agarwal_combining_2023` | Bold only the main title; add NBER Working Paper no. 31422. |
| `benitez_mirror_2024` | Bold only the main title; add IDB-WP-1624. |
| `appel_anthropic_2026` | Bold only “Anthropic Economic Index report”; leave “Economic primitives” unbolded. |
| `osorio_o_2003` | Add Texto para Discussão no. 996. |
| `humlum_still_2025` | Bold only the main title; add NBER Working Paper no. 33777. |
| `aldasoro_ai_2026` | Bold only the main title; add EIB Working Paper no. 2026/02. |

The three rendered references currently classified as `OK` are `autor_skill_2003`, `brasil_decreto_12342_2024`, and `chandar_tracking_2025`.

### 4. Preserve the link layer as optional metadata

Ten unique destinations are used by the 31 linked occurrences. All ten resolved to the intended work. Five returned HTTP 200 directly. The OUP, IDB, and three SSRN destinations rejected an automated request with anti-bot HTTP 403 responses, but their official/search records resolved to the intended publications; they are therefore classified as `VÁLIDO`, not `QUEBRADO`.

Adding links to the 27 unlinked occurrences may improve navigation, but it should be handled separately from ABNT compliance. Exact-page deep links should wait until page-level evidence has been verified against the consulted PDF version.

## Methodological bibliography audit

The eight methodological records passed essential-metadata verification. The review verdict was `pass_with_normalization`:

- **Clean:** `de_chaisemartin_two-way_2020`, `santos_silva_log_2006`, `benjamini_controlling_1995`, and `rambachan_more_2023`.
- **Normalization only:** sentence-case title normalization for Goodman-Bacon, Callaway–Sant’Anna, and Sun–Abraham; removal of a corrupted optional abstract from Chen–Roth.
- **No mixed-paper metadata** was found, and all eight DOI/title/author/year combinations were verified.
- `references/library.bib` was not edited. The normalized `corrected.bib` inside the audit run is a review-only artifact.

Six local methodological PDFs are earlier versions of the same research rather than the final published versions: Goodman-Bacon, Callaway–Sant’Anna, Sun–Abraham, de Chaisemartin–D’Haultfœuille, Santos Silva–Tenreyro, and Chen–Roth. Their pagination can differ from the canonical publication. Before the page-level claim audit, either replace those PDFs with the published versions or record explicitly which version supplies each page locator.

Goodman-Bacon and Santos Silva–Tenreyro also need a confirmed access date if their online versions are used to render an ABNT reference with `Disponível em` and `Acesso em`.

## Existing page/localizer queue

Only four formal citation occurrences currently contain a page or note locator:

| Occurrence | Location | Citation key | Locator | Portable PDF |
|---|---|---|---|---|
| CIT-025 | 4.1 Abordagem de diferenças em diferenças, paragraph 1 | `brynjolfsson_canaries_2025` | p. 15 | `pdfs/brynjolfsson_canaries_2025.pdf` |
| CIT-031 | 4.1 Abordagem de diferenças em diferenças, paragraph 7 | `humlum_still_2025` | p. 12, nota 8 | `pdfs/humlum_still_2025.pdf` |
| CIT-032 | 4.2 Construção do painel ocupação-mês com CAGED e crosswalk CBO → OIT, paragraph 5 | `klein_teeselink_generative_2025` | p. 11 | `pdfs/klein_teeselink_generative_2025.pdf` |
| CIT-038 | 4.5 Validações e falsificações, paragraph 3 | `teutloff_winners_2025` | p. 12 | `pdfs/teutloff_winners_2025.pdf` |

These four rows are ready for the next-stage page extraction, subject to confirming that each locator matches the stored PDF version.

## Method-name mentions

The exact expression **“Benjamini-Hochberg”** appears 16 additional times as a procedure name, table-note convention, or multiplicity label. These are not counted as separate formal source citations. The dissertation contains one full formal citation to `benjamini_controlling_1995` in §4.4.

| Section | Method-name mentions |
|---|---:|
| 5.2.1 Efeitos por Sexo | 1 |
| 5.2.2 Efeitos por raça/cor | 1 |
| 5.2.3 Efeitos por faixa etária | 1 |
| 5.2.4 Efeitos por nível de escolaridade | 1 |
| 5.2.5 Efeitos por faixa salarial ocupacional | 1 |
| 5.2.6 Síntese das heterogeneidades demográficas | 2 |
| 5.4.1 Estoque de vínculos formais na RAIS | 1 |
| 5.4.2 Deslocamento para a informalidade na PNAD Contínua | 1 |
| 6.1 O que os dados mostram | 1 |
| A.2 Sexo | 1 |
| A.3 Raça/cor | 1 |
| A.4 Idade | 2 |
| A.5 Escolaridade | 1 |
| A.6 Renda ocupacional pré-tratamento | 1 |

## Reference-list reconciliation

- **Cited but absent from Notion references:** 9 works.
- **Present in Notion references but not cited:** 0 works.
- **Formal citations without a `.bib` record:** 0 occurrences.
- **Ambiguous citation-to-key matches:** 0 occurrences.
- **`.bib` records not cited in the current dissertation:** 20 records.

The following uncited records are informational only and must not be added automatically to the final dissertation bibliography:

- `acemoglu_automation_2019`
- `acemoglu_culture_2025`
- `acemoglu_learning_2024`
- `acemoglu_race_2018`
- `acemoglu_robots_2020`
- `acemoglu_skills_2011`
- `adamczyk_skills_2024`
- `autor_applying_2024`
- `autor_does_2007`
- `autor_places_2025`
- `autor_polarization_2006`
- `autor_putting_2013`
- `autor_skills_2014`
- `autor_work_2019`
- `brynjolfsson_generative_2024`
- `dellacqua_navigating_2023`
- `felten_occupational_2021`
- `goos_lousy_2007`
- `hui_short-term_2024`
- `stanford_institute_for_human-centered_artificial_intelligence_ai_2026`

## Acceptance checks

- The TSV has one header plus 58 occurrence rows.
- Every row contains all four requested status dimensions.
- The occurrence total reconciles with the 24-work consolidation.
- Repeated works were assessed occurrence by occurrence.
- Narrative, parenthetical, linked, unlinked, note, legend, and table-note contexts were scanned.
- Existing links were classified individually and reconciled to ten unique destinations.
- The eight methodological records received a separate metadata review.
- The final Notion fetch matched the frozen semantic snapshot.
- No content was changed in Notion, Zotero, or `references/library.bib`.

## Scope boundary and next step

This report establishes **bibliographic correspondence and formatting status**. It does not yet establish that the cited article supports the exact claim, nor does it extract the relevant PDF pages.

After author review, the next step is to apply the approved in-text and reference-list corrections. Only then should the claim-to-source audit begin, using the exact stored PDF version, verified page locators, and page-level/deep-link artifacts.

