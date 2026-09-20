#!/usr/bin/env python3
"""Validate and materialize frozen CAGED construction backing data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import pyarrow.parquet as pq


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PACKAGE_ROOT / "data"
DEFAULT_SOURCE_DIR = (
    DEFAULT_DATA_DIR / "derived" / "caged" / "construction_outputs"
)
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "results"
EXPECTED_FILES = frozenset(
    {
        "reconciliation/build_movements_metrics.json",
        "reconciliation/cnae_month_treatment_support.csv",
        "reconciliation/crosswalk_coverage.json",
        "reconciliation/origem_por_competencia.csv",
        "reconciliation/painel_cbo_cnae_support.json",
        "reconciliation/painel_nacional_support.json",
        "reconciliation/treatment_classification_validation.json",
        "treatment/treatment_variant_comparison.csv",
        "treatment/treatment_variant_support.json",
    }
)
VARIANT_COLUMNS = {
    "V-A": "gradient_v_a",
    "V-B": "gradient_v_b",
    "V-C": "gradient_v_c",
    "V-D": "gradient_v_d",
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_file_set(source_dir: Path) -> None:
    actual = {
        path.relative_to(source_dir).as_posix()
        for path in source_dir.rglob("*")
        if path.is_file()
    }
    if actual != EXPECTED_FILES:
        raise RuntimeError(
            "Frozen CAGED construction backing differs from its contract; "
            f"missing={sorted(EXPECTED_FILES - actual)}, "
            f"extra={sorted(actual - EXPECTED_FILES)}"
        )


def _validate_national_panel(data_dir: Path, source_dir: Path) -> None:
    support = _read_json(
        source_dir / "reconciliation" / "painel_nacional_support.json"
    )
    panel = pd.read_parquet(data_dir / "derived" / "painel_nacional.parquet")
    observed = {
        "cells": int(len(panel)),
        "months": int(panel["periodo_num"].nunique()),
        "cbo_families": int(panel["cbo_4d"].nunique()),
        "zero_admission_cells": int(panel["admissoes"].eq(0).sum()),
        "zero_separation_cells": int(panel["desligamentos"].eq(0).sum()),
        "max_admission_wage": float(panel["salario_medio_adm"].max()),
        "max_separation_wage": float(panel["salario_medio_desl"].max()),
    }
    for field, value in observed.items():
        expected = support.get(field)
        if isinstance(value, float):
            matches = abs(value - float(expected)) <= 1e-9
        else:
            matches = value == expected
        if not matches:
            raise RuntimeError(
                f"National-panel backing drift for {field}: "
                f"{value!r} != {expected!r}"
            )
    for flow, wage in (
        ("admissoes", "salario_medio_adm"),
        ("desligamentos", "salario_medio_desl"),
    ):
        if not panel.loc[panel[flow].eq(0), wage].isna().all():
            raise RuntimeError(f"Zero-flow wage is not missing: {wage}")


def _validate_sector_panel(data_dir: Path, source_dir: Path) -> None:
    support = _read_json(
        source_dir / "reconciliation" / "painel_cbo_cnae_support.json"
    )
    panel_path = data_dir / "derived" / "painel_cbo_cnae.parquet"
    if pq.ParquetFile(panel_path).metadata.num_rows != support["cells"]:
        raise RuntimeError("Sector-panel row count differs from frozen backing")
    if panel_path.stat().st_size != support["sector_panel_bytes"]:
        raise RuntimeError("Sector-panel byte size differs from frozen backing")
    if _sha256(panel_path) != support["sector_panel_sha256"]:
        raise RuntimeError("Sector-panel SHA-256 differs from frozen backing")
    coexistence = (
        source_dir
        / "reconciliation"
        / "cnae_month_treatment_support.csv"
    )
    if coexistence.stat().st_size != support["coexistence_bytes"]:
        raise RuntimeError("CNAE support byte size differs from frozen backing")
    if _sha256(coexistence) != support["coexistence_sha256"]:
        raise RuntimeError("CNAE support SHA-256 differs from frozen backing")
    if len(pd.read_csv(coexistence)) != support["cnae_month_cells"]:
        raise RuntimeError("CNAE support row count differs from frozen backing")


def _validate_treatment(data_dir: Path, source_dir: Path) -> None:
    variants = pd.read_csv(
        data_dir / "derived" / "treatment_variants.csv",
        dtype={"cbo_4d": "string"},
    )
    comparison = pd.read_csv(
        source_dir / "treatment" / "treatment_variant_comparison.csv"
    )
    support = _read_json(
        source_dir / "treatment" / "treatment_variant_support.json"
    )
    if len(variants) != support["cbo_families"]:
        raise RuntimeError("Treatment-variant family count differs from backing")
    observed_rows: list[dict[str, Any]] = []
    base = variants["gradient_v_a"]
    for variant, column in VARIANT_COLUMNS.items():
        changed = int(variants[column].ne(base).sum())
        if changed != support["variant_changes_vs_v_a"][variant]:
            raise RuntimeError(f"Treatment-variant drift for {variant}")
        counts = variants[column].value_counts(dropna=False)
        for classification in comparison.loc[
            comparison["variant"].eq(variant), "classification"
        ]:
            observed_rows.append(
                {
                    "variant": variant,
                    "classification": classification,
                    "cbo_families": int(counts.get(classification, 0)),
                    "changed_vs_v_a": changed,
                }
            )
    observed = pd.DataFrame(observed_rows)
    pd.testing.assert_frame_equal(
        observed.reset_index(drop=True),
        comparison.reset_index(drop=True),
        check_dtype=False,
    )
    coverage = _read_json(
        source_dir / "reconciliation" / "crosswalk_coverage.json"
    )
    if coverage["cbo_families"] != len(variants):
        raise RuntimeError("Crosswalk coverage differs from treatment variants")
    validation = _read_json(
        source_dir
        / "reconciliation"
        / "treatment_classification_validation.json"
    )
    if any(
        validation[field] != 0
        for field in (
            "different_assignments",
            "missing_from_reference",
            "missing_from_v2",
        )
    ):
        raise RuntimeError("Frozen treatment classification does not reconcile")


def _validate_movement_contract(data_dir: Path, source_dir: Path) -> None:
    metrics = _read_json(
        source_dir / "reconciliation" / "build_movements_metrics.json"
    )
    partitions = list(
        (data_dir / "interim" / "movimentacoes").rglob("*.parquet")
    )
    if len(partitions) != metrics["partitions_written"]:
        raise RuntimeError("Signed movement partition count differs from backing")
    if metrics["archives_processed"] != 195:
        raise RuntimeError("Frozen construction did not process 195 archives")
    if metrics["negative_weight_rows"] != metrics["total_exclusion_rows"]:
        raise RuntimeError("Negative weights do not reconcile with exclusions")


def validate_construction_backing(
    data_dir: Path,
    source_dir: Path,
) -> dict[str, Any]:
    """Validate frozen backing against the analytical inputs."""
    _validate_file_set(source_dir)
    _validate_movement_contract(data_dir, source_dir)
    _validate_national_panel(data_dir, source_dir)
    _validate_sector_panel(data_dir, source_dir)
    _validate_treatment(data_dir, source_dir)
    return {
        "files": len(EXPECTED_FILES),
        "status": "pass",
    }


def materialize(source_dir: Path, output_dir: Path) -> None:
    """Copy the validated backing into the isolated public results tree."""
    for relative in sorted(EXPECTED_FILES):
        source = source_dir / relative
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(f"{destination.suffix}.tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    data_dir = args.data_dir.resolve()
    source_dir = (
        args.source_dir.resolve()
        if args.source_dir
        else data_dir / "derived" / "caged" / "construction_outputs"
    )
    summary = validate_construction_backing(data_dir, source_dir)
    materialize(source_dir, args.output_dir.resolve())
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
