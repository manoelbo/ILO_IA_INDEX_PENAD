# Prioritized Code Recommendations

## Decision rule

These recommendations are ranked by scientific impact, not by whether
they make estimates more statistically significant. V1 is a frozen
baseline and should not be silently patched. Material corrections should
be implemented in V2 and documented even if estimates become weaker or
null.

## P0 — Required before circulation as a robust replication package

| Priority | Change | Impact | Effort | Depends on |
| --- | --- | --- | --- | --- |
| P0.1 | Rebuild wage missingness: wage and wage-composition fields must be `NA` when their corresponding flow is zero; reject invalid/extreme salary records before aggregation | Prevents artificial salary outcomes and contaminated controls | Medium | New CAGED vintage |
| P0.2 | Make the no-contemporaneous-composition-control model the main specification; use predetermined controls × post only as named robustness | Removes a plausible post-treatment-conditioning problem | Medium | Frozen model contract |
| P0.3 | Correct A.6 to use the income source, assert allowed income labels, and assert that A.6 is semantically distinct from A.5 | Eliminates a known false table | Low | Correct source table |
| P0.4 | Re-estimate every inferential artifact from analytical inputs: event studies, exact-model pretrends, DDD, PPML, real wages, heterogeneity, and occupation cases | Converts rendering reproducibility into scientific reproducibility | High | Rebuilt panel and stable APIs |
| P0.5 | Replace clipped event time with a balanced `-23…+23` main window and explicit named horizons; never label pooled endpoints as individual months | Aligns estimand, figure, and pretrend test | Medium | Continuous monthly panel |
| P0.6 | Publish complete raw-to-output provenance: URL, retrieval date, release vintage, checksum, size, schema, stage input/output hashes, and row deltas | Makes `full` auditable and repeatable | Medium | Official inputs frozen |

## P1 — Required methodological and validation gates

### Count and wage estimators

- Estimate admissions and separations with PPML as the preferred model.
- Retain OLS on `log(1+y)` only as a secondary estimand.
- Estimate real admission wages only where a valid admission wage exists.
- Retain `asinh(net flow)` as a complementary, non-percentage outcome.
- Record PPML convergence, separation, dropped cells, observations,
  clusters, and fixed effects for every model.

### Data construction and merges

- Add fail-fast domain checks for movement type, sex, race/color,
  education, age, CBO, CNAE, municipality, establishment size, and
  salary fields.
- Preserve the explicit female code `sexo = 3`.
- Define unknown/missing categories and denominators before aggregation.
- Assert uniqueness and expected cardinality before and after each merge.
- Report unmatched keys and row gains/losses for each stage.
- Require continuous months and report CBO support for each analysis
  window.

### Treatment and crosswalk

- Freeze every crosswalk source by checksum and retrieval date.
- Keep `G1–G4 versus Not Exposed` as the main contrast while explicitly
  reporting that G4 is empty if that remains true.
- Keep `Minimal Exposure` excluded from the main contrast.
- Use the broad control, continuous exposure, and legacy MTE benchmark
  only as labelled robustness checks.

### Dynamic and subgroup inference

- Estimate pretrends in the exact model and exact estimation sample.
- Do not interpret a non-significant pretrend test as proof of parallel
  trends.
- Add HonestDiD sensitivity for compatible linear models.
- Require DDD as `post × treatment × subgroup` plus all lower-order
  terms.
- Report support by subgroup cell and adjust multiplicity by outcome
  family.
- Treat thin-support or failed-pretrend results as exploratory.

### Reference and artifact integrity

- Validate `results/reference` against a signed or checksum manifest
  before comparing reproduced outputs.
- Add semantic contracts for table labels, allowed category sets, units,
  sample sizes, and source IDs.
- Replace thumbnail-only figure comparison with exact backing-data
  comparison plus a meaningful image-diff threshold.
- Map every manuscript number to a producer, specification, input
  vintage, and output hash.

## P2 — Valuable but not a blocker for the empirical decision

- Strengthen Section 3 checks for finite positive survey weights,
  complete 2025Q3 period fields, and valid demographic domains.
- Add simulated-data tests for DDD signs, lower-order interactions,
  fixed effects, clustering, and binary-group mirroring.
- Run the full DAG twice in clean environments and require identical
  manifests.
- Separate terminology in logs and documentation:
  `re-estimated`, `validated frozen estimate`, and `rendered artifact`.

## Tests that should become release gates

1. Income A.6 contains only the pre-specified income bands and has the
   correct source hash.
2. Wage is missing whenever the corresponding flow is zero.
3. Invalid and implausible salaries are reported and handled before
   aggregation.
4. The main formula contains no contemporaneous composition controls.
5. Every inferential table has a live estimator test, not only a copied
   backing file.
6. Event-study horizons are complete and never clipped.
7. Every merge reports uniqueness, match status, and row deltas.
8. Demographic code fixtures include unknown and missing values.
9. Python and R agree on observations, coefficients, and standard errors
   to at least six decimals.
10. All reference files match the immutable reference manifest.

## What not to spend time on now

- cosmetic refactoring of already readable modules;
- renaming every legacy internal schema identifier;
- adding new heterogeneity dimensions not present in the dissertation;
- tuning models to recover significance;
- expanding the dissertation's chapter structure.

The highest-return work is a clean data rebuild, corrected outcome
semantics, a pre-specified estimator hierarchy, and complete
claim-to-artifact lineage.
