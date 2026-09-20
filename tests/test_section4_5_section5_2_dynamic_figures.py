import math
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.section5_2_dynamic_figures import (  # noqa: E402
    add_winsorized_wage_path,
    complete_group_panel,
    estimate_dynamic_ddd,
    estimate_dynamic_did,
    expected_contract_counts,
    expected_figure_filenames,
    expected_model_specs,
    figure_layout,
    normalize_paths,
    plot_event_study_panels,
    plot_path_panels,
    safely_estimate_dynamic,
    support_diagnostics,
    validate_long_frames,
)


class Section52DynamicFigureDataTests(unittest.TestCase):
    @staticmethod
    def _base() -> pd.DataFrame:
        rows = []
        for cbo, role, treat in [
            ("1111", "treated", 1),
            ("2222", "control", 0),
        ]:
            for t, periodo in [(-1, "2022-11"), (0, "2022-12")]:
                rows.append(
                    {
                        "cbo_4d": cbo,
                        "ano": 2022,
                        "mes": 11 if t == -1 else 12,
                        "periodo": periodo,
                        "t": t,
                        "scenario_role": role,
                        "scenario_treat": treat,
                        "indice": 100.0,
                        "admissoes": 99,
                        "desligamentos": 98,
                    }
                )
        return pd.DataFrame(rows)

    def test_contract_counts_cover_every_model_path_and_figure(self) -> None:
        self.assertEqual(
            expected_contract_counts(),
            {
                "models": 63,
                "coefficient_rows": 2331,
                "pretrend_rows": 63,
                "path_rows": 4662,
                "figures": 36,
            },
        )

    def test_complete_group_panel_fills_flows_but_preserves_missing_wages(self) -> None:
        raw = pd.DataFrame(
            {
                "dimension": ["sex"],
                "group_id": ["women"],
                "subgroup": ["target"],
                "cbo_4d": ["1111"],
                "ano": [2022],
                "mes": [11],
                "admissoes": [2],
                "desligamentos": [1],
                "salario_sum": [200.0],
                "salario_count": [2],
            }
        )

        out = complete_group_panel(raw, self._base(), "sex", "women")

        self.assertEqual(len(out), 8)
        observed = out[
            out["cbo_4d"].eq("1111")
            & out["subgroup"].eq("target")
            & out["t"].eq(-1)
        ].iloc[0]
        self.assertEqual(observed["admissoes"], 2)
        self.assertAlmostEqual(observed["ln_salario_real_adm"], math.log(100.0))

        missing = out[
            out["cbo_4d"].eq("2222")
            & out["subgroup"].eq("target")
            & out["t"].eq(0)
        ].iloc[0]
        self.assertEqual(missing["admissoes"], 0)
        self.assertEqual(missing["desligamentos"], 0)
        self.assertTrue(pd.isna(missing["ln_salario_real_adm"]))

    def test_flow_paths_use_each_cbo_pre_period_log_baseline(self) -> None:
        rows = []
        for cbo, role, treat, post_count in [
            ("1111", "treated", 1, 3),
            ("2222", "control", 0, 1),
        ]:
            for t, count in [(-1, 1), (0, post_count)]:
                rows.append(
                    {
                        "cbo_4d": cbo,
                        "scenario_role": role,
                        "scenario_treat": treat,
                        "t": t,
                        "admissoes": count,
                        "desligamentos": count,
                        "ln_salario_real_adm": math.log(100.0),
                    }
                )

        paths = normalize_paths(
            pd.DataFrame(rows),
            dimension="national",
            group_id="national",
            group_label="Nacional",
            outcome="ln_admissoes",
            event_times=[-1, 0],
            pre_min=-1,
            pre_max=-1,
        )

        treated = paths[paths["scenario_role"].eq("treated") & paths["t"].eq(0)].iloc[0]
        control = paths[paths["scenario_role"].eq("control") & paths["t"].eq(0)].iloc[0]
        self.assertAlmostEqual(treated["path_index"], 200.0)
        self.assertAlmostEqual(control["path_index"], 100.0)
        self.assertEqual(set(paths["path_status"]), {"estimated"})
        self.assertEqual(set(paths["window_rule"]), {"strict_no_tail_binning"})

    def test_winsorization_changes_only_the_descriptive_wage_field(self) -> None:
        panel = pd.DataFrame(
            {
                "salario_adm": [10.0, 20.0, 1000.0],
                "indice": [100.0, 100.0, 100.0],
                "ln_salario_real_adm": [math.log(10.0), math.log(20.0), math.log(1000.0)],
            }
        )

        out = add_winsorized_wage_path(panel, wage_column="salario_adm", bounds=(15.0, 100.0))

        self.assertEqual(out["ln_salario_real_adm"].tolist(), panel["ln_salario_real_adm"].tolist())
        self.assertAlmostEqual(out.loc[0, "ln_salario_real_adm_path"], math.log(15.0))
        self.assertAlmostEqual(out.loc[2, "ln_salario_real_adm_path"], math.log(100.0))


