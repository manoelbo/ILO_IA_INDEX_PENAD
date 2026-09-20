import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section5_3_occupation_cases.config import (  # noqa: E402
    CASE_ORDER,
    DICTIONARY_PATH,
    OFFICIAL_METADATA_PATH,
    PRIMARY_CASE_SIZES,
    load_occupation_dictionary,
)
from section5_3_occupation_cases.transforms import (  # noqa: E402
    aggregate_case_cells,
    assign_age_group,
    assign_demographic_group,
    build_demographic_difference_matrix,
    build_exposure_composition,
    build_membership_table,
    build_preperiod_diagnostics,
    build_same_month_terminal_sensitivity,
    complete_case_panel,
    normalize_case_paths,
)
from section5_3_occupation_cases.data import (  # noqa: E402
    aggregate_admission_records,
    apply_record_wage_winsorization,
    compute_record_wage_winsor_bounds,
)
from section5_3_occupation_cases.figures import (  # noqa: E402
    make_age_paths_free_scale_figure,
    make_age_paths_figure,
    make_age_paths_split_figure,
    make_age_terminal_heatmap,
    save_figure_bundle,
)
from section5_3_occupation_cases.report import build_result_selection_log  # noqa: E402
from section5_3_occupation_cases.tables import (  # noqa: E402
    build_exposure_summary_table,
    write_table_pair,
)


class OccupationCaseDictionaryTests(unittest.TestCase):
    def test_stable_official_metadata_extract_covers_every_dictionary_code(
        self,
    ) -> None:
        dictionary = load_occupation_dictionary(DICTIONARY_PATH)
        metadata = pd.read_csv(OFFICIAL_METADATA_PATH, dtype={"cbo_6d": str})

        self.assertEqual(len(metadata), 80)
        self.assertFalse(metadata["cbo_6d"].duplicated().any())
        self.assertEqual(set(metadata["cbo_6d"]), set(dictionary["cbo_6d"]))
        title_lookup = metadata.set_index("cbo_6d")["official_title"]
        expected_titles = dictionary.set_index("cbo_6d")["cbo_title"]
        pd.testing.assert_series_equal(
            title_lookup.sort_index(),
            expected_titles.sort_index(),
            check_names=False,
        )
        self.assertTrue(metadata["official_activities"].str.len().gt(0).all())

    def test_primary_dictionary_has_six_disjoint_cases_and_76_codes(self) -> None:
        dictionary = load_occupation_dictionary(DICTIONARY_PATH)
        primary = dictionary[dictionary["primary_included"]].copy()

        self.assertEqual(primary["case_id"].drop_duplicates().tolist(), CASE_ORDER)
        self.assertEqual(len(primary), 76)
        self.assertFalse(primary["cbo_6d"].duplicated().any())
        self.assertEqual(
            primary.groupby("case_id", sort=False)["cbo_6d"].nunique().to_dict(),
            PRIMARY_CASE_SIZES,
        )

    def test_supervisor_rule_expands_to_53_codes_and_excludes_maintenance(self) -> None:
        dictionary = load_occupation_dictionary(DICTIONARY_PATH)
        supervisors = dictionary[
            dictionary["primary_included"]
            & dictionary["case_id"].eq("production_supervisors")
        ]

        self.assertEqual(len(supervisors), 53)
        self.assertNotIn("860105", set(supervisors["cbo_6d"]))
        self.assertIn("860110", set(supervisors["cbo_6d"]))
        self.assertIn("860115", set(supervisors["cbo_6d"]))

    def test_pre_specified_variants_are_encoded_without_changing_primary(self) -> None:
        dictionary = load_occupation_dictionary(DICTIONARY_PATH)
        variants = {
            variant: set(
                dictionary.loc[
                    dictionary["variant_membership"].str.split(";").map(
                        lambda values: variant in values
                    ),
                    "cbo_6d",
                ]
            )
            for variant in [
                "customer_extended",
                "supervisor_industry",
                "stock_extended",
                "health_restricted",
            ]
        }

        self.assertEqual(
            variants["customer_extended"],
            {"422310", "422315", "422320"},
        )
        self.assertNotIn("860110", variants["supervisor_industry"])
        self.assertNotIn("860115", variants["supervisor_industry"])
        self.assertEqual(len(variants["supervisor_industry"]), 51)
        self.assertEqual(
            variants["stock_extended"],
            {"414105", "414110", "414120", "414125", "414135", "414140", "521125"},
        )
        self.assertNotIn("414115", variants["stock_extended"])
        self.assertEqual(
            variants["health_restricted"],
            {"515110", "516210", "516220"},
        )


