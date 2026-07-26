#!/usr/bin/env python3
"""Parse and validate one official Novo CAGED archive."""

from __future__ import annotations

import argparse
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd
import py7zr


BASE_COLUMNS = (
    "competenciamov",
    "regiao",
    "uf",
    "municipio",
    "secao",
    "subclasse",
    "saldomovimentacao",
    "cbo2002ocupacao",
    "categoria",
    "graudeinstrucao",
    "idade",
    "horascontratuais",
    "racacor",
    "sexo",
    "tipoempregador",
    "tipoestabelecimento",
    "tipomovimentacao",
    "tipodedeficiencia",
    "indtrabintermitente",
    "indtrabparcial",
    "salario",
    "tamestabjan",
    "indicadoraprendiz",
    "origemdainformacao",
    "competenciadec",
    "indicadordeforadoprazo",
    "unidadesalariocodigo",
    "valorsalariofixo",
)
EXCLUSION_COLUMNS = (
    *BASE_COLUMNS[:25],
    "competenciaexc",
    "indicadordeexclusao",
    *BASE_COLUMNS[25:],
)
DOMAIN_VALUES = {
    "categoria": {
        "101",
        "102",
        "103",
        "104",
        "105",
        "106",
        "107",
        "108",
        "111",
        "999",
    },
    "graudeinstrucao": {
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "80",
        "99",
    },
    "racacor": {"1", "2", "3", "4", "5", "6", "9"},
    "sexo": {"1", "3", "9"},
    # Code 1 is present in the frozen official files but absent from the
    # frozen layout. It is preserved as an undocumented category and must not
    # be remapped to any documented employer type.
    "tipoempregador": {"0", "1", "2", "9"},
    "tipoestabelecimento": {"1", "3", "4", "5", "9"},
    "tipomovimentacao": {
        "10",
        "20",
        "25",
        "31",
        "32",
        "33",
        "35",
        "40",
        "43",
        "45",
        "50",
        "60",
        "70",
        "80",
        "90",
        "97",
        "98",
        "99",
    },
    "tipodedeficiencia": {"0", "1", "2", "3", "4", "5", "6", "9"},
    "indtrabintermitente": {"0", "1", "9"},
    "indtrabparcial": {"0", "1", "9"},
    "tamestabjan": {
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "90",
        "97",
        "98",
        "99",
    },
    "indicadoraprendiz": {"0", "1", "9"},
    "origemdainformacao": {"1", "2", "3"},
    "indicadordeexclusao": {"0", "1"},
    "indicadordeforadoprazo": {"0", "1"},
    "unidadesalariocodigo": {
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "99",
    },
}
DECIMAL_COLUMNS = ("salario", "valorsalariofixo", "horascontratuais")
INTEGER_COLUMNS = ("saldomovimentacao", "idade")
ARCHIVE_PATTERN = re.compile(r"^CAGED(MOV|FOR|EXC)\d{6}\.7z$")


def normalize_column_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name.strip().lower())
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]", "", without_accents)


def archive_type(archive_path: Path) -> str:
    match = ARCHIVE_PATTERN.fullmatch(archive_path.name)
    if not match:
        raise ValueError(
            "Archive filename must match CAGED{MOV|FOR|EXC}AAAAMM.7z: "
            f"{archive_path.name}"
        )
    return match.group(1)


def validate_columns(frame: pd.DataFrame, archive_kind: str) -> None:
    if len(frame.columns) not in {28, 30}:
        raise ValueError(
            "Novo CAGED files must contain exactly 28 or 30 columns; "
            f"found {len(frame.columns)}"
        )
    expected = EXCLUSION_COLUMNS if archive_kind == "EXC" else BASE_COLUMNS
    if tuple(frame.columns) != expected:
        missing = sorted(set(expected) - set(frame.columns))
        unexpected = sorted(set(frame.columns) - set(expected))
        raise ValueError(
            f"Unexpected {archive_kind} schema; missing={missing}, "
            f"unexpected={unexpected}"
        )


def validate_domains(frame: pd.DataFrame) -> None:
    for column, allowed_values in DOMAIN_VALUES.items():
        if column not in frame.columns:
            continue
        values = frame[column].astype(str).str.strip()
        invalid = values[(values != "") & ~values.isin(allowed_values)]
        if invalid.empty:
            continue
        counts = invalid.value_counts().sort_index()
        detail = ", ".join(f"{code} ({count})" for code, count in counts.items())
        raise ValueError(f"Invalid domain code(s) in {column}: {detail}")


def _convert_decimal(series: pd.Series, column: str) -> pd.Series:
    cleaned = series.astype(str).str.strip().str.replace(",", ".", regex=False)
    cleaned = cleaned.replace("", pd.NA)
    try:
        return pd.to_numeric(cleaned, errors="raise")
    except ValueError as error:
        raise ValueError(f"Invalid decimal value in {column}: {error}") from error


def _convert_integer(series: pd.Series, column: str) -> pd.Series:
    cleaned = series.astype(str).str.strip().replace("", pd.NA)
    try:
        numeric = pd.to_numeric(cleaned, errors="raise")
    except ValueError as error:
        raise ValueError(f"Invalid integer value in {column}: {error}") from error
    non_integer = numeric.dropna().mod(1).ne(0)
    if non_integer.any():
        raise ValueError(f"Non-integer value found in {column}")
    return numeric.astype("Int64")


def normalize_frame(frame: pd.DataFrame, archive_kind: str) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [
        normalize_column_name(str(column)) for column in normalized.columns
    ]
    validate_columns(normalized, archive_kind)
    for column in normalized.columns:
        normalized[column] = normalized[column].astype(str).str.strip()
    validate_domains(normalized)
    for column in DECIMAL_COLUMNS:
        normalized[column] = _convert_decimal(normalized[column], column)
    for column in INTEGER_COLUMNS:
        normalized[column] = _convert_integer(normalized[column], column)
    return normalized


def _validated_member_name(archive: py7zr.SevenZipFile) -> str:
    members = archive.getnames()
    if len(members) != 1:
        raise ValueError(
            f"Novo CAGED archive must contain exactly one file; found {members}"
        )
    member = members[0]
    member_path = Path(member)
    if (
        member_path.name != member
        or member_path.suffix.lower() != ".txt"
        or member_path.is_absolute()
    ):
        raise ValueError(f"Unsafe or unexpected archive member: {member}")
    return member


def parse_archive(
    archive_path: Path | str,
    *,
    temporary_parent: Path | None = None,
) -> pd.DataFrame:
    """Extract, parse, validate, and clean up one official archive."""
    resolved_archive = Path(archive_path)
    kind = archive_type(resolved_archive)
    if not resolved_archive.is_file():
        raise FileNotFoundError(resolved_archive)

    with tempfile.TemporaryDirectory(
        prefix="caged-v2-",
        dir=temporary_parent,
    ) as temporary_directory:
        extraction_root = Path(temporary_directory)
        with py7zr.SevenZipFile(resolved_archive, mode="r") as archive:
            member = _validated_member_name(archive)
            archive.extractall(path=extraction_root)
        text_path = extraction_root / member
        frame = pd.read_csv(
            text_path,
            sep=";",
            encoding="utf-8",
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        )
        return normalize_frame(frame, kind)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse and validate official Novo CAGED archives."
    )
    parser.add_argument("archives", nargs="+", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for archive_path in args.archives:
        frame = parse_archive(archive_path)
        print(
            f"{archive_path.name}: rows={len(frame)} columns={len(frame.columns)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
