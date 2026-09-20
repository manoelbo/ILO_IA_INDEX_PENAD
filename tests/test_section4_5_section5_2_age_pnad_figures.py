import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.section5_2_age_pnad_figures import (  # noqa: E402
    AGE_PNAD_GROUPS,
    COMBINED_NOTE,
    OUTCOME_OVERVIEW_NOTES,
    OUTCOME_OVERVIEW_FILENAMES,
    OVERVIEW_FILENAME,
    OVERVIEW_OUTCOMES,
    OUTCOMES,
    _event_ylim_for_outcome,
    _path_ylim_for_outcome,
    expected_contract_counts,
    expected_figure_filenames,
    validate_long_frames,
    write_bundle,
)
from section4_5_final.section5_2_tables import SECTION5_2_ADDITIONAL_SPECS  # noqa: E402


def synthetic_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coefficients: list[dict[str, object]] = []
    pretrends: list[dict[str, object]] = []
    paths: list[dict[str, object]] = []
    for group_index, (group_id, group_label) in enumerate(AGE_PNAD_GROUPS):
        for outcome_index, outcome in enumerate(OUTCOMES):
            for t in range(-12, 25):
                coef = 0.0 if t == -1 else 0.002 * t + 0.005 * group_index
                coefficients.append(
                    {
                        "dimension": "age_pnad",
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
                        "power_status": "adequate",
                        "treated_cbo": 75,
                        "control_cbo": 266,
                    }
                )
            pretrends.append(
                {
                    "dimension": "age_pnad",
                    "group_id": group_id,
                    "group_label": group_label,
                    "outcome": outcome,
                    "estimand": "ddd",
                    "window_rule": "strict_no_tail_binning",
                    "pretrend_status": "fail" if group_id == "age_55_plus" and outcome == "ln_desligamentos" else "pass",
                    "joint_p_value": 0.01 if group_id == "age_55_plus" and outcome == "ln_desligamentos" else 0.50,
                    "power_status": "adequate",
                    "treated_cbo": 75,
                    "control_cbo": 266,
                    "result_status": "estimated",
                }
            )
            for role_index, role in enumerate(["treated", "control"]):
                for t in range(-12, 25):
                    paths.append(
                        {
                            "dimension": "age_pnad",
                            "group_id": group_id,
                            "group_label": group_label,
                            "outcome": outcome,
                            "window_rule": "strict_no_tail_binning",
                            "scenario_role": role,
                            "role_label": "Exposed" if role == "treated" else "Not Exposed",
                            "t": t,
                            "path_index": 100 + 0.15 * t + group_index + outcome_index + role_index,
                            "path_status": "estimated",
                            "power_status": "adequate",
                            "treated_cbo": 75,
                            "control_cbo": 266,
                        }
                    )
    return pd.DataFrame(coefficients), pd.DataFrame(pretrends), pd.DataFrame(paths)


