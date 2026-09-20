import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "bibliography"
    / "build_corrected_bibliography.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "build_corrected_bibliography", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CorrectedBibliographyTests(unittest.TestCase):
    def test_replace_entry_changes_only_requested_key(self):
        module = load_module()
        source = (
            "@article{first,\n\ttitle = {Old},\n}\n\n"
            "@article{second,\n\ttitle = {Keep},\n}\n"
        )
        replacement = "@article{first,\n\ttitle = {New},\n}\n"

        result = module.replace_entry(source, "first", replacement)

        self.assertIn("title = {New}", result)
        self.assertIn("@article{second,\n\ttitle = {Keep}", result)

    def test_replace_in_entry_refuses_missing_old_value(self):
        module = load_module()
        source = "@article{first,\n\ttitle = {Old},\n}\n"

        with self.assertRaisesRegex(ValueError, "expected text"):
            module.replace_in_entry(
                source,
                "first",
                "title = {Missing}",
                "title = {New}",
            )


if __name__ == "__main__":
    unittest.main()
