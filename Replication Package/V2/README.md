# V2 Status: EXECUTION STARTED

## Current decision

The refreshed empirical round started on 25 July 2026. This directory contains
only outputs produced by the preregistered V2 pipeline; provisional or
simulated empirical results are prohibited.

The foundation storage gate is open:

- 43 GiB free was verified before the approved plan was finalized, above the
  required 15 GiB minimum;
- 54 GiB free was measured again when execution started;
- the official cutoff is fixed at May 2026: 65 competencies and 195
  MOV/FOR/EXC archives from January 2021 through May 2026.

No user data will be deleted to create storage space, and the project
will not mix a new tail of months with an older historical vintage.

## Conditions required to execute

Execution proceeds only while all of the following remain true:

- at least 15 GiB is available without deleting user data;
- one complete official Novo CAGED vintage is frozen from January 2021
  through May 2026;
- the historical 2021–2025 competencies are downloaded from that same
  vintage and reconciled with official aggregates;
- IPCA and every crosswalk or metadata source are frozen to compatible
  vintages with checksums and schemas;
- monthly continuity, treatment support, wage domains, movement codes,
  and demographic code domains pass fail-fast validation;
- the central models remain estimable with defensible support.

## Frozen methodological contract

When released, V2 will retain the public interface:

```bash
python run_replication.py \
  --section all|3|4-5 \
  --mode reproduce|full
```

The empirical hierarchy is pre-specified:

- principal contrast: G1–G4 versus `Not Exposed`, excluding
  `Minimal Exposure`;
- admissions and separations: PPML primary, OLS `log(1+y)` secondary;
- admission wage: OLS on valid log real wages;
- net flow: `asinh(net flow)` as a complementary outcome;
- CBO4 × month benchmark, with CBO × CNAE only as a supported robustness
  design;
- balanced event window `-23…+23`, November 2022 as reference, no
  endpoint clipping;
- no contemporaneous composition controls in the preferred causal
  specification;
- exact-model pretrends, support diagnostics, multiplicity correction,
  and HonestDiD where compatible;
- DDD only with `post × treatment × subgroup` and all lower-order terms.

The detailed design and stop rules are in
`../../Final Review/Codex/05_v2_empirical_plan.md`.

## Prohibited interpretation

V2 will not be selected because it produces larger or more significant
coefficients. It will be selected only if it materially improves data
lineage, outcome construction, identification, dynamic specification,
or artifact reproducibility.
