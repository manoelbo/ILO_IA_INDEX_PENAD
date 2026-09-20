# Dissertation Text and Render Audit

## Verdict

**HOLD — do not circulate the current PDF.**

The manuscript has a coherent structure, a defensible research question,
and unusually explicit discussion of support, pretrends, multiplicity,
and the distinction between exposure and observed adoption. Many central
numbers match their backing files. The current deliverables nevertheless
contain one critical cross-package inconsistency and several major
substantive or rendering defects that a reader will see immediately.

The chapter structure does not need to change. The required work is
targeted: correct the headline universe, reconcile the appendix with its
computational sources, report or narrow promised robustness claims,
reduce causal overreach, repair broken artifact links, regenerate the
reference list, and rebuild the PDF from the corrected canonical source.

## Scope

The review read the canonical Markdown from start to finish and compared
it with the adjacent HTML export, the 40-page PDF, all local figures,
the V1 reference package, relevant workspace backing tables, the
canonical bibliography, and the prior Referee 2 rounds.

Canonical source:

`Dissertação/Dissertação de Mestrado 33fcc8ca461080cb8412e25e5b5b6ba3.md`

Rendered verification snapshots:

- `Dissertação/Dissertação de Mestrado 33fcc8ca461080cb8412e25e5b5b6ba3.html`;
- `Dissertação/Dissertao_de_Mestrado.pdf`.

## Critical finding

### C-A01 / prior C039 — Manuscript A.6 and package A.6 are different objects

**Severity: critical**

The manuscript's Appendix A.6 contains the intended income groups at
Markdown lines 956–986. V1 files named `table_a_6_income_*` instead
contain education groups. The cause is explicit in:

- `Replication Package/V1/code/sections4_5/publication.py:335`;
- `Replication Package/V1/code/sections4_5/pipeline.py:239`.

The V1 validation marks the wrong artifacts as passing because they are
byte-identical to the wrong reference files.

**Implication:** the current manuscript may contain the right income
values, but the public package cannot produce them under the published
A.6 artifact names. The claim-to-code chain is broken.

## Major findings

### T-A02 — The highlighted 10% statistic uses the wrong population

**Location:** Markdown line 5; PDF page 1.

The executive summary says that approximately 10% of the **formal**
workforce is highly exposed. The tables and line 21 establish:

- 10.1% of the total employed population;
- 14.8% of formal workers;
- 6.7% of informal workers.

This is a headline factual error.

### T-A03 — Appendix A.5 does not deliver the promised education panels

**Locations:** Markdown lines 621 and 929–954.

The body promises education DDD, pretrend diagnostics, net flow, and
alternative net-flow measures. A.5 includes only three main outcomes and
omits `asinh(net flow)` and all B.2 rows. The complete backing table
exists in:

`outputs/section4_5_final/tables/table_5_2_6_heterogeneity_education.md`.

This is a consequential convenient omission because education contains
one of the manuscript's most emphasized heterogeneity results.

### T-A04 — Robustness is promised but not reported

**Locations:** Markdown lines 362, 399, and 407–412.

The method states that the dissertation uses or evaluates:

- a broader control group including `Minimal Exposure`;
- models without contemporaneous controls;
- predetermined controls;
- Poisson count models.

The manuscript does not show results or a compact disposition table for
these specifications. Backing files outside the dissertation do not make
the claim auditable to a reader.

### T-A05 — The PDF removes support diagnostics and prints markup

**Location:** PDF pages 31–37.

- A.2–A.6 lose the final `treated/control CBOs` column;
- literal `<br>` appears in several appendix tables;
- `&lt;0,001` appears literally;
- A.6 lacks a clear B.1 label, ends with an English note, and omits the
  operational definition of pre-treatment occupational income.

These are not cosmetic defects: the clipped column contains the support
diagnostic used to qualify heterogeneity results.

### Prior C031 — All six Appendix B backing links are broken

**Location:** Markdown line 990.

The six Notion-style artifact links returned HTTP 404 during the audit.
Corresponding local artifacts exist under `outputs/`. The final
manuscript must link to stable bundled artifacts or include them
directly.

### T-A07 — Some causal and adoption language exceeds the design

Examples occur at Markdown lines 23, 66, 137–155, 231, 297, 377–395,
and 420.

Problematic moves include:

- simultaneous lower admissions and separations described as “not job
  destruction” even though employment stock is unobserved;
- high exposure described as an ongoing transformation;
- subgroup effects said to “appear first”;
- the DiD coefficient described as the effect attributable only to the
  post-ChatGPT differential;
- descriptive occupation cases described as mechanisms.

The design observes potential occupational exposure, formal labor-market
flows, and an event date. It does not observe firm adoption, worker use,
employment stock, or isolated mechanisms. Failed national flow
pretrends further limit causal interpretation.

