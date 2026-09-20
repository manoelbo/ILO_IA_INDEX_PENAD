#!/usr/bin/env python3
"""Build age-specific Software/IT flow paths and dynamic DDD event studies.

The script produces two complementary visual layers for admissions and
separations. Normalized event-time paths preserve the dark-treatment versus
light-control layout, while dynamic triple-difference figures report the
inferential event-study coefficients with clustered 95% confidence intervals.
"""

from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pyfixest as pf
from scipy.stats import chi2


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from section4_5_final.plot_software_it_wage_paths_by_age import (  # noqa: E402
    AGE_COLORS,
    AGE_LABELS,
    AGE_ORDER,
    CLASSIFICATION_PATH,
    DATA_RAW,
    EVENT_MAX,
    EVENT_MIN,
    HETEROGENEITY_PATH,
    PRE_MAX,
    PRE_MIN,
    RAW_BATCH_SIZE,
    ROOT,
    assign_canaries_age_band,
    build_strict_software_it_roles,
    lighten_color,
    normalize_cbo,
)
from section4_5_final.style import (  # noqa: E402
    GRID,
    TEXT_DARK,
    TEXT_MUTED,
    get_pyplot,
    save_figure,
    setup_plot_style,
)


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)

PANEL_PATH = ROOT / "data" / "output" / "painel_2b_ready.parquet"
OUTPUT_FIGURE_DIR = ROOT / "outputs" / "section4_5_final" / "figures"
OUTPUT_TABLE_DIR = ROOT / "outputs" / "section4_5_final" / "tables"
REFERENCE_PERIOD = -1
EVENT_TIMES = list(range(EVENT_MIN, EVENT_MAX + 1))
CONTROL_COLUMNS = ["idade_media_adm", "pct_mulher_adm", "pct_superior_adm", "pct_negra_adm"]
CONTROL_TERMS = " + ".join(CONTROL_COLUMNS)

OUTCOME_SPECS = {
    "ln_admissoes": {
        "count_col": "admissoes",
        "label": "Admissões",
        "label_lower": "admissões",
        "path_figure": "figure_5_2a_experimental_software_it_admissions_paths_by_age.png",
        "path_csv": "figure_5_2a_experimental_software_it_admissions_paths_by_age.csv",
        "event_figure": "figure_5_2c_experimental_software_it_admissions_ddd_event_study_by_age.png",
        "event_csv": "figure_5_2c_experimental_software_it_admissions_ddd_event_study_by_age.csv",
        "pretrend_csv": "figure_5_2c_experimental_software_it_admissions_ddd_pretrends.csv",
        "figure_path_label": "Figura 5.2A (teste)",
        "figure_event_label": "Figura 5.2C (teste)",
    },
    "ln_desligamentos": {
        "count_col": "desligamentos",
        "label": "Desligamentos",
        "label_lower": "desligamentos",
        "path_figure": "figure_5_2b_experimental_software_it_separations_paths_by_age.png",
        "path_csv": "figure_5_2b_experimental_software_it_separations_paths_by_age.csv",
        "event_figure": "figure_5_2d_experimental_software_it_separations_ddd_event_study_by_age.png",
        "event_csv": "figure_5_2d_experimental_software_it_separations_ddd_event_study_by_age.csv",
        "pretrend_csv": "figure_5_2d_experimental_software_it_separations_ddd_pretrends.csv",
        "figure_path_label": "Figura 5.2B (teste)",
        "figure_event_label": "Figura 5.2D (teste)",
    },
}


def log(message: str) -> None:
    print(f"[software_it_flow_event_studies] {message}", flush=True)


def build_event_periods() -> pd.DataFrame:
    reference = pd.Period("2022-12", freq="M")
    rows = []
    for t in EVENT_TIMES:
        period = reference + t
        rows.append(
            {
                "ano": int(period.year),
                "mes": int(period.month),
                "periodo": str(period),
                "t": t,
            }
        )
    return pd.DataFrame(rows)


def raw_path_overlaps_event_window(path: Path) -> bool:
    try:
        year = int(path.stem.rsplit("_", 1)[-1])
    except ValueError:
        return True
    first_t = (year - 2022) * 12 + (1 - 12)
    last_t = (year - 2022) * 12 + (12 - 12)
    return last_t >= EVENT_MIN and first_t <= EVENT_MAX


