# V1 Specification on the V2 Panel

The exact V1 OLS specification was re-estimated on the refreshed national panel for January 2021-June 2025, with the original four admission-composition controls, CBO4 and month fixed effects, and CRV1 standard errors clustered by CBO4.

| Outcome | V1 coefficient (SE) | V2 coefficient (SE) | Delta | Delta vs V1 | Sign change | 5% significance crossing |
|---|---:|---:|---:|---:|---|---|
| ln_admissoes | -0.030879 (0.026288) | -0.024528 (0.025876) | +0.006351 | +20.6% | no | no |
| ln_desligamentos | -0.041658 (0.025418) | -0.033882 (0.025355) | +0.007777 | +18.7% | no | no |
| ln_salario_real_adm | -0.020706 (0.013992) | -0.046974 (0.010317) | -0.026268 | -126.9% | no | yes |
| asinh_saldo | -0.659661 (0.377251) | -0.607197 (0.375065) | +0.052463 | +8.0% | no | no |

## Explicit gate declarations

Sign changes: none.
Crossings of the 5% significance threshold: ln_salario_real_adm

Checkpoint C is a non-blocking measurement checkpoint. These results are reported regardless of direction or significance.

The four coefficients were independently reproduced by iterative Frisch-Waugh-Lovell fixed-effect absorption; the maximum absolute difference from `pyfixest` was 1.410e-14.
