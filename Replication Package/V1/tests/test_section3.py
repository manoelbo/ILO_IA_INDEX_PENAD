from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = PACKAGE_ROOT / "code"
sys.path.insert(0, str(CODE_ROOT))


class Section3DataConstructionTests(unittest.TestCase):
    def test_rejects_any_period_other_than_2025_q3(self) -> None:
        from section3.build_data import validate_pnad_period

        wrong = pd.DataFrame({"ano": [2025], "trimestre": [2]})
        with self.assertRaisesRegex(ValueError, "2025 Q3"):
            validate_pnad_period(wrong)

    def test_hierarchical_crosswalk_and_sector_mapping_are_deterministic(self) -> None:
        from section3.build_data import (
            apply_hierarchical_crosswalk,
            clean_pnad,
            finalize_analytic_data,
            process_ilo,
        )

        raw = pd.DataFrame(
            [
                {
                    "ano": 2025,
                    "trimestre": 3,
                    "sigla_uf": "SP",
                    "sexo": 1,
                    "idade": 30,
                    "raca_cor": 1,
                    "nivel_instrucao": 5,
                    "cod_ocupacao": "1111",
                    "grupamento_atividade": 58000,
                    "posicao_ocupacao": 1,
                    "rendimento_habitual": 3000,
                    "rendimento_efetivo": 2900,
                    "horas_habituais": 40,
                    "horas_efetivas": 38,
                    "peso": 2.0,
                },
                {
                    "ano": 2025,
                    "trimestre": 3,
                    "sigla_uf": "BA",
                    "sexo": 2,
                    "idade": 40,
                    "raca_cor": 4,
                    "nivel_instrucao": 7,
                    "cod_ocupacao": "1239",
                    "grupamento_atividade": 85000,
                    "posicao_ocupacao": 2,
                    "rendimento_habitual": 5000,
                    "rendimento_efetivo": 4800,
                    "horas_habituais": 40,
                    "horas_efetivas": 40,
                    "peso": 3.0,
                },
                {
                    "ano": 2025,
                    "trimestre": 3,
                    "sigla_uf": "BA",
                    "sexo": 2,
                    "idade": 17,
                    "raca_cor": 4,
                    "nivel_instrucao": 5,
                    "cod_ocupacao": "1111",
                    "grupamento_atividade": 85000,
                    "posicao_ocupacao": 2,
                    "rendimento_habitual": 1000,
                    "rendimento_efetivo": 1000,
                    "horas_habituais": 20,
                    "horas_efetivas": 20,
                    "peso": 1.0,
                },
            ]
        )
        ilo_raw = pd.DataFrame(
            {
                "ISCO_08": [1111, 1230, 1231],
                "Title": ["Exact", "Fallback A", "Fallback B"],
                "mean_score_2025": [0.2, 0.4, 0.6],
                "SD_2025": [0.1, 0.1, 0.1],
                "potential25": [
                    "Not Exposed",
                    "Exposed: Gradient 1",
                    "Exposed: Gradient 1",
                ],
            }
        )

        clean, diagnostics = clean_pnad(raw)
        ilo = process_ilo(ilo_raw)
        matched, coverage = apply_hierarchical_crosswalk(clean, ilo)
        final = finalize_analytic_data(matched)

        self.assertEqual(len(final), 2)
        self.assertEqual(diagnostics["after_filters"], 2)
        self.assertEqual(final["match_level"].tolist(), ["4-digit", "3-digit"])
        self.assertAlmostEqual(float(final.loc[1, "exposure_score"]), 0.5)
        self.assertEqual(
            final["setor_agregado"].tolist(),
            ["Informação e Comunicação", "Educação"],
        )
        self.assertEqual(coverage["rows_4_digit"], 1)
        self.assertEqual(coverage["rows_3_digit"], 1)


class Section3PipelineTests(unittest.TestCase):
    def test_reproduce_mode_writes_five_tables_without_external_repository_paths(self) -> None:
        from section3.pipeline import run

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "section3"
            summary = run(
                package_root=PACKAGE_ROOT,
                mode="reproduce",
                raw_dir=PACKAGE_ROOT / "data" / "raw" / "section3",
                output_dir=output_dir,
                billing_project=None,
                skip_figures=True,
            )

            self.assertEqual(summary.table_count, 5)
            self.assertEqual(summary.figure_count, 0)
            self.assertEqual(summary.failure_count, 0)
            self.assertEqual(len(list((output_dir / "tables").glob("*.csv"))), 5)
            manifest = (output_dir / "run_manifest.json").read_text(encoding="utf-8")
            self.assertNotIn("/Users/", manifest)


if __name__ == "__main__":
    unittest.main()
