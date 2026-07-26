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