class Section52DynamicEstimatorTests(unittest.TestCase):
    @staticmethod
    def _dynamic_panel(with_subgroups: bool) -> pd.DataFrame:
        rows = []
        effects = {-2: 0.0, -1: 0.0, 0: 0.4, 1: 0.7}
        for cbo_index in range(8):
            treat = int(cbo_index < 4)
            role = "treated" if treat else "control"
            subgroups = ["target", "complement"] if with_subgroups else [None]
            for subgroup in subgroups:
                target = int(subgroup == "target")
                for t in [-2, -1, 0, 1]:
                    period = str(pd.Period("2022-11", freq="M") + (t + 1))
                    dynamic_effect = effects[t] * treat * (target if with_subgroups else 1)
                    deterministic_noise = 0.001 * ((cbo_index + t + target) % 3)
                    rows.append(
                        {
                            "cbo_4d": f"{1000 + cbo_index}",
                            "periodo": period,
                            "t": t,
                            "scenario_role": role,
                            "scenario_treat": treat,
                            "subgroup": subgroup,
                            "group_indicator": target,
                            "ln_admissoes": (
                                0.2 * cbo_index
                                + 0.05 * t
                                + 0.1 * target
                                + 0.08 * treat * target
                                + dynamic_effect
                                + deterministic_noise
                            ),
                        }
                    )
        return pd.DataFrame(rows)

    def test_dynamic_did_recovers_known_national_effects(self) -> None:
        coefficients, pretrend = estimate_dynamic_did(
            self._dynamic_panel(with_subgroups=False),
            dimension="national",
            group_id="national",
            group_label="Nacional",
            outcome="ln_admissoes",
            event_times=[-2, -1, 0, 1],
            control_columns=[],
        )

        by_t = coefficients.set_index("t")
        self.assertAlmostEqual(by_t.loc[-1, "coef"], 0.0)
        self.assertAlmostEqual(by_t.loc[0, "coef"], 0.4, delta=0.01)
        self.assertAlmostEqual(by_t.loc[1, "coef"], 0.7, delta=0.01)
        self.assertEqual(set(coefficients["estimand"]), {"did"})
        self.assertEqual(set(coefficients["window_rule"]), {"strict_no_tail_binning"})
        self.assertEqual(pretrend["n_pre_coefficients"], 1)

    def test_failed_estimation_keeps_the_reference_and_requested_grid(self) -> None:
        panel = pd.DataFrame(
            {
                "cbo_4d": ["1111", "1111"],
                "periodo": ["2022-11", "2022-12"],
                "t": [-1, 0],
                "scenario_role": ["treated", "treated"],
                "scenario_treat": [1, 1],
                "admissoes": [1, 1],
                "desligamentos": [1, 1],
                "ln_admissoes": [math.log(2), math.log(2)],
            }
        )

        coefficients, pretrend = safely_estimate_dynamic(
            panel,
            dimension="national",
            group_id="national",
            group_label="Nacional",
            outcome="ln_admissoes",
            estimand="did",
            event_times=[-1, 0],
            control_columns=[],
        )

        self.assertEqual(len(coefficients), 2)
        reference = coefficients[coefficients["t"].eq(-1)].iloc[0]
        self.assertEqual(reference["coef"], 0.0)
        self.assertEqual(reference["coefficient_status"], "reference")
        self.assertEqual(set(coefficients["result_status"]), {"failed_estimation"})
        self.assertEqual(pretrend["pretrend_status"], "not_available")

    def test_dynamic_ddd_recovers_known_target_vs_complement_effects(self) -> None:
        coefficients, pretrend = estimate_dynamic_ddd(
            self._dynamic_panel(with_subgroups=True),
            dimension="sex",
            group_id="women",
            group_label="Mulheres",
            outcome="ln_admissoes",
            event_times=[-2, -1, 0, 1],
            control_columns=[],
        )

        by_t = coefficients.set_index("t")
        self.assertAlmostEqual(by_t.loc[-1, "coef"], 0.0)
        self.assertAlmostEqual(by_t.loc[0, "coef"], 0.4, delta=0.01)
        self.assertAlmostEqual(by_t.loc[1, "coef"], 0.7, delta=0.01)
        self.assertEqual(set(coefficients["estimand"]), {"ddd"})
        self.assertEqual(pretrend["n_pre_coefficients"], 1)