def _filtered_flow_batch(batch: pa.RecordBatch, eligible_cbo: pa.Array) -> pd.DataFrame:
    table = pa.Table.from_batches([batch])
    cbo_4d = pc.utf8_slice_codeunits(table["cbo_2002"], start=0, stop=4)
    t = pc.add(
        pc.multiply(pc.subtract(table["ano"], 2022), 12),
        pc.subtract(table["mes"], 12),
    )
    movement = pc.is_in(table["saldo_movimentacao"], value_set=pa.array([-1, 1], type=pa.int64()))
    mask = pc.and_kleene(
        movement,
        pc.and_kleene(
            pc.is_in(cbo_4d, value_set=eligible_cbo),
            pc.and_kleene(pc.greater_equal(t, EVENT_MIN), pc.less_equal(t, EVENT_MAX)),
        ),
    )
    mask = pc.and_kleene(mask, pc.greater_equal(table["idade"], 22))
    filtered = table.filter(mask)
    if filtered.num_rows == 0:
        return pd.DataFrame()
    out = filtered.select(["ano", "mes", "cbo_2002", "idade", "saldo_movimentacao"]).to_pandas()
    out["cbo_4d"] = normalize_cbo(out["cbo_2002"])
    out["age_group"] = assign_canaries_age_band(out["idade"])
    out["periodo"] = out["ano"].astype(int).astype(str) + "-" + out["mes"].astype(int).astype(str).str.zfill(2)
    out["t"] = (out["ano"].astype(int) - 2022) * 12 + (out["mes"].astype(int) - 12)
    out["admissoes"] = out["saldo_movimentacao"].eq(1).astype("int8")
    out["desligamentos"] = out["saldo_movimentacao"].eq(-1).astype("int8")
    return out.dropna(subset=["age_group"])


