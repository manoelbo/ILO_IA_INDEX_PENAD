#!/usr/bin/env python3
"""Build final combined Section 5.2 event-study and path figures.

The module reads the previously estimated dynamic long tables, keeps national
admissions, separations, and real admission wages, and combines inference with
descriptive paths. Demographic figures remain restricted to admissions and real
admission wages. It does not estimate models or modify the curated dissertation
package.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import textwrap
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from section4_5_final.section5_2_tables import (  # noqa: E402
    HETEROGENEITY_SPECS,
    SECTION5_2_ADDITIONAL_SPECS,
)
from section4_5_final.style import (  # noqa: E402
    GRID,
    OUTCOME_COLORS,
    TEXT_DARK,
    TEXT_MUTED,
    get_pyplot,
    setup_plot_style,
)


ROOT = Path(__file__).resolve().parents[3]
INPUT_ROOT = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "experimental"
    / "section5_2_dynamic"
    / "tables"
)
OUTPUT_ROOT = ROOT / "outputs" / "section4_5_final" / "section5_2_dynamic_combined"
NATIONAL_COMBINED_FILENAME = "figure_s5_2_national_main_outcomes_event_study_paths.png"
NATIONAL_COMBINED_TITLE = "Resultados nacionais — event studies e trajetórias"
NATIONAL_COMBINED_NOTE = (
    "Nota: event studies com IC pontual de 95% e referência t=-1; erros-padrão clusterizados por CBO.\n"
    "Trajetórias normalizadas pela média pré (=100) e usadas apenas como evidência descritiva; "
    "escalas verticais ajustadas separadamente por outcome.\n"
    "Salários das trajetórias winsorizados em P1/P99; painéis com pretrend reprovado são exploratórios."
)

EVENT_MIN = -12
EVENT_MAX = 24
REFERENCE_PERIOD = -1
EVENT_TIMES = list(range(EVENT_MIN, EVENT_MAX + 1))
DIMENSION_ORDER = ["national", "sex", "income", "age_canaries", "race_color", "education"]
FOCAL_OUTCOMES = ["ln_admissoes", "ln_salario_real_adm"]
NATIONAL_OUTCOMES = ["ln_admissoes", "ln_desligamentos", "ln_salario_real_adm"]

OUTCOME_TITLES = {
    "ln_admissoes": "Admissões",
    "ln_desligamentos": "Desligamentos",
    "ln_salario_real_adm": "Salário real de admissão",
}
OUTCOME_FILE_STEMS = {
    "ln_admissoes": "admissions",
    "ln_desligamentos": "separations",
    "ln_salario_real_adm": "real_admission_wage",
}
DIMENSION_TITLE_PHRASES = {
    "national": "nacionais",
    "sex": "por sexo",
    "income": "por renda pré-tratamento",
    "income_pnad": "por renda pré-tratamento — faixas PNAD/IBGE",
    "age_canaries": "por idade",
    "race_color": "por raça/cor",
    "race_color_b": "por raça/cor — Branca e Negra",
    "education": "por escolaridade",
}
DIMENSION_LABELS = {
    "national": "Nacional",
    "sex": "Sexo",
    "income": "Renda pré-tratamento",
    "income_pnad": "Renda pré-tratamento — faixas PNAD/IBGE",
    "age_canaries": "Idade — coortes Canaries",
    "race_color": "Raça/cor",
    "race_color_b": "Raça/cor — Branca e Negra",
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


def dimension_groups(dimension: str) -> list[tuple[str, str]]:
    """Return groups in their dissertation display order."""
    if dimension == "national":
        return [("national", "Nacional")]
    specs = {**HETEROGENEITY_SPECS, **SECTION5_2_ADDITIONAL_SPECS}
    if dimension not in specs:
        raise KeyError(f"Unknown Section 5.2 dimension: {dimension}")
    return list(specs[dimension]["groups"])


def outcomes_for_dimension(dimension: str) -> list[str]:
    """Return outcomes selected for a dimension in publication order."""
    if dimension == "national":
        return list(NATIONAL_OUTCOMES)
    if dimension not in DIMENSION_ORDER and dimension not in SECTION5_2_ADDITIONAL_SPECS:
        raise KeyError(f"Unknown Section 5.2 dimension: {dimension}")
    return list(FOCAL_OUTCOMES)


def figure_specifications() -> list[tuple[str, str]]:
    """Return the allowed dimension-outcome figure pairs in display order."""
    return [
        (dimension, outcome)
        for dimension in DIMENSION_ORDER
        for outcome in outcomes_for_dimension(dimension)
    ]


def expected_contract_counts() -> dict[str, int]:
    """Return exact counts for the selected national and demographic package."""
    models = sum(
        len(dimension_groups(dimension)) * len(outcomes_for_dimension(dimension))
        for dimension in DIMENSION_ORDER
    )
    return {
        "models": models,
        "coefficient_rows": models * len(EVENT_TIMES),
        "pretrend_rows": models,
        "path_rows": models * 2 * len(EVENT_TIMES),
        "figures": len(figure_specifications()) + 1,
    }


def figure_layout(group_count: int) -> tuple[int, int, tuple[float, float]]:
    """Return responsive card-grid dimensions and publication size."""
    layouts = {
        1: (1, 1, (8.2, 7.2)),
        2: (1, 2, (12.6, 7.2)),
        3: (1, 3, (14.8, 7.1)),
        4: (2, 2, (12.6, 10.6)),
        5: (2, 3, (14.8, 10.6)),
        6: (2, 3, (14.8, 10.6)),
    }
    if group_count not in layouts:
        raise ValueError(f"Unsupported combined figure group count: {group_count}")
    return layouts[group_count]


def _figure_grid_slots(group_count: int) -> tuple[int, int, list[tuple[int, int, int]]]:
    """Return row and column spans, centering the second row for five groups."""
    rows, columns, _figsize = figure_layout(group_count)
    if group_count == 5:
        return (
            2,
            6,
            [
                (0, 0, 2),
                (0, 2, 4),
                (0, 4, 6),
                (1, 1, 3),
                (1, 3, 5),
            ],
        )
    slots = [
        (index // columns, index % columns, index % columns + 1)
        for index in range(group_count)
    ]
    return rows, columns, slots


def figure_title(dimension: str, outcome: str) -> str:
    """Return the final visible Portuguese figure title."""
    if dimension not in DIMENSION_TITLE_PHRASES:
        raise KeyError(f"Unknown figure dimension: {dimension}")
    if outcome not in OUTCOME_TITLES:
        raise KeyError(f"Unknown figure outcome: {outcome}")
    return f"{OUTCOME_TITLES[outcome]} — event study e trajetórias {DIMENSION_TITLE_PHRASES[dimension]}"


def _figure_note(outcome: str, dimension: str) -> str:
    """Return the note layout used by each published figure vintage."""
    if outcome not in NATIONAL_OUTCOMES:
        raise KeyError(f"Unsupported grouped figure outcome: {outcome}")
    wage_note = (
        " Salários das trajetórias winsorizados em P1/P99."
        if outcome == "ln_salario_real_adm"
        else ""
    )
    if dimension not in {"sex", "income", "education"}:
        return (
            "Nota: event studies com IC pontual de 95% e referência t=-1; "
            "erros-padrão clusterizados por CBO.\n"
            "Trajetórias normalizadas pela média pré (=100) e usadas apenas "
            f"como evidência descritiva.{wage_note}\n"
            "Painéis com pretrend reprovado ou poder thin são exploratórios."
        )
    return (
        "Nota: event studies com IC pontual de 95% e referência t=-1; "
        "erros-padrão clusterizados por CBO. Trajetórias normalizadas pela "
        "média pré (=100) e usadas apenas como evidência descritiva. "
        "Painéis com pretrend reprovado ou poder thin são exploratórios."
        f"{wage_note}"
    )


def _figure_filename(dimension: str, outcome: str) -> str:
    return f"figure_s5_2_{dimension}_{OUTCOME_FILE_STEMS[outcome]}_event_study_paths.png"


def expected_figure_filenames() -> list[str]:
    """Return the deterministic final PNG names."""
    individual = [
        _figure_filename(dimension, outcome)
        for dimension, outcome in figure_specifications()
    ]
    return [NATIONAL_COMBINED_FILENAME, *individual]


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def _model_order() -> dict[tuple[str, str, str], int]:
    order = {}
    index = 0
    for dimension in DIMENSION_ORDER:
        for group_id, _ in dimension_groups(dimension):
            for outcome in outcomes_for_dimension(dimension):
                order[(dimension, group_id, outcome)] = index
                index += 1
    return order


def _sort_filtered_frame(frame: pd.DataFrame, *, paths: bool = False) -> pd.DataFrame:
    order = _model_order()
    out = frame.copy()
    out["_model_order"] = [
        order[(dimension, group_id, outcome)]
        for dimension, group_id, outcome in zip(out["dimension"], out["group_id"], out["outcome"])
    ]
    sort_columns = ["_model_order"]
    if paths:
        out["_role_order"] = out["scenario_role"].map({"treated": 0, "control": 1})
        sort_columns.append("_role_order")
    if "t" in out.columns:
        sort_columns.append("t")
    return out.sort_values(sort_columns).drop(columns=[column for column in ["_model_order", "_role_order"] if column in out]).reset_index(drop=True)


def filter_and_validate_inputs(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Select allowed outcomes and enforce the complete model contract."""
    _require_columns(
        coefficients,
        {"dimension", "group_id", "group_label", "outcome", "t", "coef", "ci_low", "ci_high", "coefficient_status"},
        "coefficients",
    )
    _require_columns(
        pretrends,
        {"dimension", "group_id", "group_label", "outcome", "pretrend_status", "power_status"},
        "pretrends",
    )
    _require_columns(
        paths,
        {"dimension", "group_id", "group_label", "outcome", "scenario_role", "t", "path_index", "path_status"},
        "paths",
    )
    allowed_pairs = set(figure_specifications())
    selected = tuple(
        frame[
            [
                (dimension, outcome) in allowed_pairs
                for dimension, outcome in zip(frame["dimension"], frame["outcome"])
            ]
        ].copy()
        for frame in [coefficients, pretrends, paths]
    )
    coefficients_out = _sort_filtered_frame(selected[0])
    pretrends_out = _sort_filtered_frame(selected[1])
    paths_out = _sort_filtered_frame(selected[2], paths=True)
    expected = expected_contract_counts()
    contracts = [
        (coefficients_out, expected["coefficient_rows"], ["dimension", "group_id", "outcome", "t"], "coefficients"),
        (pretrends_out, expected["pretrend_rows"], ["dimension", "group_id", "outcome"], "pretrends"),
        (paths_out, expected["path_rows"], ["dimension", "group_id", "outcome", "scenario_role", "t"], "paths"),
    ]
    expected_models = list(_model_order())
    for frame, row_count, keys, name in contracts:
        if len(frame) != row_count:
            raise ValueError(f"{name} has {len(frame)} rows; expected {row_count}")
        if frame.duplicated(keys).any():
            raise ValueError(f"{name} contains duplicate cells for {keys}")
        observed_models = list(
            frame[["dimension", "group_id", "outcome"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        )
        if observed_models != expected_models:
            raise ValueError(f"{name} model order differs from the dimension-outcome contract")
    if set(coefficients_out["t"]) != set(EVENT_TIMES) or set(paths_out["t"]) != set(EVENT_TIMES):
        raise ValueError("Inputs do not cover the strict t=-12,...,24 window")
    if set(paths_out["scenario_role"]) != {"treated", "control"}:
        raise ValueError("Paths must contain treated and control roles")
    reference = coefficients_out[coefficients_out["t"].eq(REFERENCE_PERIOD)]
    if len(reference) != expected["models"] or not np.allclose(reference["coef"], 0.0, equal_nan=False):
        raise ValueError("Every event-study reference coefficient at t=-1 must equal zero")
    return coefficients_out, pretrends_out, paths_out


def load_inputs(input_root: Path = INPUT_ROOT) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the previously estimated dynamic tables without modifying them."""
    filenames = [
        "event_study_coefficients_long.csv",
        "event_study_pretrends.csv",
        "normalized_paths_long.csv",
    ]
    frames = []
    for filename in filenames:
        path = input_root / filename
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Missing dynamic input: {path}")
        frames.append(pd.read_csv(path))
    return filter_and_validate_inputs(*frames)


def group_color(dimension: str, group_id: str, outcome: str) -> str:
    """Return the stable publication color for a dimension group."""
    if dimension == "national":
        return OUTCOME_COLORS[outcome]
    if dimension == "age_canaries":
        return AGE_COLORS[group_id]
    group_ids = [item[0] for item in dimension_groups(dimension)]
    return GROUP_PALETTE[group_ids.index(group_id)]


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


def _group_title(group_label: str, group_count: int) -> str:
    width = {1: 36, 2: 28, 3: 22, 4: 28, 5: 22, 6: 22}[group_count]
    return textwrap.fill(group_label, width=width, break_long_words=False, break_on_hyphens=False)


def _event_ylim(coefficients: pd.DataFrame, dimension: str, outcome: str) -> tuple[float, float]:
    selected = coefficients[
        coefficients["dimension"].eq(dimension) & coefficients["outcome"].eq(outcome)
    ]
    bounds = selected[["ci_low", "ci_high"]].apply(pd.to_numeric, errors="coerce").to_numpy().ravel()
    bounds = bounds[np.isfinite(bounds)]
    maximum = max(0.05, float(np.abs(bounds).max()) if bounds.size else 0.05)
    return -1.06 * maximum, 1.06 * maximum


def _path_ylim(paths: pd.DataFrame, dimension: str, outcome: str) -> tuple[float, float]:
    selected = paths[paths["dimension"].eq(dimension) & paths["outcome"].eq(outcome)]
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
    dimension: str,
    group_id: str,
    group_label: str,
    outcome: str,
    ylim: tuple[float, float],
    group_count: int,
) -> None:
    color = group_color(dimension, group_id, outcome)
    view = coefficients[
        coefficients["dimension"].eq(dimension)
        & coefficients["group_id"].eq(group_id)
        & coefficients["outcome"].eq(outcome)
        & coefficients["coefficient_status"].isin(["estimated", "reference"])
    ].sort_values("t")
    diagnostic = pretrends[
        pretrends["dimension"].eq(dimension)
        & pretrends["group_id"].eq(group_id)
        & pretrends["outcome"].eq(outcome)
    ]
    estimand = "DiD" if dimension == "national" else "DDD"

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
    axis.set_title(
        _group_title(group_label, group_count),
        loc="left",
        color=color,
        fontweight="bold",
        fontsize=10.5,
        pad=4,
    )
    axis.text(0.01, 0.91, f"Event study {estimand}", transform=axis.transAxes, fontsize=6.8, color=TEXT_MUTED)
    if not diagnostic.empty:
        status = _status_pt(str(diagnostic.iloc[0]["pretrend_status"]))
        power = str(diagnostic.iloc[0].get("power_status", "não disponível"))
        axis.text(
            0.985,
            0.965,
            f"pretrend: {status} | poder: {power}",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=6.7,
            color=TEXT_MUTED,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.65, "pad": 0.8},
        )
    axis.set_xlim(EVENT_MIN, EVENT_MAX)
    axis.set_ylim(*ylim)
    axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
    axis.tick_params(axis="x", labelbottom=False)
    axis.grid(axis="x", visible=False)


def _draw_path_axis(
    axis: object,
    paths: pd.DataFrame,
    *,
    dimension: str,
    group_id: str,
    outcome: str,
    ylim: tuple[float, float],
) -> None:
    color = group_color(dimension, group_id, outcome)
    control_color = _lighten_color(color)
    view = paths[
        paths["dimension"].eq(dimension)
        & paths["group_id"].eq(group_id)
        & paths["outcome"].eq(outcome)
    ]
    treated = view[view["scenario_role"].eq("treated") & view["path_status"].eq("estimated")].sort_values("t")
    control = view[view["scenario_role"].eq("control") & view["path_status"].eq("estimated")].sort_values("t")

    axis.axvspan(0, EVENT_MAX, color="#F2F2F2", alpha=0.72, zorder=0)
    axis.axhline(100, color=GRID, linewidth=0.85, zorder=1)
    axis.axvline(0, color="#777777", linewidth=0.8, linestyle=":", zorder=1)
    if not control.empty:
        axis.plot(
            control["t"],
            control["path_index"],
            color=control_color,
            linewidth=1.45,
            linestyle=(0, (4, 2.5)),
            zorder=2,
        )
    if not treated.empty:
        axis.plot(treated["t"], treated["path_index"], color=color, linewidth=1.85, zorder=3)
    if treated.empty and control.empty:
        axis.text(0.5, 0.5, "trajetória indisponível", transform=axis.transAxes, ha="center", va="center", color=TEXT_MUTED)
    path_label = "Trajetórias nacionais" if dimension == "national" else "Trajetórias do subgrupo"
    axis.text(0.01, 0.91, path_label, transform=axis.transAxes, fontsize=6.8, color=TEXT_MUTED)
    axis.set_xlim(EVENT_MIN, EVENT_MAX)
    axis.set_ylim(*ylim)
    axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
    axis.grid(axis="x", visible=False)


def _path_legend_handles() -> list[object]:
    from matplotlib.lines import Line2D

    return [
        Line2D([0], [0], color=TEXT_DARK, linewidth=2.0, label="Exposed"),
        Line2D([0], [0], color="#A9A9A9", linewidth=1.6, linestyle=(0, (4, 2.5)), label="Not Exposed"),
    ]


def _save_figure(fig: object, output_path: Path, dpi: int) -> Path:
    plt = get_pyplot()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def plot_combined_figure(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    dimension: str,
    outcome: str,
    output_path: Path,
    dpi: int = 300,
) -> Path:
    """Render event-study inference above descriptive paths in each group card."""
    groups = dimension_groups(dimension)
    rows, columns, figsize = figure_layout(len(groups))
    grid_rows, grid_columns, grid_slots = _figure_grid_slots(len(groups))
    plt = get_pyplot()
    setup_plot_style()
    fig = plt.figure(figsize=figsize)
    bottom = 0.15 if rows == 2 else 0.20
    top = 0.82 if rows == 2 else 0.77
    outer = fig.add_gridspec(
        grid_rows,
        grid_columns,
        left=0.09,
        right=0.985,
        top=top,
        bottom=bottom,
        hspace=0.34,
        wspace=0.19,
    )
    event_ylim = _event_ylim(coefficients, dimension, outcome)
    path_ylim = _path_ylim(paths, dimension, outcome)
    for index, (group_id, group_label) in enumerate(groups):
        row, column_start, column_stop = grid_slots[index]
        inner = outer[row, column_start:column_stop].subgridspec(
            2,
            1,
            height_ratios=[1.05, 0.95],
            hspace=0.08,
        )
        event_axis = fig.add_subplot(inner[0])
        path_axis = fig.add_subplot(inner[1], sharex=event_axis)
        _draw_event_axis(
            event_axis,
            coefficients,
            pretrends,
            dimension=dimension,
            group_id=group_id,
            group_label=group_label,
            outcome=outcome,
            ylim=event_ylim,
            group_count=len(groups),
        )
        _draw_path_axis(
            path_axis,
            paths,
            dimension=dimension,
            group_id=group_id,
            outcome=outcome,
            ylim=path_ylim,
        )
        first_card_in_row = index == 0 or grid_slots[index - 1][0] != row
        if first_card_in_row:
            estimand = "DiD" if dimension == "national" else "DDD"
            event_axis.set_ylabel(f"Coeficiente {estimand} (log)", fontsize=8)
            path_axis.set_ylabel("Índice (pré=100)", fontsize=8)

    fig.suptitle(
        figure_title(dimension, outcome),
        x=0.09,
        y=0.97,
        ha="left",
        fontsize=14.5 if len(groups) < 3 else 15,
        fontweight="bold",
        color=TEXT_DARK,
    )
    subtitle = (
        "Exposed vs Not Exposed: inferência DiD acima e trajetórias descritivas abaixo."
        if dimension == "national"
        else "O DDD compara o subgrupo com seu complemento; as trajetórias mostram Exposed e Not Exposed dentro do subgrupo."
    )
    fig.text(0.09, 0.90, subtitle, ha="left", fontsize=8.9, color=TEXT_MUTED)
    fig.legend(handles=_path_legend_handles(), loc="upper right", bbox_to_anchor=(0.985, 0.895), frameon=False, ncol=2)
    xlabel_y = 0.09 if rows == 2 else 0.105
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=xlabel_y, fontsize=9.5)
    fig.text(
        0.09,
        0.022,
        _figure_note(outcome, dimension),
        ha="left",
        va="bottom",
        fontsize=7.2,
        color=TEXT_MUTED,
        linespacing=1.25,
    )
    return _save_figure(fig, output_path, dpi)


def plot_national_outcomes_figure(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    output_path: Path,
    *,
    dpi: int = 300,
) -> Path:
    """Render the three national outcomes in one horizontal publication figure."""
    plt = get_pyplot()
    setup_plot_style()
    fig = plt.figure(figsize=(14.8, 7.1))
    outer = fig.add_gridspec(
        1,
        len(NATIONAL_OUTCOMES),
        left=0.07,
        right=0.985,
        top=0.77,
        bottom=0.20,
        wspace=0.20,
    )
    for column, outcome in enumerate(NATIONAL_OUTCOMES):
        inner = outer[0, column].subgridspec(2, 1, height_ratios=[1.05, 0.95], hspace=0.08)
        event_axis = fig.add_subplot(inner[0])
        path_axis = fig.add_subplot(inner[1], sharex=event_axis)
        _draw_event_axis(
            event_axis,
            coefficients,
            pretrends,
            dimension="national",
            group_id="national",
            group_label=OUTCOME_TITLES[outcome],
            outcome=outcome,
            ylim=_event_ylim(coefficients, "national", outcome),
            group_count=len(NATIONAL_OUTCOMES),
        )
        _draw_path_axis(
            path_axis,
            paths,
            dimension="national",
            group_id="national",
            outcome=outcome,
            ylim=_path_ylim(paths, "national", outcome),
        )
        if column == 0:
            event_axis.set_ylabel("Coeficiente DiD (log)", fontsize=8)
            path_axis.set_ylabel("Índice (pré=100)", fontsize=8)

    fig.suptitle(
        NATIONAL_COMBINED_TITLE,
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
        "Exposed vs Not Exposed: inferência DiD acima e trajetórias descritivas abaixo.",
        ha="left",
        fontsize=8.9,
        color=TEXT_MUTED,
    )
    fig.legend(
        handles=_path_legend_handles(),
        loc="upper right",
        bbox_to_anchor=(0.985, 0.895),
        frameon=False,
        ncol=2,
    )
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.105, fontsize=9.5)
    fig.text(
        0.07,
        0.022,
        NATIONAL_COMBINED_NOTE,
        ha="left",
        va="bottom",
        fontsize=7.2,
        color=TEXT_MUTED,
        linespacing=1.25,
    )
    return _save_figure(fig, output_path, dpi)


def render_all_figures(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    figure_dir: Path,
    *,
    dpi: int = 300,
) -> list[Path]:
    """Render every allowed dimension-by-outcome PNG."""
    figure_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for dimension, outcome in figure_specifications():
        rendered.append(
            plot_combined_figure(
                coefficients,
                pretrends,
                paths,
                dimension=dimension,
                outcome=outcome,
                output_path=figure_dir / _figure_filename(dimension, outcome),
                dpi=dpi,
            )
        )
    rendered.append(
        plot_national_outcomes_figure(
            coefficients,
            pretrends,
            paths,
            figure_dir / NATIONAL_COMBINED_FILENAME,
            dpi=dpi,
        )
    )
    return rendered


def validate_figure_files(figure_dir: Path) -> None:
    """Validate exact filenames and nonempty PNGs."""
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
    forbidden = [
        name
        for name in observed
        if any(word in name.lower() for word in ["layout", "experimental", "teste"])
    ]
    if forbidden:
        raise RuntimeError(f"Final filenames contain forbidden terms: {forbidden}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _diagnostic_items(pretrends: pd.DataFrame, column: str, values: set[str]) -> list[str]:
    selected = pretrends[pretrends[column].astype(str).isin(values)]
    return [
        f"{DIMENSION_LABELS[row.dimension]} / {row.group_label} / {OUTCOME_TITLES[row.outcome]}: {getattr(row, column)}"
        for row in selected.itertuples(index=False)
    ]


def _format_report_list(items: list[str], empty_message: str) -> list[str]:
    if not items:
        return [f"- **[DONE] {empty_message}**"]
    return [f"- **[FLAG]** {item}" for item in items]


def write_blindspot_report(
    output_root: Path,
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> Path:
    """Write a reproducible peripheral-vision audit of the selected figures."""
    pretrend_counts = pretrends["pretrend_status"].value_counts(dropna=False).to_dict()
    power_counts = pretrends["power_status"].value_counts(dropna=False).to_dict()
    pretrend_flags = _diagnostic_items(pretrends, "pretrend_status", {"fail", "warning"})
    power_flags = _diagnostic_items(pretrends, "power_status", {"thin", "limited"})
    path_view = paths.dropna(subset=["path_index"]).copy()
    path_view["distance_from_100"] = (path_view["path_index"] - 100.0).abs()
    extreme_rows = path_view.nlargest(5, "distance_from_100")
    extremes = [
        (
            f"{DIMENSION_LABELS[row.dimension]} / {row.group_label} / {OUTCOME_TITLES[row.outcome]} / "
            f"{row.scenario_role} at t={int(row.t)}: index={row.path_index:.1f}"
        )
        for row in extreme_rows.itertuples(index=False)
    ]
    sex = coefficients[coefficients["dimension"].eq("sex")]
    mirror_residual = np.nan
    if set(sex["group_id"]) == {"men", "women"}:
        pivot = sex.pivot_table(index=["outcome", "t"], columns="group_id", values="coef", aggfunc="first")
        mirror_residual = float((pivot["men"] + pivot["women"]).abs().max())
    estimated_nonreference = int(
        coefficients[coefficients["coefficient_status"].eq("estimated") & coefficients["t"].ne(REFERENCE_PERIOD)].shape[0]
    )
    ruling = "CONDITIONAL" if pretrend_flags or power_flags else "CLEAR"
    contract = expected_contract_counts()
    lines = [
        "# Blindspot Report",
        "",
        f"**Output:** {contract['figures']} combined Section 5.2 dynamic figures",
        "",
        f"**Date:** {date.today().isoformat()}",
        "",
        "**Stated finding under examination:** Pairing dynamic estimates with normalized paths improves interpretation across national outcomes and demographic groups.",
        "",
        "## Vice 1: The Unexplained Feature",
        "",
        f"- **[DONE] Diagnostic inventory completed.** Pretrend counts: `{pretrend_counts}`; power counts: `{power_counts}`.",
        f"- **[DONE] The five largest path departures from 100 were inventoried:** {'; '.join(extremes)}.",
        "- **[DONE] The national composite preserves the requested outcome order.** Admissions appear first, separations second, and real admission wages third.",
    ]
    if np.isfinite(mirror_residual):
        lines.append(
            f"- **[DONE] Binary sex DDD mirroring was checked.** The largest men-plus-women coefficient residual is `{mirror_residual:.3g}`; mirrored panels are a construction feature, not independent discoveries."
        )
    lines.extend(_format_report_list(pretrend_flags, "No failed or warning pretrends were found."))
    lines.extend(
        [
            "",
            "## Vice 2: The Convenient Absence",
            "",
            f"- **[FLAG] Confidence bands are pointwise and unadjusted.** The package displays `{estimated_nonreference}` non-reference dynamic coefficients.",
            "- **[FLAG] The descriptive paths do not display each subgroup complement.** They show Exposed versus Not Exposed inside the named subgroup; the DDD remains the formal subgroup-versus-complement contrast.",
            "- **[FLAG] The selected strict window does not replace tail-binning or alternative-window sensitivity checks.**",
            "- **[FLAG] The national composite uses outcome-specific vertical scales.** This preserves detail but means line height must not be compared mechanically across columns; readers should use the labeled axes.",
            "- **[DONE] Separations are national-only by design.** The demographic figures remain focused on admissions and real admission wages, so no omitted separation DDD is implied by this package.",
        ]
    )
    lines.extend(_format_report_list(power_flags, "No thin or limited support cells were found."))
    lines.extend(
        [
            "",
            "## Virtue 1: The Unasked Question",
            "",
            "- **[DONE] Entry flows, exit flows, and entry-price adjustment are visible together nationally.** The three national cards make it easier to distinguish hiring, separations, and wage-composition changes.",
            "- **[DONE] The recommended national composite can replace three separate dissertation figures.** It preserves the inferential/descriptive distinction while reducing figure count in the main text.",
            "- **[DONE] Timing differences are visible.** The figures reveal whether average post-treatment coefficients hide delayed, short-lived, or irregular dynamics.",
            "- **[FLAG] Panels with divergent event studies and paths should trigger a composition audit before interpretation.**",
            "",
            "## Virtue 2: The Unexploited Strength",
            "",
            "- **[DONE] The bundle is complete for its stated asymmetric scope.** National figures cover three outcomes; demographic figures cover the two focal outcomes, all with the same event window, reference period, role definitions, and visual grammar.",
            "- **[DONE] The inferential/descriptive distinction is explicit inside every card.** This reduces the risk of treating normalized paths as causal estimates.",
            "- **[DONE] Weak diagnostics stay visible.** Failed pretrends and fragile support are not silently removed.",
            "",
            "## Ruling",
            "",
            f"- [{'x' if ruling == 'CLEAR' else ' '}] **CLEAR** — proceed to interpretation without unresolved diagnostic flags.",
            f"- [{'x' if ruling == 'CONDITIONAL' else ' '}] **CONDITIONAL** — use the figures, but keep failed pretrends, fragile support, path extremes, and multiplicity explicit.",
            "- [ ] **HOLD** — do not use or publish the figures.",
            "",
            "The figures are suitable as a comparative diagnostic package. They do not convert failed identification diagnostics into causal evidence.",
        ]
    )
    audit_path = output_root / "audit" / "section5_2_combined_figures_blindspot.md"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return audit_path


def write_readme(
    output_root: Path,
    source_hashes: dict[str, str],
    pretrends: pd.DataFrame,
) -> Path:
    """Write the standalone bundle documentation in English."""
    contract = expected_contract_counts()
    lines = [
        "# Section 5.2 Combined Dynamic Figures",
        "",
        "This package pairs dynamic DiD/DDD inference with descriptive Exposed-versus-Not-Exposed paths.",
        "It reads previously estimated long tables and does not estimate models or modify the curated dissertation package.",
        "",
        "## Contract",
        "",
        f"- {contract['figures']} PNG figures at 300 dpi: three national outcomes and two demographic outcomes across five heterogeneity dimensions.",
        f"- {contract['models']} group-outcome models, {contract['coefficient_rows']:,} coefficient rows, {contract['pretrend_rows']} pretrend rows, and {contract['path_rows']:,} path rows.",
        "- Strict event window `t=-12,...,24`; inferential reference at `t=-1`.",
        "- National figures report dynamic DiD for admissions, separations, and real admission wages.",
        "- Demographic figures report target-versus-complement dynamic DDD for admissions and real admission wages; separations are intentionally national-only.",
        "- Paths are descriptive, normalize each CBO to its pre-period mean (=100), and compare Exposed with Not Exposed inside the named group.",
        "- Real admission wages are winsorized at P1/P99 only in descriptive paths.",
        "",
        "## Recommended national figure",
        "",
        f"- `figures/{NATIONAL_COMBINED_FILENAME}` combines admissions, separations, and real admission wages in that order.",
        "- Each outcome keeps its own vertical scale for legibility; the three individual national PNGs remain available as supporting files.",
        "",
        "## Figures",
        "",
        "| File | Visible title |",
        "| --- | --- |",
        f"| `figures/{NATIONAL_COMBINED_FILENAME}` | {NATIONAL_COMBINED_TITLE} |",
    ]
    for dimension, outcome in figure_specifications():
        lines.append(f"| `figures/{_figure_filename(dimension, outcome)}` | {figure_title(dimension, outcome)} |")
    lines.extend(
        [
            "",
            "## Diagnostics",
            "",
            f"- Pretrend status counts: `{pretrends['pretrend_status'].value_counts(dropna=False).to_dict()}`.",
            f"- Power status counts: `{pretrends['power_status'].value_counts(dropna=False).to_dict()}`.",
            "- Confidence intervals are pointwise and unadjusted for multiple testing.",
            "- See `audit/section5_2_combined_figures_blindspot.md` before interpretation.",
            "",
            "## Backing data",
            "",
            "- `tables/event_study_coefficients_long.csv`",
            "- `tables/event_study_pretrends.csv`",
            "- `tables/normalized_paths_long.csv`",
            "",
            "## Source integrity",
            "",
            "| Source file | SHA-256 |",
            "| --- | --- |",
        ]
    )
    for filename, digest in source_hashes.items():
        lines.append(f"| `{filename}` | `{digest}` |")
    readme = output_root / "README.md"
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme


def write_manifest(output_root: Path) -> Path:
    """Write deterministic byte counts and SHA-256 hashes for bundle files."""
    files = sorted(
        path
        for path in output_root.rglob("*")
        if path.is_file() and path.name != "MANIFEST.md"
    )
    lines = [
        "# Section 5.2 Combined Figures Manifest",
        "",
        "| File | Bytes | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    for path in files:
        lines.append(f"| `{path.relative_to(output_root)}` | {path.stat().st_size} | `{_sha256(path)}` |")
    manifest = output_root / "MANIFEST.md"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def run(
    input_root: Path = INPUT_ROOT,
    output_root: Path = OUTPUT_ROOT,
    *,
    dpi: int = 300,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build the self-contained final combined-figure bundle."""
    source_filenames = [
        "event_study_coefficients_long.csv",
        "event_study_pretrends.csv",
        "normalized_paths_long.csv",
    ]
    source_hashes = {filename: _sha256(input_root / filename) for filename in source_filenames}
    coefficients, pretrends, paths = load_inputs(input_root)
    if output_root.exists():
        shutil.rmtree(output_root)
    figure_dir = output_root / "figures"
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(table_dir / "event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(table_dir / "event_study_pretrends.csv", index=False)
    paths.to_csv(table_dir / "normalized_paths_long.csv", index=False)
    render_all_figures(coefficients, pretrends, paths, figure_dir, dpi=dpi)
    validate_figure_files(figure_dir)
    write_blindspot_report(output_root, coefficients, pretrends, paths)
    write_readme(output_root, source_hashes, pretrends)
    write_manifest(output_root)
    return coefficients, pretrends, paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.input_root, args.output_root, dpi=args.dpi)
