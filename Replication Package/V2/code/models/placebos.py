#!/usr/bin/env python3
"""Run the frozen national temporal and group-placebo falsifications."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from estimators import fit_model


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
)
DEFAULT_LADDER = (
    PACKAGE_ROOT / "results" / "models" / "specification_ladder.csv"
)
DEFAULT_TEMPORAL_RESULTS = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "temporal_placebo_results.csv"
)
DEFAULT_TEMPORAL_GATE = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "temporal_placebo_gate.json"
)
DEFAULT_GROUP_DISTRIBUTION = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "group_placebo_distribution.csv"
)
DEFAULT_GROUP_SUMMARY = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "group_placebo_summary.csv"
)
DEFAULT_GROUP_STATUS = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "group_placebo_status.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "diagnostics"
    / "PLACEBO_RESULTS.md"
)
DEFAULT_GROUP_PANEL_CSV = (
    PACKAGE_ROOT
    / "data"
    / "interim"
    / "placebos"
    / "national_main.csv"
)
DEFAULT_GROUP_ASSIGNMENTS = (
    PACKAGE_ROOT
    / "data"
    / "interim"
    / "placebos"
    / "group_assignments.csv"
)

TRUE_PRE_START = 202101
FALSE_EVENT_PERIOD = 202112
TRUE_PRE_END = 202211
GROUP_PLACEBO_REPETITIONS = 500
GROUP_PLACEBO_SEED = 20260726
SIGNIFICANCE_LEVEL = 0.05
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)


def _main_sample(panel: pd.DataFrame) -> pd.DataFrame:
    required = {
        "cbo_4d",
        "periodo_num",
        "periodo",
        "post",
        "treated_main",
        "included_main",
        *[outcome for outcome, _ in OUTCOMES],
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"National panel is missing columns: {missing}")
    sample = panel.loc[panel["included_main"].eq(True)].copy()
    if sample["treated_main"].isna().any():
        raise ValueError("Main sample contains missing treatment assignments")
    sample["cbo_4d"] = sample["cbo_4d"].astype(str).str.zfill(4)
    sample["treated_main"] = pd.to_numeric(
        sample["treated_main"],
        errors="raise",
    ).astype("int8")
    treated_by_cbo = sample.groupby("cbo_4d")["treated_main"].nunique()
    if not treated_by_cbo.eq(1).all():
        raise ValueError("Treatment must be time invariant within CBO4")
    return sample


def prepare_temporal_placebo(panel: pd.DataFrame) -> pd.DataFrame:
    sample = _main_sample(panel)
    sample = sample.loc[
        sample["periodo_num"].between(TRUE_PRE_START, TRUE_PRE_END)
    ].copy()
    sample["post_placebo"] = (
        sample["periodo_num"].ge(FALSE_EVENT_PERIOD).astype("int8")
    )
    sample["placebo_time_treat"] = (
        sample["post_placebo"] * sample["treated_main"]
    ).astype("int8")
    if not {0, 1}.issubset(set(sample["post_placebo"].unique())):
        raise ValueError("Temporal placebo lacks pre- or post-placebo periods")
    return sample.sort_values(["cbo_4d", "periodo_num"]).reset_index(
        drop=True
    )


def run_temporal_placebo(panel: pd.DataFrame) -> pd.DataFrame:
    sample = prepare_temporal_placebo(panel)
    rows: list[dict[str, Any]] = []
    for outcome, estimator in OUTCOMES:
        result, _ = fit_model(
            sample,
            model_id=f"temporal_placebo__{outcome}",
            outcome=outcome,
            treatment_term="placebo_time_treat",
            estimator=estimator,
            fixed_effects=("cbo_4d", "periodo"),
            cluster_variables=("cbo_4d",),
            controls=(),
            principal=True,
            separation_check=("fe",),
        )
        result.update(
            {
                "falsification": "temporal_placebo",
                "false_event_period": FALSE_EVENT_PERIOD,
                "true_pre_start": TRUE_PRE_START,
                "true_pre_end": TRUE_PRE_END,
            }
        )
        rows.append(result)
    results = pd.DataFrame(rows)
    expected = {outcome for outcome, _ in OUTCOMES}
    if set(results["outcome"]) != expected or len(results) != len(expected):
        raise RuntimeError("Temporal placebo outcome family is incomplete")
    return results


def evaluate_temporal_gate(
    results: pd.DataFrame,
) -> dict[str, Any]:
    expected = [outcome for outcome, _ in OUTCOMES]
    if results["outcome"].duplicated().any():
        raise ValueError("Temporal placebo contains duplicate outcomes")
    indexed = results.set_index("outcome")
    missing = sorted(set(expected) - set(indexed.index))
    if missing:
        raise ValueError(f"Temporal placebo is missing outcomes: {missing}")
    p_values = pd.to_numeric(
        indexed.loc[expected, "p_value"],
        errors="raise",
    )
    if p_values.isna().any():
        raise ValueError("Temporal placebo contains missing p-values")
    significant = [
        outcome
        for outcome in expected
        if float(p_values.loc[outcome]) < SIGNIFICANCE_LEVEL
    ]
    passed = not significant
    return {
        "status": "pass" if passed else "fail",
        "significance_level": SIGNIFICANCE_LEVEL,
        "decision_rule": (
            "pass only if all five national temporal-placebo "
            "p-values are at least 0.05"
        ),
        "outcome_count": len(expected),
        "significant_outcomes": significant,
        "may_proceed_to_group_placebo": passed,
        "may_proceed_to_phase_6": passed,
    }


def random_treatment_assignments(
    cbos: Sequence[str],
    *,
    treated_count: int,
    repetitions: int,
    seed: int,
) -> np.ndarray:
    ordered = np.asarray(sorted(str(cbo).zfill(4) for cbo in cbos))
    if len(np.unique(ordered)) != len(ordered):
        raise ValueError("CBO4 identifiers must be unique")
    if not 0 < treated_count < len(ordered):
        raise ValueError("Treated count must be between zero and CBO count")
    if repetitions <= 0:
        raise ValueError("Repetitions must be positive")
    rng = np.random.default_rng(seed)
    assignments = np.zeros(
        (repetitions, len(ordered)),
        dtype=np.int8,
    )
    for repetition in range(repetitions):
        selected = rng.choice(
            len(ordered),
            size=treated_count,
            replace=False,
        )
        assignments[repetition, selected] = 1
    return assignments


def summarize_randomization_distribution(
    *,
    observed_coefficient: float,
    placebo_coefficients: np.ndarray,
) -> dict[str, float | int]:
    coefficients = np.asarray(placebo_coefficients, dtype=float)
    if coefficients.ndim != 1 or not len(coefficients):
        raise ValueError("Placebo coefficients must be a nonempty vector")
    if not np.isfinite(coefficients).all():
        raise ValueError("Placebo coefficients must all be finite")
    repetitions = len(coefficients)
    percentile = 100.0 * float(
        np.mean(coefficients <= observed_coefficient)
    )
    extreme = int(
        np.sum(
            np.abs(coefficients) >= abs(observed_coefficient)
        )
    )
    return {
        "observed_coefficient": float(observed_coefficient),
        "observed_percentile": percentile,
        "empirical_two_sided_p_value": (
            (extreme + 1.0) / (repetitions + 1.0)
        ),
        "repetitions": repetitions,
        "placebo_mean": float(np.mean(coefficients)),
        "placebo_standard_deviation": float(
            np.std(coefficients, ddof=1)
        ),
        "placebo_p025": float(np.quantile(coefficients, 0.025)),
        "placebo_p975": float(np.quantile(coefficients, 0.975)),
    }


def two_way_residualize(
    values: np.ndarray,
    row_codes: np.ndarray,
    column_codes: np.ndarray,
    *,
    tolerance: float = 1e-12,
    maximum_iterations: int = 10_000,
) -> np.ndarray:
    residual = np.asarray(values, dtype=float).copy()
    rows = np.asarray(row_codes, dtype=int)
    columns = np.asarray(column_codes, dtype=int)
    if residual.ndim != 1 or not (
        len(residual) == len(rows) == len(columns)
    ):
        raise ValueError("Two-way residualization inputs must align")
    if not np.isfinite(residual).all():
        raise ValueError("Two-way residualization requires finite values")
    row_count = np.bincount(rows)
    column_count = np.bincount(columns)
    if (row_count == 0).any() or (column_count == 0).any():
        raise ValueError("Fixed-effect codes must be contiguous")
    for _ in range(maximum_iterations):
        previous = residual.copy()
        row_sum = np.bincount(rows, weights=residual)
        residual -= row_sum[rows] / row_count[rows]
        column_sum = np.bincount(columns, weights=residual)
        residual -= column_sum[columns] / column_count[columns]
        if np.max(np.abs(residual - previous)) < tolerance:
            return residual
    raise RuntimeError("Two-way residualization did not converge")


def ppml_two_way_coefficient(
    outcome: np.ndarray,
    mask: np.ndarray,
    *,
    treatment: np.ndarray,
    post: np.ndarray,
    tolerance: float = 1e-11,
) -> float:
    values = np.asarray(outcome, dtype=float)
    observed = np.asarray(mask, dtype=bool)
    treated = np.asarray(treatment, dtype=float)
    post_period = np.asarray(post, dtype=float)
    if values.shape != observed.shape:
        raise ValueError("PPML outcome and observation mask must align")
    if values.shape != (len(treated), len(post_period)):
        raise ValueError("PPML treatment and post vectors do not align")
    if not np.isfinite(values[observed]).all():
        raise ValueError("PPML outcome must be finite on observed cells")
    if (values[observed] < 0).any():
        raise ValueError("PPML outcome must be weakly positive")
    if not np.all(values[~observed] == 0):
        raise ValueError("Unobserved PPML cells must be zero-filled")

    row_margin = values.sum(axis=1)
    column_margin = values.sum(axis=0)
    if (row_margin <= 0).any() or (column_margin <= 0).any():
        raise ValueError(
            "PPML lightweight backend requires positive FE margins"
        )
    interaction = treated[:, None] * post_period[None, :]
    observed_interaction_sum = float(
        np.sum(values * interaction)
    )
    total = float(values.sum())

    def score(coefficient: float) -> float:
        weighted_mask = (
            np.exp(coefficient * interaction) * observed
        )
        row_effect = np.ones(len(treated), dtype=float)
        column_effect = np.ones(len(post_period), dtype=float)
        for _ in range(10_000):
            previous = row_effect.copy()
            row_denominator = (
                weighted_mask * column_effect[None, :]
            ).sum(axis=1)
            row_effect = row_margin / row_denominator
            column_denominator = (
                weighted_mask * row_effect[:, None]
            ).sum(axis=0)
            column_effect = column_margin / column_denominator
            relative_change = np.max(
                np.abs(row_effect - previous)
                / (1.0 + np.abs(previous))
            )
            if relative_change < tolerance:
                break
        else:
            raise RuntimeError("PPML margin fitting did not converge")
        fitted = (
            row_effect[:, None]
            * column_effect[None, :]
            * weighted_mask
        )
        return observed_interaction_sum - float(
            np.sum(fitted * interaction)
        )

    lower = -2.0
    upper = 2.0
    lower_score = score(lower)
    upper_score = score(upper)
    while lower_score < 0:
        lower *= 2.0
        lower_score = score(lower)
    while upper_score > 0:
        upper *= 2.0
        upper_score = score(upper)
    for _ in range(80):
        midpoint = (lower + upper) / 2.0
        midpoint_score = score(midpoint)
        if (
            abs(midpoint_score) <= tolerance * max(total, 1.0)
            or upper - lower <= tolerance
        ):
            return midpoint
        if midpoint_score > 0:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def export_group_placebo_inputs(
    panel: pd.DataFrame,
    *,
    panel_path: Path,
    assignments_path: Path,
    repetitions: int = GROUP_PLACEBO_REPETITIONS,
    seed: int = GROUP_PLACEBO_SEED,
) -> dict[str, Any]:
    sample = _main_sample(panel)
    cbo_treatment = (
        sample[["cbo_4d", "treated_main"]]
        .drop_duplicates()
        .sort_values("cbo_4d")
        .reset_index(drop=True)
    )
    cbos = cbo_treatment["cbo_4d"].tolist()
    treated_count = int(cbo_treatment["treated_main"].sum())
    assignments = random_treatment_assignments(
        cbos,
        treated_count=treated_count,
        repetitions=repetitions,
        seed=seed,
    )
    assignment_frame = pd.DataFrame(
        {
            "repetition": np.repeat(
                np.arange(1, repetitions + 1),
                len(cbos),
            ),
            "seed": seed,
            "cbo_4d": np.tile(cbos, repetitions),
            "assigned": assignments.reshape(-1),
        }
    )
    panel_columns = [
        "cbo_4d",
        "periodo_num",
        "periodo",
        "post",
        *[outcome for outcome, _ in OUTCOMES],
    ]
    exported_panel = (
        sample[panel_columns]
        .sort_values(["cbo_4d", "periodo_num"])
        .reset_index(drop=True)
    )
    _atomic_csv(exported_panel, panel_path)
    _atomic_csv(assignment_frame, assignments_path)
    return {
        "seed": seed,
        "repetitions": repetitions,
        "panel_rows": int(len(exported_panel)),
        "cbo_count": len(cbos),
        "treated_cbo_count": treated_count,
        "control_cbo_count": len(cbos) - treated_count,
        "assignment_rows": int(len(assignment_frame)),
        "all_assignments_preserve_treated_count": bool(
            np.all(assignments.sum(axis=1) == treated_count)
        ),
    }


def _principal_observed_coefficients(
    ladder: pd.DataFrame,
) -> dict[str, float]:
    principal = ladder.loc[
        ladder["step_id"].eq("01_no_controls")
    ].copy()
    expected = [outcome for outcome, _ in OUTCOMES]
    if principal["outcome"].duplicated().any():
        raise ValueError("Principal ladder contains duplicate outcomes")
    principal = principal.set_index("outcome")
    missing = sorted(set(expected) - set(principal.index))
    if missing:
        raise ValueError(
            f"Principal ladder is missing outcomes: {missing}"
        )
    return {
        outcome: float(principal.loc[outcome, "coefficient"])
        for outcome in expected
    }


def run_group_placebo_reference(
    panel: pd.DataFrame,
    ladder: pd.DataFrame,
    *,
    repetitions: int = GROUP_PLACEBO_REPETITIONS,
    seed: int = GROUP_PLACEBO_SEED,
    checkpoint_path: Path | None = None,
    progress_every: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    sample = _main_sample(panel)
    cbo_treatment = (
        sample[["cbo_4d", "treated_main"]]
        .drop_duplicates()
        .sort_values("cbo_4d")
        .reset_index(drop=True)
    )
    cbos = cbo_treatment["cbo_4d"].tolist()
    treated_count = int(cbo_treatment["treated_main"].sum())
    assignments = random_treatment_assignments(
        cbos,
        treated_count=treated_count,
        repetitions=repetitions,
        seed=seed,
    )
    observed = _principal_observed_coefficients(ladder)
    cbo_positions = {cbo: position for position, cbo in enumerate(cbos)}
    row_positions = sample["cbo_4d"].map(cbo_positions).to_numpy()

    rows: list[dict[str, Any]] = []
    completed_repetitions: set[int] = set()
    if checkpoint_path is not None and checkpoint_path.exists():
        checkpoint = pd.read_csv(checkpoint_path)
        required = {
            "repetition",
            "seed",
            "outcome",
            "estimator",
            "coefficient",
        }
        missing = sorted(required - set(checkpoint.columns))
        if missing:
            raise ValueError(
                f"Group-placebo checkpoint is missing columns: {missing}"
            )
        if not checkpoint["seed"].eq(seed).all():
            raise ValueError("Group-placebo checkpoint seed mismatch")
        expected_outcomes = {outcome for outcome, _ in OUTCOMES}
        for repetition, group in checkpoint.groupby("repetition"):
            if (
                len(group) != len(expected_outcomes)
                or set(group["outcome"]) != expected_outcomes
            ):
                raise ValueError(
                    "Group-placebo checkpoint contains a partial repetition"
                )
            completed_repetitions.add(int(repetition))
        rows.extend(checkpoint.to_dict("records"))
        if completed_repetitions:
            print(
                "Resuming group placebo after "
                f"{max(completed_repetitions)} completed repetitions.",
                flush=True,
            )
    for repetition in range(repetitions):
        repetition_number = repetition + 1
        if repetition_number in completed_repetitions:
            continue
        assigned = assignments[repetition, row_positions]
        sample["placebo_group_treat"] = (
            sample["post"].to_numpy(dtype=np.int8) * assigned
        )
        for outcome, estimator in OUTCOMES:
            result, _ = fit_model(
                sample,
                model_id=(
                    f"group_placebo_{repetition + 1:03d}__{outcome}"
                ),
                outcome=outcome,
                treatment_term="placebo_group_treat",
                estimator=estimator,
                fixed_effects=("cbo_4d", "periodo"),
                cluster_variables=("cbo_4d",),
                controls=(),
                principal=True,
                separation_check=("fe",),
            )
            rows.append(
                {
                    "repetition": repetition + 1,
                    "seed": seed,
                    "outcome": outcome,
                    "estimator": estimator,
                    "coefficient": result["coefficient"],
                    "n_obs": result["n_obs"],
                    "n_clusters": result["minimum_clusters"],
                    "treated_cbo_count": treated_count,
                    "control_cbo_count": len(cbos) - treated_count,
                }
            )
        if (
            checkpoint_path is not None
            and (
                repetition_number % progress_every == 0
                or repetition_number == repetitions
            )
        ):
            checkpoint_frame = (
                pd.DataFrame(rows)
                .sort_values(["repetition", "outcome"])
                .reset_index(drop=True)
            )
            _atomic_csv(checkpoint_frame, checkpoint_path)
            print(
                "Group placebo progress: "
                f"{repetition_number}/{repetitions} repetitions.",
                flush=True,
            )
    distribution = (
        pd.DataFrame(rows)
        .sort_values(["repetition", "outcome"])
        .reset_index(drop=True)
    )
    expected_rows = repetitions * len(OUTCOMES)
    if len(distribution) != expected_rows:
        raise RuntimeError("Group-placebo distribution is incomplete")

    summaries: list[dict[str, Any]] = []
    for outcome, estimator in OUTCOMES:
        coefficients = distribution.loc[
            distribution["outcome"].eq(outcome),
            "coefficient",
        ].to_numpy()
        summary = summarize_randomization_distribution(
            observed_coefficient=observed[outcome],
            placebo_coefficients=coefficients,
        )
        summary.update(
            {
                "outcome": outcome,
                "estimator": estimator,
                "seed": seed,
                "treated_cbo_count": treated_count,
                "control_cbo_count": len(cbos) - treated_count,
            }
        )
        summaries.append(summary)
    summary_frame = pd.DataFrame(summaries)
    status = {
        "status": "completed",
        "seed": seed,
        "repetitions": repetitions,
        "outcomes": len(OUTCOMES),
        "model_count": expected_rows,
        "treated_cbo_count": treated_count,
        "control_cbo_count": len(cbos) - treated_count,
        "all_assignments_preserve_treated_count": bool(
            np.all(assignments.sum(axis=1) == treated_count)
        ),
    }
    return distribution, summary_frame, status


def run_group_placebo(
    panel: pd.DataFrame,
    ladder: pd.DataFrame,
    *,
    repetitions: int = GROUP_PLACEBO_REPETITIONS,
    seed: int = GROUP_PLACEBO_SEED,
    checkpoint_path: Path | None = None,
    progress_every: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    sample = _main_sample(panel).sort_values(
        ["cbo_4d", "periodo_num"]
    ).reset_index(drop=True)
    cbos = sorted(sample["cbo_4d"].unique())
    periods = sorted(sample["periodo"].unique())
    cbo_lookup = {cbo: index for index, cbo in enumerate(cbos)}
    period_lookup = {
        period: index for index, period in enumerate(periods)
    }
    row_codes = sample["cbo_4d"].map(cbo_lookup).to_numpy(dtype=int)
    column_codes = sample["periodo"].map(period_lookup).to_numpy(
        dtype=int
    )
    shape = (len(cbos), len(periods))
    mask = np.zeros(shape, dtype=bool)
    mask[row_codes, column_codes] = True
    if int(mask.sum()) != len(sample):
        raise ValueError("National panel contains duplicate CBO-month cells")

    treatment_by_cbo = (
        sample[["cbo_4d", "treated_main"]]
        .drop_duplicates()
        .set_index("cbo_4d")
        .loc[cbos, "treated_main"]
        .to_numpy(dtype=np.int8)
    )
    treated_count = int(treatment_by_cbo.sum())
    assignments = random_treatment_assignments(
        cbos,
        treated_count=treated_count,
        repetitions=repetitions,
        seed=seed,
    )
    post_by_period = (
        sample[["periodo", "post"]]
        .drop_duplicates()
        .set_index("periodo")
        .loc[periods, "post"]
        .to_numpy(dtype=np.int8)
    )
    if not set(np.unique(post_by_period)) <= {0, 1}:
        raise ValueError("Post indicator must be binary by month")

    count_contexts: dict[str, np.ndarray] = {}
    for outcome, estimator in OUTCOMES:
        if estimator != "ppml":
            continue
        matrix = np.zeros(shape, dtype=float)
        matrix[row_codes, column_codes] = sample[outcome].to_numpy(
            dtype=float
        )
        count_contexts[outcome] = matrix

    linear_contexts: dict[str, dict[str, np.ndarray | int]] = {}
    for outcome, estimator in OUTCOMES:
        if estimator != "ols":
            continue
        valid = sample[outcome].notna().to_numpy()
        valid_rows = row_codes[valid]
        valid_columns = column_codes[valid]
        outcome_residual = two_way_residualize(
            sample.loc[valid, outcome].to_numpy(dtype=float),
            valid_rows,
            valid_columns,
        )
        linear_contexts[outcome] = {
            "row_codes": valid_rows,
            "column_codes": valid_columns,
            "post": sample.loc[valid, "post"].to_numpy(dtype=np.int8),
            "outcome_residual": outcome_residual,
            "n_obs": int(valid.sum()),
        }

    rows: list[dict[str, Any]] = []
    completed_repetitions: set[int] = set()
    if checkpoint_path is not None and checkpoint_path.exists():
        checkpoint = pd.read_csv(checkpoint_path)
        required = {
            "repetition",
            "seed",
            "outcome",
            "estimator",
            "coefficient",
        }
        missing = sorted(required - set(checkpoint.columns))
        if missing:
            raise ValueError(
                f"Group-placebo checkpoint is missing columns: {missing}"
            )
        if not checkpoint["seed"].eq(seed).all():
            raise ValueError("Group-placebo checkpoint seed mismatch")
        expected_outcomes = {outcome for outcome, _ in OUTCOMES}
        for repetition, group in checkpoint.groupby("repetition"):
            if (
                len(group) != len(expected_outcomes)
                or set(group["outcome"]) != expected_outcomes
            ):
                raise ValueError(
                    "Group-placebo checkpoint contains a partial repetition"
                )
            completed_repetitions.add(int(repetition))
        rows.extend(checkpoint.to_dict("records"))
        if completed_repetitions:
            print(
                "Resuming group placebo after "
                f"{max(completed_repetitions)} completed repetitions.",
                flush=True,
            )

    for repetition in range(repetitions):
        repetition_number = repetition + 1
        if repetition_number in completed_repetitions:
            continue
        assigned = assignments[repetition]
        for outcome, estimator in OUTCOMES:
            if estimator == "ppml":
                coefficient = ppml_two_way_coefficient(
                    count_contexts[outcome],
                    mask,
                    treatment=assigned,
                    post=post_by_period,
                )
                n_obs = len(sample)
            else:
                context = linear_contexts[outcome]
                valid_rows = context["row_codes"]
                valid_columns = context["column_codes"]
                raw_treatment = (
                    assigned[valid_rows] * context["post"]
                )
                treatment_residual = two_way_residualize(
                    raw_treatment,
                    valid_rows,
                    valid_columns,
                )
                denominator = float(
                    treatment_residual @ treatment_residual
                )
                if denominator <= 0:
                    raise RuntimeError(
                        "Random assignment has no residual treatment "
                        f"variation in repetition {repetition_number}"
                    )
                coefficient = float(
                    treatment_residual
                    @ context["outcome_residual"]
                    / denominator
                )
                n_obs = int(context["n_obs"])
            rows.append(
                {
                    "repetition": repetition_number,
                    "seed": seed,
                    "outcome": outcome,
                    "estimator": estimator,
                    "coefficient": coefficient,
                    "n_obs": n_obs,
                    "n_clusters": len(cbos),
                    "treated_cbo_count": treated_count,
                    "control_cbo_count": len(cbos) - treated_count,
                }
            )
        if (
            checkpoint_path is not None
            and (
                repetition_number % progress_every == 0
                or repetition_number == repetitions
            )
        ):
            checkpoint_frame = (
                pd.DataFrame(rows)
                .sort_values(["repetition", "outcome"])
                .reset_index(drop=True)
            )
            _atomic_csv(checkpoint_frame, checkpoint_path)
            print(
                "Group placebo progress: "
                f"{repetition_number}/{repetitions} repetitions.",
                flush=True,
            )

    distribution = (
        pd.DataFrame(rows)
        .sort_values(["repetition", "outcome"])
        .reset_index(drop=True)
    )
    expected_rows = repetitions * len(OUTCOMES)
    if len(distribution) != expected_rows:
        raise RuntimeError("Group-placebo distribution is incomplete")
    observed = _principal_observed_coefficients(ladder)
    summaries: list[dict[str, Any]] = []
    for outcome, estimator in OUTCOMES:
        coefficients = distribution.loc[
            distribution["outcome"].eq(outcome),
            "coefficient",
        ].to_numpy()
        summary = summarize_randomization_distribution(
            observed_coefficient=observed[outcome],
            placebo_coefficients=coefficients,
        )
        summary.update(
            {
                "outcome": outcome,
                "estimator": estimator,
                "seed": seed,
                "treated_cbo_count": treated_count,
                "control_cbo_count": len(cbos) - treated_count,
            }
        )
        summaries.append(summary)
    summary_frame = pd.DataFrame(summaries)
    status = {
        "status": "completed",
        "backend": "ppml_ipf_and_ols_fwl",
        "seed": seed,
        "repetitions": repetitions,
        "outcomes": len(OUTCOMES),
        "model_count": expected_rows,
        "treated_cbo_count": treated_count,
        "control_cbo_count": len(cbos) - treated_count,
        "all_assignments_preserve_treated_count": bool(
            np.all(assignments.sum(axis=1) == treated_count)
        ),
    }
    return distribution, summary_frame, status


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_report(
    temporal: pd.DataFrame,
    gate: dict[str, Any],
    group_summary: pd.DataFrame | None,
    group_status: dict[str, Any],
    path: Path,
) -> None:
    lines = [
        "# Task 22 placebo falsifications",
        "",
        "## Frozen contract",
        "",
        (
            "The temporal placebo assigns a false event in December 2021 "
            "and uses only the true pre-treatment sample from January 2021 "
            "through November 2022. The exact national estimator family is "
            "retained without contemporary controls."
        ),
        "",
        "## Temporal placebo",
        "",
        "| Outcome | Estimator | Coefficient | SE | p-value | Gate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in temporal.itertuples(index=False):
        status = (
            "FAIL"
            if float(row.p_value) < SIGNIFICANCE_LEVEL
            else "PASS"
        )
        lines.append(
            f"| {row.outcome} | {row.estimator} | "
            f"{row.coefficient:.6f} | {row.standard_error:.6f} | "
            f"{row.p_value:.6g} | {status} |"
        )
    lines.extend(
        [
            "",
            f"**Checkpoint F temporal gate: {gate['status'].upper()}.**",
            "",
        ]
    )
    if gate["status"] == "fail":
        failed = ", ".join(gate["significant_outcomes"])
        lines.extend(
            [
                (
                    "At least one national temporal placebo is significant "
                    f"at 5% ({failed}). Under the frozen stopping rule, the "
                    "group placebo and Phase 6 are **NOT EXECUTED**. No "
                    "specification is changed in response."
                ),
                "",
            ]
        )
    elif group_summary is not None:
        lines.extend(
            [
                "## Group placebo",
                "",
                (
                    f"Exactly 75 of 341 CBO4 families were reassigned in "
                    f"each of {group_status['repetitions']} repetitions "
                    f"with seed {group_status['seed']}."
                ),
                "",
                (
                    "The randomization coefficients use the algebraically "
                    "equivalent PPML margin-fitting and OLS FWL backend. "
                    "The first assignment is reconciled against the shared "
                    "reference estimator in "
                    "`group_placebo_backend_validation.csv`."
                ),
                "",
                (
                    "| Outcome | Observed coefficient | Observed percentile "
                    "| Two-sided randomization p |"
                ),
                "|---|---:|---:|---:|",
            ]
        )
        for row in group_summary.itertuples(index=False):
            lines.append(
                f"| {row.outcome} | {row.observed_coefficient:.6f} | "
                f"{row.observed_percentile:.2f} | "
                f"{row.empirical_two_sided_p_value:.6f} |"
            )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the frozen Task 22 placebo falsifications."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--ladder", type=Path, default=DEFAULT_LADDER)
    parser.add_argument(
        "--temporal-results",
        type=Path,
        default=DEFAULT_TEMPORAL_RESULTS,
    )
    parser.add_argument(
        "--temporal-gate",
        type=Path,
        default=DEFAULT_TEMPORAL_GATE,
    )
    parser.add_argument(
        "--group-distribution",
        type=Path,
        default=DEFAULT_GROUP_DISTRIBUTION,
    )
    parser.add_argument(
        "--group-summary",
        type=Path,
        default=DEFAULT_GROUP_SUMMARY,
    )
    parser.add_argument(
        "--group-status",
        type=Path,
        default=DEFAULT_GROUP_STATUS,
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--group-panel-csv",
        type=Path,
        default=DEFAULT_GROUP_PANEL_CSV,
    )
    parser.add_argument(
        "--group-assignments",
        type=Path,
        default=DEFAULT_GROUP_ASSIGNMENTS,
    )
    parser.add_argument(
        "--export-group-inputs",
        action="store_true",
        help="Freeze the 500 group assignments and R-compatible panel.",
    )
    parser.add_argument(
        "--temporal-only",
        action="store_true",
        help="Run and evaluate only the blocking temporal placebo.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    panel = pd.read_parquet(args.panel)
    if args.export_group_inputs:
        support = export_group_placebo_inputs(
            panel,
            panel_path=args.group_panel_csv,
            assignments_path=args.group_assignments,
        )
        print(json.dumps(support, sort_keys=True))
        return 0
    temporal = run_temporal_placebo(panel)
    gate = evaluate_temporal_gate(temporal)
    _atomic_csv(temporal, args.temporal_results)
    _atomic_json(gate, args.temporal_gate)

    if gate["status"] == "fail":
        group_status = {
            "status": "not_executed_gate_failed",
            "reason": (
                "The national temporal placebo is significant at 5%; "
                "the frozen Checkpoint F stopping rule applies."
            ),
            "significant_outcomes": gate["significant_outcomes"],
            "planned_repetitions": GROUP_PLACEBO_REPETITIONS,
            "seed": GROUP_PLACEBO_SEED,
        }
        _atomic_json(group_status, args.group_status)
        _write_report(
            temporal,
            gate,
            None,
            group_status,
            args.report,
        )
        print(json.dumps({"gate": gate, "group": group_status}))
        return 2

    if args.temporal_only:
        group_status = {
            "status": "not_executed_temporal_only",
            "reason": "Temporal-only execution was requested.",
            "planned_repetitions": GROUP_PLACEBO_REPETITIONS,
            "seed": GROUP_PLACEBO_SEED,
        }
        _atomic_json(group_status, args.group_status)
        _write_report(
            temporal,
            gate,
            None,
            group_status,
            args.report,
        )
        print(json.dumps({"gate": gate, "group": group_status}))
        return 0

    distribution, group_summary, group_status = run_group_placebo(
        panel,
        pd.read_csv(args.ladder),
        checkpoint_path=args.group_distribution,
    )
    _atomic_csv(distribution, args.group_distribution)
    _atomic_csv(group_summary, args.group_summary)
    _atomic_json(group_status, args.group_status)
    _write_report(
        temporal,
        gate,
        group_summary,
        group_status,
        args.report,
    )
    print(json.dumps({"gate": gate, "group": group_status}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
