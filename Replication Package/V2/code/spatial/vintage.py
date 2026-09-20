#!/usr/bin/env python3
"""Freeze selected members from the official Anatel broadband ZIP via ranges."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import struct
import sys
import tempfile
import unicodedata
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


EOCD_SIGNATURE = b"PK\x05\x06"
CENTRAL_SIGNATURE = b"PK\x01\x02"
LOCAL_SIGNATURE = b"PK\x03\x04"
TAIL_BYTES = 1024 * 1024
URL = (
    "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/"
    "acessos/acessos_banda_larga_fixa.zip"
)
EXPECTED_CONTENT_LENGTH = 1_019_626_579
EXPECTED_LAST_MODIFIED = "Wed, 22 Jul 2026 10:32:35 GMT"
SELECTED_MEMBERS = (
    "Acessos_Banda_Larga_Fixa_2021.csv",
    "Acessos_Banda_Larga_Fixa_2022.csv",
    "Densidade_Banda_Larga_Fixa.csv",
    "Acessos_Banda_Larga_Fixa_Total.csv",
)
ACCESS_HEADER = [
    "Ano",
    "Mês",
    "Grupo Econômico",
    "Empresa",
    "CNPJ",
    "Porte da Prestadora",
    "UF",
    "Município",
    "Código IBGE Município",
    "Faixa de Velocidade",
    "Velocidade",
    "Tecnologia",
    "Meio de Acesso",
    "Tipo de Pessoa",
    "Tipo de Produto",
    "Acessos",
]
DENSITY_HEADER = [
    "Ano",
    "Mês",
    "UF",
    "Município",
    "Código IBGE",
    "Densidade",
    "Nível Geográfico Densidade",
]
FRONT_ROOT = Path(__file__).resolve().parents[1]
VINTAGE_DIR = FRONT_ROOT / "data" / "vintage"
DEFAULT_MANIFEST = VINTAGE_DIR / "manifest.json"
IBGE_FROZEN = VINTAGE_DIR / "ibge_municipios_censo2022.parquet"
IBGE_FROZEN_SHA256 = (
    "66c65598a2a5d5c9d18459542587058719dd084f7b8efa97c45d00814392bd7f"
)
DEFAULT_PRE_TREATMENT = FRONT_ROOT / "data" / "anatel_pre_treatment.csv"
DEFAULT_DOMAIN_AUDIT = FRONT_ROOT / "results" / "anatel_domain_audit.csv"
DEFAULT_TOTAL_RECONCILIATION = (
    FRONT_ROOT / "results" / "anatel_total_reconciliation.csv"
)
DEFAULT_STATUS = FRONT_ROOT / "results" / "anatel_vintage_status.json"

V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
for module_path in (
    V2_ROOT / "code" / "common",
    V2_ROOT / "code" / "caged" / "panel",
):
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))

from build_panel import _configure_connection  # noqa: E402
from merge_audit import audited_merge  # noqa: E402


@dataclass(frozen=True)
class ExtractedMember:
    member: str
    csv_bytes: bytes
    compressed_bytes: bytes
    inventory: dict[str, Any]


class HTTPRangeClient:
    """HTTP client that rejects servers ignoring the requested byte range."""

    def __init__(self, url: str = URL) -> None:
        self.url = url
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"HEAD", "GET"}),
        )
        self.session = requests.Session()
        self.session.mount(
            "https://",
            HTTPAdapter(max_retries=retry),
        )
        self.headers = {
            "Accept-Encoding": "identity",
            "User-Agent": "dissertation-anatel-stage0/1.0",
        }

    def head(self) -> dict[str, Any]:
        response = self.session.head(
            self.url,
            headers=self.headers,
            timeout=60,
            allow_redirects=True,
        )
        response.raise_for_status()
        return {
            "content_length": int(response.headers["Content-Length"]),
            "last_modified": response.headers.get("Last-Modified", ""),
            "content_type": response.headers.get("Content-Type", ""),
            "accept_ranges": response.headers.get("Accept-Ranges", ""),
            "etag": response.headers.get("ETag", ""),
        }

    def fetch_range(self, start: int, end: int) -> bytes:
        headers = {
            **self.headers,
            "Range": f"bytes={start}-{end}",
        }
        response = self.session.get(
            self.url,
            headers=headers,
            timeout=(30, 180),
        )
        response.raise_for_status()
        if response.status_code != 206:
            raise RuntimeError(
                f"Anatel server ignored Range {start}-{end}: "
                f"HTTP {response.status_code}"
            )
        expected_content_range = f"bytes {start}-{end}/"
        observed = response.headers.get("Content-Range", "")
        if not observed.startswith(expected_content_range):
            raise RuntimeError(
                f"Unexpected Content-Range for {start}-{end}: {observed}"
            )
        return response.content


class RangeZipReader:
    """Read a non-ZIP64 archive through an inclusive byte-range callback."""

    def __init__(
        self,
        *,
        content_length: int,
        fetch_range: Callable[[int, int], bytes],
    ) -> None:
        if content_length <= 0:
            raise ValueError("ZIP content length must be positive")
        self.content_length = int(content_length)
        self.fetch_range = fetch_range
        self._inventory: list[dict[str, Any]] | None = None

    def _fetch_exact(self, start: int, end: int) -> bytes:
        if start < 0 or end < start or end >= self.content_length:
            raise ValueError(f"Invalid ZIP range: {start}-{end}")
        payload = self.fetch_range(start, end)
        expected = end - start + 1
        if len(payload) != expected:
            raise RuntimeError(
                f"Range {start}-{end} returned {len(payload)} bytes; "
                f"expected {expected}"
            )
        return payload

    def inventory(self) -> list[dict[str, Any]]:
        if self._inventory is not None:
            return [dict(entry) for entry in self._inventory]
        tail_start = max(0, self.content_length - TAIL_BYTES)
        tail = self._fetch_exact(tail_start, self.content_length - 1)
        position = tail.rfind(EOCD_SIGNATURE)
        if position < 0 or position + 22 > len(tail):
            raise RuntimeError("ZIP end-of-central-directory record not found")
        (
            signature,
            disk_number,
            central_disk,
            disk_entries,
            total_entries,
            central_size,
            central_offset,
            comment_length,
        ) = struct.unpack_from("<4s4H2LH", tail, position)
        if signature != EOCD_SIGNATURE:
            raise RuntimeError("Invalid ZIP EOCD signature")
        if disk_number or central_disk or disk_entries != total_entries:
            raise RuntimeError("Multi-disk ZIP archives are unsupported")
        if (
            total_entries == 0xFFFF
            or central_size == 0xFFFFFFFF
            or central_offset == 0xFFFFFFFF
        ):
            raise RuntimeError("ZIP64 archive is unsupported")
        if position + 22 + comment_length > len(tail):
            raise RuntimeError("ZIP EOCD comment is truncated")
        central = self._fetch_exact(
            int(central_offset),
            int(central_offset + central_size - 1),
        )
        entries: list[dict[str, Any]] = []
        cursor = 0
        for _ in range(int(total_entries)):
            if central[cursor : cursor + 4] != CENTRAL_SIGNATURE:
                raise RuntimeError("Invalid ZIP central-directory signature")
            values = struct.unpack_from("<4s6H3L5H2L", central, cursor)
            (
                _,
                _version_made,
                _version_needed,
                flags,
                compression,
                _modified_time,
                _modified_date,
                crc32,
                compressed_size,
                uncompressed_size,
                name_length,
                extra_length,
                member_comment_length,
                _disk_start,
                _internal_attributes,
                _external_attributes,
                offset_local,
            ) = values
            name_start = cursor + 46
            name_end = name_start + name_length
            encoding = "utf-8" if flags & 0x800 else "cp437"
            member = central[name_start:name_end].decode(encoding)
            entries.append(
                {
                    "member": member,
                    "offset_local": int(offset_local),
                    "bytes_compressed": int(compressed_size),
                    "bytes_csv": int(uncompressed_size),
                    "compression": int(compression),
                    "crc32": int(crc32),
                }
            )
            cursor = (
                name_end
                + int(extra_length)
                + int(member_comment_length)
            )
        if cursor != len(central):
            raise RuntimeError("ZIP central-directory length mismatch")
        self._inventory = entries
        return [dict(entry) for entry in entries]

    def _entry(self, member: str) -> dict[str, Any]:
        matches = [
            entry for entry in self.inventory() if entry["member"] == member
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one ZIP member named {member}; found {len(matches)}"
            )
        return matches[0]

    def _compressed_payload(self, entry: dict[str, Any]) -> bytes:
        offset = int(entry["offset_local"])
        header = self._fetch_exact(offset, offset + 29)
        values = struct.unpack("<4s5H3L2H", header)
        if values[0] != LOCAL_SIGNATURE:
            raise RuntimeError("Invalid ZIP local-file signature")
        name_length = int(values[-2])
        extra_length = int(values[-1])
        data_start = offset + 30 + name_length + extra_length
        data_end = data_start + int(entry["bytes_compressed"]) - 1
        return self._fetch_exact(data_start, data_end)

    @staticmethod
    def _decompress(payload: bytes, entry: dict[str, Any]) -> bytes:
        compression = int(entry["compression"])
        if compression == 0:
            result = payload
        elif compression == 8:
            result = zlib.decompress(payload, -15)
        else:
            raise RuntimeError(
                f"Unsupported ZIP compression method: {compression}"
            )
        if len(result) != int(entry["bytes_csv"]):
            raise RuntimeError("ZIP member uncompressed-size mismatch")
        if zlib.crc32(result) & 0xFFFFFFFF != int(entry["crc32"]):
            raise RuntimeError("ZIP member CRC-32 mismatch")
        return result

    def extract(self, member: str) -> ExtractedMember:
        entry = self._entry(member)
        compressed = self._compressed_payload(entry)
        return ExtractedMember(
            member=member,
            csv_bytes=self._decompress(compressed, entry),
            compressed_bytes=compressed,
            inventory=entry,
        )

    def extract_to_file(
        self,
        member: str,
        destination: Path,
        *,
        chunk_size: int = 8 * 1024 * 1024,
    ) -> dict[str, Any]:
        """Stream one member to disk and hash compressed and CSV bytes."""
        entry = self._entry(member)
        offset = int(entry["offset_local"])
        header = self._fetch_exact(offset, offset + 29)
        values = struct.unpack("<4s5H3L2H", header)
        if values[0] != LOCAL_SIGNATURE:
            raise RuntimeError("Invalid ZIP local-file signature")
        data_start = offset + 30 + int(values[-2]) + int(values[-1])
        remaining = int(entry["bytes_compressed"])
        cursor = data_start
        compressed_hash = hashlib.sha256()
        csv_hash = hashlib.sha256()
        crc = 0
        csv_size = 0
        decompressor = (
            zlib.decompressobj(-15)
            if int(entry["compression"]) == 8
            else None
        )
        if int(entry["compression"]) not in {0, 8}:
            raise RuntimeError("Unsupported ZIP compression method")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        with temporary.open("wb") as handle:
            while remaining:
                size = min(chunk_size, remaining)
                block = self._fetch_exact(cursor, cursor + size - 1)
                compressed_hash.update(block)
                output = (
                    decompressor.decompress(block)
                    if decompressor is not None
                    else block
                )
                handle.write(output)
                csv_hash.update(output)
                crc = zlib.crc32(output, crc)
                csv_size += len(output)
                cursor += size
                remaining -= size
            if decompressor is not None:
                output = decompressor.flush()
                handle.write(output)
                csv_hash.update(output)
                crc = zlib.crc32(output, crc)
                csv_size += len(output)
            handle.flush()
            os.fsync(handle.fileno())
        if csv_size != int(entry["bytes_csv"]):
            temporary.unlink(missing_ok=True)
            raise RuntimeError("ZIP member uncompressed-size mismatch")
        if crc & 0xFFFFFFFF != int(entry["crc32"]):
            temporary.unlink(missing_ok=True)
            raise RuntimeError("ZIP member CRC-32 mismatch")
        os.replace(temporary, destination)
        return {
            **entry,
            "sha256_compressed": compressed_hash.hexdigest(),
            "sha256_csv": csv_hash.hexdigest(),
        }


def validate_csv_header(payload: bytes, expected: list[str]) -> None:
    first_line = payload.splitlines()[0].decode("utf-8-sig")
    observed = next(csv.reader(io.StringIO(first_line), delimiter=";"))
    if observed != expected:
        raise RuntimeError(
            f"CSV header mismatch: expected {expected}, observed {observed}"
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _file_prefix(path: Path, size: int = 4096) -> bytes:
    with path.open("rb") as handle:
        return handle.read(size)


def _freeze_ibge_reference() -> dict[str, Any]:
    """Validate the redistributable frozen IBGE cross-check input."""
    if not IBGE_FROZEN.exists():
        raise FileNotFoundError(IBGE_FROZEN)
    observed = _sha256_file(IBGE_FROZEN)
    if observed != IBGE_FROZEN_SHA256:
        raise RuntimeError(
            "Frozen IBGE municipality input hash does not match the "
            "registered analytical bundle"
        )
    return {
        "member": IBGE_FROZEN.name,
        "source": (
            "analytical_bundle:derived/spatial/vintage/"
            "ibge_municipios_censo2022.parquet"
        ),
        "bytes_csv": IBGE_FROZEN.stat().st_size,
        "sha256_csv": observed,
        "purpose": "population_filter_and_census_household_cross_check",
    }


def freeze_selected_members(
    *,
    client: HTTPRangeClient | None = None,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    client = client or HTTPRangeClient()
    metadata = client.head()
    if metadata["content_length"] != EXPECTED_CONTENT_LENGTH:
        raise RuntimeError(
            "Anatel content-length changed; record the new vintage before "
            "deriving offsets"
        )
    if metadata["last_modified"] != EXPECTED_LAST_MODIFIED:
        raise RuntimeError(
            "Anatel last-modified changed; record the new vintage before "
            "deriving offsets"
        )
    reader = RangeZipReader(
        content_length=metadata["content_length"],
        fetch_range=client.fetch_range,
    )
    inventory = reader.inventory()
    if len(inventory) != 27:
        raise RuntimeError(
            f"Expected 27 Anatel ZIP members; found {len(inventory)}"
        )
    observed_names = {entry["member"] for entry in inventory}
    missing = sorted(set(SELECTED_MEMBERS) - observed_names)
    if missing:
        raise RuntimeError(f"Anatel ZIP is missing selected members: {missing}")
    accessed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    member_records: list[dict[str, Any]] = []
    for member in SELECTED_MEMBERS:
        destination = VINTAGE_DIR / member
        record = reader.extract_to_file(member, destination)
        if member.startswith("Acessos_Banda_Larga_Fixa_20"):
            validate_csv_header(_file_prefix(destination), ACCESS_HEADER)
        elif member == "Densidade_Banda_Larga_Fixa.csv":
            validate_csv_header(_file_prefix(destination), DENSITY_HEADER)
        member_records.append(
            {
                **record,
                "url": URL,
                "content_length_zip": metadata["content_length"],
                "last_modified_zip": metadata["last_modified"],
                "accessed_at": accessed_at,
            }
        )
    manifest = {
        "source": {
            "url": URL,
            **metadata,
            "accessed_at": accessed_at,
        },
        "directory_member_count": len(inventory),
        "members": member_records,
        "supplemental_inputs": [_freeze_ibge_reference()],
        "offsets_derived_from_central_directory": True,
    }
    _atomic_json(manifest, manifest_path)
    return manifest


def validate_existing_vintage(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate every byte of a separately supplied official-source snapshot."""
    source = manifest.get("source", {})
    if (
        source.get("url") != URL
        or source.get("content_length") != EXPECTED_CONTENT_LENGTH
        or source.get("last_modified") != EXPECTED_LAST_MODIFIED
    ):
        raise RuntimeError("Spatial vintage source identity does not match")
    records = manifest.get("members")
    if not isinstance(records, list):
        raise RuntimeError("Spatial vintage member inventory is missing")
    by_name = {str(record.get("member")): record for record in records}
    if set(by_name) != set(SELECTED_MEMBERS):
        raise RuntimeError("Spatial vintage member set does not match")
    for name in SELECTED_MEMBERS:
        path = VINTAGE_DIR / name
        record = by_name[name]
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != int(record.get("bytes_csv", -1)):
            raise RuntimeError(f"Spatial vintage byte count changed: {name}")
        if _sha256_file(path) != record.get("sha256_csv"):
            raise RuntimeError(f"Spatial vintage hash changed: {name}")
    _freeze_ibge_reference()
    return manifest


