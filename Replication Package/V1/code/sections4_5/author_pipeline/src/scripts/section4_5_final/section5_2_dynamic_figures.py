#!/usr/bin/env python3
"""Build experimental dynamic figures for national and demographic results.

The module keeps descriptive exposed-versus-unexposed paths separate from
dynamic DiD/DDD inference. It intentionally writes to an experimental bundle
and does not modify the curated Section 4/5 package manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from section4_5_final.section5_2_tables import (  # noqa: E402
    HETEROGENEITY_SPECS,
    OUTCOME_LABELS,
    OUTCOME_ORDER,
)
from section4_5_final.style import (  # noqa: E402
    GRID,
    OUTCOME_COLORS,
    TEXT_DARK,
    TEXT_MUTED,
    get_pyplot,
    save_figure,
    setup_plot_style,
)
from section4_event_study.config import CONTROL_COLUMNS  # noqa: E402


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = ROOT / "outputs" / "section4_5_final" / "experimental" / "section5_2_dynamic"
MICRO_CACHE_PATH = ROOT / "data" / "processed" / "section5_2_dynamic_micro_pairs.parquet"
MICRO_CACHE_VERSION = "section5_2_dynamic_micro_pairs_v1"

EVENT_MIN = -12
EVENT_MAX = 24
REFERENCE_PERIOD = -1
PRE_MIN = -12
PRE_MAX = -1
EVENT_TIMES = list(range(EVENT_MIN, EVENT_MAX + 1))
WINDOW_RULE = "strict_no_tail_binning"

PATH_ROLES = ["treated", "control"]
SUBGROUPS = ["target", "complement"]

DIMENSION_LABELS = {
    "national": "Nacional",
    "sex": "Sexo",
    "income": "Renda pré-tratamento",
    "age_canaries": "Idade — coortes Canaries",
    "race_color": "Raça/cor",
    "education": "Escolaridade",
}

GROUP_PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#6A51A3"]
AGE_COLORS = {
    "age_22_25": "#0072B2",
    "age_26_30": "#E69F00",
    "age_31_34": "#009E73",
    "age_35_40": "#CC79A7",
    "age_41_49": "#D55E00",
    "age_50_plus": "#6A51A3",
}

OUTCOME_FILE_STEMS = {
    "ln_admissoes": "admissions",
    "ln_desligamentos": "separations",
    "ln_salario_real_adm": "real_admission_wage",
}

OUTCOME_LOWER_LABELS = {
    "ln_admissoes": "admissões",
    "ln_desligamentos": "desligamentos",
    "ln_salario_real_adm": "salário real de admissão",
}


def _event_suffix(t: int) -> str:
    return f"tm{-t}" if t < 0 else f"t{t}"


def _classify_pretrend(n_pre_p_lt_005: int, joint_p_value: float) -> str:
    if pd.isna(joint_p_value):
        return "warning"
    if joint_p_value < 0.05 or n_pre_p_lt_005 >= 2:
        return "fail"
    if n_pre_p_lt_005 == 0 and joint_p_value > 0.10:
        return "pass"
    return "warning"


def _parse_wald_result(result: object) -> tuple[float, float]:
    statistic = np.nan
    p_value = np.nan
    items = result.items() if hasattr(result, "items") else []
    for key, value in items:
        key_text = str(key).lower()
        if "p" in key_text:
            p_value = float(value)
        if ("stat" in key_text or "wald" in key_text) and not pd.isna(value):
            statistic = float(value)
    return statistic, p_value


def _joint_pretrend(model: object, pre_terms: list[str]) -> tuple[float, float, str]:
    if not pre_terms:
        return np.nan, np.nan, "not_available_no_pre_terms"
    coefficient_names = list(model.coef().index)
    try:
        restriction = np.zeros((len(pre_terms), len(coefficient_names)))
        for row_index, term in enumerate(pre_terms):
            restriction[row_index, coefficient_names.index(term)] = 1.0
        result = model.wald_test(R=restriction, q=np.zeros(len(pre_terms)), distribution="chi2")
        statistic, p_value = _parse_wald_result(result)
        if not pd.isna(p_value):
            return statistic, p_value, "wald_test_R_beta_eq_q_chi2"
        return statistic, p_value, "wald_test_returned_no_p_value"
    except Exception as exc:  # noqa: BLE001 - preserve diagnostics in the output
        return np.nan, np.nan, f"wald_test_failed: {exc}"


def _dynamic_terms(
    data: pd.DataFrame,
    event_times: list[int],
    estimand: str,
) -> tuple[pd.DataFrame, dict[int, dict[str, str]]]:
    out = data.copy()
    term_map: dict[int, dict[str, str]] = {}
    columns: dict[str, pd.Series] = {}
    if estimand == "ddd":
        if "group_indicator" not in out.columns:
            raise RuntimeError("DDD data must contain group_indicator.")
        out["group_indicator"] = pd.to_numeric(out["group_indicator"], errors="raise").astype(int)
        out["treat_group"] = out["scenario_treat"].astype(int) * out["group_indicator"]
    for t in event_times:
        if t == REFERENCE_PERIOD:
            continue
        at_t = out["t"].eq(t).astype("int8")
        suffix = _event_suffix(t)
        if estimand == "did":
            did_term = f"did_{suffix}"
            columns[did_term] = (at_t * out["scenario_treat"].astype(int)).astype("int8")
            term_map[t] = {"effect": did_term}
        elif estimand == "ddd":
            group_term = f"group_{suffix}"
            did_term = f"did_{suffix}"
            ddd_term = f"ddd_{suffix}"
            columns[group_term] = (at_t * out["group_indicator"]).astype("int8")
            columns[did_term] = (at_t * out["scenario_treat"].astype(int)).astype("int8")
            columns[ddd_term] = (at_t * out["treat_group"]).astype("int8")
            term_map[t] = {"group": group_term, "did": did_term, "effect": ddd_term}
        else:
            raise ValueError(f"Unsupported dynamic estimand: {estimand}")
    return pd.concat([out, pd.DataFrame(columns, index=out.index)], axis=1), term_map


def _model_sample_counts(model: object, data: pd.DataFrame) -> tuple[int, int, str]:
    """Report post-singleton counts when PyFixest stores them, with an auditable fallback."""
    n_obs = getattr(model, "_N", None)
    model_data = getattr(model, "_data", None)
    if n_obs is not None and isinstance(model_data, pd.DataFrame) and "cbo_4d" in model_data.columns:
        return int(n_obs), int(model_data["cbo_4d"].nunique()), "pyfixest_retained_sample"
    return int(len(data)), int(data["cbo_4d"].nunique()), "input_sample_fallback"


def _estimate_dynamic(
    panel: pd.DataFrame,
    *,
    dimension: str,
    group_id: str,
    group_label: str,
    outcome: str,
    estimand: str,
    event_times: list[int] | None,
    control_columns: list[str] | None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    if outcome not in OUTCOME_ORDER:
        raise ValueError(f"Unsupported dynamic outcome: {outcome}")
    times = EVENT_TIMES if event_times is None else list(event_times)
    controls = CONTROL_COLUMNS if control_columns is None else list(control_columns)
    data, term_map = _dynamic_terms(panel, times, estimand)
    effect_terms = [term_map[t]["effect"] for t in times if t != REFERENCE_PERIOD]
    if estimand == "ddd":
        dynamic_rhs = [name for t in times if t != REFERENCE_PERIOD for name in term_map[t].values()]
        has_subgroups = "subgroup" in data.columns and data["subgroup"].notna().any()
        if has_subgroups:
            dynamic_rhs.append("treat_group")
            fixed_effects = "cbo_4d + periodo + subgroup"
        else:
            fixed_effects = "cbo_4d + periodo"
    else:
        dynamic_rhs = effect_terms
        fixed_effects = "cbo_4d + periodo"
    required = [outcome, "cbo_4d", "periodo", "scenario_treat", *controls]
    if estimand == "ddd":
        required.append("group_indicator")
    data = data.dropna(subset=required).copy()
    rhs = [*dynamic_rhs, *controls]
    formula = f"{outcome} ~ {' + '.join(rhs)} | {fixed_effects}"
    model = pf.feols(formula, data=data, vcov={"CRV1": "cbo_4d"})
    coefs = model.coef()
    ses = model.se()
    pvalues = model.pvalue()
    coefficient_names = set(coefs.index)
    n_obs, n_cbo, sample_count_source = _model_sample_counts(model, data)

    rows: list[dict[str, object]] = []
    for t in times:
        if t == REFERENCE_PERIOD:
            estimate = {
                "coef": 0.0,
                "se": 0.0,
                "p_value": np.nan,
                "ci_low": 0.0,
                "ci_high": 0.0,
                "coefficient_status": "reference",
            }
        else:
            term = term_map[t]["effect"]
            if term in coefficient_names:
                coef = float(coefs.loc[term])
                se = float(ses.loc[term])
                estimate = {
                    "coef": coef,
                    "se": se,
                    "p_value": float(pvalues.loc[term]),
                    "ci_low": coef - 1.96 * se,
                    "ci_high": coef + 1.96 * se,
                    "coefficient_status": "estimated",
                }
            else:
                estimate = {
                    "coef": np.nan,
                    "se": np.nan,
                    "p_value": np.nan,
                    "ci_low": np.nan,
                    "ci_high": np.nan,
                    "coefficient_status": "omitted",
                }
        rows.append(
            {
                "dimension": dimension,
                "group_id": group_id,
                "group_label": group_label,
                "outcome": outcome,
                "outcome_label": OUTCOME_LABELS[outcome],
                "estimand": estimand,
                "window_rule": WINDOW_RULE,
                "t": t,
                "is_reference": t == REFERENCE_PERIOD,
                "is_pre": t < 0 and t != REFERENCE_PERIOD,
                "result_status": "estimated",
                "n_obs_input": int(len(data)),
                "n_obs": n_obs,
                "n_cbo": n_cbo,
                "sample_count_source": sample_count_source,
                "formula": formula,
                "error": "",
                **estimate,
            }
        )

    pre_terms = [
        term_map[t]["effect"]
        for t in times
        if t < 0 and t != REFERENCE_PERIOD and term_map[t]["effect"] in coefficient_names
    ]
    pre_pvalues = pd.Series(pvalues).reindex(pre_terms).astype(float)
    statistic, joint_p_value, method = _joint_pretrend(model, pre_terms)
    n_pre_p_lt_005 = int((pre_pvalues < 0.05).sum())
    pretrend = {
        "dimension": dimension,
        "group_id": group_id,
        "group_label": group_label,
        "outcome": outcome,
        "outcome_label": OUTCOME_LABELS[outcome],
        "estimand": estimand,
        "window_rule": WINDOW_RULE,
        "result_status": "estimated",
        "n_obs_input": int(len(data)),
        "n_obs": n_obs,
        "n_cbo": n_cbo,
        "sample_count_source": sample_count_source,
        "n_pre_coefficients": len(pre_terms),
        "n_pre_p_lt_005": n_pre_p_lt_005,
        "joint_statistic": statistic,
        "joint_p_value": joint_p_value,
        "joint_test_method": method,
        "pretrend_status": _classify_pretrend(n_pre_p_lt_005, joint_p_value),
        "formula": formula,
        "error": "",
    }
    return pd.DataFrame(rows), pretrend


def estimate_dynamic_did(
    panel: pd.DataFrame,
    *,
    dimension: str,
    group_id: str,
    group_label: str,
    outcome: str,
    event_times: list[int] | None = None,
    control_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Estimate a national dynamic DiD with ``t=-1`` omitted."""
    return _estimate_dynamic(
        panel,
        dimension=dimension,
        group_id=group_id,
        group_label=group_label,
        outcome=outcome,
        estimand="did",
        event_times=event_times,
        control_columns=control_columns,
    )


