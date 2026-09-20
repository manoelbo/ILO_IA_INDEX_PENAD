import math
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.plot_software_it_flow_event_studies_by_age import (  # noqa: E402
    AGE_ORDER,
    CONTROL_COLUMNS,
    add_dynamic_ddd_terms,
    build_age_pair_panel,
    build_flow_paths,
    classify_pretrend,
    complete_age_flow_panel,
    model_cluster_count,
    model_observation_count,
    plot_ddd_event_studies,
    plot_normalized_flow_paths,
)


class SoftwareITFlowEventStudyTests(unittest.TestCase):
    @staticmethod
    def _roles() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "cbo_4d": ["2123", "1111"],
                "scenario_role": ["treated", "control"],
                "scenario_treat": [1, 0],
            }
        )

    @staticmethod
    def _periods() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "ano": [2022, 2022],
                "mes": [11, 12],
                "periodo": ["2022-11", "2022-12"],
                "t": [-1, 0],
            }
        )

    def test_complete_panel_fills_missing_age_cbo_month_cells_with_zero(self) -> None:
        observed = pd.DataFrame(
            {
                "cbo_4d": ["2123"],
                "age_group": ["age_22_25"],
                "ano": [2022],
                "mes": [11],
                "periodo": ["2022-11"],
                "t": [-1],
                "admissoes": [3],
                "desligamentos": [2],
            }
        )

        out = complete_age_flow_panel(observed, self._roles(), self._periods())

        self.assertEqual(len(out), 2 * len(AGE_ORDER) * 2)
        filled = out[
            out["cbo_4d"].eq("1111")
            & out["age_group"].eq("age_50_plus")
            & out["t"].eq(0)
        ].iloc[0]
        self.assertEqual(filled["admissoes"], 0)
        self.assertEqual(filled["desligamentos"], 0)
        observed_row = out[
            out["cbo_4d"].eq("2123")
            & out["age_group"].eq("age_22_25")
            & out["t"].eq(-1)
        ].iloc[0]
        self.assertEqual(observed_row["admissoes"], 3)
        self.assertEqual(observed_row["scenario_role"], "treated")

    def test_flow_paths_normalize_log_one_plus_counts_to_pre_period(self) -> None:
        rows = []
        for cbo, role, treat, post_count in [
            ("2123", "treated", 1, 3),
            ("1111", "control", 0, 1),
        ]:
            for t, count in [(-1, 1), (0, post_count)]:
                rows.append(
                    {
                        "cbo_4d": cbo,
                        "age_group": "age_22_25",
                        "scenario_role": role,
                        "scenario_treat": treat,
                        "t": t,
                        "admissoes": count,
                        "desligamentos": count,
                    }
                )

        out = build_flow_paths(pd.DataFrame(rows), "ln_admissoes", pre_min=-1, pre_max=-1)

        treated_post = out[out["scenario_role"].eq("treated") & out["t"].eq(0)].iloc[0]
        control_post = out[out["scenario_role"].eq("control") & out["t"].eq(0)].iloc[0]
        self.assertAlmostEqual(treated_post["flow_index"], 200.0)
        self.assertAlmostEqual(control_post["flow_index"], 100.0)
        self.assertAlmostEqual(treated_post["mean_log_change"], math.log(2.0))

    def test_age_pair_uses_all_other_canaries_bands_as_the_complement(self) -> None:
        observed = pd.DataFrame(
            {
                "cbo_4d": ["2123", "2123"],
                "age_group": ["age_22_25", "age_26_30"],
                "ano": [2022, 2022],
                "mes": [12, 12],
                "periodo": ["2022-12", "2022-12"],
                "t": [0, 0],
                "admissoes": [3, 7],
                "desligamentos": [2, 5],
            }
        )
        periods = self._periods().query("t == 0").copy()
        roles = self._roles().query("cbo_4d == '2123'").copy()
        panel = complete_age_flow_panel(observed, roles, periods)
        controls = periods.assign(cbo_4d="2123")
        for column in CONTROL_COLUMNS:
            controls[column] = 0.0

        out = build_age_pair_panel(panel, controls, "age_22_25", "ln_admissoes")

        target = out[out["subgroup"].eq("target")].iloc[0]
        complement = out[out["subgroup"].eq("complement")].iloc[0]
        self.assertEqual(target["flow_count"], 3)
        self.assertEqual(complement["flow_count"], 7)
        self.assertAlmostEqual(target["ln_admissoes"], math.log1p(3))
        self.assertAlmostEqual(complement["ln_admissoes"], math.log1p(7))

    def test_age_pair_keeps_only_cbo_months_with_observed_stage2_controls(self) -> None:
        observed = pd.DataFrame(
            {
                "cbo_4d": ["2123", "2123"],
                "age_group": ["age_22_25", "age_22_25"],
                "ano": [2022, 2022],
                "mes": [11, 12],
                "periodo": ["2022-11", "2022-12"],
                "t": [-1, 0],
                "admissoes": [2, 3],
                "desligamentos": [1, 2],
            }
        )
        roles = self._roles().query("cbo_4d == '2123'").copy()
        panel = complete_age_flow_panel(observed, roles, self._periods())
        controls = self._periods().query("t == -1").assign(cbo_4d="2123")
        for column in CONTROL_COLUMNS:
            controls[column] = 0.0

        out = build_age_pair_panel(panel, controls, "age_22_25", "ln_admissoes")

        self.assertEqual(set(out["t"]), {-1})
        self.assertEqual(len(out), 2)
        self.assertFalse(out[CONTROL_COLUMNS].isna().any().any())

    def test_dynamic_terms_encode_only_the_triple_interaction_for_treated_target(self) -> None:
        rows = []
        for role, treat in [("treated", 1), ("control", 0)]:
            for subgroup in ["target", "complement"]:
                for t in [-1, 0]:
                    rows.append(
                        {
                            "scenario_role": role,
                            "scenario_treat": treat,
                            "subgroup": subgroup,
                            "t": t,
                        }
                    )
        data, terms = add_dynamic_ddd_terms(pd.DataFrame(rows), event_times=[-1, 0])

        self.assertNotIn(-1, terms)
        ddd_term = terms[0]["ddd"]
        treated_target = data[
            data["scenario_role"].eq("treated")
            & data["subgroup"].eq("target")
            & data["t"].eq(0)
        ].iloc[0]
        other_rows = data.drop(index=treated_target.name)
        self.assertEqual(treated_target[ddd_term], 1)
        self.assertEqual(other_rows[ddd_term].sum(), 0)

    def test_pretrend_classification_matches_section4_rules(self) -> None:
        self.assertEqual(classify_pretrend(0, 0.50), "pass")
        self.assertEqual(classify_pretrend(0, 0.08), "warning")
        self.assertEqual(classify_pretrend(0, 0.01), "fail")
        self.assertEqual(classify_pretrend(2, 0.50), "fail")

    def test_model_observation_count_uses_post_singleton_estimation_sample(self) -> None:
        model = type("FakeModel", (), {"_N": 99})()

        self.assertEqual(model_observation_count(model, fallback=100), 99)

    def test_model_cluster_count_uses_post_singleton_estimation_sample(self) -> None:
        model = type("FakeModel", (), {"_data": pd.DataFrame({"cbo_4d": ["1111", "2123"]})})()

        self.assertEqual(model_cluster_count(model, "cbo_4d", fallback=3), 2)

    def test_both_plot_types_write_nonempty_pngs(self) -> None:
        path_rows = []
        coefficient_rows = []
        pretrend_rows = []
        for age_index, age_group in enumerate(AGE_ORDER):
            for role in ["treated", "control"]:
                for t in [-2, -1, 0, 1]:
                    path_rows.append(
                        {
                            "age_group": age_group,
                            "scenario_role": role,
                            "t": t,
                            "flow_index": 100.0 + age_index + (t if role == "treated" else 0.0),
                            "n_cbo": 4 if role == "treated" else 20,
                        }
                    )
            for t in [-2, -1, 0, 1]:
                coef = 0.0 if t == -1 else 0.01 * (age_index + t)
                coefficient_rows.append(
                    {
                        "age_group": age_group,
                        "t": t,
                        "coef": coef,
                        "ci_low": coef - 0.02,
                        "ci_high": coef + 0.02,
                        "coefficient_status": "reference" if t == -1 else "estimated",
                    }
                )
            pretrend_rows.append({"age_group": age_group, "pretrend_status": "pass", "joint_p_value": 0.50})

        with tempfile.TemporaryDirectory() as tmp:
            normalized_path = Path(tmp) / "normalized.png"
            ddd_path = Path(tmp) / "ddd.png"
            plot_normalized_flow_paths(pd.DataFrame(path_rows), normalized_path, "ln_admissoes")
            plot_ddd_event_studies(
                pd.DataFrame(coefficient_rows),
                pd.DataFrame(pretrend_rows),
                ddd_path,
                "ln_admissoes",
            )
            self.assertGreater(normalized_path.stat().st_size, 0)
            self.assertGreater(ddd_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
