#!/usr/bin/env python3
"""Build combined dynamic figures for the PNAD/IBGE age bands in Table 5.2.4B."""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from section4_5_final.section5_2_dynamic_figures import (  # noqa: E402
    EVENT_MAX,
    EVENT_MIN,
    EVENT_TIMES,
    REFERENCE_PERIOD,
    _wage_bounds,
    add_winsorized_wage_path,
    complete_group_panel,
    load_main_strict_panel,
    normalize_paths,
    safely_estimate_dynamic,
)
from section4_5_final.section5_2_tables import (  # noqa: E402
    OUTCOME_ORDER,
    SECTION5_2_ADDITIONAL_SPECS,
)
from section4_5_final.style import (  # noqa: E402
    GRID,
    TEXT_DARK,
    TEXT_MUTED,
    get_pyplot,
    setup_plot_style,
)


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = ROOT / "outputs" / "section4_5_final" / "section5_2_age_pnad_combined"
MICRO_CACHE_PATH = ROOT / "data" / "processed" / "section5_2_dynamic_age_pnad_pairs.parquet"
MICRO_CACHE_VERSION = "section5_2_dynamic_age_pnad_pairs_v1"

DIMENSION = "age_pnad"
OUTCOMES = list(OUTCOME_ORDER)
OVERVIEW_OUTCOMES = ["ln_admissoes", "ln_salario_real_adm"]
AGE_PNAD_DISPLAY_LABELS = {
    "age_18_24": "18–24 anos",
    "age_25_34": "25–34 anos",
    "age_35_44": "35–44 anos",
    "age_45_54": "45–54 anos",
    "age_55_plus": "55–65 anos",
}
AGE_PNAD_GROUPS = [
    (group_id, AGE_PNAD_DISPLAY_LABELS[group_id])
    for group_id, _table_label in SECTION5_2_ADDITIONAL_SPECS[DIMENSION]["groups"]
]

GROUP_COLORS = {
    "age_18_24": "#0072B2",
    "age_25_34": "#E69F00",
    "age_35_44": "#009E73",
    "age_45_54": "#CC79A7",
    "age_55_plus": "#D55E00",
}
OUTCOME_TITLES = {
    "ln_admissoes": "Admissões",
    "ln_desligamentos": "Desligamentos",
    "ln_salario_real_adm": "Salário real de admissão",
}
GROUP_FILE_STEMS = {
    "age_18_24": "18_24",
    "age_25_34": "25_34",
    "age_35_44": "35_44",
    "age_45_54": "45_54",
    "age_55_plus": "55_65",
}
OVERVIEW_FILENAME = (
    "figure_s5_2_age_pnad_all_age_groups_main_outcomes_event_study_paths.png"
)
OUTCOME_OVERVIEW_FILENAMES = {
    "ln_admissoes": (
        "figure_s5_2_age_pnad_all_age_groups_admissions_event_study_paths.png"
    ),
    "ln_salario_real_adm": (
        "figure_s5_2_age_pnad_all_age_groups_real_admission_wage_event_study_paths.png"
    ),
}
COMBINED_NOTE = (
    "Nota: event studies DDD com IC pontual de 95% e referência t=-1; erros-padrão clusterizados por CBO.\n"
    "Trajetórias Exposed vs Not Exposed normalizadas pela média pré (=100); escalas verticais ajustadas por outcome.\n"
    "Salários das trajetórias winsorizados em P1/P99; universo de 18–65 anos; pretrends reprovados ou em alerta são exploratórios."
)
OUTCOME_OVERVIEW_NOTES = {
    "ln_admissoes": (
        "Nota: event studies DDD com IC pontual de 95% e referência t=-1; erros-padrão clusterizados por CBO.\n"
        "Trajetórias Exposed vs Not Exposed normalizadas pela média pré (=100); escalas verticais compartilhadas entre idades.\n"
        "Universo de 18–65 anos; pretrends reprovados ou em alerta são exploratórios."
    ),
    "ln_salario_real_adm": COMBINED_NOTE,
}


def log(message: str) -> None:
    print(f"[section5_2_age_pnad] {message}", flush=True)


def expected_contract_counts() -> dict[str, int]:
    """Return exact row and figure counts for the PNAD age package."""
    models = len(AGE_PNAD_GROUPS) * len(OUTCOMES)
    return {
        "models": models,
        "coefficient_rows": models * len(EVENT_TIMES),
        "pretrend_rows": models,
        "path_rows": models * 2 * len(EVENT_TIMES),
        "figures": len(AGE_PNAD_GROUPS) + 1 + len(OUTCOME_OVERVIEW_FILENAMES),
    }


def _age_band_figure_filenames() -> list[str]:
    return [
        f"figure_s5_2_age_pnad_{GROUP_FILE_STEMS[group_id]}_main_outcomes_event_study_paths.png"
        for group_id, _ in AGE_PNAD_GROUPS
    ]


def expected_figure_filenames() -> list[str]:
    """Return the five age-band figures and all comparative overview filenames."""
    return [
        *_age_band_figure_filenames(),
        OVERVIEW_FILENAME,
        *OUTCOME_OVERVIEW_FILENAMES.values(),
    ]


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def _expected_model_keys() -> list[tuple[str, str]]:
    return [(group_id, outcome) for group_id, _ in AGE_PNAD_GROUPS for outcome in OUTCOMES]


