from __future__ import annotations

from pathlib import Path
import sys

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
COMMON_DIR = PACKAGE_ROOT / "code" / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from paths import ReplicationPaths, portable_path


def test_default_path_context_is_entirely_v2_local() -> None:
    paths = ReplicationPaths.defaults()

    assert paths.package == PACKAGE_ROOT
    assert paths.data == PACKAGE_ROOT / "data"
    assert paths.raw == PACKAGE_ROOT / "data" / "vintage"
    assert paths.reference == PACKAGE_ROOT / "results" / "reference"
    assert paths.reproduced == PACKAGE_ROOT / "results" / "reproduced"
    assert paths.work == PACKAGE_ROOT / ".replication-work"


def test_path_context_round_trips_through_the_runtime_environment(
    tmp_path: Path,
) -> None:
    original = ReplicationPaths(
        package=PACKAGE_ROOT,
        data=tmp_path / "bundle",
        raw=tmp_path / "raw",
        reference=PACKAGE_ROOT / "results" / "reference",
        reproduced=tmp_path / "output",
        work=tmp_path / "work",
    )

    restored = ReplicationPaths.from_environment(original.environment())

    assert restored == original.resolved()


def test_portable_path_preserves_globs_without_leaking_the_host_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "package"
    source = root / "data" / "partition=*" / "part.parquet"

    assert portable_path(source, relative_to=root) == (
        "data/partition=*/part.parquet"
    )
    with pytest.raises(ValueError, match="outside"):
        portable_path(tmp_path / "external.csv", relative_to=root)
