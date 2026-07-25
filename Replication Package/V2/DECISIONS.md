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
