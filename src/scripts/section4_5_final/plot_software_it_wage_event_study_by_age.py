#!/usr/bin/env python3
"""Build dynamic age DDD estimates for real admission wages in Software/IT.

The target age band is compared with all other Canaries-style age bands inside
the strict four-CBO Software/IT treatment and the matched ``Not Exposed``
control. Wage means are reconstructed from positive-wage admissions and the
dynamic specification uses ``t=-1`` as its event-time reference.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from section4_5_final.plot_software_it_flow_event_studies_by_age import (  # noqa: E402
    CONTROL_COLUMNS,
    REFERENCE_PERIOD,
    estimate_dynamic_ddd,
    load_controls,
    raw_path_overlaps_event_window,
)
from section4_5_final.plot_software_it_wage_paths_by_age import (  # noqa: E402
    AGE_COLORS,
    AGE_LABELS,
    AGE_ORDER,
    CLASSIFICATION_PATH,
    DATA_RAW,
    EVENT_MAX,
    EVENT_MIN,
    IPCA_PATH,
    ROOT,
    build_strict_software_it_roles,
    reconstruct_age_wage_panel,
)
from section4_5_final.style import (  # noqa: E402
    TEXT_DARK,
    TEXT_MUTED,
    get_pyplot,
    save_figure,
    setup_plot_style,
)


OUTCOME = "ln_salario_real_adm"
PANEL_PATH = ROOT / "data" / "output" / "painel_2b_ready.parquet"
OUTPUT_FIGURE_PATH = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "figures"
    / "figure_5_2e_experimental_software_it_admission_wage_ddd_event_study_by_age.png"
)
OUTPUT_EVENT_CSV_PATH = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "tables"
    / "figure_5_2e_experimental_software_it_admission_wage_ddd_event_study_by_age.csv"
)
OUTPUT_PRETREND_CSV_PATH = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "tables"
    / "figure_5_2e_experimental_software_it_admission_wage_ddd_pretrends.csv"
)


def log(message: str) -> None:
    print(f"[software_it_wage_event_study] {message}", flush=True)


def build_wage_pair_panel(
    wage_panel: pd.DataFrame,
    controls: pd.DataFrame,
    age_group: str,
    roles: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create target/complement wage rows on the Stage 2 CBO-month support."""
    if age_group not in AGE_ORDER:
        raise ValueError(f"Unsupported age group: {age_group}")
    wage_columns = {
        "cbo_4d",
        "age_group",
        "ano",
        "mes",
        "t",
        "salary_sum",
        "wage_count",
        "indice",
        "scenario_role",
        "scenario_treat",
    }
    missing_wage = sorted(wage_columns - set(wage_panel.columns))
    if missing_wage:
        raise RuntimeError(f"Age-wage panel is missing columns: {missing_wage}")
    control_keys = ["cbo_4d", "ano", "mes", "periodo", "t"]
    missing_controls = sorted(set(control_keys + CONTROL_COLUMNS) - set(controls.columns))
    if missing_controls:
        raise RuntimeError(f"Control panel is missing columns: {missing_controls}")

    if roles is None:
        roles = wage_panel[["cbo_4d", "scenario_role", "scenario_treat"]].drop_duplicates()
    else:
        roles = roles[["cbo_4d", "scenario_role", "scenario_treat"]].drop_duplicates()
    if roles["cbo_4d"].duplicated().any():
        raise RuntimeError("Treatment roles contain duplicate CBO definitions.")

    data = wage_panel.copy()
    data["salary_sum"] = pd.to_numeric(data["salary_sum"], errors="coerce")
    data["wage_count"] = pd.to_numeric(data["wage_count"], errors="coerce")
    data["indice"] = pd.to_numeric(data["indice"], errors="coerce")
    group_keys = ["cbo_4d", "ano", "mes", "t", "indice"]
    target = (
        data[data["age_group"].eq(age_group)]
        .groupby(group_keys, observed=True)[["salary_sum", "wage_count"]]
        .sum()
        .reset_index()
    )
    target["subgroup"] = "target"
    complement = (
        data[~data["age_group"].eq(age_group)]
        .groupby(group_keys, observed=True)[["salary_sum", "wage_count"]]
        .sum()
        .reset_index()
    )
    complement["subgroup"] = "complement"
    observed = pd.concat([target, complement], ignore_index=True)
    has_wage = observed["wage_count"].gt(0) & observed["salary_sum"].gt(0)
    observed["salario_adm"] = np.where(
        has_wage,
        observed["salary_sum"] / observed["wage_count"],
        np.nan,
    )
    observed["salario_real_adm"] = observed["salario_adm"] * (100.0 / observed["indice"])
    observed[OUTCOME] = np.log(observed["salario_real_adm"].where(observed["salario_real_adm"].gt(0)))

    control_view = controls[control_keys + CONTROL_COLUMNS].drop_duplicates(control_keys)
    if len(control_view) != len(controls):
        raise RuntimeError("Stage 2 controls contain duplicate CBO-month rows.")
    base = control_view.merge(roles, on="cbo_4d", how="inner", validate="many_to_one")
    subgroup = pd.DataFrame({"subgroup": ["target", "complement"]})
    base = (
        base.assign(_cross_key=1)
        .merge(subgroup.assign(_cross_key=1), on="_cross_key")
        .drop(columns="_cross_key")
    )
    observed_keys = ["cbo_4d", "ano", "mes", "t", "subgroup"]
    observed_view = observed[
        observed_keys
        + ["salary_sum", "wage_count", "indice", "salario_adm", "salario_real_adm", OUTCOME]
    ]
    out = base.merge(observed_view, on=observed_keys, how="left", validate="one_to_one")
    if out.empty:
        raise RuntimeError(f"No eligible Stage 2 support remains for {age_group}.")
    out["age_group"] = age_group
    return out.sort_values(["subgroup", "cbo_4d", "t"]).reset_index(drop=True)


