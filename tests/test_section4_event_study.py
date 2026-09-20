import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_event_study.data import (
    add_continuous_exposure,
    add_net_flow_measures,
    add_pre_treatment_control_interactions,
    add_real_wage_measures,
)
from section4_event_study.formatting import stars
from section4_event_study.heterogeneity import (
    DIMENSIONS,
    _add_triple_terms,
    _estimate_group_did,
    _estimate_triple,
    _group_power,
    build_pre_treatment_income_group_assignments,
    estimate_heterogeneity,
    group_series_for_dimension,
    income_group_for_median,
)
from section4_event_study.treatment import assign_roles, assign_single_gradient_roles, validate_base_and_broad_roles


class TreatmentRoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.classification = pd.DataFrame(
            {
                "cbo_4d": ["1111", "2222", "3333", "4444", "5555", "6666"],
                "mte_match_status": [
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "sem_match_mte_no_result",
                ],
                "cbo_ilo_gradient": [
                    "Not Exposed",
                    "Minimal Exposure",
                    "Exposed: Gradient 1",
                    "Exposed: Gradient 4",
                    "No score",
                    "Exposed: Gradient 2",
                ],
                "isco08_mean_score": [0.1, 0.3, 0.45, 0.65, np.nan, 0.5],
                "isco08_pooled_sd": [0.05, 0.12, 0.2, 0.1, np.nan, 0.1],
                "role__baseline_mte2d_top20_vs_rest": [
                    "control",
                    "control",
                    "treated",
                    "treated",
                    "excluded",
                    "excluded",
                ],
            }
        )

    def test_strict_base_excludes_minimal_no_score_and_unmatched(self) -> None:
        roles = assign_roles(self.classification, "main_strict")

        included = roles[roles["scenario_role"].isin(["treated", "control"])]

        self.assertEqual(set(included["cbo_4d"]), {"1111", "3333", "4444"})
        self.assertEqual(set(included.loc[included["scenario_role"].eq("control"), "cbo_ilo_gradient"]), {"Not Exposed"})
        self.assertNotIn("Minimal Exposure", set(included["cbo_ilo_gradient"]))
        self.assertNotIn("No score", set(included["cbo_ilo_gradient"]))
        self.assertTrue(included["mte_match_status"].eq("matched_official_mte").all())

    def test_broad_control_includes_minimal_exposure(self) -> None:
        roles = assign_roles(self.classification, "main_broad_control")

        controls = roles[roles["scenario_role"].eq("control")]

        self.assertEqual(set(controls["cbo_ilo_gradient"]), {"Not Exposed", "Minimal Exposure"})
        self.assertIn("2222", set(controls["cbo_4d"]))

    def test_base_and_broad_validation_accept_expected_roles(self) -> None:
        strict = assign_roles(self.classification, "main_strict")
        broad = assign_roles(self.classification, "main_broad_control")

        validate_base_and_broad_roles(strict, broad)

    def test_single_gradient_roles_compare_one_gradient_to_not_exposed(self) -> None:
        roles = assign_single_gradient_roles(self.classification, "Exposed: Gradient 1", "g1_vs_not_exposed")

        included = roles[roles["scenario_role"].isin(["treated", "control"])]

        self.assertEqual(set(included["cbo_4d"]), {"1111", "3333"})
        self.assertEqual(set(roles.loc[roles["scenario_role"].eq("treated"), "cbo_ilo_gradient"]), {"Exposed: Gradient 1"})
        self.assertEqual(set(roles.loc[roles["scenario_role"].eq("control"), "cbo_ilo_gradient"]), {"Not Exposed"})


class ContinuousExposureTests(unittest.TestCase):
    def test_continuous_exposure_is_zscore_of_mean_plus_sd(self) -> None:
        classification = pd.DataFrame(
            {
                "isco08_mean_score": [0.1, 0.2, 0.4],
                "isco08_pooled_sd": [0.2, 0.2, 0.4],
            }
        )

        out = add_continuous_exposure(classification)

        raw = pd.Series([0.3, 0.4, 0.8], dtype=float)
        expected = (raw - raw.mean()) / raw.std(ddof=0)
        np.testing.assert_allclose(out["continuous_exposure"], expected)


