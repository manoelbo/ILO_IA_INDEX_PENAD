"""Build and render the 18 numbered Phase 8B dissertation tables."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

RENDER_DIR = Path(__file__).resolve().parent
MODELS_DIR = RENDER_DIR.parent / "models"
COMMON_DIR = RENDER_DIR.parent / "common"
for _directory in (RENDER_DIR, MODELS_DIR, COMMON_DIR):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from merge_audit import audited_merge
from phase8b_common import (
    OUTCOME_LABELS,
    PACKAGE_ROOT,
    PACKAGE_ROOT,
    RESULTS_DIR,
    TABLES_DIR,
    atomic_csv,
    atomic_text,
    format_integer,
    format_number,
    format_p_value,
    interpretation_counts,
    mandatory_interpretation_note,
    markdown_table,
    save_table_pair,
    significance_stars,
)


OUTCOME_ORDER = (
    "admissoes",
    "desligamentos",
    "n_movimentacoes",
    "ln_salario_real_adm",
    "asinh_saldo",
)
MAIN_OUTCOME_ORDER = (
    "admissoes",
    "desligamentos",
    "ln_salario_real_adm",
    "asinh_saldo",
)
GROUP_LABELS_PT = {
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
MAIN_TABLE_SPECS = {
    "5.2.1": {
        "slug": "sex",
        "dimension": "sex",
        "groups": ("men", "women"),
        "title": "Tabela 5.2.1 — Resultados por sexo",
    },
    "5.2.2": {
        "slug": "race",
        "dimensions": ("race_color", "race_aggregate"),
        "groups": ("race_white", "race_negra"),
        "title": "Tabela 5.2.2 — Resultados por raça/cor",
    },
    "5.2.3": {
        "slug": "age",
        "dimension": "age_pnad",
        "groups": (
            "age_18_24",
            "age_25_34",
            "age_35_44",
            "age_45_54",
            "age_55_65",
        ),
        "title": "Tabela 5.2.3 — Resultados por faixa etária PNAD/IBGE",
    },
    "5.2.4": {
        "slug": "education",
        "dimension": "education",
        "groups": (
            "fundamental_or_less",
            "high_school",
            "higher_education",
        ),
        "title": "Tabela 5.2.4 — Resultados por escolaridade",
    },
    "5.2.5": {
        "slug": "income",
        "dimension": "income",
        "groups": ("low_income", "middle_income", "high_income"),
        "title": "Tabela 5.2.5 — Resultados por renda ocupacional",
    },
}


def _ordered(
    frame: pd.DataFrame,
    groups: tuple[str, ...],
) -> pd.DataFrame:
    data = frame.copy()
    data["_group_order"] = pd.Categorical(
        data["group_id"],
        categories=list(groups),
        ordered=True,
    )
    data["_outcome_order"] = pd.Categorical(
        data["outcome"],
        categories=list(OUTCOME_ORDER),
        ordered=True,
    )
    return (
        data.sort_values(["_group_order", "_outcome_order"])
        .drop(columns=["_group_order", "_outcome_order"])
        .reset_index(drop=True)
    )


def build_main_group_table(
    family_c: pd.DataFrame,
    diagnostics: pd.DataFrame,
    *,
    dimension: str | tuple[str, ...],
    groups: tuple[str, ...],
) -> pd.DataFrame:
    dimensions = (dimension,) if isinstance(dimension, str) else dimension
    selected = family_c.loc[
        family_c["dimension"].isin(dimensions)
        & family_c["group_id"].isin(groups)
        & family_c["outcome"].isin(MAIN_OUTCOME_ORDER)
    ].copy()
    diagnostic_columns = diagnostics[
        [
            "dimension",
            "group_id",
            "outcome",
            "group_pretrend_pretrend_status",
            "group_pretrend_error",
        ]
    ].rename(
        columns={
            "group_pretrend_pretrend_status": (
                "diagnostic_group_pretrend"
            ),
            "group_pretrend_error": "pretrend_reason",
        }
    )
    selected = audited_merge(
        selected,
        diagnostic_columns,
        merge_id="phase8b_main_table_attach_pretrend_reason",
        on=["dimension", "group_id", "outcome"],
        how="left",
        validate="one_to_one",
        reporter=None,
    )
    if len(selected) != len(groups) * len(MAIN_OUTCOME_ORDER):
        raise RuntimeError("Main group table has an incomplete result grid")
    selected["group_pretrend"] = selected[
        "diagnostic_group_pretrend"
    ]
    selected["pretrend_reason"] = selected["pretrend_reason"].fillna("")
    selected["stars"] = [
        significance_stars(value)
        for value in selected["bh_adjusted_p_value"]
    ]
    selected["star_source"] = "bh_adjusted_p_value"
    if not selected["family_id"].eq("C").all():
        raise RuntimeError("Main group tables must use Family C")
    if not selected["family_size"].eq(130).all():
        raise RuntimeError("Main group tables must declare 130 tests")
    return _ordered(selected, groups)


def _appendix_rows(
    frame: pd.DataFrame,
    *,
    dimension: str,
    groups: tuple[str, ...],
    family_id: str,
    family_size: int,
    panel_label: str,
) -> pd.DataFrame:
    selected = frame.loc[
        frame["dimension"].eq(dimension)
        & frame["group_id"].isin(groups)
    ].copy()
    if len(selected) != len(groups) * len(OUTCOME_ORDER):
        raise RuntimeError(
            f"Appendix grid is incomplete for {dimension}"
        )
    selected = _ordered(selected, groups)
    treated_support = selected.get(
        "target_treated_cbo_with_flows",
        pd.Series(np.nan, index=selected.index),
    )
    control_support = selected.get(
        "target_control_cbo_with_flows",
        pd.Series(np.nan, index=selected.index),
    )
    result = pd.DataFrame(
        {
            "panel_family_group": (
                panel_label
                + " · Família "
                + family_id
                + f" ({family_size}) · "
                + selected["group_id"]
                .map(GROUP_LABELS_PT)
                .fillna(selected["group_label"])
                .astype(str)
            ),
            "outcome": selected["outcome"].map(OUTCOME_LABELS),
            "ddd_estimate_se": [
                f"{format_number(coefficient)} "
                f"({format_number(standard_error)})"
                for coefficient, standard_error in zip(
                    selected["ddd_coefficient"],
                    selected["ddd_standard_error"],
                    strict=True,
                )
            ],
            "nominal_p_value": selected["ddd_nominal_p_value"],
            "bh_adjusted_p_value": selected[
                "ddd_bh_adjusted_p_value"
            ],
            "group_pretrend": selected[
                "group_pretrend_pretrend_status"
            ],
            "ddd_pretrend": selected["ddd_pretrend_status"],
            "group_mde_80_power": selected["group_mde_80_power"],
            "n_and_cbo_support": [
                (
                    f"N={format_integer(n_obs)}; CBOs "
                    f"{format_integer(treated)}/"
                    f"{format_integer(control)}; {support_status}"
                )
                for n_obs, treated, control, support_status in zip(
                    selected["group_did_n_obs"],
                    treated_support,
                    control_support,
                    selected["support_status"],
                    strict=True,
                )
            ],
        }
    )
    return result


def build_appendix_age_table(
    family_a: pd.DataFrame,
    family_b: pd.DataFrame,
) -> pd.DataFrame:
    pnad = _appendix_rows(
        family_b,
        dimension="age_pnad",
        groups=(
            "age_18_24",
            "age_25_34",
            "age_35_44",
            "age_45_54",
            "age_55_65",
        ),
        family_id="B",
        family_size=30,
        panel_label="Painel 1 — PNAD/IBGE",
    )
    canaries = _appendix_rows(
        family_a,
        dimension="age_canaries",
        groups=(
            "age_22_25",
            "age_26_30",
            "age_31_34",
            "age_35_40",
            "age_41_49",
            "age_50_plus",
        ),
        family_id="A",
        family_size=100,
        panel_label="Painel 2 — Canaries",
    )
    return pd.concat([pnad, canaries], ignore_index=True)


def build_national_appendix(
    ladder: pd.DataFrame,
    diagnostics: pd.DataFrame,
    stock: pd.DataFrame,
) -> pd.DataFrame:
    principal = ladder.loc[
        ladder["step_id"].eq("01_no_controls")
    ].copy()
    diagnostic_columns = diagnostics[
        [
            "outcome",
            "pretrend_status",
            "joint_lead_p_value",
            "dynamic_pre_p_lt_005",
        ]
    ].rename(columns={"joint_lead_p_value": "pretrend_p_value"})
    principal = audited_merge(
        principal,
        diagnostic_columns,
        merge_id="phase8b_national_appendix_attach_pretrends",
        on=["outcome"],
        how="left",
        validate="one_to_one",
        reporter=None,
    )
    panel_b1 = pd.DataFrame(
        {
            "panel": "B.1",
            "outcome_id": principal["outcome"],
            "outcome": principal["outcome"].map(OUTCOME_LABELS),
            "coefficient": principal["coefficient"],
            "standard_error": principal["standard_error"],
            "p_value": principal["p_value"],
            "pretrend_status": principal["pretrend_status"],
            "pretrend_p_value": principal["pretrend_p_value"],
            "n_obs": principal["n_obs"],
            "n_clusters": principal["minimum_clusters"],
            "interpretation": (
                "principal national estimate; all available pretrends fail"
            ),
        }
    )
    proxy = stock.iloc[0]
    panel_b2 = pd.DataFrame(
        [
            {
                "panel": "B.2",
                "outcome_id": "stock_proxy_index",
                "outcome": "Proxy cumulativo de fluxo líquido",
                "coefficient": proxy["coefficient"],
                "standard_error": proxy["standard_error"],
                "p_value": proxy["p_value"],
                "pretrend_status": "not_available",
                "pretrend_p_value": np.nan,
                "n_obs": proxy["n_obs"],
                "n_clusters": proxy["minimum_clusters"],
                "interpretation": (
                    "cumulative flow proxy; not employment stock"
                ),
            }
        ]
    )
    return pd.concat([panel_b1, panel_b2], ignore_index=True)


def _attach_support(
    diagnostics: pd.DataFrame,
    support: pd.DataFrame,
    *,
    merge_id: str,
) -> pd.DataFrame:
    keep = support[
        [
            "dimension",
            "group_id",
            "target_treated_cbo_with_flows",
            "target_control_cbo_with_flows",
        ]
    ]
    return audited_merge(
        diagnostics,
        keep,
        merge_id=merge_id,
        on=["dimension", "group_id"],
        how="left",
        validate="many_to_one",
        reporter=None,
    )


def build_panel_scope_table(
    panel_support: dict[str, Any],
    ladder: pd.DataFrame,
) -> pd.DataFrame:
    principal = ladder.loc[
        ladder["step_id"].eq("01_no_controls")
    ]
    main_cells = int(principal["input_cells"].max())
    main_cbos = int(principal["minimum_clusters"].max())
    rows = [
        (
            "Células CBO-mês no painel nacional observado",
            panel_support["cells"],
            "results/reconciliation/painel_nacional_support.json",
        ),
        (
            "Células CBO-mês na amostra principal completa",
            main_cells,
            "results/models/specification_ladder.csv",
        ),
        (
            "CBOs na amostra principal",
            main_cbos,
            "results/models/specification_ladder.csv",
        ),
        (
            "Meses",
            panel_support["months"],
            "results/reconciliation/painel_nacional_support.json",
        ),
        (
            "Janela",
            "2021-01 a 2026-05",
            "results/reconciliation/painel_nacional_support.json",
        ),
        (
            "CBOs tratadas / controle",
            "75 / 266",
            "results/treatment/treatment_variant_comparison.csv",
        ),
    ]
    return pd.DataFrame(rows, columns=["indicator", "value", "source"])


def build_treatment_classification_table(
    variants: pd.DataFrame,
) -> pd.DataFrame:
    data = variants.copy()
    data["analysis_role"] = np.select(
        [
            data["classification"].str.startswith("Exposed:"),
            data["classification"].eq("Not Exposed"),
        ],
        ["treated", "control"],
        default="excluded from principal contrast",
    )
    data["source"] = (
        "results/treatment/treatment_variant_comparison.csv"
    )
    return data


def build_panel_coverage_table(
    coverage: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for group, view in coverage.groupby(
        "grupo_tratamento",
        sort=False,
    ):
        rows.append(
            {
                "treatment_group": group,
                "months": int(view["competenciamov"].nunique()),
                "movement_rows": int(view["linhas_mov"].sum()),
                "late_rows": int(view["linhas_for"].sum()),
                "excluded_rows": int(view["linhas_exc"].sum()),
                "mean_late_share_pct": float(
                    view["fracao_for_sobre_mov_pct"].mean()
                ),
                "min_late_share_pct": float(
                    view["fracao_for_sobre_mov_pct"].min()
                ),
                "max_late_share_pct": float(
                    view["fracao_for_sobre_mov_pct"].max()
                ),
                "source": (
                    "results/reconciliation/"
                    "completude_por_tratamento.csv"
                ),
            }
        )
    return pd.DataFrame(rows)


def build_outcome_contract_table(
    ladder: pd.DataFrame,
) -> pd.DataFrame:
    principal = ladder.loc[
        ladder["step_id"].eq("01_no_controls")
    ].set_index("outcome")
    definitions = (
        (
            "Fluxos",
            "admissoes",
            "Número de admissões formais na CBO-mês",
            "PPML sobre a contagem em nível",
            "Semi-elasticidade; não é log-log",
        ),
        (
            "Fluxos",
            "desligamentos",
            "Número de desligamentos formais na CBO-mês",
            "PPML sobre a contagem em nível",
            "Semi-elasticidade; não é log-log",
        ),
        (
            "Fluxos",
            "n_movimentacoes",
            "Admissões mais desligamentos na CBO-mês",
            "PPML sobre a contagem em nível",
            "Semi-elasticidade; não é log-log",
        ),
        (
            "Salários",
            "ln_salario_real_adm",
            "Salário médio de admissão deflacionado pelo IPCA",
            "Log; OLS",
            "Diferença aproximada em proporção",
        ),
        (
            "Saldo",
            "asinh_saldo",
            "Admissões menos desligamentos na CBO-mês",
            "asinh; OLS",
            "Não interpretar como percentual",
        ),
    )
    rows = []
    for group, outcome, definition, transformation, interpretation in definitions:
        estimator = str(principal.loc[outcome, "estimator"])
        rows.append(
            {
                "group": group,
                "outcome_id": outcome,
                "outcome": OUTCOME_LABELS[outcome],
                "definition": definition,
                "transformation_and_estimator": transformation,
                "coefficient_interpretation": interpretation,
                "verified_estimator": estimator,
                "source": "results/models/specification_ladder.csv",
            }
        )
    return pd.DataFrame(rows)


def build_national_results_table(
    ladder: pd.DataFrame,
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    outcomes = (
        "admissoes",
        "desligamentos",
        "ln_salario_real_adm",
        "asinh_saldo",
    )
    principal = ladder.loc[
        ladder["step_id"].eq("01_no_controls")
        & ladder["outcome"].isin(outcomes)
    ].copy()
    principal = audited_merge(
        principal,
        diagnostics[["outcome", "pretrend_status"]],
        merge_id="phase8b_table_5_1_attach_pretrend",
        on=["outcome"],
        how="left",
        validate="one_to_one",
        reporter=None,
    )
    principal["_order"] = pd.Categorical(
        principal["outcome"],
        categories=list(outcomes),
        ordered=True,
    )
    principal = principal.sort_values("_order").drop(columns="_order")
    return principal[
        [
            "outcome",
            "estimator",
            "coefficient",
            "standard_error",
            "ci_low",
            "ci_high",
            "p_value",
            "pretrend_status",
            "n_obs",
        ]
    ].assign(source="results/models/specification_ladder.csv")


def build_sector_control_table(
    ladder: pd.DataFrame,
    sector_ladder: pd.DataFrame,
    level_comparison: pd.DataFrame,
    national_pretrends: pd.DataFrame,
    sector_pretrends: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble the frozen level-1/level-2 sector-control comparison."""
    level_1 = ladder.loc[
        ladder["step_id"].eq("01_no_controls")
        & ladder["outcome"].isin(OUTCOME_ORDER),
        [
            "outcome",
            "coefficient",
            "standard_error",
            "p_value",
            "n_obs",
            "minimum_clusters",
            "cluster_counts",
            "causal_role",
        ],
    ].rename(
        columns={
            column: f"level_1_{column}"
            for column in (
                "coefficient",
                "standard_error",
                "p_value",
                "n_obs",
                "minimum_clusters",
                "cluster_counts",
            )
        }
        | {"causal_role": "level_1_role"}
    )
    level_2 = sector_ladder.loc[
        sector_ladder["level_id"].eq("level_2"),
        [
            "outcome",
            "coefficient",
            "standard_error",
            "p_value",
            "n_obs",
            "minimum_clusters",
            "cluster_counts",
            "role",
        ],
    ].rename(
        columns={
            column: f"level_2_{column}"
            for column in (
                "coefficient",
                "standard_error",
                "p_value",
                "n_obs",
                "minimum_clusters",
                "cluster_counts",
            )
        }
        | {"role": "level_2_role"}
    )
    two_way = sector_ladder.loc[
        sector_ladder["level_id"].eq("level_2_two_way"),
        [
            "outcome",
            "coefficient",
            "standard_error",
            "p_value",
            "n_obs",
            "minimum_clusters",
            "cluster_counts",
            "role",
        ],
    ].rename(
        columns={
            column: f"two_way_{column}"
            for column in (
                "coefficient",
                "standard_error",
                "p_value",
                "n_obs",
                "minimum_clusters",
                "cluster_counts",
                "role",
            )
        }
    )
    national_diagnostics = national_pretrends[
        ["outcome", "pretrend_status", "joint_lead_p_value"]
    ].rename(
        columns={
            "pretrend_status": "level_1_pretrend_status",
            "joint_lead_p_value": "level_1_pretrend_joint_p_value",
        }
    )
    sector_diagnostics = sector_pretrends.loc[
        sector_pretrends["specification_id"].eq("level_2"),
        ["outcome", "pretrend_status", "joint_lead_p_value"],
    ].rename(
        columns={
            "pretrend_status": "level_2_pretrend_status",
            "joint_lead_p_value": "level_2_pretrend_joint_p_value",
        }
    )
    two_way_diagnostics = sector_pretrends.loc[
        sector_pretrends["specification_id"].eq("level_2_two_way"),
        [
            "outcome",
            "pretrend_status",
            "joint_lead_p_value",
            "lead_covariance_positive_semidefinite",
        ],
    ].rename(
        columns={
            "pretrend_status": "two_way_pretrend_status",
            "joint_lead_p_value": "two_way_pretrend_joint_p_value",
            "lead_covariance_positive_semidefinite": (
                "two_way_lead_covariance_positive_semidefinite"
            ),
        }
    )
    comparison = level_comparison[
        ["outcome", "coefficient_delta_level_2_minus_level_1"]
    ]

    result = level_1
    for index, addition in enumerate(
        (
            level_2,
            comparison,
            national_diagnostics,
            sector_diagnostics,
            two_way,
            two_way_diagnostics,
        ),
        start=1,
    ):
        result = audited_merge(
            result,
            addition,
            merge_id=f"phase8b_sector_control_source_{index}",
            on=["outcome"],
            how="left",
            validate="one_to_one",
            reporter=None,
        )

    if len(result) != len(OUTCOME_ORDER):
        raise RuntimeError("Sector-control table must contain five outcomes")
    if not result["level_1_role"].eq("principal").all():
        raise RuntimeError("Level 1 must remain principal")
    if not result["level_2_role"].eq("co_principal_sector").all():
        raise RuntimeError("Level 2 must remain co-principal")
    for column in (
        "level_1_pretrend_status",
        "level_2_pretrend_status",
        "two_way_pretrend_status",
    ):
        if not result[column].eq("fail").all():
            raise RuntimeError(f"All {column} values must remain fail")
    calculated_delta = (
        result["level_2_coefficient"] - result["level_1_coefficient"]
    )
    if not np.allclose(
        calculated_delta,
        result["coefficient_delta_level_2_minus_level_1"],
        rtol=0,
        atol=1e-12,
    ):
        raise RuntimeError("Level 2 minus level 1 does not reconcile")
    non_psd = set(
        result.loc[
            ~result[
                "two_way_lead_covariance_positive_semidefinite"
            ].astype(bool),
            "outcome",
        ]
    )
    expected_non_psd = {
        "admissoes",
        "desligamentos",
        "n_movimentacoes",
    }
    if non_psd != expected_non_psd:
        raise RuntimeError(
            "Unexpected two-way non-PSD lead-covariance outcomes"
        )
    result["two_way_pretrend_interpretation"] = np.where(
        result["two_way_lead_covariance_positive_semidefinite"],
        "fail",
        "not_interpretable_non_psd_lead_covariance",
    )
    result["level_1_source"] = (
        "results/models/specification_ladder.csv; step_id=01_no_controls"
    )
    result["level_2_source"] = (
        "results/models/sector_fixed_effect_ladder.csv; level_id=level_2"
    )
    result["difference_source"] = (
        "results/models/sector_level1_vs_level2.csv"
    )
    result["level_1_pretrend_source"] = (
        "results/diagnostics/pretrend_diagnostics.csv"
    )
    result["level_2_pretrend_source"] = (
        "results/diagnostics/pretrend_level2.csv; "
        "specification_id=level_2"
    )
    result["two_way_source"] = (
        "results/models/sector_fixed_effect_ladder.csv; "
        "level_id=level_2_two_way"
    )
    result["two_way_pretrend_source"] = (
        "results/diagnostics/pretrend_level2.csv; "
        "specification_id=level_2_two_way"
    )
    result["_order"] = pd.Categorical(
        result["outcome"],
        categories=list(OUTCOME_ORDER),
        ordered=True,
    )
    return (
        result.sort_values("_order")
        .drop(columns="_order")
        .reset_index(drop=True)
    )


