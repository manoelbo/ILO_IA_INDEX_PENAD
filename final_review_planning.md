# Final Review Planning

**Project:** AI exposure and formal labor-market outcomes in Brazil  
**Review date:** 2026-07-25  
**Status:** Planning only — no methodological or narrative change is approved until the relevant task passes its acceptance gate.

## 1. Objective

Run one final, controlled review of the empirical study to:

1. Correct remaining conceptual, econometric, data-construction, and editorial errors.
2. Upgrade the use of Novo CAGED microdata, including CNAE and movement-type information.
3. Refresh the full analysis through June 2026 using one frozen data vintage.
4. Replace specification choices that are difficult to defend with a transparent estimator and robustness hierarchy.
5. Separate evidence about labor-market flows from claims about employment stocks, firm adoption, or vacancy replacement.
6. Deliver a reproducible dissertation chapter and replication package whose tables, figures, diagnostics, and prose agree exactly.

This is a methodological refinement round, not a search for more statistically significant results. All choices below must be implemented independently of whether they strengthen or weaken the current findings.

## 2. Final Design Decisions

### 2.1 Data window and event timing

| Element | Final-review default |
| --- | --- |
| Master sample | January 2021–June 2026 |
| Availability event | Public launch of ChatGPT on November 30, 2022 |
| First treated month | December 2022 |
| Event-study reference | November 2022 (`t = -1`) |
| Primary monthly event-study window | January 2021–November 2024 (`t = -23` to `t = +23`) |
| Long-run extension | December 2022–June 2026, reported in explicit horizons |
| Pandemic-window sensitivity | January 2022–June 2026 |
| Recent-data sensitivity | End the sample in December 2025 |

The launch date represents a public availability shock, not observed adoption by Brazilian firms. The study therefore estimates differential post-launch changes by predetermined occupational exposure. It must not be described as the direct effect of firm-level AI adoption.

The 100-million-user milestone, GPT-4 release, Brazilian mobile availability, ChatGPT Enterprise, and Microsoft Copilot releases may be annotated as diffusion milestones. They must not replace the main event date or be searched over as competing cutoffs.

### 2.2 Estimator hierarchy

| Outcome | Main estimator | Secondary specification |
| --- | --- | --- |
| Admissions | PPML with fixed effects and clustered inference | OLS on `log(1 + y)` |
| Separations | PPML with fixed effects and clustered inference | OLS on `log(1 + y)` |
| Gross worker flows | PPML | OLS on `log(1 + y)` |
| Separation types | PPML | Descriptive shares and levels |
| Real admission wage | OLS on log real wage, valid wage cells only | Alternative composition specifications |
| Real separation wage | Complementary OLS result | Appendix robustness |
| Net flow | Complementary outcome only | Alternative normalizations |

PPML is a quasi-maximum-likelihood estimator; the data do not need to follow a literal Poisson distribution. Report count-model effects as `100 × (exp(beta) - 1)`.

`log(1 + y)` remains useful because it targets a different transformed-outcome estimand and weights small and large occupation cells differently. It must not be presented as a direct percentage effect, and the dissertation must remove the false claim that the current national panel contains “many zeros.”

### 2.3 Control hierarchy

1. **Main specification:** no contemporaneous composition controls.
2. **Predetermined-control robustness:** pre-treatment characteristics interacted flexibly with calendar time.
3. **Conditional descriptive specification:** contemporaneous composition controls, explicitly labeled as potentially post-treatment and not interpreted as the total causal effect.

Contemporaneous admission composition must not be used as the preferred control set for separation outcomes.

### 2.4 Fixed-effect hierarchy

1. **National CBO-month benchmark:** CBO fixed effects and month fixed effects.
2. **Industry-enriched main model:** CBO×CNAE unit fixed effects and CNAE×month fixed effects.
3. **Occupation-cycle robustness:** add CBO2×month fixed effects when within-cell treatment support is adequate.
4. **Secure-data extension:** firm×CBO fixed effects and firm×month fixed effects, restricted to firms with within-firm variation in occupational exposure.

