# Referee 2 audit report: dissertation Sections 4–5

## Executive ruling

**HOLD pending correction.** The core computational results are reproducible, and the 13 figures resolve to their declared sources. However, Appendix A.6 is a critical editorial failure: both income panels reproduce education results. The methods also describe an obsolete four-group mechanism exercise instead of the six occupation cases actually presented.

After those critical corrections, the substantive ruling becomes **CONDITIONAL**: results may be reported as short-run, exploratory exposure-by-post associations, not as direct effects of AI adoption or evidence that employment stocks were preserved.

## Scope

- Exported HTML: 23 tables and 13 figures.
- Table cells reviewed, including headers: 1,424.
- Narrative and external claims: screened in the claim ledger.
- Independent models: three national DiDs and five income DDDs in Python and R.
- Stata: not run because it is unavailable in the environment.
- Author code, replication package, HTML and dissertation: not modified.

## Computational replication

Python and R agree to a maximum absolute difference of 5.385e-12 across coefficients, CRV1 standard errors and p-values. All eight selected estimates also agree with the frozen author outputs at the 1e-8 tolerance.

| model_id                              | coefficient_python   | standard_error_python   | p_value_python     | coefficient_r       | standard_error_r   | p_value_r          | status   |
|:--------------------------------------|:---------------------|:------------------------|:-------------------|:--------------------|:-------------------|:-------------------|:---------|
| national_ln_admissoes                 | -0.0308787948103299  | 0.0262877745409276      | 0.2409589210347981 | -0.0308787948101683 | 0.026287774540928  | 0.2409589210372631 | pass     |
| national_ln_desligamentos             | -0.0416583904078544  | 0.0254181321975795      | 0.1021540182055647 | -0.0416583904077702 | 0.0254181321975806 | 0.1021540182062701 | pass     |
| national_ln_salario_adm               | -0.0207064895904531  | 0.0139919807485822      | 0.1398305308731776 | -0.0207064895904768 | 0.0139919807485841 | 0.1398305308727796 | pass     |
| income_low_income_ln_admissoes        | 0.1399086361322515   | 0.0576627358106019      | 0.0152525324863696 | 0.1399086361321708  | 0.0576627358105931 | 0.0152525324864128 | pass     |
| income_low_income_ln_desligamentos    | 0.1182256940974542   | 0.0562066336205417      | 0.0354297914173489 | 0.1182256940975133  | 0.056206633620523  | 0.035429791417196  | pass     |
| income_middle_income_ln_admissoes     | -0.1509592018188606  | 0.0610399396594658      | 0.0133938508140784 | -0.1509592018241405 | 0.0610399396594364 | 0.0133938508107919 | pass     |
| income_middle_income_ln_desligamentos | -0.1834841639725477  | 0.0568541300804035      | 0.0012497335521378 | -0.1834841639779331 | 0.0568541300803282 | 0.0012497335517053 | pass     |
| income_high_income_ln_desligamentos   | 0.2452727750889861   | 0.124335108769857       | 0.0485325888240556 | 0.2452727750842011  | 0.124335108769863  | 0.048532588828454  | pass     |

The replicated national point estimates are:

- Admissions: beta = -0.0308788, or -3.04%, p = 0.241.
- Separations: beta = -0.0416584, or -4.08%, p = 0.102.
- Real admission wage: beta = -0.0207065, or -2.05%, p = 0.140.

The selected income DDDs reproduce the omitted countervailing evidence:

- Up to 2 minimum wages, admissions: beta = 0.1399, +15.0%, p = 0.015; pretrend fails.
- Up to 2 minimum wages, separations: beta = 0.1182, +12.6%, p = 0.035; pretrends pass.
- 2–5 minimum wages, admissions: beta = -0.1510, -14.0%, p = 0.013; pretrend fails.
- 2–5 minimum wages, separations: beta = -0.1835, -16.8%, p = 0.001; pretrends pass.
- Above 5 minimum wages, separations: beta = 0.2453, +27.8%, p = 0.049; support is only 3 treated and 7 controls.

## Table and figure audit

- Tables T01–T21 match their computational authorities after semantic normalization.
- Tables T22–T23 are the wrong content. 162 body cells are marked critical in the ledger and full replacements are supplied.
- All 13 figures pass reference, source, dimension and visual-RMS checks.
- The package's HTML table views correctly preserve what was in the HTML, but this means they also preserve the A.6 copy error. They should be understood as editorial snapshots, not independent computational validation.

