# V1-V2 Reconciliation

## Headline result — exact V1 model on the V2 panel

The preregistered Task 14 gate re-estimated the exact V1 OLS specification on
the refreshed panel over the original January 2021-June 2025 window. It kept
the original admission-composition controls, CBO4 and month fixed effects,
G1-G4 versus `Not Exposed`, and CRV1 clustering by CBO4.

| Outcome | V1 coefficient (SE) | V2 coefficient (SE) | Delta | Sign change | Crossed 5% significance |
|---|---:|---:|---:|---|---|
| Log admissions | -0.030879 (0.026288) | -0.024528 (0.025876) | +0.006351 | no | no |
| Log separations | -0.041658 (0.025418) | -0.033882 (0.025355) | +0.007777 | no | no |
| Log real admission wage | -0.020706 (0.013992) | -0.046974 (0.010317) | -0.026268 | no | **yes** |
| Asinh net balance | -0.659661 (0.377251) | -0.607197 (0.375065) | +0.052463 | no | no |

No coefficient changes sign. The real admission-wage coefficient becomes more
negative and crosses the 5% threshold (`p = 0.00000738`); the other three
remain statistically insignificant at 5%. The literal V1 specification retains
18,281 V2 observations and 341 CBO4 families, compared with 18,307
observations in V1. This 26-observation decrease is disclosed rather than
silently balanced or imputed.

Independent Frisch-Waugh-Lovell fixed-effect absorption reproduces all four
`pyfixest` coefficients with a maximum absolute difference of
`1.41e-14`. Checkpoint C is non-blocking by prior author decision, so this
measurement is recorded without selecting or changing the specification.

The V1 baseline is the frozen local Base dos Dados MOV extract. The V2 vintage is the official MTE FTP reconstruction using MOV + FOR - EXC.

## Blocking 2021 check

- V1 movements: 36,554,795.
- V2 movements: 39,103,072.
- Absolute delta: 2,548,277.
- Percentage delta: 6.97%.
- MOV revision: 0.
- FOR contribution: 2,680,702.
- EXC contribution: -132,425.

The plan requires this delta to be positive and on the order of 8%. The observed positive delta is of that order and therefore passes the blocking check. No numerical tolerance was introduced beyond that written contract.

## Monthly summary

- admissoes: mean monthly delta 2.58%; maximum absolute percentage delta 10.37% in 202101.
- desligamentos: mean monthly delta 3.05%; maximum absolute percentage delta 12.63% in 202101.
- movimentacoes: mean monthly delta 2.80%; maximum absolute percentage delta 11.40% in 202101.
- Largest absolute monthly movement delta: 324,150 in 202101.

## Decomposition

For each flow and month, the CSV decomposes the total delta as `MOV revision + FOR contribution + EXC contribution`, where the EXC contribution is negative.

The optional live BigQuery comparison was not required for this local reconciliation. The frozen V1 extracts already provide the exact Base dos Dados MOV rows used by V1.

## Official PDET adjusted-series validation

The May 2026 official Novo CAGED workbook was frozen by SHA-256 and its
`Tabela 5.1 - com ajustes` series was compared with the signed V2 movements
for every fact month from January 2021 through May 2026.

- Months compared: 65.
- Months with any difference: 0.
- Maximum and total absolute admission difference: 0.
- Maximum and total absolute separation difference: 0.
- Maximum and total absolute balance difference: 0.
- Total absolute discrepancy after a one-month backward shift: 28,189,094.
- Total absolute discrepancy after a one-month forward shift: 28,189,094.

This exact match validates the new reassignment by `competenciamov`, which
the V1 MOV identity and annual Base dos Dados FOR identity could not test.
There is no systematic one-month shift. The Checkpoint B PDET pendency is
closed before Task 14 interpretation.