def estimate_dynamic_ddd(
    panel: pd.DataFrame,
    *,
    dimension: str,
    group_id: str,
    group_label: str,
    outcome: str,
    event_times: list[int] | None = None,
    control_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Estimate a target-versus-complement dynamic DDD with ``t=-1`` omitted."""
    return _estimate_dynamic(
        panel,
        dimension=dimension,
        group_id=group_id,
        group_label=group_label,
        outcome=outcome,
        estimand="ddd",
        event_times=event_times,
        control_columns=control_columns,
    )


def safely_estimate_dynamic(
    panel: pd.DataFrame,
    *,
    dimension: str,
    group_id: str,
    group_label: str,
    outcome: str,
    estimand: str,
    event_times: list[int] | None = None,
    control_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Estimate a model while retaining a complete, auditable failure grid."""
    times = EVENT_TIMES if event_times is None else list(event_times)
    try:
        support = support_diagnostics(panel, outcome)
    except Exception:  # noqa: BLE001 - the model error remains visible below
        support = {"power_status": "thin", "treated_cbo": 0, "control_cbo": 0}
    try:
        estimator = {"did": estimate_dynamic_did, "ddd": estimate_dynamic_ddd}[estimand]
        coefficients, pretrend = estimator(
            panel,
            dimension=dimension,
            group_id=group_id,
            group_label=group_label,
            outcome=outcome,
            event_times=times,
            control_columns=control_columns,
        )
        for key, value in support.items():
            coefficients[key] = value
            pretrend[key] = value
        return coefficients, pretrend
    except Exception as exc:  # noqa: BLE001 - failed models must remain in the bundle
        error = str(exc)
        rows = []
        for t in times:
            is_reference = t == REFERENCE_PERIOD
            rows.append(
                {
                    "dimension": dimension,
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "estimand": estimand,
                    "window_rule": WINDOW_RULE,
                    "t": t,
                    "is_reference": is_reference,
                    "is_pre": t < 0 and not is_reference,
                    "result_status": "failed_estimation",
                    "n_obs_input": int(len(panel)),
                    "n_obs": 0,
                    "n_cbo": 0,
                    "sample_count_source": "not_available",
                    "formula": "",
                    "error": error,
                    "coef": 0.0 if is_reference else np.nan,
                    "se": 0.0 if is_reference else np.nan,
                    "p_value": np.nan,
                    "ci_low": 0.0 if is_reference else np.nan,
                    "ci_high": 0.0 if is_reference else np.nan,
                    "coefficient_status": "reference" if is_reference else "not_estimated",
                    **support,
                }
            )
        pretrend = {
            "dimension": dimension,
            "group_id": group_id,
            "group_label": group_label,
            "outcome": outcome,
            "outcome_label": OUTCOME_LABELS[outcome],
            "estimand": estimand,
            "window_rule": WINDOW_RULE,
            "result_status": "failed_estimation",
            "n_obs_input": int(len(panel)),
            "n_obs": 0,
            "n_cbo": 0,
            "sample_count_source": "not_available",
            "n_pre_coefficients": 0,
            "n_pre_p_lt_005": 0,
            "joint_statistic": np.nan,
            "joint_p_value": np.nan,
            "joint_test_method": "not_available_failed_estimation",
            "pretrend_status": "not_available",
            "formula": "",
            "error": error,
            **support,
        }
        return pd.DataFrame(rows), pretrend


def expected_contract_counts() -> dict[str, int]:
    """Return the fixed artifact and long-data contracts for this bundle."""
    heterogeneity_groups = sum(len(spec["groups"]) for spec in HETEROGENEITY_SPECS.values())
    models = len(OUTCOME_ORDER) * (1 + heterogeneity_groups)
    dimensions = 1 + len(HETEROGENEITY_SPECS)
    return {
        "models": models,
        "coefficient_rows": models * len(EVENT_TIMES),
        "pretrend_rows": models,
        "path_rows": (1 + heterogeneity_groups) * len(OUTCOME_ORDER) * len(PATH_ROLES) * len(EVENT_TIMES),
        "figures": dimensions * len(OUTCOME_ORDER) * 2,
    }


def expected_model_specs() -> list[dict[str, str]]:
    """Enumerate the 63 national and heterogeneity model contracts."""
    specs: list[dict[str, str]] = []
    for outcome in OUTCOME_ORDER:
        specs.append(
            {
                "dimension": "national",
                "group_id": "national",
                "group_label": "Nacional",
                "outcome": outcome,
                "estimand": "did",
            }
        )
    for dimension in ["sex", "income", "age_canaries", "race_color", "education"]:
        for group_id, group_label in _dimension_groups(dimension):
            for outcome in OUTCOME_ORDER:
                specs.append(
                    {
                        "dimension": dimension,
                        "group_id": group_id,
                        "group_label": group_label,
                        "outcome": outcome,
                        "estimand": "ddd",
                    }
                )
    return specs


def expected_figure_filenames() -> list[str]:
    """Return deterministic names for the 36 experimental PNGs."""
    filenames = []
    for dimension in ["national", "sex", "income", "age_canaries", "race_color", "education"]:
        for outcome in OUTCOME_ORDER:
            stem = OUTCOME_FILE_STEMS[outcome]
            filenames.extend(
                [
                    f"figure_experimental_s5_2_{dimension}_{stem}_event_study.png",
                    f"figure_experimental_s5_2_{dimension}_{stem}_paths.png",
                ]
            )
    return filenames


def support_diagnostics(panel: pd.DataFrame, outcome: str) -> dict[str, int | str]:
    """Classify target-group CBO support using the Section 5.2 thresholds."""
    if outcome not in OUTCOME_ORDER:
        raise ValueError(f"Unsupported support outcome: {outcome}")
    required = {"cbo_4d", "scenario_role", outcome}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Support panel is missing columns: {missing}")
    data = panel.copy()
    if "subgroup" in data.columns:
        data = data[data["subgroup"].eq("target")].copy()
    elif "group_indicator" in data.columns:
        data = data[pd.to_numeric(data["group_indicator"], errors="coerce").eq(1)].copy()
    if outcome in {"ln_admissoes", "ln_desligamentos"}:
        flow_columns = [column for column in ["admissoes", "desligamentos"] if column in data.columns]
        if flow_columns:
            flow = data[flow_columns].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
            supported = data.assign(_has_support=flow.gt(0)).groupby("cbo_4d", observed=True)["_has_support"].any()
        else:
            supported = data.groupby("cbo_4d", observed=True)[outcome].apply(lambda values: values.notna().any())
    else:
        supported = data.groupby("cbo_4d", observed=True)[outcome].apply(lambda values: values.notna().any())
    supported_cbo = set(supported[supported].index.astype(str))
    data = data[data["cbo_4d"].astype(str).isin(supported_cbo)]
    roles = data[["cbo_4d", "scenario_role"]].drop_duplicates()
    treated = int(roles[roles["scenario_role"].eq("treated")]["cbo_4d"].nunique())
    control = int(roles[roles["scenario_role"].eq("control")]["cbo_4d"].nunique())
    if treated >= 20 and control >= 50:
        status = "adequate"
    elif treated >= 10 and control >= 25:
        status = "limited"
    else:
        status = "thin"
    return {"power_status": status, "treated_cbo": treated, "control_cbo": control}


def validate_long_frames(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> None:
    """Validate exact long-data contracts before any bundle is accepted."""
    expected = expected_contract_counts()
    frames = {"coefficients": coefficients, "pretrends": pretrends, "paths": paths}
    for name, frame in frames.items():
        if "outcome" not in frame.columns:
            raise RuntimeError(f"{name} is missing outcome.")
        outcomes = set(frame["outcome"].dropna().astype(str))
        if any("salario_real_desl" in outcome or "dismissal_wage" in outcome for outcome in outcomes):
            raise RuntimeError(f"{name} contains a forbidden dismissal wage outcome.")
        if outcomes != set(OUTCOME_ORDER):
            raise RuntimeError(f"{name} outcomes differ from the three-outcome contract: {sorted(outcomes)}")
    if len(coefficients) != expected["coefficient_rows"]:
        raise RuntimeError(f"Coefficient row count is {len(coefficients)}; expected {expected['coefficient_rows']}.")
    if len(pretrends) != expected["pretrend_rows"]:
        raise RuntimeError(f"Pretrend row count is {len(pretrends)}; expected {expected['pretrend_rows']}.")
    if len(paths) != expected["path_rows"]:
        raise RuntimeError(f"Path row count is {len(paths)}; expected {expected['path_rows']}.")

    coefficient_keys = ["dimension", "group_id", "outcome", "t"]
    pretrend_keys = ["dimension", "group_id", "outcome"]
    path_keys = ["dimension", "group_id", "outcome", "scenario_role", "t"]
    if coefficients.duplicated(coefficient_keys).any():
        raise RuntimeError("Coefficient grid contains duplicate model-event cells.")
    if pretrends.duplicated(pretrend_keys).any():
        raise RuntimeError("Pretrend grid contains duplicate models.")
    if paths.duplicated(path_keys).any():
        raise RuntimeError("Path grid contains duplicate group-role-event cells.")
    if set(pd.to_numeric(coefficients["t"], errors="coerce")) != set(EVENT_TIMES):
        raise RuntimeError("Coefficient grid does not cover the full event window.")
    if set(pd.to_numeric(paths["t"], errors="coerce")) != set(EVENT_TIMES):
        raise RuntimeError("Path grid does not cover the full event window.")
    if set(paths["scenario_role"]) != set(PATH_ROLES):
        raise RuntimeError("Path grid must contain exactly treated and control roles.")
    reference = coefficients[coefficients["t"].eq(REFERENCE_PERIOD)]
    if len(reference) != expected["models"] or not np.allclose(
        pd.to_numeric(reference["coef"], errors="coerce"), 0.0, equal_nan=False
    ):
        raise RuntimeError("Every model must contain a zero coefficient at t=-1.")


def add_winsorized_wage_path(
    panel: pd.DataFrame,
    *,
    wage_column: str,
    bounds: tuple[float, float] | None = None,
    lower_q: float = 0.01,
    upper_q: float = 0.99,
) -> pd.DataFrame:
    """Add a winsorized wage field used only for descriptive paths."""
    if not 0 <= lower_q < upper_q <= 1:
        raise ValueError("Wage quantiles must satisfy 0 <= lower < upper <= 1.")
    required = {wage_column, "indice", "ln_salario_real_adm"}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Cannot build wage paths; missing columns: {missing}")
    out = panel.copy()
    wages = pd.to_numeric(out[wage_column], errors="coerce").where(lambda values: values.gt(0))
    if bounds is None:
        lower, upper = wages.quantile([lower_q, upper_q]).astype(float)
    else:
        lower, upper = map(float, bounds)
    if not np.isfinite(lower) or not np.isfinite(upper) or lower <= 0 or upper <= lower:
        raise RuntimeError(f"Invalid wage winsorization bounds: lower={lower}, upper={upper}.")
    out["salario_adm_path"] = wages.clip(lower=lower, upper=upper)
    out["salario_real_adm_path"] = out["salario_adm_path"] * (100.0 / out["indice"])
    out["ln_salario_real_adm_path"] = np.log(
        out["salario_real_adm_path"].where(out["salario_real_adm_path"].gt(0))
    )
    out.attrs["wage_path_bounds"] = (lower, upper)
    return out


def figure_layout(group_count: int) -> tuple[int, int, tuple[float, float]]:
    """Return the publication layout for a dimension's group count."""
    layouts = {
        1: (1, 1, (8.2, 5.4)),
        2: (1, 2, (12.0, 5.4)),
        3: (1, 3, (13.8, 5.0)),
        6: (2, 3, (13.8, 8.2)),
    }
    if group_count not in layouts:
        raise ValueError(f"Unsupported figure group count: {group_count}")
    return layouts[group_count]


def _dimension_groups(dimension: str) -> list[tuple[str, str]]:
    if dimension == "national":
        return [("national", "Nacional")]
    if dimension not in HETEROGENEITY_SPECS:
        raise KeyError(f"Unknown Section 5.2 figure dimension: {dimension}")
    return list(HETEROGENEITY_SPECS[dimension]["groups"])


def _group_color(dimension: str, group_id: str, outcome: str) -> str:
    if dimension == "national":
        return OUTCOME_COLORS[outcome]
    if dimension == "age_canaries":
        return AGE_COLORS[group_id]
    order = [item[0] for item in _dimension_groups(dimension)]
    return GROUP_PALETTE[order.index(group_id)]


def _lighten_color(hex_color: str, amount: float = 0.58) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    rgb = np.array([int(value[index : index + 2], 16) / 255.0 for index in (0, 2, 4)])
    return tuple(rgb + (1.0 - rgb) * amount)


def _status_pt(status: str) -> str:
    return {
        "pass": "aprovado",
        "warning": "com alerta",
        "fail": "reprovado",
        "not_available": "não disponível",
    }.get(status, status)


def plot_event_study_panels(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    *,
    dimension: str,
    outcome: str,
    output_path: Path,
) -> None:
    """Render dynamic DiD/DDD panels in the experimental reference style."""
    groups = _dimension_groups(dimension)
    rows, columns, figsize = figure_layout(len(groups))
    plt = get_pyplot()
    setup_plot_style()
    fig, axes = plt.subplots(rows, columns, figsize=figsize, sharex=True, sharey=True, squeeze=False)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.78, bottom=0.20, hspace=0.42, wspace=0.20)
    flat_axes = list(axes.flat)

    bounds = coefficients[["ci_low", "ci_high"]].apply(pd.to_numeric, errors="coerce").to_numpy().ravel()
    bounds = bounds[np.isfinite(bounds)]
    max_abs = max(0.05, float(np.abs(bounds).max()) if bounds.size else 0.05)
    ylim = (-1.06 * max_abs, 1.06 * max_abs)

    for axis, (group_id, group_label) in zip(flat_axes, groups):
        color = _group_color(dimension, group_id, outcome)
        view = coefficients[
            coefficients["group_id"].eq(group_id)
            & coefficients["coefficient_status"].isin(["estimated", "reference"])
        ].sort_values("t")
        diagnostic = pretrends[pretrends["group_id"].eq(group_id)]
        pretrend_status = "not_available" if diagnostic.empty else str(diagnostic.iloc[0]["pretrend_status"])
        power_status = "not_available" if diagnostic.empty else str(diagnostic.iloc[0].get("power_status", "not_available"))
        axis.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.7, zorder=0)
        axis.axhline(0, color="#333333", linewidth=0.9, zorder=1)
        axis.axvline(REFERENCE_PERIOD, color="#777777", linewidth=0.8, linestyle="--", zorder=1)
        axis.axvline(0, color="#999999", linewidth=0.8, linestyle=":", zorder=1)
        if view.empty:
            axis.text(0.5, 0.5, "não estimado", transform=axis.transAxes, ha="center", va="center", color=TEXT_MUTED)
        else:
            axis.plot(
                view["t"].astype(float),
                view["coef"].astype(float),
                color=color,
                linewidth=1.9,
                marker="o",
                markersize=2.8,
                zorder=3,
            )
            band = view.dropna(subset=["ci_low", "ci_high"])
            axis.fill_between(
                band["t"].astype(float).to_numpy(),
                band["ci_low"].astype(float).to_numpy(),
                band["ci_high"].astype(float).to_numpy(),
                color=color,
                alpha=0.16,
                zorder=2,
            )
        axis.set_title(group_label, loc="left", color=color, fontweight="bold", fontsize=11)
        axis.text(
            0.99,
            0.97,
            f"pretrend: {_status_pt(pretrend_status)} | poder: {power_status}",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=7.5,
            color=TEXT_MUTED,
        )
        axis.set_xlim(EVENT_MIN, EVENT_MAX)
        axis.set_ylim(*ylim)
        axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
        axis.grid(axis="x", visible=False)
    for axis in flat_axes[len(groups) :]:
        axis.set_visible(False)

    estimand = "DiD" if dimension == "national" else "DDD"
    fig.suptitle(
        f"Figura experimental: Event study {estimand} de {OUTCOME_LOWER_LABELS[outcome]} — {DIMENSION_LABELS[dimension]}",
        x=0.09,
        y=0.96,
        ha="left",
        fontsize=14.5,
        fontweight="bold",
        color=TEXT_DARK,
    )
    subtitle = (
        "Exposed vs Not Exposed × tempo de evento."
        if dimension == "national"
        else "Exposed vs Not Exposed × subgrupo vs complemento × tempo de evento."
    )
    fig.text(0.09, 0.88, subtitle, ha="left", va="top", fontsize=9.3, color=TEXT_MUTED)
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0); referência: t=-1", y=0.105, fontsize=10)
    fig.supylabel(f"Coeficiente {estimand} em {OUTCOME_LABELS[outcome].lower()}", x=0.02, fontsize=10)
    fig.text(
        0.09,
        0.025,
        "Nota: IC pontual de 95%; pretrend é o teste conjunto em t=-12,...,-2; "
        "efeitos fixos e controles da especificação principal; erros-padrão clusterizados por CBO.\n"
        "Sem correção por testes múltiplos; janela estrita, sem agrupar caudas. "
        "Painéis com pretrend falho ou poder thin são exploratórios.",
        ha="left",
        va="bottom",
        fontsize=7.7,
        color=TEXT_MUTED,
    )
    save_figure(fig, output_path)