class Section52DynamicFigureRenderTests(unittest.TestCase):
    def test_layouts_match_the_dimension_contract(self) -> None:
        self.assertEqual(figure_layout(1), (1, 1, (8.2, 5.4)))
        self.assertEqual(figure_layout(2), (1, 2, (12.0, 5.4)))
        self.assertEqual(figure_layout(3), (1, 3, (13.8, 5.0)))
        self.assertEqual(figure_layout(6), (2, 3, (13.8, 8.2)))

    def test_event_and_path_renderers_write_nonempty_pngs(self) -> None:
        coefficients = []
        pretrends = []
        paths = []
        for group_id, group_label in [("men", "Homens"), ("women", "Mulheres")]:
            for t, coef in [(-1, 0.0), (0, 0.05)]:
                coefficients.append(
                    {
                        "dimension": "sex",
                        "group_id": group_id,
                        "group_label": group_label,
                        "outcome": "ln_admissoes",
                        "estimand": "ddd",
                        "t": t,
                        "coef": coef,
                        "ci_low": coef - 0.02,
                        "ci_high": coef + 0.02,
                        "coefficient_status": "reference" if t == -1 else "estimated",
                    }
                )
            pretrends.append(
                {
                    "dimension": "sex",
                    "group_id": group_id,
                    "outcome": "ln_admissoes",
                    "pretrend_status": "pass",
                    "joint_p_value": 0.50,
                    "power_status": "adequate",
                }
            )
            for role in ["treated", "control"]:
                for t, index in [(-1, 100.0), (0, 95.0 if role == "treated" else 101.0)]:
                    paths.append(
                        {
                            "dimension": "sex",
                            "group_id": group_id,
                            "group_label": group_label,
                            "outcome": "ln_admissoes",
                            "scenario_role": role,
                            "t": t,
                            "path_index": index,
                            "path_status": "estimated",
                        }
                    )

        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.png"
            path_path = Path(tmp) / "paths.png"
            plot_event_study_panels(
                pd.DataFrame(coefficients),
                pd.DataFrame(pretrends),
                dimension="sex",
                outcome="ln_admissoes",
                output_path=event_path,
            )
            plot_path_panels(
                pd.DataFrame(paths),
                dimension="sex",
                outcome="ln_admissoes",
                output_path=path_path,
            )
            self.assertGreater(event_path.stat().st_size, 0)
            self.assertGreater(path_path.stat().st_size, 0)


class Section52DynamicBundleContractTests(unittest.TestCase):
    def test_expected_names_cover_36_unique_pngs_without_dismissal_wages(self) -> None:
        filenames = expected_figure_filenames()

        self.assertEqual(len(filenames), 36)
        self.assertEqual(len(set(filenames)), 36)
        self.assertTrue(all(name.endswith(".png") for name in filenames))
        self.assertFalse(any("dismissal_wage" in name for name in filenames))

    def test_thin_support_is_visible_for_three_treated_and_seven_controls(self) -> None:
        rows = []
        for index in range(10):
            role = "treated" if index < 3 else "control"
            rows.append(
                {
                    "cbo_4d": f"{3000 + index}",
                    "scenario_role": role,
                    "admissoes": 1,
                    "desligamentos": 1,
                    "ln_admissoes": math.log(2),
                }
            )

        diagnostic = support_diagnostics(pd.DataFrame(rows), "ln_admissoes")

        self.assertEqual(diagnostic, {"power_status": "thin", "treated_cbo": 3, "control_cbo": 7})

    def test_long_contract_accepts_the_complete_grid_and_rejects_dismissal_wages(self) -> None:
        models = expected_model_specs()
        coefficient_rows = []
        pretrend_rows = []
        path_rows = []
        for model in models:
            for t in range(-12, 25):
                coefficient_rows.append(
                    {
                        **model,
                        "outcome_label": model["outcome"],
                        "t": t,
                        "coef": 0.0,
                        "coefficient_status": "reference" if t == -1 else "estimated",
                    }
                )
            pretrend_rows.append({**model, "pretrend_status": "pass"})
            for role in ["treated", "control"]:
                for t in range(-12, 25):
                    path_rows.append(
                        {
                            "dimension": model["dimension"],
                            "group_id": model["group_id"],
                            "group_label": model["group_label"],
                            "outcome": model["outcome"],
                            "scenario_role": role,
                            "t": t,
                            "path_status": "estimated",
                            "path_index": 100.0,
                        }
                    )

        coefficients = pd.DataFrame(coefficient_rows)
        pretrends = pd.DataFrame(pretrend_rows)
        paths = pd.DataFrame(path_rows)
        validate_long_frames(coefficients, pretrends, paths)

        coefficients.loc[0, "outcome"] = "ln_salario_real_desl"
        with self.assertRaisesRegex(RuntimeError, "dismissal wage"):
            validate_long_frames(coefficients, pretrends, paths)

if __name__ == "__main__":
    unittest.main()
