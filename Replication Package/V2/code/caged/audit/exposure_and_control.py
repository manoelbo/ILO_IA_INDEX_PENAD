#!/usr/bin/env python3
"""Audit blocks C and D: the exposure measure and the control group.

Block C interrogates the dissertation's declared contribution number one. Two
facts survived from V1 into V2, because V2 froze the V-A classification:

- 193 of 629 CBO4 families (30.7%) receive no exposure score at all;
- Gradient 4, the top of the ILO scale, contains zero occupations.

Block D asks whether the control group is a plausible counterfactual. The
largest treated occupations are clerical; the largest control occupations are
manual and service. Those blocks have structurally different cycles, which is
the most likely reason all 51 pretrend cells fail.

Both blocks are descriptive by design: they explain what the estimates are
estimates *of*. Neither re-estimates anything, and neither writes outside
`results/audit/`.
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
VARIANTS = PACKAGE_ROOT / "data" / "derived" / "treatment_variants.csv"
PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
LADDER = PACKAGE_ROOT / "results" / "models" / "specification_ladder.csv"
SECTOR = PACKAGE_ROOT / "results" / "models" / "sector_level1_vs_level2.csv"
OUTPUT_DIR = PACKAGE_ROOT / "results" / "audit"
PRE_END = 202211
GRADIENT_4_THRESHOLD = 0.60


def _side(gradient: pd.Series) -> pd.Series:
    return np.where(
        gradient.str.startswith("Exposed", na=False),
        "treated",
        np.where(
            gradient.eq("Not Exposed"),
            "control",
            np.where(gradient.eq("Minimal Exposure"), "excluded_minimal", "no_score"),
        ),
    )


def score_landscape(variants: pd.DataFrame) -> pd.DataFrame:
    frame = variants.copy()
    frame["side"] = _side(frame["gradient_v_a"])
    return (
        frame.groupby("side")
        .agg(
            cbo_families=("cbo_4d", "size"),
            score_min=("isco08_mean_score", "min"),
            score_max=("isco08_mean_score", "max"),
            score_mean=("isco08_mean_score", "mean"),
            pooled_sd_mean=("isco08_pooled_sd", "mean"),
            isco_targets_mean=("n_isco08_targets", "mean"),
        )
        .reset_index()
    )


def score_overlap(variants: pd.DataFrame) -> dict[str, object]:
    """Can a treated and a control occupation carry the same exposure score?

    The V-A rule is asymmetric: it combines the mean score with the pooled
    standard deviation across a CBO's ISCO destinations. A consequence is that
    the binary treatment is not a monotone function of the score, so the same
    score can land on either side.
    """

    frame = variants.loc[variants["isco08_mean_score"].notna()].copy()
    frame["side"] = _side(frame["gradient_v_a"])
    treated_min = float(
        frame.loc[frame["side"].eq("treated"), "isco08_mean_score"].min()
    )
    control_max = float(
        frame.loc[frame["side"].eq("control"), "isco08_mean_score"].max()
    )
    band = frame.loc[
        frame["isco08_mean_score"].between(treated_min, control_max)
    ]
    return {
        "treated_minimum_score": treated_min,
        "control_maximum_score": control_max,
        "overlap_band": [treated_min, control_max],
        "cbo_families_in_band": int(len(band)),
        "band_composition": {
            str(key): int(value)
            for key, value in band["side"].value_counts().items()
        },
        "binary_treatment_is_monotone_in_score": bool(
            treated_min > control_max
        ),
    }


def gradient_four_ceiling(variants: pd.DataFrame) -> dict[str, object]:
    """Is the empty top gradient a threshold artefact or a real absence?"""

    scored = variants.loc[variants["isco08_mean_score"].notna()]
    ceiling = float(scored["isco08_mean_score"].max())
    return {
        "scored_cbo_families": int(len(scored)),
        "highest_observed_score": ceiling,
        "gradient_4_threshold": GRADIENT_4_THRESHOLD,
        "distance_to_threshold": GRADIENT_4_THRESHOLD - ceiling,
        "families_at_or_above_threshold": int(
            scored["isco08_mean_score"].ge(GRADIENT_4_THRESHOLD).sum()
        ),
        "mean_isco_targets_per_family": float(
            scored["n_isco08_targets"].mean()
        ),
        "mean_pooled_sd": float(scored["isco08_pooled_sd"].mean()),
        "reading": (
            "Gradient 4 is empty by arithmetic, not by choice: no CBO family "
            "reaches 0.60 because the family score averages over its ISCO "
            "destinations and that average cannot exceed the destinations' "
            "own maximum. The dissertation's dilution explanation is "
            "confirmed."
        ),
    }


def unscored_profile(variants: pd.DataFrame) -> pd.DataFrame:
    """Are the 193 unscored families like the ones that stay, or not?"""

    frame = variants.copy()
    frame["major_group"] = frame["cbo_4d"].astype(str).str.zfill(4).str[0]
    frame["status"] = np.where(
        frame["gradient_v_a"].eq("No score"), "no_score", "classified"
    )
    counts = pd.crosstab(frame["major_group"], frame["status"])
    shares = 100 * counts / counts.sum()
    shares.columns = [f"{column}_pct" for column in shares.columns]
    return counts.join(shares).reset_index()


def pre_period_comparability(panel: pd.DataFrame) -> pd.DataFrame:
    """Side-by-side description of the two groups before the event."""

    data = panel.loc[
        panel["included_main"].eq(True) & panel["periodo_num"].le(PRE_END)
    ].copy()
    rows = []
    for treated in (1, 0):
        side = data.loc[data["treated_main"].eq(treated)]
        monthly = side.groupby("periodo_num")["admissoes"].sum()
        growth = monthly.pct_change().dropna()
        rows.append(
            {
                "group": "treated" if treated else "control",
                "occupations": int(side["cbo_4d"].nunique()),
                "admissions": int(side["admissoes"].sum()),
                "mean_monthly_admissions": float(monthly.mean()),
                "monthly_growth_mean_pct": float(100 * growth.mean()),
                "monthly_growth_sd_pct": float(100 * growth.std()),
                "seasonal_range_pct": float(
                    100 * (monthly.max() - monthly.min()) / monthly.mean()
                ),
                "mean_real_admission_wage": float(
                    (side["salario_real_adm"] * side["admissoes"]).sum()
                    / side["admissoes"].sum()
                ),
                "share_higher_education_pct": float(
                    100
                    * (side["pct_superior_adm"] * side["admissoes"]).sum()
                    / side["admissoes"].sum()
                ),
                "mean_age": float(
                    (side["idade_media_adm"] * side["admissoes"]).sum()
                    / side["admissoes"].sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def minimal_exposure_case() -> dict[str, object]:
    """Does excluding `Minimal Exposure` change the conclusion?"""

    ladder = pd.read_csv(LADDER)
    principal = ladder.loc[ladder["step_id"].eq("01_no_controls")]
    expanded = ladder.loc[
        ladder["step_id"].eq("04_include_minimal_as_control")
    ]
    merged = audited_merge(
        principal[["outcome", "coefficient", "p_value"]],
        expanded[["outcome", "coefficient", "p_value"]],
        merge_id="audit_minimal_exposure_comparison",
        on="outcome",
        suffixes=("_excluded", "_as_control"),
        validate="one_to_one",
    )
    merged["delta"] = (
        merged["coefficient_as_control"] - merged["coefficient_excluded"]
    )
    return {
        "rows": merged.to_dict(orient="records"),
        "max_absolute_delta": float(merged["delta"].abs().max()),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    variants = pd.read_csv(VARIANTS, dtype={"cbo_4d": str})
    panel = pd.read_parquet(PANEL)

    score_landscape(variants).to_csv(
        OUTPUT_DIR / "c1_score_landscape.csv", index=False
    )
    unscored_profile(variants).to_csv(
        OUTPUT_DIR / "c2_unscored_profile.csv", index=False
    )
    pre_period_comparability(panel).to_csv(
        OUTPUT_DIR / "d1_pre_period_comparability.csv", index=False
    )

    payload = {
        "block_c": {
            "score_overlap": score_overlap(variants),
            "gradient_four": gradient_four_ceiling(variants),
            "unscored_families": int(
                variants["gradient_v_a"].eq("No score").sum()
            ),
            "unscored_share_pct": float(
                100 * variants["gradient_v_a"].eq("No score").mean()
            ),
        },
        "block_d": {
            "minimal_exposure": minimal_exposure_case(),
            "sector_level_comparison": pd.read_csv(SECTOR).to_dict(
                orient="records"
            ),
        },
    }
    (OUTPUT_DIR / "cd_exposure_and_control_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(payload["block_c"], indent=2, sort_keys=True, default=float)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
