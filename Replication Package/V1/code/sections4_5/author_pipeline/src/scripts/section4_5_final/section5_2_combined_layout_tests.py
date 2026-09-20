#!/usr/bin/env python3
"""Render three dissertation layout prototypes for age dynamic evidence.

The script reuses the already estimated Section 5.2 age event studies and
normalized paths. It does not re-estimate models or modify official figures.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from section4_5_final.section5_2_dynamic_figures import (  # noqa: E402
    AGE_COLORS,
    EVENT_MAX,
    EVENT_MIN,
    REFERENCE_PERIOD,
    _lighten_color,
    _status_pt,
)
from section4_5_final.section5_2_tables import HETEROGENEITY_SPECS  # noqa: E402
from section4_5_final.style import (  # noqa: E402
    GRID,
    TEXT_DARK,
    TEXT_MUTED,
    get_pyplot,
    setup_plot_style,
)


ROOT = Path(__file__).resolve().parents[3]
INPUT_TABLE_DIR = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "experimental"
    / "section5_2_dynamic"
    / "tables"
)
OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "section4_5_final"
    / "experimental"
    / "section5_2_combined_layout_tests"
)

AGE_GROUPS = list(HETEROGENEITY_SPECS["age_canaries"]["groups"])
FOCAL_OUTCOMES = ["ln_admissoes", "ln_salario_real_adm"]
OUTCOME_TITLES = {
    "ln_admissoes": "Admissões",
    "ln_salario_real_adm": "Salário real de admissão",
}
OUTCOME_FILE_STEMS = {
    "ln_admissoes": "admissions",
    "ln_salario_real_adm": "real_admission_wage",
}

LAYOUT_FILENAMES = [
    "layout_1_outcome_first_admissions.png",
    "layout_1_outcome_first_real_admission_wage.png",
    "layout_2_method_first_event_studies.png",
    "layout_2_method_first_paths.png",
    "layout_3_stage_first_early_career.png",
    "layout_3_stage_first_later_career.png",
    "layout_comparison_sheet.png",
]


def expected_layout_filenames() -> list[str]:
    """Return the complete prototype artifact contract."""
    return list(LAYOUT_FILENAMES)


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def validate_age_inputs(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> None:
    """Validate the complete age-by-outcome grids used by every layout."""
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

    group_ids = {group_id for group_id, _ in AGE_GROUPS}
    event_times = set(range(EVENT_MIN, EVENT_MAX + 1))
    expected_coefficients = len(AGE_GROUPS) * len(FOCAL_OUTCOMES) * len(event_times)
    expected_pretrends = len(AGE_GROUPS) * len(FOCAL_OUTCOMES)
    expected_paths = expected_coefficients * 2

    contracts = [
        (coefficients, expected_coefficients, ["group_id", "outcome", "t"], "coefficients"),
        (pretrends, expected_pretrends, ["group_id", "outcome"], "pretrends"),
        (paths, expected_paths, ["group_id", "outcome", "scenario_role", "t"], "paths"),
    ]
    for frame, expected_rows, keys, name in contracts:
        if len(frame) != expected_rows:
            raise ValueError(f"{name} has {len(frame)} rows; expected {expected_rows}")
        if frame.duplicated(keys).any():
            raise ValueError(f"{name} contains duplicate cells for {keys}")
        if set(frame["dimension"]) != {"age_canaries"}:
            raise ValueError(f"{name} must contain only the age_canaries dimension")
        if set(frame["group_id"]) != group_ids:
            raise ValueError(f"{name} does not contain the six required age groups")
        if set(frame["outcome"]) != set(FOCAL_OUTCOMES):
            raise ValueError(f"{name} must contain only admissions and real admission wages")

    if set(coefficients["t"]) != event_times or set(paths["t"]) != event_times:
        raise ValueError("Dynamic inputs do not cover the strict t=-12,...,24 window")
    if set(paths["scenario_role"]) != {"treated", "control"}:
        raise ValueError("Paths must contain Exposed and Not Exposed roles")

    reference = coefficients[coefficients["t"].eq(REFERENCE_PERIOD)]
    if len(reference) != expected_pretrends or not np.allclose(reference["coef"], 0.0, equal_nan=False):
        raise ValueError("Every event-study reference coefficient at t=-1 must equal zero")


def load_age_inputs(input_dir: Path = INPUT_TABLE_DIR) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and filter the existing Section 5.2 dynamic long tables."""
    filenames = {
        "coefficients": "event_study_coefficients_long.csv",
        "pretrends": "event_study_pretrends.csv",
        "paths": "normalized_paths_long.csv",
    }
    loaded = {}
    for name, filename in filenames.items():
        path = input_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Missing dynamic input: {path}")
        frame = pd.read_csv(path)
        loaded[name] = frame[
            frame["dimension"].eq("age_canaries") & frame["outcome"].isin(FOCAL_OUTCOMES)
        ].copy()
    result = loaded["coefficients"], loaded["pretrends"], loaded["paths"]
    validate_age_inputs(*result)
    return result


