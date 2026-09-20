#!/usr/bin/env python3
"""Audit block B: is the national result 75 occupations or three?

54.1% of treated admissions sit in three CBO4 codes — 4110, 4211 and 4221, all
clerical — and 80.4% in ten. The control side is far more dispersed (33.9% in
its three largest). PPML weights by size, so the "national" coefficient could
be, in substance, the coefficient for office clerks.

That would not make the estimate wrong. It would change what it is an estimate
*of*, and therefore what the dissertation is allowed to call it.

Three exercises:

1. leave-one-out over all 75 treated occupations, five outcomes;
2. drop the three largest simultaneously;
3. an occupation-unweighted comparison, so size-weighting stops driving the
   average.

Writes evidence only. Touches no existing artefact and re-estimates nothing
that is already published.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
COMMON_DIR = Path(__file__).resolve().parents[2] / "common"
for _directory in (MODELS_DIR, COMMON_DIR):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from estimators import fit_model


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
LADDER = PACKAGE_ROOT / "results" / "models" / "specification_ladder.csv"
OUTPUT_DIR = PACKAGE_ROOT / "results" / "audit"
OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)


def load() -> pd.DataFrame:
    panel = pd.read_parquet(PANEL)
    data = panel.loc[panel["included_main"].eq(True)].copy()
    data["treated_main"] = pd.to_numeric(
        data["treated_main"], errors="raise"
    ).astype(float)
    data["post_treat"] = (
        pd.to_numeric(data["post"], errors="raise").astype(float)
        * data["treated_main"]
    )
    return data


def concentration(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for treated in (1, 0):
        side = data.loc[data["treated_main"].eq(treated)]
        totals = (
            side.groupby("cbo_4d")["admissoes"].sum().sort_values(
                ascending=False
            )
        )
        share = totals / totals.sum()
        rows.append(
            {
                "group": "treated" if treated else "control",
                "occupations": int(len(totals)),
                "admissions": int(totals.sum()),
                "top1_share_pct": float(100 * share.iloc[0]),
                "top3_share_pct": float(100 * share.head(3).sum()),
                "top5_share_pct": float(100 * share.head(5).sum()),
                "top10_share_pct": float(100 * share.head(10).sum()),
                "largest_codes": ";".join(totals.head(3).index.astype(str)),
            }
        )
    return pd.DataFrame(rows)


def _fit(data: pd.DataFrame, outcome: str, estimator: str, label: str) -> dict:
    result, _ = fit_model(
        data,
        model_id=label,
        outcome=outcome,
        treatment_term="post_treat",
        estimator=estimator,
        fixed_effects=("cbo_4d", "periodo"),
        cluster_variables=("cbo_4d",),
        principal=False,
        separation_check=("fe",),
    )
    return {
        "outcome": outcome,
        "estimator": estimator,
        "coefficient": result["coefficient"],
        "standard_error": result["standard_error"],
        "p_value": result["p_value"],
        "n_obs": result["n_obs"],
        "n_clusters": result["minimum_clusters"],
    }


def leave_one_out(data: pd.DataFrame) -> pd.DataFrame:
    treated_codes = sorted(
        data.loc[data["treated_main"].eq(1), "cbo_4d"].unique().tolist()
    )
    rows: list[dict[str, Any]] = []
    for index, code in enumerate(treated_codes, start=1):
        subset = data.loc[data["cbo_4d"].ne(code)]
        for outcome, estimator in OUTCOMES:
            try:
                row = _fit(
                    subset,
                    outcome,
                    estimator,
                    f"loo_{code}_{outcome}",
                )
                row.update({"dropped_cbo": code, "status": "estimated"})
            except Exception as exception:  # noqa: BLE001
                row = {
                    "outcome": outcome,
                    "estimator": estimator,
                    "coefficient": np.nan,
                    "standard_error": np.nan,
                    "p_value": np.nan,
                    "n_obs": np.nan,
                    "n_clusters": np.nan,
                    "dropped_cbo": code,
                    "status": f"failed: {exception}"[:200],
                }
            rows.append(row)
        print(
            f"[jackknife] {index}/{len(treated_codes)} dropped {code}",
            flush=True,
        )
    return pd.DataFrame(rows)


def drop_largest(data: pd.DataFrame, how_many: int = 3) -> pd.DataFrame:
    totals = (
        data.loc[data["treated_main"].eq(1)]
        .groupby("cbo_4d")["admissoes"]
        .sum()
        .sort_values(ascending=False)
    )
    largest = totals.head(how_many).index.tolist()
    subset = data.loc[~data["cbo_4d"].isin(largest)]
    rows = []
    for outcome, estimator in OUTCOMES:
        row = _fit(subset, outcome, estimator, f"drop_top{how_many}_{outcome}")
        row["dropped_cbos"] = ";".join(map(str, largest))
        rows.append(row)
    return pd.DataFrame(rows)


def unweighted_comparison(data: pd.DataFrame) -> pd.DataFrame:
    """OLS on log flows gives every occupation-month the same weight.

    PPML weights observations by the conditional mean, so large occupations
    dominate. This is not a better estimator — it answers a different
    question, and the gap between the two is the size-weighting effect.
    """

    frame = data.copy()
    rows = []
    for outcome, _ in OUTCOMES:
        if outcome in {"ln_salario_real_adm", "asinh_saldo"}:
            continue
        frame[f"ln1p_{outcome}"] = np.log1p(frame[outcome])
        rows.append(
            _fit(
                frame,
                f"ln1p_{outcome}",
                "ols",
                f"unweighted_{outcome}",
            )
            | {"weighting": "occupation_month_equal", "base_outcome": outcome}
        )
    return pd.DataFrame(rows)


def summarise(
    loo: pd.DataFrame,
    baseline: pd.Series,
) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for outcome, _ in OUTCOMES:
        cut = loo.loc[
            loo["outcome"].eq(outcome) & loo["status"].eq("estimated")
        ]
        base = float(baseline[outcome])
        significant = cut["p_value"].lt(0.05)
        shift = (cut["coefficient"] - base).abs()
        summary[outcome] = {
            "baseline": base,
            "draws": int(len(cut)),
            "min": float(cut["coefficient"].min()),
            "max": float(cut["coefficient"].max()),
            "sign_flips": int(
                (np.sign(cut["coefficient"]) != np.sign(base)).sum()
            ),
            "share_significant_at_5pct": float(significant.mean()),
            "largest_absolute_shift": float(shift.max()),
            "most_influential_cbo": str(
                cut.loc[shift.idxmax(), "dropped_cbo"]
            ),
            # A single occupation whose removal flips the conclusion is what
            # would make the national estimate an artefact of that occupation.
            "any_single_removal_changes_5pct_verdict": bool(
                significant.nunique() > 1
            ),
        }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Leave-one-out influence of treated occupations."
    )
    parser.add_argument("--skip-jackknife", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load()

    concentration(data).to_csv(
        OUTPUT_DIR / "b1_concentration.csv", index=False
    )
    drop_largest(data).to_csv(
        OUTPUT_DIR / "b3_drop_three_largest.csv", index=False
    )
    unweighted_comparison(data).to_csv(
        OUTPUT_DIR / "b4_unweighted_comparison.csv", index=False
    )

    if args.skip_jackknife:
        print("jackknife skipped")
        return 0

    ladder = pd.read_csv(LADDER)
    baseline = ladder.loc[
        ladder["step_id"].eq("01_no_controls")
    ].set_index("outcome")["coefficient"]

    loo = leave_one_out(data)
    loo.to_csv(OUTPUT_DIR / "b2_leave_one_out.csv", index=False)
    summary = summarise(loo, baseline)
    (OUTPUT_DIR / "b_jackknife_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