def _display_main_group_table(table: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Grupo": table["group_id"]
            .map(GROUP_LABELS_PT)
            .fillna(table["group_label"]),
            "Resultado": table["outcome"].map(OUTCOME_LABELS),
            "DiD no grupo": [
                f"{format_number(coefficient)}{stars}"
                for coefficient, stars in zip(
                    table["coefficient"],
                    table["stars"],
                    strict=True,
                )
            ],
            "EP": table["standard_error"].map(format_number),
            "p BH": table["bh_adjusted_p_value"].map(format_p_value),
            "Pretrend grupo": table["group_pretrend"],
            "Motivo diagnóstico": table["pretrend_reason"].replace(
                "", "—"
            ),
            "Suporte": table["support_status"],
        }
    )


def _display_appendix(table: pd.DataFrame) -> pd.DataFrame:
    display = table.copy()
    display["nominal_p_value"] = display["nominal_p_value"].map(
        format_p_value
    )
    display["bh_adjusted_p_value"] = display[
        "bh_adjusted_p_value"
    ].map(format_p_value)
    display["group_mde_80_power"] = display[
        "group_mde_80_power"
    ].map(format_number)
    return display.rename(
        columns={
            "panel_family_group": "Painel · Família · Grupo",
            "outcome": "Resultado",
            "ddd_estimate_se": "DDD (EP)",
            "nominal_p_value": "p nominal",
            "bh_adjusted_p_value": "p BH",
            "group_pretrend": "Pretrend grupo",
            "ddd_pretrend": "Pretrend DDD",
            "group_mde_80_power": "MDE 80%",
            "n_and_cbo_support": "N · CBOs trat./controle · suporte",
        }
    )