Treatment is assigned at the occupational level, so CBO clustering remains the primary inference level. Two-way CBO and CNAE clustering should be evaluated as a robustness check for the industry panel.

### 2.5 Dynamic-effect hierarchy

The primary monthly event study must not pool heterogeneous endpoint months. Use the balanced `-23` to `+23` window without clipping.

The full June 2026 extension must report:

- Horizon 1: December 2022–November 2023.
- Horizon 2: December 2023–November 2024.
- Horizon 3: December 2024–November 2025.
- Horizon 4, partial: December 2025–June 2026.

A single post-treatment coefficient may remain as a summary, but it is not the primary long-run estimand.

## 3. Non-Negotiable Conceptual Corrections

- Use **separations**, not **dismissals**, unless the outcome is explicitly restricted by `tipo_movimentacao`.
- Do not infer employment-stock destruction, preservation, or growth from CAGED flow outcomes.
- Do not interpret lower separations as proof of retention, junior-vacancy freezing, or non-replacement.
- Do not equate age with tenure, experience, or job seniority.
- Describe the main coefficient as a post-ChatGPT differential between exposed and non-exposed occupations.
- Use “absence of robust aggregate evidence,” not “absence of impact.”
- Correct the description of the ADP study: it uses employment stocks across a broad firm sample, not only technology firms.
- Do not call subgroup regressions DDD unless the estimated term is explicitly `post × treatment × subgroup`.
- Do not append pre-2020 CAGED and Novo CAGED as if they were one measurement-consistent monthly series.
- Do not select the start date, end date, event date, controls, or estimator based on p-values or pretrend-test outcomes.

## 4. Dependency Order

```text
Freeze the current baseline and correction ledger
    |
    v
Refresh and version all source data
    |
    v
Rebuild and validate national and CNAE-enriched panels
    |
    v
Estimate the PPML core and redesigned event windows
    |
    v
Run fixed-effect, pretrend, support, and sensitivity diagnostics
    |
    v
Estimate mechanisms and pre-specified heterogeneity
    |
    v
Regenerate every table, figure, and in-text statistic
    |
    v
Rewrite the interpretation and close editorial blockers
    |
    v
Run replication, link, visual, and final referee audits
```

## 5. Execution Plan

### Phase 0 — Freeze the Current Submission

#### Task 1: Create a frozen pre-review baseline

**Description:** Preserve the current data, outputs, regression specifications, dissertation text, and replication results before introducing the June 2026 refresh.

**Acceptance criteria:**

- [ ] A manifest records the current data window, row counts, CBO counts, result-file hashes, code revision, and extraction dates.
- [ ] Existing outputs remain reproducible and are not overwritten by refreshed outputs.
- [ ] The current Round 2 referee findings are copied into a correction ledger with an owner and final-review phase.

**Verification:**

- [ ] Re-run the existing Sections 4–5 validation suite.
- [ ] Confirm that frozen reference estimates match the current Python and R replications.
- [ ] Confirm that the worktree diff contains no accidental deletion or replacement of author files.

**Dependencies:** None.

**Likely areas:** replication manifest, frozen output directory, `correspondence/referee2/`.

**Estimated scope:** Medium.

#### Task 2: Lock the final methodological contract

**Description:** Convert the decisions in Section 2 into one machine-readable and one human-readable specification contract before estimation begins.

**Acceptance criteria:**

- [ ] Treatment, control, event date, sample windows, estimators, controls, fixed effects, clustering, and primary outcomes are named explicitly.
- [ ] Primary, robustness, exploratory, and appendix results are separated in advance.
- [ ] No implementation task may silently change the contract because a result is weak or a pretrend fails.

**Verification:**

- [ ] Every planned result table maps to exactly one specification in the contract.
- [ ] Every specification maps to a stated estimand and interpretation.

**Dependencies:** Task 1.

**Likely areas:** project methodology specification and analysis configuration.

**Estimated scope:** Small.

### Checkpoint A — Baseline and Contract

