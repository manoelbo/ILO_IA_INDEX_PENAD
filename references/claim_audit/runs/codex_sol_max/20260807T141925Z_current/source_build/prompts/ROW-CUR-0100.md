# Isolated current claim audit: ROW-CUR-0100

You are the sole semantic auditor for exactly one claim-source-occurrence row.

Your working directory is the current run: `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. Do not search for a run
directory and do not enter `20260801T155350Z` or any other historical run. All
relative artifact paths below resolve from `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. The project root is
`/Users/manebrasil/Documents/Projects/Dissetação Mestrado`.

## Runtime gate

- Required model: `gpt-5.6-sol`
- Required reasoning effort: `max`
- Fallback: prohibited
- Worker task name: `current_claim_row_0100`

If the effective runtime differs, stop without writing artifacts.

## Blindness and scope

Audit only the row below. Do not read or list any old run, any Claude path, `results/`, other prompts/candidates, the consolidated TSV, reports, QC artifacts, or another row's evidence. Do not use a prior verdict or evidence. Read `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/audit_protocol.txt` and `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/claim_result.schema.json` completely. Do not use filesystem search to find alternatives; every authorized path is explicit below.

Read `/Users/manebrasil/.agents/skills/split-pdf/SKILL.md` completely before source content. Use the page-text/search index only for localization. Never load the complete PDF into context. Open no more than three four-page splits per batch and document each batch. Visually inspect pages containing tables, figures, formulas, footnotes, unusual layout, or questionable OCR. Extract exactly the declared physical pages to `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0100.pdf` using `python3` (not `python`) with `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/scripts/extract_evidence.py` and `PYTHONPATH=/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260801T155350Z/source_build/python_deps`. The final controller, not the worker, performs authoritative JSON Schema validation.

Authorized source reads:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/gmyrek_generative_2025/source_build_manifest.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/gmyrek_generative_2025/page_index.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/gmyrek_generative_2025/search_index.tsv`
- four-page splits listed in `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/gmyrek_generative_2025/source_build_manifest.json`
- original `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/pdfs/gmyrek_generative_2025.pdf` only for selected-page extraction/rendering
- the exact BibLaTeX entry reproduced below

Authorized writes only:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/candidates/ROW-CUR-0100.candidate.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0100.pdf`
- optional visual renders under `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/renders/ROW-CUR-0100/`

## Row

```json
{
  "row_id": "ROW-CUR-0100",
  "claim_id": "CLM-CUR-090",
  "occurrence_id": "CIT-CUR-018",
  "citation_key": "gmyrek_generative_2025",
  "work": "Generative AI and jobs: A refined global index of occupational exposure",
  "claim_type": "AUTHOR_INFERENCE",
  "affirmation_pt": "O ILO Global Index é o índice principal desta dissertação.",
  "source_excerpt": "ILO Global Index (Gmyrek et al., 2025) | ISCO-08 (internacional) | Validação em três camadas (trabalhadores, especialistas e LLMs) escalada por LLM; média e desvio padrão das tarefas | Validação em múltiplas etapas e comparabilidade internacional via ISCO-08 | Índice global; pode não captar especificidades brasileiras; exige crosswalk COD/CBO | Índice principal",
  "section": "2.3 Índices de exposição à IA na literatura",
  "paragraph": "6"
}
```

Technical identity:
- row_id: `ROW-CUR-0100`
- claim_row_sha256: `9313a25eb0e91756f8ca902da67078d4000992192c4f7ef5e4c589f85660b457`
- bibliography_entry_sha256: `0f7243bee9c197dfedbc52fc8e6af5336e9f9ba3152a4ad8a8341ea4521e0daf`
- source_sha256: `9077761c72aabaa3c7ee70999ec5aa46a6afcf943b5fb01baa971f601d363ee9`
- schema_sha256: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- reconciliation_status: `REAUDITED_TEXT_CHANGED`

Compute `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/prompts/ROW-CUR-0100.md`'s SHA-256 after reading it and store it as `worker_prompt_sha256`.

## Exact BibLaTeX entry