def plot_path_panels(
    paths: pd.DataFrame,
    *,
    dimension: str,
    outcome: str,
    output_path: Path,
) -> None:
    """Render exposed-versus-unexposed descriptive paths."""
    groups = _dimension_groups(dimension)
    rows, columns, figsize = figure_layout(len(groups))
    plt = get_pyplot()
    setup_plot_style()
    fig, axes = plt.subplots(rows, columns, figsize=figsize, sharex=True, sharey=True, squeeze=False)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.78, bottom=0.20, hspace=0.40, wspace=0.20)
    flat_axes = list(axes.flat)
    values = pd.to_numeric(paths["path_index"], errors="coerce").dropna()
    lower = min(float(values.min()), 100.0) if not values.empty else 95.0
    upper = max(float(values.max()), 100.0) if not values.empty else 105.0
    padding = max(2.0, 0.08 * max(upper - lower, 1.0))

    for axis, (group_id, group_label) in zip(flat_axes, groups):
        color = _group_color(dimension, group_id, outcome)
        control_color = _lighten_color(color)
        view = paths[paths["group_id"].eq(group_id)]
        treated = view[view["scenario_role"].eq("treated") & view["path_status"].eq("estimated")].sort_values("t")
        control = view[view["scenario_role"].eq("control") & view["path_status"].eq("estimated")].sort_values("t")
        axis.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.7, zorder=0)
        axis.axhline(100, color=GRID, linewidth=0.9, zorder=1)
        axis.axvline(0, color="#777777", linewidth=0.9, linestyle=":", zorder=1)
        if not control.empty:
            axis.plot(control["t"], control["path_index"], color=control_color, linewidth=1.65, linestyle=(0, (4, 2.5)), zorder=2)
        if not treated.empty:
            axis.plot(treated["t"], treated["path_index"], color=color, linewidth=2.1, zorder=3)
        if control.empty and treated.empty:
            axis.text(0.5, 0.5, "trajetória indisponível", transform=axis.transAxes, ha="center", va="center", color=TEXT_MUTED)
        axis.set_title(group_label, loc="left", color=color, fontweight="bold", fontsize=11)
        axis.set_xlim(EVENT_MIN, EVENT_MAX)
        axis.set_ylim(lower - padding, upper + padding)
        axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
        axis.grid(axis="x", visible=False)
    for axis in flat_axes[len(groups) :]:
        axis.set_visible(False)

    from matplotlib.lines import Line2D

    fig.legend(
        handles=[
            Line2D([0], [0], color=TEXT_DARK, linewidth=2.2, label="Exposed"),
            Line2D([0], [0], color="#A9A9A9", linewidth=1.7, linestyle=(0, (4, 2.5)), label="Not Exposed"),
        ],
        loc="upper right",
        bbox_to_anchor=(0.985, 0.87),
        frameon=False,
        ncol=2,
    )
    fig.suptitle(
        f"Figura experimental: Trajetórias de {OUTCOME_LOWER_LABELS[outcome]} — {DIMENSION_LABELS[dimension]}",
        x=0.09,
        y=0.96,
        ha="left",
        fontsize=14.5,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.09,
        0.88,
        "Séries em tempo de evento normalizadas pela média pré-ChatGPT de cada CBO (=100).",
        ha="left",
        va="top",
        fontsize=9.3,
        color=TEXT_MUTED,
    )
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.105, fontsize=10)
    fig.supylabel(f"Índice de {OUTCOME_LOWER_LABELS[outcome]} (média pré=100)", x=0.02, fontsize=10)
    wage_note = " Salários CBO-grupo-mês winsorizados em P1/P99." if outcome == "ln_salario_real_adm" else ""
    fig.text(
        0.09,
        0.025,
        "Nota: média não ponderada das variações em log entre CBOs; linhas escuras: Exposed; "
        f"linhas claras tracejadas: Not Exposed.{wage_note}\n"
        "Séries descritivas em janela estrita; a inferência está no event study correspondente.",
        ha="left",
        va="bottom",
        fontsize=7.7,
        color=TEXT_MUTED,
    )
    save_figure(fig, output_path)