def _save_figure(fig: object, output_path: Path, dpi: int) -> Path:
    plt = get_pyplot()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def _event_ylim(coefficients: pd.DataFrame, outcome: str) -> tuple[float, float]:
    selected = coefficients[coefficients["outcome"].eq(outcome)]
    bounds = selected[["ci_low", "ci_high"]].apply(pd.to_numeric, errors="coerce").to_numpy().ravel()
    bounds = bounds[np.isfinite(bounds)]
    maximum = max(0.05, float(np.abs(bounds).max()) if bounds.size else 0.05)
    return -1.06 * maximum, 1.06 * maximum


def _path_ylim(paths: pd.DataFrame, outcome: str) -> tuple[float, float]:
    values = pd.to_numeric(paths.loc[paths["outcome"].eq(outcome), "path_index"], errors="coerce").dropna()
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
    ylim: tuple[float, float],
    title: str | None = None,
    show_xlabels: bool = True,
    compact_diagnostic: bool = False,
) -> None:
    color = AGE_COLORS[group_id]
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
            linewidth=1.65,
            marker="o",
            markersize=2.2,
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
    if title:
        axis.set_title(title, loc="left", color=color, fontweight="bold", fontsize=10.5, pad=4)
    if not diagnostic.empty:
        status = _status_pt(str(diagnostic.iloc[0]["pretrend_status"]))
        power = str(diagnostic.iloc[0].get("power_status", "não disponível"))
        label = f"pré: {status}" if compact_diagnostic else f"pretrend: {status} | poder: {power}"
        axis.text(
            0.985,
            0.965,
            label,
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=6.4 if compact_diagnostic else 6.9,
            color=TEXT_MUTED,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.65, "pad": 0.8},
        )
    axis.set_xlim(EVENT_MIN, EVENT_MAX)
    axis.set_ylim(*ylim)
    axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
    axis.tick_params(axis="x", labelbottom=show_xlabels)
    axis.grid(axis="x", visible=False)


def _draw_path_axis(
    axis: object,
    paths: pd.DataFrame,
    *,
    group_id: str,
    outcome: str,
    ylim: tuple[float, float],
    title: str | None = None,
    show_xlabels: bool = True,
) -> None:
    color = AGE_COLORS[group_id]
    control_color = _lighten_color(color)
    view = paths[paths["group_id"].eq(group_id) & paths["outcome"].eq(outcome)]
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
        axis.plot(treated["t"], treated["path_index"], color=color, linewidth=1.8, zorder=3)
    if treated.empty and control.empty:
        axis.text(0.5, 0.5, "trajetória indisponível", transform=axis.transAxes, ha="center", va="center", color=TEXT_MUTED)
    if title:
        axis.set_title(title, loc="left", color=color, fontweight="bold", fontsize=10.5, pad=4)
    axis.set_xlim(EVENT_MIN, EVENT_MAX)
    axis.set_ylim(*ylim)
    axis.set_xticks([-12, -6, 0, 6, 12, 18, 24])
    axis.tick_params(axis="x", labelbottom=show_xlabels)
    axis.grid(axis="x", visible=False)


def _path_legend_handles() -> list[object]:
    from matplotlib.lines import Line2D

    return [
        Line2D([0], [0], color=TEXT_DARK, linewidth=2.0, label="Exposed"),
        Line2D([0], [0], color="#A9A9A9", linewidth=1.6, linestyle=(0, (4, 2.5)), label="Not Exposed"),
    ]


