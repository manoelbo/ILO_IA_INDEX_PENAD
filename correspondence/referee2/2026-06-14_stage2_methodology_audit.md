# Stage 2 Methodology Audit: CAGED + ILO DiD

Date: 2026-06-14

## Executive Summary

This audit confirms that the current Stage 2 pipeline is not merely the old notebook with a corrected crosswalk. The DiD structure is broadly retained, but the current version changes the exposure assignment, eligible CBO sample, treatment classification, final control set, real-wage reconstruction, and age heterogeneity design.

The historical PDFs/exports do confirm the old headline wage findings: the old notebook showed a negative nominal wage effect, a smaller real wage effect, and a much larger young-worker wage effect. Those effects do not survive the current MTE-based baseline. The most defensible interpretation is that the older salary story was sensitive to the old crosswalk and old heterogeneity construction; the newer version is methodologically stronger but less dramatic on wages.

## Sources Checked

| source_type | stage | exists | text_chars | path |
| --- | --- | --- | --- | --- |
| pdf | stage2a | True | 114670 | /Users/manebrasil/Downloads/ETAPA 2a — Preparação do Painel CAGED + ILO Exposure Index (1).pdf |
| pdf | stage2b | True | 88310 | /Users/manebrasil/Downloads/ETAPA 2b — Análise Difference-in-Differences_ IA Generativa e Emprego Formal no Brasil (1).pdf |
| pdf | stage2c | True | 64851 | /Users/manebrasil/Downloads/ETAPA 2c — Resultados_ Consolidação e Síntese da Análise DiD (1).pdf |
| notebook_export_md | stage2a | True | 88760 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/notebooks/_export_md/etapa_2a_preparacao_dados_did_caged_ilo.md |
| notebook_export_md | stage2b | True | 73825 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/notebooks/_export_md/etapa_2b_analise_did_caged_ilo.md |
| notebook_export_md | stage2c | True | 48707 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/notebooks/_export_md/etapa_2c_resultados.md |
| current_script | stage2a | True | 70405 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py |
| current_script | stage2b | True | 54950 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/scripts/etapa_2b_analise_did_caged_ilo.py |
| current_script | section4 | True | 35924 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/scripts/build_dissertation_section4_results.py |
| current_script | crosswalk | True | 14434 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/scripts/caged_mte_crosswalk.py |
| current_script | scenario_grid | True | 57144 | /Users/manebrasil/Documents/Projects/Dissetação Mestrado/src/scripts/run_treatment_scenario_grid.py |

The PDFs were extracted with `pdftotext -layout` and saved under `outputs/stage2_methodology_audit/pdf_text/`. They are treated as the historical snapshot; exported Markdown is used as the easier-to-parse companion source.

## Methodology Comparison

| domain | audit_status | historical_pdf_or_notebook | current_scripts_or_outputs |
| --- | --- | --- | --- |
| Data window and unit | Mostly retained, but sample is smaller after MTE matching. | CAGED occupation-month panel, Jan/2021-Jun/2025 in the Stage 2b notebook output; PDFs/notebook describe 23 pre months and 31 post months. | Current Stage 2 panel has 23,319 rows, 436 CBOs, and 54 months after MTE matching. |
| Crosswalk | Substantive methodological change; this is the largest defensibility improvement. | Main text described CBO 2002 -> ISCO-08 using 2-digit matching/fallback and 4-digit hierarchical robustness. | Current `caged_mte_crosswalk.py` uses official MTE CBO2002-CBO94-CIUO88, then ISCO-88 -> ISCO-08, with no numeric CBO=ISCO fallback. |
| Treatment/control | Baseline estimand mostly retained; treatment assignment changed through the new score and eligible sample. | Top 20% of exposure score as treatment, bottom 80%/rest as control. | Still top 20% vs rest for the baseline, but thresholds are now computed over CBOs with valid MTE scores; scenario grid tests top 30%, ISCO 4d consensus, gradient definitions, and excluded-middle strategies. |
| Controls and fixed effects | Retained with one added demographic control; older generated comparison files may predate this control. | Occupation and month fixed effects, cluster by CBO 4d, controls for age, female share, and higher education share. | Current scripts retain CBO and period fixed effects and CBO clustering; final scripts also include `pct_negra_adm` as a required control. |
| Nominal wages | Retained as an aggregate-wage outcome, but it is log(mean wage), not mean(log wage). | `ln_salario_adm = log(salario_medio_adm)` after P1/P99 winsorization in Stage 2b. | Stage 2a builds `salario_medio_adm` as mean monthly admission wage; Stage 2b winsorizes aggregate CBO-month wages and recalculates logs. |
| Real wages | Current reconstruction is more defensible; audit still tests deflator arithmetic and missing/zero handling. | Notebook/PDF treats `ln_salario_real_adm` as a main cleaned inflation-adjusted outcome. | Current Section 4 reconstructs real wage from raw CAGED microdata using IPCA monthly index before group aggregation. |
| Age heterogeneity | Substantive change in heterogeneity design; old and new age estimates are not directly comparable. | Old Stage 2b uses `jovem_adm = idade_media_adm <= 30` in an aggregate triple-DiD and reports a strong young wage interaction in the PDF/notebook. | Current Section 4 reconstructs subgroup panels from raw microdata and splits age into 14-24, 25-34, 35-59, and 60+. |

