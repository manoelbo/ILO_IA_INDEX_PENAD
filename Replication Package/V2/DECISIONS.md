# V2 Decision Log

This file is append-only. Decisions are recorded before the affected
estimations or data transformations run.

## 2026-07-25 — Fixed Novo CAGED cutoff

The official-data vintage ends at May 2026. The inventory must contain exactly
65 monthly competencies from January 2021 through May 2026 and exactly 195
MOV/FOR/EXC archives. June 2026 is excluded even if it becomes available
during execution because it would be the least complete month and adds
negligible information after 42 post-treatment months.

## 2026-07-25 — V1 verification environment

The literal command `uv run --with pytest pytest tests/ -q` installs pytest but
not V1's pinned scientific dependencies, so it fails during collection on a
missing `pandas` import. The unchanged V1 suite is therefore executed from the
V1 directory with the provisioned V2 environment:

```bash
../V2/.venv/bin/pytest tests/ -q
```

This operational correction changes neither V1 code nor its test semantics.

## 2026-07-25 — OPEN: undocumented `tipoempregador = 1`

Task 6 is paused by the domain fail-fast gate. The frozen official layout
defines `tipoempregador` as `{0, 2, 9}`, but the frozen May 2026 archives
contain the undocumented code `1`:

- MOV: 67 rows;
- FOR: 17 rows;
- EXC: 3 rows.

All 67 MOV records are in CNAE section `O`, use `tipoestabelecimento = 1` and
`origemdainformacao = 1`, and are concentrated in UFs 14, 16, 53, and 11.
This evidence does not identify the code's official meaning.

No rows were dropped, remapped, or admitted into the parser domain. Execution
is paused pending an author decision. The least-assumptive proposed resolution
is to preserve code `1` as an observed undocumented category, accept it without
semantic remapping, and report its monthly continuity explicitly in Task 9.

## 2026-07-26 — RESOLVED: preserve undocumented employer code

The author approved the least-assumptive resolution. `tipoempregador = 1` is
accepted as an observed undocumented category and preserved without remapping.
It remains in all national aggregates, is audited month by month in Task 9,
and is reported separately rather than assigned to either side of the
public-versus-private contrast in Task 26.

## 2026-07-26 — OPEN: same-month exclusion records

Task 7 is paused by the preregistered temporal-domain check. The plan states
that EXC facts must be strictly earlier than the archive month, but the frozen
official vintage contains 11 same-month exclusions:

- `CAGEDEXC202101`: 6 rows with `competenciamov = competenciaexc = 202101`;
- `CAGEDEXC202102`: 5 rows with `competenciamov = competenciaexc = 202102`.

No EXC archive contains a fact month later than its archive month, and the
remaining 63 EXC archives satisfy the strict-earlier relationship.

No record has been discarded or moved to another fact month. The proposed
resolution is to accept `competenciamov <= competencia_arquivo` for EXC only,
preserve all 11 rows with weight `-1` in their stated fact month, keep FOR
strictly earlier, and add an explicit same-month EXC count to the Task 9
continuity audit.

## 2026-07-26 — RESOLVED: preserve same-month exclusions

The author approved the proposed temporal rule. EXC records may satisfy
`competenciamov <= competencia_arquivo`; the 11 observed same-month exclusions
remain in their stated fact month with weight `-1`. Future-dated EXC records
remain invalid, FOR remains strictly retroactive, and same-month EXC counts are
carried into the reconciliation output for the Task 9 continuity audit.

## 2026-07-26 — OPEN: undocumented `tipoestabelecimento = -1`

Task 7 stopped at the domain fail-fast gate while parsing
`CAGEDMOV202506.7z`. The frozen official layout defines
`tipoestabelecimento` as `{1, 3, 4, 5, 9}`, but this archive contains one row
with the undocumented value `-1`.

