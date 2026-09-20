from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = PACKAGE_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from render.complementary import render_component
from replication.component_pipeline import (
    REPRODUCE_COMMANDS,
    SPATIAL_OFFICIAL_VINTAGE_FILES,
    _stage_runtime,
    _spatial_vintage_reuse_allowed,
    validate_component_results,
)


def reference_backing(component: str) -> Path:
    return (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / component
        / "backing_data"
    )


def test_component_reproduction_sequences_close_their_public_outputs() -> None:
    assert REPRODUCE_COMMANDS["rais"][-4:] == (
        ("r10_sensitivities.py", "replay-diagnostic"),
        ("r10_sensitivities.py", "estimate"),
        ("r11_proxy_validation.py",),
        ("r12_cross_replication.py",),
    )
    assert REPRODUCE_COMMANDS["pnadc"][-1] == (
        "pnadc_cross_replication.py",
    )


def test_rais_offline_bundle_carries_the_frozen_acquisition_gate() -> None:
    contract = (
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "rais"
        / "contracts"
        / "rais_stage0_status.json"
    )
    payload = json.loads(contract.read_text(encoding="utf-8"))

    assert payload["gate_r_g1"] == "pass"
    assert payload["gate_r_g2"] == "pass"
    assert payload["treatment_coefficient_estimated"] is False


def test_spatial_full_mode_reuses_only_a_complete_separate_raw_vintage(
    tmp_path: Path,
) -> None:
    vintage = tmp_path / "spatial"
    vintage.mkdir()
    (vintage / "manifest.json").write_text("{}\n", encoding="utf-8")

    try:
        _spatial_vintage_reuse_allowed(vintage)
    except RuntimeError as error:
        assert "incomplete" in str(error)
    else:
        raise AssertionError("Incomplete spatial raw vintage was accepted")

    for name in SPATIAL_OFFICIAL_VINTAGE_FILES:
        (vintage / name).write_text("registered source\n", encoding="utf-8")
    assert _spatial_vintage_reuse_allowed(vintage)


def test_component_runtime_uses_collision_free_python_packages(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    contracts = bundle / "derived" / "rais" / "contracts"
    contracts.mkdir(parents=True)
    (contracts / "receipt.json").write_text("{}\n", encoding="utf-8")
    raw = tmp_path / "raw"
    raw.mkdir()

    runtime, front, reuse = _stage_runtime(
        "rais",
        data_dir=bundle,
        raw_dir=raw,
        mode="reproduce",
        work_dir=tmp_path / "work",
    )

    assert runtime.name == "V2"
    assert (front / "v2_rais" / "part1.py").is_file()
    assert not (front / "rais").exists()
    assert reuse is False


def test_pnadc_full_runtime_carries_the_frozen_part1_gate(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    contracts = bundle / "derived" / "pnadc" / "contracts"
    contracts.mkdir(parents=True)
    gate = {
        "gate": "P-B1",
        "gate_status": "open",
        "treatment_coefficients_computed": False,
    }
    (contracts / "pnadc_part1_status.json").write_text(
        json.dumps(gate) + "\n",
        encoding="utf-8",
    )
    raw = tmp_path / "raw"
    raw.mkdir()

    _, front, _ = _stage_runtime(
        "pnadc",
        data_dir=bundle,
        raw_dir=raw,
        mode="full",
        work_dir=tmp_path / "work",
    )

    staged = front / "results" / "pnadc_part1_status.json"
    assert json.loads(staged.read_text(encoding="utf-8")) == gate


def test_rais_renderer_writes_table_d_1_and_b_1(tmp_path: Path) -> None:
    output = tmp_path / "rais"
    render_component(
        "rais",
        results_dir=reference_backing("rais"),
        output_dir=output,
    )

    table = pd.read_csv(output / "tables" / "table_d_1_rais.csv")
    pretrends = pd.read_csv(output / "tables" / "table_b_1_rais_pretrends.csv")
    assert len(table) == 3
    assert len(pretrends) == 3
    assert set(table["family_id"]) == {"D"}


def test_pnadc_renderer_writes_table_d_2_and_b_2(tmp_path: Path) -> None:
    output = tmp_path / "pnadc"
    render_component(
        "pnadc",
        results_dir=reference_backing("pnadc"),
        output_dir=output,
    )

    table = pd.read_csv(output / "tables" / "table_d_2_pnadc.csv")
    pretrends = pd.read_csv(output / "tables" / "table_b_2_pnadc_pretrends.csv")
    assert len(table) == 6
    assert len(pretrends) == 12
    assert set(table["family_id"]) == {"E"}


def test_spatial_renderer_stops_at_support_without_treatment_results(
    tmp_path: Path,
) -> None:
    output = tmp_path / "spatial"
    render_component(
        "spatial",
        results_dir=reference_backing("spatial"),
        output_dir=output,
    )

    placebo = pd.read_csv(output / "tables" / "table_b_3_spatial_placebo.csv")
    support = pd.read_csv(output / "tables" / "table_b_4_spatial_support.csv")
    family = pd.read_csv(output / "backing_data" / "family_f_declaration.csv")
    assert len(placebo) == 4
    assert len(support) == 3
    assert len(family) == 12
    assert family["coefficient"].isna().all()
    assert family["p_value"].isna().all()
    assert family["bh_adjusted_p_value"].isna().all()
    public_names = {path.name.lower() for path in output.rglob("*") if path.is_file()}
    assert not any("ddd" in name for name in public_names)


def test_public_component_validation_preserves_scientific_limits() -> None:
    rais = validate_component_results(
        "rais",
        reference_backing("rais"),
    )
    pnadc = validate_component_results(
        "pnadc",
        reference_backing("pnadc"),
    )
    spatial = validate_component_results(
        "spatial",
        reference_backing("spatial"),
    )

    assert rais["family"] == "D"
    assert rais["cross_language_status"] == "pass"
    assert rais["causal_effect_claim_authorized"] is False
    assert pnadc["family"] == "E"
    assert pnadc["pretrend_failures"] == 12
    assert pnadc["causal_effect_claim_authorized"] is False
    assert spatial["family"] == "F"
    assert spatial["declared_slots"] == 12
    assert spatial["estimated_coefficients"] == 0
    assert spatial["support_gate_open"] is False
