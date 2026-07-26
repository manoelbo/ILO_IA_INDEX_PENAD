# Exact-model pretrend diagnostics

All diagnostics use the exact balanced dynamic model, sample, fixed effects, reference month, and CBO4 clustering reported in the event-study output.

| Outcome | Estimator | Joint-lead p | Linear-slope p | Individual leads p<0.05 | Status | N | Clusters |
|---|---:|---:|---:|---:|---:|---:|---:|
| admissoes | ppml | 2.12415e-52 | 7.23865e-13 | 3 | fail | 15,935 | 341 |
| desligamentos | ppml | 2.12836e-18 | 7.63773e-06 | 10 | fail | 15,935 | 341 |
| n_movimentacoes | ppml | 4.34751e-43 | 0.00106402 | 1 | fail | 15,935 | 341 |
| ln_salario_real_adm | ols | 0.00015801 | 0.220798 | 11 | fail | 15,907 | 341 |
| asinh_saldo | ols | 1.48317e-06 | 0.919829 | 21 | fail | 15,935 | 341 |

The three named diagnostics are not interchangeable: the joint Wald test evaluates all leads simultaneously, the GLS linear test evaluates a single differential slope, and the dynamic inspection counts individually unusual leads.

A non-significant pretrend diagnostic is not proof of parallel trends. Failed and warning results remain visible and require appropriately non-causal narrative language.
