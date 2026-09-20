from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = PACKAGE_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from section3.data import read_data
from section3.r_validation import build_python_aggregates


def test_section3_r_contract_covers_tables_and_figure_backing_data() -> None:
    frame = read_data(
        PACKAGE_ROOT / "data" / "derived" / "section3" / "pnad_ilo_merged.parquet"
    )
    aggregates = build_python_aggregates(frame)

    assert aggregates["aggregate_id"].is_unique
    assert {
        "base",
        "gradient",
        "exposure_group",
        "high_occupation",
        "sector",
        "demographic",
        "state",
        "occupation_group",
        "score_distribution",
    } == set(aggregates["scope"])
    assert len(aggregates) > 100


def test_section3_r_script_does_not_read_python_results() -> None:
    script = (PACKAGE_ROOT / "R" / "section3_replication.R").read_text(
        encoding="utf-8"
    )

    assert "--input" in script
    assert "results/reference" not in script
    assert "table_3_" not in script
