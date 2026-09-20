# Occupation-Case Strategy for Dissertation Section 5.3

**Project:** Master's dissertation on generative-AI exposure and the Brazilian labor market  
**Reference:** Brynjolfsson, Chandar, and Chen (2025), *Canaries in the Coal Mine?*  
**Implementation date:** July 24, 2026  
**Empirical package:** `outputs/section5_3_occupation_cases/`

## Executive verdict

Section 5.3 should remain a **descriptive and comparative occupation-case extension**. It should not estimate six new DiDs or event studies, and it should not replace the aggregate causal design in Sections 5.1–5.2.

| Component | Verdict | Final treatment |
| --- | --- | --- |
| Six semantically defined occupation cases | **KEEP** | Main Section 5.3, one exposure table and two 2 × 3 figures |
| Admissions by age | **KEEP AS HEADLINE** | Main comparative outcome |
| Real admission wages by age | **KEEP WITH CONDITIONS** | Main figure; text restricted to time-baseline-stable patterns |
| Sex and education comparisons | **MOVE TO APPENDIX** | No consistent cross-case pattern under the frozen rule |
| Race/color comparison in admissions | **REDUCE** | One cautious sentence in Section 5.3; complete result in Appendix B |
| Four previous manual occupation groups | **MOVE TO LEGACY APPENDIX** | Preserve diagnostics; remove from headline manifest and editorial Top 30 |
| Occupation-specific causal claims | **EXCLUDE** | No case-specific control comparison is estimated |
| SOC–ISCO–CBO crosswalk as selection authority | **EXCLUDE** | Membership is based directly on official CBO6 titles and tasks |
| LLM-based membership | **EXCLUDE** | The dictionary was selected and reviewed manually |

The final Blindspot ruling is **CONDITIONAL**, not `HOLD`. The design is suitable for the dissertation if admissions carry the central comparison, unstable wage cells are not elevated to textual findings, production supervisors receive a composition caveat, and all demographic language remains descriptive.

## 1. What is taken from the reference paper

The six occupations in the opening figures of *Canaries* are descriptive case studies. The paper's central inference does not consist of six occupation-specific regressions; it uses the full occupation distribution, exposure quintiles, and firm-by-time variation.

Section 5.3 adopts only three elements from those figures:

1. the list and order of the six occupation cases;
2. the six age bands; and
3. normalization around October 2022.

The Brazilian exercise does not reproduce the reference paper's estimand. ADP measures employment stocks, whereas Novo CAGED measures formal labor-market flows. A decline in admissions is not equivalent to a decline in employment. The appropriate description is therefore a **Brazilian descriptive dialogue with the reference cases**, not a direct replication.

## 2. Frozen semantic dictionary

### 2.1 Selection rule

The occupation dictionary was frozen independently of post-ChatGPT coefficients. Inclusion relies on the official CBO6 title and task profile. No SOC-to-ISCO or ISCO-to-CBO correspondence is used as a gate, and no LLM decides membership.

Each dictionary row records:

- case and CBO6 identifiers;
- official occupation title;
- primary or sensitivity status;
- semantic rationale;
- mapping confidence;
- official source and URL; and
- retrieval date.

The canonical dictionary is `data/input/occupation_case_dictionary.csv`.

```text
SHA-256: b213f5ce089039c1976c57a1f7ca241badd9ac1a1689b8451c56d8f95b97b8cf
```

The source manifest is `data/input/occupation_case_dictionary_source_manifest.csv`.

```text
SHA-256: 5bf03505b66bb9399dd73f94b4991455ecf85da8847b34d7f76c63c5c2f63113
```

The dictionary-scoped extract of official titles, tasks, and synonyms is
`data/input/occupation_case_official_metadata.csv`. The production pipeline
uses this stable file and has no runtime dependency on temporary downloads.

```text
SHA-256: ad2e52ff5face4034c2975f6dfc687db51a45e30d99ca9b943e13bec50fbb9a2
```

### 2.2 Primary cases

