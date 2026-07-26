# Task 22 placebo falsifications

## Frozen contract

The temporal placebo assigns a false event in December 2021 and uses only the true pre-treatment sample from January 2021 through November 2022. The exact national estimator family is retained without contemporary controls.

## Temporal placebo

| Outcome | Estimator | Coefficient | SE | p-value | Gate |
|---|---:|---:|---:|---:|---:|
| admissoes | ppml | 0.002406 | 0.024079 | 0.920465 | PASS |
| desligamentos | ppml | 0.024760 | 0.018891 | 0.190866 | PASS |
| n_movimentacoes | ppml | 0.012746 | 0.020426 | 0.533036 | PASS |
| ln_salario_real_adm | ols | -0.019835 | 0.011348 | 0.0813978 | PASS |
| asinh_saldo | ols | -0.127755 | 0.308500 | 0.679052 | PASS |

**Checkpoint F temporal gate: PASS.**

## Group placebo

Exactly 75 of 341 CBO4 families were reassigned in each of 500 repetitions with seed 20260726.

The randomization coefficients use the algebraically equivalent PPML margin-fitting and OLS FWL backend. The first assignment is reconciled against the shared reference estimator in `group_placebo_backend_validation.csv`.

| Outcome | Observed coefficient | Observed percentile | Two-sided randomization p |
|---|---:|---:|---:|
| admissoes | -0.053772 | 16.60 | 0.299401 |
| desligamentos | -0.042014 | 13.80 | 0.295409 |
| n_movimentacoes | -0.048093 | 14.00 | 0.271457 |
| ln_salario_real_adm | -0.050740 | 0.00 | 0.001996 |
| asinh_saldo | -0.551267 | 5.80 | 0.089820 |
