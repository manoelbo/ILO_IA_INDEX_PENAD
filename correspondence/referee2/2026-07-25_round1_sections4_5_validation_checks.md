# Audit validation checks

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