def _appendix_caution_count(
    diagnostics: pd.DataFrame,
    *,
    dimensions: tuple[str, ...],
) -> tuple[int, int]:
    selected = diagnostics.loc[
        diagnostics["dimension"].isin(dimensions)
    ]
    caution = (
        selected["group_pretrend_pretrend_status"].isin(
            ["fail", "not_estimated"]
        )
        | selected["ddd_pretrend_status"].eq("fail")
        | selected["support_status"].eq("thin")
    )
    return int(caution.sum()), int(len(selected))


def _save_simple_table(
    audit: pd.DataFrame,
    *,
    stem: str,
    title: str,
    notes: list[str],
    display: pd.DataFrame | None = None,
) -> None:
    save_table_pair(
        audit,
        display if display is not None else audit,
        csv_path=TABLES_DIR / f"{stem}.csv",
        md_path=TABLES_DIR / f"{stem}.md",
        title=title,
        notes=notes,
    )


FOREST_COLUMNS = (
    "dimension",
    "group_id",
    "group_label",
    "outcome",
    "coefficient",
    "standard_error",
    "adjusted_ci_low",
    "adjusted_ci_high",
    "nominal_p_value",
    "bh_adjusted_p_value",
    "bh_significant_005",
    "support_status",
    "target_treated_cbo_with_flows",
    "target_control_cbo_with_flows",
    "bh_discovery_alpha",
    "adjusted_interval_method",
    "family_id",
    "family_size",
)


