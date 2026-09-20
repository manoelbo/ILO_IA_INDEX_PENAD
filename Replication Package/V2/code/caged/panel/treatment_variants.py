#!/usr/bin/env python3
"""Build preregistered employment-weighted treatment variants."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Sequence

import duckdb
import numpy as np
import pandas as pd

from crosswalk import (
    ILO_FILENAME,
    ISCO_CORRESPONDENCE_FILENAME,
    MTE_CACHE_FILENAME,
    build_classification_from_frozen,
    classify_ilo_mean_sd,
    load_ilo_scores,
    load_isco88_to_isco08,
    normalize_code,
    unique_preserve,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CROSSWALK_DIR = PACKAGE_ROOT / "data" / "vintage" / "crosswalk"
DEFAULT_MOVEMENTS = (
    PACKAGE_ROOT
    / "data"
    / "interim"
    / "movimentacoes"
    / "competenciamov=*"
    / "part.parquet"
)
DEFAULT_VARIANTS = (
    PACKAGE_ROOT / "data" / "derived" / "treatment_variants.csv"
)
DEFAULT_COMPARISON = (
    PACKAGE_ROOT
    / "results"
    / "treatment"
    / "treatment_variant_comparison.csv"
)
DEFAULT_CBO_4121_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "treatment"
    / "CBO_4121_TREATMENT_VARIANTS.md"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "treatment"
    / "treatment_variant_support.json"
)
PRE_START = 202101
PRE_END = 202211
LABEL_ORDER = (
    "Not Exposed",
    "Minimal Exposure",
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
)
VARIANT_COLUMNS = {
    "V-A": "gradient_v_a",
    "V-B": "gradient_v_b",
    "V-C": "gradient_v_c",
    "V-D": "gradient_v_d",
}


def _numeric_arrays(
    values: Sequence[float],
    weights: Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    if (
        value_array.ndim != 1
        or weight_array.ndim != 1
        or len(value_array) == 0
        or len(value_array) != len(weight_array)
    ):
        raise ValueError("Values and weights must be non-empty vectors")
    if (
        not np.isfinite(value_array).all()
        or not np.isfinite(weight_array).all()
        or (weight_array < 0).any()
        or weight_array.sum() <= 0
    ):
        raise ValueError("Values and weights must be finite and positive")
    return value_array, weight_array


def weighted_mean(
    values: Sequence[float],
    weights: Sequence[float],
) -> float:
    value_array, weight_array = _numeric_arrays(values, weights)
    return float(np.average(value_array, weights=weight_array))


def task_only_sd(
    standard_deviations: Sequence[float],
    weights: Sequence[float],
) -> float:
    sd_array, weight_array = _numeric_arrays(
        standard_deviations,
        weights,
    )
    return float(
        np.sqrt(np.average(sd_array**2, weights=weight_array))
    )


def between_destination_sd(
    scores: Sequence[float],
    weights: Sequence[float],
) -> float:
    score_array, weight_array = _numeric_arrays(scores, weights)
    mean_score = np.average(score_array, weights=weight_array)
    return float(
        np.sqrt(
            np.average(
                (score_array - mean_score) ** 2,
                weights=weight_array,
            )
        )
    )


def pooled_weighted_sd(
    scores: Sequence[float],
    standard_deviations: Sequence[float],
    weights: Sequence[float],
) -> float:
    score_array, weight_array = _numeric_arrays(scores, weights)
    sd_array = np.asarray(standard_deviations, dtype=float)
    if len(sd_array) != len(score_array) or not np.isfinite(sd_array).all():
        raise ValueError("Task standard deviations must match scores")
    mean_score = np.average(score_array, weights=weight_array)
    variance = np.average(
        sd_array**2 + (score_array - mean_score) ** 2,
        weights=weight_array,
    )
    return float(np.sqrt(variance))


def weighted_mode_label(
    labels: Sequence[str],
    weights: Sequence[float],
) -> str:
    if len(labels) != len(weights) or not labels:
        raise ValueError("Labels and weights must be non-empty and aligned")
    unknown = sorted(set(labels) - set(LABEL_ORDER))
    if unknown:
        raise ValueError(f"Unknown ILO exposure labels: {unknown}")
    _, weight_array = _numeric_arrays(
        [float(LABEL_ORDER.index(label)) for label in labels],
        weights,
    )
    totals = {
        label: float(
            weight_array[
                np.asarray(labels, dtype=object) == label
            ].sum()
        )
        for label in set(labels)
    }
    maximum = max(totals.values())
    tied = {
        label
        for label, total in totals.items()
        if math.isclose(total, maximum, rel_tol=0, abs_tol=1e-12)
    }
    return next(label for label in LABEL_ORDER if label in tied)


def split_cbo6_weight(
    admission_weight: float,
    destination_count: int,
) -> list[float]:
    if admission_weight < 0 or destination_count <= 0:
        raise ValueError("Weight must be non-negative and targets positive")
    share = float(admission_weight) / destination_count
    return [share] * destination_count


def aggregate_pre_admissions(
    movements_glob: Path,
    *,
    start_period: int = PRE_START,
    end_period: int = PRE_END,
) -> tuple[pd.DataFrame, dict[str, int]]:
    source = "'" + str(movements_glob).replace("'", "''") + "'"
    connection = duckdb.connect()
    try:
        frame = connection.execute(
            f"""
            SELECT
                lpad(CAST(cbo2002ocupacao AS VARCHAR), 6, '0')
                    AS cbo2002_6d,
                CAST(sum(peso) AS BIGINT) AS pre_admissions
            FROM read_parquet({source}, hive_partitioning = true)
            WHERE CAST(competenciamov AS INTEGER)
                  BETWEEN {start_period} AND {end_period}
              AND saldomovimentacao = 1
              AND regexp_full_match(
                  CAST(cbo2002ocupacao AS VARCHAR),
                  '[0-9]{{4,6}}'
              )
              AND substring(
                  CAST(cbo2002ocupacao AS VARCHAR), 1, 4
              ) <> '0000'
              AND salario > 0
              AND salario < 1000000
              AND idade BETWEEN 14 AND 100
            GROUP BY cbo2002_6d
            ORDER BY cbo2002_6d
            """
        ).df()
    finally:
        connection.close()
    if (frame["pre_admissions"] < 0).any():
        raise RuntimeError("Negative signed CBO6 admission weight found")
    metrics = {
        "pre_admissions": int(frame["pre_admissions"].sum()),
        "cbo6_with_pre_admissions": int(
            frame["cbo2002_6d"].nunique()
        ),
    }
    return frame, metrics


def build_destination_table(
    crosswalk_dir: Path,
    pre_admissions: pd.DataFrame,
) -> pd.DataFrame:
    cache = pd.read_csv(
        crosswalk_dir / MTE_CACHE_FILENAME,
        dtype=str,
        keep_default_na=False,
    )
    scores = load_ilo_scores(crosswalk_dir / ILO_FILENAME)
    score_lookup = scores.set_index("isco_08").to_dict("index")
    correspondence = load_isco88_to_isco08(
        crosswalk_dir / ISCO_CORRESPONDENCE_FILENAME
    )
    admission_lookup = (
        pre_admissions.set_index("cbo2002_6d")["pre_admissions"]
        .astype(float)
        .to_dict()
    )
    records: list[dict[str, Any]] = []
    matched = cache.loc[
        cache["status"].eq("matched")
        & cache["cbo2002_6d"].ne("")
        & cache["ciuo88_code"].ne("")
    ].copy()
    for (cbo_4d, cbo_6d), group in matched.groupby(
        ["source_cbo_4d", "cbo2002_6d"],
        sort=True,
    ):
        targets = unique_preserve(
            [
                target
                for value in group["ciuo88_code"]
                for target in correspondence.get(
                    normalize_code(value),
                    [],
                )
                if target in score_lookup
                and not pd.isna(
                    score_lookup[target]["exposure_score"]
                )
                and not pd.isna(score_lookup[target]["exposure_sd"])
            ]
        )
        if not targets:
            continue
        normalized_cbo6 = normalize_code(cbo_6d, width=6)
        weight = float(admission_lookup.get(normalized_cbo6, 0.0))
        split_weights = split_cbo6_weight(weight, len(targets))
        for target, destination_weight in zip(
            targets,
            split_weights,
            strict=True,
        ):
            target_record = score_lookup[target]
            records.append(
                {
                    "cbo_4d": normalize_code(cbo_4d),
                    "cbo2002_6d": normalized_cbo6,
                    "isco08": target,
                    "isco08_title": target_record[
                        "occupation_title"
                    ],
                    "score": float(target_record["exposure_score"]),
                    "task_sd": float(target_record["exposure_sd"]),
                    "native_label": str(
                        target_record["exposure_gradient"]
                    ),
                    "cbo6_pre_admissions": weight,
                    "destination_weight": destination_weight,
                }
            )
    return pd.DataFrame(records)


def build_variants(
    base: pd.DataFrame,
    destinations: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    grouped = {
        cbo: group
        for cbo, group in destinations.groupby("cbo_4d", sort=True)
    }
    for row in base.itertuples(index=False):
        cbo = normalize_code(row.cbo_4d)
        record = row._asdict()
        record["gradient_v_a"] = row.cbo_ilo_gradient
        if cbo not in grouped:
            record.update(
                {
                    "gradient_v_b": "No score",
                    "gradient_v_c": "No score",
                    "gradient_v_d": "No score",
                    "employment_weight_fallback": False,
                    "matched_pre_admissions": 0.0,
                    "variant_b_mean": math.nan,
                    "variant_b_pooled_sd": math.nan,
                    "variant_c_task_sd": math.nan,
                    "between_destination_sd": math.nan,
                }
            )
            records.append(record)
            continue

        targets = (
            grouped[cbo]
            .groupby("isco08", as_index=False, sort=True)
            .agg(
                isco08_title=("isco08_title", "first"),
                score=("score", "first"),
                task_sd=("task_sd", "first"),
                native_label=("native_label", "first"),
                destination_weight=("destination_weight", "sum"),
            )
        )
        raw_weights = targets["destination_weight"].to_numpy(
            dtype=float
        )
        fallback = bool(raw_weights.sum() <= 0)
        employment_weights = (
            np.ones(len(targets), dtype=float)
            if fallback
            else raw_weights
        )
        equal_weights = np.ones(len(targets), dtype=float)
        scores = targets["score"].to_numpy(dtype=float)
        task_sds = targets["task_sd"].to_numpy(dtype=float)
        mean_b = weighted_mean(scores, employment_weights)
        pooled_b = pooled_weighted_sd(
            scores,
            task_sds,
            employment_weights,
        )
        mean_c = weighted_mean(scores, equal_weights)
        task_sd_c = task_only_sd(task_sds, equal_weights)
        record.update(
            {
                "gradient_v_b": classify_ilo_mean_sd(mean_b, pooled_b),
                "gradient_v_c": classify_ilo_mean_sd(
                    mean_c,
                    task_sd_c,
                ),
                "gradient_v_d": weighted_mode_label(
                    targets["native_label"].tolist(),
                    employment_weights,
                ),
                "employment_weight_fallback": fallback,
                "matched_pre_admissions": float(raw_weights.sum()),
                "variant_b_mean": mean_b,
                "variant_b_pooled_sd": pooled_b,
                "variant_c_task_sd": task_sd_c,
                "between_destination_sd": (
                    between_destination_sd(scores, equal_weights)
                ),
            }
        )
        records.append(record)
    result = pd.DataFrame(records).sort_values("cbo_4d")
    if not result["gradient_v_a"].equals(base["cbo_ilo_gradient"]):
        raise RuntimeError("Variant A changed from the frozen classification")
    return result.reset_index(drop=True)


def comparison_table(variants: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant, column in VARIANT_COLUMNS.items():
        changed = int(
            variants[column].ne(variants["gradient_v_a"]).sum()
        )
        counts = variants[column].value_counts().to_dict()
        for label in (*LABEL_ORDER[::-1], "No score"):
            rows.append(
                {
                    "variant": variant,
                    "classification": label,
                    "cbo_families": int(counts.get(label, 0)),
                    "changed_vs_v_a": changed,
                }
            )
    return pd.DataFrame(rows)


def render_cbo_4121_report(
    variants: pd.DataFrame,
    destinations: pd.DataFrame,
) -> str:
    row = variants.loc[variants["cbo_4d"].eq("4121")].iloc[0]
    targets = destinations.loc[
        destinations["cbo_4d"].eq("4121")
    ].copy()
    target_summary = (
        targets.groupby("isco08", as_index=False)
        .agg(
            title=("isco08_title", "first"),
            score=("score", "first"),
            task_sd=("task_sd", "first"),
            native_label=("native_label", "first"),
            pre_admission_weight=("destination_weight", "sum"),
        )
        .sort_values("isco08")
    )
    lines = [
        "# CBO 4121 Treatment-Variant Audit",
        "",
        "CBO 4121 (data-entry and transmission-equipment operators) is a "
        "decisive crosswalk case because one of its destinations is ISCO-08 "
        "4132, the highest-scored occupation in the frozen ILO index "
        "(mean score 0.70). The official chain also reaches ISCO-08 3341 "
        "and 4131, so the CBO4 classification is an aggregation rather than "
        "a one-to-one inheritance.",
        "",
        "| ISCO-08 | Title | Mean score | Task SD | Native label | "
        "Pre-treatment admission weight |",
        "|---|---|---:|---:|---|---:|",
    ]
    for target in target_summary.itertuples(index=False):
        lines.append(
            f"| {target.isco08} | {target.title} | "
            f"{target.score:.3f} | {target.task_sd:.3f} | "
            f"{target.native_label} | "
            f"{target.pre_admission_weight:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Variant outcome",
            "",
            f"- V-A principal: {row.gradient_v_a}.",
            f"- V-B employment-weighted mean and pooled SD: "
            f"{row.gradient_v_b} (mean {row.variant_b_mean:.3f}, "
            f"SD {row.variant_b_pooled_sd:.3f}).",
            f"- V-C task-only SD: {row.gradient_v_c} "
            f"(task SD {row.variant_c_task_sd:.3f}; separate "
            f"between-destination SD {row.between_destination_sd:.3f}).",
            f"- V-D employment-weighted native label: {row.gradient_v_d}.",
            f"- Equal-weight fallback used: "
            f"{'yes' if row.employment_weight_fallback else 'no'}.",
            "",
            "V-A remains the principal classification regardless of these "
            "sensitivity outcomes.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_outputs(
    variants: pd.DataFrame,
    comparison: pd.DataFrame,
    destinations: pd.DataFrame,
    pre_metrics: dict[str, int],
    variants_path: Path = DEFAULT_VARIANTS,
    comparison_path: Path = DEFAULT_COMPARISON,
    report_path: Path = DEFAULT_CBO_4121_REPORT,
    support_path: Path = DEFAULT_SUPPORT,
) -> dict[str, Any]:
    variants_path.parent.mkdir(parents=True, exist_ok=True)
    variants.to_csv(variants_path, index=False)
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(comparison_path, index=False)
    _atomic_text(
        render_cbo_4121_report(variants, destinations),
        report_path,
    )
    matched_cbo6 = destinations.loc[
        destinations["destination_weight"].gt(0),
        ["cbo2002_6d", "cbo6_pre_admissions"],
    ].drop_duplicates("cbo2002_6d")
    support: dict[str, Any] = {
        **pre_metrics,
        "cbo_families": int(len(variants)),
        "employment_weight_fallback_cbo_families": int(
            variants["employment_weight_fallback"].sum()
        ),
        "matched_cbo6_pre_admissions": int(
            matched_cbo6["cbo6_pre_admissions"].sum()
        ),
        "variant_changes_vs_v_a": {
            variant: int(
                variants[column].ne(variants["gradient_v_a"]).sum()
            )
            for variant, column in VARIANT_COLUMNS.items()
        },
    }
    support["matched_pre_admission_share"] = (
        support["matched_cbo6_pre_admissions"]
        / support["pre_admissions"]
    )
    _atomic_text(
        json.dumps(support, indent=2, sort_keys=True) + "\n",
        support_path,
    )
    return support


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build preregistered CBO treatment variants."
    )
    parser.add_argument(
        "--crosswalk-dir",
        type=Path,
        default=DEFAULT_CROSSWALK_DIR,
    )
    parser.add_argument(
        "--movements-glob",
        type=Path,
        default=DEFAULT_MOVEMENTS,
    )
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS)
    parser.add_argument(
        "--comparison",
        type=Path,
        default=DEFAULT_COMPARISON,
    )
    parser.add_argument(
        "--cbo-4121-report",
        type=Path,
        default=DEFAULT_CBO_4121_REPORT,
    )
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pre_admissions, pre_metrics = aggregate_pre_admissions(
        args.movements_glob
    )
    base = build_classification_from_frozen(args.crosswalk_dir)
    destinations = build_destination_table(
        args.crosswalk_dir,
        pre_admissions,
    )
    variants = build_variants(base, destinations)
    comparison = comparison_table(variants)
    support = write_outputs(
        variants,
        comparison,
        destinations,
        pre_metrics,
        args.variants,
        args.comparison,
        args.cbo_4121_report,
        args.support,
    )
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