def plot_layout_1_outcome_first(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    outcome: str,
    output_path: Path,
    dpi: int,
) -> Path:
    """Place an event study above its path inside each age card."""
    plt = get_pyplot()
    setup_plot_style()
    fig = plt.figure(figsize=(14.8, 10.6))
    outer = fig.add_gridspec(
        2,
        3,
        left=0.075,
        right=0.985,
        top=0.82,
        bottom=0.13,
        hspace=0.34,
        wspace=0.19,
    )
    event_ylim = _event_ylim(coefficients, outcome)
    path_ylim = _path_ylim(paths, outcome)

    for index, (group_id, group_label) in enumerate(AGE_GROUPS):
        row, column = divmod(index, 3)
        inner = outer[row, column].subgridspec(2, 1, height_ratios=[1.05, 0.95], hspace=0.08)
        event_axis = fig.add_subplot(inner[0])
        path_axis = fig.add_subplot(inner[1], sharex=event_axis)
        _draw_event_axis(
            event_axis,
            coefficients,
            pretrends,
            group_id=group_id,
            outcome=outcome,
            ylim=event_ylim,
            title=group_label,
            show_xlabels=False,
        )
        _draw_path_axis(
            path_axis,
            paths,
            group_id=group_id,
            outcome=outcome,
            ylim=path_ylim,
        )
        event_axis.text(0.01, 0.91, "Event study DDD", transform=event_axis.transAxes, fontsize=6.8, color=TEXT_MUTED)
        path_axis.text(0.01, 0.91, "Trajetória", transform=path_axis.transAxes, fontsize=6.8, color=TEXT_MUTED)
        if column == 0:
            event_axis.set_ylabel("Coeficiente DDD (log)", fontsize=8)
            path_axis.set_ylabel("Índice (pré=100)", fontsize=8)

    fig.suptitle(
        f"Teste de layout 1 — {OUTCOME_TITLES[outcome]}: event study e trajetória por idade",
        x=0.075,
        y=0.97,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.075,
        0.915,
        "Cada faixa etária funciona como um cartão: evidência inferencial acima e trajetórias descritivas abaixo.",
        ha="left",
        color=TEXT_MUTED,
        fontsize=9.2,
    )
    fig.legend(handles=_path_legend_handles(), loc="upper right", bbox_to_anchor=(0.985, 0.91), frameon=False, ncol=2)
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.075, fontsize=9.5)
    wage_note = " Salários das trajetórias winsorizados em P1/P99." if outcome == "ln_salario_real_adm" else ""
    fig.text(
        0.075,
        0.022,
        "Nota: event studies DDD com IC pontual de 95% e referência t=-1; trajetórias normalizadas pela média pré (=100). "
        f"Linhas escuras: Exposed; linhas claras tracejadas: Not Exposed.{wage_note}",
        ha="left",
        fontsize=7.5,
        color=TEXT_MUTED,
    )
    return _save_figure(fig, output_path, dpi)


def plot_layout_2_method_first(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    kind: str,
    output_path: Path,
    dpi: int,
) -> Path:
    """Stack complete outcome blocks on an inference or paths page."""
    if kind not in {"event_studies", "paths"}:
        raise ValueError(f"Unsupported method-first figure kind: {kind}")
    plt = get_pyplot()
    setup_plot_style()
    fig = plt.figure(figsize=(14.8, 11.5))
    grid = fig.add_gridspec(
        4,
        3,
        left=0.075,
        right=0.985,
        top=0.80,
        bottom=0.12,
        hspace=0.48,
        wspace=0.19,
    )
    axes: list[list[object]] = [[], []]

    for outcome_index, outcome in enumerate(FOCAL_OUTCOMES):
        ylim = _event_ylim(coefficients, outcome) if kind == "event_studies" else _path_ylim(paths, outcome)
        for group_index, (group_id, group_label) in enumerate(AGE_GROUPS):
            within_row, column = divmod(group_index, 3)
            row = outcome_index * 2 + within_row
            axis = fig.add_subplot(grid[row, column])
            axes[outcome_index].append(axis)
            show_xlabels = within_row == 1
            if kind == "event_studies":
                _draw_event_axis(
                    axis,
                    coefficients,
                    pretrends,
                    group_id=group_id,
                    outcome=outcome,
                    ylim=ylim,
                    title=group_label,
                    show_xlabels=show_xlabels,
                )
            else:
                _draw_path_axis(
                    axis,
                    paths,
                    group_id=group_id,
                    outcome=outcome,
                    ylim=ylim,
                    title=group_label,
                    show_xlabels=show_xlabels,
                )
            if column == 0:
                label = "Coeficiente DDD (log)" if kind == "event_studies" else "Índice (pré=100)"
                axis.set_ylabel(label, fontsize=8)

    fig.canvas.draw()
    for outcome_index, outcome in enumerate(FOCAL_OUTCOMES):
        header_y = axes[outcome_index][0].get_position().y1 + 0.023
        fig.text(
            0.075,
            header_y,
            f"Painel {'A' if outcome_index == 0 else 'B'} · {OUTCOME_TITLES[outcome]}",
            ha="left",
            va="bottom",
            fontsize=11.2,
            fontweight="bold",
            color=TEXT_DARK,
        )

    method_title = "Event studies de admissões e salário de admissão" if kind == "event_studies" else "Trajetórias de admissões e salário de admissão"
    fig.suptitle(
        f"Teste de layout 2 — {method_title}",
        x=0.075,
        y=0.97,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_DARK,
    )
    subtitle = (
        "Uma página concentra toda a inferência; a trajetória correspondente fica na segunda figura."
        if kind == "event_studies"
        else "Uma página concentra toda a evidência descritiva; a inferência correspondente fica na primeira figura."
    )
    fig.text(0.075, 0.92, subtitle, ha="left", fontsize=9.2, color=TEXT_MUTED)
    if kind == "paths":
        fig.legend(handles=_path_legend_handles(), loc="upper right", bbox_to_anchor=(0.985, 0.915), frameon=False, ncol=2)
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.07, fontsize=9.5)
    note = (
        "Nota: coeficientes DDD com IC pontual de 95%; referência t=-1; o diagnóstico de pretrend aparece em cada painel."
        if kind == "event_studies"
        else "Nota: trajetórias normalizadas pela média pré (=100); Exposed em linha escura e Not Exposed em linha clara tracejada. Salários winsorizados em P1/P99."
    )
    fig.text(0.075, 0.025, note, ha="left", fontsize=7.5, color=TEXT_MUTED)
    return _save_figure(fig, output_path, dpi)


