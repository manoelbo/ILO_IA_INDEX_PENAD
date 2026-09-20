#!/usr/bin/env python3
"""T8A.7: estimate the four preregistered long-run horizons.

`results/models/long_run_horizons.csv` shipped as a period-to-horizon mapping
with no coefficient in it. The frozen contract asked for horizon estimates, so
this script produces them.

They matter more than a missing table usually would. The balanced event study
stops at November 2024 (`t = +23`) while the static coefficient runs to May
2026 (`t = +41`). For the real admission wage the mean of the visible post
coefficients is far smaller than the static estimate, and the last visible
coefficients are close to zero. If the wage effect is concentrated after
November 2024 — the window V1 did not have — only horizon estimates make that
visible.

One model per outcome carries all four horizon interactions at once, with the
pre-period as the omitted base, so the horizons are mutually exclusive and
jointly exhaustive of the post period.
"""

from __future__ import annotations

import argparse
import json
import math
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
from estimators import cluster_t_inference
from event_study import build_horizon_grid, horizon_name
from pretrend_engine import add_event_time, atomic_csv, atomic_json, atomic_text


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
MODELS_RESULTS = PACKAGE_ROOT / "results" / "models"
DEFAULT_LADDER = MODELS_RESULTS / "specification_ladder.csv"
DEFAULT_OUTPUT = MODELS_RESULTS / "long_run_horizon_estimates.csv"
DEFAULT_RECONCILIATION = MODELS_RESULTS / "long_run_horizon_reconciliation.csv"
DEFAULT_REPORT = MODELS_RESULTS / "LONG_RUN_HORIZONS.md"
DEFAULT_SUPPORT = MODELS_RESULTS / "long_run_horizons_support.json"

OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)
HORIZONS = (
    ("2022-12_to_2023-11", "h1", False),
    ("2023-12_to_2024-11", "h2", False),
    ("2024-12_to_2025-11", "h3", False),
    ("2025-12_to_cutoff", "h4", True),
)
FIXED_EFFECTS = ("cbo_4d", "periodo")
CLUSTERS = ("cbo_4d",)


def horizon_terms() -> tuple[str, ...]:
    return tuple(f"{key}_treat" for _, key, _ in HORIZONS)


def prepare(panel: pd.DataFrame) -> pd.DataFrame:
    data = panel.loc[panel["included_main"].eq(True)].copy()
    data = add_event_time(data)
    data["horizon"] = [
        horizon_name(int(value))[0] for value in data["event_time"]
    ]
    data["treated_main"] = pd.to_numeric(
        data["treated_main"],
        errors="raise",
    ).astype(float)
    for horizon, key, _ in HORIZONS:
        data[f"{key}"] = (
            data["horizon"].eq(horizon).astype(float)
        )
        data[f"{key}_treat"] = data[key] * data["treated_main"]
    post_flag = data["horizon"].notna().astype(int)
    if not post_flag.equals(
        pd.to_numeric(data["post"], errors="raise").astype(int)
    ):
        raise RuntimeError(
            "Horizon assignment does not partition the frozen post indicator"
        )
    return data


