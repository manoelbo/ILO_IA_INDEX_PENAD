#!/usr/bin/env python3
"""Estimate preregistered sensitivity to alternative exposure measures."""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

MODULE_DIR = Path(__file__).resolve().parent
PANEL_DIR = MODULE_DIR.parent / "panel"
if str(PANEL_DIR) not in sys.path:
    sys.path.insert(0, str(PANEL_DIR))

from crosswalk import (
    ILO_FILENAME,
    classify_ilo_mean_sd,
    normalize_code,
    pooled_equal_weight_sd,
)
from estimators import fit_model


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_VARIANTS = (
    PACKAGE_ROOT / "data" / "derived" / "treatment_variants.csv"
)
DEFAULT_WORKBOOK = (
    PACKAGE_ROOT / "data" / "vintage" / "crosswalk" / ILO_FILENAME
)
DEFAULT_ANTHROPIC = (
    REPOSITORY_ROOT
    / "data"
    / "processed"
    / "anthropic_automation_augmentation_cbo.parquet"
)
DEFAULT_CLASSIFICATIONS = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "exposure_measure_variants.csv"
)
DEFAULT_RESULTS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "exposure_sensitivity_results.csv"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "exposure_sensitivity_support.csv"
)
DEFAULT_CORRELATIONS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "exposure_rank_correlations.csv"
)
DEFAULT_STATUS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "exposure_sensitivity_status.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "EXPOSURE_MEASURE_SENSITIVITY.md"
)

VINTAGE_2023_ORDER = (
    "Not affected",
    "Augmentation Potential",
    "Automation Potential",
    "The Big Uknown",
)
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)


def vintage_2023_mode(labels: Iterable[str]) -> str:
    values = [str(label) for label in labels if pd.notna(label)]
    if not values:
        return "No score"
    unknown = sorted(set(values) - set(VINTAGE_2023_ORDER))
    if unknown:
        raise ValueError(f"Unknown 2023 potential labels: {unknown}")
    counts = Counter(values)
    maximum = max(counts.values())
    return next(
        label
        for label in VINTAGE_2023_ORDER
        if counts.get(label, 0) == maximum
    )


def _first_unique(group: pd.DataFrame, column: str) -> Any:
    values = group[column].dropna().drop_duplicates()
    if len(values) > 1:
        raise RuntimeError(
            f"ISCO occupation has inconsistent {column}: "
            f"{values.tolist()}"
        )
    return values.iloc[0] if len(values) else np.nan


def build_isco_measures(tasks: pd.DataFrame) -> pd.DataFrame:
    required = {
        "ISCO_08",
        "Title",
        "predicted_score_2025_gpt4o",
        "predicted_score_2025_gemini",
        "mean_score_2023",
        "SD_2023",
        "potential23",
        "mean_score_2025",
        "SD_2025",
    }
    missing = sorted(required - set(tasks.columns))
    if missing:
        raise ValueError(f"ILO workbook is missing columns: {missing}")
    frame = tasks.copy()
    frame["isco08"] = frame["ISCO_08"].map(normalize_code)
    numeric = (
        "predicted_score_2025_gpt4o",
        "predicted_score_2025_gemini",
        "mean_score_2023",
        "SD_2023",
        "mean_score_2025",
        "SD_2025",
    )
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    records: list[dict[str, Any]] = []
    for isco08, group in frame.groupby("isco08", sort=True):
        gpt = group["predicted_score_2025_gpt4o"].dropna()
        gemini = group["predicted_score_2025_gemini"].dropna()
        gpt_mean = float(gpt.mean()) if len(gpt) else math.nan
        gemini_mean = float(gemini.mean()) if len(gemini) else math.nan
        gpt_sd = float(gpt.std(ddof=0)) if len(gpt) else math.nan
        gemini_sd = float(gemini.std(ddof=0)) if len(gemini) else math.nan
        gpt_label = classify_ilo_mean_sd(gpt_mean, gpt_sd)
        gemini_label = classify_ilo_mean_sd(gemini_mean, gemini_sd)
        records.append(
            {
                "isco08": isco08,
                "title": _first_unique(group, "Title"),
                "mean_score_2023": _first_unique(
                    group, "mean_score_2023"
                ),
                "sd_2023": _first_unique(group, "SD_2023"),
                "potential_2023": _first_unique(group, "potential23"),
                "mean_score_2025": _first_unique(
                    group, "mean_score_2025"
                ),
                "sd_2025": _first_unique(group, "SD_2025"),
                "gpt4o_mean": gpt_mean,
                "gpt4o_sd": gpt_sd,
                "gpt4o_label": gpt_label,
                "gemini_mean": gemini_mean,
                "gemini_sd": gemini_sd,
                "gemini_label": gemini_label,
                "models_agree": (
                    gpt_label == gemini_label
                    and gpt_label != "No score"
                ),
            }
        )
    result = pd.DataFrame(records)
    if result["isco08"].duplicated().any():
        raise RuntimeError("ISCO measure table is not unique by occupation")
    return result


