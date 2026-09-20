# Isolated current claim audit: ROW-CUR-0079

You are the sole semantic auditor for exactly one claim-source-occurrence row.

Your working directory is the current run: `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. Do not search for a run
directory and do not enter `20260801T155350Z` or any other historical run. All
relative artifact paths below resolve from `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. The project root is
`/Users/manebrasil/Documents/Projects/Dissetação Mestrado`.

## Runtime gate

- Required model: `gpt-5.6-sol`
- Required reasoning effort: `max`
- Fallback: prohibited
- Worker task name: `current_claim_row_0079`

If the effective runtime differs, stop without writing artifacts.

## Blindness and scope

Audit only the row below. Do not read or list any old run, any Claude path, `results/`, other prompts/candidates, the consolidated TSV, reports, QC artifacts, or another row's evidence. Do not use a prior verdict or evidence. Read `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/audit_protocol.txt` and `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/claim_result.schema.json` completely. Do not use filesystem search to find alternatives; every authorized path is explicit below.

Read `/Users/manebrasil/.agents/skills/split-pdf/SKILL.md` completely before source content. Use the page-text/search index only for localization. Never load the complete PDF into context. Open no more than three four-page splits per batch and document each batch. Visually inspect pages containing tables, figures, formulas, footnotes, unusual layout, or questionable OCR. Extract exactly the declared physical pages to `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0079.pdf` using `python3` (not `python`) with `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/scripts/extract_evidence.py` and `PYTHONPATH=/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260801T155350Z/source_build/python_deps`. The final controller, not the worker, performs authoritative JSON Schema validation.

Authorized source reads:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/benitez_mirror_2024/source_build_manifest.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/benitez_mirror_2024/page_index.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/benitez_mirror_2024/search_index.tsv`
- four-page splits listed in `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/benitez_mirror_2024/source_build_manifest.json`
- original `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/pdfs/benitez_mirror_2024.pdf` only for selected-page extraction/rendering
- the exact BibLaTeX entry reproduced below

Authorized writes only:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/candidates/ROW-CUR-0079.candidate.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0079.pdf`
- optional visual renders under `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/renders/ROW-CUR-0079/`

## Row

```json
{
  "row_id": "ROW-CUR-0079",
  "claim_id": "CLM-CUR-069",
  "occurrence_id": "CIT-CUR-016",
  "citation_key": "benitez_mirror_2024",
  "work": "Mirror, Mirror on the Wall: Which Jobs Will AI Replace After All?: A New Index of Occupational Exposure",
  "claim_type": "DIRECT",
  "affirmation_pt": "O GENOE é apresentado como sensível a barreiras sociais e institucionais.",
  "source_excerpt": "GENOE (Benítez; Parrado, 2024) | O*NET / SOC (EUA) | LLM com contexto completo da ocupação (avaliação holística) | Sensível a barreiras sociais e institucionais | Avaliações inteiramente sintéticas, sem validação direta por especialistas — a aferição é indireta, pela replicação do AIOE; base americana | Comparação",
  "section": "2.3 Índices de exposição à IA na literatura",
  "paragraph": "6"
}
```

Technical identity:
- row_id: `ROW-CUR-0079`
- claim_row_sha256: `28b4bcad7a0570c335d1dc66d3e577a6e6fc118f6c8289c8ebbb0414a09cfc01`
- bibliography_entry_sha256: `68d96977aa93198589bc5631fb56148252053b8478d1bab3e5d10127460d2543`
- source_sha256: `8847920fa160282c8ba5b5f456f35b24669a7e19dd8a655e2a801b265efb5fda`
- schema_sha256: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- reconciliation_status: `REAUDITED_TEXT_CHANGED`

Compute `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/prompts/ROW-CUR-0079.md`'s SHA-256 after reading it and store it as `worker_prompt_sha256`.

## Exact BibLaTeX entry

