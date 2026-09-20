#!/usr/bin/env python3
"""Run and evaluate the Anatel Stage 0 placebo and pretrend diagnostics.

Only false-event and pre-treatment coefficients are estimated here. The real
post-treatment triple interaction is never included in a fitted model.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd


V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
FRONT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = V2_ROOT / "code" / "caged" / "models"
if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

from estimators import fit_model  # noqa: E402
from pretrend_engine import (  # noqa: E402
    atomic_csv,
    atomic_json,
    atomic_text,
    diagnose_event_model,
    event_parameter_frame,
    order_diagnostic_columns,
)


STATUS_RANK = {"fail": 0, "warning": 1, "pass": 2}
OUTCOMES = (
    "ln_admissoes",
    "ln_desligamentos",
    "ln_salario_real_adm",
    "asinh_saldo",
)
FIXED_EFFECTS = (
    "cbo_municipio",
    "cbo_periodo",
    "uf_periodo",
)
TRUE_PRE_START = 202101
FALSE_EVENT_PERIOD = 202112
TRUE_PRE_END = 202211
LEAD_MINIMUM = -23
REFERENCE_EVENT_TIME = -1

PANEL_PATH = FRONT_DIR / "data" / "painel_anatel.parquet"
PLACEBO_PATH = FRONT_DIR / "results" / "anatel_placebo_dec2021.csv"
PLACEBO_OLD_PATH = (
    FRONT_DIR / "results" / "anatel_placebo_dec2021_old_cut.csv"
)
PLACEBO_SUPPORT_PATH = (
    FRONT_DIR / "results" / "anatel_placebo_dec2021_support.json"
)
PRETRENDS_PATH = (
    FRONT_DIR / "results" / "anatel_pretrends_interaction.csv"
)
PRETRENDS_OLD_PATH = (
    FRONT_DIR / "results" / "anatel_pretrends_interaction_old_cut.csv"
)
PRETREND_COEFFICIENTS_PATH = (
    FRONT_DIR / "results" / "spatial_pretrend_coefficients.csv"
)
PRETREND_COEFFICIENTS_OLD_PATH = (
    FRONT_DIR / "results" / "spatial_pretrend_coefficients_old_cut.csv"
)
STATUS_PATH = FRONT_DIR / "results" / "anatel_status.json"
CAUSE_PATH = FRONT_DIR / "results" / "anatel_stage0_cause_attribution.json"
REPORT_PATH = FRONT_DIR / "results" / "ANATEL_STAGE0.md"
SCORECARD_PATH = FRONT_DIR / "results" / "scorecard_v3.csv"
A2_SUPPORT_PATH = (
    FRONT_DIR / "results" / "anatel_late_declaration_support.json"
)
A3_SUPPORT_PATH = FRONT_DIR / "results" / "anatel_vintage_status.json"
A4_SUPPORT_PATH = FRONT_DIR / "results" / "painel_anatel_support.json"
A4_SUPPORT_CSV = FRONT_DIR / "results" / "painel_anatel_support.csv"
LATE_BY_CONNECTIVITY_PATH = (
    FRONT_DIR / "results" / "anatel_late_declaration_by_connectivity.csv"
)


def evaluate_gate_a_g1(
    placebo: pd.DataFrame,
    pretrends: pd.DataFrame,
    *,
    low_connectivity_share: float,
) -> dict[str, Any]:
    expected_outcomes = set(OUTCOMES)
    if set(placebo["outcome"]) != expected_outcomes:
        raise RuntimeError("A-G1 placebo outcome set is incomplete")
    if set(pretrends["outcome"]) != expected_outcomes:
        raise RuntimeError("A-G1 pretrend outcome set is incomplete")
    placebo_pass = bool(
        pd.to_numeric(placebo["p_value"], errors="raise").ge(0.05).all()
    )
    pretrend_pass = bool(
        pretrends["pretrend_status"].astype(str).ne("fail").any()
    )
    cut_pass = bool(float(low_connectivity_share) >= 0.30)
    criteria = {
        "placebo_all_outcomes": placebo_pass,
        "pretrend_any_non_fail": pretrend_pass,
        "low_connectivity_at_least_30_percent": cut_pass,
    }
    return {
        "opens": bool(all(criteria.values())),
        "criteria": criteria,
        "failed_criteria": [
            name for name, passed in criteria.items() if not passed
        ],
    }


def _p_values(frame: pd.DataFrame) -> dict[str, float]:
    return {
        str(row.outcome): float(row.p_value)
        for row in frame[["outcome", "p_value"]].itertuples(index=False)
    }


def _statuses(frame: pd.DataFrame) -> dict[str, str]:
    return {
        str(row.outcome): str(row.pretrend_status)
        for row in frame[
            ["outcome", "pretrend_status"]
        ].itertuples(index=False)
    }


def attribute_stage0_causes(
    *,
    v1_placebo: pd.DataFrame,
    corrected_old_cut_placebo: pd.DataFrame,
    corrected_new_cut_placebo: pd.DataFrame,
    corrected_old_cut_pretrends: pd.DataFrame,
    corrected_new_cut_pretrends: pd.DataFrame,
) -> dict[str, Any]:
    """Apply the attribution rule frozen in the local decision log."""
    v1 = _p_values(v1_placebo)
    old_cut = _p_values(corrected_old_cut_placebo)
    new_cut = _p_values(corrected_new_cut_placebo)
    flow_outcomes = {"ln_admissoes", "ln_desligamentos"}
    vintage_changes = sorted(
        outcome
        for outcome in flow_outcomes
        if v1.get(outcome, 1.0) < 0.05
        and old_cut.get(outcome, 0.0) >= 0.05
    )
    cut_placebo_changes = sorted(
        outcome
        for outcome, old_p in old_cut.items()
        if old_p < 0.05 and new_cut.get(outcome, 0.0) >= 0.05
    )
    old_status = _statuses(corrected_old_cut_pretrends)
    new_status = _statuses(corrected_new_cut_pretrends)
    cut_pretrend_improvements = sorted(
        outcome
        for outcome, before in old_status.items()
        if outcome in new_status
        and STATUS_RANK.get(new_status[outcome], -1)
        > STATUS_RANK.get(before, -1)
    )
    vintage_supported = bool(vintage_changes)
    cut_supported = bool(cut_placebo_changes or cut_pretrend_improvements)
    if vintage_supported and cut_supported:
        conclusion = "both"
    elif vintage_supported:
        conclusion = "vintage_contamination"
    elif cut_supported:
        conclusion = "broken_cut"
    else:
        conclusion = "neither"
    return {
        "vintage_contamination_supported": vintage_supported,
        "broken_cut_supported": cut_supported,
        "vintage_placebo_changes": vintage_changes,
        "cut_placebo_changes": cut_placebo_changes,
        "cut_pretrend_improvements": cut_pretrend_improvements,
        "conclusion": conclusion,
    }


def prepare_placebo_sample(
    panel: pd.DataFrame,
    *,
    high_column: str,
) -> pd.DataFrame:
    """Build the false-event sample and exclude every true-post month."""
    required = {"periodo_num", "treated", high_column}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Placebo sample is missing columns: {missing}")
    sample = panel.loc[
        panel["periodo_num"].between(TRUE_PRE_START, TRUE_PRE_END)
    ].drop(columns=["post"], errors="ignore").copy()
    sample["placebo_post"] = (
        sample["periodo_num"].ge(FALSE_EVENT_PERIOD).astype("int8")
    )
    sample["placebo_post_treated"] = (
        sample["placebo_post"] * sample["treated"]
    ).astype("int8")
    sample["placebo_post_high"] = (
        sample["placebo_post"] * sample[high_column]
    ).astype("int8")
    sample["placebo_treated_high"] = (
        sample["treated"] * sample[high_column]
    ).astype("int8")
    sample["placebo_triple"] = (
        sample["placebo_post"]
        * sample["treated"]
        * sample[high_column]
    ).astype("int8")
    if int(sample["periodo_num"].max()) > TRUE_PRE_END:
        raise RuntimeError("Placebo sample includes a true-post month")
    if set(sample["placebo_post"].unique()) != {0, 1}:
        raise RuntimeError("Placebo sample lacks a false pre or post period")
    return sample


def build_pretrend_formula(
    outcome: str,
    *,
    triple_interaction: str,
    high_interaction: str,
) -> str:
    """Build the pre-only dynamic triple-interaction formula.

    The treated-by-event lower term is exactly absorbed by cbo_periodo. The
    time-invariant treated-by-high lower term is exactly absorbed by
    cbo_municipio. The high-by-event lower term is identifiable and included.
    """
    fixed = " + ".join(FIXED_EFFECTS)
    return (
        f"{outcome} ~ i(event_time, {triple_interaction}, ref=-1)"
        f" + i(event_time, {high_interaction}, ref=-1)"
        f" | {fixed}"
    )


def run_placebos(
    panel: pd.DataFrame,
    *,
    cut: str,
    high_column: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    sample = prepare_placebo_sample(panel, high_column=high_column)
    rows: list[dict[str, Any]] = []
    for outcome in OUTCOMES:
        result, model = fit_model(
            sample,
            model_id=f"anatel_stage0_placebo__{cut}__{outcome}",
            outcome=outcome,
            treatment_term="placebo_triple",
            estimator="ols",
            fixed_effects=FIXED_EFFECTS,
            cluster_variables=("id_municipio",),
            controls=("placebo_post_high",),
            principal=True,
        )
        result.update(
            {
                "cut": cut,
                "falsification": "december_2021_temporal_placebo",
                "false_event_period": FALSE_EVENT_PERIOD,
                "sample_start": int(sample["periodo_num"].min()),
                "sample_end": int(sample["periodo_num"].max()),
                "true_post_rows": 0,
                "lower_order_included": "placebo_post_high",
                "lower_order_absorbed": (
                    "placebo_post; placebo_post_treated; "
                    "placebo_treated_high"
                ),
                "real_treatment_coefficient_estimated": False,
            }
        )
        rows.append(result)
        del model
        gc.collect()
    results = pd.DataFrame(rows)
    support = {
        "cut": cut,
        "sample_start": int(sample["periodo_num"].min()),
        "sample_end": int(sample["periodo_num"].max()),
        "false_event_period": FALSE_EVENT_PERIOD,
        "true_treatment_period": 202212,
        "sample_is_strictly_pre_treatment": bool(
            sample["periodo_num"].max() < 202212
        ),
        "rows": int(len(sample)),
        "municipalities": int(sample["id_municipio"].nunique()),
        "cbo": int(sample["cbo_4d"].nunique()),
        "outcomes": list(OUTCOMES),
        "estimator": "ols",
        "fixed_effects": list(FIXED_EFFECTS),
        "cluster": "id_municipio",
        "real_treatment_coefficient_estimated": False,
    }
    del sample
    gc.collect()
    return results, support


def run_pretrends(
    panel: pd.DataFrame,
    *,
    cut: str,
    high_column: str,
    coefficient_path: Path | None = None,
) -> pd.DataFrame:
    """Estimate only the 22 pre-treatment months of the triple interaction."""
    import pyfixest as pf

    sample = panel.loc[
        panel["periodo_num"].between(TRUE_PRE_START, TRUE_PRE_END)
    ].drop(columns=["post"], errors="ignore").copy()
    observed_event_times = sorted(sample["event_time"].unique().tolist())
    if observed_event_times != list(range(LEAD_MINIMUM, 0)):
        raise RuntimeError(
            f"Pretrend event grid is incomplete: {observed_event_times}"
        )
    sample["pretrend_high"] = sample[high_column].astype("int8")
    sample["pretrend_treated_high"] = (
        sample["treated"] * sample[high_column]
    ).astype("int8")
    estimated_event_times = list(range(LEAD_MINIMUM, REFERENCE_EVENT_TIME))
    rows: list[dict[str, Any]] = []
    coefficient_rows: list[pd.DataFrame] = []
    for outcome in OUTCOMES:
        required = [
            outcome,
            "event_time",
            "pretrend_high",
            "pretrend_treated_high",
            "id_municipio",
            *FIXED_EFFECTS,
        ]
        model_data = sample.dropna(subset=required).copy()
        formula = build_pretrend_formula(
            outcome,
            triple_interaction="pretrend_treated_high",
            high_interaction="pretrend_high",
        )
        model = pf.feols(
            formula,
            data=model_data,
            vcov={"CRV1": "id_municipio"},
        )
        used_data = getattr(model, "_data", model_data)
        cluster_counts = {
            "id_municipio": int(used_data["id_municipio"].nunique())
        }
        diagnostics = diagnose_event_model(
            model,
            interaction="pretrend_treated_high",
            cluster_counts=cluster_counts,
            lead_minimum=LEAD_MINIMUM,
            expected_event_times=estimated_event_times,
        )
        parameters = event_parameter_frame(
            model,
            "pretrend_treated_high",
            expected_event_times=estimated_event_times,
        )
        parameters.insert(0, "outcome", outcome)
        parameters.insert(0, "cut", cut)
        parameters.insert(
            0,
            "model_id",
            f"spatial_pretrend__{cut}__{outcome}",
        )
        parameters["n_obs"] = int(model._N)
        parameters["minimum_clusters"] = int(min(cluster_counts.values()))
        parameters["reference_event_time"] = REFERENCE_EVENT_TIME
        parameters["status"] = "estimated"
        coefficient_rows.append(parameters)
        rows.append(
            {
                "specification_id": (
                    f"anatel_stage0_pretrend__{cut}__{outcome}"
                ),
                "specification_label": (
                    f"Anatel Stage 0 pre-only triple interaction ({cut})"
                ),
                "outcome": outcome,
                "estimator": "ols",
                "sample": "2021-01_to_2022-11_pre_only",
                "event_window": "-23_to_-1",
                "n_obs": int(model._N),
                "complete_case_input": int(len(model_data)),
                "minimum_clusters": int(min(cluster_counts.values())),
                "cluster_counts": json.dumps(
                    cluster_counts, sort_keys=True
                ),
                "interaction": "pretrend_treated_high",
                "formula": formula,
                "cut": cut,
                "lower_order_included": "i(event_time, pretrend_high)",
                "lower_order_absorbed": (
                    "i(event_time, treated); treated_by_high"
                ),
                "real_post_period_in_model": False,
                "real_treatment_coefficient_estimated": False,
                **diagnostics,
            }
        )
        del model, model_data
        gc.collect()
    del sample
    gc.collect()
    if coefficient_path is not None:
        coefficients = pd.concat(coefficient_rows, ignore_index=True)
        atomic_csv(
            coefficients.sort_values(["model_id", "event_time"]),
            coefficient_path,
        )
    return order_diagnostic_columns(pd.DataFrame(rows))


def _best_pretrend_status(pretrends: pd.DataFrame) -> str:
    values = pretrends["pretrend_status"].astype(str).tolist()
    return max(values, key=lambda value: STATUS_RANK.get(value, -1))


def _fmt(value: Any, digits: int = 6) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def _cause_label(value: str) -> str:
    return {
        "both": "both vintage contamination and the broken cut",
        "vintage_contamination": "vintage contamination only",
        "broken_cut": "the broken cut only",
        "neither": "neither candidate cause",
    }[value]


def _markdown_table(
    frame: pd.DataFrame,
    columns: list[str],
) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in frame[columns].itertuples(index=False, name=None):
        lines.append(
            "| "
            + " | ".join(
                _fmt(value) if isinstance(value, float) else str(value)
                for value in row
            )
            + " |"
        )
    return lines


def _build_report(
    *,
    a2: dict[str, Any],
    a3: dict[str, Any],
    a4: dict[str, Any],
    cut_table: pd.DataFrame,
    late: pd.DataFrame,
    placebo: pd.DataFrame,
    placebo_old: pd.DataFrame,
    pretrends: pd.DataFrame,
    pretrends_old: pd.DataFrame,
    gate: dict[str, Any],
    attribution: dict[str, Any],
) -> str:
    status = "OPEN" if gate["opens"] else "CLOSED"
    late_focus = late.loc[
        late["ano"].isin([2021, 2024])
        & late["cut"].eq("within_sample"),
        ["ano", "connectivity_group", "share_for", "share_flag"],
    ].copy()
    placebo_view = placebo[
        ["outcome", "coefficient", "standard_error", "p_value", "n_obs"]
    ].copy()
    placebo_old_view = placebo_old[
        ["outcome", "coefficient", "p_value"]
    ].copy()
    pretrend_view = pretrends[
        [
            "outcome",
            "joint_lead_p_value",
            "linear_pretrend_p_value",
            "dynamic_pre_p_lt_005",
            "lead_covariance_positive_semidefinite",
            "pretrend_status",
        ]
    ].copy()
    pretrend_old_view = pretrends_old[
        [
            "outcome",
            "joint_lead_p_value",
            "linear_pretrend_p_value",
            "dynamic_pre_p_lt_005",
            "pretrend_status",
        ]
    ].copy()
    lines = [
        "# Anatel Stage 0",
        "",
        f"**A-G1: {status}.** "
        + (
            "The front stops here and the real DDD is NOT EXECUTED."
            if not gate["opens"]
            else (
                "The signed gate criteria pass, but this run stops at the "
                "gate as requested; no real DDD is estimated."
            )
        ),
        "",
        "## Frozen scope",
        "",
        "- Destination: appendix or the Section 6.4 research agenda; never "
        "Section 5.",
        "- Stage 0 estimates only a false December 2021 interaction and "
        "pre-treatment leads. It does not estimate the real "
        "`post × exposed × connectivity` coefficient.",
        "- The panel was rebuilt from the signed V2 movement partitions. No "
        "legacy municipal panel or embedded connectivity cut was read.",
        "",
        "## A2 — late declarations in the corrected V2 vintage",
        "",
        (
            f"The exact signed A2 formula gives "
            f"{100 * a2['national'][1]['share_for']:.6f}% in 2021 and "
            f"{100 * a2['national'][4]['share_for']:.6f}% in 2024. "
            "The corresponding flag cross-checks are "
            f"{100 * a2['national'][1]['share_flag']:.6f}% and "
            f"{100 * a2['national'][4]['share_flag']:.6f}%."
        ),
        "",
        (
            "The preregistered rounded benchmark (8.61% and 1.29%) is not "
            "reproduced: its 2021 value mixes declaration-year and "
            "fact-month axes. This incompatibility was investigated and "
            "retained as a failed benchmark, not repaired by changing the "
            "frozen denominator."
        ),
        "",
        "Late-declaration shares by the corrected within-sample split:",
        "",
        *_markdown_table(
            late_focus,
            ["ano", "connectivity_group", "share_for", "share_flag"],
        ),
        "",
        "## A3 — frozen primary-source Anatel vintage",
        "",
        (
            f"The four required members were downloaded by byte ranges with "
            f"runtime-derived offsets. The frozen panel contains "
            f"{a3['municipalities']:,} municipalities and reconciles "
            f"{a3['total_reconciliation_months']} national months with a "
            f"maximum absolute difference of "
            f"{a3['total_reconciliation_max_absolute_difference']} access."
        ),
        "",
        (
            f"`pct_fibra`, defined by `Meio de Acesso = 'Fibra'`, ranges "
            f"from {a3['pct_fibra_min']:.6f} to "
            f"{a3['pct_fibra_max']:.6f}; it is not identically zero. "
            f"Official density and the Censo household cross-check correlate "
            f"at {a3['official_vs_census_density_correlation']:.6f}. "
            f"The median official-minus-Censo density difference is "
            f"{a3['official_minus_census_density_median']:.6f}."
        ),
        "",
        "## A4 — reconstructed municipal panel and cut",
        "",
        (
            f"The final panel has {a4['panel']['rows']:,} observed cells, "
            f"{a4['panel']['cbo']} CBO4 codes, "
            f"{a4['panel']['municipalities']} municipalities, and "
            f"{a4['panel']['periods']} months. It retains only exposed and "
            "`Not Exposed` occupations."
        ),
        "",
        *_markdown_table(
            cut_table,
            [
                "construction",
                "municipalities",
                "high_municipalities",
                "low_municipalities",
                "high_share",
                "low_share",
            ],
        ),
        "",
        "## A5 — December 2021 placebo",
        "",
        (
            "All placebo models are OLS with "
            "`cbo_municipio + cbo_periodo + uf_periodo` fixed effects and "
            "municipality-clustered inference. The sample ends in November "
            "2022; no true-post month enters."
        ),
        "",
        "Corrected within-sample cut (the gate specification):",
        "",
        *_markdown_table(
            placebo_view,
            [
                "outcome",
                "coefficient",
                "standard_error",
                "p_value",
                "n_obs",
            ],
        ),
        "",
        "Corrected vintage with the reconstructed old national cut:",
        "",
        *_markdown_table(
            placebo_old_view,
            ["outcome", "coefficient", "p_value"],
        ),
        "",
        (
            "V1 comparator: admissions +0.0469*** and separations "
            "+0.0509***. The V1 placebo was not restricted to the true "
            "pre-period, so it is a historical failure marker rather than an "
            "exact sample-matched benchmark."
        ),
        "",
        "## A5 — triple-interaction pretrends",
        "",
        (
            "The model uses only t = -23 through t = -1, with November 2022 "
            "as the omitted reference. Classification is imported from "
            "`V2/code/caged/models/pretrends.py`; the covariance PSD flag is "
            "preserved."
        ),
        "",
        "Corrected within-sample cut:",
        "",
        *_markdown_table(
            pretrend_view,
            [
                "outcome",
                "joint_lead_p_value",
                "linear_pretrend_p_value",
                "dynamic_pre_p_lt_005",
                "lead_covariance_positive_semidefinite",
                "pretrend_status",
            ],
        ),
        "",
        "Corrected vintage with reconstructed old cut:",
        "",
        *_markdown_table(
            pretrend_old_view,
            [
                "outcome",
                "joint_lead_p_value",
                "linear_pretrend_p_value",
                "dynamic_pre_p_lt_005",
                "pretrend_status",
            ],
        ),
        "",
        "V1 comparator: all four interaction pretrends had p approximately "
        "zero.",
        "",
        "## A-G1 decision",
        "",
        (
            f"- All four placebo p-values are at least 0.05: "
            f"`{str(gate['criteria']['placebo_all_outcomes']).lower()}`."
        ),
        (
            f"- At least one pretrend is not `fail`: "
            f"`{str(gate['criteria']['pretrend_any_non_fail']).lower()}`."
        ),
        (
            f"- Low-connectivity municipalities are at least 30%: "
            f"`{str(gate['criteria']['low_connectivity_at_least_30_percent']).lower()}` "
            f"({100 * a4['connectivity_cut']['low_share']:.3f}%)."
        ),
        "",
        f"Therefore A-G1 is **{status}**.",
        "",
        "## Mechanical cause attribution",
        "",
        (
            "Under the rule frozen before estimation, the Stage 0 supports "
            f"**{_cause_label(attribution['conclusion'])}**."
        ),
        "",
        (
            f"- Vintage-supporting flow placebo changes: "
            f"`{', '.join(attribution['vintage_placebo_changes']) or 'none'}`."
        ),
        (
            f"- Cut-supporting placebo changes: "
            f"`{', '.join(attribution['cut_placebo_changes']) or 'none'}`."
        ),
        (
            f"- Cut-supporting pretrend improvements: "
            f"`{', '.join(attribution['cut_pretrend_improvements']) or 'none'}`."
        ),
        "",
        "The differential late-declaration shares are descriptive mechanism "
        "evidence. They do not override the preregistered attribution rule.",
        "",
        "## Destination and interpretation",
        "",
        (
            "The real DDD is NOT EXECUTED because A-G1 closed. The documented "
            "negative belongs in the Section 6.4 research agenda."
            if not gate["opens"]
            else (
                "This run stops at A-G1. A1 remains unresolved by the author, "
                "Family F is authorized by the open gate but has not been "
                "instantiated, and no DDD result is available. The front "
                "remains capped at an appendix or the Section 6.4 agenda."
            )
        ),
        "",
        "No causal claim follows from Stage 0.",
        "",
    ]
    return "\n".join(lines)


def execute_stage0() -> dict[str, Any]:
    columns = [
        "cbo_4d",
        "id_municipio",
        "periodo_num",
        "event_time",
        "treated",
        "high_connectivity",
        "high_connectivity_old_national",
        "cbo_municipio",
        "cbo_periodo",
        "uf_periodo",
        *OUTCOMES,
    ]
    panel = pd.read_parquet(PANEL_PATH, columns=columns)
    placebo, placebo_support = run_placebos(
        panel,
        cut="within_sample",
        high_column="high_connectivity",
    )
    atomic_csv(placebo, PLACEBO_PATH)
    placebo_old, placebo_old_support = run_placebos(
        panel,
        cut="old_national",
        high_column="high_connectivity_old_national",
    )
    atomic_csv(placebo_old, PLACEBO_OLD_PATH)
    atomic_json(
        {
            "within_sample": placebo_support,
            "old_national": placebo_old_support,
            "real_treatment_coefficient_estimated": False,
        },
        PLACEBO_SUPPORT_PATH,
    )
    pretrends = run_pretrends(
        panel,
        cut="within_sample",
        high_column="high_connectivity",
        coefficient_path=PRETREND_COEFFICIENTS_PATH,
    )
    atomic_csv(pretrends, PRETRENDS_PATH)
    pretrends_old = run_pretrends(
        panel,
        cut="old_national",
        high_column="high_connectivity_old_national",
        coefficient_path=PRETREND_COEFFICIENTS_OLD_PATH,
    )
    atomic_csv(pretrends_old, PRETRENDS_OLD_PATH)
    a2 = json.loads(A2_SUPPORT_PATH.read_text(encoding="utf-8"))
    a3 = json.loads(A3_SUPPORT_PATH.read_text(encoding="utf-8"))
    a4 = json.loads(A4_SUPPORT_PATH.read_text(encoding="utf-8"))
    cut_table = pd.read_csv(A4_SUPPORT_CSV)
    late = pd.read_csv(LATE_BY_CONNECTIVITY_PATH)
    gate = evaluate_gate_a_g1(
        placebo,
        pretrends,
        low_connectivity_share=a4["connectivity_cut"]["low_share"],
    )
    v1_placebo = pd.DataFrame(
        {
            "outcome": ["ln_admissoes", "ln_desligamentos"],
            "coefficient": [0.0469, 0.0509],
            "p_value": [0.0, 0.0],
        }
    )
    attribution = attribute_stage0_causes(
        v1_placebo=v1_placebo,
        corrected_old_cut_placebo=placebo_old,
        corrected_new_cut_placebo=placebo,
        corrected_old_cut_pretrends=pretrends_old,
        corrected_new_cut_pretrends=pretrends,
    )
    atomic_json(attribution, CAUSE_PATH)
    status = {
        "status": (
            "gate_open_stopped_at_a_g1"
            if gate["opens"]
            else "not_executed_falsification_failed"
        ),
        "gate": "A-G1",
        "gate_opens": gate["opens"],
        "criteria": gate["criteria"],
        "failed_criteria": gate["failed_criteria"],
        "placebo_p_values": _p_values(placebo),
        "pretrend_statuses": _statuses(pretrends),
        "pretrend_covariance_psd": {
            str(row.outcome): bool(
                row.lead_covariance_positive_semidefinite
            )
            for row in pretrends[
                ["outcome", "lead_covariance_positive_semidefinite"]
            ].itertuples(index=False)
        },
        "low_connectivity_share": a4["connectivity_cut"]["low_share"],
        "cause_attribution": attribution,
        "real_treatment_coefficient_estimated": False,
        "family_f_authorized_by_gate": bool(gate["opens"]),
        "family_f_instantiated": False,
        "a1_resolved": False,
        "stopped_at_gate_as_requested": True,
        "destination": (
            "section_6_4_research_agenda"
            if not gate["opens"]
            else "appendix_or_section_6_4_research_agenda"
        ),
    }
    atomic_json(status, STATUS_PATH)
    report = _build_report(
        a2=a2,
        a3=a3,
        a4=a4,
        cut_table=cut_table,
        late=late,
        placebo=placebo,
        placebo_old=placebo_old,
        pretrends=pretrends,
        pretrends_old=pretrends_old,
        gate=gate,
        attribution=attribution,
    )
    atomic_text(report, REPORT_PATH)
    scorecard = pd.DataFrame(
        [
            {
                "frente": "anatel",
                "momento": "stage0",
                "fecha_limitacao_declarada": "nao",
                "gate_aquisicao": "pass",
                "gate_construcao": "pass",
                "falsificacao": (
                    "pass"
                    if gate["criteria"]["placebo_all_outcomes"]
                    else "fail"
                ),
                "pretrend": _best_pretrend_status(pretrends),
                "suporte": (
                    "adequate"
                    if gate["criteria"][
                        "low_connectivity_at_least_30_percent"
                    ]
                    else "thin"
                ),
                "familia_bh": "none",
                "barra_reprodutibilidade": "pass",
                "custo_estrutural": "apendice",
                "veredito": (
                    "apendice" if gate["opens"] else "agenda"
                ),
                "veredito_derivado_de": (
                    "gate_aquisicao;gate_construcao;falsificacao;"
                    "pretrend;suporte;custo_estrutural"
                ),
            }
        ]
    )
    atomic_csv(scorecard, SCORECARD_PATH)
    del panel
    gc.collect()
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    status = execute_stage0()
    print(json.dumps(status, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