class OccupationCaseRecodingTests(unittest.TestCase):
    def test_canaries_age_groups_use_the_frozen_boundaries(self) -> None:
        ages = pd.Series([21, 22, 25, 26, 30, 31, 34, 35, 40, 41, 49, 50, 80])

        observed = assign_age_group(ages).tolist()

        self.assertEqual(
            observed,
            [
                pd.NA,
                "age_22_25",
                "age_22_25",
                "age_26_30",
                "age_26_30",
                "age_31_34",
                "age_31_34",
                "age_35_40",
                "age_35_40",
                "age_41_49",
                "age_41_49",
                "age_50_plus",
                "age_50_plus",
            ],
        )

    def test_demographic_recodes_match_the_valid_caged_codes(self) -> None:
        frame = pd.DataFrame(
            {
                "sexo": ["1", "3", "9", "3"],
                "raca_cor": ["1", "2", "3", "9"],
                "grau_instrucao": ["7", "8", "11", "99"],
            }
        )

        sex = assign_demographic_group(frame, "sex").tolist()
        race = assign_demographic_group(frame, "race_color").tolist()
        education = assign_demographic_group(frame, "education").tolist()

        self.assertEqual(sex, ["men", "women", pd.NA, "women"])
        self.assertEqual(
            race,
            ["race_white", "race_black_combined", "race_black_combined", pd.NA],
        )
        self.assertEqual(
            education,
            ["education_other", "higher_education", "higher_education", pd.NA],
        )


