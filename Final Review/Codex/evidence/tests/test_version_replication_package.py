import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "version_replication_package.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "version_replication_package", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class VersionReplicationPackageTests(unittest.TestCase):
    def test_version_package_moves_verified_payload_into_v1(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "Replication Package"
            (package / "code").mkdir(parents=True)
            (package / "README.md").write_text("readme", encoding="utf-8")
            (package / "run_replication.py").write_text(
                "runner", encoding="utf-8"
            )
            (package / "code" / "model.py").write_text(
                "model", encoding="utf-8"
            )
            baseline = {
                "Replication Package/README.md": digest("readme"),
                "Replication Package/run_replication.py": digest("runner"),
                "Replication Package/code/model.py": digest("model"),
            }

            moved = module.version_package(
                package_root=package,
                baseline_hashes=baseline,
                execute=True,
            )

            self.assertEqual(
                moved,
                ["README.md", "code", "run_replication.py"],
            )
            self.assertEqual(
                (package / "V1" / "README.md").read_text(encoding="utf-8"),
                "readme",
            )
            self.assertTrue(package.joinpath("V1", "code", "model.py").is_file())
            self.assertFalse(package.joinpath("run_replication.py").exists())

    def test_version_package_refuses_hash_mismatch(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "Replication Package"
            package.mkdir()
            (package / "README.md").write_text("changed", encoding="utf-8")
            baseline = {
                "Replication Package/README.md": digest("original"),
            }

            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                module.version_package(
                    package_root=package,
                    baseline_hashes=baseline,
                    execute=True,
                )

            self.assertTrue(package.joinpath("README.md").is_file())
            self.assertFalse(package.joinpath("V1").exists())


if __name__ == "__main__":
    unittest.main()
