#!/usr/bin/env python3
"""T8A.2: pretrend diagnostics for the co-principal level-2 sector design.

Level 2 adds CNAE-section-by-month fixed effects, so it asks whether the
national violation is sectoral reallocation rather than an occupational
trend. It was estimated statically in the V2 release and never diagnosed.

Klein Teeselink (2025) controls for sector shocks explicitly, and
Brynjolfsson, Chandar and Chen (2025) use firm-by-time effects, which are more
saturated still. The support table is written before any coefficient.
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
from sector_models import build_support_table


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DIVISION_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_cbo_divisao.parquet"
)
DIAGNOSTICS_DIR = PACKAGE_ROOT / "results" / "diagnostics"
DEFAULT_RESULTS = DIAGNOSTICS_DIR / "pretrend_level2.csv"
DEFAULT_EVENT_COEFFICIENTS = (
    DIAGNOSTICS_DIR / "pretrend_level2_coefficients.csv"
)
DEFAULT_SUPPORT_TABLE = DIAGNOSTICS_DIR / "pretrend_level2_support.csv"
DEFAULT_SUPPORT = DIAGNOSTICS_DIR / "pretrend_level2_support.json"
DEFAULT_LEVEL1 = DIAGNOSTICS_DIR / "pretrend_power_check.csv"

OUTCOMES = (
    ("admissoes", "ppml"),
    ("desligamentos", "ppml"),
    ("n_movimentacoes", "ppml"),
    ("ln_salario_real_adm", "ols"),
    ("asinh_saldo", "ols"),
)
WINDOW = (-23, 23)
LEAD_MINIMUM = -23
CONTRACT = (
    {
        "specification_id": "level_2",
        "label": "CBO4 x CNAE section and section x month effects",
        "fixed_effects": ("cbo_section", "section_period"),
        "cluster_variables": ("cbo_4d",),
    },
    {
        "specification_id": "level_2_two_way",
        "label": "Level 2 with CBO4 and CNAE-division two-way clustering",
        "fixed_effects": ("cbo_section", "section_period"),
        "cluster_variables": ("cbo_4d", "divisao"),
    },
)


def load_sector_data(path: Path) -> pd.DataFrame:
    columns = [
        "cbo_4d",
        "secao",
        "divisao",
        "periodo",
        "periodo_num",
        "post",
        "treated_main",
        "included_main",
        *[outcome for outcome, _ in OUTCOMES],
    ]
    data = pd.read_parquet(path, columns=columns)
    data = data.loc[data["included_main"].eq(True)].copy()
    data = add_event_time(data)
    data = restrict_event_window(data, *WINDOW)
    data["treated_main"] = pd.to_numeric(data["treated_main"], errors="raise")
    data["cbo_section"] = (
        data["cbo_4d"].astype(str) + "::" + data["secao"].astype(str)
    ).astype("category")
    data["section_period"] = (
        data["secao"].astype(str) + "::" + data["periodo"].astype(str)
    ).astype("category")
    for column in ("cbo_4d", "secao", "divisao", "periodo"):
        data[column] = data[column].astype("category")
    return data


def run_level2_pretrends(
    data: pd.DataFrame,
    *,
    coefficient_frames: list[pd.DataFrame] | None = None,
) -> pd.DataFrame:
    expected = [
        value
        for value in range(WINDOW[0], WINDOW[1] + 1)
        if value != REFERENCE_EVENT_TIME
    ]
    rows: list[dict[str, Any]] = []
    for contract in CONTRACT:
        for outcome, estimator in OUTCOMES:
            model, model_data, formula, cluster_counts = fit_event_model(
                data,
                outcome=outcome,
                estimator=estimator,
                interaction="treated_main",
                fixed_effects=contract["fixed_effects"],
                cluster_variables=contract["cluster_variables"],
                model_id=f"{contract['specification_id']}__{outcome}",
            )
            if coefficient_frames is not None:
                model_id = (
                    f"sector_pretrend::{contract['specification_id']}::"
                    f"{outcome}"
                )
                coefficient_frames.append(
                    registered_event_coefficient_frame(
                        model,
                        "treated_main",
                        model_id=model_id,
                        outcome=outcome,
                        estimator=estimator,
                        sample_id=(
                            "sector:"
                            f"{contract['specification_id']}:event_-23_23"
                        ),
                        cluster_counts=cluster_counts,
                        expected_event_times=expected,
                    )
                )
            rows.append(
                diagnostic_row(
                    model=model,
                    model_data=model_data,
                    formula=formula,
                    cluster_counts=cluster_counts,
                    interaction="treated_main",
                    lead_minimum=LEAD_MINIMUM,
                    event_minimum=WINDOW[0],
                    event_maximum=WINDOW[1],
                    expected_event_times=expected,
                    specification_id=contract["specification_id"],
                    specification_label=contract["label"],
                    outcome=outcome,
                    estimator=estimator,
                    sample="level_2_cbo4_by_cnae_section",
                )
            )
            print(
                f"[level2] {contract['specification_id']} {outcome} "
                f"joint_p={rows[-1]['joint_lead_p_value']:.6g} "
                f"status={rows[-1]['pretrend_status']}",
                flush=True,
            )
    return order_diagnostic_columns(pd.DataFrame(rows))


def compare_with_level1(
    level2: pd.DataFrame,
    level1_path: Path,
) -> pd.DataFrame:
    if not level1_path.is_file():
        raise FileNotFoundError(
            "Level-1 diagnostics must be produced before the comparison: "
            f"{level1_path}"
        )
    level1 = pd.read_csv(level1_path)
    level1 = level1.loc[
        level1["specification_id"].eq("balanced_frozen_window")
        & level1["joint_lead_window"].eq("-23_to_-2"),
        [
            "outcome",
            "joint_lead_p_value",
            "linear_pretrend_p_value",
            "dynamic_pre_p_lt_005",
            "pretrend_status",
        ],
    ].rename(
        columns={
            "joint_lead_p_value": "level_1_joint_lead_p_value",
            "linear_pretrend_p_value": "level_1_linear_pretrend_p_value",
            "dynamic_pre_p_lt_005": "level_1_dynamic_pre_p_lt_005",
            "pretrend_status": "level_1_pretrend_status",
        }
    )
    merged = audited_merge(
        level2,
        level1,
        merge_id="pretrend_level2_attach_level1",
        on="outcome",
        validate="many_to_one",
    )
    merged["level_2_minus_level_1_linear_slope"] = (
        merged["linear_pretrend_coefficient"]
    )
    merged["sector_effects_resolve_pretrend"] = (
        merged["level_1_pretrend_status"].eq("fail")
        & merged["pretrend_status"].ne("fail")
    )
    return merged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run level-2 sector pretrend diagnostics."
    )
    parser.add_argument(
        "--division-panel",
        type=Path,
        default=DEFAULT_DIVISION_PANEL,
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument(
        "--event-coefficients",
        type=Path,
        default=DEFAULT_EVENT_COEFFICIENTS,
    )
    parser.add_argument(
        "--support-table",
        type=Path,
        default=DEFAULT_SUPPORT_TABLE,
    )
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument("--level1", type=Path, default=DEFAULT_LEVEL1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    support_table = build_support_table(args.division_panel)
    atomic_csv(support_table, args.support_table)
    print(
        "support table written before estimation: "
        + json.dumps(
            support_table.set_index("level_id")[
                "coexisting_cells"
            ].to_dict(),
            sort_keys=True,
        ),
        flush=True,
    )
    data = load_sector_data(args.division_panel)
    coefficient_frames: list[pd.DataFrame] = []
    results = run_level2_pretrends(
        data,
        coefficient_frames=coefficient_frames,
    )
    event_coefficients = pd.concat(coefficient_frames, ignore_index=True)
    key = ["model_id", "event_time"]
    if event_coefficients.duplicated(key).any():
        raise RuntimeError("Sector pretrend coefficient keys are duplicated")
    atomic_csv(
        event_coefficients.sort_values(key).reset_index(drop=True),
        args.event_coefficients,
    )
    comparison = compare_with_level1(results, args.level1)
    atomic_csv(comparison, args.results)
    support = {
        "task": "T8A.2",
        "event_window": list(WINDOW),
        "lead_window": "-23_to_-2",
        "model_count": int(len(results)),
        "cbo_section_levels": int(data["cbo_section"].nunique()),
        "section_period_levels": int(data["section_period"].nunique()),
        "division_clusters": int(data["divisao"].nunique()),
        "cbo_clusters": int(data["cbo_4d"].nunique()),
        "cells": int(len(data)),
        "support_table_written_before_coefficients": True,
        "pretrend_status_counts": {
            str(key): int(value)
            for key, value in results["pretrend_status"]
            .value_counts()
            .sort_index()
            .items()
        },
        "sector_effects_resolve_any_pretrend": bool(
            comparison["sector_effects_resolve_pretrend"].any()
        ),
        "principal_specification_changed": False,
    }
    atomic_json(support, args.support)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