- [ ] Current results are frozen and reproducible.
- [ ] Outstanding Round 2 corrections are tracked.
- [ ] The new specification hierarchy is approved before data refresh.

### Phase 1 — Refresh and Rebuild the CAGED Data

#### Task 3: Refresh the complete Novo CAGED vintage through June 2026

**Description:** After the official June 2026 release, retrieve the full January 2021–June 2026 series in one extraction. Do not append only the new months because prior competencies can be revised by late declarations and exclusions.

**Acceptance criteria:**

- [ ] The source, query, extraction timestamp, data vintage, schema, and checksums are recorded.
- [ ] All months from January 2021 through June 2026 are present exactly once.
- [ ] A revision table compares overlapping 2021–2025 counts with the frozen vintage.
- [ ] IPCA and any minimum-wage inputs used by the analysis are updated through the required 2026 period from official sources.

**Verification:**

- [ ] Monthly national admissions, separations, and net flows reconcile to official aggregates within a documented tolerance.
- [ ] No month, state, CBO, or source component is silently missing.
- [ ] The raw snapshot can be reconstructed or independently verified from the extraction metadata.

**Dependencies:** Task 2 and official June 2026 data availability.

**Likely areas:** raw-data extraction, price data, data-vintage manifest.

**Estimated scope:** Medium.

#### Task 4: Correct movement-level data construction

**Description:** Repair the known construction risks before aggregating the refreshed microdata.

**Acceptance criteria:**

- [ ] Zero is filled only for count outcomes; wages and composition variables remain missing when their relevant flow is zero.
- [ ] `tipo_movimentacao` is retained and mapped to documented separation categories.
- [ ] CNAE is retained at its original level and a documented aggregation, preferably CNAE division, is created.
- [ ] All generic “dismissal” labels are replaced by “separation” unless the underlying filter is employer dismissal.
- [ ] Duplicate, unmatched, invalid-CBO, invalid-CNAE, and missing-value diagnostics are exported.

**Verification:**

- [ ] Wage cells with no corresponding admissions or separations are missing, not zero.
- [ ] Aggregate admissions and separations equal the sum of movement-level categories.
- [ ] The refresh passes explicit merge cardinality and row-count assertions.

**Dependencies:** Task 3.

**Likely areas:** `src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py` and data QA outputs.

**Estimated scope:** Medium.

#### Task 5: Build two public-data analysis panels

**Description:** Preserve the current national benchmark and add an industry-enriched panel.

**Acceptance criteria:**

- [ ] Panel A is CBO4×month and reproduces the corrected national benchmark.
- [ ] Panel B is CBO4×CNAE2×month and supports CNAE×month fixed effects.
- [ ] Both panels retain treatment classification, movement types, valid outcome missingness, and the frozen crosswalk specification.
- [ ] Support tables report treated/control CBOs, industries, cell counts, zero shares, and attrition at every sample restriction.

**Verification:**

- [ ] Aggregating Panel B over CNAE reproduces Panel A within documented rounding rules.
- [ ] No `CBO4×CNAE2×month` duplicate exists.
- [ ] Treatment and control coexist within enough CNAE×month and CBO2×month cells to identify the planned models.

**Dependencies:** Task 4.

**Likely areas:** panel builder, section 4 data loader, support-audit outputs.

**Estimated scope:** Medium.

#### Task 6: Specify the secure firm-level extension

**Description:** Define the FGV secure-room extension separately from the public-data dissertation baseline.

**Acceptance criteria:**

- [ ] The target panel is defined as firm×CBO×month.
- [ ] Firm×CBO and firm×month fixed effects, minimum within-firm exposure variation, and confidentiality output rules are specified.
- [ ] A separate plan states whether RAIS linkage can supply employment stocks and pre-pandemic validation.
- [ ] Replacement is defined as an observable firm-occupation separation followed by an admission within a pre-specified horizon.

**Verification:**

- [ ] The design cannot claim firm adoption without an actual adoption measure.
- [ ] The public analysis remains fully reproducible without secure data.

