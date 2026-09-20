# Research Design and Replication Contract

## Scope

The computational authority is the 53-row publication registry in
`config/manuscript_artifacts.csv`. It covers Section 3, the CAGED design in
Sections 4 and 5.1--5.2, complementary RAIS and PNADc evidence, and Appendices
A--D. Narrative quantities are separately enumerated in
`config/numeric_claims.csv`.

This refactor changes packaging and validation, not the empirical
specifications, samples, multiplicity families, or accepted estimates. A new
estimate cannot replace the signed reference merely because it appears more
favorable.

## Treatment and CAGED estimands

The principal occupational contrast pools ILO exposure Gradients 1--4 as the
treated group and compares it with `Not Exposed`; `Minimal Exposure` is
excluded from the principal contrast. The event is the public release of
ChatGPT in November 2022, with December 2022 as event time zero.

The treatment assignment is frozen before estimation. Employment-weighted,
task-dispersion, and native-label variants remain sensitivity analyses and can
never replace the principal classification because of their coefficients or
significance. Ties in the native-label weighted mode are resolved toward the
less-exposed category. CBO6 employment is split equally across multiple
crosswalk destinations before destination weights are applied.

Principal flow outcomes use PPML. Real admission wages use OLS in logs, and net
flows use OLS after the inverse-hyperbolic-sine transformation. The national
specification absorbs CBO4 and month fixed effects and clusters by CBO4. The
balanced event-study window is `-23...+23`, with November 2022 as the omitted
period. Sector robustness adds CNAE fixed effects and the registered clustering
structure.

Reported inference uses cluster-robust standard errors with a cluster-t
reference distribution and degrees of freedom equal to the smallest cluster
count minus one. Contemporary composition controls are excluded from the
principal specification. The complete January 2021--May 2026 window is retained
because the preregistered treated-control late-declaration gap stays below one
percentage point; the direction and magnitude of the incomplete tail remain
reported.

The static admission-wage coefficient (`-0.050740`) and the event-study
post-period average (`-0.015363`) are different estimands. The former averages
the static post indicator through event time `+41` against the complete
pre-period; the latter is `average_post_event_time_0_to_23`, normalized to
November 2022. HonestDiD, including the `M = 0` statement about whether the
interval excludes zero, targets the latter event-study estimand. The package
never juxtaposes the two as if they were the same estimate.

DDD is reserved for a model containing `post x treatment x subgroup` and all
identified lower-order terms. Per-group DiDs remain descriptive inputs to the
heterogeneity display and do not become triple differences by relabeling.

## Multiplicity families

- Family A: 100 planned primary subgroup DDD tests.
- Family B: 30 planned alternative-partition DDD tests.
- Family C: 130 per-group DiD tests, adjusted once over the complete family.
- Family D: three RAIS outcomes.
- Family E: six PNADc outcomes.
- Family F: twelve declared spatial outcome-by-proxy slots that remain
  unestimated because the support gate closes.

Benjamini--Hochberg is applied once within each estimated family. Family F has
no coefficient, p-value, or BH value.

## Identification gates

Support is evaluated before coefficients. Pretrend classification combines the
registered joint lead Wald test, GLS linear slope, and individual lead
inspection. A failed pretrend, a non-PSD covariance block, a thin-support label,
or an estimation failure remains visible in outputs and cross-language status.
Positive semidefiniteness and numerical rank are recorded separately. The
declared rank threshold is
`max(nrow, ncol) * machine epsilon * largest singular value` in both languages.
A PSD but rank-deficient lead block cannot identify an inverse-covariance Wald
test or GLS slope. Its event coefficients and standard errors remain published,
while the derived tests are missing by construction and the classification is
`not_interpretable_rank_deficient`.

The national CAGED and subgroup DDD designs do not pass the complete identifying
diagnostics. They therefore support an exploratory treated-versus-control
description, not an unqualified causal effect. RAIS and PNADc are
complementary measurement exercises: composition is not a worker transition. The spatial
module is a documented support negative and stops before the treatment model.
Its legacy 8.61 percent late-declaration benchmark is retained as incompatible:
that number mixes declaration-year and fact-month axes, whereas the registered
construct consistently uses the signed fact month. The discrepancy is not
repaired by redefining the frozen denominator.

Registered robustness and mechanism modules retain wage missingness and
winsorization checks, contemporary controls, count-estimator alternatives,
treatment-classification variants, separation flows, the cumulative net-flow
proxy, hourly wages and schedules, establishment size, public/private
falsification, and alternative exposure measures. These diagnostics do not
override the identification gates.

The high-income target-group pretrend has especially thin effective support.
All five outcome models are estimated, including separation flows, but each has
rank 7 in a 22-lead covariance block. The event coefficients and standard
errors remain visible while the joint Wald and GLS slope diagnostics are
undefined by construction. Python and R agree on the estimated status and the
`not_interpretable_rank_deficient` classification.

## Independent R replication

Python constructs coefficient-free analytical inputs and explicit model
contracts. R 4.4.1 reads only those inputs and independently recalculates:

- all Section 3 aggregates;
- national and sector CAGED estimates;
- Families A--C and all registered event-time coefficients;
- national, sector, DDD, and group pretrend diagnostics;
- Families D and E, including their exact-model pretrends;
- spatial placebos, pre-treatment interactions, effective support, and the
  Family F stopping condition.

The join keys are stable analysis, model, term, and event-time identifiers.
Coefficients and standard errors must differ by no more than `1e-6`.
Observation counts, minimum clusters, samples, statuses, and reference event
times must match exactly. Derived diagnostic p-values use a declared `2e-5`
absolute numerical tolerance, and joint Wald statistics use `1e-6` absolute
plus `1e-3` relative tolerance; pretrend classifications, covariance rank, and
PSD flags still match exactly. HonestDiD remains R-native; Python validates its
coefficient and covariance inputs and its registered outputs. Those inputs are
exported directly from the independently fitted R event-study models and never
from a Python result file.

## Reproducibility gates

A release requires all of the following:

1. exactly 53 registered publications, with no missing or extra publication;
2. every registered narrative quantity reconciled to backing data;
3. offline `reproduce` success from repository plus analytical bundle;
4. an end-to-end `full` rebuild from the frozen official sources;
5. two deterministic `reproduce` runs for text and data artifacts, plus
   structural and visual checks for figures;
6. complete Python--R validation with no silently skipped row;
7. no absolute path or dependency outside the package and supplied bundle;
8. byte preservation of V1; and
9. an independent Referee 2 audit before release.

The CAGED sector panel is aggregated by DuckDB with a single worker and is
sorted by its complete analytical key before Parquet serialization. This makes
the panel hash and all sector-model derivatives independent of parallel group
aggregation order; the estimation sample and model contracts are unchanged.