def plot_wage_ddd_event_studies(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    output_path: Path,
) -> None:
    """Plot one dynamic DDD panel per Canaries-style age band."""
    required_coefficients = {
        "age_group",
        "t",
        "coef",
        "ci_low",
        "ci_high",
        "coefficient_status",
    }
    missing = sorted(required_coefficients - set(coefficients.columns))
    if missing:
        raise RuntimeError(f"Wage DDD coefficients are missing columns: {missing}")
    if not {"age_group", "pretrend_status"}.issubset(pretrends.columns):
        raise RuntimeError("Wage DDD pretrends are missing age_group or pretrend_status.")

    plt = get_pyplot()
    setup_plot_style()
    fig, axes = plt.subplots(2, 3, figsize=(13.8, 8.2), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.18, hspace=0.39, wspace=0.18)
    bounds = coefficients[["ci_low", "ci_high"]].apply(pd.to_numeric, errors="coerce").to_numpy().ravel()
    bounds = bounds[np.isfinite(bounds)]
    max_abs = max(0.03, float(np.abs(bounds).max()) if bounds.size else 0.03)
    ylim = (-1.06 * max_abs, 1.06 * max_abs)
    status_labels = {"pass": "aprovado", "warning": "com alerta", "fail": "reprovado"}

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
            f"pretrend dinâmico: {status_labels.get(status, status)}",
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
        "Figura 5.2E (teste): Event study DDD do salário real de admissão por idade",
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
    fig.supxlabel(
        "Meses relativos ao lançamento do ChatGPT (t=0); referência: t=-1",
        y=0.095,
        fontsize=10,
    )
    fig.supylabel("Coeficiente DDD em log do salário real de admissão", x=0.018, fontsize=10)
    fig.text(
        0.075,
        0.025,
        "Nota: IC de 95%; pretrend dinâmico é o teste conjunto dos coeficientes em "
        "t=-12,...,-2; efeitos fixos de CBO, mês e subgrupo; controles de composição; "
        "erros-padrão clusterizados por CBO.\nSalários deflacionados pelo IPCA; médias "
        "ponderadas pelas admissões, sem winsorização adicional. Tratamento: 4 CBOs; "
        "controle estrito elegível: 266 CBOs Not Exposed.",
        ha="left",
        va="bottom",
        fontsize=7.8,
        color=TEXT_MUTED,
    )
    save_figure(fig, output_path)