**Dependencies:** Task 2; execution depends on secure-room access.

**Likely areas:** secure-data protocol only.

**Estimated scope:** Small for specification; separate implementation project.

### Checkpoint B — Data Readiness

- [ ] One frozen June 2026 data vintage exists.
- [ ] National and CNAE panels reconcile.
- [ ] Count, wage, movement-type, and missing-value checks pass.
- [ ] Identification support is documented before regression estimation.

### Phase 2 — Re-estimate the Core Design

#### Task 7: Implement static and dynamic PPML

**Description:** Make PPML the primary estimator for admissions, separations, and gross flows, using the same sample and fixed-effect contract in static and dynamic models.

**Acceptance criteria:**

- [ ] Static PPML produces coefficients, clustered standard errors, confidence intervals, p-values, observations, and cluster counts.
- [ ] Dynamic PPML estimates all planned leads and lags without reusing OLS pretrend diagnostics.
- [ ] `log(1 + y)` results are retained in a clearly labeled robustness table.
- [ ] Singleton removal, separation, convergence, and collinearity are reported.

**Verification:**

- [ ] A small independent implementation reproduces selected PPML coefficients.
- [ ] Percentage-effect transformations are tested numerically.
- [ ] Static and dynamic models use the intended samples and fixed effects.

**Dependencies:** Task 5.

**Likely areas:** `src/scripts/section4_event_study/estimation.py`, pipeline, tests, model audit outputs.

**Estimated scope:** Medium.

#### Task 8: Replace endpoint clipping with explicit windows and horizons

**Description:** Separate the balanced monthly event study from the long-run June 2026 extension.

**Acceptance criteria:**

- [ ] The primary monthly model estimates `t = -23` through `t = +23` without pooling earlier or later months.
- [ ] The full model estimates the four named post-treatment horizons.
- [ ] January 2022 and December 2025 cutoff sensitivities are run exactly as specified.
- [ ] No December 2022–January 2023 observation is reclassified as untreated in an alternative diffusion-date model.

**Verification:**

- [ ] Every plotted coefficient maps to a single month or an explicitly labeled range.
- [ ] No hidden `clip()` operation pools heterogeneous endpoints.
- [ ] Monthly and horizon sample counts reconcile.

**Dependencies:** Task 7.

**Likely areas:** event-time configuration, event-data preparation, event-study figures.

**Estimated scope:** Medium.

#### Task 9: Estimate the fixed-effect and control ladder

**Description:** Quantify how estimates change when industry shocks, broad occupation cycles, and control choices are absorbed.

**Acceptance criteria:**

- [ ] National CBO+month results are reported as the benchmark.
- [ ] CBO×CNAE unit FE plus CNAE×month FE is the industry-enriched model.
- [ ] CBO2×month FE is added only when support remains adequate.
- [ ] No-contemporaneous-control results are primary.
- [ ] Predetermined and contemporary-control specifications are labeled according to the hierarchy in Section 2.3.

**Verification:**

- [ ] A specification table reports coefficient, interval, sample size, clusters, support, convergence, and exact fixed effects.
- [ ] Any large estimate change is traced to sample, weighting, fixed effects, or controls.
- [ ] Two-way-clustering sensitivity is reported when computationally and inferentially appropriate.

**Dependencies:** Tasks 7 and 8.

**Likely areas:** section 4 configuration, pipeline, specification-ladder tables.

**Estimated scope:** Medium.

### Checkpoint C — Core Econometrics

- [ ] PPML static and event-study models run.
- [ ] The balanced and long-run windows are distinct.
- [ ] The industry and control ladders are complete.
- [ ] No preferred specification was selected by significance.

### Phase 3 — Identification, Mechanisms, and Heterogeneity

#### Task 10: Rebuild pretrend and sensitivity diagnostics

**Description:** Diagnose parallel-trend credibility in the exact preferred models and quantify sensitivity rather than treating a non-significant pretest as proof.

**Acceptance criteria:**

