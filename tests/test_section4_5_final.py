import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from section4_5_final.config import EXPECTED_FIGURES, EXPECTED_TABLES
from section4_5_final.formatting import effect_label, evidence_label, percent_from_log
from section4_5_final.section5_2_tables import (
    BALANCE_ROBUSTNESS_OUTCOME_ORDER,
    HETEROGENEITY_SPECS,
    OUTCOME_ORDER,
    PRIMARY_OUTCOME_ORDER,
    SECTION5_2_OUTCOME_ORDER,
    SECTION5_2_TABLE_SPECS,
    build_heterogeneity_long,
    build_national_long,
    significance_stars,
    validate_section5_2_outputs,
    write_section5_2_tables,
)
from section4_5_final.tables import build_crosswalk_coverage_table, build_crosswalk_table, build_panel_descriptive_table


class Section45FinalContractTests(unittest.TestCase):
    def test_expected_artifacts_match_dissertation_outline(self) -> None:
        self.assertEqual(
            EXPECTED_FIGURES,
            [
                "figure_4_1_empirical_timeline.png",
                "figure_4_2_caged_crosswalk_pipeline.png",
                "figure_5_1_national_event_studies.png",
                "figure_5_3_1_occupation_cases_admissions_by_age.png",
                "figure_5_3_2_occupation_cases_real_admission_wage_by_age.png",
                "figure_a_1_connectivity_extension.png",
                "figure_b_1_occupation_cases_by_sex.png",
                "figure_b_2_occupation_cases_by_race_color.png",
                "figure_b_3_occupation_cases_by_education.png",
            ],
        )
        self.assertEqual(
            EXPECTED_TABLES,
            [
                "table_4_1_crosswalk_exposure_summary",
                "table_4_2a_panel_descriptive_summary",
                "table_4_2b_ilo_cbo_classification",
                "table_4_2c_crosswalk_coverage",
                "table_5_2_1_national_main_results",
                "table_5_2_2_heterogeneity_sex",
                "table_5_2_3_heterogeneity_income",
                "table_5_2_3_b",
                "table_5_2_4_heterogeneity_age_canaries",
                "table_5_2_4_b",
                "table_5_2_5_heterogeneity_race_color",
                "table_5_2_5_b",
                "table_5_2_6_heterogeneity_education",
                "table_5_2_net_flow_results",
                "table_5_3_1_occupation_case_exposure_summary",
                "table_5_5_robustness_and_limits",
                "table_a_1_connectivity_extension",
                "table_a_2_top_30_results",
                "table_b_1_occupation_case_age_terminal_matrix",
                "table_b_2_occupation_case_preperiod_diagnostics",
                "table_b_3_occupation_case_sensitivity_matrix",
                "table_b_4_occupation_case_demographic_terminal_matrix",
                "table_b_5_legacy_manual_group_diagnostics",
            ],
        )

    def test_labels_do_not_overstate_failed_pretrends(self) -> None:
        self.assertEqual(evidence_label("pass", False), "Evidência mais forte")
        self.assertEqual(evidence_label("fail", False), "Sugestivo; pretrend falha")
        self.assertEqual(evidence_label("not_available", False), "Sugestivo; sem pretrend formal")
        self.assertEqual(evidence_label("pass", True), "Exploratório")

    def test_log_effect_labels_convert_only_log_outcomes(self) -> None:
        self.assertEqual(effect_label(-0.05, "ln_admissoes", "Admissões (log)"), "-4,88%")
        self.assertEqual(effect_label(-0.10, "asinh_saldo", "Saldo líquido (asinh)"), "-0,1000")
        self.assertAlmostEqual(percent_from_log(-0.05), -4.8771, places=4)

    def test_crosswalk_coverage_aggregates_exposed_gradients(self) -> None:
        import pandas as pd

        classification = pd.DataFrame(
            {
                "cbo_4d": ["1111", "2222", "3333", "4444", "5555"],
                "cbo_ilo_gradient": [
                    "Exposed: Gradient 1",
                    "Exposed: Gradient 3",
                    "Not Exposed",
                    "Minimal Exposure",
                    "No score",
                ],
                "mte_match_status": [
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "matched_official_mte",
                    "sem_match_mte_no_result",
                ],
            }
        )
        panel = pd.DataFrame(
            {
                "cbo_4d": [1111, 1111, 2222, 3333, 4444],
                "periodo": ["2021-01", "2021-02", "2021-01", "2021-01", "2021-01"],
            }
        )

        out = build_crosswalk_coverage_table({"classification": classification, "panel": panel})

        exposed = out[out["Categoria"].eq("Exposed")].iloc[0]
        no_score = out[out["Categoria"].eq("No score")].iloc[0]
        self.assertEqual(
            out.columns.tolist(),
            ["Categoria", "CBOs", "% do total", "Observações CBO-mês", "% das observações"],
        )
        self.assertEqual(exposed["CBOs"], "2")
        self.assertEqual(exposed["% do total"], "40,0%")
        self.assertEqual(exposed["Observações CBO-mês"], "3")
        self.assertEqual(exposed["% das observações"], "60,0%")
        self.assertEqual(no_score["Observações CBO-mês"], "0")

    def test_ilo_classification_uses_check_columns_for_roles(self) -> None:
        import pandas as pd

        crosswalk = pd.DataFrame(
            {
                "gradient": ["Exposed: Gradient 3", "Minimal Exposure", "Not Exposed", "No score"],
                "n_cbo": [31, 95, 266, 193],
                "matched_mte": [31, 95, 266, 0],
                "strict_treated": [31, 0, 0, 0],
                "strict_control": [0, 0, 266, 0],
                "mean_score": [0.539, 0.329, 0.202, None],
                "pooled_sd": [0.114, 0.123, 0.080, None],
            }
        )

        out = build_crosswalk_table({"crosswalk": crosswalk})

        self.assertIn("Tratamento", out.columns)
        self.assertIn("Controle", out.columns)
        self.assertIn("Excluído", out.columns)
        self.assertEqual(out.loc[out["Categoria OIT"].eq("Exposed: Gradient 3"), "Tratamento"].iloc[0], "✓")
        self.assertEqual(out.loc[out["Categoria OIT"].eq("Not Exposed"), "Controle"].iloc[0], "✓")
        self.assertEqual(out.loc[out["Categoria OIT"].eq("Minimal Exposure"), "Excluído"].iloc[0], "✓")
        self.assertEqual(out.loc[out["Categoria OIT"].eq("No score"), "Excluído"].iloc[0], "✓")

    def test_panel_descriptive_table_contains_only_scope_rows(self) -> None:
        import pandas as pd

        panel = pd.DataFrame(
            {
                "cbo_4d": ["1111", "1111", "2222"],
                "periodo": ["2021-01", "2021-02", "2021-01"],
                "admissoes": [10, 20, 30],
            }
        )

        out = build_panel_descriptive_table({"panel": panel})

        self.assertEqual(out.columns.tolist(), ["Bloco", "Indicador", "Valor"])
        self.assertEqual(out["Indicador"].tolist(), ["Observações CBO-mês", "CBOs únicos", "Meses", "Janela"])
        self.assertEqual(out["Valor"].tolist(), ["3", "2", "2", "2021-01 a 2021-02"])