The row is a June 2025 separation (`tipomovimentacao = 31`) in CBO 5121. Its
geography and industry fields also use non-identified values
(`regiao = 99`, `uf = 99`, `municipio = 999999`, `secao = Z`,
`subclasse = 9999999`). The employer type is the documented CPF code `2`.
This evidence does not establish an official semantic meaning for `-1`.

No row was dropped, remapped, or admitted into the parser domain. The
least-assumptive proposed resolution is to preserve `-1` as an observed
undocumented establishment-type category, accept it without semantic
remapping, retain the row in national flow aggregates, and audit the code by
fact month before any public-versus-private exercise in Task 26.

## 2026-07-26 — RESOLVED: preserve undocumented establishment code

The author approved the proposed resolution. `tipoestabelecimento = -1` is
accepted as an observed undocumented category and preserved without remapping.
The row remains in national flow aggregates, the code is audited by fact month
in Task 9, and it is not assigned to either side of the public-versus-private
contrast in Task 26.

## 2026-07-26 — Full-window rule after completeness diagnostics

Task 9 uses late declarations divided by same-month MOV rows (`FOR / MOV`), the
same denominator as the frozen audit. Across the 12 fact months that have had
fewer than 12 opportunities to receive late declarations, the maximum absolute
difference between the 75 treated and 266 control CBO4 groups is 0.281
percentage points, in June 2025. This is below the preregistered 1 percentage
point threshold.

Window rule A is therefore selected before any model is estimated: retain the
full January 2021-May 2026 window and include month fixed effects. No recent
months are trimmed. The progressively incomplete tail remains disclosed in the
completeness outputs.

## 2026-07-26 — Transfer and undocumented-code continuity

Task 9 finds zero physical rows with transfer codes 70 or 80 in the full
January 2021-May 2026 analytic vintage. The P0.9 transfer filter is therefore
inert and remains documented rather than removed.

The approved `tipoestabelecimento = -1` category occurs exactly once, in June
2025. The approved undocumented `tipoempregador = 1` category has a signed
total of 6,910 rows across 43 fact months. Both remain separate categories and
are excluded from semantic public-versus-private assignment in Task 26.

## 2026-07-26 — External Checkpoint B review and corrected FOR benchmark

The author independently re-aggregated the 77 signed movement partitions
instead of relying on the generated reports and reproduced the 2021 totals
exactly: MOV 36,554,795, FOR 2,680,702, EXC 132,425, and net movements
39,103,072.

The external review also established that `ano` in the Base dos Dados
`microdados_movimentacao_fora_prazo` table refers to the declaration
competency, not the fact competency. Aggregating the frozen FTP FOR archives
by archive year reproduces the Base dos Dados counts exactly, including
3,148,673 rows in 2021 and 1,314,097 in 2022. This independently validates the
FTP extraction in a second time dimension.

The original approximately 8% acceptance benchmark mixed declaration and fact
reference periods. The corrected 2021 fact-month benchmark is 7.33% gross FOR
relative to MOV and 6.97% net after EXC. The observed V2 result matches both
corrected benchmarks.

## 2026-07-26 — Disclosure direction for recent completeness

The full-window rule A remains unchanged. In 11 of the 12 recent incomplete
months, the treated-minus-control FOR/MOV difference is non-positive; the
range is -0.281 to +0.073 percentage points and the maximum absolute
difference is 0.281 percentage points in June 2025. Controls therefore have
slightly more pending late declarations than treated CBOs, in the same
direction as the V1 bias but roughly one order of magnitude smaller.

This does not cross the preregistered 1 percentage point trimming threshold.
The future dissertation text must disclose the direction and magnitude even
though no tail months are removed.

## 2026-07-26 — RESOLVED: PDET adjusted-series reconciliation

The V1 MOV identity validates the parser, and the Base dos Dados FOR identity
validates extraction, but neither test validates reassignment from declaration
month to `competenciamov`. Checkpoint B therefore required a direct comparison
of V2 admissions, separations, and net balance with the official adjusted PDET
Novo CAGED series.