def _split_codes(value: Any) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [
        normalize_code(code)
        for code in str(value).split(";")
        if normalize_code(code)
    ]


def build_cbo_measure_variants(
    classifications: pd.DataFrame,
    isco_measures: pd.DataFrame,
) -> pd.DataFrame:
    required = {"cbo_4d", "scored_isco08_codes"}
    missing = sorted(required - set(classifications.columns))
    if missing:
        raise ValueError(f"Classification is missing columns: {missing}")
    lookup = isco_measures.set_index("isco08").to_dict("index")
    records: list[dict[str, Any]] = []
    for row in classifications.itertuples(index=False):
        targets = [
            lookup[code]
            for code in _split_codes(row.scored_isco08_codes)
            if code in lookup
        ]
        vintage_targets = [
            target
            for target in targets
            if pd.notna(target["potential_2023"])
        ]
        vintage_scores = [
            float(target["mean_score_2023"])
            for target in vintage_targets
            if pd.notna(target["mean_score_2023"])
            and pd.notna(target["sd_2023"])
        ]
        vintage_sds = [
            float(target["sd_2023"])
            for target in vintage_targets
            if pd.notna(target["mean_score_2023"])
            and pd.notna(target["sd_2023"])
        ]
        consensus_targets = [
            target for target in targets if target["models_agree"]
        ]
        consensus_scores = [
            float(target["mean_score_2025"])
            for target in consensus_targets
            if pd.notna(target["mean_score_2025"])
            and pd.notna(target["sd_2025"])
        ]
        consensus_sds = [
            float(target["sd_2025"])
            for target in consensus_targets
            if pd.notna(target["mean_score_2025"])
            and pd.notna(target["sd_2025"])
        ]
        consensus_mean = (
            float(np.mean(consensus_scores))
            if consensus_scores
            else math.nan
        )
        consensus_sd = pooled_equal_weight_sd(
            consensus_scores, consensus_sds
        )
        records.append(
            {
                "cbo_4d": normalize_code(row.cbo_4d),
                "vintage_2023_label": vintage_2023_mode(
                    [
                        str(target["potential_2023"])
                        for target in vintage_targets
                    ]
                ),
                "vintage_2023_mean_score": (
                    float(np.mean(vintage_scores))
                    if vintage_scores
                    else math.nan
                ),
                "vintage_2023_pooled_sd": pooled_equal_weight_sd(
                    vintage_scores, vintage_sds
                ),
                "vintage_2023_destinations": len(vintage_targets),
                "model_consensus_label": classify_ilo_mean_sd(
                    consensus_mean, consensus_sd
                ),
                "model_consensus_mean_score": consensus_mean,
                "model_consensus_pooled_sd": consensus_sd,
                "model_consensus_destinations": len(consensus_scores),
                "all_2025_destinations": len(targets),
            }
        )
    result = pd.DataFrame(records).sort_values("cbo_4d")
    if result["cbo_4d"].duplicated().any():
        raise RuntimeError("CBO measure variants are not unique")
    return result.reset_index(drop=True)