| Case | Primary CBO6 rule | Codes |
| --- | --- | --- |
| Software developers | Software analysis, development, and technical programming occupations | `212205`, `212215`, `212405`, `212415`, `317105`, `317110`, `317120` |
| Customer service | Inbound and technical telemarketing operators | `422315`, `422320` |
| Marketing and sales managers | Official marketing-manager and sales-manager occupations | `142315`, `142320` |
| Production supervisors | All occupations in families `7201`, `7202`, `7301`, `7401`, `7501`, `7502`, `7601`–`7606`, `7701`, `7801`, `8101`–`8103`, `8201`, `8202`, `8301`, `8401`, and `8601`, except maintenance supervisor `860105` | 53 codes |
| Stock clerks and shelf replenishers | Warehouse, storage, stock, dispatch, and shelf-replenishment occupations | `414105`, `414110`, `414125`, `414135`, `521125` |
| Health and care aides | Nursing-aide, health-attendant, psychiatric-aide, elder-care, and health-caregiver occupations | `322220`, `322230`, `322235`, `322250`, `515110`, `516210`, `516220` |

The primary dictionary contains exactly **76 non-overlapping CBO6 codes**. This replaces the superseded 36-code proposal.

### 2.3 Pre-specified sensitivities

- Customer service: add `422310`.
- Production supervisors: remove `860110` and `860115` in the industry-restricted variant.
- Stock: add `414120` and `414140`; keep `414115` excluded.
- Health/care: restrict to `515110`, `516210`, and `516220`.

These variants test boundary choices; they do not replace the primary definition after results are observed.

## 3. Exposure is characterized after selection

The semantic cases are not labeled high, medium, or low using author discretion. After membership is frozen, each CBO6 inherits the dissertation's ILO classification at CBO4. Composition is weighted by admissions from January 2021 through October 2022.

| Case | Benchmark in *Canaries* | Brazilian ILO composition | Score coverage |
| --- | --- | --- | ---: |
| Software developers | High exposure | G3 64.6%; G2 29.9%; No score 5.5% | 94.5% |
| Customer service | High exposure | G3 100.0% | 100.0% |
| Marketing and sales managers | Quintile 4 | G2 100.0% | 100.0% |
| Production supervisors | Quintile 3 | Not Exposed 58.3%; Minimal Exposure 5.5%; No score 36.2% | 63.8% |
| Stock clerks and shelf replenishers | Quintile 2 | Minimal Exposure 100.0% | 100.0% |
| Health and care aides | Quintile 1 | Not Exposed 62.4%; Minimal Exposure 37.6% | 100.0% |

`No score` denotes missing defensible classification; it is never recoded as zero exposure. The Brazilian composition does not mechanically reproduce the U.S. ranking, which is substantively useful and must be discussed rather than hidden.

## 4. Data and outcomes

The pipeline reads Novo CAGED 2021–2025 once in yearly batches and retains admissions for the primary or sensitivity dictionaries from January 2021 through June 2025.

Age groups:

- 22–25;
- 26–30;
- 31–34;
- 35–40;
- 41–49; and
- 50 or older.

Outcomes:

1. monthly admission counts; and
2. monthly mean real admission wages among positive-wage records.

The main wage estimator winsorizes positive wage records at P1/P99 within CBO6 and calendar year before aggregation. This change from the initial specification was required because raw positive wages include demonstrably implausible values, with a maximum above R$70 billion. The raw mean and the originally planned cell-mean winsorization remain in the sensitivity matrix.

All 72 primary case-by-age-by-outcome cells meet the frozen October 2022 support threshold of 30 observations.

## 5. Normalization and diagnostic rules

The main path index sets October 2022 equal to 1. The fixed terminal metric is the average from January through June 2025 relative to this baseline.

Two time sensitivities are mandatory:

1. January–October 2022 mean equals 1; and
2. January–June 2025 compared month by month with January–June 2022.

Because no control group exists inside Section 5.3, the package does not perform causal pretrend tests by occupation case. It instead reports:

- observed and expected pre-period months;
- admissions and wage records;
- wage coverage;
- annualized pre-period slope; and
- coefficient of variation.

These diagnostics receive no stars and no causal pass/fail label.

## 6. Main results selected for the dissertation

### 6.1 Admissions

The admissions pattern is the strongest result.

- Software admissions are below October 2022 in every age band in the main metric, from −0.8% among workers aged 50 or older to −12.2% among ages 35–40. All six age-band signs remain negative under both alternative time comparisons.
- Customer service shows a clear age gradient: −15.0%, −9.9%, and −9.7% in the three youngest groups, compared with +17.3% at ages 41–49 and +29.7% at age 50 or older.
- Marketing and sales managers show weak or negative changes below age 35 and gains of +16.0% and +40.0% in the two oldest groups.
- Production supervisors increase in five robust age cells; the age-22–25 sign depends on normalization.
- Stock and health/care admissions increase in every age band and under every time comparison, with the largest increases among older workers.

