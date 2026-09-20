#!/usr/bin/env python3
"""Reconcile manuscript narrative numbers against reproduced backing data."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = PACKAGE_ROOT / "config" / "numeric_claims.csv"
DEFAULT_OUTPUT_ROOT = PACKAGE_ROOT / "results" / "reproduced"


def _filter_frame(frame: pd.DataFrame, specification: str) -> pd.DataFrame:
    filters = json.loads(specification)
    if not isinstance(filters, dict):
        raise ValueError("Claim filters must be a JSON object")
    selected = frame
    for raw_key, expected in filters.items():
        if raw_key.endswith("__in"):
            key = raw_key.removesuffix("__in")
            if not isinstance(expected, list):
                raise ValueError(f"{raw_key} requires a JSON list")
            selected = selected.loc[selected[key].isin(expected)]
            continue
        comparison = next(
            (
                (suffix, operator)
                for suffix, operator in (
                    ("__lt", "lt"),
                    ("__le", "le"),
                    ("__gt", "gt"),
                    ("__ge", "ge"),
                )
                if raw_key.endswith(suffix)
            ),
            None,
        )
        if comparison is not None:
            suffix, operator = comparison
            key = raw_key.removesuffix(suffix)
            values = pd.to_numeric(selected[key], errors="raise")
            selected = selected.loc[getattr(values, operator)(expected)]
            continue
        selected = selected.loc[selected[raw_key].eq(expected)]
    return selected


def _csv_value(path: Path, row: pd.Series) -> Any:
    frame = pd.read_csv(path)
    selected = _filter_frame(frame, str(row["filter"]))
    field = str(row["field"])
    aggregation = str(row["aggregation"])
    if aggregation == "scalar":
        if len(selected) != 1:
            raise ValueError(
                f"Expected one row for {row['claim_id']}, found {len(selected)}"
            )
        return selected[field].iloc[0]
    if aggregation == "count":
        return len(selected)
    if aggregation == "nunique":
        return selected[field].nunique(dropna=True)
    if aggregation in {"sum", "mean", "min", "max"}:
        return getattr(selected[field], aggregation)()
    raise ValueError(f"Unsupported CSV aggregation: {aggregation}")


def _json_value(path: Path, row: pd.Series) -> Any:
    if row["aggregation"] != "json_path":
        raise ValueError("JSON claims require aggregation=json_path")
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    for key in str(row["field"]).split("."):
        if isinstance(value, list):
            value = value[int(key)]
        else:
            value = value[key]
    return value


def _observed_value(path: Path, row: pd.Series) -> Any:
    if path.suffix.lower() == ".csv":
        return _csv_value(path, row)
    if path.suffix.lower() == ".json":
        return _json_value(path, row)
    raise ValueError(f"Unsupported backing-data format: {path}")


def _display(value: Any, value_type: str) -> str:
    if value_type == "boolean":
        return "true" if bool(value) else "false"
    if value_type == "integer":
        return str(int(value))
    if value_type == "number":
        return repr(float(value))
    return str(value)


def _matches(observed: Any, row: pd.Series) -> tuple[bool, float | None]:
    value_type = str(row["value_type"])
    expected = str(row["expected_value"])
    if value_type in {"number", "integer"}:
        difference = abs(float(observed) - float(expected))
        return difference <= float(row["tolerance"]), difference
    if value_type == "boolean":
        expected_boolean = expected.lower() == "true"
        return bool(observed) is expected_boolean, None
    return str(observed) == expected, None


def reconcile_claims(
    claims: pd.DataFrame,
    *,
    output_root: Path,
    components: set[str] | None = None,
) -> pd.DataFrame:
    if components is not None:
        claims = claims.loc[claims["component"].isin(components)].copy()
    records: list[dict[str, Any]] = []
    for _, row in claims.iterrows():
        path = output_root / str(row["component"]) / str(row["artifact_path"])
        try:
            if not path.is_file():
                raise FileNotFoundError(path)
            observed = _observed_value(path, row)
            matches, difference = _matches(observed, row)
            record = {
                **row.to_dict(),
                "observed_value": _display(observed, str(row["value_type"])),
                "absolute_difference": (
                    "" if difference is None or math.isnan(difference) else difference
                ),
                "status": "pass" if matches else "fail",
                "error": "",
            }
        except Exception as error:  # noqa: BLE001 - every claim must be recorded
            record = {
                **row.to_dict(),
                "observed_value": "",
                "absolute_difference": "",
                "status": "error",
                "error": str(error),
            }
        records.append(record)
    return pd.DataFrame(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--component",
        action="append",
        choices=("section3", "caged", "rais", "pnadc", "spatial"),
        help="Restrict reconciliation to one or more reproduced components.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    claims = pd.read_csv(args.contract, dtype=str, keep_default_na=False)
    result = reconcile_claims(
        claims,
        output_root=args.output_root.resolve(),
        components=set(args.component) if args.component else None,
    )
    destination = args.output or (
        args.output_root / "validation" / "numeric_claims_reconciliation.csv"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    result.to_csv(temporary, index=False)
    os.replace(temporary, destination)
    failed = result.loc[~result["status"].eq("pass")]
    print(
        json.dumps(
            {
                "claims": len(result),
                "failed": len(failed),
                "output": str(destination),
            },
            sort_keys=True,
        )
    )
    return 0 if failed.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
