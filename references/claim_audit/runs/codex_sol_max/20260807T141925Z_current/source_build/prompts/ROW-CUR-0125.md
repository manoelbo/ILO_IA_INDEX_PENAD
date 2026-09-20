# Isolated current claim audit: ROW-CUR-0125

You are the sole semantic auditor for exactly one claim-source-occurrence row.

Your working directory is the current run: `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. Do not search for a run
directory and do not enter `20260801T155350Z` or any other historical run. All
relative artifact paths below resolve from `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current`. The project root is
`/Users/manebrasil/Documents/Projects/Dissetação Mestrado`.

## Runtime gate

- Required model: `gpt-5.6-sol`
- Required reasoning effort: `max`
- Fallback: prohibited
- Worker task name: `current_claim_row_0125`

If the effective runtime differs, stop without writing artifacts.

## Blindness and scope

Audit only the row below. Do not read or list any old run, any Claude path, `results/`, other prompts/candidates, the consolidated TSV, reports, QC artifacts, or another row's evidence. Do not use a prior verdict or evidence. Read `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/audit_protocol.txt` and `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/claim_result.schema.json` completely. Do not use filesystem search to find alternatives; every authorized path is explicit below.

Read `/Users/manebrasil/.agents/skills/split-pdf/SKILL.md` completely before source content. Use the page-text/search index only for localization. Never load the complete PDF into context. Open no more than three four-page splits per batch and document each batch. Visually inspect pages containing tables, figures, formulas, footnotes, unusual layout, or questionable OCR. Extract exactly the declared physical pages to `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0125.pdf` using `python3` (not `python`) with `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/scripts/extract_evidence.py` and `PYTHONPATH=/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260801T155350Z/source_build/python_deps`. The final controller, not the worker, performs authoritative JSON Schema validation.

Authorized source reads:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/de_chaisemartin_two-way_2020/source_build_manifest.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/de_chaisemartin_two-way_2020/page_index.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/de_chaisemartin_two-way_2020/search_index.tsv`
- four-page splits listed in `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/de_chaisemartin_two-way_2020/source_build_manifest.json`
- original `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/pdfs/de_chaisemartin_two-way_2020.pdf` only for selected-page extraction/rendering
- the exact BibLaTeX entry reproduced below

