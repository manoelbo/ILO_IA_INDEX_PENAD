# Bibliography Audit

## Verdict

The canonical file `references/library.bib` contains 36 entries:

- 32 are factually correct;
- 4 require an update to the current canonical publication;
- 0 are unverifiable;
- 7 of the 32 correct records need optional schema or completeness
  normalization.

Under the strict rule that every normalization counts as a correction,
the result is **25 clean / 11 corrected / 0 unverifiable**.

No mixed-paper metadata was found in the canonical bibliography. The
competing root bibliography does contain mixed and false records and
must not be used to generate the dissertation references.

The review-only file `corrected_library.bib` preserves all 36 citation
keys and applies the four canonical publication updates and the seven
normalizations. It does not overwrite the author's source file.

## Per-entry verification

Legend:

- `OK`: requested identity and publication fields verified;
- `NORMALIZE`: factually correct, but schema/completeness should be
  normalized;
- `UPDATE`: replace the older working-paper metadata with the current
  canonical publication.

| Key | Status | Canonical verification |
| --- | --- | --- |
| `gmyrek_generative_2025` | NORMALIZE | [ILO/DOI](https://doi.org/10.54394/HETP0387): title, eight authors, date, Working Paper 140, and 72 pages verified |
| `brynjolfsson_canaries_2025` | OK | [Stanford Digital Economy Lab](https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/): authors and 13 November 2025 version verified |
| `autor_skill_2003` | OK | [QJE](https://doi.org/10.1162/003355303322552801): 118(4), 1279–1333, November 2003 |
| `acemoglu_race_2018` | OK | [AER](https://doi.org/10.1257/aer.20160696): 108(6), 1488–1542 |
| `felten_occupational_2021` | OK | [Strategic Management Journal](https://doi.org/10.1002/smj.3286): 42(12), 2195–2217 |
| `eloundou_gpts_2023` | OK | [arXiv](https://arxiv.org/abs/2303.10130): the record and local attachment are the long preprint; a later condensed [Science version](https://doi.org/10.1126/science.adj0998) also exists |
| `brynjolfsson_generative_2024` | UPDATE | Replace arXiv with [QJE](https://doi.org/10.1093/qje/qjae044), 140(2), 889–942, 2025 |
| `dellacqua_navigating_2023` | UPDATE | Replace SSRN with [Organization Science](https://doi.org/10.1287/orsc.2025.21838), 37(2), 403–423, 2026 |
| `autor_applying_2024` | OK | [NBER 32140](https://doi.org/10.3386/w32140), February 2024 |
| `bick_rapid_2024` | UPDATE | Replace Federal Reserve working paper with [Management Science](https://doi.org/10.1287/mnsc.2025.02523), Articles in Advance, 20 January 2026 |
| `goos_lousy_2007` | OK | [Review of Economics and Statistics](https://doi.org/10.1162/rest.89.1.118): 89(1), 118–133 |
| `benitez_mirror_2024` | NORMALIZE | [IDB](https://doi.org/10.18235/0013125): title, date, DOI verified; add `IDB-WP-1624` |
| `acemoglu_robots_2020` | OK | [Journal of Political Economy](https://doi.org/10.1086/705716): 128(6), 2188–2244 |
| `acemoglu_skills_2011` | OK | [Handbook of Labor Economics](https://doi.org/10.1016/S0169-7218(11)02410-5): volume 4B, 1043–1171 |
| `acemoglu_automation_2019` | OK | [Journal of Economic Perspectives](https://doi.org/10.1257/jep.33.2.3): 33(2), 3–30 |
| `acemoglu_culture_2025` | OK | [Journal of Economic Literature](https://doi.org/10.1257/jel.20241680): 63(2), 637–692 |
| `acemoglu_learning_2024` | OK | [Annual Review of Economics](https://doi.org/10.1146/annurev-economics-091823-025129): 16(1), 597–621 |
| `autor_does_2007` | OK | [Economic Journal](https://doi.org/10.1111/j.1468-0297.2007.02055.x): 117(521), F189–F217 |
| `autor_places_2025` | OK | [Handbook of Labor Economics](https://doi.org/10.1016/bs.heslab.2025.07.004): volume 6, chapter 7, 549–653 |
| `autor_putting_2013` | NORMALIZE | [Journal of Labor Economics](https://doi.org/10.1086/669332): 31(S1), S59–S96; use `number`, not `issue` |
| `autor_skills_2014` | OK | [Science](https://doi.org/10.1126/science.1251868): 344(6186), 843–851 |
| `autor_polarization_2006` | OK | [AER](https://doi.org/10.1257/000282806777212620): 96(2), 189–194 |
| `autor_work_2019` | OK | [AEA Papers and Proceedings](https://doi.org/10.1257/pandp.20191110): 109, 1–32 |
| `adamczyk_skills_2024` | OK | [International Labour Review](https://doi.org/10.1111/ilr.12412): 163(2), 199–224 |
| `humlum_still_2025` | OK | [NBER 33777](https://doi.org/10.3386/w33777): May 2025; revised March 2026 |
| `aldasoro_ai_2026` | NORMALIZE | [EIB](https://doi.org/10.2867/1772538): Working Paper 2026/02, 13 January 2026, 40 pages |
| `teutloff_winners_2025` | OK | [Journal of Economic Behavior & Organization](https://doi.org/10.1016/j.jebo.2024.106845): volume 235, article 106845 |
| `hui_short-term_2024` | OK | [Organization Science](https://doi.org/10.1287/orsc.2023.18441): 35(6), 1977–1989 |
| `klein_teeselink_generative_2025` | NORMALIZE | [SSRN](https://doi.org/10.2139/ssrn.5516798): author, written date, and 46 pages verified |
| `hosseini_maasoum_generative_2025` | NORMALIZE | [SSRN](https://doi.org/10.2139/ssrn.5425555): authors, written date, and 109 pages verified |
| `stanford_institute_for_human-centered_artificial_intelligence_ai_2026` | UPDATE | Replace institutional placeholder with the official [AI Index](https://hai.stanford.edu/ai-index/2026-ai-index-report) metadata and [arXiv DOI](https://doi.org/10.48550/arXiv.2606.15708) |
| `appel_anthropic_2026` | OK | [Anthropic](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report): title, seven authors, and 15 January 2026 verified |
| `agarwal_combining_2023` | OK | [NBER 31422](https://doi.org/10.3386/w31422): July 2023; current revision November 2025 |
| `osorio_o_2003` | OK | [IPEA TD 996](https://repositorio.ipea.gov.br/bitstreams/e09cc868-669f-4064-b396-693e22e0ce07/download): title, author, Brasília, November 2003 |
| `chandar_tracking_2025` | NORMALIZE | [SSRN](https://doi.org/10.2139/ssrn.5384519): 3 June 2025, 23 pages |
| `brasil_decreto_12342_2024` | OK | [Planalto](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12342.htm): number, date, text, and URL verified |

## Required canonical updates

The review copy changes:

1. `brynjolfsson_generative_2024` from arXiv to the 2025 QJE
   publication;
2. `dellacqua_navigating_2023` from SSRN to the 2026 Organization
   Science publication;
3. `bick_rapid_2024` from the 2024 working paper to the 2026 Management
   Science publication;
4. the 2026 Stanford AI Index from an institutional placeholder to the
   full official author list, title, date, DOI, and pagination.

The three article keys deliberately retain their old key names to avoid
breaking existing citations. Their local `file` fields still point to
older attachments; those PDFs must be replaced or explicitly labelled
as preprints in the reference manager.

## Normalizations applied in the review copy

- `gmyrek_generative_2025`: `pagetotal`, PDF ISBN;
- `benitez_mirror_2024`: working-paper number and type;
- `autor_putting_2013`: `number = {S1}`;
- `aldasoro_ai_2026`: exact date and `pagetotal`;
- `klein_teeselink_generative_2025`: `pagetotal`;
- `hosseini_maasoum_generative_2025`: `pagetotal`;
- `chandar_tracking_2025`: `pagetotal`.

The stale 13% abstract in `brynjolfsson_canaries_2025` was removed from
the review copy because the current page reports the revised 16% result.
The citation itself remains verified.

## Attachment audit

Of 35 local attachments:

- 31 are papers or reports;
- four are only EBSCO bibliographic exports, not the cited documents:
  `acemoglu_culture_2025.pdf`, `acemoglu_learning_2024.pdf`,
  `autor_places_2025.pdf`, and `autor_skills_2014.pdf`;
- the decree has no local attachment, which does not prevent official
  verification.

## Competing bibliography

`Citações Dissertação Mestrado.bib` must not be used for generation:

- 35 records instead of 36;
- 15 `nodate` keys;
- semantic omissions of the Chandar paper and the minimum-wage decree;
- two duplicate false records,
  `azagirre_authors_nodate` and `azagirre_authors_nodate-1`, whose title
  is an Anthropic author line and whose authors come from
  acknowledgements;
- multiple generic titles and incomplete authorship fields.

## Manuscript reference-list coverage

The manual reference list in the canonical manuscript contains only 15
of the 36 canonical entries. It omits 21 keys:

```text
acemoglu_automation_2019
acemoglu_culture_2025
acemoglu_learning_2024
acemoglu_race_2018
acemoglu_robots_2020
acemoglu_skills_2011
adamczyk_skills_2024
autor_applying_2024
autor_does_2007
autor_places_2025
autor_polarization_2006
autor_putting_2013
autor_skills_2014
autor_work_2019
brynjolfsson_generative_2024
dellacqua_navigating_2023
felten_occupational_2021
goos_lousy_2007
hui_short-term_2024
stanford_institute_for_human-centered_artificial_intelligence_ai_2026
teutloff_winners_2025
```

The final list should be generated from the corrected canonical
bibliography rather than maintained manually.

## Boundary of this audit

This report verifies bibliographic identity and metadata. Whether every
citation supports the exact sentence, mechanism, estimand, or
interpretation is assessed separately in the text audit.