def complete_age_flow_panel(
    observed: pd.DataFrame,
    roles: pd.DataFrame,
    periods: pd.DataFrame,
) -> pd.DataFrame:
    required_roles = {"cbo_4d", "scenario_role", "scenario_treat"}
    period_columns = ["ano", "mes", "periodo", "t"]
    required_periods = set(period_columns)
    if not required_roles.issubset(roles.columns):
        raise RuntimeError(f"Roles are missing columns: {sorted(required_roles - set(roles.columns))}")
    if not required_periods.issubset(periods.columns):
        raise RuntimeError(f"Periods are missing columns: {sorted(required_periods - set(periods.columns))}")

    cbo = roles[["cbo_4d"]].drop_duplicates().assign(_key=1)
    ages = pd.DataFrame({"age_group": AGE_ORDER}).assign(_key=1)
    months = periods[period_columns].drop_duplicates().assign(_key=1)
    grid = cbo.merge(ages, on="_key").merge(months, on="_key").drop(columns="_key")
    keys = ["cbo_4d", "age_group", "ano", "mes", "periodo", "t"]
    if observed.empty:
        counts = pd.DataFrame(columns=[*keys, "admissoes", "desligamentos"])
    else:
        counts = (
            observed.groupby(keys, observed=True)[["admissoes", "desligamentos"]]
            .sum()
            .reset_index()
        )
    out = grid.merge(counts, on=keys, how="left", validate="one_to_one")
    out[["admissoes", "desligamentos"]] = out[["admissoes", "desligamentos"]].fillna(0).astype(int)
    out = out.merge(
        roles[["cbo_4d", "scenario_role", "scenario_treat"]],
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    if out[["scenario_role", "scenario_treat"]].isna().any().any():
        raise RuntimeError("Completed flow panel contains CBOs without treatment roles.")
    return out.sort_values(["age_group", "scenario_role", "cbo_4d", "t"]).reset_index(drop=True)


def reconstruct_age_flow_panel(raw_paths: list[Path], roles: pd.DataFrame) -> pd.DataFrame:
    paths = [path for path in raw_paths if raw_path_overlaps_event_window(path)]
    if not paths:
        raise FileNotFoundError(f"No CAGED parquet files overlap the event window in {DATA_RAW}.")
    eligible = pa.array(sorted(roles["cbo_4d"].unique()), type=pa.string())
    pieces: list[pd.DataFrame] = []
    columns = ["ano", "mes", "cbo_2002", "idade", "saldo_movimentacao"]
    for path in paths:
        log(f"Scanning {path.name}...")
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(batch_size=RAW_BATCH_SIZE, columns=columns):
            data = _filtered_flow_batch(batch, eligible)
            if data.empty:
                continue
            grouped = (
                data.groupby(["cbo_4d", "age_group", "ano", "mes", "periodo", "t"], observed=True)[
                    ["admissoes", "desligamentos"]
                ]
                .sum()
                .reset_index()
            )
            pieces.append(grouped)
    observed = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    panel = complete_age_flow_panel(observed, roles, build_event_periods())
    expected_rows = roles["cbo_4d"].nunique() * len(AGE_ORDER) * len(EVENT_TIMES)
    if len(panel) != expected_rows:
        raise RuntimeError(f"Completed flow panel has {len(panel)} rows; expected {expected_rows}.")
    return panel


def load_controls(path: Path = PANEL_PATH) -> pd.DataFrame:
    required = ["cbo_4d", "ano", "mes", "periodo", "tempo_relativo_meses", *CONTROL_COLUMNS]
    controls = pd.read_parquet(path, columns=required)
    controls["cbo_4d"] = normalize_cbo(controls["cbo_4d"])
    controls["periodo"] = controls["periodo"].astype(str)
    controls["t"] = pd.to_numeric(controls["tempo_relativo_meses"], errors="raise").astype(int)
    controls = controls[controls["t"].between(EVENT_MIN, EVENT_MAX)].copy()
    controls = controls.drop(columns="tempo_relativo_meses")
    if controls.duplicated(["cbo_4d", "ano", "mes"]).any():
        raise RuntimeError("Stage panel controls contain duplicate CBO-month rows.")
    for column in CONTROL_COLUMNS:
        controls[column] = pd.to_numeric(controls[column], errors="coerce")
    return controls


def build_flow_paths(
    panel: pd.DataFrame,
    outcome: str,
    pre_min: int = PRE_MIN,
    pre_max: int = PRE_MAX,
) -> pd.DataFrame:
    if outcome not in OUTCOME_SPECS:
        raise ValueError(f"Unsupported flow outcome: {outcome}")
    count_col = str(OUTCOME_SPECS[outcome]["count_col"])
    required = {"cbo_4d", "age_group", "scenario_role", "t", count_col}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Flow panel is missing columns: {missing}")

    data = panel.copy()
    data["log_flow"] = np.log1p(pd.to_numeric(data[count_col], errors="coerce").clip(lower=0))
    keys = ["cbo_4d", "age_group", "scenario_role"]
    baseline = (
        data[data["t"].between(pre_min, pre_max)]
        .groupby(keys, observed=True)["log_flow"]
        .mean()
        .rename("pre_log_flow")
        .reset_index()
    )
    data = data.merge(baseline, on=keys, how="inner", validate="many_to_one")
    data["cbo_log_change"] = data["log_flow"] - data["pre_log_flow"]
    out = (
        data.groupby(["age_group", "scenario_role", "t"], observed=True)["cbo_log_change"]
        .agg(mean_log_change="mean", sd_log_change="std", n_cbo="count")
        .reset_index()
    )
    out["se_log_change"] = out["sd_log_change"] / np.sqrt(out["n_cbo"])
    out["flow_index"] = 100.0 * np.exp(out["mean_log_change"])
    out["ci_low"] = 100.0 * np.exp(out["mean_log_change"] - 1.96 * out["se_log_change"])
    out["ci_high"] = 100.0 * np.exp(out["mean_log_change"] + 1.96 * out["se_log_change"])
    out["outcome"] = outcome
    out["age_label"] = out["age_group"].map(AGE_LABELS)
    out["role_label"] = out["scenario_role"].map(
        {"treated": "Núcleo de Software e TI", "control": "Not Exposed"}
    )
    order = {age: index for index, age in enumerate(AGE_ORDER)}
    out["_age_order"] = out["age_group"].map(order)
    return out.sort_values(["_age_order", "scenario_role", "t"]).drop(columns="_age_order").reset_index(drop=True)


def build_age_pair_panel(
    flow_panel: pd.DataFrame,
    controls: pd.DataFrame,
    age_group: str,
    outcome: str,
) -> pd.DataFrame:
    if age_group not in AGE_ORDER:
        raise ValueError(f"Unsupported age group: {age_group}")
    if outcome not in OUTCOME_SPECS:
        raise ValueError(f"Unsupported flow outcome: {outcome}")
    count_col = str(OUTCOME_SPECS[outcome]["count_col"])
    keys = ["cbo_4d", "ano", "mes", "periodo", "t", "scenario_role", "scenario_treat"]
    required = set(keys + ["age_group", count_col])
    missing = sorted(required - set(flow_panel.columns))
    if missing:
        raise RuntimeError(f"Flow panel is missing pair columns: {missing}")

    target = flow_panel[flow_panel["age_group"].eq(age_group)][keys + [count_col]].copy()
    target = target.rename(columns={count_col: "flow_count"})
    target["subgroup"] = "target"
    complement = (
        flow_panel[~flow_panel["age_group"].eq(age_group)]
        .groupby(keys, observed=True)[count_col]
        .sum()
        .rename("flow_count")
        .reset_index()
    )
    complement["subgroup"] = "complement"
    out = pd.concat([target, complement], ignore_index=True)
    out[outcome] = np.log1p(pd.to_numeric(out["flow_count"], errors="coerce").clip(lower=0))

    control_keys = ["cbo_4d", "ano", "mes", "periodo", "t"]
    required_controls = set(control_keys + CONTROL_COLUMNS)
    missing_controls = sorted(required_controls - set(controls.columns))
    if missing_controls:
        raise RuntimeError(f"Control panel is missing columns: {missing_controls}")
    control_view = controls[control_keys + CONTROL_COLUMNS].drop_duplicates(control_keys)
    out = out.merge(control_view, on=control_keys, how="inner", validate="many_to_one")
    if out.empty or out[CONTROL_COLUMNS].isna().any().any():
        raise RuntimeError(f"No complete Stage 2 control sample remains for the {age_group} pair panel.")
    out["age_group"] = age_group
    return out


def event_suffix(t: int) -> str:
    return f"tm{-t}" if t < 0 else f"t{t}"


def add_dynamic_ddd_terms(
    data: pd.DataFrame,
    event_times: list[int] | None = None,
) -> tuple[pd.DataFrame, dict[int, dict[str, str]]]:
    times = EVENT_TIMES if event_times is None else event_times
    out = data.copy()
    out["group_indicator"] = out["subgroup"].eq("target").astype(int)
    out["treat_group"] = out["scenario_treat"].astype(int) * out["group_indicator"]
    terms: dict[int, dict[str, str]] = {}
    dynamic_columns: dict[str, pd.Series] = {}
    for t in times:
        if t == REFERENCE_PERIOD:
            continue
        suffix = event_suffix(t)
        age_term = f"age_{suffix}"
        treat_term = f"treat_{suffix}"
        ddd_term = f"ddd_{suffix}"
        at_t = out["t"].eq(t).astype(int)
        dynamic_columns[age_term] = (at_t * out["group_indicator"]).astype("int8")
        dynamic_columns[treat_term] = (at_t * out["scenario_treat"].astype(int)).astype("int8")
        dynamic_columns[ddd_term] = (at_t * out["treat_group"]).astype("int8")
        terms[t] = {"age": age_term, "treat": treat_term, "ddd": ddd_term}
    out = pd.concat([out, pd.DataFrame(dynamic_columns, index=out.index)], axis=1)
    return out, terms


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


def joint_pretrend_test(model: object, pre_terms: list[str]) -> tuple[float, float, str]:
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
            return statistic, p_value, "wald_chi2"
    except Exception:
        pass
    tstats = model.tstat().reindex(pre_terms).dropna()
    if tstats.empty:
        return np.nan, np.nan, "not_available_no_tstats"
    statistic = float(np.square(tstats.astype(float)).sum())
    return statistic, float(chi2.sf(statistic, len(tstats))), "tstat_chi2_fallback"


def classify_pretrend(n_pre_p_lt_005: int, joint_p_value: float) -> str:
    if pd.isna(joint_p_value):
        return "warning"
    if joint_p_value < 0.05 or n_pre_p_lt_005 >= 2:
        return "fail"
    if n_pre_p_lt_005 == 0 and joint_p_value > 0.10:
        return "pass"
    return "warning"


def model_observation_count(model: object, fallback: int) -> int:
    """Return the estimation N after fixed-effect singleton removal."""
    value = getattr(model, "_N", fallback)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def model_cluster_count(model: object, cluster_column: str, fallback: int) -> int:
    """Return the cluster count from the post-singleton model data when stored."""
    model_data = getattr(model, "_data", None)
    if isinstance(model_data, pd.DataFrame) and cluster_column in model_data.columns:
        return int(model_data[cluster_column].nunique())
    return int(fallback)


def estimate_dynamic_ddd(
    pair_panel: pd.DataFrame,
    age_group: str,
    outcome: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    data, terms = add_dynamic_ddd_terms(pair_panel)
    dynamic_terms = [name for t in EVENT_TIMES if t != REFERENCE_PERIOD for name in terms[t].values()]
    required = [outcome, "treat_group", "cbo_4d", "periodo", "subgroup", *CONTROL_COLUMNS]
    data = data.dropna(subset=required).copy()
    formula = (
        f"{outcome} ~ {' + '.join(dynamic_terms)} + treat_group + {CONTROL_TERMS} "
        "| cbo_4d + periodo + subgroup"
    )
    model = pf.feols(formula, data=data, vcov={"CRV1": "cbo_4d"})
    coefs = model.coef()
    ses = model.se()
    pvalues = model.pvalue()
    coefficient_names = set(coefs.index)
    n_obs = model_observation_count(model, fallback=len(data))
    n_cbo = model_cluster_count(model, "cbo_4d", fallback=data["cbo_4d"].nunique())
    rows = []
    for t in EVENT_TIMES:
        is_reference = t == REFERENCE_PERIOD
        if is_reference:
            estimate = {
                "coef": 0.0,
                "se": 0.0,
                "p_value": np.nan,
                "ci_low": 0.0,
                "ci_high": 0.0,
                "coefficient_status": "reference",
            }
        else:
            term = terms[t]["ddd"]
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
                "age_group": age_group,
                "age_label": AGE_LABELS[age_group],
                "outcome": outcome,
                "t": t,
                "is_reference": is_reference,
                "is_pretrend": t < 0 and not is_reference,
                "n_obs": n_obs,
                "n_cbo": n_cbo,
                **estimate,
            }
        )

    pre_terms = [
        terms[t]["ddd"]
        for t in EVENT_TIMES
        if t < 0 and t != REFERENCE_PERIOD and terms[t]["ddd"] in coefficient_names
    ]
    pre_pvalues = pd.Series(pvalues).reindex(pre_terms).astype(float)
    statistic, joint_p_value, method = joint_pretrend_test(model, pre_terms)
    n_pre_p_lt_005 = int((pre_pvalues < 0.05).sum())
    pretrend = {
        "age_group": age_group,
        "age_label": AGE_LABELS[age_group],
        "outcome": outcome,
        "n_obs": n_obs,
        "n_cbo": n_cbo,
        "n_pre_coefficients": len(pre_terms),
        "n_pre_p_lt_005": n_pre_p_lt_005,
        "joint_statistic": statistic,
        "joint_p_value": joint_p_value,
        "joint_test_method": method,
        "pretrend_status": classify_pretrend(n_pre_p_lt_005, joint_p_value),
        "formula": formula,
    }
    return pd.DataFrame(rows), pretrend


