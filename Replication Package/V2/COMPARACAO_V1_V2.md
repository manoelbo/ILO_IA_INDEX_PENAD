# V1-V2 Empirical Comparison

## Decision

V2 supersedes V1 as the auditable empirical package. This decision is based
on data lineage, construction validity, estimator coverage, and
reproducibility—not on larger or more significant coefficients.

V2 does **not** support an unqualified national causal claim. All five exact
event-study specifications fail the joint pretrend diagnostic. The national
average coefficients must therefore be described as post-ChatGPT
treated-versus-control differences under the frozen occupational-exposure
design. The dissertation-text revision is a separate round.

## Task 14 gate: exact V1 model on the V2 panel

This is the cleanest direct measurement of the effect of rebuilding the
panel. The specification, controls, treatment contrast, January 2021-June
2025 window, fixed effects, and clustered inference are identical to V1.

| Outcome | V1 coefficient (SE) | V2 coefficient (SE) | V2 − V1 | Sign change | Crossed 5% |
|---|---:|---:|---:|---|---|
| Log admissions | -0.030879 (0.026288) | -0.024528 (0.025876) | +0.006351 | no | no |
| Log separations | -0.041658 (0.025418) | -0.033882 (0.025355) | +0.007777 | no | no |
| Log real admission wage | -0.020706 (0.013992) | -0.046974 (0.010317) | -0.026268 | no | **yes** |
| Asinh net balance | -0.659661 (0.377251) | -0.607197 (0.375065) | +0.052463 | no | no |

No coefficient changes sign. Only the admission-wage result crosses the 5%
threshold. This gate combines all data-construction corrections; it does not
pretend to isolate the separate contribution of late declarations,
missingness, and winsorization.

## One line per change

