"""Cardinality-checked pandas merges with an explicit row audit."""

from __future__ import annotations

import json
from collections.abc import Callable, Hashable, Sequence
from typing import Any

import pandas as pd


Reporter = Callable[[dict[str, Any]], None]


def _columns(value: Hashable | Sequence[Hashable] | None) -> list[Hashable]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    return list(value)


def _default_reporter(report: dict[str, Any]) -> None:
    print("MERGE_AUDIT " + json.dumps(report, sort_keys=True), flush=True)


def audited_merge(
    left: pd.DataFrame,
    right: pd.DataFrame | pd.Series,
    *,
    merge_id: str,
    validate: str,
    reporter: Reporter | None = _default_reporter,
    **kwargs: Any,
) -> pd.DataFrame:
    """Merge while reporting key uniqueness and the output-row delta."""
    if not merge_id.strip():
        raise ValueError("Every merge requires a non-empty merge_id")
    if not validate:
        raise ValueError("Every merge requires an explicit cardinality")
    shared = _columns(kwargs.get("on"))
    left_keys = _columns(kwargs.get("left_on")) or shared
    right_keys = _columns(kwargs.get("right_on")) or shared
    if not left_keys or not right_keys:
        raise ValueError(
            f"Merge {merge_id} must declare on or left_on/right_on keys"
        )
    right_frame = (
        right.to_frame()
        if isinstance(right, pd.Series)
        else right
    )
    if any(key not in right_frame.columns for key in right_keys):
        index_names = {
            name for name in right_frame.index.names if name is not None
        }
        if set(right_keys).issubset(index_names):
            right_frame = right_frame.reset_index()
    left_unique = not left.duplicated(left_keys).any()
    right_unique = not right_frame.duplicated(right_keys).any()
    result = pd.merge(
        left,
        right_frame,
        validate=validate,
        **kwargs,
    )
    report = {
        "after_rows": int(len(result)),
        "delta_vs_left_rows": int(len(result) - len(left)),
        "left_key_unique": bool(left_unique),
        "left_rows": int(len(left)),
        "merge_id": merge_id,
        "right_key_unique": bool(right_unique),
        "right_rows": int(len(right_frame)),
        "validate": validate,
    }
    if reporter is not None:
        reporter(report)
    result.attrs["merge_audit"] = report
    return result
