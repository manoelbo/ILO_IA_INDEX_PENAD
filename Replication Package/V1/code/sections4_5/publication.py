"""Render publication views from compact numeric backing data."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from .contracts import FIGURE_SPECS, TABLE_SPECS


PRIMARY_OUTCOMES = (
    "ln_admissoes",
    "ln_desligamentos",
    "ln_salario_real_adm",
    "asinh_saldo",
)
BALANCE_OUTCOMES = ("saldo_per_pre_adm", "saldo_flow_rate")


def render_tables(data_root: Path, output_dir: Path) -> list[Path]:
    """Build the 23 publication tables from full-precision backing CSVs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_by_id = _build_publication_rows(data_root)
    expected_ids = {spec.artifact_id for spec in TABLE_SPECS}
    if set(rows_by_id) != expected_ids:
        raise RuntimeError(
            "Publication-table builders differ from the artifact contract; "
            f"missing={sorted(expected_ids - set(rows_by_id))}, "
            f"extra={sorted(set(rows_by_id) - expected_ids)}"
        )
    written: list[Path] = []
    for spec in TABLE_SPECS:
        rows = rows_by_id[spec.artifact_id]
        if len(rows) < 2 or not rows[0]:
            raise ValueError(
                f"Publication table is empty or malformed: {spec.artifact_id}"
            )
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError(
                f"Publication table has irregular rows: {spec.artifact_id}"
            )

        csv_path = output_dir / f"{spec.artifact_id}.csv"
        md_path = output_dir / f"{spec.artifact_id}.md"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerows(rows)
        md_path.write_text(
            _markdown_table(spec.title, rows[0], rows[1:]),
            encoding="utf-8",
        )
        written.extend([csv_path, md_path])
    return written


