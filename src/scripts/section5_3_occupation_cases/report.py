"""Package navigation, hashes, technical validation, and audit helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    AGE_ORDER,
    AUDIT_DIR,
    BASELINE_PERIOD,
    CASE_ORDER,
    FIGURE_DIR,
    OUTPUT_ROOT,
    TABLE_DIR,
)


MAIN_FIGURE_STEMS = [
    "figure_5_3_1_occupation_cases_admissions_by_age",
    "figure_5_3_2_occupation_cases_real_admission_wage_by_age",
]
ALTERNATIVE_FIGURE_STEMS = [
    "figure_5_3_1a_occupation_cases_admissions_by_age",
    "figure_5_3_1b_occupation_cases_admissions_by_age",
    "figure_5_3_1c_occupation_cases_admissions_by_age",
    "figure_5_3_2a_occupation_cases_real_admission_wage_by_age",
    "figure_5_3_2b_occupation_cases_real_admission_wage_by_age",
    "figure_5_3_2c_occupation_cases_real_admission_wage_by_age",
]
APPENDIX_FIGURE_STEMS = [
    "figure_b_1_occupation_cases_by_sex",
    "figure_b_2_occupation_cases_by_race_color",
    "figure_b_3_occupation_cases_by_education",
]

EXPOSURE_ORACLES = {
    "software_developers": {
        "Exposed: Gradient 3": 64.6,
        "Exposed: Gradient 2": 29.9,
        "No score": 5.5,
    },
    "customer_service": {"Exposed: Gradient 3": 100.0},
    "marketing_sales_managers": {"Exposed: Gradient 2": 100.0},
    "production_supervisors": {
        "Not Exposed": 58.3,
        "Minimal Exposure": 5.5,
        "No score": 36.2,
    },
    "stock_clerks": {"Minimal Exposure": 100.0},
    "health_care_aides": {
        "Not Exposed": 62.4,
        "Minimal Exposure": 37.6,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_readme() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    text = """# Section 5.3 Occupation-Case Package

This package implements the descriptive occupation-case extension inspired by the six examples in *Canaries in the Coal Mine*. It does not estimate occupation-specific DiDs or event studies. The causal analysis remains the aggregate design in Sections 5.1–5.2.

## Design

- Semantic CBO6 selection was frozen before inspecting post-ChatGPT coefficients.
- The primary dictionary contains 76 non-overlapping CBO6 occupations in six cases.
- Official titles, tasks, and synonyms are preserved in `data/input/occupation_case_official_metadata.csv`; production does not depend on temporary downloads.
- CAGED admissions and positive admission wages are aggregated monthly from January 2021 through June 2025.
- To prevent demonstrably miscoded salaries from dominating case means, the main wage series winsorizes positive admission wages at P1/P99 within CBO6 and calendar year before aggregation. Raw means and the originally planned CBO6-group-month mean winsorization remain in the sensitivity matrix.
- Main paths use October 2022 = 1. The terminal metric is the January–June 2025 mean relative to that baseline.
- Sensitivities use both the January–October 2022 mean and month-matched January–June 2022 comparisons, which directly expose seasonal dependence.
- The ILO exposure composition is assigned only after semantic selection and weighted by January 2021–October 2022 admissions.
- `No score` means that no defensible exposure score is available; it never means zero exposure.
- Pre-period diagnostics are descriptive. They contain no causal pass/fail labels or significance stars.

## Main dissertation artifacts

- `tables/table_5_3_1_occupation_case_exposure_summary.{csv,md}`
- `figures/figure_5_3_1_occupation_cases_admissions_by_age.{png,pdf,svg}`
- `figures/figure_5_3_2_occupation_cases_real_admission_wage_by_age.{png,pdf,svg}`

## Selected layout and comparison exports

Layout `a` is the selected official design and is exported under the canonical Figure 5.3.1 and 5.3.2 filenames. The parallel `1a` and `2a` exports preserve the layout-selection trail. Two additional comparison layouts remain available:

- `a` (official): larger three-by-two trajectory panels with a case-specific vertical scale;
- `b`: one occupation per row, splitting ages 22–34 and 35+ into separate columns;
- `c`: an annotated six-by-six heatmap of the pre-specified January–June 2025 terminal metric.