def plot_layout_3_stage_first(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    *,
    groups: list[tuple[str, str]],
    stage_label: str,
    output_path: Path,
    dpi: int,
) -> Path:
    """Give each age band one row with both outcomes and both evidence types."""
    if len(groups) != 3:
        raise ValueError("The career-stage layout requires exactly three age groups")
    plt = get_pyplot()
    setup_plot_style()
    fig = plt.figure(figsize=(15.6, 9.6))
    grid = fig.add_gridspec(
        3,
        4,
        left=0.085,
        right=0.985,
        top=0.80,
        bottom=0.13,
        hspace=0.34,
        wspace=0.28,
    )
    columns = [
        ("ln_admissoes", "event", "Admissões\nEvent study · coeficiente DDD"),
        ("ln_admissoes", "path", "Admissões\nTrajetória · índice pré=100"),
        ("ln_salario_real_adm", "event", "Salário real de admissão\nEvent study · coeficiente DDD"),
        ("ln_salario_real_adm", "path", "Salário real de admissão\nTrajetória · índice pré=100"),
    ]
    limits = {
        (outcome, "event"): _event_ylim(coefficients, outcome)
        for outcome in FOCAL_OUTCOMES
    }
    limits.update({
        (outcome, "path"): _path_ylim(paths, outcome)
        for outcome in FOCAL_OUTCOMES
    })
    axes: list[list[object]] = []

    for row, (group_id, _) in enumerate(groups):
        row_axes = []
        for column, (outcome, kind, column_title) in enumerate(columns):
            axis = fig.add_subplot(grid[row, column])
            row_axes.append(axis)
            show_xlabels = row == len(groups) - 1
            if kind == "event":
                _draw_event_axis(
                    axis,
                    coefficients,
                    pretrends,
                    group_id=group_id,
                    outcome=outcome,
                    ylim=limits[(outcome, kind)],
                    show_xlabels=show_xlabels,
                    compact_diagnostic=True,
                )
            else:
                _draw_path_axis(
                    axis,
                    paths,
                    group_id=group_id,
                    outcome=outcome,
                    ylim=limits[(outcome, kind)],
                    show_xlabels=show_xlabels,
                )
            if row == 0:
                axis.set_title(column_title, loc="left", fontsize=9.2, fontweight="bold", color=TEXT_DARK, pad=8)
        axes.append(row_axes)

    fig.canvas.draw()
    for row, (group_id, group_label) in enumerate(groups):
        position = axes[row][0].get_position()
        fig.text(
            0.018,
            0.5 * (position.y0 + position.y1),
            group_label,
            ha="left",
            va="center",
            fontsize=11.5,
            fontweight="bold",
            color=AGE_COLORS[group_id],
        )
    from matplotlib.lines import Line2D

    divider_x = 0.5 * (axes[0][1].get_position().x1 + axes[0][2].get_position().x0)
    fig.add_artist(
        Line2D(
            [divider_x, divider_x],
            [0.12, 0.82],
            transform=fig.transFigure,
            color=GRID,
            linewidth=1.0,
        )
    )
    fig.suptitle(
        f"Teste de layout 3 — {stage_label}: painel completo por faixa etária",
        x=0.085,
        y=0.97,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=TEXT_DARK,
    )
    fig.text(
        0.085,
        0.915,
        "Cada linha permite ler admissões e salário, inferência e trajetórias, sem trocar de figura.",
        ha="left",
        fontsize=9.2,
        color=TEXT_MUTED,
    )
    fig.legend(handles=_path_legend_handles(), loc="upper right", bbox_to_anchor=(0.985, 0.91), frameon=False, ncol=2)
    fig.supxlabel("Meses relativos ao lançamento do ChatGPT (t=0)", y=0.073, fontsize=9.5)
    fig.text(
        0.085,
        0.025,
        "Nota: event studies DDD com IC pontual de 95% e referência t=-1; trajetórias normalizadas pela média pré (=100). "
        "Salários das trajetórias winsorizados em P1/P99. Diagnósticos reprovados limitam interpretações causais.",
        ha="left",
        fontsize=7.5,
        color=TEXT_MUTED,
    )
    return _save_figure(fig, output_path, dpi)


