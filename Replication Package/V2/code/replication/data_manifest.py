#!/usr/bin/env python3
"""Build or validate the frozen analytical-bundle manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Sequence


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = PACKAGE_ROOT / "data"
DEFAULT_MANIFEST = PACKAGE_ROOT / "config" / "analytical_bundle_manifest.csv"
FIELDS = (
    "path",
    "component",
    "role",
    "source_id",
    "bytes",
    "schema",
    "encoding",
    "sha256",
)
EXCLUDED_NAMES = {".DS_Store", ".gitignore", ".gitattributes", ".gitkeep"}
EXCLUDED_SUFFIXES = {".md"}
EXCLUDED_SPATIAL_VINTAGE = {
    "Acessos_Banda_Larga_Fixa_2021.csv",
    "Acessos_Banda_Larga_Fixa_2022.csv",
    "Acessos_Banda_Larga_Fixa_Total.csv",
    "Densidade_Banda_Larga_Fixa.csv",
    "ibge_municipios_censo2022.parquet",
}


def _csv_encoding(path: Path) -> str:
    """Return the first deterministic decoding that accepts the CSV."""
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open(encoding=encoding, newline="") as handle:
                for _ in handle:
                    pass
        except UnicodeDecodeError:
            continue
        return encoding
    raise RuntimeError(f"Cannot determine CSV encoding for {path}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_bundle_files(bundle_dir: Path) -> list[Path]:
    files = []
    for path in bundle_dir.rglob("*"):
        if (
            not path.is_file()
            or path.name in EXCLUDED_NAMES
            or path.suffix.lower() in EXCLUDED_SUFFIXES
        ):
            continue
        if path.suffix.lower() == ".7z":
            continue
        relative = path.relative_to(bundle_dir)
        if (
            relative.parts[:3] == ("derived", "spatial", "vintage")
            and path.name in EXCLUDED_SPATIAL_VINTAGE
        ):
            continue
        files.append(path)
    return sorted(files)


def _schema(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix == ".parquet":
            import pyarrow.parquet as pq

            schema = pq.read_schema(path)
            return json.dumps(
                [{"name": field.name, "type": str(field.type)} for field in schema],
                separators=(",", ":"),
            )
        if suffix == ".csv":
            with path.open(encoding=_csv_encoding(path), newline="") as handle:
                header = next(csv.reader(handle))
            return json.dumps(header, separators=(",", ":"))
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                description: Any = {"top_level_keys": sorted(payload)}
            elif isinstance(payload, list):
                description = {
                    "container": "array",
                    "first_record_keys": (
                        sorted(payload[0])
                        if payload and isinstance(payload[0], dict)
                        else []
                    ),
                }
            else:
                description = {"container": type(payload).__name__}
            return json.dumps(description, separators=(",", ":"))
        if suffix in {".xlsx", ".xls"}:
            import openpyxl

            workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
            return json.dumps(
                {"sheets": workbook.sheetnames},
                separators=(",", ":"),
            )
        if suffix == ".gpkg":
            import pyogrio

            return json.dumps(
                {"layers": pyogrio.list_layers(path)[:, 0].tolist()},
                separators=(",", ":"),
            )
        if suffix == ".zip":
            import zipfile

            with zipfile.ZipFile(path) as archive:
                members = sorted(archive.namelist())
            return json.dumps({"members": members}, separators=(",", ":"))
    except Exception as error:  # noqa: BLE001
        raise RuntimeError(f"Cannot inspect schema for {path}: {error}") from error
    return json.dumps({"media_type": suffix.removeprefix(".") or "binary"})


def _encoding(path: Path) -> str:
    if path.suffix.lower() == ".csv":
        return _csv_encoding(path)
    if path.suffix.lower() in {".json", ".md"}:
        return "utf-8"
    return "binary"


def _classification(relative: Path) -> tuple[str, str, str]:
    text = relative.as_posix()
    if text.startswith("derived/section3/"):
        return "section3", "analytical_input", "pnadc_ilo_2025q3"
    if text.startswith("derived/rais/"):
        return "rais", "analytical_input", "rais_2016_2024"
    if text.startswith("derived/pnadc/"):
        return "pnadc", "analytical_input", "pnadc_quarterly"
    if text.startswith("derived/spatial/"):
        source = "pnad_tic_2021" if "pnad" in text else "anatel_broadband"
        return "spatial", "analytical_input", source
    if text.startswith("derived/caged/construction_outputs/"):
        return "caged", "construction_backing", "novo_caged"
    if text.startswith("interim/movimentacoes/"):
        return "caged", "signed_fact_partition", "novo_caged"
    if "Final_Scores_ISCO08" in text:
        return "common", "source_metadata", "ilo_nask_2025"
    if text.startswith("vintage/crosswalk/"):
        return "common", "source_metadata", "occupation_crosswalks"
    if text.startswith("vintage/cnae/"):
        return "caged", "source_metadata", "concla_cnae20"
    if text.startswith("vintage/ipca/") or "ipca" in text:
        return "common", "source_metadata", "bcb_ipca"
    if text.startswith("vintage/v1/"):
        return "caged", "validation_source", "v1_frozen_reference"
    if text.startswith("vintage/pdet/"):
        return "caged", "validation_source", "mte_pdet"
    if text.startswith("derived/"):
        return "caged", "analytical_input", "novo_caged"
    return "common", "source_metadata", "package_metadata"


def build_manifest(bundle_dir: Path, manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in expected_bundle_files(bundle_dir):
        relative = path.relative_to(bundle_dir)
        component, role, source_id = _classification(relative)
        rows.append(
            {
                "path": relative.as_posix(),
                "component": component,
                "role": role,
                "source_id": source_id,
                "bytes": str(path.stat().st_size),
                "schema": _schema(path),
                "encoding": _encoding(path),
                "sha256": sha256_file(path),
            }
        )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, manifest_path)
    return rows


def validate_manifest(bundle_dir: Path, manifest_path: Path) -> dict[str, Any]:
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or tuple(rows[0]) != FIELDS:
        raise RuntimeError("Analytical-bundle manifest columns are invalid")
    declared = {row["path"] for row in rows}
    actual = {
        path.relative_to(bundle_dir).as_posix()
        for path in expected_bundle_files(bundle_dir)
    }
    if declared != actual:
        raise RuntimeError(
            "Analytical-bundle file set differs; "
            f"missing={sorted(declared - actual)}, extra={sorted(actual - declared)}"
        )
    failures = []
    for row in rows:
        path = bundle_dir / row["path"]
        if path.stat().st_size != int(row["bytes"]):
            failures.append(f"bytes:{row['path']}")
        if sha256_file(path) != row["sha256"]:
            failures.append(f"sha256:{row['path']}")
    if failures:
        raise RuntimeError("Analytical-bundle validation failed: " + ", ".join(failures))
    return {
        "bytes": sum(int(row["bytes"]) for row in rows),
        "files": len(rows),
        "manifest_sha256": sha256_file(manifest_path),
        "status": "pass",
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "validate"))
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.action == "build":
        build_manifest(args.bundle_dir.resolve(), args.manifest.resolve())
    result = validate_manifest(args.bundle_dir.resolve(), args.manifest.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
