"""Pipeline for evaluating generated Section 4 results."""

from __future__ import annotations

import pandas as pd

from section4_results_evaluation.config import OUTPUT_DIR, TOP_N
from section4_results_evaluation.reporting import (
    add_judge_fields,
    write_audit,
    write_dissertation_report,
    write_judge_decisions,
    write_llm_prompt,
    write_top_results,
)
from section4_results_evaluation.scoring import score_candidate, select_top_results
from section4_results_evaluation.sources import load_candidate_universe


def score_candidates(universe: pd.DataFrame) -> pd.DataFrame:
    if universe.empty:
        return universe.copy()
    scored = universe.copy()
    updates = [score_candidate(row) for _, row in scored.iterrows()]
    update_df = pd.DataFrame(updates)
    for col in update_df.columns:
        scored[col] = update_df[col].values
    return scored.sort_values(["deterministic_score", "p_value"], ascending=[False, True], na_position="last")


def validate_outputs(universe: pd.DataFrame, top: pd.DataFrame) -> None:
    if universe.empty:
        raise RuntimeError("No candidate results were loaded.")
    required = ["source_file", "row_index", "coef", "p_value", "result_status"]
    for col in required:
        if col not in universe.columns or universe[col].isna().any():
            raise RuntimeError(f"Candidate universe missing required values in {col}.")
    if len(top) != TOP_N:
        raise RuntimeError(f"Expected exactly {TOP_N} top results, found {len(top)}.")
    if top["market_reconfiguration_channel"].isna().any():
        raise RuntimeError("Every selected result must have a market reconfiguration channel.")
    if (top["exploratory_only"].astype(bool) & top["placement"].eq("texto principal")).any():
        raise RuntimeError("Exploratory results cannot appear in the main text.")
    if top["pretrend_status"].astype(str).str.lower().eq("fail").any() and top["causal_tier"].eq("causal_headline").any():
        bad = top[top["pretrend_status"].astype(str).str.lower().eq("fail") & top["causal_tier"].eq("causal_headline")]
        if not bad.empty:
            raise RuntimeError("Failed-pretrend results cannot be causal headlines.")
    no_pretrend_headline = top[
        top["pretrend_status"].astype(str).str.lower().isin(["not_available", "nan"])
        & top["causal_tier"].eq("causal_headline")
    ]
    if not no_pretrend_headline.empty:
        raise RuntimeError("Results without formal pretrend tests cannot be causal headlines.")
    log_selected = top["outcome"].astype(str).str.startswith("ln_") | top["outcome_label"].astype(str).str.contains("log", case=False, na=False)
    if top.loc[log_selected, "effect_percent"].isna().any():
        raise RuntimeError("Every selected log result must have effect_percent.")
    if top["recommended_sentence_pt"].isna().any() or top["recommended_sentence_pt"].eq("").any():
        raise RuntimeError("Every selected result must have a Portuguese suggested sentence.")
    for tag, minimum in {
        "admission_flow": 4,
        "separation_flow": 4,
        "net_flow": 2,
        "wage_any": 6,
        "composition_or_heterogeneity": 5,
        "spatial_connectivity": 3,
        "occupational_mechanism": 3,
    }.items():
        count = top["channel_tags"].fillna("").str.contains(tag, regex=False).sum()
        if count < minimum:
            raise RuntimeError(f"Top results do not satisfy minimum coverage for {tag}: {count} < {minimum}")


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    universe = load_candidate_universe()
    universe.to_csv(OUTPUT_DIR / "result_candidate_universe.csv", index=False)
    scores = score_candidates(universe)
    scores.to_csv(OUTPUT_DIR / "result_candidate_scores.csv", index=False)
    top = select_top_results(scores, top_n=TOP_N)
    top = add_judge_fields(top)
    top.to_csv(OUTPUT_DIR / "top_30_results.csv", index=False)
    write_top_results(OUTPUT_DIR / "top_30_results.md", top)
    write_dissertation_report(OUTPUT_DIR / "top_30_results_for_dissertation.md", top)
    write_llm_prompt(OUTPUT_DIR / "llm_judge_prompt.md")
    write_judge_decisions(OUTPUT_DIR / "llm_judge_decisions.json", scores)
    write_audit(OUTPUT_DIR / "result_evaluation_audit.md", universe, scores, top)
    validate_outputs(universe, top)


if __name__ == "__main__":
    run()