def build_group_outcome_forest_table(
    family_c: pd.DataFrame,
) -> pd.DataFrame:
    """Build Figure 5.2.6 backing data without reapplying multiplicity."""
    required = {
        "dimension",
        "group_id",
        "group_label",
        "outcome",
        "coefficient",
        "standard_error",
        "nominal_p_value",
        "bh_adjusted_p_value",
        "bh_significant_005",
        "cluster_df",
        "support_status",
        "target_treated_cbo_with_flows",
        "target_control_cbo_with_flows",
        "family_id",
        "family_size",
        "multiplicity_method",
    }
    missing = sorted(required - set(family_c.columns))
    if missing:
        raise RuntimeError(f"Figure 5.2.6 inputs are missing columns: {missing}")
    if len(family_c) != 130:
        raise RuntimeError("Figure 5.2.6 requires all 130 Family C positions")
    if not family_c["family_id"].eq("C").all():
        raise RuntimeError("Figure 5.2.6 may only read Family C")
    if not family_c["family_size"].eq(130).all():
        raise RuntimeError("Figure 5.2.6 must preserve Family C size 130")
    if not family_c["multiplicity_method"].eq(
        "Benjamini-Hochberg"
    ).all():
        raise RuntimeError("Figure 5.2.6 requires the frozen BH results")
    if family_c[["coefficient", "standard_error", "cluster_df"]].isna().any().any():
        raise RuntimeError("Figure 5.2.6 contains an unestimated Family C row")

    discoveries = int(family_c["bh_significant_005"].astype(bool).sum())
    discovery_alpha = 0.05 * discoveries / len(family_c)
    if not 0 < discovery_alpha < 0.05:
        raise RuntimeError("Figure 5.2.6 has no valid BH discovery cutoff")
    critical = stats.t.ppf(
        1 - discovery_alpha / 2,
        family_c["cluster_df"].astype(float),
    )
    result = family_c[
        [
            "dimension",
            "group_id",
            "group_label",
            "outcome",
            "coefficient",
            "standard_error",
            "nominal_p_value",
            "bh_adjusted_p_value",
            "bh_significant_005",
            "support_status",
            "target_treated_cbo_with_flows",
            "target_control_cbo_with_flows",
            "family_id",
            "family_size",
        ]
    ].copy()
    result["adjusted_ci_low"] = (
        result["coefficient"] - critical * result["standard_error"]
    )
    result["adjusted_ci_high"] = (
        result["coefficient"] + critical * result["standard_error"]
    )
    result["bh_discovery_alpha"] = discovery_alpha
    result["adjusted_interval_method"] = (
        "two-sided cluster-t interval at BH discovery cutoff q*k/m"
    )
    return result.loc[:, FOREST_COLUMNS]