def complete_group_panel(
    raw: pd.DataFrame,
    base: pd.DataFrame,
    dimension: str,
    group_id: str,
) -> pd.DataFrame:
    """Complete target/complement CBO-month cells on the Stage 2 support."""
    required_base = {
        "cbo_4d",
        "ano",
        "mes",
        "periodo",
        "t",
        "scenario_role",
        "scenario_treat",
        "indice",
    }
    missing_base = sorted(required_base - set(base.columns))
    if missing_base:
        raise RuntimeError(f"Base panel is missing group-panel columns: {missing_base}")
    required_raw = {
        "dimension",
        "group_id",
        "subgroup",
        "cbo_4d",
        "ano",
        "mes",
        "admissoes",
        "desligamentos",
        "salario_sum",
        "salario_count",
    }
    missing_raw = sorted(required_raw - set(raw.columns))
    if missing_raw:
        raise RuntimeError(f"Raw heterogeneity panel is missing columns: {missing_raw}")

    base_keys = ["cbo_4d", "ano", "mes"]
    if base.duplicated(base_keys).any():
        raise RuntimeError("Base panel contains duplicate CBO-month cells.")
    selected = raw[raw["dimension"].eq(dimension) & raw["group_id"].eq(group_id)].copy()
    raw_keys = [*base_keys, "subgroup"]
    if selected.duplicated(raw_keys).any():
        raise RuntimeError(f"Raw panel contains duplicate cells for {dimension}/{group_id}.")

    subgroup_grid = pd.DataFrame({"subgroup": SUBGROUPS})
    values = ["admissoes", "desligamentos", "salario_sum", "salario_count"]
    base_for_grid = base.drop(columns=[column for column in values if column in base.columns])
    completed = (
        base_for_grid.assign(_cross_key=1)
        .merge(subgroup_grid.assign(_cross_key=1), on="_cross_key")
        .drop(columns="_cross_key")
    )
    completed = completed.merge(
        selected[raw_keys + values],
        on=raw_keys,
        how="left",
        validate="one_to_one",
    )
    for column in values:
        completed[column] = pd.to_numeric(completed[column], errors="coerce").fillna(0)
    completed["admissoes"] = completed["admissoes"].astype(float)
    completed["desligamentos"] = completed["desligamentos"].astype(float)
    completed["salario_adm"] = np.where(
        completed["salario_count"].gt(0) & completed["salario_sum"].gt(0),
        completed["salario_sum"] / completed["salario_count"],
        np.nan,
    )
    completed["salario_real_adm"] = completed["salario_adm"] * (100.0 / completed["indice"])
    completed["ln_admissoes"] = np.log1p(completed["admissoes"].clip(lower=0))
    completed["ln_desligamentos"] = np.log1p(completed["desligamentos"].clip(lower=0))
    completed["ln_salario_real_adm"] = np.log(
        completed["salario_real_adm"].where(completed["salario_real_adm"].gt(0))
    )
    completed["dimension"] = dimension
    completed["group_id"] = group_id
    completed["group_indicator"] = completed["subgroup"].eq("target").astype(int)
    return completed.sort_values(["subgroup", "cbo_4d", "t"]).reset_index(drop=True)


