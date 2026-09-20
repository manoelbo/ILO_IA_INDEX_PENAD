# Round 2 validation checks

| kind       | check_id                          | status   | observed                                                          | expected    | detail                                                            |
|:-----------|:----------------------------------|:---------|:------------------------------------------------------------------|:------------|:------------------------------------------------------------------|
| audit      | html_table_count                  | pass     | 23                                                                | 23          | Revised editorial table inventory.                                |
| audit      | html_figure_count                 | pass     | 16                                                                | 16          | Thirteen main figures plus three Appendix B figures.              |
| audit      | tables_t01_t21_match              | pass     | 21                                                                | 21          | Approved editorial corrections are normalized before comparison.  |
| audit      | a6_correct_rows_present           | pass     | 2                                                                 | 2           | All correct income rows exist despite the broken layout.          |
| acceptance | a6_structure_ready                | fail     | content_present_structure_broken,content_present_structure_broken | pass,pass   | Headers and row order must match the replacement table.           |
| audit      | all_figure_pixels_valid           | pass     | 16                                                                | 16          | References, sources, dimensions and visual pixels were compared.  |
| audit      | appendix_b_figures_exact_pixels   | pass     | 0.000000,0.000000,0.000000                                        | 0,0,0       | The three new figures are pixel-identical to specialized outputs. |
| audit      | round1_resolution_inventory       | pass     | 44                                                                | 44          | Every Round 1 correction has a Round 2 disposition.               |
| acceptance | round1_critical_items_fully_fixed | fail     | fixed,partially_fixed                                             | fixed,fixed | The method paragraph is fixed; A.6 remains only partially fixed.  |
| acceptance | appendix_b_links_reachable        | fail     | 0                                                                 | 6           | Every linked appendix table must work outside Notion.             |
| audit      | appendix_b_broken_links_detected  | pass     | 6                                                                 | 6           | The audit must not silently accept rewritten Notion URLs.         |
| audit      | cross_language_replication        | pass     | 5.385e-12                                                         | <=1e-8      | Python, R and frozen author outputs remain aligned.               |
| audit      | replication_package_unchanged     | pass     | True                                                              | True        | Round 2 did not modify the Replication Package.                   |
| audit      | phase1_validation_still_green     | pass     | 121                                                               | 121         | The frozen package validation remains green.                      |
| acceptance | no_substantive_round2_findings    | fail     | 4                                                                 | 0           | Major and moderate findings block acceptance.                     |
