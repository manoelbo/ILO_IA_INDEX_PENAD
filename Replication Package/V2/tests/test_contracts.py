from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "replication" / "contracts.py"


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location("contracts", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load contracts.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_wrong_semantic_table_is_rejected(tmp_path: Path) -> None:
    module = load_module()
    expected = pd.DataFrame(
        {
            "dimension": ["income", "income"],
            "group": ["low", "high"],
            "coefficient": [0.1, 0.2],
        }
    )
    contract = module.infer_csv_contract(
        expected,
        artifact_path="mechanisms/income_results.csv",
        source_id="models.heterogeneity:income",
    )
    wrong = pd.DataFrame(
        {
            "dimension": ["education", "education"],
            "group": ["secondary", "tertiary"],
            "coefficient": [0.1, 0.2],
        }
    )
    injected = tmp_path / "income_results.csv"
    wrong.to_csv(injected, index=False)

    with pytest.raises(module.SemanticContractError, match="dimension"):
        module.validate_artifact_semantics(injected, contract)


def test_signed_manifest_detects_reference_tampering(
    tmp_path: Path,
) -> None:
    module = load_module()
    results = tmp_path / "results"
    artifact = results / "mechanisms" / "hourly_wage_results.csv"
    artifact.parent.mkdir(parents=True)
    pd.DataFrame(
        {
            "outcome": ["ln_hourly_wage"],
            "coefficient": [-0.04],
        }
    ).to_csv(artifact, index=False)
    reference = results / "reference"

    module.freeze_reference(results, reference)
    module.validate_reference(reference)

    frozen = (
        reference
        / "artifacts"
        / "mechanisms"
        / "hourly_wage_results.csv"
    )
    frozen.write_text(
        "outcome,coefficient\nln_hourly_wage,-9.99\n",
        encoding="utf-8",
    )

    with pytest.raises(module.ManifestValidationError, match="SHA-256"):
        module.validate_reference(reference)


def test_every_current_reference_artifact_has_a_contract() -> None:
    module = load_module()
    reference = PACKAGE_ROOT / "results" / "reference"
    if not reference.is_dir():
        pytest.skip("Reference freeze is created by Task 28")

    summary = module.validate_reference(reference)

    assert summary["artifacts"] >= 80
    assert summary["all_sources_declared"]
    assert summary["all_category_domains_declared"]


def test_complementary_backing_data_names_real_producers() -> None:
    module = load_module()

    assert module.source_id_for(
        "rais/backing_data/rais_cross_replication_status.json"
    ) == "code.rais.r12_cross_replication"
    assert module.source_id_for(
        "pnadc/backing_data/pnadc_pretrend_cross_status.json"
    ) == "code.pnadc.pnadc_pretrend_cross_replication"
    assert module.source_id_for(
        "spatial/backing_data/spatial_r_model_comparison.csv"
    ) == "code.spatial.spatial_r_replication"


def test_group_outcome_forest_has_public_render_contracts() -> None:
    module = load_module()

    assert module.source_id_for(
        "caged/figures/figure_5_2_6_group_outcome_forest.png"
    ) == "code.render.phase8b_figures"
    assert module.source_id_for(
        "caged/backing_data/figure_5_2_6_group_outcome_forest.csv"
    ) == "code.render.phase8b_tables"
