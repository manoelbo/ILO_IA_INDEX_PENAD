"""Final publication-style figures for Sections 4 and 5."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    CORE_OCCUPATION_GROUPS,
    CORE_OUTCOMES,
    FIGURE_DIR,
    SECTION5_3_ROOT,
)
from .formatting import fmt_number
from .style import (
    GRID,
    HIGH_RED,
    LOW_BLUE,
    MODERATE_YELLOW,
    OUTCOME_COLORS,
    TEXT_MUTED,
    get_pyplot,
    save_figure,
    setup_plot_style,
    title_axis,
)


OUTCOME_LABELS_SHORT = {
    "ln_admissoes": "Admissões",
    "ln_desligamentos": "Desligamentos",
    "ln_salario_adm": "Salário adm.",
    "ln_salario_real_adm": "Salário adm.",
    "ln_salario_desl": "Salário deslig.",
    "ln_salario_real_desl": "Salário deslig.",
    "asinh_saldo": "Saldo (asinh)",
    "saldo_per_pre_adm": "Saldo/admissões pré",
}

AGE_ORDER = ["age_22_25", "age_26_30", "age_31_34", "age_35_40", "age_41_49", "age_50_plus"]
AGE_LABELS = {
    "age_22_25": "22-25",
    "age_26_30": "26-30",
    "age_31_34": "31-34",
    "age_35_40": "35-40",
    "age_41_49": "41-49",
    "age_50_plus": "50+",
}


def _add_note(fig, text: str) -> None:
    # Place notes outside the plotting area; bbox_inches="tight" includes them on export.
    fig.text(0.01, -0.025, text, ha="left", va="bottom", fontsize=8, color=TEXT_MUTED)


def _ci(row) -> tuple[float, float]:
    coef = float(row.coef)
    se = float(row.se)
    return coef - 1.96 * se, coef + 1.96 * se


def plot_empirical_timeline(path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(11.0, 3.6), constrained_layout=True)
    ax.set_xlim(-13, 25)
    ax.set_ylim(0, 1)
    ax.axvspan(-12, -1, color=LOW_BLUE, alpha=0.14, label="Pré")
    ax.axvspan(0, 24, color=HIGH_RED, alpha=0.10, label="Pós")
    ax.axvline(-1, color="#444444", linewidth=1.2, linestyle="--")
    ax.axvline(0, color=HIGH_RED, linewidth=1.2)
    ax.plot([-12, 24], [0.46, 0.46], color="#222222", linewidth=1.2)
    ax.scatter([-1, 0], [0.46, 0.46], color=["#444444", HIGH_RED], s=55, zorder=3)
    ax.text(-1.35, 0.58, "t = -1\nreferência", ha="right", va="bottom", fontsize=9)
    ax.text(0.35, 0.58, "30/11/2022\nChatGPT", ha="left", va="bottom", fontsize=9, color=HIGH_RED)
    ax.text(-6.5, 0.24, "Janela pré-tratamento", ha="center", va="center", fontsize=10)
    ax.text(12, 0.24, "Janela pós-difusão", ha="center", va="center", fontsize=10)
    ax.set_yticks([])
    ax.set_xlabel("Meses relativos ao choque")
    title_axis(
        ax,
        "Figura 4.1: Linha do tempo da estratégia empírica",
        "Unidade principal: CBO 4 dígitos por mês; contraste: ocupações expostas vs. Not Exposed.",
    )
    ax.legend(loc="upper right", frameon=False, ncol=2)
    _add_note(fig, "Fonte: elaboração própria a partir do desenho empírico da Seção 4.")
    save_figure(fig, path)


def plot_crosswalk_pipeline(path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(11.2, 4.1), constrained_layout=True)
    ax.axis("off")
    labels = [
        "CAGED\nmicrodados",
        "CBO 2002\n4 dígitos",
        "Crosswalk\nMTE/CBO",
        "ISCO/OIT\nscore e gradiente",
        "Painel final\nCBO-mês",
    ]
    x = np.linspace(0.08, 0.92, len(labels))
    y = 0.52
    colors = [LOW_BLUE, LOW_BLUE, MODERATE_YELLOW, HIGH_RED, "#6e6e6e"]
    for i, (label, xpos, color) in enumerate(zip(labels, x, colors)):
        ax.text(
            xpos,
            y,
            label,
            ha="center",
            va="center",
            fontsize=10,
            color="#1A1A1A",
            bbox=dict(boxstyle="round,pad=0.46", facecolor="white", edgecolor=color, linewidth=1.6),
            transform=ax.transAxes,
        )
        if i < len(labels) - 1:
            ax.annotate(
                "",
                xy=(x[i + 1] - 0.075, y),
                xytext=(xpos + 0.075, y),
                xycoords=ax.transAxes,
                arrowprops=dict(arrowstyle="->", color="#555555", lw=1.1),
            )
    ax.text(
        0.5,
        0.18,
        "Regra final: CBOs sem match MTE, No score e Minimal Exposure ficam fora do modelo base.",
        ha="center",
        va="center",
        fontsize=9,
        color=TEXT_MUTED,
        transform=ax.transAxes,
    )
    title_axis(ax, "Figura 4.2: Pipeline de dados e crosswalk")
    _add_note(fig, "Fonte: CAGED, crosswalk MTE/CBO e ILO Global Index.")
    save_figure(fig, path)


def _event_panel(ax, df: pd.DataFrame, outcome: str, title: str, color: str) -> None:
    view = df[(df["outcome"].eq(outcome)) & df["coefficient_status"].isin(["estimated", "reference"])].copy()
    view = view.sort_values("t")
    ax.axhline(0, color="#222222", linewidth=0.8)
    ax.axvline(-1, color="#666666", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
    ax.plot(view["t"], view["coef"], marker="o", markersize=2.7, linewidth=1.2, color=color)
    band = view.dropna(subset=["ci_low", "ci_high"])
    if not band.empty:
        ax.fill_between(
            band["t"].astype(float),
            band["ci_low"].astype(float),
            band["ci_high"].astype(float),
            color=color,
            alpha=0.18,
        )
    ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold")
    ax.set_xlabel("Meses relativos")
    ax.set_ylabel("Coeficiente")


def plot_national_event_studies(sources: dict[str, pd.DataFrame], path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    main = sources["event_study"].copy()
    net = sources["net_flow_event_study"].copy()
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.4), constrained_layout=True)
    panels = [
        (main, "ln_admissoes", "Admissões", LOW_BLUE),
        (main, "ln_desligamentos", "Desligamentos", MODERATE_YELLOW),
        (main, "ln_salario_adm", "Salário real de admissão", HIGH_RED),
        (net, "asinh_saldo", "Saldo líquido (asinh)", "#6e6e6e"),
    ]
    for ax, (df, outcome, title, color) in zip(axes.flat, panels):
        _event_panel(ax, df, outcome, title, color)
    fig.suptitle("Figura 5.1: Event study nacional por outcome", x=0.01, ha="left", fontsize=13, fontweight="bold")
    _add_note(fig, "Nota: salário nominal e real têm a mesma leitura com efeitos fixos de mês; saldo é complementar.")
    save_figure(fig, path)


def plot_software_it_canaries(sources: dict[str, pd.DataFrame], path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    data = sources["occupation_canaries"].copy()
    data = data[
        data["group_id"].eq("software_it_core")
        & data["outcome"].eq("ln_salario_real_adm")
        & data["heterogeneity_group_id"].isin(AGE_ORDER)
    ].copy()
    data["age_order"] = data["heterogeneity_group_id"].map({age: i for i, age in enumerate(AGE_ORDER)})
    data = data.sort_values("age_order")
    fig, ax = plt.subplots(figsize=(9.8, 5.2), constrained_layout=True)
    y = np.arange(len(data))
    colors = [HIGH_RED if status == "pass" else "#999999" for status in data["pretrend_status"]]
    for i, row in enumerate(data.itertuples()):
        low, high = _ci(row)
        ax.plot([low, high], [i, i], color=colors[i], linewidth=1.8)
        ax.scatter(row.coef, i, color=colors[i], s=48, zorder=3)
        ax.text(high + 0.006, i, f"p={fmt_number(row.p_value, 3)}; pretrend {row.pretrend_status}", va="center", fontsize=8)
    ax.axvline(0, color="#222222", linewidth=0.8)
    ax.set_yticks(y, [AGE_LABELS.get(v, v) for v in data["heterogeneity_group_id"]])
    ax.invert_yaxis()
    ax.set_xlabel("Coeficiente em salário real de admissão")
    title_axis(
        ax,
        "Figura 5.2: Coortes de carreira no Núcleo de Software e TI",
        "Coeficientes por coorte, não séries normalizadas; IC de 95%.",
    )
    _add_note(fig, "Fonte: heterogeneidade por faixas etárias estilo Canaries, pacote de grupos ocupacionais.")
    save_figure(fig, path)


def plot_occupation_group_comparison(sources: dict[str, pd.DataFrame], path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    summary = sources["occupation_summary"].copy()
    summary = summary[summary["group_id"].isin(CORE_OCCUPATION_GROUPS)].copy()
    fig, ax = plt.subplots(figsize=(10.4, 5.4), constrained_layout=True)
    y = np.arange(len(summary))
    values = summary["main_real_admission_wage_coef"].astype(float)
    colors = [HIGH_RED if v < 0 else LOW_BLUE for v in values]
    ax.barh(y, values, color=colors, alpha=0.86)
    ax.axvline(0, color="#222222", linewidth=0.8)
    ax.set_yticks(y, summary["group_label"])
    ax.invert_yaxis()
    ax.set_xlabel("Coeficiente no salário real de admissão")
    title_axis(
        ax,
        "Figura 5.3: Comparação entre grupos ocupacionais",
        "Efeito médio por grupo; resultados com pretrend falho devem ser lidos como sugestivos.",
    )
    for i, row in enumerate(summary.itertuples()):
        ax.text(
            float(row.main_real_admission_wage_coef) + (-0.004 if row.main_real_admission_wage_coef < 0 else 0.004),
            i,
            f"p={fmt_number(row.main_real_admission_wage_p, 3)}; {row.main_wage_pretrend}",
            va="center",
            ha="right" if row.main_real_admission_wage_coef < 0 else "left",
            fontsize=8,
        )
    _add_note(fig, "Fonte: resumo interpretativo dos grupos ocupacionais manuais.")
    save_figure(fig, path)


def plot_group_outcome_forest(sources: dict[str, pd.DataFrame], path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    data = sources["occupation_main"].copy()
    data = data[data["group_id"].isin(CORE_OCCUPATION_GROUPS) & data["outcome"].isin(CORE_OUTCOMES)].copy()
    data["label"] = data["group_label"] + " · " + data["outcome"].map(OUTCOME_LABELS_SHORT)
    data = data.sort_values(["group_label", "outcome"])
    fig_height = max(5.5, len(data) * 0.34 + 1.5)
    fig, ax = plt.subplots(figsize=(10.8, fig_height), constrained_layout=True)
    y = np.arange(len(data))
    for i, row in enumerate(data.itertuples()):
        low, high = _ci(row)
        color = OUTCOME_COLORS.get(row.outcome, "#444444")
        ax.plot([low, high], [i, i], color=color, linewidth=1.6)
        ax.scatter(row.coef, i, color=color, s=34, zorder=3)
    ax.axvline(0, color="#222222", linewidth=0.8)
    ax.set_yticks(y, data["label"])
    ax.invert_yaxis()
    ax.set_xlabel("Coeficiente; IC de 95%")
    title_axis(ax, "Figura 5.4: Efeitos por grupo ocupacional e outcome")
    _add_note(fig, "Fonte: grupos ocupacionais manuais. Interpretar em conjunto com pretrends e poder amostral.")
    save_figure(fig, path)


def plot_heterogeneity_heatmap(sources: dict[str, pd.DataFrame], path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    data = sources["occupation_canaries"].copy()
    data = data[
        data["group_id"].isin(CORE_OCCUPATION_GROUPS)
        & data["outcome"].eq("ln_salario_real_adm")
        & data["heterogeneity_group_id"].isin(AGE_ORDER)
    ].copy()
    pivot = data.pivot_table(
        index="occupation_group_label",
        columns="heterogeneity_group_id",
        values="coef",
        aggfunc="first",
    )
    pivot = pivot.reindex(columns=AGE_ORDER)
    fig, ax = plt.subplots(figsize=(10.6, 4.9), constrained_layout=True)
    max_abs = np.nanmax(np.abs(pivot.to_numpy(dtype=float)))
    im = ax.imshow(pivot.to_numpy(dtype=float), cmap="RdBu_r", vmin=-max_abs, vmax=max_abs, aspect="auto")
    ax.set_xticks(np.arange(len(pivot.columns)), [AGE_LABELS.get(c, c) for c in pivot.columns])
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.iloc[i, j]
            if pd.notna(value):
                ax.text(j, i, fmt_number(value, 3), ha="center", va="center", fontsize=8, color="#111111")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Coeficiente")
    title_axis(
        ax,
        "Figura 5.5: Heatmap de heterogeneidade por idade",
        "Outcome: salário real de admissão; grupos ocupacionais manuais.",
    )
    _add_note(fig, "Fonte: faixas etárias estilo Canaries; células são coeficientes de interação tripla.")
    save_figure(fig, path)


def plot_connectivity_extension(sources: dict[str, pd.DataFrame], path: Path) -> None:
    plt = get_pyplot()
    setup_plot_style()
    data = sources["connectivity_main"].copy()
    pretrend = {str(r.outcome): str(r.status) for r in sources["connectivity_pretrends"].itertuples()}
    fig, ax = plt.subplots(figsize=(9.8, 4.8), constrained_layout=True)
    data = data.sort_values("outcome")
    y = np.arange(len(data))
    for i, row in enumerate(data.itertuples()):
        low, high = _ci(row)
        color = OUTCOME_COLORS.get(row.outcome, "#444444")
        ax.plot([low, high], [i, i], color=color, linewidth=1.8)
        ax.scatter(row.coef, i, color=color, s=44, zorder=3)
        ax.text(high + 0.002, i, f"p={fmt_number(row.p_value, 3)}; pretrend {pretrend.get(row.outcome, 'n/a')}", va="center", fontsize=8)
    ax.axvline(0, color="#222222", linewidth=0.8)
    ax.set_yticks(y, data["outcome"].map(OUTCOME_LABELS_SHORT))
    ax.invert_yaxis()
    ax.set_xlabel("Coeficiente DDD; IC de 95%")
    title_axis(
        ax,
        "Figura A.1: Conectividade municipal",
        "Extensão espacial; usar como evidência sugestiva por falha de pretrends.",
    )
    _add_note(fig, "Fonte: extensão de conectividade municipal, especificação forte.")
    save_figure(fig, path)


def build_all_figures(sources: dict[str, pd.DataFrame], output_dir: Path = FIGURE_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_empirical_timeline(output_dir / "figure_4_1_empirical_timeline.png")
    plot_crosswalk_pipeline(output_dir / "figure_4_2_caged_crosswalk_pipeline.png")
    plot_national_event_studies(sources, output_dir / "figure_5_1_national_event_studies.png")
    plot_connectivity_extension(sources, output_dir / "figure_a_1_connectivity_extension.png")
    for name in [
        "figure_5_3_1_occupation_cases_admissions_by_age.png",
        "figure_5_3_2_occupation_cases_real_admission_wage_by_age.png",
        "figure_b_1_occupation_cases_by_sex.png",
        "figure_b_2_occupation_cases_by_race_color.png",
        "figure_b_3_occupation_cases_by_education.png",
    ]:
        source = SECTION5_3_ROOT / "figures" / name
        if not source.exists() or source.stat().st_size == 0:
            raise FileNotFoundError(f"Required Section 5.3 figure is missing: {source}")
        shutil.copy2(source, output_dir / name)