```bibtex
@report{gmyrek_generative_2025,
	location = {Geneva},
	title = {Generative {AI} and jobs: A refined global index of occupational exposure},
	rights = {http://creativecommons.org/licenses/by/4.0/},
	isbn = {978-92-2-042184-0},
	url = {https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure},
	doi = {10.54394/HETP0387},
	shorttitle = {Generative {AI} and jobs},
	abstract = {This study updates the {ILO}’s 2023 Global Index of Occupational Exposure to Generative {AI} ({GenAI}), incorporating recent advances in the technology and increasing user familiarity with {GenAI} tools. Using a representative sample from the 29,753 tasks in the Polish occupational classification system and a survey of 1,640 people employed in each 1-digit {ISCO}-08 groups, we collect 52,558 data points regarding perceive potential of automation for 2,861 tasks. We then compare this input with a survey and several rounds of Delphi-style discussions among a smaller group of international experts. Based on this process, we create a repository of knowledge about task automation that goes beyond national specificities and use it to develop an {AI} assistant able to predict scores for tasks in the technical documentation of {ISCO}-08.},
	pages = {72},
	number = {140},
	institution = {International Labour Organization},
	type = {{ILO} Working Paper},
	author = {Gmyrek, Pawel and Berg, Janine and Kamiński, Karol and Konopczyński, Filip and Ładna, Agnieszka and Nafradi, Balint and Rosłaniec, Konrad and Troszyński, Marek},
	urldate = {2026-07-25},
	date = {2025-05-20},
	file = {PDF:pdfs/gmyrek_generative_2025.pdf:application/pdf},
}
```

## Judgment requirements

Use only `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, or `NOT_VERIFIABLE`. Apply the balanced calibration in `audit_protocol.txt`. Every non-SUPPORTED verdict requires at least one complete structured issue. An AUTHOR_INFERENCE must separately assess factual premises, reasonableness, and whether the source explicitly states the inference.

Record printed pages and one-based physical PDF indices separately. `pages` must equal `printed_pages` and may never be blank. `N/A` requires a structured justification. Choose a deliberately short verbatim evidence anchor of no more than 8 whitespace-delimited words (stricter than the 12-word schema ceiling) and count it before writing. Search coverage must list every search term, page range, split, and visual check actually used. Do not use abstracts or outside sources as substantive evidence.

Work efficiently without reducing rigor: once unambiguous evidence and source identity are established, do not open merely confirmatory extra pages. Expand the search only when the first bounded batch leaves a material component unresolved or when a non-pass verdict requires broader documented coverage.

After writing the candidate and evidence, perform only one quick local check of the declared hashes and evidence-page count, then finish immediately. Do not install packages, troubleshoot `jsonschema`, or repeat controller-level validation; the controller validates the full schema and all identity fields after your process exits.

Write one JSON object conforming exactly to `claim_result.schema.json` at `source_build/candidates/ROW-CUR-0100.candidate.json`. Use:
- `schema_version`: `1.0.0`
- `row_id`: `ROW-CUR-0100`
- `claim_id`: `CLM-CUR-090`
- `occurrence_id`: `CIT-CUR-018`
- `worker_task_name`: `current_claim_row_0100`
- `auditor_model`: `gpt-5.6-sol`
- `reasoning_effort`: `max`
- `claim_row_sha256`: `9313a25eb0e91756f8ca902da67078d4000992192c4f7ef5e4c589f85660b457`
- `bibliography_entry_sha256`: `0f7243bee9c197dfedbc52fc8e6af5336e9f9ba3152a4ad8a8341ea4521e0daf`
- `source_sha256`: `9077761c72aabaa3c7ee70999ec5aa46a6afcf943b5fb01baa971f601d363ee9`
- `schema_sha256`: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- `evidence_path`: `evidence_pages/ROW-CUR-0100.pdf`
- `audit_status`: `COMPLETED`

For DIRECT, set `author_inference_assessment` to null. For AUTHOR_INFERENCE, fill the object. Use RFC 3339 UTC. Validate identity, hashes, evidence existence, page bounds, evidence-page count, and schema before finishing. Your final chat response must only say that the candidate is ready; do not reveal the verdict there.