def build_pre_treatment_connectivity(
    access_monthly: pd.DataFrame,
    density_monthly: pd.DataFrame,
    ibge: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Aggregate the frozen pre-period into one row per municipality."""
    access = (
        access_monthly.groupby("id_municipio", observed=True)
        .agg(
            access_months=("mes", "size"),
            media_acessos_pre=("total_accesses", "mean"),
            soma_acessos=("total_accesses", "sum"),
            soma_fibra=("fiber_accesses", "sum"),
            soma_fibra_tecnologia=(
                "fiber_technology_accesses",
                "sum",
            ),
        )
        .reset_index()
    )
    access["pct_fibra"] = access["soma_fibra"] / access[
        "soma_acessos"
    ].where(access["soma_acessos"].ne(0))
    access["pct_fiber_technology_check"] = access[
        "soma_fibra_tecnologia"
    ] / access["soma_acessos"].where(access["soma_acessos"].ne(0))
    density = (
        density_monthly.groupby("id_municipio", observed=True)
        .agg(
            density_months=("mes", "size"),
            densidade_oficial=("densidade_oficial", "mean"),
        )
        .reset_index()
    )
    connectivity = audited_merge(
        access,
        density,
        merge_id="a3_access_density",
        validate="one_to_one",
        on="id_municipio",
        how="inner",
    )
    connectivity["penetracao_bl"] = (
        connectivity["densidade_oficial"] / 100.0
    )
    old_threshold = float(connectivity["penetracao_bl"].median())
    connectivity["high_connectivity_old_national"] = connectivity[
        "penetracao_bl"
    ].gt(old_threshold).astype("int8")
    reference = ibge[
        ["id_municipio", "populacao", "domicilios"]
    ].copy()
    reference["id_municipio"] = (
        reference["id_municipio"].astype(str).str.zfill(7)
    )
    connectivity = audited_merge(
        connectivity,
        reference,
        merge_id="a3_connectivity_ibge_cross_check",
        validate="one_to_one",
        on="id_municipio",
        how="inner",
    )
    connectivity["densidade_censo_domicilios"] = (
        connectivity["media_acessos_pre"]
        / connectivity["domicilios"].where(
            connectivity["domicilios"].gt(0)
        )
        * 100.0
    )
    connectivity["populacao_por_domicilio"] = (
        connectivity["populacao"]
        / connectivity["domicilios"].where(
            connectivity["domicilios"].gt(0)
        )
    )
    difference = (
        connectivity["densidade_oficial"]
        - connectivity["densidade_censo_domicilios"]
    )
    correlation = (
        connectivity["densidade_oficial"].corr(
            connectivity["densidade_censo_domicilios"]
        )
        if len(connectivity) >= 2
        else float("nan")
    )
    audit = {
        "municipalities": int(len(connectivity)),
        "old_national_threshold": old_threshold,
        "old_national_high_municipalities": int(
            connectivity["high_connectivity_old_national"].sum()
        ),
        "old_national_low_municipalities": int(
            connectivity["high_connectivity_old_national"].eq(0).sum()
        ),
        "pct_fibra_identically_zero": bool(
            connectivity["pct_fibra"].fillna(0).eq(0).all()
        ),
        "pct_fibra_min": float(connectivity["pct_fibra"].min()),
        "pct_fibra_max": float(connectivity["pct_fibra"].max()),
        "official_vs_census_density_correlation": (
            float(correlation) if np.isfinite(correlation) else None
        ),
        "official_minus_census_density_median": float(
            difference.median()
        ),
        "official_minus_census_density_median_absolute": float(
            difference.abs().median()
        ),
        "population_per_household_median": float(
            connectivity["populacao_por_domicilio"].median()
        ),
    }
    return (
        connectivity.sort_values("id_municipio").reset_index(drop=True),
        audit,
    )


def normalize_geographic_level(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).strip().lower())
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def _csv_literal(paths: list[Path]) -> str:
    quoted = [
        "'" + str(path).replace("'", "''") + "'" for path in paths
    ]
    return "[" + ", ".join(quoted) + "]"


def build_anatel_pre_treatment(
    *,
    pre_treatment_path: Path = DEFAULT_PRE_TREATMENT,
    domain_audit_path: Path = DEFAULT_DOMAIN_AUDIT,
    total_reconciliation_path: Path = DEFAULT_TOTAL_RECONCILIATION,
    status_path: Path = DEFAULT_STATUS,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build A3 derived artifacts exclusively from the frozen local vintage."""
    access_paths = [
        VINTAGE_DIR / "Acessos_Banda_Larga_Fixa_2021.csv",
        VINTAGE_DIR / "Acessos_Banda_Larga_Fixa_2022.csv",
    ]
    density_path = VINTAGE_DIR / "Densidade_Banda_Larga_Fixa.csv"
    total_path = VINTAGE_DIR / "Acessos_Banda_Larga_Fixa_Total.csv"
    for path in [*access_paths, density_path, total_path, IBGE_FROZEN]:
        if not path.exists():
            raise FileNotFoundError(path)
    validate_csv_header(_file_prefix(total_path), ["Ano", "Mês", "Acessos"])
    access_source = _csv_literal(access_paths)
    with tempfile.TemporaryDirectory(prefix="anatel-a3-") as scratch:
        connection = duckdb.connect()
        try:
            _configure_connection(connection, Path(scratch))
            connection.execute(
                f"""
                CREATE TEMP VIEW access_source AS
                SELECT
                    CAST("Ano" AS INTEGER) AS ano,
                    CAST("Mês" AS INTEGER) AS mes,
                    lpad(CAST("Código IBGE Município" AS VARCHAR), 7, '0')
                        AS id_municipio,
                    trim(CAST("Tecnologia" AS VARCHAR)) AS tecnologia,
                    trim(CAST("Meio de Acesso" AS VARCHAR)) AS meio_acesso,
                    CAST("Acessos" AS BIGINT) AS acessos
                FROM read_csv(
                    {access_source},
                    delim = ';',
                    header = true,
                    all_varchar = true,
                    union_by_name = true
                )
                """
            )
            domain_audit = connection.execute(
                """
                SELECT
                    'Tecnologia' AS domain_variable,
                    coalesce(tecnologia, '<MISSING>') AS domain_value,
                    count(*) AS row_count,
                    sum(acessos) AS access_sum
                FROM access_source
                GROUP BY tecnologia
                UNION ALL
                SELECT
                    'Meio de Acesso' AS domain_variable,
                    coalesce(meio_acesso, '<MISSING>') AS domain_value,
                    count(*) AS row_count,
                    sum(acessos) AS access_sum
                FROM access_source
                GROUP BY meio_acesso
                ORDER BY domain_variable, row_count DESC, domain_value
                """
            ).df()
            access_monthly = connection.execute(
                """
                SELECT
                    ano,
                    mes,
                    id_municipio,
                    sum(acessos) AS total_accesses,
                    sum(CASE WHEN meio_acesso = 'Fibra'
                             THEN acessos ELSE 0 END) AS fiber_accesses,
                    sum(CASE WHEN tecnologia IN ('FTTH', 'FTTB')
                             THEN acessos ELSE 0 END)
                        AS fiber_technology_accesses
                FROM access_source
                WHERE (
                    ano = 2021
                    OR (ano = 2022 AND mes <= 10)
                )
                  AND regexp_full_match(id_municipio, '[0-9]{7}')
                  AND id_municipio <> '0000000'
                GROUP BY ano, mes, id_municipio
                ORDER BY ano, mes, id_municipio
                """
            ).df()
            access_all_monthly = connection.execute(
                """
                SELECT ano, mes, sum(acessos) AS accesses_from_members
                FROM access_source
                GROUP BY ano, mes
                ORDER BY ano, mes
                """
            ).df()
            density_literal = str(density_path).replace("'", "''")
            density_levels = connection.execute(
                f"""
                SELECT DISTINCT trim("Nível Geográfico Densidade") AS level
                FROM read_csv(
                    '{density_literal}',
                    delim = ';',
                    header = true,
                    all_varchar = true
                )
                """
            ).fetchall()
            municipal_levels = [
                str(value)
                for (value,) in density_levels
                if normalize_geographic_level(str(value)) == "municipio"
            ]
            if len(municipal_levels) != 1:
                raise RuntimeError(
                    "Could not identify exactly one municipal density level: "
                    f"{density_levels}"
                )
            density_monthly = connection.execute(
                f"""
                SELECT
                    CAST("Ano" AS INTEGER) AS ano,
                    CAST("Mês" AS INTEGER) AS mes,
                    lpad(CAST("Código IBGE" AS VARCHAR), 7, '0')
                        AS id_municipio,
                    avg(CAST(replace("Densidade", ',', '.') AS DOUBLE))
                        AS densidade_oficial,
                    count(*) AS source_rows
                FROM read_csv(
                    '{density_literal}',
                    delim = ';',
                    header = true,
                    all_varchar = true
                )
                WHERE trim("Nível Geográfico Densidade") = ?
                  AND (
                    CAST("Ano" AS INTEGER) = 2021
                    OR (
                        CAST("Ano" AS INTEGER) = 2022
                        AND CAST("Mês" AS INTEGER) <= 10
                    )
                  )
                GROUP BY ano, mes, id_municipio
                ORDER BY ano, mes, id_municipio
                """,
                municipal_levels,
            ).df()
            if int(density_monthly["source_rows"].max()) != 1:
                raise RuntimeError(
                    "Official municipal density has duplicate month rows"
                )
            density_monthly = density_monthly.drop(columns="source_rows")
            total_literal = str(total_path).replace("'", "''")
            official_total = connection.execute(
                f"""
                SELECT
                    CAST("Ano" AS INTEGER) AS ano,
                    CAST("Mês" AS INTEGER) AS mes,
                    CAST("Acessos" AS BIGINT) AS accesses_official_total
                FROM read_csv(
                    '{total_literal}',
                    delim = ';',
                    header = true,
                    all_varchar = true
                )
                WHERE CAST("Ano" AS INTEGER) IN (2021, 2022)
                """
            ).df()
        finally:
            connection.close()
    reconciliation = audited_merge(
        access_all_monthly,
        official_total,
        merge_id="a3_member_total_reconciliation",
        validate="one_to_one",
        on=["ano", "mes"],
        how="inner",
    )
    reconciliation["difference"] = (
        reconciliation["accesses_from_members"]
        - reconciliation["accesses_official_total"]
    )
    if len(reconciliation) != 24 or reconciliation["difference"].ne(0).any():
        raise RuntimeError("Anatel member totals do not reconcile")
    ibge = pd.read_parquet(IBGE_FROZEN)
    pre_treatment, audit = build_pre_treatment_connectivity(
        access_monthly,
        density_monthly,
        ibge,
    )
    if audit["pct_fibra_identically_zero"]:
        raise RuntimeError("not_executed_fiber_domain_unresolved")
    household_median = audit["population_per_household_median"]
    household_plausible = bool(2.7 <= household_median <= 2.9)
    status = {
        "status": (
            "pass" if household_plausible else "fail_household_cross_check"
        ),
        "pre_treatment_start": 202101,
        "pre_treatment_end": 202210,
        "access_monthly_rows": int(len(access_monthly)),
        "density_monthly_rows": int(len(density_monthly)),
        "total_reconciliation_months": int(len(reconciliation)),
        "total_reconciliation_max_absolute_difference": int(
            reconciliation["difference"].abs().max()
        ),
        "household_ratio_plausible_2_7_to_2_9": household_plausible,
        **audit,
        "treatment_coefficient_estimated": False,
    }
    _atomic_csv(domain_audit, domain_audit_path)
    _atomic_csv(pre_treatment, pre_treatment_path)
    _atomic_csv(reconciliation, total_reconciliation_path)
    status["pre_treatment_sha256"] = _sha256_file(pre_treatment_path)
    _atomic_json(status, status_path)
    if not household_plausible:
        raise RuntimeError("Censo household denominator cross-check failed")
    return pre_treatment, status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--process-existing",
        action="store_true",
        help="Build A3 outputs from an already frozen local vintage.",
    )
    args = parser.parse_args()
    manifest = (
        validate_existing_vintage(
            json.loads(args.manifest.read_text(encoding="utf-8"))
        )
        if args.process_existing
        else freeze_selected_members(manifest_path=args.manifest)
    )
    _, status = build_anatel_pre_treatment()
    summary = {
        "manifest": str(args.manifest),
        "members": [
            {
                "member": item["member"],
                "offset_local": item["offset_local"],
                "bytes_compressed": item["bytes_compressed"],
                "bytes_csv": item["bytes_csv"],
                "sha256_csv": item["sha256_csv"],
            }
            for item in manifest["members"]
        ],
        "status": status,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
