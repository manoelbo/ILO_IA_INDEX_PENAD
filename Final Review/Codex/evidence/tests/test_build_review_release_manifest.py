import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "build_review_release_manifest.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "build_review_release_manifest", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReviewReleaseManifestTests(unittest.TestCase):
    def test_inventory_is_portable_sorted_and_excludes_outputs_and_caches(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review = root / "Final Review/Codex"
            evidence = review / "evidence"
            evidence.mkdir(parents=True)
            (review / "z.md").write_text("zeta", encoding="utf-8")
            (review / "a.md").write_text("alpha", encoding="utf-8")
            (evidence / "__pycache__").mkdir()
            (evidence / "__pycache__/module.pyc").write_bytes(b"cache")
            package = root / "Replication Package"
            (package / "V1").mkdir(parents=True)
            (package / "V1/large.csv").write_text(
                "excluded", encoding="utf-8"
            )
            (package / "V2").mkdir()
            (package / "README.md").write_text("root", encoding="utf-8")
            (package / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
            (package / "V2/README.md").write_text("v2", encoding="utf-8")
            output = evidence / "release.csv"
            context_output = evidence / "release.json"
            output.write_text("old", encoding="utf-8")
            context_output.write_text("old", encoding="utf-8")

            rows = module.inventory_release(
                root=root,
                output=output,
                context_output=context_output,
            )

            self.assertEqual(
                [row["path"] for row in rows],
                [
                    "Final Review/Codex/a.md",
                    "Final Review/Codex/z.md",
                    "Replication Package/.gitignore",
                    "Replication Package/README.md",
                    "Replication Package/V2/README.md",
                ],
            )
            self.assertTrue(
                all(not Path(str(row["path"])).is_absolute() for row in rows)
            )
            self.assertTrue(all(len(str(row["sha256"])) == 64 for row in rows))

    def test_manifest_and_context_include_integrity_and_git_metadata(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "Final Review/Codex/evidence"
            evidence.mkdir(parents=True)
            baseline = evidence / "baseline_manifest.csv"
            baseline.write_text("baseline\n", encoding="utf-8")
            manifest = evidence / "review_release_manifest.csv"
            context_output = evidence / "review_release_context.json"
            module.write_manifest(
                manifest,
                [
                    {
                        "path": "Final Review/Codex/report.md",
                        "bytes": 6,
                        "sha256": "a" * 64,
                    }
                ],
            )

            def fake_git(_root, *args):
                if args == ("rev-parse", "HEAD"):
                    return "abc123\n"
                return " M tracked.md\n?? untracked.md\n"

            with mock.patch.object(module, "run_git", side_effect=fake_git):
                context = module.build_context(
                    root=root,
                    manifest=manifest,
                    generated_at_utc="2026-07-25T12:00:00+00:00",
                )
            module.write_context(context_output, context)

            with manifest.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(
                    reader.fieldnames,
                    ["path", "bytes", "sha256"],
                )
            saved = json.loads(context_output.read_text(encoding="utf-8"))
            self.assertEqual(saved["git_head"], "abc123")
            self.assertEqual(saved["verdict"], "DO NOT CIRCULATE")
            self.assertTrue(saved["git_status_summary"]["is_dirty"])
            self.assertEqual(saved["git_status_summary"]["entries"], 2)
            self.assertEqual(saved["git_status_summary"]["untracked"], 1)
            self.assertEqual(
                saved["manifest_sha256"],
                module.sha256_file(manifest),
            )
            self.assertEqual(
                saved["baseline_manifest_sha256"],
                module.sha256_file(baseline),
            )

    def test_status_summary_counts_index_and_worktree_states(self):
        module = load_module()
        summary = module.summarize_git_status(
            "M  staged.md\n M unstaged.md\nD  deleted.md\n"
            "R  old.md -> new.md\n?? new.txt\n"
        )

        self.assertEqual(summary["entries"], 5)
        self.assertEqual(summary["staged"], 3)
        self.assertEqual(summary["unstaged"], 1)
        self.assertEqual(summary["untracked"], 1)
        self.assertEqual(summary["deleted"], 1)
        self.assertEqual(summary["renamed"], 1)


if __name__ == "__main__":
    unittest.main()