def clean_anthropic(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "cbo_4d",
        "anthropic_automation_index",
        "imputation_method",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Anthropic data is missing columns: {missing}")
    result = frame.copy()
    result["cbo_4d"] = result["cbo_4d"].astype(str).str.strip()
    result = result.loc[
        result["cbo_4d"].str.fullmatch(r"\d{4}")
        & result["imputation_method"].ne("zero_imputation_no_data")
    ].copy()
    result["anthropic_automation_index"] = pd.to_numeric(
        result["anthropic_automation_index"], errors="coerce"
    )
    result = result.dropna(subset=["anthropic_automation_index"])
    if result["cbo_4d"].duplicated().any():
        raise RuntimeError("Anthropic data is not unique by CBO4")
    mean = float(result["anthropic_automation_index"].mean())
    standard_deviation = float(
        result["anthropic_automation_index"].std(ddof=0)
    )
    if not standard_deviation > 0:
        raise RuntimeError("Anthropic index has no cross-CBO variation")
    result["anthropic_z"] = (
        result["anthropic_automation_index"] - mean
    ) / standard_deviation
    return result.sort_values("cbo_4d").reset_index(drop=True)


def spearman_rank_correlation(
    left: pd.Series,
    right: pd.Series,
) -> float:
    complete = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(complete) < 2:
        return math.nan
    return float(
        complete["left"]
        .rank(method="average")
        .corr(complete["right"].rank(method="average"))
    )


def rank_correlations(
    variants: pd.DataFrame,
    anthropic_raw: pd.DataFrame,
) -> pd.DataFrame:
    ilo = variants[["cbo_4d", "isco08_mean_score"]].copy()
    ilo["cbo_4d"] = ilo["cbo_4d"].astype(str).str.zfill(4)
    raw = anthropic_raw.copy()
    raw["cbo_4d"] = raw["cbo_4d"].astype(str).str.strip()
    raw = raw.loc[raw["cbo_4d"].str.fullmatch(r"\d{4}")].copy()
    merged = ilo.merge(raw, on="cbo_4d", how="inner", validate="one_to_one")
    rows = []
    samples = {
        "direct_matches": merged["imputation_method"].eq("direct_match"),
        "direct_plus_hierarchical": merged["imputation_method"].ne(
            "zero_imputation_no_data"
        ),
    }
    for sample, selection in samples.items():
        current = merged.loc[selection].dropna(
            subset=["isco08_mean_score", "anthropic_automation_index"]
        )
        rows.append(
            {
                "sample": sample,
                "n_cbo": int(len(current)),
                "spearman_rho": spearman_rank_correlation(
                    current["isco08_mean_score"],
                    current["anthropic_automation_index"],
                ),
                "ilo_measure": "isco08_mean_score_2025",
                "anthropic_measure": "anthropic_automation_index",
            }
        )
    return pd.DataFrame(rows)


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or np.isnan(values).any():
        raise ValueError("BH p-values must be a complete vector")
    order = np.argsort(values)
    ranked = values[order]
    adjusted_ranked = np.minimum.accumulate(
        (ranked * len(values) / np.arange(1, len(values) + 1))[::-1]
    )[::-1]
    adjusted = np.empty(len(values), dtype=float)
    adjusted[order] = np.minimum(adjusted_ranked, 1.0)
    return adjusted


def prepare_measure_samples(
    panel: pd.DataFrame,
    cbo_variants: pd.DataFrame,
    anthropic: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    data = panel.copy()
    data["cbo_4d"] = data["cbo_4d"].astype(str).str.zfill(4)
    measures = data.merge(
        cbo_variants,
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    vintage = measures.loc[
        measures["vintage_2023_label"].isin(
            ["Automation Potential", "Not affected"]
        )
    ].copy()
    vintage["treatment_2023"] = vintage[
        "vintage_2023_label"
    ].eq("Automation Potential").astype(int)
    vintage["post_treat_2023"] = (
        vintage["post"] * vintage["treatment_2023"]
    )

    consensus = measures.loc[
        measures["model_consensus_label"].eq("Not Exposed")
        | measures["model_consensus_label"].str.startswith(
            "Exposed", na=False
        )
    ].copy()
    consensus["treatment_consensus"] = consensus[
        "model_consensus_label"
    ].str.startswith("Exposed").astype(int)
    consensus["post_treat_consensus"] = (
        consensus["post"] * consensus["treatment_consensus"]
    )

    anthro = data.merge(
        anthropic[["cbo_4d", "anthropic_z"]],
        on="cbo_4d",
        how="inner",
        validate="many_to_one",
    )
    anthro["post_anthropic_z"] = anthro["post"] * anthro["anthropic_z"]
    return {
        "vintage_2023": vintage,
        "model_consensus": consensus,
        "anthropic_continuous": anthro,
    }


def _support_row(
    measure_id: str,
    sample: pd.DataFrame,
) -> dict[str, Any]:
    if measure_id == "vintage_2023":
        treated = sample.loc[sample["treatment_2023"].eq(1), "cbo_4d"]
        control = sample.loc[sample["treatment_2023"].eq(0), "cbo_4d"]
        term = "post_treat_2023"
        scale = "Automation Potential vs Not affected"
    elif measure_id == "model_consensus":
        treated = sample.loc[
            sample["treatment_consensus"].eq(1), "cbo_4d"
        ]
        control = sample.loc[
            sample["treatment_consensus"].eq(0), "cbo_4d"
        ]
        term = "post_treat_consensus"
        scale = "Exposed vs Not Exposed among consensus destinations"
    else:
        treated = pd.Series(dtype=str)
        control = pd.Series(dtype=str)
        term = "post_anthropic_z"
        scale = "one SD of the automation-minus-augmentation index"
    return {
        "measure_id": measure_id,
        "scale": scale,
        "treatment_term": term,
        "panel_rows": int(len(sample)),
        "cbo_families": int(sample["cbo_4d"].nunique()),
        "treated_cbo_families": int(treated.nunique()),
        "control_cbo_families": int(control.nunique()),
        "months": int(sample["periodo"].nunique()),
    }


def estimate_sensitivities(
    panel: pd.DataFrame,
    cbo_variants: pd.DataFrame,
    anthropic: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    samples = prepare_measure_samples(panel, cbo_variants, anthropic)
    configurations = {
        "vintage_2023": "post_treat_2023",
        "model_consensus": "post_treat_consensus",
        "anthropic_continuous": "post_anthropic_z",
    }
    rows: list[dict[str, Any]] = []
    supports: list[dict[str, Any]] = []
    for measure_id, term in configurations.items():
        sample = samples[measure_id]
        supports.append(_support_row(measure_id, sample))
        for outcome, estimator in OUTCOMES:
            result, model = fit_model(
                sample,
                model_id=f"{measure_id}__{outcome}",
                outcome=outcome,
                treatment_term=term,
                estimator=estimator,
                fixed_effects=("cbo_4d", "periodo"),
                cluster_variables=("cbo_4d",),
                principal=True,
                separation_check=("fe",),
            )
            result["measure_id"] = measure_id
            result["measure_scale"] = supports[-1]["scale"]
            rows.append(result)
            del model
            gc.collect()
    results = pd.DataFrame(rows)
    expected = len(configurations) * len(OUTCOMES)
    if len(results) != expected:
        raise RuntimeError(
            f"Expected {expected} exposure sensitivity models"
        )
    results["p_value_adjusted_bh"] = benjamini_hochberg(
        results["p_value"].to_numpy(dtype=float)
    )
    return results, pd.DataFrame(supports)


def render_report(
    results: pd.DataFrame,
    support: pd.DataFrame,
    correlations: pd.DataFrame,
    cbo_variants: pd.DataFrame,
    isco_measures: pd.DataFrame,
) -> str:
    lines = [
        "# Exposure-Measure Sensitivity",
        "",
        "Task 27 reports all three frozen measurement exercises. The "
        "fifteen nominal p-values are adjusted together with "
        "Benjamini-Hochberg. These are sensitivity estimates; they do not "
        "repair the failed national pretrend diagnostics.",
        "",
        "## Support",
        "",
        "| Measure | Scale | CBOs | Treated | Control | Months |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in support.itertuples(index=False):
        lines.append(
            f"| {row.measure_id} | {row.scale} | {row.cbo_families} | "
            f"{row.treated_cbo_families} | {row.control_cbo_families} | "
            f"{row.months} |"
        )
    lines.extend(
        [
            "",
            "The Anthropic row is continuous, so treated/control counts are "
            "not applicable. Rows with `zero_imputation_no_data` are "
            "excluded rather than interpreted as observed zero exposure.",
            "",
            "## Rank correlation with Anthropic",
            "",
            "| Sample | CBOs | Spearman rho |",
            "|---|---:|---:|",
        ]
    )
    for row in correlations.itertuples(index=False):
        lines.append(
            f"| {row.sample} | {row.n_cbo} | {row.spearman_rho:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Re-estimated principal specification",
            "",
            "| Measure | Outcome | Coefficient | SE | Nominal p | "
            "BH-adjusted p | N | CBO clusters |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in results.itertuples(index=False):
        lines.append(
            f"| {row.measure_id} | {row.outcome} | "
            f"{row.coefficient:.6f} | {row.standard_error:.6f} | "
            f"{row.p_value:.6g} | {row.p_value_adjusted_bh:.6g} | "
            f"{row.n_obs} | {row.minimum_clusters} |"
        )
    vintage_counts = (
        cbo_variants["vintage_2023_label"].value_counts().to_dict()
    )
    consensus_destinations = int(
        isco_measures["models_agree"].sum()
    )
    lines.extend(
        [
            "",
            "## Measurement diagnostics",
            "",
            f"- ISCO-08 occupations with complete GPT-4o/Gemini gradient "
            f"agreement: {consensus_destinations} of "
            f"{len(isco_measures)}.",
            f"- CBO4 2023 native-category counts: "
            f"`{json.dumps(vintage_counts, sort_keys=True)}`.",
            "- The 2023 estimate retains the native automation-versus-not-"
            "affected distinction; it does not relabel augmentation as "
            "unexposed.",
            "- The Anthropic coefficient is per one standard deviation of "
            "automation minus augmentation and therefore has a different "
            "substantive scale from the binary ILO coefficient.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def run(
    panel_path: Path,
    variants_path: Path,
    workbook_path: Path,
    anthropic_path: Path,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    panel = pd.read_parquet(panel_path)
    variants = pd.read_csv(variants_path, dtype={"cbo_4d": str})
    isco = build_isco_measures(pd.read_excel(workbook_path))
    cbo = build_cbo_measure_variants(variants, isco)
    anthropic_raw = pd.read_parquet(anthropic_path)
    anthropic = clean_anthropic(anthropic_raw)
    correlations = rank_correlations(variants, anthropic_raw)
    results, support = estimate_sensitivities(panel, cbo, anthropic)
    return results, support, correlations, cbo, isco


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate sensitivity to exposure measurement."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--anthropic", type=Path, default=DEFAULT_ANTHROPIC)
    parser.add_argument(
        "--classifications",
        type=Path,
        default=DEFAULT_CLASSIFICATIONS,
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument(
        "--correlations",
        type=Path,
        default=DEFAULT_CORRELATIONS,
    )
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results, support, correlations, cbo, isco = run(
        args.panel,
        args.variants,
        args.workbook,
        args.anthropic,
    )
    _atomic_csv(cbo, args.classifications)
    _atomic_csv(results, args.results)
    _atomic_csv(support, args.support)
    _atomic_csv(correlations, args.correlations)
    status = {
        "bh_family_size": int(len(results)),
        "model_count": int(len(results)),
        "all_models_converged": bool(results["converged"].all()),
        "measure_count": int(results["measure_id"].nunique()),
        "isco_model_agreement_count": int(isco["models_agree"].sum()),
        "adjusted_rejections_5pct": int(
            results["p_value_adjusted_bh"].lt(0.05).sum()
        ),
        "checkpoint_g_support_complete": bool(
            support["cbo_families"].gt(1).all()
        ),
    }
    _atomic_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        args.status,
    )
    _atomic_text(
        render_report(results, support, correlations, cbo, isco),
        args.report,
    )
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
