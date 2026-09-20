from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RUNNER = PACKAGE_ROOT / "run_replication.py"


def test_section3_target_reestimates_four_tables_and_keeps_demographics_as_backing_data(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "reproduced"

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--target",
            "section3",
            "--mode",
            "reproduce",
            "--skip-figures",
            "--output-dir",
            str(output_dir),
        ],
        cwd=PACKAGE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    section_dir = output_dir / "section3"
    assert "REPLICATION: COMPLETE" in completed.stdout
    assert {path.name for path in output_dir.iterdir()} == {
        "run_manifest.json",
        "section3",
        "validation",
    }
    assert len(list((section_dir / "tables").glob("*.csv"))) == 4
    assert not (section_dir / "tables" / "table_3_5_demographics_summary.csv").exists()
    assert (
        section_dir
        / "backing_data"
        / "table_3_5_demographics_summary.csv"
    ).is_file()
    assert not (
        section_dir
        / "backing_data"
        / "table_3_5_demographics_summary.md"
    ).exists()
    manifest = json.loads(
        (section_dir / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["failure_count"] == 0
    assert "/Users/" not in json.dumps(manifest)
    root_manifest = json.loads(
        (output_dir / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert root_manifest["package_id"] == "dissertation-replication-v2"
    assert root_manifest["target"] == "section3"
    assert root_manifest["components"] == ["section3"]
    assert "/Users/" not in json.dumps(root_manifest)

    subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--target",
            "section3",
            "--mode",
            "reproduce",
            "--skip-figures",
            "--output-dir",
            str(output_dir),
        ],
        cwd=PACKAGE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