def estimate_horizons(data: pd.DataFrame) -> pd.DataFrame:
    import pyfixest as pf

    terms = horizon_terms()
    rows: list[dict[str, Any]] = []
    for outcome, estimator in OUTCOMES:
        required = [outcome, *terms, *FIXED_EFFECTS, *CLUSTERS]
        model_data = data.dropna(
            subset=list(dict.fromkeys(required))
        ).copy()
        formula = (
            f"{outcome} ~ " + " + ".join(terms) + " | " + " + ".join(
                FIXED_EFFECTS
            )
        )
        vcov = {"CRV1": " + ".join(CLUSTERS)}
        if estimator == "ppml":
            model = pf.fepois(
                formula,
                data=model_data,
                vcov=vcov,
                separation_check=["fe"],
            )
            if not bool(getattr(model, "_convergence", False)):
                raise RuntimeError(
                    f"Horizon PPML did not converge: {outcome}"
                )
        else:
            model = pf.feols(formula, data=model_data, vcov=vcov)
        used = getattr(model, "_data", model_data)
        cluster_counts = {
            variable: int(used[variable].nunique())
            for variable in CLUSTERS
        }
        tidy = model.tidy()
        # `model._data` keeps only the formula variables, so the horizon
        # indicators are recovered from the retained month labels.
        period_to_horizon = (
            model_data.drop_duplicates("periodo")
            .set_index("periodo")["horizon"]
        )
        used_horizon = used["periodo"].map(period_to_horizon)
        used_periods = used["periodo"]
        for horizon, key, partial in HORIZONS:
            term = f"{key}_treat"
            if term not in tidy.index:
                raise RuntimeError(f"Horizon term missing: {term}")
            coefficient = float(tidy.loc[term, "Estimate"])
            standard_error = float(tidy.loc[term, "Std. Error"])
            inference = cluster_t_inference(
                coefficient,
                standard_error,
                cluster_counts,
            )
            in_horizon = used_horizon.eq(horizon)
            horizon_cells = int(in_horizon.sum())
            rows.append(
                {
                    "outcome": outcome,
                    "estimator": estimator,
                    "horizon": horizon,
                    "horizon_key": key,
                    "partial_horizon": partial,
                    "term": term,
                    "coefficient": coefficient,
                    "standard_error": standard_error,
                    "ci_low": inference["ci_low"],
                    "ci_high": inference["ci_high"],
                    "p_value": inference["p_value"],
                    "cluster_df": inference["cluster_df"],
                    "n_obs": int(model._N),
                    "n_clusters": cluster_counts["cbo_4d"],
                    "horizon_cells": horizon_cells,
                    "horizon_months": int(
                        used_periods.loc[in_horizon].nunique()
                    ),
                    "effect_percent": (
                        100.0 * math.expm1(coefficient)
                        if estimator == "ppml"
                        else np.nan
                    ),
                    "formula": formula,
                    "fixed_effects": " + ".join(FIXED_EFFECTS),
                    "cluster_variables": " + ".join(CLUSTERS),
                    "converged": True,
                }
            )
    return pd.DataFrame(rows)