### T-A08 — The CBO universe is internally contradictory

**Locations:** Markdown lines 331–373.

The text alternates among:

- 629 CBOs in the classification universe;
- 436 CBOs matched in the analytical panel;
- 193 CBOs without score and excluded;
- 23,319 cells for the classified panel.

Line 364 calls all 629 CBOs “present in the panel,” and the next table
mixes a 629-CBO denominator with cells from the 436-CBO analytical
panel. `No score` then appears to have zero panel observations.

The text must distinguish classification universe, matched CBOs,
strict estimation sample, and observed CBO-month cells.

### T-A09 — The manual reference list is incomplete

The manuscript lists only 15 of the 36 canonical entries and includes
two internal Notion pages after the references. Twenty-one cited
canonical records are absent. Bick is still listed as the 2024 working
paper rather than the current publication.

See `evidence/bibliography/bibcheck_report.md`.

## Moderate findings

### T-A10 — “Many zeros” is not supported in the strict sample

Line 412 motivates `log(y+1)` with many zero counts. In the frozen strict
sample:

- 31 of 18,307 admissions cells are zero (0.169%);
- 17 of 18,307 separation cells are zero (0.093%).

The estimator may still be used as a secondary specification, but this
particular rationale is weak.

### T-A11 — Numerical and cross-reference errors

- Line 277: `0.304 − 0.252 = 0.052`, approximately 20.6%, not 0.056 and
  22%; the displayed age category is `55+`, not `55–59`.
- Line 313 emphasizes Professional Services and Public Administration as
  volume leaders, but Table 3.4 shows Commerce first at 1.36 million.
- Line 185 refers to nonexistent “Anexo 1.1”.
- Line 589 refers to nonexistent Section 3.7; the intended destination
  is Section 3.5.3.

### T-A12 — Visible export debris and duplicate content

- Figure 3.2 is embedded once as a data URI and again as a local PNG,
  producing two full figures on PDF pages 7–8.
- Sixteen `file ref` or `ref file` markers appear in the manuscript and
  PDF.
- Two internal Notion rewrite pages appear after the bibliography.
- The Markdown, HTML, and PDF have different modification times and are
  not a synchronized release set.

## Blindspot audit by result family

### National results

All three main point estimates are negative, but admissions and
separations fail pretrend diagnostics. The wage pretrend is cleaner, but
the post coefficient is imprecise. Adoption and employment stock are
unobserved. The manuscript already recognizes much of this around lines
440–456; that cautious framing should control the abstract and
conclusion too.

### Sex

The female-admissions DDD is the cleanest demographic contrast. The
summary says net-flow evidence is not robust, but Appendix A.2 contains
two significant normalized net-flow contrasts with passing DDD
pretrends. They remain secondary and are not employment-stock outcomes,
but an absolute statement that no net-flow contrast is robust is too
strong.

### Race/color

The clearest contrast is in separations. It does not establish a stock
effect or causal turnover mechanism. Appendix A.3 also lacks a complete
table hierarchy and B.2 presentation.

### Age

The pattern is not monotonic and does not reproduce a clear 18–24 or
22–25 concentration. Age is not tenure and does not measure firm-
specific tacit knowledge. The results section appropriately reports much
of this discrepancy; the conceptual motivation should be equally
cautious.

### Education

Higher-education separations are more defensible than admissions because
the admission dynamics are less compatible with parallel trends. The
incomplete A.5 suppresses the full diagnostic context and is therefore
the most important within-manuscript appendix omission.

### Income

The middle-income separation DDD has the clearest pattern but only
28 treated and 32 control CBOs. The highest-income group has only 3/7
CBOs and is correctly treated as thin. The manuscript's income table is
more defensible than the package artifact, which is semantically wrong.

### Occupation cases

Checked hardcoded claims match their matrices, including the 33/36 sign
summary and the 31.3 percentage-point racial median. Frozen semantic
selection is a strength. These are normalized trajectories without a
dedicated control group; they illustrate patterns and cannot identify
mechanisms.

## Confirmed strengths

- The manuscript does not need structural redesign.
- The DDD formula is correctly described as
  `post × treatment × subgroup`.
- Heterogeneity pretrends are distinguished from the national joint
  event-study test.
- Support and multiplicity limitations are explicitly disclosed.
- Every locally referenced PNG exists.
- Central national numbers and checked occupation-case claims match
  backing data.
- Several result paragraphs already distinguish flows from employment
  stock and exposure from adoption; those passages provide the model for
  revising the remaining overstatements.

## Audit conclusion

The paper's main contribution can survive the audit, but the present PDF
cannot. Correcting the text does not require new chapters or a new
research question. It requires a synchronized release in which the
headline universe, appendix tables, robustness claims, bibliography,
artifact links, and causal language are all consistent with the
computational evidence.
