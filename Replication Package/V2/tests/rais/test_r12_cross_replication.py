from __future__ import annotations

import importlib
import json
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_RESULTS = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "rais" / "backing_data"
)


def load_module():
    return importlib.import_module("v2_rais.r12_cross_replication")


def test_export_contains_all_three_exact_principal_panel_cells() -> None:
    module = load_module()
    annual = pd.read_parquet(
        PACKAGE_ROOT / "data" / "derived" / "rais" / "painel_rais_anual.parquet"
    )
    rotation = pd.read_parquet(
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "rais"
        / "painel_rais_rotatividade.parquet"
    )

    exported = module.build_cross_replication_input(annual, rotation)
    counts = exported.groupby("outcome").size().to_dict()

    assert counts == {
        "estoque_3112": 2_041,
        "ln_taxa_rotatividade": 1_360,
        "ln_tempo_emprego_medio": 2_041,
    }
    assert exported["model_id"].nunique() == 3
    assert exported.groupby("outcome")["cbo_4d"].nunique().eq(341).all()
    assert exported.duplicated(["model_id", "cbo_4d", "ano"]).sum() == 0
    assert set(exported["estimator"]) == {"ols", "ppml"}


def test_comparison_requires_six_decimal_coefficient_and_se_agreement() -> None:
    module = load_module()
    python_results = pd.DataFrame(
        {
            "outcome": ["estoque_3112", "ln_taxa_rotatividade"],
            "estimator": ["ppml", "ols"],
            "coefficient": [-0.04, -0.02],
            "standard_error": [0.01, 0.03],
            "n_obs": [100, 80],
            "minimum_clusters": [20, 20],
        }
    )
    r_results = pd.DataFrame(
        {
            "outcome": ["estoque_3112", "ln_taxa_rotatividade"],
            "estimator": ["ppml", "ols"],
            "coefficient": [-0.04000001, -0.02000001],
            "standard_error": [0.01000001, 0.03000001],
            "n_obs": [100, 80],
            "n_clusters": [20, 20],
        }
    )

    comparison, status = module.compare_cross_replication(
        python_results,
        r_results,
    )

    assert len(comparison) == 2
    assert status["same_n_and_clusters"]
    assert status["six_decimal_agreement"]
    assert status["models"] == 2


def test_independent_r_replication_matches_all_principal_models() -> None:
    status = json.loads(
        (REFERENCE_RESULTS / "rais_cross_replication_status.json").read_text(
            encoding="utf-8"
        )
    )

    assert status["models"] == 3
    assert status["same_n_and_clusters"]
    assert status["six_decimal_agreement"]
    assert status["max_coefficient_absolute_difference"] < 5e-7
    assert status["max_standard_error_absolute_difference"] < 5e-7
    assert status["p_values_created"] == 0
    assert status["status"] == "pass"


def test_r_result_replacement_is_atomic_without_delete_window() -> None:
    script = (
        PACKAGE_ROOT / "code" / "rais" / "r12_cross_replication.R"
    ).read_text(encoding="utf-8")

    assert 'paste0(output_path, ".tmp")' in script
    assert "file.rename(temporary_path, output_path)" in script
    assert "file.remove(output_path)" not in script
