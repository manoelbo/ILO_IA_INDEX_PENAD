# Section 4 Results Package

## Objective

Generate a reproducible empirical package for dissertation Section 4, including the corrected CAGED preparation step, the aggregate and conceptual-decomposition results, sociodemographic heterogeneity tables rebuilt from raw CAGED microdata, and a final Portuguese Markdown report with the requested figure and tables.

## Original Request

Prepare a GoalBuddy goal for the updated Section 4 results package plan.

## Intake Summary

- Input shape: `existing_plan`
- Audience: dissertation author and research team
- Authority: `requested`
- Proof type: `artifact`
- Completion proof: `outputs/dissertation_section4/` contains the requested Portuguese report, Figure 1, Tables 1, 2, 3A-3D in Markdown and CSV, the long heterogeneity audit CSV, and the validation loop passes after regenerating the affected data.
- Goal oracle: run the full execution loop and verify that all requested artifacts exist, use the required specifications, include significance stars, preserve the baseline result, and fail on the validation gates named by the user.
- Likely misfire: producing a polished report or partial tables without correcting the sex mapping, rebuilding heterogeneity from raw CAGED microdata, validating exposure definitions, checking baseline parity, or proving the final tables contain the requested outcomes and stars.
- Blind spots considered: raw CAGED codebooks may differ from assumptions; salary-minimum conversion needs an explicit source or local table; regression sample loss may hide treated/control CBO drops; scenario-grid outputs may be stale; generated outputs may touch paths outside the final package directory.
- Existing plan facts: preserve the user's four-section result structure, four exposure definitions, Table 3 panels, validation gates, output paths, model formulas, execution loop, and assumptions.

## Goal Oracle

The oracle for this goal is:

`python src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py && python src/scripts/etapa_2b_analise_did_caged_ilo.py && python src/scripts/run_treatment_scenario_grid.py && python src/scripts/build_dissertation_section4_results.py && python -m py_compile src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py src/scripts/build_dissertation_section4_results.py && git diff --check -- src/scripts outputs/dissertation_section4`

The final audit must also inspect the generated artifacts and confirm:

- `crosswalk_spec` is `mte_official_no_numeric_fallback`.
- All four exposure definitions exist in `scenario_cbo_classification.csv`.
- The regenerated baseline does not diverge from the Stage 2b result.
- `pct_mulher_adm` is not all zero after the sex-code correction.
- Every final table includes `*`, `**`, or `***` significance notation where applicable.
- Every Table 3 scenario has all four outcomes: admissions, separations, net balance, and real admission wage.
- Raw-microdata reconstruction records any treated or control CBO loss and the reason.
- The final report is in Portuguese, while scripts and code comments remain in English.

The PM must keep comparing task receipts to this oracle. Planning, discovery, a passing small slice, or a clean-looking board is not enough. The goal finishes only when a final Judge/PM audit maps receipts and verification back to this oracle and records `full_outcome_complete: true`.

## Goal Kind

`existing_plan`

## Current Tranche

Complete the full local implementation tranche for the Section 4 package. The first active task validates the existing plan against repository evidence and sets exact Worker scopes. After that, continue through the largest safe Worker packages: fix Stage 2a validation, build the Section 4 results script and output package, run the full regeneration loop, and audit completion.

## Non-Negotiable Constraints

- Do not edit notebooks in this stage.
- Keep the main specification as `baseline_mte2d_top20_vs_rest`.
- Treat `high_transformation_g34_vs_unexposed`, `augmentation_g12_vs_unexposed`, and `any_exposed_g1234_vs_unexposed` as conceptual decomposition scenarios, not the main robustness result.
- Rebuild Table 3 from raw CAGED microdata, not from current aggregate proxies.
- Correct Stage 2a to use `CODIGO_SEXO_MULHER = 3` because raw CAGED uses `sexo = 1` and `sexo = 3`.
- Add validation that fails if `pct_mulher_adm.max() == 0`.
- Validate raw `sexo`, `raca_cor`, and `grau_instrucao` codes before recoding groups.
- Income panels must classify CBOs by pre-treatment median wage in minimum-wage units: up to 2, more than 2 to 5, and more than 5 minimum wages.
- Age panels must use 14-24, 25-34, 35-59, and 60+.
- Final report language is Portuguese.
- Scripts, code comments, task receipts, and shared Markdown control docs are in English.
- If a loop command fails, fix the cause and rerun from the first affected script.

## Required Outputs

```text
outputs/dissertation_section4/
  section4_results_report.md
  figures/figure1_event_study_aggregate.png
  tables/table1_main_effects.md
  tables/table1_main_effects.csv
  tables/table2_exposure_types.md
  tables/table2_exposure_types.csv
  tables/table3_heterogeneity_baseline_mte2d_top20_vs_rest.md
  tables/table3_heterogeneity_baseline_mte2d_top20_vs_rest.csv
  tables/table3_heterogeneity_high_transformation_g34_vs_unexposed.md
  tables/table3_heterogeneity_high_transformation_g34_vs_unexposed.csv
  tables/table3_heterogeneity_augmentation_g12_vs_unexposed.md
  tables/table3_heterogeneity_augmentation_g12_vs_unexposed.csv
  tables/table3_heterogeneity_any_exposed_g1234_vs_unexposed.md
  tables/table3_heterogeneity_any_exposed_g1234_vs_unexposed.csv
  tables/table3_heterogeneity_all_scenarios_long.csv
```

## Stop Rule

Stop only when a final audit proves the full original outcome is complete.

Do not stop after planning, discovery, or Judge selection if a safe Worker task can be activated.

Do not stop after only fixing Stage 2a, only creating the builder script, or only generating partial artifacts. Continue until the requested package is generated and verified, or until a specific task is blocked with a receipt and the PM has exhausted safe local workarounds.

Do not create one Worker/Judge pair per table when the same script can generate and validate the whole package. Review at the plan-validation boundary, after the implementation package, and at final completion.

## Slice Sizing

Safe means bounded, explicit, verified, and reversible. It does not mean tiny.

A good task is the largest safe useful slice.

For this goal, the useful slices are:

1. Validate the plan and exact repo evidence before writes.
2. Apply the Stage 2a correction and defensive validations.
3. Build the Section 4 script and generated package.
4. Run the full loop, repair failures from the first affected script, and audit all artifacts.

## Canonical Board

Machine truth lives at:

`docs/goals/section4-results-package/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/section4-results-package/goal.md.
```

## PM Loop

On every `/goal` continuation:

1. Read this charter.
2. Read `state.yaml`.
3. Run the bundled GoalBuddy update checker when available and mention a newer version without blocking.
4. Re-check the intake: original request, input shape, authority, proof, blind spots, existing plan facts, and likely misfire.
5. Work only on the active board task.
6. Assign Scout, Judge, Worker, or PM according to the task.
7. Write a compact task receipt.
8. Update the board.
9. If safe local work remains, choose the next largest reversible Worker package and continue unless blocked.
10. Review at phase, risk, rejected-verification, ambiguity, or final-completion boundaries.
11. Finish only with a Judge/PM audit receipt that maps receipts and verification back to the original user outcome and records `full_outcome_complete: true`.
