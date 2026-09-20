import importlib.util
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "independent_replication"
    / "replicate_main.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "replicate_main", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IndependentReplicationTests(unittest.TestCase):
    def test_resolve_package_root_prefers_frozen_v1(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            current = workspace / "Replication Package"
            frozen = current / "V1"
            frozen.mkdir(parents=True)
            frozen.joinpath("run_replication.py").write_text(
                "# frozen", encoding="utf-8"
            )

            self.assertEqual(
                module.resolve_package_root(current),
                frozen.resolve(),
            )

    def test_compare_results_requires_six_decimal_agreement(self):
        module = load_module()
        python_results = pd.DataFrame(
            [
                {
                    "outcome": "y",
                    "coef": 0.123456789,
                    "se": 0.010000001,
                    "p_value": 0.25,
                    "n_obs": 100,
                    "n_clusters": 10,
                }
            ]
        )
        r_results = pd.DataFrame(
            [
                {
                    "outcome": "y",
                    "coef": 0.123456790,
                    "se": 0.010000002,
                    "p_value": 0.250000001,
                    "n_obs": 100,
                    "n_clusters": 10,
                }
            ]
        )

        comparison = module.compare_results(python_results, r_results)

        self.assertEqual(comparison.loc[0, "status"], "PASS")
        self.assertLess(comparison.loc[0, "max_abs_difference"], 5e-7)

    def test_compare_results_fails_different_sample_size(self):
        module = load_module()
        python_results = pd.DataFrame(
            [
                {
                    "outcome": "y",
                    "coef": 0.1,
                    "se": 0.01,
                    "p_value": 0.2,
                    "n_obs": 100,
                    "n_clusters": 10,
                }
            ]
        )
        r_results = python_results.copy()
        r_results.loc[0, "n_obs"] = 99

        comparison = module.compare_results(python_results, r_results)

        self.assertEqual(comparison.loc[0, "status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
