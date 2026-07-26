from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPORTER = (
    PACKAGE_ROOT / "code" / "replication" / "export_cross_replication.py"
)
R_SCRIPT = PACKAGE_ROOT / "R" / "cross_replication.R"


def load_exporter():
    spec = importlib.util.spec_from_file_location(
        "export_cross_replication",
        EXPORTER,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load cross-replication exporter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cross_replication_input_is_the_exact_principal_sample() -> None:
    module = load_exporter()
    panel = pd.read_parquet(module.DEFAULT_PANEL)

    sample = module.build_cross_replication_input(panel)

    assert len(sample) == 22_049
    assert sample["cbo_4d"].nunique() == 341
    assert sample["periodo"].nunique() == 65
    assert set(sample["treatment"].unique()) == {0, 1}
    assert sample["post_treat"].equals(
        sample["post"] * sample["treatment"]
    )


def test_r_cross_replication_matches_python_to_six_decimals() -> None:
    subprocess.run(
        [sys.executable, str(EXPORTER)],
        cwd=PACKAGE_ROOT,
        check=True,
    )
    subprocess.run(
        ["Rscript", str(R_SCRIPT)],
        cwd=PACKAGE_ROOT,
        check=True,
    )
    status_path = (
        PACKAGE_ROOT
        / "results"
        / "replication"
        / "cross_replication_status.json"
    )
    status = json.loads(status_path.read_text(encoding="utf-8"))

    assert status["models"] == 5
    assert status["same_n_and_clusters"]
    assert status["six_decimal_agreement"]
    assert status["max_coefficient_absolute_difference"] < 5e-7
    assert status["max_standard_error_absolute_difference"] < 5e-7
