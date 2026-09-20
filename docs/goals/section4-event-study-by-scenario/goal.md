# Section 4 Event Study and Pre-Trends with Strict and Broad Controls

## Objective

Create a standalone Section 4 event-study and pre-trends package for the baseline scenario and the OIT exposure scenarios under strict and broad control definitions, without changing the legacy Stage 2b pipeline.

## Original Request

Prepare and update a GoalBuddy goal plan for the attached plan: "Event Study E Pre-Trends Com Controle Estrito E Controle Amplo."

## Intake Summary

- Input shape: `existing_plan`
- Audience: dissertation author and research reviewers
- Authority: `requested`
- Proof type: `test`
- Completion proof: `src/scripts/build_section4_event_study_by_scenario.py` compiles and runs, the expected CSVs, PNGs, sample summary, and Markdown reports exist for all contrasts/outcomes, validation gates pass, and the final audit records `full_outcome_complete: true`.
- Goal oracle: run the script and validate the generated event-study coefficient CSV, pre-trend test CSV, sample summary CSV, contrast figures, outcome comparison figures, contrast reports, general comparison report, and `git diff --check`.
- Likely misfire: producing attractive figures or reports while silently using the wrong treatment/control definitions, omitting outcomes/contrasts, putting `Minimal Exposure` in the wrong comparison, including `No score` or no-MTE CBOs, weakening the `t = -1` reference convention, or modifying the old Stage 2b pipeline.
- Blind spots considered: pyfixest covariance access may differ from expectations; pre-trend joint tests need a transparent fallback; demographic controls must not inherit known upstream recoding errors; narrative recommendations should not outrun identification evidence.
- Existing plan facts: create `src/scripts/build_section4_event_study_by_scenario.py`; read `data/output/painel_2b_ready.parquet` and `outputs/treatment_scenario_grid/scenario_cbo_classification.csv`; estimate four outcomes across seven contrasts: `baseline_mte2d_top20_vs_rest`, `trat_alta_expo_strict_control`, `trat_alta_expo_broad_control`, `trat_media_expo_strict_control`, `trat_media_expo_broad_control`, `trat_expostos_strict_control`, and `trat_expostos_broad_control`; define OIT treatment as Gradient 3-4, Gradient 1-2, or Gradient 1-4 depending on the contrast; define strict controls as `Not Exposed`; define broad controls as `Not Exposed` plus `Minimal Exposure`; exclude `No score`, no-MTE, and invalid classifications; use `t = -1` as reference and bin event time to `[-12, 24]`; keep only treated/control rows; cluster by `cbo_4d`; generate long coefficients, pre-trend tests, sample summary, contrast figures, outcome comparison figures, contrast Markdown reports, and one general Markdown comparison report.

## Goal Oracle

The oracle for this goal is:

`python -m py_compile src/scripts/build_section4_event_study_by_scenario.py && python src/scripts/build_section4_event_study_by_scenario.py && output validation confirms all seven expected contrasts, outcomes, reference-period rows, strict/broad control definitions, exclusion rules, sample summary, pre-trend columns, reports, figures, and diff hygiene.`

The PM must keep comparing task receipts to this oracle. Planning, discovery, a passing tiny slice, or a clean-looking board is not enough. The goal finishes only when a final Judge/PM audit maps receipts and verification back to this oracle and records `full_outcome_complete: true`.

## Goal Kind

`existing_plan`

## Current Tranche

Complete the full standalone event-study package for the Section 4 baseline plus strict/broad OIT treatment contrasts: validate the user-provided plan, implement the script, run it, verify generated artifacts, and audit whether the pre-trend evidence supports the contrast recommendations.

## Non-Negotiable Constraints

- Do not alter the legacy Stage 2b pipeline.
- Preserve and validate the user-provided plan before implementation.
- Use English for code, script internals, and GoalBuddy control files.
- Use Portuguese for dissertation-facing analytical report text unless a stronger existing repo convention says otherwise.
- Treat wrong treatment/control definitions, missing outcomes, missing contrasts, missing expected files, invalid `t = -1` reference handling, inclusion of `No score`, no-MTE, invalid, or otherwise excluded rows, and demographic control anomalies as hard validation gates.
- For OIT contrasts, treatment must be `Exposed: Gradient 3` or `Exposed: Gradient 4` for `trat_alta_expo`, `Exposed: Gradient 1` or `Exposed: Gradient 2` for `trat_media_expo`, and Gradient 1-4 for `trat_expostos`.
- `strict_control` must use only `Not Exposed`; `broad_control` must use `Not Exposed` plus `Minimal Exposure`.
- The general report must compare strict vs broad and treat the strict control as the main causal specification unless the final audit gives a documented reason to change that framing.
- Use the same controls and fixed effects as Section 4 unless the active Judge task approves a documented deviation.
- Do not treat the new event-study outputs as replacing the main dissertation tables; they are diagnostic and narrative-selection artifacts.

## Stop Rule

Stop only when a final audit proves the full original outcome is complete.

Do not stop after planning, discovery, or Judge selection if a safe Worker task can be activated.

Do not stop after a single verified Worker package when the broader owner outcome still has safe local follow-up work. Advance the board to the next highest-leverage safe Worker package and continue unless a phase, risk, rejected-verification, ambiguity, or final-completion review is due.

Do not create one Worker/Judge pair per repeated contrast, outcome, figure, or report. Put repeated same-shape work into one coherent Worker package and review the package as a whole.

## Slice Sizing

Safe means bounded, explicit, verified, and reversible. It does not mean tiny.

A good task is the largest safe useful slice. For this goal, the implementation slice should produce a working script plus the planned event-study outputs, not just helper functions.

## Canonical Board

Machine truth lives at:

`docs/goals/section4-event-study-by-scenario/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/section4-event-study-by-scenario/goal.md.
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
10. Review at phase, risk, rejected-verification, ambiguity, or final-completion boundaries; do not review every small Worker by habit.
11. Finish only with a Judge/PM audit receipt that maps receipts and verification back to the original user outcome and records `full_outcome_complete: true`.