def _render_group_outcome_forest_backing(
    table: pd.DataFrame,
) -> None:
    atomic_csv(
        table,
        RESULTS_DIR
        / "backing_data"
        / "figure_5_2_6_group_outcome_forest.csv",
    )


def _render_descriptive_tables(
    panel_scope: pd.DataFrame,
    treatment: pd.DataFrame,
    coverage: pd.DataFrame,
    outcomes: pd.DataFrame,
) -> None:
    scope_display = panel_scope.rename(
        columns={
            "indicator": "Indicador",
            "value": "Valor",
            "source": "Fonte",
        }
    )
    _save_simple_table(
        panel_scope,
        stem="table_4_2_1_panel_scope",
        title="Tabela 4.2.1 — Escopo do painel ocupação-mês",
        display=scope_display,
        notes=[
            "A amostra principal é a grade completa de 341 CBOs por 65 meses.",
            "A fonte de cada célula está declarada na última coluna.",
        ],
    )

    treatment_display = treatment.rename(
        columns={
            "variant": "Variante",
            "classification": "Classificação OIT",
            "cbo_families": "CBOs",
            "changed_vs_v_a": "Mudanças vs. V-A",
            "analysis_role": "Papel na análise",
            "source": "Fonte",
        }
    )
    _save_simple_table(
        treatment,
        stem="table_4_2_2_treatment_classification",
        title="Tabela 4.2.2 — Classificação e variantes de tratamento",
        display=treatment_display,
        notes=[
            "V-A é a classificação principal: 75 CBOs tratadas e 266 controles.",
            "V-B, V-C e V-D são variantes pré-registradas; não substituem V-A.",
        ],
    )

    coverage_display = coverage.copy()
    for column in (
        "mean_late_share_pct",
        "min_late_share_pct",
        "max_late_share_pct",
    ):
        coverage_display[column] = coverage_display[column].map(
            lambda value: format_number(value, 2)
        )
    coverage_display = coverage_display.rename(
        columns={
            "treatment_group": "Grupo",
            "months": "Meses",
            "movement_rows": "Linhas MOV",
            "late_rows": "Linhas FOR",
            "excluded_rows": "Linhas EXC",
            "mean_late_share_pct": "FOR/MOV média (%)",
            "min_late_share_pct": "FOR/MOV mín. (%)",
            "max_late_share_pct": "FOR/MOV máx. (%)",
            "source": "Fonte",
        }
    )
    _save_simple_table(
        coverage,
        stem="table_4_2_3_panel_coverage",
        title="Tabela 4.2.3 — Cobertura mensal por grupo de tratamento",
        display=coverage_display,
        notes=[
            "MOV é o fluxo revisado; FOR são declarações fora do prazo; EXC são exclusões.",
            "A fonte de cada linha é o diagnóstico de completude da V2.",
        ],
    )

    outcomes_display = outcomes.rename(
        columns={
            "group": "Grupo",
            "outcome_id": "ID",
            "outcome": "Outcome",
            "definition": "Definição",
            "transformation_and_estimator": "Transformação e estimador",
            "coefficient_interpretation": "Leitura do coeficiente",
            "verified_estimator": "Estimador verificado",
            "source": "Fonte",
        }
    )
    _save_simple_table(
        outcomes,
        stem="table_4_3_1_outcomes",
        title="Tabela 4.3.1 — Outcomes da análise",
        display=outcomes_display,
        notes=[
            "Admissões, desligamentos e fluxo bruto entram no PPML em nível.",
            "O coeficiente PPML é uma semi-elasticidade, não uma elasticidade log-log.",
        ],
    )


