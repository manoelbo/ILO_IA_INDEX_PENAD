import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from build_section5_2_income_pnad import (  # noqa: E402
    DIMENSION,
    DYNAMIC_OUTCOMES,
    FIGURE_FILENAMES,
    GROUPS,
    _validate_dynamic_frames,
    write_outputs,
)
from section4_5_final.section5_2_dynamic_figures import EVENT_TIMES  # noqa: E402
from section4_5_final.section5_2_tables import SECTION5_2_ADDITIONAL_SPECS  # noqa: E402


def synthetic_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coefficients: list[dict[str, object]] = []
    pretrends: list[dict[str, object]] = []
    paths: list[dict[str, object]] = []
    for group_index, (group_id, group_label) in enumerate(GROUPS):
        for outcome_index, outcome in enumerate(DYNAMIC_OUTCOMES):
            for t in EVENT_TIMES:
                coef = 0.0 if t == -1 else 0.003 * t + 0.006 * group_index
                coefficients.append(
                    {
                        "dimension": DIMENSION,
                        "group_id": group_id,
                        "group_label": group_label,
                        "outcome": outcome,
                        "estimand": "ddd",
                        "window_rule": "strict_no_tail_binning",
                        "t": t,
                        "coef": coef,
                        "se": 0.02,
                        "p_value": 0.50,
                        "ci_low": coef - 0.04,
                        "ci_high": coef + 0.04,
                        "coefficient_status": "reference" if t == -1 else "estimated",
                        "result_status": "estimated",
                        "power_status": "thin" if group_id == "income_5_plus_sm" else "adequate",
                        "treated_cbo": 3 if group_id == "income_5_plus_sm" else 25,
                        "control_cbo": 7 if group_id == "income_5_plus_sm" else 80,
                    }
                )
            pretrends.append(
                {
                    "dimension": DIMENSION,
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": outcome,
                    "estimand": "ddd",
                    "window_rule": "strict_no_tail_binning",
                    "pretrend_status": "fail" if group_id == "income_up_to_1sm" else "pass",
                    "joint_p_value": 0.01 if group_id == "income_up_to_1sm" else 0.50,
                    "power_status": "thin" if group_id == "income_5_plus_sm" else "adequate",
                    "treated_cbo": 3 if group_id == "income_5_plus_sm" else 25,
                    "control_cbo": 7 if group_id == "income_5_plus_sm" else 80,
                    "result_status": "estimated",
                }
            )
            for role_index, role in enumerate(["treated", "control"]):
                for t in EVENT_TIMES:
                    paths.append(
                        {
                            "dimension": DIMENSION,
                            "group_id": group_id,
                            "group_label": group_label,
                            "outcome": outcome,
                            "window_rule": "strict_no_tail_binning",
                            "scenario_role": role,
                            "role_label": "Exposed" if role == "treated" else "Not Exposed",
                            "t": t,
                            "path_index": 100 + 0.2 * t + group_index + outcome_index + role_index,
                            "path_status": "estimated",
                            "power_status": "thin" if group_id == "income_5_plus_sm" else "adequate",
                            "treated_cbo": 3 if group_id == "income_5_plus_sm" else 25,
                            "control_cbo": 7 if group_id == "income_5_plus_sm" else 80,
                        }
                    )
    return pd.DataFrame(coefficients), pd.DataFrame(pretrends), pd.DataFrame(paths)


class Section52IncomePnadFigureTests(unittest.TestCase):
    def test_contract_uses_table_5_2_3_b_groups_and_b_filenames(self) -> None:
        self.assertEqual(GROUPS, SECTION5_2_ADDITIONAL_SPECS["income_pnad"]["groups"])
        self.assertEqual(len(GROUPS), 5)
        self.assertEqual(set(FIGURE_FILENAMES), set(DYNAMIC_OUTCOMES))
        self.assertTrue(all("income_pnad_b" in filename for filename in FIGURE_FILENAMES.values()))
        self.assertTrue(all("separations" not in filename for filename in FIGURE_FILENAMES.values()))

    def test_validation_enforces_complete_grids_and_zero_reference(self) -> None:
        coefficients, pretrends, paths = synthetic_frames()

        _validate_dynamic_frames(coefficients, pretrends, paths)
        self.assertEqual((len(coefficients), len(pretrends), len(paths)), (370, 10, 740))

        bad = coefficients.copy()
        bad.loc[bad["t"].eq(-1).idxmax(), "coef"] = 0.1
        with self.assertRaisesRegex(RuntimeError, "reference"):
            _validate_dynamic_frames(bad, pretrends, paths)

    def test_write_outputs_adds_two_figures_without_removing_existing_files(self) -> None:
        coefficients, pretrends, paths = synthetic_frames()

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "combined"
            figure_dir = output_root / "figures"
            figure_dir.mkdir(parents=True)
            sentinel = figure_dir / "figure_s5_2_income_admissions_event_study_paths.png"
            sentinel.write_bytes(b"existing figure")

            outputs = write_outputs(
                coefficients,
                pretrends,
                paths,
                output_root=output_root,
                dpi=48,
            )

            self.assertEqual(sentinel.read_bytes(), b"existing figure")
            for outcome, filename in FIGURE_FILENAMES.items():
                figure = output_root / "figures" / filename
                self.assertEqual(outputs[f"figure_{outcome}"], figure)
                self.assertGreater(figure.stat().st_size, 1_000)
                with Image.open(figure) as image:
                    self.assertGreater(image.width / image.height, 1.15)
                    self.assertLess(image.width / image.height, 1.65)
            self.assertEqual(
                len(pd.read_csv(output_root / "tables" / "income_pnad_b_event_study_coefficients_long.csv")),
                370,
            )
            self.assertEqual(
                len(pd.read_csv(output_root / "tables" / "income_pnad_b_event_study_pretrends.csv")),
                10,
            )
            self.assertEqual(
                len(pd.read_csv(output_root / "tables" / "income_pnad_b_normalized_paths_long.csv")),
                740,
            )
            self.assertTrue(
                (output_root / "audit" / "figure_s5_2_income_pnad_b_blindspot.md").exists()
            )


if __name__ == "__main__":
    unittest.main()
