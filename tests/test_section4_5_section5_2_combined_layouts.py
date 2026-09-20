import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.section5_2_combined_layout_tests import (  # noqa: E402
    expected_layout_filenames,
    render_all_layout_tests,
    validate_age_inputs,
)


AGE_GROUPS = [
    ("age_22_25", "22–25"),
    ("age_26_30", "26–30"),
    ("age_31_34", "31–34"),
    ("age_35_40", "35–40"),
    ("age_41_49", "41–49"),
    ("age_50_plus", "50+"),
]
OUTCOMES = ["ln_admissoes", "ln_salario_real_adm"]


def synthetic_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coefficient_rows = []
    pretrend_rows = []
    path_rows = []
    for group_index, (group_id, group_label) in enumerate(AGE_GROUPS):
        for outcome_index, outcome in enumerate(OUTCOMES):
            for t in range(-12, 25):
                coefficient = 0.0 if t == -1 else 0.006 * (group_index - 2) + 0.002 * t
                coefficient_rows.append(
                    {
                        "dimension": "age_canaries",
                        "group_id": group_id,
                        "group_label": group_label,
                        "outcome": outcome,
                        "estimand": "ddd",
                        "t": t,
                        "coef": coefficient,
                        "ci_low": coefficient - 0.04 - 0.005 * outcome_index,
                        "ci_high": coefficient + 0.04 + 0.005 * outcome_index,
                        "coefficient_status": "reference" if t == -1 else "estimated",
                    }
                )
            pretrend_rows.append(
                {
                    "dimension": "age_canaries",
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": outcome,
                    "pretrend_status": "fail" if group_id == "age_50_plus" else "pass",
                    "joint_p_value": 0.01 if group_id == "age_50_plus" else 0.50,
                    "power_status": "adequate",
                }
            )
            for role_index, role in enumerate(["treated", "control"]):
                for t in range(-12, 25):
                    path_rows.append(
                        {
                            "dimension": "age_canaries",
                            "group_id": group_id,
                            "group_label": group_label,
                            "outcome": outcome,
                            "scenario_role": role,
                            "t": t,
                            "path_index": (
                                100.0
                                + 0.25 * t
                                + 0.8 * group_index
                                + 1.5 * outcome_index
                                + 1.2 * role_index
                            ),
                            "path_status": "estimated",
                        }
                    )
    return (
        pd.DataFrame(coefficient_rows),
        pd.DataFrame(pretrend_rows),
        pd.DataFrame(path_rows),
    )


class Section52CombinedLayoutContractTests(unittest.TestCase):
    def test_contract_has_six_layout_pages_and_one_comparison_sheet(self) -> None:
        filenames = expected_layout_filenames()

        self.assertEqual(len(filenames), 7)
        self.assertEqual(len(set(filenames)), 7)
        self.assertTrue(all(name.endswith(".png") for name in filenames))
        self.assertFalse(any("separation" in name or "dismissal" in name for name in filenames))

    def test_age_input_contract_requires_complete_grids_and_zero_reference(self) -> None:
        coefficients, pretrends, paths = synthetic_frames()

        validate_age_inputs(coefficients, pretrends, paths)

        bad_reference = coefficients.copy()
        bad_reference.loc[
            bad_reference["t"].eq(-1) & bad_reference.index.to_series().eq(11),
            "coef",
        ] = 0.5
        with self.assertRaisesRegex(ValueError, "reference"):
            validate_age_inputs(bad_reference, pretrends, paths)

    def test_renderer_writes_every_layout_prototype(self) -> None:
        coefficients, pretrends, paths = synthetic_frames()

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            rendered = render_all_layout_tests(
                coefficients,
                pretrends,
                paths,
                output_dir,
                dpi=72,
            )

            self.assertEqual({path.name for path in rendered}, set(expected_layout_filenames()))
            self.assertEqual({path.name for path in output_dir.glob("*.png")}, set(expected_layout_filenames()))
            self.assertTrue(all(path.stat().st_size > 1_000 for path in rendered))


if __name__ == "__main__":
    unittest.main()