- [ ] Joint lead tests are computed for the exact PPML model and sample.
- [ ] Lead plots and confidence intervals use the same reference month and fixed effects as the reported model.
- [ ] Rambachan–Roth/HonestDiD-style sensitivity is reported for headline outcomes when technically compatible; limitations for nonlinear models are documented.
- [ ] Failed or warning diagnostics automatically trigger non-causal narrative language.

**Verification:**

- [ ] Pretrend tables name the test type, window, statistic, p-value, and model.
- [ ] Linear-trend, joint-lead, and dynamic diagnostics are never described as the same test.
- [ ] Results remain visible when diagnostics fail; they are not deleted.

**Dependencies:** Task 9.

**Likely areas:** pretrend tests, sensitivity scripts, diagnostic tables.

**Estimated scope:** Medium.

#### Task 11: Add mechanism-relevant flow outcomes

**Description:** Replace unsupported mechanism stories with outcomes that can distinguish competing explanations.

**Acceptance criteria:**

- [ ] Gross flows are defined as admissions plus separations.
- [ ] Separations are decomposed into pre-specified movement-type families, including voluntary and employer-initiated exits where supported.
- [ ] Net flow remains complementary and is not treated as employment stock.
- [ ] Retention, worker lock-in, and non-replacement are described as hypotheses unless directly tested.

**Verification:**

- [ ] Movement categories sum to total separations.
- [ ] Every mechanism paragraph cites an observable outcome or is explicitly labeled speculative.
- [ ] Stock or replacement claims appear only if RAIS/firm-level evidence is available.

**Dependencies:** Tasks 4 and 9.

**Likely areas:** panel construction, outcome configuration, mechanism tables.

**Estimated scope:** Medium.

#### Task 12: Re-run and discipline heterogeneity

**Description:** Re-estimate age and other subgroup results using the final estimator, windows, fixed effects, and control hierarchy.

**Acceptance criteria:**

- [ ] Exact Canaries-style age bins and broader Brazilian age bins are clearly separated.
- [ ] The primary subgroup family is named before reviewing refreshed results.
- [ ] Multiple-testing adjustments are reported within coherent outcome×subgroup families.
- [ ] Thin support, failed pretrends, and exploratory results are moved to the appendix or downgraded in language.

**Verification:**

- [ ] Every DDD table contains the explicit triple interaction.
- [ ] Age is not translated into junior, mid-level, experience, or tenure.
- [ ] All subgroup tables report support, observations, clusters, pretrend status, and adjusted inference.

**Dependencies:** Tasks 9 and 10.

**Likely areas:** heterogeneity pipeline, Section 5 tables and figures.

**Estimated scope:** Medium.

#### Task 13: Add a Brazilian diffusion validation

**Description:** Use Brazilian adoption evidence to validate timing without replacing the exogenous launch date.

**Acceptance criteria:**

- [ ] A frozen Google Trends series is downloaded for the ChatGPT topic in Brazil with query metadata.
- [ ] The series is used descriptively and, if estimated, through a pre-specified exposure×diffusion interaction.
- [ ] OpenAI Signals, IBGE, or Cetic evidence is used only within its actual coverage and population.
- [ ] No search-interest threshold is promoted to the primary event because it improves the outcome results.

**Verification:**

- [ ] The text distinguishes awareness, consumer use, workplace use, and firm adoption.
- [ ] Google Trends values are described as normalized search interest, not user counts.
- [ ] The diffusion extension is clearly labeled non-primary.

**Dependencies:** Task 2; estimation depends on Task 9.

**Likely areas:** external-data input, diffusion-validation appendix.

**Estimated scope:** Small.

### Checkpoint D — Identification and Interpretation

- [ ] Exact-model pretrend diagnostics are complete.
- [ ] Failed diagnostics are reflected in the causal language.
- [ ] Mechanism claims are tied to observable outcomes.
- [ ] Heterogeneity is support-gated and multiplicity-aware.
- [ ] Brazilian diffusion evidence is validation, not cutoff shopping.

### Phase 4 — Rewrite, Regenerate, and Audit

