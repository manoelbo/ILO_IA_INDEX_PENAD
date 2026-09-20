# Prioritized Text Recommendations

## Editorial decision

Keep the dissertation's current structure. Revise claims, tables,
references, and rendering in place. Do not add a literature chapter,
new heterogeneity dimensions, or a new conceptual architecture.

## P0 — Correct before sending to the advisor

| Priority | Change | Impact | Effort | Dependency |
| --- | --- | --- | --- | --- |
| P0.1 | Correct the executive-summary statistic to 10.1% of all employed workers and 14.8% of formal workers | Removes a headline factual error | Very low | None |
| P0.2 | Reconcile Appendix A.6 with a computational source that actually produces income rows | Repairs the critical text-package break | Low in text; medium in code | Correct V2 source mapping |
| P0.3 | Complete Appendix A.5 with `asinh(net flow)` and B.2 robustness rows | Restores promised education diagnostics | Low | Existing backing table |
| P0.4 | Replace or qualify unreported robustness promises | Prevents unsupported method claims | Low | Decide which existing robustness results to show |
| P0.5 | Replace broken Appendix B links with stable bundled paths or include the compact tables | Makes evidence reachable | Low | Artifact packaging |
| P0.6 | Regenerate the full reference list from the corrected canonical `.bib` | Restores citation completeness | Low | `corrected_library.bib` |
| P0.7 | Rebuild and inspect the PDF so no support column is clipped and no markup is printed | Makes diagnostics legible | Medium | Corrected Markdown |

## P1 — Tighten interpretation without changing structure

### Abstract, introduction, and conclusion

Use one consistent high-level conclusion:

> The estimates show no robust national causal effect on formal labor
> flows or entry wages. Some subgroup contrasts are compatible with
> localized post-ChatGPT changes, but several pretrend and support
> diagnostics require an exploratory interpretation. The design measures
> predetermined occupational exposure, not observed AI adoption, and
> does not observe employment stocks.

Specific replacements:

- replace “and not job destruction” with “which is compatible with lower
  turnover, but does not identify the change in employment stock”;
- replace “transformation in progress” with “occupations with greater
  technical exposure potential”;
- replace “effects should appear first” with “the analysis examines
  whether differential changes are concentrated in”;
- replace “mechanisms” for occupation cases with “descriptive pathways”
  or “illustrative trajectories”;
- reserve “effect” for sentences that immediately state the identifying
  assumptions and diagnostic limitations; otherwise use “estimate”,
  “differential change”, or “pattern”.

### Panel universe

Define four denominators once and reuse them:

1. 629 CBO4 codes in the classification universe;
2. 436 officially matched CBO4 codes in the classified panel;
3. 341 CBO4 codes in the strict treated-versus-control sample;
4. 18,307 CBO-month observations retained by the central models.

Do not label all 629 as observed analytical-panel CBOs.

### Estimator rationale

Remove “many zeros” as the central reason for `log(1+y)`. Describe it as
an interpretable secondary transformation and introduce PPML as the
preferred count estimator in V2.

### Heterogeneity language

- Treat the female-admissions DDD as the cleanest demographic contrast,
  not proof that AI adoption harmed women.
- Describe race/color results as a separation-flow differential, not a
  stock or turnover mechanism.
- State that age is not tenure or firm-specific experience.
- Emphasize the education separation result more than the admissions
  result when discussing robustness.
- Keep the top-income result out of the substantive conclusion because
  support is `thin`.

## P1 — Appendix and artifact repairs

- Add explicit B.1 and B.2 labels to A.5 and A.6.
- Use Portuguese labels and notes consistently.
- Replace Markdown `<br>` inside cells with a renderer-safe format, such
  as coefficient and standard error on one line.
- Use literal `< 0,001` only if the renderer escapes it correctly;
  otherwise use `p < 0,001` as plain text.
- Ensure all appendix tables fit in landscape or use a smaller font
  without dropping columns.
- Add a compact table that disposes of the broader control, no-control,
  predetermined-control, and Poisson robustness specifications.
- Link every table and figure to a bundled backing CSV and producer
  rather than an application-internal URL.

## P2 — Quick internal-consistency cleanup

- Correct the 55+ arithmetic and label at the current line 277.
- Correct the sector-volume sentence to identify Commerce first.
- Replace “Anexo 1.1” with the actual destination.
- Replace Section 3.7 with Section 3.5.3.
- Remove the duplicate data-URI copy of Figure 3.2.
- Remove all `file ref`/`ref file` markers.
- Remove internal Notion rewrite-page links after the references.
- Synchronize Markdown, HTML, and PDF in one final render.

## Bibliography actions

Use:

`Final Review/Codex/evidence/bibliography/corrected_library.bib`

Then:

1. regenerate all 36 references;
2. update the four canonical publication records;
3. replace or relabel the three preprint attachments that no longer
   match their published records;
4. replace four EBSCO export attachments with actual documents when
   convenient;
5. keep the root competing `.bib` out of the build.

## Suggested work order

1. Apply the factual and interpretive text corrections.
2. Insert the complete A.5 and correct A.6 source mapping.
3. Add the compact robustness disposition.
4. Replace artifact links and regenerate references.
5. Remove export debris.
6. Render HTML and PDF once.
7. Inspect every appendix page at full width.
8. Re-run the claim-to-artifact audit before sending.

## Explicit non-goals

- no chapter reordering;
- no new empirical families;
- no attempt to make results more significant;
- no exhaustive prose polishing before the material blockers are fixed;
- no claim that longer post-treatment coverage repairs failed pretrends.
