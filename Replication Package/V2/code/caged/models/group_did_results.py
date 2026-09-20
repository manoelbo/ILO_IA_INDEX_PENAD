#!/usr/bin/env python3
"""Promote the 130 per-group DiD estimates to multiplicity-aware results.

Family C combines the 100 frozen per-group estimates produced during Phase 8A
with the 30 alternative-partition estimates produced in Phase 8B. Benjamini-
Hochberg is applied once to the complete family. The 100 frozen estimates are
copied, never re-estimated.
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

from estimators import cluster_t_inference
from heterogeneity import benjamini_hochberg
from merge_audit import audited_merge
from pretrend_engine import atomic_csv, atomic_json, atomic_text


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DIAGNOSTICS_DIR = PACKAGE_ROOT / "results" / "diagnostics"
MODELS_OUTPUT_DIR = PACKAGE_ROOT / "results" / "models"
DEFAULT_FROZEN = DIAGNOSTICS_DIR / "ddd_pretrends.csv"
DEFAULT_ALTERNATIVE = (
    DIAGNOSTICS_DIR / "ddd_alternative_partitions_pretrends.csv"
)
DEFAULT_FROZEN_SUPPORT = DIAGNOSTICS_DIR / "ddd_family_support.csv"
DEFAULT_ALTERNATIVE_SUPPORT = (
    DIAGNOSTICS_DIR / "ddd_alternative_partitions_support.csv"
)
DEFAULT_OUTPUT = MODELS_OUTPUT_DIR / "group_did_results.csv"
DEFAULT_SUMMARY = MODELS_OUTPUT_DIR / "group_did_results_support.json"
DEFAULT_REPORT = MODELS_OUTPUT_DIR / "GROUP_DID_RESULTS.md"
FROZEN_SIZE = 100
ALTERNATIVE_SIZE = 30
FAMILY_SIZE = 130
KEYS = ["dimension", "group_id", "outcome"]


def _validate_source(
    frame: pd.DataFrame,
    *,
    label: str,
    expected_rows: int,
) -> None:
    if len(frame) != expected_rows:
        raise RuntimeError(
            f"{label} must contain {expected_rows} rows; found {len(frame)}"
        )
    if frame.duplicated(KEYS).any():
        raise RuntimeError(f"{label} contains duplicate result keys")


def _confidence_interval(
    coefficient: float,
    standard_error: float,
    clusters: float,
) -> tuple[float, float, float]:
    values = (coefficient, standard_error, clusters)
    if not all(np.isfinite(value) for value in values):
        return np.nan, np.nan, np.nan
    if standard_error <= 0 or clusters < 2:
        return np.nan, np.nan, np.nan
    inference = cluster_t_inference(
        float(coefficient),
        float(standard_error),
        {"cbo_4d": int(clusters)},
    )
    return (
        float(inference["ci_low"]),
        float(inference["ci_high"]),
        float(inference["cluster_df"]),
    )


def _promote_source(
    frame: pd.DataFrame,
    *,
    source_family: str,
    order_offset: int,
) -> pd.DataFrame:
    promoted = pd.DataFrame(
        {
            "dimension": frame["dimension"],
            "dimension_kind": frame["dimension_kind"],
            "group_id": frame["group_id"],
            "group_label": frame["group_label"],
            "outcome": frame["outcome"],
            "estimator": frame["estimator"],
            "coefficient": frame["group_did_coefficient"],
            "standard_error": frame["group_did_standard_error"],
            "nominal_p_value": frame["group_did_p_value"],
            "n_obs": frame["group_did_n_obs"],
            "minimum_clusters": frame["group_did_clusters"],
            "group_pretrend_status": frame[
                "group_pretrend_pretrend_status"
            ],
            "group_pretrend_joint_p_value": frame[
                "group_pretrend_joint_lead_p_value"
            ],
            "ddd_pretrend_status": frame["ddd_pretrend_status"],
            "group_mde_80_power": frame["group_mde_80_power"],
            "result_status": frame["group_did_status"],
            "error": frame["group_did_error"],
        }
    )
    promoted["source_diagnostic_family"] = source_family
    promoted["_source_order"] = np.arange(
        order_offset,
        order_offset + len(promoted),
    )
    intervals = [
        _confidence_interval(coefficient, standard_error, clusters)
        for coefficient, standard_error, clusters in zip(
            promoted["coefficient"],
            promoted["standard_error"],
            promoted["minimum_clusters"],
            strict=True,
        )
    ]
    promoted["ci_low"] = [value[0] for value in intervals]
    promoted["ci_high"] = [value[1] for value in intervals]
    promoted["cluster_df"] = [value[2] for value in intervals]
    return promoted


def build_group_did_results(
    frozen: pd.DataFrame,
    alternative: pd.DataFrame,
    frozen_support: pd.DataFrame,
    alternative_support: pd.DataFrame,
) -> pd.DataFrame:
    """Combine all per-group DiDs and adjust their p-values as one family."""
    _validate_source(
        frozen,
        label="Frozen group-DiD diagnostics",
        expected_rows=FROZEN_SIZE,
    )
    _validate_source(
        alternative,
        label="Alternative group-DiD diagnostics",
        expected_rows=ALTERNATIVE_SIZE,
    )
    promoted = pd.concat(
        [
            _promote_source(
                frozen,
                source_family="A",
                order_offset=0,
            ),
            _promote_source(
                alternative,
                source_family="B",
                order_offset=FROZEN_SIZE,
            ),
        ],
        ignore_index=True,
    )
    support_columns = [
        "dimension",
        "group_id",
        "support_status",
        "target_treated_cbo_with_flows",
        "target_control_cbo_with_flows",
    ]
    support = pd.concat(
        [
            frozen_support[support_columns],
            alternative_support[support_columns],
        ],
        ignore_index=True,
    )
    if support.duplicated(["dimension", "group_id"]).any():
        raise RuntimeError("Family C support keys are not unique")
    promoted = audited_merge(
        promoted,
        support,
        merge_id="group_did_family_c_attach_support",
        on=["dimension", "group_id"],
        how="left",
        validate="many_to_one",
    )
    if promoted[support_columns[2:]].isna().any().any():
        raise RuntimeError("Family C support is incomplete")
    promoted = promoted.sort_values("_source_order").reset_index(drop=True)
    promoted["bh_adjusted_p_value"] = benjamini_hochberg(
        promoted["nominal_p_value"].to_numpy(),
        family_size=FAMILY_SIZE,
    )
    promoted["nominal_significant_005"] = (
        promoted["nominal_p_value"] < 0.05
    )
    promoted["bh_significant_005"] = (
        promoted["bh_adjusted_p_value"] < 0.05
    )
    promoted["family_id"] = "C"
    promoted["family_size"] = FAMILY_SIZE
    promoted["multiplicity_method"] = "Benjamini-Hochberg"
    promoted["multiplicity_scope"] = (
        "single adjustment over all 130 per-group DiD tests"
    )
    promoted["interpretation"] = "reportable"
    promoted["is_causal_effect"] = False

    frozen_output = promoted.loc[
        promoted["source_diagnostic_family"].eq("A"),
        "coefficient",
    ].to_numpy()
    if not np.array_equal(
        frozen_output,
        frozen["group_did_coefficient"].to_numpy(),
    ):
        raise RuntimeError(
            "Frozen Family C coefficients differ from ddd_pretrends.csv"
        )
    if len(promoted) != FAMILY_SIZE:
        raise RuntimeError(
            f"Family C must contain {FAMILY_SIZE} rows"
        )
    return promoted.drop(columns="_source_order")


def summarize(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "task": "T8B.4",
        "family_id": "C",
        "family_size": FAMILY_SIZE,
        "multiplicity_method": "Benjamini-Hochberg",
        "multiplicity_passes": 1,
        "estimated": int(frame["result_status"].eq("estimated").sum()),
        "nominal_significant_005": int(
            frame["nominal_significant_005"].sum()
        ),
        "bh_significant_005": int(frame["bh_significant_005"].sum()),
        "frozen_coefficients_exact": True,
        "frozen_rows": FROZEN_SIZE,
        "alternative_rows": ALTERNATIVE_SIZE,
        "is_causal_effect": False,
    }


def render_report(frame: pd.DataFrame) -> str:
    summary = summarize(frame)
    return "\n".join(
        [
            "# Per-group DiD results: Family C",
            "",
            "Family C contains all 130 estimated per-group DiD tests. The "
            "100 Phase 8A coefficients were copied exactly from "
            "`ddd_pretrends.csv`; the 30 alternative-partition "
            "coefficients were copied from "
            "`ddd_alternative_partitions_pretrends.csv`. No frozen "
            "coefficient was re-estimated.",
            "",
            "Benjamini–Hochberg was applied once to all 130 nominal "
            "p-values. It was not applied separately to the 100 and 30 "
            "subsets.",
            "",
            f"- Nominal p < 0.05: {summary['nominal_significant_005']}",
            f"- Family C BH p < 0.05: {summary['bh_significant_005']}",
            "",
            "The BH-adjusted p-values in Family C are not comparable to "
            "those in `ddd_multiplicity_results.csv`. That file reports "
            "the DDD estimator in frozen Family A (100 tests); this file "
            "reports the per-group DiD estimator in Family C (130 tests).",
            "",
            "These estimates are reportable descriptive associations, "
            "not identified causal effects: the available national "
            "pretrend diagnostics fail.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the 130-test per-group DiD family."
    )
    parser.add_argument("--frozen", type=Path, default=DEFAULT_FROZEN)
    parser.add_argument(
        "--alternative",
        type=Path,
        default=DEFAULT_ALTERNATIVE,
    )
    parser.add_argument(
        "--frozen-support",
        type=Path,
        default=DEFAULT_FROZEN_SUPPORT,
    )
    parser.add_argument(
        "--alternative-support",
        type=Path,
        default=DEFAULT_ALTERNATIVE_SUPPORT,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = build_group_did_results(
        pd.read_csv(args.frozen),
        pd.read_csv(args.alternative),
        pd.read_csv(args.frozen_support),
        pd.read_csv(args.alternative_support),
    )
    atomic_csv(frame, args.output)
    atomic_json(summarize(frame), args.summary)
    atomic_text(render_report(frame), args.report)
    print(json.dumps(summarize(frame), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
