from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = PACKAGE_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from common.artifacts import compare_build_diagnostics
from section3.build_data import (
    ILO_FILENAME,
    PNAD_FILENAME,
    resolve_ilo_path,
    stable_float_sum,
    validate_pnad_source,
    write_pnad_source_manifest,
    write_canonical_build_diagnostics,
)
from section3.data import canonicalize_analytic_order
from section3.pipeline import stage_full_sources


def test_section3_full_reuses_the_registered_crosswalk_workbook(
    tmp_path: Path,
) -> None:
    section3_raw = tmp_path / "vintage" / "section3"
    registered = tmp_path / "vintage" / "crosswalk" / ILO_FILENAME
    registered.parent.mkdir(parents=True)
    registered.write_bytes(b"registered workbook")

    assert resolve_ilo_path(section3_raw) == registered


def test_section3_specific_cache_has_precedence(tmp_path: Path) -> None:
    section3_raw = tmp_path / "vintage" / "section3"
    local = section3_raw / ILO_FILENAME
    registered = tmp_path / "vintage" / "crosswalk" / ILO_FILENAME
    local.parent.mkdir(parents=True)
    registered.parent.mkdir(parents=True)
    local.write_bytes(b"local workbook")
    registered.write_bytes(b"registered workbook")

    assert resolve_ilo_path(section3_raw) == local


def test_section3_full_reports_every_allowed_workbook_location(
    tmp_path: Path,
) -> None:
    section3_raw = tmp_path / "vintage" / "section3"

    with pytest.raises(FileNotFoundError) as error:
        resolve_ilo_path(section3_raw)

    message = str(error.value)
    assert str(section3_raw / ILO_FILENAME) in message
    assert str(section3_raw.parent / "crosswalk" / ILO_FILENAME) in message


def test_full_source_staging_reads_bundle_and_raw_cache_without_mutating_them(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "bundle"
    raw_dir = tmp_path / "raw-cache" / "section3"
    workspace = tmp_path / "workspace"
    ilo = data_dir / "vintage" / "crosswalk" / ILO_FILENAME
    pnad = raw_dir / PNAD_FILENAME
    ilo.parent.mkdir(parents=True)
    pnad.parent.mkdir(parents=True)
    ilo.write_bytes(b"ilo")
    pnad.write_bytes(b"pnad")
    write_pnad_source_manifest(
        raw_dir,
        rows=1,
        queried_at="2026-08-02T00:00:00+00:00",
    )

    staged = stage_full_sources(
        raw_dir=raw_dir,
        data_dir=data_dir,
        workspace=workspace,
    )

    assert (staged / ILO_FILENAME).read_bytes() == b"ilo"
    assert (staged / PNAD_FILENAME).read_bytes() == b"pnad"
    assert (staged / "manifest.json").is_file()
    assert ilo.read_bytes() == b"ilo"
    assert pnad.read_bytes() == b"pnad"


def test_section3_cached_source_rejects_changed_bytes(tmp_path: Path) -> None:
    source = tmp_path / PNAD_FILENAME
    source.write_bytes(b"pnad")
    write_pnad_source_manifest(
        tmp_path,
        rows=1,
        queried_at="2026-08-02T00:00:00+00:00",
    )
    source.write_bytes(b"changed")

    with pytest.raises(ValueError, match="byte-size|SHA-256"):
        validate_pnad_source(tmp_path)


def test_build_diagnostic_sums_are_independent_of_query_row_order() -> None:
    first = pd.Series([1.0e16, 1.0, -1.0e16, 2.0])
    second = first.iloc[[2, 0, 3, 1]]

    assert stable_float_sum(first) == 3.0
    assert stable_float_sum(second) == 3.0


def test_section3_analytic_order_is_independent_of_source_order() -> None:
    first = pd.DataFrame(
        {
            "occupation": ["b", "a", "a"],
            "weight": [2.0, 3.0, 1.0],
            "group": [None, "x", "x"],
        }
    )
    second = first.iloc[[2, 0, 1]].reset_index(drop=True)

    pd.testing.assert_frame_equal(
        canonicalize_analytic_order(first),
        canonicalize_analytic_order(second),
    )


def test_build_diagnostics_have_a_canonical_public_precision(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text(
        "metric,value\nrows,2\npopulation_total,95943649.37116954\n",
        encoding="utf-8",
    )
    second.write_text(
        "metric,value\nrows,2\npopulation_total,95943649.37116957\n",
        encoding="utf-8",
    )

    first_output = tmp_path / "first-output.csv"
    second_output = tmp_path / "second-output.csv"
    write_canonical_build_diagnostics(first, first_output)
    write_canonical_build_diagnostics(second, second_output)

    assert first_output.read_bytes() == second_output.read_bytes()
    assert b"95943649.371170" in first_output.read_bytes()


def test_build_receipt_comparison_uses_only_the_declared_tolerance(
    tmp_path: Path,
) -> None:
    reference = tmp_path / "reference.csv"
    reproduced = tmp_path / "reproduced.csv"
    reference.write_text("metric,value\npopulation,10.0\nrows,2\n", encoding="utf-8")
    reproduced.write_text(
        "metric,value\npopulation,10.0000005\nrows,2\n",
        encoding="utf-8",
    )

    matches, detail = compare_build_diagnostics(reference, reproduced)
    assert matches is True
    assert "tolerance=1.0e-06" in detail

    reproduced.write_text(
        "metric,value\npopulation,10.000002\nrows,2\n",
        encoding="utf-8",
    )
    matches, _detail = compare_build_diagnostics(reference, reproduced)
    assert matches is False
