# CBO/ISCO-OIT Treatment Scenario Grid

## Objective

Build and run a single empirical scenario grid that compares the current CAGED treatment definition against alternative treatment/control rules based on the ILO score and ILO exposure gradients, then recommend the best specification hierarchy for the dissertation.

## Original Request

The user asked to prepare a GoalBuddy goal to test several treatment scenarios, compare them with the two alternatives already implemented, interpret the current dissertation narrative, and conclude which path is most interesting for the dissertation.

## Intake Summary

- Input shape: `existing_plan`
- Audience: dissertation author and future dissertation readers
- Authority: `requested`
- Proof type: `artifact + metric + review + decision`
- Completion proof: a verified run produces the full `outputs/treatment_scenario_grid/` artifact set, every scenario is classified as estimated or explicitly failed, and the final recommendation ranks the main, robustness, exploratory, and discarded specifications.
- Goal oracle: the scenario grid must prove, with files and model outputs, whether each candidate treatment rule is empirically viable and narratively useful relative to the current MTE/OIT baseline.
- Likely misfire: producing another plan or descriptive report without actually estimating the stage 2 and stage 3 models for every scenario.
- Blind spots considered: gradient rules can be ambiguous under many-to-many CBO-to-ISCO mappings; strict consensus rules may be conceptually clean but underpowered; significance alone must not drive the recommendation; stale dissertation numbers must not be treated as current evidence.
- Existing plan facts: preserve the user-provided scenario list, the MTE bridge, the no-overwrite constraint for main outputs, the dissertation-folder narrative read, the required output filenames, and the stop rule that every scenario must have a result status.

## Goal Oracle

The oracle for this goal is:

`/opt/homebrew/opt/python@3.11/libexec/bin/python src/scripts/run_treatment_scenario_grid.py` completes, writes the required scenario-grid outputs, and `outputs/treatment_scenario_grid/dissertation_recommendation.md` contains a defensible ranked recommendation based on methodology, ILO adherence, sample size, empirical stability, and dissertation narrative fit.

The PM must keep comparing task receipts to this oracle. Planning, discovery, a passing small helper, or a clean-looking board is not enough. The goal finishes only when a final Judge or PM audit maps receipts and verification back to this oracle and records `full_outcome_complete: true`.

## Goal Kind

`existing_plan`

## Current Tranche

This tranche is the full execution tranche: validate the existing plan, implement the unified scenario-grid script, run the scenario classification and model estimates, produce the comparison reports, interpret the dissertation narrative using current outputs, and complete a final audit.

The run should continue through safe local work packages until the full owner outcome is complete. It should not stop after plan validation, script scaffolding, or the first successful model run if required scenarios or reports remain unfinished.

## Scenario Matrix To Preserve

The `/goal` run must implement or explicitly justify any change to these scenario IDs:

- `baseline_mte2d_top20_vs_rest`
- `baseline_isco4d_all_top20_vs_rest`
- `mte2d_top30_vs_rest`
- `isco4d_all_top30_vs_rest`
- `isco4d_all_g34_vs_rest`
- `isco4d_any_g34_vs_rest`
- `isco4d_all_g1234_vs_rest`
- `isco4d_any_g1234_vs_rest`
- `high_transformation_g34_vs_unexposed`
- `augmentation_g12_vs_unexposed`
- `any_exposed_g1234_vs_unexposed`

The conceptual labels are:

- `Gradient 1-2`: complementarity or augmentation.
- `Gradient 3-4`: high transformation or stronger automation exposure.
- `Not Exposed` and `Minimal Exposure`: non-exposed or minimally exposed control group.

## Required Outputs

The implementation must write the scenario-grid outputs under `outputs/treatment_scenario_grid/`:

- `scenario_cbo_classification.csv`
- `scenario_sample_summary.csv`
- `stage2_scenario_results.csv`
- `stage3_scenario_results.csv`
- `scenario_comparison_report.md`
- `dissertation_recommendation.md`

Reports in Markdown should be in Portuguese because they will feed the dissertation discussion. The script and technical column names should remain in English.

