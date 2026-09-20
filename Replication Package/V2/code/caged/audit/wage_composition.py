#!/usr/bin/env python3
"""Audit block A: is the admission-wage differential a price or a composition?

The real admission wage is the only nationally significant result in V2
(-0.050740, p < 1e-6). It is also the most exposed to a mechanical artefact,
because the outcome is the *mean wage of the people hired* in an
occupation-month. If exposed occupations started hiring less-educated or
younger workers, that mean falls without the price of labour moving at all.

V2 dropped the contemporaneous composition controls because they are
post-treatment. That is right for the flow outcomes and it leaves the wage
outcome undefended against exactly this channel, so the channel has to be
measured rather than assumed away.

This script measures it three independent ways and writes the evidence. It
changes no existing artefact.
"""

from __future__ import annotations

import json
from pathlib import Path

import sys

import numpy as np
import pandas as pd

COMMON_DIR = Path(__file__).resolve().parents[2] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from merge_audit import audited_merge


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DDD_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_heterogeneity_ddd.parquet"
GROUP_DID = PACKAGE_ROOT / "results" / "models" / "group_did_results.csv"
LADDER = PACKAGE_ROOT / "results" / "models" / "specification_ladder.csv"
HOURLY = PACKAGE_ROOT / "results" / "mechanisms" / "hourly_wage_results.csv"
OUTPUT_DIR = PACKAGE_ROOT / "results" / "audit"
PRE_END = 202211
WAGE = "ln_salario_real_adm"


def composition_shift() -> pd.DataFrame:
    """Difference-in-differences of the education mix of the people hired."""

    panel = pd.read_parquet(
        DDD_PANEL,
        columns=[
            "dimension",
            "group_id",
            "subgroup",
            "periodo_num",
            "admissoes",
            "treated_main",
        ],
    )
    education = panel.loc[
        panel["dimension"].eq("education") & panel["subgroup"].eq("target")
    ]
    rows = []
    for treated in (1, 0):
        side = education.loc[education["treated_main"].eq(treated)]
        for label, window in (
            ("pre", side["periodo_num"].le(PRE_END)),
            ("post", side["periodo_num"].gt(PRE_END)),
        ):
            totals = side.loc[window].groupby("group_id")["admissoes"].sum()
            share = totals / totals.sum()
            for group_id, value in share.items():
                rows.append(
                    {
                        "treated": treated,
                        "window": label,
                        "group_id": group_id,
                        "admission_share": float(value),
                    }
                )
    shares = pd.DataFrame(rows)
    wide = shares.pivot_table(
        index="group_id",
        columns=["treated", "window"],
        values="admission_share",
    )
    result = pd.DataFrame(
        {
            "treated_pre": wide[(1, "pre")],
            "treated_post": wide[(1, "post")],
            "control_pre": wide[(0, "pre")],
            "control_post": wide[(0, "post")],
        }
    )
    result["treated_change_pp"] = 100 * (
        result["treated_post"] - result["treated_pre"]
    )
    result["control_change_pp"] = 100 * (
        result["control_post"] - result["control_pre"]
    )
    result["did_pp"] = (
        result["treated_change_pp"] - result["control_change_pp"]
    )
    return result.reset_index()


def within_group_decomposition(
    shares: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Oaxaca-style split of the aggregate effect into price and composition.

    The counterfactual is the aggregate effect that would have been observed
    had the education mix stayed at its pre-treatment treated-group level. It
    is the pre-period-share-weighted average of the within-education effects;
    whatever the aggregate has beyond that is composition.

    This is an approximation, not an identity: each within-group model carries
    its own occupation and month effects. It fixes the order of magnitude,
    which is what the question needs.
    """

    group_did = pd.read_csv(GROUP_DID)
    within = group_did.loc[
        group_did["dimension"].eq("education")
        & group_did["outcome"].eq(WAGE),
        ["group_id", "coefficient", "standard_error", "bh_adjusted_p_value"],
    ]
    merged = audited_merge(
        within,
        shares[["group_id", "treated_pre", "did_pp"]],
        merge_id="audit_wage_attach_education_shares",
        on="group_id",
        validate="one_to_one",
    )
    weight = merged["treated_pre"] / merged["treated_pre"].sum()
    price = float((merged["coefficient"] * weight).sum())

    ladder = pd.read_csv(LADDER)
    aggregate = float(
        ladder.loc[
            ladder["step_id"].eq("01_no_controls")
            & ladder["outcome"].eq(WAGE),
            "coefficient",
        ].item()
    )
    pre_controls = float(
        ladder.loc[
            ladder["step_id"].eq("02_pre_treatment_controls_x_post")
            & ladder["outcome"].eq(WAGE),
            "coefficient",
        ].item()
    )
    composition = aggregate - price
    summary = {
        "aggregate_effect": aggregate,
        "within_education_price_component": price,
        "composition_component": composition,
        "composition_share_of_aggregate": composition / aggregate,
        "pre_treatment_controls_effect": pre_controls,
        "pre_treatment_controls_implied_composition": aggregate - pre_controls,
        "pre_treatment_controls_implied_share": (
            (aggregate - pre_controls) / aggregate
        ),
    }
    return merged.assign(weight=weight), summary


def other_dimensions() -> pd.DataFrame:
    """Is the wage decline present inside age, sex and race groups too?

    If it is, those margins are not the mechanism. Only a dimension whose
    within-group effects are systematically smaller than the aggregate can be
    carrying composition.
    """

    group_did = pd.read_csv(GROUP_DID)
    wage = group_did.loc[group_did["outcome"].eq(WAGE)]
    rows = []
    for dimension, frame in wage.groupby("dimension"):
        rows.append(
            {
                "dimension": dimension,
                "groups": int(len(frame)),
                "min_coefficient": float(frame["coefficient"].min()),
                "max_coefficient": float(frame["coefficient"].max()),
                "unweighted_mean": float(frame["coefficient"].mean()),
                "bh_significant": int(
                    (frame["bh_adjusted_p_value"] < 0.05).sum()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("dimension")


def hourly_comparison() -> dict[str, float]:
    """Hours are the other mechanical channel, and they point the other way."""

    hourly = pd.read_csv(HOURLY)
    values = hourly.set_index("outcome")["coefficient"]
    return {
        "monthly_wage": float(values.get(WAGE, np.nan)),
        "hourly_wage": float(values.get("ln_salario_hora_real_adm", np.nan)),
        "weekly_hours": float(values.get("ln_horas_semanais_adm", np.nan)),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shares = composition_shift()
    decomposition, summary = within_group_decomposition(shares)
    dimensions = other_dimensions()
    hours = hourly_comparison()

    shares.to_csv(OUTPUT_DIR / "a1_education_composition_shift.csv", index=False)
    decomposition.to_csv(
        OUTPUT_DIR / "a2_wage_price_composition_split.csv",
        index=False,
    )
    dimensions.to_csv(
        OUTPUT_DIR / "a3_wage_within_dimension_range.csv",
        index=False,
    )
    payload = {**summary, "hourly": hours}
    (OUTPUT_DIR / "a_wage_composition_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