class Section52AgePnadFigureTests(unittest.TestCase):
    def test_groups_follow_table_5_2_4_b_and_make_the_upper_age_limit_visible(self) -> None:
        table_groups = SECTION5_2_ADDITIONAL_SPECS["age_pnad"]["groups"]

        self.assertEqual([group_id for group_id, _ in AGE_PNAD_GROUPS], [group_id for group_id, _ in table_groups])
        self.assertEqual(
            [label for _, label in AGE_PNAD_GROUPS],
            ["18–24 anos", "25–34 anos", "35–44 anos", "45–54 anos", "55–65 anos"],
        )

    def test_contract_has_five_age_figures_and_three_comparative_overviews(self) -> None:
        self.assertEqual(
            expected_contract_counts(),
            {
                "models": 15,
                "coefficient_rows": 555,
                "pretrend_rows": 15,
                "path_rows": 1110,
                "figures": 8,
            },
        )
        filenames = expected_figure_filenames()
        self.assertEqual(len(filenames), 8)
        self.assertEqual(len(set(filenames)), 8)
        self.assertIn(OVERVIEW_FILENAME, filenames)
        self.assertEqual(
            OUTCOME_OVERVIEW_FILENAMES,
            {
                "ln_admissoes": (
                    "figure_s5_2_age_pnad_all_age_groups_admissions_event_study_paths.png"
                ),
                "ln_salario_real_adm": (
                    "figure_s5_2_age_pnad_all_age_groups_real_admission_wage_event_study_paths.png"
                ),
            },
        )
        self.assertTrue(
            set(OUTCOME_OVERVIEW_FILENAMES.values()).issubset(filenames)
        )
        self.assertTrue(all(name.endswith("_event_study_paths.png") for name in filenames))
        self.assertTrue(all(not any(word in name for word in ["layout", "experimental", "teste"]) for name in filenames))

    def test_comparative_overview_omits_separations_without_changing_backing_outcomes(self) -> None:
        self.assertEqual(
            OVERVIEW_OUTCOMES,
            ["ln_admissoes", "ln_salario_real_adm"],
        )
        self.assertNotIn("ln_desligamentos", OVERVIEW_OUTCOMES)
        self.assertEqual(
            OUTCOMES,
            ["ln_admissoes", "ln_desligamentos", "ln_salario_real_adm"],
        )

    def test_overview_scales_cover_all_age_groups_within_each_outcome(self) -> None:
        coefficients, _pretrends, paths = synthetic_frames()

        for outcome in OUTCOMES:
            event_low, event_high = _event_ylim_for_outcome(coefficients, outcome)
            event_bounds = coefficients.loc[
                coefficients["outcome"].eq(outcome), ["ci_low", "ci_high"]
            ].to_numpy(dtype=float)
            self.assertLessEqual(event_low, event_bounds.min())
            self.assertGreaterEqual(event_high, event_bounds.max())

            path_low, path_high = _path_ylim_for_outcome(paths, outcome)
            path_values = paths.loc[paths["outcome"].eq(outcome), "path_index"].to_numpy(dtype=float)
            self.assertLessEqual(path_low, min(path_values.min(), 100.0))
            self.assertGreaterEqual(path_high, max(path_values.max(), 100.0))

    def test_validation_enforces_reference_roles_and_excludes_other_outcomes(self) -> None:
        coefficients, pretrends, paths = synthetic_frames()

        validate_long_frames(coefficients, pretrends, paths)

        reference = coefficients[coefficients["t"].eq(-1)]
        self.assertEqual(len(reference), 15)
        self.assertTrue(reference["coef"].eq(0).all())
        self.assertEqual(set(coefficients["outcome"]), set(OUTCOMES))
        self.assertEqual(set(paths["scenario_role"]), {"treated", "control"})

        bad = coefficients.copy()
        bad.loc[bad["t"].eq(-1).idxmax(), "coef"] = 0.2
        with self.assertRaisesRegex(ValueError, "reference"):
            validate_long_frames(bad, pretrends, paths)

        forbidden = coefficients.copy()
        forbidden.loc[forbidden.index[0], "outcome"] = "ln_salario_real_desl"
        with self.assertRaisesRegex(ValueError, "outcome"):
            validate_long_frames(forbidden, pretrends, paths)

    def test_note_has_three_lines(self) -> None:
        self.assertEqual(len(COMBINED_NOTE.splitlines()), 3)
        self.assertTrue(
            all(len(note.splitlines()) == 3 for note in OUTCOME_OVERVIEW_NOTES.values())
        )
        self.assertNotIn("Salários", OUTCOME_OVERVIEW_NOTES["ln_admissoes"])
        self.assertIn("Salários", OUTCOME_OVERVIEW_NOTES["ln_salario_real_adm"])

    def test_bundle_writes_five_age_pngs_three_overviews_and_numeric_backing_tables(self) -> None:
        coefficients, pretrends, paths = synthetic_frames()

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "age_pnad"
            write_bundle(coefficients, pretrends, paths, output_root=output_root, dpi=48)

            figures = sorted((output_root / "figures").glob("*.png"))
            self.assertEqual({path.name for path in figures}, set(expected_figure_filenames()))
            self.assertTrue(all(path.stat().st_size > 1_000 for path in figures))
            for figure in figures:
                with Image.open(figure) as image:
                    aspect_ratio = image.width / image.height
                    if figure.name == OVERVIEW_FILENAME:
                        self.assertGreater(aspect_ratio, 2.0)
                        self.assertLess(aspect_ratio, 2.4)
                    elif figure.name in OUTCOME_OVERVIEW_FILENAMES.values():
                        self.assertGreater(aspect_ratio, 2.8)
                        self.assertLess(aspect_ratio, 4.5)
                    else:
                        self.assertGreater(aspect_ratio, 1.8)
                        self.assertLess(aspect_ratio, 2.3)
            self.assertEqual(len(pd.read_csv(output_root / "tables" / "event_study_coefficients_long.csv")), 555)
            self.assertEqual(len(pd.read_csv(output_root / "tables" / "event_study_pretrends.csv")), 15)
            self.assertEqual(len(pd.read_csv(output_root / "tables" / "normalized_paths_long.csv")), 1110)
            self.assertTrue((output_root / "README.md").exists())
            self.assertTrue((output_root / "MANIFEST.md").exists())
            self.assertTrue((output_root / "audit" / "section5_2_age_pnad_figures_blindspot.md").exists())


if __name__ == "__main__":
    unittest.main()
