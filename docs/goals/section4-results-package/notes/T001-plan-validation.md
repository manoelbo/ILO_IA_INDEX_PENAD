# T001: Section 4 Plan Validation

Task: `T001`
Kind: `judge`
Status: `current`

## Summary

Decision: `approved`. The user's plan is implementable in the current worktree, but the implementation must treat the existing Stage 2a monthly cache as stale because it was built with the wrong female sex code. Worker scopes must include the generated Stage 2a, Stage 2b, treatment-grid, and Section 4 output paths needed by the verification loop.

## Evidence

- `src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py` currently computes `is_mulher` with `sexo == '2'` inside `processar_ano`, while raw CAGED contains `sexo = 1` and `sexo = 3`, with only small `sexo = 9` residuals in 2023 and 2024.
- Current `data/processed/painel_caged_mensal.parquet`, `data/output/painel_caged_did_ready.parquet`, and `data/output/painel_2b_ready.parquet` all have `pct_mulher_adm.max() == 0.0`.
- Raw code values observed from `data/raw/caged_2021.parquet` through `data/raw/caged_2025.parquet`:
  - `sexo`: `1`, `3`, and small `9` residuals.
  - `raca_cor`: `1`, `2`, `3`, `4`, `5`, `6`, `9`.
  - `grau_instrucao`: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `80`, `99`.
- `src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py` skips `step_03` when `data/processed/painel_caged_mensal.parquet` exists, so a code-only sex mapping fix would not refresh `pct_mulher_adm`.
- Current panel crosswalk evidence is valid: `data/output/painel_caged_did_ready.parquet` and `data/output/painel_2b_ready.parquet` contain only `crosswalk_spec = mte_official_no_numeric_fallback`.
- The required scenarios exist in `outputs/treatment_scenario_grid/scenario_cbo_classification.csv`:
  - `baseline_mte2d_top20_vs_rest`: 92 treated CBOs, 344 controls.
  - `high_transformation_g34_vs_unexposed`: 45 treated CBOs, 347 controls, 44 excluded.
  - `augmentation_g12_vs_unexposed`: 44 treated CBOs, 347 controls, 45 excluded.
  - `any_exposed_g1234_vs_unexposed`: 89 treated CBOs, 347 controls.
- `outputs/treatment_scenario_grid/stage2_scenario_results.csv` has all four required Stage 2 outcomes for each required scenario, all currently estimated.
- `outputs/treatment_scenario_grid/baseline_validation.csv` currently passes all 13 rows with max coefficient difference about `8.67e-17`.

## Operational Decisions

- Stage 2a must introduce constants for categorical codes, including `CODIGO_SEXO_MULHER = "3"`, and validate raw `sexo`, `raca_cor`, and `grau_instrucao` before recoding.
- Stage 2a must validate `pct_mulher_adm.max() > 0` after aggregation and in final output.
- Stage 2a should detect the stale monthly cache case and rebuild or invalidate it instead of silently proceeding with all-zero `pct_mulher_adm`.
- Sex panels for Table 3 should use `sexo = 1` for men and `sexo = 3` for women; `sexo = 9` should be excluded from sex-specific panels and counted in audit/sample-loss diagnostics.
- Education panels should be built from raw `grau_instrucao` codes with a documented mapping:
  - fundamental or less: `1`, `2`, `3`, `4`, `5`;
  - high school: `6`, `7`;
  - higher education: `8`, `9`, `10`, `11`, `80`;
  - unknown/not classified: `99`, excluded from education panels and recorded in audit diagnostics.
- Income panels should use pre-treatment CBO-level median admission wage divided by the year-specific minimum wage map already present in Stage 2a.
- Race/color should be included in the long audit output when estimable; unknown/nonresponse codes must be retained in diagnostics rather than silently dropped.
- Baseline parity should compare the builder's baseline rows against regenerated `outputs/tables/did_main_results.csv` Model 3 and/or `outputs/treatment_scenario_grid/baseline_validation.csv`.

## Approved Worker Scopes

`T002` may edit Stage 2a and regenerate the Stage 2a derived files needed to make the corrected female share real:

- `src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py`
- `data/processed/painel_caged_mensal.parquet`
- `data/processed/painel_caged_crosswalk.parquet`
- `data/processed/painel_caged_crosswalk.csv`
- `data/processed/painel_caged_tratamento.parquet`
- `data/output/painel_caged_did_ready.parquet`
- `data/output/painel_caged_did_ready.csv`
- `outputs/crosswalk_audit/source_dictionaries/mte_cbo2002_cbo94_ciuo88_by_family.csv`

`T003` may create the Section 4 builder and regenerate the outputs touched by the full oracle loop:

- `src/scripts/build_dissertation_section4_results.py`
- `outputs/dissertation_section4/**`
- `data/output/painel_2b_ready.parquet`
- `outputs/tables/balance_table_pre.csv`
- `outputs/tables/did_main_results.csv`
- `outputs/tables/did_robustez_cbo2d.csv`
- `outputs/tables/event_study_*.csv`
- `outputs/tables/parallel_trends_test.csv`
- `outputs/tables/heterogeneity_triple_did.csv`
- `outputs/tables/robustness_results.csv`
- `outputs/tables/table_did_main.tex`
- `outputs/figures/parallel_trends_all_outcomes.png`
- `outputs/figures/event_study_all_outcomes.png`
- `outputs/treatment_scenario_grid/**`

## Board Receipt Snippet

```yaml
receipt:
  result: done
  decision: approved
  full_outcome_complete: false
  note: notes/T001-plan-validation.md
  summary: "Plan approved with exact Worker scopes; Stage 2a cache is stale because pct_mulher_adm is all zero and must be rebuilt or invalidated after changing female code to 3."
```
