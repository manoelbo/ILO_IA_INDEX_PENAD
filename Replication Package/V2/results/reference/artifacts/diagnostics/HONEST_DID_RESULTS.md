# HonestDiD sensitivity results

Task 20 applies `HonestDiD` 0.2.6 only to the two linear outcomes. The target
is the equally weighted average of the 24 balanced post-treatment
event-study coefficients (`t = 0,...,23`). The input retains all 22 estimated
pre-period coefficients, the November 2022 reference, and the full
CBO4-clustered covariance matrix.

| Outcome | Average post estimate | Original 95% CI | Largest evaluated M excluding zero | Reading |
|---|---:|---:|---:|---|
| Asinh net balance | -3.3079 | [-4.6931, -1.9227] | 0.05 | The robust interval is negative at M=0.05 and includes zero at M=0.10. |
| Log real admission wage | -0.0154 | [-0.0392, 0.0085] | None | The interval includes zero already at M=0. |

The relative-magnitude sensitivity uses `DeltaRM`, the `C-LF` method, a 95%
confidence level, and the frozen grid `M = 0, 0.05,...,2`. The scalar M is the
maximum post-treatment violation relative to the largest observed
pre-treatment violation under this restriction.

At high M values, the package warns that some confidence intervals are open at
an internal grid endpoint. Those rows are explicitly flagged in the CSV.
This numerical limitation does not determine either reported robustness
threshold: the asinh interval includes zero before the first open endpoint,
and the wage interval includes zero at M=0.

The PPML admissions, separations, and gross-flow event studies are not passed
to `HonestDiD`; no linear approximation is substituted for the nonlinear
models.
