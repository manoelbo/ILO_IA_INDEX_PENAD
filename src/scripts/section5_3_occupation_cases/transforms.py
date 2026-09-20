"""Pure recoding and transformation helpers for occupation-case outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    BASELINE_PERIOD,
    CASE_ORDER,
    CASE_SHORT_LABELS,
    DEMOGRAPHIC_SPECS,
    DIMENSION_GROUPS,
    END_PERIOD,
    MIN_BASELINE_SUPPORT,
    START_PERIOD,
    TERMINAL_END,
    TERMINAL_START,
)


def normalize_codes(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def assign_age_group(age: pd.Series) -> pd.Series:
    values = pd.to_numeric(age, errors="coerce")
    group = pd.Series(pd.NA, index=age.index, dtype="string")
    group.loc[values.between(22, 25, inclusive="both")] = "age_22_25"
    group.loc[values.between(26, 30, inclusive="both")] = "age_26_30"
    group.loc[values.between(31, 34, inclusive="both")] = "age_31_34"
    group.loc[values.between(35, 40, inclusive="both")] = "age_35_40"
    group.loc[values.between(41, 49, inclusive="both")] = "age_41_49"
    group.loc[values.ge(50)] = "age_50_plus"
    return group


def assign_demographic_group(frame: pd.DataFrame, dimension: str) -> pd.Series:
    group = pd.Series(pd.NA, index=frame.index, dtype="string")
    if dimension == "sex":
        codes = normalize_codes(frame["sexo"])
        group.loc[codes.eq("1")] = "men"
        group.loc[codes.eq("3")] = "women"
        return group
    if dimension == "race_color":
        codes = normalize_codes(frame["raca_cor"])
        group.loc[codes.eq("1")] = "race_white"
        group.loc[codes.isin(["2", "3"])] = "race_black_combined"
        return group
    if dimension == "education":
        codes = normalize_codes(frame["grau_instrucao"])
        group.loc[codes.isin(["1", "2", "3", "4", "5", "6", "7"])] = "education_other"
        group.loc[codes.isin(["8", "9", "10", "11", "80"])] = "higher_education"
        return group
    raise ValueError(f"Unsupported demographic dimension: {dimension}")


def build_membership_table(dictionary: pd.DataFrame) -> pd.DataFrame:
    """Expand semicolon-delimited dictionary variants into auditable membership rows."""
    rows: list[dict[str, str]] = []
    for row in dictionary.itertuples(index=False):
        variants = [value for value in str(row.variant_membership).split(";") if value]
        for variant_id in variants:
            if variant_id == "excluded":
                continue
            if variant_id == "primary" and not bool(row.primary_included):
                continue
            rows.append(
                {
                    "case_id": str(row.case_id),
                    "variant_id": variant_id,
                    "cbo_6d": str(row.cbo_6d).zfill(6),
                }
            )
    out = pd.DataFrame(rows).drop_duplicates()
    if out.duplicated(["case_id", "variant_id", "cbo_6d"]).any():
        raise RuntimeError("Occupation membership table contains duplicate rows.")
    return out.sort_values(["case_id", "variant_id", "cbo_6d"]).reset_index(drop=True)


def _prepare_ipca(ipca: pd.DataFrame) -> pd.DataFrame:
    out = ipca.copy()
    if "period" not in out.columns:
        if not {"ano", "mes"}.issubset(out.columns):
            raise RuntimeError("IPCA input must contain period or ano/mes columns.")
        out["period"] = (
            pd.to_numeric(out["ano"], errors="coerce").astype("Int64").astype(str)
            + "-"
            + pd.to_numeric(out["mes"], errors="coerce").astype("Int64").astype(str).str.zfill(2)
        )
    out["indice"] = pd.to_numeric(out["indice"], errors="coerce")
    if out["period"].duplicated().any() or out["indice"].isna().any() or out["indice"].le(0).any():
        raise RuntimeError("IPCA input contains duplicate, missing, or non-positive values.")
    return out[["period", "indice"]]


def aggregate_case_cells(
    cells: pd.DataFrame,
    membership: pd.DataFrame,
    ipca: pd.DataFrame,
    *,
    winsorize_wages: bool = False,
    lower_q: float = 0.01,
    upper_q: float = 0.99,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate CBO-level admission cells into case-variant monthly panels."""
    if not 0 <= lower_q < upper_q <= 1:
        raise ValueError("Wage winsorization quantiles must satisfy 0 <= lower < upper <= 1.")
    required = {
        "cbo_6d",
        "dimension",
        "group_id",
        "period",
        "admissions",
        "wage_sum",
        "wage_count",
    }
    missing = sorted(required - set(cells.columns))
    if missing:
        raise RuntimeError(f"Occupation cell input is missing columns: {missing}")
    data = cells.copy()
    data["cbo_6d"] = data["cbo_6d"].astype(str).str.zfill(6)
    for column in ["admissions", "wage_sum", "wage_count"]:
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)
    data["cell_wage"] = np.where(
        data["wage_count"].gt(0),
        data["wage_sum"] / data["wage_count"],
        np.nan,
    )

    bounds_rows: list[dict[str, object]] = []
    data["adjusted_cell_wage"] = data["cell_wage"]
    if winsorize_wages:
        for dimension, index in data.groupby("dimension", observed=True).groups.items():
            wages = data.loc[index, "cell_wage"].dropna()
            if wages.empty:
                continue
            lower, upper = wages.quantile([lower_q, upper_q]).astype(float)
            data.loc[index, "adjusted_cell_wage"] = data.loc[index, "cell_wage"].clip(lower, upper)
            bounds_rows.append(
                {
                    "dimension": dimension,
                    "lower_quantile": lower_q,
                    "upper_quantile": upper_q,
                    "lower_bound": lower,
                    "upper_bound": upper,
                }
            )
    data["adjusted_wage_sum"] = data["adjusted_cell_wage"] * data["wage_count"]
    joined = data.merge(
        membership[["case_id", "variant_id", "cbo_6d"]],
        on="cbo_6d",
        how="inner",
        validate="many_to_many",
    )
    keys = ["case_id", "variant_id", "dimension", "group_id", "period"]
    out = (
        joined.groupby(keys, observed=True)
        .agg(
            admissions=("admissions", "sum"),
            wage_sum=("adjusted_wage_sum", "sum"),
            wage_count=("wage_count", "sum"),
            n_cbo_observed=("cbo_6d", "nunique"),
        )
        .reset_index()
    )
    out["nominal_admission_wage"] = np.where(
        out["wage_count"].gt(0),
        out["wage_sum"] / out["wage_count"],
        np.nan,
    )
    out = out.merge(_prepare_ipca(ipca), on="period", how="left", validate="many_to_one")
    if out["indice"].isna().any():
        missing_periods = sorted(out.loc[out["indice"].isna(), "period"].unique())
        raise RuntimeError(f"Missing IPCA values for occupation-case periods: {missing_periods}")
    out["real_admission_wage"] = out["nominal_admission_wage"] * (100.0 / out["indice"])
    out["admissions"] = out["admissions"].round().astype(int)
    out["wage_count"] = out["wage_count"].round().astype(int)
    bounds = pd.DataFrame(
        bounds_rows,
        columns=[
            "dimension",
            "lower_quantile",
            "upper_quantile",
            "lower_bound",
            "upper_bound",
        ],
    )
    return out.sort_values(keys).reset_index(drop=True), bounds