class Section52TableTests(unittest.TestCase):
    @staticmethod
    def _row(dimension: str, group_id: str, group_label: str, outcome: str) -> dict[str, object]:
        outcome_label = {
            "ln_admissoes": "Admissões (log)",
            "ln_desligamentos": "Desligamentos (log)",
            "ln_salario_real_adm": "Salário real de admissão (log)",
            "asinh_saldo": "Saldo líquido (asinh)",
            "saldo_per_pre_adm": "Saldo líquido / admissões pré",
            "saldo_flow_rate": "Saldo líquido / fluxo total",
        }[outcome]
        return {
            "dimension": dimension,
            "group_id": group_id,
            "group_label": group_label,
            "comparison": "target_vs_complement",
            "outcome": outcome,
            "outcome_label": outcome_label,
            "group_result_status": "estimated",
            "group_coef": -0.02,
            "group_se": 0.01,
            "group_p_value": 0.049,
            "group_stars": "**",
            "group_n_obs": 100,
            "group_n_cbo": 20,
            "group_error": "",
            "group_model": "outcome ~ post_treat | cbo_4d + periodo",
            "group_pretrend_status": "pass",
            "group_pretrend_p_value": 0.50,
            "group_pretrend_error": "",
            "group_power_status": "limited",
            "group_treated_cbo": 8,
            "group_control_cbo": 12,
            "result_status": "estimated",
            "coef": -0.01,
            "se": 0.005,
            "p_value": 0.04,
            "stars": "**",
            "n_obs": 200,
            "n_cbo": 20,
            "error": "",
            "model": "outcome ~ post_treat_group | cbo_4d + periodo",
            "pretrend_status": "warning",
            "pretrend_p_value": 0.08,
            "pretrend_error": "",
            "power_status": "limited",
            "wald_statistic": 4.2,
            "wald_test_method": "wald_test_R_beta_eq_q_chi2",
            "target_cbo_with_flows": 18,
        }

    @classmethod
    def _sources(cls) -> dict[str, pd.DataFrame]:
        general_rows = []
        real_rows = []
        canaries_rows = []
        net_flow_rows = []
        for spec in SECTION5_2_TABLE_SPECS.values():
            for group_id, group_label in spec["groups"]:
                for outcome in SECTION5_2_OUTCOME_ORDER:
                    row = cls._row(spec["dimension"], group_id, group_label, outcome)
                    if outcome in ["asinh_saldo", *BALANCE_ROBUSTNESS_OUTCOME_ORDER]:
                        net_flow_rows.append(row)
                    elif spec["source"] == "canaries_age":
                        canaries_rows.append(row)
                    elif outcome == "ln_salario_real_adm":
                        real_rows.append(row)
                    else:
                        general_rows.append(row)
        national_flows = pd.DataFrame(
            [
                {
                    "outcome": outcome,
                    "outcome_label": label,
                    "coef": -0.03,
                    "se": 0.02,
                    "p_value": 0.14,
                    "stars": "",
                    "result_status": "estimated",
                    "n_obs": 300,
                    "n_cbo": 30,
                }
                for outcome, label in [
                    ("ln_admissoes", "Admissões (log)"),
                    ("ln_desligamentos", "Desligamentos (log)"),
                ]
            ]
        )
        national_real = pd.DataFrame(
            [
                {
                    "outcome": "ln_salario_real_adm",
                    "outcome_label": "Salário real de admissão (log)",
                    "coef": -0.02,
                    "se": 0.01,
                    "p_value": 0.04,
                    "stars": "**",
                    "result_status": "estimated",
                    "n_obs": 290,
                    "n_cbo": 30,
                },
                {
                    "outcome": "ln_salario_real_desl",
                    "outcome_label": "Salário real de desligamento (log)",
                    "coef": 0.01,
                    "se": 0.01,
                    "p_value": 0.30,
                    "stars": "",
                    "result_status": "estimated",
                    "n_obs": 280,
                    "n_cbo": 30,
                },
            ]
        )
        pretrends = pd.DataFrame(
            [
                {"outcome": outcome, "pretrend_status": "pass", "joint_p_value": 0.50}
                for outcome in OUTCOME_ORDER
            ]
        )
        net_flow = pd.DataFrame(
            [
                {
                    "outcome": outcome,
                    "outcome_label": label,
                    "coef": -0.01,
                    "se": 0.01,
                    "p_value": 0.20,
                    "stars": "",
                    "result_status": "estimated",
                    "n_obs": 300,
                    "n_cbo": 30,
                }
                for outcome, label in [
                    ("asinh_saldo", "Saldo líquido (asinh)"),
                    ("saldo_per_pre_adm", "Saldo líquido / admissões pré"),
                    ("saldo_flow_rate", "Saldo líquido / fluxo total"),
                ]
            ]
        )
        net_flow_pretrends = pd.DataFrame(
            [
                {"outcome": "asinh_saldo", "pretrend_status": "fail", "joint_p_value": 0.01},
                {"outcome": "saldo_per_pre_adm", "pretrend_status": "pass", "joint_p_value": 0.50},
            ]
        )
        return {
            "main": national_flows,
            "real_main": national_real,
            "main_pretrends": pretrends,
            "heterogeneity": pd.DataFrame(general_rows),
            "heterogeneity_real_wage": pd.DataFrame(real_rows),
            "canaries_age": pd.DataFrame(canaries_rows),
            "net_flow": net_flow,
            "net_flow_pretrends": net_flow_pretrends,
            "net_flow_heterogeneity": pd.DataFrame(net_flow_rows),
        }

    def test_national_table_contains_four_primary_and_two_balance_robustness_outcomes(self) -> None:
        out = build_national_long(self._sources())

        self.assertEqual(len(out), 6)
        self.assertEqual(out["outcome"].tolist(), SECTION5_2_OUTCOME_ORDER)
        self.assertEqual(out.loc[out["outcome_role"].eq("primary"), "outcome"].tolist(), PRIMARY_OUTCOME_ORDER)
        self.assertEqual(
            out.loc[out["outcome_role"].eq("balance_robustness"), "outcome"].tolist(),
            BALANCE_ROBUSTNESS_OUTCOME_ORDER,
        )
        self.assertNotIn("ln_salario_real_desl", set(out["outcome"]))

    def test_national_markdown_matches_the_heterogeneity_panel_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_section5_2_tables(self._sources(), output_dir)
            markdown = (output_dir / "table_5_2_1_national_main_results.md").read_text(
                encoding="utf-8"
            )

        self.assertIn(
            "| Amostra | Admissões (log) | Desligamentos (log) | "
            "Salário real de admissão (log) | Saldo líquido (asinh) |",
            markdown,
        )
        self.assertIn("| Nacional | -0,0300<br>(0,0200)", markdown)
        self.assertIn(
            "| Resultado | DiD nacional | p DiD | Pretrend | N | CBOs |",
            markdown,
        )
        self.assertIn(
            "| Saldo líquido / admissões pré | -0,0100<br>(0,0100) | 0,200 |",
            markdown,
        )

    def test_table_star_thresholds_are_strictly_below_cutoffs(self) -> None:
        self.assertEqual(significance_stars(0.10), "")
        self.assertEqual(significance_stars(0.099999), "*")
        self.assertEqual(significance_stars(0.05), "*")
        self.assertEqual(significance_stars(0.049999), "**")
        self.assertEqual(significance_stars(0.01), "**")
        self.assertEqual(significance_stars(0.009999), "***")

    def test_heterogeneity_tables_have_exact_rows_and_group_order(self) -> None:
        sources = self._sources()
        expected_rows = {
            "sex": 12,
            "income": 18,
            "income_pnad": 30,
            "age_canaries": 36,
            "age_pnad": 30,
            "race_color": 36,
            "race_color_b": 12,
            "education": 18,
        }
        for table_id, expected in expected_rows.items():
            with self.subTest(table_id=table_id):
                out = build_heterogeneity_long(sources, table_id)
                spec = SECTION5_2_TABLE_SPECS[table_id]
                expected_groups = [
                    group_id
                    for group_id, _ in spec["groups"]
                    for _outcome in SECTION5_2_OUTCOME_ORDER
                ]
                self.assertEqual(len(out), expected)
                self.assertEqual(out["group_id"].tolist(), expected_groups)
                self.assertEqual(
                    out.groupby("group_id", sort=False)["outcome"].agg(list).tolist(),
                    [SECTION5_2_OUTCOME_ORDER] * len(spec["groups"]),
                )
                self.assertTrue(out[["group_coef", "group_se", "group_p_value", "ddd_coef", "ddd_se", "ddd_p_value"]].notna().all().all())

    def test_writer_creates_two_panel_markdown_and_numeric_long_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            legacy_csv = output_dir / "table_5_1_national_main_results.csv"
            legacy_md = output_dir / "table_5_1_national_main_results.md"
            legacy_csv.write_text("stale", encoding="utf-8")
            legacy_md.write_text("stale", encoding="utf-8")
            generated = write_section5_2_tables(self._sources(), output_dir)
            validation = validate_section5_2_outputs(output_dir)
            sex_md = (output_dir / "table_5_2_2_heterogeneity_sex.md").read_text(encoding="utf-8")
            sex_csv = pd.read_csv(output_dir / "table_5_2_2_heterogeneity_sex.csv")
            income_pnad_md = (output_dir / "table_5_2_3_b.md").read_text(encoding="utf-8")
            age_pnad_csv = pd.read_csv(output_dir / "table_5_2_4_b.csv")
            race_color_b_md = (output_dir / "table_5_2_5_b.md").read_text(encoding="utf-8")
            race_color_b_csv = pd.read_csv(output_dir / "table_5_2_5_b.csv")
            legacy_removed = not legacy_csv.exists() and not legacy_md.exists()

        self.assertEqual(
            set(generated),
            {spec["stem"] for spec in SECTION5_2_TABLE_SPECS.values()}
            | {"table_5_2_1_national_main_results"},
        )
        self.assertIn("Painel A", sex_md)
        self.assertIn("Painel B.1", sex_md)
        self.assertIn("Painel B.2", sex_md)
        self.assertIn("Saldo líquido (asinh)", sex_md)
        self.assertIn("Saldo líquido / admissões pré", sex_md)
        self.assertIn("Saldo líquido / fluxo total", sex_md)
        self.assertIn("* p<0,10; ** p<0,05; *** p<0,01", sex_md)
        self.assertIn("clusterizados por CBO de quatro dígitos", sex_md)
        self.assertIn("testes múltiplos", sex_md)
        self.assertEqual(len(sex_csv), 12)
        self.assertEqual(set(sex_csv["outcome_role"]), {"primary", "balance_robustness"})
        self.assertIn("faixas PNAD/IBGE", income_pnad_md)
        self.assertEqual(len(age_pnad_csv), 30)
        self.assertIn("Negra (preta e parda)", race_color_b_md)
        self.assertIn("contraste direto entre Branca e Negra", race_color_b_md)
        self.assertEqual(len(race_color_b_csv), 12)
        self.assertEqual(
            race_color_b_csv["group_id"].drop_duplicates().tolist(),
            ["race_white", "race_black_combined"],
        )
        self.assertNotIn("ln_salario_real_desl", sex_csv.to_csv(index=False))
        self.assertTrue(validation["status"].eq("pass").all())
        self.assertTrue(legacy_removed)

    def test_validation_rejects_removed_outcome_in_new_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_section5_2_tables(self._sources(), output_dir)
            national_path = output_dir / "table_5_2_1_national_main_results.csv"
            contaminated = pd.read_csv(national_path)
            contaminated.loc[0, "outcome"] = "ln_salario_real_desl"
            contaminated.to_csv(national_path, index=False)

            with self.assertRaisesRegex(RuntimeError, "dismissal-wage outcome"):
                validate_section5_2_outputs(output_dir)

    def test_validation_rejects_flow_support_outside_model_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_section5_2_tables(self._sources(), output_dir)
            sex_path = output_dir / "table_5_2_2_heterogeneity_sex.csv"
            contaminated = pd.read_csv(sex_path)
            contaminated.loc[0, "target_cbo_with_flows"] = 999
            contaminated.to_csv(sex_path, index=False)

            with self.assertRaisesRegex(RuntimeError, "Flow-support CBO count exceeds"):
                validate_section5_2_outputs(output_dir)

    def test_validation_rejects_missing_group_estimates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_section5_2_tables(self._sources(), output_dir)
            sex_path = output_dir / "table_5_2_2_heterogeneity_sex.csv"
            contaminated = pd.read_csv(sex_path)
            contaminated.loc[0, "group_coef"] = pd.NA
            contaminated.to_csv(sex_path, index=False)

            with self.assertRaisesRegex(RuntimeError, "Missing or failed estimates"):
                validate_section5_2_outputs(output_dir)

    def test_new_pnad_tables_preserve_non_estimable_cells_explicitly(self) -> None:
        sources = self._sources()
        net_flow = sources["net_flow_heterogeneity"].copy()
        failed = (
            net_flow["dimension"].eq("income_pnad")
            & net_flow["group_id"].eq("income_up_to_1sm")
            & net_flow["outcome"].eq("asinh_saldo")
        )
        net_flow.loc[failed, ["group_result_status", "result_status"]] = "failed_insufficient_sample"
        net_flow.loc[
            failed,
            ["group_coef", "group_se", "group_p_value", "coef", "se", "p_value", "wald_statistic"],
        ] = pd.NA
        net_flow.loc[failed, ["group_error", "error"]] = "Insufficient support for estimation."
        net_flow.loc[failed, ["group_pretrend_status", "pretrend_status"]] = "not_available"
        net_flow.loc[failed, ["group_pretrend_p_value", "pretrend_p_value"]] = pd.NA
        sources["net_flow_heterogeneity"] = net_flow

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_section5_2_tables(sources, output_dir)
            validation = validate_section5_2_outputs(output_dir)
            income_pnad_md = (output_dir / "table_5_2_3_b.md").read_text(encoding="utf-8")

        self.assertIn("não estimável", income_pnad_md)
        self.assertTrue(validation["status"].eq("pass").all())

    def test_validation_rejects_missing_significance_stars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_section5_2_tables(self._sources(), output_dir)
            sex_path = output_dir / "table_5_2_2_heterogeneity_sex.csv"
            contaminated = pd.read_csv(sex_path)
            contaminated.loc[0, "group_stars"] = ""
            contaminated.to_csv(sex_path, index=False)

            with self.assertRaisesRegex(RuntimeError, "Inconsistent significance stars"):
                validate_section5_2_outputs(output_dir)


if __name__ == "__main__":
    unittest.main()
