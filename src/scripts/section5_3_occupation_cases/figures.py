"""Publication figures for the descriptive occupation-case extension."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

from .config import (
    AGE_LABELS,
    AGE_ORDER,
    CASE_ORDER,
    CASE_SHORT_LABELS,
    DEMOGRAPHIC_SPECS,
    SHOCK_DATE,
)


AGE_COLORS = {
    "age_22_25": "#0072B2",
    "age_26_30": "#56B4E9",
    "age_31_34": "#009E73",
    "age_35_40": "#E69F00",
    "age_41_49": "#D55E00",
    "age_50_plus": "#CC79A7",
}
FOCAL_COLOR = "#0072B2"
COMPARISON_COLOR = "#D55E00"
TEXT_DARK = "#1A1A1A"
TEXT_MUTED = "#5C5C5C"
GRID_COLOR = "#D7D7D7"


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8.5,
        }
    )


def _case_title(case_id: str) -> str:
    return {
        "software_developers": "Desenvolvedores\nde software",
        "customer_service": "Atendimento\nao cliente",
        "marketing_sales_managers": "Gerentes de marketing\ne vendas",
        "production_supervisors": "Supervisores\nde produção",
        "stock_clerks": "Estoquistas\ne repositores",
        "health_care_aides": "Auxiliares de saúde\ne cuidado",
    }[case_id]


def _prepare_age_paths(paths: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Filter, validate, and date-index the primary age paths."""
    data = paths[
        paths["variant_id"].eq("primary")
        & paths["dimension"].eq("age")
        & paths["outcome"].eq(outcome)
    ].copy()
    if data.empty:
        raise RuntimeError(f"No primary age paths found for {outcome}.")
    observed_cases = set(data["case_id"])
    if observed_cases != set(CASE_ORDER):
        raise RuntimeError(
            f"Age figure for {outcome} does not contain all six cases: "
            f"{sorted(observed_cases)}"
        )
    data["date"] = pd.PeriodIndex(data["period"], freq="M").to_timestamp(
        how="end"
    )
    return data


def _outcome_phrase(outcome: str) -> str:
    if outcome == "admissions":
        return "admissões"
    if outcome == "real_admission_wage":
        return "salário real de admissão"
    raise ValueError(f"Unsupported age-path outcome: {outcome}")


def _case_y_limits(case: pd.DataFrame) -> tuple[float, float]:
    finite = pd.to_numeric(case["path_index"], errors="coerce")
    finite = finite[np.isfinite(finite)]
    if finite.empty:
        return 0.9, 1.1
    lower = min(float(finite.min()), 1.0)
    upper = max(float(finite.max()), 1.0)
    span = max(upper - lower, 0.08)
    pad = max(span * 0.10, 0.025)
    return lower - pad, upper + pad


def _format_time_axis(ax) -> None:
    ax.axhline(
        1.0,
        color="#777777",
        linewidth=0.85,
        linestyle=":",
        gid="baseline-line",
    )
    ax.axvline(
        pd.Timestamp(SHOCK_DATE),
        color="#222222",
        linewidth=1.0,
        linestyle="--",
        gid="shock-line",
    )
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.7, alpha=0.65)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _figure_source_note(outcome: str) -> str:
    wage_note = (
        " Salários positivos winsorizados em P1/P99 dentro de CBO6×ano."
        if outcome == "real_admission_wage"
        else ""
    )
    return (
        "Nota: séries descritivas; o CAGED mede fluxos de novas contratações, "
        "enquanto a ADP mede estoque de emprego. A linha tracejada marca "
        f"30 de novembro de 2022.{wage_note}"
    )


def _heatmap_source_note(outcome: str) -> str:
    wage_note = (
        " Salários positivos winsorizados em P1/P99 dentro de CBO6×ano."
        if outcome == "real_admission_wage"
        else ""
    )
    return (
        "Nota: resultados descritivos; o CAGED mede fluxos de novas "
        "contratações, enquanto a ADP mede estoque de emprego."
        f"{wage_note}"
    )