The frozen May 2026 PDET workbook, sheet `Tabela 5.1 - com ajustes`, covers all
65 fact months from January 2021 through May 2026. Every V2 monthly admission,
separation, and balance value is exactly identical to the official series:
zero differing months, zero maximum absolute difference, and zero cumulative
absolute difference for all three outcomes.

As a direct reassignment diagnostic, shifting the official series one month
backward or forward produces a total absolute discrepancy of 28,189,094,
while the zero-shift comparison produces zero. The central
`competenciamov` reassignment logic is therefore externally validated and no
systematic one-month bug is present. The PDET gate is closed, so Task 14 may
now be estimated and interpreted under the remaining preregistered gates.

## 2026-07-26 — National-panel wage bounds and new CBO coverage

Task 12 winsorizes valid positive nominal wage records at approximate P1/P99
within CBO4 and calendar year before aggregation. The same pooled
occupation-year bounds are applied to admissions and separations. Bounds are
computed from positive-weight records so exclusion rows do not create new
quantile mass; all signed rows use the resulting bounds when flow and wage
totals are aggregated.

The refreshed vintage contains one valid CBO4 family, `2414`, that is absent
from the 629-family frozen V1 treatment universe. It appears in five cells and
has one signed movement in each. The family is preserved as `No score`, with
`treated_main` missing and `included_main = false`. The 629 frozen treatment
assignments remain unchanged; no live MTE query or inferred match was used.

## 2026-07-26 — Sector-panel CNAE hierarchy and declared exception

Task 13 freezes the official IBGE CNAE 2.0 structure by file hash and carries
both subclass-derived division and section into the sector panel. The official
dictionary contains 87 divisions in 21 sections. The sector aggregation
reproduces every Task 12 CBO4-month admission and separation count exactly,
with zero duplicate keys and zero missingness-rule violations.

One administrative category is outside that dictionary:
`secao = Z, subclasse = 9999999`. It occurs in 1,093 valid signed rows with a
net signed weight of 1,047. This is a declared exception to the all-official
CNAE-domain criterion. The records are preserved as the explicit
`divisao = ZZ, cnae_status = undocumented_preserved` bucket and are never
remapped to official section U or official division 99. Any sector model must
exclude or separately disclose this bucket rather than assign it an invented
economic meaning.

The resulting panel has 6,124,959 CBO4-subclass-month cells. Of 85,043
subclass-month cells, 80,087 (94.17%) contain both treated and control CBO
families. The generated 279 MiB Parquet is retained as a hashed local
replication artifact rather than committed as a Git blob; its SHA-256 and byte
size are recorded in the Task 13 support report.

## 2026-07-26 — Task 14 reference measurement

Task 14 was estimated only after the adjusted PDET monthly-series gate closed.
The exact V1 specification, sample window, treatment contrast, controls, fixed
effects, and cluster estimator were held fixed. No coefficient changes sign.
The real admission-wage coefficient moves from -0.020706 (SE 0.013992,
`p = 0.1398`) to -0.046974 (SE 0.010317, `p = 0.00000738`) and is the only
outcome to cross the 5% significance threshold.

The V2 coefficients for log admissions, log separations, and asinh net balance
are -0.024528, -0.033882, and -0.607197, respectively. The literal model
retains 18,281 V2 observations and the same 341 CBO4 families, versus 18,307
observations in the frozen V1 reference. Checkpoint C remains non-blocking:
the result is disclosed and does not authorize specification selection.

## 2026-07-26 — Preregistered treatment-variant aggregation

Variant A is the principal treatment classification and remains exactly the
frozen Task 11 rule. Variants B, C, and D are sensitivity analyses only. No
variant may replace A because of its coefficient, standard error, or
significance.

Employment weights for variants B and D are signed pre-treatment admissions
from January 2021 through November 2022 at the CBO6 level, under the same
record-domain restrictions as the national panel. When one CBO6 maps to
multiple scored ISCO-08 destinations, its admission weight is divided equally
among those destinations. CBO6 records without a scored destination do not
receive an invented allocation. If a scored CBO4 has no positive matched
pre-treatment weight, equal destination weights are used and the fallback is
flagged.