def validate_long_frames(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> None:
    """Enforce complete DDD, pretrend, and normalized-path grids."""
    _require_columns(
        coefficients,
        {
            "dimension",
            "group_id",
            "group_label",
            "outcome",
            "estimand",
            "t",
            "coef",
            "ci_low",
            "ci_high",
            "coefficient_status",
        },
        "coefficients",
    )
    _require_columns(
        pretrends,
        {
            "dimension",
            "group_id",
            "group_label",
            "outcome",
            "estimand",
            "pretrend_status",
            "power_status",
        },
        "pretrends",
    )
    _require_columns(
        paths,
        {
            "dimension",
            "group_id",
            "group_label",
            "outcome",
            "scenario_role",
            "t",
            "path_status",
            "path_index",
        },
        "paths",
    )
    contract = expected_contract_counts()
    observed_counts = (len(coefficients), len(pretrends), len(paths))
    expected_counts = (
        contract["coefficient_rows"],
        contract["pretrend_rows"],
        contract["path_rows"],
    )
    if observed_counts != expected_counts:
        raise ValueError(f"Long-frame row counts differ from contract: {observed_counts} != {expected_counts}")
    for name, frame in [("coefficients", coefficients), ("pretrends", pretrends), ("paths", paths)]:
        if set(frame["dimension"]) != {DIMENSION}:
            raise ValueError(f"{name} contains an invalid dimension")
        if set(frame["outcome"]) != set(OUTCOMES):
            raise ValueError(f"{name} contains an invalid outcome")
        if set(frame["group_id"]) != {group_id for group_id, _ in AGE_PNAD_GROUPS}:
            raise ValueError(f"{name} contains an invalid age group")
    if set(coefficients["estimand"]) != {"ddd"} or set(pretrends["estimand"]) != {"ddd"}:
        raise ValueError("All inferential models must use the DDD estimand")
    if coefficients.duplicated(["group_id", "outcome", "t"]).any():
        raise ValueError("Coefficient grid contains duplicate cells")
    if pretrends.duplicated(["group_id", "outcome"]).any():
        raise ValueError("Pretrend grid contains duplicate cells")
    if paths.duplicated(["group_id", "outcome", "scenario_role", "t"]).any():
        raise ValueError("Path grid contains duplicate cells")
    if set(coefficients["t"]) != set(EVENT_TIMES) or set(paths["t"]) != set(EVENT_TIMES):
        raise ValueError("Dynamic grids do not cover the full event window")
    reference = coefficients[coefficients["t"].eq(REFERENCE_PERIOD)]
    if len(reference) != contract["models"] or not np.allclose(reference["coef"], 0.0):
        raise ValueError("Every model must have a zero reference coefficient at t=-1")
    if set(paths["scenario_role"]) != {"treated", "control"}:
        raise ValueError("Paths must contain treated and control roles")
    expected_keys = _expected_model_keys()
    observed_keys = list(
        pretrends[["group_id", "outcome"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    if observed_keys != expected_keys:
        raise ValueError("Model order does not match the Table 5.2.4B contract")


def load_or_build_age_pnad_pairs(base: pd.DataFrame) -> pd.DataFrame:
    """Load a source-aware PNAD-age cache or reconstruct it from CAGED microdata."""
    from section4_event_study.config import DATA_RAW, PANEL_PATH, SCENARIO_GRID
    from section4_event_study.heterogeneity import aggregate_micro_group_pairs

    source_paths = [*sorted(DATA_RAW.glob("caged_*.parquet")), PANEL_PATH, SCENARIO_GRID]
    newest_source = max((path.stat().st_mtime for path in source_paths if path.exists()), default=0.0)
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
    if MICRO_CACHE_PATH.exists() and MICRO_CACHE_PATH.stat().st_mtime >= newest_source:
        cached = pd.read_parquet(MICRO_CACHE_PATH)
        version_ok = (
            "cache_schema_version" in cached.columns
            and set(cached["cache_schema_version"].dropna().unique()) == {MICRO_CACHE_VERSION}
        )
        if required.issubset(cached.columns) and version_ok:
            log(f"Loaded cached PNAD age pairs from {MICRO_CACHE_PATH}")
            return cached

    log("Reconstructing PNAD/IBGE age pairs from CAGED microdata...")
    micro = aggregate_micro_group_pairs()
    micro = micro[micro["dimension"].eq(DIMENSION)].copy()
    support = base[["cbo_4d", "ano", "mes"]].drop_duplicates()
    micro = micro.merge(support, on=["cbo_4d", "ano", "mes"], how="inner", validate="many_to_one")
    if micro.empty or not required.issubset(micro.columns):
        raise RuntimeError("PNAD age reconstruction did not produce the required pair panel")
    micro["cache_schema_version"] = MICRO_CACHE_VERSION
    MICRO_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    micro.to_parquet(MICRO_CACHE_PATH, index=False)
    log(f"Cached {len(micro):,} PNAD age pair rows at {MICRO_CACHE_PATH}")
    return micro


def build_age_pnad_results(
    base: pd.DataFrame | None = None,
    micro: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Estimate the 15 dynamic DDDs and build their normalized paths."""
    base = load_main_strict_panel() if base is None else base.copy()
    micro = load_or_build_age_pnad_pairs(base) if micro is None else micro.copy()
    panels: dict[str, pd.DataFrame] = {}
    for group_id, _group_label in AGE_PNAD_GROUPS:
        panels[group_id] = complete_group_panel(micro, base, DIMENSION, group_id)

    target_wages = pd.concat(
        [
            panel.loc[panel["subgroup"].eq("target"), "salario_adm"]
            for panel in panels.values()
        ],
        ignore_index=True,
    )
    wage_bounds = _wage_bounds(pd.DataFrame({"salario_adm": target_wages}), "salario_adm")
    coefficients_parts: list[pd.DataFrame] = []
    pretrend_rows: list[dict[str, object]] = []
    path_parts: list[pd.DataFrame] = []
    for group_id, group_label in AGE_PNAD_GROUPS:
        panel = panels[group_id]
        path_panel = add_winsorized_wage_path(
            panel,
            wage_column="salario_adm",
            bounds=wage_bounds,
        )
        for outcome in OUTCOMES:
            log(f"Estimating {group_id}/{outcome} (DDD)...")
            coefficients, pretrend = safely_estimate_dynamic(
                panel,
                dimension=DIMENSION,
                group_id=group_id,
                group_label=group_label,
                outcome=outcome,
                estimand="ddd",
            )
            paths = normalize_paths(
                path_panel,
                dimension=DIMENSION,
                group_id=group_id,
                group_label=group_label,
                outcome=outcome,
            )
            for key in ["power_status", "treated_cbo", "control_cbo"]:
                paths[key] = pretrend[key]
            coefficients_parts.append(coefficients)
            pretrend_rows.append(pretrend)
            path_parts.append(paths)

    coefficients = pd.concat(coefficients_parts, ignore_index=True)
    pretrends = pd.DataFrame(pretrend_rows)
    paths = pd.concat(path_parts, ignore_index=True)
    order = {key: index for index, key in enumerate(_expected_model_keys())}
    for frame in [coefficients, pretrends, paths]:
        frame["_model_order"] = [
            order[(group_id, outcome)]
            for group_id, outcome in zip(frame["group_id"], frame["outcome"])
        ]
    coefficients = (
        coefficients.sort_values(["_model_order", "t"])
        .drop(columns="_model_order")
        .reset_index(drop=True)
    )
    pretrends = pretrends.sort_values("_model_order").drop(columns="_model_order").reset_index(drop=True)
    paths["_role_order"] = paths["scenario_role"].map({"treated": 0, "control": 1})
    paths = (
        paths.sort_values(["_model_order", "_role_order", "t"])
        .drop(columns=["_model_order", "_role_order"])
        .reset_index(drop=True)
    )
    validate_long_frames(coefficients, pretrends, paths)
    return coefficients, pretrends, paths


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


def _event_ylim(coefficients: pd.DataFrame, group_id: str, outcome: str) -> tuple[float, float]:
    selected = coefficients[
        coefficients["group_id"].eq(group_id) & coefficients["outcome"].eq(outcome)
    ]
    bounds = selected[["ci_low", "ci_high"]].apply(pd.to_numeric, errors="coerce").to_numpy().ravel()
    bounds = bounds[np.isfinite(bounds)]
    maximum = max(0.05, float(np.abs(bounds).max()) if bounds.size else 0.05)
    return -1.06 * maximum, 1.06 * maximum


def _path_ylim(paths: pd.DataFrame, group_id: str, outcome: str) -> tuple[float, float]:
    selected = paths[paths["group_id"].eq(group_id) & paths["outcome"].eq(outcome)]
    values = pd.to_numeric(selected["path_index"], errors="coerce").dropna()
    lower = min(float(values.min()), 100.0) if not values.empty else 95.0
    upper = max(float(values.max()), 100.0) if not values.empty else 105.0
    padding = max(1.5, 0.08 * max(upper - lower, 1.0))
    return lower - padding, upper + padding


def _event_ylim_for_outcome(
    coefficients: pd.DataFrame,
    outcome: str,
) -> tuple[float, float]:
    """Return a symmetric event-study scale shared by every age band."""
    selected = coefficients[coefficients["outcome"].eq(outcome)]
    bounds = selected[["ci_low", "ci_high"]].apply(pd.to_numeric, errors="coerce").to_numpy().ravel()
    bounds = bounds[np.isfinite(bounds)]
    maximum = max(0.05, float(np.abs(bounds).max()) if bounds.size else 0.05)
    return -1.06 * maximum, 1.06 * maximum


def _path_ylim_for_outcome(paths: pd.DataFrame, outcome: str) -> tuple[float, float]:
    """Return a descriptive-path scale shared by every age band."""
    selected = paths[paths["outcome"].eq(outcome)]
    values = pd.to_numeric(selected["path_index"], errors="coerce").dropna()
    lower = min(float(values.min()), 100.0) if not values.empty else 95.0
    upper = max(float(values.max()), 100.0) if not values.empty else 105.0
    padding = max(1.5, 0.08 * max(upper - lower, 1.0))
    return lower - padding, upper + padding


def _draw_event_axis(
    axis: object,
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    *,
    group_id: str,
    outcome: str,
    color: str,
    compact: bool = False,
) -> None:
    view = coefficients[
        coefficients["group_id"].eq(group_id)
        & coefficients["outcome"].eq(outcome)
        & coefficients["coefficient_status"].isin(["estimated", "reference"])
    ].sort_values("t")
    diagnostic = pretrends[
        pretrends["group_id"].eq(group_id) & pretrends["outcome"].eq(outcome)
    ]
    axis.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.72, zorder=0)
    axis.axhline(0, color="#333333", linewidth=0.8, zorder=1)
    axis.axvline(REFERENCE_PERIOD, color="#777777", linewidth=0.75, linestyle="--", zorder=1)
    axis.axvline(0, color="#999999", linewidth=0.75, linestyle=":", zorder=1)
    if view.empty:
        axis.text(0.5, 0.5, "não estimado", transform=axis.transAxes, ha="center", va="center", color=TEXT_MUTED)
    else:
        axis.plot(
            view["t"],
            view["coef"],
            color=color,
            linewidth=1.7,
            marker="o",
            markersize=2.3,
            zorder=3,
        )
        band = view.dropna(subset=["ci_low", "ci_high"])
        axis.fill_between(
            band["t"].to_numpy(dtype=float),
            band["ci_low"].to_numpy(dtype=float),
            band["ci_high"].to_numpy(dtype=float),
            color=color,
            alpha=0.15,
            zorder=2,
        )
    title_size = 9.0 if compact else 10.5
    detail_size = 5.8 if compact else 6.8
    diagnostic_size = 5.8 if compact else 6.7
    axis.set_title(
        OUTCOME_TITLES[outcome],
        loc="left",
        color=color,
        fontweight="bold",
        fontsize=title_size,
        pad=4,
    )
    axis.text(
        0.01,
        0.91,
        "Event study DDD",
        transform=axis.transAxes,
        fontsize=detail_size,
        color=TEXT_MUTED,
    )
    if not diagnostic.empty:
        row = diagnostic.iloc[0]
        status = _status_pt(str(row["pretrend_status"]))
        power = str(row.get("power_status", "não disponível"))
        axis.text(
            0.985,
            0.965,
            f"pretrend: {status} | poder: {power}",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=diagnostic_size,
            color=TEXT_MUTED,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.65, "pad": 0.8},
        )
    axis.set_xlim(EVENT_MIN, EVENT_MAX)
    axis.set_ylim(*_event_ylim(coefficients, group_id, outcome))
    axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
    axis.tick_params(axis="x", labelbottom=False)
    axis.grid(axis="x", visible=False)


def _draw_path_axis(
    axis: object,
    paths: pd.DataFrame,
    *,
    group_id: str,
    outcome: str,
    color: str,
    compact: bool = False,
) -> None:
    view = paths[paths["group_id"].eq(group_id) & paths["outcome"].eq(outcome)]
    treated = view[
        view["scenario_role"].eq("treated") & view["path_status"].eq("estimated")
    ].sort_values("t")
    control = view[
        view["scenario_role"].eq("control") & view["path_status"].eq("estimated")
    ].sort_values("t")
    axis.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.72, zorder=0)
    axis.axhline(100, color=GRID, linewidth=0.85, zorder=1)
    axis.axvline(0, color="#777777", linewidth=0.8, linestyle=":", zorder=1)
    if not control.empty:
        axis.plot(
            control["t"],
            control["path_index"],
            color=_lighten_color(color),
            linewidth=1.45,
            linestyle=(0, (4, 2.5)),
            zorder=2,
        )
    if not treated.empty:
        axis.plot(treated["t"], treated["path_index"], color=color, linewidth=1.85, zorder=3)
    if treated.empty and control.empty:
        axis.text(0.5, 0.5, "trajetória indisponível", transform=axis.transAxes, ha="center", va="center", color=TEXT_MUTED)
    axis.text(
        0.01,
        0.91,
        "Trajetórias da faixa etária",
        transform=axis.transAxes,
        fontsize=5.5 if compact else 6.8,
        color=TEXT_MUTED,
    )
    axis.set_xlim(EVENT_MIN, EVENT_MAX)
    axis.set_ylim(*_path_ylim(paths, group_id, outcome))
    axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
    axis.grid(axis="x", visible=False)


def _path_legend_handles() -> list[object]:
    from matplotlib.lines import Line2D

    return [
        Line2D([0], [0], color=TEXT_DARK, linewidth=2.0, label="Exposed"),
        Line2D([0], [0], color="#A9A9A9", linewidth=1.6, linestyle=(0, (4, 2.5)), label="Not Exposed"),
    ]


def plot_age_band_figure(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    group_id: str,
    group_label: str,
    output_path: Path,
    dpi: int = 300,
) -> Path:
    """Render all three outcomes for one PNAD/IBGE age band."""
    plt = get_pyplot()
    setup_plot_style()
    color = GROUP_COLORS[group_id]
    fig = plt.figure(figsize=(14.8, 7.1))
    outer = fig.add_gridspec(
        1,
        len(OUTCOMES),
        left=0.07,
        right=0.985,
        top=0.77,
        bottom=0.20,
        wspace=0.20,
    )
    for column, outcome in enumerate(OUTCOMES):
        inner = outer[0, column].subgridspec(2, 1, height_ratios=[1.05, 0.95], hspace=0.08)
        event_axis = fig.add_subplot(inner[0])
        path_axis = fig.add_subplot(inner[1], sharex=event_axis)
        _draw_event_axis(
            event_axis,
            coefficients,
            pretrends,
            group_id=group_id,
            outcome=outcome,
            color=color,
        )
        _draw_path_axis(path_axis, paths, group_id=group_id, outcome=outcome, color=color)
        if column == 0:
            event_axis.set_ylabel("Coeficiente DDD (log)", fontsize=8)
            path_axis.set_ylabel("Índice (pré=100)", fontsize=8)

    fig.suptitle(
        f"{group_label} — event studies e trajetórias por outcome",
        x=0.07,
        y=0.97,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.07,
        0.90,
        "O DDD compara a faixa etária com seu complemento; as trajetórias mostram Exposed e Not Exposed dentro da faixa.",
        ha="left",
        fontsize=8.9,
        color=TEXT_MUTED,
    )
    fig.legend(handles=_path_legend_handles(), loc="upper right", bbox_to_anchor=(0.985, 0.895), frameon=False, ncol=2)
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.105, fontsize=9.5)
    fig.text(
        0.07,
        0.022,
        COMBINED_NOTE,
        ha="left",
        va="bottom",
        fontsize=7.2,
        color=TEXT_MUTED,
        linespacing=1.25,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def plot_age_overview_figure(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    output_path: Path,
    dpi: int = 300,
) -> Path:
    """Render all age bands and the two headline outcomes in one comparison matrix."""
    plt = get_pyplot()
    setup_plot_style()
    fig = plt.figure(figsize=(20.5, 9.3))
    outer = fig.add_gridspec(
        len(OVERVIEW_OUTCOMES),
        len(AGE_PNAD_GROUPS),
        left=0.087,
        right=0.992,
        top=0.805,
        bottom=0.190,
        hspace=0.31,
        wspace=0.13,
    )
    event_limits = {
        outcome: _event_ylim_for_outcome(coefficients, outcome)
        for outcome in OVERVIEW_OUTCOMES
    }
    path_limits = {
        outcome: _path_ylim_for_outcome(paths, outcome)
        for outcome in OVERVIEW_OUTCOMES
    }
    top_event_axes: list[object] = []
    first_column_pairs: list[tuple[object, object]] = []

    for row, outcome in enumerate(OVERVIEW_OUTCOMES):
        for column, (group_id, _group_label) in enumerate(AGE_PNAD_GROUPS):
            inner = outer[row, column].subgridspec(
                2,
                1,
                height_ratios=[1.05, 0.95],
                hspace=0.07,
            )
            event_axis = fig.add_subplot(inner[0])
            path_axis = fig.add_subplot(inner[1], sharex=event_axis)
            color = GROUP_COLORS[group_id]
            _draw_event_axis(
                event_axis,
                coefficients,
                pretrends,
                group_id=group_id,
                outcome=outcome,
                color=color,
                compact=True,
            )
            _draw_path_axis(
                path_axis,
                paths,
                group_id=group_id,
                outcome=outcome,
                color=color,
                compact=True,
            )
            event_axis.set_ylim(*event_limits[outcome])
            path_axis.set_ylim(*path_limits[outcome])
            event_axis.tick_params(axis="both", labelsize=6.2)
            path_axis.tick_params(axis="both", labelsize=6.2)
            if row < len(OVERVIEW_OUTCOMES) - 1:
                path_axis.tick_params(axis="x", labelbottom=False)
            if column > 0:
                event_axis.tick_params(axis="y", labelleft=False)
                path_axis.tick_params(axis="y", labelleft=False)
            else:
                event_axis.set_ylabel("Coef. DDD (log)", fontsize=6.7)
                path_axis.set_ylabel("Índice (pré=100)", fontsize=6.7)
                first_column_pairs.append((event_axis, path_axis))
            if row == 0:
                top_event_axes.append(event_axis)

    for event_axis, (group_id, group_label) in zip(top_event_axes, AGE_PNAD_GROUPS):
        bounds = event_axis.get_position()
        fig.text(
            (bounds.x0 + bounds.x1) / 2,
            0.826,
            group_label,
            ha="center",
            va="bottom",
            fontsize=10.2,
            fontweight="bold",
            color=GROUP_COLORS[group_id],
        )
    for (event_axis, path_axis), outcome in zip(first_column_pairs, OVERVIEW_OUTCOMES):
        event_bounds = event_axis.get_position()
        path_bounds = path_axis.get_position()
        fig.text(
            0.018,
            (event_bounds.y1 + path_bounds.y0) / 2,
            OUTCOME_TITLES[outcome],
            ha="center",
            va="center",
            rotation=90,
            fontsize=10.0,
            fontweight="bold",
            color=TEXT_DARK,
        )

    fig.suptitle(
        "Heterogeneidade por idade — admissões e salário de admissão",
        x=0.087,
        y=0.972,
        ha="left",
        fontsize=16.5,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.087,
        0.925,
        "Colunas: faixas etárias; linhas: admissões e salário real de admissão. O DDD compara cada faixa com o complemento das demais idades.",
        ha="left",
        fontsize=9.2,
        color=TEXT_MUTED,
    )
    fig.legend(
        handles=_path_legend_handles(),
        loc="upper right",
        bbox_to_anchor=(0.992, 0.905),
        frameon=False,
        ncol=2,
    )
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.118, fontsize=9.5)
    fig.text(
        0.087,
        0.018,
        COMBINED_NOTE,
        ha="left",
        va="bottom",
        fontsize=7.3,
        color=TEXT_MUTED,
        linespacing=1.25,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def plot_age_outcome_overview_figure(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    outcome: str,
    output_path: Path,
    dpi: int = 300,
) -> Path:
    """Render one headline outcome across all five age bands."""
    if outcome not in OVERVIEW_OUTCOMES:
        raise ValueError(
            f"Outcome-specific age overview does not support outcome: {outcome}"
        )

    plt = get_pyplot()
    setup_plot_style()
    fig = plt.figure(figsize=(20.5, 6.2))
    outer = fig.add_gridspec(
        1,
        len(AGE_PNAD_GROUPS),
        left=0.072,
        right=0.992,
        top=0.750,
        bottom=0.255,
        wspace=0.13,
    )
    event_limits = _event_ylim_for_outcome(coefficients, outcome)
    path_limits = _path_ylim_for_outcome(paths, outcome)
    event_axes: list[object] = []

    for column, (group_id, _group_label) in enumerate(AGE_PNAD_GROUPS):
        inner = outer[0, column].subgridspec(
            2,
            1,
            height_ratios=[1.05, 0.95],
            hspace=0.07,
        )
        event_axis = fig.add_subplot(inner[0])
        path_axis = fig.add_subplot(inner[1], sharex=event_axis)
        color = GROUP_COLORS[group_id]
        _draw_event_axis(
            event_axis,
            coefficients,
            pretrends,
            group_id=group_id,
            outcome=outcome,
            color=color,
            compact=True,
        )
        _draw_path_axis(
            path_axis,
            paths,
            group_id=group_id,
            outcome=outcome,
            color=color,
            compact=True,
        )
        event_axis.set_ylim(*event_limits)
        path_axis.set_ylim(*path_limits)
        event_axis.tick_params(axis="both", labelsize=6.4)
        path_axis.tick_params(axis="both", labelsize=6.4)
        if column > 0:
            event_axis.tick_params(axis="y", labelleft=False)
            path_axis.tick_params(axis="y", labelleft=False)
        else:
            event_axis.set_ylabel("Coef. DDD (log)", fontsize=7.0)
            path_axis.set_ylabel("Índice (pré=100)", fontsize=7.0)
        event_axes.append(event_axis)

    for event_axis, (group_id, group_label) in zip(event_axes, AGE_PNAD_GROUPS):
        bounds = event_axis.get_position()
        fig.text(
            (bounds.x0 + bounds.x1) / 2,
            0.775,
            group_label,
            ha="center",
            va="bottom",
            fontsize=10.5,
            fontweight="bold",
            color=GROUP_COLORS[group_id],
        )

    outcome_title = OUTCOME_TITLES[outcome].lower()
    fig.suptitle(
        f"Heterogeneidade por idade — {outcome_title}",
        x=0.072,
        y=0.970,
        ha="left",
        fontsize=16.5,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.072,
        0.905,
        "Cada coluna apresenta o event study DDD e as trajetórias Exposed versus Not Exposed da respectiva faixa etária.",
        ha="left",
        fontsize=9.2,
        color=TEXT_MUTED,
    )
    fig.legend(
        handles=_path_legend_handles(),
        loc="upper right",
        bbox_to_anchor=(0.992, 0.885),
        frameon=False,
        ncol=2,
    )
    fig.supxlabel(
        "Meses relativos ao lançamento do ChatGPT (t=0)",
        y=0.150,
        fontsize=9.5,
    )
    fig.text(
        0.072,
        0.018,
        OUTCOME_OVERVIEW_NOTES[outcome],
        ha="left",
        va="bottom",
        fontsize=7.3,
        color=TEXT_MUTED,
        linespacing=1.25,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def render_all_figures(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    figure_dir: Path,
    *,
    dpi: int = 300,
) -> list[Path]:
    """Render five age-band figures and three comparative overviews."""
    figure_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for (group_id, group_label), filename in zip(AGE_PNAD_GROUPS, _age_band_figure_filenames()):
        rendered.append(
            plot_age_band_figure(
                coefficients,
                pretrends,
                paths,
                group_id=group_id,
                group_label=group_label,
                output_path=figure_dir / filename,
                dpi=dpi,
            )
        )
    rendered.append(
        plot_age_overview_figure(
            coefficients,
            pretrends,
            paths,
            output_path=figure_dir / OVERVIEW_FILENAME,
            dpi=dpi,
        )
    )
    for outcome, filename in OUTCOME_OVERVIEW_FILENAMES.items():
        rendered.append(
            plot_age_outcome_overview_figure(
                coefficients,
                pretrends,
                paths,
                outcome=outcome,
                output_path=figure_dir / filename,
                dpi=dpi,
            )
        )
    return rendered


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_readme(output_root: Path, pretrends: pd.DataFrame) -> Path:
    contract = expected_contract_counts()
    status_counts = pretrends["pretrend_status"].value_counts(dropna=False).to_dict()
    lines = [
        "# Section 5.2 PNAD/IBGE Age Dynamic Figures",
        "",
        "This package applies the selected combined visual design to the age bands reported in Table 5.2.4B.",
        "It includes five age-band figures, one combined landscape overview, and two outcome-specific overviews. The five age-band figures retain admissions, separations, and real admission wages. The three overviews intentionally focus on admissions and real admission wages, with each cell placing a dynamic DDD event study above descriptive Exposed-versus-Not-Exposed paths.",
        "",
        "## Contract",
        "",
        f"- {contract['figures']} PNG figures at 300 dpi: five age-band figures, one combined overview, and two outcome-specific overviews.",
        f"- {contract['models']} DDD models, {contract['coefficient_rows']:,} coefficient rows, {contract['pretrend_rows']} pretrend rows, and {contract['path_rows']:,} path rows.",
        "- Age bands: 18–24, 25–34, 35–44, 45–54, and 55–65 years.",
        "- Strict event window `t=-12,...,24`; inferential reference at `t=-1`.",
        "- Main treatment: OIT gradients G1–G4 (`Exposed`) versus `Not Exposed`; `Minimal Exposure` is excluded.",
        "- Missing CBO-age-month flow cells are completed with zero; missing wage cells remain missing.",
        "- Paths normalize each CBO to its pre-period mean (=100) and are descriptive, not causal estimates.",
        "- Real admission wages are winsorized at P1/P99 only in the descriptive paths.",
        "- All three overviews omit separations and share the vertical scale across age bands within each displayed outcome.",
        "",
        "## Diagnostics",
        "",
        f"- Dynamic pretrend status counts: `{status_counts}`.",
        "- Confidence intervals are pointwise and are not adjusted for multiple testing.",
        "- A failed dynamic pretrend can differ from the linear pretrend diagnostic shown in Table 5.2.4B.",
        "- Table 5.2.4B uses observed group cells, while this dynamic package completes the flow grid; a simple average of monthly DDD coefficients is therefore not expected to reproduce the static DDD exactly.",
        "",
        "## Files",
        "",
        f"- `figures/{OVERVIEW_FILENAME}`: combined comparison of admissions and real admission wages.",
        f"- `figures/{OUTCOME_OVERVIEW_FILENAMES['ln_admissoes']}`: admissions-only comparison.",
        f"- `figures/{OUTCOME_OVERVIEW_FILENAMES['ln_salario_real_adm']}`: real-admission-wage-only comparison.",
        "- `figures/`: three comparative overviews plus five age-band PNG figures.",
        "- `tables/event_study_coefficients_long.csv`: dynamic DDD coefficients and pointwise confidence intervals.",
        "- `tables/event_study_pretrends.csv`: joint pretrend and support diagnostics.",
        "- `tables/normalized_paths_long.csv`: descriptive normalized paths.",
        "- `audit/section5_2_age_pnad_figures_blindspot.md`: visual and econometric audit.",
    ]
    path = output_root / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_blindspot_report(
    output_root: Path,
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> Path:
    overview_coefficients = coefficients[coefficients["outcome"].isin(OVERVIEW_OUTCOMES)]
    overview_pretrends = pretrends[pretrends["outcome"].isin(OVERVIEW_OUTCOMES)]
    overview_paths = paths[paths["outcome"].isin(OVERVIEW_OUTCOMES)]
    pretrend_counts = overview_pretrends["pretrend_status"].value_counts(dropna=False).to_dict()
    power_counts = overview_pretrends["power_status"].value_counts(dropna=False).to_dict()
    flagged = overview_pretrends[
        overview_pretrends["pretrend_status"].isin(["fail", "warning"])
    ]
    flag_items = [
        f"{row.group_label} / {OUTCOME_TITLES[row.outcome]}: {row.pretrend_status}"
        for row in flagged.itertuples(index=False)
    ]
    path_view = overview_paths.dropna(subset=["path_index"]).copy()
    path_view["distance_from_100"] = (path_view["path_index"] - 100.0).abs()
    extremes = [
        f"{row.group_label} / {OUTCOME_TITLES[row.outcome]} / {row.scenario_role} at t={int(row.t)}: {row.path_index:.1f}"
        for row in path_view.nlargest(5, "distance_from_100").itertuples(index=False)
    ]
    largest_paths = path_view.nlargest(20, "distance_from_100")
    seasonal_extremes = largest_paths[
        largest_paths["outcome"].eq("ln_admissoes")
        & largest_paths["t"].isin([-12, 0, 12, 24])
    ]
    estimated = int(
        overview_coefficients[
            overview_coefficients["coefficient_status"].eq("estimated")
            & overview_coefficients["t"].ne(REFERENCE_PERIOD)
        ].shape[0]
    )
    ruling = "CONDITIONAL" if flag_items or set(power_counts) & {"thin", "limited"} else "CLEAR"
    lines = [
        "# Blindspot Report",
        "",
        "**Outputs:**",
        "",
        f"- `figures/{OVERVIEW_FILENAME}`",
        f"- `figures/{OUTCOME_OVERVIEW_FILENAMES['ln_admissoes']}`",
        f"- `figures/{OUTCOME_OVERVIEW_FILENAMES['ln_salario_real_adm']}`",
        "",
        f"**Date:** {date.today().isoformat()}",
        "",
        "**Stated finding under examination:** The combined and outcome-specific overviews make dynamic age patterns in admissions and real admission wages readable across age bands.",
        "",
        "## Vice 1: The Unexplained Feature",
        "",
        f"- **[DONE] Diagnostic inventory completed.** Pretrend counts: `{pretrend_counts}`; power counts: `{power_counts}`.",
        f"- **[DONE] The largest path departures from 100 were inventoried:** {'; '.join(extremes)}.",
    ]
    if len(seasonal_extremes) >= 3:
        lines.append(
            "- **[FLAG] Admission-path extremes cluster in December event months.** The repeated troughs at `t=0`, `t=12`, and `t=24` are consistent with seasonality in the descriptive paths; month fixed effects address common seasonality in the DDD, but the paths must not be read as isolated ChatGPT discontinuities."
        )
    if flag_items:
        lines.extend(f"- **[FLAG]** {item}." for item in flag_items)
    else:
        lines.append("- **[DONE] No failed or warning dynamic pretrends were found.**")
    lines.extend(
        [
            "- **[FLAG] The five age contrasts are coupled by construction.** Each named age band is compared with the complement of the other four bands, so columns are not independent discoveries.",
            "- **[FLAG] Static and dynamic pretrend diagnostics answer different questions.** The linear diagnostic in Table 5.2.4B must not override the joint event-study test.",
            "- **[FLAG] The static and dynamic samples are not numerically identical.** This package completes missing CBO-age-month flow cells with zero, whereas Table 5.2.4B uses observed group cells; monthly DDD averages must not be presented as replications of the static coefficient.",
            "",
            "## Vice 2: The Convenient Absence",
            "",
            f"- **[FLAG] Confidence intervals are pointwise and unadjusted.** The overview displays `{estimated}` non-reference coefficients across 10 models.",
            "- **[FLAG] The trajectories do not display each age-band complement.** They compare Exposed and Not Exposed inside the named band; only the event study represents the age-band-versus-complement DDD.",
            "- **[DONE] The overview uses a shared vertical scale across age bands within each outcome.** This makes column comparisons valid without truncating any observed confidence band or path.",
            "- **[FLAG] Scales remain outcome-specific.** Vertical distances must not be compared mechanically across the two outcome rows.",
            "- **[DONE] The overview contains 20 axes.** Removing the separation row leaves five age columns, two outcome rows, and an event-study/path pair in each cell.",
            "- **[DONE] Each outcome-specific overview contains 10 axes.** Splitting the two rows improves print readability without changing the underlying estimates.",
            "- **[DONE] Separations are omitted only from the three overviews.** They remain available in the five individual figures and in all three backing tables.",
            "- **[FLAG] The strict window does not replace alternative-window, tail-binning, or influential-month robustness checks.**",
            "",
            "## Virtue 1: The Unasked Question",
            "",
            "- **[DONE] Hiring and entry wages are visible together across all five age bands.** The tighter overview supports direct age comparisons while the individual figures preserve the separation evidence.",
            "- **[DONE] The 18–65 universe is explicit.** The final figure is labeled 55–65 rather than implying an unrestricted 55+ sample.",
            "- **[FLAG] Divergence between DDD coefficients and within-band paths should trigger a composition audit before causal interpretation.**",
            "",
            "## Virtue 2: The Unexploited Strength",
            "",
            "- **[DONE] Weak diagnostics remain visible inside the figures.** Panels are not removed when a pretrend fails.",
            "- **[DONE] The inferential and descriptive layers use the same age grouping and event window.**",
            "- **[FLAG] A leave-one-treated-CBO-out or influential-month envelope would strengthen any focal age claim.**",
            "",
            "## Ruling",
            "",
            f"- [{'x' if ruling == 'CLEAR' else ' '}] **CLEAR** — proceed without unresolved diagnostic flags.",
            f"- [{'x' if ruling == 'CONDITIONAL' else ' '}] **CONDITIONAL** — use the figures with explicit pretrend, scale, complement, and multiplicity qualifications.",
            "- [ ] **HOLD** — do not use or publish the figures.",
            "",
            "The figures are suitable for comparative diagnosis; they do not turn failed dynamic pretrends into causal evidence.",
        ]
    )
    path = output_root / "audit" / "section5_2_age_pnad_figures_blindspot.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_manifest(output_root: Path) -> Path:
    files = sorted(
        path
        for path in output_root.rglob("*")
        if path.is_file() and path.name != "MANIFEST.md"
    )
    lines = [
        "# Manifest",
        "",
        "SHA-256 hashes for the standalone PNAD/IBGE age figure package.",
        "",
        "| File | SHA-256 |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| `{path.relative_to(output_root).as_posix()}` | `{_sha256(path)}` |"
        for path in files
    )
    manifest = output_root / "MANIFEST.md"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def write_bundle(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    output_root: Path = OUTPUT_ROOT,
    dpi: int = 300,
) -> list[Path]:
    """Write tables, figures, documentation, and audit for a validated result set."""
    validate_long_frames(coefficients, pretrends, paths)
    table_dir = output_root / "tables"
    figure_dir = output_root / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(table_dir / "event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(table_dir / "event_study_pretrends.csv", index=False)
    paths.to_csv(table_dir / "normalized_paths_long.csv", index=False)
    rendered = render_all_figures(coefficients, pretrends, paths, figure_dir, dpi=dpi)
    observed = {path.name for path in figure_dir.glob("*.png")}
    expected = set(expected_figure_filenames())
    if observed != expected:
        raise RuntimeError(f"Figure files differ from contract: observed={sorted(observed)}, expected={sorted(expected)}")
    if any(path.stat().st_size == 0 for path in rendered):
        raise RuntimeError("At least one rendered PNG is empty")
    _write_readme(output_root, pretrends)
    _write_blindspot_report(output_root, coefficients, pretrends, paths)
    _write_manifest(output_root)
    return rendered


def run(output_root: Path = OUTPUT_ROOT, *, dpi: int = 300) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Estimate PNAD-age dynamics and write the standalone combined figure package."""
    coefficients, pretrends, paths = build_age_pnad_results()
    rendered = write_bundle(
        coefficients,
        pretrends,
        paths,
        output_root=output_root,
        dpi=dpi,
    )
    log(
        f"Wrote {len(rendered)} figures, {len(coefficients)} coefficients, "
        f"{len(pretrends)} pretrends, and {len(paths)} path rows to {output_root}"
    )
    return coefficients, pretrends, paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.output_root, dpi=args.dpi)