def make_age_paths_free_scale_figure(paths: pd.DataFrame, outcome: str):
    """Create the selected six-panel layout with case-specific y-scales."""
    setup_style()
    data = _prepare_age_paths(paths, outcome)
    fig, axes = plt.subplots(
        3,
        2,
        figsize=(12.8, 13.2),
        sharex=True,
        sharey=False,
    )
    for ax, case_id in zip(axes.flat, CASE_ORDER):
        case = data[data["case_id"].eq(case_id)]
        for age_id in AGE_ORDER:
            series = case[case["group_id"].eq(age_id)].sort_values("date")
            ax.plot(
                series["date"],
                series["path_index"],
                color=AGE_COLORS[age_id],
                linewidth=1.75,
                alpha=0.96,
                label=AGE_LABELS[age_id],
                gid=f"age-path-{age_id}",
            )
        _format_time_axis(ax)
        ax.set_ylim(*_case_y_limits(case))
        ax.set_title(
            _case_title(case_id),
            loc="left",
            fontweight="bold",
            color=TEXT_DARK,
        )
        ax.set_ylabel("Índice (out. 2022 = 1)")

    fig.suptitle(
        f"{_outcome_phrase(outcome).capitalize()} por caso e idade",
        x=0.07,
        y=0.975,
        ha="left",
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.07,
        0.945,
        "Painéis maiores e escala vertical própria por ocupação; "
        "compare a direção das trajetórias, não a amplitude entre painéis.",
        ha="left",
        color=TEXT_MUTED,
        fontsize=9.5,
    )
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.055),
        ncol=6,
        frameon=False,
        title="Faixa etária",
    )
    fig.text(
        0.07,
        0.012,
        _figure_source_note(outcome),
        ha="left",
        va="bottom",
        fontsize=8.2,
        color=TEXT_MUTED,
    )
    fig.subplots_adjust(
        left=0.09,
        right=0.985,
        top=0.89,
        bottom=0.12,
        hspace=0.45,
        wspace=0.18,
    )
    return fig


def make_age_paths_split_figure(paths: pd.DataFrame, outcome: str):
    """Alternative B: split younger and older age bands within each case."""
    setup_style()
    data = _prepare_age_paths(paths, outcome)
    age_columns = [
        ("22–34 anos", AGE_ORDER[:3]),
        ("35 anos ou mais", AGE_ORDER[3:]),
    ]
    fig, axes = plt.subplots(
        len(CASE_ORDER),
        2,
        figsize=(13.8, 17.2),
        sharex=True,
        sharey="row",
    )
    for row, case_id in enumerate(CASE_ORDER):
        case = data[data["case_id"].eq(case_id)]
        limits = _case_y_limits(case)
        for column, (column_title, age_ids) in enumerate(age_columns):
            ax = axes[row, column]
            for age_id in age_ids:
                series = case[case["group_id"].eq(age_id)].sort_values("date")
                ax.plot(
                    series["date"],
                    series["path_index"],
                    color=AGE_COLORS[age_id],
                    linewidth=1.85,
                    alpha=0.97,
                    label=AGE_LABELS[age_id],
                    gid=f"age-path-{age_id}",
                )
            _format_time_axis(ax)
            ax.set_ylim(*limits)
            if row == 0:
                ax.set_title(
                    column_title,
                    loc="left",
                    fontweight="bold",
                    color=TEXT_DARK,
                    pad=10,
                )
            if column == 0:
                ax.set_ylabel(
                    CASE_SHORT_LABELS[case_id],
                    rotation=0,
                    ha="right",
                    va="center",
                    labelpad=62,
                    fontweight="bold",
                )

    fig.suptitle(
        f"Alternativa B — {_outcome_phrase(outcome).capitalize()} por caso e idade",
        x=0.22,
        y=0.985,
        ha="left",
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.22,
        0.965,
        "Cada ocupação ocupa uma linha; as faixas jovens e maduras são "
        "separadas em colunas com a mesma escala dentro da linha.",
        ha="left",
        color=TEXT_MUTED,
        fontsize=9.5,
    )
    handles: list[object] = []
    labels: list[str] = []
    for ax in axes[0]:
        axis_handles, axis_labels = ax.get_legend_handles_labels()
        handles.extend(axis_handles)
        labels.extend(axis_labels)
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.57, 0.045),
        ncol=6,
        frameon=False,
        title="Faixa etária",
    )
    fig.text(
        0.22,
        0.012,
        _figure_source_note(outcome)
        + " Escalas verticais variam entre ocupações.",
        ha="left",
        va="bottom",
        fontsize=8.2,
        color=TEXT_MUTED,
    )
    fig.subplots_adjust(
        left=0.22,
        right=0.985,
        top=0.925,
        bottom=0.095,
        hspace=0.42,
        wspace=0.08,
    )
    return fig