## Historical Wage Findings Confirmed In PDF/Notebook

| label | coef | se | p_value | stars | percent_effect | n_obs | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nominal admission wage, old notebook main estimate | -0.0656 | 0.0278 | 0.019 | ** | -6.35 | 32988 | Extracted from Stage 2b PDF/exported notebook result table. |
| Real admission wage, old notebook main estimate | -0.0341 | 0.0193 | 0.078 | * | -3.35 | 32988 | Extracted from Stage 2b PDF/exported notebook result table. |
| Young-worker wage, old notebook main estimate | -0.1337 | 0.0522 | 0.011 | ** | -12.52 | 32988 | Extracted from Stage 2b PDF/exported notebook result table. |
| Nominal admission wage, old top-20 robustness table | -0.0631 | 0.0285 | 0.027 | ** | -6.12 | 32988 | Extracted from Stage 2c PDF/exported notebook robustness table. |

The user's memory of roughly a 13% young-wage effect and 3% general real-wage effect is consistent with the historical notebook/PDF: `ln_salario_jovem = -0.133735` implies about -12.52%, and `ln_salario_real_adm = -0.034081` implies about -3.35%.

## Current Main Results

| outcome | coef | se | p_value | stars | percent_effect | n_obs |
| --- | --- | --- | --- | --- | --- | --- |
| ln_admissoes | -0.0351 | 0.0235 | 0.137 |  | -3.44 | 23319 |
| ln_desligamentos | -0.0261 | 0.0230 | 0.256 |  | -2.58 | 23319 |
| saldo | -135.5690 | 100.9437 | 0.180 |  |  | 23319 |
| ln_salario_adm | -0.0143 | 0.0156 | 0.360 |  | -1.42 | 23319 |

The current final baseline has no statistically relevant wage effect in Stage 2: `ln_salario_adm` is -0.0143, p=0.360.

## Wage Decomposition

| comparison_source | before_spec | before_coef | before_p_value | before_percent_effect | after_spec | after_coef | after_p_value | after_percent_effect | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| old_full_vs_mte_existing_decomposition | before_old_full | -0.0415 | 0.031 | -4.06 | after_mte | -0.0173 | 0.269 | -1.71 | Existing crosswalk decomposition output; may predate the final pct_negra_adm control. |
| old_common_vs_mte_existing_decomposition | before_old_common | -0.0231 | 0.130 | -2.28 | after_mte | -0.0173 | 0.269 | -1.71 | Existing crosswalk decomposition output; may predate the final pct_negra_adm control. |
| current_final_baseline_with_pct_negra_control | historical_pdf_or_notebook_stage2b_main_table | -0.0656 | 0.019 | -6.35 | current_mte_final_did_main_results | -0.0143 | 0.360 | -1.42 | Direct old PDF/notebook headline to current final output comparison. |

The existing crosswalk decomposition shows that the wage effect weakens substantially even before the final control-set update: old full sample `ln_salario_adm` is negative and significant, the old score on the common MTE sample becomes smaller and non-significant, and the MTE score remains non-significant. This points to both sample selection and score reassignment, not just a cosmetic crosswalk label change.

## Salary Methodology Audit

