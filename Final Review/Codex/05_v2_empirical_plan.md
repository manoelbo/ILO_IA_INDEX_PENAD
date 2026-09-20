# V2 Empirical Plan

## Status and decision rule

V2 is a conditional methodological refresh, not a search for stronger
statistical significance. A full build proceeds only if:

1. one official Novo CAGED vintage can be frozen and reconciled;
2. the preferred models are estimable with adequate cluster and cell
   support; and
3. V2 resolves at least one material V1 weakness in data lineage,
   outcome construction, dynamic specification, estimation, or
   artifact linkage.

The baseline capture recorded 6.78 GiB free. A later gate recheck, after
temporary files were cleaned, recorded approximately 8.45 GiB. Both are
below the required 15–20 GiB. The full data refresh is therefore blocked
until storage is available. No author data may be deleted to satisfy this
gate.

## Gate audit on 25 July 2026

**Current status: NO-GO for the full V2 rebuild.**

| Gate | Status | Evidence |
| --- | --- | --- |
| Storage | NO-GO | 6.78 GiB at baseline capture; 8.45 GiB at the later post-cleanup recheck; contract requires 15–20 GiB |
| Official CAGED through May 2026 | Available | 65 continuous competencies, January 2021–May 2026 |
| Official CAGED June 2026 | Not yet available | Scheduled for 30 July 2026 |
| Single local vintage | NO-GO | Local Parquets stop at June 2025 and predate June 2026 historical revisions |
| IPCA source | Available | June 2026 is published, but the local input stops at December 2025 |
| V2 ingestion architecture | NO-GO | V1 loads annual files in memory, duplicates raw files in work, and drops planned metadata |
| Isolated Python/R environments | NO-GO | Required V2 R packages and clean pinned environments are not provisioned |
| Treatment support | Conditional | Current realization is 75 treated G1–G3 and 266 controls; G4 is empty |

The official FTP listing contains one `CAGEDMOV` file for each of the
65 continuous competencies and approximately 2.897 GiB of compressed
movement files. Historical official files for 2021–2025 were modified
in June 2026. The local yearly Parquets were created in February 2026,
contain 2021–2024 plus January–June 2025, and therefore cannot be
extended by simply appending 2026 without mixing vintages.

The cutoff will be fixed once, at execution:

- use June 2026 if competence `202606` has been officially released;
- otherwise use May 2026 and do not delay the project.

## Frozen design contract

| Element | V2 contract |
| --- | --- |
| Main population | Novo CAGED movements from January 2021 |
| Data cutoff | June 2026 if officially released when the vintage is frozen; otherwise May 2026 |
| Availability event | Public ChatGPT launch on 30 November 2022 |
| First treated month | December 2022 |
| Reference month | November 2022 (`t = -1`) |
| Main treatment | ILO exposure gradients G1-G4 |
| Main control | `Not Exposed` |
| Main exclusions | `Minimal Exposure` and occupations without an accepted score |
| Main count estimator | PPML with fixed effects and CBO-clustered inference |
| Secondary count estimator | OLS on `log(1 + y)`, interpreted as a transformed-outcome estimand |
| Main wage estimator | OLS on log real admission wage for valid wage cells |
| Complementary outcomes | Real separation wage and `asinh(net flow)` |
| Main fixed effects | CBO4 and calendar month |
| Enriched robustness | CBO-CNAE unit effects and CNAE-month effects, subject to support |
| Main monthly window | `t = -23` through `t = +23`, with no endpoint clipping |
| Pandemic sensitivity | Sample starting January 2022 |
| Recent-data sensitivity | Sample ending December 2025 |

The treatment label must disclose the realized distribution. If no
accepted occupation belongs to G4, the empirical treatment is effectively
G1-G3 even though the pre-specified rule is G1-G4.

## Data-vintage construction

1. Freeze the official MTE source URLs, retrieval timestamp, local
   SHA-256 hashes, bytes, schema, encoding, and available competencies.
2. Rebuild the full January 2021-cutoff window. Do not append only new
   months because late declarations and source corrections can revise
   earlier competencies.
3. Export a revision table comparing the V2 vintage with the overlapping
   V1 monthly totals and analysis cells.
4. Reconcile monthly admissions, separations, and net flows with official
   aggregates. Any tolerance must be explained by documented sample
   restrictions rather than silently accepted.
5. Update IPCA and any other price input through the same cutoff.
6. Preserve raw files outside the distributed package; publish only
   derived, non-identifying analytical inputs allowed by the data terms.

## Metadata contract

V2 retains source metadata before aggregation and assigns each field one
explicit role.

