#!/usr/bin/env python3
"""Independent Python replication of selected Sections 4–5 estimates.

This script is intentionally separate from the author's analysis code. It rebuilds
the national static DiD estimates and selected income DDD estimates from the
frozen analytical panel using explicit dummy-variable OLS and a manually computed
CRV1 covariance matrix.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import linalg, stats


CONTROLS = (
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
)
NATIONAL_OUTCOMES = (
    "ln_admissoes",
    "ln_desligamentos",
    "ln_salario_adm",
)
INCOME_MODELS = (
    ("low_income", "ln_admissoes"),
    ("low_income", "ln_desligamentos"),
    ("middle_income", "ln_admissoes"),
    ("middle_income", "ln_desligamentos"),
    ("high_income", "ln_desligamentos"),
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        type=Path,
        default=root
        / "Replication Package/outputs/sections4_5/inputs/data/output"
        / "painel_2b_ready.parquet",
    )
    parser.add_argument(
        "--classification",
        type=Path,
        default=root
        / "Replication Package/outputs/sections4_5/inputs/outputs"
        / "treatment_scenario_grid/scenario_cbo_classification.csv",
    )
    parser.add_argument(
        "--income-assignments",
        type=Path,
        default=root
        / "outputs/dissertation_section4/final_event_study/audit"
        / "pre_treatment_income_group_assignments.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "correspondence/referee2",
    )
    return parser.parse_args()


def _require_columns(data: pd.DataFrame, columns: set[str], source: Path) -> None:
    missing = sorted(columns - set(data.columns))
    if missing:
        raise ValueError(f"{source} is missing required columns: {missing}")


def prepare_analysis_data(
    panel_path: Path,
    classification_path: Path,
    assignments_path: Path,
) -> pd.DataFrame:
    """Build the exact strict-treatment sample used by the selected models."""
    panel = pd.read_parquet(panel_path)
    classification = pd.read_csv(classification_path, dtype={"cbo_4d": str})
    assignments = pd.read_csv(assignments_path, dtype={"cbo_4d": str})

    _require_columns(
        panel,
        {
            "cbo_4d",
            "periodo",
            "post",
            *CONTROLS,
            *NATIONAL_OUTCOMES,
        },
        panel_path,
    )
    _require_columns(
        classification,
        {
            "cbo_4d",
            "role__trat_expostos",
            "treated__trat_expostos",
        },
        classification_path,
    )
    _require_columns(
        assignments,
        {"cbo_4d", "income_group_legacy"},
        assignments_path,
    )

    panel = panel.copy()
    panel["cbo_4d"] = panel["cbo_4d"].astype(str)
    panel["periodo"] = panel["periodo"].astype(str)
    classification = classification[
        [
            "cbo_4d",
            "role__trat_expostos",
            "treated__trat_expostos",
        ]
    ].copy()
    data = panel.merge(
        classification,
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    data = data[
        data["role__trat_expostos"].isin(["treated", "control"])
    ].copy()
    data["treated"] = data["treated__trat_expostos"].astype(int)
    data["post"] = data["post"].astype(int)
    data["post_treat"] = data["post"] * data["treated"]
    data = data.merge(
        assignments[["cbo_4d", "income_group_legacy"]],
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )

    if len(data) != 18_307 or data["cbo_4d"].nunique() != 341:
        raise ValueError(
            "Strict analysis sample contract failed: "
            f"observed {len(data):,} rows and "
            f"{data['cbo_4d'].nunique()} CBOs."
        )
    if int(data["treated"].sum() > 0) != 1:
        raise ValueError("Treatment indicator is empty.")
    cbo_roles = data[["cbo_4d", "treated"]].drop_duplicates()
    if cbo_roles["treated"].value_counts().to_dict() != {0: 266, 1: 75}:
        raise ValueError("Treatment/control CBO counts differ from 75/266.")
    return data


def _cluster_crv1(
    x: np.ndarray,
    residuals: np.ndarray,
    clusters: pd.Series,
    nested_cluster_fe_count: int,
) -> tuple[np.ndarray, float, int, int]:
    """Return a CRV1 covariance matching the author's fixed-effect convention."""
    cluster_codes, _ = pd.factorize(clusters, sort=True)
    n_obs, rank = x.shape
    n_clusters = int(np.unique(cluster_codes).size)
    if n_clusters < 2:
        raise ValueError("At least two clusters are required.")

    bread = np.linalg.pinv(x.T @ x)
    scores = np.zeros((n_clusters, x.shape[1]), dtype=float)
    np.add.at(scores, cluster_codes, x * residuals[:, None])
    meat = scores.T @ scores

    effective_k = rank - nested_cluster_fe_count
    factor = (n_clusters / (n_clusters - 1)) * (
        (n_obs - 1) / (n_obs - effective_k)
    )
    covariance = factor * (bread @ meat @ bread)
    return covariance, factor, rank, effective_k


