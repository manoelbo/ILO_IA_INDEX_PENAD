import math
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.plot_software_it_wage_event_study_by_age import (  # noqa: E402
    AGE_ORDER,
    CONTROL_COLUMNS,
    build_wage_pair_panel,
    plot_wage_ddd_event_studies,
)


class SoftwareITWageEventStudyTests(unittest.TestCase):
    @staticmethod
    def _controls() -> pd.DataFrame:
        controls = pd.DataFrame(
            {
                "cbo_4d": ["2123", "2123"],
                "ano": [2022, 2022],
                "mes": [11, 12],
                "periodo": ["2022-11", "2022-12"],
                "t": [-1, 0],
            }
        )
        for column in CONTROL_COLUMNS:
            controls[column] = 0.0
        return controls

    @staticmethod
    def _wage_panel() -> pd.DataFrame:
        rows = []
        for t, month in [(-1, 11), (0, 12)]:
            rows.extend(
                [
                    {
                        "cbo_4d": "2123",
                        "age_group": "age_22_25",
                        "ano": 2022,
                        "mes": month,
                        "t": t,
                        "salary_sum": 2_500.0,
                        "wage_count": 1,
                        "indice": 100.0,
                        "scenario_role": "treated",
                        "scenario_treat": 1,
                    },
                    {
                        "cbo_4d": "2123",
                        "age_group": "age_26_30",
                        "ano": 2022,
                        "mes": month,
                        "t": t,
                        "salary_sum": 2_000.0,
                        "wage_count": 1,
                        "indice": 100.0,
                        "scenario_role": "treated",
                        "scenario_treat": 1,
                    },
                    {
                        "cbo_4d": "2123",
                        "age_group": "age_31_34",
                        "ano": 2022,
                        "mes": month,
                        "t": t,
                        "salary_sum": 12_000.0,
                        "wage_count": 3,
                        "indice": 100.0,
                        "scenario_role": "treated",
                        "scenario_treat": 1,
                    },
                ]
            )
        return pd.DataFrame(rows)

    def test_pair_panel_uses_admission_weighted_raw_wages_for_the_complement(self) -> None:
        out = build_wage_pair_panel(
            self._wage_panel(),
            self._controls(),
            "age_22_25",
        )

        post = out[out["t"].eq(0)].set_index("subgroup")
        self.assertAlmostEqual(post.loc["target", "salario_adm"], 2_500.0)
        self.assertAlmostEqual(post.loc["complement", "salario_adm"], 3_500.0)
        self.assertAlmostEqual(post.loc["target", "ln_salario_real_adm"], math.log(2_500.0))
        self.assertAlmostEqual(post.loc["complement", "ln_salario_real_adm"], math.log(3_500.0))
        self.assertEqual(post.loc["complement", "wage_count"], 4)

    def test_pair_panel_preserves_a_missing_target_wage_as_missing(self) -> None:
        wage_panel = self._wage_panel()
        wage_panel = wage_panel[
            ~(wage_panel["age_group"].eq("age_22_25") & wage_panel["t"].eq(0))
        ].copy()

        out = build_wage_pair_panel(wage_panel, self._controls(), "age_22_25")

        self.assertEqual(len(out), 4)
        missing_target = out[out["subgroup"].eq("target") & out["t"].eq(0)].iloc[0]
        self.assertTrue(pd.isna(missing_target["ln_salario_real_adm"]))
        complement = out[out["subgroup"].eq("complement") & out["t"].eq(0)].iloc[0]
        self.assertAlmostEqual(complement["salario_adm"], 3_500.0)

    def test_wage_event_study_plot_writes_a_nonempty_png(self) -> None:
        coefficient_rows = []
        pretrend_rows = []
        for age_index, age_group in enumerate(AGE_ORDER):
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
            pretrend_rows.append(
                {
                    "age_group": age_group,
                    "pretrend_status": "pass",
                    "joint_p_value": 0.50,
                }
            )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "wage_ddd.png"
            plot_wage_ddd_event_studies(
                pd.DataFrame(coefficient_rows),
                pd.DataFrame(pretrend_rows),
                output,
            )
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