#### Task 14: Regenerate all empirical outputs

**Description:** Produce the final tables, figures, appendices, and in-text statistics from the refreshed pipeline.

**Acceptance criteria:**

- [ ] Panel-scope, zero-share, coverage, result, support, pretrend, and robustness tables use the June 2026 vintage.
- [ ] Figures identify the event, reference month, estimator, confidence level, sample window, and endpoint definition.
- [ ] Every in-text number has a computational authority.
- [ ] The replication package contains the required Appendix B tables with working relative paths.

**Verification:**

- [ ] Re-running the pipeline regenerates all final artifacts.
- [ ] Table values match source CSV files and figure metadata match source coefficients.
- [ ] No broken links, missing files, manual table rows, or stale 2025 scope counts remain.

**Dependencies:** Tasks 10–13.

**Likely areas:** final package builders, outputs, replication package.

**Estimated scope:** Medium.

#### Task 15: Rewrite the methodology and findings

**Description:** Align the dissertation prose with the final estimands, data vintage, diagnostics, and evidence hierarchy.

**Acceptance criteria:**

- [ ] The methodology states PPML as the main count estimator and defines its interpretation.
- [ ] The window section explains the 2021 start, December 2022 first-treated month, balanced monthly window, and June 2026 horizons.
- [ ] The control section distinguishes main, predetermined, and potentially post-treatment controls.
- [ ] Flow results never imply stock effects.
- [ ] The age comparison with Canaries is factually correct and mechanism-conservative.
- [ ] The conclusion distinguishes robust findings, suggestive findings, null/imprecise results, and exploratory extensions.

**Verification:**

- [ ] A claim-to-output audit traces every quantitative and causal statement.
- [ ] Search checks find no stale “many zeros,” generic “dismissals,” “tech firms only,” unsupported “vacancy freeze,” or over-strong “effect/impact” language.
- [ ] All dates, table numbers, appendix references, significance legends, and citations are consistent.

**Dependencies:** Task 14.

**Likely areas:** `dissetação_texto.md`, final exported chapter, citations.

**Estimated scope:** Medium.

#### Task 16: Close existing editorial and packaging blockers

**Description:** Resolve the remaining Round 2 findings after final tables are regenerated, avoiding rework on obsolete tables.

**Acceptance criteria:**

- [ ] Appendix A.6 has the correct header and row ordering.
- [ ] All Appendix B tables are embedded or bundled and all links work outside Notion.
- [ ] Flow-versus-stock and exposure-versus-effect language is corrected.
- [ ] Remaining legend, punctuation, heading hierarchy, appendix terminology, and file-reference defects are removed.

**Verification:**

- [ ] All Round 2 acceptance gates pass.
- [ ] The exported document works in a clean environment without Notion-local links.

**Dependencies:** Tasks 14 and 15.

**Likely areas:** dissertation export and replication package.

**Estimated scope:** Small.

#### Task 17: Run the final independent audit

**Description:** Re-run code, replication, output, econometric, editorial, and visual audits on the completed review.

**Acceptance criteria:**

- [ ] The full public pipeline runs from frozen inputs to final outputs.
- [ ] Independent implementations match selected headline estimates within a declared tolerance.
- [ ] All validation, replication, link, table, figure, and narrative checks pass.
- [ ] A final Referee 2 report has no unresolved major or moderate finding.

**Verification:**

- [ ] Clean-environment replication succeeds.
- [ ] Final result and artifact hashes are recorded.
- [ ] The final package is marked ready for circulation only after all gates pass.

**Dependencies:** Task 16.

**Likely areas:** tests, replication scripts, final audit reports.

**Estimated scope:** Medium.

### Checkpoint E — Final Acceptance

- [ ] Data run through June 2026 in one frozen vintage.
- [ ] PPML is the main count estimator and has a matching dynamic event study.
- [ ] The balanced monthly window and long-run horizons are both reported.
- [ ] CNAE×month and control-hierarchy results are complete.
- [ ] Exact-model pretrends and sensitivity diagnostics are disclosed.
- [ ] Mechanisms and heterogeneity obey support and inference gates.
- [ ] All prose matches the estimands and observed outcomes.
- [ ] The dissertation and replication package pass independent audit.