class RealWageTests(unittest.TestCase):
    def test_real_wage_measures_use_monthly_ipca_index_base_100(self) -> None:
        panel = pd.DataFrame(
            {
                "ano": [2024, 2025],
                "mes": [12, 1],
                "salario_medio_adm": [2000.0, 2100.0],
                "salario_medio_desl": [1800.0, 2200.0],
            }
        )
        ipca = pd.DataFrame(
            {
                "ano": [2024, 2025],
                "mes": [12, 1],
                "indice": [100.0, 105.0],
            }
        )

        out = add_real_wage_measures(panel, ipca)

        np.testing.assert_allclose(out["salario_real_adm"], [2000.0, 2000.0])
        np.testing.assert_allclose(out["salario_real_desl"], [1800.0, 2200.0 * 100 / 105.0])
        np.testing.assert_allclose(out["ln_salario_real_adm"], np.log([2000.0, 2000.0]))
        np.testing.assert_allclose(out["ln_salario_real_desl"], np.log([1800.0, 2200.0 * 100 / 105.0]))


class PreTreatmentControlTests(unittest.TestCase):
    def test_pre_treatment_controls_are_cbo_baselines_interacted_with_post(self) -> None:
        panel = pd.DataFrame(
            {
                "cbo_4d": ["1111", "1111", "2222", "2222"],
                "periodo_num": [202201, 202301, 202201, 202301],
                "post": [0, 1, 0, 1],
                "idade_media_adm": [30.0, 35.0, 40.0, 45.0],
                "pct_mulher_adm": [0.2, 0.4, 0.6, 0.8],
                "pct_superior_adm": [0.1, 0.3, 0.5, 0.7],
                "pct_negra_adm": [0.3, 0.5, 0.7, 0.9],
            }
        )

        out, interaction_cols = add_pre_treatment_control_interactions(panel, treatment_period=202212)

        self.assertEqual(
            interaction_cols,
            [
                "post_pre_idade_media_adm",
                "post_pre_pct_mulher_adm",
                "post_pre_pct_superior_adm",
                "post_pre_pct_negra_adm",
            ],
        )
        self.assertEqual(out.loc[1, "pre_idade_media_adm"], 30.0)
        self.assertEqual(out.loc[3, "pre_pct_mulher_adm"], 0.6)
        self.assertEqual(out.loc[0, "post_pre_idade_media_adm"], 0.0)
        self.assertEqual(out.loc[1, "post_pre_idade_media_adm"], 30.0)
        self.assertEqual(out.loc[3, "post_pre_pct_negra_adm"], 0.7)


class NetFlowTests(unittest.TestCase):
    def test_net_flow_measures_use_admissions_minus_dismissals_and_pre_admission_scale(self) -> None:
        panel = pd.DataFrame(
            {
                "cbo_4d": ["1111", "1111", "2222", "2222"],
                "periodo_num": [202201, 202301, 202201, 202301],
                "admissoes": [10.0, 4.0, 0.0, 3.0],
                "desligamentos": [7.0, 9.0, 0.0, 1.0],
                "pre_adm_weight": [10.0, 10.0, np.nan, 2.0],
            }
        )

        out = add_net_flow_measures(panel, pre_adm_col="pre_adm_weight")

        np.testing.assert_allclose(out["saldo"], [3.0, -5.0, 0.0, 2.0])
        np.testing.assert_allclose(out["asinh_saldo"], np.arcsinh([3.0, -5.0, 0.0, 2.0]))
        np.testing.assert_allclose(out.loc[[0, 1, 3], "saldo_per_pre_adm"], [0.3, -0.5, 1.0])
        self.assertTrue(pd.isna(out.loc[2, "saldo_per_pre_adm"]))
        self.assertTrue(pd.isna(out.loc[2, "saldo_flow_rate"]))
        np.testing.assert_allclose(out.loc[[0, 1, 3], "saldo_flow_rate"], [3 / 17, -5 / 13, 2 / 4])


