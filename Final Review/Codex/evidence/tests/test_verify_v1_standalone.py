import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "verify_v1_standalone.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "verify_v1_standalone", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StandaloneVerificationTests(unittest.TestCase):
    def test_output_rows_are_sorted_and_hashed(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "nested").mkdir()
            (root / "z.txt").write_bytes(b"z")
            (root / "nested" / "a.txt").write_bytes(b"alpha")

            rows = module.build_output_rows(root)

            self.assertEqual(
                [row["relative_path"] for row in rows],
                ["nested/a.txt", "z.txt"],
            )
            self.assertEqual([row["bytes"] for row in rows], [5, 1])
            self.assertTrue(all(len(str(row["sha256"])) == 64 for row in rows))


if __name__ == "__main__":
    unittest.main()