def complete_case_panel(
    panel: pd.DataFrame,
    membership: pd.DataFrame,
    ipca: pd.DataFrame,
) -> pd.DataFrame:
    """Complete every case-variant-group month without fabricating wage values."""
    keys = ["case_id", "variant_id", "dimension", "group_id", "period"]
    missing = sorted(set(keys) - set(panel.columns))
    if missing:
        raise RuntimeError(f"Observed case panel is missing columns: {missing}")
    if panel.duplicated(keys).any():
        raise RuntimeError("Observed case panel contains duplicate case-group-month rows.")

    case_variants = membership[["case_id", "variant_id"]].drop_duplicates()
    periods = (
        pd.period_range(START_PERIOD, END_PERIOD, freq="M")
        .astype(str)
        .tolist()
    )
    rows: list[dict[str, str]] = []
    for case_id, variant_id in case_variants.itertuples(index=False):
        for dimension, groups in DIMENSION_GROUPS.items():
            for group_id, _label in groups:
                rows.extend(
                    {
                        "case_id": case_id,
                        "variant_id": variant_id,
                        "dimension": dimension,
                        "group_id": group_id,
                        "period": period,
                    }
                    for period in periods
                )
    grid = pd.DataFrame(rows)
    observed_keys = panel[keys]
    outside = observed_keys.merge(grid, on=keys, how="left", indicator=True)
    if outside["_merge"].eq("left_only").any():
        sample = outside[outside["_merge"].eq("left_only")].head()
        raise RuntimeError(f"Observed panel contains unexpected groups:\n{sample.to_string(index=False)}")
    out = grid.merge(panel, on=keys, how="left", validate="one_to_one")
    for column in ["admissions", "wage_sum", "wage_count", "n_cbo_observed"]:
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0)
    out["admissions"] = out["admissions"].astype(int)
    out["wage_count"] = out["wage_count"].astype(int)
    out["n_cbo_observed"] = out["n_cbo_observed"].astype(int)
    out["nominal_admission_wage"] = out["nominal_admission_wage"].where(
        out["wage_count"].gt(0)
    )
    out["real_admission_wage"] = out["real_admission_wage"].where(
        out["wage_count"].gt(0)
    )
    out = out.drop(columns=["indice"], errors="ignore").merge(
        _prepare_ipca(ipca),
        on="period",
        how="left",
        validate="many_to_one",
    )
    if out["indice"].isna().any():
        raise RuntimeError("Completed case panel has periods without IPCA.")
    sizes = (
        membership.groupby(["case_id", "variant_id"], observed=True)["cbo_6d"]
        .nunique()
        .rename("n_cbo_in_variant")
        .reset_index()
    )
    out = out.merge(sizes, on=["case_id", "variant_id"], how="left", validate="many_to_one")
    return out.sort_values(keys).reset_index(drop=True)


