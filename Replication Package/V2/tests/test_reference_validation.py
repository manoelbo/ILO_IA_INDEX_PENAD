from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = (
        PACKAGE_ROOT
        / "code"
        / "replication"
        / "reference_validation.py"
    )
    spec = importlib.util.spec_from_file_location("reference_validation_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_component_reference_comparison_requires_equal_file_sets(
    tmp_path: Path,
) -> None:
    module = load_module()
    reference = tmp_path / "reference"
    reproduced = tmp_path / "reproduced"
    expected = reference / "artifacts" / "pnadc" / "tables" / "table.csv"
    observed = reproduced / "pnadc" / "tables" / "table.csv"
    expected.parent.mkdir(parents=True)
    observed.parent.mkdir(parents=True)
    expected.write_text("value\n1\n", encoding="utf-8")
    observed.write_text("value\n1\n", encoding="utf-8")
    report = reproduced / "validation" / "reference_comparison.csv"

    summary = module.compare_reproduced_components(
        output_root=reproduced,
        reference_dir=reference,
        components=("pnadc",),
        skip_figures=False,
        report_path=report,
    )

    assert summary["status"] == "pass"
    assert pd.read_csv(report)["status"].tolist() == ["PASS"]

    extra = reproduced / "pnadc" / "tables" / "unregistered.csv"
    extra.write_text("value\n2\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="differ from the signed reference"):
        module.compare_reproduced_components(
            output_root=reproduced,
            reference_dir=reference,
            components=("pnadc",),
            skip_figures=False,
            report_path=report,
        )
    failed = pd.read_csv(report)
    assert failed.loc[failed["path"].eq("tables/unregistered.csv"), "status"].item() == "FAIL"


def test_reference_freeze_markdown_allowlist_excludes_internal_reports() -> None:
    module = load_module()

    assert module._public_markdown(Path("INDEX.md"))
    assert module._public_markdown(Path("caged/tables/table_5_1.md"))
    assert module._public_markdown(Path("section3/tables/table_3_1.md"))
    assert not module._public_markdown(Path("section3/INDEX.md"))
    assert not module._public_markdown(
        Path("section3/validation/validation_checks.md")
    )
    assert not module._public_markdown(Path("caged/DECISIONS.md"))
    assert not module._public_markdown(
        Path("section3/backing_data/table_3_5_demographics_summary.md")
    )
