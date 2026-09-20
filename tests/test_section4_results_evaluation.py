import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_results_evaluation.scoring import (
    classify_channels,
    classify_causal_tier,
    effect_percent,
    score_candidate,
    select_top_results,
)


class ResultEvaluationScoringTests(unittest.TestCase):
    def test_classify_channels_tracks_market_reconfiguration_outcomes(self) -> None:
        self.assertIn("admission_flow", classify_channels("ln_admissoes", "Admissões (log)", "final_model"))
        self.assertIn("separation_flow", classify_channels("ln_desligamentos", "Demissões (log)", "final_model"))
        self.assertIn("entry_wage", classify_channels("ln_salario_real_adm", "Salário real de admissão (log)", "final_model"))
        self.assertIn("exit_wage", classify_channels("ln_salario_real_desl", "Salário real de demissão (log)", "final_model"))
        self.assertIn("net_flow", classify_channels("asinh_saldo", "Saldo líquido (asinh)", "final_model"))
        self.assertIn("spatial_connectivity", classify_channels("ln_admissoes", "Admissões (log)", "connectivity_extension"))
        self.assertIn("occupational_mechanism", classify_channels("ln_admissoes", "Admissões (log)", "manual_occupation_groups"))

    def test_failed_pretrend_and_exploratory_results_cannot_be_causal_headlines(self) -> None:
        failed = classify_causal_tier(pretrend_status="fail", exploratory_only=False, p_value=0.001, source_family="final_model")
        exploratory = classify_causal_tier(pretrend_status="pass", exploratory_only=True, p_value=0.001, source_family="manual_occupation_groups")
        no_pretrend = classify_causal_tier(pretrend_status="not_available", exploratory_only=False, p_value=0.001, source_family="connectivity_extension")

        self.assertNotEqual(failed, "causal_headline")
        self.assertEqual(failed, "suggestive_pretrend_limit")
        self.assertEqual(exploratory, "exploratory")
        self.assertEqual(no_pretrend, "suggestive_no_pretrend_test")

    def test_effect_percent_uses_log_point_transform(self) -> None:
        self.assertAlmostEqual(effect_percent(-0.05, "ln_salario_real_adm", "Salário real de admissão (log)"), -4.8771, places=4)
        self.assertAlmostEqual(effect_percent(0.10, "ln_admissoes", "Admissões (log)"), 10.5171, places=4)
        self.assertTrue(pd.isna(effect_percent(-0.10, "asinh_saldo", "Saldo líquido (asinh)")))

    def test_selection_preserves_diversity_and_hard_gates(self) -> None:
        rows = []
        channel_specs = [
            ("admission_flow", "ln_admissoes", "Admissões (log)", "final_model", 4),
            ("separation_flow", "ln_desligamentos", "Demissões (log)", "final_model", 4),
            ("entry_wage", "ln_salario_real_adm", "Salário real de admissão (log)", "final_model", 6),
            ("net_flow", "asinh_saldo", "Saldo líquido (asinh)", "final_model", 2),
            ("composition_or_heterogeneity", "ln_salario_real_adm", "Salário real de admissão (log)", "final_model", 5),
            ("spatial_connectivity", "ln_admissoes", "Admissões (log)", "connectivity_extension", 3),
            ("occupational_mechanism", "ln_desligamentos", "Demissões (log)", "manual_occupation_groups", 3),
        ]
        idx = 0
        for channel, outcome, label, source, count in channel_specs:
            for _ in range(count):
                idx += 1
                tags = {channel}
                if outcome == "ln_admissoes":
                    tags.add("admission_flow")
                if outcome == "ln_desligamentos":
                    tags.add("separation_flow")
                if "salario" in outcome:
                    tags.add("entry_wage")
                rows.append(
                    {
                        "result_id": f"r{idx}",
                        "source_family": source,
                        "source_file": f"{source}.csv",
                        "row_index": idx,
                        "model_family": source,
                        "spec_id": f"spec{idx}",
                        "group_label": f"group{idx}",
                        "outcome": outcome,
                        "outcome_label": label,
                        "coef": -0.05,
                        "se": 0.01,
                        "p_value": 0.001,
                        "stars": "***",
                        "n_obs": 1000,
                        "n_cbo": 100,
                        "n_clusters": 100,
                        "pretrend_status": "pass",
                        "power_status": "adequate",
                        "exploratory_only": False,
                        "effect_percent": -4.8771,
                        "market_reconfiguration_channel": channel,
                        "channel_tags": "|".join(sorted(tags)),
                        "causal_tier": "causal_headline",
                        "deterministic_score": 90.0,
                        "placement": "texto principal",
                        "narrative_role": "headline",
                        "flags": "",
                    }
                )
        while len(rows) < 35:
            idx += 1
            rows.append({**rows[-1], "result_id": f"r{idx}", "row_index": idx, "group_label": f"extra{idx}", "deterministic_score": 50.0})
        rows.append({**rows[0], "result_id": "exploratory", "row_index": 999, "exploratory_only": True, "placement": "texto principal", "deterministic_score": 99.0})
        candidates = pd.DataFrame(rows)

        selected = select_top_results(candidates, top_n=30)

        self.assertEqual(len(selected), 30)
        self.assertFalse((selected["exploratory_only"] & selected["placement"].eq("texto principal")).any())
        for tag, minimum in {
            "admission_flow": 4,
            "separation_flow": 4,
            "entry_wage": 6,
            "net_flow": 2,
            "composition_or_heterogeneity": 5,
            "spatial_connectivity": 3,
            "occupational_mechanism": 3,
        }.items():
            count = selected["channel_tags"].fillna("").str.contains(tag, regex=False).sum()
            self.assertGreaterEqual(count, minimum)


class ResultEvaluationCandidateTests(unittest.TestCase):
    def test_score_candidate_adds_required_fields(self) -> None:
        row = pd.Series(
            {
                "source_family": "final_model",
                "outcome": "ln_admissoes",
                "outcome_label": "Admissões (log)",
                "coef": -0.04,
                "p_value": 0.03,
                "n_obs": 1000,
                "n_clusters": 80,
                "pretrend_status": "pass",
                "exploratory_only": False,
            }
        )

        scored = score_candidate(row)

        self.assertIn("admission_flow", scored["channel_tags"])
        self.assertEqual(scored["market_reconfiguration_channel"], "admission_flow")
        self.assertEqual(scored["causal_tier"], "causal_headline")
        self.assertGreater(scored["deterministic_score"], 0)


if __name__ == "__main__":
    unittest.main()
