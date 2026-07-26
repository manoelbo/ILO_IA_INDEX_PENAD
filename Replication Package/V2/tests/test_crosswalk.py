from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "panel" / "crosswalk.py"


def load_crosswalk_module():
    spec = importlib.util.spec_from_file_location("crosswalk", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load crosswalk.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_freeze_crosswalk_sources_copies_and_hashes_inputs(
    tmp_path: Path,
) -> None:
    module = load_crosswalk_module()
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    sources = {}
    for index, filename in enumerate(module.REQUIRED_FILENAMES, start=1):
        source = source_dir / filename
        source.write_bytes(f"frozen-{index}".encode())
        sources[filename] = source

    ilo_source = sources[module.ILO_FILENAME]
    expected_ilo_hash = hashlib.sha256(ilo_source.read_bytes()).hexdigest()
    target_dir = tmp_path / "vintage" / "crosswalk"
    manifest_path = tmp_path / "vintage" / "manifest.json"

    summary = module.freeze_crosswalk_sources(
        sources,
        target_dir,
        manifest_path,
        expected_ilo_sha256=expected_ilo_hash,
        now=lambda: datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert summary["files_frozen"] == 5
    assert summary["ilo_sha256"] == expected_ilo_hash
    assert set(path.name for path in target_dir.iterdir()) == set(
        module.REQUIRED_FILENAMES
    )
    assert set(manifest) == {
        f"crosswalk/{filename}" for filename in module.REQUIRED_FILENAMES
    }
    for filename, source in sources.items():
        entry = manifest[f"crosswalk/{filename}"]
        assert entry["bytes"] == source.stat().st_size
        assert entry["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert entry["frozen_at"] == "2026-07-26T12:00:00Z"


def test_known_crosswalk_reproduces_t10_and_t11_counts() -> None:
    module = load_crosswalk_module()
    crosswalk_dir = PACKAGE_ROOT / "data" / "vintage" / "crosswalk"

    classification = module.build_classification_from_frozen(crosswalk_dir)

    assert classification["mte_match_status"].value_counts().to_dict() == {
        "matched_official_mte": 436,
        "no_score": 193,
    }
    assert classification["cbo_ilo_gradient"].value_counts().to_dict() == {
        "Exposed: Gradient 3": 31,
        "Exposed: Gradient 2": 31,
        "Exposed: Gradient 1": 13,
        "Minimal Exposure": 95,
        "Not Exposed": 266,
        "No score": 193,
    }