def _render_national_tables(
    national: pd.DataFrame,
    appendix: pd.DataFrame,
) -> None:
    national_display = pd.DataFrame(
        {
            "Resultado": national["outcome"].map(OUTCOME_LABELS),
            "Estimador": national["estimator"].str.upper(),
            "Coeficiente": national["coefficient"].map(format_number),
            "EP": national["standard_error"].map(format_number),
            "IC 95%": [
                f"[{format_number(low)}; {format_number(high)}]"
                for low, high in zip(
                    national["ci_low"],
                    national["ci_high"],
                    strict=True,
                )
            ],
            "p": national["p_value"].map(format_p_value),
            "Pretrend": national["pretrend_status"],
            "N": national["n_obs"].map(format_integer),
            "Fonte": national["source"],
        }
    )
    _save_simple_table(
        national,
        stem="table_5_1_national_results",
        title="Tabela 5.1 — Resultados médios nacionais",
        display=national_display,
        notes=[
            "Coeficientes da especificação principal 01_no_controls.",
            "Os quatro pretrends falham; as estimativas não identificam um efeito causal médio nacional.",
            "Admissões e desligamentos são semi-elasticidades PPML em nível.",
        ],
    )

    appendix_display = pd.DataFrame(
        {
            "Painel": appendix["panel"],
            "Resultado": appendix["outcome"],
            "Coeficiente": appendix["coefficient"].map(format_number),
            "EP": appendix["standard_error"].map(format_number),
            "p": appendix["p_value"].map(format_p_value),
            "Pretrend": appendix["pretrend_status"],
            "p pretrend": appendix["pretrend_p_value"].map(
                format_p_value
            ),
            "N": appendix["n_obs"].map(format_integer),
            "CBOs": appendix["n_clusters"].map(format_integer),
            "Interpretação": appendix["interpretation"].replace(
                {
                    (
                        "principal national estimate; all available "
                        "pretrends fail"
                    ): (
                        "estimativa nacional principal; todos os "
                        "pretrends disponíveis falham"
                    ),
                    "cumulative flow proxy; not employment stock": (
                        "proxy cumulativo de fluxo; não é estoque de "
                        "emprego"
                    ),
                }
            ),
        }
    )
    _save_simple_table(
        appendix,
        stem="table_a_1_national_diagnostics",
        title="Tabela A.1 — Diagnósticos nacionais e proxy cumulativo",
        display=appendix_display,
        notes=[
            "No Painel B.1, o pretrend do salário real de admissão é fail (p=1,6e-04), não pass.",
            "O Painel B.2 usa o índice cumulativo de fluxo líquido. O proxy não observa o estoque de emprego.",
            "A Tabela A.1 é a única tabela a manter um Painel B.2.",
        ],
    )


def _render_sector_control_table(
    table: pd.DataFrame,
    *,
    level_3_treated_cbos: int,
) -> None:
    def pretrend_label(
        status: str,
        p_value: float,
        marker: str = "",
    ) -> str:
        formatted = format_p_value(p_value)
        operator = "" if formatted.startswith("<") else "="
        return f"{status} (p{operator}{formatted}{marker})"

    panel_a = pd.DataFrame(
        {
            "Resultado": table["outcome"].map(OUTCOME_LABELS),
            "Nível 1 coef.": table["level_1_coefficient"].map(
                format_number
            ),
            "EP": table["level_1_standard_error"].map(format_number),
            "p": table["level_1_p_value"].map(format_p_value),
            "Nível 1 N / clusters": [
                f"{format_integer(n_obs)} / {format_integer(clusters)}"
                for n_obs, clusters in zip(
                    table["level_1_n_obs"],
                    table["level_1_minimum_clusters"],
                    strict=True,
                )
            ],
            "Pretrend nível 1": [
                pretrend_label(status, p_value)
                for status, p_value in zip(
                    table["level_1_pretrend_status"],
                    table["level_1_pretrend_joint_p_value"],
                    strict=True,
                )
            ],
            "Nível 2 coef.": table["level_2_coefficient"].map(
                format_number
            ),
            "EP ": table["level_2_standard_error"].map(format_number),
            "p ": table["level_2_p_value"].map(format_p_value),
            "Nível 2 N / clusters": [
                f"{format_integer(n_obs)} / {format_integer(clusters)}"
                for n_obs, clusters in zip(
                    table["level_2_n_obs"],
                    table["level_2_minimum_clusters"],
                    strict=True,
                )
            ],
            "Pretrend nível 2": [
                pretrend_label(status, p_value)
                for status, p_value in zip(
                    table["level_2_pretrend_status"],
                    table["level_2_pretrend_joint_p_value"],
                    strict=True,
                )
            ],
            "Diferença N2 − N1": table[
                "coefficient_delta_level_2_minus_level_1"
            ].map(format_number),
        }
    )
    two_way_pretrend: list[str] = []
    for status, p_value, positive_semidefinite in zip(
        table["two_way_pretrend_status"],
        table["two_way_pretrend_joint_p_value"],
        table["two_way_lead_covariance_positive_semidefinite"],
        strict=True,
    ):
        marker = "" if positive_semidefinite else "†"
        interpretation = (
            ""
            if positive_semidefinite
            else " — não interpretável (matriz não PSD)"
        )
        two_way_pretrend.append(
            pretrend_label(status, p_value, marker) + interpretation
        )
    panel_b = pd.DataFrame(
        {
            "Resultado": table["outcome"].map(OUTCOME_LABELS),
            "Coeficiente": table["two_way_coefficient"].map(
                format_number
            ),
            "EP": table["two_way_standard_error"].map(format_number),
            "p": table["two_way_p_value"].map(format_p_value),
            "Pretrend conjunto": two_way_pretrend,
            "Matriz dos leads PSD": np.where(
                table["two_way_lead_covariance_positive_semidefinite"],
                "sim",
                "não",
            ),
            "N": table["two_way_n_obs"].map(format_integer),
            "Clusters": "341 CBO4; 87 divisões CNAE",
        }
    )
    title = "# Tabela 5.1.1 — Controle setorial"
    mandatory_note = (
        "O nível 1 compara ocupações expostas e não expostas em toda a "
        "economia; o nível 2 compara dentro da mesma seção CNAE no mesmo "
        "mês, absorvendo choques setoriais. As duas especificações são "
        "co-principais no contrato congelado e respondem a perguntas "
        "diferentes: o nível 2 não substitui o nível 1, ele informa quanto "
        "do diferencial é entre ocupações e quanto é entre setores. Os "
        "pretrends de ambas falham nos cinco outcomes."
    )
    robustness_warning = (
        "† No painel de robustez bidirecional, a matriz de covariância dos "
        "leads não é positiva semidefinida para admissões, desligamentos e "
        "fluxo bruto. Os p-valores de pretrend 0,269 e 0,555 exibidos para "
        "admissões e desligamentos não são interpretáveis e não podem ser "
        "lidos como “passou”."
    )
    level_3_note = (
        "O nível 3 fica fora das colunas principais: é "
        f"`support_diagnostic` e retém {level_3_treated_cbos} CBOs tratadas "
        "em células coexistentes."
    )
    markdown = "\n\n".join(
        (
            title,
            "## Painel A — Especificações co-principais",
            markdown_table(panel_a),
            "## Painel B — Robustez de inferência do nível 2",
            markdown_table(panel_b),
            "\n".join(
                f"- {note}"
                for note in (
                    mandatory_note,
                    robustness_warning,
                    level_3_note,
                    (
                        "Não há estrelas. Os cinco outcomes dos níveis 1 e "
                        "2 têm pretrend `fail`; a tabela não sustenta leitura "
                        "causal."
                    ),
                )
            ),
        )
    )
    atomic_csv(
        table,
        TABLES_DIR / "table_5_1_1_sector_control.csv",
    )
    atomic_text(
        markdown + "\n",
        TABLES_DIR / "table_5_1_1_sector_control.md",
    )