def normalize_paths(
    panel: pd.DataFrame,
    *,
    dimension: str,
    group_id: str,
    group_label: str,
    outcome: str,
    event_times: list[int] | None = None,
    pre_min: int = PRE_MIN,
    pre_max: int = PRE_MAX,
) -> pd.DataFrame:
    """Normalize CBO paths to their own pre-event log mean and complete the grid."""
    if outcome not in OUTCOME_ORDER:
        raise ValueError(f"Unsupported path outcome: {outcome}")
    if pre_min > pre_max:
        raise ValueError("pre_min must not exceed pre_max.")
    times = EVENT_TIMES if event_times is None else list(event_times)
    value_column = {
        "ln_admissoes": "admissoes",
        "ln_desligamentos": "desligamentos",
        "ln_salario_real_adm": "ln_salario_real_adm",
    }[outcome]
    required = {"cbo_4d", "scenario_role", "t", value_column}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Path panel is missing columns: {missing}")

    data = panel.copy()
    if "subgroup" in data.columns:
        data = data[data["subgroup"].eq("target")].copy()
    data = data[data["scenario_role"].isin(PATH_ROLES) & data["t"].isin(times)].copy()
    if outcome == "ln_admissoes":
        data["path_log_value"] = np.log1p(pd.to_numeric(data["admissoes"], errors="coerce").clip(lower=0))
    elif outcome == "ln_desligamentos":
        data["path_log_value"] = np.log1p(
            pd.to_numeric(data["desligamentos"], errors="coerce").clip(lower=0)
        )
    else:
        wage_column = "ln_salario_real_adm_path" if "ln_salario_real_adm_path" in data.columns else outcome
        data["path_log_value"] = pd.to_numeric(data[wage_column], errors="coerce")

    baseline_keys = ["cbo_4d", "scenario_role"]
    baseline = (
        data[data["t"].between(pre_min, pre_max)]
        .dropna(subset=["path_log_value"])
        .groupby(baseline_keys, observed=True)["path_log_value"]
        .mean()
        .rename("pre_log_value")
        .reset_index()
    )
    data = data.merge(baseline, on=baseline_keys, how="inner", validate="many_to_one")
    data["cbo_log_change"] = data["path_log_value"] - data["pre_log_value"]
    summary = (
        data.dropna(subset=["cbo_log_change"])
        .groupby(["scenario_role", "t"], observed=True)["cbo_log_change"]
        .agg(mean_log_change="mean", sd_log_change="std", n_cbo="count")
        .reset_index()
    )
    summary["se_log_change"] = summary["sd_log_change"] / np.sqrt(summary["n_cbo"])
    summary["path_index"] = 100.0 * np.exp(summary["mean_log_change"])
    summary["ci_low"] = 100.0 * np.exp(summary["mean_log_change"] - 1.96 * summary["se_log_change"])
    summary["ci_high"] = 100.0 * np.exp(summary["mean_log_change"] + 1.96 * summary["se_log_change"])

    grid = pd.MultiIndex.from_product([PATH_ROLES, times], names=["scenario_role", "t"]).to_frame(index=False)
    out = grid.merge(summary, on=["scenario_role", "t"], how="left", validate="one_to_one")
    out["path_status"] = np.where(out["path_index"].notna(), "estimated", "missing")
    out["dimension"] = dimension
    out["group_id"] = group_id
    out["group_label"] = group_label
    out["outcome"] = outcome
    out["outcome_label"] = OUTCOME_LABELS[outcome]
    out["window_rule"] = WINDOW_RULE
    out["role_label"] = out["scenario_role"].map({"treated": "Exposed", "control": "Not Exposed"})
    columns = [
        "dimension",
        "group_id",
        "group_label",
        "outcome",
        "outcome_label",
        "window_rule",
        "scenario_role",
        "role_label",
        "t",
        "path_status",
        "mean_log_change",
        "sd_log_change",
        "se_log_change",
        "n_cbo",
        "path_index",
        "ci_low",
        "ci_high",
    ]
    return out[columns]


