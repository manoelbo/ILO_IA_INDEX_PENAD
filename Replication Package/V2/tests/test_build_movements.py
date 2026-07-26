from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
INGEST_ROOT = PACKAGE_ROOT / "code" / "ingest"
MODULE_PATH = INGEST_ROOT / "build_movements.py"
if str(INGEST_ROOT) not in sys.path:
    sys.path.insert(0, str(INGEST_ROOT))

from parse import BASE_COLUMNS, EXCLUSION_COLUMNS


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_movements", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load build_movements.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized_frame(
    competencia: str,
    *,
    exclusion: bool = False,
) -> pd.DataFrame:
    row: dict[str, object] = {
        "competenciamov": competencia,
        "regiao": "3",
        "uf": "35",
        "municipio": "355030",
        "secao": "J",
        "subclasse": "6201501",
        "saldomovimentacao": 1,
        "cbo2002ocupacao": "212405",
        "categoria": "101",
        "graudeinstrucao": "9",
        "idade": 30,
        "horascontratuais": 44.0,
        "racacor": "1",
        "sexo": "3",
        "tipoempregador": "0",
        "tipoestabelecimento": "1",
        "tipomovimentacao": "20",
        "tipodedeficiencia": "0",
        "indtrabintermitente": "0",
        "indtrabparcial": "0",
        "salario": 2940.5,
        "tamestabjan": "5",
        "indicadoraprendiz": "0",
        "origemdainformacao": "1",
        "competenciadec": "202101",
        "indicadordeforadoprazo": "0",
        "unidadesalariocodigo": "5",
        "valorsalariofixo": 2940.5,
    }
    if exclusion:
        row["competenciaexc"] = "202103"
        row["indicadordeexclusao"] = "1"
        columns = EXCLUSION_COLUMNS
    else:
        columns = BASE_COLUMNS
    return pd.DataFrame([row], columns=columns)


def record(competencia: str, archive_type: str) -> dict[str, object]:
    return {
        "competencia": competencia,
        "tipo": archive_type,
        "url": (
            "ftp://ftp.mtps.gov.br/example/"
            f"CAGED{archive_type}{competencia}.7z"
        ),
        "bytes": 1,
        "data_modificacao_ftp": "2026-07-25T12:00:00Z",
    }


def test_build_uses_fact_month_and_signed_exclusion_weights(
    tmp_path: Path,
) -> None:
    module = load_build_module()
    records = [
        record("202101", "MOV"),
        record("202102", "FOR"),
        record("202101", "EXC"),
    ]
    frames = {
        "CAGEDMOV202101.7z": normalized_frame("202101"),
        "CAGEDFOR202102.7z": normalized_frame("202101"),
        "CAGEDEXC202101.7z": normalized_frame("202101", exclusion=True),
    }
    vintage_dir = tmp_path / "vintage"
    vintage_dir.mkdir()
    for filename in frames:
        (vintage_dir / filename).write_bytes(b"x")

    def fake_parser(path: Path) -> pd.DataFrame:
        return frames[path.name].copy()

    output_dir = tmp_path / "movimentacoes"
    reconciliation_path = tmp_path / "origem_por_competencia.csv"
    module.build_movements(
        records,
        vintage_dir,
        output_dir,
        reconciliation_path,
        parser=fake_parser,
    )

    partition = pd.read_parquet(
        output_dir / "competenciamov=202101" / "part.parquet"
    )
    assert partition["origem"].tolist() == ["MOV", "FOR", "EXC"]
    assert partition["competencia_arquivo"].tolist() == [
        "202101",
        "202102",
        "202101",
    ]
    assert partition["peso"].tolist() == [1, 1, -1]

    reconciliation = pd.read_csv(
        reconciliation_path,
        dtype={"competenciamov": str},
    )
    assert reconciliation.loc[0].to_dict() == {
        "competenciamov": "202101",
        "linhas_mov": 1,
        "linhas_for": 1,
        "linhas_exc": 1,
        "linhas_exc_mesmo_mes": 1,
        "liquido": 1,
    }


def test_temporal_contract_rejects_for_in_file_month() -> None:
    module = load_build_module()
    frame = normalized_frame("202102")

    with pytest.raises(ValueError, match="FOR.*strictly earlier"):
        module.prepare_archive_frame(frame, "FOR", "202102")


def test_temporal_contract_accepts_same_month_exclusion() -> None:
    module = load_build_module()
    frame = normalized_frame("202102", exclusion=True)

    prepared = module.prepare_archive_frame(frame, "EXC", "202102")

    assert prepared.loc[0, "competenciamov"] == "202102"
    assert prepared.loc[0, "peso"] == -1


def test_temporal_contract_rejects_future_exclusion() -> None:
    module = load_build_module()
    frame = normalized_frame("202103", exclusion=True)

    with pytest.raises(ValueError, match="EXC.*later than"):
        module.prepare_archive_frame(frame, "EXC", "202102")
