# Notion primary-audit application log

Status: `APPLIED TO DUPLICATE / PROVISIONAL`

## Target

- Page title: `Dissertação de Mestrado V2 (1)`
- Page ID: `33dcc8ca-4610-82bd-a888-0151f42ba19b`
- Page URL: <https://app.notion.com/p/33dcc8ca461082bda8880151f42ba19b>
- Source of changes: `PRIMARY_AUDIT_REPORT.md` and `notion_change_queue.tsv`
- Application date: 2026-08-08
- Final Notion snapshot timestamp: 2026-08-08T14:40:37.347Z
- Final semantic SHA-256: `8586595c356286821810d789ad99821b1f6f667933b07abe243afeff3f957efa`
- Final normalized character count: 230,884

The original page `325cc8ca-4610-82d7-94db-01323b295bb5` was not edited. Zotero, `references/library.bib`, and the PDF collection were not edited.

## Applied scope

| Queue range | Application status | Notes |
|---|---|---|
| CHG-001 | `DEFERRED_DEEP_AUDIT` | The already changed opening clause was preserved. Its Eloundou citation was linked, but no new substantive judgment was imposed on the changed wording. |
| CHG-002–CHG-045 | `APPLIED_CONSOLIDATED` | Claims were narrowed, split by source, or rewritten from the primary evidence. Grouped citations were separated where their support differed. |
| CHG-046–CHG-050 | `NOTION_APPLIED / SOURCE_SYSTEM_PENDING` | Citation years and reference entries were aligned to the versions audited in the workspace. Zotero, BibTeX, and attachment metadata still require a later synchronization pass. |
| CHG-051–CHG-056 | `NOTION_APPLIED / PDF_ALIGNMENT_PENDING` | Published DOI destinations and conservative methodological statements are now used in Notion. The stored PDFs and Zotero records still require version reconciliation. |
| CHG-057–CHG-060 | `APPLIED` | Author-year punctuation and compound-surname formatting were standardized. |
| CHG-061–CHG-089 | `APPLIED` | Formal citations were linked to DOI records or official landing pages. |
| CHG-090–CHG-093 | `APPLIED` | Benjamini–Hochberg, Callaway–Sant’Anna, Chen–Roth, and de Chaisemartin–D’Haultfœuille were added to the reference list. |
| CHG-094 | `NOT_APPLICABLE` | Goodman-Bacon was removed from the claim and therefore was not added to the final reference list. |
| CHG-095–CHG-111 | `APPLIED` | Remaining methodological references were added; the uncited Aldasoro entry was removed; cited entries were normalized and linked. |

## Main editorial corrections

- Removed unsupported priority or exclusivity qualifiers such as `seminal`, `first`, `only`, and `principal reference` where the cited work did not establish them.
- Rewrote the introductory international-evidence paragraph so that Brynjolfsson, Hosseini Maasoum, and Klein Teeselink support distinct statements.
- Corrected the radiology experiment description and removed unsupported occupational-task examples.
- Clarified the construction and limitations of GPT Exposure, GENOE, the Anthropic Economic Index, and the ILO Global Index.
- Removed Goodman-Bacon from the staggered-adoption claim because the audited file did not support the exact attribution used in the dissertation.
- Separated the Chen–Roth argument about log-like transformations from the Santos Silva–Tenreyro argument about heteroskedasticity and PPML.
- Rewrote the Rambachan–Roth sensitivity description.
- Corrected the Brynjolfsson pre-trend discussion: the conclusion now distinguishes the Anthropic and Eloundou exposure measures.
- Corrected the early-career magnitude from approximately 12 to 15 log points for the comparison stated in the dissertation.
- Aligned in-text years to Bick 2025, Hosseini Maasoum and Lichtinger 2026, and Humlum and Vestergaard 2026.
- Fixed the GENOE DOI to `10.18235/0013125` and the Teutloff DOI to `10.1016/j.jebo.2024.106845`.
- Fixed the prose typo `elas e concentra` to `ela se concentra`.

## Final reference-set check

The Notion reference section contains 22 cited works in alphabetical order:

1. Agarwal et al.
2. Appel et al.
3. Autor, Levy, and Murnane
4. Benítez and Parrado
5. Benjamini and Hochberg
6. Bick, Blandin, and Deming
7. Brasil
8. Brynjolfsson, Chandar, and Chen
9. Callaway and Sant’Anna
10. de Chaisemartin and D’Haultfœuille
11. Chandar
12. Chen and Roth
13. Eloundou et al.
14. Gmyrek et al.
15. Hosseini Maasoum and Lichtinger
16. Humlum and Vestergaard
17. Klein Teeselink
18. Osorio
19. Rambachan and Roth
20. Santos Silva and Tenreyro
21. Sun and Abraham
22. Teutloff et al.

`Aldasoro et al.` was removed because it is not cited. `Goodman-Bacon` was not added because its citation was removed from the corrected claim.

## Remaining work

1. Synchronize the revised source years, titles, dates, and attachment versions in Zotero and `references/library.bib`.
2. Replace or identify the final published PDFs for the methodological sources flagged by CHG-051–CHG-056.
3. Resume blind quality control on the corrected snapshot, not on the superseded text.
4. Re-audit the deferred Eloundou opening clause and any claims changed after the primary snapshot.
5. Run the final FGV/ABNT rendering check after the dissertation is exported to its submission format.

