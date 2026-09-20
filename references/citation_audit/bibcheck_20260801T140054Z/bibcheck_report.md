# Incremental Bibcheck Report

## Scope

This run audits the eight methodology/econometrics entries added after the earlier 36-entry bibliography review. It uses per-citation verification against DOI and official journal pages, followed by an independent reviewer pass.

- Source: `references/library.bib`
- Mode: per citation
- Run: `20260801T140054Z`
- Source file changed: **no**
- Verdict: **pass with normalization**

## Results

| Citation key | Final status | Canonical source | Finding |
|---|---|---|---|
| `goodman_bacon_difference_2021` | NORMALIZE | [DOI](https://doi.org/10.1016/j.jeconom.2021.03.014) | Essential metadata is correct. Prefer sentence case. Local PDF is the 2018 NBER precursor. |
| `callaway_difference_2021` | NORMALIZE | [DOI](https://doi.org/10.1016/j.jeconom.2020.12.001) | Essential metadata is correct. Prefer sentence case. Local PDF is the 2020 arXiv precursor. |
| `sun_estimating_2021` | NORMALIZE | [DOI](https://doi.org/10.1016/j.jeconom.2020.09.006) | Essential metadata is correct. Prefer sentence case. Local PDF is the 2020 arXiv precursor. |
| `de_chaisemartin_two-way_2020` | CLEAN | [DOI](https://doi.org/10.1257/aer.20181169) | Essential metadata is correct. Local PDF is the March 2020 arXiv version. |
| `santos_silva_log_2006` | CLEAN | [DOI](https://doi.org/10.1162/rest.88.4.641) | Essential metadata is correct, including the compound family name. Local PDF is the 2005 CEP precursor. |
| `chen_logs_2024` | NORMALIZE | [DOI](https://doi.org/10.1093/qje/qjad054) | Essential metadata is correct. Remove the optional abstract because extracted formulas are corrupted. Local PDF is the 2023 arXiv version. |
| `benjamini_controlling_1995` | CLEAN | [DOI](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) | All audited fields match the canonical article. |
| `rambachan_more_2023` | CLEAN | [DOI](https://doi.org/10.1093/restud/rdad018) | All audited fields match the canonical article. |

Counts: **4 clean, 4 normalize, 0 factual corrections, 0 unverifiable**.

## Reviewer conclusions

- All eight DOIs resolve to the expected publications.
- Titles, authors, publication years, journals, volumes, issues, and page ranges belong to the same works; no mixed-paper metadata was found.
- Title-case differences in three Journal of Econometrics entries are editorial normalizations, not factual errors.
- Six local PDFs are earlier versions of the same research. This is acceptable for reading, but page locators must identify the version actually consulted. Replacing them with the published versions is preferable before the page-level claim audit.
- `corrected.bib` is a review-only candidate. It was not applied to `references/library.bib`.

## Boundary

This audit checks bibliographic identity and metadata. It does not decide whether the dissertation accurately characterizes each paper or whether a cited page supports a specific claim.

