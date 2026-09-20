#!/usr/bin/env python3
"""Build the optional Section 5.2.3.b income dynamic figures.

The alternative uses the five PNAD/IBGE-style pre-treatment CBO income bands
already reported in Table 5.2.3.b. It estimates only admissions and real
admission wages, writes additive backing data, and leaves the original income
figures and the curated dissertation package unchanged.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from section4_5_final.config import TABLE_DIR  # noqa: E402
from section4_5_final.section5_2_combined_figures import (  # noqa: E402
    OUTPUT_ROOT as COMBINED_OUTPUT_ROOT,
    OUTCOME_TITLES,
    plot_combined_figure,
)
from section4_5_final.section5_2_dynamic_figures import (  # noqa: E402
    EVENT_TIMES,
    PATH_ROLES,
    add_winsorized_wage_path,
    load_main_strict_panel,
    normalize_paths,
    safely_estimate_dynamic,
)
from section4_5_final.section5_2_tables import SECTION5_2_ADDITIONAL_SPECS  # noqa: E402
from section4_event_study.heterogeneity import build_pre_treatment_income_groups  # noqa: E402


DIMENSION = "income_pnad"
GROUPS = list(SECTION5_2_ADDITIONAL_SPECS[DIMENSION]["groups"])
DYNAMIC_OUTCOMES = ["ln_admissoes", "ln_salario_real_adm"]
FIGURE_FILENAMES = {
    "ln_admissoes": "figure_s5_2_income_pnad_b_admissions_event_study_paths.png",
    "ln_salario_real_adm": (
        "figure_s5_2_income_pnad_b_real_admission_wage_event_study_paths.png"
    ),
}
BACKING_FILENAMES = {
    "coefficients": "income_pnad_b_event_study_coefficients_long.csv",
    "pretrends": "income_pnad_b_event_study_pretrends.csv",
    "paths": "income_pnad_b_normalized_paths_long.csv",
}
SOURCE_TABLE_PATH = TABLE_DIR / "table_5_2_3_b.md"
AUDIT_FILENAME = "figure_s5_2_income_pnad_b_blindspot.md"


def log(message: str) -> None:
    print(f"[section5_2_income_pnad] {message}", flush=True)


def _expected_model_keys() -> list[tuple[str, str]]:
    return [
        (group_id, outcome)
        for group_id, _group_label in GROUPS
        for outcome in DYNAMIC_OUTCOMES
    ]


def _validate_dynamic_frames(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> None:
    """Validate the complete five-group, two-outcome alternative contract."""
    required = {
        "coefficients": {
            "dimension",
            "group_id",
            "group_label",
            "outcome",
            "t",
            "coef",
            "ci_low",
            "ci_high",
            "coefficient_status",
        },
        "pretrends": {
            "dimension",
            "group_id",
            "group_label",
            "outcome",
            "pretrend_status",
            "power_status",
        },
        "paths": {
            "dimension",
            "group_id",
            "group_label",
            "outcome",
            "scenario_role",
            "t",
            "path_index",
            "path_status",
        },
    }
    frames = {
        "coefficients": coefficients,
        "pretrends": pretrends,
        "paths": paths,
    }
    for name, frame in frames.items():
        missing = sorted(required[name] - set(frame.columns))
        if missing:
            raise RuntimeError(f"{name} is missing columns: {missing}")
        if set(frame["dimension"]) != {DIMENSION}:
            raise RuntimeError(f"{name} contains another dimension.")
        if set(frame["group_id"]) != {group_id for group_id, _label in GROUPS}:
            raise RuntimeError(f"{name} contains unexpected income groups.")
        if set(frame["outcome"]) != set(DYNAMIC_OUTCOMES):
            raise RuntimeError(f"{name} contains unexpected outcomes.")

    expected_models = len(GROUPS) * len(DYNAMIC_OUTCOMES)
    expected_counts = {
        "coefficients": expected_models * len(EVENT_TIMES),
        "pretrends": expected_models,
        "paths": expected_models * len(PATH_ROLES) * len(EVENT_TIMES),
    }
    for name, frame in frames.items():
        if len(frame) != expected_counts[name]:
            raise RuntimeError(
                f"{name} has {len(frame)} rows; expected {expected_counts[name]}."
            )

    if coefficients.duplicated(["group_id", "outcome", "t"]).any():
        raise RuntimeError("Alternative coefficients contain duplicate cells.")
    if pretrends.duplicated(["group_id", "outcome"]).any():
        raise RuntimeError("Alternative pretrends contain duplicate models.")
    if paths.duplicated(["group_id", "outcome", "scenario_role", "t"]).any():
        raise RuntimeError("Alternative paths contain duplicate cells.")
    if set(coefficients["t"]) != set(EVENT_TIMES) or set(paths["t"]) != set(EVENT_TIMES):
        raise RuntimeError("Alternative dynamic grids do not cover t=-12,...,24.")
    if set(paths["scenario_role"]) != set(PATH_ROLES):
        raise RuntimeError("Alternative paths must contain Exposed and Not Exposed roles.")
    reference = coefficients[coefficients["t"].eq(-1)]
    if len(reference) != expected_models or not np.allclose(
        pd.to_numeric(reference["coef"], errors="coerce"),
        0.0,
        equal_nan=False,
    ):
        raise RuntimeError("Every alternative event-study reference must equal zero at t=-1.")

    expected_keys = _expected_model_keys()
    for name, frame in frames.items():
        observed_keys = list(
            frame[["group_id", "outcome"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        )
        if observed_keys != expected_keys:
            raise RuntimeError(f"{name} model order differs from Table 5.2.3.b.")


def build_income_pnad_results(
    base: pd.DataFrame | None = None,
    income_groups: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Estimate dynamic DDDs and descriptive paths for the five income bands."""
    base = load_main_strict_panel() if base is None else base.copy()
    if income_groups is None:
        income_groups = build_pre_treatment_income_groups("pnad")
    eligible_groups = {group_id for group_id, _label in GROUPS}
    base["cbo_4d"] = base["cbo_4d"].astype(str).str.zfill(4)
    base["income_group"] = base["cbo_4d"].map(income_groups)
    income_panel = base[base["income_group"].isin(eligible_groups)].copy()
    if income_panel.empty:
        raise RuntimeError("No CBO-month rows map to the PNAD/IBGE income bands.")
    missing_groups = eligible_groups - set(income_panel["income_group"])
    if missing_groups:
        raise RuntimeError(f"PNAD/IBGE income groups without CBO support: {sorted(missing_groups)}")

    income_paths = add_winsorized_wage_path(
        income_panel,
        wage_column="salario_medio_adm",
    )
    coefficient_parts: list[pd.DataFrame] = []
    pretrend_rows: list[dict[str, object]] = []
    path_parts: list[pd.DataFrame] = []
    for group_id, group_label in GROUPS:
        model_panel = income_panel.copy()
        model_panel["group_indicator"] = model_panel["income_group"].eq(group_id).astype(int)
        target_paths = income_paths[income_paths["income_group"].eq(group_id)].copy()
        for outcome in DYNAMIC_OUTCOMES:
            log(f"Estimating {group_id}/{outcome} (DDD)...")
            coefficients, pretrend = safely_estimate_dynamic(
                model_panel,
                dimension=DIMENSION,
                group_id=group_id,
                group_label=group_label,
                outcome=outcome,
                estimand="ddd",
            )
            paths = normalize_paths(
                target_paths,
                dimension=DIMENSION,
                group_id=group_id,
                group_label=group_label,
                outcome=outcome,
            )
            for key in ["power_status", "treated_cbo", "control_cbo"]:
                paths[key] = pretrend[key]
            coefficient_parts.append(coefficients)
            pretrend_rows.append(pretrend)
            path_parts.append(paths)

    coefficients = pd.concat(coefficient_parts, ignore_index=True)
    pretrends = pd.DataFrame(pretrend_rows)
    paths = pd.concat(path_parts, ignore_index=True)
    group_order = {group_id: index for index, (group_id, _label) in enumerate(GROUPS)}
    outcome_order = {outcome: index for index, outcome in enumerate(DYNAMIC_OUTCOMES)}
    for frame in [coefficients, pretrends, paths]:
        frame["_group_order"] = frame["group_id"].map(group_order)
        frame["_outcome_order"] = frame["outcome"].map(outcome_order)
    coefficients = (
        coefficients.sort_values(["_group_order", "_outcome_order", "t"])
        .drop(columns=["_group_order", "_outcome_order"])
        .reset_index(drop=True)
    )
    pretrends = (
        pretrends.sort_values(["_group_order", "_outcome_order"])
        .drop(columns=["_group_order", "_outcome_order"])
        .reset_index(drop=True)
    )
    paths["_role_order"] = paths["scenario_role"].map({"treated": 0, "control": 1})
    paths = (
        paths.sort_values(["_group_order", "_outcome_order", "_role_order", "t"])
        .drop(columns=["_group_order", "_outcome_order", "_role_order"])
        .reset_index(drop=True)
    )
    _validate_dynamic_frames(coefficients, pretrends, paths)
    return coefficients, pretrends, paths


