# Dissertation V4 revision — 19 September 2026

The revision is applied directly to [Dissertação de Mestrado V4 — Revisão](https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e). This directory preserves the original text, the revised readback, presentation files, and verification evidence. It is a separate editorial revision, not a new replication-package release.

## Applied changes

- Reordered Section 4 into data, crosswalk and treatment, identification, specifications and outcomes, heterogeneity, and diagnostics. The sector specification is co-primary.
- Rebuilt Section 5 around national estimates, four diagnostic blocks, and five demographic DDD comparisons. Full DDDs and within-group DiDs, including alternative partitions and all outcomes, are in Appendix A.3–A.7.
- Added Section 6 with four discussion subsections and Section 7 with seven conclusion paragraphs. Updated the introduction and affected cross-references.
- Restored nominal significance stars in the national and sector tables. Heterogeneity stars retain the original BH-adjusted values and families; selection of displayed rows does not trigger a new adjustment.
- Added three separate synthesis figures in Appendix A.8. Re-rendered eleven existing demographic figures with appendix numbering and corrected presentation notes, using the same saved series and interval conventions.
- Integrated ten review drafts at their final positions, each preceded by a `REVISAR COM MANÉ` marker. The opening toggle indexes them.

## Remaining user review and manual cleanup

The opening **Controle da revisão V4** toggle lists all ten textual review points: crosswalk attenuation, identification, national precision, income diagnostics, heterogeneity exceptions, pandemic/adoption, international comparisons, small occupations, measurement choices, and the conclusion.

Twelve original image blocks remain in Section 5.3, individually marked **M01–M12**. Their appendix destinations have been inserted and verified. Exact-match deletion through the connector failed because the signed image URLs change between reads and edits; browser control also timed out. Remove only the old copies and their adjacent pending markers, preserving the appendix figures. See [the manual cleanup inventory](evidence/manual_items.json). This follows the plan's explicit manual-operation fallback; it is the only outstanding mechanical editing step.

## Factual reconciliation

| Issue | Revision and evidence |
| --- | --- |
| Event window | Separate the full static sample through May 2026 (+41), the registered balanced event/diagnostic window −23 to +23, and the saved extended profiles through +41. November 2022 remains the omitted reference. |
| Wage multiplicity | Family A contains 100 tests, including 20 wage tests. Two wage contrasts reject after the original BH adjustment. Families A/B/C remain 100/30/130 tests. |
| Occupation denominators | The crosswalk has 629 families and 193 without scores. The observed panel adds CBO 2414 in five cells, yielding 630/194. The main sample has 341 scored families; Gradient 4 is part of the treatment rule but absent from the effective sample. |
| Income diagnostics | High-income group estimates have 423 observations; the covariance for 22 leads has rank 7. Joint Wald and GLS diagnostics are undefined, not evidence of parallel trends. DDD diagnostics belong to a different model and sample. Low- and middle-income wage joint p-values are 0.0156297 and 0.000169343. |
| Heterogeneity exceptions | Preserve significant balance and gross-flow contrasts, the high-income wage result with thin support, and the wage result for missing race/color. Do not equate significance with identification. |
| Measurement and mechanisms | Score compression does not establish attenuation of a regression coefficient. Pandemic/cycle mechanisms remain hypotheses. Adoption data would still require a design addressing selection. Occupation volume shares are not exact PPML regression weights. |

Machine-readable evidence is in [factual_reconciliation.json](evidence/factual_reconciliation.json), [multiplicity_counts.json](evidence/multiplicity_counts.json), and [the presentation map](presentation_map.csv).

## Verification

The final connector readback contains 40 native tables, 40 image blocks (including one pre-existing empty image and the twelve explicitly retained old copies), five display equations, ten review markers, and twelve manual markers. The conclusion has seven paragraphs.

- All 17 newly rendered table bodies match the Notion readback cell by cell, allowing only Notion's escaping of literal Markdown punctuation.
- All 14 inserted images were downloaded from Notion and match their local files byte for byte.
- All original image blocks remain accounted for. Sections 2 and 3 are unchanged after normalizing temporary URL query strings and whitespace.
- The eight numerical inputs hashed before rendering remain unchanged. Coefficients, BH values, and saved figure intervals were checked against their frozen inputs.
- The three new synthesis plots were visually inspected locally. Native Notion layout could not be inspected because browser control timed out; remote verification therefore consists of connector readback, structure checks, and downloaded-asset comparison.

See [final_verification.json](evidence/final_verification.json) and [render_verification.json](evidence/render_verification.json). Notion's native page verification status was not changed; readback verification here does not imply human acceptance of the dissertation.

## Files and replay

- [Original text](source/notion_before.md) and [final Notion readback](notion_after.md). Signed image URLs in these snapshots expire; local image files are retained.
- `source/images/`: downloaded original assets.
- `sections/`: prepared section drafts. The final Notion readback is authoritative, including manual-operation markers and final targeted edits.
- `tables/`: rendered table markup and full heterogeneity CSVs.
- `figures/`: three new synthesis plots in PNG/PDF, plus eleven renumbered figures.
- `scripts/assemble_*.py`: editing-stage assembly helpers; they are not a fresh end-to-end publishing workflow and may precede final targeted edits.
- `scripts/render_v4.py` and `scripts/renumber_figures.py`: presentation rendering from frozen files; neither fits models.
- `scripts/verify_final.py`: checks the final readback. The image-download portion requires a fresh Notion snapshot because download URLs expire.

From the V2 workspace, presentation replay uses:

```sh
uv run --no-project --with pandas --with matplotlib --with scipy --with pyarrow python revisions/v4_2026-09-19/scripts/render_v4.py
uv run --no-project --with pandas --with matplotlib --with scipy --with pyarrow python revisions/v4_2026-09-19/scripts/renumber_figures.py
python3 revisions/v4_2026-09-19/scripts/verify_final.py
```

No regressions were run. The frozen 53-publication inventory, package documentation, and frozen references were not synchronized or re-released. Existing unrelated workspace changes were preserved; no commit was created.
