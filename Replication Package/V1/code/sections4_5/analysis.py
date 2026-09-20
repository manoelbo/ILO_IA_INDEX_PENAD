"""Independent core-model replay and source-output contract validation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyfixest as pf

from common.validation import ValidationCheck
from .contracts import MAIN_CLUSTER, MAIN_CONTROLS, MAIN_FIXED_EFFECTS


CORE_OUTCOMES = (
    ("ln_admissoes", "main_results_3plus1.csv", "ln_admissoes"),
    ("ln_desligamentos", "main_results_3plus1.csv", "ln_desligamentos"),
    ("ln_salario_adm", "main_results_3plus1.csv", "ln_salario_adm"),
    ("asinh_saldo", "net_flow_results.csv", "asinh_saldo"),
)


def _pass_fail(
    check_id: str,
    condition: bool,
    observed: object,
    expected: object,
    detail: str,
) -> ValidationCheck:
    return ValidationCheck(
        check_id=check_id,
        status="PASS" if condition else "FAIL",
        observed=observed,
        expected=expected,
        detail=detail,
    )


def _main_analysis_data(data_root: Path) -> pd.DataFrame:
    panel = pd.read_parquet(data_root / "data/output/painel_2b_ready.parquet")
    roles = pd.read_csv(
        data_root
        / "outputs/treatment_scenario_grid/scenario_cbo_classification.csv",
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
    return data


def reestimate_core_models(
    data_root: Path,
    output_path: Path,
) -> tuple[pd.DataFrame, list[ValidationCheck]]:
    """Re-estimate the national DiD and the main net-flow specification."""
    data = _main_analysis_data(data_root)
    source_dir = data_root / "backing_data" / "national_event_study"
    source_frames = {
        filename: pd.read_csv(source_dir / filename)
        for filename in {item[1] for item in CORE_OUTCOMES}
    }
    rows: list[dict[str, object]] = []
    checks: list[ValidationCheck] = []
    controls = " + ".join(MAIN_CONTROLS)
    fixed_effects = " + ".join(MAIN_FIXED_EFFECTS)

    for outcome, filename, source_outcome in CORE_OUTCOMES:
        formula = f"{outcome} ~ post_treat + {controls} | {fixed_effects}"
        model = pf.feols(
            formula,
            data=data,
            vcov={"CRV1": MAIN_CLUSTER},
        )
        tidy = model.tidy().loc["post_treat"]
        source = source_frames[filename]
        source_row = source.loc[source["outcome"].eq(source_outcome)].iloc[0]
        row = {
            "outcome": outcome,
            "term": "post_treat",
            "coef": float(tidy["Estimate"]),
            "se": float(tidy["Std. Error"]),
            "p_value": float(tidy["Pr(>|t|)"]),
            "n_obs": int(model._N),
            "n_cbo": int(data["cbo_4d"].nunique()),
            "formula": formula,
            "fixed_effects": fixed_effects,
            "vcov": "CRV1",
            "cluster": MAIN_CLUSTER,
            "source_file": (
                f"backing_data/national_event_study/{filename}"
            ),
            "source_coef": float(source_row["coef"]),
            "source_se": float(source_row["se"]),
            "source_p_value": float(source_row["p_value"]),
        }
        row["max_abs_difference"] = max(
            abs(row["coef"] - row["source_coef"]),
            abs(row["se"] - row["source_se"]),
            abs(row["p_value"] - row["source_p_value"]),
        )
        rows.append(row)
        checks.append(
            _pass_fail(
                f"core_reestimation_{outcome}",
                bool(row["max_abs_difference"] <= 1e-12)
                and int(model._N) == int(source_row["n_obs"]),
                f"max_abs_diff={row['max_abs_difference']:.3e}; n={model._N}",
                "max_abs_diff<=1e-12 and identical retained N",
                "Independent pyfixest replay with CBO4 and month fixed effects "
                "and CRV1 CBO4 clustering.",
            )
        )

    result = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, lineterminator="\n")
    return result, checks


def validate_empirical_output_contracts(
    data_root: Path,
) -> list[ValidationCheck]:
    """Validate formulas, dynamic grids, binary DDD symmetry, and robustness."""
    source_dir = data_root / "backing_data" / "national_event_study"
    main = pd.read_csv(source_dir / "main_results_3plus1.csv")
    ddd = pd.read_csv(source_dir / "heterogeneity_triple_did_long.csv")
    ddd_wage = pd.read_csv(
        source_dir / "heterogeneity_real_wage_triple_did_long.csv"
    )
    ddd_net = pd.read_csv(source_dir / "net_flow_heterogeneity_long.csv")
    poisson = pd.read_csv(source_dir / "poisson_flow_results.csv")
    occupation_dir = (
        data_root / "backing_data" / "section5_3_occupation_cases"
    )
    occupation_paths = pd.read_csv(
        occupation_dir / "occupation_case_monthly_paths.csv"
    )
    occupation_sensitivity = pd.read_csv(
        occupation_dir / "occupation_case_sensitivity_matrix.csv"
    )
    record_winsor = pd.read_csv(
        occupation_dir / "occupation_case_record_wage_winsor_bounds.csv"
    )
    cell_winsor = pd.read_csv(
        occupation_dir / "occupation_case_wage_winsor_bounds.csv"
    )
    dynamic_paths = (
        data_root
        / "backing_data"
        / "section5_2_dynamic"
        / "event_study_coefficients_long.csv"
    )
    age_paths = (
        data_root
        / "backing_data"
        / "section5_2_age_pnad"
        / "event_study_coefficients_long.csv"
    )
    checks: list[ValidationCheck] = []

    required_main_terms = {
        "post_treat",
        *MAIN_CONTROLS,
        "cbo_4d",
        "periodo",
    }
    main_formula_ok = all(
        all(term in str(formula) for term in required_main_terms)
        for formula in main["formula"]
    )
    checks.append(
        _pass_fail(
            "main_formula_contract",
            main_formula_ok
            and set(main["cluster"]) == {MAIN_CLUSTER}
            and set(main["model_type"]) == {"ols"},
            "formula terms, cluster, and model type",
            "post_treat + four controls | CBO4 + month; CRV1 by CBO4",
            "National model contract recorded in full-precision source results.",
        )
    )

    ddd_frames = [ddd, ddd_wage, ddd_net]
    required_ddd_terms = (
        "post_treat_group",
        "post_treat",
        "post_group",
        "treat_group",
    )
    ddd_formula_ok = all(
        all(
            all(term in str(model) for term in required_ddd_terms)
            for model in frame.loc[
                frame["result_status"].eq("estimated"), "model"
            ].dropna()
        )
        for frame in ddd_frames
    )
    checks.append(
        _pass_fail(
            "ddd_formula_contract",
            ddd_formula_ok,
            required_ddd_terms if ddd_formula_ok else "missing term",
            required_ddd_terms,
            "Every estimated DDD includes the triple interaction and all "
            "lower-order interactions.",
        )
    )

    dynamic_ok = True
    dynamic_detail: list[str] = []
    for path in (dynamic_paths, age_paths):
        frame = pd.read_csv(path)
        observed_grid = set(pd.to_numeric(frame["t"], errors="raise").astype(int))
        expected_grid = set(range(-12, 25))
        reference = frame[frame["is_reference"].astype(bool)]
        reference_coef = pd.to_numeric(reference["coef"], errors="coerce")
        file_ok = (
            observed_grid == expected_grid
            and set(reference["t"].astype(int)) == {-1}
            and bool(np.allclose(reference_coef, 0.0, atol=0.0))
        )
        dynamic_ok = dynamic_ok and file_ok
        dynamic_detail.append(f"{path.name}:{len(frame)} rows")
    checks.append(
        _pass_fail(
            "dynamic_event_time_contract",
            dynamic_ok,
            "; ".join(dynamic_detail),
            "complete -12,...,24 grid and zero t=-1 reference",
            "Static and heterogeneous event-study backing grids.",
        )
    )

    mirror_checks: list[bool] = []
    for frame in ddd_frames:
        subset = frame[
            frame["dimension"].eq("race_color_b")
            & frame["group_id"].isin(("race_white", "race_black_combined"))
        ]
        pivot = subset.pivot(
            index="outcome",
            columns="group_id",
            values="coef",
        )
        mirror_checks.append(
            not pivot.empty
            and bool(
                np.allclose(
                    pivot["race_white"] + pivot["race_black_combined"],
                    0.0,
                    atol=1e-10,
                    equal_nan=False,
                )
            )
        )
    checks.append(
        _pass_fail(
            "binary_race_ddd_mirroring",
            all(mirror_checks),
            mirror_checks,
            [True, True, True],
            "Branca and Negra binary DDD coefficients must be exact mirrors.",
        )
    )

    poisson_ok = (
        len(poisson) == 6
        and set(poisson["model_type"]) == {"poisson"}
        and set(poisson["cluster"]) == {MAIN_CLUSTER}
        and poisson["result_status"].eq("estimated").all()
    )
    checks.append(
        _pass_fail(
            "poisson_robustness_contract",
            bool(poisson_ok),
            f"{len(poisson)} rows; statuses={set(poisson['result_status'])}",
            "6 estimated Poisson rows clustered by CBO4",
            "Count-model robustness for admissions and separations.",
        )
    )

    primary_age_paths = occupation_paths[
        occupation_paths["variant_id"].eq("primary")
        & occupation_paths["dimension"].eq("age")
    ]
    primary_age_sensitivity = occupation_sensitivity[
        occupation_sensitivity["variant_id"].eq("primary")
        & occupation_sensitivity["dimension"].eq("age")
    ]
    path_cells = primary_age_paths[
        ["case_id", "group_id", "outcome", "period"]
    ].drop_duplicates()
    sensitivity_cells = primary_age_sensitivity[
        ["case_id", "group_id", "outcome"]
    ].drop_duplicates()
    occupation_coverage_ok = (
        len(path_cells) == 6 * 6 * 2 * 54
        and len(sensitivity_cells) == 6 * 6 * 2
        and primary_age_paths["case_id"].nunique() == 6
        and primary_age_paths["group_id"].nunique() == 6
        and set(primary_age_paths["outcome"])
        == {"admissions", "real_admission_wage"}
        and primary_age_paths["period"].nunique() == 54
    )
    checks.append(
        _pass_fail(
            "occupation_case_age_outcome_coverage",
            bool(occupation_coverage_ok),
            (
                f"paths={len(path_cells)}; sensitivities={len(sensitivity_cells)}; "
                f"cases={primary_age_paths['case_id'].nunique()}; "
                f"ages={primary_age_paths['group_id'].nunique()}; "
                f"months={primary_age_paths['period'].nunique()}"
            ),
            "3888 monthly cells and 72 sensitivity cells (6×6×2)",
            "Complete primary occupation-case coverage across cases, ages, "
            "outcomes, and months.",
        )
    )

    record_quantiles = set(
        zip(
            pd.to_numeric(record_winsor["lower_quantile"]),
            pd.to_numeric(record_winsor["upper_quantile"]),
        )
    )
    cell_quantiles = set(
        zip(
            pd.to_numeric(cell_winsor["lower_quantile"]),
            pd.to_numeric(cell_winsor["upper_quantile"]),
        )
    )
    winsor_contract_ok = (
        record_quantiles == {(0.01, 0.99)}
        and cell_quantiles == {(0.01, 0.99)}
        and all("winsor" not in str(formula).lower() for formula in main["formula"])
    )
    checks.append(
        _pass_fail(
            "winsorization_contract",
            bool(winsor_contract_ok),
            (
                f"record={sorted(record_quantiles)}; "
                f"cell_sensitivity={sorted(cell_quantiles)}; "
                "main_regression=unwinsorized"
            ),
            (
                "unwinsorized regressions; P1/P99 descriptive paths; "
                "P1/P99 within CBO6-year for occupation-case main wages"
            ),
            "Distinct regression, trajectory, and occupation-case wage rules "
            "remain separately identified in backing data and source code.",
        )
    )
    return checks
