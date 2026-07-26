#!/usr/bin/env python3
"""Run the exact V1 national specification on the refreshed V2 panel."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyfixest as pf


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_V1_REFERENCE = (
    PACKAGE_ROOT.parent
    / "V1"
    / "results"
    / "reference"
    / "sections4_5"
    / "backing_data"
    / "core_model_reestimation.csv"
)
DEFAULT_OUTPUT = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "gate_modelo_antigo.csv"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "GATE_MODELO_ANTIGO.md"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "gate_modelo_antigo_support.json"
)
START_PERIOD = 202101
END_PERIOD = 202506
CONTROLS = (
    "idade_media_adm",
    "pct_mulher_adm",
    "pct_superior_adm",
    "pct_negra_adm",
)
FIXED_EFFECTS = ("cbo_4d", "periodo")
CLUSTER = "cbo_4d"
OUTCOME_MAP = {
    "ln_admissoes": "ln_admissoes",
    "ln_desligamentos": "ln_desligamentos",
    "ln_salario_adm": "ln_salario_real_adm",
    "asinh_saldo": "asinh_saldo",
}
PREREGISTERED_COEFFICIENTS = {
    "ln_admissoes": -0.03087879481033855,
    "ln_desligamentos": -0.04165839040785939,
    "ln_salario_real_adm": -0.020706489590455807,
    "asinh_saldo": -0.6596605902038598,
}


def prepare_gate_data(
    panel: pd.DataFrame,
    *,
    start_period: int = START_PERIOD,
    end_period: int = END_PERIOD,
) -> pd.DataFrame:
    required = {
        "cbo_4d",
        "periodo_num",
        "periodo",
        "post",
        "included_main",
        "treated_main",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"National panel is missing columns: {missing}")
    data = panel.loc[
        panel["periodo_num"].between(start_period, end_period)
        & panel["included_main"].eq(True)
    ].copy()
    if data["treated_main"].isna().any():
        raise RuntimeError(
            "Main treatment sample contains missing treatment assignments"
        )
    data["cbo_4d"] = data["cbo_4d"].astype("string").str.zfill(4)
    data["periodo"] = data["periodo"].astype("string")
    data["post_treat"] = (
        pd.to_numeric(data["post"], errors="raise")
        * pd.to_numeric(data["treated_main"], errors="raise")
    )
    return data.sort_values(["cbo_4d", "periodo_num"]).reset_index(
        drop=True
    )


def load_v1_reference(path: Path) -> pd.DataFrame:
    source = pd.read_csv(path)
    source = source.loc[
        source["outcome"].isin(OUTCOME_MAP)
    ].copy()
    if len(source) != len(OUTCOME_MAP):
        raise RuntimeError("V1 reference does not contain four core outcomes")
    source["v1_outcome"] = source["outcome"]
    source["outcome"] = source["outcome"].map(OUTCOME_MAP)
    reference = source.rename(
        columns={
            "coef": "v1_coef",
            "se": "v1_se",
            "p_value": "v1_p_value",
        }
    )[
        [
            "outcome",
            "v1_outcome",
            "v1_coef",
            "v1_se",
            "v1_p_value",
        ]
    ]
    observed = reference.set_index("outcome")["v1_coef"].to_dict()
    for outcome, expected in PREREGISTERED_COEFFICIENTS.items():
        if not np.isclose(
            observed.get(outcome, np.nan),
            expected,
            rtol=0,
            atol=1e-14,
        ):
            raise RuntimeError(
                f"V1 reference drift for {outcome}: "
                f"{observed.get(outcome)} != {expected}"
            )
    return reference.reset_index(drop=True)


def estimate_v2_models(data: pd.DataFrame) -> pd.DataFrame:
    controls = " + ".join(CONTROLS)
    fixed_effects = " + ".join(FIXED_EFFECTS)
    rows: list[dict[str, Any]] = []
    for outcome in OUTCOME_MAP.values():
        required = [
            outcome,
            "post_treat",
            *CONTROLS,
            *FIXED_EFFECTS,
        ]
        model_data = data.dropna(subset=required).copy()
        formula = (
            f"{outcome} ~ post_treat + {controls} | {fixed_effects}"
        )
        model = pf.feols(
            formula,
            data=model_data,
            vcov={"CRV1": CLUSTER},
        )
        tidy = model.tidy().loc["post_treat"]
        rows.append(
            {
                "outcome": outcome,
                "v2_coef": float(tidy["Estimate"]),
                "v2_se": float(tidy["Std. Error"]),
                "v2_p_value": float(tidy["Pr(>|t|)"]),
                "n_obs": int(model._N),
                "n_cbo": int(model_data["cbo_4d"].nunique()),
                "formula": formula,
                "fixed_effects": fixed_effects,
                "vcov": "CRV1",
                "cluster": CLUSTER,
            }
        )
    return pd.DataFrame(rows)


def validate_coefficients_with_fwl(
    data: pd.DataFrame,
    estimates: pd.DataFrame,
    *,
    tolerance: float = 1e-10,
) -> float:
    reported = estimates.set_index("outcome")["v2_coef"]
    differences: list[float] = []
    variables = ["post_treat", *CONTROLS]
    for outcome in OUTCOME_MAP.values():
        model_data = data.dropna(
            subset=[outcome, *variables, *FIXED_EFFECTS]
        ).copy()
        matrix = model_data[
            [outcome, *variables]
        ].to_numpy(dtype=float)
        for _ in range(1_000):
            previous = matrix.copy()
            frame = pd.DataFrame(matrix, index=model_data.index)
            matrix -= frame.groupby(
                model_data["cbo_4d"],
                observed=True,
            ).transform("mean").to_numpy()
            frame = pd.DataFrame(matrix, index=model_data.index)
            matrix -= frame.groupby(
                model_data["periodo"],
                observed=True,
            ).transform("mean").to_numpy()
            if np.max(np.abs(matrix - previous)) < 1e-12:
                break
        else:
            raise RuntimeError(
                f"FWL fixed-effect absorption did not converge: {outcome}"
            )
        coefficient = float(
            np.linalg.lstsq(
                matrix[:, 1:],
                matrix[:, 0],
                rcond=None,
            )[0][0]
        )
        differences.append(abs(coefficient - reported[outcome]))
    maximum = max(differences)
    if maximum > tolerance:
        raise RuntimeError(
            "Independent FWL coefficient validation failed: "
            f"{maximum:.3e} > {tolerance:.3e}"
        )
    return maximum


def build_comparison(
    reference: pd.DataFrame,
    estimates: pd.DataFrame,
) -> pd.DataFrame:
    comparison = reference.merge(
        estimates,
        on="outcome",
        how="inner",
        validate="one_to_one",
    )
    if comparison.empty:
        raise RuntimeError("V1-V2 model comparison is empty")
    comparison["delta"] = (
        comparison["v2_coef"] - comparison["v1_coef"]
    )
    comparison["delta_abs"] = comparison["delta"].abs()
    comparison["delta_pct"] = (
        comparison["delta"]
        / comparison["v1_coef"].abs().replace(0, np.nan)
        * 100.0
    )
    comparison["v1_significant_5pct"] = (
        comparison["v1_p_value"] < 0.05
    )
    comparison["v2_significant_5pct"] = (
        comparison["v2_p_value"] < 0.05
    )
    comparison["changed_sign"] = (
        np.sign(comparison["v1_coef"])
        != np.sign(comparison["v2_coef"])
    )
    comparison["crossed_significance_5pct"] = (
        comparison["v1_significant_5pct"]
        != comparison["v2_significant_5pct"]
    )
    return comparison


def summarize_comparison(
    comparison: pd.DataFrame,
    *,
    fwl_max_abs_difference: float | None = None,
) -> dict[str, Any]:
    sign_changes = comparison.loc[
        comparison["changed_sign"],
        "outcome",
    ].tolist()
    significance_crossings = comparison.loc[
        comparison["crossed_significance_5pct"],
        "outcome",
    ].tolist()
    summary = {
        "outcomes": int(len(comparison)),
        "sign_change_outcomes": sign_changes,
        "sign_changes": len(sign_changes),
        "significance_5pct_crossing_outcomes": significance_crossings,
        "significance_5pct_crossings": len(significance_crossings),
        "window_start": START_PERIOD,
        "window_end": END_PERIOD,
        "treatment_contrast": (
            "Exposed gradients 1-4 versus Not Exposed; "
            "Minimal Exposure and No score excluded"
        ),
    }
    if fwl_max_abs_difference is not None:
        summary["independent_fwl_validation"] = "pass"
        summary["fwl_max_abs_coefficient_difference"] = (
            fwl_max_abs_difference
        )
    return summary


def render_report(
    comparison: pd.DataFrame,
    summary: dict[str, Any],
) -> str:
    lines = [
        "# V1 Specification on the V2 Panel",
        "",
        "The exact V1 OLS specification was re-estimated on the refreshed "
        "national panel for January 2021-June 2025, with the original "
        "four admission-composition controls, CBO4 and month fixed effects, "
        "and CRV1 standard errors clustered by CBO4.",
        "",
        "| Outcome | V1 coefficient (SE) | V2 coefficient (SE) | "
        "Delta | Delta vs V1 | Sign change | 5% significance crossing |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in comparison.itertuples(index=False):
        lines.append(
            f"| {row.outcome} | {row.v1_coef:.6f} "
            f"({row.v1_se:.6f}) | {row.v2_coef:.6f} "
            f"({row.v2_se:.6f}) | {row.delta:+.6f} | "
            f"{row.delta_pct:+.1f}% | "
            f"{'yes' if row.changed_sign else 'no'} | "
            f"{'yes' if row.crossed_significance_5pct else 'no'} |"
        )
    sign_outcomes = summary["sign_change_outcomes"]
    significance_outcomes = summary[
        "significance_5pct_crossing_outcomes"
    ]
    lines.extend(
        [
            "",
            "## Explicit gate declarations",
            "",
            (
                "Sign changes: "
                + (", ".join(sign_outcomes) if sign_outcomes else "none.")
            ),
            (
                "Crossings of the 5% significance threshold: "
                + (
                    ", ".join(significance_outcomes)
                    if significance_outcomes
                    else "none."
                )
            ),
            "",
            "Checkpoint C is a non-blocking measurement checkpoint. These "
            "results are reported regardless of direction or significance.",
            "",
        ]
    )
    if "fwl_max_abs_coefficient_difference" in summary:
        lines.extend(
            [
                "The four coefficients were independently reproduced by "
                "iterative Frisch-Waugh-Lovell fixed-effect absorption; "
                "the maximum absolute difference from `pyfixest` was "
                f"{summary['fwl_max_abs_coefficient_difference']:.3e}.",
                "",
            ]
        )
    return "\n".join(lines)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_artifacts(
    comparison: pd.DataFrame,
    summary: dict[str, Any],
    output_path: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
    support_path: Path = DEFAULT_SUPPORT,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    comparison.to_csv(temporary, index=False)
    os.replace(temporary, output_path)
    _atomic_text(render_report(comparison, summary), report_path)
    _atomic_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        support_path,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the exact V1 model specification on the V2 panel."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument(
        "--v1-reference",
        type=Path,
        default=DEFAULT_V1_REFERENCE,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    panel = pd.read_parquet(args.panel)
    data = prepare_gate_data(panel)
    reference = load_v1_reference(args.v1_reference)
    estimates = estimate_v2_models(data)
    fwl_max_abs_difference = validate_coefficients_with_fwl(
        data,
        estimates,
    )
    comparison = build_comparison(reference, estimates)
    if len(comparison) != len(OUTCOME_MAP):
        raise RuntimeError("V1-V2 model comparison is incomplete")
    summary = summarize_comparison(
        comparison,
        fwl_max_abs_difference=fwl_max_abs_difference,
    )
    write_artifacts(
        comparison,
        summary,
        args.output,
        args.report,
        args.support,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