Authorized writes only:
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/candidates/ROW-CUR-0125.candidate.json`
- `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/evidence_pages/ROW-CUR-0125.pdf`
- optional visual renders under `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/renders/ROW-CUR-0125/`

## Row

```json
{
  "row_id": "ROW-CUR-0125",
  "claim_id": "CLM-CUR-112",
  "occurrence_id": "CIT-CUR-032",
  "citation_key": "de_chaisemartin_two-way_2020",
  "work": "Two-Way Fixed Effects Estimators with Heterogeneous Treatment Effects",
  "claim_type": "DIRECT",
  "affirmation_pt": "A literatura recente alerta para problemas em modelos de diferenças em diferenças quando as unidades começam a ser tratadas em datas diferentes.",
  "source_excerpt": "A literatura recente alerta para um problema dos modelos de diferenças em diferenças quando as unidades começam a ser tratadas em datas diferentes (Goodman-Bacon, 2021; Callaway e Sant'Anna, 2021; Sun e Abraham, 2021; de Chaisemartin e D'Haultfœuille, 2020). Esse não é o formato usado aqui. Todas as ocupações expostas passam a ser consideradas tratadas na mesma data, o lançamento do ChatGPT, e as ocupações não expostas permanecem como controle. Portanto, não há comparação entre grupos tratados mais cedo e mais tarde. A principal condição do desenho continua sendo outra: antes do evento, os grupos deveriam apresentar trajetórias paralelas. Os diagnósticos da Seção 5 mostram que essa condição não se sustenta, o que limita a interpretação causal.",
  "section": "4.1 Abordagem de diferenças em diferenças",
  "paragraph": "6"
}
```

Technical identity:
- row_id: `ROW-CUR-0125`
- claim_row_sha256: `8544e2328648d8ddea339569bb15b8e4fddc523bad468d5b51d8095aa6aeface`
- bibliography_entry_sha256: `2cadccb93fac2ce979f3074ee29372ad2092095e9028d0ca5286da979781d4c3`
- source_sha256: `ddc65e7599d8364181fd84d388ec543d57bfa51c2e66d50777af7ebac2aba3c4`
- schema_sha256: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- reconciliation_status: `AUDITED_NEW`

Compute `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/references/claim_audit/runs/codex_sol_max/20260807T141925Z_current/source_build/prompts/ROW-CUR-0125.md`'s SHA-256 after reading it and store it as `worker_prompt_sha256`.

## Exact BibLaTeX entry

```bibtex
@article{de_chaisemartin_two-way_2020,
	title = {Two-Way Fixed Effects Estimators with Heterogeneous Treatment Effects},
	volume = {110},
	issn = {0002-8282},
	url = {https://doi.org/10.1257/aer.20181169},
	doi = {10.1257/aer.20181169},
	abstract = {Linear regressions with period and group ﬁxed eﬀects are widely used to estimate treatment eﬀects. We show that they estimate weighted sums of the average treatment eﬀects ({ATE}) in each group and period, with weights that may be negative. Due to the negative weights, the linear regression coeﬃcient may for instance be negative while all the {ATEs} are positive. We propose another estimator that solves this issue. In the two applications we revisit, it is signiﬁcantly diﬀerent from the linear regression estimator.},
	pages = {2964--2996},
	number = {9},
	journaltitle = {American Economic Review},
	shortjournal = {American Economic Review},
	author = {de Chaisemartin, Clément and D'Haultfœuille, Xavier},
	urldate = {2026-07-28},
	date = {2020},
	langid = {english},
	keywords = {Economics - Econometrics},
	file = {PDF:pdfs/de_chaisemartin_two-way_2020.pdf:application/pdf},
}
```

## Judgment requirements

Use only `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `NOT_FOUND`, or `NOT_VERIFIABLE`. Apply the balanced calibration in `audit_protocol.txt`. Every non-SUPPORTED verdict requires at least one complete structured issue. An AUTHOR_INFERENCE must separately assess factual premises, reasonableness, and whether the source explicitly states the inference.

Record printed pages and one-based physical PDF indices separately. `pages` must equal `printed_pages` and may never be blank. `N/A` requires a structured justification. Choose a deliberately short verbatim evidence anchor of no more than 8 whitespace-delimited words (stricter than the 12-word schema ceiling) and count it before writing. Search coverage must list every search term, page range, split, and visual check actually used. Do not use abstracts or outside sources as substantive evidence.

Work efficiently without reducing rigor: once unambiguous evidence and source identity are established, do not open merely confirmatory extra pages. Expand the search only when the first bounded batch leaves a material component unresolved or when a non-pass verdict requires broader documented coverage.

After writing the candidate and evidence, perform only one quick local check of the declared hashes and evidence-page count, then finish immediately. Do not install packages, troubleshoot `jsonschema`, or repeat controller-level validation; the controller validates the full schema and all identity fields after your process exits.

Write one JSON object conforming exactly to `claim_result.schema.json` at `source_build/candidates/ROW-CUR-0125.candidate.json`. Use:
- `schema_version`: `1.0.0`
- `row_id`: `ROW-CUR-0125`
- `claim_id`: `CLM-CUR-112`
- `occurrence_id`: `CIT-CUR-032`
- `worker_task_name`: `current_claim_row_0125`
- `auditor_model`: `gpt-5.6-sol`
- `reasoning_effort`: `max`
- `claim_row_sha256`: `8544e2328648d8ddea339569bb15b8e4fddc523bad468d5b51d8095aa6aeface`
- `bibliography_entry_sha256`: `2cadccb93fac2ce979f3074ee29372ad2092095e9028d0ca5286da979781d4c3`
- `source_sha256`: `ddc65e7599d8364181fd84d388ec543d57bfa51c2e66d50777af7ebac2aba3c4`
- `schema_sha256`: `85f16224d232713ba83d6450158df801d1c2df99439e391f80a59b0d4a91ac15`
- `evidence_path`: `evidence_pages/ROW-CUR-0125.pdf`
- `audit_status`: `COMPLETED`

For DIRECT, set `author_inference_assessment` to null. For AUTHOR_INFERENCE, fill the object. Use RFC 3339 UTC. Validate identity, hashes, evidence existence, page bounds, evidence-page count, and schema before finishing. Your final chat response must only say that the candidate is ready; do not reveal the verdict there.