## Known Initial Feasibility Evidence

An earlier quick feasibility pass over the current matched CBO universe suggested:

- `g34_all`: 9 CBOs and about 0.39% of admissions.
- `g34_any`: 45 CBOs and about 20.55% of admissions.
- `g1234_all`: 56 CBOs and about 20.89% of admissions.
- `g1234_any`: 89 CBOs and about 42.41% of admissions.
- `g12_all`: 19 CBOs and about 2.26% of admissions.
- `g12_any`: 79 CBOs and about 42.01% of admissions.
- `none_g1234`: 347 CBOs and about 57.59% of admissions.

Treat these as non-binding orientation. The `/goal` run must recompute all counts from current files before relying on them.

## Non-Negotiable Constraints

- Do not overwrite the current main empirical outputs in `outputs/tables`.
- Do not alter notebooks or the dissertation HTML files.
- Use the current MTE/OIT bridge and current CAGED panels as the source of exposure mapping.
- Validate that panels use `crosswalk_spec = "mte_official_no_numeric_fallback"` before estimating.
- Ignore empirical numbers in the dissertation HTML because the user said they are stale.
- Use the dissertation folder only to understand the narrative:
  `/Users/manebrasil/Library/Mobile Documents/com~apple~CloudDocs/Documents/Projects/Dissetação Mestrado/Minha Dissertação Até Agora/`
- Do not choose the recommended specification based on statistical significance alone.
- Every scenario must end with one explicit status: `estimated`, `underpowered_but_estimated`, `failed_collinearity`, or `failed_empty_sample`.

## Verification Commands

At minimum, the goal should run:

```bash
/opt/homebrew/opt/python@3.11/libexec/bin/python -m py_compile src/scripts/run_treatment_scenario_grid.py
/opt/homebrew/opt/python@3.11/libexec/bin/python src/scripts/run_treatment_scenario_grid.py
git diff --check -- src/scripts/run_treatment_scenario_grid.py
```

The script should also verify that the re-estimated current baseline is consistent with current saved results within a documented tolerance, or clearly explain why an exact comparison cannot be made from current outputs.

## Stop Rule

Stop only when a final audit proves the full original outcome is complete:

- the unified script exists and passes `py_compile`;
- the script has run successfully;
- the required output files exist;
- every scenario has classification counts, sample shares, and result status;
- stage 2 and stage 3 results are present or failure reasons are recorded;
- the final recommendation ranks scenarios into main, robustness, exploratory, and discard/report-as-underpowered buckets;
- a final Judge or PM receipt records `full_outcome_complete: true`.

Do not stop after planning, discovery, or Judge selection if a safe Worker task can be activated. Do not stop after a single verified Worker package when scenario estimation, reports, or final audit still remain.

## Slice Sizing

Use the largest safe useful slices:

- one read-only validation task for the plan and current files;
- one coherent Worker package for the script and artifact generation if the scope remains as expected;
- one interpretive/reporting package only if the first Worker cannot finish both estimation and narrative reporting safely;
- one final audit task.

Avoid a one-scenario-at-a-time task loop unless a specific model failure forces isolation.

## Canonical Board

Machine truth lives at:

`docs/goals/treatment-scenario-grid/state.yaml`

If this charter and `state.yaml` disagree, `state.yaml` wins for task status, active task, receipts, verification freshness, and completion truth.

## Run Command

```text
/goal Follow docs/goals/treatment-scenario-grid/goal.md.
```

## PM Loop

On every `/goal` continuation:

1. Read this charter.
2. Read `state.yaml`.
3. Run the bundled GoalBuddy update checker when available and mention a newer version without blocking.
4. Work only on the active board task.
5. Preserve the user's scenario list, constraints, and stop rule.
6. Write a compact task receipt.
7. Update the board.
8. Continue to the next safe local work package until the oracle is satisfied.
9. Finish only with a Judge or PM audit receipt that maps receipts and verification back to the original user outcome and records `full_outcome_complete: true`.