def estimate_all_dynamic_ddd(
    flow_panel: pd.DataFrame,
    controls: pd.DataFrame,
    outcome: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefficient_rows = []
    pretrend_rows = []
    for age_group in AGE_ORDER:
        log(f"Estimating {outcome} dynamic DDD for {age_group}...")
        pair = build_age_pair_panel(flow_panel, controls, age_group, outcome)
        coefficients, pretrend = estimate_dynamic_ddd(pair, age_group, outcome)
        coefficient_rows.append(coefficients)
        pretrend_rows.append(pretrend)
    return pd.concat(coefficient_rows, ignore_index=True), pd.DataFrame(pretrend_rows)


def load_average_ddd_annotation(outcome: str) -> dict[str, object] | None:
    if not HETEROGENEITY_PATH.exists() or HETEROGENEITY_PATH.stat().st_size == 0:
        return None
    results = pd.read_csv(HETEROGENEITY_PATH)
    row = results[
        results["group_id"].eq("software_it_core")
        & results["heterogeneity_group_id"].eq("age_22_25")
        & results["outcome"].eq(outcome)
    ]
    if len(row) != 1:
        return None
    item = row.iloc[0]
    return {
        "effect_pct": 100.0 * math.expm1(float(item["coef"])),
        "p_value": float(item["p_value"]),
        "pretrend_status": str(item["pretrend_status"]),
    }


def _status_pt(status: str) -> str:
    return {"pass": "aprovado", "warning": "com alerta", "fail": "reprovado"}.get(status, status)


def _format_p_value(value: float) -> str:
    if value < 0.01:
        return "p<0,01"
    return f"p={value:.3f}".replace(".", ",")


def plot_normalized_flow_paths(
    paths: pd.DataFrame,
    output_path: Path,
    outcome: str,
    annotation: dict[str, object] | None = None,
) -> None:
    spec = OUTCOME_SPECS[outcome]
    plt = get_pyplot()
    setup_plot_style()
    fig, axes = plt.subplots(2, 3, figsize=(13.8, 8.2), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.155, hspace=0.36, wspace=0.18)
    values = pd.to_numeric(paths["flow_index"], errors="coerce").dropna()
    if values.empty:
        raise RuntimeError(f"No normalized path values are available for {outcome}.")
    lower = min(float(values.min()), 100.0)
    upper = max(float(values.max()), 100.0)
    padding = max(2.0, 0.08 * max(upper - lower, 1.0))

    for ax, age_group in zip(axes.flat, AGE_ORDER):
        color = AGE_COLORS[age_group]
        control_color = lighten_color(color)
        view = paths[paths["age_group"].eq(age_group)]
        control = view[view["scenario_role"].eq("control")].sort_values("t")
        treated = view[view["scenario_role"].eq("treated")].sort_values("t")
        ax.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.7, zorder=0)
        ax.axhline(100, color=GRID, linewidth=0.9, zorder=1)
        ax.axvline(0, color="#777777", linewidth=0.9, linestyle=":", zorder=1)
        ax.plot(
            control["t"],
            control["flow_index"],
            color=control_color,
            linewidth=1.65,
            linestyle=(0, (4, 2.5)),
            zorder=2,
        )
        ax.plot(
            treated["t"],
            treated["flow_index"],
            color=color,
            linewidth=2.25 if age_group == "age_22_25" else 2.0,
            zorder=3,
        )
        ax.set_title(AGE_LABELS[age_group], loc="left", color=color, fontweight="bold", fontsize=11)
        ax.set_xlim(EVENT_MIN, EVENT_MAX)
        ax.set_ylim(lower - padding, upper + padding)
        ax.set_xticks([-12, -6, 0, 6, 12, 18, 24])
        ax.grid(axis="x", visible=False)
        if age_group == "age_22_25" and annotation:
            effect = float(annotation["effect_pct"])
            sign = "+" if effect > 0 else ""
            ax.text(
                0.025,
                0.055,
                (
                    f"DDD 22-25 vs demais: {sign}{effect:.1f}%\n"
                    f"{_format_p_value(float(annotation['p_value']))}; "
                    f"pretrend linear {_status_pt(str(annotation['pretrend_status']))}"
                ).replace(".", ","),
                transform=ax.transAxes,
                ha="left",
                va="bottom",
                fontsize=8.2,
                color=TEXT_DARK,
                bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": color, "alpha": 0.94},
            )

    from matplotlib.lines import Line2D

    legend_handles = [
        Line2D([0], [0], color=TEXT_DARK, linewidth=2.3, label="Núcleo de Software e TI"),
        Line2D([0], [0], color="#A9A9A9", linewidth=1.7, linestyle=(0, (4, 2.5)), label="Not Exposed"),
    ]
    fig.legend(handles=legend_handles, loc="upper right", bbox_to_anchor=(0.985, 0.905), frameon=False, ncol=2)
    fig.suptitle(
        f"{spec['figure_path_label']}: Trajetórias de {spec['label_lower']} por idade",
        x=0.075,
        y=0.965,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.075,
        0.91,
        "Séries em tempo de evento, normalizadas pela média pré-ChatGPT de log(1 + fluxo) "
        "de cada CBO e faixa etária (=100).",
        ha="left",
        va="top",
        fontsize=9.5,
        color=TEXT_MUTED,
    )
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.09, fontsize=10)
    fig.supylabel(f"Índice de {spec['label_lower']} (média pré=100)", x=0.018, fontsize=10)
    fig.text(
        0.075,
        0.025,
        "Nota: média não ponderada das variações em log(1 + fluxo) entre CBOs. "
        "Linhas escuras: tratamento (4 CBOs); linhas claras tracejadas: controle estrito "
        "(266 CBOs). Séries descritivas; a inferência causal está no DDD.",
        ha="left",
        va="bottom",
        fontsize=7.8,
        color=TEXT_MUTED,
    )
    save_figure(fig, output_path)


