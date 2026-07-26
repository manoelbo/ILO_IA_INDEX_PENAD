# Secondary Log-Flow Estimators

These three models implement the preregistered secondary OLS `log(1 + y)` estimators on the exact principal sample. They use CBO4 and month fixed effects, CBO4-clustered CRV1 inference, and no contemporary controls. PPML remains principal.

| Flow | Coefficient | SE | p-value | N | CBO clusters |
|---|---:|---:|---:|---:|---:|
| admissoes | -0.010731 | 0.028456 | 0.706333 | 22049 | 341 |
| desligamentos | -0.029210 | 0.028034 | 0.298163 | 22049 | 341 |
| n_movimentacoes | -0.021221 | 0.026836 | 0.429621 | 22049 | 341 |
