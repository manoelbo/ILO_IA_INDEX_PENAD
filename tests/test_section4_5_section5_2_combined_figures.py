import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.section5_2_combined_figures import (  # noqa: E402
    AGE_COLORS,
    DIMENSION_ORDER,
    FOCAL_OUTCOMES,
    NATIONAL_COMBINED_FILENAME,
    NATIONAL_COMBINED_NOTE,
    NATIONAL_OUTCOMES,
    _figure_note,
    _figure_grid_slots,
    dimension_groups,
    expected_contract_counts,
    expected_figure_filenames,
    figure_specifications,
    figure_layout,
    figure_title,
    filter_and_validate_inputs,
    group_color,
    outcomes_for_dimension,
    run,
)


GROUPS = {
    "national": [("national", "Nacional")],
    "sex": [("men", "Homens"), ("women", "Mulheres")],
    "income": [
        ("low_income", "Até 2 salários mínimos"),
        ("middle_income", "Mais de 2 até 5 salários mínimos"),
        ("high_income", "Mais de 5 salários mínimos"),
    ],
    "age_canaries": [
        ("age_22_25", "22–25"),
        ("age_26_30", "26–30"),
        ("age_31_34", "31–34"),
        ("age_35_40", "35–40"),
        ("age_41_49", "41–49"),
        ("age_50_plus", "50+"),
    ],
    "race_color": [
        ("race_white", "Branca"),
        ("race_black", "Preta"),
        ("race_pardo", "Parda"),
        ("race_yellow", "Amarela"),
        ("race_indigenous", "Indígena"),
        ("race_unknown", "Não informada/identificada"),
    ],
    "education": [
        ("fundamental_or_less", "Fundamental ou menos"),
        ("high_school", "Médio"),
        ("higher_education", "Superior"),
    ],
}
SOURCE_OUTCOMES = ["ln_admissoes", "ln_desligamentos", "ln_salario_real_adm"]


def synthetic_source_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    coefficients = []
    pretrends = []
    paths = []
    for dimension_index, dimension in enumerate(DIMENSION_ORDER):
        for group_index, (group_id, group_label) in enumerate(GROUPS[dimension]):
            for outcome_index, outcome in enumerate(SOURCE_OUTCOMES):
                for t in range(-12, 25):
                    coefficient = 0.0 if t == -1 else 0.004 * (group_index - 1) + 0.001 * t
                    coefficients.append(
                        {
                            "dimension": dimension,
                            "group_id": group_id,
                            "group_label": group_label,
                            "outcome": outcome,
                            "estimand": "did" if dimension == "national" else "ddd",
                            "window_rule": "strict_no_tail_binning",
                            "t": t,
                            "coef": coefficient,
                            "se": 0.02,
                            "p_value": 0.50,
                            "ci_low": coefficient - 0.04,
                            "ci_high": coefficient + 0.04,
                            "coefficient_status": "reference" if t == -1 else "estimated",
                            "power_status": "thin" if group_id == "high_income" else "adequate",
                            "treated_cbo": 3 if group_id == "high_income" else 25,
                            "control_cbo": 7 if group_id == "high_income" else 80,
                        }
                    )
                pretrends.append(
                    {
                        "dimension": dimension,
                        "group_id": group_id,
                        "group_label": group_label,
                        "outcome": outcome,
                        "estimand": "did" if dimension == "national" else "ddd",
                        "window_rule": "strict_no_tail_binning",
                        "pretrend_status": "fail" if group_id == "race_unknown" else "pass",
                        "joint_p_value": 0.01 if group_id == "race_unknown" else 0.50,
                        "power_status": "thin" if group_id == "high_income" else "adequate",
                        "treated_cbo": 3 if group_id == "high_income" else 25,
                        "control_cbo": 7 if group_id == "high_income" else 80,
                    }
                )
                for role_index, role in enumerate(["treated", "control"]):
                    for t in range(-12, 25):
                        paths.append(
                            {
                                "dimension": dimension,
                                "group_id": group_id,
                                "group_label": group_label,
                                "outcome": outcome,
                                "window_rule": "strict_no_tail_binning",
                                "scenario_role": role,
                                "t": t,
                                "path_index": 100 + 0.2 * t + dimension_index + group_index + role_index,
                                "path_status": "estimated",
                                "power_status": "thin" if group_id == "high_income" else "adequate",
                                "treated_cbo": 3 if group_id == "high_income" else 25,
                                "control_cbo": 7 if group_id == "high_income" else 80,
                            }
                        )
    return pd.DataFrame(coefficients), pd.DataFrame(pretrends), pd.DataFrame(paths)