def log(message: str) -> None:
    print(f"[section5_2_dynamic] {message}", flush=True)


def _wage_bounds(panel: pd.DataFrame, wage_column: str) -> tuple[float, float]:
    wages = pd.to_numeric(panel[wage_column], errors="coerce")
    wages = wages[wages.gt(0)]
    lower, upper = wages.quantile([0.01, 0.99]).astype(float)
    if not np.isfinite(lower) or not np.isfinite(upper) or lower <= 0 or upper <= lower:
        raise RuntimeError(f"Invalid P1/P99 wage bounds for {wage_column}: {lower}, {upper}")
    return lower, upper


def load_main_strict_panel() -> pd.DataFrame:
    """Load the validated Stage 2 panel with main-strict OIT roles."""
    from section4_event_study.data import load_analysis_data
    from section4_event_study.treatment import apply_roles, assign_roles

    panel, classification = load_analysis_data()
    roles = assign_roles(classification, "main_strict")
    base = apply_roles(panel, roles)
    base["t"] = pd.to_numeric(base["tempo_relativo_meses"], errors="raise").astype(int)
    base = base[base["t"].between(EVENT_MIN, EVENT_MAX)].copy()
    base["cbo_4d"] = base["cbo_4d"].astype(str).str.zfill(4)
    if base.duplicated(["cbo_4d", "ano", "mes"]).any():
        raise RuntimeError("Main-strict Stage 2 panel contains duplicate CBO-month cells.")
    if "indice" not in base.columns or base["indice"].isna().any() or base["indice"].le(0).any():
        raise RuntimeError("Main-strict Stage 2 panel has missing or invalid IPCA indices.")
    role_counts = base[["cbo_4d", "scenario_role"]].drop_duplicates()["scenario_role"].value_counts()
    log(
        "Main strict support: "
        f"{int(role_counts.get('treated', 0))} Exposed CBOs and "
        f"{int(role_counts.get('control', 0))} Not Exposed CBOs."
    )
    return base.sort_values(["cbo_4d", "t"]).reset_index(drop=True)