def normalize_case_paths(
    panel: pd.DataFrame,
    *,
    baseline_period: str = BASELINE_PERIOD,
    baseline_window: tuple[str, str] | None = None,
    min_support: int = MIN_BASELINE_SUPPORT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize admissions and wages and compute the frozen terminal-window summary."""
    required = {
        "case_id",
        "variant_id",
        "dimension",
        "group_id",
        "period",
        "admissions",
        "wage_count",
        "real_admission_wage",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Case panel is missing columns: {missing}")
    data = panel.copy()
    keys = ["case_id", "variant_id", "dimension", "group_id"]
    outcome_specs = [
        ("admissions", "admissions", "admissions"),
        ("real_admission_wage", "real_admission_wage", "wage_count"),
    ]
    path_rows: list[pd.DataFrame] = []
    terminal_rows: list[dict[str, object]] = []
    for outcome, value_column, support_column in outcome_specs:
        selected = data[keys + ["period"]].copy()
        selected["value"] = data[value_column]
        selected["support_value"] = data[support_column]
        baseline_source = (
            selected[selected["period"].eq(baseline_period)]
            if baseline_window is None
            else selected[selected["period"].between(*baseline_window)]
        )
        baseline = (
            baseline_source.groupby(keys, observed=True)["value"]
            .mean()
            .rename("baseline_value")
            .reset_index()
        )
        support = (
            selected[selected["period"].eq(baseline_period)]
            .groupby(keys, observed=True)["support_value"]
            .first()
            .rename("baseline_support")
            .reset_index()
        )
        baseline = baseline.merge(support, on=keys, how="left", validate="one_to_one")
        selected = selected.merge(baseline, on=keys, how="left", validate="many_to_one")
        supported = (
            selected["baseline_support"].ge(min_support)
            & selected["baseline_value"].gt(0)
            & selected["baseline_value"].notna()
        )
        selected["support_status"] = np.where(
            supported,
            "adequate",
            "suppressed_pre_support",
        )
        selected["path_index"] = np.where(
            supported & selected["value"].notna(),
            selected["value"] / selected["baseline_value"],
            np.nan,
        )
        selected["outcome"] = outcome
        selected["baseline_rule"] = (
            f"{baseline_window[0]}_to_{baseline_window[1]}_mean"
            if baseline_window is not None
            else baseline_period
        )
        path_rows.append(selected)

        for group_values, view in selected.groupby(keys, observed=True):
            terminal = view[view["period"].between(TERMINAL_START, TERMINAL_END)]["path_index"]
            terminal_index = terminal.mean() if terminal.notna().any() else np.nan
            record = dict(zip(keys, group_values))
            record.update(
                {
                    "outcome": outcome,
                    "support_status": str(view["support_status"].iloc[0]),
                    "baseline_rule": str(view["baseline_rule"].iloc[0]),
                    "baseline_value": float(view["baseline_value"].iloc[0])
                    if pd.notna(view["baseline_value"].iloc[0])
                    else np.nan,
                    "baseline_support": float(view["baseline_support"].iloc[0])
                    if pd.notna(view["baseline_support"].iloc[0])
                    else np.nan,
                    "terminal_months": int(terminal.notna().sum()),
                    "terminal_index": float(terminal_index)
                    if pd.notna(terminal_index)
                    else np.nan,
                    "terminal_change_pct": 100.0 * (float(terminal_index) - 1.0)
                    if pd.notna(terminal_index)
                    else np.nan,
                }
            )
            terminal_rows.append(record)
    paths = pd.concat(path_rows, ignore_index=True)
    terminal_summary = pd.DataFrame(terminal_rows)
    return (
        paths.sort_values(keys + ["outcome", "period"]).reset_index(drop=True),
        terminal_summary.sort_values(keys + ["outcome"]).reset_index(drop=True),
    )


def _annualized_log_slope(values: pd.Series) -> float:
    valid = pd.to_numeric(values, errors="coerce")
    mask = valid.gt(0) & valid.notna()
    if int(mask.sum()) < 2:
        return np.nan
    x = np.arange(len(valid), dtype=float)[mask.to_numpy()]
    beta = np.polyfit(x, np.log(valid[mask].astype(float)), 1)[0]
    return float(100.0 * np.expm1(beta * 12.0))


def build_preperiod_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    """Describe pre-shock paths without causal pass/fail labels or p-values."""
    required = {
        "case_id",
        "variant_id",
        "dimension",
        "group_id",
        "period",
        "admissions",
        "wage_count",
        "real_admission_wage",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Case panel is missing diagnostic columns: {missing}")
    data = panel[panel["period"].between(START_PERIOD, BASELINE_PERIOD)].copy()
    keys = ["case_id", "variant_id", "dimension", "group_id"]
    expected_months = len(pd.period_range(START_PERIOD, BASELINE_PERIOD, freq="M"))
    rows: list[dict[str, object]] = []
    for group_values, view in data.groupby(keys, observed=True):
        view = view.sort_values("period")
        pre_admissions = int(view["admissions"].sum())
        pre_wage_records = int(view["wage_count"].sum())
        wage_coverage = (
            100.0 * pre_wage_records / pre_admissions if pre_admissions > 0 else np.nan
        )
        for outcome, column in [
            ("admissions", "admissions"),
            ("real_admission_wage", "real_admission_wage"),
        ]:
            values = pd.to_numeric(view[column], errors="coerce")
            observed = values.dropna()
            baseline_row = view[view["period"].eq(BASELINE_PERIOD)]
            support_column = "admissions" if outcome == "admissions" else "wage_count"
            baseline_support = (
                float(baseline_row[support_column].iloc[0])
                if not baseline_row.empty
                else 0.0
            )
            record = dict(zip(keys, group_values))
            record.update(
                {
                    "outcome": outcome,
                    "pre_months_expected": expected_months,
                    "pre_months_observed": int(observed.size),
                    "pre_admissions": pre_admissions,
                    "pre_wage_records": pre_wage_records,
                    "wage_coverage_pct": wage_coverage,
                    "baseline_support": baseline_support,
                    "pre_mean": float(observed.mean()) if not observed.empty else np.nan,
                    "pre_min": float(observed.min()) if not observed.empty else np.nan,
                    "pre_max": float(observed.max()) if not observed.empty else np.nan,
                    "annualized_log_slope_pct": _annualized_log_slope(values),
                    "coefficient_of_variation": (
                        float(observed.std(ddof=0) / observed.mean())
                        if not observed.empty and observed.mean() != 0
                        else np.nan
                    ),
                }
            )
            rows.append(record)
    return pd.DataFrame(rows).sort_values(keys + ["outcome"]).reset_index(drop=True)


def build_same_month_terminal_sensitivity(
    panel: pd.DataFrame,
    *,
    baseline_year: int = 2022,
    terminal_year: int = 2025,
    terminal_months: tuple[int, ...] = (1, 2, 3, 4, 5, 6),
    min_support: int = MIN_BASELINE_SUPPORT,
) -> pd.DataFrame:
    """Compare each terminal month with the same calendar month before ChatGPT."""
    required = {
        "case_id",
        "variant_id",
        "dimension",
        "group_id",
        "period",
        "admissions",
        "wage_count",
        "real_admission_wage",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Case panel is missing same-month columns: {missing}")
    data = panel.copy()
    parsed = pd.PeriodIndex(data["period"], freq="M")
    data["year"] = parsed.year
    data["month"] = parsed.month
    keys = ["case_id", "variant_id", "dimension", "group_id"]
    rows: list[dict[str, object]] = []
    for outcome, value_column, support_column in [
        ("admissions", "admissions", "admissions"),
        ("real_admission_wage", "real_admission_wage", "wage_count"),
    ]:
        baseline = data[
            data["year"].eq(baseline_year)
            & data["month"].isin(terminal_months)
        ][keys + ["month"]].copy()
        baseline["baseline_value"] = data.loc[baseline.index, value_column]
        baseline["baseline_support"] = data.loc[baseline.index, support_column]
        terminal = data[
            data["year"].eq(terminal_year)
            & data["month"].isin(terminal_months)
        ][keys + ["month"]].copy()
        terminal["terminal_value"] = data.loc[terminal.index, value_column]
        matched = terminal.merge(
            baseline,
            on=keys + ["month"],
            how="outer",
            validate="one_to_one",
        )
        for group_values, view in matched.groupby(keys, observed=True):
            valid = (
                view["baseline_support"].ge(min_support)
                & view["baseline_value"].gt(0)
                & view["baseline_value"].notna()
                & view["terminal_value"].notna()
            )
            complete = len(view) == len(terminal_months) and bool(valid.all())
            changes = (
                100.0
                * (
                    view.loc[valid, "terminal_value"]
                    / view.loc[valid, "baseline_value"]
                    - 1.0
                )
            )
            record = dict(zip(keys, group_values))
            record.update(
                {
                    "outcome": outcome,
                    "baseline_year": baseline_year,
                    "terminal_year": terminal_year,
                    "calendar_months": ";".join(f"{month:02d}" for month in terminal_months),
                    "matched_months": int(valid.sum()),
                    "minimum_baseline_support": float(view["baseline_support"].min())
                    if view["baseline_support"].notna().any()
                    else np.nan,
                    "support_status": "adequate"
                    if complete
                    else "suppressed_pre_support",
                    "same_month_change_pct": float(changes.mean())
                    if complete
                    else np.nan,
                }
            )
            rows.append(record)
    return pd.DataFrame(rows).sort_values(keys + ["outcome"]).reset_index(drop=True)


def build_demographic_difference_matrix(
    terminal: pd.DataFrame,
    alternative_terminal: pd.DataFrame,
    same_month_terminal: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare pre-specified demographic pairs and apply the frozen mention rule."""
    keys = ["case_id", "variant_id", "dimension", "group_id", "outcome"]
    main = terminal[terminal["variant_id"].eq("primary")].copy()
    alt = alternative_terminal[alternative_terminal["variant_id"].eq("primary")].copy()
    alt = alt[
        keys + ["terminal_change_pct", "support_status"]
    ].rename(
        columns={
            "terminal_change_pct": "alternative_terminal_change_pct",
            "support_status": "alternative_support_status",
        }
    )
    merged = main.merge(alt, on=keys, how="left", validate="one_to_one")
    if same_month_terminal is None:
        calendar = terminal[terminal["variant_id"].eq("primary")][
            keys + ["terminal_change_pct", "support_status"]
        ].rename(
            columns={
                "terminal_change_pct": "same_month_change_pct",
                "support_status": "same_month_support_status",
            }
        )
    else:
        calendar = same_month_terminal[same_month_terminal["variant_id"].eq("primary")][
            keys + ["same_month_change_pct", "support_status"]
        ].rename(columns={"support_status": "same_month_support_status"})
    merged = merged.merge(calendar, on=keys, how="left", validate="one_to_one")
    rows: list[dict[str, object]] = []
    for dimension, pairs in DEMOGRAPHIC_SPECS.items():
        focal_id, focal_label = pairs[0]
        comparison_id, comparison_label = pairs[1]
        for case_id in CASE_ORDER:
            for outcome in ["admissions", "real_admission_wage"]:
                subset = merged[
                    merged["case_id"].eq(case_id)
                    & merged["dimension"].eq(dimension)
                    & merged["outcome"].eq(outcome)
                ].set_index("group_id")
                values: dict[str, object] = {}
                for prefix, group_id in [
                    ("focal", focal_id),
                    ("comparison", comparison_id),
                ]:
                    if group_id in subset.index:
                        row = subset.loc[group_id]
                        values[f"{prefix}_change_pct"] = row["terminal_change_pct"]
                        values[f"{prefix}_support_status"] = row["support_status"]
                        values[f"{prefix}_alternative_change_pct"] = row[
                            "alternative_terminal_change_pct"
                        ]
                        values[f"{prefix}_alternative_support_status"] = row[
                            "alternative_support_status"
                        ]
                        values[f"{prefix}_same_month_change_pct"] = row[
                            "same_month_change_pct"
                        ]
                        values[f"{prefix}_same_month_support_status"] = row[
                            "same_month_support_status"
                        ]
                    else:
                        values[f"{prefix}_change_pct"] = np.nan
                        values[f"{prefix}_support_status"] = "missing"
                        values[f"{prefix}_alternative_change_pct"] = np.nan
                        values[f"{prefix}_alternative_support_status"] = "missing"
                        values[f"{prefix}_same_month_change_pct"] = np.nan
                        values[f"{prefix}_same_month_support_status"] = "missing"
                difference = values["focal_change_pct"] - values["comparison_change_pct"]
                alternative_difference = (
                    values["focal_alternative_change_pct"]
                    - values["comparison_alternative_change_pct"]
                )
                same_month_difference = (
                    values["focal_same_month_change_pct"]
                    - values["comparison_same_month_change_pct"]
                )
                support_adequate = all(
                    values[column] == "adequate"
                    for column in [
                        "focal_support_status",
                        "comparison_support_status",
                        "focal_alternative_support_status",
                        "comparison_alternative_support_status",
                        "focal_same_month_support_status",
                        "comparison_same_month_support_status",
                    ]
                )
                sign_stable = (
                    pd.notna(difference)
                    and pd.notna(alternative_difference)
                    and np.sign(difference) == np.sign(alternative_difference)
                )
                calendar_sign_stable = (
                    pd.notna(difference)
                    and pd.notna(same_month_difference)
                    and np.sign(difference) == np.sign(same_month_difference)
                )
                rows.append(
                    {
                        "dimension": dimension,
                        "focal_group": focal_id,
                        "focal_label": focal_label,
                        "comparison_group": comparison_id,
                        "comparison_label": comparison_label,
                        "case_id": case_id,
                        "case_label": CASE_SHORT_LABELS[case_id],
                        "outcome": outcome,
                        **values,
                        "difference_pp": difference,
                        "alternative_difference_pp": alternative_difference,
                        "same_month_difference_pp": same_month_difference,
                        "support_adequate": support_adequate,
                        "normalization_sign_stable": sign_stable,
                        "calendar_sign_stable": calendar_sign_stable,
                    }
                )
    matrix = pd.DataFrame(rows)
    decision_rows: list[dict[str, object]] = []
    for (dimension, outcome), view in matrix.groupby(
        ["dimension", "outcome"],
        observed=True,
    ):
        differences = pd.to_numeric(view["difference_pp"], errors="coerce")
        positive = int(differences.gt(0).sum())
        negative = int(differences.lt(0).sum())
        dominant_direction = "focal_higher" if positive >= negative else "focal_lower"
        dominant_sign = 1 if dominant_direction == "focal_higher" else -1
        n_same_direction = int(
            (
                (np.sign(differences) == dominant_sign)
                & view["normalization_sign_stable"].astype(bool)
                & view["calendar_sign_stable"].astype(bool)
            ).sum()
        )
        threshold = 5.0 if outcome == "admissions" else 2.0
        median_abs = float(differences.abs().median()) if differences.notna().any() else np.nan
        all_support = bool(view["support_adequate"].all()) and len(view) == len(CASE_ORDER)
        mentionable = (
            all_support
            and n_same_direction >= 5
            and pd.notna(median_abs)
            and median_abs >= threshold
        )
        decision_rows.append(
            {
                "dimension": dimension,
                "outcome": outcome,
                "n_cases": len(view),
                "positive_cases": positive,
                "negative_cases": negative,
                "dominant_direction": dominant_direction,
                "same_direction_all_sensitivities_cases": n_same_direction,
                "all_cells_supported": all_support,
                "median_absolute_difference_pp": median_abs,
                "minimum_required_difference_pp": threshold,
                "mentionable_in_section5_3": mentionable,
            }
        )
    decisions = pd.DataFrame(decision_rows)
    return matrix, decisions


EXPOSURE_ORDER = [
    "Exposed: Gradient 3",
    "Exposed: Gradient 2",
    "Exposed: Gradient 1",
    "Minimal Exposure",
    "Not Exposed",
    "No score",
]


def build_exposure_composition(
    cells: pd.DataFrame,
    membership: pd.DataFrame,
    classification: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Weight Brazilian ILO categories by primary-case pre-treatment admissions."""
    overall = cells[
        cells["dimension"].eq("overall")
        & cells["period"].between(START_PERIOD, BASELINE_PERIOD)
    ].copy()
    pre = (
        overall.groupby("cbo_6d", observed=True)["admissions"]
        .sum()
        .rename("pre_admissions")
        .reset_index()
    )
    primary = membership[membership["variant_id"].eq("primary")].copy()
    data = primary.merge(pre, on="cbo_6d", how="left", validate="one_to_one")
    data["pre_admissions"] = pd.to_numeric(data["pre_admissions"], errors="coerce").fillna(0)
    data["cbo_4d"] = data["cbo_6d"].str[:4]
    classes = classification[["cbo_4d", "cbo_ilo_gradient"]].copy()
    classes["cbo_4d"] = classes["cbo_4d"].astype(str).str.zfill(4)
    classes = classes.drop_duplicates("cbo_4d")
    data = data.merge(classes, on="cbo_4d", how="left", validate="many_to_one")
    data["exposure_category"] = data["cbo_ilo_gradient"].fillna("No score")
    data.loc[~data["exposure_category"].isin(EXPOSURE_ORDER), "exposure_category"] = "No score"
    grouped = (
        data.groupby(["case_id", "exposure_category"], observed=True)["pre_admissions"]
        .sum()
        .reset_index()
    )
    case_ids = primary["case_id"].drop_duplicates().tolist()
    grid = pd.MultiIndex.from_product(
        [case_ids, EXPOSURE_ORDER],
        names=["case_id", "exposure_category"],
    ).to_frame(index=False)
    long = grid.merge(
        grouped,
        on=["case_id", "exposure_category"],
        how="left",
        validate="one_to_one",
    )
    long["pre_admissions"] = long["pre_admissions"].fillna(0)
    totals = long.groupby("case_id", observed=True)["pre_admissions"].transform("sum")
    long["share_pct"] = np.where(totals.gt(0), 100.0 * long["pre_admissions"] / totals, np.nan)
    coverage = (
        long.assign(
            covered_admissions=np.where(
                long["exposure_category"].eq("No score"),
                0,
                long["pre_admissions"],
            )
        )
        .groupby("case_id", observed=True)
        .agg(
            pre_admissions=("pre_admissions", "sum"),
            covered_admissions=("covered_admissions", "sum"),
        )
        .reset_index()
    )
    coverage["score_coverage_pct"] = np.where(
        coverage["pre_admissions"].gt(0),
        100.0 * coverage["covered_admissions"] / coverage["pre_admissions"],
        np.nan,
    )
    wide = long.pivot(
        index="case_id",
        columns="exposure_category",
        values="share_pct",
    ).reset_index()
    summary = coverage.merge(wide, on="case_id", how="left", validate="one_to_one")
    return long, summary


def build_exposure_detail(
    cells: pd.DataFrame,
    membership: pd.DataFrame,
    classification: pd.DataFrame,
) -> pd.DataFrame:
    """Return the primary-case CBO6 exposure audit behind the weighted summary."""
    overall = cells[
        cells["dimension"].eq("overall")
        & cells["period"].between(START_PERIOD, BASELINE_PERIOD)
    ]
    pre = (
        overall.groupby("cbo_6d", observed=True)["admissions"]
        .sum()
        .rename("pre_admissions")
        .reset_index()
    )
    primary = membership[membership["variant_id"].eq("primary")].copy()
    primary["cbo_4d"] = primary["cbo_6d"].str[:4]
    classes = classification[
        ["cbo_4d", "cbo_ilo_gradient", "exposure_score_4d"]
    ].copy()
    classes["cbo_4d"] = classes["cbo_4d"].astype(str).str.zfill(4)
    conflicts = classes.groupby("cbo_4d", observed=True).nunique(dropna=False)
    if (conflicts > 1).any(axis=None):
        conflicted = conflicts[(conflicts > 1).any(axis=1)].index.tolist()
        raise RuntimeError(f"Conflicting exposure rows for CBO4 codes: {conflicted}")
    classes = classes.drop_duplicates("cbo_4d")
    out = (
        primary.merge(pre, on="cbo_6d", how="left", validate="one_to_one")
        .merge(classes, on="cbo_4d", how="left", validate="many_to_one")
    )
    out["pre_admissions"] = out["pre_admissions"].fillna(0).astype(int)
    out["exposure_category"] = out["cbo_ilo_gradient"].fillna("No score")
    out.loc[
        ~out["exposure_category"].isin(EXPOSURE_ORDER),
        "exposure_category",
    ] = "No score"
    totals = out.groupby("case_id", observed=True)["pre_admissions"].transform("sum")
    out["within_case_pre_admission_share_pct"] = np.where(
        totals.gt(0),
        100.0 * out["pre_admissions"] / totals,
        np.nan,
    )
    return out[
        [
            "case_id",
            "variant_id",
            "cbo_6d",
            "cbo_4d",
            "pre_admissions",
            "within_case_pre_admission_share_pct",
            "exposure_category",
            "exposure_score_4d",
        ]
    ].sort_values(["case_id", "cbo_6d"]).reset_index(drop=True)


def build_case_composition_shift(
    cells: pd.DataFrame,
    membership: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Audit CBO6 admission-share shifts between October 2022 and Jan-Jun 2025."""
    primary = membership[membership["variant_id"].eq("primary")][
        ["case_id", "cbo_6d"]
    ].copy()
    age = cells[cells["dimension"].eq("age")].merge(
        primary,
        on="cbo_6d",
        how="inner",
        validate="many_to_one",
    )
    baseline = (
        age[age["period"].eq(BASELINE_PERIOD)]
        .groupby(["case_id", "group_id", "cbo_6d"], observed=True)["admissions"]
        .sum()
        .rename("baseline_admissions")
        .reset_index()
    )
    terminal = (
        age[age["period"].between(TERMINAL_START, TERMINAL_END)]
        .groupby(["case_id", "group_id", "cbo_6d"], observed=True)["admissions"]
        .sum()
        .rename("terminal_admissions")
        .reset_index()
    )
    grid = (
        primary.assign(_key=1)
        .merge(
            pd.DataFrame({"group_id": list(DIMENSION_GROUPS["age"])}).assign(_key=1),
            on="_key",
        )
        .drop(columns="_key")
    )
    # DIMENSION_GROUPS stores (id, label) pairs.
    grid["group_id"] = grid["group_id"].map(lambda value: value[0])
    detail = (
        grid.merge(
            baseline,
            on=["case_id", "group_id", "cbo_6d"],
            how="left",
            validate="one_to_one",
        )
        .merge(
            terminal,
            on=["case_id", "group_id", "cbo_6d"],
            how="left",
            validate="one_to_one",
        )
    )
    detail[["baseline_admissions", "terminal_admissions"]] = detail[
        ["baseline_admissions", "terminal_admissions"]
    ].fillna(0)
    baseline_totals = detail.groupby(
        ["case_id", "group_id"],
        observed=True,
    )["baseline_admissions"].transform("sum")
    terminal_totals = detail.groupby(
        ["case_id", "group_id"],
        observed=True,
    )["terminal_admissions"].transform("sum")
    detail["baseline_share_pct"] = np.where(
        baseline_totals.gt(0),
        100.0 * detail["baseline_admissions"] / baseline_totals,
        np.nan,
    )
    detail["terminal_share_pct"] = np.where(
        terminal_totals.gt(0),
        100.0 * detail["terminal_admissions"] / terminal_totals,
        np.nan,
    )
    detail["share_change_pp"] = (
        detail["terminal_share_pct"] - detail["baseline_share_pct"]
    )
    summary = (
        detail.assign(absolute_share_change=detail["share_change_pp"].abs())
        .groupby(["case_id", "group_id"], observed=True)
        .agg(
            baseline_admissions=("baseline_admissions", "sum"),
            terminal_admissions=("terminal_admissions", "sum"),
            active_cbo_baseline=("baseline_admissions", lambda values: int(values.gt(0).sum())),
            active_cbo_terminal=("terminal_admissions", lambda values: int(values.gt(0).sum())),
            total_variation_share=(
                "absolute_share_change",
                lambda values: float(values.sum() / 200.0),
            ),
            largest_absolute_share_change_pp=("absolute_share_change", "max"),
        )
        .reset_index()
    )
    return (
        detail.sort_values(["case_id", "group_id", "cbo_6d"]).reset_index(drop=True),
        summary.sort_values(["case_id", "group_id"]).reset_index(drop=True),
    )
