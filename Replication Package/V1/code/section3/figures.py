"""Build the ten published Section 3 figures."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .constants import (
    AGE_ORDER,
    EDUCATION_LABELS_PT,
    FIGURE_TITLES_PT,
    FORMAL_LABELS_PT,
    GRADIENT_COLORS,
    GRADIENT_LABELS_PT,
    GRADIENT_ORDER,
    GROUP_COLORS,
    GROUP_LABELS_PT,
    HIGH_GRADIENTS,
    INCOME_ORDER,
    LOW_GRADIENTS,
    MODERATE_GRADIENTS,
    RACE_ORDER,
    SEX_ORDER,
)
from .data import group_summary, official_data, scored_data, state_high_table
from .formatting import weighted_mean


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
STATE_GEOMETRY = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "section3"
    / "brazil_states_2020.gpkg"
)
_PYPLOT = None


def get_pyplot():
    global _PYPLOT
    if _PYPLOT is None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as pyplot

        _PYPLOT = pyplot
    return _PYPLOT


def setup_plot_style() -> None:
    pyplot = get_pyplot()
    pyplot.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linewidth": 0.8,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 8,
        }
    )


def save_figure(figure, path: Path) -> None:
    pyplot = get_pyplot()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    pyplot.close(figure)


def fmt_br(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def title_axis(axis, title: str) -> None:
    axis.set_title(
        title,
        loc="left",
        fontsize=13,
        fontweight="bold",
        pad=14,
    )


def plot_histogram_kde(frame: pd.DataFrame, path: Path) -> None:
    pyplot = get_pyplot()
    setup_plot_style()
    score = scored_data(frame)
    official = score[score["is_official_gradient"]]
    figure, axis = pyplot.subplots(figsize=(10.5, 5.8))
    bins = np.linspace(
        float(score["exposure_score"].min()),
        float(score["exposure_score"].max()),
        36,
    )
    for gradient in GRADIENT_ORDER:
        group = official[official["exposure_gradient"].eq(gradient)]
        axis.hist(
            group["exposure_score"],
            bins=bins,
            weights=group["peso"] / 1e6,
            stacked=True,
            color=GRADIENT_COLORS[gradient],
            alpha=0.88,
            label=GRADIENT_LABELS_PT[gradient],
        )
    try:
        from scipy.stats import gaussian_kde

        scores = score["exposure_score"].to_numpy(dtype=float)
        weights = score["peso"].to_numpy(dtype=float)
        density = gaussian_kde(scores, weights=weights / weights.sum())
        grid = np.linspace(scores.min(), scores.max(), 250)
        bin_width = (scores.max() - scores.min()) / (len(bins) - 1)
        values = density(grid) * weights.sum() / 1e6 * bin_width
        axis.plot(
            grid,
            values,
            color="#1f1f1f",
            linewidth=2,
            label="Densidade ponderada",
        )
    except Exception:
        pass
    mean_value = weighted_mean(score["exposure_score"], score["peso"])
    axis.axvline(
        mean_value,
        color="#b22222",
        linestyle="--",
        linewidth=1.8,
        label=f"Média = {mean_value:.3f}",
    )
    title_axis(axis, FIGURE_TITLES_PT["3.1"])
    axis.set_xlabel("Score de exposição à IA")
    axis.set_ylabel("Trabalhadores (milhões)")
    axis.legend(ncol=2)
    save_figure(figure, path)


def plot_gradient_population(frame: pd.DataFrame, path: Path) -> None:
    pyplot = get_pyplot()
    setup_plot_style()
    official = official_data(frame)
    total = float(official["peso"].sum())
    rows = [
        (
            "Exposição baixa",
            "Não exposto + exposição mínima",
            LOW_GRADIENTS,
            GROUP_COLORS["Low"],
        ),
        (
            "Exposição média",
            "Gradientes 1 e 2",
            MODERATE_GRADIENTS,
            GROUP_COLORS["Moderate"],
        ),
        (
            "Exposição alta",
            "Gradientes 3 e 4",
            HIGH_GRADIENTS,
            GROUP_COLORS["High"],
        ),
    ]
    labels = [f"{label}\n{subtitle}" for label, subtitle, _, _ in rows]
    values = [
        float(
            official.loc[
                official["exposure_gradient"].isin(gradients),
                "peso",
            ].sum()
        )
        / 1e6
        for _, _, gradients, _ in rows
    ]
    percentages = [value * 1e6 / total * 100 for value in values]
    colors = [color for _, _, _, color in rows]

    figure, axis = pyplot.subplots(figsize=(10.4, 5.4))
    y_positions = np.arange(len(labels))
    bars = axis.barh(y_positions, values, color=colors, height=0.58)
    axis.set_yticks(y_positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel("Trabalhadores (milhões)")
    title_axis(axis, FIGURE_TITLES_PT["3.2"])
    for bar, value, percentage in zip(bars, values, percentages):
        axis.text(
            bar.get_width() + max(values) * 0.018,
            bar.get_y() + bar.get_height() / 2,
            f"{fmt_br(value)} mi ({fmt_br(percentage)}%)",
            va="center",
            fontsize=10,
            color="#222222",
        )
    axis.text(
        0.64,
        0.18,
        "Chave de leitura\nMédia = complementaridade\nAlta = automação",
        transform=axis.transAxes,
        ha="left",
        va="center",
        fontsize=9.5,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "white",
            "edgecolor": "#D6D6D6",
            "linewidth": 0.8,
        },
    )
    axis.text(
        0.0,
        -0.18,
        "Nota: percentuais calculados sobre ocupados classificáveis nos "
        "seis gradientes oficiais da OIT.",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color="#555555",
    )
    axis.set_xlim(0, max(values) * 1.32)
    save_figure(figure, path)


def plot_score_by_occupation_group(
    frame: pd.DataFrame,
    path: Path,
) -> None:
    pyplot = get_pyplot()
    setup_plot_style()
    score = scored_data(frame)
    bins = np.linspace(0, 0.75, 16)
    groups = (
        score.groupby("grande_grupo")["peso"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    figure, axis = pyplot.subplots(figsize=(11, 6))
    bottom = np.zeros(len(bins) - 1)
    colormap = pyplot.get_cmap("tab10")
    centers = (bins[:-1] + bins[1:]) / 2
    width = bins[1] - bins[0]
    for index, group_name in enumerate(groups):
        group = score[score["grande_grupo"].eq(group_name)]
        values, _ = np.histogram(
            group["exposure_score"],
            bins=bins,
            weights=group["peso"] / 1e6,
        )
        axis.bar(
            centers,
            values,
            width=width * 0.95,
            bottom=bottom,
            color=colormap(index % 10),
            label=group_name,
        )
        bottom += values
    title_axis(axis, FIGURE_TITLES_PT["3.3"])
    axis.set_xlabel("Score de exposição à IA")
    axis.set_ylabel("Trabalhadores (milhões)")
    axis.legend(ncol=2, fontsize=7)
    save_figure(figure, path)


def plot_state_high(frame: pd.DataFrame, path: Path) -> None:
    pyplot = get_pyplot()
    setup_plot_style()
    import geopandas as gpd
    import matplotlib.patheffects as path_effects

    if not STATE_GEOMETRY.is_file():
        raise FileNotFoundError(
            f"Packaged state geometry is missing: {STATE_GEOMETRY}"
        )
    states = state_high_table(frame).rename(columns={"UF": "sigla_uf"})
    geography = gpd.read_file(STATE_GEOMETRY)
    geography["abbrev_state"] = geography["abbrev_state"].str.upper()
    geography = geography.merge(
        states,
        left_on="abbrev_state",
        right_on="sigla_uf",
        how="left",
    )
    if geography["High (%)"].isna().any():
        missing = geography.loc[
            geography["High (%)"].isna(),
            "abbrev_state",
        ].tolist()
        raise ValueError(f"Missing state data for: {missing}")

    figure = pyplot.figure(figsize=(11.2, 8.4))
    grid = figure.add_gridspec(
        2,
        2,
        height_ratios=[0.12, 0.88],
        width_ratios=[0.76, 0.24],
        wspace=0.02,
        hspace=0.0,
    )
    title_panel = figure.add_subplot(grid[0, :])
    map_panel = figure.add_subplot(grid[1, 0])
    side_panel = figure.add_subplot(grid[1, 1])
    title_panel.axis("off")
    side_panel.axis("off")
    map_panel.set_axis_off()

    title_panel.text(
        0.0,
        0.78,
        FIGURE_TITLES_PT["3.4"],
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        color="#1A1A1A",
    )
    title_panel.text(
        0.0,
        0.25,
        "Cor: participação dos trabalhadores em Gradientes 3 e 4 dentro da "
        "força de trabalho classificável de cada UF.",
        ha="left",
        va="top",
        fontsize=9.2,
        color="#555555",
    )

    values = geography["High (%)"].to_numpy(dtype=float)
    colormap = pyplot.get_cmap("Reds")
    normalization = pyplot.Normalize(
        vmin=float(values.min()),
        vmax=float(values.max()),
    )
    geography.plot(
        column="High (%)",
        cmap=colormap,
        norm=normalization,
        linewidth=0.45,
        edgecolor="#F7F2F0",
        ax=map_panel,
        legend=False,
    )
    geography.boundary.plot(
        ax=map_panel,
        color="#777777",
        linewidth=0.25,
    )

    callout_positions = {
        "DF": (-39.5, -15.8),
        "RN": (-32.9, -5.2),
        "PB": (-32.9, -6.9),
        "PE": (-32.9, -8.6),
        "AL": (-32.9, -10.3),
        "SE": (-32.9, -11.8),
        "ES": (-32.9, -19.3),
        "RJ": (-32.9, -22.5),
    }
    label_offsets = {"GO": (0.0, -0.7)}
    for _, row in geography.iterrows():
        state = row["abbrev_state"]
        centroid = row.geometry.centroid
        label = f"{state} {fmt_br(float(row['High (%)']))}%"
        if state in callout_positions:
            text_x, text_y = callout_positions[state]
            map_panel.annotate(
                "",
                xy=(centroid.x, centroid.y),
                xytext=(text_x - 0.2, text_y),
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#666666",
                    "lw": 0.55,
                    "shrinkA": 0,
                    "shrinkB": 0,
                },
            )
            color = "#222222"
            horizontal_alignment = "left"
        else:
            text_x, text_y = centroid.x, centroid.y
            offset_x, offset_y = label_offsets.get(state, (0.0, 0.0))
            text_x += offset_x
            text_y += offset_y
            relative = (
                float(row["High (%)"]) - float(values.min())
            ) / (float(values.max()) - float(values.min()))
            color = "white" if relative > 0.55 else "#222222"
            horizontal_alignment = "center"
        stroke = (
            [path_effects.withStroke(linewidth=1.6, foreground="#333333")]
            if color == "white"
            else [path_effects.withStroke(linewidth=2.2, foreground="white")]
        )
        map_panel.text(
            text_x,
            text_y,
            label,
            ha=horizontal_alignment,
            va="center",
            fontsize=7.2,
            fontweight="bold",
            color=color,
            path_effects=stroke,
        )

    bounds = geography.total_bounds
    map_panel.set_xlim(bounds[0] - 1.2, bounds[2] + 7.2)
    map_panel.set_ylim(bounds[1] - 1.2, bounds[3] + 1.2)
    scale = pyplot.cm.ScalarMappable(cmap=colormap, norm=normalization)
    scale.set_array([])
    colorbar = figure.colorbar(
        scale,
        ax=map_panel,
        fraction=0.032,
        pad=0.015,
    )
    colorbar.set_label("% da força de trabalho da UF", fontsize=9)
    colorbar.ax.tick_params(labelsize=8)

    top_volume = states.sort_values("High (M)", ascending=False).head(6)
    side_panel.text(
        0.0,
        0.98,
        "Maiores volumes\nabsolutos",
        ha="left",
        va="top",
        fontsize=10.5,
        fontweight="bold",
    )
    y_position = 0.82
    for _, row in top_volume.iterrows():
        side_panel.text(
            0.0,
            y_position,
            f"{row['sigla_uf']}",
            ha="left",
            va="center",
            fontsize=9.5,
            fontweight="bold",
        )
        side_panel.text(
            0.22,
            y_position,
            f"{fmt_br(float(row['High (M)']), 2)} mi",
            ha="left",
            va="center",
            fontsize=9.5,
        )
        y_position -= 0.085
    side_panel.text(
        0.0,
        0.16,
        "Fonte: PNAD Contínua 3T/2025\n(IBGE) e ILO WP140.",
        ha="left",
        va="bottom",
        fontsize=8.0,
        color="#555555",
    )
    save_figure(figure, path)


def plot_demographic_dimension(
    title: str,
    summary: pd.DataFrame,
    path: Path,
) -> None:
    pyplot = get_pyplot()
    setup_plot_style()
    plot_data = summary.copy()
    positions = np.arange(len(plot_data))
    figure_height = max(3.5, len(plot_data) * 0.55 + 1.5)
    figure, axis = pyplot.subplots(figsize=(9.5, figure_height))
    left = np.zeros(len(plot_data))
    for group, column in [
        ("Low", "low_pct"),
        ("Moderate", "moderate_pct"),
        ("High", "high_pct"),
    ]:
        values = plot_data[column].to_numpy(dtype=float)
        axis.barh(
            positions,
            values,
            left=left,
            color=GROUP_COLORS[group],
            label=GROUP_LABELS_PT[group],
        )
        for index, value in enumerate(values):
            if value >= 4:
                axis.text(
                    left[index] + value / 2,
                    index,
                    f"{fmt_br(value)}%",
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=8,
                )
        left += values
    for index, row in enumerate(plot_data.itertuples(index=False)):
        axis.text(
            101,
            index,
            f"{fmt_br(row.population_m)} mi",
            va="center",
            fontsize=8,
        )
    axis.set_yticks(positions, plot_data["category"])
    axis.invert_yaxis()
    axis.set_xlim(0, 112)
    axis.set_xlabel("Participação na categoria (%)")
    title_axis(axis, title)
    axis.legend(ncol=3, loc="lower right")
    save_figure(figure, path)


def write_figures(frame: pd.DataFrame, output_dir: Path) -> list[Path]:
    figure_dir = output_dir / "figures"
    plot_histogram_kde(
        frame,
        figure_dir / "figure_3_1_histogram_kde.png",
    )
    plot_gradient_population(
        frame,
        figure_dir / "figure_3_2_gradient_population.png",
    )
    plot_score_by_occupation_group(
        frame,
        figure_dir / "figure_3_3_score_by_occupation_group.png",
    )
    plot_state_high(
        frame,
        figure_dir / "figure_3_4_state_high_exposure.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.5"],
        group_summary(frame, "sexo_texto", SEX_ORDER),
        figure_dir / "figure_3_5_sex.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.6"],
        group_summary(frame, "raca_agregada", RACE_ORDER),
        figure_dir / "figure_3_6_race.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.7"],
        group_summary(frame, "faixa_etaria", AGE_ORDER),
        figure_dir / "figure_3_7_age.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.8"],
        group_summary(
            frame,
            "nivel_instrucao",
            list(EDUCATION_LABELS_PT),
            category_labels=EDUCATION_LABELS_PT,
        ),
        figure_dir / "figure_3_8_education.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.9"],
        group_summary(
            frame[frame["tem_renda"].eq(1)],
            "faixa_renda_sm",
            INCOME_ORDER,
        ),
        figure_dir / "figure_3_9_income.png",
    )
    plot_demographic_dimension(
        FIGURE_TITLES_PT["3.10"],
        group_summary(
            frame,
            "formal",
            [1, 0],
            category_labels=FORMAL_LABELS_PT,
        ),
        figure_dir / "figure_3_10_formality.png",
    )
    return sorted(figure_dir.glob("*.png"))
