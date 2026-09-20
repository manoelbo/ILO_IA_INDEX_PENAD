#!/usr/bin/env python3
"""T8A.5: difference-in-differences that controls for the pre-trend.

Humlum and Vestergaard (2025) hit the same problem — occupational trends that
predate the chatbots — and answered it by controlling for those trends inside
the difference-in-differences, reporting that "because these trends entirely
predate AI chatbots, the pooled difference-in-differences (which control for
pre-trends) are precise zeros".

Two implementations are reported side by side, and both are robustness:

- `predetermined_pretrend_control` estimates one linear slope per CBO **using
  the pre-period only** and enters the predetermined path as a regressor. It
  cannot use post-period information to fit the trend;
- `differential_linear_trend` adds a treated-versus-control linear trend
  estimated over the whole sample. This is the specification the GLS linear
  pretrend test points at directly: if the differential trend really is
  linear, this removes it.

The plan also contemplated CBO-specific varying slopes. `pyfixest` does not
implement them: the `fe[var]` syntax is not parsed as a varying slope, it is
handed to `formulaic`, which evaluates `cbo_4d[event_time]` as a pandas
lookup. On this panel that raises; on a panel with integer keys it would
silently produce a meaningless regressor. The public design contract records
the resulting two-specification robustness role in `RESEARCH_DESIGN.md`.

Caveat, recorded before estimation and repeated in the output: a linear trend
extrapolated across 42 post-treatment months can absorb part of a genuinely
gradual diffusion effect. `differential_linear_trend` is more exposed to this
than the predetermined form, because it fits the slope using post-period data
too. In Humlum's case the specification produced precise zeros rather than a
manufactured effect, but the risk runs in both directions and neither form may
be read as a principal estimate.
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
from event_study import REFERENCE_EVENT_TIME
from pretrend_engine import add_event_time, atomic_csv, atomic_json, atomic_text


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
MODELS_RESULTS = PACKAGE_ROOT / "results" / "models"
DEFAULT_OUTPUT = MODELS_RESULTS / "pretrend_control_specification.csv"
DEFAULT_REPORT = MODELS_RESULTS / "PRETREND_CONTROL_SPECIFICATION.md"
DEFAULT_SUPPORT = MODELS_RESULTS / "pretrend_control_support.json"
DEFAULT_SLOPES = (
    PACKAGE_ROOT / "results" / "diagnostics" / "cbo_pre_period_slopes.csv"
)

OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)
PRE_END_PERIOD = 202211
FIXED_EFFECTS = ("cbo_4d", "periodo")
CLUSTERS = ("cbo_4d",)
MINIMUM_PRE_OBSERVATIONS = 6
SPECIFICATIONS = (
    {
        "specification_id": "00_no_trend_control",
        "label": "Principal specification, no trend control",
        "causal_role": "principal_reference_only",
    },
    {
        "specification_id": "01_predetermined_pretrend_control",
        "label": "Predetermined pre-period CBO slope as a control",
        "causal_role": "robustness",
    },
    {
        "specification_id": "02_differential_linear_trend",
        "label": "Treated-versus-control linear trend on the full sample",
        "causal_role": "robustness",
    },
)


def _trend_scale(outcome: str, estimator: str) -> str:
    """The scale on which the pre-period slope is measured.

    Count outcomes enter the model through a log link, so their trend is
    extracted on `log(1 + y)`; the linear outcomes are already on the model's
    own scale.
    """

    return "log1p" if estimator == "ppml" else "level"


def estimate_pre_slopes(
    data: pd.DataFrame,
    outcome: str,
    estimator: str,
) -> pd.DataFrame:
    scale = _trend_scale(outcome, estimator)
    pre = data.loc[
        data["periodo_num"].le(PRE_END_PERIOD)
        & data[outcome].notna()
    ].copy()
    pre["trend_value"] = (
        np.log1p(pre[outcome]) if scale == "log1p" else pre[outcome]
    )
    records: list[dict[str, Any]] = []
    for cbo_4d, group in pre.groupby("cbo_4d", sort=True):
        times = group["event_time"].to_numpy(dtype=float)
        values = group["trend_value"].to_numpy(dtype=float)
        if len(group) < MINIMUM_PRE_OBSERVATIONS or np.ptp(times) == 0:
            slope = 0.0
            status = "insufficient_pre_observations"
        else:
            centred = times - times.mean()
            denominator = float(centred @ centred)
            slope = float(centred @ (values - values.mean()) / denominator)
            status = "estimated"
        records.append(
            {
                "cbo_4d": cbo_4d,
                "outcome": outcome,
                "trend_scale": scale,
                "pre_observations": int(len(group)),
                "pre_slope": slope,
                "slope_status": status,
            }
        )
    return pd.DataFrame(records)


def prepare(panel: pd.DataFrame) -> pd.DataFrame:
    data = panel.loc[panel["included_main"].eq(True)].copy()
    data = add_event_time(data)
    data["treated_main"] = pd.to_numeric(
        data["treated_main"],
        errors="raise",
    ).astype(float)
    data["post_treat"] = (
        pd.to_numeric(data["post"], errors="raise").astype(float)
        * data["treated_main"]
    )
    data["trend_time"] = (
        data["event_time"].astype(float) - float(REFERENCE_EVENT_TIME)
    )
    data["treated_trend_time"] = data["treated_main"] * data["trend_time"]
    return data


def _fit(
    model_data: pd.DataFrame,
    *,
    outcome: str,
    estimator: str,
    controls: tuple[str, ...],
    fixed_effects: tuple[str, ...],
    model_id: str,
) -> dict[str, Any]:
    import pyfixest as pf

    right_hand_side = " + ".join(["post_treat", *controls])
    formula = (
        f"{outcome} ~ {right_hand_side} | " + " + ".join(fixed_effects)
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
            raise RuntimeError(f"PPML did not converge: {model_id}")
    else:
        model = pf.feols(formula, data=model_data, vcov=vcov)
    used = getattr(model, "_data", model_data)
    cluster_counts = {
        variable: int(used[variable].nunique()) for variable in CLUSTERS
    }
    tidy = model.tidy()
    coefficient = float(tidy.loc["post_treat", "Estimate"])
    standard_error = float(tidy.loc["post_treat", "Std. Error"])
    inference = cluster_t_inference(
        coefficient,
        standard_error,
        cluster_counts,
    )
    return {
        "model_id": model_id,
        "outcome": outcome,
        "estimator": estimator,
        "term": "post_treat",
        "coefficient": coefficient,
        "standard_error": standard_error,
        "ci_low": inference["ci_low"],
        "ci_high": inference["ci_high"],
        "p_value": inference["p_value"],
        "cluster_df": inference["cluster_df"],
        "n_obs": int(model._N),
        "n_clusters": cluster_counts["cbo_4d"],
        "formula": formula,
        "controls": " + ".join(controls),
        "fixed_effects": " + ".join(fixed_effects),
        "effect_percent": (
            100.0 * math.expm1(coefficient)
            if estimator == "ppml"
            else np.nan
        ),
        "converged": True,
    }


def run(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    slope_frames: list[pd.DataFrame] = []
    for outcome, estimator in OUTCOMES:
        slopes = estimate_pre_slopes(data, outcome, estimator)
        slope_frames.append(slopes)
        model_data = audited_merge(
            data,
            slopes[["cbo_4d", "pre_slope"]],
            merge_id=f"pretrend_control_attach_pre_slope__{outcome}",
            on="cbo_4d",
            how="left",
            validate="many_to_one",
        )
        model_data["pre_slope"] = model_data["pre_slope"].fillna(0.0)
        model_data["predetermined_pretrend"] = (
            model_data["pre_slope"] * model_data["trend_time"]
        )
        required = [
            outcome,
            "post_treat",
            "predetermined_pretrend",
            "treated_trend_time",
            "event_time",
            *FIXED_EFFECTS,
            *CLUSTERS,
        ]
        model_data = model_data.dropna(
            subset=list(dict.fromkeys(required))
        ).copy()
        for specification in SPECIFICATIONS:
            specification_id = specification["specification_id"]
            if specification_id == "00_no_trend_control":
                controls: tuple[str, ...] = ()
            elif specification_id == "01_predetermined_pretrend_control":
                controls = ("predetermined_pretrend",)
            else:
                controls = ("treated_trend_time",)
            result = _fit(
                model_data,
                outcome=outcome,
                estimator=estimator,
                controls=controls,
                fixed_effects=FIXED_EFFECTS,
                model_id=f"{specification_id}__{outcome}",
            )
            result.update(
                {
                    "specification_id": specification_id,
                    "specification_label": specification["label"],
                    "causal_role": specification["causal_role"],
                    "trend_scale": _trend_scale(outcome, estimator),
                    "pre_slope_source": (
                        "pre_period_only"
                        if specification_id
                        == "01_predetermined_pretrend_control"
                        else (
                            "full_sample_differential_trend"
                            if specification_id
                            == "02_differential_linear_trend"
                            else "none"
                        )
                    ),
                    "may_absorb_gradual_diffusion": specification_id
                    != "00_no_trend_control",
                }
            )
            rows.append(result)
            print(
                f"[pretrend-control] {specification_id} {outcome} "
                f"coef={result['coefficient']:+.6f} "
                f"p={result['p_value']:.6g}",
                flush=True,
            )
    results = pd.DataFrame(rows)
    baseline = results.loc[
        results["specification_id"].eq("00_no_trend_control"),
        ["outcome", "coefficient", "standard_error", "p_value"],
    ].rename(
        columns={
            "coefficient": "baseline_coefficient",
            "standard_error": "baseline_standard_error",
            "p_value": "baseline_p_value",
        }
    )
    results = audited_merge(
        results,
        baseline,
        merge_id="pretrend_control_attach_baseline",
        on="outcome",
        validate="many_to_one",
    )
    results["coefficient_minus_baseline"] = (
        results["coefficient"] - results["baseline_coefficient"]
    )
    return results, pd.concat(slope_frames, ignore_index=True)


def render_report(results: pd.DataFrame) -> str:
    lines = [
        "# Difference-in-differences controlling for the pre-trend",
        "",
        "Both trend specifications are robustness. Neither is principal, and "
        "neither may be promoted because it produces a more comfortable "
        "coefficient.",
        "",
        "`predetermined_pretrend_control` fits one linear slope per CBO on "
        "the pre-period only and enters the predetermined path as a "
        "regressor. `differential_linear_trend` adds a treated-versus-control "
        "linear trend fitted over the whole sample.",
        "",
        "**Caveat.** A linear trend extrapolated across 42 post-treatment "
        "months can absorb part of a gradual diffusion effect. The "
        "full-sample form is more exposed to this because it uses "
        "post-period data to fit the slope. Humlum and Vestergaard "
        "(2025) report precise zeros from this family, which shows it does "
        "not manufacture an effect; it does not show that it cannot hide "
        "one.",
        "",
        "| Outcome | Specification | Coefficient | SE | p | vs baseline |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in results.itertuples(index=False):
        lines.append(
            f"| {row.outcome} | {row.specification_id} | "
            f"{row.coefficient:+.6f} | {row.standard_error:.6f} | "
            f"{row.p_value:.6g} | "
            f"{row.coefficient_minus_baseline:+.6f} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate DiD specifications that control for pre-trends."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--slopes", type=Path, default=DEFAULT_SLOPES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = prepare(pd.read_parquet(args.panel))
    results, slopes = run(data)
    atomic_csv(results, args.output)
    atomic_csv(slopes, args.slopes)
    atomic_text(render_report(results), args.report)
    support = {
        "task": "T8A.5",
        "specifications": [
            item["specification_id"] for item in SPECIFICATIONS
        ],
        "model_count": int(len(results)),
        "all_converged": bool(results["converged"].all()),
        "pre_period_end": PRE_END_PERIOD,
        "minimum_pre_observations": MINIMUM_PRE_OBSERVATIONS,
        "cbo_with_insufficient_pre_observations": int(
            slopes["slope_status"].ne("estimated").sum()
        ),
        "trend_scales": sorted(slopes["trend_scale"].unique().tolist()),
        "causal_roles": sorted(results["causal_role"].unique().tolist()),
        "principal_specification_changed": False,
        "labelled_robustness_only": bool(
            results.loc[
                results["specification_id"].ne("00_no_trend_control"),
                "causal_role",
            ]
            .eq("robustness")
            .all()
        ),
    }
    atomic_json(support, args.support)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
