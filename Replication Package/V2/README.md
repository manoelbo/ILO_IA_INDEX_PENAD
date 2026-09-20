# Dissertation Replication Package V2

This package reproduces every computational table and figure in Sections 3--5
and Appendices A--D of *Generative Artificial Intelligence and the Brazilian
Labor Market: An Analysis of Occupational Exposure and Its Distributional
Effects*. Table 2.1 is a literature synthesis and is intentionally outside the
computational registry.

The manuscript registry contains exactly 53 publications. Each row in
`config/manuscript_artifacts.csv` names its producer, analytical input,
reference artifact, and public command. Narrative quantities are independently
registered in `config/numeric_claims.csv` and reconciled after every run.

## Quick start

Requirements are Python 3.10, `uv`, R 4.4.1, and the analytical bundle
described in `DATA_AVAILABILITY.md`.

```bash
uv sync --frozen
Rscript -e 'if (!requireNamespace("renv", quietly = TRUE)) install.packages("renv"); renv::restore(prompt = FALSE)'

uv run python run_replication.py \
  --target all \
  --mode reproduce \
  --data-dir /path/to/replication-v2-bundle \
  --output-dir results/reproduced
```

The locked R environment includes `fixest` 0.14.0, `HonestDiD` 0.2.6, and
`data.table` 1.17.0. Cross-language model contracts are estimated independently;
R never reads coefficients produced by Python. Every public run fails at
preflight unless R 4.4.1 and all package versions match `renv.lock`.
The HonestDiD routines consume the event-study vector and covariance matrix
estimated by that independent R replay; Python validates those inputs against
its own estimates before either sensitivity analysis can run.

`reproduce` is offline: it reads only the frozen analytical bundle, re-estimates
the registered results, renders the publications, validates the immutable
reference, runs independent R replications, and reconciles the manuscript
claims. `full` acquires missing official sources, verifies their hashes,
rebuilds the derived inputs, and then executes the same inferential DAG. A
`full` run containing PNADc requires an explicit `--billing-project` and fails
at preflight when it is omitted.

Inspect the complete plan without executing it:

```bash
uv run python run_replication.py \
  --target all \
  --mode reproduce \
  --data-dir /path/to/replication-v2-bundle \
  --dry-run
```

Rebuild every component from the frozen official-source cache:

```bash
uv run python run_replication.py \
  --target all \
  --mode full \
  --data-dir /path/to/replication-v2-bundle \
  --raw-dir /path/to/replication-v2-raw-cache \
  --billing-project YOUR_BILLING_PROJECT
```

## Public interface

```text
python run_replication.py
  --target {all,section3,caged,rais,pnadc,spatial}
  --mode {reproduce,full}
  [--data-dir PATH]
  [--raw-dir PATH]
  [--output-dir PATH]
  [--billing-project PROJECT]
  [--skip-figures]
  [--dry-run]
```

The legacy alias `--section 3|4-5|all` remains available. `--section 4-5`
selects CAGED, RAIS, PNADc, and the spatial support analysis.

Outputs are written only to `results/reproduced/` or the requested output
directory. An existing directory is replaced only when its manifest proves
that it is a complete output created by this package. Code, inputs, and
`results/reference/` are never valid output destinations. The output directory
must also be disjoint from both `--data-dir` and `--raw-dir`: it cannot equal,
contain, or be contained by either input root.

## Components

| Target | Manuscript coverage | Role |
|---|---|---|
| `section3` | Section 3 | PNADc 2025 Q3 exposure and distributional profile |
| `caged` | Sections 4, 5.1--5.2 and Appendices A and C | Panels, DiD/DDD, event studies, diagnostics, and occupation cases |
| `rais` | Appendices B.1 and D.1 | Formal stock, turnover, and job tenure |
| `pnadc` | Appendices B.2 and D.2 | Informality, self-employment, employment stocks, and income |
| `spatial` | Section 4.5 and Appendices B.3--B.4 | Placebos, pretrends, and the support stopping rule |

The spatial component stops at the registered support gate. Family F retains
12 declared positions, but it contains no treatment coefficient, nominal
p-value, or multiplicity-adjusted p-value.

## Evidence and interpretation

The code preserves failed pretrend tests, non-positive-semidefinite covariance
diagnostics, rank-deficient covariance blocks, thin support, and
non-identification. These are results, not errors to be hidden. National CAGED
estimates and subgroup DDD contrasts must be read
as exploratory post-ChatGPT treated-versus-control differences because the
registered identifying diagnostics fail. RAIS and PNADc are complementary
measurement evidence, not causal extensions.

Python performs acquisition, data construction, DAG orchestration, and
rendering. R receives coefficient-free analytical inputs and model contracts.
It independently re-estimates every registered numerical result; Python then
matches stable analysis, model, term, and event-time identifiers. Coefficients
and standard errors must agree within `1e-6`; observation counts, clusters,
sample identifiers, statuses, and reference periods must agree exactly.

See `RESEARCH_DESIGN.md` for the estimands and scientific gates and
`DATA_AVAILABILITY.md` for source and bundle details.

## Repository map

```text
R/                         independent R estimators
code/
  common/                  shared paths, manifests, and validation
  section3/                descriptive analysis
  caged/                   CAGED ingestion, panels, models, and audits
  rais/, pnadc/, spatial/  complementary evidence
  render/                  manuscript renderers
  replication/             registries and cross-language checks
config/                    publication, claim, analysis, and data contracts
data/                      local mount point; large files are not distributed
results/reference/         immutable signed reference
results/reproduced/        default public output
tests/                     scientific, interface, and portability tests
```

## Verification

```bash
OPENBLAS_NUM_THREADS=1 \
OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
NUMBA_NUM_THREADS=1 \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
uv run pytest -q tests
```

The complete test suite expects the analytical bundle to be mounted or copied
at `data/`. Runner-interface and portability tests can be executed without that
mount; public runs may instead keep the bundle external and pass `--data-dir`.

The test suite checks the typed DAG, the 53-publication set, numerical claims,
scientific gates, output isolation, deterministic manifests, and the
cross-language contracts. A release is not valid merely because a coefficient
is statistically significant.

## Citation and license

Use `CITATION.cff` to cite the package. Package code and original documentation
are licensed under MIT; source datasets retain their providers' terms.