class HeterogeneityEstimatorTests(unittest.TestCase):
    @staticmethod
    def _synthetic_group_panel() -> pd.DataFrame:
        rng = np.random.default_rng(20260711)
        rows = []
        periods = list(range(-6, 6))
        for cbo_index in range(40):
            treated = int(cbo_index >= 20)
            cbo_effect = rng.normal(scale=0.20)
            for relative_month in periods:
                post = int(relative_month >= 0)
                period_effect = 0.01 * relative_month
                for subgroup in ["complement", "target"]:
                    target = int(subgroup == "target")
                    controls = rng.normal(size=4)
                    treatment_effect = 0.10 + (-0.30 * target)
                    outcome = (
                        cbo_effect
                        + period_effect
                        + 0.15 * target
                        + treatment_effect * post * treated
                        + 0.03 * controls[0]
                        - 0.02 * controls[1]
                        + rng.normal(scale=0.01)
                    )
                    rows.append(
                        {
                            "outcome": outcome,
                            "cbo_4d": f"{cbo_index:04d}",
                            "periodo": f"m{relative_month:+03d}",
                            "subgroup": subgroup,
                            "post": post,
                            "trend": relative_month,
                            "scenario_treat": treated,
                            "idade_media_adm": controls[0],
                            "pct_mulher_adm": controls[1],
                            "pct_superior_adm": controls[2],
                            "pct_negra_adm": controls[3],
                        }
                    )
        data = pd.DataFrame(rows)
        return _add_triple_terms(data, data["subgroup"].eq("target"))

    def test_group_did_recovers_target_effect_and_ddd_recovers_difference(self) -> None:
        data = self._synthetic_group_panel()

        group = _estimate_group_did(data, "outcome", "cbo_4d + periodo")
        ddd = _estimate_triple(data, "outcome", "cbo_4d + periodo + subgroup")

        self.assertEqual(group["group_result_status"], "estimated")
        self.assertAlmostEqual(group["group_coef"], -0.20, delta=0.02)
        self.assertEqual(ddd["result_status"], "estimated")
        self.assertAlmostEqual(ddd["coef"], -0.30, delta=0.02)
        self.assertLess(ddd["p_value"], 0.01)
        self.assertEqual(ddd["wald_test_method"], "wald_test_R_beta_eq_q_chi2")

    def test_sex_and_race_codes_follow_caged_contract(self) -> None:
        raw = pd.DataFrame(
            {
                "sexo": [1, 3, 2, np.nan, np.nan, np.nan, np.nan],
                "raca_cor": [1, 2, 3, 4, 5, 6, 9],
            }
        )

        self.assertEqual(group_series_for_dimension(raw, "sex").tolist()[:2], ["men", "women"])
        self.assertTrue(group_series_for_dimension(raw, "sex").isna().iloc[2:].all())
        self.assertEqual(
            group_series_for_dimension(raw, "race_color").tolist()[:5],
            ["race_white", "race_black", "race_pardo", "race_yellow", "race_indigenous"],
        )
        alternative = group_series_for_dimension(raw, "race_color_b")
        self.assertEqual(
            alternative.tolist()[:3],
            ["race_white", "race_black_combined", "race_black_combined"],
        )
        self.assertTrue(alternative.isna().iloc[3:].all())

    def test_pnad_age_groups_use_the_18_to_65_universe_and_exact_boundaries(self) -> None:
        raw = pd.DataFrame(
            {
                "idade": [17, 18, 24, 25, 34, 35, 44, 45, 54, 55, 65, 66],
            }
        )

        groups = group_series_for_dimension(raw, "age_pnad")

        self.assertTrue(pd.isna(groups.iloc[0]))
        self.assertEqual(
            groups.iloc[1:11].tolist(),
            [
                "age_18_24",
                "age_18_24",
                "age_25_34",
                "age_25_34",
                "age_35_44",
                "age_35_44",
                "age_45_54",
                "age_45_54",
                "age_55_plus",
                "age_55_plus",
            ],
        )
        self.assertTrue(pd.isna(groups.iloc[11]))

    def test_pnad_income_groups_match_first_stage_minimum_wage_boundaries(self) -> None:
        cases = [
            (0.0, None),
            (1.0, "income_up_to_1sm"),
            (1.0001, "income_1_2sm"),
            (2.0, "income_1_2sm"),
            (2.0001, "income_2_3sm"),
            (3.0, "income_2_3sm"),
            (3.0001, "income_3_5sm"),
            (5.0, "income_3_5sm"),
            (5.0001, "income_5_plus_sm"),
            (np.nan, None),
        ]

        self.assertEqual(
            [income_group_for_median(value, scheme="pnad") for value, _expected in cases],
            [expected for _value, expected in cases],
        )
        self.assertEqual(income_group_for_median(2.0), "low_income")
        self.assertEqual(income_group_for_median(5.0), "middle_income")
        self.assertEqual(income_group_for_median(5.0001), "high_income")
        with self.assertRaisesRegex(ValueError, "Unknown income grouping scheme"):
            income_group_for_median(2.0, scheme="unknown")

    def test_income_estimator_supports_the_additional_pnad_scheme(self) -> None:
        rng = np.random.default_rng(20260718)
        group_ids = [group_id for group_id, _label in DIMENSIONS["income_pnad"]["groups"]]
        rows = []
        income_groups = {}
        for cbo_index in range(50):
            cbo_4d = f"{cbo_index:04d}"
            treated = cbo_index % 2
            income_groups[cbo_4d] = group_ids[cbo_index % len(group_ids)]
            for month_index in range(12):
                post = int(month_index >= 6)
                controls = rng.normal(size=4)
                rows.append(
                    {
                        "cbo_4d": cbo_4d,
                        "ano": 2022 if month_index < 6 else 2023,
                        "mes": month_index % 6 + 1,
                        "periodo": f"m{month_index:02d}",
                        "periodo_num": 202201 + month_index,
                        "post": post,
                        "trend": month_index - 6,
                        "scenario_treat": treated,
                        "idade_media_adm": controls[0],
                        "pct_mulher_adm": controls[1],
                        "pct_superior_adm": controls[2],
                        "pct_negra_adm": controls[3],
                        "outcome": 0.2 * post * treated + rng.normal(scale=0.05),
                    }
                )
        panel = pd.DataFrame(rows)

        with patch(
            "section4_event_study.heterogeneity.build_pre_treatment_income_groups",
            return_value=income_groups,
        ) as mocked_groups, patch(
            "section4_event_study.heterogeneity.aggregate_micro_group_pairs",
            return_value=pd.DataFrame(),
        ):
            out = estimate_heterogeneity(
                panel,
                outcomes={"outcome": "Synthetic outcome"},
                dimensions={"income_pnad": DIMENSIONS["income_pnad"]},
            )

        mocked_groups.assert_called_once_with("pnad")
        self.assertEqual(out["dimension"].unique().tolist(), ["income_pnad"])
        self.assertEqual(out["group_id"].tolist(), group_ids)
        self.assertTrue(out["result_status"].eq("estimated").all())

    def test_income_assignment_audit_preserves_medians_and_both_grouping_schemes(self) -> None:
        with patch(
            "section4_event_study.heterogeneity.build_pre_treatment_income_medians",
            return_value={"1111": 1.0, "2222": 2.5, "3333": 6.0},
        ):
            out = build_pre_treatment_income_group_assignments()

        self.assertEqual(
            out.columns.tolist(),
            [
                "cbo_4d",
                "median_pre_treatment_wage_sm",
                "income_group_legacy",
                "income_group_pnad",
            ],
        )
        self.assertEqual(out["cbo_4d"].tolist(), ["1111", "2222", "3333"])
        self.assertEqual(out["income_group_legacy"].tolist(), ["low_income", "middle_income", "high_income"])
        self.assertEqual(
            out["income_group_pnad"].tolist(),
            ["income_up_to_1sm", "income_2_3sm", "income_5_plus_sm"],
        )

    def test_group_power_counts_only_cbos_with_observed_target_flows(self) -> None:
        data = pd.DataFrame(
            {
                "cbo_4d": ["1001", "1002", "2001", "2002"],
                "scenario_treat": [1, 1, 0, 0],
                "group_indicator": [1, 1, 1, 1],
                "admissoes": [3, 0, 2, 0],
                "desligamentos": [0, 0, 0, 0],
                "ln_admissoes": [np.log(4), 0.0, np.log(3), 0.0],
            }
        )

        status, treated, control = _group_power(data, "ln_admissoes")

        self.assertEqual(status, "thin")
        self.assertEqual((treated, control), (1, 1))


class SignificanceStarTests(unittest.TestCase):
    def test_star_thresholds_are_strictly_below_reported_cutoffs(self) -> None:
        self.assertEqual(stars(0.10), "")
        self.assertEqual(stars(0.099999), "*")
        self.assertEqual(stars(0.05), "*")
        self.assertEqual(stars(0.049999), "**")
        self.assertEqual(stars(0.01), "**")
        self.assertEqual(stars(0.009999), "***")


if __name__ == "__main__":
    unittest.main()
