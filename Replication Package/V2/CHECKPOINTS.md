# V2 Checkpoint Log

## Checkpoint A — Foundation

Status: **PASS** on 25 July 2026.

Evidence:

- Python environment: `uv sync` completed with the locked Python 3.10
  environment, and the required import gate printed `ok`.
- `pyfixest`: version 0.40.1 imported successfully.
- R environment: `fixest` 0.14.0, `HonestDiD` 0.2.6, and `data.table`
  1.17.0 loaded successfully under R 4.4.1.
- V1 baseline: all 16 tests passed from `Replication Package/V1/`.
- V1 dry-run: the complete Sections 3–5 DAG printed successfully from the
  moved V1 directory.
- Storage: 54 GiB was available after environment provisioning, above the
  blocking minimum of 15 GiB.
- Freeze: `V1/FROZEN.md` is the only file added to the frozen V1 tree during
  this execution.

Operational note: Homebrew Rust was upgraded from 1.81.0_1 to 1.97.1 because
the older `cargo` binary referenced a removed `libgit2.1.8.dylib` and could not
build the pinned `pyfixest` wheel.

## Checkpoint B — Official vintage and reassignment

Status: **PASS** on 26 July 2026 after closing the PDET pendency.

Evidence:

- all 77 signed fact-month partitions were independently re-aggregated;
- the 2021 identity is 36,554,795 MOV + 2,680,702 FOR − 132,425 EXC =
  39,103,072 net movements;
- aggregating FOR by archive year reproduces the Base dos Dados
  declaration-year counts exactly, including 3,148,673 rows in 2021 and
  1,314,097 in 2022;
- the corrected like-for-like benchmark is 7.33% gross and 6.97% net, rather
  than the original approximately 8% mixed-period threshold;
- the official PDET adjusted monthly series matches V2 exactly in all 65
  months for admissions, separations, and balance;
- shifting the official series one month backward or forward creates a total
  absolute discrepancy of 28,189,094, rejecting a silent one-month
  reassignment error;
- recent treated-minus-control completeness ranges from -0.281 to +0.073
  percentage points, so Rule A retains the full January 2021-May 2026 window;
- 6,910 undocumented `tipoempregador` rows and one
  `tipoestabelecimento = -1` row remain preserved and explicitly unassigned
  to an invented ownership category.

## Checkpoint C — Reference measurement

Status: **PASS (non-blocking)** on 26 July 2026.

Evidence:

- the national and sector panels pass duplicate-key, count-reaggregation,
  wage-domain, and zero-flow missingness checks;
- the exact V1 model was re-estimated on the V2 panel for the original
  January 2021-June 2025 window and 341-CBO contrast;
- none of the four coefficients changes sign;
- the real admission-wage coefficient is the only outcome that crosses the
  5% significance threshold, moving from -0.020706 (SE 0.013992) to -0.046974
  (SE 0.010317);
- independent fixed-effect absorption reproduces the four `pyfixest`
  coefficients to a maximum absolute difference of `1.41e-14`;
- the complete numerical comparison is at the top of `RECONCILIACAO.md` and
  in `gate_modelo_antigo.csv`.

The author designated this as a measurement checkpoint rather than a pipeline
stop rule. Execution therefore proceeds regardless of coefficient direction
or significance.

## Checkpoint D — Treatment classification

Status: **PASS** on 26 July 2026.

Evidence:

- V-A reproduces the frozen Task 11 classification exactly and remains the
  principal treatment definition;
- V-B, V-C, and V-D were implemented under rules recorded in `DECISIONS.md`
  before variant estimation and remain sensitivity definitions;
- the comparison table reports all seven classification categories for all
  four variants and counts 0, 8, 16, and 53 changes relative to V-A;
- the CBO 4121 report exposes every ISCO-08 destination, score, task
  dispersion, employment weight, native label, and the conservative V-D tie;
- no coefficient was estimated with B, C, or D before the classification
  comparison was frozen.

## Checkpoint E — Econometric core

Status: **PASS** on 26 July 2026.

Evidence:

- the shared estimator passes the no-contemporaneous-controls contract and
  reports cluster-t inference, convergence, separation, losses, N, and
  cluster counts;
- the balanced event grid is complete from -23 through +23 with November 2022
  as the unique reference and no grouped tails;
- all 35 national ladder models converge and all seven preregistered steps are
  exported, including the continuous measure beside the binary measure;
- the sector-support table precedes coefficient output and shows treated and
  control coexistence in all 1,365 level-2 section-month cells;
- level 1 and level 2 are reported side by side for all five outcomes and
  their coefficient differences are explicit;
- level 3 retains 55 treated CBOs in coexisting cells, exceeds the threshold
  of 20, and remains labeled a support diagnostic;
- two-way robustness uses 341 CBO4 and 87 CNAE-division clusters, never the
  21-section dimension.

## Checkpoint F — Falsification

Status: **PASS** on 26 July 2026.

Evidence:

- the false December 2021 treatment date is estimated only on the true
  pre-period and all five outcome p-values are at least 0.05;
- the temporal stopping rule therefore passes;
- 500 exact random assignments preserve the observed 75-treated/341-CBO
  design;
- empirical two-sided group-placebo p-values are 0.299 for admissions, 0.295
  for separations, 0.271 for gross flows, 0.002 for admission wage, and 0.090
  for net balance;
- checkpoint files record the completed seed sequence and backend
  equivalence check, so the randomization exercise is resumable and
  auditable.

## Checkpoint G — Mechanisms

Status: **PASS WITH ONE DECLARED NON-EXECUTION** on 26 July 2026.

Evidence:

- six separation families reconcile exactly to aggregate separations and
  report support, static estimates, dynamic estimates, and adjusted p-values;
- the cumulative net-flow index is explicitly labeled a proxy rather than
  employment stock;
- hourly wage, contracted hours, partial schedules, and intermittent
  schedules are estimated in one declared multiplicity family;
- 50 employer-size DDD models report complete support and BH-adjusted
  inference, with zero adjusted rejections;
- the planned public-versus-private falsification was not executed because
  the official fields encode registration form rather than ownership and
  would not identify the proposed contrast;
- the non-execution is recorded as
  `not_executed_nonidentifying_fields`; no ownership coefficient was
  fabricated.

## Checkpoint H — Release package

Status: **PASS** on 26 July 2026.

Evidence:

- the public `--section 4-5 --mode reproduce --skip-figures` command completed
  all 17 DAG nodes and reported 84 non-PNG artifacts in the rendered bundle;
- all 15 inferential nodes were re-estimated rather than copied from frozen
  coefficient tables;
- the complete test suite passes: 115 tests across every `tests/test_*.py`
  module, including all ten release gates and data-construction coverage;
- the final semantic reference contains 87 artifacts and passes source,
  schema, unit, category-domain, SHA-256, and manifest-signature validation;
- the independent base-R replay has the same sample and 341 clusters for all
  five central models;
- the maximum Python-R coefficient difference is `1.1209513178789265e-10`
  and the maximum standard-error difference is
  `1.2007179972517434e-11`, exceeding the six-decimal agreement requirement;
- `COMPARACAO_V1_V2.md` covers every planned change, every mechanism, and the
  complete Task 14 gate;
- the package is delivered without rewriting the dissertation text, which
  remains a separate authoring round.
