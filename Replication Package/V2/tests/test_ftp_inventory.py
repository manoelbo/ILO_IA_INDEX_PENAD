from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "ingest" / "ftp_inventory.py"


def load_inventory_module():
    spec = importlib.util.spec_from_file_location("ftp_inventory", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load ftp_inventory.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_record(competencia: str, tipo: str) -> dict[str, object]:
    return {
        "competencia": competencia,
        "tipo": tipo,
        "url": (
            "ftp://ftp.mtps.gov.br/pdet/microdados/"
            f"NOVO%20CAGED/{competencia[:4]}/{competencia}/"
            f"CAGED{tipo}{competencia}.7z"
        ),
        "bytes": 123,
        "data_modificacao_ftp": "2026-07-25T12:00:00Z",
    }


def test_fixed_competencies_end_at_may_2026_without_gaps() -> None:
    module = load_inventory_module()

    competencies = module.fixed_competencies()

    assert len(competencies) == 65
    assert competencies[0] == "202101"
    assert competencies[-1] == "202605"
    assert "202606" not in competencies


def test_validate_inventory_requires_three_archives_per_competency() -> None:
    module = load_inventory_module()
    records = [
        make_record(competencia, tipo)
        for competencia in module.fixed_competencies()
        for tipo in ("MOV", "FOR", "EXC")
    ]

    module.validate_inventory(records)

    records.pop()
    with pytest.raises(ValueError, match="195"):
        module.validate_inventory(records)


def test_validate_inventory_rejects_unexpected_filename() -> None:
    module = load_inventory_module()
    records = [
        make_record(competencia, tipo)
        for competencia in module.fixed_competencies()
        for tipo in ("MOV", "FOR", "EXC")
    ]
    records[0]["url"] = str(records[0]["url"]).replace(
        "CAGEDMOV202101.7z",
        "unexpected.7z",
    )

    with pytest.raises(ValueError, match="filename"):
        module.validate_inventory(records)


def test_write_inventory_uses_lf_line_endings(tmp_path: Path) -> None:
    module = load_inventory_module()
    records = [
        make_record(competencia, tipo)
        for competencia in module.fixed_competencies()
        for tipo in ("MOV", "FOR", "EXC")
    ]
    output_path = tmp_path / "ftp_inventory.csv"

    module.write_inventory(records, output_path)

    assert b"\r\n" not in output_path.read_bytes()
