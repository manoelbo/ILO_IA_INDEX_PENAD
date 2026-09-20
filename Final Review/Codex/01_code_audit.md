# Code and Replication-Package Audit

## Verdict

**Major revisions required. Readiness: 5/10.**

The V1 package has a strong operational shell: one entry point, relative
paths, pinned dependencies, frozen analytical inputs, explicit treatment
roles, automated validation, and 16 passing tests. A clean temporary copy
also reproduced 116 non-figure artifacts with exit code zero.

That operational success is not equivalent to complete scientific
replication. Only four national models are re-estimated in `reproduce`
mode. Most event studies, pretrend tests, DDD models, heterogeneity
estimates, Poisson models, real-wage estimates, and occupation-case
outputs are copied or rendered from frozen backing CSVs. Six material
problems remain open.

There is no single code defect that invalidates every result. The four
central national coefficients were independently reproduced in Python
and R. Nevertheless, the current package should not be treated as a
publication-ready computational authority for all claims in the
manuscript.

## Scope and evidence

The audit covered:

- every file reached from `run_replication.py`;
- the packaged author DAG under
  `code/sections4_5/author_pipeline/`;
- frozen derived inputs and reference outputs;
- package tests, manifests, path handling, and output comparison;
- construction, merges, missingness, treatment assignment, outcomes,
  fixed effects, clustering, dynamics, DDD, and count-model robustness;
- an independent Python–R replay of the four central national models.

Evidence is preserved in:

- `evidence/baseline_manifest.csv`;
- `evidence/baseline_context.json`;
- `evidence/independent_replication/comparison.csv`;
- `evidence/logs/`;
- the frozen package at `Replication Package/V1/`.

## Reproduction results

| Check | Result |
| --- | --- |
| Package tests | 16/16 pass |
| Temporary-copy reproduction, no figures | Exit 0; 116 files |
| Central models independently replayed | 4/4 pass |
| Python–R retained observations | Identical: 18,307 |
| Python–R clusters | Identical: 341 CBO4 |
| Maximum cross-language numeric difference | Approximately `2.2e-12` |
| Full raw-data rebuild | Not established |
| Full independent replay of every inferential table | Not established |

The independent replay validates the frozen-sample coefficients for log
admissions, log separations, log admission wage, and `asinh(net flow)`.
It does not validate the event studies, subgroup models, DDD estimates,
or occupation-case analyses.

## Major findings

### C-A01 — Appendix A.6 is semantically wrong

**Severity: major**

The outputs named as income diagnostics are built with education data.
The publication loader reads both income and education sources, but the
A.6 calls pass `education`:

- `Replication Package/V1/code/sections4_5/publication.py:215`;
- `Replication Package/V1/code/sections4_5/publication.py:335`;
- `Replication Package/V1/code/sections4_5/pipeline.py:239`;
- `Replication Package/V1/code/sections4_5/contracts.py:223`.

The generated A.6 rows are education categories such as “Fundamental ou
menos”, “Médio”, and “Superior”, not income bands. Tests pass because the
reference directory contains the same wrong output. Byte identity has
therefore validated a semantic error.

**Consequence:** the package cannot computationally support the
manuscript's income appendix until the source mapping and semantic
contract are corrected.

### C-A02 — `reproduce` is mostly a frozen-output renderer

**Severity: major**

The public pipeline copies 48 backing files and renders publication
artifacts from them. Only four national models are re-estimated:

- `Replication Package/V1/code/sections4_5/pipeline.py:66`;
- `Replication Package/V1/code/sections4_5/analysis.py:65`.

The independent replay target also uses `ln_salario_adm`, while the
published narrative describes real admission wages. Month fixed effects
make the current coefficient numerically equal under the frozen data,
but the validation target is still semantically mislabelled.

**Consequence:** successful `reproduce` execution proves packaging and
rendering integrity, not independent reconstruction of most estimates.

### C-A03 — Main controls may be post-treatment variables

**Severity: major**

The preferred specification includes contemporaneous monthly mean age
and shares of women, higher education, and Black workers among
admissions:

- `Replication Package/V1/code/sections4_5/author_pipeline/src/scripts/section4_event_study/config.py:33`;
- `Replication Package/V1/code/sections4_5/author_pipeline/src/scripts/section4_event_study/estimation.py:46`.

If exposure affects the composition of admissions, these variables may
be mediators or colliders. Predetermined controls interacted with the
post period exist in the code, but are not the preferred specification:

- `Replication Package/V1/code/sections4_5/author_pipeline/src/scripts/section4_event_study/data.py:95`;
- `Replication Package/V1/code/sections4_5/author_pipeline/src/scripts/section4_event_study/pipeline.py:1140`.

**Consequence:** the current preferred coefficient may condition on an
outcome of treatment. A no-contemporaneous-control model should be the
main specification, with predetermined alternatives as robustness.