class Section52CombinedFigureContractTests(unittest.TestCase):
    def test_contract_counts_cover_43_models_and_14_figures(self) -> None:
        self.assertEqual(
            expected_contract_counts(),
            {
                "models": 43,
                "coefficient_rows": 1591,
                "pretrend_rows": 43,
                "path_rows": 3182,
                "figures": 14,
            },
        )

    def test_figure_names_and_titles_include_separations_only_nationally(self) -> None:
        filenames = expected_figure_filenames()

        self.assertEqual(len(filenames), 14)
        self.assertEqual(len(set(filenames)), 14)
        forbidden = ("layout", "experimental", "teste")
        self.assertTrue(all(not any(word in name.lower() for word in forbidden) for name in filenames))
        self.assertIn(NATIONAL_COMBINED_FILENAME, filenames)
        self.assertIn("figure_s5_2_national_separations_event_study_paths.png", filenames)
        self.assertFalse(any("separations" in name and "national" not in name for name in filenames))
        titles = [figure_title(dimension, outcome) for dimension, outcome in figure_specifications()]
        self.assertTrue(all(not any(word in title.lower() for word in forbidden) for title in titles))
        self.assertEqual(figure_title("national", "ln_admissoes"), "Admissões — event study e trajetórias nacionais")
        self.assertEqual(
            figure_title("national", "ln_desligamentos"),
            "Desligamentos — event study e trajetórias nacionais",
        )
        self.assertEqual(
            figure_title("education", "ln_salario_real_adm"),
            "Salário real de admissão — event study e trajetórias por escolaridade",
        )

    def test_dimension_outcomes_keep_separations_out_of_heterogeneity(self) -> None:
        self.assertEqual(
            outcomes_for_dimension("national"),
            ["ln_admissoes", "ln_desligamentos", "ln_salario_real_adm"],
        )
        self.assertEqual(outcomes_for_dimension("national"), NATIONAL_OUTCOMES)
        for dimension in DIMENSION_ORDER[1:]:
            self.assertEqual(outcomes_for_dimension(dimension), FOCAL_OUTCOMES)
            self.assertNotIn("ln_desligamentos", outcomes_for_dimension(dimension))

    def test_national_combined_note_has_three_lines(self) -> None:
        self.assertEqual(len(NATIONAL_COMBINED_NOTE.splitlines()), 3)

    def test_grouped_figure_notes_have_three_lines_for_both_outcomes(self) -> None:
        self.assertEqual(len(_figure_note("ln_admissoes").splitlines()), 3)
        self.assertEqual(len(_figure_note("ln_salario_real_adm").splitlines()), 3)
        self.assertIn("winsorizados", _figure_note("ln_salario_real_adm"))

    def test_layout_contract_covers_one_through_six_supported_group_counts(self) -> None:
        self.assertEqual(figure_layout(1)[:2], (1, 1))
        self.assertEqual(figure_layout(2)[:2], (1, 2))
        self.assertEqual(figure_layout(3)[:2], (1, 3))
        self.assertEqual(figure_layout(4)[:2], (2, 2))
        self.assertEqual(figure_layout(5)[:2], (2, 3))
        self.assertEqual(figure_layout(6)[:2], (2, 3))

    def test_five_group_layout_centers_two_cards_on_the_second_row(self) -> None:
        rows, columns, slots = _figure_grid_slots(5)

        self.assertEqual((rows, columns), (2, 6))
        self.assertEqual(
            slots,
            [
                (0, 0, 2),
                (0, 2, 4),
                (0, 4, 6),
                (1, 1, 3),
                (1, 3, 5),
            ],
        )

    def test_group_order_and_age_colors_match_the_table_contract(self) -> None:
        for dimension in DIMENSION_ORDER:
            self.assertEqual(dimension_groups(dimension), GROUPS[dimension])
        self.assertEqual(
            [group_color("age_canaries", group_id, "ln_admissoes") for group_id, _ in GROUPS["age_canaries"]],
            [AGE_COLORS[group_id] for group_id, _ in GROUPS["age_canaries"]],
        )
        self.assertEqual(len({group_color("race_color", group_id, "ln_admissoes") for group_id, _ in GROUPS["race_color"]}), 6)
        self.assertEqual(
            dimension_groups("race_color_b"),
            [
                ("race_white", "Branca"),
                ("race_black_combined", "Negra (preta e parda)"),
            ],
        )
        self.assertEqual(
            figure_title("race_color_b", "ln_admissoes"),
            "Admissões — event study e trajetórias por raça/cor — Branca e Negra",
        )
        self.assertEqual(
            dimension_groups("income_pnad"),
            [
                ("income_up_to_1sm", "Até 1 salário mínimo"),
                ("income_1_2sm", "Mais de 1 até 2 salários mínimos"),
                ("income_2_3sm", "Mais de 2 até 3 salários mínimos"),
                ("income_3_5sm", "Mais de 3 até 5 salários mínimos"),
                ("income_5_plus_sm", "Mais de 5 salários mínimos"),
            ],
        )
        self.assertEqual(
            figure_title("income_pnad", "ln_salario_real_adm"),
            "Salário real de admissão — event study e trajetórias por renda pré-tratamento — faixas PNAD/IBGE",
        )

    def test_filter_keeps_national_separations_and_removes_heterogeneity_separations(self) -> None:
        coefficients, pretrends, paths = synthetic_source_frames()

        filtered = filter_and_validate_inputs(coefficients, pretrends, paths)

        self.assertEqual([len(frame) for frame in filtered], [1591, 43, 3182])
        self.assertEqual(
            set(filtered[0].loc[filtered[0]["dimension"].eq("national"), "outcome"]),
            set(NATIONAL_OUTCOMES),
        )
        self.assertEqual(
            set(filtered[0].loc[filtered[0]["dimension"].ne("national"), "outcome"]),
            set(FOCAL_OUTCOMES),
        )
        reference = filtered[0][filtered[0]["t"].eq(-1)]
        self.assertEqual(len(reference), 43)
        self.assertTrue(reference["coef"].eq(0).all())

        bad = coefficients.copy()
        bad.loc[bad["t"].eq(-1).idxmax(), "coef"] = 0.25
        with self.assertRaisesRegex(ValueError, "reference"):
            filter_and_validate_inputs(bad, pretrends, paths)

    def test_run_writes_self_contained_bundle_for_every_dimension(self) -> None:
        coefficients, pretrends, paths = synthetic_source_frames()

        with tempfile.TemporaryDirectory() as tmp:
            input_root = Path(tmp) / "input"
            output_root = Path(tmp) / "output"
            input_root.mkdir()
            coefficients.to_csv(input_root / "event_study_coefficients_long.csv", index=False)
            pretrends.to_csv(input_root / "event_study_pretrends.csv", index=False)
            paths.to_csv(input_root / "normalized_paths_long.csv", index=False)

            run(input_root=input_root, output_root=output_root, dpi=48)

            figures = list((output_root / "figures").glob("*.png"))
            self.assertEqual({path.name for path in figures}, set(expected_figure_filenames()))
            self.assertTrue(all(path.stat().st_size > 1_000 for path in figures))
            combined = output_root / "figures" / NATIONAL_COMBINED_FILENAME
            with Image.open(combined) as image:
                self.assertGreater(image.width / image.height, 1.8)
                self.assertLess(image.width / image.height, 2.3)
            self.assertEqual(len(pd.read_csv(output_root / "tables" / "event_study_coefficients_long.csv")), 1591)
            self.assertEqual(len(pd.read_csv(output_root / "tables" / "event_study_pretrends.csv")), 43)
            self.assertEqual(len(pd.read_csv(output_root / "tables" / "normalized_paths_long.csv")), 3182)
            self.assertTrue((output_root / "README.md").exists())
            self.assertTrue((output_root / "MANIFEST.md").exists())
            self.assertTrue((output_root / "audit" / "section5_2_combined_figures_blindspot.md").exists())
            bundle_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in [output_root / "README.md", output_root / "MANIFEST.md"]
            ).lower()
            self.assertNotIn("experimental", bundle_text)
            self.assertIn("14 png figures", bundle_text)
            self.assertIn("recommended national figure", bundle_text)


if __name__ == "__main__":
    unittest.main()
