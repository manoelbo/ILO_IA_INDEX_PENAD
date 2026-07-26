# Task 24 cumulative net-flow proxy

## Measurement contract

This outcome is an occupation-size-normalized cumulative net-flow index, **not an employment-stock level**. It is set to 100 in January 2021 and scales subsequent cumulative net flow by each CBO's total gross flow during January 2021-November 2022.

It does not recover the unobserved initial employment stock and does not incorporate unregistered exits or any other employment transition outside Novo CAGED.

A literal January-balance ratio is rejected because 64 of 341 CBOs have a non-positive base net flow.

1 CBO lacks any pre-treatment gross flow and therefore remains in the series with a missing index but is excluded from estimation rather than assigned an artificial scale.

## Principal estimate

| Coefficient | SE | p-value | BH-adjusted p | N | CBO clusters |
|---:|---:|---:|---:|---:|---:|
| 1.429214 | 1.309287 | 0.275785 | 0.275785 | 22,100 | 340 |

The coefficient is measured in index points. Interpretation remains descriptive because the national exact-model pretrend diagnostics fail.
