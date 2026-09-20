#!/usr/bin/env python3
"""Estimate the extended-window event studies used in Section 5.2 figures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent
if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

from estimators import cluster_t_inference
from event_study import REFERENCE_EVENT_TIME
from pretrend_engine import (
    add_event_time,
    atomic_csv,
    atomic_json,
    atomic_text,
    event_parameter_frame,
    fit_event_model,
    restrict_event_window,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FROZEN_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_heterogeneity_ddd.parquet"
)
DEFAULT_ALTERNATIVE_PANEL = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "painel_heterogeneity_ddd_alternative_partitions.parquet"
)
OUTPUT_DIR = PACKAGE_ROOT / "results" / "models"
DEFAULT_COEFFICIENTS = OUTPUT_DIR / "group_event_study_coefficients.csv"
DEFAULT_PRE_MEANS = OUTPUT_DIR / "group_event_study_pre_means.csv"
DEFAULT_MODELS = OUTPUT_DIR / "group_event_study_models.csv"
DEFAULT_SUMMARY = OUTPUT_DIR / "group_event_study_support.json"
DEFAULT_REPORT = OUTPUT_DIR / "GROUP_EVENT_STUDIES.md"

WINDOW = (-23, 41)
FROZEN_WINDOW_MAXIMUM = 23
PRE_WINDOW = (-23, -2)
FIXED_EFFECTS = ("cbo_4d", "periodo")
CLUSTERS = ("cbo_4d",)
OUTCOMES = (
    ("admissoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
)

DIMENSIONS: dict[str, dict[str, Any]] = {
    "sex": {
        "groups": (
            ("men", "Men"),
            ("women", "Women"),
        ),
        "sources": {
            "men": ("frozen", "sex"),
            "women": ("frozen", "sex"),
        },
    },
    "race": {
        "groups": (
            ("race_white", "White"),
            ("race_negra", "Black or Pardo"),
        ),
        "sources": {
            "race_white": ("frozen", "race_color"),
            "race_negra": ("alternative", "race_aggregate"),
        },
    },
    "age": {
        "groups": (
            ("age_18_24", "Age 18–24"),
            ("age_25_34", "Age 25–34"),
            ("age_35_44", "Age 35–44"),
            ("age_45_54", "Age 45–54"),
            ("age_55_65", "Age 55–65"),
        ),
        "sources": {
            group_id: ("alternative", "age_pnad")
            for group_id in (
                "age_18_24",
                "age_25_34",
                "age_35_44",
                "age_45_54",
                "age_55_65",
            )
        },
    },
    "education": {
        "groups": (
            ("fundamental_or_less", "Primary or less"),
            ("high_school", "Secondary"),
            ("higher_education", "Higher education"),
        ),
        "sources": {
            group_id: ("frozen", "education")
            for group_id in (
                "fundamental_or_less",
                "high_school",
                "higher_education",
            )
        },
    },
    "income": {
        "groups": (
            ("low_income", "Up to 2 minimum wages"),
            ("middle_income", "Over 2 through 5 minimum wages"),
            ("high_income", "Over 5 minimum wages"),
        ),
        "sources": {
            group_id: ("frozen", "income")
            for group_id in (
                "low_income",
                "middle_income",
                "high_income",
            )
        },
    },
}


def expected_estimated_event_times() -> list[int]:
    return [
        event_time
        for event_time in range(WINDOW[0], WINDOW[1] + 1)
        if event_time != REFERENCE_EVENT_TIME
    ]


def complete_coefficient_grid(
    parameters: pd.DataFrame,
    *,
    minimum_clusters: int,
) -> pd.DataFrame:
    """Add the omitted reference and cluster-t intervals to one model."""
    observed = parameters["event_time"].astype(int).tolist()
    expected = expected_estimated_event_times()
    if observed != expected:
        raise RuntimeError(
            "Extended event-study coefficient grid is incomplete"
        )
    data = parameters.copy()
    inference = [
        cluster_t_inference(
            float(coefficient),
            float(standard_error),
            {"cbo_4d": minimum_clusters},
        )
        for coefficient, standard_error in zip(
            data["coefficient"],
            data["standard_error"],
            strict=True,
        )
    ]
    data["ci_low"] = [row["ci_low"] for row in inference]
    data["ci_high"] = [row["ci_high"] for row in inference]
    data["nominal_p_value"] = [row["p_value"] for row in inference]
    pre_mean = float(
        data.loc[
            data["event_time"].between(*PRE_WINDOW),
            "coefficient",
        ].mean()
    )
    reference = pd.DataFrame(
        [
            {
                "position": np.nan,
                "term": "reference_event_time",
                "event_time": REFERENCE_EVENT_TIME,
                "coefficient": 0.0,
                "standard_error": 0.0,
                "ci_low": 0.0,
                "ci_high": 0.0,
                "nominal_p_value": np.nan,
            }
        ]
    )
    complete = pd.concat([data, reference], ignore_index=True)
    complete = complete.sort_values("event_time").reset_index(drop=True)
    complete["is_reference"] = complete["event_time"].eq(
        REFERENCE_EVENT_TIME
    )
    complete["beyond_frozen_window"] = complete["event_time"].gt(
        FROZEN_WINDOW_MAXIMUM
    )
    complete["pre_coefficient_mean"] = pre_mean
    complete["pre_window"] = f"{PRE_WINDOW[0]}_to_{PRE_WINDOW[1]}"
    return complete


def _load_panels(
    frozen_path: Path,
    alternative_path: Path,
) -> dict[str, pd.DataFrame]:
    columns = [
        "cbo_4d",
        "periodo_num",
        "periodo",
        "subgroup",
        "dimension",
        "group_id",
        "treatment",
        *[outcome for outcome, _ in OUTCOMES],
    ]
    panels = {
        "frozen": pd.read_parquet(frozen_path, columns=columns),
        "alternative": pd.read_parquet(
            alternative_path,
            columns=columns,
        ),
    }
    selected: dict[str, pd.DataFrame] = {}
    for source, panel in panels.items():
        selected_panel = panel.loc[panel["subgroup"].eq("target")].copy()
        selected_panel = add_event_time(selected_panel)
        selected_panel = selected_panel.loc[
            selected_panel["event_time"].between(*WINDOW)
        ].copy()
        selected_panel["treatment"] = pd.to_numeric(
            selected_panel["treatment"],
            errors="raise",
        )
        selected[source] = selected_panel
    return selected


def _failure_model_row(
    labels: dict[str, Any],
    exception: Exception,
) -> dict[str, Any]:
    return {
        **labels,
        "status": "failed_estimation",
        "converged": False,
        "error": str(exception)[:800],
        "formula": "",
        "n_obs": np.nan,
        "minimum_clusters": np.nan,
        "coefficient_rows": 0,
        "pre_coefficient_mean": np.nan,
    }


def run_models(
    panels: dict[str, pd.DataFrame],
    *,
    selected_dimension: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coefficients: list[pd.DataFrame] = []
    pre_means: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    for figure_dimension, specification in DIMENSIONS.items():
        if (
            selected_dimension is not None
            and figure_dimension != selected_dimension
        ):
            continue
        for group_id, group_label in specification["groups"]:
            source, source_dimension = specification["sources"][group_id]
            sample = panels[source].loc[
                panels[source]["dimension"].eq(source_dimension)
                & panels[source]["group_id"].eq(group_id)
            ].copy()
            sample = restrict_event_window(sample, *WINDOW)
            for outcome, estimator in OUTCOMES:
                model_id = (
                    f"group_event__{figure_dimension}__"
                    f"{group_id}__{outcome}"
                )
                labels = {
                    "model_id": model_id,
                    "dimension": figure_dimension,
                    "source_dimension": source_dimension,
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": outcome,
                    "estimator": estimator,
                    "event_window": f"{WINDOW[0]}_to_{WINDOW[1]}",
                    "reference_event_time": REFERENCE_EVENT_TIME,
                    "reference_period": "2022-11",
                    "source_panel": source,
                    "is_causal_effect": False,
                }
                try:
                    model, model_data, formula, cluster_counts = (
                        fit_event_model(
                            sample,
                            outcome=outcome,
                            estimator=estimator,
                            interaction="treatment",
                            fixed_effects=FIXED_EFFECTS,
                            cluster_variables=CLUSTERS,
                            model_id=model_id,
                        )
                    )
                    minimum_clusters = int(min(cluster_counts.values()))
                    parameters = event_parameter_frame(
                        model,
                        "treatment",
                        expected_event_times=(
                            expected_estimated_event_times()
                        ),
                    )
                    complete = complete_coefficient_grid(
                        parameters,
                        minimum_clusters=minimum_clusters,
                    )
                    for key, value in labels.items():
                        complete[key] = value
                    complete["formula"] = formula
                    complete["n_obs"] = int(model._N)
                    complete["minimum_clusters"] = minimum_clusters
                    coefficients.append(complete)
                    pre_mean = float(
                        complete["pre_coefficient_mean"].iloc[0]
                    )
                    pre_means.append(
                        {
                            **labels,
                            "pre_window": (
                                f"{PRE_WINDOW[0]}_to_{PRE_WINDOW[1]}"
                            ),
                            "pre_coefficient_count": 22,
                            "pre_coefficient_mean": pre_mean,
                        }
                    )
                    model_rows.append(
                        {
                            **labels,
                            "status": "estimated",
                            "converged": True,
                            "error": "",
                            "formula": formula,
                            "n_obs": int(model._N),
                            "complete_case_input": int(len(model_data)),
                            "minimum_clusters": minimum_clusters,
                            "coefficient_rows": int(len(complete)),
                            "pre_coefficient_mean": pre_mean,
                        }
                    )
                except Exception as exception:  # noqa: BLE001
                    model_rows.append(
                        _failure_model_row(labels, exception)
                    )
                print(
                    f"[group-event] {figure_dimension}/{group_id}/{outcome} "
                    f"{model_rows[-1]['status']}",
                    flush=True,
                )
    coefficient_frame = (
        pd.concat(coefficients, ignore_index=True)
        if coefficients
        else pd.DataFrame()
    )
    return (
        coefficient_frame,
        pd.DataFrame(pre_means),
        pd.DataFrame(model_rows),
    )


def summarize(
    coefficients: pd.DataFrame,
    pre_means: pd.DataFrame,
    models: pd.DataFrame,
) -> dict[str, Any]:
    estimated = int(models["status"].eq("estimated").sum())
    expected_models = 30
    expected_coefficients = expected_models * 65
    return {
        "task": "T8B.6",
        "dimensions": len(DIMENSIONS),
        "groups": 15,
        "outcomes": 2,
        "expected_models": expected_models,
        "estimated_models": estimated,
        "failed_models": int(len(models) - estimated),
        "coefficient_rows": int(len(coefficients)),
        "expected_coefficient_rows": expected_coefficients,
        "pre_mean_rows": int(len(pre_means)),
        "event_window": f"{WINDOW[0]}_to_{WINDOW[1]}",
        "reference_event_time": REFERENCE_EVENT_TIME,
        "beyond_frozen_window_starts": FROZEN_WINDOW_MAXIMUM + 1,
        "all_models_complete": bool(
            len(models) == expected_models
            and estimated == expected_models
            and len(coefficients) == expected_coefficients
            and len(pre_means) == expected_models
        ),
        "is_causal_effect": False,
    }


def render_report(
    coefficients: pd.DataFrame,
    pre_means: pd.DataFrame,
    models: pd.DataFrame,
) -> str:
    support = summarize(coefficients, pre_means, models)
    return "\n".join(
        [
            "# Group event studies",
            "",
            "The figure inputs contain admissions (PPML) and real "
            "admission-wage (OLS) event studies for the 15 main-table "
            "groups. The monthly window is −23 through +41, with no tail "
            "binning and November 2022 as the unique omitted reference.",
            "",
            f"- Models estimated: {support['estimated_models']} / "
            f"{support['expected_models']}",
            f"- Coefficient rows: {support['coefficient_rows']} / "
            f"{support['expected_coefficient_rows']}",
            f"- Exported pre-period means: {support['pre_mean_rows']}",
            "",
            "Each model exports the mean of its 22 estimated pre-period "
            "coefficients (−23 through −2). This is the horizontal "
            "reference line required in every event-study figure. Rows "
            "after +23 are explicitly marked as beyond the frozen window.",
            "",
            "The national pretrend diagnostics fail, so these dynamic "
            "profiles are not interpreted as identified causal effects.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate extended-window event studies by group."
    )
    parser.add_argument(
        "--frozen-panel",
        type=Path,
        default=DEFAULT_FROZEN_PANEL,
    )
    parser.add_argument(
        "--alternative-panel",
        type=Path,
        default=DEFAULT_ALTERNATIVE_PANEL,
    )
    parser.add_argument(
        "--dimension",
        choices=tuple(DIMENSIONS),
        default=None,
    )
    parser.add_argument(
        "--coefficients",
        type=Path,
        default=DEFAULT_COEFFICIENTS,
    )
    parser.add_argument(
        "--pre-means",
        type=Path,
        default=DEFAULT_PRE_MEANS,
    )
    parser.add_argument("--models", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    panels = _load_panels(args.frozen_panel, args.alternative_panel)
    coefficients, pre_means, models = run_models(
        panels,
        selected_dimension=args.dimension,
    )
    atomic_csv(coefficients, args.coefficients)
    atomic_csv(pre_means, args.pre_means)
    atomic_csv(models, args.models)
    support = summarize(coefficients, pre_means, models)
    atomic_json(support, args.summary)
    atomic_text(
        render_report(coefficients, pre_means, models),
        args.report,
    )
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