Variant B uses those destination weights for the CBO4 mean and for the pooled
within-task plus between-destination standard deviation. Variant C retains the
equal-weight mean but uses only pooled ILO within-task dispersion,
`sqrt(mean(SD_ILO^2))`, in the threshold rule; the between-destination
standard deviation is reported separately and never folded back into the
classification.

Variant D classifies each ISCO-08 destination using its native ILO label and
aggregates labels by weighted mode. A tie is resolved toward the less exposed
label, a conservative deterministic rule fixed before estimation. The same
equal-weight fallback applies only when a scored CBO4 has no positive matched
pre-treatment weight.

## 2026-07-26 — Treatment-variant classification results

Variant A reproduces the frozen 0/31/31/13/95/266/193 classification exactly.
Relative to A, employment-weighted variant B changes 8 CBO4 families,
task-only-dispersion variant C changes 16, and native-label variant D changes
53. Variant D is the only sensitivity that assigns any CBOs to Gradient 4
(three families). Two scored CBO4 families have no positive matched
pre-treatment CBO6 weight; their documented equal-weight fallback leaves
their `Not Exposed` classification unchanged in every variant.

The pre-treatment weight frame contains 41,597,337 signed valid admissions;
32,826,892 (78.92%) belong to CBO6 codes with a scored destination in the
frozen crosswalk. This coverage is reported rather than extrapolated to
unscored occupations.

CBO 4121 reaches ISCO-08 targets 3341, 4131, and 4132. Target 4132 has the
highest frozen ILO mean score, 0.70, but it is not the CBO's only destination.
A, B, and C classify the family as Gradient 3. In D, weighted native-label
mass is tied exactly between Gradient 2 and Gradient 4; the preregistered
less-exposed tie rule therefore yields Gradient 2. This is a sensitivity
result, not a basis for replacing A.

## 2026-07-26 — Cluster-t inference for the shared estimator

The shared estimator accepts fixed effects and one- or two-way cluster
dimensions as parameters. Principal specifications reject contemporaneous
admission-composition controls at runtime. Count models use `fepois`; log real
admission wage and asinh net balance use OLS.

`pyfixest` reports normal-reference intervals for nonlinear models by default.
The V2 reporting layer instead applies the preregistered cluster-t rule to the
coefficient and cluster-robust standard error: degrees of freedom equal the
smallest cluster count minus one, including under two-way clustering. The
reported p-value and confidence interval therefore use the same t reference.
Model records also expose convergence, separation removals, complete-case
loss, other estimator removals, N, and cluster counts.

## 2026-07-26 — Single balanced event-time convention

All V2 dynamic models use December 2022 as event time zero, November 2022 as
the omitted `t = -1` reference, and the complete symmetric grid from `t = -23`
through `t = +23`. No endpoint coefficient pools heterogeneous months. The
balanced grid therefore runs from January 2021 through November 2024 for every
outcome.

Long-run summaries are named separately and never substituted for event-time
coefficients: December 2022-November 2023, December 2023-November 2024,
December 2024-November 2025, and December 2025-May 2026. The last horizon is
marked partial. All three event-study PPML models converge with zero
separation removals; the count and net-flow grids retain 15,935 cells, while
the valid real-admission-wage grid retains 15,907.

## 2026-07-26 — Complete national specification ladder

All seven preregistered Task 18 steps and all five outcomes were estimated and
exported. All 35 models converge, no PPML observation is removed for
separation, and no step is omitted. The no-control benchmark estimates PPML
effects of -5.24% for admissions, -4.11% for separations, and -4.70% for gross
flows; none is statistically significant at 5%. Its log real admission-wage
coefficient is -0.050740 (SE 0.010332, cluster-t `p < 0.00001`), while the
asinh net-balance coefficient is -0.551267 (SE 0.378317).