def render_figures(
    data_root: Path,
    output_dir: Path,
    author_scripts: Path,
) -> list[Path]:
    """Regenerate the 13 publication PNGs from long-form backing data."""
    import pandas as pd

    output_dir.mkdir(parents=True, exist_ok=True)
    author_text = str(author_scripts.resolve())
    if author_text not in sys.path:
        sys.path.insert(0, author_text)

    from section4_5_final.section5_2_age_pnad_figures import (
        plot_age_outcome_overview_figure,
    )
    from section4_5_final.section5_2_combined_figures import (
        plot_combined_figure,
        plot_national_outcomes_figure,
    )
    from section5_3_occupation_cases.figures import (
        make_age_paths_figure,
        save_figure_bundle,
    )

    backing = data_root / "backing_data"
    dynamic = backing / "section5_2_dynamic"
    coefficients = pd.read_csv(dynamic / "event_study_coefficients_long.csv")
    pretrends = pd.read_csv(dynamic / "event_study_pretrends.csv")
    paths = pd.read_csv(dynamic / "normalized_paths_long.csv")
    written: list[Path] = [
        plot_national_outcomes_figure(
            coefficients,
            pretrends,
            paths,
            output_dir
            / "figure_s5_2_national_main_outcomes_event_study_paths.png",
        )
    ]
    for dimension, stem in (
        ("sex", "sex"),
        ("education", "education"),
        ("income", "income"),
    ):
        for outcome, outcome_stem in (
            ("ln_admissoes", "admissions"),
            ("ln_salario_real_adm", "real_admission_wage"),
        ):
            legacy_path = plot_combined_figure(
                coefficients,
                pretrends,
                paths,
                dimension=dimension,
                outcome=outcome,
                output_path=(
                    output_dir
                    / f"figure_s5_2_{stem}_{outcome_stem}_event_study_paths.png"
                ),
            )
            _restore_legacy_export_padding(legacy_path)
            written.append(legacy_path)

    race_coefficients = pd.read_csv(
        dynamic / "race_color_b_event_study_coefficients_long.csv"
    )
    race_pretrends = pd.read_csv(
        dynamic / "race_color_b_event_study_pretrends.csv"
    )
    race_paths = pd.read_csv(
        dynamic / "race_color_b_normalized_paths_long.csv"
    )
    for outcome, outcome_stem in (
        ("ln_admissoes", "admissions"),
        ("ln_salario_real_adm", "real_admission_wage"),
    ):
        written.append(
            plot_combined_figure(
                race_coefficients,
                race_pretrends,
                race_paths,
                dimension="race_color_b",
                outcome=outcome,
                output_path=(
                    output_dir
                    / "figure_s5_2_race_color_b_"
                    f"{outcome_stem}_event_study_paths.png"
                ),
            )
        )

    age = backing / "section5_2_age_pnad"
    age_coefficients = pd.read_csv(age / "event_study_coefficients_long.csv")
    age_pretrends = pd.read_csv(age / "event_study_pretrends.csv")
    age_paths = pd.read_csv(age / "normalized_paths_long.csv")
    for outcome, filename in (
        (
            "ln_admissoes",
            "figure_s5_2_age_pnad_all_age_groups_admissions_event_study_paths.png",
        ),
        (
            "ln_salario_real_adm",
            "figure_s5_2_age_pnad_all_age_groups_real_admission_wage_event_study_paths.png",
        ),
    ):
        written.append(
            plot_age_outcome_overview_figure(
                age_coefficients,
                age_pretrends,
                age_paths,
                outcome=outcome,
                output_path=output_dir / filename,
            )
        )

    occupation = pd.read_csv(
        backing
        / "section5_3_occupation_cases"
        / "occupation_case_monthly_paths.csv"
    )
    for outcome, stem in (
        ("admissions", "figure_5_3_1_occupation_cases_admissions_by_age"),
        (
            "real_admission_wage",
            "figure_5_3_2_occupation_cases_real_admission_wage_by_age",
        ),
    ):
        bundle = save_figure_bundle(
            make_age_paths_figure(occupation, outcome),
            output_dir,
            stem,
        )
        written.append(next(path for path in bundle if path.suffix == ".png"))
        for path in bundle:
            if path.suffix != ".png":
                path.unlink()

    expected_names = {spec.canonical_name for spec in FIGURE_SPECS}
    observed_names = {path.name for path in written}
    if observed_names != expected_names:
        raise RuntimeError(
            "Rendered figure set differs from the artifact contract; "
            f"missing={sorted(expected_names - observed_names)}, "
            f"extra={sorted(observed_names - expected_names)}"
        )
    return sorted(written)


def _restore_legacy_export_padding(path: Path) -> None:
    """Restore the 3 px top/bottom padding used by the July 2026 exports."""
    from PIL import Image, ImageOps

    with Image.open(path) as image:
        padded = ImageOps.expand(image.convert("RGBA"), border=(0, 3), fill="white")
        padded.save(path)


