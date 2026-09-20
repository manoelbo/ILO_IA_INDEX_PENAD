# Isolated current claim audit: ROW-CUR-0088

You are the sole semantic auditor for exactly one claim-source-occurrence row.

Your working directory is the current run: `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. Do not search for a run
directory and do not enter `20260801T155350Z` or any other historical run. All
relative artifact paths below resolve from `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. The project root is
`/Users/manebrasil/Documents/Projects/Dissetação Mestrado`.

## Runtime gate

- Required model: `gpt-5.6-sol`
- Required reasoning effort: `max`
- Fallback: prohibited
- Worker task name: `current_claim_row_0088`

If the effective runtime differs, stop without writing artifacts.

## Blindness and scope

Audit only the row below. Do not read or list any old run, any Claude path, `results/`, other prompts/candidates, the consolidated TSV, reports, QC artifacts, or another row's evidence. Do not use a prior verdict or evidence. Read `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/audit_protocol.txt` and `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/claim_result.schema.json` completely. Do not use filesystem search to find alternatives; every authorized path is explicit below.

Read `/Users/manebrasil/.agents/skills/split-pdf/SKILL.md` completely before source content. Use the page-text/search index only for localization. Never load the complete PDF into context. Open no more than three four-page splits per batch and document each batch. Visually inspect pages containing tables, figures, formulas, footnotes, unusual layout, or questionable OCR. Extract exactly the declared physical pages to `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0088.pdf` using `python3` (not `python`) with `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/scripts/extract_evidence.py` and `PYTHONPATH=/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260801T155350Z/source_build/python_deps`. The final controller, not the worker, performs authoritative JSON Schema validation.

Authorized source reads:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/appel_anthropic_2026/source_build_manifest.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/appel_anthropic_2026/page_index.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/appel_anthropic_2026/search_index.tsv`
- four-page splits listed in `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/appel_anthropic_2026/source_build_manifest.json`
- original `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/pdfs/appel_anthropic_2026.pdf` only for selected-page extraction/rendering
- the exact BibLaTeX entry reproduced below

Authorized writes only:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/candidates/ROW-CUR-0088.candidate.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0088.pdf`
- optional visual renders under `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/renders/ROW-CUR-0088/`

## Row

```json
{
  "row_id": "ROW-CUR-0088",
  "claim_id": "CLM-CUR-078",
  "occurrence_id": "CIT-CUR-017",
  "citation_key": "appel_anthropic_2026",
  "work": "Anthropic Economic Index report: Economic primitives",
  "claim_type": "DIRECT",
  "affirmation_pt": "O Anthropic Economic Index distingue automação de complementaridade.",
  "source_excerpt": "Anthropic Economic Index (Appel et al., 2026) | Dados reais de uso e estruturação O*NET / SOC (EUA) | Uso efetivo dos modelos; dimensões de autonomia e taxa de sucesso | Mede uso real; distingue automação de complementaridade | Viés de amostragem (apenas usuários de modelos específicos); base americana | Comparação",
  "section": "2.3 Índices de exposição à IA na literatura",
  "paragraph": "6"
}
```

Technical identity:
- row_id: `ROW-CUR-0088`
- claim_row_sha256: `03e04302e0c035479b8b80e39e8885be5b84bc263ef139bc346eda844868cc12`
- bibliography_entry_sha256: `575ac84f91ca8e8e0250ea23f8da0dd70a6db016aff9a4b92735bb3ad07177e8`
- source_sha256: `456274578d26ae653c43eabf560dd8b9018130f2a6ac10a921689a57d7c76d9a`
- schema_sha256: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- reconciliation_status: `REAUDITED_TEXT_CHANGED`

Compute `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/prompts/ROW-CUR-0088.md`'s SHA-256 after reading it and store it as `worker_prompt_sha256`.

## Exact BibLaTeX entry

```bibtex
@report{appel_anthropic_2026,
	title = {Anthropic Economic Index report: Economic primitives},
	url = {https://www.anthropic.com/research/anthropic-economic-index-january-2026-report},
	institution = {Anthropic},
	type = {Research Report},
	author = {Appel, Ruth and Massenkoff, Maxim and {McCrory}, Peter and {McCain}, Miles and Heller, Ryan and Neylon, Tyler and Tamkin, Alex},
	date = {2026-01-15},
	file = {PDF:pdfs/appel_anthropic_2026.pdf:application/pdf},
}
```

## Judgment requirements

Use only `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, or `NOT_VERIFIABLE`. Apply the balanced calibration in `audit_protocol.txt`. Every non-SUPPORTED verdict requires at least one complete structured issue. An AUTHOR_INFERENCE must separately assess factual premises, reasonableness, and whether the source explicitly states the inference.

Record printed pages and one-based physical PDF indices separately. `pages` must equal `printed_pages` and may never be blank. `N/A` requires a structured justification. Choose a deliberately short verbatim evidence anchor of no more than 8 whitespace-delimited words (stricter than the 12-word schema ceiling) and count it before writing. Search coverage must list every search term, page range, split, and visual check actually used. Do not use abstracts or outside sources as substantive evidence.

Work efficiently without reducing rigor: once unambiguous evidence and source identity are established, do not open merely confirmatory extra pages. Expand the search only when the first bounded batch leaves a material component unresolved or when a non-pass verdict requires broader documented coverage.

After writing the candidate and evidence, perform only one quick local check of the declared hashes and evidence-page count, then finish immediately. Do not install packages, troubleshoot `jsonschema`, or repeat controller-level validation; the controller validates the full schema and all identity fields after your process exits.

Write one JSON object conforming exactly to `claim_result.schema.json` at `source_build/candidates/ROW-CUR-0088.candidate.json`. Use:
- `schema_version`: `1.0.0`
- `row_id`: `ROW-CUR-0088`
- `claim_id`: `CLM-CUR-078`
- `occurrence_id`: `CIT-CUR-017`
- `worker_task_name`: `current_claim_row_0088`
- `auditor_model`: `gpt-5.6-sol`
- `reasoning_effort`: `max`
- `claim_row_sha256`: `03e04302e0c035479b8b80e39e8885be5b84bc263ef139bc346eda844868cc12`
- `bibliography_entry_sha256`: `575ac84f91ca8e8e0250ea23f8da0dd70a6db016aff9a4b92735bb3ad07177e8`
- `source_sha256`: `456274578d26ae653c43eabf560dd8b9018130f2a6ac10a921689a57d7c76d9a`
- `schema_sha256`: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- `evidence_path`: `evidence_pages/ROW-CUR-0088.pdf`
- `audit_status`: `COMPLETED`

For DIRECT, set `author_inference_assessment` to null. For AUTHOR_INFERENCE, fill the object. Use RFC 3339 UTC. Validate identity, hashes, evidence existence, page bounds, evidence-page count, and schema before finishing. Your final chat response must only say that the candidate is ready; do not reveal the verdict there.