def _render_main_group_tables(
    family_c: pd.DataFrame,
    diagnostics: pd.DataFrame,
    note: str,
) -> None:
    for table_id, specification in MAIN_TABLE_SPECS.items():
        dimensions = specification.get(
            "dimensions",
            specification.get("dimension"),
        )
        table = build_main_group_table(
            family_c,
            diagnostics,
            dimension=dimensions,
            groups=specification["groups"],
        )
        _save_simple_table(
            table,
            stem=f"table_{table_id.replace('.', '_')}_{specification['slug']}",
            title=specification["title"],
            display=_display_main_group_table(table),
            notes=[
                "Família C: 130 testes; estrelas calculadas exclusivamente pelo p ajustado de Benjamini-Hochberg.",
                "A coluna de pretrend acompanha cada linha; not_estimated traz o motivo verificável.",
                note,
            ],
        )


def _render_appendix_table(
    table: pd.DataFrame,
    diagnostics: pd.DataFrame,
    *,
    dimensions: tuple[str, ...],
    stem: str,
    title: str,
    family_note: str,
) -> None:
    caution, total = _appendix_caution_count(
        diagnostics,
        dimensions=dimensions,
    )
    _save_simple_table(
        table,
        stem=stem,
        title=title,
        display=_display_appendix(table),
        notes=[
            family_note,
            "p nominal e p BH aparecem lado a lado; não há Painel B.2.",
            (
                f"{caution} de {total} contrastes têm pretrend fail/"
                "not_estimated ou suporte thin e exigem cautela."
            ),
        ],
    )


def _render_appendix_tables(
    family_a: pd.DataFrame,
    family_b: pd.DataFrame,
) -> None:
    sex = _appendix_rows(
        family_a,
        dimension="sex",
        groups=("men", "women"),
        family_id="A",
        family_size=100,
        panel_label="Contrastes DDD",
    )
    _render_appendix_table(
        sex,
        family_a,
        dimensions=("sex",),
        stem="table_a_2_sex",
        title="Tabela A.2 — Contrastes DDD por sexo",
        family_note="Família A: 100 testes DDD, Benjamini-Hochberg.",
    )

    race = _appendix_rows(
        family_a,
        dimension="race_color",
        groups=(
            "race_white",
            "race_black",
            "race_pardo",
            "race_yellow",
            "race_indigenous",
            "race_unknown",
        ),
        family_id="A",
        family_size=100,
        panel_label="Seis categorias raciais",
    )
    _render_appendix_table(
        race,
        family_a,
        dimensions=("race_color",),
        stem="table_a_3_race",
        title="Tabela A.3 — Contrastes DDD por raça/cor",
        family_note="Família A: 100 testes DDD; seis categorias raciais.",
    )

    age = build_appendix_age_table(family_a, family_b)
    age_diagnostics = pd.concat(
        [
            family_a.loc[family_a["dimension"].eq("age_canaries")],
            family_b.loc[family_b["dimension"].eq("age_pnad")],
        ],
        ignore_index=True,
    )
    _render_appendix_table(
        age,
        age_diagnostics,
        dimensions=("age_canaries", "age_pnad"),
        stem="table_a_4_age",
        title="Tabela A.4 — Contrastes DDD por idade",
        family_note=(
            "Painel 1: Família B (30), faixas PNAD/IBGE. "
            "Painel 2: Família A (100), coortes Canaries."
        ),
    )

    education = _appendix_rows(
        family_a,
        dimension="education",
        groups=(
            "fundamental_or_less",
            "high_school",
            "higher_education",
        ),
        family_id="A",
        family_size=100,
        panel_label="Contrastes DDD",
    )
    _render_appendix_table(
        education,
        family_a,
        dimensions=("education",),
        stem="table_a_5_education",
        title="Tabela A.5 — Contrastes DDD por escolaridade",
        family_note="Família A: 100 testes DDD, Benjamini-Hochberg.",
    )

    income = _appendix_rows(
        family_a,
        dimension="income",
        groups=("low_income", "middle_income", "high_income"),
        family_id="A",
        family_size=100,
        panel_label="Contrastes DDD",
    )
    _render_appendix_table(
        income,
        family_a,
        dimensions=("income",),
        stem="table_a_6_income",
        title="Tabela A.6 — Contrastes DDD por renda ocupacional",
        family_note="Família A: 100 testes DDD, Benjamini-Hochberg.",
    )


def build_occupation_case_table(
    dictionary: pd.DataFrame,
    frozen_summary: pd.DataFrame,
    *,
    dictionary_sha256: str,
) -> pd.DataFrame:
    primary = dictionary.loc[dictionary["primary_included"].astype(bool)]
    case_rows: list[dict[str, Any]] = []
    for (case_id, case_label), view in primary.groupby(
        ["case_id", "case_label_pt"],
        sort=False,
    ):
        confidence = view["mapping_confidence"].value_counts().to_dict()
        case_rows.append(
            {
                "case_id": case_id,
                "case_label_pt": case_label,
                "primary_cbo6_codes": int(len(view)),
                "high_confidence_codes": int(confidence.get("high", 0)),
                "medium_confidence_codes": int(
                    confidence.get("medium", 0)
                ),
                "low_confidence_codes": int(confidence.get("low", 0)),
            }
        )
    case_stats = pd.DataFrame(case_rows)
    summary = frozen_summary.rename(
        columns={
            "Caso ocupacional": "case_label_pt",
            "CBOs (n)": "reported_cbo6_codes",
            "Confiança semântica": "semantic_confidence",
            "Benchmark em Canaries": "canaries_benchmark",
            "Composição OIT no Brasil": "ilo_composition_brazil",
            "Cobertura do escore OIT": "ilo_score_coverage",
            "Admissões pré-tratamento": "preperiod_admissions",
        }
    )
    result = audited_merge(
        case_stats,
        summary,
        merge_id="phase8b_occupation_cases_attach_exposure_summary",
        on=["case_label_pt"],
        how="left",
        validate="one_to_one",
        reporter=None,
    )
    if not result["primary_cbo6_codes"].eq(
        result["reported_cbo6_codes"]
    ).all():
        raise RuntimeError("Occupation-case code counts do not reconcile")
    result["dictionary_sha256"] = dictionary_sha256
    result["dictionary_source"] = (
        "data/derived/occupation_cases/occupation_case_dictionary.csv"
    )
    result["composition_source"] = (
        "data/derived/occupation_cases/"
        "table_c_1_occupation_case_exposure_summary.csv"
    )
    return result


