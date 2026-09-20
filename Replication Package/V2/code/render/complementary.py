#!/usr/bin/env python3
"""Render the six registered complementary-evidence manuscript tables."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Callable

import pandas as pd


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def _display(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _markdown(frame: pd.DataFrame, title: str) -> str:
    columns = [str(column) for column in frame.columns]
    lines = [
        f"# {title}",
        "",
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = [
            _display(value).replace("|", "\\|").replace("\n", " ")
            for value in row
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _write_table(frame: pd.DataFrame, path: Path, title: str) -> None:
    _atomic_csv(frame, path)
    markdown_path = path.with_suffix(".md")
    temporary = markdown_path.with_suffix(".md.tmp")
    temporary.write_text(_markdown(frame, title), encoding="utf-8")
    os.replace(temporary, markdown_path)


def _select(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing renderer columns: {missing}")
    return frame.loc[:, list(columns)].copy()


def _render_rais(results_dir: Path, output_dir: Path) -> list[Path]:
    results = pd.read_csv(results_dir / "rais_static_results.csv")
    table = _select(
        results,
        (
            "outcome",
            "estimator",
            "coefficient",
            "standard_error",
            "ci_low",
            "ci_high",
            "nominal_p_value",
            "bh_adjusted_p_value",
            "n_obs",
            "minimum_clusters",
            "pretrend_status",
            "result_status",
            "family_id",
        ),
    )
    pretrends = _select(
        pd.read_csv(results_dir / "rais_pretrends.csv"),
        (
            "outcome",
            "sample_window",
            "joint_lead_count",
            "joint_lead_p_value",
            "linear_pretrend_p_value",
            "dynamic_pre_p_lt_005",
            "lead_covariance_positive_semidefinite",
            "pretrend_status",
            "n_obs",
            "minimum_clusters",
        ),
    )
    table_path = output_dir / "tables" / "table_d_1_rais.csv"
    pretrend_path = output_dir / "tables" / "table_b_1_rais_pretrends.csv"
    _write_table(table, table_path, "Table D.1. RAIS complementary evidence")
    _write_table(pretrends, pretrend_path, "Table B.1. RAIS pretrend diagnostics")
    _copy_backing(
        results_dir,
        output_dir,
        (
            "rais_static_results.csv",
            "rais_pretrends.csv",
            "rais_pretrend_r_comparison.csv",
            "rais_pretrend_r_status.json",
            "rais_sensitivities.csv",
            "rais_support.csv",
            "rais_cross_replication_comparison.csv",
            "rais_cross_replication_status.json",
        ),
    )
    return [table_path, pretrend_path]


def _render_pnadc(results_dir: Path, output_dir: Path) -> list[Path]:
    results = pd.read_csv(results_dir / "pnadc_results.csv")
    table = _select(
        results,
        (
            "outcome",
            "arm",
            "estimator",
            "coefficient",
            "standard_error",
            "ci_low",
            "ci_high",
            "nominal_p_value",
            "bh_adjusted_p_value",
            "n_obs",
            "minimum_clusters",
            "pretrend_status_full",
            "pretrend_status_without_2020",
            "result_status",
            "family_id",
        ),
    )
    pretrends = _select(
        pd.read_csv(results_dir / "pnadc_pretrends.csv"),
        (
            "outcome",
            "sample",
            "joint_lead_count",
            "joint_lead_p_value",
            "linear_pretrend_p_value",
            "dynamic_pre_p_lt_005",
            "lead_covariance_positive_semidefinite",
            "pretrend_status",
            "n_obs",
            "minimum_clusters",
        ),
    )
    table_path = output_dir / "tables" / "table_d_2_pnadc.csv"
    pretrend_path = output_dir / "tables" / "table_b_2_pnadc_pretrends.csv"
    _write_table(table, table_path, "Table D.2. PNADc complementary evidence")
    _write_table(pretrends, pretrend_path, "Table B.2. PNADc pretrend diagnostics")
    _copy_backing(
        results_dir,
        output_dir,
        (
            "pnadc_results.csv",
            "pnadc_pretrends.csv",
            "pnadc_pretrend_cross_comparison.csv",
            "pnadc_pretrend_cross_status.json",
            "pnadc_sensitivities.csv",
            "pnadc_support.csv",
            "pnadc_cross_replication_comparison.csv",
            "pnadc_cross_replication_status.json",
        ),
    )
    return [table_path, pretrend_path]


def _render_spatial(results_dir: Path, output_dir: Path) -> list[Path]:
    placebo = _select(
        pd.read_csv(results_dir / "anatel_placebo_dec2021.csv"),
        (
            "outcome",
            "coefficient",
            "standard_error",
            "p_value",
            "n_obs",
            "minimum_clusters",
            "real_treatment_coefficient_estimated",
        ),
    )
    support = _select(
        pd.read_csv(results_dir / "anatel_a6_cluster_structure.csv"),
        (
            "proxy",
            "municipality_clusters_nominal",
            "uf_clusters_nominal",
            "effective_municipality_clusters",
            "effective_uf_clusters",
            "largest_uf_leverage_code",
            "largest_uf_leverage_share",
            "classification",
        ),
    )
    support["classification"] = support["classification"].replace(
        {"thin": "insufficient"}
    )
    table_path = output_dir / "tables" / "table_b_3_spatial_placebo.csv"
    support_path = output_dir / "tables" / "table_b_4_spatial_support.csv"
    _write_table(placebo, table_path, "Table B.3. Spatial temporal placebo")
    _write_table(support, support_path, "Table B.4. Spatial effective support")
    _copy_backing(
        results_dir,
        output_dir,
        (
            "anatel_placebo_dec2021.csv",
            "anatel_pretrends_interaction.csv",
            "anatel_a6_cluster_structure.csv",
            "anatel_a6_residual_variation.csv",
            "anatel_a6_status.json",
            "spatial_pretrend_coefficients.csv",
            "spatial_r_model_comparison.csv",
            "spatial_r_pretrend_comparison.csv",
            "spatial_r_support_comparison.csv",
            "spatial_r_status.json",
        ),
    )
    family_path = results_dir / "anatel_family_f_declaration.csv"
    if not family_path.is_file():
        family_path = results_dir / "family_f_declaration.csv"
    family = pd.read_csv(family_path)
    _atomic_csv(family, output_dir / "backing_data" / "family_f_declaration.csv")
    return [table_path, support_path]


def _copy_backing(
    results_dir: Path,
    output_dir: Path,
    filenames: tuple[str, ...],
) -> None:
    backing_dir = output_dir / "backing_data"
    backing_dir.mkdir(parents=True, exist_ok=True)
    for filename in filenames:
        source = results_dir / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, backing_dir / filename)


RENDERERS: dict[str, Callable[[Path, Path], list[Path]]] = {
    "rais": _render_rais,
    "pnadc": _render_pnadc,
    "spatial": _render_spatial,
}


def render_component(
    component: str,
    *,
    results_dir: Path,
    output_dir: Path,
) -> list[Path]:
    """Render one component and write a portable navigation index."""
    try:
        renderer = RENDERERS[component]
    except KeyError as error:
        raise ValueError(f"Unsupported complementary component: {component}") from error
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = renderer(results_dir.resolve(), output_dir.resolve())
    index = {
        "component": component,
        "publication_tables": [
            path.relative_to(output_dir).as_posix() for path in tables
        ],
        "status": "rendered",
    }
    (output_dir / "artifact_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return tables