### C-A04 — Zero-flow cells receive artificial wage values

**Severity: major**

After outer joins, the author pipeline fills missing values with zero
for wages and demographics, then winsorizes admission wages:

- `Replication Package/V1/code/sections4_5/author_pipeline/src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py:783`;
- `Replication Package/V1/code/sections4_5/author_pipeline/src/scripts/etapa_2b_analise_did_caged_ilo.py:194`.

In the frozen panel:

- 62 cells with zero admissions have the same positive mean admission
  wage (`1,104.7868`); 31 enter the main sample;
- those cells carry zero-valued demographic controls;
- 44 zero-separation cells have a zero separation wage;
- separation wages reach approximately R$203.3 million, with seven
  cells above R$1 million in the main sample.

**Consequence:** wage outcomes and composition controls are not
well-defined in zero-flow cells, and extreme invalid values survive.
Salary models require a rebuilt missingness and domain-validation
contract.

### C-A05 — `full` is a hybrid rebuild, not complete raw lineage

**Severity: major**

The full DAG injects frozen derived assets, including exposure, IPCA,
dynamic pairs, and occupation metadata:

- `Replication Package/V1/code/sections4_5/full_pipeline.py:269`;
- `Replication Package/V1/code/sections4_5/pipeline.py:202`.

Some provenance exists in the workspace, but the public final manifest
does not carry source URLs, retrieval dates, raw hashes, schemas, and
complete stage-level input/output lineage for all injected assets.

**Consequence:** `full` cannot yet be interpreted as reconstruction of
all public results from fully identified raw sources.

### C-A06 — Main flow models fail their pretrend diagnostics

**Severity: major**

The national diagnostic table marks admissions, separations, and net
flow as failed pretrends:

- `Replication Package/V1/results/reference/sections4_5/tables/table_a_1_national_main_diagnostics.csv:2`;
- `Replication Package/V1/README.md:577`.

**Consequence:** null or non-null post-treatment coefficients do not
repair identification. General causal language about flow effects is
not supported by the current design.

## Moderate findings

### C-A07 — Endpoint clipping pools heterogeneous months

Event time is clipped to `[-12,+24]` in
`author_pipeline/src/scripts/section4_event_study/estimation.py:175`.
The `-12` coefficient pools months `-23…-12`, and `+24` pools months
`24…30`. Public strict-window figures use a different sample and
estimand. Labels do not consistently communicate the pooling.

### C-A08 — Crosswalk sources are not cryptographically versioned

The institutional chain is conservative and prohibits numeric
CBO=ISCO fallback, but mutable online inputs can be used to reconstruct
the cache. Expected counts are checked; content hashes and source
vintages are not public contractual inputs.

### C-A09 — Merge and missingness contracts are incomplete

The frozen panel has no duplicate CBO4-month rows, but it is unbalanced:
individual CBOs have between 8 and 54 months. Current gates do not
systematically assert merge cardinality, unmatched counts, row deltas,
outcome missingness, control missingness, or balanced-window support.

### C-A10 — Demographic definitions diverge across modules

The aggregate panel defines completed higher education with codes
`{9,10,11,80}`, while a heterogeneity module also includes code `8`.
Unknown or missing sex is included in the denominator as non-female,
and the `60+` category has no enforced upper bound.

### C-A11 — Section 3 input validation is incomplete

The Section 3 builder ignores missing period values when asserting
2025Q3 and does not require finite positive weights or validate the
domain of every demographic code.

### C-A12 — Reference outputs are not an independent anchor

The package compares regenerated artifacts with the current
`results/reference` directory but does not first cryptographically
validate that directory against `reference_manifest.json`. PNG
comparison uses dimensions and thumbnail grayscale RMS, which can miss
localized material changes.

## Confirmed strengths

- The principal contrast is implemented as 75 G1–G3 CBO4 occupations
  against 266 `Not Exposed` occupations.
- `Minimal Exposure` and `No score` are excluded from the main contrast.
- No G4 CBO4 is observed, and the code exposes that fact.
- Static and dynamic DDD code includes the triple interaction and all
  lower-order terms.
- Standard errors are clustered by CBO4.
- Relative paths, one entry point, pinned requirements, isolated output
  directories, and manifests provide a sound packaging foundation.
- The official crosswalk chain is explicit and does not equate missing
  exposure with zero exposure.
- Section 3 pins the ILO workbook SHA-256 and reports weighted coverage
  diagnostics.

## Audit conclusion

The package is useful and substantially better than an unreproducible
notebook archive, but it currently combines three different concepts:

1. true model re-estimation for four national outcomes;
2. validation of frozen backing tables;
3. deterministic rendering of publication artifacts.

These must be labelled separately. V1 should remain frozen as evidence
of the submitted baseline. Material corrections belong in V2, with a
new immutable data vintage and a complete model-to-artifact DAG.
