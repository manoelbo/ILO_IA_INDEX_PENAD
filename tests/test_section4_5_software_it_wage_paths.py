import math
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.plot_software_it_wage_paths_by_age import (  # noqa: E402
    AGE_ORDER,
    assign_canaries_age_band,
    build_normalized_paths,
    build_strict_software_it_roles,
    plot_normalized_paths,
    winsorize_age_wage_panel,
)


class SoftwareITWagePathsTests(unittest.TestCase):
    def test_canaries_age_bands_use_the_expected_boundaries(self) -> None:
        ages = pd.Series([21, 22, 25, 26, 30, 31, 34, 35, 40, 41, 49, 50, 80, None])

        out = assign_canaries_age_band(ages)

        self.assertTrue(pd.isna(out.iloc[0]))
        self.assertEqual(
            out.iloc[1:13].tolist(),
            [
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
        self.assertTrue(pd.isna(out.iloc[-1]))

    def test_strict_roles_keep_only_software_it_and_matched_not_exposed(self) -> None:
        classification = pd.DataFrame(
            {
                "cbo_4d": ["2123", "2124", "3171", "3172", "1111", "2222", "3333"],
                "mte_match_status": [
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "sem_match_mte_no_result",
                ],
                "cbo_ilo_gradient": [
                    "Exposed: Gradient 3",
                    "Exposed: Gradient 3",
                    "Exposed: Gradient 2",
                    "Exposed: Gradient 2",
                    "Not Exposed",
                    "Minimal Exposure",
                    "Not Exposed",
                ],
            }
        )

        out = build_strict_software_it_roles(classification)

        self.assertEqual(set(out.loc[out["scenario_role"].eq("treated"), "cbo_4d"]), {"2123", "2124", "3171", "3172"})
        self.assertEqual(set(out.loc[out["scenario_role"].eq("control"), "cbo_4d"]), {"1111"})
        self.assertNotIn("2222", set(out["cbo_4d"]))
        self.assertNotIn("3333", set(out["cbo_4d"]))

    def test_normalized_paths_equal_100_over_the_pre_period(self) -> None:
        rows = []
        for cbo, role, post_wage in [("2123", "treated", 90.0), ("1111", "control", 100.0)]:
            for t, wage in [(-2, 100.0), (-1, 100.0), (0, post_wage)]:
                rows.append(
                    {
                        "cbo_4d": cbo,
                        "age_group": "age_22_25",
                        "scenario_role": role,
                        "t": t,
                        "ln_salario_real_adm": math.log(wage),
                    }
                )
        panel = pd.DataFrame(rows)

        out = build_normalized_paths(panel, pre_min=-2, pre_max=-1)

        treated = out[out["scenario_role"].eq("treated")].set_index("t")
        control = out[out["scenario_role"].eq("control")].set_index("t")
        self.assertAlmostEqual(treated.loc[-2, "wage_index"], 100.0)
        self.assertAlmostEqual(treated.loc[-1, "wage_index"], 100.0)
        self.assertAlmostEqual(treated.loc[0, "wage_index"], 90.0)
        self.assertAlmostEqual(control.loc[0, "wage_index"], 100.0)
        self.assertEqual(int(treated.loc[0, "n_cbo"]), 1)

    def test_normalized_paths_aggregate_log_changes_instead_of_level_ratios(self) -> None:
        rows = []
        for index in range(100):
            cbo = f"{index:04d}"
            for t, wage in [(-1, 100.0), (0, 10_000.0 if index == 0 else 100.0)]:
                rows.append(
                    {
                        "cbo_4d": cbo,
                        "age_group": "age_26_30",
                        "scenario_role": "control",
                        "t": t,
                        "ln_salario_real_adm": math.log(wage),
                    }
                )

        out = build_normalized_paths(pd.DataFrame(rows), pre_min=-1, pre_max=-1)

        post = out.loc[out["t"].eq(0), "wage_index"].iloc[0]
        self.assertLess(post, 110.0)

    def test_winsorization_caps_extreme_cbo_month_mean_wages(self) -> None:
        panel = pd.DataFrame(
            {
                "salario_adm": [100.0, 110.0, 120.0, 130.0, 1_000_000.0],
                "indice": [100.0] * 5,
            }
        )

        out = winsorize_age_wage_panel(panel, lower_q=0.0, upper_q=0.8)

        self.assertAlmostEqual(out["salario_adm"].max(), 200_104.0)
        self.assertTrue((out["ln_salario_real_adm"] == out["salario_real_adm"].map(math.log)).all())

    def test_plot_writes_a_nonempty_png(self) -> None:
        rows = []
        for age_index, age_group in enumerate(AGE_ORDER):
            for role in ["treated", "control"]:
                for t in [-2, -1, 0, 1]:
                    rows.append(
                        {
                            "age_group": age_group,
                            "scenario_role": role,
                            "t": t,
                            "wage_index": 100.0 + age_index + (t if role == "treated" else 0.0),
                            "se": 0.5,
                            "n_cbo": 4 if role == "treated" else 20,
                        }
                    )
        paths = pd.DataFrame(rows)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "figure.png"
            plot_normalized_paths(paths, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