def _build_publication_rows(data_root: Path) -> dict[str, list[list[str]]]:
    import pandas as pd

    curated = data_root / "backing_data" / "curated_tables"
    read = lambda name: pd.read_csv(curated / name)
    read_text = lambda name: pd.read_csv(
        curated / name,
        dtype=str,
        keep_default_na=False,
    )

    panel_scope = read_text("table_4_2a_panel_descriptive_summary.csv")
    classification = read_text("table_4_2b_ilo_cbo_classification.csv")
    coverage = read_text("table_4_2c_crosswalk_coverage.csv")
    national = read("table_5_2_1_national_main_results.csv")
    sex = read("table_5_2_2_heterogeneity_sex.csv")
    income = read("table_5_2_3_heterogeneity_income.csv")
    age = read("table_5_2_4_b.csv")
    canaries = read("table_5_2_4_heterogeneity_age_canaries.csv")
    race = read("table_5_2_5_b.csv")
    education = read("table_5_2_6_heterogeneity_education.csv")
    occupation = read_text(
        "table_5_3_1_occupation_case_exposure_summary.csv"
    )

    return {
        "table_4_2_1_panel_scope": [
            ["Indicador", "Valor"],
            *panel_scope[["Indicador", "Valor"]].values.tolist(),
        ],
        "table_4_2_2_ilo_cbo_classification": [
            classification.columns.tolist(),
            *classification.values.tolist(),
        ],
        "table_4_2_3_crosswalk_coverage": [
            coverage.columns.tolist(),
            *coverage.values.tolist(),
        ],
        "table_4_2_outcomes": [
            ["Grupo", "Outcome", "Definição", "Transformação"],
            [
                "Fluxos",
                "Admissões",
                "Número de admissões formais na ocupação-mês",
                "lo g ( y + 1 ) ; Poisson na robustez",
            ],
            [
                "Fluxos",
                "Desligamentos",
                "Número de desligamentos formais na ocupação-mês",
                "lo g ( y + 1 ) ; Poisson na robustez",
            ],
            [
                "Salários",
                "Salário real de admissão",
                "Salário médio de admissão deflacionado pelo IPCA",
                "lo g",
            ],
            [
                "Saldo",
                "Saldo líquido",
                "Admissões menos desligamentos na ocupação-mês",
                "asinh ( saldo )",
            ],
        ],
        "table_5_1_national_results": _national_panel_rows(national),
        "table_5_2_1_sex": _heterogeneity_panel_rows(sex, "Grupo"),
        "table_5_2_2_race_color": _heterogeneity_panel_rows(
            race,
            "Grupo",
            compact_star=True,
        ),
        "table_5_2_3_age_pnad": _heterogeneity_panel_rows(
            age,
            "Faixa etária",
            label_overrides={"55+": "55–65"},
        ),
        "table_5_2_4_education": _heterogeneity_panel_rows(
            education,
            "Grupo",
        ),
        "table_5_2_5_income": _heterogeneity_panel_rows(
            income,
            "Faixa de renda",
        ),
        "table_5_3_1_occupation_cases": _occupation_rows(occupation),
        "table_a_1_national_main_diagnostics": _national_diagnostics(
            national,
            PRIMARY_OUTCOMES,
        ),
        "table_a_1_national_net_flow_diagnostics": _national_diagnostics(
            national,
            BALANCE_OUTCOMES,
        ),
        "table_a_2_sex_main_diagnostics": _heterogeneity_diagnostics(
            sex,
            PRIMARY_OUTCOMES,
        ),
        "table_a_2_sex_net_flow_diagnostics": _heterogeneity_diagnostics(
            sex,
            BALANCE_OUTCOMES,
        ),
        "table_a_3_race_color_diagnostics": _heterogeneity_diagnostics(
            race,
            PRIMARY_OUTCOMES,
        ),
        "table_a_4_age_pnad_main_diagnostics": _heterogeneity_diagnostics(
            age,
            PRIMARY_OUTCOMES,
        ),
        "table_a_4_age_pnad_net_flow_diagnostics": (
            _heterogeneity_diagnostics(age, BALANCE_OUTCOMES)
        ),
        "table_a_4_canaries_age_main_diagnostics": (
            _heterogeneity_diagnostics(canaries, PRIMARY_OUTCOMES)
        ),
        "table_a_4_canaries_age_net_flow_diagnostics": (
            _heterogeneity_diagnostics(canaries, BALANCE_OUTCOMES)
        ),
        "table_a_5_education_diagnostics": _education_diagnostics(education),
        "table_a_6_income_main_diagnostics": _heterogeneity_diagnostics(
            education,
            PRIMARY_OUTCOMES,
        ),
        "table_a_6_income_net_flow_diagnostics": (
            _heterogeneity_diagnostics(education, BALANCE_OUTCOMES)
        ),
    }


def _national_panel_rows(data) -> list[list[str]]:
    selected = data[data["outcome"].isin(PRIMARY_OUTCOMES[:3])]
    row = ["Nacional"]
    for outcome in PRIMARY_OUTCOMES[:3]:
        value = selected[selected["outcome"].eq(outcome)].iloc[0]
        row.append(
            _estimate(
                value["coef"],
                value["se"],
                value.get("stars", ""),
            )
        )
    return [
        [
            "Amostra",
            "Admissões (log)",
            "Desligamentos (log)",
            "Salário real de admissão (log)",
        ],
        row,
    ]