def load_or_build_dynamic_micro_pairs(base: pd.DataFrame) -> pd.DataFrame:
    """Load a source-aware cache or build the required demographic pair panel."""
    from section4_event_study.config import DATA_RAW, PANEL_PATH, SCENARIO_GRID
    from section4_event_study.heterogeneity import aggregate_micro_group_pairs

    raw_paths = sorted(DATA_RAW.glob("caged_*.parquet"))
    source_paths = [*raw_paths, PANEL_PATH, SCENARIO_GRID]
    newest_source = max((path.stat().st_mtime for path in source_paths if path.exists()), default=0.0)
    if MICRO_CACHE_PATH.exists() and MICRO_CACHE_PATH.stat().st_mtime >= newest_source:
        cached = pd.read_parquet(MICRO_CACHE_PATH)
        required = {
            "dimension",
            "group_id",
            "subgroup",
            "cbo_4d",
            "ano",
            "mes",
            "admissoes",
            "desligamentos",
            "salario_sum",
            "salario_count",
        }
        version_ok = (
            "cache_schema_version" in cached.columns
            and set(cached["cache_schema_version"].dropna().unique()) == {MICRO_CACHE_VERSION}
        )
        if required.issubset(cached.columns) and version_ok:
            log(f"Loaded cached demographic pairs from {MICRO_CACHE_PATH}")
            return cached

    micro = aggregate_micro_group_pairs()
    required_dimensions = {"sex", "canaries_age", "race_color", "education"}
    support = base[["cbo_4d", "ano", "mes"]].drop_duplicates()
    micro = micro[micro["dimension"].isin(required_dimensions)].copy()
    micro = micro.merge(support, on=["cbo_4d", "ano", "mes"], how="inner", validate="many_to_one")
    micro["cache_schema_version"] = MICRO_CACHE_VERSION
    MICRO_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    micro.to_parquet(MICRO_CACHE_PATH, index=False)
    log(f"Cached {len(micro):,} demographic pair rows at {MICRO_CACHE_PATH}")
    return micro


def _append_model_outputs(
    coefficient_parts: list[pd.DataFrame],
    pretrend_rows: list[dict[str, object]],
    path_parts: list[pd.DataFrame],
    *,
    panel: pd.DataFrame,
    path_panel: pd.DataFrame,
    dimension: str,
    group_id: str,
    group_label: str,
    outcome: str,
    estimand: str,
) -> None:
    log(f"Estimating {dimension}/{group_id}/{outcome} ({estimand.upper()})...")
    coefficients, pretrend = safely_estimate_dynamic(
        panel,
        dimension=dimension,
        group_id=group_id,
        group_label=group_label,
        outcome=outcome,
        estimand=estimand,
    )
    paths = normalize_paths(
        path_panel,
        dimension=dimension,
        group_id=group_id,
        group_label=group_label,
        outcome=outcome,
    )
    for key in ["power_status", "treated_cbo", "control_cbo"]:
        paths[key] = pretrend[key]
    coefficient_parts.append(coefficients)
    pretrend_rows.append(pretrend)
    path_parts.append(paths)