The real admission-wage coefficient remains negative and significant in every
step, including standardized continuous exposure. Including `Minimal
Exposure` in the control group yields significant negative admissions and
gross-flow estimates, but this is retained only as a declared sample
sensitivity and is not promoted over the frozen principal contrast.
Contemporary-composition results remain labeled descriptive and potentially
post-treatment.

## 2026-07-26 — Sector fixed-effect ladder

The sector support table was frozen before coefficient estimation. Every one
of the 1,365 section-month cells contains treated and control CBOs, with
median counts of 61 and 138, respectively. Level 3 is much thinner: its
observation-count p10 is one and only 32.33% of section-month-CBO2 cells have
both groups. It nevertheless retains 55 treated CBOs in coexisting cells,
above the preregistered threshold of 20, so it is estimable but remains a
fragile support diagnostic.

The co-principal level 2 estimates are -0.075076 for admissions, -0.066446 for
separations, -0.070665 for gross flows, -0.035598 for log real admission wage,
and -0.139494 for asinh net balance. Relative to level 1, sector adjustment
makes all three flow coefficients more negative, attenuates the wage
coefficient, and sharply attenuates net balance. This difference is reported
as a change in estimand, not used to choose a preferred result.

With CBO-only clustering, level 2 admissions and gross flows cross 5%.
Two-way clustering across 341 CBO4 and 87 official CNAE divisions raises
their p-values to 0.0538 and 0.0643; separations has `p = 0.0855`. The wage
coefficient remains statistically precise (`p < 0.00001`). Bidirectional
standard errors are larger for all five outcomes and remain a robustness
result rather than the principal inference.

The official division panel excludes the declared undocumented Z/ZZ bucket,
removing exactly 583 admissions and 464 separations already disclosed in
Task 13. All 15 sector models converge. PPML removes 161 separated admission
cells and 70 separated separation cells; singleton and missing-outcome losses
are recorded per model.

## 2026-07-26 — Exact-model pretrend classification

Task 19 keeps the Task 17 balanced event-study model unchanged: the same
January 2021-November 2024 window, November 2022 reference, estimator, CBO4
and month fixed effects, complete-case sample, and CBO4 cluster dimension.
Every diagnostic must reproduce the event-study N and cluster count exactly.

Three distinct diagnostics are reported and must not be described as the same
test:

1. a cluster-robust Wald test that all 22 estimated leads from event times
   -23 through -2 equal zero;
2. a generalized-least-squares linear slope through the omitted event-time
   -1 reference, estimated from those same leads and their full cluster-robust
   covariance matrix;
3. a dynamic lead inspection that counts individually significant leads at
   5% using the same cluster-t reference as the coefficient table.

The outcome classification is frozen before running the diagnostics. It is
`fail` if either formal test has `p < 0.05` or at least two individual leads
have `p < 0.05`; it is `pass` only if both formal tests have `p > 0.10` and no
individual lead has `p < 0.05`; all other cases are `warning`. A
non-significant diagnostic is never interpreted as proof of parallel trends.

## 2026-07-26 — Exact-model pretrend results

All five outcomes fail the preregistered Task 19 classification. The joint
lead Wald p-values are below 0.001 for admissions, separations, gross flows,
real admission wage, and asinh net balance. The linear-slope test also rejects
for all three PPML flow outcomes, but not for real admission wage or asinh net
balance. This divergence is retained as evidence that the joint, linear, and
dynamic diagnostics answer different questions.

Each re-estimated dynamic model exactly matches the reported Task 17 sample:
15,935 cells and 341 CBO4 clusters for the three count outcomes and asinh net
balance, and 15,907 cells with the same 341 clusters for real admission wage.
No result is removed or re-specified in response. Task 22 remains the formal
blocking gate, but every Task 19 result requires non-causal language unless a
later design resolves the identifying concern under a separately
preregistered analysis.
