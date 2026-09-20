#!/usr/bin/env python3
"""T8A.4: DDD pretrends, per-group pretrends, and per-group power.

The V1 appendix tables carried three diagnostic columns that the V2 release
dropped: `Pretrend grupo`, `Pretrend DDD`, and `Poder grupo`. This script
restores all three.

The triple-difference identifying assumption is different from, and weaker
than, the difference-in-differences one: it requires the *difference between
groups* to have evolved in parallel across exposed and unexposed occupations.
A violation that hits treated and control occupations equally within every
demographic group is differenced out. So the DDD contrasts can survive a
pretrend test that the national DiD fails, and whether they do is a finding in
its own right.

The dynamic triple difference uses the saturated form
`cbo_4d^subgroup + periodo^subgroup + periodo^treatment`, which absorbs every
lower-order dynamic term and leaves the triple interaction as the only
dynamic parameter. The lower-order-term requirement is preserved in
`RESEARCH_DESIGN.md` and the typed model contracts.

The per-group static DiD is estimated here only to obtain the standard error
that the minimum detectable effect needs. It carries
`interpretation = diagnostic_only` and is not multiplicity adjusted; the
per-group heterogeneity table belongs to Phase 8B.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent
COMMON_DIR = MODELS_DIR.parents[1] / "common"
for _directory in (MODELS_DIR, COMMON_DIR):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from merge_audit import audited_merge
from estimators import fit_model
from event_study import REFERENCE_EVENT_TIME
from heterogeneity import (
    ALTERNATIVE_DIMENSIONS,
    ALTERNATIVE_FAMILY_SIZE,
    DIMENSIONS,
    OUTCOMES,
    PLANNED_FAMILY_SIZE,
)
from pretrend_engine import (
    add_event_time,
    atomic_csv,
    atomic_json,
    atomic_text,
    diagnose_event_model,
    fit_event_model,
    minimum_detectable_effect,
    registered_event_coefficient_frame,
    restrict_event_window,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_heterogeneity_ddd.parquet"
)
DIAGNOSTICS_DIR = PACKAGE_ROOT / "results" / "diagnostics"
DEFAULT_DDD_RESULTS = DIAGNOSTICS_DIR / "ddd_multiplicity_results.csv"
DEFAULT_OUTPUT = DIAGNOSTICS_DIR / "ddd_pretrends.csv"
DEFAULT_EVENT_COEFFICIENTS = DIAGNOSTICS_DIR / "ddd_pretrends_coefficients.csv"
DEFAULT_SUPPORT = DIAGNOSTICS_DIR / "ddd_pretrends_support.json"
DEFAULT_NATIONAL_DIAGNOSTICS = DIAGNOSTICS_DIR / "pretrend_diagnostics.csv"
DEFAULT_ALTERNATIVE_PANEL = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "painel_heterogeneity_ddd_alternative_partitions.parquet"
)
DEFAULT_ALTERNATIVE_DDD_RESULTS = (
    DIAGNOSTICS_DIR / "ddd_alternative_partitions.csv"
)
DEFAULT_ALTERNATIVE_OUTPUT = (
    DIAGNOSTICS_DIR / "ddd_alternative_partitions_pretrends.csv"
)
DEFAULT_ALTERNATIVE_EVENT_COEFFICIENTS = (
    DIAGNOSTICS_DIR
    / "ddd_alternative_partitions_pretrends_coefficients.csv"
)
DEFAULT_ALTERNATIVE_SUPPORT = (
    DIAGNOSTICS_DIR / "ddd_alternative_partitions_pretrends_support.json"
)
DEFAULT_ALTERNATIVE_REPORT = (
    DIAGNOSTICS_DIR / "DDD_ALTERNATIVE_PARTITIONS_PRETRENDS.md"
)

WINDOW = (-23, 23)
LEAD_MINIMUM = -23
DDD_FIXED_EFFECTS = (
    "cbo_4d^subgroup",
    "periodo^subgroup",
    "periodo^treatment",
)
GROUP_FIXED_EFFECTS = ("cbo_4d", "periodo")
CLUSTERS = ("cbo_4d",)


def diagnostic_configuration(family_id: str) -> dict[str, Any]:
    if family_id == "A":
        return {
            "family_id": "A",
            "family_size": PLANNED_FAMILY_SIZE,
            "dimensions": DIMENSIONS,
            "panel": DEFAULT_PANEL,
            "ddd_results": DEFAULT_DDD_RESULTS,
            "output": DEFAULT_OUTPUT,
            "event_coefficients": DEFAULT_EVENT_COEFFICIENTS,
            "support": DEFAULT_SUPPORT,
        }
    if family_id == "B":
        return {
            "family_id": "B",
            "family_size": ALTERNATIVE_FAMILY_SIZE,
            "dimensions": ALTERNATIVE_DIMENSIONS,
            "panel": DEFAULT_ALTERNATIVE_PANEL,
            "ddd_results": DEFAULT_ALTERNATIVE_DDD_RESULTS,
            "output": DEFAULT_ALTERNATIVE_OUTPUT,
            "event_coefficients": DEFAULT_ALTERNATIVE_EVENT_COEFFICIENTS,
            "support": DEFAULT_ALTERNATIVE_SUPPORT,
        }
    raise ValueError(f"Unknown diagnostic family: {family_id}")


def expected_event_times() -> list[int]:
    return [
        value
        for value in range(WINDOW[0], WINDOW[1] + 1)
        if value != REFERENCE_EVENT_TIME
    ]


def load_panel(path: Path) -> pd.DataFrame:
    data = pd.read_parquet(path)
    data = add_event_time(data)
    data = data.loc[
        data["event_time"].between(*WINDOW)
    ].copy()
    data["treatment"] = pd.to_numeric(data["treatment"], errors="raise")
    data["group_indicator"] = pd.to_numeric(
        data["group_indicator"],
        errors="raise",
    )
    data["treat_group"] = pd.to_numeric(
        data["treat_group"],
        errors="raise",
    ).astype(float)
    return data


def _failure_row(reason: str, error: str) -> dict[str, Any]:
    return {
        "status": reason,
        "error": error[:400],
        "joint_lead_p_value": np.nan,
        "joint_lead_statistic": np.nan,
        "joint_lead_count": np.nan,
        "lead_covariance_positive_semidefinite": np.nan,
        "lead_covariance_min_eigenvalue": np.nan,
        "lead_covariance_dimension": np.nan,
        "lead_covariance_rank": np.nan,
        "lead_covariance_full_rank": np.nan,
        "lead_covariance_condition_number": np.nan,
        "lead_covariance_rank_tolerance": np.nan,
        "lead_covariance_psd_tolerance": np.nan,
        "linear_pretrend_coefficient": np.nan,
        "linear_pretrend_standard_error": np.nan,
        "linear_pretrend_p_value": np.nan,
        "dynamic_pre_p_lt_005": np.nan,
        "dynamic_min_p_value": np.nan,
        "pretrend_status": "not_estimated",
        "n_obs": np.nan,
        "minimum_clusters": np.nan,
    }


def _diagnose(
    sample: pd.DataFrame,
    *,
    outcome: str,
    estimator: str,
    interaction: str,
    fixed_effects: tuple[str, ...],
    model_id: str,
    registered_model_id: str,
    sample_id: str,
) -> tuple[dict[str, Any], pd.DataFrame | None]:
    try:
        model, model_data, formula, cluster_counts = fit_event_model(
            sample,
            outcome=outcome,
            estimator=estimator,
            interaction=interaction,
            fixed_effects=fixed_effects,
            cluster_variables=CLUSTERS,
            model_id=model_id,
        )
        diagnostics = diagnose_event_model(
            model,
            interaction=interaction,
            cluster_counts=cluster_counts,
            lead_minimum=LEAD_MINIMUM,
            expected_event_times=expected_event_times(),
        )
    except Exception as exception:  # noqa: BLE001
        return _failure_row("failed_estimation", str(exception)), None
    coefficients = registered_event_coefficient_frame(
        model,
        interaction,
        model_id=registered_model_id,
        outcome=outcome,
        estimator=estimator,
        sample_id=sample_id,
        cluster_counts=cluster_counts,
        expected_event_times=expected_event_times(),
    )
    result = {
        "status": "estimated",
        "error": "",
        "joint_lead_p_value": diagnostics["joint_lead_p_value"],
        "joint_lead_statistic": diagnostics["joint_lead_statistic"],
        "joint_lead_count": diagnostics["joint_lead_count"],
        "lead_covariance_positive_semidefinite": diagnostics[
            "lead_covariance_positive_semidefinite"
        ],
        "lead_covariance_min_eigenvalue": diagnostics[
            "lead_covariance_min_eigenvalue"
        ],
        "lead_covariance_dimension": diagnostics[
            "lead_covariance_dimension"
        ],
        "lead_covariance_rank": diagnostics["lead_covariance_rank"],
        "lead_covariance_full_rank": diagnostics[
            "lead_covariance_full_rank"
        ],
        "lead_covariance_condition_number": diagnostics[
            "lead_covariance_condition_number"
        ],
        "lead_covariance_rank_tolerance": diagnostics[
            "lead_covariance_rank_tolerance"
        ],
        "lead_covariance_psd_tolerance": diagnostics[
            "lead_covariance_psd_tolerance"
        ],
        "linear_pretrend_coefficient": diagnostics[
            "linear_pretrend_coefficient"
        ],
        "linear_pretrend_standard_error": diagnostics[
            "linear_pretrend_standard_error"
        ],
        "linear_pretrend_p_value": diagnostics["linear_pretrend_p_value"],
        "dynamic_pre_p_lt_005": diagnostics["dynamic_pre_p_lt_005"],
        "dynamic_min_p_value": diagnostics["dynamic_min_p_value"],
        "pretrend_status": diagnostics["pretrend_status"],
        "n_obs": int(model._N),
        "minimum_clusters": int(min(cluster_counts.values())),
        "formula": formula,
    }
    return result, coefficients


def _static_group_did(
    target: pd.DataFrame,
    *,
    outcome: str,
    estimator: str,
    model_id: str,
) -> dict[str, Any]:
    try:
        result, _ = fit_model(
            target,
            model_id=model_id,
            outcome=outcome,
            treatment_term="post_treat",
            estimator=estimator,
            fixed_effects=GROUP_FIXED_EFFECTS,
            cluster_variables=CLUSTERS,
            principal=False,
            separation_check=("fe",),
        )
    except Exception as exception:  # noqa: BLE001
        return {
            "group_did_status": "failed_estimation",
            "group_did_error": str(exception)[:400],
            "group_did_coefficient": np.nan,
            "group_did_standard_error": np.nan,
            "group_did_p_value": np.nan,
            "group_did_n_obs": np.nan,
            "group_did_clusters": np.nan,
            "group_mde_80_power": np.nan,
        }
    return {
        "group_did_status": "estimated",
        "group_did_error": "",
        "group_did_coefficient": result["coefficient"],
        "group_did_standard_error": result["standard_error"],
        "group_did_p_value": result["p_value"],
        "group_did_n_obs": result["n_obs"],
        "group_did_clusters": result["minimum_clusters"],
        "group_mde_80_power": minimum_detectable_effect(
            result["standard_error"],
            int(result["cluster_df"]),
        ),
    }


def run_group(
    panel: pd.DataFrame,
    dimension: str,
    specification: dict[str, Any],
    group_id: str,
    group_label: str,
    *,
    family_id: str,
    coefficient_frames: list[pd.DataFrame] | None = None,
) -> list[dict[str, Any]]:
    sample = panel.loc[
        panel["dimension"].eq(dimension)
        & panel["group_id"].eq(group_id)
    ].copy()
    sample = restrict_event_window(sample, *WINDOW)
    target = sample.loc[sample["subgroup"].eq("target")].copy()
    rows: list[dict[str, Any]] = []
    for outcome, estimator in OUTCOMES:
        base = {
            "dimension": dimension,
            "dimension_kind": specification["kind"],
            "group_id": group_id,
            "group_label": group_label,
            "outcome": outcome,
            "estimator": estimator,
            "event_window": f"{WINDOW[0]}_to_{WINDOW[1]}",
            "lead_window": "-23_to_-2",
            "reference_event_time": REFERENCE_EVENT_TIME,
            "reference_period": "2022-11",
            "multiplicity_adjusted": False,
            "interpretation": "diagnostic_only",
        }
        ddd, ddd_coefficients = _diagnose(
            sample,
            outcome=outcome,
            estimator=estimator,
            interaction="treat_group",
            fixed_effects=DDD_FIXED_EFFECTS,
            model_id=f"ddd_pretrend__{dimension}__{group_id}__{outcome}",
            registered_model_id=(
                f"ddd_pretrend::{family_id}::{dimension}::{group_id}::"
                f"{outcome}"
            ),
            sample_id=f"family_{family_id}:{dimension}:{group_id}",
        )
        group, group_coefficients = _diagnose(
            target,
            outcome=outcome,
            estimator=estimator,
            interaction="treatment",
            fixed_effects=GROUP_FIXED_EFFECTS,
            model_id=f"group_pretrend__{dimension}__{group_id}__{outcome}",
            registered_model_id=(
                f"group_pretrend::{family_id}::{dimension}::{group_id}::"
                f"{outcome}"
            ),
            sample_id=(
                f"family_{family_id}_target:{dimension}:{group_id}"
            ),
        )
        if coefficient_frames is not None:
            for coefficient_frame in (ddd_coefficients, group_coefficients):
                if coefficient_frame is not None:
                    coefficient_frames.append(coefficient_frame)
        static = _static_group_did(
            target,
            outcome=outcome,
            estimator=estimator,
            model_id=f"group_did__{dimension}__{group_id}__{outcome}",
        )
        row = {**base}
        row.update(
            {f"ddd_{key}": value for key, value in ddd.items()}
        )
        row.update(
            {f"group_pretrend_{key}": value for key, value in group.items()}
        )
        row.update(static)
        rows.append(row)
        print(
            f"[ddd-pretrend] {dimension}/{group_id}/{outcome} "
            f"ddd={row['ddd_pretrend_status']} "
            f"group={row['group_pretrend_pretrend_status']}",
            flush=True,
        )
    return rows


def attach_ddd_power(
    frame: pd.DataFrame,
    ddd_results_path: Path,
) -> pd.DataFrame:
    if not ddd_results_path.is_file():
        raise FileNotFoundError(
            f"DDD coefficient table is required: {ddd_results_path}"
        )
    published = pd.read_csv(ddd_results_path)
    keep = published[
        [
            "dimension",
            "group_id",
            "outcome",
            "coefficient",
            "standard_error",
            "cluster_df",
            "nominal_p_value",
            "bh_adjusted_p_value",
            "support_status",
        ]
    ].rename(
        columns={
            "coefficient": "ddd_coefficient",
            "standard_error": "ddd_standard_error",
            "cluster_df": "ddd_cluster_df",
            "nominal_p_value": "ddd_nominal_p_value",
            "bh_adjusted_p_value": "ddd_bh_adjusted_p_value",
        }
    )
    merged = audited_merge(
        frame,
        keep,
        merge_id="ddd_pretrends_attach_published_coefficients",
        on=["dimension", "group_id", "outcome"],
        how="left",
        validate="one_to_one",
    )
    merged["ddd_mde_80_power"] = [
        minimum_detectable_effect(
            standard_error,
            int(cluster_df) if np.isfinite(cluster_df) else 0,
        )
        if np.isfinite(standard_error) and np.isfinite(cluster_df)
        else np.nan
        for standard_error, cluster_df in zip(
            merged["ddd_standard_error"],
            merged["ddd_cluster_df"],
            strict=True,
        )
    ]
    return merged


def summarize(
    frame: pd.DataFrame,
    national_path: Path,
    *,
    family_id: str,
    family_size: int,
) -> dict[str, Any]:
    estimated_ddd = frame.loc[frame["ddd_status"].eq("estimated")]
    estimated_group = frame.loc[
        frame["group_pretrend_status"].eq("estimated")
    ]
    national_fail = None
    if national_path.is_file():
        national = pd.read_csv(national_path)
        national_fail = int(
            national["pretrend_status"].eq("fail").sum()
        )
    return {
        "task": "T8A.4" if family_id == "A" else "T8B.5",
        "family_id": family_id,
        "family_size": family_size,
        "contrasts": int(len(frame)),
        "ddd_estimated": int(len(estimated_ddd)),
        "ddd_failed": int(len(frame) - len(estimated_ddd)),
        "group_pretrend_estimated": int(len(estimated_group)),
        "ddd_pretrend_status_counts": {
            str(key): int(value)
            for key, value in frame["ddd_pretrend_status"]
            .value_counts()
            .sort_index()
            .items()
        },
        "group_pretrend_status_counts": {
            str(key): int(value)
            for key, value in frame["group_pretrend_pretrend_status"]
            .value_counts()
            .sort_index()
            .items()
        },
        "ddd_pass_or_warning": int(
            estimated_ddd["ddd_pretrend_status"]
            .isin(["pass", "warning"])
            .sum()
        ),
        "group_pass_or_warning": int(
            estimated_group["group_pretrend_pretrend_status"]
            .isin(["pass", "warning"])
            .sum()
        ),
        "national_outcomes_failing_pretrend": national_fail,
        "national_outcome_count": 5,
        "ddd_fixed_effects": list(DDD_FIXED_EFFECTS),
        "group_fixed_effects": list(GROUP_FIXED_EFFECTS),
        "per_group_did_is_diagnostic_only": True,
        "multiplicity_adjusted": False,
        "principal_specification_changed": False,
    }


def _format_number(value: Any, digits: int = 4) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def render_alternative_age_comparison(
    alternative: pd.DataFrame,
    frozen: pd.DataFrame,
) -> str:
    """Render the PNAD/IBGE and Canaries young-age partitions together."""
    partition_specs = (
        (
            alternative,
            "age_pnad",
            "age_18_24",
            "PNAD/IBGE 18–24",
        ),
        (
            frozen,
            "age_canaries",
            "age_22_25",
            "Canaries 22–25",
        ),
    )
    comparison_rows: list[dict[str, Any]] = []
    for frame, dimension, group_id, partition_label in partition_specs:
        selected = frame.loc[
            frame["dimension"].eq(dimension)
            & frame["group_id"].eq(group_id)
        ].copy()
        if len(selected) != len(OUTCOMES):
            raise ValueError(
                f"{partition_label} must have {len(OUTCOMES)} outcomes; "
                f"found {len(selected)}"
            )
        for row in selected.to_dict("records"):
            comparison_rows.append(
                {
                    "partition": partition_label,
                    "group_id": group_id,
                    **row,
                }
            )

    lines = [
        "# Alternative-partition pretrend diagnostics",
        "",
        "Family B contains 30 DDD contrasts: the five PNAD/IBGE age "
        "bands and the aggregate Negra category, each evaluated for five "
        "outcomes. The saturated dynamic DDD absorbs "
        "`cbo_4d^subgroup`, `periodo^subgroup`, and "
        "`periodo^treatment`.",
        "",
        "The table below places two different young-age partitions in "
        "the same frame. They overlap but are not interchangeable: "
        "PNAD/IBGE uses ages 18–24, whereas Canaries uses ages 22–25.",
        "",
        "| Partition | group_id | Outcome | DDD coefficient | Family DDD "
        "BH p | Group pretrend | DDD pretrend | Group MDE (80%) |",
        "|---|---|---|---:|---:|---|---|---:|",
    ]
    for row in comparison_rows:
        lines.append(
            "| {partition} | `{group_id}` | `{outcome}` | {coefficient} | "
            "{bh_p} | {group_pretrend} | {ddd_pretrend} | {mde} |".format(
                partition=row["partition"],
                group_id=row["group_id"],
                outcome=row["outcome"],
                coefficient=_format_number(row["ddd_coefficient"]),
                bh_p=_format_number(row["ddd_bh_adjusted_p_value"]),
                group_pretrend=row["group_pretrend_pretrend_status"],
                ddd_pretrend=row["ddd_pretrend_status"],
                mde=_format_number(row["group_mde_80_power"]),
            )
        )
    lines.extend(
        [
            "",
            "A non-rejection in either diagnostic is not evidence that "
            "parallel trends holds. The national diagnostics fail in all "
            "available cells, so these results are not presented as "
            "causal effects.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run DDD and per-group pretrend diagnostics."
    )
    parser.add_argument(
        "--family-id",
        choices=("A", "B"),
        default="A",
    )
    parser.add_argument("--panel", type=Path)
    parser.add_argument(
        "--ddd-results",
        type=Path,
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--event-coefficients", type=Path)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--national-diagnostics",
        type=Path,
        default=DEFAULT_NATIONAL_DIAGNOSTICS,
    )
    parser.add_argument("--dimension", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configuration = diagnostic_configuration(args.family_id)
    dimensions = configuration["dimensions"]
    panel_path = args.panel or configuration["panel"]
    ddd_results_path = (
        args.ddd_results or configuration["ddd_results"]
    )
    output_path = args.output or configuration["output"]
    event_coefficients_path = (
        args.event_coefficients or configuration["event_coefficients"]
    )
    support_path = args.support or configuration["support"]
    report_path = args.report or (
        DEFAULT_ALTERNATIVE_REPORT
        if args.family_id == "B"
        else None
    )
    panel = load_panel(panel_path)
    rows: list[dict[str, Any]] = []
    coefficient_frames: list[pd.DataFrame] = []
    for dimension, specification in dimensions.items():
        if args.dimension and dimension != args.dimension:
            continue
        for group_id, group_label in specification["groups"]:
            rows.extend(
                run_group(
                    panel,
                    dimension,
                    specification,
                    group_id,
                    group_label,
                    family_id=configuration["family_id"],
                    coefficient_frames=coefficient_frames,
                )
            )
    frame = pd.DataFrame(rows)
    frame = attach_ddd_power(frame, ddd_results_path)
    frame["family_id"] = configuration["family_id"]
    frame["family_size"] = configuration["family_size"]
    atomic_csv(frame, output_path)
    event_coefficients = pd.concat(coefficient_frames, ignore_index=True)
    key = ["model_id", "event_time"]
    if event_coefficients.duplicated(key).any():
        raise RuntimeError("DDD pretrend coefficient keys are duplicated")
    atomic_csv(
        event_coefficients.sort_values(key).reset_index(drop=True),
        event_coefficients_path,
    )
    support = summarize(
        frame,
        args.national_diagnostics,
        family_id=configuration["family_id"],
        family_size=configuration["family_size"],
    )
    atomic_json(support, support_path)
    if report_path is not None:
        frozen = pd.read_csv(DEFAULT_OUTPUT)
        atomic_text(
            render_alternative_age_comparison(frame, frozen),
            report_path,
        )
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
