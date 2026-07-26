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

## 2026-07-26 — HonestDiD target and sensitivity grid

Task 20 applies the installed `HonestDiD` implementation only to the two
linear outcomes: log real admission wage and asinh net balance. PPML event
studies are not converted to linear models or passed to `HonestDiD`.

The scalar target is the equally weighted average of the 24 post-treatment
event-study coefficients from event times 0 through 23. This target is fixed
before running the sensitivity analysis and is more representative of the
balanced post window than selecting one event month. The input vector retains
all 22 estimated pre-period coefficients from event times -23 through -2 and
the full cluster-robust covariance matrix exported by Task 19.

The sensitivity set is `DeltaRM`, implemented by
`createSensitivityResults_relativeMagnitudes` with the recommended `C-LF`
method, 95% confidence level, and a fixed `Mbar` grid from 0 through 2 in
increments of 0.05. The reported robustness value is the largest evaluated
`Mbar` whose robust interval excludes zero. If no interval excludes zero, the
result is reported as not robust even at `Mbar = 0`; if every interval
excludes zero, the result is reported as at least 2 rather than extrapolated
beyond the frozen grid.

## 2026-07-26 — HonestDiD results and open-grid disclosure

The average balanced-window asinh net-balance estimate is -3.3079. Its
original 95% interval is [-4.6931, -1.9227]. The `DeltaRM` robust interval
remains negative at `Mbar = 0.05`, [-6.1550, -0.5518], and includes zero at
`Mbar = 0.10`, [-8.1925, 1.4008]. The largest evaluated M that excludes zero
is therefore 0.05.

The average log real admission-wage estimate is -0.0154, with original 95%
interval [-0.0392, 0.0085]. Its HonestDiD interval includes zero already at
`Mbar = 0`, so no evaluated M supports an interval excluding zero.

At larger M values, `HonestDiD` warns that confidence intervals are open at
an internal test-inversion grid endpoint. The sensitivity CSV flags every
such row. The first open interval occurs at M=0.25 for asinh net balance and
M=0.20 for log real admission wage, after each outcome has already included
zero. The warnings therefore limit the reported width of high-M intervals
but do not determine either robustness threshold.

The vectorized 82-interval call exceeded memory and exited with code 137.
Running one M value at a time with garbage collection retained the exact
method, 1,000-point internal inversion grid, and numerical results while
holding memory stable. The serial run completed successfully; this
operational choice is encoded in the replication script.

## 2026-07-26 — DDD multiplicity family and subgroup contract

Task 21 defines one confirmatory multiplicity family before estimating any V2
heterogeneity coefficient. It contains 100 planned DDD contrasts: five
principal outcomes crossed with all 20 target-versus-complement groups in the
five existing dimensions (sex, Canaries age, race/color, education, and
pre-treatment occupational income). Missing or non-estimable rows remain in
the table and the adjustment retains the planned family size of 100.

Benjamini-Hochberg is the preregistered fallback selected by the plan.
Romano-Wolf is not used because this family mixes nonlinear PPML and linear
estimators across overlapping target-versus-complement samples; a single
valid joint resampling scheme is not available in the current estimator
contract. Every table reports the nominal cluster-t p-value and the global
BH-adjusted p-value side by side.

Every DDD formula contains exactly the focal
`post × treatment × subgroup` term plus all three two-way lower-order terms:
`post × treatment`, `post × subgroup`, and `treatment × subgroup`.
Micro-group models use CBO4, month, and target/complement fixed effects and
cluster by CBO4. Income groups are assigned at the CBO4 level and use CBO4
and month fixed effects under the same CBO4 clustering. No contemporary
composition controls enter these principal heterogeneity models.

Sex uses documented codes 1 (men) and 3 (women). Canaries age groups are
22-25, 26-30, 31-34, 35-40, 41-49, and 50+. Race/color uses white, black,
pardo, yellow, Indigenous, and the combined unidentified codes 6/9.
Education uses codes 1-5, 6-7, and 8-11/80. Each micro target is compared
with the complement of the other documented groups in its dimension; records
outside that dimension's declared groups are excluded rather than assigned
an invented category.