def plot_ddd_event_studies(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    output_path: Path,
    outcome: str,
) -> None:
    spec = OUTCOME_SPECS[outcome]
    plt = get_pyplot()
    setup_plot_style()
    fig, axes = plt.subplots(2, 3, figsize=(13.8, 8.2), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.165, hspace=0.39, wspace=0.18)
    bounds = coefficients[["ci_low", "ci_high"]].apply(pd.to_numeric, errors="coerce").to_numpy().ravel()
    bounds = bounds[np.isfinite(bounds)]
    max_abs = max(0.05, float(np.abs(bounds).max()) if bounds.size else 0.05)
    ylim = (-1.06 * max_abs, 1.06 * max_abs)

    for ax, age_group in zip(axes.flat, AGE_ORDER):
        color = AGE_COLORS[age_group]
        view = coefficients[
            coefficients["age_group"].eq(age_group)
            & coefficients["coefficient_status"].isin(["estimated", "reference"])
        ].sort_values("t")
        pre = pretrends[pretrends["age_group"].eq(age_group)]
        status = "not_available" if pre.empty else str(pre["pretrend_status"].iloc[0])
        ax.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.7, zorder=0)
        ax.axhline(0, color="#333333", linewidth=0.9, zorder=1)
        ax.axvline(REFERENCE_PERIOD, color="#777777", linewidth=0.8, linestyle="--", zorder=1)
        ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":", zorder=1)
        if not view.empty:
            x = view["t"].astype(float).to_numpy()
            y = view["coef"].astype(float).to_numpy()
            ax.plot(x, y, color=color, linewidth=1.9, marker="o", markersize=2.8, zorder=3)
            band = view.dropna(subset=["ci_low", "ci_high"])
            ax.fill_between(
                band["t"].astype(float).to_numpy(),
                band["ci_low"].astype(float).to_numpy(),
                band["ci_high"].astype(float).to_numpy(),
                color=color,
                alpha=0.16,
                zorder=2,
            )
        ax.set_title(AGE_LABELS[age_group], loc="left", color=color, fontweight="bold", fontsize=11)
        ax.text(
            0.99,
            0.97,
            f"pretrend dinâmico: {_status_pt(status)}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=7.8,
            color=TEXT_MUTED,
        )
        ax.set_xlim(EVENT_MIN, EVENT_MAX)
        ax.set_ylim(*ylim)
        ax.set_xticks([-12, -6, 0, 6, 12, 18, 24])
        ax.grid(axis="x", visible=False)

    fig.suptitle(
        f"{spec['figure_event_label']}: Event study DDD de {spec['label_lower']} por idade",
        x=0.075,
        y=0.965,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.075,
        0.91,
        "Coeficientes dinâmicos da interação tripla: Software/TI vs Not Exposed × "
        "faixa etária vs demais idades × tempo de evento.",
        ha="left",
        va="top",
        fontsize=9.3,
        color=TEXT_MUTED,
    )
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0); referência: t=-1", y=0.095, fontsize=10)
    fig.supylabel(f"Coeficiente DDD em log(1 + {spec['label_lower']})", x=0.018, fontsize=10)
    fig.text(
        0.075,
        0.025,
        "Nota: IC de 95%; pretrend dinâmico é o teste conjunto dos coeficientes em "
        "t=-12,...,-2; efeitos fixos de CBO, mês e subgrupo; controles de composição; "
        "erros-padrão clusterizados por CBO. "
        "Tratamento: 4 CBOs do Núcleo de Software e TI; controle estrito: 266 CBOs Not Exposed.",
        ha="left",
        va="bottom",
        fontsize=7.8,
        color=TEXT_MUTED,
    )
    save_figure(fig, output_path)


