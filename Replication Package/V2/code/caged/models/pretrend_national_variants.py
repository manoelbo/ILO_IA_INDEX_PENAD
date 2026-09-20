#!/usr/bin/env python3
"""Phase 8A national pretrend diagnostics that the V2 release never ran.

Covers three tasks that share the national panel:

- T8A.1 the January 2022 sample, with the mandatory power check that tells a
  genuine 2021 violation apart from a weaker test;
- T8A.3 the two specification-ladder steps that were estimated statically but
  never diagnosed dynamically;
- T8A.6 the wage event study restricted to CBOs with complete wage coverage.

This script diagnoses specifications. It does not choose one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent
COMMON_DIR = MODELS_DIR.parents[1] / "common"
for _directory in (MODELS_DIR, COMMON_DIR):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from merge_audit import audited_merge
from event_study import REFERENCE_EVENT_TIME
from pretrend_engine import (
    add_event_time,
    atomic_csv,
    atomic_json,
    diagnostic_row,
    fit_event_model,
    order_diagnostic_columns,
    registered_event_coefficient_frame,
    restrict_event_window,
)
from specification_ladder import data_for_step, prepare_ladder_data


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_VARIANTS = PACKAGE_ROOT / "data" / "derived" / "treatment_variants.csv"
DIAGNOSTICS_DIR = PACKAGE_ROOT / "results" / "diagnostics"
DEFAULT_SAMPLE_2022 = DIAGNOSTICS_DIR / "pretrend_sample_2022.csv"
DEFAULT_POWER_CHECK = DIAGNOSTICS_DIR / "pretrend_power_check.csv"
DEFAULT_LADDER_VARIANTS = DIAGNOSTICS_DIR / "pretrend_ladder_variants.csv"
DEFAULT_WAGE_COVERAGE = (
    DIAGNOSTICS_DIR / "pretrend_wage_balanced_coverage.csv"
)
DEFAULT_EVENT_COEFFICIENTS = (
    DIAGNOSTICS_DIR / "pretrend_national_variants_coefficients.csv"
)
DEFAULT_SUPPORT = DIAGNOSTICS_DIR / "pretrend_national_variants_support.json"
DEFAULT_FROZEN_DIAGNOSTICS = DIAGNOSTICS_DIR / "pretrend_diagnostics.csv"

OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)
FROZEN_WINDOW = (-23, 23)
EXTENDED_WINDOW = (-23, 41)
SAMPLE_2022_WINDOW = (-11, 41)
FULL_LEAD_MINIMUM = -23
MATCHED_LEAD_MINIMUM = -11
FIXED_EFFECTS = ("cbo_4d", "periodo")
CLUSTERS = ("cbo_4d",)


def _expected_event_times(minimum: int, maximum: int) -> list[int]:
    return [
        value
        for value in range(minimum, maximum + 1)
        if value != REFERENCE_EVENT_TIME
    ]


def _fit_and_diagnose(
    data: pd.DataFrame,
    *,
    outcome: str,
    estimator: str,
    interaction: str,
    window: tuple[int, int],
    lead_minimums: tuple[int, ...],
    specification_id: str,
    specification_label: str,
    sample: str,
    fixed_effects: tuple[str, ...] = FIXED_EFFECTS,
    cluster_variables: tuple[str, ...] = CLUSTERS,
    coefficient_frames: list[pd.DataFrame] | None = None,
) -> list[dict[str, Any]]:
    model, model_data, formula, cluster_counts = fit_event_model(
        data,
        outcome=outcome,
        estimator=estimator,
        interaction=interaction,
        fixed_effects=fixed_effects,
        cluster_variables=cluster_variables,
        model_id=f"{specification_id}__{outcome}",
    )
    expected = _expected_event_times(*window)
    if coefficient_frames is not None:
        model_labels = {
            "balanced_frozen_window": ("balanced", "v_a:balanced:-23_23"),
            "extended_full_sample": ("extended", "v_a:extended:-23_41"),
            "sample_2022_01": ("sample_2022", "v_a:sample_2022:-11_41"),
            "04_include_minimal_as_control": (
                "expanded_minimal",
                "expanded_minimal:event_-23_23",
            ),
            "05_continuous_exposure": (
                "continuous",
                "continuous:event_-23_23",
            ),
            "wage_complete_coverage": (
                "wage_complete_coverage",
                "v_a:wage_complete_coverage:event_-23_23",
            ),
        }
        label, registered_sample = model_labels[specification_id]
        coefficient_frames.append(
            registered_event_coefficient_frame(
                model,
                interaction,
                model_id=f"national_pretrend::{label}::{outcome}",
                outcome=outcome,
                estimator=estimator,
                sample_id=registered_sample,
                cluster_counts=cluster_counts,
                expected_event_times=expected,
            )
        )
    rows: list[dict[str, Any]] = []
    for lead_minimum in lead_minimums:
        rows.append(
            diagnostic_row(
                model=model,
                model_data=model_data,
                formula=formula,
                cluster_counts=cluster_counts,
                interaction=interaction,
                lead_minimum=lead_minimum,
                event_minimum=window[0],
                event_maximum=window[1],
                expected_event_times=expected,
                specification_id=specification_id,
                specification_label=specification_label,
                outcome=outcome,
                estimator=estimator,
                sample=sample,
            )
        )
    return rows


def run_sample_and_power(
    panel: pd.DataFrame,
    *,
    coefficient_frames: list[pd.DataFrame] | None = None,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """T8A.1: the 2022 sample beside the matched-lead power check."""

    principal = panel.loc[panel["included_main"].eq(True)].copy()
    principal = add_event_time(principal)
    frozen = restrict_event_window(principal, *FROZEN_WINDOW)
    extended = restrict_event_window(principal, *EXTENDED_WINDOW)
    sample_2022 = restrict_event_window(principal, *SAMPLE_2022_WINDOW)

    power_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    for outcome, estimator in OUTCOMES:
        power_rows.extend(
            _fit_and_diagnose(
                frozen,
                outcome=outcome,
                estimator=estimator,
                interaction="treated_main",
                window=FROZEN_WINDOW,
                lead_minimums=(FULL_LEAD_MINIMUM, MATCHED_LEAD_MINIMUM),
                specification_id="balanced_frozen_window",
                specification_label=(
                    "Full sample, frozen balanced window -23 to +23"
                ),
                sample="full_2021_01_to_2026_05",
                coefficient_frames=coefficient_frames,
            )
        )
        power_rows.extend(
            _fit_and_diagnose(
                extended,
                outcome=outcome,
                estimator=estimator,
                interaction="treated_main",
                window=EXTENDED_WINDOW,
                lead_minimums=(FULL_LEAD_MINIMUM, MATCHED_LEAD_MINIMUM),
                specification_id="extended_full_sample",
                specification_label=(
                    "Full sample, diagnostic window -23 to +41"
                ),
                sample="full_2021_01_to_2026_05",
                coefficient_frames=coefficient_frames,
            )
        )
        sample_rows.extend(
            _fit_and_diagnose(
                sample_2022,
                outcome=outcome,
                estimator=estimator,
                interaction="treated_main",
                window=SAMPLE_2022_WINDOW,
                lead_minimums=(MATCHED_LEAD_MINIMUM,),
                specification_id="sample_2022_01",
                specification_label=(
                    "Sample starts January 2022, window -11 to +41"
                ),
                sample="start_2022_01_to_2026_05",
                coefficient_frames=coefficient_frames,
            )
        )
    return (
        order_diagnostic_columns(pd.DataFrame(sample_rows)),
        order_diagnostic_columns(pd.DataFrame(power_rows)),
    )


def build_power_reading(
    sample_2022: pd.DataFrame,
    power_check: pd.DataFrame,
) -> pd.DataFrame:
    """Attach the preregistered three-cell reading to every outcome."""

    matched_full = power_check.loc[
        power_check["specification_id"].eq("extended_full_sample")
        & power_check["joint_lead_window"].eq("-11_to_-2"),
        ["outcome", "joint_lead_p_value", "pretrend_status"],
    ].rename(
        columns={
            "joint_lead_p_value": "full_sample_matched_leads_p",
            "pretrend_status": "full_sample_matched_leads_status",
        }
    )
    full_leads = power_check.loc[
        power_check["specification_id"].eq("extended_full_sample")
        & power_check["joint_lead_window"].eq("-23_to_-2"),
        ["outcome", "joint_lead_p_value"],
    ].rename(
        columns={"joint_lead_p_value": "full_sample_all_leads_p"}
    )
    frozen_leads = power_check.loc[
        power_check["specification_id"].eq("balanced_frozen_window")
        & power_check["joint_lead_window"].eq("-23_to_-2"),
        ["outcome", "joint_lead_p_value"],
    ].rename(
        columns={"joint_lead_p_value": "frozen_window_all_leads_p"}
    )
    restricted = sample_2022.loc[
        :,
        ["outcome", "joint_lead_p_value", "pretrend_status"],
    ].rename(
        columns={
            "joint_lead_p_value": "sample_2022_matched_leads_p",
            "pretrend_status": "sample_2022_matched_leads_status",
        }
    )
    reading = frozen_leads
    for label, addition in (
        ("full_leads", full_leads),
        ("matched_full_leads", matched_full),
        ("restricted_sample", restricted),
    ):
        reading = audited_merge(
            reading,
            addition,
            merge_id=f"power_reading_attach_{label}",
            on="outcome",
            validate="one_to_one",
        )

    def classify(row: pd.Series) -> str:
        full_rejects = row["full_sample_matched_leads_p"] < 0.05
        restricted_rejects = row["sample_2022_matched_leads_p"] < 0.05
        if full_rejects and not restricted_rejects:
            return "violation_concentrated_in_2021"
        if not full_rejects and not restricted_rejects:
            return "gain_is_power_not_substance"
        if full_rejects and restricted_rejects:
            return "violation_not_specific_to_2021"
        return "restricted_sample_rejects_only"

    reading["power_reading"] = reading.apply(classify, axis=1)
    reading["matched_lead_window"] = "-11_to_-2"
    reading["matched_lead_count"] = int(
        sample_2022["joint_lead_count"].iloc[0]
    )
    reading["full_lead_count"] = int(
        power_check.loc[
            power_check["joint_lead_window"].eq("-23_to_-2"),
            "joint_lead_count",
        ].iloc[0]
    )
    reading["interpretation_rule"] = (
        "The restricted-sample result may not be reported without the "
        "matched-lead full-sample cell beside it."
    )
    return reading


def run_ladder_variants(
    panel: pd.DataFrame,
    variants: pd.DataFrame,
    *,
    coefficient_frames: list[pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """T8A.3: the two estimated but never diagnosed ladder steps."""

    prepared = prepare_ladder_data(panel, variants)
    contract = (
        {
            "step_id": "04_include_minimal_as_control",
            "label": "Minimal Exposure included as control",
            "sample": "expanded_minimal",
            "interaction": "treatment",
            "start_period": 202101,
            "end_period": 202605,
        },
        {
            "step_id": "05_continuous_exposure",
            "label": "Standardized continuous exposure",
            "sample": "continuous",
            "interaction": "exposure_z",
            "start_period": 202101,
            "end_period": 202605,
        },
    )
    rows: list[dict[str, Any]] = []
    for step in contract:
        step_data = data_for_step(prepared, step)
        step_data = add_event_time(step_data)
        step_data = restrict_event_window(step_data, *FROZEN_WINDOW)
        for outcome, estimator in OUTCOMES:
            rows.extend(
                _fit_and_diagnose(
                    step_data,
                    outcome=outcome,
                    estimator=estimator,
                    interaction=step["interaction"],
                    window=FROZEN_WINDOW,
                    lead_minimums=(FULL_LEAD_MINIMUM,),
                    specification_id=step["step_id"],
                    specification_label=step["label"],
                    sample=step["sample"],
                    coefficient_frames=coefficient_frames,
                )
            )
    return order_diagnostic_columns(pd.DataFrame(rows))


def wage_coverage_sample(
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    principal = panel.loc[panel["included_main"].eq(True)].copy()
    principal = add_event_time(principal)
    window = restrict_event_window(principal, *FROZEN_WINDOW)
    months = window["event_time"].nunique()
    coverage = (
        window.assign(
            valid=window["ln_salario_real_adm"].notna().astype(int)
        )
        .groupby("cbo_4d", as_index=False)["valid"]
        .sum()
    )
    complete = coverage.loc[coverage["valid"].eq(months), "cbo_4d"]
    retained = window.loc[window["cbo_4d"].isin(complete)].copy()
    treated_retained = int(
        retained.loc[retained["treated_main"].eq(1), "cbo_4d"].nunique()
    )
    control_retained = int(
        retained.loc[retained["treated_main"].eq(0), "cbo_4d"].nunique()
    )
    metrics = {
        "window_months": int(months),
        "cbo_total": int(coverage["cbo_4d"].nunique()),
        "cbo_complete_wage_coverage": int(len(complete)),
        "cbo_dropped": int(coverage["cbo_4d"].nunique() - len(complete)),
        "treated_cbo_retained": treated_retained,
        "control_cbo_retained": control_retained,
        "cells_retained": int(len(retained)),
    }
    return retained, metrics


def run_wage_coverage(
    panel: pd.DataFrame,
    power_check: pd.DataFrame,
    *,
    coefficient_frames: list[pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """T8A.6: does unbalanced wage coverage manufacture oscillating leads?

    The unrestricted wage diagnostic travels in the same rows, so the
    comparison cannot be lost by reading one file without the other.
    """

    retained, metrics = wage_coverage_sample(panel)
    if metrics["cbo_complete_wage_coverage"] < 20:
        raise RuntimeError(
            "Complete wage coverage retains too few CBOs to diagnose"
        )
    rows = _fit_and_diagnose(
        retained,
        outcome="ln_salario_real_adm",
        estimator="ols",
        interaction="treated_main",
        window=FROZEN_WINDOW,
        lead_minimums=(FULL_LEAD_MINIMUM,),
        specification_id="wage_complete_coverage",
        specification_label=(
            "Real admission wage, CBOs with a valid wage in every month"
        ),
        sample="complete_wage_coverage",
        coefficient_frames=coefficient_frames,
    )
    unrestricted = power_check.loc[
        power_check["specification_id"].eq("balanced_frozen_window")
        & power_check["joint_lead_window"].eq("-23_to_-2")
        & power_check["outcome"].eq("ln_salario_real_adm")
    ]
    if len(unrestricted) != 1:
        raise RuntimeError(
            "The unrestricted wage diagnostic must exist exactly once"
        )
    reference = unrestricted.iloc[0]
    for row in rows:
        row.update(
            {
                "cbo_complete_wage_coverage": metrics[
                    "cbo_complete_wage_coverage"
                ],
                "cbo_dropped": metrics["cbo_dropped"],
                "treated_cbo_retained": metrics["treated_cbo_retained"],
                "control_cbo_retained": metrics["control_cbo_retained"],
                "unrestricted_joint_lead_p_value": float(
                    reference["joint_lead_p_value"]
                ),
                "unrestricted_linear_pretrend_p_value": float(
                    reference["linear_pretrend_p_value"]
                ),
                "unrestricted_dynamic_pre_p_lt_005": int(
                    reference["dynamic_pre_p_lt_005"]
                ),
                "unrestricted_pretrend_status": str(
                    reference["pretrend_status"]
                ),
                "unrestricted_n_obs": int(reference["n_obs"]),
                "coverage_resolves_pretrend": bool(
                    reference["pretrend_status"] == "fail"
                    and row["pretrend_status"] != "fail"
                ),
            }
        )
    metrics["unrestricted_joint_lead_p_value"] = float(
        reference["joint_lead_p_value"]
    )
    metrics["coverage_resolves_pretrend"] = bool(
        any(row["coverage_resolves_pretrend"] for row in rows)
    )
    return order_diagnostic_columns(pd.DataFrame(rows)), metrics


def _validate_frozen_reproduction(
    power_check: pd.DataFrame,
    frozen_path: Path,
) -> dict[str, Any]:
    """The frozen-window, all-lead cell must reproduce the released numbers."""

    if not frozen_path.is_file():
        return {"frozen_comparison": "unavailable"}
    frozen = pd.read_csv(frozen_path)
    reproduced = power_check.loc[
        power_check["specification_id"].eq("balanced_frozen_window")
        & power_check["joint_lead_window"].eq("-23_to_-2"),
        ["outcome", "joint_lead_p_value", "n_obs", "joint_lead_statistic"],
    ]
    merged = audited_merge(
        frozen[
            ["outcome", "joint_lead_p_value", "n_obs", "joint_lead_statistic"]
        ],
        reproduced,
        merge_id="pretrend_variants_compare_with_frozen",
        on="outcome",
        suffixes=("_frozen", "_rerun"),
        validate="one_to_one",
    )
    statistic_gap = float(
        (
            merged["joint_lead_statistic_frozen"]
            - merged["joint_lead_statistic_rerun"]
        )
        .abs()
        .max()
    )
    return {
        "frozen_comparison": "executed",
        "frozen_rows_matched": int(len(merged)),
        "n_obs_identical": bool(
            merged["n_obs_frozen"].eq(merged["n_obs_rerun"]).all()
        ),
        "max_absolute_joint_statistic_difference": statistic_gap,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 8A national pretrend diagnostics."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS)
    parser.add_argument(
        "--sample-2022",
        type=Path,
        default=DEFAULT_SAMPLE_2022,
    )
    parser.add_argument(
        "--power-check",
        type=Path,
        default=DEFAULT_POWER_CHECK,
    )
    parser.add_argument(
        "--ladder-variants",
        type=Path,
        default=DEFAULT_LADDER_VARIANTS,
    )
    parser.add_argument(
        "--wage-coverage",
        type=Path,
        default=DEFAULT_WAGE_COVERAGE,
    )
    parser.add_argument(
        "--event-coefficients",
        type=Path,
        default=DEFAULT_EVENT_COEFFICIENTS,
    )
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument(
        "--frozen-diagnostics",
        type=Path,
        default=DEFAULT_FROZEN_DIAGNOSTICS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    panel = pd.read_parquet(args.panel)
    variants = pd.read_csv(args.variants, dtype={"cbo_4d": str})

    coefficient_frames: list[pd.DataFrame] = []
    sample_2022, power_check = run_sample_and_power(
        panel,
        coefficient_frames=coefficient_frames,
    )
    reading = build_power_reading(sample_2022, power_check)
    sample_2022 = audited_merge(
        sample_2022,
        reading[
            [
                "outcome",
                "full_sample_matched_leads_p",
                "full_sample_matched_leads_status",
                "power_reading",
                "interpretation_rule",
            ]
        ],
        merge_id="sample_2022_attach_power_reading",
        on="outcome",
        validate="one_to_one",
    )
    atomic_csv(sample_2022, args.sample_2022)
    atomic_csv(
        audited_merge(
            power_check,
            reading[["outcome", "power_reading"]],
            merge_id="power_check_attach_power_reading",
            on="outcome",
            validate="many_to_one",
        ),
        args.power_check,
    )

    ladder = run_ladder_variants(
        panel,
        variants,
        coefficient_frames=coefficient_frames,
    )
    atomic_csv(ladder, args.ladder_variants)

    wage, wage_metrics = run_wage_coverage(
        panel,
        power_check,
        coefficient_frames=coefficient_frames,
    )
    atomic_csv(wage, args.wage_coverage)

    event_coefficients = pd.concat(coefficient_frames, ignore_index=True)
    key = ["model_id", "event_time"]
    if event_coefficients.duplicated(key).any():
        raise RuntimeError("National pretrend coefficient keys are duplicated")
    atomic_csv(
        event_coefficients.sort_values(key).reset_index(drop=True),
        args.event_coefficients,
    )

    support: dict[str, Any] = {
        "tasks": ["T8A.1", "T8A.3", "T8A.6"],
        "outcomes": [outcome for outcome, _ in OUTCOMES],
        "frozen_window": list(FROZEN_WINDOW),
        "extended_window": list(EXTENDED_WINDOW),
        "sample_2022_window": list(SAMPLE_2022_WINDOW),
        "matched_lead_window": "-11_to_-2",
        "matched_lead_count": int(sample_2022["joint_lead_count"].iloc[0]),
        "full_lead_count": int(
            power_check.loc[
                power_check["joint_lead_window"].eq("-23_to_-2"),
                "joint_lead_count",
            ].iloc[0]
        ),
        "power_reading_counts": {
            str(key): int(value)
            for key, value in reading["power_reading"]
            .value_counts()
            .sort_index()
            .items()
        },
        "wage_coverage": wage_metrics,
        "principal_specification_changed": False,
        "selection_on_pretest": False,
        **_validate_frozen_reproduction(
            power_check,
            args.frozen_diagnostics,
        ),
    }
    atomic_json(support, args.support)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
