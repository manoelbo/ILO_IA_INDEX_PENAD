"""Render the 14 Phase 8B dissertation figures with Matplotlib."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

RENDER_DIR = Path(__file__).resolve().parent
MODELS_DIR = RENDER_DIR.parent / "models"
for _directory in (RENDER_DIR, MODELS_DIR):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from phase8b_common import (
    FIGURES_DIR,
    RESULTS_DIR,
    SHORT_OUTCOME_LABELS,
    format_number,
    interpretation_counts,
    short_interpretation_note,
)


COLORS = (
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
)
GROUP_CI_ALPHA = 0.035
OUTCOME_COLORS = {
    "admissoes": "#0072B2",
    "desligamentos": "#D55E00",
    "n_movimentacoes": "#009E73",
    "ln_salario_real_adm": "#CC3311",
    "asinh_saldo": "#5B5B5B",
}
GROUP_LABELS = {
    "men": "Homens",
    "women": "Mulheres",
    "race_white": "Branca",
    "race_black": "Preta",
    "race_pardo": "Parda",
    "race_yellow": "Amarela",
    "race_indigenous": "Indígena",
    "race_unknown": "Não identificada",
    "race_negra": "Negra (preta e parda)",
    "age_18_24": "18–24",
    "age_25_34": "25–34",
    "age_35_44": "35–44",
    "age_45_54": "45–54",
    "age_55_65": "55–65",
    "age_22_25": "22–25",
    "age_26_30": "26–30",
    "age_31_34": "31–34",
    "age_35_40": "35–40",
    "age_41_49": "41–49",
    "age_50_plus": "50+",
    "fundamental_or_less": "Fundamental ou menos",
    "high_school": "Médio",
    "higher_education": "Superior",
    "low_income": "Até 2 SM",
    "middle_income": "Mais de 2 a 5 SM",
    "high_income": "Mais de 5 SM",
}
DIMENSION_LABELS = {
    "sex": "Sexo",
    "race": "Raça/cor",
    "race_color": "Raça/cor",
    "race_aggregate": "Raça/cor agregada",
    "age": "Idade PNAD/IBGE",
    "age_pnad": "Idade PNAD/IBGE",
    "age_canaries": "Idade Canaries",
    "education": "Escolaridade",
    "income": "Renda ocupacional",
}
CASE_LABELS = {
    "software_developers": "Desenvolvedores\nde software",
    "customer_service": "Atendimento\nao cliente",
    "marketing_sales_managers": "Gerentes de marketing\ne vendas",
    "production_supervisors": "Supervisores\nde produção",
    "stock_clerks": "Estoquistas\ne repositores",
    "health_care_aides": "Auxiliares de saúde\ne cuidado",
}
AGE_LABELS = {
    "age_22_25": "22–25",
    "age_26_30": "26–30",
    "age_31_34": "31–34",
    "age_35_40": "35–40",
    "age_41_49": "41–49",
    "age_50_plus": "50+",
}
def format_decimal_tick(value: float, _position: float | None = None) -> str:
    """Format numeric figure ticks with the Portuguese decimal comma."""
    return f"{value:g}".replace("-", "−").replace(".", ",")


DECIMAL_TICK_FORMATTER = FuncFormatter(format_decimal_tick)


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.20,
            "grid.linewidth": 0.6,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def _save_figure(fig: matplotlib.figure.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        metadata={"Creator": "Replication Package V2 Phase 8B"},
    )
    plt.close(fig)


def _event_markers(ax: matplotlib.axes.Axes) -> None:
    ax.axhline(0, color="#222222", linewidth=0.8, zorder=0)
    ax.axvline(
        -1,
        color="#333333",
        linestyle="--",
        linewidth=1.0,
        zorder=1,
    )
    ax.axvline(
        23,
        color="#777777",
        linestyle=":",
        linewidth=1.2,
        zorder=1,
    )
    top = ax.get_ylim()[1]
    ax.text(
        -1,
        top,
        "nov/2022",
        ha="right",
        va="top",
        fontsize=7,
        color="#333333",
    )
    ax.text(
        23,
        top,
        "limite +23",
        ha="right",
        va="top",
        fontsize=7,
        color="#666666",
    )


def plot_national_event_studies(
    coefficients: pd.DataFrame,
    path: Path,
) -> None:
    _setup_style()
    outcomes = (
        "admissoes",
        "desligamentos",
        "ln_salario_real_adm",
        "asinh_saldo",
    )
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12.0, 7.5),
        constrained_layout=True,
    )
    for ax, outcome in zip(axes.flat, outcomes, strict=True):
        view = coefficients.loc[
            coefficients["outcome"].eq(outcome)
        ].sort_values("event_time")
        color = OUTCOME_COLORS[outcome]
        ax.fill_between(
            view["event_time"],
            view["ci_low"],
            view["ci_high"],
            color=color,
            alpha=0.15,
            linewidth=0,
        )
        ax.plot(
            view["event_time"],
            view["coefficient"],
            color=color,
            marker="o",
            markersize=2.5,
            linewidth=1.4,
        )
        pre_mean = float(view["pre_coefficient_mean"].iloc[0])
        ax.axhline(
            pre_mean,
            color=color,
            linestyle="--",
            linewidth=1.2,
            label=f"Média pré ({format_number(pre_mean, digits=3)})",
        )
        ax.set_title(SHORT_OUTCOME_LABELS[outcome], loc="left")
        ax.set_xlim(-23.5, 41.5)
        ax.set_xticks([-23, -12, -1, 12, 23, 41])
        ax.set_xlabel("Meses relativos ao lançamento do ChatGPT")
        ax.set_ylabel("Coeficiente")
        ax.yaxis.set_major_formatter(DECIMAL_TICK_FORMATTER)
        _event_markers(ax)
        ax.legend(loc="best", frameon=False)
    fig.suptitle(
        "Figura 5.1 — Event studies nacionais por outcome",
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.5,
        -0.02,
        (
            "Estimando da figura: diferença relativa a novembro de 2022. "
            "A Tabela 5.1 compara o pós à média do pré-período; a linha "
            "tracejada mostra essa média. A linha pontilhada marca +23."
        ),
        ha="center",
        va="top",
        fontsize=8,
    )
    _save_figure(fig, path)


def plot_group_event_study(
    coefficients: pd.DataFrame,
    *,
    figure_id: str,
    dimension: str,
    outcome: str,
    path: Path,
) -> None:
    _setup_style()
    data = coefficients.loc[
        coefficients["dimension"].eq(dimension)
        & coefficients["outcome"].eq(outcome)
    ].copy()
    groups = data["group_id"].drop_duplicates().tolist()
    fig, ax = plt.subplots(
        figsize=(10.0, 6.4),
    )
    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        top=0.90,
        bottom=0.29,
    )
    for index, group_id in enumerate(groups):
        view = data.loc[data["group_id"].eq(group_id)].sort_values(
            "event_time"
        )
        color = COLORS[index % len(COLORS)]
        label = GROUP_LABELS.get(group_id, str(view["group_label"].iloc[0]))
        ax.fill_between(
            view["event_time"],
            view["ci_low"],
            view["ci_high"],
            color=color,
            alpha=GROUP_CI_ALPHA,
            linewidth=0,
        )
        ax.plot(
            view["event_time"],
            view["coefficient"],
            color=color,
            linewidth=1.5,
            label=label,
        )
        ax.axhline(
            float(view["pre_coefficient_mean"].iloc[0]),
            color=color,
            linestyle="--",
            linewidth=0.9,
            alpha=0.9,
        )
    ax.set_xlim(-23.5, 41.5)
    ax.set_xticks([-23, -12, -1, 12, 23, 41])
    ax.set_xlabel("Meses relativos ao lançamento do ChatGPT")
    ax.set_ylabel("Coeficiente")
    ax.yaxis.set_major_formatter(DECIMAL_TICK_FORMATTER)
    _event_markers(ax)
    ax.set_title(
        f"Figura {figure_id} — {DIMENSION_LABELS[dimension]} — "
        f"{SHORT_OUTCOME_LABELS[outcome]}",
        loc="left",
        fontweight="bold",
    )
    group_handles, group_labels = ax.get_legend_handles_labels()
    convention_handles = [
        Line2D(
            [0],
            [0],
            color="#555555",
            linestyle="--",
            label="Média pré de cada grupo",
        ),
        Line2D(
            [0],
            [0],
            color="#333333",
            linestyle="--",
            label="Referência nov/2022",
        ),
        Line2D(
            [0],
            [0],
            color="#777777",
            linestyle=":",
            label="Fronteira da janela congelada (+23)",
        ),
    ]
    fig.legend(
        [*group_handles, *convention_handles],
        [*group_labels, *[handle.get_label() for handle in convention_handles]],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.065),
        ncol=min(4, len(groups) + 3),
        frameon=False,
    )
    fig.text(
        0.01,
        0.018,
        (
            "Nota: perfis dinâmicos relativos a novembro de 2022; "
            "os diagnósticos nacionais de tendências prévias falham."
        ),
        ha="left",
        fontsize=7.5,
    )
    _save_figure(fig, path)


def plot_case_trajectories(
    trajectories: pd.DataFrame,
    *,
    outcome: str,
    path: Path,
) -> None:
    _setup_style()
    data = trajectories.loc[
        trajectories["outcome"].eq(outcome)
    ].copy()
    data["date"] = pd.to_datetime(
        data["periodo_num"].astype(str) + "01",
        format="%Y%m%d",
    )
    case_order = data["case_id"].drop_duplicates().tolist()
    age_order = data["age_group"].drop_duplicates().tolist()
    fig, axes = plt.subplots(
        3,
        2,
        figsize=(12.0, 12.5),
        constrained_layout=True,
    )
    for ax, case_id in zip(axes.flat, case_order, strict=True):
        case = data.loc[data["case_id"].eq(case_id)]
        for index, age_group in enumerate(age_order):
            view = case.loc[case["age_group"].eq(age_group)].sort_values(
                "date"
            )
            ax.plot(
                view["date"],
                view["normalized_value"],
                color=COLORS[index],
                linewidth=1.2,
                label=AGE_LABELS[age_group],
            )
        ax.axhline(
            1,
            color="#777777",
            linestyle=":",
            linewidth=0.9,
        )
        ax.axvline(
            pd.Timestamp("2022-11-01"),
            color="#333333",
            linestyle="--",
            linewidth=1.0,
        )
        ax.set_title(
            CASE_LABELS.get(case_id, case_id),
            loc="left",
            fontweight="bold",
        )
        ax.set_ylabel("Índice (nov/2022 = 1)")
        ax.yaxis.set_major_formatter(DECIMAL_TICK_FORMATTER)
        ax.tick_params(axis="x", rotation=0)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        title="Faixa etária",
        loc="lower center",
        ncol=6,
        frameon=False,
        bbox_to_anchor=(0.5, -0.01),
    )
    title = (
        "Admissões"
        if outcome == "admissions"
        else "Salário real de admissão"
    )
    figure_id = "C.1" if outcome == "admissions" else "C.2"
    fig.suptitle(
        f"Figura {figure_id} — {title} por caso e idade",
        fontsize=15,
        fontweight="bold",
    )
    fig.text(
        0.5,
        -0.025,
        (
            "Séries descritivas normalizadas em novembro de 2022. "
            "Não há grupo de comparação específico por caso; não são "
            "exibidos intervalos de confiança."
        ),
        ha="center",
        fontsize=8,
    )
    _save_figure(fig, path)


FOREST_GROUP_ORDER = (
    ("sex", "men"),
    ("sex", "women"),
    ("age_canaries", "age_22_25"),
    ("age_canaries", "age_26_30"),
    ("age_canaries", "age_31_34"),
    ("age_canaries", "age_35_40"),
    ("age_canaries", "age_41_49"),
    ("age_canaries", "age_50_plus"),
    ("age_pnad", "age_18_24"),
    ("age_pnad", "age_25_34"),
    ("age_pnad", "age_35_44"),
    ("age_pnad", "age_45_54"),
    ("age_pnad", "age_55_65"),
    ("race_color", "race_white"),
    ("race_color", "race_black"),
    ("race_color", "race_pardo"),
    ("race_color", "race_yellow"),
    ("race_color", "race_indigenous"),
    ("race_color", "race_unknown"),
    ("race_aggregate", "race_negra"),
    ("education", "fundamental_or_less"),
    ("education", "high_school"),
    ("education", "higher_education"),
    ("income", "low_income"),
    ("income", "middle_income"),
    ("income", "high_income"),
)


def _forest_group_label(dimension: str, group_id: str) -> str:
    dimension_label = DIMENSION_LABELS.get(dimension, dimension)
    group_label = GROUP_LABELS.get(group_id, group_id)
    return f"{dimension_label} · {group_label}"


def plot_group_outcome_forest(
    forest: pd.DataFrame,
    *,
    counts: dict[str, Any],
    path: Path,
) -> None:
    """Render the manuscript's complete 130-position Family C summary."""
    _setup_style()
    outcomes = tuple(OUTCOME_COLORS)
    expected = {
        (dimension, group_id, outcome)
        for dimension, group_id in FOREST_GROUP_ORDER
        for outcome in outcomes
    }
    observed = set(
        forest[["dimension", "group_id", "outcome"]].itertuples(
            index=False, name=None
        )
    )
    if observed != expected:
        raise RuntimeError(
            "Figure 5.2.6 does not contain the exact 26 by 5 Family C grid"
        )
    if not forest["family_id"].eq("C").all() or not forest[
        "family_size"
    ].eq(130).all():
        raise RuntimeError("Figure 5.2.6 must preserve the Family C contract")

    y_positions = np.arange(len(FOREST_GROUP_ORDER))
    labels = [
        _forest_group_label(dimension, group_id)
        for dimension, group_id in FOREST_GROUP_ORDER
    ]
    fig, axes = plt.subplots(3, 2, figsize=(14.0, 18.0))
    fig.subplots_adjust(
        left=0.12,
        right=0.98,
        top=0.955,
        bottom=0.065,
        hspace=0.18,
        wspace=0.36,
    )
    keyed = forest.set_index(["dimension", "group_id", "outcome"])
    for ax, outcome in zip(axes.flat[:5], outcomes, strict=True):
        color = OUTCOME_COLORS[outcome]
        for y, (dimension, group_id) in zip(
            y_positions, FOREST_GROUP_ORDER, strict=True
        ):
            row = keyed.loc[(dimension, group_id, outcome)]
            coefficient = float(row["coefficient"])
            low = float(row["adjusted_ci_low"])
            high = float(row["adjusted_ci_high"])
            support = str(row["support_status"])
            discovery = bool(row["bh_significant_005"])
            marker = "X" if support == "thin" else "^" if support == "limited" else "o"
            marker_face = color if discovery else "white"
            marker_edge = color if discovery else "#888888"
            interval_color = color if discovery else "#B8B8B8"
            ax.errorbar(
                coefficient,
                y,
                xerr=np.array([[coefficient - low], [high - coefficient]]),
                fmt=marker,
                markersize=4.5,
                markerfacecolor=marker_face,
                markeredgecolor=marker_edge,
                markeredgewidth=0.9,
                ecolor=interval_color,
                elinewidth=1.25,
                capsize=0,
                zorder=3 if discovery else 2,
            )
        ax.axvline(0, color="#333333", linewidth=0.9, zorder=1)
        ax.set_yticks(y_positions, labels=labels)
        ax.invert_yaxis()
        ax.set_title(SHORT_OUTCOME_LABELS[outcome], loc="left", fontweight="bold")
        ax.set_xlabel("Coeficiente DiD e intervalo no limiar BH")
        ax.xaxis.set_major_formatter(DECIMAL_TICK_FORMATTER)
        ax.grid(axis="x", alpha=0.20)
        ax.grid(axis="y", alpha=0.13)

    legend_axis = axes.flat[5]
    legend_axis.axis("off")
    legend_axis.legend(
        handles=[
            Line2D(
                [0], [0], marker="o", color="none", markerfacecolor="#555555",
                markeredgecolor="#555555", label="Sobrevive ao BH"
            ),
            Line2D(
                [0], [0], marker="o", color="none", markerfacecolor="white",
                markeredgecolor="#888888", label="Não sobrevive"
            ),
            Line2D(
                [0], [0], marker="^", color="none", markerfacecolor="white",
                markeredgecolor="#888888", label="Suporte limited"
            ),
            Line2D(
                [0], [0], marker="X", color="none", markerfacecolor="white",
                markeredgecolor="#888888", label="Suporte thin"
            ),
        ],
        loc="center",
        frameon=False,
    )
    fig.suptitle(
        "Figura 5.2.6 — DiD dentro dos grupos por outcome",
        fontsize=16,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.018,
        short_interpretation_note(counts),
        ha="center",
        fontsize=8,
    )
    _save_figure(fig, path)