Income is a predetermined occupational characteristic. Each CBO4 is assigned
from its median positive-weight admission wage in minimum-wage units during
January 2021-November 2022: up to 2, over 2 through 5, and over 5 minimum
wages. This median is frozen before DDD estimation. Micro outcomes retain the
signed MOV + FOR - EXC weights and the Task 12 CBO-year wage bounds. Negative
subgroup count cells are a fail-fast condition; they are never clipped to
zero or silently dropped from PPML.

For the income dimension, both treatment and income group are predetermined
at the CBO4 level. Their lower-order interaction `treatment × subgroup` is
therefore time invariant within CBO4 and exactly absorbed by the CBO4 fixed
effect. The full DDD contract continues to declare all four interaction
terms, while the estimable design matrix records `treat_group` as absorbed.
This is the same collinearity that linear fixed-effect software removes
automatically; passing the redundant column to PPML instead produces a
singular matrix. Removing only this exactly absorbed column is an
identification correction, not specification selection.

## 2026-07-26 — DDD multiplicity results

All 100 preregistered DDD contrasts are estimable after recording the exactly
absorbed income lower-order term. There are zero negative signed subgroup
count cells. The generated panel has 815,813 rows and its SHA-256 is
`b8bf00bb27dea79403075b8bf567f42b817a923335c1062980076cc341849b6c`.

Thirty-four contrasts have nominal `p < 0.05`; 21 remain below 0.05 after the
global Benjamini-Hochberg correction with the frozen family size of 100.
These adjusted results remain exploratory because the national exact-model
pretrend diagnostics fail and because subgroup DDDs do not repair the
national identifying assumption.

Eighteen groups have adequate occupational support under the frozen 20
treated/50 control threshold. Middle-income occupations have limited support
(26 treated and 32 control CBOs). High-income occupations have thin support
(3 treated and 6 control CBOs). The high-income real-wage DDD remains
BH-significant but must be disclosed as thin-support evidence and not promoted
as a headline heterogeneity.

## 2026-07-26 — Placebo falsification contract

Task 22 is frozen before inspecting any placebo coefficient. The temporal
placebo uses the main 75-treated/266-control national sample, restricts the
data to the true pre-treatment period from January 2021 through November
2022, and assigns a false treatment start in December 2021. It re-estimates
the exact principal estimator family without contemporary controls: PPML for
admissions, separations, and gross movements; OLS for log real admission wage
and asinh net balance; CBO4 and month fixed effects; and CBO4-clustered
inference.

The blocking rule is intentionally conservative and applies to the complete
five-outcome national design: every temporal-placebo coefficient must have
`p >= 0.05`. If any one has `p < 0.05`, Checkpoint F fails, the group placebo
is recorded as `NOT EXECUTED`, and no Phase 6 model is run. The specification
will not be altered after seeing the falsification result.

Conditional on passing that gate, the group placebo reassigns exactly 75 of
the same 341 CBO4 families to treatment without replacement in each of 500
repetitions. The seed is `20260726`. Each repetition uses the full January
2021-May 2026 principal sample and the same outcome-specific estimators,
fixed effects, clustering, and no-control contract. For each of the five
outcomes, the report will locate the observed Task 18 principal coefficient
in the random-assignment distribution and provide its empirical percentile
and finite-sample-corrected two-sided randomization p-value.

## 2026-07-26 — Placebo falsification results

The blocking temporal placebo passes for all five principal outcomes.
Cluster-t p-values are 0.9205 for admissions, 0.1909 for separations, 0.5330
for gross movements, 0.0814 for log real admission wage, and 0.6791 for
asinh net balance. The wage placebo is the closest to the threshold, but it
remains above the frozen 5% rule. Checkpoint F therefore permits the group
placebo and Phase 6; no specification was changed in response.

