#!/usr/bin/env python3
"""Emit the isolated-worker prompt for one queue row.

Every worker gets an identical contract; only the row, the source identity and the
version-gate flag vary. The controller deliberately supplies NO evidence summary,
NO candidate conclusion and NO other row's findings — the worker performs its own
extraction and search against the page index and splits.

Usage: make_worker_prompt.py <row_id>
"""
import csv, json, os, sys

ROOT = "/Users/manebrasil/Documents/Projects/Dissetação Mestrado"
RUN = "references/claim_audit/runs/claude_opus_5/20260801T160057Z_claude-opus-5_max"

# Works whose BibLaTeX record describes the PUBLISHED article while the stored file is a
# working paper / discussion paper / preprint. Protocol trigger MET -> per-row issue.
VERSION_MISMATCH = {
    "goodman_bacon_difference_2021": ("Journal of Econometrics 225(2), 254-277, 2021",
                                      "NBER Working Paper 25018"),
    "callaway_difference_2021": ("Journal of Econometrics 225(2), 200-230, 2021",
                                 "arXiv:1803.09015, dated December 1 2020"),
    "sun_estimating_2021": ("Journal of Econometrics 225(2), 175-199, 2021",
                            "arXiv:1804.05785v2, dated September 22 2020"),
    "de_chaisemartin_two-way_2020": ("American Economic Review 110(9), 2964-2996, 2020",
                                     "arXiv preprint"),
    "santos_silva_log_2006": ("The Review of Economics and Statistics 88(4), 641-658, 2006",
                              "CEP Discussion Paper No 701, July 2005"),
    "chen_logs_2024": ("The Quarterly Journal of Economics 139(2), 891-936, 2024",
                       "arXiv:2212.06080v7, dated November 15 2023"),
}

# Stored-file version strings, from the source identity scan (cover pages).
VERSIONS = {
    "bick_rapid_2024": "FRB St. Louis Working Paper 2024-027F, revision date October 2025",
    "goodman_bacon_difference_2021": "NBER Working Paper 25018",
    "callaway_difference_2021": "arXiv:1803.09015 working paper, December 1 2020",
    "sun_estimating_2021": "arXiv:1804.05785v2, September 22 2020",
    "de_chaisemartin_two-way_2020": "arXiv working paper version",
    "santos_silva_log_2006": "CEP Discussion Paper No 701, July 2005",
    "chen_logs_2024": "arXiv:2212.06080v7, November 15 2023",
}


