#!/usr/bin/env python3
"""Consolidate prior Referee 2 findings with the final-review findings."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


FIELDNAMES = [
    "finding_id",
    "source",
    "domain",
    "severity",
    "status",
    "title",
    "location",
    "evidence",
    "recommendation",
    "related_to",
]


CURRENT_FINDINGS = [
    {
        "finding_id": "C-A01",
        "source": "Codex final code audit",
        "domain": "code",
        "severity": "major",
        "status": "open",
        "title": "Package A.6 uses education data under income names",
        "location": "V1 publication.py:335; pipeline.py:239",
        "evidence": "Both A.6 outputs contain education groups and pass only by byte identity to the wrong reference.",
        "recommendation": "Use the income source and assert allowed labels and source identity.",
        "related_to": "C039",
    },
    {
        "finding_id": "C-A02",
        "source": "Codex final code audit",
        "domain": "code",
        "severity": "major",
        "status": "open",
        "title": "Most inferential outputs are not re-estimated in reproduce mode",
        "location": "V1 pipeline.py:66; analysis.py:65",
        "evidence": "Only four national models are replayed; event studies, DDD, Poisson, heterogeneity and occupation cases remain frozen.",
        "recommendation": "Re-estimate every inferential artifact in V2 and label copied artifacts explicitly.",
        "related_to": "",
    },
    {
        "finding_id": "C-A03",
        "source": "Codex final code audit",
        "domain": "econometrics",
        "severity": "major",
        "status": "open",
        "title": "Preferred models use potentially post-treatment composition controls",
        "location": "V1 section4_event_study/config.py:33",
        "evidence": "Monthly age and demographic shares among admissions can respond to treatment.",
        "recommendation": "Use no contemporaneous composition controls in the main model; predetermined controls only as robustness.",
        "related_to": "",
    },
    {
        "finding_id": "C-A04",
        "source": "Codex final code audit",
        "domain": "data construction",
        "severity": "major",
        "status": "open",
        "title": "Zero-flow cells receive artificial wage and composition values",
        "location": "V1 etapa_2a...py:783; etapa_2b...py:194",
        "evidence": "62 zero-admission cells share a positive P1 wage; 31 enter the main sample; extreme separation wages survive.",
        "recommendation": "Make wage and composition missing when the corresponding flow is zero and validate domains before aggregation.",
        "related_to": "",
    },
    {
        "finding_id": "C-A05",
        "source": "Codex final code audit",
        "domain": "provenance",
        "severity": "major",
        "status": "open",
        "title": "Full mode is a hybrid rebuild",
        "location": "V1 full_pipeline.py:269",
        "evidence": "The DAG injects frozen exposure, IPCA, dynamic pairs and metadata without complete public raw lineage.",
        "recommendation": "Publish complete source and stage manifests for one immutable vintage.",
        "related_to": "",
    },
    {
        "finding_id": "C-A06",
        "source": "Codex final code audit",
        "domain": "econometrics",
        "severity": "major",
        "status": "open",
        "title": "National flow models fail pretrend diagnostics",
        "location": "V1 table_a_1_national_main_diagnostics.csv",
        "evidence": "Admissions, separations and net flow are classified as failed pretrends.",
        "recommendation": "Restrict causal language and run exact-model diagnostics and sensitivity in V2.",
        "related_to": "",
    },
    {
        "finding_id": "C-A07",
        "source": "Codex final code audit",
        "domain": "econometrics",
        "severity": "moderate",
        "status": "open",
        "title": "Endpoint clipping pools heterogeneous event months",
        "location": "V1 section4_event_study/estimation.py:175",
        "evidence": "The -12 and +24 coefficients pool multiple endpoint months while strict figures use another estimand.",
        "recommendation": "Use the balanced -23 to +23 window with no clipping.",
        "related_to": "C041",
    },
    {
        "finding_id": "C-A08",
        "source": "Codex final code audit",
        "domain": "provenance",
        "severity": "moderate",
        "status": "open",
        "title": "Mutable crosswalk sources lack content hashes",
        "location": "V1 caged_mte_crosswalk.py:220",
        "evidence": "Counts are checked but source content and vintage are not cryptographically anchored.",
        "recommendation": "Freeze URL, retrieval time, bytes, schema and SHA-256 for every source.",
        "related_to": "",
    },
    {
        "finding_id": "C-A09",
        "source": "Codex final code audit",
        "domain": "data construction",
        "severity": "moderate",
        "status": "open",
        "title": "Merge and missingness contracts are incomplete",
        "location": "V1 panel.py:49",
        "evidence": "The panel is unique but unbalanced at 8 to 54 months per CBO; row deltas and unmatched keys are not systematically gated.",
        "recommendation": "Add uniqueness, match, row-delta, missingness and balanced-support gates.",
        "related_to": "",
    },
    {
        "finding_id": "C-A10",
        "source": "Codex final code audit",
        "domain": "data construction",
        "severity": "moderate",
        "status": "open",
        "title": "Demographic recodes diverge across modules",
        "location": "V1 preparation constants and heterogeneity.py:236",
        "evidence": "Higher-education code sets differ; unknown sex is treated as non-female; 60+ has no upper bound.",
        "recommendation": "Freeze one validated codebook and explicit missing denominators.",
        "related_to": "",
    },
    {
        "finding_id": "C-A11",
        "source": "Codex final code audit",
        "domain": "section 3",
        "severity": "moderate",
        "status": "open",
        "title": "Section 3 accepts partially malformed inputs",
        "location": "V1 section3/build_data.py:111 and 217",
        "evidence": "Missing periods, nonpositive weights and demographic domains are not all fail-fast.",
        "recommendation": "Validate complete 2025Q3 periods, finite positive weights and code domains.",
        "related_to": "",
    },
    {
        "finding_id": "C-A12",
        "source": "Codex final code audit",
        "domain": "artifact validation",
        "severity": "moderate",
        "status": "open",
        "title": "Reference directory is not independently anchored",
        "location": "V1 common/artifacts.py:30",
        "evidence": "Current references are compared without first validating them against the reference manifest.",
        "recommendation": "Verify reference hashes first and compare all backing data semantically.",
        "related_to": "",
    },
    {
        "finding_id": "T-A02",
        "source": "Codex final text audit",
        "domain": "text",
        "severity": "major",
        "status": "open",
        "title": "Headline 10 percent statistic uses the wrong universe",
        "location": "Canonical Markdown:5",
        "evidence": "10.1% refers to all employed workers; formal workers are 14.8%.",
        "recommendation": "Correct the summary and regenerate the PDF.",
        "related_to": "",
    },
    {
        "finding_id": "T-A03",
        "source": "Codex final text audit",
        "domain": "text",
        "severity": "major",
        "status": "open",
        "title": "Appendix A.5 omits promised education outcomes",
        "location": "Canonical Markdown:621 and 929-954",
        "evidence": "The appendix omits asinh net flow and the complete B.2 robustness panel.",
        "recommendation": "Insert the complete existing education backing table.",
        "related_to": "",
    },
    {
        "finding_id": "T-A04",
        "source": "Codex final text audit",
        "domain": "text",
        "severity": "major",
        "status": "open",
        "title": "Promised robustness results are not reported",
        "location": "Canonical Markdown:362, 399, 407-412",
        "evidence": "Broader control, no-control, predetermined-control and Poisson specifications are promised but absent.",
        "recommendation": "Report a compact disposition table or narrow the claims.",
        "related_to": "",
    },
    {
        "finding_id": "T-A05",
        "source": "Codex final text audit",
        "domain": "rendering",
        "severity": "major",
        "status": "open",
        "title": "PDF clips support diagnostics and prints markup",
        "location": "PDF pages 31-37",
        "evidence": "A.2-A.6 lose the treated/control CBO column and display literal br and escaped p-value markup.",
        "recommendation": "Use renderer-safe cells, fit all columns and inspect the regenerated PDF.",
        "related_to": "C038",
    },
    {
        "finding_id": "T-A07",
        "source": "Codex final text audit",
        "domain": "interpretation",
        "severity": "major",
        "status": "open",
        "title": "Residual causal and adoption language exceeds the design",
        "location": "Canonical Markdown:66, 137-155, 231, 297, 377-395, 420",
        "evidence": "Exposure is sometimes described as realized transformation, effects are said to appear first, and descriptive cases are called mechanisms.",
        "recommendation": "Use differential-change and descriptive-trajectory language; adoption and employment stock are unobserved.",
        "related_to": "C010;C020;C030",
    },
    {
        "finding_id": "T-A08",
        "source": "Codex final text audit",
        "domain": "text",
        "severity": "major",
        "status": "open",
        "title": "Panel universe is internally contradictory",
        "location": "Canonical Markdown:331-373",
        "evidence": "The text mixes 629 classification CBOs, 436 matched CBOs and 23,319 classified cells.",
        "recommendation": "Define classification universe, matched panel and strict estimation sample separately.",
        "related_to": "",
    },
    {
        "finding_id": "T-A09",
        "source": "Codex final text and bibliography audit",
        "domain": "bibliography",
        "severity": "major",
        "status": "open",
        "title": "Manual reference list contains only 15 of 36 entries",
        "location": "Canonical Markdown:1010 onward",
        "evidence": "Twenty-one canonical references are omitted and two internal Notion pages follow the list.",
        "recommendation": "Regenerate all references from corrected_library.bib.",
        "related_to": "",
    },
    {
        "finding_id": "T-A10",
        "source": "Codex final text audit",
        "domain": "text",
        "severity": "moderate",
        "status": "open",
        "title": "Many-zeros rationale is unsupported",
        "location": "Canonical Markdown:412",
        "evidence": "Strict-sample zero shares are 0.169% for admissions and 0.093% for separations.",
        "recommendation": "Use PPML as the count-model rationale and describe log1p as secondary.",
        "related_to": "",
    },
    {
        "finding_id": "T-A11",
        "source": "Codex final text audit",
        "domain": "text",
        "severity": "moderate",
        "status": "open",
        "title": "Numerical and cross-reference errors remain",
        "location": "Canonical Markdown:185, 277, 313, 589",
        "evidence": "Age arithmetic, sector ranking and two internal references are wrong.",
        "recommendation": "Apply the listed local corrections before rendering.",
        "related_to": "",
    },
    {
        "finding_id": "T-A12",
        "source": "Codex final text audit",
        "domain": "rendering",
        "severity": "moderate",
        "status": "open",
        "title": "Duplicate figure and export debris remain visible",
        "location": "Canonical Markdown:169 and 16 marker lines",
        "evidence": "Figure 3.2 renders twice; file-ref markers and internal Notion rewrite pages appear in the PDF.",
        "recommendation": "Remove export debris and produce one synchronized Markdown/HTML/PDF release.",
        "related_to": "",
    },
    {
        "finding_id": "B-A01",
        "source": "Codex bibliography audit",
        "domain": "bibliography",
        "severity": "moderate",
        "status": "fixed_in_review_copy",
        "title": "Four records use superseded publication metadata",
        "location": "references/library.bib",
        "evidence": "Brynjolfsson, Dell'Acqua, Bick and Stanford AI Index require current canonical records.",
        "recommendation": "Adopt the review-only corrected library after author review.",
        "related_to": "",
    },
    {
        "finding_id": "B-A02",
        "source": "Codex bibliography audit",
        "domain": "bibliography",
        "severity": "moderate",
        "status": "open",
        "title": "Competing root bibliography is unsafe",
        "location": "Citações Dissertação Mestrado.bib",
        "evidence": "It has 35 entries, 15 nodate keys and two false mixed-metadata records.",
        "recommendation": "Use references/library.bib as the only source and archive the root file from the build.",
        "related_to": "",
    },
    {
        "finding_id": "B-A03",
        "source": "Codex bibliography audit",
        "domain": "bibliography",
        "severity": "minor",
        "status": "open",
        "title": "Four attachments are EBSCO exports rather than papers",
        "location": "references/pdfs",
        "evidence": "The affected Acemoglu and Autor attachments contain bibliographic exports.",
        "recommendation": "Replace them when convenient; metadata identity is already verified.",
        "related_to": "",
    },
    {
        "finding_id": "V2-G01",
        "source": "Codex V2 gate audit",
        "domain": "V2 gate",
        "severity": "major",
        "status": "blocked",
        "title": "Storage gate is closed",
        "location": "workspace volume",
        "evidence": "Baseline capture: 6.78 GiB free. Later post-cleanup recheck: 8.45 GiB. Both are below the approved 15-20 GiB minimum.",
        "recommendation": "Provision space without deleting user data before the full rebuild.",
        "related_to": "",
    },
    {
        "finding_id": "V2-G02",
        "source": "Codex V2 gate audit",
        "domain": "V2 gate",
        "severity": "major",
        "status": "blocked",
        "title": "Local CAGED files are not one current official vintage",
        "location": "data/raw/caged_*.parquet",
        "evidence": "Local files stop at June 2025 and predate June 2026 revisions; official 202101-202605 is continuous.",
        "recommendation": "Redownload every competence from one official vintage after fixing the cutoff.",
        "related_to": "",
    },
]


def import_prior(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for source in csv.DictReader(handle):
            status = source["resolution_status"]
            evidence = source["evidence"]
            aliases = ""
            if source["claim_id"] == "C010":
                status = "reopened"
                aliases = "T-A07"
                evidence += " The current executive summary again says the pattern is not job destruction."
            elif source["claim_id"] == "C031":
                status = "reopened"
                aliases = "T-A06"
                evidence += " All six current Appendix B artifact links return HTTP 404."
            rows.append(
                {
                    "finding_id": source["claim_id"],
                    "source": "Referee 2 round 2",
                    "domain": "text",
                    "severity": source["round1_severity"],
                    "status": status,
                    "title": source["round1_issue"],
                    "location": source["round1_location"],
                    "evidence": evidence,
                    "recommendation": source["round1_recommended_replacement"],
                    "related_to": aliases,
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = [*import_prior(args.prior_ledger), *CURRENT_FINDINGS]
    ids = [row["finding_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate finding IDs")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} deduplicated findings to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
