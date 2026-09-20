# Isolated current claim audit: ROW-CUR-0106

You are the sole semantic auditor for exactly one claim-source-occurrence row.

Your working directory is the current run: `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. Do not search for a run
directory and do not enter `20260801T155350Z` or any other historical run. All
relative artifact paths below resolve from `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. The project root is
`/Users/manebrasil/Documents/Projects/Dissetação Mestrado`.

## Runtime gate

- Required model: `gpt-5.6-sol`
- Required reasoning effort: `max`
- Fallback: prohibited
- Worker task name: `current_claim_row_0106`

If the effective runtime differs, stop without writing artifacts.

## Blindness and scope

Audit only the row below. Do not read or list any old run, any Claude path, `results/`, other prompts/candidates, the consolidated TSV, reports, QC artifacts, or another row's evidence. Do not use a prior verdict or evidence. Read `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/audit_protocol.txt` and `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/claim_result.schema.json` completely. Do not use filesystem search to find alternatives; every authorized path is explicit below.

This is an official legal HTML source. Read only `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/brasil_decreto_12342_2024/official_snapshot.html` and `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/brasil_decreto_12342_2024/search_text.txt` as substantive evidence. Use exact article/paragraph/item locators, set `pdf_page_indices` to `N/A`, set pages/printed_pages to a legal locator ending in `(HTML sem paginação)`, and write a narrow UTF-8 evidence fragment to `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0106.html`.

Authorized source reads:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/brasil_decreto_12342_2024/source_build_manifest.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/brasil_decreto_12342_2024/official_snapshot.html`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/brasil_decreto_12342_2024/search_text.txt`
- the exact BibLaTeX entry reproduced below

Authorized writes only:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/candidates/ROW-CUR-0106.candidate.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0106.html`
- optional visual renders under `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/renders/ROW-CUR-0106/`

## Row

```json
{
  "row_id": "ROW-CUR-0106",
  "claim_id": "CLM-CUR-096",
  "occurrence_id": "CIT-CUR-022",
  "citation_key": "brasil_decreto_12342_2024",
  "work": "Decreto nº 12.342, de 30 de dezembro de 2024",
  "claim_type": "DIRECT",
  "affirmation_pt": "O salário mínimo adotado como referência é de R$ 1.518.",
  "source_excerpt": "R$ 1.518 (Brasil, 2024)",
  "section": "3.1 Base analítica e amostra",
  "paragraph": "4"
}
```

Technical identity:
- row_id: `ROW-CUR-0106`
- claim_row_sha256: `3a901daafac9ec8f00fdf7782849aa5cc8aec81d43393da1cd568644030a1756`
- bibliography_entry_sha256: `2915482671aeeae723c610507e999427ab40483283394802c8d2365317e29279`
- source_sha256: `fbca3b79c71a174e6f2ad1c66bd2b2fa03a966a4737917191f5450e443cd52e4`
- schema_sha256: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- reconciliation_status: `REAUDITED_TEXT_CHANGED`

Compute `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/prompts/ROW-CUR-0106.md`'s SHA-256 after reading it and store it as `worker_prompt_sha256`.

## Exact BibLaTeX entry

```bibtex
@legislation{brasil_decreto_12342_2024,
	title = {Decreto nº 12.342, de 30 de dezembro de 2024},
	url = {https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12342.htm},
	shorttitle = {Decreto nº 12.342/2024},
	author = {{Brasil}},
	urldate = {2026-07-25},
	date = {2024-12-30},
	langid = {brazil},
}
```

## Judgment requirements

Use only `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, or `NOT_VERIFIABLE`. Apply the balanced calibration in `audit_protocol.txt`. Every non-SUPPORTED verdict requires at least one complete structured issue. An AUTHOR_INFERENCE must separately assess factual premises, reasonableness, and whether the source explicitly states the inference.

Record printed pages and one-based physical PDF indices separately. `pages` must equal `printed_pages` and may never be blank. `N/A` requires a structured justification. Choose a deliberately short verbatim evidence anchor of no more than 8 whitespace-delimited words (stricter than the 12-word schema ceiling) and count it before writing. Search coverage must list every search term, page range, split, and visual check actually used. Do not use abstracts or outside sources as substantive evidence.

Work efficiently without reducing rigor: once unambiguous evidence and source identity are established, do not open merely confirmatory extra pages. Expand the search only when the first bounded batch leaves a material component unresolved or when a non-pass verdict requires broader documented coverage.

After writing the candidate and evidence, perform only one quick local check of the declared hashes and evidence-page count, then finish immediately. Do not install packages, troubleshoot `jsonschema`, or repeat controller-level validation; the controller validates the full schema and all identity fields after your process exits.

Write one JSON object conforming exactly to `claim_result.schema.json` at `source_build/candidates/ROW-CUR-0106.candidate.json`. Use:
- `schema_version`: `1.0.0`
- `row_id`: `ROW-CUR-0106`
- `claim_id`: `CLM-CUR-096`
- `occurrence_id`: `CIT-CUR-022`
- `worker_task_name`: `current_claim_row_0106`
- `auditor_model`: `gpt-5.6-sol`
- `reasoning_effort`: `max`
- `claim_row_sha256`: `3a901daafac9ec8f00fdf7782849aa5cc8aec81d43393da1cd568644030a1756`
- `bibliography_entry_sha256`: `2915482671aeeae723c610507e999427ab40483283394802c8d2365317e29279`
- `source_sha256`: `fbca3b79c71a174e6f2ad1c66bd2b2fa03a966a4737917191f5450e443cd52e4`
- `schema_sha256`: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- `evidence_path`: `evidence_pages/ROW-CUR-0106.html`
- `audit_status`: `COMPLETED`

For DIRECT, set `author_inference_assessment` to null. For AUTHOR_INFERENCE, fill the object. Use RFC 3339 UTC. Validate identity, hashes, evidence existence, page bounds, evidence-page count, and schema before finishing. Your final chat response must only say that the candidate is ready; do not reveal the verdict there.
