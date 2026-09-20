from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "panel" / "build_panel.py"


def load_panel_module():
    spec = importlib.util.spec_from_file_location("build_panel", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load build_panel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_ipca_frame_rebases_monthly_variation() -> None:
    module = load_panel_module()
    payload = json.dumps(
        [
            {"data": "01/11/2024", "valor": "1.00"},
            {"data": "01/12/2024", "valor": "2.00"},
            {"data": "01/01/2025", "valor": "3.00"},
        ]
    ).encode()

    frame = module.build_ipca_frame(
        payload,
        expected_start="202411",
        expected_end="202501",
        base_period="202412",
    )

    assert frame["periodo_num"].tolist() == [202411, 202412, 202501]
    assert frame.loc[1, "indice"] == pytest.approx(100.0)
    assert frame.loc[0, "indice"] == pytest.approx(100 / 1.02)
    assert frame.loc[2, "indice"] == pytest.approx(103.0)


def test_registered_source_is_reused_and_hash_validated(
    tmp_path: Path,
) -> None:
    module = load_panel_module()
    payload = b"frozen official source"
    raw_path = tmp_path / "vintage" / "source.bin"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_bytes(payload)
    manifest = {
        "source.bin": {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "url": "https://example.test/source.bin",
        }
    }

    observed, entry, reused = module._load_or_fetch_registered_source(
        raw_path=raw_path,
        manifest=manifest,
        manifest_key="source.bin",
        expected_url="https://example.test/source.bin",
        fetch=lambda _url: pytest.fail("registered source must not be fetched"),
    )

    assert observed == payload
    assert entry == manifest["source.bin"]
    assert reused is True

    raw_path.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="Registered source mismatch"):
        module._load_or_fetch_registered_source(
            raw_path=raw_path,
            manifest=manifest,
            manifest_key="source.bin",
            expected_url="https://example.test/source.bin",
            fetch=lambda _url: pytest.fail("tampering must not trigger fetch"),
        )


def test_missing_registered_source_is_downloaded_once(tmp_path: Path) -> None:
    module = load_panel_module()
    payload = b"frozen official source"
    raw_path = tmp_path / "vintage" / "source.bin"
    calls: list[str] = []
    manifest = {
        "source.bin": {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "url": "https://example.test/source.bin",
        }
    }

    observed, _entry, reused = module._load_or_fetch_registered_source(
        raw_path=raw_path,
        manifest=manifest,
        manifest_key="source.bin",
        expected_url="https://example.test/source.bin",
        fetch=lambda url: calls.append(url) or payload,
    )

    assert observed == payload
    assert raw_path.read_bytes() == payload
    assert calls == ["https://example.test/source.bin"]
    assert reused is False


