from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _load_component_pipeline():
    path = PACKAGE_ROOT / "code" / "replication" / "component_pipeline.py"
    spec = importlib.util.spec_from_file_location("component_pipeline_spatial", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load component pipeline")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_spatial_r_replication_is_part_of_public_dag() -> None:
    module = _load_component_pipeline()
    command_text = "\n".join(
        " ".join(command) for command in module.REPRODUCE_COMMANDS["spatial"]
    )
    assert "spatial_r_replication.py" in command_text


def test_spatial_r_engine_never_estimates_real_treatment_or_family_f() -> None:
    script = (
        PACKAGE_ROOT / "code" / "spatial" / "spatial_replication.R"
    ).read_text(encoding="utf-8")
    assert "family_f_coefficients_created = 0L" in script
    assert "family_f_p_values_created = 0L" in script
    assert "treatment_coefficient_estimated = FALSE" in script
    assert "stage0_triple" not in script
    assert "bh_adjusted" not in script


def test_spatial_r_support_key_is_materialized_in_model_data() -> None:
    script = (
        PACKAGE_ROOT / "code" / "spatial" / "spatial_replication.R"
    ).read_text(encoding="utf-8")

    assert "support[, support_key :=" in script
    assert "support_key ~ 1 |" in script
    assert 'fixef.rm = "none"' in script
    assert script.count('fixef.rm = "singleton"') == 2
    assert "\n    key ~ 1 |" not in script


def test_exact_spatial_metadata_comparison_is_csv_dtype_independent() -> None:
    code_root = PACKAGE_ROOT / "code"
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from common.equality import same_exact_integer

    observed = same_exact_integer(
        pd.Series([-1, pd.NA, 1533998], dtype="object"),
        pd.Series([-1.0, float("nan"), 1533998.0]),
        field="reference_event_time",
    )

    assert observed.tolist() == [True, True, True]
    with pytest.raises(RuntimeError, match="non-integer R metadata"):
        same_exact_integer(
            pd.Series([10]),
            pd.Series([10.5]),
            field="n_obs",
        )