def _heterogeneity_panel_rows(
    data,
    first_column: str,
    *,
    compact_star: bool = False,
    label_overrides: dict[str, str] | None = None,
) -> list[list[str]]:
    rows = [
        [
            first_column,
            "Admissões (log)",
            "Desligamentos (log)",
            "Salário real de admissão (log)",
            "Saldo líquido (asinh)",
        ]
    ]
    for group_label in data["group_label"].drop_duplicates():
        group = data[data["group_label"].eq(group_label)]
        row = [(label_overrides or {}).get(group_label, group_label)]
        for outcome in PRIMARY_OUTCOMES:
            value = group[group["outcome"].eq(outcome)].iloc[0]
            row.append(
                _estimate(
                    value["group_coef"],
                    value["group_se"],
                    value.get("group_stars", ""),
                    compact_star=compact_star,
                )
            )
        rows.append(row)
    return rows


def _occupation_rows(data) -> list[list[str]]:
    rows = [
        [
            "Caso ocupacional",
            "CBOs (n)",
            "Confiança semântica",
            "Referência em Canaries",
            "Composição OIT no Brasil",
            "Admissões pré-tratamento",
        ]
    ]
    for _, row in data.iterrows():
        rows.append(
            [
                row["Caso ocupacional"],
                row["CBOs (n)"],
                row["Confiança semântica"],
                row["Benchmark em Canaries"],
                _published_composition_order(
                    row["Composição OIT no Brasil"]
                ),
                _fmt_number(row["Admissões pré-tratamento"], 0),
            ]
        )
    return rows


def _published_composition_order(value: str) -> str:
    parts = [part.strip() for part in value.split(";")]
    priority = {
        "não exposto": 0,
        "exposição mínima": 1,
        "sem escore": 2,
    }
    return "; ".join(
        sorted(
            parts,
            key=lambda part: next(
                (
                    rank
                    for prefix, rank in priority.items()
                    if part.startswith(prefix)
                ),
                -1,
            ),
        )
    )


def _national_diagnostics(data, outcomes: tuple[str, ...]) -> list[list[str]]:
    rows = [["Resultado", "DiD nacional", "p DiD", "Pretrend", "N", "CBOs"]]
    for outcome in outcomes:
        row = data[data["outcome"].eq(outcome)].iloc[0]
        rows.append(
            [
                row["outcome_label"],
                _estimate(row["coef"], row["se"], row.get("stars", ""), br=True),
                _fmt_p(row["p_value"]),
                _status_with_p(
                    row.get("pretrend_status", "not_available"),
                    row.get("pretrend_p_value"),
                ),
                _fmt_number(row["n_obs"], 0),
                _fmt_number(row["n_cbo"], 0),
            ]
        )
    return rows


def _heterogeneity_diagnostics(
    data,
    outcomes: tuple[str, ...],
) -> list[list[str]]:
    rows = [
        [
            "Grupo",
            "Resultado",
            "DDD grupo–complemento",
            "p DDD",
            "Pretrend grupo",
            "Pretrend DDD",
            "Poder grupo",
            "N grupo",
            "CBOs trat./controle",
        ]
    ]
    for group_label in data["group_label"].drop_duplicates():
        group = data[data["group_label"].eq(group_label)]
        for outcome in outcomes:
            row = group[group["outcome"].eq(outcome)].iloc[0]
            rows.append(
                [
                    group_label,
                    row["outcome_label"],
                    _estimate(
                        row["ddd_coef"],
                        row["ddd_se"],
                        row.get("ddd_stars", ""),
                        br=True,
                    ),
                    _fmt_p(row["ddd_p_value"]),
                    _status_with_p(
                        row.get("group_pretrend_status", "not_available"),
                        row.get("group_pretrend_p_value"),
                    ),
                    _status_with_p(
                        row.get("ddd_pretrend_status", "not_available"),
                        row.get("ddd_pretrend_p_value"),
                    ),
                    _clean_text(row.get("group_power_status", "not_available")),
                    _fmt_number(row["group_n_obs"], 0),
                    (
                        f"{_fmt_number(row['group_treated_cbo'], 0)}/"
                        f"{_fmt_number(row['group_control_cbo'], 0)}"
                    ),
                ]
            )
    return rows