def _render_occupation_case_table(table: pd.DataFrame) -> None:
    display = table[
        [
            "case_label_pt",
            "primary_cbo6_codes",
            "semantic_confidence",
            "high_confidence_codes",
            "medium_confidence_codes",
            "ilo_composition_brazil",
            "ilo_score_coverage",
            "preperiod_admissions",
        ]
    ].rename(
        columns={
            "case_label_pt": "Caso ocupacional",
            "primary_cbo6_codes": "CBOs",
            "semantic_confidence": "Confiança",
            "high_confidence_codes": "Códigos high",
            "medium_confidence_codes": "Códigos medium",
            "ilo_composition_brazil": "Composição OIT no Brasil",
            "ilo_score_coverage": "Cobertura do escore",
            "preperiod_admissions": "Admissões pré",
        }
    )
    _save_simple_table(
        table,
        stem="table_c_1_occupation_cases",
        title="Tabela C.1 — Seleção e composição dos casos ocupacionais",
        display=display,
        notes=[
            "O dicionário congelado contém 76 códigos principais; 53 pertencem a supervisores de produção.",
            "Dos 80 mapeamentos registrados, 60 têm confiança medium.",
            (
                "Dicionário: data/derived/occupation_cases/"
                "occupation_case_dictionary.csv; SHA-256 "
                f"{table['dictionary_sha256'].iloc[0]}."
            ),
            "A composição OIT interpreta os casos depois da seleção; não redefine sua exposição.",
        ],
    )


def render_all_tables() -> None:
    reconciliation = RESULTS_DIR / "reconciliation"
    treatment_dir = RESULTS_DIR / "treatment"
    models = RESULTS_DIR / "models"
    diagnostics_dir = RESULTS_DIR / "diagnostics"
    mechanisms = RESULTS_DIR / "mechanisms"

    panel_support = json.loads(
        (reconciliation / "painel_nacional_support.json").read_text(
            encoding="utf-8"
        )
    )
    variants = pd.read_csv(
        treatment_dir / "treatment_variant_comparison.csv"
    )
    coverage_source = pd.read_csv(
        reconciliation / "completude_por_tratamento.csv"
    )
    ladder = pd.read_csv(models / "specification_ladder.csv")
    sector_ladder = pd.read_csv(
        models / "sector_fixed_effect_ladder.csv"
    )
    sector_comparison = pd.read_csv(
        models / "sector_level1_vs_level2.csv"
    )
    sector_support = pd.read_csv(
        models / "01_sector_fixed_effect_support.csv"
    )
    national_diagnostics = pd.read_csv(
        diagnostics_dir / "pretrend_diagnostics.csv"
    )
    sector_diagnostics = pd.read_csv(
        diagnostics_dir / "pretrend_level2.csv"
    )
    stock = pd.read_csv(mechanisms / "stock_proxy_result.csv")
    family_c = pd.read_csv(models / "group_did_results.csv")
    family_a_results = pd.read_csv(
        diagnostics_dir / "ddd_multiplicity_results.csv"
    )
    family_a = _attach_support(
        pd.read_csv(diagnostics_dir / "ddd_pretrends.csv"),
        pd.read_csv(diagnostics_dir / "ddd_family_support.csv"),
        merge_id="phase8b_appendix_attach_family_a_support",
    )
    family_b = _attach_support(
        pd.read_csv(
            diagnostics_dir
            / "ddd_alternative_partitions_pretrends.csv"
        ),
        pd.read_csv(
            diagnostics_dir / "ddd_alternative_partitions_support.csv"
        ),
        merge_id="phase8b_appendix_attach_family_b_support",
    )
    group_diagnostics = pd.concat(
        [family_a, family_b],
        ignore_index=True,
    )

    _render_descriptive_tables(
        build_panel_scope_table(panel_support, ladder),
        build_treatment_classification_table(variants),
        build_panel_coverage_table(coverage_source),
        build_outcome_contract_table(ladder),
    )
    _render_national_tables(
        build_national_results_table(ladder, national_diagnostics),
        build_national_appendix(
            ladder,
            national_diagnostics,
            stock,
        ),
    )
    level_3_support = sector_support.loc[
        sector_support["level_id"].eq("level_3"),
        "treated_cbos_in_coexisting_cells",
    ]
    if len(level_3_support) != 1:
        raise RuntimeError("Level 3 support must be uniquely declared")
    _render_sector_control_table(
        build_sector_control_table(
            ladder,
            sector_ladder,
            sector_comparison,
            national_diagnostics,
            sector_diagnostics,
        ),
        level_3_treated_cbos=int(level_3_support.iloc[0]),
    )
    counts = interpretation_counts(
        family_c,
        family_a_results,
        ladder,
    )
    _render_main_group_tables(
        family_c,
        group_diagnostics,
        mandatory_interpretation_note(counts),
    )
    _render_appendix_tables(family_a, family_b)
    _render_group_outcome_forest_backing(
        build_group_outcome_forest_table(family_c),
    )

    case_support = json.loads(
        (
            mechanisms / "occupation_case_panel_support.json"
        ).read_text(encoding="utf-8")
    )
    dictionary = pd.read_csv(
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "occupation_cases"
        / "occupation_case_dictionary.csv"
    )
    frozen_summary = pd.read_csv(
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "occupation_cases"
        / "table_c_1_occupation_case_exposure_summary.csv"
    )
    occupation_cases = build_occupation_case_table(
        dictionary,
        frozen_summary,
        dictionary_sha256=case_support["dictionary_sha256"],
    )
    _render_occupation_case_table(occupation_cases)


if __name__ == "__main__":
    render_all_tables()
