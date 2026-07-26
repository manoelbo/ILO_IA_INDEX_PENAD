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
