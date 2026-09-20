from __future__ import annotations

import csv
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = PACKAGE_ROOT / "config" / "manuscript_artifacts.csv"


def _rows() -> list[dict[str, str]]:
    with REGISTRY.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_registry_is_the_exact_53_item_manuscript_contract() -> None:
    rows = _rows()

    assert len(rows) == 53
    assert len({row["artifact_id"] for row in rows}) == 53
    assert {row["component"] for row in rows} == {
        "section3",
        "caged",
        "rais",
        "pnadc",
        "spatial",
    }
    assert all(
        row["producer"]
        and row["input_contract"]
        and row["reference_path"]
        and row["command"]
        for row in rows
    )


def test_registry_includes_the_current_manuscript_forest_output() -> None:
    by_id = {row["artifact_id"]: row for row in _rows()}

    assert by_id["figure_5_2_6"]["reference_path"] == (
        "caged/figures/figure_5_2_6_group_outcome_forest.png"
    )


def test_registry_uses_the_current_appendix_c_and_d_numbering() -> None:
    rows = _rows()
    identifiers = {row["artifact_id"] for row in rows}

    assert {
        "table_c_1",
        "figure_c_1",
        "figure_c_2",
        "table_d_1",
        "table_d_2",
    } <= identifiers
    assert not {
        "table_5_3_1",
        "figure_5_3_1",
        "figure_5_3_2",
        "table_5_4_1",
        "table_5_4_2",
    } & identifiers


def test_every_registered_producer_is_a_real_public_module() -> None:
    missing = []
    for row in _rows():
        producer = PACKAGE_ROOT / (row["producer"].replace(".", "/") + ".py")
        if not producer.is_file():
            missing.append(str(producer.relative_to(PACKAGE_ROOT)))

    assert not missing, f"registered producers are missing: {missing}"