All 500 group reassignments completed with exactly 75 treated and 266 control
CBO4 families in every repetition. The observed coefficients fall at
percentiles 16.6 for admissions, 13.8 for separations, 14.0 for gross
movements, 0.0 for log real admission wage, and 5.8 for asinh net balance.
The corresponding finite-sample-corrected two-sided randomization p-values
are 0.2994, 0.2954, 0.2715, 0.0020, and 0.0898. Thus the observed wage
coefficient is more negative than all 500 random assignments. This is a
group-label falsification result, not a remedy for the failed exact-model
pretrend diagnostics.

The initial repeated-estimation process was terminated by the operating
system with code 137 before the first ten-repetition checkpoint because the
reference estimator retained memory between fits. Loading the R estimator
under the same system pressure was also terminated before estimation. The
final randomization loop therefore uses an algebraically equivalent,
low-memory coefficient backend: iterative proportional fitting matches the
CBO4 and month margins and solves the PPML treatment score; two-way
Frisch-Waugh-Lovell residualization recovers the OLS coefficients. Cluster
covariance does not alter point estimates, and group-placebo inference comes
from the randomization distribution itself.

The first frozen random assignment was estimated by both the shared
reference estimator and the low-memory backend before the 500-repetition
run. Across the five outcomes, the maximum absolute coefficient difference
is `6.2833e-11`, below the `1e-8` parity tolerance. The complete comparison
is retained in `group_placebo_backend_validation.csv`; the backend change is
operational only and does not change assignments, samples, outcomes, fixed
effects, or estimands.

## 2026-07-26 — Separation-mechanism interpretation and family

Task 23 is frozen before inspecting any type-specific coefficient. The
separation family contains six mutually exclusive outcomes: dismissal
without cause (31), resignation (40), contract termination (43 and 45),
dismissal with cause or reciprocal fault (32 and 33), mutual agreement (90),
and unknown separation type (98). Retirement (50), death (60), and transfer
separations (80) are excluded from the substantive sum and reconciled
explicitly to the all-separation total.

The interpretation is directional and was specified in the plan. A decline
in dismissal without cause points to a firm-side retention decision. A
decline in resignations points instead to a worker-side reduction in outside
options. Contract endings, cause dismissals, agreements, and unknown types
remain separate mechanisms and will not be folded into either narrative.
These interpretations are conditional on design validity; the failed
national pretrend diagnostics continue to preclude strong causal language.

Each family outcome uses the principal national specification: PPML,
CBO4 and month fixed effects, CBO4-clustered inference, and no contemporary
controls. The static six-outcome family receives one global
Benjamini-Hochberg adjustment with frozen family size six. The complete
non-reference event-study coefficient family receives a separate global BH
adjustment; it is not pooled with the static tests. Support and reconciliation
are reported before coefficient interpretation.

## 2026-07-26 — Separation-mechanism results

The signed reconciliation is exact in every month and in total. The six
named families contain 118,723,283 separations; retirement, death, and
transfer exclusions contain 492,219; together they reproduce all 119,215,502
national-panel separations with zero residual. Transfer code 80 remains
absent, as already documented.

Dismissal without cause, the preregistered firm-retention margin, has an
essentially zero static estimate: coefficient -0.000020, effect -0.002%,
nominal `p = 0.9995`, and BH-adjusted `p = 0.9995`. The resignation margin
has the largest substantively interpretable decline: coefficient -0.116649,
effect -11.01%, nominal `p = 0.0749`, and BH-adjusted `p = 0.3299`.
Contract termination is -2.97% (`BH p = 0.7119`), dismissal with cause is
-14.33% (`BH p = 0.4237`), mutual agreement is -2.31%
(`BH p = 0.7119`), and unknown separation type is -18.96%
(`BH p = 0.3299`). No static mechanism survives the six-outcome adjustment.

