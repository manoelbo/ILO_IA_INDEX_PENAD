#!/usr/bin/env python3
"""Diagnose vintage completeness and variable continuity before modeling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

import matplotlib
import pandas as pd
import pyarrow.dataset as ds


matplotlib.use("Agg")
import matplotlib.pyplot as plt


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_MOVEMENTS = PACKAGE_ROOT / "data" / "interim" / "movimentacoes"
DEFAULT_CLASSIFICATION = (
    REPOSITORY_ROOT
    / "Replication Package"
    / "V1"
    / "data"
    / "derived"
    / "sections4_5"
    / "outputs"
    / "treatment_scenario_grid"
    / "scenario_cbo_classification.csv"
)
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "results" / "reconciliation"
START_MONTH = "202101"
CUTOFF = "202605"
ORIGINS = ("MOV", "FOR", "EXC")
SCANNER_COLUMNS = (
    "competenciamov",
    "competencia_arquivo",
    "origem",
    "peso",
    "cbo2002ocupacao",
    "saldomovimentacao",
    "tipomovimentacao",
    "categoria",
    "indicadoraprendiz",
    "unidadesalariocodigo",
    "racacor",
    "graudeinstrucao",
    "tipoempregador",
    "tipoestabelecimento",
    "horascontratuais",
)


def month_distance(earlier: str, later: str) -> int:
    earlier_period = pd.Period(
        f"{earlier[:4]}-{earlier[4:]}",
        freq="M",
    )
    later_period = pd.Period(
        f"{later[:4]}-{later[4:]}",
        freq="M",
    )
    return int(later_period.ordinal - earlier_period.ordinal)


def _source_counts(
    frame: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    return (
        frame.groupby(
            [*group_columns, "origem"],
            observed=True,
            dropna=False,
        )
        .size()
        .rename("linhas")
        .reset_index()
    )


def _weighted_sum(
    frame: pd.DataFrame,
    mask: pd.Series,
) -> pd.Series:
    return frame.loc[mask].groupby(
        "competenciamov",
        observed=True,
    )["peso"].sum()


def _physical_count(
    frame: pd.DataFrame,
    mask: pd.Series,
) -> pd.Series:
    return frame.loc[mask].groupby(
        "competenciamov",
        observed=True,
    ).size()


def _unknown(series: pd.Series, codes: set[str]) -> pd.Series:
    values = series.astype("string").fillna("").str.strip()
    return values.eq("") | values.isin(codes)


def _continuity_summary(frame: pd.DataFrame) -> pd.DataFrame:
    sign = pd.to_numeric(frame["saldomovimentacao"], errors="coerce")
    weight = pd.to_numeric(frame["peso"], errors="raise")
    frame = frame.copy()
    frame["peso"] = weight
    admissions = sign.eq(1)
    separations = sign.eq(-1)
    movement_type = frame["tipomovimentacao"].astype("string")
    hours = pd.to_numeric(frame["horascontratuais"], errors="coerce")
    salary_unit = frame["unidadesalariocodigo"].astype("string").fillna("")

    metrics = {
        "linhas_liquidas": _weighted_sum(
            frame,
            pd.Series(True, index=frame.index),
        ),
        "admissoes_liquidas": _weighted_sum(frame, admissions),
        "desligamentos_liquidos": _weighted_sum(frame, separations),
        "tipo_mov_admissao_ni": _weighted_sum(
            frame,
            admissions & _unknown(movement_type, {"97", "99"}),
        ),
        "tipo_mov_desligamento_ni": _weighted_sum(
            frame,
            separations & _unknown(movement_type, {"98", "99"}),
        ),
        "categoria_ni": _weighted_sum(
            frame,
            _unknown(frame["categoria"], {"999"}),
        ),
        "indicador_aprendiz_ni": _weighted_sum(
            frame,
            _unknown(frame["indicadoraprendiz"], {"9"}),
        ),
        "unidade_salario_ni": _weighted_sum(
            frame,
            _unknown(salary_unit, {"99"}),
        ),
        "unidade_salario_nao_mensal": _weighted_sum(
            frame,
            salary_unit.ne("5"),
        ),
        "raca_cor_ni": _weighted_sum(
            frame,
            _unknown(frame["racacor"], {"6", "9"}),
        ),
        "grau_instrucao_ni": _weighted_sum(
            frame,
            _unknown(frame["graudeinstrucao"], {"99"}),
        ),
        "tipo_empregador_ni": _weighted_sum(
            frame,
            _unknown(frame["tipoempregador"], {"9"}),
        ),
        "tipo_empregador_codigo_1": _weighted_sum(
            frame,
            frame["tipoempregador"].astype("string").eq("1"),
        ),
        "tipo_estabelecimento_codigo_menos_1": _weighted_sum(
            frame,
            frame["tipoestabelecimento"].astype("string").eq("-1"),
        ),
        "horas_validas_admissoes": _weighted_sum(
            frame,
            admissions & hours.gt(0),
        ),
        "horas_validas_desligamentos": _weighted_sum(
            frame,
            separations & hours.gt(0),
        ),
        "transferencia_70_liquida": _weighted_sum(
            frame,
            movement_type.eq("70"),
        ),
        "transferencia_80_liquida": _weighted_sum(
            frame,
            movement_type.eq("80"),
        ),
        "transferencia_70_linhas": _physical_count(
            frame,
            movement_type.eq("70"),
        ),
        "transferencia_80_linhas": _physical_count(
            frame,
            movement_type.eq("80"),
        ),
        "exc_mesmo_mes_linhas": _physical_count(
            frame,
            frame["origem"].eq("EXC")
            & frame["competenciamov"]
            .astype(str)
            .eq(frame["competencia_arquivo"].astype(str)),
        ),
    }
    return pd.DataFrame(metrics).fillna(0).reset_index()


def summarize_batch(
    frame: pd.DataFrame,
    role_map: Mapping[str, str],
) -> dict[str, pd.DataFrame]:
    """Reduce one scanner batch to small additive diagnostic summaries."""
    data = frame.copy()
    data["competenciamov"] = data["competenciamov"].astype(str)
    data["competencia_arquivo"] = data["competencia_arquivo"].astype(str)
    data["cbo2002ocupacao"] = (
        data["cbo2002ocupacao"].astype("string").fillna("").str.strip()
    )
    data["grande_grupo_cbo"] = data["cbo2002ocupacao"].str[:1]
    data["cbo_4d"] = data["cbo2002ocupacao"].str[:4]
    data["grupo_tratamento"] = data["cbo_4d"].map(role_map)
    treatment = data[
        data["grupo_tratamento"].isin({"treated", "control"})
    ]
    return {
        "monthly": _source_counts(data, ["competenciamov"]),
        "large_group": _source_counts(
            data[data["grande_grupo_cbo"].str.fullmatch(r"\d")],
            ["competenciamov", "grande_grupo_cbo"],
        ),
        "treatment": _source_counts(
            treatment,
            ["competenciamov", "grupo_tratamento"],
        ),
        "continuity": _continuity_summary(data),
    }


def _combine_summaries(
    frames: list[pd.DataFrame],
    keys: list[str],
) -> pd.DataFrame:
    combined = pd.concat(frames, ignore_index=True)
    value_columns = [
        column for column in combined.columns if column not in keys
    ]
    return (
        combined.groupby(keys, observed=True, as_index=False)[value_columns]
        .sum()
        .sort_values(keys)
        .reset_index(drop=True)
    )


def _pivot_origins(
    counts: pd.DataFrame,
    index_columns: list[str],
    cutoff: str,
) -> pd.DataFrame:
    pivot = counts.pivot_table(
        index=index_columns,
        columns="origem",
        values="linhas",
        aggfunc="sum",
        fill_value=0,
    )
    pivot = pivot.reindex(columns=ORIGINS, fill_value=0).reset_index()
    pivot = pivot.rename(
        columns={
            "MOV": "linhas_mov",
            "FOR": "linhas_for",
            "EXC": "linhas_exc",
        }
    )
    pivot["meses_for_possiveis"] = pivot["competenciamov"].map(
        lambda month: min(max(month_distance(str(month), cutoff), 0), 12)
    )
    pivot["fracao_for_sobre_mov_pct"] = (
        100.0 * pivot["linhas_for"] / pivot["linhas_mov"].replace(0, pd.NA)
    )
    return pivot


def finalize_treatment_completeness(
    counts: pd.DataFrame,
    cutoff: str = CUTOFF,
) -> pd.DataFrame:
    result = _pivot_origins(
        counts,
        ["competenciamov", "grupo_tratamento"],
        cutoff,
    )
    fractions = result.pivot(
        index="competenciamov",
        columns="grupo_tratamento",
        values="fracao_for_sobre_mov_pct",
    )
    if {"treated", "control"} - set(fractions.columns):
        raise RuntimeError("Treatment completeness requires treated and control")
    differential = (
        fractions["treated"] - fractions["control"]
    ).rename("diferencial_tratado_controle_pp")
    result = result.merge(
        differential,
        on="competenciamov",
        how="left",
        validate="many_to_one",
    )
    result["diferencial_acima_1pp"] = (
        result["diferencial_tratado_controle_pp"].abs() > 1.0
    )
    return result.sort_values(
        ["competenciamov", "grupo_tratamento"]
    ).reset_index(drop=True)


def _percentage(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    return 100.0 * numerator / denominator.replace(0, pd.NA)


def finalize_continuity(summary: pd.DataFrame) -> pd.DataFrame:
    result = summary.copy()
    total = result["linhas_liquidas"]
    admissions = result["admissoes_liquidas"]
    separations = result["desligamentos_liquidos"]
    shares = {
        "tipo_mov_admissao_ni_pct": (
            "tipo_mov_admissao_ni",
            admissions,
        ),
        "tipo_mov_desligamento_ni_pct": (
            "tipo_mov_desligamento_ni",
            separations,
        ),
        "categoria_ni_pct": ("categoria_ni", total),
        "indicador_aprendiz_ni_pct": ("indicador_aprendiz_ni", total),
        "unidade_salario_ni_pct": ("unidade_salario_ni", total),
        "unidade_salario_nao_mensal_pct": (
            "unidade_salario_nao_mensal",
            total,
        ),
        "raca_cor_ni_pct": ("raca_cor_ni", total),
        "grau_instrucao_ni_pct": ("grau_instrucao_ni", total),
        "tipo_empregador_ni_pct": ("tipo_empregador_ni", total),
        "tipo_empregador_codigo_1_pct": (
            "tipo_empregador_codigo_1",
            total,
        ),
        "tipo_estabelecimento_codigo_menos_1_pct": (
            "tipo_estabelecimento_codigo_menos_1",
            total,
        ),
        "horas_validas_admissoes_pct": (
            "horas_validas_admissoes",
            admissions,
        ),
        "horas_validas_desligamentos_pct": (
            "horas_validas_desligamentos",
            separations,
        ),
    }
    for output_column, (numerator, denominator) in shares.items():
        result[output_column] = _percentage(
            result[numerator],
            denominator,
        )
    return result.sort_values("competenciamov").reset_index(drop=True)


def _load_role_map(path: Path) -> dict[str, str]:
    classification = pd.read_csv(path, dtype={"cbo_4d": str})
    required = {"cbo_4d", "role__trat_expostos"}
    missing = required - set(classification.columns)
    if missing:
        raise ValueError(f"Classification is missing columns: {missing}")
    roles = classification[
        classification["role__trat_expostos"].isin({"treated", "control"})
    ]
    role_map = dict(
        zip(
            roles["cbo_4d"].str.zfill(4),
            roles["role__trat_expostos"],
        )
    )
    counts = roles["role__trat_expostos"].value_counts().to_dict()
    if counts != {"control": 266, "treated": 75}:
        raise RuntimeError(
            "Frozen treatment roles do not reproduce 75 treated and "
            f"266 controls: {counts}"
        )
    return role_map


def _plot_completeness(frame: pd.DataFrame, path: Path) -> None:
    dates = pd.to_datetime(frame["competenciamov"], format="%Y%m")
    figure, axis = plt.subplots(figsize=(12, 6.75))
    axis.plot(
        dates,
        frame["fracao_for_sobre_mov_pct"],
        color="#155E75",
        linewidth=2.2,
        label="FOR / MOV",
    )
    axis.set_ylabel("Late declarations relative to MOV (%)")
    axis.set_xlabel("Fact month")
    axis.grid(axis="y", alpha=0.25)
    second = axis.twinx()
    second.plot(
        dates,
        frame["meses_for_possiveis"],
        color="#D97706",
        linewidth=1.8,
        linestyle="--",
        label="Eligible FOR months",
    )
    second.set_ylabel("Months available for late declarations (capped at 12)")
    axis.set_title("Novo CAGED vintage completeness by fact month")
    handles_a, labels_a = axis.get_legend_handles_labels()
    handles_b, labels_b = second.get_legend_handles_labels()
    axis.legend(
        handles_a + handles_b,
        labels_a + labels_b,
        loc="upper right",
        frameon=False,
    )
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160)
    plt.close(figure)


def run_diagnostics(
    movements_path: Path,
    classification_path: Path,
    output_dir: Path,
    *,
    cutoff: str = CUTOFF,
) -> dict[str, object]:
    role_map = _load_role_map(classification_path)
    dataset = ds.dataset(
        movements_path,
        format="parquet",
        partitioning="hive",
    )
    collected: dict[str, list[pd.DataFrame]] = {
        "monthly": [],
        "large_group": [],
        "treatment": [],
        "continuity": [],
    }
    for index, batch in enumerate(
        dataset.scanner(
            columns=list(SCANNER_COLUMNS),
            filter=(
                (ds.field("competenciamov") >= int(START_MONTH))
                & (ds.field("competenciamov") <= int(cutoff))
            ),
            batch_size=500_000,
        ).to_batches(),
        start=1,
    ):
        if index % 25 == 0:
            print(f"diagnostic batches processed: {index}", flush=True)
        summaries = summarize_batch(batch.to_pandas(), role_map)
        for key, summary in summaries.items():
            collected[key].append(summary)

    monthly_counts = _combine_summaries(
        collected["monthly"],
        ["competenciamov", "origem"],
    )
    group_counts = _combine_summaries(
        collected["large_group"],
        ["competenciamov", "grande_grupo_cbo", "origem"],
    )
    treatment_counts = _combine_summaries(
        collected["treatment"],
        ["competenciamov", "grupo_tratamento", "origem"],
    )
    continuity_summary = _combine_summaries(
        collected["continuity"],
        ["competenciamov"],
    )

    monthly = _pivot_origins(
        monthly_counts,
        ["competenciamov"],
        cutoff,
    )
    by_group = _pivot_origins(
        group_counts,
        ["competenciamov", "grande_grupo_cbo"],
        cutoff,
    )
    by_treatment = finalize_treatment_completeness(
        treatment_counts,
        cutoff,
    )
    continuity = finalize_continuity(continuity_summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(
        output_dir / "completude_por_competencia.csv",
        index=False,
    )
    by_group.to_csv(
        output_dir / "completude_por_grupo_cbo.csv",
        index=False,
    )
    by_treatment.to_csv(
        output_dir / "completude_por_tratamento.csv",
        index=False,
    )
    continuity.to_csv(
        output_dir / "continuidade_variaveis.csv",
        index=False,
    )
    _plot_completeness(
        monthly,
        output_dir / "completude_por_competencia.png",
    )

    recent = by_treatment[
        by_treatment["meses_for_possiveis"].lt(12)
    ]
    max_difference = float(
        recent["diferencial_tratado_controle_pp"].abs().max()
    )
    maximum_row = recent.loc[
        recent["diferencial_tratado_controle_pp"].abs().idxmax()
    ]
    metrics = {
        "cutoff": cutoff,
        "months": int(monthly["competenciamov"].nunique()),
        "recent_incomplete_months": int(
            recent["competenciamov"].nunique()
        ),
        "max_recent_treatment_control_difference_pp": max_difference,
        "max_difference_month": str(maximum_row["competenciamov"]),
        "window_decision_blocked": max_difference > 1.0,
        "transfer_70_physical_rows": int(
            continuity["transferencia_70_linhas"].sum()
        ),
        "transfer_80_physical_rows": int(
            continuity["transferencia_80_linhas"].sum()
        ),
        "same_month_exclusion_rows": int(
            continuity["exc_mesmo_mes_linhas"].sum()
        ),
    }
    (output_dir / "diagnostico_vintage_metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose completeness and variable continuity."
    )
    parser.add_argument(
        "--movements",
        type=Path,
        default=DEFAULT_MOVEMENTS,
    )
    parser.add_argument(
        "--classification",
        type=Path,
        default=DEFAULT_CLASSIFICATION,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument("--cutoff", default=CUTOFF)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = run_diagnostics(
        args.movements,
        args.classification,
        args.output_dir,
        cutoff=args.cutoff,
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