Across the 36 case-by-age admission cells, 33 retain their direction under both alternative time baselines. This supports a comparative narrative in which the cases classified as more exposed in Brazil display weaker young-worker hiring than the minimally or non-exposed cases. It does not establish that AI caused the differences.

### 6.2 Real admission wages

Wage paths are less uniform and should not carry the section's central claim.

- Customer service is positive in all six age bands under all time comparisons.
- Stock is also positive in all six age bands under all time comparisons.
- Marketing and sales managers are negative in five of six age bands in the main metric and remain broadly negative in the sensitivities.
- Health/care wages fall strongly among workers aged 31 or older; the age-26–30 main sign is unstable.
- Production-supervisor wages are near zero and change sign under alternative time baselines.
- Software wages are modestly negative in the October-normalized metric, but most age-cell signs change under at least one alternative baseline.

Only 25 of 36 wage cells retain their direction under both time checks. The main figure should show every cell, but the prose should restrict interpretation to stable case-level patterns.

### 6.3 Demographic appendix

The pre-specified cross-case mention rule is passed only by the Black-versus-White admissions comparison:

- same direction in all six cases;
- support in every relevant cell;
- same direction under both alternative time baselines in all six cases; and
- median absolute difference of 31.3 percentage points.

This may appear once in Section 5.3 as a descriptive secondary finding. Sex, education, and all demographic wage comparisons remain in Appendix B because they fail at least one consistency criterion.

## 7. Blindspot decision

The full audit is `outputs/section5_3_occupation_cases/audit/section5_3_blindspot_report.md`.

### Material issues and disposition

| Issue | Disposition |
| --- | --- |
| Implausible raw wages dominate case means | Resolved with record-level CBO6-year P1/P99 winsorization; raw estimator retained as sensitivity |
| Single October baseline is seasonal | Mitigated with pre-mean and month-matched sensitivities |
| Broad supervisor case changes internal CBO composition | Flagged; disclose and retain restricted sensitivity |
| No case-specific control group | Disclosed; descriptive scope only |
| CAGED flows differ from ADP stocks | Disclosed in both main figures and text |
| Post-result selection risk | Controlled by frozen dictionary, complete reporting, and result-selection log |

The final ruling is `CONDITIONAL`. There is no unresolved reason to suppress the section.

## 8. Final artifact architecture

### Main text

- `table_5_3_1_occupation_case_exposure_summary.{csv,md}`
- `figure_5_3_1_occupation_cases_admissions_by_age.{png,pdf,svg}`
- `figure_5_3_2_occupation_cases_real_admission_wage_by_age.{png,pdf,svg}`

### Appendix B

- full dictionary and membership variants;
- age terminal matrix;
- monthly paths;
- pre-period diagnostics;
- exposure details;
- composition-shift diagnostics;
- normalization, composition, and wage sensitivities;
- demographic terminal matrices;
- Figures B.1–B.3 for sex, race/color, and education; and
- the legacy diagnostics of the four retired manual occupation groups.

The final Sections 4–5 package copies the dissertation-facing artifacts and excludes the former manual-group bar chart, forest plot, heatmap, focal Software/IT table, and manual-group tables from its headline manifest.

## 9. Exact narrative limits

Section 5.3 should contain six short paragraphs:

1. semantic selection, outcomes, normalization, and descriptive scope;
2. Brazilian exposure composition and its divergence from the reference ranking;
3. admissions patterns by age;
4. robust real admission-wage patterns and their sensitivity;
5. age synthesis and the one qualifying race/color pattern; and
6. comparison with the reference paper and overall interpretation.

Do not claim:

- a direct replication;
- an occupation-specific causal effect;
- that admissions are employment stocks;
- that `No score` means no exposure;
- that the six cases identify an ILO exposure gradient;
- that supervisors are a compositionally fixed occupation;
- that raw wage means are credible; or
- that the strongest observed coefficients determined case membership.

## 10. Reproduction

```bash
python src/scripts/build_section5_3_occupation_cases.py
python src/scripts/build_section4_5_final_package.py
```

The first command builds and audits the standalone occupation-case package. The second refreshes the curated Sections 4–5 package without re-estimating Section 5.3.
