from __future__ import annotations

import csv
import hashlib
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = PACKAGE_ROOT / "config" / "data_sources.csv"
REQUIRED_COLUMNS = {
    "source_id",
    "provider",
    "url",
    "vintage",
    "acquired_at",
    "bytes",
    "schema",
    "encoding",
    "sha256",
    "terms_url",
    "redistribution_notes",
}


def _rows() -> list[dict[str, str]]:
    with REGISTRY.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_source_registry_has_complete_unique_public_metadata() -> None:
    rows = _rows()

    assert rows
    assert set(rows[0]) == REQUIRED_COLUMNS
    assert len({row["source_id"] for row in rows}) == len(rows)
    assert all(row["url"].startswith(("https://", "ftp://")) for row in rows)
    assert all(row["terms_url"].startswith("https://") for row in rows)
    assert all(row["vintage"] and row["acquired_at"] for row in rows)
    assert all(not row["bytes"].startswith("/") for row in rows)
    assert all(not row["sha256"].startswith("/") for row in rows)


def test_spatial_small_source_hashes_match_the_frozen_files() -> None:
    rows = {row["source_id"]: row for row in _rows()}
    files = {
        "anatel_broadband": (
            PACKAGE_ROOT / "data" / "derived" / "spatial" / "vintage" / "manifest.json"
        ),
        "pnad_tic_2021": (
            PACKAGE_ROOT
            / "data"
            / "derived"
            / "spatial"
            / "vintage"
            / "pnad_continua_tic_2021_sidra_table_7334.json"
        ),
    }

    for source_id, path in files.items():
        assert int(rows[source_id]["bytes"]) == path.stat().st_size
        assert rows[source_id]["sha256"] == _sha256(path)

    raw_only = (
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "spatial"
        / "vintage"
        / "ibge_municipios_censo2022.parquet"
    )
    assert not raw_only.exists()
    assert (
        rows["ibge_municipality_crosscheck"]["sha256"]
        == "66c65598a2a5d5c9d18459542587058719dd084f7b8efa97c45d00814392bd7f"
    )
    assert "full cache" in rows["anatel_broadband"]["redistribution_notes"]