def plot_comparison_sheet(page_paths: list[Path], output_path: Path, dpi: int) -> Path:
    """Build a lightweight six-page contact sheet for layout selection."""
    if len(page_paths) != 6:
        raise ValueError("The comparison sheet requires the six layout pages")
    from PIL import Image

    plt = get_pyplot()
    setup_plot_style()
    fig, axes = plt.subplots(3, 2, figsize=(15.0, 17.0))
    fig.subplots_adjust(left=0.025, right=0.985, top=0.94, bottom=0.025, hspace=0.16, wspace=0.05)
    titles = [
        "Layout 1 · Admissões",
        "Layout 1 · Salário real de admissão",
        "Layout 2 · Event studies",
        "Layout 2 · Trajetórias",
        "Layout 3 · Início da carreira",
        "Layout 3 · Fases posteriores",
    ]
    for axis, page_path, title in zip(axes.flat, page_paths, titles):
        with Image.open(page_path) as source:
            preview = source.convert("RGB")
            preview.thumbnail((1600, 1200), Image.Resampling.LANCZOS)
            image = np.asarray(preview).copy()
        axis.imshow(image)
        axis.set_title(title, loc="left", fontsize=11, fontweight="bold", pad=8)
        axis.axis("off")
    fig.suptitle(
        "Comparação dos três layouts propostos",
        x=0.025,
        y=0.985,
        ha="left",
        fontsize=17,
        fontweight="bold",
        color=TEXT_DARK,
    )
    return _save_figure(fig, output_path, dpi)


def render_all_layout_tests(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
    output_dir: Path,
    *,
    dpi: int = 300,
) -> list[Path]:
    """Render the three two-page layout alternatives and a comparison sheet."""
    validate_age_inputs(coefficients, pretrends, paths)
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    for outcome in FOCAL_OUTCOMES:
        rendered.append(
            plot_layout_1_outcome_first(
                coefficients,
                pretrends,
                paths,
                outcome=outcome,
                output_path=output_dir / f"layout_1_outcome_first_{OUTCOME_FILE_STEMS[outcome]}.png",
                dpi=dpi,
            )
        )
    rendered.append(
        plot_layout_2_method_first(
            coefficients,
            pretrends,
            paths,
            kind="event_studies",
            output_path=output_dir / "layout_2_method_first_event_studies.png",
            dpi=dpi,
        )
    )
    rendered.append(
        plot_layout_2_method_first(
            coefficients,
            pretrends,
            paths,
            kind="paths",
            output_path=output_dir / "layout_2_method_first_paths.png",
            dpi=dpi,
        )
    )
    rendered.append(
        plot_layout_3_stage_first(
            coefficients,
            pretrends,
            paths,
            groups=AGE_GROUPS[:3],
            stage_label="Início da carreira (22–34 anos)",
            output_path=output_dir / "layout_3_stage_first_early_career.png",
            dpi=dpi,
        )
    )
    rendered.append(
        plot_layout_3_stage_first(
            coefficients,
            pretrends,
            paths,
            groups=AGE_GROUPS[3:],
            stage_label="Fases posteriores da carreira (35+)",
            output_path=output_dir / "layout_3_stage_first_later_career.png",
            dpi=dpi,
        )
    )
    rendered.append(
        plot_comparison_sheet(
            rendered,
            output_dir / "layout_comparison_sheet.png",
            dpi,
        )
    )
    return rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=INPUT_TABLE_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frames = load_age_inputs(args.input_dir)
    render_all_layout_tests(*frames, args.output_dir)


if __name__ == "__main__":
    main()
