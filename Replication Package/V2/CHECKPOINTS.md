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