Layouts `a` and `b` retain the monthly paths. Layout `c` is easier to scan across occupations and ages, but intentionally suppresses the monthly trajectory. All layouts are available as PNG, PDF, and SVG in `figures/`.

## Appendix artifacts

The `tables/` directory contains the full mapping, monthly paths, frozen terminal matrices, descriptive diagnostics, exposure details, all pre-specified sensitivities, and demographic comparisons. Figures B.1–B.3 are descriptive dumbbell charts for sex, race/color, and education.

## Blindspot ruling

The final audit is `audit/section5_3_blindspot_report.md`. Its ruling is `CONDITIONAL`: admissions carry the headline comparison; wage language is restricted to time-baseline-stable patterns; production supervisors receive an internal-composition caveat; and demographic findings remain descriptive.

## Reproduction

```bash
python src/scripts/build_section5_3_occupation_cases.py
```

Use `--reuse-cells` only when the cached CBO6 monthly cells were generated from the same frozen dictionary and raw inputs. The source inventory and artifact manifest contain SHA-256 hashes.
"""
    (OUTPUT_ROOT / "README.md").write_text(text, encoding="utf-8")


def build_source_inventory(
    source_paths: list[Path],
    *,
    include_hashes: bool,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in source_paths:
        if not path.exists():
            raise FileNotFoundError(path)
        rows.append(
            {
                "source_file": str(path),
                "bytes": path.stat().st_size,
                "modified_ns": path.stat().st_mtime_ns,
                "sha256": sha256_file(path) if include_hashes else "not_computed",
            }
        )
    return pd.DataFrame(rows)


def write_artifact_manifest() -> pd.DataFrame:
    """Hash every material artifact after generation, excluding the manifest itself."""
    excluded = {
        OUTPUT_ROOT / "MANIFEST.md",
        AUDIT_DIR / "artifact_manifest.csv",
        AUDIT_DIR / "artifact_manifest.md",
    }
    rows: list[dict[str, object]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if not path.is_file() or path in excluded:
            continue
        rows.append(
            {
                "artifact": str(path.relative_to(OUTPUT_ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = pd.DataFrame(rows)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(AUDIT_DIR / "artifact_manifest.csv", index=False)
    (AUDIT_DIR / "artifact_manifest.md").write_text(
        manifest.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "MANIFEST.md").write_text(
        "# Artifact Manifest\n\n"
        "All hashes below are SHA-256 hashes of the generated artifacts.\n\n"
        + manifest.to_markdown(index=False)
        + "\n",
        encoding="utf-8",
    )
    return manifest


def build_result_selection_log(
    terminal: pd.DataFrame,
    sensitivities: pd.DataFrame,
    diagnostics: pd.DataFrame,
    demographic_decisions: pd.DataFrame,
) -> pd.DataFrame:
    """Record every frozen primary result and its editorial placement."""
    focal = terminal[terminal["variant_id"].eq("primary")].copy()
    sensitivity_columns = [
        "case_id",
        "variant_id",
        "dimension",
        "group_id",
        "outcome",
        "alternative_normalization_change_pct",
        "same_month_change_pct",
        "normalization_delta_pp",
        "same_month_delta_pp",
        "raw_wage_delta_pp",
        "cell_mean_winsorization_delta_pp",
    ]
    focal = focal.merge(
        sensitivities[sensitivity_columns],
        on=["case_id", "variant_id", "dimension", "group_id", "outcome"],
        how="left",
        validate="one_to_one",
    )
    decision_lookup = demographic_decisions[
        ["dimension", "outcome", "mentionable_in_section5_3"]
    ].drop_duplicates(["dimension", "outcome"])
    focal = focal.merge(
        decision_lookup,
        on=["dimension", "outcome"],
        how="left",
        validate="many_to_one",
    )
    diagnostic_columns = [
        "case_id",
        "variant_id",
        "dimension",
        "group_id",
        "outcome",
        "pre_months_observed",
        "annualized_log_slope_pct",
        "coefficient_of_variation",
    ]
    focal = focal.merge(
        diagnostics[diagnostic_columns],
        on=["case_id", "variant_id", "dimension", "group_id", "outcome"],
        how="left",
        validate="one_to_one",
    )
    focal.insert(
        0,
        "result_id",
        focal.apply(
            lambda row: "__".join(
                [
                    str(row["case_id"]),
                    str(row["dimension"]),
                    str(row["group_id"]),
                    str(row["outcome"]),
                ]
            ),
            axis=1,
        ),
    )
    focal["eligible_for_review"] = (
        focal["support_status"].eq("adequate")
        & focal["terminal_months"].eq(6)
    )
    focal["stable_across_time_baselines"] = (
        np.sign(focal["terminal_change_pct"])
        .eq(np.sign(focal["alternative_normalization_change_pct"]))
        & np.sign(focal["terminal_change_pct"])
        .eq(np.sign(focal["same_month_change_pct"]))
    )

    def classify(row: pd.Series) -> tuple[str, str]:
        if not bool(row["eligible_for_review"]):
            return (
                "do_not_interpret",
                "The frozen support or terminal-window requirement is not satisfied.",
            )
        if row["dimension"] == "age" and row["outcome"] == "admissions":
            return (
                "main_text_headline",
                "Age-specific admissions are the pre-specified central comparison; all six cases remain visible.",
            )
        if row["dimension"] == "age" and row["outcome"] == "real_admission_wage":
            if bool(row["stable_across_time_baselines"]):
                return (
                    "main_text_context",
                    "The wage direction is stable under both alternative time baselines.",
                )
            return (
                "main_figure_only",
                "The wage path is shown, but its terminal direction changes under at least one time baseline.",
            )
        if row["dimension"] == "overall":
            if bool(row["stable_across_time_baselines"]):
                return (
                    "main_text_context",
                    "The case-level summary is stable under both alternative time baselines.",
                )
            return (
                "appendix_only",
                "The case-level summary changes direction under at least one time baseline.",
            )
        if bool(row.get("mentionable_in_section5_3", False)):
            return (
                "main_text_secondary",
                "This demographic dimension passes the frozen cross-case support, magnitude, and sensitivity rule.",
            )
        return (
            "appendix_only",
            "The demographic dimension does not pass the frozen cross-case mention rule.",
        )

    decisions = focal.apply(classify, axis=1, result_type="expand")
    focal[["selection_decision", "selection_reason"]] = decisions
    focal["selection_basis"] = (
        "Frozen terminal metric and pre-specified robustness rules; no significance filtering."
    )
    return focal[
        [
            "result_id",
            "case_id",
            "dimension",
            "group_id",
            "outcome",
            "terminal_change_pct",
            "support_status",
            "terminal_months",
            "alternative_normalization_change_pct",
            "same_month_change_pct",
            "normalization_delta_pp",
            "same_month_delta_pp",
            "raw_wage_delta_pp",
            "cell_mean_winsorization_delta_pp",
            "pre_months_observed",
            "annualized_log_slope_pct",
            "coefficient_of_variation",
            "eligible_for_review",
            "stable_across_time_baselines",
            "selection_decision",
            "selection_reason",
            "selection_basis",
        ]
    ].sort_values(["case_id", "dimension", "group_id", "outcome"]).reset_index(drop=True)


def _markdown_data_rows(path: Path) -> int:
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("|")
    ]
    return max(0, len(lines) - 2)


def validate_technical_package(
    *,
    dictionary: pd.DataFrame,
    paths: pd.DataFrame,
    terminal: pd.DataFrame,
    exposure_long: pd.DataFrame,
) -> pd.DataFrame:
    """Run hard acceptance gates and record non-fatal oracle investigations."""
    checks: list[dict[str, object]] = []

    primary = dictionary[dictionary["primary_included"]]
    checks.append(
        {
            "check": "primary_dictionary_76_unique_codes",
            "status": "pass"
            if len(primary) == 76 and not primary["cbo_6d"].duplicated().any()
            else "fail",
            "value": len(primary),
            "detail": "Frozen primary dictionary",
        }
    )

    supported = paths[paths["support_status"].eq("adequate")]
    baseline = supported[supported["period"].eq(BASELINE_PERIOD)]["path_index"]
    baseline_ok = not baseline.empty and np.allclose(baseline, 1.0, atol=1e-12, rtol=0)
    checks.append(
        {
            "check": "supported_october_paths_equal_one",
            "status": "pass" if baseline_ok else "fail",
            "value": len(baseline),
            "detail": "All supported outcomes and variants",
        }
    )

    age = terminal[
        terminal["variant_id"].eq("primary")
        & terminal["dimension"].eq("age")
    ]
    expected_age_cells = len(CASE_ORDER) * len(AGE_ORDER) * 2
    adequate_age_cells = int(age["support_status"].eq("adequate").sum())
    checks.append(
        {
            "check": "all_primary_case_age_outcomes_supported",
            "status": "pass"
            if len(age) == expected_age_cells and adequate_age_cells == expected_age_cells
            else "fail",
            "value": f"{adequate_age_cells}/{expected_age_cells}",
            "detail": "Six cases x six age groups x two outcomes",
        }
    )
    checks.append(
        {
            "check": "terminal_window_has_six_months",
            "status": "pass" if age["terminal_months"].eq(6).all() else "fail",
            "value": int(age["terminal_months"].min()) if not age.empty else 0,
            "detail": "January through June 2025",
        }
    )

    sums = exposure_long.groupby("case_id", observed=True)["share_pct"].sum()
    composition_ok = (
        set(sums.index) == set(CASE_ORDER)
        and np.allclose(sums.values, 100.0, atol=1e-8)
    )
    checks.append(
        {
            "check": "exposure_composition_sums_to_100",
            "status": "pass" if composition_ok else "fail",
            "value": len(sums),
            "detail": "No score retained as a separate category",
        }
    )

    exposure_lookup = exposure_long.set_index(["case_id", "exposure_category"])[
        "share_pct"
    ]
    for case_id, expected in EXPOSURE_ORACLES.items():
        for category, target in expected.items():
            actual = float(exposure_lookup.get((case_id, category), np.nan))
            delta = actual - target
            checks.append(
                {
                    "check": f"exposure_oracle__{case_id}__{category}",
                    "status": "pass" if np.isfinite(actual) and abs(delta) <= 0.25 else "investigate",
                    "value": round(actual, 3) if np.isfinite(actual) else np.nan,
                    "detail": f"Expected {target:.1f}; delta {delta:+.3f}",
                }
            )

    table_pairs = 0
    parity_ok = True
    for csv_path in sorted(TABLE_DIR.glob("*.csv")):
        md_path = csv_path.with_suffix(".md")
        if not md_path.exists():
            parity_ok = False
            continue
        table_pairs += 1
        if len(pd.read_csv(csv_path)) != _markdown_data_rows(md_path):
            parity_ok = False
    checks.append(
        {
            "check": "csv_markdown_row_parity",
            "status": "pass" if parity_ok and table_pairs > 0 else "fail",
            "value": table_pairs,
            "detail": "All generated table pairs",
        }
    )

    expected_figures = (
        MAIN_FIGURE_STEMS
        + ALTERNATIVE_FIGURE_STEMS
        + APPENDIX_FIGURE_STEMS
    )
    figure_files = [
        FIGURE_DIR / f"{stem}{suffix}"
        for stem in expected_figures
        for suffix in [".png", ".pdf", ".svg"]
    ]
    figure_ok = all(path.exists() and path.stat().st_size > 0 for path in figure_files)
    checks.append(
        {
            "check": "all_figure_exports_exist",
            "status": "pass" if figure_ok else "fail",
            "value": sum(path.exists() for path in figure_files),
            "detail": f"Expected {len(figure_files)} PNG/PDF/SVG files",
        }
    )

    validation = pd.DataFrame(checks)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    validation.to_csv(AUDIT_DIR / "validation_checks.csv", index=False)
    (AUDIT_DIR / "validation_checks.md").write_text(
        validation.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    failures = validation[validation["status"].eq("fail")]
    if not failures.empty:
        raise RuntimeError(
            "Section 5.3 technical validation failed:\n"
            + failures.to_string(index=False)
        )
    return validation
