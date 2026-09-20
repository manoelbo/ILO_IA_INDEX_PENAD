# Post-edit claim inventory extraction

You are reconstructing the claim inventory for a Brazilian master's dissertation.
This is an extraction task, not a fact-checking task.

## Runtime and scope

- You must operate as `gpt-5.6-sol` with reasoning effort `max`.
- Read only `source_snapshot/occurrence_packets.json` and, when needed to confirm a title, `source_manifest.tsv`.
- Do not read any older audit, judgment, result, evidence, report, change queue, or prior inventory.
- Do not open PDFs and do not search the web.
- Do not edit the Notion page, Zotero, BibTeX, or any source file.

## Output

Create `inventory_extraction_candidate.tsv` with these exact tab-separated columns:

`occurrence_id`, `context_id`, `document_line`, `section`, `paragraph`, `citation_key`, `work`, `claim_type`, `affirmation_pt`, `source_excerpt`, `extraction_note`

Use UTF-8, a single header row, literal tab delimiters, and one physical line per record. Replace any line breaks inside `source_excerpt` with a single space.

## Unit and attribution rules

Each output row is one atomic assertion attributed to one formal citation occurrence.

1. For every occurrence, extract every independently verifiable proposition in the sentence containing that occurrence.
2. Include an immediately following sentence only when it contains explicit anaphora such as “essa evidência”, “esse resultado”, “essa combinação”, or an equally unambiguous reference to the cited finding. Mark such a proposition `AUTHOR_INFERENCE` when it is the dissertation author's inference rather than a result stated by the source.
3. Preserve qualifiers exactly in meaning: population, country, period, sample, direction, magnitude, method, uncertainty, modality, and causal limitations.
4. Write `affirmation_pt` as a self-contained, concise proposition in Brazilian Portuguese. Do not strengthen or repair the dissertation's claim.
5. Use only `DIRECT` or `AUTHOR_INFERENCE` in `claim_type`.
6. Copy the occurrence's full `source_context` verbatim into `source_excerpt`, replacing embedded newlines with spaces only.
7. In a parenthetical group supporting the same sentence, repeat every atomic proposition for every cited source occurrence in that group.
8. In a paragraph with separate narrative citations, attach source-specific clauses only to the source named by that clause. A preceding synthesis sentence may be repeated across sources only when the paragraph clearly presents the subsequent cited works as the evidence for that synthesis.
9. For a table citation, use the complete table row supplied in `source_context` and atomize factual cells attributable to that cited work.
10. Preserve repeated claims in different occurrences. Do not merge across locations.
11. Do not add uncited propositions merely because they appear elsewhere in the paragraph. Do not extract claims from the reference list.
12. Every occurrence must have at least one output row. If an occurrence genuinely contains no verifiable proposition, emit one row whose `affirmation_pt` is `NO_VERIFIABLE_PROPOSITION` and explain why in `extraction_note`.
13. Do not duplicate the same normalized `affirmation_pt` within the same occurrence.

## Calibration

`CIT-REV-001` must yield exactly four rows:

1. Estima-se que 32,1% dos trabalhadores dos Estados Unidos já integravam ferramentas de IA às suas rotinas até o final de 2024. (`DIRECT`)
2. O ritmo de adoção de ferramentas de IA nos Estados Unidos era comparável ao do computador pessoal na década de 1980. (`DIRECT`)
3. A difusão das ferramentas de IA nos Estados Unidos era superior, em termos populacionais, à da internet. (`DIRECT`)
4. A combinação do alcance ocupacional com a velocidade de difusão justifica tratar essa geração de inteligência artificial como um problema econômico, e não apenas tecnológico. (`AUTHOR_INFERENCE`)

After writing the TSV, validate that all 61 occurrence IDs appear, all 22 citation keys are covered, all metadata copied from the packets is exact, and no duplicate `(occurrence_id, normalized affirmation_pt)` exists. In your final message, report only the output path, row count, unique claim-text count, occurrence count, key count, and any `NO_VERIFIABLE_PROPOSITION` occurrence IDs.