def build_all_results(
    base: pd.DataFrame | None = None,
    micro: pd.DataFrame | None = None,
    income_groups: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build all 63 model outputs and 21 exposed/control path blocks."""
    from section4_event_study.heterogeneity import build_pre_treatment_income_groups

    base = load_main_strict_panel() if base is None else base.copy()
    coefficient_parts: list[pd.DataFrame] = []
    pretrend_rows: list[dict[str, object]] = []
    path_parts: list[pd.DataFrame] = []

    national_bounds = _wage_bounds(base, "salario_medio_adm")
    national_paths = add_winsorized_wage_path(
        base,
        wage_column="salario_medio_adm",
        bounds=national_bounds,
    )
    for outcome in OUTCOME_ORDER:
        _append_model_outputs(
            coefficient_parts,
            pretrend_rows,
            path_parts,
            panel=base,
            path_panel=national_paths,
            dimension="national",
            group_id="national",
            group_label="Nacional",
            outcome=outcome,
            estimand="did",
        )

    income_groups = build_pre_treatment_income_groups() if income_groups is None else income_groups
    income_panel = base.copy()
    income_panel["income_group"] = income_panel["cbo_4d"].map(income_groups)
    income_panel = income_panel[income_panel["income_group"].notna()].copy()
    income_bounds = _wage_bounds(income_panel, "salario_medio_adm")
    income_paths = add_winsorized_wage_path(
        income_panel,
        wage_column="salario_medio_adm",
        bounds=income_bounds,
    )
    for group_id, group_label in _dimension_groups("income"):
        model_panel = income_panel.copy()
        model_panel["group_indicator"] = model_panel["income_group"].eq(group_id).astype(int)
        target_paths = income_paths[income_paths["income_group"].eq(group_id)].copy()
        for outcome in OUTCOME_ORDER:
            _append_model_outputs(
                coefficient_parts,
                pretrend_rows,
                path_parts,
                panel=model_panel,
                path_panel=target_paths,
                dimension="income",
                group_id=group_id,
                group_label=group_label,
                outcome=outcome,
                estimand="ddd",
            )

    if micro is None:
        log("Reconstructing demographic target/complement panels from CAGED microdata...")
        micro = load_or_build_dynamic_micro_pairs(base)
    for dimension in ["sex", "age_canaries", "race_color", "education"]:
        source_dimension = str(HETEROGENEITY_SPECS[dimension]["dimension"])
        group_panels: dict[str, pd.DataFrame] = {}
        labels = dict(_dimension_groups(dimension))
        for group_id, _group_label in _dimension_groups(dimension):
            completed = complete_group_panel(micro, base, source_dimension, group_id)
            completed["dimension"] = dimension
            group_panels[group_id] = completed
        target_wages = pd.concat(
            [
                panel.loc[panel["subgroup"].eq("target"), "salario_adm"]
                for panel in group_panels.values()
            ],
            ignore_index=True,
        )
        micro_bounds = _wage_bounds(pd.DataFrame({"salario_adm": target_wages}), "salario_adm")
        for group_id, panel in group_panels.items():
            path_panel = add_winsorized_wage_path(
                panel,
                wage_column="salario_adm",
                bounds=micro_bounds,
            )
            for outcome in OUTCOME_ORDER:
                _append_model_outputs(
                    coefficient_parts,
                    pretrend_rows,
                    path_parts,
                    panel=panel,
                    path_panel=path_panel,
                    dimension=dimension,
                    group_id=group_id,
                    group_label=labels[group_id],
                    outcome=outcome,
                    estimand="ddd",
                )

    coefficients = pd.concat(coefficient_parts, ignore_index=True)
    pretrends = pd.DataFrame(pretrend_rows)
    paths = pd.concat(path_parts, ignore_index=True)
    model_order = {
        (spec["dimension"], spec["group_id"], spec["outcome"]): index
        for index, spec in enumerate(expected_model_specs())
    }
    for frame in [coefficients, pretrends, paths]:
        frame["_model_order"] = [
            model_order[(dimension, group_id, outcome)]
            for dimension, group_id, outcome in zip(frame["dimension"], frame["group_id"], frame["outcome"])
        ]
    coefficients = coefficients.sort_values(["_model_order", "t"]).drop(columns="_model_order").reset_index(drop=True)
    pretrends = pretrends.sort_values("_model_order").drop(columns="_model_order").reset_index(drop=True)
    paths["_role_order"] = paths["scenario_role"].map({"treated": 0, "control": 1})
    paths = (
        paths.sort_values(["_model_order", "_role_order", "t"])
        .drop(columns=["_model_order", "_role_order"])
        .reset_index(drop=True)
    )
    validate_long_frames(coefficients, pretrends, paths)
    return coefficients, pretrends, paths


def build_micro_dimension_results(
    base: pd.DataFrame,
    micro: pd.DataFrame,
    *,
    dimension: str,
    groups: list[tuple[str, str]],
    outcomes: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build dynamic DDD results for one microdata-based alternative dimension."""
    selected_outcomes = list(OUTCOME_ORDER if outcomes is None else outcomes)
    unsupported = sorted(set(selected_outcomes) - set(OUTCOME_ORDER))
    if unsupported:
        raise ValueError(f"Unsupported dynamic outcomes: {unsupported}")
    if not groups:
        raise ValueError("Alternative dimension must contain at least one group.")

    coefficient_parts: list[pd.DataFrame] = []
    pretrend_rows: list[dict[str, object]] = []
    path_parts: list[pd.DataFrame] = []
    group_panels: dict[str, pd.DataFrame] = {}
    labels = dict(groups)
    for group_id, _group_label in groups:
        group_panels[group_id] = complete_group_panel(micro, base, dimension, group_id)

    target_wages = pd.concat(
        [
            panel.loc[panel["subgroup"].eq("target"), "salario_adm"]
            for panel in group_panels.values()
        ],
        ignore_index=True,
    )
    wage_bounds = _wage_bounds(
        pd.DataFrame({"salario_adm": target_wages}),
        "salario_adm",
    )
    for group_id, panel in group_panels.items():
        path_panel = add_winsorized_wage_path(
            panel,
            wage_column="salario_adm",
            bounds=wage_bounds,
        )
        for outcome in selected_outcomes:
            _append_model_outputs(
                coefficient_parts,
                pretrend_rows,
                path_parts,
                panel=panel,
                path_panel=path_panel,
                dimension=dimension,
                group_id=group_id,
                group_label=labels[group_id],
                outcome=outcome,
                estimand="ddd",
            )

    coefficients = pd.concat(coefficient_parts, ignore_index=True)
    pretrends = pd.DataFrame(pretrend_rows)
    paths = pd.concat(path_parts, ignore_index=True)
    group_order = {group_id: index for index, (group_id, _label) in enumerate(groups)}
    outcome_order = {outcome: index for index, outcome in enumerate(selected_outcomes)}
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
    return coefficients, pretrends, paths


def _figure_filename(dimension: str, outcome: str, kind: str) -> str:
    return f"figure_experimental_s5_2_{dimension}_{OUTCOME_FILE_STEMS[outcome]}_{kind}.png"


def render_all_figures(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    figure_dir: Path,
) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    for dimension in ["national", "sex", "income", "age_canaries", "race_color", "education"]:
        for outcome in OUTCOME_ORDER:
            coefficient_view = coefficients[
                coefficients["dimension"].eq(dimension) & coefficients["outcome"].eq(outcome)
            ]
            pretrend_view = pretrends[
                pretrends["dimension"].eq(dimension) & pretrends["outcome"].eq(outcome)
            ]
            path_view = paths[paths["dimension"].eq(dimension) & paths["outcome"].eq(outcome)]
            plot_event_study_panels(
                coefficient_view,
                pretrend_view,
                dimension=dimension,
                outcome=outcome,
                output_path=figure_dir / _figure_filename(dimension, outcome, "event_study"),
            )
            plot_path_panels(
                path_view,
                dimension=dimension,
                outcome=outcome,
                output_path=figure_dir / _figure_filename(dimension, outcome, "paths"),
            )


def validate_figure_files(figure_dir: Path) -> None:
    expected = set(expected_figure_filenames())
    observed = {path.name for path in figure_dir.glob("*.png")}
    if observed != expected:
        raise RuntimeError(
            f"Figure files differ from contract; missing={sorted(expected - observed)}, "
            f"unexpected={sorted(observed - expected)}"
        )
    empty = [path.name for path in figure_dir.glob("*.png") if path.stat().st_size == 0]
    if empty:
        raise RuntimeError(f"Empty PNG files: {empty}")


def write_readme(output_root: Path, pretrends: pd.DataFrame) -> Path:
    status_counts = pretrends["pretrend_status"].value_counts(dropna=False).to_dict()
    power_counts = pretrends["power_status"].value_counts(dropna=False).to_dict()
    failed = int(pretrends["result_status"].ne("estimated").sum())
    lines = [
        "# Experimental Section 5.2 Dynamic Figures",
        "",
        "This bundle separates dynamic inference from descriptive exposed-versus-unexposed paths.",
        "It is experimental and is not part of the curated dissertation manifest.",
        "",
        "## Contract",
        "",
        "- 36 PNG figures: six blocks, three outcomes, two figure types.",
        "- National event studies estimate dynamic DiD effects.",
        "- Demographic event studies estimate dynamic target-versus-complement DDD effects.",
        "- Paths are descriptive and normalize each CBO to its own pre-ChatGPT mean (=100).",
        "- Real admission wages are winsorized at P1/P99 only for descriptive paths.",
        "- The event window is strict (`t=-12,...,24`); observations outside it are not binned into endpoints.",
        "- Confidence intervals are pointwise and unadjusted for multiple testing.",
        "",
        "## Diagnostics",
        "",
        f"- Pretrend status counts: `{status_counts}`.",
        f"- Power status counts: `{power_counts}`.",
        f"- Failed models retained as explicit panels: `{failed}`.",
        "",
        "## Backing data",
        "",
        "- `tables/event_study_coefficients_long.csv`",
        "- `tables/event_study_pretrends.csv`",
        "- `tables/normalized_paths_long.csv`",
        "",
        "See `audit/section5_2_dynamic_blindspot.md` for the interpretation audit.",
    ]
    path = output_root / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_manifest(output_root: Path) -> Path:
    files = sorted(
        path
        for path in output_root.rglob("*")
        if path.is_file() and path.name != "MANIFEST.md"
    )
    lines = [
        "# Experimental Bundle Manifest",
        "",
        "| File | Bytes | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"| `{path.relative_to(output_root)}` | {path.stat().st_size} | `{digest}` |")
    manifest = output_root / "MANIFEST.md"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def run(output_root: Path = OUTPUT_ROOT) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute the full experimental Section 5.2 dynamic bundle."""
    if output_root.exists():
        shutil.rmtree(output_root)
    figure_dir = output_root / "figures"
    table_dir = output_root / "tables"
    (output_root / "audit").mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    coefficients, pretrends, paths = build_all_results()
    coefficients.to_csv(table_dir / "event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(table_dir / "event_study_pretrends.csv", index=False)
    paths.to_csv(table_dir / "normalized_paths_long.csv", index=False)
    render_all_figures(coefficients, pretrends, paths, figure_dir)
    validate_long_frames(coefficients, pretrends, paths)
    validate_figure_files(figure_dir)
    write_readme(output_root, pretrends)
    write_manifest(output_root)
    log(f"Wrote experimental bundle to {output_root}")
    return coefficients, pretrends, paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.output_root)