GROUP_FIGURE_SPECS = (
    ("5_2_1_1", "sex", "admissoes", "sex_admissions"),
    ("5_2_1_2", "sex", "ln_salario_real_adm", "sex_wage"),
    ("5_2_2_1", "race", "admissoes", "race_admissions"),
    ("5_2_2_2", "race", "ln_salario_real_adm", "race_wage"),
    ("5_2_3_1", "age", "admissoes", "age_admissions"),
    ("5_2_3_2", "age", "ln_salario_real_adm", "age_wage"),
    ("5_2_4_1", "education", "admissoes", "education_admissions"),
    ("5_2_4_2", "education", "ln_salario_real_adm", "education_wage"),
    ("5_2_5_1", "income", "admissoes", "income_admissions"),
    ("5_2_5_2", "income", "ln_salario_real_adm", "income_wage"),
)


def render_all_figures() -> None:
    models = RESULTS_DIR / "models"
    diagnostics = RESULTS_DIR / "diagnostics"
    mechanisms = RESULTS_DIR / "mechanisms"
    national = pd.read_csv(
        models / "national_event_study_extended_coefficients.csv"
    )
    group = pd.read_csv(
        models / "group_event_study_coefficients.csv"
    )
    trajectories = pd.read_csv(
        mechanisms / "occupation_case_trajectories.csv"
    )
    forest = pd.read_csv(
        RESULTS_DIR
        / "backing_data"
        / "figure_5_2_6_group_outcome_forest.csv"
    )
    family_c = pd.read_csv(models / "group_did_results.csv")
    family_a = pd.read_csv(diagnostics / "ddd_multiplicity_results.csv")
    ladder = pd.read_csv(models / "specification_ladder.csv")
    counts = interpretation_counts(family_c, family_a, ladder)
    plot_national_event_studies(
        national,
        FIGURES_DIR / "figure_5_1_national_event_studies.png",
    )
    for figure_id, dimension, outcome, slug in GROUP_FIGURE_SPECS:
        plot_group_event_study(
            group,
            figure_id=figure_id.replace("_", "."),
            dimension=dimension,
            outcome=outcome,
            path=FIGURES_DIR / f"figure_{figure_id}_{slug}.png",
        )
    plot_group_outcome_forest(
        forest,
        counts=counts,
        path=FIGURES_DIR / "figure_5_2_6_group_outcome_forest.png",
    )
    plot_case_trajectories(
        trajectories,
        outcome="admissions",
        path=FIGURES_DIR
        / "figure_c_1_occupation_cases_admissions_by_age.png",
    )
    plot_case_trajectories(
        trajectories,
        outcome="real_admission_wage",
        path=FIGURES_DIR
        / "figure_c_2_occupation_cases_wage_by_age.png",
    )


if __name__ == "__main__":
    render_all_figures()
