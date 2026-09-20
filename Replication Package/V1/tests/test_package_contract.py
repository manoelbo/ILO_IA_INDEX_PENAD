from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = PACKAGE_ROOT / "code"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "replication_runner",
        PACKAGE_ROOT / "run_replication.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load run_replication.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReplicationPackageContractTests(unittest.TestCase):
    def test_public_layout_is_self_contained(self) -> None:
        expected = [
            PACKAGE_ROOT / "run_replication.py",
            PACKAGE_ROOT / "requirements.txt",
            PACKAGE_ROOT / "requirements-full.txt",
            CODE_ROOT / "common",
            CODE_ROOT / "section3",
            CODE_ROOT / "sections4_5",
            PACKAGE_ROOT / "data" / "derived" / "section3",
            PACKAGE_ROOT / "data" / "derived" / "sections4_5",
            PACKAGE_ROOT / "results" / "reference" / "section3",
            PACKAGE_ROOT / "results" / "reference" / "sections4_5",
        ]
        missing = [path for path in expected if not path.exists()]
        self.assertEqual(missing, [])

    def test_runner_defaults_to_strict_reproduction_of_all_sections(self) -> None:
        runner = load_runner()
        args = runner.parse_args([])
        self.assertEqual(args.section, "all")
        self.assertEqual(args.mode, "reproduce")
        self.assertFalse(args.dry_run)

    def test_full_dry_run_lists_the_six_stage_sections45_dag(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_ROOT / "run_replication.py"),
                "--section",
                "4-5",
                "--mode",
                "full",
                "--dry-run",
            ],
            cwd=Path(tempfile.gettempdir()),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for stage in [
            "01_panel",
            "02_crosswalk_treatment",
            "03_analysis_panel",
            "04_models",
            "05_extensions",
            "06_artifacts",
        ]:
            self.assertIn(stage, completed.stdout)

    def test_reference_inventory_has_published_artifact_counts(self) -> None:
        section3 = PACKAGE_ROOT / "results" / "reference" / "section3"
        sections45 = PACKAGE_ROOT / "results" / "reference" / "sections4_5"
        self.assertEqual(len(list((section3 / "tables").glob("*.csv"))), 5)
        self.assertEqual(len(list((section3 / "figures").glob("*.png"))), 10)
        self.assertEqual(len(list((sections45 / "tables").glob("*.csv"))), 23)
        self.assertEqual(len(list((sections45 / "figures").glob("*.png"))), 13)

    def test_reference_navigation_and_manifests_are_present(self) -> None:
        for section in ("section3", "sections4_5"):
            root = PACKAGE_ROOT / "results" / "reference" / section
            for filename in (
                "INDEX.md",
                "artifact_manifest.csv",
                "reference_manifest.json",
            ):
                self.assertTrue((root / filename).is_file(), root / filename)
            manifest = json.loads(
                (root / "reference_manifest.json").read_text(encoding="utf-8")
            )
            paths = [
                record["path"]
                for group in ("code", "inputs", "artifacts")
                for record in manifest[group]
            ]
            self.assertFalse([path for path in paths if Path(path).is_absolute()])

    def test_public_code_has_no_absolute_author_paths_or_html_authority(self) -> None:
        sources = [
            PACKAGE_ROOT / "run_replication.py",
            *sorted(CODE_ROOT.rglob("*.py")),
        ]
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in sources
        )
        self.assertNotIn("/Users/", combined)
        self.assertNotIn("AUTHOR_SOURCE_MAP", combined)
        self.assertNotIn("BeautifulSoup", combined)
        self.assertFalse(
            (CODE_ROOT / "sections4_5" / "html_export.py").exists()
        )

    def test_frozen_backing_data_is_the_explicit_public_whitelist(self) -> None:
        sys.path.insert(0, str(CODE_ROOT))
        from sections4_5.contracts import BACKING_DATA_FILES

        backing = (
            PACKAGE_ROOT
            / "data"
            / "derived"
            / "sections4_5"
            / "backing_data"
        )
        observed = {
            path.relative_to(backing).as_posix()
            for path in backing.rglob("*.csv")
        }
        self.assertEqual(observed, set(BACKING_DATA_FILES))

    def test_output_cleanup_requires_a_valid_package_manifest(self) -> None:
        sys.path.insert(0, str(CODE_ROOT))
        from common.files import prepare_output_directory

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "existing"
            output.mkdir()
            (output / "run_manifest.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (output / "user-file.txt").write_text(
                "preserve me\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "valid package run manifest"):
                prepare_output_directory(output, PACKAGE_ROOT)
            self.assertTrue((output / "user-file.txt").is_file())

    def test_output_cleanup_rejects_immutable_package_subtrees(self) -> None:
        sys.path.insert(0, str(CODE_ROOT))
        from common.files import prepare_output_directory

        with self.assertRaisesRegex(ValueError, "immutable output target"):
            prepare_output_directory(
                PACKAGE_ROOT / "data" / "raw" / "section3",
                PACKAGE_ROOT,
            )


if __name__ == "__main__":
    unittest.main()