class OccupationCaseTransformationTests(unittest.TestCase):
    def test_record_wage_bounds_count_clipped_observations(self) -> None:
        records = pd.DataFrame(
            {
                "ano": [2022] * 100,
                "cbo_2002": ["212205"] * 100,
                "salario_mensal": list(range(1, 101)),
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selected.parquet"
            records.to_parquet(path, index=False)

            observed = compute_record_wage_winsor_bounds(path)

        row = observed.iloc[0]
        self.assertEqual(row["positive_wage_records"], 100)
        self.assertEqual(row["records_below_lower_bound"], 1)
        self.assertEqual(row["records_above_upper_bound"], 1)

    def test_record_wage_winsorization_is_specific_to_cbo_and_year(self) -> None:
        records = pd.DataFrame(
            {
                "ano": [2022, 2022, 2023],
                "cbo_2002": ["840105", "212205", "840105"],
                "salario_mensal": [1_000_000.0, 50_000.0, 20_000.0],
            }
        )
        bounds = pd.DataFrame(
            {
                "ano": [2022, 2022, 2023],
                "cbo_6d": ["840105", "212205", "840105"],
                "lower_bound": [1_500.0, 2_000.0, 1_600.0],
                "upper_bound": [10_000.0, 60_000.0, 18_000.0],
            }
        )

        observed = apply_record_wage_winsorization(records, bounds)

        self.assertEqual(observed["salario_mensal"].tolist(), [10_000.0, 50_000.0, 18_000.0])

    def test_raw_record_aggregation_keeps_admissions_and_positive_wages_separate(self) -> None:
        records = pd.DataFrame(
            {
                "ano": [2022, 2022, 2022, 2022],
                "mes": [10, 10, 10, 10],
                "cbo_2002": ["212205", "212205", "212205", "212205"],
                "saldo_movimentacao": [1, 1, 1, -1],
                "salario_mensal": [1_000.0, 0.0, None, 9_999.0],
                "idade": [24, 30, 21, 24],
                "sexo": ["3", "1", "3", "3"],
                "raca_cor": ["2", "1", "3", "2"],
                "grau_instrucao": ["8", "7", "9", "8"],
            }
        )

        cells = aggregate_admission_records(records)

        overall = cells[
            cells["dimension"].eq("overall")
            & cells["group_id"].eq("all")
        ].iloc[0]
        self.assertEqual(overall["admissions"], 3)
        self.assertEqual(overall["wage_count"], 1)
        self.assertEqual(overall["wage_sum"], 1_000.0)
        self.assertEqual(
            cells.loc[cells["dimension"].eq("age"), "admissions"].sum(),
            2,
        )
        self.assertEqual(
            cells.loc[
                cells["dimension"].eq("education")
                & cells["group_id"].eq("higher_education"),
                "admissions",
            ].sum(),
            2,
        )

    def test_membership_table_keeps_primary_and_sensitivity_variants_separate(self) -> None:
        dictionary = load_occupation_dictionary(DICTIONARY_PATH)

        membership = build_membership_table(dictionary)

        customer = membership[membership["case_id"].eq("customer_service")]
        self.assertEqual(
            set(customer.loc[customer["variant_id"].eq("primary"), "cbo_6d"]),
            {"422315", "422320"},
        )
        self.assertEqual(
            set(customer.loc[customer["variant_id"].eq("customer_extended"), "cbo_6d"]),
            {"422310", "422315", "422320"},
        )
        self.assertFalse(membership["variant_id"].eq("excluded").any())

    def test_case_aggregation_uses_admission_weighted_real_wages(self) -> None:
        cells = pd.DataFrame(
            {
                "cbo_6d": ["212205", "212215"],
                "dimension": ["age", "age"],
                "group_id": ["age_22_25", "age_22_25"],
                "period": ["2022-10", "2022-10"],
                "admissions": [10, 30],
                "wage_sum": [10_000.0, 60_000.0],
                "wage_count": [10, 30],
            }
        )
        membership = pd.DataFrame(
            {
                "case_id": ["software_developers", "software_developers"],
                "variant_id": ["primary", "primary"],
                "cbo_6d": ["212205", "212215"],
            }
        )
        ipca = pd.DataFrame({"period": ["2022-10"], "indice": [125.0]})

        observed, _bounds = aggregate_case_cells(cells, membership, ipca)
        row = observed.iloc[0]

        self.assertEqual(row["admissions"], 40)
        self.assertEqual(row["wage_count"], 40)
        self.assertAlmostEqual(row["nominal_admission_wage"], 1_750.0)
        self.assertAlmostEqual(row["real_admission_wage"], 1_400.0)

    def test_case_panel_completion_adds_zero_admissions_but_not_zero_wages(self) -> None:
        observed = pd.DataFrame(
            {
                "case_id": ["software_developers"],
                "variant_id": ["primary"],
                "dimension": ["overall"],
                "group_id": ["all"],
                "period": ["2022-10"],
                "admissions": [10],
                "wage_sum": [10_000.0],
                "wage_count": [10],
                "n_cbo_observed": [1],
                "nominal_admission_wage": [1_000.0],
                "real_admission_wage": [800.0],
                "indice": [125.0],
            }
        )
        membership = pd.DataFrame(
            {
                "case_id": ["software_developers"],
                "variant_id": ["primary"],
                "cbo_6d": ["212205"],
            }
        )
        months = pd.period_range("2021-01", "2025-06", freq="M")
        ipca = pd.DataFrame(
            {
                "period": months.astype(str),
                "indice": [100.0] * len(months),
            }
        )

        completed = complete_case_panel(observed, membership, ipca)

        self.assertEqual(len(completed), 13 * len(months))
        missing = completed[
            completed["dimension"].eq("overall")
            & completed["group_id"].eq("all")
            & completed["period"].eq("2022-09")
        ].iloc[0]
        self.assertEqual(missing["admissions"], 0)
        self.assertEqual(missing["wage_count"], 0)
        self.assertTrue(pd.isna(missing["real_admission_wage"]))

    def test_normalization_uses_october_support_and_fixed_terminal_window(self) -> None:
        months = ["2022-10", "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
        panel = pd.DataFrame(
            {
                "case_id": ["software_developers"] * len(months),
                "variant_id": ["primary"] * len(months),
                "dimension": ["age"] * len(months),
                "group_id": ["age_22_25"] * len(months),
                "period": months,
                "admissions": [100, 80, 80, 80, 80, 80, 80],
                "wage_count": [100, 100, 100, 100, 100, 100, 100],
                "real_admission_wage": [2_000, 1_800, 1_800, 1_800, 1_800, 1_800, 1_800],
            }
        )

        paths, terminal = normalize_case_paths(panel)

        baseline = paths[paths["period"].eq("2022-10")]
        self.assertEqual(set(baseline["path_index"]), {1.0})
        self.assertEqual(set(paths["support_status"]), {"adequate"})
        by_outcome = terminal.set_index("outcome")["terminal_change_pct"].to_dict()
        self.assertAlmostEqual(by_outcome["admissions"], -20.0)
        self.assertAlmostEqual(by_outcome["real_admission_wage"], -10.0)

    def test_normalization_suppresses_cells_using_pre_treatment_support_only(self) -> None:
        panel = pd.DataFrame(
            {
                "case_id": ["customer_service", "customer_service"],
                "variant_id": ["primary", "primary"],
                "dimension": ["age", "age"],
                "group_id": ["age_22_25", "age_22_25"],
                "period": ["2022-10", "2025-01"],
                "admissions": [29, 1_000],
                "wage_count": [29, 1_000],
                "real_admission_wage": [2_000.0, 5_000.0],
            }
        )

        paths, terminal = normalize_case_paths(panel)

        self.assertEqual(set(paths["support_status"]), {"suppressed_pre_support"})
        self.assertTrue(paths["path_index"].isna().all())
        self.assertTrue(terminal["terminal_change_pct"].isna().all())

    def test_alternative_normalization_keeps_october_support_rule(self) -> None:
        panel = pd.DataFrame(
            {
                "case_id": ["stock_clerks"] * 3,
                "variant_id": ["primary"] * 3,
                "dimension": ["age"] * 3,
                "group_id": ["age_22_25"] * 3,
                "period": ["2022-01", "2022-10", "2025-01"],
                "admissions": [100, 29, 100],
                "wage_count": [100, 29, 100],
                "real_admission_wage": [2_000.0, 2_000.0, 2_000.0],
            }
        )

        paths, _terminal = normalize_case_paths(
            panel,
            baseline_window=("2022-01", "2022-10"),
        )

        self.assertEqual(set(paths["support_status"]), {"suppressed_pre_support"})

    def test_same_month_sensitivity_compares_each_terminal_month_to_2022(self) -> None:
        rows = []
        for year, multiplier in [(2022, 1.0), (2025, 1.2)]:
            for month in range(1, 7):
                rows.append(
                    {
                        "case_id": "software_developers",
                        "variant_id": "primary",
                        "dimension": "age",
                        "group_id": "age_22_25",
                        "period": f"{year}-{month:02d}",
                        "admissions": 100 * multiplier,
                        "wage_count": 100,
                        "real_admission_wage": 2_000 * multiplier,
                    }
                )
        panel = pd.DataFrame(rows)

        observed = build_same_month_terminal_sensitivity(panel)

        self.assertEqual(set(observed["matched_months"]), {6})
        self.assertEqual(set(observed["support_status"]), {"adequate"})
        for value in observed["same_month_change_pct"]:
            self.assertAlmostEqual(value, 20.0)

    def test_exposure_composition_weights_categories_by_pre_admissions(self) -> None:
        cells = pd.DataFrame(
            {
                "cbo_6d": ["212205", "212215", "212205"],
                "dimension": ["overall", "overall", "overall"],
                "group_id": ["all", "all", "all"],
                "period": ["2021-01", "2021-01", "2022-11"],
                "admissions": [75, 25, 999],
                "wage_sum": [0.0, 0.0, 0.0],
                "wage_count": [0, 0, 0],
            }
        )
        membership = pd.DataFrame(
            {
                "case_id": ["software_developers", "software_developers"],
                "variant_id": ["primary", "primary"],
                "cbo_6d": ["212205", "212215"],
            }
        )
        classification = pd.DataFrame(
            {
                "cbo_4d": ["2122"],
                "cbo_ilo_gradient": ["Exposed: Gradient 3"],
            }
        )

        long, summary = build_exposure_composition(cells, membership, classification)

        self.assertEqual(long["pre_admissions"].sum(), 100)
        self.assertEqual(long.iloc[0]["share_pct"], 100.0)
        self.assertEqual(summary.iloc[0]["score_coverage_pct"], 100.0)
        self.assertEqual(summary.iloc[0]["pre_admissions"], 100)

    def test_preperiod_diagnostics_are_descriptive_and_have_no_test_label(self) -> None:
        months = pd.period_range("2021-01", "2022-10", freq="M").astype(str)
        panel = pd.DataFrame(
            {
                "case_id": ["software_developers"] * len(months),
                "variant_id": ["primary"] * len(months),
                "dimension": ["overall"] * len(months),
                "group_id": ["all"] * len(months),
                "period": months,
                "admissions": [100] * len(months),
                "wage_count": [90] * len(months),
                "real_admission_wage": [2_000.0] * len(months),
            }
        )

        diagnostics = build_preperiod_diagnostics(panel)

        self.assertEqual(set(diagnostics["pre_months_expected"]), {22})
        self.assertEqual(set(diagnostics["wage_coverage_pct"]), {90.0})
        self.assertNotIn("pretrend_pass", diagnostics.columns)
        self.assertNotIn("p_value", diagnostics.columns)

    def test_demographic_mention_rule_requires_five_cases_support_and_alt_stability(self) -> None:
        rows = []
        for case_id in CASE_ORDER:
            for group_id, change in [("women", 10.0), ("men", 0.0)]:
                rows.append(
                    {
                        "case_id": case_id,
                        "variant_id": "primary",
                        "dimension": "sex",
                        "group_id": group_id,
                        "outcome": "admissions",
                        "terminal_change_pct": change,
                        "support_status": "adequate",
                    }
                )
        terminal = pd.DataFrame(rows)

        _matrix, decisions = build_demographic_difference_matrix(terminal, terminal)

        sex_admissions = decisions[
            decisions["dimension"].eq("sex")
            & decisions["outcome"].eq("admissions")
        ].iloc[0]
        self.assertTrue(sex_admissions["mentionable_in_section5_3"])


class OccupationCaseFigureTests(unittest.TestCase):
    @staticmethod
    def _synthetic_paths() -> pd.DataFrame:
        rows = []
        for case_index, case_id in enumerate(CASE_ORDER):
            for age_index, group_id in enumerate(
                [
                    "age_22_25",
                    "age_26_30",
                    "age_31_34",
                    "age_35_40",
                    "age_41_49",
                    "age_50_plus",
                ]
            ):
                for period, value in [
                    ("2022-10", 1.0),
                    (
                        "2023-06",
                        1.0
                        + (case_index + 1)
                        * (age_index - 2)
                        * 0.02,
                    ),
                ]:
                    rows.append(
                        {
                            "case_id": case_id,
                            "variant_id": "primary",
                            "dimension": "age",
                            "group_id": group_id,
                            "outcome": "admissions",
                            "period": period,
                            "path_index": value,
                        }
                    )
        return pd.DataFrame(rows)

    @staticmethod
    def _synthetic_terminal() -> pd.DataFrame:
        rows = []
        for case_index, case_id in enumerate(CASE_ORDER):
            for age_index, group_id in enumerate(
                [
                    "age_22_25",
                    "age_26_30",
                    "age_31_34",
                    "age_35_40",
                    "age_41_49",
                    "age_50_plus",
                ]
            ):
                rows.append(
                    {
                        "case_id": case_id,
                        "variant_id": "primary",
                        "dimension": "age",
                        "group_id": group_id,
                        "outcome": "admissions",
                        "terminal_change_pct": (case_index - 2.5)
                        * (age_index + 1),
                        "support_status": "adequate",
                    }
                )
        return pd.DataFrame(rows)

    def test_age_figure_contains_six_panels_six_age_paths_and_all_exports(self) -> None:
        rows = []
        for case_index, case_id in enumerate(CASE_ORDER):
            for age_index, group_id in enumerate(
                [
                    "age_22_25",
                    "age_26_30",
                    "age_31_34",
                    "age_35_40",
                    "age_41_49",
                    "age_50_plus",
                ]
            ):
                for period, value in [("2022-10", 1.0), ("2022-12", 1.0 + 0.01 * (case_index + age_index))]:
                    rows.append(
                        {
                            "case_id": case_id,
                            "variant_id": "primary",
                            "dimension": "age",
                            "group_id": group_id,
                            "outcome": "admissions",
                            "period": period,
                            "path_index": value,
                        }
                    )
        paths = pd.DataFrame(rows)

        figure = make_age_paths_figure(paths, "admissions")

        self.assertEqual(len(figure.axes), 6)
        for axis in figure.axes:
            age_lines = [
                line
                for line in axis.lines
                if str(line.get_gid()).startswith("age-path-")
            ]
            self.assertEqual(len(age_lines), 6)
            self.assertTrue(any(line.get_gid() == "shock-line" for line in axis.lines))
        with tempfile.TemporaryDirectory() as directory:
            exported = save_figure_bundle(figure, Path(directory), "test_figure")
            self.assertEqual({path.suffix for path in exported}, {".png", ".pdf", ".svg"})
            self.assertTrue(all(path.stat().st_size > 0 for path in exported))

    def test_layout_a_uses_six_case_panels_with_case_specific_y_scales(self) -> None:
        figure = make_age_paths_free_scale_figure(
            self._synthetic_paths(),
            "admissions",
        )

        self.assertEqual(
            figure._suptitle.get_text(),
            "Admissões por caso e idade",
        )
        self.assertEqual(len(figure.axes), 6)
        y_limits = []
        for axis in figure.axes:
            age_lines = [
                line
                for line in axis.lines
                if str(line.get_gid()).startswith("age-path-")
            ]
            self.assertEqual(len(age_lines), 6)
            self.assertTrue(
                any(line.get_gid() == "shock-line" for line in axis.lines)
            )
            y_limits.append(tuple(round(value, 3) for value in axis.get_ylim()))
        self.assertGreater(len(set(y_limits)), 1)

    def test_official_age_figure_uses_the_selected_layout_a(self) -> None:
        figure = make_age_paths_figure(
            self._synthetic_paths(),
            "admissions",
        )

        self.assertGreater(figure.get_figheight(), figure.get_figwidth())
        y_limits = {
            tuple(round(value, 3) for value in axis.get_ylim())
            for axis in figure.axes
        }
        self.assertGreater(len(y_limits), 1)

    def test_layout_b_splits_younger_and_older_ages_without_dropping_paths(
        self,
    ) -> None:
        figure = make_age_paths_split_figure(
            self._synthetic_paths(),
            "admissions",
        )

        self.assertEqual(len(figure.axes), 12)
        for row in range(6):
            younger_axis = figure.axes[row * 2]
            older_axis = figure.axes[row * 2 + 1]
            younger_lines = [
                line
                for line in younger_axis.lines
                if str(line.get_gid()).startswith("age-path-")
            ]
            older_lines = [
                line
                for line in older_axis.lines
                if str(line.get_gid()).startswith("age-path-")
            ]
            self.assertEqual(len(younger_lines), 3)
            self.assertEqual(len(older_lines), 3)
            self.assertEqual(
                tuple(round(value, 3) for value in younger_axis.get_ylim()),
                tuple(round(value, 3) for value in older_axis.get_ylim()),
            )

    def test_layout_c_is_a_six_by_six_annotated_terminal_heatmap(self) -> None:
        figure = make_age_terminal_heatmap(
            self._synthetic_terminal(),
            "admissions",
        )

        self.assertEqual(len(figure.axes), 2)
        heatmap_axis = figure.axes[0]
        self.assertEqual(len(heatmap_axis.images), 1)
        self.assertEqual(len(heatmap_axis.get_xticks()), 6)
        self.assertEqual(len(heatmap_axis.get_yticks()), 6)
        value_annotations = [
            text for text in heatmap_axis.texts if text.get_gid() == "heatmap-value"
        ]
        self.assertEqual(len(value_annotations), 36)


class OccupationCaseTableTests(unittest.TestCase):
    def test_result_selection_log_separates_main_findings_from_appendix_exploration(
        self,
    ) -> None:
        keys = [
            ("software_developers", "age", "age_22_25", "admissions", -10.0),
            (
                "software_developers",
                "age",
                "age_22_25",
                "real_admission_wage",
                -3.0,
            ),
            (
                "software_developers",
                "race_color",
                "race_black_combined",
                "admissions",
                12.0,
            ),
            ("software_developers", "sex", "women", "admissions", 2.0),
        ]
        terminal = pd.DataFrame(
            [
                {
                    "case_id": case_id,
                    "variant_id": "primary",
                    "dimension": dimension,
                    "group_id": group_id,
                    "outcome": outcome,
                    "terminal_change_pct": value,
                    "support_status": "adequate",
                    "terminal_months": 6,
                }
                for case_id, dimension, group_id, outcome, value in keys
            ]
        )
        sensitivities = terminal.rename(
            columns={
                "terminal_change_pct": "main_terminal_change_pct",
                "support_status": "main_support_status",
            }
        ).copy()
        sensitivities["normalization_delta_pp"] = 1.0
        sensitivities["same_month_delta_pp"] = 2.0
        sensitivities["alternative_normalization_change_pct"] = (
            sensitivities["main_terminal_change_pct"]
            + sensitivities["normalization_delta_pp"]
        )
        sensitivities["same_month_change_pct"] = (
            sensitivities["main_terminal_change_pct"]
            + sensitivities["same_month_delta_pp"]
        )
        sensitivities["raw_wage_delta_pp"] = -100.0
        sensitivities["cell_mean_winsorization_delta_pp"] = -100.0
        diagnostics = terminal[
            ["case_id", "variant_id", "dimension", "group_id", "outcome"]
        ].copy()
        diagnostics["pre_months_observed"] = 22
        diagnostics["annualized_log_slope_pct"] = 0.0
        diagnostics["coefficient_of_variation"] = 0.1
        mention_decisions = pd.DataFrame(
            [
                {
                    "dimension": "race_color",
                    "outcome": "admissions",
                    "mentionable_in_section5_3": True,
                },
                {
                    "dimension": "sex",
                    "outcome": "admissions",
                    "mentionable_in_section5_3": False,
                },
            ]
        )

        observed = build_result_selection_log(
            terminal,
            sensitivities,
            diagnostics,
            mention_decisions,
        ).set_index(["dimension", "outcome"])

        self.assertEqual(
            observed.loc[("age", "admissions"), "selection_decision"],
            "main_text_headline",
        )
        self.assertEqual(
            observed.loc[("age", "real_admission_wage"), "selection_decision"],
            "main_text_context",
        )
        self.assertEqual(
            observed.loc[("race_color", "admissions"), "selection_decision"],
            "main_text_secondary",
        )
        self.assertEqual(
            observed.loc[("sex", "admissions"), "selection_decision"],
            "appendix_only",
        )
        self.assertTrue(observed["stable_across_time_baselines"].all())

    def test_compact_exposure_table_has_six_cases_and_separates_no_score(self) -> None:
        dictionary = load_occupation_dictionary(DICTIONARY_PATH)
        rows = []
        for case_id in CASE_ORDER:
            row = {
                "case_id": case_id,
                "pre_admissions": 100,
                "covered_admissions": 90,
                "score_coverage_pct": 90.0,
                "Exposed: Gradient 3": 80.0,
                "Exposed: Gradient 2": 0.0,
                "Exposed: Gradient 1": 0.0,
                "Minimal Exposure": 0.0,
                "Not Exposed": 10.0,
                "No score": 10.0,
            }
            rows.append(row)

        table = build_exposure_summary_table(pd.DataFrame(rows), dictionary)

        self.assertEqual(len(table), 6)
        self.assertTrue(table["Composição OIT no Brasil"].str.contains("sem escore").all())
        self.assertFalse(table["Composição OIT no Brasil"].str.contains("exposição zero").any())

    def test_csv_and_markdown_are_written_from_the_same_number_of_rows(self) -> None:
        frame = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        with tempfile.TemporaryDirectory() as directory:
            csv_path, md_path = write_table_pair(frame, Path(directory), "table")
            markdown_rows = [
                line
                for line in md_path.read_text(encoding="utf-8").splitlines()
                if line.startswith("|")
            ]
            self.assertEqual(len(pd.read_csv(csv_path)), 2)
            self.assertEqual(len(markdown_rows) - 2, 2)

    def test_dissertation_places_section5_3_before_appendix_with_real_links(
        self,
    ) -> None:
        manuscript_path = ROOT / "dissetação_texto.md"
        manuscript = manuscript_path.read_text(encoding="utf-8")
        heading = "## **5.3 Casos ocupacionais e trajetórias por idade**"
        appendix = "# Anexo A: Contrastes DDD e diagnósticos das heterogeneidades"
        section = manuscript[
            manuscript.index(heading) : manuscript.index(appendix)
        ]

        self.assertLess(manuscript.index(heading), manuscript.index(appendix))
        self.assertNotIn("replicação direta", section.lower())
        self.assertNotIn("efeito causal por profissão", section.lower())
        for relative_path in [
            "outputs/section5_3_occupation_cases/figures/figure_5_3_1_occupation_cases_admissions_by_age.png",
            "outputs/section5_3_occupation_cases/figures/figure_5_3_2_occupation_cases_real_admission_wage_by_age.png",
        ]:
            self.assertIn(relative_path, section)
            self.assertTrue((ROOT / relative_path).exists())


if __name__ == "__main__":
    unittest.main()