def make_age_terminal_heatmap(terminal: pd.DataFrame, outcome: str):
    """Alternative C: annotated case-by-age terminal-change heatmap."""
    setup_style()
    data = terminal[
        terminal["variant_id"].eq("primary")
        & terminal["dimension"].eq("age")
        & terminal["outcome"].eq(outcome)
    ].copy()
    if data.empty:
        raise RuntimeError(f"No primary age terminal results found for {outcome}.")
    if data.duplicated(["case_id", "group_id"]).any():
        raise RuntimeError(
            f"Duplicate case-by-age terminal results found for {outcome}."
        )
    observed_cases = set(data["case_id"])
    if observed_cases != set(CASE_ORDER):
        raise RuntimeError(
            f"Terminal heatmap for {outcome} does not contain all six cases: "
            f"{sorted(observed_cases)}"
        )
    data["plot_value"] = data["terminal_change_pct"].where(
        data["support_status"].eq("adequate")
    )
    matrix = (
        data.pivot(index="case_id", columns="group_id", values="plot_value")
        .reindex(index=CASE_ORDER, columns=AGE_ORDER)
        .astype(float)
    )
    finite = matrix.to_numpy()[np.isfinite(matrix.to_numpy())]
    if finite.size == 0:
        raise RuntimeError(f"No supported terminal values found for {outcome}.")
    vmin = min(float(finite.min()), -1e-6)
    vmax = max(float(finite.max()), 1e-6)
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)

    fig, ax = plt.subplots(figsize=(12.8, 6.8))
    image = ax.imshow(
        np.ma.masked_invalid(matrix.to_numpy()),
        cmap="RdBu",
        norm=norm,
        aspect="auto",
        interpolation="nearest",
    )
    ax.set_xticks(
        np.arange(len(AGE_ORDER)),
        [AGE_LABELS[age_id] for age_id in AGE_ORDER],
    )
    ax.set_yticks(
        np.arange(len(CASE_ORDER)),
        [CASE_SHORT_LABELS[case_id] for case_id in CASE_ORDER],
    )
    ax.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False)
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(AGE_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(CASE_ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=2.0)
    ax.tick_params(which="minor", bottom=False, left=False)

    for row in range(len(CASE_ORDER)):
        for column in range(len(AGE_ORDER)):
            value = matrix.iat[row, column]
            if pd.isna(value):
                ax.text(
                    column,
                    row,
                    "sem\nsuporte",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=TEXT_MUTED,
                )
                continue
            normalized = float(norm(value))
            text_color = "white" if normalized < 0.22 or normalized > 0.78 else TEXT_DARK
            annotation = ax.text(
                column,
                row,
                f"{value:+.1f}%",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color=text_color,
            )
            annotation.set_gid("heatmap-value")

    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    colorbar.set_label("Variação em relação a out. 2022 (%)")
    colorbar.outline.set_visible(False)
    fig.suptitle(
        f"Alternativa C — {_outcome_phrase(outcome).capitalize()} em jan.–jun. 2025",
        x=0.17,
        y=0.985,
        ha="left",
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.17,
        0.925,
        "Variação percentual da média do índice no período em relação a out. 2022. "
        "A matriz facilita comparações, mas não mostra a trajetória mensal.",
        ha="left",
        color=TEXT_MUTED,
        fontsize=9.5,
    )
    fig.text(
        0.17,
        0.025,
        _heatmap_source_note(outcome),
        ha="left",
        va="bottom",
        fontsize=8.2,
        color=TEXT_MUTED,
    )
    fig.subplots_adjust(
        left=0.17,
        right=0.92,
        top=0.84,
        bottom=0.11,
    )
    return fig


def make_age_paths_figure(paths: pd.DataFrame, outcome: str):
    """Create the official age-path figure using the selected layout A."""
    return make_age_paths_free_scale_figure(paths, outcome)


def make_demographic_dumbbell(matrix: pd.DataFrame, dimension: str):
    """Create a two-outcome appendix dumbbell for one demographic dimension."""
    if dimension not in DEMOGRAPHIC_SPECS:
        raise ValueError(f"Unsupported demographic dimension: {dimension}")
    setup_style()
    data = matrix[matrix["dimension"].eq(dimension)].copy()
    focal_id, focal_label = DEMOGRAPHIC_SPECS[dimension][0]
    comparison_id, comparison_label = DEMOGRAPHIC_SPECS[dimension][1]
    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.7), sharey=True)
    y_positions = np.arange(len(CASE_ORDER))[::-1]
    labels = [CASE_SHORT_LABELS[case_id] for case_id in CASE_ORDER]
    outcome_specs = [
        ("admissions", "Admissões", "p.p. em relação a out. 2022"),
        (
            "real_admission_wage",
            "Salário real de admissão",
            "p.p. em relação a out. 2022",
        ),
    ]
    for ax, (outcome, title, xlabel) in zip(axes, outcome_specs):
        view = data[data["outcome"].eq(outcome)].set_index("case_id")
        all_values: list[float] = []
        for y, case_id in zip(y_positions, CASE_ORDER):
            if case_id not in view.index:
                ax.text(0, y, "sem suporte", ha="center", va="center", color=TEXT_MUTED, fontsize=8)
                continue
            row = view.loc[case_id]
            focal = row["focal_change_pct"]
            comparison = row["comparison_change_pct"]
            supported = bool(row["support_adequate"])
            if not supported or pd.isna(focal) or pd.isna(comparison):
                ax.text(0, y, "sem suporte", ha="center", va="center", color=TEXT_MUTED, fontsize=8)
                continue
            all_values.extend([float(focal), float(comparison)])
            ax.plot(
                [comparison, focal],
                [y, y],
                color="#A8A8A8",
                linewidth=1.6,
                zorder=1,
            )
            ax.scatter(
                comparison,
                y,
                s=44,
                color=COMPARISON_COLOR,
                edgecolor="white",
                linewidth=0.5,
                zorder=2,
                label=comparison_label if y == y_positions[0] else None,
            )
            ax.scatter(
                focal,
                y,
                s=44,
                color=FOCAL_COLOR,
                edgecolor="white",
                linewidth=0.5,
                zorder=2,
                label=focal_label if y == y_positions[0] else None,
            )
        ax.axvline(0, color="#555555", linestyle=":", linewidth=0.9)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel(xlabel)
        ax.set_yticks(y_positions, labels)
        ax.grid(axis="x", color=GRID_COLOR, linewidth=0.7, alpha=0.65)
        if all_values:
            lower, upper = min(all_values), max(all_values)
            pad = max((upper - lower) * 0.12, 2.0)
            ax.set_xlim(min(lower - pad, -1), max(upper + pad, 1))
    title = {
        "sex": "Trajetórias terminais por sexo",
        "race_color": "Trajetórias terminais por raça/cor",
        "education": "Trajetórias terminais por escolaridade",
    }[dimension]
    fig.suptitle(title, x=0.08, y=0.98, ha="left", fontsize=14, fontweight="bold")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.04),
        ncol=2,
        frameon=False,
    )
    fig.text(
        0.08,
        0.005,
        "Nota: média de jan.–jun. 2025 do índice normalizado em out. 2022, expressa como variação percentual. "
        "Comparações descritivas; células sem suporte prévio mínimo não são exibidas. "
        "Salários positivos winsorizados em P1/P99 dentro de CBO6×ano.",
        fontsize=8.2,
        color=TEXT_MUTED,
    )
    fig.subplots_adjust(left=0.25, right=0.98, top=0.86, bottom=0.18, wspace=0.15)
    return fig


def save_figure_bundle(fig, destination: Path, stem: str) -> list[Path]:
    """Export a Matplotlib figure to PNG, PDF, and SVG from one rendered object."""
    destination.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for suffix in [".png", ".pdf", ".svg"]:
        path = destination / f"{stem}{suffix}"
        fig.savefig(
            path,
            dpi=300 if suffix == ".png" else None,
            bbox_inches="tight",
            facecolor="white",
        )
        paths.append(path)
    plt.close(fig)
    return paths
