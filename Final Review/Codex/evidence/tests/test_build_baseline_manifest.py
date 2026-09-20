import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "build_baseline_manifest.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "build_baseline_manifest", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaselineManifestTests(unittest.TestCase):
    def test_inventory_is_sorted_and_excludes_review_outputs(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Replication Package").mkdir()
            (root / "Replication Package" / "b.txt").write_text(
                "beta", encoding="utf-8"
            )
            (root / "Replication Package" / "a.txt").write_text(
                "alpha", encoding="utf-8"
            )
            (root / "Replication Package" / "__pycache__").mkdir()
            (root / "Replication Package" / "__pycache__" / "module.pyc").write_bytes(
                b"generated-bytecode"
            )
            (root / "Final Review" / "Codex").mkdir(parents=True)
            (root / "Final Review" / "Codex" / "ignored.md").write_text(
                "review", encoding="utf-8"
            )

            rows = module.inventory_paths(
                root=root,
                include_paths=[Path("Replication Package")],
                tracked_paths=set(),
                status_by_path={},
            )

            self.assertEqual(
                [row["path"] for row in rows],
                [
                    "Replication Package/__pycache__/module.pyc",
                    "Replication Package/a.txt",
                    "Replication Package/b.txt",
                ],
            )
            self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))
            self.assertTrue(all(row["tracked"] == "false" for row in rows))

    def test_write_manifest_uses_stable_column_order(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "manifest.csv"
            rows = [
                {
                    "path": "sample.txt",
                    "bytes": 6,
                    "mtime_utc": "2026-07-25T00:00:00+00:00",
                    "sha256": "a" * 64,
                    "tracked": "true",
                    "git_status": "",
                }
            ]

            module.write_manifest(output, rows)

            with output.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(
                    reader.fieldnames,
                    [
                        "path",
                        "bytes",
                        "mtime_utc",
                        "sha256",
                        "tracked",
                        "git_status",
                    ],
                )
                self.assertEqual(
                    list(reader),
                    [{**rows[0], "bytes": "6"}],
                )

    def test_write_status_snapshot_preserves_porcelain_output(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "git_status_before.txt"
            status = " M tracked.txt\n?? untracked.txt\n D deleted.txt\n"

            module.write_status_snapshot(output, status)

            self.assertEqual(
                output.read_text(encoding="utf-8"),
                status,
            )


if __name__ == "__main__":
    unittest.main()
