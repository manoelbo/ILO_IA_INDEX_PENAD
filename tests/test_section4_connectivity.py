import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_connectivity.data import prepare_connectivity_panel
from section4_connectivity.estimation import prepare_event_study_design


class ConnectivityPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.classification = pd.DataFrame(
            {
                "cbo_4d": ["1111", "2222", "3333", "4444", "5555"],
                "mte_match_status": [
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "sem_match_mte_no_result",
                ],
                "cbo_ilo_gradient": [
                    "Not Exposed",
                    "Minimal Exposure",
                    "Exposed: Gradient 1",
                    "No score",
                    "Exposed: Gradient 2",
                ],
                "isco08_mean_score": [0.1, 0.35, 0.45, np.nan, 0.50],
                "isco08_pooled_sd": [0.05, 0.10, 0.20, np.nan, 0.10],
                "role__baseline_mte2d_top20_vs_rest": ["control", "control", "treated", "excluded", "treated"],
            }
        )
        self.ipca = pd.DataFrame(
            {
                "ano": [2022, 2023],
                "mes": [11, 1],
                "indice": [100.0, 125.0],
            }
        )

    def test_prepare_connectivity_panel_uses_strict_base_roles(self) -> None:
        panel = pd.DataFrame(
            {
                "cbo_4d": ["1111", "2222", "3333", "4444", "5555"],
                "id_municipio": ["3550308"] * 5,
                "ano": [2023] * 5,
                "mes": [1] * 5,
                "periodo": ["2023-01"] * 5,
                "periodo_num": [202301] * 5,
                "post": [1] * 5,
                "tempo_relativo_meses": [1] * 5,
                "sigla_uf": ["SP"] * 5,
                "admissoes": [2, 2, 2, 2, 2],
                "desligamentos": [1, 1, 1, 1, 1],
                "salario_medio_adm": [2500.0] * 5,
                "salario_medio_desl": [2400.0] * 5,
                "alta_conectividade": [1] * 5,
                "conectividade_q75": [1] * 5,
                "conectividade_q25": [1] * 5,
                "alta_fibra": [1] * 5,
                "penetracao_bl": [0.8] * 5,
                "pct_fibra_pre": [0.7] * 5,
                "pib_per_capita": [50000.0] * 5,
                "populacao": [1000000] * 5,
                "crosswalk_spec": ["mte_official_no_numeric_fallback"] * 5,
            }
        )

        out = prepare_connectivity_panel(panel, self.classification, self.ipca)

        self.assertEqual(set(out["cbo_4d"]), {"1111", "3333"})
        self.assertEqual(set(out.loc[out["scenario_role"].eq("control"), "cbo_ilo_gradient"]), {"Not Exposed"})
        self.assertEqual(set(out.loc[out["scenario_role"].eq("treated"), "cbo_ilo_gradient"]), {"Exposed: Gradient 1"})
        self.assertNotIn("Minimal Exposure", set(out["cbo_ilo_gradient"]))
        self.assertTrue(out["mte_match_status"].eq("matched_official_mte").all())

    def test_prepare_connectivity_panel_sets_wage_logs_missing_when_no_flow(self) -> None:
        panel = pd.DataFrame(
            {
                "cbo_4d": ["1111", "3333", "3333"],
                "id_municipio": ["3550308", "3550308", "3550308"],
                "ano": [2022, 2022, 2023],
                "mes": [11, 11, 1],
                "periodo": ["2022-11", "2022-11", "2023-01"],
                "periodo_num": [202211, 202211, 202301],
                "post": [0, 0, 1],
                "tempo_relativo_meses": [-1, -1, 1],
                "sigla_uf": ["SP", "SP", "SP"],
                "admissoes": [0, 3, 4],
                "desligamentos": [2, 0, 5],
                "salario_medio_adm": [0.0, 3000.0, 4000.0],
                "salario_medio_desl": [2000.0, 0.0, 5000.0],
                "alta_conectividade": [0, 1, 1],
                "conectividade_q75": [0, 1, 1],
                "conectividade_q25": [1, 1, 1],
                "alta_fibra": [0, 1, 1],
                "penetracao_bl": [0.2, 0.8, 0.8],
                "pct_fibra_pre": [0.2, 0.7, 0.7],
                "pib_per_capita": [50000.0, 50000.0, 50000.0],
                "populacao": [1000000, 1000000, 1000000],
                "crosswalk_spec": ["mte_official_no_numeric_fallback"] * 3,
            }
        )

        out = prepare_connectivity_panel(panel, self.classification, self.ipca)

        no_adm = out[out["admissoes"].eq(0)].iloc[0]
        no_desl = out[out["desligamentos"].eq(0)].iloc[0]
        self.assertTrue(np.isnan(no_adm["ln_salario_real_adm"]))
        self.assertTrue(np.isnan(no_desl["ln_salario_real_desl"]))
        treated_post = out[(out["cbo_4d"].eq("3333")) & (out["post"].eq(1))].iloc[0]
        self.assertEqual(treated_post["post_treat_connect"], 1)
        self.assertEqual(treated_post["pre_cell_adm_weight"], 3.0)
        self.assertEqual(treated_post["saldo"], -1)
        self.assertAlmostEqual(treated_post["asinh_saldo"], np.arcsinh(-1))
        self.assertAlmostEqual(treated_post["saldo_per_pre_cell_adm"], -1 / 3)
        self.assertAlmostEqual(treated_post["saldo_flow_rate"], -1 / 9)


class ConnectivityEventStudyTests(unittest.TestCase):
    def test_event_study_design_omits_reference_period_and_sets_zero_reference(self) -> None:
        panel = pd.DataFrame(
            {
                "tempo_relativo_meses": [-2, -1, 0, 1],
                "scenario_treat": [1, 1, 1, 1],
                "high_connect": [1, 1, 1, 1],
            }
        )

        event_data, dummy_names, t_to_name, reference = prepare_event_study_design(panel, bin_min=-2, bin_max=1)

        self.assertNotIn(-1, t_to_name)
        self.assertNotIn("ddd_tm1", dummy_names)
        self.assertEqual(reference["t"], -1)
        self.assertEqual(reference["coef"], 0.0)
        self.assertEqual(reference["se"], 0.0)
        self.assertEqual(event_data.loc[0, "ddd_tm2"], 1)
        self.assertEqual(event_data.loc[1, dummy_names].sum(), 0)


if __name__ == "__main__":
    unittest.main()
