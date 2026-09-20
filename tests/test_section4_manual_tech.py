import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_event_study.manual_tech import build_manual_tech_roles, classify_manual_tech_cbo


class ManualTechClassificationTests(unittest.TestCase):
    def test_narrow_tech_includes_software_and_it_titles(self) -> None:
        data = pd.DataFrame(
            {
                "cbo_4d": ["2124", "3171"],
                "source_cbo_title": [
                    "Analistas de tecnologia da informação",
                    "Técnicos de desenvolvimento de sistemas e aplicações",
                ],
                "source_cbo_2d_title": ["Profissionais das ciências exatas", "Técnicos de nível médio"],
            }
        )

        out = classify_manual_tech_cbo(data)

        self.assertTrue(out["manual_tech_narrow"].all())
        self.assertTrue(out["manual_tech_broad"].all())
        self.assertEqual(set(out["manual_tech_tier"]), {"narrow"})

    def test_broad_tech_includes_telecom_but_not_narrow(self) -> None:
        data = pd.DataFrame(
            {
                "cbo_4d": ["3133"],
                "source_cbo_title": ["Técnicos em telecomunicações"],
                "source_cbo_2d_title": ["Técnicos de nível médio"],
            }
        )

        out = classify_manual_tech_cbo(data)

        self.assertFalse(bool(out.loc[0, "manual_tech_narrow"]))
        self.assertTrue(bool(out.loc[0, "manual_tech_broad"]))
        self.assertEqual(out.loc[0, "manual_tech_tier"], "broad_only")

    def test_false_positive_programming_titles_are_excluded_from_narrow(self) -> None:
        data = pd.DataFrame(
            {
                "cbo_4d": ["3911", "2394"],
                "source_cbo_title": [
                    "Planejadores, programadores e controladores de produção e manutenção",
                    "Programadores, avaliadores e orientadores de ensino",
                ],
                "source_cbo_2d_title": ["Outros técnicos de nível médio", "Profissionais do ensino"],
            }
        )

        out = classify_manual_tech_cbo(data)

        self.assertFalse(out["manual_tech_narrow"].any())
        self.assertFalse(out["manual_tech_broad"].any())
        self.assertTrue(out["manual_tech_exclusion_reason"].str.contains("semantic_exclusion").all())

    def test_manual_tech_roles_use_not_exposed_control_only(self) -> None:
        data = pd.DataFrame(
            {
                "cbo_4d": ["2124", "9999", "1425", "4110"],
                "source_cbo_title": [
                    "Analistas de tecnologia da informação",
                    "Ocupação administrativa sem exposição",
                    "Gerentes de tecnologia da informação",
                    "Agentes, assistentes e auxiliares administrativos",
                ],
                "source_cbo_2d_title": ["", "", "", ""],
                "mte_match_status": [
                    "matched_official_mte",
                    "matched_official_mte",
                    "no_mte_match",
                    "matched_official_mte",
                ],
                "cbo_ilo_gradient": ["Exposed: Gradient 4", "Not Exposed", "Not Exposed", "Minimal Exposure"],
            }
        )

        roles = build_manual_tech_roles(data, "narrow")
        by_cbo = roles.set_index("cbo_4d")["scenario_role"].to_dict()

        self.assertEqual(by_cbo["2124"], "treated")
        self.assertEqual(by_cbo["9999"], "control")
        self.assertEqual(by_cbo["1425"], "excluded")
        self.assertEqual(by_cbo["4110"], "excluded")


if __name__ == "__main__":
    unittest.main()