def estimate_all_wage_dynamic_ddd(
    wage_panel: pd.DataFrame,
    controls: pd.DataFrame,
    roles: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefficient_rows: list[pd.DataFrame] = []
    pretrend_rows: list[dict[str, object]] = []
    for age_group in AGE_ORDER:
        log(f"Estimating {OUTCOME} dynamic DDD for {age_group}...")
        pair = build_wage_pair_panel(wage_panel, controls, age_group, roles=roles)
        coefficients, pretrend = estimate_dynamic_ddd(pair, age_group, OUTCOME)
        coefficient_rows.append(coefficients)
        pretrend_rows.append(pretrend)
    return pd.concat(coefficient_rows, ignore_index=True), pd.DataFrame(pretrend_rows)


def validate_event_outputs(coefficients: pd.DataFrame, pretrends: pd.DataFrame) -> None:
    expected_coefficient_rows = len(AGE_ORDER) * (EVENT_MAX - EVENT_MIN + 1)
    if len(coefficients) != expected_coefficient_rows:
        raise RuntimeError(
            f"Wage DDD coefficients have {len(coefficients)} rows; "
            f"expected {expected_coefficient_rows}."
        )
    if len(pretrends) != len(AGE_ORDER):
        raise RuntimeError("Wage DDD pretrends must contain one row per age band.")
    if set(coefficients["age_group"]) != set(AGE_ORDER):
        raise RuntimeError("Wage DDD coefficients do not cover every age band.")
    if set(coefficients["t"]) != set(range(EVENT_MIN, EVENT_MAX + 1)):
        raise RuntimeError("Wage DDD coefficients do not cover the full event window.")
    reference = coefficients[coefficients["t"].eq(REFERENCE_PERIOD)]
    if len(reference) != len(AGE_ORDER) or not np.allclose(reference["coef"], 0.0):
        raise RuntimeError("Wage DDD reference-period coefficients are invalid.")
    if coefficients["coef"].dropna().empty:
        raise RuntimeError("Wage DDD event study contains no estimated coefficients.")


def run(
    figure_path: Path = OUTPUT_FIGURE_PATH,
    event_csv_path: Path = OUTPUT_EVENT_CSV_PATH,
    pretrend_csv_path: Path = OUTPUT_PRETREND_CSV_PATH,
) -> None:
    required_paths = [CLASSIFICATION_PATH, IPCA_PATH, PANEL_PATH]
    missing = [str(path) for path in required_paths if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    raw_paths = [
        path
        for path in sorted(DATA_RAW.glob("caged_*.parquet"))
        if raw_path_overlaps_event_window(path)
    ]
    if not raw_paths:
        raise FileNotFoundError(f"No CAGED parquet files overlap the event window in {DATA_RAW}.")

    classification = pd.read_csv(CLASSIFICATION_PATH, dtype={"cbo_4d": str})
    roles = build_strict_software_it_roles(classification)
    log(
        f"Strict sample: {(roles['scenario_role'] == 'treated').sum()} treated CBOs and "
        f"{(roles['scenario_role'] == 'control').sum()} Not Exposed CBOs."
    )
    ipca = pd.read_parquet(IPCA_PATH)
    wage_panel = reconstruct_age_wage_panel(raw_paths, roles, ipca)
    controls = load_controls(PANEL_PATH)
    log(f"Reconstructed {len(wage_panel):,} observed CBO-age-month wage rows.".replace(",", "."))
    log("Dynamic DDD uses the retained raw wage sums; P1/P99 fields apply only to descriptive paths.")
    coefficients, pretrends = estimate_all_wage_dynamic_ddd(wage_panel, controls, roles)
    validate_event_outputs(coefficients, pretrends)

    event_csv_path.parent.mkdir(parents=True, exist_ok=True)
    pretrend_csv_path.parent.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(event_csv_path, index=False)
    pretrends.to_csv(pretrend_csv_path, index=False)
    plot_wage_ddd_event_studies(coefficients, pretrends, figure_path)
    log(f"Wrote dynamic coefficients to {event_csv_path}")
    log(f"Wrote pretrend diagnostics to {pretrend_csv_path}")
    log(f"Wrote figure to {figure_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", type=Path, default=OUTPUT_FIGURE_PATH)
    parser.add_argument("--event-csv", type=Path, default=OUTPUT_EVENT_CSV_PATH)
    parser.add_argument("--pretrend-csv", type=Path, default=OUTPUT_PRETREND_CSV_PATH)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.figure, args.event_csv, args.pretrend_csv)
