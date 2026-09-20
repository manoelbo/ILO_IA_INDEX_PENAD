#!/usr/bin/env python3
"""Plot normalized real admission-wage paths by age for Software/IT.

This is a descriptive event-time companion to the triple-difference estimates
reported in Table 5.3. It reconstructs age-specific admission wages from the
raw CAGED microdata, keeps the strict comparison between the four Software/IT
CBOs and matched ``Not Exposed`` CBOs, and normalizes every CBO-age path to its
own pre-ChatGPT mean.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from section4_5_final.style import (  # noqa: E402
    GRID,
    TEXT_DARK,
    TEXT_MUTED,
    get_pyplot,
    save_figure,
    setup_plot_style,
)


ROOT = Path(__file__).resolve().parents[3]
DATA_RAW = ROOT / "data" / "raw"
IPCA_PATH = ROOT / "data" / "processed" / "ipca_mensal.parquet"
CLASSIFICATION_PATH = ROOT / "outputs" / "treatment_scenario_grid" / "scenario_cbo_classification.csv"
HETEROGENEITY_PATH = (
    ROOT
    / "outputs"
    / "dissertation_section4"
    / "manual_occupation_groups_extension"
    / "tables"
    / "occupation_group_canaries_age_heterogeneity.csv"
)
DEFAULT_FIGURE_PATH = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "figures"
    / "figure_5_2_experimental_software_it_wage_paths_by_age.png"
)
DEFAULT_CSV_PATH = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "tables"
    / "figure_5_2_experimental_software_it_wage_paths_by_age.csv"
)

MATCHED_MTE_STATUS = "matched_official_mte"
SOFTWARE_IT_CBO = frozenset({"2123", "2124", "3171", "3172"})
EVENT_MIN = -12
EVENT_MAX = 24
PRE_MIN = -12
PRE_MAX = -1
TREATMENT_YEAR = 2022
TREATMENT_MONTH = 12
RAW_BATCH_SIZE = 1_000_000
WAGE_WINSOR_LOWER = 0.01
WAGE_WINSOR_UPPER = 0.99

AGE_ORDER = ["age_22_25", "age_26_30", "age_31_34", "age_35_40", "age_41_49", "age_50_plus"]
AGE_LABELS = {
    "age_22_25": "22-25 anos",
    "age_26_30": "26-30 anos",
    "age_31_34": "31-34 anos",
    "age_35_40": "35-40 anos",
    "age_41_49": "41-49 anos",
    "age_50_plus": "50+ anos",
}
AGE_COLORS = {
    "age_22_25": "#0072B2",
    "age_26_30": "#E69F00",
    "age_31_34": "#009E73",
    "age_35_40": "#CC79A7",
    "age_41_49": "#D55E00",
    "age_50_plus": "#6A51A3",
}


def log(message: str) -> None:
    print(f"[software_it_wage_paths] {message}", flush=True)


def normalize_cbo(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True).str[:4].str.zfill(4)


def assign_canaries_age_band(age: pd.Series) -> pd.Series:
    values = pd.to_numeric(age, errors="coerce")
    out = pd.Series(pd.NA, index=age.index, dtype="string")
    out.loc[values.between(22, 25, inclusive="both")] = "age_22_25"
    out.loc[values.between(26, 30, inclusive="both")] = "age_26_30"
    out.loc[values.between(31, 34, inclusive="both")] = "age_31_34"
    out.loc[values.between(35, 40, inclusive="both")] = "age_35_40"
    out.loc[values.between(41, 49, inclusive="both")] = "age_41_49"
    out.loc[values.ge(50)] = "age_50_plus"
    return out


def build_strict_software_it_roles(classification: pd.DataFrame) -> pd.DataFrame:
    required = {"cbo_4d", "mte_match_status", "cbo_ilo_gradient"}
    missing = sorted(required - set(classification.columns))
    if missing:
        raise RuntimeError(f"Scenario classification is missing required columns: {missing}")

    data = classification.copy()
    data["cbo_4d"] = normalize_cbo(data["cbo_4d"])
    matched = data["mte_match_status"].eq(MATCHED_MTE_STATUS)
    treated = matched & data["cbo_4d"].isin(SOFTWARE_IT_CBO)
    control = matched & data["cbo_ilo_gradient"].eq("Not Exposed") & ~data["cbo_4d"].isin(SOFTWARE_IT_CBO)
    included = data.loc[treated | control, ["cbo_4d", "mte_match_status", "cbo_ilo_gradient"]].copy()
    included["scenario_role"] = np.where(included["cbo_4d"].isin(SOFTWARE_IT_CBO), "treated", "control")
    included["scenario_treat"] = included["scenario_role"].eq("treated").astype(int)

    observed_treated = set(included.loc[included["scenario_role"].eq("treated"), "cbo_4d"])
    if observed_treated != set(SOFTWARE_IT_CBO):
        raise RuntimeError(
            "The strict Software/IT treatment must contain exactly CBOs "
            f"{sorted(SOFTWARE_IT_CBO)}; found {sorted(observed_treated)}."
        )
    if included.loc[included["scenario_role"].eq("control"), "cbo_ilo_gradient"].ne("Not Exposed").any():
        raise RuntimeError("The strict control contains a CBO outside Not Exposed.")
    if included["cbo_4d"].duplicated().any():
        raise RuntimeError("Scenario classification contains duplicate included CBOs.")
    return included.reset_index(drop=True)


def event_time(year: pd.Series, month: pd.Series) -> pd.Series:
    return (pd.to_numeric(year, errors="coerce") - TREATMENT_YEAR) * 12 + (
        pd.to_numeric(month, errors="coerce") - TREATMENT_MONTH
    )


def _filtered_raw_batch(batch: pa.RecordBatch, eligible_cbo: pa.Array) -> pd.DataFrame:
    table = pa.Table.from_batches([batch])
    cbo_4d = pc.utf8_slice_codeunits(table["cbo_2002"], start=0, stop=4)
    t = pc.add(
        pc.multiply(pc.subtract(table["ano"], TREATMENT_YEAR), 12),
        pc.subtract(table["mes"], TREATMENT_MONTH),
    )
    mask = pc.and_kleene(
        pc.and_kleene(pc.equal(table["saldo_movimentacao"], 1), pc.greater(table["salario_mensal"], 0)),
        pc.and_kleene(
            pc.is_in(cbo_4d, value_set=eligible_cbo),
            pc.and_kleene(pc.greater_equal(t, EVENT_MIN), pc.less_equal(t, EVENT_MAX)),
        ),
    )
    mask = pc.and_kleene(mask, pc.greater_equal(table["idade"], 22))
    filtered = table.filter(mask)
    if filtered.num_rows == 0:
        return pd.DataFrame()
    out = filtered.select(["ano", "mes", "cbo_2002", "idade", "salario_mensal"]).to_pandas()
    out["cbo_4d"] = normalize_cbo(out["cbo_2002"])
    out["age_group"] = assign_canaries_age_band(out["idade"])
    out["t"] = event_time(out["ano"], out["mes"]).astype(int)
    return out.dropna(subset=["age_group", "salario_mensal"])


def winsorize_age_wage_panel(
    panel: pd.DataFrame,
    lower_q: float = WAGE_WINSOR_LOWER,
    upper_q: float = WAGE_WINSOR_UPPER,
) -> pd.DataFrame:
    if not 0 <= lower_q < upper_q <= 1:
        raise ValueError("Winsorization quantiles must satisfy 0 <= lower_q < upper_q <= 1.")
    required = {"salario_adm", "indice"}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Cannot winsorize age-wage panel; missing columns: {missing}")
    out = panel.copy()
    lower, upper = out["salario_adm"].quantile([lower_q, upper_q]).astype(float)
    if not np.isfinite(lower) or not np.isfinite(upper) or lower <= 0 or upper <= lower:
        raise RuntimeError(f"Invalid wage winsorization bounds: lower={lower}, upper={upper}.")
    out["salario_adm_raw"] = out["salario_adm"]
    out["salario_adm"] = out["salario_adm"].clip(lower=lower, upper=upper)
    out["salario_real_adm"] = out["salario_adm"] * (100.0 / out["indice"])
    out["ln_salario_real_adm"] = np.log(out["salario_real_adm"].clip(lower=1))
    out.attrs["wage_winsor_bounds"] = (lower, upper)
    return out


def reconstruct_age_wage_panel(raw_paths: list[Path], roles: pd.DataFrame, ipca: pd.DataFrame) -> pd.DataFrame:
    if not raw_paths:
        raise FileNotFoundError(f"No CAGED parquet files found in {DATA_RAW}.")
    required_ipca = {"ano", "mes", "indice"}
    if not required_ipca.issubset(ipca.columns):
        raise RuntimeError(f"IPCA data is missing columns: {sorted(required_ipca - set(ipca.columns))}")

    eligible = pa.array(sorted(roles["cbo_4d"].unique()), type=pa.string())
    pieces: list[pd.DataFrame] = []
    raw_columns = ["ano", "mes", "cbo_2002", "idade", "saldo_movimentacao", "salario_mensal"]
    for path in raw_paths:
        log(f"Scanning {path.name}...")
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(batch_size=RAW_BATCH_SIZE, columns=raw_columns):
            data = _filtered_raw_batch(batch, eligible)
            if data.empty:
                continue
            grouped = (
                data.groupby(["cbo_4d", "age_group", "ano", "mes", "t"], observed=True)["salario_mensal"]
                .agg(salary_sum="sum", wage_count="count")
                .reset_index()
            )
            pieces.append(grouped)

    if not pieces:
        raise RuntimeError("No eligible Software/IT or Not Exposed admission-wage observations were reconstructed.")
    panel = (
        pd.concat(pieces, ignore_index=True)
        .groupby(["cbo_4d", "age_group", "ano", "mes", "t"], observed=True)
        .agg(salary_sum=("salary_sum", "sum"), wage_count=("wage_count", "sum"))
        .reset_index()
    )
    panel["salario_adm"] = panel["salary_sum"] / panel["wage_count"]
    panel = panel.merge(ipca[["ano", "mes", "indice"]], on=["ano", "mes"], how="left", validate="many_to_one")
    if panel["indice"].isna().any() or panel["indice"].le(0).any():
        missing = panel.loc[panel["indice"].isna() | panel["indice"].le(0), ["ano", "mes"]].drop_duplicates()
        raise RuntimeError(f"Missing or invalid IPCA values for periods:\n{missing.to_string(index=False)}")
    panel = winsorize_age_wage_panel(panel)
    lower, upper = panel.attrs["wage_winsor_bounds"]
    log(f"Winsorized CBO-age-month mean wages at P1/P99: {lower:,.2f} to {upper:,.2f}.")
    panel = panel.merge(roles[["cbo_4d", "scenario_role", "scenario_treat"]], on="cbo_4d", how="inner", validate="many_to_one")
    return panel.sort_values(["age_group", "scenario_role", "cbo_4d", "t"]).reset_index(drop=True)


def build_normalized_paths(panel: pd.DataFrame, pre_min: int = PRE_MIN, pre_max: int = PRE_MAX) -> pd.DataFrame:
    required = {"cbo_4d", "age_group", "scenario_role", "t", "ln_salario_real_adm"}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Age-wage panel is missing required columns: {missing}")
    if pre_min > pre_max:
        raise ValueError("pre_min must not exceed pre_max.")

    data = panel.copy()
    data = data[
        data["age_group"].isin(AGE_ORDER)
        & data["scenario_role"].isin(["treated", "control"])
        & data["t"].between(EVENT_MIN, EVENT_MAX)
    ].copy()
    data["log_wage"] = pd.to_numeric(data["ln_salario_real_adm"], errors="coerce")
    data = data.dropna(subset=["log_wage"])
    keys = ["cbo_4d", "age_group", "scenario_role"]
    baseline = (
        data[data["t"].between(pre_min, pre_max)]
        .groupby(keys, observed=True)["log_wage"]
        .agg(pre_log_wage="mean", n_pre_periods="count")
        .reset_index()
    )
    baseline = baseline[np.isfinite(baseline["pre_log_wage"])].copy()
    data = data.merge(baseline, on=keys, how="inner", validate="many_to_one")
    if data.empty:
        raise RuntimeError("No CBO-age paths have a valid pre-event wage baseline.")
    data["cbo_log_change"] = data["log_wage"] - data["pre_log_wage"]

    out = (
        data.groupby(["age_group", "scenario_role", "t"], observed=True)["cbo_log_change"]
        .agg(mean_log_change="mean", sd_log_change="std", n_cbo="count")
        .reset_index()
    )
    out["se_log_change"] = out["sd_log_change"] / np.sqrt(out["n_cbo"])
    out["wage_index"] = 100.0 * np.exp(out["mean_log_change"])
    out["ci_low"] = 100.0 * np.exp(out["mean_log_change"] - 1.96 * out["se_log_change"])
    out["ci_high"] = 100.0 * np.exp(out["mean_log_change"] + 1.96 * out["se_log_change"])
    out["age_label"] = out["age_group"].map(AGE_LABELS)
    out["role_label"] = out["scenario_role"].map(
        {"treated": "Núcleo de Software e TI", "control": "Not Exposed"}
    )
    order = {age: index for index, age in enumerate(AGE_ORDER)}
    out["_age_order"] = out["age_group"].map(order)
    return out.sort_values(["_age_order", "scenario_role", "t"]).drop(columns="_age_order").reset_index(drop=True)


def lighten_color(hex_color: str, amount: float = 0.58) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    rgb = np.array([int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4)])
    return tuple(rgb + (1.0 - rgb) * amount)


def load_young_ddd_annotation(path: Path = HETEROGENEITY_PATH) -> dict[str, object] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    results = pd.read_csv(path)
    required = {"group_id", "heterogeneity_group_id", "outcome", "coef", "p_value", "pretrend_status"}
    if not required.issubset(results.columns):
        return None
    row = results[
        results["group_id"].eq("software_it_core")
        & results["heterogeneity_group_id"].eq("age_22_25")
        & results["outcome"].eq("ln_salario_real_adm")
    ]
    if len(row) != 1:
        return None
    item = row.iloc[0]
    return {
        "effect_pct": 100.0 * math.expm1(float(item["coef"])),
        "p_value": float(item["p_value"]),
        "pretrend_status": str(item["pretrend_status"]),
    }


def plot_normalized_paths(
    paths: pd.DataFrame,
    output_path: Path,
    annotation: dict[str, object] | None = None,
) -> None:
    required = {"age_group", "scenario_role", "t", "wage_index", "n_cbo"}
    missing = sorted(required - set(paths.columns))
    if missing:
        raise RuntimeError(f"Normalized paths are missing required columns: {missing}")

    plt = get_pyplot()
    setup_plot_style()
    fig, axes = plt.subplots(2, 3, figsize=(13.8, 8.2), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.155, hspace=0.36, wspace=0.18)

    values = pd.to_numeric(paths["wage_index"], errors="coerce").dropna()
    if values.empty:
        raise RuntimeError("Normalized paths contain no numeric wage-index values.")
    lower = min(float(values.min()), 100.0)
    upper = max(float(values.max()), 100.0)
    padding = max(2.0, 0.08 * (upper - lower if upper > lower else 1.0))
    ylim = (lower - padding, upper + padding)

    for ax, age_group in zip(axes.flat, AGE_ORDER):
        color = AGE_COLORS[age_group]
        control_color = lighten_color(color)
        view = paths[paths["age_group"].eq(age_group)].copy()
        control = view[view["scenario_role"].eq("control")].sort_values("t")
        treated = view[view["scenario_role"].eq("treated")].sort_values("t")

        ax.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.7, zorder=0)
        ax.axhline(100, color=GRID, linewidth=0.9, zorder=1)
        ax.axvline(0, color="#777777", linewidth=0.9, linestyle=":", zorder=1)
        if not control.empty:
            ax.plot(
                control["t"],
                control["wage_index"],
                color=control_color,
                linewidth=1.65,
                linestyle=(0, (4, 2.5)),
                zorder=2,
            )
        if not treated.empty:
            ax.plot(
                treated["t"],
                treated["wage_index"],
                color=color,
                linewidth=2.25 if age_group == "age_22_25" else 2.0,
                zorder=3,
            )
        ax.set_title(AGE_LABELS[age_group], loc="left", color=color, fontweight="bold", fontsize=11)
        ax.set_xlim(EVENT_MIN, EVENT_MAX)
        ax.set_ylim(*ylim)
        ax.set_xticks([-12, -6, 0, 6, 12, 18, 24])
        ax.grid(axis="x", visible=False)

        if age_group == "age_22_25" and annotation:
            effect = float(annotation["effect_pct"])
            p_value = float(annotation["p_value"])
            p_text = "p<0,01" if p_value < 0.01 else f"p={p_value:.3f}".replace(".", ",")
            pretrend = {"pass": "aprovado", "warning": "com alerta", "fail": "reprovado"}.get(
                str(annotation["pretrend_status"]), str(annotation["pretrend_status"])
            )
            ax.text(
                0.025,
                0.055,
                f"DDD 22-25 vs demais: {effect:.1f}%\n{p_text}; pretrend {pretrend}".replace(".", ","),
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
        Line2D(
            [0],
            [0],
            color="#A9A9A9",
            linewidth=1.7,
            linestyle=(0, (4, 2.5)),
            label="Not Exposed",
        ),
    ]
    fig.legend(handles=legend_handles, loc="upper right", bbox_to_anchor=(0.985, 0.905), frameon=False, ncol=2)
    fig.suptitle(
        "Figura 5.2 (teste): Trajetórias do salário real de admissão por idade",
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
        "Séries em tempo de evento, normalizadas pela média pré-ChatGPT de cada CBO e faixa etária (=100).",
        ha="left",
        va="top",
        fontsize=9.5,
        color=TEXT_MUTED,
    )
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.09, fontsize=10)
    fig.supylabel("Índice do salário real de admissão (média pré=100)", x=0.018, fontsize=10)
    fig.text(
        0.075,
        0.025,
        "Nota: índice obtido pela média do log salarial entre CBOs; médias CBO-faixa-mês winsorizadas em P1/P99. "
        "Linhas escuras: tratamento (4 CBOs); linhas claras tracejadas: controle estrito (até 266 CBOs). "
        "As séries são descritivas; a inferência causal está no DDD da Tabela 5.3, cujo suporte é thin.",
        ha="left",
        va="bottom",
        fontsize=7.8,
        color=TEXT_MUTED,
    )
    save_figure(fig, output_path)


def validate_paths(paths: pd.DataFrame) -> None:
    observed_ages = set(paths["age_group"].dropna())
    missing_ages = set(AGE_ORDER) - observed_ages
    if missing_ages:
        raise RuntimeError(f"Normalized paths are missing age groups: {sorted(missing_ages)}")
    cells = set(zip(paths["age_group"], paths["scenario_role"]))
    expected = {(age, role) for age in AGE_ORDER for role in ["treated", "control"]}
    missing_cells = expected - cells
    if missing_cells:
        raise RuntimeError(f"Normalized paths are missing age-role cells: {sorted(missing_cells)}")
    treated_counts = paths[paths["scenario_role"].eq("treated")].groupby("age_group", observed=True)["n_cbo"].max()
    if treated_counts.empty or int(treated_counts.min()) < 2:
        raise RuntimeError("At least one age band has fewer than two treated CBOs with observed wages.")


def run(figure_path: Path = DEFAULT_FIGURE_PATH, csv_path: Path = DEFAULT_CSV_PATH) -> None:
    raw_paths = sorted(DATA_RAW.glob("caged_*.parquet"))
    required_paths = [CLASSIFICATION_PATH, IPCA_PATH]
    missing = [str(path) for path in required_paths if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    classification = pd.read_csv(CLASSIFICATION_PATH, dtype={"cbo_4d": str})
    roles = build_strict_software_it_roles(classification)
    log(
        f"Strict sample: {(roles['scenario_role'] == 'treated').sum()} treated CBOs and "
        f"{(roles['scenario_role'] == 'control').sum()} Not Exposed CBOs."
    )
    ipca = pd.read_parquet(IPCA_PATH)
    panel = reconstruct_age_wage_panel(raw_paths, roles, ipca)
    log(f"Reconstructed {len(panel):,} CBO-age-month rows.".replace(",", "."))
    paths = build_normalized_paths(panel)
    validate_paths(paths)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    paths.to_csv(csv_path, index=False)
    plot_normalized_paths(paths, figure_path, load_young_ddd_annotation())
    log(f"Wrote backing paths to {csv_path}")
    log(f"Wrote figure to {figure_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE_PATH, help="Output PNG path.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Output backing CSV path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.figure, args.csv)
