from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = PACKAGE_ROOT / "code"
sys.path.insert(0, str(CODE_ROOT))


class Sections45InputTests(unittest.TestCase):
    def test_frozen_inputs_satisfy_the_panel_and_treatment_contract(self) -> None:
        from sections4_5.panel import validate_analytic_inputs

        checks, denominators = validate_analytic_inputs(
            PACKAGE_ROOT / "data" / "derived" / "sections4_5"
        )

        self.assertFalse([check for check in checks if check.status == "FAIL"])
        self.assertEqual(denominators["panel_observations"], 23_319)
        self.assertEqual(denominators["panel_cbo4"], 436)
        self.assertEqual(denominators["panel_months"], 54)
        self.assertEqual(denominators["main_treated_cbo4"], 75)
        self.assertEqual(denominators["main_control_cbo4"], 266)

    def test_full_mode_preflight_lists_missing_raw_inputs(self) -> None:
        from sections4_5.full_pipeline import (
            OPTIONAL_CROSSWALK_CACHE_FILENAMES,
            REQUIRED_RAW_FILENAMES,
            full_input_status,
            optional_cache_status,
            validate_full_inputs,
        )

        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            statuses = full_input_status(raw_dir)
            self.assertEqual(
                [filename for filename, _exists in statuses],
                list(REQUIRED_RAW_FILENAMES),
            )
            self.assertFalse(any(exists for _filename, exists in statuses))
            optional = optional_cache_status(raw_dir)
            self.assertEqual(
                [filename for filename, _exists in optional],
                list(OPTIONAL_CROSSWALK_CACHE_FILENAMES),
            )
            self.assertFalse(any(exists for _filename, exists in optional))
            with self.assertRaisesRegex(
                FileNotFoundError,
                "caged_2021.parquet",
            ):
                validate_full_inputs(raw_dir)
            with self.assertRaisesRegex(
                FileNotFoundError,
                "cbo-isco-conc.csv",
            ):
                validate_full_inputs(raw_dir, billing_project="billing-project")


class Sections45PipelineTests(unittest.TestCase):
    def test_publication_tables_are_rendered_from_backing_data(self) -> None:
        from sections4_5.publication import render_tables

        data_root = PACKAGE_ROOT / "data" / "derived" / "sections4_5"
        reference = (
            PACKAGE_ROOT
            / "results"
            / "reference"
            / "sections4_5"
            / "tables"
        )
        with tempfile.TemporaryDirectory() as tmp:
            written = render_tables(data_root, Path(tmp))
            self.assertEqual(len(written), 46)
            for expected in sorted(reference.glob("*.csv")):
                observed = Path(tmp) / expected.name
                self.assertEqual(
                    observed.read_bytes(),
                    expected.read_bytes(),
                    expected.name,
                )

    def test_reproduce_mode_is_standalone_and_reestimates_core_models(self) -> None:
        from sections4_5.pipeline import run

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "sections4_5"
            summary = run(
                package_root=PACKAGE_ROOT,
                mode="reproduce",
                raw_dir=PACKAGE_ROOT / "data" / "raw" / "sections4_5",
                output_dir=output_dir,
                skip_figures=True,
            )

            self.assertEqual(summary.table_count, 23)
            self.assertEqual(summary.figure_count, 0)
            self.assertEqual(summary.failure_count, 0)
            self.assertEqual(
                len(list((output_dir / "tables").glob("*.csv"))),
                23,
            )
            replay = pd.read_csv(
                output_dir / "backing_data" / "core_model_reestimation.csv"
            )
            self.assertEqual(len(replay), 4)
            self.assertLessEqual(float(replay["max_abs_difference"].max()), 1e-12)
            manifest = (output_dir / "run_manifest.json").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("/Users/", manifest)
            self.assertNotIn("Secao 4 e 5 concluida", manifest)


if __name__ == "__main__":
    unittest.main()
