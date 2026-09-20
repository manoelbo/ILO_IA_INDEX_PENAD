import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "build_artifact_inventory.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "build_artifact_inventory", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArtifactInventoryTests(unittest.TestCase):
    def test_workspace_paths_are_made_relative_without_touching_urls(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            rows = [
                {"artifact_path": (root / "results" / "table.csv").as_posix()},
                {"artifact_path": "https://example.org/table.csv"},
                {"artifact_path": "embedded:data-uri"},
            ]

            module.relativize_workspace_paths(rows, root)

            self.assertEqual(rows[0]["artifact_path"], "results/table.csv")
            self.assertEqual(
                rows[1]["artifact_path"], "https://example.org/table.csv"
            )
            self.assertEqual(rows[2]["artifact_path"], "embedded:data-uri")

    def test_manuscript_inventory_resolves_local_image_and_broken_link(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = root / "assets" / "figure.png"
            asset.parent.mkdir()
            asset.write_bytes(b"png")
            manuscript = root / "paper.md"
            manuscript.write_text(
                "**Figura 1: Test**\n\n"
                "![plot](assets/figure.png)\n\n"
                "[backing](https://app.notion.com/p/outputs/table.csv)\n",
                encoding="utf-8",
            )

            rows = module.inventory_manuscript(manuscript)

            image = next(row for row in rows if row["artifact_type"] == "image")
            link = next(
                row for row in rows if row["artifact_type"] == "artifact_link"
            )
            self.assertEqual(image["status"], "present")
            self.assertEqual(len(image["sha256"]), 64)
            self.assertEqual(link["status"], "broken")


if __name__ == "__main__":
    unittest.main()