The pattern therefore does not support a firm-retention account. At most, it
is descriptive evidence consistent with fewer worker-initiated exits and a
weaker outside option. That reading is not statistically robust after
multiplicity correction and remains non-causal because the national
pretrends fail. The complete dynamic table contains all 282 family-event
rows on the frozen -23 through +23 grid; 62 dynamic coefficients survive its
separate BH adjustment, which is interpreted as further time-pattern
instability rather than selected mechanism evidence.

Support is broad for the five substantive families. Unknown separation type
is thin: only 69 treated and 230 control CBOs ever have positive flow, and
PPML removes 2,614 static cells and 2,587 balanced-window cells for fixed
effects with no outcome variation. These removals are reported explicitly.

## 2026-07-26 — Cumulative net-flow index normalization

Task 24 cannot identify an employment-stock level without the out-of-scope
December 2020 RAIS anchor. A literal ratio of cumulative balance to the
January 2021 balance is also invalid: 63 of the 340 main-sample CBOs observed
in that month have a non-positive balance, including one zero. That
normalization would create undefined or directionally inverted indices.

The frozen proxy therefore completes the 341-by-65 CBO-month grid with zero
flows, accumulates net flows from January 2021, subtracts each CBO's January
2021 cumulative value so that the base month is exactly zero change, and
scales the change by that CBO's total gross movements during the full
pre-treatment period January 2021-November 2022. The reported index is
`100 + 100 × cumulative net-flow change / pre-treatment gross flow`.

One main-sample occupation, CBO 3227, has zero gross flow throughout the
pre-treatment period. Its grid is retained, but its normalized index is
missing and it is excluded from the index regression rather than assigned an
artificial denominator. The resulting model has 340 estimable CBOs.

This is an occupation-size-normalized cumulative net-flow index, not an
employment-stock index. It does not recover the unobserved initial stock and
does not capture exits outside Novo CAGED. The principal model is OLS with
CBO4 and month fixed effects, CBO4-clustered inference, and no contemporary
controls. Because Task 24 adds one planned contrast, its within-exercise BH
family size is one; nominal and adjusted p-values are still shown side by
side for the Checkpoint G contract.

## 2026-07-26 — Cumulative net-flow index result

The completed grid has 22,165 rows (341 CBOs by 65 months). CBO 3227 is the
only occupation without a valid pre-treatment flow scale, leaving 22,100
estimable observations and 340 CBO clusters. The five largest occupations by
pre-treatment gross flow were exported month by month for direct trajectory
inspection.

The principal estimate is +1.4292 index points with SE 1.3093,
`p = 0.2758`, and identical within-exercise BH-adjusted p-value. The estimate
does not provide statistically precise evidence of a differential cumulative
net-flow trajectory. It is not interpreted as a stock-level effect and does
not override the failed national pretrend diagnostics.

## 2026-07-26 — Hourly wage and work-schedule contract

Task 25 passes the pre-estimation continuity gate. Valid positive contracted
hours cover at least 97.61% of signed admissions in every month. The isolated
April 2022 dip immediately returns to 100% in May; the maximum adjacent
change is 2.39 percentage points, far below the preregistered structural-break
rule of a 10-point adjacent change or three consecutive months below 95%.

The official frozen layout defines `salário` as declared monthly salary and
`horascontratuais` as contracted weekly hours. The hourly measure is monthly
salary divided by five times weekly hours, the conventional monthly divisor
that maps 44 weekly hours to 220 monthly hours. Positive hourly values are
winsorized within CBO4-year at P1/P99 using the same signed-vintage principle
as the monthly wage outcome, then deflated with the frozen IPCA.

The five-outcome Task 25 family is frozen as log real monthly admission wage,
log real hourly admission wage, log weekly contracted admission hours,
partial-work admission share, and intermittent-work admission share. All
use the principal OLS CBO4 and month fixed-effects design, CBO4 clustering,
and no contemporary controls. Nominal p-values receive one global
Benjamini-Hochberg adjustment with family size five. Indicator code 9 and
missing values remain unknown and are excluded from the corresponding share
denominator rather than assigned to zero.