| check | result | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| stage2a_nominal_mean_wage_matches_raw_admission_mean | pass | max_abs_difference | 0.000000 | Stage 2a salario_medio_adm is the raw mean of admission salario_mensal by CBO-month. |
| stage2a_admission_counts_match_raw | pass | max_abs_difference | 0.000000 | Admission counts match raw aggregation for the matched MTE panel rows. |
| salario_minimo_normalization | pass | max_abs_difference | 0.000000 | salario_sm equals salario_medio_adm divided by the annual minimum wage. |
| deflate_before_vs_after_monthly_aggregation | pass | max_abs_difference | 0.000000 | Because the IPCA deflator is constant within CBO-month, deflating before or after monthly aggregation is numerically equivalent. |
| log_mean_wage_vs_mean_log_wage | methodological_choice | mean_abs_gap | 0.242249 | The pipeline estimates log(mean wage). This differs from mean(log wage); this is not a coding bug but should be stated as the estimand. |
| log_mean_wage_vs_mean_log_wage_p95_gap | methodological_choice | p95_abs_gap | 0.886115 | Large within-cell wage dispersion can make log(mean wage) materially different from mean(log wage). |
| aggregate_wage_outliers_before_stage2b_winsorization | document | rows_outside_p1_p99 | 468.000000 | Stage 2b winsorizes aggregate CBO-month wages. This preserves rows but changes the wage outcome scale. |
| zeros_in_nominal_admission_wage_panel | flag | zero_salary_rows | 63.000000 | Rows with zero aggregate wages are clipped before logs; they should be acknowledged as data-quality/missingness cases. |
| current_stage2b_wage_max_after_winsorization | document | max_salario_medio_adm | 13,930.376599 | This records the wage scale after Stage 2b winsorization. |

No fatal IPCA arithmetic error was found. The key methodological issue is the wage estimand: the pipeline uses CBO-month aggregate wages, so the wage outcome is `log(mean wage)` after aggregation and winsorization, not the individual-level `mean(log wage)`. This is defensible if described accurately, but it can change interpretation.

## Age Split Evidence

| source_design | definition | outcome | coef | p_value | stars | percent_effect | n_obs | n_cbo | sample_loss_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_raw_microdata_four_age_groups | 14-24 | ln_salario_real_adm | -0.0200 | 0.260 |  | -1.98 | 22744.0 | 436.0 | No treated/control CBO loss for this outcome and group. |
| current_raw_microdata_four_age_groups | 25-34 | ln_salario_real_adm | -0.0054 | 0.714 |  | -0.54 | 23120.0 | 435.0 | 0 treated and 1 control CBOs have no non-missing Salário real de admissão (log) observations for 25-34 after raw reconstruction. |
| current_raw_microdata_four_age_groups | 35-59 | ln_salario_real_adm | -0.0245 | 0.289 |  | -2.42 | 23128.0 | 436.0 | No treated/control CBO loss for this outcome and group. |
| current_raw_microdata_four_age_groups | 60+ | ln_salario_real_adm | -0.0288 | 0.242 |  | -2.84 | 19061.0 | 432.0 | 2 treated and 2 control CBOs have no non-missing Salário real de admissão (log) observations for 60+ after raw reconstruction. |
| new_audit_raw_microdata_binary_age_groups | age_14_24_vs_other_raw_binary: Raw microdata: age 14-24 vs all older workers | ln_salario_real_adm |  |  |  |  |  |  | The audit attempted this raw pass, but the unoptimized groupby over raw CAGED was too slow for the current run. |
| new_audit_raw_microdata_binary_age_groups | age_14_30_vs_other_raw_binary: Raw microdata: age 14-30 vs all older workers | ln_salario_real_adm |  |  |  |  |  |  | The audit attempted this raw pass, but the unoptimized groupby over raw CAGED was too slow for the current run. |

The old young result came from an aggregate triple-DiD definition based on average age (`idade_media_adm <= 30`). The current Section 4 age design uses raw microdata subgroup panels. The audit attempted the requested raw binary young/non-young reaggregation, but the local unoptimized pass over raw CAGED was too slow for this run. The report therefore records the available current aggregate `<=30` output and the four-age-group raw-microdata output, and marks the raw binary designs as a dedicated computational follow-up.

## Identification Diagnostics

