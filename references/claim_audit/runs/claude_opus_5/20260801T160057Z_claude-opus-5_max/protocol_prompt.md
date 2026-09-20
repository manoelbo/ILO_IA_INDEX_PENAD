# Source-to-Claim Fact-Check Audit Protocol — Claude Arm

## ARM ADAPTATION NOTICE (recorded for provenance)

The originating protocol specified `gpt-5.6-sol` at max reasoning effort, writing to
`references/claim_audit/runs/codex_sol_max/<run_id>/`.

The runtime gate FAILED: the session executing this protocol is Claude Code 2.1.220 running
`claude-opus-5` at max reasoning effort. The mismatch was reported to the user before any
semantic judgment occurred. The user then explicitly directed that this session execute the
**Claude arm** of the intended cross-model comparison instead.

Accordingly, and only accordingly, the following two substitutions were made:

1. Auditor model recorded as `claude-opus-5` (reasoning effort `max`), not `gpt-5.6-sol`.
2. Output root changed to `references/claim_audit/runs/claude_opus_5/<run_id>/`.

The blindness constraint INVERTS: this run must not read anything inside
`references/claim_audit/runs/codex_sol_max/`. Every other clause of the protocol is applied
unchanged. No output was ever written into `runs/codex_sol_max/`.

---

## WORKSPACE

`/Users/manebrasil/Documents/Projects/Dissetação Mestrado`

## AUTHORITATIVE INPUTS

- `references/claim_audit/claim_inventory.tsv`
- `references/claim_audit/CLAIM_INVENTORY.md`
- `references/library.bib`
- `references/pdf_manifest.tsv`
- `references/pdfs/`

Expected baseline: 186 atomic Claim IDs; 227 claim-source-occurrence rows; 58 citation
occurrences; 24 cited works; 23 cited PDFs; 1 legitimate cited legal web source without a PDF.
Verify these counts; if they do not reconcile, stop before auditing and report the discrepancy.

## SCOPE

Audit every one of the 227 unique relationships identified by `(claim_id, citation_key,
occurrence_id)`. The audit unit is the claim-source-occurrence row, not only the Claim ID.

If a claim cites three works, independently determine whether each work supports that claim.
Never approve one source because another source in the grouped citation supports it.

Do not audit uncited statements or excluded instrumental Benjamini-Hochberg mentions in this run.

## IMMUTABILITY

Do not modify: Notion, Zotero, `references/library.bib`, `references/pdf_manifest.tsv`, original
PDFs, `references/claim_audit/claim_inventory.tsv`, `references/claim_audit/CLAIM_INVENTORY.md`.

Write only inside `references/claim_audit/runs/claude_opus_5/<run_id>/`.

Create a run manifest containing hashes of every authoritative input, the exact model, reasoning
effort, prompt hash, schema hash, timestamps, and audit status. If an authoritative input changes
during execution, preserve completed results, stop cleanly, and mark the run as stale/incomplete.

## LANGUAGE

English for scripts, schemas, manifests, filenames, and report structure. Preserve dissertation
claims and source excerpts in Portuguese. Write evidence summaries, mismatch explanations, and
proposed dissertation corrections in PT-BR.

## PDF READING PROTOCOL (split-pdf skill)

Read the split-pdf SKILL.md completely before reading academic PDFs. For each PDF:

- Never load the complete PDF into one model context.
- Preserve the original PDF unchanged.
- Generate run-specific four-page splits (written under `source_build/`, never beside originals).
- Read no more than three splits (~12 pages) in a single batch.
- Use extracted text only to locate candidate evidence.
- Inspect the actual PDF page visually whenever evidence involves a table, figure, equation,
  footnote, unusual layout, or questionable OCR.
- If evidence is not found in the first candidates, continue in additional bounded batches.
- For NOT_FOUND, document all page ranges and search terms examined.
- Do not use abstracts, web snippets, secondary sources, or another paper as claim evidence.
- Web access may only verify publication identity or version; it must not replace the cited source.

Generate an independent extraction and page index. Do not reuse page candidates, summaries, or
verdicts produced by another auditor.

