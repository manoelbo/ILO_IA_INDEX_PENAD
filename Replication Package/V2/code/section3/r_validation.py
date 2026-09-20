"""Independent R validation for every Section 3 numerical aggregate."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common.merge_audit import audited_merge
from .constants import (
    HIGH_GRADIENTS,
    LOW_GRADIENTS,
    MODERATE_GRADIENTS,
    SEM_CLASS,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
TOLERANCE = 1e-6
OFFICIAL_GRADIENTS = (
    "Not Exposed",
    "Minimal Exposure",
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
)


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    valid = values.notna() & weights.notna()
    if not valid.any():
        return float("nan")
    return float(np.average(values.loc[valid], weights=weights.loc[valid]))


def build_python_aggregates(frame: pd.DataFrame) -> pd.DataFrame:
    """Build a stable long registry for all Section 3 numeric inputs."""
    rows: list[dict[str, Any]] = []

    def add(scope: str, key: str, metric: str, value: float | int) -> None:
        rows.append(
            {
                "aggregate_id": f"{scope}::{key}::{metric}",
                "scope": scope,
                "key": key,
                "metric": metric,
                "value": float(value),
            }
        )

    scored = frame.loc[frame["exposure_score"].notna()].copy()
    official = frame.loc[frame["exposure_gradient"].isin(OFFICIAL_GRADIENTS)].copy()
    total_weight = float(frame["peso"].sum())
    score_weight = float(scored["peso"].sum())
    add("base", "sample", "observations", len(frame))
    add("base", "sample", "population_m", total_weight / 1e6)
    add("base", "sample", "scored_population_m", score_weight / 1e6)
    add("base", "sample", "score_coverage_pct", score_weight / total_weight * 100)
    add("base", "sample", "four_digit_match_pct", frame["match_level"].eq("4-digit").mean() * 100)
    add("base", "sample", "three_digit_match_pct", frame["match_level"].eq("3-digit").mean() * 100)
    add("base", "sample", "unscored_rows_pct", frame["exposure_score"].isna().mean() * 100)
    add("base", "sample", "federal_units", frame["sigla_uf"].nunique())
    add("base", "sample", "occupations", frame["cod_ocupacao"].nunique())
    add("base", "sample", "matched_occupations", scored["cod_ocupacao"].nunique())
    add("base", "sample", "original_sectors", frame["setor_agregado_original"].nunique())
    add("base", "sample", "corrected_sectors", frame["sector_corrected"].nunique())

    for gradient in (*OFFICIAL_GRADIENTS, SEM_CLASS):
        group = scored.loc[scored["exposure_gradient"].eq(gradient)]
        weight = float(group["peso"].sum())
        add("gradient", gradient, "population_m", weight / 1e6)
        add("gradient", gradient, "share_pct", weight / score_weight * 100)

    for label, gradients in (
        ("low", LOW_GRADIENTS),
        ("moderate", MODERATE_GRADIENTS),
        ("high", HIGH_GRADIENTS),
    ):
        weight = float(
            official.loc[official["exposure_gradient"].isin(gradients), "peso"].sum()
        )
        add("exposure_group", label, "population_m", weight / 1e6)
        add("exposure_group", label, "share_pct", weight / official["peso"].sum() * 100)

    high = official.loc[official["exposure_gradient"].isin(HIGH_GRADIENTS)]
    occupations = []
    for (code, major_group), group in high.groupby(
        ["cod_ocupacao", "grande_grupo"], sort=False
    ):
        occupations.append(
            {
                "code": str(code),
                "major_group": str(major_group),
                "population_m": float(group["peso"].sum() / 1e6),
                "mean_score": _weighted_mean(group["exposure_score"], group["peso"]),
            }
        )
    top = pd.DataFrame(occupations).sort_values(
        ["population_m", "code"], ascending=[False, True]
    ).head(5)
    for rank, row in enumerate(top.itertuples(index=False), start=1):
        key = f"{rank}:{row.code}:{row.major_group}"
        add("high_occupation", key, "population_m", row.population_m)
        add("high_occupation", key, "mean_score", row.mean_score)

    official_total = float(official["peso"].sum())
    for sector, group in official.groupby("sector_corrected", sort=True):
        total = float(group["peso"].sum())
        low = float(group.loc[group["exposure_gradient"].isin(LOW_GRADIENTS), "peso"].sum())
        moderate = float(group.loc[group["exposure_gradient"].isin(MODERATE_GRADIENTS), "peso"].sum())
        high_weight = float(group.loc[group["exposure_gradient"].isin(HIGH_GRADIENTS), "peso"].sum())
        metrics = {
            "population_m": total / 1e6,
            "brazil_share_pct": total / official_total * 100,
            "mean_score": _weighted_mean(group["exposure_score"], group["peso"]),
            "low_population_m": low / 1e6,
            "low_share_pct": low / total * 100,
            "moderate_population_m": moderate / 1e6,
            "moderate_share_pct": moderate / total * 100,
            "high_population_m": high_weight / 1e6,
            "high_share_pct": high_weight / total * 100,
            "exposed_population_m": (moderate + high_weight) / 1e6,
            "exposed_share_pct": (moderate + high_weight) / total * 100,
        }
        for metric, value in metrics.items():
            add("sector", str(sector), metric, value)

    dimensions = (
        ("sex", "sexo_texto", frame),
        ("race", "raca_agregada", frame),
        ("age", "faixa_etaria", frame),
        ("education", "nivel_instrucao", frame),
        ("income", "faixa_renda_sm", frame.loc[frame["tem_renda"].eq(1)]),
        ("formality", "formal", frame),
    )
    for dimension, column, base in dimensions:
        score_base = base.loc[base["exposure_score"].notna()]
        official_base = base.loc[base["exposure_gradient"].isin(OFFICIAL_GRADIENTS)]
        categories = sorted(
            {str(value) for value in official_base[column].dropna().tolist()}
            | {str(value) for value in score_base[column].dropna().tolist()}
        )
        for category in categories:
            score_group = score_base.loc[score_base[column].astype(str).eq(category)]
            group = official_base.loc[official_base[column].astype(str).eq(category)]
            total = float(group["peso"].sum())
            high_weight = float(group.loc[group["exposure_gradient"].isin(HIGH_GRADIENTS), "peso"].sum())
            low_weight = float(group.loc[group["exposure_gradient"].isin(LOW_GRADIENTS), "peso"].sum())
            moderate_weight = float(group.loc[group["exposure_gradient"].isin(MODERATE_GRADIENTS), "peso"].sum())
            key = f"{dimension}:{category}"
            metrics = {
                "population_m": total / 1e6,
                "mean_score": _weighted_mean(score_group["exposure_score"], score_group["peso"]),
                "low_share_pct": low_weight / total * 100,
                "moderate_share_pct": moderate_weight / total * 100,
                "high_share_pct": high_weight / total * 100,
                "high_population_m": high_weight / 1e6,
            }
            for metric, value in metrics.items():
                add("demographic", key, metric, value)

    for state, group in official.groupby("sigla_uf", sort=True):
        total = float(group["peso"].sum())
        high_weight = float(group.loc[group["exposure_gradient"].isin(HIGH_GRADIENTS), "peso"].sum())
        add("state", str(state), "population_m", total / 1e6)
        add("state", str(state), "high_population_m", high_weight / 1e6)
        add("state", str(state), "high_share_pct", high_weight / total * 100)

    for major_group, group in scored.groupby("grande_grupo", sort=True):
        add("occupation_group", str(major_group), "population_m", group["peso"].sum() / 1e6)
        add("occupation_group", str(major_group), "mean_score", _weighted_mean(group["exposure_score"], group["peso"]))

    add("score_distribution", "all", "minimum", scored["exposure_score"].min())
    add("score_distribution", "all", "maximum", scored["exposure_score"].max())
    add("score_distribution", "all", "weighted_mean", _weighted_mean(scored["exposure_score"], scored["peso"]))

    output = pd.DataFrame(rows).sort_values("aggregate_id").reset_index(drop=True)
    if output["aggregate_id"].duplicated().any():
        raise RuntimeError("Section 3 aggregate identifiers are not unique")
    return output


def run_r_validation(frame: pd.DataFrame, output_dir: Path) -> dict[str, Any]:
    """Run R from an analytical CSV and compare all registered aggregates."""
    validation_dir = output_dir / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="section3-r-") as temporary:
        input_path = Path(temporary) / "section3_analytic.csv.gz"
        frame.to_csv(
            input_path,
            index=False,
            float_format="%.17g",
            compression={"method": "gzip", "mtime": 0},
        )
        r_output = validation_dir / "r_aggregates.csv"
        r_status = validation_dir / "r_status.json"
        completed = subprocess.run(
            [
                "Rscript",
                str(PACKAGE_ROOT / "R" / "section3_replication.R"),
                "--input",
                str(input_path),
                "--output",
                str(r_output),
                "--status",
                str(r_status),
            ],
            cwd=PACKAGE_ROOT,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("Independent Section 3 R aggregation failed")

    python = build_python_aggregates(frame).rename(columns={"value": "python_value"})
    r = pd.read_csv(validation_dir / "r_aggregates.csv").rename(
        columns={"value": "r_value"}
    )
    comparison = audited_merge(
        python,
        r[["aggregate_id", "r_value"]],
        merge_id="section3_python_r_aggregates",
        on="aggregate_id",
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    comparison["absolute_difference"] = (
        comparison["python_value"] - comparison["r_value"]
    ).abs()
    comparison["comparison_pass"] = (
        comparison["_merge"].eq("both")
        & comparison["absolute_difference"].le(TOLERANCE)
    )
    comparison_path = validation_dir / "python_r_aggregate_comparison.csv"
    comparison.to_csv(comparison_path, index=False)
    failed = int((~comparison["comparison_pass"]).sum())
    status = {
        "aggregate_rows": int(len(comparison)),
        "failed_rows": failed,
        "maximum_absolute_difference": float(comparison["absolute_difference"].max()),
        "numeric_tolerance": TOLERANCE,
        "status": "pass" if failed == 0 else "fail",
    }
    status_path = validation_dir / "python_r_status.json"
    temporary = status_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, status_path)
    if failed:
        raise RuntimeError("Section 3 Python-R aggregate comparison failed")
    return status
