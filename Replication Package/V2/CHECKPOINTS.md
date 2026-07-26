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