## SOURCE VERSION GATE

Reinspect all source identities before judging claims. The package may contain earlier versions
for at least: `goodman_bacon_difference_2021`, `callaway_difference_2021`, `sun_estimating_2021`,
`de_chaisemartin_two-way_2020`, `santos_silva_log_2006`, `chen_logs_2024`. Do not assume this
remains true; verify the actual stored files.

Where the BibLaTeX record describes the published article but the stored PDF is a working paper,
discussion paper, or preprint: audit the exact stored file; record its exact version and date; use
the stored PDF's real pagination; add `PDF_VERSION_MISMATCH`; do not present preprint pagination
as published-article pagination; recommend replacing the attachment with the final published
version. A version mismatch does not automatically determine whether the substantive claim is
supported — judge content separately, but flag pagination as non-final.

For the legal HTML source, use the official legal locator (article, paragraph, item). Never invent
a page number.

## VERDICT TAXONOMY

Fill `fact_checked` with exactly one of: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`,
`CONTRADICTED`, `NOT_FOUND`, `NOT_VERIFIABLE`, `SOURCE_BLOCKED`.

- **SUPPORTED** — the cited work supports the full claim with compatible population, geography,
  period, direction, magnitude, comparison, method, and modality.
- **PARTIALLY_SUPPORTED** — the claim contains independently meaningful components and the source
  supports only some of them.
- **OVERSTATED** — the source points in the same general direction, but the dissertation
  strengthens causality, magnitude, scope, certainty, generality, or interpretation.
- **CONTRADICTED** — the source reports a materially opposing result.
- **NOT_FOUND** — no supporting evidence found after a documented, sufficiently exhaustive search.
- **NOT_VERIFIABLE** — normative, interpretive, or author inference not establishable from the
  cited source alone.
- **SOURCE_BLOCKED** — missing, corrupt, incorrect, inaccessible, or too version-incompatible to
  evaluate responsibly.

Only `SUPPORTED` is a full pass. Every other verdict must produce a structured issue or
manual-review record.

## AUTHOR_INFERENCE RULE

For AUTHOR_INFERENCE rows, distinguish: (1) whether the cited work supports the factual premises;
(2) whether the dissertation's inference reasonably follows from those premises; (3) whether the
inference is actually the dissertation author's interpretation rather than a conclusion stated by
the source. Do not claim that an article explicitly states an author inference merely because the
inference appears reasonable.

## PAGINATION AND EVIDENCE

For every completed result record: `printed_pages`, `pdf_page_indices`, `source_locator`,
`evidence_summary_pt`, `evidence_anchor`, `evidence_path`, `search_coverage`, `source_version`,
`source_sha256`, `confidence`.

The evidence anchor must be a short source phrase of no more than 12 words. Keep printed
pagination and physical PDF indices separate. Example: pages `pp. 12–13`; pdf_page_indices
`15–16`; source_locator `Section 3.2, Table 2`.

Extract the exact supporting or conflicting page range into `evidence_pages/<row_id>.pdf`.

For HTML legislation: pages `art. X, § Y (HTML sem paginação)`; pdf_page_indices `N/A`;
source_locator the exact official legal hierarchy.

## STRUCTURED ISSUE CONTRACT

For every result other than SUPPORTED, create one or more issue objects containing: `issue_id`,
`row_id`, `issue_code`, `severity`, `claim_as_written_pt`, `source_supports_pt`,
`mismatch_explanation_pt`, `printed_pages`, `pdf_page_indices`, `source_locator`, `evidence_path`,
`recommended_revision_pt`, `needs_new_source`, `recommended_action`.

Severities: `BLOCKER`, `CRITICAL`, `MAJOR`, `MINOR`.

Issue codes: `WRONG_MAGNITUDE`, `WRONG_POPULATION`, `WRONG_PERIOD`, `WRONG_DIRECTION`,
`PARTIAL_SCOPE`, `CAUSAL_OVERCLAIM`, `GENERALIZATION_OVERCLAIM`, `MISATTRIBUTED_METHOD`,
`WRONG_SOURCE`, `MISSING_EVIDENCE`, `AUTHOR_INFERENCE_UNSUPPORTED`, `PDF_VERSION_MISMATCH`,
`SOURCE_UNAVAILABLE`.

Recommended action: `KEEP`, `NARROW_CLAIM`, `REWRITE_CLAIM`, `ADD_SOURCE`, `REPLACE_SOURCE`,
`REMOVE_CITATION`, `REMOVE_CLAIM`, `MANUAL_REVIEW`.

## OUTPUT CONTRACT

```
references/claim_audit/runs/claude_opus_5/<run_id>/
├── run_manifest.json
├── claim_result.schema.json
├── queue.tsv
├── audit_log.jsonl
├── results/
├── source_build/
├── evidence_pages/
├── issues.tsv
├── claim_inventory_audited.tsv
└── AUDIT_REPORT.md
```

Each row result saved independently as `results/<row_id>.json`.

The updated TSV must preserve every original column and original value, fill `fact_checked` and
`pages`, and append: `row_id`, `audit_status`, `source_version`, `source_sha256`, `printed_pages`,
`pdf_page_indices`, `source_locator`, `evidence_summary_pt`, `evidence_anchor`, `evidence_path`,
`search_coverage`, `confidence`, `issue_codes`, `issue_severity`, `issue_detail_pt`,
`recommended_revision_pt`, `needs_new_source`, `auditor_model`, `audited_at`.

## ONE-BY-ONE EXECUTION

Process claims strictly sequentially. The actual semantic judgment for each row must happen in a
fresh isolated worker or model context. Only one claim worker may be active at a time.

The controller may retain: queue state, input hashes, schema, validated JSON results, completion
counters. The controller must not carry informal evidence summaries or assumptions from one claim
into the next claim's judgment context.

Write each validated result atomically before advancing. A completed result may only be reused on
resume if the claim row, prompt, schema, bibliography entry, and source hashes are unchanged.

## CALIBRATION GATE

First audit only these four Bick relationships: `CLM-001 / bick_rapid_2024 / CIT-001`,
`CLM-002 / bick_rapid_2024 / CIT-001`, `CLM-003 / bick_rapid_2024 / CIT-001`,
`CLM-004 / bick_rapid_2024 / CIT-001`.

Produce the four JSON results, a temporary calibration table, and a concise calibration receipt
covering: verdict; evidence; printed page; PDF page; source version; distinction between direct
evidence and author inference; any structured issue. Then STOP and wait for explicit user approval
before processing the remaining rows.

## QUALITY CONTROL AFTER APPROVAL

After all 227 primary judgments, run a blind second review in fresh contexts for: every
non-SUPPORTED result; every LOW or MEDIUM confidence result; every source-version issue; and a
deterministic 10% sample of SUPPORTED results. The reviewer must not see the primary verdict or
rationale before issuing its own assessment. Mark disagreements as `NEEDS_ADJUDICATION`. Do not
silently choose one answer.

## FINAL REPORT

`AUDIT_REPORT.md` must include: input and model manifest; scope and limitations; counts by
verdict; counts by work; counts by claim type; counts by dissertation section; high-severity
issues; source-version problems; claims needing another source; grouped citations with mixed
support; NOT_FOUND search coverage; claim-level rollup (`ALL_SOURCES_SUPPORT`,
`AT_LEAST_ONE_SOURCE_SUPPORTS`, `MIXED_SUPPORT`, `NO_SOURCE_SUPPORTS`); quality-control
disagreements; evidence-page manifest; unresolved blockers; final Notion drift status if Notion
access is available.

## ACCEPTANCE CRITERIA

Do not mark the audit complete unless: exactly 227 unique row results exist; all 186 Claim IDs, 58
occurrences, and 24 works reconcile; every `fact_checked` cell is filled; every `pages` cell is
filled or formally blocked; every substantive verdict has exact evidence or documented search
coverage; every non-SUPPORTED result has a structured issue; all evidence files exist; all page
numbers are within source bounds; all counts reconcile across JSON, TSV, and Markdown; original
inputs retain their initial hashes; model and reasoning configuration are recorded; no output from
the opposing arm was read.