## Econometric audit

1. **Estimand.** The national coefficient is exposure-group × post, not observed adoption. DDDs are correctly specified as post × treatment × subgroup with lower interactions.
2. **Pretrends.** National admissions and separations fail. Several demographic event studies also fail or warn. The salary-income sentence incorrectly says joint tests reject in the first two income groups: their joint p-values are 0.417 and 0.277; the diagnostic fails because each has three individually significant leads.
3. **Flows versus stocks.** Admissions and separations do not identify the employment stock. Simultaneous flow declines are compatible with lower turnover but cannot establish no job destruction.
4. **Support.** The high-income comparison is too thin for substantive inference (3/7 CBOs). Middle income is limited (28/32).
5. **Multiplicity.** Heterogeneity p-values are unadjusted. The synthesis must not present selected nominal results as a stable general pattern.
6. **Windows.** Table A.1 and Figure 5.1 use different event-study samples. Their p-values differ but pass/fail classifications agree; this must be labeled.

## External-source audit

| citation                                    | claim_reviewed                                                             | status                      | recommended_action                                                                         |
|:--------------------------------------------|:---------------------------------------------------------------------------|:----------------------------|:-------------------------------------------------------------------------------------------|
| Brynjolfsson, Chandar and Chen (2025)       | ADP coverage, age concentration, six cases and relative employment decline | correction_required         | Replace 13% with 16%.                                                                      |
| Ministry of Labour and Employment           | Novo CAGED reporting system                                                | wording_correction_required | Correct the data-system description.                                                       |
| OpenAI (2022)                               | Public launch date of ChatGPT                                              | verified                    |                                                                                            |
| ILO Working Paper 140 (2025)                | Four exposure gradients and greater female exposure                        | verified                    |                                                                                            |
| Humlum and Vestergaard (2025)               | Danish earnings and hours effects                                          | verified                    |                                                                                            |
| Chandar (2025)                              | CPS aggregate employment and earnings                                      | verified_with_qualification | Retain the heterogeneity qualification.                                                    |
| Aldasoro et al. (2026)                      | AI adoption, productivity and employment                                   | wording_correction_required | Specify the EU/US matched sample and the 4% estimate.                                      |
| Hosseini Maasoum and Lichtinger (2025/2026) | Hiring versus separation mechanism                                         | verified                    |                                                                                            |
| Klein Teeselink (2025)                      | Employment, hiring, postings and temporal ordering                         | correction_required         | Remove the unsupported claim that postings decline before any employment-stock adjustment. |

## Correction inventory

Critical: 2; major: 12; moderate: 10; minor: 20.

The authoritative, paste-ready list is in `2026-07-25_round1_sections4_5_corrections_only.md`. Every table cell and screened narrative claim is in `2026-07-25_round1_sections4_5_claim_ledger.csv`.
Hashes for every generated audit artifact are in `2026-07-25_round1_sections4_5_audit_manifest.csv`.

## Validation

| check_id                                 | status   | observed       | expected     | detail                                                        |
|:-----------------------------------------|:---------|:---------------|:-------------|:--------------------------------------------------------------|
| html_table_count                         | pass     | 23             | 23           | Editorial table inventory.                                    |
| html_figure_count                        | pass     | 13             | 13           | Editorial figure inventory.                                   |
| table_mismatches_are_only_known_a6_error | pass     | 0              | 0            | T22–T23 are expected known editorial errors.                  |
| a6_error_detected                        | pass     | T22,T23        | T22,T23      | Income appendix must not silently pass.                       |
| all_figures_resolved                     | pass     | 13             | 13           | All figure references and visual comparisons pass.            |
| correction_needles_found                 | pass     | 44             | 44           | Every registered correction is anchored in the HTML or table. |
| python_r_source_replication              | pass     | 5.385e-12      | <=1e-8       | Python, R and author outputs agree.                           |
| replication_package_unchanged            | pass     | True           | True         | The entire Replication Package tree is hash-identical.        |
| a6_replacement_shape                     | pass     | (12, 9);(6, 9) | (12,9);(6,9) | Complete income main and balance panels.                      |
| table_cell_ledger_complete               | pass     | 1424           | 1424         | Every header and body cell has a ledger row.                  |
| phase1_validation_still_green            | pass     | 121            | 121          | Frozen Phase 1 validation report remains green.               |
