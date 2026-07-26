# V2 Dissertation Replication Package

Status: **released** on 26 July 2026. The public reproduction command, complete
test suite, signed-reference refresh, Python-R cross-replication, and
Checkpoint H audit all pass.

V2 supersedes V1 because it materially improves data lineage, outcome
construction, estimator coverage, and reproducibility. It is not selected
because it produces larger or more significant coefficients.

## Quick start

From this directory:

```bash
uv sync
.venv/bin/python run_replication.py \
  --section 4-5 \
  --mode reproduce
```

Inspect the complete DAG and input preflight without estimating:

```bash
.venv/bin/python run_replication.py \
  --section 4-5 \
  --mode reproduce \
  --dry-run
```

Run the release tests:

```bash
OPENBLAS_NUM_THREADS=1 \
OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
NUMBA_NUM_THREADS=1 \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
.venv/bin/pytest -q tests
```

## Public interface

```text
run_replication.py
  --section {all,3,4-5}
  --mode {reproduce,full}
  [--raw-dir PATH]
  [--output-dir PATH]
  [--skip-figures]
  [--dry-run]
```

- `reproduce` validates the signed reference and re-estimates every
  inferential family from the frozen derived inputs.
- `full` additionally rebuilds the signed movement partitions, treatment
  classification, and national and sector panels from the 195 raw archives.
- `--section 3` validates the frozen Section 3 reference.
- `--section 4-5` runs the 17-node empirical DAG.
- `--output-dir` copies the rendered bundle to another destination without
  replacing the canonical results.

The log distinguishes `RE-ESTIMATED`, `FROZEN ESTIMATE VALIDATED`,
`DATA REBUILT`, and `ARTIFACT RENDERED`.

The validated local `reproduce` run completed all 17 nodes. Its HonestDiD node
dominated runtime and took approximately 102 minutes on the release machine;
future runs should expect this step to be computationally expensive even when
it emits no intermediate log lines.

## Frozen data contract

- official cutoff: May 2026;
- period: January 2021-May 2026;
- raw vintage: 195 official MOV/FOR/EXC archives;
- signed fact-month layer: 77 Parquet partitions;
- reconstruction identity: `MOV + FOR − EXC`;
- official validation: exact monthly agreement with the adjusted PDET series
  for all 65 months and all three aggregates;
- treatment crosswalk and external exposure sources: local frozen copies with
  checksums, never live scraping during estimation.

The corrected 2021 reconstruction is 36,554,795 MOV + 2,680,702 FOR −
132,425 EXC = 39,103,072 net movements. Gross FOR is 7.33% of MOV and the net
adjustment is 6.97%.

## Empirical contract

- principal contrast: G1-G4 versus `Not Exposed`, excluding
  `Minimal Exposure`;
- admissions, separations, and gross flows: PPML principal and OLS
  `log(1+y)` secondary;
- admission wage: OLS on valid log real wages;
- net flow: OLS on `asinh(net flow)` as a complementary outcome;
- CBO4 and month fixed effects, with CBO4-clustered inference;
- no contemporary composition controls in the principal specification;
- balanced event window `-23…+23`, with November 2022 omitted and no grouped
  endpoints;
- sector robustness retains both CNAE section and division and uses CBO4 ×
  division two-way clustering;
- DDD requires `post × treatment × subgroup` and all lower-order terms;
- planned inference families report multiplicity adjustment and support.

## Headline evidence and interpretation boundary

The principal no-control estimates are -0.053772 for admissions, -0.042014
for separations, -0.048093 for gross flows, -0.050740 for real admission wage,
and -0.551267 for asinh net balance. Only admission wage rejects at 5%.

All five exact event-study specifications fail the joint pretrend diagnostic.
The wage HonestDiD interval does not exclude zero even at `M = 0`.
Accordingly, V2 does **not** support an unqualified national causal claim.
The estimates should be described as post-ChatGPT treated-versus-control
differences under the frozen occupational-exposure design.

The public-versus-private falsification is explicitly not executed: the
available official fields encode registration form rather than employer
ownership. No ownership coefficient is fabricated.

## Audit map

- `CHECKPOINTS.md`: checkpoint verdicts and evidence.
- `DECISIONS.md`: pre-estimation decisions, exceptions, and resolutions.
- `COMPARACAO_V1_V2.md`: one-line-per-change empirical comparison.
- `results/reconciliation/RECONCILIACAO.md`: vintage, PDET, and exact V1-model
  reconciliation.
- `results/reference/manifest.json`: signed semantic reference inventory.
- `results/replication/`: independent Python-R agreement evidence.

The dissertation-text revision is intentionally outside this package and
must be handled as a separate round.