```bibtex
@report{benitez_mirror_2024,
	title = {Mirror, Mirror on the Wall: Which Jobs Will {AI} Replace After All?: A New Index of Occupational Exposure},
	url = {https://publications.iadb.org/en/mirror-mirror-wall-which-jobs-will-ai-replace-after-all-new-index-occupational-exposure},
	doi = {10.18235/0013125},
	shorttitle = {Mirror, Mirror on the Wall},
	abstract = {This paper introduces the {AI} Generated Index of Occupational Exposure ({GENOE}), a novel measure quantifying the potential impact of artificial intelligence on occupations and their associated tasks. Our methodology employs synthetic {AI} surveys, leveraging large language models to conduct expert-like assessments. This approach allows for a more comprehensive evaluation of job replacement likelihood, minimizing human bias and reducing assumptions about the mechanisms through which {AI} innovations could replace job tasks and skills. The index not only considers task automation, but also contextual factors such as social and ethical considerations and regulatory constraints that may affect the likelihood of replacement. Our findings indicate that the average likelihood of job replacement is estimated at 0.28 in the next year, increasing to 0.38 and 0.44 over the next five and ten years, respectively. To validate our methodology, we successfully replicate other measures of occupational exposure that rely on human expert assessments, substituting these with {AI}-based evaluations. The {GENOE} index provides valuable insights for policymakers, employers, and workers, offering a data-driven foundation for strategic workforce planning and adaptation in the face of rapid technological change.},
	institution = {Inter-American Development Bank},
	author = {Benítez, Miguel and Parrado, Eric},
	urldate = {2026-07-25},
	date = {2024-08-27},
	langid = {english},
	file = {PDF:pdfs/benitez_mirror_2024.pdf:application/pdf},
}
```

## Judgment requirements

Use only `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, or `NOT_VERIFIABLE`. Apply the balanced calibration in `audit_protocol.txt`. Every non-SUPPORTED verdict requires at least one complete structured issue. An AUTHOR_INFERENCE must separately assess factual premises, reasonableness, and whether the source explicitly states the inference.

Record printed pages and one-based physical PDF indices separately. `pages` must equal `printed_pages` and may never be blank. `N/A` requires a structured justification. Choose a deliberately short verbatim evidence anchor of no more than 8 whitespace-delimited words (stricter than the 12-word schema ceiling) and count it before writing. Search coverage must list every search term, page range, split, and visual check actually used. Do not use abstracts or outside sources as substantive evidence.

Work efficiently without reducing rigor: once unambiguous evidence and source identity are established, do not open merely confirmatory extra pages. Expand the search only when the first bounded batch leaves a material component unresolved or when a non-pass verdict requires broader documented coverage.

After writing the candidate and evidence, perform only one quick local check of the declared hashes and evidence-page count, then finish immediately. Do not install packages, troubleshoot `jsonschema`, or repeat controller-level validation; the controller validates the full schema and all identity fields after your process exits.

Write one JSON object conforming exactly to `claim_result.schema.json` at `source_build/candidates/ROW-CUR-0079.candidate.json`. Use:
- `schema_version`: `1.0.0`
- `row_id`: `ROW-CUR-0079`
- `claim_id`: `CLM-CUR-069`
- `occurrence_id`: `CIT-CUR-016`
- `worker_task_name`: `current_claim_row_0079`
- `auditor_model`: `gpt-5.6-sol`
- `reasoning_effort`: `max`
- `claim_row_sha256`: `28b4bcad7a0570c335d1dc66d3e577a6e6fc118f6c8289c8ebbb0414a09cfc01`
- `bibliography_entry_sha256`: `68d96977aa93198589bc5631fb56148252053b8478d1bab3e5d10127460d2543`
- `source_sha256`: `8847920fa160282c8ba5b5f456f35b24669a7e19dd8a655e2a801b265efb5fda`
- `schema_sha256`: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- `evidence_path`: `evidence_pages/ROW-CUR-0079.pdf`
- `audit_status`: `COMPLETED`

For DIRECT, set `author_inference_assessment` to null. For AUTHOR_INFERENCE, fill the object. Use RFC 3339 UTC. Validate identity, hashes, evidence existence, page bounds, evidence-page count, and schema before finishing. Your final chat response must only say that the candidate is ready; do not reveal the verdict there.
