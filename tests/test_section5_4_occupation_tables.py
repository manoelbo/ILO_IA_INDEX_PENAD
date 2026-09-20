import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.config import CORE_OCCUPATION_GROUPS
from section4_5_final.section5_4_tables import (
    OUTCOME_ORDER,
    SECTION5_4_EXPECTED_ROWS,
    SECTION5_4_STEMS,
    SECTION5_4_TABLE_SPECS,
    build_occupation_heterogeneity_long,
    build_occupation_main_long,
    validate_section5_4_outputs,
    write_section5_4_tables,
)


class Section54OccupationTableTests(unittest.TestCase):
    GROUP_LABELS = {
        "software_it_core": "Núcleo de Software e TI",
        "customer_contact": "Atendimento e Contato com Cliente",
        "finance_accounting_admin": "Finanças, Contabilidade e Administração",
        "creative_communication_language": "Comunicação, Linguagem e Conteúdo",
    }

    @staticmethod
    def _main_sources() -> dict[str, pd.DataFrame]:
        outcomes = {
            "ln_admissoes": "Admissões (log)",
            "ln_desligamentos": "Desligamentos (log)",
            "ln_salario_real_adm": "Salário real de admissão (log)",
        }
        rows = []
        pretrends = []
        for group_id in CORE_OCCUPATION_GROUPS:
            for outcome, outcome_label in outcomes.items():
                rows.append(
                    {
                        "group_id": group_id,
                        "group_label": Section54OccupationTableTests.GROUP_LABELS[group_id],
                        "outcome": outcome,
                        "outcome_label": outcome_label,
                        "result_status": "estimated",
                        "coef": -0.02,
                        "se": 0.01,
                        "p_value": 0.04,
                        "n_obs": 100,
                        "n_cbo": 20,
                        "treated_cbo_in_sample": 4,
                        "control_cbo_in_sample": 16,
                    }
                )
                pretrends.append(
                    {
                        "group_id": group_id,
                        "outcome": outcome,
                        "pretrend_status": "pass",
                        "joint_p_value": 0.50,
                    }
                )
        return {
            "occupation_main": pd.DataFrame(rows),
            "occupation_pretrends": pd.DataFrame(pretrends),
        }

    @classmethod
    def _sources(cls) -> dict[str, pd.DataFrame]:
        sources = cls._main_sources()
        demographic_rows = []
        canaries_rows = []
        for occupation_group_id in CORE_OCCUPATION_GROUPS:
            for table_id in ["sex", "income", "age_canaries", "race_color", "education"]:
                spec = SECTION5_4_TABLE_SPECS[table_id]
                for subgroup_id, subgroup_label in spec["groups"]:
                    for outcome in OUTCOME_ORDER:
                        row = {
                            "group_id": occupation_group_id,
                            "occupation_group_label": cls.GROUP_LABELS[occupation_group_id],
                            "dimension": spec["dimension"],
                            "heterogeneity_group_id": subgroup_id,
                            "heterogeneity_group_label": subgroup_label,
                            "comparison": "target_vs_complement",
                            "outcome": outcome,
                            "outcome_label": {
                                "ln_admissoes": "Admissões (log)",
                                "ln_desligamentos": "Desligamentos (log)",
                                "ln_salario_real_adm": "Salário real de admissão (log)",
                            }[outcome],
                            "group_result_status": "estimated",
                            "group_coef": -0.02,
                            "group_se": 0.01,
                            "group_p_value": 0.04,
                            "group_n_obs": 100,
                            "group_n_cbo": 20,
                            "group_pretrend_status": "pass",
                            "group_pretrend_p_value": 0.50,
                            "group_power_status": "thin",
                            "group_treated_cbo": 4,
                            "group_control_cbo": 16,
                            "result_status": "estimated",
                            "coef": -0.01,
                            "se": 0.005,
                            "p_value": 0.04,
                            "n_obs": 200,
                            "n_cbo": 20,
                            "pretrend_status": "pass",
                            "pretrend_p_value": 0.60,
                            "power_status": "thin",
                            "wald_statistic": 4.2,
                            "wald_test_method": "wald_test_R_beta_eq_q_chi2",
                            "target_cbo_with_flows": 18,
                        }
                        if spec["source"] == "canaries_age":
                            canaries_rows.append(row)
                        else:
                            demographic_rows.append(row)
        sources["occupation_demographic"] = pd.DataFrame(demographic_rows)
        sources["occupation_canaries"] = pd.DataFrame(canaries_rows)
        return sources

    def test_expected_stems_cover_main_and_five_heterogeneity_tables(self) -> None:
        self.assertEqual(len(SECTION5_4_STEMS), 6)
        self.assertEqual(set(SECTION5_4_STEMS), set(SECTION5_4_EXPECTED_ROWS))

    def test_main_table_contains_four_cores_and_three_outcomes_in_order(self) -> None:
        out = build_occupation_main_long(self._main_sources())

        self.assertEqual(len(out), 12)
        self.assertEqual(out["occupation_group_id"].drop_duplicates().tolist(), CORE_OCCUPATION_GROUPS)
        self.assertEqual(
            out.groupby("occupation_group_id", sort=False)["outcome"].agg(list).tolist(),
            [OUTCOME_ORDER] * len(CORE_OCCUPATION_GROUPS),
        )
        self.assertNotIn("ln_salario_real_desl", set(out["outcome"]))

    def test_heterogeneity_tables_cover_every_core_subgroup_and_outcome(self) -> None:
        sources = self._sources()
        for table_id in ["sex", "income", "age_canaries", "race_color", "education"]:
            with self.subTest(table_id=table_id):
                out = build_occupation_heterogeneity_long(sources, table_id)
                stem = SECTION5_4_TABLE_SPECS[table_id]["stem"]
                self.assertEqual(len(out), SECTION5_4_EXPECTED_ROWS[stem])
                self.assertEqual(out["occupation_group_id"].drop_duplicates().tolist(), CORE_OCCUPATION_GROUPS)
                self.assertTrue(
                    out[["group_coef", "group_se", "group_p_value", "ddd_coef", "ddd_se", "ddd_p_value"]]
                    .notna()
                    .all()
                    .all()
                )

    def test_writer_creates_six_csv_markdown_pairs_and_removes_old_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            old_csv = output_dir / "table_5_4_occupation_group_summary.csv"
            old_md = output_dir / "table_5_4_occupation_group_summary.md"
            old_csv.write_text("stale", encoding="utf-8")
            old_md.write_text("stale", encoding="utf-8")

            generated = write_section5_4_tables(self._sources(), output_dir)
            validation = validate_section5_4_outputs(output_dir)
            sex_md = (output_dir / f"{SECTION5_4_STEMS[1]}.md").read_text(encoding="utf-8")
            sex_csv = pd.read_csv(output_dir / f"{SECTION5_4_STEMS[1]}.csv")

        self.assertEqual(set(generated), set(SECTION5_4_STEMS))
        self.assertEqual(len(sex_csv), 24)
        self.assertIn("Painel A", sex_md)
        self.assertIn("Painel B", sex_md)
        self.assertIn("Núcleo de Software e TI", sex_md)
        self.assertIn("Comunicação, Linguagem e Conteúdo", sex_md)
        self.assertIn("* p<0,10; ** p<0,05; *** p<0,01", sex_md)
        self.assertNotIn("ln_salario_real_desl", sex_csv.to_csv(index=False))
        self.assertTrue(validation["status"].eq("pass").all())
        self.assertFalse(old_csv.exists())
        self.assertFalse(old_md.exists())

    def test_writer_preserves_unidentified_cells_as_explicit_not_estimable(self) -> None:
        sources = self._sources()
        data = sources["occupation_demographic"].copy()
        failed = (
            data["group_id"].eq("software_it_core")
            & data["dimension"].eq("income")
            & data["heterogeneity_group_id"].eq("high_income")
            & data["outcome"].eq("ln_admissoes")
        )
        data.loc[failed, ["group_result_status", "result_status"]] = "failed_insufficient_sample"
        data.loc[
            failed,
            ["group_coef", "group_se", "group_p_value", "coef", "se", "p_value", "wald_statistic"],
        ] = pd.NA
        data.loc[failed, ["group_pretrend_status", "pretrend_status"]] = "not_available"
        data.loc[failed, ["group_pretrend_p_value", "pretrend_p_value"]] = pd.NA
        sources["occupation_demographic"] = data

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_section5_4_tables(sources, output_dir)
            validation = validate_section5_4_outputs(output_dir)
            income_md = (output_dir / f"{SECTION5_4_STEMS[2]}.md").read_text(encoding="utf-8")

        self.assertIn("não estimável", income_md)
        self.assertTrue(validation["status"].eq("pass").all())


if __name__ == "__main__":
    unittest.main()