def test_national_panel_preserves_zero_flow_missingness(
    tmp_path: Path,
) -> None:
    module = load_panel_module()
    partition = tmp_path / "movements" / "competenciamov=202101"
    partition.mkdir(parents=True)
    movements = pd.DataFrame(
        [
            ["111105", 1, 1, 1000.0, 20, "3", "9", "2", "A", "111301"],
            ["111105", 1, -1, 1000.0, 20, "3", "9", "2", "A", "111301"],
            ["111105", -1, 1, 2000.0, 40, "1", "7", "1", "A", "111301"],
            ["222205", 1, 1, 3000.0, 30, "3", "10", "3", "C", "1011201"],
            ["222205", -1, 1, 4000.0, 35, "1", "8", "1", "C", "1011201"],
            ["333305", 1, 1, 2500.0, 28, "1", "8", "1", "Z", "9999999"],
            ["000000", 1, 1, 5000.0, 30, "1", "9", "1", "A", "111301"],
            ["222205", 1, 1, 0.0, 30, "1", "9", "1", "C", "1011201"],
            ["222205", 1, 1, 5000.0, 10, "1", "9", "1", "C", "1011201"],
        ],
        columns=[
            "cbo2002ocupacao",
            "saldomovimentacao",
            "peso",
            "salario",
            "idade",
            "sexo",
            "graudeinstrucao",
            "racacor",
            "secao",
            "subclasse",
        ],
    )
    movements.to_parquet(partition / "part.parquet", index=False)
    ipca = pd.DataFrame(
        {
            "periodo_num": [202101],
            "indice": [80.0],
        }
    )
    classification = pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222"],
            "cbo_ilo_gradient": [
                "Not Exposed",
                "Exposed: Gradient 2",
            ],
        }
    )

    panel, metrics = module.build_national_panel(
        tmp_path / "movements" / "competenciamov=*" / "part.parquet",
        ipca,
        classification,
        start_period=202101,
        end_period=202101,
        scratch_parent=tmp_path,
    )

    first = panel.set_index("cbo_4d").loc["1111"]
    assert first["admissoes"] == 0
    assert np.isnan(first["salario_medio_adm"])
    assert np.isnan(first["idade_media_adm"])
    assert first["desligamentos"] == 1
    assert first["salario_medio_desl"] == pytest.approx(2000.0)
    assert (
        panel.set_index("cbo_4d").loc["3333", "cbo_ilo_gradient"]
        == "No score"
    )
    assert metrics["invalid_rows_rejected"] == 3
    assert metrics["new_unclassified_cbo_families"] == ["3333"]
    module.validate_national_panel(panel)

    national_path = tmp_path / "national.parquet"
    panel.to_parquet(national_path, index=False)
    cnae = pd.DataFrame(
        {
            "divisao": ["01", "10"],
            "secao": ["A", "C"],
            "divisao_descricao": ["Agriculture", "Food manufacturing"],
        }
    )
    sector_path = tmp_path / "sector.parquet"
    coexistence_path = tmp_path / "coexistence.csv"
    sector_metrics = module.build_sector_panel(
        tmp_path / "movements" / "competenciamov=*" / "part.parquet",
        ipca,
        classification,
        cnae,
        national_path,
        sector_path,
        coexistence_path,
        start_period=202101,
        end_period=202101,
        scratch_parent=tmp_path,
    )
    sector = pd.read_parquet(sector_path)

    assert sector_metrics["national_count_divergences"] == 0
    assert sector_metrics["undocumented_cnae_signed_weight"] == 1
    assert set(sector["divisao"]) == {"01", "10", "ZZ"}
    assert not sector.duplicated(
        ["cbo_4d", "subclasse", "periodo_num"]
    ).any()


def test_panel_validation_rejects_wage_in_zero_flow_cell() -> None:
    module = load_panel_module()
    invalid = pd.DataFrame(
        {
            "cbo_4d": ["1111"],
            "periodo_num": [202101],
            "admissoes": [0],
            "desligamentos": [1],
            "salario_medio_adm": [1104.7868],
            "salario_medio_desl": [2000.0],
            "idade_media_adm": [np.nan],
            "idade_media_desl": [40.0],
            "pct_mulher_adm": [np.nan],
            "pct_mulher_desl": [0.0],
            "pct_superior_adm": [np.nan],
            "pct_superior_desl": [0.0],
            "pct_negra_adm": [np.nan],
            "pct_negra_desl": [0.0],
        }
    )

    with pytest.raises(RuntimeError, match="zero-flow admission"):
        module.validate_national_panel(invalid)


def test_frozen_cnae_dictionary_has_official_division_structure() -> None:
    module = load_panel_module()

    divisions = module.load_cnae_divisions(module.DEFAULT_CNAE_DICTIONARY)

    assert len(divisions) == 87
    assert divisions["secao"].nunique() == 21
    assert divisions["divisao"].nunique() == 87


def test_sector_support_serialization_matches_the_signed_reference(
    tmp_path: Path,
) -> None:
    module = load_panel_module()
    reference = (
        PACKAGE_ROOT
        / "results"
        / "reference"
        / "artifacts"
        / "caged"
        / "reconciliation"
        / "painel_cbo_cnae_support.json"
    )
    payload = json.loads(reference.read_text(encoding="utf-8"))
    reversed_payload = dict(reversed(list(payload.items())))
    observed = tmp_path / reference.name

    module.write_sector_support(reversed_payload, observed)

    assert observed.read_bytes() == reference.read_bytes()