| Metadata | Permitted role |
| --- | --- |
| `tipo_movimentacao` | Construct and audit admissions and documented separation categories |
| CNAE | Industry composition diagnostics and the pre-specified enriched robustness panel |
| Municipality and state | Coverage and merge diagnostics; existing spatial extension only |
| Establishment size | Sample/composition diagnostics; not an improvised contemporaneous main control |
| Salary unit, fixed value, hours, and monthly salary | Validate salary monthlyization and missingness |
| Sex, race/color, education, and age | Existing pre-specified heterogeneity with raw-code validation |
| CBO fields and official descriptions | Treatment crosswalk, support, and occupation-case transparency |

Unknown codes, duplicate movement identifiers where available, invalid CBO
or CNAE values, and impossible wage/count combinations are fail-fast
conditions.

## Estimation hierarchy

### National outcomes

- Admissions and separations: PPML main model; `log(1 + y)` OLS secondary.
- Real admission wage: main linear fixed-effect model.
- Real separation wage and net flow: complementary, never headline.
- Report coefficient, transformed percentage where appropriate, standard
  error, confidence interval, observations, CBO clusters, and dropped
  cells.
- Export PPML convergence and separation diagnostics.

### Dynamic effects

- Estimate the exact preferred model for every lead and lag.
- Use the balanced monthly window `-23` to `+23` without clipping.
- Report explicit horizons:
  - December 2022-November 2023;
  - December 2023-November 2024;
  - December 2024-November 2025;
  - December 2025-data cutoff, explicitly marked partial.
- Treat product releases as annotations, not alternative event dates.
- A non-significant joint pre-trend test is not proof of parallel trends.
  Use sensitivity analysis for compatible linear specifications and
  document nonlinear-model limitations.

### Heterogeneity

- Re-estimate only families already present in the dissertation: sex,
  race/color, age, education, income, and frozen occupation cases.
- Use the term DDD only for a model containing
  `post x treatment x subgroup` and all lower-order terms.
- Report support, sample size, clusters, exact-model pre-trends, and
  multiplicity-adjusted inference by result family.
- Thin-support or unstable results remain exploratory or move to the
  appendix; they cannot become headline findings because they are
  statistically stronger.

## V2 package interface

`Replication Package/V2/run_replication.py` preserves the V1 public
interface:

```text
python run_replication.py \
  --section {all,3,4-5} \
  --mode {reproduce,full} \
  [--raw-dir PATH] \
  [--output-dir PATH] \
  [--billing-project PROJECT] \
  [--skip-figures] \
  [--dry-run]
```

The default data cutoff and specification are read from immutable,
versioned contracts. The CLI does not expose event dates, treatment
definitions, or estimator selection as result-shopping switches.

V2 must add:

- a human-readable and machine-readable analysis contract;
- a data-vintage manifest;
- revision, schema, missingness, support, and convergence reports;
- regenerated backing data for every final table and figure;
- a claim registry for every empirical number retained in the manuscript.

## Acceptance gates

### Data gate

- Every expected month appears exactly once.
- No state, CBO, CNAE, or source component is silently absent.
- V1/V2 overlap revisions are quantified.
- Official aggregates reconcile or deviations have a documented sample
  explanation.

### Model gate

- Preferred PPML models converge and report separation/drop diagnostics.
- The main treatment and control match the frozen contract.
- CBO cluster support remains adequate.
- Dynamic estimates use the exact model and contain no endpoint clipping.
- DDD and multiple-testing contracts pass automated tests.

### Artifact gate

- Every table, figure, and manuscript number maps to generated backing
  data.
- Python and independent R implementations use identical samples and
  agree to at least six decimal places, or discrepancies are diagnosed.
- The final PDF contains no broken links, scrambled tables, duplicate
  figures, clipped content, or inaccessible appendix evidence.

### Stop conditions

Record `NOT EXECUTED` rather than partial results when:

- the official vintage cannot be frozen or reconciled;
- storage remains below the safe threshold;
- preferred models fail support or convergence in a way that changes the
  estimand;
- implementing V2 would require changing the dissertation's structure or
  adding an unapproved empirical question.

## Remaining execution sequence after gates open

1. Provision storage and isolated Python/R environments.
2. Freeze all official monthly source components and the compatible IPCA
   vintage.
3. Implement monthly or batched ingestion; do not load full years into
   memory or duplicate raw inputs into the work directory.
4. Validate raw domains, revisions, continuity, merges, and official
   totals before building the analytical panel.
5. Rebuild wages and composition fields with explicit zero-flow
   missingness.
6. Estimate the pre-specified national models and diagnostics.
7. Run support gates before any enriched CBO×CNAE or subgroup model.
8. Re-estimate only the dissertation's existing heterogeneity families.
9. Run independent Python–R comparisons and artifact lineage checks.
10. Update the existing manuscript structure and issue a new frozen
    release.