| Change | V1 | V2 | Why | Numeric effect or diagnostic |
|---|---|---|---|---|
| Official vintage | MOV extract | One frozen MTE vintage, `MOV + FOR − EXC` | Assign revisions to the fact month and avoid mixed vintages | 2021: 36,554,795 MOV + 2,680,702 FOR − 132,425 EXC = 39,103,072; net +6.97% |
| FOR external validation | Annual comparison used the wrong year semantics in the original threshold | File-year counts reproduce Base dos Dados declaration-year counts | Base dos Dados `ano` is declaration competence, not fact competence | Corrected benchmark: +7.33% gross and +6.97% net, not approximately 8% under mixed periods |
| Monthly fact-time validation | No test of `competenciamov` reassignment | Adjusted PDET series matched month by month | Annual totals cannot detect a one-month assignment error | 65/65 months exact for admissions, separations, and balance; zero total discrepancy; ±1-month shift discrepancy 28,189,094 |
| Recent-month completeness | Early-sample coverage bias remained in V1 | Full window retained under Rule A with month effects | Treated-control completeness differential stays below 1 pp | Maximum recent differential 0.281 pp; window not trimmed |
| Analysis cutoff | June 2025 in the published V1 model | May 2026, frozen before estimation | Use the complete available planned vintage and avoid June 2026 release timing | Ending in Dec/2025 instead of May/2026 changes coefficients by +0.004309 admissions, -0.003930 separations, +0.000303 gross flow, +0.001378 wage, +0.098578 balance |
| Wage missingness | 62 zero-admission cells received artificial R$1,104.7868 wages; 31 entered the main sample | Wage and composition are missing whenever the corresponding flow is zero | Preserve the denominator and prevent winsor floors from manufacturing outcomes | V2 has 403 zero-admission and 355 zero-separation cells, all with missing corresponding wages |
| Invalid record domains | Invalid wages and ages could survive to aggregates | Reject wage ≤0 or ≥R$1m, age outside 14-90, invalid CBO, and impossible flow codes before aggregation | Invalid records cannot be repaired after aggregation | 3,574,530 of 252,838,929 signed rows rejected; 249,264,399 valid rows retained |
| Wage winsorization | Admission wage only; separation wage reached approximately R$203.3m | Same record-level P1/P99 rule within CBO4-year for admissions and separations | Make both wage outcomes comparable and bounded | V2 maxima: R$298,641.60 admissions and R$114,433.00 separations; the isolated coefficient contribution is not separately identified from the Task 14 rebuild |
| Real wage construction | Real-wage replay was indirectly verified because month FE absorbed the deflator | Frozen IPCA through May 2026 and live real-wage estimation | Verify the actual constructed outcome | Under the exact V1 model, wage moves from -0.020706 to -0.046974, delta -0.026268 |
| Contemporary controls | Included in the preferred V1 equation | Excluded from the principal model; reported as descriptive conditioning | Age, sex, education, and race composition may be post-treatment | Adding them back changes V2 coefficients by +0.032290 admissions, +0.003744 separations, +0.018088 gross flow, +0.003862 wage, +0.016188 balance |
| Count estimator | OLS on `log(1+y)` | PPML principal; OLS `log(1+y)` secondary | PPML targets the conditional mean in levels and handles zeros directly | PPML vs secondary OLS: -0.053772 vs -0.010731 admissions; -0.042014 vs -0.029210 separations; -0.048093 vs -0.021221 gross flow |
| Principal national coefficients | V1 published estimates above | No-control V2: -0.053772 admissions, -0.042014 separations, -0.048093 gross flow, -0.050740 real wage, -0.551267 balance | Apply the frozen V2 hierarchy | Only wage rejects at 5%; failed pretrends prevent an unqualified causal reading |
| Treatment classification | One inherited aggregation rule without a frozen sensitivity table | V-A remains principal; V-B/C/D are preregistered sensitivities | Crosswalks are many-to-many and dispersion aggregation matters | V-A retains 75 exposed and 266 controls; V-B changes 8 CBOs, V-C 16, V-D 53 |
| Treatment vintage | 2025 OIT measure only | 2023 native automation potential re-estimated | Test vintage dependence | 10 treated vs 310 controls; admissions -0.071052 and wage -0.033910; no result survives the 15-test BH family |
| GPT-4o/Gemini agreement | Model disagreement not measured | Retain only ISCO destinations with the same full gradient label | Direct measurement-error robustness | 321/427 ISCO occupations agree; 59 treated/271 controls; wage -0.056058, BH p=0.0000468 |
| Anthropic comparison | No competing-index check | Rank correlation plus standardized automation-minus-augmentation model | Separate total exposure from observed automation orientation | Spearman rho -0.1214 for 92 direct matches and -0.0802 for 127 direct+hierarchical matches; flow coefficients within 0.003 of zero |
| Event-study window | Two inconsistent V1 conventions and grouped tails | Complete `t=-23…+23`, November 2022 reference, no grouped endpoints | Make every event coefficient map to one month | 47 unique event times; 15,935 cells for flow/balance and 15,907 for wage |
| Pretrend diagnostics | Main flow pretrends were not a release gate | Exact-model joint, linear, and individual-lead diagnostics | A non-significant test is not proof; a failed test constrains claims | All five joint lead tests fail; p values range from 2.12e-52 to 0.000158 |
| HonestDiD | Not reported | Rambachan-Roth relative-magnitude sensitivity in R | Quantify sensitivity to deviations from parallel trends | Wage does not exclude zero even at M=0; balance excludes zero only through M=0.05 |
| Sector design | National CBO4-month design only | National and CBO4×CNAE models side by side; CBO4×division clustering | Test sector-time confounding and retain division for two-way inference | Level 2 minus level 1: -0.021304 admissions, -0.024432 separations, -0.022572 gross flow, +0.015142 wage, +0.411773 balance; 87 division clusters |
| DDD multiplicity | Nominal heterogeneous contrasts could be promoted | One 100-test BH family with complete DDD terms | Control false discoveries across planned dimensions | 34 nominal p<0.05; 21 BH p<0.05; 18 adequate-support groups, one limited, one thin |
| Temporal placebo | Not a blocking falsification | False December 2021 event on the true pre-period | Enforce the Checkpoint F stopping rule | All five p≥0.05; gate passes |
| Group placebo | Not reported | 500 exact 75-of-341 reassignments | Position observed coefficients in a random-group distribution | Empirical two-sided p: 0.299 admissions, 0.295 separations, 0.271 gross flow, 0.002 wage, 0.090 balance |
| Separation mechanisms | Aggregate separations only | Six reconciled separation families | Distinguish firm retention from outside-option behavior | Dismissal without cause -0.000020 (BH p=0.9995); resignation -0.116649 (BH p=0.3299); exact reconciliation |
| Cumulative net-flow proxy | No mechanism proxy with a valid normalization | `100 + 100 × cumulative net-flow change / pre-period gross flow` | Avoid division by non-positive January balance and disclose that stock is unobserved | +1.429 index points, SE 1.309, p=0.276; one CBO excluded for zero pre-period gross flow |
| Hourly wage and schedules | Monthly wage only | Real hourly wage, contracted hours, partial, and intermittent margins | Separate the price and schedule channels | Hourly wage -0.069508 (BH p=0.0000967); weekly hours +0.001552, partial -0.000779, intermittent +0.000746, all adjusted non-significant |
| Establishment size | Not reported | Ten size-band DDDs × five outcomes | Test whether patterns concentrate by employer size | 50 models; three nominal wage contrasts; zero BH rejections |
| Public/private falsification | Planned but unsupported | **Not executed** | Official fields encode registration form, not ownership; category 101 mixes general and public CLT workers | No coefficient is fabricated; status `not_executed_nonidentifying_fields` |
| Inferential reproduction | Most V1 event studies, DDDs, Poisson, and wage outputs were frozen/rendered | Public DAG re-estimates every inferential family | Successful replay must demonstrate scientific reconstruction | 17-node `reproduce` DAG after reference validation; 15 live inferential nodes |
| Semantic integrity | Byte identity could preserve a semantically wrong table | Source, schema, unit, and category contracts plus signed manifest | Detect a wrong-domain table even when its shape is plausible | Injection test fails; final reference count is recorded in the signed manifest |
| Python-R replication | Four V1 replay coefficients; real wage construction not independently checked | Five central models independently re-estimated in base R | Cross-language estimator validation | Same N and 341 clusters; max coefficient difference 1.12e-10; max SE difference 1.20e-11 |

## Interpretation recommendation

Use V2 for every future table and figure because its data vintage, semantic
contracts, estimators, and replay path are materially stronger. Do not carry
V1 coefficients into the rewritten dissertation.

For the substantive text:

1. state that the national flow estimates are negative but imprecise;
2. state that the admission-wage difference is negative and stable across
   several measurement choices;
3. immediately disclose that exact pretrend diagnostics fail and HonestDiD
   does not protect the wage sign;
4. describe mechanism and heterogeneity exercises as adjusted, support-aware
   exploratory decompositions rather than proof of causal channels;
5. disclose the unexecuted public/private falsification and the fact that the
   cumulative net-flow index is not employment stock.

That is a narrower conclusion than V1 suggested, but it is better supported
and fully auditable.