def _write_blindspot_report(
    output_root: Path,
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> Path:
    pretrend_counts = pretrends["pretrend_status"].value_counts(dropna=False).to_dict()
    power_counts = pretrends["power_status"].value_counts(dropna=False).to_dict()
    pretrend_flags = pretrends[
        pretrends["pretrend_status"].isin(["fail", "warning", "not_available"])
    ]
    support_flags = pretrends[pretrends["power_status"].isin(["thin", "limited"])]
    path_view = paths.dropna(subset=["path_index"]).copy()
    path_view["distance_from_100"] = (path_view["path_index"] - 100.0).abs()
    extremes = [
        (
            f"{row.group_label} / {OUTCOME_TITLES[row.outcome]} / {row.scenario_role} "
            f"at t={int(row.t)}: index={row.path_index:.1f}"
        )
        for row in path_view.nlargest(5, "distance_from_100").itertuples(index=False)
    ]
    ruling = "CONDITIONAL" if not pretrend_flags.empty or not support_flags.empty else "CLEAR"
    lines = [
        "# Blindspot Report",
        "",
        "**Output:** Two combined dynamic figures for the PNAD/IBGE pre-treatment income bands",
        "",
        f"**Date:** {date.today().isoformat()}",
        "",
        "**Stated finding:** Alternative income bins may reveal concentrated hiring or entry-wage dynamics hidden by the three-band specification.",
        "",
        "## Vice 1: The Unexplained Feature",
        "",
        f"- **[DONE] Complete diagnostic inventory.** Pretrend counts: `{pretrend_counts}`; power counts: `{power_counts}`.",
        f"- **[DONE] Largest descriptive path departures inventoried:** {'; '.join(extremes)}.",
    ]
    for row in pretrend_flags.itertuples(index=False):
        lines.append(
            f"- **[FLAG]** {row.group_label} / {OUTCOME_TITLES[row.outcome]} has dynamic pretrend status `{row.pretrend_status}`."
        )
    lines.extend(
        [
            "- **[FLAG] Five narrow bands do not create five independent experiments.** Each DDD compares one band with the complement of the other four bands.",
            "",
            "## Vice 2: The Convenient Absence",
            "",
            "- **[FLAG] Income is assigned at the CBO level from the pre-treatment median wage.** The figures do not represent current individual household or labor income.",
            "- **[FLAG] Confidence intervals are pointwise and unadjusted across ten dynamic models.**",
            "- **[FLAG] The descriptive paths show Exposed versus Not Exposed within the named band, not the band-versus-complement DDD itself.**",
        ]
    )
    for row in support_flags.drop_duplicates(["group_id", "power_status"]).itertuples(index=False):
        lines.append(
            f"- **[FLAG]** {row.group_label} has `{row.power_status}` CBO support; apparent spikes may be driven by very few occupations."
        )
    lines.extend(
        [
            "",
            "## Virtue 1: The Unasked Question",
            "",
            "- **[DONE] The five-band view separates the broad middle of the wage distribution.** It can distinguish the 2–3 SM and 3–5 SM groups that were pooled in the original specification.",
            "- **[FLAG] If admissions and entry wages move in different bands, the mechanism may be reallocation across occupational wage tiers rather than a uniform employment response.**",
            "",
            "## Virtue 2: The Unexploited Strength",
            "",
            "- **[DONE] Group assignment is predetermined.** It uses pre-treatment CBO wages rather than a post-treatment outcome.",
            "- **[DONE] Weak support and failed pretrends remain visible inside the figures rather than being silently removed.**",
            "- **[FLAG] A leave-one-CBO-out check is the highest-value robustness exercise for every thin income band.**",
            "",
            "## Ruling",
            "",
            f"- [{'x' if ruling == 'CLEAR' else ' '}] **CLEAR** — proceed without unresolved diagnostic flags.",
            f"- [{'x' if ruling == 'CONDITIONAL' else ' '}] **CONDITIONAL** — use as exploratory heterogeneity with explicit pretrend, support, complement, and multiplicity qualifications.",
            "- [ ] **HOLD** — do not use or publish the figures.",
            "",
            "These figures improve resolution across income bands but do not rescue a panel with a failed dynamic pretrend or thin occupational support.",
        ]
    )
    path = output_root / "audit" / AUDIT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_outputs(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    output_root: Path = COMBINED_OUTPUT_ROOT,
    dpi: int = 300,
) -> dict[str, Path]:
    """Write additive income-B artifacts without deleting existing figures."""
    _validate_dynamic_frames(coefficients, pretrends, paths)
    table_dir = output_root / "tables"
    figure_dir = output_root / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    coefficient_path = table_dir / BACKING_FILENAMES["coefficients"]
    pretrend_path = table_dir / BACKING_FILENAMES["pretrends"]
    path_path = table_dir / BACKING_FILENAMES["paths"]
    coefficients.to_csv(coefficient_path, index=False)
    pretrends.to_csv(pretrend_path, index=False)
    paths.to_csv(path_path, index=False)
    outputs: dict[str, Path] = {
        "coefficients": coefficient_path,
        "pretrends": pretrend_path,
        "paths": path_path,
    }
    for outcome in DYNAMIC_OUTCOMES:
        figure_path = figure_dir / FIGURE_FILENAMES[outcome]
        plot_combined_figure(
            coefficients,
            pretrends,
            paths,
            dimension=DIMENSION,
            outcome=outcome,
            output_path=figure_path,
            dpi=dpi,
        )
        outputs[f"figure_{outcome}"] = figure_path
    outputs["audit"] = _write_blindspot_report(
        output_root,
        coefficients,
        pretrends,
        paths,
    )
    return outputs


def build(
    output_root: Path = COMBINED_OUTPUT_ROOT,
    *,
    dpi: int = 300,
) -> dict[str, Path]:
    """Estimate and write the optional income-B dynamic package."""
    if not SOURCE_TABLE_PATH.exists() or SOURCE_TABLE_PATH.stat().st_size == 0:
        raise FileNotFoundError(f"Missing Table 5.2.3.b reference: {SOURCE_TABLE_PATH}")
    coefficients, pretrends, paths = build_income_pnad_results()
    outputs = write_outputs(
        coefficients,
        pretrends,
        paths,
        output_root=output_root,
        dpi=dpi,
    )
    outputs["source_table"] = SOURCE_TABLE_PATH
    log(
        f"Wrote 2 figures, {len(coefficients)} coefficients, "
        f"{len(pretrends)} pretrends, and {len(paths)} path rows."
    )
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=COMBINED_OUTPUT_ROOT)
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build(output_root=args.output_root, dpi=args.dpi)