## 2026-07-26 — Hourly wage and work-schedule results

The continuity gate passes in the recomputed analytic sample: valid hours
coverage ranges from 97.67% to 100%, and the largest adjacent change is 2.33
percentage points. Partial-work known-code coverage ranges from 98.35% to
98.87%; intermittent-work coverage ranges from 95.03% to 100%.

The monthly real admission-wage coefficient reproduces the Task 18 estimate
exactly at -0.050740. The real hourly-wage coefficient is more negative at
-0.069508 (approximately -6.71%), with SE 0.016668, nominal
`p = 0.0000387`, and BH-adjusted `p = 0.0000967`. Weekly hours is +0.001552
(`BH p = 0.5624`), the partial-work share is -0.000779
(`BH p = 0.6880`), and the intermittent-work share is +0.000746
(`BH p = 0.8226`).

The descriptive decomposition therefore places the wage difference on the
hourly-price margin rather than contracted hours, partial work, or
intermittent work. This does not restore causal interpretation: the exact
national wage event study fails the joint pretrend test, and HonestDiD loses
sign exclusion by `M = 0.10`.

## 2026-07-26 — Establishment size and employer-nature boundary

Task 26 uses the ten documented `tamestabjan` categories as separate
target-versus-complement DDD groups and crosses them with all five principal
outcomes, producing one frozen 50-contrast BH family. Each DDD includes
`post × treatment × size group` plus all three lower-order terms, CBO4,
month, and target/complement fixed effects, CBO4 clustering, and no
contemporary controls. Codes 90, 97, 98, and 99 are excluded from semantic
size assignment and reported in support.

The planned public-versus-private falsification is not identified by the
available fields. The official dictionary defines `tipoempregador` only as
CNPJ root (0), CPF (2), or non-identified (9), and
`tipoestabelecimento` only as CNPJ (1), CAEPF (3), CNO (4), CEI (5), or
non-identified (9). Neither is public/private. Category 101 explicitly
combines general employees with public employees hired under the CLT.

Consequently, employer and establishment registration-code support is
published, including the preserved undocumented codes, but the
public-versus-private coefficient is recorded as `NOT EXECUTED:
non-identifying source fields`. No registration category is relabeled as
public or private.

## 2026-07-26 — Establishment-size results

All ten documented size categories have positive flows in all 75 treated
CBOs and at least 257 control CBOs. All 50 preregistered DDD contrasts are
estimated. Three real-wage contrasts have nominal `p < 0.05`: zero employees
(+0.0277), 1-4 employees (+0.0262), and 500-999 employees (-0.0435). None
survives the global family adjustment; the smallest BH-adjusted p-value is
0.3757, and the family has zero adjusted rejections.

No size band is therefore promoted as a robust heterogeneity. The
registration support contains 240,580,596 signed CNPJ-root rows, 7,696,360
CPF rows, and the previously preserved 28 undocumented employer-code rows.
The establishment field likewise retains its single undocumented `-1` row.
The public-versus-private falsification remains not executed because these
counts do not add an ownership distinction.

## 2026-07-26 — Exposure-measure sensitivity contract

Task 27 is frozen before estimating any alternative-measure coefficient. The
family contains fifteen estimates: the five principal outcomes under each of
three alternative exposure definitions. Nominal p-values receive one global
Benjamini-Hochberg adjustment across all fifteen estimates. Every definition
uses CBO4 and month fixed effects, CBO4-clustered inference, the full
January 2021-May 2026 window, and no contemporary controls.

The 2023 vintage uses the workbook's native `potential23` categories rather
than retrofitting the 2025 gradient thresholds. For every CBO4, the category
is the equal-destination mode across its mapped ISCO-08 occupations; ties are
resolved conservatively toward `Not affected`, then `Augmentation Potential`,
then `Automation Potential`, with the workbook's `The Big Uknown` category
last. Only `Automation Potential` and `Not affected` enter the binary
treated-control estimate. The corresponding `mean_score_2023` and `SD_2023`
are retained and summarized as measurement support.

