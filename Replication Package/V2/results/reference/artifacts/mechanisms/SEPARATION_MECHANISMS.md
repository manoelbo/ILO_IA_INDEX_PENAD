# Task 23 separation mechanisms

## Reconciliation and support

The six named families sum to 118,723,283 signed separations. The excluded retirement, death, and transfer codes sum to 492,219. Together they reproduce the national-panel total of 119,215,502 exactly.

| Family | Codes | Signed total in main sample | Share (%) | Positive cells | Treated CBOs | Control CBOs |
|---|---:|---:|---:|---:|---:|---:|
| Contract termination | 43 + 45 | 12,139,016 | 16.281 | 21,114 | 75 | 265 |
| Dismissal with cause or reciprocal fault | 32 + 33 | 1,545,886 | 2.073 | 17,351 | 74 | 265 |
| Dismissal without cause | 31 | 34,961,446 | 46.890 | 21,952 | 75 | 266 |
| Mutual agreement | 90 | 747,994 | 1.003 | 17,960 | 75 | 263 |
| Resignation | 40 | 25,093,945 | 33.656 | 21,884 | 75 | 265 |
| Unknown separation type | 98 | 72,095 | 0.097 | 6,769 | 69 | 230 |

## Static principal specification

| Family | Coefficient | Effect (%) | SE | Nominal p | BH-adjusted p | N | CBO clusters |
|---|---:|---:|---:|---:|---:|---:|---:|
| Contract termination | -0.030129 | -2.968 | 0.047017 | 0.522075 | 0.711902 | 22,039 | 340 |
| Dismissal with cause or reciprocal fault | -0.154653 | -14.329 | 0.123641 | 0.211864 | 0.423727 | 21,974 | 339 |
| Dismissal without cause | -0.000020 | -0.002 | 0.033726 | 0.999531 | 0.999531 | 22,049 | 341 |
| Mutual agreement | -0.023386 | -2.311 | 0.043741 | 0.593252 | 0.711902 | 21,927 | 338 |
| Resignation | -0.116649 | -11.010 | 0.065293 | 0.0749043 | 0.329901 | 22,039 | 340 |
| Unknown separation type | -0.210189 | -18.957 | 0.131113 | 0.109967 | 0.329901 | 19,435 | 299 |

## Event study

The machine-readable event-study table contains all six families on the frozen ungrouped -23 through +23 grid with November 2022 as the reference. BH adjustment is reported across all non-reference dynamic coefficients.

Rows: 282; non-reference tests: 276.

Mechanism labels remain descriptive because the national exact-model pretrend diagnostics fail.