def fit_model(
    data: pd.DataFrame,
    outcome: str,
    formula_rhs: str,
    term: str,
    model_id: str,
    estimand: str,
    group_id: str = "",
) -> dict[str, object]:
    formula = (
        f"{outcome} ~ {formula_rhs} + "
        + " + ".join(CONTROLS)
        + " + C(cbo_4d) + C(periodo)"
    )
    model = smf.ols(formula, data=data)
    x_full = np.asarray(model.exog, dtype=float)
    y = np.asarray(model.endog, dtype=float)
    rank = int(np.linalg.matrix_rank(x_full))
    _, _, pivot = linalg.qr(x_full, mode="economic", pivoting=True)
    active = np.asarray(pivot[:rank], dtype=int)
    x = x_full[:, active]
    coefficients, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    residuals = y - x @ coefficients
    row_labels = model.data.row_labels
    cluster_values = data.loc[row_labels, "cbo_4d"]
    n_clusters = int(cluster_values.nunique())
    covariance, factor, rank, effective_k = _cluster_crv1(
        x,
        residuals,
        cluster_values,
        nested_cluster_fe_count=n_clusters - 1,
    )
    full_term_index = model.exog_names.index(term)
    active_matches = np.flatnonzero(active == full_term_index)
    if len(active_matches) != 1:
        raise ValueError(f"Target term {term!r} is not identified in {model_id}.")
    term_index = int(active_matches[0])
    coefficient = float(coefficients[term_index])
    standard_error = float(math.sqrt(covariance[term_index, term_index]))
    statistic = coefficient / standard_error
    if estimand == "DiD":
        p_value = float(2 * stats.t.sf(abs(statistic), df=n_clusters - 1))
        p_distribution = f"t({n_clusters - 1})"
    else:
        p_value = float(2 * stats.norm.sf(abs(statistic)))
        p_distribution = "normal/chi-square(1)"
    return {
        "language": "Python",
        "model_id": model_id,
        "estimand": estimand,
        "group_id": group_id,
        "outcome": outcome,
        "term": term,
        "coefficient": coefficient,
        "standard_error": standard_error,
        "p_value": p_value,
        "statistic": statistic,
        "p_distribution": p_distribution,
        "n_obs": int(len(y)),
        "n_cbo": n_clusters,
        "rank": rank,
        "effective_k_crv1": effective_k,
        "crv1_factor": factor,
        "formula": formula,
    }


def run_replication(data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for outcome in NATIONAL_OUTCOMES:
        rows.append(
            fit_model(
                data=data,
                outcome=outcome,
                formula_rhs="post_treat",
                term="post_treat",
                model_id=f"national_{outcome}",
                estimand="DiD",
            )
        )

    for group_id, outcome in INCOME_MODELS:
        model_data = data.copy()
        model_data["group"] = (
            model_data["income_group_legacy"].eq(group_id).astype(int)
        )
        model_data["post_group"] = model_data["post"] * model_data["group"]
        model_data["treat_group"] = model_data["treated"] * model_data["group"]
        model_data["post_treat_group"] = (
            model_data["post_treat"] * model_data["group"]
        )
        rows.append(
            fit_model(
                data=model_data,
                outcome=outcome,
                formula_rhs=(
                    "post_treat_group + post_treat + post_group + treat_group"
                ),
                term="post_treat_group",
                model_id=f"income_{group_id}_{outcome}",
                estimand="DDD",
                group_id=group_id,
            )
        )
    return pd.DataFrame(rows)


def write_bridge_data(data: pd.DataFrame, output_path: Path) -> None:
    bridge = data[
        [
            "cbo_4d",
            "periodo",
            "post",
            "treated",
            "post_treat",
            "income_group_legacy",
            *CONTROLS,
            *NATIONAL_OUTCOMES,
        ]
    ].copy()
    bridge["income_group_legacy"] = bridge["income_group_legacy"].fillna(
        "unassigned"
    )
    bridge.to_csv(output_path, index=False)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = prepare_analysis_data(
        args.panel.resolve(),
        args.classification.resolve(),
        args.income_assignments.resolve(),
    )
    bridge_path = (
        args.output_dir
        / "2026-07-25_round1_sections4_5_cross_language_input.csv"
    )
    results_path = (
        args.output_dir
        / "2026-07-25_round1_sections4_5_python_results.csv"
    )
    write_bridge_data(data, bridge_path)
    results = run_replication(data)
    results.to_csv(results_path, index=False)
    print(
        f"Wrote {len(results)} independent Python estimates to {results_path}."
    )
    print(f"Wrote the R bridge sample to {bridge_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
