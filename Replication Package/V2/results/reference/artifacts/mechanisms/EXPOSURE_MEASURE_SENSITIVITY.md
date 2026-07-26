# Exposure-Measure Sensitivity

Task 27 reports all three frozen measurement exercises. The fifteen nominal p-values are adjusted together with Benjamini-Hochberg. These are sensitivity estimates; they do not repair the failed national pretrend diagnostics.

## Support

| Measure | Scale | CBOs | Treated | Control | Months |
|---|---|---:|---:|---:|---:|
| vintage_2023 | Automation Potential vs Not affected | 320 | 10 | 310 | 65 |
| model_consensus | Exposed vs Not Exposed among consensus destinations | 330 | 59 | 271 | 65 |
| anthropic_continuous | one SD of the automation-minus-augmentation index | 168 | 0 | 0 | 65 |

The Anthropic row is continuous, so treated/control counts are not applicable. Rows with `zero_imputation_no_data` are excluded rather than interpreted as observed zero exposure.

## Rank correlation with Anthropic

| Sample | CBOs | Spearman rho |
|---|---:|---:|
| direct_matches | 92 | -0.1214 |
| direct_plus_hierarchical | 127 | -0.0802 |

## Re-estimated principal specification

| Measure | Outcome | Coefficient | SE | Nominal p | BH-adjusted p | N | CBO clusters |
|---|---|---:|---:|---:|---:|---:|---:|
| vintage_2023 | admissoes | -0.071052 | 0.038244 | 0.0641124 | 0.184732 | 20599 | 320 |
| vintage_2023 | desligamentos | -0.089329 | 0.046797 | 0.0571749 | 0.184732 | 20599 | 320 |
| vintage_2023 | n_movimentacoes | -0.080101 | 0.041029 | 0.0517778 | 0.184732 | 20599 | 320 |
| vintage_2023 | ln_salario_real_adm | -0.033910 | 0.017663 | 0.0557742 | 0.184732 | 20529 | 320 |
| vintage_2023 | asinh_saldo | 0.584221 | 0.396544 | 0.141661 | 0.263006 | 20599 | 320 |
| model_consensus | admissoes | -0.061149 | 0.037986 | 0.108404 | 0.232294 | 21301 | 330 |
| model_consensus | desligamentos | -0.031975 | 0.031076 | 0.304269 | 0.414912 | 21301 | 330 |
| model_consensus | n_movimentacoes | -0.047324 | 0.033677 | 0.16089 | 0.263006 | 21301 | 330 |
| model_consensus | ln_salario_real_adm | -0.056058 | 0.011816 | 3.12219e-06 | 4.68329e-05 | 21238 | 330 |
| model_consensus | asinh_saldo | -0.608494 | 0.448022 | 0.175337 | 0.263006 | 21301 | 330 |
| anthropic_continuous | admissoes | -0.000584 | 0.023465 | 0.98019 | 0.98019 | 10631 | 168 |
| anthropic_continuous | desligamentos | -0.002865 | 0.022470 | 0.898702 | 0.98019 | 10631 | 168 |
| anthropic_continuous | n_movimentacoes | -0.001802 | 0.022573 | 0.936478 | 0.98019 | 10631 | 168 |
| anthropic_continuous | ln_salario_real_adm | -0.019817 | 0.011018 | 0.0738926 | 0.184732 | 10552 | 168 |
| anthropic_continuous | asinh_saldo | 0.068777 | 0.170619 | 0.68739 | 0.859237 | 10631 | 168 |

## Measurement diagnostics

- ISCO-08 occupations with complete GPT-4o/Gemini gradient agreement: 321 of 427.
- CBO4 2023 native-category counts: `{"Augmentation Potential": 61, "Automation Potential": 10, "No score": 193, "Not affected": 310, "The Big Uknown": 55}`.
- The 2023 estimate retains the native automation-versus-not-affected distinction; it does not relabel augmentation as unexposed.
- The Anthropic coefficient is per one standard deviation of automation minus augmentation and therefore has a different substantive scale from the binary ILO coefficient.