def _education_diagnostics(data) -> list[list[str]]:
    outcome_labels = {
        "ln_admissoes": "Admissões",
        "ln_desligamentos": "Desligamentos",
        "ln_salario_real_adm": "Salário de admissão",
    }
    status_labels = {
        "pass": "Aprovado",
        "fail": "Falha",
        "warning": "Alerta",
        "not_available": "Não disponível",
    }
    support_labels = {
        "adequate": "Adequado",
        "limited": "Limitado",
        "thin": "Frágil",
        "not_available": "Não disponível",
    }
    rows = [
        [
            "Grupo",
            "Resultado",
            "DDD grupo-complemento",
            "p DDD",
            "Pretrend grupo",
            "Pretrend DDD",
            "Suporte",
            "N grupo",
            "CBOs trat./controle",
        ]
    ]
    for group_label in data["group_label"].drop_duplicates():
        group = data[data["group_label"].eq(group_label)]
        for outcome in PRIMARY_OUTCOMES[:3]:
            row = group[group["outcome"].eq(outcome)].iloc[0]
            group_status = _clean_text(row["group_pretrend_status"])
            ddd_status = _clean_text(row["ddd_pretrend_status"])
            p_ddd = _fmt_p(row["ddd_p_value"]).replace("<", "&lt;")
            rows.append(
                [
                    group_label,
                    outcome_labels[outcome],
                    _estimate(
                        row["ddd_coef"],
                        row["ddd_se"],
                        row.get("ddd_stars", ""),
                    ),
                    p_ddd,
                    (
                        f"{status_labels.get(group_status, group_status)} "
                        f"(p={_fmt_p(row['group_pretrend_p_value'])})"
                    ),
                    (
                        f"{status_labels.get(ddd_status, ddd_status)} "
                        f"(p={_fmt_p(row['ddd_pretrend_p_value'])})"
                    ),
                    support_labels.get(
                        _clean_text(row["group_power_status"]),
                        _clean_text(row["group_power_status"]),
                    ),
                    _fmt_number(row["group_n_obs"], 0),
                    (
                        f"{_fmt_number(row['group_treated_cbo'], 0)}/"
                        f"{_fmt_number(row['group_control_cbo'], 0)}"
                    ),
                ]
            )
    return rows


def _estimate(
    coef: object,
    se: object,
    stars: object,
    *,
    br: bool = False,
    compact_star: bool = False,
) -> str:
    if _is_missing(coef) or _is_missing(se):
        return "não estimável"
    star_text = _clean_text(stars)
    if br:
        separator = "<br>"
    elif compact_star and star_text:
        separator = ""
    else:
        separator = " "
    return (
        f"{_fmt_number(coef, 4)}{star_text}{separator}"
        f"({_fmt_number(se, 4)})"
    )


def _status_with_p(status: object, p_value: object) -> str:
    status_text = _clean_text(status) or "not_available"
    if _is_missing(p_value):
        return status_text
    return f"{status_text} (p={_fmt_p(p_value)})"


def _fmt_p(value: object) -> str:
    if _is_missing(value):
        return ""
    numeric = float(value)
    return "<0,001" if numeric < 0.001 else _fmt_number(numeric, 3)


def _fmt_number(value: object, digits: int) -> str:
    if _is_missing(value):
        return ""
    numeric = float(value)
    if digits == 0:
        return f"{numeric:,.0f}".replace(",", ".")
    return f"{numeric:.{digits}f}".replace(".", ",")


def _clean_text(value: object) -> str:
    return "" if _is_missing(value) else str(value)


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(math.isnan(float(value)))
    except (TypeError, ValueError):
        return False


def _markdown_table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
) -> str:
    def escaped(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(escaped(value) for value in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(escaped(value) for value in row) + " |"
        for row in rows
    ]
    return "\n".join([f"# {title}", "", header, separator, *body, ""])
