from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "ingest" / "download.py"


def load_download_module():
    spec = importlib.util.spec_from_file_location("download", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load download.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_record(payload: bytes) -> dict[str, object]:
    return {
        "competencia": "202101",
        "tipo": "MOV",
        "url": (
            "ftp://ftp.mtps.gov.br/pdet/microdados/"
            "NOVO%20CAGED/2021/202101/CAGEDMOV202101.7z"
        ),
        "bytes": len(payload),
        "data_modificacao_ftp": "2026-06-08T18:26:14Z",
    }


def test_download_resumes_partial_file_and_promotes_atomically(
    tmp_path: Path,
) -> None:
    module = load_download_module()
    payload = b"official-vintage-payload"
    record = make_record(payload)
    offsets: list[int] = []

    def flaky_transfer(
        _url: str,
        part_path: Path,
        offset: int,
        _timeout: float,
    ) -> None:
        offsets.append(offset)
        with part_path.open("ab") as handle:
            if len(offsets) == 1:
                handle.write(payload[:8])
                raise OSError("temporary FTP failure")
            handle.write(payload[offset:])

    result = module.download_archive(
        record,
        tmp_path,
        transfer=flaky_transfer,
        sleep=lambda _seconds: None,
        now=lambda: datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc),
    )

    final_path = tmp_path / "CAGEDMOV202101.7z"
    assert offsets == [0, 8]
    assert final_path.read_bytes() == payload
    assert not (tmp_path / "CAGEDMOV202101.7z.part").exists()
    assert result["sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["baixado_em"] == "2026-07-25T12:00:00Z"


def test_second_run_skips_valid_archive_and_preserves_manifest(
    tmp_path: Path,
) -> None:
    module = load_download_module()
    payload = b"already-downloaded"
    record = make_record(payload)
    final_path = tmp_path / "CAGEDMOV202101.7z"
    final_path.write_bytes(payload)
    manifest_path = tmp_path / "manifest.json"
    expected_manifest = {
        "CAGEDMOV202101.7z": {
            "url": record["url"],
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "data_modificacao_ftp": record["data_modificacao_ftp"],
            "baixado_em": "2026-07-25T12:00:00Z",
        }
    }
    manifest_path.write_text(
        json.dumps(expected_manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    def unexpected_transfer(*_args, **_kwargs) -> None:
        raise AssertionError("valid archive must not be downloaded again")

    module.download_inventory(
        [record],
        tmp_path,
        manifest_path,
        transfer=unexpected_transfer,
    )

    assert (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        == expected_manifest
    )


def test_verify_only_detects_same_size_hash_corruption(tmp_path: Path) -> None:
    module = load_download_module()
    payload = b"correct"
    record = make_record(payload)
    final_path = tmp_path / "CAGEDMOV202101.7z"
    final_path.write_bytes(b"corrupt")
    manifest = {
        "CAGEDMOV202101.7z": {
            "url": record["url"],
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "data_modificacao_ftp": record["data_modificacao_ftp"],
            "baixado_em": "2026-07-25T12:00:00Z",
        }
    }

    divergences = module.verify_inventory([record], tmp_path, manifest)

    assert divergences == ["CAGEDMOV202101.7z: sha256 mismatch"]


def test_archive_manifest_count_ignores_frozen_non_archive_inputs() -> None:
    module = load_download_module()
    manifest = {
        "CAGEDMOV202101.7z": {"sha256": "a" * 64},
        "crosswalk/example.csv": {"sha256": "b" * 64},
        "pdet/tabelas_202605.xlsx": {"sha256": "c" * 64},
    }

    assert module.archive_manifest_count(manifest) == 1
