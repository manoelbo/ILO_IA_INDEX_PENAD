#!/usr/bin/env python3
"""Independently replay the four central V1 models and compare Python with R."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf


OUTCOMES = (
    "ln_admissoes",
    "ln_desligamentos",
    "ln_salario_adm",
    "asinh_saldo",
)
CONTROLS = (
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
)
TOLERANCE = 5e-7


def resolve_package_root(candidate: Path) -> Path:
    """Resolve either the package container or a specific generation."""
    candidate = candidate.resolve()
    frozen = candidate / "V1"
    if frozen.joinpath("run_replication.py").is_file():
        return frozen
    if candidate.joinpath("run_replication.py").is_file():
        return candidate
    raise FileNotFoundError(
        f"Neither a frozen V1 nor a package runner exists under {candidate}"
    )


def prepare_analysis_input(package_root: Path) -> pd.DataFrame:
    """Construct the strict treated-versus-control sample without package code."""
    data_root = package_root / "data" / "derived" / "sections4_5"
    panel = pd.read_parquet(
        data_root / "data" / "output" / "painel_2b_ready.parquet"
    )
    roles = pd.read_csv(
        data_root
        / "outputs"
        / "treatment_scenario_grid"
        / "scenario_cbo_classification.csv",
        dtype={"cbo_4d": "string"},
        usecols=["cbo_4d", "role__trat_expostos"],
    )
    panel["cbo_4d"] = panel["cbo_4d"].astype("string").str.zfill(4)
    data = panel.merge(roles, on="cbo_4d", how="left", validate="many_to_one")
    data = data[
        data["role__trat_expostos"].isin(("treated", "control"))
    ].copy()
    data["scenario_treat"] = (
        data["role__trat_expostos"].eq("treated").astype(int)
    )
    data["post_treat"] = (
        pd.to_numeric(data["post"], errors="raise").astype(int)
        * data["scenario_treat"]
    )
    data["asinh_saldo"] = np.arcsinh(
        pd.to_numeric(data["saldo"], errors="coerce")
    )
    columns = [
        "cbo_4d",
        "periodo",
        "post_treat",
        *CONTROLS,
        *OUTCOMES,
    ]
    return data.loc[:, columns].sort_values(
        ["cbo_4d", "periodo"], kind="stable"
    )


def estimate_python(data: pd.DataFrame) -> pd.DataFrame:
    """Estimate the central models with pyfixest and no author-code imports."""
    controls = " + ".join(CONTROLS)
    rows: list[dict[str, object]] = []
    required_predictors = ["post_treat", *CONTROLS, "cbo_4d", "periodo"]
    for outcome in OUTCOMES:
        model_data = data[[outcome, *required_predictors]].dropna().copy()
        formula = (
            f"{outcome} ~ post_treat + {controls} | cbo_4d + periodo"
        )
        model = pf.feols(
            formula,
            data=model_data,
            vcov={"CRV1": "cbo_4d"},
        )
        result = model.tidy().loc["post_treat"]
        rows.append(
            {
                "outcome": outcome,
                "coef": float(result["Estimate"]),
                "se": float(result["Std. Error"]),
                "p_value": float(result["Pr(>|t|)"]),
                "n_obs": int(model._N),
                "n_clusters": int(model_data["cbo_4d"].nunique()),
                "formula": formula,
                "estimator": "pyfixest.feols",
                "vcov": "CRV1, cluster=cbo_4d",
            }
        )
    return pd.DataFrame(rows)


def compare_results(
    python_results: pd.DataFrame,
    r_results: pd.DataFrame,
) -> pd.DataFrame:
    """Compare languages at six-decimal precision and identical sample size."""
    merged = python_results.merge(
        r_results,
        on="outcome",
        how="outer",
        validate="one_to_one",
        suffixes=("_python", "_r"),
        indicator=True,
    )
    for field in ("coef", "se", "p_value"):
        merged[f"abs_diff_{field}"] = (
            pd.to_numeric(merged[f"{field}_python"], errors="coerce")
            - pd.to_numeric(merged[f"{field}_r"], errors="coerce")
        ).abs()
    merged["max_abs_difference"] = merged[
        ["abs_diff_coef", "abs_diff_se", "abs_diff_p_value"]
    ].max(axis=1)
    merged["n_equal"] = (
        pd.to_numeric(merged["n_obs_python"], errors="coerce")
        == pd.to_numeric(merged["n_obs_r"], errors="coerce")
    )
    merged["clusters_equal"] = (
        pd.to_numeric(merged["n_clusters_python"], errors="coerce")
        == pd.to_numeric(merged["n_clusters_r"], errors="coerce")
    )
    merged["status"] = np.where(
        merged["_merge"].eq("both")
        & merged["n_equal"]
        & merged["clusters_equal"]
        & merged["max_abs_difference"].le(TOLERANCE),
        "PASS",
        "FAIL",
    )
    return merged.drop(columns="_merge")


def parse_args() -> argparse.Namespace:
    workspace = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=workspace / "Replication Package",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    parser.add_argument(
        "--compare-only",
        action="store_true",
        help="Only compare existing python_results.csv and r_results.csv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    python_path = output_dir / "python_results.csv"
    r_path = output_dir / "r_results.csv"

    if not args.compare_only:
        package_root = resolve_package_root(args.package_root)
        data = prepare_analysis_input(package_root)
        data.to_csv(
            output_dir / "cross_language_input.csv",
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        estimate_python(data).to_csv(
            python_path,
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        print(f"Wrote Python replay for {len(OUTCOMES)} outcomes.")

    if r_path.is_file():
        comparison = compare_results(
            pd.read_csv(python_path),
            pd.read_csv(r_path),
        )
        comparison.to_csv(
            output_dir / "comparison.csv",
            index=False,
            float_format="%.17g",
            lineterminator="\n",
        )
        failures = int(comparison["status"].ne("PASS").sum())
        print(
            f"Wrote cross-language comparison with {failures} failure(s)."
        )
        return 1 if failures else 0

    print(f"R results not found yet: {r_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