| domain | item | status | metric | value | note |
| --- | --- | --- | --- | --- | --- |
| parallel_trends | Log(Admissões) | PREOCUPAÇÃO | joint_pretrend_p_value | 0.0000 | 5 individually significant pre coefficients; max \|t\|=3.66. |
| parallel_trends | Log(Desligamentos) | PREOCUPAÇÃO | joint_pretrend_p_value | 0.0080 | 2 individually significant pre coefficients; max \|t\|=3.01. |
| parallel_trends | Saldo Líquido | PARALELAS | joint_pretrend_p_value | 0.3200 | 0 individually significant pre coefficients; max \|t\|=1.54. |
| parallel_trends | Log(Salário Admissão) | PARALELAS | joint_pretrend_p_value | 0.9900 | 0 individually significant pre coefficients; max \|t\|=1.14. |
| balance | Salário médio (R$) | ⚠️ | normalized_difference | 0.7657 | Control=2,570.003, Treated=4,062.331. |
| balance | Idade média | ⚠️ | normalized_difference | -0.3309 | Control=33.094, Treated=31.932. |
| balance | % Mulheres | ⚠️ | normalized_difference | 0.8854 | Control=0.263, Treated=0.464. |
| balance | % Superior completo | ⚠️ | normalized_difference | 1.2481 | Control=0.145, Treated=0.479. |
| balance | % Negros (pretos+pardos) | ⚠️ | normalized_difference | -0.8386 | Control=0.369, Treated=0.295. |

Salary has cleaner pre-trend diagnostics than admissions and separations, but the baseline treatment/control groups remain imbalanced on salary, age, female share, education, and race/color. The dissertation should avoid a strong unconditional causal claim and frame results as evidence of selective adjustment under a more defensible exposure measure.

## Direct Answers

| question | short_answer | evidence |
| --- | --- | --- |
| Q1 | The DiD skeleton was retained, but the crosswalk, eligible sample, treatment assignment, controls, real-wage reconstruction, and age heterogeneity design changed. | Methodology comparison and crosswalk decomposition tables. |
| Q2 | The old PDF/notebook wage findings were real in the historical output: young wage -0.1337 (-12.5%) and real wage -0.0341 (-3.4%). The current final Stage 2 wage effect is -0.0143 (-1.4%), p=0.360. | Old PDF/notebook key findings and current did_main_results. |
| Q3 | No fatal deflator arithmetic error was found, but log(mean wage), winsorization after aggregation, and zero/clip handling must be stated as methodological choices. | log_mean_wage_vs_mean_log_wage, log_mean_wage_vs_mean_log_wage_p95_gap, zeros_in_nominal_admission_wage_panel |
| Q4 | The available evidence does not justify reverting to the old young-wage headline. A raw binary young/non-young reestimate remains the right follow-up, but the current four-group evidence is cleaner and more transparent. | Pending raw binary rows: 2; available current four-group rows and aggregate <=30 rows are reported. |
| Q5 | The new version is academically more defensible because it removes the weakest CBO=ISCO numeric assumptions, but the dissertation should shift away from a strong headline salary claim. | MTE crosswalk coverage and pre-trend/balance caveats. |

## Files Written

- `outputs/stage2_methodology_audit/source_inventory.csv`
- `outputs/stage2_methodology_audit/methodology_comparison.csv`
- `outputs/stage2_methodology_audit/old_pdf_notebook_key_findings.csv`
- `outputs/stage2_methodology_audit/current_main_findings.csv`
- `outputs/stage2_methodology_audit/crosswalk_and_wage_decomposition.csv`
- `outputs/stage2_methodology_audit/treatment_strategy_wage_comparison.csv`
- `outputs/stage2_methodology_audit/salary_methodology_audit.csv`
- `outputs/stage2_methodology_audit/age_binary_reestimation.csv`
- `outputs/stage2_methodology_audit/age_comparison_summary.csv`
- `outputs/stage2_methodology_audit/pretrend_balance_summary.csv`
- `outputs/stage2_methodology_audit/final_answers_summary.csv`

## Verdict

Major revision to the dissertation interpretation, not rejection of the empirical strategy. The current MTE version is academically more defensible than the old crosswalk version, but the main narrative should no longer be a strong salary-loss claim. The safer contribution is: a corrected exposure assignment changes the aggregate salary finding, while employment-flow and heterogeneity patterns should be discussed with explicit pre-trend and balance caveats.