def validate_outputs(paths: pd.DataFrame, coefficients: pd.DataFrame, pretrends: pd.DataFrame, outcome: str) -> None:
    expected_path_rows = len(AGE_ORDER) * 2 * len(EVENT_TIMES)
    expected_coefficient_rows = len(AGE_ORDER) * len(EVENT_TIMES)
    if len(paths) != expected_path_rows:
        raise RuntimeError(f"{outcome} normalized paths have {len(paths)} rows; expected {expected_path_rows}.")
    if len(coefficients) != expected_coefficient_rows:
        raise RuntimeError(
            f"{outcome} DDD coefficients have {len(coefficients)} rows; expected {expected_coefficient_rows}."
        )
    if len(pretrends) != len(AGE_ORDER):
        raise RuntimeError(f"{outcome} pretrend table must contain one row per age band.")
    if set(paths["scenario_role"]) != {"treated", "control"}:
        raise RuntimeError(f"{outcome} normalized paths do not contain both treatment roles.")
    if coefficients["coef"].dropna().empty:
        raise RuntimeError(f"{outcome} DDD event study contains no estimated coefficients.")


def run(figure_dir: Path = OUTPUT_FIGURE_DIR, table_dir: Path = OUTPUT_TABLE_DIR) -> None:
    required = [CLASSIFICATION_PATH, PANEL_PATH]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    classification = pd.read_csv(CLASSIFICATION_PATH, dtype={"cbo_4d": str})
    roles = build_strict_software_it_roles(classification)
    log(
        f"Strict sample: {(roles['scenario_role'] == 'treated').sum()} treated CBOs and "
        f"{(roles['scenario_role'] == 'control').sum()} Not Exposed CBOs."
    )
    flow_panel = reconstruct_age_flow_panel(sorted(DATA_RAW.glob("caged_*.parquet")), roles)
    controls = load_controls()
    log(f"Completed flow panel: {len(flow_panel):,} CBO-age-month rows.".replace(",", "."))
    figure_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    for outcome, spec in OUTCOME_SPECS.items():
        paths = build_flow_paths(flow_panel, outcome)
        coefficients, pretrends = estimate_all_dynamic_ddd(flow_panel, controls, outcome)
        validate_outputs(paths, coefficients, pretrends, outcome)

        path_csv = table_dir / str(spec["path_csv"])
        event_csv = table_dir / str(spec["event_csv"])
        pretrend_csv = table_dir / str(spec["pretrend_csv"])
        paths.to_csv(path_csv, index=False)
        coefficients.to_csv(event_csv, index=False)
        pretrends.to_csv(pretrend_csv, index=False)
        plot_normalized_flow_paths(
            paths,
            figure_dir / str(spec["path_figure"]),
            outcome,
            load_average_ddd_annotation(outcome),
        )
        plot_ddd_event_studies(
            coefficients,
            pretrends,
            figure_dir / str(spec["event_figure"]),
            outcome,
        )
        log(f"Wrote {spec['label_lower']} paths and DDD event-study outputs.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure-dir", type=Path, default=OUTPUT_FIGURE_DIR)
    parser.add_argument("--table-dir", type=Path, default=OUTPUT_TABLE_DIR)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.figure_dir, args.table_dir)
