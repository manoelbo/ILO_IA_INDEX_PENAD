from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import py7zr
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "ingest" / "parse.py"

BASE_COLUMNS = [
    "competênciamov",
    "região",
    "uf",
    "município",
    "seção",
    "subclasse",
    "saldomovimentação",
    "cbo2002ocupação",
    "categoria",
    "graudeinstrução",
    "idade",
    "horascontratuais",
    "raçacor",
    "sexo",
    "tipoempregador",
    "tipoestabelecimento",
    "tipomovimentação",
    "tipodedeficiência",
    "indtrabintermitente",
    "indtrabparcial",
    "salário",
    "tamestabjan",
    "indicadoraprendiz",
    "origemdainformação",
    "competênciadec",
    "indicadordeforadoprazo",
    "unidadesaláriocódigo",
    "valorsaláriofixo",
]


def load_parse_module():
    spec = importlib.util.spec_from_file_location("parse", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load parse.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_row(index: int) -> dict[str, str]:
    return {
        "competênciamov": "202101",
        "região": "3",
        "uf": "35",
        "município": "355030",
        "seção": "J",
        "subclasse": "6201501",
        "saldomovimentação": "1",
        "cbo2002ocupação": f"21240{index}",
        "categoria": "101",
        "graudeinstrução": "9",
        "idade": str(25 + index),
        "horascontratuais": "44,00",
        "raçacor": "1",
        "sexo": "3",
        "tipoempregador": "0",
        "tipoestabelecimento": "1",
        "tipomovimentação": "20",
        "tipodedeficiência": "0",
        "indtrabintermitente": "0",
        "indtrabparcial": "0",
        "salário": "2940,50",
        "tamestabjan": "5",
        "indicadoraprendiz": "0",
        "origemdainformação": "1",
        "competênciadec": "202101",
        "indicadordeforadoprazo": "0",
        "unidadesaláriocódigo": "5",
        "valorsaláriofixo": "2940,50",
    }


def build_archive(
    tmp_path: Path,
    archive_type: str,
    *,
    invalid_sex: bool = False,
    undocumented_employer: bool = False,
    undocumented_establishment: bool = False,
    omit_column: bool = False,
) -> Path:
    source_dir = tmp_path / "source"
    source_dir.mkdir(exist_ok=True)
    columns = list(BASE_COLUMNS)
    if archive_type == "EXC":
        insert_at = columns.index("competênciadec") + 1
        columns[insert_at:insert_at] = [
            "competênciaexc",
            "indicadordeexclusão",
        ]
    if omit_column:
        columns.pop()
    rows = [make_row(index) for index in range(5)]
    if archive_type == "EXC":
        for row in rows:
            row["competênciaexc"] = "202102"
            row["indicadordeexclusão"] = "1"
    if invalid_sex:
        rows[2]["sexo"] = "2"
    if undocumented_employer:
        rows[2]["tipoempregador"] = "1"
    if undocumented_establishment:
        rows[2]["tipoestabelecimento"] = "-1"

    text_path = source_dir / f"CAGED{archive_type}202101.txt"
    with text_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter=";",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    archive_path = tmp_path / f"CAGED{archive_type}202101.7z"
    with py7zr.SevenZipFile(archive_path, mode="w") as archive:
        archive.write(text_path, arcname=text_path.name)
    return archive_path


@pytest.mark.parametrize("archive_type", ["MOV", "FOR", "EXC"])
def test_parse_synthetic_five_row_archive(
    tmp_path: Path,
    archive_type: str,
) -> None:
    module = load_parse_module()
    archive_path = build_archive(tmp_path, archive_type)
    extraction_parent = tmp_path / "extract"
    extraction_parent.mkdir()

    frame = module.parse_archive(
        archive_path,
        temporary_parent=extraction_parent,
    )

    assert len(frame) == 5
    assert frame.loc[0, "competenciamov"] == "202101"
    assert frame.loc[0, "salario"] == pytest.approx(2940.50)
    assert frame.loc[0, "horascontratuais"] == pytest.approx(44.0)
    assert frame.loc[0, "valorsalariofixo"] == pytest.approx(2940.50)
    assert list(extraction_parent.iterdir()) == []
    if archive_type == "EXC":
        assert frame.loc[0, "competenciaexc"] == "202102"


def test_invalid_domain_code_fails_with_code_and_count(tmp_path: Path) -> None:
    module = load_parse_module()
    archive_path = build_archive(tmp_path, "MOV", invalid_sex=True)

    with pytest.raises(ValueError, match=r"sexo.*2.*1"):
        module.parse_archive(archive_path)


def test_undocumented_employer_code_is_preserved_without_remapping(
    tmp_path: Path,
) -> None:
    module = load_parse_module()
    archive_path = build_archive(
        tmp_path,
        "MOV",
        undocumented_employer=True,
    )

    frame = module.parse_archive(archive_path)

    assert frame.loc[2, "tipoempregador"] == "1"


def test_undocumented_establishment_code_is_preserved_without_remapping(
    tmp_path: Path,
) -> None:
    module = load_parse_module()
    archive_path = build_archive(
        tmp_path,
        "MOV",
        undocumented_establishment=True,
    )

    frame = module.parse_archive(archive_path)

    assert frame.loc[2, "tipoestabelecimento"] == "-1"


def test_invalid_column_count_fails_fast(tmp_path: Path) -> None:
    module = load_parse_module()
    archive_path = build_archive(tmp_path, "FOR", omit_column=True)

    with pytest.raises(ValueError, match=r"28 or 30"):
        module.parse_archive(archive_path)
