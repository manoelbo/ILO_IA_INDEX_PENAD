# Source gate report

Status: **BLOCKED BEFORE BLIND CLAIM REVIEW**

This report records the source-alignment gate for the complete blind audit of
`Dissertação de Mestrado V2 (1)`. No blind judgment has been started, and the
Notion page was not edited during this run.

## Frozen inputs

- Notion page ID: `33dcc8ca-4610-82bd-a888-0151f42ba19b`
- Fetch time: `2026-08-08T15:29:44.957Z`
- Current semantic SHA-256: `f4718a8410b6deb087247656d798fbe97bc231c9d42a2b59ea661bb533c4fccf`
- Previously expected SHA-256: `8586595c356286821810d789ad99821b1f6f667933b07abe243afeff3f957efa`
- Current snapshot policy: the newly fetched page is authoritative; prior
  judgments are not reused merely because an old claim resembles the new text.

The page changed materially after the previously recorded post-edit snapshot.
The current inventory was therefore rebuilt from the live frozen content.

## Bibliographic and source checks

- Zotero backup: `references/zotero_backups/20260808T152451Z_postedit_blind/dissertation_master_backup.rdf/`
- Zotero export candidate: 44 entries and 44 unique keys.
- Canonical `library.bib`: 44 entries and the same 44 keys.
- Semantic comparison excluding attachment paths: zero entry differences.
- Portable PDF manifest: 43 PDFs with valid hashes.
- Cited audit subset: 22 sources, comprising 21 PDFs and one official legal HTML snapshot.
- Cited keys missing from `library.bib`: zero.
- Duplicate cited keys: zero.

Five published methodological works use official author or arXiv manuscripts
because an accessible publisher PDF was not available. The exact manuscript
version is declared in `library.bib` and `source_manifest.tsv`. Their manuscript
page labels must never be combined with the journal page range.

## Blocking conflict

`humlum_still_2025` is aligned across Zotero, `library.bib`, and the official
current NBER PDF, but not with the frozen Notion reference.

- Current official title: *Still Waters, Rapid Currents: Early Labor Market Transformation under Generative AI*
- Date: May 2025; revised March 2026
- NBER Working Paper: 33777
- DOI: `10.3386/w33777`
- PDF SHA-256: `eb5765a77d38f7e0d66e906252ecb721aaa888f6ba3540913e3cb31edcb91807`
- Frozen Notion title: *Large language models, small labor market effects*
- Frozen Notion citation year: 2026

The former title is explicitly identified by the current NBER manuscript as a
previously circulated title. The dissertation must use `Humlum e Vestergaard
(2025)` in text and the current title/date in the reference entry if the source
gate is to pass without an exception.

## Post-edit inventory

- Formal citation occurrences: 61
- Citation keys: 22
- Source-claim-occurrence rows: 207
- Atomic claims: 182
- `DIRECT` rows: 158
- `AUTHOR_INFERENCE` rows: 49
- Empty `fact_checked` and `pages` cells: 207, as required before review
- Duplicate `(claim_id, citation_key, occurrence_id)` triples: zero
- Exact prior judgments eligible as primary judgment A: zero
- Prior rows removed or rewritten beyond exact reuse: 213

The current page includes Benjamini-Hochberg and excludes Goodman-Bacon, as
required. The full occurrence and claim inventories are available in
`citation_occurrences_postedit.tsv` and `claim_inventory_postedit.tsv`.

## Runtime and Bick readiness

- Runtime preflight: `RUNTIME_OK gpt-5.6-sol max`
- Fallback allowed: no
- Bick source PDF: Working Paper `2024-027F`, revised 2025-10-27
- Bick PDF SHA-256: `852097fc72812af45bd3693d7a661c70457eb674ab8f493cadb268450e556b5b`
- Physical pages: 53
- Immutable four-page splits: 14, all hashes verified
- Bick claims: four, matching the approved calibration exactly
- Bick judgments A/B/C: not started

The audit can resume immediately after the Humlum metadata conflict is resolved
or the author explicitly approves a documented exception. Until then, starting
blind claim reading would violate the approved source gate.
