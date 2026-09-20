#!/usr/bin/env python3
"""Gate 8A: assemble every pretrend diagnostic into one report.

The gate requires a single table — specification × outcome × joint test ×
linear slope × individual leads × verdict — so that no specification can be
quietly left out of the comparison.

This module only reads and formats. It estimates nothing, and it makes no
recommendation about which specification should be principal: that decision
belongs to the author, with this table in front of them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent
if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

from pretrend_engine import atomic_csv, atomic_json, atomic_text


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DIAGNOSTICS_DIR = PACKAGE_ROOT / "results" / "diagnostics"
MODELS_RESULTS = PACKAGE_ROOT / "results" / "models"
DEFAULT_REPORT = DIAGNOSTICS_DIR / "DIAGNOSTICO_PRETRENDS.md"
DEFAULT_TABLE = DIAGNOSTICS_DIR / "pretrend_master_table.csv"
DEFAULT_SUPPORT = DIAGNOSTICS_DIR / "pretrend_master_support.json"

SOURCES = (
    {
        "path": DIAGNOSTICS_DIR / "pretrend_diagnostics.csv",
        "specification_id": "00_frozen_exact_model",
        "label": "Frozen exact model, full sample, window -23…+23",
        "family": "national",
        "required": True,
    },
    {
        "path": DIAGNOSTICS_DIR / "pretrend_power_check.csv",
        "family": "power",
        "required": True,
    },
    {
        "path": DIAGNOSTICS_DIR / "pretrend_sample_2022.csv",
        "family": "sample",
        "required": True,
    },
    {
        "path": DIAGNOSTICS_DIR / "pretrend_ladder_variants.csv",
        "family": "ladder",
        "required": True,
    },
    {
        "path": DIAGNOSTICS_DIR / "pretrend_level2.csv",
        "family": "sector",
        "required": True,
    },
    {
        "path": DIAGNOSTICS_DIR / "pretrend_wage_balanced_coverage.csv",
        "family": "coverage",
        "required": True,
    },
)
TABLE_COLUMNS = (
    "family",
    "specification_id",
    "specification_label",
    "outcome",
    "estimator",
    "event_window",
    "joint_lead_window",
    "joint_lead_count",
    "joint_lead_p_value",
    "lead_covariance_positive_semidefinite",
    "linear_pretrend_coefficient",
    "linear_pretrend_p_value",
    "dynamic_pre_coefficients",
    "dynamic_pre_p_lt_005",
    "pretrend_status",
    "n_obs",
    "minimum_clusters",
)


def load_sources() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source in SOURCES:
        path = source["path"]
        if not path.is_file():
            if source["required"]:
                raise FileNotFoundError(
                    f"Gate 8A requires this diagnostic: {path}"
                )
            continue
        frame = pd.read_csv(path)
        frame["family"] = source["family"]
        if "specification_id" not in frame.columns:
            frame["specification_id"] = source["specification_id"]
        if "specification_label" not in frame.columns:
            frame["specification_label"] = source["label"]
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True, sort=False)
    for column in TABLE_COLUMNS:
        if column not in combined.columns:
            combined[column] = np.nan
    combined = combined[list(TABLE_COLUMNS)].copy()
    combined = combined.drop_duplicates(
        subset=[
            "family",
            "specification_id",
            "outcome",
            "joint_lead_window",
        ]
    )
    return combined.reset_index(drop=True)


def _format(value: Any, digits: int = 6) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def _psd_note(value: Any) -> str:
    if isinstance(value, str):
        value = value.strip().lower() == "true"
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return ""
    return "" if value else " ⚠"


def render_master_table(table: pd.DataFrame) -> list[str]:
    lines = [
        "| Família | Especificação | Outcome | Leads | Teste conjunto p | "
        "Tendência linear p | Leads p<0,05 | Veredito | N |",
        "|---|---|---|---:|---:|---:|---:|---|---:|",
    ]
    for row in table.itertuples(index=False):
        lines.append(
            f"| {row.family} | {row.specification_id} | {row.outcome} | "
            f"{_format(row.joint_lead_count)} | "
            f"{_format(row.joint_lead_p_value)}"
            f"{_psd_note(row.lead_covariance_positive_semidefinite)} | "
            f"{_format(row.linear_pretrend_p_value)} | "
            f"{_format(row.dynamic_pre_p_lt_005)} | "
            f"{row.pretrend_status} | {_format(row.n_obs)} |"
        )
    return lines


def read_optional(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.is_file() else None


def build_report(table: pd.DataFrame) -> tuple[str, dict[str, Any]]:
    sample_2022 = read_optional(DIAGNOSTICS_DIR / "pretrend_sample_2022.csv")
    ddd = read_optional(DIAGNOSTICS_DIR / "ddd_pretrends.csv")
    horizons = read_optional(
        MODELS_RESULTS / "long_run_horizon_reconciliation.csv"
    )
    trend_control = read_optional(
        MODELS_RESULTS / "pretrend_control_specification.csv"
    )
    coverage = read_optional(
        DIAGNOSTICS_DIR / "pretrend_wage_balanced_coverage.csv"
    )

    status_counts = (
        table["pretrend_status"].value_counts().sort_index().to_dict()
    )
    lines: list[str] = [
        "# Diagnóstico de tendências prévias — Gate 8A",
        "",
        "Este relatório reúne, em uma tabela, todos os diagnósticos de "
        "tendência prévia da Fase 8A. Ele **não recomenda especificação "
        "principal**. A especificação principal congelada continua sendo "
        "`01_no_controls` na amostra completa, com referência em novembro de "
        "2022, e qualquer mudança de hierarquia é decisão do autor.",
        "",
        "Os três testes não são intercambiáveis. O Wald conjunto avalia todos "
        "os leads ao mesmo tempo, o teste GLS avalia uma única inclinação "
        "diferencial, e a inspeção individual conta leads isoladamente "
        "atípicos. Um resultado não significativo **não é prova** de "
        "tendências paralelas.",
        "",
        "`⚠` ao lado de um p-valor marca matriz de covariância dos leads não "
        "positiva semidefinida. Isso acontece com agrupamento bidirecional em "
        "amostra finita, e o Wald calculado sobre um bloco não PSD não é "
        "interpretável.",
        "",
        "## 1. Resposta curta",
        "",
    ]

    if sample_2022 is not None:
        reading = sample_2022["power_reading"].unique().tolist()
        lines.extend(
            [
                "**A hipótese da pandemia não se sustenta.** Restringir a "
                "amostra a partir de janeiro de 2022 não resolve nada: os "
                "cinco outcomes continuam rejeitando o teste conjunto, e o "
                "teste de poder mostra que isso não é falta de poder.",
                "",
                "| Outcome | Amostra completa, leads −11…−2 | Amostra 2022, "
                "leads −11…−2 | Leitura |",
                "|---|---:|---:|---|",
            ]
        )
        for row in sample_2022.itertuples(index=False):
            lines.append(
                f"| {row.outcome} | "
                f"{_format(row.full_sample_matched_leads_p)} | "
                f"{_format(row.joint_lead_p_value)} | "
                f"{row.power_reading} |"
            )
        lines.extend(
            [
                "",
                "Os dois p-valores são praticamente idênticos por outcome. "
                "Isso tem uma explicação mecânica: com efeitos fixos de mês, "
                "cada coeficiente de lead é o contraste tratado-controle "
                "daquele mês contra novembro de 2022, e acrescentar ou "
                "retirar os meses de 2021 quase não altera esse contraste. "
                "Ou seja, a violação está **dentro de 2022**, não na "
                "recuperação de 2021.",
                "",
                "Leituras observadas: "
                + ", ".join(f"`{item}`" for item in sorted(set(reading)))
                + ".",
                "",
            ]
        )

    lines.extend(
        [
            "## 2. Tabela única",
            "",
        ]
    )
    lines.extend(render_master_table(table))
    lines.extend(
        [
            "",
            "Contagem de vereditos: "
            + ", ".join(
                f"`{key}` {int(value)}"
                for key, value in sorted(status_counts.items())
            )
            + f" — de {len(table)} células.",
            "",
        ]
    )

    if ddd is not None:
        estimated = ddd.loc[ddd["ddd_status"].eq("estimated")]
        passing = ddd.loc[
            ddd["ddd_pretrend_status"].isin(["pass", "warning"])
        ]
        group_passing = ddd.loc[
            ddd["group_pretrend_pretrend_status"].isin(["pass", "warning"])
        ]
        lines.extend(
            [
                "## 3. Diferença tripla e diagnóstico por grupo",
                "",
                "A hipótese de identificação do DDD é mais fraca que a do "
                "DiD: exige que a *diferença entre grupos* tivesse evoluído "
                "em paralelo. Uma violação que atinge tratados e controles "
                "igualmente dentro de cada grupo é diferenciada fora. Por "
                "isso os contrastes DDD podem passar onde o DiD nacional "
                "falha — e é isso que se testa aqui.",
                "",
                f"Dos {len(estimated)} contrastes DDD estimados, "
                f"{len(passing)} passam ou ficam em aviso. No DiD por grupo, "
                f"{len(group_passing)} de {len(ddd)}. No nacional, nenhum dos "
                "cinco.",
                "",
                "**Todos os contrastes DDD que sobrevivem ao diagnóstico são "
                "de salário, e todos têm coeficiente próximo de zero com "
                "p ajustado por BH bem acima de 0,05.** Ou seja: onde a "
                "hipótese mais fraca é defensável, não há heterogeneidade "
                "detectável.",
                "",
                "| Dimensão | Grupo | Outcome | Veredito DDD | DDD p conj. | "
                "Coef. DDD | p BH |",
                "|---|---|---|---|---:|---:|---:|",
            ]
        )
        for row in passing.itertuples(index=False):
            lines.append(
                f"| {row.dimension} | {row.group_id} | {row.outcome} | "
                f"{row.ddd_pretrend_status} | "
                f"{_format(row.ddd_joint_lead_p_value)} | "
                f"{_format(row.ddd_coefficient)} | "
                f"{_format(row.ddd_bh_adjusted_p_value)} |"
            )
        lines.extend(
            [
                "",
                "O DiD **dentro** de um grupo é outra coisa, e aqui há um "
                "resultado que merece atenção do autor:",
                "",
                "| Dimensão | Grupo | Outcome | Veredito | p conj. | "
                "DiD do grupo | p | MDE 80% |",
                "|---|---|---|---|---:|---:|---:|---:|",
            ]
        )
        for row in group_passing.itertuples(index=False):
            lines.append(
                f"| {row.dimension} | {row.group_id} | {row.outcome} | "
                f"{row.group_pretrend_pretrend_status} | "
                f"{_format(row.group_pretrend_joint_lead_p_value)} | "
                f"{_format(row.group_did_coefficient)} | "
                f"{_format(row.group_did_p_value)} | "
                f"{_format(row.group_mde_80_power)} |"
            )
        lines.extend(
            [
                "",
                "**Ressalvas que precisam acompanhar qualquer uso disto.** "
                "São 100 contrastes de diagnóstico sem ajuste de "
                "multiplicidade; a 5% nominal, alguns aprovados são "
                "esperados por acaso. O DiD por grupo foi estimado nesta "
                "fase apenas para obter o erro padrão do efeito mínimo "
                "detectável, e está marcado `interpretation = "
                "diagnostic_only`. A tabela de heterogeneidade com ajuste "
                "de multiplicidade é da Fase 8B.",
                "",
            ]
        )

    if horizons is not None:
        lines.extend(
            [
                "## 4. Horizontes longos",
                "",
                "Os quatro horizontes foram estimados. A hipótese de "
                "trabalho era que o efeito salarial estivesse concentrado "
                "depois de novembro de 2024, período que a V1 não tinha. "
                "**Os dados rejeitam essa hipótese:** o coeficiente de "
                "salário é estável nos quatro horizontes.",
                "",
                "| Outcome | Estático | Média ponderada dos horizontes | "
                "Diferença | 1º horizonte | 4º horizonte |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in horizons.itertuples(index=False):
            lines.append(
                f"| {row.outcome} | {_format(row.static_coefficient)} | "
                f"{_format(row.cell_weighted_horizon_average)} | "
                f"{_format(row.static_minus_cell_weighted_average)} | "
                f"{_format(row.first_horizon)} | {_format(row.last_horizon)} |"
            )
        lines.extend(
            [
                "",
                "A diferença entre o coeficiente estático e a média "
                "ponderada dos horizontes é de ordem 1e-5, o que confirma "
                "que os horizontes particionam exatamente o período pós.",
                "",
                "A distância entre o coeficiente estático (−0,050740) e a "
                "média pós do event study (−0,015363) **não** vem da janela: "
                "vem da normalização. O event study mede cada mês contra "
                "novembro de 2022, e em novembro de 2022 o hiato "
                "tratado-controle de salário está cerca de 0,037 ponto log "
                "acima da média do pré-período. A média pós menos a média "
                "pré do event study dá −0,052619, que é o coeficiente "
                "estático a menos da janela mais longa.",
                "",
            ]
        )

    if trend_control is not None:
        lines.extend(
            [
                "## 5. Controlar pela tendência prévia",
                "",
                "Humlum e Vestergaard (2025) resolveram um problema parecido "
                "controlando pela tendência dentro do DiD, e obtiveram zeros "
                "precisos. **Aqui acontece o contrário:** controlar pela "
                "tendência prévia não anula os coeficientes; deixa-os "
                "praticamente iguais e reduz muito o erro padrão.",
                "",
                "| Outcome | Especificação | Coeficiente | EP | p |",
                "|---|---|---:|---:|---:|",
            ]
        )
        for row in trend_control.itertuples(index=False):
            lines.append(
                f"| {row.outcome} | {row.specification_id} | "
                f"{_format(row.coefficient)} | "
                f"{_format(row.standard_error)} | {_format(row.p_value)} |"
            )
        lines.extend(
            [
                "",
                "As duas formas com tendência são **robustez**, nunca "
                "principais. Uma tendência linear extrapolada sobre 42 meses "
                "de pós pode absorver parte de um efeito de difusão gradual, "
                "e a forma de amostra completa é mais exposta a isso porque "
                "usa o pós para ajustar a inclinação.",
                "",
            ]
        )

    if coverage is not None and len(coverage):
        row = coverage.iloc[0]
        lines.extend(
            [
                "## 6. Cobertura salarial",
                "",
                "Restringir às CBOs com salário válido em todos os meses da "
                f"janela retém {int(row['cbo_complete_wage_coverage'])} de "
                f"{int(row['cbo_complete_wage_coverage']) + int(row['cbo_dropped'])} "
                "CBOs. O teste conjunto continua rejeitando "
                f"(p = {_format(row['joint_lead_p_value'])}), então a "
                "cobertura desbalanceada não é o que produz os leads "
                "oscilantes do salário.",
                "",
            ]
        )

    honest = read_optional(DIAGNOSTICS_DIR / "honest_did_summary.csv")
    if honest is not None:
        lines.extend(
            [
                "## 7. Sensibilidade de Rambachan-Roth",
                "",
                "O alvo da análise de sensibilidade é o estimando do **event "
                "study**, `average_post_event_time_0_to_23`, e não o "
                "coeficiente estático da manchete. São janelas e "
                "normalizações diferentes.",
                "",
                "`DeltaRM` limita a violação pós pelo máximo da violação pré. "
                "`DeltaSD` limita a curvatura da tendência diferencial, e seu "
                "`M` está em unidades do resultado — os dois `M` não são "
                "comparáveis entre si.",
                "",
                "| Outcome | Restrição | Estimativa alvo | EP | "
                "Maior M que exclui zero | Situação |",
                "|---|---|---:|---:|---:|---|",
            ]
        )
        for row in honest.itertuples(index=False):
            lines.append(
                f"| {row.outcome} | {row.Delta} | "
                f"{_format(row.target_estimate)} | "
                f"{_format(row.target_standard_error)} | "
                f"{_format(row.largest_evaluated_M_excluding_zero)} | "
                f"{row.threshold_status} |"
            )
        lines.append("")

    lines.extend(
        [
            "## 8. O que isto fecha e o que não fecha",
            "",
            "Fecha: nenhuma das especificações disponíveis — amostra de "
            "2022, nível 2 setorial, exposição contínua, `Minimal Exposure` "
            "como controle, cobertura salarial completa — passa no "
            "diagnóstico. A falha não é específica de 2021, não é falta de "
            "poder e não é artefato de cobertura.",
            "",
            "Não fecha: a decisão sobre especificação principal. Ela é do "
            "autor. Promover uma especificação porque ela passou num "
            "pré-teste é seleção sobre o diagnóstico, que é exatamente o "
            "que Roth (2022) mostra que distorce a inferência.",
            "",
        ]
    )

    support = {
        "gate": "8A",
        "rows": int(len(table)),
        "specifications": sorted(
            table["specification_id"].dropna().unique().tolist()
        ),
        "families": sorted(table["family"].dropna().unique().tolist()),
        "status_counts": {
            str(key): int(value) for key, value in status_counts.items()
        },
        "any_specification_passes": bool(
            table["pretrend_status"].isin(["pass", "warning"]).any()
        ),
        "non_psd_covariance_rows": int(
            (
                table["lead_covariance_positive_semidefinite"]
                .astype("string")
                .str.lower()
                .eq("false")
            ).sum()
        ),
        "recommends_principal_specification": False,
        "sources_present": [
            str(source["path"].name)
            for source in SOURCES
            if source["path"].is_file()
        ],
    }
    return "\n".join(lines), support


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assemble the Gate 8A pretrend report."
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    table = load_sources()
    report, support = build_report(table)
    atomic_csv(table, args.table)
    atomic_text(report, args.report)
    atomic_json(support, args.support)
    print(json.dumps(support, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
