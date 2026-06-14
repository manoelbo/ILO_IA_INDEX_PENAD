# T003 Worker Receipt - Section 4 Results Package

## Result

Done.

## Changed Or Generated Files

- `src/scripts/build_dissertation_section4_results.py`
- `outputs/dissertation_section4/section4_results_report.md`
- `outputs/dissertation_section4/figures/figure1_event_study_aggregate.png`
- `outputs/dissertation_section4/tables/table1_main_effects.md`
- `outputs/dissertation_section4/tables/table1_main_effects.csv`
- `outputs/dissertation_section4/tables/table2_exposure_types.md`
- `outputs/dissertation_section4/tables/table2_exposure_types.csv`
- `outputs/dissertation_section4/tables/table3_heterogeneity_baseline_mte2d_top20_vs_rest.md`
- `outputs/dissertation_section4/tables/table3_heterogeneity_baseline_mte2d_top20_vs_rest.csv`
- `outputs/dissertation_section4/tables/table3_heterogeneity_high_transformation_g34_vs_unexposed.md`
- `outputs/dissertation_section4/tables/table3_heterogeneity_high_transformation_g34_vs_unexposed.csv`
- `outputs/dissertation_section4/tables/table3_heterogeneity_augmentation_g12_vs_unexposed.md`
- `outputs/dissertation_section4/tables/table3_heterogeneity_augmentation_g12_vs_unexposed.csv`
- `outputs/dissertation_section4/tables/table3_heterogeneity_any_exposed_g1234_vs_unexposed.md`
- `outputs/dissertation_section4/tables/table3_heterogeneity_any_exposed_g1234_vs_unexposed.csv`
- `outputs/dissertation_section4/tables/table3_heterogeneity_all_scenarios_long.csv`

## Implementation Notes

- The builder validates `crosswalk_spec == mte_official_no_numeric_fallback`.
- The builder validates that `pct_mulher_adm.max() > 0`.
- The builder validates that the four required exposure scenarios exist.
- The builder validates Stage 2b baseline parity against the regenerated scenario-grid baseline.
- Figure 1, Tables 1 and 2, four Table 3 scenario files, the long audit CSV, and the Portuguese report are generated in one reproducible script.
- Table 3 panels are reconstructed from raw CAGED microdata, not from the existing aggregate proxy panel.
- The long audit CSV includes `race_color` rows and records sample-loss reasons when treated or control CBOs are missing for an outcome/group.

## Verification

- `python src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py`: pass
- `python src/scripts/etapa_2b_analise_did_caged_ilo.py`: pass
- `python src/scripts/run_treatment_scenario_grid.py`: pass
- `python src/scripts/build_dissertation_section4_results.py`: pass
- `python -m py_compile src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py src/scripts/build_dissertation_section4_results.py`: pass
- `git diff --check -- src/scripts outputs/dissertation_section4`: pass
- Extra whitespace check on untracked relevant scripts and Markdown outputs: pass

## Artifact Counts

- Table 1 CSV rows: 4.
- Table 2 CSV rows: 16.
- Long Table 3 audit CSV rows: 304.
- Long Table 3 scenarios: 4.
- Long Table 3 dimensions: age, education, income, race_color, sex.
- Outcomes per scenario in long Table 3: 4.
- Main Table 3 failed estimation rows: 0.
- Long audit failed estimation rows: 4, all limited to `race_color == race_code_9` and `ln_salario_real_adm`; each row records sample-loss reasons.