## 6. Priority Summary

### P0 — Required before circulation

- Freeze and version the June 2026 data.
- Fix count/wage missing-value construction.
- Implement PPML static and dynamic models.
- Remove endpoint pooling and report explicit horizons.
- Remove contemporaneous controls from the preferred causal specification.
- Add CNAE×month fixed effects using a properly rebuilt panel.
- Re-run exact-model pretrend diagnostics.
- Correct separations, flow-versus-stock, adoption, and effect language.
- Regenerate all outputs and close current Round 2 blockers.

### P1 — Strongly recommended for a materially better study

- Decompose separation types.
- Add gross worker flows.
- Run January 2022 and December 2025 window sensitivities.
- Add CBO2×month and clustering robustness where support permits.
- Apply multiplicity discipline to heterogeneity.
- Add Brazilian diffusion validation.
- Specify and, if feasible, execute the secure firm-level design.

### P2 — Optional extensions

- Link RAIS to study employment stocks and historical trends.
- Construct direct firm-occupation replacement outcomes.
- Add further geographic heterogeneity only after the national and industry designs pass all gates.
- Explore alternative exposure measures only as pre-labeled robustness exercises.

## 7. Principal Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Pandemic recovery remains correlated with occupational exposure | High | Keep 2021 in the main sample, add CNAE×month/CBO2×month FE, report January 2022 sensitivity, and use honest sensitivity analysis |
| Longer post-period captures unrelated macro and technology shocks | High | Report explicit yearly horizons and weaken attribution at longer horizons |
| Latest Novo CAGED months are revised later | Medium | Freeze the full extraction vintage, compare revisions, and report a December 2025 endpoint sensitivity |
| Industry panel becomes sparse | High | Audit within-cell support, publish attrition, and avoid over-saturated FE specifications without identifying variation |
| PPML and log specifications answer different questions | Medium | State both estimands, keep the hierarchy fixed, and report both without significance-based selection |
| Post-treatment controls bias the preferred estimate | High | Use no contemporaneous controls in the main model and pre-treatment controls only in robustness |
| Flow results are interpreted as stock or replacement effects | High | Enforce claim-to-outcome checks and require RAIS/firm evidence for stock or replacement language |
| Many subgroup tests generate false discoveries | Medium | Pre-designate primary families, report adjusted inference, and demote thin-support results |
| Secure firm sample is selected toward large multi-occupation firms | Medium | Report the support population and keep public-data results as the primary reproducible baseline |
| Refreshed results invalidate existing narrative | Expected | Rewrite from regenerated outputs; never preserve a claim because it was previously prominent |

## 8. Final Deliverables

1. Frozen current baseline and June 2026 data-vintage manifests.
2. Corrected national CBO-month and CBO×CNAE×month panels.
3. Static PPML, dynamic PPML, fixed-effect ladder, and horizon results.
4. Exact-model pretrend, support, sensitivity, and multiplicity diagnostics.
5. Movement-type, gross-flow, and disciplined heterogeneity results.
6. Brazilian diffusion validation appendix.
7. Updated Sections 4–5 and appendices with generated tables and figures.
8. Updated public replication package.
9. Secure-room protocol and separate firm-level extension, if access is available.
10. Final independent audit report with an explicit circulation verdict.

## 9. Definition of Done

The final review is complete only when the study can make the following defensible statement:

> Using a frozen Novo CAGED vintage through June 2026, the study estimates how formal labor-market flows evolved differentially across occupations with higher and lower predetermined exposure to generative AI after the public launch of ChatGPT. The preferred count models use PPML, absorb documented industry-time shocks, disclose exact-model pretrend and support diagnostics, separate short- and long-run horizons, and avoid interpreting flows as employment stocks or observed firm adoption.

Completion is determined by data, code, econometric, replication, and editorial gates—not by whether the final coefficients are statistically significant.
