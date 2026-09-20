import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_event_study.manual_occupation_groups import (  # noqa: E402
    OFFICIAL_GROUP_IDS,
    build_manual_group_roles,
    manual_group_audit,
)


class ManualOccupationGroupTests(unittest.TestCase):
    def test_software_it_core_contains_only_clean_it_cbo(self) -> None:
        spec = OFFICIAL_GROUP_IDS["software_it_core"]

        self.assertEqual(spec, {"2123", "2124", "3171", "3172"})
        self.assertNotIn("4121", spec)

    def test_digital_it_with_data_entry_adds_data_entry(self) -> None:
        spec = OFFICIAL_GROUP_IDS["digital_it_with_data_entry"]

        self.assertEqual(spec, {"2123", "2124", "3171", "3172", "4121"})

    def test_false_positive_programming_titles_are_not_in_manual_groups(self) -> None:
        false_positives = {"2394", "3911", "2527"}

        for group_id, cbo_codes in OFFICIAL_GROUP_IDS.items():
            with self.subTest(group_id=group_id):
                self.assertTrue(false_positives.isdisjoint(cbo_codes))

    def test_life_science_and_generic_rd_are_not_software_it(self) -> None:
        not_software_it = {"3251", "3252", "3250", "2011", "2012", "2032", "3951"}

        self.assertTrue(not_software_it.isdisjoint(OFFICIAL_GROUP_IDS["software_it_core"]))
        self.assertTrue(not_software_it.isdisjoint(OFFICIAL_GROUP_IDS["digital_it_with_data_entry"]))

    def test_official_roles_use_not_exposed_controls_and_exclude_no_mte(self) -> None:
        classification = pd.DataFrame(
            {
                "cbo_4d": ["2124", "3171", "4121", "1425", "9999", "4110"],
                "source_cbo_title": [
                    "Analistas de tecnologia da informação",
                    "Técnicos de desenvolvimento de sistemas e aplicações",
                    "Operadores de equipamentos de entrada e transmissão de dados",
                    "Gerentes de tecnologia da informação",
                    "Ocupação manual não exposta",
                    "Agentes, assistentes e auxiliares administrativos",
                ],
                "mte_match_status": [
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "sem_match_mte_no_result",
                    "matched_official_mte",
                    "matched_official_mte",
                ],
                "cbo_ilo_gradient": [
                    "Exposed: Gradient 3",
                    "Exposed: Gradient 2",
                    "Exposed: Gradient 3",
                    "No score",
                    "Not Exposed",
                    "Minimal Exposure",
                ],
            }
        )

        roles = build_manual_group_roles(classification, "software_it_core")
        by_cbo = roles.set_index("cbo_4d")["scenario_role"].to_dict()

        self.assertEqual(by_cbo["2124"], "treated")
        self.assertEqual(by_cbo["3171"], "treated")
        self.assertEqual(by_cbo["4121"], "excluded")
        self.assertEqual(by_cbo["1425"], "excluded")
        self.assertEqual(by_cbo["9999"], "control")
        self.assertEqual(by_cbo["4110"], "excluded")

    def test_audit_marks_clear_tech_no_mte_as_exploratory(self) -> None:
        classification = pd.DataFrame(
            {
                "cbo_4d": ["1425", "2122", "2124"],
                "source_cbo_title": [
                    "Gerentes de tecnologia da informação",
                    "Engenheiros em computação",
                    "Analistas de tecnologia da informação",
                ],
                "mte_match_status": ["sem_match_mte_no_result", "sem_match_mte_no_result", "matched_official_mte"],
                "cbo_ilo_gradient": ["No score", "No score", "Exposed: Gradient 3"],
            }
        )

        audit = manual_group_audit(classification)
        clear_no_mte = audit[audit["group_id"].eq("clear_tech_no_mte")]

        self.assertTrue(clear_no_mte["exploratory_only"].all())
        self.assertEqual(set(clear_no_mte["cbo_4d"]), {"1425", "2122"})


if __name__ == "__main__":
    unittest.main()
