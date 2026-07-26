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
