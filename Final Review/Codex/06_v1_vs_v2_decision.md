# V1 versus V2 Decision

## Final verdict

# DO NOT CIRCULATE

This verdict applies to the files as they exist at the 25 July 2026
freeze. It is not a judgment that the dissertation should be abandoned.
It means that neither the current PDF nor the V1 package satisfies the
approved circulation gates.

The recommended target is **USE V2**, after the storage and official-data
gates open.

## Why targeted V1 edits are not enough

V1 can be made easier to read, but four material problems require a new
empirical generation:

1. zero-flow cells receive artificial positive admission wages and zero
   composition controls;
2. the preferred model conditions on contemporaneous admission
   composition that may be post-treatment;
3. most inferential outputs are frozen backing estimates rather than
   re-estimated by the public `reproduce` path;
4. dynamic endpoints are clipped and the main flow models fail their
   pretrend diagnostics.

The wrong package A.6, incomplete manuscript A.5, broken links,
incomplete references, and PDF rendering defects are important but
repairable. The wage construction and model-contract issues are not
merely editorial. Silently patching them inside V1 would destroy the
meaning of the frozen baseline.

## Why V2 is worth the remaining effort

V2 is justified by credibility and reproducibility, not by a promise of
more conclusive coefficients. It will:

- rebuild one official CAGED vintage rather than append new months to
  stale local Parquets;
- correct wage and missingness semantics;
- remove contemporaneous composition controls from the preferred model;
- use PPML for count outcomes and explicit balanced horizons;
- retain the metadata needed for validation and the pre-specified
  CBO×CNAE robustness;
- regenerate every inferential artifact and connect it to the
  manuscript;
- test all central models independently in Python and R.

These changes directly address material weaknesses found in V1. They
would remain valuable even if every result became null.

## Why V2 was not executed now

The approved stop rules are binding:

- the baseline capture recorded 6.78 GiB free and a later post-cleanup
  recheck recorded 8.45 GiB, both below the required 15–20 GiB;
- June 2026 is scheduled for release on 30 July 2026 and is not yet in
  the official FTP listing;
- the local 2021–June 2025 Parquets predate June 2026 revisions to
  historical official files and cannot be mixed with a new tail;
- the local IPCA stops at December 2025;
- the current full DAG duplicates raw inputs, loads annual data into
  memory, and drops metadata required by V2;
- clean pinned Python and R environments for the full protocol are not
  yet provisioned.

No user data was deleted, and no provisional V2 coefficients, figures,
or conclusions were created.

## Minimum path to a defensible advisor draft

If the advisor needs a draft before V2 can run, use V1 only as an
explicitly preliminary empirical baseline and complete all of the
following first:

1. correct the 10.1% versus 14.8% headline universe;
2. complete A.5 and reconcile A.6 with its true computational source;
3. remove or report promised robustness claims;
4. replace broken Appendix B links;
5. regenerate all 36 references from the corrected bibliography;
6. narrow causal, adoption, stock, and mechanism language;
7. rebuild and visually inspect the PDF;
8. disclose that only four central V1 models are re-estimated publicly
   and that national flow pretrends fail.

That document may be shared for methodological feedback, but it should
not be described as the final empirical package.

## Bounded V2 work plan

The remaining work should stay tightly scoped:

### Gate-opening work

- free or provision 15–20 GiB without deleting user data;
- on or after 30 July, freeze June if available; otherwise freeze May;
- provision isolated Python and R environments.

### High-return empirical work

- batched official-data ingestion and manifests;
- wage/domain/merge validation;
- PPML and no-contemporaneous-control main models;
- exact balanced event study and named horizons;
- existing heterogeneities only;
- complete artifact and claim registry.

### Work to avoid

- new chapters;
- new outcome families;
- new subgroup searches;
- model selection by p-value;
- prose polishing before estimates and artifacts are frozen.

## Cost and stopping rule

The planned two-to-three-week window remains realistic only if scope is
held to the existing dissertation. The largest uncertainty is data
engineering, not writing. If the official vintage cannot be reconciled,
PPML lacks support, or the corrected design changes the estimand
materially, stop and retain `NOT EXECUTED` rather than publishing a
partial V2.

## Decision summary

| Question | Answer |
| --- | --- |
| Can V1 be reproduced operationally? | Yes: 16 tests pass and a temporary copy produces 116 files |
| Are the four central frozen coefficients reproducible? | Yes: Python and R agree to approximately `1e-12` |
| Does V1 support every inferential claim? | No |
| Is a text-only V1 cleanup sufficient for a final package? | No |
| Is V2 methodologically justified? | Yes |
| Can V2 be executed safely today? | No |
| Current release verdict | **DO NOT CIRCULATE** |
| Intended next release verdict | **USE V2**, conditional on all gates |