def reconcile(
    horizons: pd.DataFrame,
    ladder_path: Path,
) -> pd.DataFrame:
    ladder = pd.read_csv(ladder_path)
    static = ladder.loc[
        ladder["step_id"].eq("01_no_controls"),
        ["outcome", "coefficient", "standard_error", "p_value", "n_obs"],
    ].rename(
        columns={
            "coefficient": "static_coefficient",
            "standard_error": "static_standard_error",
            "p_value": "static_p_value",
            "n_obs": "static_n_obs",
        }
    )
    weighted = (
        horizons.assign(
            weight_numerator=horizons["horizon_cells"],
        )
        .groupby("outcome")
        .apply(
            lambda group: pd.Series(
                {
                    "cell_weighted_horizon_average": float(
                        np.average(
                            group["coefficient"],
                            weights=group["horizon_cells"],
                        )
                    ),
                    "unweighted_horizon_average": float(
                        group["coefficient"].mean()
                    ),
                    "complete_horizon_average": float(
                        np.average(
                            group.loc[
                                ~group["partial_horizon"],
                                "coefficient",
                            ],
                            weights=group.loc[
                                ~group["partial_horizon"],
                                "horizon_cells",
                            ],
                        )
                    ),
                    "first_horizon": float(
                        group.loc[
                            group["horizon_key"].eq("h1"),
                            "coefficient",
                        ].item()
                    ),
                    "last_horizon": float(
                        group.loc[
                            group["horizon_key"].eq("h4"),
                            "coefficient",
                        ].item()
                    ),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    comparison = audited_merge(
        static,
        weighted,
        merge_id="long_run_horizons_attach_static",
        on="outcome",
        validate="one_to_one",
    )
    comparison["static_minus_cell_weighted_average"] = (
        comparison["static_coefficient"]
        - comparison["cell_weighted_horizon_average"]
    )
    comparison["last_minus_first_horizon"] = (
        comparison["last_horizon"] - comparison["first_horizon"]
    )
    comparison["effect_grows_over_horizons"] = (
        comparison["last_horizon"].abs()
        > comparison["first_horizon"].abs()
    )
    return comparison


def render_report(
    horizons: pd.DataFrame,
    comparison: pd.DataFrame,
) -> str:
    lines = [
        "# Long-run horizon estimates",
        "",
        "All four horizons are estimated inside one model per outcome, with "
        "the pre-period as the omitted base, the principal estimator, CBO4 "
        "and month fixed effects, and CBO4-clustered inference. The horizons "
        "partition the frozen post indicator exactly.",
        "",
        "The fourth horizon covers December 2025 through the May 2026 cutoff "
        "and is six months rather than twelve. It is marked partial "
        "everywhere it appears.",
        "",
        "| Outcome | Horizon | Months | Coefficient | SE | p | Partial |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in horizons.itertuples(index=False):
        lines.append(
            f"| {row.outcome} | {row.horizon} | {row.horizon_months} | "
            f"{row.coefficient:+.6f} | {row.standard_error:.6f} | "
            f"{row.p_value:.6g} | {'yes' if row.partial_horizon else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Reconciliation with the static coefficient",
            "",
            "The static estimate is a single average over the whole post "
            "period. Under PPML the horizon coefficients do not have to "
            "average exactly to it, because the estimator is non-linear; the "
            "cell-weighted average is reported so the size of the gap is "
            "visible rather than assumed away.",
            "",
            "| Outcome | Static | Cell-weighted horizons | Difference | "
            "First horizon | Last horizon | Last − first |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in comparison.itertuples(index=False):
        lines.append(
            f"| {row.outcome} | {row.static_coefficient:+.6f} | "
            f"{row.cell_weighted_horizon_average:+.6f} | "
            f"{row.static_minus_cell_weighted_average:+.6f} | "
            f"{row.first_horizon:+.6f} | {row.last_horizon:+.6f} | "
            f"{row.last_minus_first_horizon:+.6f} |"
        )
    lines.extend(
        [
            "",
            "These are horizon-specific treated-versus-control differences "
            "under the frozen exposure design. Every event-study "
            "specification in this package fails its joint pretrend "
            "diagnostic, so a growing horizon profile is not by itself "
            "evidence of a growing causal effect.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate the four preregistered long-run horizons."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--ladder", type=Path, default=DEFAULT_LADDER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--reconciliation",
        type=Path,
        default=DEFAULT_RECONCILIATION,
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = prepare(pd.read_parquet(args.panel))
    horizons = estimate_horizons(data)
    comparison = reconcile(horizons, args.ladder)
    atomic_csv(horizons, args.output)
    atomic_csv(comparison, args.reconciliation)
    atomic_text(render_report(horizons, comparison), args.report)
    grid = build_horizon_grid()
    support = {
        "task": "T8A.7",
        "horizons": [horizon for horizon, _, _ in HORIZONS],
        "partial_horizon": "2025-12_to_cutoff",
        "outcomes": [outcome for outcome, _ in OUTCOMES],
        "estimate_rows": int(len(horizons)),
        "horizon_grid_months": int(len(grid)),
        "horizon_months": {
            str(key): int(value)
            for key, value in horizons.drop_duplicates("horizon")
            .set_index("horizon")["horizon_months"]
            .items()
        },
        "max_absolute_static_minus_horizon_average": float(
            comparison["static_minus_cell_weighted_average"].abs().max()
        ),
        "all_models_converged": bool(horizons["converged"].all()),
        "estimator_matches_principal": True,
        "inference_matches_principal": "CRV1 cbo_4d with cluster-t",
    }
    atomic_json(support, args.support)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