def main():
    row_id = sys.argv[1]
    rows = list(csv.DictReader(open(os.path.join(ROOT, "references/claim_audit/claim_inventory.tsv"),
                                    newline="", encoding="utf-8"), delimiter="\t"))
    inv = rows[int(row_id[1:]) - 1]
    key = inv["citation_key"]
    prep = json.load(open(os.path.join(ROOT, RUN, "source_build/source_prep_summary.json"), encoding="utf-8"))
    man = {r["citation_key"]: r for r in csv.DictReader(
        open(os.path.join(ROOT, "references/pdf_manifest.tsv"), newline="", encoding="utf-8"), delimiter="\t")}

    is_legal = key not in man
    is_ai = inv["claim_type"] == "AUTHOR_INFERENCE"
    vm = VERSION_MISMATCH.get(key)
    info = prep.get(key, {})
    version = VERSIONS.get(key, "stored file as attached (record the exact version from its cover page)")

    P = []
    A = P.append
    A("You are an isolated fact-check worker for a publication-grade source-to-claim audit of a Brazilian "
      "master's dissertation. You judge EXACTLY ONE claim-source relationship. Be rigorous, skeptical and "
      "literal. Do not be agreeable - your job is to detect mismatch. An unqualified claim must be judged "
      "as written, not as charitably reconstructed.")
    A(f"\nWORKSPACE: {ROOT}")
    A("\n## HARD CONSTRAINTS")
    A("- NEVER open the full source PDF. Read ONLY 4-page split files, at most 3 splits (~12 pages) per batch.")
    A("- Do NOT read anything under references/claim_audit/runs/ except the split files and page index named "
      "below. Never read results/, worker_out/, audit_log.jsonl, or any other auditor's output. This is a "
      "blind audit; form your own judgment.")
    A("- Do NOT modify any file outside the single output path given at the end.")
    A("- Do NOT use the abstract, web snippets, secondary sources or another paper as evidence for the claim. "
      "Evidence must come from the body of THIS stored file. (Web use is allowed ONLY to confirm publication "
      "identity/version, never to substitute for the source.)")
    A("- You MUST visually Read the actual rendered page (Read tool on the split PDF) for any evidence "
      "involving a table, figure, equation, footnote, unusual layout or doubtful OCR. Text extraction may "
      "only narrow the search; it may not be your final evidence.")

    A("\n## THE ROW UNDER AUDIT")
    A(f"row_id: {row_id}\nclaim_id: {inv['claim_id']}\ncitation_key: {key}\noccurrence_id: {inv['occurrence_id']}")
    A(f"section: \"{inv['section']}\", paragraph {inv['paragraph']}\nclaim_type: {inv['claim_type']}")
    A(f"work: {inv['work']}")
    A("\nDissertation claim (Portuguese, verbatim - do NOT translate in your output):")
    A(f"\"{inv['affirmation_pt']}\"")
    A("\nSurrounding dissertation text (verbatim, CONTEXT ONLY):")
    A(f"\"{inv['source_excerpt']}\"")
    A("\nIMPORTANT: judge ONLY the first quoted claim. If the surrounding text bundles other assertions or "
      "cites other works, those are SEPARATE rows judged by other workers - do not let them influence this "
      "verdict and do not judge them. If this claim is part of a grouped citation, judge whether THIS work "
      "supports it; never approve it because a co-cited work would.")

    A("\n## THE STORED SOURCE (audit this exact file, not the idealized citation)")
    if is_legal:
        A("This is a legal web source with NO PDF (Brazilian legislation). Use the official legal locator "
          "(article, paragraph, item). NEVER invent a page number.")
        A("Set printed_pages to the form 'art. X, § Y (HTML sem paginação)', pdf_page_indices to 'N/A', "
          "source_locator to the exact official legal hierarchy, and evidence_page_range to null.")
        A("You may use the web ONLY to retrieve the official text of this instrument from an official "
          "government domain (planalto.gov.br or equivalent). Record the URL in search_coverage.")
    else:
        rel = man[key]["pdf_path"]
        A(f"- Original (DO NOT OPEN DIRECTLY): references/{rel}")
        A(f"- Stored version: {version}")
        A(f"- Total physical pages: {info.get('pages','?')}")
        A(f"- source_sha256: {man[key]['sha256']}")
        off = info.get("printed_offset")
        if off is not None:
            A(f"- Detected page offset (VERIFY IT YOURSELF on a rendered page): printed page N == physical "
              f"page N + {off}. If the document has unnumbered front matter or restarts numbering, correct "
              f"this and say so. Report printed and physical pagination SEPARATELY - never conflate them.")
        else:
            A("- Page offset could NOT be auto-detected. You MUST establish the printed/physical relationship "
              "yourself by looking at a rendered page, and state it in search_coverage. Report printed and "
              "physical pagination separately. If the document truly has no printed numbers, set "
              "printed_pages to 'sem paginação impressa' and rely on physical indices.")
        A(f"\nSPLITS DIRECTORY:\n{RUN}/source_build/split_{key}/")
        A(f"Files are named {key}_ppA-B.pdf where A-B are PHYSICAL page numbers.")
        A(f"\nPER-PAGE TEXT INDEX (for LOCATING candidates only, never as final evidence):")
        A(f"{RUN}/source_build/{key}_page_index.json  - a JSON dict mapping physical page number -> text.")
        A("Query it with a small script (do NOT print the whole file). Derive your own search terms from the "
          "claim: figures, statistics, method names, populations, periods. Record every term and page range "
          "you examine - this is mandatory and must be exhaustive if your verdict is NOT_FOUND.")

    if vm:
        A("\n## SOURCE VERSION GATE - MISMATCH ALREADY ESTABLISHED FOR THIS WORK")
        A(f"The BibLaTeX record describes the PUBLISHED article ({vm[0]}), but the stored file is: {vm[1]}.")
        A("Therefore you MUST: (a) audit the stored file; (b) use the STORED file's real pagination and never "
          "present it as published-article pagination; (c) include one issue with issue_code "
          "PDF_VERSION_MISMATCH, severity MINOR, recommended_action REPLACE_SOURCE, needs_new_source false, "
          "recommending that the attachment be replaced by the final published version. "
          "This is IN ADDITION to any substantive issue. A version mismatch does NOT by itself determine "
          "whether the claim is supported - judge the content separately and set fact_checked on the merits. "
          "If the content is otherwise fully supported, the verdict is still not SUPPORTED, because a "
          "structured issue exists; use PARTIALLY_SUPPORTED only if the content itself is partial, otherwise "
          "report the substantive finding honestly and let the PDF_VERSION_MISMATCH issue stand alongside it. "
          "If content is fully supported and the ONLY defect is the version, set fact_checked to SUPPORTED "
          "ONLY IF you can do so with an empty issue list - which you cannot - so instead use "
          "PARTIALLY_SUPPORTED and say plainly in mismatch_explanation_pt that the substantive content is "
          "fully supported and the sole defect is the attached version.")

    A("\n## WHAT TO SCRUTINISE")
    A("Check every dimension INDEPENDENTLY and literally: population (who exactly - all adults? employed? age "
      "range? sample frame?), geography, time period/wave, the exact quantity a number refers to, direction, "
      "magnitude, comparison basis, method, and MODALITY (does the source say 'used at least once' where the "
      "dissertation says 'routinely'? 'associated with' where the dissertation says 'caused'?). Check whether "
      "a different nearby number in the source is the true match. Check whether the source hedges where the "
      "dissertation is categorical. Check whether the source's own qualifications or footnotes undercut the "
      "claim as written.")

    if is_ai:
        A("\n## AUTHOR_INFERENCE RULE - MANDATORY THREE-PART DECOMPOSITION")
        A("You must separately determine and report:")
        A("1. premises_supported - does the cited work support the FACTUAL PREMISES the inference rests on?")
        A("2. inference_follows - does the dissertation's inference reasonably follow from those premises?")
        A("3. is_author_interpretation - is this the dissertation author's own interpretation, or does the "
          "source itself state this conclusion?")
        A("CRITICAL: do NOT record that the article states the conclusion merely because the inference seems "
          "reasonable. Find the source ACTUALLY saying it, or record that it does not. A statement that is "
          "adjacent, weaker, or about a related proposition is NOT the same proposition - judge the "
          "difference precisely. NOT_VERIFIABLE exists for normative/interpretive claims that cannot be "
          "established from the cited source alone; consider it seriously. But if the source does supply the "
          "premises and the inference is a modest restatement, say so.")

    A("\n## VERDICT TAXONOMY (choose exactly one)")
    A("- SUPPORTED - supports the FULL claim with compatible population, geography, period, direction, "
      "magnitude, comparison, method and modality.\n"
      "- PARTIALLY_SUPPORTED - claim has independently meaningful components; source supports only some.\n"
      "- OVERSTATED - same general direction, but the dissertation strengthens causality, magnitude, scope, "
      "certainty, generality or interpretation.\n"
      "- CONTRADICTED - source reports a materially opposing result.\n"
      "- NOT_FOUND - no supporting evidence after documented exhaustive search.\n"
      "- NOT_VERIFIABLE - normative/interpretive/author inference not establishable from this source alone.\n"
      "- SOURCE_BLOCKED - missing, corrupt, wrong, inaccessible, or too version-incompatible to judge.")
    A("Only SUPPORTED is a full pass. Anything else REQUIRES at least one structured issue.")

    out = f"{RUN}/source_build/worker_out/{row_id}.raw.json"
    A(f"\n## OUTPUT\nWrite a single JSON object to:\n{out}\n(write nothing else anywhere)")
    A("""
{
  "row_id":"%s","claim_id":"%s","citation_key":"%s","occurrence_id":"%s",
  "fact_checked":"<verdict>",
  "printed_pages":"<e.g. p. 12 or pp. 12-13, or the legal locator form>",
  "pdf_page_indices":"<e.g. 15 or 15-16, or N/A>",
  "source_locator":"<e.g. Section 3.2, Table 2, footnote 8, or official legal hierarchy>",
  "evidence_summary_pt":"<PT-BR: what the source ACTUALLY establishes at that location, with exact figures>",
  "evidence_anchor":"<verbatim phrase from the source, its own language, MAX 12 WORDS>",
  "search_coverage":"<physical page ranges actually inspected + search terms + which pages you read VISUALLY>",
  "source_version":"<exact version/date of the stored file you audited>",
  "confidence":"HIGH|MEDIUM|LOW",
  "evidence_page_range":<[first,last] contiguous, OR [p1,p2,p3,...] discrete loci, OR null for the legal source>,%s
  "issues":[ {
     "issue_code":"<WRONG_MAGNITUDE|WRONG_POPULATION|WRONG_PERIOD|WRONG_DIRECTION|PARTIAL_SCOPE|CAUSAL_OVERCLAIM|GENERALIZATION_OVERCLAIM|MISATTRIBUTED_METHOD|WRONG_SOURCE|MISSING_EVIDENCE|AUTHOR_INFERENCE_UNSUPPORTED|PDF_VERSION_MISMATCH|SOURCE_UNAVAILABLE>",
     "severity":"BLOCKER|CRITICAL|MAJOR|MINOR",
     "claim_as_written_pt":"<verbatim PT claim>",
     "source_supports_pt":"<PT-BR: what the source supports instead>",
     "mismatch_explanation_pt":"<PT-BR: precise explanation of the gap>",
     "recommended_revision_pt":"<PT-BR: corrected dissertation sentence the author could paste in>",
     "needs_new_source":true|false,
     "recommended_action":"KEEP|NARROW_CLAIM|REWRITE_CLAIM|ADD_SOURCE|REPLACE_SOURCE|REMOVE_CITATION|REMOVE_CLAIM|MANUAL_REVIEW"
  } ]
}""" % (row_id, inv["claim_id"], key, inv["occurrence_id"],
        ("\n  \"premise_assessment\":{\"premises_supported\":\"YES|PARTIAL|NO\","
         "\"inference_follows\":\"YES|PARTIAL|NO\",\"is_author_interpretation\":true|false,"
         "\"reasoning_pt\":\"<PT-BR: separate what the source establishes from what the author concludes>\"},")
        if is_ai else ""))
    A("\"issues\" must be [] if and only if fact_checked==\"SUPPORTED\".")
    if is_ai:
        A("premise_assessment is REQUIRED regardless of verdict.")
    A("Portuguese fields in PT-BR. evidence_anchor in the source's own language, max 12 words (count them).")
    A("\nThen report back in 8 lines or fewer: verdict, printed page, pdf page, the decisive source "
      "wording/figures, and whether you visually inspected the page.")

    print("\n".join(P))


if __name__ == "__main__":
    main()