For model agreement, GPT-4o and Gemini task predictions are aggregated
separately to ISCO-08 means and population standard deviations and classified
with the frozen 2025 mean-plus-dispersion rule. An ISCO destination is retained
only when the two complete gradient labels agree. CBO4 exposure is then
recalculated from the frozen 2025 mean and SD over those consensus
destinations. The resulting exposed-versus-`Not Exposed` estimate is a
restricted-support robustness check, not a replacement classification.

The Anthropic exercise uses `anthropic_automation_index` as a standardized
continuous CBO4 measure, so its interaction coefficient is per one
cross-occupation standard deviation. `zero_imputation_no_data` rows and the
non-CBO `Grupo de base` row are excluded: a technical zero without source
evidence is not interpreted as observed zero exposure. Rank agreement with
the continuous 2025 ILO score is reported both for direct Anthropic matches
and for all direct plus hierarchical matches. Because the Anthropic measure
contrasts automation with augmentation rather than total generative-AI
exposure, its coefficient has a different substantive scale and is not
treated as a numeric replication of the binary ILO estimate.

## 2026-07-26 — Exposure-measure sensitivity results

All fifteen Task 27 models converged. The native 2023 comparison has limited
treated support: 10 `Automation Potential` CBO4 families versus 310 `Not
affected` families. Its five adjusted p-values exceed 0.18. The three flow
coefficients and admission-wage coefficient remain negative, but none is
promoted as a robust effect under this thin treated support.

GPT-4o and Gemini agree on the complete gradient label for 321 of 427 ISCO-08
occupations. The resulting CBO4 consensus sample contains 59 treated and 271
control families. The real admission-wage coefficient is -0.056058 with SE
0.011816 and global BH-adjusted `p = 0.0000468`; it is the only adjusted
rejection in the fifteen-estimate family. The flow and net-balance contrasts
do not reject at 5%.

The Anthropic sample contains 168 CBO4 families after excluding source-free
zero imputations. Its automation-minus-augmentation rank correlation with
the 2025 ILO exposure score is -0.1214 for 92 direct matches and -0.0802 for
127 direct plus hierarchical matches. Per one standard deviation of the
Anthropic index, all three flow coefficients are within 0.003 log point of
zero. The wage coefficient is -0.019817 with BH-adjusted `p = 0.1847`.

These results retain the frozen ILO 2025 classification as the principal
measure. The consensus result shows that the negative admission-wage pattern
is not driven by occupations where GPT-4o and Gemini assign different
gradient classes. The Anthropic result is interpreted as weak agreement
between distinct constructs, not as a failed replication of total exposure.
Checkpoint G is complete for executed mechanisms: every new estimated
exercise has support and adjusted p-values. The planned public/private
falsification remains explicitly not executed because the official source
fields do not identify ownership.

## 2026-07-26 — Independent Python-R cross-replication

Task 31 exports the exact 22,049-row principal sample and independently
re-estimates the five central outcomes in R. The R implementation does not
call Python or `pyfixest`: the three PPML models use iterative proportional
fitting, and the two linear models use alternating two-way
Frisch-Waugh-Lovell projections. Both covariance calculations use an
independent CBO4-clustered CRV1 score sandwich.

The small-sample correction counts the 65 month effects plus the treatment
regressor while excluding CBO4 effects nested within the CBO4 cluster. This
reproduces the `pyfixest` correction rather than relying on a package default.

All five models have identical sample sizes and 341 CBO4 clusters. The
maximum absolute Python-R coefficient difference is
`1.1209513178789265e-10`; the maximum standard-error difference is
`1.2007179972517434e-11`. Coefficients and standard errors therefore agree
well beyond the required six decimal places, including real admission wage.
